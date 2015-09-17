import urlparse
import server.db.models
import os

db_uri = os.environ.get(
        'OPENSHIFT_POSTGRESQL_DB_URL',
        'postgresql://boa:boa@127.0.0.1:5432/dci_control_server'
    )


dci_model = server.db.models.DCIModel(db_uri)

SQLALCHEMY_DATABASE_URI = db_uri
LAST_UPDATED = 'updated_at'
DATE_CREATED = 'created_at'
ID_FIELD = 'id'
ITEM_URL = ('regex("[\.-a-z0-9]{8}-[-a-z0-9]{4}-'
            '[-a-z0-9]{4}-[-a-z0-9]{4}-[-a-z0-9]{12}")')

ITEM_LOOKUP_FIELD = 'id'
ETAG = 'etag'
DEBUG = True
URL_PREFIX = 'api'
X_DOMAINS = '*'
X_HEADERS = 'Authorization'
DOMAIN = dci_model.generate_eve_domain_configuration()
# The following two lines will output the SQL statements
# executed by SQLAlchemy. Useful while debugging and in
# development. Turned off by default
# --------
SQLALCHEMY_ECHO = False
SQLALCHEMY_RECORD_QUERIES = False
