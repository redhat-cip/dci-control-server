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

from cryptography.hazmat.primitives import serialization
import json
from jwt.algorithms import RSAAlgorithm
import requests

from dci import auth
from dci import dci_config
from dci.common import exceptions as dci_exc


from jwt import exceptions as jwt_exc


def get_latest_public_key(self):
    sso_url = dci_config.CONFIG.get('SSO_URL')
    realm = dci_config.CONFIG.get('SSO_REALM')
    url = "%s/auth/realms/%s/.well-known/openid-configuration" % (sso_url, realm)
    jwks_uri = requests.get(url).json()["jwks_uri"]
    jwks = requests.get(jwks_uri).json()["keys"]
    return RSAAlgorithm.from_jwk(json.dumps(jwks[0])).public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def decode_token_with_latest_public_key(token):
    """Get the latest public key and decode the JWT token with it. This
    function is usefull when the SSO server rotated its key."""
    conf = dci_config.CONFIG
    try:
        latest_public_key = get_latest_public_key()
    except Exception as e:
        raise dci_exc.DCIException('Unable to get last SSO public key: %s' % str(e),  # noqa
                                    status_code=401)
    # SSO server didn't update its public key
    if conf['SSO_PUBLIC_KEY'] == latest_public_key:
        raise dci_exc.DCIException('Invalid JWT token.', status_code=401)  # noqa
    try:
        decoded_token = auth.decode_jwt(token,
                                        latest_public_key,
                                        conf['SSO_CLIENT_ID'])
        conf['SSO_PUBLIC_KEY'] = latest_public_key
        return decoded_token
    except (jwt_exc.DecodeError, TypeError):
        raise dci_exc.DCIException('Invalid JWT token.', status_code=401)  # noqa
    except jwt_exc.ExpiredSignatureError:
        raise dci_exc.DCIException('JWT token expired, please refresh.',  # noqa
                                    status_code=401)
