# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Red Hat, Inc
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

from __future__ import unicode_literals


def test_attach_issue_to_job(admin, job_id):
    data = {
        'url': 'https://github.com/redhat-cip/dci-control-server/issues/1'
    }
    admin.post('/api/v1/jobs/%s/issues' % job_id, data=data)
    result = admin.get('/api/v1/jobs/%s/issues' % job_id).data
    assert result['issues'][0]['url'] == data['url']


def test_get_all_issues_from_job(admin, job_id):
    data_1 = {
        'url': 'https://github.com/redhat-cip/dci-control-server/issues/1'
    }
    data_2 = {
        'url': 'https://github.com/redhat-cip/dci-control-server/issues/2'
    }
    admin.post('/api/v1/jobs/%s/issues' % job_id, data=data_1)
    admin.post('/api/v1/jobs/%s/issues' % job_id, data=data_2)
    result = admin.get('/api/v1/jobs/%s/issues' % job_id).data
    assert result['_meta']['count'] == 2


def test_unattach_issue_from_job(admin, job_id):
    data_1 = {
        'url': 'https://github.com/redhat-cip/dci-control-server/issues/1'
    }
    data_2 = {
        'url': 'https://github.com/redhat-cip/dci-control-server/issues/2'
    }
    admin.post('/api/v1/jobs/%s/issues' % job_id, data=data_1)
    result = admin.post('/api/v1/jobs/%s/issues' % job_id, data=data_2).data
    issue_id = result['issue_id']
    result = admin.get('/api/v1/jobs/%s/issues' % job_id).data
    assert result['_meta']['count'] == 2
    admin.delete('/api/v1/jobs/%s/issues/%s' % (job_id, issue_id))
    result = admin.get('/api/v1/jobs/%s/issues' % job_id).data
    assert result['_meta']['count'] == 1


def test_github_tracker(admin, job_id):
    data = {
        'url': 'https://github.com/redhat-cip/dci-control-server/issues/1'
    }
    admin.post('/api/v1/jobs/%s/issues' % job_id, data=data)
    result = admin.get('/api/v1/jobs/%s/issues' % job_id).data['issues'][0]

    assert result['issue_id'] == 1
    assert result['title'] == (
        'Create a GET handler for /componenttype/<ct_name>'
    )
    assert result['reporter'] == 'Spredzy'
    assert result['status'] == 'closed'
    assert result['product'] == 'redhat-cip'
    assert result['component'] == 'dci-control-server'
    assert result['created_at'] == '2015-12-09T09:29:26Z'
    assert result['updated_at'] == '2015-12-18T15:19:41Z'
    assert result['closed_at'] == '2015-12-18T15:19:41Z'
    assert result['assignee'] is None


def test_bugzilla_tracker(admin, job_id):
    data = {
        'url': 'https://bugzilla.redhat.com/show_bug.cgi?id=1184949'
    }
    admin.post('/api/v1/jobs/%s/issues' % job_id, data=data)
    result = admin.get('/api/v1/jobs/%s/issues' % job_id).data['issues'][0]

    assert result['issue_id'] == '1184949'
    assert result['title'] == 'Timeouts in haproxy for keystone can be too low'
    assert result['reporter'] == 'amoralej'
    assert result['assignee'] == 'mburns'
    assert result['status'] == 'NEW'
    assert result['product'] == 'Red Hat OpenStack'
    assert result['component'] == 'rubygem-staypuft'
    assert result['created_at'] == '2015-01-22 09:46:00 -0500'
    assert result['updated_at'] == '2016-06-29 18:50:43 -0400'
    assert result['closed_at'] is None
