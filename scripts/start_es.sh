#!/bin/sh
set -x -e

DCI_ES_DIR=${DCI_ES_DIR:-".es_dir"}

# get dci_es_dir absolute path
DCI_ES_DIR="$(cd $(dirname "$0") && pwd)/$DCI_ES_DIR"

# if elasticsearch is already running we do not want to run this script
[ ! -z "$DISABLE_ES_START" ] &&exit 0

# checks if not already running
PROCESS=$(ps auxfw | grep elasticsearch | grep -v grep | awk '{print $2}')
echo $PROCESS
if [ "$PROCESS" != "" ]; then kill $PROCESS; fi

[ -d "$DCI_ES_DIR" ] && rm -rf "$DCI_ES_DIR"

# init the es directory and start the process
mkdir -p ${DCI_ES_DIR}/config ${DCI_ES_DIR}/logs ${DCI_ES_DIR}/data
cp -r /usr/share/elasticsearch/* $DCI_ES_DIR/
echo "network.host: 0.0.0.0" > ${DCI_ES_DIR}/config/elasticsearch.yml
${DCI_ES_DIR}/bin/elasticsearch -d
until $(netstat -lntp | grep -q ":9200 "); do
    sleep 1
done
