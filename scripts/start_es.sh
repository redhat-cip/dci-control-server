#!/bin/sh
set -x

TIMEOUT=${TIMEOUT:-60}
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

i=1
while [ $i -lt $TIMEOUT ]; do
    status=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:9200/_cluster/health)
    if [ ${status} -eq 200 ]; then
        break
    fi
    let i++
    sleep 1
done

if [ $i -eq $TIMEOUT ]; then
    echo "Elasticsearch not ready in ${TIMEOUT}s"
    exit 1
fi

exit 0
