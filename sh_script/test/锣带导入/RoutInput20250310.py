#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:RoutInput.py
   @author:zl
   @time: 2024/12/19 9:16
   @software:PyCharm
   @desc:
"""
import os
import re
import shutil
import sys, platform

reload(sys)
sys.setdefaultencoding('utf8')
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import RoutInputUI_pyqt4 as ui
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen
from genesisPackages_zl import get_profile_limits, get_sr_area_for_step_include, get_layer_selected_limits, signalLayers

class RoutInput(QWidget, ui.Ui_Form):
    def __init__(self):
        super(RoutInput, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.jobname = os.environ.get("JOB")
        self.job = gen.Job(self.jobname)
        steps = self.job.stepsList
        self.comboBox.addItems(steps)
        stepname = os.environ.get("STEP")
        if stepname:
            idex = list(filter(lambda i: steps[i] == stepname, range(len(steps))))[0] if list(filter(lambda i: steps[i] == stepname, range(len(steps)))) else -1
            self.comboBox.setCurrentIndex(idex)
        self.label_title.setText('Job:%s' % self.jobname)
        self.setStyleSheet(
            '''#pushButton_exec,#pushButton_exit{font:11pt;background-color:#0081a6;color:white;} #pushButton_exec:hover,#pushButton_exit:hover{background:black;color:white;}''')
        self.set_path()
        self.load_list()
        self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.lineEdit_path.returnPressed.connect(self.load_list)
        self.pushButton_path.clicked.connect(self.select_path)
        self.pushButton_exec.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.checkBox_select_all.clicked.connect(self.check_all)

    def set_path(self):
        if sys.platform == "win32":
            self.get_para_path = ur"\\192.168.2.172\GCfiles\锣带备份\锣带备份".format(self.jobname[1:4].upper(),
                                                                                      self.jobname.split('-')[
                                                                                          0].upper(),
                                                                                      self.jobname.split('-')[0][
                                                                                      -2:].upper())
        else:
            self.get_para_path = u"/windows/172.file/锣带备份/锣带备份/{0}系列/{1}/".format(self.jobname[1:4].upper(),
                                                                                            self.jobname.split('-')[
                                                                                                0].upper())
            # self.get_para_path = u"/id/workfile/hdi_film/{0}".format(self.jobname.split('-')[0])
        self.lineEdit_path.setText(self.get_para_path)

    def select_path(self):
        directory = QFileDialog.getExistingDirectory(self, u"选择文件夹", self.get_para_path, QFileDialog.ShowDirsOnly)
        if directory:
            self.lineEdit_path.setText(directory)
            self.load_list()

    def check_all(self):
        if self.checkBox_select_all.isChecked():
            self.listWidget.selectAll()
        else:
            self.listWidget.clearSelection()

    def load_list(self):
        self.listWidget.clear()
        self.checkBox_select_all.setChecked(False)
        file_path = str(self.lineEdit_path.text())
        if not os.path.exists(file_path):
            QMessageBox.warning(None, u'提示', u'路径%s不存在' % str(self.lineEdit_path.text()))
            return
        files = filter(lambda x: os.path.isfile(os.path.join(file_path, x)), os.listdir(file_path))
        rout_layers = []
        for file in files:
            if file.endswith('.rout'):
                rout_layers.append(file)
        self.listWidget.addItems(rout_layers)

    def run(self):
        if not self.listWidget.selectedItems():
            QMessageBox.warning(None, u'警告', u'请选择层！')
            return
        stepname = self.comboBox.currentText()
        self.step = gen.Step(self.job, stepname)
        self.step.initStep()
        layers = [str(item.text()) for item in self.listWidget.selectedItems()]
        for layer in layers:
            filepath = os.path.join(str(self.lineEdit_path.text()), layer)
            rout_temp_filepath = os.path.join(str(self.lineEdit_path.text()), 'temp_' + layer)
            shutil.copy(filepath, rout_temp_filepath)
            new_lines = []
            not_check_index = 0
            x_mirror = "no"
            y_mirror = "no"
            for i, line in enumerate(file(rout_temp_filepath).readlines()):
                if "%" in line:
                    not_check_index = i

                if "M252" in line:
                    line = line.replace("M252", "")

                if not_check_index > 0:
                    new_lines.append(line)
                else:
                    new_lines.append(line.replace(";", ""))

                if "/user" in line.lower():
                    result = re.findall("(Mirror:.*) Mode:", line)
                    if result:
                        if "No" in result[0]:
                            x_mirror = "no"
                            y_mirror = "no"
                        if "X方向" in result[0]:
                            x_mirror = "yes"
                            y_mirror = "no"
                        if "Y方向" in result[0]:
                            x_mirror = "no"
                            y_mirror = "yes"

            with open(rout_temp_filepath, "w") as f:
                f.write("".join(new_lines))
            # 20250306 去掉命名中特殊字符
            pattern = re.compile('[^\w\.\+-]')
            layername = re.sub(pattern, '', layer).lower()
            self.step.COM('input_manual_reset')
            self.step.COM(
                'input_manual_set,path=%s,job=%s,step=%s,format=Excellon2,data_type=ascii,units=mm,coordinates=absolute,zeroes=trailing,nf1=3,nf2=3,decimal=no,separator=nl,tool_units=mm,layer=%s,wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3' % (
                    rout_temp_filepath, self.jobname, self.step.name, layername))
            self.step.COM('input_manual,script_path=')
            os.unlink(rout_temp_filepath)
            self.step.clearAll()
            self.step.affect(layername)
            self.step.resetFilter()
            self.step.selectAll()
            # comp_limits = get_layer_selected_limits(self.step, layername)
            self.step.clearSel()
            f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(self.step)
            rect = get_sr_area_for_step_include(self.step.name, include_sr_step=["edit", "set"])
            sr_xmin = min([min(x1, x2) for x1, y1, x2, y2 in rect])
            sr_ymin = min([min(y1, y2) for x1, y1, x2, y2 in rect])
            sr_xmax = max([max(x1, x2) for x1, y1, x2, y2 in rect])
            sr_ymax = max([max(y1, y2) for x1, y1, x2, y2 in rect])

            # 获取脚线区域 判断有小sr的区域
            layer_cmd = gen.Layer(self.step, signalLayers[0])
            feat_out = layer_cmd.featout_dic_Index(units="mm")["pads"]
            jx_symbol_obj = [obj for obj in feat_out if obj.symbol in ("sh-con2", "sh-con")]
            all_jx_x = [obj.x for obj in jx_symbol_obj]
            all_jx_y = [obj.y for obj in jx_symbol_obj]
            if all_jx_x and all_jx_y:
                min_jx_x = min(all_jx_x)
                max_jx_x = max(all_jx_x)
                min_jx_y = min(all_jx_y)
                max_jx_y = max(all_jx_y)

                STR = '-t step -e %s/%s -d REPEAT,units=mm' % (self.jobname, self.step.name)
                gREPEAT_info = self.step.DO_INFO(STR)
                gREPEATstep = gREPEAT_info['gREPEATstep']
                gREPEATxmax = gREPEAT_info['gREPEATxmax']
                gREPEATymax = gREPEAT_info['gREPEATymax']
                gREPEATxmin = gREPEAT_info['gREPEATxmin']
                gREPEATymin = gREPEAT_info['gREPEATymin']

                set_rect_area = []
                for i, name in enumerate(gREPEATstep):
                    if gREPEATxmin[i] > min_jx_x and gREPEATymin[i] > min_jx_y and \
                            gREPEATxmax[i] < max_jx_x and gREPEATymax[i] < max_jx_y and \
                            ("set" in name or "edit" in name or "icg" in name):
                        set_rect_area.append(
                            [gREPEATxmin[i], gREPEATymin[i], gREPEATxmax[i], gREPEATymax[i]])
                try:
                    sr_xmin = min([min(x1, x2) for x1, y1, x2, y2 in set_rect_area])
                    sr_ymin = min([min(y1, y2) for x1, y1, x2, y2 in set_rect_area])
                    sr_xmax = max([max(x1, x2) for x1, y1, x2, y2 in set_rect_area])
                    sr_ymax = max([max(y1, y2) for x1, y1, x2, y2 in set_rect_area])
                except:
                    pass

            self.step.COM("sel_transform,mode=anchor,oper=scale,duplicate=no,\
                 x_anchor=%s,y_anchor=%s,angle=0,x_scale=%s,y_scale=%s,x_offset=%s,\
                 y_offset=%s" % (0, 0, 1, 1, sr_xmin, sr_ymin))

            if x_mirror == "yes":
                self.step.COM("sel_transform,mode=anchor,oper=mirror,duplicate=no,\
                     x_anchor=%s,y_anchor=%s,angle=0,x_scale=%s,y_scale=%s,x_offset=%s,\
                     y_offset=%s" % ((f_xmin + f_xmax) * 0.5, (f_ymin + f_ymax) * 0.5, 1, 1, 0, 0))

            if y_mirror == "yes":
                self.step.COM("sel_transform,mode=anchor,oper=y_mirror,duplicate=no,\
                     x_anchor=%s,y_anchor=%s,angle=0,x_scale=%s,y_scale=%s,x_offset=%s,\
                     y_offset=%s" % ((f_xmin + f_xmax) * 0.5, (f_ymin + f_ymax) * 0.5, 1, 1, 0, 0))
            self.step.unaffectAll()
        QMessageBox.information(None, u'提示', u'导入完成！')
        sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    app.setStyleSheet('QPushButton:hover{background:black;color:white;}')
    routInput = RoutInput()
    routInput.show()
    sys.exit(app.exec_())
