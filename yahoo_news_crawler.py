import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import time
import pymongo
from datetime import datetime
import logging
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchFrameException

option = webdriver.ChromeOptions()
option.add_argument("enable-automation")
option.add_argument("headless")
option.add_argument("no-sandbox")
option.add_argument("disable-extensions")
option.add_argument("dns-prefetch-disable")
option.add_argument("disable-gpu")

driver = webdriver.Chrome(options=option)
# driver.set_page_load_timeout(10)
# driver.set_script_timeout(10)

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
                _comments['crawled_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                collection.update_one({'news': _comments['news'], 'comment_id': _comments['comment_id']},
                                      {'$set': _comments}, upsert=True)
                comments.append(_comments['content'])
    return comments


def comments_handler(comments, url):
    collection = db['comments']
    comment_url = comments[0]['href']
    driver.get(comment_url)
    driver.execute_script(js)
    time.sleep(5)
    driver.switch_to.frame(driver.find_element_by_xpath("//iframe[contains(@name,'news-cmt')]"))
    comment_soup = BeautifulSoup(driver.page_source, 'html.parser')
    _comments = comments_pagination(comment_soup, url, collection)
    while True:
        page_ul = comment_soup.find_all('ul', {'class': 'pagenation'})
        if page_ul:
            page_li = page_ul[0].find_all('li', {'class': 'next'})[0]
            if page_li and page_li.find_all('a'):
                next_href = page_li.a['href']
                if next_href:
                    try:
                        driver.get(next_href)
                        driver.execute_script(js)
                        time.sleep(5)
                        driver.switch_to.frame(driver.find_element_by_xpath("//iframe[contains(@name,'news-cmt')]"))
                        comment_soup = BeautifulSoup(driver.page_source, 'html.parser')
                        _comments += comments_pagination(comment_soup, url, collection)
                    except TimeoutException as e0:
                        logging.exception(next_href, e0)
                        driver.refresh()
                        continue
                    except NoSuchFrameException as e2:
                        logging.exception(next_href, e2)
                        driver.refresh()
                        continue
                    except Exception as e1:
                        logging.exception(f"next:{next_href}", e1)
                else:
                    break
            else:
                break
        else:
            break
    # collection.insert_many(comments)
    return _comments


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
                driver.execute_script(js)
                time.sleep(5)
                detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
                title = detail_soup.body.article.h1.get_text()
                result['title'] = title
                if title:
                    contents = detail_soup.find_all(class_='yjDirectSLinkTarget')
                    if contents:
                        temp_content = ''
                        pagination = detail_soup.find_all(class_='pagination_items')
                        driver.switch_to.frame(driver.find_element_by_xpath("//iframe[contains(@name,'news-cmt')]"))
                        try:
                            iframe = BeautifulSoup(driver.page_source, 'html.parser')
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
                            # _comments = {}
                            if comments:
                                # result['comments'] = comments_handler(comments)
                                result['comments'] = comments_handler(comments, result['url'])
                            collection.update_one({'url': result['url']}, {'$set': result}, upsert=True)
                        except Exception as e1:
                            logging.exception(result['url'], e1)
                        # with open("./yahoo_international_news.tsv", "w+", encoding="utf-8") as f:
                        #     writer = csv.writer(f, delimiter="\t")
                        #     writer.writerow([result['url'], result['title'], result['content'], result['comments']])
                        # print(result)


if __name__ == '__main__':
    js = "var q=document.documentElement.scrollTop=document.body.scrollHeight"
    logging.basicConfig(level=logging.ERROR, format="%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        handlers=[logging.FileHandler("yahoo_news.log", encoding="utf-8")])

    base_url = "https://news.yahoo.co.jp/topics/world"
    html = requests.get(base_url)

    soup = BeautifulSoup(html.text, 'html.parser')
    result = {}
    main(soup)
    while True:
        try:
            _page_ul = soup.find_all('ul', {'class': 'pagination_items'})
            if _page_ul:
                _page_li = _page_ul[0].find_all('li', {'class': 'pagination_item-next'})[0]
                if _page_li and _page_li.find_all('a'):
                    if _page_li.a['href']:
                        _next_href = "https://news.yahoo.co.jp" + _page_li.a['href']
                        soup = BeautifulSoup(requests.get(_next_href).text, 'html.parser')
                        main(soup)
                    else:
                        break
                else:
                    break
            else:
                break
        except TimeoutException as e0:
            print("time out")
            logging.exception(e0)
            driver.refresh()
            continue
        except NoSuchFrameException as e2:
            logging.exception(e2)
            driver.refresh()
            continue
        except Exception as e:
            logging.exception(e)
            break
