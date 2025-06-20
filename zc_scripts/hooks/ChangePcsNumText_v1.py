#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:ChangePcsNumText.py
   @author:zl
   @time:2024/6/28 15:35
   @software:PyCharm
   @desc:
   修改pcs数量
"""
import os
import re
import sys
import genClasses as gen

from PyQt5.QtWidgets import QApplication, QMessageBox


def get_pcs_num():
    steps = step.info.get('gREPEATstep')  # 获取set列表
    pcs_num_map = {}
    pcs_name = set()
    for s in steps:
        if 'set' in s:
            pcs_list = job.steps.get(s).info.get('gREPEATstep')
            pcs_name.update(pcs_list)  # 获取每个set中的pcs列表
            if s not in pcs_num_map:
                pcs_num_map[s] = 0
            pcs_num_map[s] += len(pcs_list)
    if len(pcs_name) > 1:
        return min(pcs_num_map.values())
    else:
        return sum(pcs_num_map.values())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    if 'pnl' not in job.steps:
        sys.exit()
    step = job.steps.get('pnl')
    pcs_num = get_pcs_num()
    step.initStep()
    layers = job.matrix.returnRows('board', 'signal|silk_screen')
    [step.affect(layer) for layer in layers]
    step.setFilterTypes('text')
    step.setTextFilter('*pcs/pnl*')
    step.selectAll()
    step.resetFilter()
    if step.Selected_count():
        step.COM('get_message_bar')
        message = step.READANS
        result = re.search('=(\d+)PCS/PNL', message)
        num = int(result.group(1))
        if num != pcs_num:
            confirm = QMessageBox.warning(None, '修改pcs数字', f'检测到pcs数量有误，\n（{num} -> {pcs_num}）是否需要修改',
                                          QMessageBox.Ok | QMessageBox.Cancel)
            if confirm == QMessageBox.Ok:
                pcs_str = re.sub('=\d+PCS/PNL',f'={pcs_num}PCS/PNL', message.split(',')[5])
                step.changeText(pcs_str)
            else:
                sys.exit()
    step.resetFilter()
    step.unaffectAll()

