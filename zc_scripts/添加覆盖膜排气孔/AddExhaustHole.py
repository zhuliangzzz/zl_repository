#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AddExhaustHole.py
   @author:zl
   @time:2024/7/8 9:31
   @software:PyCharm
   @desc:添加覆盖膜排气孔
"""
import os
import sys

import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QTableWidgetItem, QAbstractItemView, QComboBox, \
    QHeaderView

import AddExhaustHoleUI as ui

import genClasses as gen
import res_rc


class AddExhaustHole(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        header = ['覆盖膜层', '排气孔层', '是否有排气孔层', '线路层']
        self.tableWidget.setColumnCount(len(header))
        self.tableWidget.setHorizontalHeaderLabels(header)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.pushButton_exec.setIcon(qtawesome.icon('fa.download', color='white'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='white'))
        self.pushButton_exec.clicked.connect(self.exec)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet('QPushButton{background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')
        self.loadtable()

    def loadtable(self):
        covs = job.matrix.returnRows('board', 'coverlay')
        if not covs:
            QMessageBox.infomation(None, '提示', '没有覆盖膜层')
            sys.exit()
        self.tableWidget.setRowCount(len(covs))
        for n, cov in enumerate(covs):
            item = QTableWidgetItem()
            item.setText(cov)
            item.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(n, 0, item)
            item = QTableWidgetItem()
            item.setText(f'{cov}-pq')
            item.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(n, 1, item)
            item = QTableWidgetItem()
            item.setText('×')
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(QColor("red"))
            if step.isLayer(f'{cov}-pq'):
                item.setText('√')
                item.setForeground(QColor("green"))
            self.tableWidget.setItem(n, 2, item)
            item = QComboBox()
            item.addItems(job.SignalLayers)
            item.setCurrentText(job.SignalLayers[-1]) if n > len(job.SignalLayers) - 1 else item.setCurrentText(
                job.SignalLayers[n])
            self.tableWidget.setCellWidget(n, 3, item)

    def exec(self):
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(row, 2).text() == '×':
                QMessageBox.warning(self, '提示', '没有排气孔层!')
                return
        step.initStep()
        for row in range(self.tableWidget.rowCount()):
            cov = self.tableWidget.item(row, 0).text()
            pq = self.tableWidget.item(row, 1).text()
            signal = self.tableWidget.cellWidget(row, 3).currentText()
            tmp_pq = f'{pq}+++'
            step.Flatten(pq, tmp_pq)
            step.affect(tmp_pq)
            step.selectChange('r1000')
            step.copySel(cov)
            step.selectChange('r1601')
            step.copySel(signal, 'yes')
            step.unaffectAll()
            step.removeLayer(tmp_pq)
        QMessageBox.information(self, '提示', '添加完成！')
        sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':/res/demo.png'))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    step = job.steps.get('set')
    add_exhaust_hole = AddExhaustHole()
    add_exhaust_hole.show()
    sys.exit(app.exec_())
