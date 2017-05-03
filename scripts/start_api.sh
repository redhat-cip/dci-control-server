#!/bin/sh
set -xe

# checks if not already running
PROCESS=$(ps auxfw | grep runtestserver | grep -v grep | awk '{print $2}')
echo $PROCESS
if [ "$PROCESS" != "" ]; then kill $PROCESS; fi

python ./scripts/runtestserver.py provision &
