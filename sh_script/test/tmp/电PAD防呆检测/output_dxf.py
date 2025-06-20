#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#

__author__ = "Song"
__date__ = "20211218"
__version__ = "Revision: 1.1.0 "
__credits__ = u"""输出蓝胶后手动处理，需要单独输出dxf"""
__Software__ = 'PyCharm'
# ---------------------------------------------------------#
# --导入Package
import os
import platform
import sys

PRODUCT = os.environ.get('INCAM_PRODUCT', None)
if platform.system() == "Windows":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
import genCOM_26

import shutil


class MyApp(object):
    def __init__(self):
        self.GEN = genCOM_26.GEN_COM()

        self.jobName = os.environ.get('JOB', None)
        self.step_name = os.environ.get('STEP', None)
        self.output_dxf()

    def output_dxf(self):
        """
        输出dxf
        :return: None
        """
        if platform.system() == "Windows":
            path = "d:/disk/dxf/"
        else:
            path = "/id/workfile/film/%s/blue_dxf/" % self.jobName
        if not os.path.exists(path):
            os.makedirs(path)
        layer = 'blue_cs'
        self.GEN.WORK_LAYER(layer)
        self.GEN.COM('output_layer_reset')
        self.GEN.COM('output_layer_set,layer=%s,angle=0,mirror=no,x_scale=1,y_scale=1,comp=0,polarity=positive,'
                     'setupfile=,setupfiletmp=,line_units=inch,gscl_file=,step_scale=no' % layer)
        self.GEN.COM('output,job=%s,step=panel,format=DXF,dir_path=%s,prefix=,suffix=.dxf,break_sr=yes,'
                     'break_symbols=yes,break_arc=yes,scale_mode=all,surface_mode=fill,min_brush=25.4,'
                     'units=mm,x_anchor=0,y_anchor=0,x_offset=0,y_offset=0,line_units=mm,override_online=yes,'
                     'pads_2circles=no,draft=no,contour_to_hatch=no,pad_outline=no,output_files=multiple,'
                     'file_ver=old' % (self.jobName, path))
        src_file = os.path.join(path, 'blue_cs.dxf')
        dst_file = os.path.join(path, '%s.dxf' % self.jobName)
        shutil.move(src_file, dst_file)


# # # # --程序入口
if __name__ == "__main__":
    app = MyApp()


# === 更改输出路径 ====
# 2022.11.14
# V1.1.0
# 1.更改输出路径为 film下料号名、
# 2.http://192.168.2.120:82/zentao/story-view-4872.html


