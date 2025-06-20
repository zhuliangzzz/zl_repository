#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__    = "20221124"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""添加panel拼版序列号 """

import os
import sys
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
    
import pic
import re
if os.environ.get("JOB"):
    import gClasses
    from genesisPackages_zl import get_panelset_sr_step, \
         job, matrixInfo, get_profile_limits, top, \
         get_layer_selected_limits, silkscreenLayers, \
         get_sr_area_flatten, solderMaskLayers, \
         outsignalLayers, lay_num
    
from create_ui_model import app, showQuestionMessageInfo, \
     showMessageInfo
from scriptsRunRecordLog import uploadinglog

from PyQt4 import QtCore, QtGui, Qt

class add_number(QtGui.QWidget):
    
    def __init__(self, parent = None):
        super(add_number,self).__init__(parent)
        self.resize(600, 500)
        self.setWindowFlags(Qt.Qt.Window | Qt.Qt.WindowStaysOnTopHint)
        
        self.set_ui()        
        
    def set_ui(self):
        self.setObjectName("mainWindow")
        self.titlelabel = QtGui.QLabel(u"添加拼版序列号")
        self.titlelabel.setStyleSheet("QLabel {color:red}")
        self.setGeometry(700, 300, 0, 0)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.titlelabel.setFont(font)        

        self.dic_editor = {}
        self.dic_label = {}

        arraylist1 = [{u"序号类型": "QComboBox"},
                      {u"添加step": "QComboBox"},
                      {u"添加层别": "QComboBox"},
                      {u"添加序号类型": "QComboBox"},
                      {u"panel序号位置": "QComboBox"},
                      {u"字高(mil)": "QLineEdit"},
                      {u"字宽(mil)": "QLineEdit"},
                      {u"线宽(mil)": "QLineEdit"},
                      {u"是否镜像": "QComboBox"},
                      {u"添加角度": "QComboBox"},]

        group_box_font = QtGui.QFont()
        group_box_font.setBold(True)    
        widget1 = self.set_widget(group_box_font,
                                  arraylist1,
                                   u"基本信息确认",
                                   "")

        self.pushButton = QtGui.QPushButton()
        self.pushButton1 = QtGui.QPushButton()
        self.pushButton.setText(u"运行")
        self.pushButton1.setText(u"退出")
        self.pushButton.setFixedWidth(100)
        self.pushButton1.setFixedWidth(100)
        btngroup_layout = QtGui.QGridLayout()
        btngroup_layout.addWidget(self.pushButton,0,0,1,1) 
        btngroup_layout.addWidget(self.pushButton1,0,1,1,1)
        btngroup_layout.setSpacing(5)
        btngroup_layout.setContentsMargins(5, 5,5, 5)
        btngroup_layout.setAlignment(QtCore.Qt.AlignTop)          

        main_layout =  QtGui.QGridLayout()
        main_layout.addWidget(self.titlelabel,0,0,1,1,QtCore.Qt.AlignCenter)
        main_layout.addWidget(widget1, 1, 0, 1, 1, QtCore.Qt.AlignCenter)
        main_layout.addLayout(btngroup_layout, 8, 0,
                              1, 5, QtCore.Qt.AlignTop)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(main_layout)

        main_layout.setSizeConstraint(Qt.QLayout.SetFixedSize)

        self.pushButton.clicked.connect(self.show_set_order_ui)
        self.pushButton1.clicked.connect(sys.exit)

        self.setWindowTitle(u"拼版序列号一键添加%s" % __version__)
        self.setMainUIstyle()
        
        self.initGenesisData()
        
    def initGenesisData(self):	

        for item in ["", "panel", "set"]:
            self.dic_editor[u"序号类型"].addItem(item)
            
        for item in matrixInfo["gCOLstep_name"]:
            if "edit" in item or "set" in item:                
                self.dic_editor[u"添加step"].addItem(item)            

        for item in [""] + silkscreenLayers + solderMaskLayers + outsignalLayers:
            self.dic_editor[u"添加层别"].addItem(item)
            
        for item in ["0", "90", "180", "270"]:
            self.dic_editor[u"添加角度"].addItem(item)
            
        for item in ["", "no", "yes"]:
            self.dic_editor[u"是否镜像"].addItem(item)       

        for item in ["","@","@@","@@@", "@_@","@@_@","@@@_@"]:
            self.dic_editor[u"添加序号类型"].addItem(item)
            
        for item in ["",u"在前面",u"在后面"]:
            self.dic_editor[u"panel序号位置"].addItem(item)            
            
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

        arraylist = [u"字高(mil)", u"字宽(mil)",u"线宽(mil)", u"添加角度"]	    

        for key in arraylist:
            if self.dic_item_value.has_key(key):
                try:
                    self.dic_item_value[key] = float(self.dic_item_value[key])
                except:
                    QtGui.QMessageBox.information(self, u'提示', u'检测到 %s 参数[ %s ]为空或非法数字,请检查~' % (
                        key, self.dic_item_value[key]), 1)
                    # self.show()
                    return 0
                
        if self.dic_item_value[u"添加step"] == "set" or self.dic_item_value[u"序号类型"] == "set":
            arraylist = [u"序号类型", u"添加层别", u"添加序号类型"]
        else:
            arraylist = [u"序号类型", u"添加层别", u"添加序号类型", u"panel序号位置"]
            if "set" not in matrixInfo["gCOLstep_name"]:
                arraylist = [u"序号类型", u"添加层别", u"添加序号类型"]
                
        for key in arraylist:            
            if self.dic_item_value[key] == "":
                QtGui.QMessageBox.information(self, u'提示', u'检测到 {0} 为空,请检查~'.format(key), 1)            
                return 0                

        return 1
        
    def show_set_order_ui(self):
        
        res = self.get_item_value()
        if not res:
            return
        
        self.hide()
        layer = str(self.dic_item_value[u"添加层别"])
        x_size = self.dic_item_value[u"字宽(mil)"] * 25.4 / 1000
        y_size = self.dic_item_value[u"字高(mil)"] * 25.4 / 1000
        w_factor = self.dic_item_value[u"线宽(mil)"] / 3 * 0.25
        angle = self.dic_item_value[u"添加角度"]
        pnl_or_set_format = str(self.dic_item_value[u"添加序号类型"])
        pnl_order_position = self.dic_item_value[u"panel序号位置"]
        
        if self.dic_item_value[u"序号类型"] == "panel":
            if pnl_order_position == u"在前面":                
                pnl_format = len(pnl_or_set_format.split("_")[0])
                set_format = len(pnl_or_set_format.split("_")[1])
            elif pnl_order_position == u"在后面":
                pnl_format = len(pnl_or_set_format.split("_")[1])
                set_format = len(pnl_or_set_format.split("_")[0])
            else:
                pnl_format = len(pnl_or_set_format)    
                set_format = 0
        else:
            pnl_format = 0
            set_format = len(pnl_or_set_format)
            
        pcs_stepname = self.dic_item_value[u"添加step"]
        mirror = self.dic_item_value[u"是否镜像"]
        
        self.editAddText(layer, x_size, y_size, w_factor, angle,
                         pnl_format, set_format, self.dic_item_value[u"序号类型"],
                         pcs_stepname, pnl_order_position, mirror)        
        
        if self.dic_item_value[u"序号类型"] == "panel":
            if pcs_stepname == "set":
                array_steps = ["panel",pcs_stepname]
            else:
                array_steps = ["set", "panel", pcs_stepname]
                if "set" not in matrixInfo["gCOLstep_name"]:
                    array_steps = ["panel",pcs_stepname]
        else:
            array_steps = ["set", pcs_stepname]
        
        for stepname in array_steps:            
            if stepname in matrixInfo["gCOLstep_name"]:
                all_steps = get_panelset_sr_step(job.name, 'panel')
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")
                step.clearAll()
                step.affect(layer)
                step.resetFilter()
                step.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=panel')
                step.selectAll()
                
                if stepname != pcs_stepname:
                    step.resetFilter()
                    step.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=set-dot')
                    step.selectAll()
                    
                step.resetFilter()
                step.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=set')
                step.selectAll()
                if step.featureSelected():
                    if stepname in ["set", "panel"] and stepname != array_steps[-1]:
                        res = showQuestionMessageInfo(u"检测到{0}存在已添加的序号，是否删除，重新添加？".format(stepname),
                                                      start_btn_text=u"删除重新添加", start_btn_size=100,
                                                      end_btn_text=u"不处理，直接继续",end_btn_size=120)
                        if res:
                            step.selectDelete()
                    else:                            
                        step.selectDelete()
                    
                if stepname == pcs_stepname:
                    step.clearAll()
                    QtGui.QMessageBox.information(self, u'提示', u'添加完成,请检查序号！', 1)
                    try:
                        user = top.getUser()
                        uploadinglog(__credits__, __version__, os.environ.get("STEP", ""), GEN_USER=user)
                    except Exception, e:
                        print e                     
                    sys.exit()
                
                step.removeLayer("draw_set_profile")
                step.removeLayer("draw_set_profile_tmp")
                step.COM("profile_to_rout,layer=draw_set_profile,width=10")
                
                for name in all_steps:
                    step = gClasses.Step(job, name)
                    step.open()
                    step.COM("profile_to_rout,layer=draw_set_profile,width=10")
                
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")
                step.flatten_layer("draw_set_profile", "draw_set_profile_tmp")
                step.clearAll()
                step.affect("draw_set_profile_tmp")
                step.COM("arc2lines,arc_line_tol=10")
                xmin, ymin, xmax, ymax = get_profile_limits(step)
                layer_cmd = gClasses.Layer(step, "draw_set_profile_tmp")
                feat_out = layer_cmd.featOut(units="mm")["lines"]
                x_resize = 700 / (xmax-xmin)
                y_resize = 700 / (ymax-ymin)
                
                xmin = xmin - 5
                ymax = ymax + 5
                
                arraylist_profile = [((obj.xs- xmin) * x_resize , (obj.ys -ymax) * y_resize ,
                                      (obj.xe -xmin) * x_resize, (obj.ye -ymax) * y_resize) for obj in feat_out]                
                
                step.flatten_layer(layer, layer+"_set_text")
                step.clearAll()
                step.affect(layer+"_set_text")
                step.resetFilter()
                step.setAttrFilter(".string,text={0}".format(stepname))
                step.selectAll()
                step.COM("sel_reverse")
                if step.featureSelected():
                    step.selectDelete()
                    
                step.resetFilter()
                step.refSelectFilter(layer, mode="cover", f_types="text", polarity="positive")
                if step.featureSelected():
                    step.selectDelete()
                
                if stepname == "set":
                    step.removeLayer(layer+"_set_text_tmp")
                    if pnl_order_position == u"在后面":                        
                        step.resetFilter()
                        step.filter_set(feat_types='text', polarity='positive')
                        step.COM("filter_set,filter_name=popup,update_popup=no,feat_types=text,text=6")
                        step.selectAll()
                        if step.featureSelected():
                            step.moveSel(layer+"_set_text_tmp")
                            
                    layer_cmd = gClasses.Layer(step, layer+"_set_text")
                    feat_out = layer_cmd.featout_dic_Index(units="mm")["text"]
                    get_sr_area_flatten("surface_fill", stepname=stepname, get_sr_step=True)
                    arraylist_text_info = []                    
                    for obj in feat_out:
                        step.clearAll()
                        step.affect(layer+"_set_text")
                        step.selectFeatureIndex(layer+"_set_text", obj.feat_index)
                        if step.featureSelected():
                            step.removeLayer("text_tmp")
                            step.copySel("text_tmp")
                            step.clearAll()
                            if step.isLayer("surface_fill"):
                                step.affect("surface_fill")
                                step.resetFilter()
                                step.refSelectFilter("text_tmp")
                                if step.featureSelected():
                                    sel_xmin, sel_ymin, sel_xmax, sel_ymax = get_layer_selected_limits(step, "surface_fill")
                                    arraylist_text_info.append((obj.feat_index,round(((sel_xmin+sel_xmax) *0.5-xmin) *x_resize, 0), round(((sel_ymin+sel_ymax) *0.5-ymax) *y_resize, 0),))
             
                    if not arraylist_text_info:
                        arraylist_text_info = [(obj.feat_index, (obj.x -xmin) * x_resize, (obj.y -ymax) * y_resize) for obj in feat_out]
                        
                else:
                    STR='-t step -e %s/%s -d REPEAT,units=mm' %(job.name,'panel')
                    gREPEAT_info = step.DO_INFO(STR)
                    gREPEATstep=gREPEAT_info['gREPEATstep']
                    gREPEATxmax=gREPEAT_info['gREPEATxmax']
                    gREPEATymax=gREPEAT_info['gREPEATymax']
                    gREPEATxmin=gREPEAT_info['gREPEATxmin']      
                    gREPEATymin=gREPEAT_info['gREPEATymin']                
                    self.dic_rect = {}
                    arraylist_text_info = []
                    for i in xrange(len(gREPEATstep)):
                        if re.match(r'^set|^edit',gREPEATstep[i]):
                            xs = gREPEATxmin[i]
                            ys = gREPEATymin[i]
                            xe = gREPEATxmax[i]
                            ye = gREPEATymax[i]
                            step.selectNone()
                            step.filter_set(feat_types='text', polarity='positive')
                            step.selectRectangle(xs, ys, xe, ye)
                            layer_cmd = gClasses.Layer(step, layer+"_set_text")
                            feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["text"]
                            indexes = [(obj.feat_index, obj.text.replace("'", "")) for obj in feat_out]
                            arraylist_text_info.append((tuple(indexes), round(((xs+xe) *0.5-xmin) *x_resize, 0), round(((ys+ye) *0.5-ymax) *y_resize, 0)))
                
                self.dic_order = {}
                set_ui = show_set_pnl_order(self, arraylist_profile=arraylist_profile,
                                            w_size=(xmax-xmin) *x_resize+150,
                                            h_size=(ymax-ymin) *y_resize+50,
                                            text_info=arraylist_text_info,
                                            title_name=u"请确认{0}序号".format(stepname))
                set_ui.exec_()
                
                step.clearAll()
                step.affect(layer+"_set_text")
                for indexes, text in self.dic_order.iteritems():
                    step.selectNone()
                    if isinstance(indexes, str):
                        # set序号
                        step.selectFeatureIndex(layer+"_set_text", indexes)                            
                        if pnl_order_position == u"在后面":
                            if set_format == 1:
                                if (re.match("\d+", text) and float(text) < 10) or \
                                   re.match("[A-Z]", text):
                                    step.selectFeatureIndex(layer+"_set_text", indexes)
                                    if step.isLayer(layer+"_set_text_tmp"):                                        
                                        if step.featureSelected():
                                            step.removeLayer("text_tmp")
                                            step.moveSel("text_tmp")
                                            step.clearAll()
                                            step.resetFilter()
                                            step.affect(layer+"_set_text_tmp")
                                            step.refSelectFilter("text_tmp")
                                            if step.featureSelected():
                                                step.moveSel(layer+"_set_text")
                                            step.clearAll()
                                            step.affect(layer+"_set_text")
                                            step.refSelectFilter("text_tmp")
                                else:
                                    step.selectFeatureIndex(layer+"_set_text", indexes)
                            else:
                                step.selectFeatureIndex(layer+"_set_text", indexes)
                                
                    if isinstance(indexes, tuple):
                        # panel序号
                        find_indexes = []
                        for index,sel_text in indexes:
                            # step.PAUSE(str([text, sel_text]))
                            if pnl_format == 1 and pnl_order_position == u"在前面":
                                if (re.match("\d+", text) and float(text) < 10) or \
                                   re.match("[A-Z]", text):
                                    if sel_text == "66":
                                        step.selectFeatureIndex(layer+"_set_text", index)
                                        if step.featureSelected():
                                            step.selectDelete()
                                        continue
                                else:
                                    if sel_text == "6":
                                        step.selectFeatureIndex(layer+"_set_text", index)
                                        if step.featureSelected():
                                            step.selectDelete()                                        
                                        continue
                                    
                            find_indexes.append(index)
                                
                        for index in find_indexes:                            
                            step.selectFeatureIndex(layer+"_set_text", index)
                            
                    if step.featureSelected():
                        
                        format_num = 0
                        if stepname == "set":
                            if set_format > 1:
                                format_num = set_format
                        else:
                            if pnl_format > 1:
                                format_num = pnl_format
                                
                        if re.match("[A-Z]", str(text)):
                            add_text = str(text)
                        else:
                            add_text = str(text).rjust(format_num, "0")
                            
                        step.COM("sel_change_txt,text={0},x_size=-1,y_size=-1,w_factor=-1,polarity=no_change,mirror=no_change,fontname=".format(add_text))
                
                step.copyToLayer(layer)
                step.clearAll()
                step.removeLayer("text_tmp")
                step.removeLayer(layer+"_set_text")
                step.removeLayer(layer+"_set_text_tmp")
                step.removeLayer("surface_fill")
                step.removeLayer("draw_set_profile")
                step.removeLayer("draw_set_profile_tmp")
                
    def editAddText(self, layer, x_size, y_size, w_factor,
                    angle, pnl_format, set_format, order_type,
                    stepname, pnl_order_position, mirror):

        edit= gClasses.Step(job, stepname) 
        edit.open()
        edit.clearAll()
        edit.display(layer)
        edit.COM("zoom_home")
        edit.COM("units,type=mm")
        edit.COM("negative_data,mode=dim")
        
        edit.resetFilter()
        edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=panel')
        edit.selectAll()
        edit.resetFilter()
        edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=set-dot')
        edit.selectAll()
        edit.resetFilter()
        edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=set')
        edit.selectAll()
        edit.removeLayer(layer+"_exists_order")
        if edit.featureSelected():
            
            res = showQuestionMessageInfo(u"检测到{0}存在已添加的序号，是否删除，重新添加？".format(stepname),
                                          start_btn_text=u"删除重新添加", start_btn_size=100,
                                          end_btn_text=u"不处理，直接继续",end_btn_size=120)
            if res:
                edit.selectDelete()
            else:                
                edit.moveSel(layer+"_exists_order")
            
        STR = u"请选择添加的位置"

        if sys.platform == "win32":
            top.MOUSE('select a point to add Text')
        else:
            top.MOUSE(STR.encode("utf8"))

        mouse_xy = top.MOUSEANS
        mouse_x=float(mouse_xy.split()[0])
        mouse_y=float(mouse_xy.split()[1])
        edit.COM('cur_atr_reset')
        
        if order_type == "panel" and stepname != "set":
            if "set" in matrixInfo["gCOLstep_name"]:
                """存在set的情况"""
                if pnl_order_position == u"在前面":
                    edit.COM('cur_atr_set,attribute=.string,text=panel')
                else:
                    edit.COM('cur_atr_set,attribute=.string,text=set')
                edit.addText(mouse_x,mouse_y,'66'if pnl_format <3 else "6"*pnl_format,x_size, y_size, w_factor,
                             polarity = 'positive', attributes = 'yes', fontname= "simple")
                edit.COM('cur_atr_set,attribute=.string,text=set-dot')
                edit.addText(mouse_x+x_size*2 if pnl_format <3 else mouse_x+x_size*pnl_format,mouse_y,'-',x_size, y_size, w_factor,
                             polarity = 'positive', attributes = 'yes', fontname= "simple")
                if pnl_order_position == u"在前面":
                    edit.COM('cur_atr_set,attribute=.string,text=set')
                else:
                    edit.COM('cur_atr_set,attribute=.string,text=panel')
                edit.addText(mouse_x+x_size*3 if pnl_format <3 else mouse_x+x_size*(pnl_format+1),mouse_y,'66' if set_format <3 else "6"*set_format,x_size, y_size, w_factor,
                             polarity = 'positive', attributes = 'yes', fontname= "simple")
            else:
                """不存在set"""
                edit.COM('cur_atr_set,attribute=.string,text=panel')
                edit.addText(mouse_x,mouse_y,'66' if set_format <3 else "6"*set_format,x_size, y_size, w_factor,
                             polarity = 'positive', attributes = 'yes', fontname= "simple")                
        else:
            if stepname == "set":
                edit.COM('cur_atr_set,attribute=.string,text=panel')
            else:                
                edit.COM('cur_atr_set,attribute=.string,text=set')
            edit.addText(mouse_x,mouse_y,'66' if set_format <3 else "6"*set_format,x_size, y_size, w_factor,
                         polarity = 'positive', attributes = 'yes', fontname= "simple")
            
        if angle != 0:
            edit.resetFilter()
            edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=panel')
            edit.selectAll()
            edit.resetFilter()
            edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=set-dot')
            edit.selectAll()
            edit.resetFilter()
            edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=set')
            edit.selectAll()
            if edit.featureSelected():
                edit.COM("sel_transform,oper=rotate,x_anchor={0},y_anchor={1},angle={2},"
                         "x_scale=1,y_scale=1,x_offset=0,"
                         "y_offset=0,mode=anchor,duplicate=no".format(mouse_x, mouse_y, angle))            
        
        if mirror == "yes":
            edit.resetFilter()
            edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=panel')
            edit.selectAll()
            edit.resetFilter()
            edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=set-dot')
            edit.selectAll()
            edit.resetFilter()
            edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=set')
            edit.selectAll()
            if edit.featureSelected():
                xmin, ymin, xmax, ymax = get_layer_selected_limits(edit, layer)
                edit.COM("sel_transform,oper=mirror,x_anchor={0},y_anchor={1},angle=0,"
                         "x_scale=1,y_scale=1,x_offset=0,"
                         "y_offset=0,mode=anchor,duplicate=no".format((xmin+xmax) *0.5, (ymin+ymax) *0.5))
            
        edit.resetFilter()
        top.PAUSE('please check the Text....')
    
        edit.selectNone()
        
        attr_text = ""
        if pnl_format == 1 and pnl_order_position == u"在前面":
            attr_text = "panel"
        if set_format == 1 and pnl_order_position == u"在后面":
            attr_text = "set"
            
        if attr_text:            
            edit.resetFilter()
            edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text={0}'.format(attr_text))
            edit.selectAll()
            edit.COM("units,type=mm")
            
        if edit.featureSelected() > 0:
            STR='-t layer -e %s/%s/%s -d FEATURES -o select,units=mm' %(job.name, stepname,layer)
            info = edit.INFO(STR)		
            text_obj = edit.parseFeatureInfo(info)['text']

            txt_xy = [(obj.x, obj.y) for obj in text_obj]

            txt_xsize = text_obj[0].xsize
            txt_ysize = text_obj[0].ysize
            txt_wfactor = text_obj[0].wfactor
            txt_font = text_obj[0].font
            rotation = text_obj[0].rotation
            mirror_type = text_obj[0].mirror
            
            if mirror_type == "yes":

                new_x = txt_xy[0][0]-txt_xsize
                new_y = txt_xy[0][1]
                
                if rotation == 180:
                    new_x = txt_xy[0][0] + txt_xsize
                    new_y = txt_xy[0][1]                    

                if rotation == 90:			    
                    new_x = txt_xy[0][0]
                    new_y = txt_xy[0][1] - txt_ysize
                    
                if rotation == 270:			    
                    new_x = txt_xy[0][0]
                    new_y = txt_xy[0][1] + txt_ysize                

                edit.COM('cur_atr_set,attribute=.string,text={0}'.format(attr_text))
                edit.addText(new_x,new_y,'6',
                             txt_xsize,txt_ysize,txt_wfactor,mirror = mirror_type,
                             polarity = 'positive', attributes = 'yes',
                             angle= rotation, 
                             fontname= txt_font)
            else:
                new_x = txt_xy[0][0] + txt_xsize
                new_y = txt_xy[0][1]
                
                if rotation == 180:
                    new_x = txt_xy[0][0] - txt_xsize
                    new_y = txt_xy[0][1]                    

                if rotation == 90:			    
                    new_x = txt_xy[0][0]
                    new_y = txt_xy[0][1] - txt_ysize
                    
                if rotation == 270:			    
                    new_x = txt_xy[0][0]
                    new_y = txt_xy[0][1] + txt_ysize  
                    
                edit.COM('cur_atr_set,attribute=.string,text={0}'.format(attr_text))
                edit.addText(new_x,new_y,'6',
                             txt_xsize,txt_ysize,txt_wfactor,mirror =mirror_type,
                             polarity = 'positive', attributes = 'yes',
                             angle= rotation, 
                             fontname= txt_font)			
        # edit.PAUSE(str(text_obj))
        if edit.isLayer(layer+"_exists_order"):
            edit.clearAll()
            edit.affect(layer+"_exists_order")
            edit.copySel(layer)
            edit.removeLayer(layer+"_exists_order")
            
        edit.close()

    def set_widget(self, font, arraylist, title, checkbox):
        groupbox = QtGui.QGroupBox()
        groupbox.setTitle(title)
        groupbox.setStyleSheet("QGroupBox:title{color:green}")
        groupbox.setFont(font)	
        gridlayout = self.get_layout(arraylist, checkbox)
        groupbox.setLayout(gridlayout)
        return groupbox
    
    def change_order_type(self, index):
        self.dic_editor[u"panel序号位置"].show()
        self.dic_label[u"panel序号位置"].show()
        
        self.dic_editor[u"添加序号类型"].clear()
        self.dic_editor[u"添加step"].setEnabled(True)
        if index == 1:
            for item in ["", "@_@","@@_@","@_@@","@@_@@","@@@_@"]:
                self.dic_editor[u"添加序号类型"].addItem(item)
                
            if "set" not in matrixInfo["gCOLstep_name"]:
                self.dic_editor[u"添加序号类型"].clear()
                self.dic_editor[u"panel序号位置"].hide()
                self.dic_label[u"panel序号位置"].hide()            
                for item in ["","@","@@","@@@"]:
                    self.dic_editor[u"添加序号类型"].addItem(item)                
                    
        if index == 2:
            self.dic_editor[u"panel序号位置"].hide()
            self.dic_label[u"panel序号位置"].hide()            
            for item in ["","@","@@","@@@"]:
                self.dic_editor[u"添加序号类型"].addItem(item)
            
            self.dic_editor[u"添加step"].setEnabled(False)        
                
    def change_order_type_set(self):
        self.dic_editor[u"panel序号位置"].show()
        self.dic_label[u"panel序号位置"].show()        
        if self.dic_editor[u"序号类型"].currentText() == "panel":
            self.dic_editor[u"添加序号类型"].clear()
            if self.sender().currentText() == "set":
                self.dic_editor[u"panel序号位置"].setCurrentIndex(0)
                self.dic_editor[u"panel序号位置"].hide()
                self.dic_label[u"panel序号位置"].hide()
                for item in ["","@","@@","@@@"]:
                    self.dic_editor[u"添加序号类型"].addItem(item)
            else:
                for item in ["", "@_@","@@_@","@_@@","@@_@@","@@@_@"]:
                    self.dic_editor[u"添加序号类型"].addItem(item)
                    
    def change_text_mirror(self):
        """
        单面文字C面cc1
        单面文字S面cc2
        单面文字C面一次文字cc1-1
        单面文字S面一次文字cc2-1
        单面文字C面二次文字cc1-2
        单面文字S面二次文字cc2-2
        双面文字c面c1
        双面文字s面c2
        双面二次文字C面一次文字c1-1
        双面二次文字S面一次文字c2-1
        双面二次文字C面二次文字c1-2
        双面二次文字s面二次文字c2-2"""
        if str(self.sender().currentText()) in ["m2", "l{0}".format(lay_num)] or "c2" in str(self.sender().currentText()):
            self.dic_editor[u"是否镜像"].setCurrentIndex(2)
        else:
            self.dic_editor[u"是否镜像"].setCurrentIndex(1)

    def get_layout(self, arraylist, checkbox):
        gridlayout = QtGui.QGridLayout()
        for i, name in enumerate(arraylist):
            for key, value in name.iteritems():
                self.dic_label[key] = QtGui.QLabel()
                self.dic_label[key].setText(key)
                self.dic_editor[key] = getattr(QtGui, value)()
                
                if key == u"序号类型":
                    self.dic_editor[key].currentIndexChanged.connect(self.change_order_type)
                    
                if key == u"添加step":
                    self.dic_editor[key].currentIndexChanged.connect(self.change_order_type_set)
                    
                if key == u"添加层别":
                    self.dic_editor[key].currentIndexChanged.connect(self.change_text_mirror)                    
                    
                col = 2 if i % 2 else 0
                row = -1 if col else 0
                gridlayout.addWidget(self.dic_label[key], i + 1 + row, 1 + col, 1, 1)
                gridlayout.addWidget(self.dic_editor[key], i + 1 + row, 2 + col, 1, 1)

        gridlayout.setSpacing(5)
        gridlayout.setContentsMargins(5, 5,5, 5)
        gridlayout.setAlignment(QtCore.Qt.AlignTop)

        return gridlayout    
        
    def setMainUIstyle(self):#设置风格
        file = QtCore.QFile(':/pic/fblue.qss')
        file.open(QtCore.QFile.ReadOnly)
        styleSheet = file.readAll()
        styleSheet = unicode(styleSheet, encoding='gb2312')
        QtGui.qApp.setStyleSheet(styleSheet)
        
