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


class Gerrit(object):
    def __init__(self, gerrit_server):
        self.user = os.environ.get("GERRIT_USER") or os.getlogin()
        self.server = gerrit_server

    def get_open_reviews(self, gerrit_project):
        """Get open reviews from Gerrit."""
        gerrit_filter = (
            'project:%s status:open is:open '
            'is:mergeable NOT label:Verified<=-1') % gerrit_project
        reviews = subprocess.check_output(['ssh', '-xp29418', self.server,
                                           '-l', self.user, 'gerrit', 'query',
                                           '--format=json',
                                           gerrit_filter])
        reviews = reviews.decode('utf-8').rstrip().split('\n')[:-1]
        return [json.loads(review) for review in reviews]

    def get_last_patchset(self, review_number):
        """Get the last patchset of a review."""
        lpatchset = subprocess.check_output([
            'ssh', '-xp29418', '-l', self.user,
            self.server, 'gerrit', 'query',
            '--format=JSON',
            '--current-patch-set change:%d' %
            review_number])
        lpatchset = lpatchset.decode('utf-8').rstrip().split('\n')[0]
        return json.loads(lpatchset)

    def review(self, patch_sha, status):
        """Push a score (e.g: -1) on a review."""
        subprocess.check_output(['ssh', '-xp29418', '-l',
                                 self.user, self.server,
                                 'gerrit', 'review', '--verified', status,
                                 patch_sha])

    def list_open_patchsets(self, project):
        """Generator that returns the last patchsets of all the reviews of
        a given project.
        """

        reviews = self.get_open_reviews(project)
        for review in reviews:
            yield self.get_last_patchset(int(review['number']))


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


def get_patchset_score(dci_client, component_name, version):
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
        sha = version['data']['components'][component_name]['sha']
    except KeyError:
        print("Cannot find product name for version "
              "%s" % version['id'])
        return
    return {'sha': sha, 'status': status}


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
        # NOTE(Gonéri): ensure the associated test and product exist and are
        # up to date
        g = Gerrit(project['gerrit']['server'])
        test = dci_client.find_or_create_or_refresh(
            '/tests',
            {'name': project['gerrit']['test'], 'data': {}})
        project_data = project['data'] if 'data' in project else {}
        product = dci_client.find_or_create_or_refresh(
            '/products', {'name': project["name"], 'data': project_data})

        if 'git_url' in project['gerrit']:
            git_url = project['gerrit']['git']
        else:
            git_url = "http://%s/%s" % (project["gerrit"]["server"],
                                        project["gerrit"]["project"])

        # NOTE(Gonéri): For every review of a component, we
        # - create a version that overwrite the component default origin
        # with a one that is sticked to the review
        # - check if there is some result for the Git review, and if so,
        # push vote
        for patchset in g.list_open_patchsets(project['gerrit']['project']):
            version = push_patchset_as_version_in_dci(
                dci_client, product,
                project["gerrit"]["name"],
                test, patchset, git_url)
            score = get_patchset_score(dci_client,
                                       project["gerrit"]["project"],
                                       version)
            # TODO(Gonéri): also push a message and the URL to see the job.
            if score and score['status'] != 0:
                print("DCI-CS → Gerrit: %s" % score['status'])
                g.review(score['sha'], score['status'])

if __name__ == '__main__':
    main()
