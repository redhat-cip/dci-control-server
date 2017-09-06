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

from dciclient.v1.api import base
from dciclient.v1.api import context as dci_context
from dciclient.v1.api import remoteci
from dciclient.v1.api import team
from dciclient.v1.api import topic

import json
import os
import sys

dci_cs_url = os.environ.get('DCI_CS_URL', '')
dci_login = os.environ.get('DCI_LOGIN', '')
dci_password = os.environ.get('DCI_PASSWORD', '')

if not dci_cs_url or not dci_login or not dci_password:
    print("Missing environment variables DCI_CS_URL=%s, DCI_LOGIN=%s,"
          "DCI_PASSWORD=%s" % (dci_cs_url, dci_login, dci_password))
    sys.exit(1)

gfilter = {"black_teams": [], "white_topics": []}

if len(sys.argv) > 1:
    filter_file_path = sys.argv[1]
    if not os.path.exists(filter_file_path):
        print("File %s does not exists." % filter_file_path)
        sys.exit(1)
    # get the filtering rules
    gfilter = json.loads(open('./%s' % filter_file_path).read())

gcontext = dci_context.build_dci_context(
    dci_cs_url=dci_cs_url,
    dci_login=dci_login,
    dci_password=dci_password)


# to get the last job of a remoteci, we loop over all job sorted by date
# and get the first status to have the last status of a remoteci.
print("[*] Get all jobs")
ljobs = [r for r in base.iter(gcontext, 'jobs', sort='-created_at',
                              embed='components', limit=128)]

# get all topics to get the association topic_id -> topic_name
# which will be used below
print("[*] Get all topics")
ltopics = topic.list(gcontext).json()['topics']
topicids_to_name = {}
for current_topic in ltopics:
    topicids_to_name[current_topic['id']] = current_topic['name']

# get all teams to get association team_id -> team_name
print("[*] Get all teams")
lteams = team.list(gcontext).json()['teams']
teams_to_name = {}
for current_team in lteams:
    teams_to_name[current_team['id']] = current_team['name']

# get all remotecis to get the association remoteci_id -> remoteci_name
# which will be used below
print("[*] Get all remotecis")
lremotecis = remoteci.list(gcontext).json()['remotecis']
remotecis_to_name = {}
for current_remoteci in lremotecis:
    remoteci_team_id = current_remoteci['team_id']
    remoteci_team_name = teams_to_name[remoteci_team_id]
    remotecis_to_name[current_remoteci['id']] = (current_remoteci['name'],
                                                 remoteci_team_name)


results = {}

for current_job in ljobs:
    topic_id = current_job['topic_id']
    if topic_id not in results:
        results[topic_id] = {}

    remoteci_id = current_job['remoteci_id']
    if remoteci_id not in results[topic_id]:
        results[topic_id][remoteci_id] = {}

    # for osp8 and osp9 drop the director puddle
    puddle_name = current_job['components'][0]['name']
    if 'director' in current_job['components'][0]['name']:
        puddle_name = current_job['components'][1]['name']

    if puddle_name not in results[topic_id][remoteci_id]:
        if current_job['status'] in ('success', 'failure'):
            results[topic_id][remoteci_id][puddle_name] = current_job['status']

# get all puddles and all remotecis in a sorted way in order to build the html
# page table

# this dict contains an association between the topics and puddles/remotecis
# ie.  {'topic_1' : {'remotecis': ['r1', 'r2'], 'puddles': ['p1', 'p2']}}
# the remotecis and puddles list are sorted.

topics_to_puddles_remotecis = {}

for current_topic in results:
    topics_to_puddles_remotecis[current_topic] = {}
    topics_to_puddles_remotecis[current_topic]['remotecis'] = set()
    topics_to_puddles_remotecis[current_topic]['puddles'] = set()

    current_result = results[current_topic]
    topics_to_puddles_remotecis[current_topic]['remotecis'].\
        update(current_result.keys())
    for rci in current_result:
        topics_to_puddles_remotecis[current_topic]['puddles'].\
            update(current_result[rci].keys())

    topics_to_puddles_remotecis[current_topic]['remotecis'] = \
        list(topics_to_puddles_remotecis[current_topic]['remotecis'])
    topics_to_puddles_remotecis[current_topic]['remotecis'].sort()
    topics_to_puddles_remotecis[current_topic]['puddles'] = \
        list(topics_to_puddles_remotecis[current_topic]['puddles'])
    topics_to_puddles_remotecis[current_topic]['puddles'].sort(reverse=True)


def is_rci_in_gstatus(rci, is_white_topic):
    if (is_white_topic or remotecis_to_name[rci][1] not in gfilter['black_teams']):  # noqa
        return True
    return False


print("[*] Generate static html pages")
for current_topic in results:
    current_result = results[current_topic]

    bootstrapjs = "https://maxcdn.bootstrapcdn.com/bootstrap/"\
                  "3.3.7/js/bootstrap.min.js"
    bootstrapcss = "https://maxcdn.bootstrapcdn.com/"\
                   "bootstrap/3.3.7/css/bootstrap.min.css"
    jquery = "https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"

    is_white_topic = topicids_to_name[current_topic] in gfilter['white_topics']

    with open('./%s.html' % topicids_to_name[current_topic], "w") as fresult:
        fresult.write("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <title>Distributed CI</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="%s">
    <script src="%s"></script>
    <script src="%s"></script>
    </head>

    <body>
    <h1>DCI global status</h1>
    """ % (bootstrapcss, bootstrapjs, jquery))
        fresult.write("""
        <div class="container-fluid">
        <table class="table table-condensed">
          <tr>
            <th>puddle-remoteci</th>
        """)

        for rci in topics_to_puddles_remotecis[current_topic]['remotecis']:
            if is_rci_in_gstatus(rci, is_white_topic):
                fresult.write("<th>%s/%s</th>\n" % (remotecis_to_name[rci][0],
                                                    remotecis_to_name[rci][1]))
        fresult.write("</tr>")

        for puddle in topics_to_puddles_remotecis[current_topic]['puddles']:
            fresult.write("<tr>\n")
            fresult.write("<td>%s</td>\n" % puddle)
            for rci in topics_to_puddles_remotecis[current_topic]['remotecis']:
                if is_rci_in_gstatus(rci, is_white_topic):
                    if (puddle in results[current_topic][rci] and
                       results[current_topic][rci][puddle] in ('success', 'failure')):  # noqa
                        if results[current_topic][rci][puddle] == 'success':
                            fresult.write("<td class='success'>%s</td>" %
                                          results[current_topic][rci][puddle])
                        else:
                            fresult.write("<td class='danger'>%s</td>" %
                                          results[current_topic][rci][puddle])
                    else:
                        fresult.write("<td class='active'>NA</td>")
            fresult.write("</tr>\n")

        fresult.write(
            """
            </table>
            </div>
            </body>
            </html>
            """
        )

print("[*] done\n")
