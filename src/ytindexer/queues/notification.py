import json
from typing import Any, List

from ytindexer.database import ValkeyConnection
from ytindexer.config import settings
from ytindexer.logging import logger
from ytindexer.queues.base import Queue

class NotificationQueue(Queue):
    """Queue implementation using Valkey/Redis"""
    
    def __init__(self, queue_name: str = "queue", client: Any = ValkeyConnection()):
        self.client = client
        self.queue_name = queue_name
        logger.info(f"Initialized NotificationQueue with name: {queue_name}")
    
    def enqueue(self, task_data: Any) -> None:
        """Add a task to the queue"""
        if isinstance(task_data, (dict, list)):
            task_data = json.dumps(task_data)
        self.client.lpush(self.queue_name, task_data)
        logger.debug(f"Enqueued task to {self.queue_name}")
    
    def dequeue(self, timeout: float = 0.1) -> Any:
        """Remove and return a task from the queue"""
        result = self.client.brpop(self.queue_name, timeout=timeout)
        if not result:
            return None
        
        data = result[1]
        try:
            # Try to parse JSON if it's JSON data
            return json.loads(data)
        except json.JSONDecodeError:
            # Return as is if it's not JSON
            return data

    def batch_dequeue(self, batch_size: int = 10) -> List[Any]:
        """Remove and return multiple tasks from the queue"""
        pipeline = self.client.pipeline()
        
        # Use multi/exec to make this atomic
        pipeline.multi()
        for _ in range(batch_size):
            pipeline.rpop(self.queue_name)
        results = pipeline.execute()
        
        # Filter out None values and parse JSON if applicable
        processed_results = []
        for result in results:
            if result is None:
                continue
                
            try:
                processed_results.append(json.loads(result))
            except json.JSONDecodeError:
                processed_results.append(result)
                
        return processed_results

    def queue_size(self) -> int:
        """Return the current size of the queue"""
        return self.client.llen(self.queue_name)
