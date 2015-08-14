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

import os

import json
import subprocess

import client


def _get_open_reviews(gerrit_server, gerrit_project):
    """Get open reviews from Gerrit."""
    reviews = subprocess.check_output(['ssh', '-xp29418', gerrit_server,
                                       'gerrit', 'query', '--format=json',
                                       'project:%s' % gerrit_project,
                                       'status:open'])
    reviews = reviews.decode('utf-8').rstrip().split('\n')[:-1]
    return [json.loads(review) for review in reviews]


def _get_last_patchset(gerrit_server, review_number):
    """Get the last patchset of a review."""
    lpatchset = subprocess.check_output(['ssh', '-xp29418', gerrit_server,
                                        'gerrit', 'query', '--format=JSON',
                                        '--current-patch-set change:%d' %
                                        review_number])
    lpatchset = lpatchset.decode('utf-8').rstrip().split('\n')[0]
    return json.loads(lpatchset)


def _gerrit_review(gerrit_server, patch_sha, status):
    subprocess.check_output(['ssh', '-xp29418', gerrit_server, 'gerrit',
                             'review', '--verified', status, patch_sha])


def list_open_patchsets(project):
    """Generator that returns the last patchsets of all the reviews of
    a given project."""

    reviews = _get_open_reviews(project['gerrit_server'],
                                project['gerrit_project'])
    for review in reviews:
        yield _get_last_patchset(project['gerrit_server'],
                                 int(review['number']))


def push_patchset_in_dci(dci_client, product, component_name,
                         test, patchset, git_url):
    """Create a version in DCI-CS from a gerrit patchset."""
    subject = patchset['commitMessage'].split('\n')[0]
    message = patchset['commitMessage']
    gerrit_id = patchset['id']
    url = patchset['url']
    ref = patchset['currentPatchSet']['ref']
    sha = patchset['currentPatchSet']['revision']
    print("Gerrit to DCI-CS: %s" % subject)
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
                    "gerrit_id": gerrit_id,
                    "url": url,
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


def review_patchset(dci_client, project, version):
    """Update the review in Gerrit from the status of a version in DCI-CS."""

    gerrit_server = project['gerrit_server']
    component_name = project['component_name']

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
        sha = version['data']['components'][component_name]['sha']
    except KeyError:
        print("Cannot find product name for version "
              "%s" % version['id'])
        return
    # TODO(Gonéri): also push a message and the URL to see the job.
    print("DCI-CS → Gerrit: %s" % status)
    _gerrit_review(gerrit_server, sha, status)

# NOTE(Gonéri): This structure should be in a configuration files instead.
products = {
    'rdo': {
        'name': 'rdo',
        'data': {
            "ksgen_args": {
                "provisioner": "manual",
                "product": "rdo",
                "product-version": "kilo",
                "product-version-repo": "delorean",
                "product-version-workaround": "centos-7.0",
                "workarounds": "enabled",
                "distro": "centos-7.0",
                "installer": "rdo_manager",
                "installer-env": "virthost",
                "installer-images": "build",
                "installer-network": "neutron",
                "installer-network-variant": "ml2-vxlan",
                "installer-topology": "minimal",
                "extra-vars": ["product.repo_type_override=none"]},
            'components': {
                'khaleesi': {
                    'git': 'http://github.com/redhat-openstack/khaleesi'},
                'khaleesi-settings': {
                    'git': '/home/goneri/khaleesi-settings-mirror'}
            }
        }},
    'rhos': {
        'name': 'rhos',
        'data': {
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
            'components': {
                'khaleesi': {
                    'git': 'http://github.com/redhat-openstack/khaleesi'},
                'khaleesi-settings': {
                    'git': '/home/goneri/khaleesi-settings-mirror'}
            }
        }},
    'dci-control-server': {
        'name': 'dci-control-server',
        'data': {
            'components': {
                'dci-control-server': {
                    'git': 'https://github.com/redhat-cip/dci-control-server'
                }
            }
        }
    }
}

# NOTE(Gonéri): This structure should also be in a configuration file
gerrit_projects = [
    {
        'gerrit_server': 'softwarefactory.enovance.com',
        'gerrit_project': 'dci-control-server',
        'products_name': ['dci-control-server'],
        'test_name': 'tox',
        'component_name': 'dci-control-server',
        'publish_review': True
    }
]

dci_client = client.DCIClient()
for project in gerrit_projects:
    test_name = project['test_name']

    gerrit_project = project['gerrit_project']
    git_url_format = project.get('git_url_format',
                                 'http://{server}/r/{project}')
    try:
        project['gerrit_server'] = "%s@%s" % (os.environ["GERRIT_USER"],
                                              project['gerrit_server'])
        print("Using user %s" % os.environ["GERRIT_USER"])
    except KeyError:
        print("Using default user.")

    component_name = project['component_name']

    test = dci_client.find_or_create_or_refresh('/tests', {
        'name': test_name, 'data': {}})

    git_url = git_url_format.format(server=project['gerrit_server'],
                                    project=gerrit_project)
    for patchset in list_open_patchsets(project):
        for product_name in project['products_name']:
            product = dci_client.find_or_create_or_refresh(
                '/products',
                products[product_name])
            version = push_patchset_in_dci(
                dci_client, product,
                component_name,
                test, patchset, git_url)
            if project.get('publish_review', False):
                review_patchset(dci_client, project, version)
