#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# This script will connect on a Gerrit server and list the pending reviews.
# It will create the associated review in the DCI server and associate the
# tox check.
# If the version already exist, it will sync back the status of the version
# in Gerrit (-1/0/+1)

import subprocess
import sys
import yaml

import client


def sync_project(project):
    gerrit_server = project['gerrit_server']
    product_name = project['product_name']
    product_project = project['product_project']
    test_name = project['test_name']
    product_data = project.get('product_data', {})

    reviews = subprocess.check_output(['ssh', '-xp29418',
                                       gerrit_server,
                                       'gerrit', 'query', '--format=json',
                                       'project:%s' % product_project,
                                       'status:open'])
    dci_client = client.DCIClient()
    product = dci_client.find_or_create_or_refresh('/products', {
        'name': product_name, 'data': product_data})
    test = dci_client.find_or_create_or_refresh('/tests', {
        'name': test_name, 'data': {}})

    for line in reviews.decode('utf-8').rstrip().split('\n'):
        review = yaml.load(line)
        if 'id' not in review:
            continue
        patchset_query_res = subprocess.check_output([
            'ssh', '-xp29418', gerrit_server,
            'gerrit', 'query', '--format=JSON',
            '--current-patch-set change:%d' % int(review['number'])])
        patchset = yaml.load(patchset_query_res.decode('utf-8').split('\n')[0])
        subject = patchset['commitMessage'].split('\n')[0]
        message = patchset['commitMessage']
        gerrit_id = patchset['id']
        url = patchset['url']
        ref = patchset['currentPatchSet']['ref']
        sha = patchset['currentPatchSet']['revision']
        versions = dci_client.get("/versions", where={'sha': sha}).json()

        if len(versions['_items']) == 0:
            r = dci_client.post("/versions", {
                "product_id": product['id'],
                "name": subject,
                "title": subject,
                "message": message,
                "sha": sha,
                "url": url,
                "data": {
                    product_name: {
                        "git": (
                            # "http://%s/r/%s" % (gerrit_server, product_project)),
                            # NOTE(Gonéri) the /r/ should not be in the URL with
                            # gerrithub.io
                            "http://%s/%s" % (gerrit_server, product_project)),
                        "ref": ref,
                        "sha": sha,
                        "gerrit_id": gerrit_id
                    }
                }
            })
            version = r.json()
            dci_client.post("/testversions", {
                "test_id": test['id'],
                "version_id": version['id'],
            })
        else:
            version = versions['_items'][0]
            testversions = dci_client.get(
                "/testversions",
                where={'version_id': version['id']}).json()
            status = '0'
            for testversion in testversions['_items']:
                jobs = dci_client.get(
                    "/jobs",
                    where={'testversion_id': testversion['id']},
                    embedded={'jobstates_collection': 1}).json()
                for job in jobs['_items']:
                    last_job_status = job['jobstates_collection'][-1]['status']
                    if last_job_status == 'failure':
                        status = '-1'
                        break
                    elif last_job_status == 'success':
                        status = '1'
            try:
                sha = version['data'][product_name]['sha']
            except KeyError:
                print("Cannot find product name for version "
                      "%s" % version['id'])
                return
            o = subprocess.check_output([
                # NOTE(Gonéri): The echo is here on purpose
                'echo', 'ssh', '-xp29418', gerrit_server,
                'gerrit', 'review', '--verified', status,
                version['data'][product_name]['sha']])
            print("%s: %s" % (subject, status))
            print(o)

projects = [
    {
        'gerrit_server': 'review.gerrithub.io',
        'product_name': 'khaleesi',
        'product_project': 'redhat-openstack/khaleesi',
        'test_name': 'khaleesi-tempest',
        'product_data': {
            "ksgen_args": {
                "provisioner": "manual",
                "product": "rdo",
                "product-version": "kilo",
                "product-version-repo": "delorean",
                "product-version-workaround": "rhel-7.0",
                "workarounds": "enabled",
                "distro": "centos-7.0",
                "installer": "rdo_manager",
                "installer-env": "virthost",
                "installer-topology": "minimal",
                "extra-vars": ["product.repo_type_override=none"]}}
    },
    {
        'gerrit_server': 'softwarefactory.enovance.com',
        'product_name': 'dci-control-server',
        'product_project': 'dci-control-server',
        'test_name': 'tox'},
]

for project in projects:
    sync_project(project)

