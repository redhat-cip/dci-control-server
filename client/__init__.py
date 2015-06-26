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
import simplejson.scanner
import subprocess
import tempfile
import time


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
        return self.s.patch(
            "%s%s" % (self.end_point, path), data=json.dumps(data))

    def post(self, path, data):
        return self.s.post("%s%s" % (
            self.end_point, path), data=json.dumps(data))

    def get(self, path, where={}, params=None):
        return self.s.get("%s%s?where=%s" % (
            self.end_point, path, json.dumps(where)), params=params)

    def list_items(self, item_type, where={}, embedded={},
                   projection={}, page=1, max_results=10):
        """List the items for a given products.

        Return an iterator.
        """
        while True:
            r = self.s.get(
                '%s/%s?where=%s&embedded=%s'
                '&projection=%s&page=%d&max_results=%d' % (
                    self.end_point,
                    item_type,
                    json.dumps(where),
                    json.dumps(embedded),
                    json.dumps(projection),
                    page,
                    max_results))
            try:
                rd = r.json()
            except simplejson.scanner.JSONDecodeError as e:
                print(r.text)
                raise e
            if '_items' in rd:
                for item in rd['_items']:
                    yield item
            if '_links' not in rd:
                raise Exception
            if 'next' not in rd['_links']:
                break
            page += 1

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
            return self.post("/files", data)

    def call(self, job_id, arg, cwd=None, env=None, ignore_error=False):
        state = {"job_id": job_id,
                 "status": "ongoing",
                 "comment": "calling: %s" % " ".join(arg)}
        jobstate_id = self.post("/jobstates", state).json()["id"]
        print("Calling: %s" % arg)
        try:
            p = subprocess.Popen(arg,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 cwd=cwd,
                                 env=env)
        except OSError as e:
            state = {"job_id": job_id,
                     "status": "failure",
                     "comment": "internal failure: %s" % e}
            self.post("/jobstates", state)
            raise DCIInternalFailure

        f = tempfile.TemporaryFile()
        f.write(("starting: %s" % " ".join(arg)).encode('utf-8'))
        while p.returncode is None and p.stdout:
            # TODO(Gonéri): print on STDOUT p.stdout
            time.sleep(0.1)
            for c in p.stdout:
                print(c.decode('utf-8'))
                f.write(c)
            p.poll()
        self.upload_file(f, jobstate_id, name='output.log')

        if p.returncode != 0 and not ignore_error:
            state = {"job_id": job_id,
                     "status": "failure",
                     "comment": "call failure w/ code %s" % (p.returncode)}
            self.post("/jobstates", state)
            raise DCICommandFailure
        return jobstate_id


class DCIInternalFailure(Exception):
    pass


class DCICommandFailure(Exception):
    """Raised when a user-defined command has failed"""
    pass
