# DCI Control-server

## installation

### Using OpenShift

[OpenShift](https://www.openshift.com/) is the simplest and recommanded way to
deploy the Control-Server.

First create an account on [OpenShift website](https://www.openshift.com/),
install the rhc command and run `rhc setup`.

In this example `mydomain` is your domain as returned by the `rhc domain list` command.

    $ rhc create-app dcistable python-3.3 postgresql-9.2
    (...)
    Your application 'dcistable' is now available.
      URL:        http://dcistable-mydomain.rhcloud.com/
      SSH to:     552643edfcf933d464000135@dcistable-mydomain.rhcloud.com
      Git remote: ssh://blablabla@dcistable-mydomain.rhcloud.com/~/git/dcistable.git/
      Cloned to:  /home/goneri/dcistable
    $ rhc env set --app stable DCI_LOGIN=admin DCI_PASSWORD=admin
    $ git push ssh://blablabla@dcistable-mydomain.rhcloud.com/~/git/dcistable.git/ master:master -f

Your website should be able on the http://dcistable-mydomain.rhcloud.com/ URL. If it's not the
case, you can call `rhc tail dcistable` to watch the application logs.


### Manual

#### PostgreSQL configuration

install and configure PostgreSQL:

    # yum install postgresql-server postgresql-contrib
    # postgresql-setup initdb

Allow local account with password:

    # editor /var/lib/pgsql/data/pg_hba.conf

Add the following line on the top of the file:

    host    all             all             127.0.0.1/32            md5

Restart PostgreSQL with the new settings:

    # systemctl restart postgresql.service

Connect with the postgres user:

    sudo su - postgres
    $ createuser -P boa
    Enter password for new role:
    Enter it again:

    $ createdb dci_control_server -O boa
    $ psql -U boa -W -h 127.0.0.1 dci_control_server < db_schema/dci-control-server.sql


# Development

## dependencies to run tox

### Fedora 22

    # dnf install nodejs npm python-tox postgresql-server postgresql-devel postgresql-contrib
    # dnf install python-devel python3-devel libffi-devel git
    # npm install jscs -g


# REST interface

The REST API is available for any type of objects. You can browse the database on http://127.0.0.1:5000/.

# The API documentation

By installing these extra requirements, you can enable the /docs API documentation
end-point:

    # pip install git+https://github.com/hermannsblum/eve-docs
    # pip install Flask-Bootstrap
