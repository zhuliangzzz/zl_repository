#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20241120"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""D-COUPON AOI画报 """

import os
import sys
import math
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")

import gClasses
import pic
import json
import re
from genesisPackages import matrixInfo, job, \
     addFeatures, outsignalLayers, innersignalLayers, \
     signalLayers, laser_drill_layers, mai_drill_layers, \
     get_drill_start_end_layers, tongkongDrillLayer,\
     getSmallestHole, get_layer_selected_limits, \
     solderMaskLayers, lay_num

from get_erp_job_info import get_barcode_mianci, get_drill_information, \
     get_cu_weight, get_inplan_mrp_info, get_laser_depth_width_rate

from create_ui_model import app, showMessageInfo, \
     QtGui, QtCore, Qt

addfeature = addFeatures()
dic_zu_layername = {} 
die_kong = 0
# stepname = "hct_coupon_new"    
#if stepname in job.matrix.getInfo()["gCOLstep_name"]:
    #job.removeStep(stepname)

#job.addStep(stepname)
stepname = "edit"
if "edit" not in matrixInfo["gCOLstep_name"]:
    showMessageInfo(u"edit 不存在，请检查！")
    sys.exit()
    
step = gClasses.Step(job, stepname)
step.open()
step.COM("units,type=mm")

has_drl = "yes"
if "drl" not in matrixInfo["gROWname"]:
    has_drl = "no"
    step.createLayer("drl", laytype='drill')
    for layer in ["cdc", "cds"]:
        if step.isLayer(layer):
            break
    else:
        showMessageInfo(u"检测到drl层不存在，且资料内没有cdc或cds层，请检查！")
        sys.exit()
    
matrixInfo = job.matrix.getInfo()

hct_info = os.path.join(job.dbpath, "user", job.name +"_hct_coupon_info.json")

