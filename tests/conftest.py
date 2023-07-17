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

import dci.app
from dci import dci_config
from dci.db import models2
import tests.utils as utils
import tests.sso_tokens as sso_tokens

from passlib.apps import custom_app_context as pwd_context
import contextlib
import pytest
import sqlalchemy_utils.functions
from sqlalchemy.orm import sessionmaker

import uuid


@pytest.fixture(scope="session")
def engine(request):
    utils.rm_upload_folder()
    db_uri = utils.conf["SQLALCHEMY_DATABASE_URI"]

    engine = dci_config.get_engine(db_uri)

    if not sqlalchemy_utils.functions.database_exists(db_uri):
        sqlalchemy_utils.functions.create_database(db_uri)
    utils.restore_db(engine)
    return engine


@pytest.fixture
def session(engine):
    return sessionmaker(bind=engine)()


@pytest.fixture
def empty_db(engine):
    with contextlib.closing(engine.connect()) as con:
        meta = models2.Base.metadata
        trans = con.begin()
        for table in reversed(meta.sorted_tables):
            con.execute(table.delete())
        trans.commit()
    return True


@pytest.fixture
def reset_job_event(engine):
    with contextlib.closing(engine.connect()) as con:
        trans = con.begin()
        con.execute("ALTER SEQUENCE jobs_events_id_seq RESTART WITH 1")
        trans.commit()
    return True


@pytest.fixture(scope="session", autouse=True)
def memoize_password_hash():
    def memoize(func):
        cache = {}

        def helper(*args):
            if args in cache:
                return cache[args]
            else:
                value = func(*args)
                cache[args] = value
                return value

        return helper

    pwd_context.verify = memoize(pwd_context.verify)
    pwd_context.hash = memoize(pwd_context.hash)


@pytest.fixture
def teardown_db_clean(request, engine):
    request.addfinalizer(lambda: utils.restore_db(engine))


@pytest.fixture
def fs_clean(request):
    """Clean test file upload directory"""
    request.addfinalizer(utils.rm_upload_folder)


@pytest.fixture
def db_provisioning(empty_db, session):
    utils.provision(session)


@pytest.fixture
def app(db_provisioning, engine, fs_clean):
    app = dci.app.create_app()
    app.testing = True
    app.engine = engine
    return app


@pytest.fixture
def admin(app):
    return utils.generate_client(app, ("admin", "admin"))


@pytest.fixture
def unauthorized(app):
    return utils.generate_client(app, ("bob", "bob"))


@pytest.fixture
def user(app):
    return utils.generate_client(app, ("user", "user"))


@pytest.fixture
def user2(app):
    return utils.generate_client(app, ("user2", "user2"))


@pytest.fixture
def rh_employee(app):
    return utils.generate_client(app, ("rh_employee", "rh_employee"))


@pytest.fixture
def user_sso(app, access_token):
    client = utils.generate_client(app, access_token=access_token)
    # first call, it create the user in the database
    client.get("/api/v1/users/me")
    return client


@pytest.fixture
def user_id(user):
    return user.get("/api/v1/users/me").data["user"]["id"]


@pytest.fixture
def user_no_team(admin):
    r = admin.get("/api/v1/users?where=name:user_no_team")
    return dict(r.data["users"][0])


@pytest.fixture
def epm(app):
    return utils.generate_client(app, ("epm", "epm"))


@pytest.fixture
def epm_id(epm):
    return epm.get("/api/v1/users/me").data["user"]["id"]


@pytest.fixture
def topic_id(admin, team_id, product):
    data = {
        "name": "topic_name",
        "product_id": product["id"],
        "component_types": ["type_1", "type_2", "type_3"],
    }
    topic = admin.post("/api/v1/topics", data=data).data
    t_id = topic["topic"]["id"]
    admin.post("/api/v1/topics/%s/teams" % t_id, data={"team_id": team_id})
    return str(t_id)


@pytest.fixture
def topic(admin, team_user_id, product):
    topic = admin.post(
        "/api/v1/topics",
        data={
            "name": "OSP12",
            "product_id": product["id"],
            "component_types": ["puddle_osp"],
        },
    ).data["topic"]
    admin.post(
        "/api/v1/components",
        data={
            "topic_id": topic["id"],
            "name": "RH7-RHOS-12.0 2017-11-09.2",
            "type": "puddle_osp",
        },
    )
    admin.post("/api/v1/topics/%s/teams" % topic["id"], data={"team_id": team_user_id})
    return topic


@pytest.fixture
def team_id(admin, team_user_id):
    team = admin.post("/api/v1/teams", data={"name": "pname"})
    return str(team.data["team"]["id"])


@pytest.fixture
def team_product_id(admin):
    team = admin.get("/api/v1/teams?where=name:product")
    team = admin.get("/api/v1/teams/%s" % team.data["teams"][0]["id"]).data
    return str(team["team"]["id"])


@pytest.fixture
def team_user_id(admin):
    team = admin.get("/api/v1/teams?where=name:user").data["teams"][0]
    return str(team["id"])


