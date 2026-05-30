import ast
import logging
import os

import uvicorn
from dotenv import load_dotenv
from fastapi import Body, FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from requests import exceptions

from alertmanager_tg_sender_adapter.utils.auth import Authorization
from alertmanager_tg_sender_adapter.utils.metrics import (
    alert_sent_failed_total,
    alert_sent_successful_total,
)
from alertmanager_tg_sender_adapter.utils.process_payload import (
    combine_all_fields_to_body,
    parse_alertmanager_payload,
)

load_dotenv()
app = FastAPI()
r = Authorization()
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
            socket = r.post(
                os.getenv("XPLATFORM_ADDRESS", "http://mock"), message_body, 10
            )
            logging.info(f"Ответ: {socket.text}")
            if socket.status_code == 200:
                alert_sent_successful_total.labels(
                    category="Success", http_code=socket.status_code
                ).inc()
            elif socket.status_code in range(400, 500):
                python_dict = ast.literal_eval(socket.text)
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
    uvicorn.run(app, host="0.0.0.0", port=8080)
