#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:ExportSymbolTgz.py
   @author:zl
   @time: 2025/2/18 14:49
   @software:PyCharm
   @desc:
   创建料号，把symbol都加到一个层，导出
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


class ExportSymbolTgz(object):
    def __init__(self):
        self.symbol_path = '/incam/server/site_data/library/symbols/index.idx'
        self.test_jobname = 'incamlib-systest'
        self.test_job = gen.Job(self.test_jobname)
        self.export_path = '/incam/server/site_data/scripts/sh_script/test/'
        self.run()

    def run(self):
        # valid_symbols = []
        # for symbol in os.listdir(self.symbol_path):
        #     if os.path.isdir(os.path.join(self.symbol_path, symbol)):
        #         if len(os.listdir(os.path.join(self.symbol_path, symbol))) != 0:
        #             valid_symbols.append(symbol)
        with open(self.symbol_path) as reader:
            symbolstr = reader.read()
        valid_symbols = re.findall('<item.*?name="(.*?)"', str(symbolstr), re.DOTALL)
        if valid_symbols:
            self.test_job.open(1)
            step = gen.Step(self.test_job, 'symbols')
            step.initStep()
            layer = 'add_symbols'
            step.truncate(layer)
            step.affect(layer)
            for symbol in valid_symbols:
                step.addPad(0,0, symbol)
            step.unaffectAll()
            self.test_job.save()
            self.test_job.close(1)
        gen.Top().exportJob(self.test_jobname, self.export_path)


if __name__ == '__main__':
    ExportSymbolTgz()
