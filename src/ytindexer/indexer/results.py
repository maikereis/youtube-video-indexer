from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class OperationStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL_SUCCESS = "partial_success"

@dataclass
class OperationResult:
    """Result of a database or indexing operation"""
    status: OperationStatus
    message: str
    error: Optional[Exception] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def is_success(self) -> bool:
        return self.status == OperationStatus.SUCCESS
    
    @property
    def is_failure(self) -> bool:
        return self.status == OperationStatus.FAILURE
    
    @classmethod
    def success(cls, message: str, metadata: Optional[Dict[str, Any]] = None) -> 'OperationResult':
        return cls(OperationStatus.SUCCESS, message, metadata=metadata)
    
    @classmethod
    def failure(cls, message: str, error: Optional[Exception] = None, 
                metadata: Optional[Dict[str, Any]] = None) -> 'OperationResult':
        return cls(OperationStatus.FAILURE, message, error, metadata)
    
    @classmethod
    def partial_success(cls, message: str, metadata: Optional[Dict[str, Any]] = None) -> 'OperationResult':
        return cls(OperationStatus.PARTIAL_SUCCESS, message, metadata=metadata)

@dataclass
class ProcessingResult:
    """Result of processing a video through all services"""
    video_id: str
    storage_result: OperationResult
    indexing_result: OperationResult
    stats_result: OperationResult
    
    @property
    def overall_status(self) -> OperationStatus:
        if all(r.is_success for r in [self.storage_result, self.indexing_result, self.stats_result]):
            return OperationStatus.SUCCESS
        elif self.storage_result.is_success:
            return OperationStatus.PARTIAL_SUCCESS
        else:
            return OperationStatus.FAILURE
    
    @property
    def is_success(self) -> bool:
        return self.overall_status == OperationStatus.SUCCESS