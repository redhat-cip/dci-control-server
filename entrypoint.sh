#!/bin/sh

python bin/wait_for_db
python bin/init_database
python bin/provision_keycloak
pubkey=$(python bin/generate_keycloak_pem_key http://keycloak:8080 dci-test)

export SSO_PUBLIC_KEY="$pubkey"

exec "$@"
