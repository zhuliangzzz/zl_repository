#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:LaserCarvingTest.py
   @author:zl
   @time: 2024/10/21 15:53
   @software:PyCharm
   @desc:
"""
import json
import os
import re
import sys
from PyQt4 import QtGui, QtCore
# import LaserCarvingOutputUI_pyqt4 as ui
import platform
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

# import genesisPackages
import gClasses



def addPad(files):
    for file in files:
        readlines = None
        with open(file, 'r') as reader:
            readlines = reader.readlines()
        layer = file.split('/')[-1].split('.txt')[0]+"_tmp"
        if readlines:
            step.VOF()
            step.removeLayer(layer)
            step.VON()
            step.createLayer(layer)
            step.affect(layer)
            for line in readlines:
                x = float(line.split(';')[0].replace('X=',''))
                y = float(line.split(';')[1].replace('Y=',''))
                step.addPad(x,y,'s5000')
            step.clearAll()


if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    stepname = 'panel'
    files = ['/incam/server/site_data/scripts/zl/c18302gf908d1_top.txt', '/incam/server/site_data/scripts/zl/c18302gf908d1_bottom.txt']
    step = gClasses.Job(jobname).steps.get(stepname)
    step.open()
    step.setGroup()
    step.COM('units, type=mm')
    addPad(files)