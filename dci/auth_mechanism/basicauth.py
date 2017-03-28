# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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

from dci.auth_mechanism.base import BaseMechanism


class BasicAuthMechanism(BaseMechanism):

    def is_valid(self):
        auth = self.request.authorization
        if not auth:
            return False
        user, is_authenticated = self.auth_method(auth.username, auth.password)
        if not is_authenticated:
            return False
        self.identity = user
        return True
