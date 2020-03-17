from dci.worker.umb import build_umb_message


def test_build_umb_message():
    target, message = build_umb_message(
        {"job_id": "81fe1916-8929-4bc3-90b6-021983654663"}
    )
    assert target == "/topic/VirtualTopic.eng.ci.productmd-compose.test.complete"
    assert message == {}

