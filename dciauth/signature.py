#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the 'License'); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import datetime
import hashlib
import hmac
import json

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

DATETIME_FORMAT = '%Y%m%dT%H%M%SZ'
DCI_ALGORITHM = 'DCI-HMAC-SHA256'
DCI_DATETIME_HEADER = 'DCI-Datetime'


def _hash_payload(payload):
    if payload:
        string_payload = json.dumps(payload)
    else:
        string_payload = ''
    return hashlib.sha256(string_payload.encode('utf-8')).hexdigest()


def _create_string_to_sign(method, content_type, timestamp, url, query_string, hashed_payload):
    elements = (method, content_type, timestamp, url, query_string, hashed_payload,)
    return '\n'.join(elements)


def _sign(secret, string_to_sign):
    return hmac.new(
        secret.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha256).hexdigest()


def calculate_signature(secret, method, headers, url, query_string, payload):
    hashed_payload = _hash_payload(payload)
    timestamp = headers.get(DCI_DATETIME_HEADER, '')
    content_type = headers.get('Content-type', '')
    string_to_sign = _create_string_to_sign(
        method,
        content_type,
        timestamp,
        url,
        query_string,
        hashed_payload,
    )
    return _sign(secret, string_to_sign)


def get_signature_from_headers(headers):
    authorization_header = headers.get('Authorization', '')
    if DCI_ALGORITHM in authorization_header:
        return authorization_header.split(' ')[1]
    return ''


def _get_sorted_query_string(params):
    sorted_params = sorted(params.items(), key=lambda val: val[0])
    return urlencode(sorted_params)


def generate_headers_with_secret(secret, method, content_type, url, params, payload):
    hashed_payload = _hash_payload(payload)
    now = datetime.datetime.utcnow()
    dci_datetime = now.strftime(DATETIME_FORMAT)
    query_string = _get_sorted_query_string(params)
    string_to_sign = _create_string_to_sign(
        method,
        content_type,
        dci_datetime,
        url,
        query_string,
        hashed_payload,
    )
    signature = _sign(secret, string_to_sign)
    return {
        'Authorization': '%s %s' % (DCI_ALGORITHM, signature),
        'Content-Type': content_type,
        DCI_DATETIME_HEADER: dci_datetime
    }


def equals(client_signature, header_signature):
    return hmac.compare_digest(client_signature, header_signature)


def is_expired(headers):
    timestamp = headers.get(DCI_DATETIME_HEADER, '')
    if timestamp:
        now = datetime.datetime.utcnow()
        timestamp = datetime.datetime.strptime(timestamp, DATETIME_FORMAT)
        return abs(now - timestamp) > datetime.timedelta(minutes=5)
    return False
