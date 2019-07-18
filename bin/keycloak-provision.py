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


def get_auth_headers(access_token):
    return {'Authorization': 'bearer %s' % access_token,
            'Content-Type': 'application/json'}


def get_access_token():
    data = {'client_id': 'admin-cli',
            'username': 'admin',
            'password': 'admin',
            'grant_type': 'password'}
    while True:
        try:
            url = 'http://keycloak:8080/auth/realms/master/protocol/openid-connect/token'  # noqa
            r = requests.post(url,
                              data=data)
            if r.status_code == 200:
                print('Keycloak access token get successfully.')
                return r.json()['access_token']
        except Exception:
            pass


def create_realm_dci_test(access_token):
    realm_data = {'realm': 'dci-test',
                  'enabled': True}
    r = requests.post('http://keycloak:8080/auth/admin/realms',
                      data=json.dumps(realm_data),
                      headers=get_auth_headers(access_token))
    if r.status_code in (201, 409):
        print('Keycloak realm dci-test created successfully.')
    else:
        raise Exception(
            'Error while creating realm dci-test:\nstatus code %s\n'
            'error: %s' % (r.status_code, r.content)
        )


def create_client(access_token):
    """Create the dci client in the master realm."""
    url = 'http://keycloak:8080/auth/admin/realms/dci-test/clients'
    r = requests.post(url,
                      data=json.dumps(client_data),
                      headers=get_auth_headers(access_token))
    if r.status_code in (201, 409):
        print('Keycloak client dci created successfully.')
    else:
        raise Exception(
            'Error while creating Keycloak client dci:\nstatus code %s\n'
            'error: %s' % (r.status_code, r.content)
        )


def create_user_dci(access_token):
    """Create the a dci user.
    username=dci, password=dci, email=dci@distributed-ci.io"""
    user_data = {'username': 'dci',
                 'email': 'dci@distributed-ci.io',
                 'enabled': True,
                 'emailVerified': True,
                 'credentials': [{'type': 'password',
                                  'value': 'dci'}]}
    r = requests.post('http://keycloak:8080/auth/admin/realms/dci-test/users',
                      data=json.dumps(user_data),
                      headers=get_auth_headers(access_token))
    if r.status_code in (201, 409):
        print('Keycloak user dci created successfully.')
    else:
        raise Exception('Error while creating user dci:\nstatus code %s\n'
                        'error: %s' % (r.status_code, r.content))


def create_and_associate_redhat_role_to_dci_user(access_token):
    url = 'http://keycloak:8080/auth/admin/realms/dci-test/users/'
    user = requests.get(url, headers=get_auth_headers(access_token)).json()[0]
    url = 'http://keycloak:8080/auth/admin/realms/dci-test/roles/'
    requests.post(url,
                  data=json.dumps({"name": "redhat:employees"}),
                  headers=get_auth_headers(access_token))
    url = 'http://keycloak:8080/auth/admin/realms/dci-test/roles/redhat:employees'  # noqa
    r = requests.get(url, headers=get_auth_headers(access_token))
    redhat_employees = r.json()
    url = 'http://keycloak:8080/auth/admin/realms/dci-test/users/%s/role-mappings/realm' % user['id']  # noqa
    r = requests.post(url,
                      data=json.dumps([redhat_employees]),
                      headers=get_auth_headers(access_token))
    if r.status_code in (201, 204, 409):
        print('Role "redhat:employees" created successfully.')
    else:
        raise Exception('Error while creating role redhat:employees:\nstatus code %s\n'  # noqa
                        'error: %s' % (r.status_code, r.content))


def create_client_scope(access_token):
    url = "http://keycloak:8080/auth/admin/realms/dci-test/client-scopes"
    data = {"attributes": {"display.on.consent.screen": "true",
                           "include.in.token.scope": "true"},
            "name": "dci-audience",
            "protocol": "openid-connect"}
    r = requests.post(url,
                      data=json.dumps(data),
                      headers=get_auth_headers(access_token))
    if r.status_code in (201, 204, 409):
        print('Client scope "dci-audience" created successfully')
    else:
        raise Exception('Error while creating client scope "dci-audience":\nstatus code %s\n'  # noqa
                        'error: %s' % (r.status_code, r.content))


def get_client_scope_id(access_token):
    # get the "dci-audience" client scope ID
    url = "http://keycloak:8080/auth/admin/realms/dci-test/client-scopes"
    r = requests.get(url, headers=get_auth_headers(access_token))
    scopes = r.json()
    for scope in scopes:
        if scope['name'] == 'dci-audience':
            return scope['id']
    raise Exception('"dci-audience" scope not found')


def add_dci_audience_mapper_to_client_scope(access_token, scope_id):

    # associate a "dci" audience mapper to the client scope in order
    # to be present in the access token
    url = "http://keycloak:8080/auth/admin/realms/dci-test/client-scopes/%s/protocol-mappers/models" % scope_id  # noqa
    data = {"protocol": "openid-connect",
            "config": {"id.token.claim": "false",
                       "access.token.claim": "true",
                       "included.client.audience": "dci"},
            "name": "dci",
            "protocolMapper": "oidc-audience-mapper"}
    r = requests.post(url,
                      data=json.dumps(data),
                      headers=get_auth_headers(access_token))
    if r.status_code in (201, 204, 409):
        print('Adding "dci-audience" mapper to client scope successfully')
    else:
        raise Exception('Error while adding "dci-audience" mapper to client scope:\nstatus code %s\n'  # noqa
                        'error: %s' % (r.status_code, r.content))


def get_client_id(access_token):
    url = 'http://keycloak:8080/auth/admin/realms/dci-test/clients'
    r = requests.get(url, headers=get_auth_headers(access_token))
    clients = r.json()
    for client in clients:
        if client['clientId'] == 'dci':
            return client['id']
    raise Exception('client "dci" not found')


def associate_client_scope_to_dci_client(access_token, client_id, client_scope_id):  # noqa
    url = "http://keycloak:8080/auth/admin/realms/dci-test/clients/%s/default-client-scopes/%s" % (client_id, client_scope_id)  # noqa
    data = {"realm": "dci-test", "client": client_id,
            "clientScopeId": client_scope_id}
    r = requests.put(url,
                     data=json.dumps(data),
                     headers=get_auth_headers(access_token))
    if r.status_code in (201, 204, 409):
        print('Associating "dci-audience" client scope to dci client successfully')
    else:
        raise Exception('Error while associating "dci-audience" client scope to dci client:\nstatus code %s\n'  # noqa
                        'error: %s' % (r.status_code, r.content))


if __name__ == '__main__':
    access_token = get_access_token()
    create_realm_dci_test(access_token)
    create_client(access_token)
    create_user_dci(access_token)
    create_and_associate_redhat_role_to_dci_user(access_token)
    create_client_scope(access_token)
    client_scope_id = get_client_scope_id(access_token)
    client_id = get_client_id(access_token)
    add_dci_audience_mapper_to_client_scope(access_token, client_scope_id)  # noqa
    associate_client_scope_to_dci_client(access_token, client_id, client_scope_id)  # noqa
