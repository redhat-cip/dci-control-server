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
    app.messaging.publish = lambda x: None
    return app


# Clients
# Clients basic auth
@pytest.fixture
def client_unauthorized(app):
    return utils.generate_client(app, ("bob", "bob"))


@pytest.fixture
def client_admin(app):
    return utils.generate_client(app, ("admin", "admin"))


@pytest.fixture
def client_user1(app):
    return utils.generate_client(app, ("user1", "user1"))


@pytest.fixture
def client_user2(app):
    return utils.generate_client(app, ("user2", "user2"))


@pytest.fixture
def client_user3(app):
    return utils.generate_client(app, ("user3", "user3"))


@pytest.fixture
def client_epm(app):
    return utils.generate_client(app, ("epm", "epm"))


@pytest.fixture
def client_rh_employee(app):
    return utils.generate_client(app, ("rh_employee", "rh_employee"))


# SSO clients
@pytest.fixture
def sso_client_user1(app, access_token_user1):
    client = utils.generate_client(app, access_token=access_token_user1)
    # first call, it create the user in the database
    client.get("/api/v1/users/me")
    return client


@pytest.fixture
def sso_client_user4(app, access_token_user4):
    client = utils.generate_client(app, access_token=access_token_user4)
    # first call, it create the user in the database
    client.get("/api/v1/users/me")
    return client


@pytest.fixture
def access_token_user1():
    return sso_tokens.ACCESS_TOKEN_USER1


@pytest.fixture
def access_token_user4():
    return sso_tokens.ACCESS_TOKEN_USER4


@pytest.fixture
def access_token_rh_employee():
    return sso_tokens.ACCESS_TOKEN_RH_EMPLOYEE


