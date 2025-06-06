"""
FastAPI application setup for the YouTube Indexer API.

This module configures the FastAPI app with:
- API metadata (title, description, version, docs URLs)
- Route inclusion for health checks, webhooks, videos, and channels
- Middleware setup for trusted hosts, CORS, and rate limiting
- Logging configuration for the API server

The app enables transcript indexation and search for YouTube videos.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from ytindexer.api.dependencies import get_limiter
from ytindexer.api.routes import channels, health, videos, webhooks
from ytindexer.logging import configure_logging, logger

configure_logging(log_level="INFO", log_file="logs/api.log")

logger.info("Starting YTindexer API.")

app = FastAPI(
    title="YouTube Indexer API",
    description="API for YouTube video transcript indexation and search",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

logger.info("Including routes.")

app.include_router(health.router)
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(videos.router, prefix="/api/v1/videos", tags=["videos"])
app.include_router(channels.router, prefix="/api/v1/channels", tags=["channels"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])


logger.info("Configuring middlewares.")

allowed_hosts = [
    "localhost",
    "127.0.0.1",
    "pubsubhubbub.appspot.com",
    "*.ngrok-free.app",
]

app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

origins = [
    "http://*.ngrok-free.app",
    "https://*.ngrok-free.app",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = get_limiter()
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

logger.info("All done!.")
