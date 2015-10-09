from server.settings import *  # noqa
import os
import uuid

SQLALCHEMY_DATABASE_URI = "postgresql:///?host=%s&dbname=%s" % (
    os.path.abspath(os.environ['DCI_DB_DIR']), uuid.uuid4()
)
