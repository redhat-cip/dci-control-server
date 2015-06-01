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

    def get(self, path, params=None):
        return self.s.get("%s%s" % (self.end_point, path), params=params)

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

    def call(self, job_id, arg, cwd=None, ignore_error=False):
        state = {"job_id": job_id,
                 "status": "ongoing",
                 "comment": "calling: %s" % " ".join(arg)}
        jobstate_id = self.post("/jobstates", state).json()["id"]
        print("Calling: %s" % arg)
        try:
            p = subprocess.Popen(arg,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 cwd=cwd)
        except OSError as e:
            state = {"job_id": job_id,
                     "status": "failure",
                     "comment": "internal failure: %s" % e}
            self.post("/jobstates", state)
            raise DCIInternalFailure

        f = tempfile.TemporaryFile()
        f.write("starting: %s" % " ".join(arg))
        while p.returncode is None and p.stdout:
            # TODO(Gonéri): print on STDOUT p.stdout
            time.sleep(1)
            for c in p.stdout:
                print(c.decode("UTF-8").rstrip())
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
