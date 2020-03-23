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

import os

from dci.stores import filesystem, swift

import flask
import sqlalchemy

# this is an application global variable
CONFIG = flask.Config('')
CONFIG.from_object('dci.settings')
CONFIG.from_object(os.environ.get('DCI_SETTINGS_MODULE'))


# todo(yassine): remove the param used by client's CI.
def generate_conf(param=None):
    return CONFIG


def get_engine():
    sa_engine = sqlalchemy.create_engine(
        CONFIG['SQLALCHEMY_DATABASE_URI'],
        pool_size=CONFIG['SQLALCHEMY_POOL_SIZE'],
        max_overflow=CONFIG['SQLALCHEMY_MAX_OVERFLOW'],
        encoding='utf8',
        convert_unicode=CONFIG['SQLALCHEMY_NATIVE_UNICODE'],
        echo=CONFIG['SQLALCHEMY_ECHO'])
    return sa_engine


def get_store(container):
    configuration = {}
    if container == 'files':
        configuration['container'] = CONFIG['STORE_FILES_CONTAINER']
    elif container == 'components':
        configuration['container'] = CONFIG['STORE_COMPONENTS_CONTAINER']
    if CONFIG['STORE_ENGINE'] == CONFIG['SWIFT_STORE']:
        configuration['os_username'] = CONFIG['STORE_USERNAME']
        configuration['os_password'] = CONFIG['STORE_PASSWORD']
        configuration['os_tenant_name'] = CONFIG['STORE_TENANT_NAME']
        configuration['os_auth_url'] = CONFIG['STORE_AUTH_URL']
        configuration['os_region_name'] = CONFIG['STORE_REGION']
        configuration['os_identity_api_version'] = CONFIG.get('STORE_IDENTITY_API_VERSION')
        configuration['os_user_domain_name'] = CONFIG.get('STORE_USER_DOMAIN_NAME')
        configuration['os_user_domain_id'] = CONFIG.get('STORE_USER_DOMAIN_ID')
        configuration['os_project_domain_id'] = CONFIG.get('STORE_PROJECT_DOMAIN_ID')
        configuration['os_project_domain_name'] = CONFIG.get('STORE_PROJECT_DOMAIN_NAME')
        store_engine = swift.Swift(configuration)
    else:
        configuration['path'] = CONFIG['STORE_FILE_PATH']
        store_engine = filesystem.FileSystem(configuration)
    return store_engine
