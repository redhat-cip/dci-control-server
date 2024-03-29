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

from dci.api.v1 import notifications
from dci.worker.umb import send_event_on_umb

import json
import logging
import os
import smtplib
import requests
import time
import zmq

try:
    from email.MIMEText import MIMEText
except ImportError:
    from email.mime.text import MIMEText

from zmq.eventloop import ioloop, zmqstream


logging.basicConfig(level="DEBUG")
logger = logging.getLogger(__name__)

ioloop.install()

context = zmq.Context()
receiver = context.socket(zmq.PULL)
receiver.bind("tcp://0.0.0.0:5557")
stream = zmqstream.ZMQStream(receiver)


def get_email_configuration():
    configuration = {
        "server": os.getenv("DCI_EMAIL_SERVER", "mail.distributed-ci.io"),
        "port": os.getenv("DCI_EMAIL_SERVER_PORT", 587),
        "account": os.getenv("DCI_EMAIL_ACCOUNT", "no-reply@distributed-ci.io"),
        "password": os.getenv("DCI_EMAIL_PASSWORD"),
    }

    return configuration


def get_dlrn_configuration():
    configuration = {
        "server": os.getenv("DCI_DLRN_SERVER_URL", "trunk.rdoproject.org"),
        "login": os.getenv("DCI_DLRN_LOGIN"),
        "password": os.getenv("DCI_DLRN_PASSWORD"),
    }

    if (
        not configuration["login"]
        or not configuration["password"]
        or not configuration["server"]
    ):
        raise

    return configuration


def dlrn_publish(event):
    dlrn_config = get_dlrn_configuration()

    if event["dlrn"]["commit_branch"] == "master":
        dlrn_config["endpoint"] = "api-centos-master-uc"
    else:
        dlrn_config["endpoint"] = (
            "api-centos-%s" % event["dlrn"]["commit_branch"].split("/")[1]
        )

    payload = {
        "job_id": "DCI-%s" % event["topic_name"],
        "commit_hash": event["dlrn"]["commit_hash"],
        "distro_hash": event["dlrn"]["distro_hash"],
        "url": ("https://www.distributed-ci.io/jobs/%s/jobStates" % event["job_id"]),
        "timestamp": int(time.time()),
        "success": "true" if event["status"] == "success" else "false",
    }

    requests.post(
        "https://%s/%s/api/report_result"
        % (dlrn_config["server"], dlrn_config["endpoint"]),
        auth=(dlrn_config["login"], dlrn_config["password"]),
        data=json.dumps(payload),
        headers={"Content-type": "application/json"},
    )


def _get_smtp_server(email_configuration):
    server = smtplib.SMTP(email_configuration["server"], email_configuration["port"])
    server.starttls()
    if email_configuration["account"] and email_configuration["password"]:
        server.login(email_configuration["account"], email_configuration["password"])
    return server


def send_job_mail(mesg):
    email_configuration = get_email_configuration()
    if email_configuration:
        subject = "[DCI Status][%s][%s][%s]" % (
            mesg["topic_name"],
            mesg["remoteci_name"],
            mesg["status"],
        )
        message = notifications.format_job_mail_message(mesg)
        email = MIMEText(message)
        email["From"] = (
            "Distributed-CI Notification <%s>" % email_configuration["account"]
        )
        email["subject"] = subject
        email["DCI-remoteci"] = mesg["remoteci_id"]
        email["DCI-topic"] = mesg["topic_id"]

        server = _get_smtp_server(email_configuration)
        for contact in mesg["emails"]:
            # email.message are not classic dict, a new affectation does
            # not overwrite the previous one.
            del email["To"]
            email["To"] = contact
            server.sendmail(email["From"], email["To"], email.as_string())
        server.quit()


def send_component_mail(event):
    email_configuration = get_email_configuration()
    if email_configuration:
        subject = "[DCI Status][%s][%s][%s]" % (
            event["topic_name"],
            event["component_name"],
            event["status"],
        )
        message = notifications.format_component_mail_message(event)
        email = MIMEText(message)
        email["From"] = (
            "Distributed-CI Notification <%s>" % email_configuration["account"]
        )
        email["subject"] = subject

        server = _get_smtp_server(email_configuration)
        for contact in event["emails"]:
            # email.message are not classic dict, a new affectation does
            # not overwrite the previous one.
            del email["To"]
            email["To"] = contact
            server.sendmail(email["From"], email["To"], email.as_string())
        server.quit()


def loop(msg):
    try:
        events = json.loads(msg[0])
        logger.info("Worker received %d events." % len(events))
        for event in events:
            try:
                logger.info("Start processing event type %s" % event["event"])
                time_start = time.time()
                if event["event"] == "notification":
                    send_job_mail(event)
                elif event["event"] == "component_notification":
                    send_component_mail(event)
                elif event["event"] == "dlrn_publish":
                    dlrn_publish(event)
                elif event["event"] == "job_finished":
                    send_event_on_umb(event)
                time_end = time.time()
                logger.info(
                    "Event %s returned in %.2f seconds"
                    % (event["event"], time_end - time_start)
                )
            except Exception:
                logger.exception(
                    msg="An error has occurred while processing an event: %s" % event
                )
        logger.info("Worker processed all received events.")
    except Exception:
        logger.exception(msg="An error has occurred processing events.")


stream.on_recv(loop)
ioloop.IOLoop.instance().start()
