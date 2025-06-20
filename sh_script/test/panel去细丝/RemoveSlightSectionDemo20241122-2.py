#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:RemoveSlightSectionDemo.py
   @author:zl
   @time: 2024/11/21 17:01
   @software:PyCharm
   @desc:
   panel去细丝
"""
import os
import re
import sys
import platform

import genesisPackages

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

# import gClasses
import genClasses_zl as gen
from genesisPackages import outsignalLayers

def RemoveSlightSection():
    step = gen.Step(job, 'panel')
    step.initStep()
    step.setUnits('inch')
    layer = 'l2'
    tmp_signal = layer + '+++'
    tmp_surface = layer + '_surface'
    step.removeLayer(tmp_signal)
    step.removeLayer(tmp_surface)
    step.removeLayer(layer + '_symbol')
    step.removeLayer(layer + '_symbol+++')
    step.affect(layer)
    step.copySel(tmp_signal)
    step.unaffectAll()
    step.affect(tmp_signal)
    step.setAttrFilter('.pattern_fill')
    step.selectAll()
    if step.Selected_count():
        step.copySel(tmp_surface)
        step.selectAll()
        step.selectReverse()
        if step.Selected_count():
            step.copySel(layer + '_symbol')
    step.unaffectAll()
    step.resetFilter()
    info = step.Features_INFO(layer + '_symbol', 'feat_index')
    index_list = []
    for line in info:
        if line and re.match('#\d+', line[0]):
            index_list.append(int(line[0].replace('#', '')))
    for index in index_list:
        step.affect(layer + '_symbol')
        step.selectByIndex(layer + '_symbol', index)
        step.copySel(layer + '_symbol+++')
        step.unaffectAll()
        step.affect(layer + '_symbol+++')
        step.selectBreak()
        step.unaffectAll()
    step.affect(layer + '_symbol+++')
    step.setFilterTypes(polarity='positive')
    step.selectAll()
    step.resetFilter()
    if step.Selected_count():
        step.selectDelete()
    step.selectPolarity()
    step.Contourize(0)
    step.unaffectAll()
    # 整体转surface
    step.affect(tmp_signal)
    step.Contourize(0)
    step.clip_area(margin=0, ref_layer= layer + '_symbol+++')
    step.unaffectAll()
    # 加大负性层 被负性层cover到的为单独的细丝  slight_section
    sec = layer + '_slight_section'
    step.removeLayer(sec)
    step.affect(layer + '_symbol+++')
    step.selectResize(12)
    step.unaffectAll()
    step.affect(tmp_signal)
    step.refSelectFilter(layer + '_symbol+++', mode='cover')
    if step.Selected_count():
        step.copySel(sec)
    step.unaffectAll()
    step.affect(tmp_surface)
    step.selectResize(-6)
    step.selectResize(6)
    if step.isLayer(sec):
        step.clip_area(margin=0.1, ref_layer=sec)
    step.unaffectAll()
    step.affect(layer + '_symbol')
    step.copySel(tmp_surface)
    step.unaffectAll()






if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    print(outsignalLayers)
    # RemoveSlightSection()