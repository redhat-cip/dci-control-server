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


def format_mail_message(mesg):
    # compute test name:regressions number
    regressions = ', '.join(['%s: %s' % (k, v)
                             for (k, v) in mesg['regressions'].items()])
    if regressions:
        regressions = 'The regressions found are: %s' % regressions

    return """
You are receiving this email because of the DCI job {job_id} for the
topic {topic} on the Remote CI {remoteci}.

The final status of the job is: {status}

The components used are: {components}
{regressions}

For more information:
https://www.distributed-ci.io/jobs/{job_id}
""".format(
        job_id=mesg['job_id'],
        topic=mesg['topic_name'],
        remoteci=mesg['remoteci_name'],
        status=mesg['status'],
        components=', '.join(mesg['components']),
        regressions=regressions)


def build_job_finished_event(job):
    components = [
        {"id": str(c["id"]), "name": c["name"], "type": c["type"], "url": c["url"]}
        for c in job["components"]
    ]
    results = [{"name": r["name"]} for r in job["results"]]
    return {
        "event": "job_finished",
        "type": "job_finished",
        "job": {
            "id": str(job["id"]),
            "status": job["status"],
            "components": components,
            "results": results,
        }
    }


def get_email_info(job, emails):

    components_names = [c['name'] for c in job['components']]
    regressions = {res['name']: res['regressions']
                   for res in job['results']}

    return {
        'event': 'notification',
        'emails': emails,
        'job_id': str(job['id']),
        'status': job['status'],
        'topic_id': str(job['topic_id']),
        'topic_name': job['topic']['name'],
        'remoteci_id': str(job['remoteci_id']),
        'remoteci_name': job['remoteci']['name'],
        'components': components_names,
        'regressions': regressions
    }


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
                    'dlrn': data['dlrn']
                }
                return msg

    return None


def get_emails(remoteci_id):
    _USER_REMOTECIS = models.JOIN_USER_REMOTECIS

    query = (sql.select([models.USERS.c.email]).
             select_from(models.USERS.
                         join(_USER_REMOTECIS).
                         join(models.REMOTECIS)).
             where(_USER_REMOTECIS.c.remoteci_id == remoteci_id).
             where(_USER_REMOTECIS.c.remoteci_id == models.REMOTECIS.c.id).
             where(models.REMOTECIS.c.state != 'archived'))

    emails = flask.g.db_conn.execute(query).fetchall()

    return [email['email'] for email in emails]


def dispatcher(job):
    events = []
    emails = get_emails(job['remoteci_id'])
    if emails:
        email_event = get_email_info(job, emails)
        if email_event:
            events.append(email_event)

    dlrn_event = dlrn(job)
    if dlrn_event:
        events.append(dlrn_event)

    job_finished = build_job_finished_event(job)
    if job_finished:
        events.append(job_finished)

    if events:
        flask.g.sender.send_json(events)
