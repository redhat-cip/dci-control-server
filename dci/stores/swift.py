# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
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

from dci import stores
from dci.common import exceptions, utils

import logging
import os
import swiftclient

logger = logging.getLogger(__name__)


class Swift(stores.Store):

    def __init__(self, conf):
        self.os_username = conf.get('os_username', os.getenv('OS_USERNAME'))
        self.os_password = conf.get('os_password', os.getenv('OS_PASSWORD'))
        self.os_tenant_name = conf.get('os_tenant_name', os.getenv('OS_TENANT_NAME'))
        self.os_auth_url = conf.get('os_auth_url', os.getenv('OS_AUTH_URL'))
        self.os_options = dict()
        self.os_options['region_name'] = conf.get(
            'os_region_name', os.getenv('OS_REGION_NAME')
        )
        self.os_auth_version = conf.get(
            "os_identity_api_version", os.getenv("OS_IDENTITY_API_VERSION")
        )

        if not self.os_auth_version:
            if 'v2.0' in self.os_auth_url:
                self.os_auth_version = '2'
            elif 'v3' in self.os_auth_url:
                self.os_auth_version = '3'

        if self.os_auth_version == '3':
            self.os_options["user_domain_id"] = conf.get(
                "os_user_domain_id", os.getenv("OS_USER_DOMAIN_ID")
            )
            self.os_options["user_domain_name"] = conf.get(
                "os_user_domain_name", os.getenv("OS_USER_DOMAIN_NAME", "Default")
            )
            self.os_options['project_domain_id'] = conf.get(
                "os_project_domain_id", os.getenv("OS_PROJECT_DOMAIN_ID")
            )
            self.os_options['project_domain_name'] = conf.get(
                "os_project_domain_name", os.getenv("OS_PROJECT_DOMAIN_NAME", "Default")
            )
            self.os_options['project_name'] = self.os_tenant_name

            for opt in (
                "user_domain_id",
                "project_domain_id",
                "user_domain_name",
                "project_domain_name",
            ):
                if not self.os_options[opt]:
                    del(self.os_options[opt])

        self.container = conf.get('container')
        self.connection = self.get_connection()

    def get_connection(self):
        return swiftclient.client.Connection(auth_version=self.os_auth_version,
                                             user=self.os_username,
                                             key=self.os_password,
                                             tenant_name=self.os_tenant_name,
                                             os_options=self.os_options,
                                             authurl=self.os_auth_url)

    def delete(self, filename):
        try:
            self.connection.delete_object(self.container, filename,
                                          headers={'X-Delete-After': 1})
        except swiftclient.exceptions.ClientException as e:
            if e.http_status == 404:
                logger.warn('file %s not found in swift' % filename)
                return
            raise exceptions.StoreExceptions('Error while deleting file '
                                             '%s: %s' % (filename, str(e)),
                                             status_code=e.http_status)

    def get(self, filename):
        try:
            return self.connection.get_object(self.container, filename,
                                              resp_chunk_size=65535)
        except swiftclient.exceptions.ClientException as exc:
            raise exceptions.StoreExceptions('Error while getting file '
                                             '%s: %s' % (filename, str(exc)),
                                             status_code=exc.http_status)

    def head(self, filename):
        try:
            return self.connection.head_object(self.container, filename)
        except swiftclient.exceptions.ClientException as exc:
            raise exceptions.StoreExceptions('Error while heading file '
                                             '%s: %s' % (filename, str(exc)),
                                             status_code=exc.http_status)

    def upload(self, file_path, iterable, pseudo_folder=None,
               create_container=True):
        try:
            self.connection.head_container(self.container)
        except swiftclient.exceptions.ClientException as exc:
            if exc.http_status == 404 and create_container:
                try:
                    self.connection.put_container(self.container)
                except swiftclient.exceptions.ClientException as exc:
                    raise exceptions.StoreExceptions('Error while creating file '  # noqa
                                                     '%s: %s' % (file_path, str(exc)),  # noqa
                                                     status_code=exc.http_status)  # noqa

        utils.retry(
            self.connection.put_object,
            file_path,
            iterable,
            tries=3,
            delay=1,
            allowed_exceptions=(swiftclient.exceptions.ClientException,),
        )
