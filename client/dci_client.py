#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
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

# NOTE(Gonéri): to be able to mock print with Py27
from __future__ import print_function

import argparse
import os
import subprocess
import tempfile
import time

import prettytable

import client

DCI_CONTROL_SERVER = os.environ.get("DCI_CONTROL_SERVER",
                                    "http://127.0.0.1:5000/api")


def _init_conf(args=None):
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

    print("args: %s" % args)
    return parser.parse_args(args)


def _call_command(dci_client, args, job, cwd=None, env=None):
    # TODO(Gonéri): Catch exception in subprocess.Popen
    p = subprocess.Popen(args,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         cwd=cwd,
                         env=env)
    state = {"job_id": job["id"],
             "status": "ongoing",
             "comment": "calling: " + " ".join(args)}
    jobstate_id = dci_client.post("/jobstates", state).json()['id']

    f = tempfile.TemporaryFile()
    while p.returncode is None:
        # TODO(Gonéri): print on STDOUT p.stdout
        time.sleep(0.5)
        for c in p.stdout:
            print(c.decode("UTF-8"))
            f.write(c)
        p.poll()

    dci_client.upload_file(f, jobstate_id, name='ksgen_log')

    if p.returncode != 0:
        state = {
            "job_id": job["id"],
            "status": "failure",
            "comment": "call failed w/ code %s" % p.returncode}
    else:
        state = {
            "job_id": job["id"],
            "status": "ongoing",
            "comment": "call successed w/ code %s" % p.returncode}
    jobstate_id = dci_client.post("/jobstates", state)
    return jobstate_id


def main(args=None):
    conf = _init_conf(args)
    dci_client = client.DCIClient(DCI_CONTROL_SERVER, "partner", "partner")

    if conf.command == 'list':
        if conf.remotecis:
            table_result = prettytable.PrettyTable([
                "identifier", "name",
                "created_at", "updated_at"])
            remotecis = dci_client.get("/remotecis").json()

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
            jobs = dci_client.get("/jobs")

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
            jobstates = dci_client("/jobstates")

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
            scenarios = dci_client.get("/scenarios")

            for scenario in scenarios["_items"]:
                table_result.add_row([scenario["id"],
                                      scenario["name"],
                                      scenario["updated_at"]])
            print(table_result)
    elif conf.command == 'register-remoteci':
        new_remoteci = {"name": conf.name}
        dci_client.post("/remotecis", new_remoteci)
        print("RemoteCI '%s' created successfully." % conf.name)


if __name__ == '__main__':
    main()
