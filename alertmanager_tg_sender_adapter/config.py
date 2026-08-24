class Config:
    VERSION_NUMBER = "2.0.5"
    EXCLUDED_HANDLERS = [
        "/health",
        "/version",
        "/metrics",
    ]


config = Config()
