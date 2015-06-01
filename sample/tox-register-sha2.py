#!/usr/bin/env python
#
# Copyright 2015 Red Hat, Inc.
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

DCI_CONTROL_SERVER = 'https://stable-dcics.rhcloud.com/api'

import subprocess

import client

dci_client = client.DCIClient(DCI_CONTROL_SERVER, 'admin', 'admin')

dci_client.delete("/testversions")
dci_client.delete("/versions")
dci_client.delete("/tests")
dci_client.delete("/products")

team = dci_client.get("/teams/partner")
product_id = dci_client.post("/products", {
    "name": "dci-control-server",
    "data": {
        "git_url": "https://github.com/enovance/dci-control-server"}}
).json()['id']
test_id = dci_client.post("/tests", {
    "name": "tox",
}).json()['id']
revisions = subprocess.check_output([
    "git", "log", "--no-merges", "--format=oneline"])
for revision in revisions.splitlines():
    a = revision.decode('utf-8').split(" ")
    version_id = dci_client.post("/versions", {
        "product_id": product_id,
        "name": " ".join(a[1:]),
        "data": {
            "sha2": a[0]
        }
    }).json()['id']
    testversion_id = dci_client.post("/testversions", {
        "test_id": test_id,
        "version_id": version_id,
    }).json()['id']
