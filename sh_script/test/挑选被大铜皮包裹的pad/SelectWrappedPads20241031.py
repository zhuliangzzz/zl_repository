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
import math
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

from genesisPackages import outsignalLayers, get_layer_selected_limits



def select_bga_smd_by_surface_around():
    """挑选被铜面包围的smd bga 包围率50% 20241025 by lyh"""
    step = gen.Step(job, "edit")
    step.initStep()
    # step.COM("units,type=mm")
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
        # 备份bga
        step.copyLayer(jobname, step.name, worklayer + '_bga', worklayer + "_bga_bak")
        # layer_cmd = gen.Layer(step, worklayer + "_surface")
        # feat_indexes = layer_cmd.featSelIndex()
        # print(feat_indexes)
        feat_indexes = []
        feat_info = step.Features_INFO(worklayer + "_surface", mode='feat_index+select')
        for feat in feat_info:
            if feat and re.match('#\d+', feat[0]):
                feat_indexes.append(feat[0].replace('#', ''))
        res_layer = worklayer + "_result"  # 被包裹的层
        step.VOF()
        step.removeLayer(res_layer)
        step.VON()
        for sur_index in feat_indexes:
            # if int(sur_index) != 137:
            #     continue
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
            step.unaffectAll()
            # 重新复制bga
            step.truncate(worklayer + "_bga")
            step.copyLayer(jobname, step.name, worklayer + '_bga_bak', worklayer + "_bga")
            step.affect(worklayer + "_bga")
            step.refSelectFilter(sel_surface_layer, mode='disjoint')
            if step.Selected_count():
                step.selectReverse()
                if step.Selected_count():
                    step.selectDelete()
            step.unaffectAll()
            step.affect(sel_surface_layer)
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
            # 放大bga掏出缺口处，再去找缺口处的轨迹
            step.affect(worklayer + "_bga")
            step.selectResize(300)
            step.refSelectFilter(sel_surface_layer)
            if step.Selected_count():
                step.selectReverse()
                if step.Selected_count():
                    step.selectDelete()
            step.unaffectAll()
            step.affect(sel_surface_layer)
            step.clip_area(ref_layer=worklayer + "_bga", margin=0)
            step.surf_outline(1)
            step.unaffectAll()
            step.affect(worklayer + "_bga")
            step.selectResize(2)
            step.unaffectAll()
            step.affect(sel_surface_layer)
            step.refSelectFilter(worklayer + "_bga", mode='cover')
            # 缺口外形层
            block_shape = worklayer + "_shape"
            bga = worklayer + "_bga_2"
            shape = worklayer + "_shape_2"
            step.VOF()
            step.removeLayer(block_shape)
            step.removeLayer(bga)
            step.removeLayer(shape)
            step.VON()
            if step.Selected_count():
                step.copySel(block_shape)
                step.unaffectAll()
                step.affect(worklayer + "_bga")
                step.selectResize(-2)
                # step.COM('sel_feat2outline,width=1,location=on_edge,offset=0,polarity=as_feature,keep_original=no,text2limit=no')
                step.unaffectAll()
                # 遍历bga去找外形
                feat_info = step.Features_INFO(worklayer + "_bga", mode='feat_index')
                bga_indexes = []
                for feat in feat_info:
                    if feat and re.match('#\d+', feat[0]):
                        bga_indexes.append(feat[0].replace('#', ''))
                # step.PAUSE('A')
                for bga_index in bga_indexes:
                    step.affect(worklayer + "_bga")
                    step.selectByIndex(worklayer + "_bga", bga_index)
                    step.copySel(bga)
                    step.unaffectAll()
                    step.affect(block_shape)
                    step.refSelectFilter(bga)
                    step.copySel(shape)
                    step.unaffectAll()
                    # 分别计算bga和外形的长度
                    step.affect(bga)
                    step.COM('sel_feat2outline,width=1,location=on_edge,offset=0,polarity=as_feature,keep_original=no,text2limit=no')
                    step.selectAll()
                    gen_layer = gen.Layer(step, bga)
                    feats = gen_layer.featSelOut(units='mm')
                    lenth_bga = []
                    for k, v in feats.items():
                        circle = []
                        for o in v:
                            if o.len == 0:  # 按圆去算周长
                                radius = math.hypot((o.xs - o.xc), (o.ys - o.yc))
                                circle.append(math.pi * radius * 2)
                            else:
                                circle.append(o.len)
                        lenth_bga.append(sum(circle))
                    lenth_bga = sum(lenth_bga)
                    step.unaffectAll()
                    #
                    step.affect(shape)
                    step.COM('arc2lines,arc_line_tol=5')  # 把弧转成线处理
                    step.selectAll()
                    # step.PAUSE(shape)
                    gen_layer = gen.Layer(step, shape)
                    feats = gen_layer.featSelOut(units='mm')
                    step.unaffectAll()
                    lenth_shape = []
                    for k, v in feats.items():
                        # print(v)
                        lenth_shape.append(sum([o.len for o in v]))
                    lenth_shape = sum(lenth_shape)
                    # print(lenth_shape)
                    rate = lenth_shape/lenth_bga
                    # print(lenth_shape, lenth_bga, rate)
                    # step.PAUSE(bga_index)
                    if rate > 0.5:
                        step.affect(bga)
                        step.selectCutData()
                        step.unaffectAll()
                        step.affect(worklayer + "_bga_bak")
                        step.refSelectFilter(bga, mode='cover')
                        step.copySel(res_layer)
                        step.unaffectAll()
                    # step.PAUSE(bga_index)
                    step.truncate(bga)
                    step.truncate(shape)
            # else:
            #     step.unaffectAll()
            step.unaffectAll()
            # step.PAUSE('AAAAA')


    for layer in matrixinfo["gROWname"]:
        if "_surface" in layer or "_bga" in layer or "_shape" in layer:
            step.removeLayer(layer)




if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    matrixinfo = job.matrix.getInfo()
    select_bga_smd_by_surface_around()
