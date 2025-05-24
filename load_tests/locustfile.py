import uuid

from faker import Faker
from locust import HttpUser, between, task

fake = Faker()

class ApiUser(HttpUser):
    wait_time = between(1, 2)  # Wait between requests (simulate user think time)

    @task
    def post_xml_payload(self):
        fake_video_id = str(uuid.uuid4())[:11]  # YouTube video IDs are typically 11 chars
        fake_title = fake.sentence(nb_words=6)  # Generate a fake title with ~6 words

        payload = f"""<?xml version='1.0' encoding='UTF-8'?>
        <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <yt:videoId>{fake_video_id}</yt:videoId>
                <yt:channelId>UC9DuzJTFrLCna-DRLV8sZwg</yt:channelId>
                <title>{fake_title}</title>
                <link rel="alternate" href="https://www.youtube.com/watch?v={fake_video_id}"/>
                <author>
                    <name>Maike Rodrigo</name>
                </author>
                <published>2025-05-11T17:00:34+00:00</published>
                <updated>2025-05-24T15:50:55.820073346+00:00</updated>
            </entry>
        </feed>"""
        headers = {'Content-Type': 'application/xml'}
        self.client.post("/webhooks", data=payload, headers=headers)
