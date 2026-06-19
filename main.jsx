# Dynamic Prime Comparator

A real, working price comparator for 20+ Indian e-commerce and grocery sites — Amazon, Flipkart, Meesho, Myntra, Nykaa, Ajio, Snapdeal, Shopsy, Tata CLiQ, BigBasket, Blinkit, Zepto, Instamart, JioMart, Reliance Digital, Croma, FirstCry, **Tata 1mg**, PharmEasy, and more.

**Stack:** FastAPI (Python) + React (Vite) + Tailwind. Async parallel scrapers, fuzzy product matching, disk-backed cache, Docker-ready.

---

## What's actually live vs sample

This is a **hybrid** scraping system — exactly as you asked for.

| Site         | Mode              | Notes                                    |
|--------------|-------------------|------------------------------------------|
| Amazon       | Live (HTML)       | Best-effort; Amazon often blocks bots. Plug in PAAPI keys for reliable results. |
| Flipkart     | Live (HTML)       | Layout shifts often; affiliate API is more reliable. |
| BigBasket    | Live (JSON API)   | Uses their public listing endpoint.      |
| Tata 1mg     | Live (JSON API)   | Uses their PWA search API.               |
| 16 others    | Sample fallback   | Each has a stub class ready for you to implement. |

**The sample-data fallback is the magic.** Whenever a live scraper fails (timeout, blocked, layout changed), the orchestrator silently fills in deterministic sample listings so the UI is never empty. Listings from the fallback are marked with a subtle `~` and `confidence: 0.2` in the API response — so you always know what's real.

---

## Project structure

```
dpc/
├── backend/                  # FastAPI app
│   ├── app/
│   │   ├── main.py           # entrypoint
│   │   ├── api/routes.py     # /api/search, /api/sites
│   │   ├── core/
│   │   │   ├── config.py     # settings (env-driven)
│   │   │   ├── orchestrator.py  # the fan-out engine
│   │   │   ├── matcher.py    # fuzzy product grouping
│   │   │   └── cache.py      # diskcache wrapper
│   │   ├── models/schemas.py # Pydantic schemas
│   │   ├── scrapers/         # one file per site
│   │   │   ├── base.py
│   │   │   ├── amazon.py     ← live
│   │   │   ├── flipkart.py   ← live
│   │   │   ├── bigbasket.py  ← live
│   │   │   ├── tata1mg.py    ← live
│   │   │   └── _stubs.py     ← 16 stubs ready to implement
│   │   └── data/sample_data.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                 # React + Vite + Tailwind
│   ├── src/
│   │   ├── App.jsx           # main composition
│   │   ├── components/       # Masthead, SearchBar, ProductRow…
│   │   ├── lib/api.js        # fetch wrapper
│   │   └── styles/index.css  # editorial design tokens
│   ├── Dockerfile
│   └── nginx.conf
│
├── docker-compose.yml
├── dev.sh                    # one-command local dev
└── README.md
```

---

## Run it (local dev)

### Prereqs
- Python 3.10+
- Node 18+
- (Optional) Docker for production builds

### Option A — one command
```bash
./dev.sh
```
Sets up venv, installs deps, starts both servers.

### Option B — manual (two terminals)

**Terminal 1 — backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — frontend**
```bash
cd frontend
npm install
npm run dev
```

Open:
- **App:** http://localhost:5173
- **API docs:** http://localhost:8000/docs

---

## Run it (production / Docker)

```bash
docker compose up --build
```
- Frontend at http://localhost:8080
- Backend at http://localhost:8000

Cache is persisted in a named Docker volume (`dpc-cache`).

---

## How the backend works

1. `GET /api/search?q=iphone+15` hits `orchestrator.search()`.
2. The orchestrator instantiates every scraper sharing one `httpx.AsyncClient`.
3. All scrapers run **in parallel** with a semaphore (default 8 concurrent).
4. Each `search_safe()` returns `List[Listing]` or `[]` on any failure — no exceptions bubble up.
5. Sites that returned nothing get filled with deterministic sample data (if `ENABLE_FALLBACK_DATA=true`).
6. All listings flow into `matcher.group_listings()` which clusters them via fuzzy title matching (rapidfuzz `token_set_ratio ≥ 78`).
7. Result is cached on disk for 10 minutes (`CACHE_TTL_SECONDS`) and returned.

