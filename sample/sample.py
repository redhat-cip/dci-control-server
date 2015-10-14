#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
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

import random
import uuid


client = client.DCIClient(end_point="http://127.0.0.1:5000",
                          login="admin", password="admin")

componenttype_id = client.post('/api/componenttypes',
                               data={'name': 'kikoolol'}).json()["id"]

team_id = client.post('/api/teams', data={'name': 'team'}).json()["id"]

for _ in range(10):
    component = client.post('/api/components',
                            data={'name': str(uuid.uuid4())[:18],
                                  'data': {'lol': 'looool'},
                                  'componenttype_id': componenttype_id,
                                  'canonical_project_name': 'mdr'})
    component_id = component.json()["id"]

    for _ in range(5):

        test = client.post('/api/tests',
                           data={'name': 'bob',
                                 'data': {
                                     'test_keys': {
                                         'foo': ['bar1', 'bar2']}}})
        test_id = test.json()["id"]

        jobdefinition = client.post('/api/jobdefinitions',
                                    data={'name': str(uuid.uuid4())[:18],
                                          'test_id': test_id})
        jobdefinition_id = jobdefinition.json()["id"]

        client.post('/api/jobdefinition_components', data={
            'component_id': component_id,
            'jobdefinition_id': jobdefinition_id
        })

        remoteci = client.post('/api/remotecis',
                               data={
                                   'name': str(uuid.uuid4())[:18],
                                   'test_id': test_id,
                                   'team_id': team_id,
                                   'data': {
                                       'remoteci_keys': {
                                           'foo': ['bar1', 'bar2']}}})
        remoteci_id = remoteci.json()["id"]

        job = client.post('/api/jobs',
                          data={'remoteci_id': remoteci_id,
                                'team_id': team_id,
                                'jobdefinition_id': jobdefinition_id})
        job_id = job.json()["id"]

        alea = random.randint(0, 2)
        status = ["ongoing", "failure", "success"][alea]
        jobstate = client.post('/api/jobstates',
                               data={'job_id': job_id,
                                     'team_id': team_id,
                                     'status': status})
        jobstate_id = jobstate.json()["id"]

        for _ in range(2):
            client.post('/api/files',
                        data={'jobstate_id': jobstate_id,
                              'content': 'kikoolol! mdr! lol!' * 100,
                              'name': str(uuid.uuid4())[:18],
                              'mime': 'text',
                              'team_id': team_id})

print("Database populated successfully :)\n")
