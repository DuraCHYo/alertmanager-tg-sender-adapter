import logging

from alertmanager_tg_sender_adapter.config import app_config

excluded_endpoints = app_config.EXCLUDED_HANDLERS


class EndpointFilter(logging.Filter):
    def __init__(self, excluded_endpoints: list[str]):
        self.excluded_endpoints = excluded_endpoints

    def filter(self, record: logging.LogRecord):
        access_log = record.args
        _, _, endpoint, _, _ = access_log  # ty: ignore[not-iterable]
        return endpoint not in self.excluded_endpoints