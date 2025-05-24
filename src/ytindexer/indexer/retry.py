import asyncio
import random
from functools import wraps
from typing import Any, Callable, List, Optional, TypeVar, Union

from ytindexer.logging import logger

from .config import RetryConfig

T = TypeVar('T')

class RetryableOperation:
    """Handles retry logic with exponential backoff"""
    
    def __init__(self, config: RetryConfig, non_retry_exceptions: Optional[List[Union[type, str]]] = None):
        self.config = config
        self.non_retry_exceptions = non_retry_exceptions or []

    def _is_non_retryable(self, exception: Exception) -> bool:
        """Check if an exception is non-retryable."""
        for item in self.non_retry_exceptions:
            if isinstance(item, str) and item.lower() in str(exception).lower():
                return True
            if isinstance(item, type) and isinstance(exception, item):
                return True
        return False
    
    async def execute(self, operation: Callable[[], T], operation_name: str = "operation") -> T:
        """Execute an operation with retry logic"""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                result = await operation()
                if attempt > 1:
                    logger.info(f"{operation_name} succeeded on attempt {attempt}")
                return result
            except Exception as e:
                if self._is_non_retryable(e):
                    logger.warning(f"{operation_name} skipped due to non-retryable error: {e}")
                    return None

                last_exception = e
                if attempt == self.config.max_attempts:
                    logger.error(f"{operation_name} failed after {attempt} attempts: {str(e)}")
                    break
                
                delay = min(
                    self.config.base_delay * (self.config.exponential_base ** (attempt - 1)),
                    self.config.max_delay
                )
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0.1, 0.3) * delay
                total_delay = delay + jitter
                
                logger.warning(f"{operation_name} failed on attempt {attempt}, retrying in {total_delay:.2f}s: {str(e)}")
                await asyncio.sleep(total_delay)
        
        raise last_exception

def with_retry(config: RetryConfig, operation_name: str = None):
    """Decorator for adding retry logic to async functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_op = RetryableOperation(config)
            name = operation_name or func.__name__
            return await retry_op.execute(lambda: func(*args, **kwargs), name)
        return wrapper
    return decorator