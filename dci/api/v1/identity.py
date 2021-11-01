# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import base
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    clean_json_with_schema,
    update_current_user_schema
)
from dci.common import utils
from dci.db import models2
from dci import decorators


# TODO: replace this properly with JSONEncoder
def _encode_dict(_dict):
    res = {}
    for d in _dict:
        _values = {}
        for i in _dict[d]:
            _values[str(i)] = _dict[d][i]
        res[str(d)] = _values
    return res


@api.route('/identity', methods=['GET'])
@decorators.login_required
def get_identity(identity):
    """Returns some information about the currently authenticated identity"""
    return flask.Response(
        json.dumps(
            {
                'identity': {
                    'id': identity.id,
                    'etag': identity.etag,
                    'name': identity.name,
                    'fullname': identity.fullname,
                    'email': identity.email,
                    'timezone': identity.timezone,
                    'teams': _encode_dict(identity.teams)
                }
            }
        ), 200,
        headers={'ETag': identity.etag},
        content_type='application/json'
    )


@api.route('/identity', methods=['PUT'])
@decorators.login_required
def put_identity(user):
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = clean_json_with_schema(update_current_user_schema, flask.request.json)

    if user.is_not_read_only_user():
        current_password = values['current_password']
        encrypted_password = user.password
        if not auth.check_passwords_equal(current_password,
                                          encrypted_password):
            raise dci_exc.DCIException('current_password invalid')

    new_values = {}
    new_password = values.get('new_password')
    if new_password:
        encrypted_password = auth.hash_password(new_password)
        new_values['password'] = encrypted_password

    etag = utils.gen_etag()
    new_values.update({'etag': etag,
                       'fullname': values.get('fullname') or user.fullname,
                       'email': values.get('email') or user.email,
                       'timezone': values.get('timezone') or user.timezone})

    try:
        flask.g.session.query(models2.User).\
            filter(sql.and_(models2.User.id == user.id, models2.User.etag == if_match_etag)).update(new_values)
        flask.g.session.commit()
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e), status_code=409)

    user = base.get_resource_orm(models2.User, user.id)
    user_serialized = user.serialize()

    return flask.Response(
        json.dumps({'user': user_serialized}), 200, headers={'ETag': etag},
        content_type='application/json'
    )
