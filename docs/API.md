
# DCI Server API documentation

## Endpoints

The resources of DCI can be accessed through our API in a Restful way. Currently, only the json output format is supported.

Each resource provides two endpoints, one for listing: `/<resources>/`, one for fetching a dedicated element: `/<resources>/<resource_id>/`.

On those endpoints we can use some parameters on the GET method to filter, search or complete results.

On the listing endpoint:

`/<resources>?sort=field1,-field2&limit=20&offset=0&where=field1:foo,field2:bar`

- **sort** parameter will allow the user to sort the listing output according to fields, the sorting is done by ascending results, if the field is prefixed with `-`, the sorting is done descending. The order also matter, it sorts the first field, when its done it sorts the second field with the resources which have the same first field values, and so on. In our example, it will sort ascending on field1 and on resources which have the same value for field1 will sort descending on field2.
- **limit** parameter is usually used with the offset one in order to paginate results. It will limit the number of resources retrivied, by default it is set to 20 entries, but you can augment that value. Be careful, the more you fetch the longer the http call can be.
- **offset** parameter is the second pagination parameter, this will indicate at which entry we want to start the listing in the order defined by default or with other parameters.
- **where** parameter is here to filter the resources according to a field value. In this example we will retrieve the resources which field1 is equal to foo and field2 equal to bar.

On the resource endpoint:

`/<resources>/<resource_id>`

### Concurrency control with ETag

The REST API support etag headers, each request result contains the HTTP header `ETag` which is a fingerprint of the requested resource.

When a user wants to update or delete a resource then the API requires the user to provide the HTTP header `If-match` with the corresponding `ETag` in order to prevent concurrency errors.

This mechanism ensure that the user has read the most up to date value of the resource before to update/delete it.

Example:

```ShellSession
$ http POST $URL/api/v1/componenttypes name=kikoolol
HTTP/1.0 201 CREATED
Content-Length: 217
Content-Type: application/json
Date: Fri, 13 Nov 2015 12:46:18 GMT
ETag: 8f5dc53c14b865d2c2f0ca6654a4a5c2
Server: Werkzeug/0.10.4 Python/2.7.6
```

Here is the etag `ETag: 8f5dc53c14b865d2c2f0ca6654a4a5c2`.

