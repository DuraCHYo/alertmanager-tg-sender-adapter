import logging
import os

import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import Body, FastAPI
from requests import exceptions

from alertmanager_tg_sender_adapter.parser.parser import (
    combine_all_fields_to_body,
    parse_alertmanager_payload,
)

load_dotenv()
app = FastAPI()
r = requests.Session()
r.headers.update({"Content-Type": "application/json"})
r.auth = (
    os.getenv("XPLATFORM_USERNAME", "None"),
    os.getenv("XPLATFORM_PASSWORD", "None"),
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)


@app.post("/api/v1/alertmanager-tg-sender-adapter")
def sender(payload=Body()):
    parsed_alerts = parse_alertmanager_payload(payload)
    alerts_list = combine_all_fields_to_body(parsed_alerts)
    try:
        for message_body in alerts_list:
            logging.info(
                f"Отправляю сообщение для алерта: {message_body.get('Название')}"
            )
            s = r.post(
                os.getenv("XPLATFORM_ADDRESS", "http://mock"),
                json=message_body,
                timeout=10,
            )
            logging.info(f"Ответ: {s.text}")
            if s.status_code != 200:
                raise exceptions.HTTPError(s.text)
    except exceptions.BaseHTTPError as e:
        logging.error(f"Ошибка при выполнении запроса: {e}")


@app.get("/health")
def health():
    return "I'm healthy!"


def main():
    logging.info("Alertmanager TG Sender Adapter запущен")
    uvicorn.run(app, host="0.0.0.0", port=8080)