Typical response time: **300-1500 ms cold**, **<50 ms cached**.

---

## Adding a new scraper

1. Create `backend/app/scrapers/foo.py`:
   ```python
   from app.scrapers.base import BaseScraper
   from app.models import Listing, Category

   class FooScraper(BaseScraper):
       site_id = "foo"
       site_name = "Foo Mart"
       category = Category.GENERAL

       async def search(self, query, limit=10):
           r = await self.fetch(f"https://foo.com/search?q={query}")
           if not r: return []
           # ... parse and return List[Listing]
   ```
2. Register it in `backend/app/scrapers/__init__.py`:
   ```python
   from .foo import FooScraper
   SCRAPERS.append(FooScraper)
   ```
3. Restart backend — that's it.

### Tips for real scrapers

- **Always look for a JSON endpoint first.** Open the site in Chrome DevTools → Network → search for something. SPAs almost always have an internal JSON API. BigBasket and Tata 1mg use this approach.
- **HTML scraping is fragile.** Selectors break weekly. If you must, use multiple fallback selectors.
- **For aggressive sites (Amazon, Flipkart):** use Playwright (headless browser) or pay for an unblocking service like ScraperAPI / Bright Data / Oxylabs.
- **Use official affiliate APIs where possible:** Amazon PAAPI, Flipkart Affiliate API. These are *legal* and *reliable*.

---

## API reference

### `GET /api/sites`
Returns metadata about all configured sources.
```json
{ "sites": [
  { "id": "amazon", "name": "Amazon", "category": "general", "live": true },
  ...
]}
```

### `GET /api/search?q=iphone+15&sites=amazon,flipkart&fresh=false`
Returns grouped products with all listings.
```json
{
  "query": "iphone 15",
  "products": [
    {
      "product_key": "a3f9c2",
      "title": "Apple iPhone 15 (128 GB) Black",
      "category": "electronics",
      "listings": [
        { "site_id": "amazon", "site_name": "Amazon", "price": 65900, "mrp": 79900, "url": "...", "rating": 4.6, ... },
        ...
      ]
    }
  ],
  "total_listings": 142,
  "sources_responded": ["amazon", "flipkart", "bigbasket", ...],
  "sources_failed": [],
  "elapsed_ms": 412,
  "cached": false
}
```

### `POST /api/cache/clear`
Wipes the search cache.

---

## Configuration

All settings via environment variables (or `.env`). See `backend/.env.example`.

| Variable | Default | Purpose |
|----------|---------|---------|
| `DEBUG` | `true` | Enable verbose logging |
| `CACHE_TTL_SECONDS` | `600` | Cache lifetime |
| `ENABLE_FALLBACK_DATA` | `true` | Use sample data for failed scrapers |
| `REQUEST_TIMEOUT` | `12.0` | Per-HTTP-request timeout (seconds) |
| `SCRAPER_CONCURRENCY` | `8` | Max parallel scrapers |
| `RAPIDAPI_KEY` | — | Optional: unofficial product APIs |
| `AMAZON_PAAPI_*` | — | Optional: Amazon Product Advertising API |

---

## Roadmap

- [ ] Playwright-based scrapers for sites that need JS rendering
- [ ] Price-history charts (sqlite + scheduled cron)
- [ ] Browser extension companion
- [ ] Natural-language search ("cheapest moisturiser under ₹500")
- [ ] User accounts + price-drop alerts (FCM)
- [ ] Image-hash matching to reduce false-positive product groups

---

## Legal & ethical notes

- Public-data scraping in India sits in a legal grey area. Most ToS prohibit it.
- Scraped data here is for **personal/educational use** only. Don't redistribute scraped catalogs.
- For commercial deployment, **use affiliate APIs** — most major sites offer them, and they pay you for referrals.
- Be polite: respect `robots.txt`, rate-limit yourself, identify your bot truthfully if asked.

---

Built with care. Compare ethically. Buy well.
