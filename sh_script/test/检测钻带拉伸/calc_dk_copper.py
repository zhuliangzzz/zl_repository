#!/usr/bin/env python
# -*-coding: Utf-8 -*-
# @File : calc_dk_copper
# @author: tiger
# @Time：2024/3/28 
# @version: v1.0
# @note: 

import os, sys,re
import platform
reload(sys)
sys.setdefaultencoding('utf8')
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
from PyQt4.QtGui import QMainWindow,QTableWidgetItem,QComboBox,QListWidget,QCheckBox,QListWidgetItem,QLineEdit
from PyQt4 import QtGui,QtCore
from create_ui_model import showMessageInfo,app
from ui_dk import Ui_MainWindow
from genesisPackages import top, mai_drill_layers, tongkongDrillLayer, laser_drill_layers, \
    ksz_layers,get_profile_limits,auto_add_features_in_panel_edge_new,\
    get_sr_area_for_step_include,matrixInfo, addFeatures,get_sr_area_flatten
import gClasses
from get_erp_job_info import get_inplan_mrp_info
import re
# from set_ui_model import ComboCheckBox
import json

def _toQstring(s):
    to_utf8 = unicode(s, 'utf8', 'ignore')
    return to_utf8

dic_symbol_info = {}
symbol_info_path = "/incam/server/site_data/library/symbol_info.json"
if not os.path.exists(symbol_info_path):
    symbol_info_path = os.path.join(os.path.dirname(sys.argv[0]), "symbol_info.json")

if os.path.exists(symbol_info_path):
    with open(symbol_info_path) as file_obj:
        dic_symbol_info = json.load(file_obj)



def sort_dklayers(des_layers):
    numbers = [int(dk.split('-')[0].replace('l', '')) for dk in des_layers]
    zip_dk = zip(numbers, des_layers)
    all_layer = sorted(zip_dk, key=lambda x: x[0])
    sort_layer = [i[1] for i in all_layer]
    return sort_layer

addfeature = addFeatures()
jobName = top.currentJob()
job = gClasses.Job(jobName)
stepName = 'panel'
if not stepName in job.getSteps():
    showMessageInfo(u"资料中没有panel，请检查")
    sys.exit(0)
step = gClasses.Step(job, stepName)
ly_num = int(jobName[4:6])

# 获取资料中的gk和dk层
allLayers = step.getLayers()
dklayers = []
for layer in allLayers:
    if re.search('^l\d\d?-gk$|^l\d\d?-dk$', layer):
        dklayers.append(layer)
if not dklayers:
    showMessageInfo(u"资料中未发现dk或gk层，请检查命名是否正确，规范命名：l??-dk或者l??-gk")
    sys.exit(0)

inplanjob = jobName[0:13].upper()
mrp_info = get_inplan_mrp_info(jobName)
dict_dklayer={}
# 钻孔层总表


if not mrp_info:
    showMessageInfo(u"未查找到InPlan压合叠构信息")
    sys.exit(0)

for mrp in mrp_info:
    from_layer = str(mrp['FROMLAY']).lower().strip()
    to_layer = str(mrp['TOLAY']).lower().strip()
    key = from_layer + to_layer
    dk_list = []
    for dk in dklayers:
        if from_layer == dk.split('-')[0]:
            dk_list.append(dk)
    for dk in dklayers:
        if to_layer in dk.split('-')[0]:
            dk_list.append(dk)
    if dk_list:
        if len(dk_list) == 2:
            dict_dklayer[key] = {'layers': dk_list, 'thick': mrp['YHTHICK'], 'cutx' : mrp['PNLROUTX'], 'cuty' : mrp['PNLROUTY']}

        else:
            if not dk_list:
                str_dk = 'None'
            else:
                str_dk = ';'.join(dk_list)
            showMessageInfo(u"{0}-{1}压合叠构和镀孔层命名不匹配，镀孔层命名如下:{2}".format(from_layer,to_layer,str_dk))
            sys.exit(0)



