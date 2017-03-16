#!/usr/bin/env python
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


import json
import pprint
import logging
import sys

from sqlalchemy import sql, func

from dci import dci_config
from dci.db import models
from dci.api.v1 import transformations
from dci.api.v1 import utils

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

conf = dci_config.generate_conf()
engine = dci_config.get_engine(conf).connect()

_TABLE = models.FILES
_FILES_FOLDER = dci_config.generate_conf()['FILES_UPLOAD_FOLDER']


def get_junit_results(file):
    file_path = utils.build_file_path(
        _FILES_FOLDER, file['team_id'], file['id'], create=False)
    logger.debug(file_path)
    return transformations.junit2dict(file_path)


def get_next_files_metadata(offset, limit):
    query = (sql
             .select([_TABLE])
             .offset(offset)
             .limit(limit)
             .where(_TABLE.c.mime == 'application/junit'))
    return engine.execute(query)


def main(callback):
    """
    Temporary script to parse tests files
    and fill the test_results table.
    This mechanism will be done in the file controller in the future
    :param callback: method execute with every parsed test_result
    """
    query = (sql
             .select([func.count(_TABLE.c.id)])
             .select_from(_TABLE)
             .where(_TABLE.c.mime == 'application/junit'))
    nb_row = engine.execute(query).scalar()

    offset = 0
    while offset < nb_row:
        files_meta = get_next_files_metadata(offset, limit=1000)
        for file_meta in files_meta:
            try:
                file = dict(file_meta)
                junit_results = get_junit_results(file)
                test_result = transformations.format_test_result(junit_results)
                test_result['created_at'] = file['created_at'].isoformat()
                test_result['file_id'] = str(file['id'])
                test_result['job_id'] = str(file['job_id'])
                callback(test_result)
            except Exception as e:
                logger.exception(e)
                logger.debug(dict(file_meta))
        offset += files_meta.rowcount


def pretty_print(test_result):
    pprint.pprint(json.dumps(test_result))


if __name__ == '__main__':
    args = sys.argv
    if len(args) == 1:
        main(pretty_print)
