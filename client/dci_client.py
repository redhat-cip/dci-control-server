#!/usr/bin/env python
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

import argparse
import os
import tempfile
import shutil
import stat
import subprocess

import prettytable
import requests


_DCI_CONTROL_SERVER = os.environ.get("DCI_CONTROL_SERVER",
                                     "http://127.0.0.1:5000")


def _init_conf():
    parser = argparse.ArgumentParser(description='DCI client.')
    parser.add_argument('--list-platforms', action="store_true",
                        default=False,
                        help='List existing platforms.')
    parser.add_argument('--list-jobs', action="store_true",
                        default=False,
                        help='List existing jobs.')
    parser.add_argument('--list-jobstates', action="store_true",
                        default=False,
                        help='List existing jobstates.')
    parser.add_argument('--list-scenarios', action="store_true",
                        default=False,
                        help='List existing scenarios.')
    parser.add_argument('--get-job', type=str,
                        help='Get a job.')
    parser.add_argument('--auto', type=str,
                        default=False,
                        help='Run automatically a job.')
    return parser.parse_args()


def _exec_shell_script(content):
    """Execute the shell script from a string.
    :param content: The script to execute.
    """
    temp_dir_path = tempfile.mkdtemp()
    with open("%s/job.sh" % temp_dir_path, "w") as f:
        f.write(content)

    os.chmod("%s/job.sh" % temp_dir_path, stat.S_IRWXU)
    ret = subprocess.call(["%s/job.sh" % temp_dir_path])
    shutil.rmtree(temp_dir_path)

    return ret


def main():
    conf = _init_conf()

    if conf.list_platforms:
        table_result = prettytable.PrettyTable(["identifier", "name",
                                                "created_at", "updated_at"])
        platforms = requests.get("%s/platforms" % _DCI_CONTROL_SERVER).json()

        for platform in platforms["_items"]:
            table_result.add_row([platform["id"],
                                  platform["name"],
                                  platform["created_at"],
                                  platform["updated_at"]])
        print(table_result)
    if conf.list_jobs:
        table_result = prettytable.PrettyTable(["identifier",
                                                "platform", "scenario",
                                                "updated_at"])
        jobs = requests.get("%s/jobs" % _DCI_CONTROL_SERVER).json()

        for job in jobs["_items"]:
            table_result.add_row([job["id"],
                                  job["platform_id"],
                                  job["scenario_id"],
                                  job["updated_at"]])
        print(table_result)
    if conf.list_jobstates:
        table_result = prettytable.PrettyTable(["identifier", "status",
                                                "comment", "job", "updated_at"])
        jobstates = requests.get("%s/jobstates" % _DCI_CONTROL_SERVER).json()

        for jobstate in jobstates["_items"]:
            table_result.add_row([jobstate["id"],
                                  jobstate["status"],
                                  jobstate["comment"],
                                  jobstate["job_id"],
                                  jobstate["updated_at"]])
        print(table_result)
    if conf.list_scenarios:
        table_result = prettytable.PrettyTable(["identifier", "name",
                                                "updated_at"])
        scenarios = requests.get("%s/scenarios" % _DCI_CONTROL_SERVER).json()

        for scenario in scenarios["_items"]:
            table_result.add_row([scenario["id"],
                                  scenario["name"],
                                  scenario["updated_at"]])
        print(table_result)
    elif conf.get_job:
        job = requests.get("%s/jobs/get_job_by_platform/%s" %
                           (_DCI_CONTROL_SERVER, conf.get_job)).json()

        table_result = prettytable.PrettyTable(["job", "environment"])
        table_result.add_row([job["job_id"], job["url"]])
        print(table_result)
    elif conf.auto:
        # 1. Get a job
        job = requests.get("%s/jobs/get_job_by_platform/%s" %
                           (_DCI_CONTROL_SERVER, conf.auto)).json()

        # 2. Execute the job
        # 2.1. create temporary shell script and execute it
        job_errno = _exec_shell_script(job["content"])

        # 3. Report status
        status = "success"
        if job_errno != 0:
            status = "failure"
        state = {"job_id": job["job_id"],
                 "status": status,
                 "comment": "no comments"}
        jobstate = requests.post("%s/jobstates" % _DCI_CONTROL_SERVER,
                                 data=state).json()
        print("[*] jobstate created: %s\n" % jobstate["id"])

        logs_data = {"name": "SPS_logs",
                     "content": "log generated",
                     "mime": "text/plain",
                     "jobstate_id": jobstate["id"]}
        logs = requests.post("%s/files" % _DCI_CONTROL_SERVER,
                             data=logs_data).json()

        print("[*] logs created: %s\n" % logs["id"])


if __name__ == '__main__':
    main()
