#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import gClasses
import math
try:
    import numpy    
except:
    pass

import socket
import json
localip = socket.gethostbyname_ex(socket.gethostname())

top = gClasses.Top()
if top.currentJob():
    jobname = top.currentJob()
    stepname = top.currentStep()
    job = gClasses.Job(jobname)
    gen = gClasses.Matrix(job)
    os.environ["GEN_USER"] = top.getUser()
    matrixInfo = job.matrix.getInfo()

    signalLayers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                    if matrixInfo["gROWcontext"][i] == "board"
                    and (matrixInfo["gROWlayer_type"][i] == "signal" or \
                         matrixInfo["gROWlayer_type"][i] == "power_ground")]

    innersignalLayers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                         if matrixInfo["gROWcontext"][i] == "board"
                         and (matrixInfo["gROWlayer_type"][i] == "signal"
                              or matrixInfo["gROWlayer_type"][i] == "power_ground")
                         and matrixInfo["gROWside"][i] == "inner"]

    outsignalLayers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                       if matrixInfo["gROWcontext"][i] == "board"
                       and matrixInfo["gROWlayer_type"][i] == "signal"
                       and matrixInfo["gROWside"][i] != "inner"]

    solderMaskLayers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                        if matrixInfo["gROWcontext"][i] == "board"
                        and matrixInfo["gROWlayer_type"][i] == "solder_mask"]

    silkscreenLayers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                        if matrixInfo["gROWcontext"][i] == "board"
                        and matrixInfo["gROWlayer_type"][i] == "silk_screen"]

    ospLayers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                 if lay in ["gtj", "gbj", "gtm", "gbm"]]

    tongkongDrillLayer = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                          if matrixInfo["gROWcontext"][i] == "board"
                          and matrixInfo["gROWlayer_type"][i] == "drill"
                          and (re.match("^drl$", lay))]
    
    ksz_layers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                          if matrixInfo["gROWcontext"][i] == "board"
                          and matrixInfo["gROWlayer_type"][i] == "drill"
                          and (re.match("^cb.*|^cd.*|^cs.*", lay))]# 控深 喇叭 阶梯孔等

    mai_drill_layers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                        if matrixInfo["gROWcontext"][i] == "board"
                        and matrixInfo["gROWlayer_type"][i] == "drill"
                        and (re.match("^b\d{1,2}-\d{1,2}$", lay))]# 机械埋孔
    
    mai_man_drill_layers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                        if matrixInfo["gROWcontext"][i] == "board"
                        and matrixInfo["gROWlayer_type"][i] == "drill"
                        and (re.match("^m\d{1,2}-\d{1,2}$", lay))]  #埋盲孔  

    laser_drill_layers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                          if matrixInfo["gROWcontext"][i] == "board"
                          and matrixInfo["gROWlayer_type"][i] == "drill"
                          and (re.match("^s\d{1,2}-\d{1,2}$", lay))]

    sz_drillLayer = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                     if matrixInfo["gROWcontext"][i] == "board"
                     and matrixInfo["gROWlayer_type"][i] == "drill"
                     and re.match("^sz1.*", lay)]  # 树脂

    bd_drillLayer = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                     if matrixInfo["gROWcontext"][i] == "board"
                     and matrixInfo["gROWlayer_type"][i] == "drill"
                     and (re.match("^bd.*", lay))]  # 背钻

    rout_layers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                   if matrixInfo["gROWcontext"][i] == "board"
                   and matrixInfo["gROWlayer_type"][i] == "rout"]  # 锣带
    
    lp_layers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                   if matrixInfo["gROWcontext"][i] == "board"
                   and matrixInfo["gROWlayer_type"][i] == "drill"
                   and "lp" in lay] # 铝片

    # 20250520 zl
    inner_sz_layers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                     if matrixInfo["gROWlayer_type"][i] == "drill"
                     and re.match("sz\d+-\d+\.(lp|dq)(\d+)?$", lay)]

    # outer_sz_layers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
    #                    if matrixInfo["gROWlayer_type"][i] == "drill"
    #                    and re.match("sz-(c|s)\.(lp|dq)(\d+)?$", lay)]
    outer_sz_layers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                       if matrixInfo["gROWlayer_type"][i] == "drill"
                       and re.match("sz-(c|s)\.lp(\d+)?$", lay)]

    lp_sm_layers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                       if matrixInfo["gROWlayer_type"][i] == "drill"
                       and re.match("lp-(c|s)$", lay)]

    ###定义线路板层数
    try:        
        lay_num = int(jobname[4:6])
    except:
        lay_num = len(signalLayers)

else:
    if os.environ.get("NOT_JOB_EXIT", None) == "YES":
        print "run scripts in a job inside!"
        sys.exit()


def get_step_obj(**kwargs):
    if kwargs.get("JOB"):
        job = gClasses.Job(kwargs["JOB"])
        if kwargs.get("STEP"):
            step = gClasses.Step(job, kwargs["STEP"])
            return job, step

        return job, None

    return None, None


def get_mai_drill_hole(**kwargs):
    """定义埋孔层"""
    # job = gClasses.Job(kwargs["JOB"])
    # step = gClasses.Step(job, kwargs["STEP"])

    job, step = get_step_obj(**kwargs)
    if job is not None:
        matrixInfo = job.matrix.getInfo()
        mai_drill_layer = [lay for i, lay in enumerate(matrixInfo["gROWname"])

                           if matrixInfo["gROWcontext"][i] == "board"

                           and matrixInfo["gROWlayer_type"][i] == "drill"

                           and (re.match("^b\d{1,2}-\d{1,2}$", lay))]
        return mai_drill_layer

    return None


def get_drill_start_end_layers(matrixinfo, drillLayer):
    """获取钻孔层所在的 线路层"""
    row = matrixinfo["gROWname"].index(drillLayer)
    gROWdrl_start = matrixinfo["gROWdrl_start"][row]
    gROWdrl_end = matrixinfo["gROWdrl_end"][row]
    if drillLayer in ["drl", "cdc", "cds"]:
        outsignalLayers = [lay for i, lay in enumerate(matrixinfo["gROWname"])

                           if matrixinfo["gROWcontext"][i] == "board"

                           and matrixinfo["gROWlayer_type"][i] == "signal"

                           and matrixinfo["gROWside"][i] != "inner"]
        return outsignalLayers
    
    if re.match("^s\d{1,2}-\d{1,2}$", drillLayer):
        layers = []
        for layer in [gROWdrl_start, gROWdrl_end]:
            if re.match("^l\d{1,2}$", layer):
                layers.append(layer)
                
        if "s1-" in drillLayer:
            layers.append("l1")            
        
        if "s{0}-".format(lay_num) in drillLayer:
            layers.append("l{0}".format(lay_num))
            
        return list(set(layers))

    return gROWdrl_start, gROWdrl_end


def get_layer_polarity(layer):
    if layer in matrixInfo["gROWname"]:
        row = matrixInfo["gROWname"].index(layer)
        polarity = matrixInfo["gROWpolarity"][row]

        return polarity

    return "positive"


def redefine_edit_origin(stepname):
    """重新定义edit 原点 定义到profile中心"""
    step = gClasses.Step(job, stepname)
    step.open()

    Prof_xmin, Prof_ymin, Prof_xmax, Prof_ymax = \
        get_profile_limits(step)

    center_x = float(Prof_xmax + Prof_xmin) / 2
    center_y = float(Prof_ymax + Prof_ymin) / 2

    step.COM("origin,x=%s,y=%s,push_in_stack=1" % (center_x, center_y))
    step.COM("datum,x=0,y=0")
    step.COM("editor_page_close")

    return 0 - center_x, 0 - center_y


def get_profile_limits(step):
    ProfileInfo = step.getProfile()
    Prof_xmin = ProfileInfo.xmin * 25.4
    Prof_xmax = ProfileInfo.xmax * 25.4
    Prof_ymin = ProfileInfo.ymin * 25.4
    Prof_ymax = ProfileInfo.ymax * 25.4

    return Prof_xmin, Prof_ymin, Prof_xmax, Prof_ymax


def get_sr_limits(step):
    SrInfo = step.getSr()
    sr_xmin = SrInfo.xmin * 25.4
    sr_ymin = SrInfo.ymin * 25.4
    sr_xmax = SrInfo.xmax * 25.4
    sr_ymax = SrInfo.ymax * 25.4

    return sr_xmin, sr_ymin, sr_xmax, sr_ymax


def get_layer_limits(step, worklayer):
    feat_Info = step.DO_INFO(
        "-t layer -e %s/%s/%s -d LIMITS,units=mm" % (jobname, step.name, worklayer))
    gLIMITSxmin = feat_Info['gLIMITSxmin']
    gLIMITSymin = feat_Info["gLIMITSymin"]
    gLIMITSxmax = feat_Info["gLIMITSxmax"]
    gLIMITSymax = feat_Info["gLIMITSymax"]

    return gLIMITSxmin, gLIMITSymin, gLIMITSxmax, gLIMITSymax


def get_layer_selected_limits(step, worklayer):
    feat_Info = step.DO_INFO(
        "-t layer -e %s/%s/%s -d LIMITS -o select,units=mm" % (step.job.name, step.name, worklayer))
    gLIMITSxmin = feat_Info['gLIMITSxmin']
    gLIMITSymin = feat_Info["gLIMITSymin"]
    gLIMITSxmax = feat_Info["gLIMITSxmax"]
    gLIMITSymax = feat_Info["gLIMITSymax"]

    return gLIMITSxmin, gLIMITSymin, gLIMITSxmax, gLIMITSymax


def get_profile_center(stepname):
    step = gClasses.Step(job, stepname)
    step.open()

    Prof_xmin, Prof_ymin, Prof_xmax, Prof_ymax = \
        get_profile_limits(step)

    center_x = float(Prof_xmax + Prof_xmin) / 2.0
    center_y = float(Prof_ymax + Prof_ymin) / 2.0

    # step.COM("origin,x=%s,y=%s,push_in_stack=1" % (Prof_xmin, Prof_ymin))
    step.COM("datum,x=0,y=0")
    step.COM("editor_page_close")

    return center_x, center_y


def getPcsSize(stepname):
    """获取单只尺寸"""
    step = gClasses.Step(job, stepname)
    # step.open()
    Prof_xmin, Prof_ymin, Prof_xmax, Prof_ymax = \
        get_profile_limits(step)

    pcsX = Prof_xmax - Prof_xmin
    pcsY = Prof_ymax - Prof_ymin

    return pcsX, pcsY


def create_outline(stepname, layer):
    step = gClasses.Step(job, stepname)
    step.open()
    step.COM("units,type=mm")
    if step.isLayer(layer):
        step.COM("truncate_layer,layer=" + layer)
    else:
        step.createLayer(layer)

    step.clearAll()
    step.COM("profile_to_rout,layer=%s,width=150" % layer)
    step.COM("editor_page_close")


def panelization(jobname, stepname,
                 size_x, size_y,
                 numberX, numberY,
                 pcsX, pcsY, selPcs,
                 spaceX, spaceY,
                 boardX, boardY):
    """开始自动挂板"""
    step = gClasses.Step(job, stepname)
    step.open()

    Prof_xmin, Prof_ymin, Prof_xmax, Prof_ymax = \
        get_profile_limits(step)

    step.COM('units,type=mm')
    step.COM("panel_size,width=%s,height=%s" % (size_x, size_y))
    dx = pcsX + spaceX
    dy = pcsY + spaceY

    x = boardX - Prof_xmin
    y = boardY - Prof_ymin

    editstep = gClasses.Step(job, selPcs)
    editstep.open()
    edit_ProfileInfo = editstep.getProfile()
    edit_Prof_xmin = edit_ProfileInfo.xmin * 25.4
    edit_Prof_ymin = edit_ProfileInfo.ymin * 25.4
    editstep.COM("units,type=mm")
    editstep.COM("datum,x=0,y=0")
    editstep.COM("editor_page_close")

    step.open()
    step.COM("sr_tab_add,step=%s,x=%s,\
    y=%s,nx=%s,ny=%s,dx=%s,\
    dy=%s" % (selPcs, x - edit_Prof_xmin, y - edit_Prof_ymin, numberX, numberY, dx, dy))


def get_panelset_sr_step(jobname, panelset, is_all=True, is_group_by=True):
    """获取panel内或set内的step名"""
    job = gClasses.Job(jobname)
    step = gClasses.Step(job, panelset)
    # step.open()

    SrInfo = step.getSr()
    Sr_table = SrInfo.table
    stepnames = []
    for tableInfo in Sr_table:
        if tableInfo.step in stepnames and is_group_by:
            continue

        nx = tableInfo.xnum
        ny = tableInfo.ynum
        for i in range(nx*ny):
            
            stepnames.append(tableInfo.step)    
            if is_all:              
                stepnames += get_panelset_sr_step(jobname, tableInfo.step, is_all, is_group_by)

    if is_group_by:        
        return list(set(stepnames))
    else:
        return stepnames

def get_sr_area_for_step(stepname, exclude_sr_step=[]):
    step = gClasses.Step(job, stepname)
    step.open()
    step.COM("units,type=mm")
    SrInfo = step.getSr()
    Sr_table = SrInfo.table
    rectangles = []
    for tableInfo in Sr_table:
        find_step = False
        for name in exclude_sr_step:  # 排除某些step
            if name == tableInfo.step:
                find_step = True
        if find_step: continue

        rectangles.append([tableInfo.xmin * 25.4, tableInfo.ymin * 25.4,
                           tableInfo.xmax * 25.4, tableInfo.ymax * 25.4])
    return rectangles


def get_sr_area_for_step_include(stepname, include_sr_step=[]):
    step = gClasses.Step(job, stepname)
    step.open()
    step.COM("units,type=mm")
    SrInfo = step.getSr()
    Sr_table = SrInfo.table
    rectangles = []
    for tableInfo in Sr_table:
        for name in include_sr_step:  # 筛选某些step
            if name in tableInfo.step:
                rectangles.append([tableInfo.xmin * 25.4, tableInfo.ymin * 25.4,
                                   tableInfo.xmax * 25.4, tableInfo.ymax * 25.4])
    return rectangles


def get_sr_area(layer, stepname="panel"):
    step = gClasses.Step(job, stepname)
    step.open()
    step.COM("units,type=mm")

    step.clearAll()

    SrInfo = step.getSr()

    Sr_table = SrInfo.table

    if not step.isLayer(layer):
        step.createLayer(layer)
    else:
        step.COM("truncate_layer,layer=%s" % layer)

    step.clearAll()

    step.affect(layer)

    step.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,min_brush=0.254,\
    use_arcs=yes,symbol=,dx=2.54,dy=2.54,break_partial=yes,cut_prims=no,outline_draw=no,\
    outline_width=0,outline_invert=no")

    STR = '-t step -e %s/%s -d REPEAT,units=mm' % (jobname, stepname)
    gREPEAT_info = step.DO_INFO(STR)
    gREPEATstep = gREPEAT_info['gREPEATstep']
    gREPEATxmax = gREPEAT_info['gREPEATxmax']
    gREPEATymax = gREPEAT_info['gREPEATymax']
    gREPEATxmin = gREPEAT_info['gREPEATxmin']
    gREPEATymin = gREPEAT_info['gREPEATymin']

    for i in xrange(len(gREPEATstep)):
        step.addRectangle(
            gREPEATxmin[i], gREPEATymin[i], gREPEATxmax[i], gREPEATymax[i])


def get_sr_area_value(stepname="panel"):
    step = gClasses.Step(job, stepname)
    step.open()
    step.COM("units,type=mm")

    STR = '-t step -e %s/%s -d REPEAT,units=mm' % (jobname, stepname)
    gREPEAT_info = step.DO_INFO(STR)
    gREPEATstep = gREPEAT_info['gREPEATstep']
    gREPEATxmax = gREPEAT_info['gREPEATxmax']
    gREPEATymax = gREPEAT_info['gREPEATymax']
    gREPEATxmin = gREPEAT_info['gREPEATxmin']
    gREPEATymin = gREPEAT_info['gREPEATymin']
    rectangles = []
    for i in xrange(len(gREPEATstep)):
        rectangles.append(
            [gREPEATxmin[i], gREPEATymin[i], gREPEATxmax[i], gREPEATymax[i]])

    return rectangles


def get_sr_area_flatten(layer,
                        stepname="panel",
                        exclude_sr_step=[],
                        include_sr_step=[], 
                        jobname=None,
                        get_sr_step=False):
    if jobname:
        job_obj = gClasses.Job(jobname)
    else:
        job_obj = job
        jobname = job.name

    step = gClasses.Step(job_obj, stepname)
    step.open()
    step.COM("units,type=mm")
    step.clearAll()
    if step.isLayer(layer):
        step.COM("truncate_layer,layer=" + layer)
    else:
        step.createLayer(layer)
    
    if get_sr_step:
        all_steps = get_panelset_sr_step(jobname, stepname)
    else:
        all_steps = matrixInfo["gCOLstep_name"]
        
    flip = genesisFlip()
    if sys.platform == "win32":
        flip.release_flip()

    
    for name in all_steps:
        if str(name) == stepname:
            continue
        if not str(name):
            continue

        if name in exclude_sr_step:
            continue
        
        if include_sr_step:
            if name not in include_sr_step:
                continue

        editstep = gClasses.Step(job_obj, name)
        editstep.open()
        editstep.COM("units,type=mm")
        PROF_info = editstep.getProfile()
        f_xmin = PROF_info.xmin * 25.4
        f_ymin = PROF_info.ymin * 25.4
        f_xmax = PROF_info.xmax * 25.4
        f_ymax = PROF_info.ymax * 25.4
        if f_xmax == 0 and f_ymax == 0 \
                and f_xmin == 0 and f_ymin == 0:
            editstep.close()
            continue

        editstep.clearAll()
        editstep.affect(layer)
        editstep.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,min_brush=0.254,\
        use_arcs=yes,symbol=,dx=2.54,dy=2.54,break_partial=yes,cut_prims=no,outline_draw=no,\
        outline_width=0,outline_invert=no")
        editstep.COM("sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,step_max_dist_x=2540,\
        step_max_dist_y=2540,sr_margin_x=-2540,sr_margin_y=-2540,sr_max_dist_x=0,sr_max_dist_y=0,\
        nest_sr=yes,stop_at_steps=,consider_feat=no,consider_drill=no,consider_rout=no,\
        dest=affected_layers,attributes=no")
        editstep.contourize()
        editstep.clearAll()
        editstep.close()

    step.open()
    step.clearAll()
    if step.isLayer(layer):
        step.flatten_layer(layer, layer + "_flatten")
        # step.removeLayer(layer)
        # step.createLayer(layer)
        step.COM("truncate_layer,layer=" + layer)
        step.copyLayer(jobname, stepname, layer + "_flatten", layer)
        step.removeLayer(layer + "_flatten")

    if sys.platform == "win32":
        flip.restore_flip()
        
