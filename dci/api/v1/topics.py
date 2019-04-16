# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Red Hat, Inc
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
from flask import json
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import components
from dci.api.v1 import export_control
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.TOPICS
_VALID_EMBED = embeds.topics()
_T_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {
    'teams': True,
    'product': False,
    'next_topic': False,
}


@api.route('/topics', methods=['POST'])
@decorators.login_required
def create_topics(user):
    values = v1_utils.common_values_dict()
    values.update(schemas.topic.post(flask.request.json))

    product = v1_utils.verify_existence_and_get(values['product_id'],
                                                models.PRODUCTS)
    team_product_id = product['team_id']

    if user.is_not_super_admin() and user.is_not_in_team(team_product_id):
        raise dci_exc.Unauthorized()

    # todo(yassine): enabled when client updated.
    # if values['component_types'] == []:
    #     raise dci_exc.DCIException('component_types should not be void')

    query = _TABLE.insert().values(**values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    result = json.dumps({'topic': values})
    return flask.Response(result, 201, headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/topics/<uuid:topic_id>', methods=['GET'])
@decorators.login_required
def get_topic_by_id(user, topic_id):
    args = schemas.args(flask.request.args.to_dict())
    topic = v1_utils.verify_existence_and_get(topic_id, _TABLE)
    product = v1_utils.verify_existence_and_get(topic['product_id'],
                                                models.PRODUCTS)

    if user.is_not_super_admin() and user.is_not_in_team(product['team_id']):
        if not user.is_read_only_user():
            v1_utils.verify_team_in_topic(user, topic_id)
        if 'teams' in args['embed']:
            raise dci_exc.Unauthorized()

    return base.get_resource_by_id(user, topic, _TABLE, _EMBED_MANY)


@api.route('/topics', methods=['GET'])
@decorators.login_required
def get_all_topics(user):
    args = schemas.args(flask.request.args.to_dict())
    # if the user is an admin then he can get all the topics
    query = v1_utils.QueryBuilder(_TABLE, args, _T_COLUMNS)

    if user.is_not_super_admin() and user.is_not_read_only_user():
        if 'teams' in args['embed']:
            raise dci_exc.DCIException('embed=teams not authorized.',
                                       status_code=401)
        query.add_extra_condition(_TABLE.c.id.in_(v1_utils.user_topic_ids(user)))  # noqa

    query.add_extra_condition(_TABLE.c.state != 'archived')

    # get the number of rows for the '_meta' section
    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)

    return flask.jsonify({'topics': rows, '_meta': {'count': nb_rows}})


@api.route('/topics/<uuid:topic_id>', methods=['PUT'])
@decorators.login_required
def put_topic(user, topic_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = schemas.topic.put(flask.request.json)
    topic = v1_utils.verify_existence_and_get(topic_id, _TABLE)
    product = v1_utils.verify_existence_and_get(topic['product_id'],
                                                models.PRODUCTS)

    if user.is_not_super_admin() and user.is_not_in_team(product['team_id']):
        raise dci_exc.Unauthorized()

    n_topic = None
    if values.get('next_topic_id'):
        n_topic = v1_utils.verify_existence_and_get(values['next_topic_id'],
                                                    _TABLE)
        product = v1_utils.verify_existence_and_get(n_topic['product_id'],
                                                    models.PRODUCTS)

        if (user.is_not_super_admin() and
            user.is_not_in_team(product['team_id'])):
            raise dci_exc.Unauthorized()

    values['etag'] = utils.gen_etag()
    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == topic_id
    )
    query = _TABLE.update().returning(*_TABLE.columns).\
        where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)
    if not result.rowcount:
        raise dci_exc.DCIConflict('Topic', topic_id)

    return flask.Response(
        json.dumps({'topic': result.fetchone()}), 200,
        headers={'ETag': values['etag']},
        content_type='application/json'
    )