```ShellSession
$ http PUT $URL/api/v1/componenttypes/kikoolol name=kikoolol2
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

Here an update request must provide the `If-match` header.

```ShellSession
$ http PUT $URL/api/v1/componenttypes/kikoolol \
If-match:8f5dc53c14b865d2c2f0ca6654a4a5c2 name=kikoolol2
HTTP/1.0 204 NO CONTENT
Content-Length: 0
Content-Type: application/json
Date: Fri, 13 Nov 2015 12:48:45 GMT
ETag: 71c076a7ccda10632a40be60ba065511
Server: Eve/0.6 Werkzeug/0.10.4 Python/2.7.6
```

The update succeeded and the `ETag` has been updated.

### Complex where clauses

If you need more complex queries, you can use this format in the `query` parameter:

`/<resources>?sort=<field1>,-<field2>&limit=20&offset=0&query=and(eq(<field1>,foo),eq(<field2>,bar))`

Then the language is defined like that:

`eq(<field>,<value>)` to lookup resources with a `<field>` having the value `<value>`.

You can use the comparison functions `gt` (greater than), `ge` (greater or equal), `lt` (less than) or `le` (less or equal) using the same syntax as `eq`: `<op>(<field>,<value>)`.

`like(<field>,<value with percent>)` and `ilike(<field>,<value with percent>)` to lookup a field with a SQL glob like way.

`contains(<field>,<value1>,...)` and `not_contains(<field>,<value1>,...)` to lookup elements in an array. This is useful mainly for tags.

`and(<op1>(...),<op2>(...))`, `or(<op1>(...),<op2>(...))` and `not(<op>)` allow to build nested boolean queries.

`null(<field>)` to lookup resources with a `field` having a `NULL` value.

### Component Type

object attributes:

- id
- created_at
- updated_at
- name

listing url: `/api/v1/componenttypes`

- `GET`: get all the components type
  - response: 200 {'componenttypes': \[{componenttype1}, {componenttype2}\]}
- `POST`: create a component type element
  - data: {'name': ...}
  - response: 201 {'componenttype': {componenttype}}

resource url: `/api/v1/componenttypes/<componenttype_id>`

- `GET`: retrieve the dedicated component type
  - response: 200 {'componenttype': {componenttype}}
- `PUT`: update the given component type
  - data: {'name': ...}
  - response: 204 {'componenttype': {componentype}}
- `DELETE`: remove the given component type
  - response: 204

### Component

object attributes

- id
- created_at
- updated_at
- released_at
- name
- componenttype

listing url: `/api/v1/components`

- `GET`: get all the components
  - response: 200 {'components': \[{component1}, {component2}\]}
- `POST`: create a component element
  - data: {'name': ..., 'componenttype': ...}
  - response: 201 {'component': {component}}

resource url: `/api/v1/components/<component_id>`

- `GET`: retrieve the dedicated component
  - response: 200 {'component': {component}}
- `PUT`: update the given component
  - data: {'name': ..., 'componenttype': ...}
  - response: 201 {'component': {component}}
- `DELETE`: remove the given component
  - response: 204


## Check if the request is authenticated


Check if the request is authenticated. Returns 200 = success, or 401 = failure.


***Endpoint:***

```bash
Method: GET
Type: 
URL: https://api.distributed-ci.io/api/v1/identity
```



***Responses:***


Status: Check if the request is authenticated | Code: 200




```json
{
    "identity": {
        "email": null,
        "etag": null,
        "fullname": null,
        "id": "6cee7286-5d99-4a96-9949-200977f4be07",
        "name": null,
        "teams": {
            "713ecb86-0157-4445-ad90-c7aa7d0306a0": {
                "team_name": "Red Hat"
            }
        },
        "timezone": null
    }
}
```



## Get all topics


Get all topics


***Endpoint:***

```bash
Method: GET
Type: 
URL: https://api.distributed-ci.io/api/v1/topics
```



## Get a topic id by topic name


Get topic id by topic name:

	GET /api/v1/topics?where=name:<topic_name>
    response.data.topic
    {
      id: <topic_id>
    }
    
`id: <topic_id>` in response body should be saved for later use in requests: Get components for a topic and Create a new job


***Endpoint:***

```bash
Method: GET
Type: 
URL: https://api.distributed-ci.io/api/v1/topics
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| where | name:RHEL-8.2 |  |



***Responses:***


Status: Get a topic id by topic name | Code: 200


```json
{
    "_meta": {
        "count": 1
    },
    "topics": [
        {
            "component_types": [
                "Compose",
                "hwcert"
            ],
            "created_at": "2019-10-10T06:14:55.269457",
            "data": {},
            "etag": "6d279adf27286020ef95eec7349f317c",
            "export_control": false,
            "id": "c4171062-e2b4-4b60-9a5f-3e2fb32b4f68",
            "name": "RHEL-8.2",
            "next_topic_id": null,
            "product_id": "b3d8d6f3-8223-4553-bf08-9b2cecb869f2",
            "state": "active",
            "updated_at": "2019-10-10T06:15:07.565374"
        }
    ]
}
```



## Get components for a topic


GET /api/v1/topics/\<topic_id\>/components <br>

where topic_id is obtained from Get topic id by name request.

	response.data.components
    [
        {
            id: <component_id_1>
        },
        {
            id: <component_id_2>
        },
    ]


***Endpoint:***

```bash
Method: GET
Type: 
URL: https://api.distributed-ci.io/api/v1/topics/c4171062-e2b4-4b60-9a5f-3e2fb32b4f68/components
```



***Responses:***


Status: Get components for a topic | Code: 200



