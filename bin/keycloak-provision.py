#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
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

import json
import requests

import time

client_data = {
    "clientId": "dci",
    "rootUrl": "",
    "adminUrl": "",
    "surrogateAuthRequired": False,
    "enabled": True,
    "clientAuthenticatorType": "client-secret",
    "secret": "**********",
    "redirectUris": [
        "http://localhost:8000/*"
    ],
    "webOrigins": [
        "http://localhost:8000"
    ],
    "notBefore": 0,
    "bearerOnly": False,
    "consentRequired": False,
    "standardFlowEnabled": True,
    "implicitFlowEnabled": True,
    "directAccessGrantsEnabled": True,
    "serviceAccountsEnabled": False,
    "publicClient": True,
    "frontchannelLogout": False,
    "protocol": "openid-connect",
    "attributes": {
        "saml.assertion.signature": "False",
        "saml.force.post.binding": "False",
        "saml.multivalued.roles": "False",
        "saml.encrypt": "False",
        "saml_force_name_id_format": "False",
        "saml.client.signature": "False",
        "saml.authnstatement": "False",
        "saml.server.signature": "False",
        "saml.server.signature.keyinfo.ext": "False",
        "saml.onetimeuse.condition": "False"
    },
    "fullScopeAllowed": True,
    "nodeReRegistrationTimeout": -1,
    "protocolMappers": [
        {
            "name": "role list",
            "protocol": "saml",
            "protocolMapper": "saml-role-list-mapper",
            "consentRequired": False,
            "config": {
                "single": "false",
                "attribute.nameformat": "Basic",
                "attribute.name": "Role"
            }
        },
        {
            "name": "username",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-property-mapper",
            "consentRequired": False,
            "consentText": "${username}",
            "config": {
                "userinfo.token.claim": "true",
                "user.attribute": "username",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "claim.name": "username",
                "jsonType.label": "String"
            }
        },
        {
            "name": "given name",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-property-mapper",
            "consentRequired": True,
            "consentText": "${givenName}",
            "config": {
                "userinfo.token.claim": "true",
                "user.attribute": "firstName",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "claim.name": "given_name",
                "jsonType.label": "String"
            }
        },
        {
            "name": "family name",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-property-mapper",
            "consentRequired": True,
            "consentText": "${familyName}",
            "config": {
                "userinfo.token.claim": "true",
                "user.attribute": "lastName",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "claim.name": "family_name",
                "jsonType.label": "String"
            }
        },
        {
            "name": "full name",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-full-name-mapper",
            "consentRequired": True,
            "consentText": "${fullName}",
            "config": {
                "id.token.claim": "true",
                "access.token.claim": "true"
            }
        },
        {
            "name": "email",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-property-mapper",
            "consentRequired": True,
            "consentText": "${email}",
            "config": {
                "userinfo.token.claim": "true",
                "user.attribute": "email",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "claim.name": "email",
                "jsonType.label": "String"
            }
        },
        {
            "name": "docker-v2-allow-all-mapper",
            "protocol": "docker-v2",
            "protocolMapper": "docker-v2-allow-all-mapper",
            "consentRequired": False,
            "config": {}
        }
    ],
    "useTemplateConfig": False,
    "useTemplateScope": False,
    "useTemplateMappers": False
}


def get_access_token():
    r = None
    data = {'client_id': 'admin-cli',
            'username': 'admin',
            'password': 'admin',
            'grant_type': 'password'}
    while True:
        try:
            r = requests.post('http://keycloak:8180/auth/realms/master/protocol/openid-connect/token',
                              data=data)
            if r.status_code == 200:
                print('Keycloak access token get successfully.')
                return r.json()['access_token']
        except Exception:
            pass


def create_client(access_token):
    """Create the dci client in the master realm."""
    r = requests.post('http://keycloak:8180/auth/admin/realms/dci-test/clients',
                      data=json.dumps(client_data),
                      headers={'Authorization': 'bearer %s' % access_token,
                               'Content-Type': 'application/json'})
    if r.status_code in (201, 409):
        print('Keycloak client dci created successfully.')
    else:
        raise Exception('Error while creating Keycloak client dci:\nstatus code %s\n'
                        'error: %s' % (r.status_code, r.content))


def create_user_dci(access_token):
    """Create the a dci user.
    username=dci, password=dci, email=dci@distributed-ci.io"""
    user_data = {'username': 'dci',
                 'email': 'dci@distributed-ci.io',
                 'enabled': True,
                 'emailVerified': True,
                 'credentials': [{'type': 'password',
                                  'value': 'dci'}]}
    r = requests.post('http://keycloak:8180/auth/admin/realms/dci-test/users',
                      data=json.dumps(user_data),
                      headers={'Authorization': 'bearer %s' % access_token,
                               'Content-Type': 'application/json'})
    if r.status_code in (201, 409):
        print('Keycloak user dci created successfully.')
    else:
        raise Exception('Error while creating user dci:\nstatus code %s\n'
                        'error: %s' % (r.status_code, r.content))


def create_realm_dci_test(access_token):
    realm_data = {'realm': 'dci-test',
                  'enabled': True}
    r = requests.post('http://keycloak:8180/auth/admin/realms',
                      data=json.dumps(realm_data),
                      headers={'Authorization': 'bearer %s' % access_token,
                               'Content-Type': 'application/json'})
    if r.status_code in (201, 409):
        print('Keycloak realm dci-test created successfully.')
    else:
        raise Exception('Error while creating realm dci-test:\nstatus code %s\n'
                        'error: %s' % (r.status_code, r.content))


if __name__ == '__main__':
    access_token = get_access_token()
    create_realm_dci_test(access_token)
    create_client(access_token)
    create_user_dci(access_token)
