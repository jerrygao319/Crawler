import requests
from bs4 import BeautifulSoup

url = "https://twitter.com/search?q=%23KillAllNiggers&src=typed_query"
re = requests.get(url)
soup = BeautifulSoup(re.content, 'lxml')
print(soup.prettify())
