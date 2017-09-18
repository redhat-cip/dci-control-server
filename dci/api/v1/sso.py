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

from dci.api.v1 import api
from dci import dci_config

import flask
import uuid


_conf = dci_config.generate_conf()
_SSO_URL = _conf['SSO_URL']
_SSO_REALM = _conf['SSO_REALM']
_SSO_CLIENT_ID = _conf['SSO_CLIENT_ID']
_SSO_REDIRECT = _conf['SSO_REDIRECT']


@api.route('/sso', methods=['GET'])
def redirect_to_sso():
    redirect_to = '%s/auth/realms/%s/protocol/openid-connect/auth?'\
        'client_id=%s'\
        '&response_type=id_token'\
        '&scope=all'\
        '&nonce=%s'\
        '&redirect_uri=%s' % (_SSO_URL, _SSO_REALM, _SSO_CLIENT_ID,
                              str(uuid.uuid4()), _SSO_REDIRECT)
    return flask.redirect(redirect_to)
