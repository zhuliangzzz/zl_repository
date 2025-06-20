#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:demo4.py
   @author:zl
   @time: 2025/5/9 17:01
   @software:PyCharm
   @desc:
"""
from PIL import Image, ImageEnhance


im2 = Image.open('images/shuang.jpg')
# print(im.mode, im.size)
im = Image.open('images/demo.png')
# im.thumbnail((100, 100))
# print(im.mode, im.size)
# im.show()
# if im.width > im2.width:
#     width, height = im.width, int(im2.height * (im.width/im2.width))
#     im2 = im2.resize((width, height))
# else:
#     width, height = im2.width, int(im.height * (im2.width / im.width))
#     im = im.resize((width, height))
# new_im = Image.new('RGB', (im.width, im.height + im2.height))
# new_im.paste(im, (0,0))
# new_im.paste(im2, (0,im.height))
# new_im.show()


# 亮度
enhance_brightness = ImageEnhance.Brightness(im)
enhance = enhance_brightness.enhance()
enhance.show()
# 对比度
# enhance_brightness = ImageEnhance.Contrast(im)
# enhance = enhance_brightness.enhance(1.5)
# enhance.show()