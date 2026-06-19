"""
Search orchestrator. Fans out to all enabled scrapers in parallel, collects
results, falls back to sample data for failures, groups by product, and
returns a SearchResponse.
"""
from typing import List, Optional, Set
import asyncio
import time
import logging
import hashlib
import httpx

from app.scrapers import SCRAPERS
from app.scrapers.base import BaseScraper
from app.models import Listing, Product, SearchResponse
from app.core.matcher import group_listings
from app.core.cache import cache_get, cache_set
from app.core.config import settings
from app.data.sample_data import get_sample_listings

logger = logging.getLogger(__name__)


def _cache_key(query: str, sites: Optional[Set[str]]) -> str:
    payload = f"{query.lower().strip()}|{','.join(sorted(sites)) if sites else 'all'}"
    return "search:" + hashlib.md5(payload.encode()).hexdigest()


async def search(
    query: str,
    sites: Optional[Set[str]] = None,
    use_cache: bool = True,
) -> SearchResponse:
    """
    Run the full search pipeline.

    Args:
        query: free-text search like "iPhone 15"
        sites: if provided, only run scrapers for these site_ids
        use_cache: whether to read/write the cache
    """
    start = time.time()
    query = query.strip()
    if not query:
        return SearchResponse(
            query="", products=[], total_listings=0,
            sources_responded=[], sources_failed=[], elapsed_ms=0,
        )

    key = _cache_key(query, sites)
    if use_cache:
        cached = cache_get(key)
        if cached is not None:
            logger.info(f"[cache hit] {query!r}")
            resp = SearchResponse(**cached)
            resp.cached = True
            return resp

    # Build scraper instances, sharing one HTTP client for connection pooling.
    async with httpx.AsyncClient(
        timeout=settings.request_timeout,
        follow_redirects=True,
        headers=BaseScraper._default_headers(),
    ) as client:
        instances = [cls(client=client) for cls in SCRAPERS]
        if sites:
            instances = [s for s in instances if s.site_id in sites]

        # Run all in parallel with a global semaphore for politeness
        sem = asyncio.Semaphore(settings.scraper_concurrency)

        async def _run(scraper: BaseScraper):
            async with sem:
                return scraper, await scraper.search_safe(query, limit=10)

        results = await asyncio.gather(*[_run(s) for s in instances])

    # Aggregate
    all_listings: List[Listing] = []
    responded: List[str] = []
    failed: List[str] = []
    site_ids_with_real_data: Set[str] = set()

    for scraper, listings in results:
        if listings:
            all_listings.extend(listings)
            responded.append(scraper.site_id)
            site_ids_with_real_data.add(scraper.site_id)
        else:
            # Couldn't get live data — log as failed (UI can still see it via fallback)
            if not scraper.sample_only:
                failed.append(scraper.site_id)

    # Fallback: ensure stub-only sites and any failed sites have something to show.
    if settings.enable_fallback_data:
        sample = get_sample_listings(query, limit=200)
        target_sites = {s.site_id for s in instances} - site_ids_with_real_data
        for l in sample:
            if l.site_id in target_sites:
                all_listings.append(l)
        # Sites we filled with sample data still count as "responded" from
        # the user's perspective, just with lower confidence.
        for sid in target_sites:
            if any(l.site_id == sid for l in sample):
                if sid not in responded:
                    responded.append(sid)

    # Group into products
    products: List[Product] = group_listings(all_listings)
    # Sort products: those with the most listings first (more comparison value)
    products.sort(key=lambda p: -len(p.listings))

    response = SearchResponse(
        query=query,
        products=products,
        total_listings=len(all_listings),
        sources_responded=sorted(responded),
        sources_failed=sorted(failed),
        elapsed_ms=int((time.time() - start) * 1000),
        cached=False,
    )

    if use_cache:
        cache_set(key, response.model_dump(mode="json"))

    return response
