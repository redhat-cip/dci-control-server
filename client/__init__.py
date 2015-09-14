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

from __future__ import unicode_literals

import copy
import fcntl
import json
import os
import requests
import simplejson.scanner
import six
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
        self.s = self._connect(login, password)

    def _connect(self, login, password):
        s = requests.Session()
        s.headers.setdefault('Content-Type', 'application/json')
        s.auth = (login, password)
        return s

    def delete(self, path, etag=None):
        r = self.s.delete("%s%s" % (
            self.end_point,
            path),
            headers={'If-Match': etag})
        return r

    # TODO(Gonéri): Broken on Py27. To investigate.
    #    def patch(self, path, etag, data):
    #        return self.s.patch(
    #            "%s%s" % (self.end_point, path),
    #            data=json.dumps(data),
    #            headers={'If-Match': etag})

    def post(self, path, data):
        return self.s.post("%s%s" % (
            self.end_point, path), data=json.dumps(data))

    def put(self, path, etag, data):
        return self.s.put(
            "%s%s" % (self.end_point, path),
            data=json.dumps(data),
            headers={'If-Match': etag})

    def get(self, path, where={}, embedded={}, params=None):
        return self.s.get("%s%s?where=%s&embedded=%s" % (
            self.end_point, path,
            json.dumps(where),
            json.dumps(embedded)), params=params)

    def list_items(self, item_type, where={}, embedded={},
                   projection={}, page=1, max_results=10):
        """List the items for a given products.

        Return an iterator.
        """
        while True:
            r = self.s.get(
                '%s%s?where=%s&embedded=%s'
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
        while True:
            s = fd.read(1024).decode("UTF-8")
            output += s
            if s == '':
                break
        if output:
            data = {"name": name,
                    "content": output,
                    "mime": mime,
                    "jobstate_id": jobstate_id}
            return self.post("/files", data)

    def call(self, job_id, args, cwd=None, env=None,
             ignore_error=False, timeout=600):

        for idx, arg in enumerate(args):
            if six.PY2 and isinstance(arg, str):
                args[idx] = arg.decode('UTF-8')

        flatten_args = " ".join(args)
        state = {"job_id": job_id,
                 "status": "ongoing",
                 "comment": "calling: %s" % flatten_args}
        jobstate_id = self.post("/jobstates", state).json()["id"]
        print("Calling: %s" % flatten_args)
        try:
            p = subprocess.Popen(args,
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
        f.write(("starting: %s\n" % flatten_args).encode('UTF-8'))
        begin_at = int(time.time())
        fcntl.fcntl(p.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        while p.returncode is None:
            try:
                s = p.stdout.read()
                if s:
                    print(s)
                    f.write(s)
            except (OSError, IOError, TypeError):
                # ignore exceptions if there is no more data
                pass
            if time.time() - begin_at > timeout:
                print('timeout')
                f.write("Timeout! command has been Killed!\n".encode())
                p.kill()
                break
            p.poll()
            time.sleep(0.1)
        f.flush()
        self.upload_file(f, jobstate_id, name='output.log')
        f.close()

        if p.returncode != 0 and not ignore_error:
            state = {"job_id": job_id,
                     "status": "failure",
                     "comment": "call failure w/ code %s" % (p.returncode)}
            self.post("/jobstates", state)
        return {'jobstate_id': jobstate_id, 'returncode': p.returncode}

    def find_or_create_or_refresh(self, path, data, unicity_key=['name']):
        """Find, create or update an existing item

        The function doesn't return the full item, just the following keys:

        * id
        * etag
        * _status
        * created_at
        * updated_at

        """
        # TODO(Gonéri): need a test coverage
        where = {k: data[k] for k in unicity_key}
        items = self.get(path, where=where).json()
        if '_items' not in items:
            raise RuntimeError()
        elif len(items['_items']) == 1:
            item = items['_items'][0]
            current = copy.deepcopy(item)
            # NOTE(Gonéri): remove the autogenerated keys from the exsiting
            # entry to be able to compare it with the new one
            for c in ('_links', 'id', 'etag', 'created_at', 'updated_at'):
                del(current[c])
            if json.dumps(current, sort_keys=True) != \
               json.dumps(data, sort_keys=True):
                item = self.put(path + '/' + item['id'],
                                item['etag'], data).json()
        elif len(items['_items']) > 1:
            print("Duplicated element for %s, %s" % (path, unicity_key))
            raise RuntimeWarning()
        else:
            item = self.post(path, data).json()
        return item


class DCIInternalFailure(Exception):
    pass


class DCICommandFailure(Exception):
    """Raised when a user-defined command has failed"""
    pass
