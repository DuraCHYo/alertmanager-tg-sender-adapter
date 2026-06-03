import json
import logging
import os
from urllib.parse import urljoin

from requests import exceptions

from alertmanager_tg_sender_adapter.utils.auth import Authorization
from alertmanager_tg_sender_adapter.utils.metrics import (
    alert_sent_failed_total,
    alert_sent_successful_total,
)

logger = logging.getLogger(__name__)
r = Authorization()


def process_text(message_body):
    logger.info(f"Отправляю сообщение для алерта: {message_body.get('tech_alertname')}")
    socket = r.post(
        urljoin(str(os.getenv("XPLATFORM_ADDRESS")), "sendMessage"),
        message_body,
        10,
    )
    logger.info(f"Ответ: {socket.text}")
    if socket.status_code == 200:
        alert_sent_successful_total.labels(
            category="Success",
            http_code=socket.status_code,
        ).inc()
    elif socket.status_code in range(400, 500):
        python_dict = {}
        if socket.text:
            python_dict = json.loads(socket.text)
        alert_sent_failed_total.labels(
            category="clientError",
            http_code=socket.status_code,
            error_code=python_dict.get("errorCode"),
            description=python_dict.get("description"),
            detail=python_dict.get("detail"),
        ).inc()
    else:
        alert_sent_failed_total.labels(
            status="serverError",
            http_code=socket.status_code,
        ).inc()

        raise exceptions.HTTPError(socket.text)
