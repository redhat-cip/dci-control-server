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
from sqlalchemy import sql, func
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
    rconfiguration_schema,
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
_RCONFIGURATIONS = models.REMOTECIS_RCONFIGURATIONS
_RCONFIGURATIONS_COLUMNS = v1_utils.get_columns_name_with_objects(
    _RCONFIGURATIONS)


@api.route('/remotecis', methods=['POST'])
@decorators.login_required
def create_remotecis(user):
    values = flask.request.json
    check_json_is_valid(create_remoteci_schema, values)
    values.update(v1_utils.common_values_dict())

    if user.is_not_in_team(values['team_id']):
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

    if user.is_not_super_admin() and not user.is_read_only_user():
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
    if user.is_not_in_team(remoteci['team_id']):
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

    if not user.is_in_team(remoteci['team_id']):
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

    if not user.is_in_team(remoteci['team_id']):
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

    if user.is_not_super_admin():
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

    if user.is_not_in_team(remoteci['team_id']):
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
    remoteci = v1_utils.verify_existence_and_get(r_id, _TABLE)

    if u_id != user.id and \
       not user.is_in_team(remoteci['team_id']) and \
       user.is_regular_user():
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

    if not user.is_in_team(remoteci['team_id']):
        raise dci_exc.Unauthorized()

    return base.refresh_api_secret(user, remoteci, _TABLE)

# Remotecis configurations controllers


@api.route('/remotecis/<uuid:r_id>/rconfigurations', methods=['POST'])
@decorators.login_required
def create_configuration(user, r_id):
    values = flask.request.json
    check_json_is_valid(rconfiguration_schema, values)
    values.update(v1_utils.common_values_dict())

    remoteci = v1_utils.verify_existence_and_get(r_id, _TABLE)

    if user.is_not_in_team(remoteci['team_id']):
        raise dci_exc.Unauthorized()

    rconfiguration_id = values.get('id')

    with flask.g.db_conn.begin():
        try:
            # insert configuration
            query = _RCONFIGURATIONS.insert().\
                values(**values)
            flask.g.db_conn.execute(query)
            # insert join between rconfiguration and remoteci
            values_join = {
                'rconfiguration_id': rconfiguration_id,
                'remoteci_id': r_id}
            query = models.JOIN_REMOTECIS_RCONFIGURATIONS.insert().\
                values(**values_join)
            flask.g.db_conn.execute(query)
        except sa_exc.IntegrityError as ie:
            raise dci_exc.DCIException('Integrity Error: %s' % str(ie))

    return flask.Response(
        json.dumps({'rconfiguration': values}), 201,
        headers={'ETag': values['etag']},
        content_type='application/json'
    )


@api.route('/remotecis/<uuid:r_id>/rconfigurations', methods=['GET'])
@decorators.login_required
def get_all_configurations(user, r_id):
    args = check_and_get_args(flask.request.args.to_dict())

    remoteci = v1_utils.verify_existence_and_get(r_id, _TABLE)
    if not user.is_in_team(remoteci['team_id']):
        raise dci_exc.Unauthorized()

    query = sql.select([_RCONFIGURATIONS]). \
        select_from(models.JOIN_REMOTECIS_RCONFIGURATIONS.
                    join(_RCONFIGURATIONS)). \
        where(models.JOIN_REMOTECIS_RCONFIGURATIONS.c.remoteci_id == r_id)

    query = query.where(_RCONFIGURATIONS.c.state != 'archived')

    sort_list = v1_utils.sort_query(args['sort'], _RCONFIGURATIONS_COLUMNS)
    where_list = v1_utils.where_query(args['where'],
                                      _RCONFIGURATIONS,
                                      _RCONFIGURATIONS_COLUMNS)

    query = v1_utils.add_sort_to_query(query, sort_list)
    query = v1_utils.add_where_to_query(query, where_list)
    if args.get('limit', None):
        query = query.limit(args.get('limit'))
    if args.get('offset', None):
        query = query.offset(args.get('offset'))

    rows = flask.g.db_conn.execute(query).fetchall()

    query_nb_rows = sql.select([func.count(_RCONFIGURATIONS.c.id)]). \
        select_from(models.JOIN_REMOTECIS_RCONFIGURATIONS.
                    join(_RCONFIGURATIONS)). \
        where(models.JOIN_REMOTECIS_RCONFIGURATIONS.c.remoteci_id == r_id). \
        where(_RCONFIGURATIONS.c.state != 'archived')
    nb_rows = flask.g.db_conn.execute(query_nb_rows).scalar()

    res = flask.jsonify({'rconfigurations': rows,
                         '_meta': {'count': nb_rows}})
    res.status_code = 200
    return res


@api.route('/remotecis/<uuid:r_id>/rconfigurations/<uuid:c_id>',
           methods=['GET'])
@decorators.login_required
def get_configuration_by_id(user, r_id, c_id):
    v1_utils.verify_existence_and_get(r_id, _TABLE)
    configuration = v1_utils.verify_existence_and_get(c_id, _RCONFIGURATIONS)
    return base.get_resource_by_id(user, configuration, _RCONFIGURATIONS, None,
                                   resource_name='rconfiguration')


@api.route('/remotecis/<uuid:r_id>/rconfigurations/<uuid:c_id>',
           methods=['DELETE'])
@decorators.login_required
def delete_configuration_by_id(user, r_id, c_id):
    remoteci = v1_utils.verify_existence_and_get(r_id, models.REMOTECIS)
    v1_utils.verify_existence_and_get(c_id, _RCONFIGURATIONS)

    if not user.is_in_team(remoteci['team_id']):
        raise dci_exc.Unauthorized()

    with flask.g.db_conn.begin():
        values = {'state': 'archived'}
        query = _RCONFIGURATIONS.update().where(
            _RCONFIGURATIONS.c.id == c_id).values(**values)

        result = flask.g.db_conn.execute(query)

        if not result.rowcount:
            raise dci_exc.DCIDeleteConflict('rconfiguration', c_id)

    return flask.Response(None, 204, content_type='application/json')


def get_last_rconfiguration_id(topic_id, remoteci_id, db_conn=None):
    """Get the rconfiguration_id of the last job run by the remoteci.

    :param topic_id: the topic
    :param remoteci_id: the remoteci id
    :return: last rconfiguration_id of the remoteci
    """
    db_conn = db_conn or flask.g.db_conn
    __TABLE = models.JOBS
    query = sql.select([__TABLE.c.rconfiguration_id]). \
        order_by(sql.desc(__TABLE.c.created_at)). \
        where(sql.and_(__TABLE.c.topic_id == topic_id,
                       __TABLE.c.remoteci_id == remoteci_id)). \
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


@api.route('/remotecis/rconfigurations/purge', methods=['GET'])
@decorators.login_required
def get_to_purge_archived_rconfigurations(user):
    return base.get_to_purge_archived_resources(user, _RCONFIGURATIONS)


@api.route('/remotecis/rconfigurations/purge', methods=['POST'])
@decorators.login_required
def purge_archived_rconfigurations(user):
    return base.purge_archived_resources(user, _RCONFIGURATIONS)
