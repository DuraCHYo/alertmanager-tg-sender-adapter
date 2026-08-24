import logging

logger = logging.getLogger(__name__)


async def wait_for_grafana_render(page, timeout_ms=15000):
    """
    Ждет появления панелей и исчезновения полос загрузки Grafana.
    """
    logger.debug("Ожидаю монтирования панелей Grafana в DOM...")
    try:
        await page.wait_for_selector(
            'div[class*="-panel-content"]', state="visible", timeout=timeout_ms
        )
    except Exception as e:
        logger.warning(f"Панели не появились за {timeout_ms}ms: {e}")

    logger.debug("Ожидаю завершения загрузки данных в панелях...")
    try:
        await page.locator('div[class*="-panel-loading-bar-container"]').first.wait_for(
            state="hidden", timeout=timeout_ms
        )
        logger.debug("Все панели Grafana успешно прогрузились")
    except Exception as e:
        logger.warning(
            f"Полосы загрузки Grafana не исчезли за {timeout_ms}ms, делаем скриншот как есть: {e}"
        )
