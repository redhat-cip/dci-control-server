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
import sys
import tempfile
import time

import bcrypt
import prettytable

import client


def _init_conf(args=None):
    parser = argparse.ArgumentParser(description='DCI client.')
    command_subparser = parser.add_subparsers(help='commands',
                                              dest='command')

    # list resources command
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
    list_parser.add_argument('--users', action="store_true",
                             default=False,
                             help='List existing users.')

    # TODO(yassine): add the team and role options
    # create a user
    create_node_parser = command_subparser.add_parser(
        'create_user', help='create a user')
    create_node_parser.add_argument('username', action='store',
                                    help='the user name')
    create_node_parser.add_argument('password', action='store',
                                    help='the user password')

    # delete user
    create_node_parser = command_subparser.add_parser(
        'delete_user', help='delete a user')
    create_node_parser.add_argument('username', action='store',
                                    help='the user name to delete')

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
    dci_login = os.environ.get("DCI_LOGIN")
    dci_password = os.environ.get("DCI_PASSWORD")
    dci_cs_url = os.environ.get('DCI_CS_URL', "http://127.0.0.1:5000/api")

    if not dci_login or not dci_password:
        print("DCI credentials missing: 'DCI_LOGIN': %s, 'DCI_PASSWORD: %s" %
              dci_login, dci_password)
        sys.exit(1)

    dci_client = client.DCIClient("%s/api" % dci_cs_url, dci_login,
                                  dci_password)

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
            table_result = prettytable.PrettyTable(["identifier", "remoteci",
                                                    "testversion",
                                                    "updated_at"])
            jobs = dci_client.get("/jobs").json()

            for job in jobs["_items"]:
                table_result.add_row([job["id"],
                                      job["remoteci_id"],
                                      job["testversion_id"],
                                      job["updated_at"]])
            print(table_result)
        elif conf.jobstates:
            table_result = prettytable.PrettyTable(["identifier", "status",
                                                    "comment", "job",
                                                    "updated_at"])
            jobstates = dci_client.get("/jobstates").json()

            for jobstate in jobstates["_items"]:
                table_result.add_row([jobstate["id"],
                                      jobstate["status"],
                                      jobstate["comment"],
                                      jobstate["job_id"],
                                      jobstate["updated_at"]])
            print(table_result)
        elif conf.users:
            table_result = prettytable.PrettyTable(["identifier", "name"])
            users = dci_client.get("/users").json()

            for user in users["_items"]:
                table_result.add_row([user["id"], user["name"]])
            print(table_result)
        elif args.command == 'create_user':
            password_hash = bcrypt.hashpw(args.password, bcrypt.gensalt())

            dci_client.post("/api/users", {"name": args.username,
                                           "password": password_hash})
            print("User '%s' created." % args.username)
        elif args.command == 'delete_user':
            dci_user = dci_client.get("/api/users/%s" % args.username)
            if dci_user.status_code != 200:
                print("User '%s' does not exist." % args.username)
                sys.exit(1)
            dci_user = dci_user.json()
            print(dci_client.delete("/api/users/%s" % args.username,
                                    etag=dci_user["etag"]).json())

if __name__ == '__main__':
    main(sys.argv[1:])
