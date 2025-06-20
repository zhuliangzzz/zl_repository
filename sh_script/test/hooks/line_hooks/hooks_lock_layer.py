#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:hooks_lock_layer.py
   @author:zl
   @time: 2024/12/19 19:27
   @software:PyCharm
   @desc:
   open_job.post
   打开料号后把铜皮层锁住
"""
import sys
import platform

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

from open_job_lock_zl import CheckUserOpenJob
import genClasses_zl as gen


def lock():
    job = gen.Job(jobname)
    fill_layer = 'inner_panel_surface'
    if fill_layer in job.matrix.returnRows():
        CheckUserOpenJob(jobname).lock_panel_steps([fill_layer])


if __name__ == '__main__':
    jobname = sys.argv[1]
    lock()
