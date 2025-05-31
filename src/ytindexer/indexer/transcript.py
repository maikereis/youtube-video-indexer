"""Service for downloading and processing YouTube video transcripts."""

from typing import Dict, List, Optional

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from ytindexer.logging import logger


class VideoTranscriptService:
    """Downloads and formats YouTube video transcripts with multiple language support."""

    def __init__(self, languages: Optional[List[str]] = None):
        """
        Initialize the transcript service.

        Args:
            languages: Preferred languages in order of preference.
                      Defaults to ['en', 'en-US'] if not provided.
        """
        if languages is None:
            languages = ["en", "en-US"]
        self.languages = languages
        self.formatter = TextFormatter()

    def get_transcript(self, video_id: str) -> Optional[str]:
        """
        Download and format transcript for a YouTube video.

        Args:
            video_id: YouTube video ID

        Returns:
            Formatted transcript text or None if unavailable
        """
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try preferred languages first
            for language in self.languages:
                try:
                    transcript = transcript_list.find_transcript([language])
                    transcript_data = transcript.fetch()
                    return self.formatter.format_transcript(transcript_data)
                except Exception:
                    continue

            # Fallback to generated English transcript
            try:
                transcript = transcript_list.find_generated_transcript(["en"])
                transcript_data = transcript.fetch()
                return self.formatter.format_transcript(transcript_data)
            except Exception:
                # Last resort: use any available transcript
                available_transcripts = list(transcript_list)
                if available_transcripts:
                    transcript_data = available_transcripts[0].fetch()
                    return self.formatter.format_transcript(transcript_data)

        except Exception as e:
            logger.error(f"Failed to get transcript for video {video_id}: {e}")
            return None

    def get_transcript_with_timestamps(self, video_id: str) -> Optional[List[Dict]]:
        """
        Get transcript with timing information for each segment.

        Args:
            video_id: YouTube video ID

        Returns:
            List of transcript segments with 'text', 'start', 'duration' keys,
            or None if transcript unavailable
        """
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try preferred languages first
            for language in self.languages:
                try:
                    transcript = transcript_list.find_transcript([language])
                    return transcript.fetch()
                except Exception:
                    continue

            # Fallback to generated English transcript
            try:
                transcript = transcript_list.find_generated_transcript(["en"])
                return transcript.fetch()
            except Exception:
                # Last resort: use any available transcript
                available_transcripts = list(transcript_list)
                if available_transcripts:
                    return available_transcripts[0].fetch()

        except Exception as e:
            logger.error(
                f"Failed to get timestamped transcript for video {video_id}: {e}"
            )
        return None
