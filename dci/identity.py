# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Red Hat, Inc
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


class Identity:
    """Class that offers helper methods to simplify permission management
    """

    def __init__(self, user, teams):
        for key in user.keys():
            setattr(self, key, user[key])

        # TODO: replace user['role_label'] with user['role']['label']
        self.role_label = user['role_label']
        self.team = self._get_user_team(user, teams)
        # in case of sso user without team
        if self.team is None:
            self.team = {'id': None}
        self.partner_teams = self._get_partner_teams(user, teams)
        # TODO: remove teams object and use team and partner_teams
        self.teams = self._get_teams()

    # NOTE(spredzy): In order to avoid a huge refactor patch, the __getitem__
    # function is overloaded so it behaves like a dict and the code in place
    # can work transparently
    def __getitem__(self, key):
        return getattr(self, key)

    def _get_teams(self):
        teams = []
        if self.team:
            teams.append(self.team['id'])
        for partner_team in self.partner_teams:
            teams.append(partner_team['id'])
        return teams

    def _get_user_team(self, user, teams):
        for team in teams:
            if user['team_id'] == team['id']:
                return team

    def _get_partner_teams(self, user, teams):
        partner_teams = []
        for team in teams:
            if user['team_id'] != team['id']:
                partner_teams.append(team)
        return partner_teams

    def is_not_in_team(self, team_id):
        """Test if user is not in team"""
        return not self.is_in_team(team_id)

    def is_in_team(self, team_id):
        """Test if user is in team"""
        if self.is_super_admin():
            return True
        if team_id == self.team['id']:
            return True
        for partner_team in self.partner_teams:
            if team_id == partner_team['id']:
                return True
        return False

    def is_super_admin(self):
        """Ensure the user has the role SUPER_ADMIN."""

        return self.role_label == 'SUPER_ADMIN'

    def is_product_owner(self):
        """Ensure the user has the role PRODUCT_OWNER."""

        return self.role_label == 'PRODUCT_OWNER'

    # TODO: replace team_id with object team
    def is_team_product_owner(self, team_id):
        """Ensure the user has the role PRODUCT_OWNER and belongs
           to the team."""

        return self.role_label == 'PRODUCT_OWNER' and self.is_in_team(team_id)

    def is_admin(self):
        """Ensure the user has the role ADMIN."""

        return self.role_label == 'ADMIN'

    def is_read_only_user(self):
        """Check if the user is a rh employee."""
        return self.role_label == 'READ_ONLY_USER'

    def is_team_admin(self, team_id):
        """Ensure the user has the role ADMIN and belongs to the team."""

        return self.role_label == 'ADMIN' and self.is_in_team(team_id)

    def is_regular_user(self):
        """Ensure the user has the role USER."""

        return self.role_label == 'USER'

    def is_remoteci(self):
        """Ensure ther resource has the role REMOTECI."""

        return self.role_label == 'REMOTECI'

    def is_feeder(self):
        """Ensure ther resource has the role FEEDER."""

        return self.role_label == 'FEEDER'
