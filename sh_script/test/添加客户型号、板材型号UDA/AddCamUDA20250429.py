#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AddCamUDA.py
   @author:zl
   @time: 2025/3/26 11:12
   @software:PyCharm
   @desc:
"""
import os
import platform
import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import AddCamUDA_UI_pyqt4 as ui


if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen
import connect_database_all as incam_tool

class AddCamUDA(QWidget, ui.Ui_Form):
    def __init__(self):
        super(AddCamUDA, self).__init__()
        self.setupUi(self)
        self.render()

    def __getattr__(self, item):
        if item == 'customer_jobname':
            self.customer_jobname = self.get_customer_jobname()
            return self.customer_jobname
        if item == 'pp_type':
            self.pp_type = self.get_pp_type()
            return self.pp_type

    def render(self):
        self.label_job.setText('<b>Job:%s</b>' % jobname)
        self.label_8.setText('<b>Step:</b>')
        self.lineEdit_attr.setText('.string=customer_jobname')
        self.lineEdit_attr_2.setText('.string=board_jobname')
        self.lineEdit_xSize.setValidator(QDoubleValidator(self.lineEdit_xSize))
        self.lineEdit_ySize.setValidator(QDoubleValidator(self.lineEdit_ySize))
        self.lineEdit_lineWidth.setValidator(QDoubleValidator(self.lineEdit_lineWidth))
        self.fonts = ['simple', 'simplex', 'standard', 'SimSun']
        self.comboBox_fonts.addItems(self.fonts)
        self.comboBox_step_selector.addItems(job.stepsList)
        currentIndex = 0
        for i, step in enumerate(job.stepsList):
            if 'edit' in step:
                currentIndex = i
                break
        self.comboBox_step_selector.setCurrentIndex(currentIndex)
        self.lineEdit_xSize.setText('0.7')
        self.lineEdit_ySize.setText('0.9')
        self.lineEdit_lineWidth.setText('0.15')
        self.lineEdit_attr.setReadOnly(True)
        self.checkBox.setChecked(True)
        self.pushButton_exec.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            '''
            QPushButton{font:10pt;background-color:#459B81;color:white;} QPushButton:hover{background:#333;} #QCheckBox::indicator:checked{background:#459B81;}''')
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)
        self.load_info()

    def load_info(self):
        self.lineEdit_val.setText(self.customer_jobname)
        self.lineEdit_val_2.setText(self.pp_type.decode('utf8'))

    def get_customer_jobname(self):
        customer = incam_tool.InPlan(jobname).get_job_customer()
        return customer

    def get_pp_type(self):
        pptype = incam_tool.InPlan(jobname).get_pp_type()
        return pptype

    def run(self):
        stepname = self.comboBox_step_selector.currentText()
        step = gen.Step(job, stepname)
        custom_code = str(self.lineEdit_val.text())
        attr_name, attr_val = str(self.lineEdit_attr.text()).split('=')
        pp_type = str(self.lineEdit_val_2.text())
        attr2_name, attr2_val = str(self.lineEdit_attr_2.text()).split('=')
        step.COM('get_work_layer')
        workLay = step.COMANS
        # step.COM('get_affect_layer')
        # affectLays = step.COMANS.split()
        add_layers = []
        if workLay:
            add_layers.append(workLay)
        # if affectLays:
        #     add_layers.extend(affectLays)
        # if not add_layers:
        #     QMessageBox.warning(self, u'警告', u'请打开工作层或影响层')
        #     sys.exit()
        if not add_layers:
            QMessageBox.warning(self, u'警告', u'请先打开工作层')
            sys.exit()
        if not self.checkBox.isChecked() and not self.checkBox_2.isChecked():
            QMessageBox.warning(self, u'警告', u'请勾选要加的信息')
            return
        xsize = float(self.lineEdit_xSize.text())
        ysize = float(self.lineEdit_ySize.text())
        width = float(self.lineEdit_lineWidth.text())
        font = str(self.comboBox_fonts.currentText())
        step.initStep()
        self.hide()
        if self.checkBox.isChecked():  # 客户型号
            step.display(add_layers[0])
            step.MOUSE('点击选择添加客户型号位置')
            x, y = step.MOUSEANS.split()
            x, y = float(x), float(y)
            step.clearAll()
            for add_layer in add_layers:
                step.affect(add_layer)
            step.addAttr_zl('%s,text=%s' % (attr_name, attr_val))
            step.addText(x, y, custom_code, xsize, ysize, width / 0.3048, fontname=font, attributes='yes')
            step.unaffectAll()
            step.resetAttr()
        if self.checkBox_2.isChecked():  # 板材型号
            step.display(add_layers[0])
            step.MOUSE('点击选择添加板材型号位置')
            x, y = step.MOUSEANS.split()
            x, y = float(x), float(y)
            step.clearAll()
            for add_layer in add_layers:
                step.affect(add_layer)
            step.addAttr_zl('%s,text=%s' % (attr2_name, attr2_val))
            step.addText(x, y, pp_type.replace(',', ''), xsize, ysize, width / 0.3048, fontname=font, attributes='yes')
            step.unaffectAll()
            step.resetAttr()
        # if
        QMessageBox.information(self, 'tips', u'添加完成~')
        sys.exit()


if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    if not jobname:
        QMessageBox.warning(None, 'tips', u'请打开料号执行~')
        sys.exit()
    app = QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    acu = AddCamUDA()
    acu.show()
    sys.exit(app.exec_())
