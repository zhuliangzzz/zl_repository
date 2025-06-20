#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AttrTool.py
   @author:zl
   @time:2023/11/14 16:09
   @software:PyCharm
   @desc:
"""
import os
import sys

import qtawesome

import AttrToolUI as ui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import genClasses as gen
import res_rc


class AttrTool(QWidget, ui.Ui_Form):
    def __init__(self):
        super(AttrTool, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.title.setText(f"Job:{jobname} Step:{stepname}")
        jobinfo = job.DO_INFO(f'-t attributes -e {jobname}')
        self.job_attr_names = [str(name) for name in jobinfo.get('gATRname')]
        self.job_attr_names.insert(0, '*')
        self.attr_name.addItems(self.job_attr_names)
        self.attr_name.setCurrentText('.string')
        self.attr_val.setText('wg')
        self.setStyleSheet('''QPushButton{background-color:#0081a6;color:white;font:10pt;font-family:"Liberation Serif";}
                   QPushButton:hover{background:black;}
                   QGroupBox,#title{color: black;font-weight:bold;}
                   ''')
        self.add_btn.setIcon(qtawesome.icon('fa.download', scale_factor=1, color='white'))
        self.del_btn.setIcon(qtawesome.icon('fa.trash', scale_factor=1, color='white'))
        self.exit_btn.setIcon(qtawesome.icon('fa.sign-out', scale_factor=1, color='white'))
        self.tips_btn.clicked.connect(self.show_)
        self.add_btn.clicked.connect(self.add)
        self.del_btn.clicked.connect(self.delete)
        self.exit_btn.clicked.connect(lambda: sys.exit())

    def add(self):
        if step.Selected_count():
            name = self.attr_name.currentText()
            val = self.attr_val.text().strip()
            if name == '*' or name not in self.job_attr_names:
                QMessageBox.warning(None, 'warning', '输入的属性不存在！')
                return
            if val:
                step.addAttr(name, attrVal='text=' + val)
            else:
                step.addAttr(name, attrVal='')
            QMessageBox.information(None, 'tips', '添加属性成功！')
        else:
            QMessageBox.warning(None, 'warning', '没有选择物件！')
        sys.exit()

    def delete(self):
        if step.Selected_count():
            name = self.attr_name.currentText()
            if name == '*':
                attr_str = r'\;'.join(self.job_attr_names[1:])
                step.COM('sel_delete_atr,attributes=' + attr_str)
            else:
                step.COM('sel_delete_atr,attributes=' + name)
            QMessageBox.information(None, 'tips', '删除属性成功！')
        else:
            QMessageBox.warning(None, 'warning', '没有选择物件！')
        sys.exit()

    def show_(self):
        png = '/genesis/sys/scripts/zl/python/images/attributes.png'
        self.box = QMessageBox(self)
        self.box.setWindowTitle("常见属性")
        btn = QPushButton('关闭')
        btn.setIcon(qtawesome.icon('fa.times-circle', scale_factor=1, color='white'))
        self.box.addButton(btn, QMessageBox.YesRole)
        self.box.setIconPixmap(QPixmap(png))
        self.box.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    # app.setStyleSheet('*{font:11pt;font-family:"Liberation Serif";}')
    app.setWindowIcon(QIcon(':/res/demo.png'))
    # if not os.environ.get('JOB'):
    #     QMessageBox.warning(None, 'tips', '请打开料号!')
    #     sys.exit()
    if not os.environ.get('STEP'):
        QMessageBox.warning(None, 'tips', '请打开step!')
        sys.exit()
    jobname = os.environ.get('JOB')
    stepname = os.environ.get('STEP')
    job = gen.Job(jobname)
    step = job.steps.get(stepname)
    attrTool = AttrTool()
    attrTool.show()
    sys.exit(app.exec_())
