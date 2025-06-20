#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:RoutInput.py
   @author:zl
   @time: 2024/12/19 9:16
   @software:PyCharm
   @desc:
"""
import os
import re
import sys, platform

reload(sys)
sys.setdefaultencoding('utf8')
from PyQt4.QtCore import *
from PyQt4.QtGui import *

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen
import RoutInputUI_pyqt4 as ui


class RoutInput(QWidget, ui.Ui_Form):
    def __init__(self):
        super(RoutInput, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.jobname = os.environ.get("JOB")
        self.job = gen.Job(self.jobname)
        steps = self.job.stepsList
        self.comboBox.addItems(steps)
        stepname = os.environ.get("STEP")
        if stepname:
            idex = list(filter(lambda i: steps[i] == stepname, range(len(steps))))[0] if list(filter(lambda i: steps[i] == stepname, range(len(steps)))) else -1
            self.comboBox.setCurrentIndex(idex)
        self.label_title.setText('Job:%s' % self.jobname)
        self.setStyleSheet(
            '''#pushButton_exec,#pushButton_exit{font:11pt;background-color:#0081a6;color:white;} #pushButton_exec:hover,#pushButton_exit:hover{background:black;color:white;}''')
        self.set_path()
        self.load_list()
        self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.lineEdit_path.returnPressed.connect(self.load_list)
        self.pushButton_path.clicked.connect(self.select_path)
        self.pushButton_exec.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.checkBox_select_all.clicked.connect(self.check_all)

    def set_path(self):
        if sys.platform == "win32":
            self.get_para_path = ur"\\192.168.2.172\GCfiles\锣带备份\锣带备份".format(self.jobname[1:4].upper(),
                                                                                      self.jobname.split('-')[
                                                                                          0].upper(),
                                                                                      self.jobname.split('-')[0][
                                                                                      -2:].upper())
        else:
            self.get_para_path = u"/windows/172.file/锣带备份/锣带备份/{0}系列/{1}/".format(self.jobname[1:4].upper(),
                                                                                            self.jobname.split('-')[
                                                                                                0].upper())
            # self.get_para_path = u"/id/workfile/hdi_film/{0}".format(self.jobname.split('-')[0])
        self.lineEdit_path.setText(self.get_para_path)

    def select_path(self):
        directory = QFileDialog.getExistingDirectory(self, u"选择文件夹", self.get_para_path, QFileDialog.ShowDirsOnly)
        if directory:
            self.lineEdit_path.setText(directory)
            self.load_list()

    def check_all(self):
        if self.checkBox_select_all.isChecked():
            self.listWidget.selectAll()
        else:
            self.listWidget.clearSelection()

    def load_list(self):
        self.listWidget.clear()
        self.checkBox_select_all.setChecked(False)
        file_path = str(self.lineEdit_path.text())
        if not os.path.exists(file_path):
            QMessageBox.warning(None, u'提示', u'路径%s不存在' % str(self.lineEdit_path.text()))
            return
        files = filter(lambda x: os.path.isfile(os.path.join(file_path, x)), os.listdir(file_path))
        rout_layers = []
        for file in files:
            if file.endswith('.rout'):
                rout_layers.append(file)
        self.listWidget.addItems(rout_layers)

    def run(self):
        if not self.listWidget.selectedItems():
            QMessageBox.warning(None, u'警告', u'请选择层！')
            return
        stepname = self.comboBox.currentText()
        self.step = gen.Step(self.job, stepname)
        self.step.initStep()
        layers = [str(item.text()) for item in self.listWidget.selectedItems()]
        for layer in layers:
            self.step.COM('input_manual_reset')
            self.step.COM(
                'input_manual_set,path=%s,job=%s,step=%s,format=Excellon2,data_type=ascii,units=mm,coordinates=absolute,zeroes=trailing,nf1=3,nf2=3,decimal=no,separator=nl,tool_units=mm,layer=%s,wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3' % (
                    os.path.join(str(self.lineEdit_path.text()), layer), self.jobname, self.step.name, layer))
            self.step.COM('input_manual,script_path=')
            self.step.clearAll()
        QMessageBox.information(None, u'提示', u'导入完成！')
        sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    app.setStyleSheet('QPushButton:hover{background:black;color:white;}')
    routInput = RoutInput()
    routInput.show()
    sys.exit(app.exec_())
