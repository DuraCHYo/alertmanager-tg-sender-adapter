import logging
import os
import time
import uuid
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv
from playwright.async_api import ViewportSize

from alertmanager_tg_sender_adapter.authorization.auth import Authorization
from alertmanager_tg_sender_adapter.config import app_config
from alertmanager_tg_sender_adapter.model.data_model import PreparedTelegramAlert
from alertmanager_tg_sender_adapter.processors.text import process_text
from alertmanager_tg_sender_adapter.render.browser_pool import BrowserManager
from alertmanager_tg_sender_adapter.render.grafana import (
    wait_for_grafana_render,
)
from alertmanager_tg_sender_adapter.utils.metrics import (
    alert_image_sent_failed_total,
    alert_sent_failed_total,
    alert_sent_successful_total,
    disposal_errors_total,
    incoming_alerts_total,
    screenshot_duration_seconds,
    screenshot_generation_errors_total,
    upstream_request_duration_seconds,
)

load_dotenv()
r = Authorization()
logger = logging.getLogger(__name__)

browser_manager = BrowserManager()


async def process_image(grafana_dashboard_kiosk_url: str, message: PreparedTelegramAlert):
    start_execution_time_duration = time.time()
    screenshot_event_id = uuid.uuid1()

    grafana_readonly_sa_token = message.grafana_readonly_sa_token
    if not grafana_readonly_sa_token:
        logger.warning(
            "Токен для Grafana не найден, хотя дашборд указан. Авторизация может быть недоступна"
        )

    window_size = {"width": 1920, "height": 1080}
    is_full_page = message.tech_send_grafana_full_page
    viewport = ViewportSize(width=window_size["width"], height=window_size["height"])
    screenshot_path = os.path.join(os.getcwd(), f"{screenshot_event_id}.png")

    incoming_alerts_total.labels(
        has_dashboard=str(bool(grafana_dashboard_kiosk_url)),
        full_page=str(is_full_page),
    ).inc()

    screenshot_success = False
    page = None

    try:
        render_timeout = 2500 if is_full_page else 500
        page = await browser_manager.create_page()

        if grafana_dashboard_kiosk_url and grafana_readonly_sa_token:
            await page.set_extra_http_headers(
                {"Authorization": f"Bearer {grafana_readonly_sa_token}"}
            )

        await page.set_viewport_size(viewport)
        await page.goto(grafana_dashboard_kiosk_url, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")

        scroll_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = await page.evaluate("window.innerHeight")

        current_position = 0
        while current_position < scroll_height:
            await page.evaluate(f"window.scrollTo(0, {current_position})")
            await page.wait_for_timeout(timeout=render_timeout)
            current_position += viewport_height

        await page.evaluate("window.scrollTo(0, 0)")
        await wait_for_grafana_render(page, timeout_ms=15000)
        await page.wait_for_timeout(300)

        await page.screenshot(
            path=screenshot_path,
            full_page=is_full_page,
            animations="disabled",
        )
        screenshot_success = True
        logger.info(f"Скриншот создан успешно: {screenshot_event_id}.png")

    except Exception as e:
        logger.exception(
            "Ошибка при генерации скриншота Playwright"
        )
        alert_sent_failed_total.labels(
            category="image_generation_failed",
            http_code="none",
            error_code="PLAYWRIGHT_ERROR",
            description="Failed during browser automation",
            detail=str(e)[:200],
        ).inc()
        screenshot_generation_errors_total.labels(
            stage="execution", error_type=type(e).__name__
        ).inc()
    finally:
        if page is not None:
            try:
                await browser_manager.close_page(page)
            except Exception:
                logger.exception("Не удалось закрыть страницу")

    screenshot_duration_seconds.labels(full_page=str(is_full_page)).observe(
        time.time() - start_execution_time_duration
    )

    if not screenshot_success or not os.path.exists(screenshot_path):
        logger.warning(
            f"Скриншот не был сформирован. Отправка алерта '{message.tech_alertname}' текстом."
        )
        return process_text(message)

    logger.info(f"Отправляю алерт с картинкой для: {message.tech_alertname}")
    upstream_start_time = time.time()
    socket = None

    try:
        endpoint_type = app_config.ACHAT_DEFAULT_ENDPOINT if not message.chatId.startswith("-") else app_config.TG_DEFAULT_ENDPOINT
        target_url = urljoin(app_config.XPLATFORM_ADDRESS, f"{endpoint_type}/sendMediaGroup")

        socket = r.image_post(
            url=target_url,
            chat_id=message.chatId,
            text=message.text,
            screenshot_path=screenshot_path,
            timeout=15,
        )

        status_code_str = str(socket.status_code)
        upstream_request_duration_seconds.labels(
            endpoint="sendMediaGroup", http_code=str(status_code_str)
        ).observe(time.time() - upstream_start_time)

        socket.raise_for_status()
        alert_sent_successful_total.labels(
            category="image_alert", http_code=str(status_code_str)
        ).inc()

        logger.info(f"Ответ апстрима [{status_code_str}]: {socket.text}")

    except requests.exceptions.HTTPError as http_err:
        status_code = str(status_code_str) if socket else "unknown"
        response_text = socket.text[:200] if socket else "No response text"

        logger.error(
            f"Ошибка при выполнении запроса: {http_err} - {status_code} - {response_text}"
        )
        alert_sent_failed_total.labels(
            category="Send_with_image_error",
            http_code=status_code,
            error_code="HTTP_ERROR",
            description="Upstream returned HTTP Error status",
            detail=response_text,
        ).inc()
        alert_image_sent_failed_total.labels(
            category="Send_with_image_error",
            http_code=status_code,
            error_code="HTTP_ERROR",
            description="Upstream returned HTTP Error status",
            detail=response_text,
        ).inc()
    except Exception as err:
        logger.exception("Ошибка отправки запроса")
        alert_sent_failed_total.labels(
            category="Send_with_image_error",
            http_code="unknown",
            error_code="REQUEST_FAILED",
            description="Network error or connection failure to upstream",
            detail=str(err)[:200],
        ).inc()
        alert_image_sent_failed_total.labels(
            category="Send_with_image_error",
            http_code="unknown",
            error_code="REQUEST_FAILED",
            description="Network error or connection failure to upstream",
            detail=str(err)[:200],
        ).inc()
    finally:
        if os.path.exists(screenshot_path):
            try:
                os.remove(screenshot_path)
            except Exception:
                logger.exception("Не удалось удалить скриншот")
                disposal_errors_total.inc()

    return socket.text if socket else "No response"