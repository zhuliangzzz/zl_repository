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
        self.step = gen.Step(self.test_job, 'symbols')
        self.layer = 'add_symbols'
        self.ignore_rename_symbols = ('dcode', 'sh-op', 'sh_silk_autodw')
        self.compare_symbols = []
        self.check_time = time.strftime('%Y-%m-%d %H:%M:%S')
        self.change_symbols()
        self.symbol_compare()

    def change_symbols(self):
        # 先排除掉空symbol
        empty_symbol_import, empty_symbol, symbols_import, symbols = [], [], [], []
        with open(self.symbol_path) as reader:
            symbolstr = reader.read()
        valid_symbols = re.findall('<item.*?name="(.*?)"', str(symbolstr), re.DOTALL)
        self.test_job.open(1)
        self.step.initStep()
        layer_obj = gen.Layer(self.step, self.layer)
        symbols_import = [feat.symbol for feat in layer_obj.featout_dic_Index()['pads']]
        extra_symbol = []
        for symbol_import in symbols_import[:20]:
            if symbol_import in valid_symbols:
                # 重命名symbol
                symbol_mlb = symbol_import + '_mlb'
                if symbol_import in self.ignore_rename_symbols:
                    continue
                self.step.COM('rename_entity,job=%s,name=%s,new_name=%s,is_fw=no,type=symbol,fw_type=form' % (self.test_jobname, symbol_import, symbol_mlb))
                self.compare_symbols.append(symbol_import)
                # shutil.copytree(os.path.join(self.symbol_import_path, symbol_import),
                #                 os.path.join(self.symbol_path, symbol_mlb))
            else:
                extra_symbol.append(symbol_import)
                # shutil.copytree(os.path.join(self.symbol_import_path, symbol_import),
                #                 os.path.join(self.symbol_path, symbol_import))
        with open(self.log_file, 'a') as w:
            if self.compare_symbols:
                w.write('[%s] 检测到已有symbol:%s\n' % (self.check_time, ' '.join(self.compare_symbols)))
            if extra_symbol:
                w.write('[%s] 检测到新symbol:%s\n' % (self.check_time, ' '.join(extra_symbol)))

    def symbol_compare(self):
        diff_layers = []
        if self.compare_symbols:
            self.step.initStep()
            inconsistent_symbols = []
            for hdi_symbol in self.compare_symbols:
                mlb_symbol = hdi_symbol + '_mlb'
                map_layer = '%s_compare_diff+++' % hdi_symbol
                self.step.createLayer(hdi_symbol)
                self.step.createLayer(mlb_symbol)
                self.step.affect(hdi_symbol)
                self.step.addPad(0, 0, hdi_symbol)
                self.step.unaffectAll()
                self.step.affect(mlb_symbol)
                self.step.addPad(0, 0, hdi_symbol)
                self.step.unaffectAll()
                self.step.compareLayers(hdi_symbol, self.test_jobname, self.step.name, mlb_symbol, tol=25.4, map_layer=map_layer,
                                   map_layer_res=300)
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
            self.test_job.close(1)
        print(diff_layers)


if __name__ == '__main__':
    SymbolIntegration()
