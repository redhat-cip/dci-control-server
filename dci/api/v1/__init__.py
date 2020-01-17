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
from flask import json

import logging

logger = logging.getLogger(__name__)

api = flask.Blueprint('api_v1', __name__)


@api.route('/', strict_slashes=False)
def index():
    logger.info('control server is ok...')
    return flask.Response(json.dumps({'_status': 'OK',
                                      'message': 'Distributed CI.'}),
                          status=200,
                          content_type='application/json')


import dci.api.v1.analytics  # noqa
import dci.api.v1.audits  # noqa
import dci.api.v1.base  # noqa
import dci.api.v1.certs  # noqa
import dci.api.v1.components  # noqa
import dci.api.v1.feeders  # noqa
import dci.api.v1.files  # noqa
import dci.api.v1.identity  # noqa
import dci.api.v1.jobs  # noqa
import dci.api.v1.jobstates  # noqa
import dci.api.v1.jobs_events  # noqa
import dci.api.v1.global_status  # noqa
import dci.api.v1.performance  # noqa
import dci.api.v1.products  # noqa
import dci.api.v1.remotecis  # noqa
import dci.api.v1.tags  # noqa
import dci.api.v1.teams  # noqa
import dci.api.v1.teams_users  # noqa
import dci.api.v1.tests  # noqa
import dci.api.v1.topics  # noqa
import dci.api.v1.trends  # noqa
import dci.api.v1.users  # noqa
