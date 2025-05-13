from fastapi import FastAPI, Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from ytindexer.logging import logger
from ytindexer.queue import NotificationQueue
from ytindexer.config import settings


queue_name = "yt_queue"
message_queue = NotificationQueue(queue_name)


app = FastAPI(
    title="YouTube Indexer API",
    description="API for YouTube video transcript indexation and search",
    version="1.0.0",
)

allowed_hosts = [
    "localhost",
    "127.0.0.1",
    "pubsubhubbub.appspot.com",
    settings.ngrok.url,
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
    default_limits=["5/minute"],
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
async def main():
    return {"message": "Hello World"}


@app.get("/webhooks")
@limiter.limit("10/minute")  # Example: limit to 10 requests per minute
async def verify_subscription(request: Request):
    """Handle YouTube PubSubHubbub subscription verification"""
    hub_mode = request.query_params.get("hub.mode")
    hub_challenge = request.query_params.get("hub.challenge")

    if hub_mode == "subscribe" and hub_challenge:
        logger.info(f"Verifying subscription: {hub_mode}")
        return Response(content=hub_challenge, media_type="text/plain")

    return Response(status_code=400)


@app.post("/webhooks")
@limiter.limit("5/minute")  # Example: limit to 5 requests per minute
async def handle_notification(request: Request):
    """Handle YouTube PubSubHubbub content notification"""
    try:
        # Handle content update
        content = await request.body()
        xml_data = content.decode("utf-8")
        
        # Enqueue notification for processing
        message_queue.enqueue(xml_data)
        logger.info("Enqueued YouTube notification")
        
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Error handling notification: {str(e)}")
        return Response(status_code=500)
