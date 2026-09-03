from urllib.parse import urljoin

import requests
from fastapi import APIRouter

from alertmanager_tg_sender_adapter.config import app_config

router = APIRouter()

@router.get("/health")
async def get_healthcheck():
    """
    Check if the service is up and running.
    """
    return "I'm healthy!"


@router.get("/version")
async def get_version():
    return {"version": app_config.VERSION_NUMBER}
