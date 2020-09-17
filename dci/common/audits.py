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

import datetime
import flask
from functools import wraps

from dci.db import models

_TABLE = models.LOGS


def log_action(user_id, action):
    values = {
        "user_id": user_id,
        "action": action,
        "created_at": datetime.datetime.utcnow().isoformat(),
    }
    flask.g.db_conn.execute(_TABLE.insert().values(**values))


def log(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = args[0]
        log_action(user.id, f.__name__)
        return f(*args, **kwargs)

    return decorated
