import flask
from sqlalchemy.orm import *
from dci.db import models
from dci.db.orm import teams

class User(object):
    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       result = { 'id'         : self.id,
                  'name'       : self.name,
                  'created_at' : self.created_at,
                  'updated_at' : self.updated_at,
                  'team_id'    : self.team_id }

       if self.team:
           result.update({'team': self.team.serialize})

       return result

    def is_admin(self):
        if self.role == 'admin':
            return True
        else:
            return False

    def is_super_admin(self):
        Session = sessionmaker(bind=flask.g.db_conn)
        session = Session()
        query = session.query(User)
        embed_user = query.options(eagerload('team')).filter(User.id == self.id).first()
        if self.role == 'admin' and embed_user.team.name =='admin':
            return True
        return False

mapper(User, models.USERS,
       properties=dict(team=relation(teams.Team, uselist=False)))
