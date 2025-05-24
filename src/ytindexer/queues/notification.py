import json
from typing import Any, List

from ytindexer.logging import logger

from .base import Queue


class NotificationQueue(Queue):
    """Queue implementation using Valkey/Redis for notification tasks.

    This queue stores serialized JSON-compatible tasks in a Redis list.
    Tasks can be enqueued, dequeued singly or in batches.

    Attributes:
        client (Any): Redis or Valkey client instance used for queue operations.
        queue_name (str): Name/key of the Redis list representing the queue.
    """

    def __init__(self, client: Any, queue_name: str = "queue"):
        """
        Initialize a NotificationQueue instance.

        Args:
            client (Any): Redis/Valkey client instance.
            queue_name (str, optional): Name of the queue (Redis list key). Defaults to "queue".
        """
        self.client = client
        self.queue_name = queue_name
        logger.info(f"Initialized NotificationQueue with name: {queue_name}")

    def enqueue(self, task_data: Any) -> None:
        """
        Add a task to the queue.

        Serializes the task to JSON if it is a dict or list before pushing.

        Args:
            task_data (Any): The task data to enqueue. Can be any JSON-serializable object or string.
        """
        if isinstance(task_data, (dict, list)):
            task_data = json.dumps(task_data)
        self.client.lpush(self.queue_name, task_data)
        logger.debug(f"Enqueued task to {self.queue_name}")

    def dequeue(self, timeout: float = 0.1) -> Any:
        """
        Remove and return a single task from the queue.

        Performs a blocking pop with a timeout.

        Args:
            timeout (float, optional): Timeout in seconds to wait for a task before returning None. Defaults to 0.1.

        Returns:
            Any: The dequeued task, parsed from JSON if possible, or raw string if not JSON. Returns None if no task is available.
        """
        result = self.client.brpop(self.queue_name, timeout=timeout)
        if not result:
            return None

        data = result[1]
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data

    def batch_dequeue(self, batch_size: int = 10) -> List[Any]:
        """
        Remove and return multiple tasks from the queue in a batch.

        Uses a Redis pipeline to pop multiple items atomically.

        Args:
            batch_size (int, optional): Number of tasks to dequeue. Defaults to 10.

        Returns:
            List[Any]: List of dequeued tasks, each parsed from JSON if possible, otherwise raw string.
        """
        pipeline = self.client.pipeline()
        pipeline.multi()
        for _ in range(batch_size):
            pipeline.rpop(self.queue_name)
        results = pipeline.execute()

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
        """
        Get the current size of the queue.

        Returns:
            int: Number of tasks currently in the queue.
        """
        return self.client.llen(self.queue_name)
