from prometheus_client import Counter

alert_sent_successful_total = Counter(
    "alert_sent_successful_total",
    "Сколько всего успешно отправлено алертов",
    labelnames=("category", "http_code"),
)
alert_sent_failed_total = Counter(
    "alert_sent_failed_total",
    "Сколько всего ошибок при отправке алертов",
    labelnames=("category", "http_code", "error_code", "description", "detail"),
)
