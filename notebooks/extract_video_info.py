# %%
import os
import json
import requests
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# %%
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_URL = os.getenv("GOOGLE_API_URL")

# %%
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Video:
    id: str
    title: str
    url: str
    description: str
    published_at: datetime


@dataclass
class Channel:
    id: str
    name: str
    videos: list[Video] = None

    def __post_init__(self):
        self.videos = []

    def add_video(self, video: Video):
        self.videos.append(video)

# %%
channels = [
    {"name": "ByteByteGo", "id": "UCZgt6AzoyjslHTC9dz0UoTw"},
    {"name": "IBM Technology", "id": "UCKWaEZ-_VweaEx1j62do_vQ"},
    {"name": "Sebastian Rashka", "id": "UC_CzsS7UTjcxJ-xXp1ftxtA"},
    {"name": "FreeCodeCamp.org", "id": "UC8butISFwT-Wl7EV0hUK0BQ"},
]

channel_list = [Channel(**channel) for channel in channels]

# %%
channel_list

# %%
for channel in channel_list:
    skip = False

    params = {
        "key": GOOGLE_API_KEY,
        "channelId": channel.id,
        "part": ["snippet", "id"],
        "order": "date",
        "maxResults": 50,
        "pageToken": None,
    }

    while not skip:
        response = requests.get(GOOGLE_API_URL, params=params)
        data = response.json()

        if "items" in data:
            for item in data["items"]:
                if item["id"]["kind"] == "youtube#video":
                    video_id = item["id"]["videoId"]
                    video_title = item["snippet"]["title"]
                    video_description = item["snippet"]["description"]
                    video_published_at = item["snippet"]["publishTime"]
                    video_url = f"https://www.youtube.com/watch?v={video_id}"

                    try:
                        video_published_at = datetime.strptime(
                            item["snippet"]["publishTime"], "%Y-%m-%dT%H:%M:%SZ"
                        )
                    except ValueError:
                        video_published_at = None

                    video = Video(
                        id=video_id,
                        title=video_title,
                        url=video_url,
                        description=video_description,
                        published_at=video_published_at,
                    )

                    channel.add_video(video)

        if "nextPageToken" not in data:
            skip = True
        else:
            params["pageToken"] = data.get("nextPageToken")

# %%
def convert_channels_pandas(channel: Channel):
    df = pd.DataFrame.from_dict(channel.videos)
    df.loc[:, "channel"] = channel.name
    df.loc[:, "channel_id"] = channel.id
    return df

# %%
data = []

for channel in channel_list:
    channel_df = convert_channels_pandas(channel)
    data.append(channel_df)

data = pd.concat(data, ignore_index=True)

# %%
data.to_parquet("../data/videos-info.parquet", index=False)


