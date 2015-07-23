#!/usr/bin/env python
# This script will connect on a Gerrit server and list the pending reviews.
# It will create the associated review in the DCI server and associate the
# tox check.
# If the version already exist, it will sync back the status of the version
# in Gerrit (-1/0/+1)

import subprocess
import sys
import yaml

import client

dci_project = "dci-control-server"

reviews = subprocess.check_output(['ssh', '-xp29418',
                                   'softwarefactory.enovance.com',
                                   'gerrit', 'query', '--format=json',
                                   'project:%s' % dci_project, 'status:open'])

dci_client = client.DCIClient()
products = dci_client.get('/products',
                          where={'name': dci_project}).json()
try:
    product = products['_items'][0]
except KeyError:
    print("Cannot find the product")
    sys.exit(1)

test = dci_client.get('/tests/tox').json()

for line in reviews.decode('utf-8').rstrip().split('\n'):
    review = yaml.load(line)
    if 'id' not in review:
        continue
    patchset_query_res = subprocess.check_output([
        'ssh', '-xp29418', 'softwarefactory.enovance.com',
        'gerrit', 'query', '--format=JSON',
        '--current-patch-set change:%d' % int(review['number'])])
    patchset = yaml.load(patchset_query_res.decode('utf-8').split('\n')[0])
    subject = patchset['commitMessage'].split('\n')[0]
    message = patchset['commitMessage']
    gerrit_id = patchset['id']
    url = patchset['url']
    ref = patchset['currentPatchSet']['ref']
    sha = patchset['currentPatchSet']['revision']
    versions = dci_client.get("/versions", where={'sha': sha}).json()

    if len(versions['_items']) == 0:
        r = dci_client.post("/versions", {
            "product_id": product['id'],
            "name": subject,
            "title": subject,
            "message": message,
            "sha": sha,
            "url": url,
            "data": {
                "git_url": (
                    "http://softwarefactory.enovance.com/r/%s" % dci_project),
                "ref": ref,
                "sha": sha,
                "gerrit_id": gerrit_id
            }
        })
        version = r.json()
        dci_client.post("/testversions", {
            "test_id": test['id'],
            "version_id": version['id'],
        })
    else:
        version = versions['_items'][0]
        testversions = dci_client.get(
            "/testversions",
            where={'version_id': version['id']}).json()
        status = '0'
        for testversion in testversions['_items']:
            builds = dci_client.get(
                "/jobs",
                where={'testversion_id': testversion['id']},
                embedded={'jobstates_collection': 1}).json()
            for build in builds['_items']:
                if build['jobstates_collection'][-1]['status'] == 'failure':
                    status = '-1'
                    break
                elif build['jobstates_collection'][-1]['status'] == 'success':
                    status = '1'
        subprocess.check_output([
            'ssh', '-xp29418', 'softwarefactory.enovance.com',
            'gerrit', 'review', '--verified', status,
            '--message', 'DCI',
            version['data']['sha']])
        print("%s: %s" % (subject, status))
