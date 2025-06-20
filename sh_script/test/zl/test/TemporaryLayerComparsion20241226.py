#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:TemporaryLayerComparsion.py
   @author:zl
   @time: 2024/12/25 14:46
   @software:PyCharm
   @desc:
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
from genesisPackages import matrixInfo, signalLayers, outsignalLayers, innersignalLayers, silkscreenLayers, \
    solderMaskLayers
import genClasses_zl as gen

import TemporaryLayerComparsionUI_pyqt4 as ui


class TemporaryLayerComparsion(QWidget, ui.Ui_Form):
    def __init__(self):
        super(TemporaryLayerComparsion, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.job = gen.Job(jobname)
        self.temp_map = {}
        for row in self.job.matrix.returnRows():
            res = re.match(".*(-ls\d+.*)", row)
            if res:
                key = res.group(1)
                if key not in self.temp_map:
                    self.temp_map[key] = []
                self.temp_map[key].append(row)
        self.temp_layers = [i for val in self.temp_map.values() for i in val]  # 所有临时层
        self.layer_list = self.temp_layers  # 当前list中显示的临时层
        self.listWidget.addItems(self.temp_layers)
        self.comboBox_temp.addItem('')
        if self.temp_map.keys():
            self.comboBox_temp.addItems(self.temp_map.keys())
        self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.lineEdit_resolution.setValidator(QDoubleValidator(self.lineEdit_resolution))
        self.lineEdit_resolution.setText('2')
        #
        self.checkBox_all.clicked.connect(self.select_all)
        self.comboBox_temp.currentIndexChanged.connect(self.filter_temp)
        self.pushButton_exec.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet('''
        QPushButton:hover{background:black;color:white;}
        QPushButton{font:11pt;background-color:#0081a6;color:white;}
        QListWidget::Item{height:24px;border-radius:1.5px;} QListWidget::Item:selected{background:#0081a6;color:white;}
        ''')

    def filter_temp(self):
        text = str(self.comboBox_temp.currentText())
        self.listWidget.clear()
        if self.temp_map.get(text):
            self.layer_list = self.temp_map.get(text)
        else:
            self.layer_list = self.temp_layers
        self.listWidget.addItems(self.layer_list)

    def select_all(self):
        if self.checkBox_all.isChecked():
            self.listWidget.selectAll()
        else:
            self.listWidget.clearSelection()

    def run(self):
        if not self.listWidget.selectedItems():
            QMessageBox.warning(None, u'警告', u'请选择层！')
            return
        resolution = self.lineEdit_resolution.text()
        if not resolution:
            QMessageBox.warning(self, u'警告', u'比对精度不能为空')
            return
        resolution = float(resolution)
        layers = [str(item.text()) for item in self.listWidget.selectedItems()]
        step = gen.Step(self.job, 'panel')
        step.initStep()
        step.setUnits('inch')
        diff_layers = []
        for layer in layers:
            formal_layer = layer.split('-ls')[0]
            tmp_layer = '%s+++%s' % (layer, step.pid)
            tmp_formal_layer = '%s+++%s' % (formal_layer, step.pid)
            step.Flatten(layer, tmp_layer)
            step.Flatten(formal_layer, tmp_formal_layer)
            map_layer = '%s_check_compare_diff+++' % formal_layer
            step.removeLayer(map_layer)
            step.compareLayers(tmp_layer, self.job.name, step.name, tmp_formal_layer, tol=resolution, map_layer=map_layer, map_layer_res=50)
            step.affect(map_layer)
            step.resetFilter()
            step.setFilterTypes('pad')
            step.setSymbolFilter('r0')
            step.selectAll()
            step.resetFilter()
            if step.Selected_count():
                diff_layers.append([layer, formal_layer, map_layer])
            else:
                step.removeLayer(map_layer)
            step.unaffectAll()
            step.removeLayer(tmp_layer)
            step.removeLayer(tmp_formal_layer)

        if diff_layers:
            msg_list = []
            for diff_layer in diff_layers:
                msg_list.append(u'%s和%s比对有差异！请检查%s' % (diff_layer[0], diff_layer[1], diff_layer[2]))
            QMessageBox.warning(self, u'提示', '\n'.join(msg_list))
        else:
            QMessageBox.information(self, u'提示', u'比对通过！')
        sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    jobname = os.environ.get('JOB')
    temporaryLayerComparsion = TemporaryLayerComparsion()
    temporaryLayerComparsion.show()
    sys.exit(app.exec_())
