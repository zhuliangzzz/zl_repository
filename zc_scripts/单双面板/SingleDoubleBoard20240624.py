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

import SingleDoubleBoardUI20240624 as ui
import genClasses as gen


class SingleDoubleBoard(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        #
        self.signal_dict = {}
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
            self.tableWidget.setCellWidget(row, 1, combo)
        self.pushButton_run.setIcon(qtawesome.icon('fa.upload', color='cyan'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='cyan'))
        self.pushButton_run.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            'QPushButton{font:11pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')

    def run(self):
        # 取到面向
        for row in range(self.tableWidget.rowCount()):
            k = self.tableWidget.item(row, 0).text()
            v = 't' if self.tableWidget.cellWidget(row, 1).currentText() == '正' else 'b'
            self.signal_dict.update({k: v})
        # print(self.signal_dict)
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
        self.panel.do_border()
        QMessageBox.information(None, 'tips', '执行完毕!')


class Panel():
    def __init__(self):
        self.user = job.getUser()
        # 线路
        self.signalLays = board.signal_layers
        # 覆盖膜
        self.covs = []
        for row in job.matrix.returnRows('board', 'coverlay'):
            if re.match('c\d+$', row):
                self.covs.append(row)
        # 文字层
        self.wzs = job.matrix.returnRows('board', 'silk_screen')

    # 清空层创建层
    def ClearAndCreate(self):
        step.VOF()
        for layer in ('gtl', 'gbl', 'gto', 'gbo', 'c1', 'c2', 'f1', 'yy1', 'gts', 'gbs', 'map'):
            step.affect(layer)
        step.selectDelete()
        step.VON()
        step.unaffectAll()
        if not step.isLayer('map'):
            step.createLayer('map')
        step.prof_to_rout('map', 0.1)

    # 铺铜
    def do_surface(self):
        string = str.join('\;', step.info.get('gSRstep'))
        for lay in self.signalLays:
            step.affect(lay)
        step.srFill_2(step_margin_x=1, step_margin_y=1, stop_at_steps=string)
        step.unaffectAll()

    def do_fxk(self):
        for lay in self.signalLays:
            step.affect(lay)
        for cov in self.covs:
            step.affect(cov)
        for wz in self.wzs:
            step.affect(wz)
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
        for cov in self.covs:
            step.affect(cov)
        step.addPad(step.profile2.xmin + 2.5, 2.5, 'r2001')
        step.addPad(step.profile2.xmin + 2.5, step.profile2.ymax - 2.5, 'r2001')
        step.addPad(step.profile2.xmin + 4.5, step.profile2.ymax - 2.5, 's5000')
        step.addPad(step.profile2.xmin + 8.5, step.profile2.ymax - 2.5, 'r2001')
        step.addPad(step.profile2.xmin + 9.5, step.profile2.ymax - 2.5, 's5000')
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
        step.VON()

    # jsk s1500 wzdw r-mark-t c-mark-t wf-mark-t sy-mark
    def do_component(self):
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
        for cov in self.covs:
            step.affect(cov)
        for wz in self.wzs:
            step.affect(wz)
        step.addPad(57, 3.5, 'fxjt')
        step.addPad(68, 3.5, 'zf', mirror='yes')
        step.unaffectAll()
        step.VON()

    def do_film(self):
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
            step.affect(signal)
        step.addPad(82, 2.5, 'zc-job', 'negative')
        pieces = step.info.get('gNUM_REPEATS') * job.steps.get('set').info.get('gNUM_REPEATS')
        text = f'{board.lineEdit_pnl_w.text()}*{board.lineEdit_pnl_h.text()}={pieces}PCS/PNL {datetime.date.today().year}.{"%02d" % datetime.date.today().month}.{datetime.date.today().day} {self.user.upper()}'
        step.addText(135, 2.5, text, 2, 2.3, 0.989993453, fontname='simplex', polarity='negative')
        step.unaffectAll()
        step.VOF()
        for cov in self.covs:
            step.affect(cov)
        for wz in self.wzs:
            step.affect(wz)
        # step.addPad(195, 2.5, 'zc-job', mirror='yes')
        # step.addText(145, 2.5, text, mirror='yes', fontname='simplex')
        step.addPad(step.profile2.xmax - 50, 2.5, 'zc-job', mirror='yes')
        step.addText(step.profile2.xmax - 100, 2.5, text, 2, 3, 0.989993453, mirror='yes', fontname='simplex')
        step.unaffectAll()
        step.VON()

    def do_py(self):
        for signal in self.signalLays:
            step.affect(signal)
        step.addPad(3.5, step.profile2.ymin + 12, 'py', 'negative')
        step.addPad(3.5, step.profile2.ymax - 12, 'py', 'negative')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 16, 'py', 'negative')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 12, 'py', 'negative')
        step.unaffectAll()

    def do_ldi(self):
        for signal in self.signalLays:
            step.affect(signal)
            sym = 'ldi-mark-t' if board.signal_dict.get(signal) == 't' else 'ldi-mark-b'
            step.addPad(19, step.profile2.ymin + 8.5, sym, 'negative')
            step.addPad(19, step.profile2.ymax - 8.5, sym, 'negative')
            step.addPad(step.profile2.xmax - 8, step.profile2.ymax - 12, sym, 'negative')
            step.addPad(step.profile2.xmax - 19, step.profile2.ymin + 8.5, sym, 'negative')
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
        step.removeLayer(border1)
        step.removeLayer(border1 + '+++')
        step.removeLayer(border2)


class QComboBox(QComboBox):
    def wheelEvent(self, e):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # app.setStyle('fusion')
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    if 'pnl' not in job.steps:
        QMessageBox.infomation(None, '提示', '该料号没有pnl')
        sys.exit()
    step = job.steps.get('pnl')
    board = SingleDoubleBoard()
    board.show()
    sys.exit(app.exec_())
