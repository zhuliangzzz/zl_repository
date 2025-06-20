#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2022/08/31 首次上线日期：2022.09.16
# @Revision     :    1.0.0
# @File         :    split_del_other_symbol.py
# @Software     :    PyCharm
# @Usefor       :    分割料号删除标靶 http://192.168.2.120:82/zentao/story-view-4296.html
# ---------------------------------------------------------#

import os
import platform
import re
import sys
from PyQt4 import QtCore, QtGui
import json
# --加载相对位置，以实现InCAM与Genesis共用
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genCOM_26 as genCOM
from messageBox import msgBox


class MyApp(object):
    def __init__(self):
        self.job_name = os.environ.get('JOB')
        self.pnl_step = 'panel'
        self.GEN = genCOM.GEN_COM()
        self.layer_dict = self.GET_MATRIX_LAYER('signal,outer,solder_mask,silk_screen,drill,dld,sgt,md12', job=self.job_name)
        self.laser_layers = [i for i in self.layer_dict['drill'] if re.match('s\d+\-\d+',i)]
        print json.dumps(self.layer_dict,indent=2)
        # self.solder_layers = self.GEN.GET_ATTR_LAYER('solder_mask',job=self.job_name)
        # self.silk_layers = self.GEN.GET_ATTR_LAYER('silk_screen',job=self.job_name)

    def del_symbols(self):
        self.GEN.OPEN_STEP(step=self.pnl_step,job=self.job_name)
        self.GEN.CHANGE_UNITS('mm')
        layers = list(set([k for i, v in self.layer_dict.items() for k in v]))
        for layer in layers:
            bef_layer = '%s_del_bei_fen' % layer
            # --先备份层别
            self.GEN.COPY_LAYER(self.job_name, self.pnl_step, layer, bef_layer, mode='replace', invert='no')

        get_sr = self.get_sr_size()
        pnl_size = self.get_step_size(self.pnl_step)
        tmp_layer = '__tmp_split_del_symbols__'
        self.GEN.DELETE_LAYER(tmp_layer)
        # === 1.此项必须优先，由于tmp_layer此时无其他内容。sh-dwtop2013|sh-dwbot2013 外层共有8个，取消靠中间的四个，drl层有钻孔 ===
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('l1', 'yes')
        self.GEN.FILTER_RESET()
        self.GEN.FILTER_SET_INCLUDE_SYMS('sh-dwtop2013;sh-dwbot2013')
        self.GEN.FILTER_SELECT()
        del_dwtop = 'no'
        # === 当外层有8个时，才执行删除动作 ===
        if int(self.GEN.GET_SELECT_COUNT()) == 8:
            # ===  直接影响底层 ===
            self.GEN.CLEAR_LAYER()
            self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=top|bottom)')
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_INCLUDE_SYMS('sh-dwtop2013;sh-dwbot2013')
            self.GEN.COM('filter_area_strt')
            self.GEN.COM('filter_area_xy,x=%s,y=%s' % (get_sr['sr_xmin'], (get_sr['sr_ymin'] - 5)))
            self.GEN.COM('filter_area_xy,x=%s,y=%s' % (get_sr['sr_xmax'], (get_sr['sr_ymax'] + 5)))
            self.GEN.COM('filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,inside_area=yes,intersect_area=no')
            self.GEN.FILTER_RESET()

            if int(self.GEN.GET_SELECT_COUNT()) == 8:
                del_dwtop = 'yes'
                self.GEN.SEL_MOVE(tmp_layer)
        if del_dwtop == 'no':
            self.GEN.CLEAR_LAYER()
            self.GEN.COM('affected_filter,filter=(type=solder_mask&context=board&side=top|bottom)')
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_INCLUDE_SYMS('s4430;s4429')
            self.GEN.FILTER_SELECT()
            if int(self.GEN.GET_SELECT_COUNT()) != 0:
                self.GEN.SEL_COPY(tmp_layer)
                self.GEN.CLEAR_LAYER()
                self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=top|bottom)')
                self.GEN.FILTER_RESET()
                self.GEN.FILTER_SET_INCLUDE_SYMS('sh-dwtop2013;sh-dwbot2013')
                self.GEN.SEL_REF_FEAT(tmp_layer,'touch',include='s4430;s4429')
                if int(self.GEN.GET_SELECT_COUNT()) == 8:
                    del_dwtop = 'yes'
                    self.GEN.SEL_MOVE(tmp_layer)
        if del_dwtop == 'yes':
            self.GEN.CLEAR_LAYER()
            self.GEN.COM('affected_filter,filter=(type=solder_mask&context=board&side=top|bottom)')
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_INCLUDE_SYMS('s4430;s4429')
            self.GEN.SEL_REF_FEAT(tmp_layer, 'touch')
            if int(self.GEN.GET_SELECT_COUNT()) > 0:
                self.GEN.SEL_MOVE(tmp_layer)
                
            if len(self.layer_dict['md12']) > 0:
                self.GEN.CLEAR_LAYER()
                for layer in self.layer_dict['md12']:
                    self.GEN.AFFECTED_LAYER(layer, 'yes')
                self.GEN.FILTER_RESET()
                self.GEN.FILTER_SET_INCLUDE_SYMS('r3683')
                self.GEN.SEL_REF_FEAT(tmp_layer, 'touch')
                self.GEN.FILTER_RESET()
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_MOVE(tmp_layer)                
                
            self.GEN.CLEAR_LAYER()
            if 'drl' in self.layer_dict['drill']:
                self.GEN.AFFECTED_LAYER('drl', 'yes')
                self.GEN.FILTER_RESET()
                self.GEN.FILTER_SET_INCLUDE_SYMS('r3175')
                self.GEN.COM("sel_ref_feat,layers={0},use=filter,mode=same_center,"
                             "f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,"
                             "include_syms=s4430,exclude_syms=,on_multiple=smallest".format(tmp_layer)) # 20250312 zl 只删s4430位置的四个r3175
                # self.GEN.SEL_REF_FEAT(tmp_layer, 'touch')
                if int(self.GEN.GET_SELECT_COUNT()) == 4:
                    self.GEN.SEL_MOVE(tmp_layer)
            else:
                if 'cdc' in self.layer_dict['drill']:
                    # bef_layer = '%s_del_bei_fen' % 'cdc'
                    # --先备份层别
                    # self.GEN.COPY_LAYER(self.job_name, self.pnl_step, 'cdc', bef_layer, mode='replace', invert='no')
                    self.GEN.AFFECTED_LAYER('cdc', 'yes')
                    self.GEN.FILTER_SET_INCLUDE_SYMS('r3175')
                    # self.GEN.SEL_REF_FEAT(tmp_layer, 'touch')
                    self.GEN.COM("sel_ref_feat,layers={0},use=filter,mode=same_center,"
                                 "f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,"
                                 "include_syms=,exclude_syms=,on_multiple=smallest".format(tmp_layer))                      
                    if int(self.GEN.GET_SELECT_COUNT()) == 4:
                        self.GEN.SEL_MOVE(tmp_layer)
                elif 'cds' in self.layer_dict['drill']:
                    # bef_layer = '%s_del_bei_fen' % 'cds'
                    # --先备份层别
                    # self.GEN.COPY_LAYER(self.job_name, self.pnl_step, 'cds', bef_layer, mode='replace', invert='no')
                    self.GEN.AFFECTED_LAYER('cds', 'yes')
                    self.GEN.FILTER_SET_INCLUDE_SYMS('r3175')
                    # self.GEN.SEL_REF_FEAT(tmp_layer, 'touch')
                    self.GEN.COM("sel_ref_feat,layers={0},use=filter,mode=same_center,"
                                 "f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,"
                                 "include_syms=,exclude_syms=,on_multiple=smallest".format(tmp_layer))                      
                    if int(self.GEN.GET_SELECT_COUNT()) == 4:
                        self.GEN.SEL_MOVE(tmp_layer)
                        
            if len(self.layer_dict['sgt']) > 0:
                self.GEN.CLEAR_LAYER()
                for layer in self.layer_dict['sgt']:
                    self.GEN.AFFECTED_LAYER(layer, 'yes')
                self.GEN.FILTER_RESET()
                self.GEN.FILTER_SET_INCLUDE_SYMS('sh-dwtop2013;sh-dwbot2013')
                self.GEN.SEL_REF_FEAT(tmp_layer, 'touch')
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_MOVE(tmp_layer)
                # 20250312 zl 删除s4178 提出人：周涌
                self.GEN.FILTER_RESET()
                self.GEN.FILTER_SET_INCLUDE_SYMS('s4178')
                self.GEN.FILTER_SELECT()
                self.GEN.FILTER_RESET()
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_MOVE(tmp_layer)
                self.GEN.CLEAR_LAYER()

        if del_dwtop == 'no':
            text = "无法判断出外层CCD位置，未执行删除动作!"
            msg_box = msgBox()
            msg_box.warning(self, '警告', '%s' % text, QtGui.QMessageBox.Ok)
        # === sh-dwsig2014
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=top|bottom)')

        self.GEN.FILTER_RESET()
        self.GEN.FILTER_SET_INCLUDE_SYMS('sh-dwsig2014')

        self.GEN.COM('filter_area_strt')
        self.GEN.COM('filter_area_xy,x=%s,y=%s' % (pnl_size['xmin'], pnl_size['ymin']))
        self.GEN.COM('filter_area_xy,x=%s,y=%s' % (get_sr['sr_xmin'], pnl_size['ymax']))
        self.GEN.COM('filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,inside_area=yes,intersect_area=no')
        self.GEN.COM('filter_area_strt')
        self.GEN.COM('filter_area_xy,x=%s,y=%s' % (get_sr['sr_xmax'],pnl_size['ymin']))
        self.GEN.COM('filter_area_xy,x=%s,y=%s' % (pnl_size['xmax'], pnl_size['ymax']))
        self.GEN.COM('filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,inside_area=yes,intersect_area=no')
        self.GEN.FILTER_RESET()
        if int(self.GEN.GET_SELECT_COUNT()) == 8:
            self.GEN.SEL_MOVE(tmp_layer)
            # 20250306 changesymbol s4500 cover到的move
            dwsig_layer = tmp_layer + '+++'
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER(tmp_layer, 'yes')
            self.GEN.FILTER_SET_INCLUDE_SYMS('sh-dwsig2014')
            self.GEN.FILTER_SELECT()
            self.GEN.FILTER_RESET()
            self.GEN.SEL_COPY(dwsig_layer)
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER(dwsig_layer, 'yes')
            self.GEN.SEL_CHANEG_SYM('s4500')
            self.GEN.CLEAR_LAYER()
            self.GEN.COM('affected_filter,filter=(type=solder_mask&context=board&side=top|bottom)')
            self.GEN.FILTER_RESET()
            self.GEN.SEL_REF_FEAT(dwsig_layer, 'cover')
            self.GEN.FILTER_RESET()
            if self.GEN.GET_SELECT_COUNT():
                self.GEN.SEL_MOVE(tmp_layer)
                self.GEN.CLEAR_LAYER()
                self.GEN.DELETE_LAYER(dwsig_layer)
                if len(self.layer_dict['silk_screen']) > 0:
                    self.GEN.COM('affected_filter,filter=(type=silk_screen&context=board&side=top|bottom)')
                    self.GEN.FILTER_RESET()
                    self.GEN.FILTER_SET_INCLUDE_SYMS('sh-dwsd2014')
                    self.GEN.SEL_REF_FEAT(tmp_layer, 'touch', include='sh-dwsig2014')
                    self.GEN.FILTER_RESET()
                    if int(self.GEN.GET_SELECT_COUNT()) == len(self.layer_dict['silk_screen']) * 4:
                        self.GEN.SEL_MOVE(tmp_layer)
                if len(self.layer_dict['sgt']) > 0:
                    for layer in self.layer_dict['sgt']:
                        self.GEN.AFFECTED_LAYER(layer, 'yes')
                    self.GEN.FILTER_RESET()
                    self.GEN.FILTER_SET_INCLUDE_SYMS('sh-dwsig2014')
                    self.GEN.SEL_REF_FEAT(tmp_layer, 'touch', include='sh-dwsig2014')
                    if int(self.GEN.GET_SELECT_COUNT()) > 0:
                        self.GEN.SEL_MOVE(tmp_layer)
                    self.GEN.CLEAR_LAYER()
                    
                if len(self.layer_dict['md12']) > 0:
                    self.GEN.CLEAR_LAYER()
                    for layer in self.layer_dict['md12']:
                        self.GEN.AFFECTED_LAYER(layer, 'yes')
                    self.GEN.FILTER_RESET()
                    self.GEN.FILTER_SET_INCLUDE_SYMS('s3454')
                    self.GEN.SEL_REF_FEAT(tmp_layer, 'touch', include='sh-dwsig2014')
                    if int(self.GEN.GET_SELECT_COUNT()) > 0:
                        self.GEN.SEL_MOVE(tmp_layer)
                    self.GEN.CLEAR_LAYER()
                    
                self.GEN.CLEAR_LAYER()
                self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=inner)')
                self.GEN.FILTER_RESET()
                self.GEN.FILTER_SET_INCLUDE_SYMS('s3429')
                self.GEN.SEL_REF_FEAT(tmp_layer, 'touch', include='sh-dwsig2014')
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_MOVE(tmp_layer)
                self.GEN.CLEAR_LAYER()                

        # === sh_silk_autodw 外层两个，长边 防焊 r2516 文字层 sh-dwsd2014
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=top|bottom)')
        self.GEN.FILTER_RESET()
        self.GEN.FILTER_SET_INCLUDE_SYMS('sh_silk_autodw')
        self.GEN.COM('filter_area_strt')
        self.GEN.COM('filter_area_xy,x=%s,y=%s' % (pnl_size['xmin'], pnl_size['ymin']))
        self.GEN.COM('filter_area_xy,x=%s,y=%s' % (get_sr['sr_xmin'], pnl_size['ymax']))
        self.GEN.COM('filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,inside_area=yes,intersect_area=no')
        self.GEN.COM('filter_area_strt')
        self.GEN.COM('filter_area_xy,x=%s,y=%s' % (get_sr['sr_xmax'],pnl_size['ymin']))
        self.GEN.COM('filter_area_xy,x=%s,y=%s' % (pnl_size['xmax'], pnl_size['ymax']))
        self.GEN.COM('filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,inside_area=yes,intersect_area=no')
        self.GEN.FILTER_RESET()
        if int(self.GEN.GET_SELECT_COUNT()) == 4:
            self.GEN.SEL_MOVE(tmp_layer)
            self.GEN.CLEAR_LAYER()
            self.GEN.COM('affected_filter,filter=(type=solder_mask&context=board&side=top|bottom)')
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_INCLUDE_SYMS('r2516')
            self.GEN.SEL_REF_FEAT(tmp_layer, 'touch', include='sh_silk_autodw')
            self.GEN.FILTER_RESET()
            if int(self.GEN.GET_SELECT_COUNT()) == len(self.layer_dict['solder_mask']) * 2:
                self.GEN.SEL_MOVE(tmp_layer)
                self.GEN.CLEAR_LAYER()
                if len(self.layer_dict['silk_screen']) > 0:
                    self.GEN.COM('affected_filter,filter=(type=silk_screen&context=board&side=top|bottom)')
                    self.GEN.FILTER_RESET()
                    self.GEN.SEL_REF_FEAT(tmp_layer, 'touch', include='sh_silk_autodw')
                    self.GEN.FILTER_SET_INCLUDE_SYMS('sh-dwsd2014')
                    self.GEN.FILTER_RESET()
                    if int(self.GEN.GET_SELECT_COUNT()) == len(self.layer_dict['silk_screen']) * 2:
                        self.GEN.SEL_MOVE(tmp_layer)
                if len(self.layer_dict['sgt']) > 0:
                    for layer in self.layer_dict['sgt']:
                        self.GEN.AFFECTED_LAYER(layer, 'yes')
                    self.GEN.FILTER_RESET()
                    self.GEN.FILTER_SET_INCLUDE_SYMS('s4178')
                    self.GEN.SEL_REF_FEAT(tmp_layer, 'touch', include='sh_silk_autodw')
                    if int(self.GEN.GET_SELECT_COUNT()) > 0:
                        self.GEN.SEL_MOVE(tmp_layer)
                    self.GEN.CLEAR_LAYER()
                if len(self.layer_dict['md12']) > 0:
                    self.GEN.CLEAR_LAYER()
                    for layer in self.layer_dict['md12']:
                        self.GEN.AFFECTED_LAYER(layer, 'yes')
                    self.GEN.FILTER_RESET()
                    self.GEN.FILTER_SET_INCLUDE_SYMS('s3280')
                    self.GEN.SEL_REF_FEAT(tmp_layer, 'touch', include='sh_silk_autodw')
                    if int(self.GEN.GET_SELECT_COUNT()) > 0:
                        self.GEN.SEL_MOVE(tmp_layer)
                    self.GEN.CLEAR_LAYER()
        self.GEN.CLEAR_LAYER()
        # === 删除dld ===
        if len(self.layer_dict['dld']) > 0:
            self.GEN.COM('affected_filter,filter=(type=signal&context=board)')
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_INCLUDE_SYMS('sh-ldi')
            self.GEN.FILTER_SELECT()
            self.GEN.FILTER_RESET()
            if int(self.GEN.GET_SELECT_COUNT()) > 0:
                self.GEN.SEL_MOVE(tmp_layer)
                self.GEN.CLEAR_LAYER()
                for layer in self.layer_dict['dld']:
                    self.GEN.AFFECTED_LAYER(layer,'yes')
                self.GEN.FILTER_RESET()
                self.GEN.SEL_REF_FEAT(tmp_layer, 'touch', include='sh-ldi')
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_MOVE(tmp_layer)
                self.GEN.CLEAR_LAYER()
                self.GEN.COM('affected_filter,filter=(type=signal&context=board)')
                self.GEN.FILTER_RESET()
                self.GEN.FILTER_SET_INCLUDE_SYMS('s4000')
                self.GEN.SEL_REF_FEAT(tmp_layer, 'touch', include='sh-ldi')
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_MOVE(tmp_layer)
            self.GEN.CLEAR_LAYER()
        # === 删除五代靶 ===
        if len(self.laser_layers) > 0:
            self.GEN.COM('affected_filter,filter=(type=signal&context=board)')
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_INCLUDE_SYMS('hdi-dwpad')
            self.GEN.FILTER_SELECT()
            self.GEN.FILTER_RESET()
            if int(self.GEN.GET_SELECT_COUNT()) > 0:
                self.GEN.SEL_MOVE(tmp_layer)
                self.GEN.CLEAR_LAYER()
                for layer in self.laser_layers:
                    self.GEN.AFFECTED_LAYER(layer,'yes')
                self.GEN.FILTER_RESET()
                self.GEN.FILTER_SET_INCLUDE_SYMS('r520')
                self.GEN.SEL_REF_FEAT(tmp_layer, 'touch', include='hdi-dwpad')
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_MOVE(tmp_layer)
                self.GEN.CLEAR_LAYER()
                self.GEN.COM('affected_filter,filter=(type=signal&context=board)')
                self.GEN.FILTER_RESET()
                self.GEN.FILTER_SET_INCLUDE_SYMS('s5080;r0')
                self.GEN.SEL_REF_FEAT(tmp_layer, 'touch', include='hdi-dwpad')
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_MOVE(tmp_layer)
                if len(self.layer_dict['sgt']) > 0:
                    for layer in self.layer_dict['sgt']:
                        self.GEN.AFFECTED_LAYER(layer, 'yes')
                    self.GEN.FILTER_RESET()
                    self.GEN.FILTER_SET_INCLUDE_SYMS('s5588')
                    self.GEN.SEL_REF_FEAT(tmp_layer, 'touch', include='hdi-dwpad')
                    if int(self.GEN.GET_SELECT_COUNT()) > 0:
                        self.GEN.SEL_MOVE(tmp_layer)
                self.GEN.CLEAR_LAYER()
                self.GEN.COM('affected_filter,filter=(type=solder_mask&context=board&side=top|bottom)')
                self.GEN.FILTER_RESET()
                self.GEN.FILTER_SET_INCLUDE_SYMS('s5588')
                self.GEN.SEL_REF_FEAT(tmp_layer, 'touch', include='hdi-dwpad')
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_MOVE(tmp_layer)
                if len(self.layer_dict['md12']) > 0:
                    self.GEN.CLEAR_LAYER()
                    for layer in self.layer_dict['md12']:
                        self.GEN.AFFECTED_LAYER(layer, 'yes')
                    self.GEN.FILTER_RESET()
                    self.GEN.FILTER_SET_INCLUDE_SYMS('s5588')
                    self.GEN.SEL_REF_FEAT(tmp_layer, 'touch', include='hdi-dwpad')
                    if int(self.GEN.GET_SELECT_COUNT()) > 0:
                        self.GEN.SEL_MOVE(tmp_layer)
            # 20250619 zl 镭射层删除hdi-dwdrl
            self.GEN.CLEAR_LAYER()
            for layer in self.laser_layers:
                self.GEN.AFFECTED_LAYER(layer, 'yes')
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_INCLUDE_SYMS('hdi-dwdrl')
            self.GEN.FILTER_SELECT()
            self.GEN.FILTER_RESET()
            if int(self.GEN.GET_SELECT_COUNT()) > 0:
                self.GEN.SEL_MOVE(tmp_layer)
            self.GEN.CLEAR_LAYER()

        text = "运行完成，删除的所有symbol见层：%s!" % tmp_layer
        msg_box = msgBox()
        msg_box.information(self, '提示', '%s' % text, QtGui.QMessageBox.Ok)

    def get_sr_size(self):
        """
        获取拼版尺寸
        :return:
        """
        sr_dict = dict()
        info = self.GEN.DO_INFO('-t step -e %s/panel -m script -d SR_LIMITS' % self.job_name)
        sr_xmin = float(info['gSR_LIMITSxmin'])
        sr_xmax = float(info['gSR_LIMITSxmax'])
        sr_ymin = float(info['gSR_LIMITSymin'])
        sr_ymax = float(info['gSR_LIMITSymax'])
        sr_dict['sr_xmin'] = sr_xmin
        sr_dict['sr_xmax'] = sr_xmax
        sr_dict['sr_ymin'] = sr_ymin
        sr_dict['sr_ymax'] = sr_ymax
        sr_dict['sr_lenth'] = sr_xmax - sr_xmin
        sr_dict['sr_width'] = sr_ymax - sr_ymin
        return sr_dict

    def get_step_size(self, ip_step):
        """
        获取step大小，要求左下角在零点
        :param ip_step:
        :return:
        """
        panel_size = dict()
        getStepSize = self.GEN.DO_INFO("-t step -e %s/%s -d PROF_LIMITS,units=mm" % (self.job_name, ip_step))
        panel_size['xmin'] = getStepSize['gPROF_LIMITSxmin']
        panel_size['ymin'] = getStepSize['gPROF_LIMITSymin']
        panel_size['xmax'] = getStepSize['gPROF_LIMITSxmax']
        panel_size['ymax'] = getStepSize['gPROF_LIMITSymax']
        if panel_size['xmin'] != '0' or panel_size['ymin'] != '0':
            text = "'Step %s 原点不在零点处，请修改!" % (ip_step)
            msg_box = msgBox()
            msg_box.warning(self, '警告', '%s' % text, QtGui.QMessageBox.Ok)
            return False

        return panel_size

    def GET_MATRIX_LAYER(self, layer_types='drill,signal', job=None):
        """返回满足条件的字典"""
        layer_list = layer_types.split(',')
        m_info = self.GEN.DO_INFO('-t matrix -e %s/matrix' % job)
        LayValues = dict(zip(layer_list, [[] for i in layer_list]))
        for lay_type in layer_list:
            for row in m_info['gROWrow']:
                num = m_info['gROWrow'].index(row)
                if lay_type == 'drill':
                    if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'drill':
                        LayValues[lay_type].append(m_info['gROWname'][num])
                elif lay_type == 'signal':
                    if m_info['gROWcontext'][num] == 'board' and (
                            m_info['gROWlayer_type'][num] == 'signal' or m_info['gROWlayer_type'][num] == 'power_ground'):
                        LayValues[lay_type].append(m_info['gROWname'][num])
                elif lay_type == 'power_ground':
                    if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'power_ground':
                        LayValues[lay_type].append(m_info['gROWname'][num])
                elif lay_type == 'silk_screen':
                    if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'silk_screen':
                        LayValues[lay_type].append(m_info['gROWname'][num])
                elif lay_type == 'solder_mask':
                    if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'solder_mask':
                        LayValues[lay_type].append(m_info['gROWname'][num])
                elif lay_type == 'inner':
                    if m_info['gROWcontext'][num] == 'board' and m_info['gROWside'][num] == 'inner' and (
                            m_info['gROWlayer_type'][num] == 'signal' or m_info['gROWlayer_type'][num] == 'power_ground'):
                        LayValues[lay_type].append(m_info['gROWname'][num])
                elif lay_type == 'outer':
                    if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'signal' and (
                            m_info['gROWside'][num] == 'top' or m_info['gROWside'][num] == 'bottom'):
                        LayValues[lay_type].append(m_info['gROWname'][num])
                elif lay_type == 'coverlay':
                    if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'coverlay' and (
                            m_info['gROWside'][num] == 'top' or m_info['gROWside'][num] == 'bottom'):
                        LayValues[lay_type].append(m_info['gROWname'][num])
                elif lay_type == 'rout':
                    if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'rout':
                        LayValues[lay_type].append(m_info['gROWname'][num])
                elif lay_type == 'dld':
                    if re.match('dld\d+\-\d+', m_info['gROWname'][num]):
                        LayValues[lay_type].append(m_info['gROWname'][num])
                elif lay_type == 'sgt':
                    if re.match('sgt-c|sgt-s', m_info['gROWname'][num]):
                        LayValues[lay_type].append(m_info['gROWname'][num])
                elif lay_type == 'md12':
                    if re.match('md1|md2', m_info['gROWname'][num]):
                        LayValues[lay_type].append(m_info['gROWname'][num])                
                elif lay_type == 'all':
                    # --不为空时
                    # if not m_info['gROWname'][num]:
                    if m_info['gROWname'][num]:
                        LayValues[lay_type].append(m_info['gROWname'][num])
        # --返回对应数组信息
        return LayValues


# # # # --程序入口
if __name__ == "__main__":
    mapp = QtGui.QApplication(sys.argv)
    app = MyApp()
    app.del_symbols()