class show_set_pnl_order(QtGui.QDialog):
    """"""

    def __init__(self, parent = None, *args, **kwargs):
        """Constructor"""
        super(show_set_pnl_order,self).__init__(parent)
        self.setObjectName("mainWindow")
        self.width, self.height = kwargs["w_size"], kwargs["h_size"]
        self.resize(self.width, self.height)
        self.setWindowFlags(Qt.Qt.Window | Qt.Qt.WindowStaysOnTopHint)        
        
        self.dic_label = {}
        self.dic_ObjectName = {}
        self.dic_combox = {}
        self.parent = parent
        
        self.profile = kwargs["arraylist_profile"]
        self.arraylist_text_info = kwargs["text_info"]
        self.setMainUIstyle()
        self.setWindowTitle(kwargs["title_name"])
        self.set_ui_widget()
        
    def set_ui_widget(self):
        """设置控件"""
        self.l2r_btn = QtGui.QRadioButton(self)
        self.l2r_btn.setGeometry(QtCore.QRect(self.width-130, 40, 80, 40))
        self.l2r_btn.setText(u"从左到右")
        self.l2r_btn.setChecked(True)
        
        self.u2d_btn = QtGui.QRadioButton(self)
        self.u2d_btn.setGeometry(QtCore.QRect(self.width-130, 90, 80, 40))
        self.u2d_btn.setText(u"从上到下")
        
        # self.upper_calc_position_btn = QtGui.QCheckBox(u"坐上角开始算")
        self.upper_calc_position_btn = QtGui.QCheckBox(self)
        self.upper_calc_position_btn.setGeometry(QtCore.QRect(self.width-130, 140, 140, 40))
        self.upper_calc_position_btn.setText(u"左上角开始算")
        self.upper_calc_position_btn.setChecked(True)
        
        # self.down_calc_position_btn = QtGui.QCheckBox(u"坐下角开始算")
        self.down_calc_position_btn = QtGui.QCheckBox(self)
        self.down_calc_position_btn.setGeometry(QtCore.QRect(self.width-130, 190, 140, 40))
        self.down_calc_position_btn.setText(u"左下角开始算")        
        
        self.combine_row_btn = QtGui.QCheckBox(self)
        self.combine_row_btn.setGeometry(QtCore.QRect(self.width-130, 240, 120, 40))
        self.combine_row_btn.setText(u"相邻两行合并")
        
        self.combine_col_btn = QtGui.QCheckBox(self)
        self.combine_col_btn.setGeometry(QtCore.QRect(self.width-130, 290, 120, 40))
        self.combine_col_btn.setText(u"相邻两列合并")
        
        self.number_to_word_btn = QtGui.QCheckBox(self)
        self.number_to_word_btn.setGeometry(QtCore.QRect(self.width-130, 340, 120, 40))
        self.number_to_word_btn.setText(u"转换成字母")
        
        self.back_to_transition_btn = QtGui.QCheckBox(self)
        self.back_to_transition_btn.setGeometry(QtCore.QRect(self.width-130, 380, 120, 40))
        self.back_to_transition_btn.setText(u"回形路走法")
        
        self.conform_btn = QtGui.QPushButton(self)
        self.conform_btn.setGeometry(QtCore.QRect(self.width-130, 440, 80, 40))
        self.conform_btn.setText(u"确认序号")        
        
        self.l2r_btn.clicked.connect(self.change_text_order)
        self.u2d_btn.clicked.connect(self.change_text_order)
        self.upper_calc_position_btn.clicked.connect(self.change_text_order)
        self.down_calc_position_btn.clicked.connect(self.change_text_order)
        
        self.combine_row_btn.clicked.connect(self.change_text_order)
        self.combine_col_btn.clicked.connect(self.change_text_order)
        self.back_to_transition_btn.clicked.connect(self.change_text_order)
        self.conform_btn.clicked.connect(self.get_text_order)
        self.number_to_word_btn.clicked.connect(self.change_number_to_word)
        
        self.combine_row_btn.setEnabled(False)
        self.combine_col_btn.setEnabled(False)        
        
        dic_text_info = self.set_text_order("Y")
        
        i = 1
        for key in sorted(dic_text_info.keys(), key=lambda x: x * -1): 
            for index, x, y in dic_text_info[key]:
                self.dic_combox[index] = QtGui.QComboBox(self)
                self.dic_combox[index].setGeometry(QtCore.QRect(x, y*-1, 50, 30))
                # self.dic_combox[index].setObjectName("combox%s"%index)
                self.dic_combox[index].addItem("")
                for num in range(1, len(self.arraylist_text_info) + 1):
                    self.dic_combox[index].addItem(str(num))
                    
                pos = self.dic_combox[index].findText(str(i), QtCore.Qt.MatchExactly)
                self.dic_combox[index].setCurrentIndex(pos)
                
                i += 1
                
    def change_number_to_word(self):
        """数字转换成字母"""
        arraylist = "abcdefghijklmnopqrstuvwxyz"
        if len(self.dic_combox) > len(arraylist):
            # showMessageInfo(u"序号超过26个，不能进行字母转换")
            QtGui.QMessageBox.information(self, u"提示", u"序号超过26个，不能进行字母转换")
            self.sender().setChecked(False)
            return
        
        dic_zu_num_to_wor = {}
        dic_zu_wor_to_num = {}
        for i,word in enumerate(list(arraylist)):
            if i + 1 > len(self.dic_combox):
                break
            dic_zu_num_to_wor[str(i+1)] = word.upper()
            dic_zu_wor_to_num[word.upper()] = str(i + 1)
            
        if self.number_to_word_btn.isChecked():
            self.l2r_btn.setEnabled(False)
            self.u2d_btn.setEnabled(False)
            self.combine_row_btn.setEnabled(False)
            self.combine_col_btn.setEnabled(False)
            for key, editor in self.dic_combox.iteritems():
                number = str(editor.currentText())
                editor.clear()
                for key in sorted(dic_zu_num_to_wor.keys(), key=lambda x: int(x)):
                    editor.addItem(dic_zu_num_to_wor[key].upper())
                    
                pos = editor.findText(dic_zu_num_to_wor[number], QtCore.Qt.MatchExactly)
                editor.setCurrentIndex(pos)
        else:
            self.l2r_btn.setEnabled(True)
            self.u2d_btn.setEnabled(True)            
            for key, editor in self.dic_combox.iteritems():
                word = str(editor.currentText())
                editor.clear()
                for value in sorted(dic_zu_wor_to_num.values(), key=lambda x: int(x)):
                    editor.addItem(value)
                    
                pos = editor.findText(dic_zu_wor_to_num[word], QtCore.Qt.MatchExactly)
                editor.setCurrentIndex(pos)         
                
    def change_text_order(self):
        if self.sender() == self.upper_calc_position_btn:
            self.down_calc_position_btn.setChecked(False)
        if self.sender() == self.down_calc_position_btn:
            self.upper_calc_position_btn.setChecked(False)
            
        if self.l2r_btn.isChecked():            
            dic_text_info = self.set_text_order("Y")
            keys = sorted(dic_text_info.keys(), key=lambda x: x * -1)
            if self.down_calc_position_btn.isChecked():
                keys = sorted(dic_text_info.keys(), key=lambda x: x)
            self.combine_row_btn.setEnabled(True)
            self.combine_col_btn.setEnabled(False)
            self.combine_col_btn.setChecked(False)
            if self.combine_row_btn.isChecked():
                i = 0
                new_keys = []
                for key1, key2 in zip(keys, keys[1:]):
                    if i % 2:
                        i += 1
                        continue
                    
                    i += 1
                    dic_text_info[key1] += dic_text_info[key2]
                    new_keys.append(key1)
                    
                keys = sorted(new_keys, key=lambda x: x * -1)
                if self.down_calc_position_btn.isChecked():
                    keys = sorted(new_keys, key=lambda x: x)
                
            sort_index = 1
            flag = 1
        elif self.u2d_btn.isChecked():
            dic_text_info = self.set_text_order("X")
            keys = sorted(dic_text_info.keys(), key=lambda x: x)
            self.combine_row_btn.setEnabled(False)
            self.combine_row_btn.setChecked(False)
            self.combine_col_btn.setEnabled(True)            
            if self.combine_col_btn.isChecked():
                i = 0
                new_keys = []
                for key1, key2 in zip(keys, keys[1:]):
                    if i % 2:
                        i += 1
                        continue
                    
                    i += 1
                    dic_text_info[key1] += dic_text_info[key2]
                    new_keys.append(key1)
                    
                keys = sorted(new_keys, key=lambda x: x)
                
            sort_index = 2
            flag = -1
            if self.down_calc_position_btn.isChecked():
                flag = 1            
        else:            
            return 
            
        i = 1
        zu = 1
        for key in keys:
            if self.back_to_transition_btn.isChecked():
                if not zu % 2:
                    direction = -1
                else:
                    direction = 1
            else:
                direction = 1
            zu += 1
            for index, x, y in sorted(dic_text_info[key], key=lambda x: x[sort_index] *flag *direction ):
                    
                pos = self.dic_combox[index].findText(str(i), QtCore.Qt.MatchExactly)
                self.dic_combox[index].setCurrentIndex(pos)
                
                i += 1
                
    def get_text_order(self):        
        for key, editor in self.dic_combox.iteritems():
            self.parent.dic_order[key] = str(self.dic_combox[key].currentText())
            
        self.accept()
                
    def set_text_order(self, direct):        
        #按同一水平位置分组
        dic_zu = {}
        all_x = set([r[1] for r in self.arraylist_text_info])
        all_y = set([r[2] for r in self.arraylist_text_info])
        
        if direct == 'Y':
            for zu in all_y:
                dic_zu[zu] = []
                for index, x, y in self.arraylist_text_info:
                    if zu == y:
                        dic_zu[zu].append([index, x, y])
        else:
            for zu in all_x:
                dic_zu[zu] = []
                for index, x, y in self.arraylist_text_info:
                    if zu == x:
                        dic_zu[zu].append([index, x, y])
                        
        return dic_zu
        
    def paintEvent(self, event):# QPaintEvent *
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setPen(Qt.Qt.black)
        painter.scale(1, -1)
        for xs, ys, xe, ye in self.profile:            
            painter.drawPolyline(QtCore.QPointF(xs, ys),
                                  QtCore.QPointF(xe, ye))
        
        painter.end()
        
    def setMainUIstyle(self):#设置风格
        file = QtCore.QFile(':/pic/fblue.qss')
        file.open(QtCore.QFile.ReadOnly)
        styleSheet = file.readAll()
        styleSheet = unicode(styleSheet, encoding='gb2312')
        QtGui.qApp.setStyleSheet(styleSheet)    
        
        
if __name__ == '__main__':
    # app = QtGui.QApplication(sys.argv)	
    main_widget = add_number ()
    main_widget.show()
    sys.exit(app.exec_())	