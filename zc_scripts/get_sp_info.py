#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:get_sp_info.py
   @author:zl
   @time:2024/8/24 16:47
   @software:PyCharm
   @desc:
"""
import json
import pprint
import random

import requests
from ua_info import UserAgent

url = 'http://192.168.0.188:8080/_extensions/carte/executeTrans.jsp?trans=/Carte/getEngineeringData&number='


def get_sp_info_by_number(number):
    response = requests.get(url + str(number), headers={'User-Agent': random.choice(UserAgent().chrome)})
    # print(response.text)
    return response.text


if __name__ == '__main__':
    # res = json.loads(get_sp_info_by_number('01-F-FP02CG003372003'))
    res = json.loads(get_sp_info_by_number('03-F-FP07CG003772001'))
    if res.get('data'):
        datalist = json.loads(res.get('data')[0].get('json')).get('data')
        for data in datalist:
            pprint.pprint(data)
    else:
        print('无处理数据')