#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__    = "20230329"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""全流程追溯二维码添加 """

import os
import sys
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")

import json
from genesisPackages import get_profile_limits,get_sr_area_for_step_include, \
     top, signalLayers,matrixInfo, addFeatures,\
     auto_add_features_in_panel_edge_new, outsignalLayers, \
     convert_coordinate_in_panel_edge, lay_num, get_sr_area_flatten, \
     innersignalLayers

import gClasses
addfeature = addFeatures()

from get_erp_job_info import get_inplan_mrp_info
from create_ui_model import showMessageInfo, \
     showQuestionMessageInfo
from send_html_request import post_message

import MySQL_DB
conn = MySQL_DB.MySQL()
dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                           username='root', passwd='k06931!')

stepname = top.currentStep()
jobname = top.currentJob()

dic_symbol_info = {}
symbol_info_path = "/incam/server/site_data/library/symbol_info.json"
if not os.path.exists(symbol_info_path):
    symbol_info_path = os.path.join(os.path.dirname(sys.argv[0]), "symbol_info.json")
    
if os.path.exists(symbol_info_path):
    with open(symbol_info_path) as file_obj:
        dic_symbol_info = json.load(file_obj)
        
def only_uploading_data(jobname, stepname):
    job = gClasses.Job(jobname)
    step = gClasses.Step(job, stepname)
    step.open()
    step.COM("units,type=mm")
    f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
    
    array_mrp_info = get_inplan_mrp_info(jobname)    
    if not array_mrp_info:
        showMessageInfo(u"无法获取此型号在inplan中的叠构信息，请检查型号是否正确！")
        return
    
    out_lb_x = 0
    out_lb_y = 0
    out_lb_sec_x = 0
    out_lb_sec_y = 0
    all_sec_rout_x = []
    all_sec_rout_y = []
    for dic_info in sorted(array_mrp_info, key=lambda x: x["PROCESS_NUM"]):
        mrp_name = dic_info["MRPNAME"]
        pnl_routx = round(dic_info["PNLROUTX"] * 25.4, 3)
        pnl_routy = round(dic_info["PNLROUTY"] * 25.4, 3)
        if "-" in mrp_name:
            all_sec_rout_x.append((f_xmax - pnl_routx) * 0.5)
            all_sec_rout_y.append((f_ymax - pnl_routy) * 0.5)
        else:                
            out_lb_x = (f_xmax - pnl_routx) * 0.5
            out_lb_y = (f_ymax - pnl_routy) * 0.5
                
    # 取几次锣边的平均值
    if all_sec_rout_x:
        out_lb_sec_x = float(sum(all_sec_rout_x)) / len(all_sec_rout_x)
        
    if all_sec_rout_y:
        out_lb_sec_y = float(sum(all_sec_rout_y)) / len(all_sec_rout_y)
        
    x_center = (f_xmin + f_xmax) * 0.5
    y_center = (f_ymin + f_ymax) * 0.5
    uploading_barcode_coordinate_info(jobname, step, x_center, y_center, out_lb_x, out_lb_y, out_lb_sec_x, out_lb_sec_y)
    
def check_exists_barcode_symbol(step):
    worklayer = outsignalLayers[0]
    step.clearAll()
    step.affect(worklayer)
    step.resetFilter()
    step.setAttrFilter(".bit,text=trace_barcode")
    step.selectAll()
    if step.featureSelected():
        res = showQuestionMessageInfo(u"检测到板边已添加过追溯二维码，是否删除旧的重新添加！")
        if not res:
            step.clearAll()
            sys.exit()
        
        step.clearAll()
        for layer in signalLayers:
            step.affect(layer)
        step.resetFilter()
        step.setAttrFilter(".bit,text=trace_barcode")
        step.selectAll()
        if step.featureSelected():
            step.selectDelete()
        
        step.clearAll()

