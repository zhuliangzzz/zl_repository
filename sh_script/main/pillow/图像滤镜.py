#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:图像滤镜.py
   @author:zl
   @time: 2025/5/24 16:54
   @software:PyCharm
   @desc:
"""
from PIL import Image, ImageFilter

im = Image.open('images/demo.png')

# im.filter(ImageFilter.BLUR)
im.show()
# rotate_image = im.rotate(90) # 旋转
# rotate_image.show()
# im_transpose = im.transpose(Image.FLIP_LEFT_RIGHT) # 翻转
# im_transpose.show()
# # 图像滤镜
# im_filter = im.filter(ImageFilter.BLUR)  # 模糊
# im_filter.show()
# im_filter = im.filter(ImageFilter.SHARPEN)  # 锐化
# im_filter.show()
# im_filter = im.filter(ImageFilter.EDGE_ENHANCE)  # 边缘增强
# im_filter.show()
im_filter = im.filter(ImageFilter.FIND_EDGES)
im_filter.show()
