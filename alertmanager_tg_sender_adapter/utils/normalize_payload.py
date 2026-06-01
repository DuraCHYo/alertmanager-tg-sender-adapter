from requests import exceptions


def parse_alertmanager_payload(payload: dict) -> list:
    try:
        alerts = payload.get("alerts", [])
        parsed_alerts = []
        for alert in alerts:
            parsed_alert = {
                "chatId": alert.get("labels", {}).get("chatId", None),
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
                "grafana_dashboard": alert.get("labels", {}).get(
                    "grafana_dashboard", "Нет"
                ),
                "startsAt": alert.get("startsAt"),
                "endsAt": alert.get("endsAt"),
                "send_grafana_full_page": alert.get("labels", {}).get(
                    "send_grafana_full_page", "False"
                ),
            }
            parsed_alerts.append(parsed_alert)
        return parsed_alerts
    except Exception:
        raise exceptions.InvalidJSONError()


def combine_all_fields_to_body(alerts_list) -> list:
    body_to_send = []
    add_container = ""
    add_instance = ""
    for alert in alerts_list:
        send_full_page = alert.get("send_grafana_full_page", "False")
        if isinstance(send_full_page, str):
            tech_send_full_page = send_full_page.lower() == "true"
        else:
            tech_send_full_page = bool(send_full_page)
        if alert.get("status") == "resolved":
            state = "✅ Восстановление"
            ends_at_line = f"Время конца проблемы: {alert.get('endsAt')}\n"
        else:
            state = "🚨 Проблема"
            ends_at_line = ""
        if alert.get("container") is not None:
            add_container = f"Контейнер: {alert.get('container')}"
        if alert.get("instance") is not None:
            add_instance = f"Нода: {alert.get('instance')}"
        if alert.get("chatId") is None:
            raise ValueError("chatId label is not set")
        alert_body_with_all = {
            "chatId": int(alert.get("chatId")),
            "text": f"Статус: {state}\n"
            f"Группа: {alert.get('alertgroup')}\n"
            f"Название: {alert.get('alertname')}\n"
            "---------\n"
            f"Влияние: {alert.get('severity')}\n"
            f"Неймспейс: {alert.get('namespace')}\n"
            f"{add_instance}\n"
            f"{add_container}\n"
            "---------\n"
            f"Заголовок: {alert.get('summary')}\n"
            f"Описание: {alert.get('description')}\n"
            "---------\n"
            f"Время начала проблемы: {alert.get('startsAt')}\n"
            f"{ends_at_line}"
            "---------\n"
            f"Ссылка на Grafana: {alert.get('grafana_dashboard')}\n"
            "---------",
            "enableParseMode": "false",
            "tech_alertname": alert.get("alertname"),
            "tech_alertstate": state,
            "tech_severity": alert.get("severity"),
            "tech_grafana_dashboard": alert.get("grafana_dashboard"),
            "tech_send_grafana_full_page": tech_send_full_page,
        }

        body_to_send.append(alert_body_with_all)
    return body_to_send
