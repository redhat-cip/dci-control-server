import codecs
import jenkins
from pprint import pprint
print(jenkins)
import requests
import client

hexlify = codecs.getencoder('hex')


def upload_job(jobstates_collection):
    log = ''
    for jobstate in jobstates_collection['_items']:
        log += jobstate['comment']
        for _file in jobstate['files_collection']:
            log += _file['content']

    payload = ("<run><log encoding=\"hexBinary\">" +
               "%s" % (hexlify(log.encode())[0]) +
               "</log><result>%s</result>" % (0) +
               "<duration>%s</duration></run>" % (123))
    r = requests.post(
        "http://localhost:8080/job/external_job/postBuildResult", data=payload)
    print(r)


jenkins_srv = jenkins.Jenkins('http://localhost:8080')
print("Connected to Jenkins version %s" % jenkins_srv.get_version())
dci_srv = client.DCIClient()

job_name = 'external_job'

testversions = dci_srv.get(
    '/testversions', embedded={'jobs_collection': 1}).json()['_items']
for testversion in testversions:
    pprint(testversion['jobs_collection'][0]['jobstates_collection'])
    jobstates_collection = dci_srv.get(
        '/jobstates',
        _in=testversion['jobs_collection'][0]['jobstates_collection'],
        embedded={'files_collection': 1}).json()
    upload_job(jobstates_collection)
