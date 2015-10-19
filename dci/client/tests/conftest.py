# -*- encoding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
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

import dci.client as dci_client
import dci.client.tests.utils as utils
import dci.server.tests.conftest as server_conftest

import pytest


@pytest.fixture(scope='session')
def init_db_and_return_engine(request):
    return server_conftest.init_db_and_return_engine(request)


@pytest.fixture
def server(init_db_and_return_engine):
    return server_conftest.app(init_db_and_return_engine)


@pytest.fixture
def client(server):
    client = dci_client.DCIClient(
        end_point='http://dci_server.com/api',
        login='admin', password='admin'
    )
    flask_adapter = utils.FlaskHTTPAdapter(server.test_client())
    client.s.mount('http://dci_server.com', flask_adapter)
    return client


@pytest.fixture(autouse=True)
def db_provisioning(request, server):
    server_conftest.db_provisioning(request, server)
