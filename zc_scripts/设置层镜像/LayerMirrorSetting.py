#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:LayerMirrorSetting.py
   @author:zl
   @time:2024/8/26 9:43
   @software:PyCharm
   @desc:
   设置层镜像属性，在资料导出时可以按属性确定是否镜像
   多个step都会有各自的层属性，故设计一键yes/一键no
"""
import os
import sys

import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont, QCursor
from PyQt5.QtWidgets import QWidget, QApplication, QTableWidgetItem, QComboBox, QTableWidget, QHeaderView, QMessageBox, \
    QHBoxLayout, QPushButton

import LayerMirrorSettingUI as ui
import genClasses as gen
import res_rc


class LayerMirrorSetting(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.label_title.setText(f'Job:{jobname}')
        header = ['层名']
        for s in job.steps:
            header.append(f'{s}(是否镜像)')
        header.append('一键设置')
        self.tableWidget.setColumnCount(len(header))
        self.tableWidget.setHorizontalHeaderLabels(header)
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.setSelectionBehavior(QHeaderView.SelectRows)
        self.tableWidget.setSelectionMode(QHeaderView.SingleSelection)
        self.tableWidget.setEditTriggers(QHeaderView.NoEditTriggers)
        self.pushButton_exec.setIcon(qtawesome.icon('fa.download', color='white'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='white'))
        self.pushButton_exec.clicked.connect(self.exec)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            'QPushButton{font:11pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}QTableWidget::Item:selected{background: rgb(224, 224, 224);color:black;}')
        self.load_table()

    def exec(self):
        for row in range(self.tableWidget.rowCount()):
            layer = self.tableWidget.item(row, 0).text()
            n = 1
            for s in job.steps:
                step = job.steps.get(s)
                mir = self.tableWidget.cellWidget(row, n).currentText()
                step.COM(
                    f'set_attribute,type=layer,job={jobname},name1={s},name2={layer},name3=,attribute=.out_mirror,value={mir},units=inch')
                n += 1
        QMessageBox.information(self, 'tips', '设置完成~')
        sys.exit()

    def load_table(self):
        rows = job.matrix.returnRows('board', 'signal|solder_mask|coverlay|silk_screen|drill')
        self.tableWidget.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(row)))
            n = 1
            for s in job.steps:
                step = job.steps.get(s)
                mirror_box = QComboBox()
                mirror_box.addItems(['yes', 'no'])
                mirror = step.layers.get(row).getGenesisAttr('.out_mirror')
                mirror_box.setCurrentText(mirror)
                self.tableWidget.setCellWidget(i, n, mirror_box)
                n += 1
            widget = QWidget()
            widget.setStyleSheet('QPushButton{background:red;font-family: "微软雅黑";font-size:9pt;} QPushButton:hover{background:white;color:red;}')
            hbox = QHBoxLayout(widget)
            hbox.setContentsMargins(2, 0, 2, 0)
            hbox.setSpacing(2)
            btn1 = QPushButton("一键yes")
            btn1.setCursor(QCursor(Qt.PointingHandCursor))
            btn1.row = i
            btn2 = QPushButton("一键no")
            btn2.setCursor(QCursor(Qt.PointingHandCursor))
            btn2.row = i
            btn1.clicked.connect(self.toggle_check)
            btn2.clicked.connect(self.toggle_check)
            hbox.addWidget(btn1)
            hbox.addWidget(btn2)
            self.tableWidget.setCellWidget(i, n, widget)

    def toggle_check(self):
        row = self.sender().row
        check = 'yes' if self.sender().text() == '一键yes' else 'no'
        for n in range(len(job.steps)):
            self.tableWidget.cellWidget(row, n + 1).setCurrentText(check)


class QComboBox(QComboBox):
    def wheelEvent(self, event):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':res/demo.png'))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    ex = LayerMirrorSetting()
    ex.show()
    sys.exit(app.exec_())
