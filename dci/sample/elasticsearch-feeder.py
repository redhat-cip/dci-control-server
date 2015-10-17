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

import dci.client
import json
from pprint import pprint

import requests


def upload(es_s, item_type, items):
    for item in items:
        pprint(item)
        item_es_url = es_url + 'dci/' + item_type + '/' + item['id']
        print(item_es_url)
        es_r = es_s.head(item_es_url)
        print(es_r.status_code)
        if es_r.status_code == 404:
            es_r = es_s.put(item_es_url, data=json.dumps(item))
            print(es_r.status_code)
            print(es_r.text)


es_url = "http://elasticsearch-dcics.rhcloud.com/"
dci_client = dci.client.DCIClient()


es_s = requests.Session()
es_s.headers.setdefault('Content-Type', 'application/json')

jobs = dci_client.list_items(
    '/jobs',
    where={'created_at': '>= "yesterday"'},
    embedded={
        'jobstates': 1,
        'jobdefinition': 1,
        'jobdefinition.text': 1})

files = dci_client.list_items(
    '/files',
    where={'created_at': '>= "yesterday"'},
    embedded={
        'remoteci': 1,
        'jobstates': 1})
upload(es_s, 'jobs', jobs)
upload(es_s, 'files', files)
