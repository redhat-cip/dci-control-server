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

import copy

import six
from sqlalchemy.sql import text

from server.db.models import engine
from server.db.models import Job
from server.db.models import Jobstate
from server.db.models import Remoteci
from server.db.models import session
from server.db.models import TestVersion


def dict_merge(a, b):
    '''recursively merges dict's. not just simple a['key'] = b['key'], if
    both a and bhave a key who's value is a dict then dict_merge is called
    on both values and the result stored in the returned dictionary.
    '''
    if not isinstance(b, dict):
        return b
    result = copy.deepcopy(a)
    for k, v in six.iteritems(b):
        if k in result and isinstance(result[k], dict):
                result[k] = dict_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result


def get_job_by_remoteci(remoteci_id):
    """Return a job id which reference a testversion that has not been
    associated to this remote CI.
    """
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

    r = engine.execute(query, remoteci_id=remoteci_id)
    record = r.fetchone()
    if record is None:
        return {}
    test_version = session.query(TestVersion).get(str(record[0]))
    remoteci = session.query(Remoteci).get(remoteci_id)
    job = Job(
        remoteci_id=remoteci.id,
        testversion_id=test_version.id)
    session.add(job)
    session.commit()
    session.refresh(job)
    session.add(
        Jobstate(job_id=job.id, status='new')
    )
    session.commit()

    data = {}
    my_datas = (
        job.testversion.version.product.data,
        job.testversion.version.data,
        job.testversion.test.data)
    for my_data in my_datas:
        data = dict_merge(data, my_data)
    return {'job_id': job.id, 'data': data}
