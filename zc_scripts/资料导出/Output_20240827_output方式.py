#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:Output_20240827_output方式.py
   @author:zl
   @time:2024/6/18 15:14
   @software:PyCharm
   @desc:
   20240821 外层线路菲林检查是否漏加金面积
   20240826  1.根据层属性out_mirror设置是否勾选镜像层
             2.部分反面工具输出镜像提示 如果正面层选择镜像或者反面层没选镜像 提示
   20240827 改回output输出钻锣带
"""
import genClasses
import os
import re
import shutil
import sys
import res_rc
import qtawesome
import genClasses as gen

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor, QFont, QIcon
from PyQt5.QtWidgets import QWidget, QApplication, QCheckBox, QTableWidgetItem, QHeaderView, QComboBox, QFileDialog, \
    QMessageBox

import OutputUI as ui


class Output(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.__type = None
        self.label_logo.setPixmap(QPixmap(":/res/logo.png"))
        self.lineEdit_jobname.setText(jobname)
        self.lineEdit_jobname.setCursorPosition(0)
        self.comboBox_steps.addItems(job.steps)
        if os.environ.get('STEP'):
            self.comboBox_steps.setCurrentText(os.environ.get('STEP'))
        self.lineEdit_path.setText(f'D:/{jobname}')
        self.lineEdit_path.setCursorPosition(0)
        self.comboBox_anchor.addItems(['Step Datum', 'Profile center'])
        self.header1 = ['勾选', '层列表', '属性', '状态', 'x轴涨缩%%', 'y轴涨缩%%', '镜像', '格', '式', '单位', '膜面']
        self.header2 = ['勾选', '层列表', '属性', '状态', 'x轴涨缩mm', 'y轴涨缩mm', '镜像', '格', '式', '单位', '膜面']
        self.tableWidget.setColumnCount(len(self.header1))
        self.tableWidget.setHorizontalHeaderLabels(self.header1)
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.setColumnWidth(0, 40)
        self.tableWidget.setColumnWidth(1, 200)
        self.tableWidget.setColumnWidth(2, 80)
        self.tableWidget.setColumnWidth(3, 80)
        self.tableWidget.setColumnWidth(6, 40)
        self.tableWidget.setColumnWidth(7, 60)
        self.tableWidget.setColumnWidth(8, 60)
        self.pushButton_path.setIcon(qtawesome.icon('fa.link', color='cyan'))
        self.pushButton_run.setIcon(qtawesome.icon('fa.download', color='cyan'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='cyan'))
        self.radioButton.clicked.connect(self.loadTable)
        self.radioButton_2.clicked.connect(self.loadTable)
        self.radioButton_3.clicked.connect(self.loadTable)
        self.radioButton_4.clicked.connect(self.loadTable)
        self.radioButton_5.clicked.connect(self.loadTable)
        # 类型
        self.checkBox_signal.clicked.connect(self.check_type)
        self.checkBox_soldmask.clicked.connect(self.check_type)
        self.checkBox_silkscreen.clicked.connect(self.check_type)
        self.checkBox_drill.clicked.connect(self.check_type)
        self.checkBox_cov.clicked.connect(self.check_type)
        # 涨缩方式
        self.radioButton_scale_1.clicked.connect(self.change_scale_way)
        self.radioButton_scale_2.clicked.connect(self.change_scale_way)
        self.pushButton_path.clicked.connect(self.select_path)
        self.pushButton_run.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.checkBox_select_all.clicked.connect(self.check_all)
        # self.setStyleSheet('QPushButton:hover{background:#5B9761;}QHeaderView::section{background-color:#9BC2E6;}')
        self.setStyleSheet('QPushButton{font:10pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')

    def check_type(self):
        if not self.__type:
            QMessageBox.information(self, '提示', '请选择输出类型')
            self.sender().setChecked(False)
            return
        layer_type = self.sender().text()
        state = self.sender().isChecked()
        if layer_type == '线路':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 2).text() == 'signal' and self.tableWidget.item(row, 3).text() == 'board':
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row,0).setChecked(False)
        elif layer_type == '文字':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 2).text() == 'silk_screen' and self.tableWidget.item(row, 3).text() == 'board':
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row,0).setChecked(False)
        elif layer_type == '钻孔':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 2).text() == 'drill' and self.tableWidget.item(row, 3).text() == 'board':
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row,0).setChecked(False)
        elif layer_type == '阻焊':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 2).text() == 'solder_mask' and self.tableWidget.item(row, 3).text() == 'board':
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row,0).setChecked(False)
        elif layer_type == '覆盖膜':
            for row in range(self.tableWidget.rowCount()):
                if re.match(r'c\d+$', self.tableWidget.item(row, 1).text()):
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row, 0).setChecked(False)

    def change_scale_way(self):
        if self.radioButton_scale_2.isChecked():
            self.tableWidget.setHorizontalHeaderLabels(self.header2)
        else:
            self.tableWidget.setHorizontalHeaderLabels(self.header1)
    def select_path(self):
        directory = QFileDialog.getExistingDirectory(self, "选择文件夹", "D:/", QFileDialog.ShowDirsOnly)
        if directory:
            self.lineEdit_path.setText(directory)

    def check_all(self):
        if self.checkBox_select_all.isChecked():
            for row in range(self.tableWidget.rowCount()):
                self.tableWidget.cellWidget(row, 0).setChecked(True)
        else:
            for row in range(self.tableWidget.rowCount()):
                self.tableWidget.cellWidget(row, 0).setChecked(False)

    def loadTable(self):
        self.__type = self.sender().text()
        step = job.steps.get(self.comboBox_steps.currentText())
        self.tableWidget.setRowCount(0)
        self.tableWidget.clearContents()
        matrix_info = job.matrix.info
        tableData = []
        __x, __y = 3, 5
        position = '正片'
        if self.__type == '菲林Gbr':
            for name, context, type in zip(matrix_info.get('gROWname'), matrix_info.get('gROWcontext'),
                                           matrix_info.get('gROWlayer_type')):
                tableData.append([name, type, context])
        elif self.__type == '钻孔Drl':
            __x, __y = 3, 3
            position = '/'
            for name, context, type in zip(matrix_info.get('gROWname'), matrix_info.get('gROWcontext'),
                                           matrix_info.get('gROWlayer_type')):
                if type == 'drill':
                    tableData.append([name, type, context])
        elif self.__type == '切割Dxf':
            __x, __y = 1, 1
            position = '/'
            for name, context, type in zip(matrix_info.get('gROWname'), matrix_info.get('gROWcontext'),
                                           matrix_info.get('gROWlayer_type')):
                tableData.append([name, type, context])
        elif self.__type == '锣带Rou':
            __x, __y = 3, 3
            position = '/'
            for name, context, type in zip(matrix_info.get('gROWname'), matrix_info.get('gROWcontext'),
                                           matrix_info.get('gROWlayer_type')):
                if type == 'rout':
                    tableData.append([name, type, context])

        if self.__type == '存档tgz':
            jobs = genClasses.Top().listJobs()
            self.tableWidget.setRowCount(len(jobs))
            for row, data in enumerate(jobs):
                check = QCheckBox()
                check.setStyleSheet('margin-left:10px;')
                self.tableWidget.setCellWidget(row, 0, check)
                item = QTableWidgetItem('---')
                item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 1, QTableWidgetItem(str(data)))
                self.tableWidget.setItem(row, 2, item)
                item = QTableWidgetItem('---')
                item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 3, item)
                item = QTableWidgetItem('---')
                item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 4, item)
                item = QTableWidgetItem('---')
                item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 5, item)
                item = QTableWidgetItem('---')
                item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 6, item)
                item = QTableWidgetItem('---')
                item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 7, item)
                item = QTableWidgetItem('---')
                item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 8, item)
                item = QTableWidgetItem('---')
                item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 9, item)
                item = QTableWidgetItem('---')
                item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 10, item)
        else:
            self.tableWidget.setRowCount(len(tableData))
            for row, data in enumerate(tableData):
                color = '#AFEEEE'
                if data[2] == 'misc':
                    color = '#AFEEEE'
                else:
                    if data[1] == 'signal':
                        color = '#FFA500'
                    elif data[1] == 'solder_mask':
                        color = '#008080'
                    elif data[1] == 'drill':
                        color = '#A9A9A9'
                    elif data[1] == 'silk_screen':
                        color = '#FFFFFF'
                    elif data[1] == 'coverlay':
                        color = '#00FF00'
                check = QCheckBox()
                check.setStyleSheet('margin-left:10px;')
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
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 4, item)
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 5, item)
                check = QCheckBox()
                check.setStyleSheet('margin-left:10px;')
                if data[0].strip():
                    if step.layers.get(str(data[0])).getGenesisAttr('.out_mirror') == 'yes':
                        check.setChecked(True)
                self.tableWidget.setCellWidget(row, 6, check)
                font = QFont('微软雅黑', 10)
                x_len = QComboBox()
                x_len.setFont(font)
                x_len.addItems([str(i) for i in range(1, 6)])
                x_len.setCurrentText(str(__x))
                y_len = QComboBox()
                y_len.setFont(font)
                y_len.addItems([str(i) for i in range(7)])
                y_len.setCurrentText(str(__y))
                self.tableWidget.setCellWidget(row, 7, x_len)
                self.tableWidget.setCellWidget(row, 8, y_len)
                item = QTableWidgetItem('mm')
                item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 9, item)
                item = QTableWidgetItem(position)
                item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 10, item)

                self.tableWidget.item(row, 1).setBackground(QColor(color))
                self.tableWidget.item(row, 2).setBackground(QColor(color))
                self.tableWidget.item(row, 3).setBackground(QColor(color))
                self.tableWidget.item(row, 4).setBackground(QColor(color))
                self.tableWidget.item(row, 5).setBackground(QColor(color))
                self.tableWidget.item(row, 9).setBackground(QColor(color))
                self.tableWidget.item(row, 10).setBackground(QColor(color))


    def run(self):
        if not self.__type:
            QMessageBox.information(self, '提示', '请选择输出类型')
            return
        flag = False
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.cellWidget(row, 0).isChecked():
                flag = True
                break
        if not flag:
            QMessageBox.information(self, '提示', '未勾选层')
            return
        step = job.steps.get(self.comboBox_steps.currentText())
        self.step = step
        path = self.lineEdit_path.text().strip().upper()
        prefix = '' if self.checkBox_cancelJobname.isChecked() else f'{jobname}-'
        # 自动回读
        auto_read_back = self.checkBox_autoRead.isChecked()
        x_anchor,y_anchor = step.datum.get('x'),step.datum.get('y')
        if self.comboBox_anchor.currentText() == 'Profile center':
            x_anchor, y_anchor = step.profile2.xcenter, step.profile2.ycenter
        step.initStep()
        different_layers = []
        if self.__type == '菲林Gbr':
            for row in range(self.tableWidget.rowCount()):
                scale_label = ''  # 系数标签，加在文件名中
                if self.tableWidget.cellWidget(row, 0).isChecked():
                    layer = self.tableWidget.item(row, 1).text()
                    mirror = 'yes' if self.tableWidget.cellWidget(row, 6).isChecked() else 'no'
                    res = self.check_mir_layer(layer, mirror)
                    if not res:
                        return
                    if layer in (job.SignalLayers[0], job.SignalLayers[-1]):
                        flag = self.check_au_area(layer)
                        if not flag:
                            QMessageBox.warning(None,'提醒',f'检查到{layer}没有加金面积')
                    if not self.tableWidget.item(row, 4).text().strip():
                        x_scale = 1
                    else:
                        x_val = self.tableWidget.item(row, 4).text().strip()
                        scale_label += f'x{x_val}%%' if self.radioButton_scale_1.isChecked() else f'x{x_val}mm'
                        x_val = float(x_val)
                        x_scale = 1 - abs(x_val) / 10000 if x_val < 0 else 1 + x_val / 10000
                    if not self.tableWidget.item(row, 5).text().strip():
                        y_scale = 1
                    else:
                        y_val = self.tableWidget.item(row, 5).text().strip()
                        scale_label += f'y{y_val}%%' if self.radioButton_scale_1.isChecked() else f'y{y_val}mm'
                        y_val = float(y_val)
                        y_scale = 1 - abs(y_val) / 10000 if y_val < 0 else 1 + y_val / 10000
                    nf1, nf2 = self.tableWidget.cellWidget(row, 7).currentText(), self.tableWidget.cellWidget(row,8).currentText()
                    step.layers.get(layer).setGenesisAttr('.out_x_scale', x_scale)
                    step.layers.get(layer).setGenesisAttr('.out_y_scale', y_scale)
                    step.Gerber274xOut(layer,path + '/FILM', mirror=mirror, x_scale=x_scale, y_scale=y_scale, line_units='mm', prefix=prefix, units='mm', nf1=nf1, nf2=nf2,x_anchor=x_anchor,y_anchor=y_anchor)
                    if scale_label:
                        shutil.move(f'{path}/FILM/{prefix}{layer}.gbr', f'{path}/FILM/{prefix}{layer}({scale_label}).gbr')
                    if auto_read_back:
                        name = f'{prefix}{layer}({scale_label}).gbr' if scale_label else f'{prefix}{layer}.gbr'
                        file_layer = re.sub('[%()]','', name)  # genesis层名不能有特殊字符%()，去掉
                        step.COM('input_manual_reset')
                        step.COM(f'input_manual_set,path={path}/FILM/{name},job={jobname},step={step.name},format=Gerber274x,data_type=ascii,units=mm,coordinates=absolute,zeroes=trailing,nf1={nf1},nf2={nf2},decimal=no,separator=*,tool_units=inch,layer={file_layer},wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3')
                        step.COM('input_manual,script_path=')
                        res = self.do_compare(layer, file_layer, x_scale, y_scale, mirror, x_anchor, y_anchor)
                        if res:
                            different_layers.append(res)

        elif self.__type == '钻孔Drl':
            # 检查重孔
            for row in range(self.tableWidget.rowCount()):
                scale_label = ''  # 系数标签，加在文件名中
                if self.tableWidget.cellWidget(row, 0).isChecked():
                    layer = self.tableWidget.item(row, 1).text()
                    mirror = 'yes' if self.tableWidget.cellWidget(row, 6).isChecked() else 'no'
                    res = self.check_mir_layer(layer, mirror)
                    if not res:
                        return
                    if not self.tableWidget.item(row, 4).text().strip():
                        x_scale = 1
                    else:
                        x_val = self.tableWidget.item(row, 4).text().strip()
                        scale_label += f'x{x_val}%%' if self.radioButton_scale_1.isChecked() else f'x{x_val}mm'
                        x_val = float(x_val)
                        x_scale = 1 - abs(x_val) / 10000 if x_val < 0 else 1 + x_val / 10000
                    if not self.tableWidget.item(row, 5).text().strip():
                        y_scale = 1
                    else:
                        y_val = self.tableWidget.item(row, 5).text().strip()
                        scale_label += f'y{y_val}%%' if self.radioButton_scale_1.isChecked() else f'y{y_val}mm'
                        y_val = float(y_val)
                        y_scale = 1 - abs(y_val) / 10000 if y_val < 0 else 1 + y_val / 10000
                    nf1, nf2 = self.tableWidget.cellWidget(row, 7).currentText(), self.tableWidget.cellWidget(row, 8).currentText()
                    repeat = self.check_repeat_hole(layer)
                    if repeat:
                        confirm = QMessageBox.warning(self, '检查重孔', f'{layer}层检查到重孔，是否继续',
                                                      QMessageBox.Ok | QMessageBox.Cancel)
                        if confirm == QMessageBox.Cancel:
                            return
                    step.layers.get(layer).setGenesisAttr('.out_x_scale', x_scale)
                    step.layers.get(layer).setGenesisAttr('.out_y_scale', y_scale)
                    step.Excellon2Out(layer, path + '/DRILL', mirror=mirror, x_scale=x_scale, y_scale=y_scale, prefix=prefix, nf1=nf1, nf2=nf2,x_anchor=x_anchor,y_anchor=y_anchor)
                    if scale_label:
                        shutil.move(f'{path}/DRILL/{prefix}{layer}.drl', f'{path}/DRILL/{prefix}{layer}({scale_label}).drl')
                    if auto_read_back:
                        name = f'{prefix}{layer}({scale_label}).drl' if scale_label else f'{prefix}{layer}.drl'
                        file_layer = re.sub('[%()]', '', name)  # genesis层名不能有特殊字符%()，去掉
                        step.COM('input_manual_reset')
                        step.COM(f'input_manual_set,path={path}/DRILL/{name},job={jobname},step={step.name},format=Excellon2,data_type=ascii,units=mm,coordinates=absolute,zeroes=trailing,nf1={nf1},nf2={nf2},decimal=no,separator=nl,tool_units=mm,layer={file_layer},wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3')
                        step.COM('input_manual,script_path=')
                        res = self.do_compare(layer, file_layer, x_scale, y_scale, mirror, x_anchor, y_anchor)
                        if res:
                            different_layers.append(res)

        elif self.__type == '切割Dxf':
            for row in range(self.tableWidget.rowCount()):
                scale_label = ''  # 系数标签，加在文件名中
                if self.tableWidget.cellWidget(row, 0).isChecked():
                    layer = self.tableWidget.item(row, 1).text()
                    mirror = 'yes' if self.tableWidget.cellWidget(row, 6).isChecked() else 'no'
                    res = self.check_mir_layer(layer, mirror)
                    if not res:
                        return
                    if not self.tableWidget.item(row, 4).text().strip():
                        x_scale = 1
                    else:
                        x_val = self.tableWidget.item(row, 4).text().strip()
                        scale_label += f'x{x_val}%%' if self.radioButton_scale_1.isChecked() else f'x{x_val}mm'
                        x_val = float(x_val)
                        x_scale = 1 - abs(x_val) / 10000 if x_val < 0 else 1 + x_val / 10000
                    if not self.tableWidget.item(row, 5).text().strip():
                        y_scale = 1
                    else:
                        y_val = self.tableWidget.item(row, 5).text().strip()
                        scale_label += f'y{y_val}%%' if self.radioButton_scale_1.isChecked() else f'y{y_val}mm'
                        y_val = float(y_val)
                        y_scale = 1 - abs(y_val) / 10000 if y_val < 0 else 1 + y_val / 10000

                    nf1, nf2 = self.tableWidget.cellWidget(row,7).currentText(), self.tableWidget.cellWidget(row, 8).currentText()
                    repeat = self.check_repeat_line(layer)
                    if repeat:
                        confirm = QMessageBox.warning(self, '检查重线', f'{layer}层检查到重线，是否继续',
                                                      QMessageBox.Ok | QMessageBox.Cancel)
                        if confirm == QMessageBox.Cancel:
                            return
                    step.DxfOut(layer, path + '/DXF', mirror=mirror, x_scale=x_scale, y_scale=y_scale, prefix=prefix,x_anchor=x_anchor,y_anchor=y_anchor)
                    if scale_label:
                        shutil.move(f'{path}/DXF/{prefix}{layer}.dxf', f'{path}/DXF/{prefix}{layer}({scale_label}).dxf')
                    if auto_read_back:
                        name = f'{prefix}{layer}({scale_label}).dxf' if scale_label else f'{prefix}{layer}.dxf'
                        file_layer = re.sub('[%()]', '', name)  # genesis层名不能有特殊字符%()，去掉
                        step.COM('input_manual_reset')
                        step.COM(f'input_manual_set,path={path}/DXF/{name},job={jobname},step={step.name},format=DXF,data_type=ascii,units=mm,coordinates=absolute,zeroes=none,nf1={nf1},nf2={nf2},decimal=no,separator=*,tool_units=inch,layer={file_layer},wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.06096,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3')
                        step.COM('input_manual,script_path=')
                        res = self.do_compare(layer, file_layer, x_scale, y_scale, mirror, x_anchor, y_anchor)
                        if res:
                            different_layers.append(res)
        elif self.__type == '锣带Rou':
            for row in range(self.tableWidget.rowCount()):
                scale_label = ''  # 系数标签，加在文件名中
                if self.tableWidget.cellWidget(row, 0).isChecked():
                    layer = self.tableWidget.item(row, 1).text()
                    mirror = 'yes' if self.tableWidget.cellWidget(row, 6).isChecked() else 'no'
                    res = self.check_mir_layer(layer, mirror)
                    if not res:
                        return
                    if not self.tableWidget.item(row, 4).text().strip():
                        x_scale = 1
                    else:
                        x_val = self.tableWidget.item(row, 4).text().strip()
                        scale_label += f'x{x_val}%%' if self.radioButton_scale_1.isChecked() else f'x{x_val}mm'
                        x_val = float(x_val)
                        x_scale = 1 - abs(x_val) / 10000 if x_val < 0 else 1 + x_val / 10000
                    if not self.tableWidget.item(row, 5).text().strip():
                        y_scale = 1
                    else:
                        y_val = self.tableWidget.item(row, 5).text().strip()
                        scale_label += f'y{y_val}%%' if self.radioButton_scale_1.isChecked() else f'y{y_val}mm'
                        y_val = float(y_val)
                        y_scale = 1 - abs(y_val) / 10000 if y_val < 0 else 1 + y_val / 10000
                    nf1, nf2 = self.tableWidget.cellWidget(row,7).currentText(), self.tableWidget.cellWidget(row, 8).currentText()
                    step.Excellon2Out(layer, path + '/ROU', mirror=mirror, x_scale=x_scale, y_scale=y_scale, prefix=prefix, suffix='.rou', nf1=nf1, nf2=nf2,x_anchor=x_anchor,y_anchor=y_anchor)
                    if scale_label:
                        shutil.move(f'{path}/ROU/{prefix}{layer}.rou', f'{path}/ROU/{prefix}{layer}({scale_label}).rou')
        elif self.__type == '存档tgz':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.cellWidget(row, 0).isChecked():
                    name = self.tableWidget.item(row, 1).text()
                    genClasses.Top().exportJob(name, path + '/CAM')

        if different_layers:
            QMessageBox.warning(self,'提示', f"导出完成！\n回读对比结果：{'、'.join(different_layers)}导出前后有差异，请检查!")
        else:
            if auto_read_back:
                QMessageBox.information(self, '提示', '导出完成！\n回读对比结果：导出前后无差异.')
            else:
                QMessageBox.information(self, '提示', '导出完成！')

    def do_compare(self, layer, layer_after, x_scale, y_scale, mirror, x_anchor, y_anchor):
        map_layer = f'{layer}+++compare'
        self.step.affect(layer_after)
        if x_scale != 1 or y_scale != 1:
            self.step.Transform(oper='scale', x_anchor=x_anchor, y_anchor=y_anchor, x_scale=2-x_scale, y_scale=2-y_scale)
        if mirror == 'yes':
            self.step.Transform(oper='mirror', x_anchor=x_anchor, y_anchor=y_anchor)
        self.step.unaffectAll()
        self.step.VOF()
        self.step.compareLayers(layer,jobname,self.step.name, layer_after,tol=25.4, map_layer=map_layer, map_layer_res=200)
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

    def check_repeat_hole(self, layer):
        """检查重孔"""
        flatten = f'{layer}+++flat'
        self.step.Flatten(layer, flatten)
        checklist = gen.Checklist(self.step, type='valor_dfm_nfpr')
        checklist.action()
        checklist.erf('NPTH Pads')
        params = {'pp_layer': flatten, 'pp_delete': 'Duplicate\;Covered','pp_work': 'Features', 'pp_drill': '', 'pp_non_drilled': 'No',
                  'pp_in_selected': 'All', 'pp_remove_mark': 'Mark'}
        checklist.update(params=params)
        checklist.run()
        checklist.clear()
        checklist.update(params=params)
        checklist.copy()
        if checklist.name in self.step.checks:
            self.step.deleteCheck(checklist.name)
        self.step.createCheck(checklist.name)
        self.step.pasteCheck(checklist.name)
        info = self.step.INFO(f'-t check -e {jobname}/{self.step.name}/{checklist.name} -m script -d MEAS -o action=1')
        self.step.removeLayer(flatten)
        self.step.removeLayer(f'{flatten}+++')
        if info:
            return True
        else:
            return False

    def check_repeat_line(self, layer):
        """检查重线"""
        flatten = f'{layer}+++flat'
        self.step.Flatten(layer, flatten)
        checklist = gen.Checklist(self.step, type='valor_dfm_nflr')
        params = {'pp_layer': flatten, 'pp_min_line': '0', 'pp_max_line': '2540', 'pp_margin': '0',
                      'pp_remove_item': 'Line\;Arc', 'pp_delete': 'Covered', 'pp_work': 'Features',
                      'pp_remove_mark': 'Mark'}
        checklist.action()
        checklist.update(params=params)
        checklist.run('global')
        checklist.clear()
        checklist.update(params=params)
        checklist.copy()
        if checklist.name in self.step.checks:
            self.step.deleteCheck(checklist.name)
        self.step.createCheck(checklist.name)
        self.step.pasteCheck(checklist.name)
        info = self.step.INFO(f'-t check -e {jobname}/{self.step.name}/{checklist.name} -m script -d MEAS -o action=1')
        self.step.VOF()
        self.step.removeLayer(flatten)
        self.step.removeLayer(f'{flatten}+++')
        self.step.VON()
        if info:
            return True
        else:
            return False

    # 20240821 检查是否有加金面积
    def check_au_area(self, layer):
        self.step.initStep()
        self.step.affect(layer)
        self.step.setFilterTypes('text')
        self.step.setTextFilter('AU:*SQ/MM*')
        self.step.selectAll()
        self.step.resetFilter()
        if self.step.Selected_count():
            # 再判断是否有值
            info = self.step.INFO(f'-t layer -e {jobname}/{self.step.name}/{layer} -d FEATURES -o select')
            self.step.clearAll()
            del info[0]
            for line in info:
                text = line.split('\'')[1]
                text = text.replace(' ', '')
                res = re.search('AU:(\d+|\d+\.\d+)SQ/MM\((\d+|\d+\.\d+)%\)', text)
                if res:
                    return True
                else:
                    return False
        else:
            return False

    # 20240826 部分反面工具输出镜像提示
    def check_mir_layer(self, layer, mir):
        if re.match('c\d+$', layer):
            n = int(layer.replace('c', ''))
            if n % 2 and mir == 'yes':
                res = QMessageBox.warning(self, '提醒', f'检测到{layer}是正面，是否继续镜像?', QMessageBox.Ok | QMessageBox.Cancel)
                if res == QMessageBox.Cancel:
                    return False
            elif n % 2 == 0 and mir == 'no':
                res = QMessageBox.warning(self, '提醒', f'检测到{layer}是反面，是否不镜像?', QMessageBox.Ok | QMessageBox.Cancel)
                if res == QMessageBox.Cancel:
                    return False
        return True


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':res/demo.png'))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    output = Output()
    output.show()
    sys.exit(app.exec_())
