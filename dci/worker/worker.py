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

import json
import os
import smtplib
import zmq

from email.MIMEText import MIMEText
from zmq.eventloop import ioloop, zmqstream


ioloop.install()

context = zmq.Context()
receiver = context.socket(zmq.PULL)
receiver.bind('tcp://0.0.0.0:5557')
stream = zmqstream.ZMQStream(receiver)


def get_email_configuration():

    configuration = {
        'server': os.getenv('DCI_EMAIL_SERVER', 'mail.distributed-ci.io'),
        'port': os.getenv('DCI_EMAIL_SERVER_PORT', 587),
        'account': os.getenv('DCI_EMAIL_ACCOUNT'),
        'password': os.getenv('DCI_EMAIL_PASSWORD'),
    }

    if not configuration['account'] or not configuration['password']:
        configuration = None

    return configuration


def mail(mesg):
    email_configuration = get_email_configuration()
    if email_configuration:
        subject = 'DCI Status'
        message = "Subject: %s\n"\
                  "DCI-remoteci: %s\n"\
                  "DCI-topic: %s\n"\
                  "You are receiving this email because of the DCI job %s\n"\
                  "For the topic : %s/%s on the Remote CI : %s/%s\n"\
                  "The current status of the job is : %s\n"\
                  "The components used are the following: %s\n"\
                  "Message : %s"\
                  "For more information : "\
                  "https://www.distributed-ci.io/#!/jobs/%s/results"\
                  % (subject, mesg['remoteci_name'], mesg['topic_name'],
                     mesg['job_id'], mesg['topic_id'], mesg['topic_name'],
                     mesg['remoteci_id'], mesg['remoteci_name'],
                     mesg['status'], mesg['mesg'], mesg['components'],
                     mesg['job_id'])

        email = MIMEText(message)
        email["From"] = 'Distributed-CI Notification <%s>' % \
            email_configuration['account']
        email["subject"] = subject

        server = smtplib.SMTP(email_configuration['server'],
                              email_configuration['port'])
        server.starttls()
        server.login(email_configuration['account'],
                     email_configuration['password'])
        for contact in mesg['emails']:
            email['To'] = contact
            server.sendmail(email['From'], email['To'], email.as_string())
        server.quit()


def loop(msg):
    try:
        mesg = json.loads(msg[0])
        if mesg['event'] == 'notification':
            mail(mesg)
    except:
        pass

stream.on_recv(loop)
ioloop.IOLoop.instance().start()
