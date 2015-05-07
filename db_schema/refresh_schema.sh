#!/bin/bash

pg_dump --no-owner -U boa -h 127.0.0.1 -s dci_control_server|sed 's,\ \+$,,' > dci-control-server.sql
echo "INSERT INTO users (name, login, password, is_admin) VALUES ('admin', 'admin', crypt('admin', gen_salt('bf', 8)), TRUE);" >> dci-control-server.sql
echo "INSERT INTO users (name, login, password, is_admin) values ('admin', 'admin', crypt('admin', gen_salt('bf', 8)), TRUE);" >> dci-control-server.sql
for role in admin partner; do
    echo "INSERT INTO roles (name) VALUES ('${role}');" >> dci-control-server.sql
    echo "INSERT INTO user_roles (user_id, role_id) VALUES ((SELECT id from users WHERE name='admin'), (SELECT id from roles WHERE name='${role}'));" >> dci-control-server.sql
done
postgresql_autodoc -u boa -d dci_control_server -h 127.0.0.1 --password && dot dci_control_server.dot -Tpng > dci_control_server.png
pi
