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
    alert_sent_failed_total,
)

load_dotenv()
r = Authorization()
logger = logging.getLogger(__name__)


def process_image(grafana_dashboard_kiosk_url, message_body):
    start_execution_time_duration = time.time()
    screenshot_event_id = uuid.uuid1()
    window_size = {"width": 1920, "height": 1080}
    is_full_page = bool(message_body.get("tech_send_grafana_full_page", False))
    viewport = ViewportSize(
        width=window_size.get("width", 1920), height=window_size.get("height", 1080)
    )
    screenshot_path = os.path.join(os.getcwd(), f"{screenshot_event_id}.png")

    browser = None

    with sync_playwright() as p:
        chromium_args = ["--disable-dev-shm-usage"]

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
                ).inc()
                raise

            logger.debug("Создаю отдельную вкладку в браузере")
            try:
                page = browser.new_page()
            except Exception as e:
                logger.error(f"Ошибка создания вкладки: {e}")
                alert_sent_failed_total.labels(
                    category="image_generation_failed",
                ).inc()
                raise

            logger.debug("Прокидываю в хедер энву из конфигурации приложения")
            page.set_extra_http_headers({
                "Authorization": f"Bearer {os.getenv('GRAFANA_SA_TOKEN')}"
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
                ).inc()
                raise

            logger.debug(
                "Беру период на wait, чтобы CSS прогрузился с помощью отслеживания сетевой активности"
            )
            page.wait_for_load_state("networkidle")

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
                ).inc()

        except Exception as e:
            logger.error(f"Ошибка: {e}")
            alert_sent_failed_total.labels(
                category="generic_error",
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
                    ).inc()

        logger.info(
            f"Отправляю алерт с картинкой для: {message_body.get('tech_alertname', '')}"
        )
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
            socket.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error(
                f"Ошибка при выполнении запроса: {http_err} - {socket.status_code} - {socket.text}"
            )
            alert_sent_failed_total.labels(
                category="Send_with_image_error",
            ).inc()
        except Exception as err:
            print(f"Ошибка: {err}")
            alert_sent_failed_total.labels(
                category="Send_with_image_error",
            ).inc()
        logger.debug(f"Чищу сгенерированный скриншот: {screenshot_path}")
        if os.path.exists(screenshot_path):
            try:
                os.remove(screenshot_path)
            except Exception as e:
                logger.error(f"Не удалось удалить скриншот: {e}")
        logger.info(f"Ответ: {socket.text}")
        return socket.text
