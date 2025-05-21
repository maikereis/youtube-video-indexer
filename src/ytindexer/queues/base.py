from typing import Any, List
from abc import ABC, abstractmethod

class Queue(ABC):
    """Abstract base class for queue implementations"""
    
    @abstractmethod
    def enqueue(self, task_data: Any) -> None:
        """Add an item to the queue"""
        pass
    
    @abstractmethod
    def dequeue(self) -> Any:
        """Remove and return an item from the queue"""
        pass

    @abstractmethod
    def batch_dequeue(self, batch_size: int) -> List[Any]:
        """Remove and return multiple items from the queue"""
        pass

    @abstractmethod
    def queue_size(self) -> int:
        """Return the current size of the queue"""
        pass