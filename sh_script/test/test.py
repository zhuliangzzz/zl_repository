#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:test.py
   @author:zl
   @time: 2024/10/9 11:33
   @software:PyCharm
   @desc:
"""
import hashlib
# import json
# import pprint
import re
import string
import time

# import MySQL_DB
# def a(*args):
#     layers = args
#     print layers
#     print(a)
    # print list(layers[0])
    # print list(args)


# def calculate_md5(file_path):
#     md5 = hashlib.md5()
#     with open(file_path, 'rb') as f:  # 以二进制读取模式打开文件
#         for chunk in iter(lambda: f.read(4096), b""):  # 读取文件，每次4096字节
#             md5.update(chunk)  # 更新哈希值
#     return md5.hexdigest()  # 返回十六进制的哈希值
#
#
# # 使用函数计算文件的MD5值
# # file_path = r'\\192.168.2.126\workfile\lyh\tgz\da8616ph551c1.tgz'  # 替换为你的文件路径
# file_path = r'/id/workfile/film/c18302gf824a1-zltest/c18302gf824a1-zltest.tgz'  # 替换为你的文件路径
# md5_value = calculate_md5(file_path)
# print("MD5 value:", md5_value)
# if __name__ == '__main__':
#
# md5 = hashlib.md5()
# md5.update(b'10485537')
# print(md5.hexdigest())
print(time.time())
print(time.strftime('%Y%m%d%H%M%S'))

