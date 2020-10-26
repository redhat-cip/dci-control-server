import json
import datetime
from dci.worker.umb import build_umb_messages
from uuid import UUID


def test_build_umb_messages():
    now = datetime.datetime(2018, 9, 14, 18, 50, 26, 143559)
    event = {
        "event": "job_finished",
        "type": "job_finished",
        "job": {
            "id": "81fe1916-8929-4bc3-90b6-021983654663",
            "status": "success",
            "tags": ["debug"],
            "components": [
                {
                    "id": "3b59723c-4033-ba46-8df2-d93fdad1af8b",
                    "name": "hwcert-1584013618",
                    "type": "hwcert",
                    "url": "http://hwcert-server.khw2.lab.eng.bos.redhat.com/packages/devel/RHEL8",  # noqa
                },
                {
                    "id": "b7c82f18-d2ac-ba46-b909-a7bb472f5ba9",
                    "name": "RHEL-8.3.0-20200312.n.0",
                    "type": "Compose",
                    "url": "http://download-node-02.eng.bos.redhat.com/rhel-8/nightly/RHEL-8/RHEL-8.3.0-20200312.n.0",  # noqa
                },
            ],
            "results": [{"name": "beaker-results"}],
        },
    }
    messages = build_umb_messages(event, now)
    target = messages[0]["target"]
    assert target == "topic://VirtualTopic.eng.dci.job.complete"
    message = json.loads(messages[0]["body"])
    # fedora-ci productmd-compose.test.complete.yaml schema
    # contact
    assert "name" in message["contact"]
    assert "team" in message["contact"]
    assert "docs" in message["contact"]
    assert "email" in message["contact"]
    # run
    assert "url" in message["run"]
    assert "log" in message["run"]
    # artifact
    assert "id" in message["artifact"]
    assert "type" in message["artifact"]
    assert "compose_type" in message["artifact"]
    assert message["artifact"]["compose_type"] in ["nightly", "rel-eng"]
    # pipeline
    assert "id" in message["pipeline"]
    assert "name" in message["pipeline"]
    # test-common
    # test-complete
    assert "category" in message["test"]
    assert "namespace" in message["test"]
    assert "type" in message["test"]
    assert "result" in message["test"]
    assert message["test"]["category"] in [
        "functional",
        "integration",
        "interoperability",
        "static-analysis",
        "system",
        "validation",
    ]
    assert message["test"]["result"] in [
        "passed",
        "failed",
        "info",
        "needs_inspection",
        "not_applicable",
    ]
    # system
    assert "provider" in message["system"][0]
    assert "architecture" in message["system"][0]
    # generated_at
    assert "generated_at" in message
    # version
    assert "version" in message
    print(message)
    assert message == {
        u"contact": {
            u"docs": u"https://docs.distributed-ci.io/",
            u"url": u"https://distributed-ci.io/",
            u"team": u"DCI",
            u"name": u"DCI CI",
            u"email": u"distributed-ci@redhat.com",
        },
        u"artifact": {
            u"compose_type": u"nightly",
            u"type": u"productmd-compose",
            u"id": u"RHEL-8.3.0-20200312.n.0",
        },
        u"run": {
            u"log": u"https://www.distributed-ci.io/jobs/81fe1916-8929-4bc3-90b6-021983654663/jobStates",
            u"url": u"https://www.distributed-ci.io/jobs/81fe1916-8929-4bc3-90b6-021983654663/jobStates",
        },
        u"test": {
            u"namespace": u"dci",
            u"type": u"beaker-results",
            u"result": u"passed",
            u"category": u"system",
        },
        u"pipeline": {
            u"id": u"81fe1916-8929-4bc3-90b6-021983654663",
            u"name": u"job id",
        },
        u"system": [{"provider": "beaker", "architecture": "x86_64"}],
        u"generated_at": u"2018-09-14T18:50:26.143559Z",
        u"version": u"0.1.0",
    }


