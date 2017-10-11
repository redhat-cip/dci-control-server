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
from datetime import datetime
from sqlalchemy import sql

from dci.db import models
from dci.common import signature
from dci import auth
from dci.identity import Identity


class BaseMechanism(object):
    def __init__(self, request):
        self.request = request
        self.identity = None

    def is_valid(self):
        """Test if the user is a valid user."""
        pass


class BasicAuthMechanism(BaseMechanism):
    def is_valid(self):
        auth = self.request.authorization
        if not auth:
            return False
        user, is_authenticated = \
            self.get_user_and_check_auth(auth.username, auth.password)
        if not is_authenticated:
            return False
        self.identity = user
        return True

    def get_user_and_check_auth(self, username, password):
        """Check the combination username/password that is valid on the
        database.
        """
        constraint = sql.or_(
            models.USERS.c.name == username,
            models.USERS.c.email == username
        )

        user = Identity.from_db(models.USERS, constraint)
        if user is None:
            return None, False

        return user, auth.check_passwords_equal(password, user.get('password'))


class SignatureAuthMechanism(BaseMechanism):
    def is_valid(self):
        """Tries to authenticate a request using a signature as authentication
        mechanism.
        Returns True or False.
        Sets self.identity to the authenticated entity for later use.
        """
        # Get headers and extract information
        try:
            client_info = self.get_client_info()
            their_signature = self.request.headers.get('DCI-Auth-Signature')
        except ValueError:
            return False

        identity = self.get_identity(client_info['type'], client_info['id'])
        if identity is None:
            return False
        self.identity = identity

        return self.verify_auth_signature(
            identity, client_info['timestamp'], their_signature)

    @staticmethod
    def get_identity(client_type, client_id):
        """Get a client including its API secret
        """
        allowed_types_model = {
            'remoteci': models.REMOTECIS,
            'feeder': models.FEEDERS,
        }

        client_model = allowed_types_model.get(client_type, None)
        if client_model is None:
            return None

        constraint = client_model.c.id == client_id

        identity = Identity.from_db(client_model, constraint)
        return identity

    def get_client_info(self):
        """Extracts timestamp, client type and client id from a
        DCI-Client-Info header.
        Returns a hash with the three values.
        Throws an exception if the format is bad or if strptime fails."""
        bad_format_exception = \
            ValueError('DCI-Client-Info should match the following format: ' +
                       '"YYYY-MM-DD HH:MI:SSZ/<client_type>/<id>"')

        client_info = self.request.headers.get('DCI-Client-Info', '')
        client_info = client_info.split('/')
        if len(client_info) != 3 or not all(client_info):
            raise bad_format_exception

        dateformat = '%Y-%m-%d %H:%M:%SZ'
        return {
            'timestamp': datetime.strptime(client_info[0], dateformat),
            'type': client_info[1],
            'id': client_info[2],
        }

    def verify_auth_signature(self, client, timestamp,
                              their_signature):
        """Extract the values from the request, and pass them to the signature
        verification method."""
        if client.api_secret is None:
            return False

        return signature.is_valid(
            their_signature=their_signature.encode('utf-8'),
            secret=client.api_secret.encode('utf-8'),
            http_verb=self.request.method.upper().encode('utf-8'),
            content_type=(self.request.headers.get('Content-Type')
                          .encode('utf-8')),
            timestamp=timestamp,
            url=self.request.path.encode('utf-8'),
            query_string=self.request.query_string,
            payload=self.request.data)
