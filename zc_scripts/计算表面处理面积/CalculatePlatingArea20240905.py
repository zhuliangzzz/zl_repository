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
   20240723 覆盖膜的set切割线删除
"""
import os
import sys

from PyQt5.QtWidgets import QApplication, QMessageBox
import genClasses as gen


def do_usestep(name):
    everysteps = []

    def do_every_step(job, stepname):
        infoDict = job.DO_INFO(' -t step -e %s/%s -d REPEAT,units=mm' % (jobname, stepname))
        if infoDict['gREPEATstep']:
            stepArr = set(infoDict['gREPEATstep'])
            for s in stepArr:
                everysteps.append(str(s))
                do_every_step(job, str(s))

    do_every_step(job, name)
    return set(everysteps)


def calculatePlatingArea():
    mix_top = 'mixtop'
    mix_bot = 'mixbot'
    pnl_step = job.steps.get('pnl')
    usestep = do_usestep(pnl_step.name)
    if pnl_step.isLayer('gts') and pnl_step.isLayer('c1'):
        if not pnl_step.isLayer('yy1'):
            QMessageBox.warning(None, '提示', '有阻焊和覆盖膜,缺失yy1！')
            sys.exit()
    if pnl_step.isLayer('gbs') and pnl_step.isLayer('c2'):
        if not pnl_step.isLayer('yy2'):
            QMessageBox.warning(None, '提示', '有阻焊和覆盖膜,缺失yy2！')
            sys.exit()
    pnl_step.VOF()
    pnl_step.removeLayer(mix_top)
    pnl_step.VON()
    pnl_step.createLayer(mix_top)
    cov, sm, yy = 'c1', 'gts', 'yy1'
    # top
    for stepname in usestep:
        step = job.steps.get(stepname)
        if pnl_step.isLayer(sm) and pnl_step.isLayer(cov):
            if 'set' in stepname:
                step.initStep()
                step.affect(cov)
                step.copySel(mix_top)
                step.unaffectAll()
                step.close()
            elif 'pcs' in stepname:
                step.initStep()
                step.affect(cov)
                step.refSelectFilter2(yy, mode='cover', polarity='positive')
                tmp_cov = f'{cov}+++{step.pid}'
                if step.Selected_count():
                    step.copySel(tmp_cov)
                    step.refSelectFilter2(yy, mode='cover', polarity='positive')
                    step.selectReverse()
                    if step.Selected_count():
                        step.copySel(mix_top)
                    # 把profile1mm外的去掉
                    step.unaffectAll()
                    # profile
                    tmp_profile = f'profile+++{step.pid}'
                    step.createLayer(tmp_profile)
                    step.affect(tmp_profile)
                    step.srFill_2()
                    step.selectResize(2000)
                    step.unaffectAll()
                    step.affect(tmp_cov)
                    step.refSelectFilter(tmp_profile, mode='cover')
                    if step.Selected_count():
                        step.selectReverse()
                        if step.Selected_count():
                            step.moveSel(mix_top)
                    step.unaffectAll()
                    step.affect(sm)
                    step.refSelectFilter(tmp_cov, mode='cover')
                    if step.Selected_count():
                        step.copySel(mix_top)
                    step.unaffectAll()
                    step.removeLayer(tmp_profile)
                else:
                    step.selectReverse()
                    if step.Selected_count():
                        step.copySel(mix_top)
                    step.unaffectAll()
                step.close()
            else:
                step.initStep()
                step.affect(cov)
                step.refSelectFilter2(yy, mode='cover', polarity='positive')
                tmp_cov = f'{cov}+++{step.pid}'
                if step.Selected_count():
                    step.copySel(tmp_cov)
                    step.refSelectFilter2(yy, mode='cover', polarity='positive')
                    step.selectReverse()
                    if step.Selected_count():
                        step.copySel(mix_top)
                    step.unaffectAll()
                    step.affect(sm)
                    step.refSelectFilter(tmp_cov, mode='cover')
                    if step.Selected_count():
                        step.copySel(mix_top)
                    step.unaffectAll()
                else:
                    step.selectReverse()
                    if step.Selected_count():
                        step.copySel(mix_top)
                    step.unaffectAll()
                step.close()
        elif pnl_step.isLayer(sm) or pnl_step.isLayer(cov):
            tl = sm if pnl_step.isLayer(sm) else cov
            step.initStep()
            step.affect(tl)
            step.copySel(mix_top)
            step.unaffectAll()
            step.close()
    if pnl_step.isLayer(sm) and pnl_step.isLayer(cov):
        pnl_step.initStep()
        pnl_step.affect(cov)
        pnl_step.refSelectFilter2(yy, mode='cover', polarity='positive')
        if pnl_step.Selected_count():
            pnl_step.copySel(tmp_cov)
            pnl_step.refSelectFilter2(yy, mode='cover', polarity='positive')
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
        pnl_step.initStep()
        pnl_step.affect(tl)
        pnl_step.copySel(mix_top)
        pnl_step.unaffectAll()
    # bot
    pnl_step.VOF()
    pnl_step.removeLayer(mix_bot)
    pnl_step.VON()
    pnl_step.createLayer(mix_bot)
    cov, sm, yy = 'c2', 'gbs', 'yy2'
    for stepname in usestep:
        step = job.steps.get(stepname)
        if pnl_step.isLayer(sm) and pnl_step.isLayer(cov):
            if 'set' in stepname:
                step.initStep()
                step.affect(cov)
                step.copySel(mix_bot)
                step.unaffectAll()
                step.close()
            elif 'pcs' in stepname:
                step.initStep()
                step.affect(cov)
                step.refSelectFilter2(yy, mode='cover', polarity='positive')
                tmp_cov = f'{cov}+++{step.pid}'
                if step.Selected_count():
                    step.copySel(tmp_cov)
                    step.refSelectFilter2(yy, mode='cover', polarity='positive')
                    step.selectReverse()
                    if step.Selected_count():
                        step.copySel(mix_bot)
                    # 把profile1mm外的去掉
                    step.unaffectAll()
                    # profile
                    tmp_profile = f'profile+++{step.pid}'
                    step.createLayer(tmp_profile)
                    step.affect(tmp_profile)
                    step.srFill_2()
                    step.selectResize(2000)
                    step.unaffectAll()
                    step.affect(tmp_cov)
                    step.refSelectFilter(tmp_profile, mode='cover')
                    if step.Selected_count():
                        step.selectReverse()
                        if step.Selected_count():
                            step.moveSel(mix_bot)
                    step.unaffectAll()
                    step.affect(sm)
                    step.refSelectFilter(tmp_cov, mode='cover')
                    if step.Selected_count():
                        step.copySel(mix_bot)
                    step.unaffectAll()
                    step.removeLayer(tmp_profile)
                else:
                    step.selectReverse()
                    if step.Selected_count():
                        step.copySel(mix_bot)
                    step.unaffectAll()
                step.close()
            else:
                step.initStep()
                step.affect(cov)
                step.refSelectFilter2(yy, mode='cover', polarity='positive')
                tmp_cov = f'{cov}+++{step.pid}'
                if step.Selected_count():
                    step.copySel(tmp_cov)
                    step.refSelectFilter2(yy, mode='cover', polarity='positive')
                    step.selectReverse()
                    if step.Selected_count():
                        step.copySel(mix_bot)
                    step.unaffectAll()
                    step.affect(sm)
                    step.refSelectFilter(tmp_cov, mode='cover')
                    if step.Selected_count():
                        step.copySel(mix_bot)
                    step.unaffectAll()
                else:
                    step.selectReverse()
                    if step.Selected_count():
                        step.copySel(mix_bot)
                    step.unaffectAll()
                step.close()
        elif pnl_step.isLayer(sm) or pnl_step.isLayer(cov):
            tl = sm if pnl_step.isLayer(sm) else cov
            step.initStep()
            step.affect(tl)
            step.copySel(mix_bot)
            step.unaffectAll()
            step.close()
    if pnl_step.isLayer(sm) and pnl_step.isLayer(cov):
        pnl_step.initStep()
        pnl_step.affect(cov)
        pnl_step.refSelectFilter2(yy, mode='cover', polarity='positive')
        if pnl_step.Selected_count():
            pnl_step.copySel(tmp_cov)
            pnl_step.refSelectFilter2(yy, mode='cover', polarity='positive')
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
        pnl_step.initStep()
        pnl_step.affect(tl)
        pnl_step.copySel(mix_bot)
        pnl_step.unaffectAll()
    # 去除mixtop/mixbot边框线
    pnl_profile = f'pnl_profile+++{pnl_step.pid}'
    pnl_step.prof_to_rout(pnl_profile, 105)
    pnl_step.affect(mix_top)
    pnl_step.affect(mix_bot)
    pnl_step.refSelectFilter(pnl_profile)
    if pnl_step.Selected_count():
        pnl_step.selectDelete()
    pnl_step.selectPolarity()
    pnl_step.unaffectAll()
    pnl_step.removeLayer(pnl_profile)
    # 刷新matrix
    job.matrix.refresh()
    # ccd钻孔
    drill_list = ['f1'] if pnl_step.isLayer('f1') else []
    if pnl_step.isLayer('ccd1'):
        job.matrix.modifyRow('ccd1', context='board', type='drill')
        drill_list.append('ccd1')
    pnl_step.initStep()
    top_signal, bot_signal = job.SignalLayers[0], job.SignalLayers[-1]
    pnl_step.COM(
        f'exposed_area,layer1={top_signal},mask1={mix_top},layer2=,mask2=,mask_mode=or,drills=yes,consider_rout=no,ignore_pth_no_pad=no,drills_source=matrix,drills_list={";".join(drill_list)},thickness=0,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes')
    area, percent = pnl_step.COMANS.split()
    text = f'AU:{"%.2f" % float(area)}SQ/MM({"%.2f" % float(percent)}%)'
    pnl_step.affect(top_signal)
    pnl_step.setFilterTypes('text')
    pnl_step.setTextFilter('*SQ/MM*')
    pnl_step.selectAll()
    pnl_step.resetFilter()
    if pnl_step.Selected_count():
        pnl_step.changeText(text)
    else:
        mir = 'no'
        x, y = 52, step.sr2.ymin - 2
        pnl_step.addText(x, y, text, 1, 1.2, 0.492125988, mir, fontname='simple', polarity='negative')
    pnl_step.unaffectAll()
    pnl_step.COM(
        f'exposed_area,layer1={bot_signal},mask1={mix_bot},layer2=,mask2=,mask_mode=or,drills=yes,consider_rout=no,ignore_pth_no_pad=no,drills_source=matrix,drills_list={";".join(drill_list)},thickness=0,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes')
    area, percent = pnl_step.COMANS.split()
    text = f'AU:{"%.2f" % float(area)}SQ/MM({"%.2f" % float(percent)}%)'
    pnl_step.affect(bot_signal)
    pnl_step.setFilterTypes('text')
    pnl_step.setTextFilter('*SQ/MM*')
    pnl_step.selectAll()
    pnl_step.resetFilter()
    if pnl_step.Selected_count():
        pnl_step.changeText(text)
    else:
        mir = 'yes'
        x, y = 70, step.sr2.ymin - 2
        pnl_step.addText(x, y, text, 1, 1.2, 0.492125988, mir, fontname='simple', polarity='negative')
    pnl_step.unaffectAll()
    for dk in ('dkt', 'dkb'):
        if pnl_step.isLayer(dk):
            pnl_step.COM(
                f'copper_area,layer1={dk},layer2=,drills=yes,consider_rout=no,ignore_pth_no_pad=no,drills_source=matrix,thickness=0,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes')
            area, percent = pnl_step.COMANS.split()
            text = f'CU:{"%.2f" % float(area)}SQ/MM({"%.2f" % float(percent)}%)'
            pnl_step.affect(dk)
            pnl_step.setFilterTypes('text')
            pnl_step.setTextFilter('*SQ/MM*')
            pnl_step.selectAll()
            pnl_step.resetFilter()
            if pnl_step.Selected_count():
                pnl_step.changeText(text)
            else:
                x, mir = 70, 'yes'
                if dk == 'dkt':
                    x, mir = 52, 'no'
                y = step.sr2.ymin - 2
                pnl_step.addText(x, y, text, 1, 1.2, 0.492125988, mir, fontname='simple', polarity='negative')
            pnl_step.unaffectAll()
    QMessageBox.information(None, '提示', '执行完成!')
    sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    jobname = os.environ.get('JOB')
    if not jobname:
        QMessageBox.warning(None, '提示', '请先打开料号')
        sys.exit()
    job = gen.Job(jobname)
    if 'pnl' not in job.steps:
        QMessageBox.warning(None, '提示', '该料号没有pnl')
        sys.exit()
    calculatePlatingArea()