def add_barcode_area(jobname, stepname):
    """全流程追溯二维码逻辑 内层需要有两个位置，一个给压合后扫码内层信息，一个为当前层次扫码
    压合后跟外层共一个位置，都只供当前层次扫码使用，用完后就没什么作用。"""    
    job = gClasses.Job(jobname)
    step = gClasses.Step(job, stepname)
    step.open()
    step.COM("units,type=mm")
    f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
    rect= get_sr_area_for_step_include(stepname, include_sr_step=["edit", "set", "icg"])
    sr_xmin = min([min(x1, x2) for x1, y1, x2, y2 in rect])    
    sr_ymin = min([min(y1, y2) for x1, y1, x2, y2 in rect])   
    sr_xmax = max([max(x1, x2) for x1, y1, x2, y2 in rect])    
    sr_ymax = max([max(y1, y2) for x1, y1, x2, y2 in rect])  
    
    array_mrp_info = get_inplan_mrp_info(jobname, "1=1")
    
    if not array_mrp_info:
        showMessageInfo(u"无法获取此型号在inplan中的叠构信息，请检查型号是否正确！")
        return    
    
    check_exists_barcode_symbol(step)
    
    get_sr_area_flatten("fill", get_sr_step=True)
    
    dic_inner_zu = {}
    dic_sec_zu = {}
    dic_outer_zu = {}
    out_lb_x = 0
    out_lb_y = 0
    out_lb_sec_x = 0
    out_lb_sec_y = 0
    all_sec_rout_x = []
    all_sec_rout_y = []
    for dic_info in sorted(array_mrp_info, key=lambda x: x["PROCESS_NUM"]):
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
                all_sec_rout_x.append((f_xmax - pnl_routx) * 0.5)
                all_sec_rout_y.append((f_ymax - pnl_routy) * 0.5)
            else:
                if not dic_outer_zu.has_key(process_num):
                    dic_outer_zu[process_num] = []                    
                dic_outer_zu[process_num].append([mrp_name, top_layer, bot_layer, pnl_routx, pnl_routy, 0])
                
                out_lb_x = (f_xmax - pnl_routx) * 0.5
                out_lb_y = (f_ymax - pnl_routy) * 0.5
                
    # 取几次锣边的平均值
    if all_sec_rout_x:
        out_lb_sec_x = float(sum(all_sec_rout_x)) / len(all_sec_rout_x)
        
    if all_sec_rout_y:
        out_lb_sec_y = float(sum(all_sec_rout_y)) / len(all_sec_rout_y)          

    print array_mrp_info
    print dic_inner_zu
    next_position_num = 0
    symbol_width = 10.5
    symbol_length = 1
    dic_position = {}
    dic_negative_layer = {}
    core_layers = []
    core_bot_layers = []
    if dic_inner_zu:
        process_num = dic_inner_zu.keys()[0]
        core_layers += [value[1].lower() for value in dic_inner_zu.values()[0]]
        core_layers += [value[2].lower() for value in dic_inner_zu.values()[0]]
        print core_layers
        for num, value in enumerate(sorted(dic_inner_zu.values()[0], key=lambda x: x[0])):
            top_layer = value[1].lower()
            bot_layer = value[2].lower()            
            if num == 0:
                dic_inner_zu[process_num][0][5] = 1
                next_position_num = 1                
                if lay_num <= 2:
                    symbol_length += 9.5
                    # 双面板按外层来计算坐标
                    bar_type = "bar_code_out"
                    dic_position[next_position_num] = ("s10500", symbol_width / 2.0, symbol_length - 10.5 * 0.5, bar_type)
                    dic_negative_layer[next_position_num] = []
                else:
                    symbol_length += 9
                    bar_type = "bar_code_innerl2l3"
                    dic_position[next_position_num] = ("s9000", symbol_width / 2.0, 9 * 0.5, bar_type)
                    dic_negative_layer[next_position_num] = [lay for lay in core_layers if lay not in [top_layer]]
                    # 第一个芯板位置 次外层也要掏开
                    if dic_sec_zu:
                        for key, values in dic_sec_zu.iteritems():                        
                            for _, layer1, layer2, _, _, _ in values:
                                dic_negative_layer[next_position_num] += [layer1.lower(), layer2.lower()]
            else:
                dic_inner_zu[process_num][0][5] = 2
                next_position_num = 2 
                if not dic_negative_layer.has_key(next_position_num):
                    symbol_length += 15
                    dic_negative_layer[next_position_num] = []
                    
                dic_position[next_position_num] = ("s9000", symbol_width / 2.0, 9 * 0.5 + 2.5 + 10 + 2.5, "bar_code_sec")
                # dic_position[next_position_num] = ("s9000", symbol_width / 2.0, symbol_length - 0.5 - 2, "bar_code_sec")
                dic_negative_layer[next_position_num] += [bot_layer]
            
            # 双面板底层暂时不掏开 这里过滤掉
            if lay_num > 2:
                core_bot_layers.append(bot_layer)
    #print dic_position
    #print dic_inner_zu.values()[0]
    
    if dic_sec_zu:
        next_position_num = next_position_num + 1
        symbol_length = 34.5
        if len(core_layers) == 2:            
            symbol_length = 19.5
            
        dic_position[next_position_num] = ("s9000", symbol_width / 2.0, symbol_length - 10.5 * 0.5, "bar_code_sec")
        # dic_position[next_position_num] = ("s9000", symbol_width / 2.0, symbol_length / 2.0 + 2.5, "bar_code_sec")
        # 次外层底层也要掏开
        #for key, values in dic_sec_zu.iteritems():                        
            #for _, layer1, layer2, _, _, _ in values:
                #dic_negative_layer[next_position_num] += [layer2.lower()]
        dic_negative_layer[next_position_num] = core_layers
        for key in sorted(dic_sec_zu.keys()):
            dic_sec_zu[key][0][5] = next_position_num
            
    if dic_outer_zu:
        next_position_num = next_position_num + 1
        symbol_length = 34.5
        if len(core_layers) == 2:            
            symbol_length = 19.5
                
        dic_position[next_position_num] = ("s10500", symbol_width / 2.0, symbol_length - 10.5 * 0.5, "bar_code_out")
        # dic_position[next_position_num] = ("s10500", symbol_width / 2.0, symbol_length/2.0 + 2.5, "bar_code_out")
        dic_negative_layer[next_position_num] = core_layers
        for key in sorted(dic_outer_zu.keys()):
            dic_outer_zu[key][0][5] = next_position_num
    
    print dic_negative_layer
    print dic_position

    add_x = sr_xmin - 1 - 11.5 / 2.0# f_xmax - 30
    add_y = f_ymax/2.0 - symbol_length/2.0 - 2
    move_model_fx = "Y"
    angle = 0
    symbolname = "rect{0}x{1}".format(symbol_width*1000, symbol_length*1000)
    worklayer = "barcode_tmp"
    checklayer_list = signalLayers
    area_x = [sr_xmin - 1, f_xmin + out_lb_x, -0.25]
    area_y = [f_ymax/2.0,f_ymax / 2.0 - 100, -0.25]
    # area_y = [f_ymax/2.0,sr_ymin + 100, -0.25]
    #step.clearAll()
    #step.affect(worklayer)
    #step.addRectangle(area_x[0], area_y[0], area_x[1], area_y[1])
    #step.PAUSE("ddd")
    
    # 设备厂家沟通可以按单边添加 取消斜对称模式 先测试20230701 by lyh
    #coordinate_mode = u"斜对称转换"
    #msg = u"添加全流程追溯二维码失败，有接触到板边其他物件，请手动移动合适的位置，然后继续！".encode("cp936")
    #result = auto_add_features_in_panel_edge_new(step, add_x, add_y, worklayer,
                                                 #symbolname, checklayer_list,
                                                 #msg, 0, -1,  angle, 
                                                 #area_x=area_x, area_y=area_y,
                                                 #move_length=1, 
                                                 #move_model_fx=move_model_fx,
                                                 #to_sr_area=1, max_min_area_method="yes",
                                                 #dic_all_symbol_info=dic_symbol_info,
                                                 #manual_add="no", exclude_symbols=["r1"], 
                                                 #convert_coordinate_mode=u"斜对称转换")
    #if not result:
        #area_y = [f_ymax/2.0, f_ymax / 2.0 + 100, 0.25]      
        #result = auto_add_features_in_panel_edge_new(step, add_x, add_y, worklayer,
                                                     #symbolname, checklayer_list,
                                                     #msg, 0, 1,  angle, 
                                                     #area_x=area_x, area_y=area_y,
                                                     #move_length=1, 
                                                     #move_model_fx=move_model_fx,
                                                     #to_sr_area=1, max_min_area_method="yes",
                                                     #dic_all_symbol_info=dic_symbol_info,
                                                     #manual_add="no", exclude_symbols=["r1"], 
                                                     #convert_coordinate_mode=u"斜对称转换")
    #if not result:
    area_x = [sr_xmin - 1, f_xmin + out_lb_x, -0.25]
    area_y = [f_ymax/2.0,f_ymax / 2.0 - 100, -0.25]        
    coordinate_mode = u"单边添加"
    msg = u"添加全流程追溯二维码失败，有接触到板边其他物件，请手动移动合适的位置，然后继续！".encode("cp936")
    result = auto_add_features_in_panel_edge_new(step, add_x, add_y, worklayer,
                                                 symbolname, checklayer_list,
                                                 msg, 0, -1,  angle, 
                                                 area_x=area_x, area_y=area_y,
                                                 move_length=1, 
                                                 move_model_fx=move_model_fx,
                                                 to_sr_area=1, max_min_area_method="yes",
                                                 dic_all_symbol_info=dic_symbol_info,
                                                 manual_add="no", exclude_symbols=["r1"], 
                                                 convert_coordinate_mode=None)
    # add_position = u"panel下方"
    if not result:
        area_y = [f_ymax/2.0, f_ymax / 2.0 + 100, 0.25]   
        result = auto_add_features_in_panel_edge_new(step, add_x, add_y, worklayer,
                                                     symbolname, checklayer_list,
                                                     msg, 0, 1,  angle, 
                                                     area_x=area_x, area_y=area_y,
                                                     move_length=1, 
                                                     move_model_fx=move_model_fx,
                                                     to_sr_area=1, max_min_area_method="yes",
                                                     dic_all_symbol_info=dic_symbol_info,
                                                     manual_add="yes", exclude_symbols=["r1"], 
                                                     convert_coordinate_mode=None)
        # add_position = u"panel上方"
        
    if result:
        add_x, add_y, angle, _ = result
    else:
        showMessageInfo(u"添加全流程追溯码异常，请重跑试试，若还有问题请反馈给程序工程师测试！")
        return "error"
    
    x_center = (f_xmin + f_xmax) * 0.5
    y_center = (f_ymin + f_ymax) * 0.5
    
    if coordinate_mode == u"斜对称转换":   
        convert_x, convert_y = convert_coordinate_in_panel_edge(step, add_x, add_y, x_center, y_center, u"斜对称转换")
    
    dic_zu_layername = {}
    for layer in matrixInfo["gROWname"]:
        dic_zu_layername[layer] = []
        
    for layer in signalLayers:
        dic_zu_layername[layer].append([add_x,
                                        add_y,
                                        symbolname,
                                        {"polarity": "positive",
                                         "attrstring": ".bit,text=trace_barcode"}])
        
        if coordinate_mode == u"斜对称转换":            
            dic_zu_layername[layer].append([convert_x,
                                            convert_y,
                                            symbolname,
                                            {"polarity": "positive",
                                             "attrstring": ".bit,text=trace_barcode"}])        
    
    # neg_symbolname = "rect{0}x{1}".format(symbol_width*1000-1000, symbol_length*1000-1000)
    neg_symbolname = symbolname
    for key, value in dic_position.iteritems():
        
        for layer in core_bot_layers:
            dic_zu_layername[layer].append([add_x,
                                            add_y,
                                            neg_symbolname,
                                            {"polarity": "negative",
                                             "attrstring": ".bit,text=trace_barcode"}])
            if coordinate_mode == u"斜对称转换": 
                dic_zu_layername[layer].append([convert_x,
                                                convert_y,
                                                neg_symbolname,
                                                {"polarity": "negative",
                                                 "attrstring": ".bit,text=trace_barcode"}])
        if coordinate_mode == u"斜对称转换": 
            convert_x1, convert_y1 = convert_coordinate_in_panel_edge(step, add_x, add_y - symbol_length / 2.0 + value[2],
                                                                    x_center, y_center, u"斜对称转换")
        for layer in outsignalLayers:          
            dic_zu_layername[layer].append([add_x,
                                            add_y - symbol_length / 2.0 + value[2],
                                            "s5000"if value[0] == "s9000" else "s6500",
                                            {"polarity": "positive",
                                             "attrstring": [".string,text={0}".format(value[3]), ".bit,text=trace_barcode"]}])
            if coordinate_mode == u"斜对称转换": 
                dic_zu_layername[layer].append([convert_x1,
                                                convert_y1,
                                                "s5000"if value[0] == "s9000" else "s6500",
                                                {"polarity": "positive",
                                                 "attrstring": [".string,text={0}_convert".format(value[3]), ".bit,text=trace_barcode"]}])            
            
        for layer in dic_negative_layer[key]:
            if layer not in core_bot_layers:                
                dic_zu_layername[layer].append([add_x,
                                                add_y - symbol_length / 2.0 + value[2],
                                                "s10510",# 负片设计多加10um
                                                {"polarity": "negative",
                                                 "attrstring": ".bit,text=trace_barcode"}])
                if coordinate_mode == u"斜对称转换": 
                    dic_zu_layername[layer].append([convert_x1,
                                                    convert_y1,
                                                    value[0],
                                                    {"polarity": "negative",
                                                     "attrstring": ".bit,text=trace_barcode"}])                
        
    addfeature.start_add_info(step, matrixInfo, dic_zu_layername)
    
    step.removeLayer("barcode_tmp")
    step.removeLayer("fill")
    uploading_barcode_coordinate_info(jobname, step, x_center, y_center, out_lb_x, out_lb_y, out_lb_sec_x, out_lb_sec_y)    
    
