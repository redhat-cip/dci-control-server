# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2023 Red Hat, Inc
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

import flask
from flask import json
import logging
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql
import sqlalchemy.orm as sa_orm

from datetime import datetime, timedelta

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import components
from dci.api.v1 import utils as v1_utils
from dci.api.v1 import jobs_events
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    check_json_is_valid,
    clean_json_with_schema,
    create_job_schema,
    update_job_schema,
    upgrade_job_schema,
    schedule_job_schema,
    add_component_schema,
    check_and_get_args,
)
from dci.common import utils
from dci.db import declarative
from dci.db import models2

from dci.api.v1 import files
from dci.api.v1 import export_control
from dci.api.v1 import jobstates


logger = logging.getLogger(__name__)


def get_utc_now():
    return datetime.utcnow()


@api.route("/jobs", methods=["POST"])
@decorators.login_required
def create_jobs(user):
    values = flask.request.json
    check_json_is_valid(create_job_schema, values)
    values.update(v1_utils.common_values_dict())

    components_ids = values.pop("components")

    return internal_create_jobs(user, values, components_ids)


@api.route("/jobs/schedule", methods=["POST"])
@decorators.login_required
def schedule_jobs(user):
    """Dispatch jobs to remotecis.

    The remoteci can use this method to request a new job.

    Before a job is dispatched, the server will flag as 'killed' all the
    running jobs that were associated with the remoteci. This is because they
    will never be finished.
    """
    values = flask.request.json
    check_json_is_valid(schedule_job_schema, values)

    return internal_create_jobs(user, values)


def internal_create_jobs(user, values, components_ids=None):
    if user.is_not_remoteci():
        raise dci_exc.DCIException("Only remoteci can create job")

    # check remoteci
    remoteci = base.get_resource_orm(models2.Remoteci, user.id)
    if remoteci.state != "active":
        message = 'RemoteCI "%s" is disabled.' % remoteci.id
        raise dci_exc.DCIException(message, status_code=412)

    # check primary topic
    topic_id = values.get("topic_id")
    topic = base.get_resource_orm(models2.Topic, topic_id)
    product_id = topic.product_id
    if topic.state != "active":
        msg = "Topic %s:%s not active." % (topic_id, topic.name)
        raise dci_exc.DCIException(msg, status_code=412)
    export_control.verify_access_to_topic(user, topic)

    previous_job_id = values.get("previous_job_id")
    if previous_job_id:
        base.get_resource_orm(models2.Job, previous_job_id)

    values.update(
        {
            "id": utils.gen_uuid(),
            "created_at": get_utc_now().isoformat(),
            "updated_at": get_utc_now().isoformat(),
            "etag": utils.gen_etag(),
            "status": "new",
            "remoteci_id": user.id,
            "team_id": user.teams_ids[0],
            "product_id": topic.product_id,
            "duration": 0,
            "user_agent": flask.request.environ.get("HTTP_USER_AGENT"),
            "client_version": flask.request.environ.get("HTTP_CLIENT_VERSION"),
            "previous_job_id": previous_job_id,
        }
    )
    components_access_teams_ids = components.get_components_access_teams_ids(
        user.teams_ids
    )
    # schedule
    if components_ids is None:
        kill_existing_jobs(remoteci.id)

        components_ids = values.pop("components_ids")
        for c_id in components_ids:
            c = base.get_resource_orm(models2.Component, c_id)
            if (
                c.team_id is not None
                and c.team_id not in user.teams_ids
                and c.team_id not in components_access_teams_ids
            ):
                raise dci_exc.Unauthorized()

        values = _build_job(product_id, topic_id, remoteci, components_ids, values)
    # create
    else:
        base.create_resource_orm(models2.Job, values)
        j = base.get_resource_orm(models2.Job, values["id"])
        for cmpt_id in components_ids:
            c = base.get_resource_orm(models2.Component, cmpt_id)
            if (
                c.team_id is not None
                and c.team_id not in user.teams_ids
                and c.team_id not in components_access_teams_ids
            ):
                raise dci_exc.Unauthorized()

        for cmpt_id in components_ids:
            c = base.get_resource_orm(models2.Component, cmpt_id)
            try:
                j.components.append(c)
                flask.g.session.add(j)
                flask.g.session.commit()
            except sa_exc.IntegrityError as e:
                logger.error(str(e))
                flask.g.session.rollback()
                raise dci_exc.DCIException(
                    message="conflict when adding component %s" % c.name,
                    status_code=409,
                )

    return flask.Response(
        json.dumps({"job": values}),
        201,
        headers={"ETag": values["etag"]},
        content_type="application/json",
    )


