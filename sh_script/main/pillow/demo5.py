#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:demo5.py
   @author:zl
   @time: 2025/5/16 17:25
   @software:PyCharm
   @desc:
"""
from PIL import Image

im = Image.open('images/3.gif')
print(im.n_frames)
for i in range(1, im.n_frames, 20):
    print(i)
    im.seek(i)
    im.save(f'images/gif/{i}.png')
