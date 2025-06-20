#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:SetEdgeSealing.py
   @author:zl
   @time:2024/7/17 08:30
   @software:PyCharm
   @desc: set封边
"""
import datetime
import os
import re
import sys
import res_rc

import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont, QIcon, QDoubleValidator
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QTableWidgetItem, QComboBox, QAbstractItemView, \
    QHeaderView

import SetEdgeSealingUI as ui
import genClasses as gen


class SetEdgeSealing(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        #
        step.initStep()
        self.label_logo.setPixmap(QPixmap(':/res/logo.png'))
        self.label_jobname.setText(jobname)
        self.lineEdit_set_w.setText(str(step.profile2.xsize))
        self.lineEdit_set_h.setText(str(step.profile2.ysize))
        self.lineEdit_margin_x.setValidator(QDoubleValidator())
        self.lineEdit_margin_y.setValidator(QDoubleValidator())
        self.lineEdit_margin_x.setText('1.2')
        self.lineEdit_margin_y.setText('1.2')
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
            type_name = '软板'
        elif __type == 'rf':
            type_name = '软硬结合板'
        elif __type == 'pc':
            type_name = '硬板'
        else:
            type_name = '其他'
        self.label_product.setText(type_name)
        # 铺铜
        methods = ['实铜', '网格', '六边形']
        # methods = ['实铜', '六边形']
        self.comboBox_method.addItems(methods)
        # 面向
        self.pushButton_run.setIcon(qtawesome.icon('fa.upload', color='cyan'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='cyan'))
        self.pushButton_run.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            'QPushButton{font:11pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

    def run(self):
        # 取到margin
        self.margin_x = self.lineEdit_margin_x.text()
        self.margin_y = self.lineEdit_margin_y.text()
        if self.margin_x == '' or self.margin_y == '':
            QMessageBox.warning(self, '警告', 'margin值不能为空!')
            return
        self.margin_x = float(self.margin_x)
        self.margin_y = float(self.margin_y)
        # if not step.isLayer('map-set'):
        #     confirm = QMessageBox.warning(self, 'tips', '没有map-set层，是否继续', QMessageBox.Ok | QMessageBox.Cancel)
        #     if confirm == QMessageBox.Cancel:
        #         return
        self.fill_sur = 'surface'
        if self.comboBox_method.currentText() == '网格':
            self.fill_sur = 'grid'
        elif self.comboBox_method.currentText() == '六边形':
            self.fill_sur = 'lbx'
        step.initStep()
        self.set = Set()
        self.set.ClearAndCreate()
        self.set.do_surface()
        # self.set.do_mk()
        # self.set.do_mark()
        QMessageBox.information(self, 'tips', '执行完毕!')


class Set():
    def __init__(self):
        self.user = job.getUser()
        self.tmp_map = f'map+++{step.pid}'
        self.cus = None  # 客户类型
        # 线路
        self.signalLays = job.SignalLayers
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
        self.drills = []
        for row in job.matrix.returnRows('board', 'drill'):
            if re.match('f\d+', row):
                self.drills.append(row)


    # 清空层创建层
    def ClearAndCreate(self):
        step.VOF()
        for layer in self.signalLays + self.wzs + self.covs + self.zhs + self.dks + self.yys + self.drills:
            step.affect(layer)
        step.selectDelete()
        step.unaffectAll()

    # 铺铜
    def do_surface(self):
        i = 0
        for lay in self.signalLays:
            if i % 2:
                direction = 'even'
                x_off = 0.9
                y_off = 0.9
            else:
                direction = 'odd'
                x_off = 0
                y_off = 0
            step.affect(lay)
            step.srFill_2(sr_margin_x=setEdgeSealing.margin_x, sr_margin_y=setEdgeSealing.margin_y)
            if setEdgeSealing.fill_sur == 'grid':
                line_width = 200
                # 网格铜外围线宽
                outline_width = 400
                # 网格铜边到边间距
                side_spacing = 500
                step.selectFill(type='standard', solid_type='surface', std_type='cross', x_off=x_off,
                                     y_off=y_off, std_line_width=line_width, std_step_dist=side_spacing,
                                     std_indent=direction, outline_draw='yes', outline_width=outline_width)
            elif setEdgeSealing.fill_sur == 'lbx':
                x_off = 4.2 if i % 2 else 0
                y_off = 0
                step.selectFill(type='pattern', dx=12.6, dy=7.3, solid_type='surface', symbol='lbx_fill',
                                     x_off=x_off, y_off=y_off, std_indent=direction, cut_prims='yes')
            step.unaffectAll()
            step.resetFill()
            i += 1
        step.VOF()
        for zh in self.zhs:
            step.affect(zh)
        step.srFill_2()
        step.unaffectAll()
        step.resetFill()
        # 对dks铺铜
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
                side_spacing = 500
                step.affect(dk)
                step.srFill_2(sr_margin_x= setEdgeSealing.margin_x + 0.5, sr_margin_y=setEdgeSealing.margin_y + 0.5)
                tmp = dk + '+++'
                step.copySel(tmp)
                step.unaffectAll()
                step.affect(tmp)
                step.selectResize(200)
                # step.selectFill(type='standard', solid_type='surface', std_type='cross', x_off=0,
                #                 y_off=0, std_line_width=line_width, std_step_dist=side_spacing,
                #                 std_indent=direction, outline_draw='yes', outline_width=outline_width)
                step.selectFill(type='standard', solid_type='surface', std_type='cross', x_off=0,
                                y_off=0, std_line_width=line_width, std_step_dist=side_spacing,
                                std_indent=direction)
                step.copySel(dk, 'yes')
                step.unaffectAll()
                step.resetFill()
                step.removeLayer(tmp)

    # 加线路层symbol
    def do_mk(self):
        if step.isLayer('mk'):
            mk_tmp = f'mk+++{step.pid}'
            step.affect('mk')
            step.copySel(mk_tmp)
            step.unaffectAll()
            step.affect(mk_tmp)
            step.selectChange('r2300')
            for signal in self.signalLays:
                step.copySel(signal)
            step.selectChange('donut_r2000x1000')
            step.copySel(self.signalLays[0], 'yes')
            step.selectChange('r1500')
            for cov in self.covs:
                step.copySel(cov)
            step.selectChange('r2700')
            for dk in self.dks:
                step.copySel(dk, 'yes')
            step.unaffectAll()
            step.removeLayer(mk_tmp)

    def do_mark(self):
        if not step.isLayer('map-set'):
            return
        tmp_map = f'map-set+++{step.pid}'
        step.affect('map-set')
        for i, signal in enumerate(self.signalLays):
            if not i % 2:
                step.copySel(signal, 'yes')
        step.unaffectAll()
        step.affect('map-set')
        step.copySel(tmp_map)
        step.unaffectAll()
        step.affect(tmp_map)
        step.selectBreak()
        step.setFilterTypes('line')
        step.selectAll()
        if step.Selected_count():
            step.selectDelete()
        step.selectPolarity()
        step.selectCutData()
        for i, signal in enumerate(self.signalLays):
            if i % 2:
                step.copySel(signal, 'yes')
        for cov in self.covs:
            step.copySel(cov)
        for dk in self.dks:
            step.copyToLayer(dk, 'yes', size=500)
        step.unaffectAll()
        step.removeLayer(tmp_map)
        step.removeLayer(tmp_map + '+++')
        # 黑色覆盖膜 文字层加那些symbol的文字
        if setEdgeSealing.radioButton_yellow.isChecked():
            return
        step.affect('map-set')
        step.copySel(tmp_map)
        step.unaffectAll()
        step.affect(tmp_map)
        step.selectBreak()
        step.setFilterTypes('line')
        step.selectAll()
        step.resetFilter()
        if step.Selected_count():
            step.selectReverse()
            if step.Selected_count():
                step.selectDelete()
        for wz in self.wzs:
            step.copySel(wz)
        step.unaffectAll()
        step.removeLayer(tmp_map)

class QComboBox(QComboBox):
    def wheelEvent(self, e):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setStyleSheet('QPushButton{font-family:"微软雅黑";font:11pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')
    app.setWindowIcon(QIcon(":res/demo.png"))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    if 'set' not in job.steps:
        QMessageBox.information(None, '提示', '该料号没有set')
        sys.exit()
    step = job.steps.get('set')
    setEdgeSealing = SetEdgeSealing()
    setEdgeSealing.show()
    sys.exit(app.exec_())
