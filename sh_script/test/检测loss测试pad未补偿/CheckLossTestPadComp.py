#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CheckLossTestPadComp.py
   @author:zl
   @time: 2025/3/5 16:30
   @software:PyCharm
   @desc:
"""
import os
import sys
import platform
import time

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")


import genClasses_zl as gen

from genesisPackages_zl import get_layer_selected_limits


class CheckLossTestPadComp(object):
    def __init__(self):
        self.back_path = '/windows/174.db/'
        self.logfile = os.path.join(self.back_path, 'check_loss_test_pad_comp.txt')
        self.job = gen.Job(jobname)
        self.check_time = time.strftime('%Y-%m-%d %H:%M:%S')
        self.run()

    def run(self):
        if jobname not in gen.Top().listJobs():
            with open(self.logfile, 'a') as writer:
                    writer.write('[%s]Job %s: not exists\n' % (self.check_time, jobname))
            sys.exit()
        self.job.open(0)
        stepname = 'loss'
        step = gen.Step(self.job, stepname)
        step.initStep()
        arraylist = []
        lay_num = int(jobname[4:6])
        check_layers = {'l1': 'l2', 'l%s' % lay_num: 'l%s' % (lay_num - 1)}
        for outsignal, second_outsignal in check_layers.items():
            loss_stub_outer_areas = []
            tmp_outsignal = '%s+++check_loss_test_pad' % outsignal
            step.removeLayer(tmp_outsignal)
            step.affect(outsignal)
            step.selectSymbol('loss_stub_outer_v4')
            step.resetFilter()
            if step.Selected_count():
                step.copySel(tmp_outsignal)
                step.unaffectAll()
                step.affect(tmp_outsignal)
                step.selectAll()
                layer_obj = gen.Layer(step, tmp_outsignal)
                feats = layer_obj.featout_dic_Index()['pads']
                step.clearSel()
                for feat in feats:
                    step.selectByIndex(tmp_outsignal, feat.feat_index)
                    xmin, ymin, xmax, ymax = get_layer_selected_limits(step, tmp_outsignal)
                    loss_stub_outer_areas.append([xmin - 0.05, ymin - 0.05, xmax + 0.05, ymax + 0.05])
                    step.clearSel()
            else:
                step.unaffectAll()
                continue
            step.unaffectAll()
            step.truncate(tmp_outsignal)
            step.affect(tmp_outsignal)
            for area in loss_stub_outer_areas:
                step.addRectangle(area[0], area[1], area[2], area[3])
            step.unaffectAll()
            ids = []
            step.affect(outsignal)
            step.setSymbolFilter('rect*')
            step.refSelectFilter(tmp_outsignal, mode='cover')
            step.resetFilter()
            if step.Selected_count():
                layer_obj = gen.Layer(step, outsignal)
                feats = layer_obj.featout_dic_Index('feat_index+select')['pads']
                for feat in feats:
                    if feat.symbol in ('rect20x8', 'rect20x12'):
                        ids.append(feat.feat_index)
            step.unaffectAll()
            if ids:
                step.affect(outsignal)
                [step.selectByIndex(outsignal, id) for id in ids]
                log = "step:{0} 检测到{1}层测试pad未补偿！".format(step.name, outsignal)
                arraylist.append(log)
                step.unaffectAll()
            # 掏开
            ids = []
            step.affect(second_outsignal)
            step.setSymbolFilter('rect*')
            step.refSelectFilter(tmp_outsignal, mode='cover')
            step.resetFilter()
            if step.Selected_count():
                layer_obj = gen.Layer(step, second_outsignal)
                feats = layer_obj.featout_dic_Index('feat_index+select')['pads']
                for feat in feats:
                    if feat.symbol in ('rect20x8', 'rect20x12'):
                        ids.append(feat.feat_index)
            step.unaffectAll()
            if ids:
                step.affect(second_outsignal)
                [step.selectByIndex(second_outsignal, id) for id in ids]
                log = "step:{0} 检测到{1}层未补偿掏开！".format(step.name, second_outsignal)
                arraylist.append(log)
                step.unaffectAll()
        self.job.close(0)
        with open(self.logfile, 'a') as writer:
            if arraylist:
                writer.write('[%s]Job %s: %s\n' % (self.check_time, jobname, '\n'.join(arraylist)))
            else:
                writer.write('[%s]Job %s: check ok\n' % (self.check_time, jobname))


if __name__ == '__main__':
    jobname = sys.argv[1]
    CheckLossTestPadComp()