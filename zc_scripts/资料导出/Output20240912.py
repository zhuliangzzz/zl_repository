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
   20240828 分段输出
   20240829 需要flatten，否则分段后内部step的东西会导出
   20240905 1. 检查dkt dkb受镀面积是否添加  未添加则提示并退出，有添加则进一步计算受镀面积是否正确，并提示是否更新
            2.增加导dxf打散块  pad as circle
            3.增加导dxf层合并
            4.break钻孔，merge钻孔/锣带
   20240911 林杰龙 导dxf文字转surface
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
        #
        self.checkBox_pad_as_circle.setVisible(False)
        self.checkBox_merge.setVisible(False)
        # 分段
        self.comboBox_split.addItems(['', '上', '下'])
        self.comboBox_split.currentIndexChanged.connect(self.changeRotateEnable)
        self.checkBox_split_rotate.setEnabled(False)
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
        # self.tableWidget.setColumnWidth(8, 60)
        self.tableWidget.horizontalHeader().setSectionResizeMode(8, QHeaderView.Stretch)
        self.pushButton_path.setIcon(qtawesome.icon('fa.link', color='cyan'))
        self.pushButton_run.setIcon(qtawesome.icon('fa.download', color='cyan'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='cyan'))
        self.comboBox_steps.currentIndexChanged.connect(self.steps_changed)
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

    def steps_changed(self):
        step = job.steps.get(self.comboBox_steps.currentText())
        if self.__type:
            for row in range(self.tableWidget.rowCount()):
                lay = self.tableWidget.item(row, 1).text()
                if lay:
                    if step.layers.get(str(lay)).getGenesisAttr('.out_mirror') == 'yes':
                        self.tableWidget.cellWidget(row, 6).setChecked(True)
                    else:
                        self.tableWidget.cellWidget(row, 6).setChecked(False)
    def changeRotateEnable(self):
        if self.comboBox_split.currentIndex():
            self.checkBox_split_rotate.setEnabled(True)
        else:
            self.checkBox_split_rotate.setEnabled(False)

    def loadTable(self):
        self.__type = self.sender().text()
        step = job.steps.get(self.comboBox_steps.currentText())
        self.tableWidget.setRowCount(0)
        self.tableWidget.clearContents()
        matrix_info = job.matrix.info
        tableData = []
        __x, __y = 3, 5
        position = '正片'
        self.checkBox_pad_as_circle.setVisible(False)
        self.checkBox_merge.setVisible(False)
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
            self.checkBox_pad_as_circle.setVisible(True)
            self.checkBox_merge.setVisible(True)
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
        clip_layer = f'split+++{step.pid}'
        if self.comboBox_split.currentIndex():
            # 做一层clip
            step.createLayer(clip_layer)
            step.affect(clip_layer)
            if self.comboBox_split.currentIndex() == 1:
                step.addRectangle(step.profile2.xmin - 30, step.profile2.ycenter, step.profile2.xmax + 30,
                                  step.profile2.ycenter - 355)
            else:
                step.addRectangle(step.profile2.xmin - 30, step.profile2.ycenter, step.profile2.xmax + 30,
                                  step.profile2.ycenter + 355)
            step.unaffectAll()
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
                    if step.name == 'pnl':
                        if layer in (job.SignalLayers[0], job.SignalLayers[-1]):
                            flag = self.check_au_area(layer)
                            if not flag:
                                QMessageBox.warning(None,'提醒',f'检查到{layer}没有加金面积')
                                sys.exit()
                         # 20240905 检查受镀面积
                        if layer in ('dkt', 'dkb'):
                            self.check_cu_area(layer)
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
                    # 20240829 flatten
                    flat_layer = f'{layer}_flat'
                    step.Flatten(layer, flat_layer)
                    if self.comboBox_split.currentIndex():
                        self.splitLayer(step, flat_layer, clip_layer)
                    step.Gerber274xOut(flat_layer, path + '/FILM', mirror=mirror, x_scale=x_scale, y_scale=y_scale, line_units='mm', prefix=prefix, break_sr='no', units='mm', nf1=nf1, nf2=nf2,x_anchor=x_anchor,y_anchor=y_anchor)
                    if scale_label:
                        shutil.move(f'{path}/FILM/{prefix}{flat_layer}.gbr', f'{path}/FILM/{prefix}{layer}({scale_label}).gbr')
                    else:
                        shutil.move(f'{path}/FILM/{prefix}{flat_layer}.gbr', f'{path}/FILM/{prefix}{layer}.gbr')
                    step.removeLayer(flat_layer)
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
                    # 20240829 flatten
                    flat_layer = f'{layer}_flat'
                    step.Flatten(layer, flat_layer)
                    # 20240905 打散
                    step.affect(flat_layer)
                    step.selectBreak()
                    step.unaffectAll()
                    # 20240905 merge
                    step.COM(f'tools_merge_ex,layer={flat_layer},mode=merge')
                    if self.comboBox_split.currentIndex():
                        self.splitLayer(step, flat_layer, clip_layer)
                    step.COM(f'ncset_cur,job={jobname},step={step.name},layer={flat_layer},ncset={layer}')
                    step.COM('ncd_set_machine,machine=default_excellon,thickness=0')
                    step.COM(f'ncd_set_params,format=Excellon2,zeroes=trailing,units=mm,tool_units=mm,nf1={nf1},nf2={nf2},decimal=no,modal_coords=no,single_sr=yes,sr_zero_set=no,repetitions=sr,incremental=no,optimize=yes,iterations=5,reduction_percent=1,cool_spread=0,break_sr=yes,sort_method=Standard,strip_width=0,xspeed=100,yspeed=100,rout_layer=,fixed_tools=yes,tools_assign_mode=increasing_size,comp_short_slot=no')
                    step.COM(f'ncd_register,angle=0,mirror={mirror},xoff=0,yoff=0,version=1,xorigin=0,yorigin=0,xscale={x_scale},yscale={y_scale},xscale_o=0,yscale_o=0')
                    step.COM('ncd_cre_drill')
                    step.COM('ncset_units,units=mm')
                    if not os.path.exists(path + '/DRILL'):
                        os.makedirs(path + '/DRILL')
                    step.COM(f'ncd_ncf_export,stage=1,split=1,dir={path + "/DRILL"},name={prefix}{flat_layer}.drl')
                    step.COM(f'ncset_delete,name={layer}')
                    if scale_label:
                        shutil.move(f'{path}/DRILL/{prefix}{flat_layer}.drl', f'{path}/DRILL/{prefix}{layer}({scale_label}).drl')
                    else:
                        shutil.move(f'{path}/DRILL/{prefix}{flat_layer}.drl',f'{path}/DRILL/{prefix}{layer}.drl')
                    step.removeLayer(flat_layer)
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
            pad_as_circle = 'yes' if self.checkBox_pad_as_circle.isChecked() else 'no'
            if self.checkBox_merge.isChecked():
                flats = []
                step.COM('output_layer_reset')
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
                        repeat = self.check_repeat_line(layer)
                        if repeat:
                            confirm = QMessageBox.warning(self, '检查重线', f'{layer}层检查到重线，是否继续',
                                                          QMessageBox.Ok | QMessageBox.Cancel)
                            if confirm == QMessageBox.Cancel:
                                return
                        # flatten
                        flat_layer = f'{layer}_flat'
                        step.Flatten(layer, flat_layer)
                        # 20240911 林杰龙 文字转surface
                        step.affect(flat_layer)
                        step.setFilterTypes('text')
                        step.selectAll()
                        step.resetFilter()
                        if step.Selected_count():
                            step.Contourize()
                        step.unaffectAll()
                        if self.comboBox_split.currentIndex():
                            self.splitLayer(step, flat_layer, clip_layer)
                        flats.append(flat_layer)
                        step.COM(f'output_layer_set,layer={flat_layer},angle=0,mirror={mirror},x_scale={x_scale},y_scale={y_scale},comp=0,polarity=positive,setupfile=,setupfiletmp=,line_units=mm,gscl_file=,step_scale=no')
                        # step.DxfOut(flat_layer, path + '/DXF', mirror=mirror, x_scale=x_scale, y_scale=y_scale,
                        #             prefix=prefix, x_anchor=x_anchor, y_anchor=y_anchor, pads_2circles=pad_as_circle)
                step.COM(f'output,job={jobname},step={step.name},format=DXF,dir_path={path + "/DXF"},prefix={prefix},suffix=.dxf,break_sr=yes,break_symbols=yes,break_arc=no,scale_mode=all,surface_mode=contour,min_brush=25.4,units=mm,x_anchor={x_anchor},y_anchor={y_anchor},x_offset=0,y_offset=0,line_units=mm,override_online=yes,pads_2circles={pad_as_circle},draft=no,contour_to_hatch=no,pad_outline=no,output_files=single,file_ver=old')
                for flat in flats:
                    step.removeLayer(flat)
                if scale_label:
                    shutil.move(f'{path}/DXF/{prefix}{flats[0]}.dxf',
                                        f'{path}/DXF/{prefix}{flats[0].replace("_flat","")}({scale_label}).dxf')
                else:
                    shutil.move(f'{path}/DXF/{prefix}{flats[0]}.dxf', f'{path}/DXF/{prefix}{flats[0].replace("_flat","")}.dxf')
            else:
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
                        # flatten
                        flat_layer = f'{layer}_flat'
                        step.Flatten(layer, flat_layer)
                        # 20240911 林杰龙 文字转surface
                        step.affect(flat_layer)
                        step.setFilterTypes('text')
                        step.selectAll()
                        step.resetFilter()
                        if step.Selected_count():
                            step.Contourize()
                        step.unaffectAll()
                        if self.comboBox_split.currentIndex():
                            self.splitLayer(step, flat_layer, clip_layer)
                        step.DxfOut(flat_layer, path + '/DXF', mirror=mirror, x_scale=x_scale, y_scale=y_scale, prefix=prefix, x_anchor=x_anchor, y_anchor=y_anchor, pads_2circles=pad_as_circle)
                        if scale_label:
                            shutil.move(f'{path}/DXF/{prefix}{flat_layer}.dxf', f'{path}/DXF/{prefix}{layer}({scale_label}).dxf')
                        else:
                            shutil.move(f'{path}/DXF/{prefix}{flat_layer}.dxf',f'{path}/DXF/{prefix}{layer}.dxf')
                        step.removeLayer(flat_layer)
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
                    nf1, nf2 = self.tableWidget.cellWidget(row, 7).currentText(), self.tableWidget.cellWidget(row, 8).currentText()
                    step.layers.get(layer).setGenesisAttr('.out_x_scale', x_scale)
                    step.layers.get(layer).setGenesisAttr('.out_y_scale', y_scale)
                    # 20240829 flatten
                    flat_layer = f'{layer}_flat'
                    step.Flatten(layer, flat_layer)
                    # 20240905 merge
                    step.COM(f'tools_merge_ex,layer={flat_layer},mode=merge')
                    if self.comboBox_split.currentIndex():
                        self.splitLayer(step, flat_layer, clip_layer)
                    step.COM(f'ncrset_cur,job={jobname},step={step.name},layer={flat_layer},ncset={layer}')
                    step.COM('ncr_set_machine,machine=default_excellon,thickness=0')
                    step.COM(f'ncr_set_params,format=Excellon2,zeroes=trailing,units=mm,tool_units=mm,nf1={nf1},nf2={nf2},decimal=no,modal_coords=yes,single_sr=no,sr_zero_set=no,repetitions=sr,drill_layer=rt2drl,sr_zero_drill_layer=drill,break_sr=no,ccw=no,short_lines=none,press_down=no,last_z_up=16,max_arc_ang=180,sep_lyrs=no,allow_no_chain_f=yes,keep_table_order=no')
                    step.COM(f'ncr_register,angle=0,mirror={mirror},xoff=1,yoff=1,version=1,xorigin=1,yorigin=1,xscale={x_scale},yscale={y_scale},xscale_o=0,yscale_o=0')
                    step.COM('ncr_cre_rout')
                    step.COM('ncrset_units,units=mm')
                    if not os.path.exists(path + '/ROU'):
                        os.makedirs(path + '/ROU')
                    step.COM(f'ncr_ncf_export,dir={path + "/ROU"},name={prefix}{flat_layer}.rou')
                    step.COM(f'ncrset_delete,name={layer}')
                    step.removeLayer(flat_layer)
                    if scale_label:
                        shutil.move(f'{path}/ROU/{prefix}{flat_layer}.rou', f'{path}/ROU/{prefix}{layer}({scale_label}).rou')
                    else:
                        shutil.move(f'{path}/ROU/{prefix}{flat_layer}.rou', f'{path}/ROU/{prefix}{layer}.rou')
                    if auto_read_back:
                        name = f'{prefix}{layer}({scale_label}).rou' if scale_label else f'{prefix}{layer}.rou'
                        file_layer = re.sub('[%()]', '', name)  # genesis层名不能有特殊字符%()，去掉
                        step.COM('input_manual_reset')
                        step.COM(
                            f'input_manual_set,path={path}/ROU/{name},job={jobname},step={step.name},format=Excellon2,data_type=ascii,units=mm,coordinates=absolute,zeroes=trailing,nf1={nf1},nf2={nf2},decimal=no,separator=nl,tool_units=mm,layer={file_layer},wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3')
                        step.COM('input_manual,script_path=')
                        res = self.do_compare(layer, file_layer, x_scale, y_scale, mirror, x_anchor, y_anchor)
                        if res:
                            different_layers.append(res)

        elif self.__type == '存档tgz':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.cellWidget(row, 0).isChecked():
                    name = self.tableWidget.item(row, 1).text()
                    genClasses.Top().exportJob(name, path + '/CAM')

        # 20240829 清除clip层
        if self.comboBox_split.currentIndex():
            step.removeLayer(clip_layer)
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

    def check_cu_area(self, layer):
        self.step.initStep()
        self.step.affect(layer)
        self.step.setFilterTypes('text')
        self.step.setTextFilter('CU:*SQ/MM*')
        self.step.selectAll()
        self.step.resetFilter()
        if self.step.Selected_count():
            # 再判断是否有值
            info = self.step.INFO(f'-t layer -e {jobname}/{self.step.name}/{layer} -d FEATURES -o select')
            # self.step.clearAll()
            del info[0]
            for line in info:
                text = line.split('\'')[1]
                text = text.replace(' ', '')
                res = re.search('CU:(\d+|\d+\.\d+)SQ/MM\((\d+|\d+\.\d+)%\)', text)
                if res:
                    self.step.COM(
                        f'copper_area,layer1={layer},layer2=,drills=yes,consider_rout=no,ignore_pth_no_pad=no,drills_source=matrix,thickness=0,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes')
                    area, percent = self.step.COMANS.split()
                    new_text = f'CU:{"%.2f" % float(area)}SQ/MM({"%.2f" % float(percent)}%)'
                    if text != new_text:
                        confirm = QMessageBox.information(self, '提醒', f'检查到{layer}受镀面积{text}不正确,\n是否立即更新 更新为{new_text}', QMessageBox.Apply | QMessageBox.Abort)
                        if confirm == QMessageBox.Apply:
                            self.step.changeText(new_text)
                            self.step.clearAll()
                        else:
                            self.step.clearAll()
                            sys.exit()
                else:
                    self.step.clearAll()
                    QMessageBox.warning(self, '提醒', f'检查到{layer}没有加受镀面积')
                    sys.exit()
        else:
            self.step.clearAll()
            QMessageBox.warning(self, '提醒', f'检查到{layer}没有加受镀面积')
            sys.exit()

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

    # 分段输出
    def splitLayer(self, step, layer, clip_layer):
        step.affect(layer)
        step.clip_area(margin=500, ref_layer=clip_layer)
        if self.checkBox_split_rotate.isChecked():
            step.Transform(oper='rotate', x_anchor=step.profile2.xcenter,y_anchor=step.profile2.ycenter, angle=180)
        step.unaffectAll()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':res/demo.png'))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    output = Output()
    output.show()
    sys.exit(app.exec_())
