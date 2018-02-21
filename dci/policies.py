# -*- encoding: utf-8 -*-
#
# Copyright 2017 Red Hat, Inc.
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

ALL = ['USER', 'ADMIN', 'PRODUCT_OWNER', 'FEEDER', 'REMOTECI', 'SUPER_ADMIN']
HUMAN = ['USER', 'ADMIN', 'PRODUCT_OWNER', 'SUPER_ADMIN']
SUPER_ADMIN = ['SUPER_ADMIN']

ROLES = {
    # products
    'create_product': SUPER_ADMIN,
    'update_product': SUPER_ADMIN,
    'get_all_products': ALL,
    'get_product_by_id': ALL,
    'delete_product_by_id': SUPER_ADMIN,
    'get_to_purge_archived_products': SUPER_ADMIN,
    'purge_archived_products': SUPER_ADMIN,
    # identity
    'get_identity': ALL
}
