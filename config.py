"""
Canonical data schema. Every scraper, regardless of source, must return Listings
in this shape so the comparator can reason across them uniformly.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class Category(str, Enum):
    GENERAL = "general"
    FASHION = "fashion"
    BEAUTY = "beauty"
    GROCERY = "grocery"
    ELECTRONICS = "electronics"
    KIDS = "kids"
    PHARMACY = "pharmacy"


class Listing(BaseModel):
    """A single offer from a single source for a single product."""
    site_id: str = Field(..., description="Slug like 'amazon', 'flipkart'")
    site_name: str
    title: str
    url: str
    image_url: Optional[str] = None
    price: float = Field(..., ge=0)
    mrp: Optional[float] = Field(None, ge=0)
    currency: str = "INR"
    rating: Optional[float] = Field(None, ge=0, le=5)
    review_count: Optional[int] = Field(None, ge=0)
    in_stock: bool = True
    delivery: Optional[str] = None
    coupon: Optional[str] = None
    category: Category = Category.GENERAL
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    # source confidence: 1.0 = live scrape, 0.5 = stale cache, 0.2 = sample fallback
    confidence: float = 1.0


class Product(BaseModel):
    """A grouped set of listings believed to be the same product."""
    product_key: str = Field(..., description="Hash/slug uniquely identifying this product group")
    title: str
    image_url: Optional[str] = None
    category: Category = Category.GENERAL
    tags: List[str] = []
    listings: List[Listing]

    @property
    def min_price(self) -> Optional[float]:
        in_stock = [l for l in self.listings if l.in_stock]
        return min((l.price for l in in_stock), default=None)

    @property
    def max_price(self) -> Optional[float]:
        in_stock = [l for l in self.listings if l.in_stock]
        return max((l.price for l in in_stock), default=None)


class SearchResponse(BaseModel):
    query: str
    products: List[Product]
    total_listings: int
    sources_responded: List[str]
    sources_failed: List[str]
    elapsed_ms: int
    cached: bool = False
