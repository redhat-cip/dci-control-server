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


from dci.api import v1 as api_v1
from dci.common import exceptions
from dci.common import utils
from dci.elasticsearch import engine as es_engine
from dci.influxdb import engine as influxdb_engine

import flask
import logging

from sqlalchemy import exc as sa_exc

from dci import dci_config


class DciControlServer(flask.Flask):

    def __init__(self, conf):
        super(DciControlServer, self).__init__(__name__)
        self.config.update(conf)
        self.url_map.strict_slashes = False
        self.engine = dci_config.get_engine(conf)
        self.es_engine = es_engine.DCIESEngine(conf)

    def make_default_options_response(self):
        resp = super(DciControlServer, self).make_default_options_response()
        methods = ['GET', 'POST', 'PUT', 'DELETE']
        headers = resp.headers

        headers.add_header('Access-Control-Allow-Methods', ', '.join(methods))
        headers.add_header('Access-Control-Allow-Headers',
                           self.config['X_HEADERS'])
        return resp

    def process_response(self, resp):
        headers = resp.headers
        headers.add_header('Access-Control-Expose-Headers',
                           self.config['X_HEADERS'])
        headers.add_header('Access-Control-Allow-Origin',
                           self.config['X_DOMAINS'])

        return super(DciControlServer, self).process_response(resp)


def handle_api_exception(api_exception):
    response = flask.jsonify(api_exception.to_dict())
    response.status_code = api_exception.status_code
    return response


def handle_dbapi_exception(dbapi_exception):
    dci_exception = exceptions.DCIException(str(dbapi_exception)).to_dict()
    response = flask.jsonify(dci_exception)
    response.status_code = 400
    return response


def create_app(conf):
    dci_config.TEAM_ADMIN_ID = dci_config.get_team_admin_id()

    dci_app = DciControlServer(conf)

    # Logging support
    loggers = [dci_app.logger, logging.getLogger('sqlalchemy'),
               logging.getLogger('werkzeug')]
    for logger in loggers:
        format = (conf['DEBUG_LOG_FORMAT'] if conf['DEBUG']
                  else conf['PROD_LOG_FORMAT'])

        handler = (logging.StreamHandler() if conf['DEBUG']
                   else logging.FileHandler(conf['LOG_FILE']))
        handler.setFormatter(logging.Formatter(format))

        logger.setLevel(logging.DEBUG if conf['DEBUG'] else logging.WARN)
        logger.addHandler(handler)

    @dci_app.before_request
    def before_request():
        flask.g.db_conn = dci_app.engine.connect()
        flask.g.es_conn = dci_app.es_engine
        flask.g.influxdb_conn = dci_app.influxdb_engine

    @dci_app.teardown_request
    def teardown_request(_):
        flask.g.db_conn.close()

    # Registering REST error handler
    dci_app.register_error_handler(exceptions.DCIException,
                                   handle_api_exception)
    dci_app.register_error_handler(sa_exc.DBAPIError,
                                   handle_dbapi_exception)

    # Registering REST API v1
    dci_app.register_blueprint(api_v1.api, url_prefix='/api/v1')

    # Registering custom encoder
    dci_app.json_encoder = utils.JSONEncoder

    return dci_app
