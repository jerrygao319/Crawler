import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import time
import pymongo
from datetime import datetime
import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchFrameException

option = webdriver.ChromeOptions()
# When set to none Selenium WebDriver only waits until the initial page is downloaded.
option.page_load_strategy = 'none'
option.add_argument("enable-automation")
option.add_argument("--headless")
option.add_argument("--no-sandbox")
option.add_argument("--disable-extensions")
option.add_argument("--dns-prefetch-disable")
option.add_argument("--disable-gpu")
option.add_argument('--disable-dev-shm-usage')
option.add_argument('start-maximize')
option.add_argument('--disable-browser-side-navigation')
option.add_argument('--disable-infobars')


driver = webdriver.Chrome(options=option)
# driver.set_page_load_timeout(10)
# driver.set_script_timeout(10)

client = pymongo.MongoClient()
db = client['yahoo_news']

wait = WebDriverWait(driver, 30)


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


def save_comments(comment_soup, url, collection):
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
    wait.until(EC.presence_of_element_located((By.NAME, 'news-cmt')))
    driver.execute_script(js)
    time.sleep(3)
    if BeautifulSoup(driver.page_source, 'html.parser').find_all('iframe', {'name': 'news-cmt'}):
        driver.switch_to.frame('news-cmt')
        comment_soup = BeautifulSoup(driver.page_source, 'html.parser')
        _comments = save_comments(comment_soup, url, collection)
        page_li = comment_soup.find_all('li', {'class': 'next'})
        while page_li and page_li[0].find_all('a'):
            next_href = page_li[0].a['href']
            if next_href:
                try:
                    driver.get(next_href)
                    wait.until(EC.presence_of_element_located((By.NAME, 'news-cmt')))
                    driver.execute_script(js)
                    time.sleep(3)
                    if BeautifulSoup(driver.page_source, 'html.parser').find_all('iframe', {'name': 'news-cmt'}):
                        driver.switch_to.frame('news-cmt')
                        comment_soup = BeautifulSoup(driver.page_source, 'html.parser')
                        _comments += save_comments(comment_soup, url, collection)
                        page_li = comment_soup.find_all('li', {'class': 'next'})
                except TimeoutException as e0:
                    logger.exception(next_href, e0)
                    driver.get(next_href)
                    wait.until(EC.presence_of_element_located((By.NAME, 'news-cmt')))
                    continue
                except NoSuchFrameException as e2:
                    logger.exception(next_href, e2)
                    driver.refresh()
                    wait.until(EC.presence_of_element_located((By.NAME, 'news-cmt')))
                    continue
                except Exception as e1:
                    logger.exception(f"next:{next_href}", e1)
            else:
                break

        # while True:
        #     page_ul = comment_soup.find_all('ul', {'class': 'pagenation'})
        #     if page_ul:
        #         page_li = page_ul[0].find_all('li', {'class': 'next'})[0]
        #         if page_li and page_li.find_all('a'):
        #             next_href = page_li.a['href']
        #             if next_href:
        #                 try:
        #                     driver.get(next_href)
        #                     wait.until(EC.presence_of_element_located((By.NAME, 'news-cmt')))
        #                     driver.execute_script(js)
        #                     time.sleep(5)
        #                     if BeautifulSoup(driver.page_source, 'html.parser').find_all('iframe', {'name': 'news-cmt'}):
        #                         driver.switch_to.frame('news-cmt')
        #                         comment_soup = BeautifulSoup(driver.page_source, 'html.parser')
        #                         _comments += save_comments(comment_soup, url, collection)
        #                 except TimeoutException as e0:
        #                     logging.exception(next_href, e0)
        #                     driver.refresh()
        #                     continue
        #                 except NoSuchFrameException as e2:
        #                     logging.exception(next_href, e2)
        #                     driver.refresh()
        #                     continue
        #                 except Exception as e1:
        #                     logging.exception(f"next:{next_href}", e1)
        #             else:
        #                 break
        #         else:
        #             break
        #     else:
        #         break
    # collection.insert_many(comments)
        return _comments


def main(news_soup, result):
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
                try:
                    # use selenium to load comment
                    # detail_html = requests.get(result['url'])
                    driver.get(result['url'])
                    wait.until(EC.title_contains('Yahoo!ニュース'))
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
                            has_comments = detail_soup.find_all('iframe', {'name': 'news-cmt'})
                            try:
                                comments = ''
                                if has_comments:
                                    driver.switch_to.frame('news-cmt')
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
                                # result['comments'] = comments_handler(comments)
                                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} start collecting comments from {result['url']}")
                                result['comments'] = comments_handler(comments, result['url']) if comments else ''
                                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} end collecting comments, total comments: {len(result['comments'])}")
                                collection.update_one({'url': result['url']}, {'$set': result}, upsert=True)
                            except NoSuchFrameException as e2:
                                logger.exception(result['url'], e2)
                            except Exception as e1:
                                logger.exception(result['url'], e1)
                except TimeoutException as e0:
                    logger.exception(result['url'], e0)
                    driver.get(result['url'])
                    wait.until(EC.title_contains('Yahoo!ニュース'))
                except Exception as e:
                    logger.exception(result['url'], e)


def main_process(base_url):
    html = requests.get(base_url)

    soup = BeautifulSoup(html.text, 'html.parser')
    result = {}
    main(soup, result)


if __name__ == '__main__':
    js = "var q=document.documentElement.scrollTop=document.body.scrollHeight"
    logging.basicConfig(level=logging.ERROR, format="%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        handlers=[logging.FileHandler("./yahoo_log/yahoo_news.log", encoding="utf-8")])
    logger = logging.getLogger(__name__)
    base_url = 'https://news.yahoo.co.jp/topics/world'

    try:
        main_process(base_url)
        main_process(base_url + '?page=2')
        main_process(base_url + '?page=3')
    finally:
        driver.close()

    # while True:
    #     try:
    #         _page_ul = soup.find_all('ul', {'class': 'pagination_items'})
    #         if _page_ul:
    #             _page_li = _page_ul[0].find_all('li', {'class': 'pagination_item-next'})[0]
    #             if _page_li and _page_li.find_all('a'):
    #                 if _page_li.a['href']:
    #                     _next_href = "https://news.yahoo.co.jp" + _page_li.a['href']
    #                     soup = BeautifulSoup(requests.get(_next_href).text, 'html.parser')
    #                     main(soup)
    #                 else:
    #                     break
    #             else:
    #                 break
    #         else:
    #             break
    #     except TimeoutException as e0:
    #         print("time out")
    #         logging.exception(e0)
    #         driver.refresh()
    #         continue
    #     except NoSuchFrameException as e2:
    #         logging.exception(e2)
    #         driver.refresh()
    #         continue
    #     except Exception as e:
    #         logging.exception(e)
    #         break
