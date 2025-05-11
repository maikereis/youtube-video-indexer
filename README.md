Youtube Index

Youtube Video --> Transcript --> Embeddings

The embeddings are then used in a semantic search pipeline to recommend the best videos given a user query 

To register a push notification listener

1. Install ngrok 

    You can follow this [https://ngrok.com/]() 

2. Configure the ngrok installation

    ngrok config add-authtoken <your-auth-token-here>

3. Expose your local port to the web 

    ngrok http http://localhost:8080 #make sure to use the same port you use in api


4. run the api

    uvicorn src.app:app --host 0.0.0.0 --port 8080 --reload

For batch processing, run the  


Every time a channel you subscribe to uploads or updates a new video, you will be notified. More info here [Subscribe to Push Notifications](https://developers.google.com/youtube/v3/guides/push_notifications) 

The notification can further handled to extract video info like link, title, and the transcripts, that will be embedded