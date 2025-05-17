import asyncio

from ytindexer.indexer import VideoIndexer
from ytindexer.queue import NotificationQueue


async def main():
    metadata_queue = NotificationQueue(queue_name="metadata_queue")
    indexer = VideoIndexer(metadata_queue)
    await indexer.run_worker()

if __name__ == "__main__":
    asyncio.run(main())