```json
{
    "_meta": {
        "count": 21
    },
    "components": [
        {
            "canonical_project_name": "RHEL-8.2.0-20191029.n.0",
            "created_at": "2019-10-29T05:45:00.790012",
            "data": {},
            "etag": "729416351fa3e5ee5d72bfa0a336d55d",
            "id": "4e7a2754-9871-41ad-9444-665219fd0745",
            "message": null,
            "name": "RHEL-8.2.0-20191029.n.0",
            "state": "active",
            "title": null,
            "topic_id": "c4171062-e2b4-4b60-9a5f-3e2fb32b4f68",
            "type": "Compose",
            "updated_at": "2019-10-29T07:08:46.539578",
            "url": "http://download-node-02.eng.bos.redhat.com/rhel-8/nightly/RHEL-8/RHEL-8.2.0-20191029.n.0"
        },
        {
            "canonical_project_name": "hwcert-1572272875",
            "created_at": "2019-10-28T14:45:00.572710",
            "data": {
                "path": "/packages/devel/RHEL8",
                "repo_name": "rhcert-dev-el8",
                "version": "hwcert-server.khw2.lab.eng.bos.redhat.com"
            },
            "etag": "d1992b9538ad3d01288b6ecd7f91928c",
            "id": "8c8f22fd-611a-4284-9cde-057c8d2599b7",
            "message": null,
            "name": "hwcert-1572272875",
            "state": "active",
            "title": null,
            "topic_id": "c4171062-e2b4-4b60-9a5f-3e2fb32b4f68",
            "type": "hwcert",
            "updated_at": "2019-10-28T14:45:44.252868",
            "url": "http://hwcert-server.khw2.lab.eng.bos.redhat.com/packages/devel/RHEL8"
        },
        {
            "canonical_project_name": "RHEL-8.2.0-20191028.n.0",
            "created_at": "2019-10-28T05:45:00.063471",
            "data": {},
            "etag": "04276278c6a6def258010a4e950c92d4",
            "id": "a3587df1-83f0-418c-8a97-094df763006d",
            "message": null,
            "name": "RHEL-8.2.0-20191028.n.0",
            "state": "active",
            "title": null,
            "topic_id": "c4171062-e2b4-4b60-9a5f-3e2fb32b4f68",
            "type": "Compose",
            "updated_at": "2019-10-28T07:06:18.939543",
            "url": "http://download-node-02.eng.bos.redhat.com/rhel-8/nightly/RHEL-8/RHEL-8.2.0-20191028.n.0"
        },
        {
            "canonical_project_name": "RHEL-8.2.0-20191027.n.0",
            "created_at": "2019-10-27T05:44:59.913636",
            "data": {},
            "etag": "9a66c947bfc5ac88329688b92cd7a186",
            "id": "9242b2c6-4c6b-4547-8688-ed8a77330cc0",
            "message": null,
            "name": "RHEL-8.2.0-20191027.n.0",
            "state": "active",
            "title": null,
            "topic_id": "c4171062-e2b4-4b60-9a5f-3e2fb32b4f68",
            "type": "Compose",
            "updated_at": "2019-10-27T07:13:04.559639",
            "url": "http://download-node-02.eng.bos.redhat.com/rhel-8/nightly/RHEL-8/RHEL-8.2.0-20191027.n.0"
        },
        {
            "canonical_project_name": "RHEL-8.2.0-20191026.n.0",
            "created_at": "2019-10-26T05:44:59.542342",
            "data": {},
            "etag": "9b3e12c39a027dec726d9be90e4b0fda",
            "id": "530c727c-22f0-486a-98a8-868b21c42d13",
            "message": null,
            "name": "RHEL-8.2.0-20191026.n.0",
            "state": "inactive",
            "title": null,
            "topic_id": "c4171062-e2b4-4b60-9a5f-3e2fb32b4f68",
            "type": "Compose",
            "updated_at": "2019-10-29T07:08:48.150986",
            "url": "http://download-node-02.eng.bos.redhat.com/rhel-8/nightly/RHEL-8/RHEL-8.2.0-20191026.n.0"
        },
        {
            "canonical_project_name": "RHEL-8.2.0-20191025.n.0",
            "created_at": "2019-10-25T05:45:00.658373",
            "data": {},
            "etag": "87cb1dd32f4e56ded9d1bd93813e0fc4",
            "id": "c5f4993c-aefe-40bc-a628-d51febccb773",
            "message": null,
            "name": "RHEL-8.2.0-20191025.n.0",
            "state": "inactive",
            "title": null,
            "topic_id": "c4171062-e2b4-4b60-9a5f-3e2fb32b4f68",
            "type": "Compose",
            "updated_at": "2019-10-28T07:06:20.549124",
            "url": "http://download-node-02.eng.bos.redhat.com/rhel-8/nightly/RHEL-8/RHEL-8.2.0-20191025.n.0"
        }
    ]
}
```



