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

import genClasses_zl as gen


def DefinedBGA_attr():
    bot_signal = 'l%s' % len(job.matrix.returnRows('board', 'signal|power_ground'))
    step.initStep()
    for signal in ['l1', bot_signal]:
        sm = 'm1' if signal == 'l1' else 'm2'
        step.affect(signal)
        step.setFilterTypes('pad')
        step.setSymbolFilter('r*', 'rect*')
        step.setAttrFilter('.smd')
        if step.isLayer(sm):
            step.refSelectFilter(sm, mode='cover')
            step.resetFilter()
            if step.Selected_count():
                step.COM('sel_delete_atr,mode=list,attributes=.smd')
        step.resetFilter()
        step.setFilterTypes('pad')
        step.setSymbolFilter('r*', 'rect*')
        if step.isLayer(sm):
            step.refSelectFilter(sm, mode='cover')
            step.resetFilter()
            if step.Selected_count():
                step.addAttr('.bga', attrVal='')
        step.resetAttr()
        step.resetFilter()
        step.unaffectAll()


if __name__ == '__main__':
    jobname, stepname = sys.argv[1:]
    job = gen.Job(jobname)
    step = gen.Step(job, stepname)
    DefinedBGA_attr()
