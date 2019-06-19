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
from dci.db import models


def _check(user, topic):
    """If the topic has it's export_control set to True then all the teams
    associated to the product can access to the topic's resources.

    :param user:
    :param topic:
    :return: True if check is ok, False otherwise
    """
    # if export_control then check the team is associated to the product
    if topic['export_control']:
        product = v1_utils.verify_existence_and_get(topic['product_id'],
                                                    models.PRODUCTS)
        v1_utils.verify_team_in_product(user, product['id'])
        return True
    return False


def verify_access_to_topic(user, topic):
    if (user.is_not_super_admin() and user.is_not_read_only_user()
        and user.is_not_epm()):
        if not _check(user, topic):
            # If topic has it's export_control set to False then only teams
            # associated to the topic can access to the topic's resources.
            v1_utils.verify_team_in_topic(user, topic['id'])
