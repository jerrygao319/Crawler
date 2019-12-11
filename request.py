import requests
import http.cookiejar as cookie_lib
import os
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) " \
             "Chrome/78.0.3904.108 Safari/537.36 "
HEADER = {
    "Host": "subjregist.naist.jp",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "Rerferer": "https://subjregist.naist.jp/",
    "User-agent": USER_AGENT
}
ACCOUNT = "zhiwei-g"
PASSWORD = "Jerry520"
naist_session = requests.session()
naist_session.cookies = cookie_lib.LWPCookieJar(filename="naist_cookies.txt")


def login(account, password):
    print("login start..")
    post_url = "https://subjregist.naist.jp/users/login"
    post_data = {
        "_method": "POST",
        "data[User][account]": account,
        "data[User][password]": password
    }
    response_res = naist_session.post(post_url, data=post_data, headers=HEADER, )
    print(f"statusCode = {response_res.status_code}")
    naist_session.cookies.save()
    return response_res


def is_login_status():
    route_url = "https://subjregist.naist.jp/schedules/preview_monthly"
    response_res = naist_session.get(route_url, headers=HEADER, allow_redirects=False)
    print(f"isLoginStatus = {response_res.status_code}")
    if response_res.status_code != 200:
        return False
    else:
        return True


if __name__ == "__main__":
    if not os.path.exists("naist_cookies.txt"):
        with open("naist_cookies.txt", "w+") as f:
            line = f.readline()
            if not line or line != "#LWP-Cookies-2.0\n":
                f.write("#LWP-Cookies-2.0\n")
        f.close()
    naist_session.cookies.load()
    # is_login = is_login_status()
    # print(f"is login naist = {is_login}")
    if not False:
        # print("re-login..")
        response = login(ACCOUNT, PASSWORD)
        print(response.text)
        # resp = naist_session.get("https://subjregist.naist.jp/schedules/preview_monthly", headers=HEADER,
        #                         allow_redirects=False)
        # print(naist_session.cookies)
        # print(f"resp.status = {resp.status_code}")