class MyWindow(QMainWindow, Ui_MainWindow):
    """
    前端界面
    """
    def __init__(self):
        super(MyWindow, self).__init__()
        self.initUI()
        self.signalControl()

    def initUI(self):
        self.setupUi(self)
        self.resize(600, 350)
        self.setFixedSize(self.width(), self.height())
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setTable()


    def setTable(self):
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setVisible(False)
        rows = len(dict_dklayer.keys()) * 2
        self.tableWidget.setRowCount(rows)
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setColumnWidth(0, 81)
        self.tableWidget.setColumnWidth(1, 81)
        self.tableWidget.setColumnWidth(2, 81)
        self.tableWidget.setColumnWidth(3, 152)
        self.tableWidget.setColumnWidth(4, 82)
        font = QtGui.QFont()
        font.setPointSize(15)


        for i, d in enumerate(dict_dklayer.values()):
            all_drls = tongkongDrillLayer + mai_drill_layers
            insert_drls = [lay for lay in all_drls if lay != u'全选']
            # 计算镀孔层对应的钻孔层
            t_layer, b_layer = d['layers']
            t_num, b_num = int(str(t_layer).split('-')[0].replace('l', '')), int(str(b_layer).split('-')[0].replace('l', ''))
            sel_drill = []
            if t_num == 1:
                if 'drl' in tongkongDrillLayer:
                    sel_drill.append('drl')
                if 'cdc' in ksz_layers:
                    sel_drill.append('cdc')
                if 'cds' in ksz_layers:
                    sel_drill.append('cds')
            else:
                # 查看是否存在埋孔层
                mai_drill = 'b{0}-{1}'.format(t_num, b_num)
                if mai_drill in mai_drill_layers:
                    sel_drill.append(mai_drill)

            self.tableWidget.setSpan(i * 2, 0, 2, 1)
            self.tableWidget.setSpan(i * 2, 2, 2, 1)
            self.tableWidget.setSpan(i * 2, 3, 2, 1)
            # 写入层名第2列
            item = QTableWidgetItem(str(d['layers'][0]))
            item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
            item.setFont(font)
            self.tableWidget.setItem(i * 2 , 1 ,item)
            item = QTableWidgetItem(str(d['layers'][1]))
            item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
            item.setFont(font)
            self.tableWidget.setItem(i * 2 + 1, 1, item)
            # 写入板厚第3列
            item = QTableWidgetItem(str(d['thick']))
            item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
            item.setFont(font)
            self.tableWidget.setItem(i * 2,  2, item)
            # item = QTableWidgetItem(str(d['thick']))
            # item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
            # item.setFont(font)
            # self.tableWidget.setItem(i * 2 + 1, 2, item)
            # 加入checkbox第1列
            wgt = self.addCheckBox(True)
            self.tableWidget.setCellWidget(i* 2 , 0, wgt)
            # self.tableWidget.setCellWidget(i * 2 + 1, 0, wgt)
            #加入钻孔层选择第4列
            # step.PAUSE(';'.join(sel_drill))
            cbox = ComboCheckBox(insert_drls)
            styleSheet = 'QComboBox{font:15pt;background-color: rgb(187 ,255, 255);margin:3px;border: 1px solid gray;' \
                         'border-radius: 3px;padding: 1px 2px 1px 2px}'
            cbox.setStyleSheet(styleSheet)
            for ii in range(len(insert_drls)):
                if insert_drls[ii] in sel_drill:
                    cbox.qCheckBox[ii].setChecked(True)
            self.tableWidget.setCellWidget(i * 2, 3, cbox)

    def signalControl(self):
        self.pushButton.clicked.connect(self.apply)  # 确定
        self.pushButton_2.clicked.connect(exit)  # 取消

    def apply(self):
        # 获取表格状态
        seclect_list = []
        get_rows = self.tableWidget.rowCount()
        for i in range(get_rows):
            seclect_dk_dict = {}
            if i % 2 == 0:
                check_state = self.tableWidget.cellWidget(i , 0).isChecked()
                if check_state :
                    seclect_dk_dict['thick'] = str(self.tableWidget.item(i, 2).text())
                    seclect_drls = self.tableWidget.cellWidget(i, 3).Selectlist()
                    if not seclect_dk_dict['thick']:
                        showMessageInfo(u"板厚数据不正确")
                        return
                    seclect_dk_dict['layer'] = [str(self.tableWidget.item(i, 1).text()), str(self.tableWidget.item(i + 1 , 1).text())]
                    seclect_dk_dict['sel'] = seclect_drls
                if seclect_dk_dict:
                    seclect_list.append(seclect_dk_dict)
        self.run_main(seclect_list)
        showMessageInfo(u"铜面积添加完成！")
        self.pushButton.setEnabled(False)

    def flipStepName(self, step, stepname, flipList = []):
        """
        递归寻找出有镜像的step，并append到 flipList数组中
        :param step: step名
        :return: None
        """
        info = step.DO_INFO('-t step -e %s/%s -m script -d SR -p flip+step' % (job.name, stepname))
        step_flip_tuple = [(info['gSRstep'][i], info['gSRflip'][i]) for i in range(len(info['gSRstep']))]
        step_flip_tuple = list(set(step_flip_tuple))
        for (name, flip_yn) in step_flip_tuple:
            if flip_yn == 'yes':
                flipList.append(name)
            elif flip_yn == 'no':
                flipList = self.flipStepName(step, name, flipList)
        # --返回
        return flipList

    def run_main(self, list_sel):
        all_get = {}
        for dict_sel in list_sel:
            step.open()
            step.clearAll()
            step.resetFilter()
            step.COM("units,type=mm")
            t_layer, b_layer = dict_sel['layer']
            thick_board = float(dict_sel['thick']) * 1000
            # t_num, b_num = int(str(t_layer).split('-')[0].replace('l', '')), int(str(b_layer).split('-')[0].replace('l', ''))

            # if t_num == 1:
            #     if 'drl' in tongkongDrillLayer:
            #         sel_drill.append('drl')
            #     if 'cdc' in ksz_layers:
            #         sel_drill.append('cdc')
            #     if 'cds' in ksz_layers:
            #         sel_drill.append('cds')
            # else:
            #     # 查看是否存在埋孔层
            #     mai_drill = 'b{0}-{1}'.format(t_num,b_num)
            #     if mai_drill in mai_drill_layers:
            #         sel_drill.append(mai_drill)

            flip_steps = []
            flip_steps = self.flipStepName(step, "panel", flip_steps)
            sel_drill = dict_sel['sel']
            if flip_steps:
                flipstep = gClasses.Step(job, "edit")
                flipstep.open()
                flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % job.name)
                flipstep.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=signal".format(jobName,t_layer))
                flipstep.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=signal".format(jobName, b_layer))
                flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % job.name)
                flipstep.close()
            else:
                step.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=signal".format(jobName, t_layer))
                step.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=signal".format(jobName, b_layer))

            back_drl_list = []
            if sel_drill:
                for dr in sel_drill:
                    back_layer = dr + 'calcooper'
                    back_drl_list.append(back_layer)
                    step.removeLayer(back_layer)
                    step.flatten_layer(dr, back_layer)
                    if flip_steps:
                        flipstep = gClasses.Step(job, "edit")
                        flipstep.open()
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % job.name)
                        flipstep.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=drill".format(jobName, back_layer))
                        flipstep.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(jobName,back_layer))
                        flipstep.COM("matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(jobName,back_layer,t_layer,b_layer))
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % job.name)
                        flipstep.close()
                    else:
                        step.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=drill".format(jobName, back_layer))
                        step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(jobName,back_layer))
                        step.COM("matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(jobName,back_layer,t_layer,b_layer))
            str_drill_list = '\;'.join(back_drl_list)
            if not sel_drill:
                incolse_drill = 'no'
            else:
                incolse_drill = 'yes'
            # step.PAUSE(str_drill_list)
            step.COM("copper_area,layer1={0},layer2={1},drills={2},consider_rout=no,ignore_pth_no_pad=yes,drills_source=matrix,"
                     "drills_list={3},thickness={4},resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes,out_file=/tmp/copper_result,out_layer=first"
                     .format(t_layer,b_layer,incolse_drill, str_drill_list, thick_board))
            area, PerCent = self.get_copper_area()
            all_get[t_layer] = {'area' : area , 'percent': PerCent, 'side': 'top'}
            step.COM(
                "copper_area,layer1={0},layer2={1},drills={2},consider_rout=no,ignore_pth_no_pad=yes,drills_source=matrix,"
                "drills_list={3},thickness={4},resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes,out_file=/tmp/copper_result,out_layer=second"
                .format(t_layer, b_layer, incolse_drill, str_drill_list, thick_board))
            area, PerCent = self.get_copper_area()
            all_get[b_layer] = {'area': area, 'percent': PerCent, 'side': 'bot'}
            if flip_steps:
                flipstep = gClasses.Step(job, "edit")
                flipstep.open()
                flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % job.name)
                flipstep.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=solder_paste".format(jobName, t_layer))
                flipstep.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=solder_paste".format(jobName, b_layer))
                flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % job.name)
                flipstep.close()
            else:
                step.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=solder_paste".format(jobName, t_layer))
                step.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=solder_paste".format(jobName, b_layer))
            if back_drl_list:
                for dr in back_drl_list:
                    if flip_steps:
                        flipstep = gClasses.Step(job, "edit")
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % job.name)
                        flipstep.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(jobName,dr))
                        flipstep.removeLayer(dr)
                        flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % job.name)
                    else:
                        step.removeLayer(dr)
        if all_get:
            self.rewriteTable(all_get)
             # 更新数据
            for key, val in all_get.items():
                self.add_copper_to_layer(key, val)

    def add_copper_to_layer(self, layer, copper):
        have_rate = False
        step.clearAll()
        step.affect(layer)
        step.resetFilter()
        # 先删除旧的symbol
        step.filter_set(feat_types='pad', include_syms ='chris-tudian')
        step.selectAll()
        if step.featureSelected():
            step.selectDelete()
            step.resetFilter()
            step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.area_name,text=copper_rate")
            step.filter_set(feat_types='text', polarity='negative')
            step.selectAll()
            if step.featureSelected():
                step.selectDelete()
        else:
            step.resetFilter()
            step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.area_name,text=copper_rate")
            step.selectAll()
            if step.featureSelected():
                have_rate = True
        if have_rate:
            step.clearAll()
            step.resetFilter()
            for text_name in ["copper_rate", "copper_area"]:
                step.clearAll()
                step.affect(layer)
                step.filter_set(feat_types='text', polarity='negative')
                step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.area_name,text={0}".format(text_name))
                step.selectAll()
                if step.featureSelected():
                    if text_name == 'copper_rate':
                        chang_text = copper['percent']+ '%'
                    else:
                        chang_text = copper['area']
                    step.COM("sel_change_txt,text={0},x_size=2.413,y_size=3.048,"
                        "w_factor=1.25,polarity=no_change,mirror=no_change,fontname=standard".format(chang_text))
                step.clearAll()
                step.resetFilter()
        else:
            # 没有添加铜面积计算板边空位添加
            add = Add_copper_Area(copper['side'])
            add.add_tudian_area([layer, copper['percent'],copper['area']])
            # subprocess.Popen(['python', '/incam/server/site_data/scripts/sh_script/add_tu_dian_copper_area_pnl_edge/add_tu_dian_copper_area_pnl_edge.py', 'arg1', 'arg2'])

    def rewriteTable(self, dict):
        font = QtGui.QFont()
        font.setPointSize(15)
        get_rows = self.tableWidget.rowCount()
        for i in range(get_rows):
            item_layer = str(self.tableWidget.item(i, 1).text())
            if item_layer in dict.keys():
                des_dict = dict[item_layer]
                item = QTableWidgetItem(str(des_dict['area']))
                item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
                item.setFont(font)
                # 写入数据面积和百分比
                self.tableWidget.setItem(i, 4, item)
                self.tableWidget.item(i, 4).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                item = QTableWidgetItem(str(des_dict['percent']))
                item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
                item.setFont(font)
                self.tableWidget.setItem(i, 5, item)
                self.tableWidget.item(i, 5).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))


    def get_copper_area(self):
        with open('/tmp/copper_result', 'r') as f:
            lines = f.readlines()
        area, PerCent = None, None
        for line in lines:
            if re.search('Total copper', line):
                area = str(round(float(line.split(':')[1].split()[0].strip()) / 92903.04, 2))
            if re.search('Percentage', line):
                PerCent = str(round(float(line.split(':')[1].strip()), 1))
        return area, PerCent

    def addCheckBox(self, check_type):
        """
        在表格中加入checkBOX，必须先放入一个容器widget
        :param check:
        :return:
        """
        widget = QtGui.QWidget()
        checkbox = QtGui.QCheckBox()
        checkbox.setChecked(check_type)
        self.setCheckBoxStyle(checkbox)
        widget.setChecked = checkbox.setChecked
        widget.checkState = checkbox.checkState
        widget.isChecked = checkbox.isChecked
        widget.clicked = checkbox.clicked
        #checkbox.setStyleSheet(Methed().setCheckBox('checkbox'))
        h = QtGui.QHBoxLayout()
        h.addWidget(checkbox)
        h.setAlignment(QtCore.Qt.AlignHCenter)
        widget.setLayout(h)
        return widget

    def setCheckBoxStyle(self, wgt):
        STR = ("#%s{\n"
                "font-size: 20px;\n"
                "}\n"
                " \n"
                "#%s::indicator {\n"
                "padding-top: 1px;\n"
               "width: 40px;\n"
               "height: 40px;border: none;\n"               
               "}\n"
               " \n"
               "#%s::indicator:unchecked {\n"
               "    image: url(:pic/png/unchecked.png);\n"
               "}\n"
               " \n"
               "#%s::indicator:checked {\n"
               "    image: url(:pic/png/right.png);\n"              
               "}" % (wgt, wgt, wgt, wgt))
        return STR

