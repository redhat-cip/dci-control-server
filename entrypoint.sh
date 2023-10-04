#!/bin/sh

python3 bin/dci-wait-for-db
python3 bin/dci-dbinit

pubkey=$(python3 bin/dci-get-pem-ks-key.py ${SSO_URL} ${SSO_REALM})

export SSO_PUBLIC_KEY="$pubkey"
echo $SSO_PUBLIC_KEY
exec "$@"
