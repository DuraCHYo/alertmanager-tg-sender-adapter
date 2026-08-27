class Config:
    VERSION_NUMBER = "2.0.11"
    EXCLUDED_HANDLERS = [
        "/health",
        "/version",
        "/metrics",
    ]


config = Config()
