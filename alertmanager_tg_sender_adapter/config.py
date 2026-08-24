class Config:
    VERSION_NUMBER = "2.0.3"
    EXCLUDED_HANDLERS = [
        "/health",
        "/version",
        "/metrics",
    ]


config = Config()
