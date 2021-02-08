#!/bin/sh

if [ "${ENV_DEV}" == 1 ]
then
    python3 bin/dci-wait-for-db
    python3 bin/dci-dbinit
    python3 bin/keycloak-provision.py

    pubkey=$(python3 bin/dci-get-pem-ks-key.py http://${KEYCLOAK_HOST:-keycloak}:${KEYCLOAK_PORT:-8080} dci-test)

    export SSO_PUBLIC_KEY="$pubkey"
fi

jinja2 /opt/dci-control-server/conf/vhost.j2 -o /etc/httpd/conf.d/01_api.conf

exec "$@"