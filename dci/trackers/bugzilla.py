# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Red Hat, Inc
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

import requests

from six.moves.urllib.parse import urlparse
from xml.etree import ElementTree

_URI_BASE = 'show_bug.cgi?ctype=xml&id='

class Bugzilla(object):

    def __init__(self, url):
        self.url = url
        self.retrieve_info(url)

    def retrieve_info(self, url):
        """Query the api.github.com endpoint to retrieve the needed infos."""
        
        scheme = urlparse(url).scheme
        netloc = urlparse(url).netloc
        query = urlparse(url).query

        for item in query.split('&'):
            if 'id=' in item:
                ticket_id = item.split('=')[1]
                break

        bugzilla_url = '%s://%s/%s%s' % (scheme, netloc, _URI_BASE, ticket_id)

        result = requests.get(bugzilla_url).content
        tree = ElementTree.fromstring(result)

        self.title = tree.findall("./bug/short_desc").pop().text
        self.issue_id = tree.findall("./bug/bug_id").pop().text
        self.reporter = tree.findall("./bug/reporter").pop().text
        self.assignee = tree.findall("./bug/assigned_to").pop().text
        self.status = tree.findall("./bug/bug_status").pop().text
        self.product = tree.findall("./bug/product").pop().text
        self.component = tree.findall("./bug/component").pop().text
        self.created_at = tree.findall("./bug/creation_ts").pop().text
        self.updated_at = tree.findall("./bug/delta_ts").pop().text

        self.closed_at = None
  
    def dump(self):
        """Return the object itself."""

        return {
            'title': self.title,
            'issue_id': self.issue_id,
            'reporter': self.reporter,
            'assignee': self.assignee,
            'status': self.status,
            'product': self.product,
            'component': self.component,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'closed_at': self.closed_at
        }
