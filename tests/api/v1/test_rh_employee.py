# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Red Hat, Inc
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

import datetime
import uuid

import mock


# COMPONENTS
@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_components(m_datetime, admin, user_sso_rh_employee, app, engine,
                    topic_id):
    user_sso = user_sso_rh_employee
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        flask.g.db_conn = engine.connect()
        pc = admin.post('/api/v1/components',
                        data={'name': 'pname%s' % uuid.uuid4(),
                              'type': 'gerrit_review',
                              'topic_id': topic_id,
                              'export_control': True}).data
        pc_id = pc['component']['id']

        cmpts = user_sso.get('/api/v1/topics/%s/components' % topic_id)
        assert cmpts.status_code == 200
        cmpt = user_sso.get('/api/v1/components/%s' % pc_id)
        assert cmpt.status_code == 200
