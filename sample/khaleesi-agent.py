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

import glob
import os
import shutil
import signal
import six
import subprocess
import sys
import tempfile
import yaml

from dci import client
from dci.client import utils


try:
    config_file = sys.argv[1]
except IndexError:
    print("Usage: %s config_file" % sys.argv[0])
    sys.exit(1)

config_file = sys.argv[1]

# TODO(Gonéri): Create a load_config() method or something similar
settings = yaml.load(open(config_file, 'r'))

dci_client = client.DCIClient()

if subprocess.call([
        'ssh', '-o', 'StrictHostKeyChecking=no',
        '-o', 'KbdInteractiveAuthentication=no',
        '-o', 'PreferredAuthentications=publickey',
        '-o', 'PasswordAuthentication=no',
        '-o', 'User=root', '-o', 'ConnectTimeout=60',
        'root@%s' % settings['hypervisor'], 'date']) != 0:
    print('Cannot connect to hypervisor %s as root' % settings['hypervisor'])
    sys.exit(1)

test_name = "khaleesi-tempest"

r = dci_client.get("/tests/%s" % test_name)
if r.status_code == 404:
    print("Test '%s' doesn't exist." % test_name)
    sys.exit(1)
else:
    test_id = r.json()['id']
try:
    r = dci_client.get("/remotecis/%s" % settings['name'])
except client.DCIServerError as e:
    if e.status_code == 404:
        r = dci_client.post("/remotecis", {
            'name': settings['name'],
            'test_id': test_id})
remoteci_id = r.json()['id']
try:
    r = dci_client.post("/jobs", {"remoteci_id": remoteci_id})
except client.DCIServerError as e:
    if e.status_code == 412:
        print(e.message)
        sys.exit(0)
    else:
        raise e
job = r.json()


def kill_handler(signum, frame):
    state = {"job_id": job['id'],
             "status": 'killed',
             "comment": "Job killed on the remote CI (sig: %s)." % signum}
    dci_client.post("/jobstates", state)
    print("Job killed by the user.")
    sys.exit(0)
signal.signal(signal.SIGINT, kill_handler)

# Get full job
r = dci_client.get("/jobs/%s" % job['id'],
                   embedded={'jobdefinition': 1,
                             'jobdefinition.components': 1,
                             'jobdefinition.components.componenttype': 1})
job = r.json()
structure_from_server = job['data']

venv_dir = tempfile.mkdtemp()
components = job['jobdefinition']['components']

python_bin = venv_dir + '/bin/python'
pip_bin = venv_dir + '/bin/pip'
ansible_playbook_bin = venv_dir + '/bin/ansible-playbook'
ksgen_bin = venv_dir + '/bin/ksgen'
workspace_dir = tempfile.mkdtemp()
kh_dir = workspace_dir + '/khaleesi'

cmds = [
    {'args': ['virtualenv', venv_dir]},
    {'args': [pip_bin, 'install', '-U', 'ansible==1.9.2']},
    {'args': [ansible_playbook_bin, '--version']}]

for component in components:
    project_canonical_name = component['canonical_project_name']
    component_dir = workspace_dir + '/' + project_canonical_name
    if component.get('ref'):
        ref = component['ref']
    else:
        ref = ''
    cmds += [
        {'args': ['virtualenv', venv_dir]},
        {'args': [pip_bin, 'install', '-U', 'ansible==1.9.2']},
        {'args': ['git', 'init', component_dir]},
        {'args': ['git', 'pull',
                  component['git'],
                  ref], 'cwd': component_dir},
        {'args': ['git', 'fetch', '--all'], 'cwd': component_dir},
        {'args': ['git', 'clean', '-ffdx'], 'cwd': component_dir},
        {'args': ['git', 'reset', '--hard'], 'cwd': component_dir}]

    if 'sha' in component:
        cmds.append({'args': ['git', 'checkout', '-f',
                     component['sha']], 'cwd': component_dir})

cmds.append(
    {'args': [python_bin, 'setup.py', 'develop'],
     'cwd': '%s/tools/ksgen' % kh_dir})

for cmd in cmds:
    r = dci_client.call(job['id'], cmd['args'],
                        cwd=cmd.get('cwd'), status="initializing")
    if r['returncode'] != 0:
        print("Test has failed")
        shutil.rmtree(workspace_dir)
        sys.exit(1)


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
            for sv in utils.flatten(v):
                args.append('--%s' % (k))
                args.append(sv)
        else:
            args.append('--%s' % (k))
            args.append('%s' % (v))
with open(kh_dir + '/ssh.config.ansible', "w") as fd:
    fd.write('')

args.append('--extra-vars')
args.append('@' + workspace_dir +
            '/khaleesi-settings/hardware_environments' +
            '/virt/network_configs/none/hw_settings.yml')
args.append(workspace_dir + '/ksgen_settings.yml')

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
    # 'BEAKER_MACHINE': settings['hypervisor'],
    'TEST_MACHINE': settings['hypervisor'],
    'PWD': kh_dir,
    'CONFIG_BASE': workspace_dir + '/khaleesi-settings/settings',
    'WORKSPACE': workspace_dir})

print("test machine is: %s" % environ['TEST_MACHINE'])

collected_files_path = ("%s/collected_files" %
                        kh_dir)
print(collected_files_path)
if os.path.exists(collected_files_path):
    shutil.rmtree(collected_files_path)
r = dci_client.call(job['id'],
                    args,
                    cwd=kh_dir,
                    env=environ)

if r['returncode'] != 0:
    print("ksgen has failed")
    shutil.rmtree(workspace_dir)
    sys.exit(1)


shutil.copyfile(workspace_dir + '/khaleesi/ansible.cfg.example',
                workspace_dir + '/khaleesi/ansible.cfg')
with open(workspace_dir + '/khaleesi/ansible.cfg', 'a+') as f:
    f.write('ssh_args = -F ssh.config.ansible\n')

with open(workspace_dir + '/khaleesi/ssh.config.ansible', 'w') as f:
    f.write('#nothing\n')
    pass

args = [
    ansible_playbook_bin,
    '-vvvv', '--extra-vars',
    '@' + workspace_dir + '/ksgen_settings.yml',
    '-i', kh_dir + '/local_hosts',
    kh_dir + '/playbooks/full-job-no-test.yml']

status = 'success'
r = dci_client.call(job['id'],
                    args,
                    cwd=kh_dir,
                    env=environ,
                    timeout=7200)
if r['returncode'] != 0:
    print("Test has failed")
    status = 'failure'

for log in glob.glob(collected_files_path + '/*'):
    with open(log) as f:
        dci_client.upload_file(f, r['jobstate_id'])
state = {"job_id": job["id"],
         "status": status,
         "comment": "Job has been processed"}
jobstate = dci_client.post("/jobstates", state).json()
shutil.rmtree(workspace_dir)
