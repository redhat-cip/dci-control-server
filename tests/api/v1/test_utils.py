# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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


from dci.api.v1 import utils
from dci.identity import Identity


def test_utils_topic_ids(admin, product_owner, user_admin, user,
                         topic_id, topic_user_id):
    """Ensure that for a given identity, the proper topics are returned."""

    admin_topics = utils.user_topic_ids(admin)
    assert len(admin_topics) == 2

    po_topics = utils.user_topic_ids(product_owner)
    assert len(po_topics) == 1

    user_admin_topics = utils.user_topic_ids(user_admin)
    assert len(user_admin_topics) == 1

    user_topics = utils.user_topic_ids(user)
    assert len(user_topics) == 1
