#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:demo1.py
   @author:zl
   @time: 2025/5/6 10:19
   @software:PyCharm
   @desc:
"""

from PIL import Image

im = Image.open('images/xiaoai.jpg')
print(im.format, im.size, im.mode)
ysize = int(500 / im.size[0] * im.size[1])
im = im.resize((500, ysize))

# im = im.rotate(45)
# 转置
# im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
# im = im.transpose(Image.Transpose.ROTATE_90)
sizex, sizey = 50, int(ysize/ 10)
times = int((500 - sizex) / (sizex * 2))
im2 = Image.open('images/xiaoai.jpg')
for i in range(times):
    box = (sizex * i, sizey * i, 500 - sizex * i, ysize - sizey * i)
    region = im2.resize((500 - sizex * i * 2, ysize - sizey * i * 2))
    # region = im.crop(box)
    # region = region.transpose(Image.Transpose.ROTATE_90)
    im.paste(region, box)
im.save('look.png')
