1. install ngrok

    you can follow this [https://ngrok.com/]()

2. Configure the ngrok installation

    ngrok config add-authtoken <your-auth-token-here>

3. expose your local port to the web

    ngrok http http://localhost:8080 #make sure to use the same port you use in api


4. run the api

    uvicorn src.app:app --host 0.0.0.0 --port 8080 --reload

Now every time a channel you had subscripbed upload or update a new video, you will be notified. More info here [Subscribe to Push Notifications](https://developers.google.com/youtube/v3/guides/push_notifications)
