#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:genesisTest.py
   @author:zl
   @time: 2024/10/18 16:33
   @software:PyCharm
   @desc:
"""
import os

import os
import sys
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")

import genClasses_zl as gen

if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    step = gen.Step(job, 'panel')
    step.initStep()
    print(job.steps)