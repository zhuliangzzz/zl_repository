#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#                  VGT SOFTWARE GROUP                      #
# ---------------------------------------------------------#
# @Author       :    LiJiaXing & LiuChuang
# @Mail         :    Chuang_cs@163.com
# @Date         :    2021.08.08
# @Revision     :    4.1
# @File         :    loss_coupon4.py
# @Software     :    PyCharm
# @Usefor       :    自动实现浪潮客户Loss条设计
# @Revision     :    4.0 变更需求见:http://192.168.2.120:82/zentao/story-view-3848.html
# ---------------------------------------------------------#
__version__ = "V1.0.0"

import csv
import json
import math
import os
import re
import sys
from PyQt4 import QtCore, QtGui, Qt
from PyQt4.QtGui import QMessageBox
#from PyQt4.QtCore import *
from collections import Mapping, MutableSequence
from operator import itemgetter

sys.path.append(r"%s/sys/scripts/Package" % os.environ.get('SCRIPTS_DIR'))
import genCOM_26 as genCOM
import Oracle_DB
from messageBoxPro import msgBox

import lossRunUI_v3 as FormUi
import checkBDdrill_add as BDDrill_Check
import getCompensationValue as getComp_Val

from get_icg_coupon_compensate_value import icg_coupon_compensate_value
icg_coupon_compensate = icg_coupon_compensate_value()

import gClasses
from create_ui_model import app
from SMK_Imp_TableDelegate import itemDelegate
from genesisPackages import matrixInfo, job, \
     getSmallestHole, laser_drill_layers, mai_drill_layers, \
     get_drill_start_end_layers, tongkongDrillLayer, signalLayers, \
     outsignalLayers, lay_num


#reload(sys)
#sys.setdefaultencoding('utf-8')
class listView(QtGui.QWidget):

    def __init__(self, parent = None):

        super(listView, self).__init__(parent)

        self.setWindowFlags(Qt.Qt.FramelessWindowHint | Qt.Qt.WindowMinimizeButtonHint | Qt.Qt.WindowSystemMenuHint | Qt.Qt.WindowStaysOnTopHint)

        self.listbox = QtGui.QListWidget()
        label = QtGui.QLabel(u"请勾阻值 然后点击确定")
        pushbtn = QtGui.QPushButton(u"确定")
        self.statusBar = QtGui.QStatusBar()
        self.statusBar.setFixedHeight(30)
        self.statusBar.addWidget(label)
        self.statusBar.addWidget(pushbtn)
        
        self.listbox.addItems(["", "10", "50", "100"])
        
        self.listbox.itemClicked.connect(self.onItemClicked)

        main_layout = QtGui.QVBoxLayout()        
        main_layout.addWidget(self.listbox)
        main_layout.addWidget(self.statusBar)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)        
        pushbtn.clicked.connect(self.set_layers)
        
        self.get_sigle_select_condition()        
        
    def onItemClicked(self, item):
        if self.sigle_select_condition == "yes":
            for i in range(self.listbox.count()):  
                if self.listbox.item(i) != item:  
                    self.listbox.item(i).setCheckState(0)
                    
    def get_sigle_select_condition(self, condition="no"):
        self.sigle_select_condition = condition
        
    def set_layers(self):
        values = []
        for index in range(self.listbox.count()):
            item = self.listbox.item(index)            
            if item.checkState() == 2:
                values.append(unicode(item.text().toUtf8(), 'utf8', 'ignore').encode('cp936').decode("cp936"))
        
        self.hide()
        self.emit(QtCore.SIGNAL("ohm_values(PyQt_PyObject)"), values)  


class Ding_wei_hole(object):
    """
    2.0mm的定位孔
    """

    def __init__(self, dw_xy_left=None, dw_xy_right=None, parm=None):
        self.dw_xy_left = dw_xy_left
        self.dw_xy_right = dw_xy_right
        self.parm = parm
        self.GEN = genCOM.GEN_COM()

    def all_process(self):
        """
        添加定位孔
        :return:
        :rtype:
        """
        if self.dw_xy_left is None or self.dw_xy_right is None:
            return
        else:
            self.hole_process()
            self.signal_process()
            self.md_process()
            self.mask_process()
            self.paste_process()

    def hole_process(self):
        """
        添加孔
        :return:
        :rtype:
        """
        dw_xy_left = sorted(self.dw_xy_left)
        dw_xy_right = sorted(self.dw_xy_right)
        ymax_right = sorted(self.dw_xy_right, key=itemgetter(1))[-1][1]
        xmax_right = sorted(self.dw_xy_right, key=itemgetter(1))[-1][0]
        # --左侧定位孔取xy最小值
        self.hole_x_left, self.hole_y_left = dw_xy_left[0]
        # --右侧定位孔取xy最大值
        self.hole_x_right, self.hole_y_right = xmax_right, ymax_right
        self.GEN.CLEAR_LAYER()
        self.GEN.WORK_LAYER('drl')
        self.GEN.COM('cur_atr_reset')
        self.GEN.COM('cur_atr_set,attribute=.drill,text=,option=non_plated')
        self.GEN.ADD_PAD(self.hole_x_left, self.hole_y_left, 'r78.74', pol='positive', attr='yes')
        self.GEN.ADD_PAD(self.hole_x_right, self.hole_y_right, 'r78.74', pol='positive', attr='yes')
        self.GEN.COM('cur_atr_reset')

    def signal_process(self):
        """
        套开内外层
        :return:
        :rtype:
        """
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=signal&context=board)')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_x_left, self.hole_y_left, 'r98.74', pol='negative')
            self.GEN.ADD_PAD(self.hole_x_right, self.hole_y_right, 'r98.74', pol='negative')
        self.GEN.CLEAR_LAYER()

    def md_process(self):
        """
        处理档点
        :return:
        :rtype:
        """
        md_pad = 'r%s' % (78.74 + 6.0)
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('md1', 'yes')
        self.GEN.AFFECTED_LAYER('md2', 'yes')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_x_left, self.hole_y_left, md_pad, pol='positive')
            self.GEN.ADD_PAD(self.hole_x_right, self.hole_y_right, md_pad, pol='positive')
        self.GEN.CLEAR_LAYER()

    def mask_process(self):
        """
        处理防焊
        :return:
        :rtype:
        """
        mask_pad = 'r%s' % (78.74 + 10.0)
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=solder_mask&context=board&side=top|bottom)')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_x_left, self.hole_y_left, mask_pad, pol='positive')
            self.GEN.ADD_PAD(self.hole_x_right, self.hole_y_right, mask_pad, pol='positive')
        self.GEN.CLEAR_LAYER()

    def paste_process(self):
        """
        处理锡膏
        :return:
        :rtype:
        """
        paste_pad = 'r%s' % (78.74 - 6)
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('p1', 'yes')
        self.GEN.AFFECTED_LAYER('p2', 'yes')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_x_left, self.hole_y_left, paste_pad, pol='positive')
            self.GEN.ADD_PAD(self.hole_x_right, self.hole_y_right, paste_pad, pol='positive')
        self.GEN.CLEAR_LAYER()


class NP_process(object):
    """
    每个loss对应四个NPTH孔,原点为连线pad的中心位置
    """

    def __init__(self, org_x=0.0, org_y=0.0, factor=1, parm=None):
        self.org_x = org_x
        self.org_y = org_y
        self.factor = factor
        self.parm = parm
        self.GEN = genCOM.GEN_COM()

    def all_process(self):
        """
        实际添加物件
        :return:
        :rtype:
        """
        self.hole_process()
        self.outer_process()
        # self.inner_process()
        self.md_process()
        self.mask_process()
        self.paste_process()

    def hole_process(self):
        """
        处理孔层
        :return:
        :rtype:
        """
        hole_sym = 'r%s' % self.parm.npSize
        self.hole_datum_x = self.org_x - 0.186 * self.factor
        self.hole_datum_y = self.org_y - 0.05
        self.GEN.CLEAR_LAYER()
        self.GEN.WORK_LAYER('drl')
        self.GEN.COM('cur_atr_reset')
        self.GEN.COM('cur_atr_set,attribute=.drill,text=,option=plated')
        self.GEN.ADD_PAD(self.hole_datum_x, self.hole_datum_y, hole_sym, pol='positive', nx=2, ny=2,
            dx=250 * self.factor, dy=100, attr='yes')
        self.GEN.COM('cur_atr_reset')

    def outer_process(self):
        """
        处理外层
        :return:
        :rtype:
        """
        outer_pad = 'r%s' % (self.parm.npSize + 12)
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=top|bottom)')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_datum_x, self.hole_datum_y, outer_pad, pol='positive', nx=2, ny=2,
                dx=250 * self.factor, dy=100, attr='yes')
        self.GEN.CLEAR_LAYER()

    def inner_process(self):
        """
        处理内层
        :return:
        :rtype:
        """
        inner_pad = 'r%s' % (self.parm.npSize + 15.824)
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=inner)')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_datum_x, self.hole_datum_y, inner_pad, pol='negative', nx=2, ny=2,
                dx=250 * self.factor, dy=100)
        self.GEN.CLEAR_LAYER()

    def md_process(self):
        """
        处理档点
        :return:
        :rtype:
        """
        md_pad = 'r%s' % (self.parm.npSize + 6.0)
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('md1', 'yes')
        self.GEN.AFFECTED_LAYER('md2', 'yes')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_datum_x, self.hole_datum_y, md_pad, pol='positive', nx=2, ny=2,
                dx=250 * self.factor, dy=100)
        self.GEN.CLEAR_LAYER()

    def mask_process(self):
        """
        处理防焊
        :return:
        :rtype:
        """
        mask_pad = 'r%s' % (self.parm.npSize + 14.0)
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=solder_mask&context=board&side=top|bottom)')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_datum_x, self.hole_datum_y, mask_pad, pol='positive', nx=2, ny=2,
                dx=250 * self.factor, dy=100)
        self.GEN.CLEAR_LAYER()

    def paste_process(self):
        """
        处理锡膏
        :return:
        :rtype:
        """
        paste_pad = 'r%s' % (self.parm.npSize - 3.937)
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('p1', 'yes')
        self.GEN.AFFECTED_LAYER('p2', 'yes')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_datum_x, self.hole_datum_y, paste_pad, pol='positive', nx=2, ny=2,
                dx=250 * self.factor, dy=100)
        self.GEN.CLEAR_LAYER()


class Tilt_via(object):
    """
    倾斜的伴随接地孔
    """

    def __init__(self, org_x=0.0, org_y=0.0, turn_points_upper=None, turn_points_lower=None, parm=None):
        self.org_x = org_x
        self.org_y = org_y
        self.turn_points_upper = turn_points_upper
        self.turn_points_lower = turn_points_lower
        self.parm = parm
        self.GEN = genCOM.GEN_COM()
        self.dx = 0.050 * math.cos(math.radians(10))
        self.dy = 0.050 * math.sin(math.radians(10))

    def horizontal_via(self, direct='upper'):
        """
        添加水平接地孔
        :return:
        :rtype:
        """
        viaTilt = self.parm.viaTilt
        tiltPad = 'r%s' % viaTilt
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('drl', 'yes')
        # --地孔添加属性
        self.GEN.COM('cur_atr_reset')
        self.GEN.COM('cur_atr_set,attribute=.string,text=tilt_via')
        if direct == 'lower':
            # --通过dy_factor将地孔加在线下
            dy_factor = -1
            turn_points = self.turn_points_lower
            y_coord = self.org_y - 0.15
            # y_coord = self.turn_points_lower[2][1] - 0.1
        else:
            # --通过dy_factor将地孔加在线上
            dy_factor = 1
            turn_points = self.turn_points_upper
            y_coord = self.org_y + 0.15
            # y_coord = self.turn_points_upper[1][1] + 0.1
        x_coord = turn_points[0][0] + 0.05
        length = turn_points[-1][0] - turn_points[0][0]
        # --计算总共可以添加的地孔数量
        pad_number = int((length - 0.05 * 2) / 0.05)
        # --小数部分超过0.5，计算多一个
        if math.modf(length / 0.05)[0] > 0.5:
            pad_number += 1
        self.GEN.ADD_PAD(x_coord, y_coord, tiltPad, pol='positive', nx=pad_number, ny=1, dx=50, dy=0, attr='yes')
        # --重置属性和层别
        self.GEN.COM('cur_atr_reset')
        self.GEN.CLEAR_LAYER()

    def add_via(self, direct='upper'):
        """
        添加下线via
        :return:
        :rtype:
        """
        viaTilt = self.parm.viaTilt
        tiltPad = 'r%s' % viaTilt
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('drl', 'yes')
        # --地孔添加属性
        self.GEN.COM('cur_atr_reset')
        self.GEN.COM('cur_atr_set,attribute=.string,text=tilt_via')
        if direct == 'lower':
            # --通过dy_factor将地孔加在线下
            dy_factor = -1
            turn_points = self.turn_points_lower
        else:
            # --通过dy_factor将地孔加在线上
            dy_factor = 1
            turn_points = self.turn_points_upper
        # --前一个点的坐标，初始化为0,0
        pre_x = 0
        pre_y = 0
        for i, (x_coord, y_coord) in enumerate(turn_points):
            j = i + 1
            factor = (-1) ** i
            # --最后一个点break出循环
            if j == len(turn_points):
                break
            # --计算第一个点的坐标
            dy = 0.09 / math.cos(math.radians(10))
            pad_x = x_coord
            pad_y = y_coord + dy * dy_factor

            # --第一段线第一个点不加，因为此位置可能会有2.0的定位孔，需要避开
            if pre_x != 0 and pre_y != 0:
                # --计算与前一个地孔的距离，小于30mil的不加
                pre_distance = math.hypot(pad_x - pre_x, pad_y - pre_y)
                if pre_distance > 0.03:
                    self.GEN.ADD_PAD(pad_x, pad_y, tiltPad, pol='positive', nx=1, ny=1, dx=0, dy=0, attr='yes')

            # --计算此段折线的总长度
            next_x, next_y = turn_points[j]
            length = math.hypot(next_x - x_coord, next_y - y_coord)
            # --计算此段折线总共可以添加的地孔数量
            pad_number = int((length - 0.05) / 0.05)
            # --小数部分超过0.5，计算多一个
            if math.modf(length / 0.05)[0] > 0.5:
                pad_number += 1
            # --依次添加其它的地孔
            for _i in range(pad_number):
                pad_x += self.dx
                pad_y += self.dy * factor
                self.GEN.ADD_PAD(pad_x, pad_y, tiltPad, pol='positive', nx=1, ny=1, dx=0, dy=0, attr='yes')
                # --重置前一个地孔的坐标
                pre_x = pad_x
                pre_y = pad_y
        # --重置属性和层别
        self.GEN.COM('cur_atr_reset')
        self.GEN.CLEAR_LAYER()


class PTH_process(object):
    """
    每个loss对应五个PTH孔,原点为连线pad的中心位置,分两次添加，中心pad和四个角
    """

    def __init__(self, layer=None, org_x=0.0, org_y=0.0, factor=1, ground_layer=None, parm=None):
        self.layer = layer
        self.org_x = org_x
        self.org_y = org_y
        self.factor = factor
        self.ground_layer = ground_layer
        self.parm = parm
        self.GEN = genCOM.GEN_COM()

    def all_process(self):
        """
        实际添加物件
        :return:
        :rtype:
        """
        self.hole_process()
        # self.ground_process()
        self.outer_process()
        self.inner_process()

        # --改成了小过孔,不需要再做挡点及阻焊
        # @formatter:off
        # self.md_process()
        # self.mask_process()
        # self.paste_process()
        # @formatter:on


    def hole_process(self):
        """
        处理孔层
        :return:
        :rtype:
        """
        pthSize = self.parm.viaSize
        pthPad = 'r%s' % pthSize
        self.hole_datum_x = self.org_x - 0.122 * self.factor
        self.hole_datum_y = self.org_y - 0.05
        self.hole_center_x = self.org_x - 0.122 * self.factor
        self.hole_center_y = self.org_y
        self.GEN.CLEAR_LAYER()
        self.GEN.WORK_LAYER('drl')
        self.GEN.COM('cur_atr_reset')
        self.GEN.COM('cur_atr_set,attribute=.drill,text=,option=plated')
        # self.GEN.PAUSE('SSS1')
        # # --先加上下两组
        # self.GEN.ADD_PAD(self.hole_datum_x,self.hole_datum_y,pthPad,pol='positive',nx=2,ny=2,dx=48*self.factor,dy=100,attr='yes')
        # self.GEN.PAUSE('SSS2')
        # # --再加中间一个
        # self.GEN.ADD_PAD(self.hole_center_x,self.hole_center_y,pthPad,pol='positive',attr='yes')
        # self.GEN.PAUSE('SSS3')

        # --按原点直接添加(右侧添加需要旋转)
        if self.factor == 1:
            self.GEN.ADD_PAD(self.org_x, self.org_y, 'loss_hole_pg_cu', pol='positive', attr='yes')
            if self.layer not in outer:
                self.GEN.ADD_PAD(self.org_x, self.org_y, 'loss_hole_pg', pol='positive', attr='yes')
            # self.GEN.PAUSE('SSS3')
        else:
            self.GEN.ADD_PAD(self.org_x, self.org_y, 'loss_hole_pg_cu', pol='positive', attr='yes', angle=180)
            if self.layer not in outer:
                self.GEN.ADD_PAD(self.org_x, self.org_y, 'loss_hole_pg', pol='positive', attr='yes', angle=180)
        # --打散，并过滤出图形改变成实际大小
        for loosSym in ('loss_hole_pg_cu', 'loss_hole_pg'):
            self.GEN.SEL_BREAK()
            self.GEN.FILTER_TEXT_ATTR('.bit', loosSym, reset=1)
            self.GEN.FILTER_SELECT()
            if self.GEN.GET_SELECT_COUNT() > 0:
                self.GEN.SEL_CHANEG_SYM(pthPad)

        self.GEN.COM('cur_atr_reset')

    def outer_process(self):
        """
        处理外层
        :return:
        :rtype:
        """
        outer_pad = 'r%s' % (self.parm.pthSize + 12)
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=top|bottom)')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_datum_x, self.hole_datum_y, outer_pad, pol='positive', nx=2, ny=2,
                dx=48 * self.factor, dy=100)
            self.GEN.ADD_PAD(self.hole_center_x, self.hole_center_y, outer_pad, pol='positive')
        self.GEN.CLEAR_LAYER()

    def inner_process(self):
        """
        处理内层
        :return:
        :rtype:
        """
        pass

    def md_process(self):
        """
        处理档点
        :return:
        :rtype:
        """
        md_pad = 'r%s' % (self.parm.pthSize + 8)
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('md1', 'yes')
        self.GEN.AFFECTED_LAYER('md2', 'yes')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_datum_x, self.hole_datum_y, md_pad, pol='positive', nx=2, ny=2,
                dx=48 * self.factor, dy=100)
            self.GEN.ADD_PAD(self.hole_center_x, self.hole_center_y, md_pad, pol='positive')
        self.GEN.CLEAR_LAYER()

    def mask_process(self):
        """
        处理防焊
        :return:
        :rtype:
        """
        mask_pad = 'r%s' % (self.parm.pthSize + 15.001)
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=solder_mask&context=board&side=top|bottom)')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_datum_x, self.hole_datum_y, mask_pad, pol='positive', nx=2, ny=2,
                dx=48 * self.factor, dy=100)
            self.GEN.ADD_PAD(self.hole_center_x, self.hole_center_y, mask_pad, pol='positive')
        self.GEN.CLEAR_LAYER()

    def paste_process(self):
        """
        处理锡膏
        :return:
        :rtype:
        """
        paste_pad = 'r%s' % (self.parm.pthSize + 6.063)
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('p1', 'yes')
        self.GEN.AFFECTED_LAYER('p2', 'yes')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_datum_x, self.hole_datum_y, paste_pad, pol='positive', nx=2, ny=2,
                dx=48 * self.factor, dy=100)
            self.GEN.ADD_PAD(self.hole_center_x, self.hole_center_y, paste_pad, pol='positive')
        self.GEN.CLEAR_LAYER()

    def ground_process(self):
        """
        测试pad接地
        :return:
        :rtype:
        """
        rect_x = self.hole_center_x - self.factor * (0.138 - 0.095) / 2
        rect_y = self.hole_center_y
        if self.ground_layer:
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER(self.ground_layer, 'yes')
            self.GEN.COM('get_affect_layer')
            layers = self.GEN.COMANS.split()
            if len(layers) > 0:
                self.GEN.ADD_PAD(rect_x, rect_y, 'rect233x174', pol='positive')
            self.GEN.CLEAR_LAYER()


