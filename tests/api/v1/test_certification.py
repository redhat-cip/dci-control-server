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
import base64

from dci.api.v1 import certification


def test_build_certification():
    with open('tests/data/certification.xml.tar.gz', 'rb') as f:
        node_id = '40167'
        username = 'dci'
        password = 'dci'
        file_name = 'certification.xml.tar.gz'
        file_content = f.read()
        cert = certification.build_certification(username, password, node_id,
                                                 file_name, file_content)

        assert cert['username'] == 'dci'
        assert cert['password'] == 'dci'
        assert cert['id'] == '40167'
        assert cert['type'] == 'certification'
        assert cert['description'] == 'DCI automatic upload test log'
        assert cert['filename'] == 'certification.xml.tar.gz'

        base64.decodestring(cert['data'])
