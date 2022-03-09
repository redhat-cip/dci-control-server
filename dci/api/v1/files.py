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
import base64
import datetime
import io

try:
    from xmlrpclib import ServerProxy
except ImportError:
    from xmlrpc.client import ServerProxy

import flask
from flask import json

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import transformations as tsfm
from dci.api.v1 import tests
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    check_json_is_valid,
    file_upload_certification_schema,
    check_and_get_args,
)
from dci.common import utils
from dci.db import models2
from dci.db import declarative
from dci import dci_config
from dci.stores import files_utils
import logging

from sqlalchemy import sql
from sqlalchemy import orm
from sqlalchemy import exc as sa_exc

logger = logging.getLogger(__name__)


def get_previous_job_in_topic(job):
    topic_id = job.topic_id
    query = flask.g.session.query(models2.Job)
    query = (
        query.filter(
            sql.and_(
                models2.Job.topic_id == topic_id,
                models2.Job.created_at < job.created_at,
                models2.Job.id != job.id,
                models2.Job.remoteci_id == job.remoteci_id,
                models2.Job.state != "archived",
            ),
            models2.Job.name == job.name,
            models2.Job.configuration == job.configuration,
            models2.Job.url == job.url,
        )
        .order_by(sql.desc(models2.Job.created_at))
        .limit(1)
    )
    try:
        return query.one()
    except orm.exc.NoResultFound:
        return None


def _get_previous_jsonunit(job, filename):
    prev_job = get_previous_job_in_topic(job)
    if prev_job is None:
        return None
    query = flask.g.session.query(models2.TestsResult).filter(
        sql.and_(
            models2.TestsResult.job_id == prev_job.id,
            models2.TestsResult.name == filename,
        )
    )
    try:
        res = query.one()
    except orm.exc.NoResultFound:
        return None
    test_file = base.get_resource_orm(models2.File, res.file_id)
    file_descriptor = get_file_descriptor(test_file)
    return tsfm.junit2dict(file_descriptor)


def _compute_regressions_successfix(jsonunit, previous_jsonunit):
    if previous_jsonunit and len(previous_jsonunit["testscases"]) > 0:
        return tsfm.add_regressions_and_successfix_to_tests(previous_jsonunit, jsonunit)
    return jsonunit


def _compute_known_tests_cases(jsonunit, job):
    tests_to_issues = tests.get_tests_to_issues(job.topic_id)
    return tsfm.add_known_issues_to_tests(jsonunit, tests_to_issues)


def _process_junit_file(values, junit_file, job):
    jsonunit = tsfm.junit2dict(junit_file)
    previous_jsonunit = _get_previous_jsonunit(job, values["name"])

    jsonunit = _compute_regressions_successfix(jsonunit, previous_jsonunit)
    jsonunit = _compute_known_tests_cases(jsonunit, job)

    tr = models2.TestsResult()
    tr.id = utils.gen_uuid()
    tr.created_at = values["created_at"]
    tr.updated_at = datetime.datetime.utcnow().isoformat()
    tr.file_id = values["id"]
    tr.job_id = job.id
    tr.name = values["name"]
    tr.success = jsonunit["success"]
    tr.failures = jsonunit["failures"]
    tr.errors = jsonunit["errors"]
    tr.regressions = jsonunit["regressions"]
    tr.successfixes = jsonunit["successfixes"]
    tr.skips = jsonunit["skips"]
    tr.total = jsonunit["total"]
    tr.time = jsonunit["time"]

    try:
        flask.g.session.add(tr)
        flask.g.session.commit()
    except sa_exc.IntegrityError as ie:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(ie), status_code=409)
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e))


def get_file_info_from_headers(headers):
    new_headers = {}
    for key, value in headers.items():
        key = key.lower().replace("dci-", "").replace("-", "_")
        if key in ["md5", "mime", "jobstate_id", "job_id", "name", "test_id"]:
            new_headers[key] = value
    return new_headers


@api.route("/files", methods=["POST"])
@decorators.login_required
def create_files(user):
    file_info = get_file_info_from_headers(dict(flask.request.headers))
    values = dict.fromkeys(["md5", "mime", "jobstate_id", "job_id", "name", "test_id"])
    values.update(file_info)

    if values.get("jobstate_id") is None and values.get("job_id") is None:
        raise dci_exc.DCIException(
            "HTTP headers DCI-JOBSTATE-ID or " "DCI-JOB-ID must be specified"
        )
    if values.get("name") is None:
        raise dci_exc.DCIException("HTTP header DCI-NAME must be specified")

    if values.get("jobstate_id") and values.get("job_id") is None:
        jobstate = base.get_resource_orm(models2.Jobstate, values.get("jobstate_id"))
        values["job_id"] = jobstate.job_id

    job = base.get_resource_orm(models2.Job, values.get("job_id"))
    if (
        user.is_not_in_team(job.team_id)
        and user.is_read_only_user()
        and user.is_not_epm()
    ):
        raise dci_exc.Unauthorized()

    file_id = utils.gen_uuid()
    file_path = files_utils.build_file_path(job.team_id, values["job_id"], file_id)

    store = dci_config.get_store("files")
    store.upload(file_path, io.BytesIO(flask.request.data))
    s_file = store.head(file_path)

    etag = utils.gen_etag()
    values.update(
        {
            "id": file_id,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat(),
            "team_id": job.team_id,
            "md5": None,
            "size": s_file["content-length"],
            "state": "active",
            "etag": etag,
        }
    )

    new_file = base.create_resource_orm(models2.File, values)
    result = json.dumps({"file": new_file})

    if new_file["mime"] == "application/junit":
        _, junit_file = store.get(file_path)
        _process_junit_file(values, junit_file, job)

    # Update job duration if it's jobstate's file
    job_duration = datetime.datetime.utcnow() - job.created_at
    base.update_resource_orm(job, {"duration": job_duration.seconds})

    return flask.Response(result, 201, content_type="application/json")


