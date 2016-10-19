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

from dci import dci_config
from dci.db import models

conf = dci_config.generate_conf()
engine = dci_config.get_engine(conf)

context = zmq.Context()
receiver = context.socket(zmq.PULL)
receiver.bind('tcp://0.0.0.0:5557')

poller = zmq.Poller()
poller.register(receiver, zmq.POLLIN)

_TABLE = models.TEAMS

while True:
    socks = dict(poller.poll())
    if receiver in socks and socks[receiver] == zmq.POLLIN:
        msg = json.loads(receiver.recv_json()[0])
        try:
            if msg['values']['status'] == "failure":
                query = (sql.select([_TABLE])
                         .where(_TABLE.team_id == msg['job']['team_id']))
                result = engine.db_conn.execute(query).fetchone()
                if result['notification'] == True:
                    if result['email'] not None:
                        email.mail(msg, result['email'])
        except:
            pass
