#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:ClearTempAndBackupLayer.py
   @author:zl
   @time: 2025/1/24 15:36
   @software:PyCharm
   @desc:
   清除临时层-ls和备份层-bf   10天前
   20250207 把不存在的层的锁信息去除
   20250211 优化旋转拼版的料号和跳过ODB格式的料号
"""
import os
import re
# import subprocess
# import tarfile
import datetime
import time


class Main(object):
    def __init__(self):
        self.db1 = '/data2/incamp_db1/jobs'
        self.log_file = '/data3/backup_linshi_jobs/clear_temp_and_back_layer.log'  # 日志文件 clear_temp_and_back_layer.log
        self.term = 10  # 期限：天
        self.clear_layer_file = '/windows/174.db/clear_layer_contains.txt'
        self.run()

    def run(self):
        clear_dict = {}
        run_time = time.strftime('%Y-%m-%d %H:%M:%S')
        # 匹配杂层
        clear_layers = []
        try:
            with open(self.clear_layer_file) as reader:
                readlines = reader.readlines()
                for readline in readlines:
                    readline = re.sub('[\r\s\n]', '', readline)
                    # 20250306 文件内容异常
                    try:
                        re.compile(readline)
                        clear_layers.append(readline)
                    except Exception:
                        with open(self.log_file, 'a') as writer:
                            writer.write('[%s]%s文件字符%s正则匹配异常!\n' % (run_time, self.clear_layer_file, readline))
        except Exception:
            pass
        if not clear_layers:
            with open(self.log_file, 'a') as writer:
                writer.write('[%s]文件%s异常!\n' % (run_time, self.clear_layer_file))
            return
        for jobname in os.listdir(self.db1):
            if len(jobname) != 13:
                continue
            if os.path.isdir(os.path.join(self.db1, jobname)):
                # 判断是否是ODB格式
                if os.path.exists(os.path.join(self.db1, jobname, 'misc/info')):
                    with open(os.path.join(self.db1, jobname, 'misc/info'), 'r') as r:
                        content = r.readlines()
                    odb_flag = False
                    for line in content:
                        if line.startswith('ODB_VERSION'):
                            odb_flag = True
                            break
                    if odb_flag:
                        with open(self.log_file, 'a') as writer:
                            writer.write('[%s]Job %s is ODB format!\n' % (run_time, jobname))
                        continue
                else:
                    with open(self.log_file, 'a') as writer:
                        writer.write('[%s]Job %s not exist misc/info\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), jobname))
                    continue
                if not os.path.exists(os.path.join(self.db1, jobname, 'steps')) or not os.listdir(os.path.join(self.db1, jobname, 'steps')):
                    continue

                # layers
                for lyr in os.listdir(os.path.join(self.db1, jobname, 'steps', os.listdir(os.path.join(self.db1, jobname, 'steps'))[0], 'layers')):
                    res = re.search('-(ls|bf)(\d{6}.\d{4})', lyr)
                    if res:
                        time_str = res.group(2)
                        if self.is_expired(time_str):
                            # 过期的层
                            if jobname not in clear_dict.keys():
                                clear_dict[jobname] = []
                            clear_dict[jobname].append(lyr)
                    # 杂层
                    if re.search('^(-+|rout_drc|symbol_tmp|profile_outline|patternfill_flatten)$|%s' % '|'.join(clear_layers + [jobname]) , lyr) or lyr.count('+') > 1:
                        if jobname not in clear_dict.keys():
                            clear_dict[jobname] = []
                        clear_dict[jobname].append(lyr)
        exception_job_num = 0
        # i = 0
        for jobname, lyrs in clear_dict.items():
            lyrs_str = ' '.join(lyrs)
            status = os.system('python /frontline/incam/server/site_data/scripts/sh_script/zl/crontab/ClearTempAndBackupLayer.py %s %s' % (jobname, lyrs_str))
            if status == 0:
                with open(self.log_file, 'a') as writer:
                    writer.write('[%s]Job %s cleaning completed.\n' % (run_time, jobname))
            else:
                with open(self.log_file, 'a') as writer:
                    writer.write('[%s]Job %s cleaning exception.\n' % (run_time, jobname))
                exception_job_num += 1
            # if i > 1:
            #     break
            # i += 1
        if clear_dict:
            with open(self.log_file, 'a') as writer:
                writer.write('[%s]The number of cleaning this time: %s.\n\n' % (run_time, len(clear_dict.keys()) - exception_job_num))
        # jobname = 'sd1024e7213bk_20250219023241'
        # lyrs_str = 'l1-ls250209.0113 l24-ls250209.0113'
        # os.system('python /frontline/incam/server/site_data/scripts/sh_script/zl/crontab/ClearTempAndBackupLayer.py %s %s' % (jobname, lyrs_str))

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
