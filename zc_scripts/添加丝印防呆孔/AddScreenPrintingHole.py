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
    profile = f'profile+++{step.pid}'
    step.initStep()
    step.createLayer(sy)
    step.createLayer(profile)
    pnl_ = profile + '+++'
    step.createLayer(pnl_)
    step.affect(pnl_)
    step.srFill_2(sr_margin_x=-2540, sr_margin_y=-2540)
    step.unaffectAll()
    step.affect(profile)
    step.srFill_2(sr_margin_x=2, sr_margin_y=2)
    step.copySel(pnl_, 'yes')
    step.unaffectAll()
    step.removeLayer(profile)
    step.affect(pnl_)
    step.Contourize(0)
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
    step.setFilterTypes('line')
    step.selectAll()
    step.resetFilter()
    if step.Selected_count():
        step.selectDelete()
    step.clip_area(inout='outside', margin=0)
    step.refSelectFilter(pnl_)
    if step.Selected_count():
        step.selectDelete()
    step.removeLayer(pnl_)
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
    for i, signal in enumerate(job.SignalLayers):
        step.selectChange('sy-pin-b') if i % 2 else step.selectChange('sy-pin-t')
        step.copySel(signal)
    step.selectChange('r2500')
    for cov in job.matrix.returnRows('board', 'coverlay'):
        step.copySel(cov)
    step.clearAll()
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
