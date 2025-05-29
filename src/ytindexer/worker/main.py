import asyncio

from ytindexer.config import settings
from ytindexer.database import ValkeyConnection
from ytindexer.queues import NotificationQueue
from ytindexer.worker import (YouTubeNotificationParser,
                              YouTubeNotificationProcessor)


async def main():

    valkey_client = ValkeyConnection(
        host=settings.valkey.host,
        port=settings.valkey.port,
        password=settings.valkey.password.get_secret_value(),
    )

    valkey_conn = await valkey_client.connect()

    notification_queue = NotificationQueue(valkey_conn, "notification-queue")
    output_queue = NotificationQueue(valkey_conn, "output-queue")
    parser = YouTubeNotificationParser()

    processor = YouTubeNotificationProcessor(notification_queue, output_queue, parser)

    await processor.run()


if __name__ == "__main__":
    asyncio.run(main())
