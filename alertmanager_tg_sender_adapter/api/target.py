import logging
import hashlib
import time
from alertmanager_tg_sender_adapter.processors.image import process_image
from alertmanager_tg_sender_adapter.processors.text import process_text
from alertmanager_tg_sender_adapter.utils.validation import (
    is_dashboard_screenshoter_url_available,
)

logger = logging.getLogger(__name__)
from alertmanager_tg_sender_adapter.model.data_model import PreparedTelegramAlert

_processed_alerts = {}
_DUPLICATION_WINDOW = 60  # sec


def _get_alert_fingerprint(message: PreparedTelegramAlert) -> str:
    """Генерирует уникальный fingerprint для алерта."""
    fingerprint_data = f"{message.tech_alertname}-{message.chatId}-{message.text[:100]}"
    return hashlib.md5(fingerprint_data.encode()).hexdigest()


def _is_duplicate(fingerprint: str) -> bool:
    """Проверяет, был ли уже обработан такой алерт."""
    if fingerprint in _processed_alerts:
        if time.time() - _processed_alerts[fingerprint] < _DUPLICATION_WINDOW:
            logger.warning(f"Обнаружен дубликат алерта: {fingerprint}")
            return True
    _processed_alerts[fingerprint] = time.time()
    return False


async def route_messages(messages: list[PreparedTelegramAlert]):
    for message in messages:
        try:
            fingerprint = _get_alert_fingerprint(message)

            if _is_duplicate(fingerprint):
                logger.info(f"Пропуск дубликата алерта: {message.tech_alertname}")
                continue

            dashboard_url = message.tech_grafana_dashboard
            alert_name = message.tech_alertname

            if not dashboard_url:
                logger.info(
                    f"Для алерта '{alert_name}' нет URL. Отправка текстового сообщения."
                )
                process_text(message)
                continue

            is_valid_url, kiosk_mode_notify, connection_ok = (
                is_dashboard_screenshoter_url_available(dashboard_url)
            )

            if not is_valid_url or not connection_ok:
                reason = "невалидный URL" if not is_valid_url else "URL недоступен"
                logger.info(
                    f"Для алерта '{alert_name}' {reason}. Отправка текстового сообщения."
                )
                process_text(message)
                continue

            if kiosk_mode_notify:
                logger.warning(
                    f"В URL дашборда для алерта '{alert_name}' не указан kiosk mode."
                )

            logger.info(
                f"Для алерта '{alert_name}' найден валидный URL. Отправка со скриншотом."
            )
            await process_image(dashboard_url, message)

        except Exception as e:
            logger.error(
                f"Ошибка при обработке алерта '{message.tech_alertname}': {e}",
                exc_info=True,
            )
