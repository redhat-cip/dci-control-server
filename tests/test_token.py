# -*- encoding: utf-8 -*-
#
# Copyright 2017 Red Hat, Inc.
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

from datetime import datetime, timedelta
import pytest

from dci.common import token


def test_gen_token():
    assert len(token.gen_token()) == 64
    assert len(token.gen_token(128)) == 128
    assert token.gen_token() != token.gen_token()


def test_format_string_to_sign():
    timestamp = datetime(2016, 5, 19, 13, 51, 59)

    formated = token.format_for_signature(
        'DELETE', 'application/json', timestamp, '/api/v1/boo/yah',
        'param=value&foo=bar',
        '41af286dc0b172ed2f1ca934fd2278de4a1192302ffa07087cea2682e7d372e3')

    assert formated == '''DELETE
application/json
2016-05-19 13:51:59Z
/api/v1/boo/yah
param=value&foo=bar
41af286dc0b172ed2f1ca934fd2278de4a1192302ffa07087cea2682e7d372e3'''


def test_gen_signature():
    timestamp = datetime(2016, 5, 19, 13, 51, 59)

    signature = token.gen_signature(
        '*}I)|u!)288|_WrH(C_^2\'#8,UMVpR:+lnd4Kt<TS;3~v)SQ%"s\'g[}<5C_c*\'{Z',
        'DELETE', 'application/json', timestamp, '/api/v1/boo/yah',
        'param=value&foo=bar',
        'lala')

    assert signature == \
        '8b267071e9690457205811e8a4464de3f822c7c4e3f6abbdd7a4bfcfa8132ecb'


def test_parse_client_id_bad():
    bad_format_message = 'Client id should match the following format: ' + \
        '"YYYY-MM-DD HH:MI:SSZ/<client_type>/<id>"'

    with pytest.raises(ValueError) as e_info:
        token.parse_client_id('pif!paf!pouf!')
    assert e_info.value.args[0] == bad_format_message

    with pytest.raises(ValueError) as e_info:
        token.parse_client_id('pif/paf')
    assert e_info.value.args[0] == bad_format_message

    with pytest.raises(ValueError) as e_info:
        token.parse_client_id('pif/paf/pouf/.')
    assert e_info.value.args[0] == bad_format_message

    with pytest.raises(ValueError) as e_info:
        token.parse_client_id('p/p/')
    assert e_info.value.args[0] == bad_format_message

    with pytest.raises(ValueError) as e_info:
        token.parse_client_id('p//p')
    assert e_info.value.args[0] == bad_format_message

    with pytest.raises(ValueError) as e_info:
        token.parse_client_id('pif/paf/pouf')


def test_parse_client_id_good():
    expected = {
        'timestamp': datetime(2016, 3, 21, 15, 37, 59),
        'client_type': 'foo',
        'id': '12890-abcdef',
    }
    client_id = '2016-03-21 15:37:59Z/foo/12890-abcdef'

    assert token.parse_client_id(client_id) == expected


# def _is_signature_timestamp_valid(timestamp):
#     return token.is_signature_valid(
#         '8b267071e9690457205811e8a4464de3f822c7c4e3f6abbdd7a4bfcfa8132ecb',
#         '*}I)|u!)288|_WrH(C_^2\'#8,UMVpR:+lnd4Kt<TS;3~v)SQ%"s\'g[}<5C_c*\'{Z',
#         'DELETE', 'application/json', timestamp, '/api/v1/boo/yah',
#         'param=value&foo=bar',
#         'lala')[0]

def test_is_signature_valid():
    # All correct
    args = [
        '*}I)|u!)288|_WrH(C_^2\'#8,UMVpR:+lnd4Kt<TS;3~v)SQ%"s\'g[}<5C_c*\'{Z',
        'DELETE', 'application/json', datetime.utcnow(), '/api/v1/boo/yah',
        'param=value&foo=bar', 'lala'
    ]
    signature = token.gen_signature(*args)
    assert token.is_signature_valid(signature, *args)

    # Timestamp was generated 4 minutes ago
    args = [
        '*}I)|u!)288|_WrH(C_^2\'#8,UMVpR:+lnd4Kt<TS;3~v)SQ%"s\'g[}<5C_c*\'{Z',
        'DELETE', 'application/json', datetime.utcnow() - timedelta(minutes=4),
        '/api/v1/boo/yah', 'param=value&foo=bar', 'lala'
    ]
    signature = token.gen_signature(*args)
    assert token.is_signature_valid(signature, *args)

    # Timestamp was generated 6 minutes ago
    args = [
        '*}I)|u!)288|_WrH(C_^2\'#8,UMVpR:+lnd4Kt<TS;3~v)SQ%"s\'g[}<5C_c*\'{Z',
        'DELETE', 'application/json', datetime.utcnow() - timedelta(minutes=6),
        '/api/v1/boo/yah', 'param=value&foo=bar', 'lala'
    ]
    signature = token.gen_signature(*args)
    assert not token.is_signature_valid(signature, *args)

    # Changing an element in the args
    args = [
        '*}I)|u!)288|_WrH(C_^2\'#8,UMVpR:+lnd4Kt<TS;3~v)SQ%"s\'g[}<5C_c*\'{Z',
        'DELETE', 'application/json', datetime.utcnow(),
        '/api/v1/boo/yah', 'param=value&foo=bar', 'lala'
    ]
    signature = token.gen_signature(*args)
    args[1] = 'PUT'
    assert not token.is_signature_valid(signature, *args)


def test_is_timestamp_in_bounds(monkeypatch):
    now = datetime(2016, 11, 11, 12, 50, 0)

    assert token.is_timestamp_in_bounds(datetime(2016, 11, 11, 12, 45, 10),
                                        now=now)
    assert token.is_timestamp_in_bounds(datetime(2016, 11, 11, 12, 54, 50),
                                        now=now)
    assert not token.is_timestamp_in_bounds(datetime(2016, 11, 11, 12, 44, 10),
                                            now=now)
    assert not token.is_timestamp_in_bounds(datetime(2016, 11, 11, 12, 55, 50),
                                            now=now)
