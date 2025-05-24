import asyncio
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar('T')

class AsyncDatabaseConnection(Generic[T], ABC):
    """
    Abstract base class for asynchronous database connections.

    This class defines the interface for establishing and closing
    asynchronous connections to a database or similar resource.
    Intended to be used with dependency injection.

    Args:
        *args: Variable length argument list for subclasses.
        **kwargs: Arbitrary keyword arguments for subclasses.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the connection instance.

        Subclasses may override this to accept parameters such as
        database URLs or credentials.
        """
        pass

    @abstractmethod
    async def connect(self) -> T:
        """
        Establish and return the asynchronous database connection.

        This method should be overridden by subclasses to implement
        the logic for creating the actual connection.

        Returns:
            T: An instance representing the database connection.
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """
        Close the database connection.

        This method should be overridden by subclasses to implement
        proper cleanup and resource deallocation.

        Returns:
            None
        """
        raise NotImplementedError
