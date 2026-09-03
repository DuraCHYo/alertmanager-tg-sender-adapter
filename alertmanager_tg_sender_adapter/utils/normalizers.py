from alertmanager_tg_sender_adapter.model.data_model import (
    AlertmanagerPayload,
    PreparedTelegramAlert,
)


def _normalize_field_name(field_name: str) -> str:
    """Нормализует имя поля, удаляя суффиксы типа .keyword, .text и т.д.

    Примеры:
    - namespace.keyword -> namespace
    - namespace.text -> namespace
    - project.keyword -> project
    - instance -> instance
    """
    suffixes = ['.keyword', '.text', '.raw', '.exact']
    for suffix in suffixes:
        if field_name.endswith(suffix):
            return field_name[:-len(suffix)]
    return field_name


def build_messages(
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
        add_namespace= f'Неймспейс: {labels.namespace}\n' if labels.namespace else ""
        add_grafana_dashboard_url = f"Ссылка на Grafana: {labels.grafana_dashboard}\n" if labels.grafana_dashboard else ""
        add_description = f"Описание {annotations.description}\n" if annotations.description else ""
        add_alert_group = f"Группа: {labels.alertgroup}\n" if labels.alertgroup else ""
        add_severity = f"Влияние: {labels.severity}\n" if labels.severity else ""

        starts_at_str = alert.startsAt.isoformat()

        text = (
            f"Статус: {state}\n"
            f"{add_alert_group}"
            f"Название: {labels.alertname}\n"
            "---------\n"
            f"{add_severity}"
            f"{add_namespace}"
            f"{add_instance}"
            f"{add_container}"
            "---------\n"
            f"Заголовок: {annotations.summary}\n"
            f"{add_description}"
            "---------\n"
            f"Время начала проблемы: {starts_at_str}\n"
            f"{ends_at_line}"
            "---------\n"
            f"{add_grafana_dashboard_url}"
        )

        # Собираем дополнительные лейблы для дедупликации (игнорируя системные поля)
        extra_labels = {}
        model_fields = {"chatId", "alertname", "alertgroup", "severity", "instance",
                       "pod", "namespace", "container", "grafana_dashboard",
                       "send_grafana_full_page", "grafana_readonly_sa_token"}

        # Получаем все дополнительные поля из лейблов (например, project, environment и т.д.)
        for key, value in labels.model_dump(exclude_unset=True).items():
            if key not in model_fields and value:
                # Нормализуем имя поля (namespace.keyword -> namespace)
                normalized_key = _normalize_field_name(key)
                extra_labels[normalized_key] = str(value)

        prepared_message = PreparedTelegramAlert(
            chatId=labels.chatId,
            text=text,
            tech_alertname=labels.alertname,
            tech_alertstate=state,
            tech_severity=labels.severity,
            tech_grafana_dashboard=labels.grafana_dashboard,
            tech_send_grafana_full_page=labels.send_grafana_full_page,
            grafana_readonly_sa_token=labels.grafana_readonly_sa_token,
            tech_alertgroup=labels.alertgroup,
            tech_instance=labels.instance,
            tech_namespace=labels.namespace or "",
            tech_container=labels.container or "",
            tech_pod=labels.pod or "",
            tech_extra_labels=extra_labels,
        )

        messages.append(prepared_message)

    return messages
