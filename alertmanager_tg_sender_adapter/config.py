import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    """Application configuration dataclass."""
    VERSION_NUMBER: str = "2.0.12"
    EXCLUDED_HANDLERS: tuple[str, ...] = (
        "/health",
        "/version",
        "/metrics",
    )
    ACHAT_DEFAULT_ENDPOINT: str = "achat-sender-api/api/v1/achat"
    TG_DEFAULT_ENDPOINT: str = "tg-sender-api/api/v1/tg"
    XPLATFORM_ADDRESS: str = os.getenv("XPLATFORM_ADDRESS", "")

app_config = Config()