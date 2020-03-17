import datetime
import logging

from dci_umb.sender import send
from dci.dci_config import CONFIG as config

logger = logging.getLogger(__name__)


def build_umb_messages(event, now=datetime.datetime.utcnow()):
    messages = []
    job = event["job"]
    for component in job["components"]:
        if component["type"] != "Compose":
            continue
        for result in job["results"]:
            test_name = result["name"]
            job_url = "https://www.distributed-ci.io/jobs/%s/jobStates" % job["id"]
            target = "/topic/VirtualTopic.eng.dci.job.complete"
            messages.append(
                {
                    "target": target,
                    "body": {
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
                        "pipeline": {"id": job["id"], "name": "job id"},
                        "test": {
                            "category": "system",
                            "namespace": "dci",
                            "type": test_name,
                            "result": "passed"
                            if job["status"] == "success"
                            else "failed",
                        },
                        "system": [],
                        "generated_at": "%sZ" % now.isoformat(),
                        "version": "0.1.0",
                    },
                }
            )
    return messages


def send_event_on_umb(event):
    messages = build_umb_messages(event)
    for message in messages:
        try:
            send(
                {
                    "key_file": config["UMB_KEY_FILE_PATH"],
                    "crt_file": config["UMB_CRT_FILE_PATH"],
                    "ca_file": config["UMB_CA_FILE_PATH"],
                    "brokers": config["UMB_BROKERS"],
                    "target": message["target"],
                    "message": message["body"],
                }
            )
        except Exception as e:
            logger.exception(e)
