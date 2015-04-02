#!/bin/bash

pg_dump -U boa -h 127.0.0.1 -s dci_control_server|sed 's,\ \+$,,' > dci-control-server.sql
