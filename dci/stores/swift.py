# Copyright 2016 Yanis Guenane <yguenane@redhat.com>
# Author: Yanis Guenane <yguenane@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dci import stores
from dci.common import exceptions

import os
import swiftclient


class Swift(stores.Store):

    def __init__(self, conf):
        self.os_username = conf.get('os_username',
                                    os.getenv('OS_USERNAME'))
        self.os_password = conf.get('os_password',
                                    os.getenv('OS_PASSWORD'))
        self.os_tenant_name = conf.get('os_tenant_name',
                                       os.getenv('OS_TENANT_NAME'))
        self.os_auth_url = conf.get('os_auth_url',
                                    os.getenv('OS_AUTH_URL'))
        self.os_options = dict()
        self.os_options['region_name'] = conf.get('os_region_name',
                                                  os.getenv('OS_REGION_NAME'))
        self.container = conf.get('container')
        self.connection = self.get_connection()

    def get_connection(self):
        return swiftclient.client.Connection(auth_version='2',
                                             user=self.os_username,
                                             key=self.os_password,
                                             tenant_name=self.os_tenant_name,
                                             os_options=self.os_options,
                                             authurl=self.os_auth_url)

    def delete(self, filename):
        try:
            self.connection.delete_object(self.container, filename)
        except swiftclient.exceptions.ClientException:
            raise exceptions.StoreExceptions('An error occured while '
                                             'deleting %s' % filename)

    def get(self, filename):
        try:
            return self.connection.get_object(self.container, filename,
                                              resp_chunk_size=65535)
        except swiftclient.exceptions.ClientException as exc:
            if exc.http_code == 404:
                raise exceptions.DCINotFound('file not found', filename)
            raise exceptions.DCIException(exc.http_reason)

    def head(self, filename):
        try:
            return self.connection.head_object(self.container, filename)
        except swiftclient.exceptions.ClientException:
            raise exceptions.DCINotFound('Content File', filename)

    def upload(self, file_path, iterable, pseudo_folder=None,
               create_container=True):
        try:
            self.connection.head_container(self.container)
        except swiftclient.exceptions.ClientException as exc:
            if exc.http_reason == 'Not Found' and create_container:
                self.connection.put_container(self.container)

        self.connection.put_object(self.container, file_path, iterable)

    @staticmethod
    def build_file_path(root, middle, file_id):
        root = str(root)
        middle = str(middle)
        file_id = str(file_id)
        return "%s/%s/%s" % (root, middle, file_id)
