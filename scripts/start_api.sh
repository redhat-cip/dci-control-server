#!/bin/sh
set -x

# checks if not already running
PROCESS=$(ps auxfw | grep runtestserver | grep -v grep | awk '{print $2}')
echo $PROCESS
if [ "$PROCESS" != "" ]; then kill $PROCESS; fi

python ./scripts/runtestserver.py provision | tee /tmp/dciapi.log &

while true; do
    curl --user admin:admin http://127.0.0.1:5000/api/v1
    if [ $? -eq 0 ]; then
        break
    fi
    sleep 1
done
