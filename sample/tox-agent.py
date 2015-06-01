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

WORKDIR = '/tmp/dci-tox'

import subprocess
import sys
import tempfile
import time

import client


def call(arg, cwd=None, ignore_error=False):
    state = {"job_id": job_id,
             "status": "ongoing",
             "comment": "calling: %s" % " ".join(arg)}
    jobstate_id = dci_client.post("/jobstates", state)
    try:
        p = subprocess.Popen(arg,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             cwd=cwd)
    except OSError as e:
        state = {"job_id": job_id,
                 "status": "failure",
                 "comment": "internal failure: %s" % e}
        dci_client.post("/jobstates", state)
        sys.exit(1)

    f = tempfile.TemporaryFile()
    while p.returncode is None:
        # TODO(Gonéri): print on STDOUT p.stdout
        time.sleep(1)
        for c in p.stdout:
            print(c.decode("UTF-8").rstrip())
            f.write(c)
        p.poll()
    dci_client.upload_file(f, jobstate_id, name='output.log')

    if p.returncode != 0 and not ignore_error:
        state = {"job_id": job_id,
                 "status": "failure",
                 "comment": "call failure w/ code %s" % (p.returncode)}
        dci_client.post("/jobstates", state)
        sys.exit(0)


try:
    remoteci_name = sys.argv[1]
except IndexError:
    print("Usage: %s remoteci_name" % sys.argv[0])
    sys.exit(1)


dci_client = client.DCIClient()

remoteci = dci_client.get("/remotecis/%s" % remoteci_name)
if '_error' in remoteci and remoteci['_error']['code'] == 404:
    remoteci_id = dci_client.post("/remotecis", {'name': remoteci_name})
else:
    remoteci_id = remoteci['id']
job_id = dci_client.post("/jobs", {"remoteci_id": remoteci_id})
job = dci_client.get("/jobs/%s" % job_id)
structure_from_server = job['data']
call(['git', 'init', WORKDIR])
call(['git', 'remote', 'add', 'origin',
      structure_from_server['git_url']], cwd=WORKDIR, ignore_error=True)
call(['git', 'fetch', '--all'], cwd=WORKDIR)
call(['git', 'clean', '-ffdx'], cwd=WORKDIR)
call(['git', 'reset', '--hard'], cwd=WORKDIR)
call(['git', 'checkout', '-f', structure_from_server['sha2']],
     cwd=WORKDIR)
call(['tox'], cwd=WORKDIR)

state = {
    "job_id": job["id"],
    "status": "success",
    "comment": "Process finished successfully"}
jobstate_id = dci_client.post("/jobstates", state)
