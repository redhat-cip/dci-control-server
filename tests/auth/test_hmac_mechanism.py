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

from dci import auth_mechanism
from dci.common import exceptions as dci_exc

import pytest


def test_hmac_mechanism_get_client_info():
    mechanism = auth_mechanism.HmacMechanism({})
    client_info = mechanism.get_client_info({
        'DCI-Client-Info': 'remoteci/426fc04f04bf8fdb5831dc37bbb6dcf70f63a37e'
    })
    expected_client_info = {
        'type': 'remoteci',
        'id': '426fc04f04bf8fdb5831dc37bbb6dcf70f63a37e',
    }
    for key in expected_client_info.keys():
        assert expected_client_info[key] == client_info[key]


def test_hmac_mechanism_invalid_header_raise_exception():
    mechanism = auth_mechanism.HmacMechanism({})
    with pytest.raises(dci_exc.DCIException):
        mechanism.get_client_info({
            'DCI-Invalid-Header': ''
        })


def test_hmac_mechanism_from_outside(remoteci_context):
    jobs_request = remoteci_context.get('/api/v1/jobs')
    assert jobs_request.status_code == 200


def test_hmac_mechanism_params(remoteci_context):
    jobs_request = remoteci_context.get('/api/v1/jobs?embed=components')
    assert jobs_request.status_code == 200
