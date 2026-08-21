from fastapi import APIRouter

router = APIRouter()
from alertmanager_tg_sender_adapter.config import config


@router.get("/health")
async def get_healthcheck():
    return "I'm healthy!"


@router.get("/version")
async def get_version():
    return {"version": config.VERSION_NUMBER}
