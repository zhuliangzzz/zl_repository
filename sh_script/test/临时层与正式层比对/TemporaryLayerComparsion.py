#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:TemporaryLayerComparsion-lyh.py
   @author:zl
   @time: 2024/12/25 14:46
   @software:PyCharm
   @desc:
   阴阳拼版逻辑  由于board层必须是对称的，所以不能把所有临时层一次性去改board属性
   必须循环临时层内去改board属性 两个层必须依次变成board 和misc  然后在各自为misc的时候去panel里flatten 再去对比flatten后的层
   20241230 比对层排除周期区域和sh-op区域
   20250226 不含属性area的物件不能进板内1.5mm 比对时不含属性area的去掉 审核人不排除区域，比对所有区域
   20250329 check用户 比对精度可编辑，默认未0.1 其他用户不设置
"""
import os
import re
import sys, platform

reload(sys)
sys.setdefaultencoding('utf8')
from PyQt4.QtCore import *
from PyQt4.QtGui import *

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen
from genesisPackages import get_layer_selected_limits, get_sr_area_flatten
import TemporaryLayerComparsionUI_pyqt4 as ui


class TemporaryLayerComparsion(QWidget, ui.Ui_Form):
    def __init__(self):
        super(TemporaryLayerComparsion, self).__init__()
        self.setupUi(self)
        self.render()

    def closeEvent(self, event):
        event.ignore()

    def render(self):
        self.job = gen.Job(jobname)
        if platform.system() == "Windows":
            self.userDir = "%s/fw/jobs/%s/user" % (os.environ.get('GENESIS_DIR', 'D:/genesis'), jobname)
        else:
            self.userDir = os.environ.get('JOB_USER_DIR', None)
            if not self.userDir:
                self.userDir = "%s/user" % self.job.dbpath
        # print(self.userDir)
        self.comparsion_log = os.path.join(self.userDir, '%s_temp_layer_comparsion.log' % jobname)
        self.temp_map = {}
        self.rows = self.job.matrix.returnRows()
        for row in self.rows:
            res = re.match(".*(-ls\d+.*)", row)
            if res:
                key = res.group(1)
                if key not in self.temp_map:
                    self.temp_map[key] = []
                self.temp_map[key].append(row)
        self.temp_layers = sorted([i for val in self.temp_map.values() for i in val], key=self.temp_layers_sort, reverse=True)  # 所有临时层
        self.flipList = []  # flip的step
        self.listWidget.addItems(self.temp_layers)
        self.tableWidget.setColumnCount(1)
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.horizontalHeader().hide()
        self.tableWidget.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.comboBox_temp.addItem('')
        if self.temp_map.keys():
            self.comboBox_temp.addItems(sorted(self.temp_map.keys(), reverse=True))
        self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.comboBox_resolution.addItems(['1', '2'])
        if is_check_user:
            self.comboBox_resolution.setEditable(True)
            self.comboBox_resolution.addItem('0.1')
            self.comboBox_resolution.setCurrentIndex(2)
        #
        self.checkBox_all.clicked.connect(self.select_all)
        self.radioButton.clicked.connect(self.select_type)
        self.radioButton_2.clicked.connect(self.select_type)
        self.comboBox_temp.currentIndexChanged.connect(self.filter_temp)
        self.comboBox_temp_2.currentIndexChanged.connect(self.filter_temp2)
        self.pushButton_exec.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit(1))
        self.tableWidget.verticalHeader().setDefaultSectionSize(24)
        self.tableWidget_2.verticalHeader().setDefaultSectionSize(24)
        self.setStyleSheet('''
        QPushButton:hover{background:black;color:white;}
        QPushButton{font:11pt;background-color:#0081a6;color:white;}
        QMessageBox{font-size:10pt;}
        QListWidget::Item{height:24px;border-radius:1.5px;} QListWidget::Item:selected{background:#0081a6;color:white;}
        ''')
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)
        self.load_table()


    def render2(self):
        self.temp_map2 = {}
        self.listWidget_2.clear()
        self.comboBox_temp_2.clear()
        self.checkBox_all_2.setChecked(False)
        for row in self.rows:
            res = re.match(".*(-bf\d+.*)", row)
            if res:
                key = res.group(1)
                if key not in self.temp_map2:
                    self.temp_map2[key] = []
                self.temp_map2[key].append(row)
        self.temp2_layers = sorted([i for val in self.temp_map2.values() for i in val], key=self.temp_layers_sort2,
                                  reverse=True)  # 所有临时层
        self.flipList = []  # flip的step
        self.listWidget_2.addItems(self.temp2_layers)
        self.tableWidget_2.setColumnCount(1)
        self.tableWidget_2.verticalHeader().hide()
        self.tableWidget_2.horizontalHeader().hide()
        self.tableWidget_2.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.comboBox_temp_2.addItem('')
        if self.temp_map2.keys():
            self.comboBox_temp_2.addItems(sorted(self.temp_map2.keys(), reverse=True))
        self.listWidget_2.setSelectionMode(QAbstractItemView.MultiSelection)
        #
        self.checkBox_all_2.clicked.connect(self.select_all2)
        self.load_table2()
    def temp_layers_sort(self, layer):
        res = re.match(".*(-ls\d+.*)", layer)
        return res.group(1)

    def temp_layers_sort2(self, layer):
        res = re.match(".*(-bf\d+.*)", layer)
        return res.group(1)

    def filter_temp(self):
        text = str(self.comboBox_temp.currentText())
        self.listWidget.clear()
        # print(text)
        if self.temp_map.get(text):
            self.listWidget.addItems(self.temp_map.get(text))
        else:
            self.listWidget.addItems(self.temp_layers)
        self.load_table()


    def filter_temp2(self):
        text = str(self.comboBox_temp_2.currentText())
        self.listWidget_2.clear()
        # print(text)
        if self.temp_map2.get(text):
            self.listWidget_2.addItems(self.temp_map2.get(text))
        else:
            self.listWidget_2.addItems(self.temp2_layers)
        self.load_table2()

    def load_table(self):
        text = str(self.comboBox_temp.currentText())
        self.tableWidget.clear()
        if self.temp_map.get(text):
            self.tableWidget.setRowCount(len(self.temp_map.get(text)))
            for row, layer in enumerate(self.temp_map.get(text)):
                combox = QComboBox()
                combox.addItems(self.rows)
                formal_layer = layer.split('-ls')[0]
                index = None
                for i in range(combox.count()):
                    if combox.itemText(i) == formal_layer:
                        index = i
                        break
                if index is None:
                    index = 0
                    combox.setStyleSheet('color:red;')
                combox.setCurrentIndex(index)
                self.tableWidget.setCellWidget(row, 0, combox)
        else:
            self.tableWidget.setRowCount(len(self.temp_layers))
            for row, layer in enumerate(self.temp_layers):
                combox = QComboBox()
                combox.addItems(self.rows)
                formal_layer = layer.split('-ls')[0]
                index = None
                for i in range(combox.count()):
                    if combox.itemText(i) == formal_layer:
                        index = i
                        break
                if index is None:
                    index = 0
                    combox.setStyleSheet('color:red;')
                combox.setCurrentIndex(index)
                self.tableWidget.setCellWidget(row, 0, combox)

    def load_table2(self):
        text = str(self.comboBox_temp_2.currentText())
        self.tableWidget_2.clear()
        if self.temp_map2.get(text):
            self.tableWidget_2.setRowCount(len(self.temp_map2.get(text)))
            for row, layer in enumerate(self.temp_map2.get(text)):
                combox = QComboBox()
                combox.addItems(self.rows)
                formal_layer = layer.split('-bf')[0]
                index = None
                for i in range(combox.count()):
                    if combox.itemText(i) == formal_layer:
                        index = i
                        break
                if index is None:
                    index = 0
                    combox.setStyleSheet('color:red;')
                combox.setCurrentIndex(index)
                self.tableWidget_2.setCellWidget(row, 0, combox)
        else:
            self.tableWidget_2.setRowCount(len(self.temp2_layers))
            for row, layer in enumerate(self.temp2_layers):
                combox = QComboBox()
                combox.addItems(self.rows)
                formal_layer = layer.split('-bf')[0]
                index = None
                for i in range(combox.count()):
                    if combox.itemText(i) == formal_layer:
                        index = i
                        break
                if index is None:
                    index = 0
                    combox.setStyleSheet('color:red;')
                combox.setCurrentIndex(index)
                self.tableWidget_2.setCellWidget(row, 0, combox)

    def select_all(self):
        if self.checkBox_all.isChecked():
            self.listWidget.selectAll()
        else:
            self.listWidget.clearSelection()

    def select_all2(self):
        if self.checkBox_all_2.isChecked():
            self.listWidget_2.selectAll()
        else:
            self.listWidget_2.clearSelection()

    def select_type(self):
        if self.radioButton.isChecked():
            self.stackedWidget.setCurrentIndex(0)
        else:
            self.stackedWidget.setCurrentIndex(1)
            self.render2()

    def run(self):
        if self.radioButton.isChecked():
            if not self.listWidget.selectedItems():
                QMessageBox.warning(None, u'警告', u'请选择层！')
                return
            get_sr_area_flatten("surface_fill")
            resolution = self.comboBox_resolution.currentText()
            resolution = float(resolution)
            layers = [str(item.text()) for item in self.listWidget.selectedItems()]
            board_layers = self.job.matrix.returnRows('board')
            step = gen.Step(self.job, 'panel')
            flipstep = gen.Step(self.job, "edit")
            self.flipStepName(step.name)
            # # 如果阴阳拼版 把属性取消
            dic_drill_start_end = self.get_drill_start_end_layers()
            step.initStep()
            # step.setUnits('inch')
            diff_layers, enter_board_layers = [], []
            for layer in layers:
                for i in range(self.listWidget.count()):
                    if self.listWidget.item(i).text() == layer:
                        index = i
                        break
                formal_layer = self.tableWidget.cellWidget(index, 0).currentText()
                # formal_layer = layer.split('-ls')[0]
                tmp_layer = '%s+++%s' % (layer, step.pid)
                tmp_formal_layer = '%s+++%s' % (formal_layer, step.pid)
                if self.flipList:
                    # 临时层是board
                    if layer in board_layers:
                        step.Flatten(formal_layer, tmp_formal_layer)
                        flipstep.open()
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % jobname)
                        self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(jobname, layer))
                        self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(jobname, formal_layer))
                        new_dic_drill_start_end = self.get_drill_start_end_layers()
                        for key, value in new_dic_drill_start_end.iteritems():
                            if value["start"] and value["end"]:

                                for new_key in [key, key.split("-ls")[0]]:
                                    if not dic_drill_start_end.has_key(new_key):
                                        continue

                                    if dic_drill_start_end[new_key]["start"] == value["start"] and \
                                            dic_drill_start_end[new_key]["end"] == value["end"]:
                                        continue
                                    # start end 可能是正式层也可能是临时层 也可能跟目前这两层没关系
                                    start = formal_layer if dic_drill_start_end[new_key]["start"] == layer else dic_drill_start_end[new_key]["start"]
                                    end = formal_layer if dic_drill_start_end[new_key]["end"] == layer else dic_drill_start_end[new_key]["end"]
                                    self.job.COM("matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(
                                        jobname, key, start,end
                                    ))
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % jobname)
                        step.open()
                        step.Flatten(layer, tmp_layer)
                        # 还原
                        flipstep.open()
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % jobname)
                        self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(jobname, layer))
                        self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(jobname, formal_layer))
                        new_dic_drill_start_end = self.get_drill_start_end_layers()
                        for key, value in new_dic_drill_start_end.iteritems():
                            if value["start"] and value["end"]:
                                for new_key in [key, key.split("-ls")[0]]:
                                    if not dic_drill_start_end.has_key(new_key):
                                        continue
                                    if dic_drill_start_end[new_key]["start"] == value["start"] and \
                                            dic_drill_start_end[new_key]["end"] == value["end"]:
                                        continue
                                    self.job.COM(
                                        "matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(
                                            jobname, key, dic_drill_start_end[new_key]["start"],
                                            dic_drill_start_end[new_key]["end"]
                                        ))
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % jobname)
                        step.open()
                    else:
                        step.Flatten(layer, tmp_layer)
                    # 正式层是board
                    if formal_layer in board_layers:
                        step.Flatten(layer, tmp_layer)
                        flipstep.open()
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % jobname)
                        self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(jobname, formal_layer))
                        self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(jobname, layer))
                        new_dic_drill_start_end = self.get_drill_start_end_layers()
                        for key, value in new_dic_drill_start_end.iteritems():
                            if value["start"] and value["end"]:

                                for new_key in [key, key.split("-ls")[0]]:
                                    if not dic_drill_start_end.has_key(new_key):
                                        continue

                                    if dic_drill_start_end[new_key]["start"] == value["start"] and \
                                            dic_drill_start_end[new_key]["end"] == value["end"]:
                                        continue
                                    # start end 可能是正式层也可能是临时层 也可能跟目前这两层没关系
                                    start = layer if dic_drill_start_end[new_key]["start"] == formal_layer else dic_drill_start_end[new_key]["start"]
                                    end = layer if dic_drill_start_end[new_key]["end"] == formal_layer else dic_drill_start_end[new_key]["end"]
                                    self.job.COM("matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(jobname, key, start, end))
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % jobname)
                        step.open()
                        step.Flatten(formal_layer, tmp_formal_layer)
                        # 还原
                        flipstep.open()
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % jobname)
                        self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(jobname, formal_layer))
                        self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(jobname, layer))
                        new_dic_drill_start_end = self.get_drill_start_end_layers()
                        for key, value in new_dic_drill_start_end.iteritems():
                            if value["start"] and value["end"]:

                                for new_key in [key, key.split("-ls")[0]]:
                                    if not dic_drill_start_end.has_key(new_key):
                                        continue

                                    if dic_drill_start_end[new_key]["start"] == value["start"] and \
                                            dic_drill_start_end[new_key]["end"] == value["end"]:
                                        continue

                                    self.job.COM(
                                        "matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(
                                            jobname, key, dic_drill_start_end[new_key]["start"],
                                            dic_drill_start_end[new_key]["end"]
                                        ))
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % jobname)
                        step.open()
                    else:
                        step.Flatten(formal_layer, tmp_formal_layer)
                else:
                    step.Flatten(layer, tmp_layer)
                    step.Flatten(formal_layer, tmp_formal_layer)
                map_layer = '%s_check_compare_diff+++' % formal_layer
                step.removeLayer(map_layer)
                areas = []
                # 20250226 把不含area属性的去除
                step.affect(layer)
                step.setAttrFilter_pro('.area')
                step.setAttrLogic_pro()
                step.selectAll()
                step.resetFilter()
                temporaryLayer = '%s+++enter_board' % layer
                step.removeLayer(temporaryLayer)
                if step.Selected_count():
                    step.selectReverse()
                    if step.Selected_count():
                        step.copySel(temporaryLayer)
                        step.unaffectAll()
                        feats = step.INFO('-t layer -e %s/%s/%s -d FEATURES -o feat_index' % (self.job.name, step.name, temporaryLayer))
                        del feats[0]
                        ids = []
                        for feat in feats:
                            feat = feat.strip()
                            if feat:
                                index_str = feat.split()[0]
                                if re.match('#\d+', index_str):
                                    ids.append(index_str.replace('#', ''))
                        step.affect(temporaryLayer)
                        for id in ids:
                            step.selectByIndex(temporaryLayer, id)
                            xmin, ymin, xmax, ymax = get_layer_selected_limits(step, temporaryLayer)
                            areas.append([xmin - 0.5, ymin - 0.5, xmax + 0.5, ymax + 0.5])
                            step.clearSel()
                        step.selectResize(1500)
                        step.refSelectFilter('surface_fill')
                        if step.Selected_count():
                            step.selectReverse()
                            if step.Selected_count():
                                step.selectDelete()
                            enter_board_layers.append(layer)
                            step.unaffectAll()
                        else:
                            step.removeLayer(temporaryLayer)
                        step.unaffectAll()
                step.unaffectAll()
                step.compareLayers(tmp_layer, self.job.name, step.name, tmp_formal_layer, tol=resolution * 25.4, map_layer=map_layer, map_layer_res=5080)
                # 获取区域
                layer_cmd = gen.Layer(step, tmp_formal_layer)
                step.affect(tmp_formal_layer)
                step.selectSymbol('sh-op*')
                step.resetFilter()
                if step.Selected_count():
                    feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]
                    for obj in feat_out:
                        step.clearSel()
                        step.selectByIndex(tmp_formal_layer, obj.feat_index)
                        xmin, ymin, xmax, ymax = get_layer_selected_limits(step, tmp_formal_layer)
                        areas.append([xmin - 0.5, ymin - 0.5, xmax + 0.5, ymax + 0.5])
                        step.clearSel()
                step.setFilterTypes('text')
                step.selectAll()
                step.resetFilter()
                if step.Selected_count():
                    feat_text = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["text"]
                    feat_barcodes = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["barcodes"]
                    for obj in feat_text:
                        for week_text in ["$$yy", "$${yy}", "$$ww","$${ww}", "$$month", "$${month}","$$layer","$${layer}",
                                          "$$day", "$${day}", "$$banci", "$${banci}", "$$xingqi", "$${xingqi}",
                                          "$$picihao", "$${picihao}", "$$mm","$${mm}", "$$dd", "$${dd}", "$$year","$${year}"]:
                            if week_text in obj.text.replace("'", "").lower():
                                step.clearSel()
                                step.selectByIndex(tmp_formal_layer, obj.feat_index)
                                xmin, ymin, xmax, ymax = get_layer_selected_limits(step, tmp_formal_layer)
                                areas.append([xmin - 0.5, ymin - 0.5, xmax + 0.5, ymax + 0.5])
                                step.clearSel()
                                break
                    for obj in feat_barcodes:
                        for week_text in ["$$yy", "$${yy}", "$$ww", "$${ww}", "$$month", "$${month}","$$layer","$${layer}",
                                          "$$day", "$${day}", "$$banci", "$${banci}", "$$xingqi", "$${xingqi}",
                                          "$$picihao", "$${picihao}", "$$mm", "$${mm}", "$$dd", "$${dd}", "$$year",
                                          "$${year}"]:
                            if week_text in obj.text.replace("'", "").lower():
                                step.clearSel()
                                step.selectByIndex(tmp_formal_layer, obj.feat_index)
                                xmin, ymin, xmax, ymax = get_layer_selected_limits(step, tmp_formal_layer)
                                areas.append([xmin - 0.5, ymin - 0.5, xmax + 0.5, ymax + 0.5])
                                step.clearSel()
                                break
                step.unaffectAll()
                area_layer = 'area_layer+++'
                if areas:
                    step.removeLayer(area_layer)
                    step.createLayer(area_layer)
                    step.affect(area_layer)
                    for area in areas:
                        step.addRectangle(area[0], area[1], area[2], area[3])
                    step.unaffectAll()
                step.affect(map_layer)
                step.resetFilter()
                step.setFilterTypes('pad')
                step.setSymbolFilter('r0')
                if not is_check_user:
                    if step.isLayer(area_layer):
                        step.refSelectFilter(area_layer, mode='cover')
                        if step.Selected_count():
                            step.selectDelete()
                    # if step.isLayer("surface_fill"):
                    #     if step.isLayer(temporaryLayer):
                    #         step.refSelectFilter(temporaryLayer, mode='cover')
                    #         if step.Selected_count():
                    #             step.selectDelete()
                        # step.refSelectFilter("surface_fill", mode='cover')
                step.selectAll()
                step.resetFilter()
                if step.Selected_count():
                    diff_layers.append([layer, formal_layer, map_layer])
                else:
                    step.removeLayer(map_layer)
                step.unaffectAll()
                step.removeLayer(area_layer)
                step.removeLayer(tmp_layer)
                step.removeLayer(tmp_formal_layer)
            # step.PAUSE('A')
            step.removeLayer('surface_fill')
            record = []
            for layer in layers:
                diff = list(filter(lambda diff_layer: layer == diff_layer[0], diff_layers))
                if diff:
                    record.append(u'%s 比对异常\n' % layer)
                else:
                    record.append(u'%s 比对OK\n' % layer)
            if record:
                with open(self.comparsion_log, 'a') as w:
                    w.writelines(record)
            msg_list = []
            if enter_board_layers:
                msg_list.append(u'临时层有物件进入板内！<br>请查看%s' % u'、'.join(['%s+++enter_board' % enter_board_layer for enter_board_layer in enter_board_layers]))
            if diff_layers:
                for diff_layer in diff_layers:
                    msg_list.append(u'%s和%s比对有差异！请检查%s' % (diff_layer[0], diff_layer[1], diff_layer[2]))
            if msg_list:
                msg = '<span>%s<br><font style="color:red;">检测到异常，即将异常退出</font></span>' % '<br>'.join(msg_list)
                QMessageBox.warning(self, u'提示', msg)
                sys.exit(1)
            else:
                QMessageBox.information(self, u'提示', u'比对通过！')
                sys.exit()
        else:
            if not self.listWidget_2.selectedItems():
                QMessageBox.warning(None, u'警告', u'请选择层！')
                return
            # get_sr_area_flatten("surface_fill")
            resolution = self.comboBox_resolution.currentText()
            resolution = float(resolution)
            layers = [str(item.text()) for item in self.listWidget_2.selectedItems()]
            board_layers = self.job.matrix.returnRows('board')
            step = gen.Step(self.job, 'panel')
            flipstep = gen.Step(self.job, "edit")
            self.flipStepName(step.name)
            # # 如果阴阳拼版 把属性取消
            dic_drill_start_end = self.get_drill_start_end_layers()
            step.initStep()
            # step.setUnits('inch')
            diff_layers = []
            for layer in layers:
                for i in range(self.listWidget_2.count()):
                    if self.listWidget_2.item(i).text() == layer:
                        index = i
                        break
                formal_layer = self.tableWidget_2.cellWidget(index, 0).currentText()
                # formal_layer = layer.split('-ls')[0]
                tmp_layer = '%s+++%s' % (layer, step.pid)
                tmp_formal_layer = '%s+++%s' % (formal_layer, step.pid)
                if self.flipList:
                    # 临时层是board
                    if layer in board_layers:
                        step.Flatten(formal_layer, tmp_formal_layer)
                        flipstep.open()
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % jobname)
                        self.job.COM(
                            "matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(jobname, layer))
                        self.job.COM(
                            "matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(jobname,
                                                                                                        formal_layer))
                        new_dic_drill_start_end = self.get_drill_start_end_layers()
                        for key, value in new_dic_drill_start_end.iteritems():
                            if value["start"] and value["end"]:

                                for new_key in [key, key.split("-bf")[0]]:
                                    if not dic_drill_start_end.has_key(new_key):
                                        continue

                                    if dic_drill_start_end[new_key]["start"] == value["start"] and \
                                            dic_drill_start_end[new_key]["end"] == value["end"]:
                                        continue
                                    # start end 可能是正式层也可能是临时层 也可能跟目前这两层没关系
                                    start = formal_layer if dic_drill_start_end[new_key]["start"] == layer else \
                                    dic_drill_start_end[new_key]["start"]
                                    end = formal_layer if dic_drill_start_end[new_key]["end"] == layer else \
                                    dic_drill_start_end[new_key]["end"]
                                    self.job.COM(
                                        "matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(
                                            jobname, key, start, end
                                        ))
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % jobname)
                        step.open()
                        step.Flatten(layer, tmp_layer)
                        # 还原
                        flipstep.open()
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % jobname)
                        self.job.COM(
                            "matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(jobname, layer))
                        self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(jobname,
                                                                                                                formal_layer))
                        new_dic_drill_start_end = self.get_drill_start_end_layers()
                        for key, value in new_dic_drill_start_end.iteritems():
                            if value["start"] and value["end"]:
                                for new_key in [key, key.split("-bf")[0]]:
                                    if not dic_drill_start_end.has_key(new_key):
                                        continue
                                    if dic_drill_start_end[new_key]["start"] == value["start"] and \
                                            dic_drill_start_end[new_key]["end"] == value["end"]:
                                        continue
                                    self.job.COM(
                                        "matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(
                                            jobname, key, dic_drill_start_end[new_key]["start"],
                                            dic_drill_start_end[new_key]["end"]
                                        ))
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % jobname)
                        step.open()
                    else:
                        step.Flatten(layer, tmp_layer)
                    # 正式层是board
                    if formal_layer in board_layers:
                        step.Flatten(layer, tmp_layer)
                        flipstep.open()
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % jobname)
                        self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(jobname,
                                                                                                                formal_layer))
                        self.job.COM(
                            "matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(jobname, layer))
                        new_dic_drill_start_end = self.get_drill_start_end_layers()
                        for key, value in new_dic_drill_start_end.iteritems():
                            if value["start"] and value["end"]:

                                for new_key in [key, key.split("-bf")[0]]:
                                    if not dic_drill_start_end.has_key(new_key):
                                        continue

                                    if dic_drill_start_end[new_key]["start"] == value["start"] and \
                                            dic_drill_start_end[new_key]["end"] == value["end"]:
                                        continue
                                    # start end 可能是正式层也可能是临时层 也可能跟目前这两层没关系
                                    start = layer if dic_drill_start_end[new_key]["start"] == formal_layer else \
                                    dic_drill_start_end[new_key]["start"]
                                    end = layer if dic_drill_start_end[new_key]["end"] == formal_layer else \
                                    dic_drill_start_end[new_key]["end"]
                                    self.job.COM(
                                        "matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(
                                            jobname, key, start, end))
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % jobname)
                        step.open()
                        step.Flatten(formal_layer, tmp_formal_layer)
                        # 还原
                        flipstep.open()
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % jobname)
                        self.job.COM(
                            "matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(jobname,
                                                                                                        formal_layer))
                        self.job.COM(
                            "matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(jobname, layer))
                        new_dic_drill_start_end = self.get_drill_start_end_layers()
                        for key, value in new_dic_drill_start_end.iteritems():
                            if value["start"] and value["end"]:

                                for new_key in [key, key.split("-bf")[0]]:
                                    if not dic_drill_start_end.has_key(new_key):
                                        continue

                                    if dic_drill_start_end[new_key]["start"] == value["start"] and \
                                            dic_drill_start_end[new_key]["end"] == value["end"]:
                                        continue

                                    self.job.COM(
                                        "matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(
                                            jobname, key, dic_drill_start_end[new_key]["start"],
                                            dic_drill_start_end[new_key]["end"]
                                        ))
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % jobname)
                        step.open()
                    else:
                        step.Flatten(formal_layer, tmp_formal_layer)
                else:
                    step.Flatten(layer, tmp_layer)
                    step.Flatten(formal_layer, tmp_formal_layer)
                map_layer = '%s_bf_check_compare_diff+++' % formal_layer
                step.removeLayer(map_layer)
                step.compareLayers(tmp_layer, self.job.name, step.name, tmp_formal_layer, tol=resolution * 25.4,
                                   map_layer=map_layer, map_layer_res=5080)
                # 获取区域
                # areas = []
                # layer_cmd = gen.Layer(step, tmp_formal_layer)
                # step.affect(tmp_formal_layer)
                # step.selectSymbol('sh-op*')
                # step.resetFilter()
                # if step.Selected_count():
                #     feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]
                #     for obj in feat_out:
                #         step.clearSel()
                #         step.selectByIndex(tmp_formal_layer, obj.feat_index)
                #         xmin, ymin, xmax, ymax = get_layer_selected_limits(step, tmp_formal_layer)
                #         areas.append([xmin - 0.5, ymin - 0.5, xmax + 0.5, ymax + 0.5])
                #         step.clearSel()
                # step.setFilterTypes('text')
                # step.selectAll()
                # step.resetFilter()
                # if step.Selected_count():
                #     feat_text = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["text"]
                #     feat_barcodes = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["barcodes"]
                #     for obj in feat_text:
                #         for week_text in ["$$yy", "$${yy}", "$$ww", "$${ww}", "$$month", "$${month}",
                #                           "$$day", "$${day}", "$$banci", "$${banci}", "$$xingqi", "$${xingqi}",
                #                           "$$picihao", "$${picihao}", "$$mm", "$${mm}", "$$dd", "$${dd}", "$$year",
                #                           "$${year}"]:
                #             if week_text in obj.text.replace("'", "").lower():
                #                 step.clearSel()
                #                 step.selectByIndex(tmp_formal_layer, obj.feat_index)
                #                 xmin, ymin, xmax, ymax = get_layer_selected_limits(step, tmp_formal_layer)
                #                 areas.append([xmin - 0.5, ymin - 0.5, xmax + 0.5, ymax + 0.5])
                #                 step.clearSel()
                #                 break
                #     for obj in feat_barcodes:
                #         for week_text in ["$$yy", "$${yy}", "$$ww", "$${ww}", "$$month", "$${month}",
                #                           "$$day", "$${day}", "$$banci", "$${banci}", "$$xingqi", "$${xingqi}",
                #                           "$$picihao", "$${picihao}", "$$mm", "$${mm}", "$$dd", "$${dd}", "$$year",
                #                           "$${year}"]:
                #             if week_text in obj.text.replace("'", "").lower():
                #                 step.clearSel()
                #                 step.selectByIndex(tmp_formal_layer, obj.feat_index)
                #                 xmin, ymin, xmax, ymax = get_layer_selected_limits(step, tmp_formal_layer)
                #                 areas.append([xmin - 0.5, ymin - 0.5, xmax + 0.5, ymax + 0.5])
                #                 step.clearSel()
                #                 break
                # step.unaffectAll()
                # area_layer = 'area_layer+++'
                # if areas:
                #     step.removeLayer(area_layer)
                #     step.createLayer(area_layer)
                #     step.affect(area_layer)
                #     for area in areas:
                #         step.addRectangle(area[0], area[1], area[2], area[3])
                #     step.unaffectAll()
                step.affect(map_layer)
                step.resetFilter()
                step.setFilterTypes('pad')
                step.setSymbolFilter('r0')
                # if step.isLayer(area_layer):
                #     step.refSelectFilter(area_layer, mode='cover')
                #     if step.Selected_count():
                #         step.selectDelete()
                # if step.isLayer("surface_fill"):
                #     step.refSelectFilter("surface_fill", mode='cover')
                # else:
                #     step.selectAll()
                step.selectAll()
                step.resetFilter()
                if step.Selected_count():
                    diff_layers.append([layer, formal_layer, map_layer])
                else:
                    step.removeLayer(map_layer)
                step.unaffectAll()
                # step.removeLayer(area_layer)
                step.removeLayer(tmp_layer)
                step.removeLayer(tmp_formal_layer)
            # step.removeLayer('surface_fill')
            record = []
            for layer in layers:
                diff = list(filter(lambda diff_layer: layer == diff_layer[0], diff_layers))
                if diff:
                    record.append(u'%s 比对异常\n' % layer)
                else:
                    record.append(u'%s 比对OK\n' % layer)
            if record:
                # print(record)
                with open(self.comparsion_log, 'a') as w:
                    w.writelines(record)
            if diff_layers:
                msg_list = []
                for diff_layer in diff_layers:
                    msg_list.append(u'%s和%s比对有差异！请检查%s' % (diff_layer[0], diff_layer[1], diff_layer[2]))
                msg = '<span>%s<br><font style="color:red;">检测到异常，即将异常退出</font></span>' % '\n'.join(msg_list)
                QMessageBox.warning(self, u'提示', msg)
                sys.exit(1)
            else:
                QMessageBox.information(self, u'提示', u'比对通过！')
                sys.exit()

    def flipStepName(self, step):
        """
        递归寻找出有镜像的step，并append到 flipList数组中
        :param step: step名
        :return: None
        """
        info = self.job.DO_INFO('-t step -e %s/%s -m script -d SR -p flip+step' % (jobname, step))
        step_flip_tuple = [(info['gSRstep'][i], info['gSRflip'][i]) for i in range(len(info['gSRstep']))]
        step_flip_tuple = list(set(step_flip_tuple))
        for (stepName, flip_yn) in step_flip_tuple:
            if flip_yn == 'yes':
                self.flipList.append(stepName)
            elif flip_yn == 'no':
                self.flipStepName(stepName)

    def get_drill_start_end_layers(self):
        matrixInfo = self.job.matrix.getInfo()
        dic_drill_start_end = {}
        for i, layer in enumerate(matrixInfo["gROWname"]):
            if matrixInfo["gROWlayer_type"][i] == "drill" and \
                    matrixInfo["gROWcontext"][i] == "board":
                row = matrixInfo["gROWname"].index(layer)
                gROWdrl_start = matrixInfo["gROWdrl_start"][row]
                gROWdrl_end = matrixInfo["gROWdrl_end"][row]
                dic_drill_start_end[layer] = {"start": gROWdrl_start, "end": gROWdrl_end, }

        return dic_drill_start_end


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    is_check_user = False
    if len(sys.argv) > 1:
        is_check_user = True
    jobname = os.environ.get('JOB')
    temporaryLayerComparsion = TemporaryLayerComparsion()
    temporaryLayerComparsion.show()
    sys.exit(app.exec_())
