import asyncio
import logging

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


class BrowserManager:
    """Singleton для управления переиспользуемым браузером Playwright (Async API)."""

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            # Для singleton в async контексте используем обычный lock для создания
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._playwright = None
        self._browser = None
        self._initialized = True
        logger.info("BrowserManager инициализирован")

    async def start(self):
        """Запускает браузер (вызывать при старте приложения)."""
        async with self._lock:
            if self._browser is not None:
                logger.info("Браузер уже запущен")
                return

            try:
                self._playwright = await async_playwright().start()
                chromium_args = [
                    "--disable-dev-shm-usage",
                    "--ignore-certificate-errors",
                ]
                self._browser = await self._playwright.chromium.launch(args=chromium_args)
                logger.info("Браузер успешно запущен")
            except Exception:
                logger.exception("Ошибка при запуске браузера")
                raise

    async def stop(self):
        """Останавливает браузер (вызывать при остановке приложения)."""
        async with self._lock:
            if self._browser is None:
                return

            try:
                if self._browser:
                    await self._browser.close()
                if self._playwright:
                    await self._playwright.stop()
                self._browser = None
                self._playwright = None
                logger.info("Браузер остановлен")
            except Exception:
                logger.exception("Ошибка при остановке браузера")

    async def get_browser(self):
        """Возвращает экземпляр браузера. Если не запущен - запускает."""
        async with self._lock:
            if self._browser is None:
                logger.warning("Браузер не запущен, запускаем...")
                await self.start()
            return self._browser

    async def create_page(self):
        """Создаёт новую страницу в браузере."""
        browser = await self.get_browser()
        return await browser.new_page()

    async def close_page(self, page):
        """Закрывает страницу."""
        try:
            if page:
                await page.close()
        except Exception:
            logger.exception("Ошибка при закрытии страницы")
