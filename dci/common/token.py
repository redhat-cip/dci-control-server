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

from datetime import datetime, timedelta
import hashlib
import hmac
import random
import string


def gen_token(length=64):
    """ Generates a token of given length
    """
    charset = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.SystemRandom().choice(charset)
                   for _ in range(length))


def _format_for_signature(http_verb, content_type, timestamp, url,
                          query_string, payload_hash):
    """Returns the string used to generate the signature in a correctly
    formatter manner.
    """
    return '\n'.join((http_verb,
                      content_type,
                      timestamp.strftime('%Y-%m-%d %H:%M:%SZ'),
                      url,
                      query_string,
                      payload_hash))


def gen_signature(secret, http_verb, content_type, timestamp, url,
                  query_string, payload):
    """Generates a signature compatible with DCI for the parameters passed"""
    payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    stringtosign = _format_for_signature(
        http_verb,
        content_type,
        timestamp,
        url,
        query_string,
        payload_hash
    )

    return hmac.new(secret.encode('utf-8'),
                    stringtosign.encode('utf-8'),
                    hashlib.sha256).hexdigest()


# FIXME: this should go into the client instead !
# def gen_headers(remoteci_id, secret, http_verb, content_type, url,
#                 query_string, payload):
#     timestamp = datetime.utcnow()
#     client_id = '%s/remoteci/%s' % (timestamp.strftime('%Y-%m-%d %H:%M:%SZ'),
#                                     remoteci_id)
#     signature = _gen_signature(secret, http_verb, content_type, timestamp,
#                                url, query_string, payload)
#
#     return {
#         'DCI-Client-ID': client_id,
#         'DCI-Auth-Signature': signature,
#     }


def compare_digest(foo, bar):
    """ Compares two hmac digests.
    NOTE: this uses hmac.compare_digest() if possible, a simple == else.
          hmac.compare_digest is available only in python≥(2.7.7,3.3)"""
    f = getattr(hmac, 'compare_digest', lambda a, b: a == b)
    return f(foo, bar)


def parse_client_id(client_id):
    """Extracts timestamp, client type and resource id from a DCI-Client-ID
    header.
    Returns a hash with the three values.
    Throws an exception if the format is bad or if strptime fails."""
    bad_format_exception = \
        ValueError('Client id should match the following format: ' +
                   '"YYYY-MM-DD HH:MI:SSZ/<client_type>/<id>"')

    client_id = client_id.split('/')
    if len(client_id) != 3 or not all(client_id):
        raise bad_format_exception

    return {
        'timestamp': datetime.strptime(client_id[0], '%Y-%m-%d %H:%M:%SZ'),
        'client_type': client_id[1],
        'id': client_id[2],
    }


def is_signature_valid(remote_signature,
                       secret, http_verb, content_type, timestamp, url,
                       query_string, payload):
    """Verifies the remote signature against a locally computed signature and
    ensures the timestamp lies within ±5 minutes of current time.

    Returns a tuple of two booleans indicating the validity of the timestamp
    and the signature, respectively. (timestamp_ok, signature_ok)"""
    local_signature = gen_signature(secret, http_verb, content_type, timestamp,
                                    url, query_string, payload)
    time_difference = abs(datetime.utcnow() - timestamp)

    return (
        time_difference < timedelta(minutes=5),
        compare_digest(remote_signature, local_signature)
    )
