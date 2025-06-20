#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:test.py
   @author:zl
   @time: 2025/1/15 20:28
   @software:PyCharm
   @desc:
"""
import sys

try:
    with open('db1_jobs_list', 'r') as reader:
        lines = reader.readlines()
except FileNotFoundError:
    sys.exit()
# except Exception as e:
#     QtGui.QMessageBox.warning(None, u"判断外层已审核失败，请联系程序组处理", str(e))
#     gen.Job(jobname).COM('skip_current_command')
#     sys.exit()
output = []
if lines:
    output = [job for jobs in map(lambda line:line.strip().split(), lines) for job in jobs]
    print(output)