def get_panel_features_in_set_position(jobname, set_step,
                                       pnl_step,create_layer,
                                       pnl_feature_layer, 
                                       **kwargs ):
    """获取panel中元素在set中的位置或set中的元素在pcs中的位置"""
    
    stepname = pnl_step
    job = gClasses.Job(jobname)
    step = gClasses.Step(job, stepname)
    step.open()
    step.COM("units,type=mm")
    step.removeLayer(create_layer)
    step.createLayer(create_layer)
    
    STR = '-t step -e %s/%s -d REPEAT,units=mm' % (job.name, stepname)
    gREPEAT_info = step.DO_INFO(STR)
    gREPEATstep = gREPEAT_info['gREPEATstep']
    gREPEATxmax = gREPEAT_info['gREPEATxmax']
    gREPEATymax = gREPEAT_info['gREPEATymax']
    gREPEATxmin = gREPEAT_info['gREPEATxmin']
    gREPEATymin = gREPEAT_info['gREPEATymin']
    set_rect_area = []
    for i in xrange(len(gREPEATstep)):
        if gREPEATstep[i] == set_step:                
            set_rect_area.append(
                [gREPEATxmin[i], gREPEATymin[i], gREPEATxmax[i], gREPEATymax[i]])        
        
    #计算panel有序号的在set中的位置
    find_piont_area = []
    if set_rect_area:
        editstep = gClasses.Step(job, set_step)
        editstep.open()
        editstep.COM("units,type=mm")
        editstep.clearAll()
        editstep.removeLayer("calc_num_position")
        editstep.COM("profile_to_rout,layer=calc_num_position,width=10")
        editstep.affect("calc_num_position")
        editstep.COM("sel_create_sym,symbol=calc_num_position,x_datum=0,y_datum=0,"
                     "delete=no,fill_dx=2.54,fill_dy=2.54,attach_atr=no,retain_atr=no")
        editstep.selectDelete()
        editstep.addPad(0, 0, "calc_num_position")            
        
        step.open()
        step.flatten_layer("calc_num_position", "calc_num_position_flt")
        for xs, ys, xe, ye in set_rect_area:
            step.clearAll()
            step.affect(pnl_feature_layer)
            step.resetFilter()
            step.selectRectangle(xs-5, ys-5, xe+5, ye+5, intersect='yes')
            if not step.featureSelected():
                continue
            
            if kwargs.get("create_symbol", None) == "yes":
                #if "-lyh" in job.name:
                    #step.PAUSE(pnl_feature_layer)
                step.removeLayer("create_symbol_tmp")
                step.copySel("create_symbol_tmp")
                step.clearAll()
                step.affect("calc_num_position_flt")
                step.resetFilter()
                step.selectFeatureIndex("calc_num_position_flt", 1)
                if step.featureSelected():
                    layer_cmd = gClasses.Layer(step, "calc_num_position_flt")
                    feat_out = layer_cmd.featSelOut(units="mm")["pads"]
                    create_symbol_x = feat_out[0].x
                    create_symbol_y = feat_out[0].y
                    angle = feat_out[0].rotation
                    step.copySel("create_symbol_tmp")
                    step.clearAll()
                    step.affect("create_symbol_tmp")
                    if angle != 0:
                        step.COM("sel_transform,mode=anchor,oper=rotate,duplicate=no,\
                        x_anchor=0,y_anchor=0,angle={0},x_scale=1,\
                        y_scale=1,x_offset=0,y_offset=0".format(360-angle))
                    
                    step.selectNone()
                    step.selectSymbol("calc_num_position", 1, 1)
                    layer_cmd = gClasses.Layer(step, "create_symbol_tmp")
                    feat_out = layer_cmd.featSelOut(units="mm")["pads"]
                    create_symbol_x = feat_out[0].x
                    create_symbol_y = feat_out[0].y                    
                    
                    step.selectNone()
                    step.COM("sel_create_sym,symbol=cal_gold_area_positoin,x_datum={0},y_datum={1},"
                             "delete=no,fill_dx=2.54,fill_dy=2.54,attach_atr=no,"
                             "retain_atr=no".format(create_symbol_x, create_symbol_y))
                    step.removeLayer("create_symbol_tmp")
                    step.removeLayer("calc_num_position_flt")
                    step.removeLayer("calc_num_position")                    
                    return "cal_gold_area_positoin"
                
                return "error"                    
            
            layer_cmd1 = gClasses.Layer(step, pnl_feature_layer)
            feat_out1 = layer_cmd1.featSelIndex()
                
            step.clearAll()
            step.affect("calc_num_position_flt")
            step.resetFilter()
            step.setSymbolFilter("calc_num_position")
            step.selectRectangle(xs, ys, xe, ye, intersect='yes')
            feat_out2 = ""
            if step.featureSelected():
                layer_cmd2 = gClasses.Layer(step, "calc_num_position_flt")
                feat_out2 = layer_cmd2.featSelOut(units="mm")["pads"]
                
            # print feat_out1, 222222222,feat_out2, 1111111111, "\n"
            if feat_out1 and feat_out2:
                angle = 360 - feat_out2[0].rotation
                step.clearAll()
                step.affect(pnl_feature_layer)
                step.resetFilter()
                
                for index in feat_out1:
                    step.selectNone()
                    step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(pnl_feature_layer, index))                        
                    xmin, ymin, xmax, ymax = get_layer_selected_limits(step, pnl_feature_layer)                        
                    set_x = xmin - feat_out2[0].x
                    set_y = ymin - feat_out2[0].y
                    new_xmin, new_ymin = get_convert_coordinate(set_x, set_y, angle)
                    
                    set_x = xmax - feat_out2[0].x
                    set_y = ymax - feat_out2[0].y
                    new_xmax, new_ymax = get_convert_coordinate(set_x, set_y, angle)                                               
                    
                    if (new_xmin, new_ymin, new_xmax, new_ymax) not in find_piont_area:                            
                        find_piont_area.append((new_xmin, new_ymin, new_xmax, new_ymax))
                    
                break
    
    #删除辅助层
    step.removeLayer("calc_num_position")
    step.removeLayer("calc_num_position_flt")
    step.clearAll()
    
    if find_piont_area:
        editstep.open()
        editstep.clearAll()
        editstep.affect(create_layer)
        editstep.reset_fill_params()
        for x1, y1, x2, y2 in find_piont_area:
            editstep.addRectangle(x1, y1, x2, y2)
            
    editstep.clearAll()
    
def get_convert_coordinate(set_x, set_y, angle):
    if angle == 90:
        new_set_x = set_y
        new_set_y = set_x * -1
    elif angle == 180:
        new_set_x = set_x * -1
        new_set_y = set_y * -1
    elif angle == 270:
        new_set_x = set_y * -1
        new_set_y = set_x
    else:
        new_set_x = set_x
        new_set_y = set_y
        
    return new_set_x, new_set_y   


def create_genesis_layer_features_file(jobname, stepname,
                                       infolist, features_path):
    """根据info信息 生成genesis层目录下的features文件"""
    job = gClasses.Job(jobname)
    step = gClasses.Step(job, stepname)

    # dic_info = step.parseFeatureInfo(infolist)
    # feat_out = dic_info.get("pads", [])
    # feat_out += dic_info.get("lines", [])
    # feat_out += dic_info.get("arcs", [])
    # all_symbols = list(set([obj.symbol for obj in feat_out]))
    all_symbols = []
    for line in infolist:
        line = line.strip()
        symbol = ""
        if re.match("^#P ", line):
            symbol = line.split()[3]
        if re.match("^#L ", line):
            symbol = line.split()[5]
        if re.match("^#A ", line):
            symbol = line.split()[7]
        if symbol:
            all_symbols.append(symbol)

    step.COM("units,type=inch")
    all_symbols = list(set(all_symbols))
    step.removeLayer("symbol_tmp")
    step.createLayer("symbol_tmp")
    step.affect("symbol_tmp")
    for symbol in all_symbols:
        step.addPad(0, 0, symbol)

    step.removeLayer("symbol_tmp")
    step.COM("units,type=mm")

    dic_zu = {}
    header_arraylist = ["#\n", "#Feature symbol names\n", "#\n"]
    for i, symbol in enumerate(all_symbols):
        header_arraylist.append("${0} {1}\n".format(
            i, symbol))
        dic_zu[symbol] = str(i)

    dic_angle = {}
    dic_angle["0"] = 0
    dic_angle["90"] = 1
    dic_angle["180"] = 2
    dic_angle["270"] = 3
    dic_mirror = {}
    dic_mirror["N"] = 0
    dic_mirror["Y"] = 4

    arraylist = []
    for line in infolist[1:]:
        line = line.replace("#", "")
        if ";" in line:
            new_line = line.split(";")[0] + "\n"
        else:
            new_line = line

        if new_line.startswith("P"):
            new_line_list = new_line.split()
            mirror = "N"
            if new_line.endswith("Y\n"):
                mirror = "Y"

            new_line = new_line.replace("N\n", "").strip(
            ) + "\n"
            new_line = new_line.replace("Y\n", "").strip(
            ) + "\n"
            if new_line.endswith("0\n"):
                angle = "0"
            if new_line.endswith("90\n"):
                angle = "90"
            if new_line.endswith("180\n"):
                angle = "180"
            if new_line.endswith("270\n"):
                angle = "270"
            new_line = new_line.replace("90\n", "")
            new_line = new_line.replace("180\n", "")
            new_line = new_line.replace("270\n", "")
            new_line = new_line.replace("0\n", "")
            new_line += (str(dic_angle[angle] +
                             dic_mirror[mirror]) + "\n")
            arraylist.append(new_line)
        elif new_line.startswith("T"):
            new_line_list = new_line.split()
            angle = new_line_list[5].strip()
            new_line_list[5] = str(dic_angle[angle] +
                                   dic_mirror["N"])
            if new_line_list[6].strip() == "Y":
                new_line_list[5] = str(dic_angle[angle] +
                                       dic_mirror["Y"])
            new_line_list[6] = ""
            arraylist.append(" ".join(new_line_list) + "\n")
        else:
            arraylist.append(new_line)

    all_lines = "".join(arraylist)
    all_symbols_bak = all_symbols[:]

    replace_symbols = []
    while True:
        for symbol in all_symbols:
            for other_symbol in all_symbols:
                if symbol == other_symbol:
                    continue

                if symbol in other_symbol:
                    break
            else:
                all_lines = all_lines.replace(symbol, dic_zu[symbol])
                replace_symbols.append(symbol)

        # print len(replace_symbols), len(all_symbols_bak)
        if len(replace_symbols) == len(all_symbols_bak):
            break
        else:
            all_symbols = [x for x in all_symbols if x not in replace_symbols]

    try:
        with open(features_path, "w") as f:
            f.write("".join(header_arraylist) +
                    "\n" + all_lines)
    except:
        return 0

    return 1


def get_inplan_info():
    """获取inplan信息"""
    jobpath = job.dbpath
    inplan_info_file = jobpath + "/user/inplan_info"
    if sys.platform == "win32":
        if not os.path.exists(inplan_info_file):
            dblist = os.path.join(
                os.environ["GENESIS_DIR"], "sys", "dblist")
            dbpath = ""
            for line in file(dblist).readlines():
                if "PATH=" in line:
                    dbpath = line.split("=")[1].strip()
                    break

            jobpath = os.path.join(dbpath, "jobs", jobname)
            inplan_info_file = jobpath + "/user/inplan_info"

    # print "-------------->", inplan_info_file

    if not os.path.exists(inplan_info_file):
        if sys.platform == "win32":
            os.system("perl %s/sys/scripts/suntak/check_inplan_info_file.pl " % os.environ["GENESIS_DIR"])

        else:
            if os.path.exists("/incam2"):
                os.system("perl /incam2/server/site_data/scripts/suntak/check_inplan_info_file.pl ")
            else:
                os.system("perl /incam/server/site_data/scripts/suntak/check_inplan_info_file.pl ")

    if not os.path.exists(inplan_info_file):
        return {}

    lines = file(inplan_info_file).readlines()
    lines = [line for line in lines if line.startswith("set")]

    return lines


def get_parseInplan_info():
    """获取字典形式的inplan信息"""
    lines = get_inplan_info()
    dic_inplan_info = job.parseInfo(lines, "=")
    return dic_inplan_info


def get_inplan_job():
    """获取inplan jobname 20210913 by lyh"""
    dic_inplan_info = get_parseInplan_info()
    inplan_job = ""
    if dic_inplan_info:
        try:
            inplan_job = dic_inplan_info["inplan_job"].replace(
                '"', "").replace("'", "")
        except:
            pass

    return inplan_job


def getSmallestHole(jobname, stepname, drillLayer, panel="panel"):
    """获取板内最小孔"""
    job = gClasses.Job(jobname)
    d = job.matrix.getInfo()
    if panel not in d["gCOLstep_name"]:
        steps = d["gCOLstep_name"]
    else:
        steps = get_panelset_sr_step(jobname, panel)
    flip = genesisFlip()
    arraylist = []
    for name in steps:
        if stepname in str(name):
            if not str(name).strip():
                continue
            if flip.is_step_flip(name):
                flip.release_flip()
            step = gClasses.Step(job, name)
            STR = r'-t layer -e %s/%s/%s -d TOOL -p drill_size+type,units=mm' % (jobname, name, drillLayer)
            drillLayer_size = step.DO_INFO(STR)['gTOOLdrill_size']
            drillLayer_type = step.DO_INFO(STR)['gTOOLtype']
            if drillLayer_size:
                if drillLayer.startswith("bd"):
                    pth_holes = [size for i, size in enumerate(drillLayer_size)]
                else:
                    pth_holes = [size for i, size in enumerate(drillLayer_size)
                                 if drillLayer_type[i] != "non_plated"]
                    
                    for tk_drill in ["drl", "cdc", "cds"]:
                        if tk_drill in drillLayer:
                            # 通孔要 过滤有后缀的小孔 
                            pth_holes = [size for size in pth_holes if str(size).split(".")[0][-1] == "0"]
                        
                if pth_holes:
                    small_size = min(pth_holes)
                    arraylist.append(small_size)

    if arraylist:
        return min(arraylist)

    return 0

def getSmallestHole_and_step(jobname, stepname, drillLayer, panel="panel", return_all_step=None):
    """获取板内最小孔"""
    job = gClasses.Job(jobname)
    d = job.matrix.getInfo()
    if panel not in d["gCOLstep_name"]:
        steps = d["gCOLstep_name"]
    else:
        steps = get_panelset_sr_step(jobname, panel)
    flip = genesisFlip()
    arraylist = []
    for name in steps:
        if stepname in str(name):
            if flip.is_step_flip(name):
                flip.release_flip()
            step = gClasses.Step(job, name)
            STR = r'-t layer -e %s/%s/%s -d TOOL -p drill_size+type,units=mm' % (jobname, name, drillLayer)
            drillLayer_size = step.DO_INFO(STR)['gTOOLdrill_size']
            drillLayer_type = step.DO_INFO(STR)['gTOOLtype']
            if drillLayer_size:
                if drillLayer.startswith("bd"):
                    pth_holes = [size for i, size in enumerate(drillLayer_size)]
                else:
                    pth_holes = [size for i, size in enumerate(drillLayer_size)
                                 if drillLayer_type[i] != "non_plated"]
                    
                    for tk_drill in ["drl", "cdc", "cds"]:
                        if tk_drill in drillLayer:
                            # 通孔要 过滤有后缀的小孔 
                            pth_holes = [size for size in pth_holes if str(size).split(".")[0][-1] == "0"]
                if pth_holes:
                    small_size = min(pth_holes)
                    arraylist.append([small_size, name])

    if return_all_step:        
        if arraylist:
            return arraylist
    
        return [(0, None)]
    else:
        if arraylist:
            return sorted(arraylist, key=lambda x: x[0])[0]
        
        return 0, None

def get_drill_hole_size(jobname, stepname, drillLayer, pnl_name):
    """获取板内孔size"""
    job = gClasses.Job(jobname)
    d = job.matrix.getInfo()
    steps = get_panelset_sr_step(jobname, pnl_name)
    flip = genesisFlip()
    arraylist = []
    for name in steps:
        if stepname in str(name):
            # if flip.is_step_flip(name):continue
            step = gClasses.Step(job, name)
            STR = r'-t layer -e %s/%s/%s -d TOOL -p drill_size,units=mm' % (jobname, name, drillLayer)
            info = step.DO_INFO(STR)['gTOOLdrill_size']
            if info:
                hole_size = list(set(info))
                arraylist = arraylist + hole_size

    if arraylist:
        return list(set(arraylist))

    return []


def get_core_layers():
    lines = get_inplan_info()
    dic_inplan_info = job.parseInfo(lines, "=")
    core_layers = []
    if dic_inplan_info:
        for layer in innersignalLayers:
            LAY_WID_SPA = "LAY_WID_SPA_%s" % layer
            if dic_inplan_info.get(LAY_WID_SPA):
                process_name = dic_inplan_info[LAY_WID_SPA][1]
                pattern = ".*(\d+|\d)/(\d+|\d).*"
                reg = re.compile(pattern)
                result = reg.findall(process_name)
                # job.PAUSE(str(result + [process_name]))
                if result:
                    pre, suffix = result[0]
                    if abs(int(pre) - int(suffix)) != 1:
                        continue
                    else:
                        core_layers.append(layer)

    return core_layers