def uploading_barcode_coordinate_info(jobname,step, x_center, y_center, out_lb_x, out_lb_y, out_lb_sec_x, out_lb_sec_y):
    """上传坐标信息"""
    if len(jobname) != 13 and "-lyh" not in jobname:
        return
    
    worklayer = outsignalLayers[0]
    step.clearAll()
    step.affect(worklayer)
    step.resetFilter()
    step.setAttrFilter(".string,text=bar_code_innerl2l3")
    step.selectAll()
    step.resetFilter()
    step.setAttrFilter(".string,text=bar_code_sec")
    step.selectAll()
    step.resetFilter()
    step.setAttrFilter(".string,text=bar_code_out")
    step.selectAll()
    if step.featureSelected():
        layer_cmd = gClasses.Layer(step, worklayer)
        featout = layer_cmd.featSelOut(units="mm")["pads"]
        dic_zu = {"jobname": jobname.split("-")[0], "layer": u"{0}层".format(lay_num),"user": top.getUser(),}
        dic_attr = {"bar_code_innerl2l3": "innerl2l3",
                    "bar_code_sec": "inner",
                    "bar_code_out": "out",}
        
        for obj in featout:
            if dic_attr.get(obj.string, None):                
                if obj.string == "bar_code_out":
                    # 二位码坐标定义：压合裁膜后的这个机械钻码机是以二维码的左上角来定义二维码位置坐标的
                    # 因外层进板方向跟芯板不一样 外层 x 跟y方向要对调
                    # x方向要从原点开始计算 而不是板中心                    
                    dic_zu[dic_attr[obj.string]+"_x"] = "%.2f" % (obj.y - 6.5 * 0.5 - out_lb_y)
                    dic_zu[dic_attr[obj.string]+"_y"] = "%.2f" % (obj.x - 6.5 * 0.5 - out_lb_x)
                    
                elif obj.string == "bar_code_innerl2l3":
                    # 二位码坐标定义：是进料边的这一侧二维码边的中心点
                    dic_zu[dic_attr[obj.string]+"_x"] = "%.2f" % (obj.x - 5 * 0.5)
                    dic_zu[dic_attr[obj.string]+"_y"] = "%.2f" % (obj.y - y_center)
                else:
                    # 二位码坐标定义：压合裁膜后的这个机械钻码机是以二维码的左上角来定义二维码位置坐标的
                    # 因次外层进板方向跟芯板不一样 次外层 x 跟y方向要对调
                    # x方向要从原点开始计算 而不是板中心
                    dic_zu[dic_attr[obj.string]+"_x"] = "%.2f" % (obj.y - 5 * 0.5 - out_lb_sec_y)
                    dic_zu[dic_attr[obj.string]+"_y"] = "%.2f" % (obj.x - 5 * 0.5 - out_lb_sec_x)
        
        exists_info = get_exists_coordinate_info(jobname, select_dic=True)
        if exists_info:
            dic_info = eval(exists_info[0]["trace_code_coordinates"])
            dic_info["layer"] = dic_info["layer"].decode("utf8")
            dic_info["create_time"] = exists_info[0]["create_time"]
            dic_info["start_btn_text"] = u"上传"
            dic_info["end_btn_text"] = u"退出，不上传数据"
            dic_info["end_btn_size"] = 120
            res = showQuestionMessageInfo(u"查询型号{0}在数据库已有坐标数据如下，点击上传将覆盖数据:".format(jobname), **dic_info)
            if not res:
                step.clearAll()
                return
        else:
            res = showQuestionMessageInfo(u"即将上传型号{0}二维码坐标信息到MES，是否继续，退出将不上传数据！".format(jobname))
            if not res:
                step.clearAll()
                return
            
        msg = post_message(**dic_zu)
        if msg:
            showMessageInfo(msg)
        else:
            uploading_coordinate_record(jobname, dic_zu)
            del dic_zu["user"]
            showMessageInfo(u"添加完成，上传MES坐标数据如下:", **dic_zu)
    else:
        showMessageInfo(u"未检测到板边的全流程追溯二维码，请检查！")
        
    step.clearAll()
    
