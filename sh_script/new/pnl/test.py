#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:test.py
   @author:zl
   @time: 2025/3/3 11:45
   @software:PyCharm
   @desc:
"""
import jieba as j
import wordcloud as wc
import imageio
with open('test2.txt', 'r', encoding='utf-8') as r: # 读取test2.txt中的文本作为词云源文本内容
    txt = r.read()
text_cut = ' '.join(j.lcut(txt))
mask = imageio.v2.imread('bg.png')  # 背景形状图，设置mask参数，以该参数设置的图形生成词云形状 该图片需要透明背景的图形  mask默认为矩形
cloud = wc.WordCloud(background_color='black', font_path='msyh.ttc', max_font_size=200, width=1100, height=860, mask=mask)  # max_font_size 最大文字大小 background_color 词云图背景颜色
cloud.generate(text_cut)
cloud.to_file('cloudDemo.png')  # 保存为cloudDemo.jpg
