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

from dci.api.v1 import utils
from dci.common import exceptions as dci_exc
from uuid import UUID

import datetime
import pytest
import sqlalchemy as sa

# Use a fake model for testing
stub = utils.embed(join=sa.Table('stubs', sa.MetaData()))


def test_verify_embed_list():
    valid_embed_list = {'a': stub, 'a.b': stub, 'a.b.c': stub}
    embed_list = ['a', 'a.b.c', 'a.b']

    qb = utils.QueryBuilder(None, embed=valid_embed_list)
    qb.join(embed_list)

    assert len(qb._join) == 3


def test_verify_embed_list_not_valid():
    valid_embed_list = {'a': stub, 'a.b': stub, 'a.b.c': stub}
    embed_list = ['a', 'a.b', 'kikoolol']

    qb = utils.QueryBuilder(None, embed=valid_embed_list)

    assert pytest.raises(dci_exc.DCIException, qb.join, embed_list)


def test_group_embedded_resources():
    embed_list = ['a', 'b', 'a.c']
    row = {'id': '12', 'name': 'lol',
           'a_id': '123', 'a_name': 'lol2', 'a_c_id': '12345',
           'b_id': '1234', 'b_name': 'lol3',
           'a.c_name': 'mdr1'}
    result = utils.group_embedded_resources(embed_list, row)

    assert {'id': '12', 'name': 'lol',
            'a': {'id': '123', 'name': 'lol2',
                  'c': {'id': '12345', 'name': 'mdr1'}},
            'b': {'id': '1234', 'name': 'lol3'}} == result


def test_common_values_dict_correct_fields():
    user = {'team_name': 'team42'}

    mydict = utils.common_values_dict(user)
    expected_keys = ['id', 'created_at', 'updated_at', 'etag']
    assert sorted(mydict.keys()) == sorted(expected_keys)


def test_common_values_dict_correct_fields_type():
    user = {'team_name': 'team42'}

    mydict = utils.common_values_dict(user)
    assert UUID(mydict['id'], version=4)
    assert UUID(mydict['etag'], version=4)

    assert datetime.datetime.strptime(
        mydict['created_at'], '%Y-%m-%dT%H:%M:%S.%f'
    )
    assert datetime.datetime.strptime(
        mydict['updated_at'], '%Y-%m-%dT%H:%M:%S.%f'
    )
