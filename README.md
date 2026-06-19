"""
Scraper registry. The orchestrator imports SCRAPERS from here.
"""
from typing import List, Type
from app.scrapers.base import BaseScraper
from app.scrapers.amazon import AmazonScraper
from app.scrapers.flipkart import FlipkartScraper
from app.scrapers.bigbasket import BigBasketScraper
from app.scrapers.tata1mg import Tata1mgScraper
from app.scrapers._stubs import (
    MeeshoScraper, SnapdealScraper, ShopsyScraper, TataCliqScraper,
    MyntraScraper, AjioScraper, NykaaScraper, NykaaFashionScraper,
    BlinkitScraper, ZeptoScraper, InstamartScraper, JioMartScraper,
    RelianceDigitalScraper, CromaScraper, FirstCryScraper, PharmEasyScraper,
)

# Order matters only for default UI listing; orchestrator runs them in parallel.
SCRAPERS: List[Type[BaseScraper]] = [
    # Live implementations
    AmazonScraper,
    FlipkartScraper,
    BigBasketScraper,
    Tata1mgScraper,
    # Stub fallbacks (use sample data)
    MeeshoScraper,
    SnapdealScraper,
    ShopsyScraper,
    TataCliqScraper,
    MyntraScraper,
    AjioScraper,
    NykaaScraper,
    NykaaFashionScraper,
    BlinkitScraper,
    ZeptoScraper,
    InstamartScraper,
    JioMartScraper,
    RelianceDigitalScraper,
    CromaScraper,
    FirstCryScraper,
    PharmEasyScraper,
]


def all_sites_meta():
    """Lightweight metadata for the frontend (categories, names, etc)."""
    return [
        {
            "id": s.site_id,
            "name": s.site_name,
            "category": s.category.value,
            "live": not s.sample_only,
        }
        for s in SCRAPERS
    ]
