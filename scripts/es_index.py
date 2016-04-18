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

from dci import dci_config
from dci.elasticsearch import engine as es_engine
from dciclient.v1.api import context
from dciclient.v1.api import file
import json

dci_context = context.build_dci_context()
conf = dci_config.generate_conf()

es_engine = es_engine.DCIESEngine(conf)
db_files = json.loads(file.list(dci_context).text)
es_files = es_engine.list()

if es_files is None:
    print("no index found")
else:
    es_files = es_files['hits']['hits']

print("- Documents In DB")
print(len(db_files['files']))
print("- Documents In ES")
print(len(es_files))

# Preare the to delete list
to_del = []
for es_file in es_files:
    flag = True
    for db_file in db_files['files']:
        if es_file['_id'] == db_file['id']:
            flag = False
            break
    if flag:
        to_del.append(es_file)

# Prepare the to add list
to_add = []
for db_file in db_files['files']:
    flag = True
    for es_file in es_files:
        if es_file['_id'] == db_file['id']:
            flag = False
            break
    if flag:
        to_add.append(db_file)

print("- To Add")
print(len(to_add))
print("- To Delete")
print(len(to_del))

for add in to_add:
    es_engine.index(add)

for delete in to_del:
    es_engine.delete(delete['_id'])
