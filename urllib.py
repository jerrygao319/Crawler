#%%
from urllib.request import urlopen
html = urlopen(
    "http://localhost:8888/tree"
    ).read().decode("utf-8")
print(html)

#%%
import re
title = re.findall(r"<head>(.*?)</head>", html, flags=re.DOTALL)
print(title)
#%%
