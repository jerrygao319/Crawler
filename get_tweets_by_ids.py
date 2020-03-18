import tweepy
import csv
import argparse
import os
import index
import time
import logging
from datetime import datetime, timedelta
from index import Tweet

token = {
    "app_key": "pxtScDDWdQWnAu8UVAuPc2HHL",
    "app_secret": "Ipv3LCFO23veDVy8WyfcMcOSCeadjEcLVSVX0B4XTJhjqm78Ya",
    "access_token": "1014405726884642816-F3UOrYtJoEQkpHLZFvKvAdl2fiavEN",
    "access_token_secret": "o5FoeM9Tg72ZLrQG5HChRIgaAzAMpQBXvRrhFuz36eH37"
}
tweet_attributes = ["created_at", "id_str", "text", "source", "user", "username", "name", "coordinates", "place",
                    "is_quote_status", "quoted_status", "retweet_count", "favorite_count", "possibly_sensitive", "lang",
                    "entities-urls", "in_reply_to_status_id_str", "in_reply_to_screen_name", "reply_text"]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default='./COVID-19-TweetIDs/2020-03/')
    parser.add_argument("--start", type=str, default='2020-03-05')
    parser.add_argument("--end", type=str, default='2020-03-12')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        handlers=[logging.FileHandler("./log/get_id.log", encoding="utf-8")])
    logger = logging.getLogger(__name__)

    auth = tweepy.OAuthHandler(token["app_key"], token["app_secret"])
    auth.set_access_token(token["access_token"], token["access_token_secret"])
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
                        for line in f:
                            if line.endswith("\n"):
                                line = line[:-1]
                            try:
                                status = api.get_status(line, tweet_mode='extended')
                            except tweepy.RateLimitError:
                                logger.error("Rate Limited!")
                                time.sleep(15 * 60)
                            except tweepy.TweepError as te:
                                print(f"get [{line}] error: {str(te)}")
                                logger.error(f"get [{line}] error: {str(te)}")
                            except Exception as e:
                                logger.error(f"get {line} error: {str(e)}")

                            tweet = Tweet(status)
                            data = index.filter_attribute(tweet, tweet_attributes)
                            writer.writerow(data)
                            total += 1
                    logger.debug(f"{file} total: {total}")
        start_date = start_date + timedelta(days=1)