class VIA_process(object):
    """
    每个loss对应四个NPTH孔,原点为连线pad的中心位置
    """

    def __init__(self, layer='l1', org_x=0.0, org_y=0.0, bd_layer=None, stub_side='top', parm=None, onlyBd_add=False):
        self.layer = layer
        self.org_x = org_x
        self.org_y = org_y
        self.hole_inner_x = self.org_x
        self.hole_inner_y = self.org_y - 0.015
        self.bd_layer = bd_layer
        self.stub_side = stub_side
        self.parm = parm
        self.GEN = genCOM.GEN_COM()
        self.JOB = os.environ.get('JOB', None)
        self.onlyBd_add = onlyBd_add


    def all_process(self):
        """
        实际添加物件
        :return:
        :rtype:
        """
        if self.layer not in outer:
            # 当多次添加时，图形层忽略（第一次已加过）
            if not self.onlyBd_add:
                self.hole_process()
                self.anti_process()
                self.outer_process()
                self.inner_process()
                # self.md_process()
                # self.mask_process()
                # self.paste_process()
                self.lp_process()
            # self.GEN.PAUSE('1-Layer:%s Bd_layer:%s' % (self.layer, self.bd_layer))
            self.bd_process()
            # self.GEN.PAUSE('2-Layer:%s Bd_layer:%s' % (self.layer, self.bd_layer))

    def hole_process(self):
        """
        处理孔层
        :return:
        :rtype:
        """
        viaSize = self.parm.viaSize
        viaPad = 'r%s' % viaSize

        self.line_yd = self.hole_inner_y
        self.line_yu = self.hole_inner_y + 0.03
        self.hole_outer_x = self.org_x
        self.hole_outer_y = self.org_y - 0.015 - 0.035
        self.GEN.CLEAR_LAYER()
        self.GEN.WORK_LAYER('drl')
        self.GEN.ADD_PAD(self.hole_inner_x, self.hole_inner_y, viaPad, pol='positive', nx=1, ny=2, dx=0, dy=30)
        self.GEN.ADD_PAD(self.hole_outer_x, self.hole_outer_y, viaPad, pol='positive', nx=1, ny=2, dx=0, dy=100)

    def anti_process(self):
        """
        椭圆的anti pad套开内外层
        :return:
        :rtype:
        """
        if self.layer not in outer:
            # --所有内层套开,antiPad
            self.GEN.CLEAR_LAYER()
            anti_pad = 'r%s' % self.parm.antiSize
            self.GEN.COM('cur_atr_reset')
            self.GEN.COM('cur_atr_set,attribute=.string,text=loss_anti')
            self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=inner)')
            self.GEN.COM('get_affect_layer')
            layers = self.GEN.COMANS.split()
            if len(layers) > 0:
                self.GEN.ADD_LINE(self.hole_inner_x, self.line_yu, self.hole_inner_x, self.line_yd, anti_pad,
                    pol='negative', attr='yes')

            # --外层套开(张莹要求外层比内层大10Mil即可)
            # anti_pad_out = 'r%s' % (self.parm.antiSize + 18.016)
            anti_pad_out = 'r%s' % (self.parm.antiSize + 10)
            if self.stub_side == 'top':
                self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=bottom)')
            else:
                self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=top)')
            self.GEN.COM('get_affect_layer')
            layers = self.GEN.COMANS.split()
            if len(layers) > 0:
                self.GEN.ADD_LINE(self.hole_inner_x, self.line_yu, self.hole_inner_x, self.line_yd, anti_pad_out,
                    pol='negative', attr='yes')
            self.GEN.COM('cur_atr_reset')
            self.GEN.CLEAR_LAYER()

    def outer_process(self):
        """
        处理外层
        :return:
        :rtype:
        """
        outer_pad_o = 'r%s' % (self.parm.viaSize + 14.357)
        outer_pad_i = 'r%s' % (self.parm.viaSize + 14.357)
        if self.bd_layer:
            outer_pad_i = 'r%s' % self.parm.viaSize
        self.GEN.CLEAR_LAYER()
        # --外围接地pad
        # self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=top|bottom)')
        # self.GEN.COM('get_affect_layer')
        # layers = self.GEN.COMANS.split()
        # if len(layers) > 0:
        # self.GEN.ADD_PAD(self.hole_outer_x, self.hole_outer_y, outer_pad_o, pol='positive', nx=1, ny=2, dx=0, dy=100)

        # --接线pad
        if self.stub_side == 'top':
            self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=top)')
            self.GEN.COM('get_affect_layer')
            layers = self.GEN.COMANS.split()
            if len(layers) > 0:
                # --添加symgol图形(当外层有信号线时，不添加另个基材位置的接地孔)
                self.GEN.ADD_PAD(self.org_x, self.org_y, 'loss_hole_pg_cu', pol='positive', attr='yes')
                # --仅当外层没有线路时，才加基材上的接地孔
                if self.layer not in outer:
                    self.GEN.ADD_PAD(self.org_x, self.org_y, 'loss_hole_pg', pol='positive', attr='yes')

                # --选择并打散
                for looSym in ('loss_hole_pg', 'loss_hole_pg_cu'):
                    self.GEN.FILTER_SET_INCLUDE_SYMS(looSym, reset=1)
                    self.GEN.FILTER_SELECT()
                    if self.GEN.GET_SELECT_COUNT() > 0:
                        self.GEN.SEL_BREAK()
                        # --TODO 这里考虑使用size来过滤可避免每次添加都会change到size
                        self.GEN.FILTER_TEXT_ATTR('.bit', looSym, reset=1)
                        self.GEN.FILTER_SELECT()
                        if self.GEN.GET_SELECT_COUNT() > 0:
                            self.GEN.SEL_CHANEG_SYM(outer_pad_o)

                # self.GEN.PAUSE("555555555555555555555555555-1")
                self.GEN.ADD_PAD(self.hole_inner_x, self.hole_inner_y, outer_pad_o, pol='positive', nx=1, ny=2, dx=0,
                    dy=30)
                # self.GEN.PAUSE("555555555555555555555555555-2")
            self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=bottom)')
            self.GEN.COM('get_affect_layer')
            layers = self.GEN.COMANS.split()
            if len(layers) > 0:
                self.GEN.ADD_PAD(self.hole_inner_x, self.hole_inner_y, outer_pad_i, pol='positive', nx=1, ny=2, dx=0,
                    dy=30)
        else:
            self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=bottom)')
            self.GEN.COM('get_affect_layer')
            layers = self.GEN.COMANS.split()
            if len(layers) > 0:
                # --添加symgol图形
                self.GEN.ADD_PAD(self.org_x, self.org_y, 'loss_hole_pg_cu', pol='positive', attr='yes', angle=180)
                if self.layer not in outer:
                    self.GEN.ADD_PAD(self.org_x, self.org_y, 'loss_hole_pg', pol='positive', attr='yes', angle=180)
                # --选择并打散
                for looSym in ('loss_hole_pg', 'loss_hole_pg_cu'):
                    self.GEN.FILTER_SET_INCLUDE_SYMS(looSym, reset=1)
                    self.GEN.FILTER_SELECT()
                    if self.GEN.GET_SELECT_COUNT() > 0:
                        self.GEN.SEL_BREAK()
                        self.GEN.FILTER_TEXT_ATTR('.bit', looSym, reset=1)
                        self.GEN.FILTER_SELECT()
                        if self.GEN.GET_SELECT_COUNT() > 0:
                            self.GEN.SEL_CHANEG_SYM(outer_pad_o)
                self.GEN.ADD_PAD(self.hole_inner_x, self.hole_inner_y, outer_pad_o, pol='positive', nx=1, ny=2, dx=0,
                    dy=30)
            self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=top)')
            self.GEN.COM('get_affect_layer')
            layers = self.GEN.COMANS.split()
            if len(layers) > 0:
                self.GEN.ADD_PAD(self.hole_inner_x, self.hole_inner_y, outer_pad_i, pol='positive', nx=1, ny=2, dx=0,
                    dy=30)
        self.GEN.CLEAR_LAYER()

    def inner_process(self):
        """
        处理内层
        :return:
        :rtype:
        """
        if self.layer not in outer:
            # --走线层加接线pad
            inner_pad = 'r%s' % (self.parm.viaSize + 12.157)
            self.GEN.WORK_LAYER(self.layer)
            self.GEN.COM('cur_atr_reset')
            self.GEN.COM('cur_atr_set,attribute=.string,text=test_point')            
            self.GEN.ADD_PAD(self.hole_inner_x, self.hole_inner_y, inner_pad, pol='positive', nx=1, ny=2, dx=0, dy=30, attr='yes')
            self.GEN.COM('cur_atr_reset')
            

    def md_process(self):
        """
        处理档点
        :return:
        :rtype:
        """
        md_pad = 'r%s' % (self.parm.viaSize + 10)
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('md1', 'yes')
        self.GEN.AFFECTED_LAYER('md2', 'yes')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_inner_x, self.hole_inner_y, md_pad, pol='positive', nx=1, ny=2, dx=0, dy=30)
            self.GEN.ADD_PAD(self.hole_outer_x, self.hole_outer_y, md_pad, pol='positive', nx=1, ny=2, dx=0, dy=100)
        self.GEN.CLEAR_LAYER()

    def mask_process(self):
        """
        处理防焊
        :return:
        :rtype:
        """
        mask_pad = 'r%s' % (self.parm.viaSize + 16.557)
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=solder_mask&context=board&side=top|bottom)')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_inner_x, self.hole_inner_y, mask_pad, pol='positive', nx=1, ny=2, dx=0, dy=30)
            self.GEN.ADD_PAD(self.hole_outer_x, self.hole_outer_y, mask_pad, pol='positive', nx=1, ny=2, dx=0, dy=100)
        self.GEN.CLEAR_LAYER()

    def paste_process(self):
        """
        处理锡膏
        :return:
        :rtype:
        """
        paste_pad = 'r%s' % (self.parm.viaSize + 10)
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('p1', 'yes')
        self.GEN.AFFECTED_LAYER('p2', 'yes')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_inner_x, self.hole_inner_y, paste_pad, pol='positive', nx=1, ny=2, dx=0, dy=30)
            self.GEN.ADD_PAD(self.hole_outer_x, self.hole_outer_y, paste_pad, pol='positive', nx=1, ny=2, dx=0, dy=100)
        self.GEN.CLEAR_LAYER()

    def lp_process(self):
        """
        铝片层D+6
        :return:
        :rtype:
        """
        lp_pad = 'r%s' % (self.parm.viaSize + 6)
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('lp', 'yes')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.hole_inner_x, self.hole_inner_y, lp_pad, pol='positive', nx=1, ny=2, dx=0, dy=30)
            self.GEN.ADD_PAD(self.hole_outer_x, self.hole_outer_y, lp_pad, pol='positive', nx=1, ny=2, dx=0, dy=100)
        self.GEN.CLEAR_LAYER()

    def bd_process(self):
        """
        处理背钻层（同板内该层最小的孔径一致）-统一为inch
        :return:
        :rtype:
        """
        bdRegex = re.compile(r'bd([1-9][0-9]?)-([1-9][0-9]?)')
        self.GEN.CLEAR_LAYER()
        bd_info = self.parm.bd_info
        if self.bd_layer:
            bd_layer = self.bd_layer.lower()
            match_Obj = bdRegex.match(bd_layer).groups()
            try:
                # --取出当前信号层与当前料号中的bd层起始屋对比，判断是否穿过或接触
                if int(match_Obj[0]) <= int(self.layer[1:]) <= int(match_Obj[1]) or \
                        int(match_Obj[1]) <= int(self.layer[1:]) <= int(match_Obj[0]):
                    # --从Inplan中对比，当前信号层是不是要钻穿层
                    for layDict in bd_info:
                        _layer = layDict.layer
                        if bd_layer == _layer:
                            index_start = layDict.index_start
                            index_end = layDict.index_end
                            # --从top面钻
                            if index_start < index_end:
                                if index_start < int(self.layer[1:]) <= index_end:
                                    return
                            else:
                                if index_end <= int(self.layer[1:]) < index_start:
                                    return
            except:
                pass
                # --当前信号层与背钻冲突时不作添加背钻
            # --改成同板内一样的背钻孔大小
            bd_pad = self.getBdDrillSize(bd_layer)
            self.GEN.VOF()
            self.GEN.AFFECTED_LAYER(bd_layer, 'yes')
            self.GEN.VON()
            self.GEN.COM('get_affect_layer')
            layers = self.GEN.COMANS.split()

            if len(layers) > 0:
                self.GEN.ADD_PAD(self.hole_inner_x, self.hole_inner_y, bd_pad, pol='positive', nx=1, ny=2, dx=0, dy=30)
            self.GEN.CLEAR_LAYER()

    def getBdDrillSize(self, bd_layer):
        """
        获取背钻层中对应的孔大小(unit_run:全局变量) 统一为inch单位
        :return:bd size
        """
        symbolList = self.GEN.DO_INFO(
            '-t layer -e %s/%s/%s -d SYMS_HIST -p symbol -o break_sr,  units=inch' % (self.JOB, 'edit', bd_layer))
        if len(symbolList) > 0:
            return symbolList['gSYMS_HISTsymbol'][0]
        else:
            return 'r%s' % (self.parm.viaSize + 10)


class outer_mark(object):
    """
    仅外层l1添加标识
    """

    def __init__(self, mark_top=None, mark_top_x=None, mark_top_y=None, mark_bot=None, mark_bot_x=None, mark_bot_y=None,
                 loss_layer=None):
        self.mark_top = mark_top
        self.mark_bot = mark_bot
        self.mark_top_x = mark_top_x
        self.mark_top_y = mark_top_y
        self.mark_bot_x = mark_bot_x
        self.mark_bot_y = mark_bot_y
        self.loss_layer = loss_layer
        self.GEN = genCOM.GEN_COM()

    def add_mark_top(self):
        """
        在外层添加mark
        :return:
        :rtype:
        """
        mark_list = self.mark_top
        mark_x = self.mark_top_x
        mark_y = self.mark_top_y
        for mark, x, y in zip(mark_list, mark_x, mark_y):
            mark_layer = mark.split("_")[0].lower()
            self.GEN.WORK_LAYER('l1')
            self.GEN.ADD_TEXT(x, y, mark, 0.03, 0.035, w_factor=0.4166666567, attr='no',
                polarity='negative', angle='0', mirr='no', font='standard')
            # self.GEN.PAUSE("check add mark top")
            # --字符层加正字
            self.GEN.CLEAR_LAYER()
            self.GEN.COM('affected_filter,filter=(type=silk_screen&context=board&side=top)')
            self.GEN.COM('get_affect_layer')
            layers = self.GEN.COMANS.split()
            for layer in layers:
                if layer in ['xlxm-c', 'xlxm-s']:
                    self.GEN.AFFECTED_LAYER(layer, 'no')
            self.GEN.COM('get_affect_layer')
            layers = self.GEN.COMANS.split()
            if len(layers) > 0:
                self.GEN.ADD_TEXT(x, y, mark, 0.03, 0.035, w_factor=0.4166666567, attr='no',
                    polarity='positive', angle='0', mirr='no', font='standard')
            self.GEN.CLEAR_LAYER()

    def add_mark_bot(self):
        """
        在外层添加mark
        :return:
        :rtype:
        """
        mark_list = self.mark_bot
        mark_x = self.mark_bot_x
        mark_y = self.mark_bot_y
        for mark, x, y in zip(mark_list, mark_x, mark_y):
            mark_layer = mark.split("_")[0].lower()
            self.GEN.WORK_LAYER(outer[1])
            self.GEN.ADD_TEXT(x, y, mark, 0.03, 0.035, w_factor=0.4166666567, attr='no',
                polarity='negative', angle='0', mirr='yes', font='standard')
            # self.GEN.PAUSE("check add mark bot")
            # --字符层加正字
            self.GEN.CLEAR_LAYER()
            self.GEN.COM('affected_filter,filter=(type=silk_screen&context=board&side=bottom)')
            self.GEN.COM('get_affect_layer')
            layers = self.GEN.COMANS.split()
            for layer in layers:
                if layer in ['xlxm-c', 'xlxm-s']:
                    self.GEN.AFFECTED_LAYER(layer, 'no')
            self.GEN.COM('get_affect_layer')
            layers = self.GEN.COMANS.split()
            if len(layers) > 0:
                self.GEN.ADD_TEXT(x, y, mark, 0.03, 0.035, w_factor=0.4166666567, attr='no',
                    polarity='positive', angle='0', mirr='yes', font='standard')
            self.GEN.CLEAR_LAYER()


class stub_process(object):
    """
    仅外层top与防焊top面有图形
    """

    def __init__(self, layer='l1', stub_side='top', org_x=0.0, org_y=0.0, factor=1, refer1='l2', ohms=85.0,
                 line_width=0, line_space=0, refer2=None, parm=None):
        self.layer = layer
        self.org_x = org_x
        self.org_y = org_y
        self.factor = factor
        self.refer1 = refer1
        self.refer2 = refer2
        self.ohms = ohms
        self.line_width = line_width
        self.line_space = line_space
        self.parm = parm
        self.stub_side = stub_side
        self.GEN = genCOM.GEN_COM()

    def all_process(self):
        """
        实际添加物件
        :return:
        :rtype:
        """
        if self.layer not in outer:
            self.clear_process()
        self.surface_process()
        self.pad_process()
        if self.layer not in outer:
            self.connect_line_process()

    def get_line_info(self):
        """
        获取当前ohms对应外层的线宽间距
        :return:
        :rtype:
        """
        line_width, line_space = None, None
        for layDict in self.parm.impAll:
            layer = layDict.layer
            ohms = layDict.ohms
            if ohms == self.ohms and layer in outer:
                line_width = layDict.line_width
                line_space = layDict.line_space                
                return line_width, line_space
        return line_width, line_space

    def connect_line_process(self):
        """
        用两根线连接两个pad
        :return:
        :rtype:
        """
        line_width, line_space = self.get_line_info()
        if line_width is None and line_space is None:
            line_width = self.line_width
            line_space = self.line_space
        # --线中心到中心的一半
        half_l2l = (line_width + line_space) / 2000.0
        line_sym = 'r%s' % line_width
        # --test pad连线坐标计算
        self.pad_x_test = self.org_x - 0.0404 * self.factor
        self.pad_yu_test = self.org_y + 0.00984
        self.pad_yd_test = self.org_y - 0.00984
        self.line_yu = self.org_y + half_l2l
        self.line_yd = self.org_y - half_l2l
        line_angle = 45
        angle_radians = math.radians(line_angle)
        dy1 = self.pad_yu_test - self.line_yu
        self.p2l_dx1 = dy1 * math.tan(angle_radians) * self.factor
        self.line_xs_upper = self.pad_x_test + self.p2l_dx1
        self.line_xs_lower = self.pad_x_test + self.p2l_dx1
        # --via pad连线坐标计算
        self.pad_x_via = self.org_x
        self.pad_yu_via = self.org_y + 0.015
        self.pad_yd_via = self.org_y - 0.015
        dy2 = self.pad_yu_via - self.line_yu
        self.p2l_dx2 = dy2 * math.tan(angle_radians) * self.factor
        self.line_xe_upper = self.pad_x_via - self.p2l_dx2
        self.line_xe_lower = self.pad_x_via - self.p2l_dx2

        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=%s)' % self.stub_side)
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            # --upper线添加
            self.GEN.ADD_LINE(self.pad_x_test, self.pad_yu_test, self.line_xs_upper, self.line_yu, line_sym)
            self.GEN.ADD_LINE(self.line_xs_upper, self.line_yu, self.line_xe_upper, self.line_yu, line_sym)
            self.GEN.ADD_LINE(self.line_xe_upper, self.line_yu, self.pad_x_via, self.pad_yu_via, line_sym)
            # --lower线添加
            self.GEN.ADD_LINE(self.pad_x_test, self.pad_yd_test, self.line_xs_lower, self.line_yd, line_sym)
            self.GEN.ADD_LINE(self.line_xs_lower, self.line_yd, self.line_xe_lower, self.line_yd, line_sym)
            self.GEN.ADD_LINE(self.line_xe_lower, self.line_yd, self.pad_x_via, self.pad_yd_via, line_sym)
        self.GEN.CLEAR_LAYER()

    def pad_process(self):
        """
        外层无孔pad处理,此pad用来拉loss线，外层直接与loss线相连，内层通过via孔对应的pad相连
        :return:
        :rtype:
        """
        # --从界面获取到的testSize
        testOuter = self.parm.testSize if 'rect' in self.parm.testSize else 'r%s' % self.parm.testSize
        # --防焊D+3
        if 'rect' in self.parm.testSize:
            rectSize = self.parm.testSize[4:].split('x')
            # 20250310 zl 加补偿
            testOuter = 'rect%sx%s' % (float(rectSize[0]) + float(self.parm.comp), float(rectSize[1]) + float(self.parm.comp))
            testMask = 'rect%sx%s' % (float(rectSize[0]) + 3, float(rectSize[1]) + 3)
        else:
            testMask = 'r%s' % (float(self.parm.testSize) + float(self.parm.comp))
        self.pad_x = self.org_x - 0.0404 * self.factor
        # self.pad_y = self.org_y - 0.0197
        self.pad_y = self.org_y - 0.00984
        # --添加外层Pad
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=%s)' % self.stub_side)
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()

        if len(layers) > 0:
            # --添加symgol图形
            if self.factor == 1:
                self.GEN.ADD_PAD(self.org_x, self.org_y, 'loss_hole_pg_cu', pol='positive', attr='yes')
                if self.layer not in outer:
                    self.GEN.ADD_PAD(self.org_x, self.org_y, 'loss_hole_pg', pol='positive', attr='yes')
            else:
                self.GEN.ADD_PAD(self.org_x, self.org_y, 'loss_hole_pg_cu', pol='positive', attr='yes', angle=180)
                if self.layer not in outer:
                    self.GEN.ADD_PAD(self.org_x, self.org_y, 'loss_hole_pg', pol='positive', attr='yes', angle=180)
            # --选择并打散
            for lossSym in ('loss_hole_pg', 'loss_hole_pg_cu'):
                self.GEN.FILTER_SET_INCLUDE_SYMS(lossSym, reset=1)
                self.GEN.FILTER_SELECT()
                if self.GEN.GET_SELECT_COUNT() > 0:
                    self.GEN.SEL_BREAK()
                    # --TODO 这里考虑使用size来过滤可避免每次添加都会change到size
                    self.GEN.FILTER_TEXT_ATTR('.bit', lossSym, reset=1)
                    self.GEN.FILTER_SELECT()
                    if self.GEN.GET_SELECT_COUNT() > 0:
                        self.GEN.SEL_CHANEG_SYM('r%s' % (self.parm.viaSize + 14.357))

            # self.GEN.ADD_PAD(self.pad_x,self.pad_y,testOuter,pol='positive',nx=1,ny=2,dx=0,dy=39.4)
            self.GEN.CUR_ART_RESET()
            # --增加smd属性，防止使用外层DFM优化时，切偏
            self.GEN.CUR_ATR_SET(attr='.smd')
            self.GEN.ADD_PAD(self.pad_x, self.pad_y, testOuter, pol='positive', nx=1, ny=2, dx=0, dy=19.68, attr='yes')
            self.GEN.CUR_ART_RESET()

        # --参考层中间夹的层别套开,只有外层走线需要套开，内层走线有antiPad套开
        if self.layer in outer:
            self.GEN.CLEAR_LAYER()
            layer_id = int(self.layer[1:])
            refer1_id = int(self.refer1[1:])
            # --计算参考层最大最小值
            if self.refer2 == 'None':
                if self.layer == outer[0]:
                    refer_min = layer_id + 1
                    refer_max = refer1_id
                elif self.layer == outer[1]:
                    refer_min = refer1_id
                    refer_max = layer_id - 1
            else:
                refer2_id = int(self.refer2[1:])
                refer_min = min(refer1_id, refer2_id)
                refer_max = max(refer1_id, refer2_id)
            # --在参考层最小最大值中间的都需要套开
            for layer in outer + inner:
                layer_id = int(layer[1:])
                if layer_id >= refer_min and layer_id <= refer_max:
                    self.GEN.AFFECTED_LAYER(layer, 'yes')
            self.GEN.COM('get_affect_layer')
            layers = self.GEN.COMANS.split()
            if len(layers) > 0:
                self.GEN.ADD_PAD(self.pad_x, self.pad_y, testOuter, pol='negative', nx=1, ny=2, dx=0, dy=19.68)
        else:
            self.GEN.CLEAR_LAYER()
            if self.stub_side == 'top':
                self.GEN.AFFECTED_LAYER('l2', 'yes')
            else:
                sub_layer = 'l%s' % (self.parm.layer_number - 1)
                self.GEN.AFFECTED_LAYER(sub_layer, 'yes')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.pad_x, self.pad_y, testOuter, pol='negative', nx=1, ny=2, dx=0, dy=19.68)

        # --添加防焊pad
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=solder_mask&context=board&side=%s)' % self.stub_side)
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.pad_x, self.pad_y, testMask, pol='positive', nx=1, ny=2, dx=0, dy=19.68)
        self.GEN.CLEAR_LAYER()

    def surface_process(self):
        """
        外层加loss_stub_outer_v4,防焊加loss_sm_small_v4
        :return:
        :rtype:
        """
        self.stub_x = self.org_x - 0.0777099 * self.factor
        if self.factor == 1:
            mirror = 'no'
        else:
            mirror = 'yes'
        self.stub_y = self.org_y
        # --外层
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=%s)' % self.stub_side)
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.stub_x, self.stub_y, 'loss_stub_outer_v4', pol='positive', mir=mirror)
        # --防焊开窗
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=solder_mask&context=board&side=%s)' % self.stub_side)
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.ADD_PAD(self.stub_x, self.stub_y, 'loss_sm_small_v4', pol='positive', mir=mirror)
        self.GEN.CLEAR_LAYER()

    def clear_process(self):
        """
        外层净空
        :return:
        :rtype:
        """
        # self.clear_x = self.org_x - 0.03082*self.factor
        self.clear_x = self.org_x - 0.021319 * self.factor
        self.clear_y = self.org_y
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=%s)' % self.stub_side)
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            # self.GEN.ADD_PAD(self.clear_x, self.clear_y, 'rect181.64x168.2', pol='negative')
            self.GEN.ADD_PAD(self.clear_x, self.clear_y, 'rect105.362x84.3', pol='negative')


