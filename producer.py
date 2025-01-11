import praw
import json
import time
from kafka import KafkaProducer
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve variables
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
user_agent = os.getenv("USER_AGENT")


# Initialize Reddit client
reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=user_agent
)

producer = KafkaProducer(bootstrap_servers=["localhost:9092"], 
                               value_serializer=lambda v: json.dumps(v).encode("utf-8"))
topic = "reddit_topic"


def get_data():
    """
    This function streams comments from the dataengineeringjobs subreddit and sends them
    to the kafka topic "redditstream". The function will continue to run until it is
    manually stopped. The function will print each comment to the console and wait
    for 30 seconds before checking for the next comment.

    :return: None
    """
    try:

        subreddit = reddit.subreddit("dataengineeringjobs")
        for comment in subreddit.stream.comments():
            data = {
                "id": comment.id,
                "body": comment.body,
                "author": comment.author.name,
                "subreddit": comment.subreddit.display_name
            }
            producer.send(topic, data)
            producer.flush()
            print("**"*100)
            print(f" Comment: {data}") # Print the comment body (comment.body)
            time.sleep(10)  
    except Exception as e:
        print(f"An error occurred: {e}")

get_data()
    