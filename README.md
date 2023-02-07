# Distributed CI control server

![](https://img.shields.io/badge/license-Apache2.0-blue.svg?style=flat) ![](https://img.shields.io/badge/python-2.7,3.5-green.svg?style=flat)

This repository is used for the development of the API of Distributed CI. It contains the source code, tests, development and building scripts.

## Getting started

If you are using the development environment provided [here](https://github.com/redhat-cip/dci-dev-env) you can directly start at step 5.

To run the api in development mode follow those steps:

1.  clone the repository: <http://softwarefactory-project.io/r/dci-control-server>
2.  ensure that a postgresql database is running and accessible on the URI defined in the `src/settings.py` (if no database is running see [database installation]())
3.  install the python requirements: `pip install -r requirements.txt`
4.  run the dev server: `./bin/dci-runtestserver`
5.  provision the database: `python bin/dci-dbprovisioning` (BEWARE: it will erase the previous db)

## Database installation

Assuming that we are running on a fedora based distribution here are the steps for installing the database which will be used by the API and its tests.

install and configure PostgreSQL:

```sourceCode
$ yum install postgresql-server postgresql-contrib
$ postgresql-setup initdb
```

Allow local account with password:

```sourceCode
$ editor /var/lib/pgsql/data/pg_hba.conf
```

Add the following line on the top of the file:

```sourceCode
host    all             all             127.0.0.1/32            md5
```

Restart PostgreSQL with the new settings:

```sourceCode
$ systemctl restart postgresql.service
```

Connect with the postgres user:

```sourceCode
$ sudo su - postgres
$ createuser -P dci
Enter password for new role:
Enter it again:

$ createdb dci_control_server -O dci
```

## REST interface

The REST API is available for any type of objects. You can browse the database on <http://127.0.0.1:5000/>.

See [API doc](docs/API.md) for details.

## License

Apache 2.0

## Author Information

Distributed-CI Team <distributed-ci@redhat.com>
