#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:ClearCornerLine.py
   @author:zl
   @time:2024/8/6 13:20
   @software:PyCharm
   @desc:喷印清除pnl角边框线和fxk  (框选）
"""
import os
import sys

from PyQt5.QtWidgets import QMessageBox, QApplication

import genClasses as gen


def ClearCornerLine():
    step.initStep()
    for silkscreen in silkscreens:
        step.affect(silkscreen)
    step.selectRectangle(step.profile2.xmin - 0.1, step.profile2.ymin - 0.1, step.profile2.xmin + 5.1,
                         step.profile2.ymin + 5.1)
    step.selectRectangle(step.profile2.xmin - 0.1, step.profile2.ymax + 0.1, step.profile2.xmin + 16.1,
                         step.profile2.ymax - 5.1)
    step.selectRectangle(step.profile2.xmax + 0.1, step.profile2.ymax + 0.1, step.profile2.xmax - 5.1,
                         step.profile2.ymax - 5.1)
    step.selectRectangle(step.profile2.xmax + 0.1, step.profile2.ymin - 0.1, step.profile2.xmax - 5.1,
                         step.profile2.ymin + 5.1)
    if step.Selected_count():
        step.selectDelete()
    step.unaffectAll()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    jobname = os.environ.get('JOB')
    stepname = os.environ.get('STEP')
    if not stepname:
        QMessageBox.warning(None, '提示', '请打开step执行')
        sys.exit()
    if stepname != 'pnl':
        sys.exit()
    job = gen.Job(jobname)
    silkscreens = job.matrix.returnRows('board', 'silk_screen')
    if not silkscreens:
        sys.exit()
    step = job.steps.get(stepname)
    ClearCornerLine()
