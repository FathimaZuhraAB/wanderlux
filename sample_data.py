"""
Amazon search scraper.

Reality check: Amazon aggressively blocks scrapers. This implementation tries
HTML parsing as a best-effort. If you have a Product Advertising API key,
set AMAZON_PAAPI_* env vars and we'll prefer the official API path (TODO).

For production: use the official PAAPI 5 SDK or a service like Rainforest API.
"""
from typing import List
import logging
import re
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper
from app.models import Listing, Category

logger = logging.getLogger(__name__)


def _parse_price(text: str) -> float:
    if not text:
        return 0.0
    cleaned = re.sub(r"[^\d.]", "", text.replace(",", ""))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


class AmazonScraper(BaseScraper):
    site_id = "amazon"
    site_name = "Amazon"
    category = Category.GENERAL

    BASE = "https://www.amazon.in"

    async def search(self, query: str, limit: int = 10) -> List[Listing]:
        url = f"{self.BASE}/s"
        params = {"k": query}
        r = await self.fetch(url, params=params)
        if not r:
            return []

        soup = BeautifulSoup(r.text, "lxml")
        cards = soup.select("div[data-component-type='s-search-result']")
        if not cards:
            logger.info("[amazon] no result cards — likely blocked or layout changed")
            return []

        items: List[Listing] = []
        for c in cards[:limit]:
            try:
                title_el = c.select_one("h2 a span") or c.select_one("h2 span")
                link_el = c.select_one("h2 a")
                price_el = c.select_one("span.a-price > span.a-offscreen")
                mrp_el = c.select_one("span.a-price.a-text-price > span.a-offscreen")
                rating_el = c.select_one("span.a-icon-alt")
                reviews_el = c.select_one("span.a-size-base.s-underline-text")
                img_el = c.select_one("img.s-image")

                if not (title_el and link_el and price_el):
                    continue
                price = _parse_price(price_el.get_text())
                if price <= 0:
                    continue
                href = link_el.get("href", "")
                rating = None
                if rating_el:
                    m = re.match(r"([\d.]+)", rating_el.get_text())
                    if m:
                        rating = float(m.group(1))
                reviews = None
                if reviews_el:
                    m = re.search(r"[\d,]+", reviews_el.get_text())
                    if m:
                        reviews = int(m.group(0).replace(",", ""))

                items.append(Listing(
                    site_id=self.site_id,
                    site_name=self.site_name,
                    title=title_el.get_text(strip=True),
                    url=self.BASE + href if href.startswith("/") else href,
                    image_url=img_el.get("src") if img_el else None,
                    price=price,
                    mrp=_parse_price(mrp_el.get_text()) if mrp_el else None,
                    rating=rating,
                    review_count=reviews,
                    delivery="Tomorrow",
                    confidence=1.0,
                ))
            except Exception as e:
                logger.debug(f"[amazon] skip card: {e}")
                continue
        return items
