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

from dci import trackers
from six.moves.urllib.parse import urlparse
from xml.etree import ElementTree


_URI_BASE = "show_bug.cgi?ctype=xml&id="


class Bugzilla(trackers.Tracker):
    def __init__(self, url):
        super(Bugzilla, self).__init__(url)

    def retrieve_info(self):
        """Query Bugzilla API to retrieve the needed infos."""

        scheme = urlparse(self.url).scheme
        netloc = urlparse(self.url).netloc
        query = urlparse(self.url).query

        if scheme not in ("http", "https"):
            return

        for item in query.split("&"):
            if "id=" in item:
                ticket_id = item.split("=")[1]
                break
        else:
            return

        bugzilla_url = "%s://%s/%s%s" % (scheme, netloc, _URI_BASE, ticket_id)

        result = requests.get(bugzilla_url)
        self.status_code = result.status_code

        if result.status_code == 200:
            tree = ElementTree.fromstring(result.content)

            self.title = tree.findall("./bug/short_desc").pop().text
            self.issue_id = tree.findall("./bug/bug_id").pop().text
            self.reporter = tree.findall("./bug/reporter").pop().text
            self.assignee = tree.findall("./bug/assigned_to").pop().text
            self.status = tree.findall("./bug/bug_status").pop().text
            self.product = tree.findall("./bug/product").pop().text
            self.component = tree.findall("./bug/component").pop().text
            self.created_at = tree.findall("./bug/creation_ts").pop().text
            self.updated_at = tree.findall("./bug/delta_ts").pop().text
            try:
                self.closed_at = tree.findall("./bug/cf_last_closed").pop().text
            except IndexError:
                # cf_last_closed is present only if the issue has been closed
                # if not present it raises an IndexError, meaning the issue
                # isn't closed yet, which is a valid use case.
                pass