class Add_copper_Area:
    def __init__(self, side):
        self.layer_side = side

    def add_tudian_area(self,tudian_area_info):

        info = step.DO_INFO('-t symbol -e %s/%s -m script -d EXISTS' % (jobName, "chris-tudian2"))
        if info['gEXISTS'] == "no":
            if sys.platform != "win32":
                step.COM('import_lib_item_to_job,src_category=symbols,src_profile=system,src_customer=,'
                         'dst_names=%s' % "chris-tudian2")
            else:
                step.COM('copy_entity,type=symbol,source_job=genesislib,source_name=%s,dest_job=%s,dest_name=%s,'
                         'dest_database=' % ("chris-tudian2", jobName, "chris-tudian2"))

        step.COM("units,type=mm")
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
        rect = get_sr_area_for_step_include(stepName, include_sr_step=["edit", "set", "icg", "zk"])
        sr_xmin = min([min(x1, x2) for x1, y1, x2, y2 in rect])
        sr_ymin = min([min(y1, y2) for x1, y1, x2, y2 in rect])
        sr_xmax = max([max(x1, x2) for x1, y1, x2, y2 in rect])
        sr_ymax = max([max(y1, y2) for x1, y1, x2, y2 in rect])

        get_sr_area_flatten("fill", get_sr_step=True)

        array_mrp_info = get_inplan_mrp_info(jobName, "1=1")

        if not array_mrp_info:
            showMessageInfo(u"无法获取此型号在inplan中的叠构信息，请检查型号是否正确！")
            return
        dic_inner_zu = {}
        dic_sec_zu = {}
        dic_outer_zu = {}
        out_lb_x = 0
        out_lb_y = 0
        for dic_info in array_mrp_info:
            top_layer = dic_info["FROMLAY"]
            bot_layer = dic_info["TOLAY"]
            process_num = dic_info["PROCESS_NUM"]
            mrp_name = dic_info["MRPNAME"]
            pnl_routx = round(dic_info["PNLROUTX"] * 25.4, 3)
            pnl_routy = round(dic_info["PNLROUTY"] * 25.4, 3)

            if process_num == 1:
                if not dic_inner_zu.has_key(process_num):
                    dic_inner_zu[process_num] = []
                dic_inner_zu[process_num].append([mrp_name, top_layer, bot_layer, pnl_routx, pnl_routy, 0])
            else:
                if "-" in mrp_name:
                    if not dic_sec_zu.has_key(process_num):
                        dic_sec_zu[process_num] = []
                    dic_sec_zu[process_num].append([mrp_name, top_layer, bot_layer, pnl_routx, pnl_routy, 0])
                else:
                    if not dic_outer_zu.has_key(process_num):
                        dic_outer_zu[process_num] = []
                    dic_outer_zu[process_num].append([mrp_name, top_layer, bot_layer, pnl_routx, pnl_routy, 0])

                    out_lb_x = (f_xmax - pnl_routx) * 0.5
                    out_lb_y = (f_ymax - pnl_routy) * 0.5

        symbolname = "chris-tudian2"
        worklayer = "chris-tudian_tmp"
        checklayer_list = [tudian_area_info[0]]
        add_x = sr_xmax + 1.5 + 4
        add_y = f_ymax / 2.0 + 20
        move_model_fx = "Y"
        angle = 270
        area_x = [sr_xmax + 1.5, f_xmax - out_lb_x, 1]
        area_y = [f_ymax / 2.0 + 20, sr_ymax - 20, 1]

        arraylist_symbol_info = []

        step.clearAll()
        if not step.isLayer(worklayer):
            step.createLayer(worklayer)

        # step.affect(worklayer)
        # step.addRectangle(area_x[0], area_y[0], area_x[1], area_y[1])
        # step.PAUSE(str(dic_symbol_info))
        msg = u"长边添加图电面积chris-tudian2，有接触到板边其他物件，请手动移动合适的位置，然后继续！".encode("cp936")
        result = auto_add_features_in_panel_edge_new(step, add_x, add_y, worklayer,
                                                     symbolname, checklayer_list,
                                                     msg, 0, 1, angle,
                                                     area_x=area_x, area_y=area_y,
                                                     move_length=1,
                                                     move_model_fx=move_model_fx,
                                                     to_sr_area=1, max_min_area_method="yes",
                                                     dic_all_symbol_info=dic_symbol_info,
                                                     manual_add="yes")
        # step.PAUSE(str(result))
        if result:
            add_x, add_y, angle, _ = result
            arraylist_symbol_info.append([add_x, add_y, angle])
        else:
            showMessageInfo(u"长边添加图电面积chris-tudian2，请重跑试试，若还有问题请反馈给程序工程师测试！")
            return "error"

        add_x = f_xmax / 2.0 + 20
        add_y = sr_ymax + 1.5 + 4
        move_model_fx = "X"
        angle = 0
        area_x = [f_xmax / 2.0 + 20, sr_xmax - 20, 1]
        area_y = [sr_ymax + 1.5, f_ymax - out_lb_y, 1]

        # step.clearAll()
        # step.affect(worklayer)
        # step.addRectangle(area_x[0], area_y[0], area_x[1], area_y[1])
        # step.PAUSE("ddd")

        msg = u"短边添加图电面积chris-tudian2，有接触到板边其他物件，请手动移动合适的位置，然后继续！".encode("cp936")
        result = auto_add_features_in_panel_edge_new(step, add_x, add_y, worklayer,
                                                     symbolname, checklayer_list,
                                                     msg, 1, 0, angle,
                                                     area_x=area_x, area_y=area_y,
                                                     move_length=1,
                                                     move_model_fx=move_model_fx,
                                                     to_sr_area=1, max_min_area_method="yes",
                                                     dic_all_symbol_info=dic_symbol_info,
                                                     manual_add="yes")
        if result:
            add_x, add_y, angle, _ = result
            arraylist_symbol_info.append([add_x, add_y, angle])
        else:
            showMessageInfo(u"短边添加图电面积chris-tudian2，请重跑试试，若还有问题请反馈给程序工程师测试！")
            return "error"

        step.clearAll()
        dic_zu_layername = {}
        for layer in matrixInfo["gROWname"]:
            dic_zu_layername[layer] = []
        if 'gk' in tudian_area_info[0] or 'dk' in tudian_area_info[0]:
            gklayer = str(tudian_area_info[0])
            mirror = 'no'
            if self.layer_side == 'bot':
                mirror = 'yes'
            # if '-' in gklayer:
            #     ref_sig = gklayer.split('-')[0]
            #     info = step.DO_INFO("-t layer -e %s/panel/%s -d FOIL_SIDE" % (jobName, ref_sig))['gFOIL_SIDE']
            #     if info == 'bottom':
            #         mirror = 'yes'
            # elif '_' in gklayer:
            #     ref_sig = gklayer.split('_')[0]
            #     info = step.DO_INFO("-t layer -e %s/panel/%s -d FOIL_SIDE" % (jobName, ref_sig))['gFOIL_SIDE']
            #     if info == 'bottom':
            #         mirror = 'yes'
            dic_percent = tudian_area_info[1]
            dic_area = tudian_area_info[2]

            for x, y, angle in arraylist_symbol_info:
                dic_zu_layername[gklayer].append([x,
                                                  y,
                                                  symbolname,
                                                  {"polarity": "positive",
                                                   "angle": angle,
                                                   "mirror": mirror, }])
                if angle == 0:
                    add_text_x1 = x - 7
                    add_text_x2 = x + 5
                    add_text_y1 = y - 1.5
                    add_text_y2 = y - 1.5
                    if mirror == "yes":
                        add_text_x1 = x + 7
                        add_text_x2 = x - 5
                else:
                    add_text_x1 = x + 1.5
                    add_text_x2 = x + 1.5
                    add_text_y1 = y - 7
                    add_text_y2 = y + 5
                    if mirror == "yes":
                        add_text_x1 = x - 3.048 / 2
                        add_text_x2 = x - 3.048 / 2

                dic_zu_layername[gklayer].append([add_text_x1,
                                                  add_text_y1,
                                                  dic_percent + '%',
                                                  {"mirror": mirror,
                                                   "angle": angle,
                                                   "xSize": 2.413,
                                                   "ySize": 3.048,
                                                   "width": 1.25,
                                                   "attrstring": ".area_name,text=copper_rate",
                                                   "polarity": "negative"}])

                dic_zu_layername[gklayer].append([add_text_x2,
                                                  add_text_y2,
                                                  dic_area,
                                                  {"mirror": mirror,
                                                   "angle": angle,
                                                   "xSize": 2.413,
                                                   "ySize": 3.048,
                                                   "width": 1.25,
                                                   "attrstring": ".area_name,text=copper_area",
                                                   "polarity": "negative"}])

        addfeature.start_add_info(step, matrixInfo, dic_zu_layername)

        step.removeLayer("chris-tudian_tmp")
        step.removeLayer("fill")

