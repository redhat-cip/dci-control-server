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


def generate_conf():
    conf = flask.Config('')
    conf.from_object('dci.settings')
    conf.from_object(os.environ.get('DCI_SETTINGS_MODULE'))
    return conf


def get_engine(conf):
    sa_engine = sqlalchemy.create_engine(
        conf['SQLALCHEMY_DATABASE_URI'],
        pool_size=conf['SQLALCHEMY_POOL_SIZE'],
        max_overflow=conf['SQLALCHEMY_MAX_OVERFLOW'],
        encoding='utf8',
        convert_unicode=conf['SQLALCHEMY_NATIVE_UNICODE'],
        echo=conf['SQLALCHEMY_ECHO'])
    return sa_engine


def get_store(container):
    conf = generate_conf()
    configuration = {}
    if container == 'files':
        configuration['container'] = conf['STORE_FILES_CONTAINER']
    elif container == 'components':
        configuration['container'] = conf['STORE_COMPONENTS_CONTAINER']
    if conf['STORE_ENGINE'] == conf['SWIFT_STORE']:
        configuration['os_username'] = conf['STORE_USERNAME']
        configuration['os_password'] = conf['STORE_PASSWORD']
        configuration['os_tenant_name'] = conf['STORE_TENANT_NAME']
        configuration['os_auth_url'] = conf['STORE_AUTH_URL']
        configuration['os_region_name'] = conf['STORE_REGION']
        store_engine = swift.Swift(configuration)
    else:
        configuration['path'] = conf['STORE_FILE_PATH']
        store_engine = filesystem.FileSystem(configuration)
    return store_engine
