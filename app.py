from fastapi import FastAPI, Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

import xml.etree.ElementTree as ET

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["5/minute"],
)

app = FastAPI()

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "pubsubhubbub.appspot.com", "*.ngrok-free.app"]
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

def handle_response(xml_data: str):
    try:
        # Parse the XML content
        root = ET.fromstring(xml_data)

        # Define namespaces
        namespaces = {
            "atom": "http://www.w3.org/2005/Atom",
            "yt": "http://www.youtube.com/xml/schemas/2015",
        }

        # Find the entry element
        entry = root.find("atom:entry", namespaces)
        if entry is not None:
            video_id = entry.find("yt:videoId", namespaces).text
            channel_id = entry.find("yt:channelId", namespaces).text
            title = entry.find("atom:title", namespaces).text
            published = entry.find("atom:published", namespaces).text
            updated = entry.find("atom:updated", namespaces).text

            # Process the extracted information as needed
            print(f"New video uploaded: {title} (ID: {video_id}) on channel {channel_id}")
            print(f"Published at: {published}, Updated at: {updated}")
        else:
            print("No entry found in the feed.")

    except ET.ParseError as e:
        print(f"Failed to parse XML: {e}")

@app.post("/webhooks")
@limiter.limit("5/minute")  # Example: limit to 5 requests per minute
async def handle_notification(request: Request):
    # Handle content update
    content = await request.body()
    handle_response(content)
    return Response(status_code=200)
