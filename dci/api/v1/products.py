# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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
from flask import json

from sqlalchemy import exc as sa_exc
import sqlalchemy.orm as sa_orm
from sqlalchemy import sql

from dci import decorators
from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci.api.v1 import teams
from dci.common import audits
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    check_json_is_valid,
    create_product_schema,
    update_product_schema,
    add_team_to_product_schema,
    check_and_get_args
)
from dci.common import utils
from dci.db import declarative as d
from dci.db import models
from dci.db import models2

_TABLE = models.PRODUCTS
_T_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {
    'topics': True
}


@api.route('/products', methods=['POST'])
@decorators.login_required
@audits.log
def create_product(user):
    values = flask.request.json
    check_json_is_valid(create_product_schema, values)
    values.update(v1_utils.common_values_dict())

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    if not values['label']:
        values.update({'label': values['name'].upper()})

    try:
        p = models2.Product(**values)
        p_serialized = p.serialize()
        flask.g.session.add(p)
        flask.g.session.commit()
    except sa_exc.IntegrityError as ie:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(ie), status_code=409)
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e))

    return flask.Response(
        json.dumps({'product': p_serialized}), 201,
        headers={'ETag': values['etag']}, content_type='application/json'
    )


@api.route('/products/<uuid:product_id>', methods=['PUT'])
@decorators.login_required
def update_product(user, product_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = flask.request.json
    check_json_is_valid(update_product_schema, values)

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    values['etag'] = utils.gen_etag()

    try:
        flask.g.session.query(models2.Product).\
            filter(models2.Product.id == product_id).\
            filter(models2.Product.etag == if_match_etag).\
            update(values)
        flask.g.session.commit()
    except sa_exc.IntegrityError as ie:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(ie), status_code=409)
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e))

    p = flask.g.session.query(models2.Product).filter(models2.Product.id == product_id).one()
    if not p:
        raise dci_exc.DCIException(message="unable to return product", status_code=400)

    return flask.Response(
        json.dumps({'product': p.serialize()}), 200, headers={'ETag': values['etag']},
        content_type='application/json')


@api.route('/products', methods=['GET'])
@decorators.login_required
def get_all_products(user):
    args = check_and_get_args(flask.request.args.to_dict())

    q = flask.g.session.query(models2.Product).\
        filter(models2.Product.state != 'archived').\
        options(sa_orm.joinedload('topics'))
    q = d.handle_args(q, models2.Product, args)

    if (user.is_not_super_admin() and user.is_not_read_only_user()
        and user.is_not_epm()):
        _JPT = models2.JOIN_PRODUCTS_TEAMS
        q = q.join(_JPT, sql.and_(_JPT.c.product_id == models2.Product.id,
                                  _JPT.c.team_id.in_(user.teams_ids)))

    nb_products = q.count()
    q = d.handle_pagination(q, args)
    products = q.all()
    products = list(map(lambda p: p.serialize(), products))

    return flask.jsonify({'products': products, '_meta': {'count': nb_products}})


@api.route('/products/<uuid:product_id>', methods=['GET'])
@decorators.login_required
def get_product_by_id(user, product_id):
    try:
        q = flask.g.session.query(models2.Product).\
            filter(models2.Product.state != 'archived').\
            filter(models2.Product.id == product_id).\
            options(sa_orm.joinedload('topics'))
        if (user.is_not_super_admin() and user.is_not_read_only_user()
           and user.is_not_epm()):
            _JPT = models2.JOIN_PRODUCTS_TEAMS
            q = q.join(_JPT, sql.and_(_JPT.c.product_id == models2.Product.id,
                                      _JPT.c.team_id.in_(user.teams_ids)))
        p = q.one()
    except sa_orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="product not found", status_code=404)

    return flask.Response(
        json.dumps({'product': p.serialize()}), 200, headers={'ETag': p.etag},
        content_type='application/json')


@api.route('/products/<uuid:product_id>', methods=['DELETE'])
@decorators.login_required
def delete_product_by_id(user, product_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    v1_utils.verify_existence_and_get(product_id, _TABLE)

    values = {'state': 'archived'}
    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == product_id
    )

    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Product deletion error',
                                  product_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/products/<uuid:product_id>/teams', methods=['POST'])
@decorators.login_required
def add_team_to_product(user, product_id):
    values = flask.request.json
    check_json_is_valid(add_team_to_product_schema, values)

    team_id = values.get('team_id')
    product = v1_utils.verify_existence_and_get(product_id, _TABLE)
    team_id = v1_utils.verify_existence_and_get(team_id, models.TEAMS,
                                                get_id=True)

    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    values = {'product_id': product['id'],
              'team_id': team_id}
    query = models.JOIN_PRODUCTS_TEAMS.insert().values(**values)
    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(
            models.JOIN_PRODUCTS_TEAMS.name, "product_id, team_id"
        )

    result = json.dumps(values)
    return flask.Response(result, 201, content_type='application/json')


@api.route('/products/<uuid:product_id>/teams/<uuid:team_id>', methods=['DELETE'])
@decorators.login_required
def delete_team_from_product(user, product_id, team_id):
    product = v1_utils.verify_existence_and_get(product_id, _TABLE)
    team_id = v1_utils.verify_existence_and_get(team_id, models.TEAMS,
                                                get_id=True)

    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    JPT = models.JOIN_PRODUCTS_TEAMS
    where_clause = sql.and_(JPT.c.product_id == product['id'],
                            JPT.c.team_id == team_id)
    query = JPT.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Products_teams', team_id)

    return flask.Response(None, 204, content_type='application/json')


def serialize_teams(rows):
    result = []
    for row in rows:
        new_row = {}
        for k, v in row.items():
            if not k.startswith("products_teams"):
                new_key = k.split('_')[1]
                new_row[new_key] = v
        result.append(new_row)
    return result


@api.route('/products/<uuid:product_id>/teams', methods=['GET'])
@decorators.login_required
def get_all_teams_from_product(user, product_id):
    product = v1_utils.verify_existence_and_get(product_id, _TABLE)

    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    args = check_and_get_args(flask.request.args.to_dict())
    _JPT = models.JOIN_PRODUCTS_TEAMS
    query = v1_utils.QueryBuilder(models.TEAMS, args,
                                  teams._T_COLUMNS,
                                  root_join_table=_JPT,
                                  root_join_condition=sql.and_(_JPT.c.product_id == product['id'],  # noqa
                                                               _JPT.c.team_id == models.TEAMS.c.id))  # noqa
    rows = query.execute(fetchall=True)

    return flask.jsonify({'teams': serialize_teams(rows),
                          '_meta': {'count': len(rows)}})


@api.route('/products/purge', methods=['GET'])
@decorators.login_required
def get_to_purge_archived_products(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/products/purge', methods=['POST'])
@decorators.login_required
def purge_archived_products(user):
    return base.purge_archived_resources(user, _TABLE)
