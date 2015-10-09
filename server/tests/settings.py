from server.settings import *  # noqa
import uuid

SQLALCHEMY_DATABASE_URI = '%s_%s' % (
    SQLALCHEMY_DATABASE_URI, uuid.uuid4()
)
