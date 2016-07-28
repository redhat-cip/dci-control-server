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

import json
import requests

from six.moves.urllib.parse import urlparse

_URL_BASE = 'https://api.github.com/repos'

class Github(object):

    def __init__(self, url):
        self.url = url
        self.retrieve_info(url)

    def retrieve_info(self, url):
        """Query the api.github.com endpoint to retrieve the needed infos."""

        path = urlparse(url).path
        path = path.split('/')[1:]

        github_url = '%s/%s/%s/issues/%s' % (_URL_BASE, path[0],
                                             path[1], path[3])

        result = requests.get(github_url).json()

        self.title = result['title']
        self.issue_id = result['number']
        self.reporter = result['user']['login']
        self.assignee = result['assignee']
        self.status = result['state']
        self.created_at = result['created_at']
        self.updated_at = result['updated_at']
        self.closed_at = result['closed_at']

    def dump(self):
        """Return the object itself."""

        return {
            'title': self.title,
            'issue_id': self.issue_id,
            'reporter': self.reporter,
            'assignee': self.assignee,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'closed_at': self.closed_at
        }
