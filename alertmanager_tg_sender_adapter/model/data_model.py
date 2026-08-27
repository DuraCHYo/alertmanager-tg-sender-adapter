from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class AlertLabels(BaseModel):
    model_config = ConfigDict(extra="allow")
    
    chatId: str
    alertname: str
    alertgroup: str = ""
    severity: str = ""
    instance: str = ""
    pod: str | None = None
    namespace: str | None = None
    container: str | None = None
    grafana_dashboard: str = ""
    send_grafana_full_page: bool = False
    grafana_readonly_sa_token: str = ""


class AlertAnnotations(BaseModel):
    model_config = ConfigDict(extra="allow")
    
    summary: str = ""
    description: str = ""


class AlertItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    
    status: str
    startsAt: datetime
    endsAt: datetime | None = None
    labels: AlertLabels
    annotations: AlertAnnotations = Field(default_factory=AlertAnnotations)


class AlertmanagerPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    
    receiver: str = ""
    status: str = ""
    alerts: list[AlertItem] = Field(default_factory=list)


class PreparedTelegramAlert(BaseModel):
    chatId: str
    text: str
    tech_alertname: str
    tech_alertstate: str
    tech_severity: str
    tech_grafana_dashboard: str
    tech_send_grafana_full_page: bool
    grafana_readonly_sa_token: str
    # Дополнительные поля для точной дедупликации
    tech_alertgroup: str = ""
    tech_instance: str = ""
    tech_namespace: str = ""
    tech_container: str = ""
    tech_pod: str = ""
    # Для поддержки кастомных полей (например, project)
    tech_extra_labels: dict = {}
