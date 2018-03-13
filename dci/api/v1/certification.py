# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Red Hat, Inc
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

import base64

from dci.common import schemas

try:
    from xmlrpclib import ServerProxy
except ImportError:
    from xmlrpc.client import ServerProxy

import flask

from dci import dci_config
from dci.api.v1 import api
from dci import decorators
from dci.api.v1.files import get_file_descriptor, get_file_object


def build_certification(username, password, node_id, file_name, file_content):
    return {
        'username': username,
        'password': password,
        'id': node_id,
        'type': 'certification',
        'data': base64.b64encode(file_content),
        'description': 'DCI automatic upload test log',
        'filename': file_name
    }


@api.route('/files/<uuid:file_id>/certifications', methods=['POST'])
@decorators.login_required
@decorators.check_roles
def upload_certification(user, file_id):
    data = schemas.file_upload_certification.post(flask.request.json)

    file_object = get_file_object(file_id)
    file_descriptor = get_file_descriptor(file_object)
    file_content = file_descriptor.read()

    username = data['username']
    password = data['password']
    conf = dci_config.generate_conf()
    proxy = ServerProxy(conf['CERTIFICATION_HOST'])
    certification_details = proxy.Cert.getOpenStack_4_7({
        'username': username,
        'password': password,
        'certification_id': data['certification_id']
    })
    certification = build_certification(
        username,
        password,
        certification_details['cert_nid'],
        file_object['name'],
        file_content
    )
    proxy.Cert.uploadTestLog(certification)
    return flask.Response(None, 204, content_type='application/json')
