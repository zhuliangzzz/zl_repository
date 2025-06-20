#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:DefinedBGA_attr.py
   @author:zl
   @time: 2024/10/23 20:02
   @software:PyCharm
   @desc:
   去掉圆形pad 的.smd属性 再把圆形pad定义成.bga属性
"""
import os
import sys
import platform

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genClasses_zl

def DefinedBGA_attr():
    bot_signal = 'l%s' % len(job.matrix.returnRows('board', 'signal|power_ground'))
    step.initStep()
    step.affect('l1')
    step.affect(bot_signal)
    step.setFilterTypes('pad')
    step.setSymbolFilter('r*', 'rect*')
    step.setAttrFilter('.smd')
    step.selectAll()
    step.resetFilter()
    if step.Selected_count():
        step.COM('sel_delete_atr,mode=list,attributes=.smd')
    step.setFilterTypes('pad')
    step.setSymbolFilter('r*', 'rect*')
    step.selectAll()
    step.addAttr('.bga', attrVal='')
    step.resetAttr()
    step.unaffectAll()


if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    job = genClasses_zl.Job(jobname)
    step = job.steps.get('net')
    DefinedBGA_attr()
