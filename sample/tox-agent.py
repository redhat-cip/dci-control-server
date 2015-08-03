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

import shutil
import sys
import tempfile

import client

try:
    remoteci_name = sys.argv[1]
except IndexError:
    print("Usage: %s remoteci_name" % sys.argv[0])
    sys.exit(1)


workdir = tempfile.mkdtemp(suffix='dci_tox_agent')

dci_client = client.DCIClient()

test_name = "tox"

r = dci_client.get("/tests/%s" % test_name)
if r.status_code == 404:
    print("Test '%s' doesn't exist." % test_name)
    sys.exit(1)
else:
    test_id = r.json()['id']
r = dci_client.get("/remotecis/%s" % remoteci_name)
if r.status_code == 404:
    r = dci_client.post("/remotecis", {
        'name': remoteci_name,
        'test_id': test_id})
remoteci_id = r.json()['id']
job_id = dci_client.post("/jobs", {"remoteci_id": remoteci_id}).json()['id']
job = dci_client.get("/jobs/%s" % job_id).json()
dci_client.call(job_id, ['git', 'init', workdir])
structure_from_server = job['data']['components']['dci-control-server']
dci_client.call(job_id, ['git', 'pull',
                         structure_from_server['git'],
                         structure_from_server.get('ref', '')],
                cwd=workdir, ignore_error=True)
dci_client.call(job_id, ['git', 'fetch', '--all'], cwd=workdir)
dci_client.call(job_id, ['git', 'clean', '-ffdx'], cwd=workdir)
dci_client.call(job_id, ['git', 'reset', '--hard'], cwd=workdir)
dci_client.call(job_id, ['git', 'checkout', '-f',
                         structure_from_server['sha']],
                cwd=workdir)

try:
    dci_client.call(job_id, ['tox'], cwd=workdir)
except client.DCICommandFailure:
    print("Test has failed")
    pass
else:
    state = {
        "job_id": job["id"],
        "status": "success",
        "comment": "Process finished successfully"}
    jobstate_id = dci_client.post("/jobstates", state)

shutil.rmtree(workdir)
