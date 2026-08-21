class Config:
    VERSION_NUMBER = "1.1.8"
    EXCLUDED_HANDLERS = [
        "/healthz",
        "/version",
        "/metrics",
    ]


config = Config()
