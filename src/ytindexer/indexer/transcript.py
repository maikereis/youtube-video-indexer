# -*- coding: utf-8 -*-
"""Service for downloading and processing YouTube video transcripts."""

from typing import Dict, List, Optional

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    VideoUnavailable,
    NoTranscriptFound,
    CouldNotRetrieveTranscript,
)

from ytindexer.logging import logger


class VideoTranscriptService:
    """Downloads YouTube video transcripts with multiple language support"""

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
        if not video_id or not video_id.strip():
            logger.error("Empty or invalid video ID provided")
            return None

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try preferred languages first
            for language in self.languages:
                try:
                    transcript = transcript_list.find_transcript([language])
                    transcript_data = transcript.fetch()
                    formatted_text = self.formatter.format_transcript(transcript_data)
                    logger.info(
                        f"Successfully retrieved transcript for {video_id} in {language}"
                    )
                    return formatted_text
                except NoTranscriptFound:
                    logger.debug(
                        f"No transcript found for {video_id} in language {language}"
                    )
                    continue
                except Exception as e:
                    logger.debug(
                        f"Error getting transcript in {language} for {video_id}: {e}"
                    )
                    continue

            # Fallback to generated English transcript
            try:
                transcript = transcript_list.find_generated_transcript(["en"])
                transcript_data = transcript.fetch()
                formatted_text = self.formatter.format_transcript(transcript_data)
                logger.info(
                    f"Successfully retrieved generated English transcript for {video_id}"
                )
                return formatted_text
            except NoTranscriptFound:
                logger.debug(f"No generated English transcript found for {video_id}")
            except Exception as e:
                logger.debug(f"Error getting generated transcript for {video_id}: {e}")

            # Last resort: use any available transcript
            try:
                available_transcripts = list(transcript_list)
                if available_transcripts:
                    first_transcript = available_transcripts[0]
                    transcript_data = first_transcript.fetch()
                    formatted_text = self.formatter.format_transcript(transcript_data)
                    logger.info(
                        f"Retrieved fallback transcript for {video_id} in {first_transcript.language}"
                    )
                    return formatted_text
                else:
                    logger.warning(f"No transcripts available for video {video_id}")
                    return None
            except Exception as e:
                logger.error(f"Error fetching fallback transcript for {video_id}: {e}")

        except TranscriptsDisabled:
            logger.warning(f"Transcripts are disabled for video {video_id}")
            return None
        except VideoUnavailable:
            logger.error(f"Video {video_id} is unavailable")
            return None
        except NoTranscriptFound:
            logger.warning(f"No transcripts available for video {video_id}")
            return None
        except CouldNotRetrieveTranscript as e:
            logger.error(f"Could not retrieve transcript for {video_id}: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error getting transcript for video {video_id}: {e}"
            )
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
        if not video_id or not video_id.strip():
            logger.error("Empty or invalid video ID provided")
            return None

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try preferred languages first
            for language in self.languages:
                try:
                    transcript = transcript_list.find_transcript([language])
                    transcript_data = transcript.fetch()
                    logger.info(
                        f"Successfully retrieved timestamped transcript for {video_id} in {language}"
                    )
                    return transcript_data
                except NoTranscriptFound:
                    logger.debug(
                        f"No transcript found for {video_id} in language {language}"
                    )
                    continue
                except Exception as e:
                    logger.debug(
                        f"Error getting timestamped transcript in {language} for {video_id}: {e}"
                    )
                    continue

            # Fallback to generated English transcript
            try:
                transcript = transcript_list.find_generated_transcript(["en"])
                transcript_data = transcript.fetch()
                logger.info(
                    f"Successfully retrieved generated English timestamped transcript for {video_id}"
                )
                return transcript_data
            except NoTranscriptFound:
                logger.debug(f"No generated English transcript found for {video_id}")
            except Exception as e:
                logger.debug(
                    f"Error getting generated timestamped transcript for {video_id}: {e}"
                )

            # Last resort: use any available transcript
            try:
                available_transcripts = list(transcript_list)
                if available_transcripts:
                    first_transcript = available_transcripts[0]
                    transcript_data = first_transcript.fetch()
                    logger.info(
                        f"Retrieved fallback timestamped transcript for {video_id} in {first_transcript.language}"
                    )
                    return transcript_data
                else:
                    logger.warning(f"No transcripts available for video {video_id}")
                    return None
            except Exception as e:
                logger.error(
                    f"Error fetching fallback timestamped transcript for {video_id}: {e}"
                )

        except TranscriptsDisabled:
            logger.warning(f"Transcripts are disabled for video {video_id}")
            return None
        except VideoUnavailable:
            logger.error(f"Video {video_id} is unavailable")
            return None
        except NoTranscriptFound:
            logger.warning(f"No transcripts available for video {video_id}")
            return None
        except CouldNotRetrieveTranscript as e:
            logger.error(
                f"Could not retrieve timestamped transcript for {video_id}: {e}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error getting timestamped transcript for video {video_id}: {e}"
            )
            return None
