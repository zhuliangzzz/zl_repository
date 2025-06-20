#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:Output_20240827_output方式.py
   @author:zl
   @time:2024/6/18 15:14
   @software:PyCharm
   @desc: 
"""
import genClasses
import os
import re
import sys
import res_rc
import qtawesome
from qtawesome import icon_browser
import genClasses as gen

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor, QFont
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
        self.comboBox_anchor.addItems(['Profile center', 'Step Datum'])
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
        self.setStyleSheet('QPushButton{font:11pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')

    def check_type(self):
        if not self.__type:
            QMessageBox.information(self, '提示', '请选择输出类型')
            self.sender().setChecked(False)
            return
        layer_type = self.sender().text()
        state = self.sender().isChecked()
        # if layer_type == '线路':
        #     layer_type = 'signal'
        # elif layer_type == '文字':
        #     layer_type = 'silk_screen'
        # elif layer_type == '钻孔':
        #     layer_type = 'drill'
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
                if re.match(r'g(t|b|\d+)s', self.tableWidget.item(row, 1).text()):
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row,0).setChecked(False)
        elif layer_type == '覆盖膜':
            for row in range(self.tableWidget.rowCount()):
                if re.match(r'c\d+', self.tableWidget.item(row, 1).text()):
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
                self.tableWidget.setItem(row, 4, QTableWidgetItem())
                self.tableWidget.setItem(row, 5, QTableWidgetItem())
                check = QCheckBox()
                check.setStyleSheet('margin-left:10px;')
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
        path = self.lineEdit_path.text().strip().upper()
        prefix = '' if self.checkBox_cancelJobname.isChecked() else f'{jobname}-'
        x_anchor,y_anchor = step.datum.get('x'),step.datum.get('y')
        if self.comboBox_anchor.currentText() == 'Profile center':
            x_anchor, y_anchor = step.profile2.xcenter, step.profile2.ycenter
        step.initStep()
        if self.__type == '菲林Gbr':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.cellWidget(row,0).isChecked():
                    layer = self.tableWidget.item(row,1).text()
                    x_scale = 1 if not self.tableWidget.item(row, 4).text().strip() else self.tableWidget.item(row,4).text()
                    y_scale = 1 if not self.tableWidget.item(row, 5).text().strip() else self.tableWidget.item(row,5).text()
                    mirror = 'yes' if self.tableWidget.cellWidget(row, 6).isChecked() else 'no'
                    nf1, nf2 = self.tableWidget.cellWidget(row,7).currentText(), self.tableWidget.cellWidget(row,8).currentText()
                    step.Gerber274xOut(layer,path + '/FILM', mirror=mirror, x_scale=x_scale, y_scale=y_scale, line_units='mm', prefix=prefix, units='mm', nf1=nf1, nf2=nf2,x_anchor=x_anchor,y_anchor=y_anchor)
        elif self.__type == '钻孔Drl':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.cellWidget(row,0).isChecked():
                    layer = self.tableWidget.item(row,1).text()
                    x_scale = 1 if not self.tableWidget.item(row, 4).text().strip() else self.tableWidget.item(row,4).text()
                    y_scale = 1 if not self.tableWidget.item(row, 5).text().strip() else self.tableWidget.item(row,5).text()
                    mirror = 'yes' if self.tableWidget.cellWidget(row, 6).isChecked() else 'no'
                    nf1, nf2 = self.tableWidget.cellWidget(row,7).currentText(), self.tableWidget.cellWidget(row, 8).currentText()
                    step.Excellon2Out(layer, path + '/DRILL', mirror=mirror, x_scale=x_scale, y_scale=y_scale, prefix=prefix, nf1=nf1, nf2=nf2,x_anchor=x_anchor,y_anchor=y_anchor)
        elif self.__type == '切割Dxf':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.cellWidget(row,0).isChecked():
                    layer = self.tableWidget.item(row,1).text()
                    x_scale = 1 if not self.tableWidget.item(row, 4).text().strip() else self.tableWidget.item(row,4).text()
                    y_scale = 1 if not self.tableWidget.item(row, 5).text().strip() else self.tableWidget.item(row,5).text()
                    mirror = 'yes' if self.tableWidget.cellWidget(row, 6).isChecked() else 'no'
                    nf1, nf2 = self.tableWidget.cellWidget(row,7).currentText(), self.tableWidget.cellWidget(row, 8).currentText()
                    step.DxfOut(layer, path + '/DXF', mirror=mirror, x_scale=x_scale, y_scale=y_scale, prefix=prefix, nf1=nf1, nf2=nf2,x_anchor=x_anchor,y_anchor=y_anchor)
        elif self.__type == '锣带Rou':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.cellWidget(row,0).isChecked():
                    layer = self.tableWidget.item(row,1).text()
                    x_scale = 1 if not self.tableWidget.item(row, 4).text().strip() else self.tableWidget.item(row,4).text()
                    y_scale = 1 if not self.tableWidget.item(row, 5).text().strip() else self.tableWidget.item(row,5).text()
                    mirror = 'yes' if self.tableWidget.cellWidget(row, 6).isChecked() else 'no'
                    nf1, nf2 = self.tableWidget.cellWidget(row,7).currentText(), self.tableWidget.cellWidget(row, 8).currentText()
                    step.Excellon2Out(layer, path + '/ROU', mirror=mirror, x_scale=x_scale, y_scale=y_scale, prefix=prefix, suffix='.rou', nf1=nf1, nf2=nf2,x_anchor=x_anchor,y_anchor=y_anchor)
        elif self.__type == '存档tgz':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.cellWidget(row,0).isChecked():
                    name = self.tableWidget.item(row,1).text()
                    genClasses.Top().exportJob(name, path + '/CAM')
        QMessageBox.information(self, '提示', '导出完成！')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    output = Output()
    output.show()
    sys.exit(app.exec_())
