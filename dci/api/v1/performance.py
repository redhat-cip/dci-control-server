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

import flask

from dci.api.v1 import api
from dci.api.v1 import utils as v1_utils
from dci.api.v1 import files
from dci.db import models
from dci import decorators

import logging
from sqlalchemy import sql
from xml.etree import ElementTree

LOG = logging.getLogger(__name__)


def _get_junit_to_dict(file_descriptor, base_file_test_dict=None):
    results = {}
    try:
        for _, element in ElementTree.iterparse(file_descriptor):
            if element.tag == "testcase":
                test_name = "%s/%s" % (element.attrib.get("classname", ""),
                                       element.attrib.get("name", ""))
                results[test_name] = {"duration": element.attrib.get("time", -1)}  # noqa
                results[test_name]['delta'] = 0
                if base_file_test_dict is not None:
                    if base_file_test_dict.get(test_name) is not None:
                        base_duration = float(base_file_test_dict.get(test_name)["duration"])  # noqa
                        results_duration = float(results[test_name]['duration'])
                        diff = results_duration - base_duration
                        percentage = (diff * 100.) / base_duration
                        results[test_name]['delta'] = percentage
                    else:
                        results[test_name]['delta'] = -1
    except Exception as e:
        LOG.exception(e)
        return None
    return results


def _get_performance_tests(base_file, test_files):
    res = []
    base_file_fd = files.get_file_descriptor(base_file)
    base_file_test_dict = _get_junit_to_dict(base_file_fd)
    for f in test_files:
        fd = files.get_file_descriptor(f)
        test_dict = _get_junit_to_dict(fd, base_file_test_dict)
        fd.close()
        if test_dict is None:
            continue
        res.append({"testcases": test_dict})
    base_file_fd.close()
    return res


def _get_test_files(base_job_id, jobs_ids, test_filename):
    """"for each job get the associated file corresponding to the
    provided filename"""

    def _get_file(job_id):
        query = sql.select([models.FILES]). \
            where(models.FILES.c.job_id == job_id). \
            where(models.FILES.c.name == test_filename)
        return flask.g.db_conn.execute(query).fetchone()

    res = []
    for j_id in [base_job_id] + jobs_ids:
        j = v1_utils.verify_existence_and_get(j_id, models.JOBS, _raise=False)
        if j is None:
            LOG.error("job %s not found" % j_id)
            continue
        file = _get_file(j_id)
        if file is None:
            logger.error("file %s from job %s not found" % (test_filename, j_id))  # noqa
            continue
        res.append(file)
    if len(res) > 1:
        return res[0], res[1:]
    return None, None


@api.route('/performance', methods=['GET'])
@decorators.login_required
def compare_performance(user):
    values = flask.request.json
    base_job_id = values["base_job_id"]
    test_filename = values["test_filename"]
    jobs_ids = values["jobs"]
    base_file, test_files = _get_test_files(base_job_id, jobs_ids, test_filename)  # noqa
    if test_files is None:
        return flask.jsonify({"performance": []}), 200
    res = _get_performance_tests(base_file, test_files)
    return flask.jsonify({"performance": res}), 200
