# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
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

from dci.api.v1 import utils as v1_utils
from dci.common import exceptions as dci_exc
from dci.db import models

import flask
from sqlalchemy import sql


def is_teams_associated_to_product(team_ids, product_id):
    q_get_product_team = sql.select([models.JOIN_PRODUCTS_TEAMS]).where(
        models.JOIN_PRODUCTS_TEAMS.c.team_id.in_(team_ids)
    )
    result = flask.g.db_conn.execute(q_get_product_team)
    return result.rowcount > 0


def is_teams_associated_to_topic(team_ids, topic_id):
    q_get_topic__team = sql.select([models.JOINS_TOPICS_TEAMS]).where(
        models.JOINS_TOPICS_TEAMS.c.team_id.in_(team_ids)
    )
    result = flask.g.db_conn.execute(q_get_topic__team)
    return result.rowcount > 0


def has_access_to_topic(user, topic):
    """If the topic has it's export_control set to True then all the teams
    associated to the product can access to the topic's resources. If the
    export control is False check if user's teams associated to the topic.

    :param user:
    :param topic:
    :return: True if has_access_to_topic, False otherwise
    """
    if topic["export_control"] is True:
        product = v1_utils.verify_existence_and_get(
            topic["product_id"], models.PRODUCTS
        )
        return is_teams_associated_to_product(user.teams_ids, product["id"])
    return is_teams_associated_to_topic(user.teams_ids, topic["id"])


def verify_access_to_topic(user, topic):
    """Verify that the user can access to a topic, raise an unauthorized
       exception if not."""
    if (
        user.is_not_super_admin()
        and user.is_not_read_only_user()
        and user.is_not_epm()
        and user.is_not_feeder()
        and not has_access_to_topic(user, topic)
    ):
        raise dci_exc.Unauthorized()
