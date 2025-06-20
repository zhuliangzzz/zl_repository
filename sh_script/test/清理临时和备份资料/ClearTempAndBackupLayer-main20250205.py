#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:ClearTempAndBackupLayer.py
   @author:zl
   @time: 2025/1/24 15:36
   @software:PyCharm
   @desc:
   清除临时层-ls和备份层-bf   10天前
"""
import os
import re
# import subprocess
# import tarfile
import datetime


class Main(object):
    def __init__(self):
        self.db1 = '/data2/incamp_db1/jobs'
        self.back_path = '/data3/backup_jobs/jobs'
        self.term = 10  # 期限：天
        self.run()

    def run(self):
        clear_dict = {}
        for jobname in os.listdir(self.db1):
            # print(jobname)
            # if len(jobname) != 13:
            #     continue
            if os.path.isdir(os.path.join(self.db1, jobname)):
                if not os.path.exists(os.path.join(self.db1, jobname, 'steps')) or not os.listdir(os.path.join(self.db1, jobname, 'steps')):
                    continue
                # layers
                for lyr in os.listdir(
                        os.path.join(self.db1, jobname, 'steps', os.listdir(os.path.join(self.db1, jobname, 'steps'))[0],'layers')):
                    res = re.search('-(ls|bf)(\d{6}.\d{4})', lyr)
                    if res:
                        time_str = res.group(2)
                        if self.is_expired(time_str):
                            # 过期的层
                            if jobname not in clear_dict.keys():
                                clear_dict[jobname] = []
                            clear_dict[jobname].append(lyr)
        os.environ['FRONTLINE_NO_LOGIN_SCREEN'] = '/frontline/incam/server/site_data/scripts/sh_script/zl/crontab/login'
        for jobname, lyrs in clear_dict.items():
            # lyrs = ['m1-ls250115', 'm2-ls250115']
            # if jobname != 'fa8622o6804d1-zltest':
            if jobname != 'da8612ph596a6':
                continue
            lyrs_str = ' '.join(lyrs)
            # print(lyrs_str)
            os.system('/incampro/release/bin/InCAMPro -X -s/frontline/incam/server/site_data/scripts/sh_script/zl/crontab/ClearTempAndBackupLayer.py %s %s >> /frontline/incam/server/site_data/scripts/sh_script/zl/crontab/log.txt' % (jobname, lyrs_str))
            # 定义命令和参数
            # rsync_command = ["/incampro/release/bin/InCAMPro", "-X", "-s/frontline/incam/server/site_data/scripts/sh_script/zl/crontab/ClearTempAndBackupLayer.py", jobname, lyrs_str, '>> /frontline/incam/server/site_data/scripts/sh_script/zl/crontab/log.txt']
            # # 创建子进程
            # process = subprocess.Popen(rsync_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # # 获取命令的输出和错误信息
            # output, error = process.communicate()
            break
    def is_expired(self, time_str):

        # 解析时间字符串为 datetime 对象
        try:
            given_time = datetime.datetime.strptime(time_str, "%y%m%d.%H%M")
        except ValueError as e:
            print("时间格式错误:" + str(e))
            return False
        # 当前时间
        current_time = datetime.datetime.now()

        # 计算时间差
        time_difference = current_time - given_time

        # 判断时间差是否在十天以内
        if time_difference <= datetime.timedelta(days=self.term):
            return False
        else:
            return True


if __name__ == '__main__':
    Main()
