#!/bin/sh

type "pg_ctl" > /dev/null || exit 0


pg_ctl status 2> /dev/null || pg_ctl -w -l /dev/stderr -o \
    "-F -h '' -c client_encoding=utf8 full_page_writes=off logging_collector=off" start
