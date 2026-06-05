import json
import logging
import os
import time
from urllib.parse import urljoin

from requests import exceptions

from alertmanager_tg_sender_adapter.utils.auth import Authorization
from alertmanager_tg_sender_adapter.utils.metrics import (
    alert_sent_failed_total,
    alert_sent_successful_total,
    incoming_alerts_total,
    upstream_request_duration_seconds,
)

logger = logging.getLogger(__name__)
r = Authorization()


def process_text(message_body):
    incoming_alerts_total.labels(has_dashboard="False", full_page="False").inc()

    logger.info(f"Отправляю сообщение для алерта: {message_body.get('tech_alertname')}")

    upstream_start_time = time.time()

    # Выполняем запрос
    socket = r.post(
        urljoin(str(os.getenv("XPLATFORM_ADDRESS")), "sendMessage"),
        message_body,
        10,
    )

    upstream_request_duration_seconds.labels(
        endpoint="sendMessage", http_code=str(socket.status_code)
    ).observe(time.time() - upstream_start_time)

    logger.info(f"Ответ: {socket.text}")

    if socket.status_code == 200:
        alert_sent_successful_total.labels(
            category="Success",
            http_code=str(socket.status_code),
        ).inc()

    elif socket.status_code in range(400, 500):
        python_dict = {}
        if socket.text:
            try:
                python_dict = json.loads(socket.text)
            except json.JSONDecodeError:
                python_dict = {
                    "description": "Invalid JSON response",
                    "detail": socket.text[:200],
                }

        alert_sent_failed_total.labels(
            category="clientError",
            http_code=str(socket.status_code),
            error_code=str(python_dict.get("errorCode", "none")),
            description=str(python_dict.get("description", "none"))[:100],
            detail=str(python_dict.get("detail", "none"))[:200],
        ).inc()

    else:
        python_dict = {}
        if socket.text:
            try:
                python_dict = json.loads(socket.text)
            except json.JSONDecodeError:
                python_dict = {
                    "description": "Server Error Response",
                    "detail": socket.text[:200],
                }

        alert_sent_failed_total.labels(
            category="serverError",
            http_code=str(socket.status_code),
            error_code=str(python_dict.get("errorCode", "SERVER_ERROR")),
            description=str(python_dict.get("description", "Upstream server error"))[
                :100
            ],
            detail=str(python_dict.get("detail", socket.text))[:200],
        ).inc()

        raise exceptions.HTTPError(socket.text)
