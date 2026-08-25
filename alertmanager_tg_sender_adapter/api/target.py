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


def _normalize_field_name(field_name: str) -> str:
    """Нормализует имя поля, удаляя суффиксы типа .keyword, .text и т.д.
    
    Примеры:
    - namespace.keyword -> namespace
    - namespace.text -> namespace
    - project.keyword -> project
    - instance -> instance
    """
    # Удаляем распространённые суффиксы OpenSearch/Elasticsearch
    suffixes = ['.keyword', '.text', '.raw', '.exact']
    for suffix in suffixes:
        if field_name.endswith(suffix):
            return field_name[:-len(suffix)]
    return field_name


def _get_alert_fingerprint(message: PreparedTelegramAlert) -> str:
    """Генерирует уникальный fingerprint для алерта на основе множества полей."""
    
    # Основные поля
    fields = [
        message.tech_alertname,
        str(message.chatId),
        message.tech_alertgroup,
        message.tech_instance,
        message.tech_namespace,
        message.tech_container,
        message.tech_pod,
    ]
    
    # Сортируем дополнительные лейблы для consistency
    if message.tech_extra_labels:
        sorted_labels = sorted(message.tech_extra_labels.items())
        for key, value in sorted_labels:
            # Нормализуем имя поля (namespace.keyword -> namespace)
            normalized_key = _normalize_field_name(key)
            fields.append(f"{normalized_key}={value}")
    
    # Создаём строку для хеширования
    fingerprint_data = "|".join(fields)
    
    return hashlib.md5(fingerprint_data.encode()).hexdigest()


def _is_duplicate(fingerprint: str) -> bool:
    """Проверяет, был ли уже обработан такой алерт."""
    if fingerprint in _processed_alerts:
        if time.time() - _processed_alerts[fingerprint] < _DUPLICATION_WINDOW:
            logger.debug(f"Обнаружен дубликат алерта (fingerprint: {fingerprint[:16]}...)")
            return True
    _processed_alerts[fingerprint] = time.time()
    return False


async def route_messages(messages: list[PreparedTelegramAlert]):
    for message in messages:
        try:
            fingerprint = _get_alert_fingerprint(message)

            if _is_duplicate(fingerprint):
                logger.info(
                    f"Пропуск дубликата алерта: {message.tech_alertname} "
                    f"(group: {message.tech_alertgroup}, instance: {message.tech_instance}, "
                    f"namespace: {message.tech_namespace}, extra: {message.tech_extra_labels})"
                )
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
