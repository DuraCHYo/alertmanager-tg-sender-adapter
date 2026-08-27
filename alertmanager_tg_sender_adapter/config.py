class Config:
    VERSION_NUMBER = "2.0.10"
    EXCLUDED_HANDLERS = [
        "/health",
        "/version",
        "/metrics",
    ]


config = Config()
