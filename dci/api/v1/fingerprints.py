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

import flask

from flask import json
from sqlalchemy import sql
from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import models
from dci.elasticsearch import es_client


_TABLE = models.FINGERPRINTS
_T_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {}


@api.route('/fingerprints', methods=['POST'])
@decorators.login_required
def create_fingerprint(user):
    """Create Fingerprint.
    """

    if not auth.is_admin(user) and role_id == auth.get_role_id('SUPER_ADMIN'):
        raise auth.UNAUTHORIZED

    values = v1_utils.common_values_dict(user)
    values.update(schemas.fingerprint.post(flask.request.json))

    with flask.g.db_conn.begin():
        query = _TABLE.insert().values(**values)
        flask.g.db_conn.execute(query)

    return flask.Response(json.dumps({'fingerprint': values}), 201,
                          headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/fingerprints', methods=['GET'])
@decorators.login_required
def get_all_fingerprints(user):
    """Get all Fingerprint.
    """
    args = schemas.args(flask.request.args.to_dict())

    query = v1_utils.QueryBuilder(_TABLE, args, _T_COLUMNS)

    query.add_extra_condition(_TABLE.c.state != 'archived')

    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name)

    return flask.jsonify({'fingerprints': rows, '_meta': {'count': nb_rows}})


@api.route('/fingerprints/<uuid:fp_id>', methods=['GET'])
@decorators.login_required
def get_fingerprint_by_id(user, fp_id):
    """Get Fingerprint by id.
    """
    fp = v1_utils.verify_existence_and_get(fp_id, _TABLE)
    return base.get_resource_by_id(user, fp,
                                   _TABLE, _EMBED_MANY)