def add_features_in_panel_edge(step, x, y,
                               worklayer,
                               symbolname,
                               checklayer_list,
                               msg,
                               move_x_flag,
                               move_y_flag,
                               angle,
                               manual_add="yes",
                               move_length=100,
                               attr_name="",
                               set_attr=""):
    step.removeLayer(worklayer)
    step.createLayer(worklayer)

    if set_attr:
        layer_cmd = gClasses.Layer(step, worklayer)
        layer_cmd.setGenesisAttr(attr_name, set_attr)

    move_size = 0
    manual_move = False
    while True:
        if move_size <= move_length:
            step.clearAll()
            step.affect(worklayer)
            step.selectDelete()
            step.addPad(x + move_x_flag * move_size,
                        y + move_y_flag * move_size,
                        symbolname, angle=angle)

        step.clearAll()
        for layer in checklayer_list:
            if step.isLayer(layer):
                step.affect(layer)

        step.resetFilter()
        step.COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad;line;arc;text,\
            polarity=positive;negative,exclude_syms=r1250")
        step.refSelectFilter(worklayer)
        if step.featureSelected():
            """此处过滤板边铺铜的线元素 例如307780c06a2"""
            step.setAttrFilter(".bit,text=copper")
            step.COM('''filter_area_end,layer=,filter_name=popup,operation=unselect,\
                area_type=none,inside_area=no,intersect_area=no,lines_only=no,\
                ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0''')
            # 过滤.pattern_fill 填充元素20220422 by lyh
            step.resetFilter()
            step.setAttrFilter(".pattern_fill")
            step.COM("filter_set,filter_name=popup,update_popup=no,feat_types=line,\
            polarity=positive;negative,exclude_syms=")
            step.COM('''filter_area_end,layer=,filter_name=popup,operation=unselect,\
                area_type=none,inside_area=no,intersect_area=no,lines_only=no,\
                ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0''')

        if "fill" in checklayer_list and not step.featureSelected():
            step.clearAll()
            step.affect("fill")
            step.resetFilter()
            step.refSelectFilter(worklayer)

        if step.featureSelected():
            move_size += 2
        else:
            break

        if move_size > move_length:
            if manual_add == "yes":
                if sys.platform == "win32":

                    os.system("python %s/sys/scripts/suntak/lyh/messageBox.py %s" %
                              (os.environ["GENESIS_DIR"], msg))
                else:
                    if os.path.exists("/incam2"):
                        os.system("python /incam2/server/site_data/scripts/suntak/lyh/autoRunScripts.py messageBox %s" %
                                  (msg))
                    else:
                        os.system("python /incam/server/site_data/scripts/suntak/lyh/autoRunScripts.py messageBox %s" %
                                  (msg))
                step.clearAll()
                step.display(worklayer)
                step.COM("pan_center,x=%s,y=%s" % (x + move_x_flag * move_size,
                                                   y + move_y_flag * move_size))
                step.COM("zoom_factor,factor=1.000000:0.400000")
                step.PAUSE("cannot auto select position, please manual move %s" %
                           symbolname)
                manual_move = True
                # break
            else:
                # 自动的无法添加 程序不添加
                return False

    step.clearAll()
    layercmd = gClasses.Layer(step, worklayer)
    pad_info = layercmd.featOut(units="mm")["pads"]
    pad_x = pad_info[0].x
    pad_y = pad_info[0].y

    return pad_x, pad_y, manual_move


def auto_add_features_in_panel_edge(step, add_pad_x, add_pad_y,
                                    worklayer, symbolname,
                                    checklayer_list, msg,
                                    move_x_flag, move_y_flag,
                                    angle, manual_add="yes",
                                    move_length=100, attr_name="",
                                    set_attr="", orig_id=83,
                                    to_feat_size=0, area_x=[0, 0, 0],
                                    area_y=[0, 0, 0], move_model_fx="X",
                                    mirror="no", to_sr_area=3,
                                    exclude_symbols=[], exists_arraylist_feature_xy=[],
                                    return_check_feature_xy="no", check_sr_area="yes",
                                    max_min_area_method="no"):
    # max_min_area_method 为yes时 改为区间法则 提升计算效率 20220517 by lyh
    if check_sr_area == "yes":
        step.removeLayer(worklayer)
        step.createLayer(worklayer)

        sr_repeat_area = get_sr_area_value(step.name)

        if set_attr:
            layer_cmd = gClasses.Layer(step, worklayer)
            layer_cmd.setGenesisAttr(attr_name, set_attr)
    else:
        sr_repeat_area = []

    # dic_symbol_info = get_erp_symbol_info(orig_id)
    dic_symbol_info = {}
    if exists_arraylist_feature_xy:
        arraylist_feature_xy = exists_arraylist_feature_xy
    else:
        arraylist_feature_xy = []

    if not exists_arraylist_feature_xy:
        for layer in checklayer_list:
            if step.isLayer(layer):
                layer_cmd = gClasses.Layer(step, layer)
                feat_out = layer_cmd.featCurrent_LayerOut(units="mm")
                pad_feat_out = feat_out["pads"]
                
                text_feat_out = feat_out["text"]
                for obj in text_feat_out:    
                    if abs(obj.rotation) in [0, 90, 180, 270]:
                        if abs(obj.rotation) in [0, 180]:                            
                            obj.x = obj.x + len(obj.text) *obj.xsize * 0.5
                            obj.y = obj.y + obj.ysize * 0.5
                            if abs(obj.rotation) == 180:
                                obj.x = obj.x - len(obj.text) *obj.xsize * 0.5
                                obj.y = obj.y - obj.ysize * 0.5
                            obj.symbol = "rect%sx%s" % (len(obj.text) *obj.xsize * 1000, obj.ysize * 1000)
                        else:
                            obj.x = obj.x + obj.ysize * 0.5
                            obj.y = obj.y - len(obj.text) *obj.xsize * 0.5
                            if abs(obj.rotation) == 270:
                                obj.x = obj.x - obj.ysize * 0.5
                                obj.y = obj.y + len(obj.text) *obj.xsize * 0.5                  
                            obj.symbol = "rect%sx%s" % (obj.ysize * 1000, len(obj.text) *obj.xsize * 1000)
                            
                        obj.rotation = 0
                        pad_feat_out.append(obj)   

                line_feat_out = feat_out["lines"]
                r500_fill_lines = [obj for obj in line_feat_out
                                   if obj.symbol[0] == "r"
                                   and hasattr(obj, "pattern_fill")]

                for obj in line_feat_out:

                    if hasattr(obj, "pattern_fill") and \
                            obj.symbol == "r1250":
                        continue

                    if len(r500_fill_lines) > 500:
                        # 剔除掉板边的填充网格线
                        if obj in r500_fill_lines:
                            continue

                    if abs(obj.angle) in [0, 90, 180, 270]:
                        obj.x = (obj.xe + obj.xs) * 0.5
                        obj.y = (obj.ye + obj.ys) * 0.5
                        obj.rotation = abs(obj.angle)
                        obj.mirror = "no"
                        if abs(obj.angle) in [0, 180]:
                            obj.symbol = "rect%sx%s" % (
                                obj.len * 1000 + float(obj.symbol[1:]), obj.symbol)
                        else:
                            obj.symbol = "rect%sx%s" % (
                                obj.symbol, obj.len * 1000 + float(obj.symbol[1:]))

                        obj.angle = abs(obj.angle)

                        pad_feat_out.append(obj)

                layer_cell = layer_cmd.cell
                size = to_feat_size
                if getattr(layer_cell, "layer_type", None) and \
                        layer_cell.layer_type == "drill":
                    size = to_feat_size + 1

                if 'bk' in layer:
                    size = 5

                for obj in pad_feat_out:

                    if obj.symbol in exclude_symbols:
                        continue

                    extra_size = 0
                    if obj.symbol in ["auto_register_signal2"]:
                        extra_size = 5

                    # if getattr(obj, "xs", None):
                    # 线元素多避开一点
                    # extra_size = 3

                    # 陈晓君通知 板边一圈LED pad可以忽略 20220518 by lyh
                    if getattr(obj, "string", "") == "led_pad":
                        continue

                    if return_check_feature_xy == "yes":
                        extra_size = 0

                    if max_min_area_method == 'no':
                        arraylist_feature_xy += get_symbol_area(step, jobname, step.name,
                                                                obj.symbol, [obj.x,
                                                                             obj.y],
                                                                obj.rotation, obj.mirror,
                                                                to_feat_size=size + extra_size,
                                                                dic_symbol_info=dic_symbol_info)
                    else:
                        symbol_around_xy = get_symbol_area(step, jobname, step.name,
                                                           obj.symbol, [obj.x,
                                                                        obj.y],
                                                           obj.rotation, obj.mirror,
                                                           to_feat_size=size + extra_size,
                                                           dic_symbol_info=dic_symbol_info)
                        symbol_xmin = min([x for x, y in symbol_around_xy])
                        symbol_ymin = min([y for x, y in symbol_around_xy])
                        symbol_xmax = max([x for x, y in symbol_around_xy])
                        symbol_ymax = max([y for x, y in symbol_around_xy])

                        arraylist_feature_xy.append(
                            [symbol_xmin, symbol_ymin, symbol_xmax, symbol_ymax])

    symbol_min_max_xy = get_symbol_area(
        step, jobname, step.name, symbolname, [0, 0], angle, mirror, dic_symbol_info=dic_symbol_info)
    symbol_xmin = min([x for x, y in symbol_min_max_xy])
    symbol_ymin = min([y for x, y in symbol_min_max_xy])
    symbol_xmax = max([x for x, y in symbol_min_max_xy])
    symbol_ymax = max([y for x, y in symbol_min_max_xy])

    # step.PAUSE(
    # str([symbol_xmin, symbol_ymin, symbol_xmax, symbol_ymax, checklayer_list]))

    new_area_x = (area_x[0], area_x[1])
    if area_x[2] < 0:
        new_area_x = (area_x[1], area_x[0])

    new_area_y = (area_y[0], area_y[1])
    if area_y[2] < 0:
        new_area_y = (area_y[1], area_y[0])

    check_arraylist_feature_xy = []
    if max_min_area_method == 'no':
        for x, y in arraylist_feature_xy:
            if new_area_x[0] < x < new_area_x[1] and new_area_y[0] < y < new_area_y[1]:
                check_arraylist_feature_xy.append([x, y, x, y])
    else:
        for min_x, min_y, max_x, max_y in arraylist_feature_xy:
            if new_area_x[0] < min_x < new_area_x[1] or \
                    new_area_y[0] < min_y < new_area_y[1] or \
                    new_area_x[0] < max_x < new_area_x[1] or \
                    new_area_y[0] < max_y < new_area_y[1]:
                check_arraylist_feature_xy.append(
                    [min_x, min_y, max_x, max_y])

    # print "------------>", len(check_arraylist_feature_xy), len(sr_repeat_area)
    if move_model_fx == "X":
        find_xy = False
        for y in numpy.arange(area_y[0], area_y[1], area_y[2]):
            find_xy = False
            for x in numpy.arange(area_x[0], area_x[1], area_x[2]):
                x1, y1 = x + symbol_xmin, y + symbol_ymin
                x2, y2 = x + symbol_xmax, y + symbol_ymax
                if new_area_x[0] < x1 < new_area_x[1] and new_area_y[0] < y1 < new_area_y[1] \
                        and new_area_x[0] < x2 < new_area_x[1] and new_area_y[0] < y2 < new_area_y[1]:

                    for rt_xmin, rt_ymin, rt_xmax, rt_ymax in sr_repeat_area:

                        # 两个区间有交集的 左右25mm的区域不添加 以免字符变动进入有效单元
                        if max(x1, rt_xmin - 25) < min(x2, rt_xmax + 25) and \
                                max(y1, rt_ymin - to_sr_area) < min(y2, rt_ymax + to_sr_area):
                            break

                        # 有效单元3mm以内的 不添加
                        if rt_xmin - to_sr_area < x1 < rt_xmax + to_sr_area and rt_ymin - to_sr_area < y1 < rt_ymax + to_sr_area:
                            break
                        if rt_xmin - to_sr_area < x2 < rt_xmax + to_sr_area and rt_ymin - to_sr_area < y2 < rt_ymax + to_sr_area:
                            break
                        if rt_xmin - to_sr_area < x1 < rt_xmax + to_sr_area and rt_ymin - to_sr_area < y2 < rt_ymax + to_sr_area:
                            break
                        if rt_xmin - to_sr_area < x2 < rt_xmax + to_sr_area and rt_ymin - to_sr_area < y1 < rt_ymax + to_sr_area:
                            break
                        if x1 <= rt_xmin <= x2 and y1 <= rt_ymin <= y2:
                            break
                        if x1 <= rt_xmin <= x2 and y1 <= rt_ymax <= y2:
                            break
                        if x1 <= rt_xmax <= x2 and y1 <= rt_ymax <= y2:
                            break
                        if x1 <= rt_xmax <= x2 and y1 <= rt_ymin <= y2:
                            break
                    else:
                        for feature_min_x, feature_min_y, feature_max_x, feature_max_y in check_arraylist_feature_xy:
                            if max_min_area_method == "no":
                                if x1 <= feature_min_x <= x2 and y1 <= feature_min_y <= y2:
                                    break
                            else:
                                if max(x1, feature_min_x) < min(x2, feature_max_x) and \
                                        max(y1, feature_min_y) < min(y2, feature_max_y):
                                    break
                        else:
                            add_pad_x, add_pad_y = x, y
                            find_xy = True
                            break

            if find_xy:
                break

    elif move_model_fx == "Y":
        find_xy = False
        for x in numpy.arange(area_x[0], area_x[1], area_x[2]):
            find_xy = False
            for y in numpy.arange(area_y[0], area_y[1], area_y[2]):
                x1, y1 = x + symbol_xmin, y + symbol_ymin
                x2, y2 = x + symbol_xmax, y + symbol_ymax
                if new_area_x[0] < x1 < new_area_x[1] and new_area_y[0] < y1 < new_area_y[1] \
                        and new_area_x[0] < x2 < new_area_x[1] and new_area_y[0] < y2 < new_area_y[1]:

                    for rt_xmin, rt_ymin, rt_xmax, rt_ymax in sr_repeat_area:

                        # 两个区间有交集的 上下25mm的区域不添加 以免字符变动进入有效单元
                        if max(x1, rt_xmin - to_sr_area) < min(x2, rt_xmax + to_sr_area) and \
                                max(y1, rt_ymin - 25) < min(y2, rt_ymax + 25):
                            break

                        # 有效单元3mm以内的 不添加
                        if rt_xmin - to_sr_area < x1 < rt_xmax + to_sr_area and rt_ymin - to_sr_area < y1 < rt_ymax + to_sr_area:
                            break
                        if rt_xmin - to_sr_area < x2 < rt_xmax + to_sr_area and rt_ymin - to_sr_area < y2 < rt_ymax + to_sr_area:
                            break
                        if rt_xmin - to_sr_area < x1 < rt_xmax + to_sr_area and rt_ymin - to_sr_area < y2 < rt_ymax + to_sr_area:
                            break
                        if rt_xmin - to_sr_area < x2 < rt_xmax + to_sr_area and rt_ymin - to_sr_area < y1 < rt_ymax + to_sr_area:
                            break
                        if x1 <= rt_xmin <= x2 and y1 <= rt_ymin <= y2:
                            break
                        if x1 <= rt_xmin <= x2 and y1 <= rt_ymax <= y2:
                            break
                        if x1 <= rt_xmax <= x2 and y1 <= rt_ymax <= y2:
                            break
                        if x1 <= rt_xmax <= x2 and y1 <= rt_ymin <= y2:
                            break
                    else:
                        for feature_min_x, feature_min_y, feature_max_x, feature_max_y in check_arraylist_feature_xy:
                            if max_min_area_method == "no":
                                if x1 <= feature_min_x <= x2 and y1 <= feature_min_y <= y2:
                                    break
                            else:
                                if max(x1, feature_min_x) < min(x2, feature_max_x) and \
                                        max(y1, feature_min_y) < min(y2, feature_max_y):
                                    break
                        else:
                            add_pad_x, add_pad_y = x, y
                            find_xy = True
                            break

            if find_xy:
                break

    if return_check_feature_xy == "yes":
        return add_pad_x, add_pad_y, False, arraylist_feature_xy

    if not move_length:
        if find_xy:
            return add_pad_x, add_pad_y, False

        return False

    move_size = 0
    manual_move = False
    while True:
        # print "-------->", move_size, move_length,find_xy
        if move_size <= move_length:
            step.clearAll()
            step.affect(worklayer)
            step.selectDelete()
            step.addPad(add_pad_x + move_x_flag * move_size,
                        add_pad_y + move_y_flag * move_size,
                        symbolname, angle=angle, mirror=mirror)

        step.clearAll()
        for layer in checklayer_list:
            if step.isLayer(layer):
                step.affect(layer)

        step.resetFilter()
        step.COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad;line;arc;text,\
            polarity=positive;negative,exclude_syms=%s" % (";".join(exclude_symbols + ["r1250"])))
        step.refSelectFilter(worklayer)
        if step.featureSelected():
            """此处过滤板边铺铜的线元素 例如307780c06a2"""
            step.setAttrFilter(".bit,text=copper")
            step.COM('''filter_area_end,layer=,filter_name=popup,operation=unselect,\
                area_type=none,inside_area=no,intersect_area=no,lines_only=no,\
                ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0''')
            step.resetFilter()
            step.setAttrFilter(".pattern_fill")
            step.COM('''filter_area_end,layer=,filter_name=popup,operation=unselect,\
                area_type=none,inside_area=no,intersect_area=no,lines_only=no,\
                ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0''')

        if "fill" in checklayer_list and not step.featureSelected():
            step.clearAll()
            step.affect("fill")
            step.resetFilter()
            step.refSelectFilter(worklayer)

        if step.featureSelected():
            move_size += 2
        else:
            if find_xy:
                break

        if move_size > move_length or not find_xy:
            move_size += 2
            if manual_add == "yes":
                if sys.platform == "win32":

                    os.system("python %s/sys/scripts/suntak/lyh/messageBox.py %s" %
                              (os.environ["GENESIS_DIR"], msg))
                else:
                    if os.path.exists("/incam2"):
                        os.system("python /incam2/server/site_data/scripts/suntak/lyh/autoRunScripts.py messageBox %s" %
                                  (msg))
                    else:
                        os.system("python /incam/server/site_data/scripts/suntak/lyh/autoRunScripts.py messageBox %s" %
                                  (msg))
                step.clearAll()
                step.display(worklayer)
                step.COM("pan_center,x=%s,y=%s" % (add_pad_x + move_x_flag * move_size,
                                                   add_pad_y + move_y_flag * move_size))
                step.COM("zoom_factor,factor=1.000000:0.400000")
                step.PAUSE("cannot auto select position, please manual move %s" %
                           symbolname)
                manual_move = True
                find_xy = True
                # break
            else:
                # 自动的无法添加 程序不添加
                return False

    step.clearAll()
    layercmd = gClasses.Layer(step, worklayer)
    pad_info = layercmd.featOut(units="mm")["pads"]
    pad_x = pad_info[0].x
    pad_y = pad_info[0].y

    return pad_x, pad_y, manual_move

def convert_coordinate_in_panel_edge(step, x, y, x_center, y_center, mode):
    """板边坐标对称或旋转转换"""
    new_x = x
    new_y = y
    if mode == u"斜对称转换":
        "短边或长边左上角到右下角等"
        if x < x_center:
            new_x = x_center - x + x_center
        else:
            new_x = x_center - (x - x_center)
            
        if y < y_center:
            new_y = y_center - y + y_center
        else:
            new_y = y_center - (y - y_center)
            
    return new_x, new_y
            

