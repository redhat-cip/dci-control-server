from sqlalchemy.orm import *
from dci.db import models
from dci.db.orm import teams

class User(object):
    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'id'         : self.id,
           'name'       : self.name,
           'created_at' : self.created_at,
           'updated_at' : self.updated_at,
           'team_id'    : self.team_id
       }

    def is_admin(self):
        if self.role == 'admin':
            return True
        else:
            return False

mapper(User, models.USERS,
       properties=dict(team=relation(teams.Team, uselist=False)))
