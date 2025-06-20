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

im = Image.open('images/demo.png')
print(im.format, im.size, im.mode)
im = im.resize((500, 500))
# im = im.rotate(45)
# 转置
# im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
# im = im.transpose(Image.Transpose.ROTATE_90)
box = (100,100,400,400)
region = im.crop(box)
region = region.transpose(Image.Transpose.ROTATE_90)
im.paste(region, box)
im.save('look.png')