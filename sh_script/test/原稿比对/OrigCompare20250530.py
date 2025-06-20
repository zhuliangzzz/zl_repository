#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:Output_20240827_output方式.py
   @author:zl
   @time:2025/5/27 14:36
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

import OutputUI_pyqt4 as ui


class Output(QWidget, ui.Ui_Form):
    def __init__(self):
        super(Output, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.db1 = '/id/incamp_db1/jobs'
        self.jobs = [str(j) for j in gen.Top().listJobs()]
        print(len(self.jobs))
        self.lineEdit_jobname.setText(jobname)
        self.lineEdit_jobname.setCursorPosition(0)
        self.comboBox_steps.addItems(job.stepsList)
        if os.environ.get('STEP'):
            for index, val in enumerate(job.stepsList):
                if val == os.environ.get('STEP'):
                    self.comboBox_steps.setCurrentIndex(index)
        else:
            for index, val in enumerate(job.stepsList):
                if val == 'edit':
                    self.comboBox_steps.setCurrentIndex(index)
        self.comboBox_target_job.addItems(self.jobs)
        for index, _ in enumerate(self.jobs):
            if _ == jobname:
                self.comboBox_target_job.setCurrentIndex(index)
        self.comboBox_target_steps.addItems(job.stepsList)
        self.comboBox_target_steps.setCurrentIndex(self.comboBox_steps.currentIndex())
        # self.lineEdit_path.setText(f'D:/{jobname}')
        # self.lineEdit_path.setCursorPosition(0)
        #
        # self.checkBox_pad_as_circle.setVisible(False)
        # self.checkBox_merge.setVisible(False)
        # self.lineEdit_merge_name.setVisible(False)
        # 分段
        # self.comboBox_split.addItems(['', '上', '下'])
        # self.comboBox_split.currentIndexChanged.connect(self.changeRotateEnable)
        # self.checkBox_split_rotate.setEnabled(False)
        # self.comboBox_anchor.addItems(['Step Datum', 'Profile center'])
        self.header1 = [u'勾选', u'层列表', 'type', 'context', u'单边比对参数']
        self.tableWidget.setColumnCount(len(self.header1))
        self.tableWidget.setHorizontalHeaderLabels(self.header1)
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.setColumnWidth(0, 30)
        self.tableWidget.setSelectionMode(QHeaderView.NoSelection)
        self.tableWidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setResizeMode(2, QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setResizeMode(3, QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setResizeMode(4, QHeaderView.Stretch)
        # self.tableWidget.horizontalHeader().setSectionResizeMode(9, QHeaderView.Stretch)
        # self.tableWidget.horizontalHeader().setSectionResizeMode(10, QHeaderView.Stretch)
        self.tableWidget.setItemDelegateForColumn(1, EmptyDelegate(self))
        self.tableWidget.setItemDelegateForColumn(2, EmptyDelegate(self))
        self.tableWidget.setItemDelegateForColumn(3, EmptyDelegate(self))
        # 类型
        self.checkBox_signal.clicked.connect(self.check_type)
        self.checkBox_soldmask.clicked.connect(self.check_type)
        self.checkBox_silkscreen.clicked.connect(self.check_type)
        self.checkBox_drill.clicked.connect(self.check_type)
        self.checkBox_board.clicked.connect(self.check_type)
        #
        layer_extra = (u'前缀', u'后缀')
        self.comboBox_layer_extra.addItems(layer_extra)
        self.lineEdit_layer_extra.setText('+++compare')
        tolerance = ('1.0', '2.0')
        self.comboBox_tolerance.addItems(tolerance)
        self.comboBox_tolerance.lineEdit().setValidator(QDoubleValidator(self.comboBox_tolerance))
        self.comboBox_area.addItems(('global', 'profile'))
        #
        self.pushButton_run.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.checkBox_select_all.clicked.connect(self.check_all)
        self.comboBox_target_job.lineEdit().returnPressed.connect(self.target_job_returnPressed)
        self.comboBox_target_job.currentIndexChanged.connect(self.target_job_changed)
        self.setStyleSheet(
            '''QPushButton{font:10pt;background-color:#0081a6;color:white;border:none;} QPushButton:hover{background:black;}''')
        # self.setStyleSheet(
        #     '''QPushButton{font:10pt;background-color:#459B81;color:white;} QPushButton:hover{background:black;}''')
        self.loadTable()
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)

    def check_type(self):
        layer_type = str(self.sender().text())
        state = self.sender().isChecked()
        print(state, layer_type)
        if layer_type == '线路':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 2).text() == 'signal' and self.tableWidget.item(row, 3).text() == 'board':
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row,
                                                                                                                   0).setChecked(
                        False)
        elif layer_type == '文字':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 2).text() == 'silk_screen' and self.tableWidget.item(row,
                                                                                                   3).text() == 'board':
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row,
                                                                                                                   0).setChecked(
                        False)
        elif layer_type == '钻孔':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 2).text() == 'drill' and self.tableWidget.item(row, 3).text() == 'board':
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row,
                                                                                                                   0).setChecked(
                        False)
        elif layer_type == '阻焊':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 2).text() == 'solder_mask' and self.tableWidget.item(row,
                                                                                                   3).text() == 'board':
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row,
                                                                                                                   0).setChecked(
                        False)
        elif layer_type == '板层':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 3).text() == 'board':
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row,
                                                                                                                   0).setChecked(
                        False)

    def check_all(self):
        if self.checkBox_select_all.isChecked():
            for row in range(self.tableWidget.rowCount()):
                self.tableWidget.cellWidget(row, 0).setChecked(True)
        else:
            for row in range(self.tableWidget.rowCount()):
                self.tableWidget.cellWidget(row, 0).setChecked(False)

    def loadTable(self):
        step = job.steps.get(self.comboBox_steps.currentText())
        self.tableWidget.setRowCount(0)
        self.tableWidget.clearContents()
        matrix_info = job.matrix.info
        tableData = []
        for name, context, type in zip(matrix_info.get('gROWname'), matrix_info.get('gROWcontext'),
                                       matrix_info.get('gROWlayer_type')):
            tableData.append([name, type, context])
        self.tableWidget.setRowCount(len(tableData))
        for row, data in enumerate(tableData):
            color = '#AFEEEE'
            if data[2] == 'misc':
                color = '#AFEEEE'
                size = 2
            else:
                if data[1] == 'signal':
                    color = '#FFA500'
                    # todo getsize
                    size = 2
                elif data[1] == 'solder_mask':
                    color = '#008080'
                    size = 2
                elif data[1] == 'drill':
                    color = '#A9A9A9'
                elif data[1] == 'silk_screen':
                    color = '#FFFFFF'
                    size = 2
            check = QCheckBox()
            check.setStyleSheet('margin-left:5px;')
            self.tableWidget.setCellWidget(row, 0, check)
            item = QTableWidgetItem(str(data[0]))
            item.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(row, 1, item)
            item = QTableWidgetItem(str(data[1]))
            item.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(row, 2, item)
            item = QTableWidgetItem(str(data[2]))
            item.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(row, 3, item)
            input_ = QLineEdit(str(size))
            input_.setStyleSheet('background-color: transparent;margin:4px;')
            self.tableWidget.setCellWidget(row, 4, input_)
            self.tableWidget.item(row, 1).setBackground(QColor(color))
            self.tableWidget.item(row, 2).setBackground(QColor(color))
            self.tableWidget.item(row, 3).setBackground(QColor(color))

            # self.tableWidget.item(row, 4).setBackground(QColor(color))

    def run(self):
        target_job = str(self.comboBox_target_job.currentText()).strip()
        if not target_job:
            QMessageBox.warning(self, u'提示', u'请选择目标料号！')
            return
        if target_job not in self.jobs:
            QMessageBox.warning(self, u'提示', u'目标料号不存在！')
            return
        target_step = str(self.comboBox_target_steps.currentText())
        target_steps = os.listdir(os.path.join(self.db1, target_job, 'steps'))
        if target_step not in target_steps:
            QMessageBox.warning(self, u'提示', u'输入料号需要回车更新目标step!')
            return
        tolerance = str(self.comboBox_tolerance.currentText()).strip()
        if not tolerance:
            QMessageBox.warning(self, u'提示', u'请输入或选择比对精度!')
            return
        flag = False
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.cellWidget(row, 0).isChecked():
                flag = True
                break
        if not flag:
            QMessageBox.information(self, u'提示', u'未勾选层')
            return
        step = job.steps.get(self.comboBox_steps.currentText())

    def do_compare(self, layer, layer_after, x_scale, y_scale, mirror, x_anchor, y_anchor):
        map_layer = '%s+++compare' % layer
        self.step.affect(layer_after)
        if x_scale != 1 or y_scale != 1:
            self.step.Transform(oper='scale', x_anchor=x_anchor, y_anchor=y_anchor, x_scale=2 - x_scale,
                                y_scale=2 - y_scale)
        if mirror == 'yes':
            self.step.Transform(oper='mirror', x_anchor=x_anchor, y_anchor=y_anchor)
        self.step.unaffectAll()
        self.step.VOF()
        self.step.compareLayers(layer, jobname, self.step.name, layer_after, tol=25.4, map_layer=map_layer,
                                map_layer_res=200)
        self.step.VON()
        self.step.affect(map_layer)
        self.step.selectSymbol('r0')
        self.step.resetFilter()
        count = self.step.Selected_count()
        self.step.unaffectAll()
        self.step.removeLayer(map_layer)
        if count:
            return layer
        else:
            return None

    def target_job_changed(self, index):
        print('changed', index)
        if index >= len(self.jobs):
            return
        target_job = self.jobs[index]
        target_steps = os.listdir(os.path.join(self.db1, target_job, 'steps'))
        self.comboBox_target_steps.clear()
        self.comboBox_target_steps.addItems(target_steps)

    def target_job_returnPressed(self):
        print(self.comboBox_target_job.currentText())
        if self.comboBox_target_job.currentText() not in self.jobs:
            QMessageBox.warning(self, 'warning', u'该料号不存在')
            self.comboBox_target_job.clear()
            self.comboBox_target_job.addItems(self.jobs)
            for index, _ in enumerate(self.jobs):
                if _ == jobname:
                    self.comboBox_target_job.setCurrentIndex(index)
                    self.target_job_changed(index)
        else:
            for index, _ in enumerate(self.jobs):
                if _ == self.comboBox_target_job.currentText():
                    self.comboBox_target_job.setCurrentIndex(index)
                    self.target_job_changed(index)


# 代理类
class EmptyDelegate(QItemDelegate):
    def __init__(self, parent):
        super(EmptyDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        return None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    # app.setWindowIcon(QIcon(':res/demo.png'))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    output = Output()
    output.show()
    sys.exit(app.exec_())