class line_process(object):
    """
    走线，包括水平线和折线
    """

    def __init__(self, layer='l1', org_x=0, org_y=0, line_width=6.7, line_space=3.8, line_lenth=2.0, factor=1,
                 upper_length=0, lower_length=0, up_first='no', layDict=None):
        self.org_x = org_x
        self.org_y = org_y
        self.layer = layer
        self.org_layer = layer[:-5]
        self.line_width = line_width
        self.line_space = line_space
        self.line_lenth = line_lenth
        self.factor = factor
        
        self.org_width = layDict.org_width
        self.org_space = layDict.org_space
        self.ohms = layDict.ohms
        self.refer1 = layDict.refer1
        self.refer2 = layDict.refer2
        
        self.upper_length = upper_length
        self.lower_length = lower_length
        self.up_first = up_first
        self.turn_points_upper = []
        self.turn_points_lower = []
        self.GEN = genCOM.GEN_COM()

    def all_process(self):
        """
        处理孔层
        :return:
        :rtype:
        """
        # --左侧pad到线
        self.pad_to_line_left()
        # --左侧水平线
        self.horizon_line_left()
        # --获取最左侧、最右侧折线的高度
        self.get_broken_dy()
        # --左侧斜线
        self.left_dia_line(self.line_xe_upper, self.line_yu, self.line_xe_lower, self.line_yd)
        # --标准长的折线，循环添加
        for i in range(int(self.broken_line_number)):
            line_xe_upper, line_ye_upper = self.broken_line(self.line_xe_upper, self.line_ye_upper)
            line_xe_lower, line_ye_lower = self.broken_line(self.line_xe_lower, self.line_ye_lower)
            self.upper_length += math.hypot(line_xe_upper - self.line_xe_upper, line_ye_upper - self.line_ye_upper)
            self.lower_length += math.hypot(line_xe_lower - self.line_xe_lower, line_ye_lower - self.line_ye_lower)
            self.line_xe_upper = line_xe_upper
            self.line_ye_upper = line_ye_upper
            self.line_xe_lower = line_xe_lower
            self.line_ye_lower = line_ye_lower
            self.turn_points_upper.append((line_xe_upper, line_ye_upper))
            self.turn_points_lower.append((line_xe_lower, line_ye_lower))
        # --右侧斜线
        self.right_dia_line(self.line_xe_upper, self.line_ye_upper, self.line_xe_lower, self.line_ye_lower)
        # --右侧水平线
        self.horizon_line_right()
        # --右侧pad到线
        self.pad_to_line_right()

    def get_right_org(self):
        """
        获取右侧原点
        :return:
        :rtype:
        """
        if self.org_layer in outer:
            return self.line_xe_upper - 0.0404, self.org_y
        else:
            return self.line_xe_upper, self.org_y

    def broken_line(self, line_xs, line_ys):
        """
        折线
        :return:
        :rtype:
        """
        if line_ys > self.org_y:
            line_ye = line_ys - self.broken_dy_max
        else:
            line_ye = line_ys + self.broken_dy_max
        line_xe = line_xs + 0.4
        self.GEN.COM('cur_atr_reset')
        self.GEN.COM('cur_atr_set,attribute=.string,text=loss_line')
        self.GEN.COM('cur_atr_set, attribute =imp_lw_ref_info, text ={0}_{1}_{2}_{3}_{4}_{5}'.format(
            self.org_width,self.org_space, 0,self.ohms, self.refer1, self.refer2
        ))
        self.GEN.ADD_LINE(line_xs, line_ys, line_xe, line_ye, self.line_sym, attr='yes')
        self.GEN.COM('cur_atr_reset')
        return line_xe, line_ye

    def get_broken_dy(self):
        """
        获取折线的y坐标
        :return:
        :rtype:
        """
        # --线倾斜角度10度
        dia_angle = 10
        # --将角度转换为弧度
        dia_radians = math.radians(dia_angle)
        self.dia_radians = dia_radians
        # --每折水平距离400mil,垂直方向dy/400=tan(10)
        self.broken_dy_max = 0.4 * math.tan(dia_radians)
        # --计算每折的长度
        self.broken_line_length = math.hypot(self.broken_dy_max, 0.4)
        self.broken_line_number = 0
        if self.factor == 1:
            # --总长2inch- pad_to_line - horizon_line = 剩下的折线的长度
            dia_length = self.line_lenth - 2 * self.upper_length
            # --计算宽度达到400mil的折线的数量
            self.broken_line_number = math.modf(dia_length / self.broken_line_length)[1] - 2
            # --计算剩下的宽度小于400mil的折线的总长度
            remain_dia_length = dia_length - self.broken_line_number * self.broken_line_length
            # --计算宽度小于400mil的折线的高度
            self.broken_dy2 = 0.25 * (self.broken_dy_max + remain_dia_length * math.sin(dia_radians))
            self.broken_dy1 = self.broken_dy2 - 0.5 * self.broken_dy_max
        else:
            remain_dia_length = self.line_lenth - self.upper_length
            # --计算宽度小于400mil的折线的高度
            self.broken_dy2 = 0.25 * self.broken_dy_max + 0.5 * remain_dia_length * math.sin(dia_radians)
            self.broken_dy1 = self.broken_dy2 - 0.5 * self.broken_dy_max

    def left_dia_line(self, line_xs_upper, line_ys_upper, line_xs_lower, line_ys_lower, recursion=False):
        """
        左侧斜线,10度或-10度均可以
        :return:
        :rtype:
        """
        # --线倾斜角度10度
        dia_radians = self.dia_radians
        # --计算upper线的起始结束点y坐标差值
        if recursion:
            # --递归调用
            dy_upper = self.broken_dy2
            dy_factor = -1
        else:
            dy_upper = self.broken_dy1
            dy_factor = 1
        # --计算upper线的x坐标
        dx_upper = dy_upper / math.tan(dia_radians)
        if self.up_first == 'yes':
            line_ye_upper = line_ys_upper + dy_upper * dy_factor
        else:
            line_ye_upper = line_ys_upper - dy_upper * dy_factor
        line_xe_upper = line_xs_upper + dx_upper * self.factor

        # --计算lower终点y坐标差值
        line_xe_lower = line_xe_upper
        dx_lower = math.fabs(line_xe_lower - line_xs_lower)
        dy_lower = dx_lower * math.tan(dia_radians)
        if self.up_first == 'yes':
            line_ye_lower = line_ys_lower + dy_lower * dy_factor
        else:
            line_ye_lower = line_ys_lower - dy_lower * dy_factor
        # --本次线段的终点，做为下次线段的起点
        self.line_xe_upper = line_xe_upper
        self.line_ye_upper = line_ye_upper
        self.line_xe_lower = line_xe_lower
        self.line_ye_lower = line_ye_lower
        self.turn_points_upper.append((line_xe_upper, line_ye_upper))
        self.turn_points_lower.append((line_xe_lower, line_ye_lower))
        # --添加左侧斜线1,加上属性，方便后期套开线路周围铜皮
        self.GEN.COM('cur_atr_reset')
        self.GEN.COM('cur_atr_set,attribute=.string,text=loss_line')
        self.GEN.COM('cur_atr_set, attribute =imp_lw_ref_info, text ={0}_{1}_{2}_{3}_{4}_{5}'.format(
            self.org_width,self.org_space, 0,self.ohms, self.refer1, self.refer2
        ))        
        self.GEN.ADD_LINE(line_xs_upper, line_ys_upper, line_xe_upper, line_ye_upper, self.line_sym, attr='yes')
        self.GEN.ADD_LINE(line_xs_lower, line_ys_lower, line_xe_lower, line_ye_lower, self.line_sym, attr='yes')
        self.GEN.COM('cur_atr_reset')
        # --累计长度
        self.upper_length += math.hypot(line_xs_upper - line_xe_upper, line_ys_upper - line_ye_upper)
        self.lower_length += math.hypot(line_xs_lower - line_xe_lower, line_ys_lower - line_ye_lower)
        if not recursion:
            # --递归调用自身一次,添加左侧斜线2
            self.left_dia_line(line_xe_upper, line_ye_upper, line_xe_lower, line_ye_lower, recursion=True)

    def right_dia_line(self, line_xs_upper, line_ys_upper, line_xs_lower, line_ys_lower, recursion=False):
        """
        右侧斜线,10度或-10度均可以
        :return:
        :rtype:
        """
        # --线倾斜角度10度
        dia_radians = self.dia_radians
        # --计算upper线的起始结束点y坐标差值
        if recursion:
            # --递归调用
            dy_upper = self.broken_dy1
        else:
            dy_upper = self.broken_dy2
        # --计算upper线的x坐标
        dx_upper = dy_upper / math.tan(dia_radians)
        if line_ys_upper > self.org_y:
            line_ye_upper = line_ys_upper - dy_upper
        else:
            line_ye_upper = line_ys_upper + dy_upper
        line_xe_upper = line_xs_upper + dx_upper * self.factor

        # --计算lower终点y坐标差值
        if recursion:
            # --最后一折，保证沿org_y方向均分y值
            line_ye_lower = self.line_yd
            dy_lower = math.fabs(line_ys_lower - line_ye_lower)
            dx_lower = dy_lower / math.tan(dia_radians)
            line_xe_lower = line_xs_lower + dx_lower
        else:
            line_xe_lower = line_xe_upper
            dx_lower = math.fabs(line_xe_lower - line_xs_lower)
            dy_lower = dx_lower * math.tan(dia_radians)
            if line_ys_upper > self.org_y:
                line_ye_lower = line_ys_lower - dy_lower
            else:
                line_ye_lower = line_ys_lower + dy_lower
        # --本次线段的终点，做为下次线段的起点
        self.line_xe_upper = line_xe_upper
        self.line_ye_upper = line_ye_upper
        self.line_xe_lower = line_xe_lower
        self.line_ye_lower = line_ye_lower
        # --添加地孔需要的参考坐标列表
        if not recursion:
            self.turn_points_upper.append((line_xe_upper, line_ye_upper))
            self.turn_points_lower.append((line_xe_lower, line_ye_lower))
        # --添加左侧斜线1
        self.GEN.COM('cur_atr_reset')
        self.GEN.COM('cur_atr_set,attribute=.string,text=loss_line')
        self.GEN.COM('cur_atr_set, attribute =imp_lw_ref_info, text ={0}_{1}_{2}_{3}_{4}_{5}'.format(
            self.org_width,self.org_space, 0,self.ohms, self.refer1, self.refer2
        ))        
        self.GEN.ADD_LINE(line_xs_upper, line_ys_upper, line_xe_upper, line_ye_upper, self.line_sym, attr='yes')
        self.GEN.ADD_LINE(line_xs_lower, line_ys_lower, line_xe_lower, line_ye_lower, self.line_sym, attr='yes')
        self.GEN.COM('cur_atr_reset')
        self.upper_length += math.hypot(line_xs_upper - line_xe_upper, line_ys_upper - line_ye_upper)
        self.lower_length += math.hypot(line_xs_lower - line_xe_lower, line_ys_lower - line_ye_lower)
        if not recursion:
            # --递归调用自身一次,添加左侧斜线2
            self.right_dia_line(line_xe_upper, line_ye_upper, line_xe_lower, line_ye_lower, recursion=True)

    def pad_to_line_left(self):
        """
        与pad相连的线
        :return:
        :rtype:
        """
        # --双线中心到中心的一半
        self.half_l2l = half_l2l = (self.line_width + self.line_space) / 2000.0
        self.line_sym = 'r%s' % self.line_width
        # --引出线加补0.8mil
        self.line_sym_ad = 'r%s' % (self.line_width + 0.8)
        self.line_sym_ad = self.line_sym
        self.shave_sym = 'r%s' % self.line_space
        if self.org_layer in outer:
            self.pad_x = self.org_x - 0.0404 * self.factor
            self.pad_yu = self.org_y + 0.00984
            self.pad_yd = self.org_y - 0.00984
            self.line_yu = self.org_y + half_l2l
            self.line_yd = self.org_y - half_l2l
            line_angle = 45
            angle_radians = math.radians(line_angle)
            dy = self.pad_yu - self.line_yu
            self.p2l_dx = dy * math.tan(angle_radians) * self.factor
            self.line_xs_upper = self.pad_x + self.p2l_dx
            self.line_xs_lower = self.pad_x + self.p2l_dx
        else:
            self.pad_x = self.org_x
            self.pad_yu = self.org_y + 0.015
            self.pad_yd = self.org_y - 0.015
            self.line_yu = self.org_y + half_l2l
            self.line_yd = self.org_y - half_l2l
            line_angle = 90 - 25.67
            angle_radians = math.radians(line_angle)
            dy = self.pad_yu - self.line_yu
            self.p2l_dx = dy * math.tan(angle_radians) * self.factor
            self.line_xs_upper = self.pad_x + self.p2l_dx
            self.line_xs_lower = self.pad_x + self.p2l_dx
        self.GEN.CLEAR_LAYER()
        self.GEN.WORK_LAYER(self.layer)
        self.GEN.ADD_LINE(self.pad_x, self.pad_yu, self.line_xs_upper, self.line_yu, self.line_sym_ad)
        self.GEN.ADD_LINE(self.pad_x, self.pad_yd, self.line_xs_lower, self.line_yd, self.line_sym_ad)
        # --加补0.8mil后为了保证间距，用负片削开
        # self.GEN.ADD_LINE(self.pad_x, self.org_y, self.line_xs_lower+0.005, self.org_y, self.shave_sym,pol='negative')
        # --长度累计
        self.p2l_length_upper = math.hypot(self.pad_x - self.line_xs_upper, self.pad_yu - self.line_yu)
        self.p2l_length_lower = math.hypot(self.pad_x - self.line_xs_lower, self.pad_yd - self.line_yd)
        self.upper_length += self.p2l_length_upper
        self.lower_length += self.p2l_length_lower

    def pad_to_line_right(self):
        """
        右侧pad到线
        :return:
        :rtype:
        """
        line_xs_upper = self.line_xe_upper
        line_xs_lower = line_xs_upper
        line_xe_upper = line_xs_upper + self.p2l_dx
        line_xe_lower = line_xe_upper
        self.GEN.CLEAR_LAYER()
        self.GEN.WORK_LAYER(self.layer)
        self.GEN.ADD_LINE(line_xs_upper, self.line_yu, line_xe_upper, self.pad_yu, self.line_sym_ad)
        self.GEN.ADD_LINE(line_xs_lower, self.line_yd, line_xe_lower, self.pad_yd, self.line_sym_ad)
        # --加补0.8mil后为了保证间距，用负片削开
        # self.GEN.ADD_LINE(line_xs_upper-0.005, self.org_y, line_xe_upper, self.org_y, self.shave_sym,pol='negative')
        # --长度累计
        self.p2l_length_upper = math.hypot(line_xs_upper - line_xe_upper, self.line_yu - self.pad_yu)
        self.p2l_length_lower = math.hypot(line_xs_lower - line_xe_lower, self.line_yd - self.pad_yd)
        self.upper_length += self.p2l_length_upper
        self.lower_length += self.p2l_length_lower
        # --本次线段的终点，做为下次线段的起点
        self.line_xe_upper = line_xe_upper
        self.line_xe_lower = line_xe_lower

    def horizon_line_left(self):
        """
        左侧水平线
        :return:
        :rtype:
        """
        # --10度的线，先用math.radians将角度转换为弧度,再用math.tan计算正切值,参考模型
        dia_radians = math.radians(10)
        dx_compensate = self.half_l2l * math.tan(dia_radians)
        if self.up_first == 'yes':
            self.line_xe_upper = self.org_x + 0.06 * self.factor
            self.line_xe_lower = self.org_x + (0.06 + dx_compensate) * self.factor
        else:
            self.line_xe_upper = self.org_x + (0.06 + dx_compensate) * self.factor
            self.line_xe_lower = self.org_x + 0.06 * self.factor
        self.GEN.CLEAR_LAYER()
        self.GEN.WORK_LAYER(self.layer)
        self.GEN.COM('cur_atr_reset')
        self.GEN.COM('cur_atr_set,attribute=.string,text=loss_line')
        self.GEN.COM('cur_atr_set, attribute =imp_lw_ref_info, text ={0}_{1}_{2}_{3}_{4}_{5}'.format(
            self.org_width,self.org_space, 0,self.ohms, self.refer1, self.refer2
        ))        
        self.GEN.ADD_LINE(self.line_xs_upper, self.line_yu, self.line_xe_upper, self.line_yu, self.line_sym, attr='yes')
        self.GEN.ADD_LINE(self.line_xs_lower, self.line_yd, self.line_xe_lower, self.line_yd, self.line_sym, attr='yes')
        self.GEN.COM('cur_atr_reset')
        # --长度累计
        self.horizon_length_upper = math.hypot(self.line_xs_upper - self.line_xe_upper, self.line_yu - self.line_yu)
        self.horizon_length_lower = math.hypot(self.line_xs_lower - self.line_xe_lower, self.line_yd - self.line_yd)
        self.upper_length += self.horizon_length_upper
        self.lower_length += self.horizon_length_lower

    def horizon_line_right(self):
        """
        右侧水平线
        :return:
        :rtype:
        """
        line_xs_upper = self.line_xe_upper
        line_xs_lower = self.line_xe_lower
        dx_upper = self.line_lenth - self.upper_length - self.p2l_length_upper
        line_xe_upper = line_xs_upper + dx_upper
        line_xe_lower = line_xe_upper
        self.GEN.CLEAR_LAYER()
        self.GEN.WORK_LAYER(self.layer)
        self.GEN.COM('cur_atr_reset')
        self.GEN.COM('cur_atr_set,attribute=.string,text=loss_line')
        self.GEN.COM('cur_atr_set, attribute =imp_lw_ref_info, text ={0}_{1}_{2}_{3}_{4}_{5}'.format(
            self.org_width,self.org_space, 0,self.ohms, self.refer1, self.refer2
        ))        
        self.GEN.ADD_LINE(line_xs_upper, self.line_yu, line_xe_upper, self.line_yu, self.line_sym, attr='yes')
        self.GEN.ADD_LINE(line_xs_lower, self.line_yd, line_xe_lower, self.line_yd, self.line_sym, attr='yes')
        self.GEN.COM('cur_atr_reset')
        # --长度累计
        self.horizon_length_upper = math.hypot(line_xs_upper - line_xe_upper, self.line_yu - self.line_yu)
        self.horizon_length_lower = math.hypot(line_xs_lower - line_xe_lower, self.line_yd - self.line_yd)
        self.upper_length += self.horizon_length_upper
        self.lower_length += self.horizon_length_lower
        # --本次线段的终点，做为下次线段的起点
        self.line_xe_upper = line_xe_upper
        self.line_ye_upper = self.line_yu
        self.line_xe_lower = line_xe_lower
        self.line_ye_lower = self.line_yd


