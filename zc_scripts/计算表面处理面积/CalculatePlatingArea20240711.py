#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CalculatePlatingArea.py
   @author:zl
   @time:2024/7/10 17:02
   @software:PyCharm
   @desc:生成mixtop pcs/pnl: yy cover 覆盖膜 和未cover的(放mixtop)  cover的去cover 阻焊层，被cover的复制到mixtop
   set的直接复制覆盖膜层或阻焊层到mixtop
   反面为mixbot
"""
import os
import sys

from PyQt5.QtWidgets import QApplication, QMessageBox
import genClasses as gen


def calculatePlatingArea():
    mix_top = 'mixtop'
    mix_bot = 'mixbot'
    pnl_step = job.steps.get('pnl')
    set_step = job.steps.get('set')
    pcs_step = job.steps.get('pcs')
    if pnl_step.isLayer('gts') and pnl_step.isLayer('c1'):
        if not pnl_step.isLayer('yy1'):
            QMessageBox.warning(None, '提示', '有阻焊和覆盖膜,缺失yy1！')
            sys.exit()
    if pnl_step.isLayer('gbs') and pnl_step.isLayer('c2'):
        if not pnl_step.isLayer('yy2'):
            QMessageBox.warning(None, '提示', '有阻焊和覆盖膜,缺失yy2！')
            sys.exit()
    # top
    pcs_step.VOF()
    pcs_step.removeLayer(mix_top)
    pcs_step.VON()
    pcs_step.createLayer(mix_top)
    cov, sm, yy = 'c1', 'gts', 'yy1'
    if pnl_step.isLayer(sm) and pnl_step.isLayer(cov):
        pcs_step.initStep()
        pcs_step.affect(cov)
        pcs_step.refSelectFilter(yy, mode='cover')
        tmp_cov = f'{cov}+++{pcs_step.pid}'
        if pcs_step.Selected_count():
            pcs_step.copySel(tmp_cov)
            pcs_step.refSelectFilter(yy, mode='cover')
            pcs_step.selectReverse()
            if pcs_step.Selected_count():
                pcs_step.copySel(mix_top)
            pcs_step.unaffectAll()
            pcs_step.affect(sm)
            pcs_step.refSelectFilter(tmp_cov, mode='cover')
            if pcs_step.Selected_count():
                pcs_step.copySel(mix_top)
            pcs_step.unaffectAll()
        else:
            pcs_step.selectReverse()
            if pcs_step.Selected_count():
                pcs_step.copySel(mix_top)
            pcs_step.unaffectAll()
        pcs_step.close()
        set_step.initStep()
        set_step.affect(cov)
        set_step.copySel(mix_top)
        set_step.unaffectAll()
        set_step.close()
        pnl_step.initStep()
        pnl_step.affect(cov)
        pnl_step.refSelectFilter(yy, mode='cover')
        if pnl_step.Selected_count():
            pnl_step.copySel(tmp_cov)
            pnl_step.refSelectFilter(yy, mode='cover')
            pnl_step.selectReverse()
            if pnl_step.Selected_count():
                pnl_step.copySel(mix_top)
            pnl_step.unaffectAll()
            pnl_step.affect(sm)
            pnl_step.refSelectFilter(tmp_cov, mode='cover')
            if pnl_step.Selected_count():
                pnl_step.copySel(mix_top)
            pnl_step.unaffectAll()
        else:
            pnl_step.selectReverse()
            if pnl_step.Selected_count():
                pnl_step.copySel(mix_top)
            pnl_step.unaffectAll()
        pnl_step.VOF()
        pnl_step.removeLayer(tmp_cov)
        pnl_step.VON()
    elif pnl_step.isLayer(sm) or pnl_step.isLayer(cov):
        tl = sm if pnl_step.isLayer(sm) else cov
        pcs_step.initStep()
        pcs_step.affect(tl)
        pcs_step.copySel(mix_top)
        pcs_step.unaffectAll()
        pcs_step.close()
        set_step.initStep()
        set_step.affect(tl)
        set_step.copySel(mix_top)
        set_step.unaffectAll()
        set_step.close()
        pnl_step.initStep()
        pnl_step.affect(tl)
        pnl_step.copySel(mix_top)
        pnl_step.unaffectAll()
        # pnl_step.close()
    # bot
    pcs_step.VOF()
    pcs_step.removeLayer(mix_bot)
    pcs_step.VON()
    pcs_step.createLayer(mix_bot)
    cov, sm, yy = 'c2', 'gbs', 'yy2'
    if pnl_step.isLayer(sm) and pnl_step.isLayer(cov):
        pcs_step.initStep()
        pcs_step.affect(cov)
        tmp_cov = f'{cov}+++{pcs_step.pid}'
        pcs_step.refSelectFilter(yy, mode='cover')
        if pcs_step.Selected_count():
            pcs_step.copySel(tmp_cov)
            pcs_step.refSelectFilter(yy, mode='cover')
            pcs_step.selectReverse()
            if pcs_step.Selected_count():
                pcs_step.copySel(mix_bot)
            pcs_step.unaffectAll()
            pcs_step.affect(sm)
            pcs_step.refSelectFilter(tmp_cov, mode='cover')
            if pcs_step.Selected_count():
                pcs_step.copySel(mix_bot)
            pcs_step.unaffectAll()
        else:
            pcs_step.selectReverse()
            if pcs_step.Selected_count():
                pcs_step.copySel(mix_bot)
            pcs_step.unaffectAll()
        pcs_step.close()
        set_step.initStep()
        set_step.affect(cov)
        set_step.copySel(mix_bot)
        set_step.unaffectAll()
        set_step.close()
        pnl_step.initStep()
        pnl_step.affect(cov)
        pnl_step.refSelectFilter(yy, mode='cover')
        if pnl_step.Selected_count():
            pnl_step.copySel(tmp_cov)
            pnl_step.refSelectFilter(yy, mode='cover')
            pnl_step.selectReverse()
            if pnl_step.Selected_count():
                pnl_step.copySel(mix_bot)
            pnl_step.unaffectAll()
            pnl_step.affect(sm)
            pnl_step.refSelectFilter(tmp_cov, mode='cover')
            if pnl_step.Selected_count():
                pnl_step.copySel(mix_bot)
            pnl_step.unaffectAll()
        else:
            pnl_step.selectReverse()
            if pnl_step.Selected_count():
                pnl_step.copySel(mix_bot)
            pnl_step.unaffectAll()
        pnl_step.VOF()
        pnl_step.removeLayer(tmp_cov)
        pnl_step.VON()
    elif pnl_step.isLayer(sm) or pnl_step.isLayer(cov):
        tl = sm if pnl_step.isLayer(sm) else cov
        pcs_step.initStep()
        pcs_step.affect(tl)
        pcs_step.copySel(mix_bot)
        pcs_step.unaffectAll()
        pcs_step.close()
        set_step.initStep()
        set_step.affect(tl)
        set_step.copySel(mix_bot)
        set_step.unaffectAll()
        set_step.close()
        pnl_step.initStep()
        pnl_step.affect(tl)
        pnl_step.copySel(mix_bot)
        pnl_step.unaffectAll()
        # pnl_step.close()

    QMessageBox.information(None, '提示', '执行完成!')
    sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    jobname = os.environ.get('JOB')
    if not jobname:
        QMessageBox.warning(None, '提示', '请先打开料号')
        sys.exit()
    job = gen.Job(jobname)
    if 'pcs' not in job.steps or 'set' not in job.steps or 'pnl' not in job.steps:
        QMessageBox.warning(None, '提示', '需要有pcs、set、pnl')
        sys.exit()
    calculatePlatingArea()
