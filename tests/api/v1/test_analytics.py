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
import uuid

from dci.api.v1 import analytics
from dci.analytics import query_es_dsl as qed


@mock.patch("dci.api.v1.analytics.requests.get")
def test_elasticsearch_ressource_not_found(
    mock_requests, client_admin, team2_remoteci_id, rhel_80_topic_id
):
    mock_404 = mock.MagicMock()
    mock_404.status_code = 404
    mock_requests.return_value = mock_404
    res = client_admin.get(
        "/api/v1/analytics/tasks_duration_cumulated?remoteci_id=%s&topic_id=%s"
        % (team2_remoteci_id, rhel_80_topic_id)
    )
    assert res.status_code == 404


@mock.patch("dci.api.v1.analytics.requests.get")
def test_elasticsearch_error(
    mock_requests, client_admin, team2_remoteci_id, rhel_80_topic_id
):
    mock_error = mock.MagicMock()
    mock_error.status_code = 400
    mock_error.text = "error"
    mock_requests.return_value = mock_error
    res = client_admin.get(
        "/api/v1/analytics/tasks_duration_cumulated?remoteci_id=%s&topic_id=%s"
        % (team2_remoteci_id, rhel_80_topic_id)
    )
    assert res.status_code == 400


@mock.patch("dci.api.v1.analytics.requests.get")
def test_elasticsearch_connection_error(
    mock_requests, client_admin, team2_remoteci_id, rhel_80_topic_id
):
    mock_requests.side_effect = ConnectionError()
    res = client_admin.get(
        "/api/v1/analytics/tasks_duration_cumulated?remoteci_id=%s&topic_id=%s"
        % (team2_remoteci_id, rhel_80_topic_id)
    )
    assert res.status_code == 503


def test_tasks_analytics_pipelines_status(client_user1, team_admin_id):
    res = client_user1.post(
        "/api/v1/analytics/pipelines_status",
        data={
            "start_date": "1970-01-01",
            "end_date": "1970-01-01",
            "teams_ids": [team_admin_id],
            "pipelines_names": ["pipeline_name"],
        },
    )
    assert res.status_code == 401


def test_tasks_jobs(client_user1, client_admin):
    res = client_admin.get(
        "/api/v1/analytics/jobs?query=foo",
    )
    assert res.status_code == 400


def test_handle_es_sort():
    res = analytics.handle_es_sort({"sort": "titi"})
    assert res == [{"titi": {"order": "asc", "format": "strict_date_optional_time"}}]

    res = analytics.handle_es_sort({"sort": "-titi"})
    assert res == [{"titi": {"order": "desc", "format": "strict_date_optional_time"}}]

    res = analytics.handle_es_sort({})
    assert res == [
        {"created_at": {"order": "desc", "format": "strict_date_optional_time"}}
    ]


def test_handle_es_timeframe():
    query = qed.build("name='titi'")
    res = analytics.handle_es_timeframe(
        query, {"from": "2024-01-01", "to": "2024-02-01"}
    )
    assert res == {
        "bool": {
            "filter": [
                {"range": {"created_at": {"gte": "2024-01-01", "lte": "2024-02-01"}}},
                query,
            ]
        }
    }


def test_handle_includes_excludes():
    ret = analytics.handle_includes_excludes(
        {"includes": "titi,tata", "excludes": "toto"}
    )
    assert ret == {"excludes": ["toto"], "includes": ["titi", "tata"]}

    ret = analytics.handle_includes_excludes({})
    assert ret == {}


def test_build_es_query():
    args = {
        "offset": 10,
        "limit": 10,
        "query": "(((components.type='ocp') and (components.tags in ['build:ga'])) and ((components.type='f5-spk')) and (tags in ['daily']))",
        "sort": "-created_at",
        "from": "2024-01-01",
        "to": "2024-02-01",
        "includes": "team,topic",
        "excludes": "jobstates",
    }
    ret = analytics.build_es_query(args)
    assert ret == {
        "from": 10,
        "size": 10,
        "query": {
            "bool": {
                "filter": [
                    {
                        "range": {
                            "created_at": {"gte": "2024-01-01", "lte": "2024-02-01"}
                        }
                    },
                    {
                        "bool": {
                            "filter": [
                                {
                                    "nested": {
                                        "path": "components",
                                        "query": {
                                            "bool": {
                                                "filter": [
                                                    {
                                                        "term": {
                                                            "components.type": "ocp"
                                                        }
                                                    },
                                                    {
                                                        "terms": {
                                                            "components.tags": [
                                                                "build:ga"
                                                            ]
                                                        }
                                                    },
                                                ]
                                            }
                                        },
                                    }
                                },
                                {
                                    "nested": {
                                        "path": "components",
                                        "query": {
                                            "term": {"components.type": "f5-spk"}
                                        },
                                    }
                                },
                                {"terms": {"tags": ["daily"]}},
                            ]
                        }
                    },
                ]
            }
        },
        "sort": [
            {"created_at": {"order": "desc", "format": "strict_date_optional_time"}}
        ],
        "_source": {"excludes": ["jobstates"], "includes": ["team", "topic"]},
    }


def test_build_es_query_with_teams():
    args = {
        "offset": 10,
        "limit": 10,
        "query": "(name='toto')",
        "sort": "-created_at",
        "from": "2024-01-01",
        "to": "2024-02-01",
        "includes": "team,topic",
        "excludes": "jobstates",
    }
    teams_ids = [uuid.uuid4(), uuid.uuid4()]
    ret = analytics.build_es_query(args, teams_ids)
    assert ret == {
        "from": 10,
        "size": 10,
        "query": {
            "bool": {
                "filter": [
                    {
                        "bool": {
                            "should": [
                                {"term": {"team_id": str(teams_ids[0])}},
                                {"term": {"team_id": str(teams_ids[1])}},
                            ]
                        }
                    },
                    {
                        "bool": {
                            "filter": [
                                {
                                    "range": {
                                        "created_at": {
                                            "gte": "2024-01-01",
                                            "lte": "2024-02-01",
                                        }
                                    }
                                },
                                {"term": {"name": "toto"}},
                            ]
                        }
                    },
                ]
            }
        },
        "sort": [
            {"created_at": {"order": "desc", "format": "strict_date_optional_time"}}
        ],
        "_source": {"excludes": ["jobstates"], "includes": ["team", "topic"]},
    }


def test_build_autocompletion_query():
    args = {"field": "field"}
    res = analytics.build_autocompletion_query(
        args, "6e6b1cbc-9e0d-49fd-8cff-9ebf37caf147"
    )
    assert res == {
        "field": "field",
        "team_id": "6e6b1cbc-9e0d-49fd-8cff-9ebf37caf147",
        "size": 10,
    }


@mock.patch("dci.api.v1.analytics.requests.get")
def test_autocomplete_field(mock_requests, client_user1):
    mock_autocomplete = mock.MagicMock()
    mock_autocomplete.status_code = 200
    mock_autocomplete.json.return_value = ["job1", "job2"]
    mock_requests.return_value = mock_autocomplete
    res = client_user1.get("/api/v1/analytics/jobs/autocomplete?field=name")
    assert res.status_code == 200
    assert res.data == ["job1", "job2"]
