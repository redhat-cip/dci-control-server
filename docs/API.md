
# DCI Server API documentation

Subset of DCI server API calls related to HMAC authentication, identity, create job and upload test results.

## Indices

* [DCI Server](#dci-server)

  * [Check if the request is authenticated](#1-check-if-the-request-is-authenticated)
  * [Get all topics](#2-get-all-topics)
  * [Get a topic id by topic name](#3-get-a-topic-id-by-topic-name)
  * [Get components for a topic](#4-get-components-for-a-topic)
  * [Get all jobs](#5-get-all-jobs)
  * [Create a new job](#6-create-a-new-job)
  * [Change  a job state to pre-run](#7-change--a-job-state-to-pre-run)
  * [Change  a job state to running](#8-change--a-job-state-to-running)
  * [Change  a job state to success](#9-change--a-job-state-to-success)
  * [Change  a job state to failure](#10-change--a-job-state-to-failure)
  * [Upload test results](#11-upload-test-results)


--------


## DCI Server



### 1. Check if the request is authenticated


Check if the request is authenticated. Returns 200 = success, or 401 = failure.


***Endpoint:***

```bash
Method: GET
Type: 
URL: https://api.distributed-ci.io/api/v1/identity
```



***Responses:***


Status: Check if the request is authenticated | Code: 200




```js
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



### 2. Get all topics


Get all topics


***Endpoint:***

```bash
Method: GET
Type: 
URL: https://api.distributed-ci.io/api/v1/topics
```



### 3. Get a topic id by topic name


Get topic id by topic name:

	GET /api/v1/topics?where=name:<topic_name>
    response.data.topic
    {
      id: <topic_id>
    }
    
id: \<topic_id\> in response body should be saved for later use in requests: Get components for a topic and Create a new job


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


```js
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



### 4. Get components for a topic


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



```js
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



### 5. Get all jobs


Get all jobs


***Endpoint:***

```bash
Method: GET
Type: 
URL: https://api.distributed-ci.io/api/v1/jobs
```



### 6. Create a new job


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



### 7. Change  a job state to pre-run


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

```js        
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



### 8. Change  a job state to running



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

```js        
{
 "job_id": "bf878d0c-3119-4194-913b-1da1cf3a19fa",
 "status": "running"
}
```



***Responses:***


Status: Change  a job state to running | Code: 201



```js
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



### 9. Change  a job state to success


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

```js        
{
 "job_id": "bf878d0c-3119-4194-913b-1da1cf3a19fa",
 "status": "success"
}
```



***Responses:***


Status: Change  a job state to success | Code: 201



```js
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



### 10. Change  a job state to failure


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

```js        
{
 "job_id": "bf878d0c-3119-4194-913b-1da1cf3a19fa",
 "status": "failure"
}
```



***Responses:***


Status: Change  a job state to failure | Code: 201


```js
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



### 11. Upload test results


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

```js        
{
 "job_id": "bf878d0c-3119-4194-913b-1da1cf3a19fa",
 "status": "failure"
}
```



***Responses:***


Status: Upload test results | Code: 201



```js
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
        "test_id": null,
        "updated_at": "2019-10-29T15:34:48.962824"
    }
}
```