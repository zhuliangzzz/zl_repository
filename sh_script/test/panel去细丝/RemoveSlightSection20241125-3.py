#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:RemoveSlightSection20241125.py
   @author:zl
   @time: 2024/11/22 12:09
   @software:PyCharm
   @desc:
"""
import os
import re
import sys
import platform

from PyQt4 import QtCore, QtGui

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen
# from genesisPackages import outsignalLayers
import RemoveSlightSectionUI_pyqt4 as ui

class RemoveSlightSection(QtGui.QWidget, ui.Ui_Form):
    def __init__(self):
        super(RemoveSlightSection, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        signals = job.matrix.returnRows('board', 'signal|power_ground')
        # for signal in outsignalLayers:
        #     signals.remove(signal)
        # print signals
        self.listWidget.addItems(signals)
        self.listWidget.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.lineEdit_size.setValidator(QtGui.QDoubleValidator(self.lineEdit_size))
        self.lineEdit_size.setText('6')
        self.lineEdit_bak_name.setText('_bak')
        self.checkBox.clicked.connect(self.select_all)
        self.pushButton_exec.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)
        # self.setStyleSheet(
        #     'QPushButton{background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')
        self.setStyleSheet(
            '''QPushButton {background:rgb(49,194,124);color:white;} QPushButton:hover{background:#F7D674; color:black;}
            QListWidget{outline: 0px;border:0px;min-width: 260px;color:black;background:white;font:14px;}
            QComboBox{background:#0081a6;}
            QComboBox:hover,QListWidget::Item:hover{background:#F7D674; color:black;}
            QListWidget::Item{height:24px;border-radius:1.5px;} QMessageBox{font-size:10pt;} QListWidget::Item:selected{background:rgb(49,194,124);color:white;}''')

    def select_all(self):
        if self.checkBox.isChecked():
            self.listWidget.selectAll()
        else:
            self.listWidget.clearSelection()

    def run(self):
        if not self.listWidget.selectedItems():
            QtGui.QMessageBox.warning(None, u'警告', u'请选择层！')
            return
        section_size = self.lineEdit_size.text()  # 细丝大小
        if not section_size:
            QtGui.QMessageBox.warning(self, u'提示', u'细丝大小不能为空')
            return
        # self.hide()
        section_size = float(section_size)
        bak_name = self.lineEdit_bak_name.text()
        layers = [item.text() for item in self.listWidget.selectedItems()]
        step = gen.Step(job, 'panel')
        step.initStep()
        step.setUnits('inch')
        for layer in layers:
            tmp_signal = layer + '+++'
            tmp_surface = layer + '_surface'
            tmp_symbol = layer + '_symbol'
            tmp_symbol_ = layer + '_symbol+++'
            bak_layer = layer + bak_name   # 备份层
            step.removeLayer(tmp_signal)
            step.removeLayer(tmp_surface)
            step.removeLayer(tmp_symbol)
            step.removeLayer(tmp_symbol_)
            step.affect(layer)
            step.copySel(bak_layer)
            step.copySel(tmp_signal)
            step.unaffectAll()
            step.affect(tmp_signal)
            # step.affect(layer)
            step.setFilterTypes('surface')
            # step.setAttrFilter('.pattern_fill')
            step.selectAll()
            if step.Selected_count():
                step.copySel(tmp_surface)
                step.selectAll()
                step.selectReverse()
                if step.Selected_count():
                    step.copySel(tmp_symbol)
            else:
                step.removeLayer(tmp_signal)
                continue
            step.unaffectAll()
            step.resetFilter()
            info = step.Features_INFO(tmp_symbol, 'feat_index')
            index_list = []
            for line in info:
                if line and re.match('#\d+', line[0]):
                    index_list.append(int(line[0].replace('#', '')))
            for index in index_list:
                step.affect(tmp_symbol)
                step.selectByIndex(tmp_symbol, index)
                step.copySel(tmp_symbol_)
                step.unaffectAll()
                step.affect(tmp_symbol_)
                step.selectBreak()
                step.unaffectAll()
            step.affect(tmp_symbol_)
            step.setFilterTypes(polarity='positive')
            step.selectAll()
            step.resetFilter()
            if step.Selected_count():
                step.selectDelete()
            # 上下板边有跟负性线排除掉
            step.setFilterTypes('line', 'negative')
            step.setSymbolFilter('r0*')
            step.selectAll()
            step.resetFilter()
            if step.Selected_count():
                step.selectDelete()
            step.selectPolarity()
            # 有些symbol是负性的外形线 这里填充一下
            # step.selectCutData(ignore_width='no') #  不忽略线宽
            step.COM('sel_cut_data,det_tol=1,con_tol=1,rad_tol=0.1,ignore_width=no,filter_overlaps=no,delete_doubles=no,use_order=yes,ignore_holes=none,start_positive=yes,polarity_of_touching=same,contourize=yes,simplify=yes,resize_thick_lines=no')
            step.Contourize(0)
            step.unaffectAll()
            step.affect(tmp_surface)
            step.clip_area(margin=0, ref_layer=tmp_symbol_)
            step.selectResize(-section_size)
            step.selectResize(section_size)
            step.unaffectAll()
            step.affect(tmp_symbol)
            step.copySel(tmp_surface)
            step.unaffectAll()
            # 先将layer层清除
            step.truncate(layer)
            step.affect(tmp_surface)
            step.moveSel(layer)
            step.unaffectAll()
            step.removeLayer(tmp_signal)
            step.removeLayer(tmp_surface)
            step.removeLayer(tmp_symbol)
            step.removeLayer(tmp_symbol_)
            step.removeLayer(tmp_symbol_ + '+++')
        QtGui.QMessageBox.information(self, u'提示',  u'执行完成！请检查')
        sys.exit()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    if 'panel' not in job.getSteps():
        QtGui.QMessageBox.warning(None, u'警告', u'没有panel')
        sys.exit()
    window = RemoveSlightSection()
    window.show()
    sys.exit(app.exec_())
