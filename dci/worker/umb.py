import logging

from dci_umb.sender import send
from dci.dci_config import CONFIG as config

logger = logging.getLogger(__name__)


def build_umb_message(event):
    pass


def send_event_on_umb(event):
    target, message = build_umb_message(event)
    params = {
        "key_file": config["UMB_KEY_FILE_PATH"],
        "crt_file": config["UMB_CRT_FILE_PATH"],
        "ca_file": config["UMB_CA_FILE_PATH"],
        "brokers": config["UMB_BROKERS"],
        "target": target,
        "message": message,
    }
    try:
        send(params)
    except Exception as e:
        logger.exception(e)
