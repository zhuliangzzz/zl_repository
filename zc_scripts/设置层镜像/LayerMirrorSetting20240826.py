#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:LayerMirrorSetting.py
   @author:zl
   @time:2024/8/26 9:43
   @software:PyCharm
   @desc:
   设置层镜像属性，在资料导出时可以按属性确定是否镜像
"""
import os
import sys

import qtawesome
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QApplication, QTableWidgetItem, QComboBox, QTableWidget, QHeaderView, QMessageBox

import LayerMirrorSettingUI as ui
import genClasses as gen
import res_rc


class LayerMirrorSetting(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.label_title.setText(f'Job:{jobname}\tStep:{stepname}')
        header = ['层名', '输出镜像']
        self.tableWidget.setColumnCount(len(header))
        self.tableWidget.setHorizontalHeaderLabels(header)
        self.tableWidget.verticalHeader().hide()
        # self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.pushButton_exec.setIcon(qtawesome.icon('fa.download', color='white'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='white'))
        self.pushButton_exec.clicked.connect(self.exec)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            'QPushButton{font:11pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')
        self.load_table()

    def exec(self):
        for row in range(self.tableWidget.rowCount()):
            layer = self.tableWidget.item(row, 0).text()
            mir = self.tableWidget.cellWidget(row, 1).currentText()
            step.COM(
                f'set_attribute,type=layer,job={jobname},name1={stepname},name2={layer},name3=,attribute=.out_mirror,value={mir},units=inch')
        QMessageBox.information(self, 'tips', '设置完成~')
        sys.exit()

    def load_table(self):
        rows = job.matrix.returnRows('board', 'signal|solder_mask|coverlay|silk_screen|drill')
        self.tableWidget.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(row)))
            mirror_box = QComboBox()
            mirror_box.addItems(['yes', 'no'])
            mirror = step.layers.get(row).getGenesisAttr('.out_mirror')
            mirror_box.setCurrentText(mirror)
            self.tableWidget.setCellWidget(i, 1, mirror_box)


class QComboBox(QComboBox):
    def wheelEvent(self, event):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':res/demo.png'))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    stepname = os.environ.get('STEP')
    step = job.steps.get(stepname)
    ex = LayerMirrorSetting()
    ex.show()
    sys.exit(app.exec_())
