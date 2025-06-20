#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:SingleBoardSetMaking.py
   @author:zl
   @time:2022/08/15 16:01
   @software:PyCharm
   @desc:
"""
import os
import re
import sys

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import SingleBoardSetMakingUI as ui

import genClasses as gen
import ZL_mysqlCon as zlsql

import res_rc


class SingleBoardSetMaking():
    def __init__(self):
        num = job.SignalNum
        if num != 1:
            QMessageBox.warning(None, 'infomation', '该料号不是单面板!')
            sys.exit()
        form.label.setText("<font style='font-weight:bold;'>JOB:<font style='color:green;'>%s</font></font>" % jobname)
        form.boardnum_label.setText('1')
        self.bz_type = '软硬结合板'
        if re.search(r'^fs', jobname) or jobname[2] == 'f':
            self.bz_type = '纯软板'
        form.boardtype_label.setText(self.bz_type)
        form.comboBox.addItems(["电池板", "摄像头板"])
        form.comboBox_2.addItems(["网格", "横砖块", "竖砖块", "铜皮", "六边形"])
        form.comboBox_3.addItems(["黑色", "黄色"])
        form.comboBox_4.addItems(["OSP", "AU", "沉金+OSP"])
        form.lineEdit.setText("0")
        form.lineEdit_2.setText(SetMaking().customercode)
        form.pushButton.clicked.connect(self.ScriptRun)
        form.pushButton_2.clicked.connect(lambda: sys.exit())
        # xcenter = (app.desktop().width() - widget.geometry().width()) / 2
        # ycenter = (app.desktop().height() - widget.geometry().height()) / 2
        # widget.move(xcenter, ycenter)

    def ScriptRun(self):
        widget.hide()
        self.making = SetMaking()
        self.making.setCusotmerCode()
        self.making.initStep()
        self.making.do_sm()
        self.making.addSymbols()
        QMessageBox.information(None, '提示', '脚本执行完毕！', QMessageBox.Ok)
        sys.exit()


class SetMaking():
    def __init__(self):
        self.step = step
        self.signals = job.SignalLayers
        self.silk_lays = job.matrix.returnRows('board', 'silk_screen')
        self.soldmask_lays = job.matrix.returnRows('board', 'solder_mask')
        self.proxmin = self.step.profile2.xmin
        self.proxmax = self.step.profile2.xmax
        self.proymin = self.step.profile2.ymin
        self.proymax = self.step.profile2.ymax
        self.soldmask_list, self.cov_list = [], []
        for lay in self.soldmask_lays:
            if lay in ('cm', 'sm'):
                self.soldmask_list.append(lay)
            if lay in ('cov-c', 'cov-s'):
                self.cov_list.append(lay)
        self.current_customercode = form.lineEdit_2.text().upper()
        self.isNVT = self.isXWD = 0
        if self.current_customercode == 'JRDX075':
            self.isNVT = 1
        if self.current_customercode == 'JRDS205':
            self.isXWD = 1
        if form.comboBox.currentText() == '电池板':
            self.jz_type = 'battery'
            self.hi_line = 500
            self.out_line = 501
            self.hi_dis = 1100
            if self.isNVT:
                self.hi_dis = 800
        else:
            self.jz_type = 'camera'
            self.hi_line = 101
            self.out_line = 101
            self.hi_dis = 400

        if form.comboBox_2.currentText() == '网格':
            self.fill_sur = 'grid'
        elif form.comboBox_2.currentText() == '横砖块':
            self.fill_sur = 'hbrack'
        elif form.comboBox_2.currentText() == '竖砖块':
            self.fill_sur = 'vbrack'
        elif form.comboBox_2.currentText() == '六边形':
            self.fill_sur = 'lbx'
        else:
            self.fill_sur = 'surface'
        if form.comboBox_3.currentText() == '黑色':
            self.cov_colour = 'black'
        else:
            self.cov_colour = 'yellow'
        if form.comboBox_4.currentText() == 'OSP':
            self.surface_treament = 'osp'
        elif form.comboBox_4.currentText() == 'AU':
            self.surface_treament = 'au'
        else:
            self.surface_treament = 'au+osp'

    # 客户代码
    def __getattr__(self, item):
        if item == 'customercode':  # 表中的客户代码(已保存的)
            self.customercode = self.getCustomerCode()
            return self.customercode

    def getCustomerCode(self):
        sql = 'select customercode from fpc_jobinfo where jobname = %s'
        cursor.execute(sql, jobname)
        res = cursor.fetchone()
        if res:
            code = res[0]
        else:
            code = ''
        return code

    # 保存客户代码
    def setCusotmerCode(self):
        # 取当前客户代码
        attrnames = job.info.get('gATTRname')
        attrvals = job.info.get('gATTRval')
        for name, val in zip(attrnames, attrvals):
            if name == '.customer':
                thecustomer = val
                break
        if thecustomer != self.current_customercode:
            job.COM("set_attribute,type=job,job=%s,name1=,name2=,name3=,attribute=.customer,value=%s,units=inch" % (
                jobname, self.current_customercode))
        # 更新客户代码
        if self.customercode != self.current_customercode:
            # if self.current_customercode:
            try:
                sql = 'replace into fpc_jobinfo(jobname,customercode) values (%s,%s)'
                cursor.execute(sql, (jobname, self.current_customercode))
                dbcon.commit()
            except Exception as e:
                print(e)
                dbcon.rollback()

    # 清空相关层
    def initStep(self):
        self.step.initStep()
        for lay in self.signals + self.silk_lays + self.soldmask_lays:
            self.step.affect(lay)
        self.step.selectDelete()
        self.step.unaffectAll()

    def do_surface(self):
        if self.jz_type == 'battery':
            marginx = 0.2
            marginy = 0.2
        else:
            marginx = 0.3
            marginy = 0.3

        for lay in self.signals:
            self.step.affect(lay)
            # 铺实铜
            self.step.resetFill()
            self.step.srFill_2(step_margin_x=-0.1, step_margin_y=-0.1, sr_margin_x=marginx, sr_margin_y=marginy)
            self.step.unaffectAll()
            # oll外形加大600去掏空
            self.step.affect('tmp_zlsys')
            self.step.copyToLayer(lay, 'yes', size=600)
            self.step.unaffectAll()
            self.step.affect(lay)
            self.step.Contourize()
            self.step.selectFill(std_type='cross', min_brush=100)
            self.step.Contourize()
            self.step.unaffectAll()
            self.step.affect(lay)
            if self.fill_sur == 'grid':
                self.step.selectFill(type='standard', solid_type='surface', std_type='cross',
                                     std_line_width=self.hi_line,
                                     std_step_dist=self.hi_dis, std_indent='even', outline_draw='yes',
                                     outline_width=self.out_line)
                # 删除小段网格线
                self.step.setFilterTypes('line', 'positive')
                self.step.setFilterSlot(max_len=0.1)
                self.step.selectAll()
                self.step.resetFilter()
                if self.step.Selected_count():
                    self.step.selectDelete()
            elif self.fill_sur == 'hbrack':
                self.step.selectFill(type='pattern', dx=3.3, dy=3.6, solid_type='surface', symbol='qq',
                                     std_indent='even',
                                     cut_prims='yes')
            elif self.fill_sur == 'vbrack':
                self.step.selectFill(type='pattern', dx=3.6, dy=3.3, solid_type='surface', symbol='ww',
                                     std_indent='even',
                                     cut_prims='yes')
            elif self.fill_sur == 'lbx':
                self.step.selectFill(type='pattern', dx=8.55, dy=4.95, solid_type='surface', symbol='lbx_fill',
                                     std_indent='even', cut_prims='yes')
                # 去细丝
                self.step.selectResize(-150)
                self.step.selectResize(150)
            elif self.fill_sur == 'surface':
                self.step.COM(
                    "fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=cross,min_brush=100,use_arcs=yes,symbol=,dx=2.54,dy=2.54,x_off=0,y_off=0,std_angle=45,std_line_width=254,std_step_dist=1270,std_indent=odd,break_partial=yes,cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no")
                self.step.srFill_2(step_margin_x=0.25, step_margin_y=0.25, sr_margin_x=1.3, sr_margin_y=1.3)
            self.step.unaffectAll()
            # oll缩600填充
            self.step.affect('tmp_zlsys')
            self.step.setFilterTypes('surface', 'positive')
            self.step.selectAll()
            self.step.resetFilter()
            if self.step.Selected_count():
                self.step.copyToLayer(lay, size=-600)
            self.step.unaffectAll()

    # 阻焊
    def do_sm(self):
        for lay in self.soldmask_list:
            self.step.prof_to_rout(lay, 80)
            self.step.affect(lay)
            self.step.selectCutData()
            self.step.selectResize(400)
            self.step.unaffectAll()
            self.step.VOF()
            self.step.removeLayer(lay + '+++')
            self.step.VON()
        ##开窗层掏空
        for lay in ('cm-1open', 'sm-1open', 'cmopen', 'smopen'):
            if self.step.isLayer(lay):
                cmlay = lay.replace('open', '')
                self.step.truncate(lay)
                self.step.Flatten(lay, lay + '-pa')
                self.step.affect(lay + '-pa')
                self.step.copyToLayer(cmlay, 'yes')
                self.step.unaffectAll()
                self.step.affect(cmlay)
                self.step.Contourize()
                self.step.unaffectAll()
                self.step.VOF()
                self.step.removeLayer(lay + '-pa')
                self.step.removeLayer(lay + '-pa+++')
                self.step.VON()

    # 加oll上对应的冲孔
    def addSymbols(self):
        if not self.step.isLayer('oll'):
            QMessageBox.warning(None, "warning", '没有oll层!')
            sys.exit()
        self.step.VOF()
        self.step.removeLayer('tmp_zlsys')
        self.step.removeLayer('ck1')
        self.step.VON()
        self.step.Flatten('oll', 'tmp_zlsys')
        self.step.prof_to_rout('ck1', 400)
        self.step.affect('tmp_zlsys')
        self.step.setFilterTypes('line|arc')
        self.step.refSelectFilter('ck1')
        self.step.resetFilter()
        if self.step.Selected_count():
            self.step.selectDelete()
        info = self.step.DO_INFO('-t layer -e %s/%s/%s,units=mm' % (jobname, self.step.name, 'tmp_zlsys'))
        oll_syms = info.get('gSYMS_HISTsymbol')
        for sym in oll_syms:
            if re.match(r'(r|s)\d{2}10$', sym):
                self.filter_pad(sym, '10_tmplay')
            elif re.match(r'(r|s)\d{2}11$', sym):
                self.filter_pad(sym, '11_tmplay')
            elif re.match(r'(r|s)\d{2}12$', sym):
                self.filter_pad(sym, '12_tmplay')
            elif re.match(r'(r|s)\d{2}13$', sym):
                self.filter_pad(sym, '13_tmplay')
            elif re.match(r'(r|s)\d{2}14$', sym):
                self.filter_pad(sym, '14_tmplay')
            elif re.match(r'(r|s)\d{2}15$', sym):
                self.filter_pad(sym, '15_tmplay')
            elif re.match(r'(r|s)\d{2}16$', sym):
                self.filter_pad(sym, '16_tmplay')
            elif re.match(r'(r|s)\d{2,3}1$', sym):
                self.filter_pad(sym, '1_tmplay')
            elif re.match(r'(r|s)\d{2,3}2$', sym):
                self.filter_pad(sym, '2_tmplay')
            elif re.match(r'(r|s)\d{2,3}3$', sym):
                self.filter_pad(sym, '3_tmplay')
            elif re.match(r'(r|s)\d{2,3}4$', sym):
                self.filter_pad(sym, '4_tmplay')
            elif re.match(r'(r|s)\d{2,3}5$', sym):
                self.filter_pad(sym, '5_tmplay')
            elif re.match(r'(r|s)\d{2,3}6$', sym):
                self.filter_pad(sym, '6_tmplay')
            elif re.match(r'(r|s)\d{2,3}7$', sym):
                self.filter_pad(sym, '7_tmplay')
            elif re.match(r'(r|s)\d{2,3}8$', sym):
                self.filter_pad(sym, '8_tmplay')
            elif re.match(r'(r|s)\d{3}9$', sym):
                self.filter_pad(sym, '9_tmplay')
            else:
                continue

        self.step.selectCutData()
        self.step.unaffectAll()
        self.step.Flatten('ol', 'tmp_zlsys1')
        self.step.affect('tmp_zlsys1')
        self.step.setFilterTypes('line|arc')
        self.step.refSelectFilter('ck1')
        self.step.resetFilter()
        if self.step.Selected_count():
            self.step.selectDelete()
        self.step.selectCutData()
        self.step.unaffectAll()
        self.step.VOF()
        self.step.removeLayer('tmp_zlsys1+++')
        self.step.removeLayer('tmp_zlsys+++')
        self.step.removeLayer('ck1')
        self.step.VON()
        self.do_surface()

        for i in range(1, 17):
            layer = '%s_tmplay' % i
            if self.step.isLayer(layer):
                if i == 9:
                    self.step.affect(layer)
                    self.step.copyToLayer('mark1')
                    sym = 'setcstoolinghole_new.lx' if self.signals[0] == 'cs' else 'setsstoolinghole_new.lx'
                    self.step.selectChange(sym)
                    self.step.copyToLayer(self.signals[0])
                    self.step.unaffectAll()
                    self.step.affect('mark1')
                    if self.cov_colour == 'black' or self.surface_treament == 'osp':
                        for lay in self.cov_list:
                            self.step.copyToLayer(lay, size=391)
                    for lay in self.silk_lays:
                        self.step.copyToLayer(lay, size=1200)
                        self.step.copyToLayer(lay, 'yes', size=800)
                    self.step.unaffectAll()
                    self.step.removeLayer('mark1')
                if i == 10:
                    self.step.affect(layer)
                    self.step.copyToLayer('mark1')
                    self.step.selectChange('setcstoolinghole.lx')
                    self.step.copyToLayer(self.signals[0])
                    self.step.unaffectAll()
                    self.step.affect('mark1')
                    if self.cov_colour == 'black':
                        for lay in self.cov_list:
                            self.step.copyToLayer(lay, size=-410)
                    self.step.unaffectAll()
                    self.step.removeLayer('mark1')
                if i == 11:
                    self.step.affect(layer)
                    self.step.copyToLayer('mark1')
                    self.step.selectChange('csx-cm2')
                    for lay in self.soldmask_list:
                        self.step.copyToLayer(lay)
                    if self.soldmask_list:
                        self.step.selectChange('csx-cm')
                        self.step.copyToLayer(self.signals[0])
                    else:
                        self.step.selectChange('csx-cm1')
                        self.step.copyToLayer(self.signals[0])
                    self.step.unaffectAll()
                    self.step.affect('mark1')
                    for lay in self.cov_list:
                        self.step.copyToLayer(lay, size=-11)
                    for lay in ('skc', 'sks'):
                        if self.step.isLayer(lay):
                            self.step.copyToLayer(lay, size=3989)
                    self.step.unaffectAll()
                    self.step.removeLayer('mark1')
                if i == 1 or i == 2:
                    self.step.affect(layer)
                    self.step.copyToLayer(self.signals[0], size=2500)
                    cs_mark = self.signals[0]
                    if i == 1:
                        add2 = 999
                        if self.jz_type == 'battery':
                            add1 = 79
                        else:
                            add1 = 49
                    if i == 2:
                        add2 = 998
                        if self.jz_type == 'battery':
                            add1 = 78
                        else:
                            add1 = 48
                    self.step.copyToLayer(cs_mark, 'yes', size=1600)
                    self.step.copyToLayer(cs_mark, size=add1)
                    if self.cov_list:
                        self.step.copyToLayer(self.cov_list[0], size=add2)
                    self.step.unaffectAll()
                if i == 3 or i == 4:
                    cs_mark = self.signals[0]
                    if i == 3:
                        sk_mak = 'skc'
                        if self.jz_type == 'battery':
                            add2 = 1047
                            add3 = 47
                            if self.isNVT:
                                add2 = 1497
                            elif self.isXWD:
                                add2 = 2497
                        else:
                            add2 = 1027
                            add3 = 27
                            if self.isNVT:
                                add2 = 1477
                            elif self.isXWD:
                                add2 = 2477
                    if i == 4:
                        sk_mak = 'sks'
                        if self.jz_type == 'battery':
                            add2 = 1046
                            add3 = 46
                            if self.isNVT:
                                add2 = 1496
                            elif self.isXWD:
                                add2 = 2496
                        else:
                            add2 = 1026
                            add3 = 26
                            if self.isNVT:
                                add2 = 1476
                            elif self.isXWD:
                                add2 = 2476

                    self.step.affect(layer)
                    backpadsize = 2200
                    negativesize = 1200
                    csmarkpad = 600
                    zhnegpad = 2047
                    if i == 4:
                        if self.isNVT:
                            backpadsize = 2596
                            negativesize = 1796
                            csmarkpad = 996
                            zhnegpad = 2496
                        elif self.isXWD:
                            backpadsize = 3596
                            negativesize = 2796
                            csmarkpad = 1996
                            zhnegpad = 3496
                    if i == 3:
                        if self.isNVT:
                            backpadsize = 2597
                            negativesize = 1797
                            csmarkpad = 997
                            zhnegpad = 2497
                        elif self.isXWD:
                            backpadsize = 3597
                            negativesize = 2797
                            csmarkpad = 1997
                            zhnegpad = 3497

                    self.step.copyToLayer(cs_mark, size=backpadsize)
                    self.step.copyToLayer(cs_mark, 'yes', size=negativesize)
                    self.step.copyToLayer(cs_mark, size=csmarkpad)
                    if self.cov_list:
                        self.step.copyToLayer(self.cov_list[0], size=add2)
                    if self.step.isLayer(sk_mak):
                        self.step.copyToLayer(sk_mak, size=3997)
                    if self.soldmask_lays:
                        self.step.copyToLayer(self.soldmask_lays[0], 'yes', size=zhnegpad)
                        self.step.copyToLayer(self.soldmask_lays[0], size=add3)
                    if self.surface_treament == 'osp' and not self.isNVT and not self.isXWD:
                        self.step.selectChange('ospline')
                        self.step.copyToLayer(cs_mark)
                    if self.isXWD:
                        self.step.resetFilter()
                        self.step.setFilterTypes('pad')
                        self.step.selectSymbol('r1003\;r1004')
                        self.step.selectAll()
                        self.step.resetFilter()
                        if self.step.Selected_count():
                            self.step.selectChange('ospline2')
                            self.step.copyToLayer(cs_mark)
                        self.step.setFilterTypes('pad')
                        self.step.selectSymbol('r2003\;r2004')
                        self.step.selectAll()
                        self.step.resetFilter()
                        if self.step.Selected_count():
                            self.step.selectChange('ospline3')
                            self.step.copyToLayer(cs_mark)
                    self.step.unaffectAll()
                if i == 5:
                    self.step.affect(layer)
                    self.step.copyToLayer(self.signals[0], size=1400)
                    self.step.copyToLayer(self.signals[0], 'yes', size=1200)
                    if self.jz_type == 'battery':
                        self.step.copyToLayer(self.signals[0], size=75)
                    else:
                        self.step.copyToLayer(self.signals[0], size=45)
                    if self.cov_list:
                        self.step.copyToLayer(self.cov_list[0], size=795)
                    self.step.unaffectAll()
                if i == 16 and self.surface_treament == 'au+osp':
                    self.step.affect(layer)
                    if self.step.isLayer('cs'):
                        self.step.selectChange('jfn_add')
                        self.step.copyToLayer('cs')
                    if self.step.isLayer('cm'):
                        self.step.selectChange('jfn_cm')
                        self.step.copyToLayer('cm')
                    self.step.unaffectAll()
                self.step.removeLayer(layer)
        if self.surface_treament == 'au':
            tt_y = float("%.8f" % (self.proymax / 2))
            tt_x1 = 1.5
            tt_x2 = float("%.8f" % (self.proxmax - 1.5))
            self.step.VOF()
            self.step.removeLayer('mark3')
            self.step.VON()
            self.step.createLayer('mark3', ins_layer='ol')
            self.step.affect('mark3')
            self.step.addPad(tt_x1, tt_y, 's2301')
            self.step.addPad(tt_x2, tt_y, 's2301')
            self.step.unaffectAll()
            self.step.affect('tmp_zlsys')
            self.step.copyToLayer('mark3', 'yes', size=600)
            self.step.unaffectAll()
            self.step.affect('mark3')
            self.step.Contourize()
            self.step.copyToLayer(self.signals[0])
            self.step.unaffectAll()
            if self.signals[0] == 'cs':
                self.step.affect('cs')
                self.step.addPad(tt_x1, tt_y, 's2001', 'negative')
                self.step.addPad(tt_x2, tt_y, 's2001', 'negative')
                self.step.addPad(tt_x1, tt_y, 's600')
                self.step.addPad(tt_x2, tt_y, 's600')
                self.step.unaffectAll()
            if 'cov-c' in self.cov_list:
                self.step.affect('cov-c')
                self.step.addPad(tt_x1, tt_y, 'r1601')
                self.step.addPad(tt_x2, tt_y, 'r1601')
                self.step.unaffectAll()

        #  电池板连接筋位置添加
        if self.jz_type == 'battery':
            self.do_ljset('ljset')
        self.step.VOF()
        self.step.removeLayer('tmp_zlsys')
        self.step.removeLayer('tmp_zlsys1')
        self.step.removeLayer('mark1')
        self.step.removeLayer('mark3')
        self.step.VON()

    def do_ljset(self, lay):
        linewidth = 'r400'
        if self.current_customercode == 'JRDX075':
            linewidth = 'r600'
        elif self.current_customercode == 'JRDF072':
            linewidth = 'r1000'
        if self.step.isLayer(lay):
            self.step.Flatten(lay, lay + '-pa')
            self.step.affect(lay + '-pa')
            self.step.selectCutData()
            self.step.selectResize(-200)
            self.step.copyToLayer('lj-33')
            self.step.copyToLayer('lj-44')
            self.step.unaffectAll()
            self.step.Flatten('ol', 'ol-f')
            self.step.affect('ol-f')
            self.step.COM('sel_delete_atr,attributes=.rout_chain')
            self.step.selectChange(linewidth)
            self.step.copyToLayer('lj-33', 'yes')
            self.step.copyToLayer('lj-44', 'yes', size=200)
            self.step.unaffectAll()
            self.step.affect('lj-33')
            self.step.affect('lj-44')
            self.step.Contourize()
            self.step.selectFill(100, std_type='cross')
            self.step.Contourize()
            self.step.unaffectAll()
            self.step.affect(lay + '-pa')
            self.step.copyToLayer(self.signals[0], 'yes', size=-100)
            self.step.unaffectAll()
            if self.signals[0] == 'cs':
                self.step.affect('lj-33')
                self.step.copyToLayer(self.signals[0])
                self.step.unaffectAll()
            else:
                self.step.affect('lj-44')
                self.step.copyToLayer(self.signals[0])
                self.step.unaffectAll()
            self.step.removeLayer('ol-f')
            self.step.removeLayer(lay + '-pa')
            self.step.removeLayer('lj-33')
            self.step.removeLayer('lj-44')
            self.step.removeLayer(lay + '-pa+++')

    def filter_pad(self, *args):
        sym, lay = args[0], args[1]
        self.step.resetFilter()
        self.step.setFilterTypes('pad')
        self.step.selectSymbol(sym)
        self.step.selectAll()
        self.step.resetFilter()
        if self.step.Selected_count():
            self.step.moveSel(lay)


if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    stepname = os.environ.get('STEP')
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setWindowIcon(QIcon(":/res/demo.png"))
    app.setStyleSheet("QMessageBox{font-size:12pt;} QPushButton:hover{background:#99eeee;}")
    if not jobname:
        QMessageBox.warning(None, 'infomation', '请打开料号!')
        sys.exit()
    if stepname != 'set':
        QMessageBox.warning(None, 'infomation', '请在set中执行!')
        sys.exit()
    job = gen.Job(jobname)
    step = job.steps.get('set')
    dbcls = zlsql.DBConnect()
    dbcon = dbcls.connection
    cursor = dbcls.cursor
    form = ui.Ui_Form()
    widget = QWidget()
    form.setupUi(widget)
    making = SingleBoardSetMaking()
    widget.show()
    sys.exit(app.exec_())
