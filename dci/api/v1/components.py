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
from sqlalchemy import sql

from dci import dci_config
from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import export_control
from dci.api.v1 import issues
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    check_json_is_valid,
    clean_json_with_schema,
    create_component_schema,
    update_component_schema,
    check_and_get_args
)
from dci.common import utils
from dci.db import models
from dci.db import models2
from dci.db import declarative
from dci.stores import files_utils
import sqlalchemy.orm as sa_orm

# associate column names with the corresponding SA Column object
_TABLE = models.COMPONENTS
_TABLE_TAGS = models.JOIN_COMPONENTS_TAGS

_TABLE_TAGS_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE_TAGS)
_JJC = models.JOIN_JOBS_COMPONENTS
_C_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_CF_COLUMNS = v1_utils.get_columns_name_with_objects(models.COMPONENTFILES)
_JOBS_C_COLUMNS = v1_utils.get_columns_name_with_objects(models.JOBS)

logger = logging.getLogger(__name__)


def _verify_component_and_topic_access(user, component):
    component_team_id = component.team_id
    if component_team_id is not None:
        if user.is_not_in_team(component_team_id):
            dci_exc.Unauthorized()
    else:
        topic = base.get_resource_orm(models2.Topic, component.topic_id)
        export_control.verify_access_to_topic(user, topic)


def _verify_component_access_and_role(user, component):
    component_team_id = component.team_id
    if component_team_id is not None:
        if user.is_not_in_team(component_team_id):
            dci_exc.Unauthorized()
    elif user.is_not_super_admin() and user.is_not_feeder() and user.is_not_epm():
        raise dci_exc.Unauthorized()


@api.route('/components', methods=['POST'])
@decorators.login_required
def create_components(user):
    values = flask.request.json
    check_json_is_valid(create_component_schema, values)
    values.update(v1_utils.common_values_dict())

    if "team_id" in values:
        if user.is_not_in_team(values['team_id']):
            raise dci_exc.Unauthorized()
    else:
        if user.is_not_super_admin() and user.is_not_feeder() and user.is_not_epm():
            raise dci_exc.Unauthorized()

    values["type"] = values["type"].lower()

    c = base.create_resource_orm(models2.Component, values)

    return flask.Response(
        json.dumps({"component": c}),
        201,
        headers={"ETag": values["etag"]},
        content_type="application/json",
    )


@api.route('/components/<uuid:c_id>', methods=['PUT'])
@decorators.login_required
def update_components(user, c_id):
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    component = base.get_resource_orm(models2.Component, c_id, if_match_etag)

    _verify_component_and_topic_access(user, component)

    values = clean_json_with_schema(update_component_schema, flask.request.json)
    values["type"] = values.get("type", component.type).lower()
    base.update_resource_orm(component, values)

    component = base.get_resource_orm(models2.Component, c_id)

    return flask.Response(
        json.dumps({'component': component.serialize()}),
        200,
        headers={'ETag': component.etag},
        content_type='application/json'
    )


def get_all_components(user, topic_id):
    """Get all components of a topic that are accessible by
    the user."""

    args = check_and_get_args(flask.request.args.to_dict())

    query = flask.g.session.query(models2.Component)
    query = query.filter(sql.and_(
        models2.Component.topic_id == topic_id,
        models2.Component.state != 'archived'))

    if (user.is_not_super_admin() and user.is_not_feeder() and
        user.is_not_epm()):
        query = query.filter(
            sql.or_(
                models2.Component.team_id.in_(user.teams_ids),
                models2.Component.team_id == None)  # noqa
        )

    query = declarative.handle_args(query, models2.Component, args)
    nb_components = query.count()

    components = [component.serialize() for component in query.all()]

    return flask.jsonify({'components': components, '_meta': {'count': nb_components}})


@api.route('/components/<uuid:c_id>', methods=['GET'])
@decorators.login_required
def get_component_by_id(user, c_id):
    component = base.get_resource_orm(models2.Component, c_id, options=[sa_orm.joinedload('files'), sa_orm.joinedload('jobs')])
    _verify_component_and_topic_access(user, component)

    return flask.Response(
        json.dumps({"component": component.serialize()}),
        200,
        headers={"ETag": component.etag},
        content_type="application/json",
    )


@api.route('/components/<uuid:c_id>', methods=['DELETE'])
@decorators.login_required
def delete_component_by_id(user, c_id):

    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    component = base.get_resource_orm(models2.Component, c_id, if_match_etag)
    _verify_component_access_and_role(user, component)
    base.update_resource_orm(component, {"state": "archived"})

    return flask.Response(None, 204, content_type="application/json")


