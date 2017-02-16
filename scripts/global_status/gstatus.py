#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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

from dciclient.v1.api import context as dci_context
from dciclient.v1.api import topic
from dciclient.v1.api import team
from dciclient.v1.api import remoteci
from dciclient.v1.api import job
from dciclient.v1.api import base

import os
import sys

dci_cs_url = os.environ.get('DCI_CS_URL', '')
dci_login = os.environ.get('DCI_LOGIN', '')
dci_password = os.environ.get('DCI_PASSWORD', '')

if not dci_cs_url or not dci_login or not dci_password:
    print("Missing environment variables DCI_CS_URL=%s, DCI_LOGIN=%s, DCI_PASSWORD=%s" %
          (dci_cs_url, dci_login, dci_password))
    sys.exit(1)

gcontext = dci_context.build_dci_context(
    dci_cs_url=dci_cs_url,
    dci_login=dci_login,
    dci_password=dci_password)


# to get the last job of a remoteci, we loop over all job sorted by date
# and get the first status to have the last status of a remoteci.
ljobs = [r for r in base.iter(gcontext, 'jobs', sort='-created_at', embed='components,jobdefinition')]

#ljobs = job.list(gcontext, sort='-created_at', embed='components,jobdefinition', limit=1024).json()['jobs']

# get all topics in order to get the association topic_id -> topic_name
# which will be used below
ltopics = topic.list(gcontext).json()['topics']
topicids_to_name = {}
for current_topic in ltopics:
    topicids_to_name[current_topic['id']] = current_topic['name']

# get all remotecis in order to get the association remoteci_id -> remoteci_name
# which will be used below
lremotecis = remoteci.list(gcontext).json()['remotecis']
remotecis_to_name = {}
for current_remoteci in lremotecis:
    remotecis_to_name[current_remoteci['id']] = current_remoteci['name']

results = {}

for current_job in ljobs:
    topic_id = current_job['jobdefinition']['topic_id']
    if not results.has_key(topic_id):
        results[topic_id] = {}

    remoteci_id = current_job['remoteci_id']
    if not results[topic_id].has_key(remoteci_id):
        results[topic_id][remoteci_id] = {}

    puddle_name = current_job['components'][0]['name']
    if not results[topic_id][remoteci_id].has_key(puddle_name):
        if current_job['status'] in ('success', 'failure'):
            results[topic_id][remoteci_id][puddle_name] = current_job['status']


# get all puddles and all remotecis in a sorted way in order to build the html page table

# this dict contains an association between the topics and the puddles/remotecis
# ie.  {'topic_1' : {'remotecis': ['r1', 'r2'], 'puddles': ['p1', 'p2']}}
# the remotecis and puddles list are sorted.

topics_to_puddles_remotecis = {}

all_puddles = set()
all_remotecis = set()

for current_topic in results:
    topics_to_puddles_remotecis[current_topic] = {}
    topics_to_puddles_remotecis[current_topic]['remotecis'] = set()
    topics_to_puddles_remotecis[current_topic]['puddles'] = set()

    current_result = results[current_topic]
    topics_to_puddles_remotecis[current_topic]['remotecis'].update(current_result.keys())
    for rci in current_result:
        topics_to_puddles_remotecis[current_topic]['puddles'].update(current_result[rci].keys())

    topics_to_puddles_remotecis[current_topic]['remotecis'] = list(topics_to_puddles_remotecis[current_topic]['remotecis'])
    topics_to_puddles_remotecis[current_topic]['remotecis'].sort()
    topics_to_puddles_remotecis[current_topic]['puddles'] = list(topics_to_puddles_remotecis[current_topic]['puddles'])
    topics_to_puddles_remotecis[current_topic]['puddles'].sort()


for current_topic in results:
    current_result  = results[current_topic]

    with open('./%s.html' % topicids_to_name[current_topic], "w") as fresult:
        fresult.write("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <title>Distributed CI</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>
    </head>

    <body>
    <h1>DCI global status</h1>
    """)
        fresult.write("""
        <table class="table table-condensed">
          <tr>
            <th>puddle-remoteci</th>
        """)

        for rci in topics_to_puddles_remotecis[current_topic]['remotecis']:
            fresult.write("<th>%s</th>\n" % remotecis_to_name[rci])
        fresult.write("</tr>")

        for puddle in topics_to_puddles_remotecis[current_topic]['puddles']:
            fresult.write("<tr>\n")
            fresult.write("<td>%s</td>\n" % puddle)
            for rci in topics_to_puddles_remotecis[current_topic]['remotecis']:
                if (results[current_topic][rci].has_key(puddle) and
                   results[current_topic][rci][puddle] in ('success', 'failure')):
                    if results[current_topic][rci][puddle] == 'success':
                        fresult.write("<td class='success'>%s</td>" % results[current_topic][rci][puddle])
                    else:
                        fresult.write("<td class='danger'>%s</td>" % results[current_topic][rci][puddle])
                else:
                    fresult.write("<td class='active'>NA</td>")
            fresult.write("</tr>\n")

        fresult.write(
            """
            </table>
            </body>
            </html>
            """
        )

print("done\n")