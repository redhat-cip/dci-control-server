# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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

import datetime

import flask
from flask import json
import logging
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci import dci_config
from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import export_control
from dci.api.v1 import issues
from dci.api.v1 import remotecis
from dci.api.v1 import tags
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models
from dci.stores import files_utils

# associate column names with the corresponding SA Column object
_TABLE = models.COMPONENTS
_TABLE_TAGS = models.JOIN_COMPONENTS_TAGS

_TABLE_TAGS_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE_TAGS)
_JJC = models.JOIN_JOBS_COMPONENTS
_VALID_EMBED = embeds.components()
_C_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_CF_COLUMNS = v1_utils.get_columns_name_with_objects(models.COMPONENTFILES)
_JOBS_C_COLUMNS = v1_utils.get_columns_name_with_objects(models.JOBS)
_EMBED_MANY = {
    'files': True,
    'jobs': True
}

LOG = logging.getLogger(__name__)


def _get_latest_components():
    __C_COLUMNS = dict(_C_COLUMNS)
    __C_COLUMNS.update({
        'topic_id': models.TOPICS.c.id.label('topic_id'),
        'topic_name': models.TOPICS.c.name.label('topic_name'),
        'product_id': models.PRODUCTS.c.id.label('product_id'),
        'product_name': models.PRODUCTS.c.name.label('product_name'),
    })

    join_condition = sql.join(
        models.COMPONENTS, models.TOPICS,
        sql.and_(models.COMPONENTS.c.topic_id == models.TOPICS.c.id,
                 models.TOPICS.c.state == 'active')
    ).join(
        models.PRODUCTS,
        sql.and_(models.TOPICS.c.product_id == models.PRODUCTS.c.id,
                 models.PRODUCTS.c.state == 'active')
    )

    select_clause = list(dict(__C_COLUMNS).values())
    query = (sql.select(select_clause).select_from(join_condition).
             distinct(models.TOPICS.c.id, models.COMPONENTS.c.type).
             where(models.COMPONENTS.c.state == 'active').
             order_by(models.TOPICS.c.id, models.COMPONENTS.c.type,
                      models.COMPONENTS.c.created_at.desc()))
    rows = flask.g.db_conn.execute(query).fetchall()

    return [dict(row) for row in rows]


@api.route('/components', methods=['POST'])
@decorators.login_required
def create_components(user):
    values = v1_utils.common_values_dict()
    values.update(schemas.component.post(flask.request.json))

    if str(values['topic_id']) not in v1_utils.user_topic_ids(user):
        raise dci_exc.Unauthorized()

    query = _TABLE.insert().values(**values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    result = json.dumps({'component': values})
    return flask.Response(result, 201, content_type='application/json')


@api.route('/components/<uuid:c_id>', methods=['PUT'])
@decorators.login_required
def update_components(user, c_id):
    component = v1_utils.verify_existence_and_get(c_id, _TABLE)
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    if str(component['topic_id']) not in v1_utils.user_topic_ids(user):
        raise dci_exc.Unauthorized()

    values = schemas.component.put(flask.request.json)
    values['etag'] = utils.gen_etag()

    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == c_id
    )

    query = _TABLE.update().returning(*_TABLE.columns).where(where_clause).\
        values(**values)

    result = flask.g.db_conn.execute(query)
    if not result.rowcount:
        raise dci_exc.DCIConflict('Component', c_id)

    return flask.Response(
        json.dumps({'component': result.fetchone()}), 200,
        headers={'ETag': values['etag']}, content_type='application/json'
    )


def get_all_components(user, topic_id):
    """Get all components of a topic."""

    args = schemas.args(flask.request.args.to_dict())

    query = v1_utils.QueryBuilder(_TABLE, args, _C_COLUMNS)

    query.add_extra_condition(sql.and_(
        _TABLE.c.topic_id == topic_id,
        _TABLE.c.state != 'archived'))

    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)

    return flask.jsonify({'components': rows, '_meta': {'count': nb_rows}})


@api.route('/components/latest', methods=['GET'])
@decorators.login_required
def get_latest_components(user):
    authorized_topics = v1_utils.user_topic_ids(user)

    latest_components = _get_latest_components()
    latest_components = [c for c in latest_components
                         if str(c['topic_id']) in authorized_topics]

    return flask.jsonify({
        'components': latest_components,
        '_meta': {'count': len(latest_components)}
    })


