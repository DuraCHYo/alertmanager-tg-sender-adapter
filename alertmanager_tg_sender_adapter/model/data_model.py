from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class AlertLabels(BaseModel):
    chatId: int
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
    summary: str = ""
    description: str = ""


class AlertItem(BaseModel):
    status: str
    startsAt: datetime
    endsAt: datetime | None = None
    labels: AlertLabels
    annotations: AlertAnnotations = Field(default_factory=AlertAnnotations)


class AlertmanagerPayload(BaseModel):
    receiver: str = ""
    status: str = ""
    alerts: list[AlertItem] = Field(default_factory=list)


class PreparedTelegramAlert(BaseModel):
    chatId: int
    text: str
    tech_alertname: str
    tech_alertstate: str
    tech_severity: str
    tech_grafana_dashboard: str
    tech_send_grafana_full_page: bool
    grafana_readonly_sa_token: str
