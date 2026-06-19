"""
HTTP API routes.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
import logging

from app.core import orchestrator
from app.core.cache import cache_clear
from app.scrapers import all_sites_meta
from app.models import SearchResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/sites")
async def list_sites():
    """Return metadata about all configured sites (for the UI filter panel)."""
    return {"sites": all_sites_meta()}


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=200, description="Search term"),
    sites: Optional[str] = Query(
        None,
        description="Comma-separated site IDs to restrict search to. Omit for all.",
    ),
    fresh: bool = Query(False, description="Set true to bypass cache."),
):
    site_set = None
    if sites:
        site_set = {s.strip() for s in sites.split(",") if s.strip()}
    return await orchestrator.search(q, sites=site_set, use_cache=not fresh)


@router.post("/cache/clear")
async def clear_cache():
    cache_clear()
    return {"status": "cleared"}
