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

from dci.tsdb import driver
from dci.common import exceptions
from influxdb import InfluxDBClient
from influxdb import InfluxDBClientError
from influxdb import InfluxDBServerError


class InfluxDB(driver.BaseTSDB):

    def __init__(self, conf):
        super(InfluxDB, self).__init__(host=conf['INFLUXDB_HOST'],
                                       port=conf['INFLUXDB_PORT'],
                                       user=conf['INFLUXDB_USER'],
                                       password=conf['INFLUXDB_PASS'])
        self.conn = InfluxDBClient(self.host, self.port, self.user,
                                   self.password)

    def create_database(self, name):
        try:
            self.conn.create_database(name)
        except InfluxDBServerError as e:
            raise exceptions.DCITsdbInfluxDBException(str(e))
        except InfluxDBClientError as e:
            raise exceptions.DCITsdbInfluxDBException(str(e))

    def create_user(self, name, password):
        try:
            self.conn.create_user(name, password)
        except InfluxDBServerError as e:
            raise exceptions.DCITsdbInfluxDBException(str(e))
        except InfluxDBClientError as e:
            raise exceptions.DCITsdbInfluxDBException(str(e))

    def grant_privilege(self, username, databasename):
        try:
            self.conn.grant_privilege('all', databasename, username)
        except InfluxDBServerError as e:
            raise exceptions.DCITsdbInfluxDBException(str(e))
        except InfluxDBClientError as e:
            raise exceptions.DCITsdbInfluxDBException(str(e))