class Loss(object):
    """
    主类
    """

    def __init__(self, job_name=None, step_name=None, json_data=None):
        self.JOB = job_name
        self.STEP = step_name
        self.parm = FrozenJSON(json.loads(json_data, encoding='utf8'))
        self.GEN = genCOM.GEN_COM()
        self.pid = os.getpid()
        self.layer_number = int(self.JOB[4:6])

    def run(self):
        """
        所以分板函数归集
        :return:
        :rtype:
        """
        # --更新指定symbol（以免造成旧symbol未更新）
        self.updateSymbols()

        # --获取loss走线、参考层
        self.loss_layer, self.loss_refer = self.get_layer_and_refer()
        # --创建step
        self.create_loss()
        # --外型层w、ww
        self.ww_outline()
        # --铺铜
        self.fill_copper()
        # --定位孔坐标列表
        self.dw_xy_left = []
        self.dw_xy_right = []
        # --各层mark列表
        self.mark_top = []
        self.mark_bot = []
        # --标识起点x坐标列表
        self.mark_top_x = []
        self.mark_bot_x = []
        # --标识起点y坐标列表
        self.mark_top_y = []
        self.mark_bot_y = []
        # --既是走线，又是参考层列表
        self.fill_refer_list = []
        # --原始点坐标初始化
        org_x = 0.1205 + 0.19
        org_y = 0.1205 + 0.05
        for count, layDict in enumerate(self.parm.impList):
            layer = layDict.layer
            # --定义左侧定位孔坐标
            if len(self.dw_xy_left) == 0:
                # --定位孔中心距左侧profile 0.107486,保证距1.15的NP孔0.1mm
                self.dw_xy_left.append((org_x - 0.19 - 0.013014, org_y))
                # --相应的org_x向右侧偏移
                org_x += 0.086986
            else:
                # --其它层重置org_x，保证左侧对齐
                org_x = 0.1205 + 0.19

            if count == 0:
                pre_layer = None
                if layer in self.parm.adjacent_layer:
                    org_y += 0.01
            else:
                pre_layer = self.parm.impList[count - 1].layer
            if count == len(self.parm.impList) - 1:
                next_layer = None
            else:
                next_layer = self.parm.impList[count + 1].layer

            line_width = layDict.line_width
            line_space = layDict.line_space
            org_width = layDict.org_width
            org_space = layDict.org_space
            ohms = layDict.ohms
            compensate = layDict.compensate
            refer1 = layDict.refer1
            refer2 = layDict.refer2
            # --实际添加loss的函数
            # self.GEN.PAUSE("aaaaaaaaaaaaa1")
            self.loss_process(org_x, org_y, layer, refer1, refer2, line_width, line_space, org_width, org_space, ohms,
                count)
            # self.GEN.PAUSE("aaaaaaaaaaaaa2")
            # --每个loss y方向错开0.2inch
            org_y += 0.2
            # --考虑多个外层走线的情况,org_y作修正
            if layer == next_layer:
                # --同一层两个走线时,多偏移0.15
                org_y += 0.15
            elif layer == outer[0] and next_layer == outer[1]:
                # --外层top面，紧接着是外层bot面，两者之间差开+0.15inch,很常见的一种情况
                org_y += 0.15
                pass
            elif layer in self.parm.adjacent_layer:
                if next_layer is None:
                    # --层别本身为相邻走线层，但是为最后一层，只需要多加0.05inch
                    org_y += 0.05
                else:
                    # --层别本身为相邻走线层，需要多加0.1inch
                    org_y += 0.1
            elif next_layer in self.parm.adjacent_layer:
                # --下一层为相邻走线层，需要多加0.1inch
                org_y += 0.1
        # self.GEN.PAUSE("XXXXXXXXXX1")
        # --D+160套外层走线
        self.clean_outer()
        # self.GEN.PAUSE("XXXXXXXXXX2")
        # --既是走线，又是参考层，将铜皮反到最底层
        self.move_refer_copper()
        # self.GEN.PAUSE("XXXXXXXXXX3")
        # --外层统一添加阻抗标识
        mark_out = outer_mark(mark_top=self.mark_top, mark_top_x=self.mark_top_x, mark_top_y=self.mark_top_y,
            mark_bot=self.mark_bot, mark_bot_x=self.mark_bot_x, mark_bot_y=self.mark_bot_y,
            loss_layer=self.loss_layer)
        mark_out.add_mark_top()
        mark_out.add_mark_bot()
        # --添加定位孔
        dw_hole = Ding_wei_hole(dw_xy_left=self.dw_xy_left, dw_xy_right=self.dw_xy_right)
        dw_hole.all_process()
        # --添加伴随接地孔
        self.add_tilt_via_pad()
        # --内层走线层铺dummy
        self.fill_dummy()
        
        #镭射测试孔优化 暂时屏蔽 
        self.opt_laser_test_holes(self.STEP, self.parm.impList)
        
    def opt_laser_test_holes(self, stepname, arraylist_imp_info):
        """优化镭射测试孔"""
        self.small_hole_list = self.parm.Alldrill_small_hole
        if not laser_drill_layers:
            return        
        step = gClasses.Step(job, 'loss')
        step.open()
        step.COM("units,type=mm")
        exist_add_laser_hole_layers = []
        for dic_imp in arraylist_imp_info:
            worklayer = dic_imp.layer
            if worklayer in outsignalLayers:
                # 外层loss 按通孔来导通测试
                continue
            
            if worklayer in exist_add_laser_hole_layers:
                continue
            
            exist_add_laser_hole_layers.append(worklayer)            
            
            step.clearAll()
            step.affect(worklayer)
            step.removeLayer(worklayer+"_testpoint_tmp")
            step.resetFilter()
            step.filter_set(feat_types='pad', polarity='positive')
            step.setAttrFilter(".string,text=test_point")
            step.selectAll()
            if step.featureSelected():
                step.copySel(worklayer+"_testpoint_tmp")
                
            worklayer_index = signalLayers.index(worklayer)
            step.clearAll()
            step.affect("drl")
            step.resetFilter()
            step.refSelectFilter(worklayer+"_testpoint_tmp", mode="cover")
            if step.featureSelected():                
                step.copySel(worklayer+"_testpoint")
            
            step.removeLayer(worklayer+"_testpoint_tmp")
            step.clearAll()
            step.affect(worklayer+"_testpoint")
            
            arraylist_laser_start_layers = []
            arraylist_laser_end_layers = []
            
            for i, layer in enumerate(signalLayers):
                is_continue = False
                if worklayer_index + 1 <= lay_num * 0.5:
                    flag = 1
                    if i > worklayer_index:
                        is_continue = True
                else:
                    flag = -1
                    if i < worklayer_index:
                        is_continue = True
                
                # 内层线路对应靠内的一层线路测点位置套开
                #if i == index + flag * 1:
                    #step.copyToLayer(layer, invert="yes", size=20*25.4)
                        
                if is_continue:
                    continue
                
                # 先加一个负片
                if layer not in [worklayer] + outsignalLayers:
                    step.copyToLayer(layer, invert="yes", size=20*25.4)
                    
                if layer == worklayer:
                    continue                
                
                for j in range(1, 5):
                    laser_drill = "s{0}-{1}".format(i+1, i+1+flag*j)
                    
                    if i+1+flag*j == worklayer_index + 1 + flag:
                        # 已经超过工作层的镭射不要加孔
                        break
                    
                    # 有1to3 1to4的优先用
                    for m in range(1, 5):                        
                        laser_drill_skipvia = "s{0}-{1}".format(i+1, i+1+flag*(j+m))
                        
                        if i+1+flag*(j+m) == worklayer_index + 1 + flag:
                            # 已经超过工作层的镭射不要加孔
                            break
                        
                        if laser_drill_skipvia in laser_drill_layers\
                           and ((flag == 1 and i+1+flag*(j+m) <= worklayer_index + 1) or \
                           (flag == -1 and i+1+flag*(j+m) >= worklayer_index + 1)):                            
                            laser_drill = laser_drill_skipvia[::]
                        
                    if laser_drill in laser_drill_layers:
                        arraylist_laser_start_layers.append("l"+laser_drill.split("-")[0][1:])
                        arraylist_laser_end_layers.append("l"+laser_drill.split("-")[1])
                        
                        hole_size = self.get_min_hole_size_from_dict(laser_drill)
                        step.changeSymbol("r{0}".format(hole_size))
                        step.copySel(laser_drill)
                        step.copyToLayer(layer, size=5*2*25.4)                        
               
                    #if "-lyh" in job.name:
                        #step.PAUSE(str([worklayer, layer, laser_drill, worklayer_index, i, is_continue, lay_num]))
                        
            if mai_drill_layers:
                for drill_layer in mai_drill_layers:
                    layer1, layer2 = get_drill_start_end_layers(matrixInfo, drill_layer)
                    index1 = signalLayers.index(layer1)
                    index2 = signalLayers.index(layer2)                    
                    if min([index1, index2])< worklayer_index < max([index1, index2]):
                        
                        if worklayer_index <= lay_num * 0.5:
                            if layer1 in arraylist_laser_start_layers and worklayer in arraylist_laser_end_layers:
                                # 说明有镭射直接导通到信号层 埋孔层不加孔
                                break
                        else:
                            if layer2 in arraylist_laser_start_layers and worklayer in arraylist_laser_end_layers:
                                # 说明有镭射直接导通到信号层 埋孔层不加孔
                                break
                    
                        step.copyToLayer(layer1, invert="yes", size=20*25.4)
                        step.copyToLayer(layer2, invert="yes", size=20*25.4)
                        hole_size = self.get_min_hole_size_from_dict(drill_layer)
                        step.changeSymbol("r{0}".format(hole_size))
                        step.copySel(drill_layer)
                        step.copyToLayer(layer1, size=5*2*25.4)
                        step.copyToLayer(layer2, size=5*2*25.4)
                    
            step.clearAll()            
            step.affect("drl")
            step.resetFilter()
            step.refSelectFilter(worklayer+"_testpoint")
            if step.featureSelected():
                step.selectDelete()
                
            step.removeLayer(worklayer+"_testpoint")
        
        step.COM("units,type=inch")
    
    def get_min_hole_size_from_dict(self, drill_layer):
        """获取界面上的最小孔径"""
        for info in self.small_hole_list:
            if info[0] == drill_layer:
                return info[1]
        else:
            # showMessageInfo(u"层名{0} 最小孔径不存在，请检查层名跟界面列表内的命名是否一致！".format(drill_layer))
            msgBox().critical(None, u"错误", u"层名{0} 最小孔径不存在，请检查层名跟界面列表内的命名是否一致！".format(drill_layer), QMessageBox.Ok)
            sys.exit(1)    

    def updateSymbols(self):
        """
        更新项目中所用到的symbol
        :return: None
        """
        runEnv = self.GEN.getEnv()
        # allSymbols = self.GEN.DO_INFO("-t job -e %s -d SYMBOLS_LIST" % self.JOB)
        # print (allSymbols)
        for upSymbol in ('loss_hole_pg', 'loss_hole_pg_cu', 'loss_stub_outer_v4', 'loss_sm_small_v4'):
            # --当料号中不存在时，选择不更新
            info = self.GEN.DO_INFO('-t symbol -e %s/%s -m script -d EXISTS' % (self.JOB, upSymbol))
            if info['gEXISTS'] == 'no':
                continue
            # --根据不同环境调用不同方法更新对应的symbol
            if runEnv['software'] == 'genesis':
                self.GEN.COM('copy_entity,type=symbol,source_job=genesislib,source_name=%s,dest_job=%s,'
                             'dest_name=%s,dest_database=' % (upSymbol, self.JOB, upSymbol))
            else:
                self.GEN.COM('import_lib_item_to_job,src_category=symbols,src_profile=system,src_customer=,'
                             'dst_names=%s' % upSymbol)


    def get_layer_and_refer(self):
        """
        获取走线层和参考层
        :return:两个列表
        :rtype:
        """
        loss_layer = []
        loss_refer = []
        self.loss_top = []
        self.loss_bot = []
        self.loss_inn = []
        imp_List = self.parm.impList        
        for layDict in imp_List:
            layer = layDict.layer
            if layer not in loss_layer:
                loss_layer.append(layer)
            refer1 = layDict.refer1
            if refer1 not in loss_refer:
                loss_refer.append(refer1)
            refer2 = layDict.refer2
            if refer2 not in ['None'] and refer2 not in loss_refer:
                loss_refer.append(refer2)
        # --返回loss走线层、参考层
        return loss_layer, loss_refer

    def create_loss(self):
        """
        创建loss step
        :return:
        :rtype:
        """
        loss_type = self.parm.loss_type
        imp_List = self.parm.impList
        loss_place = self.parm.loss_place
        adjacent_layer = self.parm.adjacent_layer
        loss_factor = 1
        if loss_type == 'std_type':
            if loss_place == u'品字形':
                self.width = 0.1205 * 4 + 0.2 * len(imp_List) + 0.2 * (len(imp_List) - 1)
                self.lenth = 10.22578 + 0.1205 * 2
                loss_factor = 2
            else:
                self.width = 0.1205 * 2 + 0.1 * len(imp_List) + 0.1 * (len(imp_List) - 1)
                self.lenth = 18.174159 + 0.1205 * 2
        else:
            # --孔到孔0.1inch,相邻间距也是0.1
            self.width = 0.1205 * 2 + 0.1 * len(imp_List) + 0.1 * (len(imp_List) - 1)
            self.lenth = 9.025

        info = self.GEN.DO_INFO('-t step -e %s/loss -d EXISTS' % self.JOB)
        if info['gEXISTS'] == "yes":
            # --如果loss存在时，删除现有loss并重新生成
            self.GEN.DELETE_ENTITY('step', 'loss', job=self.JOB)
        self.GEN.COM('create_entity,job=%s,is_fw=no,type=step,name=loss,db=,fw_type=form' % self.JOB)
        self.GEN.OPEN_STEP('loss', job=self.JOB)
        self.GEN.COM('units,type=inch')
        # --定义全局变量，内外层
        global outer
        global inner
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=top|bottom)')
        self.GEN.COM('get_affect_layer')
        outer = self.GEN.COMANS.split()
        self.GEN.COM('affected_filter,filter=(type=signal&context=board&side=inner)')
        self.GEN.COM('get_affect_layer')
        inner = self.GEN.COMANS.split()
        self.GEN.CLEAR_LAYER()
        # --获取loss列表,外层top,外层bot,内层,并计算profile高度
        for count, layDict in enumerate(imp_List):
            layer = layDict.layer
            try:
                next_layer = imp_List[count + 1].layer
                # print "layer",layer
                # print "next_layer",next_layer
                # self.GEN.PAUSE("check")
            except IndexError:
                next_layer = None
            if layer == outer[0]:
                self.loss_top.append(layer)
                if next_layer == outer[1]:
                    # --外层top面，紧接着是外层bot面，两者之间差开+0.15inch,很常见的一种情况
                    self.width += 0.15 * loss_factor
                    pass
            if layer == outer[1]:
                self.loss_bot.append(layer)
            if layer not in outer:
                self.loss_inn.append(layer)
            if next_layer is not None:
                if next_layer == layer:
                    # --当前层连续两个走线,按ohms排序后，这种情况不多见
                    self.width += 0.15 * loss_factor
                elif next_layer in adjacent_layer:
                    # --下一层为相邻走线层，需要多加0.1inch
                    self.width += 0.1 * loss_factor
                elif layer in adjacent_layer:
                    # --层别本身为相邻走线层，需要多加0.1inch
                    self.width += 0.1 * loss_factor
                    if count == 0:
                        # --第一个层为相邻层，org_y要上移0.01inch
                        self.width += 0.01 * loss_factor
            else:
                if layer in outer and count == 0:
                    # --只有外层一层走线，需要加多0.15inch,否则mark没地方添加
                    self.width += 0.15 * loss_factor
                if layer in adjacent_layer:
                    # --层别本身为相邻走线层，且为最后一个走线层，需要多加0.01inch
                    self.width += 0.01 * loss_factor

        if self.loss_layer[-1] != outer[1]:
            # --bot面走线不是最后一组,右侧添加定位孔，会超出原来的长度，需要修正
            self.lenth += 0.086986
        if self.loss_layer[0] != outer[0]:
            # --top面走线不是第一组,左侧添加定位孔，会超出原来的长度，需要修正
            self.lenth += 0.086986

        self.GEN.COM('profile_rect,x1=0,y1=0,x2=%s,y2=%s' % (self.lenth, self.width))
        self.GEN.COM('zoom_home')
        # self.GEN.PAUSE('X')

    def ww_outline(self):
        """
        w及ww层
        :return:
        :rtype:
        """
        self.GEN.COM('profile_to_rout,layer=w,width=4')
        self.GEN.COM('profile_to_rout,layer=ww,width=4')

    def fill_copper(self):
        """
        没有走线的层别，进行铺铜
        :return:
        :rtype:
        """
        # --铺铜距profile 20mil
        self.GEN.CLEAR_LAYER()
        for layer in outer + inner:
            if layer not in self.loss_layer:
                self.GEN.AFFECTED_LAYER(layer, 'yes')
            if layer in outer:
                self.GEN.AFFECTED_LAYER(layer, 'yes')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            self.GEN.COM('fill_params,type=solid,origin_type=datum,solid_type=surface')
            self.GEN.COM('sr_fill,polarity=positive,step_margin_x=0.02,step_margin_y=0.02,step_max_dist_x=100,'
                         'step_max_dist_y=100,sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=yes,'
                         'stop_at_steps=,consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,'
                         'attributes=no')
        self.GEN.CLEAR_LAYER()

    def fill_dummy(self):
        """
        走线层铺dummy
        :return:
        :rtype:
        """
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('chklist_single,action=valor_dfm_balance,show=yes')
        # --由铺铜pad的改为铺铜皮(并接地)
        # fillType = 'Circle'
        fillType = 'Solid'
        for layer in self.loss_layer:

            mask_layer = '%s_mask' % layer
            self.GEN.AFFECTED_LAYER(layer, 'yes')
            # --查看外层是否有走线
            self.GEN.FILTER_TEXT_ATTR('.string', 'loss_line', reset=1)
            self.GEN.FILTER_SET_POL('negative')
            self.GEN.FILTER_SELECT()
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                # --相邻层相互避开的负极性的线
                self.GEN.SEL_COPY(mask_layer, invert='yes')
                self.GEN.COM(
                    'chklist_cupd,chklist=valor_dfm_balance,nact=1,params=((pp_layer=.affected)(pp_size=30)(pp_pitch=40)'
                    '(pp_shape_type=%s)(pp_drill_spacing=20)(pp_feature_spacing=50)(pp_rout_spacing=30)'
                    '(pp_prof_spacing=10)(pp_fiducial_spacing=50)(pp_mask_layer=%s)(pp_shape_name=)(pp_pitch_x=10)'
                    '(pp_pitch_y=10)(pp_min_f_num=0)(pp_min_area_value=3000)(pp_bottleneck_value=20)),mode=regular' % (
                        fillType, mask_layer))
                self.GEN.COM('chklist_run,chklist=valor_dfm_balance,nact=1,area=profile')
                self.GEN.DELETE_LAYER(mask_layer)
            else:
                # self.GEN.COM('chklist_cupd,chklist=valor_dfm_balance,nact=1,params=((pp_layer=.affected)(pp_size=30)(pp_pitch=40)'
                #     '(pp_shape_type=%s)(pp_drill_spacing=20)(pp_feature_spacing=50)(pp_rout_spacing=30)'
                #     '(pp_prof_spacing=10)(pp_fiducial_spacing=50)(pp_mask_layer=)(pp_shape_name=)(pp_pitch_x=10)'
                #     '(pp_pitch_y=10)(pp_min_f_num=0)(pp_min_area_value=3000)(pp_bottleneck_value=20)),mode=regular' % fillType)
                # self.GEN.COM('chklist_run,chklist=valor_dfm_balance,nact=1,area=profile')
                # --用线去套开
                tmpLayer = '_+_tmp_+_'
                self.GEN.DELETE_LAYER(tmpLayer)
                self.GEN.SEL_COPY(tmpLayer)
                # --填充当前层
                self.GEN.FILL_SUR_PARAMS()
                self.GEN.SR_FILL('positive', 0.02, 0.02, 100, 100)
                self.GEN.AFFECTED_LAYER(layer, 'no')
                self.GEN.AFFECTED_LAYER(tmpLayer, 'yes')
                # --选择正片拷贝过去
                self.GEN.FILTER_SET_POL('positive', reset=1)
                self.GEN.FILTER_SELECT()
                if self.GEN.GET_SELECT_COUNT() > 0:
                    self.GEN.SEL_COPY(layer, invert='yes', size=160)
                self.GEN.SEL_MOVE(layer)

            # self.GEN.PAUSE("Layer:%s" % layer)
            self.GEN.AFFECTED_LAYER(layer, 'no')
        self.GEN.COM('chklist_close,chklist=valor_dfm_balance,mode=hide')
        self.GEN.CLEAR_LAYER()

    def add_Teardrops(self):
        """
        添加泪滴
        :return:
        :rtype:
        """
        self.GEN.CLEAR_LAYER()
        for layer in self.loss_layer:
            self.GEN.AFFECTED_LAYER(layer, 'yes')
        if outer[0] not in self.loss_layer:
            self.GEN.AFFECTED_LAYER(outer[0], 'yes')
        if outer[1] not in self.loss_layer:
            self.GEN.AFFECTED_LAYER(outer[1], 'yes')
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) > 0:
            if self.GEN.getEnv()['software'] == 'genesis':
                self.GEN.COM('chklist_single,action=frontline_dfm_tear_drop,show=no')
                self.GEN.COM(
                    'chklist_cupd,chklist=frontline_dfm_tear_drop,nact=1,params=((pp_layer=.affected)(pp_type=Straight)'
                    '(pp_target=Drilled Pads\;Undrilled Pads)(pp_ar=10)(pp_min_hole=0)(pp_max_hole=80)(pp_spacing=5)'
                    '(pp_hole_spacing=11)(pp_del_old=Yes)(pp_selected=All)(pp_work_mode=Repair)),mode=regular')
                self.GEN.COM('chklist_run,chklist=frontline_dfm_tear_drop,nact=1,area=profile')
                self.GEN.COM('chklist_close,chklist=frontline_dfm_tear_drop,mode=hide')
            else:
                # --incam和incampro环境添加弧形泪滴
                self.GEN.COM('chklist_single,show=no,action=frontline_dfm_tear_drop')
                self.GEN.COM('top_tab,tab=Checklists')
                self.GEN.COM('chklist_erf,chklist=frontline_dfm_tear_drop,nact=1,erf=arc')
                self.GEN.COM('chklist_cupd,chklist=frontline_dfm_tear_drop,nact=1,params=((pp_layer=.affected)'
                             '(pp_type=Arc by Radius)(pp_target=Drilled Pads\;Undrilled Pads)(pp_radius_of_arc=14)'
                             '(pp_radius_of_arc_min=2)(pp_ar=12)(pp_min_hole=0)(pp_max_hole=120)(pp_spacing=4)'
                             '(pp_hole_spacing=8)(pp_del_old=Yes)(pp_selected=All)(pp_work_mode=Repair)'
                             '(pp_handle_pads_drilled_by=PTH\;Via\;LASER-Via)),mode=regular')
                self.GEN.COM('chklist_cnf_act,chklist=frontline_dfm_tear_drop,nact=1,cnf=no')
                self.GEN.COM('chklist_set_hdr,chklist=frontline_dfm_tear_drop,save_res=no,stop_on_err=no,run=activated,'
                             'area=global,mask=None,mask_usage=include')
                self.GEN.COM('chklist_run,chklist=frontline_dfm_tear_drop,nact=1,area=global,async_run=yes')
        self.GEN.CLEAR_LAYER()

    def add_tilt_via_pad(self):
        """
        伴随接地孔补外层pad
        :return:
        :rtype:
        """
        # --存在两种接地孔 .string=tilt_via & .bit=loss_hole_pg
        for string, value in (['.string', 'tilt_via'], ['.bit', 'loss_hole_pg'], ['.bit', 'loss_hole_pg_cu']):
            self.GEN.CLEAR_LAYER()
            self.GEN.WORK_LAYER('drl')
            self.GEN.FILTER_TEXT_ATTR(string, value, reset=1)
            self.GEN.FILTER_SELECT()
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                for layer in outer:
                    self.GEN.AFFECTED_LAYER(layer, 'yes')
                # --D+8mil copy到外层
                self.GEN.COM('sel_copy_other,dest=affected_layers,target_layer=,invert=no,dx=0,dy=0,size=8,'
                             'x_anchor=0,y_anchor=0,rotation=0,mirror=none')
                self.GEN.COM('affected_layer,mode=all,affected=no')
            self.GEN.FILTER_SELECT()
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                # --D+6mil copy到lp层
                self.GEN.SEL_COPY('lp', size=6)

            self.GEN.FILTER_RESET()
            self.GEN.CLEAR_LAYER()

    def move_refer_copper(self):
        """
        将既是参考层又是走线层的铜皮反到最底层
        :return:
        :rtype:
        """
        for layer in self.fill_refer_list:
            tmp_layer = '%s_tmp' % layer
            self.GEN.AFFECTED_LAYER(layer, 'yes')
            # --查看外层是否有走线
            self.GEN.FILTER_TEXT_ATTR('.string', 'loss_copper', reset=1)
            self.GEN.FILTER_SELECT()
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                self.GEN.SEL_MOVE(tmp_layer)
                # --将其它物件copy到tmp_layer
                self.GEN.FILTER_RESET()
                self.GEN.FILTER_SELECT()
                count = self.GEN.GET_SELECT_COUNT()
                if count > 0:
                    self.GEN.SEL_COPY(tmp_layer)
                # --用tmp_layer替换layer
                self.GEN.COPY_LAYER(self.JOB, 'loss', tmp_layer, layer, mode='replace')
            else:
                self.GEN.FILTER_RESET()
            self.GEN.DELETE_LAYER(tmp_layer)
            self.GEN.FILTER_RESET()
            self.GEN.AFFECTED_LAYER(layer, 'no')

    def clean_outer(self):
        """
        外层走线用D+160净空
        :return:
        :rtype:
        """
        self.GEN.CLEAR_LAYER()
        for layer in outer:
            tmp_layer = '%s_tmp' % layer
            self.GEN.AFFECTED_LAYER(layer, 'yes')
            # --查看外层是否有走线
            self.GEN.FILTER_TEXT_ATTR('.string', 'loss_line', reset=1)
            self.GEN.FILTER_SELECT()
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                # --外层有走线才需要D+160套开线
                self.GEN.CLEAR_FEAT()
                # --将surface move到tmp_layer
                self.GEN.FILTER_SET_TYP('surface', reset=1)
                self.GEN.FILTER_SELECT()
                # --加上anti pad净空
                self.GEN.FILTER_TEXT_ATTR('.string', 'loss_anti', reset=1)
                self.GEN.FILTER_SELECT()
                count = self.GEN.GET_SELECT_COUNT()
                if count > 0:
                    self.GEN.SEL_MOVE(tmp_layer)
                    # --将.string=loss_line属性的线D+160copy到tmp_layer
                    self.GEN.FILTER_TEXT_ATTR('.string', 'loss_line', reset=1)
                    self.GEN.FILTER_SELECT()
                    count = self.GEN.GET_SELECT_COUNT()
                    if count > 0:
                        self.GEN.SEL_COPY(tmp_layer, invert='yes', size=160)
                    # --将其它物件copy到tmp_layer
                    self.GEN.FILTER_RESET()
                    self.GEN.FILTER_SELECT()
                    count = self.GEN.GET_SELECT_COUNT()
                    if count > 0:
                        self.GEN.SEL_COPY(tmp_layer)
                    # --用tmp_layer替换layer
                    self.GEN.COPY_LAYER(self.JOB, 'loss', tmp_layer, layer, mode='replace')
                else:
                    self.GEN.FILTER_RESET()
            self.GEN.DELETE_LAYER(tmp_layer)
            self.GEN.AFFECTED_LAYER(layer, 'no')

    def fill_copper_refer(self, layer, org_x, right_org_x, org_y, refer1, refer2):
        """
        既是参考层又是走线层,参考料号b13*063a1
        :return:
        :rtype:
        """
        return
    
        surface_xmin = org_x - 0.19 - 0.08
        surface_xmax = right_org_x + 0.19 + 0.08
        surface_ymin = org_y - 0.16
        surface_ymax = org_y + 0.16
        for refer in [refer1, refer2]:
            if refer != 'None' and refer in self.loss_layer:
                self.GEN.WORK_LAYER(refer)
                self.GEN.COM('cur_atr_reset')
                self.GEN.COM('cur_atr_set,attribute=.string,text=loss_copper,option=')
                self.GEN.COM('add_surf_strt,surf_type=feature')
                self.GEN.COM('add_surf_poly_strt,x=%s,y=%s' % (surface_xmin, surface_ymin))
                self.GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (surface_xmin, surface_ymax))
                self.GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (surface_xmax, surface_ymax))
                self.GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (surface_xmax, surface_ymin))
                self.GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (surface_xmin, surface_ymin))
                self.GEN.COM('add_surf_poly_end')
                self.GEN.COM('add_surf_end,attributes=yes,polarity=positive')
                self.GEN.COM('cur_atr_reset')
                if refer not in self.fill_refer_list:
                    self.fill_refer_list.append(refer)
        self.GEN.CLEAR_LAYER()

    def clear_refer(self, layer, line_layer, refer1, refer2):
        """
        穿透的参考层用D+160净空，参考b13/092 l4-2-5
        :return:
        :rtype:
        """
        # --在参考层最小最大值中间的都需要套开
        refer_min, refer_max = self.get_clean_refer(layer, refer1, refer2)
        self.GEN.CLEAR_LAYER()
        self.GEN.WORK_LAYER(line_layer)
        # --查看是否有走线
        self.GEN.FILTER_TEXT_ATTR('.string', 'loss_line', reset=1)
        self.GEN.FILTER_SELECT()
        count = self.GEN.GET_SELECT_COUNT()
        if count > 0:
            for _layer in outer + inner:
                layer_id = int(_layer[1:])
                if layer_id > refer_min and layer_id < refer_max and _layer != layer:
                    self.GEN.SEL_COPY(_layer, invert='yes', size=150)

    def get_clean_refer(self, layer, refer1, refer2):
        """
        获取最小参考层和最大参考层
        :return:
        :rtype:
        """
        layer_id = int(layer[1:])
        refer1_id = int(refer1[1:])

        # --计算参考层最大最小值
        if refer2 == 'None':
            if layer == outer[0]:
                refer_min = layer_id
                refer_max = refer1_id
            elif layer == outer[1]:
                refer_min = refer1_id
                refer_max = layer_id
            else:
                refer_min = refer_max = refer1_id
        else:
            refer2_id = int(refer2[1:])
            refer_min = min(refer1_id, refer2_id)
            refer_max = max(refer1_id, refer2_id)
        return refer_min, refer_max

    def loss_process(self, org_x, org_y, layer, refer1, refer2, line_width, line_space, org_width, org_space, ohms,
                     count):
        """
        每个loss，执行一次本函数
        :return:
        :rtype:
        """
        # --获取下一个走线层名
        if count == 0:
            pre_layer = None
        else:
            pre_layer = self.parm.impList[count - 1].layer
        if count == len(self.parm.impList) - 1:
            next_layer = None
        else:
            next_layer = self.parm.impList[count + 1].layer
        adjacent_layer = self.parm.adjacent_layer
        # --左侧原点坐标，品字形排列时重置坐标用到
        org_x_left = org_x
        org_y_left = org_y
        # --绕线在单独的临时层别中，完成后再copy到原来的层别
        line_layer = '%s_line' % layer
        info = self.GEN.DO_INFO('-t layer -e %s/loss/%s -d EXISTS' % (self.JOB, line_layer))
        if info['gEXISTS'] == "no":
            self.GEN.COM('create_layer,layer=%s,context=misc,type=signal,polarity=positive,ins_layer=' % line_layer)

        # --如果有背钻，stub就近，反之就远
        bd_info = self.parm.bd_info
        is_back_drill = self.parm.is_back_drill
        layer_id = int(layer[1:])
        bd_layer = None
        bd_layer_top = None
        bd_layer_bot = None
        # --计算背钻之间的跨度,C面S面同时有背钻时，取跨度大的背钻
        bd_span = None
        bd_span_top = None
        bd_span_bot = None
        stub_side = None

        # --计算需要添加孔的背钻层
        bdRegex = re.compile(r'bd([1-9][0-9]?)-([1-9][0-9]?)')
        # for layDict in bd_info:
        #     _layer = layDict.layer
        #     print ("SS:%s\n" % _layer)
        # self.GEN.PAUSE('XXXXXXXXX')
        for layDict in bd_info:
            _layer = layDict.layer
            info = self.GEN.DO_INFO('-t layer -e %s/loss/%s -d EXISTS' % (self.JOB, _layer))
            if bdRegex.match(_layer) and info['gEXISTS'] == "yes":
                match_Obj = bdRegex.match(_layer).groups()
                # --TODO 这里需要判断InPlan里面的数据是否一致；
                index_start = layDict.index_start
                if index_start == 1:
                    bd_to = 'l%s' % (int(match_Obj[-1]) + 1)
                    bd_thr = 'l%s' % (int(match_Obj[-1]))
                    if layer == bd_to or layer == bd_thr:
                        bd_span_now = int(match_Obj[-1]) - int(match_Obj[0])
                        if bd_span_bot is None:
                            bd_layer_bot = _layer
                            stub_side = 'bottom'
                            # --重置跨度
                            bd_span_bot = bd_span_now
                        else:
                            if bd_span_now > bd_span_bot:
                                bd_layer_bot = _layer
                                stub_side = 'bottom'
                                # --重置跨度
                                bd_span_bot = bd_span_now
                else:
                    bd_to = 'l%s' % (int(match_Obj[-1]) - 1)
                    bd_thr = 'l%s' % (int(match_Obj[-1]))
                    if layer == bd_to or layer == bd_thr:
                        bd_span_now = int(match_Obj[0]) - int(match_Obj[-1])
                        if bd_span_top is None:
                            bd_layer_top = _layer
                            stub_side = 'top'
                            # --重置跨度
                            bd_span_top = bd_span_now
                        else:
                            if bd_span_now > bd_span_top:
                                bd_layer_top = _layer
                                stub_side = 'top'
                                # --重置跨度
                                bd_span_top = bd_span_now

        # --当未从背钻中获取到stub中，或不存在背钻时,按距离此层更远的底层做测试点
        # hdi按 最小Stub及最小长度 也就是就近原则 20240816 by lyh
        if stub_side is None:
            # --按远的stub值
            if laser_drill_layers:
                if layer_id > self.layer_number/2:
                    stub_side = 'bottom'
                else:
                    stub_side = 'top'
            else:
                if layer_id > self.layer_number/2:
                    stub_side = 'top'
                else:
                    stub_side = 'bottom'                

        # --当为顶层或底层时，测试点就在对应层（重置上面的参数）
        if layer_id == 1:
            stub_side = 'top'
        if layer_id == self.layer_number:
            stub_side = 'bottom'

        # --当bd_span_top 与 bd_span_bot都存在时判断哪个stub对应的背钻层更深
        if bd_layer_top and bd_layer_bot:
            # --计算top面跨度值
            bd_top = bd_layer_top[2:].split('-')
            topAbs = abs(int(bd_top[0]) - int(bd_top[1]))
            # --计算bot面跨度值
            bd_bot = bd_layer_bot[2:].split('-')
            botAbs = abs(int(bd_bot[0]) - int(bd_bot[1]))
            # --比较两个跨度值
            if topAbs >= botAbs:
                bd_layer_bot = None
                stub_side = 'top'
            else:
                bd_layer_top = None
                stub_side = 'bottom'

        # --接线pad接地层定义
        ground_layer = None
        if stub_side == 'top':
            info = self.GEN.DO_INFO('-t layer -e %s/loss/%s -d EXISTS' % (self.JOB, 'l3'))
            if info['gEXISTS'] == "yes":
                ground_layer = 'l3'
        if stub_side == 'bottom':
            tmp_layer = 'l%s' % (self.layer_number - 2)
            info = self.GEN.DO_INFO('-t layer -e %s/loss/%s -d EXISTS' % (self.JOB, tmp_layer))
            if info['gEXISTS'] == "yes":
                ground_layer = tmp_layer

        # --根据选择的loss类型，生成不同长度的loss线
        loss_type = self.parm.loss_type
        loss_place = self.parm.loss_place
        if loss_type == 'std_type':
            if loss_place == u'品字形':
                loss_len_list = [10, 2, 5]
            else:
                loss_len_list = [2, 5, 10]
        else:
            loss_len_list = [2, 6]

        # --循环处置每个长度
        for loss_len in loss_len_list:
            right_org_x, right_org_y = 0, 0
            for direct in ['left', 'right']:
                if direct in ['left']:
                    factor = 1
                    # --测试pad
                    stub = stub_process(layer=layer, stub_side=stub_side, org_x=org_x, org_y=org_y, factor=factor,
                        refer1=refer1, refer2=refer2, ohms=ohms, line_width=line_width,
                        line_space=line_space, parm=self.parm)
                    stub.all_process()
                    # self.GEN.PAUSE('AAAAAAAAAAA')
                    # --定位孔
                    np = NP_process(org_x=org_x, org_y=org_y, factor=factor, parm=self.parm)
                    np.all_process()

                    pth = PTH_process(layer=layer, org_x=org_x, org_y=org_y, factor=1, ground_layer=ground_layer,
                        parm=self.parm)
                    pth.all_process()
                    # self.GEN.PAUSE('BBBBBBBBBBBBBB')

                    # --VIA 孔及对应孔pad
                    via = VIA_process(layer=layer, org_x=org_x, org_y=org_y, stub_side='top', parm=self.parm,
                        bd_layer=bd_layer_top)
                    via.all_process()

                    onlyBd_add = True if bd_layer_top else False
                    via = VIA_process(layer=layer, org_x=org_x, org_y=org_y, stub_side='bottom', parm=self.parm,
                        bd_layer=bd_layer_bot, onlyBd_add=onlyBd_add)
                    via.all_process()

                    # self.GEN.PAUSE('Left:bbbbbbbbbb2')

                    # --线及线头上的pad
                    line = line_process(layer=line_layer, org_x=org_x, org_y=org_y, line_width=line_width,
                        line_space=line_space, line_lenth=loss_len, factor=factor, layDict=self.parm.impList[count])
                    line.all_process()
                    # self.GEN.PAUSE('CCCCCCCCCCCCCCCC')
                    # --添加伴随接地孔
                    turn_points_upper = line.turn_points_upper
                    turn_points_lower = line.turn_points_lower
                    tilt_via = Tilt_via(org_x=org_x, org_y=org_y, turn_points_upper=turn_points_upper,
                        turn_points_lower=turn_points_lower, parm=self.parm)
                    if count == 0:
                        # --第一个走线,lower加伴随接地孔
                        if layer in adjacent_layer:
                            tilt_via.horizontal_via(direct='lower')
                        elif pre_layer in adjacent_layer:
                            tilt_via.horizontal_via(direct='lower')
                        else:
                            tilt_via.add_via(direct='lower')
                    if layer in adjacent_layer or next_layer in adjacent_layer:
                        tilt_via.horizontal_via(direct='upper')
                    else:
                        tilt_via.add_via(direct='upper')
                    # --计算右侧原点
                    right_org_x, right_org_y = line.get_right_org()

                    # --TODO 所有层，定位孔均加在右侧，防止套断线，异常料号b06/123a1,l1-85 l6-85
                    dw_x_right = right_org_x + 0.19 + 0.1
                    if loss_place == u'品字形' and loss_len in [5]:
                        # --品字形排版时，右上角定位孔坐标为profile偏左0.107486
                        dw_x_right = self.lenth - 0.107486
                    dw_y_right = right_org_y
                    self.dw_xy_right.append((dw_x_right, dw_y_right))
                else:
                    factor = -1
                    stub = stub_process(layer=layer, stub_side=stub_side, org_x=right_org_x, org_y=right_org_y,
                        factor=factor, refer1=refer1, refer2=refer2, ohms=ohms, line_width=line_width,
                        line_space=line_space, parm=self.parm)
                    stub.all_process()
                    np = NP_process(org_x=right_org_x, org_y=right_org_y, factor=factor, parm=self.parm)
                    np.all_process()
                    # self.GEN.PAUSE('Right:bbbbbbbbbb1')
                    pth = PTH_process(layer=layer, org_x=right_org_x, org_y=right_org_y, factor=factor,
                        ground_layer=ground_layer,
                        parm=self.parm)
                    pth.all_process()
                    # self.GEN.PAUSE('Right:bbbbbbbbbb1')

                    via = VIA_process(layer=layer, org_x=right_org_x, org_y=right_org_y, stub_side='top',
                        parm=self.parm, bd_layer=bd_layer_top)
                    via.all_process()

                    onlyBd_add = True if bd_layer_top else False
                    via = VIA_process(layer=layer, org_x=right_org_x, org_y=right_org_y, stub_side='bottom',
                        parm=self.parm, bd_layer=bd_layer_bot, onlyBd_add=onlyBd_add)
                    via.all_process()

                    # onlyBd_add = True if bd_layer_top else False
                    # via = VIA_process(layer=layer, org_x=org_x, org_y=org_y, stub_side='bottom', parm=self.parm,
                    #     bd_layer=bd_layer_bot, onlyBd_add=onlyBd_add)
                    # via.all_process()
                    # --既是参考层，又是走线层，铺铜
                    self.fill_copper_refer(layer, org_x, right_org_x, org_y, refer1, refer2)
            # self.GEN.PAUSE("XXXXXXXXXXXXXXXXaaaa")

            # --添加阻抗标示
            mark_text = '%s_%s_%sINCH_%s/%s' % (layer.upper(), int(ohms), loss_len, org_width, org_space)
            mark_len = 0.035 * len(mark_text)
            if stub_side == 'top':
                self.mark_top.append(mark_text)
                if layer == next_layer:
                    # --同一层有两个走线
                    self.mark_top_x.append(org_x + mark_len + 0.1 + 0.25575)
                    self.mark_top_y.append(org_y + 0.15)
                elif layer == outer[0]:
                    if next_layer in outer:
                        # --l1之后为外层bot面，两层之间多偏移了0.15inch
                        self.mark_top_x.append(org_x + mark_len + 0.1 + 0.25575)
                        self.mark_top_y.append(org_y + 0.15)
                    else:
                        # --l1层之后为其它内层走线层,两者之间只偏移了0.2inch,但标识可以加在同一水平线上
                        self.mark_top_x.append(org_x + mark_len + 0.1 + 0.25575)
                        self.mark_top_y.append(org_y + 0.2)
                else:
                    # --内层走线
                    self.mark_top_x.append(org_x + 0.25575)
                    self.mark_top_y.append(org_y)
            else:
                # --标识在bottom面
                self.mark_bot.append(mark_text)
                if layer not in outer:
                    # --走线层不是bottom
                    self.mark_bot_x.append(org_x + mark_len + 0.25575)
                    self.mark_bot_y.append(org_y)
                else:
                    self.mark_bot_x.append(org_x + 2 * mark_len + 0.35575)
                    # --y坐标定义
                    if len(self.mark_bot_y) == 0:
                        # --如果是第一个bot标识
                        if len(self.loss_inn) == 0 and len(self.loss_top) == 0:
                            # --如果没有内层走线,也没有外层top走线
                            self.mark_bot_y.append(org_y + 0.15)
                        else:
                            # --如果有内层走线
                            self.mark_bot_y.append(org_y - 0.2)
                    else:
                        if pre_layer in outer:
                            # --外层第二次走线，标识
                            self.mark_bot_y.append(org_y - 0.175)
                        elif pre_layer is None:
                            # --只有外层bot面一层走线
                            self.mark_bot_y.append(org_y + 0.15)
                        else:
                            # --前一个层别是内层
                            self.mark_bot_y.append(org_y - 0.2)

            # --切换线段长度后，计算当前线段左侧原点坐标
            if loss_place == u'品字形' and loss_len in [10]:
                org_x = org_x_left
                org_y = org_y_left + self.width / 2.0
            else:
                if layer in outer:
                    if org_x == 0.1205 + 0.19 + 0.086986:
                        # --l1层左侧加了定位孔，整体向右偏移了0.086986的情况
                        org_x += right_org_x - org_x + 0.19 * 2 + 0.15
                    else:
                        # --其它保证起始点与内层平齐
                        org_x += right_org_x - org_x + 0.19 * 2 + 0.15 + 0.086986
                else:
                    org_x += right_org_x - org_x + 0.19 * 2 + 0.15
                if loss_place == u'品字形':
                    org_y = org_y_left + self.width / 2.0
        # --跨参考层净空处理
        self.clear_refer(layer, line_layer, refer1, refer2)
        # --将线加入正式层别
        self.GEN.COPY_LAYER(self.JOB, 'loss', line_layer, layer, mode='append')
        # --删除临时层别
        info = self.GEN.DO_INFO('-t layer -e %s/loss/%s -d EXISTS' % (self.JOB, line_layer))
        if info['gEXISTS'] == "yes":
            self.GEN.COM('delete_layer,layer=%s' % line_layer)


