import logging
import os

import urllib3
import uvicorn
from fastapi import Body, FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from alertmanager_tg_sender_adapter.processors.image import process_image
from alertmanager_tg_sender_adapter.processors.text import process_text
from alertmanager_tg_sender_adapter.utils.auth import Authorization
from alertmanager_tg_sender_adapter.utils.logger_config import init_logging
from alertmanager_tg_sender_adapter.utils.normalize_payload import (
    combine_all_fields_to_body,
    parse_alertmanager_payload,
)
from alertmanager_tg_sender_adapter.utils.validate import (
    is_dashboard_screenshoter_url_available,
)

# Всё логирование в отдельный сервис, потому что ну... так просто удобнее. Инициализировать в других файлах в 2 строки
# import logging
# logger = logging.getLogger(__name__)

log_level = init_logging()

logger = logging.getLogger(__name__)

app = FastAPI()
# Делаю экземпляр класса, чтобы рулить авторизацией
r = Authorization()


@app.post("/api/v1/alertmanager-tg-sender-adapter/send")
def router(payload=Body()):
    parsed_alerts = parse_alertmanager_payload(payload)
    alerts_list = combine_all_fields_to_body(parsed_alerts)

    try:
        for message_body in alerts_list:
            grafana_dashboard_url = message_body.get("tech_grafana_dashboard", "")
            alert_name = message_body.get("tech_alertname", "")

            # Проверяем, что URL есть и это не строка "Нет"
            if grafana_dashboard_url == "Нет":
                logger.info(
                    f"Для алерта '{alert_name}' нет URL. Отправка текстового сообщения."
                )
                process_text(message_body)
                continue

            is_valid_url, kiosk_mode_notify, connection_established_ok = (
                is_dashboard_screenshoter_url_available(grafana_dashboard_url)
            )

            if not is_valid_url or not connection_established_ok:
                reason = "невалидный URL" if not is_valid_url else "URL недоступен"
                logger.info(
                    f"Для алерта '{alert_name}' {reason}. Отправка текстового сообщения."
                )
                process_text(message_body)
                continue

            if kiosk_mode_notify:
                logger.warning(
                    f"В URL дашборда для алерта '{alert_name}' не указан kiosk mode. "
                    "Скриншот может быть некорректно обработан."
                )

            logger.info(
                f"Для алерта '{alert_name}' найден валидный URL. Отправка сообщения со скриншотом."
            )
            process_image(grafana_dashboard_url, message_body)

    except Exception as e:
        logger.error(f"Ошибка при обработке пейлоада: {e}", exc_info=True)


@app.get("/health")
def health():
    return "I'm healthy!"


def main():
    if os.getenv("DISABLE_SSL"):
        urllib3.disable_warnings()
    else:
        pass
    instrumentator = Instrumentator(
        excluded_handlers=["/metrics"],
        should_respect_env_var=True,
        env_var_name="ENABLE_METRICS",
    ).instrument(app)
    instrumentator.expose(app)
    logger.error("Alertmanager TG Sender Adapter запущен")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level=log_level)
