#!/bin/sh
set -xe

DCI_DB_DIR=${DCI_DB_DIR:-".db_dir"}
DCI_DB_USER=${DCI_DB_USER:-"dci"}
DCI_DB_PASS=${DCI_DB_PASS:-"dci"}
DCI_DB_NAME=${DCI_DB_NAME:-"dci"}

# get dci_db_dir absolute path
DCI_DB_DIR="$(cd "$(dirname "$0")/.." && pwd)/$DCI_DB_DIR"

# if the database is already running we do not want to run this script
[ ! -z "$DISABLE_DB_START" ] &&exit 0

PLATFORM=$(awk -F'=' '/^ID=/ { print $2 }' /etc/os-release)
VERSION_ID=$(awk -F'=' '/^VERSION_ID=/ { print $2 }' /etc/os-release)

if [[ ( "${PLATFORM//\"}" == rhel || "${PLATFORM//\"}" == centos ) ]] && (( ${VERSION_ID//\"} < 8 )); then
    source /opt/rh/rh-postgresql96/enable
fi

# checks if pg_ctl command exists
type "pg_ctl"

# checks if not already running
pg_ctl status -D "$DCI_DB_DIR" &> /dev/null && pg_ctl stop -D "$DCI_DB_DIR" -m fast

[ -d "$DCI_DB_DIR" ] && rm -rf "$DCI_DB_DIR"

# init the database directory and start the process
pg_ctl initdb -D "$DCI_DB_DIR"
echo "unix_socket_directories = '${DCI_DB_DIR}'" >> $DCI_DB_DIR/postgresql.conf
pg_ctl start -w -D "$DCI_DB_DIR"
psql -d postgres -h ${DCI_DB_DIR} -c "CREATE USER ${DCI_DB_USER} WITH SUPERUSER PASSWORD '${DCI_DB_PASS}';"
createdb -h ${DCI_DB_DIR} -O "${DCI_DB_USER}" "${DCI_DB_NAME}"
