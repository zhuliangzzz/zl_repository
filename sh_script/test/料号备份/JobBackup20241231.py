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
import tarfile
import socket


class JobBackup(object):
    def __init__(self):
        self.host = socket.gethostname()
        # job存放路径
        # self.job_path = '/incampro/incamp_db1/jobs/'
        data = json.load(open('config'))
        self.job_path = data.get('job_path')
        # job备份路径
        # self.job_backup_path = '/incam/server/site_data/scripts/zl/tmp/'
        self.job_backup_path = data.get('job_backup_path')
        if 'ntincam' in self.host:
            # self.job_path = '/incampro/incamp_db3/jobs/'
            self.job_path = data.get('nt_job_path')
        # 设置更新时间差 :h
        self.diff_time = float(data.get('diff_time')) * 3600   # 秒

    def backup(self):
        for job_dir in os.listdir(self.job_path):
            # print(job_dir)
            if not os.path.exists(os.path.join(self.job_backup_path, job_dir + '.tgz')):
                self.tar_tgz(job_dir)
            else:
                # 判断时间差
                job_time = os.path.getmtime(os.path.join(self.job_path, job_dir + '/misc/info'))
                back_time = os.path.getctime(os.path.join(self.job_backup_path, job_dir + '.tgz'))
                # print(job_time, back_time)
                if job_time - back_time > self.diff_time:
                    # print('backuping')
                    self.tar_tgz(job_dir)

    def tar_tgz(self, jobname):
        if not os.path.exists(self.job_backup_path):
            os.makedirs(self.job_backup_path)
        output_file = os.path.join(self.job_backup_path, jobname + '.tgz')
        tar = tarfile.open(output_file, "w:gz")
        for root, dirs, files in os.walk(jobname):
            for file in files:
                file_path = os.path.join(root, file)
                tar.add(file_path)
        tar.close()


if __name__ == '__main__':
    jobBackup = JobBackup()
    jobBackup.backup()