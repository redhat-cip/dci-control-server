#!/usr/bin/env python
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
import sys
import json
import requests

try:
    from jwt.algorithms import RSAAlgorithm
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("Module cryptography or pyJWT not found")
    sys.exit(1)


"""The SSO server publish its public
key with the modulus and exponent. This script get the
public key from the SSO server and transform it to the PEM format.
The dci control server stores this value in its configuration file with the
key 'SSO_PUBLIC_KEY'.
"""

def get_latest_public_key(sso_url, realm):
    url = "%s/auth/realms/%s/.well-known/openid-configuration" % (sso_url, realm)
    jwks_uri = requests.get(url).json()["jwks_uri"]
    jwks = requests.get(jwks_uri).json()["keys"]
    return RSAAlgorithm.from_jwk(json.dumps(jwks[0])).public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )


if __name__ == "__main__":
    if len(sys.argv) < 3:
        usage = """
Usage:
$ %s SSO_URL REALM_NAME\n
Example:
$ %s http://localhost:8180 dci-test
$ %s https://sso.redhat.com redhat-external
                """ % (
            sys.argv[0],
            sys.argv[0],
            sys.argv[0],
        )
        print(usage)
        sys.exit(1)
    public_key = get_latest_public_key(sys.argv[1], sys.argv[2])
    print(public_key)
