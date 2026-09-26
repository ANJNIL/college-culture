from typing import Dict
from fastapi import APIRouter, Depends
from app.core.config import settings
from app.security.auth import get_admin_user

router = APIRouter(prefix="/api/config", tags=["Configuration"])


@router.get("/status", response_model=Dict[str, bool])
async def get_config_status(
    admin_user: dict = Depends(get_admin_user)
) -> Dict[str, bool]:
    """
    Returns API integrations configuration status.
    Protected and accessible ONLY to authenticated administrators.

    CRITICAL SECURITY RULE:
    Returns exclusively Boolean values.
    NEVER returns API keys, tokens, passwords, database URLs, private keys, or secrets.
    """
    return settings.get_integrations_status()
