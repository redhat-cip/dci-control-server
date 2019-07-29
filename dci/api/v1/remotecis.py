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
import flask
import re
from datetime import datetime, timedelta
from flask import json
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql
from OpenSSL import crypto

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci import dci_config
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    check_json_is_valid,
    create_remoteci_schema,
    update_remoteci_schema,
    check_and_get_args
)

from dci.common import signature
from dci.common import utils
from dci.db import embeds
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.REMOTECIS
_VALID_EMBED = embeds.remotecis()
_R_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {
    'team': False,
    'users': True
}


@api.route('/remotecis', methods=['POST'])
@decorators.login_required
def create_remotecis(user):
    values = flask.request.json
    check_json_is_valid(create_remoteci_schema, values)
    values.update(v1_utils.common_values_dict())

    if user.is_not_in_team(values['team_id']) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    values.update({
        'data': values.get('data', {}),
        # XXX(fc): this should be populated as a default value from the
        # model, but we don't return values from the database :(
        'api_secret': signature.gen_secret()
    })

    query = _TABLE.insert().values(**values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    return flask.Response(
        json.dumps({'remoteci': values}), 201,
        headers={'ETag': values['etag']}, content_type='application/json'
    )


@api.route('/remotecis', methods=['GET'])
@decorators.login_required
def get_all_remotecis(user, t_id=None):
    args = check_and_get_args(flask.request.args.to_dict())

    # build the query thanks to the QueryBuilder class
    query = v1_utils.QueryBuilder(_TABLE, args, _R_COLUMNS,
                                  ignore_columns=['keys', 'cert_fp'])

    if (user.is_not_super_admin() and user.is_not_read_only_user()
        and user.is_not_epm()):
        query.add_extra_condition(_TABLE.c.team_id.in_(user.teams_ids))

    if t_id is not None:
        query.add_extra_condition(_TABLE.c.team_id == t_id)

    query.add_extra_condition(_TABLE.c.state != 'archived')

    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)

    return flask.jsonify({'remotecis': rows, '_meta': {'count': len(rows)}})


@api.route('/remotecis/<uuid:r_id>', methods=['GET'])
@decorators.login_required
def get_remoteci_by_id(user, r_id):
    remoteci = v1_utils.verify_existence_and_get(r_id, _TABLE)
    if user.is_not_in_team(remoteci['team_id']) and user.is_not_epm():
        raise dci_exc.DCINotFound('RemoteCI', remoteci['id'])
    return base.get_resource_by_id(user, remoteci, _TABLE, _EMBED_MANY,
                                   ignore_columns=["keys", "cert_fp"])


