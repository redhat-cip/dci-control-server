#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
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

import glob
import os
import shutil
import six
import sys
import tempfile

import client


try:
    remoteci_name = sys.argv[1]
except IndexError:
    print("Usage: %s remoteci_name" % sys.argv[0])
    sys.exit(1)


dci_client = client.DCIClient()

test_name = "khaleesi"

r = dci_client.get("/tests/%s" % test_name)
if r.status_code == 404:
    print("Test '%s' doesn't exist." % test_name)
    sys.exit(1)
else:
    test_id = r.json()['id']
r = dci_client.get("/remotecis/%s" % remoteci_name)
if r.status_code == 404:
    r = dci_client.post("/remotecis", {
        'name': remoteci_name,
        'test_id': test_id})
remoteci_id = r.json()['id']

job_id = dci_client.post(
    "/jobs", {"remoteci_id": remoteci_id}).json()['id']
job = dci_client.get("/jobs/%s" % job_id).json()
structure_from_server = job['data']

# TODO(Gonéri): Create a load_config() method or something similar
import yaml
settings = yaml.load(open('local_settings.yml', 'r'))

for k, v in six.iteritems(structure_from_server['ksgen_args']):
    if isinstance(v, dict):
        settings['ksgen_args'][k] = v
    else:
        settings['ksgen_args'][k] = v.replace(
            '%%KHALEESI_SETTINGS%%',
            settings['location']['khaleesi_settings'])
args = [settings['location'].get('python_bin', 'python'),
        './tools/ksgen/ksgen/core.py',
        '--config-dir=%s/settings' % (
            settings['location']['khaleesi_settings']),
        'generate']
for k, v in six.iteritems(settings['ksgen_args']):
    if isinstance(v, dict):
        for sk, sv in six.iteritems(v):
            args.append('--%s' % (k))
            args.append('%s=%s' % (sk, sv))
    else:
        args.append('--%s' % (k))
        args.append('%s' % (v))
ksgen_settings_file = tempfile.NamedTemporaryFile()
args.append(ksgen_settings_file.name)
environ = os.environ
environ['PYTHONPATH'] = './tools/ksgen'

collected_files_path = ("%s/collected_files" %
                        settings['location']['khaleesi'])
if os.path.exists(collected_files_path):
    shutil.rmtree(collected_files_path)
dci_client.call(job_id,
                args,
                cwd=settings['location']['khaleesi'],
                env=environ)

args = [
    './run.sh', '-vvvv', '--use',
    ksgen_settings_file.name,
    'playbooks/packstack.yml']
jobstate_id = dci_client.call(job_id,
                              args,
                              cwd=settings['location']['khaleesi'])
for log in glob.glob(collected_files_path + '/*'):
    with open(log) as f:
        dci_client.upload_file(f, jobstate_id)
# NOTE(Gonéri): this call slow down the process (pulling data
# that we have sent just before)
jobstate = dci_client.get("/jobstates/%s" % jobstate_id).json()
final_status = 'success' if jobstate['_status'] == 'OK' else 'failure'
state = {"job_id": job["id"],
         "status": final_status,
         "comment": "Job has been processed"}
jobstate = dci_client.post("/jobstates", state).json()