class UI_info(object):
    # --描述符类，主要用来从UI界面取值或者向UI界面设置值
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, cls):
        """
        通过描述符获取值
        :param instance:描述符实例
        :type instance:
        :param cls:描述符托管类
        :type cls:
        :return:
        :rtype:
        """
        # print "描述符获取类变量"
        if instance is None:
            # --如果是通过类名来调用，直接返回描述符本身
            return self
        else:
            # --如果是通过实例调用
            obj = instance.findChild(QWidget, self.name)
            # print "描述符实例字典中没有值，直接从界面取值"
            if isinstance(obj, QtGui.QComboBox):
                curText = obj.currentText().toUtf8()
                return str(curText)
            elif isinstance(obj, QtGui.QCheckBox):
                return obj.isChecked()
            elif isinstance(obj, QtGui.QRadioButton):
                return obj.isChecked()
            else:
                curText = obj.text().toUtf8()
                try:
                    if isinstance(curText, bool):
                        # --bool值也可以float,False=0.0,True=1.0,所以不能直接转float，避免造成误解
                        curText = bool(curText)
                    else:
                        # --如果LineEdit中的是float,直接返回float,省去后面转换的麻烦
                        curText = float(curText)
                    return curText
                except ValueError:
                    return str(curText)

    def __set__(self, instance, value):
        """
        通过描述符设值
        :param instance:描述符实例
        :type instance:
        :param value:值
        :type value:
        :return:
        :rtype:
        """
        # print "描述符设置类变量"
        obj = instance.findChild(QWidget, self.name)
        if isinstance(obj, QtGui.QComboBox):
            AllItems = [obj.itemText(i) for i in range(obj.count())]
            index = AllItems.index(value)
            obj.setCurrentIndex(index)
        elif isinstance(obj, QtGui.QCheckBox):
            obj.setChecked(value)
        elif isinstance(obj, QtGui.QRadioButton):
            obj.setChecked(value)
        else:
            if isinstance(value, float) or isinstance(value, int):
                # --如果是浮点数，要转成str,否则会报错
                value = str(value)
            obj.setText(value)


class FrozenJSON(object):
    """
    一个只读接口，使用属性表示法访问JSON类对象
    """

    def __init__(self, mapping):
        self.__data = dict(mapping)

    def __getattr__(self, name):
        """
        FrozenJSON 类的关键是__getattr__ 方法
        仅当无法使用常规的方式获取属性(即在实例、类或超类中找不到指定的属性),解释器才会调用特殊的__getattr__方法
        :param name: 属性名比如.keys,.values,.items,不是字典键
        :type name:
        :return:
        :rtype:
        """
        if hasattr(self.__data, name):
            # --比如调用字典的keys、values等方法
            return getattr(self.__data, name)
        else:
            return FrozenJSON.build(self.__data[name])

    @classmethod
    def build(cls, obj):
        """
        类方法，第一个参数是类本身
        :param arg: 构建类的参数
        """
        if isinstance(obj, Mapping):
            # --如果obj 是映射,那就构建一个FrozenJSON对象
            return cls(obj)
        elif isinstance(obj, MutableSequence):
            # --如果参数是序列实例
            return [cls.build(item) for item in obj]
        else:
            # --其它如字符、int形式直接返回
            return obj


# --所有与InPlan查询相关的全部写到InPlan类中
class InPlan(object):
    def __init__(self, job_name):
        self.JOB = job_name
        self.JOB_SQL = self.JOB.upper()[:13]  # --截取前十三位料号名
        if self.JOB == self.JOB[:13] + "-c":
            # --专门做阻抗条的料号,参考K65308GN238A1-C
            self.JOB_SQL = self.JOB.upper()
        self.JOB_like = '%' + self.JOB_SQL + '%'
        self.layer_number = int(self.JOB[4:6])

        # --Oracle相关参数定义
        self.DB_O = Oracle_DB.ORACLE_INIT()
        self.dbc_o = self.DB_O.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
            username='GETDATA', passwd='InplanAdmin')

    def __del__(self):
        # --关闭数据库连接
        if self.dbc_o:
            self.DB_O.DB_CLOSE(self.dbc_o)

    def get_diff_imp(self):
        """
        获取差分阻抗信息
        :return:
        :rtype:
        """
        sql = """
        SELECT
            a.item_name AS 料号名,
            i.CREATION_DATE AS 创建时间,
            d.model_type_ AS 阻抗性质,
            d.trace_layer_ AS 测试层1,
            d.ref_layer_ AS 参考层1,
            round(d.finish_lw_, 3) AS 成品线宽,
            round(d.finish_ls_, 3) AS 成品线距,
            d.spacing_2_copper_ AS 到铜皮间距,
            c.customer_required_impedance AS 成品阻抗,
            round(c.artwork_trace_width, 2) work_width 
        FROM
            vgt_hdi.items a
            INNER JOIN vgt_hdi.public_items b ON a.root_id = b.root_id
            INNER JOIN vgt_hdi.impedance_constraint c ON b.item_id = c.item_id 
            AND b.REVISION_ID = c.revision_id
            INNER JOIN vgt_hdi.impedance_constraint_da d ON c.item_id = d.item_id 
            AND c.revision_id = d.revision_id 
            AND c.sequential_index = d.sequential_index
            INNER JOIN vgt_hdi.rpt_job_list i ON i.job_name = a.item_name 
        WHERE
            a.ITEM_NAME = '%s'
            AND d.model_type_ in (1,3)
            """ % self.JOB_SQL
        # --返回数据字典
        return self.DB_O.SELECT_DIC(self.dbc_o, sql)

    def get_REQUIRED_CU_WEIGHT_and_LAYER_ORIENTATION(self):
        """
        从InPlan中获取铜厚及层别正反的数据
        :return:sql后的字典
        """
        sql = """
            SELECT I.ITEM_NAME AS JOB_NAME,
                     II.ITEM_NAME AS LAYER_NAME,
                     ROUND(C.REQUIRED_CU_WEIGHT / 28.3495, 2) AS CU_WEIGHT,
                     ROUND(CD.CAL_CU_THK_ , 2) AS FINISH_THICKNESS,
                     C.LAYER_ORIENTATION,
                     C.LAYER_INDEX
            FROM VGT_HDI.PUBLIC_ITEMS    I,
                     VGT_HDI."JOB"           J,
                     VGT_HDI.PUBLIC_ITEMS    II,
                     VGT_HDI.COPPER_LAYER    C,
                     VGT_HDI.COPPER_LAYER_DA CD
            WHERE I.ITEM_TYPE = 2
            AND I.ITEM_NAME = '%s'
            AND I.ROOT_ID = J.ITEM_ID
            AND I.ITEM_ID = J.ITEM_ID
             AND I.REVISION_ID = J.REVISION_ID
             AND I.ROOT_ID = II.ROOT_ID
             AND II.ITEM_TYPE = 3
             AND II.ITEM_ID = C.ITEM_ID
             AND II.REVISION_ID = C.REVISION_ID
             AND C.ITEM_ID = CD.ITEM_ID
             AND C.REVISION_ID = CD.REVISION_ID
            ORDER BY C.LAYER_INDEX""" % self.JOB_SQL

        # --返回数据字典
        return self.DB_O.SELECT_DIC(self.dbc_o, sql)

    def get_hole_wall_thickness(self):
        """
        获取孔壁厚度
        """
        sql = """
            SELECT
                MIN_HOLE_CU_ 
            FROM
                vgt.rpt_drill_program_list 
            WHERE
                job_name = '%s'
                AND program_name = 'drl'
            """ % self.JOB_SQL
        # --返回数据字典
        flowDict = self.DB_O.SELECT_DIC(self.dbc_o, sql)
        wall_thickness = flowDict[0]['MIN_HOLE_CU_']
        wall_thickness = float('%.2f' % wall_thickness)
        hole_thickness = 0.7
        if wall_thickness >= 1.0:
            hole_thickness = 1.0
        elif wall_thickness >= 0.9:
            hole_thickness = 0.9
        elif wall_thickness >= 0.8:
            hole_thickness = 0.8
        elif wall_thickness >= 0.7:
            hole_thickness = 0.7
        return hole_thickness

    def get_flow_type(self):
        """
        从InPlan中获取一次铜、二次铜流程
        :return: flow_content 一次铜、二次铜
        """
        sql = """
            SELECT
                p.item_name as JOB_NAME, 
                i.item_name as LAYER_NAME,
                s.Flow_TYPE_  as FLOW_TYPE
            FROM
                VGT.public_items p,
                VGT.job j,
                VGT.PROCESS pr,
                VGT.PROCESS_DA s,
                VGT.public_items i 
            WHERE
                p.item_type = 2 
                AND p.item_name = '%s' 
                AND j.item_id = p.item_id 
                AND j.revision_id = p.revision_id 
                AND p.root_id = i.root_id 
                AND i.item_type = 7 
                AND i.item_id = s.item_id 
                AND i.revision_id = s.revision_id 
                AND pr.item_id = s.item_id 
                AND pr.revision_id = s.revision_id 
                AND pr.proc_type = 1
                AND pr.proc_subtype=29 """ % self.JOB_SQL

        # --返回数据字典
        flowDict = self.DB_O.SELECT_DIC(self.dbc_o, sql)
        flow_content = flowDict[0]['FLOW_TYPE']
        if flow_content == 1 or flow_content == 2:
            # --2对应none,也当成一次铜
            flow_content = u'一次铜'
        else:
            flow_content = u'二次铜'
        return flow_content

    def get_core_thick(self):
        """
        层别关联core厚度,内层补偿需考虑内层铜厚为1oz，基板厚铜≥0.8MM的界定，间距需3.4MIL，阻抗脚本需判定间距。
        :return:
        :rtype:
        """
        core_thick = dict()
        sql = """
            SELECT
                p.ITEM_NAME,
                pi.ITEM_NAME AS LAYER_NAME,
                ROUND( c.laminate_thickness / 39.37, 3 ) AS CORE_THICKNESS,
                co.layer_index,
                seg.stackup_seg_index 
            FROM
                VGT.public_items P,
                vgt.public_items i,
                vgt.public_items pi,
                vgt.STACKUP_SEG seg,
                VGT.SEGMENT_MATERIAL sm,
                vgt.MATERIAL m,
                vgt.core c,
                vgt.copper_layer co 
            WHERE
                p.item_type = 2 
                AND upper( p.item_name ) = '%s'
                AND i.root_id = p.root_id 
                AND i.item_type = 10 
                AND seg.item_id = i.item_id 
                AND seg.revision_id = i.revision_id 
                AND seg.segment_type = 0 
                AND sm.item_id = i.item_id 
                AND sm.revision_id = i.revision_id 
                AND m.item_id = sm.material_item_id 
                AND m.revision_id = sm.material_revision_id 
                AND m.item_id = c.item_id 
                AND m.REVISION_ID = c.REVISION_ID 
                AND i.root_id = pi.root_id 
                AND pi.item_type = 3 
                AND pi.item_id = co.item_id 
                AND pi.revision_id = co.revision_id 
                AND ( seg.stackup_seg_index = co.layer_index )
                """ % self.JOB_SQL
        query_result = self.DB_O.SELECT_DIC(self.dbc_o, sql)
        for query_dict in query_result:
            layer = query_dict['LAYER_NAME'].lower()
            core_thickness = query_dict['CORE_THICKNESS']
            core_thick[layer] = core_thickness
        return core_thick

    def get_Layer_Mode(self):
        """
        层别归类
        :return:
        :rtype:
        """
        core_thick = self.get_core_thick()
        layerMode = dict()
        outLayers = []
        secLayers = []
        innLayers = []
        sql = """
            SELECT
                p.item_name AS JOB_NAME,
                i.item_name AS LAYERS,
                pr.proc_subtype AS PRO_TYPE,
            -- decode(d.proc_subtype,29,'最外层',28,'子压合',27,'电镀芯板',26,'芯板') as  类型
                s.Flow_TYPE_ AS FLOW_TYPE 
            FROM
                vgt.public_items p
                INNER JOIN vgt.job j ON p.item_id = j.item_id 
                AND p.revision_id = j.revision_id
                INNER JOIN vgt.public_items i ON p.root_id = i.root_id
                INNER JOIN vgt.process pr ON i.item_id = pr.item_id 
                AND i.revision_id = pr.revision_id
                INNER JOIN vgt.process_da s ON i.item_id = s.item_id 
                AND i.revision_id = s.revision_id 
                AND pr.item_id = s.item_id 
                AND pr.revision_id = s.revision_id 
            WHERE
                p.item_name = '%s'
                AND pr.proc_type = 1
            """ % self.JOB_SQL
        query_result = self.DB_O.SELECT_DIC(self.dbc_o, sql)
        for query_dict in query_result:
            layers = query_dict['LAYERS']
            layers = layers.lower().split('-')
            proc_subtype = query_dict['PRO_TYPE']
            if proc_subtype in [26]:
                innLayers.extend(layers)
                if core_thick.has_key(layers[0]):
                    # --补全core的另一个层别
                    core_thick[layers[1]] = core_thick[layers[0]]
                elif core_thick.has_key(layers[1]):
                    # --补全core的另一个层别
                    core_thick[layers[0]] = core_thick[layers[1]]
            elif proc_subtype in [27, 28]:
                secLayers.extend(layers)
            elif proc_subtype in [29]:
                outLayers.extend(layers)
        layerMode['out'] = outLayers
        layerMode['sec'] = secLayers
        layerMode['inn'] = innLayers
        return layerMode, core_thick

    def get_bd_info(self):
        """
        通过sql查询获取背钻
        :return:
        :rtype:
        """
        bk_drl = []
        sql = """
        SELECT
            a.item_name AS 料号名,
            c.item_name AS 钻带名,
            decode(
                d.drill_technology,
                0,
                'Mechanical',
                1,
                'Controll Depth',
                2,
                'Laser',
                5,
                'Countersink',
                6,
                'Counterbore',
                7,
                'Backdrill' 
            ) AS 钻带类型,
            d.start_index AS 起始层,
            d.end_index AS 结束层 
        FROM
            VGT_HDI.items a
            INNER JOIN VGT_HDI.job b ON a.item_id = b.item_id 
            AND a.last_checked_in_rev = b.revision_id
            INNER JOIN VGT_HDI.public_items c ON a.root_id = c.root_id
            INNER JOIN VGT_HDI.drill_program d ON c.item_id = d.item_id 
            AND c.revision_id = d.revision_id
            INNER JOIN VGT_HDI.drill_program_da e ON d.item_id = e.item_id 
            AND d.revision_id = e.revision_id 
        WHERE
            a.item_name = '%s' 
        ORDER BY
            c.item_name
        """ % self.JOB_SQL
        query_result = self.DB_O.SELECT_DIC(self.dbc_o, sql)
        bd_info = []
        for query_dict in query_result:
            layer = query_dict['钻带名'].lower()
            index_start = query_dict['起始层']
            index_end = query_dict['结束层']
            layer_dict = {
                'layer': layer,
                'index_start': index_start,
                'index_end': index_end
            }
            bd_info.append(layer_dict)
        return bd_info


## --重写滚轮事件，以免识操作导致选项错误
#class QComboBox(QComboBox):
    #def wheelEvent(self, QWheelEvent):
        #pass


