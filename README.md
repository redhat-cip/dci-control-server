# DCI Control-server

## installation

### PostgreSQL configuration

install and configure PostgreSQL:

    yum install postgresql-server postgresql-contrib

Allow local account with password:

    editor /var/lib/pgsql/data/pg_hba.conf

Add the following line on the top of the file:

    host    all             all             127.0.0.1/32            md5

Restart PostgreSQL with the new settings:

    systemctl restart postgresql.service

Connect with the postgres user:

    sudo su - postgres
        $ createuser -P boa
    Enter password for new role:
    Enter it again:

    $ createdb boa -O boa
    $ psql -U boa -W -h 127.0.0.1 dci_control_server < db_schema/dci-control-server.sql
