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
import yaml

import client


try:
    remoteci_name = sys.argv[1]
except IndexError:
    print("Usage: %s remoteci_name" % sys.argv[0])
    sys.exit(1)


dci_client = client.DCIClient()

test_name = "khaleesi-tempest"

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

venv_dir = tempfile.mkdtemp()
dci_client.call(job_id,
                ['virtualenv', venv_dir])

components = structure_from_server['components']

# TODO(Gonéri): Create a load_config() method or something similar
settings = yaml.load(open('local_settings.yml', 'r'))
python_bin = venv_dir + '/bin/python'
pip_bin = venv_dir + '/bin/pip'
ansible_playbook_bin = venv_dir + '/bin/ansible-playbook'
ksgen_bin = venv_dir + '/bin/ksgen'
workspace_dir = tempfile.mkdtemp()

dci_client.call(job_id, [pip_bin, 'install', '-U', 'ansible==1.9.2'])
dci_client.call(job_id, [ansible_playbook_bin, '--version'])
for component_name, component in six.iteritems(components):
    component_dir = workspace_dir + '/' + component_name
    dci_client.call(job_id, ['git', 'init', component_dir])
    dci_client.call(job_id, ['git', 'pull',
                             component['git'],
                             component.get('ref', '')],
                    cwd=component_dir, ignore_error=True)
    dci_client.call(job_id, ['git', 'fetch', '--all'],
                    cwd=component_dir)
    dci_client.call(job_id, ['git', 'clean', '-ffdx'],
                    cwd=component_dir)
    dci_client.call(job_id, ['git', 'reset', '--hard'],
                    cwd=component_dir)
    if 'sha' in component:
        dci_client.call(job_id, ['git', 'checkout', '-f',
                                 component['sha']],
                        cwd=component_dir)

kh_dir = workspace_dir + '/khaleesi'

dci_client.call(job_id, [python_bin, 'setup.py', 'develop'],
                cwd='%s/tools/ksgen' % kh_dir)


args = [ksgen_bin,
        '--config-dir=%s/khaleesi-settings/settings' % (
            workspace_dir),
        'generate']
for ksgen_args in (structure_from_server.get('ksgen_args', {}),
                   settings.get('ksgen_args', {})):
    for k, v in six.iteritems(ksgen_args):
        if isinstance(v, list):
            for sv in v:
                args.append('--%s' % (k))
                args.append(sv)
        elif isinstance(v, dict):
            for sk, sv in six.iteritems(v):
                args.append('--%s' % (k))
                args.append('%s=%s' % (sk, sv))
        else:
            args.append('--%s' % (k))
            args.append('%s' % (v))
ksgen_settings_file = tempfile.NamedTemporaryFile()
with open(kh_dir + '/ssh.config.ansible', "w") as fd:
    fd.write('')

args.append(ksgen_settings_file.name)
environ = os.environ
environ.update({
    'PYTHONPATH': './tools/ksgen',
    'JOB_NAME': '',
    'ANSIBLE_HOST_KEY_CHECKING': 'False',
    'ANSIBLE_ROLES_PATH': kh_dir + '/roles',
    'ANSIBLE_LIBRARY': kh_dir + '/library',
    'ANSIBLE_DISPLAY_SKIPPED_HOSTS': 'False',
    'ANSIBLE_FORCE_COLOR': 'yes',
    'ANSIBLE_CALLBACK_PLUGINS': kh_dir + '/khaleesi/plugins/callbacks/',
    'ANSIBLE_FILTER_PLUGINS': kh_dir + '/khaleesi/plugins/filters/',
    'ANSIBLE_SSH_ARGS': ' -F ssh.config.ansible',
    'ANSIBLE_TIMEOUT': '60',
    # TODO(Gonéri): BEAKER_MACHINE is probably deprecated
    'BEAKER_MACHINE': settings['hypervisor'],
    'TEST_MACHINE': settings['hypervisor'],
    'HOST': settings['hypervisor'],
    'PWD': kh_dir,
    'CONFIG_BASE': workspace_dir + '/khaleesi-settings/settings',
    'WORKSPACE': workspace_dir})

collected_files_path = ("%s/collected_files" %
                        kh_dir)
print(collected_files_path)
if os.path.exists(collected_files_path):
    shutil.rmtree(collected_files_path)
dci_client.call(job_id,
                args,
                cwd=kh_dir,
                env=environ)

args = [
    ansible_playbook_bin,
    '-vvvv', '--extra-vars',
    '@' + ksgen_settings_file.name,
    '-i', kh_dir + '/local_hosts',
    kh_dir + '/playbooks/full-job-no-test.yml']

status = 'success'
try:
    jobstate_id = dci_client.call(job_id,
                                  args,
                                  cwd=kh_dir,
                                  env=environ)
except client.DCICommandFailure:
    print("Test has failed")
    status = 'failure'
    pass
for log in glob.glob(collected_files_path + '/*'):
    with open(log) as f:
        dci_client.upload_file(f, jobstate_id)
state = {"job_id": job["id"],
         "status": status,
         "comment": "Job has been processed"}
jobstate = dci_client.post("/jobstates", state).json()