def get_exists_coordinate_info(jobname, select_dic=False):
    if not select_dic:        
        sql = "select id from hdi_engineering.incam_mes_trace_code where job_name = '{0}'"
        result = conn.SQL_EXECUTE(dbc_m, sql.format(jobname.split("-")[0]))
    else:
        sql = "select * from hdi_engineering.incam_mes_trace_code where job_name = '{0}'"
        result = conn.SELECT_DIC(dbc_m, sql.format(jobname.split("-")[0]))        
    return result
    
def uploading_coordinate_record(jobname, dic_info):    
    result = get_exists_coordinate_info(jobname)    
    cursor = dbc_m.cursor()
    if result: 
        update_sql = u"""update hdi_engineering.incam_mes_trace_code set trace_code_coordinates=%s,create_time=now() where id=%s"""
        cursor.execute(update_sql, (json.dumps(dic_info, ensure_ascii=False), result[0][0]))
    else:
        insert_sql = "insert into hdi_engineering.incam_mes_trace_code\
        (job_name,trace_code_coordinates,cam_user) values (%s,%s,%s)"
        cursor.execute(insert_sql, (jobname.split("-")[0], json.dumps(dic_info, ensure_ascii=False), top.getUser()))
        
    dbc_m.commit()
    cursor.close()
    dbc_m.close()
    
if __name__ == "__main__":
    if "only_uploading_data" in sys.argv[1:]:
        only_uploading_data(jobname, stepname)
    else:
        add_barcode_area(jobname, stepname)