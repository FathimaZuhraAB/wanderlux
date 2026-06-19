"""
Stub scrapers for sites where:
  - We don't yet have a working live implementation, OR
  - The site requires Playwright/headless browser (heavier infra), OR
  - The site has aggressive bot defenses that won't yield to httpx alone

These return empty from .search(), letting the orchestrator fall back to
sample data so the UI is never blank. Replace each .search() with real
logic as you build out the project.

To swap in a real implementation:
  1. Inspect the site's network tab — many SPAs have JSON search endpoints
     similar to BigBasket/1mg.
  2. If no JSON endpoint exists, use Playwright (see scrapers/_playwright.py
     stub for the pattern).
  3. Mark the listing with confidence=1.0.
"""
from typing import List, ClassVar
from app.scrapers.base import BaseScraper
from app.models import Listing, Category


class _Stub(BaseScraper):
    """Base for sites we haven't implemented live scraping for yet."""
    sample_only: ClassVar[bool] = True

    async def search(self, query: str, limit: int = 10) -> List[Listing]:
        # Returning empty triggers the sample-data fallback in the orchestrator.
        return []


class MeeshoScraper(_Stub):
    site_id = "meesho"; site_name = "Meesho"; category = Category.GENERAL

class SnapdealScraper(_Stub):
    site_id = "snapdeal"; site_name = "Snapdeal"; category = Category.GENERAL

class ShopsyScraper(_Stub):
    site_id = "shopsy"; site_name = "Shopsy"; category = Category.GENERAL

class TataCliqScraper(_Stub):
    site_id = "tatacliq"; site_name = "Tata CLiQ"; category = Category.GENERAL

class MyntraScraper(_Stub):
    site_id = "myntra"; site_name = "Myntra"; category = Category.FASHION

class AjioScraper(_Stub):
    site_id = "ajio"; site_name = "Ajio"; category = Category.FASHION

class NykaaScraper(_Stub):
    site_id = "nykaa"; site_name = "Nykaa"; category = Category.BEAUTY

class NykaaFashionScraper(_Stub):
    site_id = "nykaafashion"; site_name = "Nykaa Fashion"; category = Category.FASHION

class BlinkitScraper(_Stub):
    site_id = "blinkit"; site_name = "Blinkit"; category = Category.GROCERY

class ZeptoScraper(_Stub):
    site_id = "zepto"; site_name = "Zepto"; category = Category.GROCERY

class InstamartScraper(_Stub):
    site_id = "swiggyinstamart"; site_name = "Instamart"; category = Category.GROCERY

class JioMartScraper(_Stub):
    site_id = "jiomart"; site_name = "JioMart"; category = Category.GROCERY

class RelianceDigitalScraper(_Stub):
    site_id = "reliancedigital"; site_name = "Reliance Digital"; category = Category.ELECTRONICS

class CromaScraper(_Stub):
    site_id = "croma"; site_name = "Croma"; category = Category.ELECTRONICS

class FirstCryScraper(_Stub):
    site_id = "firstcry"; site_name = "FirstCry"; category = Category.KIDS

class PharmEasyScraper(_Stub):
    site_id = "pharmeasy"; site_name = "PharmEasy"; category = Category.PHARMACY
