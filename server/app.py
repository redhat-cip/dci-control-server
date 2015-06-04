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

import flask
import json
from pprint import pprint

import server.auth
import server.db.api as api
from server.db.models import Base
from server.db.models import engine
from server.db.models import Job
from server.db.models import session
from server.db.models import TestVersion

from eve import Eve
from eve_sqlalchemy import SQL
from eve_sqlalchemy.validation import ValidatorSQL
from flask import abort
from sqlalchemy.sql import text

from dci_databrowser import dci_databrowser

import os

app_py_dir = os.path.dirname(os.path.realpath(__file__))
settings_file = os.path.join(app_py_dir, 'settings.py')
app = Eve(settings=settings_file, validator=ValidatorSQL,
          data=SQL, auth=server.auth.DCIBasicAuth)
db = app.data.driver
Base.metadata.bind = engine
db.Model = Base


def site_map():
    for rule in app.url_map.iter_rules():
        pprint(rule)


def load_docs(app):
    try:
        from eve_docs import eve_docs
        from flask.ext.bootstrap import Bootstrap
        Bootstrap(app)
        app.register_blueprint(eve_docs, url_prefix='/docs')
    except ImportError:
        print("Failed to load eve_docs.")


def pick_jobs(documents):
    query = text(
        """
SELECT
    testversions.id
FROM
    testversions, remotecis
WHERE testversions.id NOT IN (
    SELECT
        jobs.testversion_id
    FROM jobs
    WHERE jobs.remoteci_id=:remoteci_id
) AND testversions.test_id=remotecis.test_id AND remotecis.id=:remoteci_id
LIMIT 1""")

    for d in documents:
        if 'testversion_id' in d:
            continue
        r = engine.execute(query, remoteci_id=d['remoteci_id']).fetchone()
        if r is None:
            abort(412, "No test to run left.")
        testversion = session.query(TestVersion).get(str(r[0]))
        d['testversion_id'] = testversion.id


def aggregate_job_data(response):
    data = {}
    job = session.query(Job).get(response['id'])
    my_datas = (
        job.testversion.version.product.data,
        job.testversion.version.data,
        job.testversion.test.data,
        job.remoteci.data)
    for my_data in my_datas:
        if my_data:
            data = api.dict_merge(data, my_data)
    response['data'] = data


def set_real_owner(resource, items):
    """Hack to allow the 'admin' user to change the team_id."""
    if flask.request.authorization.username != 'admin':
        return
    # NOTE(Gonéri): the fields returned by flask.request.get_json() are
    # already mangled by the Role Based Access Control.
    request_fields = json.loads(flask.request.data.decode('utf-8'))
    if "team_id" in request_fields:
        items[0]['team_id'] = request_fields['team_id']

app.on_insert += set_real_owner
app.on_insert_jobs += pick_jobs
app.on_fetched_item_jobs += aggregate_job_data

app.register_blueprint(dci_databrowser, url_prefix='/client')
load_docs(app)

if __name__ == "__main__":
    site_map()
    app.run(debug=True)
