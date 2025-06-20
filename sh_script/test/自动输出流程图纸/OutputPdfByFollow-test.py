#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:OutputPdfByFollow.py
   @author:zl
   @time: 2025/4/17 17:00
   @software:PyCharm
   @desc:
   自动提供选化油图纸
"""
import math
import os
import platform
import re
import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen
from get_erp_job_info import get_inplan_all_flow


class OutputPdfByFollow():
    def __init__(self):
        self.jobname = os.environ['JOB']
        self.job = gen.Job(self.jobname)
        self.step = gen.Step(self.job, 'set')
        self.panelStep = gen.Step(self.job, 'panel')
        # self.outputdir = '/windows/174.file/HDI_INCMAPRO_JOB_DB'
        self.outputdir = "/windows/174.file/产品监控资料/IPQC监控图纸/%s系列/%s" % (self.jobname[1:4].upper(), self.jobname.split('-')[0].upper()[:-1])

    def output(self):
        inplan_all_flow = get_inplan_all_flow(self.jobname[:13], True)
        has_selective_printing_oil = False
        tool_list, tmp_list, tool_map = [], [], {'exposure': [], 'exposure2':[], 'signal': []}
        for d in inplan_all_flow:
            # print(d)
            if '印选化油' in d['WORK_CENTER_CODE']:
                print(d)
                has_selective_printing_oil = True
                if d['VALUE_AS_STRING']:
                    print(d['VALUE_AS_STRING'])
                    tool = re.findall('(linek-(c|s)(-\d+)?)', str(d['VALUE_AS_STRING']))
                    print(tool)
                    if tool:
                        tmp_list.append([t[0] for t in tool])
                elif d['NOTE_STRING'] and '工具层名' in d['NOTE_STRING']:
                    print(d['NOTE_STRING'])
                    tool = re.findall('(linek-(c|s)(-\d+)?)', str(d['NOTE_STRING']))
                    print(tool)
                    if tool:
                        tmp_list.append([t[0] for t in tool])
            if has_selective_printing_oil:
                print('tmp', tmp_list)
                if '电镀镍金' in d['WORK_CENTER_CODE']:
                    if tmp_list:
                        if tmp_list[-1] not in tool_list:
                            tool_list.append(tmp_list[-1])
                            tool_map['exposure'].append(tmp_list[-1])
            if '印选化油' in d['WORK_CENTER_CODE']:
                has_selective_printing_oil = True
                if d['VALUE_AS_STRING']:
                    tool = re.findall('(linek-(c|s)(-\d+)?)', d['VALUE_AS_STRING'])
                    if tool:
                        tmp_list.append([t[0] for t in tool])
                elif d['NOTE_STRING'] and '工具层名' in d['NOTE_STRING']:
                    tool = re.findall('(linek-(c|s)(-\d+)?)', d['NOTE_STRING'])
                    tmp_list.append([t[0] for t in tool])
            if has_selective_printing_oil:
                if '沉金' in d['WORK_CENTER_CODE']:
                    if tmp_list:
                        if tmp_list[-1] not in tool_list:
                            tool_list.append(tmp_list[-1])
                            tool_map['exposure2'].append(tmp_list[-1])
            # if '金手指去导线' in d['WORK_CENTER_CODE']:
            if '金手指去' in d['WORK_CENTER_CODE'] and '导线' in d['WORK_CENTER_CODE']:
                if d['WORK_DESCRIPTION'] == '174|使用曝光资料' and d['VALUE_AS_STRING']:
                    if d['VALUE_AS_STRING'].strip().split(',') not in tool_list:
                        tool_list.append(d['VALUE_AS_STRING'].strip().split(','))
                        tool_map['signal'].append(d['VALUE_AS_STRING'].strip().split(','))

        print('toolmap', tool_map)
        layers = []
        for vals in tool_map.values():
            layers.extend(vals)
        if not layers:
            QMessageBox.information(None, u'提示', u'没有印选化油/选化干膜/蚀刻金手指引线流程或没有注明指定层')
            sys.exit()
        self.step.initStep()
        for type, layerlist in tool_map.items():
            for layers in layerlist:
                if type == 'exposure':
                    for layer in layers:
                        exposure_layer = 'xlym-c' if '-c' in layer else 'xlym-s'
                        layer_side = 'C' if '-c' in layer else 'S'
                        tmp_layer = 'tmp_%s+++' % layer
                        self.step.initStep()
                        self.step.Flatten(layer, tmp_layer)
                        self.step.affect(tmp_layer)
                        self.step.selectReverse()
                        if not self.step.Selected_count():
                            self.step.removeLayer(tmp_layer)
                            self.step.unaffectAll()
                            self.panelStep.initStep()
                            self.panelStep.COM("display_sr,display=yes")
                            self.panelStep.display(layer)
                            self.panelStep.display_layer(exposure_layer, 2)
                        else:
                            self.step.removeLayer(tmp_layer)
                            self.step.unaffectAll()
                            self.step.initStep()
                            self.step.COM("display_sr,display=yes")
                            self.step.display(layer)
                            self.step.display_layer(exposure_layer, 2)
                        self.printPDF([type, layer_side, layer, exposure_layer])
                elif type == 'exposure2':
                    for layer in layers:
                        exposure_layer = 'xlym-c' if '-c' in layer else 'xlym-s'
                        layer_side = 'C' if '-c' in layer else 'S'
                        tmp_layer = 'tmp_%s+++' % layer
                        self.step.initStep()
                        self.step.Flatten(layer, tmp_layer)
                        self.step.affect(tmp_layer)
                        self.step.selectReverse()
                        if not self.step.Selected_count():
                            self.step.removeLayer(tmp_layer)
                            self.step.unaffectAll()
                            self.panelStep.initStep()
                            self.panelStep.COM("display_sr,display=yes")
                            self.panelStep.display(layer)
                            self.panelStep.display_layer(exposure_layer, 2)
                        else:
                            self.step.removeLayer(tmp_layer)
                            self.step.unaffectAll()
                            self.step.initStep()
                            self.step.COM("display_sr,display=yes")
                            self.step.display(layer)
                            self.step.display_layer(exposure_layer, 2)
                        self.printPDF([type, layer_side, layer, exposure_layer])
                elif type == 'signal':
                    for layer in layers:
                        signal_layer = 'l1' if '-c' in layer else 'l%s' % int(self.jobname[4:6])
                        layer_side = 'C' if '-c' in layer else 'S'
                        tmp_layer = 'tmp_%s+++' % layer
                        self.step.initStep()
                        self.step.Flatten(layer, tmp_layer)
                        self.step.affect(tmp_layer)
                        self.step.selectReverse()
                        if not self.step.Selected_count():
                            self.step.removeLayer(tmp_layer)
                            self.step.unaffectAll()
                            self.panelStep.initStep()
                            self.panelStep.COM("display_sr,display=yes")
                            self.panelStep.display(layer)
                            self.panelStep.display_layer(signal_layer, 2)
                        else:
                            self.step.removeLayer(tmp_layer)
                            self.step.unaffectAll()
                            self.step.initStep()
                            self.step.COM("display_sr,display=yes")
                            self.step.display(layer)
                            self.step.display_layer(signal_layer, 2)
                        self.printPDF([type, layer_side, layer, signal_layer])
        QMessageBox.information(None, u'提示', u'输出完成')


    def printPDF(self, layers):
        print(layers)
        type_ = layers[0]
        side = layers[1]
        print_layer_name = '\;'.join(layers[2:])
        if type_ == 'exposure':
            layername = '电金选化油%s面图纸' % side
        elif type_ == 'exposure2':
            layername = '沉金选化油%s面图纸' % side
        elif type_ == 'signal':
            layername = '蚀刻引线%s面图纸' % side
        pdffile = os.path.join(self.outputdir, '%s_%s.png' % (self.jobname, layername))
        # self.job.COM(
        #     "print,title=,layer_name=%s,mirrored_layers=,draw_profile=no,drawing_per_layer=no,label_layers=no,dest=pdf_file,num_copies=1,dest_fname=%s,paper_size=A4,scale_to=0,nx=1,ny=1,orient=portrait,paper_orient=portrait,paper_width=0,paper_height=0,auto_tray=no,top_margin=0.5,bottom_margin=0.5,left_margin=0.5,right_margin=0.5,x_spacing=0,y_spacing=0,color1=990000,color2=9900,color3=99,color4=990099,color5=999900,color6=9999,color7=0" % (
        #         print_layer_name, pdffile))
        self.job.COM('disp_snapshot,file=%s' % pdffile)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    outputPdfByFollow = OutputPdfByFollow()
    outputPdfByFollow.output()
