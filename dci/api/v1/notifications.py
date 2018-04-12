# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Red Hat, Inc
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

import flask
from dci.db import models
from sqlalchemy import sql


def email(job):

    if job['status'] != 'failure':
        return None

    components_names = [c['name'] for c in job['components']]

    _TABLE_URCIS = models.JOIN_USER_REMOTECIS

    query = (sql.select([models.USERS.c.email]).
             select_from(models.USERS.join(_TABLE_URCIS)).
             where(_TABLE_URCIS.c.remoteci_id == job['remoteci_id']))
    result = flask.g.db_conn.execute(query).fetchall()

    emails = [k['email'] for k in result]
    if emails:
        msg = {
            'event': 'notification',
            'emails': emails,
            'job_id': str(job['id']),
            'status': job['status'],
            'topic_id': str(job['topic_id']),
            'topic_name': job['topic']['name'],
            'remoteci_id': str(job['remoteci_id']),
            'remoteci_name': job['remoteci']['name'],
            'components': components_names
        }
        return msg

    return None


def dlrn(job):

    for component in job['components']:
        data = component['data']
        if 'dlrn' in data and data['dlrn']:
            if data['dlrn']['commit_hash'] and \
               data['dlrn']['distro_hash'] and \
               data['dlrn']['commit_branch']:
                msg = {
                    'event': 'dlrn_publish',
                    'status': job['status'],
                    'job_id': str(job['id']),
                    'topic_name': job['topic']['name'],
                    'dlrn': component['data']['dlrn']
                }
                return msg

    return None


def dispatcher(job):

    events = []

    email_event = email(job)
    if email_event:
        events.append(email_event)

    dlrn_event = dlrn(job)
    if dlrn_event:
        events.append(dlrn_event)

    if events:
        flask.g.sender.send_json(events)
