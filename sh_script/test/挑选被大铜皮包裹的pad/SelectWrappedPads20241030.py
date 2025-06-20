#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:SelectWrappedPads.py
   @author:zl
   @time: 2024/10/28 17:52
   @software:PyCharm
   @desc:
   计算掏开的周长
"""

import os, sys
import os
import re
import sys
import platform

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genClasses_zl as gen
# import gClasses

from genesisPackages import get_mai_drill_hole, \
    get_drill_start_end_layers, get_panelset_sr_step, \
    outsignalLayers, innersignalLayers, solderMaskLayers, \
    silkscreenLayers, lay_num, top, get_sr_area_flatten, \
    laser_drill_layers, get_layer_selected_limits, \
    tongkongDrillLayer, mai_drill_layers, get_profile_limits, \
    get_sr_area_for_step_include, signalLayers, get_sr_limits, \
    get_panel_features_in_set_position, calcExposeArea, \
    mai_man_drill_layers, get_symbol_area


def select_bga_smd_by_surface_around():
    """挑选被铜面包围的smd bga 包围率50% 20241025 by lyh"""
    step = gen.Step(job, "edit")
    step.open()
    step.COM("units,type=mm")
    for layer in matrixinfo["gROWname"]:
        if "_surface" in layer or "_bga" in layer:
            step.removeLayer(layer)
    for worklayer in outsignalLayers:
        step.clearAll()
        step.affect(worklayer)
        step.resetFilter()
        step.setFilterTypes('surface', 'positive')
        step.COM('set_filter_attributes,filter_name=popup,exclude_attributes=yes,condition=no,attribute=.detch_comp,min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=')
        step.selectAll()
        if step.Selected_count():
            # step.removeLayer(worklayer + "_surface")
            step.copySel(worklayer + "_surface")
        step.selectNone()
        step.resetFilter()
        step.setAttrFilter(".bga")
        step.selectAll()
        if step.Selected_count():
            # step.removeLayer(worklayer + "_bga")
            step.copySel(worklayer + "_bga")
        step.clearAll()
        step.affect(worklayer + "_bga")
        step.resetFilter()
        step.refSelectFilter(worklayer + "_surface", mode="cover")
        if step.Selected_count():
            step.selectDelete()
        step.clearAll()
        step.affect(worklayer + "_surface")
        step.COM("sel_resize,size={0}".format(20 * 25.4))
        step.resetFilter()
        step.refSelectFilter(worklayer + "_bga", mode="disjoint")
        if step.Selected_count():
            step.selectDelete()
        step.COM("sel_resize,size=-{0}".format(20 * 25.4))
        step.selectAll()
        # layer_cmd = gen.Layer(step, worklayer + "_surface")
        # feat_indexes = layer_cmd.featSelIndex()
        # print(feat_indexes)
        step.PAUSE('1')
        feat_indexes = []
        feat_info = step.Features_INFO(worklayer + "_surface", mode='feat_index+select')
        for feat in feat_info:
            if feat and re.match('#\d+', feat[0]):
                feat_indexes.append(feat[0].replace('#', ''))
        step.PAUSE(worklayer)
        for sur_index in feat_indexes:
            if int(sur_index) != 137:
                continue
            step.clearAll()
            step.affect(worklayer + "_surface")
            step.selectNone()
            step.selectByIndex(worklayer + "_surface", sur_index)
            xmin, ymin, xmax, ymax = get_layer_selected_limits(step, worklayer + "_surface")
            step.VOF()
            step.removeLayer(worklayer + "_surface_{0}".format(sur_index))
            step.VON()
            step.copySel(worklayer + "_surface_{0}".format(sur_index))
            sel_surface_layer = worklayer + "_surface_{0}".format(sur_index)
            step.copyLayer(job.name, step.name, sel_surface_layer, sel_surface_layer + "_bak")
            step.clearAll()
            step.affect(sel_surface_layer)
            #
            step.COM('sel_clean_holes,max_size=99999,clean_mode=x_and_y')
            step.PAUSE('2')
            # step.COM("sel_surf2outline,width=1")
            step.surf_outline(1)
            step.copyLayer(job.name, step.name, sel_surface_layer, sel_surface_layer + "_line_bak")
            step.unaffectAll()
            rect = 'rectangle_%s' % sur_index
            step.VOF()
            step.removeLayer(rect)
            step.VON()
            step.createLayer(rect)
            step.affect(rect)
            step.addRectangle(float(xmin),float(ymin),float(xmax), float(ymax))
            step.unaffectAll()
            step.affect(sel_surface_layer)
            step.selectCutData()
            step.copySel(rect, 'yes')
            step.unaffectAll()
            step.affect(rect)
            step.Contourize()
            step.unaffectAll()
            step.affect(worklayer + "_bga")


if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    matrixinfo = job.matrix.getInfo()
    select_bga_smd_by_surface_around()
