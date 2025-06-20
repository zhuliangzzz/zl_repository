#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:SymbolIntegration.py
   @author:zl
   @time: 2025/2/17 14:43
   @software:PyCharm
   @desc:
   # 用两个料号各自加symbol复制过来
"""
import os
import re
import shutil
import platform, sys
import time

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genClasses_zl as gen


class SymbolIntegration(object):
    def __init__(self):
        # self.symbol_import_path = '/windows/inplan/symbols'
        self.symbol_path = '/incam/server/site_data/library/symbols/index.idx'
        # self.log_file = '/tmp/zl/log/symbol_integration.log'
        self.log_file = '/windows/174.file/HDI_INCMAPRO_JOB_DB/symbol_integration.log'
        self.test_jobname = 'incamlib-systest'
        self.test_job = gen.Job(self.test_jobname)
        self.test_job_import = gen.Job(self.test_jobname + '-import')
        self.step = gen.Step(self.test_job, 'symbols')
        self.step_import = gen.Step(self.test_job_import, 'symbols')
        self.layer = 'add_symbols'
        self.compare_symbols = []
        self.check_time = time.strftime('%Y-%m-%d %H:%M:%S')
        self.import_job()
        self.change_symbols()
        self.symbol_compare()

    def import_job(self):
        gen_top = gen.Top()
        if self.test_job_import.name in gen_top.listJobs():
            gen_top.COM('is_job_open,job=%s' % self.test_job_import.name)
            if gen_top.COMANS == 'yes':
                self.test_job_import.close(1)
            gen_top.deleteJob(self.test_job_import.name)
        gen_top.COM('import_job,db=db1,path=/incampro/server/site_data/scripts/sh_script/zl/test/incamlib-systest.tgz,name=%s' % self.test_job_import.name)
    def change_symbols(self):
        with open(self.symbol_path) as reader:
            symbolstr = reader.read()
        valid_symbols = re.findall('<item.*?name="(.*?)"', str(symbolstr), re.DOTALL)
        self.test_job_import.open(1)
        self.step_import.initStep()
        layer_obj = gen.Layer(self.step_import, self.layer)
        symbols_import = [feat.symbol for feat in layer_obj.featout_dic_Index()['pads']]
        extra_symbol = []
        for symbol_import in symbols_import:
            if symbol_import in valid_symbols:
                self.compare_symbols.append(symbol_import)
            else:
                extra_symbol.append(symbol_import)
        if self.compare_symbols:
            for symbol in self.compare_symbols:
                self.step_import.removeLayer(symbol)
                self.step_import.createLayer(symbol)
                self.step_import.affect(symbol)
                self.step_import.addPad(0, 0, symbol)
                self.step_import.unaffectAll()
        self.test_job_import.save()
        # self.test_job_import.close(1)
        with open(self.log_file, 'a') as w:
            if self.compare_symbols:
                w.write('[%s] 检测到已有symbol:%s\n' % (self.check_time, ' '.join(self.compare_symbols)))
            if extra_symbol:
                w.write('[%s] 检测到新symbol:%s\n' % (self.check_time, ' '.join(extra_symbol)))

    def symbol_compare(self):
        diff_layers = []
        if self.compare_symbols:
            self.test_job.open(1)
            self.step.initStep()
            inconsistent_symbols = []
            for hdi_symbol in self.compare_symbols:
                mlb_symbol = hdi_symbol + '_mlb'
                map_layer = '%s_compare_diff+++' % hdi_symbol
                self.step.removeLayer(hdi_symbol)
                self.step.removeLayer(mlb_symbol)
                self.step.removeLayer(map_layer)
                self.step.createLayer(hdi_symbol)
                self.step.createLayer(mlb_symbol)
                self.step.affect(hdi_symbol)
                self.step.addPad(0, 0, hdi_symbol)
                self.step.unaffectAll()
                self.step.copyLayer(self.test_job_import.name, self.step_import.name, hdi_symbol, mlb_symbol)
                self.step.compareLayers(hdi_symbol, self.test_jobname, self.step.name, mlb_symbol, tol=25.4, map_layer=map_layer, map_layer_res=300)
                self.step.affect(map_layer)
                self.step.setFilterTypes('pad')
                self.step.setSymbolFilter('r0')
                self.step.selectAll()
                self.step.resetFilter()
                if self.step.Selected_count():
                    diff_layers.append([hdi_symbol, mlb_symbol, map_layer])
                    inconsistent_symbols.append(hdi_symbol)
                else:
                    self.step.removeLayer(map_layer)
                self.step.unaffectAll()
            if inconsistent_symbols:
                with open(self.log_file, 'a') as w:
                    w.write('[%s] 检测到symbol比对不一致:%s\n' % (self.check_time, ' '.join(inconsistent_symbols)))
            self.step.close()
            self.test_job.save()
            self.test_job_import.close(1)
            # self.test_job.close(1)
        print(diff_layers)


if __name__ == '__main__':
    SymbolIntegration()
