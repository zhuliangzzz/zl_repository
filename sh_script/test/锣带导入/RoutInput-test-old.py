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
import copy
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
        self.rout_layers = []
        if not self.listWidget.selectedItems():
            QMessageBox.warning(None, u'警告', u'请选择要导入的tgz！')
            return
        tgz = str(self.listWidget.selectedItems()[0].text())
        self.import_jobname = tgz.rsplit('.tgz', 1)[0] + '-rout'
        # stepname = self.comboBox.currentText()
        gen_top = gen.Top()
        if self.import_jobname in gen_top.listJobs():
            gen_top.deleteJob(self.import_jobname)
        gen_top.COM(
            'import_job,db=db1,path=%s,name=%s' % (os.path.join(str(self.lineEdit_path.text()), tgz), self.import_jobname))
        self.import_job = gen.Job(self.import_jobname)
        alert_layer_window(self)
        print(self.rout_layers)
        steplist = self.job.stepsList
        for stepname in steplist:
            if stepname not in self.import_job.stepsList:
                continue
            self.step = gen.Step(self.job, stepname)
            self.step.initStep()
            for layer in self.rout_layers:
                # 备份
                bk_layer = '%s_bak' % layer
                # self.step.removeLayer(bk_layer)
                if self.step.isLayer(layer):
                    self.step.affect(layer)
                    self.step.copySel(bk_layer)
                    self.step.unaffectAll()
                self.step.copyLayer(self.import_jobname, stepname, layer, layer, 'append')
                # else:
                #     self.step.createLayer(layer)
                #     self.step.copyLayer(import_jobname, stepname, layer, layer)
        self.import_job.close(1)
        gen_top.deleteJob(self.import_jobname)
        for layer in self.rout_layers:
            self.job.matrix.modifyRow(layer, type='rout')
        if self.rout_layers:
            QMessageBox.information(None, u'提示', u'导入完成！\n导入的层：%s' % '、'.join(self.rout_layers))
        else:
            QMessageBox.information(None, u'提示', u'没有要导入的锣带和外形层！')
        sys.exit()


class alert_layer_window(QDialog):
    def __init__(self, parent):
        super(alert_layer_window, self).__init__(parent)
        self.render()
        self.exec_()

    def render(self):
        self.setWindowTitle('Layer Selector')
        self.resize(200, 240)
        layout = QVBoxLayout(self)
        # combo = QComboBox(self)
        self.tree = QTreeWidget()
        # 设置列数
        self.tree.setColumnCount(1)
        # 设置树形控件头部的标题
        self.tree.setHeaderLabels(['Layers'])

        # 设置根节点
        self.root = QTreeWidgetItem(self.tree)
        self.root.setText(0, 'All')
        # root.setIcon(0, QIcon('./images/root.png'))

        # todo 优化2 设置根节点的背景颜色
        # 设置树形控件的列的宽度
        self.tree.setColumnWidth(0, 120)
        # 设置子节点
        # all_lays = routInput.import_job.matrix.returnRows()
        rout_lays = routInput.import_job.matrix.returnRows('board', 'rout')
        if rout_lays:
            signal_Node = QTreeWidgetItem(self.root)
            signal_Node.setText(0, u'锣带层')
            signal_Node.setCheckState(0, Qt.Unchecked)
            for layer in rout_lays:
                item = QTreeWidgetItem()
                item.setText(0, str(layer))
                # item.setIcon(0, QIcon('images/signal.png'))
                item.setCheckState(0, Qt.Unchecked)
                signal_Node.addChild(item)

        # 加载根节点的所有属性与子控件
        self.root.setCheckState(0, Qt.Unchecked)
        self.tree.addTopLevelItem(self.root)

        # TODO 优化3 给节点添加响应事件
        self.tree.clicked.connect(self.onClicked)

        # 节点全部展开
        self.tree.expandAll()
        layout.addWidget(self.tree)
        btn_box = QHBoxLayout()
        ok = QPushButton(self)
        ok.setText('OK')
        ok.setStyleSheet('background-color:#0081a6;color:white;')
        ok.setObjectName('dialog_ok')
        ok.setCursor(QCursor(Qt.PointingHandCursor))
        ok.clicked.connect(self.generate_layerstr)
        close = QPushButton(self)
        close.setText('Close')
        close.setStyleSheet('background-color:#464646;color:white;')
        close.setObjectName('dialog_close')
        close.setCursor(QCursor(Qt.PointingHandCursor))
        close.clicked.connect(lambda: self.close())
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_box.addItem(spacerItem1)
        btn_box.addWidget(ok)
        btn_box.addWidget(close)
        layout.addLayout(btn_box)
        self.setStyleSheet('QPushButton{font-family:黑体;font-size:10pt;}')

    def onClicked(self, qmodeLindex):
        # print(qmodeLindex.data())
        count = self.tree.topLevelItemCount()
        for index in range(count):
            item = self.tree.topLevelItem(index)
            # 判断根节点
            if item.text(0) == qmodeLindex.data():
                if item.checkState(0) == 0:
                    for i in range(item.childCount()):
                        child = item.child(i)
                        # if child.checkState(0) == 0:
                        #     child.setCheckState(0, Qt.Checked)
                        # else:
                        child.setCheckState(0, Qt.Unchecked)

                        for j in range(child.childCount()):
                            sub_child = child.child(j)
                            # if sub_child.checkState(0) == 0:
                            #     sub_child.setCheckState(0, Qt.Checked)
                            # else:
                            sub_child.setCheckState(0, Qt.Unchecked)
                    break
                else:
                    for i in range(item.childCount()):
                        child = item.child(i)
                        # if child.checkState(0) == 0:
                        child.setCheckState(0, Qt.Checked)
                        # else:
                        #     child.setCheckState(0, Qt.Unchecked)

                        for j in range(child.childCount()):
                            sub_child = child.child(j)
                            # if sub_child.checkState(0) == 0:
                            sub_child.setCheckState(0, Qt.Checked)
                            # else:
                            #     sub_child.setCheckState(0, Qt.Unchecked)
                    break
            for i in range(item.childCount()):
                child = item.child(i)
                if qmodeLindex.data() == child.text(0):
                    if child.checkState(0) == 0:
                        for i in range(child.childCount()):
                            chi = child.child(i)
                            chi.setCheckState(0, Qt.Unchecked)
                    else:
                        for i in range(child.childCount()):
                            chi = child.child(i)
                            chi.setCheckState(0, Qt.Checked)
            break

    def generate_layerstr(self):
        # 取到选择的layers
        # print('generate layerstr')
        count = self.tree.topLevelItemCount()
        select_lay = []
        for index in range(count):
            item = self.tree.topLevelItem(index)
            for i in range(item.childCount()):
                child = item.child(i)
                for j in range(child.childCount()):
                    chi = child.child(j)
                    if chi.checkState(0) == 2:
                        select_lay.append(str(chi.text(0)))
        # print(select_lay)
        # print(len(select_lay))
        routInput.rout_layers.extend(select_lay)
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    app.setStyleSheet('QPushButton:hover{background:black;color:white;}')
    routInput = RoutInput()
    routInput.show()
    sys.exit(app.exec_())