def auto_add_features_in_panel_edge_new(step, add_pad_x, add_pad_y,
                                        worklayer, symbolname,
                                        checklayer_list, msg,
                                        move_x_flag, move_y_flag,
                                        angle, manual_add="yes",
                                        move_length=100, attr_name="",
                                        set_attr="", site_id="hdi_1",
                                        to_feat_size=0, area_x=[0, 0, 0],
                                        area_y=[0, 0, 0], move_model_fx="X",
                                        mirror="no", to_sr_area=3,
                                        exclude_symbols=[], exists_arraylist_feature_xy=[],
                                        return_check_feature_xy="no", check_sr_area="yes",
                                        max_min_area_method="no", dic_all_symbol_info={},
                                        convert_coordinate_mode=None):

    new_area_x = (area_x[0], area_x[1])
    if area_x[2] < 0:
        new_area_x = (area_x[1], area_x[0])

    new_area_y = (area_y[0], area_y[1])
    if area_y[2] < 0:
        new_area_y = (area_y[1], area_y[0])
        
    f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
    x_center = (f_xmin + f_xmax) * 0.5
    y_center = (f_ymin + f_ymax) * 0.5
    
    # max_min_area_method 为yes时 改为区间法则 提升计算效率 20220517 by lyh
    if check_sr_area == "yes":
        step.removeLayer(worklayer)
        step.createLayer(worklayer)

        sr_repeat_area = get_sr_area_value(step.name)
        
        if convert_coordinate_mode is not None:
            sr_repeat_area_tmp = []
            for xmin1, ymin1, xmax1, ymax1 in sr_repeat_area:
                x1, y1 = convert_coordinate_in_panel_edge(step, xmin1, ymin1,
                                                          x_center, y_center, convert_coordinate_mode)
                x2, y2 = convert_coordinate_in_panel_edge(step, xmax1, ymax1,
                                                          x_center, y_center, convert_coordinate_mode)
                xmin1 = min([x1, x2])
                ymin1 = min([y1, y2])
                xmax1 = max([x1, x2])
                ymax1 = max([y1, y2])
                sr_repeat_area_tmp.append([xmin1, ymin1, xmax1, ymax1])
                
            sr_repeat_area = sr_repeat_area_tmp[:]

        if set_attr:
            layer_cmd = gClasses.Layer(step, worklayer)
            layer_cmd.setGenesisAttr(attr_name, set_attr)
    else:
        sr_repeat_area = []    

    if exists_arraylist_feature_xy:
        arraylist_feature_xy = exists_arraylist_feature_xy
    else:
        arraylist_feature_xy = []
        
    if not exists_arraylist_feature_xy:
        for layer in checklayer_list:
            if step.isLayer(layer):
                layer_cmd = gClasses.Layer(step, layer)
                feat_out = layer_cmd.featCurrent_LayerOut(units="mm")
                pad_feat_out = feat_out["pads"]                

                text_feat_out = feat_out["text"]
                for obj in text_feat_out:    
                    if abs(obj.rotation) in [0, 90, 180, 270]:
                        if "zuanzi" in obj.text:
                            # 取最大长度字符串
                            obj.text = "P00 WLW190-268B1-B3-8 L1.000000 W1.000000"
                            
                        if abs(obj.rotation) in [0, 180]:                            
                            obj.x = obj.x + len(obj.text) *obj.xsize * 0.5
                            obj.y = obj.y + obj.ysize * 0.5
                            if abs(obj.rotation) == 180:
                                obj.x = obj.x - len(obj.text) *obj.xsize * 0.5
                                obj.y = obj.y - obj.ysize * 0.5
                            obj.symbol = "rect%sx%s" % (len(obj.text) *obj.xsize * 1000, obj.ysize * 1000)
                        else:
                            if abs(obj.rotation) == 270:
                                obj.x = obj.x + obj.ysize * 0.5
                                obj.y = obj.y - len(obj.text) *obj.xsize * 0.5
                            else:
                                obj.x = obj.x - obj.ysize * 0.5
                                obj.y = obj.y + len(obj.text) *obj.xsize * 0.5                  
                            obj.symbol = "rect%sx%s" % (obj.ysize * 1000, len(obj.text) *obj.xsize * 1000)
                            
                        obj.rotation = 0
                        pad_feat_out.append(obj)                   

                line_feat_out = feat_out["lines"]
                r500_fill_lines = [obj for obj in line_feat_out
                                   if obj.symbol[0] == "r"
                                   and hasattr(obj, "pattern_fill")]

                for obj in line_feat_out:

                    if hasattr(obj, "pattern_fill") and \
                            obj.symbol == "r1250":
                        continue
                    
                    if 'dk' in layer or 'gk' in layer:
                        if hasattr(obj, "pattern_fill"):
                            continue
                        
                    if obj.symbol == "r1":
                        continue

                    if len(r500_fill_lines) > 500:
                        # 剔除掉板边的填充网格线
                        if obj in r500_fill_lines:
                            continue

                    if abs(obj.angle) in [0, 90, 180, 270]:
                        obj.x = (obj.xe + obj.xs) * 0.5
                        obj.y = (obj.ye + obj.ys) * 0.5
                        # obj.rotation = abs(obj.angle)
                        obj.mirror = "no"
                        if abs(obj.angle) in [0, 180]:
                            obj.symbol = "rect%sx%s" % (
                                obj.len * 1000 + float(obj.symbol[1:]), obj.symbol[1:])
                        else:
                            obj.symbol = "rect%sx%s" % (
                                obj.symbol[1:], obj.len * 1000 + float(obj.symbol[1:]))

                        obj.rotation = 0
                        pad_feat_out.append(obj)

                # layer_cell = layer_cmd.cell
                size = to_feat_size
                #if getattr(layer_cell, "layer_type", None) and \
                        #layer_cell.layer_type == "drill":
                    #size = to_feat_size + 1

                if 'inn' in layer and "inn-pp" not in layer:
                    size = 5                                  

                for obj in pad_feat_out:

                    if obj.symbol in exclude_symbols:
                        continue

                    extra_size = 0
                    # if getattr(obj, "xs", None):
                    # 线元素多避开一点
                    # extra_size = 3

                    if return_check_feature_xy == "yes":
                        extra_size = 0

                    symbol_around_xy = get_symbol_area(step, jobname, step.name,
                                                       obj.symbol, [obj.x,obj.y],
                                                       obj.rotation, obj.mirror,
                                                       to_feat_size=size + extra_size,
                                                       dic_symbol_info=dic_all_symbol_info)
                    #if "192.168.19.243" in localip[2]:
                        #if obj.symbol in ["sh-opnew2021+3mil", "s4000"]:
                            #step.PAUSE(
                            #str(symbol_around_xy+[obj.symbol]))
                            
                    symbol_xmin = min([x for x, y in symbol_around_xy])
                    symbol_ymin = min([y for x, y in symbol_around_xy])
                    symbol_xmax = max([x for x, y in symbol_around_xy])
                    symbol_ymax = max([y for x, y in symbol_around_xy])
                    
                    if symbol_xmin != symbol_xmax and symbol_ymin != symbol_ymax:                          
                        arraylist_feature_xy.append(
                            [symbol_xmin, symbol_ymin, symbol_xmax, symbol_ymax])
                        if convert_coordinate_mode is not None:
                                                  
                            x1, y1 = convert_coordinate_in_panel_edge(step, symbol_xmin, symbol_ymin,
                                                                      x_center, y_center, convert_coordinate_mode)
                            x2, y2 = convert_coordinate_in_panel_edge(step, symbol_xmax, symbol_ymax,
                                                                      x_center, y_center, convert_coordinate_mode)
                            #step.PAUSE(str([symbol_xmin, symbol_ymin, symbol_xmax, symbol_ymax,
                                            #symbol_xmin1, symbol_ymin1, symbol_xmax1, symbol_ymax1]))
                            symbol_xmin1 = min([x1, x2])
                            symbol_ymin1 = min([y1, y2])
                            symbol_xmax1 = max([x1, x2])
                            symbol_ymax1 = max([y1, y2])
                            arraylist_feature_xy.append(
                                [symbol_xmin1, symbol_ymin1, symbol_xmax1, symbol_ymax1])                            
                            # step.PAUSE(str(arraylist_feature_xy))
                            #if obj.symbol == "rect9000x20000":
                                #step.PAUSE(str([symbol_xmin, symbol_ymin, symbol_xmax, symbol_ymax,
                                                #symbol_xmin1, symbol_ymin1, symbol_xmax1, symbol_ymax1,
                                                #new_area_x, new_area_y,
                                                #x1, y1, x2, y2]))                                  
                            #if max(new_area_x[0], symbol_xmin1) < min(new_area_x[1], symbol_xmax1) and \
                                    #max(new_area_y[0], symbol_ymin1) < min(new_area_y[1], symbol_ymax1):                            
                                #step.addRectangle(symbol_xmin, symbol_ymin, symbol_xmax, symbol_ymax)
                                #step.addPad(obj.x,obj.y, obj.symbol)
                                #step.addRectangle(symbol_xmin1, symbol_ymin1, symbol_xmax1, symbol_ymax1)
                                #step.PAUSE(str([symbol_xmin, symbol_ymin, symbol_xmax, symbol_ymax,
                                                #symbol_xmin1, symbol_ymin1, symbol_xmax1, symbol_ymax1]))                                 

    symbol_min_max_xy = get_symbol_area(
        step, jobname, step.name, symbolname, [0, 0], angle, mirror, dic_symbol_info=dic_all_symbol_info)
    symbol_xmin = min([x for x, y in symbol_min_max_xy])
    symbol_ymin = min([y for x, y in symbol_min_max_xy])
    symbol_xmax = max([x for x, y in symbol_min_max_xy])
    symbol_ymax = max([y for x, y in symbol_min_max_xy])

    #step.PAUSE(
    #str([symbol_xmin, symbol_ymin, symbol_xmax, symbol_ymax, checklayer_list]))
        
    check_arraylist_feature_xy = []
    if max_min_area_method == 'no':
        for x, y in arraylist_feature_xy:
            if new_area_x[0] < x < new_area_x[1] and new_area_y[0] < y < new_area_y[1]:
                check_arraylist_feature_xy.append([x, y, x, y])
    else:
        for min_x, min_y, max_x, max_y in arraylist_feature_xy:
            if max(new_area_x[0], min_x) < min(new_area_x[1], max_x) and \
                    max(new_area_y[0], min_y) < min(new_area_y[1], max_y):
                check_arraylist_feature_xy.append(
                    [min_x, min_y, max_x, max_y])

    #print "------------>", check_arraylist_feature_xy
    if "192.168.19.243" in localip[2]:
        step.clearAll()
        step.affect(worklayer)
        for xs, ys, xe, ye in check_arraylist_feature_xy:        
            step.addRectangle(xs, ys, xe, ye)
        step.PAUSE("ddd")
    
    if move_model_fx == "X":
        find_xy = False
        for y in numpy.arange(area_y[0], area_y[1], area_y[2]):
            find_xy = False
            for x in numpy.arange(area_x[0], area_x[1], area_x[2]):
                x1, y1 = x + symbol_xmin, y + symbol_ymin
                x2, y2 = x + symbol_xmax, y + symbol_ymax
                if new_area_x[0] < x1 < new_area_x[1] and new_area_y[0] < y1 < new_area_y[1] \
                        and new_area_x[0] < x2 < new_area_x[1] and new_area_y[0] < y2 < new_area_y[1]:

                    for rt_xmin, rt_ymin, rt_xmax, rt_ymax in sr_repeat_area:

                        # 两个区间有交集的 区域不添加 以免字符变动进入有效单元
                        if max(x1, rt_xmin - to_sr_area) < min(x2, rt_xmax + to_sr_area) and \
                                max(y1, rt_ymin - to_sr_area) < min(y2, rt_ymax + to_sr_area):
                            break
                        
                    else:
                        for feature_min_x, feature_min_y, feature_max_x, feature_max_y in check_arraylist_feature_xy:
                            if max_min_area_method == "no":
                                if x1 <= feature_min_x <= x2 and y1 <= feature_min_y <= y2:
                                    break
                            else:
                                if max(x1, feature_min_x) < min(x2, feature_max_x) and \
                                        max(y1, feature_min_y) < min(y2, feature_max_y):
                                    break
                        else:
                            add_pad_x, add_pad_y = x, y
                            find_xy = True
                            break

            if find_xy:
                break

    elif move_model_fx == "Y":
        find_xy = False
        for x in numpy.arange(area_x[0], area_x[1], area_x[2]):
            find_xy = False
            for y in numpy.arange(area_y[0], area_y[1], area_y[2]):
                x1, y1 = x + symbol_xmin, y + symbol_ymin
                x2, y2 = x + symbol_xmax, y + symbol_ymax
                if new_area_x[0] < x1 < new_area_x[1] and new_area_y[0] < y1 < new_area_y[1] \
                        and new_area_x[0] < x2 < new_area_x[1] and new_area_y[0] < y2 < new_area_y[1]:

                    for rt_xmin, rt_ymin, rt_xmax, rt_ymax in sr_repeat_area:

                        # 两个区间有交集的 区域不添加 以免字符变动进入有效单元
                        if max(x1, rt_xmin - to_sr_area) < min(x2, rt_xmax + to_sr_area) and \
                                max(y1, rt_ymin - to_sr_area) < min(y2, rt_ymax + to_sr_area):
                            break
                    else:
                        for feature_min_x, feature_min_y, feature_max_x, feature_max_y in check_arraylist_feature_xy:
                            if max_min_area_method == "no":
                                if x1 <= feature_min_x <= x2 and y1 <= feature_min_y <= y2:
                                    break
                            else:
                                if max(x1, feature_min_x) < min(x2, feature_max_x) and \
                                        max(y1, feature_min_y) < min(y2, feature_max_y):
                                    break
                        else:
                            add_pad_x, add_pad_y = x, y
                            find_xy = True
                            break

            if find_xy:
                break

    if return_check_feature_xy == "yes":
        return add_pad_x, add_pad_y, False, arraylist_feature_xy

    if not move_length:
        if find_xy:
            return add_pad_x, add_pad_y, False

        return False
    
    #step.clearAll()
    #step.affect(worklayer)
    #step.addPad(add_pad_x ,
                #add_pad_y,
                #symbolname, angle=angle, mirror=mirror)
    #if "192.168.19.243" in localip[2]:
        #step.PAUSE(str([add_pad_x, add_pad_y, find_xy]))
    move_size = 0
    manual_move = False
    while True:
        # print "-------->", move_size, move_length,find_xy
        if move_size <= move_length:
            step.clearAll()
            step.affect(worklayer)
            step.selectDelete()
            step.addPad(add_pad_x + move_x_flag * move_size,
                        add_pad_y + move_y_flag * move_size,
                        symbolname, angle=angle, mirror=mirror)

        step.clearAll()
        for layer in checklayer_list:
            if step.isLayer(layer):
                step.affect(layer)

        step.resetFilter()
        step.COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad;line;arc,\
            polarity=positive;negative,exclude_syms=%s" % (";".join(exclude_symbols + ["r1250", "r1"])))
        step.refSelectFilter(worklayer)
        if step.featureSelected():
            """此处过滤板边铺铜的线元素 例如307780c06a2"""
            step.setAttrFilter(".bit,text=copper")
            step.COM('''filter_area_end,layer=,filter_name=popup,operation=unselect,\
                area_type=none,inside_area=no,intersect_area=no,lines_only=no,\
                ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0''')
            step.resetFilter()
            step.setAttrFilter(".pattern_fill")
            step.COM('''filter_area_end,layer=,filter_name=popup,operation=unselect,\
                area_type=none,inside_area=no,intersect_area=no,lines_only=no,\
                ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0''')

        if "fill" in checklayer_list and not step.featureSelected():
            step.clearAll()
            step.affect("fill")
            step.resetFilter()
            step.refSelectFilter(worklayer)

        if step.featureSelected():
            move_size += 2
        else:
            if find_xy:
                break

        if move_size > move_length or not find_xy:
            move_size += 2
            if manual_add == "yes":
                if sys.platform == "win32":
                    os.system("python %s/sys/scripts/lyh/messageBox.py %s" %
                              (os.environ["GENESIS_DIR"], msg))
                else:
                    os.system("python /incam/server/site_data/scripts/lyh/messageBox.py %s" %
                              (msg))
                    
                if "-lyh" in step.job.name:
                    step.PAUSE("please check {0}".format(find_xy))
                    
                step.clearAll()
                step.display(worklayer)
                step.COM("pan_center,x=%s,y=%s" % (add_pad_x + move_x_flag * move_size,
                                                   add_pad_y + move_y_flag * move_size))
                step.COM("zoom_factor,factor=1.000000:0.400000")
                step.PAUSE("cannot auto select position, please manual move %s" %
                           symbolname)
                manual_move = True
                find_xy = True
                # break
            else:
                # 自动的无法添加 程序不添加
                return False

    step.clearAll()
    layercmd = gClasses.Layer(step, worklayer)
    pad_info = layercmd.featOut(units="mm")["pads"]
    pad_x = pad_info[0].x
    pad_y = pad_info[0].y
    angle = pad_info[0].rotation

    return pad_x, pad_y, angle, manual_move


