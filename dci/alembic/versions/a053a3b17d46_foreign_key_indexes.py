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

"""Foreign key indexes

Revision ID: a053a3b17d46
Revises: 75a91edc23b8
Create Date: 2017-02-07 20:16:40.545916

"""

# revision identifiers, used by Alembic.
revision = 'a053a3b17d46'
down_revision = '75a91edc23b8'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    # Table component_files
    op.create_index('component_files_component_id_idx',
                    'component_files', ['component_id'])

    # Table components
    op.create_index('components_topic_id_idx', 'components', ['topic_id'])

    # Table files
    op.create_index('files_job_id_idx', 'files', ['job_id'])
    op.create_index('files_jobstate_id_idx', 'files', ['jobstate_id'])
    op.create_index('files_team_id_idx', 'files', ['team_id'])

    # Table jobdefinitions
    op.create_index('jobdefinitions_topic_id_idx',
                    'jobdefinitions', ['topic_id'])

    # Table jobs
    op.create_index('jobs_jobdefinition_id_idx', 'jobs', ['jobdefinition_id'])
    op.create_index('jobs_previous_job_id_idx', 'jobs', ['previous_job_id'])
    op.create_index('jobs_remoteci_id_idx', 'jobs', ['remoteci_id'])
    op.create_index('jobs_team_id_idx', 'jobs', ['team_id'])

    # Table jobstates
    op.create_index('jobstates_team_id_idx', 'jobstates', ['job_id'])
    op.create_index('jobstatesteam_id_idx', 'jobstates', ['team_id'])

    # Table logs
    op.create_index('logs_team_id_idx', 'logs', ['team_id'])
    op.create_index('logs_user_id_idx', 'logs', ['user_id'])

    # Table metas
    op.create_index('metas_job_id_idx', 'metas', ['job_id'])

    # Table remotecis
    op.create_index('remotecis_team_id_idx', 'remotecis', ['team_id'])

    # Table tests
    op.create_index('tests_team_id_idx', 'tests', ['team_id'])

    # Table topics
    op.create_index('topics_next_topic_idx', 'topics', ['next_topic'])

    # Table users
    op.create_index('users_team_id_idx', 'users', ['team_id'])


def downgrade():
    # Table component_files
    op.drop_index('component_files_component_id_idx')

    # Table components
    op.drop_index('components_topic_id_idx')

    # Table files
    op.drop_index('files_job_id_idx')
    op.drop_index('files_jobstate_id_idx')
    op.drop_index('files_team_id_idx')

    # Table jobdefinitions
    op.drop_index('jobdefinitions_topic_id_idx')

    # Table jobs
    op.drop_index('jobs_jobdefinition_id_idx')
    op.drop_index('jobs_previous_job_id_idx')
    op.drop_index('jobs_remoteci_id_idx')
    op.drop_index('jobs_team_id_idx')

    # Table jobstates
    op.drop_index('jobstates_team_id_idx')
    op.drop_index('jobstatesteam_id_idx')

    # Table logs
    op.drop_index('logs_team_id_idx')
    op.drop_index('logs_user_id_idx')

    # Table metas
    op.drop_index('metas_job_id_idx')

    # Table remotecis
    op.drop_index('remotecis_team_id_idx')

    # Table tests
    op.drop_index('tests_team_id_idx')

    # Table template
    op.drop_index('topics_next_topic_idx')

    # Table users
    op.drop_index('users_team_id_idx')
