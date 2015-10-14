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
import copy
import os
import sys

import json
import subprocess
import yaml

import client


class Gerrit(object):
    def __init__(self, gerrit_server, vote=False):
        self.user = os.environ.get("GERRIT_USER") or os.getlogin()
        self.server = gerrit_server
        self.vote = vote

    def get_open_reviews(self, gerrit_project, gerrit_filter):
        """Get open reviews from Gerrit."""
        gerrit_filter = (
            'project:%s status:open %s' % (gerrit_project, gerrit_filter))
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
        if self.vote:
            subprocess.check_output([
                'ssh', '-xp29418', '-l',
                self.user, self.server,
                'gerrit', 'review', '--verified', status,
                patch_sha])
        else:
            print("[Voting disabled] should put %s to review %s" % (
                status, patch_sha))

    def list_open_patchsets(self, project, gerrit_filter=''):
        """Generator that returns the last patchsets of all the reviews of
        a given project.
        """

        reviews = self.get_open_reviews(project, gerrit_filter)
        for review in reviews:
            yield self.get_last_patchset(int(review['number']))


def create_jobdefinition(dci_client, test, name, components):
    jobdefinition = dci_client.find_or_create_or_refresh(
        '/jobdefinitions',
        {
            "name": name,
            "test_id": test['id']
        },
        unicity_key=['test_id', 'name']
    )
    # NOTE(Gonéri): associate the jobdefinition with its components
    for component in components:
        dci_client.find_or_create_or_refresh(
            '/jobdefinition_components',
            {
                "component_id": component['id'],
                "jobdefinition_id": jobdefinition['id']
            },
            unicity_key=['component_id', 'jobdefinition_id']
        )
    # TODO(Gonéri): our jobdefinition is ready, we should turn it on.
    return jobdefinition


def push_patchset_as_component_in_dci(dci_client, component_name,
                                      test, patchset, git_url, componenttype):
    """Create a version in DCI-CS from a gerrit patchset."""
    title = patchset['commitMessage'].split('\n')[0]
    message = patchset['commitMessage']
    gerrit_id = patchset['id']
    url = patchset['url']
    ref = patchset['currentPatchSet']['ref']
    sha = patchset['currentPatchSet']['revision']
    print("Gerrit to DCI-CS: %s" % title)
    version_data = {
        "componenttype_id": componenttype['id'],
        "name": "[gerrit] %s - %s" % (component_name, title),
        "title": title,
        "message": message,
        "sha": sha,
        "url": url,
        # TODO(Gonéri): We use components/$name/ref now
        "git": git_url,
        "ref": ref,
        "data": {
            "gerrit_id": gerrit_id,
        },
        "canonical_project_name": component_name
    }
    component = dci_client.find_or_create_or_refresh(
        '/components', version_data, unicity_key=['sha'])
    return component


def get_patchset_score(dci_client, jobdefinition):
    """Update the review in Gerrit from the status of a version in DCI-CS."""

    jobdefinition = dci_client.get(
        '/jobdefinitions',
        projection={'jobs': 1},
        where={'id': jobdefinition['id']}).json()

    status = '0'
    for job_id in jobdefinition['_items'][0]['jobs']:
        jobs = dci_client.get(
            "/jobs",
            where={'id': job_id},
            embedded={'jobstates_collection': 1}).json()
        for job in jobs['_items']:
            last_job_status = job['jobstates'][-1]['status']
            if last_job_status == 'failure':
                status = '-1'
                break
            elif last_job_status == 'success':
                status = '1'
    return status


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
        gerrit = Gerrit(
            project['gerrit']['server'],
            project['gerrit'].get('vote', False))
        test = dci_client.find_or_create_or_refresh(
            '/tests',
            {'name': project['gerrit']['test'], 'data': {}})
        componenttype = dci_client.find_or_create_or_refresh(
            '/componenttypes',
            {"name": "gerrit_review"})

        if 'git' in project['gerrit']:
            git_url = project['gerrit']['git']
        else:
            git_url = "http://%s/%s" % (project["gerrit"]["server"],
                                        project["gerrit"]["project"])

        base_components = []
        for component in project['jobdefinition']['components']:
            componenttype = dci_client.find_or_create_or_refresh(
                '/componenttypes',
                {"name": component['componenttype']})
            del component['componenttype']
            component['componenttype_id'] = componenttype['id']
            base_components += [
                dci_client.find_or_create_or_refresh(
                    '/components', component, unicity_key=['sha'])]

        # NOTE(Gonéri): For every review of a component, we
        # - create a version that overwrite the component default origin
        # with a one that is sticked to the review
        # - check if there is some result for the Git review, and if so,
        # push vote
        for patchset in gerrit.list_open_patchsets(
                project['gerrit']['project'],
                project['gerrit'].get('filter', '')):
            components = copy.deepcopy(base_components)
            components += [
                push_patchset_as_component_in_dci(
                    dci_client,
                    project["gerrit"]["name"],
                    test, patchset, git_url, componenttype)]

            name = "Khalessi gerrit review: %s" % (patchset['id'])
            jobdefinition = create_jobdefinition(
                dci_client, test, name, components)
            print(jobdefinition)
            score = get_patchset_score(dci_client, jobdefinition)
            # TODO(Gonéri): also push a message and the URL to see the job.
            if score != '0':
                print("DCI-CS → Gerrit: %s" % score)
                gerrit.review(
                    patchset['currentPatchSet']['revision'], score)

if __name__ == '__main__':
    main()
