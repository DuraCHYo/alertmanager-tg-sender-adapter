import logging

import uvicorn
from dotenv import load_dotenv
from fastapi import Body, FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from alertmanager_tg_sender_adapter.api import system
from alertmanager_tg_sender_adapter.api.target import route_messages
from alertmanager_tg_sender_adapter.config import config
from alertmanager_tg_sender_adapter.model.data_model import AlertmanagerPayload
from alertmanager_tg_sender_adapter.model.filter import EndpointFilter
from alertmanager_tg_sender_adapter.utils.logger import init_logging
from alertmanager_tg_sender_adapter.utils.normalizers import build_telegram_messages

# Всё логирование в отдельный сервис, потому что ну... так просто удобнее. Инициализировать в других файлах в 2 строки
# import logging
# logger = logging.getLogger(__name__)

load_dotenv()
log_level = init_logging()

logger = logging.getLogger(__name__)

logging.getLogger("uvicorn.access").addFilter(EndpointFilter(config.EXCLUDED_HANDLERS))

app = FastAPI()

app.include_router(system.router)

instrumentation = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    excluded_handlers=config.EXCLUDED_HANDLERS,
    should_respect_env_var=True,
    env_var_name="ENABLE_METRICS",
).instrument(app)


@app.post("/api/v1/alertmanager-tg-sender-adapter/send")
def entrypoint(payload: AlertmanagerPayload):
    messages = build_telegram_messages(payload)
    try:
        route_messages(messages)
        return {"status": "ok", "processed": len(messages)}
    except Exception as e:
        return {"error": str(e)}


def main():
    logger.info("Alertmanager TG Sender Adapter запущен")
    instrumentation.expose(app, endpoint="/metrics", include_in_schema=True)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level=log_level,
        reload=False,
    )


if __name__ == "__main__":
    main()
