from server.settings import *  # noqa
import os
import uuid

SQLALCHEMY_DATABASE_URI = "postgresql:///%s?host=%s" % (
    uuid.uuid4(), os.path.abspath(os.environ['DCI_DB_DIR'])
)
