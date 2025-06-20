#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CheckLossTestPadComp-main.py
   @author:zl
   @time: 2025/3/5 14:50
   @software:PyCharm
   @desc:
   检测loss测试pad是否补偿
"""
import json
import os
import re
import sys
import platform

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import MySQL_DB
class CheckLossTestPadComp(object):
    def __init__(self):
        self.mysql = MySQL_DB.MySQL()
        self.dbc = self.mysql.MYSQL_CONNECT()
        self.check()

    def check(self):
        total_jobs = []
        sql = '''SELECT job_name, layer_info FROM  hdi_engineering.incam_job_layer_info'''
        datas = self.mysql.SELECT_DIC(self.dbc, sql)
        for data in datas:
            jobname = data.get('job_name')
            if data.get('layer_info') and jobname:
                if 'loss' in json.loads(data.get('layer_info')).get('gCOLstep_name'):
                    print(jobname)
                    # total_jobs.append(jobname)
                    # os.system('python /frontline/incam/server/site_data/scripts/sh_script/zl/crontab/CheckLossTestPadComp.py %s' % jobname)

        # with open(r'C:\Users\99234\Desktop\check.txt', encoding='utf8') as r:
        #     readline = r.readlines()
        # job_dict = {}
        # for line in readline:
        #     res = re.search('Job (.*?):(.*)', line)
        #     jobname,log = res.group(1), res.group(2)
        #
        #     job_dict[jobname] = log.strip()
        # for job in total_jobs:
        #     if job in job_dict.keys():
        #         print(job_dict.get(job))
        #     else:
        #         print('料号不存在')
if __name__ == '__main__':
    CheckLossTestPadComp()

