# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
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

import os

SQLALCHEMY_DATABASE_URI = os.environ.get(
    'OPENSHIFT_POSTGRESQL_DB_URL',
    'postgresql://boa:boa@127.0.0.1:5432/dci_control_server'
)


LAST_UPDATED = 'updated_at'
DATE_CREATED = 'created_at'
ID_FIELD = 'id'
ITEM_URL = ('regex("[\.-a-z0-9]{8}-[-a-z0-9]{4}-'
            '[-a-z0-9]{4}-[-a-z0-9]{4}-[-a-z0-9]{12}")')

ITEM_LOOKUP_FIELD = 'id'
ETAG = 'etag'
DEBUG = True
URL_PREFIX = 'api'
X_DOMAINS = '*'
X_HEADERS = 'Authorization'
# The following two lines will output the SQL statements
# executed by SQLAlchemy. Useful while debugging and in
# development. Turned off by default
# --------
SQLALCHEMY_ECHO = False
SQLALCHEMY_RECORD_QUERIES = False
