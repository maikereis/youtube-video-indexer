import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, HttpUrl, field_validator

from ytindexer.logging import logger


class YouTubeNotification(BaseModel):
    """
    Represents a parsed YouTube PubSubHubbub notification.

    Attributes:
        video_id (str): Unique identifier of the video.
        channel_id (Optional[str]): Identifier of the channel.
        title (Optional[str]): Title of the video.
        published (Optional[datetime]): Datetime when the video was published.
        updated (Optional[datetime]): Datetime when the video metadata was updated.
        link (Optional[HttpUrl]): URL link to the video.
        author (Optional[str]): Author name of the video.
        processed_at (datetime): Timestamp when the notification was processed.
        source (str): Source of the notification, e.g., "pubsubhubbub".
    """

    video_id: str
    channel_id: Optional[str]
    title: Optional[str]
    published: Optional[datetime]
    updated: Optional[datetime]
    link: Optional[HttpUrl]
    author: Optional[str]
    processed_at: datetime
    source: str

    @field_validator("published", "updated", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        """
        Validate and parse datetime fields from string to datetime object.

        Args:
            v (str | datetime | None): Input value to parse.

        Returns:
            datetime | None: Parsed datetime object or None if parsing fails.
        """
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                pass
        return v


class YouTubeNotificationParser:
    """
    Parser for YouTube PubSubHubbub notification XML data.

    Attributes:
        namespaces (dict): XML namespaces used for parsing.
    """

    namespaces = {
        'xmlns': 'http://www.w3.org/2005/Atom',
        'yt': 'http://www.youtube.com/xml/schemas/2015'
    }

    @staticmethod
    def _find_text(entry: ET.Element, tag: str) -> Optional[str]:
        """
        Find text content for a given tag inside an XML element.

        Args:
            entry (ET.Element): XML element to search within.
            tag (str): Tag name to find.

        Returns:
            Optional[str]: Text content of the found element or None if not found.
        """
        elem = entry.find(tag, YouTubeNotificationParser.namespaces)
        return elem.text if elem is not None else None

    @staticmethod
    def _find_link(entry: ET.Element) -> Optional[str]:
        """
        Find the 'href' attribute from the link element inside the XML entry.

        Args:
            entry (ET.Element): XML element to search within.

        Returns:
            Optional[str]: URL string if found, otherwise None.
        """
        link_elem = entry.find('xmlns:link', YouTubeNotificationParser.namespaces)
        return link_elem.get('href') if link_elem is not None else None

    @staticmethod
    def parse(xml_data: str) -> Optional[YouTubeNotification]:
        """
        Parse YouTube PubSubHubbub notification XML string into a YouTubeNotification model.

        Args:
            xml_data (str): XML string of the notification.

        Returns:
            Optional[YouTubeNotification]: Parsed notification object or None if parsing fails.
        """
        try:
            root = ET.fromstring(xml_data)
            entry = root.find('xmlns:entry', YouTubeNotificationParser.namespaces)
            if entry is None:
                logger.warning("No entry found in notification XML")
                return None

            video_id = YouTubeNotificationParser._find_text(entry, "yt:videoId")
            if not video_id:
                logger.warning("Missing video ID in notification")
                return None

            notification = YouTubeNotification(
                video_id=video_id,
                channel_id=YouTubeNotificationParser._find_text(entry, "yt:channelId"),
                title=YouTubeNotificationParser._find_text(entry, "xmlns:title"),
                published=YouTubeNotificationParser._find_text(entry, "xmlns:published"),
                updated=YouTubeNotificationParser._find_text(entry, "xmlns:updated"),
                link=YouTubeNotificationParser._find_link(entry),
                author=YouTubeNotificationParser._find_text(entry, './xmlns:author/xmlns:name'),
                processed_at=datetime.now(timezone.utc),
                source="pubsubhubbub"
            )
            return notification

        except Exception as e:
            logger.error(f"Failed to parse notification XML: {e}")
            logger.debug(f"Notification data: {xml_data}")
            return None