@api.route('/components/<uuid:c_id>', methods=['GET'])
@decorators.login_required
def get_component_by_id(user, c_id):
    component = v1_utils.verify_existence_and_get(c_id, _TABLE)
    topic = v1_utils.verify_existence_and_get(component['topic_id'],
                                              models.TOPICS)

    export_control.verify_access_to_topic(user, topic)
    return base.get_resource_by_id(user, component, _TABLE, _EMBED_MANY)


@api.route('/components/<uuid:c_id>', methods=['DELETE'])
@decorators.login_required
def delete_component_by_id(user, c_id):
    component = v1_utils.verify_existence_and_get(c_id, _TABLE)

    if str(component['topic_id']) not in v1_utils.user_topic_ids(user):
        raise dci_exc.Unauthorized()

    values = {'state': 'archived'}
    where_clause = sql.and_(
        _TABLE.c.id == c_id
    )
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Component', c_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/components/<uuid:c_id>/files', methods=['GET'])
@decorators.login_required
def list_components_files(user, c_id):
    component = v1_utils.verify_existence_and_get(c_id, _TABLE)
    topic = v1_utils.verify_existence_and_get(component['topic_id'],
                                              models.TOPICS)
    export_control.verify_access_to_topic(user, topic)

    args = schemas.args(flask.request.args.to_dict())

    query = v1_utils.QueryBuilder(models.COMPONENTFILES, args, _CF_COLUMNS)
    query.add_extra_condition(models.COMPONENTFILES.c.component_id == c_id)

    nb_rows = query.get_number_of_rows(models.COMPONENTFILES,
                                       models.COMPONENTFILES.c.component_id == c_id)  # noqa
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, models.COMPONENTFILES.name, None, None)

    return flask.jsonify({'component_files': rows,
                          '_meta': {'count': nb_rows}})


@api.route('/components/<uuid:c_id>/files/<uuid:f_id>', methods=['GET'])
@decorators.login_required
def get_component_file(user, c_id, f_id):
    component = v1_utils.verify_existence_and_get(c_id, _TABLE)
    topic = v1_utils.verify_existence_and_get(component['topic_id'],
                                              models.TOPICS)
    export_control.verify_access_to_topic(user, topic)

    COMPONENT_FILES = models.COMPONENT_FILES
    where_clause = sql.and_(COMPONENT_FILES.c.id == f_id,
                            COMPONENT_FILES.c.component_id == c_id)

    query = sql.select([COMPONENT_FILES]).where(where_clause)

    component_f = flask.g.db_conn.execute(query).fetchone()

    if component_f is None:
        raise dci_exc.DCINotFound('Component File', f_id)

    res = flask.jsonify({'component_file': component_f})
    return res


@api.route('/components/<uuid:c_id>/files/<uuid:f_id>/content',
           methods=['GET'])
@decorators.login_required
def download_component_file(user, c_id, f_id):
    store = dci_config.get_store('components')
    component = v1_utils.verify_existence_and_get(c_id, _TABLE)
    topic = v1_utils.verify_existence_and_get(component['topic_id'],
                                              models.TOPICS)
    export_control.verify_access_to_topic(user, topic)

    component_file = v1_utils.verify_existence_and_get(
        f_id, models.COMPONENT_FILES)
    file_path = files_utils.build_file_path(component['topic_id'], c_id, f_id)

    # Check if file exist on the storage engine
    store.head(file_path)

    _, file_descriptor = store.get(file_path)
    return flask.send_file(file_descriptor, mimetype=component_file['mime'])


