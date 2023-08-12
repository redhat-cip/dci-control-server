# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Red Hat, Inc
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

from sqlalchemy import orm
from sqlalchemy import exc
from dci.common import exceptions as dci_exc
from dci.common import utils


def get_resources_orm(table, filters=[], options=[]):
    query = flask.g.session.query(table)
    try:
        getattr(table, "state")
        query = query.filter(table.state != "archived")
    except AttributeError:
        pass
    for filter in filters:
        query = query.filter(filter)
    for option in options:
        query = query.options(option)
    return query.all()


def get_resource_orm(table, id, etag=None, options=[]):
    try:
        query = flask.g.session.query(table).filter(table.id == id)
        try:
            getattr(table, "state")
            query = query.filter(table.state != "archived")
        except AttributeError:
            pass

        if etag:
            query = query.filter(table.etag == etag)
        for option in options:
            query = query.options(option)
        return query.one()
    except orm.exc.NoResultFound:
        resource_name = table.__tablename__[0:-1]
        raise dci_exc.DCIException(
            message="%s not found" % resource_name, status_code=404
        )


def update_resource_orm(resource, data):
    for k, v in data.items():
        setattr(resource, k, v)
    setattr(resource, "etag", utils.gen_etag())
    try:
        flask.g.session.commit()
    except exc.IntegrityError:
        flask.g.session.rollback()
        raise dci_exc.DCIException(
            message="We are unable to update this resource. A similar resource already exists.",
            status_code=409,
        )
    except Exception:
        flask.g.session.rollback()
        raise dci_exc.DCIException(
            message="We are unable to update this resource. Please contact a DCI administrator."
        )


def create_resource_orm(table, data):
    try:
        resource = table(**data)
        resource_serialized = resource.serialize()
        flask.g.session.add(resource)
        flask.g.session.commit()
        return resource_serialized
    except exc.IntegrityError:
        flask.g.session.rollback()
        raise dci_exc.DCIException(
            message="We are unable to create this resource. A similar resource already exists.",
            status_code=409,
        )
    except Exception:
        flask.g.session.rollback()
        raise dci_exc.DCIException(
            message="We are unable to create this resource. Please contact a DCI administrator."
        )


def get_archived_resources_query(table):
    return flask.g.session.query(table).filter(table.state == "archived")


def get_to_purge_archived_resources(user, table):
    """List the entries to be purged from the database."""

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    archived_resources = [
        r.serialize() for r in get_archived_resources_query(table).all()
    ]

    return flask.jsonify(
        {
            table.__tablename__: archived_resources,
            "_meta": {"count": len(archived_resources)},
        }
    )


def purge_archived_resources(user, table):
    """Remove the entries to be purged from the database."""

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    try:
        get_archived_resources_query(table).delete()
        flask.g.session.commit()
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e), status_code=409)
    return flask.Response(None, 204, content_type="application/json")


def get_resources_to_purge_orm(user, table):
    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    query = flask.g.session.query(table).filter(table.state == "archived")
    archived_resources = [resource.serialize() for resource in query.all()]

    return flask.jsonify(
        {
            table.__tablename__: archived_resources,
            "_meta": {"count": len(archived_resources)},
        }
    )


def purge_archived_resources_orm(user, table):
    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    flask.g.session.query(table).filter(table.state == "archived").delete()
    try:
        flask.g.session.commit()
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e), status_code=409)

    return flask.Response(None, 204, content_type="application/json")
