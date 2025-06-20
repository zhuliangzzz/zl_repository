#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:RoutInput.py
   @author:zl
   @time: 2024/12/19 9:16
   @software:PyCharm
   @desc:
   读取tgz导入
"""
import os
import re
import shutil
import sys, platform

reload(sys)
sys.setdefaultencoding('utf8')
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import RoutInputUI_pyqt4 as ui
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen
from genesisPackages_zl import get_profile_limits, get_sr_area_for_step_include, get_layer_selected_limits, signalLayers

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
        if 'panel' in steps:
            stepname = 'panel'
        elif 'set' in steps:
            stepname = 'set'
        else:
            stepname = steps[0]
        if stepname:
            idex = list(filter(lambda i: steps[i] == stepname, range(len(steps))))[0] if list(filter(lambda i: steps[i] == stepname, range(len(steps)))) else -1
            self.comboBox.setCurrentIndex(idex)
        self.label_title.setText('Job:%s' % self.jobname)
        self.setStyleSheet(
            '''#pushButton_exec,#pushButton_exit{font:11pt;background-color:#0081a6;color:white;} #pushButton_exec:hover,#pushButton_exit:hover{background:black;color:white;}''')
        self.set_path()
        self.load_list()
        # self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
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
        tgzs = []
        for file in files:
            if file.endswith('.tgz'):
                tgzs.append(file)
        self.listWidget.addItems(tgzs)

    def run(self):
        if not self.listWidget.selectedItems():
            QMessageBox.warning(None, u'警告', u'请选择要导入的tgz！')
            return
        import_jobname = str(self.listWidget.selectedItems()[0].text())
        stepname = self.comboBox.currentText()
        gen_top = gen.Top()
        if import_jobname in gen_top.listJobs():
            gen_top.deleteJob(import_jobname)
        gen_top.COM(
            'import_job,db=db1,path=%s,name=%s' % (os.path.join(str(self.lineEdit_path.text()), import_jobname), import_jobname))
        import_job = gen.Job(import_jobname)
        layers = import_job.matrix.returnRows()
        rout_layers = filter(lambda layer: re.match('jp-rout$|ccd-rout$|ccd-half-rout$|ccd-pth-rout$|ccd-mid-rout$|rout$|rout-fb$|half-rout$|rout-cd(c|s)$|ccd-rout-cd(c|s)$|pth-rout$|mid-rout$|(rout)(\d)|([a-z].*)-rout?|rout-([a-z].*)?', layer), layers)
        ref_rrr_layers = []
        for rout_layer in rout_layers:
            if re.match('ccd-rout$', rout_layer):
                ref_rrr_layers.append('rrr-ccd')
            elif re.match('ccd-half-rout$', rout_layer):
                ref_rrr_layers.append('ccd-rrr-half')
            elif re.match('ccd-pth-rout$', rout_layer):
                ref_rrr_layers.append('ccd-rrr-pth')
            elif re.match('ccd-mid-rout$', rout_layer):
                ref_rrr_layers.append('ccd-rrr-mid')
            elif re.match('rout$|rout-fb$', rout_layer):
                ref_rrr_layers.append('rrr')
            elif re.match('half-rout$', rout_layer):
                ref_rrr_layers.append('rrr-half')
            elif re.match('rout-cd(c|s)$', rout_layer):
                ref_rrr_layers.append('rrr-cd%s' % re.match('rout-cd(c|s)$', rout_layer).group(1))
            elif re.match('ccd-rout-cd(c|s)$', rout_layer):
                ref_rrr_layers.append('ccd-rrr-cd%s' % re.match('ccd-rout-cd(c|s)$', rout_layer).group(1))
            elif re.match('pth-rout$', rout_layer):
                ref_rrr_layers.append('rrr-pth')
            elif re.match('mid-rout$', rout_layer):
                ref_rrr_layers.append('rrr-mid')
            elif re.match('rout(\d)', rout_layer):
                ref_rrr_layers.append('rrr%s' % re.match('rout(\d)', rout_layer).group(1))
            elif re.match('([a-z].*)-rout?', rout_layer):
                ref_rrr_layers.append('rrr-%s' % re.match('([a-z].*)-rout?', rout_layer).group(1))
            elif re.match('rout-([a-z].*)?', rout_layer):
                ref_rrr_layers.append('rrr-%s' % re.match('rout-([a-z].*)?', rout_layer).group(1))
        ref_rrr_layers = sorted(list(set(list(filter(lambda rrr: rrr in layers, ref_rrr_layers)))))
        self.step = gen.Step(self.job, stepname)
        self.step.initStep()
        if rout_layers:
            rout_layers.extend(ref_rrr_layers)
            for layer in rout_layers:
                # 备份
                bk_layer = '%s_bak' % layer
                self.step.removeLayer(bk_layer)
                if self.step.isLayer(layer):
                    self.step.affect(layer)
                    self.step.copySel(bk_layer)
                    self.step.unaffectAll()
                self.step.copyLayer(import_jobname, stepname, layer, layer, 'append')
                # else:
                #     self.step.createLayer(layer)
                #     self.step.copyLayer(import_jobname, stepname, layer, layer)
        import_job.close(1)
        gen_top.deleteJob(import_jobname)
        if rout_layers:
            QMessageBox.information(None, u'提示', u'导入完成！\n导入的层：%s' % '、'.join(rout_layers))
        else:
            QMessageBox.information(None, u'提示', u'没有要导入的锣带和外形层！')
        sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    app.setStyleSheet('QPushButton:hover{background:black;color:white;}')
    routInput = RoutInput()
    routInput.show()
    sys.exit(app.exec_())
