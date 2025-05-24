import pytest
from datetime import datetime, timezone
from ytindexer.worker.parser import YouTubeNotificationParser, YouTubeNotification

# Sample valid XML notification
VALID_XML = """
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:yt="http://www.youtube.com/xml/schemas/2015">
  <entry>
    <yt:videoId>abc123</yt:videoId>
    <yt:channelId>channel456</yt:channelId>
    <title>Test Video</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc123"/>
    <author>
      <name>Test Channel</name>
    </author>
    <published>2025-05-23T12:00:00Z</published>
    <updated>2025-05-23T12:30:00Z</updated>
  </entry>
</feed>
"""

# Sample XML missing the videoId
MISSING_VIDEO_ID_XML = """
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:yt="http://www.youtube.com/xml/schemas/2015">
  <entry>
    <yt:channelId>channel456</yt:channelId>
    <title>Test Video</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc123"/>
    <author>
      <name>Test Channel</name>
    </author>
    <published>2025-05-23T12:00:00Z</published>
    <updated>2025-05-23T12:30:00Z</updated>
  </entry>
</feed>
"""

# Sample malformed XML
MALFORMED_XML = "<feed><entry><yt:videoId>abc123</yt:videoId></entry>"

def test_parse_valid_notification():
    """Test parsing of a valid YouTube notification XML."""
    result = YouTubeNotificationParser.parse(VALID_XML)
    assert result is not None
    assert isinstance(result, YouTubeNotification)
    assert result.video_id == "abc123"
    assert result.channel_id == "channel456"
    assert result.title == "Test Video"
    assert str(result.link) == "https://www.youtube.com/watch?v=abc123"
    assert result.author == "Test Channel"
    assert result.published == datetime(2025, 5, 23, 12, 0, 0, tzinfo=timezone.utc)
    assert result.updated == datetime(2025, 5, 23, 12, 30, 0, tzinfo=timezone.utc)
    assert result.source == "pubsubhubbub"
    assert isinstance(result.processed_at, datetime)

def test_parse_missing_video_id():
    """Test parsing of XML missing the videoId."""
    result = YouTubeNotificationParser.parse(MISSING_VIDEO_ID_XML)
    assert result is None

def test_parse_malformed_xml():
    """Test parsing of malformed XML."""
    result = YouTubeNotificationParser.parse(MALFORMED_XML)
    assert result is None
