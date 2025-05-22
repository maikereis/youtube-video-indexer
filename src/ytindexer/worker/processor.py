import asyncio
import traceback
from typing import Any, Dict, Optional

from ytindexer.logging import logger
from ytindexer.queues import Queue
from ytindexer.worker.parser import YouTubeNotificationParser


class YouTubeNotificationProcessor:
    """
    Processes YouTube PubSubHubbub notifications from the queue using the parser
    """

    def __init__(self, notification_queue: Queue, output_queue: Queue, parser: Any = YouTubeNotificationParser()):
        self.notification_queue = notification_queue
        self.output_queue = output_queue
        self.parser = parser

    async def process_notification(self, xml_data: str) -> Optional[Dict[str, Any]]:
        """
        Process a single YouTube notification XML
        
        Returns a dictionary with extracted video metadata or None if processing fails
        """
        metadata = self.parser.parse(xml_data)
        if metadata is None:
            logger.warning("Notification processing returned None metadata")
        return metadata

    async def process_batch(self, batch_size: int = 10) -> int:
        """
        Process a batch of notifications from the queue
        
        Returns the number of successfully processed notifications
        """
        notifications = []
        processed = 0

        for _ in range(batch_size):
            notification = self.notification_queue.dequeue(timeout=0.1)
            if notification is None:
                break
            notifications.append(notification)

        if not notifications:
            return 0

        tasks = [self.process_notification(notification) for notification in notifications]
        results = await asyncio.gather(*tasks)

        for result in results:
            if result is not None:
                self.output_queue.enqueue(result)
                processed += 1

        logger.info(f"Processed {processed}/{len(notifications)} notifications")
        return processed

    async def run(self, poll_interval: float = 0.5):
        
        """
        Run the worker process to continuously process notifications
        """
        logger.info("Starting YouTube notification processor worker")

        try:
            while True:
                queue_size = self.notification_queue.queue_size()

                if queue_size > 0:
                    logger.debug(f"Queue has {queue_size} notifications pending")
                    await self.process_batch()
                else:
                    await asyncio.sleep(poll_interval)

        except KeyboardInterrupt:
            logger.info("Worker shutting down gracefully")
        except Exception as e:
            logger.error(f"Worker encountered an error: {str(e)}")
            logger.error(traceback.format_exc())