@api.route('/components/<uuid:c_id>/files', methods=['GET'])
@decorators.login_required
def list_components_files(user, c_id):
    component = base.get_resource_orm(models2.Component, c_id)
    _verify_component_and_topic_access(user, component)
    args = check_and_get_args(flask.request.args.to_dict())

    query = flask.g.session.query(models2.Componentfile)
    query = query.filter(
        sql.and_(models2.Componentfile.component_id == c_id,
                 models2.Componentfile.state != "archived"))

    nb_componentfiles = query.count()

    query = declarative.handle_args(query, models2.Componentfile, args)

    componentfiles = [cf.serialize() for cf in query.all()]

    return flask.jsonify({'component_files': componentfiles,
                          '_meta': {'count': nb_componentfiles}})


@api.route('/components/<uuid:c_id>/files/<uuid:f_id>', methods=['GET'])
@decorators.login_required
def get_component_file_by_id(user, c_id, f_id):
    component = base.get_resource_orm(models2.Component, c_id)
    _verify_component_and_topic_access(user, component)

    componentfile = base.get_resource_orm(models2.Componentfile, f_id)

    res = flask.jsonify({'component_file': componentfile.serialize()})
    return res


@api.route('/components/<uuid:c_id>/files/<uuid:f_id>/content',
           methods=['GET'])
@decorators.login_required
def download_component_file(user, c_id, f_id):
    component = base.get_resource_orm(models2.Component, c_id)
    _verify_component_and_topic_access(user, component)

    store = dci_config.get_store('components')

    componentfile = base.get_resource_orm(models2.Componentfile, f_id)
    file_path = files_utils.build_file_path(component.topic_id, c_id, f_id)

    # Check if file exist on the storage engine
    store.head(file_path)

    _, file_descriptor = store.get(file_path)
    return flask.send_file(file_descriptor, mimetype=componentfile.mime)


@api.route('/components/<uuid:c_id>/files', methods=['POST'])
@decorators.login_required
def upload_component_file(user, c_id):
    component = base.get_resource_orm(models2.Component, c_id)
    _verify_component_and_topic_access(user, component)

    if str(component.topic_id) not in v1_utils.user_topic_ids(user):
        raise dci_exc.Unauthorized()

    store = dci_config.get_store('components')

    file_id = utils.gen_uuid()
    file_path = files_utils.build_file_path(component.topic_id,
                                            c_id,
                                            file_id)
    store.upload(file_path, flask.request.data)
    s_file = store.head(file_path)

    values = dict.fromkeys(['md5', 'mime', 'component_id', 'name'])

    values.update({
        'id': file_id,
        'component_id': c_id,
        'name': file_id,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'etag': s_file['etag'],
        'md5': s_file['etag'],
        'mime': s_file['content-type'],
        'size': s_file['content-length']
    })

    componentfile = base.create_resource_orm(models2.Componentfile, values)

    result = json.dumps({'component_file': componentfile})
    return flask.Response(result, 201, content_type='application/json')


@api.route('/components/<uuid:c_id>/files/<uuid:f_id>', methods=['DELETE'])
@decorators.login_required
def delete_component_file(user, c_id, f_id):
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    component = base.get_resource_orm(models2.Component, c_id)
    _verify_component_access_and_role(user, component)
    componentfile = base.get_resource_orm(models2.Componentfile, f_id, if_match_etag)
    base.update_resource_orm(componentfile, {"state": "archived"})

    return flask.Response(None, 204, content_type="application/json")


def get_component_types_from_topic(topic_id, db_conn=None):
    """Returns the component types of a topic."""
    db_conn = db_conn or flask.g.db_conn
    query = sql.select([models.TOPICS]).\
        where(models.TOPICS.c.id == topic_id)
    topic = db_conn.execute(query).fetchone()
    topic = dict(topic)
    return topic['component_types']


def get_last_components_by_type(component_types, topic_id, session=None):
    """For each component type of a topic, get the last one."""
    session = session or flask.g.session
    _components_ids = []
    _components = []
    for ct in component_types:
        try:
            component = session.query(models2.Component).filter(
                sql.and_(models2.Component.type == ct,
                         models2.Component.topic_id == topic_id,
                         models2.Component.state == 'active')
            ).order_by(
                models2.Component.created_at.desc()
            ).first()
        except sa_orm.exc.NoResultFound:
            raise dci_exc.DCIException(
                message="component of type %s not found or not exported" % ct, status_code=404
            )
        if component is None:
            msg = 'Component of type "%s" not found or not exported.' % ct
            raise dci_exc.DCIException(msg, status_code=412)

        if str(component.id) in _components_ids:
            msg = ('Component types %s malformed: type %s duplicated.' %
                   (component_types, ct))
            raise dci_exc.DCIException(msg, status_code=412)
        _components.append(component)
        _components_ids.append(str(component.id))
    return _components


