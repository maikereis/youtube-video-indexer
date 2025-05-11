# %%
%load_ext autoreload
%autoreload 2

import requests
import os
from dotenv import load_dotenv, find_dotenv

# %%
load_dotenv(find_dotenv(".env"), override=True)

# %%
NGROK_CALLBACK_URL = os.getenv("NGROK_CALLBACK_URL")
HUB_URL = "https://pubsubhubbub.appspot.com/subscribe"

# %%
channels = [
    {"name": "ByteByteGo", "id": "UCZgt6AzoyjslHTC9dz0UoTw"},
    {"name": "IBM Technology", "id": "UCKWaEZ-_VweaEx1j62do_vQ"},
    {"name": "Sebastian Rashka", "id": "UC_CzsS7UTjcxJ-xXp1ftxtA"},
    {"name": "FreeCodeCamp.org", "id": "UC8butISFwT-Wl7EV0hUK0BQ"},
    {"name": "suspicious.joblib", "id": "UC9DuzJTFrLCna-DRLV8sZwg"},
]

# %%
for channel in channels:
    channel_name = channel["name"]
    channel_id = channel["id"]
    topic_url = "https://www.youtube.com/xml/feeds/videos.xml?channel_id=" + channel_id

    data = {
        "hub.mode": "subscribe",
        "hub.topic": topic_url,
        "hub.callback": NGROK_CALLBACK_URL,
        "hub.verify": "async",
    }

    response = requests.post(HUB_URL, data=data)

    if response.status_code == 202:
        print(f"Successfully subscribed to {channel_name} (id: {channel_id})")
    else:
        print(f"Failed to subscribe to {channel_name} (id: {channel_id})")