@api.route('/components/<uuid:c_id>/files', methods=['POST'])
@decorators.login_required
def upload_component_file(user, c_id):
    COMPONENT_FILES = models.COMPONENT_FILES

    component = v1_utils.verify_existence_and_get(c_id, _TABLE)
    if str(component['topic_id']) not in v1_utils.user_topic_ids(user):
        raise dci_exc.Unauthorized()

    store = dci_config.get_store('components')

    file_id = utils.gen_uuid()
    file_path = files_utils.build_file_path(component['topic_id'],
                                            c_id,
                                            file_id)
    content = files_utils.get_stream_or_content_from_request(flask.request)
    store.upload(file_path, content)
    s_file = store.head(file_path)

    values = dict.fromkeys(['md5', 'mime', 'component_id', 'name'])

    values.update({
        'id': file_id,
        'component_id': c_id,
        'name': file_id,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'md5': s_file['etag'],
        'mime': s_file['content-type'],
        'size': s_file['content-length']
    })

    query = COMPONENT_FILES.insert().values(**values)

    flask.g.db_conn.execute(query)
    result = json.dumps({'component_file': values})
    return flask.Response(result, 201, content_type='application/json')


@api.route('/components/<uuid:c_id>/files/<uuid:f_id>', methods=['DELETE'])
@decorators.login_required
def delete_component_file(user, c_id, f_id):
    COMPONENT_FILES = models.COMPONENT_FILES
    component = v1_utils.verify_existence_and_get(c_id, _TABLE)
    if str(component['topic_id']) not in v1_utils.user_topic_ids(user):
        raise dci_exc.Unauthorized()
    v1_utils.verify_existence_and_get(f_id, COMPONENT_FILES)

    where_clause = COMPONENT_FILES.c.id == f_id

    query = COMPONENT_FILES.delete().where(where_clause)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Component File', f_id)

    store = dci_config.get_store('components')
    file_path = files_utils.build_file_path(component['topic_id'], c_id, f_id)
    store.delete(file_path)

    return flask.Response(None, 204, content_type='application/json')


def get_component_types_from_topic(topic_id, db_conn=None):
    """Returns the component types of a topic."""
    db_conn = db_conn or flask.g.db_conn
    query = sql.select([models.TOPICS]).\
        where(models.TOPICS.c.id == topic_id)
    topic = db_conn.execute(query).fetchone()
    topic = dict(topic)
    return topic['component_types']


