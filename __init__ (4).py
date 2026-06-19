"""
Application configuration. Reads from environment variables with sensible defaults.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    app_name: str = "Dynamic Prime Comparator"
    debug: bool = True
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # --- Scraping ---
    request_timeout: float = 12.0          # seconds per HTTP request
    scraper_concurrency: int = 8           # max parallel scrapers per query
    cache_ttl_seconds: int = 600           # 10 minutes — prices change, but not every second
    cache_dir: str = ".cache"

    # --- Fallback behavior ---
    # When True, sites that fail/timeout fall back to cached or sample data
    # so the UI is never empty. Set to False to surface real failures.
    enable_fallback_data: bool = True

    # --- Optional API keys (used by official-API scrapers if you have them) ---
    rapidapi_key: str = ""                 # for unofficial product APIs on RapidAPI
    amazon_paapi_access_key: str = ""      # Amazon Product Advertising API
    amazon_paapi_secret: str = ""
    amazon_paapi_partner_tag: str = ""
    flipkart_affiliate_id: str = ""
    flipkart_affiliate_token: str = ""


settings = Settings()
