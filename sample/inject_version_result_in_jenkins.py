#!/usr/bin/env python
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

"""
This is an example of a DCI client script that fetch job results
and inject them as new build in a Jenkins job.

This example depends on python-jenkins module.

Usage: dci-jenkins-import $jobdefinition_id

$jobdefinition_id is the ID of the DCI version from which you want to
collect jobs.
"""
from __future__ import print_function

import codecs
import email.utils
import requests
import sys
import time

import jenkins

import client

hexlify = codecs.getencoder('hex')
config_xml = """
<?xml version='1.0' encoding='UTF-8'?>
<hudson.model.ExternalJob plugin="external-monitor-job@1.4">
  <actions/>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties/>
</hudson.model.ExternalJob>
"""


def exit_error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def get_job_duration(jobstates):
    begin_date = email.utils.parsedate(
        jobstates[0]['created_at'])
    end_date = email.utils.parsedate(
        jobstates[-1]['created_at'])

    return int(time.mktime(end_date) - time.mktime(begin_date))


def get_last_code(jobstates):
    code = '-1'
    for jobstate in jobstates:
        if jobstate['status'] == 'success':
            code = 0
        elif jobstate['status'] == 'failure':
            code = 1
    return code


def upload_job(job_name, jobstates):
    log = ''
    for jobstate in jobstates:
        log += jobstate['comment']
        for _file in jobstate['files']:
            log += _file['content']

    payload = ("<run><log encoding=\"hexBinary\">" +
               "%s" % (hexlify(log.encode())[0]) +
               "</log><result>%s" % (get_last_code(jobstates)) +
               "</result>" +
               "<duration>%s" % (get_job_duration(jobstates)) +
               "</duration></run>")
    r = requests.post(
        "http://localhost:8080/job/%s/postBuildResult" % job_name,
        data=payload)
    if r.status_code == 200:
        print("Build created in '%s'" % job_name)


def get_testversions(version_id):
    r = dci_srv.get(
        '/testversions', where={'version_id': version_id},
        embedded={'jobs': 1, 'test': 1, 'version': 1}
    )
    if r.status_code == 404:
        return []
    if r.status_code != 200:
        exit_error('Unexpected error from DCI server (%s): %s' % (
            r.status_code, r.text))
    return r.json()['_items']

try:
    jobdefinition_id = sys.argv[1]
except IndexError:
    exit_error('Usage: %s $jobdefinition_id' % sys.argv[0])

dci_srv = client.DCIClient()
jenkins_srv = jenkins.Jenkins('http://localhost:8080')
print("Connected to Jenkins version %s" % jenkins_srv.get_version())

jobdefinition = dci_srv.get(
    '/jobdefinitions/%s' % jobdefinition_id,
    embedded={'test': 1}, projection={'jobs': 1}).json()

if len(jobdefinition['jobs']) < 1:
    print("No job associated to this jobdefinition.")
    sys.exit(0)

job_name = "DCI-%s" % (
    jobdefinition['test']['name'])

try:
    jenkins_srv.get_job_config(job_name)
except jenkins.NotFoundException:
    jenkins_srv.create_job(job_name, config_xml)

current_build_number = len(jenkins_srv.get_job_info(job_name)['builds'])

for job in dci_srv.list_items(
        '/jobs', where={'jobdefinition_id': jobdefinition_id},
        page=(current_build_number + 1),
        max_results=1,
        embedded={'jobstates': 1}):
    # NOTE(Gonéri): use the Jenkins build number to know the cur ID
    jobstates = job['jobstates']
    for jobstate in jobstates:
        jobstate['files'] = dci_srv.get(
            '/files',
            where={'jobstate_id': jobstate['id']}).json()['_items']
    upload_job(job_name, jobstates)
