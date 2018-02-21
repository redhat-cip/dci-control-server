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

EVERYBODY = ['USER', 'ADMIN', 'PRODUCT_OWNER', 'FEEDER', 'REMOTECI', 'SUPER_ADMIN']
HUMAN = ['USER', 'ADMIN', 'PRODUCT_OWNER', 'SUPER_ADMIN']
SUPER_ADMIN = ['SUPER_ADMIN']

ROLES = {
    'create_jobs': HUMAN,
    'schedule_jobs': ['REMOTECI'],
    'upgrade_jobs': HUMAN,
    'get_all_jobs': HUMAN,
    'get_components_from_job': HUMAN,
    'get_jobstates_by_job': HUMAN,
    'get_job_by_id': HUMAN,
    'update_job_by_id': HUMAN,
    'add_file_to_jobs': ['REMOTECI'],
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
}
