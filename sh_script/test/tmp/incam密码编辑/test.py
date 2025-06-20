#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:test.py
   @author:zl
   @time: 2024/12/27 11:53
   @software:PyCharm
   @desc:
"""
import pandas as pd
from hashlib import md5
from TOPCAM_IKM import IKM


def get_md5(s):
    return md5(s.encode()).hexdigest()


if __name__ == '__main__':
    data = pd.read_excel(r'C:\Users\99234\Desktop\user_info.xlsx', dtype={'工号': 'Int64'})
    print(data)
    df = data.iloc[:, [0, 2, 5, 7]]
    data = []
    for index, row in df.iterrows():
        if not pd.isna(row.values[:2]).any():
            data.append(row.values[:2])
        if not pd.isna(row.values[2:]).any():
            data.append(row.values[2:])
    print(data)

    # ikm_fun = IKM()
    # for staffid, pwd in data:
    #     pwd = pwd.strip()
    #     sql = """update sys_user set password='%s' where staffid='%s'""" % (get_md5(pwd), staffid)
    #     data_info = ikm_fun.PG.SQL_EXECUTE(ikm_fun.dbc_p, sql)
    #     if data_info:
    #         print('%s已更新密码%s' % (staffid, pwd))
