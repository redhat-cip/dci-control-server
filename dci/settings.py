# -*- encoding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Global parameters about the API itself
#
HOST = '127.0.0.1'
PORT = 5000
DEBUG = True

# ElasticSearch Connection parameters
#
ES_HOST = '127.0.0.1'
ES_PORT = '9200'

# InfluxDB Connection parameters
#
INFLUXDB_HOST = '127.0.0.1'
INFLUXDB_PORT = '8086'
INFLUXDB_USER = 'root'
INFLUXDB_PASS = 'root'

# Database (SQLAlchemy) related parameters
#
SQLALCHEMY_DATABASE_URI = 'postgresql://dci:dci@127.0.0.1:5432/dci'

# The following two lines will output the SQL statements
# executed by SQLAlchemy. Useful while debugging and in
# development. Turned off by default
# --------
SQLALCHEMY_ECHO = False
SQLALCHEMY_RECORD_QUERIES = False

SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 0
SQLALCHEMY_NATIVE_UNICODE = True


# Logging related parameters
PROD_LOG_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
DEBUG_LOG_FORMAT = (
    '-' * 80 + '\n' +
    '%(levelname)s at %(asctime)s in %(name)s:\n' +
    '%(message)s\n' +
    '-' * 80
)

LOG_FILE = '/tmp/dci.log'

# TSDB backend to use for storing metrics.
#
# Available backends are: influxdb
# Set to None or comment if you do not wish to store metrics
#
# TSDB_DRIVER = influxdb

# Metrics dasbhoard backend to use for exploring metrics.
#
# Available backends are: grafana
# Set to None or comment if you do not wish to store metrics
#
# DASHBOARD_DRIVER = grafana
DASHBOARD_HOST = '127.0.0.1'
DASHBOARD_PORT = '3000'
DASHBOARD_USER = 'admin'
DASHBOARD_PASS = 'admin'


LAST_UPDATED = 'updated_at'
DATE_CREATED = 'created_at'
ID_FIELD = 'id'
ITEM_URL = ('regex("[\.-a-z0-9]{8}-[-a-z0-9]{4}-'
            '[-a-z0-9]{4}-[-a-z0-9]{4}-[-a-z0-9]{12}")')

ITEM_LOOKUP_FIELD = 'id'
ETAG = 'etag'
URL_PREFIX = 'api'
X_DOMAINS = '*'
X_HEADERS = 'Authorization, Content-Type, If-Match, ETag'
MAX_CONTENT_LENGTH = 20 * 1024 * 1024