# HMAC clients
@pytest.fixture
def hmac_client_admin(app, client_admin, team_admin_id):
    admin_remoteci = client_admin.post(
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
def hmac_client_team1(app, team1_remoteci):
    remoteci = {
        "id": team1_remoteci["id"],
        "api_secret": team1_remoteci["api_secret"],
        "type": "remoteci",
    }
    return utils.generate_token_based_client(app, remoteci)


@pytest.fixture
def hmac_client_redhat(app, redhat_remoteci):
    return utils.generate_token_based_client(
        app,
        {
            "id": redhat_remoteci["id"],
            "api_secret": redhat_remoteci["api_secret"],
            "type": "remoteci",
        },
    )


@pytest.fixture
def hmac_client_feeder(app, team1_feeder):
    feeder = {
        "id": team1_feeder["id"],
        "api_secret": team1_feeder["api_secret"],
        "type": "feeder",
    }
    return utils.generate_token_based_client(app, feeder)


# Users
@pytest.fixture
def admin(client_admin):
    return client_admin.get("/api/v1/users/me").data["user"]


@pytest.fixture
def admin_id(admin):
    return admin["id"]


@pytest.fixture
def epm(client_epm):
    return client_epm.get("/api/v1/users/me").data["user"]


@pytest.fixture
def epm_id(epm):
    return epm["id"]


@pytest.fixture
def user_no_team(client_admin):
    r = client_admin.get("/api/v1/users?where=name:user_no_team")
    return r.data["users"][0]


@pytest.fixture
def user1_id(client_user1):
    return client_user1.get("/api/v1/users/me").data["user"]["id"]


@pytest.fixture
def user3_id(client_user3):
    return client_user3.get("/api/v1/users/me").data["user"]["id"]


@pytest.fixture
def user4_id(sso_client_user4):
    return sso_client_user4.get("/api/v1/users/me").data["user"]["id"]


@pytest.fixture
def rh_employee(client_rh_employee):
    return client_rh_employee.get("/api/v1/users/me").data["user"]


@pytest.fixture
def rh_employee_id(rh_employee):
    return rh_employee["id"]


# Teams
@pytest.fixture
def team_admin(client_admin):
    return client_admin.get("/api/v1/teams?where=name:admin").data["teams"][0]


@pytest.fixture
def team_admin_id(team_admin):
    return str(team_admin["id"])


@pytest.fixture
def team1(client_admin):
    return client_admin.get("/api/v1/teams?where=name:team1").data["teams"][0]


@pytest.fixture
def team1_id(team1):
    return str(team1["id"])


@pytest.fixture
def team2(client_admin):
    return client_admin.get("/api/v1/teams?where=name:team2").data["teams"][0]


@pytest.fixture
def team2_id(team2):
    return str(team2["id"])


@pytest.fixture
def team3(client_admin):
    return client_admin.get("/api/v1/teams?where=name:team3").data["teams"][0]


@pytest.fixture
def team3_id(team3):
    return str(team3["id"])


@pytest.fixture
def team_redhat(client_admin):
    return client_admin.get("/api/v1/teams?where=name:Red Hat").data["teams"][0]


@pytest.fixture
def team_redhat_id(team_redhat):
    return str(team_redhat["id"])


@pytest.fixture
def team_epm(client_admin):
    return client_admin.get("/api/v1/teams?where=name:EPM").data["teams"][0]


@pytest.fixture
def team_epm_id(team_epm):
    return str(team_epm["id"])


# Remotecis
@pytest.fixture
def team1_remoteci(client_user1, team1_id):
    data = {"name": "user remoteci", "team_id": team1_id}
    remoteci = client_user1.post("/api/v1/remotecis", data=data).data

    return remoteci["remoteci"]


@pytest.fixture
def team1_remoteci_id(team1_remoteci):
    return str(team1_remoteci["id"])


@pytest.fixture
def team2_remoteci(client_admin, team2_id):
    data = {"name": "remoteci", "team_id": team2_id}
    return client_admin.post("/api/v1/remotecis", data=data).data["remoteci"]


@pytest.fixture
def team2_remoteci_id(team2_remoteci):
    return str(team2_remoteci["id"])


@pytest.fixture
def redhat_remoteci(client_rh_employee, team_redhat_id):
    data = {"name": "Red Hat remoteci", "team_id": team_redhat_id}
    return client_rh_employee.post("/api/v1/remotecis", data=data).data["remoteci"]


# Jobs, jobstates, files
@pytest.fixture
def team_admin_job(hmac_client_admin, rhel_80_topic, rhel_80_component_id):
    data = {
        "components_ids": [rhel_80_component_id],
        "topic_id": rhel_80_topic["id"],
    }
    return hmac_client_admin.post("/api/v1/jobs/schedule", data=data).data["job"]


@pytest.fixture
def team1_job(hmac_client_team1, rhel_80_topic, rhel_80_component_id):
    data = {
        "name": "test",
        "components_ids": [rhel_80_component_id],
        "topic_id": rhel_80_topic["id"],
    }
    return hmac_client_team1.post("/api/v1/jobs/schedule", data=data).data["job"]


@pytest.fixture
def team1_job_id(team1_job):
    return team1_job["id"]


@pytest.fixture
def team1_jobstate(client_user1, team1_job_id):
    data = {"job_id": team1_job_id, "status": "running", "comment": "kikoolol"}
    jobstate = client_user1.post("/api/v1/jobstates", data=data).data
    return jobstate["jobstate"]["id"]


@pytest.fixture
def team1_jobstate_file(client_user1, team1_jobstate, team1_id):
    headers = {"DCI-JOBSTATE-ID": team1_jobstate, "DCI-NAME": "name"}
    file = client_user1.post("/api/v1/files", headers=headers, data="kikoolol").data
    headers["team_id"] = team1_id
    headers["id"] = file["file"]["id"]
    return file["file"]["id"]


@pytest.fixture
def team1_job_file(client_user1, team1_job_id, team1_id):
    headers = {"DCI-JOB-ID": team1_job_id, "DCI-NAME": "name"}
    file = client_user1.post("/api/v1/files", headers=headers, data="foobar").data
    headers["team_id"] = team1_id
    headers["id"] = file["file"]["id"]
    return file["file"]["id"]


# Products, topic, components
@pytest.fixture
def rhel_product(client_admin):
    return client_admin.get("/api/v1/products?where=label:RHEL").data["products"][0]


@pytest.fixture
def rhel_80_topic(client_admin, rhel_product):
    data = {
        "name": "RHEL-8.0",
        "product_id": rhel_product["id"],
        "component_types": ["compose"],
        "export_control": True,
    }
    return client_admin.post("/api/v1/topics", data=data).data["topic"]


@pytest.fixture
def rhel_80_topic_id(rhel_80_topic):
    return str(rhel_80_topic["id"])


@pytest.fixture
def rhel_80_component(client_admin, rhel_80_topic):
    data = {
        "topic_id": rhel_80_topic["id"],
        "name": "RHEL-8.0.0-20190926.n.0",
        "type": "compose",
    }
    return client_admin.post("/api/v1/components", data=data).data["component"]


@pytest.fixture
def rhel_80_component_id(rhel_80_component):
    return rhel_80_component["id"]


@pytest.fixture
def rhel_81_topic(client_admin, rhel_product):
    data = {
        "name": "RHEL-8.1",
        "product_id": rhel_product["id"],
        "component_types": ["compose"],
        "export_control": False,
    }
    return client_admin.post("/api/v1/topics", data=data).data["topic"]


@pytest.fixture
def rhel_81_component(client_admin, rhel_81_topic):
    data = {
        "topic_id": rhel_81_topic["id"],
        "name": "RHEL-8.1.0-20190926.n.0",
        "type": "compose",
    }
    return client_admin.post("/api/v1/components", data=data).data["component"]


@pytest.fixture
def openstack_product(client_admin):
    return client_admin.get("/api/v1/products?where=label:OPENSTACK").data["products"][
        0
    ]


@pytest.fixture
def openstack_171_topic(client_admin, openstack_product):
    data = {
        "name": "OSP17.1",
        "product_id": openstack_product["id"],
        "component_types": ["compose"],
        "export_control": False,
    }
    return client_admin.post("/api/v1/topics", data=data).data["topic"]


@pytest.fixture
def openstack_171_component(client_admin, openstack_171_topic):
    data = {
        "topic_id": openstack_171_topic["id"],
        "name": "RHOS-17.1-RHEL-9-20230831.n.1",
        "type": "compose",
    }
    return client_admin.post("/api/v1/components", data=data).data["component"]


@pytest.fixture
def openshift_product(client_admin):
    return client_admin.get("/api/v1/products?where=label:OPENSHIFT").data["products"][
        0
    ]


@pytest.fixture
def openshift_410_topic(client_admin, openshift_product):
    data = {
        "name": "OCP-4.10",
        "product_id": openshift_product["id"],
        "component_types": ["ocp"],
    }
    return client_admin.post("/api/v1/topics", data=data).data["topic"]


# Feeders
@pytest.fixture
def team_admin_feeder(client_admin, team_admin_id):
    data = {
        "name": "Admin feeder",
        "team_id": team_admin_id,
    }
    return client_admin.post("/api/v1/feeders", data=data).data["feeder"]


@pytest.fixture
def team1_feeder(client_admin, team1_id):
    data = {"name": "feeder_osp", "team_id": team1_id}
    return client_admin.post("/api/v1/feeders", data=data).data["feeder"]
