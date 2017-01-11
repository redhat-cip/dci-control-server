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

from elasticsearch import Elasticsearch
import elasticsearch.exceptions
import elasticsearch.helpers


class DCIESEngine(object):
    def __init__(self, conf, index="global", timeout=30):
        self.esindex = index
        self.conn = Elasticsearch(conf['ES_HOST'], port=conf['ES_PORT'],
                                  timeout=timeout)
        if not self.conn.indices.exists(index=self.esindex):
            self.conn.indices.create(index=self.esindex)

    def get(self, id, team_id=None, **kargs):
        try:
            res = self.conn.get(index=self.esindex, doc_type='log', id=id, **kargs)
        except elasticsearch.exceptions.NotFoundError:
            res = {}
        if team_id:
            if res:
                if res['_source']['team_id'] != team_id:
                    res = {}
        return res

    def delete(self, id):
        self.conn.delete(index=self.esindex, doc_type='log', id=id)
        return True

    def _build_query(self, size=None, includes=None, excludes=None):
        query = {
            "query": {
                "match_all": {}
            }
        }
        if size:
            query['query']['size'] = size
        if includes:
            query['_source'] = {
                'includes': includes
            }
        if excludes:
            query['_source'] = {
                'excludes': excludes
            }


    def list(self, includes=None, excludes=None):
        query = self._build_query(size=1000, includes=includes,
                                  excludes=excludes)
        if self.conn.indices.exists(index=self.esindex):
            return self.conn.search(index=self.esindex, body=query)
        else:
            return None

    def iter(self, includes=None, excludes=None):
        query = self._build_query(includes, excludes)
        return elasticsearch.helpers.scan(self.conn,
                                          query=query,
                                          index=self.esindex)

    def index(self, values):
        return self.conn.index(index=self.esindex, doc_type='log',
                               id=values['id'], body=values)

    def refresh(self):
        return self.conn.indices.refresh(index=self.esindex,
                                         force=True)

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

        return self.conn.search(index=self.esindex, body=query,
                                request_cache=False, size=100)

    def cleanup(self):
        if self.conn.indices.exists(index=self.esindex):
            return self.conn.indices.delete(index=self.esindex)