class MainWindow(QtGui.QWidget):
    ## --via孔大小
    #viaSize = UI_info('viaSize')
    ## --伴地孔大小
    #viaTilt = UI_info('viaTilt')
    ## --via孔大小
    #npSize = UI_info('npSize')
    ## --pth孔大小
    #pthSize = UI_info('pthSize')
    ## --loss模式
    #less_type = UI_info('less_type')
    #std_type = UI_info('std_type')
    ## --单位
    #unit_mm = UI_info('unit_mm')
    #unit_mil = UI_info('unit_mil')
    ## --排列模式：
    #loss_place = UI_info('loss_place')
    ## --anti pad大小
    #antiSize = UI_info('antiSize')
    ## --测试pad大小
    #testSize = UI_info('testSize')

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        # --TODO 测试用数据
        # self.JOB = os.environ.get('JOB', 'd51916pfk71a1')
        self.JOB = os.environ.get('JOB', 'hb1306pr092a1')
        self.layer_number = int(self.JOB[4:6])
        self.STEP = os.environ.get('STEP', None)
        self.GEN = genCOM.GEN_COM()
        self.abs_path = os.path.dirname(os.path.abspath(__file__))

        # --初始化获取补偿值的数据
        # self.COMP_VAL = getComp_Val.Main()
        self.COMP_VAL = None
        # self.getFlow, self.matchComp = self.COMP_VAL.getCom(self.JOB)

        # --初始化窗口
        #self.ui = FormUi.Ui_MainWindow()
        #self.ui.setupUi(self)
        
        #self.ui.tableWidget.hideColumn(8)
        #self.ui.tableWidget.horizontalHeader().setStretchLastSection(True)
        # --定义一个字典，收集所有变量
        self.parm = dict()
        # --连接InPlan并查询相关数据
        self.get_InPlan_info()
        # --默认less_type,2/6inch
        self.less_type = True
        # --默认单位mm
        self.unit_mil = True
        # --添加动态子部件
        # self.addPart_Ui()
        # --从料号获取信息并设置界面参数
        # self.set_UI_by_JOB()
        # --定义信号和槽函数
        # self.slot_func()
        
        self.create_ui_params()
        
    def create_ui_params(self):
        """创建界面参数"""        
        self.setWindowFlags(Qt.Qt.Window )    
        self.setObjectName("mainWindow")
        self.titlelabel = QtGui.QLabel(u"参数确认")
        self.titlelabel.setStyleSheet("QLabel {color:red}")
        self.setGeometry(700, 300, 0, 0)
        self.resize(1100, 500)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.titlelabel.setFont(font)        
    
        self.dic_editor = {}
        self.dic_label = {}
    
        arraylist1 = [ {u"VIA孔大小": "QLineEdit"},
                      {u"伴地孔大小": "QLineEdit"},
                      {u"NP孔大小": "QLineEdit"},
                      {u"Anti Pad大小": "QLineEdit"},
                      {u"PTH孔大小": "QLineEdit"},
                      {u"测试Pad大小": "QLineEdit"},
                      {u"loss条长度": "QComboBox"},
                      {u"loss排列方式": "QComboBox"},
                      #{u"允许修改信息": "QCheckBox"},
                       {u'外层铜厚': "QLineEdit"},
                       {u'补偿值': "QLineEdit"}
                      ]

        group_box_font = QtGui.QFont()
        group_box_font.setBold(True)    
        widget1 = self.set_widget(group_box_font,
                                  arraylist1,
                                   u"基本信息确认(单位MIL)",
                                   "")
        
        self.tableWidget1 = QtGui.QTableView()        
        self.tableWidget2 = QtGui.QTableView()        
        self.tableWidget3 = QtGui.QTableWidget()
        self.tableWidget3.setFixedHeight(150)
        
        self.pushButton = QtGui.QPushButton()
        self.pushButton1 = QtGui.QPushButton()
        self.pushButton2 = QtGui.QPushButton()
        self.pushButton.setText(u"运行")
        self.pushButton1.setText(u"退出")
        self.pushButton2.setText(u"加载上一次数据")
        self.pushButton.setFixedWidth(100)
        self.pushButton1.setFixedWidth(100)
        self.pushButton2.setFixedWidth(100)
        btngroup_layout = QtGui.QGridLayout()
        btngroup_layout.addWidget(self.pushButton,0,0,1,1) 
        btngroup_layout.addWidget(self.pushButton1,0,1,1,1)
        # btngroup_layout.addWidget(self.pushButton2,0,2,1,1)
        btngroup_layout.setSpacing(5)
        btngroup_layout.setContentsMargins(5, 5,5, 5)
        btngroup_layout.setAlignment(QtCore.Qt.AlignTop)          
    
        main_layout =  QtGui.QGridLayout()
        main_layout.addWidget(self.titlelabel,0,0,1,10, QtCore.Qt.AlignCenter)
        main_layout.addWidget(widget1,1,0,1,10)
        main_layout.addWidget(self.tableWidget3,2,0,1,11)
        main_layout.addWidget(self.tableWidget1,3,0,1,3)
        main_layout.addWidget(self.tableWidget2,3,2,1,9)
        main_layout.addLayout(btngroup_layout, 8, 0,1, 10)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(main_layout)
    
        # main_layout.setSizeConstraint(Qt.QLayout.SetFixedSize)
    
        self.pushButton.clicked.connect(self.clickApply)
        self.pushButton1.clicked.connect(sys.exit)
        # self.pushButton2.clicked.connect(self.reloading_data)
    
        self.setWindowTitle(u"LOSS COUPON参数确认%s" % __version__)
        self.setMainUIstyle()
        
        self.setTableWidget(self.tableWidget1, [u"钻带", u"最小孔径(um)"])
        self.setTableWidget(self.tableWidget2, [u"勾选", u"分组step", u"层名", u"菲林线宽",
                                                u"菲林线距", u"参考1", u"参考2", u"制作线宽",
                                                u"制作线距", u"OHM", u"补偿", u"阻抗类型"])
        #self.setTableWidget(self.tableWidget3, [u"层别", u"类型", u"铜厚", u"阻抗正常补偿",
                                                #u"特性加补", u"差分加补", u"共面特性补偿", u"共面差分补偿",
                                                #u"间距管控", u"成品线宽", u"成品线距"]) 
        
        self.tableItemDelegate = itemDelegate(self)
        self.tableWidget2.setItemDelegateForColumn(0, self.tableItemDelegate)
        self.connect(self.tableItemDelegate, QtCore.SIGNAL("select_item(PyQt_PyObject,PyQt_PyObject)"), self.order_coupon_step)
        
        
        self.filter_listbox = listView()    
        self.filter_listbox.hide()    
        self.filter_listbox.installEventFilter(self)        
        
        self.tableWidget2.horizontalHeader().sectionClicked.connect(self.show_filter_listbox) 
        self.connect(self.filter_listbox, QtCore.SIGNAL("ohm_values(PyQt_PyObject)"), self.update_tablewidget)
        
        #self.tableWidget1.setEnabled(False)
        #self.tableWidget2.setEnabled(False)            
        self.initial_value()
        
        self.table_laylist_set()
        
    def table_laylist_set(self):
        self.sig_layers = signalLayers
        self.layerInfo = icg_coupon_compensate.layerInfo
        self.stackupInfo = icg_coupon_compensate.stackupInfo
        self.getCouponCompList = icg_coupon_compensate.getCouponCompList
        self.out_gm_rule = icg_coupon_compensate.out_gm_rule
        self.inn_gm_rule = icg_coupon_compensate.inn_gm_rule
        # 层别列表定义
        self.tableWidget3.setAlternatingRowColors(True)
        # === 隐藏行标题
        self.tableWidget3.verticalHeader().hide()
        # self.tableWidget3.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableWidget3.setEditTriggers(QtGui.QTableWidget.NoEditTriggers)
        # 显示共面差分列 7 --> 8
        self.tableWidget3.setColumnCount(11)
        self.tableWidget3.setHorizontalHeaderLabels([u"层别", u"类型", u"铜厚", u"阻抗正常补偿",
                                                     u"特性加补", u"差分加补", u"共面特性补偿", u"共面差分补偿",
                                                     u"间距管控", u"成品线宽", u"成品线距"])
        self.tableWidget3.setRowCount(len(self.sig_layers))
        tableLyrRowWidth = [52, 38, 45, 85, 65, 85, 85, 85, 75,75,70]
        for rr in range(len(tableLyrRowWidth)):
            self.tableWidget3.setColumnWidth(rr, tableLyrRowWidth[rr])

        for x in range(len(self.sig_layers)):
            if not self.stackupInfo.has_key(self.sig_layers[x]):
                msg_box = msgBox()
                msg_box.warning(self, '警告', '未获取到{0}层干膜信息，请反馈MI上传'.format(self.sig_layers[x]), QtGui.QMessageBox.Ok)
                sys.exit(0)
            # === layer_mode out|sec|sec1|inn
            layer_mode = self.stackupInfo[self.sig_layers[x]]['layerMode']
            item = QtGui.QTableWidgetItem()
            # --样式（背景色）
            brush = QtGui.QBrush(QtGui.QColor(253, 199, 77))
            brush.setStyle(QtCore.Qt.SolidPattern)
            item.setBackground(brush)
            # --样式（前景色）
            brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
            brush.setStyle(QtCore.Qt.NoBrush)
            item.setForeground(brush)
            # --位置
            self.tableWidget3.setItem(x, 0, item)
            item = self.tableWidget3.item(x, 0)
            # --设置文字居中
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter)
            item.setText(str(self.sig_layers[x]))
            item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
            # print 'x' * 40,self.sig_layers[x],'x' * 40
            for index in range(len(self.layerInfo)):
                layName = self.layerInfo[index]['LAYER_NAME'].lower()
                if layName == self.sig_layers[x]:
                    item = QtGui.QTableWidgetItem(str(self.layerInfo[index]['CAL_CU_THK']))
                    item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
                    self.tableWidget3.setItem(x, 2, item)

                    cu_thick = self.layerInfo[index]['CAL_CU_THK']
                    if layer_mode == 'inn':
                        cu_thick = self.layerInfo[index]['CU_WEIGHT']
                    # === V3.7.5 合并单个参数改为一个，简化代码
                    compData = self.getCouponCompList(cu_thick, layer_mode)
                    if compData is None:
                        if layer_mode == 'sec1' and float(cu_thick) < 0.6:
                            # === 2022.12.23 部分料号超出规范定义范围，但仍需补偿的，使用最小区间下限进行补偿 ===
                            cu_thick = 0.6
                            compData = self.getCouponCompList(cu_thick, layer_mode)
                            self.tableWidget3.item(x, 2).setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 0)))
                            showText = u"料号:%s层别:%s无法获取补偿信息，层别类型:%s基铜:%s完成铜厚:%s,使用完成铜厚0.6进行补偿!" % (
                                self.job_name, self.sig_layers[x], self.stackupInfo[self.sig_layers[x]]['layerMode'],
                                self.layerInfo[index]['CU_WEIGHT'], self.layerInfo[index]['CAL_CU_THK'])
                            msg_box = msgBox()
                            msg_box.warning(self, '警告', showText, QtGui.QMessageBox.Ok)
                        else:
                            showText = u"料号:%s层别:%s无法获取补偿信息，层别类型:%s基铜:%s完成铜厚:%s,程序退出!" % (
                                self.job_name, self.sig_layers[x], self.stackupInfo[self.sig_layers[x]]['layerMode'],
                                self.layerInfo[index]['CU_WEIGHT'], self.layerInfo[index]['CAL_CU_THK'])
                            msg_box = msgBox()
                            msg_box.critical(self, '警告', showText, QtGui.QMessageBox.Ok)
                            exit(1)
                    l2lspc = float(compData.l2lspcControl) * 1.0

                    # === TODO 外层次外层增加解析度的比对，inn类型Hoz增加成品线宽，成品线距的条件
                    w_line_width = self.layerInfo[index]['成品线宽']
                    w_line_space = self.layerInfo[index]['成品线距']
                    self.tableWidget3.setItem(x, 9, QtGui.QTableWidgetItem(str(w_line_width)))
                    self.tableWidget3.setItem(x, 10, QtGui.QTableWidgetItem(str(w_line_space)))
                    if layer_mode == 'inn':
                        if 0.01 < cu_thick < 0.53:
                            if w_line_width == 0 or w_line_space == 0:
                                showText = []
                                if w_line_width == 0:
                                    showText.append(u'铜厚HOZ未能获取层别：%s 成品线宽，按默认值控制，请确认！' % (layName))
                                if w_line_space == 0:
                                    showText.append(u'铜厚HOZ未能获取层别：%s 成品线距，按默认值控制，请确认！' % (layName))
                                if showText:
                                    msg_box = msgBox()
                                    msg_box.warning(self, '警告', '\n'.join(showText), QtGui.QMessageBox.Ok)
                            elif 1.8 >= float(w_line_width) > 1.5 and 1.8 >= float(w_line_space) > 1.5:
                                l2lspc = 1.4
                                compData.impBaseComp = 0.5
                            elif 2.0 >= float(w_line_width) > 1.8 and 2.0 >= float(w_line_space) > 1.8:
                                l2lspc = 1.6
                                compData.impBaseComp = 0.6
                            # 同一芯板取最小的一组线宽线距
                            # if self.stackupInfo[layName].has_key('film_bg') and self.stackupInfo[layName]['film_bg']:
                            #     for d in self.layerInfo:
                            #         if str(d['LAYER_NAME']).strip().upper() == str(self.stackupInfo[layName]['film_bg']).strip().upper():
                            #             w_line_width_bg = d['成品线宽']
                            #             w_line_space_bg = d['成品线距']
                            #             if float(w_line_width) == 0 or float(w_line_space) == 0:
                            #                 if float(w_line_width_bg) > 1.5 and float(w_line_space_bg) > 1.5:
                            #                     w_line_width = w_line_width_bg
                            #                     w_line_space = w_line_space_bg
                            #             else:
                            #                 if w_line_width_bg > 1.5 and w_line_space > 1.5:
                            #                     if float(w_line_width) > float(w_line_width_bg) and float(w_line_space) > float(w_line_space_bg):
                            #                         w_line_width = w_line_width_bg
                            #                         w_line_space = w_line_space_bg
                            # elif 2.0 >= float(w_line_width) and 2.0 >= float(w_line_space):
                            #     l2lspc = 1.6
                    compData.l2lspcControl = l2lspc * 1.0

                    df_type = self.stackupInfo[layName]['df_type']
                    if layer_mode == 'sec' or layer_mode == 'out':
                        get_gm_min_space = None
                        for gm_line in self.out_gm_rule:
                            if df_type == gm_line['gm_type']:
                                get_gm_min_space = float(gm_line['min_space'])
                        if get_gm_min_space:
                            l2lspc = max(compData.l2lspcControl, get_gm_min_space)
                        else:
                            showText = u'未能获取层别：%s干膜：%s的解析度，使用规范中最小间距，需确认！' % (layName, df_type)
                            msg_box = msgBox()
                            msg_box.warning(self, '警告', showText, QtGui.QMessageBox.Ok)
                    if layer_mode == 'sec1' or layer_mode == 'inn':
                        get_gm_min_space = None
                        for gm_line in self.inn_gm_rule:
                            if df_type == gm_line['gm_type']:
                                get_gm_min_space = float(gm_line['min_space'])

                        if get_gm_min_space:
                            l2lspc = max(compData.l2lspcControl, get_gm_min_space)
                        else:
                            showText = u'未能获取层别：%s干膜：%s的解析度，使用规范中最小间距，需确认！' % (layName, df_type)
                            msg_box = msgBox()
                            msg_box.warning(self, '警告', showText, QtGui.QMessageBox.Ok)

                    # ======================================

                    self.layerInfo[index]['compData'] = compData
                    self.tableWidget3.setItem(x, 3, QtGui.QTableWidgetItem('%s' % compData.impBaseComp))
                    self.tableWidget3.setItem(x, 4, QtGui.QTableWidgetItem('%s' % compData.SingleComp))
                    self.tableWidget3.setItem(x, 5, QtGui.QTableWidgetItem('%s' % compData.DiffComp))
                    self.tableWidget3.setItem(x, 6, QtGui.QTableWidgetItem('%s' % compData.CopSingleComp))
                    self.tableWidget3.setItem(x, 7, QtGui.QTableWidgetItem('%s' % compData.CopDiffComp))
                    self.tableWidget3.setItem(x, 8, QtGui.QTableWidgetItem('%s' % l2lspc))
                    if layer_mode == 'inn' and  0.01 < cu_thick < 0.53:
                        if w_line_width == 0 or w_line_space == 0:
                            brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
                            brush.setStyle(QtCore.Qt.NoBrush)
                            self.tableWidget3.item(x, 8).setForeground(brush)
                            self.tableWidget3.item(x, 8).setToolTip(u"未获取到原稿线宽或线距，按默认最高区间控制")
            # print json.dumps (layerInfo, sort_keys=True, indent=2, separators=(',', ': '))
            item = QtGui.QTableWidgetItem('%s' % layer_mode)
            item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
            self.tableWidget3.setItem(x, 1, item)    

    def order_coupon_step(self, index, check_box):
        """给选中的行进行step分组"""
        model = self.tableWidget2.model()
        select_imp_row_info = []
        for i,j in self.tableItemDelegate.dic_editor.keys():
            if self.tableItemDelegate.dic_editor[i, j].isChecked():
                sig_layer = str(model.item(i, 2).text()).lower()
                ref_layer1 = str(model.item(i, 5).text()).lower()
                ref_layer2 = str(model.item(i, 6).text()).lower()
                #array_indexes = []
                #for layer in [sig_layer, ref_layer1, ref_layer2]:                    
                    #if layer in signalLayers:
                        #array_indexes.append(signalLayers.index(layer))
                        
                #geceng_ref_layers = []# 隔层参考
                #if array_indexes:                    
                    #for layer_index, layer in enumerate(signalLayers):
                        #if min(array_indexes)< layer_index < max(array_indexes) and layer != sig_layer:
                            #geceng_ref_layers.append(layer)
                            
                info = [sig_layer, ref_layer1, ref_layer2, i]

                select_imp_row_info.append(info)
            else:
                model.item(i, 1).setText("")
        
        dic_zu = {}
        for zu in range(1, 10):
            if not dic_zu.has_key(zu):
                dic_zu[zu] = []
                    
                for info in select_imp_row_info:
                    if "finish_group" not in info:
                        if not dic_zu[zu]:
                            info.append("finish_group")
                            dic_zu[zu].append(info)
                        else:
                            for group_info in dic_zu[zu]:
                                
                                if group_info == info:
                                    break
                                
                                if info[0] in group_info[1:]:
                                    break
                                
                                if info[1] == group_info[0] or \
                                   info[2] == group_info[0] :
                                    break
                            else:                                
                                info.append("finish_group")
                                dic_zu[zu].append(info)
                                    
        # print(dic_zu)
        for key, value in dic_zu.iteritems():
            for info in value:
                model.item(info[3], 1).setText(str(key))
        
    def update_tablewidget(self, values):
        """过滤阻值"""
        # print(values)
        recordStyleIndex = []
            
        rowcount = self.tableWidget2.model().rowCount()        
        for i in range(rowcount):            
            self.tableWidget2.showRow(i)
            ohm = str(self.tableWidget2.model().item(i, 9).text())
            for text in values:
                if float(text) == float(ohm): 
                    recordStyleIndex.append(i)
                    
        if not values:
            return
              
        for i in range(rowcount):            
            if i not in recordStyleIndex:                
                self.tableWidget2.hideRow(i)                     

    def show_filter_listbox(self, column):
        """显示层选择框"""        
        
        if column != 9:
            return
        
        self.filter_listbox.move(QtGui.QCursor.pos())   
        self.filter_listbox.show()
        
    def eventFilter(self,  source,  event):        
        if event.type() == QtCore.QEvent.ActivationChange:            
            if QtGui.QApplication.activeWindow() != self.filter_listbox:                
                self.filter_listbox.close()            
            
        return QtGui.QMainWindow.eventFilter(self,  source,  event)
    
    def initial_value(self):
        """初始化参数"""
        for item in ["2/6inch", u"2/5/10inch"]:
            self.dic_editor[u"loss条长度"].addItem(item)
            
        for item in [u"横排",u"品字型"]:
            self.dic_editor[u"loss排列方式"].addItem(item)

        self.dic_editor[u"VIA孔大小"].setText("9.843")
        self.dic_editor[u"伴地孔大小"].setText("9.843")
        self.dic_editor[u"NP孔大小"].setText("45.276")
        self.dic_editor[u"Anti Pad大小"].setText("36")
        self.dic_editor[u"PTH孔大小"].setText("19.685")
        self.dic_editor[u"测试Pad大小"].setText("rect20x12")
        # cu_weight = self.CU_WEIGHT.get('l1') if self.CU_WEIGHT.get('l1') else 0

        self.scrDir = '/incam/server/site_data/scripts/hdi_scr/Etch/outerBaseComp'
        self.config_file = self.scrDir + '/etch_data-hdi1-out.csv'
        if self.JOB[1:4] in ["a86", "d10"]:
            self.config_file = self.scrDir + '/etch_data-hdi1-out_nv.csv'
        self.out_comp_rule = []
        with open(self.config_file) as f:
            f_csv = csv.DictReader(f)
            for row in f_csv:
                self.out_comp_rule.append(row)
        comp = 0
        # print('comp_rule:', self.out_comp_rule)
        thickness = self.FINISH_THICKNESS.get('l1', 0)
        for index in range(len(icg_coupon_compensate.layerInfo)):
            layName = icg_coupon_compensate.layerInfo[index]['LAYER_NAME'].lower()
            if layName == "l1":
                thickness = float(icg_coupon_compensate.layerInfo[index]['CAL_CU_THK'])
                
        #print('a2', self.FINISH_THICKNESS)
        #print('a3', thickness)
        for data in self.out_comp_rule:
            rw, comp_ = data.get('range_type'), data.get('smdup12')
            min_num, max_num = float(rw[:3]), float(rw[-3:])
            if min_num <= thickness < max_num:
                comp = comp_
                break
        self.dic_editor[u"外层铜厚"].setText(str(thickness))
        self.dic_editor[u"补偿值"].setText(str(comp))

        
        self.dic_layer_info = {}
        self.add_data_to_table()
        
    def add_data_to_table(self):
        """表格内加载数据"""
        self.dic_min_hole_size = self.get_min_hole_size()
        arraylist = []
        for key, value in self.dic_min_hole_size.iteritems():
            if isinstance(value, (list, tuple)):
                arraylist.append([key, value[0]])
                continue
            arraylist.append([key, value])
        
        self.set_model_data(self.tableWidget1, arraylist)
        
        # self.dic_layer_info = self.get_layer_pad_ring_line_width()
        #arraylist = []
        #for key in sorted(self.dic_layer_info.keys(), key=lambda x: int(x[1:])):
            #arraylist.append([key]+ self.dic_layer_info[key])
            
        arraylist = self.get_inplan_imp_info()            
        self.set_model_data(self.tableWidget2, arraylist)
        
        self.filter_listbox.listbox.clear()
        ohm_vaues = [x[9] for x in arraylist]
        for ohm in  sorted(set(ohm_vaues)):
            item = QtGui.QListWidgetItem(str(ohm), self.filter_listbox.listbox)
            item.setCheckState(0)
    
    def get_min_hole_size(self):
        """获取最小孔径"""
        dic_min_hole_size = {}
        for drillLayer in tongkongDrillLayer + mai_drill_layers + laser_drill_layers:
            dic_min_hole_size[drillLayer] = ""
            if drillLayer in tongkongDrillLayer:
                if "edit" in matrixInfo["gCOLstep_name"]:
                    # 板内最小孔剔除掉槽孔 及引孔
                    edit_step = gClasses.Step(job, "edit")
                    edit_step.open()
                    edit_step.COM("units,type=mm")
                    edit_step.clearAll()
                    edit_step.affect(drillLayer)
                    edit_step.copyLayer(job.name, "edit", drillLayer, drillLayer+"_tmp")
                    edit_step.copyLayer(job.name, "edit", drillLayer, drillLayer+"_tmp1")
                    edit_step.clearAll()
                    edit_step.affect(drillLayer+"_tmp1")
                    edit_step.contourize()
                    edit_step.COM("sel_delete_atr,attributes=.rout_chain")                        
                    edit_step.COM("sel_resize,size=-5")
                    
                    edit_step.clearAll()
                    edit_step.affect(drillLayer+"_tmp")
                    edit_step.resetFilter()
                    edit_step.filter_set(feat_types='line;arc')
                    edit_step.selectAll()
                    if edit_step.featureSelected():
                        edit_step.moveSel("slot_tmp")
                        edit_step.resetFilter()
                        edit_step.refSelectFilter("slot_tmp")
                        if edit_step.featureSelected():
                            edit_step.selectDelete()
                            
                        edit_step.removeLayer("slot_tmp")                  
                    
                    edit_step.resetFilter()
                    edit_step.refSelectFilter(drillLayer+"_tmp1", mode="cover")
                    if edit_step.featureSelected():
                        edit_step.selectDelete()
                    
                    hole_size = getSmallestHole(job.name, "edit", drillLayer+"_tmp") or \
                        getSmallestHole(job.name, "", drillLayer+"_tmp")
                    
                    edit_step.removeLayer(drillLayer+"_tmp")
                    edit_step.removeLayer(drillLayer+"_tmp1")
                else:
                    hole_size = getSmallestHole(job.name, "edit", drillLayer, panel=None)
            else:                        
                hole_size = getSmallestHole(job.name, "edit", drillLayer, panel=None)
                if getattr(self, "big_laser_holes", None) is not None:
                    for laser_layer in self.big_laser_holes:
                        if drillLayer[1:] in laser_layer:
                            symbolname = self.get_raoshao_laser_hole(drillLayer)
                            # step.PAUSE(str(symbolname))
                            # 绕烧不能判断孔径大小 暂定为350
                            # max_laser_hole = 350
                            # dic_raoshao[drillLayer] = "yes"
                            if symbolname:
                                hole_size = (hole_size, symbolname)
                            else:
                                log = u"检测到{0}镭射INPLAN钻孔信息有备注绕烧，但钻带内处理绕烧孔径失败，请手动修改镭射孔径！"
                                # showMessageInfo(log.format(drillLayer))
                                QtGui.QMessageBox.information(self, u'提示', log.format(drillLayer), 1)                                
            
            if drillLayer in tongkongDrillLayer:
                # 有，如通孔里面没有小孔的，取0.452的孔做导通 最大不能超过0.452
                self.tong_hole_type = "has_small_pth"
                if not hole_size:
                    self.tong_hole_type = "no_small_pth"
                    
                hole_size = hole_size if hole_size else 452
                if hole_size > 452:
                    hole_size = 452
            else:
                if not hole_size:
                    if drillLayer in laser_drill_layers:
                        # 镭射层板内没孔的不计算在内
                        del dic_min_hole_size[drillLayer]
                        
                    continue
                
            dic_min_hole_size[drillLayer] = hole_size
            
        return dic_min_hole_size    
            
    def get_inplan_imp_info(self):
        """获取inplan阻抗信息
        料号名 ，分组，阻抗类型，原始线宽，原始间距，原始铜距，阻抗层，参考层，
        出货线宽，出货线距，出货铜距，客户需求阻值，是否开窗阻抗"""
        # array_imp_info = get_inplan_imp(job.name.upper())
        array_imp_info = icg_coupon_compensate.get_dic_compensate_imp_info()
        
        arraylist_info = []
        for dic_info in array_imp_info:
            if u"特性" in dic_info["imodel".upper()].decode("utf8"):
                continue
            list_info = ["", ""]
            for key in ["trace_layer_", "workLineWid", "workLineSpc","ref_layer_", "finish_lw_",
                        "finish_ls_", "cusimp", "compensate_value", "imodel"]:
                if key == "ref_layer_":
                    key = key.upper()
                    ref_layer = dic_info[key].upper()
                    if ref_layer is not None:
                        if "&" in ref_layer:                            
                            layer1, layer2 = sorted(ref_layer.split("&"),key=lambda x: int(x[1:]) )                      
                            list_info.append(layer1)
                            list_info.append(layer2)
                        else:
                            if dic_info["trace_layer_".upper()] == "L1":
                                list_info.append("None")
                                list_info.append(ref_layer)
                            else:
                                list_info.append(ref_layer)
                                list_info.append("None")        
                    else:
                        list_info.append("None")
                        list_info.append("None")
                else:
                    if key in ["org_width", "org_spc"]:
                        key = key.upper()
                        list_info.append("%.2f" % dic_info[key] if dic_info[key] is not None else 0)
                    elif key in ["imodel"]:
                        key = key.upper()
                        if u"差动" in dic_info[key].decode("utf8"):
                            list_info.append("diff")
                        if u"特性" in dic_info[key].decode("utf8"):
                            list_info.append("single")
                    elif key in ["compensate_value"]:
                        list_info.append(0)
                    elif key in ["workLineWid", "workLineSpc"]:
                        list_info.append(dic_info[key])
                    else:
                        key = key.upper()
                        list_info.append(dic_info[key])
                    
            # list_info.append(0)
            arraylist_info.append(list_info)
    
        return sorted(arraylist_info, key=lambda x: int(x[2][1:]))  
        
    def set_model_data(self, table, data_info):
        """设置表内数据"""
        model = table.model()            
        model.setRowCount(len(data_info))
        for i, array_info in enumerate(data_info):
            for j , data in enumerate(array_info):                
                index = model.index(i,j, QtCore.QModelIndex())
                model.setData(index, data)
                if table == self.tableWidget2:
                    if j == 0:
                        self.tableWidget2.openPersistentEditor(index)
                        if data == "1":
                            self.tableItemDelegate.dic_editor[i, j].setCheckState(2)
                        else:
                            self.tableItemDelegate.dic_editor[i, j].setCheckState(0)
    
    def setTableWidget(self, table, columnHeader):
        # table = self.tableWidget  
        # self.columnHeader = [u"钻带", u"最小孔", u"最小ring环(um)"]
        self.tableModel = QtGui.QStandardItemModel(table)
        self.tableModel.setColumnCount(len(columnHeader))
        for j in range(len(columnHeader)):
            self.tableModel.setHeaderData(
                j, Qt.Qt.Horizontal, columnHeader[j])
        table.setModel(self.tableModel)
        table.verticalHeader().setVisible(False)
        #table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        #table.setEditTriggers(QtGui.QTableWidget.NoEditTriggers)
        
        header = table.horizontalHeader()
        header.setDefaultAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        header.setTextElideMode(QtCore.Qt.ElideRight)
        header.setStretchLastSection(True)
        header.setClickable(True)
        header.setMouseTracking(True)
        table.setColumnWidth(0, 60)
        table.setColumnWidth(1, 70)
        table.setColumnWidth(2, 70)
        table.setColumnWidth(3, 70)
        table.setColumnWidth(4, 60)
        table.setColumnWidth(5, 50)
        table.setColumnWidth(6, 50)
        table.setColumnWidth(7, 60)
        table.setColumnWidth(8, 70)
        table.setColumnWidth(9, 70)
        
        table.hideColumn(11)
        table.hideColumn(10)

    def set_widget(self, font, arraylist, title, checkbox):
        groupbox = QtGui.QGroupBox()
        groupbox.setTitle(title)
        groupbox.setStyleSheet("QGroupBox:title{color:green}")
        groupbox.setFont(font)	
        gridlayout = self.get_layout(arraylist, checkbox)
        groupbox.setLayout(gridlayout)
        return groupbox

    def get_layout(self, arraylist, checkbox):
        gridlayout = QtGui.QGridLayout()
        for i, name in enumerate(arraylist):
            for key, value in name.iteritems():
                self.dic_label[key] = QtGui.QLabel()
                self.dic_label[key].setText(key)
                self.dic_editor[key] = getattr(QtGui, value)()
                col = 2 if i % 2 else 0
                row = -1 if col else 0
                gridlayout.addWidget(self.dic_label[key], i + 1 + row, 1 + col, 1, 1)
                gridlayout.addWidget(self.dic_editor[key], i + 1 + row, 2 + col, 1, 1)
                
                if key == u"loss条长度":
                    self.dic_editor[key].currentIndexChanged.connect(self.change_loss_order)

        gridlayout.setSpacing(5)
        gridlayout.setContentsMargins(5, 5,5, 5)
        gridlayout.setAlignment(QtCore.Qt.AlignTop)
        return gridlayout

    def change_loss_order(self, index):
        if index == 0:
            self.dic_editor[u"loss排列方式"].setCurrentIndex(0)
            self.dic_editor[u"loss排列方式"].setEnabled(False)
        else:
            self.dic_editor[u"loss排列方式"].setCurrentIndex(0)
            self.dic_editor[u"loss排列方式"].setEnabled(True)            
    
    def setTableModifyStatus(self):
        if self.sender().isChecked():
            self.tableWidget1.setEnabled(True)
            self.tableWidget2.setEnabled(True)
        else:
            self.tableWidget1.setEnabled(False)
            self.tableWidget2.setEnabled(False)
            
    def setMainUIstyle(self):#设置风格
        file = QtCore.QFile(':/pic/fblue.qss')
        file.open(QtCore.QFile.ReadOnly)
        styleSheet = file.readAll()
        styleSheet = unicode(styleSheet, encoding='gb2312')
        QtGui.qApp.setStyleSheet(styleSheet)
        
    def setValue(self):
        res = 0
        if os.path.exists(smk_info):
            with open(smk_info) as file_obj:
                self.dic_hct_info = json.load(file_obj)

            for key, value in self.dic_editor.iteritems():
                if self.dic_hct_info.get(key):		    
                    if isinstance(self.dic_editor[key], QtGui.QLineEdit):
                        if isinstance(self.dic_hct_info[key], float):
                            self.dic_editor[key].setText("%s" % self.dic_hct_info[key])
                        else:
                            self.dic_editor[key].setText(self.dic_hct_info[key])
                    elif isinstance(self.dic_editor[key], QtGui.QComboBox):
                        pos = self.dic_editor[key].findText(
                            self.dic_hct_info[key], QtCore.Qt.MatchExactly)
                        self.dic_editor[key].setCurrentIndex(pos)
                        
            if self.dic_hct_info.get(u"最小孔径"):
                self.set_model_data(self.tableWidget1, self.dic_hct_info[u"最小孔径"])
            else:
                res += 1
                
            if self.dic_hct_info.get(u"阻抗及补偿信息"):
                self.set_model_data(self.tableWidget2, self.dic_hct_info[u"阻抗及补偿信息"])
            else:
                res += 1
        else:
            res = 1
                
        return res
        
    def get_item_value(self):
        """获取界面参数"""	
        self.dic_item_value = {}
        for key, value in self.dic_editor.iteritems():
            if isinstance(self.dic_editor[key], QtGui.QLineEdit):
                self.dic_item_value[key] = unicode(self.dic_editor[key].text(
                    ).toUtf8(), 'utf8', 'ignore').encode('cp936').decode("cp936")
            elif isinstance(self.dic_editor[key], QtGui.QComboBox):
                self.dic_item_value[key] = unicode(self.dic_editor[key].currentText(
                    ).toUtf8(), 'utf8', 'ignore').encode('cp936').decode("cp936")                
                
        arraylist = [ u"VIA孔大小",
                      u"伴地孔大小",
                      u"NP孔大小",
                      u"Anti Pad大小",
                      u"PTH孔大小",
                      ]        
        
        for key in arraylist:
            if self.dic_item_value.has_key(key):
                try:
                    self.dic_item_value[key] = float(self.dic_item_value[key])
                except:
                    QtGui.QMessageBox.information(self, u'提示', u'检测到 %s 参数[ %s ]为空或非法数字,请检查~' % (
                        key, self.dic_item_value[key]), 1)
                    # self.show()
                    return 0

        #if self.dic_item_value[u"二维码面次"] == "":
            #QtGui.QMessageBox.information(self, u'提示', u'检测到 二维码面次 为空,请选择C面或S面,请检查~', 1)
            #return 0       
        
        self.dic_item_value[u"最小孔径"] = []
        model = self.tableWidget1.model()
        for row in range(model.rowCount()):
            arraylist = []
            for col in range(model.columnCount()):
                value = str(model.item(row, col).text())
                if col <> 0:
                    try:
                        float(value)
                    except:
                        QtGui.QMessageBox.information(self, u'提示', u'检测到 %s 最小孔 有参数[ %s ]为空或非法数字,请检查~' % (
                            model.item(row, 0).text(), value), 1)
                        return 0
                arraylist.append(value)
                
            self.dic_item_value[u"最小孔径"].append(arraylist)            
            
        self.parm["Alldrill_small_hole"] = self.dic_item_value[u"最小孔径"]
        self.dic_item_value[u"阻抗及补偿信息"] = []
        model = self.tableWidget2.model()
        for row in range(model.rowCount()):
            arraylist = []
            for col in range(model.columnCount()):
                value = str(model.item(row, col).text())
                arraylist.append(value)
                
            self.dic_item_value[u"阻抗及补偿信息"].append(arraylist)             

        #with open(smk_info, 'w') as file_obj:
            #json.dump(self.dic_item_value, file_obj)

        return 1


    def slot_func(self):
        """
        集中定义信号和槽函数
        :return: None
        """
        # --定义执行按钮的信号、槽连接
        self.connect(self.ui.create_btn, QtCore.SIGNAL("clicked()"), self.clickApply)
        self.connect(self.ui.std_type, QtCore.SIGNAL("clicked()"), self.On_sel_std_type)
        self.connect(self.ui.less_type, QtCore.SIGNAL("clicked()"), self.On_sel_less_type)
        self.connect(self.ui.unit_mm, QtCore.SIGNAL("clicked()"), self.On_sel_unit_mm)
        self.connect(self.ui.unit_mil, QtCore.SIGNAL("clicked()"), self.On_sel_unit_mil)
        # --QTableWidgetItem变更
        self.connect(self.ui.tableWidget, QtCore.SIGNAL("cellChanged(int, int)"), self.On_cellChange)
        # --安装事件过滤器，达到禁用QComboBox滚轮事件的目的
        self.ui.loss_place.installEventFilter(self)

    def clickApply(self):
        """
        点击loss条按钮（创建）的事件方法
        :return:
        """
        # --设定鼠标光标为busy状态
        # self.setCursor(Qt.WaitCursor)
        res = self.get_item_value()
        if not res:
            return

        # --从UI界面取值
        self.get_UI_info()

        # --关闭主界面
        # self.close()

        # --执行运行方法
        self.run()
        
        sys.exit(0)

    def run(self):
        """
        在genesis或incam中具体执行添加物件的函数
        :return:
        :rtype:
        """
        for stepname in ["loss-edit", "loss-orig"]:
            info = self.GEN.DO_INFO('-t step -e {0}/{1} -d EXISTS'.format( self.JOB, stepname))
            if info['gEXISTS'] == "yes":
                # --如果loss存在时，删除现有loss并重新生成
                self.GEN.DELETE_ENTITY('step', stepname, job=self.JOB)
                
            if stepname == "loss-orig":
                for layDict in self.parm["impAll"]:
                    layDict["line_width"] = layDict["org_width"]
                    layDict["line_space"] = layDict["org_space"]
                self.parm['comp'] = 0

            json_string = json.dumps(self.parm, ensure_ascii=False, indent=4, separators=(', ', ': '), sort_keys=True)
            print(json_string)
            # self.GEN.PAUSE("XXXX")
            self.GEN.COM('disp_off')
            loss = Loss(job_name=self.JOB, step_name=self.STEP, json_data=json_string)
            loss.run()
    
            # --因添加的图形是从下往上加的，必然会导致部分负性在正片的下面，最后再统一提下所有负性顺序（除去surface不提，其它全部选择并move出去，再move回来）
            self.loopAllsignals()
    
            # --检测背钻的添加逻辑
            BD_Check = BDDrill_Check.Main(JOB=self.JOB, STEP=self.STEP)
            BD_Check.checkBD_Broken()
    
            # --Run 相关DFM
            self.runOpt_DFM()
    
            # --添加所有走线层添加泪滴
            loss.add_Teardrops()
            
            self.GEN.COM("rename_entity,job={0},name=loss,new_name={1},is_fw=no,type=step,fw_type=form".format(
                self.JOB, stepname
            ))

        self.GEN.COM('disp_on')
        msg_box = msgBox()
        msg_box.information(self, '脚本运行完成', '脚本运行OK, 请检查！', QMessageBox.Ok)

    def get_UI_info(self):
        '''
        从window界面TabWidget控件中获取所有参数
        :return:
        '''
        # 界面关闭前，参数不再变化，统一从界面获取参数并存入字典
        #if self.unit_mm:
            #self.parm['viaSize'] = float(self.convert_to_mil(self.viaSize))
            #self.parm['viaTilt'] = float(self.convert_to_mil(self.viaTilt))
            #self.parm['pthSize'] = float(self.convert_to_mil(self.pthSize))
            #self.parm['npSize'] = float(self.convert_to_mil(self.npSize))
            #self.parm['antiSize'] = float(self.convert_to_mil(self.antiSize))
            #try:
                #self.parm['testSize'] = float(self.convert_to_mil(self.testSize))
            #except:
                #self.parm['testSize'] = self.convert_to_mil(self.testSize)
        #else:
            #self.parm['viaSize'] = self.viaSize
            #self.parm['viaTilt'] = self.viaTilt
            #self.parm['pthSize'] = self.pthSize
            #self.parm['npSize'] = self.npSize
            #self.parm['antiSize'] = self.antiSize
            #self.parm['testSize'] = self.testSize
        #arraylist1 = [ {u"VIA孔大小": "QLineEdit"},
                      #{u"伴地孔大小": "QLineEdit"},
                      #{u"NP孔大小": "QLineEdit"},
                      #{u"Anti Pad大小": "QLineEdit"},
                      #{u"PTH孔大小": "QLineEdit"},
                      #{u"测试Pad大小": "QLineEdit"},
                      #{u"loss条长度": "QComboBox"},
                      #{u"loss排列方式": "QComboBox"},
                      ##{u"允许修改信息": "QCheckBox"},
                      #]            
        self.viaSize = self.dic_item_value[u"VIA孔大小"]
        self.viaTilt = self.dic_item_value[u"伴地孔大小"]
        self.pthSize = self.dic_item_value[u"PTH孔大小"]
        self.npSize = self.dic_item_value[u"NP孔大小"]
        self.antiSize = self.dic_item_value[u"Anti Pad大小"]
        self.testSize = self.dic_item_value[u"测试Pad大小"]
        self.comp = self.dic_item_value[u"补偿值"]
        self.loss_place = self.dic_item_value[u"loss排列方式"]
        if self.dic_item_value[u"loss条长度"] == "2/6inch":
            self.less_type = True
        else:
            self.less_type = False
        
        self.parm['viaSize'] = float(self.viaSize)
        self.parm['viaTilt'] = float(self.viaTilt)
        self.parm['pthSize'] = float(self.pthSize)
        self.parm['npSize'] = float(self.npSize)
        self.parm['antiSize'] = float(self.antiSize)
        self.parm['testSize'] = self.testSize
        self.parm['comp'] = self.comp
        self.parm['loss_place'] = self.loss_place
        self.impList = self.get_table_widget_info()
        self.parm['impList'] = self.impList
        if self.less_type:
            self.parm['loss_type'] = 'less_type'
        else:
            self.parm['loss_type'] = 'std_type'
        self.parm['is_back_drill'] = self.is_back_drill
        self.parm['bd_info'] = self.bd_info
        self.parm['layer_number'] = self.layer_number

    #def eventFilter(self, watched, event):
        #"""
        #事件过滤器
        #:param watched:
        #:type watched:
        #:param event:
        #:type event:
        #:return:
        #:rtype:
        #"""
        #if watched == self.ui.loss_place:
            #if event.type() == QEvent.Wheel:
                ## --拦截事件，不再发送到原来的控件,返回True,继续返回原控件返回False
                #return True
        ## --其它未拦截事件仍然返回原控件
        #return False

    def convert_to_mm(self, size_mil):
        """
        mil转换成mm
        :return:
        :rtype:
        """
        if 'rect' in str(size_mil):
            sizeSplit = size_mil[4:].split('x')
            size_mm = 'rect%.3fx%.3f' % (float(sizeSplit[0]) * 0.0254, float(sizeSplit[1]) * 0.0254)
        else:
            size_mm = float(size_mil) * 0.0254
            size_mm = '%.3f' % size_mm

        return size_mm

    def convert_to_mil(self, size_mm):
        """
        mm转换成mil
        :return:
        :rtype:
        """
        if 'rect' in str(size_mm):
            sizeSplit = size_mm[4:].split('x')
            size_mil = 'rect%.3fx%.3f' % (float(sizeSplit[0]) / 0.0254, float(sizeSplit[1]) / 0.0254)
        else:
            size_mil = (size_mm * 1000.0) / 25.4
            size_mil = '%.3f' % size_mil

        return size_mil

    def On_sel_unit_mm(self):
        """
        选择单位mm时触发
        :return:
        :rtype:
        """
        # --pth孔固定0.50mm
        self.pthSize = 0.50
        # --np孔固定1.15mm
        self.npSize = 1.15
        # --计算并转换via孔大小
        self.viaSize = self.convert_to_mm(self.viaSize)
        # --计算并转换伴地孔大小
        self.viaTilt = self.convert_to_mm(self.viaTilt)
        # --计算并转换antiPad大小
        self.antiSize = self.convert_to_mm(self.antiSize)
        # --计算并转换testPad大小
        self.testSize = self.convert_to_mm(self.testSize)
        # --设置groupBox的标题
        self.ui.groupBox.setTitle(u'参数选择(单位：mm)')

    def On_sel_unit_mil(self):
        """
        选择单位mil时触发
        :return:
        :rtype:
        """
        # --pth孔固定0.50mm
        self.pthSize = 19.685
        # --np孔固定1.15mm
        self.npSize = 45.276
        # --计算转换并设置via孔大小
        self.viaSize = self.convert_to_mil(self.viaSize)
        # --计算转换并设置伴地孔大小
        self.viaTilt = self.convert_to_mil(self.viaTilt)
        # --计算转换并设置antiPad大小
        self.antiSize = self.convert_to_mil(self.antiSize)
        # --计算转换并设置testPad大小
        self.testSize = self.convert_to_mil(self.testSize)
        self.ui.groupBox.setTitle(u'参数选择(单位：mil)')

    def On_sel_less_type(self):
        """
        loss条长度选择：2/5/10 inch
        :return:
        :rtype:
        """
        # --设置手指方向QComboBox不可选择
        self.ui.loss_place.setEnabled(False)
        self.loss_place = u'横排'

    def On_sel_std_type(self):
        """
        loss条长度选择：2/6 inch
        :return:
        :rtype:
        """
        # --设置手指方向QComboBox可以选择
        self.ui.loss_place.setEnabled(True)

    def get_InPlan_info(self):
        """
        从InPlan查询相关信息
        :return:
        :rtype:
        """
        # --连接InPlan并查询相关数据
        self.InPlan = InPlan(self.JOB)
        self.sqlDic = self.InPlan.get_REQUIRED_CU_WEIGHT_and_LAYER_ORIENTATION()
        # self.CuThickHole = self.InPlan.get_hole_wall_thickness()
        # self.layerMode, self.core_thick = self.InPlan.get_Layer_Mode()
        self.CU_WEIGHT, self.FINISH_THICKNESS = self.convert_layer_thick()
        # self.impDict = self.InPlan.get_diff_imp()
        self.impDict = icg_coupon_compensate.get_dic_compensate_imp_info()
        # self.flow_content = self.InPlan.get_flow_type()
        self.bd_info = self.InPlan.get_bd_info()
        if len(self.bd_info) > 0:
            self.is_back_drill = True
        else:
            self.is_back_drill = False
        print('bbbb',self.CU_WEIGHT)

    def addPart_Ui(self):
        """
        在原框架基础上继续加载窗体
        :return:None
        """
        # --加载动态层列表
        impDict = self.impDict
        sqlDic = self.sqlDic

        # --当从InPlan中未获取到参数时
        if len(sqlDic) == 0:
            msg_box = msgBox()
            msg_box.critical(self, '警告', 'Inplan数据库中没有料号:%s的铜厚数据，无法确定补偿值！' % self.JOB, QMessageBox.Ok)
            sys.exit()
        if len(impDict) == 0:
            msg_box = msgBox()
            msg_box.critical(self, '警告', 'Inplan数据库中没有料号:%s的差分阻抗数据，程序无法执行！' % self.JOB, QMessageBox.Ok)
            sys.exit()

        # --取出测试层2
        allDict = []
        for rowDir in impDict:
            if rowDir["IMODEL"] == "特性":
                continue            
            # layName2 = rowDir['测试层2']
            # refers2 = rowDir['参考层2']
            # if layName2 is not None:
            #     layDict = dict(rowDir)
            #     layDict['测试层1'] = layName2
            #     layDict['参考层1'] = refers2
            #     allDict.append(rowDir)
            #     allDict.append(layDict)
            # else:
            allDict.append(rowDir)
        
        #同步阻抗条的算法获取跟阻抗条一样的补偿值菲林线宽及线距 20240805 by lyh
        # ['TRACE_LAYER_', 'WORKLINEWID', 'WORKLINESPC', 'REF_LAYER_', 'FINISH_LW_', 'FINISH_LS_', 'CUSIMP', 'COMPENSATE_VALUE', 'IMODEL']
        # --以层别名进行排序
        allDict = sorted(allDict, key=lambda layDict: int(str(layDict['TRACE_LAYER_'])[1:]))

        # --重新定义行数
        self.ui.tableWidget.setRowCount(len(allDict))
        # --样式（背景色）
        brush_bg = QtGui.QBrush(QtGui.QColor(253, 199, 77))
        brush_bg.setStyle(QtCore.Qt.SolidPattern)

        # --设定QTableWidget各列的宽度
        tableRowWidth = [85, 85, 85, 80, 85, 85, 85, 85, 80]
        for rr in range(len(tableRowWidth)):
            self.ui.tableWidget.setColumnWidth(rr, tableRowWidth[rr])

        # --循环所有层并加入行
        # infoList = []
        for rowDir in allDict:                
            # --获取数组序号
            rowNum = allDict.index(rowDir)
            # --获取层名
            layName = rowDir['TRACE_LAYER_']
            layName = layName.lower()
            # --获取原稿线宽
            org_width = float(rowDir['FINISH_LW_'])
            # --获取补偿值
            # compensate = self.get_compensate(layName)
            compensate = 0

            # --获取菲林线宽
            # line_width = org_width + compensate
            line_width = float(rowDir['workLineWid'])
            # --获取原稿间距
            org_space = float(rowDir['FINISH_LS_'])
            # --获取菲林间距
            # line_space = org_space - compensate
            line_space = float(rowDir['workLineSpc'])
            # --获取参考层
            refers = rowDir['REF_LAYER_']
            refers = refers.lower().split('&')
            if len(refers) == 1:
                refers.append('None')
            # --获取欧姆值
            ohms = str(rowDir['CUSIMP'])
            # --层别列：
            item = QtGui.QTableWidgetItem()
            self.table_Item(item, layName, rowNum=rowNum, colNum=0, brush_bg=brush_bg)
            # --线宽列
            item = QtGui.QTableWidgetItem()
            self.table_Item(item, str(line_width), rowNum=rowNum, colNum=1)
            # --间距列
            item = QtGui.QTableWidgetItem()
            self.table_Item(item, str(line_space), rowNum=rowNum, colNum=2)
            # --参考1
            item = QtGui.QTableWidgetItem()
            self.table_Item(item, refers[0], rowNum=rowNum, colNum=3)
            # --参考2
            item = QtGui.QTableWidgetItem()
            self.table_Item(item, refers[1], rowNum=rowNum, colNum=4)
            # --原稿线宽
            item = QtGui.QTableWidgetItem()
            self.table_Item(item, str(org_width), rowNum=rowNum, colNum=5)
            # --原稿间距
            item = QtGui.QTableWidgetItem()
            self.table_Item(item, str(org_space), rowNum=rowNum, colNum=6)
            # --欧姆值
            item = QtGui.QTableWidgetItem()
            self.table_Item(item, ohms, rowNum=rowNum, colNum=7)
            # --补偿值
            item = QtGui.QTableWidgetItem()
            self.table_Item(item, str(compensate), rowNum=rowNum, colNum=8)
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
            # layDict = {
            #     'layer'     : layer,
            #     'line_width': line_width,
            #     'line_space': line_space,
            #     'refer1'    : refer1,
            #     'refer2'    : refer2,
            #     'org_width' : org_width,
            #     'org_space' : org_space,
            #     'ohms'      : float(ohms),
            #     'compensate': compensate,
            # }
            # infoList.append(layDict)

    def On_cellChange(self):
        """
        补偿值列编辑后，更新tableWidget
        :return:
        :rtype:
        """
        # --先断开信号的连接,以免在下面再次修改item时发生递归死循环事件发生
        self.disconnect(self.ui.tableWidget, QtCore.SIGNAL("cellChanged(int, int)"), self.On_cellChange)
        # --获取选中的物件，若没有选中直接return
        items = self.ui.tableWidget.selectedItems()
        if len(items) == 0:
            # --退出前，再次启动信号连接
            self.connect(self.ui.tableWidget, QtCore.SIGNAL("cellChanged(int, int)"), self.On_cellChange)
            return
        # --获取选中的行信息，行号，列号
        selRow = items[0].row()
        selCol = 8
        item_text = self.ui.tableWidget.item(selRow, selCol).text()
        # --获取选择行的补偿信息
        try:
            finishComp = float(item_text)
            if finishComp < 0:
                msg_box = msgBox()
                msg_box.critical(self, '警告', '第%d行%d列 补偿值 %s 不是正数，请修改!' % (selRow + 1, selCol + 1, item_text),
                    QMessageBox.Ok)
                self.ui.tableWidget.item(selRow, selCol).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                self.connect(self.ui.tableWidget, QtCore.SIGNAL("cellChanged(int, int)"), self.On_cellChange)
                return False
            # --重新更新UI数据
            self.refreshTableWidget(selRow, finishComp)
        except ValueError:
            msg_box = msgBox()
            msg_box.critical(self, '警告', '第%d行%d列 补偿值 %s 不是有效数字，请修改!' % (selRow + 1, selCol + 1, item_text),
                QMessageBox.Ok)
            self.ui.tableWidget.item(selRow, selCol).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
            # --退出前，再次启动信号连接
            self.connect(self.ui.tableWidget, QtCore.SIGNAL("cellChanged(int, int)"), self.On_cellChange)
            return False
        # --退出前，再次启动信号连接
        self.connect(self.ui.tableWidget, QtCore.SIGNAL("cellChanged(int, int)"), self.On_cellChange)

    def refreshTableWidget(self, Row, Value):
        """
        更新当前行信息
        :param Row:
        :param Value:
        :return:
        """
        # --原稿线宽
        line_width_org = self.ui.tableWidget.item(Row, 5).text()
        # --原稿间距
        line_space_org = self.ui.tableWidget.item(Row, 6).text()
        # --层别名
        layer = self.ui.tableWidget.item(Row, 0).text()
        # --更新线宽列
        item = QtGui.QTableWidgetItem()
        line_width = float(line_width_org) + float(Value)
        self.table_Item(item, str(line_width), rowNum=Row, colNum=1)
        # --更新间距列
        line_space = float(line_space_org) - float(Value)
        item = QtGui.QTableWidgetItem()
        self.table_Item(item, str(line_space), rowNum=Row, colNum=2)
        # # --更新测试pad大小 -- 取消测试Pad额外的补偿
        # outer = ['l1', 'l%s' % self.layer_number]
        # if layer in outer:
        #     self.testSize = 24 + float(Value)
        # --清空选中的行
        self.ui.tableWidget.clearSelection()

    def set_UI_by_JOB(self):
        """
        通过料号DO_INFO获取信息并填充主界面参数
        :return:
        :rtype:
        """
        self.viaSize = 9.843
        self.viaTilt = 9.843
        self.pthSize = 19.685
        self.npSize = 45.276
        self.antiSize = 36
        # --获取补偿值
        # compensate = self.get_compensate('l1', compType='Pad')
        compensate = 0
        # self.testSize = 24 + compensate
        # self.testSize = 'rect%sx%s' % (23.6 + compensate, 15.6 + compensate)
        self.testSize = 'rect%sx%s' % (20 + compensate, 8 + compensate)


    def get_table_widget_info(self):
        """
        从tableWidget中获取信息
        :return:
        :rtype:
        """
        infoList = []
        infoAll = []
        ohmsList = []
        selList = []
        reRowList = []

        # --TODO 如果没有选中层别，则默认选中所有层别,运用生成器表达式，节省内存
        #selItems = self.ui.tableWidget.selectedItems()
        #items = (self.ui.tableWidget.item(row, 0) for row in range(self.ui.tableWidget.rowCount()))
        #for selObj in items:
            ## --获取选中的行selRow
            #selRow = selObj.row()
            #selCol = selObj.column()
            ## --层别列
            #item = self.ui.tableWidget.item(selRow, 0)
            #layer = str(item.text())
            ## --线宽列
            #item = self.ui.tableWidget.item(selRow, 1)
            #line_width = float(item.text())
            ## --间距列
            #item = self.ui.tableWidget.item(selRow, 2)
            #line_space = float(item.text())
            ## --参考1
            #item = self.ui.tableWidget.item(selRow, 3)
            #refer1 = str(item.text())
            ## --参考2
            #item = self.ui.tableWidget.item(selRow, 4)
            #refer2 = str(item.text())
            ## --原稿线宽
            #item = self.ui.tableWidget.item(selRow, 5)
            #org_width = float(item.text())
            ## --原稿间距
            #item = self.ui.tableWidget.item(selRow, 6)
            #org_space = float(item.text())
            ## --欧姆值
            #item = self.ui.tableWidget.item(selRow, 7)
            #ohms = float(item.text())
            #if ohms not in ohmsList:
                #ohmsList.append(ohms)
            ## --补偿值
            #item = self.ui.tableWidget.item(selRow, 8)
            #compensate = float(item.text())
            #layDict = {
                #'layer': layer,
                #'line_width': line_width,
                #'line_space': line_space,
                #'refer1': refer1,
                #'refer2': refer2,
                #'org_width': org_width,
                #'org_space': org_space,
                #'ohms': ohms,
                #'compensate': compensate,
            #}
            #if selObj.isSelected() or len(selItems) == 0:
                #infoList.append(layDict)
            ## --所有阻抗信息存入一个列表
            #infoAll.append(layDict)
        
        self.parm['adjacent_layer'] = []
        
        dic_array_info = {}
        for info in self.dic_item_value[u"阻抗及补偿信息"]:
            # if info[0] == "1":
            if not dic_array_info.has_key(info[1]):                    
                dic_array_info[info[1]] = [info]
            else:
                dic_array_info[info[1]].append(info)            
            
        for key, values in dic_array_info.iteritems():
            
            infoList = []
            ohmsList = []
            selList = []
            
            for array_info in values:
                ohms = float(array_info[9])
                if ohms not in ohmsList:
                    ohmsList.append(ohms)
                layer, line_width, line_space, refer1, refer2, org_width, org_space, ohms = array_info[2:10]
                if refer1 == "None":
                    refer1 = str(refer2.lower())
                    refer2 = "None"
                    
                layDict = {
                    'layer': layer.lower(),
                    'line_width': float(line_width),
                    'line_space': float(line_space),
                    'refer1': refer1.lower() if refer1 != "None" else refer1,
                    'refer2': refer2.lower() if refer2 != "None" else refer2,
                    'org_width': float(org_width),
                    'org_space': float(org_space),
                    'ohms': float(ohms),
                    'compensate': 0,
                }
                if str(array_info[0]) == "1":
                    infoList.append(layDict)
                    
                infoAll.append(layDict)

            # --为节省空间，尽量错开同一层别不同走线,对阻抗信息进行重排
            for ohms in ohmsList:
                for layDict in infoList:
                    ohms_ = layDict['ohms']
                    if ohms_ == ohms:
                        selList.append(layDict)
    
            # --若有相邻走线层，需要错开
            reRowList += self.insert_adjacent(selList)
        
        # --将infoAll赋值到impAll
        self.parm['impAll'] = infoAll        
        return reRowList

    def insert_adjacent(self, selList):
        """
        在相邻层之间插入其它层，以错开相邻层
        :return:
        :rtype:
        """
        # --相邻走线层中间错开
        pre_refer1 = None
        pre_refer2 = None
        pre_dict = None
        outer = ['l1', 'l%s' % self.layer_number]
        insert_list = []
        before_list = []
        after_list = []
        for count, layDict in enumerate(selList):
            layer = layDict['layer']
            refer1 = layDict['refer1']
            refer2 = layDict['refer2']
            if layer in [pre_refer1, pre_refer2]:
                insert_list = [pre_dict, layDict]
                before_list = selList[:count - 1]
                if count < len(selList) - 1:
                    after_list = selList[count + 1:]
            pre_refer1 = refer1
            pre_refer2 = refer2
            pre_dict = layDict

        # --相邻层存入parm,后续常用
        self.parm['adjacent_layer'] += [layerDict['layer'] for layerDict in insert_list]
        if len(insert_list):
            insert_flag = True
            # --插入相邻层时，先不考虑外层
            for layDict in after_list:
                after_layer = layDict['layer']
                if after_layer not in outer and insert_flag:
                    insert_list.insert(1, layDict)
                    after_list.remove(layDict)
                    insert_flag = False
                    break
            for layDict in reversed(before_list):
                before_layer = layDict['layer']
                if before_layer not in outer and insert_flag:
                    insert_list.insert(1, layDict)
                    before_list.remove(layDict)
                    insert_flag = False
                    break
            # --若有没内层可以插入，才考虑外层
            if insert_flag:
                for layDict in after_list:
                    if insert_flag:
                        insert_list.insert(1, layDict)
                        insert_flag = False
                    else:
                        insert_list.append(layDict)
                for layDict in reversed(before_list):
                    if insert_flag:
                        insert_list.insert(1, layDict)
                        insert_flag = False
                    else:
                        insert_list.insert(0, layDict)
            else:
                # --列表拼接
                insert_list = before_list + insert_list + after_list
            return insert_list
        else:
            # --没有相邻层，直接返回原列表
            return selList

    def convert_layer_thick(self):
        """
        生成层别:铜厚的字典
        :return:
        :rtype:
        """
        CU_WEIGHT = dict()
        FINISH_THICKNESS = dict()
        for line_dict in self.sqlDic:
            layer_name = line_dict['LAYER_NAME']
            cu_weight = float(line_dict['CU_WEIGHT'])
            finish_thickness = float(line_dict['FINISH_THICKNESS'])
            CU_WEIGHT[layer_name] = cu_weight
            FINISH_THICKNESS[layer_name] = finish_thickness
        return CU_WEIGHT, FINISH_THICKNESS


    def get_compensate(self, layer, compType='Line'):
        """
        传入层别，获取补偿值
        :param layer: 层名
        :param compType: 补偿类型（Line | Pad）
        :return: float
        """

        if layer in self.layerMode['inn']:
            loopList = self.matchComp[u'内层补偿']
        elif layer in self.layerMode['sec']:
            loopList = self.matchComp[u'次外层补偿']
        elif layer in self.layerMode['out']:
            loopList = self.matchComp[u'外层补偿']
        else:
            loopList = self.matchComp

        if compType == 'Line':
            compensate = self.getCompensate_Line(layer, loopList)
        else:
            compensate = self.getCompensate_Pad(layer, loopList)
        return compensate

    def getCompensate_Line(self, layeyKey, loopCompList):
        """
        循环并获取线的补偿数据（用户阻抗线的补偿）
        :param layeyKey: 层名
        :return: float
        """
        layeyKey = layeyKey.upper()
        compMax = 0

        for layDict in loopCompList:
            if layeyKey in layDict.keys():
                # --循环等级，取出最大的一个补偿（按大的补偿）
                for level in layDict[layeyKey].keys():
                    if layeyKey.lower() in self.layerMode['inn']:
                        if layDict[layeyKey][level][u'稀疏区'] > compMax:
                            compMax = layDict[layeyKey][level][u'稀疏区']
                    else:
                        # 正片，且不是次外层
                        if self.getFlow == u'正片' and layeyKey.lower() not in self.layerMode['sec']:
                            if layDict[layeyKey][level][u'稀疏区'] > compMax:
                                compMax = layDict[layeyKey][level][u'稀疏区']
                        else:
                            if layDict[layeyKey][level][u'基础补偿'] > compMax:
                                compMax = layDict[layeyKey][level][u'基础补偿']

                return compMax
                break
        return 0

    def getCompensate_Pad(self, layeyKey, loopCompList):
        """
        循环并获取Pad的补偿数据(用于外层pad补偿）
        :param layeyKey: 层名
        :return: float
        """
        layeyKey = layeyKey.upper()
        compMax = 0
        for layDict in loopCompList:
            if layeyKey in layDict.keys():
                # --循环等级，取出最大的一个补偿（按大的补偿）
                for level in layDict[layeyKey].keys():
                    # 正片，且不是次外层
                    if self.getFlow == u'正片' and layeyKey.lower() not in self.layerMode['sec']:
                        if layDict[layeyKey][level][u'线路开窗Pad'] > compMax:
                            compMax = layDict[layeyKey][level][u'线路开窗Pad']
                    else:
                        if layDict[layeyKey][level][u'SMD小于等于12补偿'] > compMax:
                            compMax = layDict[layeyKey][level][u'SMD小于等于12补偿']
                # return u'匹配到的值不唯一'
                return compMax
                break
        return 0

    def table_Item(self, obj, text, rowNum=None, colNum=None, foreColor='black', brush_bg=None):
        """
        在tableWidget中加入普通的item控件
        :param obj: 控件引用
        :param text: 控件上的文本
        :param rowNum: 传入需要放置的行号
        :param colNum: 传入需要放置的列号
        :param foreColor: 传入前景颜色
        :param brush_bg: 传入背景画刷
        :return:
        """
        # --设置tabWidgetItem控件不可编辑
        obj.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        # --位置
        self.ui.tableWidget.setItem(rowNum, colNum, obj)
        # --设置文字居中
        obj.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter)
        # --写入文本信息
        obj.setText(text)
        if brush_bg:
            # --如果传入的参数有指定背景刷，则设定背景
            obj.setBackground(brush_bg)
        # --根据传入的颜色设置样式（前景色）
        brush = QtGui.QBrush(QtGui.QColor(foreColor))
        brush.setStyle(QtCore.Qt.NoBrush)
        obj.setForeground(brush)

    def runOpt_DFM(self):
        """
        Run 相关DFM处理图形（ring、间距、绿油桥）
        :return: None
        """
        # --去除重孔（临时的修改策略）
        # --获取所有钻孔层
        ppLayer = self.GEN.GET_ATTR_LAYER('drill', job=self.JOB)
        ppLayer = ';'.join(ppLayer) + ';lp'
        self.GEN.COM('chklist_single,action=valor_dfm_nfpr,show=no')
        self.GEN.COM('chklist_cupd,chklist=valor_dfm_nfpr,nact=1,params=((pp_layer=%s)'
                     '(pp_delete=Duplicate\;Drilled Over)(pp_work=Features)'
                     '(pp_drill=PTH\;NPTH\;Via\;PTH - Pressfit\;Via - Laser\;Via - Photo)'
                     '(pp_non_drilled=No)(pp_in_selected=All)(pp_remove_mark=Remove)),mode=regular' % ppLayer)
        self.GEN.COM('chklist_run,chklist=valor_dfm_nfpr,nact=1,area=profile')
        self.GEN.COM('chklist_close,chklist=valor_dfm_nfpr,mode=hide')

        def runGenesisDFM():
            # --优化间距、Ring环
            self.GEN.COM('chklist_single,action=valor_dfm_sigopt,show=no')
            self.GEN.COM(
                'chklist_cupd,chklist=valor_dfm_sigopt,nact=1,params=((pp_layer=.type=signal&context=board&side=top|bottom)'
                '(pp_min_pth_ar=5)(pp_opt_pth_ar=5)(pp_min_via_ar=5)(pp_opt_via_ar=5)(pp_min_microvia_ar=0)'
                '(pp_opt_microvia_ar=0)(pp_min_spacing=4)(pp_opt_spacing=4)(pp_min_p2p_spacing=4)'
                '(pp_opt_p2p_spacing=4)(pp_min_line=5)(pp_opt_line=10)(pp_nd_percent=25)(pp_abs_min_line=5)'
                '(pp_min_pth2c=6)(pp_selected=All)(pp_work_on=Pads\;SMDs\;Drills)(pp_modification=PadUp\;Shave)),'
                'mode=regular')
            self.GEN.COM('chklist_run,chklist=valor_dfm_sigopt,nact=1,area=profile')
            self.GEN.COM('chklist_close,chklist=valor_dfm_sigopt,mode=hide')

            # --优化绿油桥 frontline_dfm_smo
            self.GEN.COM('chklist_single,action=valor_dfm_smcc,show=no')
            self.GEN.COM(
                'chklist_cupd,chklist=valor_dfm_smcc,nact=1,params=((pp_layer=.type=solder_mask&context=board&side=top|bottom)'
                '(pp_min_clear=0.5)(pp_opt_clear=0.5)(pp_min_cover=2.2)(pp_opt_cover=3)(pp_bridge=3)'
                '(pp_selected=All)(pp_use_mask=Yes)(pp_use_shave=Yes)),mode=regular')
            self.GEN.COM('chklist_run,chklist=valor_dfm_smcc,nact=1,area=profile')
            self.GEN.COM('chklist_close,chklist=valor_dfm_smcc,mode=hide')

        def runInCAMDFM():
            # --优化间距、Ring环（包括内层）
            self.GEN.COM('chklist_single,show=no,action=valor_dfm_new_sigopt')
            self.GEN.COM(
                'chklist_cupd,chklist=valor_dfm_new_sigopt,nact=1,params=((pp_layer=.type=signal&context=board)'
                '(pp_action=AR\;Spacing\;Bus spacing\;Drill to copper)'
                '(pp_pad=Shave\;Enlarge\;Reshape\;Connect drilled)(pp_smd=Shave)'
                '(pp_bga=Shave BGA pads)(pp_trace=)(pp_surface=None)(pp_min_pth_ar=5)'
                '(pp_opt_pth_ar=5)(pp_min_pth2c=8)(pp_opt_pth2c=8)(pp_min_via_ar=5)(pp_opt_via_ar=5)'
                '(pp_min_via2c=6.5)(pp_opt_via2c=7)(pp_min_microvia_ar=0)(pp_opt_microvia_ar=0)'
                '(pp_min_microvia2c=0)(pp_opt_microvia2c=0)(pp_min_npth2c=8)(pp_opt_npth2c=10)'
                '(pp_min_rout2c=8)(pp_opt_rout2c=10)(pp_min_spacing=4)(pp_opt_spacing=4)(pp_minimal_line_w=5)'
                '(pp_optimal_line_w=5)(pp_minimal_surf_w=4.5)(pp_min_peelable=10)(pp_minimal_patch_w=4)(pp_selected=All)),mode=regular')
            # --允许多削SMD
            self.GEN.COM(
                'chklist_erf_variable,chklist=valor_dfm_new_sigopt,nact=1,variable=limit_smd_shaving,value=1,options=0')
            self.GEN.COM('chklist_cnf_act,chklist=valor_dfm_new_sigopt,nact=1,cnf=no')
            self.GEN.COM('chklist_run,chklist=valor_dfm_new_sigopt,nact=1,area=global,async_run=yes')

            # --优化绿油桥 frontline_dfm_smo
            self.GEN.COM('chklist_single,show=no,action=frontline_dfm_smo')
            self.GEN.COM(
                'chklist_cupd,chklist=frontline_dfm_smo,nact=1,params=((pp_layer=.type=signal|mixed&side=top|bottom)'
                '(pp_min_clear=0.5)(pp_opt_clear=1.5)(pp_min_cover=2.51)(pp_opt_cover=3)(pp_min_bridge=3)'
                '(pp_opt_bridge=3)(pp_selected=All)(pp_use_mask=Yes)(pp_use_shave=Yes)(pp_shave_cu=)'
                '(pp_rerout_line=)(pp_min_cu_width=5)(pp_min_cu_spacing=2.5)(pp_min_pth_ar=5)(pp_min_via_ar=5)'
                '(pp_fix_coverage=PTH\;Via\;NPTH\;SMD\;BGA)(pp_fix_bridge=PTH\;Via\;NPTH\;SMD\;BGA)'
                '(pp_split_clr_for_pad=)(pp_partial=SMD)(pp_gasket_smd_as_regular=1)(pp_gasket_bga_as_regular=1)'
                '(pp_gasket_pth_as_regular=4.1)(pp_gasket_via_as_regular=1)(pp_do_small_clearances=)'
                '(pp_handle_same_size=Same Size Clearance)(pp_handle_embedded_as_regular=)'
                '(pp_partial_embedded_mode=Partial Embedded)),mode=regular')
            self.GEN.COM('chklist_cnf_act,chklist=frontline_dfm_smo,nact=1,cnf=no')
            self.GEN.COM('chklist_run,chklist=frontline_dfm_smo,nact=1,area=global,async_run=yes')


        if self.GEN.getEnv()['software'] == 'genesis':
            runGenesisDFM()
        else:
            runInCAMDFM()

        return

    def loopAllsignals(self):
        """
        循环所有signal层并提升部分除surface （正负片）的顺序
        :return: None
        """
        tmpCopyLay = '++loop_cp++'
        # --通过层过滤器，选择指定类型层列表
        allList = self.GEN.GET_FILTER_LAYERS(side='top|bottom|inner')
        # --循环所有signal层并提升部分除surface （正负片）的顺序
        for sigLay in allList:
            self.GEN.WORK_LAYER(sigLay)
            self.GEN.FILTER_SET_TYP('line\;pad\;arc\;text', reset=1)
            self.GEN.FILTER_SET_POL('positive')
            self.GEN.FILTER_SELECT()
            if self.GEN.GET_SELECT_COUNT() > 0:
                self.GEN.DELETE_LAYER(tmpCopyLay)
                self.GEN.SEL_MOVE(tmpCopyLay)
                self.GEN.WORK_LAYER(tmpCopyLay)
                self.GEN.SEL_MOVE(sigLay)
        # --还原过滤器
        self.GEN.DELETE_LAYER(tmpCopyLay)
        self.GEN.FILTER_RESET()
        return True


