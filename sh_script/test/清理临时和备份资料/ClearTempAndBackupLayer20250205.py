#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CheckLossTestPadComp.py
   @author:zl
   @time: 2025/1/24 15:36
   @software:PyCharm
   @desc:
   清除临时层-ls和备份层-bf   10天前
"""
import os
import re
import sys
import tarfile
import platform
import time

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genClasses_zl as gen


class ClearTempAndBackupLayer(object):
    def __init__(self):
        self.db1 = '/data2/incamp_db1/jobs'
        self.back_path = '/data3/backup_jobs/jobs'
        self.term = 10  # 期限：天
        self.suffix = time.strftime('_%Y%m%d%H%M%S')
        self.logfile = os.path.join(self.back_path, '%s.txt' % jobname)
        self.run()

    def run(self):
        job = gen.Job(jobname)
        job.COM('is_job_open,job=%s' % jobname)
        if job.COMANS == 'yes':
            print("Job already open, not opening")
            with open(self.logfile, 'a') as writer:
                writer.write('[%s]Job already open: %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), jobname))
            sys.exit()
        os.chdir(self.db1)
        self.tar_tgz(jobname)
        job.open(1)
        for lyr in lyrs:
            job.matrix.deleteRow(lyr)
        job.save()
        job.close(1)
        with open(self.logfile, 'a') as writer:
            writer.write('[%s]removed layer: %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), ''.join(lyrs)))
        exit()


    def tar_tgz(self, jobname):
        if not os.path.exists(self.back_path):
            os.makedirs(self.back_path)
        output_file = os.path.join(self.back_path, jobname + self.suffix + '.tgz')
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
    jobname = sys.argv[1]
    lyrs = sys.argv[2:]
    ClearTempAndBackupLayer()
