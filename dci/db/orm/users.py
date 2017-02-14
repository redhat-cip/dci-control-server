from sqlalchemy.orm import *
from dci.db import models

class User(object): pass
class Team(object): pass

mapper(User, models.USERS)
mapper(Team, models.TEAMS)