@api.route('/fingerprints/<uuid:fp_id>', methods=['PUT'])
@decorators.login_required
def modify_fingerprint(user, fp_id):
    """Modify a Fingerprint.
    """

    if not auth.is_admin(user) and role_id == auth.get_role_id('SUPER_ADMIN'):
        raise auth.UNAUTHORIZED

    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = schemas.fingerprint.put(flask.request.json)

    v1_utils.verify_existence_and_get(fp_id, _TABLE)

    values['etag'] = utils.gen_etag()
    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == fp_id
    )
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Fingerprint', fp_id)

    return flask.Response(None, 204, headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/fingerprints/<uuid:fp_id>', methods=['DELETE'])
@decorators.login_required
def delete_fingerprint_by_id(user, fp_id):
    """... Fingerprint.
    """

    if not auth.is_admin(user) and role_id == auth.get_role_id('SUPER_ADMIN'):
        raise auth.UNAUTHORIZED

    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    if not auth.is_admin(user):
        raise auth.UNAUTHORIZED

    v1_utils.verify_existence_and_get(fp_id, _TABLE)

    with flask.g.db_conn.begin():
        values = {'state': 'archived'}
        where_clause = sql.and_(
            _TABLE.c.etag == if_match_etag,
            _TABLE.c.id == fp_id
        )
        query = _TABLE.update().where(where_clause).values(**values)
        result = flask.g.db_conn.execute(query)

        if not result.rowcount:
            raise dci_exc.DCIDeleteConflict('Fingerprint', fp_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/fingerprints/<uuid:fp_id>/jobs', methods=['GET'])
@decorators.login_required
def get_jobs_by_fingerprint(user, fp_id):
    """ Retrieve all the jobs that matches a specific fingerprint.
    """

    if not auth.is_admin(user) and role_id == auth.get_role_id('SUPER_ADMIN'):
        raise auth.UNAUTHORIZED

    fp = v1_utils.verify_existence_and_get(fp_id, _TABLE)

    result = flask.g.es_client.search(fp.fingerprint['regexp'])
    array = []
    if "error" not in result.keys():
        for found in result['hits']['hits']:
            array.append(found['fields']['job_id'][0])
    else:
        return flask.Response("{'error': 'elasticsearch not available'}", 500,
                              content_type='application/json')
    return flask.jsonify({'job_match': array })


@api.route('/fingerprints/<uuid:fp_id>/jobs', methods=['POST'])
@decorators.login_required
def run_fingerprint_on_jobs(user, fp_id):
    """ Check if a all job matches a specific fingerprint or any fingerprint.
    """

    if not auth.is_admin(user) and role_id == auth.get_role_id('SUPER_ADMIN'):
        raise auth.UNAUTHORIZED

    fp = v1_utils.verify_existence_and_get(fp_id, _TABLE)

    msg = {'event': 'fingerprints',
           'topic_id': str(fp['topic_id']),
           'fingerprint_id': str(fp_id)}
    flask.g.sender.send_json(msg)
    return flask.Response(None, 204,
                          content_type='application/json')

@api.route('/fingerprints/<uuid:fp_id>/jobs/<uuid:job_id>', methods=['GET'])
@decorators.login_required
def get_fingerprint_on_job(user, fp_id, job_id):
    """ Check if a specific job matches a specific fingerprint or any fingerprint.
    """

    if not auth.is_admin(user) and role_id == auth.get_role_id('SUPER_ADMIN'):
        raise auth.UNAUTHORIZED

    fp = v1_utils.verify_existence_and_get(fp_id, _TABLE)
    job = v1_utils.verify_existence_and_get(job_id, models.JOBS)

    result = flask.g.es_client.search_by_id(fp.fingerprint['regexp'], job_id)
    array = []
    if result['hits']['hits'][0]['fields']['job_id'][0]:
        return flask.jsonify({'job_match': 'true' })
    else:
        return flask.jsonify({'job_match': 'false' })


@api.route('/fingerprints/jobs/<uuid:job_id>', methods=['GET'])
@decorators.login_required
def get_fingerprints_on_job(user, fp_id):
    """ Check if a specific job matches a specific fingerprint or any fingerprint.
    """
    if not auth.is_admin(user) and role_id == auth.get_role_id('SUPER_ADMIN'):
        raise auth.UNAUTHORIZED

    job = v1_utils.verify_existence_and_get(job_id, models.JOBS)

    result = flask.g.es_client.search_by_id(fp.fingerprint['regexp'], job_id)
    array = []
    if result['hits']['hits'][0]['fields']['job_id'][0]:
        return flask.jsonify({'job_match': 'true' })
    else:
        return flask.jsonify({'fingerprint_match': 'false' })


@api.route('/fingerprints/<uuid:fp_id>/jobs/<uuid:job_id>', methods=['POST'])
@decorators.login_required
def run_fingerprint_on_job(user, fp_id):
    """ Check if a specific job matches a specific fingerprint or any fingerprint.
    """

    if not auth.is_admin(user) and role_id == auth.get_role_id('SUPER_ADMIN'):
        raise auth.UNAUTHORIZED

    fp = v1_utils.verify_existence_and_get(fp_id, _TABLE)

    msg = {'event': 'fingerprints',
           'topic_id': str(fp['topic_id']),
           'fingerprint_id': str(fp_id),
           'job_id': str(job_id)}
    flask.g.sender.send_json(msg)
    return flask.Response(None, 204,
                          content_type='application/json')


@api.route('/fingerprints/jobs/<uuid:job_id>', methods=['POST'])
@decorators.login_required
def run_fingerprints_on_job(user, fp_id):
    """ Do the action attached to all fingerprints a job matches.
    """

    if not auth.is_admin(user) and role_id == auth.get_role_id('SUPER_ADMIN'):
        raise auth.UNAUTHORIZED

    fp = v1_utils.verify_existence_and_get(fp_id, _TABLE)

    msg = {'event': 'fingerprints',
           'topic_id': str(fp['topic_id']),
           'job_id': str(job_id)}
    flask.g.sender.send_json(msg)
    return flask.Response(None, 204,
                          content_type='application/json')

@api.route('/fingerprints/jobs', methods=['POST'])
@decorators.login_required
def run_fingerprints_on_jobs(user):
    """ Finally the initial bulk tagging would look like.
    """

    if not auth.is_admin(user) and role_id == auth.get_role_id('SUPER_ADMIN'):
        raise auth.UNAUTHORIZED

    msg = {'event': 'fingerprints',
           'topic_id': str(fp['topic_id'])}
    flask.g.sender.send_json(msg)
    return flask.Response(None, 204,
                          content_type='application/json')


@api.route('/fingerprints/purge', methods=['GET'])
@decorators.login_required
def get_to_purge_archived_fingerprint(user):
    """Show purgeable items in Fingerprint.
    """
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/fingerprints/purge', methods=['POST'])
@decorators.login_required
def purge_fingerprint(user):
    """Purge Fingerprint.
    """
    return base.purge_archived_resources(user, _TABLE)
