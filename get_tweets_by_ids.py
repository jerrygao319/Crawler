import tweepy
import csv
import argparse
import os
import index
import time
import logging
from datetime import datetime, timedelta
from index import Tweet
from configparser import ConfigParser

tweet_attributes = ["created_at", "id_str", "text", "source", "user", "username", "name", "coordinates", "place",
                    "is_quote_status", "quoted_status", "retweet_count", "favorite_count", "possibly_sensitive", "lang",
                    "entities-urls", "in_reply_to_status_id_str", "in_reply_to_screen_name", "reply_text"]


if __name__ == '__main__':
    raw_cfg = ConfigParser()
    raw_cfg.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), "", "config.ini"), encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default='./COVID-19-TweetIDs/2020-03/')
    parser.add_argument("--start", type=str, default='2020-03-05')
    parser.add_argument("--end", type=str, default='2020-03-12')
    parser.add_argument("--index", type=int, default=3)
    args = parser.parse_args()

    logging.basicConfig(level=logging.ERROR, format="%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        handlers=[logging.FileHandler("./log/covid19_tweetIDs.log", encoding="utf-8")])
    logger = logging.getLogger(__name__)

    app_key = raw_cfg.get(f"Authentication{args.index}", "app_key")
    app_secret = raw_cfg.get(f"Authentication{args.index}", "app_secret")
    access_token = raw_cfg.get(f"Authentication{args.index}", "access_token")
    access_token_secret = raw_cfg.get(f"Authentication{args.index}", "access_token_secret")

    auth = tweepy.OAuthHandler(app_key, app_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    file_path = args.path
    start = args.start
    end = args.end
    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    files = sorted(os.listdir(file_path))
    while start_date <= end_date:
        now_date = datetime.strftime(start_date, "%Y-%m-%d")
        with open(f"./covid19_tweets/convid19_tweets_{now_date}.csv", "w+", encoding="utf-8") as w:
            writer = csv.writer(w)
            writer.writerow(tweet_attributes)
            total = 0
            for file in files:
                if file.find(now_date) > -1:
                    with open(f"{file_path}/{file}", "r", encoding="utf-8") as f:
                        tweet_ids = [line[:-1] if line.endswith("\n") else line for line in
                                     map(str.strip, f.readlines())]
                        tweets_count = len(tweet_ids)
                        for i in range((tweets_count // 100) + 1):
                            end_loc = min((i + 1) * 100, tweets_count)
                            ids = tweet_ids[i * 100:end_loc]
                            try:
                                status_list = api.statuses_lookup(ids, tweet_mode='extended', include_entities=True)
                            except tweepy.RateLimitError:
                                logger.error("Rate limited!")
                                time.sleep(15 * 60)
                            except tweepy.TweepError as te:
                                print(f"get [{ids}] from [{file}] error: {te}")
                                logger.error(f"get [{ids}] from [{file}] error: {te}")

                            get_ids = []
                            for status in status_list:
                                tweet = Tweet(status)
                                get_ids.append(tweet.id_str)
                                data = index.filter_attribute(tweet, tweet_attributes)
                                writer.writerow(data)
                            miss_ids = list(set(ids) - set(get_ids))
                            if len(miss_ids) > 0:
                                logger.error(f"cannot get {miss_ids} from [{file}] ")
        start_date = start_date + timedelta(days=1)
