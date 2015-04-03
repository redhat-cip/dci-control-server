# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
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

import server.db.api as api
from server.db.models import Environment
from server.db.models import File
from server.db.models import Job
from server.db.models import Platform
from server.db.models import Scenario
from server.db.models import session


session.query(Job).delete()
session.query(File).delete()
session.query(Environment).delete()
session.query(Platform).delete()
session.query(Scenario).delete()

platform = Platform(name='boa2')
environment = Environment(name="RH7.0-3nodes")
scenario = Scenario(
    name='my test scenario',
    content='#!/bin/sh\necho roberto\n')

session.add_all([
    platform,
    environment,
    scenario,
    Platform(name='boa3'),
    Environment(name="RH7.0-7nodes"),
    Environment(name="RH7.0-11nodes"),
    Scenario(name="Yet another scenario", content="bob"),
])
session.flush()
session.refresh(environment)
session.refresh(platform)
session.refresh(scenario)
session.add(Job(
    environment_id=environment.id,
    platform_id=platform.id,
    scenario_id=scenario.id))
session.commit()

i = 0
while i < 7:
    i += 1
    job_info = api.get_job_by_platform(platform.id)
    jobstate_id = api.create_jobstate(job_info['job_id'])['jobstate_id']
    api.create_jobstate(job_info['job_id'], comment='Step 1')
    api.create_file(
        name='step_1.log',
        content='The log of the step one',
        mime='text/plain',
        jobstate_id=jobstate_id,
    )
    jobstate_id = api.create_jobstate(
        job_info['job_id'], comment='Step 2')['jobstate_id']
    api.create_file(
        name='step_2.log',
        content='A log generated during step 2',
        mime='text/plain',
        jobstate_id=jobstate_id,
    )
    jobstate_id = api.create_jobstate(
        job_info['job_id'], comment='Step 3', status='success')['jobstate_id']
    api.create_file(
        name='a filename',
        content='this is a blabla',
        mime='text/plain',
        jobstate_id=jobstate_id
    )
