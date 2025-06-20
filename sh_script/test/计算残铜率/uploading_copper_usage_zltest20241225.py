#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__    = "20230307"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""残铜率上传 """

import os
import sys
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
    
import gClasses
import MySQL_DB
import json
import re
from genesisPackages import calcCopperArea, \
     innersignalLayers, matrixInfo, get_panelset_sr_step, \
     jobname, job, get_sr_area_flatten, get_profile_limits, \
     top
from get_erp_job_info import get_inplan_mrp_info, \
     get_inplan_all_flow

conn = MySQL_DB.MySQL()
dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                           username='root', passwd='k06931!')
user = top.getUser()
dic_layer_copper_type = {}
panel_param_path = os.path.join(job.dbpath, "user", "panel_parameter.json")
flipList = []
if os.path.exists(panel_param_path):
    try:        
        with open(panel_param_path) as file_obj:
            dic_info = json.load(file_obj, encoding='utf8')
    
        if dic_info.has_key("fill_array"):
            for dic_layer_info in dic_info["fill_array"]:
                layer_name = dic_layer_info["layer_name"]
                dic_layer_copper_type[layer_name] = dic_layer_info["panel_fill"]
    except:
        pass



def get_szsk_layers_from_inplan():
    """从inplan中获取树脂塞孔层名"""
    process_data_info = get_inplan_all_flow(job.name.upper(), select_dic=True)
    mrp_name = job.name.split("-")[0].upper()
    # job.PAUSE(str([process_data_info]))
    arraylist_erp_drill = []
    for dic_process_info in process_data_info:
        if dic_process_info["WORK_CENTER_CODE"] and \
           u"树脂塞孔" in dic_process_info["WORK_CENTER_CODE"].decode("utf8") and \
           mrp_name.upper() == dic_process_info["MRP_NAME"]:
            if dic_process_info["NOTE_STRING"] and \
               (u"树脂塞孔铝片" in dic_process_info["NOTE_STRING"].decode("utf8").replace("\n", "") or \
                u"铝片" in dic_process_info["NOTE_STRING"].decode("utf8").replace("\n", "")):
                find_sting = re.findall("(sz\S+)", dic_process_info["NOTE_STRING"].decode("utf8").lower())
                # print(find_sting)
                if find_sting:
                    for x in find_sting:
                        new_x = ""
                        for t in x:
                            if ord(t) in [45,46,48, 49,50,51,52,53,54,55,56,57,99,107,108,112,115,122]:
                                new_x += t
                            else:
                                new_x += " "
                                
                        arraylist_erp_drill += new_x.split(" ")
                    
            if dic_process_info["WORK_DESCRIPTION"] and \
               u"树脂塞孔铝片" in dic_process_info["WORK_DESCRIPTION"].decode("utf8"):
                if dic_process_info["VALUE_AS_STRING"]:                                
                    arraylist_erp_drill += [dic_process_info["VALUE_AS_STRING"]]
    
    if not arraylist_erp_drill:
        for dic_process_info in process_data_info:
            if dic_process_info["WORK_CENTER_CODE"] and \
               u"树脂塞孔" in dic_process_info["WORK_CENTER_CODE"].decode("utf8") and \
               mrp_name.upper() == dic_process_info["MRP_NAME"]:                    
                if dic_process_info["NOTE_STRING"]:
                    find_sting = re.findall("(sz\S+)", dic_process_info["NOTE_STRING"].decode("utf8").lower())
                    # print(find_sting)
                    if find_sting:
                        for x in find_sting:
                            new_x = ""
                            for t in x:
                                if ord(t) in [45,46,48, 49,50,51,52,53,54,55,56,57,99,107,108,112,115,122]:
                                    new_x += t
                                else:
                                    new_x += " "
                                    
                            arraylist_erp_drill += new_x.split(" ")
                            
    return list(set(arraylist_erp_drill))