@api.route('/topics/<uuid:topic_id>', methods=['DELETE'])
@decorators.login_required
def delete_topic_by_id(user, topic_id):
    topic = v1_utils.verify_existence_and_get(topic_id, _TABLE)
    product = v1_utils.verify_existence_and_get(topic['product_id'],
                                                models.PRODUCTS)
    if user.is_not_super_admin() and user.is_not_in_team(product['team_id']):
        raise dci_exc.Unauthorized()

    topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE, get_id=True)

    with flask.g.db_conn.begin():
        values = {'state': 'archived'}
        where_clause = sql.and_(_TABLE.c.id == topic_id)
        query = _TABLE.update().where(where_clause).values(**values)

        result = flask.g.db_conn.execute(query)

        if not result.rowcount:
            raise dci_exc.DCIDeleteConflict('Topic', topic_id)

        query = models.COMPONENTS.update().where(
            models.COMPONENTS.c.topic_id == topic_id).values(**values)
        flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type='application/json')


# component GET
@api.route('/topics/<uuid:topic_id>/components', methods=['GET'])
@decorators.login_required
def get_all_components(user, topic_id):
    topic = v1_utils.verify_existence_and_get(topic_id, _TABLE)
    export_control.verify_access_to_topic(user, topic)
    return components.get_all_components(user, topic_id=topic['id'])


@api.route('/topics/<uuid:topic_id>/components/latest', methods=['GET'])
@decorators.login_required
def get_latest_component_per_topic(user, topic_id):
    topic = v1_utils.verify_existence_and_get(topic_id, _TABLE)
    export_control.verify_access_to_topic(user, topic)

    last_component = None
    latest_components = components._get_latest_components()
    for component in latest_components:
        if component['topic_id'] == topic['id']:
            last_component = component
            break

    return flask.jsonify({'component': last_component})


# teams set apis
@api.route('/topics/<uuid:topic_id>/teams', methods=['POST'])
@decorators.login_required
def add_team_to_topic(user, topic_id):
    # TODO(yassine): use voluptuous schema
    data_json = flask.request.json
    team_id = data_json.get('team_id')

    topic = v1_utils.verify_existence_and_get(topic_id, _TABLE)
    team_id = v1_utils.verify_existence_and_get(team_id, models.TEAMS,
                                                get_id=True)

    product = v1_utils.verify_existence_and_get(topic['product_id'],
                                                models.PRODUCTS)
    team_product_id = product['team_id']

    if (user.is_not_super_admin() and
        user.is_not_in_team(team_product_id) and
        user.is_not_product_owner(team_id)):
        raise dci_exc.Unauthorized()

    values = {'topic_id': topic['id'],
              'team_id': team_id}
    query = models.JOINS_TOPICS_TEAMS.insert().values(**values)
    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(models.JOINS_TOPICS_TEAMS.name,
                                          'team_id, topic_id')

    result = json.dumps(values)
    return flask.Response(result, 201, content_type='application/json')


@api.route('/topics/<uuid:topic_id>/teams/<uuid:team_id>', methods=['DELETE'])
@decorators.login_required
def delete_team_from_topic(user, topic_id, team_id):
    topic = v1_utils.verify_existence_and_get(topic_id, _TABLE)
    team_id = v1_utils.verify_existence_and_get(team_id, models.TEAMS,
                                                get_id=True)
    product = v1_utils.verify_existence_and_get(topic['product_id'],
                                                models.PRODUCTS)

    if user.is_not_super_admin() and user.is_not_in_team(product['team_id']):
        raise dci_exc.Unauthorized()

    JTT = models.JOINS_TOPICS_TEAMS
    where_clause = sql.and_(JTT.c.topic_id == topic['id'],
                            JTT.c.team_id == team_id)
    query = JTT.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Topics_teams', team_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/topics/<uuid:topic_id>/teams', methods=['GET'])
@decorators.login_required
def get_all_teams_from_topic(user, topic_id):
    topic = v1_utils.verify_existence_and_get(topic_id, _TABLE)

    if user.is_not_super_admin() and \
            not user.product_id == topic['product_id']:
        raise dci_exc.Unauthorized()

    # Get all teams which belongs to a given topic
    JTT = models.JOINS_TOPICS_TEAMS
    query = (sql.select([models.TEAMS])
             .select_from(JTT.join(models.TEAMS))
             .where(JTT.c.topic_id == topic['id']))
    rows = flask.g.db_conn.execute(query)

    return flask.jsonify({'teams': rows,
                          '_meta': {'count': rows.rowcount}})


@api.route('/topics/purge', methods=['GET'])
@decorators.login_required
def get_to_purge_archived_topics(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/topics/purge', methods=['POST'])
@decorators.login_required
def purge_archived_topics(user):
    return base.purge_archived_resources(user, _TABLE)
