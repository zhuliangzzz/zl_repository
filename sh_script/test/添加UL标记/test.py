#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:test.py
   @author:zl
   @time: 2025/6/27 9:51
   @software:PyCharm
   @desc:
"""
import pprint
import re

import pandas as pd

excel = pd.read_excel(r'C:\Users\99234\Result_1.xlsx')

dict_ = {}
for i in excel.values:
    if i[0] not in dict_:
        dict_[i[0]] = []
    dict_[i[0]].append(i[1])
list_, list2 = [],[]
for k, v in dict_.items():
    # print(k,re.search('SH(\S+)?', k), v[0])
    if re.search('SH(\S+)?', k):
        s_ = re.search('SH(\S+)?', k).group(1)
        if s_ is not None:
            if re.match('\d+$', s_):
                if int(s_) > 14:
                    list_.append([int(s_), v[0]])
            else:
                list2.append([s_, v[0]])
list_.sort(key=lambda i:i[0])
pprint.pp(list_)
pprint.pp(list2)