def test_cki_message():
    now = datetime.datetime(2020, 10, 20, 7, 52, 15, 241148)
    event = {
        "event": "job_finished",
        "type": "job_finished",
        "job": {
            "comment": "releng job comment",
            "status": "success",
            "user_agent": "python-requests/2.6.0 CPython/2.7.5 Linux/5.8.11-200.fc32.x86_64",
            "remoteci_id": UUID("ab632138-55da-45c9-b64a-d06fb941fe3c"),
            "tags": ["debug", "ppc64le"],
            "previous_job_id": None,
            "created_at": datetime.datetime(2020, 10, 20, 8, 42, 12, 384316),
            "remoteci": {
                "cert_fp": None,
                "name": "Remoteci partner",
                "api_secret": "u1ZthjIrvDOyQ7kLsmkHAtPYbUKRulywqaiXUdBHeKAZYvzUlZbgPw5BswOOIaWm",
                "created_at": datetime.datetime(2020, 10, 20, 7, 56, 18, 195947),
                "updated_at": datetime.datetime(2020, 10, 20, 7, 56, 18, 195947),
                "id": UUID("ab632138-55da-45c9-b64a-d06fb941fe3c"),
                "state": "active",
                "etag": "f54cacaec95ab19a8ad067a98eb90a8d",
                "team_id": UUID("627d5b72-6213-490e-83b9-6a07df2d20a8"),
                "data": {},
                "public": False,
            },
            "updated_at": datetime.datetime(2020, 10, 20, 8, 43, 27, 165594),
            "update_previous_job_id": None,
            "results": [
                {
                    "errors": 0,
                    "job_id": UUID("6015a9ae-15a3-4e1f-8603-0daf95da6da6"),
                    "success": 1,
                    "created_at": datetime.datetime(2020, 10, 20, 8, 43, 26, 833558),
                    "updated_at": datetime.datetime(2020, 10, 20, 8, 43, 26, 842542),
                    "successfixes": 0,
                    "id": UUID("b22ca408-063a-494e-8887-7af8c8247bad"),
                    "skips": 0,
                    "testcases": [
                        {
                            "successfix": False,
                            "name": "exit_code",
                            "value": "",
                            "classname": "LTP",
                            "time": 0.53,
                            "action": "passed",
                            "message": "",
                            "type": "",
                            "regression": False,
                        },
                        {
                            "successfix": False,
                            "name": "RHELKT1LITE.FILTERED",
                            "value": "Logs:\nrecipes/1/tasks/1/results/1603842751/logs/dmesg.log\nrecipes/1/tasks/1/results/1603842751/logs/resultoutputfile.log",
                            "classname": "LTP",
                            "time": 10.247,
                            "action": "failure",
                            "message": "",
                            "type": "",
                            "regression": False,
                        },
                    ],
                    "file_id": UUID("75a45e48-d255-490c-a80e-5ba67588650a"),
                    "time": 10.777,
                    "failures": 1,
                    "total": 2,
                    "regressions": 0,
                    "name": "cki-results",
                }
            ],
            "topic": {
                "next_topic_id": None,
                "name": "RHEL-8.2-milestone",
                "created_at": datetime.datetime(2020, 10, 20, 7, 56, 15, 241148),
                "updated_at": datetime.datetime(2020, 10, 20, 7, 56, 15, 241148),
                "id": UUID("bbd380b0-a291-443b-8743-b0fc53314db6"),
                "state": "active",
                "etag": "c804a7353f1dca5c4c6ec2a7770fd307",
                "component_types": ["Compose"],
                "data": {},
                "export_control": True,
                "product_id": UUID("8c5ce412-9f43-4cc6-b70d-2146d3938ac3"),
            },
            "team_id": UUID("627d5b72-6213-490e-83b9-6a07df2d20a8"),
            "state": "active",
            "etag": "524fd81818986991317e29214e10f0e7",
            "components": [
                {
                    "name": "RHEL-8.2.0-20200404.0",
                    "tags": ["kernel:4.18.0-240.3.el8"],
                    "url": "http://download-node-02.eng.bos.redhat.com/rhel-8/rel-eng/RHEL-8/RHEL-8.2.0-20200404.0",  # noqa
                    "type": "Compose",
                    "created_at": datetime.datetime(2020, 10, 20, 7, 56, 17, 93452),
                    "title": None,
                    "updated_at": datetime.datetime(2020, 10, 20, 7, 56, 17, 93452),
                    "released_at": datetime.datetime(2020, 10, 20, 7, 56, 17, 94224),
                    "canonical_project_name": None,
                    "state": "active",
                    "etag": "de27226e8db2157d9aaf6ff6b32a228a",
                    "topic_id": UUID("bbd380b0-a291-443b-8743-b0fc53314db6"),
                    "team_id": None,
                    "message": None,
                    "data": {},
                    "id": UUID("d1c36709-f401-4eb0-ba45-e91726ad0981"),
                }
            ],
            "topic_id": UUID("bbd380b0-a291-443b-8743-b0fc53314db6"),
            "duration": 74,
            "client_version": None,
            "id": UUID("6015a9ae-15a3-4e1f-8603-0daf95da6da6"),
            "product_id": UUID("8c5ce412-9f43-4cc6-b70d-2146d3938ac3"),
        },
    }
    messages = build_umb_messages(event, now)
    message = json.loads(messages[0]["body"])
    assert message == {
        u"summarized_result": u"",
        u"team_email": u"distributed-ci@redhat.com",
        u"team_name": u"DCI",
        u"kernel_version": u"4.18.0-240.3.el8",
        u"artifact": {
            u"compose_type": u"rel-eng",
            u"id": u"RHEL-8.2.0-20200404.0",
            u"type": u"productmd-compose",
        },
        "results": [
            {
                u"test_description": u"LTP",
                u"is_debug": False,
                u"test_log_url": [
                    u"https://www.distributed-ci.io/jobs/6015a9ae-15a3-4e1f-8603-0daf95da6da6/jobStates"
                ],
                u"test_arch": u"ppc64le",
                u"test_result": u"PASS",
                u"test_name": u"exit_code",
            },
            {
                u"test_description": u"LTP",
                u"is_debug": False,
                u"test_log_url": [
                    u"https://www.distributed-ci.io/jobs/6015a9ae-15a3-4e1f-8603-0daf95da6da6/jobStates"
                ],
                u"test_arch": u"ppc64le",
                u"test_result": u"PASS",
                u"test_name": u"RHELKT1LITE.FILTERED",
            },
        ],
    }
