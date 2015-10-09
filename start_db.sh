#!/bin/sh

# checks if pg_ctl command exists
type "pg_ctl" &> /dev/null || exit 0

# checks if not already running
pg_ctl status &> /dev/null && exit 0

# else run postgres

OPTIONS="--client-encoding=utf8 --full-page_writes=off \
    --logging-collector=off --log-destination='stderr'"

pg_ctl -w -D /var/lib/pgsql/data -o "-F -h '' $OPTIONS" start
