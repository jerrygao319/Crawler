#%%
from urllib.request import urlopen
html = urlopen(
    "https://github.com/jerry0319/Crawl"
    ).read().decode("utf-8")
print(html)

#%%
