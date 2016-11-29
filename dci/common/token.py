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


def _digest_request(secret, request):
    h = hmac.new(secret.encode(), digestmod=hashlib.sha256)
    h.update(request.url.encode(request.charset or 'utf-8'))
    if request.data:
        h.update(h.data.encode(request.charset or 'utf-8'))
    return h


def compare_digest(foo, bar):
    f = getattr(hmac, 'compare_digest', lambda a, b: a == b)
    # NOTE(fc): hmac.compare_digest available in python≥(2.7,3.3)
    return f(foo, bar)
