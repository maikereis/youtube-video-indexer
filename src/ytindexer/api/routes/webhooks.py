from fastapi import APIRouter, Depends, Request, Response

from ytindexer.api.dependencies import get_limiter, get_notification_queue
from ytindexer.logging import logger
from ytindexer.queues import MessageQueue

router = APIRouter()
limiter = get_limiter()


@router.get("")
@limiter.limit("30/minute")  # Example: limit to 10 requests per minute
async def verify_subscription(request: Request):
    """Handle YouTube PubSubHubbub subscription verification"""
    hub_mode = request.query_params.get("hub.mode")
    hub_challenge = request.query_params.get("hub.challenge")

    if hub_mode == "subscribe" and hub_challenge:
        logger.info(f"Verifying subscription: {hub_mode}")
        return Response(content=hub_challenge, media_type="text/plain")

    return Response(status_code=400)


@router.post("")
@limiter.limit("30/minute")  # Example: limit to 5 requests per minute
async def handle_notification(
    request: Request,
    notification_queue: MessageQueue = Depends(get_notification_queue),
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