def get_symbol_area(step, jobname, stepname,
                    symbolname, symbol_xy, angle,
                    mirror, to_feat_size=0,
                    dic_symbol_info={}):
    """获取symbol的区域坐标范围 20220128 by lyh"""

    arraylist_xy = []
    arraylist_xy.append(symbol_xy)

    if sys.platform == "win32":
        symbolpath = os.path.join(job.dbpath, "symbols", symbolname)
    else:
        symbolpath = "/incam/server/site_data/library/symbols/%s" % symbolname

    get_symbol_limits = True
    if dic_symbol_info.has_key(symbolname):
        xmin, ymin, xmax, ymax = dic_symbol_info[symbolname]
        get_symbol_limits = False
        
    #if "-lyh" in jobname:        
        #print dic_symbol_info
        #print symbolname
        #print symbolname in dic_symbol_info.keys()
        
        # step.PAUSE(str([symbolname, get_symbol_limits, dic_symbol_info.has_key(symbolname)]))

    if os.path.exists(symbolpath):
        if get_symbol_limits:
            if sys.platform == "win32":
                info = step.DO_INFO("-t symbol -e %s/%s -d LIMITS,units= mm" %
                                    (jobname, symbolname))
            else:
                info = step.DO_INFO("-t symbol -e %s/%s -d LIMITS,units= mm" %
                                    (jobname, symbolname))                
            xmin = info["gLIMITSxmin"]
            ymin = info["gLIMITSymin"]
            xmax = info["gLIMITSxmax"]
            ymax = info["gLIMITSymax"]
    else:
        if not dic_symbol_info.has_key(symbolname):
            result = re.findall("\d+(?:\.\d+)?", symbolname)
            if result:
                max_size = 0
                try:
                    max_size = max([float(size) for size in result])
                except:
                    pass
                if "rect" in symbolname or "oval" in symbolname:
                    a, b = result[0], result[1]
                    # if angle == 90 or angle == 270:
                    # xmin = -float(b) / 2000.0
                    # ymin = -float(a) / 2000.0
                    # xmax = float(b) / 2000.0
                    # ymax = float(a) / 2000.0
                    # else:
                    xmin = -float(a) / 2000.0
                    ymin = -float(b) / 2000.0
                    xmax = float(a) / 2000.0
                    ymax = float(b) / 2000.0
                else:
    
                    if max_size:
                        xmin = -max_size / 2000.0
                        ymin = -max_size / 2000.0
                        xmax = max_size / 2000.0
                        ymax = max_size / 2000.0
                    else:
                        return arraylist_xy
            else:
                return arraylist_xy

    orig_center_x = (xmax + xmin) * 0.5
    orig_center_y = (ymax + ymin) * 0.5

    if angle == 90:
        feature_center_x = orig_center_y
        feature_center_y = orig_center_x * -1
    elif angle == 180:
        feature_center_x = orig_center_x * -1
        feature_center_y = orig_center_y * -1
    elif angle == 270:
        feature_center_x = orig_center_y * -1
        feature_center_y = orig_center_x
    else:
        feature_center_x = orig_center_x
        feature_center_y = orig_center_y

    if mirror == "yes":
        feature_center_x = feature_center_x * -1

    sb_x = symbol_xy[0] + feature_center_x
    sb_y = symbol_xy[1] + feature_center_y

    #if "192.168.19.243" in localip[2] and symbolname in ["circle_2", "sh-ldi"]:        
        #step.PAUSE(
        #str([sb_x, sb_y, feature_center_x, feature_center_y, symbolname, angle]))
    # 定义好四个象限数组 左下 右下 右上 左上
    arraylist_flag = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    #for a, b, c, d in [[(-1, -1), (1, -1), (1, 1), (-1, 1)]]:
        #arraylist_flag.append((a, b, c, d))

    #for zu_info in arraylist_flag:
    for i, zu in enumerate(arraylist_flag):
        flag_x, flag_y = zu
        if angle == 0 or angle == 180:
            new_xmin = abs(xmax - xmin) * 0.5 + to_feat_size
            new_ymin = abs(ymax - ymin) * 0.5 + to_feat_size
            new_xmax = abs(xmax - xmin) * 0.5 + to_feat_size
            new_ymax = abs(ymax - ymin) * 0.5 + to_feat_size
        if angle == 90 or angle == 270:
            new_xmin = abs(ymax - ymin) * 0.5 + to_feat_size
            new_ymin = abs(xmax - xmin) * 0.5 + to_feat_size
            new_xmax = abs(ymax - ymin) * 0.5 + to_feat_size
            new_ymax = abs(xmax - xmin) * 0.5 + to_feat_size

        if (angle == 0 and i == 0) or \
                (angle == 90 and i == 1) or \
                (angle == 180 and i == 2) or \
                (angle == 270 and i == 3):  # 左下
            arraylist_xy.append((sb_x + new_xmin *
                                 flag_x, sb_y + new_ymin * flag_y))

        if (angle == 0 and i == 1) or \
                (angle == 90 and i == 2) or \
                (angle == 180 and i == 3) or \
                (angle == 270 and i == 0):  # 右下
            arraylist_xy.append((sb_x + new_xmax *
                                 flag_x, sb_y + new_ymin * flag_y))

        if (angle == 0 and i == 2) or \
                (angle == 90 and i == 3) or \
                (angle == 180 and i == 0) or \
                (angle == 270 and i == 1):  # 右上
            arraylist_xy.append((sb_x + new_xmax *
                                 flag_x, sb_y + new_ymax * flag_y))

        if (angle == 0 and i == 3) or \
                (angle == 90 and i == 0) or \
                (angle == 180 and i == 1) or \
                (angle == 270 and i == 2):  # 左上
            arraylist_xy.append((sb_x + new_xmin *
                                 flag_x, sb_y + new_ymax * flag_y))

    return arraylist_xy


def calcExposeArea(step, layer1,
                   mask1, layer2,
                   mask2, thickness,
                   area_x1=0, area_y1=0,
                   area_x2=0, area_y2=0,
                   units="mm", drillLayers=["drl"]):  # 计算金面积

    area_conditon = "no"
    if area_x1 or area_x2 or area_y1 or area_y2:
        area_conditon = "yes"

    step.COM("units,type=" + units)
    if units == "mm":
        step.COM(
            "exposed_area,layer1=%s,mask1=%s,layer2=%s,mask2=%s,mask_mode=or,drills=yes,"
            "drills_list=%s,consider_rout=no,"
            "drills_source=matrix,thickness=%s,"
            "resolution_value=25.4,x_boxes=3,y_boxes=3,area=%s,x1=%s,y1=%s,x2=%s,y2=%s,"
            "dist_map=yes" % (layer1, mask1, layer2, mask2, ";".join(drillLayers),
                              thickness * 1000, area_conditon,
                              area_x1, area_y1,
                              area_x2, area_y2))
    else:
        step.COM(
            "exposed_area,layer1=%s,mask1=%s,layer2=%s,mask2=%s,mask_mode=or,"
            "drills=yes,drills_list=%s,consider_rout=no,"
            "drills_source=matrix,thickness=%s,"
            "resolution_value=1,x_boxes=3,y_boxes=3,area=%s,x1=%s,y1=%s,x2=%s,y2=%s,"
            "dist_map=yes" % (layer1, mask1, layer2, mask2, ";".join(drillLayers),
                              thickness * 39.37, area_conditon,
                              area_x1, area_y1,
                              area_x2, area_y2))

    areaInfo = step.COMANS
    mianji, average = ["%.2f" % float(areaInfo.split()[0]), "%.2f" % float(areaInfo.split()[1])]

    return mianji, average


def calcCopperArea(step,
                   layer1, layer2,
                   thickness,
                   area_x1=0, area_y1=0,
                   area_x2=0, area_y2=0,
                   units="mm", drillLayers=["drl"]):  # 计算铜面积
    
    area_conditon = "no"
    if area_x1 or area_x2 or area_y1 or area_y2:
        area_conditon = "yes"

    step.COM("units,type=" + units)
    if drillLayers:
        drills = "yes"
    else:
        drills = "no"

    if units == "mm":
        step.COM("copper_area,layer1=%s,layer2=%s,drills=%s,drills_list=%s,consider_rout=no,"
                 "ignore_pth_no_pad=no,drills_source=matrix,thickness=%s,"
                 "resolution_value=25.4,x_boxes=3,y_boxes=3,area=%s,x1=%s,y1=%s,x2=%s,y2=%s,"
                 "dist_map=yes" % (layer1, layer2, drills, ";".join(drillLayers),
                                   thickness * 1000 / 2.0, area_conditon,
                                   area_x1, area_y1,
                                   area_x2, area_y2))
    else:
        step.COM("copper_area,layer1=%s,layer2=%s,drills=%s,drills_list=%s,consider_rout=no,"
                 "ignore_pth_no_pad=no,drills_source=matrix,thickness=%s,"
                 "resolution_value=1,x_boxes=3,y_boxes=3,area=%s,x1=%s,y1=%s,x2=%s,y2=%s,"
                 "dist_map=yes" % (layer1, layer2, drills, ";".join(drillLayers),
                                   thickness * 39.37 / 2.0, area_conditon,
                                   area_x1, area_y1,
                                   area_x2, area_y2))

    areaInfo = step.COMANS
    mianji, average = ["%.2f" % float(areaInfo.split()[0]), "%.2f" % float(areaInfo.split()[1])]

    return mianji, average


def outputgerber274x(step, worklayer, mirror,
                     scale_x, scale_y, jobname,
                     stepname, outputpath,
                     prefix, suffix, units,
                     break_symbols="yes",
                     x_anchor=0, y_anchor=0):
    """gerber274x资料输出"""
    min_brush = 0.1 if units == "inch" else 25.4
    nf1 = 2 if units == "inch" else 3
    nf2 = 6 if units == "inch" else 5
    step.COM("output_layer_reset")
    step.COM("output_layer_set,layer=%s,angle=0,mirror=%s,x_scale=%s,y_scale=%s,\
    comp=0,polarity=positive,setupfile=,setupfiletmp=,\
    line_units=%s,gscl_file=" % (worklayer, mirror, scale_x, scale_y, units))
    step.COM("output,job=%s,step=%s,format=Gerber274x,dir_path=%s,\
    prefix=%s,suffix=%s,break_sr=yes,break_symbols=%s,break_arc=no,\
    scale_mode=nocontrol,surface_mode=contour,min_brush=%s,units=%s,coordinates=absolute,\
    zeroes=none,nf1=%s,nf2=%s,x_anchor=%s,y_anchor=%s,wheel=,x_offset=0,\
    y_offset=0,line_units=%s,override_online=yes,film_size_cross_scan=0,\
    film_size_along_scan=0,\
    ds_model=RG6500" % (jobname, stepname, outputpath, prefix,
                        suffix, break_symbols, min_brush, units,
                        nf1, nf2, x_anchor, y_anchor, units ))


def outputgerber274x_incam(step, worklayer, mirror,
                           scale_x, scale_y, jobname,
                           stepname, outputpath,
                           prefix, suffix, units,
                           break_symbols="yes",
                           x_anchor=0, y_anchor=0):
    min_brush = 0.125 if units == "inch" else 25.4
    nf1 = 2 if units == "inch" else 3
    nf2 = 6 if units == "inch" else 5
    step.COM("set_step,name=%s" % stepname)
    step.COM("output_add_device,type=format,name=Gerber274x")
    step.COM("output_device_show,type=format,name=Gerber274x")
    step.COM("output_reload_device,type=format,name=Gerber274x")
    step.COM(
        "output_device_show_layer,type=format,name=Gerber274x,layer=%s" % worklayer)
    step.COM("output_update_device,type=format,name=Gerber274x,dir_path=%s,\
    prefix=%s,suffix=%s,x_anchor=%s,y_anchor=%s,x_offset=0,y_offset=0,line_units=%s,\
    format_params=(break_sr=no)(break_symbols=%s)(break_arc=yes)(scale_mode=all)\
    (surface_mode=contour)(min_brush=%s)(units=%s)(coordinates=absolute)(zeroes=none)\
    (nf1=%s)(nf2=%s)(wheel=)(out_zero_line_to_pad=yes)(out_gbr_empty_macro_stop=no)\
    (out_gbr_modal=yes)(out_274x_apr_max_size=50000)(out_274x_special_max_elements=1000000)\
    (out_274x_poly_max_edges=1000000)(out_274x_rotate_octagon=no)(out_274x_single_sf=no)\
    (out_274x_stop_ill_polygon=no)(out_gbr_override_standard_precision=no)(out_274x_trans_parameters=yes)\
    (iol_out_allow_overlapping_profiles=yes)(iol_274x_sr_ij_scaled=no)(out_sqr_diag_line=0)" % (outputpath, prefix,
                                                                                                suffix,x_anchor, y_anchor,
                                                                                                units,break_symbols, 
                                                                                                min_brush, units, nf1,
                                                                                                nf2))
    """output_update_device,type=format,name=Gerber274x,dir_path=,
    prefix=,suffix=,x_anchor=0,y_anchor=0,x_offset=0,y_offset=0,line_units=inch,
    format_params=(break_sr=no)(break_symbols=yes)(break_arc=yes)(scale_mode=all)
    (surface_mode=contour)(min_brush=1)(units=inch)(coordinates=absolute)(zeroes=none)
    (nf1=2)(nf2=4)(wheel=)(out_zero_line_to_pad=yes)(out_gbr_empty_macro_stop=no)
    (out_gbr_modal=yes)(out_274x_apr_max_size=50000)(out_274x_special_max_elements=1000000)
    (out_274x_poly_max_edges=1000000)(out_274x_rotate_octagon=no)(out_274x_single_sf=no)
    (out_274x_stop_ill_polygon=no)(out_274x_trans_parameters=yes)(out_gbr_override_standard_precision=no)
    (iol_out_allow_overlapping_profiles=yes)(iol_274x_sr_ij_scaled=no)(out_sqr_diag_line=0)"""
    
    step.COM(
        "output_device_set_lyrs_filter,type=format,name=Gerber274x,layers_filter=")
    step.COM("output_update_device_layer,type=format,name=Gerber274x,\
    layer=%s,angle=0,x_mirror=%s,y_mirror=no,x_scale=%s,y_scale=%s,\
    comp=0,polarity=positive,setupfile=, setupfiletmp=,line_units=%s,gscl_file=,\
    incl_attrs=,excl_attrs=,logic_incl_attrs=and,logic_excl_attrs=and" % (worklayer, mirror, scale_x, scale_y, units))

    step.COM("output_device_select_reset,type=format,name=Gerber274x")
    step.COM(
        "output_device_select_item,type=format,name=Gerber274x,item=%s,select=yes" % worklayer)
    step.COM(
        "output_device,type=format,name=Gerber274x,overwrite=yes,overwrite_ext=,on_checkout_by_other=output_anyway")


def ncOutPutFile(step, jobname,
                 XSCALE, YSCALE,
                 X_org, Y_org,
                 X_center, Y_center,
                 outputPath, machine,
                 outputLayer, mirror,
                 angle, optimize="yes",
                 stepname="panel"):
    filepath = os.path.join(outputPath, "%s_%s x=%s y=%s.drl" % (
        jobname, outputLayer, XSCALE, YSCALE))
    if os.path.exists(filepath):
        os.unlink(filepath)
    Prof_xmin, Prof_ymin, Prof_xmax, Prof_ymax = \
        get_profile_limits(step)
    step.COM("matrix_layer_type,job=%s,matrix=matrix,layer=%s,type=drill" %
             (jobname, outputLayer))
    step.COM('ncset_cur,job=%s,step=%s,layer=%s,ncset=%s' %
             (jobname, stepname, outputLayer, os.getpid()))
    step.COM('ncd_set_machine,machine=%s,thickness=0' % machine)
    step.COM('ncset_units,units=mm')
    step.COM('disp_on')
    step.COM('origin_on')
    step.COM('ncd_auto_all,create_drill=no')
    if Prof_xmax > 1000 or Prof_ymax > 1000:
        step.COM('ncd_set_params,format=Excellon2,zeroes=trailing,\
        units=mm,tool_units=mm,nf1=4,nf2=3,decimal=no,modal_coords=no,\
        single_sr=yes,sr_zero_set=no,repetitions=sr,incremental=no,\
        optimize=%s,iterations=10,reduction_percent=1,cool_spread=0,\
        break_sr=yes,sort_method=Standard,strip_width=0,xspeed=2540,yspeed=2540,\
        rout_layer=ncd,fixed_tools=yes,tools_assign_mode=increasing_size,\
        comp_short_slot=no' % optimize)
    else:
        step.COM('ncd_set_params,format=Excellon2,zeroes=trailing,\
        units=mm,tool_units=mm,nf1=3,nf2=3,decimal=no,modal_coords=no,\
        single_sr=yes,sr_zero_set=no,repetitions=sr,incremental=no,\
        optimize=%s,iterations=10,reduction_percent=1,cool_spread=0,\
        break_sr=yes,sort_method=Standard,strip_width=0,xspeed=2540,yspeed=2540,\
        rout_layer=ncd,fixed_tools=yes,tools_assign_mode=increasing_size,\
        comp_short_slot=no' % optimize)
    step.COM('ncd_register,angle=%s,mirror=%s,xoff=0,yoff=0,\
    version=1,xorigin=%s,yorigin=%s,xscale=%s,yscale=%s,\
    xscale_o=%s,yscale_o=%s' % (angle, mirror, X_org, Y_org, XSCALE, YSCALE, X_center, Y_center))
    step.COM('ncd_cre_drill')
    step.COM('ncd_ncf_export,stage=1,split=1,dir=%s,\
    name=%s' % (outputPath, "%s_%s x=%s y=%s.drl" % (jobname, outputLayer, XSCALE, YSCALE)))
    step.COM('ncset_page_close')

    return filepath


def exportRout(step, jobname, stepname,
               layer, xscale, yscale,
               xcenter, ycenter, outputpath,
               machine, is_compensate=False,
               is_report=False, xorigin=0,
               yorigin=0, xoff=0, yoff=0):
    step.COM("matrix_layer_type,job=%s,matrix=matrix,layer=%s,type=rout" % (
        jobname, layer))
    step.COM("matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=board" % (jobname, layer))
    if is_compensate:
        step.COM("compensate_layer,source_layer=%s,dest_layer=%s_compensate,dest_layer_type=rout" % (layer, layer))

    step.COM("units,type=mm")
    step.COM("ncrset_cur,job=%s,step=,layer=,ncset=" % jobname)
    step.COM("ncrset_cur,job=%s,step=%s,layer=,ncset=" % (jobname, stepname))

    if is_compensate:
        step.COM("ncrset_cur,job=%s,step=%s,layer=%s_compensate,ncset=%s" % (jobname, stepname, layer, os.getpid()))
    else:
        step.COM("ncrset_cur,job=%s,step=%s,layer=%s,ncset=%s" % (jobname, stepname, layer, os.getpid()))

    step.COM("ncr_set_machine,machine=%s,thickness=0" % machine)
    step.COM("ncrset_units,units=mm")
    step.COM("ncr_auto_all,create_rout=no")
    step.COM("ncr_register,angle=0,mirror=no,xoff=%s,yoff=%s,version=1,\
    xorigin=%s,yorigin=%s,xscale=%s,yscale=%s,\
    xscale_o=%s,yscale_o=%s" % (xoff, yoff, xorigin, yorigin, xscale, yscale, xcenter, ycenter))

    step.COM("ncr_cre_rout")
    step.COM("ncr_ncf_export,dir=%s,name=%s.%s" %
             (outputpath, jobname, layer))
    if is_report:
        step.COM("ncr_report,path=%s/%s.rc" % (outputpath, jobname))

    step.COM("ncrset_page_close")
    rout_path = "%s/%s.%s" % (outputpath, jobname, layer)
    return rout_path

