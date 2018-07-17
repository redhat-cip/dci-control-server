#!/bin/sh

python /opt/dci-control-server/bin/wait_for_db.py
python /opt/dci-control-server/bin/init_database.py
python /opt/dci-control-server/bin/provision_database.py

pubkey=$(python bin/dci-get-pem-ks-key.py http://keycloak:8080 dci-test)

export SSO_PUBLIC_KEY="$pubkey"

exec "$@"
