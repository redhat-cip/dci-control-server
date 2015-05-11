# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
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

from server.db.models import File
from server.db.models import Job
from server.db.models import Notification
from server.db.models import Remoteci
from server.db.models import session
from server.db.models import TestVersion


session.query(Job).delete()
session.query(File).delete()
session.query(Notification).delete()
session.query(Remoteci).delete()
session.query(TestVersion).delete()
