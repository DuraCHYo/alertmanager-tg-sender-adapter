class Config:
    VERSION_NUMBER = "2.0.6"
    EXCLUDED_HANDLERS = [
        "/health",
        "/version",
        "/metrics",
    ]


config = Config()
