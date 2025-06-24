# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
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

from datetime import timedelta
import sqlalchemy.orm as sa_orm

from dci.db import models2
from dci.common.time import get_utc_now


def get_jobs(session, offset, limit, unit, amount, status=None):
    delta = {unit: amount}
    query = session.query(models2.Job)
    if status:
        query = query.filter(models2.Job.status == status)
    query = query.filter(models2.Job.state != "archived")
    query = query.filter(models2.Job.updated_at >= (get_utc_now() - timedelta(**delta)))
    query = query.order_by(models2.Job.updated_at.asc())
    query = query.offset(offset)
    query = query.limit(limit)
    query = query.from_self()

    query = (
        query.options(sa_orm.selectinload("components"))
        .options(sa_orm.selectinload("jobstates"))
        .options(sa_orm.selectinload("jobstates.files"))
        .options(sa_orm.selectinload("files"))
        .options(sa_orm.selectinload("results"))
        .options(sa_orm.joinedload("pipeline", innerjoin=False))
        .options(sa_orm.joinedload("remoteci", innerjoin=True))
        .options(sa_orm.joinedload("topic", innerjoin=True))
        .options(sa_orm.joinedload("product", innerjoin=True))
        .options(sa_orm.joinedload("team", innerjoin=True))
        .options(sa_orm.joinedload("keys_values", innerjoin=False))
    )

    jobs = [j.serialize(ignore_columns=["data"]) for j in query.all()]

    return jobs


def get_job_by_id(session, job_id):
    query = session.query(models2.Job)
    query = query.filter(models2.Job.id == job_id)
    query = query.from_self()

    query = (
        query.options(sa_orm.selectinload("components"))
        .options(sa_orm.selectinload("jobstates"))
        .options(sa_orm.selectinload("jobstates.files"))
        .options(sa_orm.selectinload("files"))
        .options(sa_orm.selectinload("results"))
        .options(sa_orm.joinedload("pipeline", innerjoin=False))
        .options(sa_orm.joinedload("remoteci", innerjoin=True))
        .options(sa_orm.joinedload("topic", innerjoin=True))
        .options(sa_orm.joinedload("product", innerjoin=True))
        .options(sa_orm.joinedload("team", innerjoin=True))
        .options(sa_orm.joinedload("keys_values", innerjoin=False))
    )

    return query.one().serialize(ignore_columns=["data"])


def get_components(session, offset, limit, unit, amount):
    delta = {unit: amount}

    query = session.query(models2.Component)
    query = query.filter(models2.Component.state != "archived")
    query = query.filter(
        models2.Component.created_at >= (get_utc_now() - timedelta(**delta))
    )
    query = query.order_by(models2.Component.created_at.asc())

    query = query.options(sa_orm.selectinload("jobs"))

    query = query.offset(offset)
    query = query.limit(limit)

    jobs = [c.serialize() for c in query.all()]

    return jobs