class d_coupon_aoi(QtGui.QWidget):
    """"""

    def __init__(self, parent=None):
        """Constructor"""
        super(d_coupon_aoi, self).__init__(parent)
        
        global top_lasers, top_laser_signal_layers, top_center_laser_signal_layers, \
               bot_lasers, bot_laser_signal_layers, bot_center_laser_signal_layers, \
               top_mai_signal_layers, bot_mai_signal_layers, dic_top_laser_signal_layer, \
               dic_bot_laser_signal_layer, dic_center_laser_signal_layer, dic_top_mai_signal_layer, \
               dic_top_bot_signal_layer
        
        # 分开计算顶层 跟底层镭射
        top_lasers = []
        top_laser_signal_layers = []
        top_center_laser_signal_layers = []
        bot_lasers = []
        bot_laser_signal_layers = []
        bot_center_laser_signal_layers = []
        top_mai_signal_layers = []
        bot_mai_signal_layers = []
        dic_top_laser_signal_layer = {}
        dic_bot_laser_signal_layer = {}
        dic_center_laser_signal_layer = {}
        dic_top_mai_signal_layer = {}
        dic_top_bot_signal_layer = {}
        for i, drillLayer in enumerate(sorted(mai_drill_layers)):
            layer1, layer2 = get_drill_start_end_layers(matrixInfo, drillLayer)                
            if signalLayers.index(layer1) < signalLayers.index(layer2):
                top_mai_signal_layers.append(layer1)
                bot_mai_signal_layers.append(layer2)
                dic_top_mai_signal_layer[drillLayer] = layer1
                dic_top_bot_signal_layer[drillLayer] = layer2
            else:
                top_mai_signal_layers.append(layer2)
                bot_mai_signal_layers.append(layer1)
                dic_top_mai_signal_layer[drillLayer] = layer2
                dic_top_bot_signal_layer[drillLayer] = layer1                
                
        for i, layer in enumerate(signalLayers):
            for die_kong in range(10):                
                if i <= len(signalLayers) *0.5:
                    drill_layer = "s{0}-{1}".format(i+1, i+2+die_kong)
                    if drill_layer in laser_drill_layers:
                        top_lasers.append(drill_layer)
                        top_laser_signal_layers.append("l{0}".format(i+1))
                        top_laser_signal_layers.append("l{0}".format(i+2+die_kong))
                        dic_top_laser_signal_layer[drill_layer] = "l{0}".format(i+1)
                        dic_bot_laser_signal_layer[drill_layer] = "l{0}".format(i+2+die_kong)
                        if die_kong:
                            for num in range(die_kong):                            
                                top_center_laser_signal_layers.append("l{0}".format(i+2+num))
                            dic_center_laser_signal_layer[drill_layer] = top_center_laser_signal_layers
                else:
                    drill_layer = "s{0}-{1}".format(i+1+die_kong, i)
                    if drill_layer in laser_drill_layers:
                        bot_lasers.append(drill_layer)
                        bot_laser_signal_layers.append("l{0}".format(i)) 
                        bot_laser_signal_layers.append("l{0}".format(i+1+die_kong))
                        dic_top_laser_signal_layer[drill_layer] = "l{0}".format(i+1+die_kong) 
                        dic_bot_laser_signal_layer[drill_layer] = "l{0}".format(i)                
                        if die_kong:
                            for num in range(die_kong):
                                bot_center_laser_signal_layers.append("l{0}".format(i+1+num))
                            dic_center_laser_signal_layer[drill_layer] = bot_center_laser_signal_layers          
        
    def run_all_model(self):
        """添加所有模块"""
        global laser_drill_layers, dic_zu_layername, die_kong, mai_drill_layers
        
        res = self.get_item_value()
        if not res:
            return
        
        if not self.dic_item_value[u"模块类型"]:
            showMessageInfo(u"模块类型 要选择,请检查")
            return               
            
        #all_mai_drill_layers = [x for x in mai_drill_layers]
        if mai_drill_layers:            
            mai_drill_layers = sorted(mai_drill_layers, key=lambda x: int(x.split("-")[1]))
            # 杨经理通知 取最外层埋孔层次
            mai_drill_layers = [mai_drill_layers[-1]]        
        
            new_laser_drill_layers = []
            for i, layer in enumerate(signalLayers):
                for die_kong in range(10)[::-1]:                
                    if i <= len(signalLayers) *0.5:
                        drill_layer = "s{0}-{1}".format(i+1, i+2+die_kong)
                        if drill_layer in laser_drill_layers:
                            new_laser_drill_layers.append(drill_layer)
                            break
                    else:
                        drill_layer = "s{0}-{1}".format(i+1+die_kong, i)
                        if drill_layer in laser_drill_layers:
                            new_laser_drill_layers.append(drill_layer)
                            break
                        
            if new_laser_drill_layers:
                laser_drill_layers = new_laser_drill_layers
        
        #die_lasers_drill_layers = []
        #normal_lasers_drill_layers = []
        #inplan_job = job.name.upper().split("-")[0]
        ## 有叠孔设计的 叠孔需单独跑一个模块        
        #if "edit" in matrixInfo["gCOLstep_name"]:
            #edit_step = gClasses.Step(job, "edit")
        #else:
            #edit_step = None
            #if len(inplan_job) == 13:    
                #showMessageInfo(u"edit 不存在,请检查")
                #sys.exit()          
        
        #dic_die_zu = {}
        #for drill_layer in laser_drill_layers:
            #if edit_step is not None:
                ## 镭射层内没孔的 不计算镭射层
                #edit_step.clearAll()
                #edit_step.affect(drill_layer)
                #edit_step.resetFilter()
                #feat_out = edit_step.selectAll() or \
                    #getSmallestHole(job.name, "", drill_layer)
                ##layer_cmd = gClasses.Layer(edit_step, drill_layer)
                ##feat_out = layer_cmd.featOut()["pads"] or\
                    ##getSmallestHole(job.name, "", drill_layer)
                #if not feat_out:
                    #continue
                
            #if not drill_layer.startswith("s"):
                #continue
                
            #result = re.findall("(\d\d?)", drill_layer)
            #if result:
                #zu = abs(float(result[0]) - float(result[1]))
                #if zu > 1:
                    ## die_lasers_drill_layers.append(drill_layer)
                    #if (zu,abs(float(result[0]) - (lay_num+1)/2.0) )in dic_die_zu.keys():
                        #dic_die_zu[(zu,abs(float(result[0]) - (lay_num+1)/2.0) )].append(drill_layer)
                    #else:
                        #dic_die_zu[(zu,abs(float(result[0]) - (lay_num+1)/2.0) )]=[drill_layer]
                #else:
                    #normal_lasers_drill_layers.append(drill_layer)
                    
        #if normal_lasers_drill_layers and dic_die_zu:
            #log = u"检测到镭射贯穿一个层次跟两个层次同时存在，\
            #系统将同时跑出hct_coupon_new和hct_coupon_new_1两个模块，请注意添加到panel内！"
            #showMessageInfo(log)
            
        #if u"任意介" in self.dic_item_value[u"模块类型"] and u"埋" in self.dic_item_value[u"模块类型"] and \
           #not self.dic_editor[u"是否盲叠埋设计"].isChecked():
            #log = u"系统暂时不支持 此种{0} 且存在埋孔，且盲叠埋设计未被选中，请反馈主管评审！！".format(self.dic_item_value[u"模块类型"])
            #showMessageInfo(log)
            #return
        
        #for key in sorted(dic_die_zu.keys()):
            #die_lasers_drill_layers.append(dic_die_zu[key])            
            
        #for i, new_laser_drill_layers in enumerate([normal_lasers_drill_layers]+die_lasers_drill_layers):
            #if not new_laser_drill_layers:
                #continue
            
            #array_add_mai_dril_to_step = [""]
            #if len(all_mai_drill_layers) > 1:
                #array_add_mai_dril_to_step = all_mai_drill_layers
            
            #for mai_drill in array_add_mai_dril_to_step:
                
                #if mai_drill:
                    #mai_drill_layers = [mai_drill]
                
                #stepname = "hct_coupon_new{0}".format(mai_drill.replace("b", "_").replace("m", "_"))
                #if i and normal_lasers_drill_layers:
                    #stepname = "hct_coupon_new_{0}{1}".format(i, mai_drill.replace("b", "_").replace("m", "_"))
        
        stepname = "clip_line_coupon"
        if stepname in job.matrix.getInfo()["gCOLstep_name"]:
            job.removeStep(stepname)
        
        job.addStep(stepname)        
        self.step = gClasses.Step(job, stepname)
        self.step.open()
        self.step.COM("units,type=mm")
        
        #laser_drill_layers = new_laser_drill_layers
        #if new_laser_drill_layers in die_lasers_drill_layers:  
            #for key in sorted(dic_die_zu.keys()):
                ## print(new_laser_drill_layers, key, dic_die_zu[key])
                #if new_laser_drill_layers == dic_die_zu[key]:                        
                    #die_kong = int(key[0] - 1)
                    #break
                
            # job.PAUSE(str(die_kong))
        
        dic_zu_layername = {}
        for layer in matrixInfo["gROWname"]:
            if layer.strip():
                dic_zu_layername[layer] = []              
        
        if self.dic_item_value[u"模块类型"] in [u"通盲埋"]:                         
            dic_zu_layername, center_hole_coordinate = self.run_create_model_laser_mai_drl()
            
        if self.dic_item_value[u"模块类型"] in [u"通"]:
            dic_zu_layername, center_hole_coordinate = self.run_create_model_drl()
            
        if u"任意介" in self.dic_item_value[u"模块类型"]:            
            dic_zu_layername, center_hole_coordinate = self.run_create_model_laser_mai_drl_any()
            
        #if self.dic_item_value[u"模块类型"] in [u"通盲", u"通盲-任意介"]:            
            #self.create_drl_model()
            #if not self.dic_editor[u"盲孔是否叠孔设计"].isChecked():
                #self.add_laser_model_no_die()
            #else:
                #self.create_laser_model()  
            #if self.dic_item_value[u"模块类型"] == u"通盲":                
                #self.create_not_mai_model()
                
        #if self.dic_item_value[u"模块类型"] == u"盲-任意介":            
            #if not self.dic_editor[u"盲孔是否叠孔设计"].isChecked():
                #self.add_laser_model_no_die()
            #else:
                #self.create_laser_model()  
        
        coordinate_x = []
        coordinate_y = []
        for key, values in dic_zu_layername.iteritems():
            for info in values:
                if isinstance(info[0], (list, tuple)):
                    coordinate_x.append(info[0][0])
                    coordinate_y.append(info[0][1])
                if isinstance(info[0], (float, int)):
                    coordinate_x.append(info[0])
                    coordinate_y.append(info[1])
        
        #定义延长模块的长度
        #if self.dic_item_value[u"模块类型"] in [u"盲-任意介", u"通盲-任意介"] or self.dic_editor[u"是否盲叠埋设计"].isChecked():
            #strech_size = 5.2 + 9.5
            #move_text_size = 11.5
        #else:
            #strech_size = 5.2
            #move_text_size = 0
            
        #self.add_test_point_pad(coordinate_x, coordinate_y, strech_size)
        
        #self.add_text_barcode(coordinate_x, coordinate_y, move_text_size)
        
        addfeature.start_add_info(self.step, matrixInfo, dic_zu_layername)
        
        # self.connect_line_for_model()        
       
        self.fill_surface(coordinate_x, coordinate_y, center_hole_coordinate)
            
        showMessageInfo(u"d-coupon划报废模块运行完成！<br>{0}".format(getattr(self, "log_info", "")))
        sys.exit()
        
    def check_copper_thick(self):
        """翟鸣通知 检测内外层铜厚是否符合要求 纯内层铜厚大于2OZ/次外层、外层铜厚大于等于3mil报警不予添加 20230523 by lyh"""        
        array_cu_weight = get_cu_weight(job.name.upper(), True)
        array_mrp_info = get_inplan_mrp_info(str(job.name).upper(), condtion="1=1")
        # print array_mrp_info
        arraylist_log = []
        for dic_mrp_info in array_mrp_info:
            if dic_mrp_info["FROMLAY"] is None:
                continue
            if dic_mrp_info["TOLAY"] is None:
                continue            
            layer1 = dic_mrp_info["FROMLAY"].lower()
            layer2 = dic_mrp_info["TOLAY"].lower()
            process_num = dic_mrp_info["PROCESS_NUM"]
            if process_num == 1:
                if layer1 in signalLayers:
                    self.dic_layer_info[layer1] = [7, 7, 7, 8]
                if layer2 in signalLayers:
                    self.dic_layer_info[layer2] = [7, 7, 7, 8]
            else:
                if layer1 in signalLayers:
                    self.dic_layer_info[layer1] = [7, 7, 7, 8]
                if layer2 in signalLayers:
                    self.dic_layer_info[layer2] = [7, 7, 7, 8]                
            # print layer1, layer2, process_num
            if process_num == 1:
                for dic_cu_info in array_cu_weight:
                    # print dic_cu_info["LAYER_NAME"].lower(), "---->1"
                    if dic_cu_info["LAYER_NAME"].lower() in [layer1, layer2]:
                        weight = dic_cu_info["CU_WEIGHT"]
                        # print weight, "----->2"
                        if weight >= 1.98:
                            """检测到内层L2、L3铜厚大于2 OZ，请与主管确认线宽、孔ring设计！"""
                            arraylist_log.append(u"检测到内层{0} {1}铜厚大于等于2OZ，请与主管确认线宽、孔ring设计！".format(layer1, layer2))
                            # self.dic_layer_info[dic_cu_info["LAYER_NAME"].lower()] = [9, 9, 7, 10]  
                        elif 0.5< weight < 1.98:
                            # self.dic_layer_info[dic_cu_info["LAYER_NAME"].lower()] = [9, 9, 7, 10]
                            pass
            else:
                for dic_cu_info in array_cu_weight:
                    if dic_cu_info["LAYER_NAME"].lower() in [layer1, layer2]:
                        weight = dic_cu_info[u"厂内管控计算铜MIL".encode("utf8")]
                        # print weight, "----->2"
                        if weight >= 2.99:
                            arraylist_log.append(u"检测到次外层或外层{0} {1}铜厚大于等于3mil，请与主管确认线宽、孔ring设计！".format(layer1, layer2))
                            # self.dic_layer_info[dic_cu_info["LAYER_NAME"].lower()] = [9, 9, 7, 12]  
                        elif 1.6 < weight < 2.99:
                            # self.dic_layer_info[dic_cu_info["LAYER_NAME"].lower()] = [9, 9, 7, 12]
                            pass

        return list(set(arraylist_log))
        
    def create_ui_params(self):
        """创建界面参数"""        
        self.setWindowFlags(Qt.Qt.Window | Qt.Qt.WindowStaysOnTopHint)    
        self.setObjectName("mainWindow")
        self.titlelabel = QtGui.QLabel(u"参数确认")
        self.titlelabel.setStyleSheet("QLabel {color:red}")
        self.setGeometry(700, 300, 0, 0)
        self.resize(700, 500)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.titlelabel.setFont(font)        
    
        self.dic_editor = {}
        self.dic_label = {}
    
        arraylist1 = [{u"模块类型": "QComboBox"},
                      {u"允许修改信息": "QCheckBox"},]

        group_box_font = QtGui.QFont()
        group_box_font.setBold(True)    
        widget1 = self.set_widget(group_box_font,
                                  arraylist1,
                                   u"基本信息确认",
                                   "")
        
        self.tableWidget1 = QtGui.QTableView()        
        self.tableWidget2 = QtGui.QTableView()
        
        self.pushButton = QtGui.QPushButton()
        self.pushButton1 = QtGui.QPushButton()
        self.pushButton2 = QtGui.QPushButton()
        self.pushButton.setText(u"运行")
        self.pushButton1.setText(u"退出")
        self.pushButton2.setText(u"加载上一次数据")
        self.pushButton.setFixedWidth(100)
        self.pushButton1.setFixedWidth(100)
        self.pushButton2.setFixedWidth(100)
        btngroup_layout = QtGui.QGridLayout()
        btngroup_layout.addWidget(self.pushButton,0,0,1,1) 
        btngroup_layout.addWidget(self.pushButton1,0,1,1,1)
        # btngroup_layout.addWidget(self.pushButton2,0,2,1,1)
        btngroup_layout.setSpacing(5)
        btngroup_layout.setContentsMargins(5, 5,5, 5)
        btngroup_layout.setAlignment(QtCore.Qt.AlignTop)          
    
        main_layout =  QtGui.QGridLayout()
        main_layout.addWidget(self.titlelabel,0,0,1,10, QtCore.Qt.AlignCenter)
        main_layout.addWidget(widget1,1,0,1,10)
        main_layout.addWidget(self.tableWidget1,2,0,1,3)
        main_layout.addWidget(self.tableWidget2,2,2,1,9)
        main_layout.addLayout(btngroup_layout, 8, 0,1, 10)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(main_layout)
    
        # main_layout.setSizeConstraint(Qt.QLayout.SetFixedSize)
    
        self.pushButton.clicked.connect(self.run_all_model)
        self.pushButton1.clicked.connect(sys.exit)
        self.pushButton2.clicked.connect(self.reloading_data)
    
        self.setWindowTitle(u"d-coupon划报废模块参数确认%s" % __version__)
        self.setMainUIstyle()
        
        self.setTableWidget(self.tableWidget1, [u"钻带", u"最小孔径(um)"])
        self.setTableWidget(self.tableWidget2, [u"层名", u"通孔ring环(mil)", u"埋孔ring环(mil)", u"镭射ring环(mil)", u"最小线宽(mil)"])
        self.tableWidget1.setEnabled(False)
        self.tableWidget2.setEnabled(False)            
        self.initial_value()
        
    def initial_value(self):
        """初始化参数"""
        #self.dic_editor[u"通孔间距(mm)"].setText("1")
        #self.dic_editor[u"埋孔间距(mm)"].setText("1")
        #self.dic_editor[u"镭射孔间距(mm)"].setText("1")
        
        #dw_size, mianci,mianci_detail = self.get_erp_information(job.name.upper())
        #if dw_size == 0:
            #showMessageInfo(u"抓取erp定位孔大小失败，请手动在界面上录入定位孔大小数据")
            #dw_size = ""
        #else:            
            #self.dic_editor[u"定位孔大小(mm)"].setText(str(float(dw_size) / 1000.0))
        
        #for item in ["", u"蚀刻C面",u"蚀刻S面", u"防焊C面", u"防焊S面"]:
            #self.dic_editor[u"二维码面次"].addItem(item)
        
        #if mianci:
            #pos = self.dic_editor[u"二维码面次"].findText(
                                    #mianci_detail, QtCore.Qt.MatchContains)
            #if pos < 0:
                #showMessageInfo(u"二维码面次匹配失败，请手动在界面上选择二维码面次")
            
            #self.dic_editor[u"二维码面次"].setCurrentIndex(pos)
        #else:
            #showMessageInfo(u"抓取二维码面次失败，请手动在界面上选择二维码面次")        
        
        #res = self.setValue()
        #if res:
        self.dic_layer_info = {}
        
        res = self.check_copper_thick()
        
        self.add_data_to_table()
        
        # model_type = ""
        # if getattr(self, "tong_hole_type", None) == "has_small_pth":
        model_type = u"通"
        
        if laser_drill_layers:
            model_type += u"盲"
            
        if mai_drill_layers:
            model_type += u"埋"
            
        if not (top_lasers and bot_lasers):
            model_type = u"通"
            
        #计算HDI阶数 1阶直接用通孔
        top_laser_num = len(set([x.split("-")[0] for x in top_lasers]))
        bot_laser_num = len(set([x.split("-")[0] for x in bot_lasers]))
        hdi_jie = max([top_laser_num, bot_laser_num])
        if not mai_drill_layers:
            model_type = u"通"
        
        # 任意介
        if len(laser_drill_layers) == len(signalLayers) - 1:
            model_type += u"-任意介"
            
        for item in ["", u"通", u"通盲埋",]:
            self.dic_editor[u"模块类型"].addItem(item)
            
        pos = self.dic_editor[u"模块类型"].findText(
                                model_type, QtCore.Qt.MatchExactly)
        self.dic_editor[u"模块类型"].setCurrentIndex(pos)
        
        # self.dic_editor[u"盲孔是否叠孔设计"].setChecked(True) 
            
    def reloading_data(self):
        self.setValue()
        if not os.path.exists(hct_info):
            showMessageInfo(u"未发现上次有保存记录!")
            
    def add_data_to_table(self):
        """表格内加载数据"""
        self.dic_min_hole_size = self.get_min_hole_size()
        arraylist = []
        for key, value in self.dic_min_hole_size.iteritems():
            if isinstance(value, (list, tuple)):
                arraylist.append([key, value[0]])
                continue
            arraylist.append([key, value])
        
        self.set_model_data(self.tableWidget1, arraylist)
        
        # self.dic_layer_info = self.get_layer_pad_ring_line_width()
        arraylist = []
        for key in sorted(self.dic_layer_info.keys(), key=lambda x: int(x[1:])):
            arraylist.append([key]+ self.dic_layer_info[key])
            
        self.set_model_data(self.tableWidget2, arraylist)        
        
    def set_model_data(self, table, data_info):
        """设置表内数据"""
        model = table.model()            
        model.setRowCount(len(data_info))
        for i, array_info in enumerate(data_info):
            for j , data in enumerate(array_info):                
                index = model.index(i,j, QtCore.QModelIndex())
                model.setData(index, data)

    def setTableWidget(self, table, columnHeader):
        # table = self.tableWidget  
        # self.columnHeader = [u"钻带", u"最小孔", u"最小ring环(um)"]
        self.tableModel = QtGui.QStandardItemModel(table)
        self.tableModel.setColumnCount(len(columnHeader))
        for j in range(len(columnHeader)):
            self.tableModel.setHeaderData(
                j, Qt.Qt.Horizontal, columnHeader[j])
        table.setModel(self.tableModel)
        table.verticalHeader().setVisible(False)
        
        header = table.horizontalHeader()
        header.setDefaultAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        header.setTextElideMode(QtCore.Qt.ElideRight)
        header.setStretchLastSection(True)
        header.setClickable(True)
        header.setMouseTracking(True)
        table.setColumnWidth(0, 60)
        table.setColumnWidth(1, 110)
        table.setColumnWidth(2, 110)
        table.setColumnWidth(3, 120)

    def set_widget(self, font, arraylist, title, checkbox):
        groupbox = QtGui.QGroupBox()
        groupbox.setTitle(title)
        groupbox.setStyleSheet("QGroupBox:title{color:green}")
        groupbox.setFont(font)	
        gridlayout = self.get_layout(arraylist, checkbox)
        groupbox.setLayout(gridlayout)
        return groupbox

    def get_layout(self, arraylist, checkbox):

        gridlayout = QtGui.QGridLayout()
        for i, name in enumerate(arraylist):
            for key, value in name.iteritems():
                self.dic_label[key] = QtGui.QLabel()
                self.dic_label[key].setText(key)
                self.dic_editor[key] = getattr(QtGui, value)()
                col = 2 if i % 2 else 0
                row = -1 if col else 0
                gridlayout.addWidget(self.dic_label[key], i + 1 + row, 1 + col, 1, 1)
                gridlayout.addWidget(self.dic_editor[key], i + 1 + row, 2 + col, 1, 1)
                
                if key == u"允许修改信息":
                    self.dic_editor[key].clicked.connect(self.setTableModifyStatus)

        gridlayout.setSpacing(5)
        gridlayout.setContentsMargins(5, 5,5, 5)
        gridlayout.setAlignment(QtCore.Qt.AlignTop)

        return gridlayout
    
    def setTableModifyStatus(self):
        if self.sender().isChecked():
            self.tableWidget1.setEnabled(True)
            self.tableWidget2.setEnabled(True)
        else:
            self.tableWidget1.setEnabled(False)
            self.tableWidget2.setEnabled(False)            
        
    def setMainUIstyle(self):#设置风格
        file = QtCore.QFile(':/pic/fblue.qss')
        file.open(QtCore.QFile.ReadOnly)
        styleSheet = file.readAll()
        styleSheet = unicode(styleSheet, encoding='gb2312')
        QtGui.qApp.setStyleSheet(styleSheet)
        
    def setValue(self):
        res = 0
        if os.path.exists(hct_info):
            with open(hct_info) as file_obj:
                self.dic_hct_info = json.load(file_obj)

            for key, value in self.dic_editor.iteritems():
                if self.dic_hct_info.get(key):		    
                    if isinstance(self.dic_editor[key], QtGui.QLineEdit):
                        if isinstance(self.dic_hct_info[key], float):
                            self.dic_editor[key].setText("%s" % self.dic_hct_info[key])
                        else:
                            self.dic_editor[key].setText(self.dic_hct_info[key])
                    elif isinstance(self.dic_editor[key], QtGui.QComboBox):
                        pos = self.dic_editor[key].findText(
                            self.dic_hct_info[key], QtCore.Qt.MatchExactly)
                        self.dic_editor[key].setCurrentIndex(pos)
                        
            if self.dic_hct_info.get(u"最小孔径"):
                self.set_model_data(self.tableWidget1, self.dic_hct_info[u"最小孔径"])
            else:
                res += 1
                
            if self.dic_hct_info.get(u"层ring及线宽"):
                self.set_model_data(self.tableWidget2, self.dic_hct_info[u"层ring及线宽"])
            else:
                res += 1
        else:
            res = 1
                
        return res
        
    def get_item_value(self):
        """获取界面参数"""	
        self.dic_item_value = {}
        for key, value in self.dic_editor.iteritems():
            if isinstance(self.dic_editor[key], QtGui.QLineEdit):
                self.dic_item_value[key] = unicode(self.dic_editor[key].text(
                    ).toUtf8(), 'utf8', 'ignore').encode('cp936').decode("cp936")
            elif isinstance(self.dic_editor[key], QtGui.QComboBox):
                self.dic_item_value[key] = unicode(self.dic_editor[key].currentText(
                    ).toUtf8(), 'utf8', 'ignore').encode('cp936').decode("cp936")                
                
        arraylist = [u"通孔间距(mm)", u"埋孔间距(mm)",
                     u"镭射孔间距(mm)", u"定位孔大小(mm)",]
        
        for key in arraylist:
            if self.dic_item_value.has_key(key):
                try:
                    self.dic_item_value[key] = float(self.dic_item_value[key])
                except:
                    QtGui.QMessageBox.information(self, u'提示', u'检测到 %s 参数[ %s ]为空或非法数字,请检查~' % (
                        key, self.dic_item_value[key]), 1)
                    # self.show()
                    return 0

        #if self.dic_item_value[u"二维码面次"] == "":
            #QtGui.QMessageBox.information(self, u'提示', u'检测到 二维码面次 为空,请选择C面或S面,请检查~', 1)
            #return 0
        
        #if self.dic_item_value[u"定位孔大小(mm)"] > 10:
            #QtGui.QMessageBox.information(self, u'提示', u'定位孔超过10mm,请确认数值输入是否正确，请检查~', 1)
            #return 0            
        
        self.dic_item_value[u"最小孔径"] = []
        model = self.tableWidget1.model()
        for row in range(model.rowCount()):
            arraylist = []
            for col in range(model.columnCount()):
                value = str(model.item(row, col).text())
                if col <> 0:
                    try:
                        float(value)
                    except:
                        QtGui.QMessageBox.information(self, u'提示', u'检测到 %s 最小孔 有参数[ %s ]为空或非法数字,请检查~' % (
                            model.item(row, 0).text(), value), 1)
                        return 0
                arraylist.append(value)
                
            self.dic_item_value[u"最小孔径"].append(arraylist)         
            
        self.dic_item_value[u"层ring及线宽"] = []
        model = self.tableWidget2.model()
        for row in range(model.rowCount()):
            arraylist = []
            for col in range(model.columnCount()):
                value = str(model.item(row, col).text())
                if col <> 0:
                    try:
                        float(value)
                    except:
                        QtGui.QMessageBox.information(self, u'提示', u'检测到 %s 层ring及线宽 有参数[ %s ]为空或非法数字,请检查~' % (
                            model.item(row, 0).text(), value), 1)
                        return 0
                arraylist.append(value)
                
            self.dic_item_value[u"层ring及线宽"].append(arraylist)            

        with open(hct_info, 'w') as file_obj:
            json.dump(self.dic_item_value, file_obj)

        return 1
        
    def get_min_hole_size(self):
        """获取最小孔径"""
        dic_min_hole_size = {}
        for drillLayer in tongkongDrillLayer + mai_drill_layers + laser_drill_layers:
            dic_min_hole_size[drillLayer] = ""
            if drillLayer in tongkongDrillLayer:
                if "edit" in matrixInfo["gCOLstep_name"]:
                    # 板内最小孔剔除掉槽孔 及引孔
                    edit_step = gClasses.Step(job, "edit")
                    edit_step.open()
                    edit_step.clearAll()
                    edit_step.affect(drillLayer)
                    edit_step.copyLayer(job.name, "edit", drillLayer, drillLayer+"_tmp")
                    edit_step.copyLayer(job.name, "edit", drillLayer, drillLayer+"_tmp1")
                    edit_step.clearAll()
                    edit_step.affect(drillLayer+"_tmp1")
                    edit_step.contourize()
                    edit_step.COM("sel_delete_atr,attributes=.rout_chain")                        
                    edit_step.COM("sel_resize,size=-5")
                    
                    edit_step.clearAll()
                    edit_step.affect(drillLayer+"_tmp")
                    edit_step.resetFilter()
                    edit_step.filter_set(feat_types='line;arc')
                    edit_step.selectAll()
                    if edit_step.featureSelected():
                        edit_step.moveSel("slot_tmp")
                        edit_step.resetFilter()
                        edit_step.refSelectFilter("slot_tmp")
                        if edit_step.featureSelected():
                            edit_step.selectDelete()
                            
                        edit_step.removeLayer("slot_tmp")                  
                    
                    edit_step.resetFilter()
                    edit_step.refSelectFilter(drillLayer+"_tmp1", mode="cover")
                    if edit_step.featureSelected():
                        edit_step.selectDelete()
                    
                    hole_size = getSmallestHole(job.name, "edit", drillLayer+"_tmp") or \
                        getSmallestHole(job.name, "", drillLayer+"_tmp")
                    
                    edit_step.removeLayer(drillLayer+"_tmp")
                    edit_step.removeLayer(drillLayer+"_tmp1")
                else:
                    hole_size = getSmallestHole(job.name, "edit", drillLayer, panel=None)
            else:                        
                hole_size = getSmallestHole(job.name, "edit", drillLayer, panel=None)
                if getattr(self, "big_laser_holes", None) is not None:
                    for laser_layer in self.big_laser_holes:
                        if drillLayer[1:] in laser_layer:
                            symbolname = self.get_raoshao_laser_hole(drillLayer)
                            # step.PAUSE(str(symbolname))
                            # 绕烧不能判断孔径大小 暂定为350
                            # max_laser_hole = 350
                            # dic_raoshao[drillLayer] = "yes"
                            if symbolname:
                                hole_size = (hole_size, symbolname)
                            else:
                                log = u"检测到{0}镭射INPLAN钻孔信息有备注绕烧，但钻带内处理绕烧孔径失败，请手动修改镭射孔径！"
                                showMessageInfo(log.format(drillLayer))                                       
            
            if drillLayer in tongkongDrillLayer:
                # 有，如通孔里面没有小孔的，取0.452的孔做导通 最大不能超过0.452
                self.tong_hole_type = "has_small_pth"
                if not hole_size:
                    self.tong_hole_type = "no_small_pth"
                    
                hole_size = hole_size if hole_size else 452
                if hole_size > 452:
                    hole_size = 452
            else:
                if not hole_size:
                    if drillLayer in laser_drill_layers:
                        # 镭射层板内没孔的不计算在内
                        del dic_min_hole_size[drillLayer]
                        
                    continue
                
            dic_min_hole_size[drillLayer] = hole_size
            
        return dic_min_hole_size
    
    def get_layer_pad_ring_line_width(self):
        """获取各层的孔pad 及线宽大小"""
        dic_layer_info = {}
        for layer in signalLayers:
            dic_layer_info[layer] = [6, 6, 4, 8]
            
        return dic_layer_info
                
    def get_raoshao_laser_hole(self, drill_layer):
        """获取绕烧的镭射尺寸 原理建一个symbol 把coupon里面的changesymbol"""
        if "edit" in matrixInfo["gCOLstep_name"]:
            step = gClasses.Step(job, "edit")
            step.open()
        
            step.removeLayer(drill_layer+"_tmp1")
            step.removeLayer(drill_layer+"_tmp2")
            step.copyLayer(job.name, step.name, drill_layer, drill_layer+"_tmp1")
            step.copyLayer(job.name, step.name, drill_layer, drill_layer+"_tmp2")
            step.clearAll()
            step.affect(drill_layer+"_tmp1")
            step.contourize()
            step.COM("sel_delete_atr,attributes=.rout_chain")            
            step.COM("sel_resize,size=-5")        
            step.resetFilter()
            step.refSelectFilter(drill_layer+"_tmp2", mode="cover")
            if step.featureSelected():
                step.selectDelete()
                
            for index in range(1, 5):
                step.VOF()
                step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(drill_layer+"_tmp1", index))
                step.VON()
                step.COM("sel_reverse")
                if step.featureSelected():
                    step.selectDelete()
                
                step.resetFilter()
                step.selectAll()
                if step.featureSelected() == 1:
                    break
                
            step.resetFilter()
            step.selectAll()
            if step.featureSelected() != 1:
                step.removeLayer(drill_layer+"_tmp1")
                step.removeLayer(drill_layer+"_tmp2")            
                return None
            
            step.isLayer()
            step.clearAll()
            step.affect(drill_layer+"_tmp2")
            step.resetFilter()
            step.refSelectFilter(drill_layer+"_tmp1")
            if step.featureSelected():
                xmin, ymin, xmax, ymax = get_layer_selected_limits(step, drill_layer+"_tmp2")
                center_x = (xmin + xmax) * 0.5
                center_y = (ymin + ymax) * 0.5
                step.COM("sel_create_sym,symbol={0},x_datum={1},y_datum={2},"
                         "delete=no,fill_dx=2.54,fill_dy=2.54,attach_atr=no,"
                         "retain_atr=yes".format("raoshao_hole_size_tmp", center_x, center_y))
                step.removeLayer(drill_layer+"_tmp1")
                step.removeLayer(drill_layer+"_tmp2")            
                return "raoshao_hole_size_tmp"
        
            step.removeLayer(drill_layer+"_tmp1")
            step.removeLayer(drill_layer+"_tmp2")        
        return None
    
    def get_erp_information(self, inplan_job):
        """获取hct coupon定位孔大小 及二维码蚀刻面次"""
        drill_info = get_drill_information(inplan_job)
        size = 0
        self.big_laser_holes = []
        for info in drill_info:
            if info[1].decode("utf8") == u"一次钻孔" and \
               info[7].decode("utf8") == u"HCT coupon定位孔":
                size = info[6]
                break
            
        for info in drill_info:
            if u"镭射" in info[1].decode("utf8"):
                if info[8] and u"绕烧" in info[8].decode("utf8"):
                    self.big_laser_holes.append(info[1].decode("utf8"))
        
        mianci_info = get_barcode_mianci(inplan_job)
        mianci = None        
        if mianci_info:
            if "C" in mianci_info[0][1].upper():
                mianci = "c"
                
            if "S" in mianci_info[0][1].upper():
                mianci = "s"
                
            return size, mianci, mianci_info[0][1].decode("utf8")
                
        return size, mianci, None
    
    def run_create_model_laser_mai_drl(self):
        """开始生成通埋盲模块"""
        
        drl_add_line_symbol, drl_add_hole_pad = self.get_dic_add_symbol_line("drl")
        mai_add_line_symbol, mai_add_hole_pad = self.get_dic_add_symbol_line("mai")
        laser_add_line_symbol, laser_add_hole_pad = self.get_dic_add_symbol_line("laser")
        drl_small_hole_size = float(self.get_min_hole_size_from_dict("drl")) / 25.4
        if float(self.get_min_hole_size_from_dict("drl")) > 452:
            drl_small_hole_size = 452 / 25.4
        
        arraylist_coordinate,center_hole_coordinate = self.get_coordinate("laser")               
        
        all_x = [x for x, y, _,_ in arraylist_coordinate]
        all_y = [y for x, y, _,_ in arraylist_coordinate]
        
        #coupon_name = "clip_line_coupon"
        #if coupon_name in matrixInfo["gCOLstep_name"]:
            #job.removeStep(coupon_name)
        
        #job.addStep(coupon_name)
        
        #step = gClasses.Step(job, coupon_name)
        #step.open()
        #step.COM("units,type=mm")
        step = self.step
        
        index = 0
        new_arraylist_coordinate = []
        for x, y , layer,inner_or_outer in arraylist_coordinate:
            index += 1
            append_coor = True
            if inner_or_outer == "not_add_pad":
                continue
                
            if layer in outsignalLayers and inner_or_outer == "outer":
                #step.clearAll()
                #step.affect("drl")                
                #step.addPad(x, y, "r452")
                dic_zu_layername["drl"].append([x,
                                                y,
                                                "r452",
                                                {"attrstring": ".drill,option=via"}])
                
                for sig_layer in outsignalLayers:                    
                    dic_zu_layername[sig_layer].insert(0, [x,
                                                        y,
                                                        "r1254",
                                                         {"polarity": "negative",}])
                    dic_zu_layername[sig_layer].append([x,
                                                        y,
                                                        "r1000",
                                                         {"polarity": "positive",
                                                          "attrstring": ".string,text=test_pad",}])
                    
                for sig_layer in innersignalLayers:                    
                    dic_zu_layername[sig_layer].insert(0, [x,
                                                        y,
                                                        "r{0}".format((drl_add_hole_pad[layer]+drl_small_hole_size+8)*25.4),
                                                         {"polarity": "negative",}])
                    dic_zu_layername[sig_layer].append([x,
                                                        y,
                                                        "r{0}".format((drl_add_hole_pad[layer]+drl_small_hole_size)*25.4),
                                                         {"polarity": "positive",
                                                          "attrstring": ".string,text=test_pad",}])
                                    
                
            else:                
                all_in_mai_signal_layers = []
                for drill_layer in mai_drill_layers:
                    top_layer = dic_top_mai_signal_layer[drill_layer]
                    bot_layer = dic_top_bot_signal_layer[drill_layer]
                    
                    for sig_layer in signalLayers:
                        if int(top_layer[1:])< int(sig_layer[1:]) < int(bot_layer[1:]):
                            all_in_mai_signal_layers.append(sig_layer)
                    
                    if int(top_layer[1:])<= int(layer[1:]) <= int(bot_layer[1:]):
                        
                        if layer in [top_layer]:
                            for laser_drill_layer in laser_drill_layers:
                                laser_top_layer = dic_top_laser_signal_layer[laser_drill_layer]
                                laser_bot_layer = dic_bot_laser_signal_layer[laser_drill_layer]
                                #if (layer == laser_bot_layer and int(layer[1:]) <= lay_num * 0.5) or \
                                   #(layer == laser_top_layer and int(layer[1:]) > lay_num * 0.5):
                                if layer == laser_bot_layer:
                                    
                                    laser_small_hole_size = float(self.get_min_hole_size_from_dict(laser_drill_layer)) / 25.4
                                    dic_zu_layername[laser_drill_layer].append([x,
                                                                                y + 15 * 0.0254,
                                                                                "r{0}".format(laser_small_hole_size*25.4),
                                                                                {"attrstring": ".drill,option=via"}])
                                    
                                    for sig_layer in [laser_top_layer, laser_bot_layer]:
                                        dic_zu_layername[sig_layer].insert(0, [x,
                                                                               y + 15 * 0.0254,
                                                                               "r{0}".format((laser_add_hole_pad[layer]+laser_small_hole_size+8)*25.4),
                                                                                {"polarity": "negative",}])
                                        dic_zu_layername[sig_layer].append([x,
                                                                            y + 15 * 0.0254,
                                                                            "r{0}".format((laser_add_hole_pad[layer]+laser_small_hole_size)*25.4),
                                                                             {"polarity": "positive",}])                                    
                                    
                                    # if layer == top_layer:
                                    new_arraylist_coordinate.append([x, y + 15 * 0.0254, laser_bot_layer, inner_or_outer])
                                    #else:
                                        #new_arraylist_coordinate.append([x, y + 15 * 0.0254, laser_top_layer, inner_or_outer])
                                        
                                    break
                                
                        mai_small_hole_size = float(self.get_min_hole_size_from_dict(drill_layer)) / 25.4
                        dic_zu_layername[drill_layer].append([x,
                                                              y,
                                                              "r{0}".format(mai_small_hole_size*25.4),
                                                              {"attrstring": ".drill,option=via"}])
                        
                        for sig_layer in signalLayers:
                            if int(top_layer[1:])<= int(sig_layer[1:]) <= int(bot_layer[1:]):
                                dic_zu_layername[sig_layer].insert(0, [x,
                                                                    y,
                                                                    "r{0}".format((mai_add_hole_pad[layer]+mai_small_hole_size+8)*25.4),
                                                                     {"polarity": "negative",}])
                                dic_zu_layername[sig_layer].append([x,
                                                                    y,
                                                                    "r{0}".format((mai_add_hole_pad[layer]+mai_small_hole_size)*25.4),
                                                                     {"polarity": "positive",
                                                                      "attrstring": ".string,text=check_shave",}])
                                
                        new_arraylist_coordinate.append([x, y, layer, inner_or_outer])
                        append_coor = False
                        
                        if layer in [bot_layer] and abs(int(top_layer[1:]) - int(bot_layer[1:])) == 1 and lay_num == 4:                            
                            x = 0
                            for laser_drill_layer in laser_drill_layers:
                                laser_top_layer = dic_top_laser_signal_layer[laser_drill_layer]
                                laser_bot_layer = dic_bot_laser_signal_layer[laser_drill_layer]
                                #if (layer == laser_bot_layer and int(layer[1:]) <= lay_num * 0.5) or \
                                   #(layer == laser_top_layer and int(layer[1:]) > lay_num * 0.5):
                                if layer == laser_bot_layer:
                                    
                                    laser_small_hole_size = float(self.get_min_hole_size_from_dict(laser_drill_layer)) / 25.4
                                    dic_zu_layername[laser_drill_layer].append([x,
                                                                                y,
                                                                                "r{0}".format(laser_small_hole_size*25.4),
                                                                                {"attrstring": ".drill,option=via"}])
                                    
                                    for sig_layer in [laser_top_layer, laser_bot_layer]:
                                        dic_zu_layername[sig_layer].insert(0, [x,
                                                                               y,
                                                                               "r{0}".format((laser_add_hole_pad[layer]+laser_small_hole_size+8)*25.4),
                                                                                {"polarity": "negative",}])
                                        dic_zu_layername[sig_layer].append([x,
                                                                            y,
                                                                            "r{0}".format((laser_add_hole_pad[layer]+laser_small_hole_size)*25.4),
                                                                             {"polarity": "positive",}])                                    
                                    
                                    # if layer == top_layer:
                                    new_arraylist_coordinate.append([x, y, laser_bot_layer, inner_or_outer])
                                    if laser_top_layer in outsignalLayers:
                                        new_arraylist_coordinate.append([x, y, laser_top_layer, inner_or_outer])
                                        
                                        x1, y1, layer1, inner_or_outer1 = arraylist_coordinate[-2]
                                        arraylist_coordinate[-2] = [1.67, y1, layer1, "not_add_pad"]
                                    break
                        break
                else:
                    for drill_layer in laser_drill_layers:
                        try:                            
                            top_layer = dic_top_laser_signal_layer[drill_layer]
                            bot_layer = dic_bot_laser_signal_layer[drill_layer]
                            center_layers = dic_center_laser_signal_layer.get(drill_layer, [])
                        except:
                            top_layer, bot_layer = get_drill_start_end_layers(matrixInfo, drill_layer)
                            center_layers = []
                        
                        # 再埋孔内的镭射不加
                        if bot_layer in all_in_mai_signal_layers or top_layer in all_in_mai_signal_layers:
                            continue
                        
                        # if layer in [top_layer, bot_layer]:
                        if (layer == bot_layer and int(layer[1:]) < lay_num * 0.5) or \
                           (layer == top_layer and int(layer[1:]) > lay_num * 0.5):
                            
                            laser_small_hole_size = float(self.get_min_hole_size_from_dict(drill_layer)) / 25.4
                            dic_zu_layername[drill_layer].append([x,
                                                                  y,
                                                                  "r{0}".format(laser_small_hole_size*25.4),
                                                                  {"attrstring": ".drill,option=via"}])
                            
                            if center_layers:
                                for sig_layer in center_layers:
                                    dic_zu_layername[sig_layer].insert(0, [x,
                                                                           y,
                                                                           "r{0}".format((laser_add_hole_pad[layer]+laser_small_hole_size+8)*25.4),
                                                                            {"polarity": "negative",}])                                
                            
                            for sig_layer in [top_layer, bot_layer]:
                                dic_zu_layername[sig_layer].insert(0, [x,
                                                                    y,
                                                                    "r{0}".format((laser_add_hole_pad[layer]+laser_small_hole_size+8)*25.4),
                                                                     {"polarity": "negative",}])
                                dic_zu_layername[sig_layer].append([x,
                                                                    y,
                                                                    "r{0}".format((laser_add_hole_pad[layer]+laser_small_hole_size)*25.4),
                                                                     {"polarity": "positive",}])                             
                            break
            
            if append_coor:                
                new_arraylist_coordinate.append([x, y, layer, inner_or_outer])
            
        #最后一次 再追加一个孔
        x, y, _, _ = new_arraylist_coordinate[-2]
        # if x == 0:
        if "not_add_pad" in arraylist_coordinate[-2]:
            new_arraylist_coordinate.insert(len(new_arraylist_coordinate) - 1, [1.67, y, "l{0}".format(lay_num), "outer"])
        else:            
            new_arraylist_coordinate.insert(len(new_arraylist_coordinate) - 1, [0, y, "l{0}".format(lay_num), "outer"])
            
        # job.PAUSE(str(new_arraylist_coordinate))
        
        rect = [min(all_x) - 0.6, min(all_y) - 0.6, max(all_x) + 0.6, max(all_y) + 0.6]        
        step.COM(
                "profile_rect,x1={0},y1={1},x2={2},y2={3}".format(*rect))
        step.clearAll()
        for layer in signalLayers:            
            step.affect(layer)
            
        step.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,\
            min_brush=0.5,use_arcs=yes,symbol=,dx=1,dy=1,break_partial=yes,\
            cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no")
    
        step.COM("sr_fill,polarity=%s,step_margin_x=0.2,step_margin_y=0.2,\
            step_max_dist_x=%s,step_max_dist_y=%s,sr_margin_x=0,\
            sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,\
            consider_feat=no,feat_margin=0,consider_drill=no,drill_margin=0,\
            consider_rout=no,dest=affected_layers,layer=,\
            attributes=no" % ("positive", 2540, 2540))

        point_index = 0
        # step.PAUSE(str(new_arraylist_coordinate))
        for x, y , layer,_ in new_arraylist_coordinate:
            if point_index+1 > len(new_arraylist_coordinate) - 1:
                break            
            next_x, next_y, _,_ = new_arraylist_coordinate[point_index+1]            
            dic_zu_layername[layer].insert(0, [(x, y),
                                               (next_x, next_y),
                                               "r{0}".format((drl_add_line_symbol[layer]+8)*25.4),
                                               {"addline": True,"polarity": "negative",}])               
            point_index += 1
                        
        point_index = 0
        for x, y , layer,_ in new_arraylist_coordinate:
            if point_index+1 > len(new_arraylist_coordinate) - 1:
                break
            next_x, next_y, _,_ = new_arraylist_coordinate[point_index+1]       
            dic_zu_layername[layer].append([(x, y),
                                            (next_x, next_y),
                                            "r{0}".format(drl_add_line_symbol[layer]*25.4),
                                            {"addline": True,"polarity": "positive",}])             
            point_index += 1              
        
        return dic_zu_layername, center_hole_coordinate

    def run_create_model_laser_mai_drl_any(self):
        """开始生成通埋盲模块"""
        
        drl_add_line_symbol, drl_add_hole_pad = self.get_dic_add_symbol_line("drl")
        mai_add_line_symbol, mai_add_hole_pad = self.get_dic_add_symbol_line("mai")
        laser_add_line_symbol, laser_add_hole_pad = self.get_dic_add_symbol_line("laser")
        drl_small_hole_size = float(self.get_min_hole_size_from_dict("drl")) / 25.4
        if float(self.get_min_hole_size_from_dict("drl")) > 452:
            drl_small_hole_size = 452 / 25.4
        
        arraylist_coordinate,center_hole_coordinate = self.get_coordinate("laser_any")               
        
        all_x = [x for x, y, _,_ in arraylist_coordinate]
        all_y = [y for x, y, _,_ in arraylist_coordinate]
        
        #coupon_name = "clip_line_coupon"
        #if coupon_name in matrixInfo["gCOLstep_name"]:
            #job.removeStep(coupon_name)
        
        #job.addStep(coupon_name)
        
        #step = gClasses.Step(job, coupon_name)
        #step.open()
        #step.COM("units,type=mm")
        step = self.step
        
        index = 0
        new_arraylist_coordinate = []
        for x, y , layer,inner_or_outer in arraylist_coordinate:
            index += 1
            if layer in outsignalLayers and inner_or_outer == "outer":
                #step.clearAll()
                #step.affect("drl")                
                #step.addPad(x, y, "r452")
                dic_zu_layername["drl"].append([x,
                                                y,
                                                "r452",
                                                {"attrstring": ".drill,option=via"}])
                
                for sig_layer in outsignalLayers:                    
                    dic_zu_layername[sig_layer].insert(0, [x,
                                                        y,
                                                        "r1254",
                                                         {"polarity": "negative",}])
                    dic_zu_layername[sig_layer].append([x,
                                                        y,
                                                        "r1000",
                                                         {"polarity": "positive",
                                                          "attrstring": ".string,text=test_pad",}])                
            else:
                
                for drill_layer in laser_drill_layers + mai_drill_layers:
                    try:                            
                        top_layer = dic_top_laser_signal_layer[drill_layer]
                        bot_layer = dic_bot_laser_signal_layer[drill_layer]
                    except:
                        top_layer, bot_layer = get_drill_start_end_layers(matrixInfo, drill_layer)
                    
                    # if layer in [top_layer, bot_layer]:
                    if (layer == bot_layer and int(layer[1:]) <= lay_num * 0.5) or \
                       (layer == top_layer and int(layer[1:]) > lay_num * 0.5):
                        
                        laser_small_hole_size = float(self.get_min_hole_size_from_dict(drill_layer)) / 25.4
                        
                        if drill_layer in mai_drill_layers:                            
                            signal_symbol_neg = "r{0}".format((mai_add_hole_pad[layer]+laser_small_hole_size+8)*25.4)
                            signal_symbol_pos = "r{0}".format((mai_add_hole_pad[layer]+laser_small_hole_size)*25.4)
                        else:
                            signal_symbol_neg = "r{0}".format((laser_add_hole_pad[layer]+laser_small_hole_size+8)*25.4)
                            signal_symbol_pos = "r{0}".format((laser_add_hole_pad[layer]+laser_small_hole_size)*25.4)
                        
                        dic_zu_layername[drill_layer].append([x,
                                                              y,
                                                              "r{0}".format(laser_small_hole_size*25.4),
                                                              {"attrstring": ".drill,option=via"}])
                        
                        for sig_layer in [top_layer, bot_layer]:
                            dic_zu_layername[sig_layer].insert(0, [x,
                                                                y,
                                                                signal_symbol_neg,
                                                                 {"polarity": "negative",}])
                            dic_zu_layername[sig_layer].append([x,
                                                                y,
                                                                signal_symbol_pos,
                                                                {"polarity": "positive",}])                             
                        break
                           
            
            new_arraylist_coordinate.append([x, y, layer, inner_or_outer])
            
        #最后一次 再追加一个孔
        #x, y, _, _ = new_arraylist_coordinate[-2]
        ## if x == 0:
        #if "not_add_pad" in arraylist_coordinate[-2]:
            #new_arraylist_coordinate.insert(len(new_arraylist_coordinate) - 1, [1.67, y, "l{0}".format(lay_num), "outer"])
        #else:            
            #new_arraylist_coordinate.insert(len(new_arraylist_coordinate) - 1, [0, y, "l{0}".format(lay_num), "outer"])
            
        #job.PAUSE(str(new_arraylist_coordinate))
        
        rect = [min(all_x) - 0.6, min(all_y) - 0.6, max(all_x) + 0.6, max(all_y) + 0.6]        
        step.COM(
                "profile_rect,x1={0},y1={1},x2={2},y2={3}".format(*rect))
        step.clearAll()
        for layer in signalLayers:            
            step.affect(layer)
            
        step.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,\
            min_brush=0.5,use_arcs=yes,symbol=,dx=1,dy=1,break_partial=yes,\
            cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no")
    
        step.COM("sr_fill,polarity=%s,step_margin_x=0.2,step_margin_y=0.2,\
            step_max_dist_x=%s,step_max_dist_y=%s,sr_margin_x=0,\
            sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,\
            consider_feat=no,feat_margin=0,consider_drill=no,drill_margin=0,\
            consider_rout=no,dest=affected_layers,layer=,\
            attributes=no" % ("positive", 2540, 2540))         
 
        point_index = 0
        step.PAUSE(str(new_arraylist_coordinate))
        for x, y , layer,_ in new_arraylist_coordinate:
            step.clearAll()
            step.affect(layer)
            if point_index+1 > len(new_arraylist_coordinate) - 1:
                break            
            next_x, next_y, _,_ = new_arraylist_coordinate[point_index+1]            
            dic_zu_layername[layer].insert(0, [(x, y),
                                               (next_x, next_y),
                                               "r{0}".format((drl_add_line_symbol[layer]+8)*25.4),
                                               {"addline": True,"polarity": "negative",}])               
            point_index += 1
                        
        point_index = 0
        for x, y , layer,_ in new_arraylist_coordinate:
            if point_index+1 > len(new_arraylist_coordinate) - 1:
                break
            next_x, next_y, _,_ = new_arraylist_coordinate[point_index+1]       
            dic_zu_layername[layer].append([(x, y),
                                            (next_x, next_y),
                                            "r{0}".format(drl_add_line_symbol[layer]*25.4),
                                            {"addline": True,"polarity": "positive",}])             
            point_index += 1              
        
        return dic_zu_layername, center_hole_coordinate
    
    def run_create_model_drl(self):
        """开始生成通孔模块"""        
        drl_add_line_symbol, drl_add_hole_pad = self.get_dic_add_symbol_line("drl")
        small_hole_size = float(self.get_min_hole_size_from_dict("drl")) / 25.4
        if float(self.get_min_hole_size_from_dict("drl")) > 452:
            small_hole_size = 452 / 25.4
        
        arraylist_coordinate,center_hole_coordinate = self.get_coordinate("drl")
        
        all_x = [x for x, y, _,_ in arraylist_coordinate]
        all_y = [y for x, y, _,_ in arraylist_coordinate]
        
        #coupon_name = "clip_line_coupon"
        #if coupon_name in matrixInfo["gCOLstep_name"]:
            #job.removeStep(coupon_name)
        
        #job.addStep(coupon_name)
        
        #step = gClasses.Step(job, coupon_name)
        #step.open()
        step = self.step

        for x, y , layer,inner_or_out in arraylist_coordinate:
            if layer in outsignalLayers and inner_or_out == "outer":
                dic_zu_layername["drl"].append([x,
                                                y,
                                                "r452",
                                                {"attrstring": ".drill,option=via"}])                
            else:
                dic_zu_layername["drl"].append([x,
                                                y,
                                                "r{0}".format(small_hole_size*25.4),
                                                {"attrstring": ".drill,option=via"}])                 
        
        rect = [min(all_x) - 0.6, min(all_y) - 0.6, max(all_x) + 0.6, max(all_y) + 0.6]        
        step.COM(
                "profile_rect,x1={0},y1={1},x2={2},y2={3}".format(*rect))
        step.clearAll()
        for layer in signalLayers:            
            step.affect(layer)
            
        step.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,\
            min_brush=0.5,use_arcs=yes,symbol=,dx=1,dy=1,break_partial=yes,\
            cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no")
    
        step.COM("sr_fill,polarity=%s,step_margin_x=0.2,step_margin_y=0.2,\
            step_max_dist_x=%s,step_max_dist_y=%s,sr_margin_x=0,\
            sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,\
            consider_feat=no,feat_margin=0,consider_drill=no,drill_margin=0,\
            consider_rout=no,dest=affected_layers,layer=,\
            attributes=no" % ("positive", 2540, 2540))         
        
        for layer in signalLayers:           
            for x, y , sig_layer,inner_or_out in arraylist_coordinate:
                if sig_layer in outsignalLayers and inner_or_out == "outer":
                    dic_zu_layername[layer].append([x,
                                                    y,
                                                    "r1254",
                                                     {"polarity": "negative",}])                     
                else:
                    dic_zu_layername[layer].append([x,
                                                    "r{0}".format((drl_add_hole_pad[layer]+small_hole_size+8)*25.4),
                                                    {"polarity": "negative",}])

                    for layer in signalLayers:
                        for x, y , sig_layer,inner_or_out in arraylist_coordinate:
                            if sig_layer in outsignalLayers and inner_or_out == "outer":
                                dic_zu_layername[layer].append([x,
                                                                y,
                                                                "r1000",
                                                                {"attrstring": ".string,text=test_pad",}])
                    y,

                else:                
                    dic_zu_layername[layer].append([x,
                                                    y,
                                                    "r{0}".format((drl_add_hole_pad[sig_layer]+small_hole_size)*25.4), 
                                                    {"attrstring": ".string,text=check_shave"}])                     
        
        #最后一次 再追加一个孔
        x, y, _, _ = arraylist_coordinate[-2]
        if x == 0:            
            arraylist_coordinate.insert(len(arraylist_coordinate) - 1, [1.67, y, "l{0}".format(lay_num), "outer"])
            
        point_index = 0
        for x, y , layer,_ in arraylist_coordinate:
            if point_index+1 > len(arraylist_coordinate) - 1:
                break
            next_x, next_y, _,_ = arraylist_coordinate[point_index+1]
            dic_zu_layername[layer].insert(0, [(x, y),
                                            (next_x, next_y),
                                            "r{0}".format((drl_add_line_symbol[layer]+8)*25.4),
                                            {"addline": True,"polarity": "negative",}])                     
            point_index += 1
            
        point_index = 0
        for x, y , layer,_ in arraylist_coordinate:
            if point_index+1 > len(arraylist_coordinate) - 1:
                break
            next_x, next_y, _,_ = arraylist_coordinate[point_index+1]
            dic_zu_layername[layer].append([(x, y),
                                            (next_x, next_y),
                                            "r{0}".format(drl_add_line_symbol[layer]*25.4),
                                            {"addline": True,"polarity": "positive",}])             
            point_index += 1

        return dic_zu_layername, center_hole_coordinate
            
    def get_coordinate(self, model):
        arraylist_coordinate = [[2.06, 0, "l1", "outer"]]
        flag = [1, -1, 0.5]
        center_hole_coordinate = []
        if model == "laser":
            number = lay_num - 2
        else:
            number = lay_num - 1
            
        for i in range(number):
            if i == 0:                
                x = arraylist_coordinate[-1][0] + 1.67 * flag[0]
                y = arraylist_coordinate[-1][1] + 2.0 * flag[1] * flag[2]
                if model != "laser":
                    y = y - 0.65
            else:
                x = arraylist_coordinate[-1][0] + 1.67 * flag[0]
                y = arraylist_coordinate[-1][1] + 1.35 * flag[1] * flag[2]
                    
            if i + 2 == lay_num * 0.5 + 1:
                x = 1.67 
                y = arraylist_coordinate[-1][1]
                flag = [1, 1, 0.5]
                
                length = math.hypot(x-arraylist_coordinate[-1][0], y-arraylist_coordinate[-1][1])
                if length < 1:
                    x = 0
                    y = arraylist_coordinate[-1][1]
                    flag = [-1, 1, 0.5]
            
            layer_name = "l{0}".format(i+2)
            if i + 2 > lay_num:
                layer_name = "l{0}".format(lay_num)
                
            arraylist_coordinate.append([x, y, layer_name, "inner"])
            if i + 2 < lay_num * 0.5 + 1:
                if flag[0] < 0:                    
                    center_hole_coordinate.append([x, y, layer_name, "inner"])
            else:
                if flag[0] > 0:                    
                    center_hole_coordinate.append([x, y, layer_name, "inner"])
                    
            if flag[0] == 1:
                flag[0] = -1
            else:
                flag[0] = 1
        
        if model == "laser":
            arraylist_coordinate.append([3.73, center_hole_coordinate[-1][1], "l{0}".format(lay_num), "inner"])
        
        arraylist_coordinate.append([0, 0, "l{0}".format(lay_num), "outer"])
        
        return arraylist_coordinate, center_hole_coordinate
            
    def fill_surface(self, coordinate_x, coordinate_y, center_hole_coordinate):
        """开始铺铜"""
        #获取元素区域 建profile
        
        step = self.step
        step.COM("units,type=mm")
        #arraylist = [min(coordinate_x) - 0.6, min(coordinate_y) - 0.6,
                     #max(coordinate_x) + 0.6, max(coordinate_y) + 0.6]
        #step.COM(
                #"profile_rect,x1={0},y1={1},x2={2},y2={3}".format(*arraylist))
        
        #step.clearAll()
        #for layer in signalLayers:            
            #step.affect(layer)
            
        #step.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,\
            #min_brush=0.5,use_arcs=yes,symbol=,dx=1,dy=1,break_partial=yes,\
            #cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no")
    
        #step.COM("sr_fill,polarity=%s,step_margin_x=0.2,step_margin_y=0.2,\
            #step_max_dist_x=%s,step_max_dist_y=%s,sr_margin_x=0,\
            #sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,\
            #consider_feat=no,feat_margin=0,consider_drill=no,drill_margin=0,\
            #consider_rout=no,dest=affected_layers,layer=,\
            #attributes=no" % ("positive", 2540, 2540))  
        
        #测试位置加开窗        
        for layer in outsignalLayers:
            step.clearAll()
            step.affect(layer)
            step.resetFilter()
            step.setAttrFilter(".string,text=test_pad")
            step.selectAll()
            if step.featureSelected():
                if layer == "l1":
                    if step.isLayer("m1"):                        
                        step.copyToLayer("m1", size=4*25.4)
                    else:
                        if step.isLayer("m1-1"):
                            step.copyToLayer("m1-1", size=4*25.4)
                else:
                    if step.isLayer("m2"):                        
                        step.copyToLayer("m2", size=4*25.4)
                    else:
                        if step.isLayer("m2-1"):
                            step.copyToLayer("m2-1", size=4*25.4)
            
        #削铜宽不够15mil的细丝
        for worklayer in signalLayers:
            step.clearAll()
            step.affect(worklayer)
            step.resetFilter()
            step.filter_set(feat_types='surface')
            step.selectAll()
            step.resetFilter()
            step.filter_set(polarity='negative')
            step.selectAll()
            if step.featureSelected():
                step.removeLayer(worklayer+"_surface")
                step.moveSel(worklayer+"_surface")
                step.clearAll()
                step.affect(worklayer+"_surface")
                step.contourize(accuracy=0)               
                # step.copyLayer(job.name, step.name, worklayer+"_surface", worklayer+"_surface_bak")
                
                step.COM("sel_resize,size={0},corner_ctl=no".format(-8*25.4))
                # step.PAUSE("dd")
                step.COM("sel_resize,size={0},corner_ctl=yes".format(8*25.4))
                # step.PAUSE("dd2")
                # step.copyToLayer(worklayer+"_surface_bak", invert="yes")
                
                step.clearAll()
                step.affect(worklayer)
                step.copySel(worklayer+"_surface")
                step.copyLayer(job.name, step.name, worklayer+"_surface", worklayer)
                
                #step.clearAll()
                #step.affect(worklayer+"_surface_bak")
                #if worklayer == "l1":
                    #step.copySel(worklayer+"_surface_bak11")
                #step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                         #"area_type=rectangle,inout=inside,contour_cut=yes,margin={2},"
                         #"ref_layer={1},feat_types=line\;pad\;surface\;arc\;text,"
                         #"break_to_islands=yes".format(
                             #worklayer+"_surface_bak",
                             #worklayer+"_surface", 0
                         #))                
                ## step.contourize(accuracy=0)
                #step.COM("sel_resize,size=-1,corner_ctl=no")
                #step.COM("sel_resize,size=1,corner_ctl=no")
                ## step.PAUSE("dd3")
                #step.copyToLayer(worklayer, size=25.4, invert="yes")
            
            # if worklayer not in ["l1"]:                
            step.removeLayer(worklayer+"_surface")
            step.removeLayer(worklayer+"_surface_bak")
        
        step.clearAll()
        
        #选化层制作
        step.clearAll()
        step.affect("drl")                
        step.resetFilter()        
        for xh_layer in ["sgt-c", "sgt-s"]:
            if step.isLayer(xh_layer):
                step.setAttrFilter(".string,text=dw_pad")
                step.selectAll()
                if step.featureSelected():
                    step.copyToLayer(xh_layer, size=254)
                    
        #挡点网制作
        for dd_layer in ["md1", "md2"]:
            if step.isLayer(dd_layer):               
                
                step.clearAll()
                step.affect("drl")
                step.resetAttr()
                step.resetFilter()
                # step.setAttrFilter(".string,text=test_pad")                             
                # step.selectSymbol("r{0}".format(hole_size))
                step.selectAll()
                if step.featureSelected():
                    layer_cmd = gClasses.Layer(step, "drl")
                    feat_out = layer_cmd.featSelOut(units="mm")["pads"]
                    symbols = [obj.symbol for obj in feat_out]
                    for symbol in set(symbols):
                        step.selectNone()
                        step.selectSymbol(symbol, 1, 1)
                        if step.featureSelected():
                            
                            hole_size = float(symbol[1:])                        
                            #小孔的挡点 最大小孔450 故取两个判断条件
                            if 400< hole_size <=500:
                                resize = 3 * 25.4
                            else:
                                resize = 6 * 25.4                    
                            step.copyToLayer(dd_layer, size=resize)
                    
                    
        step.clearAll()
        for layer in signalLayers:
            step.affect(layer)
        
        step.resetFilter()
        step.setAttrFilter(".string,text=check_shave")
        step.selectAll()
        step.removeLayer("check_shave_pad")
        if step.featureSelected():
            step.copyToLayer("check_shave_pad")
        
        # 绘制削间距的line
        step.clearAll()
        step.removeLayer("spacing_line")
        step.createLayer("spacing_line")
        step.affect("spacing_line")
        center_hole_coordinate = sorted(center_hole_coordinate, key=lambda x: x[1])
        for xy1, xy2 in zip(center_hole_coordinate, center_hole_coordinate[1:]):
            x1, y1,_,_ = xy1
            x2, y2,_,_ = xy2
            step.addLine(x1, y1, x2, y2, "r{0}".format(4*25.4))
        
        step.COM("sel_extend_slots,mode=ext_to,size=600,from=center")
        step.COM("sel_transform,oper=rotate,x_anchor=0,y_anchor=0,angle=90,"
                 "direction=ccw,x_scale=1,y_scale=1,x_offset=0,y_offset=0,"
                 "mode=axis,duplicate=no")
        # step.PAUSE("check")
        if step.isLayer("check_shave_pad"):
            step.resetFilter()
            step.refSelectFilter("check_shave_pad", mode="disjoint")
            if step.featureSelected():
                step.selectDelete()
            
            step.selectAll()
            if step.featureSelected():
                step.selectNone()
                
                for layer in signalLayers:               
                    step.copyToLayer(layer, invert="yes")
                    
        #for layer in signalLayers:
            #step.resetFilter()
            #step.refSelectFilter(layer, f_types="pad", polarity="positive")
            #if step.featureSelected():                
                #step.copyToLayer(layer, invert="yes")
        
        step.removeLayer("check_shave_pad")
        step.clearAll()
        step.affect("l1")
        step.resetFilter()
        step.selectAll()
        xmin,ymin,xmax,ymax = get_layer_selected_limits(step, "l1")
        arraylist = [xmin - 0.06, ymin - 0.02, xmax + 0.02, ymax + 0.06]
        step.COM(
                "profile_rect,x1={0},y1={1},x2={2},y2={3}".format(*arraylist))
        step.COM("datum,x={0},y={1}".format(*arraylist))
        step.COM("origin,x={0},y={1},push_in_stack=1".format(*arraylist))           
        
        step.clearAll()
        # self.create_shave_pad_layer()
        
    def create_shave_pad_layer(self):
        """创建一个削镭射pad间距的负片层20231102 by lyh"""
        spacing = float(self.dic_item_value[u"镭射孔间距(mm)"])# 定义孔间距
        self.log_info = ""
        if spacing >= 1:
            return
        
        step = self.step
        all_pad_x = [value[0] for key, value in self.top_laser_dic_coordinate.iteritems()]
        all_pad_y = [value[1] for key, value in self.top_laser_dic_coordinate.iteritems()]        
        arraylist = []
        for key, value in self.top_laser_dic_coordinate.iteritems():
            x, y = value
            if value[1] == max(all_pad_y):
                if value[0] != max(all_pad_x):
                    arraylist.append([x + spacing * 0.5, y - 0.35, x + spacing * 0.5, y + 0.35,])
            else:
                if value[0] == max(all_pad_x):
                    arraylist.append([x - 0.35, y + spacing * 0.5, x + 0.35, y + spacing * 0.5,])
                else:
                    arraylist.append([x + spacing * 0.5, y - 0.35, x + spacing * 0.5, y + 0.35,])
                    arraylist.append([x - 0.35, y + spacing * 0.5, x + 0.35, y + spacing * 0.5,])
                    
        step.clearAll()
        step.removeLayer("shave_spacing_tmp")
        step.createLayer("shave_spacing_tmp")
        step.affect("shave_spacing_tmp")
        
        for xs, ys, xe, ye in arraylist:
            step.addLine(xs, ys, xe, ye, "s{0}".format(3*25.4))
            
        for worklayer in signalLayers:
            step.clearAll()
            step.resetFilter()
            step.affect(worklayer)
            step.filter_set(feat_types='pad', polarity='positive')
            step.refSelectFilter("shave_spacing_tmp")
            if step.featureSelected():
                step.COM("sel_reverse")
                if step.featureSelected():
                    step.removeLayer(worklayer+"_hct_tmp")
                    step.moveSel(worklayer+"_hct_tmp")
                    step.clearAll()
                    step.affect("shave_spacing_tmp")
                    step.resetFilter()
                    step.refSelectFilter(worklayer)
                    if step.featureSelected():
                        step.copyToLayer(worklayer, invert="yes")
                    
                    step.clearAll()
                    step.affect(worklayer+"_hct_tmp")
                    step.moveSel(worklayer)
                    step.removeLayer(worklayer+"_hct_tmp")
        
        step.removeLayer("shave_spacing_tmp")
        step.clearAll()
        
        self.log_info = u"有修改模块数据，跑完注意检查线宽、Ring环和间距设计。"
            
    def get_coordinate_dict_n(self, point_num, spacing, origin_x_start, flag=1, offset_y=0):
        """获取N型坐标信息
        spacing 间距
        origin_x_start 起点的开始位置"""
        dic_coordinate = {}
        col = -1
        for i in range(point_num):
            if not i % 4 :
                col += 1
            
            row = i % 4
            if not col % 2:
                dic_coordinate[i] = (origin_x_start + spacing * col, spacing *flag * row + offset_y)
            else:
                dic_coordinate[i] = (origin_x_start + spacing * col, spacing *flag * (3 - row) + offset_y)        
        
        return dic_coordinate

    def get_coordinate_dict_z(self, point_num, spacing, origin_x_start):
        """获取Z型坐标信息
        spacing 间距
        origin_x_start 起点的开始位置"""
        dic_coordinate = {}
        row = -1
        for i in range(point_num):
            if not i % 15 :
                row += 1
            
            col = i % 15
            if not row % 2:
                dic_coordinate[i] = (origin_x_start + spacing * col, spacing * row)
            else:
                dic_coordinate[i] = (origin_x_start + spacing * (14 - col), spacing * row)        
        
        return dic_coordinate
    
    def get_dic_add_symbol_line(self, model_type):
        """获取各层的线宽信息"""
        dic_layer_line_symbol = {}
        dic_layer_pad_symbol = {}
        for info in self.dic_item_value[u"层ring及线宽"]:
            layer = info[0]
            dic_layer_line_symbol[layer] = float(info[4])
            if model_type == "drl":
                dic_layer_pad_symbol[layer] = float(info[1]) * 2
            if model_type == "mai":
                dic_layer_pad_symbol[layer] = float(info[2]) * 2
            if model_type == "laser":
                dic_layer_pad_symbol[layer] = float(info[3]) * 2
                
        return dic_layer_line_symbol, dic_layer_pad_symbol
    
    def get_min_hole_size_from_dict(self, drill_layer):
        """获取界面上的最小孔径"""
        for info in self.dic_item_value[u"最小孔径"]:
            if info[0] == drill_layer:
                return info[1]
        else:
            showMessageInfo(u"层名{0} 最小孔径不存在，请检查层名跟界面列表内的命名是否一致！".format(drill_layer))
            sys.exit()

if __name__ == "__main__":
    main = d_coupon_aoi()
    main.create_ui_params()
    main.show()
    sys.exit(app.exec_())