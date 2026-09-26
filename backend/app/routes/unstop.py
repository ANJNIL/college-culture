from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Request, Query, HTTPException, status
from app.services.unstop import unstop_service
from app.security.rate_limiter import limiter

router = APIRouter(prefix="/api/unstop", tags=["Unstop Scraper"])


@router.get("/items", response_model=List[Dict[str, Any]])
@limiter.limit("10/minute")
async def get_unstop_items(
    request: Request,
    keyword: Optional[str] = Query(None, description="Search keyword for hackathons/competitions"),
    max_items: Optional[int] = Query(20, ge=1, le=100, description="Max items to retrieve")
):
    """
    Fetch Unstop hackathons, competitions, and opportunities through the backend proxy.
    Keeps all scraper credentials secure on the backend.
    """
    payload = {}
    if keyword:
        payload["keyword"] = keyword
    if max_items:
        payload["maxItems"] = max_items

    return await unstop_service.fetch_dataset_items(payload=payload)


@router.post("/scrape", response_model=List[Dict[str, Any]])
@limiter.limit("5/minute")
async def trigger_unstop_scrape(
    request: Request,
    input_data: Optional[Dict[str, Any]] = None
):
    """
    Execute Unstop scraper actor with custom filtering payload.
    """
    return await unstop_service.fetch_dataset_items(payload=input_data or {})
