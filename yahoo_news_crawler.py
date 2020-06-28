import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import time
import csv
import pymongo
from datetime import datetime

option = webdriver.ChromeOptions()
option.add_argument('headless')
driver = webdriver.Chrome(chrome_options=option)

client = pymongo.MongoClient()
db = client['yahoo_news']


def pagination_handler(pagination, t_content):
    page_url = []
    next_lis = pagination[0].find_all('li', {'class': 'pagination_item'})
    for li in next_lis[2:-1]:
        page_url.append('https://news.yahoo.co.jp' + li.a['href'])
        next_page = requests.get('https://news.yahoo.co.jp' + li.a['href'])
        next_soup = BeautifulSoup(next_page.text, 'html.parser')
        next_content = next_soup.find_all(class_='yjDirectSLinkTarget')
        if next_content:
            for next_part in next_content:
                t_content += next_part.get_text()
    return t_content


def comments_pagination(comment_soup, url, collection):
    comments = []
    comment_list = comment_soup.find_all(class_='commentListItem')
    for comment_item in comment_list:
        _comments = {'news': url}
        if comment_item.has_attr('pos'):
            _comments['comment_id'] = comment_item['id']
            comment_p = comment_item.find_all('span', {'class': 'cmtBody'})
            if comment_p:
                _comments['content'] = comment_p[0].get_text()
                votes = comment_item.find_all('div', {'class': 'emotion_vote'})
                for vote in votes:
                    option_ = vote.parent['class']
                    if option_ and (option_[0] == 'good' or option_[0] == 'bad'):
                        vote_num = vote.find_all('span', {'class': 'userNum'})[0].get_text()
                        _comments[option_[0]] = vote_num
                # comments.append(_comments)
                _comments['crawled_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                collection.update_one({'news': _comments['news'], 'comment_id': _comments['comment_id']},
                                      {'$set': _comments}, upsert=True)
    return comments


def comments_handler(comments, url):
    collection = db['comments']
    comment_url = comments[0]['href']
    driver.get(comment_url)
    time.sleep(3)
    driver.switch_to.frame("news-cmt")
    comment_soup = BeautifulSoup(driver.page_source, 'html.parser')
    comments = comments_pagination(comment_soup, url, collection)
    while True:
        page_ul = comment_soup.find_all('ul', {'class': 'pagenation'})
        if page_ul:
            page_li = page_ul[0].find_all('li', {'class': 'next'})[0]
            if page_li and page_li.find_all('a'):
                next_href = page_li.a['href']
                driver.get(next_href)
                time.sleep(3)
                driver.switch_to.frame("news-cmt")
                comment_soup = BeautifulSoup(driver.page_source, 'html.parser')
                comments += comments_pagination(comment_soup, url, collection)
            else:
                break
        else:
            break
    # collection.insert_many(comments)
    # return comments


def main(news_soup):
    collection = db['news']
    news_list = news_soup.find_all(class_='newsFeed_item')
    for news in news_list:
        news_title_div = news.find_all(class_='newsFeed_item_title')
        if news_title_div:
            url = news.a['href']
            news_page = requests.get(url)
            news_soup = BeautifulSoup(news_page.text, 'html.parser')
            if news_soup.find_all(class_='pickupMain_detailLink'):
                result['url'] = news_soup.find_all(class_='pickupMain_detailLink')[0].a['href']
                # use selenium to load comment
                # detail_html = requests.get(result['url'])
                driver.get(result['url'])
                js = "var q=document.documentElement.scrollTop=document.body.scrollHeight"
                driver.execute_script(js)
                time.sleep(3)
                detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
                driver.switch_to.frame("news-cmt")
                iframe = BeautifulSoup(driver.page_source, 'html.parser')
                title = detail_soup.body.article.h1.get_text()
                result['title'] = title
                if title:
                    contents = detail_soup.find_all(class_='yjDirectSLinkTarget')
                    if contents:
                        temp_content = ''
                        pagination = detail_soup.find_all(class_='pagination_items')
                        comments = iframe.find_all('a', {'id': 'loadMoreComments'})
                        next_temp_content = ''
                        if pagination:
                            next_temp_content = pagination_handler(pagination, next_temp_content)
                        for part in contents:
                            temp_content += part.get_text()
                        temp_content += next_temp_content
                        result['content'] = temp_content
                        result['crawled_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        time_p = detail_soup.find_all('time')[0].get_text().replace("\n", "")
                        result['created_at'] = time_p
                        collection.update_one({'url': result['url']}, {'$set': result}, upsert=True)
                        # _comments = {}
                        if comments:
                            # result['comments'] = comments_handler(comments)
                            comments_handler(comments, result['url'])
                        # with open("./yahoo_international_news.tsv", "w+", encoding="utf-8") as f:
                        #     writer = csv.writer(f, delimiter="\t")
                        #     writer.writerow([result['url'], result['title'], result['content'], result['comments']])
                        # print(result)


if __name__ == '__main__':
    base_url = "https://news.yahoo.co.jp/topics/world"
    html = requests.get(base_url)

    soup = BeautifulSoup(html.text, 'html.parser')
    result = {}
    main(soup)
    while True:
        _page_ul = soup.find_all('ul', {'class': 'pagination_items'})
        if _page_ul:
            _page_li = _page_ul[0].find_all('li', {'class': 'pagination_item-next'})[0]
            if _page_li and _page_li.find_all('a'):
                _next_href = "https://news.yahoo.co.jp" + _page_li.a['href']
                soup = BeautifulSoup(requests.get(_next_href).text, 'html.parser')
                main(soup)
            else:
                break
        else:
            break
