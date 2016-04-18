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

from dciclient.v1.api import file
from dciclient.v1.api import context
from dci.elasticsearch import engine as es_engine
from dci import dci_config
import json

dci_context = context.build_dci_context()
conf = dci_config.generate_conf()

es_engine = es_engine.DCIESEngine(conf)
files = json.loads(file.list(dci_context).text)
es_files = es_engine.list()

if es_files == None:
    print "no index found"
else:
    es_files = es_files['hits']['hits']

for file in files['files']:
    es_engine.index(file)
