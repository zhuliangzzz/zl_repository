#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__    = "20230926"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""拉力测试模块 """
#import sip
# sip.setapi('QVariant', 2)

import os
import sys
import re
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")

import gClasses
from genesisPackages import job, signalLayers, \
     addFeatures, solderMaskLayers, innersignalLayers, \
     outsignalLayers
from get_erp_job_info import get_barcode_mianci

from create_ui_model import QtGui, Qt 
addfeature = addFeatures()

def run_pull_cu_step():
    matrixInfo = job.matrix.getInfo()
    
    mianci_info = get_barcode_mianci(job.name.upper())
    mianci = None        
    if mianci_info:
        if "C" in mianci_info[0][1].upper():
            mianci = "c"
            
        if "S" in mianci_info[0][1].upper():
            mianci = "s"
            
    if mianci is None:    
        item, okPressed = QtGui.QInputDialog.getItem(QtGui.QWidget(), u"提示", u"选择明码面次:",
                                                     [u"C面", u"S面"], 0, False, Qt.Qt.WindowStaysOnTopHint)
        mianci = "c" if "C" in item else "s"
        if not okPressed:
            sys.exit()
    
    item, okPressed = QtGui.QInputDialog.getText(QtGui.QWidget(), u"提示", u"请确认定位孔大小(um):",
                                                 0, "2000",  Qt.Qt.WindowStaysOnTopHint)    
    hole_size = str(item)    
    if not okPressed:
        sys.exit()    
    
    coupon_step = "cu-coupon"
    
    if coupon_step in matrixInfo["gCOLstep_name"]:
        job.removeStep(coupon_step)             
    
    job.addStep(coupon_step)
    step = gClasses.Step(job, coupon_step)
    step.open()
    step.reset_fill_params()    
    
    dic_zu_layername = {}
    for layer in matrixInfo["gROWname"]:
        dic_zu_layername[layer] = []
        
    step.COM('units,type=mm')
    arraylist = [0, 0, 3.6 * 25.4, 0.3 * 25.4]
    step.COM(
            "profile_rect,x1={0},y1={1},x2={2},y2={3}".format(*arraylist))
    step.COM("datum,x={0},y={1}".format(*arraylist))
    step.COM("origin,x={0},y={1},push_in_stack=1".format(*arraylist))
    
    add_pad_x = 0
    add_pad_y = 0
    for layer in outsignalLayers:
        dic_zu_layername[layer].append([add_pad_x,
                                        add_pad_y,
                                        "pull_signal_outer",
                                        {}])
    for layer in innersignalLayers:
        dic_zu_layername[layer].append([add_pad_x,
                                        add_pad_y,
                                        "pull_signal_inner",
                                        {}])        
    for layer in solderMaskLayers:
        dic_zu_layername[layer].append([add_pad_x,
                                        add_pad_y,
                                        "pull_signal_mask",
                                        {}])
    for layer in ["md1", "md2"]:
        if step.isLayer(layer):            
            dic_zu_layername[layer].append([add_pad_x,
                                            add_pad_y,
                                            "pull_signal_md",
                                            {}])         
        
    dic_zu_layername["drl"].append([add_pad_x,
                                    add_pad_y,
                                    "pull_signal_drl",
                                    {}])
    
    add_text_x1 = 17
    add_text_y1 = 0.35
    add_text_x2 = 28
    add_text_y2 = 0.36
    mirror = "no"
    add_layer = outsignalLayers[0]
    if mianci == "s":
        add_text_x1 = 32
        add_text_x2 = 21
        mirror = "yes"
        add_layer = outsignalLayers[-1]
        
    dic_zu_layername[add_layer].append([add_text_x1,
                                        add_text_y1,
                                        "B1001001",
                                        {"attrstring": [".orbotech_plot_stamp", ".deferred"],
                                         "mirror": mirror,
                                         "angle": 0,
                                         "xSize": 1.1176,
                                         "ySize": 1.1176,
                                         "width": 0.5,}])
    
    dic_zu_layername[add_layer].append([add_text_x2,
                                        add_text_y2,
                                        "-SSS",
                                        {"attrstring": [".orbotech_plot_stamp", ".deferred"],
                                         "mirror": mirror,
                                         "angle": 0,
                                         "xSize": 1.1176,
                                         "ySize": 1.1176,
                                         "width": 0.5,}])
    
    dic_zu_layername["l1"].append([add_text_x1 + 40,
                                   add_text_y1,
                                   "$$job_cut",
                                   {"mirror": "no",
                                    "angle": 0,
                                    "xSize": 1.1176,
                                    "ySize": 1.1176,
                                    "width": 0.5,}])    
            
    addfeature.start_add_info(step, matrixInfo, dic_zu_layername)
    
    step.clearAll()
    step.affect("drl")
    step.COM("sel_break")
    step.changeSymbol("r{0}".format(hole_size))
    step.resetAttr()
    step.addAttr(".drill", attrVal="non_plated", valType='option', change_attr="yes")
    step.resetAttr()
    
    for layer in ["cdc", "cds"]:
        if step.isLayer(layer):
            step.copySel(layer)
            
    for layer in innersignalLayers:
        step.copyToLayer(layer, invert='yes', size=1000)        
        
    #挡点网制作
    for dd_layer in ["md1", "md2"]:
        if step.isLayer(dd_layer):
            if float(hole_size) <= 1000:
                resize = 152.4
            else:
                resize = -203.2
                
            step.copyToLayer(dd_layer, size=resize)
                
    for layer in solderMaskLayers:
        step.copyToLayer(layer, size=4*25.4)
            
    step.clearAll()
    #for layer in ["sgt-c", "sgt-s"]:
        #if step.isLayer(layer):
            #step.clearAll()
            #step.affect(layer)
            
            #step.COM("sr_fill,polarity=%s,step_margin_x=0,step_margin_y=0,\
                #step_max_dist_x=%s,step_max_dist_y=%s,sr_margin_x=0,\
                #sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,\
                #consider_feat=no,feat_margin=0,consider_drill=no,drill_margin=0,\
                #consider_rout=no,dest=affected_layers,layer=,\
                #attributes=no" % ("positive", 2540, 2540))
            
    step.clearAll()
    
    #翟鸣通知 阻焊盖油制作 20240913 by lyh
    # http://192.168.2.120:82/zentao/story-view-8262.html 20250123 按需求改成开窗制作
    #for layer in solderMaskLayers:
        #step.clearAll()
        #step.affect(layer)
        #step.resetFilter()
        #step.selectAll()
        #step.COM("sel_break")
        #step.selectNone()
        #step.filter_set(feat_types='surface', polarity='positive')
        #step.selectAll()
        #if step.featureSelected():
            #step.selectDelete()
            
    step.clearAll()
    step.resetFilter()    
    
    #削铜宽不够15mil的细丝
    for worklayer in innersignalLayers:
        step.clearAll()
        step.affect(worklayer)
        step.contourize()
        step.COM("sel_resize,size={0},corner_ctl=no".format(-15*25.4))
        step.COM("sel_resize,size={0},corner_ctl=yes".format(15*25.4))    
    
    if step.isLayer("ww"):
        step.clearAll()
        step.affect("ww")        
        step.COM("profile_to_rout,layer=ww,width={0}".format(16*25.4))
        
    step.clearAll()
    
if __name__ == "__main__":
    run_pull_cu_step()