# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import flask
from sqlalchemy import sql

from dci.common import exceptions as dci_exc
from dci.db import models

_TABLE = models.JOBS


def get_last_rconfiguration_id(topic_id, remoteci_id, db_conn=None):
    """Get the rconfiguration_id of the last job run by the remoteci.

    :param topic_id: the topic
    :param remoteci_id: the remoteci id
    :return: last rconfiguration_id of the remoteci
    """
    db_conn = db_conn or flask.g.db_conn
    query = sql.select([_TABLE.c.rconfiguration_id]). \
        order_by(sql.desc(_TABLE.c.created_at)). \
        where(sql.and_(_TABLE.c.topic_id == topic_id,
                       _TABLE.c.remoteci_id == remoteci_id)). \
        limit(1)
    rconfiguration_id = db_conn.execute(query).fetchone()
    if rconfiguration_id is not None:
        return str(rconfiguration_id[0])
    else:
        return None


def get_remoteci_configuration(topic_id, remoteci_id, db_conn=None):
    """Get a remoteci configuration. This will iterate over each
    configuration in a round robin manner depending on the last
    rconfiguration used by the remoteci."""

    db_conn = db_conn or flask.g.db_conn
    last_rconfiguration_id = get_last_rconfiguration_id(
        topic_id, remoteci_id, db_conn=db_conn)
    _RCONFIGURATIONS = models.REMOTECIS_RCONFIGURATIONS
    _J_RCONFIGURATIONS = models.JOIN_REMOTECIS_RCONFIGURATIONS
    query = sql.select([_RCONFIGURATIONS]). \
        select_from(_J_RCONFIGURATIONS.
                    join(_RCONFIGURATIONS)). \
        where(_J_RCONFIGURATIONS.c.remoteci_id == remoteci_id)
    query = query.where(sql.and_(_RCONFIGURATIONS.c.state != 'archived',
                                 _RCONFIGURATIONS.c.topic_id == topic_id))
    query = query.order_by(sql.desc(_RCONFIGURATIONS.c.created_at))
    query = query.order_by(sql.asc(_RCONFIGURATIONS.c.name))
    all_rconfigurations = db_conn.execute(query).fetchall()

    if len(all_rconfigurations) > 0:
        for i in range(len(all_rconfigurations)):
            if str(all_rconfigurations[i]['id']) == last_rconfiguration_id:
                # if i==0, then indice -1 is the last element
                return all_rconfigurations[i - 1]
        return all_rconfigurations[0]
    else:
        return None


def get_component_types_from_topic(topic_id, db_conn=None):
    db_conn = db_conn or flask.g.db_conn
    query = sql.select([models.TOPICS]).\
        where(models.TOPICS.c.id == topic_id)
    topic = db_conn.execute(query).fetchone()
    topic = dict(topic)
    return topic['component_types']


def get_component_types(topic_id, remoteci_id, db_conn=None):

    db_conn = db_conn or flask.g.db_conn
    rconfiguration = get_remoteci_configuration(topic_id, remoteci_id,
                                                db_conn=db_conn)

    # if there is no rconfiguration associated to the remoteci or no
    # component types then use the topic's one.
    if (rconfiguration is not None and
            rconfiguration['component_types'] is not None):
        component_types = rconfiguration['component_types']
    else:
        component_types = get_component_types_from_topic(topic_id,
                                                         db_conn=db_conn)

    return component_types, rconfiguration


def get_last_components(component_types, topic_id):
    schedule_components_ids = []
    for ct in component_types:
        where_clause = sql.and_(models.COMPONENTS.c.type == ct,
                                models.COMPONENTS.c.topic_id == topic_id,
                                models.COMPONENTS.c.export_control == True,
                                models.COMPONENTS.c.state == 'active')  # noqa
        query = (sql.select([models.COMPONENTS.c.id])
                 .where(where_clause)
                 .order_by(sql.desc(models.COMPONENTS.c.created_at)))
        cmpt_id = flask.g.db_conn.execute(query).fetchone()

        if cmpt_id is None:
            msg = 'Component of type "%s" not found or not exported.' % ct
            raise dci_exc.DCIException(msg, status_code=412)

        cmpt_id = cmpt_id[0]
        if cmpt_id in schedule_components_ids:
            msg = ('Component types %s malformed: type %s duplicated.' %
                   (component_types, ct))
            raise dci_exc.DCIException(msg, status_code=412)
        schedule_components_ids.append(cmpt_id)
    return schedule_components_ids


def get_components_from_ids(topic_id, components_ids, component_types):

    if len(components_ids) != len(component_types):
        msg = 'The number of component ids does not match the number ' \
              'of component types %s' % component_types
        raise dci_exc.DCIException(msg, status_code=412)

    # get the components from their ids
    schedule_component_types = set()
    for c_id in components_ids:
        where_clause = sql.and_(models.COMPONENTS.c.id == c_id,
                                models.COMPONENTS.c.topic_id == topic_id,
                                models.COMPONENTS.c.export_control == True,  # noqa
                                models.COMPONENTS.c.state == 'active')
        query = (sql.select([models.COMPONENTS])
                 .where(where_clause))
        cmpt = flask.g.db_conn.execute(query).fetchone()

        if cmpt is None:
            msg = 'Component id %s not found or not exported' % c_id
            raise dci_exc.DCIException(msg, status_code=412)
        cmpt = dict(cmpt)

        if cmpt['type'] in schedule_component_types:
            msg = ('Component types malformed: type %s duplicated.' %
                   cmpt['type'])
            raise dci_exc.DCIException(msg, status_code=412)
        schedule_component_types.add(cmpt['type'])
    return components_ids


def verify_and_get_components_ids(topic_id, component_types, components_ids):
    if components_ids == []:
        schedule_components_ids = get_last_components(
            component_types, topic_id)
    else:
        schedule_components_ids = get_components_from_ids(
            topic_id, components_ids, component_types)
    return schedule_components_ids


def kill_existing_jobs(remoteci_id, topic_id):

    where_clause = sql.expression.and_(
        _TABLE.c.remoteci_id == remoteci_id,
        _TABLE.c.topic_id == topic_id,
        _TABLE.c.status.in_(('new', 'pre-run', 'running', 'post-run'))
    )
    kill_query = _TABLE .update().where(where_clause).values(status='killed')
    flask.g.db_conn.execute(kill_query)
