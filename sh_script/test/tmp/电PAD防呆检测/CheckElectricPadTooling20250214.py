#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CheckElectricPadTooling.py
   @author:zl
   @time: 2025/2/14 10:56
   @software:PyCharm
   @desc:
"""
import sys

import platform
import time

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

from genesisPackages_zl import lay_num
import genClasses_zl as gen


class CheckElectricPadTooling():
    def __init__(self):
        self.jobs_file = 'jobs.txt'
        self.tool_sysmbol = ['hdi-dwpad',
                             'hdi-dwtop-t',
                             'hdi-dwtop-b',
                             'sh-dwsig2014',
                             'sh_silk_autodw',
                             'hdi-dwtop2013',
                             'hdi1-baj*',
                             'hdi1-ba*',
                             'hdi1-byj*',
                             'hdi1-by*',
                             'hdi1-bs*',
                             'sh-ldi',
                             'sh-bb',
                             'sh-dwtop',
                             'measure_l*',
                             'measure_fd_l*']
        self.log_file = '/tmp/zl/log/CheckElectricPadTooling.log'
        self.check()

    def __getattr__(self, item):
        if item == 'jobs':
            self.jobs = self.get_jobs()
            return self.jobs

    def get_jobs(self):
        joblist = []
        with open(self.jobs_file) as reader:
            reader.readlines()


    def check(self):
        error_jobs = []
        for jobname in self.jobs:
            job = gen.Job(jobname)
            job.open(0)
            if 'panel' not in job.steps.keys():
                continue
            step = gen.Step(job, 'panel')
            step.initStep()
            for outsignalLayer in ['l1', 'l%s' % lay_num]:
                dk = '%s-dk' % outsignalLayer
                if dk not in step.layers:
                    continue
                tmp_dk = '%s+++' % dk
                to_tool = 1 if int(outsignalLayer.replace('l', '')) < lay_num / 2 else -1
                tool_layer = 'l%s' % (int(outsignalLayer.replace('l', '')) + to_tool)
                tmp_tool_layer = '%s+++' % tool_layer
                step.affect(dk)
                step.setFilterTypes('line')
                step.setAttrFilter('.pattern_fill')
                step.setSymbolFilter('r254')
                step.selectAll()
                step.resetFilter()
                if step.Selected_count():
                    step.copyToLayer(tmp_dk, size=5000)
                    step.unaffectAll()
                    step.affect(tool_layer)
                    step.selectSymbol('\;'.join(self.tool_sysmbol))
                    step.resetFilter()
                    if step.Selected_count():
                        step.copySel(tmp_tool_layer)
                    step.unaffectAll()
                step.unaffectAll()
                if step.isLayer(tmp_tool_layer):
                    step.affect(tmp_dk)
                    step.refSelectFilter(tmp_tool_layer)
                    if step.Selected_count():
                        error_jobs.append(jobname)
                    step.unaffectAll()
                step.removeLayer(tmp_dk)
                step.removeLayer(tmp_tool_layer)
            job.close(0)
        if error_jobs:
            with open(self.log_file, 'w') as r:
                r.write('[%s]Check error jobs:%s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'),' '.join(error_jobs)))


if __name__ == '__main__':
    CheckElectricPadTooling()