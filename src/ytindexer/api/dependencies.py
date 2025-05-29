from slowapi import Limiter
from slowapi.util import get_remote_address

from ytindexer.database import ValkeyConnection
from ytindexer.queues import NotificationQueue
from ytindexer.config import settings

def get_limiter() -> Limiter:
    return Limiter(
        key_func=get_remote_address,
        default_limits=["500/minute"],
    )

async def get_notification_queue() -> NotificationQueue:
    client = await ValkeyConnection(
        host=settings.valkey.host,
        port=settings.valkey.port,
        password=settings.valkey.password.get_secret_value(),
    ).connect()
    return NotificationQueue(client, "notification-queue")