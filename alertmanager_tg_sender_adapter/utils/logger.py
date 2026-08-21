import logging
import os


def init_logging() -> str:
    env_level = os.getenv("LOG_LEVEL", "INFO").upper()
    if env_level == "FATAL":
        env_level = "CRITICAL"

    allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}

    log_level = env_level if env_level in allowed else "INFO"

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    )

    return log_level.lower()
