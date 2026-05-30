import logging
import os

from requests import exceptions


def parse_alertmanager_payload(payload: dict) -> list:
    try:
        alerts = payload.get("alerts", [])
        parsed_alerts = []
        for alert in alerts:
            parsed_alert = {
                "alertname": alert.get("labels", {}).get("alertname", ""),
                "status": alert.get("status"),
                "alertgroup": alert.get("labels", {}).get("alertgroup", ""),
                "pod": alert.get("labels", {}).get("pod", ""),
                "severity": alert.get("labels", {}).get("severity", ""),
                "namespace": alert.get("labels", {}).get("namespace", ""),
                "summary": alert.get("annotations", {}).get("summary", ""),
                "container": alert.get("labels", {}).get("container", ""),
                "instance": alert.get("labels", {}).get("instance", ""),
                "description": alert.get("annotations", {}).get("description", ""),
                "grafana_dashboard": alert.get("annotations", {}).get(
                    "grafana_dashboard", ""
                ),
                "startsAt": alert.get("startsAt"),
                "endsAt": alert.get("endsAt"),
            }
            parsed_alerts.append(parsed_alert)
        return parsed_alerts
    except Exception as e:
        logging.error(f"Ошибка парсинга JSON-пейлоада от Alertmanager: {e}")
        raise exceptions.InvalidJSONError()


def combine_all_fields_to_body(alerts_list) -> list:
    body_to_send = []
    add_container = ""
    add_instance = ""
    for alert in alerts_list:
        if alert.get("status") == "resolved":
            state = "✅ Восстановление"
            ends_at_line = f"Время конца проблемы: {alert.get('endsAt')}\n"
        else:
            state = "🚨 Проблема"
            ends_at_line = ""
        if alert.get("container") != "":
            add_container = f"Контейнер: {alert.get('container')}"
        if alert.get("instance") != "":
            add_instance = f"Нода: {alert.get('instance')}"
        alert_body_with_all = {
            "chatId": int(os.getenv("INFRA_CHAT_ID", "0000")),
            "text": f"Статус: {state}\n"
            f"Группа: {alert.get('alertgroup')}\n"
            f"Название: {alert.get('alertname')}\n"
            "---------"
            f"Влияние: {alert.get('severity')}\n"
            f"Неймспейс: {alert.get('namespace')}\n"
            f"{add_instance}"
            f"{add_container}"
            "---------"
            f"Заголовок: {alert.get('summary')}\n"
            f"Описание: {alert.get('description')}\n"
            "---------"
            f"Время начала проблемы: {alert.get('startsAt')}\n"
            f"{ends_at_line}"
            "---------"
            f"Ссылка на Grafana: {alert.get('grafana_dashboard')}",
            "enableParseMode": "true",
            "Название": alert.get("alertname"),
            "Статус": state,
            "Влияние": alert.get("severity"),
        }

        body_to_send.append(alert_body_with_all)
    return body_to_send
