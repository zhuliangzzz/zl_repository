#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20230116"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""胜宏HDI自动检测模块 """


"""sh_hdi_warning_director_process"""

"""
# 20241024 zl check_md_cover_info 外层检测增加项目---挡点是否比防焊开窗大&双面开窗孔存在挡点 
# 20241025 zl check_offset_et_rj_fbk 内层检测增加检测项目--防爆孔与融合块位置一致 
# 20241105 zl check_isolated_smd_bga_comp_info 检测孤立bga/smd补偿是否正常
# 20241106 zl check_wrapped_smd_bga_comp_info 检测被包裹的bga/smd补偿是否正常
# 20241113 zl check_compare_layers 内外层自动检测增加---钻孔&线路&防焊&文字Compare layers，差异大于1mil的报警显示位置供制作者判定
# 20241129 zl check_hole_open_window 选化层孔是否开窗检测
# 20241202 zl check_silk_screen 文字上pad检测
# 20241204 zl check_removed_slight_section 检查是否执行去细丝程序
# 20241206 zl check_steel_mesh_to_via_not_plugged 检测未塞孔的VIA孔对应是否有钢网
# 20241213 zl check_text_serial_number 检测文字序列号防呆
"""


import os
import sys
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")

os.environ["COM_VON_VOF"] = "yes"

import re
import time
import gClasses
import genClasses_zl as gen
# stepTool = gen.Step(gen.Job('myJob'),'step_tool')
import math
import get_luokong_area
import datetime
import json
import tarfile
from genesisPackages import get_mai_drill_hole, \
     get_drill_start_end_layers, get_panelset_sr_step, \
     outsignalLayers, innersignalLayers, solderMaskLayers,\
     silkscreenLayers, lay_num, top, get_sr_area_flatten, \
     laser_drill_layers, get_layer_selected_limits, \
     tongkongDrillLayer, mai_drill_layers, get_profile_limits, \
     get_sr_area_for_step_include, signalLayers, get_sr_limits, \
     get_panel_features_in_set_position, calcExposeArea, \
     mai_man_drill_layers, get_symbol_area

from get_erp_job_info import get_face_tech_params, \
     get_inplan_all_flow, get_plating_type, \
     get_inplan_mrp_info, get_target_distance_info, \
     get_mysql_target_info, get_mysql_ks_bd_target_info, \
     get_cu_weight, get_mysql_all_target_info, \
     get_mysql_ks_bd_all_target_info, get_expose_area_from_erp, \
     get_led_board, get_job_type, get_ks_bd_target_info_detail, \
     getPanelSRTable, get_inplan_mrp_info_new, getJobData, \
     get_all_job_creation_date, get_inplan_imp, \
     get_inplan_gold_area, get_job_attr_info, get_mrp_name, \
     get_drill_info_detail

from checkRules import rule
checkrule = rule()

from scriptsRunRecordLog import uploadinglog
from create_ui_model import showMessageInfo, \
     showQuestionMessageInfo, show_message_picture_ui, \
     QtGui, Qt
try:
    from sh_hdi_auto_check_list import get_check_function_list, \
         update_current_job_check_log, processID, jobID
    from showTargetDistanceInformation import TargetDistance_UI
    
    from send_html_request_to_tc_aac_file import post_message
except:
    pass

try:
    from send_message_to_topcam import uploading_message_to_topcam    
except:
    pass
try:
    from TOPCAM_IKM import IKM
    ikm_fun = IKM()
except Exception, e:
    print e
    
try:        
    from Dingtalk import TopApi
    ding_app = TopApi()
except:
    pass    
    
import socket
localip = socket.gethostbyname_ex(socket.gethostname())
from oracleConnect import oracleConn
import MySQL_DB
conn = MySQL_DB.MySQL()
dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                           username='root', passwd='k06931!')
dbc_p = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='project_status', prod=3306,
                           username='root', passwd='k06931!')

jobname = os.environ.get("JOB")
stepname = os.environ.get("STEP")
job = gClasses.Job(jobname)
matrixinfo = job.matrix.getInfo()

dic_symbol_info = {}
if sys.platform == "win32":            
    symbol_info_path = "{0}/fw/lib/symbols/symbol_info.json".format(os.environ["GENESIS_DIR"])
else:
    symbol_info_path = "/incam/server/site_data/library/symbol_info.json"
if not os.path.exists(symbol_info_path):
    symbol_info_path = os.path.join(os.path.dirname(sys.argv[0]), "symbol_info.json")
    
if os.path.exists(symbol_info_path):
    with open(symbol_info_path) as file_obj:
        dic_symbol_info = json.load(file_obj)

class auto_check_rule(object):
    """"""
    def __init__(self):
        """Constructor"""
    
    def view_note_detail(self, coordinate_info=None):
        """查看标记"""
        if coordinate_info is None:            
            dic_info = get_check_function_list(top.getUser(), job.name, "id = {0}".format(os.environ.get("CHECK_ID", "NULL")))
            if not dic_info:
                return
            dic_coordinate_info = eval(dic_info[0]["note_coordinate"].replace('""', '"'))
        else:
            dic_coordinate_info = coordinate_info
            
        for stepname, value in dic_coordinate_info.iteritems():
            for worklayer, array_info in value.iteritems():                
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")
                step.COM("negative_data,mode=dim")
                step.COM("display_sr,display=yes")
                
                if step.isLayer(worklayer):                    
                    checkrule.deleteNote(job.name, stepname, worklayer)
                    for coordinate, note_info,display_layer in array_info:
                        step.COM("units,type=mm")
                        checkrule.addNote(step, worklayer, coordinate, "please check")
                        if isinstance(display_layer, (list, tuple)):
                            num = 2
                            for show_layer in display_layer:
                                step.display_layer(show_layer, num)
                                num += 1
                        else:
                            step.display_layer(display_layer, 2)
                        
                        #增加有元素进入板内时同时打开ww层 20230801 by lyh
                        if u"有元素进入单元内".encode("utf8") in note_info:
                            if step.isLayer("ww"):
                                step.display_layer("ww", 3)
                                
                        if stepname == "panel":                            
                            step.COM("zoom_in")
                            step.COM("zoom_in")
                            
                        step.PAUSE("step: {0} layer: {1}  {2}".format(stepname, worklayer, note_info))
                        checkrule.deleteNote(job.name, stepname, worklayer)
                        if sys.platform != "win32":
                            step.COM("show_tab,tab=Notes,show=no")
                            step.COM("set_note_layer,layer=")                        
                else:
                    if sys.platform != "win32":
                        step.COM("show_tab,tab=Notes,show=no")
                        step.COM("set_note_layer,layer=")
                        
                    if "view_layer" in worklayer:
                        step.clearAll()
                        layer = worklayer.replace("view_layer_", "")
                        if layer in matrixinfo["gROWname"]:
                            step.display(layer)
                            
                        for log, layer_list in array_info.iteritems():                            
                            for num, layer in enumerate(layer_list):
                                if step.isLayer(layer):
                                    step.display_layer(layer, num+2)
                            step.PAUSE("{0}{1}".format(log, layer_list))

        if "view_note_detail" in sys.argv[1:]:
            self.create_log_and_update_coordinate(jobname, "view_note_detail", "check_over", {})

    def write_check_log_file(self, jobname, function_name, log):
        log_path = "/tmp/check_log_{0}_{1}.log".format(jobname, function_name)
        with open(log_path, "w") as f:
            f.write(log.encode("cp936"))
            
    def get_selected_dic_note_coordinate(self, jobname, stepname, step,
                                         worklayer, show_display_layer,
                                         show_pause_log,dic_zu_layer={},
                                         add_note_layer=None, delete_note=True,
                                         calc_legth=None):
        """获取被选中的元素的坐标信息及打标记"""
        
        if not dic_zu_layer.has_key(stepname):
            dic_zu_layer[stepname] = {}
        
        if delete_note:            
            step.COM("note_delete_all,layer={0},user=,note_from=0,note_to=2147483647".format(worklayer))
            if add_note_layer is not None:
                step.COM("note_delete_all,layer={0},user=,note_from=0,note_to=2147483647".format(add_note_layer))
            
        STR = r'-t layer -e %s/%s/%s -d FEATURES -o select,units= mm' % (
                            jobname, step.name,worklayer)
        infoList = step.INFO(STR)
        add_note_layer = worklayer if add_note_layer is None else add_note_layer
        if dic_zu_layer[stepname].has_key(add_note_layer):
            dic_zu_layer[stepname][add_note_layer].append([checkrule.parseInfoList(step, infoList, calc_legth),
                                                      show_pause_log.encode("utf8"), show_display_layer])                                                            
        else:
            dic_zu_layer[stepname][add_note_layer] = [[checkrule.parseInfoList(step, infoList, calc_legth),
                                                  show_pause_log.encode("utf8"), show_display_layer]]
            
        return dic_zu_layer
    
    def get_view_dic_layers(self, jobname, stepname, step,
                            worklayer="view_layer",dic_layer_list={},
                            dic_zu_layer={}):
        """记录要查看的层别"""
        
        if not dic_zu_layer.has_key(stepname):
            dic_zu_layer[stepname] = {}

        dic_zu_layer[stepname][worklayer] ={}
        for key, value in dic_layer_list.iteritems():
            dic_zu_layer[stepname][worklayer][key.encode("utf8")] = value
            
        return dic_zu_layer
    
    def create_log_and_update_coordinate(self, jobname, function_name,
                                         log, dic_coordinate):
        """生成日志及上传打标记坐标信息"""        
        self.write_check_log_file(jobname, function_name, "\n".join(log).replace("'", '"') if isinstance(log, (list, tuple)) else log.replace("'", '"'))
        
        if dic_coordinate:
            update_current_job_check_log(os.environ.get("CHECK_ID", "NULL"),
                                         "note_coordinate='{0}'".format(str(dic_coordinate).replace("'", '"')))      
            
    def check_mai_hole_and_lp_is_right(self):
        """埋孔钻孔与埋孔塞孔铝片是否在同一位置，个数是否正确"""
        mai_drill_layers = get_mai_drill_hole(**os.environ)
        if not mai_drill_layers:
            return u"success 无埋孔，不用检测", None
        
        data_info = get_inplan_all_flow(jobname, select_dic=True)
        
        arraylist = []
        dic_zu_layer = {}
        if "panel" in matrixinfo["gCOLstep_name"]:
            all_steps = get_panelset_sr_step(jobname, "panel")
            stepname = "panel"
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            for layer in matrixinfo["gROWname"]:
                if "_autocheck_hole+++" in layer:
                    step.removeLayer(layer)                    
                    
            if mai_drill_layers:
                dic_drill_lp = {}
                for drill_layer in mai_drill_layers:
                    dic_drill_lp[drill_layer] = []
                    #lp_layer = "{0}.lp".format(drill_layer)                    
                    #if step.isLayer(lp_layer):
                        #break
                    #lp_layer = "{0}.lp".format(drill_layer) .replace("b", "sz")                   
                    #if step.isLayer(lp_layer):
                        #break
                    names = [dic_info["MRP_NAME"] for dic_info in data_info
                                if dic_info["VALUE_AS_STRING"] and
                                drill_layer in dic_info["VALUE_AS_STRING"].lower()]
                    if names:
                        mrp_name = names[0]
                        
                        arraylist_erp_drill = []
                        for dic_process_info in data_info:
                            if dic_process_info["WORK_CENTER_CODE"] and \
                               u"树脂塞孔" in dic_process_info["WORK_CENTER_CODE"].decode("utf8") and \
                               mrp_name.upper() == dic_process_info["MRP_NAME"]:
                                
                                if dic_process_info["NOTE_STRING"] and \
                                   (u"树脂塞孔铝片" in dic_process_info["NOTE_STRING"].decode("utf8") or \
                                    u"铝片" in dic_process_info["NOTE_STRING"].decode("utf8")):
                                    find_sting = re.findall("(sz\S+)", dic_process_info["NOTE_STRING"].decode("utf8").lower())
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
                                        
                        if arraylist_erp_drill:
                            for lp_layer in set(arraylist_erp_drill):
                                if "-lyh" in job.name:
                                    step.PAUSE(str(arraylist_erp_drill))
                                if not lp_layer.lower():
                                    continue
                                # if step.isLayer(lp_layer.lower()):
                                if lp_layer.lower() in matrixinfo["gROWname"]:
                                    dic_drill_lp[drill_layer].append(lp_layer.lower())
                                # if step.isLayer(lp_layer.lower() + ".lp"):
                                if lp_layer.lower() + ".lp" in matrixinfo["gROWname"]:
                                    dic_drill_lp[drill_layer].append(lp_layer.lower() + ".lp")                               
                        
                        sz_process = [dic_info for dic_info in data_info
                                      if dic_info["MRP_NAME"] == mrp_name
                                      and u"树脂塞孔" in dic_info["WORK_CENTER_CODE"].decode("utf8")]
                        if not sz_process:
                            log = u"success 埋孔层{0} 不存在 树脂塞孔流程，无需检测".format(drill_layer)
                            arraylist.append(log)
                        else:
                            break
                        
                else:
                    if arraylist:
                        return arraylist, None
                    
                    return "success", None
                    
                for stepname in all_steps:
                    # 尾孔不检测
                    if stepname in mai_drill_layers:
                        continue
                    # 切片孔模块不检测
                    if "qie_hole_coupon_new_" in stepname:
                        continue
                   
                    step = gClasses.Step(job, stepname)
                    step.open()
                    step.COM("units,type=mm")
                    
                    for drill_layer in mai_drill_layers:
                        step.clearAll()
                        step.resetFilter()
                        step.affect(drill_layer)
                        step.selectAll()
                        if not step.featureSelected():
                            continue
                        
                        layers = []
                        info = []
                        if not dic_drill_lp.get(drill_layer):                            
                            lp_layer = drill_layer+".lp"# "{0}.lp".format(drill_layer)
                        else:
                            lp_layer = dic_drill_lp[drill_layer][0]
                            
                        layers.append(lp_layer)
                        if not step.isLayer(lp_layer):
                            lp_layer = lp_layer.replace("b", "sz")
                            layers.append(lp_layer)
                            if not step.isLayer(lp_layer):                            
                                for cs in ["-c.lp", "-s.lp"]:
                                    for lay in layers:
                                        lp_layer = lay.replace(".lp", cs)
                                        if step.isLayer(lp_layer):
                                            break
                                        info.append(lay)
                                        info.append(lp_layer)
                        
                        if not step.isLayer(lp_layer):
                            log = u"不存在铝片层{0},请检查层命名是否正确！".format(layers)
                            if log not in arraylist:                                
                                arraylist.append(log)
                            continue
                        
                        # get_sr_area_flatten("surface_fill", exclude_sr_step=[drill_layer], get_sr_step=True)
                        
                        #step.flatten_layer(drill_layer, drill_layer+"_autocheck_hole+++")
                        #step.flatten_layer(lp_layer, lp_layer+"_autocheck_hole+++")
                        
                        step.copyLayer(job.name, stepname, drill_layer, drill_layer+"_autocheck_hole+++")
                        #for tmp_layer in laser_drill_layers:
                            #if tmp_layer.split("-")[0].replace("s", "b") in drill_layer:
                                #step.clearAll()
                                #step.clearAll()
                                #step.affect(tmp_layer)
                                #step.copyToLayer(drill_layer+"_autocheck_hole+++")                                   
                        
                        if dic_drill_lp.get(drill_layer):
                            lp_layer = "_".join(dic_drill_lp[drill_layer])
                            # step.removeLayer(lp_layer+"_autocheck_hole+++")
                            for tmp_layer in dic_drill_lp[drill_layer]:
                                step.clearAll()
                                step.affect(tmp_layer)
                                step.copyToLayer(lp_layer+"_autocheck_hole+++")                                
                        else:
                            step.copyLayer(job.name, stepname, lp_layer, lp_layer+"_autocheck_hole+++")
                        
                        #for tmp_lay in [drill_layer, lp_layer]:                        
                            #step.clearAll()
                            #step.resetFilter()
                            #step.affect(tmp_lay+"_autocheck_hole+++")
                            #step.refSelectFilter(tmp_lay, mode="touch")
                            #if step.featureSelected():
                                #step.selectDelete()
                                
                            #if step.isLayer("surface_fill"):
                                #step.refSelectFilter("surface_fill", mode="disjoint")
                                #if step.featureSelected():
                                    #step.selectDelete()
                                
                        step.clearAll()
                        step.affect(drill_layer+"_autocheck_hole+++")
                        step.resetFilter()
                        step.selectAll()
                        count1 = step.featureSelected()
                        step.selectNone()
                        step.COM("sel_ref_feat,layers={0},use=filter,mode=same_center,"
                                 "f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,"
                                 "include_syms=,exclude_syms=,on_multiple=smallest".format(lp_layer+"_autocheck_hole+++"))                    
                        # step.refSelectFilter(lp_layer+"_autocheck_hole+++", mode="disjoint")
                        step.COM("sel_reverse")
                        find_hole = False
                        if step.featureSelected():
                            log = u"检测到埋孔层{0}跟铝片层{1}孔位置不一致，请到{4}中的{2}_autocheck_hole+++和{3}_autocheck_hole+++层查看不一致的地方！"
                            arraylist.append(log.format(drill_layer, lp_layer, drill_layer, lp_layer, stepname))
                            
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, drill_layer+"_autocheck_hole+++",
                                                                                 lp_layer+"_autocheck_hole+++",
                                                                                 log.format(drill_layer, lp_layer, drill_layer, lp_layer, stepname),
                                                                                 dic_zu_layer)
                            find_hole = True
                            
                        step.clearAll()
                        step.affect(lp_layer+"_autocheck_hole+++")
                        step.resetFilter()
                        step.selectAll()
                        count2 = step.featureSelected()
                        step.selectNone()
                        step.COM("sel_ref_feat,layers={0},use=filter,mode=same_center,"
                                 "f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,"
                                 "include_syms=,exclude_syms=,on_multiple=smallest".format(drill_layer+"_autocheck_hole+++"))                     
                        # step.refSelectFilter(drill_layer+"_autocheck_hole+++", mode="disjoint")
                        step.COM("sel_reverse")
                        if step.featureSelected() and not find_hole:
                            log = u"检测到铝片层{0}跟埋孔层{1}孔位置不一致，请到{4}中的{2}_autocheck_hole+++和{3}_autocheck_hole+++层查看不一致的地方！"
                            arraylist.append(log.format(lp_layer, drill_layer, lp_layer, drill_layer, stepname))                        
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, lp_layer+"_autocheck_hole+++",
                                                                                 drill_layer+"_autocheck_hole+++",
                                                                                 log.format(lp_layer, drill_layer, lp_layer, drill_layer, stepname),
                                                                                 dic_zu_layer)
                            
                        #layer_cmd = gClasses.Layer(step, drill_layer+"_autocheck_hole+++")
                        #feat_out1 = layer_cmd.featCurrent_LayerOut(units="mm")["pads"]
                        #layer_cmd = gClasses.Layer(step, lp_layer+"_autocheck_hole+++")
                        #feat_out2 = layer_cmd.featCurrent_LayerOut(units="mm")["pads"]
                        if count1 != count2:
                            log = u"检测到铝片层{0}孔数{1}跟埋孔层{2}孔数{3}不一致，请到{6}中的{4}_autocheck_hole+++和{5}_autocheck_hole+++层查看孔数！"
                            arraylist.append(log.format(lp_layer,count2, drill_layer, count1, lp_layer, drill_layer, stepname))
                            dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                                  dic_layer_list={u"请查看异常层：":[lp_layer+"_autocheck_hole+++", drill_layer+"_autocheck_hole+++"], },
                                                                  dic_zu_layer=dic_zu_layer)
            
            step.removeLayer("surface_fill")
            if not arraylist:
                for layer in job.matrix.getInfo()["gROWname"]:
                    if "_autocheck_hole+++" in layer:
                        step.removeLayer(layer)                  
            
        if arraylist:
            return arraylist, dic_zu_layer
        
        return "success", None
    
    def check_big_hole_compare_orig_position(self):
        """检测 0.55mm及以上孔位是否与原稿有偏移"""        
        stepname = "edit"
        if stepname in matrixinfo["gCOLstep_name"]:
            dic_zu_layer = {}
            if "orig" not in matrixinfo["gCOLstep_name"]:
                log = u"原稿orig不存在,请检查命名是否正确！"                
                return log, None
            
            if "drl" not in matrixinfo["gROWname"]:
                log = u"drl层不存在,请检查命名是否正确！"                
                return log, None                
            
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            for layer in matrixinfo["gROWname"]:
                if "_autocheck_big_hole+++" in layer:
                    step.removeLayer(layer)
                    
            step.copyLayer(job.name, "orig", "drl", "drl_autocheck_big_hole+++")
            step.copyLayer(job.name, stepname, "drl", "drl_tmp+++")
            step.copyLayer(job.name, stepname, "drl", "drl_tmp+++1")
            step.clearAll()
            step.affect("drl_tmp+++1")
            step.VOF()
            step.COM("sel_delete_atr,mode=list,attributes=.rout_chain")
            step.VON()
            step.contourize()
            step.COM("sel_resize,size=-5")
            step.clearAll()
            step.affect("drl_tmp+++")
            step.resetFilter()
            step.refSelectFilter("drl_tmp+++1", mode="cover")
            if step.featureSelected():
                step.selectDelete()
                
            step.removeLayer("drl_tmp+++1")
            
            layer_cmd = gClasses.Layer(step, "drl_tmp+++")
            feat_out = layer_cmd.featCurrent_LayerOut(units="mm")["pads"]
            try:                
                find_symbol = [obj.symbol for obj in feat_out
                               if float(obj.symbol[1:]) < 550]
            except Exception, e:
                log = u"drl层有非法孔径,请检查，异常原因：{0}".format(str(e))                
                return log, None
            
            if find_symbol:                
                step.resetFilter()
                step.filter_set(feat_types='pad')
                step.selectSymbol(";".join(set(find_symbol)), 1, 1)
                if step.featureSelected():
                    step.selectDelete()
                    
            step.resetFilter()
            step.filter_set(feat_types='line;arc')
            step.selectAll()
            if step.featureSelected():
                step.selectDelete()
            
            step.resetFilter()
            step.COM("sel_ref_feat,layers={0},use=filter,mode=same_center,"
                     "f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,"
                     "include_syms=,exclude_syms=,on_multiple=smallest".format("drl_autocheck_big_hole+++"))
            if step.featureSelected():
                step.selectDelete()
            
            #翟鸣 通知未接触到的孔删除
            step.refSelectFilter("drl_autocheck_big_hole+++", mode="disjoint")
            if step.featureSelected():
                step.selectDelete()
                
            step.clearAll()
            step.affect("drl")
            step.resetFilter()
            step.refSelectFilter("drl_tmp+++", mode="cover")            
            if step.featureSelected():
                log = u"检测到drl层0.55mm及以上孔位与原稿有偏移，请到edit中的drl_autocheck_big_hole+++层查看不一致的地方！"                                     
                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "drl",
                                                                     "drl_autocheck_big_hole+++", log, dic_zu_layer)
                step.removeLayer("drl_tmp+++")
                return log, dic_zu_layer
            else:
                step.removeLayer("drl_autocheck_big_hole+++")
                step.removeLayer("drl_tmp+++")
            
        return "success", None
    
    def check_tk_ykj_layer_holes(self, show_ui=None):
        """http://192.168.2.120:82/zentao/story-view-5455.html
        因每个人制作tk.ykj层时机不一致和中途修改问题，导致其他Step中tk.ykj层不一定有钻孔，造成资料异常
        检测层内钻孔孔数、位置与drl层是否一致。注意排除槽引孔、大孔引孔、槽孔旋转"""
        if "panel" in matrixinfo["gCOLstep_name"]:
            
            all_steps = get_panelset_sr_step(job.name, "panel")
            stepname = "panel"
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            dic_zu_layer = {}
            arraylist = []
            worklayer = "drl"
            reflayer = "tk.ykj"            
            if step.isLayer("drl") and step.isLayer("tk.ykj"):                
                for stepname in all_steps:
                    step = gClasses.Step(job, stepname)
                    step.open()
                    step.COM("units,type=mm")
                    
                    coordinate_info1 = []
                    if step.isLayer(worklayer):
                        layer_cmd1 = gClasses.Layer(step, worklayer)
                        feat_out1 = layer_cmd1.featout_dic_Index(units="mm", options="feat_index")["lines"]
                        
                        coordinate_info1 = [(obj, math.hypot((obj.xs+obj.xe) *0.5, (obj.ys+obj.ye) *0.5),
                                            obj.xs, obj.ys, obj.xe, obj.ye,obj.angle) for obj in feat_out1]
                    
                    coordinate_info2 = []
                    if step.isLayer(reflayer):                
                        layer_cmd2 = gClasses.Layer(step, reflayer)
                        feat_out2 = layer_cmd2.featout_dic_Index(units="mm", options="feat_index")["lines"]
                        
                        coordinate_info2 = [(obj, math.hypot((obj.xs+obj.xe) *0.5, (obj.ys+obj.ye) *0.5),
                                            obj.xs, obj.ys, obj.xe, obj.ye,obj.angle) for obj in feat_out2]
                        
                    if coordinate_info1 and coordinate_info2:                
                        for pre_info in coordinate_info1:
                            for suffix_info in coordinate_info2:
                                # 坐标到原点位置接近 且中心位置接近的 为同一个槽
                                if pre_info[1] - suffix_info[1] < 0.1 and \
                                   abs((pre_info[2] + pre_info[4]) * 0.5 - (suffix_info[2] + suffix_info[4]) * 0.5) < 0.1 and \
                                   abs((pre_info[3] + pre_info[5]) * 0.5 - (suffix_info[3] + suffix_info[5]) * 0.5) < 0.1:
                                    
                                    p = pre_info[6]                            
                                    s = suffix_info[6]
                                        
                                    diff_angle = abs(p - s)
                                    if diff_angle != 0:
                                        # 有旋转的槽孔 不进行比对
                                        step.clearAll()
                                        step.affect(worklayer)
                                        step.selectFeatureIndex(worklayer, pre_info[0].feat_index)
                                        if step.featureSelected():
                                            step.resetAttr()
                                            step.addAttr(".area", valType='', change_attr="yes")
                                            
                                        step.clearAll()
                                        step.affect(reflayer)
                                        step.selectFeatureIndex(reflayer, suffix_info[0].feat_index)
                                        if step.featureSelected():
                                            step.resetAttr()
                                            step.addAttr(".area", valType='', change_attr="yes")                                            
                                        
                    # if "-lyh" in job.name:                        
                    step.removeLayer("drl_diff")
                    tol = 11
                    step.COM("compare_layers,layer1=%s,job2=%s,step2=%s,\
                        layer2=%s,layer2_ext=,tol=%s,area=global,consider_sr=no,\
                        ignore_attr=.area,map_layer=%s_diff,map_layer_res=300" % (
                        "drl", job.name, stepname, "tk.ykj", tol, "drl"))
            
                    step.clearAll()
                    step.affect("drl_diff")
                    step.resetFilter()
                    step.COM(
                        "filter_set,filter_name=popup,update_popup=no,feat_types=pad,polarity=positive")
                    step.setSymbolFilter("r0")
                    step.selectAll()
                    if step.featureSelected():
                        step.affect("drl")
                        step.resetFilter()
                        step.refSelectFilter("drl_diff", include_syms="r0", f_types="pad")
                        if step.featureSelected():                            
                            log = u"检测到{0} drl层的孔在tk.ykj内有缺失,或者孔位置及大小有偏差，请检查标记的位置孔是否异常！"                                     
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "drl",
                                                                                 "tk.ykj", log.format(stepname), dic_zu_layer)
                            arraylist.append(log.format(stepname))                        
                        
                    step.removeLayer("drl_diff")
                    
                    #step.clearAll()
                    #step.affect("drl")
                    #step.resetFilter()
                    #step.refSelectFilter("tk.ykj", mode="disjoint")
                    #if step.featureSelected():
                        #log = u"检测到{0} drl层的孔在tk.ykj内有缺失，请检查标记的位置是否异常！"                                     
                        #dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "drl",
                                                                             #"tk.ykj", log.format(stepname), dic_zu_layer)
                        #arraylist.append(log.format(stepname))
                        
                    step.clearAll()
                    step.affect(worklayer)
                    step.COM("sel_delete_atr,mode=list,attributes=.area")
                    
                    step.clearAll()
                    step.affect(reflayer)
                    step.COM("sel_delete_atr,mode=list,attributes=.area")
                    
                    step.clearAll()
                    
            if arraylist:
                if show_ui == "yes":
                    showMessageInfo(u"跑镀孔跟盖孔菲林需用到tk.ykj层，检测到此层孔异常，请先处理！", *arraylist)
                    self.view_note_detail(dic_zu_layer)
                    
                return arraylist, dic_zu_layer
            
        return "success", None
    
    def check_hole_plug_in_pth_holes(self):
        """检测塞孔 塞在pth大孔上的报警 20240420 by lyh
        http://192.168.2.120:82/zentao/story-view-6697.html"""
        tong_lp_layers = ["sz.lp","szsk-c.lp","szsk-s.lp","szsk2-1.lp","szsk2-2.lp","sz-c.lp","sz-s.lp"]
        other_lp_layers = [name for name in matrixinfo["gROWname"]
                         if ".lp" in name and name not in tong_lp_layers]
        arraylist = []
        dic_zu_layer = {}
        if "panel" in matrixinfo["gCOLstep_name"]:
            
            all_steps = get_panelset_sr_step(job.name, "panel")
            for stepname in all_steps:
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")                
                for worklayer in tong_lp_layers + other_lp_layers:
                    if step.isLayer(worklayer):
                        
                        mai_drill = worklayer.replace(".lp", "").replace("sz", "b")
                        man_drill = worklayer.replace(".lp", "").replace("sz", "m")
                        if worklayer in other_lp_layers and \
                           (step.isLayer(mai_drill) or step.isLayer(man_drill)):
                            continue
                        
                        step.clearAll()
                        step.resetFilter()
                        step.affect(worklayer)
                        
                        for ref_layer in ["drl", "cdc", "cds", "2nd"]:
                            if step.isLayer(ref_layer):                                
                                layer_cmd = gClasses.Layer(step, ref_layer)
                                pad_feat_out = layer_cmd.featOut(units="mm")["pads"]
                                slot_feat_out = layer_cmd.featOut(units="mm")["lines"]
                                pad_symbols = list(set([obj.symbol for obj in pad_feat_out
                                                        if float(obj.symbol[1:]) >= 600]))
                                slot_symbols = list(set([obj.symbol for obj in slot_feat_out]))
                                if pad_symbols:                                    
                                    step.refSelectFilter(ref_layer, include_syms=';'.join(pad_symbols), f_types="pad")
                                if slot_symbols:                                    
                                    step.refSelectFilter(ref_layer, include_syms=';'.join(slot_symbols), f_types="line")
                                    
                                if step.featureSelected():
                                    log = u"检测到{0} {1}层中有塞孔钻到{2} 层内0.6mm及以上大孔上，请检查标记处是否异常!"
                                    arraylist.append(log.format(stepname, worklayer, ref_layer))
                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, worklayer,
                                                                                         ref_layer, log.format(stepname, worklayer, ref_layer),
                                                                                         dic_zu_layer)
                        step.clearAll()                
                        
            if arraylist:
                # showMessageInfo(*arraylist)
                return arraylist, dic_zu_layer
            
        return "success", None                        
    
    def check_drill_layer_is_over_lap_hole(self):
        """检测所有钻带是否存在重孔"""
        """http://192.168.2.120:82/zentao/story-view-5006.html
        1，输出埋孔树脂铝片（层名：b2-7.lp;2-7为变量)&树脂导气(b2-7...dq；2-7为变量)检测板边工具孔是否与埋孔层的工具孔在同一位置
        a,在同一位置放行。
        b,不在同一位置提醒且不让输出。 
        2，输出埋孔树脂铝片&通孔树脂铝片检测是否存在重孔。 
        a,无重孔放行
        b,有重孔提醒且不让输出
        3，输出通孔树脂铝片（层名：sz.lp/szsk-c.lp/szsk-s.lp/szsk2-1.lp/szsk2-2.lp/sz-c.lp/sz-s.lp )&树脂导气(层名：前缀与铝片一致，后缀...dq)检测板边工具孔                 是否与通孔层的工具孔在同一位置 
        a,在同一位置放行。
        b,不在同一位置提醒且不让输出。20221227 by lyh"""       
            
        tong_lp_layers = ["sz.lp","szsk-c.lp","szsk-s.lp","szsk2-1.lp","szsk2-2.lp","sz-c.lp","sz-s.lp"]
        tong_dq_layers = [name.replace(".lp", "...dq") for name in tong_lp_layers]
        
        all_drill_layers = [lay for i, lay in enumerate(matrixinfo["gROWname"])        
                             if matrixinfo["gROWcontext"][i] == "board"        
                             and matrixinfo["gROWlayer_type"][i] == "drill"]      
        
        mai_drill_layers = get_mai_drill_hole(**os.environ)
        arraylist = []
        dic_zu_layer = {}
        if "panel" in matrixinfo["gCOLstep_name"]:
            
            all_steps = get_panelset_sr_step(job.name, "panel")
            
            stepname = "panel"
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            for layer in matrixinfo["gROWname"]:
                if "_overlap_hole+++" in layer:
                    step.removeLayer(layer)
                if "_dw_hole_error+++" in layer:
                    step.removeLayer(layer)                    
                    
            for layer in tong_lp_layers + tong_dq_layers:
                if step.isLayer(layer):
                    if not step.isLayer("drl"):
                        log = u"drl 通孔层不存在，请检查命名是否正常！"
                        if log not in arraylist:                            
                            arraylist.append(log)
                        continue
                    log = u"检测到{0}层定位孔跟{1}通孔层的不在一个位置，详细结果请查看{2}层！".format(layer, "drl", layer+"_dw_hole_error+++")
                    res = self.get_check_dw_hole_overlap(step, layer, "drl", log)
                    if res:                                
                        arraylist.append(res)
                        dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                              worklayer="view_layer_"+layer, 
                                                              dic_layer_list={log:[layer+"_dw_hole_error+++"], },
                                                              dic_zu_layer=dic_zu_layer)                       
                    
            if mai_drill_layers:                
                for drill_layer in mai_drill_layers:
                    lp_layer = "{0}.lp".format(drill_layer)
                    dq_layer = "{0}...dq".format(drill_layer)
                        
                    for layer in [lp_layer, dq_layer]:                        
                        if step.isLayer(layer):
                            log = u"检测到{0}层定位孔跟{1}埋孔层的不在一个位置，详细结果请查看{2}层！".format(layer, drill_layer, layer+"_dw_hole_error+++")
                            res = self.get_check_dw_hole_overlap(step, layer, drill_layer, log)
                            if res:                                
                                arraylist.append(res)
                                dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                                      worklayer="view_layer_"+layer, 
                                                                      dic_layer_list={log:[layer+"_dw_hole_error+++"], },
                                                                      dic_zu_layer=dic_zu_layer)
            step.clearAll()
            
            for stepname in all_steps + ["panel"]:
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")                
                                    
                #if step.isLayer("drl"):
                    #log = u"检测到通孔层{0}层有重孔，详细结果请查看{1}层！".format("drl", "drl"+"_overlap_hole+++")
                    #res = self.check_drill_layer_exists_overlap_hole(step, "drl", log)
                    #if res:                                
                        #arraylist.append(res)
                        #dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                              #worklayer="view_layer_"+"drl", 
                                                              #dic_layer_list={log:["drl"+"_overlap_hole+++"], },
                                                              #dic_zu_layer=dic_zu_layer)
                        
                for drill_layer in all_drill_layers:
                    if step.isLayer(drill_layer):                    
                        log = u"检测到钻孔层{0}层有重孔，详细结果请查看{1}层！".format(drill_layer, drill_layer+"_overlap_hole+++")
                        res = self.check_drill_layer_exists_overlap_hole(step, drill_layer, log)
                        if res:                                
                            arraylist.append(res)
                            dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                                  worklayer="view_layer_"+drill_layer, 
                                                                  dic_layer_list={log:[drill_layer+"_overlap_hole+++"], },
                                                                  dic_zu_layer=dic_zu_layer)
                            
                        if stepname == "panel":
                            res = self.check_panel_edge_touch_holes(step, drill_layer)
                            if res:                                
                                arraylist.append(res)
                                dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                                      worklayer="view_layer_"+drill_layer, 
                                                                      dic_layer_list={res:[drill_layer+"_touch_hole_tmp+++"], },
                                                                      dic_zu_layer=dic_zu_layer)
                                
                #if mai_drill_layers:                
                    #for drill_layer in mai_drill_layers:
                        #lp_layer = "{0}.lp".format(drill_layer)
                        #dq_layer = "{0}...dq".format(drill_layer)
                        
                        #log = u"检测到埋孔层{0}层有重孔，详细结果请查看{1}层！".format(drill_layer, drill_layer+"_overlap_hole+++")
                        #res = self.check_drill_layer_exists_overlap_hole(step, drill_layer, log)
                        #if res:                                
                            #arraylist.append(res)
                            #dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                                  #worklayer="view_layer_"+drill_layer, 
                                                                  #dic_layer_list={log:[drill_layer+"_overlap_hole+++"], },
                                                                  #dic_zu_layer=dic_zu_layer)
                            
                        #for layer in [lp_layer, dq_layer]:                        
                            #if step.isLayer(layer):
                                #if layer == lp_layer:
                                    #log = u"检测到埋孔树脂铝片层{0}层有重孔，详细结果请查看{1}层！".format(layer, layer+"_overlap_hole+++")
                                    #res = self.check_drill_layer_exists_overlap_hole(step, layer, log)
                                    #if res:                                
                                        #arraylist.append(res)
                                        #dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                                              #worklayer="view_layer_"+layer, 
                                                                              #dic_layer_list={log:[layer+"_overlap_hole+++"], },
                                                                              #dic_zu_layer=dic_zu_layer)                       
                                        
                #for layer in tong_lp_layers + tong_dq_layers:
                    #if step.isLayer(layer):
                        #if layer in tong_lp_layers:                        
                            #log = u"检测到通孔树脂铝片层{0}层有重孔，详细结果请查看{1}层！".format(layer, layer+"_overlap_hole+++")
                            #res = self.check_drill_layer_exists_overlap_hole(step, layer, log)
                            #if res:                                
                                #arraylist.append(res)
                                #dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                                      #worklayer="view_layer_"+layer, 
                                                                      #dic_layer_list={log:[layer+"_overlap_hole+++"], },
                                                                      #dic_zu_layer=dic_zu_layer)                              
                
                step.clearAll()
                
        res, new_dic_zu_layer = self.check_drill_layer_features(dic_zu_layer)
        
        if new_dic_zu_layer:
            dic_zu_layer = new_dic_zu_layer
            
        if res != "success":
            arraylist += res
                        
        if arraylist:
            return arraylist, dic_zu_layer
        
        return "success", None
    
    def check_panel_edge_touch_holes(self, step, drill_layer):
        """检测panel板边的相交孔"""
        step.removeLayer(drill_layer+"_touch_hole_tmp+++")
        if re.match("drl|cdc|cds|b\d+-\d+", drill_layer):                
            step.clearAll()
            step.affect(drill_layer)
            step.resetFilter()
            step.selectAll()
            layer_cmd = gClasses.Layer(step, drill_layer)
            feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]
            feat_out += layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["lines"]
            for obj in feat_out:
                step.selectNone()
                step.selectFeatureIndex(drill_layer, obj.feat_index)
                select_feat1 = layer_cmd.featSelOut(units="mm")["pads"]
                step.COM("sel_ref_feat,layers=,use=select,mode=touch,"
                         "pads_as=shape,f_types=line\;pad\;surface\;arc\;text,"
                         "polarity=positive\;negative,include_syms=,exclude_syms=")
                select_feat2 = layer_cmd.featSelOut(units="mm")["pads"]
                select_feat2 += layer_cmd.featSelOut(units="mm")["lines"]
                if step.featureSelected():
                    if select_feat1 and select_feat2:
                        for select_obj in select_feat2:                                
                            if getattr(select_feat1[0], "string", None) == "mdk-hole" or getattr(select_obj, "string", None) == "mdk-hole":
                                if abs(select_feat1[0].x - select_obj.x) > 0.1 or \
                                   abs(select_feat1[0].y - select_obj.y) > 0.1:
                                    break
                            else:
                                break
                        else:
                            continue
                            
                    step.copySel(drill_layer+"_touch_hole_tmp+++")
        
        step.clearAll()
        
        if step.isLayer(drill_layer+"_touch_hole_tmp+++"):
            return u"检测到panel内{0}层 有相交孔，详细请查看备份{1}层!".format(drill_layer, drill_layer+"_touch_hole_tmp+++")
        
        return None
                                           
    def check_drill_layer_exists_overlap_hole(self, step, layer, log):
        layer_cmd = gClasses.Layer(step, layer)
        feat_out = layer_cmd.featCurrent_LayerOut(units="mm")["pads"]
        coordinate_info = [(obj, math.hypot(obj.x, obj.y), obj.x, obj.y, obj.symbol) for obj in feat_out]
        coordinate_info = sorted(coordinate_info, key=lambda x: x[1])
        find_pad = False
        for pre, suffix in zip(coordinate_info[1:], coordinate_info):
            if pre[1] - suffix[1] < 0.1 and pre[2] == suffix[2] and \
               pre[3] == suffix[3] and pre[4] == suffix[4]:
                if not step.isLayer(layer+"_overlap_hole+++"):                    
                    step.createLayer(layer+"_overlap_hole+++")
                step.clearAll()
                step.affect(layer+"_overlap_hole+++")
                obj,_,_,_,_ = pre                  
                step.addPad(obj.x, obj.y, obj.symbol)
                obj,_,_,_,_ = suffix                  
                step.addPad(obj.x, obj.y, obj.symbol)                
                find_pad = True
                
        feat_out = layer_cmd.featCurrent_LayerOut(units="mm")["lines"]
        coordinate_info = [(obj, math.hypot((obj.xs+obj.xe) *0.5, (obj.ys+obj.ye) *0.5),
                            obj.xs, obj.ys, obj.xe, obj.ye,obj.symbol) for obj in feat_out]
        coordinate_info = sorted(coordinate_info, key=lambda x: x[1])
        # find_pad = False
        for pre, suffix in zip(coordinate_info[1:], coordinate_info):
            if pre[1] - suffix[1] < 0.1 and pre[2] == suffix[2] and \
               pre[3] == suffix[3] and pre[4] == suffix[4] and \
               pre[5] == suffix[5] and pre[6] == suffix[6]:
                if not step.isLayer(layer+"_overlap_hole+++"):                    
                    step.createLayer(layer+"_overlap_hole+++")
                step.clearAll()
                step.affect(layer+"_overlap_hole+++")
                obj = pre[0]                  
                step.addLine(obj.xs, obj.ys, obj.xe, obj.ye,obj.symbol)
                obj = suffix[0]                 
                step.addLine(obj.xs, obj.ys, obj.xe, obj.ye,obj.symbol)          
                find_pad = True            
                
        if find_pad:            
            return log.format(layer, layer+"_overlap_hole+++")
        
        return
    
    def get_check_dw_hole_overlap(self, step, checklayer, reflayer, log):
        step.clearAll()
        step.affect(checklayer)
        step.resetFilter()
        step.selectSymbol('r3175', 1, 1)
        if step.featureSelected():
            step.removeLayer(checklayer+"_3175_tmp")
            step.removeLayer(checklayer+"_3175_tmp_bak")
            step.copySel(checklayer+"_3175_tmp")
            step.clearAll()
            step.affect(checklayer+"_3175_tmp")
            step.copySel(checklayer+"_3175_tmp_bak")
            step.contourize()
            step.COM("sel_resize,size=1000")
            step.contourize()
            step.COM("sel_resize,size=-1500")
            step.resetFilter()
            step.refSelectFilter(checklayer+"_3175_tmp_bak", mode="cover")
            step.COM("sel_reverse")
            if step.featureSelected():
                step.selectDelete()
                
            step.clearAll()
            step.affect(checklayer+"_3175_tmp_bak")
            step.refSelectFilter(checklayer+"_3175_tmp", mode="disjoint")
            if step.featureSelected():
                step.selectDelete()
            
            step.removeLayer(checklayer+"_3175_tmp")
            
        if step.isLayer(checklayer+"_3175_tmp_bak"):
            worklayer = checklayer+"_3175_tmp_bak"
        else:
            worklayer = checklayer
            
        step.clearAll()
        step.affect(worklayer) 
        step.resetFilter()
        step.setSymbolFilter("r3175")        
        step.refSelectFilter(reflayer, mode="cover")
        step.COM("sel_reverse")
        if step.featureSelected():
            layer_cmd = gClasses.Layer(step, worklayer)
            feat_out = layer_cmd.featSelOut(units="mm")["pads"]
            r3175_holes = [obj for obj in feat_out if obj.symbol == "r3175"]
            step.removeLayer(checklayer+"_3175_tmp_bak")
            if r3175_holes:
                if not step.isLayer(checklayer+"_dw_hole_error+++"): 
                    step.createLayer(checklayer+"_dw_hole_error+++")
                step.clearAll()
                step.affect(checklayer+"_dw_hole_error+++")
                for obj in r3175_holes:                    
                    step.addPad(obj.x, obj.y, obj.symbol)                
                
                return log.format(checklayer, reflayer, checklayer+"_dw_hole_error+++")
        
        step.removeLayer(checklayer+"_3175_tmp_bak")
        return
    
    def check_drill_layer_features(self, dic_zu_layer={}):
        """检测钻孔层是否存在孔以外的物件"""
        # dic_zu_layer = {}
        arraylist = []
        if "panel" in matrixinfo["gCOLstep_name"]:            
            all_steps = get_panelset_sr_step(job.name, "panel")            
            for stepname in all_steps:                
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")
                
                for i, layer in enumerate(matrixinfo["gROWname"]):
                    if matrixinfo["gROWcontext"][i] == "board" and \
                       matrixinfo["gROWlayer_type"][i] == "drill":
                        step.clearAll()
                        step.affect(layer)
                        step.resetFilter()
                        step.filter_set(feat_types='pad;line', polarity='positive')
                        step.selectAll()
                        step.COM("sel_reverse")
                        if step.featureSelected():
                            log = u"检测到{0}钻孔层{1}存在非孔的物件，请检查！".format(stepname, layer)                                    
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, layer,
                                                                                 layer, log, dic_zu_layer)
                            arraylist.append(log)
                        
                        layer_cmd = gClasses.Layer(step, layer)
                        feat_out = layer_cmd.featCurrent_LayerOut(units="mm")["pads"]
                        find_other_symbol = [obj.symbol for obj in feat_out
                                             if not re.match("r\d+\.?\d+", obj.symbol)]
                        if find_other_symbol:
                            log = u"检测到{0}钻孔层{1}存在非法symbol：{2}的物件，请检查！".format(stepname, layer, find_other_symbol)                                    
                            arraylist.append(log)
                            
                step.clearAll()
            if arraylist:
                return arraylist, dic_zu_layer
            
        return "success", None
    
    def check_loss_pad_for_hole(self, *args):
        """检测埋孔对应的次外层是否有ring的检测项目，比如b3-8,
        那么检测线路层的l3&l8层是否有ring存在，
        增加通孔对应的外层是否存在ring的检测项目（PTH，VIA）.
        对应的icg coupon&set也加入检测。
        增加镭射层 检测
        如无就提醒，如有就显示OK 20221101 by lyh"""
        
        check_type = args[0]
        
        arraylist = []
        dic_zu_layer = {}
        if len(args) >= 2:
            dic_zu_layer = args[1]
            
        if "panel" in matrixinfo["gCOLstep_name"]:            
            all_steps = get_panelset_sr_step(jobname, "panel")

            mai_drill_layers = get_mai_drill_hole(**os.environ)
            
            step = gClasses.Step(job, all_steps[0])
            for layer in mai_drill_layers + laser_drill_layers + ["drl"]:
                step.removeLayer(layer+"_lackpad++")
            
            if check_type == "inner":
                new_laser_drill_layers =laser_drill_layers
                #[layer for layer in laser_drill_layers
                                          #if "s1-" not in layer and "s{0}-".format(lay_num) not in layer]
                if mai_drill_layers:            
                    for stepname in all_steps:
                        for name in ["icg", "set", "edit"]:
                            if name in stepname:                            
                                arraylist,dic_zu_layer = self.check_hole_exists_signal_pad(stepname, mai_drill_layers,
                                                                                           arraylist,dic_zu_layer, check_type)
                                
                if new_laser_drill_layers:            
                    for stepname in all_steps:
                        for name in ["icg", "set", "edit"]:
                            if name in stepname:                            
                                arraylist,dic_zu_layer = self.check_hole_exists_signal_pad(stepname, new_laser_drill_layers,
                                                                                       arraylist,dic_zu_layer, check_type)
            if check_type == "outer":
                new_laser_drill_layers = [layer for layer in laser_drill_layers
                                          if "s1-" in layer or "s{0}-".format(lay_num) in layer]                
                for stepname in all_steps:
                    for name in ["icg", "set", "edit"]:
                        if name in stepname:                    
                            arraylist,dic_zu_layer = self.check_hole_exists_signal_pad(stepname, ["drl"],
                                                                               arraylist,dic_zu_layer, check_type)
                            
                if new_laser_drill_layers:            
                    for stepname in all_steps:
                        for name in ["icg", "set", "edit"]:
                            if name in stepname:                            
                                arraylist,dic_zu_layer = self.check_hole_exists_signal_pad(stepname, new_laser_drill_layers,
                                                                                       arraylist,dic_zu_layer, check_type)                            
                    
        if arraylist:
            return arraylist, dic_zu_layer                    
            
        return "success", None
                
    def check_hole_exists_signal_pad(self, stepname, drill_layers,
                                     arraylist=[], dic_zu_layer={},
                                     check_type=None):
        """检测埋孔对应的次外层是否有ring的检测项目，比如b3-8,
        那么检测线路层的l3&l8层是否有ring存在，
        增加通孔对应的外层是否存在ring的检测项目（PTH，VIA）.
        对应的icg coupon&set也加入检测。 
        如无就提醒，如有就显示OK 20221101 by lyh"""
        #是否灯板
        led_type = get_led_board(job.name)
        
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")       
        for worklayer in drill_layers:
            if not step.isLayer(worklayer):
                continue
            step.clearAll()
            step.affect(worklayer)
            step.resetFilter()
            step.setAttrFilter(".drill,option=plated")
            step.selectAll()
            step.resetFilter()
            step.setAttrFilter(".drill,option=non_plated")
            step.selectAll()
            step.resetFilter()            
            step.setAttrFilter(".drill,option=via")
            step.selectAll()
            step.COM("sel_reverse")
            if step.featureSelected() and "icg" not in stepname:
                if stepname == "set" and re.match("^s\d{1,2}-\d{1,2}", worklayer) and step.featureSelected() == 1:
                    """加lot号的不检测"""
                    continue
                
                log = u"警告:step:{0}通埋孔{1}存在未定义属性的孔，请定义属性!".format(stepname, worklayer)
                arraylist.append(log)
                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, worklayer,
                                                                     worklayer, log, dic_zu_layer)                  
                continue
            
            sig_layers = get_drill_start_end_layers(matrixinfo, worklayer)
            for siglayer in sig_layers:
                
                if check_type == "inner":
                    if siglayer in outsignalLayers:
                        continue
                    
                step.clearAll()
                if led_type:
                    # 灯板不优化负片 否则很卡
                    step.copyLayer(job.name, stepname, siglayer, siglayer+"_check_hole")
                else:
                    if stepname == "set":
                        step.copyLayer(job.name, stepname, siglayer, siglayer+"_check_hole")
                    else:                        
                        step.COM("optimize_levels,layer={0},opt_layer={1}_check_hole,levels=1".format(siglayer, siglayer))
                    step.clearAll()
                    step.affect(siglayer+"_check_hole")
                    step.resetFilter()
                    step.filter_set(polarity='negative')
                    step.selectAll()
                    if step.featureSelected():
                        step.selectNone()
                        step.contourize()
                        
                    if stepname == "icg":
                        step.contourize()
                    
                step.resetFilter()
                step.clearAll()
                # step.display(worklayer, work=1)
                step.affect(worklayer)
                step.removeLayer(worklayer+"_check_pad")
                step.copySel(worklayer+"_check_pad")
                # step.display(worklayer+"_check_pad", work=1)
                step.clearAll()
                step.affect(worklayer+"_check_pad")
                step.resetFilter()
                step.setAttrFilter(".drill,option=non_plated")
                step.selectAll()
                if step.featureSelected():
                    step.selectDelete()
                    
                if worklayer.startswith("s"):
                    # 镭射层去掉lot号孔
                    step.resetFilter()
                    step.resetAttr()
                    step.selectSymbol("r515", 1, 1)
                    if step.featureSelected():
                        step.selectDelete()
                        
                #去掉背钻的孔
                # 翟鸣通知 去掉，这次就是死在这里的。不管有没有背钻，只管该镀铜的孔外层要有pad 20231120 by lyh
                #for row, bd_layer in enumerate(matrixinfo["gROWname"]):
                    #if bd_layer.startswith("bd") and matrixinfo["gROWlayer_type"][row] == "drill":
                        #step.resetFilter()
                        #step.resetAttr()
                        #step.COM("reset_filter_criteria,filter_name=ref_select,criteria=inc_attr")
                        #step.refSelectFilter(bd_layer, mode="cover", polarity="positive")
                        ##if "-lyh" in job.name and stepname == "edit" and worklayer == "drl":
                            ##step.PAUSE("ddd")                        
                        #if step.featureSelected():
                            #step.selectDelete()
                
                step.resetFilter()
                step.resetAttr()
                step.COM("adv_filter_reset")
                step.COM("reset_filter_criteria,filter_name=,criteria=all")
                step.COM("reset_filter_criteria,filter_name=ref_select,criteria=inc_attr")
                step.refSelectFilter("{0}_check_hole".format(siglayer), mode="cover", polarity="positive")
                step.COM("sel_reverse")
                #if "-lyh" in job.name and "edit" in step.name:
                    #step.PAUSE("ddd")                
                if step.featureSelected():                   
                    step.copySel(worklayer+"_lackpad++")                        
                    log= u"Warning系统检测到step:{0} ,layer:{1}有孔对应线路{3}无Pad，请检查！".format(stepname, worklayer, worklayer, siglayer)
                    arraylist.append(log)                    
                    
                    step.clearAll()
                    step.affect(worklayer)
                    step.resetFilter()
                    step.refSelectFilter(worklayer+"_lackpad++")                    
                    
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, worklayer,
                                                                         siglayer, log, dic_zu_layer)                    
                step.removeLayer(siglayer+"_check_hole")
            step.removeLayer(worklayer+"_check_pad")
            step.removeLayer(worklayer+"_lackpad++")
            step.clearAll()
            
        return arraylist, dic_zu_layer
    
    def check_npth_hole_condition(self, auto_check=None):
        """输出TGZ增加卡关，1，监测NPTH孔是否有套铜皮单边8mil。(输出内外TGZ都检测）如没有套铜皮提醒修改。
        2，监测NPTH孔是否存在防焊开窗及档点。（输出外层TGZ检测）如未存在开窗及档点提醒修改。
        3，监测NPTH孔对应的sgt-c,sgt-s层是否存在开窗。（输出外层TGZ检测）如未存在开窗提醒修改。
        5, 输出TGZ增加检测二维码的正反（根据层别识别）
        http://192.168.2.120:82/zentao/story-view-4696.html 20221115 by lyh
        """
        tmp_file = os.path.join(job.tmpdir, "exit_script_run_{0}".format(job.name))
        if os.path.exists(tmp_file):
            os.unlink(tmp_file)
            
        force_exit_script = False# 设置是否强制退出tgz输出程序
        arraylist = []
        dic_zu_layer = {}
        if "panel" in matrixinfo["gCOLstep_name"]:
            
            if "drl" not in matrixinfo["gROWname"]:
                if "tk.ykj" not in matrixinfo["gROWname"]:                    
                    return u"drl跟tk.ykj不存在", None
            
            all_steps = get_panelset_sr_step(job.name, "panel")

            res = os.environ.get("INNER_OUTER", "outer")
            
            if res == "inner":
                check_sig_layers = innersignalLayers
            else:
                check_sig_layers = outsignalLayers
                
            step = gClasses.Step(job, "panel")
            step.removeLayer("npth_clip_cu_not_enough")
            drill_layer = "tk.ykj" if step.isLayer("tk.ykj") else "drl"
            for stepname in all_steps:
                dic_zu_layer[stepname] = {}
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")
                step.clearAll()
                if stepname == "set":
                    step.flatten_layer(drill_layer, drill_layer+"_tmp")
                    step.affect(drill_layer+"_tmp")
                    if step.isLayer("2nd"):
                        step.flatten_layer("2nd", "2nd_tmp")
                        step.affect("2nd_tmp")
                else:
                    step.affect(drill_layer)
                    if step.isLayer("2nd"):
                        step.affect("2nd")

                step.resetFilter()
                step.setAttrFilter(".drill,option=non_plated")
                step.selectAll()                
                if not step.featureSelected():
                    continue
                step.removeLayer("npth_tmp")
                step.copySel("npth_tmp")
                
                step.removeLayer(drill_layer+"_tmp")
                step.removeLayer("2nd_tmp")
                
                #此处因有些槽会被加锣链导致加大会报错 故先删除属性在加大
                step.clearAll()
                step.affect("npth_tmp")
                
                if res == "outer":
                    # 周涌通知 输出全套tgz的时候，要排除cdc与cds的时候 20221230 by lyh                    
                    step.resetFilter()
                    if step.isLayer("cdc"):
                        step.refSelectFilter("cdc", mode="include")
                        step.refSelectFilter("cdc", mode="cover")
                        if step.featureSelected():
                            step.selectDelete()
                    if step.isLayer("cds"):
                        step.refSelectFilter("cds", mode="include")
                        step.refSelectFilter("cds", mode="cover")
                        if step.featureSelected():
                            step.selectDelete()
                        
                step.VOF()
                step.COM("sel_delete_atr,mode=list,attributes=.rout_chain")
                step.VON()
                step.COM("sel_resize,size={0}".format(16*25.4))
                
                for worklayer in check_sig_layers:
                    
                    step.clearAll()
                    step.affect("npth_tmp")
                    step.resetFilter()
                    if stepname == "set":
                        step.flatten_layer(worklayer, worklayer+"_flt")
                        step.refSelectFilter(worklayer+"_flt")
                        suffix = "_flt"
                    else:
                        step.refSelectFilter(worklayer)
                        suffix = ""
                    if not step.featureSelected():
                        continue
                    
                    step.copyLayer(job.name, stepname, worklayer+suffix, worklayer+suffix+"_tmp")
                    step.clearAll()
                    step.affect(worklayer+suffix+"_tmp")
                    step.contourize()
                    #因表面化精度差异 这里减50um
                    step.COM("sel_resize,size=-50")
                    
                    step.clearAll()
                    step.affect("npth_tmp")
                    step.resetFilter()
                    step.refSelectFilter(worklayer+suffix+"_tmp")
                    if step.featureSelected():
                        log = u"检测{0}中npth孔掏{1}层铜不够单边8mil，请到npth_clip_cu_not_enough层检查相应的孔位置查看！"
                        arraylist.append(log.format(stepname, worklayer))                        
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "npth_tmp",
                                                                             worklayer, log.format(stepname, worklayer),
                                                                             dic_zu_layer, delete_note=False,
                                                                             add_note_layer="npth_clip_cu_not_enough")  
                        step.copySel("npth_clip_cu_not_enough")

                    step.removeLayer(worklayer+suffix+"_tmp")
                    step.removeLayer(worklayer+"_flt")
                
                #以下针对为外层tgz输出检测
                if res <> "outer":
                    continue
                
                # 切片孔暂时不检测 20230504 by lyh
                if "qie_hole_coupon_new_" in stepname:
                    continue
                
                step.clearAll()
                step.affect("npth_tmp")
                step.COM("sel_resize,size=-{0}".format(16*25.4))
                for worklayer in solderMaskLayers:
                    step.flatten_layer(worklayer, worklayer+"_tmp")
                    # step.copyLayer(job.name, stepname, worklayer, worklayer+"_tmp")
                    step.clearAll()
                    step.affect(worklayer+"_tmp")
                    step.contourize()
                    
                    step.resetFilter()
                    step.clearAll()
                    step.affect("npth_tmp")
                    step.refSelectFilter(worklayer+"_tmp", mode="cover", polarity="positive")
                    step.COM("sel_reverse")
                    if step.featureSelected():                        
                        log = u"检测{0}中npth孔在{1}层中没有开窗，请到npth_clip_cu_not_enough层检查相应的孔位置查看！"
                        arraylist.append(log.format(stepname, worklayer))
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "npth_tmp",
                                                                             worklayer, log.format(stepname, worklayer), dic_zu_layer, delete_note=False,
                                                                             add_note_layer="npth_clip_cu_not_enough")
                        step.copySel("npth_clip_cu_not_enough")
                        
                        force_exit_script = True
                        
                    step.removeLayer(worklayer+"_tmp")
                    
                for worklayer in ["md1", "md2", "sgt-c","sgt-s"]:
                    if step.isLayer(worklayer):
                        step.flatten_layer(worklayer, worklayer+"_tmp")
                        # step.copyLayer(job.name, stepname, worklayer, worklayer+"_tmp")
                        step.clearAll()
                        step.affect(worklayer+"_tmp")
                        step.contourize()
                        
                        step.resetFilter()
                        step.clearAll()
                        step.affect("npth_tmp")
                        step.refSelectFilter(worklayer+"_tmp", polarity="positive")
                        step.COM("sel_reverse")
                        if step.featureSelected():                            
                            log = u"检测{0}中npth孔在{1}层中没有开窗，请到npth_clip_cu_not_enough层检查相应的孔位置查看！"
                            arraylist.append(log.format(stepname, worklayer))   
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "npth_tmp",
                                                                                 worklayer, log.format(stepname, worklayer), dic_zu_layer, delete_note=False,
                                                                                 add_note_layer="npth_clip_cu_not_enough")
                            step.copySel("npth_clip_cu_not_enough")
                            
                            if worklayer in ["md1", "md2"]:
                                force_exit_script = True
                                         
                        step.removeLayer(worklayer+"_tmp")
                        
            step.removeLayer("npth_tmp")                       
        
        if arraylist:     
            if auto_check is None:
                arraylist_barcode, dic_zu_layer_barcode = self.check_barcode_condition()
                arraylist += arraylist_barcode                  
                if force_exit_script:
                    arraylist.append(u"请修改ok后再重新输出tgz！！！！")
                else:
                    arraylist.append(u"请确认资料是否ok，点击ok继续输出")                
                showMessageInfo(*arraylist)
                
                if force_exit_script:                
                    with open(tmp_file, "w") as f:
                        f.write("yes")
                        
                for dic_zu in [dic_zu_layer, dic_zu_layer_barcode]:
                    for stepname, value in dic_zu.iteritems():
                        for worklayer, array_info in value.iteritems():
                            step = gClasses.Step(job, stepname)
                            checkrule.deleteNote(job.name, stepname, worklayer)
                            for coordinate, note_info,display_layer in array_info:                        
                                checkrule.addNote(step, worklayer, coordinate, "please check")
                                if step.isLayer("npth_clip_cu_not_enough"):                                
                                    step.display_layer("npth_clip_cu_not_enough", 2)
                                step.PAUSE("step: {0} layer: {1}  {2}".format(stepname, worklayer, note_info))                           
            else:
                return arraylist, dic_zu_layer                             
        
        return "success", None
    
    def check_barcode_condition(self):
        """检测二维码是否镜像
        5, 输出TGZ增加检测二维码的正反（根据层别识别）
        http://192.168.2.120:82/zentao/story-view-4696.html 20221115 by lyh"""
        
        tmp_file = os.path.join(job.tmpdir, "exit_script_run_{0}".format(job.name))
        if os.path.exists(tmp_file):
            os.unlink(tmp_file)
            
        arraylist = []
        dic_zu_layer = {}
        check_layers = silkscreenLayers + solderMaskLayers + outsignalLayers
        if "set" in matrixinfo["gCOLstep_name"]:
            #all_steps = get_panelset_sr_step(job.name, "panel")  
            #for stepname in all_steps:
            stepname = "set"
            step = gClasses.Step(job, stepname)
            step.open()
            dic_zu_layer[stepname] = {}
            for worklayer in check_layers:
                layer_cmd = gClasses.Layer(step, worklayer)
                bar_feat_out = layer_cmd.featout_dic_Index(options="feat_index", units="mm")["barcodes"]
                pad_feat_out = layer_cmd.featout_dic_Index(options="feat_index", units="mm")["pads"]
                pad_feat_out = [obj for obj in pad_feat_out
                                if re.search("zq-(2wm|ewm|wm)",obj.symbol)]
                
                if bar_feat_out + pad_feat_out:
                    log = ""
                    allsymbol_xy = []
                    for obj in bar_feat_out + pad_feat_out:                        
                        if obj.mirror == "yes":
                            if worklayer in ["l1", "c1", "m1"]:
                                log = u"检测{0}中{1}层中存在二维码 被镜像，此面二维码无需镜像，请检查！".format(stepname, worklayer)
                                allsymbol_xy.append((obj.x, obj.y, obj.text))
                        
                        if obj.mirror == "no":
                            if worklayer in ["l{0}".format(lay_num), "c2", "m2"]:
                                log = u"检测{0}中{1}层中存在二维码 没有被镜像，此面二维码需要镜像，请检查！".format(stepname, worklayer)
                                allsymbol_xy.append((obj.x, obj.y, obj.text))
                        
                    if allsymbol_xy:
                        if dic_zu_layer[stepname].has_key(worklayer):
                            dic_zu_layer[stepname][worklayer].append([allsymbol_xy,log.encode("utf8") ])                                                            
                        else:
                            dic_zu_layer[stepname][worklayer] = [[allsymbol_xy, log.encode("utf8")]]                        
                                                            
                    if log:
                        arraylist.append(log)
                    
                    indexes = [obj.feat_index for obj in bar_feat_out]
                    step.clearAll()
                    step.affect(worklayer)
                    step.resetFilter()                        
                    for index in indexes:
                        step.selectFeatureIndex(worklayer, index)
                        if step.featureSelected():
                            step.removeLayer("barcode_tmp")
                            step.copySel("barcode_tmp")
                            step.filter_set(feat_types='pad;line;arc;surface', polarity='positive')
                            step.refSelectFilter("barcode_tmp", mode='include',f_types="text", polarity="negative")
                            if step.featureSelected():
                                sel_indexes = layer_cmd.featSelIndex()
                                for sel_index in sel_indexes:
                                    if int(index) < int(sel_index):
                                        log = u"检测{0}中{1}层中存在二维码 被铜皮或pad覆盖，请检查！".format(stepname, worklayer)
                                        arraylist.append(log)                                        
                                        
                                        STR = r'-t layer -e %s/%s/%s -d FEATURES -o select,units= mm' % (
                                                            job.name, stepname,worklayer)
                                        infoList = step.INFO(STR)
                                        if dic_zu_layer[stepname].has_key(worklayer):
                                            dic_zu_layer[stepname][worklayer].append([checkrule.parseInfoList(step, infoList), log.encode("utf8")])                                                            
                                        else:
                                            dic_zu_layer[stepname][worklayer] = [[checkrule.parseInfoList(step, infoList), log.encode("utf8")]]
                                            
                    step.removeLayer("barcode_tmp")
                    
        if arraylist:
            with open(tmp_file, "w") as f:
                f.write("yes")
                    
        return arraylist,dic_zu_layer
    
    def check_pnl_exists_copper_area_value(self):
        """检测正片流程外层板边是否有残铜率"""
        if "panel" not in matrixinfo["gCOLstep_name"]:
            return u"panel不存在", None
        
        stepname = "panel"
        arraylist = []
        dic_zu_layer = {}
        data_info = get_plating_type(job.name)
        if data_info:
            check_layers = []
            for info in data_info:
                if "Final Assembly" in info.get("PROCESS_NAME", ""):
                    if info.get("PLATING_TYPE_", "") == 2:
                        check_layers.append(info.get("LAYER_NAME"))
            
            if check_layers:
                step = gClasses.Step(job, stepname)
                step.open()

                for worklayer in outsignalLayers:
                    if not step.isLayer(worklayer):
                        continue
                    
                    step.clearAll()
                    step.resetFilter()
                    step.affect(worklayer)
                    
                    step.selectSymbol("chris-tudian", 1, 1)
                    if step.featureSelected():
                        layer_cmd = gClasses.Layer(step, worklayer)
                        feat_out1 = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]
                        for obj1 in feat_out1:
                            step.selectNone()
                            step.resetFilter()
                            step.selectFeatureIndex(worklayer, obj1.feat_index)
                            xmin, ymin, xmax, ymax = get_layer_selected_limits(step, worklayer)
                            step.selectNone()
                            step.filter_set(feat_types='text')
                            step.selectRectangle(xmin, ymin, xmax, ymax, intersect="yes")
                            if step.featureSelected():
                                feat_out2 = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["text"]
                                copper_text = [obj2.text for obj2 in feat_out2]
                                for obj2 in feat_out2:
                                    if obj2.feat_index > obj1.feat_index:
                                        break
                                else:
                                    step.selectNone()
                                    step.selectFeatureIndex(worklayer, obj1.feat_index)
                                    log= u"检测到正片板边{0} 图电symbol索引：{1}上没有残铜率 text，请检查是否被覆盖！"
                                    arraylist.append(log.format(worklayer, obj1.feat_index)) 
                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, worklayer,
                                                                                         worklayer, log.format(worklayer, obj1.feat_index), dic_zu_layer)                                     
                            else:
                                step.selectFeatureIndex(worklayer, obj1.feat_index)
                                log= u"检测到正片板边{0} 图电symbol索引：{1}上没有残铜率 text，请检查标记位置是否异常！"
                                arraylist.append(log.format(worklayer, obj1.feat_index)) 
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, worklayer,
                                                                                     worklayer, log.format(worklayer, obj1.feat_index), dic_zu_layer)
                    else:
                        log= u"检测到正片板边{0} 没有图电symbol：chris-tudian，请检查！"
                        arraylist.append(log.format(worklayer))
                        
                step.clearAll()
            else:
                return u"success 非正片板流程，无需检测", None
            
        if arraylist:
            return arraylist, dic_zu_layer
        
        return "success", None
    
    def check_ccd_drill_conformation(self):
        """检查ccd钻是否正常 有钻带及定位孔 20230613 by lyh
        http://192.168.2.120:82/zentao/story-view-5655.html"""
        data_info = get_inplan_all_flow(job.name, select_dic=True)
        ccd_process = ['HDI24701','HDI24801','HDI24901']
        array_ccd_info = [dic_info for dic_info in data_info
                    if dic_info["OPERATION_CODE"] in ccd_process]
        tools = list(set([x["VALUE_AS_STRING"] for x in array_ccd_info]))
        
        find_genesis_ccd_layers = []
        for i, layername in enumerate(matrixinfo["gROWname"]):
            if matrixinfo["gROWlayer_type"][i] == "drill" and \
               matrixinfo["gROWcontext"][i] == "board":
                if "_ccd" in layername and ".inn" not in layername:
                    find_genesis_ccd_layers.append(layername)
                    
        if array_ccd_info:                        
            if not find_genesis_ccd_layers:
                return u"检测到此型号有ccd钻流程工具{0}，但资料没未发现ccd钻层名(注：ccd钻层名以_ccd结尾)，请确认层名命名是否正确！".format(tools), None
            
        if find_genesis_ccd_layers:
            if not array_ccd_info:
                return u"检测到资料内有ccd钻层名{0}，但inplan内无ccd钻流程{1},请反馈MI处理！".format(find_genesis_ccd_layers, ccd_process), None
            
            arraylist_log = []
            for layer in find_genesis_ccd_layers:
                for dic_info in array_ccd_info:
                    if layer in str(dic_info["VALUE_AS_STRING"]).lower():
                        break
                    if layer in str(dic_info["NOTE_STRING"]).lower():
                        break                    
                else:
                    log = u"检测到资料内有ccd钻层名{0},但inplan内ccd钻流程中没有匹配此层名的工具，请反馈MI处理!".format(layer)
                    arraylist_log.append(log)
                    
                if layer + ".inn" not in matrixinfo["gROWname"]:
                    log = u"检测到资料内有ccd钻层名{0}，但没有ccd定位孔层{1}.inn，请检查！".format(layer, layer)
                    arraylist_log.append(log)
            
            if arraylist_log:
                return arraylist_log, None
            
        return "success", None
    
    def check_aobao_danymic_text_info(self, *layers):
        """检测奥宝明码 大小是否符合最新设计
        有2/6 3/6 4/6才放行，没有这种的卡主
        http://192.168.2.120:82/zentao/story-view-7548.html 20241012"""
      
        if "panel" not in matrixinfo["gCOLstep_name"]:
            return u"panel不存在", None
        
        stepname = "panel"
        arraylist = []
        dic_zu_layer = {}
        
        auto_check_type = os.environ.get("INNER_OUTER", "")
        check_layers = layers
        if not layers:
            if auto_check_type == "inner":
                check_layers = innersignalLayers
                
            if auto_check_type == "outer":
                check_layers = outsignalLayers + solderMaskLayers     
        
        all_steps = get_panelset_sr_step(job.name, "panel")
        for stepname in all_steps + ["panel"]:            
            step = gClasses.Step(job, stepname)
            step.open()           
            for worklayer in check_layers:
                step.clearAll()
                step.affect(worklayer)
                step.resetFilter()
                step.filter_set(feat_types='text')
                step.selectAll()
                layer_cmd = gClasses.Layer(step, worklayer)
                if step.featureSelected():
                    feat_out = layer_cmd.featout_dic_Index(options="feat_index+select")["text"]
                    barcode_feat_out = layer_cmd.featout_dic_Index(options="feat_index+select")["barcodes"]
                    for obj in feat_out + barcode_feat_out:                        
                        if "-SSS" == str(obj.text).upper().replace("'", "") or \
                           "B1001001" == str(obj.text).upper().replace("'", "") or \
                           "H1SSSSSS11111SSS" == str(obj.text).upper().replace("'", "") or \
                           "B2123123SSS" == str(obj.text).upper().replace("'", ""):
                            
                            if obj.shape == "Text":                                
                                xsize = round(obj.xsize*1000, 1)
                                ysize = round(obj.ysize*1000, 1)
                                factor = obj.wfactor
                                # step.PAUSE(str([xsize, ysize, factor, obj.text]))
                                # 周涌通知输出LDI时及内部升级版不检测大小  其他情况都检测
                                if auto_check_type and job.name.split("-")[0][-1] == "1":                                    
                                    if abs(xsize - ysize) > 0.1 or not (
                                        (abs(xsize - 22) < 0.1 and abs(factor - 0.25) < 0.01) or
                                        (abs(xsize - 33) < 0.1 and abs(factor - 0.3333333433) < 0.01) or
                                        (abs(xsize - 44) < 0.1 and abs(factor - 0.5) < 0.01)
                                    ):
                                        log = u"检测到{0} 层存在{1} 明码，但字高字宽不是2/6 3/6 4/6三种类型，<br>实际字高字宽为{2},请调整后输出！"
                                        arraylist.append(log.format(worklayer, obj.text, ["%0.1f" % xsize, "%0.1f" % ysize, "%0.1f" % (factor / 0.5 *6)]))
                                        step.selectNone()
                                        step.selectFeatureIndex(worklayer, obj.feat_index)
                                        
                                        dic_zu_layer = self.get_selected_dic_note_coordinate(
                                            job.name, stepname, step, worklayer,worklayer,
                                            log.format(worklayer, obj.text, ["%0.1f" % xsize, "%0.1f" % ysize, "%0.1f" % (factor / 0.5 *6)]), dic_zu_layer)                                
                            #周涌通知 取消检测 20241016 by lyh
                            #if obj.shape == "Barcode":
                                #width = obj.width * 25.4
                                #height = obj.height * 25.4
                                ##if "-lyh" in job.name:
                                    ##step.PAUSE(str([width, height, abs(width - 4.5), height - 4.5]))
                                #if (width < 4.5 and abs(width - 4.5) > 0.1) or \
                                   #(height < 4.5 and abs(height - 4.5) > 0.1):
                                    #log = u"检测到{0} 层存在{1} 二维码，但高宽小于4.5，<br>实际属性为{2},请修改后输出！"
                                    #arraylist.append(log.format(worklayer, obj.text, [width, height]))
                                    #step.selectNone()
                                    #step.selectFeatureIndex(worklayer, obj.feat_index)
                                    
                                    #dic_zu_layer = self.get_selected_dic_note_coordinate(
                                        #job.name, stepname, step, worklayer,worklayer,
                                        #log.format(worklayer, obj.text, [width, height]), dic_zu_layer) 
                                
                            if "deferred" not in obj.attributes or \
                               "orbotech_plot_stamp" not in obj.attributes:
                                log = u"检测到{0} 层存在{1} 明码，但缺少.deferred 或.orbotech_plot_stamp，<br>实际属性为{2},请添加后输出！"
                                if obj.shape == "Barcode":
                                    log = u"检测到{0} 层存在{1} 二维码，但缺少.deferred 或.orbotech_plot_stamp，<br>实际属性为{2},请添加后输出！"
                                    
                                arraylist.append(log.format(worklayer, obj.text, obj.attributes))
                                step.selectNone()
                                step.selectFeatureIndex(worklayer, obj.feat_index)
                                
                                dic_zu_layer = self.get_selected_dic_note_coordinate(
                                    job.name, stepname, step, worklayer,worklayer,
                                    log.format(worklayer, obj.text, obj.attributes), dic_zu_layer)                                 
                                
                step.clearAll()
                            
        if arraylist:
            if layers and os.environ.get("SHOW_UI", "yes") == "yes":                
                showMessageInfo(*arraylist)
                self.view_note_detail(dic_zu_layer)
                #with open("/tmp/exit_script_run_".format(job.name), "w") as f:
                    #f.write("yes")
                exit(1)
                
            return arraylist, dic_zu_layer
        
        if layers and os.environ.get("SHOW_UI", "yes") == "yes":
            exit(0)
            
        return "success", None
    
    def check_record_week_picihao_to_mysql(self, *args):
        """检测是否有登记周期批次号数量面次等信息 20241022 by lyh"""
        sql = "select job_detail_info_for_output from hdi_engineering.incam_job_layer_info\
        where job_name = '{0}' and job_detail_info_for_output is not null"
        data_info = conn.SELECT_DIC(dbc_m, sql.format(jobname.split("-")[0]))
        if not data_info:
            showMessageInfo(u"检测到资料未登记公共程序内的 CAM资料数据记录程序，请登记ok后再输出资料！")
                    
            # if os.environ.get("SHOW_UI", "yes") == "yes":
            if "SHOW_UI" in args:                
                exit(1)
            else:
                return "error", None
        else:
            try:
                job_detail_info_for_output = json.loads(data_info[0]["job_detail_info_for_output"], encoding='utf8')
            except:
                job_detail_info_for_output = None
            
            check_status = "success"
            if job_detail_info_for_output is None:
                check_status = "error"
            else:
                for key, value in job_detail_info_for_output.iteritems():
                    if key == "week_table":
                        for info in value:
                            if info[-1] != u"审核OK":
                                check_status = "error"
                
            if check_status == "error":
                showMessageInfo(u"检测到资料 CAM资料数据记录程序 有数据未审核，请通知CAM审核后再输出资料！")
                # if os.environ.get("SHOW_UI", "yes") == "yes":
                if "SHOW_UI" in args:            
                    exit(1)
                else:
                    return "error", None
                
            res = self.check_week_picihao_banci_diff_mysql_record(job_detail_info_for_output, *args)
            if res[0] == "error":
                showMessageInfo(*res[1])
                # if os.environ.get("SHOW_UI", "yes") == "yes":
                if "SHOW_UI" in args:            
                    exit(1)
                else:
                    return "error", None
            
        # if os.environ.get("SHOW_UI", "yes") == "yes":
        if "SHOW_UI" in args:            
            exit(0)
        else:            
            return "success",None
        
    def check_week_picihao_banci_diff_mysql_record(self, dic_job_detail_info_for_output, *args):
        """检测周期批次号班次信息跟mysql内登记的信息是否一致 20241023 by lyh"""
        if not dic_job_detail_info_for_output:
            sql = "select job_detail_info_for_output from hdi_engineering.incam_job_layer_info\
            where job_name = '{0}' and job_detail_info_for_output is not null"
            data_info = conn.SELECT_DIC(dbc_m, sql.format(jobname.split("-")[0]))
            try:
                dic_job_detail_info_for_output = json.loads(data_info[0]["job_detail_info_for_output"], encoding='utf8')
            except:
                dic_job_detail_info_for_output = {}
        
        res = self.get_week_picihao_banci_info(*args)
        if res:
            dic_tgz_week_layers, dic_tgz_barcode_week_layers, dic_tgz_banci_layers, dic_tgz_picihao_layers, week_font = res
        else:
            return "error", [u"获取板内周期信息失败，请反馈程序组查看！"]
        
        arraylist_log = []
        for key, value in dic_job_detail_info_for_output.iteritems():
            if key == "week_table":                
                for info in value:
                    order, name, layer1, num1, layer2, num2,layer3, num3,status = info
                    if ("signal" in args and layer1 != "/" and num1 != "0") or \
                       ("solder_mask" in args and layer2 != "/" and num2 != "0"):
                        array_layers = layer1.split() if "signal" in args else layer2.split()
                        calc_num = 0
                        
                        for worklayer in array_layers:                                
                            if order == "1":  
                                calc_num += len(dic_tgz_week_layers.get(worklayer, []))
                            if order == "2":
                                calc_num += len(dic_tgz_barcode_week_layers.get(worklayer, []))
                            if order == "3":
                                calc_num += len(dic_tgz_picihao_layers.get(worklayer, []))
                            if order == "4":
                                calc_num += len(dic_tgz_banci_layers.get(worklayer, []))                                 

                        if calc_num != int(num):
                            log = u"获取{0}层板内{3}个数{1}跟登记数量{2}不一致，请检查板内{3}情况！"
                            arraylist_log.append(log.format(layer, calc_num, num, name))
                            
                if dic_tgz_week_layers:
                    num = 0
                    for key, vaules in dic_tgz_week_layers.iteritems():
                        num += len(vaules)
                    if ("signal" in args and int(value[0][3]) != num) or\
                       ("solder_mask" in args and int(value[0][5]) != num):
                        log = u"获取{0}层板内{3}个数{1}跟登记数量{2}不一致，请检查板内{3}情况！"
                        arraylist_log.append(log.format(dic_tgz_week_layers.keys(), num, value[0][3], value[0][1]))
                    
                if dic_tgz_barcode_week_layers:
                    num = 0
                    for key, vaules in dic_tgz_barcode_week_layers.iteritems():
                        num += len(vaules)
                    if ("signal" in args and int(value[1][3]) != num) or\
                       ("solder_mask" in args and int(value[1][5]) != num):
                        log = u"获取{0}层板内{3}个数{1}跟登记数量{2}不一致，请检查板内{3}情况！"
                        arraylist_log.append(log.format(dic_tgz_barcode_week_layers.keys(), num, value[0][3], value[0][1]))                        
                    
                if dic_tgz_picihao_layers:
                    num = 0
                    for key, vaules in dic_tgz_picihao_layers.iteritems():
                        num += len(vaules)
                    if ("signal" in args and int(value[2][3]) != num) or\
                       ("solder_mask" in args and int(value[2][5]) != num):
                        log = u"获取{0}层板内{3}个数{1}跟登记数量{2}不一致，请检查板内{3}情况！"
                        arraylist_log.append(log.format(dic_tgz_picihao_layers.keys(), num, value[0][3], value[0][1]))                           
                
                if dic_tgz_banci_layers:
                    num = 0
                    for key, vaules in dic_tgz_banci_layers.iteritems():
                        num += len(vaules)
                    if ("signal" in args and int(value[2][3]) != num) or\
                       ("solder_mask" in args and int(value[2][5]) != num):
                        log = u"获取{0}层板内{3}个数{1}跟登记数量{2}不一致，请检查板内{3}情况！"
                        arraylist_log.append(log.format(dic_tgz_banci_layers.keys(), num, value[0][3], value[0][1]))                           
                            
        if arraylist_log:
            return "error", arraylist_log 
        
        return "success",None 
    
    def check_set_to_set_connection_mask_open(self, *args):
        """检测连接位置是否开窗 20241014 by lyh
        http://192.168.2.120:82/zentao/story-view-7549.html"""
        arraylist_log = []
        dic_zu_layer = {}
        data_info = get_job_attr_info(job.name, "CI_CONNECTION_OPEN_WINDOW_")
        if data_info:
            if data_info[0]["VALUE"].decode("utf8") != u"是":
                return u"success inplan连接位是否开窗栏位：{0},无需检测！", None
        else:
            return u"success 未获取到inplan连接位是否开窗栏位信息,无需检测！", None
        
        if "set" in matrixinfo["gCOLstep_name"]:            
            edit_steps = [name for name in matrixinfo["gCOLstep_name"] if "edit" in name]        
            get_sr_area_flatten("set_fill_surface", stepname="set", include_sr_step=edit_steps)
            stepname = "set"
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            
            if step.isLayer("set_fill_surface"):
                step.copyLayer(job.name, step.name, "set_fill_surface", "set_fill_surface_bak")
                step.clearAll()
                step.affect("set_fill_surface")
                step.COM("sel_resize,size=800")
                step.removeLayer("find_connection_line")
                
                step.COM("sel_surf2outline,width=1")
                if step.isLayer("ww"):
                    step.flatten_layer("ww", "ww_flt")
                    
                    step.clearAll()
                    step.affect("ww_flt")                    
                    step.resetFilter()
                    step.filter_set(feat_types='line;arc', polarity='positive')
                    step.refSelectFilter("set_fill_surface")
                    if step.featureSelected():
                        step.copySel("find_connection")
                        
                        step.clearAll()
                        step.affect("set_fill_surface")
                        step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                                 "area_type=rectangle,inout=inside,contour_cut=no,margin={2},"
                                 "ref_layer={1},feat_types=line\;pad\;surface\;arc\;text".format(
                                     "set_fill_surface",
                                     "find_connection", 0
                                 ))
                        
                        step.clearAll()
                        step.copyLayer(job.name, step.name, "find_connection", "find_connection_tmp")
                        step.affect("find_connection_tmp")
                        step.COM("sel_resize,size=10")
                        step.contourize()
                        step.resetAttr()
                        step.addAttr(".area", valType='', change_attr="yes")
                        step.copySel("set_fill_surface")
                        
                        step.clearAll()
                        step.affect("set_fill_surface")
                        step.resetFilter()
                        step.setAttrFilter(".area")
                        step.selectAll()
                        feat_indexes = []
                        layer_cmd = gClasses.Layer(step, "set_fill_surface")
                        if step.featureSelected():                            
                            feat_indexes = layer_cmd.featSelIndex()
                        else:
                            pass
                        
                        step.resetFilter()
                        dic_find_sel_polyline_xy = {}
                        for index in feat_indexes:
                            step.selectNone()
                            step.selectFeatureIndex("set_fill_surface", index)
                            find_sel_polyline_xy = []
                            if step.featureSelected():
                                step.COM("sel_ref_feat,layers=,use=select,mode=touch,\
                                pads_as=shape,f_types=line\;pad\;surface\;arc\;text,\
                                polarity=positive\;negative,include_syms=,exclude_syms=")
                                feat_out = layer_cmd.featSelOut(units="mm")["lines"]
                                for obj in feat_out:
                                    step.selectNone()
                                    sel_x = (obj.xe + obj.xs) * 0.5
                                    sel_y = (obj.ye + obj.ys) * 0.5
                                    find_sel_polyline_xy.append([sel_x, sel_y])
                                    
                                feat_out = layer_cmd.featSelOut(units="mm")["arcs"]
                                for obj in feat_out:
                                    step.selectNone()
                                    sel_x = obj.xe# (obj.xe + obj.xs) * 0.5
                                    sel_y = obj.ye# (obj.ye + obj.ys) * 0.5
                                    find_sel_polyline_xy.append([sel_x, sel_y])                                    
                                    
                            dic_find_sel_polyline_xy[index] = find_sel_polyline_xy
                        
                        step.selectNone()
                        step.resetFilter()
                        step.setAttrFilter(".area")
                        step.selectAll()
                        if step.featureSelected():
                            step.selectDelete()
                        
                        for key, array_xy in dic_find_sel_polyline_xy.iteritems():
                            tmp_length = 100
                            tmp_layer = str(key)
                            step.clearAll()
                            step.affect("set_fill_surface")
                            for sel_x, sel_y in array_xy:
                                step.resetFilter()
                                step.selectNone()
                                step.COM("sel_polyline_feat,operation=select,x={0},y={1},tol=76.2225"
                                         .format(sel_x, sel_y))
                                
                                if step.featureSelected() > 1:
                                    continue
                                if not step.featureSelected():
                                    continue
                                
                                find_feat_out = layer_cmd.featSelOut(units="mm")["lines"]
                                find_feat_out += layer_cmd.featSelOut(units="mm")["arcs"]
                                all_len = sum([obj.len for obj in find_feat_out])
                                # step.PAUSE(str([key, all_len]))
                                if all_len < tmp_length:
                                    tmp_length = all_len
                                    step.removeLayer(tmp_layer)
                                    step.copySel(tmp_layer)
                                    
                            if step.isLayer(tmp_layer):
                                step.clearAll()
                                step.affect(tmp_layer)
                                step.copySel("find_connection_line")
                                step.removeLayer(tmp_layer)
                        
                        #继续计算连接位的外围范围
                        if step.isLayer("find_connection_line"):
                            step.removeLayer("find_connection_outer_line")
                            step.removeLayer("find_connection_line_new")
                            step.copyLayer(job.name, step.name, "find_connection_line", "find_connection_line_bak")
                            
                            #获取连接位跟单元边接触的直线
                            step.removeLayer("set_connection_tmp")
                            step.createLayer("set_connection_tmp")
                            f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
                            step.reset_fill_params()
                            step.clearAll()
                            step.affect("set_connection_tmp")
                            step.addRectangle(f_xmin, f_ymin, f_xmax, f_ymax)
                            step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                                     "area_type=rectangle,inout=inside,contour_cut=yes,margin={2},"
                                     "ref_layer={1},feat_types=line\;pad\;surface\;arc\;text".format(
                                         "set_connection_tmp",
                                         "ww_flt", 0
                                     ))                                
                            step.COM("sel_decompose,overlap=yes")
                            step.refSelectFilter("find_connection_line_bak", mode="disjoint")
                            if step.featureSelected():
                                step.selectDelete()
                            
                            step.COM("sel_resize,size=520,corner_ctl=no")
                            step.copyLayer(job.name, step.name, "set_fill_surface_bak", "set_fill_surface")
                            step.clearAll()
                            step.affect("set_fill_surface")
                            step.COM("sel_surf2outline,width=1")
                            step.resetFilter()
                            step.refSelectFilter("set_connection_tmp")
                            if step.featureSelected():
                                step.removeLayer("find_connection_touch_pcs_line")
                                step.copySel("find_connection_touch_pcs_line")
                                #if "-lyh" in job.name:
                                    #step.PAUSE("dd")                                
                                step.clearAll()
                                step.resetFilter()
                                step.affect("find_connection_touch_pcs_line")                                
                                step.changeSymbol("r254")
                                step.filter_set(feat_types='line')
                                step.selectAll()
                                if step.featureSelected():
                                    step.changeSymbol("s254")
                                step.contourize()
                                #if "-lyh" in job.name:
                                    #step.PAUSE("22")                                  
                            
                            max_run_times = 0
                            first_rout_touch_times = 0
                            first_rout_touch_width = 0# 设置第1次接触到锣区最外围
                            mode = "new"#mode="old"                            
                            for i in range(1, 1000):
                                step.clearAll()
                                step.affect("find_connection_line")
                                step.changeSymbol("r127")
                                step.resetFilter()
                                step.selectAll()
                                if not step.featureSelected():
                                    max_run_times = i
                                    break
                                step.COM("sel_extend_slots,mode=ext_by,size=300,from=center")
                                if mode == "new":
                                    step.copyLayer(job.name, step.name, "find_connection_touch_pcs_line", "set_fill_surface")
                                else:
                                    step.copyLayer(job.name, step.name, "set_fill_surface_bak", "set_fill_surface")
                                step.clearAll()
                                step.affect("set_fill_surface")
                                if mode == "new":
                                    step.COM("sel_resize,size={0},corner_ctl=no".format(800+i*100-254))
                                else:
                                    step.COM("sel_resize,size={0},corner_ctl=no".format(800+i*100))
                                step.COM("sel_surf2outline,width=1")
                                step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                                         "area_type=rectangle,inout=inside,contour_cut=no,margin={2},"
                                         "ref_layer={1},feat_types=line\;pad\;surface\;arc\;text".format(
                                             "set_fill_surface",
                                             "ww_flt", 0
                                         ))
                                step.refSelectFilter("find_connection_line", mode="cover")                               
                                if step.featureSelected():
                                    step.removeLayer("find_connection_line_new")
                                    step.copySel("find_connection_line_new")
                                    
                                    step.clearAll()
                                    step.affect("find_connection_line")
                                    step.resetFilter()
                                    step.refSelectFilter("find_connection_line_new", mode="disjoint")
                                    if step.featureSelected():
                                        # 没有接触到的线 为连接位的边缘
                                        #if "-lyh" in job.name:
                                            #step.PAUSE("check")
                                        step.moveSel("find_connection_outer_line")
                                        
                                        if not first_rout_touch_width:                                            
                                            first_rout_touch_width = (800+i*100) * 0.5
                                            first_rout_touch_times = i
                                            
                                    #if first_rout_touch_width:
                                        #if "-lyh" in job.name:
                                            #step.PAUSE(str([(800+i*100) * 0.5, i]))
                                            
                                    step.copyLayer(job.name, step.name, "find_connection_line_new", "find_connection_line")
                                    
                                else:
                                    step.clearAll()
                                    step.affect("find_connection_line")                                    
                                    step.moveSel("find_connection_outer_line")
                        
                            if step.isLayer("find_connection_outer_line"):
                                layer_cmd = gClasses.Layer(step, "find_connection_outer_line")
                                feat_out = layer_cmd.featOut(units="mm")["lines"]
                                all_len = [obj.len for obj in feat_out]                                                               
                                
                                step.clearAll()
                                step.affect("ww_flt")                                    
                                step.resetFilter()
                                step.refSelectFilter("find_connection_outer_line")
                                if step.featureSelected():
                                    step.COM("sel_extend_slots,mode=ext_by,size={0},from=center".format(
                                        max(all_len) *2000+10
                                    ))
                                    
                                step.resetFilter()
                                step.refSelectFilter("find_connection_outer_line")
                                if step.featureSelected():
                                    step.addAttr(".area", valType='', change_attr="yes")
                                
                                step.resetFilter()
                                step.setAttrFilter(".area")
                                step.refSelectFilter("find_connection_line_bak")
                                if step.featureSelected():
                                    step.COM("sel_extend_slots,mode=ext_by,size=-{0},from=center".format(
                                        max(all_len) *2000+10
                                    ))
                                    
                                step.resetFilter()
                                
                                #找出最外围链接位的线 没有被ww的线接触的 有弧接 导致不能切出连接位183*845e1  
                                # if step.isLayer("ww_flt_0_90_line"):                                    
                                step.clearAll()
                                step.affect("find_connection_outer_line")
                                step.resetFilter()
                                step.refSelectFilter("ww_flt", mode="disjoint", f_types="line")
                                if step.featureSelected():
                                    step.removeLayer("find_connection_outer_not_touch_ww_strech_line")
                                    step.copySel("find_connection_outer_not_touch_ww_strech_line")
                                    step.clearAll()
                                    step.affect("find_connection_outer_not_touch_ww_strech_line")
                                    step.COM("sel_extend_slots,mode=ext_by,size={0},from=center".format(
                                        max(all_len) *1000 +10
                                    ))                                        
                                
                                step.removeLayer("set_connection_surface")
                                step.createLayer("set_connection_surface")
                                f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
                                step.reset_fill_params()
                                step.clearAll()
                                step.affect("set_connection_surface")
                                step.addRectangle(f_xmin, f_ymin, f_xmax, f_ymax)
                                step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                                         "area_type=rectangle,inout=inside,contour_cut=yes,margin={2},"
                                         "ref_layer={1},feat_types=line\;pad\;surface\;arc\;text".format(
                                             "set_connection_surface",
                                             "ww_flt", 0
                                         ))
                                if step.isLayer("find_connection_outer_not_touch_ww_strech_line"):
                                    step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                                             "area_type=rectangle,inout=inside,contour_cut=yes,margin={2},"
                                             "ref_layer={1},feat_types=line\;pad\;surface\;arc\;text".format(
                                                 "set_connection_surface",
                                                 "find_connection_outer_not_touch_ww_strech_line", 0
                                             ))
                                    
                                step.COM("sel_decompose,overlap=yes")                                 
                                
                                step.refSelectFilter("find_connection_line_bak", mode="disjoint")
                                if step.featureSelected():
                                    # step.selectDelete()
                                    step.removeLayer("find_rout_copper_area")
                                    step.moveSel("find_rout_copper_area")
                                
                                #继续获取连接位置中间的位置 为后续判断用
                                step.removeLayer("find_connection_contain_center_area")
                                step.copyToLayer("find_connection_contain_center_area", size=-200)
                                #for i in range(1, first_rout_touch_times):
                                    #step.copyLayer(job.name, step.name, "find_connection_touch_pcs_line", "set_fill_surface")
                                    #step.clearAll()
                                    #step.affect("set_fill_surface")
                                    #step.COM("sel_resize,size={0},corner_ctl=no".format(254+i*100))
                                    #step.COM("sel_surf2outline,width=1")
                                    #step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                                             #"area_type=rectangle,inout=inside,contour_cut=no,margin={2},"
                                             #"ref_layer={1},feat_types=line\;pad\;surface\;arc\;text".format(
                                                 #"set_fill_surface",
                                                 #"ww_flt", 50
                                             #))
                                    #step.refSelectFilter("set_connection_surface", mode="cover")
                                    #if step.featureSelected():
                                        #step.copySel("find_connection_contain_all_line")
                                    #else:
                                        #break                                     
                                    
                                step.resetFilter()
                                step.selectAll()
                                layer_cmd = gClasses.Layer(step, "set_connection_surface")
                                indexes = layer_cmd.featSelIndex()
                                #for sel_index in indexes:
                                    #step.selectNone()
                                    #step.selectFeatureIndex("set_connection_surface", sel_index)
                                    #if step.featureSelected():
                                        #step.addAttr(".string", attrVal=sel_index, valType='text', change_attr="yes")
                                        #step.selectNone()
                                        #step.setAttrFilter(".string,text={0}".format(sel_index))
                                        
                                if mode == "old":                                    
                                    step.clearAll()
                                    step.affect("find_connection_line_bak")
                                    step.copySel("set_connection_surface")
                                    
                                    step.clearAll()
                                    step.resetFilter()
                                    step.affect("set_connection_surface")
                                    for sel_index in indexes:
                                        step.selectNone()
                                        step.selectFeatureIndex("set_connection_surface", sel_index)
                                        if step.featureSelected():
                                            step.COM("sel_ref_feat,layers=,use=select,mode=touch,\
                                            pads_as=shape,f_types=line\;pad\;surface\;arc\;text,\
                                            polarity=positive\;negative,include_syms=,exclude_syms=")
                                            if step.featureSelected() > 4:
                                                step.selectNone()
                                                step.selectFeatureIndex("set_connection_surface", sel_index)
                                                step.moveSel("set_connection_surface_clip")
                                
                                if step.isLayer("set_connection_surface_clip"):
                                    step.clearAll()
                                    step.copyLayer(job.name, step.name,
                                                   "set_connection_surface_clip",
                                                   "set_connection_surface_clip_bak")
                                    step.affect("set_connection_surface_clip")
                                    step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                                             "area_type=rectangle,inout=inside,contour_cut=no,margin={2},"
                                             "ref_layer={1},feat_types=line\;pad\;surface\;arc\;text".format(
                                                 "set_connection_surface_clip",
                                                 "set_fill_surface_bak", first_rout_touch_width
                                             ))
                                    
                                    step.COM("sel_decompose,overlap=yes")
                                    step.COM("sel_resize,size=-100,corner_ctl=no")
                                    step.refSelectFilter("set_connection_surface")
                                    if step.featureSelected():
                                        step.selectDelete()
                                        
                                    step.clearAll()
                                    step.affect("set_connection_surface_clip_bak")
                                    step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                                             "area_type=rectangle,inout=inside,contour_cut=no,margin={2},"
                                             "ref_layer={1},feat_types=line\;pad\;surface\;arc\;text".format(
                                                 "set_connection_surface_clip_bak",
                                                 "set_connection_surface_clip", 5
                                             ))
                                    #if "-lyh" in job.name:
                                        #step.PAUSE("ddd")
                                    step.refSelectFilter("find_connection_line_bak")
                                    if step.featureSelected():                                        
                                        step.copySel("set_connection_surface")
                                        
                                # 继续计算获取要检测开窗是否满足锣区1mil的间距要求
                                # step.flatten_layer("ww", "ww_flt")
                                step.removeLayer("check_mask_open_1mil")
                                step.clearAll()
                                step.affect("set_connection_surface")
                                step.resetFilter()
                                step.filter_set(feat_types='line;arc')
                                step.selectAll()
                                if step.featureSelected():
                                    step.selectDelete()
                                    
                                step.copyToLayer("check_mask_open_1mil")
                                step.clearAll()
                                step.affect("ww_flt")
                                step.resetFilter()
                                step.filter_set(feat_types='line')
                                step.setAttrFilter(".area")
                                step.selectAll()
                                if step.featureSelected():
                                    step.removeLayer("find_connection_outer_ww_line")
                                    step.copySel("find_connection_outer_ww_line")
                                    step.clearAll()
                                    step.affect("find_connection_outer_ww_line")
                                    step.COM("sel_resize,size=10")
                                    step.refSelectFilter("find_connection_line_bak")
                                    if step.featureSelected():
                                        step.selectDelete()
                                    
                                    #清除尖角位置的线
                                    if step.isLayer("find_connection_contain_center_area"):
                                        step.COM("sel_extend_slots,mode=ext_by,size={0},from=center".format(
                                            max(all_len) *1000 +10
                                        ))
                                        step.refSelectFilter("find_connection_contain_center_area")
                                        if step.featureSelected():
                                            step.selectDelete()
                                            
                                        step.COM("sel_extend_slots,mode=ext_by,size=-{0},from=center".format(
                                            max(all_len) *1000 +10
                                        ))                                            
                                    
                                    step.clearAll()
                                    step.affect("find_connection_line_bak")
                                    step.resetFilter()
                                    step.filter_set(feat_types='arc')
                                    step.selectAll()
                                    if step.featureSelected():
                                        step.copySel("find_connection_outer_ww_line")
                                        
                                    step.clearAll()
                                    step.affect("find_connection_outer_ww_line")
                                    step.changeSymbol("r1")                                        

                                step.clearAll()
                                step.affect("check_mask_open_1mil")
                                step.COM("sel_resize,size=600,corner_ctl=no")
                                #step.COM("sel_extend_slots,mode=ext_by,size={0},from=center".format(
                                    #2000
                                #))                                    
                                step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                                         "area_type=rectangle,inout=inside,contour_cut=no,margin={2},"
                                         "ref_layer={1},feat_types=line\;pad\;surface\;arc\;text".format(
                                             "check_mask_open_1mil",
                                             "find_rout_copper_area", -25.4
                                         ))                              
                                step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                                         "area_type=rectangle,inout=inside,contour_cut=no,margin={2},"
                                         "ref_layer={1},feat_types=line\;pad\;surface\;arc\;text".format(
                                             "check_mask_open_1mil",
                                             "set_fill_surface_bak", 10
                                         ))                                  
                                if step.isLayer("find_connection_outer_ww_line"):
                                    step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                                             "area_type=rectangle,inout=inside,contour_cut=no,margin={2},"
                                             "ref_layer={1},feat_types=line\;pad\;surface\;arc\;text".format(
                                                 "check_mask_open_1mil",
                                                 "find_connection_outer_ww_line", 10
                                             ))
                                if step.isLayer("set_connection_surface_clip"):
                                    step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                                             "area_type=rectangle,inout=inside,contour_cut=no,margin={2},"
                                             "ref_layer={1},feat_types=line\;pad\;surface\;arc\;text".format(
                                                 "check_mask_open_1mil",
                                                 "set_connection_surface_clip", 0
                                             ))
                                    
                                if step.isLayer("find_connection_outer_not_touch_ww_strech_line"):
                                    step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                                             "area_type=rectangle,inout=inside,contour_cut=no,margin={2},"
                                             "ref_layer={1},feat_types=line\;pad\;surface\;arc\;text".format(
                                                 "check_mask_open_1mil",
                                                 "find_connection_outer_not_touch_ww_strech_line", 0
                                             ))                                    
                                
                                #if "-lyh" in job.name:
                                    #step.PAUSE("dd")
                                step.COM("sel_decompose,overlap=yes")
                                step.COM("sel_resize,size=-400,corner_ctl=no")
                                step.COM("sel_resize,size=400,corner_ctl=no")                                     
                                step.resetFilter()
                                step.refSelectFilter("set_connection_surface", mode='disjoint')
                                if step.featureSelected():
                                    step.selectDelete()
                                    
                                #step.clearAll()
                                #step.affect("set_connection_surface")
                                #step.copyToLayer("set_connection_surface_500um", size=508)
                                if "auto_check" in args:
                                    step.clearAll()
                                    step.affect("find_rout_copper_area")
                                    step.refSelectFilter("find_connection_outer_line", mode="disjoint")
                                    if step.featureSelected():
                                        step.selectDelete()
                                    step.COM("sel_resize,size=254")                                
                                    
                                for mask_layer in ["m1", "m2"]:
                                    # 制作时不做检测
                                    if "auto_check" not in args:
                                        continue
                                    if step.isLayer(mask_layer):
                                        step.copyLayer(job.name, step.name, mask_layer, mask_layer+"_tmp")
                                        step.clearAll()
                                        step.affect(mask_layer+"_tmp")
                                        #去掉孔的开窗
                                        step.resetFilter()
                                        for drill_layer in ["drl", "cdc", "cds"]:
                                            if step.isLayer(drill_layer):                                                
                                                step.COM("sel_ref_feat,layers={0},use=filter,mode=same_center,"
                                                         "f_types=line;pad;surface;arc;text,polarity=positive;negative,"
                                                         "include_syms=,exclude_syms=,on_multiple=smallest".format(drill_layer))
                                                if step.featureSelected():
                                                    step.selectDelete()                                                    
                                                    
                                        if mask_layer == "m1":
                                            sig_layer = "l1"
                                        else:
                                            sig_layer = "l{0}".format(lay_num)
                                            
                                        #step.COM("sel_ref_feat,layers={0},use=filter,mode=same_center,"
                                                 #"f_types=pad,polarity=positive;negative,"
                                                 #"include_syms=,exclude_syms=,on_multiple=smallest".format(sig_layer))
                                        #if step.featureSelected():
                                            #step.selectDelete()                                                      
                                        
                                        step.contourize()
                                        step.resetFilter()
                                        step.refSelectFilter("set_connection_surface", mode="disjoint")
                                        if step.featureSelected():
                                            step.selectDelete()
                                                                                  
                                        #step.refSelectFilter("set_connection_surface_500um", mode="include")
                                        #step.COM("sel_reverse")
                                        #if step.featureSelected():
                                            #step.selectDelete()
                                        
                                        #相切的情况会有误报 这里减一个5um
                                        step.COM("sel_resize,size=-5")
                                        step.refSelectFilter("set_fill_surface_bak")
                                        if step.featureSelected():
                                            log = u"检测到{0} 内有连接位开窗进板内，请检查标记位置是否异常!".format(mask_layer)                                          
                                            arraylist_log.append(log)                                        
                                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, mask_layer+"_tmp",
                                                                                                 ["ww", "check_mask_open_1mil"], log.format(mask_layer),
                                                                                                 add_note_layer=mask_layer,
                                                                                                 dic_zu_layer=dic_zu_layer)
                                        step.COM("sel_resize,size=5")
                                            
                                        step.clearAll()
                                        step.affect("set_connection_surface")
                                        step.COM("sel_cont2pad,match_tol=25.4,restriction=,min_size=127,max_size=2540000,suffix=+++")
                                        step.resetFilter()
                                        step.refSelectFilter(mask_layer+"_tmp", mode="cover")
                                        if step.featureSelected():
                                            step.removeLayer("set_connection_surface_cover")                                            
                                            step.copySel("set_connection_surface_cover")
                                            
                                        step.affect("set_connection_surface")
                                        step.resetFilter()
                                        step.refSelectFilter(mask_layer+"_tmp", mode="cover")
                                        step.COM("sel_reverse")
                                        if step.featureSelected():
                                            log = u"检测到{0} 内有连接位 未全部开窗，请检查标记位置是否异常!".format(mask_layer)                                          
                                            arraylist_log.append(log)                                        
                                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "set_connection_surface",
                                                                                                 ["ww", "check_mask_open_1mil"], log.format(mask_layer),
                                                                                                 add_note_layer=mask_layer,
                                                                                                 dic_zu_layer=dic_zu_layer)
                                            
                                            step.removeLayer("set_connection_surface_no_cover")                                            
                                            step.copySel("set_connection_surface_no_cover")
                                            
                                        if step.isLayer("find_rout_copper_area"):                                            
                                            step.clearAll()
                                            step.affect(mask_layer+"_tmp")                                            
                                            step.refSelectFilter("find_rout_copper_area")
                                            if step.featureSelected():
                                                step.removeLayer("find_connection_outer_touch")
                                                step.copySel("find_connection_outer_touch")
                                                step.clearAll()
                                                step.affect("find_connection_outer_touch")
                                                step.refSelectFilter("set_connection_surface_cover")
                                                if step.featureSelected():
                                                    
                                                    log = u"检测到{0} 内有连接位开窗超出锣区最外围位置，请检查标记位置是否异常!".format(mask_layer)                                          
                                                    arraylist_log.append(log)                                        
                                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "find_connection_outer_touch",
                                                                                                         ["ww", "check_mask_open_1mil"], log.format(mask_layer),
                                                                                                         add_note_layer=mask_layer,
                                                                                                         dic_zu_layer=dic_zu_layer)                                                
                                            
                                        step.clearAll()
                                        step.affect("check_mask_open_1mil")
                                        step.refSelectFilter(mask_layer+"_tmp", mode="cover")
                                        step.COM("sel_reverse")
                                        if step.featureSelected():
                                            step.removeLayer("check_mask_open_line_tmp")
                                            step.copySel("check_mask_open_line_tmp")
                                            step.clearAll()
                                            step.affect("check_mask_open_line_tmp")
                                            if step.isLayer("set_connection_surface_cover"):
                                                
                                                step.refSelectFilter("set_connection_surface_cover")
                                                if step.featureSelected():
                                                    log = u"检测到{0} 内有连接位开窗区域未延伸到锣区1mil范围外，请检查标记位置是否异常!".format(mask_layer)                                          
                                                    arraylist_log.append(log)                                        
                                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "check_mask_open_line_tmp",
                                                                                                         ["ww", "check_mask_open_1mil"], log.format(mask_layer),
                                                                                                         add_note_layer=mask_layer,
                                                                                                         dic_zu_layer=dic_zu_layer)
                                                    
                                        if step.isLayer("set_connection_surface_cover") and step.isLayer(sig_layer):
                                            step.clearAll()
                                            step.affect("set_connection_surface_cover")
                                            step.resetFilter()
                                            step.refSelectFilter(sig_layer)
                                            if step.featureSelected():
                                                log = u"检测到{0} 内有连接位开窗 在线路上有铺铜，请检查标记位置是否异常!".format(mask_layer)                                          
                                                arraylist_log.append(log)                                        
                                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "set_connection_surface_cover",
                                                                                                     ["ww", "check_mask_open_1mil", mask_layer], log.format(mask_layer),
                                                                                                     add_note_layer=sig_layer,
                                                                                                     dic_zu_layer=dic_zu_layer)                                            
                            else:                                
                                if step.isLayer("find_connection_line"):
                                    for mask_layer in ["m1", "m2"]:
                                        # 制作时不做检测
                                        if "auto_check" in args:
                                            continue                                        
                                        if step.isLayer(mask_layer):
                                            step.copyLayer(job.name, step.name, mask_layer, mask_layer+"_tmp")
                                            step.clearAll()
                                            step.affect(mask_layer+"_tmp")
                                            step.contourize()
                                            
                                            step.clearAll()
                                            step.affect("find_connection_line")
                                            step.resetFilter()
                                            step.refSelectFilter(mask_layer+"_tmp", mode='cover')
                                            step.COM("sel_reverse")
                                            if step.featureSelected():
                                                log = u"检测到{0} 内有连接位 未全部开窗，请检查标记位置是否异常!".format(mask_layer)                                          
                                                arraylist_log.append(log)                                        
                                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "find_connection_line",
                                                                                                     "ww", log.format(mask_layer),
                                                                                                     add_note_layer=mask_layer,
                                                                                                     dic_zu_layer=dic_zu_layer)
                                            step.removeLayer(mask_layer+"_tmp")
                                
                        # if "-lyh" not in job.name:
                        for layer in job.matrix.getInfo()["gROWname"]:
                            if "find_connection" in layer or "set_connection" in layer:
                                step.removeLayer(layer)
                        for mask_layer in ["m1", "m2"]:
                            step.removeLayer(mask_layer+"_tmp")
                            
                        step.removeLayer("find_connection_line")
                        step.removeLayer("find_connection")
                        step.removeLayer("find_connection_tmp")
                        step.removeLayer("set_fill_surface")
                        step.removeLayer("ww_flt")
                        step.removeLayer("ww_flt_0_90_line")
                        step.removeLayer("check_mask_open_line_tmp")
                        step.removeLayer("set_connection_surface_no_cover")
                        step.removeLayer("set_connection_surface_cover")
                        step.removeLayer("find_rout_copper_area")
                        if "get_tab_slot_area_layer" not in args:
                            step.removeLayer("set_fill_surface_bak")                        
                            
                        if "auto_make_connection" in args:
                            step.copyLayer(job.name, step.name, "check_mask_open_1mil", "set_connect_mask_open")
                            step.clearAll()
                            step.removeLayer("check_mask_open_1mil")
                            step.display("set_connect_mask_open")
                            step.resetAttr()
                            step.addAttr(".string", attrVal='connect_mask_open', valType='text', change_attr="yes")
                            
                            step.display_layer("ww", num=2)
                            showMessageInfo(u"连接位开窗已制作完成，请对比ww检查set_connect_mask_open层是否异常！")
                            
                        if "get_tab_slot_area_layer" in args:
                            step.flatten_layer("ww", "ww_flt")
                            step.removeLayer("tab_area")
                            step.removeLayer("slot_area")
                            step.createLayer("tab_area")
                            #f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
                            #step.reset_fill_params()
                            step.clearAll()
                            step.affect("check_mask_open_1mil")
                            # step.COM("sel_resize,size=-508,corner_ctl=no")
                            
                            step.clearAll()
                            step.copyLayer(job.name, step.name,
                                           "set_fill_surface_bak",
                                           "slot_line")
                            step.affect("slot_line")
                            step.COM("sel_resize,size=800,corner_ctl=no")
                            step.COM("sel_surf2outline,width=1")
                            step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                                     "area_type=rectangle,inout=inside,contour_cut=no,margin={2},"
                                     "ref_layer={1},feat_types=line\;pad\;surface\;arc\;text".format(
                                         "slot_line",
                                         "ww_flt", 0
                                     ))
                            step.refSelectFilter("check_mask_open_1mil", mode="cover")
                            if step.featureSelected():
                                step.moveSel("set_connection_line")
                            
                            step.clearAll()
                            step.affect("tab_area")
                            step.reset_fill_params()
                            names = list(set(get_panelset_sr_step(job.name, step.name)))
                            step.COM("""sr_fill,type=solid,solid_type=surface,min_brush=25.4,
                            use_arcs=yes,cut_prims=no,outline_draw=no,outline_width=0,
                            outline_invert=no,polarity=positive,step_margin_x=0,
                            step_margin_y=0,step_max_dist_x=2540,step_max_dist_y=2540,
                            sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,
                            nest_sr=yes,consider_feat=no,feat_margin=0,consider_drill=no,
                            drill_margin=0,consider_rout=no,dest=affected_layers,
                            layer=.affected,stop_at_steps={0}""".format(";".join(names)))
                            
                            #step.clearAll()
                            #step.affect("ww_flt")
                            #step.copyToLayer("tab_area", invert="yes")
                            #step.clearAll()
                            #step.affect(lay)
                            # step.addRectangle(f_xmin, f_ymin, f_xmax, f_ymax)
                            step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                                     "area_type=rectangle,inout=inside,contour_cut=yes,margin={2},"
                                     "ref_layer={1},feat_types=line\;pad\;surface\;arc\;text,"
                                     "break_to_islands=yes".format(
                                         "tab_area",
                                         "ww_flt", 0
                                     ))                                
                            # step.COM("sel_decompose,overlap=no")
                            
                            step.refSelectFilter("slot_line", mode="touch")
                            if step.featureSelected():
                                step.moveSel("slot_area")
                            
                            step.refSelectFilter("check_mask_open_1mil", mode="cover")
                            if step.featureSelected():
                                step.selectDelete()
                            
                            step.COM("sel_resize,size=600,corner_ctl=no")
                            step.refSelectFilter("check_mask_open_1mil", mode="disjoint")
                            if step.featureSelected():
                                step.moveSel("slot_area")                            
                            step.COM("sel_resize,size=-600,corner_ctl=no")
                            
                            step.copyLayer(job.name, step.name, "check_mask_open_1mil", "set_connect_area")
                            step.clearAll()
                            step.removeLayer("check_mask_open_1mil")
                            step.removeLayer("slot_line")
                            step.removeLayer("set_fill_surface_bak")
                            step.removeLayer("ww_flt")
                            step.removeLayer("set_connection_line")
                                    
                    else:
                        return u"ww层内未找到连接位的位置线，请检查ww层是否异常！！", None
                else:
                    u"ww层不存在，请先制作ww层！！", None
        else:
            return u"set不存在,请检查！", None
        
        if arraylist_log:
            return arraylist_log, dic_zu_layer
    
        return "success", None
    
    def check_silk_process_show_warning(self):
        """工单流程设计有文字印刷站，在外层自动检测中增加一条指示并且报红，
        人员确认后才报OK ，所有网印白油块工作稿在成品基础上整体缩小0.1mm制作
        http://192.168.2.120:82/zentao/story-view-6095.html
        20240220 规范要求改成0.05mm"""
        data_info = get_inplan_all_flow(job.name, select_dic=True)
        silk_process = [dic_info for dic_info in data_info
                        if u"文字印刷" in dic_info["PROCESS_DESCRIPTION"].decode("utf8")]
        if silk_process:
            log = u"检测到工单流程设计有文字印刷站，所有网印白油块工作稿在成品基础上整体缩小0.05mm制作,请确认是否已处理！"
            res = showQuestionMessageInfo(log, start_btn_text=u"已处理OK", end_btn_text=u"未处理")
            if not res:
                return u"未处理(" + log + ")", None
            
            return u"success已处理OK(" +log + ")",None 
        
        return "success", None
    
    def check_silk_distance_mask_info(self):
        """检测白油块距防焊开窗、距喷墨文字间距是否≥0.254mm。此要求容易忘记，
        造成品质问题。外层新增自动检测网印白油块到第一次文字间距及阻焊开窗是否有10mil
        http://192.168.2.120:82/zentao/story-view-6245.html 20231128 by lyh"""
        data_info = get_inplan_all_flow(job.name, select_dic=True)
        silk_process = [dic_info for dic_info in data_info
                        if u"文字印刷" in dic_info["PROCESS_DESCRIPTION"].decode("utf8")]
        if silk_process:
            arraylist_log = []
            dic_zu_layer = {}
            all_layers = matrixinfo["gROWname"]
            for info in silk_process:
                if info["WORK_DESCRIPTION"] and u"174|使用曝光资料" in info["WORK_DESCRIPTION"].decode("utf8"):
                    if info["VALUE_AS_STRING"] is not None:                        
                        check_layers = [x.lower() for x in info["VALUE_AS_STRING"].split(",") if x.lower() in silkscreenLayers]
                        if not check_layers:
                            log = u"检测到有 文字印刷 流程，但inplan的工具{0} 未发现在tgz资料内，请检查工具是否异常!".format(info["VALUE_AS_STRING"])
                            arraylist_log.append(log)
                            continue
                        top_sig_index = all_layers.index("l1")
                        for worklayer in check_layers:
                            index1 = all_layers.index(worklayer)
                            find_silk_layer = []
                            find_mask_layer = []
                            for contact_silk_layer in silkscreenLayers:
                                if contact_silk_layer in check_layers:
                                    continue
                                index2 = all_layers.index(contact_silk_layer)
                                if index1 < top_sig_index and index2 < top_sig_index:
                                    find_silk_layer.append(contact_silk_layer)
                                    
                            for contact_mask_layer in solderMaskLayers:
                                # 伍青 通知第二次加大的阻焊资料不用分析到字符的间距 
                                if "-2" in contact_mask_layer:
                                    continue
                                index2 = all_layers.index(contact_mask_layer)
                                if index1 < top_sig_index and index2 < top_sig_index:
                                    find_mask_layer.append(contact_mask_layer)
                                            
                            for stepname in matrixinfo["gCOLstep_name"]:
                                if "edit" in stepname:
                                    step = gClasses.Step(job, stepname)
                                    step.open()
                                    step.COM("units,type=mm")
                                    step.clearAll()
                                    step.copyLayer(job.name, stepname, worklayer, worklayer+"_tmp")
                                    step.affect(worklayer+"_tmp")
                                    step.COM("sel_resize,size=508")
                                    if find_silk_layer:
                                        
                                        step.refSelectFilter(";".join(find_silk_layer))
                                        if step.featureSelected():
                                            log = u"检测到{2} 内网印字符{0} 距喷墨字符{1}间距不够10mil ，请检查是否异常!".format(worklayer, ";".join(find_silk_layer), stepname)
                                            if log not in arraylist_log:                                            
                                                arraylist_log.append(log)
                                                
                                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, worklayer+"_tmp",
                                                                                                     [worklayer]+find_silk_layer, log,
                                                                                                 add_note_layer=worklayer, dic_zu_layer=dic_zu_layer)                                            
                                        
                                    step.selectNone()
                                    if find_mask_layer:
                                        
                                        step.refSelectFilter(";".join(find_mask_layer))
                                        if step.featureSelected():
                                            log = u"检测到{2} 内网印字符{0} 距阻焊开窗{1}间距不够10mil ，请检查是否异常!".format(worklayer, ";".join(find_mask_layer), stepname)
                                            if log not in arraylist_log:                                            
                                                arraylist_log.append(log)
                                                
                                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, worklayer+"_tmp",
                                                                                                     [worklayer]+find_mask_layer, log,
                                                                                                     add_note_layer=worklayer, dic_zu_layer=dic_zu_layer)                                             
                                        
                            step.removeLayer(worklayer+"_tmp")
                            
            if arraylist_log:
                return arraylist_log, dic_zu_layer
            
        return "success", None                                
        
    def check_layer_info_show_warning(self):
        """增加外层自动检测里，料号中有以下层名（gold-c/gold-s、stg-c/sgt-s）自动提醒就报红
        检测选化资料文字大白油块有没做化金
        http://192.168.2.120:82/zentao/story-view-6178.html"""
        for layer in ["gold-c", "gold-s", "sgt-c", "sgt-s"]:            
            if layer in matrixinfo["gROWname"]:
                log = u"检测到【选化板及电金板】，请检查选化资料文字层大白油块，密集字符是否有做化金(流程设计在文字后)，请确认是否已处理！"
                #res = showQuestionMessageInfo(log, start_btn_text=u"已处理OK", end_btn_text=u"未处理")
                #if not res:
                    #return u"未处理(" + log + ")", None
                
                #return u"success已处理OK(" +log + ")",None
                return log, None
            
        return "success", None

    def check_all_process_exists_layer(self):
        """检测inplan流程对应的工具在资料内是否存在"""
        #1.0 检测镀孔流程 是否跑镀孔菲林程序
        mrp_info = get_inplan_mrp_info(job.name.upper(), "1=1")        
        inplan_all_flow_data = get_inplan_all_flow(job.name.upper(), True)        
        arraylist = []
        inner_outer = os.environ.get("INNER_OUTER", "inner")
        for info in mrp_info:
            mrp_name = info["MRPNAME"]
            has_dk_process = False
            for flow_info in inplan_all_flow_data:
                if flow_info["MRP_NAME"] == mrp_name:
                    if u"选镀图形" in flow_info["WORK_CENTER_CODE"].decode("utf8"):
                        has_dk_process = True
            
            if not has_dk_process:
                continue
            
            if inner_outer == "outer" and "-" in mrp_name:
                continue
            
            if inner_outer == "inner" and "-" not in mrp_name:
                continue            
                      
            FROMLAY = info["FROMLAY"].lower() + "-dk"
            TOLAY = info["TOLAY"].lower() + "-dk"
            for layer in [FROMLAY, TOLAY]:                
                if layer not in matrixinfo["gROWname"] :
                    arraylist.append(layer)
        
        if arraylist:
            if inner_outer == "outer":
                name = u"7.39外层镀孔菲林制作"
            else:
                name = u"6.24内层镀孔菲林制作"            
            log = u"检测{1}有镀孔流程，但镀孔菲林{0} 不存在，请检查[{2}]是否运行完整!".format(" ".join(arraylist), mrp_name, name)
            return log, None
        
        return "success", None
    
    def check_big_hole_add_yk(self):
        """http://192.168.2.120:82/zentao/story-view-6233.html
        检测大孔是否加引孔 20231128 by lyh"""
        if "panel" in matrixinfo["gCOLstep_name"]:
            dic_zu_layer = {}
            arraylist = []            
            all_steps = get_panelset_sr_step(job.name, "panel")
            for stepname in all_steps + ["panel"]:
                #if stepname in ["drl", "2nd"]:
                    #continue
                # if "edit" in stepname or "set" in stepname:
                if re.match("^edit|^set", stepname): 
                    step = gClasses.Step(job, stepname)
                    step.open()
                    step.COM("units,type=mm")
                    for worklayer in ["drl", "2nd"]:
                        if step.isLayer(worklayer):
                            step.clearAll()
                            step.affect(worklayer)
                            step.resetFilter()
                            layer_cmd = gClasses.Layer(step, worklayer)
                            feat_out = layer_cmd.featCurrent_LayerOut(units="mm")['pads']
                            feat_out += layer_cmd.featCurrent_LayerOut(units="mm")['lines']
                            big_hole_symbols = list(set([obj.symbol for obj in feat_out if float(obj.symbol[1:]) >= 3500]))
                            if big_hole_symbols:
                                step.selectNone()
                                step.selectSymbol(";".join(big_hole_symbols), 1, 1)
                                if step.featureSelected():
                                    step.removeLayer("big_hole_tmp")
                                    step.copySel("big_hole_tmp")
                                    step.clearAll()
                                    step.affect("big_hole_tmp")
                                    
                                    step.resetFilter()
                                    step.filter_set(polarity='positive', exclude_syms=";".join(big_hole_symbols))
                                    step.refSelectFilter(worklayer, polarity="positive")
                                    step.COM("sel_reverse")
                                    if step.featureSelected():                                    
                                        log= u"检测到{0} {1}层 有大于3.5mm孔未加引孔，请检查标记处是否异常！"
                                        arraylist.append(log.format(stepname, worklayer)) 
                                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "big_hole_tmp",
                                                                                             worklayer, log.format(stepname, worklayer),
                                                                                             add_note_layer=worklayer, dic_zu_layer=dic_zu_layer)
                                    step.removeLayer("big_hole_tmp")
                    
                    step.clearAll()
                
            if arraylist:
                return arraylist, dic_zu_layer
            
        return "success", None                                    
    
    def check_coupon_netpoint_pad_connetion(self, auto_check=None, show_ui=None, icg_name=None):
        """检测内层接地pad 是否跟大同皮相连 20230619 by lyh"""
        arraylist = []
        dic_zu_layer = {}          
        for name in matrixinfo["gCOLstep_name"]:
            if ("icg" in name and icg_name is None) or \
               (icg_name is not None and name == icg_name):
                stepname = name
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")
                          
                for worklayer in signalLayers:
                    step.copyLayer(job.name, stepname, worklayer, worklayer+"_tmp+++")
                    step.clearAll()
                    step.affect(worklayer+"_tmp+++")
                    # step.contourize()
                    
                    #step.clearAll()
                    #if step.isLayer("drl"):
                        #step.affect("drl")
                    #else:
                        #if step.isLayer("cdc"):
                            #step.affect("cdc")
                        #else:
                            #if step.isLayer("cds"):
                                #step.affect("cds")
                            #else:
                                #arraylist.append(u"{0}中未检测到drl 或cdc cds层".format(stepname))
                                #break
                            
                    step.resetFilter()
                    step.filter_set(feat_types='pad', polarity='positive', include_syms='s*')                    
                    step.COM("reset_filter_criteria,filter_name=ref_select,criteria=inc_attr")
                    step.refSelectFilter(worklayer, include_syms="r381")
                         
                    step.COM("reset_filter_criteria,filter_name=ref_select,criteria=inc_attr")
                    step.COM("set_filter_attributes,filter_name=ref_select,"
                             "exclude_attributes=no,condition=yes,attribute=.string,"
                             "min_int_val=0,max_int_val=0,min_float_val=0,"
                             "max_float_val=0,option=,text=jx_line")
                    step.refSelectFilter(worklayer)
                    # step.PAUSE(worklayer)
                    if step.featureSelected():
                        step.removeLayer("check_pad_point_tmp")
                        step.copySel("check_pad_point_tmp")                        
                        layer_cmd = gClasses.Layer(step, "check_pad_point_tmp")
                        featout = layer_cmd.featout_dic_Index(units="mm", options="feat_index")["pads"]
                        
                        step.clearAll()
                        step.affect(worklayer+"_tmp+++")
                        step.contourize()
                        
                        for obj in featout:
                            step.clearAll()
                            step.affect("check_pad_point_tmp")
                            step.resetFilter()
                            step.selectFeatureIndex("check_pad_point_tmp", obj.feat_index)
                            if step.featureSelected():
                                step.addAttr(".string", attrVal=str(obj.feat_index), valType='text', change_attr="yes")
                                
                                step.clearAll()
                                step.affect(worklayer)
                                step.resetFilter()
                                step.COM("reset_filter_criteria,filter_name=ref_select,criteria=inc_attr")
                                step.COM("set_filter_attributes,filter_name=ref_select,exclude_attributes=no,"
                                         "condition=yes,attribute=.string,min_int_val=0,max_int_val=0,"
                                         "min_float_val=0,max_float_val=0,option=,text={0}".format(obj.feat_index))
                                step.filter_set(feat_types='surface', polarity='positive')
                                step.refSelectFilter("check_pad_point_tmp")
                                x_min1, y_min1, x_max1, y_max1 = get_layer_selected_limits(step, worklayer)                                
                                
                                step.clearAll()
                                step.affect(worklayer+"_tmp+++")
                                step.COM("sel_net_feat,operation=select,x={0},y={1},tol=170.4725,use_ffilter=no".format(obj.x, obj.y))
                                x_min2, y_min2, x_max2, y_max2 = get_layer_selected_limits(step, worklayer+"_tmp+++")                                
                                #if auto_check is None and worklayer == "l5":
                                    #step.display_layer("check_pad_point_tmp", 2)
                                    #step.PAUSE(str([x_min1, y_min1, x_max1, y_max1, x_min2, y_min2, x_max2, y_max2]))
                                    
                                # if abs((x_max1 - x_min1) - (x_max2 - x_min2)) > 20 or \
                                if abs((y_max1 - y_min1) - (y_max2 - y_min2)) > 2:
                                    # step.PAUSE(str([x_min1, y_min1, x_max1, y_max1, x_min2, y_min2, x_max2, y_max2]))
                                    step.clearAll()
                                    step.affect("check_pad_point_tmp")
                                    step.resetFilter()
                                    step.selectFeatureIndex("check_pad_point_tmp", obj.feat_index)
                                    
                                    log = u"检测到阻抗条{0}层 标记处接地pad跟大铜皮异常断开，请务必到资料内打开标记检查！非常重要！！"
                                    arraylist.append(log.format(worklayer))
                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "check_pad_point_tmp",
                                                                                         worklayer, log.format(worklayer), dic_zu_layer,
                                                                                         add_note_layer=worklayer)
                                
                    step.removeLayer("check_pad_point_tmp")
                    step.removeLayer(worklayer+"_tmp+++")
                    step.clearAll()
                    
        if arraylist:
            if auto_check is None or show_ui == "yes":              
                showMessageInfo(*arraylist)
                self.view_note_detail(dic_zu_layer)

            else:
                return arraylist, dic_zu_layer
        
        return "success", None
    
    def check_imp_contact_inplan_is_right(self):
        """检测inplan阻抗条更新是否跟cam制作的数量一致
        http://192.168.2.120:82/zentao/story-view-6267.html"""
        arraylist_imp_info = get_inplan_imp(job.name.upper())
        array_imp_check_info = []
        for name in matrixinfo["gCOLstep_name"]:
            if "icg" in name:
                stepname = name
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")
                
                for worklayer in signalLayers:
                    step.clearAll()
                    step.affect(worklayer)
                    step.resetFilter()
                    step.filter_set(feat_types='text')
                    step.selectAll()
                    if step.featureSelected():
                        layer_cmd = gClasses.Layer(step, worklayer)
                        feat_out = layer_cmd.featSelOut(units="mm")["text"]
                        for obj in feat_out:
                            if "REF" in getattr(obj, "text", "") and "OHM" in getattr(obj, "text", ""):
                                array_imp_check_info.append(obj.text)
                
                step.clearAll()
                                
        arraylist = []
        # print(array_imp_check_info)
        if array_imp_check_info:
            
            for check_text in array_imp_check_info:
                for dic_imp_info in arraylist_imp_info:
                    ref_layer = dic_imp_info["REF_LAYER_"]
                    if ref_layer is None:
                        ref_layer = ""
                    trace_layer = dic_imp_info["TRACE_LAYER_"]
                    finish_lw = dic_imp_info["FINISH_LW_"]
                    finish_ls = dic_imp_info["FINISH_LS_"]
                    
                    origin_lw = dic_imp_info["ORG_WIDTH"]
                    origin_ls = dic_imp_info["ORG_SPC"]
                    
                    eq_lw = dic_imp_info["EQ_LW_"]
                    eq_ls = dic_imp_info["EQ_LS_"]                    
                    
                    cusimp = float(dic_imp_info["CUSIMP"])
                    if int(cusimp) == float(cusimp):
                        cusimp = str(int(cusimp))
                    else:
                        cusimp = str(cusimp)
                        
                    finish_lw_ls_text = ("%.2f" % finish_lw).rstrip("0").rstrip(".")
                    if finish_ls:
                        finish_lw_ls_text = "{0}/{1}".format(("%.2f" % finish_lw).rstrip("0").rstrip("."),
                                                             ("%.2f" % finish_ls).rstrip("0").rstrip("."))
                        
                    origin_lw_ls_text = ("%.2f" % origin_lw).rstrip("0").rstrip(".")
                    if origin_ls:
                        origin_lw_ls_text = "{0}/{1}".format(("%.2f" % origin_lw).rstrip("0").rstrip("."),
                                                             ("%.2f" % origin_ls).rstrip("0").rstrip("."))
                        
                    eq_lw_ls_text = ("%.2f" % eq_lw).rstrip("0").rstrip(".")
                    if eq_ls:
                        eq_lw_ls_text = "{0}/{1}".format(("%.2f" % eq_lw).rstrip("0").rstrip("."),
                                                             ("%.2f" % eq_ls).rstrip("0").rstrip("."))
                        
                    if trace_layer in check_text and\
                       ref_layer in check_text and\
                       (finish_lw_ls_text in check_text or \
                        origin_lw_ls_text in check_text or \
                        eq_lw_ls_text in check_text                        
                        ) and\
                       cusimp in check_text:
                        break
                else:
                    log = u"发现{0}存在icg阻抗条中，但inplan阻抗信息内未发现此条阻抗信息，请检查！"
                    arraylist.append(log.format(check_text.replace('"', "").replace("'", "")))
                    
            for dic_imp_info in arraylist_imp_info:
                ref_layer = dic_imp_info["REF_LAYER_"]
                if ref_layer is None:
                    ref_layer = ""
                trace_layer = dic_imp_info["TRACE_LAYER_"]
                finish_lw = dic_imp_info["FINISH_LW_"]
                finish_ls = dic_imp_info["FINISH_LS_"]
                origin_lw = dic_imp_info["ORG_WIDTH"]
                origin_ls = dic_imp_info["ORG_SPC"]                
                eq_lw = dic_imp_info["EQ_LW_"]
                eq_ls = dic_imp_info["EQ_LS_"]                 
                cusimp = float(dic_imp_info["CUSIMP"])
                if int(cusimp) == float(cusimp):
                    cusimp = str(int(cusimp))
                else:
                    cusimp = str(cusimp)
                    
                finish_lw_ls_text = ("%.2f" % finish_lw).rstrip("0").rstrip(".")
                if finish_ls:
                    finish_lw_ls_text = "{0}/{1}".format(("%.2f" % finish_lw).rstrip("0").rstrip("."),
                                                         ("%.2f" % finish_ls).rstrip("0").rstrip("."))
                    
                origin_lw_ls_text = ("%.2f" % origin_lw).rstrip("0").rstrip(".")
                if origin_ls:
                    origin_lw_ls_text = "{0}/{1}".format(("%.2f" % origin_lw).rstrip("0").rstrip("."),
                                                         ("%.2f" % origin_ls).rstrip("0").rstrip("."))
                    
                eq_lw_ls_text = ("%.2f" % eq_lw).rstrip("0").rstrip(".")
                if eq_ls:
                    eq_lw_ls_text = "{0}/{1}".format(("%.2f" % eq_lw).rstrip("0").rstrip("."),
                                                         ("%.2f" % eq_ls).rstrip("0").rstrip("."))
                    
                for check_text in array_imp_check_info:
                    if trace_layer in check_text and\
                       ref_layer in check_text and\
                       (finish_lw_ls_text in check_text or \
                        origin_lw_ls_text in check_text or \
                        eq_lw_ls_text in check_text                        
                        ) and\
                       cusimp in check_text:
                        break
                else:
                    log = u"发现{0} 参考{1}  {2}  {3} OHM存在inplan中，但icg阻抗条内未发现此条阻抗信息，请检查！"
                    arraylist.append(log.format(trace_layer, ref_layer, finish_lw_ls_text, cusimp))
                    
            
        
        if arraylist:
            # showMessageInfo(*arraylist)
            return arraylist, None
        
        return "success", None
    
    def check_hct_coupon_netlist_info(self):
        """检查hct coupon 是否导通
        http://192.168.2.120:82/zentao/story-view-5687.html"""
        if "panel" in matrixinfo["gCOLstep_name"]:
            all_steps = get_panelset_sr_step(job.name, "panel")
        else:
            all_steps = matrixinfo["gCOLstep_name"]
        all_hct_coupon = [name for name in all_steps if "hct" in name ]
        
        arraylist = []
        check_hct_steps = []
        for stepname in matrixinfo["gCOLstep_name"]:
            if "hct_coupon" in stepname or "hct-coupon" in stepname:                
                # stepname = "hct_coupon_new"
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")
                # worklayer = "l1"
                check_hct_steps.append(stepname)
                for worklayer in outsignalLayers:
                    if step.isLayer(worklayer):                
                        step.clearAll()
                        step.affect(worklayer)
                        step.resetFilter()
                        if "hct_coupon_new" in stepname:                        
                            step.selectSymbol("rect2200x4600;rect2600x2060", 1, 1)
                        else:
                            step.selectSymbol("s1524", 1, 1)
                        if step.featureSelected():
                            layer_cmd = gClasses.Layer(step, worklayer)
                            featout = layer_cmd.featSelOut(units="mm")["pads"]
                            pos_x = featout[0].x
                            pos_y = featout[0].y
                            step.display(worklayer)
                            step.selectNone()
                            step.COM("sel_board_net_feat,operation=select,x={0},y={1},tol=170.4725,use_ffilter=no".format(pos_x, pos_y))
                            if step.featureSelected():
                                featout = layer_cmd.featSelOut(units="mm")["pads"]
                                # symbols = [obj.symbol for obj in featout]
                                s1524_symbols = [obj.symbol for obj in featout if obj.symbol == "s1524"]
                                symbols_rect = [obj.symbol for obj in featout
                                                if obj.symbol not in ("rect2600x2060", "rect2200x4600")
                                                and "rect" in obj.symbol]
                                # print s1524_symbols
                                if ("hct_coupon_new" in stepname and not symbols_rect) or \
                                   ("hct-coupon" in stepname and len(s1524_symbols) < 2):
                                    log = u"检测到{0} step 网络不导通，请检查是否异常".format(stepname)
                                    arraylist.append(log)
                                    break
                                    # step.PAUSE(str(set(symbols)))
                        #else:
                            #log = u"检测到{0} 此模块未加入网络导通性检测，请反馈程序工程师加入".format(stepname)
                            #arraylist.append(log)                        
                    else:
                        log = u"{0}层不存在，请检查资料是否异常"
                        arraylist.append(log.format(worklayer))
                    
                step.clearAll()
        
        not_check_hct_steps = [name for name in all_hct_coupon if name not in check_hct_steps]
        if not_check_hct_steps:
            log = u"检测到以下 {0} ,hct没有检测逻辑，系统未进行网络导通性检测，请手动检测网络导通性！！！！"
            arraylist.append(log.format(not_check_hct_steps))            
            
        if arraylist:
            return arraylist, None
        
        return "success" , None
    
    def check_cdc_drl_hole_info(self):
        """检测资料中有控深钻时检测是否存在drl层，drl层是否仍有钻孔
        http://192.168.2.120:82/zentao/story-view-5686.html"""
        drl = "drl"
        arraylist = []
        dic_zu_layer = {}
        for drill_layer in ["cdc", "cds"]:
            if drill_layer in matrixinfo["gROWname"] and \
               drl in matrixinfo["gROWname"]:
                if "panel" in matrixinfo["gCOLstep_name"]:                    
                    all_steps = get_panelset_sr_step(jobname, "panel") + ["panel"]
                    for stepname in all_steps:
                        step = gClasses.Step(job, stepname)
                        step.open()
                        
                        step.clearAll()
                        step.affect(drl)
                        step.resetFilter()
                        step.refSelectFilter(drill_layer, mode="disjoint")
                        if step.featureSelected():
                            log = u"检测到{0} 中drl层的孔未全部合并到{1}层中，请检查标记处孔是否异常！".format(stepname, drill_layer)
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, drl,
                                                                                 drill_layer, log, dic_zu_layer,
                                                                                 add_note_layer=drl)                            
                        step.selectNone()
                        step.refSelectFilter(drill_layer, mode="touch")
                        if step.featureSelected():
                            step.removeLayer("touch_hole_tmp")
                            step.copySel("touch_hole_tmp")
                            step.clearAll()
                            step.affect("touch_hole_tmp")
                            step.COM("sel_ref_feat,layers={0},use=filter,mode=same_center,"
                                     "f_types=line;pad;surface;arc;text,polarity=positive;negative,"
                                     "include_syms=,exclude_syms=,on_multiple=smallest".format(drill_layer))
                            step.COM("sel_reverse")
                            # step.PAUSE("ddd")
                            if step.featureSelected():                                
                                log = u"检测到{0} 中drl层的孔与{1}层不在同一位置，请检查标记处孔是否异常！".format(stepname, drill_layer)
                                arraylist.append(log)                                
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "touch_hole_tmp",
                                                                                     drill_layer, log, dic_zu_layer,
                                                                                     add_note_layer=drl)
                                
                            step.COM("sel_ref_feat,layers={0},use=filter,mode=same_center,"
                                 "f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,"
                                 "include_syms=,exclude_syms=,on_multiple=smallest".format(drill_layer))
                            step.COM("sel_reverse")
                            if step.featureSelected():
                                step.selectDelete()
                            
                            step.refSelectFilter(drill_layer, mode="cover")
                            step.COM("sel_reverse")
                            if step.featureSelected():
                                step.removeLayer("hole_size_diff_tmp")
                                step.moveSel("hole_size_diff_tmp")
                            
                            step.clearAll()
                            step.affect(drill_layer)
                            step.COM("sel_ref_feat,layers={0},use=filter,mode=same_center,"
                                 "f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,"
                                 "include_syms=,exclude_syms=,on_multiple=smallest".format("touch_hole_tmp"))
                            if step.featureSelected():
                                step.removeLayer("touch_hole_tmp2")
                                step.copySel("touch_hole_tmp2")
                                step.clearAll()
                                step.affect("touch_hole_tmp2")
                                step.refSelectFilter("touch_hole_tmp", mode="cover")
                                step.COM("sel_reverse")
                                if step.featureSelected():
                                    step.moveSel("hole_size_diff_tmp")
                                
                            if step.isLayer("hole_size_diff_tmp"):
                                step.clearAll()
                                step.affect("hole_size_diff_tmp")
                                step.selectAll()
                                log = u"检测到{0} 中drl层的孔与{1}层孔径大小不一致，请检查标记处孔是否异常！".format(stepname, drill_layer)
                                arraylist.append(log)                                
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "hole_size_diff_tmp",
                                                                                     drill_layer, log, dic_zu_layer,
                                                                                     add_note_layer=drl) 
                        step.clearAll()
                        step.removeLayer("touch_hole_tmp")
                        step.removeLayer("touch_hole_tmp2")
                        step.removeLayer("hole_size_diff_tmp")
        
        if arraylist:
            return arraylist, dic_zu_layer
        
        return "success", None            
    
    def check_pnl_stepname_info(self, auto_check=None):
        """检查panel拼版内 step命名不能存在-edit，-set，        
        会影响输出程序获取有效单元数据异常，请修改，
        增加 存在icg step时icg是否拼入panel"""
        find_steps = []
        arraylist = []
        icg_steps = []
        icg_step_check_erro = False
        if "panel" in matrixinfo["gCOLstep_name"]:            
            all_steps = get_panelset_sr_step(job.name, "panel")
            for name in all_steps:
                if re.match(".*[_-](edit|set)[_-]?.*", name):
                    find_steps.append(name)
                    
            for icg_stepname in matrixinfo["gCOLstep_name"]:
                if "icg" in icg_stepname and icg_stepname not in all_steps:
                    icg_steps.append(icg_stepname)
                    icg_step_check_erro = True
                    
        if find_steps:
            log= u"检测到panel拼版内存在{0} step命名不能存在-edit，-set，<br>会影响输出程序获取有效单元数据异常，请修改！"
            arraylist.append(log.format(find_steps))            
                
        if icg_step_check_erro:
            log= u"检测到存在icg step，panel拼版内未拼入{0}，请检查！"
            arraylist.append(log.format(icg_steps))
            
        if auto_check is None:
            if arraylist:                
                showMessageInfo(*arraylist)        
            
        if auto_check == "yes":
            return arraylist if arraylist else "success", None
        
    def check_pnl_sr_spacing(self):
        """检测拼版间距"""
        stepname = "panel"
        if stepname not in matrixinfo["gCOLstep_name"]:
            return u"panel不存在", None
        
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        STR = '-t step -e %s/%s -d REPEAT,units=mm' % (job.name, stepname)
        gREPEAT_info = step.DO_INFO(STR)
        gREPEATstep = gREPEAT_info['gREPEATstep']
        gREPEATxmax = gREPEAT_info['gREPEATxmax']
        gREPEATymax = gREPEAT_info['gREPEATymax']
        gREPEATxmin = gREPEAT_info['gREPEATxmin']
        gREPEATymin = gREPEAT_info['gREPEATymin']
        rect_area = []
        rect_area_all = []
        for i in xrange(len(gREPEATstep)):
            xs = gREPEATxmin[i]
            ys = gREPEATymin[i]
            xe = gREPEATxmax[i]
            ye = gREPEATymax[i]
            rect_area_all.append([xs, ys, xe, ye])
            if re.match(r'^set|^edit|^icg', str(gREPEATstep[i])):       
                rect_area.append([xs, ys, xe, ye])
                
        spacing = []
        check_area = []
        arraylist = []
        log = ""
        step.removeLayer("sr_spacing_error+++")
        step.createLayer("sr_spacing_error+++")
        step.clearAll()
        step.affect("sr_spacing_error+++")
        step.reset_fill_params()
        #测试
        # self.pause_check_result(step, u"请比对相应的层及参考信息")
        for x1, y1, x2, y2 in rect_area:
            for x3, y3, x4, y4 in rect_area_all:
                if (x1, y1, x2, y2) == (x3, y3, x4, y4):
                    continue
                if (x3, y3, x4, y4) in check_area:
                    continue
                
                if max(x1, x3) < min(x2, x4) and \
                        max(y1, y3) < min(y2, y4):
                    spacing.append("0")
                    log += u"检测到拼版内有零间距，"
                    step.addRectangle(x1, y1, x2, y2)
                    step.addRectangle(x3, y3, x4, y4)
                    continue
                    
                if max(x1, x3 - 10) < min(x2, x4 + 10) and \
                        max(y1, y3 - 10) < min(y2, y4 + 10):
                    check_area.append((x3, y3, x4, y4))
                    arraylist_x = [x1-x4, x2-x3]
                    if x3< x1 < x4 or x3< x2 < x4:
                        arraylist_x = []
                    arraylist_y = [y1-y4, y2-y3]
                    if y3< y1 < y4 or y3< y2 < y4:
                        arraylist_y = []                
                    for value in arraylist_x + arraylist_y:                
                        if abs(value) < 10:
                            if [x3, y3, x4, y4] in rect_area_all and \
                               [x3, y3, x4, y4] not in rect_area:
                                if abs(value) > 2:
                                    continue
                                else:
                                    if max(x1, x3 - 2) < min(x2, x4 + 2) and \
                                       max(y1, y3 - 2) < min(y2, y4 + 2):
                                        pass
                                    else:
                                        continue
                                
                            #if "%.3f" % abs(value) == "1.013":
                                #print (x1, y1, x2, y2) , (x3, y3, x4, y4)
                            if abs(value) < 1.59:
                                if "1.6mm" not in log:
                                    log += u"检测到拼版内有小于1.6mm的间距，"
                                step.addRectangle(x1, y1, x2, y2)
                                step.addRectangle(x3, y3, x4, y4)                                
                                
                            spacing.append("%.2f" % abs(value))
        
        if spacing:
            if log:
                log += u"请到sr_spacing_error+++层内查看详细位置！所有拼版间距：{0}".format(",".join(sorted(list(set(spacing)), key=lambda x: float(x))))
                arraylist.append(log)
                layer = "sr_spacing_error+++"
                dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                      worklayer="view_layer_"+layer, 
                                                      dic_layer_list={log:[layer], },
                                                      dic_zu_layer={})
                return arraylist, dic_zu_layer
            
        return u"success 所有拼版间距:{0}".format(sorted(list(set(spacing)), key=lambda x: float(x))), None
    
    def pause_check_result(self, step, log, args=[], delete_log_file=True):
        if args:
            function_name = func+" "+" ".join(args)
        else:
            function_name = func        
        self.write_check_log_file(job.name, function_name+"_pause", u"暂停检查中")
        step.PAUSE(log.encode("utf8"))
        
        if delete_log_file:            
            if sys.platform == "win32":
                pause_log_path = "c:/tmp/check_log_{0}_{1}_pause.log".format(job.name, function_name)
            else:            
                pause_log_path = "/tmp/check_log_{0}_{1}_pause.log".format(job.name, function_name)
            try:            
                os.unlink(pause_log_path)
            except Exception, e:
                print e
        
    def comare_smd_mask_on_surface(self, auto_check=None):
        """挑选铜面smd比对开窗是否缩小"""
        stepname = "edit"
        if stepname in matrixinfo["gCOLstep_name"]:
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            arraylist = []
            dic_zu_layer = {}
            for worklayer in outsignalLayers:
                step.clearAll()
                step.affect(worklayer)
                step.resetFilter()
                step.setAttrFilter(".smd")
                step.selectAll()
                
                step.removeLayer(worklayer+"_smd+++")
                step.copySel(worklayer+"_smd+++")
                
                step.clearAll()
                step.affect(worklayer+"_smd+++")
                step.resetFilter()
                step.refSelectFilter(worklayer, mode='cover', f_types="surface", polarity="positive")
                step.COM("sel_reverse")
                if step.featureSelected():
                    step.selectDelete()
                    
                step.COM("sel_resize,size=10")                    
                
                step.clearAll()
                mask_layer = ""
                if worklayer == "l1":
                    if step.isLayer("m1"):
                        mask_layer = "m1"
                    if step.isLayer("m1-1"):
                        mask_layer = "m1-1"
                    
                else:
                    if step.isLayer("m2"):
                        mask_layer = "m2"
                    if step.isLayer("m2-1"):
                        mask_layer = "m2-1"                    
                
                if not mask_layer:
                    continue
                
                step.affect(mask_layer)
                step.resetFilter()
                step.refSelectFilter(worklayer+"_smd+++", mode='include', polarity="positive")
                if step.featureSelected():
                    step.removeLayer("find_smd+++")
                    step.copySel("find_smd+++")
                    step.clearAll()
                    step.affect("find_smd+++")
                    step.resetFilter()
                    step.refSelectFilter(worklayer, mode='cover', f_types="surface", polarity="positive")
                    step.COM("sel_reverse")
                    if step.featureSelected():
                        step.selectDelete()
                        
                    step.clearAll()
                    step.affect(mask_layer)
                    step.resetFilter()
                    step.refSelectFilter("find_smd+++",mode='include', polarity="positive")
                    if step.featureSelected():                        
                        log= u"检测到{0}层smd在铜面上的开窗比线路pad要大，请确认是否要缩铜面开窗，请检查！".format(worklayer)
                        arraylist.append(log)
                        
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, mask_layer,
                                                                         worklayer, log, dic_zu_layer)
                step.removeLayer(worklayer+"_smd+++")
            
            step.clearAll()
            step.removeLayer("find_smd+++")
            
            if arraylist and auto_check is None:
                showMessageInfo(*arraylist)
                self.view_note_detail(dic_zu_layer)
                
            if auto_check == "yes":
                return arraylist, dic_zu_layer
    
    def check_add_dynamics_jobname(self):
        """翟鸣提出：http://192.168.2.120:82/zentao/story-view-5123.html
        (1)940/B69/676/975/C75系列出货单元添加厂内料号时选择:$jobn，如中途变更型号保存后自动更新
        (2)其它系列添加时选择: $$job
        (3)防呆检测，特定系列检测Panel外Step是否添加$jobn Symbol，其它系列检测panel外Step是否添加$job Symbol
        (4)A11/A57部分型号不允许变更小版本部分型号允许。需MI指示，系统做提醒。"""
        stepname = "panel"
        if stepname not in matrixinfo["gCOLstep_name"]:
            return u"panel不存在", None
        
        cust_no = jobname[1:4]
        if cust_no.upper() in "A11/A57":
            return u"success A11/A57部分型号不允许变更小版本部分型号允许，请查看MI指示并确认添加是否正确", None
        
        all_steps = get_panelset_sr_step(jobname, "panel")
        arraylist = []
        dic_zu_layer = {}
        for stepname in all_steps:
            step = gClasses.Step(job, stepname)
            step.open()
            
            
            for layer in silkscreenLayers + solderMaskLayers + outsignalLayers:
                step.clearAll()
                step.affect(layer)
            
                step.resetFilter()
                step.filter_set(feat_types='text')
                step.selectAll()
                if step.featureSelected():
                    step.removeLayer("check_jobname_tmp")
                    step.copySel("check_jobname_tmp")
                    layer_cmd = gClasses.Layer(step, "check_jobname_tmp")
                    
                    feat_out = layer_cmd.featout_dic_Index(options="feat_index")["text"]
                    feat_out += layer_cmd.featout_dic_Index(options="feat_index")["barcodes"]
                    find_feat_index = []
                    for obj in feat_out:
                        # 屏蔽掉job_cut检测 20231025 by lyh
                        if "$$job" in getattr(obj, "text", "").lower() and "$$job_cut" not in getattr(obj, "text", "").lower():
                            if cust_no.upper() in "940/B69/676/975/C75":
                                if "$$jobn" not in obj.text.lower():
                                    log = u"940/B69/676/975/C75系列出货单元添加厂内料号时选择:$$jobn，检查到{0} 内添加的是$$job，请检查".format(stepname)
                                    arraylist.append(log)
                                    find_feat_index.append(obj.feat_index)
                            else:
                                if "$$jobn" in obj.text.lower():
                                    log = u"非940/B69/676/975/C75系列出货单元添加厂内料号时要用:$$job，检查到{0} 内添加的是$$jobn，请检查".format(stepname)
                                    arraylist.append(log)
                                    find_feat_index.append(obj.feat_index)                                

                    if find_feat_index:
                        step.clearAll()
                        step.affect("check_jobname_tmp")
                        for index in find_feat_index:
                            step.selectFeatureIndex("check_jobname_tmp", index)
                            
                        if step.featureSelected():                            
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "check_jobname_tmp",
                                                                                 layer, log, dic_zu_layer, add_note_layer=layer)            
            step.clearAll()
            step.removeLayer("check_jobname_tmp")
            
        if arraylist:
            return arraylist, dic_zu_layer
        
        return "success", None
    
    def check_set_panelization_is_defender(self, auto_check=None):
        """检测set拼版是否180度或镜像防呆
        http://192.168.2.120:82/zentao/story-view-6161.html"""
        stepname = "set"
        arraylist = []
        if stepname in matrixinfo["gCOLstep_name"]:
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            worklayer = "ww"            
            if step.isLayer(worklayer):
                xmin, ymin, xmax, ymax = get_profile_limits(step)
                dic_zu = {0: ["rotate", 180],1: ["mirror", 0],2: ["rotate\;mirror", 180],}
                for i in range(3):
                    step.removeLayer(worklayer+"-bf")
                    step.removeLayer(worklayer+"_diff")
                    step.clearAll()
                    step.copyLayer(job.name, stepname, worklayer, worklayer+"-bf")
                    step.affect(worklayer+"-bf")
                    step.COM("sel_transform,mode=anchor,oper={2},"
                             "duplicate=no,x_anchor={0},y_anchor={1},"
                             "angle={3},x_scale=1,y_scale=1,x_offset=0,"
                             "y_offset=0".format((xmin+xmax) *0.5, (ymin+ymax) *0.5, *dic_zu[i]))
                    tol = 25.4
                    step.COM("compare_layers,layer1=%s,job2=%s,step2=%s,\
                        layer2=%s,layer2_ext=,tol=%s,area=global,consider_sr=yes,\
                        ignore_attr=,map_layer=%s_diff,map_layer_res=2540" % (
                        worklayer, job.name, stepname, worklayer + "-bf", tol, worklayer))
                    step.clearAll()                    
                    step.affect(worklayer+"_diff")
                    step.resetFilter()
                    step.filter_set(feat_types='pad', include_syms='r0')
                    step.selectAll()
                    if not step.featureSelected():
                        if i == 0:                            
                            log = u"检测到此型号{0} 旋转180度拼版不防呆，请检查！".format(job.name)
                        if i == 1:
                            log = u"检测到此型号{0} X方向镜像拼版不防呆，请检查！".format(job.name)
                        if i == 2:
                            log = u"检测到此型号{0} Y方向镜像拼版不防呆，请检查！".format(job.name)                            
                        arraylist.append(log)
                        
                step.removeLayer(worklayer+"-bf")
                step.removeLayer(worklayer+"_diff")                
        
        if arraylist:            
            if auto_check == "manual":            
                showMessageInfo(*arraylist)
                return
            else:
                return arraylist, None
            
        return "success", None
    
    def check_inn_bk_touch_other_holes(self, auto_check=None):
        """检测靶孔跟通孔或内层其他孔是否接触 安全距离是否大于6mm
        http://192.168.2.120:82/zentao/story-view-6521.html
        20240301 by lyh"""
        stepname = "panel"
        if stepname in matrixinfo["gCOLstep_name"]:
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            arraylist_log = []
            for i, inn_layer in enumerate(matrixinfo["gROWname"]):
                if matrixinfo["gROWlayer_type"][i] == "drill" and "inn" in inn_layer:
                    drill_layers = []
                    if inn_layer == "inn":
                        drill_layers = ["drl", "cdc", "cds"]
                    else:                        
                        index = inn_layer[3:]
                        
                        for pre in ["b", "m"]:                            
                            mai_drill_layer = ""
                            if len(index) == 2:
                                mai_drill_layer = "{2}{0}-{1}".format(index[0], index[1], pre)
                            elif len(index) == 3:
                                mai_drill_layer = "{2}{0}-{1}".format(index[0], index[1:], pre)
                            elif len(index) == 4:
                                mai_drill_layer = "{2}{0}-{1}".format(index[:2], index[2:], pre)
                            
                            if "-" in index:
                                mai_drill_layer = "{1}{0}".format(index, pre)
                            
                            if mai_drill_layer and step.isLayer(mai_drill_layer):
                                drill_layers.append(mai_drill_layer)
                    
                    if drill_layers:
                        step.clearAll()                        
                        step.copyLayer(job.name, step.name, inn_layer, inn_layer+"_tmp_check")
                        step.affect(inn_layer+"_tmp_check")
                        step.changeSymbol("r12000")
                        
                        log = ""
                        for worklayer in drill_layers:
                            if step.isLayer(worklayer):
                                step.clearAll()
                                step.flatten_layer(worklayer, worklayer+"_flt_check")
                                step.affect(worklayer+"_flt_check")
                                step.resetFilter()
                                step.refSelectFilter(inn_layer+"_tmp_check")
                                if step.featureSelected():
                                    log = u"检测到靶孔层{0} 跟钻孔层{1} 的安全距离不够6mm，有部分孔被touch，请对比检查{2}层跟{3}层的内容！"
                                    arraylist_log.append(log.format(inn_layer, worklayer, inn_layer+"_tmp_check", worklayer+"_flt_check"))
                                else:
                                    step.removeLayer(worklayer+"_flt_check")
                                    
                        if not log:
                            step.removeLayer(inn_layer+"_tmp_check")
                            
            step.clearAll()            
            if arraylist_log:
                
                if auto_check == "manual":    
                    showMessageInfo(*arraylist_log)
                    return
                    
                return arraylist_log, None
                                    
        else:
            return u"success panel不存在，无需检测！", None
        
        return "success", None
    def check_target_distance_uploading_to_erp(self, uploading_to_erp="NO"):
        """检测靶距"""
        stepname = "panel"        
        if stepname not in matrixinfo["gCOLstep_name"]:
            return u"panel 不存在", None
        
        if lay_num <= 2:
            return u"success单双面板,无需检测", None
            
        step = gClasses.Step(job, stepname)
        step.open()
        user = top.getUser()
        mrp_info = get_mysql_target_info(job.name, "hdi_engineering.incam_process_info_temp") or \
            get_mysql_target_info(job.name, "hdi_engineering.incam_process_info")            
        ks_bs_mrp_info = get_mysql_ks_bd_target_info(job.name, "hdi_engineering.incam_drillprogram_info_temp") or \
            get_mysql_ks_bd_target_info(job.name, "hdi_engineering.incam_drillprogram_info")
        
        #检测MRPNAME跟型号是否一致 20231106 by lyh
        for dic_info in sorted(mrp_info, key=lambda x: x["PROCESS_NUM"] * -1):
            mrp_name = dic_info["MRPNAME"]
            if mrp_name.split("-")[0].lower() not in job.name:
                mrp_info = []
                break
        
        if uploading_to_erp in ["check_output", "auto_check", "output_tgz_check"]:
            # 输出裁磨线检测
            mrp_info = get_mysql_target_info(job.name, "hdi_engineering.incam_process_info")
            if uploading_to_erp == "check_output" and not mrp_info:
                mrp_info = get_mysql_target_info(job.name, "hdi_engineering.incam_process_info_temp")
                if mrp_info:
                    return u"靶距还未上传erp，请上传后再输出裁磨数据！", None
                
            ks_bs_mrp_info = get_mysql_ks_bd_target_info(job.name, "hdi_engineering.incam_drillprogram_info")
            # if uploading_to_erp == "auto_check" and not mrp_info: 自动检测跟裁磨输出都要检测跟erp是否一致 20230830 by lyh
            if not mrp_info:
                mrp_info = get_inplan_mrp_info(job.name)     

        if not mrp_info and uploading_to_erp == "manual":
            # 针对ECN升级的型号 先在临时库生成一个记录
            uploading_mrp_info = get_inplan_mrp_info(job.name)                   
            self.uploading_target_data(job.name, uploading_mrp_info, database="hdi_engineering.incam_process_info_temp")
            #因南通网络有延时 这里需等待0.5s
            num = 1
            while not mrp_info:                
                time.sleep(0.5)
                mrp_info = get_mysql_target_info(job.name, "hdi_engineering.incam_process_info_temp")
                num += 1
                if num > 20:
                    break
            #ecn升级的 板内的控深靶距对应erp的不好处理 以inplan的为准 cam不做上传
            ks_bs_mrp_info = []
            
        # 新增优先抓取资料user夹子下的控深靶记录 20240222 by lyh
        if uploading_to_erp == "manual":
            userDir = os.environ.get('JOB_USER_DIR', None)
            #此文件来自跑板边程序生成
            target_info_file = os.path.join(userDir, 'drill_bk_target_info.json')
            if os.path.exists(target_info_file):
                with open(target_info_file) as file_obj:
                    ks_bs_mrp_info = json.load(file_obj)
                
                for info in ks_bs_mrp_info:
                    info["START_INDEX"] = info["start_index"]
                    info["END_INDEX"] = info["end_index"]
                    del info["start_index"]
                    del info["end_index"]
        
        core_mrp_info = get_inplan_mrp_info(job.name.upper(), condtion="d.proc_subtype IN ( 27 ) ")
        
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
        rect_area = get_sr_area_for_step_include(stepname,
                                                 include_sr_step=["set", "edit", "icg"])
        all_x = [x1 for x1, y1, x2, y2 in rect_area]+[x2 for x1, y1, x2, y2 in rect_area]
        all_y = [y1 for x1, y1, x2, y2 in rect_area]+[y2 for x1, y1, x2, y2 in rect_area]
        sr_xmin = min(all_x)
        sr_xmax = max(all_x)
        sr_ymin = min(all_y)
        sr_ymax = max(all_y)
        # arraylist = []
        arraylist = [u"检测到靶距有以下问题，请检查是否异常！"]
        arraylist_same_size_log = [u"检测当前型号靶距跟ERP内相同尺寸(尺寸小于10mm以内算相同)靶距之差小于2mm为不防呆，请手动调整！"] # 记录比对相同尺寸 靶距不防呆的信息
        only_compare_distance_info = []# 输出tgz时仅检测靶距是否一致 防止有修改靶距 未重新上传跟输出裁膜
        show_msg = False
        dic_uploading_info = {}
        dic_uploading_erp_info = {}
        dic_coordinate_info = {}
        uploading_erp_info_log = [u"是否重新上传以下靶距信息到ERP，请确认："]
        
        if uploading_to_erp == "check_same_size_defender":
            
            dic_job_date = {}
            for dic_info in get_all_job_creation_date():       
                dic_job_date[dic_info["JOB_NAME"]] = dic_info["CREATION_DATE"]
                
            arraylist_same_size_info = self.get_same_size_jobs_info(job.name, f_xmax, f_ymax)
            #计算只保留最新版本
            new_arraylist_same_size_info = []
            jobnames = [x["JOB_NAME"][:11] for x in arraylist_same_size_info]
            exists_check_jobs = []
            for i, same_size_info in enumerate(arraylist_same_size_info):
                name = same_size_info["JOB_NAME"][:11]
                if name in exists_check_jobs:
                    continue
                
                if name in jobnames[i+1:] and name not in exists_check_jobs:
                    find_job_info = sorted([x for x in arraylist_same_size_info
                                            if x["JOB_NAME"][:11] == name], key=lambda t: t["JOB_NAME"])
                    new_arraylist_same_size_info.append(find_job_info[-1])
                    exists_check_jobs.append(name)
                else:
                    new_arraylist_same_size_info.append(same_size_info)
                    exists_check_jobs.append(name)
                #if "-lyh" in job.name:
                    #if "C67604EI045" in name.upper():
                        #print(same_size_info)
                    
                        #print(find_job_info)
                        #exit(0)
        
        for dic_info in sorted(mrp_info, key=lambda x: x["PROCESS_NUM"] * -1):
            from_lay = dic_info["FROMLAY"].lower()
            to_lay = dic_info["TOLAY"].lower()
            mrp_name = dic_info["MRPNAME"]
            rout_x = dic_info["PNLROUTX"] * 25.4
            rout_y = dic_info["PNLROUTY"] * 25.4
            lb_x = (f_xmax - rout_x) * 0.5
            lb_y = (f_ymax - rout_y) * 0.5
            
            array_erp_target_info = get_target_distance_info(mrp_name)
            if uploading_to_erp != "output_tgz_check":                
                if not array_erp_target_info:
                    log = u"检测到此型号{0} MI还未上传ERP，请通知MI上传完后，再重新上传靶距！".format(mrp_name)
                    if uploading_to_erp == "manual":
                        showMessageInfo(log)
                        return
                    else:
                        return log, None
                    
                if mrp_name.split("-")[0].lower() not in job.name:
                    log = u"检测到此型号{0} 压合子料号{1}跟型号名不一致，请通知MI更新数据后，再重新上传靶距！".format(job.name, mrp_name)
                    if uploading_to_erp == "manual":
                        showMessageInfo(log)
                        return
                    else:
                        return log, None                
            
            erp_target_info = {}
            for key, value in array_erp_target_info[0].iteritems():
                if value is None:
                    value = 0
                try:                    
                    erp_target_info[key] = format(round(float(value), 3), "0<6")
                except Exception as e:
                    erp_target_info[key] = "0"
                
            erp_log = u"erp:{0}-{1} 防呆靶：{L_X} 箭靶：{L_Y} X1：{X1} X2：{X2} Y1：{Y1} Y2：{Y2}"
            hdi_ba_log = ""
            if float(erp_target_info["W_X1"]) > 0:
                hdi_ba_log = u" 外X1：{W_X1} 外X2：{W_X2} 外Y1：{W_Y1} 外Y2：{W_Y2}"
            
            dic_calc_target_info = {}
            dic_coordinate_info[mrp_name] = {}
            dic_coordinate_info[mrp_name]["COORDINATE_JSON"] = {}
            
            index = signalLayers.index(from_lay)
            check_layer = signalLayers[index+1]
            
            press_num = dic_info["PROCESS_NUM"] - 1
            
            step.clearAll()
            step.affect(check_layer)
            step.resetFilter()
            
            step.selectSymbol("hdi1-baj{0};hdi1-bajt".format(press_num), 1, 1)
            layer_cmd = gClasses.Layer(step, check_layer)
            feat_out1 = layer_cmd.featSelOut(units="mm")["pads"]
            step.selectNone()
            step.selectSymbol("hdi1-ba{0};hdi1-bat".format(press_num), 1, 1)
            feat_out2 = layer_cmd.featSelOut(units="mm")["pads"]
            #特殊结构按下面进行 20230922 by lyh
            if "HD5604GI006B2".lower() in job.name and press_num == 1:
                step.selectSymbol("hdi1-baj{0}".format(press_num), 1, 1)
                layer_cmd = gClasses.Layer(step, check_layer)
                feat_out1 = layer_cmd.featSelOut(units="mm")["pads"]
                step.selectNone()
                step.selectSymbol("hdi1-ba{0}".format(press_num), 1, 1)
                feat_out2 = layer_cmd.featSelOut(units="mm")["pads"]
            
            #特殊料号
            if mrp_name == "SB6610GQXM2A3-10104":
                press_num = 1
                step.selectSymbol("hdi1-baj{0}".format(press_num), 1, 1)
                layer_cmd = gClasses.Layer(step, check_layer)
                feat_out1 = layer_cmd.featSelOut(units="mm")["pads"]
                step.selectNone()
                step.selectSymbol("hdi1-ba{0}".format(press_num), 1, 1)
                feat_out2 = layer_cmd.featSelOut(units="mm")["pads"]
                press_num = 2
            
            #特殊料号
            if mrp_name == "SB6610GQXM2A3-10510":
                press_num = 2
                step.selectSymbol("hdi1-baj{0}".format(press_num), 1, 1)
                layer_cmd = gClasses.Layer(step, check_layer)
                feat_out1 = layer_cmd.featSelOut(units="mm")["pads"]
                step.selectNone()
                step.selectSymbol("hdi1-ba{0}".format(press_num), 1, 1)
                feat_out2 = layer_cmd.featSelOut(units="mm")["pads"]                              
            
            #if "-lyh" in jobname:
                #step.PAUSE(str([check_layer,len(feat_out1), len(feat_out2)]))
            if len(feat_out1) ==2 and len(feat_out2) == 5:
                # 上箭靶
                upper_jianba_x = min([obj.x for obj in feat_out1])
                upper_jianba_y = [obj.y for obj in feat_out1
                                  if obj.x == upper_jianba_x][0]
                
                # 防呆靶
                fangdai_x = max([obj.x for obj in feat_out2
                             if obj.y > f_ymax * 0.5])
                fangdai_y = [obj.y for obj in feat_out2
                             if obj.y > f_ymax * 0.5
                             and obj.x == fangdai_x][0]        
                
                # 左上角
                upper_left_x, upper_left_y = \
                    [(obj.x, obj.y) for obj in feat_out2
                     if obj.y > f_ymax * 0.5
                     and obj.x != fangdai_x][0]
                
                # 右上角
                upper_right_x, upper_right_y = \
                    [(obj.x, obj.y) for obj in feat_out1
                     if obj.x != upper_jianba_x][0]
                
                # 左下角
                down_all_x = [obj.x for obj in feat_out2
                              if obj.y < f_ymax * 0.5]
                down_left_x, down_left_y = \
                    [(obj.x, obj.y) for obj in feat_out2
                     if obj.y < f_ymax * 0.5
                     and obj.x == min(down_all_x)][0]
                
                # 右下角
                down_right_x, down_right_y = \
                    [(obj.x, obj.y) for obj in feat_out2
                     if obj.y < f_ymax * 0.5
                     and obj.x == max(down_all_x)][0]
                
                # 下箭靶
                down_jianba_x, down_jianba_y = \
                    [(obj.x, obj.y) for obj in feat_out2
                     if obj.y < f_ymax * 0.5
                     and obj.x < max(down_all_x)
                     and obj.x > min(down_all_x)][0]
                
                dic_coordinate_info[mrp_name]["COORDINATE_JSON"]["bar3_xy"] = [(upper_jianba_x, upper_jianba_y), (fangdai_x, fangdai_y),
                                                                               (down_jianba_x, down_jianba_y)]
                
                dic_coordinate_info[mrp_name]["COORDINATE_JSON"]["bar4_xy"] = [(upper_left_x, upper_left_y), (upper_right_x, upper_right_y),
                                                                               (down_right_x, down_right_y), (down_left_x, down_left_y)]
                
                ba_type = ""
                all_x = [upper_left_x, upper_right_x, down_right_x, down_left_x]
                all_y = [upper_left_y, upper_right_y, down_right_y, down_left_y]                  
                # if "-lyh" in job.name:
                # 靶在长短边的交叉点处 需要将备用靶加进来一起参考
                ba_type = u"短边"
                if min(all_x) < sr_xmin and max(all_x) > sr_xmax:
                    ba_type = u"长边"
                    
                if min(all_y) < sr_ymin and max(all_y) > sr_ymax and \
                    min(all_x) < sr_xmin and max(all_x) > sr_xmax:
                    step.selectNone()
                    step.selectSymbol("hdi1-byj{0};hdi1-byjt".format(press_num), 1, 1)
                    if step.featureSelected():
                        byb_featout = layer_cmd.featSelOut(units="mm")["pads"]
                        if sr_xmin < byb_featout[0].x < sr_xmax and byb_featout[0].y > sr_ymax:
                            ba_type = u"长边"
                            
                        if sr_ymin < byb_featout[0].y < sr_ymax and byb_featout[0].x > sr_xmax:
                            ba_type = u"短边"                
                                          
                # if min(all_x) < sr_xmin and max(all_x) > sr_xmax:
                if ba_type == u"长边":                    
                    if (len(core_mrp_info) >= 2 or (f_xmax <= 622.3 and f_ymax <= 622.3)):
                        if f_ymax - lb_y - upper_right_y > 40 :                            
                            log =u"检测四靶在长边，但{1}层四靶顶部靶距裁边超工艺范围40，实际值{0}，请检查！".format(abs(f_ymax - lb_y - upper_right_y), check_layer)
                            arraylist.append(log)
                            show_msg = True
                    else:                        
                        if f_ymax - lb_y - upper_right_y > 70 or \
                           f_ymax - lb_y - upper_right_y < 20:
                            log =u"检测四靶在长边，但{1}层四靶顶部靶距裁边超工艺范围20-70，实际值{0}，请检查！".format(abs(f_ymax - lb_y - upper_right_y), check_layer)
                            arraylist.append(log)
                            show_msg = True                        
                        
                    if (len(core_mrp_info) >= 2 or (f_xmax <= 622.3 and f_ymax <= 622.3)):
                        if abs(f_ymin + lb_y - down_left_y) > 40:                            
                            log =u"检测四靶在长边，但{1}层四靶底部靶距裁边超工艺范围40，实际值{0}，请检查！".format(abs(f_ymin + lb_y - down_left_y), check_layer)
                            arraylist.append(log)
                            show_msg = True
                    else:                        
                        if abs(f_ymin + lb_y - down_left_y) > 70 or \
                           abs(f_ymin + lb_y - down_left_y) < 20:
                            log =u"检测四靶在长边，但{1}层四靶底部靶距裁边超工艺范围20-70，实际值{0}，请检查！".format(abs(f_ymin + lb_y - down_left_y), check_layer)
                            arraylist.append(log)
                            show_msg = True 
                        
                # if min(all_y) < sr_ymin and max(all_y) > sr_ymax:
                if ba_type == u"短边":
                    if abs(f_xmin + lb_x - upper_left_x) > 70 or \
                       abs(f_xmin + lb_x - upper_left_x) < 20:
                        log =u"检测四靶在短边，但{1}层四靶左侧靶距裁边超工艺范围20-70，实际值{0}，请检查！".format(abs(f_xmin + lb_x - upper_left_x), check_layer)
                        arraylist.append(log)
                        show_msg = True
                        
                        #if"-lyh" in job.name:
                            #step.PAUSE(str([upper_left_x,f_xmin, lb_x, fangdai_x, [obj.x for obj in feat_out2 if obj.y > f_ymax * 0.5]]))
                        
                    # step.PAUSE(str([f_ymax, lb_x, upper_right_x]))
                    if f_xmax - lb_x - upper_right_x > 70 or \
                       f_xmax - lb_x - upper_right_x < 20:
                        log =u"检测四靶在短边，但{1}层四靶右侧靶距裁边超工艺范围20-70，实际值{0}，请检查！".format(abs(f_xmax - lb_x - upper_right_x), check_layer)
                        arraylist.append(log)
                        show_msg = True                    
                
                if abs(upper_right_y - upper_left_y) > 0.1:
                    log =u"检测到四靶顶部靶距X方向不在一条直线上，相差{0}".format(abs(upper_right_y - upper_left_y))
                    arraylist.append(log)
                    show_msg = True
                
                if abs(upper_right_x - down_right_x) > 0.1:
                    log =u"检测到四靶右侧靶距Y方向不在一条直线上，相差{0}".format(abs(upper_right_x - down_right_x))
                    arraylist.append(log)
                    show_msg = True
                    
                if abs(upper_left_x - down_left_x) > 0.1:
                    log =u"检测到四靶左侧靶距Y方向不在一条直线上，相差{0}".format(abs(upper_left_x - down_left_x))                    
                    arraylist.append(log)
                    show_msg = True
                
                # 周涌通知防呆距离改为小于1mm 卡死 之前是2mm 20240913 by lyh
                if abs(abs(upper_left_y - down_left_y) - abs(upper_right_y - down_right_y)) < 1:
                    log =u"检测到四靶防呆靶防呆距离不足1mm，实际值{0}，请调整防呆间距".format(abs(abs(upper_left_y - down_left_y) - abs(upper_right_y - down_right_y)))                    
                    if log not in arraylist:
                        arraylist.append(log)
                    show_msg = True
                    
                step.selectNone()
                step.selectSymbol("hdi1-bs{0};hdi1-bst".format(press_num), 1, 1)
                #特殊料号
                if mrp_name == "SB6610GQXM2A3-10104":
                    step.selectNone()
                feat_out3 = layer_cmd.featSelOut(units="mm")["pads"]
                hdi_ba_log = ""
                if len(feat_out3) == 4:                    
                    dic_coordinate_info[mrp_name]["COORDINATE_JSON"]["wai_bar4_xy"] = [(obj.x, obj.y) for obj in feat_out3]
                    
                    all_x = [obj.x for obj in feat_out3]
                    all_y = [obj.y for obj in feat_out3]
                    if min(all_x) < sr_xmin and max(all_x) > sr_xmax:
                        upper_all_x = [obj.x for obj in feat_out3
                                      if obj.y > sr_ymax * 0.5]
                        upper_all_y = [obj.y for obj in feat_out3
                                      if obj.y > sr_ymax * 0.5]                        
                        down_all_x = [obj.x for obj in feat_out3
                                       if obj.y < sr_ymax * 0.5]
                        
                        left_all_y = [obj.y for obj in feat_out3
                                      if obj.x < sr_xmin]
                        left_all_x = [obj.x for obj in feat_out3
                                      if obj.x < sr_xmin]                        
                        right_all_y = [obj.y for obj in feat_out3
                                       if obj.x > sr_xmin]
                        right_all_x = [obj.x for obj in feat_out3
                                       if obj.x > sr_xmin] 
                        hdi_ba_log = u" 外X1：{0} 外X2：{1} 外Y1：{2} 外Y2：{3}"
                        hdi_ba_log = hdi_ba_log.format("", "",
                                                       format(round(max(right_all_y) - min(right_all_y), 3), "0<6"),
                                                       format(round(max(left_all_y) - min(left_all_y), 3), "0<6"))                                              
                    
                    if min(all_y) < sr_ymin and max(all_y) > sr_ymax:
                        upper_all_x = [obj.x for obj in feat_out3
                                      if obj.y > sr_ymax]
                        upper_all_y = [obj.y for obj in feat_out3
                                      if obj.y > sr_ymax]                        
                        down_all_x = [obj.x for obj in feat_out3
                                       if obj.y < sr_ymin]
                        left_all_y = [obj.y for obj in feat_out3
                                      if obj.x < sr_xmax * 0.5]
                        left_all_x = [obj.x for obj in feat_out3
                                      if obj.x < sr_xmax * 0.5]                        
                        right_all_y = [obj.y for obj in feat_out3
                                       if obj.x > sr_xmax * 0.5]
                        right_all_x = [obj.x for obj in feat_out3
                                       if obj.x > sr_xmax * 0.5]                        
                        hdi_ba_log = u" 外X1：{0} 外X2：{1} 外Y1：{2} 外Y2：{3}"
                        hdi_ba_log = hdi_ba_log.format(format(round(max(upper_all_x) - min(upper_all_x), 3), "0<6"),
                                                       format(round(max(down_all_x) - min(down_all_x), 3), "0<6"), "", "")                                               
                        
                    # if min(all_x) < sr_xmin and max(all_x) > sr_xmax:
                    if ba_type == u"长边":         
                        if (len(core_mrp_info) >= 2 or (f_xmax <= 622.3 and f_ymax <= 622.3)):
                            if f_ymax - lb_y - max(upper_all_y) > 40 :                                
                                log =u"检测外四靶在长边，但{1}层外四靶顶部靶距裁边超工艺范围40，实际值{0}，请检查！".format(abs(f_ymax - lb_y - max(upper_all_y)), check_layer)
                                arraylist.append(log)
                                show_msg = True
                        else:
                            if f_ymax - lb_y - max(upper_all_y) > 70 or \
                               f_ymax - lb_y - max(upper_all_y) < 20:
                                log =u"检测外四靶在长边，但{1}层外四靶顶部靶距裁边超工艺范围20-70，实际值{0}，请检查！".format(abs(f_ymax - lb_y - max(upper_all_y)), check_layer)
                                arraylist.append(log)
                                show_msg = True                            
                            
                        if (len(core_mrp_info) >= 2 or (f_xmax <= 622.3 and f_ymax <= 622.3)):
                            if abs(f_ymin + lb_y - min(left_all_y)) > 40:                                
                                log =u"检测外四靶在长边，但{1}层外四靶底部靶距裁边超工艺范围40，实际值{0}，请检查！".format(abs(f_ymin + lb_y - min(left_all_y)), check_layer)
                                arraylist.append(log)
                                show_msg = True
                        else:
                            if abs(f_ymin + lb_y - min(left_all_y)) > 70 or \
                               abs(f_ymin + lb_y - min(left_all_y)) < 20:
                                log =u"检测外四靶在长边，但{1}层外四靶底部靶距裁边超工艺范围20-70，实际值{0}，请检查！".format(abs(f_ymin + lb_y - min(left_all_y)), check_layer)
                                arraylist.append(log)
                                show_msg = True                             
                            
                    # if min(all_y) < sr_ymin and max(all_y) > sr_ymax:
                    if ba_type == u"短边":         
                        if abs(f_xmin + lb_x - min(upper_all_x)) > 70 or \
                           abs(f_xmin + lb_x - min(upper_all_x)) < 20:
                            log =u"检测外四靶在短边，但{1}层外四靶左侧靶距裁边超工艺范围20-70，实际值{0}，请检查！".format(abs(f_xmin + lb_x - min(upper_all_x)), check_layer)
                            arraylist.append(log)
                            show_msg = True
                            
                        # step.PAUSE(str([f_ymax, lb_x, upper_right_x]))
                        if f_xmax - lb_x - max(right_all_x) > 70 or \
                           f_xmax - lb_x - max(right_all_x) < 20:
                            log =u"检测外四靶在短边，但{1}层外四靶右侧靶距裁边超工艺范围20-70，实际值{0}，请检查！".format(abs(f_xmax - lb_x - max(right_all_x)), check_layer)
                            arraylist.append(log)
                            show_msg = True                           
                        
                    if abs(max(upper_all_y) - min(upper_all_y)) > 0.1:
                        log =u"检测到外四靶顶部靶距X方向不在一条直线上，相差{0}".format(max(upper_all_y) - min(upper_all_y))
                        arraylist.append(log)
                        show_msg = True
                    
                    if abs(max(right_all_x) - min(right_all_x)) > 0.1:
                        log =u"检测到外四靶右侧靶距Y方向不在一条直线上，相差{0}".format(max(right_all_x) - min(right_all_x))
                        arraylist.append(log)
                        show_msg = True
                        
                    if abs(max(left_all_x) - min(left_all_x)) > 0.1:
                        log =u"检测到外四靶左侧靶距Y方向不在一条直线上，相差{0}".format(max(left_all_x) - min(left_all_x))                    
                        arraylist.append(log)
                        show_msg = True
                    
                    # 周涌通知防呆距离改为小于1mm 卡死 之前是2mm 20240913 by lyh
                    if abs(abs(max(right_all_y) - min(right_all_y)) - abs(max(left_all_y) - min(left_all_y))) < 1:
                        log =u"检测到外四靶防呆靶防呆距离不足1mm，实际值{0}，请调整防呆间距".format(abs(abs(max(right_all_y) - min(right_all_y)) - abs(max(left_all_y) - min(left_all_y))))                    
                        if log not in arraylist:
                            arraylist.append(log)
                        show_msg = True                        
                        
                    dic_calc_target_info["W_X1"] = round(max(all_x) - min(all_x), 3)
                    dic_calc_target_info["W_Y1"] = round(max(right_all_y) - min(right_all_y), 3)
                    dic_calc_target_info["W_X2"] = round(max(all_x) - min(all_x), 3)
                    dic_calc_target_info["W_Y2"] = round(max(left_all_y) - min(left_all_y), 3)                           
                        
                        
                tgz_log = u"tgz:{0}-{1} 防呆靶：{2} 箭靶：{3} X1：{4} X2：{5} Y1：{6} Y2：{7}{8}"
                
                dic_calc_target_info["L_X"] = round(upper_jianba_x-fangdai_x, 3)
                dic_calc_target_info["L_Y"] = round(upper_jianba_y-down_jianba_y, 3)
                
                dic_calc_target_info["X1"] = round(upper_right_x-upper_left_x, 3)
                dic_calc_target_info["Y1"] = round(upper_right_y-down_right_y, 3)
                dic_calc_target_info["X2"] = round(down_right_x-down_left_x, 3)
                dic_calc_target_info["Y2"] = round(upper_left_y-down_left_y, 3)
                
                if "-" not in mrp_name and uploading_to_erp == "check_same_size_defender":
                    # 只检测外层即可
                    # print(new_arraylist_same_size_info)
                    same_size_log = u"当前型号:防呆靶：{L_X} 箭靶：{L_Y} 四靶 X1：{X1} X2：{X2} Y1：{Y1} Y2：{Y2} panel_x:{panel_x} panel_y:{panel_y} ({JOB_NAME})"
                    arraylist_same_size_log.append(same_size_log.format(JOB_NAME=job.name,panel_x=f_xmax, panel_y=f_ymax, **dic_calc_target_info))
                    for same_size_dic_info in new_arraylist_same_size_info:
                        
                        job_create_time = dic_job_date.get(same_size_dic_info["JOB_NAME"], datetime.datetime.now())
                        timestamp = time.mktime(job_create_time.timetuple()) 
                        diff_time = time.time() - timestamp
                        if diff_time / (24 * 3600) > 90:
                            continue
                        #if "C67604EI045" in same_size_dic_info["JOB_NAME"].upper():
                            #print(same_size_dic_info,dic_calc_target_info)
                            #exit(0)
                        bar4_x1 = same_size_dic_info["BAR4X1"]
                        bar4_y1 = same_size_dic_info["BAR4Y1"]
                        if round(abs(bar4_x1 - dic_calc_target_info["X1"]), 1) < 2 and round(abs(bar4_y1 - dic_calc_target_info["Y1"]), 1) < 2:
                            same_size_log = u"其他型号:防呆靶：{BAR3X} 箭靶：{BAR3Y} 四靶 X1：{BAR4X1} X2：{BAR4X2} Y1：{BAR4Y1} Y2：{BAR4Y2}  panel_x:{panel_x} panel_y:{panel_y} ({JOB_NAME} 四靶不防呆)"
                            arraylist_same_size_log.append(same_size_log.format(**same_size_dic_info))
                            
                        #bar3_x = same_size_dic_info["BAR3X"]
                        #bar3_y = same_size_dic_info["BAR3Y"]
                        #if abs(bar3_x - dic_calc_target_info["L_X"]) < 2 and abs(bar3_y - dic_calc_target_info["L_Y"]) < 2:
                            #same_size_log = u"其他型号:防呆靶：{BAR3X} 箭靶：{BAR3Y} 四靶 X1：{BAR4X1} X2：{BAR4X2} Y1：{BAR4Y1} Y2：{BAR4Y2}  panel_x:{panel_x} panel_y:{panel_y} ({JOB_NAME} 箭靶不防呆)"
                            #arraylist_same_size_log.append(same_size_log.format(**same_size_dic_info))                            
                        
                dic_uploading_info[mrp_name] = {"BAR4X1": dic_calc_target_info["X1"],"BAR4X2": dic_calc_target_info["X2"],
                                                "BAR4Y1": dic_calc_target_info["Y1"],"BAR4Y2": dic_calc_target_info["Y2"],
                                                "BAR3Y": dic_calc_target_info["L_Y"] ,"BAR3X": dic_calc_target_info["L_X"],
                                                "SIG4X1": dic_calc_target_info.get("W_X1", 0),"SIG4X2": dic_calc_target_info.get("W_X2", 0),
                                                "SIG4Y1": dic_calc_target_info.get("W_Y1", 0),"SIG4Y2": dic_calc_target_info.get("W_Y2", 0),
                                                "TARGET_DESIGNREGION": u"'{0}'".format(ba_type),
                                                "CAM_NOTES": u"'用户{0}重新上传'".format(user),}
                
                dic_uploading_erp_info[mrp_name] = {"TC_AAC231": dic_calc_target_info["X1"],"TC_AAC233": dic_calc_target_info["X2"],
                                                    "TC_AAC232": dic_calc_target_info["Y1"],"TC_AAC234": dic_calc_target_info["Y2"],
                                                    "TC_AAC28": dic_calc_target_info["L_Y"] ,"TC_AAC27": dic_calc_target_info["L_X"],
                                                    "TC_AAC235": dic_calc_target_info.get("W_X1", 0),"TC_AAC237": dic_calc_target_info.get("W_X2", 0),
                                                    "TC_AAC236": dic_calc_target_info.get("W_Y1", 0),"TC_AAC238": dic_calc_target_info.get("W_Y2", 0),}             
                
                uploading_erp_info_log.append(tgz_log.format(from_lay.upper(), format(to_lay.upper()[1:], ">2"),
                                                             format(round(upper_jianba_x-fangdai_x, 3), "0<6"),
                                                             format(round(upper_jianba_y-down_jianba_y, 3), "0<6"),
                                                             format(round(upper_right_x-upper_left_x, 3), "0<6"),
                                                             format(round(down_right_x-down_left_x, 3), "0<6"),
                                                             format(round(upper_right_y-down_right_y, 3), "0<6"),
                                                             format(round(upper_left_y-down_left_y, 3), "0<6"),
                                                             hdi_ba_log))                
                step.clearAll()
                
                #检测靶是否被镜像 20240527 by lyh
                # if "-lyh" in job.name:                    
                is_mirror = [obj.mirror for obj in feat_out1 + feat_out2 + feat_out3]
                if "yes" in is_mirror:
                    log =u"检测到{0} 层四靶或L靶被镜像 ，请检查靶是否异常！".format(check_layer)
                    arraylist.append(log)
                    show_msg = True
                    
                # print dic_calc_target_info
                # print erp_target_info
                
                # if "-lyh" in job.name:                    
                try:
                    dic_coordinate_json_info = json.loads(dic_info["COORDINATE_JSON"], encoding='utf8')
                except:
                    dic_coordinate_json_info = None
                if dic_coordinate_json_info is not None:
                    for check_key, check_value in dic_coordinate_info[mrp_name]["COORDINATE_JSON"].iteritems():
                        if dic_coordinate_json_info.get(check_key):
                            for (x1, y1) in dic_coordinate_json_info[check_key]:
                                for (x2, y2) in check_value:
                                    if abs(x1 - x2) < 0.1 and abs(y1-y2) < 0.1:
                                        break
                                else:
                                    log = u"检测到{0} 坐标被移动，没有重新上传数据库，请重新上传靶距1！"
                                    only_compare_distance_info.append(log.format(check_key))
                                    break
                        else:
                            log = u"检测到{0} 坐标被移动，没有重新上传数据库，请重新上传靶距2！"
                            only_compare_distance_info.append(log.format(check_key))
                            break                                
                
                diff_log = ""
                for key, value in dic_calc_target_info.iteritems():
                    
                    if value < 0:                        
                        log =u"检测到{0} 为负值{1}，请检查靶标添加是否正确！".format(u"外"+key.replace("W_", "") if "W_" in key else "", value)                    
                        if log not in arraylist:
                            arraylist.append(log)
                        show_msg = True
                        if uploading_to_erp == "manual":
                            showMessageInfo(log)
                            return None                           
                    
                    if erp_target_info.has_key(key):
                        # print "--->",mrp_name, float(erp_target_info[key]) , value, float(erp_target_info[key]) - value
                        if key in ["W_X1", "W_X2","W_Y1","W_Y2"] and float(erp_target_info[key]) == 0:
                            continue
                        if abs(float(erp_target_info[key]) - value) > 0.1:
                            diff_log = u"{3}-{4} {0}{1}相差{2}:".format(u"外"+key.replace("W_", "") if "W_" in key else "", key,
                                                                        format(round(float(erp_target_info[key]) - value, 1), "0<3"),
                                                                        from_lay.upper(),
                                                                        format(to_lay.upper()[1:], ">2"))                            
                            arraylist.append(diff_log)
                            #此种情况为erp还未上传数据
                            if erp_target_info[key] != "0":
                                only_compare_distance_info.append(diff_log)
                            
                if diff_log:                    
                    arraylist.append((erp_log+hdi_ba_log).format(from_lay,to_lay, **erp_target_info))
                    arraylist.append(tgz_log.format(from_lay.upper(), format(to_lay.upper()[1:], ">2"),
                                                format(round(upper_jianba_x-fangdai_x, 3), "0<6"),
                                                format(round(upper_jianba_y-down_jianba_y, 3), "0<6"),
                                                format(round(upper_right_x-upper_left_x, 3), "0<6"),
                                                format(round(down_right_x-down_left_x, 3), "0<6"),
                                                format(round(upper_right_y-down_right_y, 3), "0<6"),
                                                format(round(upper_left_y-down_left_y, 3), "0<6"),
                                                hdi_ba_log))
                    
                    if only_compare_distance_info:
                        
                        only_compare_distance_info.append((erp_log+hdi_ba_log).format(from_lay,to_lay, **erp_target_info))
                        only_compare_distance_info.append(tgz_log.format(from_lay.upper(), format(to_lay.upper()[1:], ">2"),
                                                    format(round(upper_jianba_x-fangdai_x, 3), "0<6"),
                                                    format(round(upper_jianba_y-down_jianba_y, 3), "0<6"),
                                                    format(round(upper_right_x-upper_left_x, 3), "0<6"),
                                                    format(round(down_right_x-down_left_x, 3), "0<6"),
                                                    format(round(upper_right_y-down_right_y, 3), "0<6"),
                                                    format(round(upper_left_y-down_left_y, 3), "0<6"),
                                                    hdi_ba_log))
                    show_msg = True
            else:
                if "-" not in dic_info["MRPNAME"]:                
                    if rout_x == 0 and rout_y == 0:
                        # 双面板 直接返回成功
                        log = u"检测到此型号{0} 为双面板，双面板无需上传靶距！".format(mrp_name)
                        if uploading_to_erp == "manual":
                            showMessageInfo(log)
                            return
                        else:                                            
                            return "success", None
                    
                log = u"tgz:{0}-{1} 对应的靶标抓取异常，请手动测量此组数据！"
                arraylist.append(log.format(from_lay.upper(), to_lay.upper()[1:],))
                show_msg = True
                
            step.clearAll()
            
        if uploading_to_erp == "output_tgz_check":
            if only_compare_distance_info:
                showMessageInfo(u"检测到靶距跟erp不一致，请重新上传靶距并输出裁膜资料！！", *only_compare_distance_info)
                return only_compare_distance_info, None
            return "success", None
            
        # step.PAUSE(str([len(ks_bs_mrp_info)]))
        if ks_bs_mrp_info:
            # 比对背钻跟控深靶距
            dic_uploading_ks_bs_info = {}
            for i, ks_drill_lay in enumerate(matrixinfo["gROWname"]):
                if matrixinfo["gROWlayer_type"][i] == "drill":
                    # step.PAUSE(str([ks_drill_lay, re.match("[bc]d[cs].*", ks_drill_lay)]))
                    if re.match("[bc]d[cs]?.*", ks_drill_lay) and \
                       step.isLayer(ks_drill_lay+".inn"):
                        layer_cmd = gClasses.Layer(step, ks_drill_lay+".inn")
                        feat_out = layer_cmd.featCurrent_LayerOut(units="mm")["pads"]
                        attrs = [getattr(obj, "string", "") for obj in feat_out]
                        is_continue = True
                        ks_bd_erp_target_info = {}
                        for dic_info in sorted(ks_bs_mrp_info, key=lambda x: x["PROCESS_LEVEL"] * -1):
                            ks_bd_erp_target_info = dic_info
                            mysql_id = dic_info["ID"]
                            # print "--->", [mysql_id]
                            if str(mysql_id) in "".join(attrs):
                                is_continue = False
                                break
                            
                        # step.PAUSE(str([ks_bs_mrp_info, len(feat_out), attrs, is_continue]))
                        if is_continue:
                            continue                        
                        
                        dic_ks_bd_calc_target_info = {}
                        if len(feat_out) == 4:                
                            # 左上角
                            upper_left_x, upper_left_y = \
                                [(obj.x, obj.y) for obj in feat_out
                                 if obj.y > f_ymax * 0.5
                                 and obj.x < f_xmax * 0.5][0]
                            
                            # 右上角
                            upper_right_x, upper_right_y = \
                                [(obj.x, obj.y) for obj in feat_out
                                 if obj.y > f_ymax * 0.5
                                 and obj.x > f_xmax * 0.5][0]
                            
                            # 左下角
                            down_left_x, down_left_y = \
                                [(obj.x, obj.y) for obj in feat_out
                                 if obj.y < f_ymax * 0.5
                                 and obj.x < f_xmax * 0.5][0]
                            
                            # 右下角
                            down_right_x, down_right_y = \
                                [(obj.x, obj.y) for obj in feat_out
                                 if obj.y < f_ymax * 0.5
                                 and obj.x > f_xmax * 0.5][0]
                            
                            dic_ks_bd_calc_target_info["TARGET_X1"] = round(upper_right_x-upper_left_x, 3)
                            dic_ks_bd_calc_target_info["TARGET_Y1"] = round(upper_right_y-down_right_y, 3)
                            dic_ks_bd_calc_target_info["TARGET_X2"] = round(down_right_x-down_left_x, 3)
                            dic_ks_bd_calc_target_info["TARGET_Y2"] = round(upper_left_y-down_left_y, 3)
                            
                            dic_uploading_ks_bs_info[mysql_id] = dic_ks_bd_calc_target_info
                            
                            for key, value in dic_ks_bd_calc_target_info.iteritems():
                                if ks_bd_erp_target_info.has_key(key):
                                    if abs(float(ks_bd_erp_target_info[key]) - value) > 0.1:
                                        diff_log = u"\n\n控深或背钻靶距{0} {1}相差{2}:".format(ks_drill_lay, key,
                                                                            format(round(float(ks_bd_erp_target_info[key]) - value, 1), "0<3"))                                        
                                        arraylist.append(diff_log)
                                        show_msg = True
                                        # step.PAUSE(str([ks_bd_erp_target_info[key], value, key]))
            
        if uploading_to_erp == "manual":
            if not mrp_info:
                showMessageInfo(u"检测到mysql数据没有保存靶距信息，请重新跑板边生成信息0！")
                return
            # res = showQuestionMessageInfo(u"靶距跟erp不一致，点击继续，将弹出上传界面！", end_btn_text=u"退出,不上传")
            # if res:
            #if "-lyh" in jobname:
                #job.PAUSE(str([mrp_info, "----------------->", dic_uploading_info]))
                
            new_array_mrp_info = []
            for dic_info in mrp_info:
                mrp_name = dic_info["MRPNAME"]
                dic_info.update(dic_uploading_info[mrp_name])                        
                new_array_mrp_info.append(dic_info)
                
            #先往正式库内写入数据
            if "-lyh" not in job.name:                
                uploading_mrp_info = get_mysql_all_target_info(job.name, "hdi_engineering.incam_process_info_temp")            
                self.uploading_target_data(job.name, uploading_mrp_info, database="hdi_engineering.incam_process_info")
                
            ui = TargetDistance_UI()
            ui.set_model_data(1, new_array_mrp_info, ["JOB_NAME", "MRPNAME",
                                                      "BAR4X1", "BAR4Y1", "BAR4X2", "BAR4Y2",
                                                      "BAR3X", "BAR3Y",
                                                      "SIG4X1", "SIG4Y1", "SIG4X2", "SIG4Y2",
                                                      "FROMLAY", "TOLAY", "CAM_NOTES"],
                              u"'{0}用户上传'".format(user))
            
            # if "-lyh" in job.name:
            self.update_coordinate_json_info(job.name, dic_coordinate_info)
            
            if ks_bs_mrp_info:                
                new_array_mrp_info = []
                log = ""
                for dic_info in ks_bs_mrp_info:
                    ID = dic_info["ID"]
                    if dic_uploading_ks_bs_info.has_key(ID):                        
                        dic_info.update(dic_uploading_ks_bs_info[ID])
                    else:
                        log += u"{0} 的靶距抓取失败，请手动测量并录入靶距值！\n"
                        dic_info["TARGET_X1"] = ""
                        dic_info["TARGET_Y1"] = ""
                        dic_info["TARGET_X2"] = ""
                        dic_info["TARGET_Y2"] = ""
                    
                    # dic_info["CAM_NOTES"] = u"'{0}用户重新上传'".format(user)
                    new_array_mrp_info.append(dic_info)
                
                #先往正式库内写入数据
                if "-lyh" not in job.name:
                    uploading_mrp_info = get_mysql_ks_bd_all_target_info(job.name, "hdi_engineering.incam_drillprogram_info_temp")                
                    self.uploading_target_data(job.name, uploading_mrp_info, database="hdi_engineering.incam_drillprogram_info")
                
                ui.set_model_data(2, new_array_mrp_info, ["JOB_NAME", "MRP_NAME", "ODB_DRILL_NAME",
                                                          "TARGET_X1", "TARGET_Y1", "TARGET_X2", "TARGET_Y2",
                                                          "START_INDEX", "END_INDEX", "ID"],
                                  u"'{0}用户上传'".format(user))  
            ui.exec_()
            
            #if len(job.name) == 13 or "-lyh" in job.name:                        
                #result = self.uploading_target_info_to_erp(dic_uploading_erp_info)                            
                #self.uploading_target_data(job.name, dic_uploading_info)
                #if result:
                    #showMessageInfo(result)
                    #return result, None
                
            showMessageInfo(u"靶距上传成功")
            
            return None        
    
        if uploading_to_erp == "atuo_uploading":
            
            if not mrp_info:
                return u"检测到mysql数据没有保存靶距信息，请重新跑板边生成信息0！", None
            
            #sql = """select * from pdm_job_workflow a,
            #pdm_job b
            #where a.process_id = 527
            #and a.job_id = b.id
            #and b.jobname = '{0}'"""
            #data_info = ikm_fun.PG.SELECT_DIC(ikm_fun.dbc_p, sql.format(jobname.lower()))
            #if data_info:
                #return u"检测到裁磨资料有输出记录，程序不能自动上传靶距，请手动上传后再重新输出裁磨资料！", None
            
            # if not data_info:
                
                #for dic_info in mrp_info:
                    #mrp_name = dic_info["MRPNAME"]
                    #array_erp_target_info = get_target_distance_info(mrp_name)
                    #if array_erp_target_info:
                        #return u"erp已上传了靶距信息，程序不能自动上传，请手动上传覆盖！", None
                
            new_array_mrp_info = []
            for dic_info in mrp_info:
                mrp_name = dic_info["MRPNAME"]
                dic_info.update(dic_uploading_info[mrp_name])                        
                new_array_mrp_info.append(dic_info)
                
                dic_uploading_info[mrp_name]["CAM_NOTES"] = "'system'"
                # 此三个参数因inplan后续会修改 故不将此三个参数放到mysql数据库
                # 裁磨线输出也是以inplan内的数据为准 20230905 by lyh
                dic_uploading_info[mrp_name]["YHTHICK"] = 0
                dic_uploading_info[mrp_name]["YHTHKPLUS"] = 0
                dic_uploading_info[mrp_name]["YHTHKDOWN"] = 0
                
            #先往正式库内写入数据                  
            uploading_mrp_info = get_mysql_all_target_info(job.name, "hdi_engineering.incam_process_info_temp")            
            self.uploading_target_data(job.name, uploading_mrp_info, database="hdi_engineering.incam_process_info")
            
            res = self.update_target_data(job.name,dic_uploading_info, database="hdi_engineering.incam_process_info")
            if res:
                return res, None
            
            result = self.uploading_target_info_to_erp(dic_uploading_erp_info)
            if result:
                return result, None            
            
            if ks_bs_mrp_info:                
                new_array_mrp_info = []
                log = ""
                for dic_info in ks_bs_mrp_info:
                    ID = dic_info["ID"]
                    if dic_uploading_ks_bs_info.has_key(ID):                        
                        dic_info.update(dic_uploading_ks_bs_info[ID])
                        dic_uploading_ks_bs_info[ID]["CAM_NOTES"] = "'system'"
                    else:
                        log += u"{0} 的靶距抓取失败，请手动测量并录入靶距值！\n"
                        dic_info["TARGET_X1"] = ""
                        dic_info["TARGET_Y1"] = ""
                        dic_info["TARGET_X2"] = ""
                        dic_info["TARGET_Y2"] = ""
                    
                    new_array_mrp_info.append(dic_info)
                
                #先往正式库内写入数据                
                uploading_mrp_info = get_mysql_ks_bd_all_target_info(job.name, "hdi_engineering.incam_drillprogram_info_temp")                
                self.uploading_target_data(job.name, uploading_mrp_info, database="hdi_engineering.incam_drillprogram_info")
                
                res = self.update_target_data(job.name,dic_uploading_ks_bs_info, database="hdi_engineering.incam_drillprogram_info")
                if res:
                    return res, None                
                
        if uploading_to_erp == "check_same_size_defender":
            if len(arraylist_same_size_log) > 2:
                return arraylist_same_size_log, None               
                
        if show_msg:
            #if uploading_to_erp == "YES":
                #showMessageInfo(*arraylist)
                #res = showQuestionMessageInfo(*(arraylist+uploading_erp_info_log), end_btn_text=u"退出,不上传")
                #if res:
                    #if len(job.name) == 13 or "-lyh" in job.name:                        
                        #result = self.uploading_target_info_to_erp(dic_uploading_erp_info)                            
                        #self.uploading_target_data(job.name, dic_uploading_info)
                        #if result:
                            #showMessageInfo(result)
                            #return result, None                        
                        #return u"success重新上传成功", None
                        
            return arraylist, None                
        
        if not mrp_info:
            return u"success非新跑板边，无需检测", None
        
        return "success", None
    
    def get_same_size_jobs_info(self,jobname, panel_x, panel_y):
        """获取相同尺寸的型号"""
        sql = """select a.bar3x BAR3X,a.bar3y BAR3Y,
        a.bar4x1 BAR4X1,a.bar4y1 BAR4Y1,
        a.bar4x2 BAR4X2,a.bar4y2 BAR4Y2,
        a.job_name JOB_NAME,round(a.pnlxinch*25.4,3) panel_x,
        round(a.pnlyinch*25.4,3) panel_y
        from hdi_engineering.incam_process_info a
        where ABS(a.pnlxinch*25.4-{0}) < 10
        and ABS(a.pnlyinch*25.4-{1}) < 10
        and a.mrpname not like '%-%'
        and a.job_name <>'{2}'"""
        # print(sql.format(panel_x, panel_y, jobname.split("-")[0]))
        data_info1 = conn.SELECT_DIC(dbc_m, sql.format(panel_x, panel_y, jobname.split("-")[0]))
        
        sql = """select a.bar3x BAR3X,a.bar3y BAR3Y,
        a.bar4x1 BAR4X1,a.bar4y1 BAR4Y1,
        a.bar4x2 BAR4X2,a.bar4y2 BAR4Y2,
        a.job_name JOB_NAME,round(a.pnlxinch*25.4,3) panel_x,
        round(a.pnlyinch*25.4,3) panel_y
        from hdi_engineering.incam_process_info_temp a
        where ABS(a.pnlxinch*25.4-{0}) < 10
        and ABS(a.pnlyinch*25.4-{1}) < 10
        and a.mrpname not like '%-%'
        and a.job_name <>'{2}'"""
        # print(sql.format(panel_x, panel_y, jobname.split("-")[0]))
        data_info2 = conn.SELECT_DIC(dbc_m, sql.format(panel_x, panel_y, jobname.split("-")[0]))        
        
        if data_info1 and data_info2:
            return data_info2 + data_info1
        else:
            return data_info1 or data_info2
    
    def uploading_target_info_to_erp(self, dic_erp_info={}):
        """上传靶距到erp系统"""
        for key, value in dic_erp_info.iteritems():
            new_value = {}
            for k, v in value.iteritems():
                new_value[k.lower()] = "%.3f" % v
                
            new_value.update({"tc_aac01": key.upper()})
            dic_params = {"body": new_value,"col": 11,"row": 1,}
            res = post_message(**dic_params)            
            if res:
                return res

    def uploading_target_data(self, jobname, arraylist_data, database="hdi_engineering.incam_process_info"):
        """上传靶距到mysql系统"""
        sql = "select * from {1} where job_name = '{0}'"
        data_info = conn.SQL_EXECUTE(dbc_m, sql.format(jobname.split("-")[0], database))
        if data_info:
            sql = "delete from {1} where job_name = '{0}'"
            conn.SQL_EXECUTE(dbc_m, sql.format(jobname.split("-")[0], database))
            
        for dic_info in arraylist_data:
            arraylist_key = []
            arraylist_value = []
            for key, value in dic_info.iteritems():
                if key == "id" and database <> "hdi_engineering.incam_drillprogram_info":
                    continue
                arraylist_key.append(key)
                if isinstance(value, (float)):
                    if key in ["PNLXINCH", "PNLYINCH"]:
                        arraylist_value.append(str(value))
                    else:
                        arraylist_value.append("%.3f"%(value))
                else:
                    try:                        
                        arraylist_value.append(str(value))
                    except:
                        arraylist_value.append(value)

            insert_sql = u"insert into {2} ({0}) values ({1})"
            conn.SQL_EXECUTE(dbc_m, insert_sql.format(",".join(arraylist_key),",".join(["%s"]*len(arraylist_key)), database), arraylist_value)
            
    def update_target_data(self, jobname, dic_target_info={}, database="hdi_engineering.incam_process_info"):
        """更新靶距到mysql系统"""
        sql = "select * from {1} where job_name = '{0}'"
        # print "--------->", sql.format(jobname.split("-")[0], database)
        data_info = conn.SQL_EXECUTE(dbc_m, sql.format(jobname.split("-")[0], database))
        if data_info:
            for key, value in dic_target_info.iteritems():
                param = []
                for k, v in value.iteritems():
                    if k == "ID":
                        continue
                    if not v:
                        v = "''"
                    param.append(u"{0}={1}".format(k, v))
                if database == "hdi_engineering.incam_process_info" or database == "hdi_engineering.incam_process_info_temp":                    
                    sql = u"update {2} set {0},create_time=now() where mrpname = '{1}'"
                    conn.SQL_EXECUTE(dbc_m, sql.format(",".join(param), key, database))
                else:
                    sql = u"update {2} set {0},create_time=now() where ID = {1}"
                    conn.SQL_EXECUTE(dbc_m, sql.format(",".join(param), key, database))
        else:
            return u"检测到mysql数据没有靶距信息，请重新跑板边生成信息！"
        
        return None
    
    def update_coordinate_json_info(self, jobname, dic_target_info={}, database="hdi_engineering.incam_process_info"):
        """更新靶距的各个靶标坐标位置信息"""
        sql = "select * from {1} where job_name = '{0}'"
        # print "--------->", sql.format(jobname.split("-")[0], database)
        data_info = conn.SQL_EXECUTE(dbc_m, sql.format(jobname.split("-")[0], database))
        if data_info:
            for key, value in dic_target_info.iteritems():
                param = []
                update_values = []
                for k, v in value.iteritems():
                    if k == "ID":
                        continue
                    if not v:
                        v = "''"
                    param.append(u"{0}=%s".format(k))
                    if isinstance(v, dict):
                        update_values.append(json.dumps(v))
                    else:
                        update_values.append(v)
                    
                if database == "hdi_engineering.incam_process_info" or database == "hdi_engineering.incam_process_info_temp":                    
                    sql = u"update {2} set {0},create_time=now() where mrpname = '{1}'"
                    conn.SQL_EXECUTE(dbc_m, sql.format(",".join(param), key, database), params=update_values)
                else:
                    sql = u"update {2} set {0},create_time=now() where ID = {1}"
                    conn.SQL_EXECUTE(dbc_m, sql.format(",".join(param), key, database), params=update_values)           
    
    def confirm_customer_work_file(self, *args):
        """检测 工程管理系统中有 客户确认工作稿时间
        时提示用户检查资料跟回传工作稿是否一致20240327 by lyh"""
        jobname = job.name
        
        if jobname.split("-")[0][-1] == "1" and jobname.split("-")[0][-2] in list("abcdefghijklmnopqrstuvwxyz"):
            pass
        else:
            return u"success厂内升级版本，无需检测。", None
        
        sql = """select psj.*
        from project_status_jobmanage psj
        WHERE job = '{0}'
        order by id desc"""
        job_process_info = conn.SELECT_DIC(dbc_p, sql.format(jobname.split("-")[0]))
        if not job_process_info:
            return u"success工程任务计划内无此型号，无需检测。", None
        
        # print(job_process_info)
        if job_process_info and job_process_info[0].get("workDataEndTime", ""):
            showMessageInfo(u"检测到客户已确认回传工作稿,确认时间:{0}，请注意比对当前资料跟客户回传的工作稿资料是否一致，请检查！".format(job_process_info[0].get("workDataEndTime", "")))
            return u"success检测到客户已确认回传工作稿，确认时间:{0}，请注意比对当前资料跟客户回传的工作稿资料是否一致！".format(job_process_info[0].get("workDataEndTime", "")), None
        
        return u"success客户未回传工作稿", None
    
    def check_customer_pn_number_new(self, *args):
        """检测客户品名"""
        dic_info = getJobData(job.name.upper())
        if not dic_info:
            ikm_fun.update_flow_report(processID, jobid=jobID, report=u"未获取到erp的客户品名，请手动查询比对！")
            showMessageInfo(u"未获取到erp的客户品名，请手动查询比对！")
            return
        
        if "panel" in matrixinfo["gCOLstep_name"]:                
            all_steps = get_panelset_sr_step(jobname, "panel")
            if not all_steps:
                all_steps = matrixinfo["gCOLstep_name"]  
        else:
            all_steps = matrixinfo["gCOLstep_name"]   
            
        user = top.getUser()
        all_steps = [name for name in all_steps
                     if "edit" in name or "set" in name]
        for stepname in all_steps + ["edit"]:
            if stepname in matrixinfo["gCOLstep_name"]:
                step = gClasses.Step(job, stepname)
                step.open()
                step.clearAll()        
            
        log = u"请按以下要求操作：<br>1.需检查资料内客户PN号跟实物板内的PN号是否一致<br>\
        <br>2.请框选中资料内的PN号，系统将把框选的内容上传到数据库，以备后续审核查看检验！！"
        res = showQuestionMessageInfo(log.format(jobname.split("-")[0]), end_btn_text=u"板内无客户PN号", end_btn_size=120)
        if not res:
            ikm_fun.update_flow_report(processID, jobid=jobID, report=u"success板内无客户PN号，无需检查。")
            return u"success板内无客户PN号，无需检查。", None
            
        job.PAUSE(u"请框选中资料内的PN号，然后continue".encode("utf8"))
        
        arraylist_sel = []
        while len(arraylist_sel) != 1:        
            for stepname in all_steps:
                step = gClasses.Step(job, stepname)
                step.open()
                if step.featureSelected():
                    arraylist_sel.append(stepname)
        
            if not arraylist_sel:
                job.PAUSE(u"未检测到框选中元素，请框选中资料内的PN号，然后continue".encode("utf8"))
                
            if len(arraylist_sel) > 1:
                log = u"检查到{0}有两个及以上的step中有物体被选中，请确认是否正确！".format(arraylist_sel)
                job.PAUSE(log.encode("utf8"))
        
        stepname = arraylist_sel[0]
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        step.COM("get_work_layer")
        worklayer = step.COMANS
        xmin, ymin, xmax, ymax = get_layer_selected_limits(step, worklayer)
        layer_cmd = gClasses.Layer(step, worklayer)
        feat_out = layer_cmd.featSelOut(units="mm")["text"]
        text = ""
        if feat_out:        
            for obj in feat_out:
                text += obj.text
                
        step.copySel("cuspn_tmp")
        step.clearAll()
        step.display("cuspn_tmp")
        if worklayer not in ["l1", "m1", "c1"] and "c1" not in worklayer:
            step.COM("sel_transform,mode=anchor,oper={0},duplicate=no,\
            x_anchor={1},y_anchor={2},angle=0,x_scale=1,\
            y_scale=1,x_offset=0,y_offset=0,direction=ccw".format("mirror", (xmin+xmax) *0.5, (ymin+ymax) *0.5))
            
        if xmax - xmin < ymax - ymin:
            log = u"检测到选中的PN号为垂直方向，请旋转调整到水平方向后继续！"
            job.PAUSE(log.encode("utf8"))
            
        step.resetFilter()
        step.selectAll()
        xmin, ymin, xmax, ymax = get_layer_selected_limits(step, "cuspn_tmp")
        
        step.COM("display_profile,display=no")
        step.COM("display_datum,display=no")
        step.selectNone()
        cmd = "disp_snapshot,file={0}.jpg,width={1},height={2},x_min={3},y_min={4},x_max={5},y_max={6}"
        step.COM(cmd.format("/tmp/cuspn_"+jobname, 800, (ymax-ymin+2) *40, xmin-1, ymin-1, xmax+1, ymax+1))
        step.removeLayer("cuspn_tmp")
        step.display(worklayer)
        step.COM("display_profile,display=yes")
        step.COM("display_datum,display=yes")
        
        tgz_pn_nubmer = self.show_message_picture_ui_compare(u"客户PN号检查", u"请确认实物板内的PN号跟上面图片内的是否一致，\n此数据将上传到数据库，请务必确认清楚。",
                        "/tmp/cuspn_"+jobname+".jpg", dic_info["cust_pn"].decode("utf8"), text.replace("'", ""))        

        sql = "select * from hdi_engineering.incam_job_operate_notes where job_name = '{0}_{1}'"
        cust_pn_info = conn.SELECT_DIC(dbc_m, sql.format(jobname.split("-")[0], user))
        if cust_pn_info:            
            sql = "delete from hdi_engineering.incam_job_operate_notes where job_name = '{0}_{1}'"
            conn.SQL_EXECUTE(dbc_m, sql.format(jobname.split("-")[0], user))
        
        fd = open("/tmp/cuspn_"+jobname+".jpg")
        image = fd.read()
        fd.close()
        
        insert_sql = "insert into hdi_engineering.incam_job_operate_notes\
        (job_name,cust_pn,cust_pn_picture,cust_pn_import_user) values (%s,%s,%s,%s)"
        cursor = dbc_m.cursor()
        cursor.execute(insert_sql, (jobname.split("-")[0]+"_"+user, tgz_pn_nubmer, image, user))
        dbc_m.commit()
        cursor.close()
        dbc_m.close()
        
        os.system("rm -rf "+"/tmp/cuspn_"+jobname+".jpg")
        ikm_fun.update_flow_report(processID, jobid=jobID, report=u"已确认")
        
    def show_message_picture_ui_compare(self, title, note_text, picture_path, erp_pn, pn_text):
        self.dialog = QtGui.QDialog()
        self.dialog.setWindowFlags(Qt.Qt.Window|Qt.Qt.WindowStaysOnTopHint)
        self.dialog.setWindowTitle(title)
        label = QtGui.QLabel()
        label2 = QtGui.QLabel()
        label2.setText(note_text)
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(15)
        label2.setFont(font)
        label2.setStyleSheet("QLabel{color:red;}")
        label3 = QtGui.QLabel(u"手动填写")
        self.line_edit = QtGui.QLineEdit(pn_text)
        self.label4 = QtGui.QLabel(u"erp上客户品名:"+erp_pn)
        self.label4.hide()
        self.label4.setFont(font)
        
        button = QtGui.QPushButton(u"比对")
        button.setFixedWidth(120)
        button1 = QtGui.QPushButton(u"退出")
        button1.setFixedWidth(120)
        png = QtGui.QPixmap(picture_path)
        label.setPixmap(png)
        layout = QtGui.QGridLayout()
        layout.addWidget(label, 0, 0, 1, 2)
        layout.addWidget(label2, 1, 0, 1, 2)
        layout.addWidget(label3, 2, 0, 1, 1)
        layout.addWidget(self.line_edit, 2, 1, 1, 1)
        layout.addWidget(self.label4, 3, 0, 1, 2)
        layout.addWidget(button, 5, 0, 1, 1)
        layout.addWidget(button1, 5, 1, 1, 1)
        self.erp_pn = erp_pn
        button.clicked.connect(self.compare_customer_pn_number)
        button1.clicked.connect(self.dialog.accept)
        self.dialog.setLayout(layout)
        self.dialog.exec_()
        
        tgz_pn_number = str(self.line_edit.text())
        
        return tgz_pn_number
    
    def compare_customer_pn_number(self):
        """比对客户品名"""
        erp_pn_number = self.erp_pn# str(self.label4.text())
        tgz_pn_number = str(self.line_edit.text())
        if tgz_pn_number == "":
            showMessageInfo(u"请先手动录入图片中的客户品名")
            return
        
        self.label4.show()
        if tgz_pn_number.lower() == erp_pn_number.lower():
            showMessageInfo(u"比对一致")
        else:
            showMessageInfo(u"比对不一致，请检查差异内容！")
        
        # self.dialog.accept()
                
    def check_customer_pn_number(self, *args):
        """check_type 为director时 审核人运行，maker 为制作人运行"""

        check_type = args[0]
        jobname = job.name
        
        if jobname.split("-")[0][-1] == "1" and jobname.split("-")[0][-2] in list("bcdefghijklmnopqrstuvwxyz"):
            pass
        else:
            return u"success非客户升级版本，无需检测。", None
        
        sql = "select * from hdi_engineering.incam_job_operate_notes where job_name = '{0}'"
        cust_pn_info = conn.SELECT_DIC(dbc_m, sql.format(jobname.split("-")[0]))
        
        sql = """select psj.*
        from project_status_jobmanage psj
        WHERE job = '{0}'
        order by id desc"""
        job_process_info = conn.SELECT_DIC(dbc_p, sql.format(jobname.split("-")[0]))
        if not job_process_info:
            return u"success工程任务计划内无此型号，无需检测。", None
            
        #已审核完的不检测
        if job_process_info and job_process_info[0].get("ocheckfinish_time", ""):
            return u"success外层资料已审核完毕，无需检测。", None
        
        user = top.getUser()
        
        #sql = """select * from pdm_job_check_user_list where person_number = '{0}'"""
        #dic_user_info = ikm_fun.PG.SELECT_DIC(ikm_fun.dbc_p, sql.format(user))
        #if not dic_user_info:
            #return u"用户{0} 未定义角色，请反馈程序工程师维护。".format(user), None
            
        #person_role = dic_user_info[0].get("person_role", "").decode("utf8")
        #if not person_role:
            #person_role = u"制作人"
            
        #if person_role in [u"管理员", u"制作人", u"审核人", u"测试员"]:
            
        if check_type == "director":
            if not cust_pn_info:
                return u"检测到此型号为升级版本，制作人未进行客户版本截图，请审核人自行比对实物客户型号跟资料内的客户型号是否一致", None
            
            # if cust_pn_info and check_type == "director":                    
                
            if cust_pn_info[0]["cam_notes"] is None or user not in cust_pn_info[0]["cam_notes"]:
                
                with open("/tmp/check_cust_pn_{0}.jpg".format(jobname), "wb") as f:
                    f.write(cust_pn_info[0]["cust_pn_picture"])
                         
                show_message_picture_ui(u"客户升级版本PN号核对",
                                        u"检测到此型号为客户升级版本，请审核确认实物板内的PN号跟上面图片内的是否一致，请务必确认清楚。",
                                        "/tmp/check_cust_pn_{0}.jpg".format(jobname))
                os.system("rm -rf "+"/tmp/check_cust_pn_{0}.jpg".format(jobname))
                
                insert_sql = "update hdi_engineering.incam_job_operate_notes\
                set cam_notes=%s where id ={0}"
                cursor = dbc_m.cursor()
                cursor.execute(insert_sql.format(cust_pn_info[0]["id"]), (u"{0}已确认".format(user)))
                dbc_m.commit()
                cursor.close()
                dbc_m.close()
                
            return u"success审核已查看比对", None
        
        if cust_pn_info:
            return u"success已检查，客户PN号图片上传成功", None
        
        if "panel" in matrixinfo["gCOLstep_name"]:                
            all_steps = get_panelset_sr_step(jobname, "panel")
        else:
            all_steps = matrixinfo["gCOLstep_name"]
            
        all_steps = [name for name in all_steps
                     if "edit" in name or "set" in name]
        for stepname in all_steps + ["edit"]:
            if stepname in matrixinfo["gCOLstep_name"]:
                step = gClasses.Step(job, stepname)
                step.open()
                step.clearAll()        
            
        log = u"检测到此型号{0}为客户升级版本，<br>请按以下要求操作：<br>1.需检查资料内客户PN号跟实物板内的PN号是否一致<br>\
        <br>2.请框选中资料内的PN号，系统将把框选的内容上传到数据库，以备后续审核查看检验！！"
        res = showQuestionMessageInfo(log.format(jobname.split("-")[0]), end_btn_text=u"无客户PN号")
        if not res:        
            return u"success板内无客户PN号，无需检查。", None
            
        # job.PAUSE(u"请框选中资料内的PN号，然后continue".encode("utf8"))
        self.pause_check_result(job, u"请框选中资料内的PN号，然后continue",args=args, delete_log_file=False)
        
        arraylist_sel = []
        while len(arraylist_sel) != 1:        
            for stepname in all_steps:
                step = gClasses.Step(job, stepname)
                step.open()
                if step.featureSelected():
                    arraylist_sel.append(stepname)
        
            if not arraylist_sel:
                # job.PAUSE(u"未检测到框选中元素，请框选中资料内的PN号，然后continue".encode("utf8"))
                self.pause_check_result(job, u"未检测到框选中元素，请框选中资料内的PN号，然后continue", args=args, delete_log_file=False)
                
            if len(arraylist_sel) > 1:
                log = u"检查到{0}有两个及以上的step中有物体被选中，请确认是否正确！".format(arraylist_sel)
                # job.PAUSE(log.encode("utf8"))
                self.pause_check_result(job, log, args=args, delete_log_file=False)
        
        stepname = arraylist_sel[0]
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        step.COM("get_work_layer")
        worklayer = step.COMANS
        xmin, ymin, xmax, ymax = get_layer_selected_limits(step, worklayer)
        layer_cmd = gClasses.Layer(step, worklayer)
        feat_out = layer_cmd.featSelOut(units="mm")["text"]
        text = ""
        if feat_out:        
            for obj in feat_out:
                text += obj.text
                
        # step.COM("zoom_area,x1={0},y1={1},x2={2},y2={3}".format(xmin, ymin, xmax, ymax))
        step.copySel("cuspn_tmp")
        step.clearAll()
        step.display("cuspn_tmp")
        if worklayer not in ["l1", "m1", "c1"] and "c1" not in worklayer:
            step.COM("sel_transform,mode=anchor,oper={0},duplicate=no,\
            x_anchor={1},y_anchor={2},angle=0,x_scale=1,\
            y_scale=1,x_offset=0,y_offset=0,direction=ccw".format("mirror", (xmin+xmax) *0.5, (ymin+ymax) *0.5))
            
        if xmax - xmin < ymax - ymin:
            log = u"检测到选中的PN号为垂直方向，请旋转调整到水平方向后继续！"
            # job.PAUSE(log.encode("utf8"))
            self.pause_check_result(job, log, args=args, delete_log_file=False)
            
        step.resetFilter()
        step.selectAll()
        xmin, ymin, xmax, ymax = get_layer_selected_limits(step, "cuspn_tmp")
        
        step.COM("display_profile,display=no")
        step.COM("display_datum,display=no")
        step.selectNone()
        cmd = "disp_snapshot,file={0}.jpg,width={1},height={2},x_min={3},y_min={4},x_max={5},y_max={6}"
        step.COM(cmd.format("/tmp/cuspn_"+jobname, 800, (ymax-ymin+2) *40, xmin-1, ymin-1, xmax+1, ymax+1))
        step.removeLayer("cuspn_tmp")
        step.display(worklayer)
        step.COM("display_profile,display=yes")
        step.COM("display_datum,display=yes")
        
        show_message_picture_ui(u"客户PN号检查", u"请确认实物板内的PN号跟上面图片内的是否一致，\n此数据将上传到数据库，请务必确认清楚。",
                        "/tmp/cuspn_"+jobname+".jpg") 
        
        if cust_pn_info:
            sql = "delete from hdi_engineering.incam_job_operate_notes where job_name = '{0}'"
            conn.SQL_EXECUTE(dbc_m, sql.format(jobname.split("-")[0]))
        
        fd = open("/tmp/cuspn_"+jobname+".jpg")
        image = fd.read()
        fd.close()
        
        insert_sql = "insert into hdi_engineering.incam_job_operate_notes\
        (job_name,cust_pn,cust_pn_picture,cust_pn_import_user) values (%s,%s,%s,%s)"
        cursor = dbc_m.cursor()
        cursor.execute(insert_sql, (jobname.split("-")[0], text, image, user))
        dbc_m.commit()
        cursor.close()
        dbc_m.close()
        
        os.system("rm -rf "+"/tmp/cuspn_"+jobname+".jpg")            
        os.system("rm -rf /tmp/check_log_{0}_*_pause.log".format(jobname))
        
        return u"success已检查，客户PN号图片上传成功", None
    
    def check_all_text_in_pcs_and_panel(self):
        """检测所有的text内是否包含型号且型号为当前版本 20230411 by lyh"""
        stepname = "panel"
        if stepname not in matrixinfo["gCOLstep_name"]:
            return u"panel不存在", None
        
        all_steps = get_panelset_sr_step(jobname, "panel")
        arraylist = []
        dic_zu_layer = {}
        for stepname in all_steps + ["panel"]:
            step = gClasses.Step(job, stepname)
            step.open()            
            
            for layer in silkscreenLayers + solderMaskLayers + outsignalLayers + innersignalLayers:
                step.clearAll()
                step.affect(layer)
            
                step.resetFilter()
                step.filter_set(feat_types='text')
                step.selectAll()
                if step.featureSelected():
                    step.removeLayer("check_jobname_tmp")
                    step.copySel("check_jobname_tmp")
                    layer_cmd = gClasses.Layer(step, "check_jobname_tmp")
                    
                    feat_out = layer_cmd.featout_dic_Index(options="feat_index")["text"]
                    # print"----->11111"
                    feat_out += layer_cmd.featout_dic_Index(options="feat_index")["barcodes"]
                    find_feat_index = []
                    for obj in feat_out:
                        # if jobname[:11] in obj.text.lower():
                        # if "-lyh" in jobname:
                            #if stepname == "set":
                                #step.PAUSE(str([obj.feat_index, obj.text]))
                            #try:
                                #print obj.x, obj.y
                                #print obj.text
                            #except:
                                #step.PAUSE(str([obj.feat_index, obj]))
                                
                        result = re.findall("({0}\w?\w?)".format(jobname[:11]), obj.text.lower()) or \
                            re.findall("([a-z]\w{3}\d{2}\w{3}\d{2}[a-z]\d)", obj.text.lower())
                        if result:
                            if result[0] not in jobname:
                                text = obj.text.lower().replace("'", "").replace('"', "")
                                log = u"检测到{0}  {1}层内有包含静态型号的text: {2} 跟当前版本{3}不一致，请检查".format(stepname, layer, text, jobname)
                                arraylist.append(log)
                                find_feat_index.append(obj.feat_index) 
                                    
                    if find_feat_index:
                        step.clearAll()
                        step.affect("check_jobname_tmp")
                        for index in find_feat_index:
                            step.selectFeatureIndex("check_jobname_tmp", index)
                            
                        if step.featureSelected():                            
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "check_jobname_tmp",
                                                                                 layer, log, dic_zu_layer, add_note_layer=layer)            
            step.clearAll()
            step.removeLayer("check_jobname_tmp")
            
        if arraylist:
            return arraylist, dic_zu_layer
        
        return "success", None        
    
    def check_set_panel_conductor_width(self):
        """折断边铜条宽度≥15 Mil  金手指板边铜皮宽度是否≥20mil"""
        arraylist = []
        dic_zu_layer = {}        
        if "set" in matrixinfo["gCOLstep_name"]:
            stepname = "set"
            step = gClasses.Step(job, stepname)
            step.open()
            
            step.clearAll()
            for layer in outsignalLayers + innersignalLayers:
                step.affect(layer)
            
            step.resetFilter()
            step.filter_set(feat_types='surface', polarity='positive')
            step.selectAll()
            
            chklist = "analysis_conductor_width"
            step.COM("chklist_from_lib,chklist={0},profile=none,customer=".format(chklist))
            step.COM("chklist_create,chklist=checklist,allow_save=no")
            step.COM("chklist_open,chklist={0}".format(chklist))
            step.COM("chklist_show,chklist={0},nact=1,pinned=no,pinned_enabled=yes".format(chklist))
            step.COM("chklist_run,chklist={0},nact=1,area=global,async_run=no".format(chklist))
            step.COM("chklist_create_lyrs,chklist={0},severity=3,suffix=conductor".format(chklist))
            step.COM("show_tab,tab=Checklists,show=no")
            step.clearAll()
            for layer in outsignalLayers + innersignalLayers:
                ms_layer = "ms_1_{0}_conductor".format(layer)
                if step.isLayer(ms_layer):
                    step.clearAll()
                    step.affect(ms_layer)
                    step.resetFilter()
                    step.setAttrFilter(".string,text=conductor_width")
                    step.refSelectFilter(layer, mode='disjoint', f_types="text")
                    if step.featureSelected():
                        log= u"检测到{0}层折断边铜条宽度不够15 Mil，请检查异常位置是否正常！".format(layer)
                        arraylist.append(log)                        
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, ms_layer,
                                                                             layer, log, dic_zu_layer,
                                                                             add_note_layer=layer, calc_legth="inch")
                        
            for layer in outsignalLayers + innersignalLayers:
                ms_layer = "ms_1_{0}_conductor".format(layer)
                step.removeLayer(ms_layer)
                
        if arraylist:
            return arraylist, dic_zu_layer
        
        return "success", None            
            
    def check_yk_layer_conditon(self):
        """出货单元内有不塞孔的钻孔时是否制作验孔资料yk（成型辅助孔除外）"""
        stepname = "set"
        if stepname not in matrixinfo["gCOLstep_name"]:
            stepname = "edit"
        
        if stepname not in matrixinfo["gCOLstep_name"]:
            return u"set 跟edit 都不存在，请检查!"
        
        step = gClasses.Step(job, stepname)
        step.open()
        
        os.environ["STEP"] = stepname
        szsk = ["szsk.lp", "szsk-c.lp", "szsk-s.lp"]
        create_lk_layer = get_luokong_area.create_luokong_layer(stepname=stepname)
        create_lk_layer.run()
        
        step.clearAll()
        
        if step.isLayer("drl"):
            step.flatten_layer("drl", "drl_tmp")
            step.clearAll()
            step.affect("drl_tmp")
            step.resetFilter()
            step.copySel("hole_tmp")
            
        if step.isLayer("2nd"):
            step.flatten_layer("2nd", "2nd_tmp")
            step.clearAll()
            step.affect("2nd_tmp")
            step.resetFilter()
            step.copySel("hole_tmp")            
            
        step.affect("hole_tmp")
        step.resetFilter()
        for reflayer in szsk:
            if step.isLayer(reflayer):
                step.flatten_layer(reflayer, reflayer+"_tmp")
                step.refSelectFilter(reflayer+"_tmp", mode="touch")
                if step.featureSelected():
                    step.selectDelete()
                
        if step.isLayer("rout_down"):
            step.clearAll()
            step.affect("hole_tmp")
            step.resetFilter()
            step.refSelectFilter("rout_down")
            if step.featureSelected():
                step.selectDelete()
        
        step.clearAll()
        step.affect("hole_tmp")
        step.resetFilter()
        step.selectAll()
        if step.featureSelected():
            if step.isLayer("yk"):
                step.selectNone()
                step.flatten_layer("yk", "yk_tmp")
                step.resetFilter()
                step.refSelectFilter("yk_tmp", mode="disjoint")
                if step.featureSelected():
                    step.removeLayer("hole_not_in_yk_+++")
                    step.copySel("hole_not_in_yk_+++")
                    
                    log = u"检测到出货单元有未塞孔钻孔未做到yk层，请到hole_not_in_yk_+++层查看是否异常！"
                    layer = "hole_not_in_yk_+++"
                    dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                          worklayer="view_layer_"+layer, 
                                                          dic_layer_list={log:[layer, "yk"], },
                                                          dic_zu_layer={})
                    step.removeLayer("hole_tmp")
                    step.removeLayer("2nd_tmp")
                    step.removeLayer("drl_tmp")
                    step.removeLayer("yk_tmp")
                    step.removeLayer("rout_down")
                    step.removeLayer("tab_area")                    
                    for layer in szsk:
                        step.removeLayer(layer+"_tmp")                      
                    return log, dic_zu_layer                    
                    
            else:
                step.removeLayer("hole_tmp")
                step.removeLayer("2nd_tmp")
                step.removeLayer("drl_tmp")
                step.removeLayer("yk_tmp")
                step.removeLayer("rout_down")
                step.removeLayer("tab_area")                
                for layer in szsk:
                    step.removeLayer(layer+"_tmp")                  
                return u"检测到出货单元有未塞孔，但资料内不存在yk层，请检查！", None
        
        step.removeLayer("hole_tmp")
        step.removeLayer("2nd_tmp")
        step.removeLayer("drl_tmp")
        step.removeLayer("yk_tmp")
        step.removeLayer("rout_down")
        step.removeLayer("tab_area")
        for layer in szsk:
            step.removeLayer(layer+"_tmp")        
        
        return "success", None
        
    def create_signal_checklist_layer(self, step, signal_layers):
        
        for lay in matrixinfo["gROWname"]:
            if "ms_1" in lay or "mk_1" in lay:
                step.removeLayer(lay)

        step.clearAll()
        for layer in signal_layers:
            if step.isLayer(layer):
                step.affect(layer)

        step.VOF()
        step.COM("chklist_delete,chklist=checklist_space")
        step.COM("chklist_cdel,chklist=checklist_space,nact=1")

        step.COM("chklist_single,action=valor_analysis_signal,show=yes")

        step.COM("""chklist_cupd,chklist=valor_analysis_signal,nact=1,
            params=((pp_layer=.affected)(pp_spacing=254)(pp_r2c=635)
            (pp_d2c=1270)(pp_sliver=254)(pp_min_pad_overlap=127)
            (pp_tests=Drill)(pp_selected=All)(pp_check_missing_pads_for_drills=Yes)
            (pp_use_compensated_rout=No)(pp_sm_spacing=No)),mode=regular""")

        step.COM("chklist_run,chklist=valor_analysis_signal,nact=1,area=profile")
        step.COM("chklist_pclear")
        step.COM("chklist_pcopy,chklist=valor_analysis_signal,nact=1")
        step.COM("chklist_close,chklist=valor_analysis_signal,mode=hide")
        step.COM("chklist_create,chklist=checklist_space")
        step.COM("chklist_ppaste,chklist=checklist_space,row=0")
        step.COM("chklist_create_lyrs,chklist=checklist_space,severity=3,suffix=ref")
        step.COM("chklist_close,chklist=checklist_space,mode=hide")
        step.COM("show_tab,tab=Checklists,show=no")
        step.VON()
        
    
    def get_min_pth_ring(self, step, drill_layer, signal_layers):
        
        ring_info = []
        d = job.matrix.getInfo()        
        
        for worklayer in signal_layers:
            step.removeLayer(worklayer+"_pth_ring")
            step.removeLayer(worklayer+"_miss_pad")
            is_continue = "no"
            step.clearAll()
            step.resetFilter()            
            for lay in d["gROWname"]:
                if "ms_1" in lay and worklayer in lay:
                    step.affect(lay)
                    is_continue = "yes"
                    
            if is_continue == "yes":                
                step.COM(
                        "filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=pth_ar")
                step.selectAll()
                step.resetFilter()
                step.COM(
                        "filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=via_ar")
                step.selectAll()
                step.resetFilter()
                step.COM(
                        "filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=slot_ar")
                step.selectAll()                
                if step.featureSelected():
                    step.copySel(worklayer+"_pth_ring")
                    step.clearAll()
                    step.affect(worklayer+"_pth_ring")
                    step.resetFilter()
    
                    step.selectNone()
                    step.resetFilter()
                    step.refSelectFilter(drill_layer)
                    if step.featureSelected():
                        layer_cmd = gClasses.Layer(step, worklayer+"_pth_ring")
                        feat_sel_out = layer_cmd.featout_dic_Index(units="mm", options="select+feat_index")["lines"]
                        ring_info += [(worklayer, obj.feat_index, obj.len) for obj in feat_sel_out
                                         if round(obj.len, 3) >= 0]

        return ring_info

    def check_pth_hole_ring(self):
        """金属钻孔对应的外层ring≥2 Mil（检测内层、次外层）
        金属钻孔对应的外层ring≥2 Mil（检测外层）
        """
        stepname = "panel"
        if stepname not in matrixinfo["gCOLstep_name"]:
            return u"panel不存在", None
        
        all_steps = get_panelset_sr_step(jobname, "panel")
        dic_zu_layer = {}
        arraylist = []
        all_steps = [name for name in all_steps
                     if "edit" in name or "set" in name or "icg" in name or "hct" in name]
        # 测试
        # all_steps = ["edit"]
        res = os.environ.get("INNER_OUTER", "inner")
        
        for stepname in all_steps:
            
            step = gClasses.Step(job, stepname)
            step.open()            
                       
            if res == "inner":
                arraylist_drill = mai_drill_layers + mai_man_drill_layers + laser_drill_layers
                signal_layers = innersignalLayers
            elif res == "outer":
                arraylist_drill = tongkongDrillLayer + ["2nd", "3nd"] + laser_drill_layers
                signal_layers = outsignalLayers
            else:
                continue
            
            self.create_signal_checklist_layer(step, signal_layers)
            #测试
            # arraylist_drill = ["b4-7"]
            # step.PAUSE("sdfsdfds")
            for drill_layer in arraylist_drill:
                if not step.isLayer(drill_layer):
                    continue
                if drill_layer in tongkongDrillLayer + ["2nd", "3nd"]:
                    signal_layers = outsignalLayers
                else:
                    signal_layers = get_drill_start_end_layers(matrixinfo, drill_layer)
                    
                info = self.get_min_pth_ring(step, drill_layer, signal_layers)
                
                
                dic_find_feat_index = {}
                for signal_layer, index, ring in info:
                    if not dic_find_feat_index.has_key(signal_layer):                        
                        dic_find_feat_index[signal_layer] = []
                        
                    if ring < 1.98 * 0.0254:
                        dic_find_feat_index[signal_layer].append(index)                        
                        
                #print info
                #print dic_find_feat_index
                for signal_layer,indexes in dic_find_feat_index.iteritems():
                    if indexes:
                        step.clearAll()
                        step.affect(signal_layer+"_pth_ring")                        
                        step.selectNone()
                        for index in indexes:                            
                            step.selectFeatureIndex(signal_layer+"_pth_ring", index)                

                        if step.featureSelected():
                            log = u"检测到{2} {0}层 对应线路{1} 的pth孔ring环小于2mil，请检查".format(drill_layer, signal_layer, stepname)
                            arraylist.append(log)                    
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, signal_layer+"_pth_ring",
                                                                         drill_layer, log, dic_zu_layer, add_note_layer=signal_layer)
                            
                for sig_layer in signalLayers:
                    if step.isLayer(sig_layer+"_miss_pad"):
                        log = u"检测到{2} {0}层 对应线路{1} 的有丢失pad，请参考{3}层进行比对检查是否异常！".format(drill_layer, signal_layer, stepname, sig_layer+"_miss_pad")
                        arraylist.append(log)
                        dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                              worklayer="view_layer_"+sig_layer, 
                                                              dic_layer_list={log:[sig_layer+"_miss_pad", drill_layer], },
                                                              dic_zu_layer=dic_zu_layer)
                        
                            
        for lay in job.matrix.getInfo()["gROWname"]:
            if "ms_1" in lay or "mk_1" in lay or "pth_ring" in lay:
                step.removeLayer(lay)
                
        new_arraylist, dic_zu_layer1 = self.check_loss_pad_for_hole(res)
        if new_arraylist == "success":
            new_arraylist = []
            dic_zu_layer1 = {}
    
        if arraylist + new_arraylist:
            return arraylist + new_arraylist, dict(dic_zu_layer, **dic_zu_layer1)
        
        return "success", None
    
    def check_modify_signal_layer_base_comp_info(self, autocheck=None):
        """检测线路 基础补偿是否正常"""
        res = os.environ.get("INNER_OUTER", None)
        
        if res == "inner":
            os.system("python /incam/server/site_data/scripts/hdi_scr/Etch/innerLayerComp/innComp_win_check.py autocheck")
            error_log = "/tmp/check_inner_compensate_error_{0}.log".format(job.name)
            success_log = "/tmp/check_inner_compensate_success_{0}.log".format(job.name)
            # check_signal_layers = innersignalLayers
        elif res == "outer":
            os.system("python /incam/server/site_data/scripts/hdi_scr/Etch/outerBaseComp/out_comp_check.py autocheck")
            error_log = "/tmp/check_outer_compensate_error_{0}.log".format(job.name)
            success_log = "/tmp/check_outer_compensate_success_{0}.log".format(job.name)
            # check_signal_layers = outsignalLayers
        
        if res is not None:            
            if os.path.exists(error_log):
                lines = file(error_log).readlines()
                os.unlink(error_log)                
                return [line.decode("cp936") for line in lines], None
            
            if os.path.exists(success_log):
                os.unlink(success_log)
            else:
                return [u"检测{0}线路基础补偿 运行异常，请手动检查！".format(res), ], None
        
        return "success", None

    # 20241106 zl
    def check_wrapped_smd_bga_comp_info(self, autocheck=None):
        """检测被包裹的bga/smd补偿是否正常"""
        stepname = "edit"
        if stepname not in matrixinfo["gCOLstep_name"]:
            return u"edit不存在", None
        arraylist = []
        # res = os.environ.get("INNER_OUTER", None)
        os.environ["STEP"] = stepname
        os.system("python /incam/server/site_data/scripts/hdi_scr/Etch/outerBaseComp/out_comp_check20241105zltest.py check_wrapped_smd_bga")
        step = gClasses.Step(job, stepname)
        step.open()
        dic_zu_layer = {}
        check_signal_layers = outsignalLayers
        for sig_layer in check_signal_layers:
            layer = '%s_result' % sig_layer
            if not step.isLayer(layer):
                log = u"检测到{0}层线路没有对应包裹的smd/bga层{1}！！".format(sig_layer, layer)
                arraylist.append(log)
            else:
                if step.isLayer(sig_layer + "_wrapped_smd_bga_compensate_error_+++"):
                    log = u"检测对应线路{0} 包裹的smd和bga有补偿不一致，请参考{1}层进行比对检查是否异常！".format(sig_layer,
                                                                                                                  sig_layer + "_wrapped_smd_bga_compensate_error_+++")
                    arraylist.append(log)
                    dic_zu_layer = self.get_view_dic_layers(job.name, stepname, step,
                                                                worklayer="view_layer_" + sig_layer,
                                                                dic_layer_list={log: [
                                                                    sig_layer + "_wrapped_smd_bga_compensate_error_+++"], },
                                                                dic_zu_layer=dic_zu_layer)
        if arraylist:
            if autocheck == "show_ui":
                showMessageInfo(*arraylist)
                self.view_note_detail(dic_zu_layer)
            return arraylist, dic_zu_layer
        return "success", None


    # 20241105 zl
    def check_isolated_smd_bga_comp_info(self, autocheck=None):
        """检测孤立bga/smd补偿是否正常"""
        stepname = "edit"
        if stepname not in matrixinfo["gCOLstep_name"]:
            return u"edit不存在", None
        arraylist = []
        if jobname[1:4] not in ["a86", "d10"]:
            return u"success非nv料号", None
        # res = os.environ.get("INNER_OUTER", None)
        os.environ["STEP"] = stepname
        os.system("python /incam/server/site_data/scripts/hdi_scr/Etch/outerBaseComp/out_comp_check20241105zltest.py check_isolated_smd_bga")
        step = gClasses.Step(job, stepname)
        step.open()
        dic_zu_layer = {}
        check_signal_layers = outsignalLayers
        for sig_layer in check_signal_layers:
                error_layer = sig_layer + "_isolated_smd_bga_compensate_error_+++"
                check_error_layer = 'check_' + sig_layer + "_isolated_smd_bga_compensate_error_+++"
                if step.isLayer(error_layer):
                    log = u"检测对应线路{0} 孤立smd和bga有补偿不一致，请参考{1}层进行比对检查是否异常！".format(sig_layer, error_layer)
                    arraylist.append(log)
                    dic_zu_layer = self.get_view_dic_layers(job.name, stepname, step,
                                                            worklayer="view_layer_" + error_layer,
                                                            dic_layer_list={log: [sig_layer],},
                                                            dic_zu_layer=dic_zu_layer)
                if step.isLayer(check_error_layer):
                    log = u"检测对应线路{0} 孤立smd和bga有多补偿0.5mil，请参考{1}层进行比对检查是否异常！".format(sig_layer, check_error_layer)
                    arraylist.append(log)
                    dic_zu_layer = self.get_view_dic_layers(job.name, stepname, step,
                                                            worklayer="view_layer_" + check_error_layer,
                                                            dic_layer_list={log: [sig_layer],},
                                                            dic_zu_layer=dic_zu_layer)
        if arraylist:
            if autocheck == "show_ui":
                showMessageInfo(*arraylist)
                self.view_note_detail(dic_zu_layer)
            return arraylist, dic_zu_layer
        return "success", None

    # 20241113 zl
    # 钻孔&线路&防焊&文字Compare layers
    def check_compare_layers(self):
        stepname = "edit"
        if stepname not in matrixinfo["gCOLstep_name"]:
            return u"edit不存在", None
        if 'orig' not in matrixinfo["gCOLstep_name"]:
            return u"orig不存在", None
        check_layers = job.matrix.returnRows('board','drill|signal|solder_mask|silk_screen')
        if not check_layers:
            return u"没有要检查的层", None
        arraylist = []
        dic_zu_layer = {}
        step = gen.Step(job, stepname)
        step.open()
        step.setUnits('inch')
        for layer in check_layers:
            map_layer = layer + "_check_compare_diff+++"
            step.removeLayer(map_layer)
            step.compareLayers(layer, jobname, 'orig', layer, map_layer=map_layer, map_layer_res=50)
            step.affect(map_layer)
            step.resetFilter()
            step.setFilterTypes('pad')
            step.setSymbolFilter('r0')
            step.selectAll()
            step.resetFilter()
            if step.Selected_count():
                log = u"{0}与orig对比检测到{1}层差异大于1mil，请参考{2}层进行比对检查是否异常！".format(stepname, layer, map_layer)
                arraylist.append(log)
                dic_zu_layer = self.get_view_dic_layers(job.name, stepname, step,
                                                        worklayer="view_layer_" + layer,
                                                        dic_layer_list={log:[map_layer], },
                                                        dic_zu_layer=dic_zu_layer)
            else:
                step.removeLayer(map_layer)
            step.unaffectAll()
        if arraylist:
            return arraylist, dic_zu_layer
        return "success", None

    # 20241129 zl 选化层孔开窗
    # 1.表面处理抓取inplan--osp+化金
    # 2.检测层别名称sgt-c/sgt-s
    # a.检测所有双面开窗的孔不区分属性 - --检测sgt-c/sgt-s层不能存在单面开窗;
    # b.大于等于1mm的pth孔属性(槽孔以槽长计算) - --检测sgt-c/sgt-s层不能不开窗;
    def check_hole_open_window(self, autocheck=None):
        get_pnl_steps = get_panelset_sr_step(jobname=job.name, panelset='panel')
        sgt_layers = []
        rows = job.matrix.rowList()
        if 'sgt-c' in rows:
            sgt_layers.append('sgt-c')
        if 'sgt-s' in rows:
            sgt_layers.append('sgt-s')
        if not sgt_layers:
            return u"没有要检查的sgt-c/sgt-s", None
        if 'drl' not in rows:
            return u"没有孔层drl", None
        arraylist = []
        dic_zu_layer = {}
        # 清理层
        step = gen.Step(job, 'panel')
        step.initStep()
        for sgt in sgt_layers:
            step.removeLayer('%s+++hole_open_window' % sgt)
            step.removeLayer('drl_%s+++hole_open_window' % sgt)
        # 表面处理
        data_info = get_face_tech_params(job.name.upper())
        for _, face_tech in data_info:
            if face_tech and u'化金+OSP' == face_tech.decode('utf-8'):
                for stepname in list(set(get_pnl_steps)) + ["panel"]:
                    step = gen.Step(job, stepname)
                    step.initStep()
                    zuanzi_attr = step.layers.get('drl').getGenesisAttr('zuanzi')
                    # 检测sgt-c/sgt-s层不能存在单面开窗
                    if len(sgt_layers) == 2:
                        for sgt in sgt_layers:
                            tmp_sgt = sgt + '+++'
                            step.removeLayer(tmp_sgt)
                            step.affect(sgt)
                            step.copySel(tmp_sgt)
                            step.unaffectAll()
                            step.affect(tmp_sgt)
                            step.Contourize(0)
                            step.unaffectAll()
                            cover_ = 'drl+++%s' % sgt
                            step.removeLayer(cover_)
                            step.createLayer(cover_)
                            step.affect('drl')
                            step.refSelectFilter(tmp_sgt, mode='cover')
                            if step.Selected_count():
                                step.copySel(cover_)
                            step.unaffectAll()
                            # 设置属性
                            if zuanzi_attr:
                                step.layers.get(cover_).setGenesisAttr('zuanzi', zuanzi_attr)
                            step.removeLayer(tmp_sgt)
                        # 两个层都cover的 没接触到的就是单面开窗
                        sgt1 = 'drl+++%s' % sgt_layers[0]
                        sgt2 = 'drl+++%s' % sgt_layers[-1]
                        sgt1_check = '%s+++hole_open_window' % sgt_layers[0]
                        sgt2_check = '%s+++hole_open_window' % sgt_layers[-1]
                        step.affect(sgt1)
                        step.refSelectFilter(sgt2, mode='disjoint')
                        if step.Selected_count():
                            step.copySel(sgt1_check)
                            log = u"检测到{0}单面开窗，请到{1}中的{2}查看位置！".format(sgt_layers[0],stepname,sgt1_check)
                            arraylist.append(log)
                            dic_zu_layer = self.get_view_dic_layers(job.name, stepname, step,
                                                                        worklayer="view_layer_" + sgt_layers[0],
                                                                        dic_layer_list={
                                                                            u"单面开窗异常层：": [sgt1_check, sgt_layers[0]], },
                                                                        dic_zu_layer=dic_zu_layer)
                        step.unaffectAll()
                        step.affect(sgt2)
                        step.refSelectFilter(sgt1, mode='disjoint')
                        if step.Selected_count():
                            step.copySel(sgt2_check)
                            log = u"检测到{0}单面开窗，请到{1}中的{2}查看位置！".format(sgt_layers[-1], stepname, sgt2_check)
                            arraylist.append(log)
                            dic_zu_layer = self.get_view_dic_layers(job.name, stepname, step,
                                                                        worklayer="view_layer_" + sgt_layers[-1],
                                                                        dic_layer_list={
                                                                            u"单面开窗异常层：": [sgt2_check, sgt_layers[-1]], },
                                                                        dic_zu_layer=dic_zu_layer)
                        step.unaffectAll()
                        step.removeLayer(sgt1)
                        step.removeLayer(sgt2)
                    # 检测大于1mm的pth孔在sgt-c/sgt-s是否有开窗
                    # 找出大于1mm的pth孔和槽孔
                    check_drl = 'drl+++hole_open_window'
                    step.removeLayer(check_drl)
                    step.affect('drl')
                    step.setFilterTypes('line|pad')
                    step.COM('set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=yes,attribute=.drill,min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=plated,text=')
                    step.COM('set_filter_and_or_logic,filter_name=popup,criteria=inc_attr,logic=or')
                    step.selectAll()
                    step.resetFilter()
                    feat_indexes = []
                    if step.Selected_count():
                        step.copySel(check_drl)
                        feat_info = step.Features_INFO(check_drl, mode='feat_index')
                        for feat in feat_info:
                            size = float(feat[4].replace('r', ''))
                            if feat[1] == '#P' and size >= 1000:
                                feat_indexes.append(int(feat[0].replace('#', '')))
                            if feat[1] == '#L':
                                x1, y1, x2, y2 = float(feat[2]), float(feat[3]), float(feat[4]), float(feat[5])
                                length = math.sqrt(math.pow((x1 - x2), 2) + math.pow((y1 - y2), 2))
                                if length > 1:
                                    feat_indexes.append(int(feat[0].replace('#', '')))
                    step.unaffectAll()
                    if feat_indexes:
                        step.affect(check_drl)
                        for index in feat_indexes:
                            step.selectByIndex(check_drl, index)
                        step.selectReverse()
                        if step.Selected_count():
                            step.selectDelete()
                        step.unaffectAll()
                        # 留下符合条件的pth孔和槽孔 去检测在sgt-c/sgt-s是否有开窗
                        for sgt in sgt_layers:
                            tmp_sgt = sgt + '+++'
                            step.affect(sgt)
                            step.copySel(tmp_sgt)
                            step.unaffectAll()
                            step.affect(tmp_sgt)
                            step.Contourize(0)
                            step.unaffectAll()
                            show_sgt = 'drl_%s+++hole_open_window' % sgt
                            step.affect(check_drl)
                            step.refSelectFilter(tmp_sgt, mode='cover')
                            step.selectReverse()
                            if step.Selected_count():
                                step.copySel(show_sgt)
                                log = u"检测到大于1mm的pth孔在{0}没有开窗，请到{1}中的{2}查看位置！".format(sgt, stepname,
                                                                                              show_sgt)
                                arraylist.append(log)
                                dic_zu_layer = self.get_view_dic_layers(job.name, stepname, step,
                                                                            worklayer="view_layer_" + sgt,
                                                                            dic_layer_list={
                                                                                u"缺少开窗异常层：": [show_sgt, sgt], },
                                                                            dic_zu_layer=dic_zu_layer)
                            step.unaffectAll()
                            step.removeLayer(tmp_sgt)
                    step.removeLayer(check_drl)
                    step.unaffectAll()
        if arraylist:
            if autocheck == "show_ui":
                showMessageInfo(*arraylist)
                self.view_note_detail(dic_zu_layer)
            return arraylist, dic_zu_layer
        return "success", None

    # 20241202 zl 外层检测增加项目 - -文字上pad检测
    def check_silk_screen(self, autocheck=None):
        """ 外层检测增加文字检测，1.遇文字上pad的报警显示位置；
                            2.文字线宽小于4mil的报警显示位置；文字对应的线路网格铜位置线宽小于6mil显示位置；
                            3.字高小于25mil的报警显示位置；文字对应的线路网格铜位置字宽小于38mil报警显示位置；
                            4.字宽小于16mil的报警显示位置"""
        get_pnl_steps = get_panelset_sr_step(jobname=job.name, panelset='panel')
        ss_layers = job.matrix.returnRows('board', 'silk_screen')
        if not ss_layers:
            return u"没有要检查的文字层", None
        arraylist = []
        dic_zu_layer = {}
        # 清理层
        panel_step = gen.Step(job, 'panel')
        panel_step.initStep()
        for ss in ss_layers:
            panel_step.removeLayer('%s+++check_silk_screen' % ss)
            panel_step.removeLayer('%s+++' % ss)
        for stepname in get_pnl_steps + ['panel']:
            step = gen.Step(job, stepname)
            step.initStep()
            for ss in ss_layers:
                show_ss = '%s+++check_silk_screen' % ss
                sm = 'm1' if ss[1] == '1' else 'm2'
                signal = outsignalLayers[0] if ss[1] == '1' else outsignalLayers[-1]
                tmp_ss = '%s+++' % ss
                tmp_sm = '%s+++' % sm
                step.affect(ss)
                step.copySel(tmp_ss)
                step.unaffectAll()
                step.affect(sm)
                step.copySel(tmp_sm)
                step.unaffectAll()
                step.affect(tmp_ss)
                step.affect(tmp_sm)
                step.selectSymbol('wzfd-*')
                step.resetFilter()
                if step.Selected_count():
                    step.selectDelete()
                step.Contourize(0)
                step.unaffectAll()
                step.affect(tmp_ss)
                # 排除.geometry=wzfd-both1
                step.COM('set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=yes,attribute=.geometry,min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=wzfd-both1')
                step.COM('set_filter_and_or_logic,filter_name=popup,criteria=inc_attr,logic=or')
                step.selectAll()
                step.resetFilter()
                if step.Selected_count():
                    step.selectDelete()
                if stepname == 'panel':
                    panel_step.COM('set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=yes,attribute=.string,min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=panel')
                step.refSelectFilter(tmp_sm)
                step.resetFilter()
                if step.Selected_count():
                    step.copySel(show_ss)
                    log = u"检测到文字层{0}在{1}有开窗，请到{2}中的{3}查看位置！".format(ss, sm, stepname, show_ss)
                    arraylist.append(log)
                    dic_zu_layer = self.get_view_dic_layers(job.name, stepname, step,
                                                            worklayer="view_layer_" + show_ss,
                                                            dic_layer_list={
                                                                u"有开窗异常层：": [show_ss, sm], },
                                                            dic_zu_layer=dic_zu_layer)
                step.unaffectAll()
                step.removeLayer(tmp_ss)
                step.removeLayer(tmp_sm)
                step.affect(ss)
                step.setFilterTypes('text')
                step.selectAll()
                step.resetFilter()
                if not step.Selected_count():
                    step.unaffectAll()
                    continue
                # 字宽 字高 线宽
                index_list1,index_list2,index_list3 = [], [], []
                layerObj = gen.Layer(step, ss)
                feat_info = layerObj.featout_dic_Index(options="select+feat_index")['text']
                for feat in feat_info:
                    # print(feat.feat_index, feat.wfactor * 12)
                    if feat.xsize * 1000 < 16:
                        index_list1.append(feat.feat_index)
                    if feat.ysize * 1000 < 25:
                        index_list2.append(feat.feat_index)
                    if feat.wfactor * 12 < 4:
                        index_list3.append(feat.feat_index)
                step.clearSel()
                if index_list1:
                    for i in index_list1:
                        step.selectByIndex(ss, i)
                    log = u"检测到字宽小于16mil,请检查{0}文字层{1}".format(stepname, ss)
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, ss, ss, log,
                                                                      dic_zu_layer)
                    step.clearSel()
                if index_list2:
                    for i in index_list2:
                        step.selectByIndex(ss, i)
                    log = u"检测到字高小于25mil,请检查{0}文字层{1}".format(stepname, ss)
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, ss, ss, log,
                                                                         dic_zu_layer)
                    step.clearSel()
                if index_list3:
                    for i in index_list3:
                        step.selectByIndex(ss, i)
                    log = u"检测到文字线宽小于4mil,请检查{0}文字层{1}".format(stepname, ss)
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, ss, ss, log,
                                                                         dic_zu_layer)
                    step.clearSel()
                step.unaffectAll()
                # 线路网格铜
                tmp_signal = signal + '+++'
                step.affect(signal)
                step.setFilterTypes('line')
                step.COM('set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=no,attribute=.pattern_fill,min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=')
                step.COM('set_filter_and_or_logic,filter_name=popup,criteria=inc_attr,logic=or')
                step.selectAll()
                step.resetFilter()
                if not step.Selected_count():
                    step.unaffectAll()
                    continue
                step.copySel(tmp_signal)
                step.unaffectAll()
                step.affect(ss)
                step.setFilterTypes('text')
                step.refSelectFilter(tmp_signal)
                step.resetFilter()
                if step.Selected_count():
                    index_list1, index_list2 = [], []
                    feat_info = layerObj.featout_dic_Index(options="select+feat_index")['text']
                    for feat in feat_info:
                        # print(feat.feat_index, feat.wfactor * 12)
                        if feat.xsize * 1000 < 38:
                            index_list1.append(feat.feat_index)
                        if feat.wfactor * 12 < 6:
                            index_list2.append(feat.feat_index)
                    step.clearSel()
                    if index_list1:
                        for i in index_list1:
                            step.selectByIndex(ss, i)
                        log = u"检测到线路网格铜位置字宽小于38mil,请检查{0}文字层{1}".format(stepname, ss)
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, ss, ss, log,
                                                                             dic_zu_layer)
                        step.clearSel()
                    if index_list2:
                        for i in index_list2:
                            step.selectByIndex(ss, i)
                        log = u"检测到线路网格铜位置线宽小于6mil,请检查{0}文字层{1}".format(stepname, ss)
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, ss, ss, log,
                                                                             dic_zu_layer)
                        step.clearSel()
                step.unaffectAll()
                step.removeLayer(tmp_signal)
                # step.PAUSE(ss)

        if arraylist:
            if autocheck == "show_ui":
                showMessageInfo(*arraylist)
                self.view_note_detail(dic_zu_layer)
            return arraylist, dic_zu_layer
        return "success", None

    # 20241204 zl 检查是否执行去细丝程序
    def check_removed_slight_section(self, autocheck=None):
        sql = """select * from pdm_job_workflow a, pdm_job b where a.process_id = 2140 and a.job_id = b.id and b.jobname = '{0}' and a.status = 'Done'"""
        data_info = ikm_fun.PG.SELECT_DIC(ikm_fun.dbc_p, sql.format(jobname.lower()))
        if not data_info:
            return u"检测到未执行panel板边去细丝程序（11.3 panel板边去除细丝）！", None
        return "success", None

    # 20241206 zl 检测未塞孔的VIA孔对应是否有钢网
    def check_steel_mesh_to_via_not_plugged(self, autocheck=None):
        p_layers = []
        rows = job.matrix.rowList()
        process_data_info = get_inplan_all_flow(job.name.upper(), select_dic=True)
        # 20241212 判断流程
        lp_process = ['HDI12302']
        array_lp_info = [dic_info for dic_info in process_data_info if dic_info["OPERATION_CODE"] in lp_process]
        lp_tools = list(
            set([x["VALUE_AS_STRING"] for x in array_lp_info if x["VALUE_AS_STRING"] and "lp" in x["VALUE_AS_STRING"]]))
        if not lp_tools:
            return u"success 没有防焊塞孔流程，无需检测该项", None
        if 'p1' in rows:
            p_layers.append('p1')
        if 'p2' in rows:
            p_layers.append('p2')
        if not p_layers:
            return u"没有钢网层p1/p2", None
        if 'drl' not in rows:
            return u"没有钻孔层drl", None
        if 'lp' not in rows:
            return u"没有lp层", None
        stepname = 'edit'
        arraylist = []
        dic_zu_layer = {}
        # 清理层
        step = gen.Step(job, stepname)
        step.initStep()
        for p in p_layers:
            tmp_drl = 'drl_check_steel_mesh_to_via_not_plugged'
            step.removeLayer(tmp_drl)
            step.affect('drl')
            step.COM('set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=yes,attribute=.drill,min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=via,text=')
            step.COM('set_filter_and_or_logic,filter_name=popup,criteria=inc_attr,logic=or')
            step.refSelectFilter('lp', mode='disjoint')
            step.resetFilter()
            if step.Selected_count():
                step.copySel(tmp_drl)
                step.unaffectAll()
                step.affect(tmp_drl)
                step.refSelectFilter(p)
                if step.Selected_count():
                    step.selectReverse()
                    if step.Selected_count():
                        step.selectDelete()
                    step.unaffectAll()
                    step.affect('drl')
                    step.refSelectFilter(tmp_drl)
                    log = u"检测到钢网层{0}对应VIA孔未塞孔，贴片会存在漏锡现象，反馈MI主管再次确认是否需要塞孔".format(p)
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, 'drl', p, log, dic_zu_layer)
                step.unaffectAll()
            step.unaffectAll()
            step.removeLayer(tmp_drl)
        if arraylist:
            if autocheck == "show_ui":
                showMessageInfo(*arraylist)
                self.view_note_detail(dic_zu_layer)
            return arraylist, dic_zu_layer
        return "success", None

    # 20241213 zl 检测文字序列号防呆
    def check_text_serial_number(self, autocheck=None):
        # 检测mi指示栏位有pcs&Set序号,cam资料未添加时报警提示
        conn = oracleConn("inmind")
        sql = u"""
       	SELECT
        j.JOB_NAME,
        i.CI_ADD_POSITION_CODE_,
        es.VALUE 
        FROM
        VGT_HDI.RPT_JOB_LIST j
        INNER JOIN VGT_HDI.RPT_JOB_INFO i ON i.ITEM_ID = j.ITEM_ID AND j.REVISION_ID = i.REVISION_ID
        LEFT JOIN ( SELECT VALUE, ENUM FROM VGT_HDI.ENUM_VALUES WHERE ENUM_TYPE = 1099 ) es ON es.ENUM = i.CI_ADD_POSITION_CODE_ where j.JOB_NAME = '{0}'"""
        data_info = conn.select_dict(sql.format(jobname.split("-")[0].upper()), is_arraysize=False)
        if not data_info:
            return  u"没有添加序号的数据", None
        data = data_info[0]
        if data['CI_ADD_POSITION_CODE_'] == '0':
            return u"success 不加序列号，不检测", None
        stepname = 'panel'
        check_layers = outsignalLayers + silkscreenLayers + solderMaskLayers
        step = gen.Step(job, stepname)
        step.initStep()
        serial_layers = []
        for check_layer in check_layers:
            step.affect(check_layer)
            step.COM('set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=yes,attribute=.string,min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=panel')
            step.selectAll()
            step.resetFilter()
            if step.Selected_count():
                serial_layers.append(check_layer)
            step.unaffectAll()
        if not serial_layers:
            return u"检测到资料未添加文字序列号", None
        else:
            return u'success 检测到%s层已添加序列号,mi指示为(%s)' % ('、'.join(serial_layers), data['VALUE'].decode('utf-8')), None

    def check_modify_signal_layer_detch_comp_info(self, autocheck=None):
        """检测修改线路后是否有漏动补 20240924"""
        userDir = os.environ.get('JOB_USER_DIR', None)
        res = os.environ.get("INNER_OUTER", None)
        if res == "inner":
            check_signal_layers = innersignalLayers
        elif res == "outer":
            check_signal_layers = outsignalLayers
        else:
            check_signal_layers = signalLayers
        
        # 计算大于2oz的内层 此层所有线都要动补 其他层控制15mil以下的
        array_cu_weight = get_cu_weight(job.name.upper(), True)
        array_mrp_info = get_inplan_mrp_info(str(job.name).upper(), condtion="1=1")
        over_2oz_inner_layers = []
        for dic_mrp_info in array_mrp_info:
            if dic_mrp_info["FROMLAY"] is None:
                continue
            layer1 = dic_mrp_info["FROMLAY"].lower()
            layer2 = dic_mrp_info["TOLAY"].lower()
            process_num = dic_mrp_info["PROCESS_NUM"]
            if process_num == 1:
                for dic_cu_info in array_cu_weight:
                    if dic_cu_info["LAYER_NAME"].lower() in [layer1, layer2]:
                        weight = dic_cu_info["CU_WEIGHT"]
                        if weight >= 1.98:
                            over_2oz_inner_layers.append(dic_cu_info["LAYER_NAME"].lower())
                            
        #此文件来自保存资料时生成
        signal_change_info_file = os.path.join(userDir, 'signal_change_log')
        dic_check_step = {}
        if os.path.exists(signal_change_info_file):
            lines = file(signal_change_info_file).readlines()            
            
            for line in lines:
                stepname = line.split("-->")[1].split(";")[0].strip()
                if not stepname:
                    continue
                
                if not dic_check_step.has_key(stepname):
                    dic_check_step[stepname] = []
                    
                for layer in signalLayers:
                    if layer in line:
                        dic_check_step[stepname].append(layer)
        
        if autocheck == "auto":
            dic_check_step["edit"] = check_signal_layers
        else:
            if not dic_check_step:
                dic_check_step["edit"] = check_signal_layers
            
        if "drl" in matrixinfo["gROWname"]:
            tong_drill = "drl"
            if "cdc" in matrixinfo["gROWname"]:
                tong_drill = "cdc"
            if "cds" in matrixinfo["gROWname"]:
                tong_drill = "cds"
        else:
            tong_drill = None
            
        arraylist = []
        dic_zu_layer = {}
        if dic_check_step:                
            for stepname, check_layers in dic_check_step.iteritems():
                # 先只检测edit
                if not re.match("^edit", stepname):
                    continue
                if stepname not in matrixinfo["gCOLstep_name"]:
                    continue
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")
                
                for worklayer in list(set(check_layers)):
                    step.removeLayer(worklayer+"_check_detch_line+++")
                    step.clearAll()
                    step.affect(worklayer)
                    step.resetFilter()
                    # step.setAttrFilter(".detch_comp")
                    step.filter_set(feat_types='surface', polarity='positive')
                    step.selectAll()
                    if step.featureSelected():
                        # 有时候动补会有一侧比线少的情况
                        step.copyToLayer(worklayer+"_surface", size=100)
                        
                    step.resetFilter()
                    step.filter_set(feat_types='line;arc', polarity='positive')
                    step.selectAll()
                    if step.featureSelected():                            
                        step.copySel(worklayer+"_check_detch_line+++")
                    else:
                        step.removeLayer(worklayer+"_surface")
                        continue
                    
                    if step.isLayer(worklayer+"_check_detch_line+++") and \
                       not step.isLayer(worklayer+"_surface"):
                        log = u"检测到层{0} 有线未做动补，请到{0}_check_detch_line+++层检查是否异常！！".format(worklayer)
                        arraylist.append(log)                            
                        dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                              worklayer="view_layer_"+worklayer, 
                                                              dic_layer_list={log:[worklayer+"_check_detch_line+++"], },
                                                              dic_zu_layer=dic_zu_layer)
                        continue
                    
                    if "net" in matrixinfo["gCOLstep_name"]:                        
                        step.copyLayer(job.name, "net", worklayer, worklayer+"_net_line")
                        step.clearAll()
                        step.affect(worklayer+"_net_line")
                        step.resetFilter()
                        step.filter_set(feat_types='line;arc', polarity='positive')
                        step.selectAll()
                        step.COM("sel_reverse")
                        if step.featureSelected():
                            step.selectDelete()
                    
                    step.clearAll()
                    step.affect(worklayer+"_check_detch_line+++")
                    step.resetFilter()
                    #删除泪滴
                    step.setAttrFilter(".tear_drop")
                    step.selectAll()
                    if step.featureSelected():
                        step.selectDelete()
                        
                    #翟鸣通知 删除铜桥
                    step.resetFilter()
                    step.setAttrFilter(".patch")
                    step.selectAll()
                    if step.featureSelected():
                        step.selectDelete()                    
                        
                    #被pad cover的删除
                    step.resetFilter()
                    step.refSelectFilter(worklayer, mode='multi_cover', f_types="pad")
                    if step.featureSelected():
                        step.selectDelete()
                        
                    #被槽孔cover 或这跟槽孔一个中心位置覆盖的
                    if tong_drill:                        
                        step.resetFilter()                    
                        step.refSelectFilter(tong_drill, mode='multi_cover')
                        if step.featureSelected():
                            step.selectDelete()
                        
                        step.refSelectFilter(tong_drill, mode='include')
                        if step.featureSelected():
                            step.selectDelete()
                        
                        if step.isLayer("tk.ykj"):
                            step.refSelectFilter(tong_drill, mode='multi_cover')
                            if step.featureSelected():
                                step.selectDelete()
                            
                            step.refSelectFilter(tong_drill, mode='include')
                            if step.featureSelected():
                                step.selectDelete()
                                
                    if worklayer not in over_2oz_inner_layers:
                        step.resetFilter()
                        layer_cmd = gClasses.Layer(step, worklayer+"_check_detch_line+++")
                        feat_out = layer_cmd.featCurrent_LayerOut(units="mm")["lines"]
                        over_15mil_line_symbol = list(set([obj.symbol for obj in feat_out
                                                           if float(obj.symbol[1:]) >= 15 * 25.4]))
                        if over_15mil_line_symbol:
                            step.selectSymbol(";".join(over_15mil_line_symbol), 1, 1)
                            if step.featureSelected():
                                step.selectDelete()
                        
                    step.resetFilter()
                    step.refSelectFilter(worklayer+"_surface", mode='multi_cover')
                    step.COM("sel_reverse")
                    if step.featureSelected():
                        if step.isLayer(worklayer+"_net_line"):
                            step.resetFilter()
                            step.selectNone()
                            step.refSelectFilter(worklayer+"_net_line", mode='disjoint')
                            if step.featureSelected():
                                step.selectDelete()
                    
                    step.selectNone()
                    step.resetFilter()
                    step.refSelectFilter(worklayer+"_surface", mode='multi_cover')
                    step.COM("sel_reverse")
                    if step.featureSelected():
                        step.COM("sel_reverse")
                        if step.featureSelected():
                            step.selectDelete()
                        
                        log = u"检测到层{0} 有线未做动补，请到{0}_check_detch_line+++层检查是否异常！！".format(worklayer)
                        arraylist.append(log)                            
                        dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                              worklayer="view_layer_"+worklayer, 
                                                              dic_layer_list={log:[worklayer+"_check_detch_line+++"], },
                                                              dic_zu_layer=dic_zu_layer)
                    else:
                        step.removeLayer(worklayer+"_check_detch_line+++")
                        
                    step.removeLayer(worklayer+"_surface")
                    step.removeLayer(worklayer+"_net_line")
                    
        if os.path.exists(signal_change_info_file):
            os.unlink(signal_change_info_file)
            
        result = self.check_modify_signal_layer_base_comp_info()
        if result[0] != "success":
            arraylist += result[0]
            
        if arraylist:
            if autocheck == "manual":
                showMessageInfo(*arraylist)
                
            return arraylist, dic_zu_layer
        else:
            if autocheck == "manual":
                showMessageInfo(u"程序运行完成，检测正常！")
        
        return "success", None
    
    def check_zk_line_cover_by_reflayer(self, *args):
        """检测工作稿阻抗线是否被屏蔽层大铜皮完全覆盖"""
        res = os.environ.get("INNER_OUTER", None)
        
        if "auto_check" in args:
            if job.name[1:4] not in ["a86", "d10"]:
                return u"success非NV型号，无需检测！", None
        
        if "edit" not in matrixinfo["gCOLstep_name"]:
            return u"edit 不存在，请检查", None
        
        if "net" not in matrixinfo["gCOLstep_name"]:
            return u"net 不存在，请检查", None
        
        arraylist_imp_info = get_inplan_imp(job.name.upper())
        
        stepname = "edit"
        step = gClasses.Step(job, "net")
        step.open()
        step.COM("units,type=inch")
        
        for layer in job.matrix.getInfo()["gROWname"]:
            if "_ref_" in layer and ("_imp_orig_line" in layer or "_imp_orig_surface" in layer):
                step.removeLayer(layer)        
        
        if res == "inner":
            signal_layers = innersignalLayers            
        elif res == "outer":
            signal_layers = outsignalLayers
        else:
            signal_layers = signalLayers
            
        #if "-lyh" in job.name:
            #signal_layers = ["l4"]
            
            
        for worklayer in signal_layers:
            dic_ref_layer = {}
            for dic_imp_info in arraylist_imp_info:
                ref_layers = dic_imp_info["REF_LAYER_"]
                if ref_layers is None:
                    ref_layers = ""
                
                ref_layers = sorted([x.lower() for x in ref_layers.split("&")], key=lambda x: int(x[1:]))
                trace_layer = dic_imp_info["TRACE_LAYER_"]
                orig_width = dic_imp_info["ORG_WIDTH"]
                if trace_layer.lower() == worklayer:
                    if dic_ref_layer.get(orig_width, None):
                        if ref_layers not in dic_ref_layer[orig_width]:                            
                            dic_ref_layer[orig_width].append(ref_layers)
                    else:
                        dic_ref_layer[orig_width] = [ref_layers]                    
            
            for orig_width, array_ref_layers in dic_ref_layer.iteritems():
                step.clearAll()
                step.affect(worklayer)
                step.resetFilter()
                step.selectSymbol("r{0}".format(orig_width), 1, 1)
                if "cam_director" in args :
                    resize = -1 * (orig_width - 0.1)
                else:
                    resize = -1*orig_width*0.5
                    
                if step.featureSelected():
                    step.removeLayer(worklayer+"_{0}".format(orig_width))
                    step.copySel(worklayer+"_{0}".format(orig_width))
                    step.copyLayer(job.name, step.name,
                                   worklayer+"_{0}".format(orig_width),
                                   worklayer+"_{0}_surface".format(orig_width))
                    step.clearAll()
                    step.affect(worklayer+"_{0}_surface".format(orig_width))
                    step.contourize(units="inch")
                    step.COM("sel_resize,size=0.5")
                    
                    step.clearAll()                    
                    for ref_layers in array_ref_layers:
                        for ref_layer in ref_layers:                            
                            step.clearAll()
                            step.affect(ref_layer)
                            step.resetFilter()
                            step.filter_set(polarity='negative')                            
                            step.selectAll()
                            if step.featureSelected():
                                step.selectNone()
                                step.copySel(worklayer+"_ref_{0}_imp_orig_surface".format(ref_layer))
                                step.clearAll()
                                step.affect(worklayer+"_ref_{0}_imp_orig_surface".format(ref_layer))
                                step.contourize(units="inch", accuracy=0)
                            else:
                                step.resetFilter()
                                step.filter_set(feat_types='surface', polarity='positive')                                
                                step.selectAll()
                                if step.featureSelected():
                                    step.copySel(worklayer+"_ref_{0}_imp_orig_surface".format(ref_layer))
                            
                    if len(array_ref_layers) == 1:                                
                        step.clearAll()
                        step.affect(worklayer+"_{0}".format(orig_width))
                        step.resetFilter()
                        for ref_layer in array_ref_layers[0]:                            
                            step.copyToLayer(worklayer+"_ref_{0}_imp_orig_line".format(ref_layer), size=resize)                        
                    else:
                        step.clearAll()                       
                        step.affect(worklayer+"_{0}".format(orig_width))
                        step.resetFilter()
                        step.changeSymbol("r0.1")
                        step.refSelectFilter(worklayer, mode='cover', f_types="pad", polarity="positive")
                        if step.featureSelected():
                            step.selectDelete()
                            
                        for ref_layers in sorted(array_ref_layers, key=lambda x: int(x[0][1:]) * -1):
                            step.clearAll()                       
                            step.affect(worklayer+"_{0}".format(orig_width))
                            step.resetFilter()
                            for ref_layer in ref_layers:
                                step.resetFilter()
                                step.refSelectFilter(worklayer+"_ref_{0}_imp_orig_surface".format(ref_layer), mode="cover")
                            
                            if step.featureSelected():
                                step.removeLayer("find_ref_line")
                                
                                step.removeLayer("find_ref_line_tmp")
                                step.moveSel("find_ref_line_tmp")
                                step.clearAll()
                                step.affect(worklayer+"_{0}_surface".format(orig_width))
                                step.resetFilter()
                                step.refSelectFilter("find_ref_line_tmp")
                                if step.featureSelected():
                                    step.removeLayer("find_ref_line_surface_tmp")
                                    step.moveSel("find_ref_line_surface_tmp")
                                    step.clearAll()
                                    step.affect(worklayer+"_{0}".format(orig_width))
                                    step.resetFilter()
                                    step.refSelectFilter("find_ref_line_surface_tmp")
                                    if step.featureSelected():
                                        step.moveSel("find_ref_line")
                                        step.clearAll()
                                        step.affect("find_ref_line")
                                        step.changeSymbol("r{0}".format(orig_width))
                                        for ref_layer in ref_layers:
                                            step.copyToLayer(worklayer+"_ref_{0}_imp_orig_line".format(ref_layer), size=resize)
                                            
                        #有未匹配到屏蔽层的线 所有屏蔽层都拷贝
                        step.clearAll()                       
                        step.affect(worklayer+"_{0}".format(orig_width))
                        step.resetFilter()
                        step.selectAll()
                        if step.featureSelected():
                            step.selectNone()
                            step.changeSymbol("r{0}".format(orig_width))
                            for ref_layers in sorted(array_ref_layers, key=lambda x: int(x[0][1:]) * -1):
                                for ref_layer in ref_layers:
                                    step.copyToLayer(worklayer+"_ref_{0}_imp_orig_line".format(ref_layer), size=resize)
            
                step.removeLayer(worklayer+"_{0}".format(orig_width))
                for layer in job.matrix.getInfo()["gROWname"]:
                    if "_surface" in layer and "_imp_orig_surface" not in layer:                        
                        step.removeLayer(layer)
                step.removeLayer("find_ref_line")
                step.removeLayer("find_ref_line_tmp")
                step.removeLayer("find_ref_line_surface_tmp")
        
        step = gClasses.Step(job, "edit")
        step.open()
        step.COM("units,type=mm")
        check_imp_layers = []
        dic_zu_layer = {}
        arraylist = []
        for layer in job.matrix.getInfo()["gROWname"]:
            if "_ref_" in layer and ("_imp_orig_line" in layer or "_imp_orig_surface" in layer):
                step.copyLayer(job.name, "net", layer, layer)                
                if "_imp_orig_line" in layer:                    
                    check_imp_layers.append(layer)
        
        for check_layer in check_imp_layers:
            orig_check_line_layer = check_layer
            orig_check_surface_layer = check_layer.replace("line", "surface")
            edit_check_line_layer = check_layer.replace("orig", "edit")
            edit_check_surface_layer = check_layer.replace("orig_line", "edit_surface")
            
            step.removeLayer(edit_check_line_layer)
            step.removeLayer(edit_check_surface_layer)
            worklayer = check_layer.split("_")[0]
            ref_layer = check_layer.split("_")[2]
            
            step.clearAll()
            step.affect(ref_layer)
            step.resetFilter()
            step.filter_set(feat_types='surface', polarity='positive')
            step.selectAll()
            if step.featureSelected():
                step.copySel(edit_check_surface_layer)
                
            step.clearAll()
            step.affect(worklayer)
            step.removeLayer("find_imp_line")
            step.resetFilter()
            step.filter_set(feat_types='line;arc', polarity='positive')
            step.setAttrFilter(".imp_line")
            step.selectAll()
            if step.featureSelected():
                step.resetFilter()
                step.setAttrFilter(".detch_comp")
                step.filter_set(feat_types='surface', polarity='positive')
                step.COM("sel_ref_feat,layers=,use=select,mode=touch,\
                pads_as=shape,f_types=line\;pad\;surface\;arc\;text,\
                polarity=positive\;negative,include_syms=,exclude_syms=")
                if step.featureSelected():
                    step.copySel("find_imp_line")
                
            else:
                if step.isLayer(orig_check_line_layer):
                    log = u"检测到{0} 参考{1}层 阻抗线未定义到属性，请自行排查此层参考屏蔽层是否异常！".format(worklayer, ref_layer)
                    arraylist.append(log)
                continue
            
            step.resetFilter()
            step.filter_set(feat_types='line;arc', polarity='positive')
            step.setAttrFilter(".imp_line")
            step.selectAll()
            if step.featureSelected():            
                step.copySel("find_imp_line")
            
            step.clearAll()
            step.affect("find_imp_line")
            step.resetFilter()
            step.filter_set(feat_types='line;arc;surface', polarity='positive')
            step.refSelectFilter(check_layer, mode="include")
            if step.featureSelected():                
                step.copySel(edit_check_line_layer)
                
            step.clearAll()           
            
            step.copyLayer(job.name, step.name, orig_check_line_layer, orig_check_line_layer+"_tmp")
            step.copyLayer(job.name, step.name, edit_check_line_layer, edit_check_line_layer+"_tmp")
            
            step.clearAll()
            step.affect(orig_check_surface_layer)
            step.copyToLayer(orig_check_line_layer+"_tmp", invert="yes")
            
            step.clearAll()
            step.affect(edit_check_surface_layer)
            step.copyToLayer(edit_check_line_layer+"_tmp", invert="yes")
            
            step.clearAll()
            step.affect(orig_check_line_layer+"_tmp")
            step.affect(edit_check_line_layer+"_tmp")
            step.contourize(accuracy=0)
            
            step.clearAll()
            step.affect(edit_check_line_layer+"_tmp")
            if "cam_director" in args or "auto_check" in args:                
                step.COM("sel_resize,size=-5")
                
            step.resetFilter()
            step.refSelectFilter(worklayer, mode="touch", f_types="pad", polarity="positive")
            if step.featureSelected():
                step.selectDelete()
                
            step.resetFilter()            
            step.refSelectFilter(orig_check_line_layer+"_tmp", mode="disjoint")
            if step.featureSelected():
                #if "-lyh" in job.name:
                    #step.PAUSE("dd")
                log = u"检测到{0} 参考{1}层 阻抗线未全部被铜皮屏蔽，请检查标识位置是否异常！".format(worklayer, ref_layer)
                arraylist.append(log)                    
                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, edit_check_line_layer+"_tmp",
                                                                     ref_layer, log, dic_zu_layer, add_note_layer=worklayer)
                #挑出对应的阻抗线 放到临时层 给到制作补铜皮使用
                # if "-lyh" in job.name:
                if "cam_maker" in args:
                    step.affect(edit_check_line_layer+"_tmp")
                    step.resetFilter()            
                    step.refSelectFilter(orig_check_line_layer+"_tmp", mode="disjoint")
                    if step.featureSelected():
                        step.copySel(edit_check_line_layer+"_find_not_cover_line_tmp")                        
                        step.clearAll()
                        step.affect(edit_check_line_layer)

                        step.copyLayer(job.name, step.name, edit_check_line_layer, edit_check_line_layer+"_find_not_cover_line")
                        step.copyLayer(job.name, step.name, edit_check_line_layer, edit_check_line_layer+"_find_not_cover_line_bak")
                        
                        step.clearAll()
                        step.affect(edit_check_line_layer+"_find_not_cover_line_bak")
                        step.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,"
                                 "area_type=rectangle,inout=inside,contour_cut=yes,margin={2},"
                                 "ref_layer={1},feat_types=line\;pad\;surface\;arc\;text".format(
                                     edit_check_line_layer+"_find_not_cover_line_bak",
                                     edit_check_line_layer+"_find_not_cover_line_tmp", 5*25.4
                                 ))
                        step.copyToLayer(edit_check_line_layer+"_find_not_cover_line", size=5, invert="yes")
                        
                        step.clearAll()
                        step.affect(edit_check_line_layer+"_find_not_cover_line")
                        step.contourize(units="mm", accuracy=0)
                        step.COM("sel_decompose,overlap=no")
                        step.addAttr(".string", attrVal='imp_cover_surface', valType='text', change_attr="yes")
                        
                        step.removeLayer(edit_check_line_layer+"_find_not_cover_line_bak")
                        step.removeLayer(edit_check_line_layer+"_find_not_cover_line_tmp")
            
            #if "-lyh" in job.name:
            ##a86*594b4 这种就不能报 暂时取消这种检测
                #step.clearAll()
                #step.affect(orig_check_line_layer+"_tmp")
                #step.resetFilter()
                #step.refSelectFilter(worklayer, mode="disjoint", f_types="pad", polarity="positive")
                #if step.featureSelected():
                    #log = u"检测到原稿中{0} 参考{1}层 阻抗线未全部被铜皮屏蔽，请检查反馈MI是否需要问客此处要被屏蔽！".format(worklayer, ref_layer)
                    #arraylist.append(log)                    
                    #dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, orig_check_line_layer+"_tmp",
                                                                         #ref_layer, log, dic_zu_layer, add_note_layer=worklayer)                    
                
        if "-lyh" not in job.name:            
            for layer in job.matrix.getInfo()["gROWname"]:
                if "_ref_" in layer and "_imp_" in layer and ("_find_not_cover_line" not in layer):                
                    step.removeLayer(layer)
                    
            step.removeLayer("find_imp_line")
                    
        if arraylist:
            if "cam_director" in args:
                showMessageInfo(*arraylist)
                self.view_note_detail(dic_zu_layer)
            
            if "cam_maker" in args:
                showMessageInfo(u"检测完成，生成的补铜皮层在后缀_find_not_cover_line 层中，<br>请参考相应的层检查后拷贝到对应的参考层！！")
                
            return arraylist, dic_zu_layer
        
        return "success", None            
            
    def create_mask_layer_condition(self, step):
        """选化金面积计算去掉 osp区域 生成临时层"""
        # step = gClasses.Step(job, step.name)
        step.COM("units,type=mm")
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
        
        for layer in ["sgt-c", "sgt-s"]:
            layer_cmd = gClasses.Layer(step, layer)
            if step.isLayer(layer) and getattr(layer_cmd.cell, "context", None) == "board":
                if step.name != "panel":   
                    step.flatten_layer(layer, layer+"_calc_expose_tmp")
                    step.flatten_layer(dic_zu[layer], dic_mask_layer[dic_zu[layer]]+"_calc_expose_tmp")
                else:
                    step.copyLayer(step.job.name, step.name, layer, layer+"_calc_expose_tmp")
                    step.copyLayer(step.job.name, step.name, dic_zu[layer], dic_mask_layer[dic_zu[layer]]+"_calc_expose_tmp")
                
                
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
    
    def re_calc_expose_area_auto(self, sig_layer):
        """重新自动计算金面积"""
        user = top.getUser()
        
        get_pnl_steps = get_panelset_sr_step(jobname=job.name, panelset='panel')
    
        for stepname in list(set(get_pnl_steps)) + ["panel"]:
            step = gClasses.Step(job, stepname)
            step.open()
            # input组 高贵 跟马文慧  吕方，安绵六，董飞他们3个负责拼版跑边，胡刚负责INPUT读入料号 不优化 20230504 by lyh
            if user not in ["70928", "50313", "68233", "72616", "72451", "69615", "system"]:
                self.create_mask_layer_condition(step)
        
        step = gClasses.Step(job, "panel")
        step.open()
        step.COM("units,type=mm")
        dic_job_info = getJobData(job.name.upper().split("-")[0])
        thickness = dic_job_info.get("out_thick", 0)
        drillLayers = []
        if step.isLayer("drl"):    
            drillLayers = ["drl"]
            if step.isLayer("cdc"):
                drillLayers = ["cdc"]
            if step.isLayer("cds"):
                drillLayers = ["cds"]
        
        sz_drills = self.get_szsk_layers_from_inplan()
        # step.PAUSE(str([sz_drills]))        
        expose_drills = []
        for drill_layer in drillLayers:
            step.flatten_layer(drill_layer, drill_layer+"_exposed_drill_tmp")
            step.clearAll()
            step.affect(drill_layer+"_exposed_drill_tmp")
            step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board"
                     .format(job.name, drill_layer+"_exposed_drill_tmp"))
            step.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=drill"
                     .format(job.name, drill_layer+"_exposed_drill_tmp"))
            for i, sz_layer in enumerate(matrixinfo["gROWname"]):
                if sz_layer in sz_drills +["sz.lp", "szsk-c.lp", "szsk-s.lp"] and\
                   matrixinfo["gROWlayer_type"][i] == "drill" and \
                   "...dq" not in sz_layer:
                    step.removeLayer(sz_layer+"_exposed_drill_tmp")
                    step.flatten_layer(sz_layer, sz_layer+"_exposed_drill_tmp")
                    step.resetFilter()
                    step.refSelectFilter(sz_layer+"_exposed_drill_tmp")
                    if step.featureSelected():
                        step.selectDelete()
            
            expose_drills.append(drill_layer+"_exposed_drill_tmp")
                
        # for sig_layer in outsignalLayers:            
        if "l1" == sig_layer:
            if step.isLayer("m1"):
                mask_layer = "m1"
            else:
                if step.isLayer("m1-1"):
                    mask_layer = "m1-1"
                    
            if step.isLayer(mask_layer+"_calc_expose_tmp"):
                mask_layer = mask_layer+"_calc_expose_tmp"
                
            mianji, percent = calcExposeArea(step, sig_layer, mask_layer, "", "", thickness*0.5, drillLayers=expose_drills)
        else:
            if step.isLayer("m2"):
                mask_layer = "m2"
            else:
                if step.isLayer("m2-1"):
                    mask_layer = "m2-1"
                    
            if step.isLayer(mask_layer+"_calc_expose_tmp"):
                mask_layer = mask_layer+"_calc_expose_tmp"
                
            mianji, percent = calcExposeArea(step, "", "",sig_layer, mask_layer,  thickness*0.5, drillLayers=expose_drills)
            
        for layer in job.matrix.getInfo()["gROWname"]:
            if "_calc_expose_tmp" in layer or "_exposed_drill_tmp" in layer:
                step.removeLayer(layer)
        
        return mianji, percent
    
    def get_szsk_layers_from_inplan(self):
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
    
    def check_panel_edge_has_add_expose_value(self, auto_check=None):
        """检测有化金流程的板边是否有加金面积symbol"""
        
        tmp_file = os.path.join(job.tmpdir, "exit_script_run_{0}".format(job.name))
        if os.path.exists(tmp_file):
            os.unlink(tmp_file)
        
        expose_area_info = get_expose_area_from_erp(job.name.upper())
        data_info = get_face_tech_params(job.name.upper())
        for _, face_tech in data_info:
            if face_tech and (u"化金" in face_tech.decode("utf8") or \
                              u"沉金" in face_tech.decode("utf8") or \
                              u"镍钯金" in face_tech.decode("utf8")):
                stepname = "panel"
                step = gClasses.Step(job, stepname)
                step.open()
                
                if not expose_area_info:
                    return u"检查到此化金板未上传金面积到ERP，请重新运行金面积计算程序！", None
                else:
                    for info in expose_area_info:
                        if info["TOP_AREA"] is  None and info["BOT_AREA"] is None:
                            return u"检查到此化金板未上传金面积到ERP，请重新运行金面积计算程序！", None
                
                step.clearAll()
                for layer in outsignalLayers:                    
                    step.affect(layer)
                    
                step.resetFilter()
                step.selectSymbol("gold_sq", 1, 1)
                if step.featureSelected():
                    step.clearAll()
                    dic_zu = {}
                    dic_layer = {}
                    auto_calc_area = {} # 系统自动计算金面积
                    for layer in outsignalLayers:
                        step.clearAll()
                        step.affect(layer)
                        step.resetFilter()
                        step.filter_set(feat_types='text')
                        step.setAttrFilter(".area_name,text=expose_area")
                        step.selectAll()
                        if layer == "l1":
                            dic_layer["TOP_AREA"] = layer.upper()
                        else:
                            dic_layer["BOT_AREA"] = layer.upper()
                        if step.featureSelected():
                            layer_cmd = gClasses.Layer(step, layer)
                            feat_out = layer_cmd.featSelOut(units="mm")["text"]
                            for obj in feat_out:
                                if layer == "l1":
                                    dic_zu["TOP_AREA"] = float(obj.text.replace("'", ""))                                    
                                else:
                                    dic_zu["BOT_AREA"] = float(obj.text.replace("'", ""))
                            
                            # if "-lyh" in job.name:
                            mianji, percent = self.re_calc_expose_area_auto(layer)
                            if layer == "l1":
                                auto_calc_area["TOP_AREA"] = float(mianji)
                            else:
                                auto_calc_area["BOT_AREA"] = float(mianji)
                                
                    
                    step.clearAll()
                    if not dic_zu:
                        return u"检查到此化金板板边没有金面积数据text，请重新运行金面积计算程序！", None
                    
                    arraylist = []
                    for info in expose_area_info:
                        for key, value in info.iteritems():
                            if key in ["TOP_AREA", "BOT_AREA"]:
                                if info[key] is not None :
                                    if dic_zu.get(key, None) is None:
                                        arraylist.append(u"检查到此化金板[{0}]层板边没有金面积数据text，请重新运行金面积计算程序！".format(dic_layer[key]))
                                        continue
                                    
                                    if abs(float(info[key]) - dic_zu[key]) > 1:
                                        log = u"检查到此化金板[{0}]层板边金面积text数据[{1}]跟erp中的数据[{2}]不一致,请检查！"
                                        arraylist.append(log.format(dic_layer[key], dic_zu[key], info[key]))
                                        
                                    # if "-lyh" in job.name:
                                    if abs(auto_calc_area[key] - dic_zu[key]) > 300:
                                        log = u"检查到此化金板[{0}]层板边金面积text数据[{1}]跟后台自动计算的[{2}]差异太大,请重新跑金面积检查是否异常！"
                                        arraylist.append(log.format(dic_layer[key], dic_zu[key], auto_calc_area[key]))                                            
                    
                    if arraylist:
                        return arraylist, None
                    
                    return "success" , None
                
                log = u"检测到此型号表面处理：{0} 需在外层制作完后 需在板边添加金面积数据，以供生产查看，板边{1}层未检测到gold_sq，请重新运行金面积计算程序。"
                if auto_check is not None:
                    showMessageInfo(log.format(face_tech.decode("utf8"), outsignalLayers))
                    with open(tmp_file, "w") as f:
                        f.write("yes")
                    sys.exit()
                
                step.clearAll()
                return log.format(face_tech.decode("utf8"), outsignalLayers), None
            
        return "success", None
    
    def check_fbk_position_and_num(self):
        """检测防爆孔的位置及数量是否ok 20231114 by lyh
        http://192.168.2.120:82/zentao/story-view-6182.html"""
        if "panel" in matrixinfo["gCOLstep_name"]:
            stepname = "panel"
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            worklayer = "drl"
            arraylist = []
            dic_zu_layer = {}
            
            if not step.isLayer(worklayer):
                worklayer = "cdc"
                if not step.isLayer(worklayer):
                    worklayer = "cds"
                    
            if not step.isLayer(worklayer):
                return u"未发现通孔层，请检查！",None
            
            step.clearAll()
            step.affect(worklayer)
            step.resetFilter()
            step.setAttrFilter(".string,text=fbk")
            step.selectAll()
            step.removeLayer("fbk_tmp")
            if step.featureSelected():
                step.copySel("fbk_tmp")                
            
            step.clearAll()
            for layer in signalLayers:
                step.affect(layer)
                step.resetFilter()
                step.selectSymbol("chris-rjpad", 1, 1)
                if step.featureSelected():
                    step.copySel("rj_tmp")
                    break
            
            if step.isLayer("rj_tmp"):
                if not step.isLayer("fbk_tmp"):
                    return u"融合板 通孔层{0}内未发现防爆孔，防爆孔属性(.string=fbk),请检查防爆孔添加是否正确！".format(worklayer),None
                
                step.clearAll()
                step.affect("rj_tmp")                
                step.changeSymbol("rect6000x20000")
                step.COM("sel_resize,size={0}".format(20*25.4))
                
                layer_cmd = gClasses.Layer(step, "rj_tmp")
                feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index")["pads"]
                step.removeLayer("rj_tmp1")
                step.createLayer("rj_tmp1")
                for obj in feat_out:
                    step.clearAll()
                    step.affect("rj_tmp1")
                    step.COM("truncate_layer,layer=rj_tmp1")
                    step.addPad(obj.x, obj.y, obj.symbol)
                    step.clearAll()
                    step.affect("fbk_tmp")
                    step.resetFilter()
                    step.refSelectFilter("rj_tmp1")
                    touch_count = step.featureSelected()
                    if touch_count < 10:
                        log = u"检测到融合块索引[{0}]上的防爆孔数量少于10颗，请检查是否异常！".format(obj.feat_index)
                        arraylist.append(log)                        
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "fbk_tmp",
                                                                     worklayer, log, dic_zu_layer, add_note_layer=worklayer)
                    step.selectNone()
                    step.refSelectFilter("rj_tmp1", mode="cover")
                    cover_count = step.featureSelected()
                    if touch_count != cover_count:
                        step.refSelectFilter("rj_tmp1")
                        step.removeLayer("fbk_tmp1")
                        step.copySel("fbk_tmp1")
                        step.clearAll()
                        step.affect("fbk_tmp1")
                        step.refSelectFilter("rj_tmp1", mode="cover")
                        if step.featureSelected():
                            step.selectDelete()
                        
                        step.selectAll()
                        if step.featureSelected():                            
                            log = u"检测到有防爆孔跟融合块中心偏移有10mil，请检查是否异常！"
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "fbk_tmp1",
                                                                         worklayer, log, dic_zu_layer, add_note_layer=worklayer)                
            step.removeLayer("fbk_tmp")
            step.removeLayer("fbk_tmp1")                
            step.removeLayer("rj_tmp")
            step.removeLayer("rj_tmp1")
            
            if arraylist:
                # showMessageInfo(*arraylist)
                return arraylist, dic_zu_layer
            
        return "success", None            
                
    def check_vcut_dw_hole(self):
        """检查 vcut定位孔 是否符合要求
        http://192.168.2.120:82/zentao/story-view-6034.html
        """
        stepname = "panel"
        arraylist_log = []
        if stepname in matrixinfo["gCOLstep_name"] and "vcut" in matrixinfo["gROWname"]:
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            drilllayer = "drl"
            if not step.isLayer(drilllayer):
                drilllayer = "cdc"
                if not step.isLayer(drilllayer):
                    drilllayer = "cds"
            
            if not step.isLayer(drilllayer):
                return u"未找到通孔drl层，请检查层命名是否正确！", None
            
            f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
            
            layer_cmd = gClasses.Layer(step, drilllayer)
            feat_out = layer_cmd.featCurrent_LayerOut(units="mm")["pads"]
            vcut_hole = [obj for obj in feat_out
                         if getattr(obj, "string", None) == "vcut_dw"
                         and obj.symbol.startswith("r")]
            drl_hole_obj = feat_out
            if not vcut_hole:
                return u"检测到资料内有vcut层，但钻带内未找到vcut定位孔，请检查vcut孔是否有.string=vcut_dw属性！", None
            
            vcut_hole_all_x = list(set([obj.x for obj in vcut_hole]))
            vcut_hole_all_y = list(set([obj.y for obj in vcut_hole]))

            for a, b in zip(sorted(vcut_hole_all_x), sorted(vcut_hole_all_x)[1:]):
                if round(abs(a-b), 1) != 100:
                    log = u"检测到X方向 有孔与孔之前间距不等于100mm，实际值{0}mm,请检查！".format(round(abs(a-b), 1))
                    if log not in arraylist_log:
                        arraylist_log.append(log)
                        
            for a, b in zip(sorted(vcut_hole_all_y), sorted(vcut_hole_all_y)[1:]):
                if round(abs(a-b), 1) != 100:
                    log = u"检测到Y方向 有孔与孔之前间距不等于100mm，实际值{0}mm,请检查！".format(round(abs(a-b), 1))
                    if log not in arraylist_log:
                        arraylist_log.append(log)                         
            
            array_data_info = get_inplan_mrp_info(job.name.upper())
            if not array_data_info:
                return u"获取inplan锣边尺寸异常，请检查型号是否正确！", None
            
            pnl_rout_layer = "pnl_rout{0}".format(len(array_data_info))
            max_pnl_rout_x = 0
            min_pnl_rout_y = 0
            if step.isLayer(pnl_rout_layer):
                pnl_rout_layer_cmd = gClasses.Layer(step, pnl_rout_layer)
                feat_out = pnl_rout_layer_cmd.featCurrent_LayerOut(units="mm")["lines"]
                if not feat_out:
                    return u"{0}层没物件，系统无法检测，请检查！".format(pnl_rout_layer), None
                rout_all_x = [obj.xe for obj in feat_out]
                rout_all_x += [obj.xs for obj in feat_out]
                rout_all_y = [obj.ye for obj in feat_out]
                rout_all_y += [obj.ys for obj in feat_out]
                min_pnl_rout_x = min(rout_all_x)
                max_pnl_rout_x = max(rout_all_x)
                min_pnl_rout_y = min(rout_all_y)
                max_pnl_rout_y = max(rout_all_y)
                
            else:
                dic_outer_info = [dic_info for dic_info in array_data_info
                                  if "-" not in dic_info["MRPNAME"]][0]
                min_pnl_rout_x = (f_xmax - dic_outer_info["PNLROUTX"] * 25.4) * 0.5
                max_pnl_rout_x = f_xmax - (f_xmax - dic_outer_info["PNLROUTX"] * 25.4) * 0.5
                min_pnl_rout_y = (f_ymax - dic_outer_info["PNLROUTY"] * 25.4) * 0.5
                max_pnl_rout_y = f_ymax - (f_ymax - dic_outer_info["PNLROUTY"] * 25.4) * 0.5
                
            if not max_pnl_rout_x or not min_pnl_rout_y:
                return u"获取最后一次锣边尺寸异常，请检查！", None
                
            layer_cmd = gClasses.Layer(step, "vcut")
            feat_out = layer_cmd.featOut(units="mm")["lines"]
            h_lines = [obj for obj in feat_out if obj.angle in [90, 270]]
            v_lines = [obj for obj in feat_out if obj.angle in [0, 180]]
            
            if h_lines:
                h_all_x = [obj.xe for obj in h_lines]
                h_all_x += [obj.xs for obj in h_lines]                
                max_vcut_line_x = max(h_all_x)
                
                if abs(max(vcut_hole_all_x) - max_vcut_line_x) < 8:
                    log = u"检测到V-CUT定位孔中心到Y方向第一刀V-CUT线小于8mm,请检查！"
                    arraylist_log.append(log)
                    
                if abs(min(vcut_hole_all_y) - min_pnl_rout_y) > 9:                
                    log = u"检测到V-CUT第一个定位孔Y方向到最后一次锣边大于9mm,请检查！"                
                    arraylist_log.append(log)                
                    
                if abs(max(vcut_hole_all_y) - max_pnl_rout_y) > 100:
                    log = u"检测到最后一个V-CUT定位孔Y方向到最后一次锣边大于100mm，请检查！"
                    arraylist_log.append(log)                    
                
            if v_lines:
                v_all_y = [obj.ye for obj in v_lines]
                v_all_y += [obj.ys for obj in v_lines]                
                min_vcut_line_y = min(v_all_y)
                
                if abs(min(vcut_hole_all_y) - min_vcut_line_y) < 8:
                    log = u"检测到V-CUT定位孔中心到X方向第一刀V-CUT线小于8mm,请检查！"
                    arraylist_log.append(log)

                if abs(max(vcut_hole_all_x) - max_pnl_rout_x) > 9:
                    log = u"检测到V-CUT第一个定位孔X方向到最后一次锣边大于9mm,请检查！"
                    arraylist_log.append(log)
                    
                if abs(min(vcut_hole_all_x) - min_pnl_rout_x) > 100:                    
                    log = u"检测到最后一个V-CUT定位孔X方向到最后一次锣边大于100mm，请检查！"
                    arraylist_log.append(log)  
                
            #检测1.0的vcut定位孔是否在vcut线的中心 20231025 by lyh
            find_hole,find_vcut_line = self.check_vcut_small_hole_info(drl_hole_obj, h_lines, v_lines)
            if find_hole:
                log = u"检测到有1.0mm的vcut定位孔不在vcut线的中心上，异常的vcut定位孔请到vcut_hole_error+++层查看对比，请检查！"
                arraylist_log.append(log)
                step.clearAll()
                step.removeLayer("vcut_hole_error+++")
                step.createLayer("vcut_hole_error+++")
                step.affect("vcut_hole_error+++")
                for obj in find_hole:
                    step.addPad(obj.x, obj.y, "r1000")
                
                step.clearAll()
                
                update_current_job_check_log(os.environ.get("CHECK_ID", "NULL"),
                                             u"forbid_or_information='{0}'".format(u"拦截"))                  
                
            if find_vcut_line:
                log = u"检测到有vcut线两端的1.0mm定位孔数量不是两个，异常的vcut线请到vcut_line_error+++层查看对比，请检查！"
                arraylist_log.append(log)
                step.clearAll()
                step.removeLayer("vcut_line_error+++")
                step.createLayer("vcut_line_error+++")
                step.affect("vcut_line_error+++")
                for obj in find_vcut_line:
                    step.addLine(obj.xe, obj.ye, obj.xs, obj.ys,obj.symbol)
                
                step.clearAll()
                
                update_current_job_check_log(os.environ.get("CHECK_ID", "NULL"),
                                             u"forbid_or_information='{0}'".format(u"拦截"))                   
                
        if arraylist_log:
            return arraylist_log, None
        
        return "success", None
    
    def check_vcut_small_hole_info(self, hole_obj, h_lines, v_lines):
        """检测1.0mmvcut 定位孔"""
        
        small_vcut_hole = [obj for obj in hole_obj
                           if getattr(obj, "string", None) == "vcut_fd"
                           and obj.symbol.startswith("r1000")]
        
        find_hole = []
        # 还有就是1.0的孔是，V-CUT线两头要加。漏了也要检测一下1条回复
        find_vcut_line = []
        if small_vcut_hole:
            for hole_obj in small_vcut_hole:
                in_vcut_line = False
                for line_obj in h_lines:
                    if abs(hole_obj.x - line_obj.xs) < 0.1:
                        in_vcut_line = True
                        break
                    
                for line_obj in v_lines:
                    if abs(hole_obj.y - line_obj.ys) < 0.1:
                        in_vcut_line = True
                        break
                
                if not in_vcut_line:
                    find_hole.append(hole_obj)
            
            for line_obj in h_lines:
                count = 0
                for hole_obj in small_vcut_hole:                    
                    if abs(hole_obj.x - line_obj.xs) < 0.1:
                        count += 1
                
                if count != 2:
                    find_vcut_line.append(line_obj)
                    
            for line_obj in v_lines:
                count = 0
                for hole_obj in small_vcut_hole:                    
                    if abs(hole_obj.y - line_obj.ys) < 0.1:
                        count += 1
                
                if count != 2:
                    find_vcut_line.append(line_obj) 
                    
        return find_hole,find_vcut_line 
    
    def check_only_skip_via_laser_target_is_right(self, auto_check=None):
        """http://192.168.2.120:82/zentao/story-view-6834.html 20240528 by lyh
        （1）只存在L1-3 Skipvia，孔有连接L2层时，钻带使用L2层内靶对位；
        （2）只存在L1-3 Skipvia，孔不连接L2层时，钻带使用L3层内靶对位；
        （3）只存在L1-3 Skipvia，孔有部分连接L2层时，部分不连接L2层时，钻带使用L2层内靶对位；
        （4）同时存在L1-3 Skipvia和L1-2镭射，统一选用L2层内靶对位。
        （5）其余存在L1-N设计时，输出提示评审。
        以上情况可归结为 改一种情况即可 就是跟中间层导通的情况 加在N-1层上  其他的情况都不变"""
        
        if "panel" in matrixinfo["gCOLstep_name"]:            
            # jobname = job.name
            stepname = "edit"
            # job = gClasses.Job(jobname)
            step = gClasses.Step(job, stepname)
            # step.open()
            step.COM("units,type=mm")
            
            pnl_step = gClasses.Step(job, "panel")
            # pnl_step.open()
            pnl_step.COM("units,type=mm")
            arraylist = []
            for drill_layer in laser_drill_layers:
                
                start_index = int(drill_layer.split("-")[0][1:])
                end_index = int(drill_layer.split("-")[1])
                step.open()
                if abs(start_index - end_index) >= 2:
                    if start_index >= lay_num * 0.5:
                        flag = -1
                    else:
                        flag = 1
                        
                    for i in range(1, 10):
                        next_drill = "s{0}-{1}".format(start_index, start_index+i*flag)
                        if next_drill in laser_drill_layers and next_drill <> drill_layer:
                            break
                    else:
                        # check_target_layer = ""
                        # arraylist_log = []
                        skip_via_change = ""
                        skip_via_change2 = "no"
                        if start_index >= lay_num * 0.5:
                            reverse_laser_drill = "s{0}-{1}".format(lay_num-start_index+1, lay_num-start_index+1+abs(start_index - end_index))
                            if reverse_laser_drill in laser_drill_layers:                                
                                for i in range(1, 10):
                                    next_drill = "s{0}-{1}".format(lay_num-start_index+1, lay_num-start_index+1+i*1)
                                    if next_drill in laser_drill_layers and next_drill <> reverse_laser_drill:
                                        skip_via_change = "no"
                                        break
                                else:
                                    #if "-lyh" in job.name:
                                        #step.PAUSE(str([drill_layer, reverse_laser_drill, lay_num-start_index+1, lay_num-start_index+1 + abs(start_index - end_index)]))                                      
                                    skip_via_change2 = self.check_only_skip_via_layer(step, reverse_laser_drill, lay_num-start_index+1, lay_num-start_index+1+abs(start_index - end_index), 1)
                        else:
                            reverse_laser_drill = "s{0}-{1}".format(lay_num-start_index+1, lay_num-start_index+1-abs(start_index - end_index))
                            if reverse_laser_drill in laser_drill_layers:                                
                                for i in range(1, 10):
                                    next_drill = "s{0}-{1}".format(lay_num-start_index+1, lay_num-start_index+1+i*-1)
                                    if next_drill in laser_drill_layers and next_drill <> reverse_laser_drill:
                                        skip_via_change = "no"
                                        break
                                else:
                                    #if "-lyh" in job.name:
                                        #step.PAUSE(str([drill_layer, reverse_laser_drill, lay_num-start_index+1, lay_num-start_index+1-abs(start_index - end_index)]))                                    
                                    skip_via_change2 = self.check_only_skip_via_layer(step, reverse_laser_drill, lay_num-start_index+1, lay_num-start_index+1-abs(start_index - end_index), -1)
                                    
                        if skip_via_change != "no":
                            if skip_via_change2 == "yes":
                                skip_via_change = "yes"
                            else:
                                skip_via_change = self.check_only_skip_via_layer(step, drill_layer, start_index, end_index, flag)
                        #if "-lyh" in job.name:
                            #step.PAUSE(str([drill_layer, reverse_laser_drill, skip_via_change, skip_via_change2]))
                        if skip_via_change == "yes":
                            check_dld_layer = "l{0}".format(end_index-flag)
                            log = u"检测到此型号有只存在{0} Skipvia，孔有连接{1}层时，钻带需使用{1}层内靶对位，<br>\
                            但panel内{1}层没有sh-ldi对应{2}层的靶标,请检查dld内靶添加是否异常！"
                        else:
                            check_dld_layer = "l{0}".format(end_index)
                            log = u"检测到此型号有只存在{0} Skipvia，孔跟中间层不导通，钻带需使用{1}层内靶对位，<br>\
                            但panel内{1}层没有sh-ldi对应{2}层的靶标,请检查dld内靶添加是否异常！"                            
                            
                        dld_layer = drill_layer.replace("s", "dld")
                        pnl_step.open()
                        pnl_step.clearAll()
                        pnl_step.affect(check_dld_layer)
                        
                        pnl_step.resetFilter()
                        pnl_step.filter_set(feat_types='pad', polarity='positive', include_syms='sh-ldi')
                        pnl_step.refSelectFilter(dld_layer)
                        if not pnl_step.featureSelected():                                
                            arraylist.append(log.format(drill_layer, check_dld_layer.upper(), dld_layer))
                        pnl_step.clearAll()
            
            step.clearAll()
            
            if arraylist:
                if auto_check is None:
                    showMessageInfo(*arraylist)                     
                else:                
                    return arraylist, None
            
        return "success" ,None
    
    def check_skip_via_center_layer_is_right(self):
        """http://192.168.2.120:82/zentao/story-view-7306.html
        11.3  内层检测增加--- 1，存在skip via中间层导通时，检测是否有套比孔小的负性PAD没有，（如有不提醒，反之提醒）
        2，存在skip via中间层存在独立的pad，检测是否删除，（如未删除，提醒请删除skip via中间层的独立pad，需mi指示）20240904 by lyh"""
        #if "-lyh" in job.name:
            #return
        
        if "panel" in matrixinfo["gCOLstep_name"]:
            
            all_steps = get_panelset_sr_step(job.name, "panel")        
                
            arraylist = []
            dic_zu_layer = {}
            check_drill_layers = []
            for drill_layer in laser_drill_layers:                
                start_index = int(drill_layer.split("-")[0][1:])
                end_index = int(drill_layer.split("-")[1])                    
                if abs(start_index - end_index) >= 2:
                    check_drill_layers.append(drill_layer)
            
            if not check_drill_layers:
                return "success", None
            
            for stepname in all_steps:
                step = gClasses.Step(job, stepname)
                step.COM("units,type=mm")                    
                step.open()
                for drill_layer in check_drill_layers:
                    start_index = int(drill_layer.split("-")[0][1:])
                    end_index = int(drill_layer.split("-")[1])
                    if start_index >= lay_num * 0.5:
                        flag = -1
                    else:
                        flag = 1
                        
                    res = self.check_skip_via_layer_by_copper_cover(step, drill_layer, start_index, end_index, flag)
                    if res[0] == "yes":
                        log = u"检测到skip via镭射{0} 在{1} {2}层线路内，被铜皮覆盖，请检查标记处位置是否异常！".format(
                            drill_layer, step.name, res[1]
                        )
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, drill_layer,
                                                                             res[1], log, dic_zu_layer)
                    else:
                        if "-lyh" in job.name:                            
                            res = self.check_skip_via_layer_by_copper_negative(step, drill_layer, start_index, end_index, flag)
                            if res[0] == "yes":
                                log = u"检测到skip via镭射{0} 在{1} {2}层线路内，负片尺寸大小异常，请检查标记处位置是否按孔径*0.7-1来设计！".format(
                                    drill_layer, step.name, res[1]
                                )
                                arraylist.append(log)
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, drill_layer+"_tmp",
                                                                                     res[1], log, dic_zu_layer)
                                step.removeLayer(drill_layer+"_tmp")     
                        
                    res = self.check_skipvia_isolatepad_info(step, drill_layer, start_index, end_index, flag)
                    if res[0] == "yes":
                        log = u"检测到skip via镭射{0} 在{1} {2}层线路层有独立pad，请确认是否删除，同时删除skip via中间层的独立pad，需mi指示！".format(
                            drill_layer, step.name, res[1]
                        )
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, res[2],
                                                                             [res[1], drill_layer], log, dic_zu_layer,
                                                                             add_note_layer=res[1])
                        step.removeLayer(res[2])                        
                        
            if arraylist:
                if "-lyh" in job.name:
                    showMessageInfo(*arraylist)
                    self.view_note_detail(dic_zu_layer)
                    
                return arraylist, dic_zu_layer
                        
        return "success", None
                
    def check_skip_via_layer_by_copper_cover(self, step, drill_layer, start_index, end_index, flag):
        skip_via_cover = "no"
        for index in range(start_index+1*flag, end_index, flag):
            sig_layer = "l{0}".format(index)
            step.removeLayer(sig_layer+"_tmp")
            step.copyLayer(job.name, step.name, sig_layer, sig_layer+"_tmp")
            step.clearAll()
            step.affect(sig_layer+"_tmp")  
            step.contourize()
            
            step.clearAll()
            step.resetFilter()
            step.affect(drill_layer)                  
            step.refSelectFilter(sig_layer+"_tmp", mode="cover")
            if step.featureSelected():
                step.removeLayer(sig_layer+"_tmp")
                skip_via_cover = "yes"
                return skip_via_cover, sig_layer
            
            step.removeLayer(sig_layer+"_tmp")
            
        return skip_via_cover, None
    
    def check_skip_via_layer_by_copper_negative(self, step, drill_layer, start_index, end_index, flag):
        """检测skipvia负片大小是否正确 孔径*0.7-1"""
        skip_via_cover = "no"
        step = gClasses.Step(job, step.name)
        step.removeLayer(drill_layer+"_tmp")
        step.createLayer(drill_layer+"_tmp")
        layer_cmd = gClasses.Layer(step, drill_layer)
        feat_out = layer_cmd.featCurrent_LayerOut()["pads"]
        step.clearAll()
        step.affect(drill_layer+"_tmp")
        for obj in feat_out:
            step.addPad(obj.x, obj.y, "r{0}".format(float(obj.symbol[1:]*0.7-1)))
            
        for index in range(start_index+1*flag, end_index, flag):
            sig_layer = "l{0}".format(index)
            step.removeLayer(sig_layer+"_tmp")
            step.copyLayer(job.name, step.name, sig_layer, sig_layer+"_tmp")
            step.clearAll()
            step.affect(sig_layer+"_tmp")
            step.contourize()
            
            step.clearAll()
            step.resetFilter()
            step.affect(drill_layer+"_tmp")
            step.COM("sel_resize,size=-0.01")
            step.refSelectFilter(sig_layer+"_tmp", mode="touch")
            if not step.featureSelected():
                step.COM("sel_resize,size=0.02")
                step.refSelectFilter(sig_layer+"_tmp", mode="disjoint")
                
            if step.featureSelected():
                step.removeLayer(sig_layer+"_tmp")
                skip_via_cover = "yes"
                return skip_via_cover, sig_layer
            
            step.removeLayer(sig_layer+"_tmp")
            
        return skip_via_cover, None    
    
    def check_skipvia_isolatepad_info(self, step, drill_layer, start_index, end_index, flag):
        """检测skipvia独立pad是否存在"""

        for index in range(start_index+1*flag, end_index, flag):
            sig_layer = "l{0}".format(index)
            step.clearAll()
            step.affect(sig_layer)
            
            step.VOF()
            step.COM("chklist_delete,chklist=checklist_space")
            step.COM("chklist_cdel,chklist=checklist_space,nact=1")    
            step.COM("chklist_single,action=valor_dfm_nfpr,show=yes")
            step.COM("chklist_cupd,chklist=valor_dfm_nfpr,nact=1,"
                     "params=((pp_layer=.affected)(pp_delete=Isolated)"
                     "(pp_work=Features)(pp_drill=PTH\;Via\;Via - Laser)"
                     "(pp_non_drilled=Yes)(pp_in_selected=All)"
                     "(pp_remove_mark=Mark)),mode=regular")
    
            step.COM("chklist_run,chklist=valor_dfm_nfpr,nact=1,area=profile")
            step.COM("chklist_pclear")
            step.COM("chklist_pcopy,chklist=valor_dfm_nfpr,nact=1")
            step.COM("chklist_close,chklist=valor_dfm_nfpr,mode=hide")
            step.COM("chklist_create,chklist=checklist_space")
            step.COM("chklist_ppaste,chklist=checklist_space,row=0")
            step.COM("chklist_create_lyrs,chklist=checklist_space,severity=3,suffix=isolated")
            step.COM("chklist_close,chklist=checklist_space,mode=hide")
            step.COM("show_tab,tab=Checklists,show=no")
            step.VON()            
            
            ms_layer = "ms_1_{0}_isolated".format(sig_layer)
            if step.isLayer(ms_layer):
                step.clearAll()
                step.affect(ms_layer)
                step.resetFilter()
                step.setAttrFilter(".string,text=isolated")
                step.refSelectFilter(drill_layer)
                if step.featureSelected():                    
                    return "yes", sig_layer, ms_layer
            
        return "no", None, None

    def check_d_coupon_skipvia_type(self):
        """检测d_coupon的是否为skipvia"""
        d_coupon_steps = [name for name in matrixinfo["gCOLstep_name"]
                          if "d-coupon" in name or "d_coupon" in name]
        if not d_coupon_steps:
            return u"success 未发现d-coupon，无需检测", None
        
        stepname = "edit"        
        if stepname in matrixinfo["gCOLstep_name"]:            
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            
            dic_edit_skip_via = {}
            for drill_layer in laser_drill_layers:
                
                start_index = int(drill_layer.split("-")[0][1:])
                end_index = int(drill_layer.split("-")[1])            
                if abs(start_index - end_index) >= 2:
                    if start_index >= lay_num * 0.5:
                        flag = -1
                    else:
                        flag = 1
                        
                    skip_via_type = self.check_only_skip_via_layer(step, drill_layer, start_index, end_index, flag)
                    dic_edit_skip_via[drill_layer] = skip_via_type
                    
            for stepname in set(d_coupon_steps):
                step = gClasses.Step(job, stepname)
                step.COM("units,type=mm")
                step.open()
                
                for drill_layer in laser_drill_layers:                
                    start_index = int(drill_layer.split("-")[0][1:])
                    end_index = int(drill_layer.split("-")[1])            
                    if abs(start_index - end_index) >= 2:
                        if start_index >= lay_num * 0.5:
                            flag = -1
                        else:
                            flag = 1                        
                        skip_via_type = self.check_only_skip_via_layer(step, drill_layer, start_index, end_index, flag)
                        
                        if skip_via_type != dic_edit_skip_via[drill_layer]:
                            if skip_via_type == "no":
                                return u"检测到{0} 内{1}镭射对应的中间层被掏空，而edit内是有铜的，请检查是否异常！", None
                            else:
                                return u"检测到{0} 内{1}镭射对应的中间层有铜，而edit内是被掏空的，请检查是否异常！", None
                        
        return "success", None
    
    def check_only_skip_via_layer(self, step, drill_layer, start_index, end_index, flag):
        skip_via_change2 = "no"
        for index in range(start_index+1*flag, end_index, flag):
            sig_layer = "l{0}".format(index)
            step.removeLayer(sig_layer+"_tmp")
            step.copyLayer(job.name, step.name, sig_layer, sig_layer+"_tmp")
            step.clearAll()
            step.affect(sig_layer+"_tmp")
            step.contourize()
            # arraylist_log.append([sig_layer, drill_layer])
            step.refSelectFilter(drill_layer)
            if step.featureSelected():
                step.removeLayer(sig_layer+"_tmp")
                skip_via_change2 = "yes"
                break
            step.removeLayer(sig_layer+"_tmp")
            
        return skip_via_change2
    
    def check_bga_smd_compensate_on_surface(self, auto_check=None):
        """检测铜面smd bga补偿及开窗是否一致
        http://192.168.2.120:82/zentao/story-view-6042.html
        """
        arraylist = []
        dic_zu_layer = {}
        
        dic_zu_mask_layer = {}
        dic_zu_mask_layer["l1"] = "m1"
        if "m1" not in solderMaskLayers:
            if "m1-1" in solderMaskLayers:
                dic_zu_mask_layer["l1"] = "m1-1"
        dic_zu_mask_layer[outsignalLayers[-1]] = "m2"
        if "m2" not in solderMaskLayers:
            if "m2-1" in solderMaskLayers:
                dic_zu_mask_layer[outsignalLayers[-1]] = "m2-1"        
        
        #伍青通知 灯板检测会卡死 顾灯板无需检测20231114 by lyh
        # 伍青通知 审核还是要运行 前台有传参 director 为审核运行 20231115 by lyh
        if auto_check != "director":            
            led_type = get_led_board(job.name.upper())
            if led_type:
                return u"success灯板无需检测", None
        
        #step = gClasses.Step(job, "edit")
        #for layer in job.matrix.getInfo()["gROWname"]:
            #if "ms_1_" in layer or "mk_1_" in layer or \
               #"_check_smd_on_surface" in layer or \
               #"orig_tmp" in layer or \
               #"ar_ring" in layer or \
               #"_tmp1" in layer or \
               #"_tmp2" in layer:                            
                #step.removeLayer(layer)        
        
        for stepname in matrixinfo["gCOLstep_name"]:
            if "edit" in stepname and "coupon" not in stepname:
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")                
                for worklayer in outsignalLayers:
                    find_on_surface_bga_smd = False
                    step.clearAll()
                    step.removeLayer(worklayer+"_tmp")
                    step.copyLayer(job.name, stepname, worklayer, worklayer+"_tmp")
                    step.affect(worklayer+"_tmp")
                    step.resetFilter()
                    step.setAttrFilter(".bga")
                    step.selectAll()
                    step.resetFilter()
                    step.setAttrFilter(".smd")
                    step.selectAll()
                    if step.featureSelected():
                        step.removeLayer(worklayer+"_smd_bga")
                        step.moveSel(worklayer+"_smd_bga")
                        step.contourize()
                        step.clearAll()
                        step.resetFilter()
                        step.affect(worklayer+"_smd_bga")
                        step.refSelectFilter(worklayer+"_tmp", mode="cover")
                        step.COM("sel_reverse")
                        if step.featureSelected():
                            step.selectDelete()
                        
                        step.selectAll()
                        if step.featureSelected():
                            #if worklayer == "l1":
                                #ins_layer = "l1"
                            #else:
                                #ins_layer = "m2"
                            # if not step.isLayer(worklayer+"_check_smd_on_surface"):
                                # step.removeLayer(worklayer+"_check_smd_on_surface")
                                # step.createLayer(worklayer+"_check_smd_on_surface")
                            
                            step.copySel(worklayer+"_check_smd_on_surface1")
                            
                            layer_cmd = gClasses.Layer(step, worklayer+"_check_smd_on_surface1")
                            feat_out = layer_cmd.featCurrent_LayerOut(units="mm")["pads"]
                            # orig_smd_symbols = list(set([getattr(obj, "orig_size_mm", "null") for obj in feat_out]))
                            
                            # all_symbols = [obj.symbol for obj in feat_out]
                            
                            #orig_name = ""
                            #if "net" in matrixinfo["gCOLstep_name"]:
                                #orig_name = "net"
                            #else:
                                #if "orig" in matrixinfo["gCOLstep_name"]:
                                    #orig_name = "orig"
                            step.removeLayer(worklayer+"_check_smd_on_surface")
                            step.createLayer(worklayer+"_check_smd_on_surface")
                            # step.COM("truncate_layer,layer={0}".format(worklayer+"_check_smd_on_surface"))
                            find_on_surface_bga_smd = True
                            step.clearAll()
                            step.affect(worklayer+"_check_smd_on_surface")
                            for obj in feat_out:
                                # solder_defined阻焊定义PAD，也是阻焊PAD+2mil，这个如果检测不了，就不运行阻焊定义PAD
                                if getattr(obj, "orig_size_mm", None) and getattr(obj, "solder_defined", None) is None:
                                    step.VOF()
                                    step.addPad(obj.x, obj.y, obj.orig_size_mm, angle=obj.rotation)
                                    step.VON()
                                    
                            #if orig_name:
                                #step.copyLayer(job.name, orig_name, worklayer, worklayer+"_orig_tmp")
                                #step.clearAll()
                                #step.affect(worklayer+"_orig_tmp")
                                #step.resetFilter()
                                #step.selectSymbol(";".join(orig_smd_symbols), 1, 1)
                                #if step.featureSelected():
                                    #step.copySel(worklayer+"_check_smd_on_surface")
                                    
                                    #step.clearAll()
                                    #step.affect(worklayer+"_check_smd_on_surface")
                                    #step.resetFilter()
                                    #step.refSelectFilter(worklayer+"_smd_bga", mode='cover')
                                    #step.COM("sel_reverse")
                                    #if step.featureSelected():
                                        #step.selectDelete()
                                        
                                    #step.selectAll()
                                    #if step.featureSelected():
                                        #find_on_surface_bga_smd = True
                                    
                        step.removeLayer(worklayer+"_smd_bga")                            
                        step.removeLayer(worklayer+"_tmp")
                        step.removeLayer(worklayer+"_open")
                        step.removeLayer(worklayer+"_open+++")
                        
                    if find_on_surface_bga_smd:                      
                        step.copyLayer(jobname, stepname, dic_zu_mask_layer[worklayer], dic_zu_mask_layer[worklayer]+"_tmp1")
                        step.copyLayer(jobname, stepname, dic_zu_mask_layer[worklayer], dic_zu_mask_layer[worklayer]+"_tmp2")
                        step.clearAll()
                        step.affect(dic_zu_mask_layer[worklayer]+"_tmp1")
                        step.contourize(accuracy=0)
                        
                        step.clearAll()
                        step.affect(dic_zu_mask_layer[worklayer]+"_tmp2")
                        step.resetFilter()
                        step.filter_set(polarity='negative')
                        step.selectAll()
                        if step.featureSelected():
                            step.selectDelete()
                        
                        step.clearAll()
                        step.affect(worklayer+"_check_smd_on_surface")
                        
                        step.copySel(worklayer+"_check_smd_on_surface2")
                        
                        step.resetFilter()
                        step.COM("sel_resize,size={0}".format(2*25.4-5))# 2mil减去5um
                        step.refSelectFilter(dic_zu_mask_layer[worklayer]+"_tmp2", mode="cover")
                        if step.featureSelected():
                            step.moveSel(worklayer+"_find_error_smd")
                            step.clearAll()
                            step.affect(worklayer+"_find_error_smd")
                            step.COM("sel_resize,size=10")# 加大10um                            
                            step.refSelectFilter(dic_zu_mask_layer[worklayer]+"_tmp2", mode="include")
                            if step.featureSelected():
                                # 正常补偿2mil的
                                step.selectDelete()
                                
                            step.resetFilter()
                            step.selectAll()
                            if step.featureSelected():
                                step.selectNone()
                                step.refSelectFilter(dic_zu_mask_layer[worklayer]+"_tmp1", mode="include")
                                if step.featureSelected():
                                    step.moveSel(worklayer+"_find_error_smd_tmp")
                                    step.clearAll()
                                    step.affect(worklayer+"_find_error_smd_tmp")
                                    step.COM("sel_resize,size=-10")# 减去10um
                                    step.refSelectFilter(dic_zu_mask_layer[worklayer]+"_tmp1", mode="cover")
                                    if step.featureSelected():
                                        # 正常补偿2mil的
                                        step.selectDelete()

                                    step.copySel(worklayer+"_find_error_smd")
                            
                            step.clearAll()
                            step.affect(worklayer+"_find_error_smd")                         
                                        
                        step.clearAll()
                        step.affect(worklayer+"_check_smd_on_surface")
                        step.resetFilter()
                        step.selectAll()
                        if step.featureSelected():                            
                            step.copySel(worklayer+"_find_error_smd")                            
                        
                        if step.isLayer(worklayer+"_find_error_smd"):
                            step.clearAll()
                            step.affect(worklayer+"_check_smd_on_surface2")
                            step.resetFilter()
                            step.refSelectFilter(worklayer+"_find_error_smd")
                            if step.featureSelected():
                                step.copyToLayer(worklayer+"_compensate_not_2mil", size=2*25.4)
                                
                                step.clearAll()
                                step.affect(worklayer+"_compensate_not_2mil")
                                step.resetFilter()
                                step.selectAll()
                                if step.featureSelected():                                
                                    log = u"检测到{0} {1}层铜面smd、bga补偿不是2mil，请对比原稿smd备份层{2}，请检查！".format(stepname, worklayer, worklayer+"_compensate_not_2mil")
                                    arraylist.append(log)                                               
                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, worklayer+"_compensate_not_2mil",
                                                                                         [dic_zu_mask_layer[worklayer], worklayer+"_compensate_not_2mil"],
                                                                                         log, dic_zu_layer, add_note_layer=dic_zu_mask_layer[worklayer])
                                
                #if find_on_surface_bga_smd:
                    #chklist = "smc"
                    #step.COM("chklist_from_lib,chklist={0},profile=none,customer=".format(chklist))
                    #step.COM("chklist_create,chklist=checklist,allow_save=no")
                    #step.COM("chklist_open,chklist={0}".format(chklist))
                    #step.COM("chklist_show,chklist={0},nact=1,pinned=no,pinned_enabled=yes".format(chklist))
                    #step.COM("chklist_cupd,chklist=smc,nact=1,params=((pp_layers=.type=solder_mask&context=board&side=top|bottom|none&pol=positive)"
                             #"(pp_ar=254)(pp_coverage=254)(pp_sm2r=254)(pp_sliver=203.2)(pp_spacing=6)(pp_bridge=152.4)(pp_min_clear_overlap=127)"
                             #"(pp_sm2dam=0)(pp_tests=Pads)(pp_selected=All)(pp_use_compensated_rout=No)),mode=regular")
                    #step.COM("chklist_run,chklist={0},nact=1,area=global,async_run=no".format(chklist))
                    #step.COM("chklist_create_lyrs,chklist={0},severity=3,suffix=mask_open".format(chklist))
                    #step.COM("show_tab,tab=Checklists,show=no")
                    #step.clearAll()
                    #dic_zu_mask_layer = {}
                    #dic_zu_mask_layer["m1"] = "l1"
                    #dic_zu_mask_layer["m2"] = outsignalLayers[-1]
                    #for masklayer in ["m1", "m2"]:
                        #ms_layer = "ms_1_{0}_mask_open".format(masklayer)
                        #if step.isLayer(ms_layer):
                            #step.clearAll()
                            #step.affect(ms_layer)
                            #step.resetFilter()
                            #step.filter_set(feat_types='line')
                            #step.setAttrFilter(".string,text=ar_smd")
                            #step.selectAll()
                            #step.resetFilter()
                            #step.setAttrFilter(".string,text=ar_bga")
                            #step.selectAll()
                            #if step.featureSelected():
                                #step.copySel(masklayer+"_ar_ring")
                                #layer_cmd = gClasses.Layer(step, masklayer+"_ar_ring")
                                #feat_out = layer_cmd.featout_dic_Index(units="inch", options="feat_index")["lines"]
                                #find_obj = [obj for obj in feat_out if abs(obj.len*1000 - 1) > 0.05 ]
                                ## step.PAUSE(str(set([obj.len for obj in feat_out])))
                                #if find_obj:
                                    #step.clearAll()
                                    #step.affect(masklayer+"_ar_ring")
                                    #step.resetFilter()
                                    #for obj in find_obj:                                        
                                        #step.selectFeatureIndex(masklayer+"_ar_ring", obj.feat_index)
                                    
                                    #step.COM("sel_reverse")
                                    #if step.featureSelected():
                                        #step.selectDelete()
                                    
                                    #step.clearAll()
                                    
                                    ## for worklayer in outsignalLayers:
                                        
                                    #sig_layer = dic_zu_mask_layer[masklayer] + "_check_smd_on_surface"
                                    ##if masklayer == "m1":
                                        ##if worklayer == "l1":
                                            ##sig_layer = worklayer + "_check_smd_on_surface"
                                        ##else:
                                            ##continue
                                    ##else:
                                        ##if worklayer == "l1":
                                            ##continue
                                        ##else:
                                            ##sig_layer = worklayer + "_check_smd_on_surface"                                            
                                    #worklayer = dic_zu_mask_layer[masklayer]
                                    #step.clearAll()
                                    #step.affect(sig_layer)
                                    #step.resetFilter()
                                    #step.resetAttr()
                                    #step.refSelectFilter(masklayer+"_ar_ring")
                                    #if step.featureSelected():
                                        #step.copySel(worklayer+"_compensate_not_2mil")
                                        #log = u"检测到{0} {1}层铜面smd、bga补偿不是2mil，请对比原稿smd备份层{2}，及note标记value值为单边开窗大小！".format(stepname, worklayer, worklayer+"_compensate_not_2mil")
                                        #arraylist.append(log)
                                        #step.clearAll()
                                        #step.affect(masklayer+"_ar_ring")
                                        #step.resetFilter()
                                        #step.selectAll()                                            
                                        #dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, masklayer+"_ar_ring",
                                                                                     #[masklayer, worklayer+"_compensate_not_2mil"],
                                                                                     # log, dic_zu_layer, add_note_layer=masklayer, calc_legth="inch")
                if "-lyh" not in job.name:                    
                    for layer in job.matrix.getInfo()["gROWname"]:
                        if "ms_1_" in layer or "mk_1_" in layer or \
                           "_check_smd_on_surface" in layer or \
                           "_check_smd_on_surface1" in layer or \
                           "_check_smd_on_surface2" in layer or \
                           "_compensate_not_2mil_tmp" in layer or \
                           "_find_error_smd" in layer or \
                           "orig_tmp" in layer or \
                           "ar_ring" in layer or \
                           "_tmp1" in layer or \
                           "_tmp2" in layer:                            
                            step.removeLayer(layer)
                        
        if arraylist:
            if auto_check is None:
                showMessageInfo(*arraylist)
                self.view_note_detail(dic_zu_layer)  
            else:
                return arraylist, dic_zu_layer
        
        return "success", None
    
    def create_calc_inplan_sr_panel(self, array_data_info, pnl_x, pnl_y):
        """创建inplan拼版获取实际sr大小 来计算双面板的留边"""
        stepname = "inplan_pnl"
        if stepname in matrixinfo["gCOLstep_name"]:
            job.removeStep(stepname)
        job.addStep(stepname)
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=inch")
        step.COM('profile_rect, x1=0, y1=0, x2=%s, y2=%s' % (pnl_x, pnl_y))
        step.COM("set_step,name={0}".format(stepname))
        step.COM("set_subsystem,name=Panel-Design")
        index = 1
        for line in array_data_info:
            step_name = line['OP_STEP'].lower()
            step_reg = re.compile('edit|set')
            if step_reg.match(step_name):
                
                p = {}
                p['ang'] = line['ROTATION_ANGLE']
                p['dx'] = line['DELTA_X']
                p['dy'] = line['DELTA_Y']
                p['point_x'] = line['START_X']
                p['point_y'] = line['START_Y']
                p['nx'] = line['X_NUM']
                p['ny'] = line['Y_NUM']
                
                step.COM('sr_tab_add,line=%s,step=%s,x=0,y=0,nx=1,ny=1' % (index, step_name))
                step.COM('sr_tab_change,line=%s,step=%s,x=%s,y=%s,nx=%s,ny=%s,dx=%s,dy=%s,angle=%s' % (
                    index, step_name, p['point_x'], p['point_y'], p['nx'], p['ny'], p['dx'], p['dy'], p['ang']))
                
                index += 1
                
        xmid = pnl_x / 2
        ymid = pnl_y / 2
        step.COM("sredit_keep_sr_pattern,keep_sr_entry=yes")
        step.COM("sredit_keep_gap,keep_gap=yes")
        step.COM("sredit_keep_margin,keep_margin=yes")
        step.COM("sredit_sel_clear")
        step.COM("sredit_pack_steps, mode = vcenter,pos=%s" % ymid)
        step.COM("sredit_sel_clear")
        step.COM("sredit_pack_steps, mode = hcenter,pos=%s" % xmid)
        
        step.COM("units,type=mm")
        
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
        sr_xmin, sr_ymin, sr_xmax, sr_ymax = get_sr_limits(step)
        
        lb_x = sr_xmin - f_xmin
        lb_y = sr_ymin - f_ymin
        
        job.removeStep(stepname)
        
        return lb_y, lb_x
    
    def check_panel_info(self):
        """检测panel拼板是否正确"""
        array_data_info = getPanelSRTable(job.name.upper())
        if array_data_info and "panel" in matrixinfo["gCOLstep_name"]:
            
            if "-lyh" not in job.name:                
                if lay_num <= 2:
                    # 双面板获取不到留边 暂时不检测
                    return "success", None
            
            array_data_info1 = get_inplan_mrp_info_new(job.name.upper(), "1=1")
            if not array_data_info1:
                return u"获取inplan的留边尺寸异常，请检查型号名是否正确！", None
            
            left_lb_size = 0
            top_lb_size = 0
            pnl_size_x = 0
            pnl_size_y = 0
            op_step = None
            op_step_num = 0
            for dic_info in array_data_info:
                if "SET" in dic_info["OP_STEP"] or \
                   "PCS" in dic_info["OP_STEP"]:
                    op_step_num += dic_info["X_NUM"] * dic_info["Y_NUM"]
                    op_step = dic_info["OP_STEP"]
                
            for dic_info in array_data_info1:                
                if "-" not in dic_info["MRPNAME"]:                    
                    top_lb_size = dic_info["TOP_B"] + (dic_info["PNLYINCH"] - dic_info["PNLROUTY"]) * 0.5 * 25.4
                    left_lb_size = dic_info["LEFT_B"] + (dic_info["PNLXINCH"] - dic_info["PNLROUTX"]) * 0.5 * 25.4
                    # print dic_info, dic_info["LEFT_B"], (dic_info["PNLXINCH"] - dic_info["PNLROUTX"]) * 0.5 * 25.4, left_lb_size
                    pnl_size_x = dic_info["PNLXINCH"] * 25.4
                    pnl_size_y = dic_info["PNLYINCH"] * 25.4
                    break
            
            if lay_num > 2:
                if not left_lb_size or not top_lb_size:
                    return u"获取inplan的留边尺寸异常，请反馈程序工程师检查！", None
                
                if not op_step or not op_step_num:
                    return u"获取inplan拼版信息异常，请反馈程序工程师检查！", None
            else:
                if "-lyh" in job.name:       
                    top_lb_size, left_lb_size = self.create_calc_inplan_sr_panel(array_data_info, pnl_size_x/25.4, pnl_size_y/25.4)
            
            # 获取脚线区域 判断有小sr的区域
            worklayer = "l1"
            stepname = "panel"
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            
            f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
            
            layer_cmd = gClasses.Layer(step, worklayer)
            feat_out = layer_cmd.featCurrent_LayerOut(units="mm")["pads"]
            jx_symbol_obj = [obj for obj in feat_out if obj.symbol in ("sh-con2", "sh-con")]
            all_jx_x = [obj.x for obj in jx_symbol_obj]
            all_jx_y = [obj.y for obj in jx_symbol_obj]
            min_jx_x = min(all_jx_x)
            max_jx_x = max(all_jx_x)
            min_jx_y = min(all_jx_y)
            max_jx_y = max(all_jx_y)            
            
            STR = '-t step -e %s/%s -d REPEAT,units=mm' % (jobname, stepname)
            gREPEAT_info = step.DO_INFO(STR)
            gREPEATstep = gREPEAT_info['gREPEATstep']
            gREPEATxmax = gREPEAT_info['gREPEATxmax']
            gREPEATymax = gREPEAT_info['gREPEATymax']
            gREPEATxmin = gREPEAT_info['gREPEATxmin']
            gREPEATymin = gREPEAT_info['gREPEATymin']
            
            panel_set_num = 0
            set_rect_area = []
            for i, name in enumerate(gREPEATstep):
                if op_step.lower() == name:
                    panel_set_num += 1
                    set_rect_area.append(
                        [gREPEATxmin[i], gREPEATymin[i], gREPEATxmax[i], gREPEATymax[i]])                    
                
                if gREPEATxmin[i] > min_jx_x and gREPEATymin[i] > min_jx_y and \
                   gREPEATxmax[i] < max_jx_x and gREPEATymax[i] < max_jx_y and \
                   ("set" in name or "edit" in name or "icg" in name):
                    set_rect_area.append(
                        [gREPEATxmin[i], gREPEATymin[i], gREPEATxmax[i], gREPEATymax[i]])
            
            all_sr_x = [x[0] for x in set_rect_area] + [x[2] for x in set_rect_area]
            all_sr_y = [x[1] for x in set_rect_area] + [x[3] for x in set_rect_area]                     
            
            if abs(pnl_size_x-(f_xmax-f_xmin)) > 0.1 or \
               abs(pnl_size_y-(f_ymax-f_ymin)) > 0.1:
                return u"检测拼版尺寸(长：{0} 短：{1})跟inplan中的(长：{2} 短：{3})不一致，\
                请反馈MI检查是否有重新排版未通知到CAM！".format(pnl_size_y, pnl_size_x, (f_ymax-f_ymin), (f_xmax-f_xmin)), None                        
            
            if abs(min(all_sr_x) - f_xmin - left_lb_size) > 0.1 or \
               abs(min(all_sr_y) - f_ymin - top_lb_size) > 0.1 :
                return u"留边尺寸底部短边：{0} 左侧长边：{1} 跟inplan的拼版留边(短：{2}，长：{3})不一致，\
                请反馈MI检查是否有重新排版未通知到CAM！".format(min(all_sr_y) - f_ymin, min(all_sr_x) - f_xmin, top_lb_size, left_lb_size), None
            
            #if "-lyh" in job.name:
                #step.PAUSE(str([min(all_sr_x), max(all_sr_x), min(all_sr_x) - f_xmin, f_xmax - max(all_sr_x), left_lb_size]))            
            #print f_xmax - max(all_sr_x), left_lb_size
            #print f_ymax - max(all_sr_y), top_lb_size
            if abs(f_xmax - max(all_sr_x) - left_lb_size) > 0.1 or \
               abs(f_ymax - max(all_sr_y) - top_lb_size) > 0.1 :
                return u"留边尺寸顶部短边：{0} 右侧长边：{1} 跟inplan的拼版留边(短：{2}，长：{3})不一致，\
                请反馈MI检查是否有重新排版未通知到CAM！".format(f_ymax - max(all_sr_y), f_xmax - max(all_sr_x), top_lb_size, left_lb_size), None
            
            if panel_set_num and panel_set_num != op_step_num:
                return u"拼版内的{0}数量{1}跟inplan中的{0}数量{2}不一致，\
                请反馈MI检查是否有重新排版未通知到CAM！".format(op_step, panel_set_num, op_step_num), None            
            
        return "success", None
    
    def find_pth_hole_slot_contact_profile(self, args="auto_check"):
        """检查与profile相交的槽及孔
        对于板内有 > 0.9mm 的槽 (PTH) 或 者 0.7 <= (PTH) 圆孔锣半孔成型锣空位与槽或者孔重合时"""
        
        setsteps = get_panelset_sr_step(jobname, "panel")
        arraylist_log = []
        for stepname in list(set(setsteps)):            
            if "edit" in stepname:
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")
                step.COM("profile_to_rout,layer=outline_tmp,width=1")                

                for i, drill_layer in enumerate(matrixinfo["gROWname"]):
                    if matrixinfo["gROWcontext"][i] == "board" and \
                       matrixinfo["gROWlayer_type"][i] == "drill":
                        step.clearAll()
                        step.affect(drill_layer)
                        step.resetFilter()
                        step.filter_set(feat_types='pad;line', polarity='positive')
                        step.setAttrFilter(".drill,option=plated")
                        step.refSelectFilter("outline_tmp")
                        if step.featureSelected():
                            step.removeLayer("find_hole_slot")
                            step.copySel("find_hole_slot")
                            step.clearAll()
                            if step.isLayer("l1"):
                                step.affect("l1")
                                step.contourize()
                                step.clearAll()
                                step.affect("find_hole_slot")
                                step.resetFilter()
                                step.refSelectFilter("l1", mode="cover")
                                step.COM("sel_reverse")
                                if step.featureSelected():
                                    step.selectDelete()
                                    
                            layer_cmd = gClasses.Layer(step, "find_hole_slot")
                            slot_feat = layer_cmd.featOut(units="mm")["lines"]
                            pad_feat = layer_cmd.featOut(units="mm")["pads"]
                            
                            find_slot = list(set([obj.symbol for obj in slot_feat if float(obj.symbol[1:]) > 900]))
                            find_pad = list(set([obj.symbol for obj in pad_feat if float(obj.symbol[1:]) >= 700]))
                            
                            if find_slot:                                
                                log = u"型号{0}:{1} {2}层内发现有{3} PTH槽跟成型线相交！"
                                arraylist_log.append(log.format(job.name, stepname, drill_layer, find_slot))
                                
                            if find_pad:                                
                                log = u"型号{0}:型号{1} {2}层内发现有{3} PTH孔跟成型线相交！"
                                arraylist_log.append(log.format(job.name, stepname, drill_layer, find_pad))
                                
        if args == "auto_check":
            return arraylist_log
        
        if arraylist_log:            
            with open("d:/tmp/find_slot_hole.log", "a") as f:
                f.write("\n".join(arraylist_log).encode("cp936"))
                f.write("\n")

    def find_ks_target_has_outer_pad(self, args="auto_check"):
        """检查控深靶外层是否有铜皮pad"""
        
        stepname = "panel"
        if stepname not in matrixinfo["gCOLstep_name"]:
            return
        
        arraylist_log = []
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        step.clearAll()
        for layer in innersignalLayers:
            step.affect(layer)
        
        step.selectSymbol('hdi1-bmd;hdi1-bmdj', 1, 1)
        if step.featureSelected():
            step.removeLayer("ks_ba_tmp")
            step.copySel("ks_ba_tmp")
            
            for layer in signalLayers:
                step.affect(layer)
                
            step.resetFilter()
            step.setSymbolFilter("sh-dwtop;sh-dwbot")
            step.refSelectFilter("ks_ba_tmp")
            if step.featureSelected():
                arraylist_log = [job.name]
        
        if arraylist_log:      
            with open("d:/tmp/find_target_error_jobs.log", "a") as f:
                f.write("\n".join(arraylist_log).encode("cp936"))
                f.write("\n")
                
    def delJob(self, jobname):
        # top = gClasses.Top()
        top.VOF()			
        STR ='check_inout,mode=in,type=job,job=%s' %jobname
        STR1 ='close_job,job=%s' %jobname
        STR2='close_form,job=%s' %jobname
        STR3='close_flow,job=%s' %jobname
        STR4='delete_entity,job=,type=job,name=%s' %jobname		
        top.COM(STR1)
        top.COM(STR2)
        top.COM(STR3)
        top.COM(STR4)    
        top.VON()    
                
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
                
    def check_gold_finger_connection_info(self):
        """检测金手指导通性 20240902 by lyh"""
        jobname = os.environ["JOB"]
        job = gClasses.Job(jobname)
        job.open(1)
        matrixinfo = job.matrix.getInfo()
        
        has_gold_finger = False        
        data_info = get_inplan_all_flow(jobname.upper(), True)
        ganmo_process = [dic_info for dic_info in data_info
                        if u"选化干膜" in dic_info["WORK_CENTER_CODE"].decode("utf8") or \
                        u"选镀干膜" in dic_info["WORK_CENTER_CODE"].decode("utf8") ]
        shimo_process = [dic_info for dic_info in data_info
                        if u"印选化油" in dic_info["WORK_CENTER_CODE"].decode("utf8")]
        has_jsz_process = [dic_info for dic_info in data_info
                        if u"电镀镍金" in dic_info["WORK_CENTER_CODE"].decode("utf8")]        

        worklayers = []
        for i, layer in enumerate(matrixinfo["gROWname"]):
            if matrixinfo["gROWcontext"][i] == "board":
                if ganmo_process:                    
                    if layer in ["gold-c", "gold-s"]:
                        index = matrixinfo["gROWname"].index(layer)
                        if matrixinfo["gROWcontext"][index] != "board":
                            continue
                        worklayers.append(layer)
                        has_gold_finger = True
                        
                if shimo_process:
                    if layer in ["linek-c-1", "linek-s-1", "linek-c", "linek-s"]:
                        index = matrixinfo["gROWname"].index(layer)
                        if matrixinfo["gROWcontext"][index] != "board":
                            continue
                        worklayers.append(layer)
                        has_gold_finger = True  
        
        # if not has_gold_finger:
        if not has_jsz_process:
            return u"success非镀金手指板，无需检测", None
        
        stepname = "panel"
        if stepname not in matrixinfo["gCOLstep_name"]:
            return u"success panel不存在，无需检测", None
             
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)            
        
        rect= get_sr_area_for_step_include(step.name, include_sr_step=["edit", "set"])
        sr_xmin = min([min(x1, x2) for x1, y1, x2, y2 in rect])    
        sr_ymin = min([min(y1, y2) for x1, y1, x2, y2 in rect])   
        sr_xmax = max([max(x1, x2) for x1, y1, x2, y2 in rect])
        sr_ymax = max([max(y1, y2) for x1, y1, x2, y2 in rect])
        
        editname = "edit"
        edit_step = gClasses.Step(job, editname)
        edit_step.open()
        edit_step.COM("units,type=mm")
        arraylist = []
        for layer in outsignalLayers:
            edit_step.clearAll()
            edit_step.affect(layer)
            edit_step.resetFilter()
            edit_step.filter_set(feat_types='pad', polarity='positive')
            edit_step.setAttrFilter(".string,text=gf")
            edit_step.selectAll()
            if not edit_step.featureSelected():
                log = u"检测到此板为金手指板，但{0}层内未发现定义属性.string=gf 的金手指pad".format(layer)
                arraylist.append(log)
                
        edit_step.clearAll()
        if arraylist:
            return arraylist, None
        
        # 需copy一个型号出来检测
        if "172.28.30" in localip[2][0]:
            dbname = "db3"
        else:
            dbname = "db1"
            
        if jobname+"_flt" in top.listJobs():
            self.delJob(jobname+"_flt")
            
        top.COM("copy_entity,type=job,source_job={0},source_name={0},"
                "dest_job={1},dest_name={1},"
                "dest_database={2},remove_from_sr=yes".format(jobname,
                                                              jobname+"_flt",
                                                              dbname))
        
        job = gClasses.Job(jobname+"_flt")
        job.open(1)
        
        editname = "edit"
        edit_step = gClasses.Step(job, editname)
        edit_step.open()
        edit_step.COM("units,type=mm")
        arraylist = []
        
        for layer in signalLayers:
            # 从旧型号拷贝资料过来 
            edit_step.copyLayer(os.environ["JOB"], editname, layer, layer)
            
        for layer in outsignalLayers:
            edit_step.clearAll()
            edit_step.affect(layer)
            edit_step.resetFilter()
            edit_step.filter_set(feat_types='pad', polarity='positive')
            edit_step.setAttrFilter(".string,text=gf")
            edit_step.selectAll()
            if not edit_step.featureSelected():
                log = u"检测到此板为金手指板，但{0}层内未发现定义属性.string=gf 的金手指pad".format(layer)
                arraylist.append(log)
            edit_step.removeLayer(layer+"_attr_pcs_finger")
            if layer == "l1":         
                edit_step.createLayer(layer+"_attr_pcs_finger", laytype="signal", ins_layer=layer, location="before")
            else:
                edit_step.createLayer(layer+"_attr_pcs_finger", laytype="signal", ins_layer=layer, location="after")            
            
            layer_cmd = gClasses.Layer(edit_step, layer)
            feat_out = layer_cmd.featSelOut(units="mm")["pads"]
            
            edit_step.copySel(layer+"_attr_pcs_finger")
            
            edit_step.resetFilter()
            edit_step.filter_set(feat_types='pad', polarity='positive')
            # edit_step.setAttrFilter(".smd")
            
            all_x = [obj.x for obj in feat_out]
            all_y = [obj.y for obj in feat_out]
            symbolnames = list(set([obj.symbol for obj in feat_out]))
            
            # X方向的
            dic_zu = {}
            for i, y1 in enumerate(list(set(all_y))):
                dic_zu[y1] = 0
                arraylist_x = []
                for j, y2 in enumerate(all_y):
                    if y2 == y1 and all_x[j] not in arraylist_x:
                    # if y2 == y1:
                        dic_zu[y1] += 1
                        arraylist_x.append(all_x[j])
            # 找出最多的一排y值
            # find_y = [k for k, v in dic_zu.iteritems() if v == max(dic_zu.values())]
            for k, v in dic_zu.iteritems():
                if v >= 3:                                        
                    shuiping_feat_out = [obj for obj in feat_out if obj.y == k]
                    shuiping_x = [obj.x for obj in shuiping_feat_out]
                    shuiping_y = shuiping_feat_out[0].y
                    rect_area = [min(shuiping_x) - 1 , shuiping_y - 1.5, max(shuiping_x) + 1 , shuiping_y + 1.5]
                    edit_step.setSymbolFilter(";".join(symbolnames))
                    edit_step.selectRectangle(*rect_area, intersect='yes')
                    if edit_step.featureSelected():
                        edit_step.copySel(layer+"_attr_pcs_finger")
                        
                    edit_step.resetFilter()
                    edit_step.filter_set(polarity='positive')
                    # 有些铜皮也有smd属性 要镀金的
                    edit_step.setAttrFilter(".smd")
                    edit_step.selectRectangle(*rect_area, intersect='yes')
                    if edit_step.featureSelected():
                        edit_step.copySel(layer+"_attr_pcs_finger")
                        
            #if "-lyh" in job.name:
                #edit_step.PAUSE(str(dic_zu))
            # Y方向的
            dic_zu = {}
            for i, x1 in enumerate(list(set(all_x))):
                dic_zu[x1] = 0
                arraylist_y = []
                for j, x2 in enumerate(all_x):
                    if x2 == x1 and all_y[j] not in arraylist_y:
                    # if x2 == x1:
                        dic_zu[x1] += 1
                        arraylist_y.append(all_y[j])
            # 找出最多的一排x值
            # find_x = [k for k, v in dic_zu.iteritems() if v == max(dic_zu.values())]
            for k, v in dic_zu.iteritems():
                if v >= 3:                                
                    chuizhi_feat_out = [obj for obj in feat_out if obj.x == k]
                    chuizhi_y = [obj.y for obj in chuizhi_feat_out]
                    chuizhi_x = chuizhi_feat_out[0].x
                    rect_area = [chuizhi_x - 1.5, min(chuizhi_y) - 1, chuizhi_x + 1.5, max(chuizhi_y) + 1 ]
                    edit_step.setSymbolFilter(";".join(symbolnames))
                    edit_step.selectRectangle(*rect_area, intersect='yes')
                    if edit_step.featureSelected():
                        edit_step.copySel(layer+"_attr_pcs_finger")
                        
                    edit_step.resetFilter()
                    edit_step.filter_set(polarity='positive')
                    # 有些铜皮也有smd属性 要镀金的
                    edit_step.setAttrFilter(".smd")
                    edit_step.selectRectangle(*rect_area, intersect='yes')
                    if edit_step.featureSelected():
                        edit_step.copySel(layer+"_attr_pcs_finger")                        
            
            edit_step.clearAll()
            
        if arraylist:
            self.delJob(jobname+"_flt")
            return arraylist, None        
        
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        matrixinfo = job.matrix.getInfo()
        
        check_layers = []
        for i, layer in enumerate(matrixinfo["gROWname"]):
            if matrixinfo["gROWcontext"][i] == "board" and \
               matrixinfo["gROWlayer_type"][i] == "drill"\
               and ("bdc" not in layer and "bds" not in layer):
                check_layers.append(layer)
                
            if "_attr_pcs_finger" in layer:
                check_layers.append(layer)
        
        check_layers += signalLayers
        
        for i, layer in enumerate(matrixinfo["gROWname"]):
            if layer not in check_layers:
                step.removeLayer(layer)
                
        step.COM("sredit_reduce_nesting,mode=except_lowest")
        step.COM("sredit_reduce_nesting,mode=one_highest")
        
        #f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)            
        
        #rect= get_sr_area_for_step_include(step.name, include_sr_step=["edit", "set"])
        #sr_xmin = min([min(x1, x2) for x1, y1, x2, y2 in rect])    
        #sr_ymin = min([min(y1, y2) for x1, y1, x2, y2 in rect])   
        #sr_xmax = max([max(x1, x2) for x1, y1, x2, y2 in rect])    
        #sr_ymax = max([max(y1, y2) for x1, y1, x2, y2 in rect])
        #周涌通知 有些是内拉引线 故所有的线路跟钻带都要flatten
  
        ## for worklayer in signalLayers + ["drl", "cdc", "cds"] + mai_drill_layers + mai_man_drill_layers + laser_drill_layers:
        #for worklayer in outsignalLayers + ["drl", "cdc", "cds", "2nd"]:            
            #if not step.isLayer(worklayer):
                #continue
            
            #if worklayer in ["drl", "cdc", "cds", "2nd"] + mai_drill_layers + mai_man_drill_layers + laser_drill_layers:
                #layer_type = "drill"
            #else:
                #layer_type = "signal"
               
            #step.removeLayer(worklayer+"_flt")
            #if worklayer == "l1":                
                #step.createLayer(worklayer+"_flt", laytype=layer_type, ins_layer=worklayer, location="before")
            #else:
                #step.createLayer(worklayer+"_flt", laytype=layer_type, ins_layer=worklayer, location="after")
            #step.clearAll() 
            #step.flatten_layer(worklayer, worklayer+"_flt")
            
        ## if "-lyh" in job.name:            
        #flip_steps = []
        #flip_steps = self.flipStepName(step, stepname, flip_steps)
        #if flip_steps:                  
            #flipstep = gClasses.Step(job, "edit")
            #flipstep.open()
            #flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % job.name)
        
            #for worklayer in outsignalLayers:               
                #flipstep.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(job.name, worklayer+"_flt"))
                #flipstep.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(job.name, worklayer+"_attr_pcs_finger"))
                
            ## for worklayer in innersignalLayers + ["drl", "cdc", "cds"] + mai_drill_layers + mai_man_drill_layers + laser_drill_layers:
            #for worklayer in ["drl", "cdc", "cds", "2nd"]:                
                #if not step.isLayer(worklayer):
                    #continue
                #flipstep.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(job.name, worklayer+"_flt"))
        #else:
            ## for worklayer in signalLayers + ["drl", "cdc", "cds"] + mai_drill_layers + mai_man_drill_layers + laser_drill_layers:
            #for worklayer in outsignalLayers + ["drl", "cdc", "cds", "2nd"]:
                #if not step.isLayer(worklayer):
                    #continue  
                #step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(job.name, worklayer+"_flt"))
        
        ## if "-lyh" in job.name:            
        #if flip_steps:               
            #flipstep = gClasses.Step(job, "edit")
            #flipstep.open()
            #flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % job.name)
        
        step.open(iconic='No')
        for worklayer in outsignalLayers:
            step.clearAll()
            
            step.removeLayer(worklayer+"_pnl_finger_smd")
            step.createLayer(worklayer+"_pnl_finger_smd")
            #step.removeLayer(worklayer+"_flt")
            #step.flatten_layer(worklayer, worklayer+"_flt")
            # step.affect(worklayer+"_flt")
            step.display(worklayer)
            step.COM("sel_delete_atr,attributes=.n_electric")
            
            for i in range(100):
                x, y = sr_xmin - 1.5 - 0.1 * i, sr_ymin - 1.5 - 0.1 * i                
                step.selectNone()
                step.COM("sel_board_net_feat,operation=select,x={0},y={1},tol=599.5625,use_ffilter=no".format(x, y))
                #if "-lyh" in job.name:
                    #step.PAUSE("ddd")                
                if step.featureSelected() > 10:
                    break
                if x < f_xmin or y < f_ymin:
                    break

            if not step.featureSelected():
                for i in range(100):
                    x, y = f_xmin + 0.5 * i, f_ymin + 0.5 * i                
                    step.selectNone()
                    step.COM("sel_board_net_feat,operation=select,x={0},y={1},tol=599.5625,use_ffilter=no".format(x, y))
                    if step.featureSelected() > 10:
                        break
                    if x > sr_xmin:
                        break                
            
            if step.featureSelected():
                step.removeLayer(worklayer+"_find_feat")
                step.copySel(worklayer+"_find_feat")
                
                step.clearAll()
                step.affect(worklayer+"_find_feat")
                step.resetFilter()
                # step.setAttrFilter(".smd")
                # 有些手指会漏属性 这里全部选中
                step.selectAll()
                if step.featureSelected():                    
                    step.copyToLayer(worklayer+"_pnl_finger_smd", size=10)                    
                    
        #for pnl_step, edit_name in [("panel", "set"), ("panel", "edit"), ("set", "edit")]:
            
            #if pnl_step not in matrixinfo["gCOLstep_name"]:
                #continue
            
            #all_steps = get_panelset_sr_step(job.name, pnl_step, is_all=False)
            #if edit_name not in all_steps:
                #continue
            
            #for worklayer in outsignalLayers:
                #if pnl_step == "panel":
                    #symbol = get_panel_features_in_set_position(job.name, edit_name, pnl_step,
                                                                #"{0}_gold_finger_set".format(worklayer),
                                                                #worklayer,
                                                                #create_symbol="yes")
                #else:
                    #symbol = get_panel_features_in_set_position(job.name, edit_name, pnl_step,
                                                                #"{0}_gold_finger_set".format(worklayer),
                                                                #"{0}_calc_gold_tmp".format(worklayer),
                                                                #create_symbol="yes")                    
                #if symbol != "error":
                    #set_step = gClasses.Step(job, edit_name)
                    #set_step.open()
                    #set_step.COM("units,type=mm")
                    #if set_step.isLayer("{0}_calc_gold_tmp".format(worklayer)):
                        #set_step.COM("truncate_layer,layer={0}_calc_gold_tmp".format(worklayer))
                    #else:
                        #set_step.createLayer("{0}_calc_gold_tmp".format(worklayer))
                    
                    #set_step.clearAll()
                    #set_step.affect("{0}_calc_gold_tmp".format(worklayer))
                    #set_step.addPad(0, 0, symbol)
                    #set_step.COM("sel_break")
                    #set_step.selectSymbol("r10", 1, 1)
                    #if set_step.featureSelected():
                        #set_step.selectDelete()
                    
                    #set_step.resetFilter()
                    #set_step.filter_set(polarity='negative')
                    #set_step.selectAll()
                    #if set_step.featureSelected():
                        #set_step.selectDelete()
                        
                    #if pnl_step == "panel" and edit_name == "set":
                        #set_step.clearAll()
                        #set_step.affect(worklayer)
                        #set_step.copySel("{0}_calc_gold_tmp".format(worklayer))
                    
                    #if edit_name == "edit":
                        #set_step.clearAll()
                        #set_step.affect(worklayer)
                        #set_step.resetFilter()
                        #set_step.filter_set(polarity='positive')
                        #set_step.refSelectFilter("{0}_calc_gold_tmp".format(worklayer))
                        #if set_step.featureSelected():
                            #set_step.filter_set(polarity='positive')
                            #set_step.setAttrFilter(".smd")
                            #set_step.COM("sel_ref_feat,layers=,use=select,mode=touch,\
                            #pads_as=shape,f_types=line\;pad\;surface\;arc\;text,\
                            #polarity=positive\;negative,include_syms=,exclude_syms=")
                            #count = 1
                            #while  not set_step.featureSelected():
                                #set_step.selectNone()
                                #set_step.resetFilter()
                                #set_step.filter_set(polarity='positive')
                                #set_step.refSelectFilter("{0}_calc_gold_tmp".format(worklayer))
                                #for i in range(count):
                                    #set_step.COM("sel_ref_feat,layers=,use=select,mode=touch,\
                                    #pads_as=shape,f_types=line\;pad\;surface\;arc\;text,\
                                    #polarity=positive\;negative,include_syms=,exclude_syms=")
                                #set_step.filter_set(polarity='negative')
                                #set_step.COM("filter_area_end,filter_name=popup,operation=unselect")
                                
                                #set_step.filter_set(polarity='positive')
                                ##if "-lyh" in job.name:
                                    ##set_step.PAUSE("ee")
                                #set_step.setAttrFilter(".smd")
                                #set_step.COM("sel_ref_feat,layers=,use=select,mode=touch,\
                                #pads_as=shape,f_types=line\;pad\;surface\;arc\;text,\
                                #polarity=positive\;negative,include_syms=,exclude_syms=")
                                #count += 1
                                #if set_step.featureSelected():
                                    #break
                                
                                #if count > 3:
                                    #break
                                
                            #if set_step.featureSelected():
                                #layer_cmd = gClasses.Layer(set_step, worklayer)
                                #feat_out = layer_cmd.featSelOut(units="mm")["pads"]
                                
                                #set_step.removeLayer(worklayer+"_find_pcs_figer")
                                #set_step.copySel(worklayer+"_find_pcs_figer")                                
                                
                                #all_x = [obj.x for obj in feat_out]
                                #all_y = [obj.y for obj in feat_out]
                                ## X方向的
                                #dic_zu = {}
                                #for i, y1 in enumerate(list(set(all_y))):
                                    #dic_zu[y1] = 0
                                    #for j, y2 in enumerate(all_y):
                                        #if y2 == y1:
                                            #dic_zu[y1] += 1
                                ## 找出最多的一排y值
                                ## find_y = [k for k, v in dic_zu.iteritems() if v == max(dic_zu.values())]
                                #for k, v in dic_zu.iteritems():
                                    #if v >= 2:                                        
                                        #shuiping_feat_out = [obj for obj in feat_out if obj.y == k]
                                        #shuiping_x = [obj.x for obj in shuiping_feat_out]
                                        #shuiping_y = shuiping_feat_out[0].y
                                        #rect_area = [min(shuiping_x) , shuiping_y - 0.1, max(shuiping_x) , shuiping_y + 0.1]
                                        #set_step.selectRectangle(*rect_area, intersect='yes')
                                        #if set_step.featureSelected():
                                            #set_step.copySel(worklayer+"_find_pcs_figer")
                                
                                ## Y方向的
                                #dic_zu = {}
                                #for i, x1 in enumerate(list(set(all_x))):
                                    #dic_zu[x1] = 0
                                    #for j, x2 in enumerate(all_x):
                                        #if x2 == x1:
                                            #dic_zu[x1] += 1
                                ## 找出最多的一排x值
                                ## find_x = [k for k, v in dic_zu.iteritems() if v == max(dic_zu.values())]
                                #for k, v in dic_zu.iteritems():
                                    #if v >= 2:                                
                                        #chuizhi_feat_out = [obj for obj in feat_out if obj.x == k]
                                        #chuizhi_y = [obj.y for obj in chuizhi_feat_out]
                                        #chuizhi_x = shuiping_feat_out[0].x
                                        #rect_area = [chuizhi_x - 0.1, min(chuizhi_y) , chuizhi_x + 0.1, max(chuizhi_y)]
                                        #set_step.selectRectangle(*rect_area, intersect='yes')
                                        #if set_step.featureSelected():
                                            #set_step.copySel(worklayer+"_find_pcs_figer")
                                            
                                #set_step.clearAll()
                                            
        #开始panel比对
        step.open()
        arraylist = []
        dic_zu_layer = {}
        for worklayer in outsignalLayers:
            if not step.isLayer(worklayer+"_pnl_finger_smd"):
                log = u"检测到此板为镀金手指板，但panel内 引线网络异常，请手动检查是否金手指网络导通性！！"
                arraylist.append(log.format(worklayer))
                continue
            
            step.flatten_layer(worklayer+"_attr_pcs_finger", worklayer+"_attr_pcs_finger_flt")
            step.resetFilter()
            step.clearAll()
            step.affect(worklayer+"_attr_pcs_finger_flt")
            step.refSelectFilter(worklayer+"_pnl_finger_smd", mode="cover")
            step.COM("sel_reverse")
            if step.featureSelected():
                log = u"检测到此板为镀金手指板，但panel内{0}层的部分手指网络不导通1，请检查标记处手指引线是否异常！！"
                arraylist.append(log.format(worklayer))                                               
                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, worklayer+"_attr_pcs_finger_flt",
                                                                     worklayer,log.format(worklayer), dic_zu_layer, add_note_layer=worklayer)
                # continue
                
            #if step.isLayer(worklayer+"_pnl_finger_smd") and step.isLayer(worklayer+"_find_pcs_figer"):
                #step.flatten_layer(worklayer+"_find_pcs_figer", worklayer+"_find_pcs_figer_flt")
                #step.resetFilter()
                #step.clearAll()
                #step.affect(worklayer+"_find_pcs_figer_flt")
                #step.refSelectFilter(worklayer+"_pnl_finger_smd", mode="cover")
                #step.COM("sel_reverse")
                #if step.featureSelected():
                    #log = u"检测到此板为镀金手指板，但panel内{0}层的部分手指网络不导通2，请检查标记处手指引线是否异常！！"
                    #arraylist.append(log.format(worklayer))                                               
                    #dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, worklayer+"_find_pcs_figer_flt",
                                                                         #worklayer,log.format(worklayer), dic_zu_layer, add_note_layer=worklayer)
            
            if "-lyh" not in job.name:                
                step.removeLayer(worklayer+"_pnl_finger_smd")
                step.removeLayer(worklayer+"_find_pcs_figer")
                step.removeLayer(worklayer+"_find_pcs_figer_flt")
                step.removeLayer(worklayer+"_finger_smd")
                step.removeLayer(worklayer+"_calc_gold_tmp")
                step.removeLayer(worklayer+"_gold_finger_set")
                step.removeLayer(worklayer+"_find_feat")
                step.removeLayer(worklayer+"_flt")
                step.removeLayer(worklayer+"_attr_pcs_finger_flt")
                step.removeLayer(worklayer+"_attr_pcs_finger")
        
        if "-lyh" not in job.name:  
            for worklayer in signalLayers + ["drl", "cdc", "cds"] + mai_drill_layers + mai_man_drill_layers + laser_drill_layers:
                step.removeLayer(worklayer+"flt")
        
        if arraylist:
            if "-lyh" in job.name:
                for layer in outsignalLayers:
                    step.COM("note_delete_all,layer={0},user=,note_from=0,note_to=2147483647".format(layer))
                showMessageInfo(*arraylist)
                self.view_note_detail(dic_zu_layer)
            
            self.delJob(jobname+"_flt")
            return arraylist, dic_zu_layer
        self.delJob(jobname+"_flt")
        return "success", None
    
    def check_rotation_step_and_week_number(self):
        """检测旋转step及周期的一致性"""
        dic_step_week_info = {} # 检测step对应是否有周期 已经step是否有旋转
        if "panel" in matrixinfo["gCOLstep_name"]:
            step = gClasses.Step(job, "panel")
            step.open()
            pnl_step_info = step.getInfo()
            arraylist_log = []
            all_steps = get_panelset_sr_step(jobname, "panel")
            # dic_step_angle_info = {}
            for stepname in list(set(all_steps)):
                step = gClasses.Step(job, stepname)
                step.open()
                repeat_angle = list(set([pnl_step_info["gREPEATangle"][i] for i, repeat_step in enumerate(pnl_step_info["gREPEATstep"])
                                         if stepname == repeat_step]))
                # dic_step_angle_info[stepname] = repeat_angle
                
                other_angles = list(set([agl for agl in repeat_angle if agl not in [0, 90, 270, 180]]))
                normal_angles = list(set([agl for agl in repeat_angle if agl in [0, 90, 270, 180]]))
                if other_angles and normal_angles:
                    log = u"检测到{0} 有在panel内有旋转，但此step在panel拼版内同时存在旋转{3}跟不旋转{4}的角度，<br>\
                    请反馈领导此step是否全部旋转或全部不旋转，以免输出ODB++后造成动态周期会存在不一致的现象，请检查！"
                    arraylist_log.append(log.format(stepname, other_angles, normal_angles))            
            
            if arraylist_log:
                return arraylist_log, None            
        
        
    def get_week_picihao_banci_info(self, *check_types):
        """获取周期 批次 班次信息"""
        
        if "panel" in matrixinfo["gCOLstep_name"]:            
            setsteps = get_panelset_sr_step(jobname, "panel")
            if not check_types:                
                check_types = ["silk_screen", "signal", "solder_mask"]        
            dic_tgz_week_layers = {}
            dic_tgz_barcode_week_layers = {}
            dic_tgz_banci_layers = {}
            dic_tgz_picihao_layers = {}
            
            week_font = []
            # job.PAUSE(str(list(set(setsteps))))
            for stepname in list(set(setsteps)):
                step = gClasses.Step(job, stepname)
                step.open()
                
                for output_type in check_types:
                    checkLayers = []
                    if output_type == "silk_screen":                    
                        checkLayers = silkscreenLayers
                    if output_type == "solder_mask":                    
                        checkLayers = solderMaskLayers
                    if output_type == "signal":
                        checkLayers = outsignalLayers
                        
                    for worklayer in checkLayers:
                        step.clearAll()
                        step.resetFilter()
                        step.affect(worklayer)
                        step.filter_set(feat_types='text')
                        step.selectAll()
                        layer_cmd = gClasses.Layer(step, worklayer)
                        feat_out = layer_cmd.featSelOut(
                            units="mm")["text"]
                        
                        for obj in feat_out:
                            for wwyy in ["$$yy", "$$ww"]:
                                if wwyy in str(obj.text).replace("{", "").replace("}", "").lower():                                
                                    if dic_tgz_week_layers.has_key(worklayer):
                                        if obj not in dic_tgz_week_layers[worklayer]:                                        
                                            dic_tgz_week_layers[worklayer] += [obj]
                                            week_font.append(obj.font)
                                    else:
                                        dic_tgz_week_layers[worklayer] = [obj]
                                        week_font.append(obj.font)
                                        
                            for banci_pici in ["$$banci", "$$picihao"]:
                                if banci_pici in str(obj.text).replace("{", "").replace("}", "").lower():
                                    if banci_pici == "$$banci":                                    
                                        if dic_tgz_banci_layers.has_key(worklayer):
                                            if obj not in dic_tgz_banci_layers[worklayer]:                                            
                                                dic_tgz_banci_layers[worklayer] += [obj]
                                                week_font.append(obj.font)
                                        else:
                                            dic_tgz_banci_layers[worklayer] = [obj]
                                            week_font.append(obj.font)
                                            
                                    if banci_pici == "$$picihao":
                                        if dic_tgz_picihao_layers.has_key(worklayer):
                                            if obj not in dic_tgz_picihao_layers[worklayer]:                                            
                                                dic_tgz_picihao_layers[worklayer] += [obj]
                                                week_font.append(obj.font)
                                        else:
                                            dic_tgz_picihao_layers[worklayer] = [obj]
                                            week_font.append(obj.font)                                    
                        #if stepname in ["set", "edit"]:
                            #step.PAUSE(str(dic_tgz_week_layers))
                        feat_out = layer_cmd.featSelOut(
                            units="mm")["barcodes"]
                        for obj in feat_out:
                            for wwyy in ["$$yy", "$$ww"]:                        
                                if wwyy in str(obj.text).replace("{", "").replace("}", "").lower():
                                    
                                    if dic_tgz_barcode_week_layers.has_key(worklayer):
                                        if obj not in dic_tgz_barcode_week_layers[worklayer]:                                        
                                            dic_tgz_barcode_week_layers[worklayer] += [obj]
                                            week_font.append(obj.font)
                                    else:
                                        dic_tgz_barcode_week_layers[worklayer] = [obj]
                                        week_font.append(obj.font)
                                        
                            for banci_pici in ["$$banci", "$$picihao"]:
                                if banci_pici in str(obj.text).replace("{", "").replace("}", "").lower():
                                    if banci_pici == "$$banci":                                    
                                        if dic_tgz_banci_layers.has_key(worklayer):
                                            if obj not in dic_tgz_banci_layers[worklayer]:                                            
                                                dic_tgz_banci_layers[worklayer] += [obj]
                                                week_font.append(obj.font)
                                        else:
                                            dic_tgz_banci_layers[worklayer] = [obj]
                                            week_font.append(obj.font)
                                            
                                    if banci_pici == "$$picihao":
                                        if dic_tgz_picihao_layers.has_key(worklayer):
                                            if obj not in dic_tgz_picihao_layers[worklayer]:                                            
                                                dic_tgz_picihao_layers[worklayer] += [obj]
                                                week_font.append(obj.font)
                                        else:
                                            dic_tgz_picihao_layers[worklayer] = [obj]
                                            week_font.append(obj.font)                                      
                        
                        step.clearAll()
                        step.affect(worklayer)
                        step.resetFilter()
                        step.selectSymbol("zq-2wm;zq-ewm;zq-wm", 1, 1)
                        if step.featureSelected():
                            feat_out = layer_cmd.featSelOut(units="mm") ["pads"]
                            if dic_tgz_week_layers.has_key(worklayer):
                                if obj not in dic_tgz_week_layers[worklayer]:                                
                                    dic_tgz_week_layers[worklayer] += [obj for obj in feat_out]
                            else:
                                dic_tgz_week_layers[worklayer] = [obj for obj in feat_out]                   
                    
                step.clearAll()
                step.close()
                    
            return dic_tgz_week_layers, dic_tgz_barcode_week_layers, dic_tgz_banci_layers, dic_tgz_picihao_layers, week_font
        
        return None
    
    def check_rotation_step_week(self):
        """检测有旋转step的周期是否一致 20240902 by lyh"""
        dic_step_week_info = {} # 检测step对应是否有周期 已经step是否有旋转
        if "panel" in matrixinfo["gCOLstep_name"]:
            step = gClasses.Step(job, "panel")
            step.open()
            pnl_step_info = step.getInfo()
            arraylist_log = []
            all_steps = get_panelset_sr_step(jobname, "panel")
            for stepname in list(set(all_steps)):
                step = gClasses.Step(job, stepname)
                step.open()
                repeat_angle = list(set([pnl_step_info["gREPEATangle"][i] for i, repeat_step in enumerate(pnl_step_info["gREPEATstep"])
                                         if stepname == repeat_step]))
                dic_step_week_info[stepname] = []
                for worklayer in silkscreenLayers + solderMaskLayers + outsignalLayers:
                    step.clearAll()
                    step.affect(worklayer)
                    step.resetFilter()
                    step.filter_set(feat_types='text')
                    step.selectAll()
                    if not step.featureSelected():
                        continue
                    layer_cmd = gClasses.Layer(step, worklayer)
                    feat_out = layer_cmd.featSelOut(
                        units="mm")["text"]
                    for wwyy in ["$$yy", "$$ww"]:
                        for obj in feat_out:
                            week_text = str(obj.text).replace("{", "").replace("}", "").lower()
                            if wwyy in week_text:        
                                dic_step_week_info[stepname].append([worklayer, week_text, repeat_angle])
                                
            if dic_step_week_info:
                for stepname, info in dic_step_week_info.iteritems():
                    repeat_anle = []
                    for worklayer, text, angles in info:
                        repeat_anle += angles
                    
                    other_angles = list(set([agl for agl in repeat_anle if agl not in [0, 90, 270, 180]]))
                    normal_angles = list(set([agl for agl in repeat_anle if agl in [0, 90, 270, 180]]))
                    if other_angles and normal_angles:
                        log = u"检测到{0} 层{1} 内存在动态周期text:{2}，但此step在panel拼版内同时存在旋转{3}跟不旋转{4}的角度，<br>\
                        请反馈领导此step是否全部旋转或全部不旋转，以免输出ODB++后造成动态周期会存在不一致的现象，请检查！"
                        arraylist_log.append(log.format(stepname, worklayer, text, other_angles, normal_angles))
                        
            if arraylist_log:
                # showMessageInfo(*arraylist_log)
                return arraylist_log, None
            
        return "success", None            
    
    def check_period_week_info(self, check_types=[]):
        """检测周期面次信息"""
        dic_info = getJobData(job.name.upper())
        if dic_info:
            show_warning_log = []
            dic_zu_layer_type = {}
            dic_zu_layer_type["signal"] = u"线路层"
            dic_zu_layer_type["solder_mask"] = u"阻焊层"
            dic_zu_layer_type["silk_screen"] = u"字符层"            
            setsteps = get_panelset_sr_step(jobname, "panel")
            ERPPeriod = dic_info["dc_format"]
            layer_side = dic_info["dc_side"].decode("utf8")
            dic_side_layer = {u"文字C面": ["c1"],
                              u"文字C面+S面": ["c1", "c2"],
                              u"文字S面": ["c2"],
                              u"蚀刻C面": ["l1"],
                              u"蚀刻S面": [outsignalLayers[-1]],
                              u"蚀刻C面+S面": outsignalLayers,
                              u"蚀刻C面+文字S面": ["l1", "c2"],
                              u"蚀刻S面+文字C面": [outsignalLayers[-1], "c1"],
                              u"防焊C面": ["m1"],
                              u"防焊S面": ["m2"],
                              u"防焊C面+S面": ["m1", "m2"],
                              }
            inplan_check_layer = dic_side_layer.get(layer_side, [])
            # job.PAUSE(str(inplan_check_layer))
            if not check_types:
                check_types = ["silk_screen", "signal", "solder_mask"]
            
            dic_tgz_week_layers = {}
            week_font = []
            job_ww_exists = False
            job_yy_exists = False
            for stepname in list(set(setsteps)):
                step = gClasses.Step(job, stepname)
                step.open()
                step_yy_exists = False
                step_ww_exists = False
                
                for output_type in check_types:
                    checkLayers = []
                    if output_type == "silk_screen":                    
                        checkLayers = silkscreenLayers
                    if output_type == "solder_mask":                    
                        checkLayers = solderMaskLayers
                    if output_type == "signal":
                        checkLayers = outsignalLayers
                        
                    for worklayer in checkLayers:
                        layer_cmd = gClasses.Layer(step, worklayer)
                        feat_out = layer_cmd.featCurrent_LayerOut(
                            units="mm")["text"]
                        for wwyy in ["$$yy", "$$ww"]:
                            for obj in feat_out:
                                if wwyy in str(obj.text).replace("{", "").replace("}", "").lower():
                                    if "yy" in wwyy:
                                        step_yy_exists = True
                                    if "ww" in wwyy:
                                        step_ww_exists = True
                                    
                                    if dic_tgz_week_layers.has_key(worklayer):
                                        dic_tgz_week_layers[worklayer] += [str(obj.text).lower()]
                                        week_font.append(obj.font)
                                    else:
                                        dic_tgz_week_layers[worklayer] = [str(obj.text).lower()]
                                        week_font.append(obj.font)
                                    
                        step.clearAll()
                        step.affect(worklayer)
                        step.resetFilter()
                        step.selectSymbol("zq-2wm;zq-ewm;zq-wm", 1, 1)
                        if step.featureSelected():
                            feat_out = layer_cmd.featSelOut(units="mm") ["pads"]
                            if dic_tgz_week_layers.has_key(worklayer):
                                dic_tgz_week_layers[worklayer] += [obj.symbol for obj in feat_out]
                            else:
                                dic_tgz_week_layers[worklayer] = [obj.symbol for obj in feat_out]

                    if (step_yy_exists and not step_ww_exists) or\
                       (not step_yy_exists and step_ww_exists):
                        log = u"检测到此型号[%s]存在动态周期，ERP周期类型为:%s,但%s层[%s]内未发现全部的动态年周或周年，请检查周期是否被打散!" % (
                            dic_zu_layer_type[output_type], ERPPeriod, stepname, worklayer)
                        show_warning_log.append(log)
                        
                    if step_ww_exists and step_yy_exists:
                        job_ww_exists = True
                        job_yy_exists = True                       
                
                step.clearAll()
                step.close()
                
            if not job_ww_exists and not job_yy_exists and "yy" in ERPPeriod.lower() and "ww" in ERPPeriod.lower():
                log = u"检测到此型号[%s]存在动态周期，ERP周期类型为:%s,但资料内未发现全部的动态周期!" % (
                    dic_zu_layer_type[output_type],ERPPeriod)
                show_warning_log.append(log)
                
            for layer in dic_tgz_week_layers.keys():
                if layer not in inplan_check_layer:
                    log = u"检测到{0}层内存在动态周期{1}，但跟inplan要求周期添加层次:{2}-->{3}不一致，请检查周期是否添加层次有误！"
                    show_warning_log.append(log.format(layer, list(set(dic_tgz_week_layers[layer])), layer_side, inplan_check_layer))
            
            if dic_tgz_week_layers:            
                for layer in inplan_check_layer:
                    if layer not in dic_tgz_week_layers.keys():
                        log = u"检测到inplan要求周期添加层次:{0}-->{1}中的{2}内不存在动态周期，请检查周期是否添加层次有误，或周期是否打散！"
                        show_warning_log.append(log.format(layer, list(set(dic_tgz_week_layers[layer])), layer_side, inplan_check_layer))
                        
            if inplan_check_layer and ("yy" in ERPPeriod.lower() or "ww" in ERPPeriod.lower()):
                if not dic_tgz_week_layers:                
                    log = u"检测到inplan要求添加动态周期{0}，但资料内不存在动态周期，请检查周期是否被打散！"
                    show_warning_log.append(log.format(ERPPeriod))
            
            if "output_silk_tgz" in check_types:
                show_warning_log = ""
                if ERPPeriod.lower() not in ["yyww", "wwyy", "yy-ww", "ww-yy"]:
                    log = u"劲鑫资料输出只允许动态周期[YYWW, WWYY, YY-WW, WW-YY]形式输出，\n检测到此型号inplan周期为{0},含有静态文字，系统不允许有静态形式周期的劲鑫资料输出，若要强制输出，请走审批流程申请输出！"
                    show_warning_log += log.format(ERPPeriod)
                
                if ERPPeriod:
                    if not dic_tgz_week_layers:
                        log = u"\n检测到此型号inplan周期为{0},但资料内未检测到有动态周期，请检查资料内周期是否被打散，若要强制输出，请走审批流程申请输出！"
                        show_warning_log += log.format(ERPPeriod)
                        
                    for fontname in set(week_font):
                        if fontname.replace("'", "").lower() not in ["vgt_date", "standard", "simple", "simplex"]:
                            log = u"\n检测到此型号有周期字体{0}，此字体周期在genesis中不支持动态变化，若要强制输出，请走审批流程申请输出！"
                            show_warning_log += log.format(fontname)
            
            if show_warning_log:
                return show_warning_log, None
            
        return "success", None
    
    def check_barcode_has_attr_in_outsig_mask(self):
        """检测增加外层线路&防焊有添加二维码时，需检测二维码是否有 .deferred属性及正反是否正确。"""
        if "panel" in matrixinfo["gCOLstep_name"]:            
            setsteps = get_panelset_sr_step(jobname, "panel") + ["panel"]
            checkLayers = solderMaskLayers + outsignalLayers
            arraylist = []
            dic_zu_layer = {}
            for stepname in list(set(setsteps)):
                step = gClasses.Step(job, stepname)
                step.open()
    
                for worklayer in checkLayers:                    
                    step.clearAll()
                    step.affect(worklayer)
                    step.resetFilter()
                    step.filter_set(feat_types='text')
                    step.selectAll()
                    if step.featureSelected():
                        layer_cmd = gClasses.Layer(step, worklayer)
                        feat_out = layer_cmd.featout_dic_Index(
                            units="mm", options="select+feat_index")["barcodes"]
                        step.selectNone()
                        for obj in feat_out:
                            if getattr(obj, "deferred", None) is None:
                                log = u"检测到{1} {0} 层有二维码没加.deferred属性，请检查是否异常！".format(worklayer, stepname)
                                
                                if log not in arraylist:                                
                                    arraylist.append(log)
                                    
                                step.selectFeatureIndex(worklayer, obj.feat_index)
                            
                    if step.featureSelected():                        
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, worklayer,
                                                                             worklayer,log, dic_zu_layer)
                step.clearAll()
                
            if arraylist:
                return arraylist, dic_zu_layer

        return "success", None            
    
    def check_week_barcode_text_add_side(self):
        """检测周期等文字是否镜像或在top面被镜像 20231113 by lyh
        http://192.168.2.120:82/zentao/story-view-6177.html"""
        
        if "panel" in matrixinfo["gCOLstep_name"]:            
            setsteps = get_panelset_sr_step(jobname, "panel") + ["panel"]
            checkLayers = silkscreenLayers + solderMaskLayers + outsignalLayers
            arraylist = []
            dic_zu_layer = {}
            for stepname in list(set(setsteps)):
                step = gClasses.Step(job, stepname)
                step.open()
    
                for worklayer in checkLayers:
                    check_mirror = "no"
                    if worklayer in outsignalLayers:
                        if worklayer == "l1":
                            check_mirror = "no"
                        else:
                            check_mirror = "yes"
                    elif worklayer in silkscreenLayers:
                        if "c1" in worklayer:
                            check_mirror = "no"
                        else:
                            check_mirror = "yes"
                    else:
                        if "m1" in worklayer:
                            check_mirror = "no"
                        else:
                            check_mirror = "yes"
                    
                    step.clearAll()
                    step.affect(worklayer)
                    
                    layer_cmd = gClasses.Layer(step, worklayer)
                    feat_out = layer_cmd.featout_dic_Index(
                        units="mm", options="feat_index")["text"]
                    feat_out += layer_cmd.featout_dic_Index(
                        units="mm", options="feat_index")["barcodes"]
                    
                    pad_obj = layer_cmd.featout_dic_Index(
                        units="mm", options="feat_index")["pads"]
                    
                    for obj in feat_out:
                        if obj.mirror != check_mirror:
                            if check_mirror == "no":                                
                                log = u"检测到{2} {0} 层为top面，字符{1} 被镜像，请检查是否异常！".format(worklayer, obj.text, stepname)
                            else:
                                log = u"检测到{2} {0} 层为bot面，字符{1} 没有被镜像，请检查是否异常！".format(worklayer, obj.text, stepname)
                            
                            if log not in arraylist:                                
                                arraylist.append(log)
                                
                            step.selectFeatureIndex(worklayer, obj.feat_index)
                            
                    for obj in pad_obj:
                        if (re.match("barcode\d+x\d+", obj.symbol) and getattr(obj, "id", None) is not None) or \
                           obj.symbol == "num_250" or \
                           re.match("2dbc_\d+mm", obj.symbol):
                            
                            if obj.mirror != check_mirror:
                                if check_mirror == "no":                                
                                    log = u"检测到{2} {0} 层为top面，二维码symbol {1} 被镜像，请检查是否异常！".format(worklayer, obj.symbol, stepname)
                                else:
                                    log = u"检测到{2} {0} 层为bot面，二维码symbol {1} 没有被镜像，请检查是否异常！".format(worklayer, obj.symbol, stepname)
                                
                                if log not in arraylist:                                
                                    arraylist.append(log)
                                    
                                step.selectFeatureIndex(worklayer, obj.feat_index)                            
                    
                    if step.featureSelected():                        
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, worklayer,
                                                                     worklayer,log, dic_zu_layer)
                step.clearAll()
                
        if arraylist:
            # showMessageInfo(*arraylist)
            return arraylist, dic_zu_layer
        
        return "success", None
    
    def auto_check_flj_result(self):
        """审核自动检测防漏接是否异常"""
        os.system("python /incam/server/site_data/scripts/hdi_scr/Signal/run_check/get_checklist_result.py auto_check")
        error_log = "/tmp/check_flj_error_{0}.log".format(job.name)
        success_log = "/tmp/check_flj_success_{0}.log".format(job.name)
        if os.path.exists(error_log):
            lines = file(error_log).readlines()
            os.unlink(error_log)
            return [line.decode("cp936") for line in lines], None
        
        if os.path.exists(success_log):
            os.unlink(success_log)
            return "success", None
        else:
            return u"防漏接检测程序运行异常，请手动检查！", None
        
    def check_laser_touch_mai_tong_holes(self):
        """检测镭射钻在埋孔或通孔上的情况
        内层全自动检测----增加检测项目，1，遇盲孔完全在埋孔里的孔（包含在埋孔钻带内的镭射孔），
        报告出来显示位置，并提醒反馈给MI问客是否删除。举例：镭射S4-5在B4-10的埋孔上时，报警提醒
        2，遇盲孔在埋孔上，没有被埋孔钻带包含的孔，报告出来显示位置，并提醒需要移孔，或流程埋孔有树脂塞+盖孔电镀时，
        不需要移孔，举例：镭射s3-4在B4-10埋孔的孔上时，"""
        
        if "panel" in matrixinfo["gCOLstep_name"]:            
            setsteps = get_panelset_sr_step(jobname, "panel")
            dic_zu_layer = {}
            arraylist = []
            get_mrp_names = get_mrp_name(job.name.upper().split("-")[0])
            data_info = get_inplan_all_flow(job.name.upper().split("-")[0], select_dic=True)
            drill_info = get_drill_info_detail(job.name.upper().split("-")[0])
            
            erp_laser_drills = [info["ODB_DRILL_NAME"] for info in drill_info]
            #if "-lyh" in job.name:                
                #job.PAUSE(str([get_mrp_names, len(data_info)]))
            
            for stepname in setsteps:
                
                #if "icg" in stepname or "coupon-qp" in stepname or stepname in ["coupon1", "coupon2"]:
                    #continue
                
                step = gClasses.Step(job, stepname)
                step.open()     
                step.COM("units,type=mm")
                
                drill_layers = mai_drill_layers + mai_man_drill_layers + ["drl", "cdc", "cds"]
                # self.get_layer_hole_to_hole_info(step, drill_layers)
                
                for mai_drill in drill_layers:
                    if not step.isLayer(mai_drill):
                        continue
                    mrp_name = ""
                    result = re.findall("[bm](\d+)-(\d+)", mai_drill)
                    if mai_drill not in ["drl", "cdc", "cds"]:
                        drill_name = u"埋孔"
                        a, b = result[0]
                        a = int(a)
                        b = int(b)                            
                        for dic_mrp in get_mrp_names:
                            if dic_mrp["MRP_NAME"] is None:
                                continue
                            if "-" in dic_mrp["MRP_NAME"]:
                                start = dic_mrp["MRP_NAME"].split("-")[1][1:3]
                                end = dic_mrp["MRP_NAME"].split("-")[1][3:5]
                                if a < b:
                                    if a == int(start):
                                        mrp_name = dic_mrp["MRP_NAME"]
                                        break
                                else:
                                    if a == int(end):
                                        mrp_name = dic_mrp["MRP_NAME"]
                                        break                                    
                    else:
                        drill_name = u"通孔"
                        result = [(1, lay_num)]
                        mrp_name = job.name.upper().split("-")[0]
                    
                    has_plug_gaikong = False
                  
                    if mrp_name:
                        drill_name = drill_name + "(" + mrp_name + ")"
                        
                        process1 = [dic_info for dic_info in data_info
                                   if dic_info["MRP_NAME"] == mrp_name
                                   and u"树脂塞孔" in dic_info["WORK_CENTER_CODE"].decode("utf8")]
                        process2 = [dic_info for dic_info in data_info
                                   if dic_info["MRP_NAME"] == mrp_name
                                   and u"盖孔电镀" in dic_info["WORK_CENTER_CODE"].decode("utf8")]
                        if process1 and process2:
                            has_plug_gaikong = True
                            
                    #if "-lyh" in job.name:                
                        #job.PAUSE(str([mrp_name, has_plug_gaikong]))
                        
                    laser_drill_outer_mai_layers = []
                    laser_drill_inner_mai_layers = []                    
                    if result:
                        a, b = result[0]
                        a = int(a)
                        b = int(b)
                        if a < b:                            
                            for i in range(1, 5):                                
                                laser_drill_top = "s{0}-{1}".format(a-i, a)
                                laser_drill_bot = "s{0}-{1}".format(b+i, b)
                                if step.isLayer(laser_drill_top):                                    
                                    laser_drill_outer_mai_layers.append(laser_drill_top)
                                if step.isLayer(laser_drill_bot):   
                                    laser_drill_outer_mai_layers.append(laser_drill_bot)
                                    
                                laser_drill_top = "s{0}-{1}".format(a, a+i)
                                laser_drill_bot = "s{0}-{1}".format(b, b-i)
                                if step.isLayer(laser_drill_top):                                    
                                    laser_drill_inner_mai_layers.append(laser_drill_top)
                                if step.isLayer(laser_drill_bot):   
                                    laser_drill_inner_mai_layers.append(laser_drill_bot)                                    
                        else:
                            for i in range(1, 5):                                
                                laser_drill_top = "s{0}-{1}".format(b-i, b)
                                laser_drill_bot = "s{0}-{1}".format(a+i, a)
                                if step.isLayer(laser_drill_top):                                    
                                    laser_drill_outer_mai_layers.append(laser_drill_top)
                                if step.isLayer(laser_drill_bot):   
                                    laser_drill_outer_mai_layers.append(laser_drill_bot)
                                    
                                laser_drill_top = "s{0}-{1}".format(b, b+i)
                                laser_drill_bot = "s{0}-{1}".format(a, a-i)
                                if step.isLayer(laser_drill_top):                                    
                                    laser_drill_inner_mai_layers.append(laser_drill_top)
                                if step.isLayer(laser_drill_bot):   
                                    laser_drill_inner_mai_layers.append(laser_drill_bot)
                    #if "-lyh" in job.name:                
                        #job.PAUSE(str([mai_drill, laser_drill_inner_mai_layers, laser_drill_outer_mai_layers]))                                
                    if laser_drill_inner_mai_layers or laser_drill_outer_mai_layers:
                        for laser_drill in laser_drill_inner_mai_layers + laser_drill_outer_mai_layers:
                            
                            if laser_drill not in laser_drill_layers and \
                               laser_drill not in erp_laser_drills:
                                    continue
                            
                            step.clearAll()
                            step.resetFilter()
                            step.affect(laser_drill)
                            step.refSelectFilter(mai_drill)
                            if step.featureSelected():
                                step.removeLayer(laser_drill+"_tmp_find")
                                step.copySel(laser_drill+"_tmp_find")
                                
                            step.refSelectFilter(mai_drill)                                
                            step.COM("profile_to_rout,layer=outline_tmp,width=508")   
                            if "coupon-qp" in stepname: 
                                if step.isLayer(laser_drill+"_tmp_find"):
                                    step.clearAll()
                                    step.affect(laser_drill+"_tmp_find")                                                             
                                    step.refSelectFilter("outline_tmp", mode="cover")
                                    if step.featureSelected():
                                        step.selectDelete()
                                        
                                    step.clearAll()
                                    step.affect(laser_drill)
                                    step.refSelectFilter(laser_drill+"_tmp_find")
                                
                            if step.featureSelected():
                                log = u"检测到{3} {0}镭射钻孔被{1}{2}钻到，请检查是否异常，并反馈给MI问客是否删除！"
                                if laser_drill in laser_drill_outer_mai_layers:
                                    log = u"检测到{3} {0}镭射钻孔钻在{1}{2}上，但未全被{2}钻带包含，请检查是否需要移孔，或检查流程埋孔是否有树脂塞+盖孔电镀，则不需要移孔！"
                                    if has_plug_gaikong:
                                        continue
                                
                                if "icg" in stepname and mai_drill in ["drl", "cdc", "cds"]:
                                    continue
                                
                                arraylist.append(log.format(laser_drill, mai_drill, drill_name, stepname))
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, laser_drill,
                                                                                     mai_drill,log.format(laser_drill, mai_drill, drill_name, stepname),
                                                                                     dic_zu_layer) 
                            
                            # if laser_drill in laser_drill_inner_mai_layers:
                            ref_layer = "{0}_resize_4mil".format(mai_drill)
                            #if step.isLayer(ms_layer):
                            step.copyLayer(job.name, step.name, mai_drill, ref_layer)
                            step.clearAll()
                            step.affect(ref_layer)
                            step.resetFilter()
                            step.COM("sel_delete_atr,attributes=.rout_chain")
                            step.COM("sel_resize,size={0}".format(3.99*25.4*2))
                            
                            step.clearAll()
                            step.resetFilter()
                            step.affect(laser_drill)
                            step.refSelectFilter(ref_layer)
                            if step.featureSelected():
                                step.removeLayer(laser_drill+"_close_hole")
                                step.copySel(laser_drill+"_close_hole")
                                step.clearAll()
                                step.affect(laser_drill+"_close_hole")
                                step.resetFilter()
                                if step.isLayer(laser_drill+"_tmp_find"):
                                    step.refSelectFilter(laser_drill+"_tmp_find")
                                    if step.featureSelected():
                                        step.selectDelete()
                                        
                                if "coupon-qp" in stepname:
                                    step.refSelectFilter("outline_tmp", mode="cover")
                                    if step.featureSelected():
                                        step.selectDelete()                                    
                                        
                                step.clearAll()
                                step.affect(laser_drill)
                                step.refSelectFilter(laser_drill+"_close_hole")
                            
                            if step.featureSelected():                                    
                                # step.PAUSE("dd")
                                log = u"检测到{3} {0}镭射钻孔跟{1}{2}孔间距小于4mil，请检查是否异常，并反馈给MI问客是否删除！"
                                if laser_drill in laser_drill_outer_mai_layers:
                                    if has_plug_gaikong:
                                        continue                                
                                    
                                if "icg" in stepname and mai_drill in ["drl", "cdc", "cds"]:
                                    continue                                
                                        
                                arraylist.append(log.format(laser_drill, mai_drill, drill_name, stepname))
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, laser_drill,
                                                                                     mai_drill,log.format(laser_drill, mai_drill, drill_name, stepname),
                                                                                     dic_zu_layer)
                                    
                            step.removeLayer(laser_drill+"_tmp_find")
                            step.removeLayer(laser_drill+"_close_hole")
                            step.removeLayer("{0}_resize_4mil".format(mai_drill))
                            
            if arraylist:
                #if "-lyh" in job.name:
                
                #showMessageInfo(*arraylist)
                #self.view_note_detail(dic_zu_layer)
                    
                return arraylist, dic_zu_layer
            
            return "success", None
        
    def get_layer_hole_to_hole_info(self, step, drill_layers):
        """获取各层的孔到孔之间的距离"""
        stepname = step.name
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")        
        matrixInfo = job.matrix.getInfo()        
        for layer in matrixInfo["gROWname"]:
            if "ms_2_" in layer or "mk_2_" in layer:
                step.removeLayer(layer)
        
        step.clearAll()
        for layer in laser_drill_layers:            
            step.affect(layer)
        
        step.COM('cur_atr_reset')
        step.COM('cur_atr_set,attribute=.drill,option=via')
        step.COM('cur_atr_set,attribute=.via_type,option=laser')
        step.COM('sel_change_atr,mode=add')
        step.COM('cur_atr_reset')
        step.clearAll()
        
        chklist = "checklist_space"
        step.COM("chklist_from_lib,chklist=hdi-drc,profile=none,customer=")
        step.COM("chklist_delete,chklist={0}".format(chklist))
        step.COM("chklist_create,chklist={0},allow_save=no".format(chklist))
        step.COM("chklist_open,chklist=hdi-drc")
        step.COM("chklist_show,chklist=hdi-drc,nact=2,pinned=no,pinned_enabled=yes")
        
        step.COM("""chklist_cupd,chklist=hdi-drc,nact=2,
        params=((pp_operation_modes=Single\;Cross)(pp_layers_all=Board)
        (pp_input_layer=.type=drill&context=board)(pp_1_element=Via)
        (pp_2_element=Via\;PTH\;NPTH\;Rout)(pp_7_element=Laser Via)
        (pp_8_element=Laser Via\;Via\;PTH\;NPTH\;Rout)(pp_3_element=PTH)
        (pp_4_element=PTH\;NPTH\;Rout)(pp_5_element=NPTH)(pp_6_element=NPTH\;Rout)
        (pp_use_compensated_rout=Yes)),mode=regular""")
        
        step.COM("chklist_run,chklist=hdi-drc,nact=2,area=profile")
        step.COM("chklist_pclear")
        step.COM("chklist_pcopy,chklist=hdi-drc,nact=2")
        step.COM("chklist_close,chklist=hdi-drc,mode=hide")
        step.COM("show_tab,tab=Checklists,show=no")
        
        step.COM("chklist_create,chklist=checklist_space")
        step.COM("chklist_ppaste,chklist=checklist_space,row=0")
        step.COM("chklist_create_lyrs,chklist=checklist_space,severity=3,suffix=ref")
        step.COM("chklist_close,chklist=checklist_space,mode=hide")

        for worklayer in drill_layers:
            
            step.clearAll()
            ref_layer = "{0}_hole2hole".format(worklayer)
            step.removeLayer(ref_layer)
            for layer in matrixInfo["gROWname"]:                
                if "ms_2" in layer and worklayer in layer:
                    step.affect(layer)
                    step.resetFilter()
                    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=close_lvia2via_same_net")
                    step.selectAll()
                    step.resetFilter()
                    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=close_lvia2via_diff_net")          
                    step.selectAll()
                    step.resetFilter()  
                    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=close_lvia2pth_same_net")
                    step.selectAll()
                    step.resetFilter()
                    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=close_lvia2pth_diff_net")          
                    step.selectAll()               
                    if step.featureSelected():
                        step.copySel(ref_layer)
                        
            if step.isLayer(ref_layer):
                step.clearAll()
                step.affect(ref_layer)
                step.COM("filter_set,filter_name=popup,update_popup=yes,slot=line,slot_by=length,min_len={0},max_len=1000".format(3.99*0.0254))
                step.selectAll()
                if step.featureSelected():
                    step.selectDelete()
        
        step.clearAll()
            
    def check_trace_barcode_coordinate_info(self):
        """检测全流程追溯二维码坐标信息是否上传"""
        stepname = "panel"
        arraylist = []
        exists_info = self.get_exists_coordinate_info(job.name, select_dic=True)
        if stepname in matrixinfo["gCOLstep_name"]:            
            step = gClasses.Step(job, stepname)
            step.open()
            f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
            rect= get_sr_area_for_step_include(stepname, include_sr_step=["edit", "set", "icg"])
            sr_xmin = min([min(x1, x2) for x1, y1, x2, y2 in rect])    
            sr_ymin = min([min(y1, y2) for x1, y1, x2, y2 in rect])   
            sr_xmax = max([max(x1, x2) for x1, y1, x2, y2 in rect])    
            sr_ymax = max([max(y1, y2) for x1, y1, x2, y2 in rect])
            
            # 获取脚线区域 判断有小sr的区域
            step.COM("units,type=mm")
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
            
            array_mrp_info = get_inplan_mrp_info(job.name)            
            dic_attr = {"bar_code_innerl2l3": "innerl2l3",
                        "bar_code_sec": "inner",
                        "bar_code_out": "out",}
            
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
                #else:                
                    #out_lb_x = (f_xmax - pnl_routx) * 0.5
                    #out_lb_y = (f_ymax - pnl_routy) * 0.5
                    
                # 重新定义 以第一次压合尺寸来计算 mes通过其他锣边跟第一次锣边的距离来计算后续压合的数据 20241008 by lyh
                if dic_info["PROCESS_NUM"] - 1 == 1:
                    if pnl_routx > 0 and pnl_routy > 0:
                        out_lb_x = (f_xmax - pnl_routx) * 0.5
                        out_lb_y = (f_ymax - pnl_routy) * 0.5                 
                    
            if lay_num <= 2:
                # 双面板没有修边尺寸
                out_lb_x = 0
                out_lb_y = 0                
                        
            # 取几次锣边的平均值
            if all_sec_rout_x:
                out_lb_sec_x = float(sum(all_sec_rout_x)) / len(all_sec_rout_x)
                
            if all_sec_rout_y:
                out_lb_sec_y = float(sum(all_sec_rout_y)) / len(all_sec_rout_y)
                
            x_center = (f_xmin + f_xmax) * 0.5
            y_center = (f_ymin + f_ymax) * 0.5
            
            dic_exists_info = {}
            if exists_info:
                dic_exists_info = eval(exists_info[0]["trace_code_coordinates"])
            
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
                dic_zu = {}
                for obj in featout:
                    if obj.y + 6.5 *0.5 > f_ymax * 0.5 + 100 or obj.y - 6.5 *0.5 < f_ymax * 0.5 - 100:
                        log = u"检测到此型号{0}有添加全流程二维码坐标超出中心Y范围100mm，物件属性(.string={1})，请检查是否异常！".format(job.name, obj.string)
                        arraylist.append(log)
                    
                    if obj.x + 6.5 * 0.5 > sr_xmin - 1:
                        log = u"检测到此型号{0}有添加全流程二维码坐标距单元内X范围不足1mm，物件属性(.string={1})，请检查是否异常！".format(job.name, obj.string)
                        arraylist.append(log)
                        
                    if obj.x - f_xmin > 25:
                        log = u"检测到此型号{0}有添加板边加的全流程追溯二维码中心距发料边X范围超25mm，物件属性(.string={1})，请检查是否异常！".format(job.name, obj.string)
                        arraylist.append(log)                        
                        
                    if dic_attr.get(obj.string, None):                
                        if obj.string == "bar_code_out":
                            # 二位码坐标定义：压合裁膜后的这个机械钻码机是以二维码的左上角来定义二维码位置坐标的
                            # 因外层进板方向跟芯板不一样 外层 x 跟y方向要对调
                            # x方向要从原点开始计算 而不是板中心                    
                            dic_zu[dic_attr[obj.string]+"_x"] = round(obj.y - 6.5 * 0.5 - out_lb_y, 2)
                            dic_zu[dic_attr[obj.string]+"_y"] = round(obj.x - 6.5 * 0.5 - out_lb_x, 2)
                            #if "-lyh" in job.name:
                                #job.PAUSE(str([obj.x, obj.y, out_lb_x, out_lb_y, dic_zu[dic_attr[obj.string]+"_x"], dic_zu[dic_attr[obj.string]+"_y"]]))
                            
                        elif obj.string == "bar_code_innerl2l3" or obj.string == "bar_code_sec":
                            # 二位码坐标定义：是进料边的这一侧二维码边的中心点
                            dic_zu[dic_attr[obj.string]+"_x"] = round(obj.x - 5 * 0.5, 2)
                            dic_zu[dic_attr[obj.string]+"_y"] = round(obj.y - y_center, 2)
                        # else:
                            # 二位码坐标定义：压合裁膜后的这个机械钻码机是以二维码的左上角来定义二维码位置坐标的
                            # 因次外层进板方向跟芯板不一样 次外层 x 跟y方向要对调
                            # x方向要从原点开始计算 而不是板中心
                            #dic_zu[dic_attr[obj.string]+"_x"] = round(obj.y - 5 * 0.5 - out_lb_sec_y, 2)
                            #dic_zu[dic_attr[obj.string]+"_y"] = round(obj.x - 5 * 0.5 - out_lb_sec_x, 2)
                
                log = u"\n检测到此型号{0} MES内的坐标信息跟板内不一致，请检查二维码是否被移动没有重新上传数据，请重新运行上传程序！".format(job.name)
                add_log = False
                for key, value in dic_exists_info.iteritems():
                    # print [key, value]
                    if key[:-2] in dic_attr.values():                        
                        if abs(dic_zu.get(key, 0) - float(value)) > 1:
                            add_log = True
                            log += u"\nMES坐标信息{0}:{1}".format(key, value)
                            log += u"\nTGZ坐标信息{0}:{1}".format(key, dic_zu.get(key, 0))
                            
                if add_log:                    
                    arraylist.append(log)                        
                    
                if exists_info:
                    pass
                else:
                    step.clearAll()
                    log = u"检测到此型号{0}有加全流程追溯二维码，但未上传坐标信息到MES系统，请运行上传程序！".format(job.name)
                    arraylist.append(log)
            else:
                if exists_info:
                    step.clearAll()
                    log = u"检测到此型号{0} MES系统有上传坐标信息，但板边未加全流程追溯二维码位置属性\n(.string,text=bar_code_innerl2l3 或 .string,text=bar_code_sec 或 .string,text=bar_code_out)，请重新运行添加程序！".format(job.name)
                    arraylist.append(log)
                else:
                    array_jobtype_info = get_job_type(job.name)
                    car_type = [info for info in array_jobtype_info
                                if (info["JOB_PRODUCT_LEVEL1_"] and u"汽车" in info["JOB_PRODUCT_LEVEL1_"].decode("utf8"))
                                or info["ES_CAR_BOARD_"] == 1]
                    
                    if job.name[1:4] in ["183", 'a86', 'd10']:
                        log = u"{0}系列要求添加板边全流程追溯码，此板未添加".format(job.name[1:4])
                        arraylist.append(log)
                        
                    if job.name.startswith("q") or car_type:
                        log = u"汽车板 要求添加板边全流程追溯码，此板未添加！"
                        arraylist.append(log)                        

            step.clearAll()
            
        if arraylist:
            return arraylist, None
            
        return "success", None
    
    def compare_mi_cam_gold_area_diff(self, *args):
        """MI与cam电镀金面积比对异常推送"""
        has_gold_finger = False
        
        data_info = get_inplan_all_flow(job.name.upper(), True)
        ganmo_process = [dic_info for dic_info in data_info
                        if u"选化干膜" in dic_info["WORK_CENTER_CODE"].decode("utf8") or \
                        u"选镀干膜" in dic_info["WORK_CENTER_CODE"].decode("utf8") ]
        shimo_process = [dic_info for dic_info in data_info
                        if u"印选化油" in dic_info["WORK_CENTER_CODE"].decode("utf8")]
        has_jsz_process = [dic_info for dic_info in data_info
                        if u"电镀镍金" in dic_info["WORK_CENTER_CODE"].decode("utf8")]
        # print(ganmo_process)
        # print(shimo_process)
        worklayers = []
        for i, layer in enumerate(matrixinfo["gROWname"]):
            if matrixinfo["gROWcontext"][i] == "board":
                if ganmo_process:                    
                    if layer in ["gold-c", "gold-s"]:
                        index = matrixinfo["gROWname"].index(layer)
                        if matrixinfo["gROWcontext"][index] != "board":
                            continue
                        worklayers.append(layer)
                        has_gold_finger = True
                        
                if shimo_process:
                    if layer in ["linek-c-1", "linek-s-1", "linek-c", "linek-s"]:
                        index = matrixinfo["gROWname"].index(layer)
                        if matrixinfo["gROWcontext"][index] != "board":
                            continue
                        worklayers.append(layer)
                        has_gold_finger = True
        
        # if has_jsz_process and has_gold_finger:
            
        
        arraylist_test = [job.name]
        
        if has_jsz_process:
            
            data_info = get_inplan_gold_area(job.name)
            # job.PAUSE(str(data_info))
            if "set" in matrixinfo["gCOLstep_name"]:
                pnl_step = "set"
                set_step = "edit"
            else:
                pnl_step = "panel"
                set_step = "edit"
            
            dic_job_info = getJobData(jobname.upper())
            thickness = dic_job_info.get("out_thick", 0)            
            dic_calc_layer = {"l1": "gold-c_cal_area","l{0}".format(lay_num): "gold-s_cal_area",}        
            
            arraylist = []
            ding_arraylist = []            
            for gold_layer in worklayers:
                    
                step = gClasses.Step(job, set_step)
                step.open()
                step.COM("units,type=mm")
                if gold_layer in ["gold-c", "gold-s"]:                        
                    symbolname = get_panel_features_in_set_position(jobname, set_step, pnl_step,
                                                                    gold_layer+"-tmp", gold_layer,
                                                                    create_symbol="yes")
                else:
                    step.clearAll()
                    step.removeLayer(gold_layer+"_tmp")
                          
                    step.copyLayer(job.name, step.name, gold_layer, gold_layer+"_tmp")
                        
                    step.affect(gold_layer+"_tmp")
                    step.contourize()
                    #step.resetFilter()
                    #step.selectAll()
                    #if step.featureSelected() > 2:
                        ##with open("d:/tmp/error.log", "a") as f:
                            ##f.write(job.name+"\n")                            
                        #continue
                    
                    #if step.featureSelected() == 2:
                        #select_index = 0
                        #area = 0
                        #for index in [1, 2]:
                            #step.selectNone()
                            #step.selectFeatureIndex(gold_layer+"_tmp", index)
                            #x1, y1, x2, y2  = get_layer_selected_limits(step, gold_layer+"_tmp")
                            #if area == 0:
                                #area = abs(x2 - x1) *abs(y2-y1)
                                #select_index = index
                            #else:
                                #if abs(x2 - x1) *abs(y2-y1) < area:                                        
                                    #select_index = index
                        
                        #step.selectNone()
                        #step.selectFeatureIndex(gold_layer+"_tmp", select_index)
                        
                    step.COM("sel_create_sym,symbol=cal_gold_area_positoin,x_datum=0,y_datum=0,"
                                 "delete=no,fill_dx=2.54,fill_dy=2.54,attach_atr=no,retain_atr=no")
                    symbolname = "cal_gold_area_positoin"                            
                    
                drillLayers = []
                if step.isLayer("drl"):    
                    drillLayers = ["drl"]
                    if step.isLayer("cdc"):
                        drillLayers = ["cdc"]
                    if step.isLayer("cds"):
                        drillLayers = ["cds"]
                        
                if symbolname != "error":
                    step.removeLayer(gold_layer+"_cal_area")
                    step.clearAll()
                    if gold_layer in ["gold-c", "gold-s"]:           
                        step.copyLayer(job.name, step.name, gold_layer, gold_layer+"_cal_area")
                    else:
                        step.createLayer(gold_layer+"_cal_area")
                        
                    step.affect(gold_layer+"_cal_area")
                    if symbolname is not None:                            
                        step.addPad(0, 0, symbolname)
                        
                    step.COM("sel_break")
                    step.resetFilter()
                    step.filter_set(feat_types='line;arc', polarity='positive')
                    step.selectSymbol("r10", 1, 1)
                    if step.featureSelected():
                        step.selectDelete()
                        
                    step.copyLayer(job.name, step.name, gold_layer+"_cal_area", gold_layer+"_cal_area_bak")
                    clip_mask_layer = ""
                    if "-c" in gold_layer:
                        if step.isLayer("m1"):
                            clip_mask_layer = "m1"
                        else:
                            if step.isLayer("m1-1"):
                                clip_mask_layer = "m1-1"
                    else:
                        if step.isLayer("m2"):
                            clip_mask_layer = "m2"
                        else:
                            if step.isLayer("m2-1"):
                                clip_mask_layer = "m2-1"
                    
                    if clip_mask_layer:
                        step.clearAll()
                        step.removeLayer(clip_mask_layer+"_tmp")
                        step.copyLayer(job.name, step.name, clip_mask_layer, clip_mask_layer+"_tmp")
                        step.affect(clip_mask_layer+"_tmp")
                        step.contourize()
                        step.clearAll()
                        step.affect(gold_layer+"_cal_area_bak")
                        step.COM("clip_area_end,layers_mode=layer_name,layer={0},"
                                 "area=reference,area_type=rectangle,inout=inside,"
                                 "contour_cut=no,margin=0,ref_layer={1},"
                                 "feat_types=line\;pad\;surface\;arc\;text,".format(gold_layer+"_cal_area_bak",
                                                                        clip_mask_layer+"_tmp"))
                        
                        step.copyToLayer(gold_layer+"_cal_area", invert="yes")                       
                        
                        step.clearAll()
                        step.affect(gold_layer+"_cal_area")
                        step.contourize()
                        #step.resetFilter()
                        #step.selectAll()
                        #count = step.featureSelected()
                        
                        ##选取最大的一块保留
                        #dic_index = {}
                        #for index in range(count):
                            #step.selectNone()
                            #step.selectFeatureIndex(gold_layer+"_cal_area", index+1)
                            #x1, y1, x2, y2 = get_layer_selected_limits(step, gold_layer+"_cal_area")
                            #area = abs(x2 - x1) *abs(y2-y1)
                            ## job.PAUSE(str([index+1, area]))
                            #dic_index[index+1] = area

                        #select_index = sorted(dic_index.keys(), key=lambda x: dic_index[x])[-1]
                        #step.selectNone()
                        #step.selectFeatureIndex(gold_layer+"_cal_area", select_index)
                        #if step.featureSelected():
                            #step.COM("sel_reverse")
                            #if step.featureSelected():
                                #step.selectDelete()
                                
                        step.COM("clip_area_end,layers_mode=layer_name,"
                                 "layer={0},area=profile,area_type=rectangle,"
                                 "inout=outside,contour_cut=yes,margin=0,"
                                 "feat_types=line\;pad\;surface\;arc\;text".format(gold_layer+"_cal_area"))
                        
                        step.removeLayer(clip_mask_layer+"_tmp")
                        
                        step.COM("sel_resize,size=-1500")
                        step.COM("sel_resize,size=1500")
                        
                    for sig_layer in sorted(dic_calc_layer.keys()):
                        mask_layer = gold_layer+"_cal_area"
                        # if mask_layer == gold_layer+"_cal_area":
                        if ("-c" in gold_layer and "-c" in dic_calc_layer[sig_layer] ) or ("-s" in gold_layer and "-s" in dic_calc_layer[sig_layer]):
                            
                            get_sr_area_flatten("fill_sur_tmp", stepname=step.name)
                            step.clearAll()
                            step.affect("fill_sur_tmp")
                            step.COM("sel_resize,size=1000")
                            step.COM("sel_surf2outline,width=1")
                            step.clearAll()
                            step.affect(sig_layer)
                            step.resetFilter()
                            step.filter_set(feat_types='line', polarity='positive')
                            step.refSelectFilter("fill_sur_tmp")
                            if step.featureSelected():
                                step.copySel("n_electric_line")
                                step.clearAll()
                                step.affect(mask_layer)
                                step.resetFilter()
                                step.refSelectFilter("n_electric_line", mode="disjoint")
                                if step.featureSelected():
                                    step.selectDelete()
                            
                            net_step = gClasses.Step(job, "net")
                            net_step.open()
                            net_step.copyLayer(job.name, "edit", mask_layer, mask_layer)
                            
                            net_step.clearAll()
                            net_step.affect(sig_layer)
                            net_step.resetFilter()
                            net_step.filter_set(feat_types='line', polarity='positive')
                            net_step.setAttrFilter(".n_electric")
                            net_step.selectAll()
                            if net_step.featureSelected():
                                net_step.selectDelete()
                            
                            if "-c" in gold_layer:                                    
                                mianji, percent = calcExposeArea(net_step, sig_layer, mask_layer, "", "", thickness, drillLayers=drillLayers)
                            else:
                                mianji, percent = calcExposeArea(net_step, "", "",sig_layer, mask_layer,  thickness, drillLayers=drillLayers)
                            # print(gold_layer, data_info, mianji, percent)
                            if "-c" in gold_layer:
                                key = "GOLD_C"
                            else:
                                key = "GOLD_S"
                            
                            for dic_info in data_info:
                                if dic_info.get(key):
                                    inplan_mianji = dic_info[key]
                                    arraylist_test.append(str(inplan_mianji))
                                    arraylist_test.append(str(mianji))
                                    diff_percent = abs(float(mianji) - inplan_mianji) / float(inplan_mianji)
                                    # job.PAUSE(str([inplan_mianji, mianji, diff_percent * 100]))
                                    if diff_percent * 100 > 10:
                                        log = u"检测型号{0} {4}层中inplan镀金面积{1} 跟CAM资料镀金面积{2} 差异{3}%大于10%，请反馈领导处理！"                                            
                                        arraylist.append(log.format(job.name, inplan_mianji, mianji, "%.1f" % (diff_percent*100), sig_layer))
                                        ding_log = u"检测型号{0} {4}层中inplan镀金面积{1} 跟CAM资料镀金面积{2} 差异{3}%大于10%，请相关人员知悉并反馈领导处理！"
                                        ding_arraylist.append(ding_log.format(job.name, inplan_mianji, mianji, "%.1f" % (diff_percent*100), sig_layer))

                #step.removeLayer(gold_layer+"_cal_area")
                #step.removeLayer(gold_layer+"_cal_area_bak")
                #step.removeLayer(gold_layer+"-tmp")
                    
            if arraylist:
                showMessageInfo(*arraylist)
                # https://oapi.dingtalk.com/robot/send?access_token=a996971f65ddd1f035a526621a732aa9b09c2006fa798fa17a233ea005a830a1
                with open("d:/tmp/diff_job.log", "a") as f:
                    f.write("\n".join(ding_arraylist).encode("cp936") + "\n")
                #ding_app.sent_markdown("",
                        #"https://oapi.dingtalk.com/robot/send?access_token=a996971f65ddd1f035a526621a732aa9b09c2006fa798fa17a233ea005a830a1",
                        #"<br>".join(ding_arraylist).encode("utf8"),
                        #u"镀金面积 差异提醒".encode("utf8"), [])
                # return arraylist, None
        #else:
            #with open("d:/tmp/no_finger_jobs.log", "w") as f:
                #f.write(job.name+"\n")
        
        with open("d:/tmp/job_area_value.log", "a") as f:
            f.write(",".join(arraylist_test) + "\n")
            
        return "success", None
    
    def check_exists_coupon_for_customer(self, customer=None):
        """检测特殊客户是否添加测试模块"""
        arraylist = []
        all_steps = get_panelset_sr_step(job.name, "panel")
        if job.name[1:4] == "676":
            
            array_mrp_drl_info_detail = get_ks_bd_target_info_detail(job.name.upper())            
            has_pth_hole = [x["ODB_DRILL_NAME"] for x in array_mrp_drl_info_detail                                 
                             if x["DRILL_TYPE"] == "Mechanical"
                             and x["DRILL_LAYER_"] == u"一次钻孔".encode("utf8")
                             and x["TYPE_T"] in '\"PTH\",\"Via\",\"Micro Via\",\"Plated Slot\"'
                             and x["PCB_COUNT"] > 0]
            
            log = ""
            if not has_pth_hole:                
                if "plating_hole_coupon" not in all_steps :                 
                    log = u"676客户要求 板内无pth孔时需添加电镀孔coupon: plating_hole_coupon，此板未添加！"
            else:
                if "dzd_cp" not in all_steps :
                    log = u"676客户要求 板内有pth孔时需添加对准度模块coupon: dzd_cp，此板未添加！"
                
            if log:                
                arraylist.append(log)
                
        if job.name[1:4] == "a15" and customer == "a15":
            if "bhast-coupon" not in "".join(all_steps):
                log = u"a15客户要求 添加测试coupon: bhast-coupon，此板未添加！"
                arraylist.append(log)
                
            if "cu-coupon" not in all_steps :
                log = u"a15客户要求 添加拉力测试coupon: cu-coupon，此板未添加！"
                arraylist.append(log)                
        
        if arraylist:
            return arraylist, None
            
        return u"success", None
    
    def check_inner_barcode_is_right(self, tgz_file_path=None):
        """检测tgz的内层二维码 输出odb++是否symbol会异常 比如两张不同芯板 symbol名字一样 报警
        增加tgz的完整性检测 20240913 by lyh http://192.168.2.120:82/zentao/story-view-7425.html"""
        data_info = get_inplan_mrp_info(job.name.upper(), condtion="1=1")
        check_layers = []
        for dic_mrp_info in data_info:
            if dic_mrp_info["PROCESS_NUM"] == 1:
                if dic_mrp_info["FROMLAY"]:                    
                    from_lay = dic_mrp_info["FROMLAY"].lower()
                    check_layers.append(from_lay)
                if dic_mrp_info["TOLAY"]:                    
                    to_lay = dic_mrp_info["TOLAY"].lower()
                    check_layers.append(to_lay)
                    
        if tgz_file_path is not None:
            if not os.path.exists(tgz_file_path):
                return "success", None
            dic_layer_symbol = {}            
            
            try:
                tgz = tarfile.open(tgz_file_path, 'r:gz')
                # 获取.tgz文件中所有的成员（文件和目录）
                members = tgz.getmembers()
                # 遍历所有的成员
                for member in members:
                    # 检查是否是文件
                    if member.isfile():
                        for layer in check_layers:                
                            if "steps/panel/layers/{0}/features".format(layer) in member.name:                    
                                # 读取文件内容
                                f = tgz.extractfile(member)
                                # 打印文件名和内容
                                # print('File: {0}'.format(member.name))
                                # print('Content: {0}'.format(f.read()))
                                content = f.read()
                                symbols = [line.split(" ")[1] for line in content.split("\n")
                                           if line.startswith("$")]
                                find_symbols = [symbol for symbol in symbols
                                                if "barcode" in symbol]                    
                                dic_layer_symbol[layer] = find_symbols
                                
                                # 关闭文件对象
                                f.close()
            except (tarfile.ReadError, tarfile.TarError, KeyError, IOError) as e:
                log = u"检测到输出的tgz文件打开异常，程序将删除已产生的tgz文件，请重新输出！{0}".format(e)
                os.unlink(tgz_file_path)
                return [log], None
            
            finally:
                # 确保.tgz文件被关闭
                tgz.close()
                
            arraylist =[]
            exists_layers = []
            
            if len(check_layers) > 2:
                for key, value in dic_layer_symbol.iteritems():                
                    if key in exists_layers:
                        continue                
                    for key1, value1 in dic_layer_symbol.iteritems():
                        if key != key1:            
                            same_symbol = [x for x in value if x in value1]
                            if same_symbol:
                                arraylist.append(u"%s检测到tgz内%s层跟%s层二维码一样:%s，会造成产线抓取此二维码预叠防呆机制失效，\
                                有品质隐患，请检查层内二维码是否动态2！"%(jobname, key.upper(), key1.upper(), same_symbol))
                                exists_layers.append(key)
                                exists_layers.append(key1)
                            
            if arraylist:
                return arraylist, None                
            
            return "success", None                            

        if len(check_layers) > 2 and "panel" in matrixinfo["gCOLstep_name"]:
            step = gClasses.Step(job, "panel")
            step.open()
            barcode_names = []
            barcode_attr = []
            delete_attr = False
            dic_symbolname = {}
            arraylist = []
            for layer in check_layers:
                step.clearAll()
                step.affect(layer)
                step.resetFilter()
                step.selectSymbol("barcode*")
                if step.featureSelected():
                    layer_cmd = gClasses.Layer(step, layer)
                    feat_out = layer_cmd.featSelOut()["pads"]
                    for obj in feat_out:
                        if obj.symbol in barcode_names:
                            # step.PAUSE(str([layer, dic_symbolname[obj.symbol]]))
                            compare_layer = ""
                            for key, value in dic_symbolname.iteritems():
                                if key == obj.symbol:
                                    compare_layer = value
                            arraylist.append(u"检测到tgz内%s层跟%s层板边二维码一样:%s，<br>会造成产线抓取此二维码预叠防呆机制失效，有品质隐患，请检查层内板边二维码是否动态1！"%(layer.upper(), compare_layer, obj.symbol))
                            break
                    
                    for obj in feat_out:
                        barcode_names.append(obj.symbol)
                        # if not dic_symbolname.has_key(obj.symbol):                            
                        dic_symbolname[obj.symbol] = layer
                        
                step.resetFilter()
                step.filter_set(feat_types='text')
                step.selectAll()
                if step.featureSelected():
                    layer_cmd = gClasses.Layer(step, layer)
                    feat_out = layer_cmd.featout_dic_Index(options="feat_index+select")["barcodes"]
                    feat_out += layer_cmd.featout_dic_Index(options="feat_index+select")["text"]
                    for obj in feat_out:
                        if getattr(obj, "genesis_sym_name", "none") in barcode_attr:
                            delete_attr = True
                            
                    for obj in feat_out:
                        barcode_attr.append(getattr(obj, "genesis_sym_name", ""))                                                 
            
            step.clearAll()
            
            if delete_attr :
                step.clearAll()
                for layer in check_layers:
                    step.affect(layer)
                step.resetFilter()
                step.filter_set(feat_types='text')
                step.selectAll()
                if step.featureSelected():
                    step.COM("sel_delete_atr,attributes=.genesis_sym_name")
                    
                step.clearAll()
                # step.PAUSE("ddd")
                job.save()
                
            if arraylist:
                # showMessageInfo(*arraylist)
                return arraylist, None
            
        return "success", None
      
    def get_exists_coordinate_info(self, jobname, select_dic=False):
        if not select_dic:        
            sql = "select id from hdi_engineering.incam_mes_trace_code where job_name = '{0}'"
            result = conn.SQL_EXECUTE(dbc_m, sql.format(jobname.split("-")[0]))
        else:
            sql = "select * from hdi_engineering.incam_mes_trace_code where job_name = '{0}'"
            result = conn.SELECT_DIC(dbc_m, sql.format(jobname.split("-")[0]))        
        return result
    
    def check_mask_open_has_pad_in_signal_layer(self):
        """2.	Net里转pad是否正确（阻焊开窗pad对应都应有线路pad）"""
        stepname = "net"
        if stepname not in matrixinfo["gCOLstep_name"]:
            return u"net不存在", None
        
        step = gClasses.Step(job, stepname)
        step.open()        
        step.COM("zoom_home")
        
        for sig_lay in outsignalLayers:
            for mask_lay in solderMaskLayers:
                if sig_lay == "l1":
                    if mask_lay == "m1":
                        step.clearAll()
                        step.display(sig_lay)
                        step.display_layer(mask_lay, 2)
                        step.resetFilter()
                        step.filter_set(feat_types='pad', polarity='positive')
                        step.selectAll()
                        self.pause_check_result(step, u"请检查{0}阻焊开窗pad对应{1}是否都有线路pad！".format(mask_lay, sig_lay), delete_log_file=False)
                        # step.PAUSE(u"请检查{0}阻焊开窗pad对应{1}是否都有线路pad！".encode("utf8").format(mask_lay, sig_lay))
                        break
                else:
                    if mask_lay != "m1":
                        step.clearAll()
                        step.display(sig_lay)
                        step.display_layer(mask_lay, 2)
                        step.resetFilter()
                        step.filter_set(feat_types='pad', polarity='positive')
                        step.selectAll()
                        break
                    
        self.pause_check_result(step, u"请检查{0}阻焊开窗pad对应{1}是否都有线路pad！".format(mask_lay, sig_lay))
        step.clearAll()
        return u"人工检查完毕，若需单独查看请点击手动运行，按提示步骤进行检查", None
    
    def check_signal_exists_tear_drop(self):
        """Edit里线路是否加泪滴"""
        stepname = "edit"
        if stepname not in matrixinfo["gCOLstep_name"]:
            return u"edit不存在", None
        
        step = gClasses.Step(job, stepname)
        step.open()
        res = os.environ.get("INNER_OUTER", "inner")
        if res == "inner":
            check_layers = innersignalLayers
        else:
            check_layers = outsignalLayers
        
        step.clearAll()
        for layer in check_layers:
            step.affect(layer)
            
        step.resetFilter()
        step.setAttrFilter(".tear_drop")
        step.selectAll()
        if step.featureSelected():
            step.clearAll()
            return "success", None
        
        step.clearAll()
        return u"检测到edit中线路层{0}未添加泪滴，请检查是否异常".format(check_layers), None
    
    def check_out_layer_conditon(self):
        """4.	Out层的外形是否正确"""
        stepname = "edit"
        if stepname not in matrixinfo["gCOLstep_name"]:
            return u"edit不存在", None
        
        if "out" not in matrixinfo["gROWname"]:
            return u"out层不存在", None
        
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=inch")
        
        step.clearAll()
        step.display("out")
        step.COM("zoom_home")
        step.COM("sel_delete_atr,attributes=.rout_chain")
        step.changeSymbol("r4")
        step.display_layer("drl", 2)
        self.pause_check_result(step, u"请检查out层外形")
        
        return u"人工检查完毕，若需单独查看请点击手动运行，按提示步骤进行检查", None
    
    def check_Features_in_profile(self):
        """检测板内是否有东西"""
        
        res = os.environ.get("INNER_OUTER", "inner")            
        if "panel" in matrixinfo["gCOLstep_name"]:
            all_steps = [name for name in get_panelset_sr_step(jobname, "panel")]
        else:
            if "set" in matrixinfo["gCOLstep_name"]:
                all_steps = [name for name in get_panelset_sr_step(jobname, "set")]
            else:
                return u"panel 跟set 不存在，请检查", None
        
        arraylist = []
        dic_zu_layer = {}
        steps = ["set", "panel"]
        
        checklayers = [lay for i, lay in enumerate(matrixinfo["gROWname"])
                       if matrixinfo["gROWcontext"][i] == "board"]    

        drill_layers = [lay for i, lay in enumerate(matrixinfo["gROWname"])
                        if matrixinfo["gROWcontext"][i] == "board"
                        and matrixinfo["gROWlayer_type"][i] == "drill"]        
        # 测试
        # steps = ["set"]
        for stepname in steps:
            if stepname not in matrixinfo["gCOLstep_name"]:
                continue
            
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            step.removeLayer("patternfill")
            step.removeLayer("patternfill_flatten")
            step.removeLayer("outline_tmp")
            
            all_steps = [name for name in get_panelset_sr_step(jobname, stepname)]
            
            for editname in set(all_steps):
                # 尾孔不检测
                if editname in drill_layers:
                    continue
                editstep = gClasses.Step(job, editname)            
                editstep.open()
                editstep.COM("units,type=mm")
                editstep.clearAll()
                if not editstep.isLayer("patternfill"):
                    editstep.createLayer("patternfill")
                else:
                    editstep.COM("truncate_layer,layer=patternfill")
    
                editstep.affect("patternfill")
                editstep.reset_fill_params()
                if editname != "set": 
                    editstep.COM("sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,"
                                 "step_max_dist_x=2540,step_max_dist_y=2540,sr_margin_x=0,sr_margin_y=0,"
                                 "sr_max_dist_x=2540,sr_max_dist_y=2540,nest_sr=yes,stop_at_steps=,"
                                 "consider_feat=no,consider_drill=no,consider_rout=no,"
                                 "dest=affected_layers,attributes=no")
                else:
                    prof_xmin, prof_ymin, prof_xmax, prof_ymax = get_profile_limits(editstep)
                    editstep.addRectangle(prof_xmin, prof_ymin, prof_xmax, prof_ymax)
                    
                    editstep.COM("profile_to_rout,layer=outline_tmp,width=1")
                    editstep.clearAll()
                    editstep.affect("outline_tmp")
                    editstep.copyToLayer("patternfill", invert="yes")
                    editstep.clearAll()
                    editstep.affect("patternfill")
                    editstep.contourize()                    
                    editstep.COM("sel_decompose,overlap=no")
                    editstep.resetFilter()
                    editstep.COM("filter_set,filter_name=popup,update_popup=no,profile=out")
                    editstep.selectAll()
                    if editstep.featureSelected():
                        editstep.selectDelete()
                        
                    editstep.removeLayer("outline_tmp")
                    
                #set内 添加的模块内缩一点
                if stepname == "set":
                    if "edit" not in editname:
                        editstep.clearAll()
                        editstep.affect("patternfill")                        
                        editstep.COM("sel_resize,size=-500")
            
            if not step.isLayer("patternfill"):
                continue        
    
            if res == "outer":
                check_layers = checklayers
            else:
                check_layers = innersignalLayers + drill_layers	    

            step.clearAll()
            step.resetFilter()            
            step.COM("flatten_layer,source_layer=patternfill,target_layer=patternfill_flatten")
    
            for layer in set(check_layers):
                if not step.isLayer(layer):continue
                
                resize = 0
                if layer in ["p1", "p2"]:
                    resize = -1000
                    
                if layer in ["sgt-c", "sgt-s", "etch-c", "etch-s"]:
                    resize = -500                    
                
                if resize:                    
                    step.clearAll()
                    step.affect("patternfill_flatten")
                    step.COM("sel_resize,size={0}".format(resize))
                    
                step.clearAll()
                step.affect(layer)
    
                step.resetFilter()
                step.filter_set(feat_types='pad;line;arc;text')
                step.refSelectFilter("patternfill_flatten", mode="touch")

                #if layer == "drl" and stepname == "set" and face_tech in ["98", "26", "27"]:
                    #"""通孔层再检测是否 有掏断edit板外引线 例如：一厂100310266c0698a01 20191119 by lyh"""
                    #for checksiglayer in signalLayers:
                        #if step.isLayer(checksiglayer):
                            #if checksiglayer.endswith("n"):
                                #pol = "negative"
                            #else:
                                #pol = "positive"
    
                            #step.flatten_layer(checksiglayer, checksiglayer + "_tmp_check")
                            ## step.refSelectFilter(checksiglayer + "_tmp_check", mode="touch")
                            #step.COM("sel_ref_feat,layers=%s_tmp_check,use=filter,mode=touch,"
                                     #"pads_as=shape,f_types=line\;pad\;arc,polarity=%s,"
                            #"include_syms=,exclude_syms=" % (checksiglayer, pol))
                            #step.removeLayer(checksiglayer + "_tmp_check")
                if step.featureSelected():
                    log = u"检测到{0} {1}层内有元素进入单元内，请检查！".format(stepname, layer)
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, layer,
                                                                         layer, log, dic_zu_layer)                    
    
                # surface 不好取坐标 把surface挑出来 转成外形线 再打标记 20201112 by lyh
                step.resetFilter()
                step.selectNone()
                step.filter_set(feat_types='surface')
                step.refSelectFilter("patternfill_flatten", mode="touch")
                if step.featureSelected():
                    step.removeLayer(layer + "_surface")
                    step.copySel(layer + "_surface")
                    step.clearAll()
                    step.affect(layer + "_surface")
                    step.COM("sel_surf2outline,width=1")

                    #step.resetFilter()
                    #step.refSelectFilter("patternfill_flatten", mode="disjoint")
                    #if step.featureSelected():
                        #step.selectDelete()

                    step.resetFilter()
                    step.selectAll()
                    if step.featureSelected():
                        log = u"检测到{0} {1}层内有元素进入单元内，请检查！".format(stepname, layer)
                        if log not in arraylist:                            
                            arraylist.append(log)
                            
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, layer + "_surface",
                                                                             layer, log, dic_zu_layer, add_note_layer=layer) 
                    step.removeLayer(layer + "_surface")		
    
                
                if resize:                    
                    step.clearAll()
                    step.affect("patternfill_flatten")
                    step.COM("sel_resize,size={0}".format(resize*-1))                
            
            #step.removeLayer("patternfill_flatten")
            #step.removeLayer("patternfill")	
            step.clearAll()
            
        if arraylist:
            return arraylist, dic_zu_layer
        
        return "success", None
    
    def check_Features_Outside_profile(self):
        """检测板外是否有东西"""

        res = os.environ.get("INNER_OUTER", "inner")
        if "panel" in matrixinfo["gCOLstep_name"]:
            all_steps = [name for name in get_panelset_sr_step(jobname, "panel")]
        else:
            if "set" in matrixinfo["gCOLstep_name"]:
                all_steps = [name for name in get_panelset_sr_step(jobname, "set")]
            else:
                return u"panel 跟set 不存在，请检查", None
            
        if not all_steps:
            # 拼版内容为空时20230508
            if "edit" in matrixinfo["gCOLstep_name"]:
                all_steps.append("edit")
            if "set" in matrixinfo["gCOLstep_name"]:
                all_steps.append("set")                
            
        boardlayers = [lay for i, lay in enumerate(matrixinfo["gROWname"])
                       if matrixinfo["gROWcontext"][i] == "board"
                       and matrixinfo["gROWlayer_type"][i] != "rout"]

        other_layers = [lay for i, lay in enumerate(matrixinfo["gROWname"])
                        if matrixinfo["gROWcontext"][i] == "board"
                        and matrixinfo["gROWlayer_type"][i] == "solder_paste"]

        drill_layers = [lay for i, lay in enumerate(matrixinfo["gROWname"])
                        if matrixinfo["gROWcontext"][i] == "board"
                        and matrixinfo["gROWlayer_type"][i] == "drill"]

        if res == "outer":
            check_layers = boardlayers + solderMaskLayers + silkscreenLayers + other_layers
        else:
            check_layers = innersignalLayers + drill_layers	

        dic_zu_layer = {}
        arraylist = []        

        for stepname in set(all_steps):
            
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            
            step.clearAll()
            step.resetFilter()            
            if not step.isLayer("patternfill"):
                step.createLayer("patternfill")
            else:
                step.COM("truncate_layer,layer=patternfill")
    
            if "set" == stepname:
                """检测set板外物 是否进入另一个单元"""
                step.removeLayer("set_fill_outside_1.8")
                step.createLayer("set_fill_outside_1.8")
                step.affect("set_fill_outside_1.8")
                step.COM("profile_to_rout,layer=set_fill_outside_1.8,width=3000")
                step.contourize()
                step.COM("sel_surf2outline,width=2.54")
                step.COM("filter_set,filter_name=popup,update_popup=no,profile=out")
                step.selectAll()
                step.COM("sel_reverse")
                if step.featureSelected():
                    step.selectDelete()
                
                #因某些set内拼pcs不规则 填充会很慢 故此处用计算的方式获取set的填充
                all_steps = [name for name in get_panelset_sr_step(jobname, stepname)]                
                for editname in set(all_steps):
                    editstep = gClasses.Step(job, editname)            
                    editstep.open()
                    editstep.COM("units,type=mm")
                    editstep.clearAll()
                    if not editstep.isLayer("fill_tmp"):
                        editstep.createLayer("fill_tmp")
                    else:
                        editstep.COM("truncate_layer,layer=fill_tmp")
        
                    editstep.affect("fill_tmp")
                    editstep.reset_fill_params()                    
                    editstep.COM("sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,"
                                 "step_max_dist_x=2540,step_max_dist_y=2540,sr_margin_x=0,sr_margin_y=0,"
                                 "sr_max_dist_x=2540,sr_max_dist_y=2540,nest_sr=yes,stop_at_steps=,"
                                 "consider_feat=no,consider_drill=no,consider_rout=no,"
                                 "dest=affected_layers,attributes=no")
                
                step.clearAll()
                step.affect("patternfill")
                prof_xmin, prof_ymin, prof_xmax, prof_ymax = get_profile_limits(step)
                step.addRectangle(prof_xmin, prof_ymin, prof_xmax, prof_ymax)
                
                if step.isLayer("fill_tmp"):                    
                    step.flatten_layer("fill_tmp", "fill_tmp_flt")
                else:
                    get_sr_area_flatten("fill_tmp_flt", stepname=step.name)
                    
                step.clearAll()
                step.affect("fill_tmp_flt")
                step.copyToLayer("patternfill", invert="yes")                
                
                step.COM("profile_to_rout,layer=outline_tmp,width=1")
                step.clearAll()
                step.affect("outline_tmp")
                step.copyToLayer("patternfill", invert="yes")
                step.clearAll()
                step.affect("patternfill")
                step.contourize()                    
                step.COM("sel_decompose,overlap=no")
                step.resetFilter()
                step.COM("filter_set,filter_name=popup,update_popup=no,profile=out")
                step.selectAll()
                if step.featureSelected():
                    step.selectDelete()
                
                step.contourize()
                step.COM("sel_resize,size=508")
                step.removeLayer("fill_tmp")
                step.removeLayer("fill_tmp_flt")
                step.removeLayer("outline_tmp")
            else:
    
                step.clearAll()
                step.affect("patternfill")
                step.reset_fill_params()
                step.COM("sr_fill,polarity=positive,step_margin_x=-0.254,step_margin_y=-0.254,"
                         "step_max_dist_x=2540,step_max_dist_y=2540,sr_margin_x=-0.254,"
                         "sr_margin_y=-0.254,sr_max_dist_x=2540,sr_max_dist_y=2540,nest_sr=yes,"
                         "stop_at_steps=,consider_feat=no,consider_drill=no,"
                         "consider_rout=no,dest=affected_layers,attributes=no")
    
            #ss = self.getERPProductType1(jobname)#检测是否半孔板
            #if ss:
                # step.COM("sel_resize,size=30,corner_ctl=no")
    
            if not step.isLayer("patternfill-outline"):
                step.createLayer("patternfill-outline")
                step.copySel("patternfill-outline")
            else:
                step.COM("truncate_layer,layer=patternfill-outline")
                step.copySel("patternfill-outline")
    
            step.unaffect("patternfill")
            step.affect("patternfill-outline")
            step.COM("sel_surf2outline,width=508")
            step.COM("sel_change_sym,symbol=r2.54,reset_angle=no")
    
            for layer in set(check_layers):
                if not step.isLayer(layer):continue
                step.clearAll()
                step.COM("units,type=mm")
                step.affect(layer)		    
                step.resetFilter()
    
                step.setAttrFilter(".string,text=set_outside_feature")
                step.selectAll()
                if step.featureSelected():
                    step.COM("sel_delete_atr,attributes=.string")
                step.selectNone()
                step.resetFilter()
                
                if step.isLayer("set_fill_outside_1.8"):
                    step.flatten_layer(layer, layer+"_set_outside")
                    step.resetFilter()
                    step.affect(layer+"_set_outside")
                    step.refSelectFilter("set_fill_outside_1.8")
                    if step.featureSelected():
                        step.copySel("selectfeature")		    
                    else:
                        step.removeLayer(layer+"_set_outside")                
    
                step.VOF()
                step.COM("filter_set,filter_name=popup,update_popup=no,profile=out")
                step.selectAll()	    
                step.VON()
                
                count = step.featureSelected()
                if count:
                    step.copySel("selectfeature")
                    
                # if not count:
                    # if "set" in stepname:
                step.VOF()
                step.COM("filter_set,filter_name=popup,update_popup=no,profile=in")
                step.selectAll()	    
                step.VON()
                if step.featureSelected():                    
                    step.COM("sel_reverse")                
                    if step.featureSelected():
                        count += step.featureSelected()
                        step.copySel("selectfeature")           

                if not count:
                    step.resetFilter()
                    step.refSelectFilter("patternfill-outline",mode="touch")
                    if step.featureSelected():
                        count += step.featureSelected()
                        step.copySel("selectfeature")
                
                #if count:
                    #step.copySel("%s_ref"%layer)
                #step.clearAll()
                #step.affect("selectfeature")
                #step.resetFilter()
                #step.refSelectFilter("patternfill",mode="cover")
                #if step.featureSelected():
                    #step.selectDelete()
                    
                #step.unaffect(layer)
                #step.affect("%s_ref" % layer)
                #step.refSelectFilter("patternfill-outline", mode="touch")
                #if step.featureSelected():
                    #step.copySel("selectfeature")
    
                if step.isLayer("selectfeature"):
                    step.clearAll()
                    step.affect("selectfeature")
                    step.resetFilter()
                    step.refSelectFilter("patternfill",mode="cover")
                    if step.featureSelected():
                        step.selectDelete()
                    
                    step.clearAll()
                    step.affect("patternfill")

                    # 整体加大900 因外形掏负性很多都是单边400 20220318
                    step.COM("sel_resize,size=900,corner_ctl=no")
    
                    step.unaffect("patternfill")
                    step.affect("selectfeature")
                    step.resetFilter()
 
                    # 去掉负性外形线
                    step.COM("filter_set,filter_name=popup,update_popup=no,polarity=negative")    
                    step.refSelectFilter("patternfill", mode="cover")
                    if step.featureSelected():
                        step.selectDelete()
                        
                    step.clearAll()
                    step.affect("patternfill")
                    step.COM("sel_resize,size=-900,corner_ctl=no")
                    step.clearAll()
                    step.affect("selectfeature")
                    step.resetFilter()
                    step.filter_set(feat_types='pad;line;arc;text')
                    step.selectAll()
                    if step.featureSelected():
                        log = u"检测到{0} {1}层有元素超出profile板外，请检查！".format(stepname, layer)                    
                        arraylist.append(log)                            
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "selectfeature",
                                                                             layer, log, dic_zu_layer, add_note_layer=layer)                         
    
                    # surface 不好取坐标 把surface挑出来 转成外形线 再打标记 20201112 by lyh
                    step.selectNone()
                    step.filter_set(feat_types='surface')
                    step.selectAll()
                    if step.featureSelected():
                        step.removeLayer(layer + "_surface")
                        step.moveSel(layer + "_surface")
                        step.clearAll()
                        step.affect(layer + "_surface")
                        step.COM("sel_surf2outline,width=1")
    
                        # surface存在板内的坐标要去掉 否则很多误报 20220312 by lyh
                        step.resetFilter()
                        step.refSelectFilter("patternfill", mode="cover")
                        if step.featureSelected():
                            step.selectDelete()
    
                        step.resetFilter()
                        step.selectAll()
                        if step.featureSelected():
                            log = u"检测到{0} {1}层有元素超出profile板外，请检查！".format(stepname, layer)
                            if log not in arraylist:                                
                                arraylist.append(log)
                                
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, layer + "_surface",
                                                                                 layer, log, dic_zu_layer, add_note_layer=layer)                             
                            
                        step.removeLayer(layer + "_surface")		
                      
                    if step.isLayer("set_fill_outside_1.8"):
                        """检测板外物会进去拼版单元其他单元内 20200514"""
                        step.clearAll()
                        step.resetFilter()
                        step.affect(layer)
                        step.refSelectFilter("set_fill_outside_1.8")
                        if step.featureSelected():                                
                            log = u"检测到{0} {1}层有板外物会进去拼版单元其他单元内，请检查！".format(stepname, layer)                              
                            arraylist.append(log)                                
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, layer,
                                                                                 layer, log, dic_zu_layer)
                            
                        if step.isLayer(layer+"_set_outside"):
                            step.clearAll()
                            step.resetFilter()
                            step.affect(layer+"_set_outside")
                            step.refSelectFilter("set_fill_outside_1.8")
                            if step.featureSelected():                                
                                log = u"检测到{0} {1}层有板外物有可能会进入到panel的其他拼版单元内，请到panel内仔细检查！".format(stepname, layer)                              
                                arraylist.append(log)                                
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, layer+"_set_outside",
                                                                                     layer, log, dic_zu_layer, add_note_layer=layer)                            
                            
                step.removeLayer("selectfeature")
                step.removeLayer("%s_ref"%layer)
                step.clearAll()
    
            step.COM("editor_page_close")
            step.clearAll()
            step.removeLayer("set_fill_outside_1.8")
        
        if all_steps:       
            step.removeLayer("patternfill-outline")
            step.removeLayer("patternfill")
            
        if arraylist:
            return arraylist, dic_zu_layer

        return "success", None
    
    def check_sold_mask_is_clip_film(self):
        """检测阻焊是否为套印资料 自动制作程序有添加一个r1 属性auto_make_mask的pad 检测此pad即可"""
        stepname = "panel"
        if stepname in matrixinfo["gCOLstep_name"]:
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            
            step.clearAll()
            for layer in solderMaskLayers:
                step.affect(layer)
            
            step.resetFilter()
            step.filter_set(feat_types='pad', polarity='positive')
            step.setAttrFilter(".string,text=auto_make_mask")
            step.selectSymbol("r1")
            if step.featureSelected():
                step.clearAll()
                step.resetFilter()
                return "not_run_check"
        
            step.resetFilter()
            step.filter_set(feat_types='pad', polarity='positive')
            step.setAttrFilter(".string,text=auto_check_mask_error")
            step.selectSymbol("r1")
            if step.featureSelected():
                step.clearAll()
                step.resetFilter()
                return "run_check_mask_error"            
            
            step.clearAll()
            step.resetFilter()
            
        return False
    
    def check_slot_rotation_angle_condition(self):
        """检测槽孔旋转角度跟规范是否一致20230410 by lyh"""
        
        # stepname = "edit"
        arraylist = []
        dic_zu_layer = {}
        ykj_has_slot = {}
        for stepname in ["edit", "set"]:            
            if stepname in matrixinfo["gCOLstep_name"]:
                step = gClasses.Step(job, stepname)
                step.open()
                worklayer = "drl"
                reflayer = "tk.ykj"
                coordinate_info1 = []
                if step.isLayer(worklayer):
                    layer_cmd1 = gClasses.Layer(step, worklayer)
                    feat_out1 = layer_cmd1.featout_dic_Index(units="mm", options="feat_index")["lines"]
                    
                    coordinate_info1 = [(obj, math.hypot((obj.xs+obj.xe) *0.5, (obj.ys+obj.ye) *0.5),
                                        obj.xs, obj.ys, obj.xe, obj.ye,obj.angle) for obj in feat_out1]
                else:
                    continue
                
                coordinate_info2 = []
                if step.isLayer(reflayer):                
                    layer_cmd2 = gClasses.Layer(step, reflayer)
                    feat_out2 = layer_cmd2.featout_dic_Index(units="mm", options="feat_index")["lines"]
                    
                    coordinate_info2 = [(obj, math.hypot((obj.xs+obj.xe) *0.5, (obj.ys+obj.ye) *0.5),
                                        obj.xs, obj.ys, obj.xe, obj.ye,obj.angle) for obj in feat_out2]
                    
                step.clearAll()
                step.resetFilter()
                step.affect(worklayer)
                if coordinate_info1 and coordinate_info2:
                    ykj_has_slot[stepname] = "yes"
                    for pre_info in coordinate_info1:
                        for suffix_info in coordinate_info2:
                            # 坐标到原点位置接近 且中心位置接近的 为同一个槽
                            if pre_info[1] - suffix_info[1] < 0.1 and \
                               abs((pre_info[2] + pre_info[4]) * 0.5 - (suffix_info[2] + suffix_info[4]) * 0.5) < 0.1 and \
                               abs((pre_info[3] + pre_info[5]) * 0.5 - (suffix_info[3] + suffix_info[5]) * 0.5) < 0.1:
                                
                                p = pre_info[6]                            
                                s = suffix_info[6]
                                    
                                diff_angle = abs(p - s)
                                if 260<= diff_angle < 270:
                                    diff_angle = 270 - abs(p - s)
                                elif 270<= diff_angle < 330:
                                    diff_angle = abs(p - s) - 270
                                    
                                elif 170<= diff_angle < 180:
                                    diff_angle = 180 - abs(p - s)
                                elif 180<= diff_angle < 220:
                                    diff_angle = abs(p - s) - 180
                                    
                                elif 80<= diff_angle < 90:
                                    diff_angle = 90 - abs(p - s)
                                elif 90<= diff_angle < 120 :
                                    diff_angle = abs(p - s) - 90 
                                    
                                slot_size = float(suffix_info[0].symbol[1:])
                                slot_len = suffix_info[0].len
                                calc_angle = self.get_slot_rotation_angle(slot_size, slot_len)
                                if not isinstance(calc_angle, int):
                                    if calc_angle not in arraylist:                                    
                                        arraylist.append(calc_angle)
                                    continue
                                
                                if diff_angle and round(diff_angle, 1) != calc_angle:
                                    step.selectNone()
                                    step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(worklayer, pre_info[0].feat_index))
                                    # step.PAUSE(str([pre_info, suffix_info, diff_angle, calc_angle, slot_size, slot_len]))
                                    log = u"槽孔{0}槽长{1} 实际旋转角度{2} 跟规范要求角度{3} 不一致，请检查！".format(slot_size, slot_len*1000+float(slot_size), diff_angle, calc_angle)                                 
                                    if log not in arraylist:                                    
                                        arraylist.append(log)
                                        
                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, worklayer,
                                                                                         reflayer, log, dic_zu_layer)                                 
                    step.clearAll()
                    
                else:
                    #if not coordinate_info1:
                        #return u"success无槽孔，无需检测", None
                    
                    if coordinate_info1 and not coordinate_info2:
                        ykj_has_slot[stepname] = "no"
                        # return u"{0}层内不存在槽孔，请检查".format(reflayer), None
        
        if ykj_has_slot:
            if "yes" not in ykj_has_slot.values():
                return u"set跟edit的 {0}层内都不存在槽孔，请检查".format(reflayer), None
                
        if arraylist:                    
            return arraylist, dic_zu_layer
        
        return u"success", None        
        # return u"edit不存在，请检查", None
                            
    def get_slot_rotation_angle(self, slot_size, slot_len):
        """获取槽孔角度"""
        
        #去除槽孔的尾数来计算20230726 by lyh
        if slot_size % 10 > 0 and slot_size % 5 > 0:
            a, b = divmod(slot_size, 10)
            new_slot_size = a * 10
        else:
            new_slot_size = slot_size
            
        r = round((float(slot_len) *1000 +float(slot_size)) / float(new_slot_size), 2)
        if slot_size <= 809:
            if r >= 2:
                return 0
            if 1.8< r < 2:
                return 3
            if 1.5< r <= 1.8:
                return 6
            if r <= 1.5:
                return 8
            
        if 850<= slot_size <= 1259:
            if r >= 2:
                return 0
            if 1.8< r < 2:
                return 3
            if 1.5< r <= 1.8:
                return 4
            if 1.25< r <= 1.5:
                return 5            
            if r <= 1.25:
                return 6
            
        if 1300<= slot_size <= 1959:
            if r >= 2:
                return 0
            if 1.8< r < 2:
                return 2
            if 1.5< r <= 1.8:
                return 3
            if 1.25< r <= 1.5:
                return 4            
            if r <= 1.25:
                return 5
            
        if 2000<= slot_size:
            if r >= 2:
                return 0
            if 1.5< r <= 2:
                return 2
            if 1.25< r <= 1.5:
                return 3
            if r <= 1.25:
                return 5
        
        return u"槽孔{0}槽长{1}不在规范内，请反馈工艺处理！".format(slot_size, float(slot_len) *1000 +float(slot_size))
    
    def check_target_symbol_touch_other_features(self):
        """检测重要靶标是否被其他surface的元素有覆盖 20230410 by lyh"""
        check_symbol = """hdi-dwpad
        hdi-dwtop-t
        hdi-dwtop-b
        sh-dwsig2014
        sh_silk_autodw
        hdi-dwtop2013
        hdi1-baj*
        hdi1-ba*
        hdi1-byj*
        hdi1-by*
        hdi1-bs*
        sh-ldi
        sh-dwtop
        measure_l*
        measure_fd_l*"""
        stepname = "panel"
        if stepname not in matrixinfo["gCOLstep_name"]:
            return u"panel不存在，请检查", None
        
        step = gClasses.Step(job, stepname)
        step.open()
        
        symbols = [x.strip() for x in check_symbol.split()]
        
        arraylist = []
        dic_zu_layer = {}
        for worklayer in outsignalLayers + innersignalLayers:
            step.clearAll()
            step.resetFilter()
            step.affect(worklayer)
            
            step.selectSymbol(";".join(symbols), 1, 1)
            find_indexes = []
            find_symbols = []
            if step.featureSelected():                
                layer_cmd = gClasses.Layer(step, worklayer)
                feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]
                for obj in feat_out:
                    step.selectNone()
                    step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(worklayer, obj.feat_index))
                    #if worklayer == "l2":                        
                        #step.PAUSE(worklayer)
                    step.resetFilter()
                    step.filter_set(exclude_syms='r0')
                    if obj.symbol in ["hdi-dwpad"]:
                        step.filter_set(exclude_syms='r0;s5080')
                        
                    if obj.symbol in ["sh-ldi"]:
                        step.filter_set(exclude_syms='s4000;s3850')
                        
                    if "hdi1-b" in obj.symbol:
                        step.filter_set(exclude_syms='donut_s5100x4650')                          
                        
                    step.COM("sel_ref_feat,layers=,use=select,mode=touch,\
                    pads_as=shape,f_types=line\;pad\;surface\;arc\;text,\
                    polarity=positive\;negative,include_syms=,exclude_syms=")
                    log = ""
                    #if worklayer == "l2":                        
                        #step.PAUSE(worklayer)                        
                    if step.featureSelected():
                        indexes = layer_cmd.featSelIndex()
                        feat_out_touch = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]
                        touch_indexes = [touch_obj.feat_index for touch_obj in feat_out_touch]
                        
                        for index in indexes:
                            if float(index) > float(obj.feat_index):
                                if index not in touch_indexes:                                    
                                    find_symbols.append(obj.symbol)
                                    log = u"检测到{0} 层靶标{1} 上有被其他元素[索引:{2}]覆盖接触，请检查靶标是否完整！".format(worklayer, obj.symbol, index)
                                else:
                                    touch_obj = [o for o in feat_out_touch if o.feat_index == index][0]
                                    
                                    # if "-lyh" in job.name:                                        
                                    resize = 0.3
                                    if obj.symbol in ["hdi-dwpad"]:
                                        resize = 0.9
                                        
                                    area_xy1 = self.get_symbol_calc_area(get_symbol_area(step, job.name, step.name, obj.symbol, (obj.x, obj.y),
                                                                                         obj.rotation, obj.mirror,
                                                                                         dic_symbol_info=dic_symbol_info), resize)
                                    
                                    area_xy2 = self.get_symbol_calc_area(get_symbol_area(step, job.name, step.name, touch_obj.symbol, (touch_obj.x, touch_obj.y),
                                                                                         touch_obj.rotation, touch_obj.mirror,
                                                                                         dic_symbol_info=dic_symbol_info))
                                    if self.intersection_area(*area_xy1+area_xy2):
                                        find_symbols.append(obj.symbol)
                                        log = u"检测到{0} 层靶标{1} 上有被其他元素[索引:{2}]覆盖接触，请检查靶标是否完整！".format(worklayer, obj.symbol, index)                                        
                                
                    if log:
                        find_indexes.append(obj.feat_index)
            
            # if "-lyh" in job.name:
            for drill_layer in ["drl", "2nd", "3nd",
                                "cdc", "cds", "bdc", "bds"] + mai_drill_layers:
                for i, layer in enumerate(matrixinfo["gROWname"]):
                    if matrixinfo["gROWcontext"][i] == "board" and \
                       drill_layer in layer:
                        
                        if layer in mai_drill_layers:
                            start, end = get_drill_start_end_layers(matrixinfo, layer)
                            index1 = matrixinfo["gROWname"].index(start)
                            index2 = matrixinfo["gROWname"].index(end)
                            index = matrixinfo["gROWname"].index(worklayer)
                            if not min([index1, index2])<= index <= max([index1, index2]):
                                continue                            
                        else:
                            if worklayer not in ["l1", "l2", "l{0}".format(lay_num), "l{0}".format(lay_num-1),]:
                                continue
                            
                        step.selectNone()
                        step.resetFilter()
                        step.setSymbolFilter(";".join(symbols))
                        step.refSelectFilter(layer)
                        if step.featureSelected():
                            layer_cmd = gClasses.Layer(step, worklayer)
                            feat_out_touch = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]
                            find_symbols = [touch_obj.symbol for touch_obj in feat_out_touch]                                
                            log = u"检测到{0} 层靶标{1} 上有被钻孔层{2}接触，请检查靶标是否完整！".format(worklayer,";".join(list(set(find_symbols))), layer)
                            arraylist.append(log)
                            
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, worklayer,
                                                                                 layer, log, dic_zu_layer)
                step.resetFilter()
                            
            if find_indexes:
                
                log = " "
                if find_symbols:            
                    log = u"检测到{0} 层靶标{1} 上有被其他元素覆盖接触，请检查靶标是否完整！".format(worklayer,";".join(list(set(find_symbols))))
                    arraylist.append(log)
                    
                step.selectNone()
                for feat_index in find_indexes:                    
                    step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(worklayer, feat_index))
                
                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, worklayer,
                                                                 worklayer, log, dic_zu_layer)            
                        
        step.clearAll()        
            
        if arraylist:
            return arraylist, dic_zu_layer
        
        return "success" , None   
    
    def intersection_area(self, A_x1, A_y1, A_x2, A_y2, B_x1, B_y1, B_x2, B_y2):
        # 计算交集区域的坐标
        x1 = max(A_x1, B_x1)
        y1 = max(A_y1, B_y1)
        x2 = min(A_x2, B_x2)
        y2 = min(A_y2, B_y2)
    
        # 检查交集区域是否有效
        if x1 < x2 and y1 < y2:
            # 计算交集区域的面积
            area = (x2 - x1) * (y2 - y1)
            return area
        else:
            # 没有交集
            return 0
    
    def get_symbol_calc_area(self, arraylist_xy, resize=0):
        all_x = [x for x, y in arraylist_xy]
        all_y = [y for x, y in arraylist_xy]
        
        return min(all_x) + resize, min(all_y) + resize, max(all_x) - resize, max(all_y) -resize
    
    def check_v5_laser_hole_contact_signal_symbol(self, show_ui=None):
        """检测镭射五代靶中心跟线路靶标是否一致"""
        if "panel" in matrixinfo["gCOLstep_name"]:
            stepname = "panel"
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            arraylist = []
            dic_zu_layer = {}
            for drill_layer in laser_drill_layers:
                step.clearAll()
                step.affect(drill_layer)
                step.selectSymbol("r520", 1, 1)
                if not step.featureSelected():
                    continue
                else:
                    step.removeLayer(drill_layer+"_r520_tmp")
                    step.copySel(drill_layer+"_r520_tmp")
                siglayer = "l{0}".format(drill_layer.split("-")[0][1:])
                # layer2 = "l{0}".format(drill_layer.split("-")[1])                
                # for siglayer in [layer1, layer2]:
                step.clearAll()
                step.affect(siglayer)
                step.selectSymbol("hdi-dwpad", 1, 1)                    
                if step.featureSelected():
                    step.removeLayer(siglayer+"_v5_target")
                    step.copySel(siglayer+"_v5_target")
                    
                    step.clearAll()
                    step.affect(siglayer+"_v5_target")
                    step.changeSymbol("s3974")
                    
                    step.clearAll()
                    step.affect(drill_layer+"_r520_tmp")
                    step.resetFilter()
                    step.setSymbolFilter("r520")                        
                    step.refSelectFilter(siglayer+"_v5_target", mode="cover")
                    if step.featureSelected():
                        step.selectDelete()
                    
                    step.contourize()
                    step.resetFilter()
                    step.selectAll()
                    if step.featureSelected():
                        log = u"检测到{0} 层五代靶跟线路{1}靶中心不一致，请检查标记处靶标是否异常！".format(drill_layer,siglayer)
                        arraylist.append(log)
                        
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, drill_layer+"_r520_tmp",
                                                                             siglayer, log, dic_zu_layer, add_note_layer=drill_layer)
                step.removeLayer(drill_layer+"_r520_tmp")
                step.removeLayer(siglayer+"_v5_target")
                    
            if arraylist:
                if show_ui is None:
                    return arraylist, dic_zu_layer
                else:                    
                    showMessageInfo(*arraylist)
                    self.view_note_detail(dic_zu_layer)
                    return arraylist, dic_zu_layer
            
            return "success", None
        
        return u"success没有panel信息，无需检测。", None
                
    def check_copper_thick_for_hct_coupon(self):
        """翟鸣通知 检测内外层铜厚是否符合要求 纯内层铜厚大于2OZ/次外层、外层铜厚大于等于3mil报警不予添加 20230523 by lyh"""
        array_mrp_info = get_inplan_mrp_info(str(job.name).upper(), condtion="1=1")
        array_cu_weight = get_cu_weight(job.name.upper(), True)
        arraylist = []
        # print array_mrp_info
        for dic_mrp_info in array_mrp_info:
            if dic_mrp_info["FROMLAY"] is None:
                continue
            layer1 = dic_mrp_info["FROMLAY"].lower()
            layer2 = dic_mrp_info["TOLAY"].lower()
            process_num = dic_mrp_info["PROCESS_NUM"]
            # print layer1, layer2, process_num
            if process_num == 1:
                for dic_cu_info in array_cu_weight:
                    # print dic_cu_info["LAYER_NAME"].lower(), "---->1"
                    if dic_cu_info["LAYER_NAME"].lower() in [layer1, layer2]:
                        weight = dic_cu_info["CU_WEIGHT"]
                        # print weight, "----->2"
                        if weight >= 1.98:
                            arraylist.append(u"检测到内层{0} {1}铜厚大于等于2OZ，请与主管确认HCT COUPON线宽、孔ring设计！".format(layer1, layer2))
            else:
                for dic_cu_info in array_cu_weight:
                    if dic_cu_info["LAYER_NAME"].lower() in [layer1, layer2]:
                        weight = dic_cu_info[u"厂内管控计算铜MIL".encode("utf8")]
                        # print weight, "----->2"
                        if weight >= 2.99:
                            arraylist.append(u"检测到次外层或外层{0} {1}铜厚大于等于3mil，请与主管确认HCT COUPON线宽、孔ring设计！".format(layer1, layer2))
                            
        if arraylist:
            return arraylist, None        

        return "success" , None
    
    def check_set_luokongqu_fill_copper(self):
        """6.	Set里线路捞空区是否铺铜"""
        if "set" not in matrixinfo["gCOLstep_name"]:
            return u"success set 不存在，无需检查", None
        
        if "out" not in matrixinfo["gROWname"]:
            return u"out 层不存在，请检查", None
        
        stepname = "set"
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=inch")
        
        step.clearAll()
        step.removeLayer("set-out-tu")
        step.createLayer("set-out-tu")
        step.affect("set-out-tu")
        step.reset_fill_params()
        step.COM("sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,"
                 "step_max_dist_x=100,step_max_dist_y=100,sr_margin_x=0,"
                 "sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=yes,"
                 "stop_at_steps=,consider_feat=no,consider_drill=no,"
                 "consider_rout=no,dest=affected_layers,attributes=no")
        
        step.clearAll()
        step.affect("drl")
        if step.isLayer("l2"):            
            step.affect("l2")
            
        step.affect("ww")
        step.removeLayer("nnn")
        step.copySel("nnn")
        step.clearAll()
        step.affect("nnn")
        step.contourize(units="inch")
        step.COM("sel_delete_atr,attributes=.rout_chain")
        step.COM("sel_resize,size=81")
        step.copyToLayer("set-out-tu", invert="yes")
        
        step.clearAll()
        step.display("set-out-tu")
        step.contourize(units="inch")
        
        if step.isLayer("l2"):            
            step.display_layer("l2", 2)
        else:
            step.display_layer("l1", 2)
            
        step.display_layer("ww", 3)
        step.COM("display_sr,display=yes")
        
        log = u"请检查锣空区是否有铺铜！"
        self.pause_check_result(step, log)
        
        return u"人工检查完毕，若需单独查看请点击手动运行，按提示步骤进行检查", None
    
    def check_set_panelization_info(self):
        """9.	Set挂板是否正确（是否有重复挂板，挂偏）"""
        if "set" not in matrixinfo["gCOLstep_name"]:
            return u"success set 不存在，无需检查", None
        
        stepname = "set"
        step = gClasses.Step(job, stepname)
        step.open()
        step.removeLayer("sr_fill")
        step.removeLayer("sr_fill_tmp")
        step.removeLayer("sr_panelization_error+++")
        dic_zu_layer = {}
        arraylist = []
        get_sr_area_flatten("sr_fill", stepname=stepname, get_sr_step=True)
        if step.isLayer("sr_fill"):
            layer_cmd = gClasses.Layer(step, "sr_fill")            
            step.clearAll()
            step.affect("sr_fill")
            step.resetFilter()
            step.COM("sel_resize,size=-1")
            step.selectAll()
            indexes = layer_cmd.featSelIndex()
            step.resetFilter()
            for feat_index in set(indexes):
                step.selectNone()
                step.selectFeatureIndex("sr_fill", feat_index)                
                if step.featureSelected():
                    step.removeLayer("sr_fill_tmp")
                    step.copySel("sr_fill_tmp")
                    step.refSelectFilter("sr_fill_tmp", mode='cover', f_types="surface", polarity="positive")
                    if step.featureSelected() >= 2:                                                      
                        layer = "sr_panelization_error+++"
                        step.copySel(layer)
                        log = u"检测到{0} 标识区域有重复挂板，请到{1}层查看，请检查！".format(stepname, layer)                              
                        arraylist.append(log)                          
                        dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                              worklayer="view_layer_"+layer, 
                                                              dic_layer_list={log:[layer], },
                                                              dic_zu_layer=dic_zu_layer)
                    else:
                        step.refSelectFilter("sr_fill_tmp", mode='touch', f_types="surface", polarity="positive")
                        if step.featureSelected() >= 2:                                                        
                            layer = "sr_panelization_error+++"
                            step.copySel(layer)
                            log = u"检测到{0} 标识区域跟附近其他拼版单元有接触，请到{1}层查看，请检查！".format(stepname, layer)  
                            arraylist.append(log)     
                            dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                                  worklayer="view_layer_"+layer, 
                                                                  dic_layer_list={log:[layer], },
                                                                  dic_zu_layer=dic_zu_layer)
        step.removeLayer("sr_fill")
        step.removeLayer("sr_fill_tmp")
        if step.isLayer("ww"):
            all_steps = [name for name in get_panelset_sr_step(job.name, stepname)
                         if "edit" in name]                
            for editname in set(all_steps):
                editstep = gClasses.Step(job, editname)            
                editstep.open()
                editstep.COM("units,type=mm")
                editstep.clearAll()
                if not editstep.isLayer("fill_tmp"):
                    editstep.createLayer("fill_tmp")
                else:
                    editstep.COM("truncate_layer,layer=fill_tmp")
    
                editstep.affect("fill_tmp")
                editstep.reset_fill_params()                    
                editstep.COM("sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,"
                             "step_max_dist_x=2540,step_max_dist_y=2540,sr_margin_x=0,sr_margin_y=0,"
                             "sr_max_dist_x=2540,sr_max_dist_y=2540,nest_sr=yes,stop_at_steps=,"
                             "consider_feat=no,consider_drill=no,consider_rout=no,"
                             "dest=affected_layers,attributes=no")
            
            step.copyLayer(job.name, stepname, "ww", "ww_surface")
            step.clearAll()
            step.affect("ww_surface")
            step.contourize()
            
            if step.isLayer("fill_tmp"):
                step.clearAll()
                step.flatten_layer("fill_tmp", "sr_fill")
                step.affect("sr_fill")
                step.copyLayer(job.name, stepname, "sr_fill", "sr_fill_bak")
                step.COM("sel_surf2outline,width=1")
                
                step.resetFilter()
                step.refSelectFilter("ww_surface", mode='cover')
                step.COM("sel_reverse")
                if step.featureSelected():                                                
                    layer = "sr_panelization_error2+++"
                    log = u"检测到{0} 标识区域挂板跟ww层有偏差，请到{1}层查看，请检查挂板是否有偏移！".format(stepname, layer)    
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, "sr_fill",
                                                                         layer, log, dic_zu_layer, add_note_layer="ww")
                    
                    step.copyToLayer(layer, size=100)
                    step.clearAll()
                    step.affect("sr_fill_bak")
                    step.refSelectFilter(layer)
                    if step.featureSelected():
                        step.copySel(layer)
                    
                    #dic_zu_layer=self.get_view_dic_layers(job.name, stepname, step,
                                                          #worklayer="view_layer_"+layer, 
                                                          #dic_layer_list={log:[layer, "ww"], },
                                                          #dic_zu_layer=dic_zu_layer)
                    
        step.removeLayer("fill_tmp")
        step.removeLayer("sr_fill")
        step.removeLayer("sr_fill_bak")
        step.removeLayer("ww_surface")
        if arraylist:
            return arraylist, dic_zu_layer
        
        return "success", None

    # 20241024 zl
    # 外层检测增加项目---挡点是否比防焊开窗大&双面开窗孔存在挡点
    def check_md_cover_info(self):
        md_layers = ['md1', 'md2']
        arraylist = []
        dic_zu_layer = {}
        if "panel" in matrixinfo["gCOLstep_name"]:
            all_steps = get_panelset_sr_step(job.name, "panel")
            for stepname in all_steps:
                step = gen.Step(job, stepname)
                step.open()
                step.setUnits('mm')
                for layer in matrixinfo["gROWname"]:
                    if "_autocheck_md_cover+++" in layer:
                        step.removeLayer(layer)
                for solderMaskLayer in solderMaskLayers:
                    if solderMaskLayer == 'm1':
                        md_layer = 'md1'
                    else:
                        md_layer = 'md2'
                    if step.isLayer(md_layer):
                        tmp_md = '%s_autocheck_md_cover+++' % md_layer
                        step.affect(md_layer)
                        # 如果是空 跳过
                        step.selectReverse()
                        if not step.Selected_count():
                            step.unaffectAll()
                            continue
                        step.copyToLayer(tmp_md, size=50.8)
                        step.clearAll()
                        step.affect(solderMaskLayer)
                        # 去掉负片
                        tmp_sm = '%s_autocheck_md_cover+++' % solderMaskLayer
                        step.copySel(tmp_sm)
                        step.unaffectAll()
                        step.affect(tmp_sm)
                        step.Contourize()
                        step.copySel(tmp_md, 'yes')
                        step.clearAll()
                        step.removeLayer(tmp_sm)
                        step.affect(tmp_md)
                        step.Contourize()
                        step.selectReverse()
                        if step.Selected_count():
                            log = u"检测到挡点{0}不比防焊开窗{1}小单边1mil，请到{2}中的{3}查看超出位置！".format(md_layer, solderMaskLayer, stepname, tmp_md)
                            arraylist.append(log)
                            dic_zu_layer = self.get_view_dic_layers(job.name, stepname, step, worklayer="view_layer_"+md_layer,dic_layer_list={u"请查看异常层：": [
                                                                        md_layer, solderMaskLayer, tmp_md], },
                                                                    dic_zu_layer=dic_zu_layer)
                        step.clearAll()
                if step.isLayer("drl"):
                    drl = "drl"
                    if step.isLayer("cdc"):
                        drl = "cdc"
                    if step.isLayer("cds"):
                        drl = "cds"
                    for md in md_layers:
                        if step.isLayer(md):
                            step.affect(drl)
                            step.refSelectFilter(md, mode='disjoint')
                            if step.Selected_count():
                                log = u"双面开窗的孔必须存在挡点,请检查{0}中钻孔层{1}和挡点层{2}".format(stepname, drl, md)
                                arraylist.append(log)
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, drl, drl, log, dic_zu_layer)
                            step.clearAll()

            if arraylist:
                # showMessageInfo(*arraylist)
                return arraylist, dic_zu_layer

        return "success", None

    # 20241025 zl 内层检测增加检测项目--防爆孔与融合块位置一致
    def check_offset_et_rj_fbk(self):
        if "panel" not in matrixinfo["gCOLstep_name"]:
            return u"success panel 不存在，无需检查", None
        if "drl" not in matrixinfo["gROWname"]:
            return u"drl 层不存在，请检查", None
        arraylist = []
        dic_zu_layer = {}
        stepname = 'panel'
        step = gen.Step(job, stepname)
        step.open()
        step.setUnits('mm')
        step.clearAll()
        step.resetFilter()
        for layer in matrixinfo["gROWname"]:
            if "_autocheck_offset_et_rj_fbk+++" in layer:
                step.removeLayer(layer)
        # fbk
        drl = 'drl'
        tmp_drl = '%s_autocheck_offset_et_rj_fbk+++' % drl
        step.affect(drl)
        step.setAttrFilter(".string,text=fbk")
        step.selectAll()
        step.resetFilter()
        if step.Selected_count():
            step.copySel(tmp_drl)
            step.unaffectAll()
        else:
            return u"success drl不存在fbk属性，无需检查", None
        step.unaffectAll()
        for innersignalLayer in innersignalLayers:
            tmp = '%s_autocheck_offset_et_rj_fbk+++' % innersignalLayer
            step.affect(innersignalLayer)
            step.selectSymbol('et_rj_pad_p')
            step.resetFilter()
            if step.Selected_count():
                step.copySel(tmp)
                step.unaffectAll()
                step.affect(tmp)
                step.selectBreak()
                step.Contourize()
                step.COM('sel_clean_holes,max_size=1270,clean_mode=x_and_y')
                # 放大防爆孔的1/3， 超出这个范围则判定为偏移
                step.selectResize(1333)
                step.unaffectAll()
                step.affect(tmp_drl)
                step.refSelectFilter(tmp, mode='cover')
                if step.Selected_count():
                    step.selectReverse()
                    if step.Selected_count():
                        show_drl = '%s_%s' % (innersignalLayer, tmp_drl)
                        step.copySel(show_drl)
                        log = u"检测到{0}防爆孔与{1}融合块位置偏移，请到{2}中的{3}查看超出位置！".format(drl, innersignalLayer,
                                                                                                           stepname,
                                                                                                           show_drl)
                        arraylist.append(log)
                        dic_zu_layer = self.get_view_dic_layers(job.name, stepname, step, worklayer="view_layer_"+innersignalLayer,
                                                                dic_layer_list={u"请查看异常层：": [innersignalLayer, show_drl], },
                                                                dic_zu_layer=dic_zu_layer)
                step.unaffectAll()
                step.removeLayer(tmp)
            step.unaffectAll()
        step.removeLayer(tmp_drl)
        if arraylist:
            # showMessageInfo(*arraylist)
            return arraylist, dic_zu_layer
        return "success", None

    def check_set_drill_analysis_info(self):
        """12.	Set里实体化钻孔分析（只分析通孔，防止工艺边加的孔跟板内孔间距太近断刀）"""
        if "set" not in matrixinfo["gCOLstep_name"]:
            return u"success set 不存在，无需检查", None
        
        if "drl" not in matrixinfo["gROWname"]:
            return u"drl 层不存在，请检查", None
        
        stepname = "set"
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        worklayer = "drl"
        step.flatten_layer(worklayer, worklayer+"_flt")
        step.clearAll()
        step.resetFilter()
        step.affect(worklayer+"_flt")
        step.refSelectFilter(worklayer, mode='cover')
        if step.featureSelected():
            step.selectDelete()        
        
        arraylist = []
        dic_zu_layer = {}
        step.COM("sel_delete_atr,attributes=.rout_chain")
        step.COM("sel_resize,size={0}".format(6*25.4))
        step.clearAll()
        step.affect(worklayer)
        step.refSelectFilter(worklayer+"_flt")
        if step.featureSelected():
            log = u"检测到set工艺边加的孔 跟板内孔间距小于6mil，请检查是否异常！"
            arraylist.append(log)
            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, worklayer,
                                                                 worklayer, log, dic_zu_layer)
        
        step.removeLayer(worklayer+"_flt")
        if arraylist:
            return arraylist, dic_zu_layer
        
        return "success", None
    
    def check_caotou_slot_info(self):
        """13.	槽头孔加的是否正确"""
        if "set" not in matrixinfo["gCOLstep_name"]:
            return u"set 不存在，请检查", None
        
        if "drl" not in matrixinfo["gROWname"]:
            return u"drl 层不存在，请检查", None
        
        stepname = "set"
        worklayer = "drl"
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=inch")
        
        step.clearAll()
        step.affect("ww")
        step.changeSymbol("r4")
        
        step.clearAll()
        step.display(worklayer)
        step.display_layer("ww", 2)
        step.refSelectFilter("ww")
        
        log = u"请检查槽头孔加的是否正确"
        self.pause_check_result(step, log)
        
        step.clearAll()
        return u"人工检查完毕，若需单独查看请点击手动运行，按提示步骤进行检查", None
    
    def check_set_signal_analysis_info(self):
        """14.	分析set线路rout，size，bottleneck这3项"""
        if "set" not in matrixinfo["gCOLstep_name"]:
            return u"set 不存在，请检查", None
        
        stepname = "set"
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=inch")
        step.clearAll()
        step.COM("matrix_layer_context,job={0},matrix=matrix,layer=ww,context=board".format(job.name))
        step.COM("matrix_layer_type,job={0},matrix=matrix,layer=ww,type=rout".format(job.name))
        step.display("ww")
        step.COM("affected_filter,filter=(type=signal&context=board)")
        step.COM("chklist_single,action=valor_analysis_signal,show=yes")
        step.COM("chklist_cupd,chklist=valor_analysis_signal,nact=1,params=((pp_layer=.affected)"
                 "(pp_spacing=4.5)(pp_r2c=6)(pp_d2c=10)(pp_sliver=4)(pp_min_pad_overlap=5)"
                 "(pp_tests=Rout\;Size\;Bottleneck)(pp_selected=All)(pp_check_missing_pads_for_drills=Yes)"
                 "(pp_use_compensated_rout=No)(pp_sm_spacing=No)),mode=regular")
        step.COM("chklist_run,chklist=valor_analysis_signal,nact=1,area=global")
        step.COM("chklist_hist_show,chklist=valor_analysis_signal,nact=1")        
        step.COM("show_tab,tab=Checklists,show=no")        
        self.pause_check_result(step, u"请检查set线路rout，size，bottleneck这3项")
        step.COM("chklist_res_close,chklist=valor_analysis_signal,nact=1")
        
        return u"人工检查完毕，若需单独查看请点击手动运行，按提示步骤进行检查", None
    
    def check_set_mask_to_pcs_info(self):
        """15.	Set里开窗到板内的开窗的桥是否足够"""
        if "set" not in matrixinfo["gCOLstep_name"]:
            return u"set 不存在，请检查", None
        
        stepname = "set"
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=inch")    
    
            
    def show_message_info(self, *args):
        if args[0] == "check_die_ceng":
            # showMessageInfo(u"请参考客户叠层信息进行检查！")
            job.COM("show_component,component=Step_Matrix,show=yes,width=0,height=0")
            self.pause_check_result(job, u"请参考客户叠层信息进行检查", args=args)
            job.COM("show_component,component=Step_Matrix,show=no,width=0,height=0")
            
        return u"人工检查完毕，若需单独查看请点击手动运行，按提示步骤进行检查", None

if __name__ == "__main__":    
    main = auto_check_rule()
    func = None
    try:
        func = sys.argv[1]
    except Exception, e:
        print e

    args = []
    try:
        args = sys.argv[2:]
    except Exception, e:
        print 'args:', e

    # 测试
    #if func is None:
        #func = "set_dl_negative_process_fill_cu"
        #args = ['100332344s0699a01', 'panel']
    ####

    if func is None:
        pass
    else:        
        if hasattr(main, func):
            if args:
                result = getattr(main, func)(*args)
            else:
                result = getattr(main, func)()

            if result:
                if args:
                    main.create_log_and_update_coordinate(job.name, func+" "+" ".join(args), *result)
                else:
                    main.create_log_and_update_coordinate(job.name, func, *result)
                    
    sys.exit()


    
    