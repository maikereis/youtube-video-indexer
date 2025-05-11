from fastapi import FastAPI, Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from notifications import NotificationQueue

MESSAGE_QUEUE_NAME = "yt_queue"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "pubsubhubbub.appspot.com", "*.ngrok-free.app"]

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["5/minute"],
)

app = FastAPI()

notification_queue = NotificationQueue(MESSAGE_QUEUE_NAME)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.get("/")
async def main():
    return {"message": "Hello World"}


@app.get("/webhooks")
@limiter.limit("10/minute")  # Example: limit to 10 requests per minute
async def verify_subscription(request: Request):
    hub_mode = request.query_params.get("hub.mode")
    hub_challenge = request.query_params.get("hub.challenge")
    if hub_mode == "subscribe" and hub_challenge:
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(status_code=400)


@app.post("/webhooks")
@limiter.limit("5/minute")  # Example: limit to 5 requests per minute
async def handle_notification(request: Request):
    # Handle content update
    content = await request.body()
    xml_data = content.decode("utf-8")
    notification_queue.enqueue(xml_data)
    return Response(status_code=200)
