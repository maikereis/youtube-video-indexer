import asyncio
import traceback
from typing import Any, Dict, Optional

from ytindexer.logging import logger
from ytindexer.queues import Queue

from .parser import YouTubeNotification


class YouTubeNotificationProcessor:
    """
    Processes YouTube PubSubHubbub notifications from the queue using the parser.
    """

    def __init__(self, notification_queue: Queue, output_queue: Queue, parser: Any):
        self.notification_queue = notification_queue
        self.output_queue = output_queue
        self.parser = parser
        self._shutdown_event = asyncio.Event()

    async def process_notification(self, xml_data: str) -> Optional[Dict[str, Any]]:
        """
        Process a single YouTube notification XML.

        Args:
            xml_data (str): Raw XML data from the notification.

        Returns:
            Optional[Dict[str, Any]]: Extracted video metadata if successful, otherwise None.
        """
        try:
            metadata = self.parser.parse(xml_data)
            if metadata is None:
                logger.warning("Notification processing returned None metadata")
            return metadata
        except Exception as e:
            logger.error(f"Failed to process notification: {e}")
            logger.debug(traceback.format_exc())
            return None

    async def process_batch(self, batch_size: int = 10) -> int:
        """
        Process a batch of notifications from the queue.

        Args:
            batch_size (int): Number of notifications to process in a batch.

        Returns:
            int: Number of successfully processed notifications.
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
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error during notification processing: {result}")
                continue
            if result is not None:
                if isinstance(result, dict):
                    self.output_queue.enqueue(result)
                elif isinstance(result, YouTubeNotification):
                    self.output_queue.enqueue(result.model_dump_json())
                else:
                    raise ValueError(f"Can't equeue payload with type: {type(result)}")
                processed += 1

        logger.info(f"Processed {processed}/{len(notifications)} notifications")
        return processed

    async def run(self, poll_interval: float = 0.5):
        """
        Run the worker process to continuously process notifications.

        Args:
            poll_interval (float): Time to wait between polling the queue.
        """
        logger.info("Starting YouTube notification processor worker")

        try:
            while not self._shutdown_event.is_set():
                queue_size = self.notification_queue.queue_size()

                if queue_size > 0:
                    logger.debug(f"Queue has {queue_size} notifications pending")
                    await self.process_batch()
                else:
                    await asyncio.sleep(poll_interval)

        except asyncio.CancelledError:
            logger.info("Worker cancelled gracefully")
            raise
        except Exception as e:
            logger.error(f"Worker encountered an error: {str(e)}")
            logger.error(traceback.format_exc())

    def shutdown(self):
        """
        Signal the processor to shut down gracefully.
        """
        self._shutdown_event.set()
