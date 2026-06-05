import logging
import os
import time
import uuid
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv
from playwright.sync_api import ViewportSize, sync_playwright

from alertmanager_tg_sender_adapter.utils.auth import Authorization
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


def process_image(grafana_dashboard_kiosk_url, message_body):
    start_execution_time_duration = time.time()
    screenshot_event_id = uuid.uuid1()
    grafana_readonly_sa_token = message_body.get("grafana_readonly_sa_token", "")
    if not grafana_readonly_sa_token:
        logger.warning(
            "Токен для Grafana не найден, хотя дашборд указан. Авторизация может быть недоступна"
        )
    window_size = {"width": 1920, "height": 1080}
    is_full_page = bool(message_body.get("tech_send_grafana_full_page", False))
    viewport = ViewportSize(
        width=window_size.get("width", 1920), height=window_size.get("height", 1080)
    )
    screenshot_path = os.path.join(os.getcwd(), f"{screenshot_event_id}.png")

    incoming_alerts_total.labels(
        has_dashboard=str(bool(grafana_dashboard_kiosk_url)),
        full_page=str(is_full_page),
    ).inc()

    browser = None

    with sync_playwright() as p:
        chromium_args = ["--disable-dev-shm-usage", "--ignore-certificate-errors"]

        try:
            render_timeout = 2500 if is_full_page else 500
            if not chromium_args:
                logger.debug("Запускаю chromium без аргументов")
            else:
                logger.debug(
                    f"Запускаю chrome с аргументами: {' '.join(chromium_args)}"
                )
            try:
                logger.debug("Вызываю песочницу playwright")
                browser = p.chromium.launch(args=chromium_args)
            except Exception as e:
                end_execution_time_duration = time.time()
                logger.error(
                    f"Ошибка запуска chromium: {e}. Время запуска: {end_execution_time_duration - start_execution_time_duration}"
                )
                alert_sent_failed_total.labels(
                    category="image_generation_failed",
                    http_code="none",
                    error_code="LAUNCH_ERROR",
                    description="Failed to launch chromium browser",
                    detail=str(e)[:200],
                ).inc()
                screenshot_generation_errors_total.labels(
                    stage="launch", error_type=type(e).__name__
                ).inc()
                raise

            logger.debug("Создаю отдельную вкладку в браузере")
            try:
                page = browser.new_page()
            except Exception as e:
                logger.error(f"Ошибка создания вкладки: {e}")
                alert_sent_failed_total.labels(
                    category="image_generation_failed",
                    http_code="none",
                    error_code="NEW_PAGE_ERROR",
                    description="Failed to create new browser page",
                    detail=str(e)[:200],
                ).inc()
                screenshot_generation_errors_total.labels(
                    stage="open_page", error_type=type(e).__name__
                ).inc()
                raise

            logger.debug("Прокидываю в хедер энву из конфигурации приложения")
            if grafana_dashboard_kiosk_url and grafana_readonly_sa_token:
                page.set_extra_http_headers({
                    "Authorization": f"Bearer {grafana_readonly_sa_token}"
                })
            logger.debug(
                f"Выставляю размер окна {window_size.get('width')}x{window_size.get('height')}"
            )
            page.set_viewport_size(viewport)

            try:
                logger.debug(
                    f"Открываю страницу из лейбла: {grafana_dashboard_kiosk_url}"
                )
                page.goto(grafana_dashboard_kiosk_url, wait_until="domcontentloaded")
            except Exception as e:
                logger.error(
                    f"Ошибка при открытии страницы по адресу: {grafana_dashboard_kiosk_url}. Ошибка: {e}"
                )
                alert_sent_failed_total.labels(
                    category="image_generation_failed",
                    http_code="none",
                    error_code="GOTO_ERROR",
                    description="Failed to open Grafana URL",
                    detail=str(e)[:200],
                ).inc()
                screenshot_generation_errors_total.labels(
                    stage="open_page", error_type=type(e).__name__
                ).inc()
                raise

            logger.debug(
                "Беру период на wait, чтобы CSS прогрузился с помощью отслеживания сетевой активности"
            )
            try:
                page.wait_for_load_state("networkidle")
            except Exception as e:
                screenshot_generation_errors_total.labels(
                    stage="network_idle", error_type=type(e).__name__
                ).inc()
                raise

            scroll_height = page.evaluate("document.body.scrollHeight")
            viewport_height = page.evaluate("window.innerHeight")

            current_position = 0
            try:
                while current_position < scroll_height:
                    page.evaluate(f"window.scrollTo(0, {current_position})")
                    page.wait_for_timeout(timeout=render_timeout)
                    current_position += viewport_height
                logger.debug(
                    "Прогружаю всю страницу, чтобы не оставалось пустых панелей"
                )
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(timeout=render_timeout)
                page.wait_for_load_state("networkidle")
            except Exception as e:
                logger.error(f"Ошибка при прогрузке страницы: {e}")
                alert_sent_failed_total.labels(
                    category="image_generation_failed",
                    http_code="none",
                    error_code="SCROLL_ERROR",
                    description="Failed during page scrolling or networkidle wait",
                    detail=str(e)[:200],
                ).inc()
                screenshot_generation_errors_total.labels(
                    stage="scroll", error_type=type(e).__name__
                ).inc()
            logger.debug("Выполняю скриншот браузера с URL")
            try:
                page.screenshot(
                    path=screenshot_path,
                    full_page=bool(is_full_page),
                    animations="disabled",
                )
                logger.info("Скриншот создан успешно")
                logger.debug(f"Скриншот создан успешно {screenshot_event_id}.png")
            except Exception as e:
                logger.error(f"Ошибка при генерации скриншота: {e}")
                alert_sent_failed_total.labels(
                    category="image_generation_failed",
                    http_code="none",
                    error_code="SCREENSHOT_ERROR",
                    description="Failed to take page screenshot",
                    detail=str(e)[:200],
                ).inc()
                screenshot_generation_errors_total.labels(
                    stage="screenshot", error_type=type(e).__name__
                ).inc()

        except Exception as e:
            logger.error(f"Ошибка: {e}")
            alert_sent_failed_total.labels(
                category="generic_error",
                http_code="none",
                error_code="GENERIC_ERROR",
                description="Unexpected error inside playwright execution context",
                detail=str(e)[:200],
            ).inc()
        finally:
            if browser is not None:
                logger.debug("Завершаю сессию браузера")
                try:
                    browser.close()
                except Exception as e:
                    logger.error(f"Не удалось корректно закрыть браузер: {e}")
                    alert_sent_failed_total.labels(
                        category="browser_close_error",
                        http_code="none",
                        error_code="BROWSER_CLOSE_ERROR",
                        description="Failed to close browser instance cleanly",
                        detail=str(e)[:200],
                    ).inc()

    screenshot_duration_seconds.labels(full_page=str(is_full_page)).observe(
        time.time() - start_execution_time_duration
    )

    logger.info(
        f"Отправляю алерт с картинкой для: {message_body.get('tech_alertname', '')}"
    )

    upstream_start_time = time.time()
    socket = None

    try:
        socket = r.image_post(
            url=urljoin(
                str(os.getenv("XPLATFORM_ADDRESS")),
                "sendMediaGroup",
            ),
            chat_id=message_body.get("chatId", None),
            text=message_body.get("text", ""),
            screenshot_path=screenshot_path,
            timeout=15,
        )

        upstream_request_duration_seconds.labels(
            endpoint="sendMediaGroup", http_code=str(socket.status_code)
        ).observe(time.time() - upstream_start_time)

        socket.raise_for_status()

        alert_sent_successful_total.labels(
            category="image_alert", http_code=str(socket.status_code)
        ).inc()

    except requests.exceptions.HTTPError as http_err:
        status_code = str(socket.status_code) if socket else "unknown"
        response_text = socket.text[:200] if socket else "No response text"

        upstream_request_duration_seconds.labels(
            endpoint="sendMediaGroup", http_code=status_code
        ).observe(time.time() - upstream_start_time)

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
        if socket:
            upstream_request_duration_seconds.labels(
                endpoint="sendMediaGroup", http_code=str(socket.status_code)
            ).observe(time.time() - upstream_start_time)
        else:
            upstream_request_duration_seconds.labels(
                endpoint="sendMediaGroup", http_code="unknown"
            ).observe(time.time() - upstream_start_time)

        print(f"Ошибка: {err}")
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

    logger.debug(f"Чищу сгенерированный скриншот: {screenshot_path}")
    if os.path.exists(screenshot_path):
        try:
            os.remove(screenshot_path)
        except Exception as e:
            logger.error(f"Не удалось удалить скриншот: {e}")
            disposal_errors_total.inc()

    if socket:
        logger.info(f"Ответ: {socket.text}")
        return socket.text
    return "No response from socket due to setup error"
