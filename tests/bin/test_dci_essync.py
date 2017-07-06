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


from tests import utils


def test_add_files(user, jobstate_user_id, db_clean, reset_files_event_pk,
                   es_clean, es_engine):
    for i in range(5):
        f_id = utils.post_file(user, jobstate_user_id,
                        utils.FileDesc('kikoolol', 'content'))

    status = utils.run_bin('dci-essync')
    status.communicate()
    assert status.returncode == 0
    assert es_engine.get_last_sequence(doc_type='logs') == 5
    # 5 /logs  + 1 /logs/sequence = 6
    with open('/tmp/kikoo', 'w') as f:
        f.write(str(es_engine.get_all_logs()))
    assert es_engine.get_all_logs()['hits'] == 6


def test_deleted_files(user, jobstate_user_id, db_clean, reset_files_event_pk,
                       es_clean, es_engine):
    # create 5 files create events
    files_ids = []
    for i in range(5):
        fc_id = utils.post_file(user, jobstate_user_id,
                             utils.FileDesc('kikoolol', 'content'))
        files_ids.append(fc_id)

    # create 5 files delete events
    for f_id in files_ids:
        user.delete('/api/v1/files/%s' % f_id)

    status = utils.run_bin('dci-essync')
    status.communicate()
    assert status.returncode == 0
    assert es_engine.get_last_sequence(doc_type='logs') == 10

