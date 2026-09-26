import logging
from typing import Dict, Any, Optional, List
import httpx
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger("unstop_scraper_service")


class UnstopScraperService:
    """
    Backend service proxy for Unstop Scraper API (Apify Actor).
    
    SECURITY & ARCHITECTURE:
    - Frontend communicates ONLY with FastAPI Backend.
    - Scraper credentials (UNSTOP_SCRAPER_API_KEY) and target endpoints remain 100% server-side.
    - Supports Apify Bearer Token header, ?token= query parameter, and custom headers.
    """

    def __init__(self):
        self.api_url = settings.UNSTOP_SCRAPER_API_URL.strip()
        self.api_key = settings.UNSTOP_SCRAPER_API_KEY.strip()
        self.timeout = 60.0  # Apify actor run-sync may take up to 60s

    def is_configured(self) -> bool:
        return bool(self.api_url)

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            # Apify standard authorization: Bearer <token>
            headers["Authorization"] = f"Bearer {self.api_key}"
            # Also provide standard API key header for compatibility
            headers["X-Apify-Token"] = self.api_key
        return headers

    def _build_url_with_token(self, base_url: str) -> str:
        """Append token query param if key is present and not already in URL."""
        if not self.api_key:
            return base_url
        separator = "&" if "?" in base_url else "?"
        if "token=" not in base_url:
            return f"{base_url}{separator}token={self.api_key}"
        return base_url

    async def fetch_dataset_items(
        self,
        payload: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes the Unstop scraper actor synchronously and fetches dataset items.
        Proxies request safely without leaking token or internal endpoints.
        """
        if not self.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unstop scraper service is not configured. Set UNSTOP_SCRAPER_API_URL in backend/.env"
            )

        target_url = self._build_url_with_token(self.api_url)
        headers = self._headers = self._build_headers()

        # Combine additional query parameters
        params = dict(query_params or {})

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info("Executing Unstop Scraper via Apify actor proxy...")
                # Apify run-sync-get-dataset-items expects POST (or GET if empty)
                if payload:
                    response = await client.post(target_url, headers=headers, json=payload, params=params)
                else:
                    response = await client.post(target_url, headers=headers, json={}, params=params)

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        return data.get("items", [data])
                    return []
                else:
                    logger.error(f"Unstop scraper returned HTTP {response.status_code}: {response.text[:200]}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Unstop scraper upstream returned HTTP {response.status_code}"
                    )
        except httpx.TimeoutException:
            logger.error("Unstop scraper timed out waiting for dataset items.")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Unstop scraper upstream timed out. Try refining search filters."
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to communicate with Unstop Scraper: {type(e).__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to query Unstop scraper service."
            )


unstop_service = UnstopScraperService()
