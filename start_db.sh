#!/bin/sh
set -x

DCI_DB_DIR="$(cd $(dirname "$0") && pwd)/$DCI_DB_DIR"

# checks if we are in a docker_compose configuration
[ ! -z "$DB_PORT" ] &&exit 0

# checks if pg_ctl command exists
type "pg_ctl" &> /dev/null ||exit 1

# checks if not already running
pg_ctl -D "$DCI_DB_DIR" status &> /dev/null && pg_ctl -D  "$DCI_DB_DIR" stop

[ -d "$DCI_DB_DIR" ] && rm -rf "$DCI_DB_DIR"

OPTIONS="--client-encoding=utf8 --full-page_writes=off \
    --logging-collector=off --log-destination='stderr'"

mkdir "$DCI_DB_DIR"
pg_ctl initdb -D "$DCI_DB_DIR" -o "--no-locale"
pg_ctl start -w -D "$DCI_DB_DIR" -o "-k $DCI_DB_DIR -F -h '' $OPTIONS"

