#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AddC5.py
   @author:zl
   @time:2024/7/13 9:35
   @software:PyCharm
   @desc:
"""
import os
import re
import sys

import qtawesome
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox

import AddC5UI as ui

import genClasses as gen
import res_rc


class AddC5(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.label_title.setText(f'Job: {jobname}\t Step: {stepname}')
        self.label_tips.setText('<font style="color:red;">*</font>添加位置：距离profile内1.5mm pcs外2mm')
        self.listWidget.addItems(job.SignalLayers)
        rows = job.matrix.returnRows()
        ccds = filter(lambda row: re.match('ccd\d+$', row), rows)
        self.comboBox.addItems(ccds)
        self.pushButton_exec.setIcon(qtawesome.icon('fa.download', color='white'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='white'))
        self.pushButton_exec.clicked.connect(self.exec)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            '''
            #label_title{color:#eee;border-radius:5px;background-color:#0081a6;} 
            QPushButton{font:9pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}
            QListWidget::Item{height:26px;border-radius:1.5px;}
            QListWidget::Item:selected{background: #0081a6;color:white;}
            ''')

    def exec(self):
        top_layers = [item.text() for item in self.listWidget.selectedItems()]
        bot_layers = filter(lambda lay: lay not in top_layers, job.SignalLayers)
        ccd = self.comboBox.currentText()
        covs = job.matrix.returnRows('board', 'coverlay')
        self.hide()
        step.initStep()
        area_layer = f'c5_area+++{step.pid}'
        add_layer = f'c5+++{step.pid}'
        step.createLayer(area_layer)
        step.createLayer(add_layer)
        ###
        step.affect(area_layer)
        step.srFill_2(step_margin_x=1.5, step_margin_y=1.5, sr_margin_x=2, sr_margin_y=2, stop_at_steps='pcs')
        step.unaffectAll()
        #
        signal_layer = job.SignalLayers[-1]
        tmp_signal = f'{signal_layer}+++{step.pid}'
        step.affect(signal_layer)
        step.copySel(tmp_signal)
        step.unaffectAll()
        step.affect(tmp_signal)
        step.setAttrFilter('.pattern_fill')
        step.selectAll()
        step.resetFilter()
        if step.Selected_count():
            step.selectDelete()
        step.selectPolarity()
        step.Contourize(0)
        step.selectResize(400)
        step.unaffectAll()
        #
        nx = step.profile2.xsize / 5 + 1
        ny = step.profile2.ysize / 5 + 1
        step.affect(add_layer)
        step.addPad(0, 0, 'r2000', nx=nx, ny=ny, dx=5000, dy=5000)
        step.refSelectFilter(area_layer, mode='cover')
        if step.Selected_count():
            step.selectReverse()
            if step.Selected_count():
                step.selectDelete()
        else:
            QMessageBox.warning(self, 'tips', '范围内没有放置c5的位置')
            step.unaffectAll()
            step.removeLayer(tmp_signal)
            step.removeLayer(area_layer)
            step.removeLayer(add_layer)
            sys.exit()
        step.selectChange('c5')
        step.refSelectFilter(tmp_signal)
        if step.Selected_count():
            step.selectDelete()
        step.unaffectAll()
        step.removeLayer(tmp_signal)
        step.display(add_layer)
        QMessageBox.information(self, 'tips', '请选中要加的c5')
        step.PAUSE('select c5')
        step.affect(add_layer)
        step.selectReverse()
        if step.Selected_count():
            step.selectDelete()
        step.selectChange('c5')
        for top_layer in top_layers:
            step.copySel(top_layer)
        for bot_layer in bot_layers:
            step.selectChange('r4201')
            step.copySel(bot_layer)
            step.selectChange('r3201')
            step.copySel(bot_layer, 'yes')
        for cov in covs:
            step.selectChange('r2000')
            step.copySel(cov)
        if ccd:
            step.selectChange('r2000')
            step.copySel(ccd)
        step.unaffectAll()
        step.removeLayer(area_layer)
        step.removeLayer(add_layer)
        QMessageBox.information(self, '提示', '添加完成')
        sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setStyleSheet('QMessageBox{font:10pt;}')
    app.setWindowIcon(QIcon(":res/demo.png"))
    jobname = os.environ.get('JOB')
    if not jobname:
        QMessageBox.warning(None, 'tips', '请打开料号!')
        sys.exit()
    stepname = os.environ.get('STEP')
    if not stepname:
        QMessageBox.warning(None, 'tips', '请打开Step!')
        sys.exit()
    job = gen.Job(jobname)
    step = job.steps.get(stepname)
    ex = AddC5()
    ex.show()
    sys.exit(app.exec_())
