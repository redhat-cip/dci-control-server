# -*- encoding: utf-8 -*-
#
# Copyright 2018 Red Hat, Inc.
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
import mock

from dci.common.utils import gen_etag
from dci.common.utils import gen_uuid

def test_gen_uuid():
    assert type(gen_uuid()) is bytes


@mock.patch('dci.common.utils.gen_uuid')
def test_gen_etag(gen_uuid_fn):
    gen_uuid_fn.return_value = b'79c3e143-1461-4383-9d7c-a54996ebb02f'
    assert gen_etag() == 'b46a0dedacdb9e79682c48b1b12e0040'
