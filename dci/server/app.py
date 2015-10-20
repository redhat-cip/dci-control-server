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


import json
import os

from dci.server import auth
from dci.server.db import models
from dci.server import eve_model
from dci.server import utils

from eve import Eve
from eve_sqlalchemy import SQL
from eve_sqlalchemy.validation import ValidatorSQL
import flask
from sqlalchemy.sql import text

from dci.dci_databrowser import dci_databrowser


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
        DciControlServer._DCI_MODEL.Base.metadata.bind = DciControlServer.\
            _DCI_MODEL.engine
        self._db = self.data.driver
        self._db.Model = DciControlServer._DCI_MODEL.Base
        self._init_hooks()

    @staticmethod
    def pick_jobs(documents):
        picked_job = documents[0]
        session = DciControlServer._DCI_MODEL.get_session()

        # First, test if its a recheck request
        if flask.request.args.get('recheck'):
            job_id_to_recheck = str(flask.request.args.get('job_id'))
            if not job_id_to_recheck:
                flask.abort(400, "job_id missing.")
            job_to_recheck = session.query(
                DciControlServer._DCI_MODEL.Job).\
                get(job_id_to_recheck)
            if not job_to_recheck:
                flask.abort(400, "job '%s' does not exist." %
                            job_id_to_recheck)
            # Replicate the recheck job
            picked_job['jobdefinition_id'] = job_to_recheck.jobdefinition_id
            picked_job['remoteci_id'] = job_to_recheck.remoteci_id
            picked_job['team_id'] = job_to_recheck.team_id
            picked_job['recheck'] = True
        else:
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
            ORDER BY
                priority ASC
            LIMIT 1
            """)

            r = DciControlServer._DCI_MODEL.engine.execute(
                query, remoteci_id=picked_job['remoteci_id']).fetchone()
            if r is None:
                flask.abort(412, "No test to run left.")
            jobdefinition = session.query(
                DciControlServer._DCI_MODEL.Jobdefinition).\
                get(str(r[0]))
            picked_job['jobdefinition_id'] = jobdefinition.id
            session.close()

    @staticmethod
    def stop_running_jobs(documents):
        session = DciControlServer._DCI_MODEL.get_session()
        Jobs = DciControlServer._DCI_MODEL.Job
        Jobstates = DciControlServer._DCI_MODEL.Jobstate
        for d in documents:
            jobs = session.query(Jobs).filter(
                Jobs.remoteci_id == d['remoteci_id']).all()
            for job in jobs:
                jobstates = job.jobstates
                if not jobstates:
                    continue
                jobstate = jobstates[0]
                if jobstate.status in ('new', 'ongoing', 'initializing'):
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
        job = session.query(DciControlServer._DCI_MODEL.Job).\
            get(response['id'])
        # TODO(Gonéri): do we still need that?
        my_datas = [job.jobdefinition.test.data,
                    job.remoteci.data]
        for component in job.jobdefinition.components:
            my_datas.append(component.data)
        for my_data in my_datas:
            if my_data:
                data = utils.dict_merge(data, my_data)
        session.close()
        response['data'] = data

    @staticmethod
    def get_remotecis_extra(response):
        if not (flask.request.args.get('extra_data') and
                flask.request.args.get('version_id')):
            return

        version_id = flask.request.args.get('version_id')
        session = DciControlServer._DCI_MODEL.get_session()
        Remotecis = DciControlServer._DCI_MODEL.Remoteci
        remotecisTotal = session.query(Remotecis).count()

        rate = {"success": 0, "failure": 0, "ongoing": 0,
                "not_started": remotecisTotal}
        for remoteci in response["_items"]:
            Testversions = DciControlServer._DCI_MODEL.Testversions
            testversions = session.query(Testversions).\
                filter(Testversions.version_id == version_id).all()

            for testversion in testversions:
                Jobs = DciControlServer._DCI_MODEL.Job
                job = session.query(Jobs).\
                    filter((Jobs.testversion_id == testversion.id) and
                           (Jobs.remoteci_id == remoteci["id"])).first()
                if job:
                    Jobstate = DciControlServer._DCI_MODEL.Jobstate
                    jobstate = job.jobstates.filter(
                        Jobstate.job_id == job.id).first()
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
        os.environ.get('DCI_SETTINGS_MODULE') or 'dci.server.settings')
    return conf


def create_app(conf):
    dci_model = models.DCIModel(conf['SQLALCHEMY_DATABASE_URI'])
    conf['DOMAIN'] = eve_model.domain_configuration()
    basic_auth = auth.DCIBasicAuth(dci_model)

    app = DciControlServer(dci_model, validator=ValidatorSQL, data=SQL,
                           auth=basic_auth, settings=conf)

    return app
