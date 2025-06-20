#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:update_symbol.py
   @author:zl
   @time:2024/7/31 13:59
   @software:PyCharm
   @desc:
"""
import os
import sys

from PyQt5.QtGui import QIcon
import genClasses as gen

from PyQt5.QtWidgets import QMessageBox, QApplication


def update(symbolName):
    job.COM(f'open_entity,job={jobname},type=symbol,name={symbolName},iconic=no')
    job.AUX(f'set_group,group={job.COMANS}')
    job.COM('sel_clear_feat')
    job.COM('filter_set,filter_name=popup,update_popup=no,feat_types=text')
    job.COM('filter_area_strt')
    job.COM('filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no')
    job.COM(
        f'sel_change_txt,text=BK1-{len(job.SignalLayers)},x_size=-25.4,y_size=-25.4,w_factor=-1,polarity=no_change,angle=-1,mirror=no,fontname=simplex')
    job.COM('editor_page_close')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # app.setStyle('fusion')
    app.setWindowIcon(QIcon(":res/demo.png"))
    jobname = os.environ.get('JOB')
    if not jobname:
        QMessageBox.information(None, '提示', '请打开料号！')
        sys.exit()
    job = gen.Job(jobname)
    update('x-ray')
