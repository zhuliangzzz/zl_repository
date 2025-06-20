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
    20240801 与韦厚勇确认阻焊选镀的做法：profile外的去掉， 用阻焊选镀层去掏整个profile的铜皮  ldi料号命名： 料号名-所选的阻焊选镀层名拼接 没有选阻焊选镀层 则命名为：料号名-选的所有层拼接
    20240821 漏加金面积提示
    20240829 增加对ldi资料分段输出
    20240830 增加对aoi资料分段输出
"""
import os
import re
import sys

import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor, QIcon, QIntValidator
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
        self.groupBox_scale_mirror.setVisible(False)
        self.groupBox_split_ldi.setVisible(False)
        # 分段
        self.comboBox_split.addItems(['', '上', '下'])
        self.comboBox_split.currentIndexChanged.connect(self.changeRotateEnable)
        self.checkBox_split_rotate.setEnabled(False)
        #
        self.lineEdit_x_scale.setValidator(QIntValidator())
        self.lineEdit_y_scale.setValidator(QIntValidator())
        self.lineEdit_x_scale.setText('0')
        self.lineEdit_y_scale.setText('0')
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

    def changeRotateEnable(self):
        if self.comboBox_split.currentIndex():
            self.checkBox_split_rotate.setEnabled(True)
        else:
            self.checkBox_split_rotate.setEnabled(False)

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
        # 验证涨缩系数
        top = gen.Top()
        bak = f'{jobname}-bak'
        top.VOF()
        top.deleteJob(bak)
        top.VON()
        top.copyJob(jobname, bak, 'genesis')
        job.open(1)
        if self.radioButton_aoi.isChecked():
            if self.checkBox_split.isChecked(): # aoi分段   b-aoi 上半部分   a-aoi 下半部分
                if 'pcs' not in job.steps:
                    QMessageBox.warning(self, '警告', '没有pcs无法分段')
                    return
                another_aoi = f'{jobname}-a-aoi'
                top.copyJob(jobname, another_aoi, 'genesis') # 另一部分
                # 当前
                dest = f'{jobname}-b-aoi'
                delete_row = filter(lambda row: row not in layers, job.matrix.getInfo().get('gROWname'))
                for row in delete_row:
                    job.matrix.deleteRow(row)
                pnl_step = job.steps.get('pnl')
                if pnl_step:
                    pnl_step.initStep()
                    for layer in layers:
                        pnl_step.affect(layer)
                    pnl_step.selectRectangle(pnl_step.profile2.xmin, pnl_step.profile2.ymin, pnl_step.profile2.xmax,
                                             pnl_step.profile2.ymax)
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
                    # pnl_step.close()
                # 切pcs
                pcs_step = job.steps.get('pcs')
                pcs_step.initStep()
                # 原先的profile
                prof = f'prof+++{pcs_step.pid}'
                pcs_step.prof_to_rout(prof, 100)
                clip_layer = f'clip+++{pcs_step.pid}'
                pcs_step.createLayer(clip_layer)
                pcs_step.affect(clip_layer)
                pcs_step.addRectangle(pcs_step.profile2.xmin - 30, pcs_step.profile2.ycenter - 5, pcs_step.profile2.xmax + 30, pcs_step.profile2.ymin - 355)
                pcs_step.unaffectAll()
                for layer in layers:
                    pcs_step.affect(layer)
                pcs_step.affect(prof)
                pcs_step.clip_area(margin=0, ref_layer=clip_layer)
                # pcs_step.Transform(oper='rotate', x_anchor=pcs_step.profile2.xcenter, y_anchor=pcs_step.profile2.ycenter, angle=180)
                pcs_step.unaffectAll()
                pcs_step.affect(prof)
                pcs_step.surf_outline()
                pcs_step.selectAll()
                pcs_step.selectCreateProf()
                pcs_step.unaffectAll()
                # pcs_step.close()
                set_step = job.steps.get('set')
                if set_step:
                    set_step.initStep()
                    # 原先的profile
                    # prof = f'prof+++{set_step.pid}'
                    set_step.prof_to_rout(prof, 100)
                    # clip_layer = f'clip+++{set_step.pid}'
                    # set_step.createLayer(clip_layer)
                    set_step.affect(clip_layer)
                    set_step.addRectangle(set_step.profile2.xmin - 30, set_step.profile2.ycenter - 5,
                                          set_step.profile2.xmax + 30, set_step.profile2.ymin - 355)
                    set_step.unaffectAll()
                    for layer in layers:
                        set_step.affect(layer)
                    set_step.affect(prof)
                    set_step.clip_area(margin=0, ref_layer=clip_layer)
                    # set_step.Transform(oper='rotate', x_anchor=set_step.profile2.xcenter, y_anchor=set_step.profile2.ycenter, angle=180)
                    set_step.unaffectAll()
                    set_step.affect(prof)
                    set_step.surf_outline()
                    set_step.selectAll()
                    set_step.selectCreateProf()
                    set_step.unaffectAll()
                pnl_step = job.steps.get('pnl')
                if pnl_step:
                    pnl_step.initStep()
                    # 原先的profile
                    # prof = f'prof+++{set_step.pid}'
                    pnl_step.prof_to_rout(prof, 100)
                    # clip_layer = f'clip+++{set_step.pid}'
                    # set_step.createLayer(clip_layer)
                    pnl_step.affect(clip_layer)
                    pnl_step.addRectangle(pnl_step.profile2.xmin - 30, pnl_step.profile2.ycenter - 5,
                                          pnl_step.profile2.xmax + 30, pnl_step.profile2.ymin - 355)
                    pnl_step.unaffectAll()
                    for layer in layers:
                        pnl_step.affect(layer)
                    pnl_step.affect(prof)
                    pnl_step.clip_area(margin=0, ref_layer=clip_layer)
                    # pnl_step.Transform(oper='rotate', x_anchor=pnl_step.profile2.xcenter, y_anchor=pnl_step.profile2.ycenter, angle=180)
                    pnl_step.unaffectAll()
                    pnl_step.affect(prof)
                    pnl_step.surf_outline()
                    pnl_step.selectAll()
                    pnl_step.selectCreateProf()
                    pnl_step.unaffectAll()
                pcs_step.removeLayer(prof)
                pcs_step.removeLayer(clip_layer)
                job.save()
                job.close(1)
                top.renameJob(jobname, dest, 'genesis')
                # a-aoi
                another_aoi_job = gen.Job(another_aoi)
                another_aoi_job.open(1)
                delete_row = filter(lambda row: row not in layers, another_aoi_job.matrix.getInfo().get('gROWname'))
                for row in delete_row:
                    another_aoi_job.matrix.deleteRow(row)
                pnl_step = another_aoi_job.steps.get('pnl')
                if pnl_step:
                    pnl_step.initStep()
                    for layer in layers:
                        pnl_step.affect(layer)
                    pnl_step.selectRectangle(pnl_step.profile2.xmin, pnl_step.profile2.ymin, pnl_step.profile2.xmax,
                                             pnl_step.profile2.ymax)
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
                    # pnl_step.close()
                # 切pcs
                pcs_step = another_aoi_job.steps.get('pcs')
                pcs_step.initStep()
                # 原先的profile
                prof = f'prof+++{pcs_step.pid}'
                pcs_step.prof_to_rout(prof, 100)
                clip_layer = f'clip+++{pcs_step.pid}'
                pcs_step.createLayer(clip_layer)
                pcs_step.affect(clip_layer)
                pcs_step.addRectangle(pcs_step.profile2.xmin - 30, pcs_step.profile2.ycenter + 5,
                                      pcs_step.profile2.xmax + 30, pcs_step.profile2.ymax + 355)
                pcs_step.unaffectAll()
                for layer in layers:
                    pcs_step.affect(layer)
                pcs_step.affect(prof)
                pcs_step.clip_area(margin=0, ref_layer=clip_layer)
                pcs_step.unaffectAll()
                pcs_step.affect(prof)
                pcs_step.surf_outline()
                pcs_step.selectAll()
                pcs_step.selectCreateProf()
                pcs_step.unaffectAll()
                # pcs_step.close()
                set_step = another_aoi_job.steps.get('set')
                if set_step:
                    set_step.initStep()
                    # 原先的profile
                    # prof = f'prof+++{set_step.pid}'
                    set_step.prof_to_rout(prof, 100)
                    # clip_layer = f'clip+++{set_step.pid}'
                    # set_step.createLayer(clip_layer)
                    set_step.affect(clip_layer)
                    set_step.addRectangle(set_step.profile2.xmin - 30, set_step.profile2.ycenter + 5,
                                          set_step.profile2.xmax + 30, set_step.profile2.ymax + 355)
                    set_step.unaffectAll()
                    for layer in layers:
                        set_step.affect(layer)
                    set_step.affect(prof)
                    set_step.clip_area(margin=0, ref_layer=clip_layer)
                    set_step.unaffectAll()
                    set_step.affect(prof)
                    set_step.surf_outline()
                    set_step.selectAll()
                    set_step.selectCreateProf()
                    set_step.unaffectAll()
                pnl_step = another_aoi_job.steps.get('pnl')
                if pnl_step:
                    pnl_step.initStep()
                    # 原先的profile
                    # prof = f'prof+++{set_step.pid}'
                    pnl_step.prof_to_rout(prof, 100)
                    # clip_layer = f'clip+++{set_step.pid}'
                    # set_step.createLayer(clip_layer)
                    pnl_step.affect(clip_layer)
                    pnl_step.addRectangle(pnl_step.profile2.xmin - 30, pnl_step.profile2.ycenter + 5,
                                          pnl_step.profile2.xmax + 30, pnl_step.profile2.ymax + 355)
                    pnl_step.unaffectAll()
                    for layer in layers:
                        pnl_step.affect(layer)
                    pnl_step.affect(prof)
                    pnl_step.clip_area(margin=0, ref_layer=clip_layer)
                    pnl_step.unaffectAll()
                    pnl_step.affect(prof)
                    pnl_step.surf_outline()
                    pnl_step.selectAll()
                    pnl_step.selectCreateProf()
                    pnl_step.unaffectAll()
                pcs_step.removeLayer(prof)
                pcs_step.removeLayer(clip_layer)
                another_aoi_job.save()
                another_aoi_job.close(1)
            else:
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
            x_val = self.lineEdit_x_scale.text().replace('+', '')
            y_val = self.lineEdit_y_scale.text().replace('+', '')
            if x_val == '':
                x_val = 0
            if y_val == '':
                y_val = 0
            x_val = int(x_val)
            y_val = int(y_val)
            x_scale = 1 - abs(x_val) / 10000 if x_val < 0 else 1 + x_val / 10000
            y_scale = 1 - abs(y_val) / 10000 if y_val < 0 else 1 + y_val / 10000
            # 镜像
            # mir = 'mirror' if self.checkBox.isChecked()
            # if len(layers) > 1:
            #     dest = f'{jobname}-{"-".join(layers)}'
            # 选镀/阻焊层
            target_layers = []
            for lay in job.matrix.returnRows():
                if re.match(r'g[tb\d+]s$|dk[tb\d+](-\d+)?$', lay):
                    target_layers.append(lay)
                if lay not in layers:
                    job.matrix.deleteRow(lay)
            target_list = list(filter(lambda layer: layer in target_layers, layers))
            suffix = "-".join(target_list) if target_list else "-".join(layers)
            dest = f'{jobname}-{suffix}'
            if stepname == 'pnl':
                pnl_step = job.steps.get('pnl')
                # 外层线路
                out_signal = list(filter(lambda row: row in (job.SignalLayers[0], job.SignalLayers[-1]), layers))
                if out_signal:
                    ng_signal = []
                    for signal in out_signal:
                        flag = self.check_au_area(signal)
                        if not flag:
                            ng_signal.append(signal)
                    if ng_signal:
                        QMessageBox.warning(None, '提醒', f'检查到{"、".join(ng_signal)}没有加金面积')
                pnl_step.initStep()
                # 分段
                clip_layer = f'split+++{pnl_step.pid}'
                if self.comboBox_split.currentIndex():
                    # 做一层clip
                    pnl_step.createLayer(clip_layer)
                    pnl_step.affect(clip_layer)
                    if self.comboBox_split.currentIndex() == 1:
                        pnl_step.addRectangle(pnl_step.profile2.xmin - 30, pnl_step.profile2.ycenter,
                                              pnl_step.profile2.xmax + 30,
                                              pnl_step.profile2.ycenter - 355)
                    else:
                        pnl_step.addRectangle(pnl_step.profile2.xmin - 30, pnl_step.profile2.ycenter,
                                              pnl_step.profile2.xmax + 30,
                                              pnl_step.profile2.ycenter + 355)
                    pnl_step.unaffectAll()
                #
                for layer in layers:
                    pnl_step.affect(layer)
                # if target_layers:
                #     [pnl_step.affect(lay) for lay in target_layers]
                pnl_step.selectRectangle(pnl_step.profile2.xmin - 0.15, pnl_step.profile2.ymin - 0.15, pnl_step.profile2.xmax + 0.15, pnl_step.profile2.ymax + 0.15)
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
                    # 20240907 设置涨缩系数
                    pnl_step.layers.get(layer).setGenesisAttr('.out_x_scale', x_scale)
                    pnl_step.layers.get(layer).setGenesisAttr('.out_y_scale', y_scale)
                    if layer in target_layers:
                        pnl_step.prof_to_rout(layer)
                        pnl_step.affect(layer)
                        pnl_step.selectCutData()
                        pnl_step.unaffectAll()
                        pnl_step.VOF()
                        pnl_step.removeLayer(layer + '+++')
                        pnl_step.VON()
                        # 20240829 分段
                        if self.comboBox_split.currentIndex():
                            self.splitLayer(pnl_step, layer, clip_layer)
                            self.splitLayer(pnl_step, tmp_, clip_layer)
                        pnl_step.affect(tmp_)
                        # 涨缩镜像
                        pnl_step.Transform(oper='scale', x_anchor=pnl_step.profile2.xcenter, y_anchor=pnl_step.profile2.ycenter, x_scale=x_scale, y_scale=y_scale)
                        if self.checkBox.isChecked():
                            pnl_step.Transform(oper='mirror', x_anchor=pnl_step.profile2.xcenter, y_anchor=pnl_step.profile2.ycenter)
                        pnl_step.moveSel(layer, 'yes')
                    else:
                        if self.comboBox_split.currentIndex():
                            self.splitLayer(pnl_step, tmp_, clip_layer)  # 20240829 分段
                        pnl_step.affect(tmp_)
                        # 涨缩镜像
                        pnl_step.Transform(oper='scale', x_anchor=pnl_step.profile2.xcenter, y_anchor=pnl_step.profile2.ycenter, x_scale=x_scale, y_scale=y_scale)
                        if self.checkBox.isChecked():
                            pnl_step.Transform(oper='mirror', x_anchor=pnl_step.profile2.xcenter, y_anchor=pnl_step.profile2.ycenter)
                        pnl_step.moveSel(layer)
                    pnl_step.unaffectAll()
                    pnl_step.removeLayer(tmp_)
                pnl_step.VOF()
                pnl_step.removeLayer(clip_layer)
                pnl_step.VON()
                pnl_step.close()
            else:
                step = job.steps.get(stepname)
                step.initStep()
                # 分段
                clip_layer = f'split+++{step.pid}'
                if self.comboBox_split.currentIndex():
                    # 做一层clip
                    step.createLayer(clip_layer)
                    step.affect(clip_layer)
                    if self.comboBox_split.currentIndex() == 1:
                        step.addRectangle(step.profile2.xmin - 30, step.profile2.ycenter,
                                              step.profile2.xmax + 30,
                                              step.profile2.ycenter - 355)
                    else:
                        step.addRectangle(step.profile2.xmin - 30, step.profile2.ycenter,
                                              step.profile2.xmax + 30,
                                              step.profile2.ycenter + 355)
                    step.unaffectAll()
                    for layer in layers:
                        self.splitLayer(step, layer, clip_layer)
                for layer in layers:
                    step.affect(layer)
                    # 涨缩镜像
                step.Transform(oper='scale', x_anchor=step.profile2.xcenter, y_anchor=step.profile2.ycenter, x_scale=x_scale, y_scale=y_scale)
                if self.checkBox.isChecked():
                    step.Transform(oper='mirror', x_anchor=step.profile2.xcenter, y_anchor=step.profile2.ycenter)
                step.unaffectAll()
                step.VOF()
                step.removeLayer(clip_layer)
                step.VON()
            for name in job.steps:
                if name != stepname:
                    job.removeStep(name)
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
            self.groupBox_scale_mirror.setVisible(True)
            self.groupBox_split_ldi.setVisible(True)
            self.groupBox_split_aoi.setVisible(False)
            for name, context, type in zip(matrix_info.get('gROWname'), matrix_info.get('gROWcontext'),
                                           matrix_info.get('gROWlayer_type')):
                if context == 'board' and type in ('signal', 'drill'):
                    tableData.append([name, type, context])
                # 选镀/阻焊
                if re.match(r'g[tb\d+]s$|dk[tb\d+](-\d+)?$', name):
                    tableData.append([name, type, context])
        else:
            self.groupBox_scale_mirror.setVisible(False)
            self.groupBox_split_ldi.setVisible(False)
            self.groupBox_split_aoi.setVisible(True)
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

    # 20240821 检查是否有加金面积
    def check_au_area(self, layer):
        step = job.steps.get('pnl')
        step.initStep()
        step.affect(layer)
        step.setFilterTypes('text')
        step.setTextFilter('AU:*SQ/MM*')
        step.selectAll()
        step.resetFilter()
        if step.Selected_count():
            # 再判断是否有值
            info = step.INFO(f'-t layer -e {jobname}/{step.name}/{layer} -d FEATURES -o select')
            step.clearAll()
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
    app.setWindowIcon(QIcon(':/res/demo.png'))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    stepname = os.environ.get('STEP')
    output = AOI_LDI_Output()
    output.show()
    sys.exit(app.exec_())
