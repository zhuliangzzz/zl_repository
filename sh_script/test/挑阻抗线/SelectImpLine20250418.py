#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:SelectImpLine.py
   @author:zl
   @time: 2025/3/24 8:40
   @software:PyCharm
   @desc:
   20250414 层名增加线距 线距铜 参考层信息
"""
import math
import os
import platform
import re
import sys
import time

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import SelectImpLineUI_pyqt4 as ui

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen
from get_erp_job_info import get_inplan_imp
from genesisPackages_zl import outsignalLayers, innersignalLayers, signalLayers

class SelectImpLine(QMainWindow, ui.Ui_MainWindow):
    def __init__(self):
        super(SelectImpLine, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.result_mode = 'tl_tmp_layer'
        self.split_up, self.split_down = 'imp--------', 'imp++++++++'
        self.work_mode_items = {u'内层': 'inner', u'外层': 'outer', u'全部': 'all'}
        self.comboBox_work_mode.addItems(dict(sorted(self.work_mode_items.items(), key=lambda d:d[1])).keys())
        self.lineEdit_line_width_tol.setText('0.1')
        self.lineEdit_line_spacing_tol.setText('0.1')
        self.lineEdit_step.setText('edit')
        self.pushButton_exec.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet('''
               QPushButton:hover{background:black;color:white;}
               QPushButton{font:11pt;background-color:#0081a6;color:white;}
               QMessageBox{font-size:10pt;}
               QListWidget::Item{height:24px;border-radius:1.5px;} QListWidget::Item:selected{background:#0081a6;color:white;}
               QStatusBar{color:red;}
               ''')
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

    def run(self):
        self.step = None
        # 线宽公差
        self.line_width_tol = 0.1
        if self.lineEdit_line_width_tol.text():
            self.line_width_tol = float(self.lineEdit_line_width_tol.text())
        # 线距公差
        self.spacing_tol = 0.1
        if self.lineEdit_line_spacing_tol.text():
            self.spacing_tol = float(self.lineEdit_line_spacing_tol.text())
        work_layer = self.comboBox_work_mode.currentText()
        # stepfilter
        step_filter = str(self.lineEdit_step.text())
        print(len(job.stepsList))
        try:
            if not job.stepsList:
                QMessageBox.warning(self, 'error', u'在料号中没有Step存在,将退出!')
                return
            elif len(job.stepsList) != 1:
                if step_filter:
                    self.steps = list(filter(lambda stepname: step_filter in stepname, job.stepsList))
                else:
                    self.steps = job.stepsList
                if len(self.steps) == 0:
                    QMessageBox.warning(self, 'error', u'根据脚本参数过滤出的step为空，请确认资料或脚本参数!')
                    return
                elif len(self.steps) == 1:
                    self.step = self.steps[0]
                else:
                    print('aaaaaaaaaa')
                    StepDialog(self)
            else:
                self.step = job.stepsList[0]
            if not self.step:
                QMessageBox.warning(self, 'error', u'请选择step!')
                return
            self.statusbar.showMessage(u'正在打开%s step...' % self.step)
            step = gen.Step(job, self.step)
            step.initStep()
            units = 'inch'
            step.setUnits(units)
            matrix = job.matrix.getInfo()
            matrix_ = {}
            for i in range(len(matrix.get('gROWname'))):
                matrix_[matrix.get('gROWname')[i]] = {'side': matrix.get('gROWside')[i]}
            return_code = self.getImpInfo(step)
            if return_code == -1:
                return
            self.statusbar.showMessage(u'挑阻抗线完成（特性:_tx_线宽_ref_参考层；差分:_cd_线宽_线距_ref_参考层；共面: _gm线距铜），请检查~')
            self.statusbar.setToolTip(u'<span style="color:red;">挑阻抗线完成（特性:_tx_线宽_ref_参考层；差分:_cd_线宽_线距_ref_参考层；共面: _gm线距铜），请检查~<span>')

        except Exception as e:
            QMessageBox.critical(self, 'error', str(e))
            return
        # finally:
        #     step.unaffectAll()
        #     self._deleteLayer([self.split_up, self.split_down, self.ref_lyr])

    def getImpInfo(self, step):
        self.statusbar.showMessage(u'获取阻抗信息...')
        arraylist_imp_info = get_inplan_imp(job.name.upper())
        time.sleep(0.5)
        if not arraylist_imp_info:
            self.statusbar.showMessage(u'没有阻抗信息，无法挑阻抗线.')
            return -1
        print(arraylist_imp_info)
        res = self.work_mode_items.get(unicode(self.comboBox_work_mode.currentText().toUtf8().data(), 'utf-8'))
        print('aaa', res )
        if res == "inner":
            signal_layers = innersignalLayers
        elif res == "outer":
            signal_layers = outsignalLayers
        else:
            signal_layers = signalLayers
        for worklayer in signal_layers:
            dic_ref_layer = {}  # 特性
            dic2_ref_layer = {}  # 差动
            spacing_layer = {}  # 间距
            spc2cu_layer, spc2cu2_layer = {}, {}  # 共面
            trace_layers = []
            for dic_imp_info in arraylist_imp_info:
                imodel = dic_imp_info['IMODEL']
                ref_layers = dic_imp_info["REF_LAYER_"]
                spc2cu = dic_imp_info["SPC2CU"]  # 有值为共面
                if ref_layers is None:
                    ref_layers = ""
                ref_layers = sorted([x.lower() for x in ref_layers.split("&")], key=lambda x: int(x[1:]))
                trace_layer = dic_imp_info["TRACE_LAYER_"]
                orig_width = dic_imp_info["ORG_WIDTH"]
                if trace_layer.lower() == worklayer:
                    if imodel == '特性':
                        trace_layers.append(worklayer)
                        if dic_ref_layer.get(orig_width, None):
                            if ref_layers not in dic_ref_layer[orig_width]:
                                dic_ref_layer[orig_width].append(ref_layers)
                        else:
                            dic_ref_layer[orig_width] = [ref_layers]
                        spc2cu_layer[orig_width] = spc2cu
                    elif imodel == '差动':
                        trace_layers.append(worklayer)
                        spacing_layer[orig_width] = dic_imp_info["ORG_SPC"]
                        if dic2_ref_layer.get(orig_width, None):
                            if ref_layers not in dic2_ref_layer[orig_width]:
                                dic2_ref_layer[orig_width].append(ref_layers)
                        else:
                            dic2_ref_layer[orig_width] = [ref_layers]
                        spc2cu2_layer[orig_width] = spc2cu
            if worklayer not in trace_layers:
                continue
            self.statusbar.showMessage(u'获取%s层特性阻抗线...' % worklayer)
            time.sleep(0.5)
            gen_layer = gen.Layer(step, worklayer)
            for orig_width, array_ref_layers in dic_ref_layer.iteritems():
                ids = []
                step.affect(worklayer)
                step.setFilterTypes('line|arc', 'positive')
                step.setSymbolFilter('r*')
                step.selectAll()
                step.resetFilter()
                if step.Selected_count():
                    feats = gen_layer.featout_dic_Index(options='feat_index+select')['lines']
                    for feat in feats:
                        orig_size_inch = feat.symbol.replace('r', '')
                        if orig_width - self.line_width_tol < float(orig_size_inch) < orig_width + self.line_width_tol:
                            ids.append(feat.feat_index)
                    feats = gen_layer.featout_dic_Index(options='feat_index+select')['arcs']
                    for feat in feats:
                        orig_size_inch = feat.symbol.replace('r', '')
                        if orig_width - self.line_width_tol < float(orig_size_inch) < orig_width + self.line_width_tol:
                            ids.append(feat.feat_index)
                step.clearSel()
                if ids:
                    if spc2cu_layer.get(orig_width):
                        tx_layer = worklayer + "_tx_gm{2}_{0}_ref_{1}".format(round(orig_width, 2), '_'.join(array_ref_layers[0]), spc2cu_layer.get(orig_width))
                    else:
                        tx_layer = worklayer + "_tx_{0}_ref_{1}".format(round(orig_width, 2), '_'.join(array_ref_layers[0]))
                    step.removeLayer(tx_layer)
                    for id in ids:
                        step.selectByIndex(worklayer, id)
                    step.copySel(tx_layer)
                step.unaffectAll()
            self.statusbar.showMessage(u'获取%s层差动阻抗线...' % worklayer)
            time.sleep(0.5)
            for orig_width, array_ref_layers in dic2_ref_layer.iteritems():
                ids = []
                spc_ = round(spacing_layer.get(orig_width), 2) # 线距
                step.affect(worklayer)
                step.setFilterTypes('line|arc', 'positive')
                step.setSymbolFilter('r*')
                step.selectAll()
                step.resetFilter()
                if step.Selected_count():
                    feats = gen_layer.featout_dic_Index(options='feat_index+select')['lines']
                    for feat in feats:
                        orig_size_inch = feat.symbol.replace('r', '')
                        if orig_width - self.line_width_tol < float(orig_size_inch) < orig_width + self.line_width_tol:
                            ids.append(feat.feat_index)
                    feats = gen_layer.featout_dic_Index(options='feat_index+select')['arcs']
                    for feat in feats:
                        orig_size_inch = feat.symbol.replace('r', '')
                        if orig_width - self.line_width_tol < float(orig_size_inch) < orig_width + self.line_width_tol:
                            ids.append(feat.feat_index)
                step.clearSel()
                if ids:
                    if spc2cu2_layer.get(orig_width):
                        cd_layer = worklayer + "_cd_gm{3}_{0}_{1}_ref_{2}".format(round(orig_width, 2), spc_, '_'.join(array_ref_layers[0]), spc2cu_layer.get(orig_width))
                    else:
                        cd_layer = worklayer + "_cd_{0}_{1}_ref_{2}".format(round(orig_width, 2), spc_, '_'.join(array_ref_layers[0]))
                    step.removeLayer(cd_layer)
                    for id in ids:
                        step.selectByIndex(worklayer, id)
                    step.copySel(cd_layer)
                step.unaffectAll()
            # 分析
            print('spacing', spacing_layer)
            print(dic2_ref_layer)
            # step.PAUSE('A')
            self.statusbar.showMessage(u'分析%s层差分阻抗线间距...' % worklayer)
            time.sleep(0.5)
            for orig_width, array_ref_layers in dic2_ref_layer.iteritems():
                spc_ = round(spacing_layer.get(orig_width), 2)
                if spc2cu2_layer.get(orig_width):
                    cd_layer = worklayer + "_cd_gm{3}_{0}_{1}_ref_{2}".format(round(orig_width, 2), spc_, '_'.join(array_ref_layers[0]), spc2cu_layer.get(orig_width))
                else:
                    cd_layer = worklayer + "_cd_{0}_{1}_ref_{2}".format(round(orig_width, 2), spc_, '_'.join(array_ref_layers[0]))
                # cd_ref = worklayer + "_cd_ref_{0}".format(orig_width)
                coors = []
                if step.isLayer(cd_layer):
                    # todo 线路分析spacing l2l
                    checklist = gen.Checklist(step, type='valor_analysis_signal')
                    checklist.action()
                    checklist.COM('chklist_cupd,chklist=%s,nact=1,params=((pp_layer=%s)(pp_spacing=20)(pp_r2c=10)(pp_d2c=10)(pp_sliver=4)(pp_min_pad_overlap=5)(pp_tests=Spacing)(pp_selected=All)(pp_check_missing_pads_for_drills=Yes)(pp_use_compensated_rout=No)(pp_sm_spacing=No)),mode=regular' % (checklist.type, cd_layer))
                    checklist.run()
                    checklist.clear()
                    checklist.copy()
                    if checklist.name in step.checks:
                        step.deleteCheck(checklist.name)
                    step.createCheck(checklist.name)
                    step.pasteCheck(checklist.name)
                    lines = checklist.INFO('-t check -e %s/%s/%s -m script -d MEAS -o index+action=1+category=l2l' % (jobname, step.name, checklist.name))
                    for line in lines:
                        datas = line.split()
                        spacing, xs, ys, xe, ye = float(datas[2]), float(datas[7]), float(datas[8]), float(datas[9]), float(datas[10])
                        if spacing_layer.get(orig_width) - self.spacing_tol < spacing < spacing_layer.get(orig_width) + self.spacing_tol:
                            coors.append([xs, ys, xe, ye])
                if coors:
                    # step.createLayer(cd_ref)
                    # step.affect(cd_ref)
                    # for coor in coors:
                    #     xs, ys, xe, ye = coor
                    #     step.addLine(xs, ys, xe, ye, 'r0')
                    # step.unaffectAll()
                    step.affect(cd_layer)
                    for coor in coors:
                        xs, ys, xe, ye = coor
                        step.COM('sel_net_feat,operation=select,x=%s,y=%s,tol=2.0888779528,use_ffilter=no' % (xs, ys))
                        step.COM('sel_net_feat,operation=select,x=%s,y=%s,tol=2.0888779528,use_ffilter=no' % (xe, ye))
                    if step.Selected_count():
                        step.selectReverse()
                        if step.Selected_count():
                            step.selectDelete()
                    step.unaffectAll()
            self.statusbar.showMessage(u'%s层阻抗线已挑出.' % worklayer)
            time.sleep(0.5)
        return 0

    def _deleteLayer(self, *args):
        layers = []
        [layers.extend(arg) for arg in args]
        for layer in layers:
            job.matrix.deleteRow(layer)

    def get_poly_lines(self, gen_step, layer):
        features = gen_step.INFO('-t layer -e %s/%s/%s -m script -d FEATURES' % (jobname, gen_step.name,layer))
        self.statusbar.showMessage(u'正在获得poly lines')
        lines = []
        polyline = {}
        for feature in features:
            if feature.startswith('#L'):
                lines.append(feature)
        polylines_flag = 1
        line_flag = 1
        for i in range(len(lines)):
            line_info1 = lines[i].split()
            line_info2 = lines[i+1].split()
            polyline[polylines_flag][line_flag] = {
                'xs': line_info1[1],
                'ys': line_info1[2],
                'xe': line_info1[3],
                'ye': line_info1[4],
                'symbol': line_info1[5],
            }
            if line_info1[3] == line_info2[1] and line_info1[4] == line_info2[2]:
                line_flag += 1
                polyline[polylines_flag][line_flag] = {
                    'xs': line_info2[1],
                    'ys': line_info2[2],
                    'xe': line_info2[3],
                    'ye': line_info2[4],
                    'symbol': line_info1[5],
                }
            else:
                polylines_flag += 1
                line_flag = 1
        return polyline

    def point2line_dist(self, x, y, line):
        # 如果线段长度为0，则无法计算垂直距离
        xs, ys, xe, ye = line.get('xs'), line.get('ys'), line.get('xe'), line.get('ye')
        if xs == xe and ys == ye:
            return None

        # 使用点到直线距离公式：|Ax + By + C|/√(A² + B²)
        # 其中直线方程为：Ax + By + C = 0
        # A = y2-y1, B = x1-x2, C = x2*y1 - x1*y2

        A = ye - ys
        B = xs - xe
        C = xe * ys - xs * ye

        # 计算垂直距离
        distance = abs(A * x + B * y + C) / math.sqrt(A * A + B * B)
        return distance

class StepDialog(QDialog):
    def __init__(self, parent=None):
        super(StepDialog, self).__init__(parent)
        self.stepList = sil.steps
        self.setupUI()
        self.exec_()

    def setupUI(self):
        self.setWindowTitle(u'请选择工作step')
        self.search_input = QLineEdit()
        self.listWidget = QListWidget()
        self.listWidget.addItems(self.stepList)
        self.search_input.textChanged.connect(self.search)
        layout = QVBoxLayout(self)
        btn_box = QHBoxLayout()
        ok = QPushButton(self)
        ok.setText(u'√确定')
        ok.setStyleSheet('background-color:#0081a6;color:white;')
        ok.setObjectName('dialog_ok')
        ok.setCursor(QCursor(Qt.PointingHandCursor))
        ok.clicked.connect(self.generate_stepstr)
        close = QPushButton(self)
        close.setText(u'×取消')
        close.setStyleSheet('background-color:#464646;color:white;')
        close.setObjectName('dialog_close')
        close.setCursor(QCursor(Qt.PointingHandCursor))
        close.clicked.connect(lambda: self.close())
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_box.addItem(spacerItem1)
        btn_box.addWidget(ok)
        btn_box.addWidget(close)
        layout.addWidget(self.search_input)
        layout.addWidget(self.listWidget)
        layout.addLayout(btn_box)
        self.setStyleSheet('QPushButton{font-family:黑体;font-size:10pt;}')

    def search(self):
        search_result = []
        key = str(self.search_input.text())
        if key:
            for step in self.stepList:
                if key in step:
                    search_result.append(step)
        else:
            search_result = self.stepList
        self.listWidget.clear()
        self.listWidget.addItems(search_result)

    def generate_stepstr(self):
        if not len(self.listWidget.selectedItems()):
            QMessageBox.warning(self, 'error', u'请选择step!')
            return
        sil.step = self.listWidget.selectedItems()[0].text()
        self.close()


if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    app = QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    sil = SelectImpLine()
    sil.show()
    sys.exit(app.exec_())
