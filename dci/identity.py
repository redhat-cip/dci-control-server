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
    """Class that offers helper methods to simplify permission management
    """

    def __init__(self, user_info, all_teams):

        self.id = user_info['id']
        self.password = user_info['password']
        self.name = user_info['name']
        self.fullname = user_info['fullname']
        self.timezone = user_info['timezone']
        self.email = user_info['email']
        self.etag = user_info['etag']
        # user_info['teams'] = {'<team-id1>': {'parent_id': <id>,
        #                                      'team_name': <name> 
        #                                      'role': <role>},
        #                       '<team-id2>: {...}}
        self.teams = user_info['teams']
        self.teams_ids = self.teams.keys()
        self._is_super_admin = user_info['is_super_admin']
        # if the user's team is a product team then it does have some
        # child teams, then get all the child teams
        self.child_teams_ids, self.parent_teams = self._get_child_and_parent_teams_ids(self.teams, all_teams)  # noqa

    @staticmethod
    def _get_child_and_parent_teams_ids(user_teams, all_teams):
        child_teams = set()
        parent_teams = set()
        for u_t in user_teams:
            if u_t['parent_id']:
                parent_teams.add(u_t['parent_id'])
            for a_team in all_teams:
                if a_team['parent_id'] == u_t['id']:
                    child_teams.add(a_team['id'])
        return child_teams, parent_teams

    def is_super_admin(self):
        """Ensure the user has the role SUPER_ADMIN."""

        return self._is_super_admin

    def is_not_super_admin(self):
        """Ensure the user has not the role SUPER_ADMIN."""

        return not self.is_super_admin()

    def is_product_owner(self, team_id):
        """Ensure the user is a PRODUCT_OWNER."""

        if self.is_super_admin():
            return True
        team_id = uuid.UUID(str(team_id))
        return team_id in self.child_teams_ids

    def is_not_product_owner(self, team_id):
        """Ensure the user has not the role PRODUCT_OWNER."""

        return not self.is_product_owner(team_id)

    def is_read_only_user(self):
        """Check if the user is a rh employee."""
        return self.teams[None]['role'] == 'READ_ONLY_USER'

    def is_not_read_only_user(self):
        """Check if the user is not a read only user."""

        return not self.is_read_only_user()

    def is_in_team(self, team_id):
        """Test if user is in team"""

        if self.is_super_admin():
            return True
        team_id = uuid.UUID(str(team_id))
        return team_id in self.teams or team_id in self.child_teams_ids

    def is_not_in_team(self, team_id):
        """Test if user is not in team"""

        return not self.is_in_team(team_id)

    def is_remoteci(self, team_id):
        """Ensure ther resource has the role REMOTECI."""

        if team_id not in self.teams_ids:
            return False
        return self.teams[team_id]['role'] == 'REMOTECI'

    def is_feeder(self, team_id):
        """Ensure ther resource has the role FEEDER."""

        if team_id not in self.teams_ids:
            return False
        return self.teams[team_id]['role'] == 'FEEDER'
