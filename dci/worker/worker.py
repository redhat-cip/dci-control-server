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
from dci.api.v1 import utils as v1_utils
from dci.db import models
from dci import dci_config

ioloop.install()

context = zmq.Context()
receiver = context.socket(zmq.PULL)
receiver.bind('tcp://0.0.0.0:5557')
stream = zmqstream.ZMQStream(receiver)
dci_context = context.build_dci_context()
conf = dci_config.generate_conf()
engine = dci_config.get_engine(conf)
es_engine = es_client.DCIESEngine(conf['ES_HOST'], conf['ES_PORT'], 'dci')


def fingerprints(mesg):
    if 'fingerprint_id' in mesg.keys():
        fps = [v1_utils.verify_existence_and_get(fp_id, models.FINGERPRINTS)]
    else:
        where_clause = table.c.state != 'archived'
        query = sql.select([models.FINGERPRINTS]).where(where_clause)
        fps = db_conn.execute(query).fetchall()
    for fp in fps:
        if 'job_id' in mesg.keys():
            if es_engine.search_by_id(fp.fingerprint['regexp'], job_id)['match']:
                #DO ACTION of FP
        else:
            results = es_engine.search(fp.fingerprint['regexp'])
            for result in results['match_job']:
                #DO ACTION of FP


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
