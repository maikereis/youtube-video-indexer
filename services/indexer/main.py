import asyncio

from ytindexer.queues import NotificationQueue
from ytindexer.indexer import VideoIndexer


async def main():
    metadata_queue = NotificationQueue(queue_name="metadata_queue")
    indexer = VideoIndexer(metadata_queue)
    await indexer.run_worker()

if __name__ == "__main__":
    asyncio.run(main())
