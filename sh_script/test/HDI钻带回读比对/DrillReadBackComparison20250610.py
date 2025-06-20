#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:DrillReadBackComparison.py
   @author:zl
   @time: 2024/12/19 9:16
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
import genClasses_zl as gen
import DrillReadBackComparisonUI_pyqt4 as ui


class DrillReadBackComparison(QWidget, ui.Ui_Form):
    def __init__(self):
        super(DrillReadBackComparison, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.jobname = os.environ.get("JOB")
        self.job = gen.Job(self.jobname)
        self.stepname = os.environ.get("STEP")
        self.step = gen.Step(self.job, self.stepname)
        self.label_title.setText('Job:%s Step:%s' % (self.jobname, self.stepname))
        self.checkBox_auto_compare.setChecked(True)
        header = [u'勾选', u'钻带文件', u'钻孔层']
        self.tableWidget.setColumnCount(len(header))
        self.tableWidget.setHorizontalHeaderLabels(header)
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setResizeMode(2, QHeaderView.Stretch)
        self.tableWidget.setColumnWidth(0, 40)
        self.tableWidget.setSelectionBehavior(QHeaderView.SelectRows)
        self.tableWidget.setSelectionMode(QHeaderView.SingleSelection)
        self.tableWidget.setEditTriggers(QHeaderView.NoEditTriggers)
        self.setStyleSheet(
            '#pushButton_exec,#pushButton_exit {font:11pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;color:white;}QTableWidget::Item:selected{background: rgb(224, 224, 224);color:black;}')

        # --设定参数文件路径
        self.filePath = '/tmp/get_reread_drill_file_scripts_para'
        if platform.system() == "Windows":
            self.filePath = 'C:/tmp/get_reread_drill_file_scripts_para'
        self.drill_layer = list(filter(lambda _:not _.startswith('filebak'), self.job.matrix.returnRows(type='drill') + ['']))
        # --设定回读文件路径
        self.set_path()
        self.load_table()
        self.radioButton_machinery.clicked.connect(self.load_table)
        self.radioButton_laser.clicked.connect(self.load_table)
        self.lineEdit_path.returnPressed.connect(self.load_table)
        self.pushButton_path.clicked.connect(self.select_path)
        self.pushButton_exec.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.checkBox_select_all.clicked.connect(self.check_all)

    def set_path(self):
        # self.get_para_path = ''
        # if os.path.exists(self.filePath):
        # with open(self.filePath, 'r') as f:
        # self.get_para_path = f.read().strip()
        if sys.platform == "win32":
            self.get_para_path = ur"\\192.168.2.57\临时文件夹\系列资料临时存放区\{0}系列\{1}\{2}".format(self.jobname[1:4].upper(),self.jobname.split('-')[0].upper(), self.jobname.split('-')[0][-2:].upper())
        else:
            # self.get_para_path = u"/windows/33.file/{0}系列/{1}/{2}".format(self.jobname[1:4].upper(),self.jobname.split('-')[0].upper(), self.jobname.split('-')[0][-2:].upper())
            self.get_para_path = u"/id/workfile/hdi_film/{0}".format(self.jobname.split('-')[0])
        self.lineEdit_path.setText(self.get_para_path)

    def select_path(self):
        directory = QFileDialog.getExistingDirectory(self, u"选择文件夹", self.get_para_path, QFileDialog.ShowDirsOnly)
        if directory:
            self.lineEdit_path.setText(directory)
            self.load_table()
    def check_all(self):
        if self.checkBox_select_all.isChecked():
            for row in range(self.tableWidget.rowCount()):
                self.tableWidget.cellWidget(row, 0).setChecked(True)
        else:
            for row in range(self.tableWidget.rowCount()):
                self.tableWidget.cellWidget(row, 0).setChecked(False)
    def load_table(self):
        self.tableWidget.setRowCount(0)
        self.tableWidget.clearContents()
        self.checkBox_select_all.setChecked(False)
        file_path = str(self.lineEdit_path.text())
        if not os.path.exists(file_path):
            QMessageBox.warning(None, u'提示', u'路径%s不存在' % str(self.lineEdit_path.text()))
            return
        files = filter(lambda x: os.path.isfile(os.path.join(file_path, x)) and '.tgz' not in x, os.listdir(file_path))
        # 过滤s数字-数字的作为镭射类，其他的为机械类
        laser_layers, machinery_layers = {}, {}  # key：层名   value:文件名
        for file in files:
            if self.jobname[:13] + '.' in file:
                layer = file.split(self.jobname[:13] + '.')[-1]
                if re.match('s\d+-\d+', layer):
                    if layer.endswith('.write'):
                        layer = re.findall('s\d+-\d+',layer)[0]
                        laser_layers[layer] = file
                else:
                    machinery_layers[layer] = file
        if self.radioButton_machinery.isChecked():
            # 机械
            files = machinery_layers
        else:
            # 镭射
            files = laser_layers
        print(files)
        self.tableWidget.setRowCount(len(files))
        row = 0
        for layer, file in files.items():
            check = QCheckBox()
            check.setStyleSheet('margin-left:10px;')
            self.tableWidget.setCellWidget(row, 0, check)
            item = QTableWidgetItem(file)
            item.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(row, 1, item)
            comboBox = QComboBox()
            comboBox.addItems(self.drill_layer)
            if layer in self.drill_layer:
                current_index = comboBox.findText(layer)
                if current_index >= 0:
                    comboBox.setCurrentIndex(current_index)
            else:
                comboBox.setCurrentIndex(-1)
            self.tableWidget.setCellWidget(row, 2, comboBox)
            row += 1

    def run(self):
        flag = False
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.cellWidget(row, 0).isChecked():
                flag = True
                break
        if not flag:
            QMessageBox.information(self, u'提示', u'未勾选层')
            return
        # 比对异常的层
        self.err_info = []
        if self.radioButton_machinery.isChecked():
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.cellWidget(row, 0).isChecked():
                    file = str(self.tableWidget.item(row, 1).text())
                    layer = str(self.tableWidget.cellWidget(row, 2).currentText())
                    if not layer:
                        continue
                    self.check_file(os.path.join(str(self.lineEdit_path.text()), file), 1)
                    self.input_file()
        else:
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.cellWidget(row, 0).isChecked():
                    file = str(self.tableWidget.item(row, 1).text())
                    layer = str(self.tableWidget.cellWidget(row, 2).currentText())
                    if not layer:
                        continue
                    self.check_file(os.path.join(str(self.lineEdit_path.text()), file), 0)
                    self.input_file()
        if self.err_info:
            QMessageBox.warning(self, u'比对结果', '\n'.join(self.err_info), QMessageBox.Ok)
        else:
            QMessageBox.information(self, u'提示', u'完成退出!', QMessageBox.Ok)
        sys.exit(0)

    # 机械1 镭射0
    def check_file(self, file_path, type=1):
        if type:
            if sys.platform == "win32":
                filearray = file_path.split('\\')
            else:
                filearray = file_path.split('/')
            if len(filearray) > 0:
                self.file_bak = 'filebak_' + filearray[len(filearray) - 1]
            else:
                self.file_bak = 'filebak_' + filearray[len(filearray)]

            self.file_bak_path = '/tmp/' + self.file_bak
            if platform.system() == "Windows":
                self.file_bak_path = 'D:\\tmp\\' + self.file_bak

            if not os.path.exists(file_path):
                file_path = file_path.decode("utf8")

            if os.path.exists(file_path):
                g82_g83 = re.compile('(G82|G83)(X(-?)(\d+)Y(-?)(\d+))')
                delete_tool = re.compile('^T(\d+)')
                change_tool = re.compile('\w')
                orig_tool = re.compile('T21')
                per_symbol = re.compile('%')

                with open(file_path, 'r') as f:
                    dile_data = f.readlines()
                    write_file_bak = open(self.file_bak_path, 'w+')
                    flag = 'neck'

                    clip_drill = 'no'
                    for ck in dile_data:
                        # --当检查到资料内存在T10则视为分割资料
                        if ck == 'T10':
                            clip_drill = 'yes'

                    if clip_drill == 'yes':
                        for line in dile_data:
                            if flag == 'neck':
                                if g82_g83.search(line):
                                    flag = 'first'
                            elif flag == 'first':
                                if delete_tool.search(line):
                                    flag = 'delete'
                            elif flag == 'delete':
                                if not change_tool.search(line):
                                    flag = 'change'
                            elif flag == 'change':
                                if orig_tool.search(line):
                                    flag = 'orig'

                            if flag == 'neck':
                                if per_symbol.search(line):
                                    write_file_bak.write(line)
                                    write_file_bak.write('T01\n')
                                else:
                                    write_file_bak.write(line)
                            elif flag == 'first':
                                # [G82|G83](X(-?)(\d+)Y(-?)(\d+))
                                match_obj = g82_g83.match(line)
                                if match_obj:
                                    write_file_bak.write(match_obj.group(2) + "\n")
                            elif flag == 'change':
                                match_obj = g82_g83.match(line)
                                if match_obj:
                                    write_file_bak.write(match_obj.group(2) + "\n")
                                elif change_tool.search(line) is None:
                                    write_file_bak.write("T500\n")
                                else:
                                    if not re.search('^T50[1-9]', line):
                                        write_file_bak.write(line)
                            elif flag == 'orig':
                                write_file_bak.write(line)
                    else:
                        for line in dile_data:
                            if per_symbol.search(line):
                                write_file_bak.write(line)
                                write_file_bak.write('T01\n')
                            elif g82_g83.search(line):
                                match_obj = g82_g83.match(line)
                                if match_obj:
                                    write_file_bak.write(match_obj.group(2) + "\n")
                                else:
                                    write_file_bak.write(line)
                            else:
                                if not re.search('^T50[1-9]', line):
                                    write_file_bak.write(line)
                    write_file_bak.close()
        else:
            if sys.platform == "win32":
                filearray = file_path.split('\\')
            else:
                filearray = file_path.split('/')
            if len(filearray) > 0:
                self.file_bak = 'filebak_' + filearray[len(filearray) - 1]
            else:
                self.file_bak = 'filebak_' + filearray[len(filearray)]

            self.file_bak_path = '/tmp/' + self.file_bak
            if platform.system() == "Windows":
                self.file_bak_path = 'D:\\tmp\\' + self.file_bak

            if not os.path.exists(file_path):
                file_path = file_path.decode("utf8")

            if os.path.exists(file_path):
                g82_g83 = re.compile('(G82|G83)(X(-?)(\d+)Y(-?)(\d+))')
                delete_tool = re.compile('^T(\d+)')
                change_tool = re.compile('\w')
                orig_tool = re.compile('T21')
                per_symbol = re.compile('%')

                with open(file_path, 'r') as f:
                    dile_data = f.readlines()
                    write_file_bak = open(self.file_bak_path, 'w+')
                    flag = 'neck'

                    clip_drill = 'no'
                    for ck in dile_data:
                        # --当检查到资料内存在T10则视为分割资料
                        if ck == 'T10':
                            clip_drill = 'yes'

                    if clip_drill == 'yes':
                        for line in dile_data:
                            if flag == 'neck':
                                if g82_g83.search(line):
                                    flag = 'first'
                            elif flag == 'first':
                                if delete_tool.search(line):
                                    flag = 'delete'
                            elif flag == 'delete':
                                if not change_tool.search(line):
                                    flag = 'change'
                            elif flag == 'change':
                                if orig_tool.search(line):
                                    flag = 'orig'

                            if flag == 'neck':
                                if per_symbol.search(line):
                                    write_file_bak.write(line)
                                    write_file_bak.write('T01\n')
                                else:
                                    write_file_bak.write(line)
                            elif flag == 'first':
                                # [G82|G83](X(-?)(\d+)Y(-?)(\d+))
                                match_obj = g82_g83.match(line)
                                if match_obj:
                                    write_file_bak.write(match_obj.group(2) + "\n")
                            elif flag == 'change':
                                match_obj = g82_g83.match(line)
                                if match_obj:
                                    write_file_bak.write(match_obj.group(2) + "\n")
                                elif change_tool.search(line) is None:
                                    write_file_bak.write("T500\n")
                                else:
                                    write_file_bak.write(line)
                            elif flag == 'orig':
                                write_file_bak.write(line)
                    else:
                        for line in dile_data:
                            if per_symbol.search(line):
                                write_file_bak.write(line)
                                write_file_bak.write('T01\n')
                            elif g82_g83.search(line):
                                match_obj = g82_g83.match(line)
                                if match_obj:
                                    write_file_bak.write(match_obj.group(2) + "\n")
                                else:
                                    write_file_bak.write(line)
                            else:
                                write_file_bak.write(line)
                    write_file_bak.close()

    def input_file(self):
        self.step.initStep()
        # --导入文件
        self.step.COM('input_manual_reset')
        self.step.COM('input_manual_set,path=%s,job=%s,step=panel,format=Excellon2,data_type=ascii,\
                     units=mm,coordinates=absolute,zeroes=trailing,nf1=3,nf2=3,decimal=no,separator=nl,tool_units=mm,layer=%s,wheel=,\
                     wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3' % (
        self.file_bak_path, self.jobname, self.file_bak))
        self.step.COM('input_manual,script_path=')
        self.step.clearAll()
        lines = file(self.file_bak_path).readlines()
        if "Mirror_ver:7" in "".join(lines):
            self.step.affect(self.file_bak)
            if sys.platform == "win32":
                self.step.COM("sel_transform,mode=anchor,oper=y_mirror,duplicate=no,"
                             "x_anchor=0,y_anchor=0,angle=0,x_scale=1,y_scale=1,"
                             "x_offset=0,y_offset=0")
            else:
                self.step.COM("sel_transform,oper=rotate\;mirror,x_anchor=0,y_anchor=0,angle=180,\
                direction=ccw,x_scale=1,y_scale=1,x_offset=0,y_offset=0,\
                mode=anchor,duplicate=no")

        os.unlink(self.file_bak_path)
        if self.checkBox_auto_compare.isChecked():
            status, souce_layer, layer_map = self.auto_compare()
            if status:
                self.err_info.append(u'比对%s和%s   发现异常:%s处\n详细请检查:%s!\n%s' %( self.file_bak, souce_layer, status, layer_map, '-'*50))
                # QMessageBox.critical(self, '警告', '重读资料比对:\n%s和%s\n发现异常:%s处\n详细请检查:%s!' % (
                # self.file_bak, souce_layer, status, layer_map), QMessageBox.Ok)

    def auto_compare(self):
        if self.radioButton_machinery.isChecked():
            layer_name = [os.path.basename(self.file_bak_path).split(".")[1]]
            if layer_name[0]:
                if self.step.isLayer(layer_name[0]) and self.step.isLayer(self.file_bak):
                    layer_bak = 'new_bak_' + layer_name[0]
                    map_layer = layer_name[0] + '_reread_compare'
                    self.step.COM("units,type=inch")
                    self.step.COM('flatten_layer,source_layer=%s,target_layer=%s' % (layer_name[0], layer_bak))
                    self.step.COM(
                        'compare_layers,layer1=%s,job2=%s,step2=%s,layer2=%s,layer2_ext=,tol=0.3,area=global,consider_sr=yes,ignore_attr=,map_layer=%s,map_layer_res=200' % (
                        layer_bak, self.jobname, self.stepname, self.file_bak, map_layer))
                    self.step.removeLayer(layer_bak)
                    info = self.step.DO_INFO(
                        '-t layer -e %s/%s/%s -m script -d SYMS_HIST' % (self.jobname, self.stepname, map_layer))
                    sym_list = info['gSYMS_HISTsymbol']
                    sym_size = info['gSYMS_HISTpad']
                    for n in range(len(sym_list)):
                        if sym_list[n] == 'r0':
                            return sym_size[n], layer_name[0], map_layer
                else:
                    if not self.step.isLayer(layer_name[0]):
                        log = u"{0}层不存在，请检查".format(layer_name[0])
                    else:
                        log = u"%s钻带回读异常，请手动回读比对" % layer_name[0]
                    self.err_info.append(log + '\n' + '-'*50)
                    # QMessageBox.critical(self, '警告', log, QMessageBox.Ok)

        else:
            compare_layer = re.compile('s\d+-\d+')
            layer_name = compare_layer.findall(self.file_bak_path)
            if layer_name[0]:
                if self.step.isLayer(layer_name[0]) and self.step.isLayer(self.file_bak):
                    layer_bak = 'new_bak_' + layer_name[0]
                    map_layer = layer_name[0] + '_reread_compare'
                    self.step.COM('flatten_layer,source_layer=%s,target_layer=%s' % (layer_name[0], layer_bak))
                    self.step.COM(
                        'compare_layers,layer1=%s,job2=%s,step2=%s,layer2=%s,layer2_ext=,tol=1,area=global,consider_sr=yes,ignore_attr=,map_layer=%s,map_layer_res=200' % (
                        layer_bak, self.jobname, self.stepname, self.file_bak, map_layer))
                    self.step.removeLayer(layer_bak)

                    info = self.step.DO_INFO(
                        '-t layer -e %s/%s/%s -m script -d SYMS_HIST' % (self.jobname, self.stepname, map_layer))
                    sym_list = info['gSYMS_HISTsymbol']
                    sym_size = info['gSYMS_HISTpad']
                    for n in range(len(sym_list)):
                        if sym_list[n] == 'r0':
                            return sym_size[n], layer_name[0], map_layer
        return None, None, None


class QComboBox(QComboBox):
    def __init__(self):
        super(QComboBox, self).__init__()

    def wheelEvent(self, event):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    drillReadBackComparison = DrillReadBackComparison()
    drillReadBackComparison.show()
    sys.exit(app.exec_())
