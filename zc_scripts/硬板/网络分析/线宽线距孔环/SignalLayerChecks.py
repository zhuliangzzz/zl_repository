#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:SignalLayerChecks.py
   @author:zl
   @time:2024/8/13 9:20
   @software:PyCharm
   @desc:
"""
import genClasses as gen
import os
import sys

from PyQt5.QtWidgets import QApplication, QMessageBox


class SignalLayerChecks:
    def __init__(self):
        pass

    def check(self):
        checklist_name = 'signal_layer_checks'
        checklist = gen.Checklist(step, checklist_name, 'valor_analysis_signal')
        checklayers = ';'.join(job.SignalLayers)
        checklist.action()
        params = {'pp_layer': checklayers, 'pp_spacing': '254', 'pp_r2c': '635', 'pp_d2c': '355.6', 'pp_sliver': '254',
                  'pp_min_pad_overlap': '127',
                  'pp_tests': 'Spacing\;Drill\;Rout\;Size\;Sliver\;Stubs\;Center\;SMD', 'pp_selected': 'All', 'pp_check_missing_pads_for_drills': 'Yes',
                  'pp_use_compensated_rout': 'No', 'pp_sm_spacing': 'No'}
        checklist.update(params=params)
        checklist.run()
        checklist.clear()
        checklist.update(params=params)
        checklist.copy()
        if checklist.name in step.checks:
            step.deleteCheck(checklist.name)
        step.createCheck(checklist.name)
        step.pasteCheck(checklist.name)
        result = []
        result.append('最小线宽：')
        for layer in job.SignalLayers:
            info = step.INFO(f'-t check -e %s/%s/%s -d MEAS -o action=1+category=line+layer={layer},units=mm' % (jobname, step.name, checklist.name))
            res = ''
            if info:
                res = min([float(l.split()[2]) for l in info])
            result.append(f"{layer}:{res}")
        result.append('最小线距：')
        for layer in job.SignalLayers:
            info = step.INFO(f'-t check -e %s/%s/%s -d MEAS -o action=1+category=spacing_length+layer={layer},units=mm' % (jobname, step.name, checklist.name))
            res = ''
            if info:
                res = min([float(l.split()[2]) for l in info])
            result.append(f"{layer}:{res}")
        result.append('最小孔环：')
        for layer in job.SignalLayers:
            info = step.INFO(f'-t check -e %s/%s/%s -d MEAS -o action=1+category=pth_ar+layer={layer},units=mm' % (jobname, step.name, checklist.name))
            res = ''
            if info:
                res = min([float(l.split()[2]) for l in info])
            result.append(f"{layer}:{res}")
        QMessageBox.information(None, '分析结果', '\n'.join(result))



if __name__ == '__main__':
    app = QApplication(sys.argv)
    jobname = os.environ.get('JOB')
    if not jobname:
        QMessageBox.warning(None, 'tips', '请打开料号')
        sys.exit()
    job = gen.Job(jobname)
    user = job.getUser()
    stepname = os.environ.get('STEP')
    if not stepname:
        QMessageBox.warning(None, 'tips', '请打开step')
        sys.exit()
    step = job.steps.get(stepname)
    slc = SignalLayerChecks()
    slc.check()