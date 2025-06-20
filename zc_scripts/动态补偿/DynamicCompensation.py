#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:DynamicCompensation.py
   @author:zl
   @time:2024/8/22 13:07
   @software:PyCharm
   @desc:
   输入了面铜的就认为需要执行补偿
"""
import os
import re
import sys

import qtawesome
from PyQt5.QtGui import QIcon, QFont, QIntValidator
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QHeaderView, QCheckBox, QTableWidgetItem, QLineEdit

import DynamicCompensationUI as ui
import genClasses as gen
import res_rc


class DynamicCompensation(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.label.setText('Job:%s\t\tStep:%s' % (jobname, stepname))
        self.lineEdit_lw.setText('100')
        self.lineEdit_lw_2.setText('100')
        self.lineEdit_ls.setText('200')
        self.lineEdit_ls_2.setText('300')
        header = ['层名', "面铜", '最小线距(my)', '补偿值(my)']
        self.tableWidget.setColumnCount(len(header))
        self.tableWidget.setHorizontalHeaderLabels(header)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.setEditTriggers(QHeaderView.NoEditTriggers)
        self.pushButton_exec.setIcon(qtawesome.icon('fa.upload', scale_factor=1, color='white'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.arrow-circle-o-right', scale_factor=1, color='white'))
        self.pushButton_exec.clicked.connect(self.exec)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            'QPushButton{font-family: "微软雅黑";background-color:#0081a6;color:white;} QPushButton:hover{background:black;} QListWidget::Item{height:20px;} QListWidget::Item:selected{background: #0081a6;color:white;}')
        self.loadTable()


    def loadTable(self):
        self.tableWidget.setRowCount(job.SignalNum)
        for row, lay in enumerate(job.SignalLayers):
            self.tableWidget.setItem(row, 0, QTableWidgetItem(lay))
            edit = QLineEdit()
            edit.setValidator(QIntValidator())
            edit.rownum = row
            edit.setFont(QFont('微软雅黑', 10))
            edit.textChanged.connect(self.getCompensation)
            self.tableWidget.setCellWidget(row, 1, edit)

    def getCompensation(self):
        if self.sender().text() == '':
            return
        cu_thickness = int(self.sender().text())
        rownum = self.sender().rownum
        if cu_thickness < 12:
            min_spacing = 0
            compensation = 0
        elif cu_thickness < 16:
            min_spacing = 40
            compensation = 15
        elif cu_thickness < 20:
            min_spacing = 40
            compensation = 15
        elif cu_thickness < 25:
            min_spacing = 40
            compensation = 15
        elif cu_thickness < 30:
            min_spacing = 50
            compensation = 25
        elif cu_thickness < 35:
            min_spacing = 55
            compensation = 25
        elif cu_thickness < 40:
            min_spacing = 60
            compensation = 30
        elif cu_thickness < 45:
            min_spacing = 65
            compensation = 30
        elif cu_thickness < 50:
            min_spacing = 70
            compensation = 30
        elif cu_thickness < 55:
            min_spacing = 75
            compensation = 30
        elif cu_thickness < 60:
            min_spacing = 80
            compensation = 35
        elif cu_thickness < 65:
            min_spacing = 85
            compensation = 35
        elif cu_thickness < 70:
            min_spacing = 90
            compensation = 40
        elif cu_thickness < 76:
            min_spacing = 95
            compensation = 40
        else:
            min_spacing = 0
            compensation = 0
        self.tableWidget.setItem(rownum, 2, QTableWidgetItem(str(min_spacing)))
        self.tableWidget.setItem(rownum, 3, QTableWidgetItem(str(compensation)))

    def exec(self):
        flag = False
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.cellWidget(row, 1).text() != '':
                flag = True
                break
        if not flag:
            QMessageBox.information(self, '提示', '请先输入面铜~')
            return
        lw = float(self.lineEdit_lw.text())
        lw_2 = float(self.lineEdit_lw_2.text())
        ls = self.lineEdit_ls.text()
        ls_2 = self.lineEdit_ls_2.text()
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.cellWidget(row, 1).text():
                layer = self.tableWidget.item(row, 0).text()
                min_spacing = self.tableWidget.item(row, 2).text()
                compensation = self.tableWidget.item(row, 3).text()
                step.initStep()
                # 备份
                step.affect(layer)
                step.copySel(layer + '_bak')
                step.unaffectAll()
                info_ = step.layers.get(layer).info2
                # 小于等于lw的所有线宽和大于lw2的所有线宽
                lines, lines_2 = [], []
                for symbol, line in zip(info_.get('gSYMS_HISTsymbol'), info_.get('gSYMS_HISTline')):
                    if line > 0:
                        res = re.match(r'(r|s)(\d+\.?\d*)', symbol)
                        if res and float(res.group(2)) <= lw:
                            lines.append(symbol)
                        if res and float(res.group(2)) > lw_2:
                            lines_2.append(symbol)
                for symbol, line in zip(info_.get('gSYMS_HISTsymbol'), info_.get('gSYMS_HISTarc')):
                    if line > 0:
                        res = re.match(r'(r|s)(\d+\.?\d*)', symbol)
                        if res and float(res.group(2)) <= lw:
                            lines.append(symbol)
                        if res and float(res.group(2)) > lw_2:
                            lines_2.append(symbol)
                # tmp_pp = f'{layer}+++{step.pid}'
                step.affect(layer)
                if lines:
                    line_str = ';'.join(lines)
                    step.setFilterTypes('line|arc', 'positive')
                    step.selectSymbol(line_str)
                    # 取消选中网格线
                    step.setAttrFilter('.string', 'text=wg')
                    step.selectAll('unselect')
                    checklist = gen.Checklist(step, type='frontline_dfm_ddetch')
                    checklist.action()
                    checklist.COM(
                        f'chklist_cupd,chklist=frontline_dfm_ddetch,nact=1,params=((pp_layer={layer})(pp_spc1=0)(pp_cmp1=0)(pp_interpolation=Steps)(pp_spc2={ls})(pp_cmp2={compensation})(pp_spc3=-1)(pp_cmp3=-1)(pp_spc4=-1)(pp_cmp4=-1)(pp_save=No)(pp_spc5=-1)(pp_cmp5=-1)(pp_spc6=-1)(pp_cmp6=-1)(pp_comp_func=.zero)(pp_min_spacing={min_spacing})(pp_select=Yes)),mode=regular')
                    checklist.COM('chklist_run,chklist=frontline_dfm_ddetch,nact=1,area=profile')
                    step.resetFilter()
                    step.VOF()
                    step.removeLayer(f'{layer}+++')
                    step.VON()
                    step.clearSel()
                if lines_2:
                    line_str = ';'.join(lines)
                    step.setFilterTypes('line|arc', 'positive')
                    step.selectSymbol(line_str)
                    # 取消选中网格线
                    step.setAttrFilter('.string', 'text=wg')
                    step.selectAll('unselect')
                    checklist = gen.Checklist(step, type='frontline_dfm_ddetch')
                    checklist.action()
                    checklist.COM(
                        f'chklist_cupd,chklist=frontline_dfm_ddetch,nact=1,params=((pp_layer={layer})(pp_spc1=0)(pp_cmp1=0)(pp_interpolation=Steps)(pp_spc2={ls_2})(pp_cmp2={compensation})(pp_spc3=-1)(pp_cmp3=-1)(pp_spc4=-1)(pp_cmp4=-1)(pp_save=No)(pp_spc5=-1)(pp_cmp5=-1)(pp_spc6=-1)(pp_cmp6=-1)(pp_comp_func=.zero)(pp_min_spacing={min_spacing})(pp_select=Yes)),mode=regular')
                    checklist.COM('chklist_run,chklist=frontline_dfm_ddetch,nact=1,area=profile')
                    step.resetFilter()
                    step.VOF()
                    step.removeLayer(f'{layer}+++')
                    step.VON()
                    step.clearSel()
                step.unaffectAll()
        QMessageBox.information(self, 'tips', '动态补偿已完成~')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setStyleSheet('QMessageBox {font-size:10pt;} QPushButton{font-family: "黑体";font-size:10pt;}')
    app.setWindowIcon(QIcon(':res/demo.png'))
    jobname = os.environ.get('JOB')
    stepname = os.environ.get('STEP')
    if not jobname:
        QMessageBox.warning(None, 'warning', '请打开料号！')
        sys.exit()
    if not stepname:
        QMessageBox.warning(None, 'warning', '请打开step！')
        sys.exit()
    job = gen.Job(jobname)
    step = job.steps.get(stepname)
    dc = DynamicCompensation()
    dc.show()
    sys.exit(app.exec_())