def output_opfx(**kwargs):
    """输出LDI opfx格式"""
    step = kwargs["step_obj"]
    step.COM("image_set_elpd2,job={job},step={step},layer={layer},device_type=DP100,polarity={polarity},\
    speed=0,xstretch={xstretch},ystretch={ystretch},xshift=0,yshift=0,xmirror={xmirror},ymirror={ymirror},xcenter={xcenter},\
    ycenter={ycenter},minvec=0,advec=0,minflash=0,adflash=0,conductors1=0,conductors2=0,conductors3=0,conductors4=0,\
    conductors5=0,media=first,smoothing=smooth,swap_axes={swap_axes},define_ext_lpd=yes,resolution_value={resolution_value},\
    resolution_units=micron,quality=auto,enlarge_polarity=both,enlarge_other=leave_as_is,enlarge_panel=no,\
    enlarge_contours_by=0,overlap=no,enlarge_image_symbols=no,enlarge_0_vecs=no,enlarge_symbols=none,\
    enlarge_symbols_by=0,symbol_name1=,enlarge_by1=0,symbol_name2=,enlarge_by2=0,symbol_name3=,enlarge_by3=0,\
    symbol_name4=,enlarge_by4=0,symbol_name5=,enlarge_by5=0,symbol_name6=,enlarge_by6=0,symbol_name7=,\
    enlarge_by7=0,symbol_name8=,enlarge_by8=0,symbol_name9=,enlarge_by9=0,symbol_name10=,\
    enlarge_by10=0".format(**kwargs))
    
    step.COM("output_layer_reset")
    step.COM("output_layer_set,layer={layer},angle=0,mirror=no,x_scale=1,y_scale=1,comp=0,polarity=positive,setupfile=,\
    setupfiletmp=,line_units=mm,gscl_file=,step_scale=no".format(**kwargs))
    step.COM("output,job={job},step={step},format=DP100X,dir_path={dir_path},prefix=,\
    suffix=,break_sr=no,break_symbols=no,break_arc=no,scale_mode=nocontrol,surface_mode=contour,units=mm,\
    x_anchor={x_anchor},y_anchor={y_anchor},x_offset=0,y_offset=0,line_units=mm,override_online=yes,local_copy=yes,send_to_plotter=no,\
    dp100x_lamination=0,dp100x_clip=0,clip_size={clip_size},clip_orig={clip_orig},clip_width={clip_width},clip_height={clip_height},\
    clip_orig_x={clip_orig_x},clip_orig_y={clip_orig_y},plotter_group=any,units_factor=0.01,auto_purge=no,entry_num=5,plot_copies=999,\
    dp100x_iserial=1,imgmgr_name=LDI,deliver_date=".format(**kwargs))


class compareLayersForOutput(object):
    """资料输出回读比对"""

    def __init__(self, parent=None):
        super(compareLayersForOutput, self).__init__()

    def compare_gerber274x(self, *args):
        """比对gerber文件"""
        self.input_gerber_file(args[0], args[1], args[6], args[2])
        result = self.compare_layer(*args)
        return result
    
    def compare_opfx(self, *args):
        """比对gerber文件"""
        self.input_opfx_file(args[0], args[1], args[6], args[2])
        result = self.compare_layer(*args)
        return result    

    def compare_drill(self, *args):
        self.input_drill_file(args[0], args[1], args[6], args[2])
        result = self.compare_layer(*args)
        return result

    def compare_layer(self, *args):
        """开始比对文件"""
        (jobname,
        stepname,
        worklayer,
        mirror,
        scale_x,
        scale_y,
        gerberfilepath,
        widget,
        anthor_x,
        anthor_y) = args[:10]
        if len(args) > 10:
            compare_mode = args[10]
        
        #from checkRules import rule
        #checkrule = rule()        
        
        job = gClasses.Job(jobname)
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")        
        
        get_sr_area_flatten("fill_area")        

        Prof_xmin, Prof_ymin, Prof_xmax, Prof_ymax = \
            get_profile_limits(step)
        
        if "opfx" in args:
            if not step.isLayer(worklayer+"+1"):
                return 0, "", 100
            
            step.clearAll()
            step.affect(worklayer+"+1")
            step.copySel(worklayer + "_compare")
        
        step.clearAll()
        step.affect(worklayer + "_compare")
        step.resetFilter()
        step.selectAll()
        #资料回读异常
        if not step.featureSelected():
            return 0, "", 100

        arraylist_area = get_sr_area_for_step(stepname)
        flip = genesisFlip()
        flip.release_flip()
        
        if mirror in ["y_mirror", "x_mirror",]:            
            step.COM("sel_transform,mode=anchor,oper={0},duplicate=no,\
            x_anchor=0,y_anchor=0,angle=0,x_scale=1,\
            y_scale=1,x_offset={1},y_offset={2}".format(mirror, anthor_x, anthor_y))
        #else:
            #step.COM("sel_transform,mode=anchor,oper={0},duplicate=no,\
            #x_anchor=0,y_anchor=0,angle=0,x_scale=1,\
            #y_scale=1,x_offset={1},y_offset={2}".format("", anthor_x, anthor_y))
        
        # 镭射钻带
        if re.match("s\d+-\d+|s\d+-\d+-.*", worklayer):     
            step.selectNone()
            step.resetFilter()            
            dld_layer = worklayer.replace("s", "dld")
            if step.isLayer(dld_layer):                
                step.refSelectFilter(dld_layer)
            else:
                step.selectSymbol("r45", 1, 1)
            #if "192.168.19.243" in localip[2]:
                #step.PAUSE(str([step.featureSelected()]))                        
            if step.featureSelected() in [4, 8, 16, 32]:
                step.selectDelete()
                
            if re.match("s\d+-\d+-.*", worklayer):
                # 合并后的r501不一定重合 这里判断下 并删除掉
                step.clearAll()
                step.affect(worklayer)                
                step.selectSymbol("r501", 1, 1)
                if step.featureSelected() == 4:
                    step.selectDelete()
                
                step.clearAll()
                step.affect(worklayer+"_compare")
                step.selectSymbol("r501", 1, 1)
                if step.featureSelected() == 4:
                    step.selectDelete()

        weikong_step_area = []
        text_area = []
        hct_coupon_barcode_area = []
        gerber_scale_text_area = []
        if "drill" in args:            
            step.removeLayer(worklayer+"_flt")
            step.flatten_layer(worklayer, worklayer+"_flt")
            
            step.clearAll()
            step.affect(worklayer + '_flt')
            center_x = anthor_x
            center_y = anthor_y
            #if "192.168.19.243" in localip[2]:
                #step.PAUSE(str([scale_x, scale_y, center_x, center_y]))               
            step.COM("sel_transform,mode=anchor,oper=scale,duplicate=no,\
            x_anchor=%s,y_anchor=%s,angle=0,x_scale=%.6f,y_scale=%.6f,x_offset=0,\
            y_offset=0" % (center_x, center_y, scale_x, scale_y))
            if "inn" in worklayer:
                step.changeSymbol("r3175")
            
            step.clearAll()
            step.affect(worklayer + '_compare')
            if "inn" in worklayer:
                step.changeSymbol("r3175")                
            
            #step.COM("register_layers,reference_layer={0},tolerance=38.1,"
                     #"mirror_allowed=yes,rotation_allowed=yes,zero_lines=no,"
                     #"reg_mode=affected_layers,register_layer=".format(worklayer+"_flt"))
            
            #auto_move = False
            #step.resetFilter()
            #step.selectAll()
            #count = step.featureSelected()
            #step.selectNone()
            #if sys.platform == "win32":                
                #step.refSelectFilter(worklayer+"_flt", mode='include')
            #else:
                #step.COM("sel_ref_feat,layers={0},use=filter,mode=same_center,"
                         #"f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,"
                         #"include_syms=,exclude_syms=,on_multiple=smallest".format(worklayer+"_flt"))               
            #if step.featureSelected() < count * 0.5:
                #auto_move = True
            
            #if auto_move:
            layer_cmd1 = gClasses.Layer(step, worklayer + '_compare')
            layer_cmd2 = gClasses.Layer(step, worklayer + '_flt')
            
            feat_out1 =[obj for obj in layer_cmd1.featCurrent_LayerOut(units="mm")["pads"]]
            feat_out2 =[obj for obj in layer_cmd2.featCurrent_LayerOut(units="mm")["pads"]]
            
            compare_xmin = min([obj.x for obj in feat_out1])
            flatten_xmin = min([obj.x for obj in feat_out2])
            compare_ymax = max([obj.y for obj in feat_out1])
            flatten_ymax = max([obj.y for obj in feat_out2])
            
            offset_x = flatten_xmin - compare_xmin
            offset_y = flatten_ymax - compare_ymax
            step.clearAll()
            step.affect(worklayer + "_compare")
            step.resetFilter()
            #if "192.168.19.243" in localip[2]:
                #step.PAUSE(str([offset_x, offset_y]))                   
            step.COM("sel_transform,mode=anchor,oper=scale,duplicate=no,\
                x_anchor=%s,y_anchor=%s,angle=0,x_scale=%s,y_scale=%s,x_offset=%s,\
                y_offset=%s" % (0, 0, 1, 1, offset_x, offset_y))
            #if "192.168.19.243" in localip[2]:
                #step.PAUSE(str([offset_x, offset_y, 2]))                               
            
            #因加了text 回读会有差异 故将比对层跟工作层text删除后再比对            
            step.clearAll()
            step.affect(worklayer + '_flt')
            step.resetFilter()
            step.filter_set(feat_types='text')
            step.selectAll()
            if step.featureSelected():
                layer_cmd = gClasses.Layer(step, worklayer)
                indexes = layer_cmd.featSelIndex()
                for index in indexes:
                    step.selectNone()
                    step.selectFeatureIndex(worklayer, index)
                    xmin, ymin, xmax, ymax = get_layer_selected_limits(step, worklayer)
                    text_area.append([xmin - 0.3, ymin - 0.3, xmax + 0.3, ymax + 0.3])

            # 如果板内有*号则变更为88888字样
            if worklayer in tongkongDrillLayer + mai_drill_layers + mai_man_drill_layers:
                change_8888 = '8' * 15
            else:
                change_8888 = '8' * 8
            lay_cmd = gClasses.Layer(step, worklayer + '_compare')
            info_texts = lay_cmd.featout_dic_Index(options='feat_index')['text']
            for obj in info_texts:
                if '*' == obj.text:
                    step.clearAll()
                    step.affect(worklayer + '_compare')
                    step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(worklayer + '_compare',obj.feat_index))
                    if step.featureSelected():
                        step.COM("sel_change_txt,text={0}".format(change_8888))

            step.clearAll()
            step.affect(worklayer + '_compare')            
            step.resetFilter()
            step.filter_set(feat_types='text')
            delete_text = True            
            if step.isLayer("fill_area"):
                step.selectNone()
                step.refSelectFilter("fill_area")
                #方松通知 铝片可以不检测是否钻到其他模块 20240204 by lyh 徐志刚要求 还是要避开模块等有物件的区域
                # if step.featureSelected() and ".lp" not in worklayer:
                if step.featureSelected():
                    # 检测到字唛孔会进板内 不删除 直接报警比对异常
                    delete_text = False

            step.affect(worklayer + '_flt')
            if delete_text:                
                step.selectAll()
                if step.featureSelected():                                 
                    step.selectDelete()
            
            step.clearAll()
            
            if worklayer in matrixInfo["gCOLstep_name"]:
                weikong_step_area = get_sr_area_for_step_include(step.name, include_sr_step=[worklayer])
                
            if "tk.ykj" in worklayer:
                weikong_step_area = get_sr_area_for_step_include(step.name, include_sr_step=["drl"])

        if "gerber274x" in args:            
            if scale_x != 1 or scale_y != 1:
                
                drill_info_path = "d:/drill_info/drill_info.json"
                if sys.platform != "win32":
                    drill_info_path = "/tmp/drill_info.json"                
                
                #gerber加系数的位置计算出来 
                drill_coordinate_info = {}
                if os.path.exists(drill_info_path):
                    with open(drill_info_path) as file_obj:
                        drill_coordinate_info = json.load(file_obj)
                        
                if drill_coordinate_info.get(job.name):                    
                    if drill_coordinate_info[job.name].has_key(worklayer):
                        for symbol, x, y in drill_coordinate_info[job.name][worklayer]:
                            if symbol == "rect3000x43000":
                                gerber_scale_text_area.append([x - 2 - 5, y - 23 - 5, x + 2 + 5, y + 23 + 5])
                        
                step.clearAll()
                step.affect(worklayer)
                step.copyLayer(job.name, step.name, worklayer, worklayer+"_tmp_bak")
                # step.contourize(accuracy=0)
                step.removeLayer(worklayer+"_flt")
                step.flatten_layer(worklayer, worklayer+"_flt")
                step.clearAll()
                step.resetFilter()
                step.affect(worklayer+"_flt")
                #此物件输出会变没了 这里要删除掉
                step.filter_set(feat_types='pad', include_syms='barcode*')
                step.selectAll()
                if step.featureSelected():
                    step.selectDelete()
                    
                if step.isLayer(worklayer+"_compare_contourize"):
                    step.clearAll()
                    step.affect(worklayer+"_flt")
                    step.contourize(accuracy=0)
                
                step.copyLayer(job.name, step.name,  worklayer+"_tmp_bak", worklayer)
                
                step.clearAll()
                step.affect(worklayer + '_compare')
                step.resetFilter()
                step.COM("sel_transform,mode=anchor,oper=scale,duplicate=no,\
                x_anchor=%s,y_anchor=%s,angle=0,x_scale=%.6f,y_scale=%.6f,x_offset=0,\
                y_offset=0" % (anthor_x, anthor_y, 1/scale_x, 1/ scale_y))
                
                if step.STATUS > 0:
                    """解决异常不能拉伸的问题"""
                    step.resetFilter()
                    step.COM("filter_set,filter_name=popup,update_popup=no,feat_types=surface,polarity=negative")
                    step.selectAll()
                    step.COM("sel_resize,size=-5.08")
                    step.selectAll()
                    step.COM("sel_resize,size=5.08")
                    step.COM("sel_transform,mode=anchor,oper=scale,duplicate=no,\
                    x_anchor=%s,y_anchor=%s,angle=0,x_scale=%.6f,y_scale=%.6f,x_offset=0,\
                    y_offset=0" % (anthor_x, anthor_y,1/scale_x, 1/scale_y))                
                
                #step.COM("register_layers,reference_layer={0},tolerance=38.1,"
                         #"mirror_allowed=yes,rotation_allowed=yes,zero_lines=no,"
                         #"reg_mode=affected_layers,register_layer=".format(worklayer+"_flt"))
                #if "192.168.19.243" in localip[2]:
                    #step.PAUSE("CHECK")
                step.selectNone()
                step.selectSymbol("r9.9", 1, 1)
                r9_9_symbol = False
                if step.featureSelected():                    
                    layer_cmd_comp = gClasses.Layer(step, worklayer+"_compare")
                    feat_out_comp = layer_cmd_comp.featSelOut(units="mm")["pads"]
                    all_x = [obj.x for obj in feat_out_comp]
                    all_y = [obj.y for obj in feat_out_comp]
                    compare_xmin = min(all_x)
                    compare_ymin = min(all_y)
                    compare_xmax = max(all_x)
                    compare_ymax = max(all_y)                    
                    r9_9_symbol = True
                    step.selectDelete()
                else:
                    step.selectAll()
                    compare_xmin, compare_ymin, compare_xmax, compare_ymax = get_layer_selected_limits(step, worklayer + '_compare')
                    
                step.clearAll()
                step.affect(worklayer+"_flt")
                step.resetFilter()
                if r9_9_symbol:
                    step.selectSymbol("sh-dwsd2014*", 1, 1)
                    layer_cmd_flt = gClasses.Layer(step, worklayer+"_flt")
                    feat_out_flt = layer_cmd_flt.featSelOut(units="mm")["pads"]
                    all_x = [obj.x for obj in feat_out_flt]
                    all_y = [obj.y for obj in feat_out_flt]
                    flatten_xmin = min(all_x)
                    flatten_ymin = min(all_y)
                    flatten_xmax = max(all_x)
                    flatten_ymax = max(all_y)
                else:
                    step.selectAll()
                    flatten_xmin, flatten_ymin, flatten_xmax, flatten_ymax = get_layer_selected_limits(step, worklayer+"_flt")
                
                if abs(compare_xmin - flatten_xmin) > 0 or abs(compare_ymin - flatten_ymin) > 0:
                    offset_x = flatten_xmin - compare_xmin
                    offset_y = flatten_ymin - compare_ymin
                    step.clearAll()
                    step.affect(worklayer + "_compare")
                    step.resetFilter()
                    #if "10.3.7.10" in localip[2]:
                        #step.PAUSE(str([offset_x, offset_y, compare_xmin, flatten_xmin, compare_ymin, flatten_ymin, 1, r9_9_symbol]))                   
                    step.COM("sel_transform,mode=anchor,oper=scale,duplicate=no,\
                        x_anchor=%s,y_anchor=%s,angle=0,x_scale=%s,y_scale=%s,x_offset=%s,\
                        y_offset=%s" % (0, 0, 1, 1, offset_x, offset_y))
                    #if "10.3.7.10" in localip[2]:
                        #step.PAUSE(str([offset_x, offset_y, compare_xmin, flatten_xmin, compare_ymin, flatten_ymin, 2, r9_9_symbol]))  
            else:
                if sys.platform != "win32":                    
                    step.clearAll()
                    step.affect(worklayer)
                    step.removeLayer(worklayer+"_flt")
                    step.flatten_layer(worklayer, worklayer+"_flt")
                    if step.isLayer(worklayer+"_compare_contourize"):
                        # step.removeLayer(worklayer)
                        step.COM("matrix_rename_layer,job={0},matrix=matrix,layer={1},new_name={1}_bak++++".format(job.name, worklayer))
                        
                        step.copyLayer(job.name, step.name, worklayer+"_flt", worklayer)
                        
                        step.clearAll()
                        step.affect(worklayer)
                        step.contourize(accuracy=0)
                    
        if "opfx" in args:
            for name in matrixInfo["gCOLstep_name"]:
                if "hct_coupon" in name:
                    hct_coupon_barcode_area += get_sr_area_for_step_include(step.name, include_sr_step=[name])
            
        tol = 25.4
        map_res = 254
        if "gerber274x" in args:
            map_res = 5080
            
        compare_status = 0
        if sys.platform == "win32":
            diff_layer = worklayer+ "_diff"
            step.removeLayer(diff_layer)
            step.COM("compare_layers,layer1=%s,job2=%s,step2=%s,\
                layer2=%s,layer2_ext=,tol=%s,area=global,consider_sr=yes,\
                ignore_attr=,map_layer=%s_diff,map_layer_res=%s" % (
                worklayer+"_flt" if "drill" in args else worklayer, jobname, stepname, worklayer + "_compare", tol, worklayer, map_res))
            compare_status = step.STATUS
        else:            
            if compare_mode == "step_compare":
                diff_layer = "diff_" + worklayer
                step.removeLayer(diff_layer)
                step.COM("stpcmp_page_open,job2=%s,step2=%s" % (job.name, step.name))
                step.COM("stpcmp_add_layers_pair,layer1=%s,layer2=%s" % (worklayer+"_flt" if "drill" in args else worklayer, worklayer + "_compare"))
                step.COM("rv_tab_empty,report=step_compare,is_empty=yes")
                step.COM("stpcmp_compare,area=profile,tol=%s,map_res=508,ignore_attr=,map_layer_prefix=diff_,consider_sr=yes" % tol)
                step.COM("rv_tab_view_results_enabled,report=step_compare,is_enabled=no,serial_num=-1,all_count=-1")
                compare_status = step.STATUS
            else:
                diff_layer = worklayer+ "_diff"
                step.removeLayer(diff_layer)
                step.COM("compare_layers,layer1=%s,job2=%s,step2=%s,\
                    layer2=%s,layer2_ext=,tol=%s,area=global,consider_sr=yes,\
                    ignore_attr=,map_layer=%s_diff,map_layer_res=%s" % (
                    worklayer+"_flt" if "drill" in args else worklayer, jobname, stepname, worklayer + "_compare", tol, worklayer, map_res))
                compare_status = step.STATUS
                #diff_layer = "diff_" + worklayer
                #step.removeLayer(diff_layer)
                #step.COM("rv_tab_empty,report=graphic_compare,is_empty=yes")
                #step.COM("graphic_compare_res,layer1=%s,job2=%s,step2=%s,layer2=%s,layer2_ext=,"
                         #"tol=%s,resolution=508,area=global,ignore_attr=.ignore_action,"
                         #"map_layer_prefix=diff_,consider_sr=yes" % (worklayer, jobname, stepname, worklayer + "_compare", tol))
                #step.COM("rv_tab_view_results_enabled,report=graphic_compare,is_enabled=yes,serial_num=-1,all_count=-1")            
            
        #if "10.3.7.10" in localip[2]:
            #step.PAUSE("check")
            
        step.clearAll()
        get_sr_area("fill_tmp", stepname=stepname)
        
        step.clearAll()
        if step.isLayer(diff_layer):            
            step.affect(diff_layer)
        else:
            step.createLayer(diff_layer)
            step.affect(diff_layer)
            
        step.resetFilter()
        step.COM(
            "filter_set,filter_name=popup,update_popup=no,feat_types=pad,polarity=positive")
        step.selectSymbol("r0")
        if step.featureSelected():
            step.removeLayer("r0_tmp")
            step.copySel("r0_tmp")
            step.clearAll()
            step.affect("r0_tmp")
            if weikong_step_area:
                # 去掉尾孔比对不一致的情况 因尾孔step位置会动 所以这个区域暂时去掉
                for sr_xmin, sr_ymin, sr_xmax, sr_ymax in weikong_step_area:
                    step.selectRectangle(sr_xmin-0.3, sr_ymin-0.3, sr_xmax+0.3, sr_ymax+0.3)
                    if step.featureSelected():
                        step.selectDelete()                      
                        
            if "lp" in worklayer:
                # 铝片内因字唛被打散 这个把字唛去掉删除掉
                if text_area:
                    for sr_xmin, sr_ymin, sr_xmax, sr_ymax in text_area:
                        step.selectRectangle(sr_xmin, sr_ymin, sr_xmax, sr_ymax)
                        if step.featureSelected():
                            step.selectDelete()
                            
            if "opfx" in args:
                if hct_coupon_barcode_area:
                    # 此hct模块 回读二位码位置会加四个角标 暂时不清楚原因 先忽略此异常位置
                    for sr_xmin, sr_ymin, sr_xmax, sr_ymax in hct_coupon_barcode_area:
                        step.selectRectangle(sr_xmin, sr_ymin, sr_xmax, sr_ymax)
                        if step.featureSelected():
                            step.selectDelete()
            
            if "gerber274x" in args:
                if gerber_scale_text_area:
                    for sr_xmin, sr_ymin, sr_xmax, sr_ymax in gerber_scale_text_area:
                        step.selectRectangle(sr_xmin, sr_ymin, sr_xmax, sr_ymax)
                        if step.featureSelected():
                            step.selectDelete()  
            
            #if "192.168.19.243" in localip[2]:
                #step.PAUSE(str(args))
                
            if not step.isLayer("fill_tmp"):
                for sr_xmin, sr_ymin, sr_xmax, sr_ymax in arraylist_area:
                    step.selectRectangle(sr_xmin, sr_ymin, sr_xmax, sr_ymax)
            else:
                step.refSelectFilter("fill_tmp")
    
            step.removeLayer("fill_tmp")

            diff = step.featureSelected()
            diff_in_pcs = ""
            if not diff:
                step.selectRectangle(Prof_xmin, Prof_ymin, Prof_xmax, Prof_ymax)
                diff = step.featureSelected()
                if diff:                
                    diff_in_pcs = "out_pcs"
            else:
                step.selectRectangle(Prof_xmin, Prof_ymin, Prof_xmax, Prof_ymax)
                diff_in_pcs = "in_pcs"
        else:
            diff = 0
            diff_in_pcs = ""
            
        if diff:
            #STR = r'-t layer -e %s/%s/%s -d FEATURES -o select,units= mm' % (
                #jobname, stepname, "r0_tmp")
            #info = step.INFO(STR)
            #infolist = self.parseInfoList(step, info)# checkrule.parseInfoList(step, info)

            step.clearAll()
            # step.display(worklayer + "_diff")
            step.display(diff_layer)
            # step.COM("note_delete_all,layer=%s,note_from=0,note_to=2147483647,user="%(worklayer + "_diff"))
            #checkrule.addNote(step, worklayer + "_diff",
                              #infolist, "find not same position!")
            # self.addNote(step, worklayer + "_diff", infolist,  "find not same position!")
            # step.display_layer(worklayer + "_flatten", 3)
            step.display_layer(worklayer , 3)
            step.display_layer(worklayer + "_compare", 4)
        else:
            step.removeLayer("r0_tmp")
            step.removeLayer(worklayer + "_diff")
            step.removeLayer(worklayer + "_compare")
            step.removeLayer(worklayer + "_compare+1")
            step.removeLayer(worklayer + "_compare+++")
            step.removeLayer(worklayer + "_flatten")
            step.removeLayer(worklayer + "_flt")
            step.removeLayer(worklayer + "_compare_opt")

        return diff, diff_in_pcs, compare_status
    
    def addNote(self,step,layer,infoList,noteText,showNote="yes",user="",showSymbol = "yes"): 
        #step.COM("note_delete_all,layer=%s,note_from=0,note_to=2147483647,user="%layer)
        step.COM("get_origin")
        orignx, origny = step.COMANS.split()
        orignx = float(orignx)
        origny = float(origny)

        # step.PAUSE(str([orignx,origny]))
        for x,y,symbol in infoList:
            if showSymbol == "yes":
                # step.PAUSE(str([x, y, x - orignx,y - origny]))
                if "spacing:" in noteText:
                    step.COM("note_add,layer=%s,x=%s,y=%s,user=%s,text=%s %s" %
                             (layer, x - orignx, y - origny, user, noteText, symbol))
                else:
                    step.COM("note_add,layer=%s,x=%s,y=%s,user=%s,text=%s symbol:%s"%(layer,x - orignx,y - origny,user,noteText,symbol))
            else:
                step.COM("note_add,layer=%s,x=%s,y=%s,user=%s,text=%s "%(layer,x - orignx,y - origny,user,noteText))

        if showNote == "yes":            
            step.COM("zoom_home")
            step.COM("note_page_close")
            step.clearAll()
            step.display(layer,work=1)
            if sys.platform == "win32":
                step.COM("note_page_show,layer=%s"%layer)
            else:
                step.COM("set_note_layer,layer=%s"%layer)
                step.COM("show_component,component=Notes,show=yes,width=0,height=0")

    def parseInfoList(self,step,infoList, calc_legth=None):
        dic_Obj = step.parseFeatureInfo(infoList)
        allsymbol_xy = []
        exists_coordinate = []
        for key in dic_Obj:
            for Obj in dic_Obj[key]:
                if Obj.shape in ["Pad","Text", "Barcode"]:# and Obj.polarity == "positive":
                    if (Obj.x,Obj.y) in exists_coordinate:
                        continue

                    if Obj.shape == "Pad":
                        allsymbol_xy.append((Obj.x,Obj.y,Obj.symbol))
                        exists_coordinate.append((Obj.x,Obj.y))
                    else:
                        allsymbol_xy.append((Obj.x,Obj.y,Obj.text))
                        exists_coordinate.append((Obj.x,Obj.y))

                if Obj.shape in ["Arc"]:  # and Obj.polarity == "positive":
                    if (Obj.xs,Obj.ys) in exists_coordinate:
                        continue

                    allsymbol_xy.append((Obj.xs, Obj.ys, Obj.symbol))
                    exists_coordinate.append((Obj.xs,Obj.ys))

                if Obj.shape in ["Line"]:
                    if ((Obj.xs + Obj.xe) / 2.0, (Obj.ys + Obj.ye) / 2.0) in exists_coordinate:
                        continue
                    if calc_legth is None:			
                        allsymbol_xy.append(((Obj.xs + Obj.xe) / 2.0, (Obj.ys + Obj.ye) / 2.0, Obj.symbol))
                    else:
                        if calc_legth == "inch":
                            flag = 39.37
                            units = "mil"
                        else:
                            flag = 1
                            units = "mm"
                        allsymbol_xy.append(((Obj.xs + Obj.xe) / 2.0, (Obj.ys + Obj.ye) / 2.0,
                                             Obj.symbol+" value:{0} {1}".format(round(Obj.len*flag, 1), units)))

                    exists_coordinate.append(((Obj.xs + Obj.xe) / 2.0, (Obj.ys + Obj.ye) / 2.0))

                if Obj.shape in ["Surface"]:
                    if (Obj.x,Obj.y) in exists_coordinate:
                        continue		    
                    allsymbol_xy.append((Obj.x,Obj.y,"surface"))		    
                    exists_coordinate.append((Obj.x,Obj.y))

        return allsymbol_xy


    def input_gerber_file(self, jobname, stepname, filepath, worklayer):
        """导入资料"""
        top.COM('input_manual_reset')
        top.COM('input_manual_set,path=%s,job=%s,step=%s,\
        format=Gerber274x,data_type=ascii,units=inch,coordinates=absolute, \
        zeroes=none,nf1=2,nf2=6,decimal=no,separator=*,tool_units=inch, \
        layer=%s,wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.1, \
        signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200, \
        resolution=3' % (filepath, jobname, stepname, worklayer + "_compare"))
        top.COM('input_manual,script_path=')
        
    def input_opfx_file(self, jobname, stepname, filepath, worklayer):
        """导入资料"""
        top.COM('input_manual_reset')
        top.COM('input_manual_set,path=%s,job=%s,step=%s,\
        format=OPFX,data_type=ascii,units=inch,coordinates=absolute, \
        zeroes=none,nf1=2,nf2=6,decimal=no,separator=*,tool_units=inch, \
        layer=,wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.1, \
        signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200, \
        resolution=3' % (filepath, jobname, stepname))
        top.COM('input_manual,script_path=')

    def input_drill_file(self, jobname, stepname, filepath, worklayer):
        step = gClasses.Step(job, stepname)
        step.open()
        step.clearAll()
        step.resetFilter()
        step.COM("units,type=mm")
        if step.isLayer(worklayer + "_compare"):
            step.removeLayer(worklayer + "_compare")
        step.createLayer(worklayer + "_compare")
        step.affect(worklayer + "_compare")
        step.COM("sel_transform,mode=anchor,oper=,duplicate=no,\
        x_anchor=0,y_anchor=0,angle=0,x_scale=1,y_scale=1,x_offset=0,y_offset=0")
        step.COM('input_manual_reset')
        if os.environ.get("NUMBER_FORMAT") == "43":
            step.COM('input_manual_set,path=%s,job=%s,step=%s,\
            format=Excellon2,data_type=ascii,units=mm,coordinates=absolute,\
            zeroes=trailing,nf1=4,nf2=3,decimal=no,separator=nl,tool_units=mm,\
            layer=%s,wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,\
            signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,\
            resolution=3' % (filepath, jobname, stepname, worklayer + "_compare"))
        else:
            step.COM('input_manual_set,path=%s,job=%s,step=%s,\
            format=Excellon2,data_type=ascii,units=mm,coordinates=absolute,\
            zeroes=trailing,nf1=3,nf2=3,decimal=no,separator=nl,tool_units=mm,\
            layer=%s,wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,\
            signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,\
            resolution=3' % (filepath, jobname, stepname, worklayer + "_compare"))
        step.COM('input_manual,script_path=')


