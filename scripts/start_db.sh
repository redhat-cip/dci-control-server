#!/bin/sh
set -xe

DCI_DB_DIR=${DCI_DB_DIR:-".db_dir"}

# get dci_db_dir absolute path
DCI_DB_DIR="$(cd "$(dirname "$0")/.." && pwd)/$DCI_DB_DIR"

# if the database is already running we do not want to run this script
[ ! -z "$DISABLE_DB_START" ] &&exit 0

# checks if pg_ctl command exists
type "pg_ctl"

# checks if not already running
pg_ctl status -D "$DCI_DB_DIR" &> /dev/null && pg_ctl stop -D "$DCI_DB_DIR" -m fast

[ -d "$DCI_DB_DIR" ] && rm -rf "$DCI_DB_DIR"

OPTIONS="--client-encoding=utf8 --full-page_writes=off \
         --logging-collector=off --log-destination='stderr'"

# init the database directory and start the process
pg_ctl initdb -D "$DCI_DB_DIR" -o "--no-locale -E UTF8"
pg_ctl start -w -D "$DCI_DB_DIR" -o "-k $DCI_DB_DIR -F -h '' $OPTIONS"
