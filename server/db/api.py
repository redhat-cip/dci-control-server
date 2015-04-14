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

from sqlalchemy.sql import text

from server.db.models import engine
from server.db.models import Environment
from server.db.models import File
from server.db.models import Job
from server.db.models import Jobstate
from server.db.models import Platform
from server.db.models import Scenario
from server.db.models import session


def get_job_by_platform(platform_id):
    """Return the first scenario_id that has not be associated to this platform.
    """
    s = text(
        """
SELECT

  scenarios.id, environments.id, MAX(jobstates.created_at)

FROM

  scenarios

CROSS JOIN

  environments

LEFT JOIN

jobs

ON jobs.scenario_id=scenarios.id

AND jobs.environment_id=environments.id

AND jobs.platform_id=:platform_id

LEFT JOIN

jobstates AS jobstates

ON jobstates.job_id=jobs.id

GROUP BY scenarios.id, environments.id

ORDER BY MAX(jobstates.created_at) ASC NULLS FIRST

LIMIT 1""")

    r = engine.execute(s, platform_id=platform_id)
    record = r.fetchone()
    scenario = session.query(Scenario).get(str(record[0]))
    environment = session.query(Environment).get(str(record[1]))
    platform = session.query(Platform).get(platform_id)
    job = Job(
        environment_id=environment.id,
        platform_id=platform.id,
        scenario_id=scenario.id)
    session.add(job)
    session.commit()
    session.refresh(job)
    session.add(
        Jobstate(job_id=job.id, status='new')
    )
    session.commit()

    # NOTE(Gonéri): loop to get the father environments URL
    url_list = [environment.url]
    while environment.environment:
        environment = environment.environment
        url_list.insert(0, environment.url)

    return {'job_id': job.id,
            'content': scenario.content,
            'url': url_list}


def create_file(name, jobstate_id, content, mime, checksum=None):
    filen = File(
        name=name,
        content=content,
        mime=mime,
        jobstate_id=jobstate_id)
    session.add(filen)
    session.flush()
    session.refresh(filen)
    return {'file_id': filen.id}


def create_jobstate(job_id, status='ongoing', comment=None):
    jobstate = Jobstate(job_id=job_id, status=status, comment=comment)
    session.add(jobstate)
    session.commit()
    session.refresh(jobstate)
    return {'jobstate_id': jobstate.id}