def _build_job(product_id, topic_id, remoteci, components_ids, values):
    # get components of topic
    p_component_types = components.get_component_types_from_topic(topic_id)
    p_schedule_components_ids = components.get_schedule_components_ids(
        topic_id, p_component_types, components_ids
    )

    values.update(
        {"product_id": product_id, "topic_id": topic_id, "team_id": remoteci.team_id}
    )
    base.create_resource_orm(models2.Job, values)
    j = base.get_resource_orm(models2.Job, values["id"])

    for sci in p_schedule_components_ids:
        c = base.get_resource_orm(models2.Component, sci)
        try:
            j.components.append(c)
            flask.g.session.add(j)
            flask.g.session.commit()
        except sa_exc.IntegrityError as e:
            logger.error(str(e))
            flask.g.session.rollback()
            raise dci_exc.DCIException(
                message="conflict when adding component %s" % c.name, status_code=409
            )

    return values


def kill_existing_jobs(remoteci_id, session=None):
    try:
        session = session or flask.g.session
        yesterday = datetime.now() - timedelta(hours=24)
        query = flask.g.session.query(models2.Job)
        query = query.filter(models2.Job.remoteci_id == remoteci_id)
        query = query.filter(
            models2.Job.status.in_(("new", "pre-run", "running", "post-run"))
        )
        query = query.filter(models2.Job.created_at < yesterday)
        query = query.update({"status": "killed"}, synchronize_session=False)
        session.commit()
    except Exception as e:
        flask.g.session.rollback()
        logger.error("error while killing existing jobs: %s" % str(e))
        raise dci_exc.DCIException(
            message="error while killing existing jobs", status_code=409
        )


