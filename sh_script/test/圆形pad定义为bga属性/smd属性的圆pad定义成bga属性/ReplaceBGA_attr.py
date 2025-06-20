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
import re
import sys
import platform

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
from genesisPackages_zl import lay_num
import genClasses_zl as gen

def DefinedBGA_attr():
    bot_signal = 'l%s' % lay_num
    step.initStep()
    step.affect('l1')
    step.affect(bot_signal)
    step.setFilterTypes('pad')
    step.setAttrFilter('.smd')
    step.selectAll()
    step.resetFilter()
    if step.Selected_count():
        # 找出里面的r数字的所有圆pad
        layer1 = gen.Layer(step, 'l1')
        layer2 = gen.Layer(step, bot_signal)
        pad_objs = layer1.featout_dic_Index(units='mm', options='feat_index+select')['pads']
        pad2_objs = layer2.featout_dic_Index(units='mm', options='feat_index+select')['pads']
        pads = set()
        for pad_obj in pad_objs:
            if re.match('r(\d+|\d+.\d+)$', pad_obj.symbol):
                pads.add(pad_obj.symbol)
        for pad_obj in pad2_objs:
            if re.match('r(\d+|\d+.\d+)$', pad_obj.symbol):
                pads.add(pad_obj.symbol)
        step.clearSel()
        step.setFilterTypes('pad')
        step.setAttrFilter('.smd')
        step.setSymbolFilter('\;'.join(pads))
        step.selectAll()
        step.resetFilter()
        if step.Selected_count():
            step.resetAttr()
            step.COM('cur_atr_set,attribute=.bga')
            step.COM('sel_change_atr,mode=replace,attributes=.smd')
        step.resetAttr()
    step.unaffectAll()


if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    stepname = os.environ.get('STEP')
    job = gen.Job(jobname)
    step = gen.Step(job, stepname)
    DefinedBGA_attr()
