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

Usage: dci-jenkins-import $version_id

$version_id is the ID of the DCI version from which you want to collect jobs.
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
product_by_id = {}


def exit_error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def get_job_duration(jobstates_collection):
    begin_date = email.utils.parsedate(
        jobstates_collection[0]['created_at'])
    end_date = email.utils.parsedate(
        jobstates_collection[-1]['created_at'])

    return int(time.mktime(end_date) - time.mktime(begin_date))


def get_last_code(jobstates_collection):
    code = '-1'
    for jobstate in jobstates_collection:
        if jobstate['status'] == 'success':
            code = 0
        elif jobstate['status'] == 'failure':
            code = 1
    return code


def upload_job(job_name, jobstates_collection):
    log = ''
    for jobstate in jobstates_collection:
        log += jobstate['comment']
        for _file in jobstate['files_collection']:
            log += _file['content']

    payload = ("<run><log encoding=\"hexBinary\">" +
               "%s" % (hexlify(log.encode())[0]) +
               "</log><result>%s" % (get_last_code(jobstates_collection)) +
               "</result>" +
               "<duration>%s" % (get_job_duration(jobstates_collection)) +
               "</duration></run>")
    r = requests.post(
        "http://localhost:8080/job/%s/postBuildResult" % job_name,
        data=payload)
    if r.status_code == 200:
        print("Build created in '%s'" % job_name)


def get_product(product_id):
    """return the product associated to $product_id."""
    try:
        product = product_by_id[testversion['version']['product_id']]
    except KeyError:
        product = dci_srv.get(
            '/products/%s' % testversion['version']['product_id']).json()
        product_by_id[testversion['version']['product_id']] = product
    return product


def get_testversions(version_id):
    r = dci_srv.get(
        '/testversions', where={'version_id': version_id},
        embedded={'jobs_collection': 1, 'test': 1, 'version': 1}
    )
    if r.status_code == 404:
        return []
    if r.status_code != 200:
        exit_error('Unexpected error from DCI server (%s): %s' % (
            r.status_code, r.text))
    return r.json()['_items']

try:
    version_id = sys.argv[1]
except IndexError:
    exit_error('Usage: %s $version_id' % sys.argv[0])

dci_srv = client.DCIClient()
jenkins_srv = jenkins.Jenkins('http://localhost:8080')
print("Connected to Jenkins version %s" % jenkins_srv.get_version())

for testversion in get_testversions(version_id):
    product = get_product(testversion['version']['product_id'])
    job_name = "DCI-%s-%s-%s" % (
        product['name'],
        testversion['version']['name'],
        testversion['test']['name'])
    try:
        jenkins_srv.get_job_config(job_name)
    except jenkins.NotFoundException:
        jenkins_srv.create_job(job_name, config_xml)

    # NOTE(Gonéri): use the Jenkins build number to know the cur ID
    current_build_number = len(jenkins_srv.get_job_info(job_name)['builds'])
    for job in testversion['jobs_collection']:
        jobstates_collection = dci_srv.get(
            '/jobstates',
            _in=job['jobstates_collection'],
            embedded={'files_collection': 1}).json()
        upload_job(job_name, jobstates_collection['_items'])
