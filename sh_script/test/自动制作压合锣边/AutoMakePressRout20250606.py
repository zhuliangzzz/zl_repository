#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AutoMakePressRout.py
   @author:zl
   @time: 2025/6/6 9:40
   @software:PyCharm
   @desc:
"""
import os
import platform
import re
import sys

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen
from genesisPackages_zl import get_layer_limits
from get_erp_job_info import get_inplan_mrp_info, get_inplan_all_flow


class AutoMakePressRout(object):
    def __init__(self):
        self.jobname = jobname[:13]
        mrp_info = get_inplan_mrp_info(self.jobname.upper())
        if not mrp_info:
            return u"没有压合数据"
        self.job = gen.Job(jobname)
        self.stepname = 'panel'
        if self.stepname not in self.job.getSteps():
            return u"没有panel"
        self.pnlrout_dic = {}
        for data in mrp_info:
            if data['PROCESS_NUM'] > 1:
                pnlrout = 'pnl_rout%s' % (data['PROCESS_NUM'] - 1)
                self.pnlrout_dic[pnlrout] = [data['FROMLAY'], data['TOLAY']]

    def make_press_rout(self):
        print(self.pnlrout_dic)
        step = gen.Step(self.job, self.stepname)
        step.initStep()
        keys = sorted(self.pnlrout_dic.keys(), key=lambda i: int(i.split('pnl_rout')[1]))
        lastkey = keys[-1]
        inplan_all_flow = get_inplan_all_flow(self.jobname, True)
        for data in inplan_all_flow:
            if data['WORK_CENTER_CODE'] == '打靶' and data['PROCESS_DESCRIPTION'] == 'X-RAY打靶':
                note_string = data['NOTE_STRING']
                # print(note_string)
                search = re.search('“(.*?)”', str(note_string))
                if not search:
                    continue
                pnl_rout_n = search.group(1)
                inn_layer = None
                if pnl_rout_n.upper() == 'T':
                    pnl_rout = lastkey
                    inn_layer = 'inn'
                else:
                    pnl_rout = 'pnl_rout%s' % pnl_rout_n
                if step.isLayer(pnl_rout):
                    # print(pnl_rout, self.pnlrout_dic.get(pnl_rout))
                    if not inn_layer:
                        inn_layer = 'inn%s%s' % (self.pnlrout_dic.get(pnl_rout)[0].replace('L', ''),
                                                 self.pnlrout_dic.get(pnl_rout)[1].replace('L', ''))
                        print(pnl_rout, inn_layer)
                    tmp_pnl_rout = '%s+++' % pnl_rout
                    step.removeLayer(tmp_pnl_rout)
                    step.affect(pnl_rout)
                    step.copySel(tmp_pnl_rout)
                    step.unaffectAll()
                    step.affect(tmp_pnl_rout)
                    step.setFilterTypes('pad')
                    step.selectAll()
                    step.resetFilter()
                    if step.Selected_count():
                        step.selectDelete()
                    step.unaffectAll()
                    step.affect(inn_layer)
                    step.copySel(tmp_pnl_rout)
                    step.selectChange('r3100')
                    step.unaffectAll()
                    xmin, ymin, xmax, ymax = get_layer_limits(step, tmp_pnl_rout)
                    xmin, ymin, xmax, ymax = xmin + 1.2, ymin + 1.2, xmax - 1.2, ymax - 1.2
                    step.affect(tmp_pnl_rout)
                    step.addLine(xmax - 11, ymin, xmax - 11, ymin + 3, 'r2400')
                    step.addLine(xmax - 11, ymin + 3, xmax - 5, ymin + 3, 'r2400')
                    step.addLine(xmax - 5, ymin + 3, xmax - 5, ymin, 'r2400')
                    # step.addLine(xmax - 15, ymin + 1.2, xmax - 15, ymin + 3, 'r2400')
                    # step.addLine(xmax - 15, ymin + 3, xmax - 11.4, ymin + 3, 'r2400')
                    # step.addLine(xmax - 11.4, ymin + 3, xmax - 11.4, ymin + 1.2, 'r2400')
                    step.selectSingle(xmax - 11, ymin)
                    step.selectSingle(xmax - 12, ymin)
                    step.COM('sel_intersect_best,function=find_connect,mode=corner,radius=0,length_x=0,length_y=0,type_x=length,type_y=length,show_all=no,keep_remainder1=no,keep_remainder2=no,ang_x=0,ang_y=0')
                    step.unaffectAll()


if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    auto_make_press_rout = AutoMakePressRout()
    auto_make_press_rout.make_press_rout()
