#
# Copyright (C) 2022 Red Hat, Inc
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

"""Initial migration

Revision ID: a918b053c43a
Revises:
Create Date: 2022-06-29 17:07:13.603539

"""

# revision identifiers, used by Alembic.
revision = "a918b053c43a"
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.types.json import JSONType


def upgrade():
    op.create_table(
        "counter",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=True),
        sa.Column("etag", sa.String(length=40), nullable=False),
        sa.PrimaryKeyConstraint("name"),
    )
    op.create_table(
        "jobs_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("success", "failure", "error", name="final_statuses"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("jobs_events_job_id_idx", "jobs_events", ["job_id"], unique=False)
    op.create_table(
        "logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("logs_user_id_idx", "logs", ["user_id"], unique=False)
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("etag", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "state",
            sa.Enum("active", "inactive", "archived", name="states"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("label"),
    )
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("etag", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=255), nullable=True),
        sa.Column(
            "state",
            sa.Enum("active", "inactive", "archived", name="states"),
            nullable=True,
        ),
        sa.Column("external", sa.BOOLEAN(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="teams_name_key"),
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("etag", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sso_username", sa.String(length=255), nullable=True),
        sa.Column("fullname", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password", sa.Text(), nullable=True),
        sa.Column("timezone", sa.String(length=255), nullable=False),
        sa.Column(
            "state",
            sa.Enum("active", "inactive", "archived", name="states"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("sso_username"),
    )
    op.create_table(
        "feeders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("etag", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("data", JSONType(), nullable=True),
        sa.Column("api_secret", sa.String(length=64), nullable=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "state",
            sa.Enum("active", "inactive", "archived", name="states"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "team_id", name="feeders_name_team_id_key"),
    )
    op.create_index("feeders_team_id_idx", "feeders", ["team_id"], unique=False)
    op.create_table(
        "products_teams",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("product_id", "team_id"),
    )
    op.create_table(
        "remotecis",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("etag", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("data", JSONType(), nullable=True),
        sa.Column("api_secret", sa.String(length=64), nullable=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("public", sa.BOOLEAN(), nullable=True),
        sa.Column("cert_fp", sa.String(length=255), nullable=True),
        sa.Column(
            "state",
            sa.Enum("active", "inactive", "archived", name="states"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "team_id", name="remotecis_name_team_id_key"),
    )
    op.create_index("remotecis_team_id_idx", "remotecis", ["team_id"], unique=False)
    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("etag", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "component_types", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "component_types_optional",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("next_topic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "export_control", sa.BOOLEAN(), server_default="false", nullable=False
        ),
        sa.Column(
            "state",
            sa.Enum("active", "inactive", "archived", name="states"),
            nullable=True,
        ),
        sa.Column("data", JSONType(), nullable=True),
        sa.ForeignKeyConstraint(
            ["next_topic_id"],
            ["topics.id"],
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        "topics_next_topic_id_idx", "topics", ["next_topic_id"], unique=False
    )
    op.create_index("topics_product_id_idx", "topics", ["product_id"], unique=False)
    op.create_table(
        "users_teams",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "team_id", name="users_teams_key"),
    )
    op.create_table(
        "components",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("etag", sa.String(length=40), nullable=False),
        sa.Column("released_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=255), nullable=False),
        sa.Column("canonical_project_name", sa.String(), nullable=True),
        sa.Column("data", JSONType(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "state",
            sa.Enum("active", "inactive", "archived", name="states"),
            nullable=True,
        ),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "name",
            "topic_id",
            "type",
            "team_id",
            name="name_topic_id_type_team_id_unique",
        ),
    )
    op.create_index(
        "active_components_name_topic_id_team_id_null_key",
        "components",
        ["name", "topic_id", "type"],
        unique=True,
        postgresql_where=sa.text(
            "components.state = 'active' AND components.team_id is NULL"
        ),
    )
    op.create_index("components_topic_id_idx", "components", ["topic_id"], unique=False)
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("etag", sa.String(length=40), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("status_reason", sa.Text(), nullable=True),
        sa.Column("configuration", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "new",
                "pre-run",
                "running",
                "post-run",
                "success",
                "failure",
                "killed",
                "error",
                name="statuses",
            ),
            nullable=True,
        ),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("remoteci_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("client_version", sa.String(length=255), nullable=True),
        sa.Column("previous_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "update_previous_job_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column(
            "state",
            sa.Enum("active", "inactive", "archived", name="states"),
            nullable=True,
        ),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("data", JSONType(), nullable=True),
        sa.ForeignKeyConstraint(
            ["previous_job_id"],
            ["jobs.id"],
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["remoteci_id"], ["remotecis.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["update_previous_job_id"],
            ["jobs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "jobs_previous_job_id_idx", "jobs", ["previous_job_id"], unique=False
    )
    op.create_index("jobs_product_id_idx", "jobs", ["product_id"], unique=False)
    op.create_index("jobs_remoteci_id_idx", "jobs", ["remoteci_id"], unique=False)
    op.create_index("jobs_team_id_idx", "jobs", ["team_id"], unique=False)
    op.create_index("jobs_topic_id_idx", "jobs", ["topic_id"], unique=False)
    op.create_index(
        "jobs_update_previous_job_id_idx",
        "jobs",
        ["update_previous_job_id"],
        unique=False,
    )
    op.create_table(
        "topics_teams",
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("topic_id", "team_id"),
    )
    op.create_table(
        "user_remotecis",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("remoteci_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["remoteci_id"], ["remotecis.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "remoteci_id"),
    )
    op.create_table(
        "users_topics",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "topic_id"),
    )
    op.create_table(
        "component_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("etag", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("mime", sa.String(), nullable=True),
        sa.Column("md5", sa.String(length=32), nullable=True),
        sa.Column("size", sa.BIGINT(), nullable=True),
        sa.Column("component_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "state",
            sa.Enum("active", "inactive", "archived", name="states"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["component_id"], ["components.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "component_files_component_id_idx",
        "component_files",
        ["component_id"],
        unique=False,
    )
    op.create_table(
        "jobs_components",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("component_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["component_id"], ["components.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("job_id", "component_id"),
    )
    op.create_table(
        "jobstates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "new",
                "pre-run",
                "running",
                "post-run",
                "success",
                "failure",
                "killed",
                "error",
                name="statuses",
            ),
            nullable=False,
        ),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("jobstates_job_id_idx", "jobstates", ["job_id"], unique=False)
    op.create_table(
        "files",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("etag", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("mime", sa.String(), nullable=True),
        sa.Column("md5", sa.String(length=32), nullable=True),
        sa.Column("size", sa.BIGINT(), nullable=True),
        sa.Column(
            "state",
            sa.Enum("active", "inactive", "archived", name="states"),
            nullable=True,
        ),
        sa.Column("jobstate_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["jobstate_id"], ["jobstates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("files_job_id_idx", "files", ["job_id"], unique=False)
    op.create_index("files_jobstate_id_idx", "files", ["jobstate_id"], unique=False)
    op.create_index("files_team_id_idx", "files", ["team_id"], unique=False)
    op.create_table(
        "tests_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("total", sa.Integer(), nullable=True),
        sa.Column("success", sa.Integer(), nullable=True),
        sa.Column("skips", sa.Integer(), nullable=True),
        sa.Column("failures", sa.Integer(), nullable=True),
        sa.Column("regressions", sa.Integer(), nullable=True),
        sa.Column("successfixes", sa.Integer(), nullable=True),
        sa.Column("errors", sa.Integer(), nullable=True),
        sa.Column("time", sa.Integer(), nullable=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "tests_results_file_id_idx", "tests_results", ["file_id"], unique=False
    )
    op.create_index(
        "tests_results_job_id_idx", "tests_results", ["job_id"], unique=False
    )


def downgrade():
    op.drop_index("tests_results_job_id_idx", table_name="tests_results")
    op.drop_index("tests_results_file_id_idx", table_name="tests_results")
    op.drop_table("tests_results")
    op.drop_index("files_team_id_idx", table_name="files")
    op.drop_index("files_jobstate_id_idx", table_name="files")
    op.drop_index("files_job_id_idx", table_name="files")
    op.drop_table("files")
    op.drop_index("jobstates_job_id_idx", table_name="jobstates")
    op.drop_table("jobstates")
    op.drop_table("jobs_components")
    op.drop_index("component_files_component_id_idx", table_name="component_files")
    op.drop_table("component_files")
    op.drop_table("users_topics")
    op.drop_table("user_remotecis")
    op.drop_table("topics_teams")
    op.drop_index("jobs_update_previous_job_id_idx", table_name="jobs")
    op.drop_index("jobs_topic_id_idx", table_name="jobs")
    op.drop_index("jobs_team_id_idx", table_name="jobs")
    op.drop_index("jobs_remoteci_id_idx", table_name="jobs")
    op.drop_index("jobs_product_id_idx", table_name="jobs")
    op.drop_index("jobs_previous_job_id_idx", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("components_topic_id_idx", table_name="components")
    op.drop_index(
        "active_components_name_topic_id_team_id_null_key", table_name="components"
    )
    op.drop_table("components")
    op.drop_table("users_teams")
    op.drop_index("topics_product_id_idx", table_name="topics")
    op.drop_index("topics_next_topic_id_idx", table_name="topics")
    op.drop_table("topics")
    op.drop_index("remotecis_team_id_idx", table_name="remotecis")
    op.drop_table("remotecis")
    op.drop_table("products_teams")
    op.drop_index("feeders_team_id_idx", table_name="feeders")
    op.drop_table("feeders")
    op.drop_table("users")
    op.drop_table("teams")
    op.drop_table("products")
    op.drop_index("logs_user_id_idx", table_name="logs")
    op.drop_table("logs")
    op.drop_index("jobs_events_job_id_idx", table_name="jobs_events")
    op.drop_table("jobs_events")
    op.drop_table("counter")