@api.route("/jobs/<uuid:job_id>/update", methods=["POST"])
@decorators.login_required
def create_new_update_job_from_an_existing_job(user, job_id):
    """Create a new job in the same topic as the job_id provided and
    associate the latest components of this topic."""
    previous_job_id = job_id
    values = {
        "id": utils.gen_uuid(),
        "created_at": get_utc_now().isoformat(),
        "updated_at": get_utc_now().isoformat(),
        "etag": utils.gen_etag(),
        "previous_job_id": previous_job_id,
        "update_previous_job_id": previous_job_id,
        "status": "new",
    }

    previous_job = base.get_resource_orm(models2.Job, previous_job_id)

    if user.is_not_in_team(previous_job.team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    # get the remoteci
    remoteci_id = str(previous_job.remoteci_id)
    remoteci = base.get_resource_orm(models2.Remoteci, remoteci_id)
    values.update({"remoteci_id": remoteci_id})

    # get the associated topic
    topic_id = str(previous_job.topic_id)
    topic = base.get_resource_orm(models2.Topic, topic_id)
    product_id = topic.product_id

    values.update(
        {
            "user_agent": flask.request.environ.get("HTTP_USER_AGENT"),
            "client_version": flask.request.environ.get("HTTP_CLIENT_VERSION"),
        }
    )

    values = _build_job(product_id, topic_id, remoteci, [], values)

    return flask.Response(
        json.dumps({"job": values}),
        201,
        headers={"ETag": values["etag"]},
        content_type="application/json",
    )


@api.route("/jobs/upgrade", methods=["POST"])
@decorators.login_required
def create_new_upgrade_job_from_an_existing_job(user):
    """Create a new job in the 'next topic' of the topic of
    the provided job_id."""
    values = flask.request.json
    check_json_is_valid(upgrade_job_schema, values)
    previous_job_id = values.pop("job_id")
    values.update(
        {
            "id": utils.gen_uuid(),
            "created_at": get_utc_now().isoformat(),
            "updated_at": get_utc_now().isoformat(),
            "etag": utils.gen_etag(),
            "previous_job_id": previous_job_id,
            "status": "new",
        }
    )

    previous_job = base.get_resource_orm(models2.Job, previous_job_id)
    if user.is_not_in_team(previous_job.team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    # get the remoteci
    remoteci_id = str(previous_job.remoteci_id)
    remoteci = base.get_resource_orm(models2.Remoteci, remoteci_id)
    values.update({"remoteci_id": remoteci_id})

    # get the associated topic
    topic_id = str(previous_job.topic_id)
    topic = base.get_resource_orm(models2.Topic, topic_id)

    values.update(
        {
            "user_agent": flask.request.environ.get("HTTP_USER_AGENT"),
            "client_version": flask.request.environ.get("HTTP_CLIENT_VERSION"),
        }
    )

    next_topic_id = topic.next_topic_id

    if not next_topic_id:
        raise dci_exc.DCIException("topic %s does not contains a next topic" % topic_id)
    topic = base.get_resource_orm(models2.Topic, next_topic_id)
    product_id = topic.product_id

    # instantiate a new job in the next_topic_id
    # todo(yassine): make possible the upgrade to choose specific components
    values = _build_job(product_id, next_topic_id, remoteci, [], values)

    return flask.Response(
        json.dumps({"job": values}),
        201,
        headers={"ETag": values["etag"]},
        content_type="application/json",
    )


@api.route("/jobs", methods=["GET"])
@decorators.login_required
def get_all_jobs(user, topic_id=None):
    """Get all jobs.

    If topic_id is not None, then return all the jobs with a topic
    pointed by topic_id.
    """
    # get the diverse parameters
    args = check_and_get_args(flask.request.args.to_dict())

    query = flask.g.session.query(models2.Job)

    # If not admin nor rh employee then restrict the view to the team
    if user.is_not_super_admin() and user.is_not_read_only_user() and user.is_not_epm():
        query = query.filter(models2.Job.team_id.in_(user.teams_ids))

    # If topic_id not None, then filter by topic_id
    if topic_id is not None:
        query = query.filter(models2.Job.topic_id == topic_id)

    # Get only the non archived jobs
    query = query.filter(models2.Job.state != "archived")
    query = query.from_self()
    query = declarative.handle_args(query, models2.Job, args)

    # Load associated ressources
    query = (
        query.options(sa_orm.selectinload("results"))
        .options(sa_orm.joinedload("remoteci", innerjoin=True))
        .options(sa_orm.selectinload("components"))
        .options(sa_orm.joinedload("topic", innerjoin=True))
        .options(sa_orm.joinedload("team", innerjoin=True))
        .options(sa_orm.joinedload("pipeline", innerjoin=False))
        .options(sa_orm.joinedload("keys_values", innerjoin=False))
    )

    nb_jobs = query.count()
    query = declarative.handle_pagination(query, args)

    jobs = [j.serialize(ignore_columns=["data"]) for j in query.all()]

    return flask.jsonify({"jobs": jobs, "_meta": {"count": nb_jobs}})


@api.route("/jobs/<uuid:job_id>/components", methods=["GET"])
@decorators.login_required
def get_components_from_job(user, job_id):
    query = flask.g.session.query(models2.Job)

    if user.is_not_super_admin() and user.is_not_read_only_user() and user.is_not_epm():
        query = query.filter(models2.Job.team_id.in_(user.teams_ids))

    try:
        j = (
            query.filter(models2.Job.state != "archived")
            .filter(models2.Job.id == job_id)
            .options(sa_orm.selectinload("components"))
            .one()
        )
    except sa_orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="job not found", status_code=404)

    j_serialized = j.serialize()
    c_serialized = j_serialized["components"]
    return flask.jsonify(
        {"components": c_serialized, "_meta": {"count": len(c_serialized)}}
    )


@api.route("/jobs/<uuid:job_id>/components", methods=["POST"])
@decorators.login_required
def add_component_to_job(user, job_id):
    values = flask.request.json
    check_json_is_valid(add_component_schema, values)

    j = base.get_resource_orm(models2.Job, job_id)
    component = base.get_resource_orm(models2.Component, values["id"])

    if component.team_id and not user.is_in_team(component.team_id):
        raise dci_exc.Unauthorized()

    try:
        j.components.append(component)
        flask.g.session.add(j)
        flask.g.session.commit()
    except sa_exc.IntegrityError as e:
        flask.g.session.rollback()
        logger.error(str(e))
        raise dci_exc.DCIException(
            message="Unable to associate component %s to job %s"
            % (values["id"], job_id),
            status_code=409,
        )

    return flask.Response(None, 201, content_type="application/json")


@api.route("/jobs/<uuid:job_id>/components/<uuid:cmpt_id>", methods=["DELETE"])
@decorators.login_required
def remove_component_from_job(user, job_id, cmpt_id):
    j = base.get_resource_orm(models2.Job, job_id)
    component = base.get_resource_orm(models2.Component, cmpt_id)

    if component.team_id and not user.is_in_team(component.team_id):
        raise dci_exc.Unauthorized()

    try:
        j.components.remove(component)
        flask.g.session.add(j)
        flask.g.session.commit()
    # if the component is not present
    except ValueError:
        pass
    except sa_exc.IntegrityError as e:
        flask.g.session.rollback()
        logger.error(str(e))
        raise dci_exc.DCIException(
            message="Unable to remove component %s from job %s" % (cmpt_id, job_id),
            status_code=409,
        )

    return flask.Response(None, 201, content_type="application/json")


@api.route("/jobs/<uuid:job_id>/jobstates", methods=["GET"])
@decorators.login_required
def get_jobstates_by_job(user, job_id):
    base.get_resource_orm(models2.Job, job_id)
    return jobstates.get_all_jobstates(user, job_id)


@api.route("/jobs/<uuid:job_id>", methods=["GET"])
@decorators.login_required
def get_job_by_id(user, job_id):
    query = flask.g.session.query(models2.Job)
    query = query.filter(models2.Job.id == job_id)

    # If not admin nor rh employee then restrict the view to the team
    if user.is_not_super_admin() and user.is_not_read_only_user() and user.is_not_epm():
        query = query.filter(models2.Job.team_id.in_(user.teams_ids))

    # Get only non archived job
    query = query.filter(models2.Job.state != "archived")
    query = (
        query.options(sa_orm.joinedload("remoteci", innerjoin=True))
        .options(sa_orm.joinedload("topic", innerjoin=True))
        .options(sa_orm.joinedload("team", innerjoin=True))
        .options(sa_orm.selectinload("results"))
        .options(sa_orm.selectinload("components"))
        .options(sa_orm.selectinload("jobstates"))
        .options(sa_orm.joinedload("pipeline", innerjoin=False))
        .options(sa_orm.joinedload("keys_values", innerjoin=False))
    )
    try:
        job = query.one()
        job = job.serialize()
        files = [
            f.serialize()
            for f in flask.g.session.query(models2.File)
            .filter(
                sql.and_(
                    models2.File.jobstate_id == None,  # noqa
                    models2.File.job_id == job_id,
                    models2.File.state != "archived",
                )
            )
            .all()
        ]
        job["files"] = files

    except sa_orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="job not found", status_code=404)

    return flask.Response(
        json.dumps({"job": job}),
        200,
        headers={"ETag": job["etag"]},
        content_type="application/json",
    )


