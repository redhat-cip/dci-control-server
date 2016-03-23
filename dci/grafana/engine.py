# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Red Hat, Inc
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

import datetime
import json
import requests


class DCIGrafanaEngine(object):

    def __init__(self, conf):
        self.__host = conf['GRAFANA_HOST']
        self.__port = conf['GRAFANA_PORT']
        self.__user = conf['GRAFANA_USER']
        self.__password = conf['GRAFANA_PASS']
        self.__influxdb_host = conf['INFLUXDB_HOST']
        self.__influxdb_port = conf['INFLUXDB_PORT']
        self.__influxdb_admin_user = conf['INFLUXDB_USER']
        self.__influxdb_admin_password = conf['INFLUXDB_PASS']
        self.__url = 'http://%s:%s@%s:%s' % (self.__user, self.__password,
                                             self.__host, self.__port)

        self.__dashboard = json.loads(open('/tmp/dashboard.json', 'r').read())

    def create_datasource(self, name):

        payload = {
            'name': name,
            'type': 'influxdb',
            'url': 'http://%s:%s' % (self.__influxdb_host,
                                     self.__influxdb_port),
            'access': 'direct',
            'database': name,
            'user': self.__influxdb_admin_user,
            'password': self.__influxdb_admin_password
        }

        requests.post('%s/api/datasources' % self.__url, data=payload)

    def create_dashboard(self, name):

        date_from = datetime.datetime.utcnow().isoformat('T') + 'Z'
        date_to = (datetime.datetime..utcnow() + datetime.timedelta(0, 7200)).isoformat('T') + 'Z'
        self.__dashboard['dashboard']['time']['from'] = date_from
        self.__dashboard['dashboard']['time']['to'] = date_to

        self.__dashboard['dashboard']['title'] = 'DCI Job - %s' % name
        self.__dashboard['dashboard']['originalTitle'] = 'DCI Job - %s' % name

        for row in self.__dashboard['dashboard']['rows']:
            for panel in row['panels']:
                panel['datasource'] = name

        requests.post('%s/api/dashboards/db' % self.__url,
                      json=self.__dashboard)