if __name__ == '__main__':
    # app = QtGui.QApplication(sys.argv)
    myapp = MainWindow()

    # --修改尺寸，并以桌面居中形式弹出
    myapp.resize(830, 666)
    # --定义窗体属性
    #myapp.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint |  # 使能最小化按钮
                         #QtCore.Qt.WindowMaximizeButtonHint |  # 使能最大化按钮
                         #QtCore.Qt.WindowCloseButtonHint |  # 使能关闭按钮
                         #QtCore.Qt.WindowStaysOnTopHint)  # 窗体总在最前端
    # 先将窗口放到屏幕外，可避免移动窗口时的闪烁现象。
    myapp.move(myapp.width() * -2, 0)
    myapp.show()

    desktop = QtGui.QApplication.desktop()
    x = (desktop.width() - myapp.frameSize().width()) / 2
    y = (desktop.height() - myapp.frameSize().height()) / 2

    # --从屏幕外移回
    myapp.move(x, y)

    app.exec_()
    sys.exit(0)

"""
__END__:
日期  ：2022.06.23
更新人：Chuang.Liu
版本  ：V4.1
更新内容：
1、修复一堆的bug（特别针对有背钻的部分）

日期  ：2022.06.27
更新人：Chuang.Liu
版本  ：V4.2
更新内容：
1、又修复一堆的bug（还是针对有背钻的部分）
2、并按张莹要求，优化当外层线路层时，不设计基材位置的接地孔（故将loss_hole_pg symbol 拆分）

日期  ：2022.06.28
更新人：Chuang.Liu
版本  ：V4.3
更新内容：
1、更新阻焊开窗（前版本设计为下油，此版本起，要求不下油，全部开出）
2、修改外层测试Pad 大小，按rect8x20mm + 外层补偿值进行设计
3、增加补偿值自动匹配逻辑

"""
