# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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
import json
from jwt.algorithms import RSAAlgorithm
from cryptography.hazmat.primitives import serialization
from passlib.apps import custom_app_context as pwd_context


def hash_password(password):
    return pwd_context.hash(password)


def check_passwords_equal(password, encrypted_password):
    return pwd_context.verify(password, encrypted_password)


def jwk_to_pem(jwk):
    return RSAAlgorithm.from_jwk(json.dumps(jwk)).public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def decode_jwt(access_token, pem_public_key, audience):
    return jwt.decode(
        access_token,
        verify=True,
        key=pem_public_key,
        audience=audience,
        algorithms=["RS256"],
    )
