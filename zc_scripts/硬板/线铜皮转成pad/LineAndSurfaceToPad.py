#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:LineAndSurfaceToPad.py
   @author:zl
   @time:2024/8/21 10:11
   @software:PyCharm
   @desc:
"""
import os
import sys

from PyQt5.QtWidgets import QMessageBox, QApplication
import genClasses as gen

def LineAndSurfaceToPad():
    tmp_lay = f'{workLay}+++{step.pid}'
    if step.Selected_count():
        step.moveSel(tmp_lay)
    step.clearAll()
    step.affect(tmp_lay)
    step.Contourize(0)
    step.cont2pad(max_size=25400)
    step.VOF()
    step.removeLayer(tmp_lay + '+++')
    step.VON()
    step.moveSel(workLay)
    step.unaffectAll()
    step.removeLayer(tmp_lay)
    step.display(workLay)
    QMessageBox.information(None, 'tips', '已转为pad')
    sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    jobname = os.environ.get('JOB')
    stepname = os.environ.get('STEP')
    if not stepname:
        QMessageBox.warning(None, '警告','请打开所在层执行')
        sys.exit()
    job = gen.Job(jobname)
    step = job.steps.get(stepname)
    step.COM('get_work_layer')
    workLay = step.COMANS
    if not workLay:
        QMessageBox.information(None, 'tips', '请选择工作层')
        sys.exit()
    step.COM('get_affect_layer')
    affectLays = step.COMANS.split()
    if len(affectLays) > 1:
        QMessageBox.information(None, 'tips', '不能选择多层')
        sys.exit()
    if workLay:
        if affectLays and affectLays[0] != workLay:
            QMessageBox.information(None, 'tips', '不能同时选择多个层')
            sys.exit()
    LineAndSurfaceToPad()