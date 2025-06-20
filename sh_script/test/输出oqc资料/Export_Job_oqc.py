#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:Export_Job_oqc.py
   @author:zl
   @time: 2024/12/18 11:30
   @software:PyCharm
   @desc:
"""
import copy
import os
import sys
from PyQt4 import QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *
# from PyQt4.QtCore import Qt
# from PyQt4.QtGui import QIcon, QCursor, QColor, QPainter, QWidget, QApplication, QTreeWidgetItem, QVBoxLayout, QTreeWidget, QDialog, QHBoxLayout, \
#     QPushButton, QSpacerItem, QSizePolicy

import Export_JobUI_pyqt4 as ui
import platform
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen



class Export_Job(QWidget, ui.Ui_Form):
    def __init__(self):
        super(Export_Job, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        system = platform.system()
        if system == 'Linux':
            self.export_path = "/id/workfile/hdi_film/%s" % jobname
        else:
            self.export_path = "D:/disk/film/%s" % jobname
        # oqc
        self.oqc_steps = list(filter(lambda stepname: 'panel' not in stepname, job.stepsList))
        if not self.oqc_steps:
            QMessageBox.information(None, u'提示', u'%s没有step!' % jobname)
            sys.exit()
        self.setWindowFlags(Qt.WindowMinMaxButtonsHint)
        # self.output_type = 'full'
        self.output_type = 'partial'
        mode = ['Include', 'Exclude']
        self.comboBox_step.addItems(['Include'])
        self.comboBox_layer.addItems(mode)
        self.lineEdit_jobname.setText(jobname)
        self.lineEdit_export_path.setText(self.export_path)
        self.lineEdit_mode.setText('Tar/gzip(.tgz)')
        # self.radioButton.clicked.connect(self.check_type)
        # self.radioButton_2.clicked.connect(self.check_type)
        self.pushButton_select_steps.clicked.connect(lambda: self.filter(1))
        self.pushButton_select_layers.clicked.connect(lambda: self.filter(2))
        self.widget.setVisible(True)
        self.radioButton.setVisible(False)
        self.radioButton_2.setChecked(True)
        # self.resize(320, 3)
        self.setStyleSheet(
            '#pushButton_select_steps,#pushButton_select_layers{padding:2px;background-color:#464646;color:white;}#pushButton_ok{background-color:#0081a6;color:white;}#pushButton_cancel{background-color:#464646;color:white;} '
            'QToolTip{background-color:#cecece;}#pushButton_ok:hover,#pushButton_cancel:hover{background:#882F09;}QMessageBox{font:10pt;}')
        self.pushButton_ok.clicked.connect(self.export)
        # self.pushButton_cancel.clicked.connect(lambda: sys.exit())

    # def check_type(self):
    #     if self.radioButton.isChecked():
    #         self.output_type = 'full'
    #         self.widget.setVisible(False)
    #     else:
    #         self.output_type = 'partial'
    #         self.widget.setVisible(True)
    def export(self):
        if self.output_type == 'full':
            job.COM('export_job,job=%s,path=%s,mode=tar_gzip,submode=full,overwrite=yes' % (jobname, self.export_path))
        else:
            steps_mode = self.comboBox_step.currentText()
            layer_mode = self.comboBox_layer.currentText()
            steps, lyrs = str(self.lineEdit_steps.text()).strip(), str(self.lineEdit_layers.text()).strip()
            if lyrs:
                # 判断step和layer是否手输错误
                err_lyr = filter(lambda x: x not in job.matrix.returnRows(), lyrs.split(';'))
                if err_lyr:
                    QMessageBox.warning(self, u'提示', u'请检查要输出的层名是否有误')
                    return
            if steps:
                err_step = filter(lambda x: x not in ex.oqc_steps, steps.split(';'))
                if err_step:
                    QMessageBox.warning(self, u'提示', u'请检查要输出的step是否有误')
                    return
            else:
                QMessageBox.warning(self, u'提示', u'请选择要输出的step')
                return
            if not os.path.exists(self.export_path):
                os.makedirs(self.export_path)
            job.COM('export_job,job=%s,path=%s,mode=tar_gzip,submode=partial,steps_mode=%s,steps=%s,lyrs_mode=%s,lyrs=%s,overwrite=yes'
                    % (jobname, self.export_path, steps_mode, steps, layer_mode, lyrs))
        QMessageBox.information(self, u'提示', u'输出完成！')
        sys.exit()

    def filter(self, flag):
        if flag == 1:
            alert_step_window(self)
        else:
            alert_layer_window(self)
class alert_step_window(QDialog):
    def __init__(self, parent):
        super(alert_step_window, self).__init__(parent)
        self.render()
        self.exec_()

    def render(self):
        self.setWindowTitle('Step Filter')
        self.resize(200, 240)
        layout = QVBoxLayout(self)
        # combo = QComboBox(self)
        self.tree = QTreeWidget()
        # 设置列数
        self.tree.setColumnCount(1)
        # 设置树形控件头部的标题
        self.tree.setHeaderLabels(['Steps'])

        # 设置根节点
        self.root = QTreeWidgetItem(self.tree)
        self.root.setText(0, 'All')
        # root.setIcon(0, QIcon('./images/root.png'))

        # todo 优化2 设置根节点的背景颜色
        # 设置树形控件的列的宽度
        self.tree.setColumnWidth(0, 120)
        # 设置子节点
        # all_lays = job.matrix.returnRows()
        # signal_lays = job.matrix.returnRows('board', 'signal|power_ground')
        steps = ex.oqc_steps
        if steps:
            for step in steps:
                item = QTreeWidgetItem(self.root)
                item.setText(0, step)
                item.setCheckState(0, Qt.Unchecked)
                # item.setIcon(0, QIcon('images/other.png'))


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
        ok.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        ok.clicked.connect(self.generate_stepstr)
        close = QPushButton(self)
        close.setText('Close')
        close.setStyleSheet('background-color:#464646;color:white;')
        close.setObjectName('dialog_close')
        close.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
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

    def generate_stepstr(self):
        # 取到选择的steps
        count = self.tree.topLevelItemCount()
        select_step = []
        for index in range(count):
            item = self.tree.topLevelItem(index)
            for i in range(item.childCount()):
                child = item.child(i)
                if child.checkState(0) == 2:
                    select_step.append(str(child.text(0)))
        layer_str = ';'.join(select_step)
        ex.lineEdit_steps.setText(layer_str)
        self.close()

class alert_layer_window(QDialog):
    def __init__(self, parent):
        super(alert_layer_window, self).__init__(parent)
        self.render()
        self.exec_()

    def render(self):
        self.setWindowTitle('Layer Filter')
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
        all_lays = job.matrix.returnRows()
        signal_lays = job.matrix.returnRows('board')
        if signal_lays:
            signal_Node = QTreeWidgetItem(self.root)
            signal_Node.setText(0, 'Board')
            signal_Node.setCheckState(0, Qt.Unchecked)
            for layer in signal_lays:
                item = QTreeWidgetItem()
                item.setText(0, str(layer))
                # item.setIcon(0, QIcon('images/signal.png'))
                item.setCheckState(0, Qt.Unchecked)
                signal_Node.addChild(item)
        copy_lays = copy.copy(all_lays)
        for lay in copy_lays:
            if lay in signal_lays:
                all_lays.remove(lay)
        if all_lays:
            other_Node = QTreeWidgetItem(self.root)
            other_Node.setText(0, 'Other')
            other_Node.setCheckState(0, Qt.Unchecked)
            for layer in all_lays:
                item = QTreeWidgetItem()
                item.setText(0, str(layer))
                item.setIcon(0, QIcon('images/other.png'))
                item.setCheckState(0, Qt.Unchecked)
                other_Node.addChild(item)

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
        ok.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        ok.clicked.connect(self.generate_layerstr)
        close = QPushButton(self)
        close.setText('Close')
        close.setStyleSheet('background-color:#464646;color:white;')
        close.setObjectName('dialog_close')
        close.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
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
        layer_str = ';'.join(select_lay)
        ex.lineEdit_layers.setText(layer_str)
        self.close()


if __name__ == '__main__':
    # jobname = sys.argv[1]
    # export_path = sys.argv[2]
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    app = QApplication(sys.argv)
    info = job.DO_INFO('-t job -e %s -d IS_CHANGED' % jobname)
    if info.get('gIS_CHANGED') == 'yes':
        QMessageBox.information(None, u'提示', u'料号 %s 未保存，请先保存!' % jobname)
        sys.exit()
    #
    ex = Export_Job()
    ex.show()
    sys.exit(app.exec_())