class ComboCheckBox(QComboBox):
    def __init__(self, items):  # items==[str,str...]
        super(ComboCheckBox, self).__init__()
        self.items = items
        self.row_num = len(self.items)
        self.qCheckBox = []
        self.qLineEdit = QLineEdit()
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(15)
        self.qLineEdit.setFont(font)
        self.qLineEdit.setReadOnly(True)
        self.qListWidget = QListWidget()
        # self.addQCheckBox(0)
        for i in range(self.row_num):
            self.addQCheckBox(i)
            self.qCheckBox[i].stateChanged.connect(self.show)
        self.setModel(self.qListWidget.model())
        self.setView(self.qListWidget)
        self.setLineEdit(self.qLineEdit)

    def addQCheckBox(self, i):
        self.qCheckBox.append(QCheckBox())
        qItem = QListWidgetItem(self.qListWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.qCheckBox[i].setFont(font)
        self.qCheckBox[i].setText(self.items[i])
        self.qListWidget.setItemWidget(qItem, self.qCheckBox[i])

    def Selectlist(self):
        Outputlist = []
        for i in range(self.row_num):
            if self.qCheckBox[i].isChecked() == True:
                Outputlist.append(_toQstring(self.qCheckBox[i].text()))
        return Outputlist

    def show(self):
        Outputlist = self.Selectlist()
        self.qLineEdit.setReadOnly(False)
        showmes = ';'.join(Outputlist)
        self.qLineEdit.setText(showmes)
        self.qLineEdit.setReadOnly(True)

if __name__ == "__main__":
    w = MyWindow()
    # 界面设置居中，改变linux时候不居中的情况
    screen = QtGui.QDesktopWidget().screenGeometry()
    size = w.geometry()
    w.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)
    w.show()
    sys.exit(app.exec_())