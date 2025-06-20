#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:MultiLayerBoard.py
   @author:zl
   @time:2024/7/25 8:28
   @software:PyCharm
   @desc:
"""
import datetime
import os
import re
import sys
import itertools

import qtawesome
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QPixmap, QFont, QIcon, QRegExpValidator, QDoubleValidator
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QTableWidgetItem, QComboBox, QAbstractItemView, \
    QHeaderView

import MultiLayerBoardUI as ui
import genClasses as gen
import res_rc

class MultiLayerBoard(QWidget, ui.Ui_Form):
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
        self.signal_layers = job.SignalLayers
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
            self.type_name = '软板'
        elif __type == 'rf':
            self.type_name = '软硬结合板'
        elif __type == 'pc':
            self.type_name = '硬板'
        else:
            self.type_name = '其他'
        self.label_product.setText(self.type_name)
        # 表面处理
        __treatment = jobname[4:6]
        self.label_treatment.setText(__treatment)
        # 铺铜
        methods = ['实铜', '网格', '六边形']
        self.comboBox_method.addItems(methods)
        # 叠构
        exp = QRegExp(r'^(1|2)\+(1|2)(\+(1|2))*$')
        validator = QRegExpValidator(exp)
        self.comboBox_structure.setValidator(validator)
        self.comboBox_structure.setPlaceholderText('N+N...(N为1或2)')
        self.comboBox_structure.currentTextChanged.connect(self.load_position)
        self.lineEdit_margin_x.setValidator(QDoubleValidator())
        self.lineEdit_margin_y.setValidator(QDoubleValidator())
        self.lineEdit_margin_x.setText('1')
        self.lineEdit_margin_y.setText('1')
        # 面向
        header = ['线路层名', '面向']
        self.tableWidget.setColumnCount(len(header))
        self.tableWidget.setHorizontalHeaderLabels(header)
        self.tableWidget.setRowCount(len(self.signal_layers))
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.verticalHeader().hide()
        for row, lay in enumerate(self.signal_layers):
            self.tableWidget.setItem(row, 0, QTableWidgetItem(lay))
        if len(self.signal_layers) < 7:
            structures = self.get_structure(len(self.signal_layers))
            self.comboBox_structure.addItems(structures)
            self.comboBox_structure.setCurrentText(structures[0])
        self.pushButton_make_map.setIcon(qtawesome.icon('mdi.target', color='cyan'))
        self.pushButton_run.setIcon(qtawesome.icon('fa.upload', color='cyan'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='cyan'))
        self.pushButton_make_map.clicked.connect(self.make_map)
        self.pushButton_run.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            'QComboBox{font-family:微软雅黑;} QPushButton{font:11pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

    def load_position(self):
        structure = self.comboBox_structure.currentText()
        list_ = [int(i) for i in structure.split('+')]
        i = -1
        for i_ in list_:
            i += i_
            if i_ == 1:
                combo = QComboBox()
                combo.setFont(QFont('微软雅黑', 9))
                combo.addItems(['正', '反'])
                combo.setCurrentText('正')
                self.tableWidget.setCellWidget(i, 1, combo)
            else:
                combo = QComboBox()
                combo.setFont(QFont('微软雅黑', 9))
                combo.addItems(['正', '反'])
                combo.setCurrentText('正')
                self.tableWidget.setCellWidget(i - 1, 1, combo)
                combo = QComboBox()
                combo.setFont(QFont('微软雅黑', 9))
                combo.addItems(['正', '反'])
                combo.setCurrentText('反')
                self.tableWidget.setCellWidget(i, 1, combo)
        # 最后一层设置为反
        self.tableWidget.cellWidget(self.tableWidget.rowCount() - 1, 1).setCurrentText('反')

    def make_map(self):
        step.initStep()
        self.panel = Panel()
        self.panel.make_map_layer()

    def run(self):
        if len(self.signal_layers) < 3:
            QMessageBox.warning(self, '提示', '该料号不是多层板')
            sys.exit()
        # 判断叠构是否正确
        self.structure = self.comboBox_structure.currentText()
        if self.structure == '':
            QMessageBox.warning(self, '提示', '请选择或输入叠构')
            return
        structure_array = self.structure.split('+')
        count = 0
        for n in structure_array:
            count += int(n)
        if count != len(self.signal_layers):
            QMessageBox.warning(self, '提示', '叠构错误')
            return
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
        self.fill_sur = 'surface'
        if self.comboBox_method.currentText() == '网格':
            self.fill_sur = 'grid'
        elif self.comboBox_method.currentText() == '六边形':
            self.fill_sur = 'lbx'
        step.initStep()
        self.panel = Panel()
        self.panel.ClearAndCreate()
        self.panel.do_surface()
        self.panel.do_fxk()
        self.panel.do_sy()
        self.panel.do_component()
        self.panel.do_fxjt()
        self.panel.do_wz()
        self.panel.do_py()
        self.panel.do_ldi()
        self.panel.do_scale()
        self.panel.do_2d()
        self.panel.do_b2()
        self.panel.do_x_ray()
        self.panel.do_lpi()
        self.panel.do_qp()
        self.panel.do_donut()
        self.panel.do_au_text()
        self.panel.do_sc_mark()
        # self.panel.do_cov()
        self.panel.do_drill_letter()
        self.panel.do_border()
        self.panel.do_film()
        self.panel.do_clear_tmp()
        QMessageBox.information(board, 'tips', '执行完毕!')

    @classmethod
    def get_structure(cls, num):
        results = []
        for i in range(2, num + 1):
            for repeats in itertools.product('12', repeat=i):
                if sum([int(repeat) for repeat in repeats]) == num:
                    results.append(repeats)
        return list(map(lambda result: '+'.join(result), results))

    # 根据上下层得出通孔
    def get_through_drills(self, n, m):
        through_drills = []
        for i in range(2, n + 1):
            for j in range(m, len(self.signal_layers) + 1):
                if step.isLayer(f'l{i}-{j}d'):
                    through_drills.append(f'l{i}-{j}d')
        return through_drills


class Panel():
    def __init__(self):
        self.user = job.getUser()
        self.tmp_map = f'map+++{step.pid}'
        self.wz_map = f'wz_map+++{step.pid}'  # 字符symbol用来打散复制到选镀层掏开0.2
        self.cus = None  # 客户类型
        # 线路
        self.signalLays = board.signal_layers
        # 外层线路
        self.out_signals = [self.signalLays[0], self.signalLays[-1]]
        # 内层线路
        self.inner_signals = [self.signalLays[int(len(self.signalLays)/2) -1], self.signalLays[int(len(self.signalLays)/2)]] if len(self.signalLays) % 2 == 0 else [self.signalLays[int(len(self.signalLays)/2)]]
        # 次外层
        self.second_signals = [s for s in self.signalLays[1: -1] if s not in self.inner_signals]
        # 覆盖膜
        self.covs = []
        for row in job.matrix.returnRows('board', 'coverlay'):
            if re.match('c\d+$', row):
                self.covs.append(row)
        # 阻焊层, 印油层
        self.zhs, self.dks, self.yys = [], [], []
        for row in job.matrix.returnRows('board', 'solder_mask'):
            if re.match('g(t|b)s$', row):
                self.zhs.append(row)
            if re.match('dk(t|b)$', row):
                self.dks.append(row)
        for row in job.matrix.returnRows():
            if re.match('yy(\d+)$', row):
                self.yys.append(row)
        # 文字层
        self.wzs = []
        for row in job.matrix.returnRows('board', 'silk_screen'):
            if re.match('g(t|b|\d+)o$', row):
                self.wzs.append(row)
        # 钻孔层
        self.drills = job.matrix.returnRows('board', 'drill')
        self.buried_drills = list(filter(lambda d: re.match('l\d+-\d+d', d), self.drills))
        # for row in job.matrix.returnRows('board', 'drill'):
        #     if re.match('f\d+', row):
        #         self.drills.append(row)

    def make_map_layer(self):
        if step.isLayer('map'):
            step.truncate('map')
        else:
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
        x1, y1 = 3.5, step.profile2.ymax - 21
        x2, y2 = 3.5, step.profile2.ymin + 18
        x3, y3 = step.profile2.xmax - 3.5, step.profile2.ymax - 54
        x4, y4 = step.profile2.xmax - 3.5, step.profile2.ymin + 18
        step.addPad(x1, y1, sym, 'positive', 180)
        step.addPad(x2, y2, sym, 'positive')
        step.addPad(x3, y3, sym, 'positive')
        step.addPad(x4, y4, sym, 'positive')
        # step.addPad(step.profile2.xmin + 21, step.profile2.ymin + 3.5, sym, 'positive', 270)
        # step.addPad(step.profile2.xmin + 21, step.profile2.ymax - 3.5, sym, 'positive', 270)
        # step.addPad(step.profile2.xmax - 25, step.profile2.ymax - 3.5, sym, 'positive', 90)
        step.addPad(25, 3.5, 'jsk')
        step.addPad(50, step.profile2.ymax - 3.5, 'jsk')
        step.addPad(step.profile2.xmax - 48, step.profile2.ymax - 3.5, 'jsk')
        step.addPad(step.profile2.xmax - 40, 3.5, 'jsk')
        step.addPad(3.5, step.profile2.ymax - 44, 'jsk')
        step.addPad(3.5, step.profile2.ymin + 41.5, 'jsk')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 39, 'jsk')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 44, 'jsk')
        # 中间
        step.addPad(3.5, step.profile2.ycenter - 7, 'jsk')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 2, 'jsk')
        # s1500
        step.addPad(27.5, 3.5, 's1500')
        step.addPad(47.5, step.profile2.ymax - 3.5, 's1500')
        step.addPad(step.profile2.xmax - 45.5, step.profile2.ymax - 3.5, 's1500')
        step.addPad(step.profile2.xmax - 37.5, 3.5, 's1500')
        step.addPad(3.5, step.profile2.ymax - 41.5, 's1500')
        step.addPad(3.5, step.profile2.ymin + 39.5, 's1500')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 36.5, 's1500')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 41.5, 's1500')
        # 中间
        step.addPad(3.5, step.profile2.ycenter - 4.5, 's1500')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 0.5, 's1500')
        # wzdw
        step.addPad(30.5, 3.5, 'wzdw')
        step.addPad(43.5, step.profile2.ymax - 3.5, 'wzdw')
        step.addPad(step.profile2.xmax - 41.5, step.profile2.ymax - 3.5, 'wzdw')
        step.addPad(step.profile2.xmax - 34.5, 3.5, 'wzdw')
        step.addPad(3.5, step.profile2.ymax - 38, 'wzdw')
        step.addPad(3.5, step.profile2.ymin + 37, 'wzdw')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 33, 'wzdw')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 38, 'wzdw')
        # 中间
        step.addPad(3.5, step.profile2.ycenter, 'wzdw')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 3.5, 'wzdw')
        # r-mark-t
        sym = 'r-mark-t'
        step.addPad(36, 3.5, sym)
        step.addPad(39, step.profile2.ymax - 3.5, sym)
        step.addPad(step.profile2.xmax - 35, step.profile2.ymax - 3.5, sym)
        step.addPad(step.profile2.xmax - 28, 3.5, sym)
        step.addPad(3.5, step.profile2.ymax - 32, sym, angle=270)
        step.addPad(3.5, step.profile2.ymin + 34, sym, angle=270)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 29, sym, angle=90)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 32, sym, angle=90)
        # 中间
        step.addPad(3.5, step.profile2.ycenter + 5.5, sym, angle=270)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 8, sym, angle=90)
        # c-mark-t
        sym = 'c-mark-t'
        step.addPad(40, 3.5, sym)
        step.addPad(61, step.profile2.ymax - 3.5, sym, 'positive', 180)
        step.addPad(step.profile2.xmax - 29, step.profile2.ymax - 3.5, sym, 'positive', 180)
        step.addPad(step.profile2.xmax - 24, 3.5, sym)
        step.addPad(3.5, step.profile2.ymax - 55, sym, 'positive', 270)
        step.addPad(3.5, step.profile2.ymin + 44, sym, 'positive', 270)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 41.5, sym, 'positive', 90)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 29, sym, 'positive', 90)
        # 中间
        step.addPad(3.5, step.profile2.ycenter - 19, sym, 'positive', 270)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 5, sym, 'positive', 90)
        # wf-mark-t
        sym = 'wf-mark-t'
        step.addPad(45.5, 3.5, sym)
        step.addPad(53, step.profile2.ymax - 3.5, sym)
        step.addPad(step.profile2.xmax - 52, step.profile2.ymax - 3.5, sym, 'positive', 180)
        step.addPad(step.profile2.xmax - 18, 3.5, sym)
        step.addPad(3.5, step.profile2.ymax - 49, sym, 'positive', 270)
        step.addPad(3.5, step.profile2.ymin + 26.5, sym, 'positive', 270)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 48.5, sym, 'positive', 270)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 48, sym, 'positive', 270)
        # 中间
        step.addPad(3.5, step.profile2.ycenter - 12.5, sym, 'positive', 270)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 12, sym, 'positive', 270)
        # sy-mark
        step.addPad(51, 3.5, 'sy-mark')
        step.addPad(65, step.profile2.ymax - 3.5, 'sy-mark')
        step.addPad(step.profile2.xmax - 58, step.profile2.ymax - 3.5, 'sy-mark', 'positive', 180)
        step.addPad(step.profile2.xmax - 43, 3.5, 'sy-mark')
        step.addPad(3.5, step.profile2.ymax - 28, 'sy-mark', 'positive', 270)
        step.addPad(3.5, step.profile2.ymin + 23.5, 'sy-mark', 'positive', 270)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 23, 'sy-mark', 'positive', 270)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 23.5, 'sy-mark', 'positive', 270)
        # 中间
        step.addPad(3.5, step.profile2.ycenter + 10, 'sy-mark', 'positive', 270)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 14, 'sy-mark', 'positive', 270)
        # film
        step.addPad(step.profile2.xmin + 5, step.profile2.ymax - 89, 'base_film_map')
        step.addPad(step.profile2.xmin + 5, step.profile2.ymin + 73, 'base_film_map')
        step.addPad(step.profile2.xmax - 5, step.profile2.ymax - 73, 'base_film_map', angle=180)
        step.addPad(step.profile2.xmax - 5, step.profile2.ymin + 73, 'base_film_map', angle=180)
        #
        sym = 'ldi-mark-t'
        step.addPad(19, step.sr2.ymin - 2, sym)
        step.addPad(19, step.sr2.ymax + 2, sym)
        step.addPad(step.profile2.xmax - 23, step.sr2.ymax + 2, sym)
        step.addPad(step.profile2.xmax - 19, step.sr2.ymin - 2, sym)
        # qp
        # 左右
        step.addPad(3.5, step.profile2.ymax - 75.5, 'qp', angle=90)
        step.addPad(3.5, step.profile2.ymin + 53, 'qp', angle=90)
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 61, 'qp', angle=270)
        step.addPad(step.profile2.xmax - 3.5, 57, 'qp', angle=270)
        # if len(self.signalLays) > 1:
        #     # 加flzddw-jt线
        #     step.addAttr_zl('.out_flag,int=233')
        #     step.addLine(step.profile2.xmin + 3, step.profile2.ymin + 45, step.profile2.xmin + 3, step.profile2.ymax - 45, 'r401', attributes='yes')
        #     step.addLine(step.profile2.xmin - 9, step.profile2.ymin + 45, step.profile2.xmin - 9, step.profile2.ymax - 45, 'r401', attributes='yes')
        #     step.addLine(step.profile2.xmin + 3, step.profile2.ymin + 45, step.profile2.xmin - 9, step.profile2.ymin + 45, 'r401', attributes='yes')
        #     step.addLine(step.profile2.xmin + 3, step.profile2.ymax - 45, step.profile2.xmin - 9, step.profile2.ymax - 45, 'r401', attributes='yes')
        #     step.addLine(step.profile2.xmax - 3, step.profile2.ymin + 45, step.profile2.xmax - 3, step.profile2.ymax - 45, 'r401', attributes='yes')
        #     step.addLine(step.profile2.xmax + 9, step.profile2.ymin + 45, step.profile2.xmax + 9, step.profile2.ymax - 45, 'r401', attributes='yes')
        #     step.addLine(step.profile2.xmax - 3, step.profile2.ymin + 45, step.profile2.xmax + 9, step.profile2.ymin + 45, 'r401', attributes='yes')
        #     step.addLine(step.profile2.xmax - 3, step.profile2.ymax - 45, step.profile2.xmax + 9, step.profile2.ymax - 45, 'r401', attributes='yes')
        #     step.resetAttr()
        # py
        step.addPad(3.5, step.profile2.ymin + 11, 'py')
        step.addPad(3.5, step.profile2.ymax - 11, 'py')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 19, 'py')
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 11, 'py')
        # 2d
        step.addPad(97.5, step.profile2.ymax - 8, '2d')
        step.addPad(step.profile2.xmax - 102.5, step.profile2.ymax - 8, '2d')
        # b2
        step.addPad(8, 10, 'sy-pnlb2')
        step.addPad(8, step.profile2.ymax - 10, 'sy-pnlb2')
        step.addPad(8, step.profile2.ymax - 16, 'sy-pnlb2')
        step.addPad(step.profile2.xmax - 8, step.profile2.ymax - 10, 'sy-pnlb2')
        step.addPad(step.profile2.xmax - 8, 10, 'sy-pnlb2')
        # x-ray
        step.addPad(20, 10, 'x-ray')
        step.addPad(20, step.profile2.ymax - 10, 'x-ray')
        step.addPad(step.profile2.xmax - 20, step.profile2.ymax - 10, 'x-ray')
        step.addPad(step.profile2.xmax - 20, 10, 'x-ray')
        step.unaffectAll()
        QMessageBox.information(board, 'tips', '创建完成!')
        sys.exit()


    # 清空层创建层
    def ClearAndCreate(self):
        step.VOF()
        for layer in self.signalLays + self.wzs + self.covs + self.zhs + self.dks + self.yys + self.drills:
            step.affect(layer)
        step.selectDelete()
        step.unaffectAll()
        if step.isLayer('2d'):
            step.truncate('2d')
        else:
            step.createLayer('2d')
        step.VON()
        if not board.map_flag:
            step.createLayer('map')
            step.prof_to_rout('map', 0.1)
        else:
            step.createLayer(self.tmp_map)
        step.createLayer(self.wz_map)
        # 保护层
        struct_arr = [int(i) for i in board.structure.split('+')]
        i = 0
        layer_list = []
        for i_ in struct_arr:
            i += i_
            if i_ == 2:
                layer_list.append([i - 1, i])

        print(layer_list)
        # 判断是否包含 layer_list
        if layer_list:
            pass
        step.PAUSE('A')


    # 铺铜
    def do_surface(self):
        # string = str.join('\;', step.info.get('gSRstep'))
        imps = list(filter(lambda s: s.startswith('imp'), step.info.get('gSRstep')))
        imp_profile = f'imp_profile+++{step.pid}'
        pnl_imp = f'pnl_imp+++{step.pid}'
        if imps:
            for imp in imps:
                imp_step = job.steps.get(imp)
                imp_step.initStep()
                imp_step.prof_to_rout(imp_profile)
                imp_step.affect(imp_profile)
                imp_step.selectCutData()
                imp_step.close()
            step.removeLayer(imp_profile + '+++')
            step.Flatten(imp_profile, pnl_imp)
        step_marigin_x = board.lineEdit_margin_x.text() if board.lineEdit_margin_x.text() != '' else 1
        step_marigin_y = board.lineEdit_margin_y.text() if board.lineEdit_margin_y.text() != '' else 1
        for i, lay in enumerate(self.signalLays):
            if board.type_name == '软硬结合板':  # 软硬结合板外层不铺
                if i == 0 or i == len(self.signalLays) - 1:
                    continue
            if i % 2:
                direction = 'even'
                x_off = 0.9
                y_off = 0.9
            else:
                direction = 'odd'
                x_off = 0
                y_off = 0
            step.affect(lay)
            step.srFill_2(step_margin_x=step_marigin_x, step_margin_y=step_marigin_y, nest_sr='no')
            if imps:
                step.clip_area('reference',margin=500,ref_layer=pnl_imp)
            if board.fill_sur == 'grid':
                line_width = 200
                # 网格铜外围线宽
                outline_width = 400
                # 网格铜边到边间距
                side_spacing = 600
                step.selectFill(type='standard', solid_type='surface', std_type='cross', x_off=x_off,
                                     y_off=y_off, std_line_width=line_width, std_step_dist=side_spacing,
                                     std_indent=direction, outline_draw='yes', outline_width=outline_width)
            elif board.fill_sur == 'lbx':
                x_off = 4.2 if i % 2 else 0
                y_off = 0
                step.selectFill(type='pattern', dx=12.6, dy=7.3, solid_type='surface', symbol='lbx_fill',
                                     x_off=x_off, y_off=y_off, std_indent=direction, cut_prims='yes')
            step.unaffectAll()
            step.resetFill()
        step.VOF()
        # for zh in self.zhs:
        #     step.affect(zh)
        # step.srFill_2()
        # step.unaffectAll()
        step.resetFill()
        # 20240709 对dks加网格
        if self.dks:
            for n, dk in enumerate(self.dks):
                if n % 2:
                    direction = 'even'
                else:
                    direction = 'odd'
                line_width = 200
                # 网格铜外围线宽
                outline_width = 200
                # 网格铜边到边间距
                side_spacing = 600
                step.affect(dk)
                step.srFill_2(nest_sr='no')
                if imps:
                    step.clip_area('reference', margin=500, ref_layer=pnl_imp)
                tmp = dk + '+++'
                step.copySel(tmp)
                step.unaffectAll()
                step.affect(tmp)
                step.selectResize(200)
                step.selectFill(type='standard', solid_type='surface', std_type='cross', x_off=0,
                                y_off=0, std_line_width=line_width, std_step_dist=side_spacing,
                                std_indent=direction, outline_draw='yes', outline_width=outline_width)
                step.copySel(dk, 'yes')
                step.unaffectAll()
                step.resetFill()
                step.removeLayer(tmp)
            for dk in self.dks:
                step.affect(dk)
            step.addRectangle(step.profile2.xmin, step.profile2.ymax, step.profile2.xmax, step.sr2.ymax - 1)
            step.addRectangle(step.profile2.xmin, step.profile2.ymin, step.profile2.xmax, step.sr2.ymin + 1)
            step.unaffectAll()
        for cov in self.covs:
            step.prof_to_rout(cov, 100)
        step.removeLayer(imp_profile)
        step.removeLayer(pnl_imp)
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
            # for signal in self.signalLays:
            #     step.affect(signal)
            # step.addPad(step.profile2.xmin + 4.5, step.profile2.ymax - 2.5, 's5000')
            # step.addPad(step.profile2.xmin + 9.5, step.profile2.ymax - 2.5, 's5000')
            # step.unaffectAll()
            step.affect('map')
            step.selectSymbol('rffxk')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                step.selectChange('fxk-wz')
                for wz in self.wzs:
                    step.copySel(wz)
                for yy in self.yys:
                    step.copySel(yy)
                step.selectChange('fxk-yy')
                for zh in self.zhs:
                    step.copySel(zh)
                step.selectChange('r2001')
                step.selectPolarity()
                for cov in self.covs:
                    step.copySel(cov)
                for drill in self.drills:
                    step.copySel(drill)
                step.selectChange('s5000')
                for signal in self.signalLays:
                    step.copySel(signal)
                step.selectChange('rffxk')
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
            for yy in self.yys:
                step.affect(yy)
            step.addPad(step.profile2.xmin + 2.5, 2.5, 'fxk-wz')
            step.addPad(step.profile2.xmin + 2.5, step.profile2.ymax - 2.5, 'fxk-wz')
            step.addPad(step.profile2.xmin + 7.5, step.profile2.ymax - 2.5, 'fxk-wz')
            step.addPad(step.profile2.xmin + 12.5, step.profile2.ymax - 2.5, 'fxk-wz')
            step.addPad(step.profile2.xmax - 2.5, 2.5, 'fxk-wz')
            step.addPad(step.profile2.xmax - 2.5, step.profile2.ymax - 2.5, 'fxk-wz')
            step.unaffectAll()
            for zh in self.zhs:
                step.affect(zh)
            step.addPad(step.profile2.xmin + 2.5, 2.5, 'fxk-yy')
            step.addPad(step.profile2.xmin + 2.5, step.profile2.ymax - 2.5, 'fxk-yy')
            step.addPad(step.profile2.xmin + 7.5, step.profile2.ymax - 2.5, 'fxk-yy')
            step.addPad(step.profile2.xmin + 12.5, step.profile2.ymax - 2.5, 'fxk-yy')
            step.addPad(step.profile2.xmax - 2.5, 2.5, 'fxk-yy')
            step.addPad(step.profile2.xmax - 2.5, step.profile2.ymax - 2.5, 'fxk-yy')
            step.unaffectAll()
            for cov in self.covs:
                step.affect(cov)
            step.addPad(step.profile2.xmin + 2.5, 2.5, 'r2001')
            step.addPad(step.profile2.xmin + 2.5, step.profile2.ymax - 2.5, 'r2001')
            step.addPad(step.profile2.xmin + 7.5, step.profile2.ymax - 2.5, 'r2001')
            step.addPad(step.profile2.xmin + 12.5, step.profile2.ymax - 2.5, 'r2001')
            step.addPad(step.profile2.xmax - 2.5, 2.5, 'r2001')
            step.addPad(step.profile2.xmax - 2.5, step.profile2.ymax - 2.5, 'r2001')
            step.unaffectAll()
            for signal in self.signalLays:
                step.affect(signal)
            step.addPad(step.profile2.xmin + 2.5, 2.5, 's5000')
            step.addPad(step.profile2.xmin + 2.5, step.profile2.ymax - 2.5, 's5000')
            step.addPad(step.profile2.xmin + 7.5, step.profile2.ymax - 2.5, 's5000')
            step.addPad(step.profile2.xmin + 12.5, step.profile2.ymax - 2.5, 's5000')
            step.addPad(step.profile2.xmax - 2.5, 2.5, 's5000')
            step.addPad(step.profile2.xmax - 2.5, step.profile2.ymax - 2.5, 's5000')
            step.addPad(step.profile2.xmin + 2.5, 2.5, 'rffxk', 'negative')
            step.addPad(step.profile2.xmin + 2.5, step.profile2.ymax - 2.5, 'rffxk', 'negative')
            step.addPad(step.profile2.xmin + 7.5, step.profile2.ymax - 2.5, 'rffxk', 'negative')
            step.addPad(step.profile2.xmin + 12.5, step.profile2.ymax - 2.5, 'rffxk', 'negative')
            step.addPad(step.profile2.xmax - 2.5, 2.5, 'rffxk', 'negative')
            step.addPad(step.profile2.xmax - 2.5, step.profile2.ymax - 2.5, 'rffxk', 'negative')
            step.unaffectAll()
            step.VON()
            step.affect('map')
            step.addPad(step.profile2.xmin + 2.5, 2.5, 'rffxk')
            step.addPad(step.profile2.xmin + 2.5, step.profile2.ymax - 2.5, 'rffxk')
            step.addPad(step.profile2.xmin + 7.5, step.profile2.ymax - 2.5, 'rffxk')
            step.addPad(step.profile2.xmin + 12.5, step.profile2.ymax - 2.5, 'rffxk')
            step.addPad(step.profile2.xmax - 2.5, 2.5, 'rffxk')
            step.addPad(step.profile2.xmax - 2.5, step.profile2.ymax - 2.5, 'rffxk')
            step.unaffectAll()

    def do_sy(self):
        if board.map_flag:
            step.affect('map')
            step.selectSymbol('sy-pin-t;sy-pin-b')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                step.copySel(self.wz_map)
                for signal in self.signalLays:
                    step.selectChange('sy-pin-t') if board.signal_dict.get(signal) == 't' else step.selectChange('sy-pin-b')
                    step.selectPolarity('negative')
                    step.copySel(signal)
                step.selectChange('r2500')
                step.selectPolarity()
                step.VOF()
                for cov in self.covs:
                    step.copySel(cov)
                step.selectChange('r3400')
                for dk in self.dks:
                    step.copySel(dk, 'yes')
                step.selectChange('r2000')
                for drill in self.drills:
                    step.copySel(drill)
                step.unaffectAll()
                step.VON()
            step.unaffectAll()
            step.truncate(self.tmp_map)
        else:
            for signal in self.signalLays:
                step.affect(signal)
                sym = 'sy-pin-t' if board.signal_dict.get(signal) == 't' else 'sy-pin-b'
                step.addPad(3.5, step.profile2.ymax - 21, sym, 'negative', 180)
                step.addPad(3.5, step.profile2.ymin + 18, sym, 'negative')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 54, sym, 'negative')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 18, sym, 'negative')
                step.unaffectAll()
            step.affect('map')
            step.addPad(3.5, step.profile2.ymax - 21, 'sy-pin-t', 'negative', 180)
            step.addPad(3.5, step.profile2.ymin + 18, 'sy-pin-t', 'negative')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 54, 'sy-pin-t', 'negative')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 18, 'sy-pin-t', 'negative')
            step.unaffectAll()
            step.VOF()
            for cov in self.covs:
                step.affect(cov)
            step.addPad(3.5, step.profile2.ymax - 21, 'r2500')
            step.addPad(3.5, step.profile2.ymin + 18, 'r2500')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 54, 'r2500')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 18, 'r2500')
            step.unaffectAll()
            for dk in self.dks:
                step.affect(dk)
            step.addPad(3.5, step.profile2.ymax - 21, 'r3400', 'negative')
            step.addPad(3.5, step.profile2.ymin + 18, 'r3400', 'negative')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 54, 'r3400', 'negative')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 18, 'r3400', 'negative')
            step.unaffectAll()
            # 避字符
            sym = 'sy-pin-t'
            step.affect(self.wz_map)
            step.addPad(3.5, step.profile2.ymax - 21, sym, 'positive', 180)
            step.addPad(3.5, step.profile2.ymin + 18, sym)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 54, sym)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 18, sym)
            step.unaffectAll()
            for drill in self.drills:
                step.affect(drill)
            step.addPad(3.5, step.profile2.ymax - 21, 'r2000')
            step.addPad(3.5, step.profile2.ymin + 18, 'r2000')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 54, 'r2000')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 18, 'r2000')
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
                step.selectChange('r2501')
                for dk in self.dks:
                    step.copySel(dk, 'yes')
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
                step.selectChange('r2501')
                for dk in self.dks:
                    step.copySel(dk)
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
                step.selectChange('r2501')
                for dk in self.dks:
                    step.copySel(dk)
                if board.radioButton_other.isChecked():
                    step.selectChange('r2800')
                    step.selectPolarity()
                    for cov in self.covs:
                        step.copySel(cov)
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
            step.affect('map')
            step.selectSymbol('r-mark-t')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                step.copySel(self.wz_map)
                for signal in self.signalLays:
                    step.selectChange('r-mark-t') if board.signal_dict.get(signal) == 't' else step.selectChange(
                        'r-mark-b')
                    step.selectPolarity('negative')
                    step.copySel(signal)
                step.selectChange('r2800')
                for dk in self.dks:
                    step.copySel(dk)
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
                step.copySel(self.wz_map)
                for signal in self.signalLays:
                    step.selectChange('c-mark-t') if board.signal_dict.get(signal) == 't' else step.selectChange(
                        'c-mark-b')
                    step.selectPolarity('negative')
                    step.copySel(signal)
                step.selectChange('r2100')
                step.selectPolarity()
                for cov in self.covs:
                    step.copySel(cov)
                step.selectChange('r2501')
                for dk in self.dks:
                    step.copySel(dk, 'yes')
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
            step.affect('map')
            step.selectSymbol('wf-mark-t')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                step.copySel(self.wz_map)
                for signal in self.signalLays:
                    step.selectChange('wf-mark-t') if board.signal_dict.get(signal) == 't' else step.selectChange(
                        'wf-mark-b')
                    step.selectPolarity('negative')
                    step.copySel(signal)
                step.selectChange('r1750')
                for zh in self.zhs:
                    step.copySel(zh)
                step.selectChange('r2600')
                for dk in self.dks:
                    step.copySel(dk)
                step.selectChange('donut_r2400x1750')
                step.selectPolarity()
                for yy in self.yys:
                    step.copySel(yy)
                if board.radioButton_other.isChecked():
                    step.selectChange('r2500')
                    for cov in self.covs:
                        step.copySel(cov)
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
                step.selectChange('r3501')
                for dk in self.dks:
                    step.copySel(dk)
                if board.radioButton_other.isChecked():
                    step.selectChange('r3000')
                    step.selectPolarity()
                    for cov in self.covs:
                        step.copySel(cov)
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
                step.addPad(3.5, step.profile2.ymax - 44, 'jsk')
                step.addPad(3.5, step.profile2.ymin + 41.5, 'jsk')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 39, 'jsk')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 44, 'jsk')
                # 中间
                step.addPad(3.5, step.profile2.ycenter - 7, 'jsk')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 2, 'jsk')
                # s1500
                step.addPad(27.5, 3.5, 's1500', 'negative')
                step.addPad(47.5, step.profile2.ymax - 3.5, 's1500', 'negative')
                step.addPad(step.profile2.xmax - 45.5, step.profile2.ymax - 3.5, 's1500', 'negative')
                step.addPad(step.profile2.xmax - 37.5, 3.5, 's1500', 'negative')
                step.addPad(3.5, step.profile2.ymax - 41.5, 's1500', 'negative')
                step.addPad(3.5, step.profile2.ymin + 39.5, 's1500', 'negative')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 36.5, 's1500', 'negative')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 41.5, 's1500', 'negative')
                # 中间
                step.addPad(3.5, step.profile2.ycenter - 4.5, 's1500', 'negative')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 0.5, 's1500', 'negative')
                # wzdw
                step.addPad(30.5, 3.5, 'wzdw', 'negative')
                step.addPad(43.5, step.profile2.ymax - 3.5, 'wzdw', 'negative')
                step.addPad(step.profile2.xmax - 41.5, step.profile2.ymax - 3.5, 'wzdw', 'negative')
                step.addPad(step.profile2.xmax - 34.5, 3.5, 'wzdw', 'negative')
                step.addPad(3.5, step.profile2.ymax - 38, 'wzdw', 'negative')
                step.addPad(3.5, step.profile2.ymin + 37, 'wzdw', 'negative')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 33, 'wzdw', 'negative')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 38, 'wzdw', 'negative')
                # 中间
                step.addPad(3.5, step.profile2.ycenter, 'wzdw', 'negative')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 3.5, 'wzdw', 'negative')
                # r-mark-t
                sym = 'r-mark-b' if board.signal_dict.get(signal) == 'b' else 'r-mark-t'
                step.addPad(36, 3.5, sym, 'negative')
                step.addPad(39, step.profile2.ymax - 3.5, sym, 'negative')
                step.addPad(step.profile2.xmax - 35, step.profile2.ymax - 3.5, sym, 'negative')
                step.addPad(step.profile2.xmax - 28, 3.5, sym, 'negative')
                step.addPad(3.5, step.profile2.ymax - 32, sym, 'negative', 270)
                step.addPad(3.5, step.profile2.ymin + 34, sym, 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 29, sym, 'negative', 90)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 32, sym, 'negative', 90)
                # 中间
                step.addPad(3.5, step.profile2.ycenter + 5.5, sym, 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 8, sym, 'negative', 90)
                # c-mark-t
                sym = 'c-mark-b' if board.signal_dict.get(signal) == 'b' else 'c-mark-t'
                step.addPad(40, 3.5, sym, 'negative')
                step.addPad(61, step.profile2.ymax - 3.5, sym, 'negative', 180)
                step.addPad(step.profile2.xmax - 29, step.profile2.ymax - 3.5, sym, 'negative', 180)
                step.addPad(step.profile2.xmax - 24, 3.5, sym, 'negative')
                step.addPad(3.5, step.profile2.ymax - 55, sym, 'negative', 270)
                step.addPad(3.5, step.profile2.ymin + 44, sym, 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 41.5, sym, 'negative', 90)
                step.addPad(step.profile2.xmax - 3.5, step.profile.ymin + 29, sym, 'negative', 90)
                # 中间
                step.addPad(3.5, step.profile2.ycenter - 19, sym, 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 5, sym, 'negative', 90)
                # wf-mark-t
                sym = 'wf-mark-b' if board.signal_dict.get(signal) == 'b' else 'wf-mark-t'
                step.addPad(45.5, 3.5, sym, 'negative')
                step.addPad(53, step.profile2.ymax - 3.5, sym, 'negative')
                step.addPad(step.profile2.xmax - 52, step.profile2.ymax - 3.5, sym, 'negative', 180)
                step.addPad(step.profile2.xmax - 18, 3.5, sym, 'negative')
                step.addPad(3.5, step.profile2.ymax - 49, sym, 'negative', 270)
                step.addPad(3.5, step.profile2.ymin + 26.5, sym, 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 48.5, sym, 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 48, sym, 'negative', 270)
                # 中间
                step.addPad(3.5, step.profile2.ycenter - 12.5, sym, 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 12, sym, 'negative', 270)
                # sy-mark
                step.addPad(51, 3.5, 'sy-mark', 'negative')
                step.addPad(65, step.profile2.ymax - 3.5, 'sy-mark', 'negative')
                step.addPad(step.profile2.xmax - 58, step.profile2.ymax - 3.5, 'sy-mark', 'negative', 180)
                step.addPad(step.profile2.xmax - 43, 3.5, 'sy-mark', 'negative')
                step.addPad(3.5, step.profile2.ymax - 28, 'sy-mark', 'negative', 270)
                step.addPad(3.5, step.profile2.ymin + 23.5, 'sy-mark', 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 23, 'sy-mark', 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 23.5, 'sy-mark', 'negative', 270)
                # 中间
                step.addPad(3.5, step.profile2.ycenter + 10, 'sy-mark', 'negative', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 14, 'sy-mark', 'negative', 270)
                step.unaffectAll()
            step.VOF()
            for drill in self.drills:
                step.affect(drill)
            # jsk
            step.addPad(25, 3.5, 'r500')
            step.addPad(50, step.profile2.ymax - 3.5, 'r500')
            step.addPad(step.profile2.xmax - 48, step.profile2.ymax - 3.5, 'r500')
            step.addPad(step.profile2.xmax - 40, 3.5, 'r500')
            step.addPad(3.5, step.profile2.ymax - 44, 'r500')
            step.addPad(3.5, step.profile2.ymin + 41.5, 'r500')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 39, 'r500')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 44, 'r500')
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
            step.addPad(3.5, step.profile2.ymax - 32, sym, 'positive', 270)
            step.addPad(3.5, step.profile2.ymin + 34, sym, 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 29, sym, 'positive', 90)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 32, sym, 'positive', 90)
            # 中间
            step.addPad(3.5, step.profile2.ycenter + 5.5, sym, 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 8, sym, 'positive', 90)
            step.unaffectAll()
            step.affect(self.wz_map)
            sym = 'r-mark-t'
            step.addPad(36, 3.5, sym)
            step.addPad(39, step.profile2.ymax - 3.5, sym)
            step.addPad(step.profile2.xmax - 35, step.profile2.ymax - 3.5, sym)
            step.addPad(step.profile2.xmax - 28, 3.5, sym)
            step.addPad(3.5, step.profile2.ymax - 32, sym, 'positive', 270)
            step.addPad(3.5, step.profile2.ymin + 34, sym, 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 29, sym, 'positive', 90)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 32, sym, 'positive', 90)
            # 中间
            step.addPad(3.5, step.profile2.ycenter + 5.5, sym, 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 8, sym, 'positive', 90)
            # c-mark-t
            sym = 'c-mark-t'
            step.addPad(40, 3.5, sym)
            step.addPad(61, step.profile2.ymax - 3.5, sym, 'positive', 180)
            step.addPad(step.profile2.xmax - 29, step.profile2.ymax - 3.5, sym, 'positive', 180)
            step.addPad(step.profile2.xmax - 24, 3.5, sym)
            step.addPad(3.5, step.profile2.ymax - 55, sym, 'positive', 270)
            step.addPad(3.5, step.profile2.ymin + 47, sym, 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 41.5, sym, 'positive', 90)
            step.addPad(step.profile2.xmax - 3.5, step.profile.ymin + 29, sym, 'positive', 90)
            # 中间
            step.addPad(3.5, step.profile2.ycenter - 19, sym, 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 5, sym, 'positive', 90)
            # wf-mark-t
            sym = 'wf-mark-t'
            step.addPad(45.5, 3.5, sym)
            step.addPad(53, step.profile2.ymax - 3.5, sym)
            step.addPad(step.profile2.xmax - 52, step.profile2.ymax - 3.5, sym, 'positive', 180)
            step.addPad(step.profile2.xmax - 18, 3.5, sym)
            step.addPad(3.5, step.profile2.ymax - 49, sym, 'positive', 270)
            step.addPad(3.5, step.profile2.ymin + 26.5, sym, 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 48.5, sym, 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 48, sym, 'positive', 270)
            # 中间
            step.addPad(3.5, step.profile2.ycenter - 12.5, sym, 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 12, sym, 'positive', 270)
            step.unaffectAll()
            for dk in self.dks:
                step.affect(dk)
            step.addPad(3.5, step.profile2.ymax - 44, 'r2501', 'negative')
            step.addPad(3.5, step.profile2.ymin + 44, 'r2501', 'negative')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 39, 'r2501', 'negative')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 44, 'r2501', 'negative')
            # s1500
            step.addPad(3.5, step.profile2.ymax - 41.5, 'r2501', 'negative')
            step.addPad(3.5, step.profile2.ymin + 39.5, 'r2501', 'negative')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 36.5, 'r2501', 'negative')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 41.5, 'r2501', 'negative')
            # wzdw
            step.addPad(3.5, step.profile2.ymax - 38, 'r2501', 'negative')
            step.addPad(3.5, step.profile2.ymin + 37, 'r2501', 'negative')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 33, 'r2501', 'negative')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 38, 'r2501', 'negative')
            # r-mark
            sym = 'r2800'
            step.addPad(36, 3.5, sym, 'negative')
            step.addPad(39, step.profile2.ymax - 3.5, sym, 'negative')
            step.addPad(step.profile2.xmax - 35, step.profile2.ymax - 3.5, sym, 'negative')
            step.addPad(step.profile2.xmax - 28, 3.5, sym, 'negative')
            step.addPad(3.5, step.profile2.ymax - 32, sym, 'negative', 270)
            step.addPad(3.5, step.profile2.ymin + 34, sym, 'negative', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 29, sym, 'negative', 90)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 32, sym, 'negative', 90)
            # 中间
            step.addPad(3.5, step.profile2.ycenter + 5.5, sym, 'negative', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 8, sym, 'negative', 90)
            # c-mark-t
            step.addPad(40, 3.5, 'r2501', 'negative')
            step.addPad(61, step.profile2.ymax - 3.5, 'r2501', 'negative', 180)
            step.addPad(step.profile2.xmax - 29, step.profile2.ymax - 3.5, 'r2501', 'negative', 180)
            step.addPad(step.profile2.xmax - 24, 3.5, 'r2501', 'negative')
            step.addPad(3.5, step.profile2.ymax - 55, 'r2501', 'negative', 270)
            step.addPad(3.5, step.profile2.ymin + 47, 'r2501', 'negative', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 41.5, 'r2501', 'negative', 90)
            step.addPad(step.profile2.xmax - 3.5, step.profile.ymin + 29, 'r2501', 'negative', 90)
            # 中间
            step.addPad(3.5, step.profile2.ycenter - 19, 'r2501', 'negative', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 5, 'r2501', 'negative', 90)
            # wf-mark-t
            step.addPad(45.5, 3.5, 'r2600', 'negative')
            step.addPad(53, step.profile2.ymax - 3.5, 'r2600', 'negative')
            step.addPad(step.profile2.xmax - 52, step.profile2.ymax - 3.5, 'r2600', 'negative', 180)
            step.addPad(step.profile2.xmax - 18, 3.5, 'r2600', 'negative')
            step.addPad(3.5, step.profile2.ymax - 49, 'r2600', 'negative', 270)
            step.addPad(3.5, step.profile2.ymin + 26.5, 'r2600', 'negative', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 48.5, 'r2600', 'negative', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 48, 'r2600', 'negative', 270)
            # 中间
            step.addPad(3.5, step.profile2.ycenter - 12.5, 'r2600', 'negative', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 12, 'r2600', 'negative', 270)
            # sy-mark
            step.addPad(3.5, step.profile2.ymax - 28, 'r3501', 'negative', 270)
            step.addPad(3.5, step.profile2.ymin + 23.5, 'r3501', 'negative', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 23, 'r3501', 'negative', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 23.5, 'r3501', 'negative', 270)
            step.unaffectAll()
            for yy in self.yys:
                step.affect(yy)
            # sym = 'r1860'
            # step.addPad(36, 3.5, sym, 'negative')
            # step.addPad(39, step.profile2.ymax - 3.5, sym, 'negative')
            # step.addPad(step.profile2.xmax - 35, step.profile2.ymax - 3.5, sym, 'negative')
            # step.addPad(step.profile2.xmax - 28, 3.5, sym, 'negative')
            # step.addPad(3.5, step.sr2.ymax - 23, sym, 'negative', 270)
            # step.addPad(3.5, step.sr2.ymin + 25, sym, 'negative', 270)
            # step.addPad(step.profile2.xmax - 3.5, step.sr2.ymax - 20, sym, 'negative', 90)
            # step.addPad(step.profile2.xmax - 3.5, step.sr2.ymin + 22, sym, 'negative', 90)
            # # 中间
            # step.addPad(3.5, step.profile2.ycenter + 5.5, sym, 'negative', 270)
            # step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 8, sym, 'negative', 90)
            sym = 'donut_r2400x1750'
            step.addPad(45.5, 3.5, sym)
            step.addPad(53, step.profile2.ymax - 3.5, sym)
            step.addPad(step.profile2.xmax - 52, step.profile2.ymax - 3.5, sym, 'positive', 180)
            step.addPad(step.profile2.xmax - 18, 3.5, sym)
            step.addPad(3.5, step.profile2.ymax - 49, sym, 'positive', 270)
            step.addPad(3.5, step.profile2.ymin + 26.5, sym, 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 48.5, sym, 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 48, sym, 'positive', 270)
            # 中间
            step.addPad(3.5, step.profile2.ycenter - 12.5, sym, 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 12, sym, 'positive', 270)
            step.unaffectAll()
            for cov in self.covs:
                step.affect(cov)
            step.addPad(27.5, 3.5, 'r1500')
            step.addPad(47.5, step.profile2.ymax - 3.5, 'r1500')
            step.addPad(step.profile2.xmax - 45.5, step.profile2.ymax - 3.5, 'r1500')
            step.addPad(step.profile2.xmax - 37.5, 3.5, 'r1500')
            step.addPad(3.5, step.profile2.ymax - 41.5, 'r1500')
            step.addPad(3.5, step.profile2.ymin + 41.5, 'r1500')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 36.5, 'r1500')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 41.5, 'r1500')
            # 中间
            step.addPad(3.5, step.profile2.ycenter - 4.5, 'r1500')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 0.5, 'r1500')
            # c-mark-t
            step.addPad(40, 3.5, 'r2100')
            step.addPad(61, step.profile2.ymax - 3.5, 'r2100', 'positive', 180)
            step.addPad(step.profile2.xmax - 29, step.profile2.ymax - 3.5, 'r2100', 'positive', 180)
            step.addPad(step.profile2.xmax - 24, 3.5, 'r2100')
            step.addPad(3.5, step.profile2.ymax - 55, 'r2100', 'positive', 270)
            step.addPad(3.5, step.profile2.ymin + 47, 'r2100', 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 41.5, 'r2100', 'positive', 90)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 29, 'r2100', 'positive', 90)
            # 中间
            step.addPad(3.5, step.profile2.ycenter - 19, 'r2100', 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 5, 'r2100', 'positive', 90)
            if board.radioButton_other.isChecked():
                # sy-mark
                step.addPad(51, 3.5, 'r3000')
                step.addPad(65, step.profile2.ymax - 3.5, 'r3000')
                step.addPad(step.profile2.xmax - 58, step.profile2.ymax - 3.5, 'r3000', 'positive', 180)
                step.addPad(step.profile2.xmax - 43, 3.5, 'r3000')
                step.addPad(3.5, step.profile2.ymax - 28, 'r3000', 'positive', 270)
                step.addPad(3.5, step.profile2.ymin + 23.5, 'r3000', 'positive', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 23, 'r3000', 'positive', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 23.5, 'r3000', 'positive', 270)
                # 中间
                step.addPad(3.5, step.profile2.ycenter + 10, 'r3000', 'positive', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 14, 'r3000', 'positive', 270)
                # wzdw
                step.addPad(30.5, 3.5, 'r2800')
                step.addPad(43.5, step.profile2.ymax - 3.5, 'r2800')
                step.addPad(step.profile2.xmax - 41.5, step.profile2.ymax - 3.5, 'r2800')
                step.addPad(step.profile2.xmax - 34.5, 3.5, 'r2800')
                step.addPad(3.5, step.profile2.ymax - 38, 'r2800')
                step.addPad(3.5, step.profile2.ymin + 36, 'r2800')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 33, 'r2800')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 38, 'r2800')
                # 中间
                step.addPad(3.5, step.profile2.ycenter, 'r2800')
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 3.5, 'r2800')
                # wf-mark-t
                step.addPad(45.5, 3.5, 'r2500')
                step.addPad(53, step.profile2.ymax - 3.5, 'r2500')
                step.addPad(step.profile2.xmax - 52, step.profile2.ymax - 3.5, 'r2500', 'positive', 180)
                step.addPad(step.profile2.xmax - 18, 3.5, 'r2500')
                step.addPad(3.5, step.profile2.ymax - 49, 'r2500', 'positive', 270)
                step.addPad(3.5, step.profile2.ymin + 26.5, 'r2500', 'positive', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 48.5, 'r2500', 'positive', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 48, 'r2500', 'positive', 270)
                # 中间
                step.addPad(3.5, step.profile2.ycenter - 12.5, 'r2500', 'positive', 270)
                step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter - 12, 'r2500', 'positive', 270)
            step.unaffectAll()
            for wz in self.wzs:
                step.affect(wz)
            # wzdw
            step.addPad(30.5, 3.5, 'wzdw')
            step.addPad(43.5, step.profile2.ymax - 3.5, 'wzdw')
            step.addPad(step.profile2.xmax - 41.5, step.profile2.ymax - 3.5, 'wzdw')
            step.addPad(step.profile2.xmax - 34.5, 3.5, 'wzdw')
            step.addPad(3.5, step.profile2.ymax - 38, 'wzdw')
            step.addPad(3.5, step.profile2.ymin + 37, 'wzdw')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 33, 'wzdw')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 38, 'wzdw')
            # 中间
            step.addPad(3.5, step.profile2.ycenter, 'wzdw')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ycenter + 3.5, 'wzdw')
            # sy-mark
            step.addPad(51, 3.5, 'sy-1')
            step.addPad(65, step.profile2.ymax - 3.5, 'sy-1')
            step.addPad(step.profile2.xmax - 58, step.profile2.ymax - 3.5, 'sy-1', 'positive', 180)
            step.addPad(step.profile2.xmax - 43, 3.5, 'sy-1', 'positive')
            step.addPad(3.5, step.profile2.ymax - 28, 'sy-1', 'positive', 270)
            step.addPad(3.5, step.profile2.ymin + 23.5, 'sy-1', 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 23, 'sy-1', 'positive', 270)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 23.5, 'sy-1', 'positive', 270)
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
            dk = 'dkt' if signal == 'gtl' else 'dkb'
            if step.isLayer(dk):
                step.affect(dk)
                step.addPad(57, 3.5, 'fxjt', 'negative')
                step.addPad(68, 3.5, 'dkzp', 'negative', mirror=mir)
                step.unaffectAll()
        step.VOF()
        for wz in self.wzs:
            step.affect(wz)
        step.addPad(57, 3.5, 'fxjt')
        step.addPad(68, 3.5, 'zf')
        step.unaffectAll()
        for yy in self.yys:
            step.affect(yy)
        step.addPad(57, 3.5, 'fxjt')
        step.addPad(68, 2.5, 'zhyy')
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
            step.resetFilter()
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                for signal in self.signalLays:
                    step.selectChange('base_film_top') if board.signal_dict.get(signal) == 't' else step.selectChange('base_film_bot')
                    step.copySel(signal)
                    dk = 'dkt' if signal == 'gtl' else 'dkb'
                    if step.isLayer(dk):
                        step.copySel(dk, 'yes')
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
        else:
            for signal in self.signalLays:
                sym = 'base_film_top' if board.signal_dict.get(signal) == 't' else 'base_film_bot'
                step.affect(signal)
                step.addPad(step.profile2.xmin + 5, step.profile2.ymax - 89, sym)
                step.addPad(step.profile2.xmin + 5, step.profile2.ymin + 73, sym)
                step.addPad(step.profile2.xmax - 5, step.profile2.ymax - 73, sym, angle=180)
                step.addPad(step.profile2.xmax - 5, step.profile2.ymin + 73, sym, angle=180)
                step.unaffectAll()
                dk = 'dkt' if signal == 'gtl' else 'dkb'
                if step.isLayer(dk):
                    step.affect(dk)
                    step.addPad(step.profile2.xmin + 5, step.profile2.ymax - 88, sym, 'negative')
                    step.addPad(step.profile2.xmin + 5, step.profile2.ymin + 73, sym, 'negative')
                    step.addPad(step.profile2.xmax - 5, step.profile2.ymax - 72, sym, 'negative', angle=180)
                    step.addPad(step.profile2.xmax - 5, step.profile2.ymin + 73, sym, 'negative', angle=180)
                    step.unaffectAll()
            step.affect('map')
            step.addPad(step.profile2.xmin + 5, step.profile2.ymax - 89, 'base_film_map')
            step.addPad(step.profile2.xmin + 5, step.profile2.ymin + 73, 'base_film_map')
            step.addPad(step.profile2.xmax - 5, step.profile2.ymax - 73, 'base_film_map', angle=180)
            step.addPad(step.profile2.xmax - 5, step.profile2.ymin + 73, 'base_film_map', angle=180)
            step.unaffectAll()

    def do_wz(self):
        pieces = self.get_pcs_num()
        text = f'{board.lineEdit_pnl_w.text()}*{board.lineEdit_pnl_h.text()}={pieces}PCS/PNL {datetime.date.today().year}.{"%02d" % datetime.date.today().month}.{datetime.date.today().day} {self.user.upper()}'
        for signal in self.signalLays:
            mir = 'no'
            x1, x2 = 82, 135
            if board.signal_dict.get(signal) == 'b':
                mir = 'yes'
                x1, x2 = step.profile2.xmax - 50, step.profile2.xmax - 100
            #########
            if board.fill_sur != 'surface':
                step.VOF()
                step.removeLayer('zll')
                step.removeLayer('background_lx')
                step.VON()
                step.createLayer('zll', laytype='signal')
                step.createLayer('background_lx', laytype='signal')
                step.affect('zll')
                step.addPad(x1, 2.5, 'zc-job', 'positive', mirror=mir)
                step.selectBreak()
                step.unaffectAll()
                # 加背景实铜
                step.affect('background_lx')
                infoDict = step.DO_INFO(' -t layer -e %s/%s/zll -d LIMITS,units=mm' % (jobname, step.name))
                bg_xmin = infoDict['gLIMITSxmin'] - 0.8
                bg_ymin = infoDict['gLIMITSymin'] - 0.2
                bg_xmax = infoDict['gLIMITSxmax'] + 0.8
                bg_ymax = infoDict['gLIMITSymax'] + 0.2
                step.addAttr_zl('.string,text=mark_bg')
                step.addRectangle(bg_xmin, bg_ymin, bg_xmax, bg_ymax, attributes='yes')
                step.resetAttr()
                step.unaffectAll()
                step.truncate('zll')
                step.affect('zll')
                step.addText(x2, 2.5, text, 2, 2.3, 0.989993453, mir, fontname='simplex')
                step.unaffectAll()
                # 加背景实铜
                step.affect('background_lx')
                infoDict = step.DO_INFO(' -t layer -e %s/%s/zll -d LIMITS,units=mm' % (jobname, step.name))
                bg_xmin = infoDict['gLIMITSxmin'] - 0.8
                bg_ymin = infoDict['gLIMITSymin'] - 0.2
                bg_xmax = infoDict['gLIMITSxmax'] + 0.8
                bg_ymax = infoDict['gLIMITSymax']
                step.addAttr_zl('.string,text=mark_bg')
                step.addRectangle(bg_xmin, bg_ymin, bg_xmax, bg_ymax, attributes='yes')
                step.resetAttr()
                step.unaffectAll()
                step.affect('background_lx')
                step.copySel(signal)
                step.unaffectAll()
                step.removeLayer('zll')
                step.removeLayer('background_lx')
            ##########
            step.affect(signal)
            dk = 'dkt' if signal == 'gtl' else 'dkb'
            if step.isLayer(dk):
                step.affect(dk)
            step.addPad(x1, 2.5, 'zc-job', 'negative', mirror=mir)
            step.addText(x2, 2.5, text, 2, 2.3, 0.989993453, mir, fontname='simplex', polarity='negative')
            step.unaffectAll()
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
        for zh in self.zhs:
            step.affect(zh)
            mir = 'no'
            x1, x2 = 82, 135
            if 'b' in zh:
                mir = 'yes'
                x1, x2 = step.profile2.xmax - 50, step.profile2.xmax - 100
            step.addPad(x1, 2.5, 'zc-job', mirror=mir)
            step.addText(x2, 2.5, text, 2, 2.3, 0.989993453, mir, fontname='simplex')
            step.unaffectAll()
            step.VON()

    def do_py(self):
        if board.map_flag:
            step.affect('map')
            step.selectSymbol('py')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                step.copySel(self.wz_map)
                for signal in self.signalLays:
                    step.copySel(signal, 'yes')
                step.selectChange('r2200')
                for cov in self.covs:
                    step.copySel(cov)
                step.selectChange('r2501')
                for dk in self.dks:
                    step.copySel(dk, 'yes')
                step.selectChange('r0')
                step.addAttr('.out_flag', attrVal='int=233')
                for wz in self.wzs:
                    step.copySel(wz)
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
        else:
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
            step.addPad(3.5, step.profile2.ymin + 11, 'r2200')
            step.addPad(3.5, step.profile2.ymax - 11, 'r2200')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 19, 'r2200')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 11, 'r2200')
            step.unaffectAll()
            for dk in self.dks:
                step.affect(dk)
            step.addPad(3.5, step.profile2.ymin + 11, 'r2501', 'negative')
            step.addPad(3.5, step.profile2.ymax - 11, 'r2501', 'negative')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 19, 'r2501', 'negative')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 11, 'r2501', 'negative')
            step.unaffectAll()
            step.affect('map')
            step.affect(self.wz_map)
            step.addPad(3.5, step.profile2.ymin + 11, 'py')
            step.addPad(3.5, step.profile2.ymax - 11, 'py')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 19, 'py')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 11, 'py')
            step.unaffectAll()
            for wz in self.wzs:
                step.affect(wz)
            step.addAttr_zl('.out_flag,int=233')
            step.addPad(3.5, step.profile2.ymin + 11, 'r0', attributes='yes')
            step.addPad(3.5, step.profile2.ymax - 11, 'r0', attributes='yes')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 19, 'r0', attributes='yes')
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 11, 'r0', attributes='yes')
            step.unaffectAll()
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
                    dk = 'dkt' if signal == 'gtl' else 'dkb'
                    if step.isLayer(dk):
                        step.copySel(dk)
                step.selectChange('r1000')
                step.selectPolarity()
                for drill in self.drills:
                    step.copySel(drill)
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
        else:
            for signal in self.signalLays:
                step.affect(signal)
                sym = 'ldi-mark-t' if board.signal_dict.get(signal) == 't' else 'ldi-mark-b'
                dk = 'dkt' if signal == 'gtl' else 'dkb'
                if step.isLayer(dk):
                    step.affect(dk)
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
            for drill in self.drills:
                step.affect(drill)
            step.addPad(19, step.sr2.ymin - 2, 'r1000')
            step.addPad(19, step.sr2.ymax + 2, 'r1000')
            step.addPad(step.profile2.xmax - 23, step.sr2.ymax + 2, 'r1000')
            step.addPad(step.profile2.xmax - 19, step.sr2.ymin - 2, 'r1000')
            step.unaffectAll()
            step.VON()

    def do_lpi(self):
        for signal in self.signalLays:
            step.affect(signal)
        step.addPad(33, 9, 'lpi-3.0', 'negative')
        step.addPad(36, step.profile2.ymax - 9, 'lpi-2.5', 'negative')
        step.addPad(step.profile2.xmax - 35.5, step.profile2.ymax - 9, 'lpi-2.5', 'negative')
        step.addPad(step.profile2.xmax - 33, 9, 'lpi-2.5', 'negative')
        step.unaffectAll()
        step.VOF()
        for zh in self.zhs:
            step.affect(zh)
        step.addPad(33, 9, 'r4400')
        step.addPad(33, 9, 'donut_r5000x1000', 'negative')
        step.addPad(36, step.profile2.ymax - 9, 'r4400')
        step.addPad(36, step.profile2.ymax - 9, 'donut_r5000x1000', 'negative')
        step.addPad(step.profile2.xmax - 35.5, step.profile2.ymax - 9, 'r4400')
        step.addPad(step.profile2.xmax - 35.5, step.profile2.ymax - 9, 'donut_r5000x1000', 'negative')
        step.addPad(step.profile2.xmax - 33, 9, 'r4400')
        step.addPad(step.profile2.xmax - 33, 9, 'donut_r5000x1000', 'negative')
        step.unaffectAll()
        for cov in self.covs:
            step.affect(cov)
        step.addPad(33, 9, 'r4000')
        step.addPad(36, step.profile2.ymax - 9, 'r4000')
        step.addPad(step.profile2.xmax - 35.5, step.profile2.ymax - 9, 'r4000')
        step.addPad(step.profile2.xmax - 33, 9, 'r4000')
        step.unaffectAll()
        for dk in self.dks:
            step.affect(dk)
        step.addPad(33, 9, 'r4700', 'negative')
        step.addPad(36, step.profile2.ymax - 9, 'r4700', 'negative')
        step.addPad(step.profile2.xmax - 35.5, step.profile2.ymax - 9, 'r4700', 'negative')
        step.addPad(step.profile2.xmax - 33, 9, 'r4700', 'negative')
        step.unaffectAll()
        step.VON()

    def do_qp(self):
        if board.map_flag:
            step.affect('map')
            step.selectSymbol('qp')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                step.selectChange('qp-xl')
                for signal in self.signalLays:
                    step.copySel(signal)
                for dk in self.dks:
                    step.copySel(dk)
                step.selectChange('qp-f')
                for drill in self.drills:
                    step.copySel(drill)
                step.unaffectAll()
            step.unaffectAll()
            step.resetFilter()
            step.truncate(self.tmp_map)
        else:
            for signal in self.signalLays:
                step.affect(signal)
            for dk in self.dks:
                step.affect(dk)
            # 左右
            step.addPad(3.5, step.profile2.ymax - 75.5, 'qp-xl', angle=90)
            step.addPad(3.5, step.profile2.ymin + 53, 'qp-xl', angle=90)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 61, 'qp-xl', angle=270)
            step.addPad(step.profile2.xmax - 3.5, 57, 'qp-xl', angle=270)
            step.unaffectAll()
            step.affect('map')
            # 左右
            step.addPad(3.5, step.profile2.ymax - 75.5, 'qp', angle=90)
            step.addPad(3.5, step.profile2.ymin + 53, 'qp', angle=90)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 61, 'qp', angle=270)
            step.addPad(step.profile2.xmax - 3.5, 57, 'qp', angle=270)
            step.unaffectAll()
            for drill in self.drills:
                step.affect(drill)
            # 左右
            step.addPad(3.5, step.profile2.ymax - 75.5, 'qp-f', angle=90)
            step.addPad(3.5, step.profile2.ymin + 53, 'qp-f', angle=90)
            step.addPad(step.profile2.xmax - 3.5, step.profile2.ymax - 61, 'qp-f', angle=270)
            step.addPad(step.profile2.xmax - 3.5, 57, 'qp-f', angle=270)
            step.unaffectAll()

    def do_donut(self):
        for signal in self.signalLays:
                step.affect(signal)
        step.VOF()
        xb1, xb3, xt1, xt3 = 85, step.profile2.xmax - 70, 57, step.profile2.xmax - 77
        # 下上
        step.addPad(xb1, 6.5, 'r2200')
        step.addPad(xb1 + 3, 6.5, 'r2200')
        step.addPad(xb1 + 6, 6.5, 'r2200')
        step.addPad(xb3, 6.5, 'r2200')
        step.addPad(xb3 + 3, 6.5, 'r2200')
        step.addPad(xb3 + 6, 6.5, 'r2200')
        step.addPad(xt1, step.profile2.ymax - 6.5, 'r2200')
        step.addPad(xt1 + 3, step.profile2.ymax - 6.5, 'r2200')
        step.addPad(xt1 + 6, step.profile2.ymax - 6.5, 'r2200')
        step.addPad(xt3, step.profile2.ymax - 6.5, 'r2200')
        step.addPad(xt3 + 3, step.profile2.ymax - 6.5, 'r2200')
        step.addPad(xt3 + 6, step.profile2.ymax - 6.5, 'r2200')
        step.addPad(xb1, 6.5, 'donut_r2000x1100', 'negative')
        step.addPad(xb1 + 3, 6.5, 'donut_r2000x1200', 'negative')
        step.addPad(xb1 + 6, 6.5, 'donut_r2000x1300', 'negative')
        step.addPad(xb3, 6.5, 'donut_r2000x1100', 'negative')
        step.addPad(xb3 + 3, 6.5, 'donut_r2000x1200', 'negative')
        step.addPad(xb3 + 6, 6.5, 'donut_r2000x1300', 'negative')
        step.addPad(xt1, step.profile2.ymax - 6.5, 'donut_r2000x1100', 'negative')
        step.addPad(xt1 + 3, step.profile2.ymax - 6.5, 'donut_r2000x1200', 'negative')
        step.addPad(xt1 + 6, step.profile2.ymax - 6.5, 'donut_r2000x1300', 'negative')
        step.addPad(xt3, step.profile2.ymax - 6.5, 'donut_r2000x1100', 'negative')
        step.addPad(xt3 + 3, step.profile2.ymax - 6.5, 'donut_r2000x1200', 'negative')
        step.addPad(xt3 + 6, step.profile2.ymax - 6.5, 'donut_r2000x1300', 'negative')
        # 左右线宽线距pad
        step.addPad(3.5, step.profile2.ymax - 64, '1-ws')  # 线宽线距symbol
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 87, '1-ws', angle=180)  # 线宽线距symbol
        step.unaffectAll()
        for zh in self.zhs:
            step.affect(zh)
        step.addPad(xb1, 6.5, 'r1000', 'positive', nx=3, dx=3000)
        step.addPad(xb3, 6.5, 'r1000', 'positive', nx=3, dx=3000)
        step.addPad(xt1, step.profile2.ymax - 6.5, 'r1000', 'positive', nx=3, dx=3000)
        step.addPad(xt3, step.profile2.ymax - 6.5, 'r1000', 'positive', nx=3, dx=3000)
        step.addPad(3.5, step.profile2.ymax - 65.7, 'r3500', 'positive')  # 线宽线距symbol
        step.addPad(3.5, step.profile2.ymax - 61, 'r3500', 'positive')  # 线宽线距symbol
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 88.7, 'r3500', 'positive')  # 线宽线距symbol
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 84, 'r3500', 'positive')  # 线宽线距symbol
        # step.addPad(xt1 - 10.5, step.sr2.ymax + 3.5, 'r3500', 'negative')  # 线宽线距symbol
        # step.addPad(xt1 - 6.4, step.sr2.ymax + 3.5, 'r3500', 'negative')  # 线宽线距symbol
        # step.addPad(xt3 + 15.2 , step.sr2.ymax + 3.5, 'r3500', 'negative')  # 线宽线距symbol
        # step.addPad(xt3 + 11.1, step.sr2.ymax + 3.5, 'r3500', 'negative')  # 线宽线距symbol
        step.unaffectAll()
        for cov in self.covs:
            step.affect(cov)
        step.addPad(xb1, 6.5, 'r1500', nx=3, dx=3000)
        step.addPad(xb3, 6.5, 'r1500', nx=3, dx=3000)
        step.addPad(xt1, step.profile2.ymax - 6.5, 'r1500', nx=3, dx=3000)
        step.addPad(xt3, step.profile2.ymax - 6.5, 'r1500', nx=3, dx=3000)
        step.addPad(3.5, step.profile2.ymax - 65.7, 'r3000')  # 线宽线距symbol
        step.addPad(3.5, step.profile2.ymax - 61, 'r3000')  # 线宽线距symbol
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 88.7, 'r3000')  # 线宽线距symbol
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 84, 'r3000')  # 线宽线距symbol
        # step.addPad(xb1 - 10.5, 6.5, 'r3000')  # 线宽线距symbol
        # step.addPad(xb1 - 6.4, 6.5, 'r3000')  # 线宽线距symbol
        # step.addPad(xb3 - 10.5, 6.5, 'r3000')  # 线宽线距symbol
        # step.addPad(xb3 - 6.4, 6.5, 'r3000')  # 线宽线距symbol
        # step.addPad(xt1 - 10.5, step.sr2.ymax + 3.5, 'r3000')  # 线宽线距symbol
        # step.addPad(xt1 - 6.4, step.sr2.ymax + 3.5, 'r3000')  # 线宽线距symbol
        # step.addPad(xt3 + 15.2, step.sr2.ymax + 3.5, 'r3000')  # 线宽线距symbol
        # step.addPad(xt3 + 11.1, step.sr2.ymax + 3.5, 'r3000')  # 线宽线距symbol
        step.unaffectAll()
        for dk in self.dks:
            step.affect(dk)
        step.addPad(xb1, 6.5, 'r2200', 'negative', nx=3, dx=3000)
        step.addPad(xb3, 6.5, 'r2200', 'negative', nx=3, dx=3000)
        step.addPad(xt1, step.profile2.ymax - 6.5, 'r2200', 'negative', nx=3, dx=3000)
        step.addPad(xt3, step.profile2.ymax - 6.5, 'r2200', 'negative', nx=3, dx=3000)
        # 左右线宽线距pad
        step.addPad(3.5, step.profile2.ymax - 64, 'rect4200x12200', 'negative')  # 线宽线距symbol
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 87, 'rect4200x12200','negative', angle=180)  # 线宽线距symbol
        step.unaffectAll()
        for yy in self.yys:
            step.affect(yy)
        step.addPad(xb1, 6.5, 'r3500', nx=3, dx=3000)
        step.addPad(xb3, 6.5, 'r3500', nx=3, dx=3000)
        step.addPad(xt1, step.profile2.ymax - 6.5, 'r3500', nx=3, dx=3000)
        step.addPad(xt3, step.profile2.ymax - 6.5, 'r3500', nx=3, dx=3000)
        step.addPad(3.5, step.profile2.ymax - 65.7, 'r4500')  # 线宽线距symbol
        step.addPad(3.5, step.profile2.ymax - 61, 'r4500')  # 线宽线距symbol
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 88.7, 'r4500')  # 线宽线距symbol
        step.addPad(step.profile2.xmax - 3.5, step.profile2.ymin + 84, 'r4500')  # 线宽线距symbol
        # step.addPad(xb1 - 10.5, 6.5, 'r4500')  # 线宽线距symbol
        # step.addPad(xb1 - 6.4, 6.5, 'r4500')  # 线宽线距symbol
        # step.addPad(xb3 - 10.5, 6.5, 'r4500')  # 线宽线距symbol
        # step.addPad(xb3 - 6.4, 6.5, 'r4500')  # 线宽线距symbol
        # step.addPad(xt1 - 10.5, step.sr2.ymax + 3.5, 'r4500')  # 线宽线距symbol
        # step.addPad(xt1 - 6.4, step.sr2.ymax + 3.5, 'r4500')  # 线宽线距symbol
        # step.addPad(xt3 + 15.2, step.sr2.ymax + 3.5, 'r4500')  # 线宽线距symbol
        # step.addPad(xt3 + 11.1, step.sr2.ymax + 3.5, 'r4500')  # 线宽线距symbol
        step.unaffectAll()
        step.VON()
        for signal in self.signalLays:
            y = step.sr2.ymax + 2.5 if board.signal_dict.get(signal) == 't' else step.sr2.ymax + 6
            dk = 'dkt' if signal == 'gtl' else 'dkb'
            step.affect(signal)
            step.addPad(106.5, y, 's3200', nx=3, dx=5000)
            step.addPad(106.5, y, 'donut_s3000x2000', 'negative', nx=3, dx=5000)
            step.addPad(step.profile2.xmax - 93.5, y, 's3200', nx=3, dx=5000)
            step.addPad(step.profile2.xmax - 93.5, y, 'donut_s3000x2000', 'negative', nx=3, dx=5000)
            step.unaffectAll()
            if step.isLayer(dk):
                step.affect(dk)
                step.addPad(106.5, y, 's3200','negative', nx=3, dx=5000)
                step.addPad(step.profile2.xmax - 93.5, y, 's3200', 'negative', nx=3, dx=5000)
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
        if board.map_flag:
            step.affect('map')
            step.selectSymbol('2d')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                step.selectChange('s6000')
                for signal in self.signalLays:
                    step.copyToLayer(signal, dx=2.5, dy=2.5)
                for dk in self.dks:
                    step.copyToLayer(dk, 'yes', dx=2.5, dy=2.5)
                step.selectChange('2d')
                step.copySel('2d')
                for signal in self.signalLays:
                    step.copySel(signal, 'yes')
                step.unaffectAll()
            step.unaffectAll()
            step.resetFilter()
            step.truncate(self.tmp_map)
        else:
            for signal in self.signalLays:
                step.affect(signal)
            step.addPad(97.5, step.profile2.ymax - 8, '2d', 'negative')
            step.addPad(step.profile2.xmax - 102.5, step.profile2.ymax - 8, '2d', 'negative')
            step.addPad(97.5 + 2.5, step.profile2.ymax - 8 + 2.5, 's6000')
            step.addPad(step.profile2.xmax - 102.5 + 2.5, step.profile2.ymax - 8 + 2.5, 's6000')
            step.unaffectAll()
            step.affect('2d')
            step.affect('map')
            step.addPad(97.5, step.profile2.ymax - 8, '2d')
            step.addPad(step.profile2.xmax - 102.5, step.profile2.ymax - 8, '2d')
            step.unaffectAll()
            step.VOF()
            for dk in self.dks:
                step.affect(dk)
            step.addPad(97.5 + 2.5, step.profile2.ymax - 8 + 2.5, 's6000', 'negative')
            step.addPad(step.profile2.xmax - 102.5 + 2.5, step.profile2.ymax - 8 + 2.5, 's6000', 'negative')
            step.unaffectAll()
            step.VON()

    def do_b2(self):
        if board.map_flag:
            step.affect('map')
            step.selectSymbol('sy-pnlb2')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                for signal in self.signalLays:
                    if signal in self.inner_signals:
                        if signal == self.inner_signals[0]:
                            step.selectChange('sy-pnlb2')
                            if board.signal_dict.get(signal) == 'b':
                                step.Transform('axis', 'mirror')
                            step.copySel_2(signal, 'yes')
                        else:
                            step.selectChange('r2000')
                            step.copySel(signal)
                            step.selectChange('r1801')
                            step.copySel(signal, 'yes')
                    else:
                        step.selectChange('wcb2')
                        step.copySel(signal, 'yes')
                step.unaffectAll()
            step.unaffectAll()
            step.resetFilter()
            step.truncate(self.tmp_map)
        else:
            for signal in self.signalLays:
                step.affect(signal)
                if signal in self.inner_signals:
                    if signal == self.inner_signals[0]:
                        mir = 'no' if board.signal_dict.get(signal) == 't' else 'yes'
                        step.addPad(8, 10, 'sy-pnlb2', 'negative', mirror=mir)
                        step.addPad(8, step.profile2.ymax - 10, 'sy-pnlb2', 'negative', mirror=mir)
                        step.addPad(8, step.profile2.ymax - 16, 'sy-pnlb2', 'negative', mirror=mir)
                        step.addPad(step.profile2.xmax - 8, step.profile2.ymax - 10, 'sy-pnlb2', 'negative', mirror=mir)
                        step.addPad(step.profile2.xmax - 8, 10, 'sy-pnlb2', 'negative', mirror=mir)
                    else:
                        step.addPad(8, 10, 'r2000')
                        step.addPad(8, 10, 'r1801', 'negative')
                        step.addPad(8, step.profile2.ymax - 10, 'r2000')
                        step.addPad(8, step.profile2.ymax - 10, 'r1801', 'negative')
                        step.addPad(8, step.profile2.ymax - 16, 'r2000')
                        step.addPad(8, step.profile2.ymax - 16, 'r1801', 'negative')
                        step.addPad(step.profile2.xmax - 8, step.profile2.ymax - 10, 'r2000')
                        step.addPad(step.profile2.xmax - 8, step.profile2.ymax - 10, 'r1801', 'negative')
                        step.addPad(step.profile2.xmax - 8, 10, 'r2000')
                        step.addPad(step.profile2.xmax - 8, 10, 'r1801', 'negative')
                else:
                    step.addPad(8, 10, 'wcb2', 'negative')
                    step.addPad(8, step.profile2.ymax - 10, 'wcb2', 'negative')
                    step.addPad(8, step.profile2.ymax - 16, 'wcb2', 'negative')
                    step.addPad(step.profile2.xmax - 8, step.profile2.ymax - 10, 'wcb2', 'negative')
                    step.addPad(step.profile2.xmax - 8, 10, 'wcb2', 'negative')
                step.unaffectAll()
            step.affect('map')
            step.addPad(8, 10, 'sy-pnlb2')
            step.addPad(8, step.profile2.ymax - 10, 'sy-pnlb2')
            step.addPad(8, step.profile2.ymax - 16, 'sy-pnlb2')
            step.addPad(step.profile2.xmax - 8, step.profile2.ymax - 10, 'sy-pnlb2')
            step.addPad(step.profile2.xmax - 8, 10, 'sy-pnlb2')
            step.unaffectAll()


    def do_x_ray(self):
        if board.map_flag:
            step.affect('map')
            step.selectSymbol('x-ray')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                for signal in self.signalLays:
                    if signal in self.inner_signals:
                        if signal == self.inner_signals[0]:
                            step.selectChange('x-ray')
                            if board.signal_dict.get(signal) == 'b':
                                step.Transform('axis', 'mirror')
                            step.copySel_2(signal)
                        else:
                            step.selectChange('s8000')
                            step.copySel(signal)
                            step.selectChange('s7500')
                            step.copySel(signal, 'yes')
                    else:
                        step.selectChange('s8000')
                        step.copySel(signal)
                        step.selectChange('s7500')
                        step.copySel(signal, 'yes')
                step.unaffectAll()
            step.unaffectAll()
            step.resetFilter()
            step.truncate(self.tmp_map)
        else:
            for signal in self.signalLays:
                step.affect(signal)
                if signal in self.inner_signals:
                    if signal == self.inner_signals[0]:
                        mir = 'no' if board.signal_dict.get(signal) == 't' else 'yes'
                        step.addPad(20, 10, 'x-ray', mirror=mir)
                        step.addPad(20, step.profile2.ymax - 10, 'x-ray', mirror=mir)
                        step.addPad(step.profile2.xmax - 20, step.profile2.ymax - 10, 'x-ray', mirror=mir)
                        step.addPad(step.profile2.xmax - 20, 10, 'x-ray', mirror=mir)
                    else:
                        step.addPad(20, 10, 's8000')
                        step.addPad(20, 10, 's7500', 'negative')
                        step.addPad(20, step.profile2.ymax - 10, 's8000')
                        step.addPad(20, step.profile2.ymax - 10, 's7500', 'negative')
                        step.addPad(step.profile2.xmax - 20, step.profile2.ymax - 10, 's8000')
                        step.addPad(step.profile2.xmax - 20, step.profile2.ymax - 10, 's7500', 'negative')
                        step.addPad(step.profile2.xmax - 20, 10, 's8000')
                        step.addPad(step.profile2.xmax - 20, 10, 's7500', 'negative')
                else:
                    step.addPad(20, 10, 's8000')
                    step.addPad(20, 10, 's7500', 'negative')
                    step.addPad(20, step.profile2.ymax - 10, 's8000')
                    step.addPad(20, step.profile2.ymax - 10, 's7500', 'negative')
                    step.addPad(step.profile2.xmax - 20, step.profile2.ymax - 10, 's8000')
                    step.addPad(step.profile2.xmax - 20, step.profile2.ymax - 10, 's7500', 'negative')
                    step.addPad(step.profile2.xmax - 20, 10, 's8000')
                    step.addPad(step.profile2.xmax - 20, 10, 's7500', 'negative')
                step.unaffectAll()
            step.affect('map')
            step.addPad(20, 10, 'x-ray')
            step.addPad(20, step.profile2.ymax - 10, 'x-ray')
            step.addPad(step.profile2.xmax - 20, step.profile2.ymax - 10, 'x-ray')
            step.addPad(step.profile2.xmax - 20, 10, 'x-ray')
            step.unaffectAll()


    def do_au_text(self):
        for signal in self.signalLays:
            mir = 'no' if board.signal_dict.get(signal) == 't' else 'yes'
            x = 52 if board.signal_dict.get(signal) == 't' else 70
            rectx = 11.5 if board.signal_dict.get(signal) == 't' else -11.5
            y = step.sr2.ymin - 2
            step.affect(signal)
            text = 'AU:SQ/MM(%)'
            step.addPad(x + rectx, y + 0.55, 'rect24000x1800')
            step.addText(x, y, text, 1, 1.2, 0.492125988,mir,fontname='simple', polarity='negative')
            step.unaffectAll()
            dk = 'dkt' if signal == 'gtl' else 'dkb'
            if step.isLayer(dk):
                step.affect(dk)
                text = 'CU:SQ/MM(%)'
                step.addPad(x + rectx, y + 0.55, 'rect24000x1800')
                step.addText(x, y, text, 1, 1.2, 0.492125988, mir, fontname='simple', polarity='negative')
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
        step.VOF()
        for cov in self.covs:
            step.affect(cov)
        for zh in self.zhs:
            step.affect(zh)
        step.addPad(4, 15, 'r1300')
        step.addPad(4, step.profile2.ymax - 15, 'r1300')
        step.addPad(step.profile2.xmax - 4, step.profile2.ymax - 15, 'r1300')
        step.addPad(step.profile2.xmax - 4, 15, 'r1300')
        step.unaffectAll()
        for dk in self.dks:
            step.affect(dk)
        step.addPad(4, 15, 'r2501', 'negative')
        step.addPad(4, step.profile2.ymax - 15, 'r2501', 'negative')
        step.addPad(step.profile2.xmax - 4, step.profile2.ymax - 15, 'r2501', 'negative')
        step.addPad(step.profile2.xmax - 4, 15, 'r2501', 'negative')
        # 20240723
        step.addPad(4, 13.8, 'rect1700x750', 'negative')
        step.addPad(2.8, 15, 'rect750x1700', 'negative')
        step.addPad(2.8, step.profile2.ymax - 15, 'rect750x1700', 'negative')
        step.addPad(step.profile2.xmax - 2.8, step.profile2.ymax - 15, 'rect750x1700', 'negative')
        step.addPad(step.profile2.xmax - 2.8, 15, 'rect750x1700', 'negative')
        step.addPad(step.profile2.xmax - 4, 13.8, 'rect1700x750', 'negative')
        step.unaffectAll()
        step.VON()


    def do_cov(self):
        """
        覆盖面加文字并在线路层掏开  反面需要镜像
        """
        for cov in self.covs:
            mir = 'no'
            x = 70
            if cov == 'c2':
                if list(board.signal_dict.values())[-1] == 'b':
                    mir = 'yes'
                    x = 78
            else:
                if list(board.signal_dict.values())[0] == 'b':
                    mir = 'yes'
                    x = 78
            tmp_cov = f'{cov}+++{step.pid}'
            step.createLayer(tmp_cov)
            step.affect(tmp_cov)
            step.addText(x, step.sr2.ymax + 0.5, cov.upper(), 5, 5, 2.296587944, mir, fontname='simple')
            step.unaffectAll()
        repeat_tx, repeat_ty = [], []
        repeat_set_x, repeat_set_y = [], []  # 保存set的y坐标，后续在对set加分割线时根据y坐标判断是否是set
        cut_ys = []
        for name, xmin, xmax, ymin, ymax in zip(step.info2.get('gREPEATstep'),
                                                step.info2.get('gREPEATxmin'),
                                                step.info2.get('gREPEATxmax'),
                                                step.info2.get('gREPEATymin'),
                                                step.info2.get('gREPEATymax')):

                repeat_ty.append(ymin)
                repeat_ty.append(ymax)
                repeat_tx.append(xmin)
                repeat_tx.append(xmax)
                if 'set' in name:
                    repeat_set_x.append(xmin)
                    repeat_set_y.append(ymin)
                    repeat_set_x.append(xmax)
                    repeat_set_y.append(ymax)
        # 20240723 排除set两边的coupon影响
        set_x_min, set_x_max = min(repeat_set_x), max(repeat_set_x)
        actual_ty = []
        for tx, ty in zip(repeat_tx, repeat_ty):
            if set_x_min < tx < set_x_max:
                actual_ty.append(ty)
        repeat_ty = sorted(list(set(actual_ty)))
        # 覆盖膜加切线和序号
        if float(board.lineEdit_pnl_h.text()) > 300:
            if len(repeat_ty) > 2 and self.covs:
                i = 1
                while i < len(repeat_ty) - 1:
                    if repeat_ty[i] in repeat_set_y:
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
            # 加覆盖膜对位孔
            step.affect(cov)
            for n, ty in enumerate(repeat_set_y):
                if n % 2:
                    step.addPad(set_x_min + 1.5, ty - 10, 'r1000')
                    step.addPad(set_x_max - 1.5, ty - 16, 'r1000')
                else:
                    step.addPad(set_x_min + 1.5, ty + 13, 'r1000')
                    step.addPad(set_x_max - 1.5, ty + 13, 'r1000')
            step.unaffectAll()


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
            x, mir, rectx = 89, 'no', -3.5
            if board.signal_dict.get(signal) == 'b':
                x, mir, rectx = 82, 'yes', 3.5
            step.affect(signal)
            step.addPad(x + rectx, step.sr2.ymax + 3.5, 'rect12400x1500', mirror=mir)
            step.addPad(x, step.sr2.ymax + 3.5, 'x-scale', 'negative', mirror=mir)
            step.addPad(x + rectx, step.sr2.ymax + 1.5, 'rect12400x1500', mirror=mir)
            step.addPad(x, step.sr2.ymax + 1.5, 'y-scale', 'negative', mirror=mir)
            step.unaffectAll()
        for dk in self.dks:
            x, mir, rectx = 89, 'no', -3.5
            signal = 'gtl' if dk == 'dkt' else 'gbl'
            if board.signal_dict.get(signal) == 'b':
                x, mir, rectx = 82, 'yes', 3.5
            step.affect(dk)
            step.addPad(x + rectx, step.sr2.ymax + 3.5, 'rect12600x1700', 'negative', mirror=mir)
            step.addPad(x + rectx, step.sr2.ymax + 1.5, 'rect12600x1700', 'negative', mirror=mir)
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
        step.selectChange('r0')
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
        step.affect(border1)
        step.selectResize(100)
        step.clip_area(margin=0)
        for zh in self.zhs:
            step.copySel(zh)
        for dk in self.dks:
            step.copySel(dk)
        step.unaffectAll()
        step.VOF()
        # 20240719 把wz_tmp里的文字一起在选镀层掏0.2
        tmp = self.wz_map + '+++'
        for dk in self.dks:
            step.affect(self.wz_map)
            step.copySel(tmp)
            step.unaffectAll()
            step.affect(tmp)
            signal = 'gtl' if dk == 'dkt' else 'gbl'
            if board.signal_dict.get(signal) == 'b':
                for s, ns in (('r-mark-t', 'r-mark-b'), ('c-mark-t', 'c-mark-b'), ('wf-mark-t', 'wf-mark-b'), ('sy-pin-t', 'sy-pin-b')):
                    step.selectSymbol(s)
                    step.resetFilter()
                    if step.Selected_count():
                        step.selectChange(ns)
            step.selectBreak()
            step.setFilterTypes('line', 'positive')
            step.selectAll()
            step.resetFilter()
            if step.Selected_count():
                step.copyToLayer(dk, 'yes', size=200)
            step.unaffectAll()
            step.removeLayer(tmp)
        step.unaffectAll()
        #######
        for zh in self.zhs:
            step.affect(zh)
        for dk in self.dks:
            step.affect(dk)
        step.addLine(step.profile2.xmin, step.profile2.ymin, step.profile2.xmin + 5, step.profile2.ymin, 'r100')
        step.addLine(step.profile2.xmin, step.profile2.ymin, step.profile2.xmin, step.profile2.ymin + 5, 'r100')
        step.addLine(step.profile2.xmin, step.profile2.ymax, step.profile2.xmin + 5, step.profile2.ymax, 'r100')
        step.addLine(step.profile2.xmin, step.profile2.ymax, step.profile2.xmin, step.profile2.ymax - 5, 'r100')
        step.addLine(step.profile2.xmax, step.profile2.ymax, step.profile2.xmax - 5, step.profile2.ymax, 'r100')
        step.addLine(step.profile2.xmax, step.profile2.ymax, step.profile2.xmax, step.profile2.ymax - 5, 'r100')
        step.addLine(step.profile2.xmax, step.profile2.ymin, step.profile2.xmax - 5, step.profile2.ymin, 'r100')
        step.addLine(step.profile2.xmax, step.profile2.ymin, step.profile2.xmax, step.profile2.ymin + 5, 'r100')
        step.unaffectAll()
        step.affect(border2)
        step.addLine(step.profile2.xmin - 12.5, step.profile2.ymin, step.profile2.xmin - 12.5, step.profile2.ymax,'r1100')
        step.addLine(step.profile2.xmax + 12.5, step.profile2.ymin, step.profile2.xmax + 12.5, step.profile2.ymax,'r1100')
        for dk in self.dks:
            step.copySel(dk, 'yes')
        step.unaffectAll()
        # dk层加电金夹点  10~50 高4mm
        for dk in self.dks:
            step.affect(dk)
        step.addRectangle(10, 1.5, 50, 5.5)
        step.addRectangle(step.profile2.xmax - 10, 1.5, step.profile2.xmax - 50, 5.5)
        step.addRectangle(10, step.profile2.ymax - 1.5, 50, step.profile2.ymax - 5.5)
        step.addRectangle(step.profile2.xmax - 10, step.profile2.ymax - 1.5, step.profile2.xmax - 50, step.profile2.ymax - 5.5)
        step.unaffectAll()
        # 20240723
        if board.map_flag:
            step.affect('map')
            step.selectSymbol('fxk')
            if step.Selected_count():
                step.copySel(self.tmp_map)
                step.unaffectAll()
                step.affect(self.tmp_map)
                step.selectChange('dk-fx')
                for dk in self.dks:
                    step.copySel(dk, 'yes')
                step.unaffectAll()
            step.unaffectAll()
            step.truncate(self.tmp_map)
        else:
            for dk in self.dks:
                step.affect(dk)
            step.addPad(step.profile2.xmin + 2.5, 2.5, 'dk-fx', 'negative')
            step.addPad(step.profile2.xmin + 2.5, step.profile2.ymax - 2.5, 'dk-fx', 'negative')
            step.addPad(step.profile2.xmin + 8.5, step.profile2.ymax - 2.5, 'dk-fx', 'negative')
            step.addPad(step.profile2.xmin + 14.5, step.profile2.ymax - 2.5, 'dk-fx', 'negative')
            step.addPad(step.profile2.xmax - 2.5, 2.5, 'dk-fx', 'negative')
            step.addPad(step.profile2.xmax - 2.5, step.profile2.ymax - 2.5, 'dk-fx', 'negative')
            step.unaffectAll()
        step.removeLayer(border1)
        step.removeLayer(border1 + '+++')
        step.removeLayer(border2)
        step.removeLayer(self.wz_map)
        step.VON()

    def do_clear_tmp(self):
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
    app.setWindowIcon(QIcon(":res/demo.png"))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    if 'pnl' not in job.steps:
        QMessageBox.information(None, '提示', '该料号没有pnl')
        sys.exit()
    step = job.steps.get('pnl')
    board = MultiLayerBoard()
    board.show()
    sys.exit(app.exec_())
