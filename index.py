import tweepy
import os
import argparse
import logging
import time
import csv
from datetime import datetime, timedelta
from configparser import ConfigParser
import pymongo
from pymongo.errors import DuplicateKeyError


class Tweet(object):
    def __init__(self, tweet_object_json):
        self.created_at = tweet_object_json.created_at.strftime("%Y-%m-%d %H:%M:%S")
        self.id = tweet_object_json.id
        self.id_str = tweet_object_json.id_str
        self.text = tweet_object_json.full_text if hasattr(tweet_object_json,
                                                           "full_text") and tweet_object_json.full_text else tweet_object_json.text

        self.source = tweet_object_json.source if tweet_object_json.source else None
        self.truncated = tweet_object_json.truncated if tweet_object_json.truncated else False
        self.in_reply_to_status_id = tweet_object_json.in_reply_to_status_id if hasattr(tweet_object_json,
                                                                                        "in_reply_to_status_id") and tweet_object_json.in_reply_to_status_id else False
        self.in_reply_to_status_id_str = tweet_object_json.in_reply_to_status_id_str if hasattr(tweet_object_json,
                                                                                                "in_reply_to_status_id_str") and tweet_object_json.in_reply_to_status_id_str else None
        self.in_reply_to_user_id = tweet_object_json.in_reply_to_user_id if hasattr(tweet_object_json,
                                                                                    "in_reply_to_user_id") and tweet_object_json.in_reply_to_user_id else None
        self.in_reply_to_user_id_str = tweet_object_json.in_reply_to_user_id_str if hasattr(tweet_object_json,
                                                                                            "in_reply_to_user_id_str") and tweet_object_json.in_reply_to_user_id_str else None
        self.in_reply_to_screen_name = tweet_object_json.in_reply_to_screen_name if hasattr(tweet_object_json,
                                                                                            "in_reply_to_screen_name") and tweet_object_json.in_reply_to_screen_name else None
        self.user = tweet_object_json.user.id_str if tweet_object_json.user else None
        self.name = tweet_object_json.user.name if tweet_object_json.user else None
        self.username = tweet_object_json.user.screen_name if tweet_object_json.user else None
        self.coordinates = tweet_object_json.coordinates if tweet_object_json.coordinates else None
        self.place = tweet_object_json.place.full_name + ", " + tweet_object_json.place.country if hasattr(
            tweet_object_json, "place") and tweet_object_json.place else None
        self.quoted_status_id_str = tweet_object_json.quoted_status_id_str if hasattr(tweet_object_json,
                                                                                      "is_quoted_status") and tweet_object_json.is_quoted_status else None
        self.quoted_count = tweet_object_json.quoted_count if hasattr(tweet_object_json,
                                                                      "quoted_count") and tweet_object_json.quoted_count else None
        self.retweet_count = tweet_object_json.retweet_count if hasattr(tweet_object_json,
                                                                        "retweet_count") and tweet_object_json.retweet_count else None
        self.favorite_count = tweet_object_json.favorite_count if hasattr(tweet_object_json,
                                                                          "favorite_count") and tweet_object_json.favorite_count else None
        self.entities = tweet_object_json.entities if tweet_object_json.entities else None

        #        if "extended_entities" in tweet_object_json:
        #            self.extended_entities = tweet_object_json['extended_entities']

        self.retweeted = tweet_object_json.retweeted if hasattr(tweet_object_json,
                                                                "retweeted") and tweet_object_json.retweeted else False
        self.possibly_sensitive = tweet_object_json.possibly_sensitive if hasattr(tweet_object_json,
                                                                                  "possibly_sensitive") and tweet_object_json.possibly_sensitive else False
        self.lang = tweet_object_json.lang if hasattr(tweet_object_json, "lang") and tweet_object_json.lang else None


def add_reply(tweet, reply):
    if reply:
        tweet.reply_text = reply.full_text if hasattr(reply, "full_text") and reply.full_text else reply.text


def filter_attribute(tweet, tweet_attributes):
    data = []
    for attr in tweet_attributes:
        if hasattr(tweet, attr):
            data += [tweet.__getattribute__(attr)]
    return data


