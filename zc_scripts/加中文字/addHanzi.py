#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:addHanzi.py
   @author:zl
   @time:2024/03/12 15:47
   @software:PyCharm
   @desc:
"""
import os
import sys

import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import addHanziUI as ui

sys.path.append('/genesis/sys/scripts/zl/lib')
import genClasses as gen
import res_rc


class AddHanzi(QWidget, ui.Ui_Form):
    def __init__(self):
        super(AddHanzi, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.jobname = os.environ.get('JOB')
        self.stepname = os.environ.get('STEP')
        if self.jobname:
            self.label_title.setText(f'Job：{self.jobname} Step：{self.stepname}')
        # 一页显示几个
        self.lineEdit_x.setText('2.64')
        self.lineEdit_y.setText('2.74')
        # self.lineEdit_line.setText('0.2')
        self.comboBox.addItems(['hzht.shx', 'hzfs.shx', 'hzst.shx', 'hzkt.shx'])
        self.lineEdit_x.setValidator(QDoubleValidator())
        self.lineEdit_y.setValidator(QDoubleValidator())
        # self.lineEdit_line.setValidator(QDoubleValidator())
        self.lineEdit_input.textChanged.connect(self.showHanzi)
        self.pushButton_add.clicked.connect(self.exec)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.pushButton_add.setIcon(qtawesome.icon('fa.download', color='white'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='white'))
        self.setStyleSheet(
            '''#pushButton_add,#pushButton_exit{background-color:#0081a6;color:white;} 
            #pushButton_add:hover,#pushButton_exit:hover{background:black;}''')
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

    def showHanzi(self):
        self.label_show.setText(self.lineEdit_input.text())

    def exec(self):
        if not self.label_show.text():
            QMessageBox.warning(self, 'tips', f'请选择文字!')
            return
        if not self.lineEdit_x.text() and not self.lineEdit_y.text() and not self.lineEdit_line.text():
            QMessageBox.warning(self, 'tips', f'请输入参数!')
            return
        if not self.stepname:
            QMessageBox.warning(self, 'tips', f'请打开step!')
            return
        self.hide()
        # w_factor = 0.00328083992 * float(self.lineEdit_line.text())
        # w_factor = float(self.lineEdit_line.text()) * 3
        fontname = self.comboBox.currentText()
        hanzi =self.lineEdit_input.text().strip()
        x_size = self.lineEdit_x.text()
        y_size = self.lineEdit_y.text()
        job = gen.Job(self.jobname)
        step = job.steps.get(self.stepname)
        # step.initStep()
        step.setUnits('mm')
        QMessageBox.information(self, 'tips', f'请点击要加的位置!')
        step.MOUSE('p select point add Chinese')
        mouseans = step.MOUSEANS
        ad_x1 = float('%.3f' % float(mouseans.split()[0]))
        ad_y1 = float('%.3f' % float(mouseans.split()[1]))
        step.COM('get_work_layer')
        workLay = step.COMANS
        step.COM('get_affect_layer')
        affectLays = step.COMANS.split()
        if not workLay and not affectLays:
            QMessageBox.information(None, 'tips', '没有选择一层工作层或影响层')
            self.show()
            return
        # 临时层
        tmp_layer = 'hanzi+++' + str(job.pid)
        step.createLayer(tmp_layer)
        step.clearAll()
        step.affect(tmp_layer)
        step.COM(f'add_text,mirror=no,bar_char_set=full_ascii,fontname={fontname},x={ad_x1},bar_type=UPC39,bar_height=0.178,y={ad_y1},text={hanzi},bar_width=0.008,y_size={y_size},ver=1,x_size={x_size},angle=0,bar_add_string_pos=top,bar_add_string=yes,w_factor=0.6,bar_background=yes,polarity=positive,type=string,attributes=no')
        step.selectBreak()
        step.selectCutData()
        if workLay:
            step.copyToLayer(workLay)
        if affectLays:
            for layer in affectLays:
                step.copyToLayer(layer)
        step.unaffectAll()
        step.removeLayer(tmp_layer)
        step.removeLayer(f'{tmp_layer}+++')
        if workLay:
            step.display(workLay)
        if affectLays:
            for layer in affectLays:
                step.affect(layer)
        QMessageBox.information(None, 'tips', '添加成功！')
        sys.exit()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setStyleSheet('*{font-family:"微软雅黑";}')
    app.setWindowIcon(QIcon(":/res/demo.png"))
    addHanzi = AddHanzi()
    addHanzi.show()
    sys.exit(app.exec_())
