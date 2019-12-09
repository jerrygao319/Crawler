import tweepy
import os
import argparse
import logging
import time
import csv
from datetime import datetime
from configparser import RawConfigParser


class Tweet(object):
    def __init__(self, tweet_object_json):
        self.created_at = tweet_object_json['created_at']
        self.id = tweet_object_json['id']
        self.id_str = tweet_object_json['id_str']
        self.text = tweet_object_json['text']

        self.source = tweet_object_json['source'] if 'source' in tweet_object_json else None

        self.truncated = tweet_object_json['truncated'] if 'truncated' in tweet_object_json else False

        self.in_reply_to_status_id = tweet_object_json[
            'in_relpy_to_status_id'] if 'in_relpy_to_status_id' in tweet_object_json else False

        self.in_reply_to_status_id_string = tweet_object_json[
            'in_relpy_to_status_id_string'] if 'in_relpy_to_status_id_string' in tweet_object_json else None

        self.in_reply_to_user_id = tweet_object_json[
            'in_relpy_to_user_id'] if 'in_relpy_to_user_id' in tweet_object_json else None

        self.in_reply_to_screen_name = tweet_object_json[
            'in_relpy_to_screen_name'] if 'in_relpy_to_screen_name' in tweet_object_json else None

        self.user = tweet_object_json['user']['id_str'] if 'user' in tweet_object_json else None

        self.coordinates = tweet_object_json['coordinates'] if 'coordinates' in tweet_object_json else None

        self.place = tweet_object_json['place'] if 'place' in tweet_object_json else None

        self.quoted_status_str = tweet_object_json[
            'quoted_status_id_str'] if 'is_quoted_status' in tweet_object_json else None

        self.retweeted_status = tweet_object_json[
            'retweeted_status'] if "retweeted_status" in tweet_object_json else False

        self.quoted_count = tweet_object_json['quoted_count'] if 'quoted_count' in tweet_object_json else None

        self.retweet_count = tweet_object_json['retweet_count'] if 'retweet_count' in tweet_object_json else None

        self.reply_count = tweet_object_json['reply_count'] if 'reply_count' in tweet_object_json else None

        self.favorite_count = tweet_object_json['favorite_count'] if 'favorite_count' in tweet_object_json else None

        self.entities = tweet_object_json['entities'] if 'entities' in tweet_object_json else None

        #        if "extended_entities" in tweet_object_json:
        #            self.extended_entities = tweet_object_json['extended_entities']

        self.retweeted = tweet_object_json['retweeted'] if 'retweeted' in tweet_object_json else False

        self.possibly_sensitive = tweet_object_json[
            'possibly_sensitive'] if 'possibly_sensitive' in tweet_object_json else False

        self.lang = tweet_object_json['lang'] if 'lang' in tweet_object_json else None


def save_to_file(tweet):
    with open("tweets_" + now_date + ".csv", "a+") as f:
        writer = csv.writer(f)
        writer.writerow(tweet)


def main_process(args):
    # authentication info
    app_key = raw_cfg.get("Authentication", "app_key")
    app_secret = raw_cfg.get("Authentication", "app_secret")
    access_token = raw_cfg.get("Authentication", "access_token")
    access_token_secret = raw_cfg.get("Authentication", "access_token_secret")

    # parameters
    lang = args.lang
    keywords = raw_cfg.get("Parameters", "keywords_" + lang)
    # date_since = raw_cfg.defaults()["since"]
    count = raw_cfg.getint("Parameters", "count")

    auth = tweepy.OAuthHandler(app_key, app_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    max_tweets = raw_cfg.getint("Parameters", "max")
    searched_tweets = []
    last_id = -1
    rate_limit_window = raw_cfg.getint("Parameters", "rate_limit_window")
    while len(searched_tweets) < max_tweets:
        try:
            tweets = api.search(q=keywords, lang=lang, count=count,max_id=str(last_id - 1))
            if not tweets:
                logger.error("NO tweet found. Language: " + lang + "Query: [" + keywords + "]")
            searched_tweets.append(tweets)
            last_id = tweets[-1].id
        except tweepy.RateLimitError as rle:
            logger.debug("Rate Limited!")
            time.sleep(rate_limit_window * 60)
            searched_tweets = []
            last_id = -1

        except tweepy.TweepError as te:
            logger.exception(te)

        else:
            for tweet in tweets:
                if (not tweet.retweeted) and ('RT @' not in tweet.text):
                    save_to_file(tweet)


if __name__ == "__main__":
    # initial config parser
    raw_cfg = RawConfigParser()
    raw_cfg.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), "", "config.ini"))

    # initial log
    now_date = datetime.now().strftime('%y%m%d')
    log_path = raw_cfg.get("Parameters", "log_path")
    os.makedirs(log_path, exist_ok=True)
    log_filename = log_path + "tweet_" + now_date + ".log"
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        handlers=[logging.FileHandler(log_filename, encoding="utf-8")])

    logger = logging.getLogger(__name__)

    # initial arguments parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", type=str, default='en')
    _args = parser.parse_args()

    main_process(_args)
