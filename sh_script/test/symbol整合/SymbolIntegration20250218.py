#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:SymbolIntegration.py
   @author:zl
   @time: 2025/2/17 14:43
   @software:PyCharm
   @desc:
"""
import os
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
        self.symbol_import_path = '/windows/inplan/symbols'
        self.symbol_path = '/incam/server/site_data/library/symbols'
        # self.log_file = '/tmp/zl/log/symbol_integration.log'
        self.log_file = '/windows/174.file/HDI_INCMAPRO_JOB_DB/symbol_integration.log'
        self.test_jobname = 'incamlib-systest'
        self.test_job = gen.Job(self.test_jobname)
        self.compare_symbols = []

        self.check_time = time.strftime('%Y-%m-%d %H:%M:%S')
        self.import_symbols()
        self.symbol_compare()

    def import_symbols(self):
        # 先排除掉空symbol
        empty_symbol_import, empty_symbol, symbols_import, symbols = [], [], [], []
        for symbol in os.listdir(self.symbol_import_path):
            if os.path.isdir(os.path.join(self.symbol_import_path, symbol)):
                if len(os.listdir(os.path.join(self.symbol_import_path, symbol))) == 0:
                    empty_symbol_import.append(symbol)
                else:
                    symbols_import.append(symbol)
        for symbol in os.listdir(self.symbol_path):
            if os.path.isdir(os.path.join(self.symbol_path, symbol)):
                if len(os.listdir(os.path.join(self.symbol_path, symbol))) == 0:
                    empty_symbol.append(symbol)
                else:
                    symbols.append(symbol)
        extra_symbol = []
        for symbol_import in symbols_import:
            if symbol_import in symbols:
                symbol_mlb = symbol_import + '_mlb'
                self.compare_symbols.append(symbol_import)
                # shutil.copytree(os.path.join(self.symbol_import_path, symbol_import),
                #                 os.path.join(self.symbol_path, symbol_mlb))
            else:
                extra_symbol.append(symbol_import)
                # shutil.copytree(os.path.join(self.symbol_import_path, symbol_import),
                #                 os.path.join(self.symbol_path, symbol_import))
        with open(self.log_file, 'a') as w:
            if self.compare_symbols:
                w.write('[%s]检测到已有symbol:%s\n' % (self.check_time, ' '.join(self.compare_symbols)))
            if extra_symbol:
                w.write('[%s]检测到新symbol:%s\n' % (self.check_time, ' '.join(extra_symbol)))
        self.test_job.COM('rebuild_lib_index,category=cam_guide,profile=all,customer=')
        self.test_job.COM('save_library')

    def symbol_compare(self):
        diff_layers = []
        if self.compare_symbols:
            self.test_job.open(0)
            step = gen.Step(self.test_job, 'symbols')
            step.initStep()
            inconsistent_symbols = []
            for hdi_symbol in self.compare_symbols:
                mlb_symbol = hdi_symbol + '_mlb'
                map_layer = '%s_compare_diff+++' % hdi_symbol
                step.createLayer(hdi_symbol)
                step.createLayer(mlb_symbol)
                step.affect(hdi_symbol)
                step.addPad(0, 0, hdi_symbol)
                step.unaffectAll()
                step.affect(mlb_symbol)
                step.addPad(0, 0, hdi_symbol)
                step.unaffectAll()
                step.compareLayers(hdi_symbol, self.test_jobname, step.name, mlb_symbol, tol=25.4, map_layer=map_layer,
                                   map_layer_res=300)
                step.affect(map_layer)
                step.setFilterTypes('pad')
                step.setSymbolFilter('r0')
                step.selectAll()
                step.resetFilter()
                if step.Selected_count():
                    diff_layers.append([hdi_symbol, mlb_symbol, map_layer])
                    inconsistent_symbols.append(hdi_symbol)
                else:
                    step.removeLayer(map_layer)
                step.unaffectAll()
            if inconsistent_symbols:
                with open(self.log_file, 'a') as w:
                    w.write('[%s]检测到symbol比对不一致:%s\n' % (self.check_time, ' '.join(inconsistent_symbols)))
        print(diff_layers)


if __name__ == '__main__':
    SymbolIntegration()
