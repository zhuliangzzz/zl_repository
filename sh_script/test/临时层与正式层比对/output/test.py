#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:test.py
   @author:zl
   @time: 2024/10/9 11:33
   @software:PyCharm
   @desc:
"""
import json
import pprint

import MySQL_DB


if __name__ == '__main__':

    mysql = MySQL_DB.MySQL()

    dbc = mysql.MYSQL_CONNECT()
    sql = '''
    SELECT step_info FROM  hdi_engineering.incam_job_layer_info where job_name like '%SD1024E7213B6%'
    '''
    data = mysql.SELECT_DIC(dbc, sql)
    rotate_steps = []
    if data:
        data_dict = json.loads(data[0].get('step_info'))
        for step, angle in zip(data_dict.get('gSRstep'), data_dict.get('gSRangle')):
            print(step, angle)
            if angle not in (0, 90, 180, 270, 360) and step not in rotate_steps:
                rotate_steps.append(step)
    print(rotate_steps)
