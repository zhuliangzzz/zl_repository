#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:test.py
   @author:zl
   @time: 2024/11/1 17:23
   @software:PyCharm
   @desc:
"""
import time

def aaaa(layers, step='panel'):
    for i, cur_layer_name in enumerate(layers, 1):
        print(i, cur_layer_name)


if __name__ == '__main__':
    print(time.strftime('_%Y%m%d%H%M%S'))