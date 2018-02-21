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
REMOTECI = ['SUPER_ADMIN', 'REMOTECI']

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
    # files events
    'get_files_events_from_sequence': SUPER_ADMIN,
    'purge_files_events_from_sequence': SUPER_ADMIN,
    # fingerprint
    'create_fingerprint': HUMAN,
    'get_all_fingerprints': HUMAN,
    'get_fingerprint_by_id': HUMAN,
    'modify_fingerprint': HUMAN,
    'delete_fingerprint_by_id': HUMAN,
    'get_to_purge_archived_fingerprint': SUPER_ADMIN,
    'purge_fingerprint': SUPER_ADMIN,
    # global status
    'get_global_status': SUPER_ADMIN_PO,
    # identity
    'get_identity': ALL,
    # jobs
    'create_jobs': HUMAN,
    'schedule_jobs': REMOTECI,
    'upgrade_jobs': REMOTECI,
    'get_all_jobs': HUMAN,
    'get_components_from_job': HUMAN,
    'get_jobstates_by_job': HUMAN,
    'get_job_by_id': HUMAN,
    'update_job_by_id': HUMAN,
    'add_file_to_jobs': REMOTECI,
    'retrieve_issues_from_job': HUMAN,
    'attach_issue_to_jobs': HUMAN,
    'unattach_issue_from_job': HUMAN,
    'get_all_files_from_jobs': HUMAN,
    'get_all_results_from_jobs': HUMAN,
    'delete_job_by_id': HUMAN,
    'associate_meta': HUMAN,
    'get_meta_by_id': HUMAN,
    'get_all_metas': HUMAN,
    'put_meta': HUMAN,
    'delete_meta': HUMAN,
    'get_to_purge_archived_jobs': SUPER_ADMIN,
    'purge_archived_jobs': SUPER_ADMIN,
    # job states
    'create_jobstates': REMOTECI,
    'get_all_jobstates': REMOTECI,
    'get_jobstate_by_id': REMOTECI,
    'delete_jobstate_by_id': REMOTECI,
    # permissions
    'create_permission':SUPER_ADMIN,
    'update_permission':SUPER_ADMIN,
    'get_all_permissions':HUMAN,
    'get_permission_by_id':HUMAN,
    'delete_permission_by_id':SUPER_ADMIN,
    'get_to_purge_archived_permissions':SUPER_ADMIN,
    'purge_archived_permissions':SUPER_ADMIN,
    # products
    'create_product': SUPER_ADMIN,
    'update_product': SUPER_ADMIN,
    'get_all_products': ALL,
    'get_product_by_id': ALL,
    'delete_product_by_id': SUPER_ADMIN,
    'get_to_purge_archived_products': SUPER_ADMIN,
    'purge_archived_products': SUPER_ADMIN,
    # remoteci
    'create_remotecis':ALL,
    'get_all_remotecis':ALL,
    'get_remoteci_by_id':ALL,
    'put_remoteci':ALL,
    'delete_remoteci_by_id':ALL,
    'get_remoteci_data':ALL,
    'add_user_to_remoteci':ALL,
    'get_all_users_from_remotecis':ALL,
    'delete_user_from_remoteci':ALL,
    'add_test_to_remoteci':ALL,
    'get_all_tests_from_remotecis':ALL,
    'delete_test_from_remoteci':ALL,
    'get_to_purge_archived_remotecis':ALL,
    'purge_archived_remotecis':ALL,
    'put_api_secret':ALL,
    'create_configuration':ADMIN,
    'get_all_configurations':ALL,
    'get_configuration_by_id':ALL,
    'delete_configuration_by_id':ADMIN,
    'get_to_purge_archived_rconfigurations':SUPER_ADMIN,
    'purge_archived_rconfigurations':SUPER_ADMIN,
    #roles
    'create_roles':SUPER_ADMIN,
    'update_role':SUPER_ADMIN,
    'get_all_roles':HUMAN,
    'get_role_by_id':HUMAN,
    'delete_role_by_id':SUPER_ADMIN,
    'get_to_purge_archived_roles':SUPER_ADMIN,
    'purge_archived_roles':SUPER_ADMIN,
    'add_permission_to_role':SUPER_ADMIN,
    'delete_permission_from_role':SUPER_ADMIN,
    # search
    'search': HUMAN,
    'get_search_by_id': HUMAN,
    # teams
    'create_teams':SUPER_ADMIN_PO,
    'get_all_teams':HUMAN,
    'get_team_by_id':HUMAN,
    'get_remotecis_by_team':HUMAN,
    'get_tests_by_team':HUMAN,
    'put_team':ADMIN,
    'delete_team_by_id':SUPER_ADMIN_PO,
    'get_to_purge_archived_teams':SUPER_ADMIN,
    'purge_archived_teams':SUPER_ADMIN,
}