def filter_attribute_to_dict(tweet, tweet_attributes):
    data = {}
    for attr in tweet_attributes:
        data[attr] = tweet.__getattribute__(attr) if hasattr(tweet, attr) else ""
    data['crawled_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return data


def search_replies(tweet, api):
    try:
        status = api.get_status(tweet.in_reply_to_status_id_str, tweet_mode='extended')
        return status
    except:
        return


def init_mongodb():
    global dao
    server = raw_cfg.get("Database", "server")
    port = raw_cfg.getint("Database", "port")
    database = raw_cfg.get("Database", "database")
    if dao is None:
        client = pymongo.MongoClient(host=server, port=port)
        dao = client[database]


def insert_records(data, language):
    collection = dao["twitter_" + language]
    try:
        print(data['id_str'])
        return collection.insert_one(data)
    except DuplicateKeyError:
        if "_id" in data:
            del data["_id"]
        collection.update_one({'id_str': data['id_str']}, {'$set': data}, upsert=True)
        return


def main_process(args):
    # authentication info
    app_key = raw_cfg.get("Authentication", "app_key")
    app_secret = raw_cfg.get("Authentication", "app_secret")
    access_token = raw_cfg.get("Authentication", "access_token")
    access_token_secret = raw_cfg.get("Authentication", "access_token_secret")

    # parameters
    lang = args.lang
    keywords = raw_cfg.get("Parameters", "keywords_" + lang)
    count = raw_cfg.getint("Parameters", "count")
    now_str = datetime.now().strftime("%Y-%m-%d")
    if not args.range:
        date_range = raw_cfg.getint("Parameters", "date_range")
        from_date_str = (datetime.now() - timedelta(date_range)).strftime("%Y-%m-%d")
        keywords += " since:" + from_date_str + " until:" + now_str
    if not args.retweet:
        keywords += " -filter:retweets"

    auth = tweepy.OAuthHandler(app_key, app_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    max_tweets = raw_cfg.getint("Parameters", "max_number")
    last_id = -1
    rate_limit_window = raw_cfg.getint("Parameters", "rate_limit_window")
    file_path = raw_cfg.get("Parameters", "file_path")
    tweet_attributes = raw_cfg.get("Parameters", "tweet_attributes").split(",")
    tweet_count = 0
    total = 0
    os.makedirs(file_path, 777, exist_ok=True)

    output_file_name = raw_cfg.get("Parameters", "output_file")
    if output_file_name == 'pneumonia':
        init_mongodb()
    with open(file_path + output_file_name + "_" + lang + "_" + now_date + ".csv", "w+", encoding="utf-8") as f:
        try:
            writer = csv.writer(f)
            writer.writerow(tweet_attributes)

            while tweet_count < max_tweets:
                try:
                    if args.range:
                        tweets = api.search(q=keywords, lang=lang, count=count, max_id=str(last_id - 1), until=now_str,
                                            tweet_mode="extended")
                    else:
                        tweets = api.search(q=keywords, lang=lang, count=count, max_id=str(last_id - 1),
                                            tweet_mode="extended")
                    if not tweets:
                        logger.error("NO tweet found. Language: " + lang + " and Query: [" + keywords + "]")
                        break
                    last_id = tweets[-1].id
                    tweet_count += len(tweets)
                except tweepy.RateLimitError:
                    logger.debug("Rate Limited!")
                    time.sleep(rate_limit_window * 60)

                except tweepy.TweepError as te:
                    logger.exception(te)

                else:
                    for tweet in tweets:
                        tweet_text = tweet.full_text if hasattr(tweet, "full_text") and tweet.full_text else tweet.text
                        if (not tweet.retweeted) and ('RT @' not in tweet_text):
                            tweet = Tweet(tweet)
                            # search for replies
                            if tweet.in_reply_to_status_id and tweet.in_reply_to_user_id:
                                replies_for = search_replies(tweet, api)
                                add_reply(tweet, replies_for)
                            if output_file_name == 'vaccine':
                                data = filter_attribute(tweet, tweet_attributes)
                                writer.writerow(data)
                                total += 1
                            elif output_file_name == 'pneumonia':
                                tweet_dict = filter_attribute_to_dict(tweet, tweet_attributes)
                                result = insert_records(tweet_dict, args.lang)
                                if result:
                                    total += 1
                    # print("Write " + str(len(tweets)) + " tweets successful.")
            print("Total: " + str(total) + " <" + lang + "> tweets.")
        except Exception as e:
            logger.exception(e)


if __name__ == "__main__":
    # initial config parser
    raw_cfg = ConfigParser()
    raw_cfg.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), "", "config.ini"), encoding="utf-8")

    # initial log
    now_date = datetime.now().strftime('%y%m%d')
    log_path = raw_cfg.get("Parameters", "log_path")
    os.makedirs(log_path, 777, exist_ok=True)
    log_filename = log_path + "tweet_" + now_date + ".log"
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        handlers=[logging.FileHandler(log_filename, encoding="utf-8")])

    logger = logging.getLogger(__name__)

    # initial arguments parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", type=str, default='en')
    parser.add_argument("--retweet", type=bool, default=False,
                        help="True from including retweets and False for excluding retweets")
    parser.add_argument("--range", type=bool, default=False,
                        help="Date range. From (Today - Range) to Today")
    _args = parser.parse_args()

    dao = None
    main_process(_args)
