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
import glob
import os
import shutil
import stat
import subprocess
import tempfile

import prettytable
import requests


_DCI_CONTROL_SERVER = os.environ.get("DCI_CONTROL_SERVER",
                                     "http://127.0.0.1:5000")


def _init_conf():
    parser = argparse.ArgumentParser(description='DCI client.')
    command_subparser = parser.add_subparsers(help='commands',
                                              dest='command')
    # register platform command
    register_platform_parser = command_subparser.add_parser(
        'register-platform', help='Register a platform.')
    register_platform_parser.add_argument('--name', action='store',
                                          help='Name of the platform.')

    # list command
    list_parser = command_subparser.add_parser('list', help='List resources.')
    list_parser.add_argument('--platforms', action='store_true',
                             default=False,
                             help='List existing platforms.')
    list_parser.add_argument('--jobs', action="store_true",
                             default=False,
                             help='List existing jobs.')
    list_parser.add_argument('--jobstates', action="store_true",
                             default=False,
                             help='List existing jobstates.')
    list_parser.add_argument('--scenarios', action="store_true",
                             default=False,
                             help='List existing scenarios.')
    list_parser.add_argument('--job', type=str,
                             help='Get a job.')

    # auto command
    auto_parser = command_subparser.add_parser('auto', help='Automated mode.')
    auto_parser.add_argument('platform', action='store',
                             help='Id of the platform')

    # get command
    auto_parser = command_subparser.add_parser('get', help='Get a job.')
    auto_parser.add_argument('platform', action='store',
                             help='Id of the platform')

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

    if conf.command == 'list':
        if conf.platforms:
            table_result = prettytable.PrettyTable(["identifier", "name",
                                                    "created_at", "updated_at"])
            platforms = requests.get("%s/platforms" %
                                     _DCI_CONTROL_SERVER).json()

            for platform in platforms["_items"]:
                table_result.add_row([platform["id"],
                                     platform["name"],
                                     platform["created_at"],
                                     platform["updated_at"]])
            print(table_result)
        elif conf.jobs:
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
        elif conf.jobstates:
            table_result = prettytable.PrettyTable(["identifier", "status",
                                                    "comment", "job",
                                                    "updated_at"])
            jobstates = requests.get(
                "%s/jobstates" % _DCI_CONTROL_SERVER).json()

            for jobstate in jobstates["_items"]:
                table_result.add_row([jobstate["id"],
                                      jobstate["status"],
                                      jobstate["comment"],
                                      jobstate["job_id"],
                                      jobstate["updated_at"]])
            print(table_result)
        elif conf.scenarios:
            table_result = prettytable.PrettyTable(["identifier", "name",
                                                    "updated_at"])
            scenarios = requests.get(
                "%s/scenarios" % _DCI_CONTROL_SERVER).json()

            for scenario in scenarios["_items"]:
                table_result.add_row([scenario["id"],
                                      scenario["name"],
                                      scenario["updated_at"]])
            print(table_result)
    elif conf.command == 'register-platform':
        new_platform = {"name": conf.name}
        requests.post("%s/platforms" % _DCI_CONTROL_SERVER,
                      data=new_platform).json()
        print("Platform '%s' created successfully." % conf.name)
    elif conf.command == 'auto':
        # 1. Get a job
        job = requests.get("%s/jobs/get_job_by_platform/%s" %
                           (_DCI_CONTROL_SERVER, conf.platform)).json()
        print("Testing environment: %s" % job['environment_id'])

        # 2. Execute the job
        # 2.1. create temporary shell script and execute it
        for environment_url in job["url"]:
            subprocess.call(["wget", "--recursive", "--continue", "--no-parent",
                             "--directory-prefix=environment", "-nH",
                             "--mirror", "--cut-dirs=2", "--quiet",
                             "--no-verbose",
                             "-e", "robots=off", "--reject", "index.html*",
#                            "--show-progress",
                             environment_url])

        status = "ongoing"
        scripts = glob.glob('environment/configure.d/*.sh')
        scripts += glob.glob('environment/test.d/*.sh')
        for script in scripts:
            print("script: %s" % script)
            try:
                # TODO(Gonéri): we need a timeout
                output = subprocess.check_output(
                    ["/bin/bash", script], stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError:
                status = "failure"

            # 3. Report status
            state = {"job_id": job["job_id"],
                     "status": status,
                     "comment": "no comments"}
            jobstate = requests.post("%s/jobstates" % _DCI_CONTROL_SERVER,
                                     data=state).json()
            print("[*] jobstate created: %s" % jobstate["id"])

            logs_data = {"name": script + '_log',
                         "content": output,
                         "mime": "text/plain",
                         "jobstate_id": jobstate["id"]}
            logs = requests.post("%s/files" % _DCI_CONTROL_SERVER,
                                 data=logs_data).json()

            print("[*] logs created: %s" % logs["id"])
            if status == "failure":
                break

        state = {"job_id": job["job_id"],
                 "status": "success",
                 "comment": "no comments"}
        jobstate = requests.post("%s/jobstates" % _DCI_CONTROL_SERVER,
                                 data=state).json()
    elif conf.command == 'get':
        job = requests.get("%s/jobs/get_job_by_platform/%s" %
                           (_DCI_CONTROL_SERVER, conf.platform)).json()

        table_result = prettytable.PrettyTable(["job", "environment"])
        table_result.add_row([job["job_id"], job["url"]])
        print(table_result)

if __name__ == '__main__':
    main()
