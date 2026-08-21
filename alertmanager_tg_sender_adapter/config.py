class Config:
    VERSION_NUMBER = "2.0.1"
    EXCLUDED_HANDLERS = [
        "/healthz",
        "/version",
        "/metrics",
    ]


config = Config()
