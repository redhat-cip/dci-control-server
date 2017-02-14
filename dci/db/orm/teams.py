from sqlalchemy.orm import *
from dci.db import models

class Team(object): pass

mapper(Team, models.TEAMS)
