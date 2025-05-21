import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, Optional
from ytindexer.logging import logger

class YouTubeNotificationParser:
    """
    Responsible for parsing YouTube PubSubHubbub notification XML
    """

    namespaces = {
        'xmlns': 'http://www.w3.org/2005/Atom',
        'yt': 'http://www.youtube.com/xml/schemas/2015'
    }

    @staticmethod
    def parse(xml_data: str) -> Optional[Dict[str, Any]]:
        try:
            root = ET.fromstring(xml_data)
            entry = root.find('xmlns:entry', YouTubeNotificationParser.namespaces)
            if entry is None:
                logger.warning("No entry found in notification XML")
                return None

            video_id_elem = entry.find("yt:videoId", YouTubeNotificationParser.namespaces)
            if video_id_elem is None or not video_id_elem.text:
                logger.warning("Could not extract video ID from notification")
                return None
            video_id = video_id_elem.text

            channel_id_elem = entry.find("yt:channelId", YouTubeNotificationParser.namespaces)
            title_elem = entry.find("xmlns:title", YouTubeNotificationParser.namespaces)
            published_at_elem = entry.find("xmlns:published", YouTubeNotificationParser.namespaces)
            updated_at_elem = entry.find("xmlns:updated", YouTubeNotificationParser.namespaces)
            link_elem = entry.find('xmlns:link', YouTubeNotificationParser.namespaces)
            author_elem = entry.find('./xmlns:author/xmlns:name', YouTubeNotificationParser.namespaces)

            metadata = {
                "video_id": video_id,
                "channel_id": channel_id_elem.text if channel_id_elem is not None else None,
                "title": title_elem.text if title_elem is not None else None,
                "published": published_at_elem.text if published_at_elem is not None else None,
                "updated": updated_at_elem.text if updated_at_elem is not None else None,
                "link": link_elem.get('href') if link_elem is not None else None,
                "author": author_elem.text if author_elem is not None else None,
                "processed_at": datetime.utcnow().isoformat(),
                "source": "pubsubhubbub"
            }
            return metadata

        except Exception as e:
            logger.error(f"Failed to parse notification XML: {str(e)}")
            logger.debug(f"Notification data: {xml_data}")
            return None
