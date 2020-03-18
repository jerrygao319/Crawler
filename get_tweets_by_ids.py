import tweepy
import csv
import argparse
import os
import index
import time
import logging
from index import Tweet

token = {
    "app_key": "uagoLmOuTfI0HHa3xVQT9Jk5j",
    "app_secret": "NDstogaWFIcnY6sj6bVCmP33cjr7MyClGEqyzJvQODz96f7wjl",
    "access_token": "1014405726884642816-G9fqYuJBPWgVykd7MKDgYkrbnGC9DJ",
    "access_token_secret": "R9VCK2SL7e7cELz0XwzDyTJtjdoDEK5pV2NIWErYtckml"
}
tweet_attributes = ["created_at", "id_str", "text", "source", "user", "username", "name", "coordinates", "place",
                    "is_quote_status", "quoted_status", "retweet_count", "favorite_count", "possibly_sensitive", "lang",
                    "entities-urls", "in_reply_to_status_id_str", "in_reply_to_screen_name", "reply_text"]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default='./COVID-19-TweetIDs/2020-03/')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        handlers=[logging.FileHandler("./log/get_id.log", encoding="utf-8")])
    logger = logging.getLogger(__name__)

    auth = tweepy.OAuthHandler(token["app_key"], token["app_secret"])
    auth.set_access_token(token["access_token"], token["access_token_secret"])
    api = tweepy.API(auth)

    file_path = args.path
    with open("convid19_tweets.csv", "w+", encoding="utf-8") as w:
        writer = csv.writer(w)
        writer.writerow(tweet_attributes)
        for file in os.listdir(file_path):
            total = 0
            with open(f"{file_path}/{file}", "r", encoding="utf-8") as f:
                for line in f:
                    if line.endswith("\n"):
                        line = line[:-1]
                    try:
                        status = api.get_status(line, tweet_mode='extended')
                    except tweepy.RateLimitError:
                        logger.error("Rate Limited!")
                        time.sleep(15 * 60)
                    except tweepy.TweepError as te:
                        logger.error(f"get [{line}] error: {str(te)}")
                    except Exception as e:
                        logger.error(f"get {line} error: {str(e)}")
                    tweet = Tweet(status)
                    data = index.filter_attribute(tweet, tweet_attributes)
                    writer.writerow(data)
                    total += 1
            logger.debug(f"{file} total: {total}")



