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
import flask
from flask import json
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models


# associate column names with the corresponding SA Column object
_TABLE = models.NOTIFICATIONS
_VALID_EMBED = embeds.notifications()
_USERS_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


@api.route('/notifications', methods=['POST'])
@decorators.login_required
def create_notifcation(user):
    # Remoteci ID in data


@api.route('/notifications', methods=['GET'])
@decorators.login_required
def get_all_notifications(user):
    # List all your notifications


@api.route('/notifications/<uuid:notif_id>', methods=['GET'])
@decorators.login_required
def get_notif_by_id(user, notif_id):
    # Get only the selected notif


@api.route('/notifications/<uuid:notif_id>', methods=['PUT'])
@decorators.login_required
def put_notif(user, notif_id):
    # Modify notif (is this really necessary ?)


@api.route('/notifications/<uuid:notif_id>', methods=['DELETE'])
@decorators.login_required
def delete_notif_by_id(user, user_id):
    # delete the specific notif
