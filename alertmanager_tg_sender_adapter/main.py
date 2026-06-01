import json
import logging
import os
import uuid
from urllib.parse import urljoin

import uvicorn
from dotenv import load_dotenv
from fastapi import Body, FastAPI
from playwright.sync_api import sync_playwright
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
log_level = setup_log_level(os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI()
r = Authorization()
logging.basicConfig(
    level=log_level.upper(),
    format="%(asctime)s - %(message)s",
)


@app.post("/api/v1/alertmanager-tg-sender-adapter/send")
def router(payload=Body()):
    parsed_alerts = parse_alertmanager_payload(payload)
    alerts_list = combine_all_fields_to_body(parsed_alerts)
    grafana_dashboard_kiosk_url = ""
    try:
        for message_body in alerts_list:
            logging.info(
                f"Отправляю сообщение для алерта: {message_body.get('tech_alertname')}"
            )
            # Если в лейблах есть "grafana_dashboard" и он непустой - вызываем функцию генерации картинок.
            if message_body.get("tech_grafana_dashboard") != "Нет":
                grafana_dashboard_kiosk_url = message_body.get("tech_grafana_dashboard")
            else:
                grafana_dashboard_kiosk_url = ""
            if grafana_dashboard_kiosk_url:
                process_image(grafana_dashboard_kiosk_url, message_body)
            # Иначе просто шлём текстом из функции сборки body для сообщения, на похуй чисто.
            else:
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
                # TODO Переделать, чтобы можно было логировать и 400 и 500. Сейчас это не работает потому что при 401 - ошибка синтаксиса из-за того что сюда ничего не доходит. (ебучий ast)
                elif socket.status_code in range(400, 500):
                    if socket.text:
                        python_dict = json.loads(socket.text)
                    python_dict = {}
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
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_extra_http_headers({
                "Authorization": f"Bearer {os.getenv('GRAFANA_SA_TOKEN')}"
            })
            page.goto(
                grafana_dashboard_kiosk_url,
                wait_until="domcontentloaded",
            )
            page.wait_for_load_state("networkidle")
            screenshot_path = os.path.join(os.getcwd(), f"{screenshot_event_id}.png")
            logging.info(f"Скриншот создан успешно {screenshot_event_id}.png")
            page.screenshot(path=screenshot_path, animations="disabled")
            browser.close()
        except Exception as e:
            logging.error(f"Ошибка при генерации скриншота: {e}")
            raise e
        try:
            socket = r.image_post(
                url=urljoin(
                    str(os.getenv("XPLATFORM_ADDRESS")),
                    "sendMediaGroup",
                ),
                chat_id=message_body["chatId"],
                text=message_body["text"],
                screenshot_path=screenshot_path,
                timeout=15,
            )
            os.remove(screenshot_path)
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
    logging.info("Alertmanager TG Sender Adapter запущен")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level=log_level.lower())
