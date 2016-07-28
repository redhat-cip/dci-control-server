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


class Tracker(object):

    def __init__(self, url):
        self.url = url
        self.retrieve_info()

    def retrieve_info(self):
        """Retrieve informations for a specific issue in a tracker."""
        pass

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
