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
import time

import prettytable
import requests
import six


_DCI_CONTROL_SERVER = os.environ.get("DCI_CONTROL_SERVER",
                                     "http://127.0.0.1:5000")


def _init_conf():
    parser = argparse.ArgumentParser(description='DCI client.')
    command_subparser = parser.add_subparsers(help='commands',
                                              dest='command')
    # register remoteci command
    register_remoteci_parser = command_subparser.add_parser(
        'register-remoteci', help='Register a remoteci.')
    register_remoteci_parser.add_argument('--name', action='store',
                                          help='Name of the remoteci.')

    # list command
    list_parser = command_subparser.add_parser('list', help='List resources.')
    list_parser.add_argument('--remotecis', action='store_true',
                             default=False,
                             help='List existing remotecis.')
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
    auto_parser.add_argument('remoteci', action='store',
                             help='Id of the remoteci')

    # get command
    auto_parser = command_subparser.add_parser('get', help='Get a job.')
    auto_parser.add_argument('remoteci', action='store',
                             help='Id of the remoteci')

    return parser.parse_args()


# NOTE(Gonéri): Note used anymore
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


def _upload_file(fd, jobstate, mime='text/plain', name=None):
    fd.seek(0)
    output = ""
    for l in fd:
        output += l.decode("UTF-8")
    logs_data = {"name": name,
                 "content": output,
                 "mime": mime,
                 "jobstate_id": jobstate["id"]}
    return requests.post("%s/files" % _DCI_CONTROL_SERVER,
                         data=logs_data).json()


def _call_command(args, job, cwd=None, env=None):
    # TODO(Gonéri): Catch exception in subprocess.Popen
    p = subprocess.Popen(args,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         cwd=cwd,
                         env=env)
    state = {"job_id": job["job_id"],
             "status": "ongoing",
             "comment": "calling: " + " ".join(args)}
    jobstate = requests.post("%s/jobstates" %
                             _DCI_CONTROL_SERVER,
                             data=state).json()

    f = tempfile.TemporaryFile()
    while p.returncode is None:
        # TODO(Gonéri): print on STDOUT p.stdout
        time.sleep(0.5)
        for c in p.stdout:
            print(c.decode("UTF-8"))
            f.write(c)
        p.poll()

    _upload_file(f, jobstate, name='ksgen_log')

    try:
        if p.returncode != 0:
            state = {
                "job_id": job["job_id"],
                "status": "failure",
                "comment": "call failed w/ code %s" % p.returncode}
            raise RuntimeError
        else:
            state = {
                "job_id": job["job_id"],
                "status": "ongoing",
                "comment": "call successed w/ code %s" % p.returncode}
    finally:
        jobstate = requests.post("%s/jobstates" %
                                 _DCI_CONTROL_SERVER,
                                 data=state).json()
    return jobstate


def main():
    conf = _init_conf()

    if conf.command == 'list':
        if conf.remotecis:
            table_result = prettytable.PrettyTable(["identifier", "name",
                                                    "created_at", "updated_at"])
            remotecis = requests.get("%s/remotecis" %
                                     _DCI_CONTROL_SERVER).json()

            for remoteci in remotecis["_items"]:
                table_result.add_row([remoteci["id"],
                                     remoteci["name"],
                                     remoteci["created_at"],
                                     remoteci["updated_at"]])
            print(table_result)
        elif conf.jobs:
            table_result = prettytable.PrettyTable(["identifier",
                                                    "remoteci", "scenario",
                                                    "updated_at"])
            jobs = requests.get("%s/jobs" % _DCI_CONTROL_SERVER).json()

            for job in jobs["_items"]:
                table_result.add_row([job["id"],
                                      job["remoteci_id"],
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
    elif conf.command == 'register-remoteci':
        new_remoteci = {"name": conf.name}
        requests.post("%s/remotecis" % _DCI_CONTROL_SERVER,
                      data=new_remoteci).json()
        print("RemoteCI '%s' created successfully." % conf.name)
    elif conf.command == 'auto':
        # 1. Get a job
        job = requests.get(
            "%s/jobs/get_job_by_remoteci/%s" %
            (_DCI_CONTROL_SERVER, conf.remoteci)).json()

        if 'data' not in job:
            print("No job to processed")
            return

        structure_from_server = job['data']

        # TODO(Gonéri): Create a log_config() method or something similar
        import yaml
        settings = yaml.load(open('local_settings.yml', 'r'))

        for k, v in six.iteritems(structure_from_server['ksgen_args']):
            settings['ksgen_args'][k] = v.replace(
                '%%KHALEESI_SETTINGS%%',
                settings['location']['khaleesi_settings'])
        args = [settings['location'].get('python_bin', 'python'),
                './tools/ksgen/ksgen/core.py',
                '--config-dir=%s/settings' % (
                    settings['location']['khaleesi_settings']),
                'generate']
        for k, v in six.iteritems(settings['ksgen_args']):
            args.append('--%s=%s' % (k, v))
        ksgen_settings_file = tempfile.NamedTemporaryFile()
        args.append(ksgen_settings_file.name)
        environ = os.environ
        environ['PYTHONPATH'] = './tools/ksgen'

        collected_files_path = ("%s/collected_files" %
                                settings['location']['khaleesi'])
        if os.path.exists(collected_files_path):
            shutil.rmtree(collected_files_path)
        _call_command(args,
                      job,
                      cwd=settings['location']['khaleesi'],
                      env=environ)

        args = [
            './run.sh', '-vvvv', '--use',
            ksgen_settings_file.name,
            'playbooks/packstack.yml']
        _call_command(args,
                      job,
                      cwd=settings['location']['khaleesi'])
        for log in glob.glob(collected_files_path + '/*'):
            with open(log) as f:
                _upload_file(f, jobstate)

        state = {"job_id": job["job_id"],
                 "status": "success",
                 "comment": "no comments"}
        jobstate = requests.post("%s/jobstates" % _DCI_CONTROL_SERVER,
                                 data=state).json()

    elif conf.command == 'get':
        job = requests.get("%s/jobs/get_job_by_remoteci/%s" %
                           (_DCI_CONTROL_SERVER, conf.remoteci)).json()

        table_result = prettytable.PrettyTable(["job", "environment"])
        table_result.add_row([job["job_id"], job["url"]])
        print(table_result)

if __name__ == '__main__':
    main()
