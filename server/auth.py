# -*- encoding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# WARNING(Gonéri): both python-bcrypt and bcrypt provide a bcrypt package
import bcrypt
import eve.auth
import flask
import sqlalchemy.orm.exc


class DCIBasicAuth(eve.auth.BasicAuth):
    def __init__(self, dci_model):
        self.dci_model = dci_model

    def check_auth(self, name, password, allowed_roles, resource, method):
        session = self.dci_model.get_session()
        users_c = self.dci_model.base.classes.users
        user_roles_c = self.dci_model.base.classes.user_roles
        roles_c = self.dci_model.base.classes.roles
        try:
            self.user = session.query(
                users_c).filter_by(name=name).one()
            self.user_roles = session.query(
                user_roles_c).filter_by(user_id=self.user.id).all()
            roles_id = [ur.role_id for ur in self.user_roles]
            self.roles = [r.name for r in session.query(
                roles_c).filter(roles_c.id.in_(roles_id)).all()]
        except sqlalchemy.orm.exc.NoResultFound:
            return False
        finally:
            session.close()
        print(self.user.password.encode('utf-8'))
        if bcrypt.hashpw(
                password.encode('utf-8'),
                self.user.password.encode('utf-8')
        ) == self.user.password.encode('utf-8'):
            return True
        return False

    def authorized(self, allowed_roles, resource, method):
        auth = flask.request.authorization
        if not hasattr(auth, 'username') or not hasattr(auth, 'password'):
            flask.abort(401, description='Unauthorized: username required')
            return False
        if not self.check_auth(auth.username, auth.password, None,
                               resource, method):
            flask.abort(401, description='Unauthorized')
            return False

        if 'admin' in self.roles:
            # NOTE(Gonéri): we preserve auth_value undefined for GET,
            # this way, admin use can read all the field from the database
            if method != 'GET':
                self.set_request_auth_value(self.user.team_id)
            return True
        self.set_request_auth_value(self.user.team_id)

        # NOTE(Gonéri): We may find useful to store this matrice directly in
        # the role entrt in the DB
        acl = {
            'partner': {
                'files': ['GET', 'POST'],
                'remotecis': ['GET', 'POST'],
                'jobs': ['GET', 'POST'],
                'jobstates': ['GET', 'POST'],
                'tests': ['GET']
            }
        }

        for role in self.roles:
            try:
                if method in acl[role][resource]:
                    return True
            except KeyError:
                pass
        flask.abort(403, description='Forbidden')
        return False
