import os
import re

import MeCab
import jieba
import paramiko
import pymongo
from scp import SCPClient
from wordcloud import WordCloud

stopwords = {"a", "about", "above", "after", "again", "against", "all", "also", "am", "an", "and", "any", "are",
             "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
             "can", "can't", "cannot", "com", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing",
             "don't", "down", "during", "each", "else", "ever", "few", "for", "from", "further", "get", "had", "hadn't",
             "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "hence", "her", "here",
             "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "however", "http", "i", "i'd",
             "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "just", "k",
             "let's", "like", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on",
             "once", "only", "or", "other", "otherwise", "ought", "our", "ours", "ourselves", "out", "over", "own", "r",
             "same", "shall", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "since", "so", "some",
             "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
             "there's", "therefore", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those",
             "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're",
             "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while",
             "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "www", "you", "you'd",
             "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves", "user", "url", "http", "amp", "-"}

m = MeCab.Tagger("-Owakati")


def cut_data(text, lang):
    cut_text_list = []

    for row in text:
        if lang == "en":
            cut_text_list = text
        elif lang == "zh":
            cut_text_list.append(" ".join(jieba.cut(row)))
        elif lang == "ja":
            cut_text_list.append(m.parse(row))
    return " ".join(cut_text_list)


def word_cloud(data, lang, current):
    if data:
        cut_text = cut_data(data, lang)
        stop_words = set(stopwords)
        if lang in ["zh", "ja"]:
            stop_words = set(map(str.strip, open(f"/home/gao/project/WordCloud/{lang}_stopwords.txt", "r",
                                                 encoding="utf-8").read().split("\n")))

        cloud = WordCloud(
            font_path="/home/gao/project/WordCloud/msyh.ttf",
            stopwords=stop_words,
            background_color='white',
            max_words=2000,
            max_font_size=5000,
            width=1000, height=860, margin=2
        )
        wordcloud = cloud.generate(cut_text)
        filename = f"/home/gao/project/WordCloud/daily_word_cloud/{lang}/{current}_{lang}.jpg"
        wordcloud.to_file(filename)
        return filename


def upload_img(filename, lang, remote_path="/home/gao/go/src/WordCloud/static/img/"):
    host = "163.221.132.124"
    port = 22  # 端口号
    username = "gao"
    password = "520jerry"

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh_client.connect(host, port, username, password)
    remote_path = remote_path + lang
    with SCPClient(ssh_client.get_transport(), socket_timeout=30.0) as scp_client:
        try:
            scp_client.put(filename, remote_path)
        except Exception as e:
            print(e)


def main(lang, current_date, previous_date):
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--date", type=str, required=True)
    # arg = parser.parse_args()
    # print(arg.date)

    # previous_2_days = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=2)).strftime("%Y-%m-%d")
    # previous_1_day = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    start = previous_date.strftime("%Y-%m-%d")
    end = current_date.strftime("%Y-%m-%d")

    client = pymongo.MongoClient()
    database = client['wuhan_pneumonia']
    # langs = ['twitter_en', 'twitter_ja', 'weibo_zh']

    keywords = {
        "en": ["Wuhan", "pneumonia", "coronavirus", "COVID19", "COVID-19", "COVID 19", "COVID"],
        "ja": ["武漢", "肺炎", "コロナ", "COVID19", "COVID-19", "COVID 19", "COVID"],
        "zh": ["武汉", "肺炎", "冠状病毒", "新冠肺炎"]
    }

    # for lang in langs:
    language = lang[-2:]
    os.makedirs(f'/home/gao/project/WordCloud/daily_word_cloud/{language}', mode=0o755, exist_ok=True)
    data = []
    collection = database[lang]
    # cursor = collection.find({"created_at": {"$gte": previous_2_days, "$lte": previous_1_day}})
    cursor = collection.find({"created_at": {"$gte": start, "$lte": end}})
    for doc in cursor:
        url_regex = r"(https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]"
        comment = re.sub(url_regex, "url", doc['text'], 0, re.IGNORECASE)
        for keyword in keywords[language]:
            comment = re.sub(keyword, "", comment, 0, re.IGNORECASE)
        data.append(comment)
    filename = word_cloud(data, language, start)
    if filename:
        upload_img(filename, language)
