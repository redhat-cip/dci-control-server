# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
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

import mock
from requests.exceptions import ConnectionError


@mock.patch("dci.api.v1.analytics.requests.get")
def test_elasticsearch_ressource_not_found(
    mock_requests, admin, remoteci_id, topic_user_id
):
    mock_404 = mock.MagicMock()
    mock_404.status_code = 404
    mock_requests.return_value = mock_404
    res = admin.get(
        "/api/v1/analytics/tasks_duration_cumulated?remoteci_id=%s&topic_id=%s"
        % (remoteci_id, topic_user_id)
    )
    assert res.status_code == 404


@mock.patch("dci.api.v1.analytics.requests.get")
def test_elasticsearch_error(mock_requests, admin, remoteci_id, topic_user_id):
    mock_error = mock.MagicMock()
    mock_error.status_code = 400
    mock_error.text = "error"
    mock_requests.return_value = mock_error
    res = admin.get(
        "/api/v1/analytics/tasks_duration_cumulated?remoteci_id=%s&topic_id=%s"
        % (remoteci_id, topic_user_id)
    )
    assert res.status_code == 400


@mock.patch("dci.api.v1.analytics.requests.get")
def test_elasticsearch_connection_error(
    mock_requests, admin, remoteci_id, topic_user_id
):
    mock_requests.side_effect = ConnectionError()
    res = admin.get(
        "/api/v1/analytics/tasks_duration_cumulated?remoteci_id=%s&topic_id=%s"
        % (remoteci_id, topic_user_id)
    )
    assert res.status_code == 503
