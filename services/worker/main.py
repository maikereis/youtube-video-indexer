import asyncio

from ytindexer.queues import NotificationQueue
from ytindexer.worker import YouTubeNotificationProcessor


async def main():
    notification_queue = NotificationQueue(queue_name="notification_queue")
    metadata_queue = NotificationQueue(queue_name="metadata_queue")

    indexer = YouTubeNotificationProcessor(notification_queue, metadata_queue)
    await indexer.run()

if __name__ == "__main__":
    asyncio.run(main())
