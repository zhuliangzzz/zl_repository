#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:SingleBoardPanelMaking.py
   @author:zl
   @time:2022/08/23 10:10
   @software:PyCharm
   @desc:
"""
import os
import re
import sys

import SingleBoardPanelMakingUI as ui

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

sys.path.append('/genesis/sys/scripts/zl/lib')
import genClasses as gen
import ZL_mysqlCon as zlsql

sys.path.append('/genesis/sys/scripts/zl/python/images')
import res_rc


class SingleBoardPanelMaking(object):
    def __init__(self):
        num = job.SignalNum
        if num != 1:
            QMessageBox.warning(None, 'infomation', '该料号不是单面板!')
            sys.exit()
        form.label.setText("<font style='color:green;font-weight:bold;'>JOB:%s\tStep:%s</font>" % (jobname, stepname))
        form.boardnum_label.setText('1')
        self.bz_type = '软硬结合板'
        if re.search(r'^fs', jobname) or jobname[2] == 'f':
            self.bz_type = '纯软板'
        self.panel = PanelMaking()
        if self.panel.serialLayer:
            form.lineEdit.setText('▲加序号' + self.panel.serialLayer + '层')
            form.lineEdit.setStyleSheet('color:#0000ff;')
        else:
            form.lineEdit.setText('▲未检测到板序号')
            form.lineEdit.setStyleSheet('color:#aaa;')
        # 尺寸列表 self.comboBox
        sizeArr = []
        if self.panel.prof_xsize == 500:
            sizeArr = ['500']
        elif self.panel.prof_xsize == 250:
            sizeArr = ['250']
        form.comboBox.addItems(sizeArr)
        form.boardtype_label.setText(self.bz_type)
        form.comboBox_2.addItems(["铜皮", "网格", "横砖块", "竖砖块", "六边形"])
        form.lineEdit_2.setText(self.panel.customercode)
        form.pushButton.clicked.connect(self.ScriptRun)
        form.pushButton_2.clicked.connect(lambda: sys.exit())
        xcenter = (app.desktop().width() - widget.geometry().width()) / 2
        ycenter = (app.desktop().height() - widget.geometry().height()) / 2
        widget.move(xcenter, ycenter)

    def ScriptRun(self):
        widget.hide()
        self.option_size = form.comboBox.currentText()
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
        self.customer = form.lineEdit_2.text().upper()
        if making.customer == 'JRDS205':
            self.panel.hi_dis = 800
        self.panel.setCustomerCode()
        self.panel.initStep()
        self.panel.do_surface()
        self.panel.do_corner()
        self.panel.do_tg_kb()
        self.panel.do_wz()
        self.panel.do_df_opr_id()
        self.panel.do_word_marks()
        self.panel.do_wz_mark()
        self.panel.do_cov()
        self.panel.do_film_marks()
        self.panel.do_addnb()
        QMessageBox.information(None, '提示', '脚本执行完毕！', QMessageBox.Ok)
        sys.exit()


class PanelMaking(object):
    def __init__(self):
        self.step = step
        self.username = job.user
        self.signals = job.SignalLayers
        self.silk_lays = job.matrix.returnRows('board', 'silk_screen')
        self.soldmask_lays = job.matrix.returnRows('board', 'solder_mask')
        self.soldmask_list, self.cov_list = [], []
        for lay in self.soldmask_lays:
            if lay in ('cm', 'sm'):
                self.soldmask_list.append(lay)
            if lay in ('cov-c', 'cov-s'):
                self.cov_list.append(lay)
        self.hi_line = 500
        self.out_line = 501
        self.hi_dis = 1100
        self.prof_xmin = self.step.profile2.xmin
        self.prof_xmax = self.step.profile2.xmax
        self.prof_ymin = self.step.profile2.ymin
        self.prof_ymax = self.step.profile2.ymax
        self.sr_xmin = step.sr2.xmin
        self.sr_ymin = step.sr2.ymin
        self.sr_xmax = step.sr2.xmax
        self.sr_ymax = step.sr2.ymax
        self.sr_xmin_t = step.sr2.xmin
        self.sr_ymin_t = step.sr2.ymin
        self.sr_xmax_t = step.sr2.xmax
        self.sr_ymax_t = step.sr2.ymax
        # profile size
        self.prof_xsize = step.profile2.xsize
        self.prof_ysize = step.profile2.ysize
        # profile center
        self.prof_xcenter = step.profile2.xcenter
        self.prof_ycenter = step.profile2.ycenter
        DBConnect = zlsql.DbConnect()
        self.connection = DBConnect.connection
        self.cursor = DBConnect.cursor

    def __getattr__(self, item):
        if item == 'serialLayer':
            self.serialLayer = self.getSerialLayer()
            return self.serialLayer
        # 客户代码
        if item == 'customercode':
            self.customercode = self.getCustomerCode()
            return self.customercode
        if item == 'doinfo':
            self.doinfo = self.doInfo()
            return self.doinfo

    # 清空相关层
    def initStep(self):
        self.step.initStep()
        for lay in self.signals + self.silk_lays + self.soldmask_lays:
            self.step.truncate(lay)

    # 加序号层
    def getSerialLayer(self):
        seriallayer = None
        for layer in ('css', 'cm', 'cs', 'ss', 'sm', 'sss'):
            if step.isLayer(layer) == 0:
                continue
            lines = step.INFO('-t layer -e %s/set/%s -d FEATURES,units=mm' % (jobname, layer))
            for line in lines:
                line.replace('\n', '').replace('\r', '')
                array = line.split()
                if len(array) > 10 and array[10] == '\'00\'':
                    seriallayer = layer
                    break
            if seriallayer:
                break
        return seriallayer

    # 查询客户代码
    def getCustomerCode(self):
        customercode = None
        sql = "select customercode from fpc_jobinfo where jobname = '%s'" % jobname
        self.cursor.execute(sql)
        array = self.cursor.fetchone()
        if array:
            customercode = array['customercode']
        return customercode

    # 更新客户代码
    def setCustomerCode(self):
        currentcode = form.lineEdit_2.text().upper()
        thecustomer = ''
        # 取当前料号的.customer属性值
        for name, val in zip(job.info.get('gATTRname'), job.info.get('gATTRval')):
            if name == '.customer':
                thecustomer = val
        if thecustomer != currentcode:
            # 将客户代码设置到料号的客户代码属性中 customer
            job.COM("set_attribute,type=job,job=%s,name1=,name2=,name3=,attribute=.customer,value=%s,units=inch" % (
                jobname, currentcode))
        # 如果当前客户代码和表中客户代码不一致 则更新
        if self.customercode != currentcode:
            sql = 'replace into fpc_jobinfo(jobname,customercode) values(%s,%s)'
            try:
                self.cursor.execute(sql, (jobname, currentcode))
                self.connection.commit()
            except Exception as e:
                self.connection.rollback()
                print(e)

    def doInfo(self):
        hashmap = job.DO_INFO(' -t step -e %s/%s,units=mm' % (jobname, stepname))
        return hashmap

    def do_surface(self):
        for lay in self.signals:
            string = str.join('\;', step.info.get('gSRstep'))
            self.step.affect(lay)
            # 铺实铜
            self.step.resetFill()
            self.step.srFill_2(step_margin_y=1, stop_at_steps=string)
            if making.fill_sur == 'grid':
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
            elif making.fill_sur == 'hbrack':
                self.step.selectFill(type='pattern', dx=3.3, dy=3.6, solid_type='surface', symbol='qq',
                                     std_indent='even',
                                     cut_prims='yes')
            elif making.fill_sur == 'vbrack':
                self.step.selectFill(type='pattern', dx=3.6, dy=3.3, solid_type='surface', symbol='ww',
                                     std_indent='even',
                                     cut_prims='yes')
            elif making.fill_sur == 'lbx':
                self.step.selectFill(type='pattern', dx=8.55, dy=4.95, solid_type='surface', symbol='lbx_fill',
                                     std_indent='even', cut_prims='yes')
                # 去细丝
                self.step.selectResize(-150)
                self.step.selectResize(150)
            self.step.resetFill()
            self.step.unaffectAll()

    # 拐角线
    def do_corner(self):
        mir = 'no'
        for layer in self.signals:
            mir = 'no' if layer == 'cs' else 'yes'
            self.step.affect(layer)
        self.step.addPad(self.prof_xmin, self.prof_ymin, 'dqjx', mirror=mir)
        self.step.addPad(self.prof_xmax, self.prof_ymin, 'dqjx', angle=270, mirror=mir)
        self.step.addPad(self.prof_xmin, self.prof_ymax, 'dqjx', angle=90, mirror=mir)
        self.step.addPad(self.prof_xmax, self.prof_ymax, 'dqjx', angle=180, mirror=mir)
        self.step.unaffectAll()

    def do_tg_kb(self):
        x1 = self.prof_xmin + 5
        x2 = self.prof_xmin + 10
        x3 = self.prof_xmin + 7
        x4 = self.prof_xmax - 5
        y1 = self.prof_ymin + 5
        y2 = self.prof_ymax - 5
        mir = 'no'
        for layer in self.signals:
            mir = 'no' if layer == 'cs' else 'yes'
            self.step.affect(layer)
        self.step.addPad(x1, y1, 'fpc.fx1', mirror=mir)
        self.step.addPad(x2, y1, 'fpc.fx1', mirror=mir)
        self.step.addPad(x4, y1, 'fpc.fx1', mirror=mir)
        self.step.addPad(x3, y2, 'fpc.fx1', mirror=mir)
        self.step.addPad(x4, y2, 'fpc.fx1', mirror=mir)
        self.step.unaffectAll()
        for layer in self.cov_list:
            self.step.affect(layer)
        self.step.VOF()
        self.step.addPad(x1, y1, 'r2000')
        self.step.addPad(x2, y1, 'r2000')
        self.step.addPad(x4, y1, 'r2000')
        self.step.addPad(x3, y2, 'r2000')
        self.step.addPad(x4, y2, 'r2000')
        self.step.VON()
        self.step.unaffectAll()

    # 文字孔
    def do_wz(self):
        x1 = self.prof_xmin + 27
        x2 = x1 + 5
        x3 = self.prof_xmin + 13
        x4 = self.prof_xmax - 13
        y1 = self.sr_ymin - 4.5
        y2 = self.sr_ymax + 4.5
        mir = 'no'
        for layer in self.signals:
            mir = 'no' if layer == 'cs' else 'yes'
            self.step.affect(layer)
        self.step.addPad(x1, y1, 'lh.7+1')
        self.step.addPad(x2, y1, 'lh.7+1')
        self.step.addPad(x4, y1, 'lh.7+1')
        self.step.addPad(x3, y2, 'lh.7+1')
        self.step.addPad(x4, y2, 'lh.7+1')
        self.step.addText(x1 - 0.7, y1 - 2.8, 'WZ', 0.889, 0.889, 0.4166666567, mirror=mir, fontname='fpc',
                          polarity='negative')
        self.step.addText(x2 - 0.7, y1 - 2.8, 'WZ', 0.889, 0.889, 0.4166666567, mirror=mir, fontname='fpc',
                          polarity='negative')
        self.step.addText(x4 - 0.7, y1 - 2.8, 'WZ', 0.889, 0.889, 0.4166666567, mirror=mir, fontname='fpc',
                          polarity='negative')
        self.step.addText(x3 - 0.7, y2 - 2.8, 'WZ', 0.889, 0.889, 0.4166666567, mirror=mir, fontname='fpc',
                          polarity='negative')
        self.step.addText(x4 - 0.7, y2 - 2.8, 'WZ', 0.889, 0.889, 0.4166666567, mirror=mir, fontname='fpc',
                          polarity='negative')
        step.unaffectAll()
        for layer in self.silk_lays:
            self.step.affect(layer)
        self.step.VOF()
        self.step.addPad(x1, y1, 'donut_r2800x2300')
        self.step.addPad(x2, y1, 'donut_r2800x2300')
        self.step.addPad(x4, y1, 'donut_r2800x2300')
        self.step.addPad(x3, y2, 'donut_r2800x2300')
        self.step.addPad(x4, y2, 'donut_r2800x2300')
        self.step.unaffectAll()
        self.step.VON()

    # 加菲林记录pad "AB123456789"
    def do_df_opr_id(self):
        x = self.prof_xmax - 55
        y = self.sr_ymin - 4.5
        for layer in self.signals:
            mir = 'no' if layer == 'cs' else 'yes'
            self.step.affect(layer)
        self.step.addPad(x, y, 'fpc.ab', mirror=mir)
        self.step.unaffectAll()

    # 字唛
    def do_word_marks(self):
        for layer in self.signals:
            mir = 'no' if layer == 'cs' else 'yes'
            self.step.affect(layer)
        wordm5_x = self.sr_xmax_t / 2 - 37
        wordm1_x = wordm5_x + 30 - 7
        wordm2_x = wordm5_x + 32.6 - 7
        wordm3_x = wordm5_x + 50 - 7
        wordm4_x = wordm5_x + 52.6 - 7
        wordm1_y = self.sr_ymin_t - 3.5
        self.step.addText(wordm1_x, wordm1_y, 'X', 2.235, 2.235, 1, mir, polarity='negative')
        self.step.resetAttr()
        self.step.addAttr_zl('.nomenclature')
        self.step.addAttr_zl('.orbotech_plot_stamp')
        # STRETCHX
        self.step.addText(wordm2_x, wordm1_y, 'STRETCHX', 2.032, 2.032, 1, mir, polarity='negative', attributes='yes')
        self.step.addText(wordm3_x, wordm1_y, 'Y', 2.235, 2.235, 1, mir, polarity='negative')
        # STRETCHY
        self.step.addText(wordm4_x, wordm1_y, 'STRETCHY', 2.032, 2.032, 1, mir, polarity='negative', attributes='yes')
        self.step.resetAttr()
        wordm5_x2 = 80
        wordm5_y = wordm1_y - 3
        words = making.customer + ' $$job $$layer ' + self.username + ' $$date'
        step.addText(wordm5_x2, wordm5_y, words, 1.800, 2.032, 1, mir, polarity='negative')
        self.step.unaffectAll()
        wordm5_x = 27
        wordm1_x = wordm5_x + 30 - 7
        wordm2_x = wordm5_x + 32.6 - 7
        wordm3_x = wordm5_x + 50 - 7
        wordm4_x = wordm5_x + 52.6 - 7
        wordm1_y = self.sr_ymin_t - 6
        for layer in self.silk_lays:
            mir = 'no' if layer == 'css' else 'yes'
            self.step.affect(layer)
            self.step.VOF()
            self.step.addText(wordm1_x, wordm1_y, 'X', 2.235, 2.235, 1, mir)
            self.step.resetAttr()
            self.step.addAttr_zl('.nomenclature')
            self.step.addAttr_zl('.orbotech_plot_stamp')
            # STRETCHX
            self.step.addText(wordm2_x, wordm1_y, 'STRETCHX', 2.032, 2.032, 1, mir, attributes='yes')
            self.step.addText(wordm3_x, wordm1_y, 'Y', 2.235, 2.235, 1)
            # STRETCHY
            self.step.addText(wordm4_x, wordm1_y, 'STRETCHY', 2.032, 2.032, 1, mir, attributes='yes')
            self.step.resetAttr()
            wordm5_x2 = 100
            words = making.customer + ' $$job $$layer ' + self.username + ' $$date'
            step.addText(wordm5_x2, wordm1_y, words, 1.800, 2.032, 1, mir)
            self.step.unaffectAll()
            self.step.VON()

    # 加正反字和十字mark
    def do_wz_mark(self):
        for layer in self.signals:
            sym = 'fpc.zheng' if layer == 'cs' else 'fpc.fan'
            self.step.affect(layer)
            self.step.addPad(13, 2.5, sym)
            panelwzpx1 = self.sr_xmin / 2  # 留边中心
            panelwzpx2 = self.prof_xmax - panelwzpx1
            panelwzpy1 = self.prof_ymax / 2 - self.prof_ymin / 2 - 62
            panelwzpy2 = self.prof_ymax / 2 - self.prof_ymin / 2 + 75
            self.step.addPad(panelwzpx1, panelwzpy1, 'fpc.wz1')
            self.step.addPad(panelwzpx2, panelwzpy1, 'fpc.wz1')
            self.step.addPad(panelwzpx1, panelwzpy2, 'fpc.wz1')
            # 20210827 zl 防错
            panelwzpy2_add = panelwzpy2 + 5
            self.step.addPad(panelwzpx2, panelwzpy2_add, 'fpc.wz1')
            self.step.unaffectAll()
            self.step.unaffectAll()
        for lay in self.silk_lays:
            sym = 'fpc.zheng' if lay == 'css' else 'fpc.fan'
            self.step.affect(lay)
            self.step.addPad(13, 2.5, sym)
            panelwzpx1 = self.sr_xmin / 2  # 留边中心
            panelwzpx2 = self.prof_xmax - panelwzpx1
            panelwzpy1 = self.prof_ymax / 2 - self.prof_ymin / 2 - 62
            panelwzpy2 = self.prof_ymax / 2 - self.prof_ymin / 2 + 75
            self.step.addPad(panelwzpx1, panelwzpy1, 'fpc.wz1')
            self.step.addPad(panelwzpx2, panelwzpy1, 'fpc.wz1')
            self.step.addPad(panelwzpx1, panelwzpy2, 'fpc.wz1')
            # 20210827 zl 防错
            panelwzpy2_add = panelwzpy2 + 5
            self.step.addPad(panelwzpx2, panelwzpy2_add, 'fpc.wz1')
            self.step.unaffectAll()
            self.step.unaffectAll()

    # 加上裁切线
    def do_cov(self):
        covlinemin_x = self.prof_xmin - 1
        covlinemin_y = self.prof_ymin - 1
        covlinemax_x = self.prof_xmax + 1
        covlinemax_y = self.prof_ymax + 1
        # 算set和set之间的距离x
        array, tmp_array = [], []
        for i in range(len(self.doinfo.get('gREPEATstep'))):
            array.append(self.doinfo.get('gREPEATxmin')[i])
            array.append(self.doinfo.get('gREPEATxmax')[i])
        array = sorted(array)
        i = 0
        while i < len(array) - 1:
            j1 = i
            j2 = i + 1
            i += 1
            tt = array[j2] - array[j1]
            if 0.8 <= tt < 25:
                tmp_array.append(tt)
        tmp_array = sorted(tmp_array)
        x_spacing = tmp_array[0] / 2 if len(tmp_array) > 0 else 0
        ###############
        # 算set与set之间的距离y
        array, tmp_array = [], []
        for i in range(len(self.doinfo.get('gREPEATstep'))):
            array.append(self.doinfo.get('gREPEATymin')[i])
            array.append(self.doinfo.get('gREPEATymax')[i])
        array = sorted(array)
        i = 0
        while i < len(array) - 1:
            j1 = i
            j2 = i + 1
            i += 1
            tt = array[j2] - array[j1]
            if 0.8 <= tt < 25:
                tmp_array.append(tt)
        tmp_array = sorted(tmp_array)
        y_spacing = tmp_array[0] / 2 if len(tmp_array) > 0 else 0
        ###################
        # 加线
        self.step.VOF()
        #
        for lay in self.cov_list:
            self.step.affect(lay)
        for i in range(len(self.doinfo.get('gREPEATstep'))):
            covline_x = self.doinfo.get('gREPEATxmax')[i] + x_spacing
            covline_y = self.doinfo.get('gREPEATymax')[i] + y_spacing
            if re.search(r'set', self.doinfo.get('gREPEATstep')[i]) or re.search(r'edit',
                                                                                 self.doinfo.get('gREPEATstep')[i]):
                if covline_x < self.sr_xmax:
                    self.step.addLine(covline_x, covlinemin_y, covline_x, covlinemax_y, 'r100')
                if covline_y < self.sr_ymax:
                    self.step.addLine(covlinemin_x, covline_y, covlinemax_x, covline_y, 'r100')
        self.step.COM('sel_design2rout,det_tol=25.4,con_tol=25.4,rad_tol=2.54')  # 去重线
        self.step.VON()
        self.step.unaffectAll()

    # 加菲林寿命管控点卡
    def do_film_marks(self):
        x = self.prof_xmax + 14
        y = self.prof_ymin + 26
        mir = 'no'
        for layer in self.signals:
            mir = 'no' if layer == 'cs' else 'yes'
            self.step.affect(layer)
        self.step.addPad(x, y, 'csx-plife', angle=270, mirror=mir)
        self.step.unaffectAll()

    # 加板序号
    def do_addnb(self):
        if not self.serialLayer:
            return
        nolayer = self.serialLayer
        setStep = job.steps.get('set')
        setStep.initStep()
        setStep.VOF()
        setStep.removeLayer('css-panel_h')
        setStep.removeLayer('css-panel_h2')
        setStep.VON()
        setStep.affect(nolayer)
        setStep.setFilterTypes('text')
        setStep.setTextFilter('00')
        setStep.selectAll()
        setStep.resetFilter()
        count = setStep.Selected_count()
        if count != 1:
            setStep.unaffectAll()
            return
        lines = setStep.INFO('-t layer -e %s/set/%s -d FEATURES -o select,units=mm' % (jobname, nolayer))
        split = lines[1].split()
        positionx_set = split[1]
        positiony_set = split[2]
        angle_set = split[5]
        setStep.copySel('css-panel_h')
        setStep.unaffectAll()
        panelStep = self.step
        panelStep.initStep()
        panelStep.Flatten('css-panel_h', 'css-panel_h2')
        info = panelStep.DO_INFO('-t step -e %s/panel -d REPEAT,units=mm' % jobname)
        REPEATxmin, REPEATymin = [], []
        # minangle = 0
        i = 0
        for name in info.get('gREPEATstep'):
            if name == 'set':
                REPEATxmin.append(info.get('gREPEATxmin')[i])
                REPEATymin.append(info.get('gREPEATymin')[i])
                # minangle = info.get('gREPEATangle')[i]
            i += 1
        REPEATxmin = sorted(REPEATxmin)
        REPEATymin = sorted(REPEATymin)
        xmin = REPEATxmin[0]
        ymin = REPEATymin[0]
        xmin = round(xmin, 3)
        ymin = round(ymin, 3)
        xmax, ymax = 0, 0
        i = 0
        for name in info.get('gREPEATstep'):
            if name == 'set':
                x1 = round(info.get('gREPEATxmin')[i], 3)
                y1 = round(info.get('gREPEATymin')[i], 3)
                x2 = round(info.get('gREPEATxmax')[i], 3)
                y2 = round(info.get('gREPEATymax')[i], 3)
                if x1 == xmin and y1 == ymin:
                    xmax = x2
                    ymax = y2
                    break
            i += 1
        panelStep.affect('css-panel_h2')
        panelStep.resetFilter()
        panelStep.setFilterTypes('text')
        panelStep.setTextFilter('00')
        panelStep.selectRectangle(xmin, ymin, xmax, ymax)
        panelStep.resetFilter()
        readlines = panelStep.INFO(
            '-t layer -e %s/%s/css-panel_h2 -d FEATURES -o select, units=mm' % (jobname, panelStep.name))
        file = readlines[1].split()
        positionx = file[1]
        positiony = file[2]
        size = float(file[9]) / 3.28
        width = file[7]
        height = file[8]
        mir = 'yes' if file[6] == 'Y' else 'no'
        # angle = float(file[5]) + minangle
        angle = float(file[5])
        if angle >= 360:
            angle -= 360
        polarity = 'negative' if file[4] == 'N' else 'positive'
        panelStep.unaffectAll()
        panelStep.affect(nolayer)
        # panelStep.stpnum_display('panel', positionx, positiony)
        panelStep.stpnum_display('set', positionx, positiony)
        panelStep.stpnum_select('set', positionx, positiony)
        panelStep.stpnum_ins_point(x=positionx_set, y=positiony_set)
        panelStep.stpnum_numbering(method='hor_left2right_top2bot', orientation='pcb_orientation', mirror=mir,
                                   rotate=int(angle_set), polarity=polarity,
                                   x_size=width, y_size=height, line_width=size, format='@@')
        panelStep.resetFilter()
        panelStep.setFilterTypes('text', 'positive')
        panelStep.setAttrFilter2('.step_numbering')
        panelStep.selectAll()
        panelStep.resetFilter()
        if panelStep.Selected_count():
            panelStep.changeText(w_factor=0.5001312336, fontname='fpc')
        panelStep.unaffectAll()
        panelStep.removeLayer('css-panel_h')
        panelStep.removeLayer('css-panel_h2')
        #####删除之前SET添加的00字符
        setStep.initStep()
        setStep.affect(nolayer)
        setStep.resetFilter()
        setStep.setFilterTypes('text', 'positive')
        setStep.setTextFilter('00')
        setStep.selectAll()
        setStep.selectDelete()
        setStep.unaffectAll()
        setStep.close()
        self.step.initStep()


if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    stepname = os.environ.get('STEP')
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setWindowIcon(QIcon(":/icon/res/demo.png"))
    app.setStyleSheet("QMessageBox{font-size:12pt;} QPushButton:hover{background:#99eeee;}")
    if not jobname:
        QMessageBox.warning(None, 'infomation', '请打开料号!')
        sys.exit()
    if stepname != 'panel':
        QMessageBox.warning(None, 'infomation', '请在panel中执行!')
        sys.exit()
    job = gen.Job(jobname)
    step = job.steps.get('panel')
    form = ui.Ui_Form()
    widget = QWidget()
    form.setupUi(widget)
    making = SingleBoardPanelMaking()
    widget.show()
    sys.exit(qApp.exec_())
