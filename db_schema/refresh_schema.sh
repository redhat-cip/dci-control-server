#!/bin/bash

pg_dump --no-owner -U boa -h 127.0.0.1 -s dci_control_server|sed 's,\ \+$,,' > dci-control-server.sql

echo "INSERT INTO teams (name) VALUES ('admin');" >> dci-control-server.sql
echo "INSERT INTO teams (name) VALUES ('partner');" >> dci-control-server.sql
echo "INSERT INTO users (name, password, team_id) VALUES ('admin', crypt('admin', gen_salt('bf', 8)), (SELECT id FROM teams WHERE name='partner'));" >> dci-control-server.sql
echo "INSERT INTO users (name, password, team_id) values ('partner', crypt('partner', gen_salt('bf', 8)), (SELECT id FROM teams WHERE name='partner'));" >> dci-control-server.sql
echo "INSERT INTO roles (name) VALUES ('admin');" >> dci-control-server.sql
echo "INSERT INTO roles (name) VALUES ('partner');" >> dci-control-server.sql
echo "INSERT INTO user_roles (user_id, role_id) VALUES ((SELECT id from users WHERE name='admin'), (SELECT id from roles WHERE name='admin'));" >> dci-control-server.sql
echo "INSERT INTO user_roles (user_id, role_id) VALUES ((SELECT id from users WHERE name='admin'), (SELECT id from roles WHERE name='partner'));" >> dci-control-server.sql
echo "INSERT INTO user_roles (user_id, role_id) VALUES ((SELECT id from users WHERE name='partner'), (SELECT id from roles WHERE name='partner'));" >> dci-control-server.sql
postgresql_autodoc -u boa -d dci_control_server -h 127.0.0.1 --password && dot dci_control_server.dot -Tpng > dci_control_server.png
