import logging
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


def is_dashboard_screenshoter_url_available(grafana_dashboard_kiosk_url):
    if not grafana_dashboard_kiosk_url or grafana_dashboard_kiosk_url == "Нет":
        return False, False, False

    splitted_url = urlparse(grafana_dashboard_kiosk_url)
    connection_established_ok = False

    is_valid_url = all([
        splitted_url.scheme in ("http", "https"),
        bool(splitted_url.netloc),
        bool(splitted_url.path),
    ])

    kiosk_mode_notify = "kiosk" not in splitted_url.query

    if is_valid_url:
        try:
            r = requests.get(grafana_dashboard_kiosk_url, timeout=5)
            connection_established_ok = r.status_code == 200  # проверяем что ответ OK
        except requests.ConnectTimeout:
            logger.error(f"Timeout при подключении к {grafana_dashboard_kiosk_url}")
        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе к {grafana_dashboard_kiosk_url}: {e}")

    return (is_valid_url, kiosk_mode_notify, connection_established_ok)
