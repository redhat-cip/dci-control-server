# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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
import os.path
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import permissions
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.db import models


def splitpath(path):
    path = os.path.normpath(path)
    paths = path.split('/')
    return [p for p in paths if p]


@api.route('/certs/verify', methods=['GET'])
@decorators.login_required
def verify_repo_access(user):
    headers = flask.request.headers
    verify = headers.get('SSLVerify')
    fp = headers.get('SSLFingerprint')
    url = headers.get('X-Original-URI')

    if verify != "SUCCESS":
        return flask.Response('wrong SSLVerify header: %s' % verify, 403)

    if len(splitpath(url)) < 3:
        return flask.Response('requested url is invalid: %s' % url, 403)

    product_id, topic_id, component_id = splitpath(url)[:3]

    REMOTECIS = models.REMOTECIS
    query = (sql.select([REMOTECIS]).where(REMOTECIS.c.cert_fp == fp))
    remoteci = flask.g.db_conn.execute(query)

    if remoteci.rowcount != 1:
        return flask.Response('remoteci fingerprint not found: %s' % fp, 403)  # noqa

    product = v1_utils.verify_existence_and_get(product_id, models.PRODUCTS)
    if product['state'] != 'active':
        return flask.Response('product %s/%s is not active' % (product['name'], product['id']), 403)  # noqa
    topic = v1_utils.verify_existence_and_get(topic_id, models.TOPICS)
    if topic['state'] != 'active':
        return flask.Response('topic %s/%s is not active' % (topic['name'], topic['id']), 403)  # noqa
    component = v1_utils.verify_existence_and_get(component_id, models.COMPONENTS)  # noqa
    if component['state'] != 'active':
        return flask.Response('component %s/%s is not active' % (component['name'], component['id']), 403)  # noqa

    team_id = remoteci.fetchone()['team_id']
    team = v1_utils.verify_existence_and_get(team_id, models.TEAMS)
    if team['state'] != 'active':
        return flask.Response('team %s/%s is not active' % (team['name'], team['id']), 403)  # noqa

    if not permissions.is_team_associated_to_product(team_id, product_id):
        return flask.Response('team %s is not associated to the product %s' % (team['name'], product['name']), 403)  # noqa

    if topic['export_control'] is True:
        return flask.Response(None, 200)

    if not permissions.is_team_associated_to_topic(team_id, topic_id):
        return flask.Response('team %s is not associated to the topic %s' % (team['name'], topic['name']), 403)  # noqa

    return flask.Response(None, 200)
