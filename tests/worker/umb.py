import datetime
from dci.worker.umb import build_umb_messages


def test_build_umb_messages():
    now = datetime.datetime(2018, 9, 14, 18, 50, 26, 143559)
    event = {
        "event": "job_finished",
        "type": "job_finished",
        "job": {
            "id": "81fe1916-8929-4bc3-90b6-021983654663",
            "status": "success",
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
            "results": [{"name": "cki-results"}],
        },
    }
    messages = build_umb_messages(event, now)
    target = messages[0]["target"]
    assert target == "topic://VirtualTopic.eng.dci.job.complete"
    message = messages[0]["body"]
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
        "validation"
    ]
    assert message["test"]["result"] in [
        "passed",
        "failed",
        "info",
        "needs_inspection",
        "not_applicable"
    ]
    # system
    assert message["system"] == []
    # todo(gvincent): get arch from job somehow to follow umb factory 2.0 messages
    # assert "provider" in message["system"][0]
    # assert "architecture" in message["system"][0]
    # end todo
    # generated_at
    assert "generated_at" in message
    # version
    assert "version" in message
    assert message == {
        "contact": {
            "name": "DCI CI",
            "team": "DCI",
            "docs": "https://docs.distributed-ci.io/",
            "email": "distributed-ci@redhat.com",
            "url": "https://distributed-ci.io/",
        },
        "run": {
            "url": "https://www.distributed-ci.io/jobs/81fe1916-8929-4bc3-90b6-021983654663/jobStates",  # noqa
            "log": "https://www.distributed-ci.io/jobs/81fe1916-8929-4bc3-90b6-021983654663/jobStates",  # noqa
        },
        "artifact": {
            "compose_type": "nightly",
            "id": "RHEL-8.3.0-20200312.n.0",
            "type": "productmd-compose",
        },
        "pipeline": {"id": "81fe1916-8929-4bc3-90b6-021983654663", "name": "job id"},
        "test": {
            "category": "system",
            "namespace": "dci",
            "type": "cki-results",
            "result": "passed",
        },
        "system": [],
        "generated_at": "2018-09-14T18:50:26.143559Z",
        "version": "0.1.0",
    }
