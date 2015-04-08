#!/bin/bash

pg_dump --no-owner -U boa -h 127.0.0.1 -s dci_control_server|sed 's,\ \+$,,' > dci-control-server.sql
postgresql_autodoc -u boa -d dci_control_server -h 127.0.0.1 --password && dot dci_control_server.dot -Tpng > dci_control_server.png
