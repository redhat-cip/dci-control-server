#!/bin/sh

python /opt/dci-control-server/bin/dci-wait-for-db
python /opt/dci-control-server/bin/dci-dbinit
python /opt/keycloak-provision.py

PGPASSWORD=dci psql -h db -p 5432 -U postgres -c "ALTER DATABASE dci OWNER TO dci;"
PGPASSWORD=dci psql -h db -p 5432 -U postgres -c "ALTER USER dci WITH SUPERUSER;"

pubkey=$(python bin/dci-get-pem-ks-key.py http://keycloak:8080 dci-test)

export SSO_PUBLIC_KEY="$pubkey"

exec "$@"
