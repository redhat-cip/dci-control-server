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

from __future__ import unicode_literals

from datetime import datetime, timedelta
import hashlib
import hmac
import random
import string

from dci.common import exceptions as dci_exc
import six




def gen_secret(length=64):
    """ Generates a secret of given length
    """
    charset = string.ascii_letters + string.digits
    return ''.join(random.SystemRandom().choice(charset)
                   for _ in range(length))


def format_for_signature(http_verb, content_type, timestamp, url,
                         query_string, payload_hash):
    """Returns the string used to generate the signature in a correctly
    formatter manner.
    """
    return '\n'.join((
        http_verb,
        content_type,
        timestamp.strftime('%Y-%m-%d %H:%M:%SZ'),
        url,
        query_string,
        str(payload_hash)
    )).encode('utf-8')


def gen_signature(secret, http_verb, content_type, timestamp, url,
                  query_string, payload):
    """Generates a signature compatible with DCI for the parameters passed"""

    if isinstance(http_verb, six.binary_type):
        http_verb = http_verb.decode('utf-8')
    if isinstance(content_type, six.binary_type):
        content_type = content_type.decode('utf-8')
    if isinstance(url, six.binary_type):
        url = url.decode('utf-8')
    if isinstance(query_string, six.binary_type):
        query_string = query_string.decode('utf-8')
    payload_hash = hashlib.sha256(payload).hexdigest()
    stringtosign = format_for_signature(
        http_verb=http_verb,
        content_type=content_type,
        timestamp=timestamp,
        url=url,
        query_string=query_string,
        payload_hash=payload_hash
    )

    if not isinstance(secret, six.binary_type):
        secret = secret.encode('utf-8')
    return hmac.new(secret,
                    stringtosign,
                    hashlib.sha256).hexdigest()


def compare_digest(foo, bar):
    """ Compares two hmac digests.
    NOTE: this uses hmac.compare_digest() if possible, a simple == else.
          hmac.compare_digest is available only in python≥(2.7.7,3.3)"""
    f = getattr(hmac, 'compare_digest', lambda a, b: a == b)
    if not isinstance(foo, six.binary_type):
        foo = foo.encode('utf-8')
    return f(foo, bar)


def is_timestamp_in_bounds(timestamp, max_drift=timedelta(minutes=5),
                           now=None):
    if now is None:
        now = datetime.utcnow()
    return abs(now - timestamp) < max_drift


def is_valid(their_signature,
             secret, http_verb, content_type, timestamp, url,
             query_string, payload):
    """Verifies the remote signature against a locally computed signature and
    ensures the timestamp lies within ±5 minutes of current time.

    Raises an exception if there's any issue with time or signature."""
    local_signature = gen_signature(secret, http_verb, content_type, timestamp,
                                    url, query_string, payload).encode('utf-8')

    if not is_timestamp_in_bounds(timestamp):
        raise dci_exc.DCIException('Timestamp out of bounds (±5 minutes of '
                                   'current server time). Is you clock '
                                   'correctly set ?',
                                   status_code=401)

    if not compare_digest(their_signature, local_signature):
        raise dci_exc.DCIException('Bad signature.',
                                   status_code=401)
