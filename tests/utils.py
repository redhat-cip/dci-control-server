# -*- encoding: utf-8 -*-
#
# Copyright 2015-2016 Red Hat, Inc.
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

try:
    from urlparse import parse_qsl
    from urlparse import urlparse
except ImportError:
    from urllib.parse import parse_qsl
    from urllib.parse import urlparse
import base64
import collections
import flask
import shutil

import jwt
import six

import dci.auth as auth
from dci.db import models2
import dci.dci_config as config
from dci.common import utils
from dciauth.v2.headers import generate_headers

import os
import subprocess

# convenient alias
conf = config.CONFIG


def restore_db(engine):
    models2.Base.metadata.reflect(engine)
    models2.Base.metadata.drop_all(engine)
    models2.Base.metadata.create_all(engine)


def rm_upload_folder():
    shutil.rmtree(conf["FILES_UPLOAD_FOLDER"], ignore_errors=True)


def generate_client(app, credentials=None, access_token=None):
    attrs = ["status_code", "data", "headers"]
    Response = collections.namedtuple("Response", attrs)

    if credentials:
        token = base64.b64encode(("%s:%s" % credentials).encode("utf8")).decode("utf8")
        headers = {
            "Authorization": "Basic " + token,
            "Content-Type": "application/json",
        }
    elif access_token:
        headers = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
        }

    def client_open_decorator(func):
        def wrapper(*args, **kwargs):
            headers.update(kwargs.get("headers", {}))
            kwargs["headers"] = headers
            content_type = headers.get("Content-Type")
            data = kwargs.get("data")
            if data and content_type == "application/json":
                kwargs["data"] = flask.json.dumps(data, cls=utils.JSONEncoder)
            response = func(*args, **kwargs)

            data = response.data
            if response.content_type == "application/json":
                data = flask.json.loads(data or "{}")
            if isinstance(data, six.binary_type):
                data = data.decode("utf8")
            return Response(response.status_code, data, response.headers)

        return wrapper

    client = app.test_client()
    client.open = client_open_decorator(client.open)

    return client


def generate_token_based_client(app, resource):
    attrs = ["status_code", "data", "headers"]
    Response = collections.namedtuple("Response", attrs)

    def client_open_decorator(func):
        def wrapper(*args, **kwargs):
            payload = kwargs.get("data")
            data = flask.json.dumps(payload, cls=utils.JSONEncoder) if payload else ""
            url = urlparse(args[0])
            params = dict(parse_qsl(url.query))
            headers = kwargs.get("headers", {})
            headers.update(
                generate_headers(
                    {
                        "method": kwargs.get("method"),
                        "endpoint": url.path,
                        "params": params,
                        "data": data,
                        "host": "localhost",
                    },
                    {
                        "access_key": "%s/%s" % (resource["type"], resource["id"]),
                        "secret_key": resource["api_secret"],
                    },
                )
            )
            headers.update({"Content-Type": "application/json"})
            kwargs["headers"] = headers
            if data:
                kwargs["data"] = data
            response = func(*args, **kwargs)
            data = flask.json.loads(response.data or "{}")
            return Response(response.status_code, data, response.headers)

        return wrapper

    client = app.test_client()
    client.open = client_open_decorator(client.open)
    return client


def generate_jwt(payload, private_key):
    return jwt.encode(payload, private_key, algorithm="RS256").decode("utf-8")


def _post_file(client, headers, content):
    return client.post("/api/v1/files", headers=headers, data=content).data["file"]


def create_task_file(client, jobstate_id, name, content="", content_type="text/plain"):
    return _post_file(
        client,
        {
            "DCI-JOBSTATE-ID": jobstate_id,
            "DCI-NAME": name,
            "DCI-MIME": content_type,
            "Content-Type": content_type,
        },
        content,
    )


def create_file(client, job_id, name, content="", content_type="text/plain"):
    return _post_file(
        client,
        {
            "DCI-JOB-ID": job_id,
            "DCI-NAME": name,
            "DCI-MIME": content_type,
            "Content-Type": content_type,
        },
        content,
    )


