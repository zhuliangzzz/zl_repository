#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20221229"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""防焊套印资料自动制作 """

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
import gClasses
import time
from genesisPackages import job, \
     solderMaskLayers, silkscreenLayers, \
     get_panelset_sr_step, matrixInfo, \
     get_layer_selected_limits, get_sr_area_for_step_include, \
     lay_num

from PyQt4 import QtCore, QtGui, Qt
from create_ui_model import showMessageInfo, showQuestionMessageInfo

ischange = job.DO_INFO('-t job -e %s -m script -d IS_CHANGED' % job.name)

if ischange['gIS_CHANGED'] == 'yes':
    showMessageInfo(u"请保存资料后再运行程序")
    sys.exit(0)

# 检测是否有创建临时层
zs_layers = [lay for lay in solderMaskLayers if lay in ['m1', 'm2']]
if zs_layers:
    showMessageInfo(u"资料中m1,m2层不能为board属性，请先使用程序创建m1和m2对应的临时层")
    sys.exit(0)
m1_ls = [lay for lay in solderMaskLayers if re.search('^m1-ls\d{6}\.\d{4}$', lay)]
m2_ls = [lay for lay in solderMaskLayers if re.search('^m2-ls\d{6}\.\d{4}$', lay)]


ls_layers = {}
if len(m1_ls) == 1 and len(m2_ls) == 1:
    ls_layers = {'m1' : m1_ls[0], 'm2' : m2_ls[0]}
    res = showQuestionMessageInfo(u"即将按临时层:{0} 制作返工资料，确认请继续？".format(';'.join(ls_layers.values())))
    if not res:
        sys.exit(0)
else:
    showMessageInfo(u"m1和m2对应board属性的临时层有且仅只能存在一层，请先把资料处理后再运行程序")
    sys.exit(0)


