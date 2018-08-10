#!/bin/sh
set -x

TIMEOUT=${TIMEOUT:-60}

# kill the running server if it exists
ps aux | awk '!/awk/' | awk '/runtestserver/ {print $2}'| xargs -r kill

# init db
DCI_LOGIN='admin' DCI_PASSWORD='admin' python ./bin/init_database

# run test server
python ./bin/runtestserver &

i=1
while [ $i -lt $TIMEOUT ]; do
    status=$(curl --user admin:admin -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/v1/users)
    if [ ${status} -eq 200 ]; then
        break
    fi
    let i++
    sleep 1
done

if [ $i -eq $TIMEOUT ]; then
    echo "API not ready in ${TIMEOUT}s"
    exit 1
fi

exit 0
