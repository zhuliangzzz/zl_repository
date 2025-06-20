#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:ZL_mysqlCon.py
   @author:zl
   @time:2024/6/18 13:17
   @software:PyCharm
   @desc: 
"""
import pymysql


class DBConnect(object):
    def __init__(self):
        self.connection = pymysql.connect(host='172.16.0.106', user='gongcheng', password='gongcheng', db='fpc')
        self.cursor = self.connection.cursor()

    def close_con(self):
        self.cursor.close()
        self.connection.close()
