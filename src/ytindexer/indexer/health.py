from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class HealthStatus:
    """Health check status for a service"""
    service_name: str
    is_healthy: bool
    response_time_ms: float
    message: str
    metadata: Optional[Dict[str, Any]] = None

class HealthCheckable(ABC):
    """Interface for services that support health checks"""
    
    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """Perform a health check and return status"""
        pass