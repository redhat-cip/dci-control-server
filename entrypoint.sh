#!/bin/sh

python /opt/dci-control-server/bin/dci-dbinit

exec "$@"
