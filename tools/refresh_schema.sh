#!/bin/bash

postgresql_autodoc -u boa -d dci_control_server -h 127.0.0.1 --password && dot dci_control_server.dot -Tpng > dci_control_server.png
