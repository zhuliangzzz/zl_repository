#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AutoAnalysis.py
   @author:zl
   @time:2024/8/13 10:53
   @software:PyCharm
   @desc:一键分析
"""
import datetime
import os
import re
import sys
import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem, QHeaderView, QTableWidget, QMenu, QAction, \
    QMessageBox

import AutoAnalysisUI as ui

import genClasses as gen
import res_rc


class OneKeyAnalysis(QMainWindow, ui.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.label_title.setText(f'料号：{jobname}  用户：{job.getUser()}')
        self.items = {
            0: ['分析线宽线距孔环', self.get_pcs_analysis],
            1: ['分析字符间距，字符与开窗/线路间距', self.get_silkscreen_analysis],
            2: ['分析阻焊间距、阻焊桥宽、阻焊盖线宽度、让位间距', self.get_soldermask_analysis],
        }
        self.data = []
        header = ['序号', '分析项', '分析结果']
        self.tableWidget.setColumnCount(len(header))
        self.tableWidget.setHorizontalHeaderLabels(header)
        self.tableWidget.setRowCount(len(self.items))
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.setColumnWidth(0, 36)
        self.tableWidget.setColumnWidth(1, 300)
        self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tableWidget.setSelectionBehavior(QHeaderView.SelectRows)
        self.tableWidget.setSelectionMode(QHeaderView.SingleSelection)
        self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableWidget.customContextMenuRequested.connect(self.popMenu)
        self.loadData()
        self.tableWidget.itemClicked.connect(self.showResult)
        self.splitter.setSizes([500, 200])
        self.pushButton_exec.setIcon(qtawesome.icon('fa.download', color='white'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='white'))
        self.pushButton_exec.clicked.connect(self.exec)
        self.pushButton_exit.clicked.connect(self.exit)
        self.setStyleSheet(
            '#label_title{color:#eee;border-radius:5px;background-color:#0081a6;} QPushButton{font:9pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}'
            'QTableWidget::item:selected{background:yellow;color:black;}')

    def closeEvent(self, event):
        confirm = QMessageBox.information(self, '提示', '请确认是否退出', QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.No:
            event.ignore()

    def loadData(self):
        for item in self.items:
            self.tableWidget.setItem(item, 0, QTableWidgetItem(str(item + 1)))
            self.tableWidget.setItem(item, 1, QTableWidgetItem(self.items[item][0]))
            self.tableWidget.setItem(item, 2, QTableWidgetItem())

    def exec(self):
        if not job.steps.get('pcs'):
            QMessageBox.warning(self, '警告', '请检查是否有pcs')
            return
        for item in self.items:
            self.tableWidget.item(item, 2).setText('')
        for item in self.items:
            self.items.get(item)[1](item)
            self.showResult()
        QMessageBox.information(self, 'tips', '执行完毕！')

    def exit(self):
        confirm = QMessageBox.information(self, '提示', '请确认是否退出', QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            sys.exit()
        else:
            return

    def popMenu(self):
        # 弹出菜单
        menu = QMenu()
        runLocal = QAction(qtawesome.icon('fa.play-circle', color='orange'), '单项执行')
        menu.addAction(runLocal)
        item = self.tableWidget.currentRow()
        runLocal.triggered.connect(lambda: self.singleExec(item))
        menu.exec_(QCursor.pos())

    def singleExec(self, item):
        self.items.get(item)[1](item)
        self.showResult()

    def showResult(self):
        row = self.tableWidget.currentRow()
        self.label_item.setText(self.tableWidget.item(row, 1).text())
        self.textEdit.setText(self.tableWidget.item(row, 2).text())

    def get_pcs_analysis(self, item):
        self.statusbar.showMessage(f'正在执行{self.items[item][0]}')
        result = []
        pp_layer = ';'.join(job.SignalLayers)
        pcs_step = job.steps.get('pcs')
        pcs_step.initStep()
        checklist = gen.Checklist(pcs_step, 'pcs_analysis_checklist', 'valor_analysis_signal')
        checklist.action()
        checklist.erf('Outer (Mils)')
        checklist.COM(
            f'chklist_cupd,chklist=valor_analysis_signal,nact=1,params=((pp_layer={pp_layer})(pp_spacing=254)(pp_r2c=635)(pp_d2c=355.6)(pp_sliver=254)(pp_min_pad_overlap=127)(pp_tests=Spacing\;Drill\;Rout\;Size\;Sliver\;Stubs\;Center\;SMD)(pp_selected=All)(pp_check_missing_pads_for_drills=Yes)(pp_use_compensated_rout=No)(pp_sm_spacing=No)),mode=regular')
        checklist.run()
        checklist.clear()
        checklist.COM(
            f'chklist_cupd,chklist=valor_analysis_signal,nact=1,params=((pp_layer={pp_layer})(pp_spacing=254)(pp_r2c=635)(pp_d2c=355.6)(pp_sliver=254)(pp_min_pad_overlap=127)(pp_tests=Spacing\;Drill\;Rout\;Size\;Sliver\;Stubs\;Center\;SMD)(pp_selected=All)(pp_check_missing_pads_for_drills=Yes)(pp_use_compensated_rout=No)(pp_sm_spacing=No)),mode=regular')
        checklist.copy()
        if checklist.name in pcs_step.checks:
            pcs_step.deleteCheck(checklist.name)
        pcs_step.createCheck(checklist.name)
        pcs_step.pasteCheck(checklist.name)
        result.append('最小线宽：\n')
        for layer in job.SignalLayers:
            info = pcs_step.INFO(f'-t check -e %s/%s/%s -d MEAS -o action=1+category=line+layer={layer},units=mm' % (
                jobname, pcs_step.name, checklist.name))
            res = ''
            if info:
                res = min([float(l.split()[2]) for l in info])
            result.append(f"{layer}:{res}\t")
        result.append('\n最小线距：\n')
        for layer in job.SignalLayers:
            info = pcs_step.INFO(
                f'-t check -e %s/%s/%s -d MEAS -o action=1+category=spacing_length+layer={layer},units=mm' % (
                    jobname, pcs_step.name, checklist.name))
            res = ''
            if info:
                res = min([float(l.split()[2]) for l in info])
            result.append(f"{layer}:{res}\t")
        result.append('\n最小孔环：\n')
        for layer in job.SignalLayers:
            info = pcs_step.INFO(f'-t check -e %s/%s/%s -d MEAS -o action=1+category=pth_ar+layer={layer},units=mm' % (
            jobname, pcs_step.name, checklist.name))
            res = ''
            if info:
                res = min([float(l.split()[2]) for l in info])
            result.append(f"{layer}:{res}\t")
        self.tableWidget.setItem(item, 2, QTableWidgetItem(''.join(result)))
        self.statusbar.showMessage(f'{self.items[item][0]}已完成')
        app.processEvents()

    def get_silkscreen_analysis(self, item):
        self.statusbar.showMessage(f'正在执行{self.items[item][0]}')
        result, data = [], []
        layers = job.matrix.returnRows('board', 'silk_screen')
        pp_layer = ';'.join(layers)
        pcs_step = job.steps.get('pcs')
        pcs_step.initStep()
        checklist = gen.Checklist(pcs_step, 'pcs_analysis_checklist', 'valor_analysis_ss')
        checklist.action()
        # checklist.erf('Outer (Mils)')
        checklist.COM(
            f'chklist_cupd,chklist=valor_analysis_ss,nact=1,params=((pp_layers={pp_layer})(pp_spacing=508)(pp_tests=SM clearance\;SMD clearance\;Pad clearance\;Hole clearance\;Rout clearance\;Line width\;Copper coverage)(pp_selected=All)(pp_use_compensated_rout=No)),mode=regular')
        checklist.run()
        checklist.clear()
        checklist.COM(
            f'chklist_cupd,chklist=valor_analysis_ss,nact=1,params=((pp_layers={pp_layer})(pp_spacing=508)(pp_tests=SM clearance\;SMD clearance\;Pad clearance\;Hole clearance\;Rout clearance\;Line width\;Copper coverage)(pp_selected=All)(pp_use_compensated_rout=No)),mode=regular')
        checklist.copy()
        if checklist.name in pcs_step.checks:
            pcs_step.deleteCheck(checklist.name)
        pcs_step.createCheck(checklist.name)
        pcs_step.pasteCheck(checklist.name)
        result.append('字符间距：\n')
        for layer in layers:
            info = pcs_step.INFO(f'-t check -e %s/%s/%s -d MEAS -o action=1+category=ss_spacing+layer={layer},units=mm' % (
                jobname, pcs_step.name, checklist.name))
            res = ''
            if info:
                res = min([float(l.split()[2]) for l in info])
            result.append(f"{layer}:{res}\t")
        result.append('\n字符与开窗：\n')
        for layer in layers:
            info = pcs_step.INFO(f'-t check -e %s/%s/%s -d MEAS -o action=1+category=ss2sm+layer={layer},units=mm' % (
                    jobname, pcs_step.name, checklist.name))
            res = ''
            if info:
                res = min([float(l.split()[2]) for l in info])
            result.append(f"{layer}:{res}\t")
        # result.append('\n字符与线路：\n')
        # for layer in job.SignalLayers:
        #     info = pcs_step.INFO(f'-t check -e %s/%s/%s -d MEAS -o action=1+category=pth_ar+layer={layer},units=mm' % (
        #     jobname, pcs_step.name, checklist.name))
        #     res = ''
        #     if info:
        #         res = min([float(l.split()[2]) for l in info])
        #     result.append(f"{layer}:{res}\t")
        self.tableWidget.setItem(item, 2, QTableWidgetItem(''.join(result)))
        self.statusbar.showMessage(f'{self.items[item][0]}已完成')
        app.processEvents()

    def get_soldermask_analysis(self, item):
        self.statusbar.showMessage(f'正在执行{self.items[item][0]}')
        result, data = [], []
        layers = job.matrix.returnRows('board', 'solder_mask')
        layers = list(filter(lambda x: x in ('gts', 'gbs'), layers))
        pp_layer = ';'.join(layers)
        pcs_step = job.steps.get('pcs')
        pcs_step.initStep()
        checklist = gen.Checklist(pcs_step, 'pcs_analysis_checklist', 'valor_analysis_sm')
        checklist.action()
        # checklist.erf('Outer (Mils)')
        checklist.COM(f'chklist_cupd,chklist=valor_analysis_sm,nact=1,params=((pp_layers={pp_layer})(pp_ar=355.6)(pp_coverage=203.2)(pp_sm2r=406.4)(pp_sliver=203.2)(pp_spacing=228.6)(pp_bridge=355.6)(pp_min_clear_overlap=127)(pp_tests=Drill\;Pads\;Coverage\;Rout\;Bridge\;Sliver\;Missing\;Spacing)(pp_selected=All)(pp_use_compensated_rout=No)),mode=regular')
        checklist.run()
        checklist.clear()
        checklist.COM(
            f'chklist_cupd,chklist=valor_analysis_sm,nact=1,params=((pp_layers={pp_layer})(pp_ar=355.6)(pp_coverage=203.2)(pp_sm2r=406.4)(pp_sliver=203.2)(pp_spacing=228.6)(pp_bridge=355.6)(pp_min_clear_overlap=127)(pp_tests=Drill\;Pads\;Coverage\;Rout\;Bridge\;Sliver\;Missing\;Spacing)(pp_selected=All)(pp_use_compensated_rout=No)),mode=regular')
        checklist.copy()
        if checklist.name in pcs_step.checks:
            pcs_step.deleteCheck(checklist.name)
        pcs_step.createCheck(checklist.name)
        pcs_step.pasteCheck(checklist.name)
        result.append('阻焊间距：\n')
        for layer in layers:
            info = pcs_step.INFO(f'-t check -e %s/%s/%s -d MEAS -o action=1+category=local_spacing+layer={layer},units=mm' % (
                jobname, pcs_step.name, checklist.name))
            res = ''
            if info:
                res = min([float(l.split()[2]) for l in info])
            result.append(f"{layer}:{res}\t")
        result.append('\n阻焊桥宽：\n')
        for layer in layers:
            info = pcs_step.INFO(
                f'-t check -e %s/%s/%s -d MEAS -o action=1+category=pad2pad_bridge+layer={layer},units=mm' % (
                    jobname, pcs_step.name, checklist.name))
            res = ''
            if info:
                res = min([float(l.split()[2]) for l in info])
            result.append(f"{layer}:{res}\t")
        # result.append('\n阻焊盖线宽度：\n')
        # for layer in layers:
        #     info = pcs_step.INFO(f'-t check -e %s/%s/%s -d MEAS -o action=1+category=coverage+layer={layer},units=mm' % (
        #         jobname, pcs_step.name, checklist.name))
        #     res = ''
        #     if info:
        #         res = min([float(l.split()[2]) for l in info])
        #     result.append(f"{layer}:{res}\t")
        result.append('\n让位间距：\n')
        for layer in layers:
            info = pcs_step.INFO(
                f'-t check -e %s/%s/%s -d MEAS -o action=1+category=coverage+layer={layer},units=mm' % (
                    jobname, pcs_step.name, checklist.name))
            res = ''
            if info:
                res = min([float(l.split()[2]) for l in info])
            result.append(f"{layer}:{res}\t")
        self.tableWidget.setItem(item, 2, QTableWidgetItem(''.join(result)))
        self.statusbar.showMessage(f'{self.items[item][0]}已完成')
        app.processEvents()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':res/demo.png'))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    oneKeyAnalysis = OneKeyAnalysis()
    oneKeyAnalysis.show()
    sys.exit(app.exec_())
