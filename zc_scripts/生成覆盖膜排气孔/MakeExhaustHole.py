#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:MakeExhaustHole.py
   @author:zl
   @time:2024/7/8 8:23
   @software:PyCharm
   @desc:生成排气孔
"""
import os
import genClasses as gen
import sys

from PyQt5.QtWidgets import QMessageBox, QApplication


def makeExhaustHole():
    covs = job.matrix.returnRows('board', 'coverlay')
    if not covs:
        QMessageBox.infomation(None, '提示', '没有覆盖膜层')
        sys.exit()
    step.initStep()
    tmp = f'tmp+++{step.pid}'
    step.prof_to_rout(tmp, 100)
    step.affect(tmp)
    step.selectAll()
    step.COM(
        f'sel_offset_poly,method=by_distance,x={step.profile2.xmin - 10},y=15.6373775,distance=1750,keep_orig=no,reselect=yes,sym_size=1500,lines_num=1')
    # step.COM('sel_line2dash,seg_len=0,gap_len=10000,min_gap_len=0,mode=break,preserve_ends=no')
    step.COM('sel_line2dash,seg_len=0,gap_len=10000,mode=gap')  # 远程的genesis这个命令有点不一样
    step.setFilterTypes('arc')
    step.selectAll()
    step.resetFilter()
    if step.Selected_count():
        step.selectDelete()
    step.selectLineToPad()
    step.unaffectAll()
    step.affect(tmp)
    for cov in covs:
        step.copySel(f'{cov}-pq')
    step.unaffectAll()
    for cov in covs:
        step.affect(cov)
        step.copyToLayer(f'{cov}+++{step.pid}', size=10000)
        step.unaffectAll()
    for cov in covs:
        step.affect(f'{cov}-pq')
        step.refSelectFilter(f'{cov}+++{step.pid}')
        if step.Selected_count():
            step.selectDelete()
        step.unaffectAll()
        step.removeLayer(f'{cov}+++{step.pid}')
    step.removeLayer(tmp)
    QMessageBox.information(None, '提示', '已跑完，生成排气孔层 %s' % '、'.join([f"{cov}-pq" for cov in covs]))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    if 'pcs' not in job.steps:
        QMessageBox.infomation(None, '提示', '没有pcs')
        sys.exit()
    step = job.steps.get('pcs')
    makeExhaustHole()
