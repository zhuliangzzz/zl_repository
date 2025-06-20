#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:LaserCarvingInput.py
   @author:zl
   @time: 2024/10/22 10:53
   @software:PyCharm
   @desc:镭雕输出回读
"""
import glob
import os
import re
import sys
import platform

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genCOM_26
GEN = genCOM_26.GEN_COM()

from PyQt4 import QtCore, QtGui

import LaserCarvingInputUI_pyqt4 as ui
class LaserCarvingInput(QtGui.QWidget, ui.Ui_Form):
    def __init__(self):
        super(LaserCarvingInput, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.all_files = []
        self.path = '/id/workfile/film/'
        self.lineEdit.setText(self.path + jobname)
        self.pushButton_select.clicked.connect(self.selectPath)
        self.lineEdit.returnPressed.connect(self.search_files)
        self.listWidget.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.pushButton_exec.clicked.connect(self.input)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.search_files()
        # filepath = QtGui.QFileDialog.getOpenFileName(None, "Open File", self.path + jobname,
        #                                              "Text Files (*.txt);;All Files (*)")
        # if filepath:
        #     side = filepath.split('/')[-1].split('.')[0].split('_')[-1]
        #     self.reread_2dbc_file(filepath, side)
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)
        self.setStyleSheet(
            'QPushButton{font:9pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')

    def selectPath(self):
        path_dialog = QtGui.QFileDialog()
        path_dialog.setOption(QtGui.QFileDialog.DontUseNativeDialog, False)
        dir = path_dialog.getExistingDirectory(self, "选择路径", self.path + jobname)
        if dir:
            self.path = dir
            self.lineEdit.setText(self.path)
            self.search_files()

    def search_files(self):
        try:
            self.path = str(self.lineEdit.text())
        except Exception as e:
            print e
            QtGui.QMessageBox.warning(self, u'警告',u'路径不能含有中文')
            return
        self.all_files = []
        self.listWidget.clear()
        self.get_files(self.path)
        self.listWidget.addItems(self.all_files)

    def get_files(self, folder_path):
        for _, _, files in os.walk(folder_path):
            self.all_files = list(filter(lambda name: name.endswith('.txt'), files))


    def input(self):
        input_files = [item.text() for item in self.listWidget.selectedItems()]
        if not input_files:
            QtGui.QMessageBox.warning(self, 'tips', u'请选择要导入的文件')
            return
        for input_file in input_files:
            side = input_file.split('.')[0].split('_')[-1]
            self.reread_2dbc_file(input_file, side)
        QtGui.QMessageBox.information(self, 'tips', u'导入完成')
    def reread_2dbc_file(self, file_name, side):
        pnl_check_layer = 'f_dc-%s' % side
        GEN.DELETE_LAYER(pnl_check_layer)
        GEN.CREATE_LAYER(pnl_check_layer)
        heads = []
        marks = []
        all_cors = []
        pnl_cors = []
        head_end = 'no'
        mark_start = 'no'
        mark_end = 'no'
        with open(self.path + '/' + file_name, 'r') as f1:
            list1 = f1.readlines()

        for line in list1:
            cur_line = line.strip('\n')
            if head_end == 'no':
                heads.append(cur_line)

            if cur_line == '#####':
                if head_end == 'no':
                    mark_start = 'yes'
                    head_end = 'yes'
                elif head_end == 'yes' and mark_start == 'yes':
                    mark_end = 'yes'

            if mark_start == 'yes' and mark_end == 'no' and cur_line != '#####':
                # marks.append(cur_line)
                cur_cor = self.parse_cor(cur_line, type='mark_cor')
                marks.append(cur_cor)

            if head_end == 'yes' and mark_end == 'yes' and cur_line != '#####':
                # all_cors.append(cur_line)
                cur_cor = self.parse_cor(cur_line)
                all_cors.append(cur_cor)

        GEN.AFFECTED_LAYER(pnl_check_layer, 'yes')
        for al_cor in all_cors:
            GEN.ADD_TEXT(al_cor['x'], al_cor['y'], 'Fset%s-pcs%s' % (al_cor['set_index'], al_cor['unit_index']),
                         1.27, 2.54, angle=al_cor['angle'])
        for m_cor in marks:
            GEN.ADD_TEXT(m_cor['x'], m_cor['y'], 'Fp', 1.27, 2.54)
        GEN.CLEAR_LAYER()



    def parse_cor(self, ip_line, type='bc_cor'):
        if type == 'bc_cor':
            m = re.match('X=(.*);Y=(.*);Ang=(.*);Type=(\d);Set=(.*);Unit=(.*);UseBarcodeSize=(\d);UseTextSize=(\d)',
                         ip_line)
            if m:
                cordict = dict(x=m.group(1), y=m.group(2), angle=m.group(3), bc_type=m.group(4), set_index=m.group(5),
                               unit_index=m.group(6), use_bc_size=m.group(7), use_text_size=m.group(8))
        if type == 'mark_cor':
            m = re.match('X=(.*);Y=(.*)', ip_line)
            if m:
                cordict = dict(x=m.group(1), y=m.group(2))
        return cordict


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    jobname = os.environ.get('JOB')
    laserCarvingInput = LaserCarvingInput()
    laserCarvingInput.show()
    sys.exit(app.exec_())
