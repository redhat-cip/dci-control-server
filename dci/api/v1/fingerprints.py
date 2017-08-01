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
from sqlalchemy import sql
from sqlalchemy import exc as sa_exc
from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import models


_TABLE = models.FINGERPRINTS
_T_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {}

@api.route('/fingerprints', methods=['POST'])
@decorators.login_required
def create_fingerprint(user):
    """Create Fingerprint.
    """
    values = v1_utils.common_values_dict(user)
    values.update(schemas.fingerprint.post(flask.request.json))

    with flask.g.db_conn.begin():
        query = _TABLE.insert().values(**values)
        flask.g.db_conn.execute(query)

    return flask.Response(json.dumps({'fingerprint': values}), 201,
                          headers={'ETag': values['etag']},
                          content_type='application/json')

@api.route('/fingerprints', methods=['GET'])
@decorators.login_required
def get_all_fingerprints(user):
    """Get all Fingerprint.
    """
    args = schemas.args(flask.request.args.to_dict())

    query = v1_utils.QueryBuilder(_TABLE, args, _T_COLUMNS)

    query.add_extra_condition(_TABLE.c.state != 'archived')

    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name)

    return flask.jsonify({'fingerprints': rows, '_meta': {'count': nb_rows}})

@api.route('/fingerprints/<uuid:fp_id>', methods=['GET'])
@decorators.login_required
def get_fingerprint_by_id(user, fp_id):
    """Get Fingerprint by id.
    """
    fp = v1_utils.verify_existence_and_get(fp_id, _TABLE)
    return base.get_resource_by_id(user, fp,
                                   _TABLE, _EMBED_MANY)

@api.route('/fingerprints/<uuid:fp_id>', methods=['PUT'])
@decorators.login_required
def modify_fingerprint(user, fp_id):
    """... Fingerprint.
    """

@api.route('/fingerprints/<uuid:fp_id>', methods=['DELETE'])
@decorators.login_required
def delete_fingerprint_by_id(user, fp_id):
    """... Fingerprint.
    """

@api.route('/fingerprints/purge', methods=['GET'])
@decorators.login_required
def get_to_purge_archived_fingerprint(user):
    """... Fingerprint.
    """

@api.route('/fingerprints/purge', methods=['POST'])
@decorators.login_required
def purge_fingerprint(user):
    """... Fingerprint.
    """
