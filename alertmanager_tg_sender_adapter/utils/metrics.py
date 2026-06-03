from prometheus_client import Counter, Histogram

alert_sent_successful_total = Counter(
    "alert_sent_successful_total",
    "Сколько всего успешно отправлено алертов",
    labelnames=("category", "http_code"),
)
alert_sent_failed_total = Counter(
    "alert_sent_failed_total",
    "Ошибок при отправке алертов",
    labelnames=("category", "http_code", "error_code", "description", "detail"),
)
#
alert_image_sent_failed_total = Counter(
    "alert_image_sent_failed_total",
    "Ошибки при отправке алертов с картинкой",
    labelnames=("category", "http_code", "error_code", "description", "detail"),
)
# Время, затраченное на полную генерацию скриншота (от запуска браузера до закрытия)
screenshot_duration_seconds = Histogram(
    "screenshot_duration_seconds",
    "Время генерации скриншота Grafana",
    labelnames=("full_page",),
)

# Стадии падения Playwright
screenshot_generation_errors_total = Counter(
    "screenshot_generation_errors_total",
    "Ошибки во время работы Playwright",
    labelnames=("stage", "error_type"),
    # stage может быть: launch, open_page, auth, network_idle, scroll, screenshot
)
# Время выполнения POST-запросов к XPLATFORM
upstream_request_duration_seconds = Histogram(
    "upstream_request_duration_seconds",
    "Время ответа внешнего API (XPLATFORM)",
    labelnames=("endpoint", "http_code"),  # endpoint: sendMessage или sendMediaGroup
)
# Сколько всего отдельных алертов пришло в одном батче от Alertmanager
incoming_alerts_total = Counter(
    "incoming_alerts_total",
    "Количество входящих алертов по типам",
    labelnames=("has_dashboard", "full_page"),  # True/False
)
# Ошибки при удалении временных файлов
disposal_errors_total = Counter(
    "disposal_errors_total", "Ошибки при удалении временных скриншотов с диска"
)
