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

"""drop CASCADE ON DELETE

Revision ID: c544e299f743
Revises: 75a91edc23b8
Create Date: 2017-02-03 13:33:08.043994

"""

# revision identifiers, used by Alembic.
revision = 'c544e299f743'
down_revision = '75a91edc23b8'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    fk = [
        ('components', 'topic_id', 'topics'),
        ('topics_teams', 'team_id', 'teams'),
        ('topics_teams', 'topic_id', 'topics'),
        ('tests', 'team_id', 'teams'),
        ('jobdefinitions', 'topic_id', 'topics'),
        ('jobdefinition_tests', 'jobdefinition_id', 'jobdefinitions'),
        ('jobdefinition_tests', 'test_id', 'tests'),
        ('remoteci_tests', 'remoteci_id', 'remotecis'),
        ('remoteci_tests', 'test_id', 'tests'),
        ('topic_tests', 'topic_id', 'topics'),
        ('topic_tests', 'test_id', 'tests'),
        ('remotecis', 'team_id', 'teams'),
        ('jobs', 'jobdefinition_id', 'jobdefinitions'),
        ('jobs', 'remoteci_id', 'remotecis'),
        ('jobs', 'team_id', 'teams'),
        ('metas', 'job_id', 'jobs'),
        ('jobs_components', 'job_id', 'jobs'),
        ('jobs_components', 'component_id', 'components'),
        ('jobs_issues', 'job_id', 'jobs'),
        ('jobs_issues', 'issue_id', 'issues'),
        ('jobstates', 'job_id', 'jobs'),
        ('jobstates', 'team_id', 'teams'),
        ('files', 'jobstate_id', 'jobstates'),
        ('files', 'team_id', 'teams'),
        ('files', 'job_id', 'jobs'),
        ('component_files', 'component_id', 'components'),
        ('users', 'team_id', 'teams'),
        ('user_remotecis', 'user_id', 'users'),
        ('user_remotecis', 'remoteci_id', 'remotecis'),
        ('logs', 'user_id', 'users'),
        ('logs', 'team_id', 'teams'),
    ]

    for i in fk:
        (source_t, c, target_t) = i
        fk_name = '%s_%s_fkey' % (source_t, c)
        op.drop_constraint(fk_name, source_t)
        op.create_foreign_key(
            fk_name, source_t,
            target_t, [c], ['id'])


def downgrade():
    pass
