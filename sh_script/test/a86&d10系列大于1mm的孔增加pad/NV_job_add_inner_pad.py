#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:NV_job_add_inner_pad.py
   @author:zl
   @time: 2025/4/15 9:52
   @software:PyCharm
   @desc:
   http://192.168.2.120:82/zentao/story-view-7419.html
   nv系列1mm以上的孔线路层加pad
"""
import os
import platform
import re
import sys
from PyQt4 import QtGui, QtCore

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen
from genesisPackages import innersignalLayers, tongkongDrillLayer


class NV_job_add_inner_pad(object):
    def __init__(self):
        self.jobname = os.environ.get('JOB')
        self.job = gen.Job(self.jobname)
        if self.jobname[1:4] not in ('a86', 'd10'):
            QtGui.QMessageBox.warning(None, '提示', '该料号非NV型号')
            sys.exit()
        if not tongkongDrillLayer:
            QtGui.QMessageBox.warning(None, '提示', '该料号没有通孔层')
            sys.exit()
        if not innersignalLayers:
            QtGui.QMessageBox.warning(None, '提示', '该料号没有内层线路层')
            sys.exit()
        self.add_pad()

    def add_pad(self):
        step = gen.Step(self.job, 'edit')
        step.initStep()
        for drl in tongkongDrillLayer:
            tmp_drl = '%s+++%s' % (drl, step.pid)
            step.affect(drl)
            step.setFilterTypes('line|pad')
            step.setAttrFilter_pro('.drill', 'non_plated')
            step.setAttrLogic_pro()
            step.selectAll()
            step.resetFilter()
            if step.Selected_count():
                step.copySel(tmp_drl)
            step.unaffectAll()
            layer_obj = gen.Layer(step, tmp_drl)
            info = layer_obj.info2
            filter_symbols = set()
            for type, size in info.get('gTOOLtype'), info.get('gTOOLdrill_size'):
                if size > 1000:
                    filter_symbols.add('r%s' % size)
                    filter_symbols.add('s%s' % size)
            step.affect(tmp_drl)
            if filter_symbols:
                step.selectSymbol(';'.join(filter_symbols))
                step.selectReverse()
                if step.Selected_count():
                    step.selectDelete()
            else:
                step.removeLayer(tmp_drl)
                continue
            step.unaffectAll()
            step.affect(tmp_drl)
            for innersignalLayer in innersignalLayers:
                step.refSelectFilter(innersignalLayer, mode='disjoint')
                if step.Selected_count():
                    step.copyToLayer(innersignalLayer, size=-304.8)
            step.unaffectAll()
            step.removeLayer(tmp_drl)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    NV_job_add_inner_pad()
