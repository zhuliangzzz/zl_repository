#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:UpdateScaleTestPadCoorTest.py
   @author:zl
   @time:2024/9/6 13:30
   @software:PyCharm
   @desc:
"""
import os
import genClasses as gen
import sys

from PyQt5.QtWidgets import QMessageBox, QApplication


def updateScaleTestPadCoor():
    step.COM('get_work_layer')
    workLay = step.COMANS
    if not workLay:
        QMessageBox.information(None, 'tips', '请选择工作层')
    step.clearAll()
    step.affect(workLay)
    step.selectSymbol('1-sc-mark')
    step.resetFilter()
    if step.Selected_count() != 4:
        QMessageBox.information(None, 'tips', '检查1-sc-mark是否是四个')
        sys.exit()
    info = step.Features_INFO(workLay, mode='select, units=mm')
    left_ = step.sr2.xmin
    right_ = step.sr2.xmax
    leftlist,rightlist = [], []
    for line in info:
        if float(line[1]) < left_:
            leftlist.append((float(line[1]), float(line[2])))
        if float(line[1]) > right_:
            rightlist.append((float(line[1]), float(line[2])))

    # 排序
    leftlist.sort(key=lambda x:x[1])
    rightlist.sort(key=lambda x:x[1])

    origin = leftlist[0]
    topleft = leftlist[1]
    topright = rightlist[1]
    botright = rightlist[0]

    # topleft
    y = topleft[1] - origin[1]
    step.clearSel()
    step.setFilterTypes('text')
    step.selectRectangle(topleft[0] - 2, topleft[1] + 0.8, topleft[0], topleft[1] - 0.8)
    if step.Selected_count() == 1:
        step.changeText(f'{y:g}')
    step.clearSel()
    y = topright[1] - origin[1]
    step.selectRectangle(topright[0], topright[1] + 0.8, topright[0] + 2, topright[1] - 0.8)
    if step.Selected_count() == 1:
        step.changeText(f'{y:g}')
    step.clearSel()
    x = botright[0] - origin[0]
    y = botright[1] - origin[1]
    step.selectRectangle(botright[0] - 1, botright[1], botright[0] + 1, botright[1] - 2)
    if step.Selected_count() == 1:
        step.changeText(f'{x:g}')
    step.clearSel()
    step.selectRectangle(botright[0], botright[1] - 1, botright[0] + 2, botright[1] + 1)
    step.changeText(f'{y:g}')
    step.resetFilter()
    step.unaffectAll()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    stepname = os.environ.get('STEP')
    step = job.steps.get(stepname)
    updateScaleTestPadCoor()