#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20241107"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""复制层给到临时修改资料使用 """

import sys
import os
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")   
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
    
import pic
import re
import time
import gClasses
import json
import GetData
from genesisPackages import job, matrixInfo, \
    stepname, get_profile_limits, signalLayers, \
    tongkongDrillLayer, mai_drill_layers, mai_man_drill_layers, \
    laser_drill_layers, lay_num, outsignalLayers, innersignalLayers, \
    silkscreenLayers, solderMaskLayers, top, get_panelset_sr_step

from PyQt4 import QtCore, QtGui, Qt
from create_ui_model import app, showMessageInfo
from oracleConnect import oracleConn



import MySQL_DB
conn = MySQL_DB.MySQL()
dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                           username='root', passwd='k06931!')

class auto_copy_layer(QtGui.QWidget):
    def __init__(self, parent=None):
        super(auto_copy_layer, self).__init__(parent)

        self.resize(400, 100)
        self.setGeometry(700, 300, 0, 0)
        
        self.getDATA = GetData.Data()
        
        self.setObjectName("mainWindow")
        layer_out = self.create_ui()
        layer_out.setSizeConstraint(Qt.QLayout.SetFixedSize)
        self.setLayout(layer_out)
        
        self.check_layers_is_normal()
        
        self.initial_value()
        
        self.setMainUIstyle()
        self.setWindowTitle(u"自动复制临时层程序%s" % __version__)
        
    def create_ui(self):                  

        self.list_box = QtGui.QListWidget()
        self.list_box.setSelectionMode(3)
        self.list_box.setFixedHeight(500)
        self.list_box.clear()
        if "restore_normal_layer" in sys.argv[1:]:
            for i, layer in enumerate(matrixInfo["gROWname"]):      
                if matrixInfo['gROWcontext'][i] == "board" and re.match(".*-ls\d+.*", layer):
                    self.list_box.addItem(layer)
        elif "restore_linshi_layer" in sys.argv[1:]:
            for i, layer in enumerate(matrixInfo["gROWname"]):      
                if matrixInfo['gROWcontext'][i] != "board" and re.match(".*-ls\d+.*", layer):
                    self.list_box.addItem(layer)            
        else:
            for i, layer in enumerate(matrixInfo["gROWname"]):
                if "-ls" not in layer:                    
                    self.list_box.addItem(layer)
                
        label = QtGui.QLabel(u"请按住CTRL键进行多选")
        self.out_checkbox = QtGui.QCheckBox(u"外层线路")
        self.inn_checkbox = QtGui.QCheckBox(u"内层线路")
        self.silk_checkbox = QtGui.QCheckBox(u"文字层")
        self.mask_checkbox = QtGui.QCheckBox(u"阻焊层")
        self.drill_checkbox = QtGui.QCheckBox(u"钻孔层")
        self.board_checkbox = QtGui.QCheckBox(u"board层")
        self.all_checkbox = QtGui.QCheckBox(u"全选")
        
        self.insert_layer_btn = QtGui.QPushButton(u"确定")
        self.insert_layer_btn.clicked.connect(self.insert_layers)
        
        self.out_checkbox.clicked.connect(self.select_layers)
        self.inn_checkbox.clicked.connect(self.select_layers)
        self.silk_checkbox.clicked.connect(self.select_layers)
        self.mask_checkbox.clicked.connect(self.select_layers)
        self.drill_checkbox.clicked.connect(self.select_layers)
        self.board_checkbox.clicked.connect(self.select_layers)
        self.all_checkbox.clicked.connect(self.select_layers)
        
        self.dic_editor = {}
        self.dic_label = {}
        
        arraylist1 = [{u"固定后缀(不可编辑)": "QLineEdit"},
                      {u"自定义后缀": "QLineEdit"},]
        if "restore_linshi_layer" in sys.argv[1:]:
            arraylist1.append({u"筛选后缀": "QComboBox"})
            
        if "restore_normal_layer" in sys.argv[1:]:
            arraylist1.append({u"还原模式": "QComboBox"})
            arraylist1.append({u"筛选后缀": "QComboBox"})

        group_box_font = QtGui.QFont()
        group_box_font.setBold(True)    
        self.widget1 = self.set_widget(group_box_font,
                                       arraylist1,
                                       u"基本信息确认",
                                       "")
        
        gridlayout = QtGui.QGridLayout()
        gridlayout.addWidget(self.widget1, 0, 0, 1, 1)
        gridlayout.addWidget(self.list_box, 2, 0, 10, 1)
        gridlayout.addWidget(self.out_checkbox, 3, 1, 1, 1)
        gridlayout.addWidget(self.inn_checkbox, 4, 1, 1, 1)
        gridlayout.addWidget(self.silk_checkbox, 5, 1, 1, 1)
        gridlayout.addWidget(self.mask_checkbox, 6, 1, 1, 1)
        gridlayout.addWidget(self.drill_checkbox, 7, 1, 1, 1)
        gridlayout.addWidget(self.board_checkbox, 8, 1, 1, 1)
        gridlayout.addWidget(self.all_checkbox, 9, 1, 1, 1)
        gridlayout.addWidget(label, 20, 0, 1, 1)
        gridlayout.addWidget(self.insert_layer_btn, 20, 1, 1, 1)

        return gridlayout
    
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

                if key == u"筛选后缀":
                    self.dic_editor[key].currentIndexChanged.connect(self.hide_show_listboxitems)
                    
                if key == u"还原模式":
                    self.dic_editor[key].currentIndexChanged.connect(self.show_linshi_layers)

        gridlayout.setSpacing(5)
        gridlayout.setContentsMargins(5, 5,5, 5)
        gridlayout.setAlignment(QtCore.Qt.AlignTop)

        return gridlayout
    
    def initial_value(self):
        """初始化参数""" 
        time_form = time.strftime('%y%m%d.%H%M', time.localtime(time.time()))
        self.dic_editor[u"固定后缀(不可编辑)"].setText("-ls{0}".format(time_form))
        self.dic_editor[u"固定后缀(不可编辑)"].setEnabled(False)
        if "restore_normal_layer" in sys.argv[1:] or "restore_linshi_layer" in sys.argv[1:]:
            self.widget1.hide()
            self.out_checkbox.hide()
            self.inn_checkbox.hide()
            self.silk_checkbox.hide()
            self.mask_checkbox.hide()
            self.drill_checkbox.hide()
            self.board_checkbox.hide()
            self.dic_editor[u"固定后缀(不可编辑)"].hide()
            self.dic_editor[u"自定义后缀"].hide()            
            self.dic_label[u"固定后缀(不可编辑)"].hide()
            self.dic_label[u"自定义后缀"].hide()               
            
        if "restore_linshi_layer" in sys.argv[1:]:
            self.widget1.show()
            arraylist_suffix = [""]
            for index in range(self.list_box.count()):
                item = self.list_box.item(index)                
                text = str(item.text())                
                arraylist_suffix.append(text.split("-ls")[1])                
            
            self.dic_editor[u"筛选后缀"].addItems(sorted(list(set(arraylist_suffix))))
            
        if "restore_normal_layer" in sys.argv[1:]:
            self.widget1.show()
            items = [u"board临时层改misc属性", u"临时层替换正式层"]
            self.dic_editor[u"还原模式"].addItems(items)
            self.dic_editor[u"还原模式"].setFixedWidth(180)
            
    def hide_show_listboxitems(self):
        current_filter_text = str(self.dic_editor[u"筛选后缀"].currentText())
        for index in range(self.list_box.count()):
            item = self.list_box.item(index)                
            text = str(item.text())
            if current_filter_text not in text:
                item.setHidden(True)
            else:
                item.setHidden(False)
                
    def show_linshi_layers(self):
        if self.sender().currentIndex() == 1:
            self.list_box.clear()
            for i, layer in enumerate(matrixInfo["gROWname"]):      
                if re.match(".*-ls\d+.*", layer):
                    self.list_box.addItem(layer)
                    
            arraylist_suffix = [""]
            for index in range(self.list_box.count()):
                item = self.list_box.item(index)                
                text = str(item.text())                
                arraylist_suffix.append(text.split("-ls")[1])                
            
            self.dic_editor[u"筛选后缀"].addItems(sorted(list(set(arraylist_suffix))))
            self.dic_editor[u"筛选后缀"].setFixedWidth(150)
        else:
            self.list_box.clear()
            for i, layer in enumerate(matrixInfo["gROWname"]):      
                if matrixInfo["gROWcontext"][i] == "board" and re.match(".*-ls\d+.*", layer):
                    self.list_box.addItem(layer)            
                
    def check_layers_is_normal(self):
        """检测层名是否正常"""
        if not ("restore_normal_layer"  in sys.argv[1:] or "restore_linshi_layer" in sys.argv[1:]):
            matrixInfo = job.matrix.getInfo()
            error_layers = []
            for i,layer in enumerate(matrixInfo['gROWname']):
                if matrixInfo['gROWcontext'][i] == "board" and re.match(".*-ls\d+.*", layer):
                    error_layers.append(layer)
                    
            if error_layers:
                new_error_layers = [";".join(error_layers[x:x+3]) for x in range(len(error_layers))[::3]]
                showMessageInfo(u"检测到board层中存在临时层{0}，请先将临时层还原正常，再运行程序！！".format("<br>".join(new_error_layers)))            
                exit(0)
        
    def select_layers(self):
        layers = []
        for name in [u"外层线路", u"内层线路", u"文字层",
                     u"阻焊层", u"钻孔层", u"board层", u"全选"]:
            if self.sender().text() == QtCore.QString(name):                
                if name == u"外层线路":
                    layers = outsignalLayers
                elif name == u"内层线路":
                    layers = innersignalLayers
                elif name == u"文字层":
                    layers = silkscreenLayers
                elif name == u"阻焊层":
                    layers = solderMaskLayers
                elif name == u"钻孔层":
                    for i, layer in enumerate(matrixInfo["gROWname"]):
                        if matrixInfo["gROWcontext"][i] == "board" and matrixInfo["gROWlayer_type"][i] == "drill":
                            layers.append(layer)                  
                elif name == u"board层":
                    for i, layer in enumerate(matrixInfo["gROWname"]):
                        if matrixInfo["gROWcontext"][i] == "board":
                            layers.append(layer)
                elif name == u"全选":
                    layers = matrixInfo["gROWname"]
                            
        if self.sender().isChecked():            
            for index in range(self.list_box.count()):
                item = self.list_box.item(index)
                text = str(item.text())
                if text in layers:
                    self.list_box.setItemSelected(item, True)
        else:
            for index in range(self.list_box.count()):
                item = self.list_box.item(index)
                text = str(item.text())
                if text in layers:
                    self.list_box.setItemSelected(item, False) 
                
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
        
    def insert_layers(self):        
        layers = []
        for item in self.list_box.selectedItems():
            if not item.isHidden():
                layers.append(str(item.text()))
        
        if not layers:
            showMessageInfo(u"未选中层别，请检查")
            return
        
        step = gClasses.Step(job, "panel")
        flip_steps = []
        flip_steps = self.flipStepName(step, "panel", flip_steps)
        if flip_steps:                  
            flipstep = gClasses.Step(job, "edit")
            flipstep.open()
            flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % job.name)
            
        if "restore_normal_layer" in sys.argv[1:]:
            if self.dic_editor[u"还原模式"].currentIndex() == 1:
                self.layer_list = [name.split("-ls")[0] for name in layers]
                res = self.getChangeDetial()
                if not res or "-lyh" in job.name:
                    self.change_stastic_layer_text_to_dynamic(layers)
                    
                    self.replace_normal_layer_by_linshi_layer(layers)
                    showMessageInfo(u"修改完成，请检查！")
                else:
                    showMessageInfo(u"检测到以下层别被锁定，请通知审核解锁后再操作：", *res)                
                exit(0)
            
        if "restore_normal_layer" in sys.argv[1:] or "restore_linshi_layer" in sys.argv[1:]:
            self.restore_original_linshi_layer(layers)
            
            if flip_steps:               
                flipstep = gClasses.Step(job, "edit")
                flipstep.open()
                flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % job.name)                
            
            exit(0)        
            
        suffix1 = str(self.dic_editor[u"固定后缀(不可编辑)"].text())
        suffix2 = str(self.dic_editor[u"自定义后缀"].text())
        middle_siglayer = signalLayers[len(signalLayers) / 2]
        
        matrixInfo = job.matrix.getInfo()
        for layer in layers:
            new_layer = layer + suffix1
            if suffix2:
                new_layer = layer + suffix1 + "-" + suffix2
                
            if new_layer in matrixInfo["gROWname"]:            
                showMessageInfo(u"检测到已存在相同临时层{0}，请过1分钟后再生成临时层或加自定义后缀试试，请检查！！".format(new_layer))
                return                
        
        dic_drill_start_end = self.get_drill_start_end_layers()
        check_layers = []
        for layer in layers:
            new_layer = layer + suffix1
            if suffix2:
                new_layer = layer + suffix1 + "-" + suffix2
            matrixInfo = job.matrix.getInfo()
            for i in xrange(len(matrixInfo['gROWcontext'])):
                if matrixInfo['gROWname'][i] == layer:
                    origRow = matrixInfo["gROWrow"][i]
                    middle_siglayer_index = matrixInfo['gROWname'].index(middle_siglayer)
                    if i < middle_siglayer_index:
                        toRow = origRow
                    else:
                        toRow = origRow + 1
                        
                    job.COM("matrix_copy_row,job={0},matrix=matrix,row={1},ins_row={2}".format(job.name,origRow,toRow))
                    new_matrixInfo = job.matrix.getInfo()
                    toRow_name = [ name for name in new_matrixInfo['gROWname'] if name not in matrixInfo['gROWname']]
                    
                    for key, value in dic_drill_start_end.iteritems():
                        if value["start"] == layer:
                            value["start"] = new_layer
                        if value["end"] == layer:
                            value["end"] = new_layer
                            
                    if len(toRow_name) == 1:
                        toRow_name = toRow_name[0]
                        job.COM("matrix_rename_layer,job={0},matrix=matrix,layer={1},new_name={2}".format(job.name, toRow_name, new_layer))
                        job.COM("matrix_refresh,job={0},matrix=matrix".format(job.name))
                        check_layers.append(new_layer)
                        break
                    
            job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(job.name, layer))
        
        new_dic_drill_start_end = self.get_drill_start_end_layers()
        
        for key, value in new_dic_drill_start_end.iteritems():
            if value["start"] and value["end"]:
                
                for new_key in [key, key.split("-ls")[0]]:
                    if not dic_drill_start_end.has_key(new_key):
                        continue
                    
                    if dic_drill_start_end[new_key]["start"] == value["start"] and \
                       dic_drill_start_end[new_key]["end"] == value["end"]:
                        continue
                    
                    job.COM("matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(
                        job.name, key, dic_drill_start_end[new_key]["start"],
                        dic_drill_start_end[new_key]["end"]
                    ))
        
        if flip_steps:               
            flipstep = gClasses.Step(job, "edit")
            flipstep.open()
            flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % job.name)
            
        self.modify_dynamic_layer_text(check_layers)
            
        showMessageInfo(u"创建完成，请检查！")
        exit(0)
        
    def get_drill_start_end_layers(self):        
        matrixInfo = job.matrix.getInfo()
        dic_drill_start_end = {}
        for i, layer in enumerate(matrixInfo["gROWname"]):
            if matrixInfo["gROWlayer_type"][i] == "drill" and \
               matrixInfo["gROWcontext"][i] == "board":                
                row = matrixInfo["gROWname"].index(layer)
                gROWdrl_start = matrixInfo["gROWdrl_start"][row]
                gROWdrl_end = matrixInfo["gROWdrl_end"][row]
                dic_drill_start_end[layer] = {"start": gROWdrl_start,"end": gROWdrl_end,}
        
        return dic_drill_start_end

    def modify_dynamic_layer_text(self, check_layers):
        """修改动态层别 text层名"""
        all_steps = get_panelset_sr_step(job.name, "panel")
        for stepname in all_steps + ["panel"]:            
            step = gClasses.Step(job, stepname)
            step.open()           
            for worklayer in check_layers:
                if not step.isLayer(worklayer):
                    continue
                step.clearAll()
                step.affect(worklayer)
                step.resetFilter()
                step.filter_set(feat_types='text')
                step.selectAll()
                layer_cmd = gClasses.Layer(step, worklayer)
                find_indexes = []
                find_texts = []
                if step.featureSelected():
                    feat_out = layer_cmd.featout_dic_Index(options="feat_index+select")["text"]
                    barcode_feat_out = layer_cmd.featout_dic_Index(options="feat_index+select")["barcodes"]
                    for obj in feat_out + barcode_feat_out:                        
                        if "$$layer" in str(obj.text).lower():
                            find_indexes.append(obj.feat_index)
                            find_texts.append(str(obj.text).replace("'", "").replace('"', ""))
                
                if find_indexes:
                    step.clearAll()
                    step.affect(worklayer)
                    step.resetFilter()
                    for i, index in enumerate(find_indexes):
                        step.selectNone()
                        step.selectFeatureIndex(worklayer, index)
                        if step.featureSelected():
                            text = find_texts[i].upper().replace("$$LAYER", worklayer.split("-ls")[0].upper())
                            step.COM("sel_change_txt,text={0},x_size=-1,y_size=-1,w_factor=-1,"
                                     "polarity=no_change,mirror=no_change,fontname=".format(text))
                            
                        step.selectFeatureIndex(worklayer, index)
                        if step.featureSelected():
                            step.addAttr(".string", attrVal=find_texts[i], valType='text', change_attr="yes")
                            
                        step.selectFeatureIndex(worklayer, index)
                        if step.featureSelected():                            
                            step.addAttr(".bit", attrVal="linshi_layer_text", valType='text', change_attr="yes")
                            
                if stepname == "panel":
                    self.change_panel_symbol_dynamic_layer(step, worklayer)
                    
            step.clearAll()
            
    def change_stastic_layer_text_to_dynamic(self, check_layers):
        """把静态层名还原成动态的"""
        all_steps = get_panelset_sr_step(job.name, "panel")
        for stepname in all_steps + ["panel"]:            
            step = gClasses.Step(job, stepname)
            step.open()           
            for worklayer in check_layers:
                if not step.isLayer(worklayer):
                    continue
                step.clearAll()
                step.affect(worklayer)
                step.resetFilter()
                step.filter_set(feat_types='text')
                step.setAttrFilter(".bit,text=linshi_layer_text")
                step.selectAll()
                layer_cmd = gClasses.Layer(step, worklayer)
                if step.featureSelected():
                    feat_out = layer_cmd.featout_dic_Index(options="feat_index+select")["text"]
                    barcode_feat_out = layer_cmd.featout_dic_Index(options="feat_index+select")["barcodes"]
                    for obj in feat_out + barcode_feat_out:
                        step.selectFeatureIndex(worklayer, obj.feat_index)
                        if step.featureSelected():
                            text = getattr(obj, "string", None)
                            if text is not None:                                
                                step.COM("sel_change_txt,text={0},x_size=-1,y_size=-1,w_factor=-1,"
                                         "polarity=no_change,mirror=no_change,fontname=".format(text))
                            
                if stepname == "panel":
                    step.selectNone()
                    step.resetFilter()
                    step.selectSymbol("sh-op*", 1, 1)
                    if step.featureSelected():
                        layer_cmd = gClasses.Layer(step, worklayer)
                        feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]            
                        for obj in feat_out:
                            if "-ls-" in obj.symbol:
                                step.selectNone()
                                step.selectSymbol(obj.symbol, 1, 1)
                                step.changeSymbol(obj.symbol.split("-ls-")[0])
                                
            step.clearAll()
    
    def change_panel_symbol_dynamic_layer(self, step, worklayer):
        """修改symbol内的动态layer名"""
        step = gClasses.Step(job, step.name)
        step.selectNone()
        step.resetFilter()
        step.selectSymbol("sh-op*", 1, 1)
        if step.featureSelected():
            layer_cmd = gClasses.Layer(step, worklayer)
            feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]            
            step.removeLayer("symbol_tmp")
            step.createLayer("symbol_tmp")
            for obj in feat_out:
                step.clearAll()
                step.affect("symbol_tmp")
                step.COM("truncate_layer,layer=symbol_tmp")
                step.addPad(0, 0, obj.symbol)
                step.resetFilter()
                step.selectSymbol(obj.symbol, 1, 1)
                if step.featureSelected():
                    step.COM("sel_break_level,attr_mode=merge")                    
                    
                    step.resetFilter()
                    step.filter_set(feat_types='text')
                    step.selectAll()
                    layer_cmd = gClasses.Layer(step, "symbol_tmp")
                    find_indexes = []
                    find_texts = []
                    if step.featureSelected():
                        feat_out = layer_cmd.featout_dic_Index(options="feat_index+select")["text"]
                        barcode_feat_out = layer_cmd.featout_dic_Index(options="feat_index+select")["barcodes"]
                        for text_obj in feat_out + barcode_feat_out:                        
                            if "$$layer" in str(text_obj.text).lower():
                                find_indexes.append(text_obj.feat_index)
                                find_texts.append(str(text_obj.text).replace("'", "").replace('"', ""))
                    
                    if find_indexes:
                        for i, index in enumerate(find_indexes):
                            step.selectNone()
                            step.selectFeatureIndex("symbol_tmp", index)
                            if step.featureSelected():
                                text = find_texts[i].upper().replace("$$LAYER", worklayer.split("-ls")[0].upper())
                                step.COM("sel_change_txt,text={0},x_size=-1,y_size=-1,w_factor=-1,"
                                         "polarity=no_change,mirror=no_change,fontname=".format(text))
                    
                    step.selectNone()
                    step.resetFilter()
                    step.selectAll()
                    step.COM("sel_create_sym,symbol={0},x_datum=0,"
                    "y_datum=0,delete=no,fill_dx=2.54,fill_dy=2.54,"
                    "attach_atr=no,retain_atr=no".format(obj.symbol+"-ls-"+worklayer.split("-ls")[0]))
                    
                    step.clearAll()
                    step.affect(worklayer)
                    step.resetFilter()
                    step.selectSymbol(obj.symbol, 1, 1)
                    if step.featureSelected():
                        step.changeSymbol(obj.symbol+"-ls-"+worklayer.split("-ls")[0])
    
    def replace_normal_layer_by_linshi_layer(self, select_layers):
        """将临时资料转正式层"""
        time_form = time.strftime('%y%m%d.%H%M', time.localtime(time.time()))
        for layer in select_layers:
            normal_layer = layer.split("-ls")[0]
            job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(job.name, normal_layer))
            job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(job.name, layer))
            
            job.COM("matrix_rename_layer,job={0},matrix=matrix,layer={1},new_name={2}".format(job.name, normal_layer, normal_layer+"-old-"+time_form))
            job.COM("matrix_rename_layer,job={0},matrix=matrix,layer={1},new_name={2}".format(job.name, layer, normal_layer))
            job.COM("matrix_refresh,job={0},matrix=matrix".format(job.name))
                    
    def restore_original_linshi_layer(self, select_layers):
        """还原临时层为正式层"""
        matrixInfo = job.matrix.getInfo()
        linshi_layers = []
        error_log = []
        exists_normal_layers = {}
        for layer in select_layers:
            linshi_layers.append(layer)
            normal_layer = layer.split("-ls")[0]
            if normal_layer not in matrixInfo["gROWname"]:
                log = u"检测到临时层{0} 对应的正常层{1}不存在，请检查资料是否被手动修改！！"
                error_log.append(log.format(layer, normal_layer))
            
            if not exists_normal_layers.has_key(normal_layer):                
                exists_normal_layers[normal_layer] = [layer]
            else:
                exists_normal_layers[normal_layer].append(layer)
        
        if "restore_linshi_layer" in sys.argv[1:]:
            for key, value in exists_normal_layers.iteritems():
                if len(value) > 1:
                    showMessageInfo(u"检测到{0}层同时恢复了两个临时层{1}的board属性，检查是否选择有误！！".format(
                        key, value
                    ))
                    return
            
            board_linshi_layers = []
            for i, layer in enumerate(matrixInfo["gROWname"]):
                if matrixInfo["gROWcontext"][i] == "board":
                    if "-ls" in layer:
                        board_linshi_layers.append(layer)
                        
                    if "-ls" in layer and layer.split("-ls")[0] in exists_normal_layers.keys():
                        showMessageInfo(u"检测到{0}层同时恢复了两个临时层{1}的board属性，请检查是否选择有误！！".format(
                            layer.split("-ls")[0], [layer, exists_normal_layers[layer.split("-ls")[0]][0]]
                        ))
                        return
                        
            same_time_layers = [x.split("-ls")[1] for x in linshi_layers]
            if len(set(same_time_layers)) != 1:
                showMessageInfo(u"检测到有多个不同时间的临时后缀层被选中{0}，请检查是否选择有误！！".format(
                    list(set(same_time_layers))
                ))
                return
                
            same_time_layers = [x.split("-ls")[1] for x in linshi_layers + board_linshi_layers]
            if len(set(same_time_layers)) != 1:
                showMessageInfo(u"检测到选中的层跟系统已加board属性的临时层<br>有多个不同时间的临时后缀{0}，请检查是否选择有误！！".format(
                    list(set(same_time_layers))
                ))
                return           

        if linshi_layers:
            if error_log:
                showMessageInfo(*error_log)
                exit(0)
            
            dic_drill_start_end = self.get_drill_start_end_layers()
            
            if "restore_normal_layer" in sys.argv[1:]:                
                for layer in linshi_layers:
                    job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(job.name, layer))
                    normal_layer = layer.split("-ls")[0]
                    job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(job.name, normal_layer))
                    
                    for key, value in dic_drill_start_end.iteritems():
                        if value["start"] == layer:
                            value["start"] = normal_layer
                        if value["end"] == layer:
                            value["end"] = normal_layer                    
                    
                new_dic_drill_start_end = self.get_drill_start_end_layers()
                
                for key, value in dic_drill_start_end.iteritems():
                    if value["start"] and value["end"]:
                        
                        for new_key in [key, key.split("-ls")[0]]:
                            if not new_dic_drill_start_end.has_key(new_key):
                                continue
                            
                            if new_dic_drill_start_end[new_key]["start"] == value["start"] and \
                               new_dic_drill_start_end[new_key]["end"] == value["end"]:
                                continue
                            
                            job.COM("matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(
                                job.name, new_key, value["start"],
                                value["end"]
                            ))                      
            else:
                for layer in linshi_layers:
                    job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(job.name, normal_layer))
                    normal_layer = layer.split("-ls")[0]
                    job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(job.name, layer))
                    
                    for key, value in dic_drill_start_end.iteritems():
                        if value["start"] == normal_layer:
                            value["start"] = layer
                        if value["end"] == normal_layer:
                            value["end"] = layer                    
                    
                new_dic_drill_start_end = self.get_drill_start_end_layers()
                for key, value in new_dic_drill_start_end.iteritems():
                    if value["start"] and value["end"]:
                        for new_key in [key, key.split("-ls")[0]]:
                            if not dic_drill_start_end.has_key(new_key):
                                continue
                            
                            if dic_drill_start_end[new_key]["start"] == value["start"] and \
                               dic_drill_start_end[new_key]["end"] == value["end"]:
                                continue
                            
                            job.COM("matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(
                                job.name, key, dic_drill_start_end[new_key]["start"],
                                dic_drill_start_end[new_key]["end"]
                            ))                     
            
            showMessageInfo(u"修改完成，请检查！")
        else:
            showMessageInfo(u"未发现需要还原的临时层，请检查！")
            
    def getJOB_LockInfo(self, dataType='locked_info'):
        """
        从数据库中获取料号的锁记录
        :param dataType: 获取的数据类型（status:locked_info log:locked_log）
        :return:dict
        """
            
        lockData = self.getDATA.getLock_Info(job.name.split("-")[0])

        try:
            return json.loads(lockData[dataType], encoding='utf8')
        except:
            # print u'传入的数据参数异常'
            return {}

    def getChangeDetial(self):
        """
        获取修改的明细
        :return:
        """
        # --从数据库中获取lock记录 获取不到在从文件内获取 20230904 by lyh
        self.pre_lock = self.getJOB_LockInfo(dataType='locked_info')
            
        if not self.pre_lock:              
            self.pre_lock = self.read_file()
            
        warn_mess=[]
        for lock_step in self.pre_lock:
            for lock_layer in self.pre_lock[lock_step]:
                if lock_layer in self.layer_list:
                    warn_mess.append(u'层别被锁定：%s' % (lock_layer)) 

        return list(set(warn_mess))
    
    def read_file(self):
        """
        用json从user文件夹中的job_lock.json中读取字典
        :return:
        :rtype:
        """
        json_dict = {}
        stat_file = os.path.join(self.userDir, self.job_lock)
        if os.path.exists(stat_file):
            fd = open(stat_file, 'r')
            json_dict = json.load(fd)
            fd.close()
        return json_dict
                    
        
    def setMainUIstyle(self):  # 设置风格
        file = QtCore.QFile(':/pic/fblue.qss')
        file.open(QtCore.QFile.ReadOnly)
        styleSheet = file.readAll()
        styleSheet = unicode(styleSheet, encoding='gb2312')
        QtGui.qApp.setStyleSheet(styleSheet)

if __name__ == "__main__":
    main_widget = auto_copy_layer()
    main_widget.show()    
    sys.exit(app.exec_())

