#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AutoAnalysis.py
   @author:zl
   @time:2024/7/12 10:53
   @software:PyCharm
   @desc:一键分析
"""
import datetime
import os
import re
import sys

import pandas as pd
import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem, QHeaderView, QTableWidget, QMenu, QAction, \
    QMessageBox

import OneKeyAnalysisUI as ui

import genClasses as gen
import res_rc


class OneKeyAnalysis(QMainWindow, ui.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.label_title.setText(f'料号：{jobname}')
        self.items = {
            0: ['pcs/set尺寸', self.get_pcs_set_size],
            1: ['线路层残铜率', self.get_signal_copper],
            2: ['ccd孔数量', self.get_ccd_drill_count],
            # 1: ['pcs/set尺寸', self.get_pcs_set_size],
        }
        self.export_path = 'D:/一键分析结果'
        header = ['序号', '分析项', '分析结果']
        self.tableWidget.setColumnCount(len(header))
        self.tableWidget.setHorizontalHeaderLabels(header)
        self.tableWidget.setRowCount(len(self.items))
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.setColumnWidth(0, 36)
        # self.tableWidget.setColumnWidth(0, 20)
        self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tableWidget.setSelectionBehavior(QHeaderView.SelectRows)
        self.tableWidget.setSelectionMode(QHeaderView.SingleSelection)
        self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableWidget.customContextMenuRequested.connect(self.popMenu)
        self.loadData()
        self.tableWidget.itemClicked.connect(self.showResult)
        self.splitter.setSizes([500, 200])
        self.pushButton_export.setIcon(qtawesome.icon('mdi6.file-export-outline', color='white'))
        self.pushButton_pause.setIcon(qtawesome.icon('fa.pause-circle-o', color='white'))
        self.pushButton_exec.setIcon(qtawesome.icon('fa.download', color='white'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='white'))
        self.pushButton_export.clicked.connect(self.export)
        self.pushButton_pause.clicked.connect(self.pause)
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

    def export(self):
        datas = []
        for row in range(self.tableWidget.rowCount()):
            datas.append([self.tableWidget.item(row, 0).text(), self.tableWidget.item(row, 1).text(), self.tableWidget.item(row, 2).text()])
        df = pd.DataFrame(datas, columns=['序号', '分析项', '分析结果'])
        filename = f'{jobname}分析结果_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
        if not os.path.exists(self.export_path):
            os.mkdir(self.export_path)
        df.to_excel(f'{self.export_path}/{filename}', index=False)
        QMessageBox.information(self, '提示', f'导出成功!\n导出路径为：{self.export_path}')

    def pause(self):
        self.hide()
        job.PAUSE('Pause Script')
        self.show()

    def exec(self):
        for item in self.items:
            self.tableWidget.item(item, 2).setText('')
        for item in self.items:
            self.items.get(item)[1](item)

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
        runLocal.triggered.connect(lambda: self.items.get(item)[1](item))
        menu.exec_(QCursor.pos())

    def showResult(self):
        row = self.tableWidget.currentRow()
        self.label_item.setText(self.tableWidget.item(row, 1).text())
        self.textEdit.setText(self.tableWidget.item(row, 2).text())

    def get_pcs_set_size(self, item):
        self.statusbar.showMessage(f'正在执行{self.items[item][0]}')
        result = []
        xsize, ysize = job.steps.get('pcs').profile2.xsize, job.steps.get('pcs').profile2.ysize
        result.append(f'pcs 宽度：{"%.5f" % xsize}mm, 高度：{"%.5f" % ysize}mm')
        xsize, ysize = job.steps.get('set').profile2.xsize, job.steps.get('set').profile2.ysize
        result.append(f'set 宽度：{"%.5f" % xsize}mm, 高度：{"%.5f" % ysize}mm')
        self.tableWidget.setItem(item, 2, QTableWidgetItem('\n'.join(result)))
        self.statusbar.showMessage(f'{self.items[item][0]}已完成')
        app.processEvents()

    def get_signal_copper(self, item):
        self.statusbar.showMessage(f'正在执行{self.items[item][0]}')
        result = []
        pnl_step = job.steps.get('pnl')
        pnl_step.initStep()
        for signal in job.SignalLayers:
            pnl_step.COM(
                f'copper_area,layer1={signal},layer2=,drills=yes,consider_rout=no,ignore_pth_no_pad=no,drills_source=matrix,thickness=0,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes')
            area, percent = pnl_step.COMANS.split()
            result.append(f'{signal}: {area}sq/mm({percent})%')
        self.tableWidget.setItem(item, 2, QTableWidgetItem('\n'.join(result)))
        self.statusbar.showMessage(f'{self.items[item][0]}已完成')
        app.processEvents()

    def get_ccd_drill_count(self, item):
        self.statusbar.showMessage(f'正在执行{self.items[item][0]}')
        result = []
        pnl_step = job.steps.get('pnl')
        pnl_step.initStep()
        rows = job.matrix.returnRows()
        ccds = filter(lambda row: re.match('ccd\d+$', row), rows)
        for ccd in ccds:
            pnl_step.affect(ccd)
            pnl_step.selectAll()
            count = pnl_step.Selected_count()
            result.append(f"层{ccd}孔数量：{count}")
            pnl_step.unaffectAll()
        self.tableWidget.setItem(item, 2, QTableWidgetItem('\n'.join(result)))
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
