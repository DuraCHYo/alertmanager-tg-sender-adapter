class Config:
    VERSION_NUMBER = "2.0.1"
    EXCLUDED_HANDLERS = [
        "/health",
        "/version",
        "/metrics",
    ]


config = Config()
