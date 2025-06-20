#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AddDateAndLogo.py
   @author:zl
   @time:2024/8/14 10:05
   @software:PyCharm
   @desc:
   20240823 zl 不同的周期格式对应不同的属性格式
"""
import datetime
import os
import sys

import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QIcon, QIntValidator
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox

import AddDateAndLogoUI as ui
import res_rc
import genClasses as gen


class AddDateAndLogo(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.setWindowTitle(' ')
        self.label_logo.setStyleSheet('color:white;background-color: rgb(69, 155, 129);border-radius:4px;padding:20px;')
        palette = QPalette()
        self.widget.setAutoFillBackground(True)
        palette.setColor(QPalette.Window, Qt.black)
        self.widget.setPalette(palette)
        week_formats = ['', '年周', '周年']
        self.comboBox_week_format.addItems(week_formats)
        layers = job.matrix.returnRows('board', 'signal|silk_screen')
        self.comboBox_target_layer.addItems(layers)
        self.checkBox.clicked.connect(self.label_show)
        self.checkBox_2.clicked.connect(self.label_show)
        self.comboBox_week_format.currentIndexChanged.connect(self.label_show)
        self.lineEdit_week.setEnabled(False)
        self.lineEdit_week.returnPressed.connect(self.input_week)
        self.lineEdit_week.setValidator(QIntValidator())
        self.pushButton_modify_week.setIcon(qtawesome.icon('fa.edit', color='white'))
        self.pushButton_exec.setIcon(qtawesome.icon('fa.download', color='white'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='white'))
        self.pushButton_modify_week.clicked.connect(self.modify_week)
        self.pushButton_exec.clicked.connect(self.exec)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            '''
            #label_1_show,#label_2_show,#label_3_show{color:red;font-weight:bold; font-size: 50px;border-radius:4px;}
            QPushButton{font:10pt;background-color:#459B81;color:white;} QPushButton:hover{background:#333;} QCheckBox::indicator:checked{background:#459B81;}''')


    def label_show(self):
        self.lineEdit_week.clear()
        self.lineEdit_week.setEnabled(True)
        self.lineEdit_week.setPlaceholderText('手动输入周期')
        if self.checkBox.isChecked():
            self.label_1_show.setStyleSheet('background-color: rgb(69, 155, 129);')
        else:
            self.label_1_show.setStyleSheet('')
        if self.checkBox_2.isChecked():
            self.label_2_show.setStyleSheet('background-color: rgb(69, 155, 129);')
        else:
            self.label_2_show.setStyleSheet('')
        if self.comboBox_week_format.currentIndex() != 0:
            week_format = self.comboBox_week_format.currentText()
            text = self.get_week(week_format)
            self.label_3_show.setText(text)
        else:
            self.label_3_show.clear()
            self.lineEdit_week.setEnabled(False)
            self.lineEdit_week.setPlaceholderText('')

    def input_week(self):
        self.label_3_show.setText(self.lineEdit_week.text())

    def modify_week(self):
        week = self.label_3_show.text()
        if len(week) != 4:
            QMessageBox.warning(self, '警告', '周期必须为四位数')
            return
        step.initStep()
        layer = self.comboBox_target_layer.currentText()
        step.affect(layer)
        # 20240823 根据周期格式设置对应的属性格式
        attrs = ('y1', 'y2', 'w1', 'w2') if self.comboBox_week_format.currentIndex() == 1 else ('w1', 'w2', 'y1', 'y2')
        for w, attr in zip(week, attrs):
            step.setAttrFilter('.string', f'text={attr}')
            step.selectAll()
            step.resetFilter()
            if step.Selected_count():
                step.changeText(w)
        step.unaffectAll()
        QMessageBox.information(self, '提示', '更新完成！')

    def exec(self):
        if self.label_3_show.text() != '':
            if len(self.label_3_show.text()) != 4:
                QMessageBox.warning(self, '警告', '周期必须为四位数')
                return
        else:
            if not self.checkBox.isChecked() and not self.checkBox_2.isChecked():
                QMessageBox.warning(self, '警告', '未选择要加的周期和标识')
                return
        layer = self.comboBox_target_layer.currentText()
        step.initStep()
        add_layer = f'{layer}_add++'
        step.VOF()
        step.removeLayer(add_layer)
        step.VON()
        self.hide()
        step.createLayer(add_layer)
        step.display(add_layer)
        step.display_layer(layer, 2)
        step.MOUSE('select a point to add')
        mouseans = step.MOUSEANS
        ad_x1 = float('%.3f' % float(mouseans.split()[0]))
        ad_y1 = float('%.3f' % float(mouseans.split()[1]))
        if self.checkBox.isChecked():
            # step.addPad(ad_x1, ad_y1, 'r3000')
            pass
        if self.checkBox_2.isChecked():
            # step.addPad(ad_x1 + 2, ad_y1, 'r4000')
            pass
        if self.comboBox_week_format.currentIndex() != 0:
            week = self.label_3_show.text()
            # 20240823 根据周期格式设置对应的属性格式
            attrs = ('y1', 'y2', 'w1', 'w2') if self.comboBox_week_format.currentIndex() == 1 else ('w1', 'w2', 'y1', 'y2')
            offset = 5
            for w, attr in zip(week, attrs):
                step.addAttr_zl(f'.string,text={attr}')
                step.addText(ad_x1 + offset, ad_y1, w, 1.2, 1.2, 0.492125988, fontname='simplex', attributes='yes')
                step.resetAttr()
                offset += 1
        step.clearAll()
        if 'b' in layer:
            infoDict = step.DO_INFO(' -t layer -e %s/%s/%s -d LIMITS,units=mm' % (jobname, step.name, layer))
            xmin = infoDict['gLIMITSxmin']
            ymin = infoDict['gLIMITSymin']
            xmax = infoDict['gLIMITSxmax']
            ymax = infoDict['gLIMITSymax']
            xc = (xmin + xmax) / 2
            yc = (ymin + ymax) / 2
            step.affect(add_layer)
            step.Transform(oper='mirror', x_anchor=xc, y_anchor=yc)
            step.unaffectAll()
        QMessageBox.information(self, '提示', f'已添加到{add_layer}层！')

    def get_week(self, format):
        if format == '年周':
            return datetime.datetime.now().strftime('%y%U')
        elif format == '周年':
            return datetime.datetime.now().strftime('%U%y')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':/res/demo.png'))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    if not os.environ.get('STEP'):
        QMessageBox.warning(None, 'tips', '请打开step！')
        sys.exit()
    stepname = os.environ.get('STEP')
    step = job.steps.get(stepname)
    ex = AddDateAndLogo()
    ex.show()
    sys.exit(app.exec_())
