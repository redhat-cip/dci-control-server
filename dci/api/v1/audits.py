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

from dci.api.v1 import api
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.LOGS
_A_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


@api.route('/audits', methods=['GET'])
@decorators.login_required
def get_logs(user):
    args = schemas.args(flask.request.args.to_dict())

    if args['limit'] is None:
        args['limit'] = 10

    query = v1_utils.QueryBuilder(_TABLE, args, _A_COLUMNS)

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'], None)

    return flask.jsonify({'audits': rows, '_meta': {'count': nb_rows}})
