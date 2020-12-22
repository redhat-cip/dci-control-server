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
import os

HOST = os.getenv('API_HOST', '127.0.0.1')
PORT = int(os.getenv('API_PORT', '5000'))
DEBUG = True
JSONIFY_PRETTYPRINT_REGULAR = False

# Database (SQLAlchemy) related parameters
#
DB_USER = os.getenv('DB_USER', 'dci')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'dci')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME', 'dci')
DEFAULT_SQLALCHEMY_DATABASE_URI = 'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'.format(  # noqa
    db_user=DB_USER,
    db_password=DB_PASSWORD,
    db_host=DB_HOST,
    db_port=DB_PORT,
    db_name=DB_NAME,
)
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI',
                                    DEFAULT_SQLALCHEMY_DATABASE_URI)

# The following two lines will output the SQL statements
# executed by SQLAlchemy. Useful while debugging and in
# development. Turned off by default
# --------
SQLALCHEMY_ECHO = False
SQLALCHEMY_RECORD_QUERIES = False

SQLALCHEMY_POOL_SIZE = 5
SQLALCHEMY_MAX_OVERFLOW = 15
SQLALCHEMY_NATIVE_UNICODE = True

# Stores configuration, to store files and components
# STORE
FILE_STORE = 'file'
SWIFT_STORE = 'swift'
STORE_FILE_PATH = os.getenv('STORE_FILE_PATH', '/tmp/')
STORE_ENGINE = os.getenv('STORE_ENGINE', FILE_STORE)
STORE_USERNAME = os.getenv('STORE_USERNAME', 'dci')
STORE_PASSWORD = os.getenv('STORE_PASSWORD', 'dci')
STORE_TENANT_NAME = os.getenv('STORE_TENANT_NAME', 'dci')
STORE_HOST = os.getenv('STORE_HOST', 'swift')
STORE_PORT = int(os.getenv('STORE_PORT', '5001'))
DEFAULT_STORE_AUTH_URL = 'http://{store_host}:{store_port}/v3'.format(
    store_host=STORE_HOST,
    store_port=STORE_PORT
)
STORE_AUTH_URL = os.getenv('STORE_AUTH_URL', DEFAULT_STORE_AUTH_URL)
STORE_REGION = os.getenv('STORE_REGION', 'regionOne')
STORE_CONTAINER = os.getenv('STORE_CONTAINER', 'dci_components')
STORE_FILES_CONTAINER = os.getenv('STORE_FILES_CONTAINER', 'dci_files')
STORE_COMPONENTS_CONTAINER = os.getenv('STORE_COMPONENTS_CONTAINER',
                                       'dci_components')

# ZMQ Connection
ZMQ_HOST = os.getenv('ZMQ_HOST', '127.0.0.1')
ZMQ_PORT = int(os.getenv('ZMQ_PORT', '5557'))
DEFAULT_ZMQ_CONN = 'tcp://{zmq_host}:{zmq_port}'.format(
    zmq_host=ZMQ_HOST,
    zmq_port=ZMQ_PORT
)
ZMQ_CONN = os.getenv('ZMQ_CONN', DEFAULT_ZMQ_CONN)

# Logging related parameters
LOG_LEVEL = 'INFO'
LOG_FORMAT = '[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s'


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
MAX_CONTENT_LENGTH = 128 * 1024 * 1024

FILES_UPLOAD_FOLDER = os.getenv('FILES_UPLOAD_FOLDER', '/var/lib/dci-control-server/files')  # noqa

# SSO_PUBLIC_KEY is set by bin/dci-gen-pem-ks-key.py
SSO_PUBLIC_KEY = os.getenv('SSO_PUBLIC_KEY')
SSO_CLIENT_ID = os.getenv('SSO_CLIENT_ID', 'dci')
SSO_READ_ONLY_GROUP = os.getenv('SSO_READ_ONLY_GROUP', 'redhat:employees')
SSO_URL = os.getenv('SSO_URL', 'https://sso.redhat.com')
SSO_REALM = os.getenv('SSO_REALM', 'redhat-external')

CA_CERT = '/etc/ssl/repo/ca.crt'
CA_KEY = '/etc/ssl/repo/ca.key'

CERTIFICATION_URL = 'https://access.stage.redhat.com/hydra/rest/cwe/xmlrpc/v2'
