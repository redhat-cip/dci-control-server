# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
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


import server.db.api as api
from server.db.models import Base
from server.db.models import engine
from server.db.models import metadata

from eve import Eve
from eve_sqlalchemy.decorators import registerSchema
from eve_sqlalchemy import SQL
from eve_sqlalchemy.validation import ValidatorSQL
from eve.utils import config
from flask import jsonify

config.ID_FIELD = 'id'
config.ITEM_URL = 'regex("[-a-z0-9]{36,64}")'

DOMAIN = {}
for table in metadata.tables:
    print("table: %s" % table)
    DB = getattr(Base.classes, table)
    registerSchema(table)(DB)
    DOMAIN[table] = DB._eve_schema[table]
    DOMAIN[table].update({
        'id_field': config.ID_FIELD,
        'item_url': config.ITEM_URL,
        'item_lookup_field': config.ID_FIELD,
    })
    if hasattr(DB, 'name'):
        DOMAIN[table].update({
            'additional_lookup': {
                'url': 'regex("[\S]+")',
                'field': 'name'
            }})
    from pprint import pprint
    pprint(DOMAIN[table])

SETTINGS = {
    'DOMAIN': DOMAIN,
    'SQLALCHEMY_DATABASE_URI':
        "postgresql://boa:boa@127.0.0.1/dci_control_server",
    'DEBUG': True,
}

app = Eve(settings=SETTINGS, validator=ValidatorSQL, data=SQL)
db = app.data.driver
Base.metadata.bind = engine
db.Model = Base


def site_map():
    from pprint import pprint
    for rule in app.url_map.iter_rules():
        pprint(rule)

site_map()


@app.route('/jobs/get_job_by_platform/<platform_id>')
def get_job_by_platform(platform_id):
    return jsonify(api.get_job_by_platform(platform_id))


app.run(debug=True)
