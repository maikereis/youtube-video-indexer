"""
Unit tests for the MessageQueue class in ytindexer.queues.

These tests cover:
- Enqueueing data to the queue (dict, string)
- Dequeueing single and batch tasks
- Handling of JSON and non-JSON data
- Edge cases like empty queue and malformed JSON
- Queue size queries
"""

import json
from unittest.mock import MagicMock

import pytest

from ytindexer.queues import MessageQueue


@pytest.fixture
def mock_redis_client():
    """Fixture providing a mocked Redis client."""
    return MagicMock()


def test_enqueue(mock_redis_client):
    """
    Test that enqueue serializes dict data to JSON and pushes to Redis list.
    """
    queue = MessageQueue(client=mock_redis_client)
    task_data = {"task": "process_data"}

    queue.enqueue(task_data)

    serialized_data = json.dumps(task_data)
    mock_redis_client.lpush.assert_called_once_with(queue.queue_name, serialized_data)


def test_dequeue(mock_redis_client):
    """
    Test that dequeue returns the deserialized task data from Redis.
    """
    queue = MessageQueue(client=mock_redis_client)
    task_data = {"task": "process_data"}
    serialized_data = json.dumps(task_data)
    mock_redis_client.brpop.return_value = (queue.queue_name, serialized_data)

    result = queue.dequeue()

    assert result == task_data
    mock_redis_client.brpop.assert_called_once_with(queue.queue_name, timeout=0.1)


def test_batch_dequeue(mock_redis_client):
    """
    Test batch_dequeue returns a list of deserialized tasks using Redis pipeline.
    """
    queue = MessageQueue(client=mock_redis_client)
    task_data_list = [{"task": "task1"}, {"task": "task2"}, {"task": "task3"}]
    serialized_data_list = [json.dumps(task) for task in task_data_list]

    pipeline = MagicMock()
    pipeline.multi.return_value = None
    pipeline.rpop.side_effect = [None for _ in serialized_data_list]
    pipeline.execute.return_value = serialized_data_list
    mock_redis_client.pipeline.return_value = pipeline

    result = queue.batch_dequeue(batch_size=3)

    assert result == task_data_list
    mock_redis_client.pipeline.assert_called_once()
    pipeline.multi.assert_called_once()
    assert pipeline.rpop.call_count == 3
    pipeline.execute.assert_called_once()


def test_queue_size(mock_redis_client):
    """
    Test queue_size returns the current length of the Redis list.
    """
    queue = MessageQueue(client=mock_redis_client)
    mock_redis_client.llen.return_value = 5

    size = queue.queue_size()

    assert size == 5
    mock_redis_client.llen.assert_called_once_with(queue.queue_name)


def test_dequeue_non_json(mock_redis_client):
    """
    Test dequeue returns raw data when Redis returns non-JSON bytes.
    """
    queue = MessageQueue(client=mock_redis_client)
    raw_data = b"plain_text_data"
    mock_redis_client.brpop.return_value = (queue.queue_name, raw_data)

    result = queue.dequeue()

    assert result == raw_data
    mock_redis_client.brpop.assert_called_once_with(queue.queue_name, timeout=0.1)


def test_dequeue_empty_queue(mock_redis_client):
    """
    Test dequeue returns None when Redis queue is empty.
    """
    queue = MessageQueue(client=mock_redis_client)
    mock_redis_client.brpop.return_value = None

    result = queue.dequeue()

    assert result is None
    mock_redis_client.brpop.assert_called_once_with(queue.queue_name, timeout=0.1)


def test_batch_dequeue_empty_queue(mock_redis_client):
    """
    Test batch_dequeue returns empty list when Redis queue is empty.
    """
    queue = MessageQueue(client=mock_redis_client)
    pipeline = MagicMock()
    pipeline.multi.return_value = None
    pipeline.rpop.side_effect = [None for _ in range(3)]
    pipeline.execute.return_value = [None, None, None]
    mock_redis_client.pipeline.return_value = pipeline

    result = queue.batch_dequeue(batch_size=3)

    assert result == []
    mock_redis_client.pipeline.assert_called_once()
    pipeline.multi.assert_called_once()
    assert pipeline.rpop.call_count == 3
    pipeline.execute.assert_called_once()


def test_queue_size_zero(mock_redis_client):
    """
    Test queue_size returns zero when Redis list is empty.
    """
    queue = MessageQueue(client=mock_redis_client)
    mock_redis_client.llen.return_value = 0

    size = queue.queue_size()

    assert size == 0
    mock_redis_client.llen.assert_called_once_with(queue.queue_name)


def test_enqueue_string_data(mock_redis_client):
    """
    Test enqueue passes through string data without JSON serialization.
    """
    queue = MessageQueue(client=mock_redis_client)
    task_data = "simple_task"

    queue.enqueue(task_data)

    mock_redis_client.lpush.assert_called_once_with(queue.queue_name, task_data)


def test_dequeue_malformed_json(mock_redis_client):
    """
    Test dequeue returns raw bytes if JSON deserialization fails.
    """
    queue = MessageQueue(client=mock_redis_client)
    malformed_json = b'{"task": "incomplete"'
    mock_redis_client.brpop.return_value = (queue.queue_name, malformed_json)

    result = queue.dequeue()

    assert result == malformed_json
    mock_redis_client.brpop.assert_called_once_with(queue.queue_name, timeout=0.1)


def test_batch_dequeue_malformed_json(mock_redis_client):
    """
    Test batch_dequeue returns mixture of deserialized and raw data for malformed JSON.
    """
    queue = MessageQueue(client=mock_redis_client)
    valid_json = json.dumps({"task": "valid"})
    malformed_json = b'{"task": "invalid"'
    pipeline = MagicMock()
    pipeline.multi.return_value = None
    pipeline.rpop.side_effect = [None, None]
    pipeline.execute.return_value = [valid_json, malformed_json]
    mock_redis_client.pipeline.return_value = pipeline

    result = queue.batch_dequeue(batch_size=2)

    assert result == [{"task": "valid"}, malformed_json]
    mock_redis_client.pipeline.assert_called_once()
    pipeline.multi.assert_called_once()
    assert pipeline.rpop.call_count == 2
    pipeline.execute.assert_called_once()


def test_enqueue_dict_data(mock_redis_client):
    """
    Test enqueue correctly serializes dict data and pushes it to Redis.
    """
    queue = MessageQueue(client=mock_redis_client)
    task_data = {"task": "process"}

    queue.enqueue(task_data)

    serialized_data = json.dumps(task_data)
    mock_redis_client.lpush.assert_called_once_with(queue.queue_name, serialized_data)
