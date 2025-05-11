# %%
import time
import pandas as pd
from dataclasses import dataclass

from xml.parsers.expat import ExpatError

from youtube_transcript_api import YouTubeTranscriptApi as YTTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound

# %%
data = pd.read_parquet("../data/videos-info.parquet")

# %%
@dataclass
class Transcript:
    id: str
    title: str
    text: str

# %%
def extract_video_transcript(video_id: str, languages: list = ["en", "en-US"]) -> str:
    try:
        transcript = YTTranscriptApi.get_transcript(video_id, languages=languages)
        text = " ".join([t["text"] for t in transcript])
        return text
    except NoTranscriptFound as e:
        print(f"No transcript found for {video_id}: {e}")
    except TypeError as e:
        print(f"TypeError for {video_id}: {e}")
    except ExpatError as e:
        print(f"ExpatError for {video_id}: {e}")
    except Exception as e:
        print(f"Unexpected error for {video_id}: {e}")
        pass
    return None

# %%
transcripts = []

for row in data[["id", "title"]].itertuples(index=False):
    time.sleep(0.5)  # To avoid hitting the API too fast
    transcript = extract_video_transcript(row.id)
    transcripts.append(Transcript(row.id, row.title, transcript))

# %%
pd.DataFrame(transcripts).to_parquet(
    "../data/transcripts.parquet",
    index=False,
    engine="pyarrow",
    compression="snappy",
)


