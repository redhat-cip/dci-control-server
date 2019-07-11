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

import uuid


class Identity:

    def __init__(self, user_info):

        self.id = user_info.get('id')
        self.password = user_info.get('password', None)
        self.name = user_info.get('name', None)
        self.fullname = user_info.get('fullname', None)
        self.timezone = user_info.get('timezone', None)
        self.email = user_info.get('email', None)
        self.sso_username = user_info.get('sso_username', None)
        self.etag = user_info.get('etag', None)
        self._is_user = user_info.get('is_user', False)
        self.api_secret = user_info.get('api_secret', '')
        self._is_remoteci = user_info.get('is_remoteci', False)
        self._is_feeder = user_info.get('is_feeder', False)
        # user_info['teams'] = {'<team-id1>': {'parent_id': <id>,
        #                                      'id': <id>,
        #                                      'name': <name>,
        #                                      'etag': <etag>,
        #                       '<team-id2>: {...}}
        self.teams = user_info.get('teams', {})
        self.teams_ids = list(self.teams.keys())
        self._is_super_admin = user_info.get('is_super_admin', False)
        self._is_read_only_user = user_info.get('is_read_only_user', False)
        self._is_epm_user = user_info.get('is_epm_user', False)

    def is_super_admin(self):
        """Ensure the user is SUPER_ADMIN."""

        return self._is_super_admin

    def is_not_super_admin(self):
        """Ensure the user is not SUPER_ADMIN."""

        return not self.is_super_admin()

    def is_epm(self):
        """Ensure the user is EPM"""

        return self._is_epm_user or self.is_super_admin()

    def is_not_epm(self):
        """Ensure the user is not EPM"""

        return not self.is_epm()

    def is_read_only_user(self):
        """Check if the user is a rh employee."""

        return self._is_read_only_user

    def is_not_read_only_user(self):
        """Check if the user is not a read only user."""

        return not self.is_read_only_user()

    def is_in_team(self, team_id):
        """Test if user is in team"""

        if self.is_super_admin() or self.is_epm():
            return True
        team_id = uuid.UUID(str(team_id))
        return team_id in self.teams

    def is_not_in_team(self, team_id):
        """Test if user is not in team"""

        return not self.is_in_team(team_id)

    def is_user(self):
        return self._is_user

    def is_remoteci(self):
        """Ensure ther resource is REMOTECI."""
        return self._is_remoteci

    def is_feeder(self):
        """Ensure ther resource is FEEDER."""
        return self.is_feeder