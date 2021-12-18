# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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

import datetime

import flask
from flask import json

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import jobs_events
from dci.api.v1 import notifications
from dci.api.v1 import files
from dci.api.v1 import transformations
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas import check_json_is_valid, jobstate_schema, check_and_get_args
from dci.common import utils
from dci.db import models
from dci.db import models2
from dci.db import declarative
import sqlalchemy.orm as sa_orm

# associate column names with the corresponding SA Column object
_TABLE = models.JOBSTATES
_JS_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {"team": False, "job": False, "files": True}


def insert_jobstate(user, values):
    values.update(
        {"id": utils.gen_uuid(), "created_at": datetime.datetime.utcnow().isoformat()}
    )

    query = _TABLE.insert().values(**values)

    flask.g.db_conn.execute(query)


def serialize_job(user, job):
    embeds = ["components", "topic", "remoteci", "results"]
    embeds_many = {
        "components": True,
        "topic": False,
        "remoteci": False,
        "results": True,
    }
    job = base.get_resource_by_id(
        user, job, models.JOBS, embed_many=embeds_many, embeds=embeds, jsonify=False
    )
    results_with_testcases = []
    for result in job["results"]:
        file = base.get_resource_orm(models2.File, result["file_id"])
        file_descriptor = files.get_file_descriptor(file)
        jsonunit = transformations.junit2dict(file_descriptor)
        result_with_testcases = result.copy()
        result_with_testcases["testcases"] = jsonunit["testscases"]
        results_with_testcases.append(result_with_testcases)
    job["results"] = results_with_testcases
    return job


@api.route("/jobstates", methods=["POST"])
@decorators.login_required
def create_jobstates(user):
    values = flask.request.json
    check_json_is_valid(jobstate_schema, values)
    values.update(
        {"id": utils.gen_uuid(), "created_at": datetime.datetime.utcnow().isoformat()}
    )

    # if one create a 'failed' jobstates and the current state is either
    # 'run' or 'pre-run' then set the job to 'error' state
    job_id = values.get("job_id")
    job = base.get_resource_orm(models2.Job, job_id)
    job_serialized = job.serialize()
    status = values.get("status")
    if status in ["failure", "error"]:
        if job.status in ["new", "pre-run"]:
            values["status"] = "error"

    created_js = base.create_resource_orm(models2.Jobstate, values)

    # Update job status
    job_duration = datetime.datetime.utcnow() - job.created_at
    job.status = status
    job.duration = job_duration.seconds

    try:
        flask.g.session.commit()
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e), status_code=409)

    # send notification in case of final jobstate status
    if status in models2.FINAL_STATUSES:
        job = serialize_job(user, job_serialized)
        jobs_events.create_event(job["id"], values["status"], job["topic_id"])
        notifications.dispatcher(job)

    result = json.dumps({"jobstate": created_js})
    return flask.Response(result, 201, content_type="application/json")


def get_all_jobstates(user, job_id):
    """Get all jobstates."""
    args = check_and_get_args(flask.request.args.to_dict())
    job = base.get_resource_orm(models2.Job, job_id)
    if user.is_not_super_admin() and user.is_not_read_only_user() and user.is_not_epm():
        if job.team_id not in user.teams_ids:
            raise dci_exc.Unauthorized()

    query = flask.g.session.query(models2.Jobstate)
    query = query.filter(models2.Jobstate.job_id == job_id).options(
        sa_orm.joinedload("files")
    )
    query = declarative.handle_args(query, models2.Jobstate, args)

    nb_jobstates = query.count()
    jobstates = [js.serialize() for js in query.all()]

    return flask.jsonify({"jobstates": jobstates, "_meta": {"count": nb_jobstates}})


@api.route("/jobstates/<uuid:js_id>", methods=["GET"])
@decorators.login_required
def get_jobstate_by_id(user, js_id):
    js = base.get_resource_orm(
        models2.Jobstate, js_id, options=[sa_orm.joinedload("files")]
    )
    return flask.Response(
        json.dumps({"jobstate": js.serialize()}),
        200,
        content_type="application/json",
    )


@api.route("/jobstates/<uuid:js_id>", methods=["DELETE"])
@decorators.login_required
def delete_jobstate_by_id(user, js_id):
    jobstate = base.get_resource_orm(models2.Jobstate, js_id)
    job = base.get_resource_orm(models2.Job, jobstate.job_id)

    if user.is_not_in_team(job.team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    try:
        flask.g.session.delete(jobstate)
        flask.g.session.commit()
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e), status_code=409)

    return flask.Response(None, 204, content_type="application/json")
