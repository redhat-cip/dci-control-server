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

import six.moves
from sqlalchemy import sql, func

from dci import dci_config
from dci.api.v1 import tests_results
from dci.db import models
from dci.api.v1 import transformations

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

conf = dci_config.generate_conf()
engine = dci_config.get_engine(conf).connect()
swift = dci_config.get_store('files')

_TABLE = models.FILES
_FILES_FOLDER = dci_config.generate_conf()['FILES_UPLOAD_FOLDER']


def get_junit_results(file):
    file_path = swift.build_file_path(file['team_id'], file['job_id'],
                                      file['id'])
    logger.debug('get junit results for %s' % file_path)
    content_file = swift.get(file_path)[1]
    return transformations.junit2dict(content_file)


def get_next_files_metadata(offset, limit):
    query = (sql
             .select([_TABLE])
             .offset(offset)
             .limit(limit)
             .where(_TABLE.c.mime == 'application/junit'))
    return engine.execute(query)


def delete_tests_results_table():
    engine.execute(models.TESTS_RESULTS.delete())


def main(callback):
    """
    Temporary script to parse tests files
    and fill the tests_results table.
    This mechanism will be done in the file controller in the future
    :param callback: method execute with every test_result
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
            file_dict = dict(file_meta)
            try:
                junit_results = get_junit_results(file_dict)
                junit_results['created_at'] = file_dict['created_at']
                junit_results['file_id'] = file_dict['id']
                junit_results['job_id'] = file_dict['job_id']
                callback(junit_results)
            except Exception as e:
                logger.exception(e)
                logger.debug(file_dict)
        offset += files_meta.rowcount


def pretty_print(test_results):
    test_results['created_at'] = test_results['created_at'].isoformat()
    test_results['file_id'] = str(test_results['file_id'])
    test_results['job_id'] = str(test_results['job_id'])
    pprint.pprint(json.dumps(test_results))


def create_test_results(test_results):
    pretty_print(test_results)
    tests_results.create_test_results(engine, test_results)
    logger.debug('create test results for job_id: '
                 '%s' % str(test_results['job_id']))


if __name__ == '__main__':
    args = sys.argv
    if len(args) == 1:
        main(pretty_print)
        print('\nRun `%s run` if you want full run' % args[0])

    if len(args) == 2 and args[1] == 'run':
        while True:
            print('Be carefull this script will delete tests_results table '
                  'and reparse all junit files:')
            print('')
            i = six.moves.input('Continue ? [y/N] ').lower()
            if not i or i == 'n':
                print('exiting')
                sys.exit(0)
            if i == 'y':
                break
        delete_tests_results_table()
        main(create_test_results)
