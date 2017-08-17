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

import json
import requests


class DCIESEngine(object):
    """Elasticsearch client based on requests module."""

    def __init__(self, es_host, es_port, index='dci'):
        self._session = self._build_http_session()
        self._index = index
        self._es_api = 'http://%s:%s' % (es_host, es_port)

    @staticmethod
    def _build_http_session():
        session = requests.Session()
        session.headers.setdefault('Content-Type', 'application/json')
        return session

    def index(self, document, doc_type='logs'):
        """
        :param document: dict with a 'sequence' key
        :param doc_type: the elasticsearch mapping to use
        :return: ES REST response
        """
        # todo(yassine): test 'sequence' in document and type(sequence) == int
        doc_id = document['id']
        return self._session.post('%s/%s/%s/%s' % (self._es_api, self._index,
                                                   doc_type, doc_id),
                                  data=json.dumps(document))

    # SEARCH TODO
    def search(self, regex, doc_type='logs'):
        data={"query" : {"term" : { "content" : regex }}, "fields" : ["job_id"]}
        return self._session.post('%s/%s/_search' % (self._es_api, self._index),
                                  data=json.dumps(data)).json()

    def search_by_id(self, regex, job_id, doc_type='logs'):
        data={"query" :
                {
                 "match" : { "content" : regex },
                 "match" : {"job_id": str(job_id)}
                },
                "fields" : ["job_id"]
             }
        return self._session.post('%s/%s/_search?size=1000' % (self._es_api, self._index),
                                  data=json.dumps(data)).json()

    def delete(self, doc_id, doc_type='logs'):
        """
        Delete a document.
        :param doc_id: the id of the document
        :param doc_type: the es type/mapping of the document
        :return: ES REST response
        """

        return self._session.delete('%s/%s/%s/%s' % (self._es_api, self._index,
                                                     doc_type, doc_id))

    def update_sequence(self, sequence, doc_type='logs'):
        self._session.put('%s/%s/%s/sequence' %
                          (self._es_api, self._index, doc_type),
                          data=json.dumps({'sequence': sequence}))

    def get_last_sequence(self, doc_type='logs'):
        """
        Get the last sequence number.

        :param doc_type: the es type/mapping to retrieve the value from
        :return: the last sequence number (integer value)
        """
        result = self._session.get('%s/%s/%s/sequence' % (self._es_api,
                                                          self._index,
                                                          doc_type)).json()
        if 'status' in result and result['status'] == 404:
            # if there is not 'sequence' resource then create it
            # ES will create the index and the type as well
            self.update_sequence(0, doc_type=doc_type)
            return 0
        return result['_source']['sequence']
