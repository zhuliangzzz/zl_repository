#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20240304"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""生成XACT软件层信息的xml格式 """

import os
import sys
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
     outsignalLayers, innersignalLayers, \
     signalLayers, laser_drill_layers, mai_drill_layers, \
     get_drill_start_end_layers, tongkongDrillLayer,\
     getSmallestHole, get_layer_selected_limits, \
     solderMaskLayers, mai_man_drill_layers

from get_erp_job_info import get_barcode_mianci, get_drill_information, \
     get_cu_weight, get_inplan_mrp_info, get_laser_depth_width_rate

from create_ui_model import app, showMessageInfo, \
     QtGui, QtCore, Qt

stepname = "edit"
if "edit" not in matrixInfo["gCOLstep_name"]:
    showMessageInfo(u"edit 不存在，请检查！")
    sys.exit()
    
step = gClasses.Step(job, stepname)
step.open()
step.COM("units,type=mm")
    
matrixInfo = job.matrix.getInfo()

xact_xml_info = os.path.join(job.dbpath, "user", job.name +"_xact_xml_info.json")

class xact_layer_xml(QtGui.QWidget):
    """"""

    def __init__(self, parent=None):
        """Constructor"""
        super(xact_layer_xml, self).__init__(parent)
        
    def create_xml(self):
        """添加所有模块"""
        
        res = self.get_item_value()
        if not res:
            return
        
        self.get_layer_spacing_ring_info()
        xml_body = """<?xml version ="1.0" encoding ="utf-8" ?> 
<data panelUnits = "inches"  drillParameterUnits ="mils" >
<panel>
	<panelCode>{1}</panelCode>
			<stackup>
{0}
		</stackup>
</panel>
</data>"""
        layer_boby = """			<layer number = "{0}">
{1}
			</layer>"""
        pth_drill_body = """				<drillLayer>
					<drillLayer>{0}</drillLayer>
					<minAnnularRing>{1}</minAnnularRing>
					<minPlatedThruToCopper>{2}</minPlatedThruToCopper>
					<minPlatedThruHole>{3}</minPlatedThruHole>
					<ARAdjustment>{4}</ARAdjustment>
				</drillLayer>"""
        laser_drill_body = """				<drillLayer>
					<drillLayer>{0}</drillLayer>
					<minAnnularRing>{1}</minAnnularRing>
					<minPlatedThruHole>{2}</minPlatedThruHole>
					<ARAdjustment>{3}</ARAdjustment>
				</drillLayer>"""
        layer_body_list = []
        for worklayer in sorted(self.dic_layer_info.keys(), key=lambda x: int(x[1:])):
            index = worklayer[1:]
            arraylist = []
            for drill_layer in self.dic_layer_info[worklayer].keys():
                # 厂家规定 孔到铜没有数据都默认7，孔环没有数据默认5 20240304 by lyh
                min_ring = self.dic_layer_info[worklayer][drill_layer].get("min_ring", 5)
                hole_to_copper = self.dic_layer_info[worklayer][drill_layer].get("hole_to_copper", 7)
                min_hole = self.dic_layer_info[worklayer][drill_layer].get("min_hole_size", None)
                if min_hole is None:
                    # 存在盲叠埋的情况
                    continue
                
                if drill_layer in ["drl", "cdc", "cds"]:
                    t = pth_drill_body.format("drl", "%.1f" % min_ring, "%.1f" % hole_to_copper,"%.1f" % min_hole,0)
                    arraylist.append((t, 1))
                else:
                    if drill_layer.startswith("s"):
                        t = laser_drill_body.format(drill_layer, "%.1f" % min_ring, "%.1f" % min_hole,0)
                        arraylist.append((t, 3))
                    else:
                        t = pth_drill_body.format(drill_layer, "%.1f" % min_ring, "%.1f" % hole_to_copper,"%.1f" % min_hole,0)
                        arraylist.append((t, 2))
            new_arraylist = []
            for info in sorted(arraylist, key=lambda x: x[1]):
                new_arraylist.append(info[0])
            layer_body_list.append(layer_boby.format(index, "\n".join(new_arraylist)))
        
        xml_info = xml_body.format("\n".join(layer_body_list), job.name.upper())
        
        # print(xml_info)
        xml_file_path = "/id/workfile/film/{0}/{0}.xml".format(job.name)
        with open("/tmp/{0}.xml".format(job.name), "w") as f:
            f.write(xml_info)
        
        try:
            os.makedirs("/id/workfile/film/{0}".format(job.name))
        except:
            pass
        with open(xml_file_path, "w") as f:
            f.write(xml_info)
            
        showMessageInfo(u"XACT xml文件生成 运行完成！<br>{0}".format(xml_file_path))
        app.quit()
        
    def get_layer_spacing_ring_info(self):
        """获取各层的ring及孔到铜的距离"""
        stepname = "edit"
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        matrixInfo = job.matrix.getInfo()
        
        for layer in matrixInfo["gROWname"]:
            if "ms_1_" in layer or "mk_1_" in layer:
                step.removeLayer(layer)
                
        step.clearAll()
        for worklayer in innersignalLayers:
            step.affect(worklayer)
        
        chklist = "checklist_space"
        step.COM("chklist_from_lib,chklist=hdi-drc,profile=none,customer=")
        step.COM("chklist_delete,chklist={0}".format(chklist))
        step.COM("chklist_create,chklist={0},allow_save=no".format(chklist))
        step.COM("chklist_open,chklist=hdi-drc")
        step.COM("chklist_show,chklist=hdi-drc,nact=3,pinned=no,pinned_enabled=yes")
        
        step.COM("""chklist_cupd,chklist=hdi-drc,nact=3,params=((pp_layer=.affected)
        (pp_spacing=254)(pp_r2c=508)(pp_d2c=254)(pp_sliver=101.6)(pp_min_pad_overlap=127)
        (pp_tests=Spacing\;Drill)(pp_selected=All)(pp_check_missing_pads_for_drills=Yes)
        (pp_use_compensated_rout=Skeleton)(pp_sm_spacing=No)),mode=regular""")
        
        step.COM("chklist_run,chklist=hdi-drc,nact=3,area=profile")
        step.COM("chklist_pclear")
        step.COM("chklist_pcopy,chklist=hdi-drc,nact=3")
        step.COM("chklist_close,chklist=hdi-drc,mode=hide")
        step.COM("show_tab,tab=Checklists,show=no")
        
        step.COM("chklist_create,chklist=checklist_space")
        step.COM("chklist_ppaste,chklist=checklist_space,row=0")
        step.COM("chklist_create_lyrs,chklist=checklist_space,severity=3,suffix=ref")
        step.COM("chklist_close,chklist=checklist_space,mode=hide")
        
        matrixInfo = job.matrix.getInfo()
        
        step.clearAll()
        step.resetFilter()      
        
        self.dic_layer_info = {}
        for worklayer in innersignalLayers:
            self.dic_layer_info[worklayer] = {}
            step.clearAll()
            ref_layer = "{0}_ar_ring".format(worklayer)
            step.removeLayer(ref_layer)
            for layer in matrixInfo["gROWname"]:
                if "ms_1" in layer and worklayer in layer:
                    step.affect(layer)
                    step.resetFilter()
                    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=pth_ar")
                    step.selectAll()
                    step.resetFilter()
                    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=via_ar")          
                    step.selectAll()
                    step.resetFilter()  
                    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=mid_ramge_pth_ar")
                    step.selectAll()                  
                    if step.featureSelected():
                        step.copySel(ref_layer)            
                    # step.removeLayer(layer)
                    
            ref_layer1 = "{0}_hole_to_copper".format(worklayer)
            step.removeLayer(ref_layer1)
            for layer in matrixInfo["gROWname"]:
                if "ms_1" in layer and worklayer in layer:
                    step.affect(layer)
                    step.resetFilter()
                    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=via2c")
                    step.selectAll()
                    step.resetFilter()
                    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=via2l")                    
                    step.selectAll()
                    step.resetFilter()
                    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=via2p")          
                    step.selectAll()
                    step.resetFilter()
                    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=pth2c")
                    step.selectAll()
                    step.resetFilter()
                    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=pth2l")                    
                    step.selectAll()
                    step.resetFilter()
                    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=pth2p")          
                    step.selectAll()                    
                    if step.featureSelected():
                        step.copySel(ref_layer1)            
                    # step.removeLayer(layer)
                    
            ref_layer2 = "{0}_laser_via_ar_ring".format(worklayer)
            step.removeLayer(ref_layer2)
            for layer in matrixInfo["gROWname"]:
                if "ms_1" in layer and worklayer in layer:
                    step.affect(layer)
                    step.resetFilter()
                    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=laser_via_ar")
                    step.selectAll()
                    if step.featureSelected():
                        step.copySel(ref_layer2)            
                    # step.removeLayer(layer)                    
            
            mai_drill = mai_drill_layers + mai_man_drill_layers
            tong_drill = ["drl"]
            if step.isLayer("cdc"):
                tong_drill = ["cdc"]
            if step.isLayer("cds"):
                tong_drill = ["cds"]
                
            arraylist_layers = [mai_drill, tong_drill]
            if getattr(self, "tong_hole_type", None) == "no_small_pth":
                arraylist_layers = [mai_drill]            
            
            for array_drill_layers in arraylist_layers:
                # 最小孔
                for drill_layer in array_drill_layers:                    
                    small_hole = self.get_min_hole_size_from_dict(drill_layer)
                    if small_hole == -1:
                        continue
                    if drill_layer in mai_drill:
                        layer1, layer2 = get_drill_start_end_layers(matrixInfo, drill_layer)
                        index1 = signalLayers.index(layer1)
                        index2 = signalLayers.index(layer2)
                        if min([index1, index2]) <= signalLayers.index(worklayer) <= max([index1, index2]):
                            if self.dic_layer_info[worklayer].has_key(drill_layer):
                                self.dic_layer_info[worklayer][drill_layer]["min_hole_size"] = small_hole
                            else:
                                self.dic_layer_info[worklayer][drill_layer] = {"min_hole_size": small_hole}
                    else:                        
                        if self.dic_layer_info[worklayer].has_key(drill_layer):
                            self.dic_layer_info[worklayer][drill_layer]["min_hole_size"] = small_hole
                        else:
                            self.dic_layer_info[worklayer][drill_layer] = {"min_hole_size": small_hole}
                
                # 机械孔ring
                step.clearAll()
                step.resetFilter()
                if step.isLayer(ref_layer):     
                    step.affect(ref_layer)
                    
                    for drill_layer in array_drill_layers:
                        step.refSelectFilter(drill_layer)
                            
                        if step.featureSelected():
                            layer_cmd = gClasses.Layer(step, ref_layer)
                            feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["lines"]
                            min_ring = min([obj.len for obj in feat_out])
                            if self.dic_layer_info[worklayer].has_key(drill_layer):
                                self.dic_layer_info[worklayer][drill_layer]["min_ring"] = min_ring * 39.37
                            else:
                                self.dic_layer_info[worklayer][drill_layer] = {"min_ring": min_ring * 39.37}
                
                # 孔到铜
                step.clearAll()
                step.resetFilter()                            
                if step.isLayer(ref_layer1):
                    step.affect(ref_layer1)
                    
                    for drill_layer in array_drill_layers:
                        step.refSelectFilter(drill_layer)                    
                        if step.featureSelected():
                            layer_cmd = gClasses.Layer(step, ref_layer1)
                            feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["lines"]
                            min_spacing = min([obj.len for obj in feat_out])
                            if self.dic_layer_info[worklayer].has_key(drill_layer):
                                self.dic_layer_info[worklayer][drill_layer]["hole_to_copper"] = min_spacing * 39.37
                            else:
                                self.dic_layer_info[worklayer][drill_layer] = {"hole_to_copper": min_spacing * 39.37}
                                
            # 镭射ring 及最小孔
            for drill_layer in laser_drill_layers:                    
                small_hole = self.get_min_hole_size_from_dict(drill_layer)
                if small_hole == -1:
                    continue
                top_laser_siglayer = "l{0}".format(drill_layer.split("-")[0][1:])
                if top_laser_siglayer == worklayer:
                    if self.dic_layer_info[worklayer].has_key(drill_layer):
                        self.dic_layer_info[worklayer][drill_layer]["min_hole_size"] = small_hole
                    else:
                        self.dic_layer_info[worklayer][drill_layer] = {"min_hole_size": small_hole}                        
                        
                    step.clearAll()
                    step.resetFilter()
                    if step.isLayer(ref_layer2):     
                        step.affect(ref_layer2)
                        
                        step.refSelectFilter(drill_layer)                            
                        if step.featureSelected():
                            layer_cmd = gClasses.Layer(step, ref_layer2)
                            feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["lines"]
                            min_ring = min([obj.len for obj in feat_out])
                            if self.dic_layer_info[worklayer].has_key(drill_layer):
                                self.dic_layer_info[worklayer][drill_layer]["min_ring"] = min_ring * 39.37
                            else:
                                self.dic_layer_info[worklayer][drill_layer] = {"min_ring": min_ring * 39.37}                        
    
        matrixInfo = job.matrix.getInfo()        
        for layer in matrixInfo["gROWname"]:
            if "ms_1_" in layer or "mk_1_" in layer:
                step.removeLayer(layer)
            if "_ar_ring" in layer:
                step.removeLayer(layer)
            if "_laser_via_ar_ring" in layer:
                step.removeLayer(layer)
            if "_hole_to_copper" in layer:
                step.removeLayer(layer)
        
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
    
        arraylist1 = [{u"允许修改信息": "QCheckBox"},]

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
        btngroup_layout.addWidget(self.pushButton2,0,2,1,1)
        btngroup_layout.setSpacing(5)
        btngroup_layout.setContentsMargins(5, 5,5, 5)
        btngroup_layout.setAlignment(QtCore.Qt.AlignTop)          
    
        main_layout =  QtGui.QGridLayout()
        main_layout.addWidget(self.titlelabel,0,0,1,10, QtCore.Qt.AlignCenter)
        # main_layout.addWidget(widget1,1,0,1,10)
        main_layout.addWidget(self.tableWidget1,2,0,1,2)
        # main_layout.addWidget(self.tableWidget2,2,2,1,9)
        main_layout.addLayout(btngroup_layout, 8, 0,1, 10)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(main_layout)
    
        # main_layout.setSizeConstraint(Qt.QLayout.SetFixedSize)
    
        self.pushButton.clicked.connect(self.create_xml)
        self.pushButton1.clicked.connect(sys.exit)
        self.pushButton2.clicked.connect(self.reloading_data)
    
        self.setWindowTitle(u"XACT各层xml文件参数确认%s" % __version__)
        self.setMainUIstyle()
        
        self.setTableWidget(self.tableWidget1, [u"钻带", u"最小孔径(mil)"])
        self.setTableWidget(self.tableWidget2, [u"层名", u"PTH孔最小ring环", u"最小PTH孔到铜", u"最小PTH孔径", u"laser孔最小ring环", u"最小laser孔径",])
        self.tableWidget1.setEnabled(False)
        self.tableWidget2.setEnabled(False)            
        self.initial_value()
        
    def initial_value(self):
        """初始化参数"""  
        self.add_data_to_table()        
            
    def reloading_data(self):
        self.setValue()
        if not os.path.exists(xact_xml_info):
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
        #arraylist = []
        #for key in sorted(self.dic_layer_info.keys(), key=lambda x: int(x[1:])):
            #arraylist.append([key]+ self.dic_layer_info[key])
            
        #self.set_model_data(self.tableWidget2, arraylist)        
        
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
        if os.path.exists(xact_xml_info):
            with open(xact_xml_info) as file_obj:
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
    
    def get_min_hole_size_from_dict(self, drill_layer):
        """获取界面上的最小孔径"""
        for info in self.dic_item_value[u"最小孔径"]:
            if info[0] == drill_layer:
                return float(info[1])
        else:
            return -1
        # else:
        #     showMessageInfo(u"层名{0} 最小孔径不存在，请检查层名跟界面列表内的命名是否一致！".format(drill_layer))
        #     sys.exit()
        
    def get_item_value(self):
        """获取界面参数"""	
        self.dic_item_value = {}
        #for key, value in self.dic_editor.iteritems():
            #if isinstance(self.dic_editor[key], QtGui.QLineEdit):
                #self.dic_item_value[key] = unicode(self.dic_editor[key].text(
                    #).toUtf8(), 'utf8', 'ignore').encode('cp936').decode("cp936")
            #elif isinstance(self.dic_editor[key], QtGui.QComboBox):
                #self.dic_item_value[key] = unicode(self.dic_editor[key].currentText(
                    #).toUtf8(), 'utf8', 'ignore').encode('cp936').decode("cp936")                
                                  
        self.dic_item_value[u"最小孔径"] = []
        model = self.tableWidget1.model()

        for row in range(model.rowCount()):
            arraylist = []
            flag = True
            for col in range(model.columnCount()):
                value = str(model.item(row, col).text())
                if col <> 0:
                    try:
                        float(value)
                    except:
                        flag = False
                        # QtGui.QMessageBox.information(self, u'提示', u'检测到 %s 最小孔 有参数[ %s ]为空或非法数字,请检查~' % (
                        #     model.item(row, 0).text(), value), 1)
                        # # return 0
                        # sys.exit()
                arraylist.append(value)
            if flag:
                self.dic_item_value[u"最小孔径"].append(arraylist)
            
        #self.dic_item_value[u"层ring及线宽"] = []
        #model = self.tableWidget2.model()
        #for row in range(model.rowCount()):
            #arraylist = []
            #for col in range(model.columnCount()):
                #value = str(model.item(row, col).text())
                #if col <> 0:
                    #try:
                        #float(value)
                    #except:
                        #QtGui.QMessageBox.information(self, u'提示', u'检测到 %s 层ring及线宽 有参数[ %s ]为空或非法数字,请检查~' % (
                            #model.item(row, 0).text(), value), 1)
                        #return 0
                #arraylist.append(value)
                
            #self.dic_item_value[u"层ring及线宽"].append(arraylist)            

        #with open(hct_info, 'w') as file_obj:
            #json.dump(self.dic_item_value, file_obj)

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
                    edit_step.COM("units,type=mm")
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
                    
                    hole_size = getSmallestHole(job.name, "edit", drillLayer+"_tmp")
                    
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
                    
                #hole_size = hole_size if hole_size else 452
                #if hole_size > 452:
                    #hole_size = 452
            else:
                if not hole_size:
                    if drillLayer in laser_drill_layers:
                        # 镭射层板内没孔的不计算在内
                        del dic_min_hole_size[drillLayer]
                        
                    continue
                
            dic_min_hole_size[drillLayer] = hole_size * 0.03937
            
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
            step.COM("units,type=mm")
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

if __name__ == "__main__":
    main = xact_layer_xml()
    main.create_ui_params()
    main.show()
    sys.exit(app.exec_())