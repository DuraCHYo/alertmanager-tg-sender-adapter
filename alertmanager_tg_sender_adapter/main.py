import json
import logging
import os
import uuid
from urllib.parse import urljoin

import uvicorn
from dotenv import load_dotenv
from fastapi import Body, FastAPI
from playwright.sync_api import ViewportSize, sync_playwright
from prometheus_fastapi_instrumentator import Instrumentator
from requests import exceptions

from alertmanager_tg_sender_adapter.utils.auth import Authorization
from alertmanager_tg_sender_adapter.utils.logging import setup_log_level
from alertmanager_tg_sender_adapter.utils.metrics import (
    alert_sent_failed_total,
    alert_sent_successful_total,
)
from alertmanager_tg_sender_adapter.utils.normalize_payload import (
    combine_all_fields_to_body,
    parse_alertmanager_payload,
)

load_dotenv()
# Формирую LOG_LEVEL из переменной среды запуска
log_level = setup_log_level(os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI()
# Делаю экземпляр класса, чтобы рулить авторизацией
r = Authorization()
# Настраиваю корневой логгер
logging.basicConfig(
    level=log_level.upper(),
    format="%(asctime)s - %(message)s",
)


@app.post("/api/v1/alertmanager-tg-sender-adapter/send")
def router(payload=Body()):
    parsed_alerts = parse_alertmanager_payload(payload)
    alerts_list = combine_all_fields_to_body(parsed_alerts)
    try:
        for message_body in alerts_list:
            # Если в лейблах есть "grafana_dashboard" и он непустой - вызываем функцию генерации картинок.
            if message_body.get("tech_grafana_dashboard") != "Нет":
                grafana_dashboard_kiosk_url = message_body.get("tech_grafana_dashboard")
            else:
                grafana_dashboard_kiosk_url = ""
            if grafana_dashboard_kiosk_url:
                process_image(grafana_dashboard_kiosk_url, message_body)
            # Иначе просто шлём текстом из функции сборки body для сообщения, на похуй чисто.
            else:
                logging.info(
                    f"Отправляю сообщение для алерта: {message_body.get('tech_alertname')}"
                )
                socket = r.post(
                    urljoin(str(os.getenv("XPLATFORM_ADDRESS")), "sendMessage"),
                    message_body,
                    10,
                )
                logging.info(f"Ответ: {socket.text}")
                if socket.status_code == 200:
                    alert_sent_successful_total.labels(
                        category="Success", http_code=socket.status_code
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
                        status="serverError", http_code=socket.status_code
                    ).inc()

                    raise exceptions.HTTPError(socket.text)
    except exceptions.BaseHTTPError as e:
        alert_sent_failed_total.labels(status="error").inc()
        logging.error(f"Ошибка при выполнении запроса: {e}")


def process_image(grafana_dashboard_kiosk_url, message_body):
    screenshot_event_id = uuid.uuid1()
    window_size = {"width": 1920, "height": 1080}
    viewport = ViewportSize(
        width=window_size.get("width", 1920), height=window_size.get("height", 1080)
    )
    with sync_playwright() as p:
        chromium_args = ["--disable-dev-shm-usage"]

        try:
            is_full_page = message_body.get("tech_send_grafana_full_page", False)
            if bool(is_full_page):
                render_timeout = 2500
            else:
                render_timeout = 500
            if not chromium_args:
                logging.debug("Запускаю chromium без аргументов")
            else:
                logging.debug(
                    f"Запускаю chrome с аргументами: {' '.join(chromium_args)}"
                )
            browser = p.chromium.launch(args=chromium_args)
            logging.debug("Создаю отдельную вкладку в браузере")
            page = browser.new_page()

            logging.debug("Прокидываю в хедер энву из конфигурации приложения")
            page.set_extra_http_headers({
                "Authorization": f"Bearer {os.getenv('GRAFANA_SA_TOKEN')}"
            })
            logging.debug(
                f"Выставляю размер окна {window_size.get('width')}x{window_size.get('height')}"
            )
            page.set_viewport_size(viewport)
            page.goto(grafana_dashboard_kiosk_url, wait_until="domcontentloaded")
            logging.debug(
                "Беру период на wait, чтобы CSS прогрузился с помощью отслеживания сетевой активности"
            )
            page.wait_for_load_state("networkidle")

            scroll_height = page.evaluate("document.body.scrollHeight")
            viewport_height = page.evaluate("window.innerHeight")

            current_position = 0
            while current_position < scroll_height:
                page.evaluate(f"window.scrollTo(0, {current_position})")
                page.wait_for_timeout(timeout=render_timeout)
                current_position += viewport_height
            logging.debug("Прогружаю всю страницу, чтобы не оставалось пустых панелей")
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(timeout=render_timeout)
            page.wait_for_load_state("networkidle")

            logging.debug(f"Создание скриншота {screenshot_event_id}.png")
            screenshot_path = os.path.join(os.getcwd(), f"{screenshot_event_id}.png")

            logging.debug("Выполняю рендер браузера с URL")
            page.screenshot(
                path=screenshot_path,
                full_page=bool(is_full_page),
                animations="disabled",
            )
            logging.debug(f"Скриншот создан успешно {screenshot_event_id}.png")

            browser.close()

        except Exception as e:
            logging.error(f"Ошибка при генерации скриншота: {e}")
            raise e

        try:
            logging.info(
                f"Отправляю алерт с картинкой для: {message_body.get('tech_alertname', '')}"
            )
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
            logging.debug("Чищу сгенерированный алерт")
            os.remove(screenshot_path)
            logging.info(f"Ответ: {socket.text}")
            return socket.text
        except exceptions.BaseHTTPError as e:
            alert_sent_failed_total.labels(category="Send with image error").inc()
            logging.error(f"Ошибка при выполнении запроса: {e}")


@app.get("/health")
def health():
    return "I'm healthy!"


def main():
    instrumentator = Instrumentator(
        excluded_handlers=["/metrics"],
        should_respect_env_var=True,
        env_var_name="ENABLE_METRICS",
    ).instrument(app)
    instrumentator.expose(app)
    logging.error("Alertmanager TG Sender Adapter запущен")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level=log_level.lower())
