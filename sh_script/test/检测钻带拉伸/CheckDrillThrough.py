#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CheckDrillThrough.py
   @author:zl
   @time: 2025/2/25 11:12
   @software:PyCharm
   @desc:
"""
import os
import re
import sys
import platform

from PyQt4 import QtGui

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

from genesisPackages_zl import tongkongDrillLayer, mai_drill_layers, laser_drill_layers, outsignalLayers
import genClasses_zl as gen


class CheckDrillThrough(object):
    def __init__(self):
        self.job = gen.Job(jobname)
        self.check()

    def check(self):
        matrix_ = self.job.matrix.getInfo()
        drill_dict = {}
        outsignal_rows = []
        for row, name, start, end in zip(matrix_['gROWrow'], matrix_['gROWname'], matrix_['gROWdrl_start'],
                                         matrix_['gROWdrl_end']):
            if name in tongkongDrillLayer + mai_drill_layers + laser_drill_layers:
                drill_dict[name] = [start, end]
            # 找外层线路的row
            if name in outsignalLayers:
                outsignal_rows.append(row)
        err_layers = []
        for layer, start_end in drill_dict.items():
            start, end = start_end[0], start_end[1]
            if layer in tongkongDrillLayer:
                # 判断是第几行
                row_start = filter(lambda t: t[1] == start, zip(matrix_['gROWrow'], matrix_['gROWname']))[0][0]
                row_end = filter(lambda t: t[1] == end, zip(matrix_['gROWrow'], matrix_['gROWname']))[0][0]
                if row_start < row_end:  # 从上往下
                    if row_start > outsignal_rows[0] or row_end < outsignal_rows[1]:
                        err_layers.append(layer)
                else:  # 从下往上
                    if row_start < outsignal_rows[1] or row_end > outsignal_rows[0]:
                        err_layers.append(layer)
            else:
                layer_ = re.sub('[sb]', '', layer)
                start_, end_ = ['l%s' % n for n in layer_.split('-')]
                # if start != start_ or end != end_:
                if (start_ in (start, end) or any([start_ + '-ls' in i for i in (start, end)])) and (end_ in (start, end) or any([end_ + '-ls' in i for i in (start, end)])):
                    pass
                else:
                    err_layers.append(layer)
        if err_layers:
            QtGui.QMessageBox.warning(None, u'提醒', u'检测到钻带贯穿层异常:\n%s\n请手动调整后再运行' % u'、'.join(err_layers))
            sys.exit(-1)
        sys.exit(0)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    jobname = os.environ.get('JOB')
    CheckDrillThrough()
