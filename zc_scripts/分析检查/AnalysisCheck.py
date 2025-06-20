#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AnalysisCheck.py
   @author:zl
   @time:2023/10/31 15:58
   @software:PyCharm
   @desc:
"""
import copy
import os
import sys

import qtawesome
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import AnalysisCheckUI as ui

sys.path.append('/genesis/sys/scripts/zl/lib')
import genClasses as gen
import res_rc


class AnalysisCheck(QMainWindow, ui.Ui_MainWindow):
    def __init__(self):
        super(AnalysisCheck, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.title.setText(f'JOB:{jobname} Step:{stepname}')
        self.checkBox.setCheckState(Qt.PartiallyChecked)
        self.checkBox_2.setCheckState(Qt.PartiallyChecked)
        self.checkBox_3.setCheckState(Qt.PartiallyChecked)
        self.checkBox_4.setCheckState(Qt.PartiallyChecked)
        self.checkBox_5.setCheckState(Qt.PartiallyChecked)
        self.checkBox_6.setCheckState(Qt.PartiallyChecked)
        self.checkBox_7.setCheckState(Qt.PartiallyChecked)
        self.checkBox_9.setCheckState(Qt.PartiallyChecked)
        self.lineEdit.setValidator(QDoubleValidator())
        self.lineEdit.setText('254')
        self.lineEdit_2.setValidator(QDoubleValidator())
        self.lineEdit_2.setText('635')
        self.lineEdit_3.setValidator(QDoubleValidator())
        self.lineEdit_3.setText('355.6')
        self.lineEdit_4.setValidator(QDoubleValidator())
        self.lineEdit_4.setText('254')
        self.lineEdit_5.setValidator(QDoubleValidator())
        self.lineEdit_5.setText('127')
        self.layers_label.setText('.type=signal|mixed&side=top|bottom')  # 线路分析默认值
        self.signal_check_name.setText(f'{user}_script_signal_check')
        self.signal_check_name.setReadOnly(True)
        self.signal_layer_btn.setIcon(qtawesome.icon('fa.search', scale_factor=1, color='white'))
        self.view_check_btn.setIcon(qtawesome.icon('fa.eye', scale_factor=1, color='white'))
        # self.pushButton.setIcon(qtawesome.icon('fa.search', scale_factor=1, color='white'))
        self.pushButton_2.setIcon(qtawesome.icon('fa.blind', scale_factor=1, color='white'))
        self.pushButton_3.setIcon(qtawesome.icon('fa.square', scale_factor=1, color='white'))
        self.signal_layer_btn.clicked.connect(self.alert_layer_win)
        self.view_check_btn.clicked.connect(self.view_check)
        self.pushButton.clicked.connect(lambda: self.run('global'))
        self.pushButton_2.clicked.connect(lambda: self.run('local'))
        self.pushButton_3.clicked.connect(lambda: self.run('profile'))
        # solder_mask
        self.checkBox_10.setCheckState(Qt.PartiallyChecked)
        self.checkBox_11.setCheckState(Qt.PartiallyChecked)
        self.checkBox_12.setCheckState(Qt.PartiallyChecked)
        self.checkBox_13.setCheckState(Qt.PartiallyChecked)
        self.checkBox_14.setCheckState(Qt.PartiallyChecked)
        self.checkBox_15.setCheckState(Qt.PartiallyChecked)
        self.checkBox_16.setCheckState(Qt.PartiallyChecked)
        self.checkBox_17.setCheckState(Qt.PartiallyChecked)
        self.checkBox_19.setCheckState(Qt.PartiallyChecked)
        self.lineEdit_6.setValidator(QDoubleValidator())
        self.lineEdit_6.setText('355.6')
        self.lineEdit_7.setValidator(QDoubleValidator())
        self.lineEdit_7.setText('203.2')
        self.lineEdit_8.setValidator(QDoubleValidator())
        self.lineEdit_8.setText('406.4')
        self.lineEdit_9.setValidator(QDoubleValidator())
        self.lineEdit_9.setText('203.2')
        self.lineEdit_10.setValidator(QDoubleValidator())
        self.lineEdit_10.setText('228.6')
        self.lineEdit_11.setValidator(QDoubleValidator())
        self.lineEdit_11.setText('355.6')
        self.lineEdit_12.setValidator(QDoubleValidator())
        self.lineEdit_12.setText('127')
        self.layers_label_2.setText('.type=solder_mask&context=board')  # 初始值
        self.signal_check_name_2.setText(f'{user}_script_soldermask_check')
        self.signal_check_name_2.setReadOnly(True)
        self.signal_layer_btn_2.setIcon(qtawesome.icon('fa.search', scale_factor=1, color='white'))
        self.view_check_btn_2.setIcon(qtawesome.icon('fa.eye', scale_factor=1, color='white'))
        self.pushButton_5.setIcon(qtawesome.icon('fa.blind', scale_factor=1, color='white'))
        self.pushButton_6.setIcon(qtawesome.icon('fa.square', scale_factor=1, color='white'))
        self.close_btn.setIcon(qtawesome.icon('fa.sign-out', scale_factor=1))
        self.signal_layer_btn_2.clicked.connect(self.alert_layer_win_2)
        self.view_check_btn_2.clicked.connect(self.view_check)
        self.pushButton_4.clicked.connect(lambda: self.run('global'))
        self.pushButton_5.clicked.connect(lambda: self.run('local'))
        self.pushButton_6.clicked.connect(lambda: self.run('profile'))
        # silkscreen
        self.checkBox_20.setCheckState(Qt.PartiallyChecked)
        self.checkBox_22.setCheckState(Qt.PartiallyChecked)
        self.checkBox_23.setCheckState(Qt.PartiallyChecked)
        self.checkBox_24.setCheckState(Qt.PartiallyChecked)
        self.checkBox_26.setCheckState(Qt.PartiallyChecked)
        self.lineEdit_13.setValidator(QDoubleValidator())
        self.lineEdit_13.setText('355.6')
        self.layers_label_3.setText('.type=silk_screen&context=board')  # 初始值
        self.signal_check_name_3.setText(f'{user}_script_silkscreen_check')
        self.signal_check_name_3.setReadOnly(True)
        self.signal_layer_btn_3.setIcon(qtawesome.icon('fa.search', scale_factor=1, color='white'))
        self.view_check_btn_3.setIcon(qtawesome.icon('fa.eye', scale_factor=1, color='white'))
        self.pushButton_8.setIcon(qtawesome.icon('fa.blind', scale_factor=1, color='white'))
        self.pushButton_9.setIcon(qtawesome.icon('fa.square', scale_factor=1, color='white'))
        self.close_btn.setIcon(qtawesome.icon('fa.sign-out', scale_factor=1))
        self.signal_layer_btn_3.clicked.connect(self.alert_layer_win_3)
        self.view_check_btn_3.clicked.connect(self.view_check)
        self.pushButton_7.clicked.connect(lambda: self.run('global'))
        self.pushButton_8.clicked.connect(lambda: self.run('local'))
        self.pushButton_9.clicked.connect(lambda: self.run('profile'))
        #
        self.close_btn.clicked.connect(lambda: sys.exit())
        # self.move((app.desktop().width() - self.geometry().width()) / 2,
        #           (app.desktop().height() - self.geometry().height()) / 2)  # signal_layer_btn{background-color:#464646;color:white;}
        self.setStyleSheet(
            '''#layers_label,#layers_label_2,#layers_label_3{padding:2px;background-color:#666;color:white;}
            #signal_layer_btn,#pushButton,#pushButton_2,#pushButton_3{background-color:#0081a6;color:white;}#close_btn:hover{background:#666;color:white;}
            #signal_layer_btn_2,#pushButton_4,#pushButton_5,#pushButton_6{background-color:#0081a6;color:white;}
            #signal_layer_btn_3,#pushButton_7,#pushButton_8,#pushButton_9{background-color:#0081a6;color:white;}
            ''')
        self.check_flag, self.check_flag_2, self.check_flag_3 = False, False, False
        self._checklist = list(filter(lambda n: n.endswith('_script_signal_check'), step.checks))
        self._checklist2 = list(filter(lambda n: n.endswith('_script_soldermask_check'), step.checks))
        self._checklist3 = list(filter(lambda n: n.endswith('_script_silkscreen_check'), step.checks))
        if self._checklist:
            self.view_check_btn.setStyleSheet('background-color:#0081a6;color:white;')
            self.view_check_btn.setEnabled(True)
        else:
            self.view_check_btn.setEnabled(False)
        if self._checklist2:
            self.view_check_btn_2.setStyleSheet('background-color:#0081a6;color:white;')
            self.view_check_btn_2.setEnabled(True)
        else:
            self.view_check_btn_2.setEnabled(False)
        if self._checklist3:
            self.view_check_btn_3.setStyleSheet('background-color:#0081a6;color:white;')
            self.view_check_btn_3.setEnabled(True)
        else:
            self.view_check_btn_3.setEnabled(False)

    def alert_layer_win(self):
        self.layer_win = alert_window(self)

    def alert_layer_win_2(self):
        self.layer_win = alert_window2(self)

    def alert_layer_win_3(self):
        self.layer_win = alert_window3(self)

    # def alert_layer_win_3(self):
    #     self.layer_win = alert_window3(self)

    def run(self, type=None):
        pagenum = self.tabWidget.currentIndex()
        if pagenum == 0:
            checklayers = self.layers_label.text()
            v1, v2, v3, v4, v5 = self.lineEdit.text(), self.lineEdit_2.text(), self.lineEdit_3.text(), self.lineEdit_4.text(), self.lineEdit_5.text()
            testlist = []
            for gb in self.groupBox.findChildren(QCheckBox):
                if gb.checkState():
                    testlist.append(gb.text())
            if not checklayers:
                self.statusbar.showMessage("未处理任何层")
                return
            if not v1 or not v2 or not v3 or not v4 or not v5:
                self.statusbar.showMessage('不合法的浮点数')
                return
            self.statusbar.showMessage('正在分析...')
            checklist_name = self.signal_check_name.text()
            self.checklist = gen.Checklist(step, checklist_name, 'valor_analysis_signal')
            self.checklist.action()
            # checklist.erf('Outer (Mils)')
            params = {'pp_layer': checklayers, 'pp_spacing': v1, 'pp_r2c': v2, 'pp_d2c': v3, 'pp_sliver': v4,
                      'pp_min_pad_overlap': v5,
                      'pp_tests': r'\;'.join(testlist), 'pp_selected': 'All', 'pp_check_missing_pads_for_drills': 'Yes',
                      'pp_use_compensated_rout': 'No', 'pp_sm_spacing': 'No'}
            self.checklist.update(params=params)
            self.checklist.run(type)
            if self.auto_checkbox.isChecked():
                self.checklist.clear()
                self.checklist.update(params=params)
                self.checklist.copy()
                if self.checklist.name in step.checks:
                    step.deleteCheck(self.checklist.name)
                step.createCheck(self.checklist.name)
                step.pasteCheck(self.checklist.name)
            self.check_flag = True
            self.statusbar.showMessage('分析已完成')
            self.view_check_btn.setEnabled(True)
            self.view_check_btn.setStyleSheet('background-color:#0081a6;color:white;')
        elif pagenum == 1:
            checklayers = self.layers_label_2.text()
            v6, v7, v8, v9, v10, v11, v12 = self.lineEdit_6.text(), self.lineEdit_7.text(), self.lineEdit_8.text(), self.lineEdit_9.text(), self.lineEdit_10.text(), self.lineEdit_11.text(), self.lineEdit_12.text()
            testlist = []
            for gb in self.groupBox_10.findChildren(QCheckBox):
                if gb.checkState():
                    testlist.append(gb.text())
            if not checklayers:
                self.statusbar.showMessage("未处理任何层")
                return
            if not v6 or not v7 or not v8 or not v9 or not v10 or not v11 or not v12:
                self.statusbar.showMessage('不合法的浮点数')
                return
            self.statusbar.showMessage('正在分析...')
            checklist_name = self.signal_check_name_2.text()
            self.checklist2 = gen.Checklist(step, checklist_name, 'valor_analysis_sm')
            self.checklist2.action()
            # checklist.erf('Outer (Mils)')
            params = {'pp_layers': checklayers, 'pp_ar': v6, 'pp_coverage': v7, 'pp_sm2r': v8, 'pp_sliver': v9,
                      'pp_spacing': v10, 'pp_bridge': v11, 'pp_min_clear_overlap': v12,
                      'pp_tests': r'\;'.join(testlist), 'pp_selected': 'All', 'pp_use_compensated_rout': 'No'}
            self.checklist2.update(params=params)
            self.checklist2.run(type)
            if self.auto_checkbox_2.isChecked():
                self.checklist2.clear()
                self.checklist2.update(params=params)
                self.checklist2.copy()
                if self.checklist2.name in step.checks:
                    step.deleteCheck(self.checklist2.name)
                step.createCheck(self.checklist2.name)
                step.pasteCheck(self.checklist2.name)
            self.check_flag_2 = True
            self.statusbar.showMessage('分析已完成')
            self.view_check_btn_2.setEnabled(True)
            self.view_check_btn_2.setStyleSheet('background-color:#0081a6;color:white;')
        elif pagenum == 2:
            checklayers = self.layers_label_3.text()
            v13 = self.lineEdit_13.text()
            testlist = []
            for gb in self.groupBox_16.findChildren(QCheckBox):
                if gb.checkState():
                    testlist.append(gb.text())
            if not checklayers:
                self.statusbar.showMessage("未处理任何层")
                return
            if not v13:
                self.statusbar.showMessage('不合法的浮点数')
                return
            self.statusbar.showMessage('正在分析...')
            checklist_name = self.signal_check_name_3.text()
            self.checklist3 = gen.Checklist(step, checklist_name, 'valor_analysis_ss')
            self.checklist3.action()
            # checklist.erf('Outer (Mils)')
            params = {'pp_layers': checklayers,'pp_tests': r'\;'.join(testlist), 'pp_selected': 'All', 'pp_use_compensated_rout': 'No'}
            self.checklist3.update(params=params)
            self.checklist3.run(type)
            if self.auto_checkbox_3.isChecked():
                self.checklist3.clear()
                self.checklist3.update(params=params)
                self.checklist3.copy()
                if self.checklist3.name in step.checks:
                    step.deleteCheck(self.checklist3.name)
                step.createCheck(self.checklist3.name)
                step.pasteCheck(self.checklist3.name)
            self.check_flag_3 = True
            self.statusbar.showMessage('分析已完成')
            self.view_check_btn_3.setEnabled(True)
            self.view_check_btn_3.setStyleSheet('background-color:#0081a6;color:white;')

    def view_check(self):
        index = self.tabWidget.currentIndex()
        if index == 0:
            if self.check_flag:
                self.checklist.res_show()
            else:
                for name in step.checks:
                    if name.endswith('_script_signal_check'):
                        mycheck = step.checks.get(name)
                        mycheck.type = name
                        mycheck.open()
                        mycheck.res_show()
        elif index == 1:
            if self.check_flag_2:
                self.checklist2.res_show()
            else:
                for name in step.checks:
                    if name.endswith('_script_soldermask_check'):
                        mycheck = step.checks.get(name)
                        mycheck.type = name
                        mycheck.open()
                        mycheck.res_show()
        elif index == 2:
            if self.check_flag_3:
                self.checklist3.res_show()
            else:
                for name in step.checks:
                    if name.endswith('_script_silkscreen_check'):
                        mycheck = step.checks.get(name)
                        mycheck.type = name
                        mycheck.open()
                        mycheck.res_show()
        sys.exit()


class alert_window(QDialog):
    def __init__(self, parent):
        super(alert_window, self).__init__(parent)
        self.render()
        self.exec()

    def render(self):
        self.setWindowTitle('Layer Filter')
        self.resize(350, 500)
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
        signal_lays = job.matrix.returnRows('board', 'signal|power_ground')
        if signal_lays:
            signal_Node = QTreeWidgetItem(self.root)
            signal_Node.setText(0, '线路层')
            signal_Node.setCheckState(0, Qt.Unchecked)
            for layer in signal_lays:
                item = QTreeWidgetItem()
                item.setText(0, str(layer))
                item.setIcon(0, QIcon('/genesis/sys/scripts/zl/python/edit2/images/signal.png'))
                item.setCheckState(0, Qt.Unchecked)
                signal_Node.addChild(item)
        copy_lays = copy.copy(all_lays)
        for lay in copy_lays:
            if lay in signal_lays:
                all_lays.remove(lay)
        if all_lays:
            other_Node = QTreeWidgetItem(self.root)
            other_Node.setText(0, '其它')
            other_Node.setCheckState(0, Qt.Unchecked)
            for layer in all_lays:
                item = QTreeWidgetItem()
                item.setText(0, str(layer))
                item.setIcon(0, QIcon('/genesis/sys/scripts/zl/python/edit2/images/other.png'))
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
        btn_box = QHBoxLayout(self)
        ok = QPushButton(self)
        ok.setText('OK')
        ok.setStyleSheet('background-color:#0081a6;color:white;')
        ok.setObjectName('dialog_ok')
        ok.clicked.connect(self.generate_layerstr)
        close = QPushButton(self)
        close.setText('Close')
        close.setStyleSheet('background-color:#464646;color:white')
        ok.setObjectName('dialog_close')
        close.clicked.connect(lambda: self.close())
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_box.addItem(spacerItem1)
        btn_box.addWidget(ok)
        btn_box.addWidget(close)
        layout.addLayout(btn_box)
        self.setLayout(layout)

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
                        select_lay.append(chi.text(0))
        layer_str = r'\;'.join(select_lay)
        analysisCheck.layers_label.setText(layer_str)
        self.close()


class alert_window2(QDialog):
    def __init__(self, parent):
        super(alert_window2, self).__init__(parent)
        self.render()
        self.exec()

    def render(self):
        self.setWindowTitle('Layer Filter')
        self.resize(350, 500)
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
        signal_lays = job.matrix.returnRows('board', 'solder_mask')
        if signal_lays:
            signal_Node = QTreeWidgetItem(self.root)
            signal_Node.setText(0, '阻焊层')
            signal_Node.setCheckState(0, Qt.Unchecked)
            for layer in signal_lays:
                item = QTreeWidgetItem()
                item.setText(0, str(layer))
                item.setIcon(0, QIcon('/genesis/sys/scripts/zl/python/edit2/images/solder_mask.png'))
                item.setCheckState(0, Qt.Unchecked)
                signal_Node.addChild(item)
        copy_lays = copy.copy(all_lays)
        for lay in copy_lays:
            if lay in signal_lays:
                all_lays.remove(lay)
        if all_lays:
            other_Node = QTreeWidgetItem(self.root)
            other_Node.setText(0, '其它')
            other_Node.setCheckState(0, Qt.Unchecked)
            for layer in all_lays:
                item = QTreeWidgetItem()
                item.setText(0, str(layer))
                item.setIcon(0, QIcon('/genesis/sys/scripts/zl/python/edit2/images/other.png'))
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
        btn_box = QHBoxLayout(self)
        ok = QPushButton(self)
        ok.setText('OK')
        ok.setStyleSheet('background-color:#0081a6;color:white;')
        ok.setObjectName('dialog_ok')
        ok.clicked.connect(self.generate_layerstr)
        close = QPushButton(self)
        close.setText('Close')
        close.setStyleSheet('background-color:#464646;color:white')
        ok.setObjectName('dialog_close')
        close.clicked.connect(lambda: self.close())
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_box.addItem(spacerItem1)
        btn_box.addWidget(ok)
        btn_box.addWidget(close)
        layout.addLayout(btn_box)
        self.setLayout(layout)

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
                        select_lay.append(chi.text(0))
        layer_str = r'\;'.join(select_lay)
        analysisCheck.layers_label_2.setText(layer_str)
        self.close()

class alert_window3(QDialog):
    def __init__(self, parent):
        super(alert_window3, self).__init__(parent)
        self.render()
        self.exec()

    def render(self):
        self.setWindowTitle('Layer Filter')
        self.resize(350, 500)
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
        signal_lays = job.matrix.returnRows('board', 'silk_screen')
        if signal_lays:
            signal_Node = QTreeWidgetItem(self.root)
            signal_Node.setText(0, '文字层')
            signal_Node.setCheckState(0, Qt.Unchecked)
            for layer in signal_lays:
                item = QTreeWidgetItem()
                item.setText(0, str(layer))
                item.setIcon(0, QIcon('/genesis/sys/scripts/zl/python/edit2/images/silk_screen.png'))
                item.setCheckState(0, Qt.Unchecked)
                signal_Node.addChild(item)
        copy_lays = copy.copy(all_lays)
        for lay in copy_lays:
            if lay in signal_lays:
                all_lays.remove(lay)
        if all_lays:
            other_Node = QTreeWidgetItem(self.root)
            other_Node.setText(0, '其它')
            other_Node.setCheckState(0, Qt.Unchecked)
            for layer in all_lays:
                item = QTreeWidgetItem()
                item.setText(0, str(layer))
                item.setIcon(0, QIcon('/genesis/sys/scripts/zl/python/edit2/images/other.png'))
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
        btn_box = QHBoxLayout(self)
        ok = QPushButton(self)
        ok.setText('OK')
        ok.setStyleSheet('background-color:#0081a6;color:white;')
        ok.setObjectName('dialog_ok')
        ok.clicked.connect(self.generate_layerstr)
        close = QPushButton(self)
        close.setText('Close')
        close.setStyleSheet('background-color:#464646;color:white')
        ok.setObjectName('dialog_close')
        close.clicked.connect(lambda: self.close())
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_box.addItem(spacerItem1)
        btn_box.addWidget(ok)
        btn_box.addWidget(close)
        layout.addLayout(btn_box)
        self.setLayout(layout)

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
                        select_lay.append(chi.text(0))
        layer_str = r'\;'.join(select_lay)
        analysisCheck.layers_label_2.setText(layer_str)
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet('QMessageBox{font:11pt;}')
    app.setWindowIcon(QIcon(':/icon/res/demo.png'))
    jobname = os.environ.get('JOB')
    if not jobname:
        QMessageBox.warning(None, 'tips', '请打开料号')
        sys.exit()
    job = gen.Job(jobname)
    user = job.getUser()
    stepname = os.environ.get('STEP')
    if not stepname:
        QMessageBox.warning(None, 'tips', '请打开step')
        sys.exit()
    step = job.steps.get(stepname)
    step.initStep()
    analysisCheck = AnalysisCheck()
    analysisCheck.show()
    sys.exit(app.exec_())