def create_mask_layer_condition(step):
    """选化金面积计算去掉 osp区域 生成临时层"""
    # step = gClasses.Step(job, step.name)
    dic_zu = {}
    if step.isLayer("m1") and step.isLayer("m2"):        
        dic_zu = {"sgt-c": "m1","sgt-s": "m2",}
        dic_mask_layer = {"m1": "m1","m2": "m2",}
    else:
        if step.isLayer("m1-1") and step.isLayer("m2-1"):        
            dic_zu = {"sgt-c": "m1-1","sgt-s": "m2-1",}
            dic_mask_layer = {"m1-1": "m1","m2-1": "m2",}
    if not dic_zu:
        return
    tool_step = gClasses.Step(job, job.info['gSTEPS_LIST'][0])
    for layer in ["sgt-c", "sgt-s"]:
        layer_cmd = gClasses.Layer(step, layer)
        if step.isLayer(layer) and getattr(layer_cmd.cell, "context", None) == "board":
            # 20241223 zl 创建层
            location = 'before' if 'c' in layer else 'after'
            # step.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % step.job.name)
            if not step.isLayer(layer+"_calc_expose_tmp"):
                if flipList:
                    tool_step.open()
                    tool_step.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % step.job.name)
                    tool_step.COM('create_layer,layer=%s,context=%s,type=%s,polarity=positive,ins_layer=%s,location=%s' % (layer+"_calc_expose_tmp", 'board', 'document', layer, location))
                    tool_step.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % step.job.name)
                else:
                    step.COM('create_layer,layer=%s,context=%s,type=%s,polarity=positive,ins_layer=%s,location=%s' % (layer+"_calc_expose_tmp", 'board', 'document', layer, location))
            if not step.isLayer(dic_zu[layer]+"_calc_expose_tmp"):
                if flipList:
                    tool_step.open()
                    tool_step.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % step.job.name)
                    tool_step.COM('create_layer,layer=%s,context=%s,type=%s,polarity=positive,ins_layer=%s,location=%s' % (dic_zu[layer]+"_calc_expose_tmp", 'board', 'document', dic_zu[layer], location))
                    tool_step.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % step.job.name)
                else:
                    step.COM('create_layer,layer=%s,context=%s,type=%s,polarity=positive,ins_layer=%s,location=%s' % (dic_zu[layer]+"_calc_expose_tmp", 'board', 'document', dic_zu[layer], location))
            # if step.name == "panel":
            step.open()
            step.PAUSE(step.name)
            step.flatten_layer(layer, layer+"_calc_expose_tmp")
            step.flatten_layer(dic_zu[layer], dic_mask_layer[dic_zu[layer]]+"_calc_expose_tmp")
            # else:
            #     step.copyLayer(step.job.name, step.name, layer, layer+"_calc_expose_tmp")
            #     step.copyLayer(step.job.name, step.name, dic_zu[layer], dic_mask_layer[dic_zu[layer]]+"_calc_expose_tmp")
            step.clearAll()
            step.resetFilter()
            step.affect(layer+"_calc_expose_tmp")
            step.selectAll()
            if not step.featureSelected():
                # osp层内没有物件的 不处理
                continue
            
            step.selectNone()
            step.affect(dic_mask_layer[dic_zu[layer]]+"_calc_expose_tmp")            
            step.contourize()
            
            step.clearAll()
            step.affect(dic_mask_layer[dic_zu[layer]]+"_calc_expose_tmp")
            step.refSelectFilter(layer+"_calc_expose_tmp", mode="cover")
            step.COM("sel_reverse")
            if step.featureSelected():
                step.selectDelete()
                
            if step.name == "panel":
                # 有时候osp区域做在panel 这里要最后在处理下
                step.flatten_layer(layer+"_calc_expose_tmp", layer+"_calc_expose_tmp_flt")
                step.flatten_layer(dic_mask_layer[dic_zu[layer]]+"_calc_expose_tmp",
                                   dic_mask_layer[dic_zu[layer]]+"_calc_expose_tmp_flt")
                step.clearAll()
                # 清除panel板边
                step.PAUSE('A')
                step.affect(dic_mask_layer[dic_zu[layer]]+"_calc_expose_tmp_flt")
                step.refSelectFilter(layer+"_calc_expose_tmp_flt", mode="cover")
                step.COM("sel_reverse")
                if step.featureSelected():
                    step.selectDelete()

                step.removeLayer(dic_mask_layer[dic_zu[layer]]+"_calc_expose_tmp")
                step.copyLayer(step.job.name, step.name,
                               dic_mask_layer[dic_zu[layer]]+"_calc_expose_tmp_flt",
                               dic_mask_layer[dic_zu[layer]]+"_calc_expose_tmp")
                step.removeLayer(layer+"_calc_expose_tmp_flt")
                step.removeLayer(dic_mask_layer[dic_zu[layer]]+"_calc_expose_tmp_flt")
                step.PAUSE('A')

def flipStepName(step):
    """
    递归寻找出有镜像的step，并append到 flipList数组中
    :param step: step名
    :return: None
    """
    info = job.DO_INFO('-t step -e %s/%s -m script -d SR -p flip+step' % (job.name, step))
    step_flip_tuple = [(info['gSRstep'][i], info['gSRflip'][i]) for i in range(len(info['gSRstep']))]
    step_flip_tuple = list(set(step_flip_tuple))
    for (stepName, flip_yn) in step_flip_tuple:
        if flip_yn == 'yes':
            flipList.append(stepName)
        elif flip_yn == 'no':
            flipStepName(stepName)



