#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:NetlistAnalyser.py
   @author:zl
   @time:2024/8/10 15:38
   @software:PyCharm
   @desc:
"""
import os
import re
import sys

import qtawesome
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QComboBox

import NetlistAnalyserUI as ui
import genClasses as gen
import res_rc


class NetlistAnalyser(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.path = 'D:/scripts/tmp/'
        self.setupUi(self)
        self.render()

    def render(self):
        self.label_title.setText(f'Job: {jobname}')
        self.comboBox_option.addItem('Compare')
        self.__type = {
            'CAD': 'cad',
            'Reference': 'ref',
            'Current': 'cur',
            'CBC': 'cur_cad'
        }
        self.comboBox_top_step.addItems(job.steps)
        self.comboBox_top_step.setCurrentText('orig')
        self.comboBox_top_type.addItems(self.__type)
        self.comboBox_top_type.setCurrentIndex(2)
        self.comboBox_top_type.currentIndexChanged.connect(self.typeChanged)
        #
        self.comboBox_bot_step.addItems(job.steps)
        self.comboBox_bot_step.setCurrentText('pcs')
        self.comboBox_bot_type.addItems(self.__type)
        self.comboBox_bot_type.setCurrentIndex(2)
        self.exec_btn.setIcon(qtawesome.icon('fa.download', scale_factor=1, color='white'))
        self.show_btn.setIcon(qtawesome.icon('fa.search', scale_factor=1, color='white'))
        self.exit_btn.setIcon(qtawesome.icon('fa.sign-out', scale_factor=1, color='white'))
        self.show_btn.setVisible(False)
        self.exec_btn.clicked.connect(self.exec)
        self.show_btn.clicked.connect(self.show_analyser)
        self.exit_btn.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            'QPushButton{font:11pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')

    def typeChanged(self, index):
        self.comboBox_bot_type.setCurrentIndex(index)

    def show_analyser(self):
        job.COM(f'netlist_page_open,set=check,job1={jobname},step1={self.top_step},type1={self.top_type},job2={jobname},step2={self.bot_step},type2={self.bot_type}')
        sys.exit()

    def exec(self):
        self.top_step = self.comboBox_top_step.currentText()
        self.top_type = self.__type.get(self.comboBox_top_type.currentText())
        self.bot_step = self.comboBox_bot_step.currentText()
        self.bot_type = self.__type.get(self.comboBox_bot_type.currentText())
        status = job.net_recalc(step=self.top_step, type=self.top_type)
        if status != 0:
            QMessageBox.warning(self, 'warning', '没有测试点')
            sys.exit()
        status = job.net_recalc(step=self.bot_step, type=self.bot_type)
        if status != 0:
            QMessageBox.warning(self, 'warning', '没有测试点')
            sys.exit()
        job.net_compare(step1=self.top_step, type1=self.top_type, step2=self.bot_step, type2=self.bot_type)
        outfile = self.path + 'net_report'
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        job.net_result('file', outfile)
        try:
            with open(outfile, 'r') as inputstream:
                contents = inputstream.read()
        except IOError as e:
            print(e)
        else:
            inputstream.close()
        os.unlink(outfile)
        self.show_btn.setVisible(True)
        res_shorted = re.search(r'Mismatch Type: Shorted\n\n(\s.+\n)+\n\sTotal : (\d+)', contents)
        res_broken = re.search(r'Mismatch Type: Broken\n\n(\s.+\n)+\n\sTotal : (\d+)', contents)
        result = []
        if res_shorted:
            total = res_shorted.group(2)
            result.append(f'检测到短路：{total}处')
        if res_broken:
            total = res_broken.group(2)
            result.append(f'检测到开路：{total}处')
        if result:
            QMessageBox.information(self, '检测到开短路', '\n'.join(result))
        else:
            QMessageBox.information(self, '检测ok', '分析通过')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':res/demo.png'))
    jobname = os.environ.get('JOB')
    if not jobname:
        QMessageBox.information(None, '提示', '请打开料号')
        sys.exit()
    job = gen.Job(jobname)
    if 'orig' not in job.steps or 'pcs' not in job.steps:
        QMessageBox.information(None, '提示', '没有orig或pcs')
        sys.exit()
    netlistAnalyser = NetlistAnalyser()
    netlistAnalyser.show()
    sys.exit(app.exec_())
