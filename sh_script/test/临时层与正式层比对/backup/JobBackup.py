#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:JobBackup.py
   @author:zl
   @time: 2024/12/30 8:49
   @software:PyCharm
   @desc: 料号备份
"""
import json
import os
import platform
import sys
import tarfile
import socket
from datetime import datetime
import time

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import MySQL_DB


class JobBackup(object):
    def __init__(self):
        self.host = socket.gethostname()
        self.ip = socket.gethostbyname(socket.gethostname())
        self.my_sql = MySQL_DB.MySQL()
        self.my_sql.MYSQL_CONNECT()
        self.job_path, self.job_backup_path, self.diff_time = None, None, None
        try:
            data = json.load(open('config'))
            # job存放路径
            self.job_path = data.get('job_path').encode('utf8')
            # job备份路径
            self.job_backup_path = data.get('job_backup_path').encode('utf8')
            # print(self.job_backup_path)
            if 'ntincam' in self.host:
                self.job_path = data.get('nt_job_path').encode('utf8')
            # 设置更新时间差 :h
            self.diff_time = float(data.get('diff_time')) * 3600  # 秒
        except Exception as e:
            sql = "insert into hdi_engineering.incam_job_backup_info(job_path, job_backup_path, diff_time,log) values(%s, %s, %s, %s)"
            self.my_sql.SQL_EXECUTE(self.my_sql.dbc, sql, (self.job_path, self.job_backup_path, self.diff_time, '配置信息异常： %s (程序地址：%s)' % (str(e), self.ip)))
            sys.exit()

    def backup(self):
        # i = 0
        os.chdir(self.job_path)
        for job_dir in os.listdir(self.job_path):
            if len(job_dir) != 13:
                continue
            # if i > 3:
            #     break
            if not os.path.exists(os.path.join(self.job_backup_path, job_dir + '.tgz')):
                # print(job_dir)
                self.tar_tgz(job_dir)
                sql = "insert into hdi_engineering.incam_job_backup_info(jobname,job_path, job_backup_path, diff_time,log) values(%s, %s, %s, %s, %s)"
                self.my_sql.SQL_EXECUTE(self.my_sql.dbc, sql, (job_dir, self.job_path, self.job_backup_path, self.diff_time / 3600, r'备份成功： %s.tgz (程序地址：%s)' % (job_dir, self.ip)))
            else:
                try:
                    # 判断时间差
                    job_time = None
                    if os.path.exists(os.path.join(self.job_path, job_dir + '/misc/info')):
                        with open(os.path.join(self.job_path, job_dir + '/misc/info'), 'r') as r:
                            content = r.readlines()
                        for line in content:
                            if line.startswith('SAVE_DATE'):
                                save_date = line.strip().split('=')[1]
                                # 将给定的日期和时间转换为 datetime 对象
                                dt = datetime.strptime(save_date, "%Y%m%d.%H%M%S")
                                # 计算时间戳
                                # job_time = int(dt.timestamp())
                                job_time = time.mktime(dt.timetuple())
                    if job_time is None:
                        e = '无法获取料号info保存时间'
                        sql = "insert into hdi_engineering.incam_job_backup_info(jobname,job_path, job_backup_path, diff_time,log) values(%s, %s, %s, %s, %s)"
                        self.my_sql.SQL_EXECUTE(self.my_sql.dbc, sql, (job_dir, self.job_path, self.job_backup_path, self.diff_time / 3600,'备份异常： %s (程序地址：%s)' % (str(e), self.ip)))
                        continue
                    # 2024.12.1以后的进行备份
                    begin_time = time.mktime(datetime(2024, 12, 1, 0, 0, 0, 0).timetuple())
                    if job_time < begin_time:  # 时间节点之前的跳过
                        continue
                    back_time = int(os.path.getctime(os.path.join(self.job_backup_path, job_dir + '.tgz')))
                    if job_time - back_time > self.diff_time:
                        self.tar_tgz(job_dir)
                        sql = "insert into hdi_engineering.incam_job_backup_info(jobname,job_path, job_backup_path, diff_time,log) values(%s, %s, %s, %s, %s)"
                        self.my_sql.SQL_EXECUTE(self.my_sql.dbc, sql, (job_dir, self.job_path, self.job_backup_path, self.diff_time/3600, r'备份成功： %s.tgz (程序地址：%s)' % (job_dir, self.ip)))
                except Exception as e:
                    print(e)
                    sql = "insert into hdi_engineering.incam_job_backup_info(jobname,job_path, job_backup_path, diff_time,log) values(%s, %s, %s, %s, %s)"
                    self.my_sql.SQL_EXECUTE(self.my_sql.dbc, sql, (job_dir, self.job_path, self.job_backup_path, self.diff_time/3600, '备份异常： %s (程序地址：%s)' % (str(e), self.ip)))
            # i += 1
    def tar_tgz(self, jobname):
        if not os.path.exists(self.job_backup_path):
            os.makedirs(self.job_backup_path)
        output_file = os.path.join(self.job_backup_path, jobname + '.tgz')
        try:
            tar = tarfile.open(output_file, "w:gz")
            for root, dirs, files in os.walk(jobname):
                for file in files:
                    file_path = os.path.join(root, file)
                    tar.add(file_path)
            tar.close()
        except IOError as e:
            os.chmod(e.filename, 0o664)
            self.tar_tgz(jobname)


if __name__ == '__main__':
    jobBackup = JobBackup()
    jobBackup.backup()
