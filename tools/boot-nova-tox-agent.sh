#!/bin/bash

set -eux

while true; do
    while [ $(nova list|awk '/(BUILD|ACTIVE)/ {print $2}'|wc -l) -lt "8" ]; do
        nova boot --flavor m1.small --image 'Fedora 21 Cloud x86_64 (RAW)' --key-name goneri --user-data=cloud-init.sh dci-tox-agent-$RANDOM
        sleep 1
    done
    for vm in $(nova list|awk '/ACTIVE/ {print $2}'); do
        if nova console-log $vm|grep 'System halted'; then
            nova delete $vm
        fi
    done
    sleep 60
done
