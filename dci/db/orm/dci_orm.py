import flask
import uuid
from sqlalchemy.orm import *
from dci.db import models

class Team(object):
    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       result = {
           'id'         : self.id,
           'name'       : self.name,
           'created_at' : self.created_at,
           'updated_at' : self.updated_at,
           'state'      : self.state,
           'etag'       : self.etag
       }
       try:
           result.update({'user': [i.serialize for i in self.user]})
       except:
           pass
       return result

class User(object):
    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       result = { 'id'         : self.id,
                  'name'       : self.name,
                  'created_at' : self.created_at,
                  'updated_at' : self.updated_at,
                  'team_id'    : self.team_id,
                  'role'       : self.role,
                  'state'      : self.state }
       try:
           result.update({'team': self.team.serialize})
       except:
           pass

       return result

    def get_password(self):
        return self.password

    def is_admin(self):
        if self.role == 'admin':
            return True
        else:
            return False

    def is_team_admin(self, team_id):
        if self.role == 'admin' and self.team_id == team_id:
            return True
        else:
            return False

    def is_super_admin(self):
        session = flask.g.db
        query = session.query(User, Team)
        embed_user, embed_team = query.join(Team).filter(User.id == self.id).first()
        team_name = embed_team.name
        session.commit()
        if self.role == 'admin' and team_name == 'admin':
            return True
        return False

mapper(Team, models.TEAMS, properties=dict(user=relation(User, back_populates="team", lazy='noload')))
mapper(User, models.USERS, properties=dict(team=relation(Team, back_populates="user", lazy='noload')))
