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

import jwt
import requests

from dci import dci_config
from dci.common import exceptions as dci_exc
from dci import auth


def get_public_key_from_token(token):
    header = jwt.get_unverified_header(token)
    kid = header["kid"]
    sso_url = dci_config.CONFIG.get("SSO_URL")
    realm = dci_config.CONFIG.get("SSO_REALM")

    url = "%s/auth/realms/%s/.well-known/openid-configuration" % (sso_url, realm)
    openid_configuration = requests.get(url)
    if openid_configuration.status_code != 200:
        raise Exception(
            "unable to get sso openid-configuration from url '%s', status=%s, error=%s"
            % (url, openid_configuration.status_code, openid_configuration.text)
        )
    if "jwks_uri" not in openid_configuration.json():
        raise dci_exc.DCIException("jwks_uri key not in the sso openid-configuration")

    jwks_uri = openid_configuration.json()["jwks_uri"]
    keys = requests.get(jwks_uri)
    if keys.status_code != 200:
        raise dci_exc.DCIException(
            "unable to get jwks content from url '%s', status=%s, error=%s"
            % (jwks_uri, keys.status_code, keys.text)
        )
    if "keys" not in keys.json():
        raise dci_exc.DCIException("no 'keys' key found in jwks content")

    keys = keys.json()["keys"]
    for k in keys:
        if k["kid"] == kid:
            return auth.jwk_to_pem(k)
    raise dci_exc.DCIException("kid '%s' from token not found in sso server" % kid)
