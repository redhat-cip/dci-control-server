# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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
from uuid import UUID

from sqlalchemy import sql

from dci.api.v1.tests_results import create_test_results

from dci.db import models


def test_create_test_results(engine, job_id, file_id):
    query = sql.select([models.TESTS_RESULTS])
    assert len(engine.execute(query).fetchall()) == 0

    now = datetime.datetime.utcnow().isoformat()
    create_test_results(engine, {
        'created_at': now,
        'job_id': job_id,
        'file_id': file_id,
        'name': 'Test result'
    })

    tests_results = engine.execute(query).fetchall()
    assert len(tests_results) == 1

    test_result = dict(tests_results[0])
    assert UUID(str(test_result['id']), version=4)
    assert tests_results[0]['created_at'].isoformat() == now