class defineCheckCondition(object):

    def __init__(self, parent=None):
        super(defineCheckCondition, self).__init__()

    def check_panel_sr_spacing(self, stepname, max_or_min="min"):
        """检测panel 拼版间距 发现间距为0的报警出来 20190411 江门一厂
        加入大连检测最大拼版间距 20191101 定义 max_or_min == max"""

        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")

        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)

        sr_xmin, sr_ymin, sr_xmax, sr_ymax = get_sr_limits(step)

        STR = '-t step -e %s/%s -d REPEAT,units=mm' % (jobname, stepname)
        gREPEAT_info = step.DO_INFO(STR)
        gREPEATstep = gREPEAT_info['gREPEATstep']
        gREPEATxmax = gREPEAT_info['gREPEATxmax']
        gREPEATymax = gREPEAT_info['gREPEATymax']
        gREPEATxmin = gREPEAT_info['gREPEATxmin']
        gREPEATymin = gREPEAT_info['gREPEATymin']
        gREPEATxmax_set = []
        gREPEATymax_set = []
        gREPEATxmin_set = []
        gREPEATymin_set = []
        gREPEATxmax_ic = []
        gREPEATymax_ic = []
        gREPEATxmin_ic = []
        gREPEATymin_ic = []

        step.removeLayer("check_sr_spacing")
        step.createLayer("check_sr_spacing")
        step.removeLayer("check_sr_spacing_zk")
        step.createLayer("check_sr_spacing_zk")
        step.clearAll()
        step.affect("check_sr_spacing")
        step.reset_fill_params()
        for i in xrange(len(gREPEATstep)):
            if "zk" in str(gREPEATstep[i]) or \
                    "imp" in str(gREPEATstep[i]):
                continue
            xs = gREPEATxmin[i]
            ys = gREPEATymin[i]
            xe = gREPEATxmax[i]
            ye = gREPEATymax[i]
            step.addRectangle(xs, ys, xe, ye)

        step.resetFilter()
        step.selectAll()
        sr_count = step.featureSelected()

        step.COM("sel_resize,size=10")
        step.contourize()
        step.selectAll()
        con_sr_count = step.featureSelected()
        if sr_count != con_sr_count:
            return u"检测到%s拼版间距有为零 或者重叠相交的情况，请检查~" % stepname

        step.clearAll()
        step.affect("check_sr_spacing_zk")
        step.reset_fill_params()
        for i in xrange(len(gREPEATstep)):
            if "zk" in str(gREPEATstep[i]) or \
                    "imp" in str(gREPEATstep[i]):
                xs = gREPEATxmin[i]
                ys = gREPEATymin[i]
                xe = gREPEATxmax[i]
                ye = gREPEATymax[i]
                step.addRectangle(xs, ys, xe, ye)

        step.COM("sel_resize,size=10")
        step.contourize()
        step.copySel("check_sr_spacing")

        step.clearAll()
        step.affect("check_sr_spacing")
        step.resetFilter()
        step.selectAll()
        sr_count = step.featureSelected()

        step.COM("sel_resize,size=10")
        step.contourize()
        step.selectAll()
        con_sr_count = step.featureSelected()
        step.removeLayer("check_sr_spacing")
        step.removeLayer("check_sr_spacing_zk")
        step.clearAll()
        step.close()
        # step.PAUSE(str([sr_count, con_sr_count]))
        if sr_count != con_sr_count:
            return u"检测到%s拼版间距有为零 或者重叠相交的情况，请检查~" % stepname

        for i in xrange(len(gREPEATstep)):
            if re.match(r'^set|^edit', str(gREPEATstep[i])):
                gREPEATxmax_set.append(gREPEATxmax[i])
                gREPEATymax_set.append(gREPEATymax[i])
                gREPEATxmin_set.append(gREPEATxmin[i])
                gREPEATymin_set.append(gREPEATymin[i])
                set_step = str(gREPEATstep[i])

            elif re.match(r'^zk.*', str(gREPEATstep[i])):
                if SITE_ID in [u"江门一厂"]:
                    continue

            else:
                gREPEATxmax_ic.append(gREPEATxmax[i])
                gREPEATymax_ic.append(gREPEATymax[i])
                gREPEATxmin_ic.append(gREPEATxmin[i])
                gREPEATymin_ic.append(gREPEATymin[i])

        ######################获取拼板间距
        gREPEATymin_set_different = [gREPEATymin_set[x] for x in xrange(len(gREPEATymin_set)) if
                                     gREPEATymin_set[x] not in gREPEATymin_set[(x + 1):]]
        gREPEATymin_set_different.sort()
        gREPEATxmin_set_different = [gREPEATxmin_set[x] for x in xrange(len(gREPEATxmin_set)) if
                                     gREPEATxmin_set[x] not in gREPEATxmin_set[(x + 1):]]
        gREPEATxmin_set_different.sort()
        setToset_x = []
        setToset_y = []

        for i in range(len(gREPEATymin_set_different)):  ####x方向拼板间距
            dic_set_xmin = []
            dic_set_xmax = []
            first = 0
            for j in range(len(gREPEATxmin_set)):
                if gREPEATymin_set[j] == gREPEATymin_set_different[i]:
                    dic_set_xmin.append(gREPEATxmin_set[j])
                    dic_set_xmax.append(gREPEATxmax_set[j])
                    if not first:
                        first_set_ymin = gREPEATymin_set[j]
                        first_set_ymax = gREPEATymax_set[j]
                        first += 1
                    for n in range(len(gREPEATxmin_ic)):
                        if abs(gREPEATxmin_ic[n] - gREPEATxmax_ic[n]) > 20:    continue
                        if (gREPEATymin_set[j] <= gREPEATymin_ic[n] <= gREPEATymax_set[j] and \
                            gREPEATxmax_set[j] <= gREPEATxmin_ic[n]) or \
                                (gREPEATymin_set[j] <= gREPEATymax_ic[n] <= gREPEATymax_set[j] and \
                                 gREPEATxmax_set[j] <= gREPEATxmin_ic[n]) or \
                                (gREPEATymax_set[j] <= gREPEATymax_ic[n] and \
                                 gREPEATymin_ic[n] <= gREPEATymin_set[j] and \
                                 gREPEATxmax_set[j] <= gREPEATxmin_ic[n]):
                            dic_set_xmin.append(gREPEATxmin_ic[n])
                            dic_set_xmax.append(gREPEATxmax_ic[n])
                if first:
                    if (first_set_ymin < gREPEATymin_set[j] < first_set_ymax) or \
                            (first_set_ymin < gREPEATymax_set[j] < first_set_ymax) or \
                            (first_set_ymin > gREPEATymin_set[j] and \
                             first_set_ymax < gREPEATymax_set[j]):
                        dic_set_xmin.append(gREPEATxmin_set[j])
                        dic_set_xmax.append(gREPEATxmax_set[j])

            if len(dic_set_xmin) <= 1: continue
            dic_set_xmin = [dic_set_xmin[x] for x in xrange(len(dic_set_xmin)) if
                            dic_set_xmin[x] not in dic_set_xmin[(x + 1):]]
            dic_set_xmax = [dic_set_xmax[x] for x in xrange(len(dic_set_xmax)) if
                            dic_set_xmax[x] not in dic_set_xmax[(x + 1):]]
            dic_set_xmin.sort()
            dic_set_xmax.sort()
            for i in range(len(dic_set_xmin)):
                if i == 0: continue
                setToset_x.append(abs(dic_set_xmax[i - 1] - dic_set_xmin[i]))

        for i in range(len(gREPEATxmin_set_different)):  ########y方向拼板间距
            dic_set_ymin = []
            dic_set_ymax = []
            first = 0
            for j in range(len(gREPEATymin_set)):
                if gREPEATxmin_set[j] == gREPEATxmin_set_different[i]:
                    dic_set_ymin.append(gREPEATymin_set[j])
                    dic_set_ymax.append(gREPEATymax_set[j])
                    if not first:
                        first_set_xmin = gREPEATxmin_set[j]
                        first_set_xmax = gREPEATxmax_set[j]
                        first += 1
                    for n in range(len(gREPEATxmin_ic)):
                        if abs(gREPEATymin_ic[n] - gREPEATymax_ic[n]) > 20:    continue
                        if (gREPEATxmin_set[j] <= gREPEATxmin_ic[n] <= gREPEATxmax_set[j] and \
                            gREPEATymax_set[j] <= gREPEATymin_ic[n]) or \
                                (gREPEATxmin_set[j] <= gREPEATxmax_ic[n] <= gREPEATxmax_set[j] and \
                                 gREPEATymax_set[j] <= gREPEATymin_ic[n]) or \
                                (gREPEATxmax_set[j] <= gREPEATxmax_ic[n] and \
                                 gREPEATxmin_ic[n] <= gREPEATxmin_set[j] and \
                                 gREPEATymax_set[j] <= gREPEATymin_ic[n]):
                            dic_set_ymin.append(gREPEATymin_ic[n])
                            dic_set_ymax.append(gREPEATymax_ic[n])

                if first:
                    if (first_set_xmin < gREPEATxmin_set[j] < first_set_xmax) or \
                            (first_set_xmin < gREPEATxmax_set[j] < first_set_xmax) or \
                            (first_set_xmin > gREPEATxmin_set[j] and \
                             first_set_xmax < gREPEATxmax_set[j]):
                        dic_set_ymin.append(gREPEATymin_set[j])
                        dic_set_ymax.append(gREPEATymax_set[j])

            if len(dic_set_ymin) <= 1: continue
            dic_set_ymin = [dic_set_ymin[x] for x in xrange(len(dic_set_ymin)) if
                            dic_set_ymin[x] not in dic_set_ymin[(x + 1):]]
            dic_set_ymax = [dic_set_ymax[x] for x in xrange(len(dic_set_ymax)) if
                            dic_set_ymax[x] not in dic_set_ymax[(x + 1):]]
            dic_set_ymin.sort()
            dic_set_ymax.sort()

            for i in range(len(dic_set_ymin)):
                if i == 0: continue
                setToset_y.append(abs(dic_set_ymax[i - 1] - dic_set_ymin[i]))

        if max_or_min == "max":
            if setToset_x and setToset_y:
                return max([max(setToset_x), max(setToset_y)])
            else:
                if setToset_x:
                    return max(setToset_x)

                if setToset_y:
                    return max(setToset_y)
        else:
            if setToset_x and setToset_y:
                return min([min(setToset_x), min(setToset_y)])
            else:
                if setToset_x:
                    return min(setToset_x)

                if setToset_y:
                    return min(setToset_y)

        return 1
    
