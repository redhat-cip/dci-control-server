#!/bin/sh

if ! python3 bin/dci-wait-for-db; then
  echo "Unable to wait for the DB. Exiting." 1>&2
  exit 0
fi

if ! python3 bin/dci-dbsync; then
  echo "Unable to init the DB. Exiting." 1>&2
  exit 0
fi

pubkey=$(python3 bin/dci-get-pem-ks-key.py ${SSO_URL} ${SSO_REALM})

export SSO_PUBLIC_KEY="$pubkey"
echo $SSO_PUBLIC_KEY
exec "$@"