@api.route('/remotecis/<uuid:r_id>', methods=['PUT'])
@decorators.login_required
def put_remoteci(user, r_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = flask.request.json
    check_json_is_valid(update_remoteci_schema, values)

    remoteci = v1_utils.verify_existence_and_get(r_id, _TABLE)

    if user.is_not_in_team(remoteci['team_id']) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    values['etag'] = utils.gen_etag()
    where_clause = sql.and_(_TABLE.c.etag == if_match_etag,
                            _TABLE.c.state != 'archived',
                            _TABLE.c.id == r_id)

    query = (_TABLE
             .update()
             .returning(*_TABLE.columns)
             .where(where_clause)
             .values(**values))

    result = flask.g.db_conn.execute(query)
    if not result.rowcount:
        raise dci_exc.DCIConflict('RemoteCI', r_id)

    _result = dict(result.fetchone())
    del _result['api_secret']

    return flask.Response(
        json.dumps({'remoteci': _result}), 200,
        headers={'ETag': values['etag']}, content_type='application/json'
    )


@api.route('/remotecis/<uuid:remoteci_id>', methods=['DELETE'])
@decorators.login_required
def delete_remoteci_by_id(user, remoteci_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    remoteci = v1_utils.verify_existence_and_get(remoteci_id, _TABLE)

    if user.is_not_in_team(remoteci['team_id']) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    with flask.g.db_conn.begin():
        values = {'state': 'archived'}
        where_clause = sql.and_(
            _TABLE.c.etag == if_match_etag,
            _TABLE.c.id == remoteci_id
        )
        query = _TABLE.update().where(where_clause).values(**values)

        result = flask.g.db_conn.execute(query)

        if not result.rowcount:
            raise dci_exc.DCIDeleteConflict('RemoteCI', remoteci_id)

        for model in [models.JOBS]:
            query = model.update().where(model.c.remoteci_id == remoteci_id) \
                         .values(**values)
            flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/remotecis/<uuid:r_id>/data', methods=['GET'])
@decorators.login_required
def get_remoteci_data(user, r_id):
    remoteci_data = get_remoteci_data_json(user, r_id)

    if 'keys' in 'keys' in flask.request.args:
        keys = flask.request.args.get('keys').split(',')
        remoteci_data = {k: remoteci_data[k] for k in keys
                         if k in remoteci_data}

    return flask.jsonify(remoteci_data)


def get_remoteci_data_json(user, r_id):
    query = v1_utils.QueryBuilder(_TABLE, {}, _R_COLUMNS)

    if user.is_not_super_admin() and user.is_not_epm():
        query.add_extra_condition(_TABLE.c.team_id.in_(user.teams_ids))

    query.add_extra_condition(_TABLE.c.id == r_id)
    row = query.execute(fetchone=True)

    if row is None:
        raise dci_exc.DCINotFound('RemoteCI', r_id)

    return row['remotecis_data']


@api.route('/remotecis/<uuid:r_id>/users', methods=['POST'])
@decorators.login_required
def add_user_to_remoteci(user, r_id):
    remoteci = v1_utils.verify_existence_and_get(r_id, _TABLE)

    if user.is_not_in_team(remoteci['team_id']) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    query = models.JOIN_USER_REMOTECIS.insert().values({'user_id': user.id,
                                                        'remoteci_id': r_id})
    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name,
                                          'remoteci_id, user_id')
    result = json.dumps({'user_id': user.id, 'remoteci_id': r_id})
    return flask.Response(result, 201, content_type='application/json')


@api.route('/remotecis/<uuid:r_id>/users', methods=['GET'])
@decorators.login_required
def get_all_users_from_remotecis(user, r_id):
    v1_utils.verify_existence_and_get(r_id, _TABLE)

    JUR = models.JOIN_USER_REMOTECIS
    query = (sql.select([models.USERS])
             .select_from(JUR.join(models.USERS))
             .where(JUR.c.remoteci_id == r_id))
    rows = flask.g.db_conn.execute(query)

    res = flask.jsonify({'users': rows,
                         '_meta': {'count': rows.rowcount}})
    return res


@api.route('/remotecis/<uuid:r_id>/users/<uuid:u_id>', methods=['DELETE'])
@decorators.login_required
def delete_user_from_remoteci(user, r_id, u_id):
    v1_utils.verify_existence_and_get(r_id, _TABLE)

    if str(u_id) != user.id and user.is_not_epm():
        raise dci_exc.Unauthorized()

    JUR = models.JOIN_USER_REMOTECIS
    where_clause = sql.and_(JUR.c.remoteci_id == r_id,
                            JUR.c.user_id == u_id)
    query = JUR.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('User', u_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/remotecis/purge', methods=['GET'])
@decorators.login_required
def get_to_purge_archived_remotecis(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/remotecis/purge', methods=['POST'])
@decorators.login_required
def purge_archived_remotecis(user):
    return base.purge_archived_resources(user, _TABLE)


@api.route('/remotecis/<uuid:r_id>/api_secret', methods=['PUT'])
@decorators.login_required
def put_api_secret(user, r_id):
    utils.check_and_get_etag(flask.request.headers)
    remoteci = v1_utils.verify_existence_and_get(r_id, _TABLE)

    if user.is_not_in_team(remoteci['team_id']) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    return base.refresh_api_secret(user, remoteci, _TABLE)


def kill_existing_jobs(remoteci_id, db_conn=None):
    db_conn = db_conn or flask.g.db_conn
    yesterday = datetime.now() - timedelta(hours=24)
    where_clause = sql.expression.and_(
        models.JOBS.c.remoteci_id == remoteci_id,
        models.JOBS.c.status.in_(('new', 'pre-run', 'running', 'post-run')),
        models.JOBS.c.created_at < yesterday
    )
    kill_query = models.JOBS.update().where(where_clause).values(
        status='killed')
    db_conn.execute(kill_query)


@api.route('/remotecis/<uuid:r_id>/keys', methods=['PUT'])
@decorators.login_required
def update_remoteci_keys(user, r_id):
    _CAKEY = dci_config.generate_conf()['CA_KEY']
    _CACERT = dci_config.generate_conf()['CA_CERT']

    etag = utils.check_and_get_etag(flask.request.headers)
    remoteci = v1_utils.verify_existence_and_get(r_id, _TABLE)

    key, cert = v1_utils.get_key_and_cert_signed(_CAKEY, _CACERT)

    values = {}
    keys = {'key': crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                          key).decode('utf-8'),
            'cert': crypto.dump_certificate(crypto.FILETYPE_PEM,
                                            cert).decode('utf-8')}
    where_clause = sql.and_(_TABLE.c.etag == etag,
                            _TABLE.c.state != 'archived',
                            _TABLE.c.id == remoteci['id'])

    values['etag'] = utils.gen_etag()
    values['cert_fp'] = re.sub(':', '',
                               cert.digest('sha1').decode('utf-8')).lower()

    query = (_TABLE
             .update()
             .where(where_clause)
             .values(**values))

    flask.g.db_conn.execute(query)

    return flask.Response(
        json.dumps({'keys': keys}), 201,
        content_type='application/json'
    )