@pytest.fixture
def team_user_id2(admin):
    team = admin.get("/api/v1/teams?where=name:user2").data["teams"][0]
    return str(team["id"])


@pytest.fixture
def team_admin_id(admin):
    team = admin.get("/api/v1/teams?where=name:admin").data["teams"][0]
    return str(team["id"])


@pytest.fixture
def team_redhat_id(admin):
    team = admin.get("/api/v1/teams?where=name:Red Hat").data["teams"][0]
    return str(team["id"])


@pytest.fixture
def team_epm_id(admin):
    team = admin.get("/api/v1/teams?where=name:EPM").data["teams"][0]
    return str(team["id"])


@pytest.fixture
def topic_user(admin, user, team_user_id, team_user_id2, product):
    data = {
        "name": "topic_user_name",
        "product_id": product["id"],
        "component_types": ["type_1", "type_2", "type_3"],
    }
    topic = admin.post("/api/v1/topics", data=data).data["topic"]
    admin.post("/api/v1/topics/%s/teams" % topic["id"], data={"team_id": team_user_id})
    admin.post("/api/v1/topics/%s/teams" % topic["id"], data={"team_id": team_user_id2})
    for i in range(1, 4):
        admin.post(
            "/api/v1/components",
            data={"topic_id": topic["id"], "name": "comp%s" % i, "type": "type_%s" % i},
        )
    return topic


@pytest.fixture
def topic_user_id(topic_user):
    return topic_user["id"]


@pytest.fixture
def remoteci_id(admin, team_id):
    data = {"name": "pname", "team_id": team_id}
    remoteci = admin.post("/api/v1/remotecis", data=data).data
    return str(remoteci["remoteci"]["id"])


@pytest.fixture
def remoteci_user_api_secret(user, remoteci_user_id):
    api_secret = user.get("/api/v1/remotecis/%s" % remoteci_user_id).data
    return api_secret["remoteci"]["api_secret"]


@pytest.fixture
def remoteci_user(user, admin, team_user_id, topic_user_id):
    data = {"name": "user remoteci", "team_id": team_user_id}
    remoteci = user.post("/api/v1/remotecis", data=data).data

    return remoteci["remoteci"]


@pytest.fixture
def remoteci_user_id(remoteci_user):
    return str(remoteci_user["id"])


@pytest.fixture
def remoteci(admin, team_id):
    data = {"name": "remoteci", "team_id": team_id}
    return admin.post("/api/v1/remotecis", data=data).data["remoteci"]


@pytest.fixture
def remoteci_context(app, remoteci_user_id, remoteci_user_api_secret):
    remoteci = {
        "id": remoteci_user_id,
        "api_secret": remoteci_user_api_secret,
        "type": "remoteci",
    }
    return utils.generate_token_based_client(app, remoteci)


@pytest.fixture
def admin_remoteci_context(app, admin, team_admin_id):
    admin_remoteci = admin.post(
        "/api/v1/remotecis", data={"name": "admin remoteci", "team_id": team_admin_id}
    ).data["remoteci"]
    return utils.generate_token_based_client(
        app,
        {
            "id": admin_remoteci["id"],
            "api_secret": admin_remoteci["api_secret"],
            "type": "remoteci",
        },
    )


@pytest.fixture
def remoteci_configuration_user_id(user, remoteci_user_id, topic_user_id):
    rc = user.post(
        "/api/v1/remotecis/%s/configurations" % remoteci_user_id,
        data={
            "name": "cname",
            "topic_id": topic_user_id,
            "component_types": ["kikoo", "lol"],
            "data": {"lol": "lol"},
        },
    ).data
    return str(rc["configuration"]["id"])


@pytest.fixture
def feeder_id(epm, team_user_id):
    data = {"name": "feeder_osp", "team_id": team_user_id}
    feeder = epm.post("/api/v1/feeders", data=data).data
    return str(feeder["feeder"]["id"])


@pytest.fixture
def feeder_api_secret(epm, feeder_id):
    api_secret = epm.get("/api/v1/feeders/%s" % feeder_id).data
    return api_secret["feeder"]["api_secret"]


@pytest.fixture
def feeder_context(app, feeder_id, feeder_api_secret):
    feeder = {"id": feeder_id, "api_secret": feeder_api_secret, "type": "feeder"}
    return utils.generate_token_based_client(app, feeder)


def create_components(user, topic_id, component_types):
    component_ids = []
    for ct in component_types:
        data = {"topic_id": topic_id, "name": "name-" + str(uuid.uuid4()), "type": ct}
        cmpt = user.post("/api/v1/components", data=data).data
        component_ids.append(str(cmpt["component"]["id"]))
    return component_ids


@pytest.fixture
def components_ids(admin, topic_id):
    component_types = ["type_1", "type_2", "type_3"]
    return create_components(admin, topic_id, component_types)


@pytest.fixture
def components_user_ids(admin, topic_user_id):
    component_types = ["type_1", "type_2", "type_3"]
    return create_components(admin, topic_user_id, component_types)


