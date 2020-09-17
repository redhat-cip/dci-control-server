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

import re
import requests

from dci import trackers
from six.moves.urllib.parse import urlparse


_URL_BASE = "https://api.github.com/repos"


class Github(trackers.Tracker):
    def __init__(self, url):
        super(Github, self).__init__(url)

    def retrieve_info(self):
        """Query the Github API to retrieve the needed infos."""

        path = urlparse(self.url).path
        path = path.split("/")[1:]

        sanity_filter = re.compile("[\da-z-_]+", re.IGNORECASE)
        self.product = sanity_filter.match(path[0]).group(0)
        self.component = sanity_filter.match(path[1]).group(0)
        self.issue_id = int(path[3])

        github_url = "%s/%s/%s/issues/%s" % (
            _URL_BASE,
            self.product,
            self.component,
            self.issue_id,
        )

        result = requests.get(github_url)
        self.status_code = result.status_code

        if result.status_code == 200:
            result = result.json()
            self.title = result["title"]
            self.reporter = result["user"]["login"]
            if result["assignee"] is not None:
                self.assignee = result["assignee"]["login"]
            self.status = result["state"]
            self.created_at = result["created_at"]
            self.updated_at = result["updated_at"]
            self.closed_at = result["closed_at"]
        elif result.status_code == 404:
            self.title = "private issue"
