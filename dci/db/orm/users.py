from sqlalchemy.orm import *
from dci.db import models

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
class Team(object): pass

mapper(User, models.USERS)
mapper(Team, models.TEAMS)
