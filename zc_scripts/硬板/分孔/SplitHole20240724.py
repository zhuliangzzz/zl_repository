#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:SplitHole.py
   @author:zl
   @time:2024/7/18 16:02
   @software:PyCharm
   @desc:
   功能： 打开-解析-分孔-退出
"""
import os
import re
import sys

import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QMainWindow, QApplication, QHeaderView, QFileDialog, QMessageBox, \
    QTableWidgetItem, QTextEdit, QLabel

import SplitHoleUI as ui
import genClasses as gen
import res_rc


class SplitHole(QMainWindow, ui.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.label_title.setText(f'Job: {jobname} Step: {stepname}')
        # 线路层数
        self.layer_num = job.SignalNum
        self.action_open.setIcon(qtawesome.icon('fa.folder-open', color='orange'))
        self.action_import.setIcon(qtawesome.icon('fa.download', color='orange'))
        self.action_split.setIcon(qtawesome.icon('fa.play-circle', color='orange'))
        self.action_exit.setIcon(qtawesome.icon('fa.sign-out', color='orange'))
        self.label.setText(f'<font style="color:red;font-weight:bold;">选择文件：</font>')
        drr_header = ['Layer Pair', 'ASCII RoundHoles File', '重命名', '文件是否存在']
        self.tableWidget_drr_info.setColumnCount(len(drr_header))
        self.tableWidget_drr_info.setHorizontalHeaderLabels(drr_header)
        self.tableWidget_drr_info.setColumnWidth(2, 50)
        self.tableWidget_drr_info.setColumnWidth(3, 100)
        self.tableWidget_drr_info.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tableWidget_drr_info.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tableWidget_drr_info.verticalHeader().hide()
        self.tableWidget_drr_info.setEditTriggers(QHeaderView.NoEditTriggers)
        # hole
        hole_header = ['目标盲孔', '孔数', '所需钻孔']
        self.tableWidget_hole_info.setColumnCount(len(hole_header))
        self.tableWidget_hole_info.setHorizontalHeaderLabels(hole_header)
        self.tableWidget_hole_info.setColumnWidth(0, 60)
        self.tableWidget_hole_info.setColumnWidth(1, 80)
        # self.tableWidget_hole_info.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tableWidget_hole_info.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tableWidget_hole_info.verticalHeader().hide()
        self.tableWidget_hole_info.setEditTriggers(QHeaderView.NoEditTriggers)
        self.menuOpen.triggered.connect(self.pressAction)

    def pressAction(self, act):
        if act.text() == '打开DRR文件':
            file_dialog = QFileDialog()
            OpenFilename = file_dialog.getOpenFileName(self, "选择DRR文件", '\\\\zhzc-sr-0002\me资料共享文件夹',
                                                       'All Files(*.DRR)')
            filename = OpenFilename[0]
            if not filename:
                QMessageBox.warning(self, '提示', '请选择DRR文件')
                return
            self.label.setText(
                f'<font style="color:green;font-weight:bold;">选择文件：</font><span style="color:brown;">{filename}</span>')
            self.parseFile(filename)
        elif act.text() == '导入/重命名':
            self.import_and_rename()
        elif act.text() == '分孔':
            self.load_hole_info()
        elif act.text() == '退出':
            sys.exit()

    def parseFile(self, filename):
        self.file_dir = os.path.dirname(filename)
        # 料号名
        # path = filename.replace('//', '')
        # jobname = path.split('/')[5]
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.read()
        if not lines:
            QMessageBox.warning(self, '提示', '文件错误')
            return
        result = re.findall('Layer Pair(.*)\nASCII RoundHoles File(.*)\n', lines, re.M)
        datas = []
        for layer, file in result:
            layer, file = layer.replace(':', ''), file.replace(':', '')
            layer = layer.strip()
            file = file.strip()
            file_exist = True if os.path.isfile(os.path.join(self.file_dir, file)) else False
            layer1, layer2 = layer.split('to', 1)
            layer1 = layer1.strip()
            layer2 = layer2.strip()
            if layer1 == 'Top Layer':
                layer1 = 1
            elif layer1 == 'Bottom Layer':
                layer1 = self.layer_num
            elif layer1.startswith('S'):
                layer1 = layer1.replace('S', '')
            if layer2 == 'Top Layer':
                layer2 = 1
            elif layer2 == 'Bottom Layer':
                layer2 = self.layer_num
            elif layer2.startswith('S'):
                layer2 = layer2.replace('S', '')
            new_name = f'{layer1}-{layer2}'
            datas.append([layer, file, new_name, file_exist])
        self.tableWidget_drr_info.setRowCount(len(datas))
        for row, data in enumerate(datas):
            self.tableWidget_drr_info.setItem(row, 0, QTableWidgetItem(data[0]))
            self.tableWidget_drr_info.setItem(row, 1, QTableWidgetItem(data[1]))
            self.tableWidget_drr_info.setItem(row, 2, QTableWidgetItem(data[2]))
            color = 'green' if data[3] else 'red'
            text = '√' if data[3] else '×'
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(QColor(color))
            self.tableWidget_drr_info.setItem(row, 3, item)
        self.statusbar.showMessage('DRR文件解析完成！')

    def import_and_rename(self):
        if not self.tableWidget_drr_info.rowCount():
            QMessageBox.warning(self, '提示', '请先选择DRR文件')
            return
        for row in range(self.tableWidget_drr_info.rowCount()):
            if self.tableWidget_drr_info.item(row, 3).text() == '×':
                QMessageBox.warning(self, '提示', '文件缺失无法导入')
                return
        step.initStep()
        nf1, nf2 = 3, 4
        for row in range(self.tableWidget_drr_info.rowCount()):
            input_file = self.tableWidget_drr_info.item(row, 1).text()
            layer = self.tableWidget_drr_info.item(row, 2).text()
            step.COM('input_manual_reset')
            step.COM(
                f'input_manual_set,path={self.file_dir}/{input_file},job={jobname},step={stepname},format=Excellon2,data_type=ascii,units=mm,coordinates=absolute,zeroes=trailing,nf1={nf1},nf2={nf2},decimal=no,separator=nl,tool_units=mm,layer={layer},wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3')
            step.COM('input_manual,script_path=')
        job.matrix.refresh()
        for row in range(self.tableWidget_drr_info.rowCount()):
            layer = self.tableWidget_drr_info.item(row, 2).text()
            job.matrix.modifyRow(layer, context='board', type='drill')
            layer_start, layer_end = layer.split('-')
            job.matrix.setDrillThrough(layer, f'l{layer_start}', f'l{layer_end}')
        self.statusbar.showMessage('导入完成！')

    def load_hole_info(self):
        self.tableWidget_hole_info.setRowCount(0)
        self.tableWidget_hole_info.clearContents()
        holes, drill_list, merge_list = [], [], []
        if self.tableWidget_drr_info.rowCount():
            for row in range(self.tableWidget_drr_info.rowCount()):
                layer = self.tableWidget_drr_info.item(row, 2).text()
                layer_start, layer_end = layer.split('-')
                layer_start, layer_end = int(layer_start), int(layer_end)
                merge_ = []
                if layer_start < self.layer_num / 2:
                    if layer_start not in holes:
                        holes.append(layer_start)
                        drill_list.append(f's{layer_start}-{layer_start + 1}')
                        for a in range(1, layer_start + 1):
                            for b in range(layer_start + 1, self.layer_num):
                                drill = f'{a}-{b}'
                                if step.isLayer(drill):
                                    merge_.append(drill)
                        merge_list.append(merge_)
                else:
                    if layer_end not in holes:
                        holes.append(layer_end)
                        drill_list.append(f's{layer_end}-{layer_end - 1}')
                        for a in range(1, layer_end):
                            for b in range(layer_end, self.layer_num + 1):
                                drill = f'{a}-{b}'
                                if step.isLayer(drill):
                                    merge_.append(drill)
                        merge_list.append(merge_)
        else:
            drills = sorted(filter(lambda d: re.match('\d+-\d+$', d), job.matrix.returnRows('board', 'drill')))
            for layer in drills:
                layer_start, layer_end = layer.split('-')
                layer_start, layer_end = int(layer_start), int(layer_end)
                merge_ = []
                if layer_start < self.layer_num / 2:
                    if layer_start not in holes:
                        holes.append(layer_start)
                        drill_list.append(f's{layer_start}-{layer_start + 1}')
                        for a in range(1, layer_start + 1):
                            for b in range(layer_start + 1, self.layer_num):
                                drill = f'{a}-{b}'
                                if step.isLayer(drill):
                                    merge_.append(drill)
                        merge_list.append(merge_)
                else:
                    if layer_end not in holes:
                        holes.append(layer_end)
                        drill_list.append(f's{layer_end}-{layer_end - 1}')
                        for a in range(1, layer_end):
                            for b in range(layer_end, self.layer_num + 1):
                                drill = f'{a}-{b}'
                                if step.isLayer(drill):
                                    merge_.append(drill)
                        merge_list.append(merge_)
        # drill_list = sorted(drill_list, key=lambda x: int(x.split('-')[0].replace('s', '')))
        self.tableWidget_hole_info.setRowCount(len(drill_list))
        for row, drill in enumerate(drill_list):
            self.tableWidget_hole_info.setItem(row, 0, QTableWidgetItem(drill))
            label = QLabel()
            label.setTextInteractionFlags(Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)
            label.setWordWrap(True)
            label.setText(' '.join(merge_list[row]))
            self.tableWidget_hole_info.setCellWidget(row, 2, label)
        for row in range(self.tableWidget_hole_info.rowCount() - 1, -1, -1):
            drill_layer = self.tableWidget_hole_info.item(row, 0).text()
            merge_drills = self.tableWidget_hole_info.cellWidget(row, 2).text().split(' ')
            if step.isLayer(drill_layer):
                step.removeLayer(drill_layer)
            job.matrix.addLayer(drill_layer, 1, 'board', 'drill')
            for drill in merge_drills:
                step.affect(drill)
            step.copySel(drill_layer)
            step.unaffectAll()
            step.affect(drill_layer)
            step.selectAll()
            count = step.Selected_count()
            step.unaffectAll()
            item = QTableWidgetItem(str(count))
            item.setTextAlignment(Qt.AlignCenter)
            self.tableWidget_hole_info.setItem(row, 1, item)
        self.statusbar.showMessage('分孔完成！')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':res/demo.png'))
    jobname = os.environ.get('JOB')
    if not jobname:
        QMessageBox.warning(None, '提示', '请打开需要分孔的料号')
        sys.exit()
    stepname = os.environ.get('STEP')
    if not stepname:
        QMessageBox.warning(None, '提示', '请打开分孔的step')
        sys.exit()
    job = gen.Job(jobname)
    step = job.steps.get(stepname)
    splitHole = SplitHole()
    splitHole.show()
    sys.exit(app.exec_())
