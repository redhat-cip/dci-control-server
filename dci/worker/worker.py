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
import plugins.email as email
import json

from zmq.eventloop import ioloop, zmqstream
ioloop.install()

context = zmq.Context()
receiver = context.socket(zmq.PULL)
receiver.bind('tcp://0.0.0.0:5557')
stream = zmqstream.ZMQStream(receiver)

def loop(msg):
    try:
        mesg = json.loads(msg[0])
        email.mail(mesg['job_id'], mesg['email'])
    except:
        pass

stream.on_recv(loop)
ioloop.IOLoop.instance().start()
