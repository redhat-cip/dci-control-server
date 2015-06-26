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
import os
from pprint import pprint

import server.auth
import server.db.api as api
import server.db.models

from eve import Eve
from eve_sqlalchemy import SQL
from eve_sqlalchemy.validation import ValidatorSQL
from flask import abort
from sqlalchemy.sql import text

from dci_databrowser import dci_databrowser


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


def set_real_owner(resource, items):
    """Hack to allow the 'admin' user to change the team_id."""
    if flask.request.authorization.username != 'admin':
        return
    # NOTE(Gonéri): the fields returned by flask.request.get_json() are
    # already mangled by the Role Based Access Control.
    request_fields = json.loads(flask.request.data.decode('utf-8'))
    if "team_id" in request_fields:
        items[0]['team_id'] = request_fields['team_id']


def init_app(db_uri=None):

    if not db_uri:
        db_uri = os.environ.get(
            'OPENSHIFT_POSTGRESQL_DB_URL',
            'postgresql://boa:boa@127.0.0.1:5432/dci_control_server')
    dci_model = server.db.models.DCIModel(db_uri)
    my_settings = {
        'SQLALCHEMY_DATABASE_URI': db_uri,
        'LAST_UPDATED': 'updated_at',
        'DATE_CREATED': 'created_at',
        'ID_FIELD': 'id',
        # 94ecbcfe-a9a6-7913-13a8-1ef1d50d9817
        'ITEM_URL': 'regex("[\.-a-z0-9]{8}-[-a-z0-9]{4}-'
                    '[-a-z0-9]{4}-[-a-z0-9]{4}-[-a-z0-9]{12}")',
        'ITEM_LOOKUP_FIELD': 'id',
        'ETAG': 'etag',
        'DEBUG': True,
        'URL_PREFIX': 'api',
        'X_DOMAINS': '*',
        'X_HEADERS': 'Authorization',
        'DOMAIN': dci_model.generate_eve_domain_configuration(),
        # The following two lines will output the SQL statements
        # executed by SQLAlchemy. Useful while debugging and in
        # development. Turned off by default
        # --------
        'SQLALCHEMY_ECHO': False,
        'SQLALCHEMY_RECORD_QUERIES': False,
    }
    my_basicauth = server.auth.DCIBasicAuth(dci_model)
    app = Eve(settings=my_settings, validator=ValidatorSQL,
              data=SQL, auth=my_basicauth)
    db = app.data.driver
    dci_model.metadata.bind = dci_model.engine
    db.Model = dci_model.base

    def pick_jobs(documents):
        session = dci_model.get_session()
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
            r = dci_model.engine.execute(
                query, remoteci_id=d['remoteci_id']).fetchone()
            if r is None:
                abort(412, "No test to run left.")
            testversion = session.query(
                dci_model.base.classes.testversions).get(str(r[0]))
            d['testversion_id'] = testversion.id
        session.close()

    def aggregate_job_data(response):
        session = dci_model.get_session()
        data = {}
        job = session.query(dci_model.base.classes.jobs).get(response['id'])
        my_datas = (
            job.testversion.version.product.data,
            job.testversion.version.data,
            job.testversion.test.data,
            job.remoteci.data)
        for my_data in my_datas:
            if my_data:
                data = api.dict_merge(data, my_data)
        session.close()
        response['data'] = data

    def get_job(response):
        if not flask.request.args.get('extra_data'):
            return

        session = dci_model.get_session()
        for job in response["_items"]:
            job["extra_data"] = {}
            # Get the jobstate
            Jobstates = dci_model.base.classes.jobstates
            jobstate = session.query(Jobstates).\
                order_by(Jobstates.created_at.desc()).\
                filter(Jobstates.job_id == job["id"]).first()
            if not jobstate:
                continue
            job["extra_data"]["last_status"] = jobstate.status
            job["extra_data"]["last_update"] = jobstate.created_at

            # Get the remote ci name
            Remotecis = dci_model.base.classes.remotecis
            remoteci = session.query(Remotecis).\
                filter(Remotecis.id == job["remoteci_id"]).one()
            job["extra_data"]["remoteci"] = remoteci.name

            # Get the testversion
            Testversions = dci_model.base.classes.testversions
            testversion = session.query(Testversions).get(
                job["testversion_id"])

            # Get the version
            Versions = dci_model.base.classes.versions
            version = session.query(Versions).get(testversion.version_id)
            job["extra_data"]["version"] = version.name

            # Get the product
            Products = dci_model.base.classes.products
            product = session.query(Products).get(version.product_id)
            job["extra_data"]["product"] = product.name

            # Get the test
            Tests = dci_model.base.classes.tests
            test = session.query(Tests).get(testversion.test_id)
            job["extra_data"]["test"] = test.name
        session.close()

    def get_versions_extra(response):
        if not flask.request.args.get('extra_data'):
            return

        session = dci_model.get_session()
        for version in response["_items"]:
            version["extra_data"] = []

            Testversions = dci_model.base.classes.testversions
            testversions = session.query(Testversions).\
                filter(Testversions.version_id == version["id"]).all()

            for testversion in testversions:
                extra_data = {}
                Tests = dci_model.base.classes.tests
                test = session.query(Tests).get(testversion.test_id)
                extra_data["test"] = test.name

                Jobs = dci_model.base.classes.jobs
                job = session.query(Jobs).\
                    filter(Jobs.testversion_id == testversion.id).first()
                extra_data["job_id"] = job.id

                Remotecis = dci_model.base.classes.remotecis
                remoteci = session.query(Remotecis).get(job.remoteci_id)
                extra_data["remoteci"] = remoteci.name

                Jobstates = dci_model.base.classes.jobstates
                jobstate = session.query(Jobstates).\
                    order_by(Jobstates.created_at.desc()).\
                    filter(Jobstates.job_id == job.id).first()
                if jobstate:
                    extra_data["status"] = jobstate.status

                version["extra_data"].append(extra_data)
        session.close()

    app.on_insert += set_real_owner
    app.on_insert_jobs += pick_jobs
    app.on_fetched_item_jobs += aggregate_job_data
    app.on_fetched_resource_jobs += get_job
    app.on_fetched_resource_versions += get_versions_extra

    app.register_blueprint(dci_databrowser, url_prefix='/client')
    load_docs(app)
    return app

if __name__ == "__main__":
    app = init_app()
    site_map()
    app.run(debug=True)
