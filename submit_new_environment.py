#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
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


import os
import random
import shutil
import sys

import json
import requests

dci_cs = os.environ['DCI_SERVER']
jenkins_build_id = random.randrange(99999999)
name = "sps-R7.0-I.1.3.0-3nodes (%s)" % jenkins_build_id
local_base_dir = "/srv/html/environments/%s" % jenkins_build_id
public_base_url = "http://94.143.114.133/environments/%s" % jenkins_build_id
os.makedirs(local_base_dir, mode=0o755, exist_ok=True)

for local_file_path in sys.argv[1:]:
    file_name = os.path.basename(local_file_path)
    shutil.copyfile(local_file_path, local_base_dir + '/' + file_name)
    public_file_url = public_base_url + '/' + file_name

payload = [{'name': name, "url": public_base_url}]
requests.post(
    'http://%s/environments' % dci_cs,
    data=json.dumps(payload),
    headers={'Content-Type': 'application/json'})


r = requests.get('http://%s/environments' % dci_cs)


for item in r.json()['_items']:
    print("name: %s (%s)" % (item['name'], item['url']))
