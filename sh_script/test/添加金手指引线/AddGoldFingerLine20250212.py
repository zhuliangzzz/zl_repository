#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AddGoldFingerLine.py
   @author:zl
   @time: 2025/2/12 11:48
   @software:PyCharm
   @desc:添加金手指引线
"""
import os
import sys

import platform
from decimal import Decimal, ROUND_HALF_UP

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

from genesisPackages_zl import outsignalLayers
import genClasses_zl as gen
from PyQt4 import QtCore, QtGui

def AddGoldFingerLine():
    # spacing = 1.4
    dialog = QtGui.QInputDialog()
    spacing, status = dialog.getDouble(None, u"添加金手指引线", u"引线超出profile距离（mm）:", 1.4, 0, 100, 1)
    if not status:
        sys.exit()
    step.initStep()
    for outsignalLayer in outsignalLayers:
        # 用引线去找手指（不准确）
        tmp = '%s_finger+++' % outsignalLayer
        step.removeLayer(tmp)
        # 属性去找
        step.affect(outsignalLayer)
        step.setAttrFilter('.string', 'text=gf')
        step.selectAll()
        step.resetFilter()
        if step.Selected_count():
            step.copySel(tmp)
        else:
            step.unaffectAll()
            continue
        step.unaffectAll()
        # 判断手指位置 上下左右
        area = None
        # 框选区域判断
        step.affect(tmp)
        step.selectRectangle(step.profile2.xmin, step.profile2.ymin, step.profile2.xmax, step.profile2.ycenter)
        if step.Selected_count():
            step.selectReverse()
            if not step.Selected_count():
                area = 'b'
        if not area:
            step.selectRectangle(step.profile2.xmin, step.profile2.ycenter, step.profile2.xmax, step.profile2.ymax)
            if step.Selected_count():
                step.selectReverse()
                if not step.Selected_count():
                    area = 't'
        if not area:
            step.selectRectangle(step.profile2.xmin, step.profile2.ymin, step.profile2.xcenter, step.profile2.ymax)
            if step.Selected_count():
                step.selectReverse()
                if not step.Selected_count():
                    area = 'l'
        if not area:
            step.selectRectangle(step.profile2.xcenter, step.profile2.ymin, step.profile2.xmax, step.profile2.ymax)
            if step.Selected_count():
                step.selectReverse()
                if not step.Selected_count():
                    area = 'r'
        step.unaffectAll()
        if not area:
            QtGui.QMessageBox.warning(None, u'异常', u'未判断出手指方向')
        info = step.Features_INFO(tmp)
        step.affect(tmp)
        for d in info:
            x, y = float(d[1]), float(d[2])
            step.addAttr_zl('.n_electric')
            if area == 'b':
                step.addLine(x, y, x, step.profile2.ymin - spacing, 'r254', attributes='yes')
            elif area == 't':
                step.addLine(x, y, x, step.profile2.ymax + spacing, 'r254', attributes='yes')
            elif area == 'l':
                step.addLine(x, y, step.profile2.xmin - spacing, y, 'r254', attributes='yes')
            else:
                step.addLine(x, y, step.profile2.xmax + spacing, y, 'r254', attributes='yes')
            step.resetAttr()
        step.unaffectAll()
    QtGui.QMessageBox.information(None, u'运行完成', u'请查看:\n%s' % u'\n'.join(['%s_finger+++' % outsignalLayer for outsignalLayer in outsignalLayers]))
    exit()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    app.setStyleSheet('*{font:11pt;selection-background-color: transparent; selection-color:black;}')
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    if 'edit' not in job.stepsList:
        exit()
    step = gen.Step(job, 'edit')
    AddGoldFingerLine()
    sys.exit(app.exec_())
