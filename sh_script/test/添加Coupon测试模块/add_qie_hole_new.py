#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__    = "20230323"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""新切片孔设计 """
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
from genesisPackages import job, get_drill_start_end_layers, \
     getSmallestHole, signalLayers, addFeatures, \
     ksz_layers, tongkongDrillLayer, mai_drill_layers, \
     mai_man_drill_layers, bd_drillLayer, lay_num

#job.PAUSE(str(tongkongDrillLayer + mai_drill_layers +\
    #mai_man_drill_layers + ksz_layers + bd_drillLayer))

def run_qie_hole_step():
    matrixInfo = job.matrix.getInfo()
    all_layers = matrixInfo["gROWname"]
    combine_steps = []
    addfeature = addFeatures()
    for index, drill_layer in enumerate(tongkongDrillLayer + mai_drill_layers +\
        mai_man_drill_layers + ksz_layers+bd_drillLayer):
        
        # drill_layer = "drl"
        hole_size = getSmallestHole(job.name, "edit",drill_layer) or \
            getSmallestHole(job.name, "set",drill_layer)
        
        if drill_layer not in ["drl"] and not hole_size:
            continue
        
        result = get_drill_start_end_layers(matrixInfo, drill_layer)
        if lay_num < 2:
            top_layer = result[0]
            top_index = all_layers.index(top_layer)
            bot_index = top_index
        else:
            top_layer, bot_layer = result
            top_index = all_layers.index(top_layer)
            bot_index = all_layers.index(bot_layer)
        
        drill_signalLayers = []
        for sig_layer in signalLayers:
            sig_index = all_layers.index(sig_layer)
            if min([top_index, bot_index]) <= sig_index <= max([top_index, bot_index]):
                drill_signalLayers.append(sig_layer)    
        
        coupon_step = "qie_hole_coupon_new_{0}".format(drill_layer)
        
        if coupon_step in matrixInfo["gCOLstep_name"]:
            job.removeStep(coupon_step)             
        
        combine_steps.append(coupon_step)
        
        job.addStep(coupon_step)
        step = gClasses.Step(job, coupon_step)
        step.open()
        step.reset_fill_params()
        
        
        dic_zu_layername = {}
        for layer in matrixInfo["gROWname"]:
            dic_zu_layername[layer] = []
            
        step.COM('units,type=mm')
        arraylist = [0, 0, 4, 8]
        step.COM(
                "profile_rect,x1={0},y1={1},x2={2},y2={3}".format(*arraylist))
        step.COM("datum,x={0},y={1}".format(*arraylist))
        step.COM("origin,x={0},y={1},push_in_stack=1".format(*arraylist))
        
        if not hole_size:
            hole_size = 452
            
        if hole_size > 452:
            hole_size = 452
            
        for layer in drill_signalLayers:
            xy1 = [0.6, 0.6]
            xy2 = [3.4, 7.4]
            dic_zu_layername[layer].append([xy1,
                                            xy2,
                                            "surface",
                                            {"addRectangle": True, }])      
        
        for i in range(11):
            for j in range(6):
                add_x = 0.8 * j
                add_y = 0.8 * i
                if 0< i <10 and j not in [0, 5]:
                    continue
                
                if 0 < j < 5 and i not in [0, 10]:
                    continue
                
                for layer in drill_signalLayers:
                    dic_zu_layername[layer].append([add_x,
                                                    add_y,
                                                    "r{0}".format(452+200),
                                                    {"polarity": "negative",}])        
                    
                dic_zu_layername[drill_layer].append([add_x,
                                                      add_y,
                                                      "r452",
                                                      {"attrstring":".drill,option=non_plated"}])
                
                #if not re.match("b\d\d?-\d\d?", drill_layer):                
                    #for dd_layer in ["md1", "md2"]:
                        #if step.isLayer(dd_layer): 
                            #resize = 152.4
                            #dic_zu_layername[dd_layer].append([add_x,
                                                               #add_y,
                                                               #"r{0}".format(452+resize),
                                                               #{}])   
                    #for mask_layer in ["m1", "m2"]:
                        #if step.isLayer(dd_layer): 
                            #resize = 200
                            #dic_zu_layername[mask_layer].append([add_x,
                                                                 #add_y,
                                                                 #"r{0}".format(452+resize),
                                                                 #{}])                         
        
        for i in range(5):
            for j in range(2):
                add_x = 1.2 if not j else 2.8
                add_y = 1.2 * (i + 1) +0.4     
                dic_zu_layername[drill_layer].append([add_x,
                                                      add_y,
                                                      "r{0}".format(hole_size),
                                                      {"attrstring":".drill,option=plated"}])
                if j == 1:            
                    pol = "positive"            
                else:
                    pol = "negative"
                    
                for layer in drill_signalLayers:
                    dic_zu_layername[layer].append([add_x,
                                                    add_y,
                                                    "r{0}".format(hole_size+400+100) if j == 1 else "r{0}".format(hole_size+400),
                                                    {"polarity": "negative",}])
                    
                    dic_zu_layername[layer].append([add_x,
                                                    add_y,
                                                    "r{0}".format(hole_size+400),
                                                    {"polarity": pol,}])        
            
            
        addfeature.start_add_info(step, matrixInfo, dic_zu_layername)
        
        arraylist = [-0.35, -0.35, 4.35, 8.35]
        step.COM(
                "profile_rect,x1={0},y1={1},x2={2},y2={3}".format(*arraylist))
        step.COM("datum,x={0},y={1}".format(*arraylist))
        step.COM("origin,x={0},y={1},push_in_stack=1".format(*arraylist))    
        
    #coupon_step = "qie_hole_coupon_new"
    #matrixInfo = job.matrix.getInfo()
    #if coupon_step in matrixInfo["gCOLstep_name"]:
        #job.removeStep(coupon_step)             
    
    #job.addStep(coupon_step)
    #step = gClasses.Step(job, coupon_step)
    #step.open()
    #step.COM('units,type=mm')
    #arraylist = [0, 0, (4 + 0.7 + 0.5) * len(combine_steps) - 0.5, 8 + 0.7]
    #step.COM(
            #"profile_rect,x1={0},y1={1},x2={2},y2={3}".format(*arraylist))
    #step.COM("datum,x={0},y={1}".format(*arraylist))
    #step.COM("origin,x={0},y={1},push_in_stack=1".format(*arraylist))
    
    #for index,couponName in enumerate(combine_steps):
        #corX = 0.35 + (4 + 0.7 + 0.5) * index
        #corY = 0.35
        #step.COM('sr_tab_add,line=0,step={0},x={1},y={2},nx=1,ny=1'.format(couponName, corX, corY))
        
    #step.COM('sredit_reduce_nesting, mode=one_highest')
    
    #for index,couponName in enumerate(combine_steps):
        #job.removeStep(couponName)
        
if __name__ == "__main__":
    run_qie_hole_step()