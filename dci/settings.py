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
import os

# API parameters
HOST = os.environ.get('API_HOST', '0.0.0.0')
PORT = int(os.environ.get('API_PORT', '5000'))
DEBUG = os.environ.get('DEBUG', True)
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

# Database (SQLAlchemy) parameters
DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = int(os.environ.get('DB_PORT', '5432'))
DB_USER = os.environ.get('DB_USER', 'dci')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'dci')
DB_NAME = os.environ.get('DB_NAME', 'dci')
SQLALCHEMY_DATABASE_URI = 'postgresql://%s:%s@%s:%s/%s' % (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)  # noqa
SQLALCHEMY_ECHO = False
SQLALCHEMY_RECORD_QUERIES = False
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 0
SQLALCHEMY_NATIVE_UNICODE = True

# ElasticSearch parameters
ES_HOST = os.environ.get('ES_PORT', '127.0.0.1')
ES_PORT = int(os.environ.get('ES_PORT', '9200'))

# Swift parameters
SWIFT_HOST = os.environ.get('SWIFT_HOST', '127.0.0.1')
SWIFT_PORT = int(os.environ.get('SWIFT_PORT', '5000'))

STORE_ENGINE = os.environ.get('STORE_ENGINE ', 'Swift')
STORE_USERNAME = os.environ.get('STORE_USERNAME ', 'dci_components')
STORE_PASSWORD = os.environ.get('STORE_PASSWORD ', 'test')
STORE_TENANT_NAME = os.environ.get('STORE_TENANT_NAME ', 'test')
STORE_AUTH_URL = os.environ.get('STORE_AUTH_URL ', 'http://%s:%s/v2.0' % (SWIFT_HOST, SWIFT_PORT))  # noqa
STORE_CONTAINER = os.environ.get('STORE_CONTAINER ', 'dci_components')
STORE_FILES_CONTAINER = os.environ.get('STORE_FILES_CONTAINER ', 'dci_files')
STORE_COMPONENTS_CONTAINER = os.environ.get('STORE_COMPONENTS_CONTAINER ', 'dci_components')  # noqa

# ZeroMQ parameters
ZMQ_HOST = os.environ.get('ZMQ_HOST', '127.0.0.1')
ZMQ_PORT = int(os.environ.get('ZMQ_PORT', '5557'))
ZMQ_CONN = "tcp://%s:%s" % (ZMQ_HOST, ZMQ_PORT)

# SSO parameters
DEFAULT_SSO_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA64PNcZgs1adZG4wPuaTv
fM1r2K0E4Yanp4RHEhcn38yoMZy593jB10ej/i+fLv5CRchpLpUPVl6230ugObie
IU4n5BKwt1Y11Wt65UIIf6K3pDTVX5iaT0u6ISSSMHBMpLo5ndfHQHDoMhiyuIFt
DI/RzFlhayJM5GeNjA/qhDHqd2mDEftJ9RyEYCdnRmFm8juOzdsY3DOqp6FpZqQt
+72TRfEbsYG8RRYHKOzhC4yL+7DebWpJdwBjzFx+CbmQRLUmVmIbY0VtDAfVqfFN
yv0IboebFxlX5mCTijk1k3BU8Xb3+vY5CT8f2OSUM78dfrwyX/0uAMPdBl6e0yae
/JE4TV3WXqstpubVybW2SJQT5MIcLPkD9h6hmD5HV19nPYCd1YfImWr383LEHMmB
lT40f5PcBYlqQqOkZj1lUac62cfNRkNBYbONhTLSbK/hezMH3myIHmw+qctMJZtp
kf7/j0VSQf0f1BIChjXsFfkcDuEeeTXSSxh+I9xIB4uYpDbzUiuSlDk74aRaiB3S
USDOa5hKSVfeIv7bNNMgGJQEXXyBIKfajI1MZCEEAOp/SP66Gj4q4nnNJI6aSh+3
hZ3LTvCbgf1OdidRPayfIBECq/oU9hsfu1oX3sJXYdISqaxBXfyWXSbwt5Rv1HuV
4GdQgMGs8c49SX/5ZUZii3sCAwEAAQ==
-----END PUBLIC KEY-----
"""
SSO_PUBLIC_KEY = os.getenv('SSO_PUBLIC_KEY', DEFAULT_SSO_PUBLIC_KEY)
