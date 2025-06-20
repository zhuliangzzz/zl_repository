#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:InputDxfTool.py
   @author:zl
   @time:2024/04/11 14:31
   @software:PyCharm
   @desc:
   钻锣带工具导入
"""
import glob
import os
import re
import sys

import qtawesome
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import InputDxfToolUI as ui

# sys.path.append('/genesis/sys/scripts/zl/lib')
import genClasses as gen
import res_rc


class InputDxfTool(QWidget, ui.Ui_Form):
    def __init__(self):
        super(InputDxfTool, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.all_files = []
        self.path = f'D:\scripts'
        self.label_jobname.setText(f'Job：{jobname}')
        self.comboBox_steps.addItems(job.steps)
        if stepname:
            self.comboBox_steps.setCurrentText(stepname)
        self.lineEdit_path.setText(self.path)
        self.lineEdit_integer.setValidator(QIntValidator())
        self.lineEdit_fraction.setValidator(QIntValidator())
        self.lineEdit_integer.setText('3')
        self.lineEdit_integer.setPlaceholderText('坐标整数位数')
        self.lineEdit_fraction.setText('3')
        self.lineEdit_fraction.setPlaceholderText('坐标小数位数')
        self.pushButton_switch_path.setIcon(qtawesome.icon('fa.chain', color='white'))
        self.pushButton_select_all.setIcon(qtawesome.icon('fa.reply-all', color='white'))
        self.pushButton_unselect.setIcon(qtawesome.icon('fa.undo', color='white'))
        self.pushButton_input.setIcon(qtawesome.icon('fa.download', color='white'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='white'))
        self.lineEdit_path.returnPressed.connect(self.search_files)
        self.pushButton_switch_path.clicked.connect(self.select_path)
        self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.pushButton_select_all.clicked.connect(lambda: self.listWidget.selectAll())
        self.pushButton_unselect.clicked.connect(lambda: self.listWidget.clearSelection())
        self.pushButton_input.clicked.connect(self.input)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        # self.move((app.desktop().width() - self.geometry().width())/2, (app.desktop().height() - self.geometry().height())/2)
        # self.setStyleSheet(
        #     '''QPushButton {background-color:#0081a6;color:white;} QPushButton:hover{background:black;}
        #     QListWidget{outline: 0px;border:0px;min-width: 200px;color:black;background:white;font:13px;}
        #     QListWidget::Item{height:22px;border-radius:1.5px;} QMessageBox{font-size:10pt;} QListWidget::Item:selected{background:#308CC6;color:white;}''')#background: #0081a6;
        self.setStyleSheet(
            '''QPushButton {background-color:#0081a6;color:white;} QPushButton:hover{background:black;}
            QListWidget{outline: 0px;border:0px;min-width: 200px;color:black;background:white;font:14px;}
            QComboBox{background:#0081a6;}
            QComboBox:hover,QListWidget::Item:hover{background:#F7D674; color:black;}
            QListWidget::Item{height:26px;border-radius:1.5px;} QMessageBox{font-size:10pt;} QListWidget::Item:selected{background:rgb(49,194,124);color:white;}''')#background: #0081a6;
        self.search_files()

    def select_path(self):
        path_dialog = QFileDialog()
        path_dialog.setOption(QFileDialog.DontUseNativeDialog, False)
        dir = path_dialog.getExistingDirectory(self, "选择路径", self.path)
        if dir:
            self.path = dir
            self.lineEdit_path.setText(self.path)
            # self.filename = self.filepath.split('/')[-1]
            self.search_files()

    def search_files(self):
        self.path = self.lineEdit_path.text()
        self.all_files.clear()
        self.listWidget.clear()
        self.get_files(self.path)
        self.listWidget.addItems(self.all_files)

    def get_files(self, p_path):
        for path in glob.glob(os.path.join(p_path, '*')):
            if os.path.isdir(path):
                self.get_files(path)
            else:
                if not re.match('(\.dwg|\.zip|\.rar|\.tgz)$',path):
                    self.all_files.append(path)

    def input(self):
        input_files = [item.text() for item in self.listWidget.selectedItems()]
        if not input_files:
            QMessageBox.warning(None, 'tips', '请选择要导入的文件')
            return
        nf1, nf2 = self.lineEdit_integer.text(), self.lineEdit_fraction.text()
        if not nf1 or not nf2:
            QMessageBox.warning(None, 'tips', '请输入坐标位数格式')
            return
        if nf1 == '0' or nf2 == '0':
            QMessageBox.warning(None, 'tips', '坐标位数必须大于0')
            return
        self.hide()
        stepname = self.comboBox_steps.currentText()
        step = job.steps.get(stepname)
        step.open()
        step.setGroup()
        for input_file in input_files:
            layer = input_file.rsplit('\\', 1)[-1]
            if input_file.endswith('.dxf'):
                step.COM('input_manual_reset')
                step.COM(f'input_manual_set,path={input_file},job={jobname},step={stepname},format=DXF,data_type=ascii,units=mm,coordinates=absolute,zeroes=none,nf1={nf1},nf2={nf2},decimal=no,separator=*,tool_units=inch,layer={layer},wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.06096,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3')
                step.COM('input_manual,script_path=')
            elif input_file.endswith('.gbr'):
                step.COM('input_manual_reset')
                step.COM(f'input_manual_set,path={input_file},job={jobname},step={stepname},format=Gerber274x,data_type=ascii,units=mm,coordinates=absolute,zeroes=none,nf1={nf1},nf2={nf2},decimal=no,separator=*,tool_units=inch,layer={layer},wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.06096,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3')
                step.COM('input_manual,script_path=')
            else:
                step.COM('input_manual_reset')
                step.COM(f'input_manual_set,path={input_file},job={jobname},step={stepname},format=Excellon2,data_type=ascii,units=mm,coordinates=absolute,zeroes=trailing,nf1={nf1},nf2={nf2},decimal=no,separator=nl,tool_units=mm,layer={layer},wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3')
                step.COM('input_manual,script_path=')
            step.COM('input_hide_page')
        job.matrix.refresh()
        QMessageBox.warning(None, 'tips', '导入成功')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    # app.setStyleSheet('*{font-family:"Liberation Serif";}QMessageBox{font-size:10pt;}')
    app.setWindowIcon(QIcon(":/res/demo.png"))
    if not os.environ.get('JOB'):
        QMessageBox.warning(None, 'tips', '请打开料号！')
        sys.exit()
    jobname = os.environ.get('JOB')
    stepname = os.environ.get('STEP')
    job = gen.Job(jobname)
    user = job.getUser()
    inputDxfTool = InputDxfTool()
    inputDxfTool.show()
    sys.exit(app.exec_())
