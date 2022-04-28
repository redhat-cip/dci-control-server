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
from dci.common import exceptions


class Store(object):
    def __init__(self, conf):
        self.containers = conf["containers"]

    def delete(self, container, filename):
        pass

    def get(self, container, filename):
        pass

    def upload(self, container, filename, iterable):
        pass

    def _get_container(self, container_name):
        if container_name not in self.containers:
            raise exceptions.StoreExceptions(
                "container name %s not in available containers" % container_name,
                status_code=400,
            )
        return self.containers[container_name]
