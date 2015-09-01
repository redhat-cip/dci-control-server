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

import argparse
import os
import sys

import json
import subprocess
import yaml

import client


def _get_open_reviews(gerrit_server, gerrit_project):
    """Get open reviews from Gerrit."""
    user = os.environ.get("GERRIT_USER") or os.getlogin()
    reviews = subprocess.check_output(['ssh', '-xp29418', gerrit_server,
                                       '-l', user, 'gerrit', 'query',
                                       '--format=json',
                                       'project:%s' % gerrit_project,
                                       'status:open'])
    reviews = reviews.decode('utf-8').rstrip().split('\n')[:-1]
    return [json.loads(review) for review in reviews]


def _get_last_patchset(gerrit_server, review_number):
    """Get the last patchset of a review."""
    user = os.environ.get("GERRIT_USER") or os.getlogin()
    lpatchset = subprocess.check_output(['ssh', '-xp29418', '-l', user,
                                         gerrit_server, 'gerrit', 'query',
                                         '--format=JSON',
                                         '--current-patch-set change:%d' %
                                         review_number])
    lpatchset = lpatchset.decode('utf-8').rstrip().split('\n')[0]
    return json.loads(lpatchset)


def _gerrit_review(gerrit_server, patch_sha, status):
    user = os.environ.get("GERRIT_USER") or os.getlogin()
    subprocess.check_output(['ssh', '-xp29418', '-l', user, gerrit_server,
                             'gerrit', 'review', '--verified', status,
                             patch_sha])


def list_open_patchsets(gerrit):
    """Generator that returns the last patchsets of all the reviews of
    a given project.
    """

    reviews = _get_open_reviews(gerrit['server'],
                                gerrit['project'])
    for review in reviews:
        yield _get_last_patchset(gerrit['server'],
                                 int(review['number']))


def push_patchset_as_version_in_dci(dci_client, product, component_name,
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

    component_name = project["gerrit"]["project"]

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
    _gerrit_review(project["gerrit"]["server"], sha, status)


def _init_conf():
    parser = argparse.ArgumentParser(description='Gerrit agent.')
    parser.add_argument("--config-file", action="store",
                        help="the configuration file path")
    return parser.parse_args()


def _get_config_file(config_file_path):
    if not os.path.exists(config_file_path):
        print("cannot open configuration file '%s'" % config_file_path)
        sys.exit(1)
    else:
        return yaml.load(open(config_file_path).read())


def main():
    conf = _init_conf()
    if conf.config_file:
        config_file = _get_config_file(conf.config_file)
    else:
        print("config file missing")
        sys.exit(1)

    projects = [project for project in config_file["products"]
                if project["enable"]]

    dci_client = client.DCIClient()
    for project in projects:
        test_name = project['gerrit']['test']

        test = dci_client.find_or_create_or_refresh(
            '/tests',
            {'name': test_name, 'data': {}})

        git_url = "http://%s/%s" % (project["gerrit"]["server"],
                                    project["gerrit"]["project"])

        for patchset in list_open_patchsets(project["gerrit"]):
            product = dci_client.find_or_create_or_refresh(
                '/products',
                {'name': project["name"], 'data': project['data']})
            version = push_patchset_as_version_in_dci(
                dci_client, product,
                project["gerrit"]["name"],
                test, patchset, git_url)
            review_patchset(dci_client, project, version)

if __name__ == '__main__':
    main()
