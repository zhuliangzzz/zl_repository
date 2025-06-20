#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:BackupDeleteJob.py
   @author:zl
   @time:2024/6/25 17:19
   @software:PyCharm
   @desc: 
"""
import os.path
import sys
import genClasses as gen

if __name__ == '__main__':
    jobname = sys.argv[1]
    path = r'D:\back_delete_tgz'
    if not os.path.exists(path):
        os.mkdir(path)
    gen.Top().exportJob(jobname, path)