## Get all jobs


Get all jobs


***Endpoint:***

```bash
Method: GET
Type: 
URL: https://api.distributed-ci.io/api/v1/jobs
```



## Create a new job


Create a new job:

	POST /api/v1/jobs/
    {
        components: [component_id],
        topic_id: topic_id
    }
    response.data.job
    {
        id: <job_id>
    }
    
Current implementation also allows
	
	POST /api/v1/jobs/schedule
    {
        topic_id: topic_id
    }
and will automatically associate the latest components of each component type that compose this topic, ie. latest Compose and latest hwcert for RHEL-8.2.


***Endpoint:***

```bash
Method: POST
Type: RAW
URL: https://api.distributed-ci.io/api/v1/jobs
```


***Headers:***

| Key | Value | Description |
| --- | ------|-------------|
| Content-Type | application/json |  |



***Body:***

```js        
{
 "components": ["d4bcd2e2-98df-4962-b224-8d50eedaba1b"],
 "topic_id": "c4171062-e2b4-4b60-9a5f-3e2fb32b4f68"
}
```



***Responses:***


Status: Create a new job | Code: 201




```js
{
    "job": {
        "client_version": null,
        "comment": null,
        "created_at": "2019-10-28T00:11:35.988480",
        "duration": 0,
        "etag": "325a2aba9b3ef362dc2e5e93671d76d5",
        "id": "bf878d0c-3119-4194-913b-1da1cf3a19fa",
        "previous_job_id": null,
        "product_id": "b3d8d6f3-8223-4553-bf08-9b2cecb869f2",
        "remoteci_id": "6cee7286-5d99-4a96-9949-200977f4be07",
        "state": "active",
        "status": "new",
        "team_id": "713ecb86-0157-4445-ad90-c7aa7d0306a0",
        "topic_id": "c4171062-e2b4-4b60-9a5f-3e2fb32b4f68",
        "topic_id_secondary": null,
        "update_previous_job_id": null,
        "updated_at": "2019-10-28T00:11:35.988480",
        "user_agent": "PostmanRuntime/7.18.0"
    }
}
```



## Change a job state to pre-run


A job can have different states: ['new', 'pre-run', 'running', 'post-run', 'success', 'failure', 'killed', 'error']. <br>
When a job is created its state is 'new'. 
At the end of a partner remote CI run job_state should be changed to success or failure for the created job.


***Endpoint:***

```bash
Method: POST
Type: RAW
URL: https://api.distributed-ci.io/api/v1/jobstates
```


***Headers:***

| Key | Value | Description |
| --- | ------|-------------|
| Content-Type | application/json |  |



***Body:***

```json
{
 "job_id": "bf878d0c-3119-4194-913b-1da1cf3a19fa",
 "status": "pre-run"
}
```



***Responses:***


Status: Change  a job state to pre-run | Code: 201




```js
{
    "jobstate": {
        "comment": null,
        "created_at": "2019-10-28T00:12:38.505403",
        "id": "011522e8-da95-49a1-a357-c9696f9c7519",
        "job_id": "bf878d0c-3119-4194-913b-1da1cf3a19fa",
        "status": "pre-run"
    }
}
```



## Change a job state to running



***Endpoint:***

```bash
Method: POST
Type: RAW
URL: https://api.distributed-ci.io/api/v1/jobstates
```


***Headers:***

| Key | Value | Description |
| --- | ------|-------------|
| Content-Type | application/json |  |



***Body:***

```json
{
 "job_id": "bf878d0c-3119-4194-913b-1da1cf3a19fa",
 "status": "running"
}
```



***Responses:***


Status: Change  a job state to running | Code: 201



