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

from dci.common import exceptions

from elasticsearch import Elasticsearch
from elasticsearch import exceptions as es_exceptions
import functools


def catchConnectionError(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except es_exceptions.ConnectionError:
            raise exceptions.DCIException('Unable to connect to elasticsearch...')  # noqa
    return wrapper


class DCIESEngine(object):
    def __init__(self, es_host, es_port, index='dci', create_index=False,
                 timeout=30):
        self._index = index
        self._conn = Elasticsearch([{'host': es_host, 'port': es_port}],
                                   timeout=timeout)
        if create_index is True:
            self._conn.indices.create(index=self._index, ignore=400)

    @catchConnectionError
    def index(self, document):
        return self._conn.index(index=self._index, doc_type='logs',
                                id=document['id'], body=document)

    @catchConnectionError
    def update_sequence(self, sequence, doc_type='logs'):
        return self._conn.index(index=self._index, doc_type=doc_type,
                                id='sequence', body={'sequence': sequence})

    @catchConnectionError
    def get_last_sequence(self, doc_type='logs'):
        try:
            res = self._conn.get(index=self._index,
                                 doc_type='logs',
                                 id='sequence')
            return res['_source']['sequence']
        except es_exceptions.NotFoundError:
            self.update_sequence(0, doc_type)
            return 0

    @catchConnectionError
    def get(self, id, team_id=None):
        res = self._conn.get(index=self.esindex, doc_type='logs', id=id)
        if team_id:
            if res:
                if res['_source']['team_id'] != team_id:
                    res = {}
        return res

    @catchConnectionError
    def delete(self, id):
        try:
            return self._conn.delete(index=self._index, doc_type='logs', id=id)
        except es_exceptions.NotFoundError:
            pass

    @catchConnectionError
    def list(self, include=None, exclude=None, size=64):

        include = include or ['id']
        query = {
            "size": size,
            "query": {
                "match_all": {}
            }
        }
        if include:
            query['_source'] = {
                'include': include
            }
        if exclude:
            query['_source'] = {
                'exclude': exclude
            }
        if self._conn.indices.exists(index=self._index):
            return self._conn.search(index=self._index, body=query)
        else:
            return None

    @catchConnectionError
    def refresh(self):
        return self._conn.indices.refresh(index=self._index,
                                          force=True)

    @catchConnectionError
    def search_content(self, pattern, team_id=None):
        if team_id:
            query = {
                "query": {
                    "filtered": {
                        "filter": {"match": {"team_id": team_id}},
                        "query": {"match": {"content": pattern}}
                    }
                }
            }
        else:
            query = {"query": {"match": {"content": pattern}}}

        return self._conn.search(index=self._index, body=query,
                                 request_cache=False, size=100)

    @catchConnectionError
    def cleanup(self):
        if self._conn.indices.exists(index=self._index):
            return self._conn.indices.delete(index=self._index)
