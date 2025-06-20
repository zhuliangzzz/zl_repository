#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:FillGaps.py
   @author:zl
   @time:2024/7/5 11:29
   @software:PyCharm
   @desc:
"""
import os
import sys

import qtawesome
from PyQt5.QtGui import QIcon, QDoubleValidator
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QAbstractItemView

import FillGrapsUI as ui
import genClasses as gen
import res_rc


class FillGaps(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.label_title.setText(f'Job: {jobname}\tStep: {stepname}')
        self.listWidget.addItems(job.SignalLayers)
        self.lineEdit_size.setValidator(QDoubleValidator())
        self.lineEdit_size.setText('200')
        self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.pushButton_clear_patch.setIcon(qtawesome.icon('fa.trash', color='white'))
        self.pushButton_exec.setIcon(qtawesome.icon('fa.download', color='white'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='white'))
        self.pushButton_clear_patch.clicked.connect(self.clear)
        self.pushButton_exec.clicked.connect(self.fill)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            'QListWidget::Item{height:24px;border-radius:1.5px;} QPushButton{background-color:#0081a6;color:white;} QPushButton:hover{background:black;} QListWidget::Item:selected{background:#34AFD1;color:white;}')

    def clear(self):
        layers = [item.text() for item in self.listWidget.selectedItems()]
        if not layers:
            QMessageBox.warning(self, 'tips', '请选择层!')
            return
        step.initStep()
        for layer in layers:
            step.affect(layer)
        step.setAttrFilter2('.patch')
        step.selectAll()
        step.resetFilter()
        if step.Selected_count():
            step.selectDelete()
            QMessageBox.information(self, 'tips', '已清除.patch属性的填充间隙!')
            step.unaffectAll()
            sys.exit()
        step.unaffectAll()

    def fill(self):
        layers = [item.text() for item in self.listWidget.selectedItems()]
        if not layers:
            QMessageBox.warning(self, 'tips', '请选择层!')
            return
        size = self.lineEdit_size.text().strip()
        if not size:
            QMessageBox.warning(self, 'tips', '请输入间隙大小!')
            return
        step.initStep()
        checklist = gen.Checklist(step, type='valor_dfm_clean_holes')
        checklist.action()
        # pp_layer = gtl\;gbl)(pp_size=200)(pp_overlap=25.4)(pp_mode=X or Y)(pp_hi=Cover islands\;Cover holes)(pp_cover_f=Lines\;Surfaces)
        params = {
            'pp_layer': ';'.join(layers),
            'pp_size': f'{size}',
            'pp_overlap': '25.4',
            'pp_mode': 'X or Y',
            'pp_hi': 'Cover islands\;Cover holes',
            'pp_cover_f': 'Lines\;Surfaces'
        }
        checklist.update(params=params)
        checklist.run()
        QMessageBox.information(self, 'tips', '执行完毕!')
        sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':/res/demo.png'))
    jobname = os.environ.get('JOB')
    stepname = os.environ.get('STEP')
    job = gen.Job(jobname)
    if not stepname:
        QMessageBox.warning(None, 'tips', '请打开step执行!')
        sys.exit()
    step = job.steps.get(stepname)
    fillGaps = FillGaps()
    fillGaps.show()
    sys.exit(app.exec_())
