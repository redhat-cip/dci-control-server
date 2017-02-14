from sqlalchemy.orm import *
from dci.db import models

class Team(object):
    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'id'         : self.id,
           'name'       : self.name,
           'created_at' : self.created_at,
           'updated_at' : self.updated_at,
       }

mapper(Team, models.TEAMS)
