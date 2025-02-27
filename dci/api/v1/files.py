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
import gc
import io
import xml.etree.ElementTree
from dci.common.time import get_job_duration

try:
    from xmlrpclib import ServerProxy
except ImportError:
    from xmlrpc.client import ServerProxy

import flask
from flask import json

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import junit
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


def _get_previous_testsuites(prev_job, filename):
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
    return junit.get_testsuites_from_junit(file_descriptor)


def _calculate_and_save_test_results(values, junit_file, job):
    prev_job = get_previous_job_in_topic(job)
    previous_testsuites = _get_previous_testsuites(prev_job, values["name"])
    testsuites = junit.get_testsuites_from_junit(junit_file)
    testsuites = junit.update_testsuites_with_testcase_changes(
        previous_testsuites, testsuites
    )
    tests_results = junit.calculate_test_results(testsuites)

    tr = models2.TestsResult()
    tr.id = utils.gen_uuid()
    tr.created_at = values["created_at"]
    tr.updated_at = datetime.datetime.utcnow().isoformat()
    tr.file_id = values["id"]
    tr.job_id = job.id
    tr.name = values["name"]
    tr.success = tests_results["success"]
    tr.failures = tests_results["failures"]
    tr.errors = tests_results["errors"]
    tr.regressions = tests_results["regressions"]
    tr.successfixes = tests_results["successfixes"]
    tr.skips = tests_results["skipped"]
    tr.total = tests_results["tests"]
    tr.time = tests_results["time"]

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
        if key in ["md5", "mime", "jobstate_id", "job_id", "name"]:
            new_headers[key] = value
    return new_headers


@api.route("/files", methods=["POST"])
@decorators.log_file_info
@decorators.login_required
def create_files(user):
    file_info = get_file_info_from_headers(dict(flask.request.headers))
    values = dict.fromkeys(["md5", "mime", "jobstate_id", "job_id", "name"])
    values.update(file_info)

    if values.get("jobstate_id") is None and values.get("job_id") is None:
        raise dci_exc.DCIException(
            "HTTP headers DCI-JOBSTATE-ID or DCI-JOB-ID must be specified"
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

    store = flask.g.store
    store.upload("files", file_path, io.BytesIO(flask.request.data))
    logger.info("store upload %s (%s)" % (values["name"], file_id))
    s_file = store.head("files", file_path)
    logger.info("store head %s (%s)" % (values["name"], file_id))
    etag = utils.gen_etag()
    values.update(
        {
            "id": file_id,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat(),
            "team_id": job.team_id,
            "md5": None,
            "size": s_file.get("content-length", s_file.get("ContentLength")),
            "state": "active",
            "etag": etag,
        }
    )

    new_file = base.create_resource_orm(models2.File, values)
    result = {"file": new_file}

    # Update job duration if it's jobstate's file
    if values.get("jobstate_id"):
        base.update_resource_orm(job, {"duration": get_job_duration(job)})
    gc.collect()

    if new_file["mime"] == "application/junit":
        try:
            _, junit_file = store.get("files", file_path)
            _calculate_and_save_test_results(values, junit_file, job)
        except xml.etree.ElementTree.ParseError as xmlerror:
            raise dci_exc.DCIException(message="Invalid XML: " + xmlerror.msg)

    job.etag = utils.gen_etag()
    try:
        flask.g.session.commit()
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e), status_code=409)

    return flask.Response(json.dumps(result), 201, content_type="application/json")


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
    store = flask.g.store
    file_path = files_utils.build_file_path(
        file_object.team_id, file_object.job_id, file_object.id
    )
    # Check if file exist on the storage engine
    store.head("files", file_path)
    _, file_descriptor = store.get("files", file_path)
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


@api.route("/files/<uuid:file_id>", methods=["DELETE"])
@decorators.login_required
def delete_file_by_id(user, file_id):
    file = base.get_resource_orm(models2.File, file_id)

    if not user.is_in_team(file.team_id):
        raise dci_exc.Unauthorized()
    base.update_resource_orm(file, {"state": "archived"})

    job = base.get_resource_orm(models2.Job, file.job_id)
    job.etag = utils.gen_etag()
    try:
        flask.g.session.commit()
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e), status_code=409)

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
    store = flask.g.store

    # for each file delete it from within a transaction
    # if the SQL deletion or the Store deletion fail then
    # rollback the transaction, otherwise commit.
    for file in archived_files:
        try:
            file_path = files_utils.build_file_path(
                file["team_id"], file["job_id"], file["id"]
            )
            store.delete("files", file_path)
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


@api.route("/files/<uuid:file_id>/junit", methods=["GET"])
@decorators.login_required
def get_junit_file(user, file_id):
    file = base.get_resource_orm(models2.File, file_id)
    if (
        user.is_not_in_team(file.team_id)
        and user.is_not_read_only_user()
        and user.is_not_epm()
    ):
        raise dci_exc.Unauthorized()
    junit_file = get_file_descriptor(file)
    testsuites = junit.get_testsuites_from_junit(junit_file)
    job = base.get_resource_orm(models2.Job, file.job_id)
    prev_job = get_previous_job_in_topic(job)
    previous_testsuites = _get_previous_testsuites(prev_job, file.name)
    previous_job_info = {"id": prev_job.id, "name": prev_job.name} if prev_job else None
    return flask.Response(
        json.dumps(
            {
                "id": str(file_id),
                "name": file.name,
                "job": {"id": job.id, "name": job.name},
                "previous_job": previous_job_info,
                "testsuites": junit.update_testsuites_with_testcase_changes(
                    previous_testsuites, testsuites
                ),
            }
        ),
        200,
        content_type="application/json",
    )
