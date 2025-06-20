#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:SingleDoubleBoard20240626-1.py
   @author:zl
   @time:2024/6/20 11:10
   @software:PyCharm
   @desc: 
"""
import datetime
import os
import re
import sys
import res_rc

import qtawesome
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QTableWidgetItem, QComboBox, QAbstractItemView, \
    QHeaderView

import SingleDoubleBoardUI as ui
import genClasses as gen


class SingleDoubleBoard(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        #
        self.signal_dict = {}
        self.map_flag = True
        self.label_logo.setPixmap(QPixmap(':/res/logo.png'))
        self.label_jobname.setText(jobname)
        self.lineEdit_pnl_w.setText(str(step.profile2.xsize))
        self.lineEdit_pnl_h.setText(str(step.profile2.ysize))
        # 线路层数
        self.signal_layers = job.matrix.returnRows('board', 'signal')
        if len(self.signal_layers) == 1:
            signal_name = '单面板'
        elif len(self.signal_layers) == 2:
            signal_name = '双面板'
        elif len(self.signal_layers) > 2:
            signal_name = f'{len(self.signal_layers)}层板'
        else:
            QMessageBox.warning(None, '提示', '该料号没有线路层')
            sys.exit()
        self.label_type.setText(signal_name)
        # 层数
        signal_len = int(jobname[2:4])
        if signal_len != len(self.signal_layers):
            QMessageBox.warning(None, '警告', '料号名线路层数与料号中的不一致，请确认')
            sys.exit()
        # 类型
        __type = jobname[:2]
        if __type == 'fp':
            type_name = '软板'
        elif __type == 'rf':
            type_name = '软硬结合板'
        elif __type == 'pc':
            type_name = '硬板'
        else:
            type_name = '其他'
        self.label_product.setText(type_name)
        # 表面处理
        __treatment = jobname[4:6]
        self.label_treatment.setText(__treatment)
        # 面向
        header = ['线路层名', '面向']
        self.tableWidget.setColumnCount(len(header))
        self.tableWidget.setHorizontalHeaderLabels(header)
        self.tableWidget.setRowCount(len(self.signal_layers))
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        for row, lay in enumerate(self.signal_layers):
            self.tableWidget.setItem(row, 0, QTableWidgetItem(lay))
            combo = QComboBox()
            combo.setFont(QFont('微软雅黑', 9))
            combo.addItems(['正', '反'])
            combo.setCurrentText('反') if row % 2 else combo.setCurrentText('正')
            self.tableWidget.setCellWidget(row, 1, combo)
        self.pushButton_make_map.setIcon(qtawesome.icon('mdi.target', color='cyan'))
        self.pushButton_run.setIcon(qtawesome.icon('fa.upload', color='cyan'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='cyan'))
        self.pushButton_make_map.clicked.connect(self.make_map)
        self.pushButton_run.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            'QPushButton{font:11pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')


    def make_map(self):
        step.initStep()
        self.panel = Panel()
        self.panel.make_map_layer()

    def run(self):
        # 取到面向
        for row in range(self.tableWidget.rowCount()):
            k = self.tableWidget.item(row, 0).text()
            v = 't' if self.tableWidget.cellWidget(row, 1).currentText() == '正' else 'b'
            self.signal_dict.update({k: v})
        if not step.isLayer('map'):
            self.map_flag = False
            confirm = QMessageBox.warning(board, 'tips', '没有map层，是否继续', QMessageBox.Ok | QMessageBox.Cancel)
            if confirm == QMessageBox.Cancel:
                return
        step.initStep()
        self.panel = Panel()
        self.panel.ClearAndCreate()
        self.panel.do_surface()
        self.panel.do_fxk()
        self.panel.do_sy()
        self.panel.do_component()
        self.panel.do_fxjt()
        self.panel.do_film()
        self.panel.do_wz()
        self.panel.do_py()
        self.panel.do_ldi()
        self.panel.do_scale()
        if len(self.panel.signalLays) > 1:
            self.panel.do_lpi()
            self.panel.do_qp()
            self.panel.do_donut()
            self.panel.do_2d()
            self.panel.do_au_text()
            self.panel.do_jt_line()
            # self.panel.do_c5_mark() # 5x5的点取五个  单独去做
            self.panel.do_sc_mark()
            self.panel.do_cov()
            self.panel.do_drill_letter()
        self.panel.do_border()
        QMessageBox.information(board, 'tips', '执行完毕!')


class Panel():
    def __init__(self):
        self.user = job.getUser()
        self.tmp_map = f'map+++{step.pid}'
        # 线路
        self.signalLays = board.signal_layers
        # 覆盖膜
        self.covs = []
        for row in job.matrix.returnRows('board', 'coverlay'):
            if re.match('c\d+$', row):
                self.covs.append(row)
        # 阻焊层, 印油层
        self.zhs, self.yys = [], []
        for row in job.matrix.returnRows('board', 'solder_mask'):
            if re.match('g(t|b)s$', row):
                self.zhs.append(row)
        for row in job.matrix.returnRows():
            if re.match('yy(\d+)$', row):
                self.yys.append(row)
        # 文字层
        self.wzs = job.matrix.returnRows('board', 'silk_screen')
        # 钻孔层
        self.drills = []
        for row in job.matrix.returnRows('board', 'drill'):
            if re.match('f\d+', row):
                self.drills.append(row)

    def make_map_layer(self):
        if step.isLayer('map'):
            step.removeLayer('map')
        step.createLayer('map')
        step.prof_to_rout('map', 0.1)
        step.affect('map')
        step.addPad(step.profile2.xmin + 2.5, 2.5, 'fxk')
        step.addPad(step.profile2.xmin + 2.5, step.profile2.ymax - 2.5, 'fxk')
        step.addPad(step.profile2.xmin + 8.5, step.profile2.ymax - 2.5, 'fxk')
        step.addPad(step.profile2.xmin + 14.5, step.profile2.ymax - 2.5, 'fxk')
        step.addPad(step.profile2.xmax - 2.5, 2.5, 'fxk')
        step.addPad(step.profile2.xmax - 2.5, step.profile2.ymax - 2.5, 'fxk')
        sym = 'sy-pin-t'
        step.addPad(step.profile2.xmin + 21, step.profile2.ymin + 3.5, sym, 'positive', 270)
        step.addPad(step.profile2.xmin + 21, step.profile2.ymax - 3.5, sym, 'positive', 270)
        step.addPad(step.profile2.xmax - 25, step.profile2.ymax - 3.5, sym, 'positive', 90)
        step.addPad(25, 3.5, 'jsk')
        step.addPad(50, step.profile2.ymax - 3.5, 'jsk')
        step.addPad(step.profile2.xmax - 48, step.profile2.ymax - 3.5, 'jsk')
        step.addPad(step.profile2.xmax - 40, 3.5, 'jsk')
        step.addPad(3.5, step.sr2.ymax - 35, 'jsk')
        step.addPad(3.5, step.sr2.ymin + 35, 'jsk')
        step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 30, 'jsk')
        step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 35, 'jsk')
        # 中间
        step.addPad(3.5, step.profile2.ycenter - 7, 'jsk')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 2, 'jsk')
        # s1500
        step.addPad(27.5, 3.5, 's1500')
        step.addPad(47.5, step.profile2.ymax - 3.5, 's1500')
        step.addPad(step.profile2.xmax - 45.5, step.profile2.ymax - 3.5, 's1500')
        step.addPad(step.profile2.xmax - 37.5, 3.5, 's1500')
        step.addPad(3.5, step.sr2.ymax - 32.5, 's1500')
        step.addPad(3.5, step.sr2.ymin + 32.5, 's1500')
        step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 27.5, 's1500')
        step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 32.5, 's1500')
        # 中间
        step.addPad(3.5, step.profile2.ycenter - 4.5, 's1500')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 0.5, 's1500')
        # wzdw
        step.addPad(30.5, 3.5, 'wzdw')
        step.addPad(43.5, step.profile2.ymax - 3.5, 'wzdw')
        step.addPad(step.profile2.xmax - 41.5, step.profile2.ymax - 3.5, 'wzdw')
        step.addPad(step.profile2.xmax - 34.5, 3.5, 'wzdw')
        step.addPad(3.5, step.sr2.ymax - 29.5, 'wzdw')
        step.addPad(3.5, step.sr2.ymin + 29, 'wzdw')
        step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 24, 'wzdw')
        step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 29, 'wzdw')
        # 中间
        step.addPad(3.5, step.profile2.ycenter, 'wzdw')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 3.5, 'wzdw')
        # r-mark-t
        sym = 'r-mark-t'
        step.addPad(36, 3.5, sym)
        step.addPad(39, step.profile2.ymax - 3.5, sym)
        step.addPad(step.profile2.xmax - 35, step.profile2.ymax - 3.5, sym)
        step.addPad(step.profile2.xmax - 28, 3.5, sym)
        step.addPad(3.5, step.sr2.ymax - 23, sym, angle=270)
        step.addPad(3.5, step.sr2.ymin + 25, sym, angle=270)
        step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 20, sym, angle=90)
        step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 22, sym, angle=90)
        # 中间
        step.addPad(3.5, step.profile2.ycenter + 5.5, sym, angle=270)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 8, sym, angle=90)
        # c-mark-t
        sym = 'c-mark-t'
        step.addPad(40, 3.5, sym)
        step.addPad(61, step.profile2.ymax - 3.5, sym, 'positive', 180)
        step.addPad(step.profile2.xmax - 29, step.profile2.ymax - 3.5, sym, 'positive', 180)
        step.addPad(step.profile2.xmax - 24, 3.5, sym)
        step.addPad(3.5, step.sr2.ymax - 46, sym, 'positive', 270)
        step.addPad(3.5, step.sr2.ymin + 38, sym, 'positive', 270)
        step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 33, sym, 'positive', 90)
        step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 17, sym, 'positive', 90)
        # 中间
        step.addPad(3.5, step.profile2.ycenter - 19, sym, 'positive', 270)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 5, sym, 'positive', 90)
        # wf-mark-t
        sym = 'wf-mark-t'
        step.addPad(45.5, 3.5, sym)
        step.addPad(53, step.profile2.ymax - 3.5, sym)
        step.addPad(step.profile2.xmax - 52, step.profile2.ymax - 3.5, sym, 'positive', 180)
        step.addPad(step.profile2.xmax - 18, 3.5, sym)
        step.addPad(3.5, step.sr2.ymax - 40, sym, 'positive', 270)
        step.addPad(3.5, step.sr2.ymin + 17.5, sym, 'positive', 270)
        step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 40, sym, 'positive', 270)
        step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 39, sym, 'positive', 270)
        # 中间
        step.addPad(3.5, step.profile2.ycenter - 12.5, sym, 'positive', 270)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 12, sym, 'positive', 270)
        # sy-mark
        step.addPad(51, 3.5, 'sy-mark')
        step.addPad(65, step.profile2.ymax - 3.5, 'sy-mark')
        step.addPad(step.profile2.xmax - 58, step.profile2.ymax - 3.5, 'sy-mark', 'positive', 180)
        step.addPad(step.profile2.xmax - 43, 3.5, 'sy-mark')
        step.addPad(3.5, step.sr2.ymax - 19, 'sy-mark', 'positive', 270)
        step.addPad(3.5, step.sr2.ymin + 13, 'sy-mark', 'positive', 270)
        step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 14, 'sy-mark', 'positive', 270)
        step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 11, 'sy-mark', 'positive', 270)
        # 中间
        step.addPad(3.5, step.profile2.ycenter + 10, 'sy-mark', 'positive', 270)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 14, 'sy-mark', 'positive', 270)
        # film
        step.addPad(step.profile2.xmin + 5, step.sr2.ymax - 57, 'base_film_map')
        step.addPad(step.profile2.xmin + 5, step.sr2.ymin + 57, 'base_film_map')
        step.addPad(step.profile2.xmax - 5, step.sr2.ymax - 57, 'base_film_map', angle=180)
        step.addPad(step.profile2.xmax - 5, step.sr2.ymin + 72, 'base_film_map', angle=180)
        #
        sym = 'ldi-mark-t'
        step.addPad(19, step.sr2.ymin - 2, sym)
        step.addPad(19, step.sr2.ymax + 2, sym)
        step.addPad(step.profile2.xmax - 23, step.sr2.ymax + 2, sym)
        step.addPad(step.profile2.xmax - 19, step.sr2.ymin - 2, sym)
        # qp
        # 左右
        step.addPad(7.6, step.profile2.ymax - 78, 'qp-map', angle=90)
        step.addPad(7.6, step.profile2.ymin + 39, 'qp-map', angle=90)
        step.addPad(step.profile2.xmax - 7.6, step.profile2.ymax - 36.5, 'qp-map', angle=270)
        step.addPad(step.profile2.xmax - 7.6, 50, 'qp-map', angle=270)
        if len(self.signalLays) > 1:
            # 加flzddw-jt线
            step.addAttr_zl('.out_flag,int=233')
            step.addLine(step.profile2.xmin + 3, step.profile2.ymin + 45, step.profile2.xmin + 3, step.profile2.ymax - 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmin - 9, step.profile2.ymin + 45, step.profile2.xmin - 9, step.profile2.ymax - 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmin + 3, step.profile2.ymin + 45, step.profile2.xmin - 9, step.profile2.ymin + 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmin + 3, step.profile2.ymax - 45, step.profile2.xmin - 9, step.profile2.ymax - 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmax - 3, step.profile2.ymin + 45, step.profile2.xmax - 3, step.profile2.ymax - 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmax + 9, step.profile2.ymin + 45, step.profile2.xmax + 9, step.profile2.ymax - 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmax - 3, step.profile2.ymin + 45, step.profile2.xmax + 9, step.profile2.ymin + 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmax - 3, step.profile2.ymax - 45, step.profile2.xmax + 9, step.profile2.ymax - 45, 'r401', attributes='yes')
            step.resetAttr()
        step.unaffectAll()
        QMessageBox.information(board, 'tips', '创建完成!')
        sys.exit()


    # 清空层创建层
    def ClearAndCreate(self):
        step.VOF()
        for layer in self.signalLays + self.wzs + self.covs + self.zhs + self.yys + self.drills:
            step.affect(layer)
        step.selectDelete()
        step.unaffectAll()
        step.removeLayer('2d')
        step.createLayer('2d')
        step.VON()
        if not board.map_flag:
            step.createLayer('map')
            step.prof_to_rout('map', 0.1)
        else:
            step.createLayer(self.tmp_map)


    # 铺铜
    def do_surface(self):
        string = str.join('\;', step.info.get('gSRstep'))
        for lay in self.signalLays:
            step.affect(lay)
        step.srFill_2(step_margin_x=1, step_margin_y=1, stop_at_steps=string)
        step.unaffectAll()
        step.VOF()
        for yy in self.yys:
            step.affect(yy)
        step.srFill_2(stop_at_steps=string)
        step.addLine(step.profile2.xmin, step.profile2.ymin, step.profile2.xmin + 5, step.profile2.ymin, 'r100', 'negative')
        step.addLine(step.profile2.xmin, step.profile2.ymin, step.profile2.xmin, step.profile2.ymin + 5, 'r100', 'negative')
        step.addLine(step.profile2.xmin, step.profile2.ymax, step.profile2.xmin + 5, step.profile2.ymax, 'r100', 'negative')
        step.addLine(step.profile2.xmin, step.profile2.ymax, step.profile2.xmin, step.profile2.ymax - 5, 'r100', 'negative')
        step.addLine(step.profile2.xmax, step.profile2.ymax, step.profile2.xmax - 5, step.profile2.ymax, 'r100', 'negative')
        step.addLine(step.profile2.xmax, step.profile2.ymax, step.profile2.xmax, step.profile2.ymax - 5, 'r100', 'negative')
        step.addLine(step.profile2.xmax, step.profile2.ymin, step.profile2.xmax - 5, step.profile2.ymin, 'r100', 'negative')
        step.addLine(step.profile2.xmax, step.profile2.ymin, step.profile2.xmax, step.profile2.ymin + 5, 'r100', 'negative')
        step.unaffectAll()
        for cov in self.covs:
            step.prof_to_rout(cov, 100)
        step.VON()

    def do_fxk(self):
        if board.map_flag:
            for lay in self.signalLays:
                step.affect(lay)
            for wz in self.wzs:
                step.affect(wz)
            for zh in self.zhs:
                step.affect(zh)
            step.addLine(step.profile2.xmin, step.profile2.ymin, step.profile2.xmin + 5, step.profile2.ymin, 'r100')
            step.addLine(step.profile2.xmin, step.profile2.ymin, step.profile2.xmin, step.profile2.ymin + 5, 'r100')
            step.addLine(step.profile2.xmin, step.profile2.ymax, step.profile2.xmin + 5, step.profile2.ymax, 'r100')
            step.addLine(step.profile2.xmin, step.profile2.ymax, step.profile2.xmin, step.profile2.ymax - 5, 'r100')
            step.addLine(step.profile2.xmax, step.profile2.ymax, step.profile2.xmax - 5, step.profile2.ymax, 'r100')
            step.addLine(step.profile2.xmax, step.profile2.ymax, step.profile2.xmax, step.profile2.ymax - 5, 'r100')
            step.addLine(step.profile2.xmax, step.profile2.ymin, step.profile2.xmax - 5, step.profile2.ymin, 'r100')
            step.addLine(step.profile2.xmax, step.profile2.ymin, step.profile2.xmax, step.profile2.ymin + 5, 'r100')
            step.unaffectAll()
            for signal in self.signalLays:
                step.affect(signal)
            step.addPad(step.profile2.xmin + 4.5, step.profile2.ymax - 2.5, 's5000')
            step.addPad(step.profile2.xmin + 9.5, step.profile2.ymax - 2.5, 's5000')
            step.unaffectAll()
            step.affect('map')
            step.selectSymbol('fxk')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                step.selectChange('fxk-yy')
                for wz in self.wzs:
                    step.copySel(wz)
                for zh in self.zhs:
                    step.copySel(zh)
                step.selectPolarity('negative')
                for yy in self.yys:
                    step.copySel(yy)
                step.selectChange('r2001')
                step.selectPolarity()
                for cov in self.covs:
                    step.copySel(cov)
                for drill in self.drills:
                    step.copySel(drill)
                step.selectChange('s5000')
                for signal in self.signalLays:
                    step.copySel(signal)
                step.selectChange('fxk')
                step.selectPolarity('negative')
                for signal in self.signalLays:
                    step.copySel(signal)
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
        else:
            for lay in self.signalLays:
                step.affect(lay)
            for wz in self.wzs:
                step.affect(wz)
            for zh in self.zhs:
                step.affect(zh)
            step.addLine(step.profile2.xmin, step.profile2.ymin, step.profile2.xmin + 5, step.profile2.ymin, 'r100')
            step.addLine(step.profile2.xmin, step.profile2.ymin, step.profile2.xmin, step.profile2.ymin + 5, 'r100')
            step.addLine(step.profile2.xmin, step.profile2.ymax, step.profile2.xmin + 5, step.profile2.ymax, 'r100')
            step.addLine(step.profile2.xmin, step.profile2.ymax, step.profile2.xmin, step.profile2.ymax - 5, 'r100')
            step.addLine(step.profile2.xmax, step.profile2.ymax, step.profile2.xmax - 5, step.profile2.ymax, 'r100')
            step.addLine(step.profile2.xmax, step.profile2.ymax, step.profile2.xmax, step.profile2.ymax - 5, 'r100')
            step.addLine(step.profile2.xmax, step.profile2.ymin, step.profile2.xmax - 5, step.profile2.ymin, 'r100')
            step.addLine(step.profile2.xmax, step.profile2.ymin, step.profile2.xmax, step.profile2.ymin + 5, 'r100')
            step.unaffectAll()
            step.VOF()
            for wz in self.wzs:
                step.affect(wz)
            step.addPad(step.profile2.xmin + 2.5, 2.5, 'fxk-yy')
            step.addPad(step.profile2.xmin + 2.5, step.profile2.ymax - 2.5, 'fxk-yy')
            step.addPad(step.profile2.xmin + 8.5, step.profile2.ymax - 2.5, 'fxk-yy')
            step.addPad(step.profile2.xmin + 14.5, step.profile2.ymax - 2.5, 'fxk-yy')
            step.addPad(step.profile2.xmax - 2.5, 2.5, 'fxk-yy')
            step.addPad(step.profile2.xmax - 2.5, step.profile2.ymax - 2.5, 'fxk-yy')
            step.unaffectAll()
            for yy in self.yys:
                step.affect(yy)
            step.addPad(step.profile2.xmin + 2.5, 2.5, 'fxk-yy', 'negative')
            step.addPad(step.profile2.xmin + 2.5, step.profile2.ymax - 2.5, 'fxk-yy', 'negative')
            step.addPad(step.profile2.xmin + 8.5, step.profile2.ymax - 2.5, 'fxk-yy', 'negative')
            step.addPad(step.profile2.xmin + 14.5, step.profile2.ymax - 2.5, 'fxk-yy', 'negative')
            step.addPad(step.profile2.xmax - 2.5, 2.5, 'fxk-yy', 'negative')
            step.addPad(step.profile2.xmax - 2.5, step.profile2.ymax - 2.5, 'fxk-yy', 'negative')
            step.unaffectAll()
            for cov in self.covs:
                step.affect(cov)
            step.addPad(step.profile2.xmin + 2.5, 2.5, 'r2001')
            step.addPad(step.profile2.xmin + 2.5, step.profile2.ymax - 2.5, 'r2001')
            step.addPad(step.profile2.xmin + 8.5, step.profile2.ymax - 2.5, 'r2001')
            step.addPad(step.profile2.xmin + 14.5, step.profile2.ymax - 2.5, 'r2001')
            step.addPad(step.profile2.xmax - 2.5, 2.5, 'r2001')
            step.addPad(step.profile2.xmax - 2.5, step.profile2.ymax - 2.5, 'r2001')
            step.unaffectAll()
            for signal in self.signalLays:
                step.affect(signal)
            step.addPad(step.profile2.xmin + 2.5, 2.5, 's5000')
            step.addPad(step.profile2.xmin + 2.5, step.profile2.ymax - 2.5, 's5000')
            step.addPad(step.profile2.xmin + 4.5, step.profile2.ymax - 2.5, 's5000')
            step.addPad(step.profile2.xmin + 8.5, step.profile2.ymax - 2.5, 's5000')
            step.addPad(step.profile2.xmin + 9.5, step.profile2.ymax - 2.5, 's5000')
            step.addPad(step.profile2.xmin + 14.5, step.profile2.ymax - 2.5, 's5000')
            step.addPad(step.profile2.xmax - 2.5, 2.5, 's5000')
            step.addPad(step.profile2.xmax - 2.5, step.profile2.ymax - 2.5, 's5000')
            step.addPad(step.profile2.xmin + 2.5, 2.5, 'fxk', 'negative')
            step.addPad(step.profile2.xmin + 2.5, step.profile2.ymax - 2.5, 'fxk', 'negative')
            step.addPad(step.profile2.xmin + 8.5, step.profile2.ymax - 2.5, 'fxk', 'negative')
            step.addPad(step.profile2.xmin + 14.5, step.profile2.ymax - 2.5, 'fxk', 'negative')
            step.addPad(step.profile2.xmax - 2.5, 2.5, 'fxk', 'negative')
            step.addPad(step.profile2.xmax - 2.5, step.profile2.ymax - 2.5, 'fxk', 'negative')
            step.unaffectAll()
            step.VON()
            step.affect('map')
            step.addPad(step.profile2.xmin + 2.5, 2.5, 'fxk')
            step.addPad(step.profile2.xmin + 2.5, step.profile2.ymax - 2.5, 'fxk')
            step.addPad(step.profile2.xmin + 8.5, step.profile2.ymax - 2.5, 'fxk')
            step.addPad(step.profile2.xmin + 14.5, step.profile2.ymax - 2.5, 'fxk')
            step.addPad(step.profile2.xmax - 2.5, 2.5, 'fxk')
            step.addPad(step.profile2.xmax - 2.5, step.profile2.ymax - 2.5, 'fxk')
            step.unaffectAll()

    def do_sy(self):
        if board.map_flag:
            step.affect('map')
            step.selectSymbol('sy-pin-t;sy-pin-b')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                for signal in self.signalLays:
                    step.selectChange('sy-pin-t') if board.signal_dict.get(signal) == 't' else step.selectChange('sy-pin-b')
                    step.selectPolarity('negative')
                    step.copySel(signal)
                step.selectChange('r2500')
                step.selectPolarity()
                step.VOF()
                for cov in self.covs:
                    step.copySel(cov)
                step.selectChange('r2000')
                for drill in self.drills:
                    step.copySel(drill)
                step.selectChange('r2010')
                step.selectPolarity('negative')
                for yy in self.yys:
                    step.copySel(yy)
                step.unaffectAll()
                step.VON()
            step.unaffectAll()
            step.truncate(self.tmp_map)
        else:
            for signal in self.signalLays:
                step.affect(signal)
                sym = 'sy-pin-t' if board.signal_dict.get(signal) == 't' else 'sy-pin-b'
                step.addPad(step.profile2.xmin + 21, step.profile2.ymin + 3.5, sym, 'negative', 270)
                step.addPad(step.profile2.xmin + 21, step.profile2.ymax - 3.5, sym, 'negative', 270)
                step.addPad(step.profile2.xmax - 25, step.profile2.ymax - 3.5, sym, 'negative', 90)
                step.unaffectAll()
            step.affect('map')
            step.addPad(step.profile2.xmin + 21, step.profile2.ymin + 3.5, sym, 'negative', 270)
            step.addPad(step.profile2.xmin + 21, step.profile2.ymax - 3.5, sym, 'negative', 270)
            step.addPad(step.profile2.xmax - 25, step.profile2.ymax - 3.5, sym, 'negative', 90)
            step.unaffectAll()
            step.VOF()
            for cov in self.covs:
                step.affect(cov)
            step.addPad(step.profile2.xmin + 21, step.profile2.ymin + 3.5, 'r2500')
            step.addPad(step.profile2.xmin + 21, step.profile2.ymax - 3.5, 'r2500')
            step.addPad(step.profile2.xmax - 25, step.profile2.ymax - 3.5, 'r2500')
            step.unaffectAll()
            for drill in self.drills:
                step.affect(drill)
            step.addPad(step.profile2.xmin + 21, step.profile2.ymin + 3.5, 'r2000')
            step.addPad(step.profile2.xmin + 21, step.profile2.ymax - 3.5, 'r2000')
            step.addPad(step.profile2.xmax - 25, step.profile2.ymax - 3.5, 'r2000')
            step.unaffectAll()
            for yy in self.yys:
                step.affect(yy)
            sym = 'r2010'
            step.addPad(step.profile2.xmin + 21, step.profile2.ymin + 3.5, sym, 'negative', 270)
            step.addPad(step.profile2.xmin + 21, step.profile2.ymax - 3.5, sym, 'negative', 270)
            step.addPad(step.profile2.xmax - 25, step.profile2.ymax - 3.5, sym, 'negative', 90)
            step.unaffectAll()
            step.VON()

    # jsk s1500 wzdw r-mark-t c-mark-t wf-mark-t sy-mark
    def do_component(self):
        if board.map_flag:
            step.affect('map')
            step.selectSymbol('jsk')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                for signal in self.signalLays:
                    step.copySel(signal)
                step.selectChange('r500')
                for drill in self.drills:
                    step.copySel(drill)
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
            step.affect('map')
            step.selectSymbol('s1500')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                step.selectPolarity('negative')
                for signal in self.signalLays:
                    step.copySel(signal)
                step.selectChange('r1500')
                step.selectPolarity()
                for cov in self.covs:
                    step.copySel(cov)
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
            step.affect('map')
            step.selectSymbol('wzdw')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                for wz in self.wzs:
                    step.copySel(wz)
                step.selectPolarity('negative')
                for signal in self.signalLays:
                    step.copySel(signal)
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
            step.affect('map')
            step.selectSymbol('r-mark-t')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                for signal in self.signalLays:
                    step.selectChange('r-mark-t') if board.signal_dict.get(signal) == 't' else step.selectChange(
                        'r-mark-b')
                    step.selectPolarity('negative')
                    step.copySel(signal)
                step.selectChange('r1860')
                step.selectPolarity('negative')
                for yy in self.yys:
                    step.copySel(yy)
                step.selectChange('r1850')
                step.selectPolarity()
                for drill in self.drills:
                    step.copySel(drill)
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
            step.affect('map')
            step.selectSymbol('c-mark-t')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                for signal in self.signalLays:
                    step.selectChange('c-mark-t') if board.signal_dict.get(signal) == 't' else step.selectChange(
                        'c-mark-b')
                    step.selectPolarity('negative')
                    step.copySel(signal)
                step.selectChange('r2100')
                step.selectPolarity()
                for cov in self.covs:
                    step.copySel(cov)
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
            step.affect('map')
            step.selectSymbol('wf-mark-t')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                for signal in self.signalLays:
                    step.selectChange('wf-mark-t') if board.signal_dict.get(signal) == 't' else step.selectChange(
                        'wf-mark-b')
                    step.selectPolarity('negative')
                    step.copySel(signal)
                step.selectChange('r1750')
                for zh in self.zhs:
                    step.copySel(zh)
                step.selectChange('donut_r2400x1750')
                step.selectPolarity('negative')
                for yy in self.yys:
                    step.copySel(yy)
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
            step.affect('map')
            step.selectSymbol('sy-mark')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                step.selectChange('sy-1')
                for wz in self.wzs:
                    step.copySel(wz)
                step.selectChange('sy-mark')
                step.selectPolarity('negative')
                for signal in self.signalLays:
                    step.copySel(signal)
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
        else:
            for signal in self.signalLays + ['map']:
                step.affect(signal)
                step.addPad(25, 3.5, 'jsk')
                step.addPad(50, step.profile2.ymax - 3.5, 'jsk')
                step.addPad(step.profile2.xmax - 48, step.profile2.ymax - 3.5, 'jsk')
                step.addPad(step.profile2.xmax - 40, 3.5, 'jsk')
                step.addPad(3.5, step.sr2.ymax - 35, 'jsk')
                step.addPad(3.5, step.sr2.ymin + 35, 'jsk')
                step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 30, 'jsk')
                step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 35, 'jsk')
                # 中间
                step.addPad(3.5, step.profile2.ycenter - 7, 'jsk')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 2, 'jsk')
                # s1500
                step.addPad(27.5, 3.5, 's1500', 'negative')
                step.addPad(47.5, step.profile2.ymax - 3.5, 's1500', 'negative')
                step.addPad(step.profile2.xmax - 45.5, step.profile2.ymax - 3.5, 's1500', 'negative')
                step.addPad(step.profile2.xmax - 37.5, 3.5, 's1500', 'negative')
                step.addPad(3.5, step.sr2.ymax - 32.5, 's1500', 'negative')
                step.addPad(3.5, step.sr2.ymin + 32.5, 's1500', 'negative')
                step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 27.5, 's1500', 'negative')
                step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 32.5, 's1500', 'negative')
                # 中间
                step.addPad(3.5, step.profile2.ycenter - 4.5, 's1500', 'negative')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 0.5, 's1500', 'negative')
                # wzdw
                step.addPad(30.5, 3.5, 'wzdw', 'negative')
                step.addPad(43.5, step.profile2.ymax - 3.5, 'wzdw', 'negative')
                step.addPad(step.profile2.xmax - 41.5, step.profile2.ymax - 3.5, 'wzdw', 'negative')
                step.addPad(step.profile2.xmax - 34.5, 3.5, 'wzdw', 'negative')
                step.addPad(3.5, step.sr2.ymax - 29.5, 'wzdw', 'negative')
                step.addPad(3.5, step.sr2.ymin + 29, 'wzdw', 'negative')
                step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 24, 'wzdw', 'negative')
                step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 29, 'wzdw', 'negative')
                # 中间
                step.addPad(3.5, step.profile2.ycenter, 'wzdw', 'negative')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 3.5, 'wzdw', 'negative')
                # r-mark-t
                sym = 'r-mark-b' if board.signal_dict.get(signal) == 'b' else 'r-mark-t'
                step.addPad(36, 3.5, sym, 'negative')
                step.addPad(39, step.profile2.ymax - 3.5, sym, 'negative')
                step.addPad(step.profile2.xmax - 35, step.profile2.ymax - 3.5, sym, 'negative')
                step.addPad(step.profile2.xmax - 28, 3.5, sym, 'negative')
                step.addPad(3.5, step.sr2.ymax - 23, sym, 'negative', 270)
                step.addPad(3.5, step.sr2.ymin + 25, sym, 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 20, sym, 'negative', 90)
                step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 22, sym, 'negative', 90)
                # 中间
                step.addPad(3.5, step.profile2.ycenter + 5.5, sym, 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 8, sym, 'negative', 90)
                # c-mark-t
                sym = 'c-mark-b' if board.signal_dict.get(signal) == 'b' else 'c-mark-t'
                step.addPad(40, 3.5, sym, 'negative')
                step.addPad(61, step.profile2.ymax - 3.5, sym, 'negative', 180)
                step.addPad(step.profile2.xmax - 29, step.profile2.ymax - 3.5, sym, 'negative', 180)
                step.addPad(step.profile2.xmax - 24, 3.5, sym, 'negative')
                step.addPad(3.5, step.sr2.ymax - 46, sym, 'negative', 270)
                step.addPad(3.5, step.sr2.ymin + 38, sym, 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 33, sym, 'negative', 90)
                step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 17, sym, 'negative', 90)
                # 中间
                step.addPad(3.5, step.profile2.ycenter - 19, sym, 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 5, sym, 'negative', 90)
                # wf-mark-t
                sym = 'wf-mark-b' if board.signal_dict.get(signal) == 'b' else 'wf-mark-t'
                step.addPad(45.5, 3.5, sym, 'negative')
                step.addPad(53, step.profile2.ymax - 3.5, sym, 'negative')
                step.addPad(step.profile2.xmax - 52, step.profile2.ymax - 3.5, sym, 'negative', 180)
                step.addPad(step.profile2.xmax - 18, 3.5, sym, 'negative')
                step.addPad(3.5, step.sr2.ymax - 40, sym, 'negative', 270)
                step.addPad(3.5, step.sr2.ymin + 17.5, sym, 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 40, sym, 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 39, sym, 'negative', 270)
                # 中间
                step.addPad(3.5, step.profile2.ycenter - 12.5, sym, 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 12, sym, 'negative', 270)
                # sy-mark
                step.addPad(51, 3.5, 'sy-mark', 'negative')
                step.addPad(65, step.profile2.ymax - 3.5, 'sy-mark', 'negative')
                step.addPad(step.profile2.xmax - 58, step.profile2.ymax - 3.5, 'sy-mark', 'negative', 180)
                step.addPad(step.profile2.xmax - 43, 3.5, 'sy-mark', 'negative')
                step.addPad(3.5, step.sr2.ymax - 19, 'sy-mark', 'negative', 270)
                step.addPad(3.5, step.sr2.ymin + 13, 'sy-mark', 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 14, 'sy-mark', 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 11, 'sy-mark', 'negative', 270)
                # 中间
                step.addPad(3.5, step.profile2.ycenter + 10, 'sy-mark', 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 14, 'sy-mark', 'negative', 270)
                step.unaffectAll()
            step.VOF()
            for drill in self.drills:
                step.affect(drill)
            step.addPad(25, 3.5, 'r500')
            step.addPad(50, step.profile2.ymax - 3.5, 'r500')
            step.addPad(step.profile2.xmax - 48, step.profile2.ymax - 3.5, 'r500')
            step.addPad(step.profile2.xmax - 40, 3.5, 'r500')
            step.addPad(3.5, step.sr2.ymax - 35, 'r500')
            step.addPad(3.5, step.sr2.ymin + 35, 'r500')
            step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 30, 'r500')
            step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 35, 'r500')
            # 中间
            step.addPad(3.5, step.profile2.ycenter - 7, 'r500')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 2, 'r500')
            step.unaffectAll()
            for drill in self.drills:
                step.affect(drill)
            sym = 'r1850'
            step.addPad(36, 3.5, sym)
            step.addPad(39, step.profile2.ymax - 3.5, sym)
            step.addPad(step.profile2.xmax - 35, step.profile2.ymax - 3.5, sym)
            step.addPad(step.profile2.xmax - 28, 3.5, sym)
            step.addPad(3.5, step.sr2.ymax - 23, sym, 'positive', 270)
            step.addPad(3.5, step.sr2.ymin + 25, sym, 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 20, sym, 'positive', 90)
            step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 22, sym, 'positive', 90)
            # 中间
            step.addPad(3.5, step.profile2.ycenter + 5.5, sym, 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 8, sym, 'positive', 90)
            step.unaffectAll()
            for yy in self.yys:
                step.affect(yy)
            sym = 'r1860'
            step.addPad(36, 3.5, sym, 'negative')
            step.addPad(39, step.profile2.ymax - 3.5, sym, 'negative')
            step.addPad(step.profile2.xmax - 35, step.profile2.ymax - 3.5, sym, 'negative')
            step.addPad(step.profile2.xmax - 28, 3.5, sym, 'negative')
            step.addPad(3.5, step.sr2.ymax - 23, sym, 'negative', 270)
            step.addPad(3.5, step.sr2.ymin + 25, sym, 'negative', 270)
            step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 20, sym, 'negative', 90)
            step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 22, sym, 'negative', 90)
            # 中间
            step.addPad(3.5, step.profile2.ycenter + 5.5, sym, 'negative', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 8, sym, 'negative', 90)
            sym = 'donut_r2400x1750'
            step.addPad(45.5, 3.5, sym, 'negative')
            step.addPad(53, step.profile2.ymax - 3.5, sym, 'negative')
            step.addPad(step.profile2.xmax - 52, step.profile2.ymax - 3.5, sym, 'negative', 180)
            step.addPad(step.profile2.xmax - 18, 3.5, sym, 'negative')
            step.addPad(3.5, step.sr2.ymax - 40, sym, 'negative', 270)
            step.addPad(3.5, step.sr2.ymin + 17.5, sym, 'negative', 270)
            step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 40, sym, 'negative', 270)
            step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 39, sym, 'negative', 270)
            # 中间
            step.addPad(3.5, step.profile2.ycenter - 12.5, sym, 'negative', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 12, sym, 'negative', 270)
            step.unaffectAll()
            for cov in self.covs:
                step.affect(cov)
            step.addPad(27.5, 3.5, 'r1500')
            step.addPad(47.5, step.profile2.ymax - 3.5, 'r1500')
            step.addPad(step.profile2.xmax - 45.5, step.profile2.ymax - 3.5, 'r1500')
            step.addPad(step.profile2.xmax - 37.5, 3.5, 'r1500')
            step.addPad(3.5, step.sr2.ymax - 32.5, 'r1500')
            step.addPad(3.5, step.sr2.ymin + 32.5, 'r1500')
            step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 27.5, 'r1500')
            step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 32.5, 'r1500')
            # 中间
            step.addPad(3.5, step.profile2.ycenter - 4.5, 'r1500')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 0.5, 'r1500')
            # c-mark-t
            step.addPad(40, 3.5, 'r2100')
            step.addPad(61, step.profile2.ymax - 3.5, 'r2100', 'positive', 180)
            step.addPad(step.profile2.xmax - 29, step.profile2.ymax - 3.5, 'r2100', 'positive', 180)
            step.addPad(step.profile2.xmax - 24, 3.5, 'r2100')
            step.addPad(3.5, step.sr2.ymax - 46, 'r2100', 'positive', 270)
            step.addPad(3.5, step.sr2.ymin + 38, 'r2100', 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 33, 'r2100', 'positive', 90)
            step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 17, 'r2100', 'positive', 90)
            # 中间
            step.addPad(3.5, step.profile2.ycenter - 19, 'r2100', 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 5, 'r2100', 'positive', 90)
            step.unaffectAll()
            for wz in self.wzs:
                step.affect(wz)
            # wzdw
            step.addPad(30.5, 3.5, 'wzdw')
            step.addPad(43.5, step.profile2.ymax - 3.5, 'wzdw')
            step.addPad(step.profile2.xmax - 41.5, step.profile2.ymax - 3.5, 'wzdw')
            step.addPad(step.profile2.xmax - 34.5, 3.5, 'wzdw')
            step.addPad(3.5, step.sr2.ymax - 29.5, 'wzdw')
            step.addPad(3.5, step.sr2.ymin + 29, 'wzdw')
            step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 24, 'wzdw')
            step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 29, 'wzdw')
            # 中间
            step.addPad(3.5, step.profile2.ycenter, 'wzdw')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 3.5, 'wzdw')
            # sy-mark
            step.addPad(51, 3.5, 'sy-1')
            step.addPad(65, step.profile2.ymax - 3.5, 'sy-1')
            step.addPad(step.profile2.xmax - 58, step.profile2.ymax - 3.5, 'sy-1', 'positive', 180)
            step.addPad(step.profile2.xmax - 43, 3.5, 'sy-1', 'positive')
            step.addPad(3.5, step.sr2.ymax - 19, 'sy-1', 'positive', 270)
            step.addPad(3.5, step.sr2.ymin + 13, 'sy-1', 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 14, 'sy-1', 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 11, 'sy-1', 'positive', 270)
            # 中间
            step.addPad(3.5, step.profile2.ycenter + 10, 'sy-1', 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 14, 'sy-1', 'positive', 270)
            step.unaffectAll()
            step.VON()

            step.affect('map')
            step.selectPolarity()
            step.unaffectAll()

    def do_fxjt(self):
        for signal in self.signalLays:
            mir = 'no' if board.signal_dict.get(signal) == 't' else 'yes'
            step.affect(signal)
            step.addPad(57, 3.5, 'fxjt', 'negative')
            step.addPad(68, 3.5, 'xlfp', 'negative', mirror=mir)
            step.unaffectAll()
        step.VOF()
        for wz in self.wzs:
            step.affect(wz)
        step.addPad(57, 3.5, 'fxjt')
        step.addPad(68, 3.5, 'zf')
        step.unaffectAll()
        for yy in self.yys:
            step.affect(yy)
        step.addPad(57, 3.5, 'fxjt', 'negative')
        step.addPad(68, 2.5, 'zhyy', 'negative')
        step.unaffectAll()
        for zh in self.zhs:
            step.affect(zh)
        step.addPad(57, 3.5, 'fxjt')
        step.addPad(68, 2.5, 'zhfh')
        step.unaffectAll()
        step.VON()


    def do_film(self):
        if board.map_flag:
            step.affect('map')
            step.selectSymbol('base_film_map')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                for signal in self.signalLays:
                    step.selectChange('base_film_top') if board.signal_dict.get(signal) == 't' else step.selectChange('base_film_bot')
                    step.copySel(signal)
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
        else:
            for signal in self.signalLays:
                sym = 'base_film_top' if board.signal_dict.get(signal) == 't' else 'base_film_bot'
                step.affect(signal)
                step.addPad(step.profile2.xmin + 5, step.sr2.ymax - 57, sym)
                step.addPad(step.profile2.xmin + 5, step.sr2.ymin + 57, sym)
                step.addPad(step.profile2.xmax - 5, step.sr2.ymax - 57, sym, angle=180)
                step.addPad(step.profile2.xmax - 5, step.sr2.ymin + 72, sym, angle=180)
                step.unaffectAll()
            step.affect('map')
            step.addPad(step.profile2.xmin + 5, step.sr2.ymax - 57, 'base_film_map')
            step.addPad(step.profile2.xmin + 5, step.sr2.ymin + 57, 'base_film_map')
            step.addPad(step.profile2.xmax - 5, step.sr2.ymax - 57, 'base_film_map', angle=180)
            step.addPad(step.profile2.xmax - 5, step.sr2.ymin + 72, 'base_film_map', angle=180)
            step.unaffectAll()

    def do_wz(self):
        for signal in self.signalLays:
            mir = 'no'
            x1, x2 = 82, 135
            if board.signal_dict.get(signal) == 'b':
                mir = 'yes'
                x1, x2 = step.profile2.xmax - 50, step.profile2.xmax - 100
            step.affect(signal)
            step.addPad(x1, 2.5, 'zc-job', 'negative', mirror=mir)
            pieces = self.get_pcs_num()
            text = f'{board.lineEdit_pnl_w.text()}*{board.lineEdit_pnl_h.text()}={pieces}PCS/PNL {datetime.date.today().year}.{"%02d" % datetime.date.today().month}.{datetime.date.today().day} {self.user.upper()}'
            step.addText(x2, 2.5, text, 2, 2.3, 0.989993453, mir, fontname='simplex', polarity='negative')
            step.unaffectAll()
        step.VOF()
        for wz in self.wzs:
            step.affect(wz)
            mir = 'no'
            x1, x2 = 82, 135
            if 'b' in wz:
                mir = 'yes'
                x1, x2 = step.profile2.xmax - 50, step.profile2.xmax - 100
            step.addPad(x1, 2.5, 'zc-job', mirror=mir)
            step.addText(x2, 2.5, text, 2, 2.3, 0.989993453, mir, fontname='simplex')
            step.unaffectAll()
            step.VON()

    def do_py(self):
        for signal in self.signalLays:
            step.affect(signal)
        step.addPad(3.5, step.profile2.ymin + 11, 'py', 'negative')
        step.addPad(3.5, step.profile2.ymax - 11, 'py', 'negative')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 19, 'py', 'negative')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 11, 'py', 'negative')
        step.unaffectAll()
        step.VOF()
        for cov in self.covs:
            step.affect(cov)
        step.addPad(3.5, step.profile2.ymin + 11, 'r2500')
        step.addPad(3.5, step.profile2.ymax - 11, 'r2500')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 19, 'r2500')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 11, 'r2500')
        step.VON()

    def do_ldi(self):
        if board.map_flag:
            step.affect('map')
            step.selectSymbol('ldi-mark-t')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                for signal in self.signalLays:
                    step.selectChange('ldi-mark-t') if board.signal_dict.get(signal) == 't' else step.selectChange(
                        'ldi-mark-b')
                    step.selectPolarity('negative')
                    step.copySel(signal)
                step.selectChange('r1010')
                for yy in self.yys:
                    step.copySel(yy)
                step.selectChange('r1000')
                step.selectPolarity()
                for drill in self.drills:
                    step.copySel(drill)
                step.selectChange('r2500')
                step.VOF()
                for cov in self.covs:
                    step.copySel(cov)
                step.VON()
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
        else:
            for signal in self.signalLays:
                step.affect(signal)
                sym = 'ldi-mark-t' if board.signal_dict.get(signal) == 't' else 'ldi-mark-b'
                step.addPad(19, step.sr2.ymin - 2, sym, 'negative')
                step.addPad(19, step.sr2.ymax + 2, sym, 'negative')
                step.addPad(step.profile2.xmax - 23, step.sr2.ymax + 2, sym, 'negative')
                step.addPad(step.profile2.xmax - 19, step.sr2.ymin - 2, sym, 'negative')
                step.unaffectAll()
            step.affect('map')
            step.addPad(19, step.sr2.ymin - 2, 'ldi-mark-t')
            step.addPad(19, step.sr2.ymax + 2, 'ldi-mark-t')
            step.addPad(step.profile2.xmax - 23, step.sr2.ymax + 2, 'ldi-mark-t')
            step.addPad(step.profile2.xmax - 19, step.sr2.ymin - 2, 'ldi-mark-t')
            step.unaffectAll()
            step.VOF()
            for yy in self.yys:
                step.affect(yy)
            sym = 'r1010'
            step.addPad(19, step.sr2.ymin - 2, sym, 'negative')
            step.addPad(19, step.sr2.ymax + 2, sym, 'negative')
            step.addPad(step.profile2.xmax - 23, step.sr2.ymax + 2, sym, 'negative')
            step.addPad(step.profile2.xmax - 19, step.sr2.ymin - 2, sym, 'negative')
            step.unaffectAll()
            for drill in self.drills:
                step.affect(drill)
            step.addPad(19, step.sr2.ymin - 2, 'r1000')
            step.addPad(19, step.sr2.ymax + 2, 'r1000')
            step.addPad(step.profile2.xmax - 23, step.sr2.ymax + 2, 'r1000')
            step.addPad(step.profile2.xmax - 19, step.sr2.ymin - 2, 'r1000')
            step.unaffectAll()
            for cov in self.covs:
                step.affect(cov)
            step.addPad(19, step.sr2.ymin - 2, 'r2500')
            step.addPad(19, step.sr2.ymax + 2, 'r2500')
            step.addPad(step.profile2.xmax - 23, step.sr2.ymax + 2, 'r2500')
            step.addPad(step.profile2.xmax - 19, step.sr2.ymin - 2, 'r2500')
            step.unaffectAll()
            step.VON()
    def do_lpi(self):
        for signal in self.signalLays:
            step.affect(signal)
        step.addPad(29.5, 9, 'lpi-3.0', 'negative')
        step.addPad(36, step.profile2.ymax - 9, 'lpi-2.5', 'negative')
        step.addPad(step.profile2.xmax - 35.5, step.profile2.ymax - 9, 'lpi-2.5', 'negative')
        step.addPad(step.profile2.xmax - 31, 9, 'lpi-2.5', 'negative')
        step.unaffectAll()
        step.VOF()
        for zh in self.zhs:
            step.affect(zh)
        step.addPad(29.5, 9, 'r6000')
        step.addPad(29.5, 9, 'donut_r5000x1000', 'negative')
        step.addPad(36, step.profile2.ymax - 9, 'r6000')
        step.addPad(36, step.profile2.ymax - 9, 'donut_r5000x1000', 'negative')
        step.addPad(step.profile2.xmax - 35.5, step.profile2.ymax - 9, 'r6000')
        step.addPad(step.profile2.xmax - 35.5, step.profile2.ymax - 9, 'donut_r5000x1000', 'negative')
        step.addPad(step.profile2.xmax - 31, 9, 'r6000')
        step.addPad(step.profile2.xmax - 31, 9, 'donut_r5000x1000', 'negative')
        step.unaffectAll()
        for cov in self.covs:
            step.affect(cov)
        step.addPad(29.5, 9, 'r4000')
        step.addPad(36, step.profile2.ymax - 9, 'r4000')
        step.addPad(step.profile2.xmax - 35.5, step.profile2.ymax - 9, 'r4000')
        step.addPad(step.profile2.xmax - 31, 9, 'r4000')
        step.unaffectAll()
        step.VON()

    def do_qp(self):
        if board.map_flag:
            step.affect('map')
            step.selectSymbol('qp-map')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                step.selectChange('qp-xl')
                for signal in self.signalLays:
                    step.copySel(signal)
                step.selectChange('qp-f')
                for drill in self.drills:
                    step.copySel(drill)
                step.selectBreak()
                step.selectSymbol('r1500')
                for yy in self.yys:
                    step.copyToLayer(yy, 'yes', size=10)
                step.unaffectAll()
            step.unaffectAll()
            step.resetFilter()
            step.truncate(self.tmp_map)
        else:
            for signal in self.signalLays:
                step.affect(signal)
            # 左右
            step.addPad(7.6, step.profile2.ymax - 78, 'qp-xl', angle=90)
            step.addPad(7.6, step.profile2.ymin + 39, 'qp-xl', angle=90)
            step.addPad(step.profile2.xmax - 7.6, step.profile2.ymax - 36.5, 'qp-xl', angle=270)
            step.addPad(step.profile2.xmax - 7.6, 50, 'qp-xl', angle=270)
            step.unaffectAll()
            step.affect('map')
            # 左右
            step.addPad(7.6, step.profile2.ymax - 78, 'qp-map', angle=90)
            step.addPad(7.6, step.profile2.ymin + 39, 'qp-map', angle=90)
            step.addPad(step.profile2.xmax - 7.6, step.profile2.ymax - 36.5, 'qp-map', angle=270)
            step.addPad(step.profile2.xmax - 7.6, 50, 'qp-map', angle=270)
            step.unaffectAll()
            for drill in self.drills:
                step.affect(drill)
            # 左右
            step.addPad(7.6, step.profile2.ymax - 78, 'qp-f', angle=90)
            step.addPad(7.6, step.profile2.ymin + 39, 'qp-f', angle=90)
            step.addPad(step.profile2.xmax - 7.6, step.profile2.ymax - 36.5, 'qp-f', angle=270)
            step.addPad(step.profile2.xmax - 7.6, 50, 'qp-f', angle=270)
            step.selectBreak()
            step.unaffectAll()
            step.affect(self.drills[0])
            step.selectSymbol('r1500')
            for yy in self.yys:
                step.copyToLayer(yy, 'yes', size=10)
            step.unaffectAll()

    def do_donut(self):
        for signal in self.signalLays:
            if board.signal_dict.get(signal) == 't':
                step.affect(signal)
        step.VOF()
        xb1, xb3, xt1, xt3 = 85, step.profile2.xmax - 70, 57, step.profile2.xmax - 77
        # 下上
        step.addPad(xb1, step.sr2.ymin - 3.5, 'donut_r2000x1100', 'negative')
        step.addPad(xb1 + 3, step.sr2.ymin - 3.5, 'donut_r2000x1200', 'negative')
        step.addPad(xb1 + 6, step.sr2.ymin - 3.5, 'donut_r2000x1300', 'negative')
        step.addPad(xb1 + 15, step.sr2.ymin - 3.5, '1-ws', angle=270)  # 线宽线距symbol
        step.addPad(xb3, step.sr2.ymin - 3.5, 'donut_r2000x1100', 'negative')
        step.addPad(xb3 + 3, step.sr2.ymin - 3.5, 'donut_r2000x1200', 'negative')
        step.addPad(xb3 + 6, step.sr2.ymin - 3.5, 'donut_r2000x1300', 'negative')
        step.addPad(xb3 + 15, step.sr2.ymin - 3.5, '1-ws', angle=270)  # 线宽线距symbol
        step.addPad(xt1, step.sr2.ymax + 3.5, 'donut_r2000x1100', 'negative')
        step.addPad(xt1 + 3, step.sr2.ymax + 3.5, 'donut_r2000x1200', 'negative')
        step.addPad(xt1 + 6, step.sr2.ymax + 3.5, 'donut_r2000x1300', 'negative')
        step.addPad(xt1 + 15, step.sr2.ymax + 3.5, '1-ws', angle=270)  # 线宽线距symbol
        step.addPad(xt3, step.sr2.ymax + 3.5, 'donut_r2000x1100', 'negative')
        step.addPad(xt3 + 3, step.sr2.ymax + 3.5, 'donut_r2000x1200', 'negative')
        step.addPad(xt3 + 6, step.sr2.ymax + 3.5, 'donut_r2000x1300', 'negative')
        step.addPad(xt3 + 15, step.sr2.ymax + 3.5, '1-ws', angle=270)  # 线宽线距symbol
        # 左右
        step.unaffectAll()
        for zh in self.zhs:
            step.affect(zh)
        step.addPad(xb1, step.sr2.ymin - 3.5, 'r1000', nx=3, dx=3000)
        step.addPad(xb3, step.sr2.ymin - 3.5, 'r1000', nx=3, dx=3000)
        step.addPad(xt1, step.sr2.ymax + 3.5, 'r1000', nx=3, dx=3000)
        step.addPad(xt3, step.sr2.ymax + 3.5, 'r1000', nx=3, dx=3000)
        step.unaffectAll()
        for cov in self.covs:
            step.affect(cov)
        step.addPad(xb1, step.sr2.ymin - 3.5, 'r1500', nx=3, dx=3000)
        step.addPad(xb3, step.sr2.ymin - 3.5, 'r1500', nx=3, dx=3000)
        step.addPad(xt1, step.sr2.ymax + 3.5, 'r1500', nx=3, dx=3000)
        step.addPad(xt3, step.sr2.ymax + 3.5, 'r1500', nx=3, dx=3000)
        step.unaffectAll()
        step.VON()


        for signal in self.signalLays:
            y = step.sr2.ymax + 2.5 if board.signal_dict.get(signal) == 't' else step.sr2.ymax + 6
            step.affect(signal)
            step.addPad(106.5, y, 'donut_s3000x2000', 'negative', nx=3, dx=5000)
            step.addPad(step.profile2.xmax - 93.5, y, 'donut_s3000x2000', 'negative', nx=3, dx=5000)
            step.unaffectAll()
        if self.covs:
            for cov in self.covs:
                if cov == 'c1':
                    y = step.sr2.ymax + 2.5 if board.signal_dict.get(self.signalLays[0]) == 't' else step.sr2.ymax + 6
                    step.affect(cov)
                    step.addPad(106.5, y, 'r2500', nx=3, dx=5000)
                    step.addPad(step.profile2.xmax - 93.5, y, 'r2500', nx=3, dx=5000)
                    step.unaffectAll()
                else:
                    y = step.sr2.ymax + 2.5 if board.signal_dict.get(self.signalLays[-1]) == 't' else step.sr2.ymax + 6
                    step.affect(cov)
                    step.addPad(106.5, y, 'r2500', nx=3, dx=5000)
                    step.addPad(step.profile2.xmax - 93.5, y, 'r2500', nx=3, dx=5000)
                    step.unaffectAll()

    def do_2d(self):
        for signal in self.signalLays:
            step.affect(signal)
        step.addPad(100, step.sr2.ymax + 4.5, '2d', 'negative')
        step.addPad(step.profile2.xmax - 100, step.sr2.ymax + 4.5, '2d', 'negative')
        step.unaffectAll()
        step.affect('2d')
        step.addPad(100, step.sr2.ymax + 4.5, '2d')
        step.addPad(step.profile2.xmax - 100, step.sr2.ymax + 4.5, '2d')
        step.unaffectAll()

    def do_au_text(self):
        for signal in self.signalLays:
            mir = 'no' if board.signal_dict.get(signal) == 't' else 'yes'
            x = 52 if board.signal_dict.get(signal) == 't' else 70
            y = step.sr2.ymin - 2
            step.affect(signal)
            text = 'AU:SQ/MM(%)'
            step.addText(x, y, text, 1, 1.2, 0.492125988,mir,fontname='simple', polarity='negative')
            step.unaffectAll()

    def do_jt_line(self):
        if board.map_flag:
            step.affect('map')
            step.setAttrFilter2('.out_flag')
            step.selectAll()
            step.resetFilter()
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect('map')
                step.setAttrFilter2('.out_flag')
                step.selectAll()
                step.resetFilter()
                step.selectReverse()
                if step.Selected_count():
                    step.copySel(self.tmp_map + '+++')
                    step.unaffectAll()
                    step.affect(self.tmp_map)
                    step.selectBreak()
                    step.clip_area(margin=500, ref_layer=self.tmp_map + '+++')
                    for signal in self.signalLays:
                        step.copySel(signal, 'yes')
                    step.unaffectAll()
                    step.removeLayer(self.tmp_map + '+++')
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
        else:
            step.createLayer(self.tmp_map + '+++')
            step.affect(self.tmp_map + '+++')
            step.addAttr_zl('.out_flag,int=233')
            step.addLine(step.profile2.xmin + 3, step.profile2.ymin + 45, step.profile2.xmin + 3,
                         step.profile2.ymax - 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmin - 9, step.profile2.ymin + 45, step.profile2.xmin - 9,
                         step.profile2.ymax - 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmin + 3, step.profile2.ymin + 45, step.profile2.xmin - 9,
                         step.profile2.ymin + 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmin + 3, step.profile2.ymax - 45, step.profile2.xmin - 9,
                         step.profile2.ymax - 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmax - 3, step.profile2.ymin + 45, step.profile2.xmax - 3,
                         step.profile2.ymax - 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmax + 9, step.profile2.ymin + 45, step.profile2.xmax + 9,
                         step.profile2.ymax - 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmax - 3, step.profile2.ymin + 45, step.profile2.xmax + 9,
                         step.profile2.ymin + 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmax - 3, step.profile2.ymax - 45, step.profile2.xmax + 9,
                         step.profile2.ymax - 45, 'r401', attributes='yes')
            step.resetAttr()
            step.clip_area(margin=500, ref_layer='map')
            for signal in self.signalLays:
                step.copySel(signal, 'yes')
            step.unaffectAll()
            step.removeLayer(self.tmp_map + '+++')
            step.affect('map')
            # 加flzddw-jt线
            step.addAttr_zl('.out_flag,int=233')
            step.addLine(step.profile2.xmin + 3, step.profile2.ymin + 45, step.profile2.xmin + 3,
                         step.profile2.ymax - 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmin - 9, step.profile2.ymin + 45, step.profile2.xmin - 9,
                         step.profile2.ymax - 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmin + 3, step.profile2.ymin + 45, step.profile2.xmin - 9,
                         step.profile2.ymin + 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmin + 3, step.profile2.ymax - 45, step.profile2.xmin - 9,
                         step.profile2.ymax - 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmax - 3, step.profile2.ymin + 45, step.profile2.xmax - 3,
                         step.profile2.ymax - 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmax + 9, step.profile2.ymin + 45, step.profile2.xmax + 9,
                         step.profile2.ymax - 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmax - 3, step.profile2.ymin + 45, step.profile2.xmax + 9,
                         step.profile2.ymin + 45, 'r401', attributes='yes')
            step.addLine(step.profile2.xmax - 3, step.profile2.ymax - 45, step.profile2.xmax + 9,
                         step.profile2.ymax - 45, 'r401', attributes='yes')
            step.resetAttr()
            step.unaffectAll()


    def do_sc_mark(self):
        for signal in self.signalLays:
            step.affect(signal)
        step.addPad(4, 15, '1-sc-mark')
        step.addPad(4, 13.8, 'rect1700x750')
        step.addText(3.2, 13.5, '0', 0.5, 0.5, 0.2624672055, fontname='simple', polarity='negative')
        step.addPad(2.8, 15, 'rect750x1700')
        step.addText(2.5, 15.8, '0', 0.5, 0.5, 0.2624672055, angle=90, fontname='simple', polarity='negative')
        step.addPad(4, step.profile2.ymax - 15, '1-sc-mark')
        step.addPad(2.8, step.profile2.ymax - 15, 'rect750x1700')
        step.addText(2.5, step.profile2.ymax - 14.2, step.profile2.ymax - 15 - 15, 0.5, 0.5, 0.2624672055, angle=90, fontname='simple', polarity='negative')
        step.addPad(step.profile2.xmax - 4, step.profile2.ymax - 15, '1-sc-mark')
        step.addPad(step.profile2.xmax - 2.8, step.profile2.ymax - 15, 'rect750x1700')
        step.addText(step.profile2.xmax - 2.5, step.profile2.ymax - 15.8, step.profile2.ymax - 15 - 15, 0.5, 0.5, 0.2624672055, angle=270,fontname='simple', polarity='negative')
        step.addPad(step.profile2.xmax - 4, 15, '1-sc-mark')
        step.addPad(step.profile2.xmax - 2.8, 15, 'rect750x1700')
        step.addPad(step.profile2.xmax - 4, 13.8, 'rect1700x750')
        step.addText(step.profile2.xmax - 2.5, 14.2, '0', 0.5, 0.5, 0.2624672055, angle=270, fontname='simple', polarity='negative')
        step.addText(step.profile2.xmax - 4.8, 13.5, step.profile2.xmax - 4 - 4, 0.5, 0.5, 0.2624672055, fontname='simple', polarity='negative')
        step.unaffectAll()
        for cov in self.covs:
            step.affect(cov)
        step.addPad(4, 15, 'r1300')
        step.addPad(4, step.profile2.ymax - 15, 'r1300')
        step.addPad(step.profile2.xmax - 4, step.profile2.ymax - 15, 'r1300')
        step.addPad(step.profile2.xmax - 4, 15, 'r1300')
        step.unaffectAll()


    def do_cov(self):
        """
        覆盖面加文字并在线路层掏开  反面需要镜像
        """
        for cov in self.covs:
            mir = 'no'
            x = 70
            if cov == 'c2':
                mir = 'yes'
                x = 78
            tmp_cov = f'{cov}+++{step.pid}'
            step.createLayer(tmp_cov)
            step.affect(tmp_cov)
            step.addText(x, step.sr2.ymax + 0.5, cov.upper(), 5, 5, 2.296587944, mir, fontname='simple')
            step.unaffectAll()
        # 覆盖膜加切线和序号
        if float(board.lineEdit_pnl_h.text()) > 300:
            repeat_tx, repeat_ty = [], []
            cut_ys = []
            for name, xmin, xmax, ymin, ymax in zip(step.info2.get('gREPEATstep'),
                                                        step.info2.get('gREPEATxmin'),
                                                        step.info2.get('gREPEATxmax'),
                                                        step.info2.get('gREPEATymin'),
                                                        step.info2.get('gREPEATymax')):
                if 'set' in name:
                    repeat_ty.append(ymin)
                    repeat_ty.append(ymax)
            repeat_ty = sorted(list(set(repeat_ty)))

            if len(repeat_ty) > 2 and self.covs:
                i = 1
                while i < len(repeat_ty) - 1:
                    ty = (repeat_ty[i + 1] + repeat_ty[i]) / 2
                    cut_ys.append(ty)
                    i += 2
            if len(cut_ys):
                for y in cut_ys:
                    for cov in self.covs:
                        step.affect(cov)
                    step.addLine(step.profile2.xmin, y, step.profile2.xmax, y, 'r100')
                    step.unaffectAll()
                for cov in self.covs:
                    i = len(cut_ys) + 1
                    for y in cut_ys:
                        mir = 'no'
                        x = (step.profile2.xmin + step.sr2.xmin) / 2
                        if cov == 'c2':
                            mir = 'yes'
                            x = (step.profile2.xmin + step.sr2.xmin) / 2 + 2.7
                        tmp_cov = f'{cov}+++{step.pid}'
                        step.affect(tmp_cov)
                        # 最下面一个加横线下方和上方各一个
                        if i == len(cut_ys) + 1:
                            step.addText(x, y - 26, i, 5, 5, 2.296587944, mir, fontname='simple')
                            i -= 1
                        step.addText(x, y + 26, i, 5, 5, 2.296587944, mir, fontname='simple')
                        step.unaffectAll()
                        i -= 1
        for cov in self.covs:
            signal = self.signalLays[0]
            if cov == 'c2':
                signal = self.signalLays[-1]
            tmp_cov = f'{cov}+++{step.pid}'
            step.affect(tmp_cov)
            step.Contourize(0)
            step.copySel(cov)
            step.copyToLayer(signal, 'yes', size=500)
            step.unaffectAll()
            step.removeLayer(tmp_cov)


    # 加字唛
    def do_drill_letter(self):
        sign = jobname[jobname.rfind("-") - 7:jobname.rfind("-")] if "-" in jobname else jobname[-7:-1]
        for drill in self.drills:
            step.affect(drill)
            step.addText(step.profile2.xcenter - 55, step.profile2.ymax - 7.7, 'x+0y+0', 3.6068, 4.2164, 1.64041996,fontname='canned_67')
            step.addText(step.profile2.xcenter + 20, step.profile2.ymax - 7.7, f'{sign} {drill.upper()}', 3.6068, 4.2164, 1.64041996, fontname='canned_57')
            step.addPad(135, step.profile2.ymin + 5.5, 'lot-drill')
            step.unaffectAll()


    # 涨缩系数
    def do_scale(self):
        for signal in self.signalLays:
            x, mir = 89, 'no'
            if board.signal_dict.get(signal) == 'b':
                x, mir = 82, 'yes'
            step.affect(signal)
            step.addPad(x, step.sr2.ymax + 3.5, 'x-scale', 'negative', mirror=mir)
            step.addPad(x, step.sr2.ymax + 1.5, 'y-scale', 'negative', mirror=mir)
            step.unaffectAll()

    # 加边框线
    def do_border(self):
        # 上下位置
        distance = (710 - step.profile2.ysize)/2
        for signal in self.signalLays:
            step.affect(signal)
        step.addLine(step.profile2.xmin - 12.5, step.profile2.ymin, step.profile2.xmin - 12.5, step.profile2.ymax, 'r1100')
        step.addLine(step.profile2.xmax + 12.5, step.profile2.ymin, step.profile2.xmax + 12.5, step.profile2.ymax, 'r1100')
        step.addLine(step.profile2.xmin - 27, step.profile2.ymin - distance, step.profile2.xmin - 27, step.profile2.ymax + distance, 'r100')
        step.addLine(step.profile2.xmax + 27, step.profile2.ymin - distance, step.profile2.xmax + 27, step.profile2.ymax + distance, 'r100')
        step.addLine(step.profile2.xmin - 27, step.profile2.ymin - distance, step.profile2.xmax + 27, step.profile2.ymin - distance, 'r100')
        step.addLine(step.profile2.xmin - 27, step.profile2.ymax + distance, step.profile2.xmax + 27, step.profile2.ymax + distance, 'r100')
        step.unaffectAll()
        border1 = f'border+++{step.pid}'
        border2 = f'tmp+++{step.pid}'
        step.createLayer(border1)
        step.createLayer(border2)
        step.affect(border1)
        step.addLine(step.profile2.xmin - 27, step.profile2.ymin - distance, step.profile2.xmin - 27, step.profile2.ymax + distance, 'r100')
        step.addLine(step.profile2.xmax + 27, step.profile2.ymin - distance, step.profile2.xmax + 27, step.profile2.ymax + distance, 'r100')
        step.addLine(step.profile2.xmin - 27, step.profile2.ymin - distance, step.profile2.xmax + 27, step.profile2.ymin - distance,'r100')
        step.addLine(step.profile2.xmin - 27, step.profile2.ymax + distance, step.profile2.xmax + 27, step.profile2.ymax + distance,'r100')
        step.unaffectAll()
        step.affect(border2)
        step.addLine(step.profile2.xmin - 27, step.profile2.ycenter, step.profile2.xmin - 20, step.profile2.ycenter, 'r2000')
        step.addLine(step.profile2.xcenter, step.profile2.ymax + distance, step.profile2.xcenter, step.profile2.ymax + distance - 9, 'r2000')
        step.addLine(step.profile2.xcenter, step.profile2.ymin - distance, step.profile2.xcenter, step.profile2.ymin - distance + 9, 'r2000')
        step.addLine(step.profile2.xmax + 27, step.profile2.ycenter, step.profile2.xmax + 26, step.profile2.ycenter, 'r2000')
        step.unaffectAll()
        step.affect(border1)
        step.copySel(border2, 'yes')
        step.selectCutData()
        step.selectResize(-100)
        step.unaffectAll()
        step.affect(border2)
        step.Contourize(0)
        step.refSelectFilter(border1)
        if step.Selected_count():
            step.selectReverse()
            if step.Selected_count():
                step.selectDelete()
        for signal in self.signalLays:
            step.copySel(signal)
        step.unaffectAll()
        if self.zhs:
            step.affect(border1)
            step.selectResize(100)
            step.clip_area(margin=0)
            for zh in self.zhs:
                step.copySel(zh)
            step.unaffectAll()
        step.removeLayer(border1)
        step.removeLayer(border1 + '+++')
        step.removeLayer(border2)
        step.VOF()
        step.removeLayer(self.tmp_map)
        step.VON()

    def get_pcs_num(self):
        steps = step.info.get('gREPEATstep') # 获取set列表
        pcs_num_map = {}
        pcs_name = set()
        for s in steps:
            if 'set' in s:
                pcs_list = job.steps.get(s).info.get('gREPEATstep')
                pcs_name.update(pcs_list) # 获取每个set中的pcs列表
                if s not in pcs_num_map:
                    pcs_num_map[s] = 0
                pcs_num_map[s] += len(pcs_list)
        if len(pcs_name) > 1:
            return min(pcs_num_map.values())
        else:
            return sum(pcs_num_map.values())


class QComboBox(QComboBox):
    def wheelEvent(self, e):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # app.setStyle('fusion')
    app.setStyleSheet('QPushButton{font-family:"微软雅黑";font:11pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    if 'pnl' not in job.steps:
        QMessageBox.information(None, '提示', '该料号没有pnl')
        sys.exit()
    step = job.steps.get('pnl')
    board = SingleDoubleBoard()
    board.show()
    sys.exit(app.exec_())
