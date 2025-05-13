import json
from unittest.mock import MagicMock, patch

import pytest

from ytindexer.queue import NotificationQueue


@pytest.fixture
def mock_valkey():
    with patch("ytindexer.queue.valkey.Valkey") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


def test_enqueue_dict(mock_valkey):
    queue = NotificationQueue(queue_name="test-queue")
    data = {"event": "video_uploaded", "video_id": 123}

    queue.enqueue(data)

    expected_data = json.dumps(data)
    mock_valkey.lpush.assert_called_once_with("test-queue", expected_data)


def test_enqueue_string(mock_valkey):
    queue = NotificationQueue(queue_name="test-queue")
    data = "plain text task"

    queue.enqueue(data)

    mock_valkey.lpush.assert_called_once_with("test-queue", data)


def test_dequeue_json(mock_valkey):
    queue = NotificationQueue(queue_name="test-queue")
    data = {"task": "notify", "id": 1}
    encoded = json.dumps(data).encode("utf-8")
    mock_valkey.brpop.return_value = ("test-queue", encoded)

    result = queue.dequeue()

    assert result == data


def test_dequeue_plain_text(mock_valkey):
    queue = NotificationQueue(queue_name="test-queue")
    data = b"not a json string"
    mock_valkey.brpop.return_value = ("test-queue", data)

    result = queue.dequeue()

    assert result == data


def test_dequeue_empty(mock_valkey):
    queue = NotificationQueue(queue_name="test-queue")
    mock_valkey.brpop.return_value = None

    result = queue.dequeue()

    assert result is None
