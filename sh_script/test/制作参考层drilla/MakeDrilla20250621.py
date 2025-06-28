#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:MakeDrilla.py
   @author:zl
   @time: 2025/6/20 10:51
   @software:PyCharm
   @desc:
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
from genesisPackages_zl import outsignalLayers


class MakeDrilla(object):
    def __init__(self):
        self.job = gen.Job(jobname)
        stepname = 'set'
        self.step = gen.Step(self.job, stepname)

    def make(self):
        make_layer = 'drilla'
        self.step.initStep()
        self.step.removeLayer(make_layer)
        row = self.job.matrix.getRow('ww')
        self.job.matrix.addLayer(make_layer, row + 1)
        ss_list = self.job.matrix.returnRows('board', 'silk_screen')
        sm_list = self.job.matrix.returnRows('board', 'solder_mask')
        self.step.setUnits('inch')
        # 坏板点
        # bad_mark_layer = 'mark_layer+++%s'% self.step.pid
        # self.step.affect('l1')
        # self.step.setAttrFilter_pro('.fiducial_name', text='badmark')
        # self.step.setAttrLogic_pro()
        # self.step.selectAll()
        # if self.step.Selected_count():
        #     self.step.copySel(bad_mark_layer)
        # self.step.unaffectAll()
        for sm in sm_list:
            tmp_sm = '%s+++' % sm
            self.step.removeLayer(tmp_sm)
            self.step.affect(sm)
            self.step.copySel(tmp_sm)
            self.step.unaffectAll()
            self.step.affect(tmp_sm)
            # self.step.setAttrFilter_pro('.drill', option='non_plated')
            self.step.setAttrFilter_pro('.string', text='set')
            self.step.setAttrLogic_pro()
            self.step.selectAll()
            self.step.resetFilter()
            self.step.selectSymbol('cs-sm')
            self.step.resetFilter()
            if self.step.Selected_count():
                self.step.selectDelete()
            self.step.setAttrFilter_pro('.geometry', text='bf-coupon')
            self.step.setAttrLogic_pro()
            self.step.selectAll()
            if self.step.Selected_count():
                self.step.surf_outline(20)
            self.step.setAttrFilter_pro('.drill', option='non_plated')
            self.step.setAttrLogic_pro()
            self.step.refSelectFilter('ww')
            self.step.resetFilter()
            if self.step.Selected_count():
                self.step.selectDelete()
            self.step.setFilterTypes('surface|line')
            self.step.refSelectFilter('ww')
            self.step.resetFilter()
            if self.step.Selected_count():
                self.step.selectDelete()
            self.step.setFilterTypes('pad')
            self.step.refSelectFilter('ww')
            self.step.resetFilter()
            if self.step.Selected_count():
                self.step.selectResize(-40)
            self.step.setFilterTypes('text')
            self.step.refSelectFilter(make_layer)
            self.step.resetFilter()
            if self.step.Selected_count():
                self.step.selectDelete()
            self.step.copySel(make_layer)
            self.step.unaffectAll()
            self.step.removeLayer(tmp_sm)
        for ss in ss_list:
            tmp_ss = '%s+++' % ss
            self.step.removeLayer(tmp_ss)
            self.step.affect(ss)
            self.step.copySel(tmp_ss)
            self.step.unaffectAll()
            self.step.affect(tmp_ss)
            self.step.setAttrFilter_pro('.string', text='set')
            self.step.setAttrLogic_pro()
            self.step.selectAll()
            self.step.resetFilter()
            if self.step.Selected_count():
                self.step.selectDelete()
            self.step.setAttrFilter_pro('.string', text='2dmark')
            self.step.setAttrLogic_pro()
            self.step.selectAll()
            self.step.resetFilter()
            if self.step.Selected_count():
                self.step.feat_outline('5')
            self.step.copySel(make_layer)
            self.step.unaffectAll()
            self.step.removeLayer(tmp_ss)
        tmp_ww = 'ww+++'
        self.step.affect('ww')
        self.step.copySel(tmp_ww)
        self.step.unaffectAll()
        self.step.affect(tmp_ww)
        self.step.selectChange('r10')
        self.step.copySel(make_layer)
        self.step.unaffectAll()
        self.step.removeLayer(tmp_ww)
        self.step.setUnits('mm')
        light_pad_lays = []
        for signal in outsignalLayers:
            tmp_signal = '%s++++' % signal
            self.step.affect(signal)
            self.step.setFilterTypes('text')
            self.step.selectAll()
            self.step.resetFilter()
            if self.step.Selected_count():
                self.step.copySel(make_layer)
            self.step.setAttrFilter_pro('.fiducial_name')
            self.step.selectAll()
            self.step.resetFilter()
            if self.step.Selected_count():
                self.step.copySel(tmp_signal)
                light_pad_lays.append(tmp_signal)
            self.step.unaffectAll()
            self.step.affect(make_layer)
            self.step.setFilterTypes('negative')
            self.step.selectAll()
            self.step.resetFilter()
            if self.step.Selected_count():
                self.step.selectPolarity()
            self.step.unaffectAll()
        # 光电位置是否一致
        sign_layer = 'sign+++'
        self.step.createLayer(sign_layer)
        if len(light_pad_lays) == 2:
            same_pad_lay = 'same_light_pad+++'
            self.step.affect(light_pad_lays[0])
            self.step.refSelectFilter(light_pad_lays[1], mode='same_center')
            if self.step.Selected_count():
                self.step.copySel(same_pad_lay)
                self.step.unaffectAll()
                self.step.PAUSE('A')
                self.step.affect(light_pad_lays[0])
                self.step.refSelectFilter(same_pad_lay, mode='same_center')
                layerObj = gen.Layer(self.step, light_pad_lays[0])
                if self.step.Selected_count():
                    feats = layerObj.featout_dic_Index(units='mm', options='select+feat_index')['pads']
                    self.step.unaffectAll()
                    self.step.affect(sign_layer)
                    # add_text,type=string,polarity=positive,x=2.3474675,y=46.4094,text=M,fontname=standard,mirror=no,angle=0,direction=cw,
                    # x_size=2.54,y_size=2,w_factor=0.98425198
                    for feat in feats:
                        x, y = feat.x, feat.y
                        pad_radius = float(re.sub('r|s', '', feat.symbol))/1000
                        add_success = False
                        # for x_ in range(10 * (x - pad_radius - 3.3), 10 * (x - pad_radius - 1.84), 1):
                        for x_ in range(10 * (x - pad_radius - 1.84), 10 * (x - pad_radius - 3.3), -1):
                            self.step.addText(x_/10, y - pad_radius, 'M', 2.54, 2, 0.98425198)
                            self.step.refSelectFilter(make_layer)
                            if not self.step.Selected_count():
                                add_success = True
                                break
                            else:
                                self.step.truncate(sign_layer)
                        if not add_success:
                            for x_ in range(10 * (x + pad_radius + 0.3), 10 * (x + pad_radius + 3.3), 1):
                                self.step.addText(x_ /10, y - pad_radius, 'M', 2.54, 2, 0.98425198)
                                self.step.refSelectFilter(make_layer)
                                if not self.step.Selected_count():
                                    add_success = True
                                    break
                                else:
                                    self.step.truncate(sign_layer)
                        if add_success:
                            self.step.copySel(light_pad_lays[0])
                    self.step.truncate(sign_layer)
                    self.step.unaffectAll()
                    self.step.affect(light_pad_lays[0])
                    self.step.setFilterTypes('pad')
                    self.step.refSelectFilter(same_pad_lay, mode='same_center')
                    self.step.selectReverse()
                    self.step.PAUSE('A')
                    self.step.resetFilter()
                    if self.step.Selected_count():
                        feats = layerObj.featout_dic_Index(units='mm', options='select+feat_index')['pads']
                        self.step.unaffectAll()
                        self.step.affect(sign_layer)
                        # add_text,type=string,polarity=positive,x=2.3474675,y=46.4094,text=M,fontname=standard,mirror=no,angle=0,direction=cw,
                        # x_size=2.54,y_size=2,w_factor=0.98425198
                        for feat in feats:
                            x, y = feat.x, feat.y
                            pad_radius = float(re.sub('r|s', '', feat.symbol)) / 1000
                            add_success = False
                            # for x_ in range(10 * (x - pad_radius - 3.3), 10 * (x - pad_radius - 1.84), 1):
                            for x_ in range(10 * (x - pad_radius - 1.84), 10 * (x - pad_radius - 3.3), -1):
                                self.step.addText(x_ / 10, y - pad_radius, 'MC', 2.54, 2, 0.98425198)
                                self.step.refSelectFilter(make_layer)
                                if not self.step.Selected_count():
                                    add_success = True
                                    break
                                else:
                                    self.step.truncate(sign_layer)
                            if not add_success:
                                for x_ in range(10 * (x + pad_radius + 0.3), 10 * (x + pad_radius + 3.3), 1):
                                    self.step.addText(x_ / 10, y - pad_radius, 'MC', 2.54, 2, 0.98425198)
                                    self.step.refSelectFilter(make_layer)
                                    if not self.step.Selected_count():
                                        add_success = True
                                        break
                                    else:
                                        self.step.truncate(sign_layer)
                            if add_success:
                                self.step.copySel(light_pad_lays[0])
                self.step.truncate(sign_layer)
                self.step.unaffectAll()
                self.step.affect(light_pad_lays[1])
                self.step.refSelectFilter(same_pad_lay, mode='same_center')
                layerObj = gen.Layer(self.step, light_pad_lays[1])
                self.step.selectReverse()
                if self.step.Selected_count():
                    feats = layerObj.featout_dic_Index(units='mm', options='select+feat_index')['pads']
                    self.step.unaffectAll()
                    self.step.affect(sign_layer)
                    # add_text,type=string,polarity=positive,x=2.3474675,y=46.4094,text=M,fontname=standard,mirror=no,angle=0,direction=cw,
                    # x_size=2.54,y_size=2,w_factor=0.98425198
                    for feat in feats:
                        x, y = feat.x, feat.y
                        pad_radius = float(re.sub('r|s', '', feat.symbol)) / 1000
                        add_success = False
                        # for x_ in range(10 * (x - pad_radius - 3.3), 10 * (x - pad_radius - 1.84), 1):
                        for x_ in range(10 * (x - pad_radius - 1.84), 10 * (x - pad_radius - 3.3), -1):
                            self.step.addText(x_ / 10, y - pad_radius, 'MS', 2.54, 2, 0.98425198)
                            self.step.refSelectFilter(make_layer)
                            if not self.step.Selected_count():
                                add_success = True
                                break
                            else:
                                self.step.truncate(sign_layer)
                        if not add_success:
                            for x_ in range(10 * (x + pad_radius + 0.3), 10 * (x + pad_radius + 3.3), 1):
                                self.step.addText(x_ / 10, y - pad_radius, 'MS', 2.54, 2, 0.98425198)
                                self.step.refSelectFilter(make_layer)
                                if not self.step.Selected_count():
                                    add_success = True
                                    break
                                else:
                                    self.step.truncate(sign_layer)
                        if add_success:
                            self.step.copySel(light_pad_lays[1])
                self.step.unaffectAll()
            else: # 没有公共光学点
                self.step.affect(light_pad_lays[0])
                layerObj = gen.Layer(self.step, light_pad_lays[0])
                self.step.selectReverse()
                if self.step.Selected_count():
                    feats = layerObj.featout_dic_Index(units='mm', options='select+feat_index')['pads']
                    self.step.unaffectAll()
                    self.step.affect(sign_layer)
                    # add_text,type=string,polarity=positive,x=2.3474675,y=46.4094,text=M,fontname=standard,mirror=no,angle=0,direction=cw,
                    # x_size=2.54,y_size=2,w_factor=0.98425198
                    for feat in feats:
                        x, y = feat.x, feat.y
                        pad_radius = float(re.sub('r|s', '', feat.symbol)) / 1000
                        add_success = False
                        # for x_ in range(10 * (x - pad_radius - 3.3), 10 * (x - pad_radius - 1.84), 1):
                        for x_ in range(10 * (x - pad_radius - 1.84), 10 * (x - pad_radius - 3.3), -1):
                            self.step.addText(x_ / 10, y - pad_radius, 'MC', 2.54, 2, 0.98425198)
                            self.step.refSelectFilter(make_layer)
                            if not self.step.Selected_count():
                                add_success = True
                                break
                            else:
                                self.step.truncate(sign_layer)
                        if not add_success:
                            for x_ in range(10 * (x + pad_radius + 0.3), 10 * (x + pad_radius + 3.3), 1):
                                self.step.addText(x_ / 10, y - pad_radius, 'MC', 2.54, 2, 0.98425198)
                                self.step.refSelectFilter(make_layer)
                                if not self.step.Selected_count():
                                    add_success = True
                                    break
                                else:
                                    self.step.truncate(sign_layer)
                        if add_success:
                            self.step.copySel(light_pad_lays[0])
                self.step.unaffectAll()
                #
                self.step.truncate(sign_layer)
                self.step.affect(light_pad_lays[1])
                layerObj = gen.Layer(self.step, light_pad_lays[1])
                self.step.selectReverse()
                if self.step.Selected_count():
                    feats = layerObj.featout_dic_Index(units='mm', options='select+feat_index')['pads']
                    self.step.unaffectAll()
                    self.step.affect(sign_layer)
                    # add_text,type=string,polarity=positive,x=2.3474675,y=46.4094,text=M,fontname=standard,mirror=no,angle=0,direction=cw,
                    # x_size=2.54,y_size=2,w_factor=0.98425198
                    for feat in feats:
                        x, y = feat.x, feat.y
                        pad_radius = float(re.sub('r|s', '', feat.symbol)) / 1000
                        add_success = False
                        # for x_ in range(10 * (x - pad_radius - 3.3), 10 * (x - pad_radius - 1.84), 1):
                        for x_ in range(10 * (x - pad_radius - 1.84), 10 * (x - pad_radius - 3.3), -1):
                            self.step.addText(x_ / 10, y - pad_radius, 'MS', 2.54, 2, 0.98425198)
                            self.step.refSelectFilter(make_layer)
                            if not self.step.Selected_count():
                                add_success = True
                                break
                            else:
                                self.step.truncate(sign_layer)
                        if not add_success:
                            for x_ in range(10 * (x + pad_radius + 0.3), 10 * (x + pad_radius + 3.3), 1):
                                self.step.addText(x_ / 10, y - pad_radius, 'MS', 2.54, 2, 0.98425198)
                                self.step.refSelectFilter(make_layer)
                                if not self.step.Selected_count():
                                    add_success = True
                                    break
                                else:
                                    self.step.truncate(sign_layer)
                        if add_success:
                            self.step.copySel(light_pad_lays[1])
                self.step.unaffectAll()
            self.step.unaffectAll()
            self.step.removeLayer(same_pad_lay)
        elif len(light_pad_lays) == 1:
            text = 'MC' if light_pad_lays[0] == 'l1+++' else 'MS'
            self.step.affect(light_pad_lays[0])
            layerObj = gen.Layer(self.step, light_pad_lays[0])
            self.step.selectReverse()
            if self.step.Selected_count():
                feats = layerObj.featout_dic_Index(units='mm', options='select+feat_index')['pads']
                self.step.unaffectAll()
                self.step.affect(sign_layer)
                # add_text,type=string,polarity=positive,x=2.3474675,y=46.4094,text=M,fontname=standard,mirror=no,angle=0,direction=cw,
                # x_size=2.54,y_size=2,w_factor=0.98425198
                for feat in feats:
                    x, y = feat.x, feat.y
                    pad_radius = float(re.sub('r|s', '', feat.symbol)) / 1000
                    add_success = False
                    # for x_ in range(10 * (x - pad_radius - 3.3), 10 * (x - pad_radius - 1.84), 1):
                    for x_ in range(10 * (x - pad_radius - 1.84), 10 * (x - pad_radius - 3.3), -1):
                        self.step.addText(x_ / 10, y - pad_radius, text, 2.54, 2, 0.98425198)
                        self.step.refSelectFilter(make_layer)
                        if not self.step.Selected_count():
                            add_success = True
                            break
                        else:
                            self.step.truncate(sign_layer)
                    if not add_success:
                        for x_ in range(10 * (x + pad_radius + 0.3), 10 * (x + pad_radius + 3.3), 1):
                            self.step.addText(x_ / 10, y - pad_radius, text, 2.54, 2, 0.98425198)
                            self.step.refSelectFilter(make_layer)
                            if not self.step.Selected_count():
                                add_success = True
                                break
                            else:
                                self.step.truncate(sign_layer)
                    if add_success:
                        self.step.copySel(light_pad_lays[0])
            self.step.unaffectAll()
        self.step.removeLayer(sign_layer)
        if light_pad_lays:
            for light_pad_lay in light_pad_lays:
                self.step.affect(light_pad_lay)
                self.step.copySel(make_layer)
                self.step.unaffectAll()
                self.step.removeLayer(light_pad_lay)


if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    MakeDrilla().make()