@pytest.fixture
def job_admin(
    admin, admin_remoteci_context, components_user_ids, topic_user_id, team_admin_id
):
    admin.post(
        "/api/v1/topics/%s/teams" % topic_user_id, data={"team_id": team_admin_id}
    )
    data = {"components_ids": components_user_ids, "topic_id": topic_user_id}
    return admin_remoteci_context.post("/api/v1/jobs/schedule", data=data).data["job"]


@pytest.fixture
def job_user(remoteci_context, components_user_ids, topic_user_id):
    data = {"components_ids": components_user_ids, "topic_id": topic_user_id}
    job = remoteci_context.post("/api/v1/jobs/schedule", data=data).data
    return job["job"]


@pytest.fixture
def job_user_id(job_user):
    return job_user["id"]


@pytest.fixture
def jobstate_user_id(user, job_user_id):
    data = {"job_id": job_user_id, "status": "running", "comment": "kikoolol"}
    jobstate = user.post("/api/v1/jobstates", data=data).data
    return jobstate["jobstate"]["id"]


@pytest.fixture
def file_user_id(user, jobstate_user_id, team_user_id):
    headers = {"DCI-JOBSTATE-ID": jobstate_user_id, "DCI-NAME": "name"}
    file = user.post("/api/v1/files", headers=headers, data="kikoolol").data
    headers["team_id"] = team_user_id
    headers["id"] = file["file"]["id"]
    return file["file"]["id"]


@pytest.fixture
def file_job_user_id(user, job_user_id, team_user_id):
    headers = {"DCI-JOB-ID": job_user_id, "DCI-NAME": "name"}
    file = user.post("/api/v1/files", headers=headers, data="foobar").data
    headers["team_id"] = team_user_id
    headers["id"] = file["file"]["id"]
    return file["file"]["id"]


@pytest.fixture
def feeder(admin, team_product_id):
    data = {
        "name": "random-name-feeder",
        "team_id": team_product_id,
    }
    feeder = admin.post("/api/v1/feeders", data=data).data
    return feeder["feeder"]


@pytest.fixture
def product_openstack(admin):
    data = {
        "name": "OpenStack",
        "label": "OPENSTACK",
        "description": "Red Hat OpenStack Platform",
    }
    return admin.post("/api/v1/products", data=data).data["product"]


@pytest.fixture
def product(admin):
    return admin.get("/api/v1/products?where=label:AWSM").data["products"][0]


@pytest.fixture
def product2(admin):
    return admin.get("/api/v1/products?where=label:BEST").data["products"][0]


@pytest.fixture
def access_token():
    return sso_tokens.ACCESS_TOKEN_USER


@pytest.fixture
def access_token_rh_employee():
    return sso_tokens.ACCESS_TOKEN_READ_ONLY_USER


@pytest.fixture
def RHELProduct(admin):
    data = {"name": "RHEL", "label": "RHEL", "description": "Red Hat Entreprise Linux"}
    return admin.post("/api/v1/products", data=data).data["product"]


@pytest.fixture
def RHEL80Topic(admin, RHELProduct):
    data = {
        "name": "RHEL-8.0",
        "product_id": RHELProduct["id"],
        "component_types": ["Compose"],
        "export_control": True,
    }
    return admin.post("/api/v1/topics", data=data).data["topic"]


@pytest.fixture
def RHEL80Component(admin, RHEL80Topic):
    data = {
        "topic_id": RHEL80Topic["id"],
        "name": "RHEL-8.0.0-20190926.n.0",
        "type": "Compose",
    }
    return admin.post("/api/v1/components", data=data).data["component"]


@pytest.fixture
def RHEL81Topic(admin, RHELProduct):
    data = {
        "name": "RHEL-8.1",
        "product_id": RHELProduct["id"],
        "component_types": ["Compose"],
        "export_control": False,
    }
    return admin.post("/api/v1/topics", data=data).data["topic"]


@pytest.fixture
def RHEL81Component(admin, RHEL81Topic):
    data = {
        "topic_id": RHEL81Topic["id"],
        "name": "RHEL-8.1.0-20190926.n.0",
        "type": "Compose",
    }
    return admin.post("/api/v1/components", data=data).data["component"]


@pytest.fixture
def cki_test_file(user, job_user):
    headers = {
        "DCI-JOB-ID": job_user["id"],
        "DCI-NAME": "cki-result",
        "DCI-MIME": "application/junit",
        "Content-Disposition": "attachment; filename=cki-results.xml",
        "Content-Type": "application/junit",
    }
    data = open("tests/data/cki-results.xml").read()
    r = user.post("/api/v1/files", headers=headers, data=data)
    return r.data["file"]


@pytest.fixture
def openshift(admin):
    data = {
        "name": "OpenShift",
        "label": "OPENSHIFT",
        "description": "OpenShift is an open source container application platform	",
    }
    return admin.post("/api/v1/products", data=data).data["product"]


@pytest.fixture
def openshift_410(admin, openshift):
    data = {
        "name": "OCP-4.10",
        "product_id": openshift["id"],
        "component_types": ["ocp"],
    }
    return admin.post("/api/v1/topics", data=data).data["topic"]
