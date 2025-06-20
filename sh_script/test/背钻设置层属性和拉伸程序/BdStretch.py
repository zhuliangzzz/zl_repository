#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:BdStretch.py
   @author:zl
   @time: 2025/6/12 11:40
   @software:PyCharm
   @desc:
"""
import os
import re
import sys, platform


from PyQt4.QtCore import *
from PyQt4.QtGui import *

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen


class BdStretch(object):
    def __init__(self):
        self.job = gen.Job(jobname)
        self.step = gen.Step(self.job, stepname)
        self.bd_drills = list(filter(lambda row: re.match('bd\d+-\d+$', row), self.job.matrix.returnRows()))
        if not self.bd_drills:
            sys.exit()
        self.run()

    def run(self):
        self.step.initStep()
        for bd_drill in self.bd_drills:
            self.job.matrix.modifyRow(bd_drill, context='board', type='drill')
            s, e = bd_drill[2:].split('-')
            self.job.matrix.setDrillThrough(bd_drill, 'l%s' % s, 'l%s' % e)
        QMessageBox.information(None, 'tips', u'背钻定属性和拉伸执行完成，请检查~')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    jobname = os.environ.get('JOB')
    stepname = os.environ.get('STEP')
    BdStretch()

