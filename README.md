# Distributed CI control server



aaaaaaaaaaaaaaaaa
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

``` sourceCode
$ yum install postgresql-server postgresql-contrib
$ postgresql-setup initdb
```

Allow local account with password:

``` sourceCode
$ editor /var/lib/pgsql/data/pg_hba.conf
```

Add the following line on the top of the file:

``` sourceCode
host    all             all             127.0.0.1/32            md5
```

Restart PostgreSQL with the new settings:

``` sourceCode
$ systemctl restart postgresql.service
```

Connect with the postgres user:

``` sourceCode
$ sudo su - postgres
$ createuser -P dci
Enter password for new role:
Enter it again:

$ createdb dci_control_server -O dci
```

## REST interface

The REST API is available for any type of objects. You can browse the database on <http://127.0.0.1:5000/>.

### Endpoints

The resources of DCI can be accessed through our API in a Restful way. Currently, only the json output format is supported.

Each resource provides two endpoints, one for listing: /resources/, one for fetching a dedicated element: /resources/&lt;resource\_id&gt;/.

On those endpoints we can use some parameters on the GET method to filter, search or complete results.

On the listing endpoint:

`/resources?sort=field1,-field2&limit=20&offset=0&where=field1:foo,field2:bar&embed:resource1,resource2`

-   **sort** parameter will allow the user to sort the listing output according to fields, the sorting is done by ascending results, if the field is prefixed with `-`, the sorting is done descending. The order also matter, it sorts the first field, when its done it sorts the second field with the resources which have the same first field values, and so on. In our example, it will sort ascending on field1 and on resources which have the same value for field1 will sort descending on field2.
-   **limit** parameter is usually used with the offset one in order to paginate results. It will limit the number of resources retrivied, by default it is set to 20 entries, but you can augment that value. Be careful, the more you fetch the longer the http call can be.
-   **offset** parameter is the second pagination parameter, this will indicate at which entry we want to start the listing in the order defined by default or with other parameters.
-   **where** parameter is here to filter the resources according to a field value. In this example we will retrieve the resources which field1 is equal to foo and field2 equal to bar.
-   **embed** parameter is for shipping linked resources in the result, in this example, the result will contain the resource1 and resource2 object into the resources fetched. Like the paginations parameter be careful when using this parameter as it can considerably slow down the http request.

On the resource endpoint:

`/resources/<resource_id>?embed:resource1,resource2`

-   **embed** parameter is the only one available at this endpoint and provides the same features as the one in the listing endpoint.

Concurrency control with etag:

The REST API support etag headers, each request result contains the HTTP header 'ETag' which is a fingerprint of the requested resource.

When a user wants to update or delete a resource then the API requires the user to provide the HTTP header 'If-match' with the corresponding etag in order to prevent concurrency errors.

This mechanism ensure that the user has read the most up to date value of the resource before to update/delete it.

Example:

``` sourceCode
$ http POST http://127.0.0.1:5000/api/v1/componenttypes name=kikoolol
HTTP/1.0 201 CREATED
Content-Length: 217
Content-Type: application/json
Date: Fri, 13 Nov 2015 12:46:18 GMT
ETag: 8f5dc53c14b865d2c2f0ca6654a4a5c2
Server: Werkzeug/0.10.4 Python/2.7.6
```

Here is the etag 'ETag: 8f5dc53c14b865d2c2f0ca6654a4a5c2'.

``` sourceCode
$ http PUT http://127.0.0.1:5000/api/v1/componenttypes/kikoolol name=kikoolol2
HTTP/1.0 412 PRECONDITION FAILED
Content-Length: 92
Content-Type: application/json
Date: Fri, 13 Nov 2015 12:47:33 GMT
Server: Werkzeug/0.10.4 Python/2.7.6
{
    "message": "'If-match' header must be provided",
    "payload": {},
    "status_code": 412
}
```

Here an update request must provide the 'If-match' header.

``` sourceCode
$ http PUT http://127.0.0.1:5000/api/v1/componenttypes/kikoolol \
If-match:8f5dc53c14b865d2c2f0ca6654a4a5c2 name=kikoolol2
HTTP/1.0 204 NO CONTENT
Content-Length: 0
Content-Type: application/json
Date: Fri, 13 Nov 2015 12:48:45 GMT
ETag: 71c076a7ccda10632a40be60ba065511
Server: Eve/0.6 Werkzeug/0.10.4 Python/2.7.6
```

The update succeed and the etag has been updated.

#### Component Type

object attributes:

-   id
-   created\_at
-   updated\_at
-   name

listing url: `/api/v1/componenttypes`

-   `GET`: get all the components type
    -   response: 200 {'componenttypes': \[{componenttype1}, {componenttype2}\]}
-   `POST`: create a component type element
    -   data: {'name': ...}
    -   response: 201 {'componenttype': {componenttype}}

resource url: `/api/v1/componenttypes/<componenttype_id>`

-   `GET`: retrieve the dedicated component type
    -   response: 200 {'componenttype': {componenttype}}
-   `PUT`: update the given component type
    -   data: {'name': ...}
    -   response: 204 {'componenttype': {componentype}}
-   `DELETE`: remove the given component type
    -   response: 204

#### Component

object attributes

-   id
-   created\_at
-   updated\_at
-   name
-   componenttype

listing url: `/api/v1/components`

-   `GET`: get all the components
    -   response: 200 {'components': \[{component1}, {component2}\]}
-   `POST`: create a component element
    -   data: {'name': ..., 'componenttype': ...}
    -   response: 201 {'component': {component}}

resource url: `/api/v1/components/<component_id>`

-   `GET`: retrieve the dedicated component
    -   response: 200 {'component': {component}}
-   `PUT`: update the given component
    -   data: {'name': ..., 'componenttype': ...}
    -   response: 201 {'component': {component}}
-   `DELETE`: remove the given component
    -   response: 204

## License

Apache 2.0

## Author Information

Distributed-CI Team &lt;<distributed-ci@redhat.com>&gt;