@api.route("/jobs/<uuid:job_id>", methods=["PUT"])
@decorators.login_required
@decorators.log
def update_job_by_id(user, job_id):
    """Update a job"""
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = clean_json_with_schema(update_job_schema, flask.request.json)

    job = base.get_resource_orm(models2.Job, job_id, if_match_etag)

    if user.is_not_in_team(job.team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    # Update jobstate if needed
    status = values.get("status")
    if status and job.status != status:
        jobstates.insert_jobstate({"status": status, "job_id": job_id})
        if status in models2.FINAL_STATUSES:
            jobs_events.create_event(job_id, status, job.topic_id)

    base.update_resource_orm(job, values)
    job = base.get_resource_orm(models2.Job, job_id)

    return flask.Response(
        json.dumps({"job": job.serialize()}),
        200,
        headers={"ETag": job.etag},
        content_type="application/json",
    )


@api.route("/jobs/<uuid:j_id>/files", methods=["POST"])
@decorators.login_required
def add_file_to_jobs(user, j_id):
    values = flask.request.json
    check_json_is_valid(create_job_schema, values)
    values.update({"job_id": j_id})

    return files.create_files(user, values)


@api.route("/jobs/<uuid:j_id>/files", methods=["GET"])
@decorators.login_required
def get_all_files_from_jobs(user, j_id):
    """Get all files."""
    return files.get_all_files(user, j_id)


@api.route("/jobs/<uuid:j_id>/results", methods=["GET"])
@decorators.login_required
def get_all_results_from_jobs(user, j_id):
    """Get all results from job."""

    job = base.get_resource_orm(models2.Job, j_id)

    if (
        user.is_not_in_team(job.team_id)
        and user.is_not_read_only_user()
        and user.is_not_epm()
    ):
        raise dci_exc.Unauthorized()

    # get testscases from tests_results
    try:
        query = flask.g.session.query(models2.TestsResult)
        query = query.filter(models2.TestsResult.job_id == job.id)
        all_tests_results = query.all()
    except Exception as e:
        logger.error(str(e))
        raise dci_exc.DCIException("error while getting the results: %s" % str(e))

    results = []
    for test_result in all_tests_results:
        test_result = test_result.serialize()
        results.append(
            {
                "filename": test_result["name"],
                "name": test_result["name"],
                "total": test_result["total"],
                "failures": test_result["failures"],
                "errors": test_result["errors"],
                "skips": test_result["skips"],
                "time": test_result["time"],
                "regressions": test_result["regressions"],
                "successfixes": test_result["successfixes"],
                "success": test_result["success"],
                "file_id": test_result["file_id"],
            }
        )

    return flask.jsonify({"results": results, "_meta": {"count": len(results)}})


@api.route("/jobs/<uuid:j_id>", methods=["DELETE"])
@decorators.login_required
@decorators.log
def delete_job_by_id(user, j_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    job = base.get_resource_orm(models2.Job, j_id, if_match_etag)

    if user.is_not_in_team(job.team_id):
        raise dci_exc.Unauthorized()

    try:
        job.state = "archived"
        query = flask.g.session.query(models2.File)
        query = query.filter(models2.File.job_id == j_id)
        query = query.update({"state": "archived"})
        flask.g.session.add(job)
        flask.g.session.commit()
    except Exception as e:
        flask.g.session.rollback()
        logging.error("unable to delete job %s: %s" % (j_id, str(e)))
        raise dci_exc.DCIException("unable to delete job %s: %s" % (j_id, str(e)))

    return flask.Response(None, 204, content_type="application/json")


@api.route("/jobs/purge", methods=["GET"])
@decorators.login_required
def get_to_purge_archived_jobs(user):
    return base.get_to_purge_archived_resources(user, models2.Job)


@api.route("/jobs/purge", methods=["POST"])
@decorators.login_required
def purge_archived_jobs(user):
    files.purge_archived_files()
    return base.purge_archived_resources(user, models2.Job)
