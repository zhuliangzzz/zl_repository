#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:UpdateScaleTestPadCoor.py
   @author:zl
   @time:2024/9/6 15:23
   @software:PyCharm
   @desc:
"""
import os
import sys

import qtawesome
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QAbstractItemView

import UpdateScaleTestPadCoorUI as ui
import genClasses as gen
import res_rc

class UpdateScaleTestPadCoor(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.toggle_flag = False
        self.label_title.setText(f'Job: {jobname}')
        self.listWidget.addItems(job.SignalLayers)
        self.listWidget.itemClicked.connect(self.itemClicked)
        self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.pushButton_toggle_select.clicked.connect(self.toggle_select)
        self.pushButton_toggle_select.setIcon(qtawesome.icon('mdi.check-decagram', color='white'))
        self.pushButton_exec.setIcon(qtawesome.icon('fa.download', color='white'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='white'))
        self.pushButton_exec.clicked.connect(self.exec)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet('''
         QListWidget::Item{height:22px;} QListWidget::Item:selected{background-color:#0081a6;color:white;}
            QPushButton{font:10pt;background-color:#0081a6;color:white;} QPushButton:hover{background:#333;}
            #label_2{background-color:#35B2D4;color:white;}
        ''')

    def toggle_select(self):
        if self.toggle_flag:
            self.toggle_flag = False
            self.listWidget.clearSelection()
            self.pushButton_toggle_select.setText('全选')
        else:
            self.toggle_flag = True
            self.listWidget.selectAll()
            self.pushButton_toggle_select.setText('取消')

    def itemClicked(self):
        select_all = False
        select_count = 0
        for i in range(self.listWidget.count()):
            if self.listWidget.item(i).isSelected():
                select_count += 1
        if select_count == self.listWidget.count():
            select_all = True
        if select_all:
            self.toggle_flag = True
            self.pushButton_toggle_select.setText('取消')
        else:
            self.toggle_flag = False
            self.pushButton_toggle_select.setText('全选')

    def exec(self):
        layers = [item.text() for item in self.listWidget.selectedItems()]
        if not layers:
            QMessageBox.warning(self, 'tips', '请选择层')
            return
        step.initStep()
        for layer in layers:
            step.affect(layer)
            step.selectSymbol('1-sc-mark')
            step.resetFilter()
            if step.Selected_count() != 4:
                step.unaffectAll()
                self.textEdit_log.append(f'<span style="color:red">检测到{layer}涨缩测试pad(1-sc-mark)数量不为4,无法确定四个坐标信息</span>')
                continue
            info = step.Features_INFO(layer, mode='select, units=mm')
            left_ = step.sr2.xmin
            right_ = step.sr2.xmax
            leftlist, rightlist = [], []
            for line in info:
                if float(line[1]) < left_:
                    leftlist.append((float(line[1]), float(line[2])))
                if float(line[1]) > right_:
                    rightlist.append((float(line[1]), float(line[2])))
            # 排序
            leftlist.sort(key=lambda x: x[1])
            rightlist.sort(key=lambda x: x[1])

            origin = leftlist[0]
            topleft = leftlist[1]
            topright = rightlist[1]
            botright = rightlist[0]
            self.textEdit_log.append(f'检测到{layer}涨缩测试pad坐标：左下角原点{origin[0],origin[1]} 左上角{topleft[0], topleft[1]} 右上角{topright[0], topright[1]} 右下角{botright[0], botright[1]}')
            app.processEvents()
            # topleft
            y = topleft[1] - origin[1]
            step.clearSel()
            step.setFilterTypes('text')
            step.selectRectangle(topleft[0] - 2, topleft[1] + 0.8, topleft[0], topleft[1] - 0.8)
            if step.Selected_count() == 1:
                step.changeText(f'{y:g}')
                self.textEdit_log.append(f'左上角竖直距离: {y:g}  修改成功!')
                app.processEvents()
            step.clearSel()
            y = topright[1] - origin[1]
            step.selectRectangle(topright[0], topright[1] + 0.8, topright[0] + 2, topright[1] - 0.8)
            if step.Selected_count() == 1:
                step.changeText(f'{y:g}')
                self.textEdit_log.append(f'右上角竖直距离: {y:g}  修改成功!')
                app.processEvents()
            step.clearSel()
            x = botright[0] - origin[0]
            y = botright[1] - origin[1]
            step.selectRectangle(botright[0] - 1, botright[1], botright[0] + 1, botright[1] - 2)
            if step.Selected_count() == 1:
                step.changeText(f'{x:g}')
                self.textEdit_log.append(f'右下角水平距离: {x:g}  修改成功!')
                app.processEvents()
            step.clearSel()
            step.selectRectangle(botright[0], botright[1] - 1, botright[0] + 2, botright[1] + 1)
            if step.Selected_count() == 1:
                step.changeText(f'{y:g}')
                self.textEdit_log.append(f'右下角竖直距离: {y:g}  修改成功!')
                app.processEvents()
            step.resetFilter()
            step.unaffectAll()
        QMessageBox.information(self, '提示', '执行完毕!')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':res/demo.png'))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    if not job.steps.get('pnl'):
        QMessageBox.warning(None, 'tips', '没有pnl！')
        sys.exit()
    step = job.steps.get('pnl')
    ex = UpdateScaleTestPadCoor()
    ex.show()
    sys.exit(app.exec_())
