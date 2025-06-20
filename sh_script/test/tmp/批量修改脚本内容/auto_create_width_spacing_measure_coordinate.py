#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20240819"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""正业设置量测坐标自动生成 """

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
import math
import shutil
from genesisPackages import matrixInfo, job, \
     signalLayers,get_sr_area_flatten, \
     get_layer_selected_limits, get_sr_area_for_step_include, \
     get_profile_limits, outsignalLayers, \
     lay_num, get_panelset_sr_step, top

outsignalLayers = ["l1", "l{0}".format(lay_num)]

from get_erp_job_info import get_mysql_mi_drawing_mark_info, \
     get_cu_weight, get_zk_tolerance, get_inplan_imp

from create_ui_model import app, showMessageInfo, \
     QtGui, QtCore, Qt

from SMK_Imp_TableDelegate import itemDelegate

import MySQL_DB
conn = MySQL_DB.MySQL()
dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                           username='root', passwd='k06931!')
dbc_p = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='project_status', prod=3306,
                           username='root', passwd='k06931!')
    
matrixInfo = job.matrix.getInfo()
arraylist_imp_info = get_inplan_imp(job.name.split("-")[0].upper())

tolerance_info = os.path.join(job.dbpath, "user", job.name +"_tolerance_info.json")

class measure_coordinate(QtGui.QWidget):
    """"""

    def __init__(self, parent=None):
        """Constructor"""
        super(measure_coordinate, self).__init__(parent)
        
        self.array_mark_infos = get_mysql_mi_drawing_mark_info(job.name.split("-")[0].upper())
        if not self.array_mark_infos:
            self.array_mark_infos = get_mysql_mi_drawing_mark_info(job.name[:12].upper())
        
    def create_text_file(self):
        """添加所有模块"""
        
        res = self.get_item_value()
        if not res:
            return
        
        self.calc_mark_point_info()
        
    def get_mysql_data(self):               
        
        self.download_info = {}
        if self.array_mark_infos:
            try:
                for key, value in self.array_mark_infos[0].iteritems():
                    if key == "job_name":                        
                        self.download_info["from_job"] = str(value)
                    if key == "update_time":
                        self.download_info[key] = str(value)                         
                    if key == "mark_count":
                        if float(value) == 0:
                            if "manual" in sys.argv[1:]:  
                                showMessageInfo(u"MI标记信息异常，mark_count数量为0，请通知MI重新运行标记图纸打印!")
                                exit(0)
                            else:
                                return u"MI标记信息异常，mark_count数量为0，请通知MI重新运行标记图纸打印!", None
                            
                for key, value in self.array_mark_infos[0].iteritems(): 
                    if key == "marks_json":
                        value = value.replace("\n","").replace(": null,",": None,").replace(":null,",":None,").replace("\r","").replace("\n","")
                        try:
                            dic_value = eval(value)
                        except:
                            dic_value = self.get_mysql_data_modify(value)
                            
                        dic_net_mark_info = dic_value["step_note"]["net"]
                        dic_profile_info = dic_value["run_profile"]
                        break                    
                    
            except Exception as e:
                if "manual" in sys.argv[1:]:  
                    showMessageInfo(u"加载数据库MI标记信息异常，请手动制作量测坐标资料，{0}!".format(e))
                    exit(0)
                else:
                    return u"加载数据库MI标记信息异常，请手动制作量测坐标资料，{0}!".format(e), None
        else:
            if "manual" in sys.argv[1:]:  
                showMessageInfo(u"数据库MI标记信息为空，无法自动输出坐标信息，请手动制作量测坐标资料!")
                exit(0)
            else:
                return u"数据库MI标记信息为空，无法自动输出坐标信息，请手动制作量测坐标资料!", None
            
        return dic_net_mark_info, dic_profile_info
    
    def get_real_zk_width_spacing_value(self, **kwargs):
        """因图纸标注内的阻抗值不一定准确，需跟阻抗表内在进行比较，取出实际阻抗线宽线距"""
        # print(kwargs)
        find_data = []
        for dic_imp_info in arraylist_imp_info:
            ref_layer = dic_imp_info["REF_LAYER_"]
            if ref_layer is None:
                ref_layer = ""
            trace_layer = dic_imp_info["TRACE_LAYER_"]
            finish_lw = dic_imp_info["FINISH_LW_"]
            finish_ls = dic_imp_info["FINISH_LS_"]
            orig_lw = dic_imp_info["ORG_WIDTH"]
            orig_ls = dic_imp_info["ORG_SPC"]
            eq_lw = dic_imp_info["EQ_LW_"]
            eq_ls = dic_imp_info["EQ_LS_"]
            if orig_ls is None:
                orig_ls = 0
            cusimp = float(dic_imp_info["CUSIMP"])
            
            #if eq_lw:
                #finish_lw = eq_lw
                #finish_ls = eq_ls
                
            #if int(cusimp) == float(cusimp):
                #cusimp = str(int(cusimp))
            #else:
                #cusimp = str(cusimp)
            if trace_layer == kwargs["TRACE_LAYER_"] and "-lyh" in job.name:
                print(trace_layer, ref_layer, cusimp, orig_lw, orig_ls, kwargs)
            if kwargs.get("LINE_2_CU", "None") != "None":
                if kwargs["LINE_2_CU"] not in dic_imp_info["IMODEL"].decode("utf8"):
                    continue
                
            if trace_layer == kwargs["TRACE_LAYER_"] and \
               ref_layer in kwargs["REF_LAYER_"] and \
               abs(float(cusimp) - float(kwargs["CUSIMP"])) < 0.1 and \
               abs(orig_lw - kwargs["ORG_WIDTH"]) < 0.1 and \
               abs(orig_ls - kwargs["ORG_SPC"]) < 0.1:
                return finish_lw, finish_ls, eq_lw, eq_ls, orig_lw, orig_ls
            
            # 去掉参考层 再计算一次 排除有些图纸打印的参考层错误
            if trace_layer == kwargs["TRACE_LAYER_"] and \
               abs(float(cusimp) - float(kwargs["CUSIMP"])) < 0.1 and \
               abs(orig_lw - kwargs["ORG_WIDTH"]) < 0.1 and \
               abs(orig_ls - kwargs["ORG_SPC"]) < 0.1:
                find_data.append([finish_lw, finish_ls, eq_lw, eq_ls, orig_lw, orig_ls])
                continue
                
            # 去掉原稿线宽线距 参考层 再计算一次 排除有些图纸打印的线宽线距错误
            if trace_layer == kwargs["TRACE_LAYER_"] and \
               abs(float(cusimp) - float(kwargs["CUSIMP"])) < 0.1:
                find_data.append([finish_lw, finish_ls, eq_lw, eq_ls, orig_lw, orig_ls])                
                
        if len(find_data) == 1:
            return find_data[0]
            
        return None
    
    def get_transform_xy(self, xy,lim_xy):
        new_xy = xy[:]
        new_xy[0] -= lim_xy[0][0]
        new_xy[1] -= lim_xy[1][1]
        new_xy[1] = 0 - new_xy[1]
        
        return new_xy
    
    def get_same_coor_type_name_order(self, array_coor_info, orig_info, lim_xy):
        """有相同note标记时 要排序按-1 -2 -3等  根据图纸的坐标算法来推算序号"""
        array_calc_info = []
        for info in array_coor_info:
            coor_x = info[10][3]
            coor_y = info[10][4]
            
            if info[3] == orig_info[3]:                
                new_coor_x, new_coor_y = self.get_transform_xy([coor_x, coor_y], lim_xy)
                distance = math.hypot(new_coor_x-0, new_coor_y-0)
                array_calc_info.append([distance, info])
                
        array_calc_info.sort()
        if len(array_calc_info) > 1:
            for i, calc_info in enumerate(array_calc_info[::-1]):
                if calc_info[1] == orig_info:
                    if self.download_info and self.download_info["update_time"] < '2024-08-27 17:51:00':
                        # 这段时间之前的 是旧模式从-1 开始
                        return orig_info[3] + "-" + str(i+1)
                    else:
                        if i >= 1:
                            return orig_info[3] + "-" + str(i)
        
        return orig_info[3]
    
    def calc_mark_point_info(self, output_dir=None,
                             uploading_erp=None,
                             set_offset_x=None,
                             set_offset_y=None):
        """计算坐标 先添加在edit 然后flatten到panel"""
        if "edit" not in matrixInfo["gCOLstep_name"]:
            if "manual" in sys.argv[1:]:    
                showMessageInfo(u"edit 不存在，请检查，请手动制作量测坐标资料!")
                sys.exit()
            else:
                # exit(0)
                return u"edit 不存在，请检查，请手动制作量测坐标资料!"
            
        if "panel" not in matrixInfo["gCOLstep_name"]:
            if "manual" in sys.argv[1:]:    
                showMessageInfo(u"panel 不存在，请检查，请手动制作量测坐标资料!")
                sys.exit()
            else:
                # exit(0)
                return u"panel 不存在，请检查，请手动制作量测坐标资料!"
            
        if "-lyh" in job.name:
            uploading_erp = True
            
        if "auto_uploading" in sys.argv[1:]:
            uploading_erp = True
            
        cu_info = get_cu_weight(job.name.upper(), select_dic=True)
        if not cu_info:           
            log = u"获取inplan 层镜像信息为空，请反馈MI是否checkin!"
            return log        
            
        stepname = "panel"
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        all_steps = get_panelset_sr_step(job.name, "panel")
        rotation_edit = None
        if "edit" not in all_steps:
            rotation_edit = list(set([name for name in all_steps if re.match("edit_\d+", name)]))
            if not rotation_edit:
                if "manual" in sys.argv[1:]:    
                    showMessageInfo(u"edit 不在panel拼版中，请检查是否有旋转或阴阳，请手动制作量测坐标资料!")
                    sys.exit()
                else:
                    # exit(0)
                    return u"edit 不在panel拼版中，请检查是否有旋转或阴阳，请手动制作量测坐标资料!"
        
        dic_net_mark_info, dic_profile_info = self.get_mysql_data()
        if dic_profile_info is None:
            return dic_net_mark_info
        
        # 获取阻抗线的公差信息
        array_erp_zk_line_tolerance_info = get_zk_tolerance(job.name.upper().split("-")[0])
        
        #设置实际计算的阻抗公差
        self.dic_zk_calc_tolerance_info = {}
        
        #units = "inch"        
        #if "manual" in sys.argv[1:]:  
            #units = str(self.dic_item_value[u"单位"])
            
        signalLayers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                        if matrixInfo["gROWcontext"][i] == "board"
                        and (matrixInfo["gROWlayer_type"][i] == "signal" or \
                             matrixInfo["gROWlayer_type"][i] == "power_ground")]
        
        dic_layer_mirror = {}
        dic_mirror = {1: "no",0: "yes",}
        for layer in signalLayers:            
            for dic_info in cu_info:
                    if dic_info["LAYER_NAME"].lower() == layer:
                        dic_layer_mirror[layer] = dic_mirror[dic_info["LAYER_ORIENTATION"]]        
            
        if "manual" in sys.argv[1:]:
            output_layers = []
            for info in self.dic_item_value[u"层及公差"]:
                if info[0] == "1":
                    output_layers.append(info[1])
            
            if output_layers:
                signalLayers = output_layers
        
        editstep = gClasses.Step(job, "edit")
        editstep.open()
        editstep.COM("units,type=mm")
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(editstep)
        if set_offset_x is None or set_offset_y is None:            
            offset_x = f_xmin - dic_profile_info["gPROF_LIMITSxmin"]
            offset_y = f_ymin - dic_profile_info["gPROF_LIMITSymin"]
        else:
            offset_x = set_offset_x
            offset_y = set_offset_y            
            
        dic_pcs_coortype_name = {}
        pcs_count = 0
        get_exists_real_imp_info = []
        
        for layer, array_coor_info in dic_net_mark_info.iteritems():
            if layer.lower() not in signalLayers:
                continue
            dic_pcs_coortype_name[layer] = []
            editstep.clearAll()
            if array_coor_info:                        
                worklayer = layer + "_mark_point"                
                editstep.removeLayer(worklayer)
                editstep.createLayer(worklayer)
                editstep.affect(worklayer)
                
                for info in array_coor_info:
                    # print(info)
                    if 'Note' in info[2]:
                        if u"低压区" in info[9].decode("utf8"):
                            log = u"有备注:{0}，请手动制作缺少部分量测坐标资料!".format(info[9].decode("utf8"))
                            get_exists_real_imp_info.append(log)                               
                        continue
                    
                    tolerance_type = ""
                    _, _, _, coor_name, finish_orig_width_spacing,cusrequire_orig_width_spacing,ohm,ref_layer1,ref_layer2 = info[:9]                    
                    if u"线" in info[1].decode("utf8") or u"阻抗" in info[1].decode("utf8"):
                        tolerance_type = "min_line_t"
                        if u"阻抗" in info[1].decode("utf8"):
                            tolerance_type = "zk_t"
                            
                        if u"线距" in info[1].decode("utf8"):
                            coor_type = "linespace"
                            if u"线宽" in info[1].decode("utf8"):
                                coor_type = "linewidth_space"
                        else:
                            coor_type = "linewidth"
                            
                        if u"差分" in info[1].decode("utf8"):
                            coor_type = "linewidth_space"
                    else:
                        coor_type = "padwidth"   
                        # if u"SMD" in info[1].decode("utf8"):
                        tolerance_type = "smd_t"                        
                        if u"BGA" in info[1].decode("utf8"):
                            tolerance_type = "bga_t"
                        
                        #产线 曹靖涵 沟通这种人工手动标记 20241105 by lyh
                        if u"IC间距" in info[1].decode("utf8"):
                            continue
                        
                        # 产线 曹靖涵 沟通这种隔离环人工手动标记 20241120 by lyh
                        if u"隔离" in info[9].decode("utf8"):
                            continue
                            
                    try:                        
                        orig_width = float(finish_orig_width_spacing.split("/")[0])
                    except:                        
                        if "*" in finish_orig_width_spacing:
                            orig_width = min([float(finish_orig_width_spacing.split("*")[0]), float(finish_orig_width_spacing.split("*")[1])])
                            
                    orig_spacing = 0
                    eq_width, eq_spacing, new_orig_width, new_orig_spacing = 0, 0, 0, 0
                    if "/" in finish_orig_width_spacing:
                        try:                            
                            orig_spacing = float(finish_orig_width_spacing.split("/")[1])
                        except:
                            pass
                        
                        if u"共面" in info[1].decode("utf8"):
                            if u"差分" not in info[1].decode("utf8"):
                                orig_spacing = 0
                        
                    ref_layer = []
                    if ref_layer1 != "/":
                        ref_layer = [ref_layer1.upper()]
                    if ref_layer2 != "/":
                        ref_layer.append(ref_layer2.upper())
                        
                    if tolerance_type == "zk_t":
                        cus_orig_width = float(cusrequire_orig_width_spacing.split("/")[0])
                        cus_orig_spacing = 0
                        line_2_cu = "None"
                        if "/" in cusrequire_orig_width_spacing:
                            try:                              
                                cus_orig_spacing = float(cusrequire_orig_width_spacing.split("/")[1])
                            except:
                                pass
                            
                            if u"共面" in info[1].decode("utf8"):
                                if u"差分" not in info[1].decode("utf8"):
                                    cus_orig_spacing = 0
                                line_2_cu = u"共面"
                            
                        res = self.get_real_zk_width_spacing_value(TRACE_LAYER_=layer.upper(),
                                                                   REF_LAYER_=["&".join(ref_layer), "&".join(ref_layer[::-1])],
                                                                   CUSIMP=float(ohm),
                                                                   ORG_WIDTH=cus_orig_width,
                                                                   ORG_SPC=cus_orig_spacing,
                                                                   LINE_2_CU=line_2_cu)
                        if res is not None:
                            orig_width, orig_spacing, eq_width, eq_spacing, new_orig_width, new_orig_spacing = res
                        else:
                            if "-lyh" in job.name:
                                job.PAUSE(str(["get_real_zk_width_spacing_value error",
                                               orig_width, orig_spacing, ohm]))
                            log = u"获取{3}层ref:{4},{0} OHM原稿线宽线距{1} {2} 对应的阻抗线调整值失败，请手动制作缺少部分量测坐标资料!"
                            get_exists_real_imp_info.append(log.format(ohm, cus_orig_width,
                                                                       cus_orig_spacing, layer,
                                                                       "&".join(ref_layer)))
                    
                    #线距的用线宽表示
                    if coor_type == "linespace":
                        orig_spacing = orig_width
                    
                    same_coor_name_info = [new_info for new_info in array_coor_info if coor_name == new_info[3]]
                    if len(same_coor_name_info) >= 2:
                        coor_name = self.get_same_coor_type_name_order(array_coor_info, info,
                                                                       [(f_xmin, f_xmax),
                                                                        (f_ymin, f_ymax)])
                    
                    coor_x = info[10][3]
                    coor_y = info[10][4]
                    point_attr = 'zy_mark_info_{4}_{5}_{6}_{0}_{1}_{2}_{3}'.format(coor_type,                                                                                                  
                                                                                   coor_name, orig_width, orig_spacing,
                                                                                   coor_x, coor_y, tolerance_type, 
                                                                                   )
                    
                    dic_pcs_coortype_name[layer].append([coor_name, orig_width, orig_spacing, ohm, tolerance_type,
                                                         ["&".join(ref_layer), "&".join(ref_layer[::-1])],
                                                         eq_width, eq_spacing, new_orig_width, new_orig_spacing])
                    
                    editstep.addAttr(".string", attrVal=point_attr, valType='text')
                    editstep.addPad(coor_x+offset_x, coor_y+offset_y, "r{0}".format((orig_width+orig_spacing) *25.4), attributes="yes")
                    
                    # editstep.PAUSE(str([ohm, info]))
                    if ohm == "/":
                        # 最小线距的情况
                        self.dic_zk_calc_tolerance_info[point_attr] = [orig_width *0.1 ,
                                                                       orig_width *0.1 ]
                    else:
                        for dic_erp_zk_info in array_erp_zk_line_tolerance_info:
                            if layer == dic_erp_zk_info[u"层名".encode("utf8")].lower() and \
                               float(ohm) == float(dic_erp_zk_info[u"阻值".encode("utf8")]) and \
                               ("&".join(ref_layer) == dic_erp_zk_info[u"参考层".encode("utf8")] or \
                                "&".join(ref_layer[::-1]) == dic_erp_zk_info[u"参考层".encode("utf8")]): 
                                # editstep.PAUSE(str([dic_erp_zk_info]))
                                self.dic_zk_calc_tolerance_info[point_attr] = [dic_erp_zk_info[u"阻抗线公差正".encode("utf8")] ,
                                                                               dic_erp_zk_info[u"阻抗线公差负".encode("utf8")] ]
                           
                    # editstep.PAUSE(str([ohm, dic_erp_zk_info[u"阻值".encode("utf8")], self.dic_zk_calc_tolerance_info, layer, "&".join(ref_layer), "&".join(ref_layer[::-1])]))
                    
                editstep.resetFilter()
                editstep.selectAll()
                if not editstep.featureSelected():
                    editstep.removeLayer(worklayer)
                    continue                
                
                editstep.removeLayer(layer+"_check_line_pad")
                editstep.copySel(layer+"_check_line_pad")
                
                editstep.clearAll()
                editstep.affect(layer)
                editstep.resetFilter()
                editstep.filter_set(feat_types='pad;line;arc', polarity='positive')
                editstep.selectAll()
                
                # if "-lyh" in job.name:                    
                if not editstep.featureSelected():
                    if "net" in matrixInfo["gCOLstep_name"]:
                        editstep.copyLayer(job.name, "net", layer, layer)
                    editstep.selectNone()
                # editstep.selectAll()
                editstep.refSelectFilter(worklayer)                    
                if editstep.featureSelected():
                    editstep.copySel(layer+"_check_line_pad")
                
                editstep.clearAll()
                editstep.affect(layer+"_check_line_pad")
                editstep.resetFilter()
                editstep.setAttrFilter(".string,text=zy_mark_info*")
                editstep.selectAll()                    
                if editstep.featureSelected():
                    layer_cmd = gClasses.Layer(editstep, layer+"_check_line_pad")
                    feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]                        
                    for obj in feat_out:
                        editstep.selectNone()
                        editstep.selectFeatureIndex(layer+"_check_line_pad", obj.feat_index)
                        if editstep.featureSelected():
                            editstep.resetFilter()
                            if "padwidth" in obj.string:
                                editstep.filter_set(feat_types='pad', polarity='positive')
                                editstep.setAttrFilter(".smd")
                                editstep.setAttrFilter(".bga")
                                editstep.COM("filter_atr_logic,filter_name=popup,logic=or")
                            else:
                                editstep.filter_set(feat_types='line;arc', polarity='positive')
                            editstep.COM("sel_ref_feat,layers=,use=select,mode=touch,\
                            pads_as=shape,f_types=line\;pad\;surface\;arc\;text,\
                            polarity=positive\;negative,include_syms=,exclude_syms=")
                            if not step.featureSelected():
                                editstep.selectFeatureIndex(layer+"_check_line_pad", obj.feat_index)
                                if editstep.featureSelected():
                                    sel_feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]   
                                    editstep.COM("sel_resize,size={0}".format(float(sel_feat_out[0].symbol[1:]) *2))
                                
                                editstep.selectFeatureIndex(layer+"_check_line_pad", obj.feat_index)
                                editstep.COM("sel_ref_feat,layers=,use=select,mode=touch,\
                                pads_as=shape,f_types=line\;pad\;surface\;arc\;text,\
                                polarity=positive\;negative,include_syms=,exclude_syms=")                                
                                    
                            if editstep.featureSelected():
                                select_feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["lines"]
                                exists_attr_check = [str(getattr(sel_obj, "string", "")) for sel_obj in select_feat_out]
                                if "check_zy_mark_info_" in "".join(exists_attr_check):
                                    editstep.addAttr(".string", attrVal="check_"+obj.string, valType='text')
                                    for sel_obj in select_feat_out:
                                        x1, y1 = sel_obj.xs, sel_obj.ys
                                        x2, y2 = sel_obj.xe, sel_obj.ye
                                        editstep.addLine(x1, y1, x2, y2, sel_obj.symbol, attributes="yes")
                                    
                                    editstep.selectNone()
                                else:
                                    editstep.addAttr(".string", attrVal="check_"+obj.string, valType='text', change_attr="yes")
                            else:                                                              
                                editstep.selectFeatureIndex(layer+"_check_line_pad", obj.feat_index)
                                if editstep.featureSelected():
                                    editstep.selectDelete()
                                    
                editstep.resetFilter()
                editstep.setAttrFilter(".string,text=*zy_mark_info*")
                editstep.selectAll()
                editstep.COM("sel_reverse")
                if editstep.featureSelected():
                    editstep.selectDelete()
                
                editstep.selectNone()
                editstep.resetFilter()
                editstep.setAttrFilter(".string,text=zy_mark_info*")                
                editstep.filter_set(feat_types='pad')
                editstep.selectAll()
                count = editstep.featureSelected()
                if count != len(dic_pcs_coortype_name[layer]):
                    log = u"获取{0}层note标记数量{1}跟图纸数量{2}不一致，请手动制作缺少部分量测坐标资料!"
                    get_exists_real_imp_info.append(log.format(layer, count, len(dic_pcs_coortype_name[layer])))                                    
                
                editstep.clearAll()
                editstep.affect(layer+"_check_line_pad")
                editstep.resetFilter()
                editstep.selectAll()
                if editstep.featureSelected():
                    pcs_count += 1
            
            if dic_pcs_coortype_name[layer]:
                find_zk_info = [zk for zk in dic_pcs_coortype_name[layer]
                                if zk[4] == "zk_t"]
                erp_zk_info = [dic_imp_info for dic_imp_info in arraylist_imp_info
                               if dic_imp_info["TRACE_LAYER_"].lower() == layer]
                
                if erp_zk_info and not find_zk_info:
                    log = u"获取{0}层阻抗线标记数量为0，请手动制作量测坐标资料!".format(layer)
                    get_exists_real_imp_info.append(log)
                    continue
                
                if len(erp_zk_info) > len(find_zk_info):
                    log = u"获取{0}层阻抗线标记缺失不全，请手动制作缺少部分量测坐标资料!".format(layer)
                    get_exists_real_imp_info.append(log)                    
                
        editstep.clearAll()
            
        if pcs_count < 1:
            if "manual" in sys.argv[1:]:
                
                if set_offset_x is None:                    
                    res = self.calc_mark_point_info(output_dir=output_dir,
                                                    uploading_erp=uploading_erp,
                                                    set_offset_x=0,
                                                    set_offset_y=0)
                    if res :
                        # showMessageInfo(res)
                        datumx = editstep.getDatum()["x"] * 25.4
                        datumy = editstep.getDatum()["y"] * 25.4
                        res = self.calc_mark_point_info(output_dir=output_dir,
                                                        uploading_erp=uploading_erp,
                                                        set_offset_x=0-datumx,
                                                        set_offset_y=0-datumy)
                        if res:                                
                            showMessageInfo(res)
                            # if "-lyh" not in job.name:      
                            sys.exit()
                        else:
                            return
                else:
                    # showMessageInfo(u"单元内未发现要输出的坐标，请检查MI上传的note标记是否异常！{0} {1}".format(set_offset_x, set_offset_y))
                    return u"单元内未发现要输出的坐标，请手动制作量测坐标资料!{0} {1}".format(set_offset_x, set_offset_y)
                    
                showMessageInfo(u"单元内未发现要输出的坐标，请手动制作量测坐标资料!")
                sys.exit()
            else:

                if set_offset_x is None:       
                    res = self.calc_mark_point_info(output_dir=output_dir,
                                                    uploading_erp=uploading_erp,
                                                    set_offset_x=0,
                                                    set_offset_y=0)
                    if res:
                        datumx = editstep.getDatum()["x"] * 25.4
                        datumy = editstep.getDatum()["y"] * 25.4
                        res = self.calc_mark_point_info(output_dir=output_dir,
                                                        uploading_erp=uploading_erp,
                                                        set_offset_x=0-datumx,
                                                        set_offset_y=0-datumy)
                    return res
                
                return u"单元内未发现要输出的坐标，请手动制作量测坐标资料!"
            
        if get_exists_real_imp_info:
            if "manual" in sys.argv[1:]:    
                showMessageInfo(*get_exists_real_imp_info)
                #if "-lyh" not in job.name:                    
                    #sys.exit()
            else:
                if u"缺少部分" not in "".join(get_exists_real_imp_info):                    
                    return "<br>".join(get_exists_real_imp_info)
            
        #有旋转edit 需把做好的层拷贝到旋转层内
        if rotation_edit:
            for name in rotation_edit:
                r_editstep = gClasses.Step(job, name)
                r_editstep.open()
                r_editstep.COM("units,type=mm")
                datumx = r_editstep.getDatum()["x"] * 25.4
                datumy = r_editstep.getDatum()["y"] * 25.4
                r_editstep.clearAll()
                for layer in signalLayers:
                    if r_editstep.isLayer(layer+"_mark_point"):
                        r_editstep.copyLayer(job.name, editstep.name, layer+"_mark_point", layer+"_mark_point")
                        r_editstep.affect(layer+"_mark_point")
                        
                    if r_editstep.isLayer(layer+"_check_line_pad"):                        
                        r_editstep.copyLayer(job.name, editstep.name, layer+"_check_line_pad", layer+"_check_line_pad")
                        r_editstep.affect(layer+"_check_line_pad")
                # r_editstep.PAUSE(str([datumx, datumy, name.split("_")[1]]))
                r_editstep.COM('sel_transform,mode=anchor,oper=rotate,duplicate=no,x_anchor=%s,y_anchor=%s,angle=%s,'
                               'x_scale=1,y_scale=1,x_offset=0,y_offset=0' % (datumx, datumy, name.split("_")[1]))
                # r_editstep.PAUSE(str([datumx, datumy, name.split("_")[1]]))

        #阻抗条坐标获取
        #if "-lyh" in job.name:
            #job.PAUSE(str(dic_pcs_coortype_name))
        try:            
            icg_error_message = self.create_icg_coordinate(signalLayers,
                                                           array_erp_zk_line_tolerance_info,
                                                           dic_pcs_coortype_name,
                                                           dic_layer_mirror)
        except Exception as e:
            icg_error_message = [u"阻抗条获取信息异常，阻抗条上缺少部分坐标请手动标注！"]
        
        if icg_error_message:
            try:                
                icg_error_message = self.create_icg_coordinate_attr(signalLayers,
                                                                    array_erp_zk_line_tolerance_info,
                                                                    dic_pcs_coortype_name,
                                                                    dic_layer_mirror)
            except Exception as e:
                icg_error_message = [u"阻抗条获取信息异常，阻抗条上缺少部分坐标请手动标注！"]
        
        if icg_error_message:
            if "manual" in sys.argv[1:]:    
                showMessageInfo(*icg_error_message)
                #if "-lyh" not in job.name:             
                    #sys.exit()
            else:
                if u"缺少部分" not in "".join(icg_error_message):    
                    return "<br>".join(icg_error_message)
        
        rotation_icg = list(set([name for name in all_steps if re.match("icg(-d)?\d?_\d+", name)]))
        if rotation_edit and rotation_icg:
            for name in rotation_icg:
                r_editstep = gClasses.Step(job, name)
                r_editstep.open()
                r_editstep.COM("units,type=mm")
                datumx = r_editstep.getDatum()["x"] * 25.4
                datumy = r_editstep.getDatum()["y"] * 25.4
                r_editstep.clearAll()
                for layer in signalLayers:
                    if r_editstep.isLayer(layer+"_mark_point"):
                        r_editstep.copyLayer(job.name, name.split("_")[0], layer+"_mark_point", layer+"_mark_point")
                        r_editstep.affect(layer+"_mark_point")
                        
                    if r_editstep.isLayer(layer+"_check_line_pad"):                        
                        r_editstep.copyLayer(job.name, name.split("_")[0], layer+"_check_line_pad", layer+"_check_line_pad")
                        r_editstep.affect(layer+"_check_line_pad")
                        
                r_editstep.COM('sel_transform,mode=anchor,oper=rotate,duplicate=no,x_anchor=%s,y_anchor=%s,angle=%s,'
                               'x_scale=1,y_scale=1,x_offset=0,y_offset=0' % (datumx, datumy, name.split("_")[1]))                          

        step.open()
        step.COM("units,type=mm")
        # panel中需挑选人工标记要测试的step 以及icg
        
        #if "set" in all_steps:            
            #editsteps = [name for name in matrixInfo["gCOLstep_name"]
                         #if "set" in name]
            #editsteps = [name for name in matrixInfo["gCOLstep_name"] if "edit"]
        #else:
        editsteps = [name for name in matrixInfo["gCOLstep_name"]
                     if "edit" in name]
        
        step.removeLayer("sur_fill_tmp")
        get_sr_area_flatten("sur_fill_tmp", stepname="panel", include_sr_step=editsteps)

        icgsteps = [name for name in matrixInfo["gCOLstep_name"]
                     if "icg" in name ]
        if icgsteps:            
            get_sr_area_flatten("icg_sur_fill_tmp", stepname="panel", include_sr_step=icgsteps)
        
        step.clearAll()
        step.affect("sur_fill_tmp")
        step.COM("sel_resize,size=100")
        step.contourize()
        step.resetFilter()
        step.selectAll()
        
        layer_cmd = gClasses.Layer(step, "sur_fill_tmp")
        feat_indexes = layer_cmd.featSelIndex()
        dic_set_area_info = {}        
        for index in feat_indexes:
            step.selectNone()
            step.selectFeatureIndex("sur_fill_tmp", index)
            if step.featureSelected():
                xmin, ymin, xmax, ymax = get_layer_selected_limits(step, "sur_fill_tmp")
                dic_set_area_info[index] = [(xmin + xmax) * 0.5, (ymin + ymax) * 0.5, xmin, ymin, xmax, ymax]
                step.addAttr(".string", attrVal=index, valType='text', change_attr="yes")
            
        #获取角线区域的有效sr
        rect= get_sr_area_for_step_include(step.name, include_sr_step=["edit", "set", "icg", "zk"])
        sr_xmin = min([min(x1, x2) for x1, y1, x2, y2 in rect])    
        sr_ymin = min([min(y1, y2) for x1, y1, x2, y2 in rect])   
        sr_xmax = max([max(x1, x2) for x1, y1, x2, y2 in rect])    
        sr_ymax = max([max(y1, y2) for x1, y1, x2, y2 in rect])
        
        # 获取脚线区域 判断有小sr的区域
        step.COM("units,type=mm")
        if signalLayers:            
            layer_cmd = gClasses.Layer(step, signalLayers[0])
            feat_out = layer_cmd.featCurrent_LayerOut(units="mm")["pads"]
            jx_symbol_obj = [obj for obj in feat_out if obj.symbol in ("sh-con2", "sh-con")]
            all_jx_x = [obj.x for obj in jx_symbol_obj]
            all_jx_y = [obj.y for obj in jx_symbol_obj]
            if all_jx_x and all_jx_y:           
                min_jx_x = min(all_jx_x)
                max_jx_x = max(all_jx_x)
                min_jx_y = min(all_jx_y)
                max_jx_y = max(all_jx_y)
                
                STR = '-t step -e %s/%s -d REPEAT,units=mm' % (job.name, step.name)
                gREPEAT_info = step.DO_INFO(STR)
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
                except :
                    pass
        
        # 光点
        dic_arraylist_mark_point_info, result = self.get_marked_positoin_info(step, sr_xmin, sr_ymin, sr_xmax, sr_ymax,
                                                                              signalLayers, f_xmin, f_ymin, f_xmax, f_ymax,
                                                                              dic_layer_mirror)
        if result == "error":
            return dic_arraylist_mark_point_info
        
        # 找到距离四个角 及中心最近的surface
        find_surface_indexes = []
        five_surface_indexes = []
        for x, y in [(sr_xmin, sr_ymin), (sr_xmin, sr_ymax), 
                     (sr_xmax, sr_ymin), (sr_xmax, sr_ymax),
                     ((sr_xmin+sr_xmax)*0.5, (sr_ymin+sr_ymax)*0.5)]:
            distance = 100000
            find_index = None
            for index in dic_set_area_info.keys():
                if index in find_surface_indexes:
                    continue
                x1, y1 = dic_set_area_info[index][:2]
                if math.hypot(x1-x,y1-y) < distance:
                    distance = math.hypot(x1-x,y1-y)
                    find_index = index
                    
            if find_index:
                find_surface_indexes.append(find_index)
                five_surface_indexes.append(find_index)
            
        #坐标上传erp的情况
        if uploading_erp:
            find_surface_indexes = dic_set_area_info.keys()            
        
        step.removeLayer("find_surface_area")
        if find_surface_indexes:
            step.clearAll()
            step.affect("sur_fill_tmp")
            for index in find_surface_indexes:
                step.selectNone()
                step.selectFeatureIndex("sur_fill_tmp", index)
                step.copySel("find_surface_area")
                
        icg_surface_feat_indexes = []
        if step.isLayer("icg_sur_fill_tmp"):            
            step.clearAll()
            step.resetFilter()
            step.affect("icg_sur_fill_tmp")
            step.copyToLayer("sur_fill_tmp", size=-10)
            
            step.clearAll()
            step.affect("sur_fill_tmp")
            step.refSelectFilter("icg_sur_fill_tmp", mode="cover")
            if step.featureSelected():            
                layer_cmd = gClasses.Layer(step, "sur_fill_tmp")
                icg_surface_feat_indexes = layer_cmd.featSelIndex()
                find_surface_indexes += icg_surface_feat_indexes
                
                for index in icg_surface_feat_indexes:
                    step.selectNone()
                    step.selectFeatureIndex("sur_fill_tmp", index)
                    if step.featureSelected():
                        xmin, ymin, xmax, ymax = get_layer_selected_limits(step, "sur_fill_tmp")
                        dic_set_area_info[index] = [(xmin + xmax) * 0.5, (ymin + ymax) * 0.5, xmin, ymin, xmax, ymax]
                        if "-lyh" in job.name:
                            step.PAUSE(str(index))
                        step.addAttr(".string", attrVal=index, valType='text', change_attr="yes")
                        if "-lyh" in job.name:
                            step.PAUSE(str(icg_surface_feat_indexes))                        
                
        step.clearAll()
        step.affect("sur_fill_tmp")        
        step.copyLayer(job.name, step.name, "sur_fill_tmp", "sur_fill_tmp_bak")
        
        dic_arraylist_text_info = {}
        dic_uploading_erp_text_info = {}
        dic_surface_area = {}
        # five_area_coordinate = []
        for worklayer in signalLayers:                
            if step.isLayer(worklayer + "_mark_point"):
                dic_arraylist_text_info[worklayer] = []
                dic_uploading_erp_text_info[worklayer] = {}
                step.clearAll()
                step.flatten_layer(worklayer+"_check_line_pad", worklayer+"_check_line_pad_tmp")
                step.flatten_layer(worklayer + "_mark_point", worklayer + "_mark_point_tmp")
                
                step.affect(worklayer + "_mark_point_tmp")
                step.copySel(worklayer+"_check_line_pad_tmp")
                
                step.clearAll()
                step.affect(worklayer+"_check_line_pad_tmp")
                #旋转90度
                if dic_layer_mirror[worklayer] == "no":
                    oper = "rotate"
                else:
                    oper = "rotate\;mirror"                
                step.COM('sel_transform,mode=anchor,oper=%s,duplicate=no,x_anchor=%s,y_anchor=%s,angle=90,'
                         'x_scale=1,y_scale=1,x_offset=0,y_offset=0' % (oper, (f_xmin+f_xmax) *0.5, (f_ymin+f_ymax) *0.5))                
                
                #旋转90度
                step.copyLayer(job.name, step.name, "sur_fill_tmp_bak", "sur_fill_tmp")
                step.clearAll()
                step.affect("sur_fill_tmp")
                step.COM('sel_transform,mode=anchor,oper=%s,duplicate=no,x_anchor=%s,y_anchor=%s,angle=90,'
                         'x_scale=1,y_scale=1,x_offset=0,y_offset=0' % (oper, (f_xmin+f_xmax) *0.5, (f_ymin+f_ymax)*0.5))
                
                dic_tolerance = {}
                if "manual" in sys.argv[1:]:
                    for arraylist_tolerance in self.dic_item_value[u"层及公差"]:
                        _, layer, min_line_t, smd_t, bga_t, zk_t,min_line_bc,zk_bc = arraylist_tolerance
                        if worklayer == layer:
                            for i, tolerance in enumerate([min_line_t, smd_t, bga_t, zk_t]):
                                if i == 0:
                                    tolerance_type = u"min_line_t"
                                elif i == 1:
                                    tolerance_type = u"smd_t"
                                elif i == 2:
                                    tolerance_type = u"bga_t"
                                else:
                                    tolerance_type = u"zk_t"
                                if "/" in tolerance:
                                    dic_tolerance[tolerance_type] = [float(tolerance.split("/")[0]) *25.4,
                                                                     float(tolerance.split("/")[1]) *25.4,
                                                                     float(min_line_bc)*25.4,
                                                                     float(zk_bc)*25.4]
                                else:
                                    dic_tolerance[tolerance_type] = [float(tolerance) *25.4,
                                                                    float(tolerance) *25.4,
                                                                    float(min_line_bc)*25.4,
                                                                    float(zk_bc)*25.4 ]
                            break
                
                # step.PAUSE(str([dic_tolerance, self.dic_item_value[u"层及公差"]]))                
                dic_area_coodinate_info = {}
                for index in find_surface_indexes:
                    step.COM("truncate_layer,layer=find_surface_area")
                    step.clearAll()
                    step.affect("sur_fill_tmp")
                    step.VOF()
                    step.selectFeatureIndex("sur_fill_tmp", index)
                    step.VON()
                    if not step.featureSelected():
                        step.resetFilter()
                        step.setAttrFilter(".string,text={0}".format(index))
                        step.selectAll()
                        step.resetFilter()
                        if "-lyh" in job.name:
                            step.PAUSE(str(index))
                        
                    if step.featureSelected():
                        xmin, ymin, xmax, ymax = get_layer_selected_limits(step, "sur_fill_tmp")
                        
                        step.copySel("find_surface_area")                            
                        step.clearAll()
                        step.affect(worklayer+"_check_line_pad_tmp")
                        step.resetFilter()
                        step.filter_set(feat_types='pad;line;arc', polarity='positive')
                        step.refSelectFilter("find_surface_area")
                        if step.featureSelected():
                            layer_cmd = gClasses.Layer(step, worklayer+"_check_line_pad_tmp")
                            feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]
                            feat_out += layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["lines"]
                            feat_out += layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["arcs"]
                            #记录添加step 后续标记区域text
                            #area_x = round((xmin+xmax)*0.5, 0)
                            #area_y = round((ymin+ymax)*0.5, 0)
                            if index in icg_surface_feat_indexes:
                                dic_surface_area[(index, "icg")] = (xmin, ymin, xmax, ymax)
                            
                                dic_area_coodinate_info[index] = {u"min_line_t": [],
                                                                  u"smd_t": [],
                                                                  u"bga_t": [],
                                                                  u"zk_t": [],}                            
                            else:
                                dic_surface_area[(index, "set")] = (xmin, ymin, xmax, ymax)
                            
                                dic_area_coodinate_info[index] = {u"min_line_t": [],
                                                                  u"smd_t": [],
                                                                  u"bga_t": [],
                                                                  u"zk_t": [],}
              
                                #if index in five_surface_indexes:
                                    #five_area_coordinate.append((area_x, area_y))
                                    
                            for obj in feat_out:
                                if "zy_mark_info" in obj.string and "check_" not in obj.string:
                                    coor_name, orig_width, orig_spacing = obj.string.split("_")[-3:]
                                    orig_width = float(orig_width)
                                    orig_spacing = float(orig_spacing)
                                    if "padwidth" in obj.string:
                                        # find_feat_out = layer_cmd.featSelOut(units="mm")["pads"]
                                        find_feat_out = [new_obj for new_obj in feat_out if new_obj.string == "check_" + obj.string]
                                        
                                        # 测量点名称， X坐标，Y坐标，角度，标准值，测量方式，上公差，下公差
                                        if find_feat_out:
                                            if re.match("r\d+\.?\d+?", find_feat_out[0].symbol):
                                                method = 4
                                            else:
                                                method = 0
                                                
                                            for key, value in dic_tolerance.iteritems():
                                                if key in obj.string:
                                                    tolerance_upper, tolerance_down,min_line_bc,zk_bc = value
                                                    bc = 0
                                                    break
                                            else:
                                                tolerance_upper, tolerance_down,min_line_bc,zk_bc = 0, 0, 0, 0
                                                bc = 0
                                                
                                            line = "{0},{1},{2},{3},{4},{5},{6},{7}".format(
                                                coor_name, find_feat_out[0].x, find_feat_out[0].y,
                                                find_feat_out[0].rotation, orig_width+bc, method, tolerance_upper, tolerance_down
                                            )
                                            dic_arraylist_text_info[worklayer].append(line)
                                            
                                            #uploading_tolerance_upper = self.dic_zk_calc_tolerance_info.get(obj.string, [0, 0])[0]
                                            #uploading_tolerance_down = self.dic_zk_calc_tolerance_info.get(obj.string, [0, 0])[1]
                                            #if uploading_tolerance_upper == 0:
                                                #uploading_tolerance_upper = 0.3 if orig_width * 0.1 < 0.3 else orig_width * 0.1
                                            #if uploading_tolerance_down == 0:
                                                #uploading_tolerance_down = 0.3 if orig_width * 0.1 < 0.3 else orig_width * 0.1
                                            
                                            #if job.name[1:4] in ["a86", "d10"]:
                                                #uploading_tolerance_upper = 0.2
                                                #uploading_tolerance_down = 0.2
                                            uploading_tolerance_upper = 0
                                            uploading_tolerance_down = 0                                            
    
                                            for key in dic_area_coodinate_info[index].keys():
                                                if key in obj.string:
                                                    coor_info = [coor_name, find_feat_out[0].x, find_feat_out[0].y,
                                                        find_feat_out[0].rotation, orig_width, method,
                                                        uploading_tolerance_upper * 0.8, uploading_tolerance_down * 0.8]
                                                    if coor_info not in dic_area_coodinate_info[index][key]:
                                                        dic_area_coodinate_info[index][key].append(coor_info)
                                    else:
                                        if "linewidth" in obj.string and "space" not in obj.string:
                                            # find_feat_out = layer_cmd.featSelOut(units="mm")["lines"]
                                            find_feat_out = [new_obj for new_obj in feat_out
                                                             if new_obj.string == "check_" + obj.string
                                                             and new_obj.shape == "Line"]
                                            # 测量点名称， X坐标，Y坐标，角度，标准值，测量方式，上公差，下公差
                                            if find_feat_out:
                                                method = 0                                                
                                                for key, value in dic_tolerance.iteritems():
                                                    if key in obj.string:
                                                        tolerance_upper, tolerance_down,min_line_bc,zk_bc = value
                                                        if "zk_t" == key:
                                                            bc = zk_bc                                                            
                                                        else:
                                                            bc = min_line_bc
                                                        break
                                                else:
                                                    tolerance_upper, tolerance_down,min_line_bc,zk_bc = 0, 0, 0, 0
                                                    bc = 0
                                                    
                                                line = "{0},{1},{2},{3},{4},{5},{6},{7}".format(
                                                    coor_name, obj.x, obj.y,
                                                    self.get_angle(find_feat_out[0]), orig_width+bc, method, tolerance_upper, tolerance_down
                                                )
                                                dic_arraylist_text_info[worklayer].append(line)
                                                
                                                uploading_tolerance_upper = self.dic_zk_calc_tolerance_info.get(obj.string, [0, 0])[0]
                                                uploading_tolerance_down = self.dic_zk_calc_tolerance_info.get(obj.string, [0, 0])[1]
                                                if uploading_tolerance_upper == 0:
                                                    uploading_tolerance_upper = 0.3 if orig_width * 0.1 < 0.3 else orig_width * 0.1
                                                if uploading_tolerance_down == 0:
                                                    uploading_tolerance_down = 0.3 if orig_width * 0.1 < 0.3 else orig_width * 0.1
                                                    
                                                if job.name[1:4] in ["a86", "d10"]:
                                                    uploading_tolerance_upper = 0.2
                                                    uploading_tolerance_down = 0.2
                                                    
                                                for key in dic_area_coodinate_info[index].keys():
                                                    if key in obj.string:
                                                        if "zk_t" == key:
                                                            pass
                                                        else:
                                                            uploading_tolerance_upper = 0
                                                            uploading_tolerance_down = 0
                                                        coor_info = [coor_name, obj.x, obj.y,
                                                        self.get_angle(find_feat_out[0]), orig_width, method,
                                                        uploading_tolerance_upper * 0.8, uploading_tolerance_down * 0.8]
                                                        if coor_info not in dic_area_coodinate_info[index][key]:
                                                            dic_area_coodinate_info[index][key].append(coor_info)                                                    
                                        else:
                                            # find_feat_out = layer_cmd.featSelOut(units="mm")["lines"]
                                            find_feat_out = [new_obj for new_obj in feat_out
                                                             if new_obj.string == "check_" + obj.string
                                                             and new_obj.shape == "Line"]
                                            # 测量点名称， X坐标，Y坐标，角度，标准值，测量方式，上公差，下公差
                                            # 线距
                                            if find_feat_out:
                                                for key, value in dic_tolerance.iteritems():
                                                    if key in obj.string:
                                                        tolerance_upper, tolerance_down,min_line_bc,zk_bc = value
                                                        if "zk_t" == key:
                                                            bc = zk_bc
                                                        else:
                                                            bc = min_line_bc
                                                        break
                                                else:
                                                    tolerance_upper, tolerance_down,min_line_bc,zk_bc = 0, 0, 0, 0
                                                    bc = 0
                                                
                                                method = 2
                                                suffix = ""
                                                if "linewidth_space" in obj.string:
                                                    suffix = "-B"
                                                line = "{0},{1},{2},{3},{4},{5},{6},{7}".format(
                                                    coor_name+suffix, obj.x, obj.y,
                                                self.get_angle(find_feat_out[0]), orig_spacing, method, tolerance_upper*2, tolerance_down*2
                                                    )
                                                dic_arraylist_text_info[worklayer].append(line)
                                                
                                                uploading_tolerance_upper = self.dic_zk_calc_tolerance_info.get(obj.string, [0, 0])[0]
                                                uploading_tolerance_down = self.dic_zk_calc_tolerance_info.get(obj.string, [0, 0])[1]
                                                if uploading_tolerance_upper == 0:
                                                    uploading_tolerance_upper = 0.3 if orig_width * 0.1 < 0.3 else orig_width * 0.1
                                                if uploading_tolerance_down == 0:
                                                    uploading_tolerance_down = 0.3 if orig_width * 0.1 < 0.3 else orig_width * 0.1
                                                    
                                                if job.name[1:4] in ["a86", "d10"]:
                                                    uploading_tolerance_upper = 0.2
                                                    uploading_tolerance_down = 0.2                                                    
                                                
                                                for key in dic_area_coodinate_info[index].keys():
                                                    if key in obj.string:
                                                        if "zk_t" == key:
                                                            pass
                                                        else:
                                                            uploading_tolerance_upper = 0
                                                            uploading_tolerance_down = 0
                                                        coor_info = [coor_name+suffix, obj.x, obj.y,
                                                        self.get_angle(find_feat_out[0]), orig_spacing, method,
                                                        orig_spacing * 0.15 , orig_spacing * 0.15 ]
                                                        if coor_info not in dic_area_coodinate_info[index][key]:
                                                            dic_area_coodinate_info[index][key].append(coor_info)                                                    
                                                
                                                if "linewidth_space" in obj.string:
                                                    ##差分线宽 取一条即可
                                                    method = 0
                                                    for find_obj in find_feat_out:
                                                        line = "{0},{1},{2},{3},{4},{5},{6},{7}".format(
                                                            coor_name, (find_obj.xe+find_obj.xs) *0.5,
                                                            (find_obj.ye+find_obj.ys) *0.5,
                                                            self.get_angle(find_obj), orig_width+bc, method, tolerance_upper, tolerance_down
                                                        )
                                                        dic_arraylist_text_info[worklayer].append(line)
                                                        
                                                        for key in dic_area_coodinate_info[index].keys():
                                                            if key in obj.string:
                                                                if "zk_t" == key:
                                                                    pass
                                                                else:
                                                                    uploading_tolerance_upper = 0
                                                                    uploading_tolerance_down = 0
                                                                coor_info = [coor_name, (find_obj.xe+find_obj.xs) *0.5,
                                                                             (find_obj.ye+find_obj.ys) *0.5,
                                                                             self.get_angle(find_obj), orig_width, method,
                                                                             uploading_tolerance_upper * 0.8, uploading_tolerance_down * 0.8]
                                                                if coor_info not in dic_area_coodinate_info[index][key]:
                                                                    dic_area_coodinate_info[index][key].append(coor_info)                                                            
                                                        break
    
                dic_uploading_erp_text_info[worklayer].update(dic_area_coodinate_info)
                
        # 添加区域标记
        if uploading_erp:            
            step.removeLayer("pcs_num_order")
            step.createLayer("pcs_num_order")
            step.clearAll()
            step.affect("pcs_num_order")
            step.COM("profile_to_rout,layer=pcs_num_order,width=254")
            num = 1
            # u"坐标顺序描述": u"测量点名称， X坐标(mm)，Y坐标(mm)，角度，标准值(um)，测量方式",
            new_dic_uploading_erp_text_info = {u"MARK_INFO": dic_arraylist_mark_point_info,
                                               u"FIVE_AREA": "",}
            
            for layer, value in dic_uploading_erp_text_info.iteritems():
                new_dic_uploading_erp_text_info[layer] = {}
            
            five_area_num = []
            for index,set_icg in sorted(dic_surface_area.keys(), key=lambda x: dic_set_area_info[x[0]]):
                if "icg" not in set_icg:                                
                    xmin, ymin, xmax, ymax = dic_set_area_info[index][2:]# dic_surface_area[(x, y, set_icg)]
                    step.addText(xmin+2, (ymin+ymax) *0.5, str(num), 10, 10, 4)
                    step.addRectangle(xmin, ymin, xmax, ymax)
                    
                for layer, value in dic_uploading_erp_text_info.iteritems():
                    for surface_index, tolerance_type in value.iteritems():
                        if surface_index == index:
                            if set_icg == "set":
                                area_num = num
                            else:
                                area_num = "icg{0}".format(num)
                            
                            if surface_index in five_surface_indexes:
                                five_area_num.append(area_num)
                                
                            new_dic_uploading_erp_text_info[layer][area_num] = {
                                u"ZZXK_ZB": tolerance_type["min_line_t"],
                                u"SMD_ZB": tolerance_type["smd_t"],
                                u"BGA_ZB": tolerance_type["bga_t"],
                                u"IMP_ZB": tolerance_type["zk_t"],}
                            
                num += 1
            
            # print(json.dumps(new_dic_uploading_erp_text_info["l15"]))
            new_dic_uploading_erp_text_info["FIVE_AREA"] = list(set(five_area_num))
            
            step.resetFilter()
            step.filter_set(feat_types='surface', polarity='positive')
            step.selectAll()
            if step.featureSelected():
                step.COM("sel_surf2outline,width=254")
            
        if output_dir is None:            
            output_dir = u"/id/workfile/hdi_film/{0}/正业量测坐标".format(job.name)
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        for key, value in dic_arraylist_text_info.iteritems():
            
            file_path = os.path.join(output_dir, job.name.split("-")[0]+"-"+key+".txt")
            arraylist_info = ["ABC&,{0},{1}".format(job.name.split("-")[0], key)]
            # 公制
            #if units == "mm":                
                #arraylist_info += dic_arraylist_mark_point_info[key]
                #arraylist_info += value
            #else:            
            ## 坐标单位，用公制mm即可：不要用mil， 线宽公差，品质监控用的是mil，
            #for line in dic_arraylist_mark_point_info[key]:                
                #m, x, y, d = line.split(",")
                #line = "{0},{1},{2},{3}".format(m, float(x)/25.4, float(y)/25.4, float(d)/25.4)
                #arraylist_info.append(line)
            arraylist_info += dic_arraylist_mark_point_info[key]
                
            for line in value:                
                m, x, y, a,d,t,u,l = line.split(",")
                line = "{0},{1},{2},{3},{4},{5},{6},{7}".format(m, x, y, a,
                                                                float(d)/25.4, t,
                                                                float(u)/25.4, float(l)/25.4)
                arraylist_info.append(line) 

            with open(file_path, "w") as f:
                f.write("\n".join(arraylist_info))
                
        if "-lyh" not in job.name:
            step.removeLayer("sur_fill_tmp")
            step.removeLayer("find_surface_area")
            step.removeLayer("icg_sur_fill_tmp")
            for layer in job.matrix.getInfo()["gROWname"]:
                if "_check_line_pad_tmp" in layer or \
                   "_mark_point_tmp" in layer or \
                   "_mark_point" in layer or \
                   "_check_line_pad" in layer or \
                   "_pnl_mark" in layer:
                    step.removeLayer(layer)
                    
        if uploading_erp:  
            self.picture_pnl_order(step, "pcs_num_order", output_dir)
            
            picture_path = os.path.join(output_dir, job.name.upper().split("-")[0]+".png")
            fd = open(picture_path)
            image = fd.read()
            fd.close()
            # job.name = "Q00812TB240D1"
            sql = "select * from hdi_engineering.meascoordinate_base where job = '{0}'".format(job.name.split("-")[0].upper())
            datainfo = conn.SELECT_DIC(dbc_m, sql)
            if datainfo:
                sql = u"update hdi_engineering.meascoordinate_base \
                set Coordinate=%s,AreaPicture=%s,create_time=now(),remark=%s\
                where job = '{0}'".format(job.name.split("-")[0].upper())
                conn.SQL_EXECUTE(dbc_m, sql, (json.dumps(new_dic_uploading_erp_text_info),
                                              image, json.dumps(self.download_info)))                
            else:
                sql = u"insert into hdi_engineering.meascoordinate_base (job,Coordinate,AreaPicture,remark) values (%s,%s,%s,%s)"
                conn.SQL_EXECUTE(dbc_m, sql, (job.name.split("-")[0].upper(),
                                              json.dumps(new_dic_uploading_erp_text_info), image,
                                              json.dumps(self.download_info)))
            
            if icg_error_message or get_exists_real_imp_info:
                return "<br>".join(get_exists_real_imp_info+icg_error_message) + "not_delete"
        
        if "manual" in sys.argv[1:]:  
            showMessageInfo(u"输出成功, 路径：{0}".format(output_dir))            
            exit(0)
            
    def picture_pnl_order(self, step, worklayer, output_dir):
        """把排版拍照"""
        dir_path = os.path.dirname(sys.argv[0])
        output_dir_ls = "/tmp/picture"
        try:
            os.makedirs(output_dir_ls)
        except:
            pass
        os.system("/incam/server/site_data/scripts/anaconda2/bin/python {0}/create_data_to_picture.py {1} {2} {3}".format(
            dir_path, step.name, worklayer, output_dir_ls
        ))
        picture_file = os.path.join(output_dir_ls, job.name.upper().split("-")[0]+".png")
        if os.path.exists(picture_file):
            shutil.copy(picture_file, output_dir)
        
        os.system("rm -rf /tmp/picture/*")
            
    def get_angle(self, obj):
        try:
            return obj.angle
        except:
            return 0
        
    def get_marked_positoin_info(self, step, sr_xmin, sr_ymin, sr_xmax, sr_ymax, signalLayers,
                                 f_xmin, f_ymin, f_xmax, f_ymax, dic_layer_mirror):
        """获取板边光点信息"""
        ##光点位置 外层阻焊靶点 内层涨缩测量靶点
        dic_arraylist_mark_point_info = {}
        dic_mark_note = {0: "A",1: "B",2: "C",}
        for worklayer in signalLayers:                
            if step.isLayer(worklayer + "_mark_point"):
                step.clearAll()
                step.affect(worklayer)
                check_symbols = []
                if worklayer in outsignalLayers:
                    symbolname = "sh-dwsig2014"
                    check_symbols = ["r2000"]
                else:
                    check_symbols = ["r1524"]
                    symbolname = "measure_l*;measure_fd_l*"
                    step.selectSymbol(symbolname, 1, 1)
                    if not step.featureSelected():
                        symbolname = "r1524"
                
                step.selectSymbol(symbolname, 1, 1)
                if step.featureSelected() >= 3:
                    pass
                else:
                    step.resetFilter()
                    step.filter_set(feat_types='pad', polarity='positive')
                    step.selectAll()
                
                auto_calc = True
                while True:                        
                    step.copySel(worklayer+"_pnl_mark")
                    step.clearAll()
                    step.affect(worklayer+"_pnl_mark")
                    step.resetFilter()
                    step.selectAll()
                    step.COM("sel_break_level,attr_mode=merge")
                    layer_cmd = gClasses.Layer(step, worklayer+"_pnl_mark")
                    step.resetFilter()
                    step.filter_set(feat_types='pad', polarity='positive')
                    step.selectAll()
                    feat_out = layer_cmd.featout_dic_Index(units="mm", options="select+feat_index")["pads"]
                    find_mark_obj = []
                    
                    if dic_layer_mirror[worklayer] == "no":
                        array_mark = [(sr_xmax, sr_ymin),(sr_xmax, sr_ymax),
                                      (sr_xmin, sr_ymin), ]
                    else:
                        array_mark = [(sr_xmax, sr_ymax),(sr_xmax, sr_ymin),
                                      (sr_xmin, sr_ymax), ]                        
                        
                    for x, y in array_mark:
                        distance = 100000
                        find_obj = None
                        for obj in feat_out:                                
                            if obj in find_mark_obj:
                                continue
                            if auto_calc and obj.symbol not in check_symbols:
                                continue
                            x1, y1 = obj.x, obj.y
                            if math.hypot(x1-x,y1-y) < distance:
                                distance = math.hypot(x1-x,y1-y)
                                find_obj = obj
                                
                        if find_obj:
                            find_mark_obj.append(find_obj)
                            
                    if len(find_mark_obj) < 3:
                        if "manual" in sys.argv[1:]:  
                            auto_calc = False
                            step.removeLayer(worklayer+"_pnl_mark")
                            if worklayer in outsignalLayers:
                                # showMessageInfo(u"自动抓取光点位置异常，请手动选择4个防焊对位pad 后继续!")
                                step.PAUSE(worklayer+u"自动抓取光点位置异常，请手动选择4个防焊对位pad 后继续!".encode("utf8"))
                            else:
                                # showMessageInfo(u"自动抓取光点位置异常，请手动选择4个内层涨缩量测pad 后继续!")
                                step.PAUSE(worklayer+u"自动抓取光点位置异常，请手动选择4个内层涨缩量测pad 后继续!".encode("utf8"))
                        else:
                            return worklayer+u"自动抓取光点位置异常，请手动制作量测坐标资料!", "error"
                    else:
                        break
                    
                # step = gClasses.Step(job, name)
                step.removeLayer(worklayer+"_find_mark_info")
                step.createLayer(worklayer+"_find_mark_info")
                step.clearAll()
                step.affect(worklayer+"_find_mark_info")
                for obj in find_mark_obj:
                    step.addPad(obj.x, obj.y, obj.symbol)
                
                if dic_layer_mirror[worklayer] == "no":
                    oper = "rotate"
                else:
                    oper = "rotate\;mirror"
                    
                step.COM('sel_transform,mode=anchor,oper=%s,duplicate=no,x_anchor=%s,y_anchor=%s,angle=90,'
                         'x_scale=1,y_scale=1,x_offset=0,y_offset=0' % (oper, (f_xmin+f_xmax) *0.5, (f_ymin+f_ymax) *0.5))
                
                layer_cmd = gClasses.Layer(step, worklayer+"_find_mark_info")
                find_feat_out = layer_cmd.featOut(units="mm")["pads"]
                        
                dic_arraylist_mark_point_info[worklayer] = []
                for i, obj in enumerate(find_feat_out):
                    if i > 2:
                        break
                    line = "{0},{1},{2},{3}".format(
                        dic_mark_note[i], obj.x, obj.y, float(obj.symbol[1:]) *0.001
                    )
                    dic_arraylist_mark_point_info[worklayer].append(line)
        
        return dic_arraylist_mark_point_info, "success"
            
    def create_icg_coordinate(self, signalLayers,
                              array_erp_zk_line_tolerance_info,
                              dic_pcs_coortype_name,
                              dic_layer_mirror):
        """阻抗条坐标提取"""
        #阻抗条坐标提取
        icg_num = 0
        message_info = []
        
        for stepname in matrixInfo["gCOLstep_name"]:
            if "icg" not in stepname:
                continue         
            
            icg_step = gClasses.Step(job, stepname)
            icg_step.open()
            icg_step.COM("units,type=mm")
            for worklayer in signalLayers:
                layer_cmd = gClasses.Layer(icg_step, worklayer)
                text_feat_out = layer_cmd.featout_dic_Index(units="mm")["text"]
                line_feat_out = layer_cmd.featout_dic_Index(units="mm")["lines"]
                zk_text_info = list(set([obj.text for obj in text_feat_out if "OHM" in obj.text]))
                zk_line_info = [obj for obj in line_feat_out if getattr(obj, "imp_info", None) is not None
                                and obj.angle in [0, 180]]
                line_symbols = sorted(list(set([obj.symbol for obj in zk_line_info])), key=lambda x: float(x[1:]))
                zk_text_info = sorted(zk_text_info, key=lambda x: float(x.split(" ")[3].split("/")[0]))
                
                if len(line_symbols) != len(zk_text_info):
                    # 有相同线宽的 这里要处理一下
                    line_symbols = []
                    for obj in zk_line_info:
                        line_info = [obj.symbol, getattr(obj, "imp_info", None), getattr(obj, "string", None)]
                        if line_info not in line_symbols:
                            line_symbols.append(line_info)
                            
                    line_symbols = sorted([symbol for symbol,attr,_ in line_symbols], key=lambda x: float(x[1:]))                
                
                if len(line_symbols) < len(zk_text_info):
                    line_symbols = []
                    for obj in line_feat_out:
                        if getattr(obj, "imp_info", None) is not None and obj.angle not in [0, 180]:
                            if getattr(obj, "imp_info", None) == "differential":
                                if obj.symbol not in line_symbols:
                                    line_symbols.append(obj.symbol)
                            else:
                                line_symbols.append(obj.symbol)
                                
                    line_symbols = sorted([symbol for symbol in line_symbols], key=lambda x: float(x[1:]))
                    
                # job.PAUSE(str([worklayer, line_symbols, zk_text_info]))
                # 计算补偿值以备验证
                # bc_value = []
                s_num = 1
                d_num = 1
                exists_text = []
                for symbol, text_info in zip(line_symbols, zk_text_info):
                    if "L13&L113.20/4.12" in text_info :
                        text_info = "L12 REF L13&L11 3.20/4.12 85 OHM"
                    try:                        
                        _, _, ref_layer,width_spacing,ohm,_ = text_info.split()
                    except Exception as e:
                        print(e)
                        if job.name.split("-")[0] == "da8612od667a4":
                            # 会存在没有参欧姆值的情况
                            _, _, ref_layer, width_spacing,_ = text_info.split()
                            ohm = 85
                        elif job.name.split("-")[0] == "da8612gh799a3":
                            #if top.getUser() == "44813":
                                #job.PAUSE(str([e, text_info]))                            
                            _, _, ref_layer,width_spacing,ohm = text_info.replace("OHM", "").replace("'", "").split()
                        else:
                            # 会存在没有参考层的情况
                            _, _, width_spacing,ohm,_ = text_info.split()
                            ref_layer = "none"
                    # symbol, attr = symbol_info
                    if "&" in ref_layer:
                        ref_layer = ref_layer.lower().split("&")
                    else:
                        ref_layer = [ref_layer.lower()]                    
                    
                    orig_width = float(width_spacing.split("/")[0])
                    orig_spacing = 0
                    # bc_value.append(float(symbol[1:]) - line_width)
                    if "/" in width_spacing and width_spacing.count("/") >= 1:
                        imp_info = "differential"
                        coor_type = "linewidth_space"
                        try:                            
                            orig_spacing = float(width_spacing.split("/")[1])
                        except:
                            pass
                        if orig_spacing == 0:
                            imp_info = "single-ended"
                            coor_type = "linewidth"                            
                    else:
                        imp_info = "single-ended"
                        coor_type = "linewidth"
                        
                    icg_step.clearAll()
                    icg_step.affect(worklayer)
                    icg_step.resetFilter()
                    icg_step.filter_set(feat_types='line', polarity='positive')
                    icg_step.setAttrFilter(".imp_info,text={0}".format(imp_info))
                    icg_step.COM("filter_set,filter_name=popup,update_popup=yes,slot=line,"
                                 "slot_by=length\;angle,min_len={0},max_len={1},"
                                 "min_angle=0,max_angle=0".format(10, 200))                        
                    icg_step.COM("filter_set,filter_name=popup,update_popup=yes,slot=line,slot_by=angle,min_angle=0,max_angle=0")
                    icg_step.setAttrFilter(".string,text={0}*{1}".format(width_spacing.replace("/", "_*"), ohm))
                    # icg_step.setSymbolFilter(symbol)
                    icg_step.selectAll()
                    count = icg_step.featureSelected() 
                    new_orig_width = 0
                    #if "-lyh" in job.name and worklayer == "l12":    
                        #job.PAUSE(str([worklayer, count, text_info]))
                    if not count:
                        icg_step.resetFilter()
                        icg_step.filter_set(feat_types='line', polarity='positive')
                        icg_step.setAttrFilter(".imp_info,text={0}".format(imp_info))
                        icg_step.COM("filter_set,filter_name=popup,update_popup=yes,slot=line,"
                                     "slot_by=length\;angle,min_len={0},max_len={1},"
                                     "min_angle=0,max_angle=0".format(80, 200))                      
                        icg_step.COM("filter_set,filter_name=popup,update_popup=yes,slot=line,slot_by=angle,min_angle=0,max_angle=0")
                        icg_step.selectSymbol(symbol)
                        count = icg_step.featureSelected()
                        if not count:                            
                            # 有时单线跟差分线宽相近 但单线补偿多 故会有错乱现象
                            for new_text_info in zk_text_info:
                                if new_text_info not in exists_text:
                                    if "L13&L113.20/4.12" in new_text_info :
                                        new_text_info = "L12 REF L13&L11 3.20/4.12 85 OHM"
                                    try:                        
                                        _, _, ref_layer,width_spacing,ohm,_ = text_info.split()
                                    except Exception as e:
                                        print(e)
                                        # 会存在没有参考层的情况
                                        _, _, width_spacing,ohm,_ = text_info.split()
                                        ref_layer = "none"
                                        
                                    if "&" in ref_layer:
                                        ref_layer = ref_layer.lower().split("&")
                                    else:
                                        ref_layer = [ref_layer.lower()]
                                        
                                    new_orig_width = float(width_spacing.split("/")[0])
                                    if abs(orig_width - new_orig_width) > 0.1:
                                        continue
                                    
                                    new_orig_spacing = 0
                                    if "/" in width_spacing and width_spacing.count("/") >= 1:
                                        imp_info = "differential"
                                        coor_type = "linewidth_space"
                                        try:                                        
                                            new_orig_spacing = float(width_spacing.split("/")[1])
                                        except:
                                            pass
                                        if new_orig_spacing == 0:
                                            imp_info = "single-ended"
                                            coor_type = "linewidth"                                       
                                    else:
                                        imp_info = "single-ended"
                                        coor_type = "linewidth"
                                        
                                    icg_step.clearAll()
                                    icg_step.affect(worklayer)
                                    icg_step.resetFilter()
                                    icg_step.filter_set(feat_types='line', polarity='positive')
                                    icg_step.setAttrFilter(".imp_info,text={0}".format(imp_info))
                                    icg_step.COM("filter_set,filter_name=popup,update_popup=yes,slot=line,"
                                                 "slot_by=length\;angle,min_len={0},max_len={1},"
                                                 "min_angle=0,max_angle=0".format(80, 200))                                     
                                    icg_step.COM("filter_set,filter_name=popup,update_popup=yes,slot=line,slot_by=angle,min_angle=0,max_angle=0")
                                    icg_step.selectSymbol(symbol)
                                    count = icg_step.featureSelected()
                                    if count:
                                        orig_width = new_orig_width
                                        orig_spacing = new_orig_spacing
                                        text_info = new_text_info
                                        break
                        
                    # job.PAUSE(str([count, symbol, text_info, orig_width, new_orig_width, width_spacing]))
                    if count:                        
                        xmin, ymin, xmax, ymax = get_layer_selected_limits(icg_step, worklayer)
                        all_line_cmd = gClasses.Layer(icg_step, worklayer)
                        all_line_feat_out = all_line_cmd.featSelOut(units="mm")["lines"]
                        all_line_len = [obj.len for obj in all_line_feat_out]
                        max_line_len = max(all_line_len)                        
                        select_max_line = sorted([obj for obj in all_line_feat_out
                                                  if obj.len >= max_line_len - 20], key=lambda line : line.ys)[-1]
                        #if "-lyh" in job.name and worklayer == "l12":                            
                            #job.PAUSE(str([count, imp_info]))
                        if (count > 2 and imp_info == "differential") or \
                           (count > 1 and imp_info == "single-ended"):
                            if ymax - ymin > (orig_width * 2 + orig_spacing) * 0.0254 + 0.1 and "-lyh" not in job.name:
                                all_line_cmd = gClasses.Layer(icg_step, worklayer)
                                all_line_feat_out = all_line_cmd.featSelOut(units="mm")["lines"]                                
                                all_line_len = [obj.len for obj in all_line_feat_out]
                                max_line_len = max(all_line_len)
                                # 有绕线的阻抗情况
                                icg_step.selectNone()
                                #icg_step.resetFilter()
                                #icg_step.setAttrFilter(".string,text={0}*{1}".format(width_spacing.replace("/", "_*"), ohm))
                                #icg_step.setSymbolFilter(symbol)
                                #icg_step.selectAll()
                                #if not icg_step.featureSelected():
                                icg_step.COM("filter_atr_reset")
                                icg_step.filter_set(feat_types='line', polarity='positive')                              
                                icg_step.setSymbolFilter(symbol)
                                if icg_step.isLayer(worklayer + "_check_line_pad"):                                        
                                    icg_step.refSelectFilter(worklayer + "_check_line_pad", mode="touch")
                                    if icg_step.featureSelected():
                                        icg_step.selectNone()
                                        icg_step.refSelectFilter(worklayer + "_check_line_pad", mode="disjoint")
                                    
                                if not icg_step.featureSelected():
                                    icg_step.filter_set(feat_types='line', polarity='positive')
                                    icg_step.COM("filter_set,filter_name=popup,update_popup=yes,slot=line,"
                                                 "slot_by=length\;angle,min_len={0},max_len={1},"
                                                 "min_angle=0,max_angle=0".format(max_line_len-3, max_line_len+1))                                      
                                    icg_step.selectSymbol(symbol)
                                
                                if icg_step.featureSelected():
                                    xmin, ymin, xmax, ymax = get_layer_selected_limits(icg_step, worklayer)
                                else:
                                    continue                        
                            
                        icg_step.copyToLayer(worklayer + "_check_line_pad")                                
                        icg_step.clearAll()
                        icg_step.affect(worklayer + "_check_line_pad")
                        
                        coor_x = (xmin + xmax) * 0.5
                        coor_y = (ymin + ymax) * 0.5
                        #if "-lyh" in job.name:                            
                            #if imp_info == "differential":
                                #coor_x = (select_max_line.xe + select_max_line.xs) * 0.5
                                #coor_y = select_max_line.ys - float(select_max_line.symbol[1:])* 0.5 * 0.001 - 0.05
                            #else:
                                #coor_x = (select_max_line.xe + select_max_line.xs) * 0.5
                                #coor_y = select_max_line.ys                    
                            
                        if dic_layer_mirror.get(worklayer) == "no":
                            mianci = "C"
                        else:
                            mianci = "S"
                        
                        new_orig_width = 0
                        new_orig_spacing = 0
                        coortype_name = None
                        for key, value in dic_pcs_coortype_name.iteritems():
                            if key == worklayer:
                                for line in value:
                                    if "zk_t" in line[4]:
                                        if (abs(orig_width - line[1]) < 0.01 and abs(orig_spacing - line[2]) < 0.01):
                                            coortype_name = line[0]
                                            new_orig_width = line[1]
                                            new_orig_spacing = line[2]
                                            if "-" not in coortype_name:                                                
                                                break
                                            
                        if coortype_name is None:
                            for key, value in dic_pcs_coortype_name.iteritems():
                                if key == worklayer:
                                    for line in value:
                                        if "zk_t" in line[4]:
                                            if (abs(orig_width - line[6]) < 0.01 and abs(orig_spacing - line[7]) < 0.01) :
                                                coortype_name = line[0]
                                                new_orig_width = line[1]
                                                new_orig_spacing = line[2]
                                                if "-" not in coortype_name:                                                
                                                    break                                                
                                    
                        #if ohm in ["85", "90"] and worklayer == "l3":
                            #icg_step.PAUSE(str([orig_width, orig_spacing, new_orig_width, new_orig_spacing, width_spacing, coortype_name, ohm, 1]))                                      
                        if coortype_name is None:
                            for key, value in dic_pcs_coortype_name.iteritems():
                                if key == worklayer:
                                    for line in value:
                                        if "zk_t" in line[4]:
                                            if (abs(orig_width - line[8]) < 0.01 and abs(orig_spacing - line[9]) < 0.01):
                                                coortype_name = line[0]
                                                new_orig_width = line[1]
                                                new_orig_spacing = line[2]
                                                if "-" not in coortype_name:                                                
                                                    break           
                        #if ohm in ["85", "90"] and worklayer == "l3":
                            #icg_step.PAUSE(str([new_orig_width, new_orig_spacing, width_spacing, coortype_name, ohm, 2]))                                  
                        if coortype_name is None:
                            for key, value in dic_pcs_coortype_name.iteritems():
                                if key == worklayer:
                                    for line in value:
                                        if "zk_t" in line[4]:
                                            if float(line[3]) == float(ohm) and "&".join(ref_layer).upper() in line[5]:
                                                coortype_name = line[0]
                                                new_orig_width = line[1]
                                                new_orig_spacing = line[2]                                                
                                                if "-" not in coortype_name:                                                
                                                    break
                                            
                        if coortype_name is None and "-lyh" in job.name:
                            print(dic_pcs_coortype_name[worklayer], worklayer, "&".join(ref_layer).upper(),width_spacing,ohm)
                            job.PAUSE("ddd")                            
                            
                        if coortype_name is None:
                            continue
                        else:
                            orig_width = new_orig_width
                            orig_spacing = new_orig_spacing
                        
                        exists_text.append(text_info)
                        icg_measure_name = "{0}-{1}".format(mianci, coortype_name)
                        icg_num += 1
                        #if imp_info == "single-ended":                            
                            #icg_measure_name = "{0}-{1}".format(mianci, s_num)
                            #if icg_num > 1:
                                #icg_measure_name = "{0}-{1}".format(mianci, s_num)
                                
                            ## s_num += 1
                        #else:
                            #icg_measure_name = "{0}-{1}".format(mianci, d_num)
                            #if icg_num > 1:
                                #icg_measure_name = "{0}-{1}".format(mianci, d_num)
                                
                            # d_num += 1                            
                        
                        point_attr = 'zy_mark_info_{4}_{5}_zk_t_{0}_{1}_{2}_{3}'.format(coor_type,                                                                                                  
                                                                                        icg_measure_name, orig_width, orig_spacing,
                                                                                        coor_x, coor_y, 
                                                                                        )
                        icg_step.addAttr(".string", attrVal=point_attr, valType='text')
                        icg_step.addPad(coor_x, coor_y, "r{0}".format((orig_width+orig_spacing) *25.4), attributes="yes")
                        
                        ref_layer = [x.upper() for x in ref_layer]                          
                        for dic_erp_zk_info in array_erp_zk_line_tolerance_info:
                            if worklayer == dic_erp_zk_info[u"层名".encode("utf8")].lower() and \
                               float(ohm) == dic_erp_zk_info[u"阻值".encode("utf8")] and \
                               ("&".join(ref_layer) == dic_erp_zk_info[u"参考层".encode("utf8")] or \
                                "&".join(ref_layer[::-1]) == dic_erp_zk_info[u"参考层".encode("utf8")]):                            
                                self.dic_zk_calc_tolerance_info[point_attr] = [dic_erp_zk_info[u"阻抗线公差正".encode("utf8")],
                                                                               dic_erp_zk_info[u"阻抗线公差负".encode("utf8")]]                        
                
                if icg_step.isLayer(worklayer + "_check_line_pad"):                    
                    icg_step.clearAll()
                    icg_step.affect(worklayer+"_check_line_pad")
                    icg_step.resetFilter()
                    icg_step.setAttrFilter(".string,text=zy_mark_info*")
                    icg_step.selectAll()                    
                    if icg_step.featureSelected():
                        layer_cmd = gClasses.Layer(icg_step, worklayer+"_check_line_pad")
                        feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]                        
                        for obj in feat_out:
                            icg_step.selectNone()
                            icg_step.selectFeatureIndex(worklayer+"_check_line_pad", obj.feat_index)
                            if icg_step.featureSelected():
                                icg_step.resetFilter()
                                icg_step.COM("sel_ref_feat,layers=,use=select,mode=touch,\
                                pads_as=shape,f_types=line\;pad\;surface\;arc\;text,\
                                polarity=positive\;negative,include_syms=,exclude_syms=")
                                if icg_step.featureSelected():
                                    icg_step.addAttr(".string", attrVal="check_"+obj.string, valType='text', change_attr="yes")          
                
                if len(exists_text) != len(zk_text_info):
                    log = u"{0} {1} 阻值未全部匹配{2} {3}，请手动制作缺少部分量测坐标资料!".format(stepname, worklayer, len(exists_text), len(zk_text_info))
                    message_info.append(log)
                    
        if icg_num == 0:
            for key, value in dic_pcs_coortype_name.iteritems():
                log = ""
                for zk in value:
                    if zk[4] == "zk_t":
                        log = u"erp有阻抗信息，但型号内未发现阻抗条信息，请手动制作量测坐标资料!"
                
                if log:                    
                    message_info.append(log)
                    break
        
        return message_info
    
    def create_icg_coordinate_attr(self, signalLayers,
                              array_erp_zk_line_tolerance_info,
                              dic_pcs_coortype_name,
                              dic_layer_mirror):
        """阻抗条坐标提取"""
        #阻抗条坐标提取
        icg_num = 0
        message_info = []
        
        for stepname in matrixInfo["gCOLstep_name"]:
            if "icg" not in stepname:
                continue         
            
            icg_step = gClasses.Step(job, stepname)
            icg_step.open()
            icg_step.COM("units,type=mm")
            for worklayer in signalLayers:
                layer_cmd = gClasses.Layer(icg_step, worklayer)
                text_feat_out = layer_cmd.featout_dic_Index(units="mm")["text"]
                line_feat_out = layer_cmd.featout_dic_Index(units="mm")["lines"]
                zk_text_info = list(set([obj.text for obj in text_feat_out if "OHM" in obj.text]))
                zk_line_info = [obj for obj in line_feat_out if getattr(obj, "imp_info", None) is not None
                                and obj.angle in [0, 180]]
                if "b13" == job.name[1:4]:
                    zk_line_info = [obj for obj in line_feat_out if getattr(obj, "imp_info", None) is not None
                                    and obj.angle in [80, 100]]
                    
                line_symbols = sorted(list(set([obj.symbol for obj in zk_line_info])), key=lambda x: float(x[1:]))
                zk_text_info = sorted(zk_text_info, key=lambda x: float(x.split(" ")[3].split("/")[0]))                

                line_symbols = []
                for obj in zk_line_info:
                    line_info = [obj.symbol, getattr(obj, "imp_info", None), getattr(obj, "string", None)]
                    if line_info not in line_symbols:
                        line_symbols.append(line_info)
                        
                # line_symbols = sorted([symbol for symbol,attr,_ in line_symbols], key=lambda x: float(x[1:]))
                    
                # job.PAUSE(str([worklayer, line_symbols,  [obj.angle for obj in line_feat_out]]))
                # 计算补偿值以备验证
                # bc_value = []
                s_num = 1
                d_num = 1
                exists_text = []
                # for symbol, text_info in zip(line_symbols, zk_text_info):
                for symbol_info in line_symbols:
                    symbol, imp_info, attr = symbol_info
                    #if "L13&L113.20/4.12" in text_info :
                        #text_info = "L12 REF L13&L11 3.20/4.12 85 OHM"
                    # _, _, ref_layer,width_spacing,ohm,_ = text_info.split()
                    # symbol, attr = symbol_info
                    #if "&" in ref_layer:
                        #ref_layer = ref_layer.lower().split("&")
                    #else:
                        #ref_layer = [ref_layer.lower()]
                    
                    orig_width, orig_spacing, _, ohm = attr.split("_")
                    orig_spacing = float(orig_spacing)
                    orig_width = float(orig_width)
                    #orig_width = float(width_spacing.split("/")[0])
                    #orig_spacing = 0
                    # bc_value.append(float(symbol[1:]) - line_width)
                    # if "/" in width_spacing and width_spacing.count("/") >= 1:
                    if orig_spacing > 0:                        
                        imp_info = "differential"
                        coor_type = "linewidth_space"                           
                    else:
                        imp_info = "single-ended"
                        coor_type = "linewidth"
                        
                    icg_step.clearAll()
                    icg_step.affect(worklayer)
                    icg_step.resetFilter()
                    icg_step.filter_set(feat_types='line', polarity='positive')
                    icg_step.setAttrFilter(".imp_info,text={0}".format(imp_info))
                    if "b13" == job.name[1:4]:
                        pass
                        #icg_step.COM("filter_set,filter_name=popup,update_popup=yes,slot=line,"
                                     #"slot_by=length\;angle,min_len={0},max_len={1},"
                                     #"min_angle=0,max_angle=0".format(8, 20))
                    else:
                        icg_step.COM("filter_set,filter_name=popup,update_popup=yes,slot=line,"
                                     "slot_by=length\;angle,min_len={0},max_len={1},"
                                     "min_angle=0,max_angle=0".format(10, 200))                    
                        icg_step.COM("filter_set,filter_name=popup,update_popup=yes,slot=line,slot_by=angle,min_angle=0,max_angle=0")
                        
                    icg_step.setAttrFilter(".string,text={0}".format(attr))
                    # icg_step.setSymbolFilter(symbol)
                    icg_step.selectAll()
                    count = icg_step.featureSelected()
                    if not count and "-lyh" in job.name:
                        icg_step.PAUSE("please select line")
                        count = icg_step.featureSelected()
                    
                    if count:                        
                        xmin, ymin, xmax, ymax = get_layer_selected_limits(icg_step, worklayer)
                        all_line_cmd = gClasses.Layer(icg_step, worklayer)
                        all_line_feat_out = all_line_cmd.featSelOut(units="mm")["lines"]
                        all_line_len = [obj.len for obj in all_line_feat_out]
                        max_line_len = max(all_line_len)                        
                        select_max_line = sorted([obj for obj in all_line_feat_out
                                                  if obj.len >= max_line_len - 2], key=lambda line : line.ys)[-1]
                        #if "-lyh" in job.name and worklayer == "l1":                            
                            #job.PAUSE(str([count, imp_info, attr]))
                        if (count > 2 and imp_info == "differential") or \
                           (count > 1 and imp_info == "single-ended"):
                            if ymax - ymin > (orig_width * 2 + orig_spacing) * 0.0254 + 0.1 and "b13" != job.name[1:4]:
                                all_line_cmd = gClasses.Layer(icg_step, worklayer)
                                all_line_feat_out = all_line_cmd.featSelOut(units="mm")["lines"]                                
                                all_line_len = [obj.len for obj in all_line_feat_out]
                                max_line_len = max(all_line_len)
                                # 有绕线的阻抗情况
                                icg_step.selectNone()
                                #icg_step.resetFilter()
                                #icg_step.setAttrFilter(".string,text={0}*{1}".format(width_spacing.replace("/", "_*"), ohm))
                                #icg_step.setSymbolFilter(symbol)
                                #icg_step.selectAll()
                                #if not icg_step.featureSelected():
                                icg_step.COM("filter_atr_reset")
                                icg_step.filter_set(feat_types='line', polarity='positive')                              
                                icg_step.setSymbolFilter(symbol)
                                if icg_step.isLayer(worklayer + "_check_line_pad"):                                        
                                    icg_step.refSelectFilter(worklayer + "_check_line_pad", mode="touch")
                                    if icg_step.featureSelected():
                                        icg_step.selectNone()
                                        icg_step.refSelectFilter(worklayer + "_check_line_pad", mode="disjoint")
                                    
                                if not icg_step.featureSelected():
                                    icg_step.filter_set(feat_types='line', polarity='positive')
                                    icg_step.COM("filter_set,filter_name=popup,update_popup=yes,slot=line,"
                                                 "slot_by=length\;angle,min_len={0},max_len={1},"
                                                 "min_angle=0,max_angle=0".format(max_line_len-3, max_line_len+1))                                      
                                    icg_step.selectSymbol(symbol)
                                
                                if icg_step.featureSelected():
                                    xmin, ymin, xmax, ymax = get_layer_selected_limits(icg_step, worklayer)
                                else:
                                    continue                        
                            
                        icg_step.copyToLayer(worklayer + "_check_line_pad")                                
                        icg_step.clearAll()
                        icg_step.affect(worklayer + "_check_line_pad")
                        
                        coor_x = (xmin + xmax) * 0.5
                        coor_y = (ymin + ymax) * 0.5
                        #if "-lyh" in job.name:
                        if "b13" == job.name[1:4]:
                            if imp_info == "differential":
                                coor_x = (select_max_line.xe + select_max_line.xs) * 0.5
                                coor_y = (select_max_line.ye + select_max_line.ys) * 0.5 - float(select_max_line.symbol[1:])* 0.5 * 0.001 - 0.05
                            else:
                                coor_x = (select_max_line.xe + select_max_line.xs) * 0.5
                                coor_y = (select_max_line.ye + select_max_line.ys) * 0.5         
                            
                        if dic_layer_mirror.get(worklayer) == "no":
                            mianci = "C"
                        else:
                            mianci = "S"
                        
                        new_orig_width = 0
                        new_orig_spacing = 0
                        coortype_name = None
                        for key, value in dic_pcs_coortype_name.iteritems():
                            if key == worklayer:
                                for line in value:
                                    if "zk_t" in line[4]:
                                        if (abs(orig_width - line[1]) < 0.01 and abs(orig_spacing - line[2]) < 0.01):
                                            coortype_name = line[0]
                                            new_orig_width = line[1]
                                            new_orig_spacing = line[2]
                                            if "-" not in coortype_name:                                                
                                                break
                                            
                        if coortype_name is None:
                            for key, value in dic_pcs_coortype_name.iteritems():
                                if key == worklayer:
                                    for line in value:
                                        if "zk_t" in line[4]:
                                            if (abs(orig_width - line[6]) < 0.01 and abs(orig_spacing - line[7]) < 0.01) :
                                                coortype_name = line[0]
                                                new_orig_width = line[1]
                                                new_orig_spacing = line[2]
                                                if "-" not in coortype_name:                                                
                                                    break                                                
                                    
                        #if ohm in ["85", "90"] and worklayer == "l3":
                            #icg_step.PAUSE(str([orig_width, orig_spacing, new_orig_width, new_orig_spacing, width_spacing, coortype_name, ohm, 1]))                                      
                        if coortype_name is None:
                            for key, value in dic_pcs_coortype_name.iteritems():
                                if key == worklayer:
                                    for line in value:
                                        if "zk_t" in line[4]:
                                            if (abs(orig_width - line[8]) < 0.01 and abs(orig_spacing - line[9]) < 0.01):
                                                coortype_name = line[0]
                                                new_orig_width = line[1]
                                                new_orig_spacing = line[2]
                                                if "-" not in coortype_name:                                                
                                                    break           
                        #if ohm in ["85", "90"] and worklayer == "l3":
                            #icg_step.PAUSE(str([new_orig_width, new_orig_spacing, width_spacing, coortype_name, ohm, 2]))
                        
                        if  "-lyh" in job.name or job.name.upper() in ["HB1312PHA55A1"]:
                            if coortype_name is None:
                                for key, value in dic_pcs_coortype_name.iteritems():
                                    if key == worklayer:
                                        for line in value:
                                            if "zk_t" in line[4]:
                                                if float(line[3]) == float(ohm):
                                                    coortype_name = line[0]
                                                    new_orig_width = line[1]
                                                    new_orig_spacing = line[2]                                                
                                                    if "-" not in coortype_name:                                                
                                                        break                            
                                                
                        if coortype_name is None and "-lyh" in job.name:
                            print(dic_pcs_coortype_name[worklayer], worklayer,ohm)
                            job.PAUSE("error")                            
                            
                        if coortype_name is None:
                            continue
                        else:
                            orig_width = new_orig_width
                            orig_spacing = new_orig_spacing
                        
                        exists_text.append(attr)
                        icg_measure_name = "{0}-{1}".format(mianci, coortype_name)
                        icg_num += 1
                        #if imp_info == "single-ended":                            
                            #icg_measure_name = "{0}-{1}".format(mianci, s_num)
                            #if icg_num > 1:
                                #icg_measure_name = "{0}-{1}".format(mianci, s_num)
                                
                            ## s_num += 1
                        #else:
                            #icg_measure_name = "{0}-{1}".format(mianci, d_num)
                            #if icg_num > 1:
                                #icg_measure_name = "{0}-{1}".format(mianci, d_num)
                                
                            # d_num += 1                            
                        
                        point_attr = 'zy_mark_info_{4}_{5}_zk_t_{0}_{1}_{2}_{3}'.format(coor_type,                                                                                                  
                                                                                        icg_measure_name, orig_width, orig_spacing,
                                                                                        coor_x, coor_y, 
                                                                                        )
                        icg_step.addAttr(".string", attrVal=point_attr, valType='text')
                        icg_step.addPad(coor_x, coor_y, "r{0}".format((orig_width+orig_spacing) *25.4), attributes="yes")
                        
                        #ref_layer = [x.upper() for x in ref_layer]                          
                        #for dic_erp_zk_info in array_erp_zk_line_tolerance_info:
                            #if worklayer == dic_erp_zk_info[u"层名".encode("utf8")].lower() and \
                               #float(ohm) == dic_erp_zk_info[u"阻值".encode("utf8")] and \
                               #("&".join(ref_layer) == dic_erp_zk_info[u"参考层".encode("utf8")] or \
                                #"&".join(ref_layer[::-1]) == dic_erp_zk_info[u"参考层".encode("utf8")]):                            
                                #self.dic_zk_calc_tolerance_info[point_attr] = [dic_erp_zk_info[u"阻抗线公差正".encode("utf8")],
                                                                               #dic_erp_zk_info[u"阻抗线公差负".encode("utf8")]]                        
                
                if icg_step.isLayer(worklayer + "_check_line_pad"):                    
                    icg_step.clearAll()
                    icg_step.affect(worklayer+"_check_line_pad")
                    icg_step.resetFilter()
                    icg_step.setAttrFilter(".string,text=zy_mark_info*")
                    icg_step.selectAll()                    
                    if icg_step.featureSelected():
                        layer_cmd = gClasses.Layer(icg_step, worklayer+"_check_line_pad")
                        feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]                        
                        for obj in feat_out:
                            icg_step.selectNone()
                            icg_step.selectFeatureIndex(worklayer+"_check_line_pad", obj.feat_index)
                            if icg_step.featureSelected():
                                icg_step.resetFilter()
                                icg_step.COM("sel_ref_feat,layers=,use=select,mode=touch,\
                                pads_as=shape,f_types=line\;pad\;surface\;arc\;text,\
                                polarity=positive\;negative,include_syms=,exclude_syms=")
                                if icg_step.featureSelected():
                                    icg_step.addAttr(".string", attrVal="check_"+obj.string, valType='text', change_attr="yes")          
                
                if len(exists_text) != len(zk_text_info):
                    log = u"{0} {1} 阻值未全部匹配{2} {3}，请手动制作缺少部分量测坐标资料!".format(stepname, worklayer, len(exists_text), len(zk_text_info))
                    message_info.append(log)
                    
        if icg_num == 0:
            for key, value in dic_pcs_coortype_name.iteritems():
                log = ""
                for zk in value:
                    if zk[4] == "zk_t":
                        log = u"erp有阻抗信息，但型号内未发现阻抗条信息，请手动制作量测坐标资料!"
                
                if log:                    
                    message_info.append(log)
                    break
        
        return message_info
    
    def get_mysql_data_modify(self, infos):
        tmps = ""
        try:
            tmpt = infos.replace('": ','": \n').replace('", ','" \n,').replace(', "',', \n"').replace('"}','"\n}').replace('", [','"\n, [').replace('"],','"\n],').split('\n')
        except:
            tmpt = ""
        ccc = 0
        for iii in tmpt:
            zzz = 0
            for nnn in iii:
                if nnn in ('"', "'"):
                    zzz += 1
            if zzz > 2:
                vvv = ""
                zvv = 0
                for nnn in iii:
                    nvv = nnn
                    if nnn in ('"', "'"):
                        zvv += 1
                        if zvv in (1,zzz):
                            nvv = nnn
                        elif zvv % 2:
                            nvv = '”'
                        else:
                            nvv = '“'
                    vvv += nvv
            else:
                vvv = iii
            tmps += vvv
            ccc += len(iii)
        tmp = {}
        if len(tmps) == ccc:
            try:
                tmp = eval(tmps)
            except:
                tmp = {}
        return tmp    
                
    def create_ui_params(self):
        """创建界面参数"""        
        self.setWindowFlags(Qt.Qt.Window | Qt.Qt.WindowStaysOnTopHint)    
        self.setObjectName("mainWindow")
        self.titlelabel = QtGui.QLabel(u"参数确认")
        self.titlelabel.setStyleSheet("QLabel {color:red}")
        self.setGeometry(700, 300, 0, 0)
        self.resize(800, 500)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.titlelabel.setFont(font)        
    
        self.dic_editor = {}
        self.dic_label = {}
    
        # arraylist1 = [{u"单位": "QComboBox"},]
        arraylist1 = []

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
        main_layout.addWidget(widget1,1,0,1,10)
        # main_layout.addWidget(self.tableWidget1,2,0,1,2)
        main_layout.addWidget(self.tableWidget2,2,0,1,10)
        main_layout.addLayout(btngroup_layout, 8, 0,1, 10)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(main_layout)
    
        # main_layout.setSizeConstraint(Qt.QLayout.SetFixedSize)
    
        self.pushButton.clicked.connect(self.create_text_file)
        self.pushButton1.clicked.connect(sys.exit)
        self.pushButton2.clicked.connect(self.reloading_data)
    
        self.setWindowTitle(u"公差信息确认%s" % __version__)
        self.setMainUIstyle()
        
        #self.setTableWidget(self.tableWidget1, [u"钻带", u"最小孔径(mil)"])
        self.setTableWidget(self.tableWidget2, [u"勾选", u"层名", u"最小线宽公差(mil)",
                                                u"smd公差(mil)",u"bga公差(mil)",u"阻抗线公差(mil)",
                                                u"最小线补偿(mil)",u"阻抗线补偿(mil)" ])
        #self.tableWidget1.setEnabled(False)
        #self.tableWidget2.setEnabled(False)
        self.tableItemDelegate = itemDelegate(self)
        self.tableWidget2.setItemDelegateForColumn(0, self.tableItemDelegate)
        # self.connect(self.tableItemDelegate, QtCore.SIGNAL("select_item(PyQt_PyObject,PyQt_PyObject)"), self.order_coupon_step)
        
        self.initial_value()
        
    def initial_value(self):
        """初始化参数"""
        #for item in ["inch", u"mm"]:
            #self.dic_editor[u"单位"].addItem(item)
            
        self.add_data_to_table()        
            
    def reloading_data(self):
        self.setValue()
        if not os.path.exists(tolerance_info):
            showMessageInfo(u"未发现上次有保存记录!")
            
    def add_data_to_table(self):
        """表格内加载数据"""

        arraylist = []
        dic_net_mark_info, dic_profile_info = self.get_mysql_data()
        if dic_profile_info is None:
            return dic_net_mark_info        
        if job.name[1:4] in ["a86", "d10"]:
            tolerance = "0.1"
            compensate_value = "0.2"
        else:
            tolerance = "0.15"
            compensate_value = "0.3"
            
        for layer, array_coor_info in dic_net_mark_info.iteritems():
            if layer.lower() not in signalLayers:
                continue
            if array_coor_info: 
                arraylist.append(["0", layer, tolerance, tolerance, tolerance, tolerance, compensate_value, compensate_value])
        
        # self.set_model_data(self.tableWidget1, arraylist)
        
        # self.dic_layer_info = self.get_layer_pad_ring_line_width()
        #arraylist = []
        #for key in sorted(self.dic_layer_info.keys(), key=lambda x: int(x[1:])):
            #arraylist.append([key]+ self.dic_layer_info[key])
            
        self.set_model_data(self.tableWidget2, sorted(arraylist, key=lambda x: int(x[1][1:])))        
        
    def set_model_data(self, table, data_info):
        """设置表内数据"""
        model = table.model()            
        model.setRowCount(len(data_info))
        for i, array_info in enumerate(data_info):
            for j , data in enumerate(array_info):                
                index = model.index(i,j, QtCore.QModelIndex())
                model.setData(index, data)
                if table == self.tableWidget2:
                    if j == 0:
                        self.tableWidget2.openPersistentEditor(index)
                        if data == "1":
                            self.tableItemDelegate.dic_editor[i, j].setCheckState(2)
                        else:
                            self.tableItemDelegate.dic_editor[i, j].setCheckState(0)
                            
                #内层无smd bga
                if array_info[1] not in outsignalLayers:
                    if j in [3, 4]:
                        item = model.item(i, j)
                        item.setFlags(item.flags() & ~Qt.Qt.ItemIsEditable)                        

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
        table.setColumnWidth(1, 60)
        table.setColumnWidth(2, 130)
        table.setColumnWidth(3, 100)
        table.setColumnWidth(4, 100)
        table.setColumnWidth(5, 110)
        table.setColumnWidth(6, 110)

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
        if os.path.exists(tolerance_info):
            with open(tolerance_info) as file_obj:
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
                
            if self.dic_hct_info.get(u"层及公差"):
                self.set_model_data(self.tableWidget2, self.dic_hct_info[u"层及公差"])
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
            showMessageInfo(u"层名{0} 最小孔径不存在，请检查层名跟界面列表内的命名是否一致！".format(drill_layer))
            sys.exit()
        
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
                
                
        #arraylist = [u"上公差(um)", u"下公差(um)"]
        
        #for key in arraylist:
            #if self.dic_item_value.has_key(key):
                #try:
                    #self.dic_item_value[key] = float(self.dic_item_value[key])
                #except:
                    #if "manual" in sys.argv[1:]:  
                        #QtGui.QMessageBox.information(self, u'提示', u'检测到 %s 参数[ %s ]为空或非法数字,请检查~' % (
                            #key, self.dic_item_value[key]), 1)
                        
                    #return 0                
                                  
        #self.dic_item_value[u"最小孔径"] = []
        #model = self.tableWidget1.model()
        #for row in range(model.rowCount()):
            #arraylist = []
            #for col in range(model.columnCount()):
                #value = str(model.item(row, col).text())
                #if col <> 0:
                    #try:
                        #float(value)
                    #except:
                        #QtGui.QMessageBox.information(self, u'提示', u'检测到 %s 最小孔 有参数[ %s ]为空或非法数字,请检查~' % (
                            #model.item(row, 0).text(), value), 1)
                        ## return 0
                        #sys.exit()
                #arraylist.append(value)
                
            #self.dic_item_value[u"最小孔径"].append(arraylist)         
            
        self.dic_item_value[u"层及公差"] = []
        model = self.tableWidget2.model()
        for row in range(model.rowCount()):
            arraylist = []
            for col in range(model.columnCount()):
                value = str(model.item(row, col).text())
                if col > 1:
                    try:
                        float(value)
                    except:
                        QtGui.QMessageBox.information(self, u'提示', u'检测到 %s 层及公差 有参数[ %s ]为空或非法数字,请检查~' % (
                            model.item(row, 0).text(), value), 1)
                        return 0
                arraylist.append(value)
                
            self.dic_item_value[u"层及公差"].append(arraylist)            

        with open(tolerance_info, 'w') as file_obj:
            json.dump(self.dic_item_value, file_obj)

        return 1   

if __name__ == "__main__":
    main = measure_coordinate()
    main.create_ui_params()
    main.show()
    sys.exit(app.exec_())