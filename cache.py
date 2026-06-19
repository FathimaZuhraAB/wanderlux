"""
FastAPI application entrypoint.

Run locally:
    cd backend
    uvicorn app.main:app --reload --port 8000

Then visit:
    http://localhost:8000/docs           — Swagger UI
    http://localhost:8000/api/sites      — list configured sources
    http://localhost:8000/api/search?q=iphone 15
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.api.routes import router

logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title=settings.app_name,
    description="Compare prices across 20+ Indian e-commerce and grocery sites.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "endpoints": ["/api/health", "/api/sites", "/api/search?q=..."],
    }
