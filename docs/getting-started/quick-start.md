### Basic Usage

First you will need to ingest a video metada. Here i will create a post method to simulate a notification received from [ByteByteGo](https://www.youtube.com/@ByteByteGo) youtube channel

```python
import requests

channel_id = "UCZgt6AzoyjslHTC9dz0UoTw"  # Use the channel ID you desire to ingest content
video_id = "2g1G8Jr88xU" # A video ID of a video from the channel you select
title = "System Design Was HARD - Until You Knew the Trade-Offs, Part 2" # The video title

payload = f"""<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
    <entry>
        <yt:videoId>{video_id}</yt:videoId>
        <yt:channelId>{channel_id}</yt:channelId>
        <title>{title}</title>
        <link rel="alternate" href="https://www.youtube.com/watch?v={video_id}"/>
        <author>
            <name>ByteByteGo</name>
        </author>
        <published>2025-05-11T17:00:34+00:00</published>
        <updated>2025-05-24T15:50:55.820073346+00:00</updated>
    </entry>
</feed>"""

headers = {'Content-Type': 'application/xml'}

url = "http://localhost:8080/webhooks"  # Replace with your webhook URL, if you use NGrok it will be like: "https://<random stuff>.ngrok-free.app/webhooks"

response = requests.post(url, data=payload, headers=headers)

print(f"Status Code: {response.status_code}")
print(f"Response Text: {response.text}")
```

Now we can query the indexed videos:

```python
import requests

# Search for videos
response = requests.get('http://localhost:8080/api/v1/videos', {
    'query': 'System Design',
    'limit': 10
})

videos = response.json()
print(f"Found {len(videos)} videos")
print(videos["results"][0])
```