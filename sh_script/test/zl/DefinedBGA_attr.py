#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:DefinedBGA_attr.py
   @author:zl
   @time: 2024/10/23 20:02
   @software:PyCharm
   @desc:
   去掉圆形pad 的.smd属性 再把圆形pad定义成.bga属性
   20241209 smd属性接触的圆pad不定bga
   20241210 阻焊层铜皮覆盖的bga默认为镭射ring 去掉bga属性
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
        # 把smd拷贝出来，如果圆pad被smd接触到，则不定bga属性
        tmp_signal = 'tmp_%s+++' % signal
        step.setAttrFilter('.smd')
        step.selectAll()
        step.resetFilter()
        if step.Selected_count():
            step.copySel(tmp_signal)
        step.setFilterTypes('pad')
        step.setSymbolFilter('r*', 'rect*')
        if step.isLayer(sm):
            step.refSelectFilter(sm, mode='cover')
            step.resetFilter()
            if step.Selected_count():
                step.addAttr('.bga', attrVal='')
        step.resetAttr()
        step.resetFilter()
        if step.isLayer(tmp_signal):
            step.setAttrFilter('.bga')
            step.refSelectFilter(tmp_signal)
            if step.Selected_count():
                step.COM('sel_delete_atr,mode=list,attributes=.bga')
        step.resetFilter()
        step.unaffectAll()
        # 阻焊层铜皮覆盖的bga默认为镭射ring 去掉bga属性
        if step.isLayer(sm):
            tmp_sm = 'tmp_%s+++' % sm
            step.affect(sm)
            step.setFilterTypes('surface')
            step.selectAll()
            step.resetFilter()
            if step.Selected_count():
                step.copySel(tmp_sm)
                step.unaffectAll()
                step.affect(signal)
                step.setAttrFilter('.bga')
                step.refSelectFilter(tmp_sm, mode='cover')
                step.resetFilter()
                if step.Selected_count():
                    step.COM('sel_delete_atr,mode=list,attributes=.bga')
                step.removeLayer(tmp_sm)
            step.unaffectAll()
        step.removeLayer(tmp_signal)


if __name__ == '__main__':
    jobname, stepname = sys.argv[1:]
    job = gen.Job(jobname)
    step = gen.Step(job, stepname)
    DefinedBGA_attr()