def allow_team_to_access_product(session, team, product):
    insert = models2.JOIN_PRODUCTS_TEAMS.insert().values(
        product_id=product.id, team_id=team.id
    )
    session.execute(insert)


def provision(session):
    # Create RHEL product
    rhel = models2.Product(
        name="RHEL",
        label="RHEL",
        description="RHEL is a Linux distribution developed by Red Hat and targeted toward the commercial market",
    )
    session.add(rhel)
    # Create OpenStack product
    openstack = models2.Product(
        name="OpenStack",
        label="OPENSTACK",
        description="OpenStack is a free and open-source software platform for cloud computing",
    )
    session.add(openstack)
    # Create OpenShift product
    openshift = models2.Product(
        name="OpenShift",
        label="OPENSHIFT",
        description="OpenShift is an open source container application platform	",
    )
    session.add(openshift)
    # Create admin
    admin_team = models2.Team(name="admin", has_pre_release_access=True)
    admin_user = models2.User(
        name="admin",
        sso_username="admin",
        password=auth.hash_password("admin"),
        fullname="Admin",
        email="admin@example.org",
    )
    admin_user.team.append(admin_team)
    session.add(admin_user)

    # Create user1
    team1 = models2.Team(name="team1")
    user1 = models2.User(
        name="user1",
        sso_username="user1",
        password=auth.hash_password("user1"),
        fullname="User 1",
        email="user@example.org",
    )
    user1.team.append(team1)
    session.add(user1)

    # Create user2
    team2 = models2.Team(name="team2")
    user2 = models2.User(
        name="user2",
        sso_username="user2",
        password=auth.hash_password("user2"),
        fullname="User 2",
        email="user2@example.org",
    )
    user2.team.append(team2)
    session.add(user2)

    # Create user3
    team3 = models2.Team(name="team3")
    user3 = models2.User(
        name="user3",
        sso_username="user3",
        password=auth.hash_password("user3"),
        fullname="User 3",
        email="user3@example.org",
    )
    user3.team.append(team3)
    session.add(user3)

    # Create user no team
    user_no_team = models2.User(
        name="user_no_team",
        sso_username="user_no_team",
        password=auth.hash_password("user_no_team"),
        fullname="User No Team",
        email="user_no_team@example.org",
    )
    session.add(user_no_team)

    # Create Red Hat employee
    red_hat = models2.Team(name="Red Hat")
    rh_employee = models2.User(
        name="rh_employee",
        sso_username="rh_employee",
        password=auth.hash_password("rh_employee"),
        fullname="Employee at Red Hat",
        email="rh_employee@redhat.com",
    )
    rh_employee.team.append(red_hat)
    session.add(rh_employee)

    # Create EPM
    epm_team = models2.Team(name="EPM")
    epm = models2.User(
        name="epm",
        sso_username="epm",
        password=auth.hash_password("epm"),
        fullname="Partner Engineer",
        email="epm@redhat.com",
    )
    epm.team.append(epm_team)
    session.add(epm)

    # Commit to create all products, teams and users
    session.commit()

    # Allow teams to access products
    allow_team_to_access_product(session, admin_team, rhel)
    allow_team_to_access_product(session, admin_team, openstack)
    allow_team_to_access_product(session, admin_team, openshift)
    allow_team_to_access_product(session, team1, rhel)
    allow_team_to_access_product(session, team1, openstack)
    allow_team_to_access_product(session, team2, rhel)
    allow_team_to_access_product(session, red_hat, rhel)
    allow_team_to_access_product(session, red_hat, openstack)
    allow_team_to_access_product(session, red_hat, openshift)
    session.commit()


SWIFT = "dci.stores.swift.Swift"

FileDesc = collections.namedtuple("FileDesc", ["name", "content"])


def run_bin(bin_name, env):
    env.update(os.environ.copy())
    exec_path = os.path.abspath(__file__)
    exec_path = os.path.abspath("%s/../../bin/%s" % (exec_path, bin_name))
    return subprocess.Popen(exec_path, shell=True, env=env)
