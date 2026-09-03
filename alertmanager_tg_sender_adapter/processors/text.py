import json
import logging
import os
import time
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv

from alertmanager_tg_sender_adapter.authorization.auth import Authorization
from alertmanager_tg_sender_adapter.config import app_config
from alertmanager_tg_sender_adapter.model.data_model import PreparedTelegramAlert
from alertmanager_tg_sender_adapter.utils.metrics import (
    alert_sent_failed_total,
    alert_sent_successful_total,
    incoming_alerts_total,
    upstream_request_duration_seconds,
)

load_dotenv()
logger = logging.getLogger(__name__)
r = Authorization()


def _parse_error_response(response_text: str) -> dict:
    """Безопасно парсит JSON-ответ с ошибкой от апстрима."""
    if not response_text:
        return {"description": "Empty response body", "detail": "none"}
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return {
            "description": "Invalid JSON response",
            "detail": response_text[:200],
        }


def process_text(message: PreparedTelegramAlert):
    incoming_alerts_total.labels(has_dashboard="False", full_page="False").inc()

    logger.info(f"Отправляю текстовое сообщение для алерта: {message.tech_alertname}")
    endpoint_type = app_config.ACHAT_DEFAULT_ENDPOINT if not message.chatId.startswith("-") else app_config.TG_DEFAULT_ENDPOINT
    target_url = urljoin(app_config.XPLATFORM_ADDRESS,f"{endpoint_type}/sendMessage")

    upstream_start_time = time.time()
    socket = None

    try:
        payload = message.model_dump()

        socket = r.post(
            target_url,
            payload,
            timeout=10,
        )

        status_code_str = str(socket.status_code)
        upstream_request_duration_seconds.labels(
            endpoint="sendMessage", http_code=status_code_str
        ).observe(time.time() - upstream_start_time)

        logger.info(f"Ответ апстрима [{status_code_str}]: {socket.text}")

        # --- 200 OK ---
        if socket.status_code == 200:
            alert_sent_successful_total.labels(
                category="Success",
                http_code=status_code_str,
            ).inc()
            return socket.text

        # --- 4xx Ошибки клиента ---
        elif 400 <= socket.status_code < 500:
            err_data = _parse_error_response(socket.text)
            alert_sent_failed_total.labels(
                category="clientError",
                http_code=status_code_str,
                error_code=str(err_data.get("errorCode", "CLIENT_ERROR")),
                description=str(err_data.get("description", "none"))[:100],
                detail=str(err_data.get("detail", "none"))[:200],
            ).inc()

        # --- 5xx Ошибки сервера ---
        else:
            err_data = _parse_error_response(socket.text)
            alert_sent_failed_total.labels(
                category="serverError",
                http_code=status_code_str,
                error_code=str(err_data.get("errorCode", "SERVER_ERROR")),
                description=str(err_data.get("description", "Upstream server error"))[
                    :100
                ],
                detail=str(err_data.get("detail", socket.text))[:200],
            ).inc()
            socket.raise_for_status()

    except requests.exceptions.RequestException as err:
        # Перехватываем ошибки сети/таймауты/HTTPError
        status_code = str(socket.status_code) if socket else "unknown"

        # Записываем метрику длительности, если socket не успел посчитаться
        if not socket:
            upstream_request_duration_seconds.labels(
                endpoint="sendMessage", http_code=status_code
            ).observe(time.time() - upstream_start_time)

        logger.error(
            f"Ошибка при отправке текстового сообщения для '{message.tech_alertname}': {err}"
        )

        alert_sent_failed_total.labels(
            category="networkOrHttpError",
            http_code=status_code,
            error_code="REQUEST_FAILED",
            description="Failed to deliver text message to upstream",
            detail=str(err)[:200],
        ).inc()
        raise