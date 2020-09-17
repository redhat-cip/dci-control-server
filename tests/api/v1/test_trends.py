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
import datetime
import json
import uuid

from dci.api.v1.trends import get_trends_from_jobs


def test_trends():
    jobs = [
        {
            "created_at": datetime.datetime.strptime(
                "2018-06-27T10:29:04", "%Y-%m-%dT%H:%M:%S"
            ),
            "status": "failure",
            "topic_id": uuid.UUID("23da2f7b-90cd-4d71-a48a-e9c88f75b5eb"),
        },
        {
            "created_at": datetime.datetime.strptime(
                "2018-06-27T14:30:02", "%Y-%m-%dT%H:%M:%S"
            ),
            "status": "success",
            "topic_id": uuid.UUID("23da2f7b-90cd-4d71-a48a-e9c88f75b5eb"),
        },
        {
            "created_at": datetime.datetime.strptime(
                "2018-06-28T02:14:03", "%Y-%m-%dT%H:%M:%S"
            ),
            "status": "success",
            "topic_id": uuid.UUID("23da2f7b-90cd-4d71-a48a-e9c88f75b5eb"),
        },
        {
            "created_at": datetime.datetime.strptime(
                "2018-06-28T12:08:02", "%Y-%m-%dT%H:%M:%S"
            ),
            "status": "success",
            "topic_id": uuid.UUID("9f2344e8-e3dc-4039-84fa-5bc7e53b8865"),
        },
    ]
    trends = get_trends_from_jobs(jobs)

    assert json.dumps(trends, indent=4, sort_keys=True) == json.dumps(
        {
            "23da2f7b-90cd-4d71-a48a-e9c88f75b5eb": [
                [1530057600, 1, 1],
                [1530144000, 1, 0],
            ],
            "9f2344e8-e3dc-4039-84fa-5bc7e53b8865": [[1530144000, 1, 0]],
        },
        indent=4,
        sort_keys=True,
    )
