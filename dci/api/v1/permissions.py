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

from dci.api.v1 import base
from dci.common import exceptions as dci_exc
from dci.db import models2

import flask
from sqlalchemy import sql


def is_teams_associated_to_product(team_ids, product_id):
    q_get_product_team = sql.select([models2.JOIN_PRODUCTS_TEAMS]).where(
        sql.and_(
            models2.JOIN_PRODUCTS_TEAMS.c.team_id.in_(team_ids),
            models2.JOIN_PRODUCTS_TEAMS.c.product_id == product_id,
        )
    )
    result = flask.g.db_conn.execute(q_get_product_team)
    return result.rowcount > 0


def has_access_to_topic(user, topic):
    """If the topic has it's export_control set to True then all the teams
    associated to the product can access to the topic's resources. If the
    export control is False check if user's teams has pre release access.

    :param user:
    :param topic:
    :return: True if has_access_to_topic, False otherwise
    """
    product = base.get_resource_orm(models2.Product, topic.product_id)
    has_access_to_the_product = is_teams_associated_to_product(
        user.teams_ids, product.id
    )
    if topic.export_control is True:
        return has_access_to_the_product
    return has_access_to_the_product and user.has_pre_release_access()


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


def get_user_product_ids(user):
    query = flask.g.session.query(models2.Product).filter(
        models2.Product.state != "archived"
    )
    query = query.join(
        models2.JOIN_PRODUCTS_TEAMS,
        sql.and_(
            models2.JOIN_PRODUCTS_TEAMS.c.product_id == models2.Product.id,
            models2.JOIN_PRODUCTS_TEAMS.c.team_id.in_(user.teams_ids),
        ),
    )
    return [product.id for product in query.all()]


def get_user_topic_ids(user):
    product_ids = get_user_product_ids(user)
    filters = [models2.Topic.product_id.in_(product_ids)]
    if user.has_not_pre_release_access():
        filters.append(models2.Topic.export_control == True)  # noqa
    return [t.id for t in base.get_resources_orm(models2.Topic, filters)]


def get_components_access_teams_ids(teams_ids):
    """A team can allow another team to see its components.
    This method returns the list of teams ids that allowed teams_ids to see theirs components.
    """
    components_access_teams_ids = []
    JTCA = models2.JOIN_TEAMS_COMPONENTS_ACCESS
    for team_id in teams_ids:
        query = flask.g.session.query(JTCA)
        query = query.filter(JTCA.c.team_id == team_id)
        teams_components_access = query.all()
        if teams_components_access:
            for tca in teams_components_access:
                components_access_teams_ids.append(tca.access_team_id)
    return components_access_teams_ids


def verify_access_to_component(user, component):
    component_team_id = component.team_id
    if component_team_id is not None:
        if user.is_not_in_team(component_team_id):
            components_access_teams_ids = get_components_access_teams_ids(
                user.teams_ids
            )
            if component_team_id not in components_access_teams_ids:
                raise dci_exc.Unauthorized()
    else:
        topic = base.get_resource_orm(models2.Topic, component.topic_id)
        verify_access_to_topic(user, topic)


def can_delete_component(user, component):
    component_team_id = component.team_id
    if component_team_id is not None:
        if user.is_not_in_team(component_team_id):
            dci_exc.Unauthorized()
    elif user.is_not_super_admin() and user.is_not_feeder() and user.is_not_epm():
        raise dci_exc.Unauthorized()
