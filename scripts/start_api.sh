#!/bin/sh
set -x

# kill the running server if it exists
ps aux | awk '!/awk/' | awk '/runtestserver/ {print $2}'| xargs -r kill

python ./scripts/runtestserver.py provision &

while true; do
    curl --user admin:admin http://127.0.0.1:5000/api/v1
    if [ $? -eq 0 ]; then
        break
    fi
    sleep 1
done

