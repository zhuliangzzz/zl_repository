#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:demo3.py
   @author:zl
   @time: 2025/5/6 16:48
   @software:PyCharm
   @desc:
"""
from PIL import Image
from PIL import ImageEnhance

im = Image.open('images/xiaoai.jpg')
# print(im.mode)
# im = im.convert('L')
# im.show()

# 拆分和合并频段
# r,g,b  = im.split()
# merge = Image.merge('RGB', (r, b, g))
# merge.show()
#
source = im.split()
R,G,B = 0,1,2
mask = source[R].point(lambda i: i < 100 and 255)
out = source[G].point(lambda i: i * 0.6)
source[G].paste(out,None, mask)

im = Image.merge(im.mode, source)
im.show()
# 增强
# contrast = ImageEnhance.Contrast(im)
# contrast.enhance(1.3).show('aaa')


