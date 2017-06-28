#!/bin/sh
set -x

# kill the running server if it exists
ps aux | awk '!/awk/' | awk '/runtestserver/ {print $2}'| xargs -r kill

python ./scripts/runtestserver.py provision &

while true; do
    status=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/v1/users)
    if [ ${status} -eq 200 ]; then
        break
    fi
    sleep 1
done