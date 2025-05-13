# %%
import os
from abc import ABC, abstractmethod
from typing import Any

QUEUE_DB_HOST = os.getenv("QUEUE_DB_HOST")
QUEUE_DB_PORT = os.getenv("QUEUE_DB_PORT")


class Queue(ABC):
    @abstractmethod
    def enqueue(self) -> None:
        pass

    @abstractmethod
    def dequeue(self) -> str:
        pass


class NotificationQueue(Queue):
    def __init__(self, queue_name: str = "queue"):
        self.client = valkey.Valkey(host=QUEUE_DB_HOST, port=QUEUE_DB_PORT, db=0)
        self.queue_name = queue_name

    def enqueue(self, task_data: Any) -> None:
        self.client.lpush(self.queue_name, task_data)

    def dequeue(self, timeout: int = 0.1) -> Any:
        result = self.client.brpop(self.queue_name, timeout=timeout)
        return result[1] if result else None


queue = ValkeyQueue("youtube_notifications")

# %%
queue.enqueue("aaa")

# %%
queue.dequeue().decode()

# %%
queue.enqueue("aaa")
queue.enqueue("bbb")

# %%
queue.dequeue().decode()

# %%
queue.dequeue().decode()


