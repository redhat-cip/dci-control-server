#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import six


def sha_walker(sha_to_walks, dci_client, repository, test):
    componenttype = dci_client.find_or_create_or_refresh(
        '/componenttypes',
        {"name": "git_repository"})

    sha = sha_to_walks.pop()
    if not sha:
        return
    commit = gh_s.get(
        'https://api.github.com/'
        'repos/%s/git/commits/%s' % (repository, sha)).json()
    if 'parents' in commit:
        for parent in commit['parents']:
            sha_to_walks.append(parent['sha'])
    message = commit['message']
    title = message.split('\n')[0]

    # NOTE(Gonéri): Is the commit already here?
    print(title)
    component = dci_client.find_or_create_or_refresh(
        '/components',
        {
            "componenttype_id": componenttype['id'],
            "name": title,
            "title": title,
            "message": message,
            "sha": sha,
            "git": 'https://github.com/%s' % repository,
            "url": 'https://github.com/%s/commit/%s' % (repository, sha),
            "data": {
                "sha": sha,
            },
            "canonical_project_name": repository.split('/')[1]
        },
        unicity_key=['sha']
    )
    jobdefinition = dci_client.find_or_create_or_refresh(
        '/jobdefinitions',
        {
            "name": "tox: %s (%s)" % (title, sha),
            "test_id": test['id']
        },
        unicity_key=['test_id', 'name']
    )
    dci_client.find_or_create_or_refresh(
        '/jobdefinition_components',
        {
            "component_id": component['id'],
            "jobdefinition_id": jobdefinition['id']
        },
        unicity_key=['component_id', 'jobdefinition_id']
    )


def fetch(gh_s, dci_client, name, repositories):
    test = dci_client.find_or_create_or_refresh(
        '/tests',
        {"name": "tox"})

    for repository in repositories:
        r = gh_s.get(
            'https://api.github.com/repos/' +
            repository +
            '/branches')
        if r.status_code == 404:
            print("Repository not found: %s" % repository)
            continue
        branches = {a['name']: a['commit'] for a in r.json()}
        sha_to_walks = [branches['master']['sha']]
        while sha_to_walks:
            sha_walker(sha_to_walks, dci_client,
                       repository, test)

products = {
    'dci-control-server': [
        'redhat-cip/dci-control-server']}
gh_s = requests.Session()
# gh_s.auth = ('user', 'xxx')
dci_client = client.DCIClient()

for name, repositories in six.iteritems(products):
    fetch(gh_s, dci_client, name, repositories)
