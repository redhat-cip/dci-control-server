# -*- encoding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from dci.server.tests import utils


class TestAuth(object):

    def test_authorized_as_partner(self, company_a_user):
        # partner can read files
        assert company_a_user.get('/api/files').status_code == 200
        # partner can create job (400 because of the missing parameters)
        assert company_a_user.post('/api/jobs').status_code == 400

    def test_wrong_pw_as_unauthorized(self, unauthorized):
        assert unauthorized.get('/api/files').status_code == 401
        assert unauthorized.get('/api/jobs').status_code == 401

    def test_authorized_as_admin(self, admin):
        assert admin.get('/api/files').status_code == 200

    def test_team_isolation(self, admin, company_b_user, company_a_user):
        test = utils.create_test(admin)
        utils.create_jobdefinition(admin, test.data['id'])
        remoteci = utils.create_remoteci(company_b_user, test.data['id'])
        job = utils.create_job(company_b_user, remoteci.data['id'])
        jobstates = utils.create_jobstate(company_b_user, job.data['id'])
        a_file = utils.create_file(company_b_user, jobstates.data['id'])

        assert a_file.status_code == 201

        assert company_a_user.get(
            '/api/files/%s' % a_file.data['id']).status_code == 404
        assert company_b_user.get(
            '/api/files/%s' % a_file.data['id']).status_code == 200
        assert admin.get(
            '/api/files/%s' % a_file.data['id']).status_code == 200

        assert len(company_a_user.get('/api/files').data['_items']) == 0
        assert len(company_b_user.get('/api/files').data['_items']) == 1
        assert len(admin.get('/api/files').data['_items']) == 1
