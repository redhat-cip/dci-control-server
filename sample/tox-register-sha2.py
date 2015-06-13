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

import client
import requests


def sha_walker(dci_client, sha, product_id, test_id):
    # NOTE(Gonéri): Is the commit already here?
    r = dci_client.get("/versions/%s" % sha)
    if r.status_code == 200:
        return

    commit = gh_s.get(
        'https://api.github.com/'
        'repos/enovance/dci-control-server/git/commits/%s' % sha).json()
    message = commit['message']
    title = message.split('\n')[0]
    print('%s - %s' % (sha, title))
    version_id = dci_client.post("/versions", {
        "product_id": product_id,
        "name": sha,
        "title": title,
        "message": message,
        "sha": sha,
        "data": {
            "sha2": sha
        }
    }).json()['id']
    dci_client.post("/testversions", {
        "test_id": test_id,
        "version_id": version_id,
    }).json()['id']

    if 'parents' in commit:
        for parent in commit['parents']:
            sha_walker(dci_client, parent['sha'], product_id, test_id)


dci_client = client.DCIClient()

product_name = "dci-control-server"

r = dci_client.get("/products/%s" % product_name)
if r.status_code == 404:
    r = dci_client.post("/products", {
        "name": "dci-control-server",
        "data": {
            "git_url": "https://github.com/enovance/dci-control-server"}}
    )
product_id = r.json()['id']
test_id = dci_client.post("/tests", {
    "name": "tox",
}).json()['id']

gh_s = requests.Session()
# gh_s.auth = ('user', 'xxxxx')
r = gh_s.get(
    'https://api.github.com/repos/'
    'enovance/dci-control-server'
    '/branches')
branches = {a['name']: a['commit'] for a in r.json()}
sha = branches['master']['sha']
sha_walker(dci_client, sha, product_id, test_id)
