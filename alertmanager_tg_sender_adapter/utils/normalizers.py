from alertmanager_tg_sender_adapter.model.data_model import (
    AlertmanagerPayload,
    PreparedTelegramAlert,
)


def build_telegram_messages(
    payload: AlertmanagerPayload,
) -> list[PreparedTelegramAlert]:
    messages = []

    for alert in payload.alerts:
        labels = alert.labels
        annotations = alert.annotations

        if alert.status == "resolved":
            state = "✅ Восстановление"
            ends_at_str = alert.endsAt.isoformat() if alert.endsAt else ""
            ends_at_line = f"Время конца проблемы: {ends_at_str}\n"
        else:
            state = "🚨 Проблема"
            ends_at_line = ""

        add_container = f"Контейнер: {labels.container}\n" if labels.container else ""
        add_instance = f"Нода: {labels.instance}\n" if labels.instance else ""

        starts_at_str = alert.startsAt.isoformat()

        text = (
            f"Статус: {state}\n"
            f"Группа: {labels.alertgroup}\n"
            f"Название: {labels.alertname}\n"
            "---------\n"
            f"Влияние: {labels.severity}\n"
            f"Неймспейс: {labels.namespace or ''}\n"
            f"{add_instance}"
            f"{add_container}"
            "---------\n"
            f"Заголовок: {annotations.summary}\n"
            f"Описание: {annotations.description}\n"
            "---------\n"
            f"Время начала проблемы: {starts_at_str}\n"
            f"{ends_at_line}"
            "---------\n"
            f"Ссылка на Grafana: {labels.grafana_dashboard}\n"
            "---------"
        )

        prepared_message = PreparedTelegramAlert(
            chatId=labels.chatId,
            text=text,
            tech_alertname=labels.alertname,
            tech_alertstate=state,
            tech_severity=labels.severity,
            tech_grafana_dashboard=labels.grafana_dashboard,
            tech_send_grafana_full_page=labels.send_grafana_full_page,
            grafana_readonly_sa_token=labels.grafana_readonly_sa_token,
        )

        messages.append(prepared_message)

    return messages
