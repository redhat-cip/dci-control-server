# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Red Hat, Inc
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


class BaseTSDB(object):

    def __init__(self, **kwargs):
        self.host = kwargs.get('host', None)
        self.port = kwargs.get('port', None)
        self.user = kwargs.get('user', None)
        self.password = kwargs.get('password', None)
        self.conn = None

    @property
    def host(self):
        return self.host

    @property
    def port(self):
        return self.port

    def create_database(self, name):
        pass

    def create_user(self, name, password):
        pass

    def grant_privilege(self, username, databasename):
        pass
