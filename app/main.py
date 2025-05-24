from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from ytindexer.config import settings
from ytindexer.database import ValkeyConnection
from ytindexer.logging import configure_logging, logger
from ytindexer.queues import NotificationQueue

configure_logging(log_level="INFO", log_file="logs/api.log")

async def init_notification_queue() -> NotificationQueue:
    client = await ValkeyConnection(
        host=settings.valkey.host,
        port=settings.valkey.port,
        password=settings.valkey.password.get_secret_value(),
    ).connect()

    return NotificationQueue(client, "notification-queue")

app = FastAPI(
    title="YouTube Indexer API",
    description="API for YouTube video transcript indexation and search",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

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

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["10000/minute"],
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
async def main():
    return {"message": "Hello World"}


@app.get("/webhooks")
@limiter.limit("10000000000/minute")  # Example: limit to 10 requests per minute
async def verify_subscription(request: Request):
    """Handle YouTube PubSubHubbub subscription verification"""
    hub_mode = request.query_params.get("hub.mode")
    hub_challenge = request.query_params.get("hub.challenge")

    if hub_mode == "subscribe" and hub_challenge:
        logger.info(f"Verifying subscription: {hub_mode}")
        return Response(content=hub_challenge, media_type="text/plain")

    return Response(status_code=400)


@app.post("/webhooks")
@limiter.limit("1000000000/minute")  # Example: limit to 5 requests per minute
async def handle_notification(
    request: Request,
    notification_queue: NotificationQueue = Depends(init_notification_queue),
):    
    """Handle YouTube PubSubHubbub content notification"""
    try:
        # Handle content update
        content = await request.body()
        xml_data = content.decode("utf-8")
        
        # Enqueue notification for processing
        notification_queue.enqueue(xml_data)
        logger.info("Enqueued YouTube notification")
        
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Error handling notification: {str(e)}")
        return Response(status_code=500)
