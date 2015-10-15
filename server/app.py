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
import os

import server.auth
import server.db.models
import server.utils

from eve import Eve
from eve_sqlalchemy import SQL
from eve_sqlalchemy.validation import ValidatorSQL
from flask import abort
from sqlalchemy.sql import text

from dci_databrowser import dci_databrowser


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


class DciControlServer(Eve):

    _DCI_MODEL = None

    def __init__(self, dci_model, **kwargs):
        super(DciControlServer, self).__init__(**kwargs)

        DciControlServer._DCI_MODEL = dci_model
        DciControlServer._DCI_MODEL.metadata.bind = DciControlServer.\
            _DCI_MODEL.engine
        self._db = self.data.driver
        self._db.Model = DciControlServer._DCI_MODEL.base
        self._init_hooks()

    @staticmethod
    def pick_jobs(documents):
        session = DciControlServer._DCI_MODEL.get_session()
        query = text("""
        SELECT
            jobdefinitions.id
        FROM
            jobdefinitions, remotecis
        WHERE jobdefinitions.id NOT IN (
            SELECT
                jobs.jobdefinition_id
            FROM jobs
            WHERE jobs.remoteci_id=:remoteci_id
              AND
           jobs.created_at > now() - interval '1 day'
        ) AND jobdefinitions.test_id=remotecis.test_id AND
        remotecis.id=:remoteci_id
        LIMIT 1
        """)

        for d in documents:
            if 'jobdefinition_id' in d:
                continue
            r = DciControlServer._DCI_MODEL.engine.execute(
                query, remoteci_id=d['remoteci_id']).fetchone()
            if r is None:
                abort(412, "No test to run left.")
            jobdefinition = session.query(
                DciControlServer._DCI_MODEL.base.classes.jobdefinitions).\
                get(str(r[0]))
            d['jobdefinition_id'] = jobdefinition.id
        session.close()

    @staticmethod
    def stop_running_jobs(documents):
        session = DciControlServer._DCI_MODEL.get_session()
        Jobs = DciControlServer._DCI_MODEL.base.classes.jobs
        Jobstates = DciControlServer._DCI_MODEL.base.classes.jobstates
        for d in documents:
            jobs = session.query(Jobs).filter(
                Jobs.remoteci_id == d['remoteci_id']).all()
            for job in jobs:
                jobstate = job.jobstates.filter(
                    Jobstates.job_id == job.id).first()
                if jobstate is None:
                    continue
                if jobstate.status == 'ongoing':
                    session.add(
                        Jobstates(
                            job_id=job.id,
                            status='unfinished',
                            comment='The remoteci has started a new job.',
                            team_id=d['team_id']))
        session.commit()
        session.close()

    @staticmethod
    def aggregate_job_data(response):
        session = DciControlServer._DCI_MODEL.get_session()
        data = {}
        job = session.query(DciControlServer._DCI_MODEL.base.classes.jobs).\
            get(response['id'])
        # TODO(Gonéri): do we still need that?
        my_datas = [job.jobdefinition.test.data,
                    job.remoteci.data]
        for component in job.jobdefinition.components:
            my_datas.append(component.data)
        for my_data in my_datas:
            if my_data:
                data = server.utils.dict_merge(data, my_data)
        session.close()
        response['data'] = data

    @staticmethod
    def get_remotecis_extra(response):
        if not (flask.request.args.get('extra_data') and
                flask.request.args.get('version_id')):
            return

        version_id = flask.request.args.get('version_id')
        session = DciControlServer._DCI_MODEL.get_session()
        Remotecis = DciControlServer._DCI_MODEL.base.classes.remotecis
        remotecisTotal = session.query(Remotecis).count()

        rate = {"success": 0, "failure": 0, "ongoing": 0,
                "not_started": remotecisTotal}
        for remoteci in response["_items"]:
            Testversions = DciControlServer._DCI_MODEL.base.classes.\
                testversions
            testversions = session.query(Testversions).\
                filter(Testversions.version_id == version_id).all()

            for testversion in testversions:
                Jobs = DciControlServer._DCI_MODEL.base.classes.jobs
                job = session.query(Jobs).\
                    filter((Jobs.testversion_id == testversion.id) and
                           (Jobs.remoteci_id == remoteci["id"])).first()
                if job:
                    Jobstates = DciControlServer._DCI_MODEL.base.classes.\
                        jobstates
                    jobstate = job.jobstates.filter(
                        Jobstates.job_id == job.id).first()
                    if jobstate:
                        rate[jobstate.status] += 1
                        rate["not_started"] -= 1
        if rate["not_started"] < 0:
            rate["not_started"] = 0
        response["extra_data"] = rate

    def _init_hooks(self):
        self.on_insert += set_real_owner
        self.on_insert_jobs += DciControlServer.pick_jobs
        self.on_insert_jobs += DciControlServer.stop_running_jobs
        self.on_fetched_item_jobs += DciControlServer.aggregate_job_data
        self.on_fetched_resource_remotecis += DciControlServer.\
            get_remotecis_extra

        self.register_blueprint(dci_databrowser)
        load_docs(self)


def generate_conf():
    conf = flask.Config('')
    conf.from_object(
        os.environ.get('DCI_SETTINGS_MODULE') or 'server.settings')
    return conf


def create_app(conf):
    dci_model = server.db.models.DCIModel(conf['SQLALCHEMY_DATABASE_URI'])
    conf['DOMAIN'] = dci_model.generate_eve_domain_configuration()
    basic_auth = server.auth.DCIBasicAuth(dci_model)

    app = DciControlServer(dci_model, validator=ValidatorSQL, data=SQL,
                           auth=basic_auth, settings=conf)

    return app


if __name__ == "__main__":
    conf = generate_conf()
    app = create_app(conf)
    app.run(conf.get('HOST', 'localhost'),
            conf.get('PORT', 5000))
