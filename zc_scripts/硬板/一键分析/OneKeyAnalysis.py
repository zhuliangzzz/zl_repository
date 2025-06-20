#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:OneKeyAnalysis.py
   @author:zl
   @time:2024/7/12 10:53
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

import OneKeyAnalysisUI as ui

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
            0: ['pcs/set尺寸', self.get_pcs_set_size],
            1: ['线路层残铜率', self.get_signal_copper],
            2: ['沉金面积', self.get_area_au],
            3: ['字符/湿膜/阻焊面积', self.get_area_info],
            4: ['ccd孔数量', self.get_ccd_drill_count],
            5: ['二维码坐标', self.get_2d_coor],
            6: ['orig分析', self.get_orig_analysis],
            7: ['pcs分析', self.get_pcs_analysis],
        }
        self.export_path = 'D:/一键分析结果'
        self.data = []
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
        header = f'Date = {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, User = {job.getUser()}\nJob = {jobname}'
        self.data.insert(0, header)
        filename = f'{jobname}.txt'
        if not os.path.exists(self.export_path):
            os.makedirs(self.export_path)
        with open(self.export_path + '/' + filename, 'w', encoding='utf-8') as w:
            w.write('\n************************************\n'.join(self.data))
            w.write('\n************************************')
        QMessageBox.information(self, '提示', f'导出成功!\n导出路径为：{self.export_path}')

    def pause(self):
        self.hide()
        job.PAUSE('Pause Script')
        self.show()

    def exec(self):
        # 检查是否有pcs/set/pnl
        if not job.steps.get('orig') or not job.steps.get('pcs') or not job.steps.get('set') or not job.steps.get('pnl'):
            QMessageBox.warning(self, '警告', '请检查是否有orig/pcs/set/pnl')
            return
        for item in self.items:
            self.tableWidget.item(item, 2).setText('')
        for item in self.items:
            self.items.get(item)[1](item)
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
        runLocal.triggered.connect(lambda: self.items.get(item)[1](item))
        menu.exec_(QCursor.pos())

    def showResult(self):
        row = self.tableWidget.currentRow()
        self.label_item.setText(self.tableWidget.item(row, 1).text())
        self.textEdit.setText(self.tableWidget.item(row, 2).text())

    def get_pcs_set_size(self, item):
        self.statusbar.showMessage(f'正在执行{self.items[item][0]}')
        result = []
        pcs_x, pcs_y = job.steps.get('pcs').profile2.xsize, job.steps.get('pcs').profile2.ysize
        result.append(f'pcs 宽度：{"%.5f" % pcs_x}mm, 高度：{"%.5f" % pcs_y}mm')
        set_x, set_y = job.steps.get('set').profile2.xsize, job.steps.get('set').profile2.ysize
        result.append(f'set 宽度：{"%.5f" % set_x}mm, 高度：{"%.5f" % set_y}mm')
        self.tableWidget.setItem(item, 2, QTableWidgetItem('\n'.join(result)))
        self.data.append(
            f'main_info_for_board\nboardlayer = {job.SignalNum}\npcsx = {pcs_x}\npcsy = {pcs_y}\nsetx = {set_x}\nsety = {set_y}')
        self.statusbar.showMessage(f'{self.items[item][0]}已完成')
        app.processEvents()

    def get_signal_copper(self, item):
        self.statusbar.showMessage(f'正在执行{self.items[item][0]}')
        result, data = [], []
        pnl_step = job.steps.get('pnl')
        pnl_step.initStep()
        for signal in job.SignalLayers:
            pnl_step.COM(
                f'copper_area,layer1={signal},layer2=,drills=yes,consider_rout=no,ignore_pth_no_pad=no,drills_source=matrix,thickness=0,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes')
            area, percent = pnl_step.COMANS.split()
            result.append(f'{signal}: {"%.8f" % (float(area) / 1000000)}sq/m²({"%.2f" % float(percent)})%')
            data.append(f'pnl_copper_info {signal} {"%.2f" % float(percent)}% {"%.8f" % (float(area) / 1000000)}')
        self.tableWidget.setItem(item, 2, QTableWidgetItem('\n'.join(result)))
        self.data.append(f'Job = {jobname}, Step = pnl, unit = mm\ncopper_info_for_pnl\n%s' % '\n'.join(data))
        self.statusbar.showMessage(f'{self.items[item][0]}已完成')
        app.processEvents()

    # 沉金面积
    def get_area_au(self, item):
        self.statusbar.showMessage(f'正在执行{self.items[item][0]}')
        result, data = [], []
        pnl_step = job.steps.get('pnl')
        pnl_step.initStep()
        # print(job.SignalLayers)
        for signal in job.SignalLayers:
            # 外层线路
            if signal in ('gtl', 'gbl', 'l1', f'l{len(job.SignalLayers)}'):
                cov = 'c1' if signal in ('gtl', 'l1') else f'c{len(job.SignalLayers)}'
                sm = 'gts' if signal in ('gtl', 'l1') else 'gbs'
                mix = 'mixtop' if signal in ('gtl', 'l1') else 'mixbot'
                if pnl_step.isLayer(sm) and pnl_step.isLayer(cov):
                    if not pnl_step.isLayer(mix):
                        result.append(f'{signal}: 缺少对应的开窗（{mix}）')
                        continue
                    pnl_step.COM(
                        f'exposed_area,layer1={signal},mask1={mix},layer2=,mask2=,mask_mode=or,drills=yes,consider_rout=no,ignore_pth_no_pad=no,drills_source=matrix,drills_list=f1,thickness=0,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes')
                    area, percent = pnl_step.COMANS.split()
                elif pnl_step.isLayer(sm) or pnl_step.isLayer(cov):
                    mask = sm if pnl_step.isLayer(sm) else cov
                    pnl_step.COM(
                        f'exposed_area,layer1={signal},mask1={mask},layer2=,mask2=,mask_mode=or,drills=yes,consider_rout=no,ignore_pth_no_pad=no,drills_source=matrix,drills_list=f1,thickness=0,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes')
                    area, percent = pnl_step.COMANS.split()
                else:
                    continue
                result.append(f'{signal}: {"%.8f" % (float(area) / 1000000)}sq/m²({"%.2f" % float(percent)})%')
                data.append(f'area_au_info {signal} {"%.2f" % float(percent)}% {"%.8f" % (float(area) / 1000000)}')
        self.tableWidget.setItem(item, 2, QTableWidgetItem('\n'.join(result)))
        self.data.append(f'Job = {jobname}, Step = pnl, unit = mm\narea_au_info_for_pnl\n%s' % '\n'.join(data))
        self.statusbar.showMessage(f'{self.items[item][0]}已完成')
        app.processEvents()

    # 字符/湿膜/阻焊面积
    def get_area_info(self, item):
        self.statusbar.showMessage(f'正在执行{self.items[item][0]}')
        result, data = [], []
        pnl_step = job.steps.get('pnl')
        pnl_step.initStep()
        # 字符
        for ss in job.matrix.returnRows('board', 'silk_screen'):
            pnl_step.COM(
                f'copper_area,layer1={ss},layer2=,drills=yes,consider_rout=no,ignore_pth_no_pad=no,drills_source=matrix,thickness=0,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes')
            area, percent = pnl_step.COMANS.split()
            result.append(f'{ss}: {"%.8f" % (float(area) / 1000000)}sq/m²({"%.2f" % float(percent)})%')
            data.append(f'area_info {ss} {"%.2f" % float(percent)}% {"%.8f" % (float(area) / 1000000)}')
        for lay in filter(lambda row: re.match('sm-(t|b|\d+)$|g(t|b|\d+)s', row), job.matrix.returnRows()):
            pnl_step.COM(
                f'copper_area,layer1={lay},layer2=,drills=yes,consider_rout=no,ignore_pth_no_pad=no,drills_source=matrix,thickness=0,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes')
            area, percent = pnl_step.COMANS.split()
            result.append(f'{lay}: {"%.8f" % (float(area) / 1000000)}sq/m²({"%.2f" % float(percent)})%')
            data.append(f'area_info {lay} {"%.2f" % float(percent)}% {"%.8f" % (float(area) / 1000000)}')
        self.tableWidget.setItem(item, 2, QTableWidgetItem('\n'.join(result)))
        self.data.append(f'Job = {jobname}, Step = pnl, unit = mm\narea_info_for_pnl\n%s' % '\n'.join(data))
        self.statusbar.showMessage(f'{self.items[item][0]}已完成')
        app.processEvents()

    def get_ccd_drill_count(self, item):
        self.statusbar.showMessage(f'正在执行{self.items[item][0]}')
        result, data = [], []
        pnl_step = job.steps.get('pnl')
        pnl_step.initStep()
        rows = job.matrix.returnRows()
        ccds = filter(lambda row: re.match('ccd\d+$', row), rows)
        for ccd in ccds:
            pnl_step.affect(ccd)
            pnl_step.selectAll()
            count = pnl_step.Selected_count()
            result.append(f"层{ccd}孔数量：{count}")
            data.append(f'ccd_info {ccd} {count}')
            pnl_step.unaffectAll()
        self.tableWidget.setItem(item, 2, QTableWidgetItem('\n'.join(result)))
        self.data.append(f'Job = {jobname}, Step = pnl, unit = mm\ndrillcount_info_for_pnl\n%s' % '\n'.join(data))
        self.statusbar.showMessage(f'{self.items[item][0]}已完成')
        app.processEvents()

    def get_2d_coor(self, item):
        self.statusbar.showMessage(f'正在执行{self.items[item][0]}')
        result, data = [], []
        pnl_step = job.steps.get('pnl')
        if pnl_step.isLayer('2d'):
            lines = pnl_step.INFO(f'-t layer -e {jobname}/pnl/2d  -d FEATURES,units=mm')
            if lines:
                del lines[0]
            for line in lines:
                x = line.split()[1]
                y = line.split()[2]
                sym = line.split()[3]
                if sym == '2d':
                    result.append(f"x：{x},y：{y}")
                    data.append(f'2d_position_info_x {x}')
                    data.append(f'2d_position_info_y {y}')
            if not data:
                result.append('没有2d symbol')
        else:
            result.append('没有2d层')
        self.tableWidget.setItem(item, 2, QTableWidgetItem('\n'.join(result)))
        self.data.append(f'Job = {jobname}, Step = pnl, unit = mm\n2d_info_for_pnl\n%s' % '\n'.join(
            data)) if data else self.data.append(f'Job = {jobname}, Step = pnl, unit = mm\n2d_info_for_pnl')
        self.statusbar.showMessage(f'{self.items[item][0]}已完成')
        app.processEvents()


    def get_orig_analysis(self, item):
        self.statusbar.showMessage(f'正在执行{self.items[item][0]}')
        result, data = [], []
        orig_step = job.steps.get('orig')
        orig_step.initStep()
        checklist = gen.Checklist(orig_step, 'orig_analysis_checklist', 'valor_analysis_signal')
        checklist.action()
        checklist.erf('Outer (Mils)')
        checklist.COM('chklist_cupd,chklist=valor_analysis_signal,nact=1,params=((pp_layer=.type=signal|mixed&side=top|bottom)(pp_spacing=254)(pp_r2c=635)(pp_d2c=355.6)(pp_sliver=254)(pp_min_pad_overlap=127)(pp_tests=Spacing\;Drill\;Rout\;Size\;Sliver\;Stubs\;Center\;SMD)(pp_selected=All)(pp_check_missing_pads_for_drills=Yes)(pp_use_compensated_rout=No)(pp_sm_spacing=No)),mode=regular')
        checklist.run()
        checklist.clear()
        checklist.COM('chklist_cupd,chklist=valor_analysis_signal,nact=1,params=((pp_layer=.type=signal|mixed&side=top|bottom)(pp_spacing=254)(pp_r2c=635)(pp_d2c=355.6)(pp_sliver=254)(pp_min_pad_overlap=127)(pp_tests=Spacing\;Drill\;Rout\;Size\;Sliver\;Stubs\;Center\;SMD)(pp_selected=All)(pp_check_missing_pads_for_drills=Yes)(pp_use_compensated_rout=No)(pp_sm_spacing=No)),mode=regular')
        checklist.copy()
        if checklist.name in orig_step.checks:
            orig_step.deleteCheck(checklist.name)
        orig_step.createCheck(checklist.name)
        orig_step.pasteCheck(checklist.name)
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=arc,units=mm' % (jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"arc:{res}")
        data.append(f'out_sig_arc = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=c2c,units=mm' % (jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"c2c:{res}")
        data.append(f'out_sig_c2c = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=conductor_width,units=mm' % (
        jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"conductor_width:{res}")
        data.append(f'out_sig_conductor_width = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=l2l,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"l2l:{res}")
        data.append(f'out_sig_l2l = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=line,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"line:{res}")
        data.append(f'out_sig_line = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=p2c,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"p2c:{res}")
        data.append(f'out_sig_p2c = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=pad,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"pad:{res}")
        data.append(f'out_sig_pad = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=pth2c,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"pth2c:{res}")
        data.append(f'out_sig_pth2c = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=pth2l,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"pth2l:{res}")
        data.append(f'out_sig_pth2l = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=pth2pth,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"pth2pth:{res}")
        data.append(f'out_sig_pth2pth = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=pth_ar,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"pth_ar:{res}")
        data.append(f'out_sig_pth_ar = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=self_spacing,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"self_spacing:{res}")
        data.append(f'out_sig_self_spacing = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=sliver,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"sliver:{res}")
        data.append(f'out_sig_sliver = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=smd2c,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"smd2c:{res}")
        data.append(f'out_sig_smd2c = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=smd2pad,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"smd2pad:{res}")
        data.append(f'out_sig_smd2pad = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=smd2smd,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"smd2smd:{res}")
        data.append(f'out_sig_smd2smd = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=smd_package,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"smd_package:{res}")
        data.append(f'out_sig_smd_package = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=smd_pad,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"smd_pad:{res}")
        data.append(f'out_sig_smd_pad = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=smd_pitch,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"smd_pitch:{res}")
        data.append(f'out_sig_smd_pitch = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=spacing_length,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"spacing_length:{res}")
        data.append(f'out_sig_spacing_length = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=stub,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"stub:{res}")
        data.append(f'out_sig_stub = {res}')
        # ss
        checklist = gen.Checklist(orig_step, 'orig_ss_analysis_checklist', 'valor_analysis_ss')
        checklist.action()
        checklist.COM('chklist_cupd,chklist=valor_analysis_ss,nact=1,params=((pp_layers=.type=silk_screen&context=board)(pp_spacing=355.6)(pp_tests=SM clearance\;SMD clearance\;Pad clearance\;Hole clearance\;Line width)(pp_selected=All)(pp_use_compensated_rout=No)),mode=regular')
        checklist.run()
        checklist.clear()
        checklist.COM('chklist_cupd,chklist=valor_analysis_ss,nact=1,params=((pp_layers=.type=silk_screen&context=board)(pp_spacing=355.6)(pp_tests=SM clearance\;SMD clearance\;Pad clearance\;Hole clearance\;Line width)(pp_selected=All)(pp_use_compensated_rout=No)),mode=regular')
        checklist.copy()
        if checklist.name in orig_step.checks:
            orig_step.deleteCheck(checklist.name)
        orig_step.createCheck(checklist.name)
        orig_step.pasteCheck(checklist.name)
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=ss_line,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"ss_ss_line:{res}")
        data.append(f'ss_ss_line = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=ss_spacing,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"ss_ss_spacing:{res}")
        data.append(f'ss_ss_spacing = {res}')
        # drill
        checklist = gen.Checklist(orig_step, 'orig_drill_analysis_checklist', 'valor_analysis_drill')
        checklist.action()
        checklist.COM('chklist_cupd,chklist=valor_analysis_drill,nact=1,params=((pp_drill_layer=.type=drill&context=board)(pp_rout_distance=5080)(pp_tests=Hole Size\;Hole Separation\;Missing Holes\;Extra Holes\;Power/Ground Shorts\;NPTH to Rout)(pp_extra_hole_type=Pth\;Via)(pp_use_compensated_rout=Skeleton)),mode=regular')
        checklist.run()
        checklist.clear()
        checklist.COM('chklist_cupd,chklist=valor_analysis_drill,nact=1,params=((pp_drill_layer=.type=drill&context=board)(pp_rout_distance=5080)(pp_tests=Hole Size\;Hole Separation\;Missing Holes\;Extra Holes\;Power/Ground Shorts\;NPTH to Rout)(pp_extra_hole_type=Pth\;Via)(pp_use_compensated_rout=Skeleton)),mode=regular')
        checklist.copy()
        if checklist.name in orig_step.checks:
            orig_step.deleteCheck(checklist.name)
        orig_step.createCheck(checklist.name)
        orig_step.pasteCheck(checklist.name)
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=missh,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"drill_missh:{res}")
        data.append(f'drill_missh = {res}')
        info = orig_step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=pth,units=mm' % (
            jobname, orig_step.name, checklist.name))
        res = ''
        if info:
            res = min([float(l.split()[2]) for l in info])
        result.append(f"drill_pth:{res}")
        data.append(f'drill_pth = {res}')
        self.tableWidget.setItem(item, 2, QTableWidgetItem('\n'.join(result)))
        self.data.append(f'Job = {jobname}, Step = orig, unit = mm\ndrc_info_for_orig\n%s' % '\n'.join(data))
        self.statusbar.showMessage(f'{self.items[item][0]}已完成')
        app.processEvents()


    def get_pcs_analysis(self, item):
        self.statusbar.showMessage(f'正在执行{self.items[item][0]}')
        result, data = [], []
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
        for layer in job.SignalLayers:
            info = pcs_step.INFO(f'-t check -e %s/%s/%s -d MEAS -o action=1+category=line+layer={layer},units=mm' % (
            jobname, pcs_step.name, checklist.name))
            res = ''
            if info:
                res = min([float(l.split()[2]) for l in info])
            result.append(f"lw {layer}:{res}")
            data.append(f'lw {layer} {res}')
        for layer in job.SignalLayers:
            info = pcs_step.INFO(f'-t check -e %s/%s/%s -d MEAS -o action=1+category=spacing_length+layer={layer},units=mm' % (
            jobname, pcs_step.name, checklist.name))
            res = ''
            if info:
                res = min([float(l.split()[2]) for l in info])
            result.append(f"lsp {layer}:{res}")
            data.append(f'lsp {layer} {res}')
        self.tableWidget.setItem(item, 2, QTableWidgetItem('\n'.join(result)))
        self.data.append(f'Job = {jobname}, Step = pcs, unit = mm\neach_layer_lwlsp_info_for_pcs\n%s' % '\n'.join(
            data)) if data else self.data.append(f'Job = {jobname}, Step = pcs, unit = mm\neach_layer_lwlsp_info_for_pcs')
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
