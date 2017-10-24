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

from dci.common import exceptions as dci_exc
from dci.common import signature


def test_gen_secret():
    assert len(signature.gen_secret()) == 64
    assert len(signature.gen_secret(128)) == 128
    assert signature.gen_secret() != signature.gen_secret()


def test_format_string_to_sign():
    timestamp = datetime(2016, 5, 19, 13, 51, 59)

    payload_hash = \
        b'41af286dc0b172ed2f1ca934fd2278de4a1192302ffa07087cea2682e7d372e3'
    formated = signature.format_for_signature(
        http_verb=b'DELETE',
        content_type=b'application/json',
        timestamp=timestamp,
        url=b'/api/v1/boo/yah',
        query_string=b'param=value&foo=bar',
        payload_hash=payload_hash)

    assert formated == b'''DELETE
application/json
2016-05-19 13:51:59Z
/api/v1/boo/yah
param=value&foo=bar
41af286dc0b172ed2f1ca934fd2278de4a1192302ffa07087cea2682e7d372e3'''


def test_gen_signature():
    timestamp = datetime(2016, 5, 19, 13, 51, 59)

    secret = \
        b'*}I)|u!)288|_WrH(C_^2\'#8,UMVpR:+lnd4Kt<TS;3~v)SQ%"s\'g[}<5C_c*\'{Z'
    sig = signature.gen_signature(
        secret=secret,
        http_verb=b'DELETE',
        content_type=b'application/json',
        timestamp=timestamp,
        url=b'/api/v1/boo/yah',
        query_string=b'param=value&foo=bar',
        payload=b'lala')

    assert sig == \
        '8b267071e9690457205811e8a4464de3f822c7c4e3f6abbdd7a4bfcfa8132ecb'


def signature_kwargs(delta_minutes=0):
    secret = \
        b'*}I)|u!)288|_WrH(C_^2\'#8,UMVpR:+lnd4Kt<TS;3~v)SQ%"s\'g[}<5C_c*\'{Z'
    return {
        'secret': secret,
        'http_verb': b'DELETE',
        'content_type': b'application/json',
        'timestamp': datetime.utcnow() + timedelta(minutes=delta_minutes),
        'url': b'/api/v1/boo/yah',
        'query_string': b'param=value&foo=bar',
        'payload': b'lala'
    }


def test_signature_is_valid():
    kwargs = signature_kwargs()
    kwargs['their_signature'] = signature.gen_signature(**kwargs)\
        .encode('utf-8')
    signature.is_valid(**kwargs)


def test_signature_4min_old_is_valid():
    # Timestamp was generated 4 minutes ago
    kwargs = signature_kwargs(-4)
    kwargs['their_signature'] = signature.gen_signature(**kwargs)\
        .encode('utf-8')
    signature.is_valid(**kwargs)


def test_signature_6min_old_is_invalid():
    # Timestamp was generated 6 minutes ago
    kwargs = signature_kwargs(-6)
    kwargs['their_signature'] = signature.gen_signature(**kwargs)\
        .encode('utf-8')
    with pytest.raises(dci_exc.DCIException,
                       match='Timestamp out of bounds.*'):
        signature.is_valid(**kwargs)


def test_signature_bad_http_verb_is_invalid():
    kwargs = signature_kwargs()
    kwargs['their_signature'] = signature.gen_signature(**kwargs)\
        .encode('utf-8')
    # Using a different verb than the one used for the signature
    kwargs['http_verb'] = b'PUT'
    with pytest.raises(dci_exc.DCIException, match='Bad signature'):
        signature.is_valid(**kwargs)


def test_timestamp_is_in_bounds_earlier():
    now = datetime(2016, 11, 11, 12, 50, 0)

    assert signature.is_timestamp_in_bounds(
        datetime(2016, 11, 11, 12, 45, 10),
        now=now)


def test_timestamp_is_in_bounds_later():
    now = datetime(2016, 11, 11, 12, 50, 0)

    assert signature.is_timestamp_in_bounds(
        datetime(2016, 11, 11, 12, 54, 50),
        now=now)


def test_timestamp_is_not_in_bounds_earlier():
    now = datetime(2016, 11, 11, 12, 50, 0)

    assert not signature.is_timestamp_in_bounds(
        datetime(2016, 11, 11, 12, 44, 10),
        now=now)


def test_timestamp_is_not_in_bounds_later():
    now = datetime(2016, 11, 11, 12, 50, 0)

    assert not signature.is_timestamp_in_bounds(
        datetime(2016, 11, 11, 12, 55, 50),
        now=now)
