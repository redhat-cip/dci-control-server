#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
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

import client
import json
from pprint import pprint

import requests


def upload(es_s, item_type, items):

#    print(es_url + 'dci/_mapping/' + item_type)
    es_r = es_s.put(es_url + 'dci')
    es_r = es_s.put(es_url + 'dci/jobs')
    es_r = es_s.put(es_url + 'dci/products')
    es_r = es_s.put(es_url + 'dci/files')
    es_r = es_s.put(es_url + 'dci/_mapping/jobs', data=json.dumps({
        "_timestamp": {
            "enabled": True,
            "path": "created_at",
            "format": "E, d MMM y HH:mm:ss ZZZ"
        },
        "properties": {
            "created_at": {"type": "date", "format":"E, d MMM y HH:mm:ss ZZZ"},
            "updated_at": {"type": "date", "format":"E, d MMM y HH:mm:ss ZZZ"},
            "name": {"type": "string", "index": "not_analyzed"},
            "etag": {"type": "string", "index": "not_analyzed"},
            "id": {"type": "string", "index": "not_analyzed"}
        }
    }))
    es_r = es_s.put(es_url + 'dci/_mapping/products', data=json.dumps({
        "_timestamp": {
            "enabled": True,
            "path": "created_at",
            "format": "E, d MMM y HH:mm:ss ZZZ"
        },
        "properties": {
            "created_at": {"type": "date", "format":"E, d MMM y HH:mm:ss ZZZ"},
            "updated_at": {"type": "date", "format":"E, d MMM y HH:mm:ss ZZZ"},
            "name": {"type": "string", "index": "not_analyzed"},
            "etag": {"type": "string", "index": "not_analyzed"},
            "id": {"type": "string", "index": "not_analyzed"},
            "versions_collection": {"type": "string", "index": "not_analyzed"}
        }
    }))
    es_r = es_s.put(es_url + 'dci/_mapping/files', data=json.dumps({
        "_timestamp": {
            "enabled": True,
            "path": "created_at",
            "format": "E, d MMM y HH:mm:ss ZZZ"
        },
        "properties": {
            "created_at": {"type": "date", "format":"E, d MMM y HH:mm:ss ZZZ"},
            "updated_at": {"type": "date", "format":"E, d MMM y HH:mm:ss ZZZ"},
            "name": {"type": "string", "index": "not_analyzed"},
            "etag": {"type": "string", "index": "not_analyzed"},
            "id": {"type": "string", "index": "not_analyzed"},
          "versions_collection" : {
#            "index_name": "version",
            "properties" : {
              "created_at" : {
                "type" : "string"
              },
              "data" : {
                "properties" : {
                  "ksgen_args" : {
                    "properties" : {
                      "extra-vars" : {
                        "type" : "string"
                      }
                    }
                  },
                  "sha2" : {
                    "type" : "string"
                  }
                }
              },
              "etag" : {
                "type" : "string"
              },
              "id" : {
                "type" : "string"
              },
              "message" : {
                "type" : "string"
              },
              "name" : {
                "type" : "string"
              },
              "product_id" : {
                "type" : "string"
              },
              "sha" : {
                "type" : "string"
              },
              "title" : {
                "type" : "string"
              },
              "updated_at" : {
                "type" : "string"
              }
            }
          }
#            "versions_collection" : {
#                "properties" : {
#                    "data" : {
#                        "properties" : {
#                            "ksgen_args" : {
#                                "properties" : {
#                                    "extra-vars" : {
#                                        "type" : "string", "index": "not_analyzed"
#                                    }
#                                }
#                            },
#                            "sha" : {
#                                "type" : "string", "index": "not_analyzed"
#                            }
#                        }
#                    },
#                    "name": {"type": "string", "index": "not_analyzed"},
#                    "message": {"type": "string", "index": "not_analyzed"},
#                    "created_at": {"type": "date", "format":"E, d MMM y HH:mm:ss ZZZ"},
#                    "updated_at": {"type": "date", "format":"E, d MMM y HH:mm:ss ZZZ"},
#                    "name": {"type": "string", "index": "analyzed"},
#                    "etag": {"type": "string", "index": "not_analyzed"},
#                    "product_id": {"type": "string", "index": "not_analyzed"},
#                    "id": {"type": "string", "index": "not_analyzed"},
#                    "sha": {"type": "string", "index": "not_analyzed"},
#                    "title" : {"type" : "string", "index": "analyzed"},
#/!                }
#            }
        }
        }
    ))

    print(es_r.text)

    for item in items:
        item_es_url = es_url + 'dci/' + item_type + '/' + item['id']
        es_r = es_s.head(item_es_url)
#        print(es_r.status_code)
        if es_r.status_code == 404:
            pprint(item)
            es_r = es_s.put(item_es_url, data=json.dumps(item))
            print(es_r.text)
            print(es_r.status_code)
        import sys
        sys.exit(0)


es_url = "http://localhost:9200/"
dci_client = client.DCIClient()


es_s = requests.Session()
es_s.headers.setdefault('Content-Type', 'application/json')


products = dci_client.list_items(
    'products',
    embedded={
        'versions_collection': 1})

jobs = dci_client.list_items(
    'jobs',
    where={'created_at': '>= "yesterday"'},
    embedded={
        'remoteci': 1,
        'team': 1,
        'jobstates_collection': 1})

files = dci_client.list_items(
    'files',
    where={'created_at': '< "now"'},
    embedded={
        'remoteci': 1,
        'jobstates_collection': 1})
es_s.delete(es_url + 'dci')
es_s.delete(es_url + 'dci/products')
#upload(es_s, 'jobs', jobs)
upload(es_s, 'products', products)
#upload(es_s, 'files', files)
