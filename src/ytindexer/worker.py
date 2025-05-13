import asyncio
import json
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional

from ytindexer.logging import logger
from ytindexer.queue import Queue


class YouTubeNotificationProcessor:
    """
    Processes YouTube PubSubHubbub notifications from the queue
    """
    def __init__(self, notification_queue: Queue, output_queue: Queue):
        self.notification_queue = notification_queue
        self.output_queue = output_queue
        
    async def process_notification(self, xml_data: str) -> Optional[Dict[str, Any]]:
        """
        Process a single YouTube notification XML
        
        Returns a dictionary with extracted video metadata or None if processing fails
        """
        try:
            # Parse the XML notification
            root = ET.fromstring(xml_data)

            # Find the YouTube video ID
            namespaces = {
                'xmlns': 'http://www.w3.org/2005/Atom',
                'yt': 'http://www.youtube.com/xml/schemas/2015'
            }

            entry = root.find('xmlns:entry', namespaces)
            if entry is None:
                logger.warning("No entry found in notification XML")
                return None

            video_id = entry.find("yt:videoId", namespaces).text

            if not video_id:
                logger.warning("Could not extract video ID from notification")
                return None

            channel_id = entry.find("yt:channelId", namespaces).text

            title = entry.find("atom:title", namespaces).text

            published_at = entry.find("atom:published", namespaces).text

            updated_at = entry.find("atom:updated", namespaces).text

            link = entry.find('xmlns:link', namespaces).get('href')

            author = entry.find('./xmlns:author/xmlns:name', namespaces)

            metadata = {
                "video_id": video_id,
                "channel_id": channel_id,
                "title": title,
                "published": published,
                "updated": updated,
                "link": link,
                "author": author,
                "processed_at": datetime.utcnow().isoformat(),
                "source": "pubsubhubbub"
            }
            
            return metadata

        except Exception as e:
            logger.error(f"Failed to process notification: {str(e)}")
            logger.debug(f"Notification data: {xml_data}")
            logger.debug(traceback.format_exc())
            return None
            
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

    async def run_worker(self, poll_interval: float = 0.5):
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
                    # If queue is empty, sleep before checking again
                    await asyncio.sleep(poll_interval)
                    
        except KeyboardInterrupt:
            logger.info("Worker shutting down gracefully")
        except Exception as e:
            logger.error(f"Worker encountered an error: {str(e)}")
            logger.error(traceback.format_exc())