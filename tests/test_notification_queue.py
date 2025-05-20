import json
import pytest
from unittest.mock import MagicMock, patch
from typing import Any, List

from ytindexer.database import ValkeyConnection
from ytindexer.queues.base import Queue
from ytindexer.queues.notification import NotificationQueue  # Assuming the class is in this module


@pytest.fixture
def mock_valkey_client():
    """Fixture to create a mock ValkeyConnection client."""
    mock_client = MagicMock()
    return mock_client


@pytest.fixture
def notification_queue(mock_valkey_client):
    """Fixture to create a NotificationQueue with a mock client."""
    queue = NotificationQueue(queue_name="test_queue")
    queue.client = mock_valkey_client
    return queue


class TestNotificationQueue:
    
    def test_initialization(self):
        """Test that the NotificationQueue initializes correctly."""
        queue = NotificationQueue(queue_name="test_initialization")
        assert queue.queue_name == "test_initialization"
        assert hasattr(queue, "client")
    
    def test_enqueue_string_data(self, notification_queue, mock_valkey_client):
        """Test enqueuing string data."""
        test_data = b"test_string_data"
        notification_queue.enqueue(test_data)
        mock_valkey_client.lpush.assert_called_once_with("test_queue", test_data)
    
    def test_enqueue_dict_data(self, notification_queue, mock_valkey_client):
        """Test enqueuing dictionary data (should be JSON serialized)."""
        test_data = {"key": "value", "number": 123}
        notification_queue.enqueue(test_data)
        mock_valkey_client.lpush.assert_called_once_with("test_queue", json.dumps(test_data))
    
    def test_enqueue_list_data(self, notification_queue, mock_valkey_client):
        """Test enqueuing list data (should be JSON serialized)."""
        test_data = ["item1", "item2", 123]
        notification_queue.enqueue(test_data)
        mock_valkey_client.lpush.assert_called_once_with("test_queue", json.dumps(test_data))
    
    def test_dequeue_no_result(self, notification_queue, mock_valkey_client):
        """Test dequeuing when there's no result."""
        mock_valkey_client.brpop.return_value = None
        result = notification_queue.dequeue()
        assert result is None
        mock_valkey_client.brpop.assert_called_once_with("test_queue", timeout=0.1)
    
    def test_dequeue_string_data(self, notification_queue, mock_valkey_client):
        """Test dequeuing string data."""
        test_data = b"test_string_data"
        mock_valkey_client.brpop.return_value = ("test_queue", test_data)
        result = notification_queue.dequeue()
        assert result == b"test_string_data"
        mock_valkey_client.brpop.assert_called_once_with("test_queue", timeout=0.1)
    
    def test_dequeue_json_data(self, notification_queue, mock_valkey_client):
        """Test dequeuing JSON data."""
        test_data = {"key": "value", "number": 123}
        encoded_data = json.dumps(test_data).encode()
        mock_valkey_client.brpop.return_value = ("test_queue", encoded_data)
        result = notification_queue.dequeue()
        assert result == test_data
        mock_valkey_client.brpop.assert_called_once_with("test_queue", timeout=0.1)
    
    def test_batch_dequeue_empty(self, notification_queue, mock_valkey_client):
        """Test batch dequeuing when queue is empty."""
        # Setup the pipeline mock
        pipeline_mock = MagicMock()
        mock_valkey_client.pipeline.return_value = pipeline_mock
        pipeline_mock.execute.return_value = [None, None, None]
        
        result = notification_queue.batch_dequeue(batch_size=3)
        
        assert result == []
        assert pipeline_mock.multi.call_count == 1
        assert pipeline_mock.rpop.call_count == 3
        assert pipeline_mock.execute.call_count == 1
    
    def test_batch_dequeue_mixed_data(self, notification_queue, mock_valkey_client):
        """Test batch dequeuing with mixed string and JSON data."""
        # Setup the pipeline mock
        pipeline_mock = MagicMock()
        mock_valkey_client.pipeline.return_value = pipeline_mock
        
        # Mix of JSON and string data
        json_data = json.dumps({"key": "value"}).encode()
        string_data = b"plain_text"
        none_data = None
        
        pipeline_mock.execute.return_value = [json_data, string_data, none_data]
        
        result = notification_queue.batch_dequeue(batch_size=3)
        
        expected = [{"key": "value"}, b"plain_text"]
        assert result == expected
        assert pipeline_mock.multi.call_count == 1
        assert pipeline_mock.rpop.call_count == 3
        assert pipeline_mock.execute.call_count == 1
    
    def test_queue_size(self, notification_queue, mock_valkey_client):
        """Test getting the queue size."""
        mock_valkey_client.llen.return_value = 42
        size = notification_queue.queue_size()
        assert size == 42
        mock_valkey_client.llen.assert_called_once_with("test_queue")