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

"""Change varchar ID to UUID

Revision ID: 1bb42ff54435
Revises: 6bbbf58ed9de
Create Date: 2017-02-07 09:28:37.493302

"""

# revision identifiers, used by Alembic.
revision = '1bb42ff54435'
down_revision = '6bbbf58ed9de'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    # Drop constraint
    op.drop_constraint('component_files_component_id_fkey', 'component_files')
    op.drop_constraint('components_topic_id_fkey', 'components')
    op.drop_constraint('files_job_id_fkey', 'files')
    op.drop_constraint('files_jobstate_id_fkey', 'files')
    op.drop_constraint('files_team_id_fkey', 'files')
    op.drop_constraint('files_test_id_fkey', 'files')
    op.drop_constraint('jobdefinition_tests_jobdefinition_id_fkey',
                       'jobdefinition_tests')
    op.drop_constraint('jobdefinition_tests_test_id_fkey',
                       'jobdefinition_tests')
    op.drop_constraint('jobdefinitions_topic_id_fkey', 'jobdefinitions')
    op.drop_constraint('jobs_team_id_fkey', 'jobs')
    op.drop_constraint('jobs_jobdefinition_id_fkey', 'jobs')
    op.drop_constraint('jobs_remoteci_id_fkey', 'jobs')
    op.drop_constraint('jobs_previous_job_id_fkey', 'jobs')
    op.drop_constraint('jobs_components_component_id_fkey', 'jobs_components')
    op.drop_constraint('jobs_components_job_id_fkey', 'jobs_components')
    op.drop_constraint('jobs_issues_issue_id_fkey', 'jobs_issues')
    op.drop_constraint('jobs_issues_job_id_fkey', 'jobs_issues')
    op.drop_constraint('jobstates_team_id_fkey', 'jobstates')
    op.drop_constraint('jobstates_job_id_fkey', 'jobstates')
    op.drop_constraint('logs_team_id_fkey', 'logs')
    op.drop_constraint('logs_user_id_fkey', 'logs')
    op.drop_constraint('metas_job_id_fkey', 'metas')
    op.drop_constraint('remoteci_tests_test_id_fkey', 'remoteci_tests')
    op.drop_constraint('remoteci_tests_remoteci_id_fkey', 'remoteci_tests')
    op.drop_constraint('remotecis_team_id_fkey', 'remotecis')
    op.drop_constraint('tests_team_id_fkey', 'tests')
    op.drop_constraint('topic_tests_test_id_fkey', 'topic_tests')
    op.drop_constraint('topic_tests_topic_id_fkey', 'topic_tests')
    op.drop_constraint('topics_next_topic_fkey', 'topics')
    op.drop_constraint('topics_teams_topic_id_fkey', 'topics_teams')
    op.drop_constraint('topics_teams_team_id_fkey', 'topics_teams')
    op.drop_constraint('user_remotecis_user_id_fkey', 'user_remotecis')
    op.drop_constraint('user_remotecis_remoteci_id_fkey', 'user_remotecis')
    op.drop_constraint('users_team_id_fkey', 'users')

    # Change type
    # Table component_files
    op.execute("ALTER TABLE component_files ALTER COLUMN component_id TYPE \
               UUID USING component_id::uuid")
    op.execute("ALTER TABLE component_files ALTER COLUMN id TYPE \
               UUID USING id::uuid")

    # Table components
    op.execute("ALTER TABLE components ALTER COLUMN id TYPE \
               UUID USING id::uuid")
    op.execute("ALTER TABLE components ALTER COLUMN topic_id TYPE \
               UUID USING topic_id::uuid")

    # Table files
    op.execute("ALTER TABLE files ALTER COLUMN id TYPE \
               UUID USING id::uuid")
    op.execute("ALTER TABLE files ALTER COLUMN jobstate_id TYPE \
               UUID USING jobstate_id::uuid")
    op.execute("ALTER TABLE files ALTER COLUMN team_id TYPE \
               UUID USING team_id::uuid")
    op.execute("ALTER TABLE files ALTER COLUMN job_id TYPE \
               UUID USING job_id::uuid")
    op.execute("ALTER TABLE files ALTER COLUMN test_id TYPE \
               UUID USING test_id::uuid")

    # Table issues
    op.execute("ALTER TABLE issues ALTER COLUMN id TYPE \
               UUID USING id::uuid")

    # Table jobdefinition_tests
    op.execute("ALTER TABLE jobdefinition_tests ALTER COLUMN jobdefinition_id \
               TYPE UUID USING jobdefinition_id::uuid")
    op.execute("ALTER TABLE jobdefinition_tests ALTER COLUMN test_id TYPE \
               UUID USING test_id::uuid")

    # Table jobdefinitions
    op.execute("ALTER TABLE jobdefinitions ALTER COLUMN id TYPE \
               UUID USING id::uuid")
    op.execute("ALTER TABLE jobdefinitions ALTER COLUMN topic_id TYPE \
               UUID USING topic_id::uuid")

    # Table jobs
    op.execute("ALTER TABLE jobs ALTER COLUMN id TYPE \
               UUID USING id::uuid")
    op.execute("ALTER TABLE jobs ALTER COLUMN jobdefinition_id TYPE \
               UUID USING jobdefinition_id::uuid")
    op.execute("ALTER TABLE jobs ALTER COLUMN remoteci_id TYPE \
               UUID USING remoteci_id::uuid")
    op.execute("ALTER TABLE jobs ALTER COLUMN team_id TYPE \
               UUID USING team_id::uuid")
    op.execute("ALTER TABLE jobs ALTER COLUMN previous_job_id TYPE \
               UUID USING previous_job_id::uuid")

    # Table jobs_components
    op.execute("ALTER TABLE jobs_components ALTER COLUMN component_id TYPE \
               UUID USING component_id::uuid")
    op.execute("ALTER TABLE jobs_components ALTER COLUMN job_id TYPE \
               UUID USING job_id::uuid")

    # Table jobs_issues
    op.execute("ALTER TABLE jobs_issues ALTER COLUMN job_id TYPE \
               UUID USING job_id::uuid")
    op.execute("ALTER TABLE jobs_issues ALTER COLUMN issue_id TYPE \
               UUID USING issue_id::uuid")

    # Table jobstates
    op.execute("ALTER TABLE jobstates ALTER COLUMN id TYPE \
               UUID USING id::uuid")
    op.execute("ALTER TABLE jobstates ALTER COLUMN job_id TYPE \
               UUID USING job_id::uuid")
    op.execute("ALTER TABLE jobstates ALTER COLUMN team_id TYPE \
               UUID USING team_id::uuid")

    # Table logs
    op.execute("ALTER TABLE logs ALTER COLUMN id TYPE \
               UUID USING id::uuid")
    op.execute("ALTER TABLE logs ALTER COLUMN user_id TYPE \
               UUID USING user_id::uuid")
    op.execute("ALTER TABLE logs ALTER COLUMN team_id TYPE \
               UUID USING team_id::uuid")

    # Table metas
    op.execute("ALTER TABLE metas ALTER COLUMN id TYPE \
               UUID USING id::uuid")
    op.execute("ALTER TABLE metas ALTER COLUMN job_id TYPE \
               UUID USING job_id::uuid")

    # Table remoteci_tests
    op.execute("ALTER TABLE remoteci_tests ALTER COLUMN remoteci_id TYPE \
               UUID USING remoteci_id::uuid")
    op.execute("ALTER TABLE remoteci_tests ALTER COLUMN test_id TYPE \
               UUID USING test_id::uuid")

    # Table remotecis
    op.execute("ALTER TABLE remotecis ALTER COLUMN id TYPE \
               UUID USING id::uuid")
    op.execute("ALTER TABLE remotecis ALTER COLUMN team_id TYPE \
               UUID USING team_id::uuid")

    # Table teams
    op.execute("ALTER TABLE teams ALTER COLUMN id TYPE \
               UUID USING id::uuid")

    # Table tests
    op.execute("ALTER TABLE tests ALTER COLUMN id TYPE \
               UUID USING id::uuid")
    op.execute("ALTER TABLE tests ALTER COLUMN team_id TYPE \
               UUID USING team_id::uuid")

    # Table topic_tests
    op.execute("ALTER TABLE topic_tests ALTER COLUMN topic_id TYPE \
               UUID USING topic_id::uuid")
    op.execute("ALTER TABLE topic_tests ALTER COLUMN test_id TYPE \
               UUID USING test_id::uuid")

    # Table topics
    op.execute("ALTER TABLE topics ALTER COLUMN id TYPE \
               UUID USING id::uuid")
    op.execute("ALTER TABLE topics ALTER COLUMN next_topic TYPE \
               UUID USING next_topic::uuid")

    # Table topics_teams
    op.execute("ALTER TABLE topics_teams ALTER COLUMN topic_id TYPE \
               UUID USING topic_id::uuid")
    op.execute("ALTER TABLE topics_teams ALTER COLUMN team_id TYPE \
               UUID USING team_id::uuid")

    # Table user_remotecis
    op.execute("ALTER TABLE user_remotecis ALTER COLUMN user_id TYPE \
               UUID USING user_id::uuid")
    op.execute("ALTER TABLE user_remotecis ALTER COLUMN remoteci_id TYPE \
               UUID USING remoteci_id::uuid")

    # Table users
    op.execute("ALTER TABLE users ALTER COLUMN id TYPE \
               UUID USING id::uuid")
    op.execute("ALTER TABLE users ALTER COLUMN team_id TYPE \
               UUID USING team_id::uuid")

    # Re-Create constraint
    op.create_foreign_key('component_files_component_id_fkey',
                          'component_files', 'components',
                          ['component_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('components_topic_id_fkey',
                          'components', 'topics',
                          ['topic_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('files_job_id_fkey',
                          'files', 'jobs',
                          ['job_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('files_jobstate_id_fkey',
                          'files', 'jobstates',
                          ['jobstate_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('files_team_id_fkey',
                          'files', 'teams',
                          ['team_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('files_test_id_fkey',
                          'files', 'tests',
                          ['test_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('jobdefinition_tests_jobdefinition_id_fkey',
                          'jobdefinition_tests', 'jobdefinitions',
                          ['jobdefinition_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('jobdefinition_tests_test_id_fkey',
                          'jobdefinition_tests', 'tests',
                          ['test_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('jobdefinitions_topic_id_fkey',
                          'jobdefinitions', 'topics',
                          ['topic_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('jobs_team_id_fkey',
                          'jobs', 'teams',
                          ['team_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('jobs_jobdefinition_id_fkey',
                          'jobs', 'jobdefinitions',
                          ['jobdefinition_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('jobs_remoteci_id_fkey',
                          'jobs', 'remotecis',
                          ['remoteci_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('jobs_previous_job_id_fkey',
                          'jobs', 'jobs',
                          ['previous_job_id'], ['id'])
    op.create_foreign_key('jobs_components_component_id_fkey',
                          'jobs_components', 'components',
                          ['component_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('jobs_components_job_id_fkey',
                          'jobs_components', 'jobs',
                          ['job_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('jobs_issues_issue_id_fkey',
                          'jobs_issues', 'issues',
                          ['issue_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('jobs_issues_job_id_fkey',
                          'jobs_issues', 'jobs',
                          ['job_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('jobstates_team_id_fkey',
                          'jobstates', 'teams',
                          ['team_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('jobstates_job_id_fkey',
                          'jobstates', 'jobs',
                          ['job_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('logs_team_id_fkey',
                          'logs', 'teams',
                          ['team_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('logs_user_id_fkey',
                          'logs', 'users',
                          ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('metas_job_id_fkey',
                          'metas', 'jobs',
                          ['job_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('remoteci_tests_test_id_fkey',
                          'remoteci_tests', 'tests',
                          ['test_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('remoteci_tests_remoteci_id_fkey',
                          'remoteci_tests', 'remotecis',
                          ['remoteci_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('remotecis_team_id_fkey',
                          'remotecis', 'teams',
                          ['team_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('tests_team_id_fkey',
                          'tests', 'teams',
                          ['team_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('topic_tests_test_id_fkey',
                          'topic_tests', 'tests',
                          ['test_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('topic_tests_topic_id_fkey',
                          'topic_tests', 'topics',
                          ['topic_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('topics_next_topic_fkey',
                          'topics', 'topics',
                          ['next_topic'], ['id'])
    op.create_foreign_key('topics_teams_topic_id_fkey',
                          'topics_teams', 'topics',
                          ['topic_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('topics_teams_team_id_fkey',
                          'topics_teams', 'teams',
                          ['team_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('user_remotecis_user_id_fkey',
                          'user_remotecis', 'users',
                          ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('user_remotecis_remoteci_id_fkey',
                          'user_remotecis', 'remotecis',
                          ['remoteci_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('users_team_id_fkey',
                          'users', 'teams',
                          ['team_id'], ['id'], ondelete='CASCADE')


def downgrade():
    pass
