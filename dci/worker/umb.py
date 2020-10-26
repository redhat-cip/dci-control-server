import datetime
import json
import os
import logging

from dci_umb.sender import send

logger = logging.getLogger(__name__)


def _get_architecture(job):
    arch = "x86_64"
    available_arches = ["x86_64", "ppc64le", "aarch64", "s390x"]
    for available_arch in available_arches:
        if available_arch in job["tags"]:
            arch = available_arch
            break
    return arch


def _build_generic_message(job, component, result, now):
    test_name = result["name"]
    job_id = str(job["id"])
    job_url = "https://www.distributed-ci.io/jobs/%s/jobStates" % job_id
    target = "topic://VirtualTopic.eng.dci.job.complete"
    architecture = _get_architecture(job)
    return {
        "target": target,
        "body": json.dumps(
            {
                "contact": {
                    "name": "DCI CI",
                    "team": "DCI",
                    "docs": "https://docs.distributed-ci.io/",
                    "email": "distributed-ci@redhat.com",
                    "url": "https://distributed-ci.io/",
                },
                "run": {"url": job_url, "log": job_url},
                "artifact": {
                    "compose_type": "nightly"
                    if "nightly" in component["url"]
                    else "rel-eng",
                    "id": component["name"],
                    "type": "productmd-compose",
                },
                "pipeline": {"id": job_id, "name": "job id"},
                "test": {
                    "category": "system",
                    "namespace": "dci",
                    "type": test_name,
                    "result": "passed" if job["status"] == "success" else "failed",
                },
                "system": [{"provider": "beaker", "architecture": architecture}],
                "generated_at": "%sZ" % now.isoformat(),
                "version": "0.1.0",
            }
        ),
    }


def _get_kernel_version(component):
    if "tags" not in component:
        return None
    kernel_version = None
    for tag in component["tags"]:
        if "kernel:" in tag:
            kernel_version = tag.replace("kernel:", "")
    return kernel_version


def _build_cki_message(job, component, result):
    job_url = "https://www.distributed-ci.io/jobs/%s/jobStates" % str(job["id"])
    target = "topic://VirtualTopic.eng.dci.cki"
    architecture = _get_architecture(job)
    return {
        "target": target,
        "body": json.dumps(
            {
                "results": [
                    {
                        "test_arch": architecture,
                        "test_description": tc["classname"],
                        "test_log_url": [job_url],
                        "test_name": tc["name"],
                        "test_result": "PASS" if job["status"] == "success" else "FAIL",
                        "is_debug": False,
                    }
                    for tc in result["testcases"]
                ],
                "summarized_result": "",
                "team_email": "distributed-ci@redhat.com",
                "team_name": "DCI",
                "kernel_version": _get_kernel_version(component),
                "artifact": {
                    "compose_type": "nightly"
                    if "nightly" in component["url"]
                    else "rel-eng",
                    "id": component["name"],
                    "type": "productmd-compose",
                },
            }
        ),
    }


def build_umb_messages(event, now=datetime.datetime.utcnow()):
    logger.debug(event)
    messages = []
    job = event["job"]
    for component in job["components"]:
        if component["type"].lower() != "compose":
            continue
        for result in job["results"]:
            if "cki-results" == result["name"].lower():
                messages.append(_build_cki_message(job, component, result))
            messages.append(_build_generic_message(job, component, result, now))
    return messages


def send_event_on_umb(event):
    messages = build_umb_messages(event)
    key_file = os.getenv("UMB_KEY_FILE_PATH", "/etc/pki/tls/private/umb.key")
    crt_file = os.getenv("UMB_CRT_FILE_PATH", "/etc/pki/tls/certs/umb.crt")
    ca_file = os.getenv("UMB_CA_FILE_PATH", "/etc/pki/tls/certs/RH-IT-Root-CA.crt")
    brokers = os.environ.get("UMB_BROKERS", "amqps://umb.api.redhat.com:5671").split()
    for message in messages:
        try:
            send(
                {
                    "key_file": key_file,
                    "crt_file": crt_file,
                    "ca_file": ca_file,
                    "brokers": brokers,
                    "target": message["target"],
                    "message": message["body"],
                }
            )
        except Exception as e:
            logger.exception(e)
