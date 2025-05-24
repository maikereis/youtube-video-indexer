import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ytindexer.worker import YouTubeNotificationProcessor, YouTubeNotificationParser  # adjust import accordingly


@pytest.fixture
def mock_parser():
    parser = MagicMock()
    return parser


@pytest.fixture
def mock_notification_queue():
    queue = MagicMock()
    return queue


@pytest.fixture
def mock_output_queue():
    queue = MagicMock()
    return queue


@pytest.mark.asyncio
async def test_process_notification_success(mock_parser, mock_notification_queue, mock_output_queue):
    xml_data = "<xml>some data</xml>"
    expected_metadata = {"video_id": "123"}
    mock_parser.parse.return_value = expected_metadata

    processor = YouTubeNotificationProcessor(
        notification_queue=mock_notification_queue,
        output_queue=mock_output_queue,
        parser=mock_parser
    )

    result = await processor.process_notification(xml_data)
    mock_parser.parse.assert_called_once_with(xml_data)
    assert result == expected_metadata


@pytest.mark.asyncio
async def test_process_notification_parse_returns_none(mock_parser, mock_notification_queue, mock_output_queue):
    mock_parser.parse.return_value = None

    processor = YouTubeNotificationProcessor(
        notification_queue=mock_notification_queue,
        output_queue=mock_output_queue,
        parser=mock_parser
    )

    result = await processor.process_notification("<xml>data</xml>")
    assert result is None


@pytest.mark.asyncio
async def test_process_notification_parse_raises_exception(mock_parser, mock_notification_queue, mock_output_queue):
    mock_parser.parse.side_effect = Exception("parse error")

    processor = YouTubeNotificationProcessor(
        notification_queue=mock_notification_queue,
        output_queue=mock_output_queue,
        parser=mock_parser
    )

    result = await processor.process_notification("<xml>data</xml>")
    assert result is None


@pytest.mark.asyncio
async def test_process_batch_success_and_failure(mock_parser, mock_notification_queue, mock_output_queue):
    notifications = ["n1", "n2", "n3"]
    # Simulate dequeues return values
    mock_notification_queue.dequeue.side_effect = notifications + [None]

    # Simulate parser returns: first succeeds, second fails (exception), third returns None
    async def side_effect_process_notification(xml):
        if xml == "n1":
            return {"id": 1}
        if xml == "n2":
            raise Exception("fail")
        if xml == "n3":
            return None

    processor = YouTubeNotificationProcessor(
        notification_queue=mock_notification_queue,
        output_queue=mock_output_queue,
        parser=mock_parser
    )

    # Patch process_notification to our side effect version
    processor.process_notification = AsyncMock(side_effect=side_effect_process_notification)

    processed_count = await processor.process_batch(batch_size=5)

    # Only one successful processing returns metadata and is enqueued
    assert processed_count == 1
    mock_output_queue.enqueue.assert_called_once_with({"id": 1})


@pytest.mark.asyncio
async def test_run_processes_when_queue_not_empty(mock_parser, mock_notification_queue, mock_output_queue):
    processor = YouTubeNotificationProcessor(
        notification_queue=mock_notification_queue,
        output_queue=mock_output_queue,
        parser=mock_parser
    )

    mock_notification_queue.queue_size.side_effect = [1, 0]
    processor.process_batch = AsyncMock(return_value=1)

    # Patch sleep to avoid actually sleeping
    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        # Run processor with a short loop - break after first loop for test
        async def shutdown_soon():
            await asyncio.sleep(0)  # yield control
            processor.shutdown()
        asyncio.create_task(shutdown_soon())

        await processor.run(poll_interval=0.01)

    processor.process_batch.assert_called()
    mock_sleep.assert_called()


@pytest.mark.asyncio
async def test_shutdown_sets_event(mock_parser, mock_notification_queue, mock_output_queue):
    processor = YouTubeNotificationProcessor(
        notification_queue=mock_notification_queue,
        output_queue=mock_output_queue,
        parser=mock_parser
    )
    assert not processor._shutdown_event.is_set()
    processor.shutdown()
    assert processor._shutdown_event.is_set()

@pytest.mark.asyncio
async def test_process_notification_with_realistic_xml(mock_notification_queue, mock_output_queue):
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom"
          xmlns:yt="http://www.youtube.com/xml/schemas/2015">
      <entry>
        <yt:videoId>abc123XYZ</yt:videoId>
        <yt:channelId>channel789</yt:channelId>
        <title>Test Video Title</title>
        <published>2023-05-01T12:00:00Z</published>
        <updated>2023-05-01T12:10:00Z</updated>
        <link rel="alternate" href="https://www.youtube.com/watch?v=abc123XYZ"/>
        <author>
          <name>Test Channel</name>
        </author>
      </entry>
    </feed>"""

    # Use the real parser here (not a mock)
    parser = YouTubeNotificationParser()

    # Create processor with real parser and mock queues
    processor = YouTubeNotificationProcessor(
        notification_queue=mock_notification_queue,
        output_queue=mock_output_queue,
        parser=parser
    )

    result = await processor.process_notification(xml_data)

    # Assert the parsed result is a YouTubeNotification object with expected fields
    assert result is not None
    assert hasattr(result, 'video_id')
    assert result.video_id == "abc123XYZ"
    assert result.channel_id == "channel789"
    assert result.title == "Test Video Title"
    assert str(result.link) == "https://www.youtube.com/watch?v=abc123XYZ"
    assert result.author == "Test Channel"
    # published and updated are datetime objects
    assert hasattr(result.published, "isoformat")
    assert hasattr(result.updated, "isoformat")

    # Simulate enqueue call
    mock_output_queue.enqueue = MagicMock()

    # Manually enqueue the result (simulate process_batch behavior)
    mock_output_queue.enqueue(result)
    mock_output_queue.enqueue.assert_called_once_with(result)