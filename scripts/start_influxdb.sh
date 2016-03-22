#!/bin/sh
set -xe

DCI_INFLUXDB_DIR=${DCI_INFLUXDB_DIR:-".influxdb_dir"}

# get dci_influxdb_dir absolute path
DCI_INFLUXDB_DIR="$(cd "$(dirname "$0")/.." && pwd)/$DCI_INFLUXDB_DIR"
# if the database is already running we do not want to run this script
[ ! -z "$DISABLE_INFLUXDB_START" ] &&exit 0

# Clean the dir for eventual leftovers
[ -d "$DCI_INFLUXDB_DIR" ] && rm -rf "$DCI_INFLUXDB_DIR"

# init the database directory and start the process
sudo systemctl stop influxdb
mkdir -p $DCI_INFLUXDB_DIR/{data,meta,wal}
cp /etc/influxdb/influxdb.conf $DCI_INFLUXDB_DIR/../influxdb.conf
sed -i "s#/var/lib/influxdb/data#${DCI_INFLUXDB_DIR}/data#g" $DCI_INFLUXDB_DIR/../influxdb.conf
sed -i "s#/var/lib/influxdb/meta#${DCI_INFLUXDB_DIR}/meta#g" $DCI_INFLUXDB_DIR/../influxdb.conf
sed -i "s#/var/lib/influxdb/wal#${DCI_INFLUXDB_DIR}/wal#g" $DCI_INFLUXDB_DIR/../influxdb.conf

influxd -config $DCI_INFLUXDB_DIR/../influxdb.conf &
