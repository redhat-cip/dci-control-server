#!/bin/sh

# checks if pg_ctl command exists
type "pg_ctl" &> /dev/null || exit 0

# checks if not already running
pg_ctl status &> /dev/null && exit 0

# else run postgres

OPTIONS="--client-encoding=utf8 --full-page_writes=off \
    --logging-collector=off --log-destination='stderr'"

TMP_DIR=$(mktemp -d)

initdb --no-locale -D "$TMP_DIR"
pg_ctl -w -D "$TMP_DIR" -o "-k $TMP_DIR -F -h '' $OPTIONS" start

