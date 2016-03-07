# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
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
import json

from dci.api.v1 import api
from dci.api.v1 import teams
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import schemas
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.LOGS
_T_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


@api.route('/audits', methods=['GET'])
@auth.requires_auth
def get_logs(user):
    args = schemas.args(flask.request.args.to_dict())

    team_id = json.loads(teams.get_all_teams().data)['teams'][0]['id']

    if not auth.is_admin(user) and not auth.is_admin_user(user, team_id):
        raise auth.UNAUTHORIZED

    if args['limit'] is None:
        args['limit'] = 10

    if not args['sort']:
        args['sort'] = ["-created_at"]

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'])
    q_bd.sort = v1_utils.sort_query(args['sort'], _T_COLUMNS)

    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == team_id)

    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()

    return flask.jsonify({'audits': rows, '_meta': {'count': nb_row}})
