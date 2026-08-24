import logging

from alertmanager_tg_sender_adapter.config import config

excluded_endpoints = config.EXCLUDED_HANDLERS


class EndpointFilter(logging.Filter):
    def __init__(self, excluded_endpoints: list[str]):
        self.excluded_endpoints = excluded_endpoints

    def filter(self, record: logging.LogRecord):
        access_log = record.args
        host, method, endpoint, version, rc = access_log  # ty: ignore[not-iterable]
        return endpoint not in self.excluded_endpoints