def verify_and_get_components_ids(topic_id, components_ids, component_types,
                                  session=None):
    """Process some verifications of the provided components ids."""
    session = session or flask.g.session
    if len(components_ids) != len(component_types):
        msg = 'The number of component ids does not match the number ' \
              'of component types %s' % component_types
        raise dci_exc.DCIException(msg, status_code=412)

    # get the components from their ids
    schedule_component_types = set()
    for c_id in components_ids:
        try:
            component = session.query(models2.Component).filter(
                sql.and_(models2.Component.id == c_id,
                         models2.Component.topic_id == topic_id,
                         models2.Component.state == 'active')
            ).one()
        except sa_orm.exc.NoResultFound:
            raise dci_exc.DCIException(
                message="component id %s not found or not exported" % c_id, status_code=404
            )

        if component.type in schedule_component_types:
            msg = 'Component types malformed: type %s duplicated.' % component.type
            raise dci_exc.DCIException(msg, status_code=412)
        schedule_component_types.add(component.type)
    return components_ids


def get_schedule_components_ids(topic_id, component_types, components_ids):
    if components_ids == []:
        return [c.id for c in get_last_components_by_type(
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


# TODO-ORM: already provided by /components/<uuid:c_id>, will be
# removed along with JOIN_COMPONENTS_TAGS
@api.route('/components/<uuid:c_id>/tags', methods=['GET'])
@decorators.login_required
def retrieve_tags_from_component(user, c_id):
    """Retrieve all tags attached to a component."""
    component = v1_utils.verify_existence_and_get(c_id, _TABLE)
    component_team_id = component['team_id']
    if component_team_id is not None:
        if user.is_not_in_team(component_team_id):
            dci_exc.Unauthorized()

    JCT = models.JOIN_COMPONENTS_TAGS
    query = (sql.select([models.TAGS])
             .select_from(JCT.join(models.TAGS))
             .where(JCT.c.component_id == c_id))
    rows = flask.g.db_conn.execute(query)

    return flask.jsonify({'tags': rows, '_meta': {'count': rows.rowcount}})


@api.route('/components/<uuid:c_id>/tags', methods=['POST'])
@decorators.login_required
def add_tag_to_component(user, c_id):
    """Add a tag on a specific component."""

    component = base.get_resource_orm(models2.Component, c_id)
    _verify_component_and_topic_access(user, component)

    values = {}
    values['etag'] = utils.gen_etag()
    tag_name = flask.request.json.get('name')
    if tag_name and tag_name not in component.tags:
        tag_name = [tag_name]
        values['tags'] = component.tags + tag_name
        base.update_resource_orm(component, values)

    return flask.Response(None, 201, content_type='application/json')


@api.route('/components/<uuid:c_id>/tags', methods=['DELETE'])
@decorators.login_required
def delete_tag_from_component(user, c_id):
    """Delete a tag from a specific component."""

    component = base.get_resource_orm(models2.Component, c_id)
    _verify_component_and_topic_access(user, component)
    values = {}
    values['etag'] = utils.gen_etag()
    tag_name = flask.request.json.get('name')
    tag_name = [tag_name] if tag_name else []
    values['tags'] = list(set(component.tags) - set(tag_name))
    base.update_resource_orm(component, values)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/components/purge', methods=['GET'])
@decorators.login_required
def get_to_purge_archived_components(user):
    return base.get_resources_to_purge_orm(user, models2.Component)


@api.route('/components/purge', methods=['POST'])
@decorators.login_required
def purge_archived_components(user):

    # get all archived components
    archived_components = base.get_resources_to_purge_orm(user, models2.Component).json['components']

    store = dci_config.get_store('components')

    # for each component delete it and all the component_files associated
    # from within a transaction
    # if the SQL deletion or the Store deletion fail then
    # rollback the transaction, otherwise commit.
    for cmpt in archived_components:
        get_cmpt_files = flask.g.session.query(models2.Componentfile)
        get_cmpt_files = get_cmpt_files.filter(models2.Componentfile.component_id == cmpt['id'])
        cmpt_files = get_cmpt_files.all()
        for cmpt_file in cmpt_files:
            file_path = files_utils.build_file_path(cmpt['topic_id'],
                                                    cmpt['id'],
                                                    cmpt_file.id)
            try:
                store.delete(file_path)
                flask.g.session.query(models2.Componentfile).filter(models2.Componentfile.id == cmpt_file.id).delete()
                flask.g.session.commit()
            except Exception as e:
                logger.error('Error while removing component file %s, message: %s'
                             % (file_path, str(e)))
                flask.g.session.rollback()
                raise dci_exc.DCIException(str(e))
        flask.g.session.query(models2.Component).filter(models2.Component.id == cmpt['id']).delete()
        flask.g.session.commit()
    return flask.Response(None, 204, content_type='application/json')
