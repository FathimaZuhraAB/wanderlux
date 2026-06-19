"""
Quick smoke tests. Run with:
    cd backend && python -m pytest tests/ -v
or just:
    cd backend && python tests/test_smoke.py
"""
import asyncio
import sys
import os

# allow running directly without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core import orchestrator
from app.core.matcher import group_listings, _normalize
from app.data.sample_data import get_sample_listings
from app.models import Listing, Category


def test_normalize():
    assert _normalize("Apple iPhone 15 (128 GB) — Black!!!") == "apple iphone 15 128 gb black"
    print("✓ _normalize")


def test_sample_data_returns_listings():
    listings = get_sample_listings("iphone")
    assert len(listings) > 0
    assert all(isinstance(l, Listing) for l in listings)
    print(f"✓ sample_data → {len(listings)} listings")


def test_grouping_clusters_similar_titles():
    listings = [
        Listing(site_id="a", site_name="A", title="Apple iPhone 15 128GB Black", url="x", price=70000),
        Listing(site_id="b", site_name="B", title="iPhone 15 (128 GB) - Black",  url="y", price=68000),
        Listing(site_id="c", site_name="C", title="Samsung Galaxy S24 256GB",     url="z", price=75000),
    ]
    products = group_listings(listings)
    # iPhones should group together; Samsung should be its own
    assert len(products) == 2
    iphone = [p for p in products if "iphone" in p.title.lower()][0]
    assert len(iphone.listings) == 2
    print(f"✓ grouping → {len(products)} products from 3 listings")


async def _orchestrator_runs():
    resp = await orchestrator.search("iphone 15", use_cache=False)
    assert resp.query == "iphone 15"
    assert resp.elapsed_ms >= 0
    assert len(resp.products) > 0
    print(f"✓ orchestrator → {len(resp.products)} products, "
          f"{resp.total_listings} listings, {resp.elapsed_ms}ms")


def test_orchestrator():
    asyncio.run(_orchestrator_runs())


if __name__ == "__main__":
    test_normalize()
    test_sample_data_returns_listings()
    test_grouping_clusters_similar_titles()
    test_orchestrator()
    print("\n🎉 all smoke tests passed")
