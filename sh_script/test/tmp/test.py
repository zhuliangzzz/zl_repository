#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:test.py
   @author:zl
   @time: 2025/3/20 15:37
   @software:PyCharm
   @desc:
"""
import re

# with open('sd1022e6261b4-zltest.b6-17') as f:
#     readlines = f.read()
# # findall = re.findall('T\d+C\d+\.\d{3}(.*)\n', readlines)
# findall = re.findall('T\d+C\d+\.?\d*([a-zA-Z].*)?\n', readlines)
# print(findall)
# print([len(p) == 0 for p in findall])
# print(any([len(p) == 0 for p in findall]))

# drl_name = 'b6-17'
# if re.search('^drl$|^b((\d+)(-)(\d+))$|^m((\d+)(-)(\d+))$|^dbk(\S+)$|^dbk$|^(2|3)nd$|^lr((\d+)(-)(\d+))$', drl_name):
#     print('a')
value = '-####'
week_code = re.search('([WY]+)', value)
print(week_code.group(1))