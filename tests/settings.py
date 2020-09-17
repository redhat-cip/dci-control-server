# -*- encoding: utf-8 -*-
#
# Copyright 2015-2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

DEBUG = False

LOG_FILE = "/dev/null"

FILES_UPLOAD_FOLDER = "/tmp/dci-control-server"

SSO_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApFWXw2HnCmWM9+Ra6PLI
GFrATlXDjDE+8krqzdJF5Em8pywacsHLXjxoQtoSHm79CQwm4PP9VukyBFSzsGe1
Y4hlLv5dK1HfmLDIWz2j8TFAqwt2ghxM/2Br1P0AE55oI1V1rWEjE/2XruUF/67D
eeP/avgvBljh8JPdZmyU7wfsTfOfxVqqteyL9ElTO//Dzh0kww5rFBlhhPd1INmO
0C4jWoqKrJnVEpSCXyeFq3+j95x99xgsRzxqQuoTadbteOytbnqb7kEzYMPkonLd
mplSKaebWKCs71xk60skpJfuXJIkp3W3KfZn9ZsIVE2wZo5Yk/rEy4x9+MT39vB0
2wIDAQAB
-----END PUBLIC KEY-----
"""

CA_CERT = "/tmp/ca.crt"
CA_KEY = "/tmp/ca.key"

SSO_URL = "http://keycloak:8080"
SSO_REALM = "dci-test"
