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

ALL = ['SUPER_ADMIN', 'USER', 'ADMIN', 'PRODUCT_OWNER', 'FEEDER', 'REMOTECI']
HUMAN = ['SUPER_ADMIN', 'USER', 'ADMIN', 'PRODUCT_OWNER']
SUPER_ADMIN = ['SUPER_ADMIN']
SUPER_ADMIN_PO = ['SUPER_ADMIN', 'PRODUCT_OWNER']
SUPER_ADMIN_PO_FEEDER = ['SUPER_ADMIN', 'PRODUCT_OWNER', 'FEEDER']
ADMIN = ['SUPER_ADMIN', 'PRODUCT_OWNER', 'ADMIN']

ROLES = {
    # audits
    'get_logs': ADMIN,
    # components
    'create_components': SUPER_ADMIN_PO_FEEDER,
    'update_components': SUPER_ADMIN_PO_FEEDER,
    'get_latest_components': ALL,
    'get_component_by_id': ALL,
    'delete_component_by_id': SUPER_ADMIN_PO_FEEDER,
    'get_to_purge_archived_components': SUPER_ADMIN,
    'purge_archived_components': SUPER_ADMIN,
    'list_components_files': ALL,
    'list_component_file': ALL,
    'download_component_file': ALL,
    'upload_component_file': SUPER_ADMIN_PO_FEEDER,
    'delete_component_file': SUPER_ADMIN_PO_FEEDER,
    'retrieve_issues_from_component': ALL,
    'attach_issue_to_component': ALL,
    'unattach_issue_from_component': ALL,
    # feeder
    'create_feeders': SUPER_ADMIN_PO,
    'get_all_feeders': SUPER_ADMIN_PO,
    'get_feeder_by_id': SUPER_ADMIN_PO,
    'put_feeder': SUPER_ADMIN_PO,
    'delete_feeder_by_id': SUPER_ADMIN_PO,
    'get_to_purge_archived_feeders': SUPER_ADMIN,
    'purge_archived_feeders': SUPER_ADMIN,
    'put_api_secret_feeder': SUPER_ADMIN_PO,
    # files
    'create_files': ALL,
    'get_all_files': ALL,
    'get_file_by_id': ALL,
    'get_file_content': ALL,
    'delete_file_by_id': ALL,
    'get_to_purge_archived_files': SUPER_ADMIN,
    'purge_archived_files': SUPER_ADMIN,
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
