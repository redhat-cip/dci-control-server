# DCI Control-server

## installation

### Deploy on local machine for development

By default the database should be accessible at 'postgresql://dci:dci@127.0.0.1:5432/dci'.

Simply run the runtestserver.py script, it will listen by default to '127.0.0.1:5000'.

    $ ./runtestserver.py
     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
     * Restarting with stat

You can initialize the database with fake entries by launching the following command line:

    $ ./samples/db_provisioning.py

BE CAREFUL: this script will override your database, so use it after saving your datas.

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
    $ echo 'CREATE EXTENSION pgcrypto;' | psql dci_control_server
    $ psql -U boa -W -h 127.0.0.1 dci_control_server < db_schema/dci-control-server.sql


# Development

## dependencies to run tox

### Fedora 22

    # dnf install nodejs npm python-tox postgresql-server postgresql-devel postgresql-contrib
    # dnf install python-devel python3-devel libffi-devel git
    # npm install jscs -g

## Use docker-compose
You can develop into a safe environment by using [docker-compose](http://docs.docker.com/compose/)

* Install docker-compose by typing `pip install docker-compose`
* Run the environment by typing `docker-compose -f compose/dci.yml up`
* You can now attach the containers needed by typing `docker attach <container_name or container_id>`


# REST interface

The REST API is available for any type of objects. You can browse the database on http://127.0.0.1:5000/.

## Endpoints

The resources of DCI can be accessed through our API in a Restful way.
Currently, only the json output format is supported.

Each resource provides two endpoints, one for listing: `/resources/`,
one for fetching a dedicated element: `/resources/<resource_id>/`.

On those endpoints we can use some parameters on the GET method to filter,
search or complete results.

On the listing endpoint:

`/resources?sort=field1,-field2&limit=20&offset=0&where=field1:foo,field2:bar&embed:resource1,resource2`

* `sort` parameter will allow the user to sort the listing output according to
fields, the sorting is done by ascending results, if the field is prefixed with
`-`, the sorting is done descending. The order also matter, it sorts the first
field, when its done it sorts the second field with the resources which have
the same first field values, and so on. In our example, it will sort ascending
on field1 and on resources which have the same value for field1 will sort
descending on field2.

* `limit` parameter is usually used with the offset one in order to paginate
results. It will limit the number of resources retrivied, by default it is
set to 20 entries, but you can augment that value. Be careful, the more you
fetch the longer the http call can be.

* `offset` parameter is the second pagination parameter, this will indicate at
which entry we want to start the listing in the order defined by default or
with other parameters.

* `where` parameter is here to filter the resources according to a field value.
In this example we will retrieve the resources which field1 is equal to foo and
field2 equal to bar.

* `embed` parameter is for shipping linked resources in the result, in this
example, the result will contain the resource1 and resource2 object into the
resources fetched. Like the paginations parameter be careful when using this
parameter as it can considerably slow down the http request.

On the resource endpoint:

`/resources/<resource_id>?embed:resource1,resource2`

* `embed` parameter is the only one available at this endpoint and provides
the same features as the one in the listing endpoint.

Concurrency control with etag:

The REST API support etag headers, each request result contains the HTTP
header 'ETag' which is a fingerprint of the requested resource.

When a user wants to update or delete a resource then the API requires the
user to provide the HTTP header 'If-match' with the corresponding etag in
order to prevent concurrency errors.

This mechanism ensure that the user has read the most up to date value of the
resource before to update/delete it.

Example:

    $ http POST http://127.0.0.1:5000/api/v1/componenttypes name=kikoolol
    HTTP/1.0 201 CREATED
    Content-Length: 217
    Content-Type: application/json
    Date: Fri, 13 Nov 2015 12:46:18 GMT
    ETag: 8f5dc53c14b865d2c2f0ca6654a4a5c2
    Server: Eve/0.6 Werkzeug/0.10.4 Python/2.7.6

Here is the etag 'ETag: 8f5dc53c14b865d2c2f0ca6654a4a5c2'.

    $ http PUT http://127.0.0.1:5000/api/v1/componenttypes/kikoolol name=kikoolol2
    HTTP/1.0 412 PRECONDITION FAILED
    Content-Length: 92
    Content-Type: application/json
    Date: Fri, 13 Nov 2015 12:47:33 GMT
    Server: Eve/0.6 Werkzeug/0.10.4 Python/2.7.6

    {
        "message": "'If-match' header must be provided",
        "payload": {},
        "status_code": 412
    }

Here an update request must provide the 'If-match' header.

    $ http PUT http://127.0.0.1:5000/api/v1/componenttypes/kikoolol \
    If-match:8f5dc53c14b865d2c2f0ca6654a4a5c2 name=kikoolol2
    HTTP/1.0 204 NO CONTENT
    Content-Length: 0
    Content-Type: application/json
    Date: Fri, 13 Nov 2015 12:48:45 GMT
    ETag: 71c076a7ccda10632a40be60ba065511
    Server: Eve/0.6 Werkzeug/0.10.4 Python/2.7.6

The update succeed and the etag has been updated.

### Component Type

object attributes:

* id
* created_at
* updated_at
* name


listing url: `/api/v1/componenttypes`

*   `GET`: get all the components type

    response: 200 {'componenttypes': [{componenttype1}, {componenttype2}]}

*   `POST`: create a component type element

    data: {'name': ...}

    response: 201 {'componenttype': {componenttype}}

resource url: `/api/v1/componenttypes/<componenttype_id>`

*   `GET`: retrieve the dedicated component type

    response: 200 {'componenttype': {componenttype}}

*   `PUT`: update the given component type

    data: {'name': ...}

    response: 204 {'componenttype': {componentype}}

*   `DELETE`: remove the given component type

    response: 204


### Component

object attributes

* id
* created_at
* updated_at
* name
* componenttype

listing url: `/api/v1/components`

*   `GET`: get all the components

    response: 200 {'components': [{component1}, {component2}]}

*   `POST`: create a component element

    data: {'name': ..., 'componenttype': ...}

    response: 201 {'component': {component}}

resource url: `/api/v1/components/<component_id>`

*   `GET`: retrieve the dedicated component

    response: 200 {'component': {component}}

*   `PUT`: update the given component

    data: {'name': ..., 'componenttype': ...}

    response: 201 {'component': {component}}

*   `DELETE`: remove the given component

    response: 204

# The API documentation

By installing these extra requirements, you can enable the /docs API documentation
end-point:

    # pip install git+https://github.com/hermannsblum/eve-docs
    # pip install Flask-Bootstrap

## Recheck a job

    $ http --form POST http://127.0.0.1:5000/api/jobs?recheck=1&job_id=job_id_to_recheck

This will create a new job with the flag 'recheck' set to True and with the same
datas as in the job to recheck.

The agent could check if there is some jobs to recheck with:

    $ http GET http://127.0.0.1:5000/api/jobs?where={'remoteci_id': 'myremoteci_id', 'recheck': 'True'}

After it finish, it set the recheck flag to False.

## Jobs priorities

Each jobdefinition contains a 'priority' attribute which is used to weight it. When an agent requests
a new job then the server will sort the jobdefinition by using the 'priority' attribute in order to
select one.
