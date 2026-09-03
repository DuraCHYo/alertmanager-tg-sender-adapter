import logging
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from alertmanager_tg_sender_adapter.api import system
from alertmanager_tg_sender_adapter.api.target import route_messages
from alertmanager_tg_sender_adapter.config import app_config
from alertmanager_tg_sender_adapter.model.data_model import AlertmanagerPayload
from alertmanager_tg_sender_adapter.model.filter import EndpointFilter
from alertmanager_tg_sender_adapter.render.browser_pool import BrowserManager
from alertmanager_tg_sender_adapter.utils.logger import init_logging
from alertmanager_tg_sender_adapter.utils.normalizers import build_messages

# Всё логирование в отдельный сервис, потому что ну... так просто удобнее. Инициализировать в других файлах в 2 строки
# import logging
# logger = logging.getLogger(__name__)

load_dotenv()
log_level = init_logging()

logger = logging.getLogger(__name__)

logging.getLogger("uvicorn.access").addFilter(EndpointFilter(list(app_config.EXCLUDED_HANDLERS)))

browser_manager = BrowserManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск браузера при старте приложения
    logger.info("Запуск браузера...")
    await browser_manager.start()
    yield
    # Остановка браузера при завершении приложения
    logger.info("Остановка браузера...")
    await browser_manager.stop()


app = FastAPI(lifespan=lifespan)

app.include_router(system.router)

instrumentation = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    excluded_handlers=list(app_config.EXCLUDED_HANDLERS),
    should_respect_env_var=True,
    env_var_name="ENABLE_METRICS",
).instrument(app)

@app.post("/api/v1/alertmanager-tg-sender-adapter/send")
@app.post("/api/v1/alertmanager-sender-adapter/send")
async def entrypoint(payload: AlertmanagerPayload, background_tasks: BackgroundTasks):
    messages = build_messages(payload)
    background_tasks.add_task(route_messages, messages)
    return {"status": "accepted", "queued": len(messages)}


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


if __name__ == '__main__':
    main()