def get_component_types(topic_id, remoteci_id, db_conn=None):
    """Returns either the topic component types or the rconfigration's
    component types."""

    db_conn = db_conn or flask.g.db_conn
    rconfiguration = remotecis.get_remoteci_configuration(topic_id,
                                                          remoteci_id,
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


def get_last_components_by_type(component_types, topic_id, db_conn=None):
    """For each component type of a topic, get the last one."""
    db_conn = db_conn or flask.g.db_conn
    _components = []
    for ct in component_types:
        where_clause = sql.and_(models.COMPONENTS.c.type == ct,
                                models.COMPONENTS.c.topic_id == topic_id,
                                models.COMPONENTS.c.state == 'active')  # noqa
        query = (sql.select([models.COMPONENTS])
                 .where(where_clause)
                 .order_by(sql.desc(models.COMPONENTS.c.created_at)))
        component = db_conn.execute(query).fetchone()

        if component is None:
            msg = 'Component of type "%s" not found or not exported.' % ct
            raise dci_exc.DCIException(msg, status_code=412)

        if component['id'] in _components:
            msg = ('Component types %s malformed: type %s duplicated.' %
                   (component_types, ct))
            raise dci_exc.DCIException(msg, status_code=412)
        _components.append(component)
    return _components


def verify_and_get_components_ids(topic_id, components_ids, component_types,
                                  db_conn=None):
    """Process some verifications of the provided components ids."""
    db_conn = db_conn or flask.g.db_conn
    if len(components_ids) != len(component_types):
        msg = 'The number of component ids does not match the number ' \
              'of component types %s' % component_types
        raise dci_exc.DCIException(msg, status_code=412)

    # get the components from their ids
    schedule_component_types = set()
    for c_id in components_ids:
        where_clause = sql.and_(models.COMPONENTS.c.id == c_id,
                                models.COMPONENTS.c.topic_id == topic_id,
                                models.COMPONENTS.c.state == 'active')
        query = (sql.select([models.COMPONENTS])
                 .where(where_clause))
        cmpt = db_conn.execute(query).fetchone()

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


def get_schedule_components_ids(topic_id, component_types, components_ids):
    if components_ids == []:
        return [c['id'] for c in get_last_components_by_type(
            component_types, topic_id)]
    return verify_and_get_components_ids(topic_id, components_ids,
                                         component_types)


@api.route('/components/<c_id>/issues', methods=['GET'])
@decorators.login_required
def retrieve_issues_from_component(user, c_id):
    """Retrieve all issues attached to a component."""
    return issues.get_issues_by_resource(c_id, _TABLE)


@api.route('/components/<c_id>/issues', methods=['POST'])
@decorators.login_required
def attach_issue_to_component(user, c_id):
    """Attach an issue to a component."""
    return issues.attach_issue(c_id, _TABLE, user.id)


@api.route('/components/<c_id>/issues/<i_id>', methods=['DELETE'])
@decorators.login_required
def unattach_issue_from_component(user, c_id, i_id):
    """Unattach an issue to a component."""
    return issues.unattach_issue(c_id, i_id, _TABLE)


@api.route('/components/<uuid:c_id>/tags', methods=['GET'])
@decorators.login_required
def retrieve_tags_from_component(user, c_id):
    """Retrieve all tags attached to a component."""
    JCT = models.JOIN_COMPONENTS_TAGS
    query = (sql.select([models.TAGS])
             .select_from(JCT.join(models.TAGS))
             .where(JCT.c.component_id == c_id))
    rows = flask.g.db_conn.execute(query)

    return flask.jsonify({'tags': rows, '_meta': {'count': rows.rowcount}})


@api.route('/components/<uuid:c_id>/tags', methods=['POST'])
@decorators.login_required
def add_tag_for_component(user, c_id):
    """Add a tag on a specific component."""

    v1_utils.verify_existence_and_get(c_id, _TABLE)

    values = {
        'component_id': c_id
    }

    component_tagged = tags.add_tag_to_resource(values,
                                                models.JOIN_COMPONENTS_TAGS)

    return flask.Response(json.dumps(component_tagged), 201,
                          content_type='application/json')


@api.route('/components/<uuid:c_id>/tags/<uuid:tag_id>', methods=['DELETE'])
@decorators.login_required
def delete_tag_for_component(user, c_id, tag_id):
    """Delete a tag on a specific component."""
    # Todo : check c_id and tag_id exist in db

    query = _TABLE_TAGS.delete().where(_TABLE_TAGS.c.tag_id == tag_id and
                                       _TABLE_TAGS.c.component_id == c_id)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE_TAGS.c.tag_id, 'tag_id')

    return flask.Response(None, 204, content_type='application/json')


@api.route('/components/purge', methods=['GET'])
@decorators.login_required
def get_to_purge_archived_components(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/components/purge', methods=['POST'])
@decorators.login_required
def purge_archived_components(user):

    # get all archived components
    archived_components = base.get_archived_resources(_TABLE)

    store = dci_config.get_store('components')

    # for each component delete it and all the component_files associated
    # from within a transaction
    # if the SQL deletion or the Store deletion fail then
    # rollback the transaction, otherwise commit.
    for cmpt in archived_components:
        get_cmpt_files = v1_utils.QueryBuilder(models.COMPONENT_FILES)
        get_cmpt_files.add_extra_condition(
            models.COMPONENT_FILES.c.component_id == cmpt['id'])
        cmpt_files = get_cmpt_files.execute(fetchall=True, use_labels=False)
        for cmpt_file in cmpt_files:
            tx = flask.g.db_conn.begin()
            file_path = files_utils.build_file_path(cmpt['topic_id'],
                                                    cmpt['id'],
                                                    cmpt_file['id'])
            try:
                q_delete_cfile = models.COMPONENT_FILES.delete().\
                    where(models.COMPONENT_FILES.c.id == cmpt_file['id'])
                flask.g.db_conn.execute(q_delete_cfile)
                store.delete(file_path)
                tx.commit()
            except dci_exc.StoreExceptions as e:
                if e.status_code == 404:
                    LOG.warn('file %s not found in store' % file_path)
                else:
                    raise e
            except Exception as e:
                tx.rollback()
                LOG.error('Error while removing component file %s, message: %s'
                          % (file_path, str(e)))
                raise dci_exc.DCIException(str(e))
        flask.g.db_conn.execute(_TABLE.delete().
                                where(_TABLE.c.id == cmpt['id']))

    return flask.Response(None, 204, content_type='application/json')
