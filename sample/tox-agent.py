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

DCI_CONTROL_SERVER = 'http://127.0.0.1:5000/api'
LOGIN = 'partner'
PASSWORD = 'partner'
WORKDIR = '/tmp/dci-tox'
REMOTECI_ID = 'aa575254-54f1-0663-f3c6-f1f1c5551ff3'

import subprocess
import tempfile
import time

import client

dci_client = client.DCIClient(DCI_CONTROL_SERVER, LOGIN, PASSWORD)

job_id = dci_client.post("/jobs", {"remoteci_id": REMOTECI_ID})
job = dci_client.get("/jobs/%s" % job_id)
structure_from_server = job['data']
subprocess.call(['git', 'init', WORKDIR])
subprocess.call(['git', 'remote', 'add', 'origin',
                 structure_from_server['git_url']], cwd=WORKDIR)
subprocess.call(['git', 'fetch', '--all'], cwd=WORKDIR)
subprocess.call(['git', 'clean', '-ffdx'], cwd=WORKDIR)
subprocess.call(['git', 'reset', '--hard'], cwd=WORKDIR)
subprocess.call(['git', 'checkout', '-f', structure_from_server['sha2']],
                cwd=WORKDIR)

p = subprocess.Popen(['tox'],
                     stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT,
                     cwd=WORKDIR)
state = {"job_id": job_id,
         "status": "ongoing",
         "comment": "calling tox"}
jobstate_id = dci_client.post("/jobstates", state)

f = tempfile.TemporaryFile()
while p.returncode is None:
    # TODO(Gonéri): print on STDOUT p.stdout
    time.sleep(1)
    for c in p.stdout:
        print(c.decode("UTF-8"))
        f.write(c)
    p.poll()

dci_client.upload_file(f, jobstate_id, name='tox.log')

status = "succes" if p.returncode == 0 else "failure"
state = {
    "job_id": job["id"],
    "status": status,
    "comment": "call %s w/ code %s" % (status, p.returncode)}
jobstate_id = dci_client.post("/jobstates", state)
