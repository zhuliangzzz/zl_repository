#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:SetDxfGenerator.py
   @author:zl
   @time:2024/8/28 13:11
   @software:PyCharm
   @desc:
   生成set图纸
"""
import datetime

import os
import shutil
import sys
import time

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox
import genClasses as gen
import res_rc


def setDxfGenerator():
    set_step = job.steps.get('set')
    pcs_step = job.steps.get('pcs')
    profile_layer = f'pcs_profile+++{pcs_step.pid}'
    profile_layer_ = f'set_profile+++{pcs_step.pid}'
    pcs_step.initStep()
    pcs_step.prof_to_rout(profile_layer, 100)
    pcs_step.affect(profile_layer)
    pcs_step.addPad(pcs_step.profile2.xcenter, pcs_step.profile2.ycenter, 'r100')
    pcs_step.unaffectAll()
    set_step.initStep()
    set_step.Flatten(profile_layer, profile_layer_)
    set_step.prof_to_rout(profile_layer_, 100)
    set_step.affect(job.SignalLayers[0])
    set_step.selectSymbol('r4000;r1038')
    if set_step.Selected_count():
        set_step.copySel(profile_layer_)
    set_step.unaffectAll()
    set_step.affect(profile_layer_)
    set_step.selectPolarity()
    set_step.unaffectAll()
    set_step.removeLayer(profile_layer)
    set_step.DxfOut(profile_layer_, output_path)
    set_step.removeLayer(profile_layer_)
    dxfname = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    shutil.move(f'{output_path}/{profile_layer_}.dxf', f'{output_path}/set_{dxfname}.dxf')
    QMessageBox.information(None,'tips',f'已导出到{output_path}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':res/demo.png'))
    app.setStyleSheet('QMessageBox,QPushButton{font:10pt;font-family:"微软雅黑"}')
    jobname = os.environ.get('JOB')
    if not jobname:
        QMessageBox.warning(None,'警告','请打开料号执行')
        sys.exit()
    job = gen.Job(jobname)
    if not job.steps.get('set') and not job.steps.get('pcs'):
        QMessageBox.warning(None, '警告', '没有set或没有pcs')
        sys.exit()
    output_path = f'D:/{jobname}/setdxf/'
    setDxfGenerator()