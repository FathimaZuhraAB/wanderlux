"""
Product matching: given a flat list of Listings from many sites, group those
that refer to the SAME product so we can compare prices.

Strategy:
  1. Normalize titles (lowercase, strip punctuation, drop filler words)
  2. Compare with token-set ratio (rapidfuzz) — robust to word reorder
  3. Pair listings above MATCH_THRESHOLD into the same Product

This is intentionally simple. For a real launch, augment with:
  - Image perceptual hashing (pHash) to confirm visual identity
  - Brand+model extraction via NER
  - GTIN/UPC barcode matching when available
"""
from typing import List, Dict
import re
import hashlib
from rapidfuzz import fuzz
from collections import defaultdict

from app.models import Listing, Product, Category


# Filler words that don't help identify a product
_STOPWORDS = {
    "with", "for", "and", "the", "of", "in", "on", "at", "by", "or",
    "pack", "piece", "set", "new", "best", "top", "buy", "online",
    "premium", "high", "quality",
}

_PUNCT_RE = re.compile(r"[^a-z0-9\s]")
_WS_RE = re.compile(r"\s+")


def _normalize(title: str) -> str:
    t = title.lower()
    t = _PUNCT_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()
    tokens = [w for w in t.split() if w not in _STOPWORDS and len(w) > 1]
    return " ".join(tokens)


MATCH_THRESHOLD = 78  # 0..100, tune empirically


def _key(normalized: str) -> str:
    return hashlib.md5(normalized.encode()).hexdigest()[:10]


def group_listings(listings: List[Listing]) -> List[Product]:
    """
    Greedy clustering: for each listing, attach to the first existing cluster
    whose representative title is similar enough; otherwise start a new cluster.
    """
    clusters: List[Dict] = []  # each: {"rep": str, "listings": [...]}

    for l in listings:
        norm = _normalize(l.title)
        if not norm:
            continue
        placed = False
        for c in clusters:
            score = fuzz.token_set_ratio(norm, c["rep"])
            if score >= MATCH_THRESHOLD:
                c["listings"].append(l)
                # keep the longest representative (more info)
                if len(norm) > len(c["rep"]):
                    c["rep"] = norm
                placed = True
                break
        if not placed:
            clusters.append({"rep": norm, "listings": [l]})

    products: List[Product] = []
    for c in clusters:
        # Pick the listing with the most info as the canonical title
        best = max(c["listings"], key=lambda x: (len(x.title), x.confidence))
        # Most common category among listings
        cat_votes: Dict[Category, int] = defaultdict(int)
        for x in c["listings"]:
            cat_votes[x.category] += 1
        category = max(cat_votes.items(), key=lambda kv: kv[1])[0]

        products.append(Product(
            product_key=_key(c["rep"]),
            title=best.title,
            image_url=best.image_url,
            category=category,
            tags=[],
            listings=c["listings"],
        ))
    return products
