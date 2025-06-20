#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:SelectWrappedPads.py
   @author:zl
   @time: 2024/10/28 17:52
   @software:PyCharm
   @desc:
"""

import os, sys
import os
import sys
import platform

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genClasses_zl as gen


def SelectWrappedPads():
    step.initStep()
    bot_signal = 'l%s' % len(job.matrix.returnRows('board', 'signal|power_ground'))
    step.initStep()
    # .smd .bga层
    cover_layer = 'smd_bga+++'
    surface_layer = 'surface+++'
    if step.isLayer(cover_layer):
        step.removeLayer(cover_layer)
    if step.isLayer(surface_layer):
        step.removeLayer(surface_layer)
    for signal in ['l1', bot_signal]:
        step.affect(signal)
        step.setAttrFilter2('.smd')
        step.setAttrFilter2('.bga')
        step.setAttrLogic(0)
        step.selectAll()
        step.resetFilter()
        if step.Selected_count():
            step.copySel(cover_layer)
            step.setFilterTypes('surface', 'positive')
            step.COM('set_filter_attributes,filter_name=popup,exclude_attributes=yes,condition=no,attribute=.detch_comp,min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=')
            step.selectAll()
            step.resetFilter()
            if step.Selected_count():
                step.copySel(surface_layer)
                step.unaffectAll()
                step.affect(surface_layer)
                step.Contourize()
                step.COM('sel_clean_holes,max_size=99999,clean_mode=x_and_y')
                step.unaffectAll()
            else:
                step.unaffectAll()
                continue
            step.unaffectAll()


        else:
            step.unaffectAll()
            continue



        # step.setFilterTypes('pad')
        # step.selectAll()
        # if step.Selected_count():
        #     step.copySel()
        # # 通过smd/pad/bga去找铜皮

        # step.unaffectAll()





if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    step = job.steps.get('edit')
    SelectWrappedPads()