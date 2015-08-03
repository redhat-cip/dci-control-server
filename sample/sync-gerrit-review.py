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
import yaml

import client


# TODO(Gonéri): use a more meaningful name to make clear this is
# gerrit specific function.
def list_open_patchset(dci_client, project):
    """Generator that return a patchset for a given project."""
    gerrit_server = project['gerrit_server']
    gerrit_project = project['gerrit_project']

    reviews = subprocess.check_output(['ssh', '-xp29418',
                                       gerrit_server,
                                       'gerrit', 'query', '--format=json',
                                       'project:%s' % gerrit_project,
                                       'status:open'])
    for line in reviews.decode('utf-8').rstrip().split('\n'):
        review = yaml.load(line)
        if 'id' not in review:
            continue
        patchset_query_res = subprocess.check_output([
            'ssh', '-xp29418', gerrit_server,
            'gerrit', 'query', '--format=JSON',
            '--current-patch-set change:%d' % int(review['number'])])
        patchset = yaml.load(patchset_query_res.decode('utf-8').split('\n')[0])
        yield patchset


def push_patchset_in_dci(dci_client, product, component_name,
                         test, patchset, git_url):
    """Create a version in DCI-CS from a gerrit patchset."""
    subject = patchset['commitMessage'].split('\n')[0]
    message = patchset['commitMessage']
    gerrit_id = patchset['id']
    url = patchset['url']
    ref = patchset['currentPatchSet']['ref']
    sha = patchset['currentPatchSet']['revision']
    print("Gerrit → DCI-CS: %s" % subject)
    version_data = {
        "product_id": product['id'],
        "name": subject,
        "title": subject,
        "message": message,
        "sha": sha,
        "url": url,
        # TODO(Gonéri): We use components/$name/ref now
        "ref": "",
        "data": {
            'components': {
                component_name: {
                    "git": git_url,
                    "ref": ref,
                    "sha": sha,
                    "gerrit_id": gerrit_id
                }
            }
        }
    }
    version = dci_client.find_or_create_or_refresh(
        '/versions', version_data, unicity_key=['sha'])
    dci_client.find_or_create_or_refresh(
        '/testversions',
        {'test_id': test['id'], 'version_id': version['id']},
        unicity_key=['test_id', 'version_id'])
    return version


def review_patchset(dci_client, product, version):
    """Update the review in Gerrit from the status of a version in DCI-CS."""
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
        sha = version['data'][product['name']]['sha']
    except KeyError:
        print("Cannot find product name for version "
              "%s" % version['id'])
        return
    subprocess.check_output([
        # NOTE(Gonéri): The echo is here on purpose
        'ssh', '-xp29418', gerrit_server,
        'gerrit', 'review', '--verified', status,
        sha])

# NOTE(Gonéri): this configuration structure should probably be exported in
# some flat configuration files.
# ksgen --config-dir=../khaleesi-settings/settings generate \
#       --provisioner=manual \
#       --product=rhos \
#       --product-version=7_director \
#       --product-version-build=latest \
#       --product-repo=puddle \
#       --distro=rhel-7.1 \
#       --installer=rdo_manager \
#       --installer-env=virthost \
#       --installer-images=build \
#       --installer-network=neutron \
#       --installer-network-variant=ml2-vxlan \
#       --installer-topology=minimal \
#       --extra-vars product.repo_type_override=none \
#       ksgen_settings.yml
projects = [
    {
        'gerrit_server': 'review.gerrithub.io',
        'product_name': 'rhos',
        'gerrit_project': 'redhat-openstack/khaleesi',
        'gerrit_local_component_name': 'khaleesi',
        'test_name': 'khaleesi-tempest',
        'git_url_format': 'http://{server}/{project}',
        'product_data': {
            "ksgen_args": {
                "provisioner": "manual",
                "product": "rhos",
                "product-version": "7_director",
                "product-version-build": "latest",
                "product-repo": "puddle",
                "distro": "rhel-7.1",
                "installer": "rdo_manager",
                "installer-env": "virthost",
                "installer-images": "build",
                "installer-network": "neutron",
                "installer-network-variant": "ml2-vxlan",
                "installer-topology": "minimal",
                "extra-vars": ["product.repo_type_override=none"]},
            # TODO(Gonéri): add a key to specify the rhos repo snapshot
            'components': {
                'khaleesi': {
                    'git': 'http://github.com/redhat-openstack/khaleesi'},
                'khaleesi-settings': {
                    'git': '/home/goneri/khaleesi-settings-mirror'}
            }
        }},
    {
        'gerrit_server': 'softwarefactory.enovance.com',
        'gerrit_project': 'dci-control-server',
        'product_name': 'dci-control-server',
        'local_gerrit_component_name': 'dci-control-server',
        'test_name': 'tox',
        'publish_review': True
    }
]

dci_client = client.DCIClient()
for project in projects:
    product_name = project['product_name']
    product_data = project.get('product_data', {})

    test_name = project['test_name']

    gerrit_project = project['gerrit_project']
    git_url_format = project.get('git_url_format',
                                 'http://{server}/r/{project}')
    gerrit_server = project['gerrit_server']
    gerrit_local_component_name = project['gerrit_local_component_name']

    print("---------------BEGIN")
    product = dci_client.find_or_create_or_refresh('/products', {
        'name': product_name, 'data': product_data})
    print("---------------END")
    from pprint import pprint
    test = dci_client.find_or_create_or_refresh('/tests', {
        'name': test_name, 'data': {}})

    git_url = git_url_format.format(server=gerrit_server,
                                    project=gerrit_project)
    for patchset in list_open_patchset(dci_client, project):
        version = push_patchset_in_dci(
            dci_client, product,
            gerrit_local_component_name,
            test, patchset, git_url)
        if project.get('publish_review', False):
            review_patchset(dci_client, product, version)
