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

from cryptography.hazmat.primitives import serialization
import datetime
import hashlib
import uuid
import flask
import json
from jwt.algorithms import RSAAlgorithm
import requests
import six
from sqlalchemy.engine import result
from werkzeug.routing import BaseConverter, ValidationError

from dci.common import exceptions
from dci import dci_config


def read(file_path, chunk_size=None, mode='rb'):
    chunk_size = chunk_size or 1024 ** 2  #  1MB
    with open(file_path, mode) as f:
        for chunk in iter(lambda: f.read(chunk_size) or None, None):
            yield chunk


class UUIDConverter(BaseConverter):

    def to_python(self, value):
        try:
            return uuid.UUID(value)
        except ValueError:
            raise ValidationError()

    def to_url(self, values):
        return str(values)


class JSONEncoder(flask.json.JSONEncoder):
    """Default JSON encoder."""
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        elif isinstance(o, result.RowProxy):
            return dict(o)
        elif isinstance(o, result.ResultProxy):
            return list(o)
        elif isinstance(o, uuid.UUID):
            return str(o)


def gen_uuid():
    return str(uuid.uuid4())


def gen_etag():
    """Generate random etag based on MD5."""

    my_salt = gen_uuid()
    if six.PY2:
        my_salt = my_salt.decode('utf-8')
    elif six.PY3:
        my_salt = my_salt.encode('utf-8')
    md5 = hashlib.md5()
    md5.update(my_salt)
    return md5.hexdigest()


def check_and_get_etag(headers):
    if_match_etag = headers.get('If-Match')
    if not if_match_etag:
        raise exceptions.DCIException("'If-match' header must be provided",
                                      status_code=412)
    return if_match_etag


def get_latest_public_key(self, sso_url, realm):
    sso_url = dci_config.CONFIG.get('SSO_URL')
    realm = dci_config.CONFIG.get('REALM')
    url = "%s/auth/realms/%s/.well-known/openid-configuration" % (sso_url, realm)
    jwks_uri = requests.get(url).json()["jwks_uri"]
    jwks = requests.get(jwks_uri).json()["keys"]
    return RSAAlgorithm.from_jwk(json.dumps(jwks[0])).public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
