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

from pprint import pprint

import server.db.api as api
from server.db.models import Base
from server.db.models import engine
from server.db.models import Job
from server.db.models import session
from server.db.models import TestVersion
from server.db.models import User

from eve import Eve
from eve_sqlalchemy import SQL
from eve_sqlalchemy.validation import ValidatorSQL
from flask import abort
from flask import request
import sqlalchemy.orm.exc
from sqlalchemy.sql import text

from dci_databrowser import dci_databrowser

# WARNING(Gonéri): both python-bcrypt and bcrypt provide a bcrypt package
import bcrypt
from eve.auth import BasicAuth


class adminOnlyCrypt(BasicAuth):
    def check_auth(self, name, password, allowed_roles, resource, method):
        return True
        try:
            user = session.query(User).filter_by(name=name).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return False

        if bcrypt.hashpw(
                password.encode('utf-8'),
                user.password.encode('utf-8')
        ) == user.password.encode('utf-8'):
            return True
        return False

    def authorized(self, allowed_roles, resource, method):
        return True
        auth = request.authorization
        if not hasattr(auth, 'username') or not hasattr(auth, 'password'):
            abort(401, description='Unauthorized: username required')
        if not self.check_auth(auth.username, auth.password, None,
                               resource, method):
            abort(401, description='Unauthorized')

        user = session.query(User).filter_by(name=auth.username).one()
        roles = set([ur.role.name for ur in user.user_roles])

        if 'admin' in roles:
            return True

        # NOTE(Gonéri): We may find useful to store this matrice directly in
        # the role entrt in the DB
        acl = {
            'partner': {
                'remotecis': ['GET'],
                'jobs': ['GET'],
                'jobstates': ['GET', 'POST']
            }
        }

        for role in roles:
            try:
                if method in acl[role][resource]:
                    return True
            except KeyError:
                pass
        abort(403, description='Forbidden')


app = Eve(validator=ValidatorSQL, data=SQL, auth=adminOnlyCrypt)
db = app.data.driver
Base.metadata.bind = engine
db.Model = Base


def site_map():
    for rule in app.url_map.iter_rules():
        pprint(rule)


def pick_jobs(documents):
    query = text(
        """
SELECT
    testversions.id
FROM
    testversions
WHERE testversions.id NOT IN (
    SELECT
        jobs.testversion_id
    FROM jobs
    WHERE jobs.remoteci_id=:remoteci_id
)
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
        job.testversion.test.data)
    for my_data in my_datas:
        data = api.dict_merge(data, my_data)
    response['data'] = data


app.on_insert_jobs += pick_jobs
app.on_fetched_item_jobs += aggregate_job_data

if __name__ == "__main__":
    site_map()
    app.register_blueprint(dci_databrowser, url_prefix='/client')
    app.run(debug=True)