```json
{
    "jobstate": {
        "comment": null,
        "created_at": "2019-10-24T15:41:46.341813",
        "id": "c078619b-8712-4e68-b5ab-54e90c03295c",
        "job_id": "9943ce77-4012-4ab3-a91a-c3387acc777c",
        "status": "running"
    }
}
```



## Change a job state to success


When a job is created it has a state 'new'. A job can have different states: ['new', 'pre-run', 'running', 'post-run', 'success', 'failure', 'killed', 'error']. At the end of a partner remote CI run job_state should be changed to success or failure for the created job.
    POST /api/v1/jobstates
 Request body:
   {
        'job_id': <job_id>, 
        'status': 'success'
    }


***Endpoint:***

```bash
Method: POST
Type: RAW
URL: https://api.distributed-ci.io/api/v1/jobstates
```


***Headers:***

| Key | Value | Description |
| --- | ------|-------------|
| Content-Type | application/json |  |



***Body:***

```json
{
 "job_id": "bf878d0c-3119-4194-913b-1da1cf3a19fa",
 "status": "success"
}
```



***Responses:***


Status: Change  a job state to success | Code: 201



```json
{
    "jobstate": {
        "comment": null,
        "created_at": "2019-10-24T15:42:50.932397",
        "id": "1135f979-35ed-4921-b310-e18076782dae",
        "job_id": "9943ce77-4012-4ab3-a91a-c3387acc777c",
        "status": "success"
    }
}
```



## Change a job state to failure


A job can have different states: ['new', 'pre-run', 'running', 'post-run', 'success', 'failure', 'killed', 'error']. <br>
When a job is created its state is 'new'. 
At the end of a partner remote CI run job_state should be changed to success or failure for the created job.

	POST /api/v1/jobstates
	Request body:
	{
        'job_id': <job_id>, 
        'status': 'failure'
	}


***Endpoint:***

```bash
Method: POST
Type: RAW
URL: https://api.distributed-ci.io/api/v1/jobstates
```


***Headers:***

| Key | Value | Description |
| --- | ------|-------------|
| Content-Type | application/json |  |



***Body:***

```json
{
 "job_id": "bf878d0c-3119-4194-913b-1da1cf3a19fa",
 "status": "failure"
}
```



***Responses:***


Status: Change  a job state to failure | Code: 201


```json
{
    "jobstate": {
        "comment": null,
        "created_at": "2019-10-24T15:43:36.102530",
        "id": "c3cb7013-4e2e-409a-99c4-d9d793adff9a",
        "job_id": "9943ce77-4012-4ab3-a91a-c3387acc777c",
        "status": "failure"
    }
}
```



## Upload test results


Upload test results:

	POST /api/v1/files
    headers = {
        'DCI-JOB-ID': <job_id>,
        'DCI-NAME': <file_name>,
        'DCI-MIME': 'application/junit',
    }
    data = <file_content>
    response.data.file
    {
        id: <file_id>
    }


***Endpoint:***

```bash
Method: POST
Type: RAW
URL: https://api.distributed-ci.io/api/v1/files
```


***Headers:***

| Key | Value | Description |
| --- | ------|-------------|
| DCI-NAME | test-result.log |  |
| DCI-MIME | application/junit |  |
| DCI-JOB-ID | bf878d0c-3119-4194-913b-1da1cf3a19fa |  |



***Body:***

```json
{
 "job_id": "bf878d0c-3119-4194-913b-1da1cf3a19fa",
 "status": "failure"
}
```



***Responses:***


Status: Upload test results | Code: 201



```json
{
    "file": {
        "created_at": "2019-10-29T15:34:48.962810",
        "etag": "0a7200c0e3223ffcb78ace010e5ea10e",
        "id": "deba6adf-aba1-4db3-800a-aa491bde7394",
        "job_id": "bf878d0c-3119-4194-913b-1da1cf3a19fa",
        "jobstate_id": null,
        "md5": null,
        "mime": "application/junit",
        "name": "test-result.log",
        "size": "75",
        "state": "active",
        "team_id": "713ecb86-0157-4445-ad90-c7aa7d0306a0",
        "updated_at": "2019-10-29T15:34:48.962824"
    }
}
```
