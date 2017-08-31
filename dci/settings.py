# -*- encoding: utf-8 -*-
#
# Copyright 2015-2016 Red Hat, Inc.
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

# Database (SQLAlchemy) related parameters
#
SQLALCHEMY_DATABASE_URI = 'postgresql://dci:password@127.0.0.1:5432/dci'

# The following two lines will output the SQL statements
# executed by SQLAlchemy. Useful while debugging and in
# development. Turned off by default
# --------
SQLALCHEMY_ECHO = False
SQLALCHEMY_RECORD_QUERIES = False

SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 0
SQLALCHEMY_NATIVE_UNICODE = True

# Stores configuration, to store files and components
# STORE
STORE_ENGINE = 'Swift'
STORE_USERNAME = 'dci_components'
STORE_PASSWORD = 'test'
STORE_TENANT_NAME = 'DCI-Prod'
STORE_AUTH_URL = 'http://46.231.132.68:5000/v2.0'
STORE_CONTAINER = 'dci_components'
STORE_FILES_CONTAINER = 'dci_files'
STORE_COMPONENTS_CONTAINER = 'dci_components'

# ZMQ Connection
ZMQ_CONN = "tcp://127.0.0.1:5557"

# Logging related parameters
PROD_LOG_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
DEBUG_LOG_FORMAT = (
    '-' * 80 + '\n' +
    '%(levelname)s at %(asctime)s in %(name)s:\n' +
    '%(message)s\n' +
    '-' * 80
)

LOG_FILE = '/tmp/dci.log'


LAST_UPDATED = 'updated_at'
DATE_CREATED = 'created_at'
ID_FIELD = 'id'
ITEM_URL = ('regex("[\.-a-z0-9]{8}-[-a-z0-9]{4}-'
            '[-a-z0-9]{4}-[-a-z0-9]{4}-[-a-z0-9]{12}")')

ITEM_LOOKUP_FIELD = 'id'
ETAG = 'etag'
URL_PREFIX = 'api'
X_DOMAINS = '*'
X_HEADERS = 'Authorization, Content-Type, If-Match, ETag, X-Requested-With'
MAX_CONTENT_LENGTH = 20 * 1024 * 1024

FILES_UPLOAD_FOLDER = '/var/lib/dci-control-server/files'

SSO_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAgBH5yRAVT3gkOyUXMIVn
wSB6L/gurcAIAr4OIg83rduY8v7JGG3FL30bFr38dRGBQCWGDUqzeSRg0KVtfUk0
r01CTa8WDvj/A35P8ANhYjZQb6Rx2ibyhTwnm4QSVLeBe424M8ybRgRl9WkAixRO
iNNF2o9uNWJkTFLZ8wCGnYcu/PI8ZQCi/PnFjF+r63id8VOG5eSDrTLZuqbs9L0L
L4w3+R8tgTIUWl2X/Fps760XYl9r3WjAXc8aYiLPqYR6EheoC00QZmGxRbdq8yVt
csnCpzVVAEEaQEwv/Smu9e1L2ObyAp387xjDOTHQZNXMb7TSJuhxyOLQQ3NWO+1o
zQIDAQAB
-----END PUBLIC KEY-----
"""
