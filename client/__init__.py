# -*- encoding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import os
import requests


class DCIClient(object):

    def __init__(self, end_point=None, login=None, password=None):
        if not end_point and not login and not password:
            end_point = os.environ['DCI_CONTROL_SERVER']
            login = os.environ['DCI_LOGIN']
            password = os.environ['DCI_PASSWORD']
        self.end_point = end_point
        self.s = requests.Session()
        self.s.headers.setdefault('Content-Type', 'application/json')
        self.s.auth = (login, password)

    def delete(self, path):
        return self.s.delete("%s%s" % (self.end_point, path))

    def patch(self, path, data):
        r = self.s.patch(
            "%s%s" % (self.end_point, path), data=json.dumps(data))
        return r.json()['id']

    def post(self, path, data):
        r = self.s.post("%s%s" % (self.end_point, path), data=json.dumps(data))
        if r.status_code != 201:
            raise DCIInternalFailure(r)
        return r.json()['id']

    def get(self, path, params=None):
        r = self.s.get("%s%s" % (self.end_point, path), params=params)
        return r.json()

    def upload_file(self, fd, jobstate_id, mime='text/plain', name=None):
        fd.seek(0)
        output = ""
        for l in fd:
            output += l.decode("UTF-8")
        if output:
            data = {"name": name,
                    "content": output,
                    "mime": mime,
                    "jobstate_id": jobstate_id}
            self.post("/files", data)


class DCIInternalFailure(Exception):
    pass
