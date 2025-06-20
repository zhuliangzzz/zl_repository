#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AddScreenPrintingHole.py
   @author:zl
   @time:2024/7/8 13:11
   @software:PyCharm
   @desc:添加丝印防呆孔
"""
import os
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox
import genClasses as gen
import res_rc

def AddScreenPrintingHole():
    drills = job.matrix.returnRows('board', 'drill')
    sy = f'sy+++{step.pid}'
    pcs_profile = f'pcs_profile+++{step.pid}'
    pcs_step = job.steps.get('pcs')
    pcs_step.initStep()
    pcs_step.prof_to_rout(pcs_profile)
    pcs_step.affect(pcs_profile)
    pcs_step.selectCutData()
    pcs_step.selectResize(4000)
    pcs_step.unaffectAll()
    pcs_step.close()
    step.initStep()
    step.createLayer(sy)
    pnl_ = pcs_profile + '+++'
    step.Flatten(pcs_profile, pnl_)
    step.affect(pnl_)
    step.addRectangle(step.profile2.xmin, step.profile2.ymax, step.profile2.xmax, step.profile2.ymax - 35)
    step.addRectangle(step.profile2.xmin, step.profile2.ymin, step.profile2.xmax, step.profile2.ymin + 35)
    step.unaffectAll()
    if drills:
        for drill in drills:
            step.affect(drill)
        tmp_drill = f'drill+++{step.pid}'
        step.copyToLayer(tmp_drill)
        step.unaffectAll()
        step.affect(tmp_drill)
        step.selectBreak()
        step.selectResize(40000)
        step.copyToLayer(pnl_)
        step.unaffectAll()
        step.removeLayer(tmp_drill)
    step.affect(sy)
    step.addPad(step.profile2.xcenter, step.profile2.ycenter, '1-sy')
    step.selectBreak()
    step.refSelectFilter(pnl_)
    if step.Selected_count():
        step.selectDelete()
    step.display(sy)
    QMessageBox.information(None, '确认', "选择一个孔作为丝印防呆孔")
    while True:
        step.PAUSE('select a pad')
        if step.Selected_count() == 1:
            step.selectReverse()
            step.selectDelete()
            break
        else:
            QMessageBox.information(None, 'info', "选择的孔数量不为1,请重新选择")
    step.clearSel()
    step.selectChange('sy-pin-t')
    for signal in job.SignalLayers:
        step.copySel(signal)
    step.selectChange('r2500')
    for cov in job.matrix.returnRows('board', 'coverlay'):
        step.copySel(cov)
    step.clearAll()
    step.removeLayer(pcs_profile)
    step.removeLayer(pnl_)
    step.removeLayer(sy)
    QMessageBox.information(None, 'info', "执行完成!")
    sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(':res/demo.png'))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    if 'pnl' not in job.steps:
        QMessageBox.infomation(None, '提示', '没有pnl')
        sys.exit()
    step = job.steps.get('pnl')
    AddScreenPrintingHole()
