#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:FillConvert.py
   @author:zl
   @time:2023/03/13 15:15
   @software:PyCharm
   @desc: 铺铜方式转换
   20230324 处理print型号铺铜
   20230921 六边形连接
   20231007 增加set中新加的操作 panel中铺铜增加margin_x
"""
import os
import re
import sys

import qtawesome
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import FillConvertUI as ui

sys.path.append('/genesis/sys/scripts/zl/lib')
import genClasses as gen
import ZL_mysqlCon as zlmysql
import res_rc


class FillConvert(QWidget, ui.Ui_Form):
    def __init__(self):
        super(FillConvert, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        path = 'D:/scripts/images/photo'
        self.job = gen.Job(jobname)
        self.step = self.job.steps.get(stepname)
        self.dbcls = zlmysql.DBConnect()
        self.cursor = self.dbcls.cursor
        self.cus = None
        self.graph = {
            'surface': os.path.join(path, 'surface.png'),
            'cross': os.path.join(path, 'cross.png'),
            'lbx': os.path.join(path, 'lbx.png'),
            'hBrack': '/genesis/sys/scripts/wlh/photo/hBrackC.jpg',
            'vBrack': '/genesis/sys/scripts/wlh/photo/vBrackC.jpg',
            'hvBrack': '/genesis/sys/scripts/wlh/photo/hvBrackC.jpg',
            'dpad': '/genesis/sys/scripts/wlh/photo/dpad.jpg'
        }
        self.methods = ['实铜', '网格', '六边形']
        self.keys = ['surface', 'cross', 'lbx']
        self.signalLays = self.job.matrix.returnRows('board','signal')
        self.selectedList = None
        self.title.setText("Job:<font style='color:green'>%s</font>  Step:<font style='color:green'>%s</font>" % (
            jobname, stepname))
        self.jztype = '摄像头板' if re.search(r'ns$|ns-\w+$', jobname) else '电池板'
        __type = jobname[:2]
        if __type == 'fp':
            type_name = '软板'
        elif __type == 'rf':
            type_name = '软硬结合板'
        elif __type == 'pc':
            type_name = '硬板'
        else:
            type_name = '其他'
        self.board_type = 'soft' if jobname.startswith('fs') or jobname[2] == 'f' else 'softandhard'
        self.series.setText(f"<font style='color:green;'>{type_name}</font>")
        self.select_btn.setIcon(QIcon(qtawesome.icon('fa.search', scale_factor=1, color='white')))
        self.exec_btn.setIcon(qtawesome.icon('fa.upload', scale_factor=1, color='white'))
        self.exit_btn.setIcon(qtawesome.icon('fa.arrow-circle-o-right', scale_factor=1, color='white'))
        # self.setStyleSheet("#layer_input{color:#000;}QPushButton:hover{background:#99eeee;}")
        self.fillMethod.addItems(self.methods)
        self.shapeLabel.setPixmap(QPixmap(list(self.graph.values())[0]))
        self.select_btn.clicked.connect(self.select_layer)
        self.fillMethod.currentIndexChanged.connect(self.loadGraph)
        self.exec_btn.clicked.connect(self.exec)
        self.exit_btn.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            'QPushButton{font:11pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')

    def select_layer(self):
        dialog = LayerSelect()
        dialog.signal.connect(self.confirmSel)
        dialog.exec_()

    def loadGraph(self, index):
        # self.scene.clear()
        # self.scene.addPixmap(QPixmap(self.graph.get(self.keys[index])))
        # self.graphicsView.setAlignment(Qt.AlignJustify)
        self.shapeLabel.setPixmap(QPixmap(self.graph.get(self.keys[index])))

    def confirmSel(self):
        if self.selectedList:
            self.layer_input.setText(';'.join(self.selectedList))

    def exec(self):
        if not self.layer_input.text().strip():
            QMessageBox.warning(None, 'tips', "请选择层")
            return
        self.hide()
        methodIndex = self.fillMethod.currentIndex()
        self.step.initStep()
        self.step.resetFill()
        i = 0
        for layer in self.selectedList:
            if i % 2:
                direction = 'even'
                x_off = 0.9
                y_off = 0.9
            else:
                direction = 'odd'
                x_off = 0
                y_off = 0
            bak_ = layer + '-bak'
            temp_ = layer + '+++%s' % self.job.pid
            self.step.VOF()
            self.step.removeLayer(bak_)
            self.step.removeLayer(temp_)
            self.step.VON()
            self.step.affect(layer)
            self.step.copyToLayer(bak_)
            self.step.setAttrFilter2('.pattern_fill')
            self.step.selectAll()
            self.step.resetFilter()
            self.step.selectReverse()
            if self.step.Selected_count():
                self.step.moveSel(temp_)
            self.step.selectDelete()
            string = ';'.join([str(s) for s in list(set(self.step.info.get('gSRstep')))])
            self.step.srFill_2(step_margin_x=1, step_margin_y=1, stop_at_steps=string)
            if methodIndex == 0:  # 实铜
                pass
            elif methodIndex == 1:
                line_width = 200
                # 网格铜外围线宽
                outline_width = 400
                # 网格铜间距
                side_spacing = 600
                self.step.selectFill(type='standard', solid_type='surface', std_type='cross', x_off=x_off,
                                     y_off=y_off, std_line_width=line_width, std_step_dist=side_spacing,
                                     std_indent=direction, outline_draw='yes', outline_width=outline_width)
            elif methodIndex == 2:
                x_off = 4.2 if i % 2 else 0
                y_off = 0
                self.step.selectFill(type='pattern', dx=12.6, dy=7.3, solid_type='surface', symbol='lbx_fill',
                                     x_off=x_off, y_off=y_off, std_indent=direction, cut_prims='yes')
            elif methodIndex == 3:
                self.step.truncate(layer)
                self.step.unaffectAll()
                sr_xmin = self.step.sr2.xmin
                sr_xmax = self.step.sr2.xmax
                sr_ymin = self.step.sr2.ymin
                sr_ymax = self.step.sr2.ymax
                prof_xmin = self.step.profile2.xmin
                prof_xmax = self.step.profile2.xmax
                # 横竖砖块
                # 创建两个临时层，分别铺横砖块和竖砖块，再考回到inner_top,inner_bot
                tmp1 = 'tmp1+++%s' % self.step.pid
                tmp2 = 'tmp2+++%s' % self.step.pid
                gSRx = sr_xmin - 0.3
                gSRx2 = sr_xmax + 0.3
                self.step.VOF()
                self.step.removeLayer(tmp1)
                self.step.removeLayer(tmp2)
                self.step.VON()
                self.step.createLayer(tmp1)
                self.step.createLayer(tmp2)
                # inner_top
                self.step.affect(tmp1)
                self.step.addPolyline(prof_xmin, sr_ymin, gSRx, sr_ymax, 'r200')
                self.step.addPolyline(gSRx2, sr_ymin, prof_xmax, sr_ymax, 'r200')
                self.step.selectCutData()
                self.step.unaffectAll()
                self.step.affect(tmp2)
                self.step.srFill_2(step_margin_y=1.5, sr_margin_x=0.3, sr_margin_y=0.3, stop_at_steps=string)
                self.step.unaffectAll()
                self.step.affect(tmp1)
                self.step.copySel(tmp2, 'yes')
                self.step.selectFill(type='pattern', dx=3.6, dy=3.3, solid_type='surface', symbol='ww', x_off=x_off,
                                         y_off=y_off, std_indent=direction, cut_prims='yes')
                self.step.copySel(layer)
                self.step.unaffectAll()
                self.step.affect(tmp2)
                self.step.Contourize()
                self.step.selectFill(type='pattern', dx=3.3, dy=3.6, solid_type='surface', symbol='qq', x_off=x_off,
                                         y_off=y_off, std_indent=direction, cut_prims='yes')
                self.step.copySel(layer)
                self.step.unaffectAll()
                # 删除临时层
                self.step.VOF()
                self.step.removeLayer(tmp1)
                self.step.removeLayer("%s+++" % tmp1)
                self.step.removeLayer(tmp2)
                self.step.VON()
                self.step.affect(layer)
            elif methodIndex == 4:
                x_off = 0
                y_off = 0.77782 if i % 2 else 0
                self.step.selectFill(type='pattern', dx=1.55564, dy=1.55564, solid_type='surface',
                                         symbol='csx-cros', x_off=x_off, y_off=y_off, std_indent=direction,
                                         cut_prims='yes')
            elif methodIndex == 5:
                x_off = 3 if i % 2 else 0
                y_off = 0
                self.step.selectFill(type='pattern', dx=8.55, dy=4.95, solid_type='surface', symbol='lbx_fill',
                                         x_off=x_off, y_off=y_off, std_indent=direction, cut_prims='yes')
            self.step.selectResize(-150)
            self.step.selectResize(150)
            self.step.resetFill()
            self.step.unaffectAll()
            if self.step.isLayer(temp_):
                self.step.affect(temp_)
                self.step.copyToLayer(layer)
                self.step.unaffectAll()
                self.step.removeLayer(temp_)
            i += 1
        QMessageBox.information(None, "tips", "运行完毕，请检查")
        sys.exit()


class LayerSelect(QDialog):
    signal = pyqtSignal(int)

    def __init__(self):
        super(LayerSelect, self).__init__()
        layout = QVBoxLayout(self)
        label = QLabel("选择层")
        label.setStyleSheet("font-weight:bold;")
        label.setAlignment(Qt.AlignCenter)
        self.layerList = QListWidget()
        self.layerList.setSelectionMode(QAbstractItemView.MultiSelection)
        self.layerList.addItems(fillCovert.signalLays)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.confirm)  # 点击ok
        buttons.rejected.connect(self.reject)
        layout.addWidget(label)
        layout.addWidget(self.layerList)
        layout.addWidget(buttons)
        layout.setStretch(0, 1)
        layout.setStretch(1, 0)
        self.setLayout(layout)
        self.setWindowTitle('线路层列表')
        self.setStyleSheet('''
        QListWidget{
            outline: 0px;
            border:0px;
            min-width: 100px;
            color: Black;
            font:14px;
        }
        QListWidget::Item{
             height:26px;
        }
        ''')

    def confirm(self):
        fillCovert.selectedList = [item.text() for item in self.layerList.selectedItems()]
        self.signal.emit(1)
        self.hide()

    def reject(self):
        self.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet('QMessageBox{font:10pt;font-weight:bold;}')
    app.setWindowIcon(QIcon(':/res/demo.png'))
    if not os.environ.get('JOB'):
        QMessageBox.warning(None, 'tips', '请打开料号！')
        sys.exit()
    jobname = os.environ.get('JOB')
    if not os.environ.get('STEP'):
        QMessageBox.warning(None, 'tips', '请打开step！')
        sys.exit()
    stepname = os.environ.get('STEP')
    if stepname != 'set' and stepname != 'pnl':
        QMessageBox.warning(None, 'tips', '本脚本在set或panel中执行！')
        sys.exit()
    fillCovert = FillConvert()
    fillCovert.show()
    sys.exit(app.exec_())
