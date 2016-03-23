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
import dci
import json
import os
import pkg_resources
import requests

from dci.dashboard import driver


class Grafana(driver.BaseDashboardEngine):

    def __init__(self, conf):
        super(Grafana, self).__init__(host=conf['DASHBOARD_HOST'],
                                      port=conf['DASHBOARD_PORT'],
                                      user=conf['DASHBOARD_USER'],
                                      password=conf['DASHBOARD_PASSWORD'],
                                      tsdb_host=conf['TSDB_HOST'],
                                      tsdb_port=conf['TSDB_PORT'],
                                      tsdb_user=conf['TSDB_USER'],
                                      tsdb_password=conf['TSDB_PASSWORD'])
        self.url = 'http://%s:%s@%s:%s' % (self.user, self.password, self.host,
                                           self.port)

        self.dashboard = json.loads(
            pkg_resources.resource_string(
                dci.__name__,
                os.path.join('data', 'dashboard.json')
            )
        )

    def create_datasource(self, name):

        payload = {
            'name': name,
            'type': 'influxdb',
            'url': 'http://%s:%s' % (self.tsdb_host, self.tsdb_port),
            'access': 'direct',
            'database': name,
            'user': self.tsdb_user,
            'password': self.tsdb_password
        }

        requests.post('%s/api/datasources' % self.url, data=payload)

    def create_dashboard(self, name):
        """Update the json dashboard template before pushing it to grafana.

        It sets :
          * Time from which the dashboard will display data
          * Title of the dasbhoard (based on the job_id)
          * Datasource of the dashboard
        """

        date_utc = datetime.datetime.utcnow()
        date_from = date_utc.isoformat('T') + 'Z'
        date_to = (date_utc + datetime.timedelta(0, 7200)).isoformat('T') + 'Z'
        self.dashboard['dashboard']['time']['from'] = date_from
        self.dashboard['dashboard']['time']['to'] = date_to

        title = 'OSP8 deployment - %s' % name
        self.dashboard['dashboard']['title'] = title
        self.dashboard['dashboard']['originalTitle'] = title

        for row in self.dashboard['dashboard']['rows']:
            for panel in row['panels']:
                panel['datasource'] = name

        requests.post('%s/api/dashboards/db' % self.url,
                      json=self.dashboard)
