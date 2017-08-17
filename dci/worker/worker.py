#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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

import zmq
import json
import smtplib

from zmq.eventloop import ioloop, zmqstream
from dci.elasticsearch import es_client
from dci import dci_config
from dciclient.v1.api import context
from dciclient.v1.api import job
from dciclient.v1.api import fingerprint

ioloop.install()

zmqcontext = zmq.Context()
receiver = zmqcontext.socket(zmq.PULL)
receiver.bind('tcp://0.0.0.0:5557')
stream = zmqstream.ZMQStream(receiver)
dci_context = context.build_dci_context()
conf = dci_config.generate_conf()
engine = dci_config.get_engine(conf)
es_engine = es_client.DCIESEngine(conf['ES_HOST'], conf['ES_PORT'], 'dci')


def fingerprints(mesg):
    if 'fingerprint_id' in mesg.keys():
        fps = [fingerprint.get(dci_context,
                               mesg['fingerprint_id']).json()['fingerprint']]
    else:
        fps = fingerprint.list(dci_context).json()['fingerprints']

    for fp in fps:
        print fp
        if 'job_id' in mesg.keys():
            search = es_engine.search_by_id(fp['fingerprint']['regexp'],
                                            mesg['job_id'])
            if search['hits']['hits']:
                meta = job.set_meta(dci_context,
                                    mesg['job_id'],
                                    fp['id'],
                                    "fingerprint")
                if meta.status == 204:
                    print('do actions')

        else:
            search = es_engine.search(fp['fingerprint']['regexp'])
            for result in search['hits']['hits']:
                meta = job.set_meta(dci_context,
                                    result['fields']['job_id'][0],
                                    fp['id'],
                                    "fingerprint")
                if meta.status == 204:
                    print('do actions')


def mail(mesg):
    FROM = 'Distributed-CI <dci@distributed-ci.io>'

    SUBJECT = "DCI Status"

    message = "Subject: %s\n"\
              "You are receiving this email because of the DCI job %s\n"\
              "For the topic : %s on the Remote CI : %s\n"\
              "The current status of the job is : %s\n"\
              "Message : %s"\
              "For more information : "\
              "https://www.distributed-ci.io/#!/jobs/%s/results"\
              % (SUBJECT, mesg['job_id'], mesg['topic_id'],
                 mesg['remoteci_id'], mesg['status'], mesg['mesg'],
                 mesg['job_id'])

    # Send the mail
    server = smtplib.SMTP('localhost')
    for email in mesg['emails']:
        TO = [email]
        server.sendmail(FROM, TO, message)
    server.quit()


def loop(msg):
    try:
        mesg = json.loads(msg[0])
        if mesg['event'] == 'notification':
            mail(mesg)
        elif mesg['event'] == 'fingerprints':
            fingerprints(mesg)
    except:
        pass

stream.on_recv(loop)
ioloop.IOLoop.instance().start()
