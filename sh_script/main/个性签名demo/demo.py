#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:demo.py
   @author:zl
   @time: 2025/4/28 17:01
   @software:PyCharm
   @desc:
"""
import io

import requests
import bs4
from PIL import Image
session = requests.session()
data = {
    'word': '朱亮',
    'fonts': 'zql.ttf',
    'size': 60,
    'fontcolor': '#000000',
}
url = 'https://www.uustv.com/'
post = session.post(url, data, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'})
print(post.text)
soup = bs4.BeautifulSoup(post.text, 'html.parser')
img_ = soup.find('div', class_='tu').img.attrs.get('src')
print(img_)
res = session.get(url + img_).content
print(res)
with open('res.gif', 'wb') as w:
    w.write(res)
