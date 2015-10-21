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

import json
import os
import re
import subprocess

import requests

from dci import client


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
            "test_id": test['id'],
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


def register_github_commit(gh_s, dci_client, componenttype, canonical_project_name, github_account, branch_name):
    branch = gh_s.get(
        'https://api.github.com/repos/' + github_account + '/' + canonical_project_name + '/branches/' + branch_name).json()
    commit = branch['commit']
    sha = commit['sha']
    url = commit['html_url']
    title = commit['commit']['message'].split('\n')[0]
    message = commit['commit']['message']
    git_url = 'https://github.com/' + github_account + '/' + canonical_project_name

    version_data = {
        "componenttype_id": componenttype['id'],
        "name": "[%s][%s] %s" % (canonical_project_name, branch_name, title),
        "title": title,
        "message": message,
        "sha": sha,
        "url": url,
        # TODO(Gonéri): We use components/$name/ref now
        "git": git_url,
        "data": {},
        "canonical_project_name": canonical_project_name
    }
    component = dci_client.find_or_create_or_refresh(
        '/components', version_data, unicity_key=['sha'])
    return component


def register_delorean_snapshot(dci_client, componenttype, url, canonical_project_name):
    r = requests.get(url)
    m = re.search(r'name=(.+-([^-]*))$', r.text,  re.MULTILINE)
    name = m.group(1)
    version = m.group(1)
    component = dci_client.find_or_create_or_refresh(
        '/components', {
            'name': name,
            'canonical_project_name': canonical_project_name,
            'componenttype_id': componenttype['id'],
            'data': {
                'ksgen_args': {
                    'extra-vars': {
                        'product.repo.poodle_pin_version:': version,
                    }}}}, unicity_key=['name'])
    return component


def get_gerrit_review_as_component(
        dci_client,
        componenttype,
        canonical_project_name,
        git_url,
        gerrit_server,
        gerrit_project,
        gerrit_filter=''):
    gerrit = Gerrit(gerrit_server)
    for patchset in gerrit.list_open_patchsets(gerrit_project, gerrit_filter):
        title = patchset['commitMessage'].split('\n')[0]
        message = patchset['commitMessage']
        gerrit_id = patchset['id']
        url = patchset['url']
        ref = patchset['currentPatchSet']['ref']
        sha = patchset['currentPatchSet']['revision']
        print("Gerrit to DCI-CS: %s" % title)
        version_data = {
            "componenttype_id": componenttype['id'],
            "name": "[gerrit] %s - %s" % (canonical_project_name, title),
            "title": title,
            "message": message,
            "sha": sha,
            "url": url,
            "git": git_url,
            "ref": ref,
            "data": {
                "gerrit_id": gerrit_id,
            },
            "canonical_project_name": canonical_project_name
        }
        component = dci_client.find_or_create_or_refresh(
            '/components', version_data, unicity_key=['sha'])
        yield component

##############################################
##############################################
##############################################

def main():
    dci_client = client.DCIClient()
    componenttypes = {
        'git_commit': dci_client.find_or_create_or_refresh(
            '/componenttypes',
            {"name": 'git_commit'}),
        'repo': dci_client.find_or_create_or_refresh(
            '/componenttypes',
            {"name": 'poodle'})}
    test = dci_client.find_or_create_or_refresh(
        '/tests',
# TODO(Gonéri): tests.name is also used by the agent to identify the kind of job they can
# process. We must fix that.
        {'name': 'khaleesi-tempest',
         'data': {
          'ksgen_args': {
              'provisioner': 'manual',
              'product': 'rdo',
              'product-version': 'liberty',
              'product-version-build': 'latest',
              'product-version-repo': 'delorean_mgt',
              'distro':  'centos-7.0',
              'installer': 'rdo_manager',
              'installer-deploy': 'templates',
              'installer-env': 'virthost',
              'installer-images': 'build',
              'installer-network': 'neutron',
              'installer-network-isolation': 'single_nic_vlans',
              'installer-network-variant': 'ml2-vxlan',
              'installer-post_action': 'none',
              'installer-topology': 'minimal',
              'installer-tempest': 'minimal',
              'workarounds': 'enabled',
              'extra-vars': {
                  'provisioner.type': 'manual',
                  'installer.nodes.node_cpu': 24}}}})

    gh_s = requests.Session()
    gh_s.auth = ('xxx', 'xxxx')

    base_components = [
        register_github_commit(
            gh_s,
            dci_client,
            componenttypes['git_commit'],
            canonical_project_name='khaleesi-settings',
            github_account='redhat-openstack',
            branch_name='master'),
        register_delorean_snapshot(
            dci_client,
            componenttypes['repo'],
            canonical_project_name='RDO_Mgnt_Development',
            url='http://trunk-mgt.rdoproject.org/centos-kilo/current/delorean-rdo-management.repo')]

    # Push the current Khaleesi master
    khaleesi_master = register_github_commit(
        gh_s,
        dci_client,
        componenttypes['git_commit'],
        canonical_project_name='khaleesi',
        github_account='redhat-openstack',
        branch_name='master')
    create_jobdefinition(
        dci_client, test, None, base_components + [khaleesi_master])

    # Push the last Gerrit review
    for component in get_gerrit_review_as_component(
            dci_client,
            componenttypes['git_commit'],
            canonical_project_name='khaleesi',
            git_url='https://review.gerrithub.io/redhat-openstack/khaleesi',
            gerrit_server='review.gerrithub.io',
            gerrit_project='redhat-openstack/khaleesi',
            gerrit_filter='project:redhat-openstack/khaleesi status:open is:open is:mergeable NOT label:Verified<=-1 NOT label:Code-Review<=-1 NOT age:1d'):
        create_jobdefinition(
            dci_client, test, None, base_components + [component])


if __name__ == '__main__':
    main()
