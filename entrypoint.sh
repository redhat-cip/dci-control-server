#!/bin/sh

DCI_LOGIN='admin' DCI_PASSWORD='admin' python /opt/dci-control-server/bin/dci-dbinit

python /opt/keycloak-provision.py

pubkey=$(python bin/dci-get-pem-ks-key.py http://keycloak:8180 dci-test)

export SSO_PUBLIC_KEY="$pubkey"

exec "$@"