def get_all_files(user, job_id):
    """Get all files."""
    args = check_and_get_args(flask.request.args.to_dict())
    job = base.get_resource_orm(models2.Job, job_id)
    if user.is_not_super_admin() and user.is_not_read_only_user() and user.is_not_epm():
        if job.team_id not in user.teams_ids:
            raise dci_exc.Unauthorized()

    query = flask.g.session.query(models2.File)
    query = query.filter(
        sql.and_(models2.File.job_id == job_id, models2.File.state != "archived")
    )

    query = declarative.handle_args(query, models2.File, args)
    nb_files = query.count()
    query = declarative.handle_pagination(query, args)

    files = [f.serialize() for f in query.all()]

    return json.jsonify({"files": files, "_meta": {"count": nb_files}})


@api.route("/files/<uuid:file_id>", methods=["GET"])
@decorators.login_required
def get_file_by_id(user, file_id):
    file = base.get_resource_orm(models2.File, file_id)

    return flask.Response(
        json.dumps({"file": file.serialize()}),
        200,
        content_type="application/json",
    )


def get_file_descriptor(file_object):
    store = dci_config.get_store("files")
    file_path = files_utils.build_file_path(
        file_object.team_id, file_object.job_id, file_object.id
    )
    # Check if file exist on the storage engine
    store.head(file_path)
    _, file_descriptor = store.get(file_path)
    return file_descriptor


@api.route("/files/<uuid:file_id>/content", methods=["GET"])
@decorators.login_required
def get_file_content(user, file_id):
    file = base.get_resource_orm(models2.File, file_id)
    if (
        user.is_not_in_team(file.team_id)
        and user.is_not_read_only_user()
        and user.is_not_epm()
    ):
        raise dci_exc.Unauthorized()
    file_descriptor = get_file_descriptor(file)
    return flask.send_file(
        file_descriptor,
        mimetype=file.mime or "text/plain",
        as_attachment=True,
        attachment_filename=file.name.replace(" ", "_"),
    )


@api.route("/files/<uuid:file_id>/testscases", methods=["GET"])
@decorators.login_required
def get_file_testscases(user, file_id):
    file = base.get_resource_orm(models2.File, file_id)
    if (
        user.is_not_in_team(file.team_id)
        and user.is_not_read_only_user()
        and user.is_not_epm()
    ):
        raise dci_exc.Unauthorized()
    file_descriptor = get_file_descriptor(file)
    jsonunit = tsfm.junit2dict(file_descriptor)
    job = base.get_resource_orm(models2.Job, file.job_id)
    previous_jsonunit = _get_previous_jsonunit(job, file.name)
    jsonunit = _compute_regressions_successfix(jsonunit, previous_jsonunit)
    return flask.Response(
        json.dumps({"testscases": jsonunit["testscases"]}),
        200,
        content_type="application/json",
    )


@api.route("/files/<uuid:file_id>", methods=["DELETE"])
@decorators.login_required
def delete_file_by_id(user, file_id):
    file = base.get_resource_orm(models2.File, file_id)

    if not user.is_in_team(file.team_id):
        raise dci_exc.Unauthorized()

    base.update_resource_orm(file, {"state": "archived"})
    return flask.Response(None, 204, content_type="application/json")


def build_certification(username, password, node_id, file_name, file_content):
    return {
        "username": username,
        "password": password,
        "id": node_id,
        "type": "certification",
        "data": base64.b64encode(file_content),
        "description": "DCI automatic upload test log",
        "filename": file_name,
    }


@api.route("/files/<uuid:file_id>/certifications", methods=["POST"])
@decorators.login_required
def upload_certification(user, file_id):
    data = flask.request.json
    check_json_is_valid(file_upload_certification_schema, data)

    file = base.get_resource_orm(models2.File, file_id)
    file_descriptor = get_file_descriptor(file)
    file_content = file_descriptor.read()

    username = data["username"]
    password = data["password"]
    conf = dci_config.CONFIG
    proxy = ServerProxy(conf["CERTIFICATION_URL"])
    certification_details = proxy.Cert.getOpenStack_4_7(
        {
            "username": username,
            "password": password,
            "certification_id": data["certification_id"],
        }
    )
    certification = build_certification(
        username, password, certification_details["cert_nid"], file.name, file_content
    )
    proxy.Cert.uploadTestLog(certification)
    return flask.Response(None, 204, content_type="application/json")


@api.route("/files/purge", methods=["GET"])
@decorators.login_required
def get_to_purge_archived_files(user):
    return base.get_resources_to_purge_orm(user, models2.File)


@api.route("/files/purge", methods=["POST"])
@decorators.login_required
def purge_archived_files(user):

    # get all archived files
    archived_files = base.get_resources_to_purge_orm(user, models2.File).json["files"]
    store = dci_config.get_store("files")

    # for each file delete it from within a transaction
    # if the SQL deletion or the Store deletion fail then
    # rollback the transaction, otherwise commit.
    for file in archived_files:
        try:
            file_path = files_utils.build_file_path(
                file["team_id"], file["job_id"], file["id"]
            )
            store.delete(file_path)
            flask.g.session.query(models2.File).filter(
                models2.File.id == file["id"]
            ).delete()
            flask.g.session.commit()
            logger.debug("file %s removed" % file_path)
        except sa_exc.DBAPIError as e:
            logger.error(
                "Error while removing file %s, message: %s" % (file_path, str(e))
            )
            flask.g.session.rollback()
            raise dci_exc.DCIException(str(e))

    return flask.Response(None, 204, content_type="application/json")
