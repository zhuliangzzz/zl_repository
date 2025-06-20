#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:UpdateNameAndDate.py
   @author:zl
   @time:2024/9/2 16:48
   @software:PyCharm
   @desc:料号和日期刷新
"""
import datetime
import os
import re
import sys

import qtawesome
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox, QWidget, QAbstractItemView
import UpdateNameAndDateUI as ui
import genClasses as gen
import res_rc


class UpdateNameAndDate(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.user = job.getUser()
        self.label_title.setText(f'Job:{jobname}\tStep:{step.name}')
        layers = job.matrix.returnRows('board', 'signal')
        self.listWidget.addItems(layers)
        self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.listWidget.itemClicked.connect(self.item_click)
        self.checkBox_jobname.setChecked(True)
        self.checkBox_date.setChecked(True)
        self.pushButton_exec.setIcon(qtawesome.icon('fa.download', color='white'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='white'))
        self.checkBox_select_all.clicked.connect(self.select_all)
        self.pushButton_exec.clicked.connect(self.exec)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            '''
            QListWidget::Item{height:22px;} QListWidget::Item:selected{background-color:#459B81;}
            QPushButton{font:10pt;background-color:#459B81;color:white;} QPushButton:hover{background:#333;} #QCheckBox::indicator:checked{background:#459B81;} ''')

    def select_all(self):
        if self.checkBox_select_all.isChecked():
            self.listWidget.selectAll()
        else:
            self.listWidget.clearSelection()

    def item_click(self):
        select_all = False
        select_count = 0
        for i in range(self.listWidget.count()):
            if self.listWidget.item(i).isSelected():
                select_count += 1
        if select_count == self.listWidget.count():
            select_all = True
        if select_all:
            self.checkBox_select_all.setChecked(True)
        else:
            self.checkBox_select_all.setChecked(False)

    def exec(self):
        layers = [item.text() for item in self.listWidget.selectedItems()]
        if not layers:
            QMessageBox.warning(self, 'tips', '请选择层')
            return
        step.initStep()
        if self.checkBox_jobname.isChecked():
            for layer in layers:
                step.affect(layer)
                step.setFilterTypes('text')
                # step.setTextFilter(jobname)
                step.selectAll()
                step.resetFilter()
                index_array = []
                if step.Selected_count():
                    lines = step.INFO(
                        '-t layer -e %s/%s/%s -d FEATURES -o feat_index+select,units=mm' % (jobname, step.name, layer))
                    del lines[0]
                    for line in lines:
                        result = re.search(r'^#(\d+)\s+#T.+\'[A-Za-z]{2}\d{2}[A-Za-z]{2}.+\'', line)  # 匹配料号名的字符串
                        if result:
                            index_array.append(int(result.group(1)))
                    step.selectNone()
                    if index_array:
                        for index in index_array:
                            step.selectByIndex(layer, index)
                        step.changeText(f'{jobname} {layer}')
                    step.selectNone()
                step.unaffectAll()
        if self.checkBox_date.isChecked():
            pieces = self.get_pcs_num()
            xsize = step.profile2.xsize
            ysize = step.profile2.ysize
            string = f'{xsize}*{ysize}={pieces}PCS/PNL {datetime.date.today().year}.{"%02d" % datetime.date.today().month}.{datetime.date.today().day} {self.user.upper()}'
            for layer in layers:
                step.affect(layer)
                step.setFilterTypes('text')
                step.setTextFilter('*pcs/pnl*')
                step.selectAll()
                step.resetFilter()
                if step.Selected_count():
                    lines = step.INFO(
                        '-t layer -e %s/%s/%s -d features -o select,units=mm' % (jobname, step.name, layer))
                    del lines[0]
                    text = lines[0].split("'")[1]
                    if text != string:
                        res = QMessageBox.warning(None, '提醒', '检测%s层板边日期需要更新为\n%s\n是否修改' % (layer, string), QMessageBox.Yes | QMessageBox.No)
                        if res == QMessageBox.Yes:
                            step.changeText(string)
                        else:
                            step.unaffectAll()
                            sys.exit()
                step.unaffectAll()
        QMessageBox.information(self, 'tips', '执行完成！')

    def get_pcs_num(self):
        steps = step.info.get('gREPEATstep')  # 获取set列表
        pcs_num_map = {}
        pcs_name = set()
        for s in steps:
            if 'set' in s:
                pcs_list = list(
                    filter(lambda repeat_: str(repeat_).startswith('pcs'), job.steps.get(s).info.get('gREPEATstep')))
                pcs_name.update(pcs_list)  # 获取每个set中的pcs列表
                if s not in pcs_num_map:
                    pcs_num_map[s] = 0
                pcs_num_map[s] += len(pcs_list)
        if len(pcs_name) > 1:
            return min(pcs_num_map.values())
        else:
            return sum(pcs_num_map.values())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':/res/demo.png'))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    if not job.steps.get('pnl'):
        QMessageBox.warning(None, 'tips', '没有pnl！')
        sys.exit()
    step = job.steps.get('pnl')
    update_pnl_date = UpdateNameAndDate()
    update_pnl_date.show()
    sys.exit(app.exec_())
