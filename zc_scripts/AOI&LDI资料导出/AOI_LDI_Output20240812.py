#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AOI_LDI_Output.py
   @author:zl
   @time:2024/7/3 15:55
   @software:PyCharm
   @desc:AOI资料   保留选择的层，其他层删掉 删除pnl中profile外的物件
   LDI资料 保留选择的层和选镀层阻焊层，选镀层和阻焊层flatten后invert，其他层删掉 删除pnl中profile外的物件
    20240731  先把当前料号备份-bak, 在当前料号去执行相关操作，并在pnl打散zc-job2，打散后重命名为料号-aoi同时导出，再把备份料号重命名会当前料号。
"""
import os
import re
import sys

import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor, QIcon
from PyQt5.QtWidgets import QWidget, QApplication, QFileDialog, QCheckBox, QTableWidgetItem, QHeaderView, QMessageBox

import AOI_LDI_OutputUI as ui
import genClasses as gen
import res_rc


class AOI_LDI_Output(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.label_logo.setPixmap(QPixmap(":/res/logo.png"))
        self.lineEdit_jobname.setText(jobname)
        self.lineEdit_jobname.clearFocus()
        self.lineEdit_jobname.setCursorPosition(0)
        self.lineEdit_path.setText(f'D:/{jobname}')
        self.lineEdit_path.clearFocus()
        self.header = ['勾选', '层列表', '属性', '状态']
        self.tableWidget.setColumnCount(len(self.header))
        self.tableWidget.setHorizontalHeaderLabels(self.header)
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.setColumnWidth(0, 40)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.pushButton_path.setIcon(qtawesome.icon('fa.link', color='cyan'))
        self.pushButton_exec.setIcon(qtawesome.icon('fa.download', color='cyan'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='cyan'))
        self.pushButton_path.clicked.connect(self.select_path)
        self.pushButton_exec.clicked.connect(self.exec)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.radioButton_aoi.clicked.connect(self.loadTable)
        self.radioButton_ldi.clicked.connect(self.loadTable)
        # 类型
        self.checkBox_signal.clicked.connect(self.check_type)
        self.checkBox_drill.clicked.connect(self.check_type)
        self.checkBox_select_all.clicked.connect(self.check_type)
        self.loadTable()
        self.setStyleSheet(
            'QPushButton{font:10pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')

    def select_path(self):
        directory = QFileDialog.getExistingDirectory(self, "选择文件夹", "D:/", QFileDialog.ShowDirsOnly)
        if directory:
            self.lineEdit_path.setText(directory)

    def check_type(self):
        layer_type = self.sender().text()
        state = self.sender().isChecked()
        if layer_type == '线路':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 2).text() == 'signal' and self.tableWidget.item(row, 3).text() == 'board':
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row, 0).setChecked(False)
        elif layer_type == '阻焊':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 2).text() == 'solder_mask' and self.tableWidget.item(row, 3).text() == 'board':
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row, 0).setChecked(False)
        elif layer_type == '全选':
            if state:
                for row in range(self.tableWidget.rowCount()):
                    self.tableWidget.cellWidget(row, 0).setChecked(True)
            else:
                for row in range(self.tableWidget.rowCount()):
                    self.tableWidget.cellWidget(row, 0).setChecked(False)

    def exec(self):
        layers, types = [], []
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.cellWidget(row, 0).isChecked():
                layers.append(self.tableWidget.item(row, 1).text())
                types.append(self.tableWidget.item(row, 2).text())
        if not layers:
            QMessageBox.information(self, '提示', '未勾选层')
            return
        path = self.lineEdit_path.text().strip().upper()
        if not path:
            QMessageBox.information(self, '提示', '路径不能为空')
            return
        top = gen.Top()
        bak = f'{jobname}-bak'
        top.VOF()
        top.deleteJob(bak)
        top.VON()
        top.copyJob(jobname, bak, 'genesis')
        job.open(1)
        if self.radioButton_aoi.isChecked():
            dest = f'{jobname}-aoi'
            delete_row = filter(lambda row: row not in layers, job.matrix.getInfo().get('gROWname'))
            for row in delete_row:
                job.matrix.deleteRow(row)
            pnl_step = job.steps.get('pnl')
            if pnl_step:
                pnl_step.initStep()
                for layer in layers:
                    pnl_step.affect(layer)
                pnl_step.selectRectangle(pnl_step.profile2.xmin, pnl_step.profile2.ymin, pnl_step.profile2.xmax, pnl_step.profile2.ymax)
                if pnl_step.Selected_count():
                    pnl_step.selectReverse()
                    if pnl_step.Selected_count():
                        pnl_step.selectDelete()
                pnl_step.selectSymbol('zdbgk')
                pnl_step.resetFilter()
                if pnl_step.Selected_count():
                    pnl_step.selectDelete()
                # 打散zc-job*
                pnl_step.selectSymbol('zc-job*')
                pnl_step.resetFilter()
                if pnl_step.Selected_count():
                    pnl_step.selectBreak()
                pnl_step.unaffectAll()
                pnl_step.close()
            job.save()
            job.close(1)
            top.renameJob(jobname, dest, 'genesis')
            if not os.path.exists(f'{path}/AOI'):
                os.makedirs(f'{path}/AOI')
            top.exportJob(dest, f'{path}/AOI')
            # top.deleteJob(dest)
        else:
            if not stepname:
                QMessageBox.information(self, '提示', '输出ldi请在step中执行！')
                return
            # if len(layers) > 1:
            #     dest = f'{jobname}-{"-".join(layers)}'
            # 选镀/阻焊层
            target_layers = []
            for lay in job.matrix.returnRows():
                if re.match(r'g[tb\d+]s$|dk[tb\d+](-\d+)?$', lay):
                    target_layers.append(lay)
                if lay not in layers:
                    job.matrix.deleteRow(lay)
            suffix = "-".join(target_layers) if target_layers else "-".join(layers)
            dest = f'{jobname}-{suffix}'
            pnl_step = job.steps.get('pnl')
            if pnl_step:
                pnl_step.initStep()
                for layer in layers:
                    pnl_step.affect(layer)
                # if target_layers:
                #     [pnl_step.affect(lay) for lay in target_layers]
                pnl_step.selectRectangle(pnl_step.profile2.xmin - 0.15, pnl_step.profile2.ymin -0.15, pnl_step.profile2.xmax + 0.15, pnl_step.profile2.ymax + 0.15)
                if pnl_step.Selected_count():
                    pnl_step.selectReverse()
                    if pnl_step.Selected_count():
                        pnl_step.selectDelete()
                pnl_step.selectSymbol('zdbgk')
                pnl_step.resetFilter()
                if pnl_step.Selected_count():
                    pnl_step.selectDelete()
                pnl_step.selectSymbol('zc-job*')
                pnl_step.resetFilter()
                if pnl_step.Selected_count():
                    pnl_step.selectBreak()
                pnl_step.unaffectAll()
                for layer in layers:
                    tmp_ = f'{layer}+++{pnl_step.pid}'
                    pnl_step.Flatten(layer, tmp_)
                    pnl_step.truncate(layer)
                    if layer in target_layers:
                        pnl_step.prof_to_rout(layer)
                        pnl_step.affect(layer)
                        pnl_step.selectCutData()
                        pnl_step.unaffectAll()
                        pnl_step.VOF()
                        pnl_step.removeLayer(layer + '+++')
                        pnl_step.VON()
                        pnl_step.affect(tmp_)
                        pnl_step.moveSel(layer, 'yes')
                    else:
                        pnl_step.affect(tmp_)
                        pnl_step.moveSel(layer)
                    pnl_step.unaffectAll()
                    pnl_step.removeLayer(tmp_)
                pnl_step.close()
            for step in job.steps:
                if step != stepname:
                    job.removeStep(step)
            job.save()
            job.close(1)
            if not os.path.exists(f'{path}/LDI'):
                os.makedirs(f'{path}/LDI')
            top.exportJob(jobname, f'{path}/LDI')
            top.renameJob(jobname, dest, 'genesis')
        # 把bak改回jobname
        top.renameJob(bak, jobname)
        job.open(1)
        if stepname:
            job.steps.get(stepname).initStep()
        else:
            job.steps.get(job.steps[0]).initStep()
        QMessageBox.information(self, '提示', '导出完成!')

    def loadTable(self):
        self.tableWidget.setRowCount(0)
        self.tableWidget.clearContents()
        self.checkBox_signal.setChecked(False)
        self.checkBox_drill.setChecked(False)
        self.checkBox_select_all.setChecked(False)
        matrix_info = job.matrix.info
        tableData = []
        if self.radioButton_ldi.isChecked():
            for name, context, type in zip(matrix_info.get('gROWname'), matrix_info.get('gROWcontext'),
                                           matrix_info.get('gROWlayer_type')):
                if context == 'board' and type in ('signal', 'drill'):
                    tableData.append([name, type, context])
                # 选镀/阻焊
                if re.match(r'g[tb\d+]s$|dk[tb\d+](-\d+)?$', name):
                    tableData.append([name, type, context])
        else:
            for name, context, type in zip(matrix_info.get('gROWname'), matrix_info.get('gROWcontext'),
                                           matrix_info.get('gROWlayer_type')):
                if context == 'board' and type in ('signal', 'drill'):
                    tableData.append([name, type, context])
        self.tableWidget.setRowCount(len(tableData))
        for row, data in enumerate(tableData):
            color = '#AFEEEE'
            if data[1] == 'signal':
                color = '#FFA500'
            elif data[1] == 'drill':
                color = '#A9A9A9'
            elif data[1] == 'solder_mask':
                color = '#008080'
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
            self.tableWidget.item(row, 1).setBackground(QColor(color))
            self.tableWidget.item(row, 2).setBackground(QColor(color))
            self.tableWidget.item(row, 3).setBackground(QColor(color))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':/res/demo.png'))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    stepname = os.environ.get('STEP')
    output = AOI_LDI_Output()
    output.show()
    sys.exit(app.exec_())