class RECTANGLE(object):
    """
    每一个独立的symbol抽象成一个矩形，为了简单起见，圆pad也当成矩形
    """

    def __init__(self, symbol=None, xmin=0.0, ymin=0.0, xmax=0.0, ymax=0.0):
        # --为防止起始坐标和结束坐标互换，再次取值
        self.xmin = min(xmin, xmax)
        self.ymin = min(ymin, ymax)
        self.xmax = max(xmax, xmin)
        self.ymax = max(ymax, ymin)
        self.xc = self.xmin + (self.xmax - self.xmin) / 2
        self.yc = self.ymin + (self.ymax - self.ymin) / 2
        self.area = self.get_lenX() * self.get_lenY()
        self.symbol = symbol

    def __repr__(self):
        """
        字符串表示形式
        :return:
        :rtype:
        """
        return 'RECTANGLE(symbol="%s",xmin=%s,ymin=%s,xmax=%s,ymax=%s)' \
               % (self.symbol, self.xmin, self.ymin, self.xmax, self.ymax)

    def __eq__(self, other):
        """
        判断self和other是否相等，other==self,并不代表self==other,小的等于大的，但大的不等于小的，从而可以去掉小area
        :param other:
        :type other:
        :return:
        :rtype:
        """
        if self.xmin == other.xmin and self.xmax == other.xmax and self.ymin == other.ymin and self.ymax == other.ymax:
            return True
        elif math.fabs(self.xc - other.xc) < 0.1 and math.fabs(self.yc - other.yc) < 0.1 and self.area < other.area:
            # --同一位置添加的symbol,取area最大的避开
            return True
        elif other.xmin > self.xmin and other.xmax < self.xmax and other.ymin > self.ymin and other.ymax < self.ymax:
            # --self==other的情况
            return True
        elif self.xmin > other.xmin and self.xmax < other.xmax and self.ymin > other.ymin and self.ymax < other.ymax:
            # --other==self的情况
            return True
        else:
            return False

    def get_lenX(self):
        """
        攻取x方向的长度
        :return: 长度
        :rtype: float
        """
        return self.xmax - self.xmin

    def get_lenY(self):
        """
        攻取y方向的长度
        :return: 长度
        :rtype: float
        """
        return self.ymax - self.ymin

    def touch(self, other):
        """
        判断两个矩形是否相交
        :param other: 判断相交的另一个矩形obj
        :type other: RECTANGLE object
        :return: True or False
        :rtype: bool
        """
        # --定义当前矩形的左下角Ax1,Ay1和右上角Ax2,Ay2坐标
        lenAx = self.get_lenX()
        lenAy = self.get_lenY()
        # --定义other矩形的左下角Bx1,By1和右上角Bx2,By2坐标
        lenBx = other.get_lenX()
        lenBy = other.get_lenY()
        # --计算两个矩形坐标中的最大值、最小值
        min_x = min(self.xmin, other.xmin)
        min_y = min(self.ymin, other.ymin)
        max_x = max(self.xmax, other.xmax)
        max_y = max(self.ymax, other.ymax)
        # --判断两个矩形是否相交
        #if max(self.xmin, other.xmin) < min(self.xmax, other.xmax) and \
                #max(self.ymin, other.ymin) < min(self.ymax, other.ymax):
            #return True
        #else:
            #return False
            
        if max_x - min_x < lenAx + lenBx and max_y - min_y < lenAy + lenBy:
            # --x方向最大值最小值之差小于两个矩形x方向总长，且y方向最大值最小值之差也小于两个矩形y方向总长
            return True
        else:
            return False


class addFeatures(object):

    def __init__(self, parent=None):

        super(addFeatures, self).__init__()

    def start_add_info(self, step, matrixinfo, dic_zu_layername):
        """开始加pad line text"""

        for layer in matrixinfo["gROWname"]:
            if layer.strip():
                exits_info = []

                if layer in dic_zu_layername.keys() and dic_zu_layername[layer]:
                    step.clearAll()
                    step.affect(layer)

                    step.COM("units,type=mm")

                    for x, y, symbol, dic_symbol_info in dic_zu_layername[layer]:
                        if [x, y, symbol, dic_symbol_info, layer] in exits_info: continue

                        if "xSize" in dic_symbol_info.keys():
                            self.addTextInfo(step, x, y, symbol, dic_symbol_info)
                        elif "addRectangle" in dic_symbol_info.keys():
                            self.addSurfaceInfo(step, x, y, symbol, dic_symbol_info)
                        elif "addline" in dic_symbol_info.keys():
                            self.addLineInfo(step, x, y, symbol, dic_symbol_info)
                        else:
                            self.addPadInfo(step, x, y, symbol, dic_symbol_info)

                        exits_info.append([x, y, symbol, dic_symbol_info, layer])

                    step.clearAll()

    def addTextInfo(self, step, x, y, text, dic_zu={}):
        # step.PAUSE(str(text))
        dic_symbol = {"xSize": 1.2, "ySize": 1.5,
                      "width": 0.6999999881, "polarity": 'positive',
                      "angle": 0, "mirror": 'no', "attributes": 'no',
                      "attrstring": "", "fontname": "standard"}

        for key in dic_zu.keys():
            if key in dic_symbol.keys():
                dic_symbol[key] = dic_zu[key]
        # print dic_zu,dic_symbol
        if dic_symbol["attrstring"]:
            dic_symbol["attributes"] = "yes"
            step.COM("cur_atr_reset")
            if isinstance(dic_symbol["attrstring"], list):
                for attr in dic_symbol["attrstring"]:
                    step.COM("cur_atr_set,attribute=%s" % attr)
            else:
                step.COM("cur_atr_set,attribute=%s" % dic_symbol["attrstring"])            

        if "type" in dic_zu.keys():
            STR = "add_text,attributes=%s,type=canned_text,x=%s,y=%s,\
            text=%s,x_size=%s,y_size=%s,w_factor=%s,polarity=positive,\
            angle=%s,mirror=%s,fontname=%s,ver=1" % (dic_symbol["attributes"], x, y, text, dic_symbol["xSize"],
                                                     dic_symbol["ySize"], dic_symbol["width"], dic_symbol["angle"],
                                                     dic_symbol["mirror"], dic_symbol["fontname"])
            step.COM(STR)
        else:
            step.addText(x, y, text, dic_symbol["xSize"],
                         dic_symbol["ySize"], dic_symbol["width"],
                         dic_symbol["mirror"], dic_symbol["angle"],
                         dic_symbol["polarity"], dic_symbol["attributes"],
                         fontname=dic_symbol.get("fontname", "standard"))

        if dic_symbol["attrstring"]:
            step.COM("cur_atr_reset")

    def addPadInfo(self, step, x, y, symbol, dic_zu={}):
        dic_symbol = {"polarity": 'positive', "angle": 0,
                      "mirror": 'no', "nx": 1, "ny": 1,
                      "dx": 0, "dy": 0, "xscale": 1, "yscale": 1,
                      "attributes": 'no', "attrstring": ""}

        for key in dic_zu.keys():
            if key in dic_symbol.keys():
                dic_symbol[key] = dic_zu[key]
        if dic_symbol["attrstring"]:
            dic_symbol["attributes"] = "yes"
            step.COM("cur_atr_reset")
            if isinstance(dic_symbol["attrstring"], list):
                for attr in dic_symbol["attrstring"]:
                    step.COM("cur_atr_set,attribute=%s" % attr)
            else:
                step.COM("cur_atr_set,attribute=%s" % dic_symbol["attrstring"])

        step.addPad(x, y, symbol, dic_symbol["polarity"],
                    dic_symbol["angle"], dic_symbol["mirror"],
                    dic_symbol["nx"], dic_symbol["ny"],
                    dic_symbol["dx"], dic_symbol["dy"],
                    dic_symbol["xscale"], dic_symbol["yscale"],
                    dic_symbol["attributes"])

        if dic_symbol["attrstring"]:
            step.COM("cur_atr_reset")

    def addSurfaceInfo(self, step, xy1, xy2, symbol, dic_zu={}):

        x1, y1 = xy1
        x2, y2 = xy2

        dic_symbol = {"polarity": 'positive', "attributes": 'no', "attrstring": ""}

        step.COM("""fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,
        min_brush=25.4,use_arcs=yes,symbol=cu-d,dx=15.9,dy=5.29999,std_angle=45,
        std_line_width=254,std_step_dist=1270,std_indent=odd,break_partial=yes,cut_prims=yes,
        outline_draw=no,outline_width=0,outline_invert=no""")

        for key in dic_zu.keys():
            if key in dic_symbol.keys():
                dic_symbol[key] = dic_zu[key]
        if dic_symbol["attrstring"]:
            dic_symbol["attributes"] = "yes"
            step.COM("cur_atr_reset")
            if isinstance(dic_symbol["attrstring"], list):
                for attr in dic_symbol["attrstring"]:
                    step.COM("cur_atr_set,attribute=%s" % attr)
            else:
                step.COM("cur_atr_set,attribute=%s" % dic_symbol["attrstring"])

        step.addRectangle(x1, y1, x2, y2, dic_symbol["polarity"], dic_symbol["attributes"])

        if dic_symbol["attrstring"]:
            step.COM("cur_atr_reset")

    def addLineInfo(self, step, xy1, xy2, symbol, dic_zu={}):

        x1, y1 = xy1
        x2, y2 = xy2

        dic_symbol = {"polarity": 'positive', "attributes": 'no', "attrstring": ""}
        for key in dic_zu.keys():
            if key in dic_symbol.keys():
                dic_symbol[key] = dic_zu[key]
        if dic_symbol["attrstring"]:
            dic_symbol["attributes"] = "yes"
            step.COM("cur_atr_reset")
            if isinstance(dic_symbol["attrstring"], list):
                for attr in dic_symbol["attrstring"]:
                    step.COM("cur_atr_set,attribute=%s" % attr)
            else:
                step.COM("cur_atr_set,attribute=%s" % dic_symbol["attrstring"])

        step.addLine(x1, y1, x2, y2, symbol, dic_symbol["polarity"], dic_symbol["attributes"])

        if dic_symbol["attrstring"]:
            step.COM("cur_atr_reset")


class genesisFlip(object):

    def __init__(self, parent=None):

        super(genesisFlip, self).__init__()

    def get_gATTRval(self, stepname, attrnames):

        CMD = '-t step -e %s/%s -d ATTR' % (jobname, stepname)

        info = job.DO_INFO(CMD)

        gATTRname = info["gATTRname"]

        gATTRval = info["gATTRval"]

        for name in attrnames:

            if name in gATTRname:

                name_index = gATTRname.index(name)

                if gATTRval[name_index]:
                    return gATTRval[name_index]

        return None

    def get_flip_step(self, stepname, attrnames):
        return self.get_gATTRval(stepname, attrnames)

    def release_flip(self, steps=[]):
        """释放flip step"""
        if steps:
            arraylist_step = steps
        else:
            arraylist_step = matrixInfo["gCOLstep_name"]
        for stepname in arraylist_step:
            if not stepname: continue
            info = self.get_gATTRval(stepname, [".flipped_of", ".rotated_of"])
            if info is not None:
                job.VOF()
                job.COM("change_step_dependency,job=%s,step=%s,operation=release" % (jobname, stepname))
                job.VON()

    def is_exists_flip(self):
        for stepname in matrixInfo["gCOLstep_name"]:
            if not stepname: continue
            info = self.get_gATTRval(stepname, [".flipped_of", ".rotated_of", ".released_from"])
            if info is not None:
                return info

        return None

    def incam_is_exists_flip(self):
        """incam内判断是否有阴阳拼版"""
        for stepname in matrixInfo["gCOLstep_name"]:
            if not stepname:
                continue

            step = gClasses.Step(job, stepname)
            STR = '-t step -e %s/%s -d REPEAT,units=mm' % (jobname, stepname)
            gREPEAT_info = step.DO_INFO(STR)
            gREPEATflip = gREPEAT_info.get('gREPEATflip')
            if gREPEATflip is not None and \
                    "yes" in gREPEATflip:
                return True

        return False

    def incam_release_flip(self):
        job.VOF()
        job.COM("matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes" % jobname)
        job.VON()

    def incam_restore_flip(self):
        job.VOF()
        job.COM("matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no" % jobname)
        job.VON()

    def is_step_flip(self, name):

        is_flip = self.get_gATTRval(name, [".flipped_of", ".rotated_of", ".released_from"])

        return is_flip

    def is_step_flip_jm_zh(self, name):
        """江门珠海大连 不加入旋转进来"""
        is_flip = self.get_gATTRval(name, [".flipped_of", ".released_from"])
        if is_flip and is_flip.startswith("f"):
            return is_flip

        return None

    def restore_flip(self, steps=[]):
        """还原 flip rotate step"""
        rmode = {'1': 'center', '0': 'datum'}
        fmode = {'1': 'center', '0': 'anchor'}
        bmode = {'1': 'yes', '0': 'no'}

        if steps:
            arraylist_step = steps
        else:
            arraylist_step = matrixInfo["gCOLstep_name"]

        # 测试 此型号刷新就异常 这里测试直接退出
        # if "100383373" in jobname:
        # return

        for stepname in arraylist_step:
            if not stepname: continue
            info = self.get_gATTRval(stepname, [".released_from"])
            if info is not None:
                transform_data = self.get_gATTRval(stepname, [".transform_data"])
                mode_info = transform_data.split()
                job.VOF()
                job.COM("change_step_dependency,job=%s,step=%s,operation=restore" % (jobname, stepname))
                job.COM("update_dependent_step,job=%s,step=%s" % (jobname, stepname))
                if info.startswith("f"):
                    if len(mode_info) < 3:
                        mode = fmode[mode_info[0]]
                        new_layer_suffix = ""
                        board_only = bmode[mode_info[1]]
                    else:
                        mode = fmode[mode_info[0]]
                        new_layer_suffix = mode_info[1]
                        board_only = bmode[mode_info[2]]

                    job.COM("flip_step,job=%s,step=%s,flipped_step=%s,\
                    new_layer_suffix=%s,mode=%s,board_only=%s" % (jobname, info[1:],
                                                                  stepname, new_layer_suffix,
                                                                  mode, board_only))
                if info.startswith("r"):
                    angle = mode_info[0]
                    mode = rmode[mode_info[1]]
                    anchor_x = mode_info[2]
                    anchor_y = mode_info[3]
                    job.COM('rotate_step,job=%s,step=%s,rotated_step=%s,\
                    angle=%s,mode=%s,units=inch,anchor_x=%s,anchor_y=%s' % (jobname, info[1:],
                                                                            stepname, angle,
                                                                            mode, anchor_x,
                                                                            anchor_y))
                # 江门一厂旋转加阴阳刷新后需全部解锁成蓝色 20220302 by lyh
                if "+rot+flip" in "".join(arraylist_step):
                    self.release_flip([stepname])

                if job.STATUS > 0:
                    msg = u"自动刷新阴阳 或旋转step 失败，请手动刷新~".encode("cp936")
                    os.system("python %s/sys/scripts/suntak/lyh/messageBox.py %s" % (os.environ["GENESIS_DIR"], msg))
                job.VON()

    def refresh_flip(self):
        self.release_flip()
        self.restore_flip()


if __name__ == "__main__":
    main = genesisFlip()

    main.release_flip()

    main.restore_flip()