dic_copper_info = {}
if "panel" in matrixInfo["gCOLstep_name"]:
    dic_rout_info = {}
    data_info = get_inplan_mrp_info(jobname)
    for info in data_info:
        layer1 = info["FROMLAY"].lower()
        layer2 = info["TOLAY"].lower()
        dic_rout_info[layer1] = (info["PNLROUTX"] * 25.4, info["PNLROUTY"] * 25.4)
        dic_rout_info[layer2] = (info["PNLROUTX"] * 25.4, info["PNLROUTY"] * 25.4)        
    
    all_steps = [name for name in get_panelset_sr_step(jobname, "panel")
                 if "set" in name or "edit" in name]
    # pnl边挂的step要计算 2024-05-08  ynh
    get_pnl_steps = get_panelset_sr_step(jobname=jobname, panelset='panel')
    # for stepname in list(set(get_pnl_steps)) + ['panel']:
    # 判断是否是阴阳拼版
    flipStepName('panel')
    for stepname in ['panel']:
        step = gClasses.Step(job, stepname)
        step.open()
        # input组 高贵 跟马文慧  吕方，安绵六，董飞他们3个负责拼版跑边，胡刚负责INPUT读入料号 不优化 20230504 by lyh
        if user not in ["70928", "50313", "68233", "72616", "72451", "69615", "system"]:
            create_mask_layer_condition(step)
    job.PAUSE('A')
    # if "-lyh" in job.name:
    step = gClasses.Step(job, "panel")
    step.open()
    step.COM("units,type=mm")
    drillLayers = []
    if step.isLayer("drl"):    
        drillLayers = ["drl"]
        if step.isLayer("cdc"):
            drillLayers = ["cdc"]
        if step.isLayer("cds"):
            drillLayers = ["cds"]
    
    sz_drills = get_szsk_layers_from_inplan()
    # step.PAUSE(str([sz_drills]))
    step.removeLayer("exposed_drill_tmp")
    step.createLayer("exposed_drill_tmp")

    step.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=drill"
             .format(job.name, "exposed_drill_tmp"))
    step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board"
             .format(job.name, "exposed_drill_tmp"))
    
    expose_drills = ["exposed_drill_tmp"]
    for drill_layer in drillLayers:
        step.flatten_layer(drill_layer, drill_layer+"_exposed_drill_tmp")
        step.clearAll()
        step.affect(drill_layer+"_exposed_drill_tmp")
        step.copyToLayer("exposed_drill_tmp")
        step.removeLayer(drill_layer+"_exposed_drill_tmp")
        step.clearAll()
        step.affect("exposed_drill_tmp")
        for i, sz_layer in enumerate(matrixInfo["gROWname"]):
            if sz_layer in sz_drills +["sz.lp", "szsk-c.lp", "szsk-s.lp"] and\
               matrixInfo["gROWlayer_type"][i] == "drill" and \
               "...dq" not in sz_layer:
                step.removeLayer(sz_layer+"_exposed_drill_tmp")
                step.flatten_layer(sz_layer, sz_layer+"_exposed_drill_tmp")
                step.resetFilter()
                step.refSelectFilter(sz_layer+"_exposed_drill_tmp")
                if step.featureSelected():
                    step.selectDelete()
                    
                step.removeLayer(sz_layer+"_exposed_drill_tmp")

    for stepname in list(set(all_steps)) + ["panel"]:
        
        dic_copper_info[stepname] = {}
        step = gClasses.Step(job, stepname)
        step.open()
        
        #测试
        # if "-lyh" in jobname:               
        #选化要处理
        #input组 高贵 跟马文慧  吕方，安绵六，董飞他们3个负责拼版跑边，胡刚负责INPUT读入料号 不优化 20230504 by lyh
        # if user not in ["70928", "50313", "68233", "72616", "72451", "69615", "system"]:
        #     create_mask_layer_condition(step)

        step.COM("units,type=mm")
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
        for worklayer in innersignalLayers:
            if dic_rout_info.get(worklayer) and stepname == "panel":
                lb_x = ((f_xmax - f_xmin) - dic_rout_info[worklayer][0]) * 0.5
                lb_y = ((f_ymax - f_ymin) - dic_rout_info[worklayer][1]) * 0.5
                x1 = f_xmin + lb_x
                y1 = f_ymin + lb_y
                x2 = f_xmax - lb_x
                y2 = f_ymax - lb_y
                mianji, per = calcCopperArea(step, worklayer, "", 0, drillLayers="",
                                             area_x1=x1, area_x2=x2, area_y1=y1, area_y2=y2)
            else:
                mianji, per = calcCopperArea(step, worklayer, "", 0, drillLayers="")
            dic_copper_info[stepname][worklayer] = float(mianji), per        
    
        if stepname == "panel":
            
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            
            STR = '-t step -e %s/%s -d REPEAT,units=mm' % (jobname, stepname)
            gREPEAT_info = step.DO_INFO(STR)
            gREPEATstep = gREPEAT_info['gREPEATstep']
            
            f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
            other_coupon_steps = [name for name in gREPEATstep
                                  if "set" not in name
                                  and "edit" not in name
                                  and "icg" not in name]
            edit_set_steps = [name for name in gREPEATstep
                              if "set" in name or "edit" in name]
            icg_coupon_stes = [name for name in gREPEATstep
                               if "icg" in name ]
            
            get_sr_area_flatten("fill_tmp", stepname=stepname,
                                get_sr_step=True, exclude_sr_step=set(other_coupon_steps+icg_coupon_stes))
    
            mianji_set_edit, _ = calcCopperArea(step, "fill_tmp", "", 0, drillLayers="")        
            step.removeLayer("fill_tmp")        
            dic_copper_info[stepname+"_coup"] = {}
            #计算panel不含交货单元的残铜率
            for worklayer in innersignalLayers:
                if dic_rout_info.get(worklayer):
                    lb_x = ((f_xmax - f_xmin) - dic_rout_info[worklayer][0]) * 0.5
                    lb_y = ((f_ymax - f_ymin) - dic_rout_info[worklayer][1]) * 0.5
                    x1 = f_xmin + lb_x
                    y1 = f_ymin + lb_y
                    x2 = f_xmax - lb_x
                    y2 = f_ymax - lb_y
                    sr_area_mian_ji = dic_rout_info[worklayer][0] * dic_rout_info[worklayer][1] - float(mianji_set_edit)
                    sr_area_usage = round(sr_area_mian_ji / (dic_rout_info[worklayer][0] * dic_rout_info[worklayer][1]), 2) *100
                else:
                    sr_area_mian_ji = f_xmax * f_ymax - float(mianji_set_edit)
                    sr_area_usage = round(sr_area_mian_ji / (f_xmax * f_ymax), 2) *100                    
                    
                set_copper_size = dic_copper_info[edit_set_steps[0]][worklayer][0] * len(edit_set_steps)
                mianji = dic_copper_info[stepname][worklayer][0]
                dic_copper_info[stepname+"_coup"][worklayer] = float(mianji) - set_copper_size, \
                    round((float(mianji) - set_copper_size) / sr_area_mian_ji, 4) *100, sr_area_usage
                
                if dic_layer_copper_type.get(worklayer, None) is None:
                    step.clearAll()
                    step.affect(worklayer)
                    step.resetFilter()
                    step.setAttrFilter(".bit,text=pnl_ladder_cu")
                    step.filter_set(feat_types='surface', polarity='positive')
                    step.selectAll()
                    if step.featureSelected():
                        dic_layer_copper_type[worklayer] = u"梯形"
                        
                    else:
                        step.resetFilter()
                        step.setAttrFilter("surface,text=copper")
                        step.filter_set(feat_types='surface', polarity='positive')
                        step.selectAll()
                        if step.featureSelected():
                            dic_layer_copper_type[worklayer] = u"蜂窝"
                            
                step.clearAll()
                step.resetFilter()
                    
    # job.PAUSE(str(dic_copper_info))
    
    # 仅正式型号上传数据 20230417 by lyh
    if len(jobname) != 13 and "-lyh" not in str(jobname):
        sys.exit()
        
    arraylist = ["job_name", 
    "layer_name", 
    "pnl_lay_copper_type", 
    "pnl_copper_usage_total", 
    "pnl_copper_usage", 
    "set_copper_usage_total", 
    "pcs_copper_usage", 
    "pnl_non_unit_area",
    "cam_notes"]
    
    sql = "select * from hdi_engineering.incam_copper_usage where job_name = '{0}'"
    data_info = conn.SQL_EXECUTE(dbc_m, sql.format(jobname))
    if data_info:
        sql = "delete from hdi_engineering.incam_copper_usage where job_name = '{0}'"
        conn.SQL_EXECUTE(dbc_m, sql.format(jobname))
        
    for layer in innersignalLayers:
        arraylist_copper = [jobname, "", "", "", "", "", "", "", ""]
        arraylist_copper[1] = layer
        arraylist_copper[2] = dic_layer_copper_type.get(layer, "")        
        for i, stepname in enumerate(["panel", "panel_coup", "set", "edit"]):        
            if dic_copper_info.has_key(stepname):
                arraylist_copper[i+3] = dic_copper_info[stepname][layer][1]
                if stepname == "panel_coup":
                    arraylist_copper[7] = dic_copper_info[stepname][layer][2]
        
        if user == "system":
            arraylist_copper[8] = user
            
        insert_sql = u"insert into hdi_engineering.incam_copper_usage ({0}) values ({1})"
        conn.SQL_EXECUTE(dbc_m, insert_sql.format(",".join(arraylist),",".join(["%s"]*len(arraylist))), arraylist_copper)