yftime = time.strftime("%Y%m%d", time.localtime(time.time()))
class auto_make_film(QtGui.QWidget):
    def __init__(self,parent = None):        
        super(auto_make_film,self).__init__(parent)
        self.resize(600, 500)
        self.setWindowFlags(Qt.Qt.Window | Qt.Qt.WindowStaysOnTopHint)

        self.setObjectName("mainWindow")
        self.titlelabel = QtGui.QLabel(u"阻焊套印制作")
        self.titlelabel.setStyleSheet("QLabel {color:red}")
        self.setGeometry(700, 300, 0, 0)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.titlelabel.setFont(font)        

        self.dic_editor = {}
        self.dic_label = {}

        arraylist1 = [{u"套印类型": "QComboBox"},
                      {u"文字是否制作": "QComboBox"},
                      {u"钻孔加大单边(mil)": "QLineEdit"},
                      {u"防焊加大单边(mil)": "QLineEdit"},
                      {u"文字加大单边(mil)": "QLineEdit"}, ]

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

        self.pushButton.clicked.connect(self.create_film)
        self.pushButton1.clicked.connect(sys.exit)

        self.setWindowTitle(u"防焊套印资料自动制作%s" % __version__)
        self.setMainUIstyle()
        self.initial_data()
        
    def initial_data(self):
        for item in [u"大板套印", u"set套印"]:
            self.dic_editor[u"套印类型"].addItem(item)
            
        for item in [u"", u"是", u"否"]:
            self.dic_editor[u"文字是否制作"].addItem(item)
            
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

        if not self.dic_item_value[u"文字是否制作"]:
            QtGui.QMessageBox.information(self, u'提示', u'检测到 %s 参数[ %s ]为空,请检查~' % (
                u"文字是否制作", self.dic_item_value[u"文字是否制作"]), 1)
            return 0
        
        if self.dic_item_value[u"文字是否制作"] == u"是":
            arraylist = [u"钻孔加大单边(mil)", u"防焊加大单边(mil)",
                         u"文字加大单边(mil)", ]
        else:
            arraylist = [u"钻孔加大单边(mil)", u"防焊加大单边(mil)"]
            
        for key in arraylist:
            if self.dic_item_value.has_key(key):
                try:
                    self.dic_item_value[key] = float(self.dic_item_value[key]) 
                except:
                    QtGui.QMessageBox.information(self, u'提示', u'检测到 %s 参数[ %s ]为空或非法数字,请检查~' % (
                        key, self.dic_item_value[key]), 1)
                    return 0

        return 1
        
    def create_film(self):
        result = self.get_item_value()
        if not result:
            return
        
        stepname = "panel"        
        
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        all_steps = get_panelset_sr_step(job.name, stepname)
        if "set" in all_steps:
            set_name = "set"
        else:
            if "edit" in all_steps:
                set_name = "edit"
            else:
                set_name = None
        
        matrixInfo = job.matrix.getInfo()
        # old_layers = matrixInfo["gROWname"]
        # bk_layer = []
        # for layer in old_layers:
        #     if layer in ["m1-bf", "m2-bf"]:
        #         bk_layer.append(layer)
        # if bk_layer:
        #     log = u"检测到资料已存在以下备份层{0}，请确认是否继续，点击yes：程序自动删除备份层，重新备份。\n点击no：返回查看"
        #     ret=QtGui.QMessageBox.question(self, u'提示', log.format(bk_layer), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        #     if ret == QtGui.QMessageBox.Yes:
        #         for layer in bk_layer:
        #             step.removeLayer(layer)
        #
        #     if ret == QtGui.QMessageBox.No:
        #         sys.exit()
            
        # for layer in ["m1", "m2"]:
        #     matrixInfo = job.matrix.getInfo()
        #     for i, name in enumerate(matrixInfo["gROWname"]):
        #         if name == layer:
        #             origRow = matrixInfo["gROWrow"][i]
        #             step.COM("matrix_copy_row,job={0},matrix=matrix,row={1},ins_row={2}".format(job.name,origRow, len(old_layers) - 2))
        #             break
                
        # matrixInfo = job.matrix.getInfo()
        # new_layers = matrixInfo["gROWname"]
        # for name in new_layers:
        #     if name not in old_layers:
        #         step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(job.name, name))
        #         step.COM("matrix_rename_layer,job={0},matrix=matrix,layer={1},new_name={2}".format(job.name,name, name[:2]+"-bf"))
        #
        
        STR = '-t step -e %s/%s -d REPEAT,units=mm' % (job.name, stepname)
        gREPEAT_info = step.DO_INFO(STR)
        gREPEATstep = gREPEAT_info['gREPEATstep']
        gREPEATxmax = gREPEAT_info['gREPEATxmax']
        gREPEATymax = gREPEAT_info['gREPEATymax']
        gREPEATxmin = gREPEAT_info['gREPEATxmin']
        gREPEATymin = gREPEAT_info['gREPEATymin']
        set_rect_area = []
        for i in xrange(len(gREPEATstep)):
            if gREPEATstep[i] == set_name:                
                set_rect_area.append(
                    [gREPEATxmin[i], gREPEATymin[i], gREPEATxmax[i], gREPEATymax[i]])
            
        
        xuhao_layer = ""
        step.resetFilter()
        # for layer in ["m1", "m2"] + silkscreenLayers:
        for layer in ls_layers.values() + silkscreenLayers:
            step.clearAll()
            step.affect(layer)
            step.filter_set(feat_types='text', polarity='positive')
            for xs, ys, xe, ye in set_rect_area:
                step.selectRectangle(xs, ys, xe, ye)
                if step.featureSelected():
                    xuhao_layer = layer
                    break
                
            if xuhao_layer:
                break
            
        #计算panel有序号的在set中的位置
        find_piont_area = []
        if xuhao_layer and set_name:# and self.dic_item_value[u"套印类型"] == u"set套印":
            editstep = gClasses.Step(job, set_name)
            editstep.open()
            editstep.COM("units,type=mm")
            editstep.clearAll()
            editstep.removeLayer("calc_num_position")
            editstep.COM("profile_to_rout,layer=calc_num_position,width=10")
            editstep.affect("calc_num_position")
            editstep.COM("sel_create_sym,symbol=calc_num_position,x_datum=0,y_datum=0,"
                         "delete=no,fill_dx=2.54,fill_dy=2.54,attach_atr=no,retain_atr=no")
            editstep.selectDelete()
            editstep.addPad(0, 0, "calc_num_position")            
            
            step.open()
            step.flatten_layer("calc_num_position", "calc_num_position_flt")
            for xs, ys, xe, ye in set_rect_area:
                step.clearAll()
                step.affect(xuhao_layer)
                step.resetFilter()
                step.filter_set(feat_types='text', polarity='positive')
                step.selectRectangle(xs, ys, xe, ye, intersect='yes')
                feat_out1 = ""
                if step.featureSelected():
                    layer_cmd1 = gClasses.Layer(step, xuhao_layer)
                    feat_out1 = layer_cmd1.featout_dic_Index(units="mm", options="feat_index+select")["text"]
                    
                step.clearAll()
                step.affect("calc_num_position_flt")
                step.resetFilter()
                step.setSymbolFilter("calc_num_position")
                step.selectRectangle(xs, ys, xe, ye, intersect='yes')                
                feat_out2 = ""
                if step.featureSelected():
                    layer_cmd2 = gClasses.Layer(step, "calc_num_position_flt")
                    feat_out2 = layer_cmd2.featSelOut(units="mm")["pads"]
                    
                if feat_out1 and feat_out2:
                    angle = 360 - feat_out2[0].rotation
                    step.clearAll()
                    step.affect(xuhao_layer)
                    step.resetFilter()
                    
                    for obj in feat_out1:
                        step.selectNone()
                        step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(xuhao_layer, obj.feat_index))                        
                        xmin, ymin, xmax, ymax = get_layer_selected_limits(step, xuhao_layer)                        
                        set_x = xmin - feat_out2[0].x
                        set_y = ymin - feat_out2[0].y
                        new_xmin, new_ymin = self.get_convert_coordinate(set_x, set_y, angle)
                        
                        set_x = xmax - feat_out2[0].x
                        set_y = ymax - feat_out2[0].y
                        new_xmax, new_ymax = self.get_convert_coordinate(set_x, set_y, angle)                                               
                        
                        if (new_xmin, new_ymin, new_xmax, new_ymax) not in find_piont_area:                            
                            find_piont_area.append((new_xmin, new_ymin, new_xmax, new_ymax))
                        
                    break    
        
        
        # step.PAUSE(str(find_piont_area))
        #删除单元内的图像 并铺铜
        step.removeLayer("hole_tmp")
        step.removeLayer("calc_num_position")
        step.removeLayer("calc_num_position_flt")
        
        hole_resize = self.dic_item_value[u"钻孔加大单边(mil)"] * 2 * 25.4
        mask_resize = self.dic_item_value[u"防焊加大单边(mil)"] * 2 * 25.4
        silk_resize = 0
        if self.dic_item_value[u"文字是否制作"] == u"是":
            silk_resize = self.dic_item_value[u"文字加大单边(mil)"] * 2 * 25.4        
        
        dic_week_layer = {}
        #dic_week_layer["m1"] = "c1"
        #if not step.isLayer("c1"):
            #dic_week_layer["m1"] = "cc"            
        #dic_week_layer["m2"] = "c2"
        #if not step.isLayer("c2"):
            #dic_week_layer["m2"] = "cs"
        # top_silk_layers = ["c1", "cc1", "c1-2", "c1-1", "cc1-2", "cc1-1"]
        # bot_silk_layers = ["c2", "cc2", "c2-2", "c2-1", "cc2-2", "cc2-1"]
        top_silk_layers = list(filter(lambda ss: re.match('(c|cc)1', ss), silkscreenLayers))
        bot_silk_layers = list(filter(lambda ss: re.match('(c|cc)2', ss), silkscreenLayers))
        # dic_week_layer["m1"] = top_silk_layers
        # dic_week_layer["m2"] = bot_silk_layers
        dic_week_layer[ls_layers['m1']] = top_silk_layers
        dic_week_layer[ls_layers['m2']] = bot_silk_layers

        for name in all_steps:
            editstep = gClasses.Step(job, name)
            editstep.open()
            editstep.COM("units,type=mm")
            editstep.clearAll()
            # for worklayer in ["m1", "m2"]:
            for worklayer in ls_layers.values():
                editstep.clearAll()
                editstep.affect(worklayer)
                
                # editstep.copyLayer(job.name, name, worklayer, worklayer+"-bf"+yftime)
            
                editstep.contourize()                
                editstep.copyLayer(job.name, name, worklayer, worklayer+"-surface")
                
                editstep.clearAll()
                editstep.affect("drl")
                editstep.resetFilter()
                editstep.refSelectFilter(worklayer, mode="disjoint")
                if editstep.featureSelected():
                    editstep.copySel("hole_tmp")
                    
                editstep.clearAll()
                editstep.affect(worklayer)
                editstep.selectDelete()
                
                editstep.reset_fill_params()
                editstep.COM("sr_fill,polarity=positive,step_margin_x=-0.254,step_margin_y=-0.254,step_max_dist_x=2540,\
                step_max_dist_y=2540,sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,\
                nest_sr=yes,stop_at_steps=,consider_feat=no,consider_drill=no,consider_rout=no,\
                dest=affected_layers,attributes=no")
                
                if editstep.isLayer("hole_tmp"):
                    editstep.clearAll()
                    editstep.affect("hole_tmp")
                    editstep.copyToLayer(worklayer, size=hole_resize, invert="yes")
                    
                editstep.clearAll()
                editstep.affect(worklayer+"-surface")
                editstep.copyToLayer(worklayer, size=mask_resize)
                
                if self.dic_item_value[u"文字是否制作"] == u"是":
                    
                    #for silk_layer in [silk_layer1, silk_layer2, silk_layer3,
                                       #silk_layer4, silk_layer5, silk_layer6]:
                    for silk_layer in silkscreenLayers:
                        if silk_layer in dic_week_layer[worklayer]:                                              
                            if step.isLayer(silk_layer):                        
                                editstep.copyLayer(job.name, name, silk_layer, silk_layer+"-surface")
                                editstep.clearAll()
                                editstep.affect(silk_layer+"-surface")
                                editstep.contourize()
                                editstep.copyToLayer(worklayer, size=silk_resize)
                                
                                #挑选文字层序号框 变成一个实体铜皮
                                editstep.clearAll()
                                editstep.affect(silk_layer)
                                editstep.resetFilter()
                                editstep.setAttrFilter("id", condition="no")
                                editstep.selectAll()                               
                                if editstep.featureSelected():
                                    editstep.copySel("id_tmp")
                                    editstep.clearAll()
                                    editstep.affect("id_tmp")
                                    editstep.COM("sel_break")
                                    editstep.COM("sel_cut_data,det_tol=25.4,con_tol=25.4,rad_tol=2.54,filter_overlaps=no,\
                                    delete_doubles=no,use_order=yes,ignore_width=yes,ignore_holes=none,\
                                    start_positive=yes,polarity_of_touching=same")
                                    editstep.copyToLayer(worklayer, size=silk_resize)
                                    editstep.removeLayer("id_tmp")
                                    editstep.removeLayer("id_tmp+++")
                                
                                editstep.resetFilter()
                                editstep.clearAll()
                
                #挑选周期 位置加上铜皮
                rect_area = []
                # for weeklayer in silkscreenLayers + [worklayer+"-bf"+yftime]:
                for weeklayer in silkscreenLayers + ['m1', 'm2']:
                    
                    if weeklayer in silkscreenLayers:                        
                        if weeklayer not in dic_week_layer[worklayer]:
                            continue
                        
                    if not step.isLayer(weeklayer):
                        continue
                    editstep.clearAll()
                    editstep.affect(weeklayer)
                    editstep.resetFilter()
                    editstep.selectSymbol("zq-2wm;zq-ewm;zq-wm", 1, 1)
                    
                    editstep.resetFilter()
                    editstep.filter_set(feat_types='text')
                    editstep.selectAll()
                    
                    if editstep.featureSelected():                        
                        layer_cmd = gClasses.Layer(editstep, weeklayer)
                        feat_out3 = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]
                        feat_out3 += layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["text"]
                        for obj in feat_out3:
                            editstep.clearAll()
                            editstep.affect(weeklayer)
                            index = obj.feat_index
                            editstep.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(weeklayer, index))
                            if editstep.featureSelected():
                                editstep.removeLayer("text_tmp")
                                editstep.copySel("text_tmp")
                                editstep.clearAll()
                                editstep.affect("text_tmp")
                                editstep.COM("sel_break")
                                editstep.resetFilter()
                                editstep.selectAll()
                                x1, y1, x2, y2 = get_layer_selected_limits(editstep, "text_tmp")
                                if weeklayer in [worklayer+"-bf"+yftime]:
                                    sur_size = mask_resize/ 1000 * 0.5
                                else:
                                    sur_size = silk_resize/ 1000 * 0.5
                                # 周期需加宽一点 以免1的数字不够 产线实际用8的数字
                                rect_area.append([x1 - sur_size - abs(x2 - x1) / 8, y1 - sur_size - abs(y2 - y1) / 8,
                                                  x2 + sur_size + abs(x2 - x1) / 8, y2 + sur_size + abs(y2 - y1) / 8])
                                # step.PAUSE(str(rect_area)) 
                                
                # step.PAUSE(str(rect_area))             
                if rect_area:
                    editstep.clearAll()
                    editstep.affect(worklayer)
                    editstep.reset_fill_params()
                    for xs, ys, xe, ye in rect_area:                        
                        editstep.addRectangle(xs, ys, xe, ye)
                        
                #panel有序号的在set中的位置上加铜
                # editstep.PAUSE(name)
                if find_piont_area and name == set_name:
                    editstep.clearAll()
                    editstep.affect(worklayer)
                    editstep.reset_fill_params()
                    for xs, ys, xe, ye in find_piont_area:
                        min_x = min([xs, xe])
                        max_x = max([xs, xe])
                        min_y = min([ys, ye])
                        max_y = max([ys, ye])
                        editstep.addRectangle(min_x-0.5, min_y-0.5, max_x+0.5, max_y+0.5)
            
            editstep.clearAll()
            editstep.close()
        
        step.open()
        step.clearAll()
        step.removeLayer("m1-surface")
        step.removeLayer("m2-surface")
        
        for silk_layer in silkscreenLayers:
            if step.isLayer(silk_layer+"-surface"):
                step.removeLayer(silk_layer+"-surface")
        #step.removeLayer("c1-surface")
        #step.removeLayer("c2-surface")
        #step.removeLayer("cc1-surface")
        #step.removeLayer("cc2-surface")        
        #step.removeLayer("c1-2-surface")
        #step.removeLayer("c2-2-surface")
        #step.removeLayer("c1-1-surface")
        #step.removeLayer("c2-1-surface")            
        #step.removeLayer("cc1-2-surface")
        #step.removeLayer("cc2-2-surface")
        #step.removeLayer("cc1-1-surface")
        #step.removeLayer("cc2-1-surface")        
    
        
        step.removeLayer("hole_tmp")
        step.removeLayer("text_tmp")
        #set套印的情况
        if self.dic_item_value[u"套印类型"] == u"set套印":
            editstep = gClasses.Step(job, "set")
            editstep.open()
            editstep.COM("units,type=mm")
            editstep.PAUSE(u"set套印创建dwd层，请手动选择好四个定位点，然后继续！".encode("utf8"))
            while not editstep.featureSelected():
                editstep.PAUSE(u"请选中定位点，然后继续！".encode("utf8"))
            
            if editstep.featureSelected():
                editstep.copySel("dwd")
                editstep.clearAll()
                editstep.affect("dwd")
                editstep.changeSymbol("r0")
                editstep.addAttr(".fiducial_name", attrVal='317.reg', valType='text', change_attr="yes")
                
                # for layer in ["m1", "m2"]:
                for layer in ls_layers.values():
                    editstep.copySel(layer)
                    
                editstep.clearAll()

        step.COM('save_job,job=%s,override=no' % job.name)
        QtGui.QMessageBox.information(self, u'提示', u"制作完成，请检查！", 1)
        sys.exit()
        
    def get_convert_coordinate(self, set_x, set_y, angle):
        if angle == 90:
            new_set_x = set_y
            new_set_y = set_x * -1
        elif angle == 180:
            new_set_x = set_x * -1
            new_set_y = set_y * -1
        elif angle == 270:
            new_set_x = set_y * -1
            new_set_y = set_x
        else:
            new_set_x = set_x
            new_set_y = set_y
            
        return new_set_x, new_set_y

    def set_widget(self, font, arraylist, title, checkbox):
        groupbox = QtGui.QGroupBox()
        groupbox.setTitle(title)
        groupbox.setStyleSheet("QGroupBox:title{color:green}")
        groupbox.setFont(font)	
        gridlayout = self.get_layout(arraylist, checkbox)
        groupbox.setLayout(gridlayout)
        return groupbox
    
    def hide_show_editor(self, index):
        if index == 2:
            self.dic_label[u"文字加大单边(mil)"].hide()
            self.dic_editor[u"文字加大单边(mil)"].hide()
        if index == 1:
            self.dic_label[u"文字加大单边(mil)"].show()
            self.dic_editor[u"文字加大单边(mil)"].show()
            
    def get_layout(self, arraylist, checkbox):

        gridlayout = QtGui.QGridLayout()

        for i, name in enumerate(arraylist):
            for key, value in name.iteritems():
                self.dic_label[key] = QtGui.QLabel()
                self.dic_label[key].setText(key)
                self.dic_editor[key] = getattr(QtGui, value)()
                if key == u"文字是否制作":
                    self.dic_editor[key].currentIndexChanged.connect(self.hide_show_editor)
                    
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

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)	
    main_widget = auto_make_film()
    main_widget.show()    
    sys.exit(app.exec_())
    