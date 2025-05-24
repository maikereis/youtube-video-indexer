from abc import ABC, abstractmethod
from typing import Any, List


class Queue(ABC):
    """Abstract base class defining the interface for queue implementations.

    This class enforces methods for enqueuing, dequeuing (single and batch), and querying
    the size of the queue. Subclasses must implement these methods according to
    the underlying queue mechanism.
    """

    @abstractmethod
    def enqueue(self, task_data: Any) -> None:
        """
        Add an item to the queue.

        Args:
            task_data (Any): The item to be added to the queue.
        """
        pass

    @abstractmethod
    def dequeue(self) -> Any:
        """
        Remove and return a single item from the queue.

        Returns:
            Any: The item removed from the queue. Should return None if the queue is empty.
        """
        pass

    @abstractmethod
    def batch_dequeue(self, batch_size: int) -> List[Any]:
        """
        Remove and return multiple items from the queue.

        Args:
            batch_size (int): Number of items to remove from the queue.

        Returns:
            List[Any]: A list of items removed from the queue. The list can be shorter than
            batch_size if the queue has fewer items.
        """
        pass

    @abstractmethod
    def queue_size(self) -> int:
        """
        Return the current number of items in the queue.

        Returns:
            int: The count of items currently in the queue.
        """
        pass
