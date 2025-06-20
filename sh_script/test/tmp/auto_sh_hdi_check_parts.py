#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20231114"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""胜宏HDI自动检测模块 """
"""sh_hdi_warning_director_process"""

import os
import re
import sys
reload(sys)
sys.setdefaultencoding('utf8')
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")
    sys.path.append(r"D:/pyproject/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
    sys.path.append(r"/incam/server/site_data/scripts/lyh")

os.environ['COM_VON_VOF'] = 'yes'
import gClasses
import gFeatures
import genCOM_26
import math
import json
from datetime import datetime

from genesisPackages import get_mai_drill_hole,get_sr_area_for_step_include, \
     get_drill_start_end_layers, get_panelset_sr_step,get_profile_limits, \
     outsignalLayers, innersignalLayers, solderMaskLayers,\
     silkscreenLayers, lay_num, top, tongkongDrillLayer,laser_drill_layers, \
        mai_drill_layers, bd_drillLayer,matrixInfo, mai_man_drill_layers,ksz_layers

from connect_database_all import MySql, InPlan, ERP
from get_erp_job_info import get_outer_target_condition, get_inplan_mrp_info,\
    get_laser_fg_type,get_plating_type

from create_ui_model import showMessageInfo

try:
    if sys.platform != "win32":
        sys.path.insert(0, "/incam/server/site_data/scripts/sh_script/sh_hdi_auto_check_list")
    from sh_hdi_auto_check_list import get_check_function_list, \
        update_current_job_check_log, processID, jobID

    from showTargetDistanceInformation import TargetDistance_UI
    from send_html_request_to_tc_aac_file import post_message
except:
    pass

# from sh_hdi_auto_check_list import get_check_function_list, update_current_job_check_log
try:
    from send_message_to_topcam import uploading_message_to_topcam
except:
    pass
try:
    from TOPCAM_IKM import IKM
    ikm_fun = IKM()
except Exception, e:
    print e


from auto_sh_hdi_check_rules import auto_check_rule
from checkRules import rule
checkrule = rule()

jobname = os.environ.get("JOB")
stepname = os.environ.get("STEP")
job = gClasses.Job(jobname)
matrixinfo = job.matrix.getInfo()


def get_topcam_status(index, job_name):
    """
    获取topcam运行状态
    """
    sql = """
                select c.title,
    			    b.jobname,
    			    a.status
                from pdm_job_workflow  a ,
                    pdm_job b,
                    pdm_workprocess c
                WHERE
                    process_id = '%s'
                    and a.job_id = b.id
                    and c.id = a.process_id
                    and b.jobname = lower('%s')	
            """ % (index, job_name)

    get_data = ikm_fun.PG.SELECT_DIC(ikm_fun.dbc_p, sql)
    if get_data:
        status = get_data[0]['status']
        if status == 'Done' or status == 'Finish':
            return True
        else:
            return False
    else:
        return False


def judge_job_type(job_name):
    """
    获取料号类型，区分双面板、是否有pth孔、是否有镭射
    :return:
    """
    double_sided_board = False
    laser_board = False
    if job_name[5:7] == '02':
        double_sided_board = True
    gen = genCOM_26.GEN_COM()
    drl_layers = gen.GET_ATTR_LAYER('drill', job=job_name)
    try:
        job_signal_num = int(job_name[4:6])
    except ValueError:
        job_signal_num = len(gen.GET_ATTR_LAYER('signal', job=job_name))
    half_job_signal_num = job_signal_num * 0.5
    print drl_layers
    laser_layers = []
    laser_steps_dict = {}
    for dlayer in drl_layers:
        matchObj = re.match('s([0-9][0-9]?)-([0-9][0-9]?)', dlayer)
        if matchObj:
            laser_board = True
            laser_layers.append(dlayer)
            start_num = int(matchObj.group(1))
            end_num = int(matchObj.group(2))
            if start_num == half_job_signal_num and end_num == half_job_signal_num + 1:
                # === 防漏接不考虑芯板镭射 ===
                continue
            if start_num > half_job_signal_num:
                laser_steps_num = job_signal_num - start_num + 1
                current_key = 'bot_layers'
            else:
                laser_steps_num = start_num
                current_key = 'top_layers'
            first_key = '%s' % laser_steps_num
            if first_key not in laser_steps_dict:
                laser_steps_dict[first_key] = {current_key: [dlayer]}
            else:
                if current_key in laser_steps_dict[first_key]:
                    laser_steps_dict[first_key][current_key].append(dlayer)
                else:
                    laser_steps_dict[first_key][current_key] = [dlayer]
    all_laser_steps_num = len(laser_steps_dict.keys())
    print json.dumps(laser_steps_dict, indent=2)
    print all_laser_steps_num
    if all_laser_steps_num > 0:
        laser_board = all_laser_steps_num
    split_via = 0
    split_pth = 0
    pth_board = False
    if 'drl' in drl_layers:
        # === 判断是否有pth孔，包括via，需按属性区分
        # === 获取split_via 与 split_pth
        info = gen.DO_INFO('-t layer -e %s/%s/%s -m script -d TOOL' % (jobname, 'edit', 'drl'))
        for i, tool_type in enumerate(info['gTOOLtype']):
            tool_size = float(info['gTOOLdrill_size'][i]) * 0.001
            if tool_type == 'via':
                if split_via == 0 or split_via == "":
                    split_via = tool_size
                else:
                    if tool_size < split_via:
                        split_via = tool_size
            elif tool_type == 'plated':
                if split_pth == 0 or split_pth == "":
                    split_pth = tool_size
                else:
                    if tool_size < split_pth:
                        split_pth = tool_size
    if split_via != 0 or split_pth != 0:
        pth_board = True
    board_type_dict = dict(double_sided_board=double_sided_board, pth_board=pth_board, laser_board=laser_board)
    return board_type_dict

class CheckParts(object):
    """"""
    def __init__(self):
        """Constructor"""

    def view_note_detail(self, coordinate_info=None):
        """查看标记"""
        if coordinate_info is None:
            dic_info = get_check_function_list(top.getUser(), job.name,
                                               "id = {0}".format(os.environ.get("CHECK_ID", "NULL")))
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
                    for coordinate, note_info, display_layer in array_info:
                        step.COM("units,type=mm")
                        checkrule.addNote(step, worklayer, coordinate, "please check")
                        if isinstance(display_layer, (list, tuple)):
                            num = 2
                            for show_layer in display_layer:
                                step.display_layer(show_layer, num)
                                num += 1
                        else:
                            step.display_layer(display_layer, 2)

                        # 增加有元素进入板内时同时打开ww层 20230801 by lyh
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
                                    step.display_layer(layer, num + 2)
                            step.PAUSE("{0}{1}".format(log, layer_list))

        if "view_note_detail" in sys.argv[1:]:
            self.create_log_and_update_coordinate(jobname, "view_note_detail", "check_over", {})

    def write_check_log_file(self, jobname, function_name, log):
        log_path = "/tmp/check_log_{0}_{1}.log".format(jobname, function_name)
        with open(log_path, "w") as f:
            f.write(log.encode("cp936"))

    def get_selected_dic_note_coordinate(self, jobname, stepname, step,
                                         worklayer, show_display_layer,
                                         show_pause_log, dic_zu_layer={},
                                         add_note_layer=None, delete_note=True,
                                         calc_legth=None, allsymbol_xy = None):
        """获取被选中的元素的坐标信息及打标记"""

        if not dic_zu_layer.has_key(stepname):
            dic_zu_layer[stepname] = {}

        if delete_note:
            step.COM("note_delete_all,layer={0},user=,note_from=0,note_to=2147483647".format(worklayer))
            if add_note_layer is not None:
                step.COM("note_delete_all,layer={0},user=,note_from=0,note_to=2147483647".format(add_note_layer))
        if not allsymbol_xy:
            STR = r'-t layer -e %s/%s/%s -d FEATURES -o select,units= mm' % (
                jobname, stepname, worklayer)
            infoList = step.INFO(STR)
            add_note_layer = worklayer if add_note_layer is None else add_note_layer
            if dic_zu_layer[stepname].has_key(add_note_layer):
                dic_zu_layer[stepname][add_note_layer].append([checkrule.parseInfoList(step, infoList, calc_legth),
                                                               show_pause_log.encode("utf8"), show_display_layer])
            else:
                dic_zu_layer[stepname][add_note_layer] = [[checkrule.parseInfoList(step, infoList, calc_legth),
                                                           show_pause_log.encode("utf8"), show_display_layer]]
        else:
            add_note_layer = worklayer if add_note_layer is None else add_note_layer
            if dic_zu_layer[stepname].has_key(add_note_layer):
                dic_zu_layer[stepname][add_note_layer].append([allsymbol_xy, show_pause_log.encode("utf8"), show_display_layer])
            else:
                dic_zu_layer[stepname][add_note_layer] = [[allsymbol_xy, show_pause_log.encode("utf8"), show_display_layer]]
        # allsymbol_xy.append((Obj.x, Obj.y, "surface"))
        return dic_zu_layer

    def get_view_dic_layers(self, jobname, stepname, step,
                            worklayer="view_layer", dic_layer_list={},
                            dic_zu_layer={}):
        """记录要查看的层别"""

        if not dic_zu_layer.has_key(stepname):
            dic_zu_layer[stepname] = {}

        dic_zu_layer[stepname][worklayer] = {}
        for key, value in dic_layer_list.iteritems():
            dic_zu_layer[stepname][worklayer][key.encode("utf8")] = value

        return dic_zu_layer

    def create_log_and_update_coordinate(self, jobname, function_name,
                                         log, dic_coordinate):
        """生成日志及上传打标记坐标信息"""
        self.write_check_log_file(jobname, function_name,
                                  "\n".join(log).replace("'", '"') if isinstance(log, (list, tuple)) else log.replace(
                                      "'", '"'))

        if dic_coordinate:
            update_current_job_check_log(os.environ.get("CHECK_ID", "NULL"),
                                         "note_coordinate='{0}'".format(str(dic_coordinate).replace("'", '"')))

    def get_sr_limits(self):
        step = gClasses.Step(job, 'panel')
        layers = innersignalLayers+outsignalLayers
        for layer in layers:
            info = step.INFO("-t layer -e %s/%s/%s  -d FEATURES" % (jobname, step.name, layer))
            lines = [gFeatures.Pad(line) for line in info if 'sh-con2' in line or 'sh-con' in line]
            if lines:
                feax = [fea.x * 25.4 for fea in lines]
                feay = [fea.y * 25.4 for fea in lines]
                sr_xmin, sr_ymin, sr_xmax, sr_ymax = min(feax) + 1, min(feay) + 1, max(feax) - 1, max(feay) - 1
                sr_info = {'sr_xmin' : sr_xmin, 'sr_ymin' : sr_ymin,'sr_xmax' : sr_xmax,'sr_ymax' : sr_ymax}
                return sr_info
        return None


    def check_pth_film_sealing(self):
        """
        检查PTH干膜封孔，http://192.168.2.120:82/zentao/story-view-6200.html
        1.在PNL内检测下类孔是否做干膜封孔（所有coupon内的以下孔都要做）
        1：封孔减铜干膜盖孔设计:钻孔径≤1.8mm按D＋3mil(单边)，钻孔径＞1.8mm按D＋6mil(单边),槽孔依槽长计算
        2：≥5mi的盲孔
        3：所有树脂塞孔的孔
        4 ;所有的PTH孔
        """
        if "panel" in matrixinfo["gCOLstep_name"]:
            dic_zu_layer = {}
            arraylist = []
            tmpLayer = {'tk1' : 'drl_tk1_tmp++',
                        'tk2': 'drl_tk2_tmp++',
                        'laser': 'drl_tk_tmp++',
                        'gk': 'stg_tmp++',
                        'sz': 'szsk_tmp++',
                        }
            pnl_cmd = gClasses.Step(job, 'panel')
            top_gk = 'l1-gk'
            bot_gk = 'l{0}-gk'.format(lay_num)
            if not pnl_cmd.isLayer(top_gk) and not pnl_cmd.isLayer(bot_gk):
                return "success", None
            for layer in tmpLayer.values():
                pnl_cmd.removeLayer(layer)
                pnl_cmd.createLayer(layer)
            stepList = get_panelset_sr_step(jobname=job.name,panelset='panel')
            dict_sgt = {}
            if pnl_cmd.isLayer(top_gk):
                drlList = []
                for layer in pnl_cmd.getLayers():
                    if re.search('^bd1-\d$|^s1-\d$|szsk-c.*.lp$|szsk-2.*.lp$|szsk1-\d.*.lp$', layer) or layer == 'drl' or layer == 'cdc' or layer == 'szsk.lp':
                        drlList.append(layer)
                dict_sgt[top_gk] = drlList
            if pnl_cmd.isLayer(bot_gk):
                drlList = []
                for layer in pnl_cmd.getLayers():
                    if re.search('^bd{0}-\d$|^s{1}-\d$|^szsk-s.*.lp$|^szsk-1.*.lp$|^szsk{2}-\d.*.lp$'.format(lay_num,lay_num,lay_num), layer) or layer == 'drl' or layer == 'cds'or layer == 'szsk.lp':
                        drlList.append(layer)
                dict_sgt[bot_gk] = drlList

            for stepName in stepList:
                step = gClasses.Step(job, stepName)
                step.open()
                step.clearAll()
                step.resetFilter()
                step.COM("units,type=inch")
                for stgName, drlLayers in dict_sgt.items():
                    for lay in tmpLayer.values():
                        step.affect(lay)
                        step.selectDelete()
                    # step.copyLayer(job.name,stepName, stgName, tmpLayer['stg'])
                    step.flatten_layer(stgName, tmpLayer['gk'])
                    step.clearAll()
                    step.affect(tmpLayer['gk'])
                    step.contourize(units='inch')
                    step.unaffect(tmpLayer['gk'])
                    for layer in drlLayers:
                        layerTP = ''
                        step.affect(layer)
                        if layer in ['drl','cdc','cds'] or re.search('^bd', layer):
                            layerTP = 'tk'
                            step.copySel(tmpLayer['tk1'])
                        elif re.search('^s\d', layer):
                            layerTP = 'laser'
                            step.copySel(tmpLayer['laser'])
                        elif re.search('^sz', layer):
                            step.copySel(tmpLayer['sz'])
                        step.clearAll()
                        if layerTP == 'tk':
                            step.affect(tmpLayer['tk1'])
                            if stgName == top_gk:
                                signalLayer = 'l1'
                            else:
                                signalLayer = 'l{0}'.format(lay_num)
                            step.refSelectFilter(signalLayer, polarity='positive')
                            if step.featureSelected():
                                step.resetFilter()
                                step.copySel(tmpLayer['tk2'])
                                step.clearAll()
                                step.affect(tmpLayer['tk2'])
                                step.refSelectFilter(tmpLayer['gk'], mode='disjoint')
                                if step.featureSelected():
                                    log = u"{0}中{1}部分PTH孔未封孔".format(stepName, layer)
                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepName, step,
                                                                                         tmpLayer['tk2'], stgName, log, dic_zu_layer, add_note_layer=layer)
                                    arraylist.append(log)
                            step.resetFilter()
                            step.clearAll()
                            step.affect(tmpLayer['tk1'])
                            step.refSelectFilter(tmpLayer['gk'], mode= 'cover', polarity='positive')
                            step.COM("sel_reverse")
                            if step.featureSelected():
                                step.selectDelete()
                            step.resetFilter()
                            step.COM("sel_delete_atr,attributes=.rout_chain")
                            big_drill = []
                            infoList = step.DO_INFO(
                                "-t layer -e %s/%s/%s -d TOOL" % (job.name, stepName, tmpLayer['tk1']))
                            if infoList:
                                for i, size in enumerate(infoList['gTOOLdrill_size']):
                                    if float(infoList['gTOOLslot_len'][i]) * 25.4 > 1800 or float(size) * 25.4 > 1800:
                                        big_drill.append('r' + size)
                                step.COM("sel_resize,size=6,corner_ctl=no")
                                if big_drill:
                                    step.filter_set(include_syms='\;'.join(big_drill))
                                    step.selectAll()
                                    if step.featureSelected():
                                        step.COM("sel_resize,size=6,corner_ctl=no")
                                step.resetFilter()
                                step.refSelectFilter(tmpLayer['gk'], mode='cover')
                                step.COM("sel_reverse")
                                if step.featureSelected():
                                    log = u"{0}中{1}部分孔径未满足≤1.8mm按D＋3mil(单边)，钻孔径＞1.8mm按D＋6mil(单边)设计".format(stepName,layer)
                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepName, step,
                                                                                         tmpLayer['tk1'], stgName, log, dic_zu_layer, add_note_layer=layer)
                                    arraylist.append(log)
                            step.clearAll()
                        elif layerTP == 'laser':
                            step.clearAll()
                            step.affect(tmpLayer['laser'])
                            step.resetFilter()
                            infoList = step.DO_INFO("-t layer -e %s/%s/%s -d TOOL" % (job.name, stepName, layer))['gTOOLdrill_size']
                            big_drill = []
                            for size in infoList:
                                if float(size) > 5:
                                    big_drill.append('r' + str(size))
                            if big_drill:
                                step.filter_set(include_syms='\;'.join(big_drill))
                                step.selectAll()
                                step.COM("sel_reverse")
                                if step.featureSelected():
                                    step.selectDelete()
                                step.resetFilter()
                                step.refSelectFilter(tmpLayer['gk'],mode='disjoint')
                                if step.featureSelected():
                                    log = u"{0}中{1}部分大于5mil的镭射孔未封孔".format(stepName,layer)
                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepName, step,
                                                                                         tmpLayer['laser'], stgName, log, dic_zu_layer, add_note_layer=layer)
                                    arraylist.append(log)
                            step.clearAll()
                        step.clearAll()
                    step.clearAll()
                    step.resetFilter()
                    step.affect(tmpLayer['sz'])
                    step.refSelectFilter(tmpLayer['gk'], mode='disjoint')
                    if step.featureSelected():
                        log = u"{0}中存在树脂塞孔的孔未作封孔".format(stepName)
                        arraylist.append(log)
                    step.clearAll()
                step.close()
            for lay in tmpLayer.values():
                pnl_cmd.removeLayer(lay)
            if arraylist:
                return arraylist, dic_zu_layer
        return "success", None

    def check_coupon_clip_cu(self):
        """
        http://192.168.2.120:82/zentao/story-view-6931.html
        检测模块切铜
        """
        # 只检测到edit和set,panel中的下一级
        dic_zu_layer = {}
        arraylist = []
        check_steps = {}
        check_type = os.environ.get("INNER_OUTER", '')

        for s in matrixinfo["gCOLstep_name"]:
            if re.search('edit|set|panel', s):
                cur_steplist = get_panelset_sr_step(job.name, s, is_all=False)
                if cur_steplist:
                    check_steps[s] = cur_steplist

        if check_steps:
            tmp_layer = {'fill_layer': 'sr_fill',
                         'fill_edit': 'sr_fill_edit',
                         'flat_layer': 'sr_fill_flat',
                         'flat_layer_reverse': 'sr_fill_flat_reverse',
                         'flat_layer_edit': 'sr_fill_flat_edit',
                         'md_cover': 'md_cover',
                         'md_clip': 'md_clip'}
            matrixInfo = job.matrix.getInfo()
            drl_layers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                           if matrixInfo["gROWcontext"][i] == "board"
                           and matrixInfo["gROWlayer_type"][i] == "drill"]

            for k, v in check_steps.items():
                cus_steps = []
                step = gClasses.Step(job, k)
                step.COM("disp_off")
                step.open()
                for layer in tmp_layer.values():
                    step.removeLayer(layer)
                step.createLayer(tmp_layer['fill_layer'])
                step.createLayer(tmp_layer['fill_edit'])
                step.createLayer(tmp_layer['flat_layer_reverse'])
                for in_step in v:
                    check_dist = 0.0
                    out_dist = 0.5 * float(check_dist)
                    xllc_dist = 0.5 * float(check_dist + 0.25)
                    pcs_dist = -0.255
                    step_cmd = gClasses.Step(job, in_step)
                    if in_step in drl_layers:
                        continue
                    step_cmd.open()
                    step_cmd.COM("units,type=mm")
                    step_cmd.clearAll()
                    step_cmd.resetFilter()
                    step_cmd.COM('cur_atr_set,attribute=.string,text=%s' % in_step)
                    out_dist = '-' + str(out_dist)
                    if in_step == 'xllc-coupon':
                        out_dist = '-' + str(xllc_dist)
                    if re.search(r'^edit$|^set$', in_step):
                        # === 用户不建议检测，此处更改为不铺出板外
                        out_dist = str(0- pcs_dist)
                        cus_steps.append(in_step)
                    if (k == 'panel' and in_step == 'set') or (k == 'set' and in_step == 'edit') or (k == 'set-d-coupon' and in_step == 'edit-d-coupon'):
                        step_cmd.affect(tmp_layer['fill_edit'])
                        step_cmd.COM(
                            'sr_fill,polarity=%s,step_margin_x=%s,step_margin_y=%s,step_max_dist_x=%s,step_max_dist_y=%s,'
                            'sr_margin_x=%s,sr_margin_y=%s,sr_max_dist_x=%s,sr_max_dist_y=%s,nest_sr=no,stop_at_steps=,'
                            'consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=yes'
                            % ('positive', out_dist, out_dist, 2540, 2540, -2540, -2540, 0, 0))

                    else:
                        step_cmd.affect(tmp_layer['fill_layer'])
                        step_cmd.COM(
                            'sr_fill,polarity=%s,step_margin_x=%s,step_margin_y=%s,step_max_dist_x=%s,step_max_dist_y=%s,'
                            'sr_margin_x=%s,sr_margin_y=%s,sr_max_dist_x=%s,sr_max_dist_y=%s,nest_sr=no,stop_at_steps=,'
                            'consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=yes'
                            % ('positive', out_dist, out_dist, 2540, 2540, 0, 0, 0, 0))
                    step_cmd.resetFilter()
                    step_cmd.clearAll()
                    step_cmd.resetFilter()
                # panel中
                step.flatten_layer(tmp_layer['fill_layer'], tmp_layer['flat_layer'])
                step.flatten_layer(tmp_layer['fill_edit'], tmp_layer['flat_layer_edit'])
                step.COM("units,type=mm")
                step.clearAll()
                step.affect(tmp_layer['flat_layer_reverse'])
                step.COM("sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,step_max_dist_x=2540,step_max_dist_y=2540,"
                         "sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=yes,stop_at_steps=,consider_feat=no,"
                         "consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no")
                step.clearAll()
                # # 重复的flatten排除掉，会多报，直接surface
                # step.affect(tmp_layer['flat_layer'])
                # step.contourize(units='mm')
                # step.COM('sel_decompose,overlap=yes')
                # step.clearAll()
                if check_type == 'outer':
                    step.COM('affected_filter,filter=(type=signal|solder_mask&context=board)')
                else:
                    step.COM('affected_filter,filter=(type=signal&context=board&side=inner&pol=positive)')
                step.COM('get_affect_layer')
                baord_layers = step.COMANS.split()
                if not baord_layers:
                    return "success", None
                step.resetFilter()
                # step.refSelectFilter(tmp_layer['flat_layer'])
                no_pass_layers = []
                for cur_layer in baord_layers:
                    # 此处直接和铜层接触比较
                    step.clearAll()
                    step.resetFilter()
                    tmp1 = cur_layer  + '_touch_part_'
                    # tmp2 = tmp_layer['flat_layer'] + cur_layer + '2'
                    if step.isLayer(tmp1):
                        step.affect(tmp1)
                        step.selectDelete()
                    step.clearAll()
                    step.affect(cur_layer)
                    step.refSelectFilter(tmp_layer['flat_layer'])
                    if not step.featureSelected():
                        continue
                    step.copySel(tmp1)
                    step.clearAll()
                    step.affect(tmp1)
                    step.COM("clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,contour_cut=yes,"
                             "margin=0,ref_layer={0},feat_types=line\;pad\;surface\;arc\;text".format(tmp_layer['flat_layer_reverse']))
                    step.clearAll()
                    step.affect(tmp_layer['flat_layer'])
                    step.refSelectFilter(cur_layer)
                    if step.featureSelected():
                        no_pass_layers.append(cur_layer)
                        log = u'%s中层:%s,切铜不完整或有物件进入coupon, 异常物件请查看标记以及临时层%s' % (step.name, cur_layer, tmp1)
                        update_current_job_check_log(os.environ.get("CHECK_ID", "NULL"),
                                                     u"forbid_or_information='{0}'".format(u"拦截"))
                        lay_cmd = gClasses.Layer(step, tmp_layer['flat_layer'])
                        info_indexs = lay_cmd.featSelIndex()
                        step.copySel(tmp_layer['flat_layer'] + cur_layer )
                        # 获取sr_fill坐标
                        allsymbols = []
                        if info_indexs:
                            for index in info_indexs:
                                step.selectNone()
                                step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(tmp_layer['flat_layer'], index))
                                limit = step.DO_INFO("-t layer -e %s/%s/%s -d LIMITS -o select, units=mm" % (jobname, step.name, tmp_layer['flat_layer']))
                                cent_x, cent_y = float(limit['gLIMITSxcenter']), float(limit['gLIMITSycenter'])
                                allsymbols.append((cent_x, cent_y, "surface"))
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, cur_layer,
                                                                                 [cur_layer, tmp1], log, dic_zu_layer,
                                                                                 add_note_layer=cur_layer,
                                                                                 allsymbol_xy=allsymbols)
                step.clearAll()
                step.resetFilter()
                for cur_lay in baord_layers:
                    step.clearAll()
                    step.resetFilter()
                    step.affect(cur_lay)
                    step.filter_set(feat_types='pad;line;arc;surface')
                    step.refSelectFilter(tmp_layer['flat_layer_edit'], mode='cover')
                    if step.featureSelected():
                        log = u'%s中层:%s,切铜不完整或有物件进入拼版单元' % (step.name, cur_lay)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step,
                                                                             cur_lay, cur_lay, log, dic_zu_layer,
                                                                         add_note_layer=cur_lay)
                        arraylist.append(log)
                step.clearAll()
                step.resetFilter()

                # === 挡点层要套出货单元。
                # （厂内单元为：1.对准度 # 2.防漏接 3.钻孔测试条 4.hct-coupon 5.尾孔 6.	防爆偏 7.线路测量coupon）
                info = step.INFO('-t layer -e %s/%s/%s -m script -d FEATURES -o feat_index' % (job.name, step.name, tmp_layer['flat_layer']))
                # 只检测edit,set,zk等step,因为其它step经常间距不足1mm
                # 翟鸣 2023.02.14 hct类coupon不需要挡点层覆盖（需套开挡点）
                indexRegex = re.compile(
                    r'^#\d+\s+#S P 0;.pattern_fill,.string=(dzd.*|.*floujie|drill_test_coupon|sm4-coupon|1-2sm4-coupon|xllc-coupon|drl)')
                indexRegex2 = re.compile(r'^#\d+\s+#S P 0;.pattern_fill,.string=')
                for line in info:
                    if re.search(indexRegex2, line):
                        # === 挡点覆盖层 ===
                        index = line.strip().split()[0].strip('#')
                        step.affect(tmp_layer['flat_layer'])
                        step.COM('sel_layer_feat,operation=select,layer=%s,index=%s' % (tmp_layer['flat_layer'], index))
                        if re.search(indexRegex, line):
                            if step.featureSelected():
                                step.copySel(tmp_layer['md_cover'])
                        else:
                            if step.featureSelected():
                                step.copySel(tmp_layer['md_clip'])
                step.clearAll()
                if step.isLayer(tmp_layer['md_cover']):
                    step.affect('md1')
                    step.affect('md2')
                    step.resetFilter()
                    step.refSelectFilter(tmp_layer['md_cover'])
                    if step.featureSelected():
                        # === 根据影响的层别判断是否有选中的物件，并分别copy至对应层 ===
                        select_layers = []
                        no_pass_layers = []
                        # === 根据影响的层别判断是否有选中的物件，并分别copy至对应层 ===
                        for cur_layer in ['md1', 'md2']:
                            get_sel_fea = step.INFO(
                                "-t layer -e %s/%s/%s -d FEATURES -o select" % ( job.name, step.name, cur_layer))
                            if len(get_sel_fea) > 1:
                                select_layers.append(cur_layer)
                        step.clearAll()
                        for cur_layer1 in select_layers:
                            cur_no_pass = '%s_%s_md_clip+++' % (step.name, cur_layer1)
                            step.removeLayer(cur_no_pass)
                            step.affect(tmp_layer['md_cover'])
                            step.refSelectFilter(cur_layer1)
                            if step.featureSelected():
                                step.copySel(cur_no_pass)
                                no_pass_layers.append(cur_layer1)
                            step.clearAll()
                        if len(no_pass_layers) > 0:
                            for cyl in no_pass_layers:
                                cur_no_pass = '%s_%s_md_clip+++' % (step.name, cyl)
                                step.clearAll()
                                step.affect(cur_no_pass)
                                step.selectAll()
                                # if 'ynh' in job.name:
                                #     step.PAUSE("13")
                                showstr = u'%s中下列层:%s,切铜不完整或有物件进入coupon' % (step.name, cyl)
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step,
                                                                                     cur_no_pass, cyl, showstr,
                                                                                     dic_zu_layer, add_note_layer=cyl)
                            log = u'%s中%s层切铜不完整或有物件进入coupon' % (step.name, ';'.join(no_pass_layers))
                            arraylist.append(log)
                step.clearAll()
                step.resetFilter()

                # === 检测不套除模块是否有挡点。
                # （厂内单元为：1.对准度 # 2.防漏接 3.钻孔测试条 4.hct-coupon 5.尾孔 6.	防爆偏 7.线路测量coupon）
                # === 需要在当前step铺铜，来确定工艺边的大小，不和此块铜皮相交的模块不进行检测 ===
                fill_copper = '%s_fill_copper__' % step.name
                if step.isLayer(tmp_layer['md_clip']):
                    step.removeLayer(fill_copper)
                    step.createLayer(fill_copper)
                    step.affect(fill_copper)
                    step.COM('sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,step_max_dist_x=2540,'
                                 'step_max_dist_y=2540,sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,'
                                 'consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no')

                    step.clearAll()
                    step.affect(tmp_layer['md_clip'])
                    step.refSelectFilter(fill_copper, mode='disjoint')
                    if step.featureSelected():
                        step.selectDelete()
                    step.clearAll()

                    for md_layer in ['md1', 'md2']:
                        cur_no_pass = '%s_%s_no_cover+++' % (step.name, md_layer)
                        step.removeLayer(cur_no_pass)
                        no_pass_layers = []
                        step.affect(tmp_layer['md_clip'])
                        step.resetFilter()
                        step.refSelectFilter(md_layer,mode='cover')
                        if step.featureSelected():
                            step.COM("sel_reverse")
                            if step.featureSelected():
                                step.copySel(cur_no_pass)
                                no_pass_layers.append(md_layer)
                        step.clearAll()
                        if len(no_pass_layers) > 0:
                            for cyl in no_pass_layers:
                                cur_no_pass = '%s_%s_no_cover+++' % (step.name, cyl)
                                step.clearAll()
                                step.affect(cur_no_pass)
                                step.selectAll()
                                showstr = u'%s中下列层:%s,模块未被挡点覆盖' % (step.name, cyl)
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step,
                                                                                     cur_no_pass, cyl, showstr,
                                                                                     dic_zu_layer, add_note_layer=cyl)
                            log = u'层别：%s 模块未被挡点覆盖' % ','.join(no_pass_layers)
                            arraylist.append(log)
                step.clearAll()
                step.resetFilter()
                for layer in tmp_layer.values():
                    # if arraylist and layer == tmp_layer['flat_layer']:
                    #     continue
                    step.removeLayer(layer)
            if arraylist:
                # showMessageInfo(*(arraylist))
                return arraylist,dic_zu_layer
        return "success", None

    def check_coupon_numbers(self):
        """
        检测板边coupon数量是否正确
        """
        dic_zu_layer = {}
        arraylist = []
        if not "panel" in matrixinfo["gCOLstep_name"]:
            return arraylist,dic_zu_layer
        job_dict = judge_job_type(jobname)
        for stepName in matrixinfo["gCOLstep_name"]:
            pnl_sr_steps = job.DO_INFO("-t step -e %s/%s -d REPEAT" % (jobname, stepName))['gREPEATstep']
            # pnl_sr_steps = get_panelset_sr_step(jobname, stepName, is_all=False)
            if stepName == 'panel':
                # === 1.板边测试模块是否有4个
                drill_test_coupon_list_num = len([i for i in pnl_sr_steps if i == 'drill_test_coupon'])
                if drill_test_coupon_list_num < 4:
                    log = u'drill_test_coupon在%s中不是4个,当前数量为%s' % (stepName, drill_test_coupon_list_num)
                    arraylist.append(log)
                if job_dict['laser_board']:
                    hct_coupon_num = len([i for i in pnl_sr_steps if i == 'hct-coupon'])
                    if hct_coupon_num < 2:
                       log = u'hct-coupon在%s中不是2个,当前数量为%s' % (stepName, hct_coupon_num)
                       arraylist.append(log)

                    hct_new_num = len([i for i in pnl_sr_steps if re.match('hct_coupon_new', i)])
                    if hct_new_num < 2:
                        log = u'hct_coupon_new在%s中不是2个,当前数量为%s' % (stepName, hct_new_num)
                        arraylist.append(log)

                # === 3.对准度 dzd_cp应该有4个   周涌通知取消PNL内检测 20250407
                # if job_dict['pth_board']:
                #     dzd_cp_num = len([i for i in pnl_sr_steps if i == 'dzd_cp'])
                #     if dzd_cp_num < 4:
                #         log = u'dzd_cp在%s中不是4个,当前数量为%s' % (stepName, dzd_cp_num)
                #         arraylist.append(log)
                        # warn_text.append(u'dzd_cp在Step:%s中不是4个,当前数量为%s' % (check, dzd_cp_num))

                # === 4.防漏阶，每阶4个 ， pnl中取消检测 20250401 周涌提出
                if job_dict['laser_board']:
                    # for step_i in range(1, job_dict['laser_board'] + 1):
                    #     plus_num = len([i for i in pnl_sr_steps if i == 'plus%s-floujie' % step_i])
                    #     if plus_num < 4:
                    #         log = 'plus{0}-floujie'.format(step_i) + u'在%s中小于4个,当前数量为%s' % (stepName, plus_num)
                    #         arraylist.append(log)

                    # === 5.线路量测coupon，4个
                    # xllc_coupon_num = len([i for i in pnl_sr_steps if i == 'xllc-coupon'])
                    # if xllc_coupon_num < 4:
                    #     log = u'xllc-coupon在Step:%s中不是4个,当前数量为%s' % (stepName, xllc_coupon_num)
                    #     arraylist.append(log)

                    # === 6. 975 c75 系列 hct-cst sir-coupon 每个最少两个 ===
                    if jobname[1:4].lower() in ['975', 'c75']:
                        hct_cust_num = len([i for i in pnl_sr_steps if i == 'hct-cst'])
                        if hct_cust_num < 2:
                            log = u'hct-cst在%s中不是2个,当前数量为%s' % (stepName, hct_cust_num)
                            arraylist.append(log)

                        sir_num = len([i for i in pnl_sr_steps if i == 'sir-coupon'])
                        if sir_num < 2:
                            log = u'sir-coupon在%s中不是2个,当前数量为%s' % (stepName, sir_num)
                            arraylist.append(log)
            elif stepName == 'set':
                # === 1.对准度 dzd_cp应该有1个
                if job_dict['pth_board']:
                    dzd_cp_num = len([i for i in pnl_sr_steps if i == 'dzd_cp'])
                    if dzd_cp_num < 1:
                        log = u'dzd_cp在%s中不是1个,当前数量为%s' % (stepName, dzd_cp_num)
                        arraylist.append(log)

                # === 2.防漏阶，
                if job_dict['laser_board']:
                    for step_i in range(1, job_dict['laser_board'] + 1):
                        plus_num = len([i for i in pnl_sr_steps if i == 'plus%s-floujie' % step_i])
                        if plus_num < 1:
                            log = u'plus%s-floujie在%s中未添加,当前数量为%s' % (step_i, stepName, plus_num)
                            arraylist.append(log)
        if arraylist:
            # showMessageInfo(*(arraylist))
            dic_zu_layer = self.get_view_dic_layers(job.name, 'panel', gClasses.Step(job,'panel'),  dic_layer_list={u'请检查':["ww"]})
            return arraylist, dic_zu_layer
        else:
            return "success", None


    def check_mic_hole(self):
        """
        http://192.168.2.120:82/zentao/story-view-6176.html
        单元内尾数是7的MIC孔，检查MIC孔是否两面焊盘或铜皮开窗，提醒注意铜皮有开窗，铜皮需要补偿
        """
        tmp_layer = {'end7':'end7_tmp_','m1':'m1_en7_tmp_', 'm2':'m2_end7_tmp_','dic':'end7_dic_tmp'}
        gen = genCOM_26.GEN_COM()
        gen.VOF()
        for lay in tmp_layer.values():
            gen.DELETE_LAYER(lay)
            gen.CREATE_LAYER(lay)
        gen.VON()
        for edit_name in gen.GET_STEP_LIST():
            if 'edit' in edit_name:
                dic_zu_layer = {}
                arraylist = []
                step_cmd = gClasses.Step(job,edit_name)
                step_cmd.open()
                step_cmd.clearAll()
                step_cmd.resetFilter()
                for lay in tmp_layer.values():
                    step_cmd.removeLayer(lay)
                    step_cmd.createLayer(lay)
                if step_cmd.isLayer('drl'):
                    d_sizes = gen.DO_INFO("-t layer -e %s/%s/drl -d TOOL -p drill_size" % (jobname,edit_name),units='mm')['gTOOLdrill_size']
                    hole_end7 = ['r' + i for i in d_sizes if i[-1] is '7']
                    if hole_end7:
                        incloud_fiter = ';'.join(hole_end7)
                        log = u"单只内存在{0}的MIC孔".format(incloud_fiter)
                        arraylist.append(log)
                        step_cmd.affect('drl')
                        step_cmd.setSymbolFilter(incloud_fiter)
                        step_cmd.selectAll()
                        if step_cmd.featureSelected():
                            step_cmd.copySel(tmp_layer['end7'])
                        else:continue
                        step_cmd.clearAll()
                        step_cmd.resetFilter()
                        open_sm1, open_sm2= False, False
                        if step_cmd.isLayer('m1'):
                            step_cmd.affect('m1')
                            step_cmd.filter_set(polarity='positive',reset='yes')
                            step_cmd.refSelectFilter(tmp_layer['end7'],mode='include')
                            if step_cmd.featureSelected():
                                step_cmd.copySel(tmp_layer['m1'])
                                step_cmd.clearAll()
                                step_cmd.resetFilter()
                                step_cmd.affect(tmp_layer['m1'])
                                step_cmd.refSelectFilter('l1', polarity='positive')
                                if step_cmd.featureSelected():
                                    open_sm1 = True
                                    step_cmd.moveSel(tmp_layer['dic'])
                            else:step_cmd.clearAll()


                        if step_cmd.isLayer('m2'):
                            step_cmd.clearAll()
                            step_cmd.affect('m2')
                            step_cmd.filter_set(polarity='positive',reset='yes')
                            step_cmd.refSelectFilter(tmp_layer['end7'],mode='include')
                            if step_cmd.featureSelected():
                                step_cmd.copySel(tmp_layer['m2'])
                                step_cmd.clearAll()
                                step_cmd.resetFilter()
                                step_cmd.affect(tmp_layer['m2'])
                                step_cmd.refSelectFilter('l2', polarity='positive')
                                if step_cmd.featureSelected():
                                    open_sm2 = True
                                    step_cmd.moveSel(tmp_layer['dic'])
                            else:step_cmd.clearAll()
                        step_cmd.clearAll()
                        step_cmd.resetFilter()
                        step_cmd.affect(tmp_layer['end7'])
                        step_cmd.refSelectFilter(tmp_layer['dic'],mode='disjoint')
                        if step_cmd.featureSelected():
                            step_cmd.selectDelete()
                        step_cmd.unaffect(tmp_layer['end7'])
                        step_cmd.affect('drl')
                        step_cmd.refSelectFilter(tmp_layer['dic'],mode='touch')
                        if step_cmd.featureSelected():
                            com_lay = 'm1'
                            if open_sm1 and open_sm2:
                                log = u"MIC孔双面铜皮开窗,请检查是否补偿"
                            elif open_sm1 and not open_sm2:
                                log = u"MIC孔C面铜皮开窗,请检查是否补偿"
                            elif not open_sm1 and open_sm2:
                                com_lay = 'm2'
                                log = u"MIC孔S面铜皮开窗,请检查是否补偿"
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, edit_name, step_cmd, 'drl', com_lay, log, dic_zu_layer)
                            arraylist.append(log)

                for lay in tmp_layer.values():
                    step_cmd.removeLayer(lay)
                if arraylist:
                    return arraylist,dic_zu_layer
        return "success", None

    def check_gear_point_desige(self):
        """
        检查阻焊档点  http://192.168.2.120:82/zentao/story-view-6181.html
        1.检测双面开窗的孔是否做档点
        2.检测档点到线路铜是否大于10mil? 应该是不和线路接触的孔?
        3.自动检测挡点大小始终比防焊开窗单边小1mil以上
         4.检测对准度孔上的档点是否小于0.45mm
         5.检测塞孔的孔不做档点
        """

        tmpLayer = {'open': 'tmp_open_drl_++',
                    'no_open': 'tmp_no_open_++',
                    'm1': 'tmp_sm_1_++',
                    'm2': 'tmp_sm_2_++',
                    'md1': 'tmp_md_1_++',
                    'md2': 'tmp_md_2_++',
                    'drl': 'tmp_drl_ref_++',
                    'md1-n': 'tmp_skc_ref_++',
                    'md2-n': 'tmp_sks_ref_++'
                    }

        if "panel" in matrixinfo["gCOLstep_name"]:
            dic_zu_layer = {}
            arraylist = []
            noExit_lay = [lay for lay in ['m1', 'm2', 'md1', 'md2'] if lay not in matrixinfo['gROWname']]
            if noExit_lay:
                log = u"资料中没有%s层" % ','.join(noExit_lay)
                arraylist.append(log)
                return arraylist, dic_zu_layer
            if 'drl' in matrixinfo['gROWname']:
                drlLayer = 'drl'
            elif 'cdc' in matrixinfo['gROWname']:
                drlLayer = 'cdc'
            elif 'cds' in matrixinfo['gROWname']:
                drlLayer = 'cds'
            else:
                drlLayer = None
                log = u"资料中没有钻孔层!"
                arraylist.append(log)
                return arraylist, dic_zu_layer
            for lay in tmpLayer.values():
                job.VOF()
                job.COM("delete_layer,layer={0}".format(lay))
                job.VON()
            if drlLayer and not noExit_lay:
                for lay in tmpLayer.values():
                    job.COM("create_layer,layer={0},context=misc,type=signal,polarity=positive,ins_layer=".format(lay))
                info_p = job.DO_INFO("-t step -e %s/panel -d REPEAT -p step" % jobname)['gREPEATstep']
                step_list = list(set(info_p))
                if 'set' in step_list:
                    info_s = job.DO_INFO("-t step -e %s/set -d REPEAT -p step" % jobname)['gREPEATstep']
                    step_list += list(set(info_s))
                for stepName in step_list:
                    step = gClasses.Step(job, stepName)
                    step.open()
                    step.resetFilter()
                    step.COM("units,type=inch")
                    if re.search('dzd', stepName):
                        for md_name in ['md1', 'md2']:
                            md_histsyms = step.DO_INFO("-t layer -e %s/%s/%s -d SYMS_HIST" % (job.name, stepName, md_name))['gSYMS_HISTsymbol']
                            md_syms = [float(i[1:]) for i in md_histsyms]
                            if md_syms and min(md_syms) * 25.4 < 450:
                                log = u"{0}中{1}层存在小于0.45mm的档点".format(stepName, md_name)
                                arraylist.append(log)
                    step.copyLayer(jobname, stepName, drlLayer, tmpLayer['drl'])
                    for lay in ['m1', 'm2','md1','md2']:
                        step.copyLayer(jobname, stepName, lay, tmpLayer[lay])
                    step.clearAll()
                    for lay in [tmpLayer['m1'],tmpLayer['m2'],tmpLayer['md2'],tmpLayer['md1']]:
                        step.affect(lay)
                    step.contourize(units='inch')
                    step.COM('sel_decompose,overlap=yes')
                    step.clearAll()
                    #检测档点是否比开窗小1mil 和距离铜皮是否10mil
                    for lay_md in [tmpLayer['md2'],tmpLayer['md1']]:
                        if lay_md == tmpLayer['md1']:
                            lay_sm = tmpLayer['m1']
                            show_md = 'md1'
                            show_sm = 'm1'

                        else:
                            lay_sm = tmpLayer['m2']
                            show_md = 'md2'
                            show_sm = 'm2'
                        step.affect(lay_md)
                        if lay_md == tmpLayer['md1']:
                            step.refSelectFilter('l1', mode='disjoint', polarity='positive')
                            if step.featureSelected():
                                step.copySel(tmpLayer['md1-n'])
                                step.clearAll()
                                step.affect(tmpLayer['md1-n'])
                                step.COM("sel_resize,size=20,corner_ctl=no")
                                step.refSelectFilter('l1', mode='touch', polarity='positive')
                                if step.featureSelected():
                                    log = u"{0}中md1层存在NPTH档点距离铜皮小于等于10mil".format(stepName)
                                    arraylist.append(log)
                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepName, step,
                                                                                         tmpLayer['md1-n'], 'l1', log,
                                                                                         dic_zu_layer,
                                                                                         add_note_layer=show_md)
                                step.clearAll()
                        else:
                            step.refSelectFilter('l{0}'.format(lay_num), mode='disjoint', polarity='positive')
                            if step.featureSelected():
                                step.copySel(tmpLayer['md2-n'])
                                step.clearAll()
                                step.affect(tmpLayer['md2-n'])
                                step.COM("sel_resize,size=20,corner_ctl=no")
                                step.refSelectFilter('l{0}'.format(lay_num), mode='touch', polarity='positive')
                                if step.featureSelected():
                                    log = u"{0}中md2层存在NPTH档点距离铜皮小于等于10mil，请注意检查!".format(stepName)
                                    arraylist.append(log)
                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepName, step,
                                                                                         tmpLayer['md2-n'], 'l{0}'.format(lay_num), log,
                                                                                         dic_zu_layer,
                                                                                         add_note_layer=show_md)

                        step.clearAll()
                        step.affect(lay_md)
                        step.COM("sel_resize,size=2,corner_ctl=no")
                        step.refSelectFilter(lay_sm, mode='include')
                        if step.featureSelected():
                            log = u"{0}中{1}层存在挡点未满足比开窗小单边1mil以上，请注意检查!".format(stepName, show_md)
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepName, step,
                                                                                 lay_md, show_sm, log,
                                                                                 dic_zu_layer,
                                                                                 add_note_layer=show_md)
                        step.selectNone()
                        step.COM("sel_resize,size=-2,corner_ctl=no")
                    step.clearAll()
                    sk_clayer,sk_slayer = [],[]
                    for lay in matrixinfo['gROWname']:
                        if re.search('^sz.lp$|^szsk.lp$|^szsk-c.lp$|^szsk1-\d.lp$',lay) or lay == 'lp':
                            sk_clayer.append(lay)
                        elif re.search('szsk{0}-\d.lp'.format(lay_num), lay) or lay == 'lp':
                            sk_slayer.append(lay)
                    if sk_clayer:
                        # 检测C塞孔层是否做挡点
                        for sk in sk_clayer:
                            step.affect(sk)
                            step.refSelectFilter('md1', mode='touch')
                            if step.featureSelected():
                                log = u"塞孔层{0}在md1层存在挡点!".format(sk)
                                arraylist.append(log)
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepName, step,
                                                                                     sk, 'md1', log,
                                                                                     dic_zu_layer,
                                                                                     add_note_layer=sk)
                            step.unaffect(sk)
                    if sk_slayer:
                        # 检测S塞孔层是否做挡点
                        for sk in sk_slayer:
                            step.affect(sk)
                            step.refSelectFilter('md2', mode='touch')
                            if step.featureSelected():
                                log = u"塞孔层{0}在md2层存在挡点!".format(sk)
                                arraylist.append(log)
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepName, step,
                                                                                     sk, 'md2', log,
                                                                                     dic_zu_layer,
                                                                                     add_note_layer=sk)
                            step.unaffect(tmpLayer['sk'])
                    #制作双面开窗孔层
                    step.affect(tmpLayer['drl'])
                    if sk_clayer or sk_slayer:
                        step.refSelectFilter(refLay='\;'.join(sk_clayer+sk_slayer), mode='touch')
                        if step.featureSelected():
                            step.selectDelete()
                    step.refSelectFilter(tmpLayer['m1'],mode='cover')
                    if step.featureSelected():
                        step.moveSel(tmpLayer['open'])
                    step.unaffect(tmpLayer['drl'])
                    step.affect(tmpLayer['open'])
                    step.refSelectFilter(tmpLayer['m2'], mode='cover')
                    step.COM("sel_reverse")
                    if step.featureSelected():
                        step.moveSel(tmpLayer['drl'])
                    #检测双面开窗孔是否加挡点
                    for md in ['md1', 'md2']:
                        step.selectNone()
                        step.refSelectFilter(tmpLayer[md], mode='touch')
                        step.COM("sel_reverse")
                        if step.featureSelected():
                            log = u"{0}中{1}层开窗孔漏加挡点!".format(stepName,md)
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepName, step,
                                                                                 tmpLayer['open'], md, log, dic_zu_layer,add_note_layer=drlLayer)
                    step.unaffect(tmpLayer['open'])
                    #检测档点大小是否比开窗小1-2mil
                    step.close()
            for lay in tmpLayer.values():
                job.VOF()
                job.COM("delete_layer,layer={0}".format(lay))
                job.VON()
            if arraylist:
                return arraylist, dic_zu_layer
        return "success", None

    def check_plug_hole_condition(self):
        """http://192.168.2.120:82/zentao/story-view-4976.html
        1.塞孔制作脚本运行后添加检测动作
        （1）双开钻孔Copy一层，命名：shaungkaivia
        （2）未做塞孔且钻孔对应有锡膏的Via钻孔copy一层，命名：busaikvia
        （3）双开有塞孔的Via孔Copy一层，命名：shaungkaivia-sk
         以上三项作出层别并提示
        """
        dic_zu_layer = {}
        arraylist = []
        if "panel" in matrixinfo["gCOLstep_name"] and "lp" in matrixinfo["gROWname"]:
            pnl_sr_steps = get_panelset_sr_step(jobname, "panel")
            step = gClasses.Step(job, "panel")
            step.removeLayer("shaungkaivia")
            step.removeLayer("no-plughole")
            step.removeLayer("shaungkaivia-sk")
            step.removeLayer("busaikvia")
            for stepname in pnl_sr_steps:
                if stepname in ['drl','qie_hole_coupon_new_drl']:
                    continue
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")
                if not step.isLayer("drl"):
                    continue
                worklayer = "lp"
                # sz_worklayer = 'sz.lp'
                ref_layer = []
                for lay_lp in ['lp', 'sz.lp']:
                    if step.isLayer(lay_lp):
                        ref_layer.append(lay_lp)
                step.clearAll()
                step.affect("drl")
                step.resetFilter()
                # step.setAttrFilter(".drill,option=via")
                step.selectAll()
                if step.featureSelected():
                    step.removeLayer("via_tmp")
                    step.copySel("via_tmp")
                    if stepname in ['coupon-qp', 'coupon-1', 'coupon-2']:
                        step.clearAll()
                        step.resetFilter()
                        step.removeLayer('rout_to_outline_')
                        step.createLayer('rout_to_outline_')
                        # step.affect("rout_to_outline_")
                        step.COM("profile_to_rout,layer=rout_to_outline_,width=100")
                        # step.clearAll()
                        step.affect("via_tmp")
                        # via孔在切片coupon外围的不检测
                        step.refSelectFilter("rout_to_outline_")
                        if step.featureSelected():
                            step.selectDelete()
                        step.clearAll()
                        step.removeLayer("rout_to_outline_")


                    for mask_layer in ["m1", "m2"]:
                        if step.isLayer(mask_layer):
                            step.copyLayer(jobname, stepname, mask_layer, mask_layer + "_tmp")
                            step.clearAll()
                            step.affect(mask_layer + "_tmp")
                            step.contourize()

                            step.clearAll()
                            step.affect("via_tmp")
                            step.resetFilter()
                            step.refSelectFilter(mask_layer + "_tmp", mode="multi_cover")
                            if step.featureSelected():
                                step.copySel(mask_layer + "_open")

                    if step.isLayer("m1_open") and step.isLayer("m2_open"):
                        for mask_layer in ["m1", "m2"]:
                            if step.isLayer(mask_layer):
                                step.clearAll()
                                step.resetFilter()
                                step.affect(mask_layer + "_open")
                                if mask_layer == "m1":
                                    step.refSelectFilter("m2_open")
                                else:
                                    step.refSelectFilter("m1_open")
                                if step.featureSelected():
                                    step.copySel("shaungkaivia")

                                step.resetFilter()
                                step.selectAll()
                                if step.featureSelected():
                                    step.copySel("one_open_si_pad")
                    else:
                        if step.isLayer("m1_open"):
                            step.copyLayer(jobname, stepname, "m1_open", "one_open_si_pad")

                        if step.isLayer("m2_open"):
                            step.copyLayer(jobname, stepname, "m2_open", "one_open_si_pad")

                    if step.isLayer("one_open_si_pad"):
                        step.clearAll()
                        step.resetFilter()
                        step.affect("one_open_si_pad")
                        # step.refSelectFilter(worklayer, mode="disjoint")
                        step.refSelectFilter('\\;'.join(ref_layer), mode="disjoint")
                        if step.featureSelected():
                            step.moveSel("busaikvia")
                            step.clearAll()
                            step.affect("busaikvia")
                            if step.isLayer("p1") or step.isLayer("p2"):
                                for paste_lay in ["p1", "p2"]:
                                    if step.isLayer(paste_lay):
                                        step.refSelectFilter(paste_lay)
                                else:
                                    if step.featureSelected():
                                        step.COM("sel_reverse")
                                        if step.featureSelected():
                                            step.selectDelete()
                                    else:
                                        step.removeLayer("busaikvia")
                            else:
                                step.removeLayer("busaikvia")

                    # 对比铝片检测是否有未开窗孔没做铝片
                    step.copyLayer(jobname, stepname, "via_tmp", "no-plughole")
                    step.clearAll()
                    step.resetFilter()
                    if step.isLayer("shaungkaivia"):
                        step.affect("no-plughole")
                        step.refSelectFilter("shaungkaivia")
                        if step.featureSelected():
                            step.selectDelete()
                        step.clearAll()
                    step.affect("no-plughole")
                    step.refSelectFilter('\\;'.join(ref_layer))
                    if step.featureSelected():
                        step.selectDelete()

                    if step.isLayer("shaungkaivia"):
                        step.clearAll()
                        step.resetFilter()
                        step.affect("shaungkaivia")
                        step.refSelectFilter(worklayer)
                        if step.featureSelected():
                            step.moveSel("shaungkaivia-sk")

                step.removeLayer("m1_tmp")
                step.removeLayer("m2_tmp")
                step.removeLayer("via_tmp")
                step.removeLayer("m1_open")
                step.removeLayer("m2_open")
                step.removeLayer("one_open_si_pad")
                step.clearAll()
                dic_zu = {}
                # 只报告双面开窗切塞孔的类型
                # dic_zu["shaungkaivia"] = u"检测到{0}中有双面开窗的过孔且没有制作塞孔，请到层{1}中查看！"
                dic_zu["shaungkaivia-sk"] = u"检测到{0}中有双面开窗且塞孔的钻孔!"
                # dic_zu["busaikvia"] = u"检测到{0}中有不塞孔的开窗过孔且过孔对应有锡膏，请到层{1}中查看！"
                dic_zu["no-plughole"] = u"检测到{0}中有未开窗但没有塞孔的钻孔！"

                for key, value in dic_zu.iteritems():
                    if step.isLayer(key):
                        displayers = ref_layer + solderMaskLayers
                        layer_cmd = gClasses.Layer(step, key)
                        feat_out = layer_cmd.featCurrent_LayerOut()["pads"]
                        if len(feat_out) > 0:
                            step.clearAll()
                            step.affect('drl')
                            step.refSelectFilter(key)
                            if step.featureSelected():
                                log = value.format(stepname)
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, 'drl', displayers, log, dic_zu_layer)
                                arraylist.append(log)
            step.removeLayer("no-plughole")
            step.removeLayer("shaungkaivia")
            step.removeLayer("shaungkaivia-sk")
            step.removeLayer("busaikvia")

        if arraylist:
            return arraylist, dic_zu_layer
        return "success", None


    def check_set_slotMark(self):
        dic_zu_layer = {}
        arraylist = []
        if "set" not in matrixinfo["gCOLstep_name"]:
            return "success", None
        step = gClasses.Step(job, 'set')
        job_upper = jobname[:12].upper()
        # 查看MI是否需要添加防呆半槽
        inplan = InPlan(jobname)
        mysql = MySql()
        mi_slot = inplan.get_set_add_slot()
        if not mi_slot:
            return "success", None
        mi_slot_size = mi_slot[0]['SLOT_SIZE']
        # 查看是否上传防呆数据至数据库
        job_sql_data = mysql.get_set_mask_slot_data(jobname)
        if not job_sql_data:
            arraylist.append(u"数据库未上传防呆半圆槽数据，请运行3.28上传防呆半槽数据")
            return arraylist, dic_zu_layer
        step.open()
        step.clearAll()
        step.resetFilter()
        step.affect('ww')
        step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.area_name,text=set_pro_slot")
        step.filter_set(feat_types='arc', polarity='positive')
        step.selectAll()
        sel_num = step.featureSelected()
        if not sel_num:
            arraylist.append(u"ww层未定义防呆半圆槽属性，请运行3.28上传防呆半槽数据")
            return arraylist, dic_zu_layer
        elif sel_num > 1:
            log = u"ww层有{0}个带属性set_pro_slot的防呆半槽，请去除多余的属性".format(sel_num)
            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, 'ww', 'ww', log, dic_zu_layer,add_note_layer='ww')
            return arraylist, dic_zu_layer

        # 已上传则查看防呆槽添加的数据
        sql_unit_width = job_sql_data[0]['unit_width']
        sql_unit_height = job_sql_data[0]['unit_height']
        sql_addmark_position = str(job_sql_data[0]['addmark_position'])
        sql_mark_data = job_sql_data[0]['mark_data']
        sql_mark_width = job_sql_data[0]['mark_width']
        # 获取板内防呆槽数据
        lay_cmd = gClasses.Layer(step, 'ww')
        pf = step.getProfile()
        x_size = round(pf.xsize * 25.4)
        y_size = round(pf.ysize * 25.4)
        arc_info = lay_cmd.featSelOut(units='mm')['arcs']
        obj = arc_info[0]
        add_x = obj.xc
        add_y = obj.yc
        x_less = abs(obj.xs - obj.xe)
        y_less = abs(obj.ys - obj.ye)
        if x_less > y_less:
            d_size = round(x_less, 1)
            mark_data = float(add_x - pf.xmin * 25.4)
            if add_y > pf.ycenter * 25.4:
                add_fw = 'upper'
            else:
                add_fw = 'down'
        else:
            d_size = round(y_less, 1)
            mark_data = float(add_y - pf.ymin * 25.4)
            if add_x < pf.xcenter * 25.4:
                add_fw = 'left'
            else:
                add_fw = 'right'
        if abs(d_size - 1.6) < 0.1 :
            d_size = 1.6
        elif abs(d_size - 2) < 0.1 :
            d_size = 2

        if abs(mi_slot_size - d_size) > 0.1:
            log = u"防呆半槽数据和MI指示的数据不一致，MI为{0},CAM为{1}".format(mi_slot_size, d_size)
            arraylist.append(log)
            return arraylist, dic_zu_layer

        if add_fw != sql_addmark_position or abs(mark_data - sql_mark_data) > 0.1 or abs(d_size - sql_mark_width) > 0.1:
            log = u"防呆半槽数据和数据库不一致，请检查或重新运行3.28上传防呆半槽数据"
            arraylist.append(log)
        else:
            # 检查是否和其它型号防呆
            exist_jobs = mysql.check_setmark_slot(x_size, y_size, add_fw, d_size, mark_data)
            if exist_jobs:
                if job_upper in exist_jobs:
                    exist_jobs.remove(jobname[:12].upper())
            if exist_jobs:
                log = u"防呆槽和下列料号未防呆:{0}".format(','.join(exist_jobs))
                arraylist.append(log)
        # 同一料号如果如果数据库未上传数据
        step.clearAll()
        step.resetFilter()
        if arraylist:
            return arraylist, dic_zu_layer

        return "success", None


    def check_silk_fpy(self):
        """
        文字防偏移检测coupon添加检测 http://192.168.2.120:82/zentao/story-view-6907.html
        二次字符检测是否有加对应的防偏移PAD，网印和喷印同时存在时提示
        """
        check_yesno = False
        if ('c1' in silkscreenLayers and 'c1-2' in silkscreenLayers) or \
                ('c2' in silkscreenLayers and 'c2-2' in silkscreenLayers):
            inplan = InPlan(jobname)
            get_flow = inplan.get_inplan_all_flow()
            pro_des = [i['PROCESS_DESCRIPTION'] for i in get_flow]
            if '文字喷印' in pro_des and '文字印刷' in pro_des:
                check_yesno = True
        if not check_yesno:
            return "success", None
        arraylist = []
        dic_zu_layer = {}
        dict_silk = {'c1-2': 'c1', 'c2-2' : 'c2'}
        step = gClasses.Step(job, 'panel')
        step.open()
        step.COM("units,type=mm")
        step.resetFilter()
        step.clearAll()
        for sk_2, sk_1 in dict_silk.items():
            if not step.isLayer(sk_2):
                continue
            step.clearAll()
            sk_2_tmp = 'tmps4000_{0}'.format(sk_2)
            step.removeLayer(sk_2_tmp)
            step.affect(sk_2)
            step.filter_set(include_syms='s4000', polarity='positive')
            step.selectAll()
            sel_sk_2_count = step.featureSelected()
            if sel_sk_2_count < 4:
                log = u"{0}层s4000的字符防偏移测试PAD少于4个!".format(sk_2)
                arraylist.append(log)
                dic_zu_layer = self.get_view_dic_layers(job.name, step.name, step,
                                                        worklayer="view_layer_" + sk_2, dic_layer_list={log: [sk_2,sk_1]},
                                                        dic_zu_layer=dic_zu_layer)
            else:
                #将字符防偏移测试PAD移动到临时层加大
                step.copyToLayer(sk_2_tmp, size= 1000)
                step.clearAll()
                step.affect(sk_1)
                step.resetFilter()
                step.filter_set(feat_types='line', polarity='positive')
                step.refSelectFilter(sk_2_tmp, mode='cover')
                sel_sk_1_count = step.featureSelected()
                if sel_sk_1_count < 16:
                    log = u"{0}层s4000的字符防偏移测试PAD对应的{1}层漏加框线!".format(sk_2 ,sk_1)
                    arraylist.append(log)
                    step.clearAll()
                    step.resetFilter()
                    step.affect(sk_2)
                    step.filter_set(include_syms='s4000', polarity='positive')
                    step.selectAll()
                    dic_zu_layer = self.get_view_dic_layers(job.name, step.name, step,
                                                            worklayer="view_layer_" + sk_2,
                                                            dic_layer_list={log: [sk_2 , sk_1]},
                                                            dic_zu_layer=dic_zu_layer)
                    step.removeLayer(sk_2_tmp)
        step.clearAll()
        step.resetFilter()
        if arraylist:
            return arraylist,dic_zu_layer

        return "success", None

    def check_mi_cam_bar_design(self):
        """
        检测和MI的靶孔设计规则是否一致
        """
        arraylist = []
        dic_zu_layer = {}
        job_sql = jobname[:13].upper()
        inplan = InPlan(job_sql)
        data_info = get_outer_target_condition(job_sql)
        mrp_info = inplan.get_inplan_mrp_info(condtion="1=1")
        if not data_info or 'panel' not in matrixinfo['gCOLstep_name']:
            return "success", None
        step = gClasses.Step(job, 'panel')
        step.open()
        step.clearAll()
        step.resetFilter()

        # 检测线路层对应5代靶标设计是否正确
        cores_proess_nums = [mrp['PROCESS_NUM'] for mrp in mrp_info]
        process_numbers = [mrp['PROCESS_NUM'] for mrp in mrp_info if mrp['PROCESS_NUM'] != 1]
        for mrp in mrp_info:

            # 开料钻的镭射孔，NV系列第一次压合有盲孔且core层数≥3时，第一次次外层图形使用靶孔对位，其它都需要使用5代靶对位
            nv_direct_laser = False
            if mrp['PROCESS_NUM'] == min(process_numbers) and mrp['PROCESS_NUM'] <> max(process_numbers) \
                    and jobname[1:4] in ['a86', 'd10'] and cores_proess_nums.count(1) >= 3:
                nv_direct_laser = True
            fromLay = mrp['FROMLAY'].lower()
            toLay = mrp['TOLAY'].lower()
            num1, num2 = fromLay.replace('l', ''), toLay.replace('l', '')
            top_laser_layer = [ls for ls in laser_drill_layers if ls.replace('s','').split('-')[0] == num1]
            bot_laser_layer = [ls for ls in laser_drill_layers if ls.replace('s', '').split('-')[0] == num2]

            # 判断是否开料钻镭射孔，
            direct_laser = False
            if cores_proess_nums.count(1) == 1 and (top_laser_layer or bot_laser_layer):
                direct_laser = True
            check_v5_bar = {fromLay: top_laser_layer, toLay: bot_laser_layer}
            for lay, laser_val in check_v5_bar.items():
                step.clearAll()
                step.resetFilter()
                step.affect(lay)
                step.setSymbolFilter('hdi-dwpad')
                if not laser_val or direct_laser or nv_direct_laser:
                    if not laser_val:
                        log = u"{0}层没有对应镭射钻带，不需要设计5代靶".format(lay)
                    elif direct_laser:
                        log = u"开料钻镭射孔，{0}不需要设计5代靶".format(lay)
                    else:
                        log = u"NV系列第一次压合有盲孔且core层数≥3时,第一次次外层线路不需要设计5代靶".format(lay)
                    step.selectAll()
                    if step.featureSelected():
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, lay, lay, log, dic_zu_layer, add_note_layer=lay)
                else:
                    step.selectAll()
                    if not step.featureSelected():
                        log = u"{0}层按准则需要设计5代靶，但CAM资料中未添加".format(lay)
                        arraylist.append(log)
                    else:
                        step.refSelectFilter(refLay='\\;'.join(laser_val))
                        if step.featureSelected() < 4:
                            log = u"{0}层5代靶设计数量不对".format(lay)
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, lay, lay, log, dic_zu_layer, add_note_layer=lay)
                # 检测和INPLAN的设计是否一致
                step.clearAll()
                step.affect(lay)
                step.setSymbolFilter('hdi-dwpad')
                if laser_val:
                    step.selectAll()
                    if mrp['V5LASER']:
                        if not step.featureSelected():
                            log = u"{0}层MI流程需要设计5代靶，但CAM资料没有添加".format(lay)
                            arraylist.append(log)
                    else:
                        if step.featureSelected():
                            log = u"{0}层MI流程不需要设计5代靶，但CAM资料有设计".format(lay)
                            arraylist.append(log)

        # TT靶孔和T靶设计的条件
        fg_info = get_laser_fg_type(job_sql)
        dic_outer_target_info = {}
        fg_type = [x for x in fg_info if x["PNL_PARCELLATION_METHOD_"] > 1]
        for index, dic_target_info in enumerate(sorted(data_info, key=lambda x: x["PROCESS_LEVEL"] * -1)):
            mrp_name = dic_target_info["MRP_NAME"]
            # 针对A86/D10系列，第一次压合有盲孔且core层数≥3时，第一次压合的线路层不用五代靶对位，需打八靶
            if dic_target_info["PROCESS_LEVEL"] == 2 and dic_target_info["LASER_NAME"]:
                if cores_proess_nums.count(1) >= 3 and jobname[1:4] in ['a86', 'd10']:
                    dic_outer_target_info[mrp_name] = dic_target_info

            if fg_type:
                # 存在镭射分割 且N-1 层无镭射的情况
                if dic_target_info["LASER_NAME"] and index < len(data_info) - 1:
                    if not data_info[index + 1]["LASER_NAME"]:
                        dic_outer_target_info[mrp_name] = dic_target_info

        mrp_info = inplan.get_inplan_mrp_info()
        for mrp in mrp_info:
            mrp_name = mrp["MRPNAME"]
            mrp_xary_type = mrp['XARY_TARGET_TYPE_']

            if mrp_xary_type == 1:
                mi_bar = 4
            elif mrp_xary_type == 2:
                mi_bar = 8
            else:
                mi_bar = 0

            (lam_des, from_lyr, to_lyr) = (int(mrp['PROCESS_NUM']) - 1, str(mrp['FROMLAY']).lower(), str(mrp['TOLAY']).lower())
            from_id = int(from_lyr[1:])
            from_next = from_id + 1
            to_id = int(to_lyr[1:])
            to_pre = to_id - 1
            from_next_layer = 'l' + str(from_next)
            to_pre_layer = 'l' + str(to_pre)
            index_name = str(lam_des) * 2
            if '-' not in mrp_name:
                index_name = 'TT'

            if not mi_bar:
                log = u"压合级别：{0}，MI流程未勾选打几靶，请反馈MI".format(lam_des)
                arraylist.append(log)

            step.clearAll()
            step.resetFilter()
            step.setSymbolFilter('hdi1-bs*')
            for next_lay in [from_next_layer, to_pre_layer]:
                step.affect(next_lay)
                step.selectAll()
                if dic_outer_target_info.has_key(mrp_name):
                    # 检测资料中是否含有TT靶
                    if step.featureSelected() < 4:
                        log = u"压合级别:{0},按规则需要使用8靶对位，但是资料{1}层未设计{2}靶".format(lam_des,next_lay, index_name)
                        arraylist.append(log)
                else:
                    if step.featureSelected():
                        log = u"压合级别:{0},按规则需要使用4靶对位，但是资料{1}层有添加{2}靶".format(lam_des,next_lay, index_name )
                        arraylist.append(log)
                # 查询和INPLAN流程备注是否一致
                if mi_bar == 4:
                    if step.featureSelected():
                        log = u"压合级别：{0}，MI流程打4靶，但是资料{1}层为8靶设计".format(lam_des, next_lay)
                        arraylist.append(log)
                elif mi_bar == 8:
                    if not step.featureSelected():
                        log = u"压合级别：{0}，MI流程打8靶，但是CAM资料{1}层为4靶设计".format(lam_des, next_lay)
                        arraylist.append(log)
        step.clearAll()
        step.resetFilter()
        if arraylist:
            return arraylist, dic_zu_layer

        return "success", None

    def check_detch_imp_line(self):
        """
        检测阻抗线动态补偿是否缺失
        """
        res = os.environ.get("INNER_OUTER", "inner")
        if res == 'inner':
            res_layers = innersignalLayers
        else:
            res_layers = outsignalLayers
        step_list = job.getSteps()
        if 'edit' in step_list:
            dic_zu_layer = {}
            arraylist = []
            stepName = 'edit'
            step = gClasses.Step(job, stepName)
            step.open()
            step.clearAll()
            step.resetFilter()
            tmp_layer = {'line': 'line_detch_tmp', 'sf': 'surface_detch_tmp'}
            for tplayer in tmp_layer.values():
                step.removeLayer(tplayer)
                step.createLayer(tplayer)
            for layer in res_layers:
                step.clearAll()
                step.resetFilter()
                step.affect(tmp_layer['line'])
                step.affect(tmp_layer['sf'])
                step.selectDelete()
                step.clearAll()
                step.affect(layer)
                step.filter_set(feat_types='line;arc', polarity='positive')
                step.setAttrFilter('.imp_line')
                step.selectAll()
                if step.featureSelected():
                    step.copySel(tmp_layer['line'])
                step.resetFilter()
                step.filter_set(polarity='negative')
                step.selectAll()
                if step.featureSelected():
                    step.copySel(tmp_layer['line'])
                step.clearAll()
                step.resetFilter()
                step.affect(layer)
                step.filter_set(feat_types='surface', polarity='positive')
                step.setAttrFilter('.imp_line')
                step.setAttrFilter('.detch_comp')
                step.selectAll()

                if step.featureSelected():
                    step.copySel(tmp_layer['sf'])
                else:
                    # 若没有选择到动补铜皮默认未制作，跳出本次循环
                    continue
                step.clearAll()
                step.resetFilter()
                step.affect(tmp_layer['sf'])
                step.COM("units, type=inch")
                step.contourize(units='inch', accuracy='0.01')
                # step.COM("sel_resize,size=0.2,corner_ctl=no")
                step.clearAll()
                # 泪滴删除
                step.affect(tmp_layer['line'])
                step.setAttrFilter('.tear_drop')
                step.selectAll()
                if step.featureSelected():
                    step.selectDelete()
                step.resetFilter()
                step.contourize(units='inch', accuracy='0.01')
                # 动补后可能 存在部分误差，将线条减小单边0.5mil
                step.COM("sel_resize,size=-1,corner_ctl=no")
                step.refSelectFilter(tmp_layer['sf'], mode='cover')
                # if 'ynh' in job.name:
                #     step.PAUSE("3")
                if step.featureSelected():
                    step.selectDelete()
                step.selectAll()
                if step.featureSelected():
                    step.clearAll()
                    step.resetFilter()
                    step.affect(layer)
                    step.filter_set(feat_types='line;arc', polarity='positive')
                    step.setAttrFilter('.imp_line')
                    step.refSelectFilter(tmp_layer['line'])
                    if step.featureSelected():
                        log = u"{0}层部分阻抗线未做动态补偿!".format(layer)
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepName, step,
                                                                             layer, layer,log, dic_zu_layer, add_note_layer=layer)
                    step.clearAll()
                    step.resetFilter()
                step.clearAll()
                step.resetFilter()

            for tplayer in tmp_layer.values():
                step.removeLayer(tplayer)
            step.clearAll()
            step.resetFilter()
            if arraylist:
                return arraylist, dic_zu_layer
        return "success", None

    def check_half_drill_linek(self):
        """
        检测半孔锣盖选化油图纸是否上传
        """
        arraylist = []
        dic_zu_layer = {}
        inplan = InPlan(jobname)
        get_flow = inplan.get_inplan_all_flow()
        if get_flow:
            linek_pd = False
            half_rout = False
            for d in get_flow:
                if d['WORK_CENTER_CODE'] == '印选化油':
                    linek_pd = True
                elif d['WORK_CENTER_CODE'] == '半孔锣' and linek_pd:
                    half_rout = True
                    break
            # 检测对应输出路径下面是否有图纸
            if half_rout:
                job_pic = job.name.upper().split("-")[0][:-1]
                pic_name = u'{0}锣半孔盖选化油位置图.png'.format(job_pic)
                output_path = ur"/windows/174.file/产品监控资料/IPQC监控图纸/{0}系列/{1}/锣半孔盖选化图纸".format(job.name[1:4].upper(),job_pic)
                file_name = os.path.join(output_path, pic_name)
                if not os.path.isfile(file_name):
                    log = u'路径:{0},下未发现->{1},请确认是否运行12.21-输出锣半孔盖选化油位置程序'.format(output_path,pic_name)
                    arraylist.append(log)
            if arraylist:
                return arraylist, dic_zu_layer
        return "success", None

    def check_erp_gold_areas(self):
        arraylist = []
        dic_zu_layer = {}
        inplan = InPlan(jobname)
        erp_area = {}
        erp = ERP()
        get_data = inplan.getSurfaceTreatment()
        gf_types = [d for d in get_data if 'GF' in d['表面处理']]
        inplan_data = inplan.get_inplan_all_flow()
        gf_dj = False
        for d in inplan_data:
            if d['PROCESS_DESCRIPTION'] == u'电镀镍金':
                gf_dj = True
        # 如果是镀金的型号检测是否上传镀金面积
        if gf_types or gf_dj:
            gf_erp = erp.get_area(jobname)
            if gf_erp:
                dict_erea = gf_erp[0]
                if dict_erea['C面镀金面积']:
                    erp_area['c'] = dict_erea['C面镀金面积']
                if dict_erea['S面镀金面积']:
                    erp_area['c'] = dict_erea['S面镀金面积']
                if not erp_area:
                    log = u'镀金面积未上传'
                    arraylist.append(log)
        if arraylist:
            return arraylist, dic_zu_layer

        return "success", None

    def check_goldfiger_old(self):
        """
        检测金手指是否漏镀,检测蚀刻引线流程做法是否正确
        """
        arraylist = []
        dic_zu_layer = {}
        inplan = InPlan(jobname)
        erp_area = {}
        erp = ERP()
        get_data = inplan.getSurfaceTreatment()
        gf_types = [d for d in get_data if 'GF' in d['表面处理']]
        inplan_data = inplan.get_inplan_all_flow()
        gf_dj = False
        for d in inplan_data:
            if d['PROCESS_DESCRIPTION'] == u'电镀镍金':
                gf_dj = True
        gf_erp = erp.get_area(jobname)
        if gf_erp or gf_dj:
            dict_erea = gf_erp[0]
            if dict_erea['C面镀金面积']:
                erp_area['c'] = dict_erea['C面镀金面积']
            if dict_erea['S面镀金面积']:
                erp_area['c'] = dict_erea['S面镀金面积']

        if not gf_types or 'panel' not in matrixinfo["gCOLstep_name"]:
            return "success", None
        check_pcb = None
        if "set" in matrixinfo["gCOLstep_name"]:
            check_pcb = 'set'
        else:
            if 'edit' in matrixinfo["gCOLstep_name"]:
                check_pcb = 'edit'
            else:
                log = u'非常规STEP命名，没有SET或EDIT，请自行检查'
                arraylist.append(log)
        if not check_pcb:
            return arraylist, dic_zu_layer
        step = gClasses.Step(job, 'panel')
        pnl_steps = get_panelset_sr_step(jobname, 'panel')
        gf_steps = [s for s in pnl_steps if s in ['edit', 'set']]
        boardLayers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                             if matrixInfo["gROWcontext"][i] == "board"]

        # check_xlym = {'xlym-c': 'l1', 'xlym-s': 'l{0}'.format(int(jobname[4:6]))}
        if not erp_area:
            log = u'镀金面积未上传'.format()
            arraylist.append(log)
            update_current_job_check_log(os.environ.get("CHECK_ID", "NULL"),
                                         u"forbid_or_information='{0}'".format(u"拦截"))

            # 获取流程中去金手指引线是酸蚀还是碱蚀
        slym_resize = 0
        etch_sk = None

        for d in inplan_data:
            if d['PROCESS_DESCRIPTION'] == u'显影/蚀刻/去膜' and u'金手指去镀金导线' in d['WORK_CENTER_CODE']:
                slym_resize = 3
                etch_sk = 's'
            elif d['PROCESS_DESCRIPTION'] == u'碱性蚀刻' and u'金手指去导线' in d['WORK_CENTER_CODE']:
                slym_resize = 0
                etch_sk = 'j'
        for layer in outsignalLayers:
            if layer == 'l1':
                xlym = 'xlym-c'
                if 'xlym-c' not in boardLayers and 'gold-c' in boardLayers:
                    xlym = 'gold-c'
                etch = 'etch-c'
            else:
                xlym = 'xlym-s'
                if 'xlym-s' not in boardLayers and 'gold-s' in boardLayers:
                    xlym = 'gold-s'
                etch = 'etch-s'
            if step.isLayer(xlym) or step.isLayer(etch):
                layer_info = job.INFO(
                    "-t layer -e {0}/{1}/{2} -d FEATURES  -o break_sr".format(jobname, check_pcb, layer))
                gold_features = [line for line in layer_info if 'string=gf' in line]
                # 缩小至WW范围内
                out_gold = False
                if gold_features and 'edit' in matrixinfo["gCOLstep_name"]:
                    step_check = gClasses.Step(job, 'edit')
                    step_check.open()
                    step_check.removeLayer('fill_figer')
                    step_check.createLayer('fill_figer')
                    step_check.clearAll()
                    step_check.affect('fill_figer')
                    step_check.COM('units,type=mm')
                    step_check.COM("sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,step_max_dist_x=2540,step_max_dist_y=2540,"
                                   "sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,consider_feat=no,consider_drill=no,"
                                   "consider_rout=no,dest=affected_layers,attributes=no")
                    step_check.clearAll()
                    step_check.affect(layer)
                    step_check.filter_set(feat_types='pad')
                    step_check.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=gf")
                    step_check.refSelectFilter('fill_figer')
                    if not step_check.featureSelected():
                        out_gold  = True
                    step_check.clearAll()
                    step_check.resetFilter()
                    step_check.close()
                if not gold_features or out_gold:
                    log = u'{0}层没有定义金手指属性'.format(layer)
                    arraylist.append(log)
                else:
                    figerLayer_pcs = layer + '_goldfiger_pcs'
                    touch_figer_line = layer + '_touch_figer'
                    outline = 'ww_profile'
                    step.removeLayer(figerLayer_pcs)
                    step.createLayer(figerLayer_pcs)
                    step.removeLayer(touch_figer_line)
                    step.createLayer(touch_figer_line)
                    step.removeLayer(outline)
                    step.createLayer(outline)
                    for s in gf_steps:
                        step_cmd = gClasses.Step(job, s)
                        step_cmd.open()
                        step_cmd.COM("units,type=inch")
                        step_cmd.COM("profile_to_rout,layer={0},width=5".format(outline))
                        step_cmd.clearAll()
                        step_cmd.resetFilter()
                        step_cmd.affect(layer)
                        step_cmd.filter_set(feat_types='pad')
                        step_cmd.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=gf")
                        step_cmd.selectAll()
                        if step_cmd.featureSelected():
                            step_cmd.copyToLayer(figerLayer_pcs)
                            # 把接触到手指的线条copy到手指层
                            step_cmd.selectNone()
                            step_cmd.resetFilter()
                            step_cmd.filter_set(feat_types='line;arc',polarity='positive')
                            step_cmd.refSelectFilter(figerLayer_pcs)
                            if step_cmd.featureSelected():
                                step_cmd.copyToLayer(touch_figer_line)
                            # 考虑到金手指可能还会被负性覆盖，把线路负性盖过去
                            step_cmd.resetFilter()
                            step_cmd.selectNone()
                            step_cmd.filter_set(polarity='negative')
                            step_cmd.refSelectFilter(figerLayer_pcs)
                            if step_cmd.featureSelected():
                                step_cmd.copyToLayer(figerLayer_pcs)
                            step_cmd.clearAll()
                            step_cmd.resetFilter()
                        step_cmd.resetFilter()
                        step_cmd.clearAll()
                        step_cmd.affect(figerLayer_pcs)
                        step_cmd.contourize(units='inch')
                        step_cmd.clearAll()
                        step_cmd.affect(touch_figer_line)
                        step_cmd.refSelectFilter(outline, mode='disjoint')
                        if step_cmd.featureSelected():
                            step_cmd.selectDelete()
                        step_cmd.selectAll()
                        if step_cmd.featureSelected():
                            step_cmd.selectNone()
                            step_cmd.COM("clip_area_strt")
                            step_cmd.COM(
                                "clip_area_end,layers_mode=affected_layers,layer=,area=profile,area_type=rectangle,"
                                "inout=outside,contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
                        step_cmd.selectAll()
                        if step_cmd.featureSelected():
                            step_cmd.selectNone()
                            step_cmd.COM("clip_area_strt")
                            step_cmd.COM("clip_area_end,layers_mode=layer_name,layer={0},area=reference,area_type=rectangle,"
                                         "inout=inside,contour_cut=yes,margin=0,ref_layer={1},feat_types=line\;pad\;surface\;arc\;text".
                                         format(touch_figer_line,figerLayer_pcs))
                        step_cmd.resetFilter()
                        step_cmd.clearAll()
                        step_cmd.close()
                    # 检测在pnl中有没有被覆盖，因为可能覆盖层不在当前step
                    step.open()
                    if step.isLayer(xlym):
                        figerLayer_xlym = layer + '_goldfiger_xlym'
                        xlym_flen = xlym + '_flen'
                        step.removeLayer(xlym_flen)
                        step.createLayer(xlym_flen)
                        step.removeLayer(figerLayer_xlym)
                        step.createLayer(figerLayer_xlym)
                        step.flatten_layer(xlym, xlym_flen)
                        step.flatten_layer(figerLayer_pcs, figerLayer_xlym)
                        step.clearAll()
                        step.resetFilter()
                        step.affect(xlym_flen)
                        step.contourize(units='inch')
                        # 加大单边.mil
                        step.COM("sel_resize,size={0},corner_ctl=no".format(slym_resize * 2 + 0.05))
                        step.clearAll()
                        step.affect(figerLayer_xlym)
                        step.contourize(units='inch')
                        step.refSelectFilter(xlym_flen, mode='cover')
                        if step.featureSelected():
                            step.selectDelete()
                        step.selectAll()
                        # step.PAUSE("11")
                        if step.featureSelected():
                            log = u'镀金干膜层{0}要覆盖{1}层金手指'.format(xlym, layer)
                            arraylist.append(log)
                            dic_zu_layer = self.get_view_dic_layers(job.name, step.name, step,
                                                                    worklayer="view_layer_" + figerLayer_xlym,
                                                                    dic_layer_list={log: [figerLayer_xlym, xlym]},
                                                                   dic_zu_layer=dic_zu_layer)
                        else:
                            step.removeLayer(figerLayer_xlym)
                        step.removeLayer(xlym_flen)
                    if step.isLayer(etch) and etch_sk:
                        figerLayer_etch = layer + '_goldfiger_etch'
                        etch_flen = etch + '_flen'
                        step.clearAll()
                        step.resetFilter()
                        step.removeLayer(etch_flen)
                        step.createLayer(etch_flen)
                        step.removeLayer(figerLayer_etch)
                        step.createLayer(figerLayer_etch)
                        step.flatten_layer(etch, etch_flen)
                        step.affect(etch_flen)
                        step.contourize(units='inch')
                        step.clearAll()
                        if etch_sk == 's':
                            step.flatten_layer(figerLayer_pcs, figerLayer_etch)
                            step.affect(figerLayer_etch)
                            step.contourize(units='inch')
                            step.refSelectFilter(etch_flen, mode='cover')
                            step.COM("sel_reverse")
                            if step.featureSelected():
                                log = u'酸性蚀刻，在HDI外层站曝光，资料需为负,引线位置不开窗，引线以外位置需开窗，请注意检查！'
                                arraylist.append(log)
                                dic_zu_layer = self.get_view_dic_layers(job.name, step.name, step,
                                                                        worklayer="view_layer_" + figerLayer_etch,
                                                                        dic_layer_list={log: [figerLayer_etch, etch]},
                                                                        dic_zu_layer=dic_zu_layer)
                            else:
                                step.removeLayer(figerLayer_etch)
                        else:
                            touch_flen = touch_figer_line + 'flen'
                            step.flatten_layer(touch_figer_line, touch_flen)
                            step.affect(touch_flen)
                            step.contourize(units='inch')
                            step.refSelectFilter(etch_flen, mode='cover')
                            step.COM("sel_reverse")
                            if step.featureSelected():
                                log = u'碱性蚀刻，在HDI选化站曝光，资料需为正，引线位置开窗，请注意检查！'
                                arraylist.append(log)
                                dic_zu_layer = self.get_view_dic_layers(job.name, step.name, step,
                                                                    worklayer="view_layer_" + touch_flen,
                                                                    dic_layer_list={log: [touch_flen, etch]},
                                                                    dic_zu_layer=dic_zu_layer)
                            else:
                                step.removeLayer(touch_flen)

                        step.removeLayer(etch_flen)
                    step.removeLayer(figerLayer_pcs)
                    step.removeLayer(touch_figer_line)
                    step.removeLayer('fill_figer')
        if arraylist:
            # showMessageInfo(';'.join(arraylist))
            return arraylist, dic_zu_layer
        else:
            return "success", None

    def check_open_sm(self):
        """
        检测二次阻焊开窗是否正确 http://192.168.2.120:82/zentao/story-view-8737.html
        第二次曝光资料将正常开窗单边估大1.5mil，估大后桥最小必须保证3.5mil或估大后取大
        针对第一次阻焊资料设计为TXT属性及动态变量字体位置，做开通窗处理，比第一次变量文字单边大10mil
        """
        arraylist = []
        dic_zu_layer = {}
        if "panel" not in matrixinfo["gCOLstep_name"]:
            return "success", None
        step = gClasses.Step(job, 'panel')
        #获取panel中含有哪些拼版
        check_steps = get_panelset_sr_step(jobname, 'panel', is_all=True)
        check_sm_layers = {}
        if step.isLayer('m1-2'):
            if not step.isLayer('m1'):
                log = u"存在m1-2层但是资料中没有m1层请检查"
                arraylist.append(log)
            else:
                check_sm_layers['m1-2'] = 'm1'
        elif step.isLayer('m2-2'):
            if not step.isLayer('m2'):
                log = u"存在m2-2层但是资料中没有m2层请检查"
                arraylist.append(log)
            else:
                check_sm_layers['m2-2'] = 'm2'

        for stepName in check_steps:
            step_cmd = gClasses.Step(job, stepName)
            step_cmd.open()
            step_cmd.COM("units,type=inch")
            for sm_2, sm_1 in check_sm_layers.items():
                step_cmd.clearAll()
                step_cmd.resetFilter()
                back_sm2 = sm_2 + 'back_open'
                back_sm1 = sm_1 + 'back_open'
                step_cmd.copyLayer(job=jobname, step=stepName, lay=sm_1, dest_lay=back_sm1)
                step_cmd.copyLayer(job=jobname, step=stepName, lay=sm_2, dest_lay=back_sm2)
                step_cmd.affect(back_sm2)


    def check_dkfilm_area_inner(self):
        """
        电金夹头位留铜检测内层镀孔只检测铜皮
        """

        arraylist = []
        dic_zu_layer = {}
        res = os.environ.get("INNER_OUTER", "inner")
        # job.PAUSE(res)
        if "panel" not in matrixinfo["gCOLstep_name"]:
            return "success", None
        step = gClasses.Step(job, 'panel')
        inplan = InPlan(jobname)
        mrp_info = inplan.get_inplan_mrp_info()
        check_dklayers = {}
        for mrp in mrp_info:
            mrp_name = mrp["MRPNAME"]
            process_num = mrp['PROCESS_NUM']
            pnl_rout = 'pnl_rout{0}'.format(process_num -1)
            if '-' in mrp_name:
                from_lay = mrp['FROMLAY']
                to_lay = mrp['TOLAY']
                if from_lay and to_lay:
                    dk1, dk2 = from_lay.lower() + '-dk', to_lay.lower() + '-dk'
                    mrp_dk_layers = []
                    for lay in [dk1, dk2]:
                        if step.isLayer(lay):
                            mrp_dk_layers.append(lay)
                    if mrp_dk_layers:
                        check_dklayers[pnl_rout] = mrp_dk_layers

        if not check_dklayers:
            return "success", None

        step.open()
        step.COM("units,type=mm")
        pf = step.getProfile()
        pf_xmin = pf.xmin * 25.4
        pf_xmax = pf.xmax * 25.4
        pf_ymin = pf.ymin * 25.4
        pf_ymax = pf.ymax * 25.4
        # 获取sr区域
        sr_info = {}
        for info_layer in outsignalLayers + innersignalLayers:
            # 用角线来确定sr区域角线有两类 sh-con,sh-con2
            info = step.INFO("-t layer -e %s/%s/%s  -d FEATURES, units=mm" % (jobname, step.name, info_layer))
            lines = [gFeatures.Pad(line) for line in info if 'sh-con2' in line or 'sh-con' in line]
            if lines:
                feax = [fea.x for fea in lines]
                feay = [fea.y for fea in lines]
                sr_info = {'sr_xmin': min(feax) + 1,
                           'sr_ymin': min(feay) + 1,
                           'sr_xmax': max(feax) - 1,
                           'sr_ymax': max(feay) - 1,
                           }
                break

        step.clearAll()
        step.resetFilter()

        compen_rout = 'compensate_routline_clip'
        step.removeLayer(compen_rout)
        for pnl_rout_name, check_layers in check_dklayers.items():
            # 锣带转化实体
            if not step.isLayer(pnl_rout_name):
                log = u"镀孔层：{0}未发现对应的锣边带{1},请检查资料".format(pnl_rout_name, ','.join(check_layers))
                arraylist.append(log)
                continue
            # 锣带转化为线条
            step.affect(pnl_rout_name)
            step.COM("compensate_layer,source_layer=%s,dest_layer=%s,dest_layer_type=document" % (pnl_rout_name, compen_rout))
            step.clearAll()
            step.affect(compen_rout)
            step.filter_set(feat_types="pad;arc")
            step.selectAll()
            if step.featureSelected():
                step.selectDelete()
            step.resetFilter()
            lay_cmd = gClasses.Layer(step, compen_rout)
            featues_lines = lay_cmd.featCurrent_LayerOut(units='mm')['lines']
            clip_rout_xmin, clip_rout_xmax, clip_rout_ymin, clip_rout_ymax = '', '', '', ''
            clip_rout_size = []
            for obj in featues_lines:
                if obj.xe == obj.xs:
                    if obj.xe > sr_info['sr_xmax']:
                        if (obj.ye > sr_info['sr_ymax'] and obj.ys < sr_info['sr_ymin']) or \
                                (obj.ys > sr_info['sr_ymax'] and obj.ye < sr_info['sr_ymin']):
                            clip_rout_xmax = obj.xe
                            clip_rout_size.append(obj.symbol)
                    elif obj.xe < sr_info['sr_xmin']:
                        if (obj.ye > sr_info['sr_ymax'] and obj.ys < sr_info['sr_ymin']) or \
                                (obj.ys > sr_info['sr_ymax'] and obj.ye < sr_info['sr_ymin']):
                            clip_rout_xmin = obj.xe
                            clip_rout_size.append(obj.symbol)
                elif obj.ye == obj.ys:
                    if obj.ye > sr_info['sr_ymax']:
                        if (obj.xe > sr_info['sr_xmax'] and obj.xs < sr_info['sr_xmin']) or \
                                (obj.xs > sr_info['sr_xmax'] and obj.xe < sr_info['sr_xmin']):
                            clip_rout_ymax = obj.ye
                            clip_rout_size.append(obj.symbol)
                    elif obj.ye < sr_info['sr_ymin']:
                        if (obj.xe > sr_info['sr_xmax'] and obj.xs < sr_info['sr_xmin']) or \
                                (obj.xs > sr_info['sr_xmax'] and obj.xe < sr_info['sr_xmin']):
                            clip_rout_ymin = obj.ye
                            clip_rout_size.append(obj.symbol)

            if len(clip_rout_size) != 4:
                log = u"锣边带{0}边距获取异常，请检查资料或联系程序工程师".format(pnl_rout_name)
                arraylist.append(log)
                continue
            else:
                half_size = float(clip_rout_size[0][1:]) / 2000
                clip_rout_xmax -= half_size
                clip_rout_xmin += half_size
                clip_rout_ymax -= half_size
                clip_rout_ymin += half_size

            back_layer = 'surfacedu_clip'
            step.removeLayer(back_layer)
            step.createLayer(back_layer)
            for layer in check_layers:
                step.clearAll()
                step.resetFilter()
                step.affect(back_layer)
                step.selectDelete()
                step.clearAll()
                step.affect(layer)
                step.COM("set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=no,attribute=.pattern_fill")
                step.filter_set(feat_types="surface", polarity='positive')
                step.selectAll()

                if not step.featureSelected():
                    log = u"{0}层未获取到铺铜区域，请检查surface是否含有属性.pattern_fill".format(layer)
                    arraylist.append(log)
                    continue
                step.copyToLayer(back_layer)
                # 负性surface也copy过去
                step.resetFilter()
                step.filter_set(feat_types="surface", polarity='negative')
                step.selectAll()
                if step.featureSelected():
                    step.copyToLayer(back_layer)
                step.clearAll()
                step.resetFilter()
                step.affect(back_layer)
                step.contourize(units='mm')
                # 确定电金夹头位置

                step.COM("sel_resize,size=2000,corner_ctl=no")
                step.COM("sel_resize,size=-2000,corner_ctl=no")
                step.COM("sel_resize,size=-3000,corner_ctl=no")
                step.COM("sel_resize,size=3000,corner_ctl=no")

                for zb in [(sr_info['sr_xmax'], sr_info['sr_ymax'], pf_xmax + 20, pf_ymax + 20),
                           (sr_info['sr_xmax'], sr_info['sr_ymin'], pf_xmax + 20, pf_ymin - 20),
                           (sr_info['sr_xmin'], sr_info['sr_ymax'], pf_xmin - 20, pf_ymax + 20),
                           (sr_info['sr_xmin'], sr_info['sr_ymin'], pf_xmin - 20, pf_ymin - 20)]:
                    step.COM("clip_area_strt")
                    step.COM("clip_area_xy,x=%s,y=%s" % (zb[0], zb[1]))
                    step.COM("clip_area_xy,x=%s,y=%s" % (zb[2], zb[3]))
                    step.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=inside,contour_cut=no,margin=0,feat_types=line\;pad\;surface\;arc\;text")

                step.clearAll()
                for eg_fx in ['l', 'r', 't', 'b']:
                    if eg_fx == 'l':
                        x1, y1 = pf_xmin, pf_ymax
                        x2, y2 = sr_info['sr_xmin'], pf_ymin
                    elif eg_fx == 'r':
                        x1, y1 = sr_info['sr_xmax'], pf_ymax
                        x2, y2 = pf_xmax, pf_ymin
                    elif eg_fx == 't':
                        x1, y1 = pf_xmin, pf_ymax
                        x2, y2 = pf_xmax, sr_info['sr_ymax']
                    else:
                        x1, y1 = pf_xmin, sr_info['sr_ymin']
                        x2, y2 = pf_xmax, pf_ymin
                    # 每个方位重新COPY铜皮位
                    back_layer_reg = back_layer + '_reg'
                    step.copyLayer(job=jobname, step=step.name, lay=back_layer, dest_lay=back_layer_reg)
                    step.affect(back_layer_reg)
                    step.COM("clip_area_strt")
                    step.COM("clip_area_xy,x=%s,y=%s" % (x1, y1))
                    step.COM("clip_area_xy,x=%s,y=%s" % (x2, y2))
                    step.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,contour_cut=no,margin=0,feat_types=line\;pad\;surface\;arc\;text")
                    # 将铜皮层和开窗层合并
                    step.clearAll()
                    step.affect(back_layer_reg)
                    step.COM("clip_area_strt")
                    step.COM("clip_area_xy,x=%s,y=%s" % (clip_rout_xmin, clip_rout_ymax))
                    step.COM("clip_area_xy,x=%s,y=%s" % (clip_rout_xmax, clip_rout_ymin))
                    step.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,contour_cut=no,margin=0,feat_types=line\;pad\;surface\;arc\;text")
                    step.affect(back_layer_reg)
                    # g切除后可能为空，跳过
                    step.selectAll()
                    if not step.featureSelected():
                        step.removeLayer(back_layer_reg)
                        continue

                    if 'ynh' in jobname:
                        step.PAUSE("12")
                    info_limits = step.DO_INFO(
                        "-t layer -e %s/panel/%s -d LIMITS , units=mm" % (jobname, back_layer_reg))
                    cent_x = float(info_limits['gLIMITSxmin']) + (
                            float(info_limits['gLIMITSxmax']) - float(info_limits['gLIMITSxmin'])) / 2
                    cent_y = float(info_limits['gLIMITSymin']) + (
                            float(info_limits['gLIMITSymax']) - float(info_limits['gLIMITSymin'])) / 2
                    allsymbols = []
                    allsymbols.append((cent_x, cent_y, "surface"))
                    if eg_fx in ['l', 'r']:
                        wide_surface = float(info_limits['gLIMITSxmax']) - float(info_limits['gLIMITSxmin'])
                    else:
                        wide_surface = float(info_limits['gLIMITSymax']) - float(info_limits['gLIMITSymin'])

                    if wide_surface < 7.9 or wide_surface > 10.1:
                        log = u"{0}层电金夹头锣边后铜皮区域不在8-10MM范围内，请检查".format(layer)
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                             [layer,  pnl_rout_name], log,
                                                                             dic_zu_layer, add_note_layer=layer,
                                                                             allsymbol_xy = allsymbols)
                    step.removeLayer(back_layer_reg)
            step.removeLayer(back_layer)
            if arraylist:
                return arraylist, dic_zu_layer

        return "success", None


    def check_goldfilm_open_area(self):
        """
        电金夹头位留露铜检测/镀孔菲林留铜检测/外层正片留铜检测
        http://192.168.2.120:82/zentao/story-view-8573.html
         增加检测，将PNL板边线路和阻焊开窗以最后一次锣边切掉，计算线路和阻焊开窗露铜，镀金干膜层gold-c/gold-s开窗露铜以最后一次锣边到板内计算8-10mm
        增加检测, 有图形镀孔菲林层 如 l1.dk,以最后一次锣边到板内计算镀孔层露铜到8-10mm
        增加检测, 外层正片，以最后一次锣边到板内计算镀孔层露铜到8-10mm
        沉金流程的不检测
        """
        arraylist = []
        dic_zu_layer = {}
        if "panel" not in matrixinfo["gCOLstep_name"]:
            return "success", None
        step = gClasses.Step(job, 'panel')
        check_layers_top, check_layers_bot = [], []
        for lay in step.getLayers():
            if lay in ['gold-c', 'l1-dk']:
                check_layers_top.append(lay)
            elif lay in ['gold-s', 'l{0}-dk'.format(int(jobname[4:6]))]:
                check_layers_bot.append(lay)

        # 获取外层是否正片蚀刻
        get_plat = get_plating_type(jobname.upper())
        if not get_plat:
            return "success", None
        max_process_num = max([i['PROCESS_NUM_'] for i in get_plat])
        for d in get_plat:
            if d['PROCESS_NUM_'] == max_process_num:
                if d['PLATING_TYPE_'] == 2:
                    film_layers = str(d['LAYER_NAME']).lower().split(',')
                    if film_layers:
                        for lay in film_layers:
                            if step.isLayer(lay):
                                if lay == 'l1':
                                    check_layers_top.append(lay)
                                elif  lay == 'l{0}'.format(int(jobname[4:6])):
                                    check_layers_bot.append(lay)

        if not check_layers_top and not check_layers_bot:
            return "success", None
        # 取得最后一次锣边带名称
        last_rout = 'pnl_rout{0}'.format(max_process_num -1)
        if last_rout == 'pnl_rout_0':
            last_rout = 'pnl_rout'

        if not step.isLayer(last_rout):
            log = u"CAM资料没有发现最后一次锣边带，请检查命名是否为：{0}".format(last_rout)
            arraylist.append(log)
            return arraylist, dic_zu_layer
        open_smlayer = {}
        if step.isLayer('m1'):
            open_smlayer['top'] = 'm1'
        elif step.isLayer('m1-1'):
            open_smlayer['top'] = 'm1-1'
        if step.isLayer('m2'):
            open_smlayer['bot'] = 'm2'
        elif step.isLayer('m2-1'):
            open_smlayer['bot'] = 'm2-1'

        step.open()
        step.COM("units,type=mm")
        pf = step.getProfile()
        pf_xmin = pf.xmin * 25.4
        pf_xmax = pf.xmax * 25.4
        pf_ymin = pf.ymin * 25.4
        pf_ymax = pf.ymax * 25.4
        # 获取sr区域
        sr_info = {}
        for info_layer in outsignalLayers+ innersignalLayers:
            # 用角线来确定sr区域角线有两类 sh-con,sh-con2
            info = step.INFO("-t layer -e %s/%s/%s  -d FEATURES, units=mm" % (jobname, step.name, info_layer))
            lines = [gFeatures.Pad(line) for line in info if 'sh-con2' in line or 'sh-con' in line]
            if lines:
                feax = [fea.x  for fea in lines]
                feay = [fea.y  for fea in lines]
                # sr_xmin, sr_ymin, sr_xmax, sr_ymax = min(feax) + 1, min(feay) + 1, max(feax) - 1, max(feay) - 1
                sr_info = {'sr_xmin' : min(feax) + 1,
                           'sr_ymin' : min(feay) + 1,
                           'sr_xmax' : max(feax) - 1,
                           'sr_ymax' : max(feay) - 1,
                           }
                break

        step.clearAll()
        step.resetFilter()
        # 锣带转化为线条
        compen_rout = last_rout + 'compensate_line'
        step.affect(last_rout)
        step.COM("compensate_layer,source_layer=%s,dest_layer=%s,dest_layer_type=document" % (last_rout, compen_rout))
        step.clearAll()
        step.affect(compen_rout)
        step.filter_set(feat_types="pad;arc")
        step.selectAll()
        if step.featureSelected():
            step.selectDelete()
        step.resetFilter()
        lay_cmd = gClasses.Layer(step, compen_rout)
        featues_lines = lay_cmd.featCurrent_LayerOut(units='mm')['lines']
        clip_rout_xmin, clip_rout_xmax, clip_rout_ymin, clip_rout_ymax = '', '', '', ''
        clip_rout_size = []
        for obj in featues_lines:
            if obj.xe == obj.xs:
                if obj.xe > sr_info['sr_xmax']:
                    if (obj.ye > sr_info['sr_ymax'] and obj.ys < sr_info['sr_ymin']) or\
                            (obj.ys > sr_info['sr_ymax'] and obj.ye < sr_info['sr_ymin']):
                        clip_rout_xmax = obj.xe
                        clip_rout_size.append(obj.symbol)
                elif obj.xe < sr_info['sr_xmin']:
                    if (obj.ye > sr_info['sr_ymax'] and obj.ys < sr_info['sr_ymin']) or\
                            (obj.ys > sr_info['sr_ymax'] and obj.ye < sr_info['sr_ymin']):
                        clip_rout_xmin = obj.xe
                        clip_rout_size.append(obj.symbol)
            elif obj.ye == obj.ys:
                if obj.ye > sr_info['sr_ymax']:
                    if (obj.xe > sr_info['sr_xmax'] and obj.xs < sr_info['sr_xmin']) or\
                            (obj.xs > sr_info['sr_xmax'] and obj.xe < sr_info['sr_xmin']):
                        clip_rout_ymax = obj.ye
                        clip_rout_size.append(obj.symbol)
                elif obj.ye < sr_info['sr_ymin']:
                    if (obj.xe > sr_info['sr_xmax'] and obj.xs < sr_info['sr_xmin']) or\
                            (obj.xs > sr_info['sr_xmax'] and obj.xe < sr_info['sr_xmin']):
                        clip_rout_ymin = obj.ye
                        clip_rout_size.append(obj.symbol)

        if len(clip_rout_size) != 4:
            log = u"最后一次锣边带{0}边距获取异常，请检查或联系程序工程师".format(last_rout)
            arraylist.append(log)
            return arraylist, dic_zu_layer
        else:
            half_size = float(clip_rout_size[0][1:]) / 2000
            clip_rout_xmax -= half_size
            clip_rout_xmin += half_size
            clip_rout_ymax -= half_size
            clip_rout_ymin += half_size

        top_sm_surface, bot_sm_surface = '', ''
        if open_smlayer.has_key('top'):
            top_sm_surface = open_smlayer['top'] + '_clip_surface'
            step.removeLayer(top_sm_surface)
            step.createLayer(top_sm_surface)
        if open_smlayer.has_key('bot'):
            bot_sm_surface = open_smlayer['bot'] + '_clip_surface'
            step.removeLayer(bot_sm_surface)
            step.createLayer(bot_sm_surface)

        for zu_lay in [(check_layers_top, top_sm_surface), (check_layers_bot, bot_sm_surface)]:
            check_lay, layer_surface = zu_lay[0], zu_lay[1]
            if not check_lay : continue
            if not layer_surface:
                if check_lay == check_layers_top:
                    log = u"top面没有发现开窗层，请检查资料命名是否正确"
                else:
                    log = u"bot面没有发现开窗层，请检查资料命名是否正确"
                arraylist.append(log)
            else:
                step.clearAll()
                step.resetFilter()
                if layer_surface == top_sm_surface:
                    org_sm = open_smlayer['top']
                else:
                    org_sm = open_smlayer['bot']
                step.affect(org_sm)
                step.COM("set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=no,attribute=.pattern_fill")
                step.filter_set(feat_types="surface")
                step.selectAll()
                sel_num = step.featureSelected()
                if not sel_num:
                    if layer_surface == top_sm_surface:
                        log = u"top面开窗层未取出开窗surface，请检查资料是否正确"
                    else:
                        log = u"bot面开窗层未取出开窗surface，请检查资料是否正确"
                    arraylist.append(log)
                    continue
                step.copyToLayer(layer_surface)
                step.clearAll()
                step.resetFilter()
                step.affect(layer_surface)
                step.selectAll()
                lay_cmd = gClasses.Layer(step, layer_surface)
                sel_indexs = lay_cmd.featSelIndex()
                sel_num = step.featureSelected()

                if sel_num <> 1:
                    index_choose = None
                    for id in sel_indexs:
                        step.selectNone()
                        step.selectFeatureIndex(layer_surface, index= id)
                        info_limits = step.DO_INFO("-t layer -e %s/panel/%s  -d LIMITS  -o select, units=mm" % (jobname, layer_surface))
                        x_rect = float(info_limits['gLIMITSxmax']) - float(info_limits['gLIMITSxmin'])
                        y_rect = float(info_limits['gLIMITSymax']) - float(info_limits['gLIMITSymin'])
                        if x_rect > pf.xsize and y_rect > pf.ysize:
                            index_choose = id
                            break
                    if not index_choose:
                        if layer_surface == top_sm_surface:
                            log = u"top面开窗层未取出开窗区域，请检查surface是否含有属性.pattern_fill"
                        else:
                            log = u"bot面开窗层未取出开窗区域，请检查surface是否含有属性.pattern_fill"
                        arraylist.append(log)
                        continue
                    else:
                        step.selectNone()
                        step.selectFeatureIndex(layer_surface, index=index_choose)
                        step.COM("sel_reverse")
                        if step.featureSelected():
                            step.selectDelete()

                step.clearAll()
                step.resetFilter()
                # 把阻焊负的资料也copy进去
                step.affect(org_sm)
                step.filter_set(feat_types="surface", polarity='negative')
                step.selectAll()
                if step.featureSelected():
                    step.copyToLayer(layer_surface)
                step.clearAll()
                step.resetFilter()
                step.affect(layer_surface)
                step.contourize(units='mm')
                step.COM("sel_resize,size=2000,corner_ctl=no")
                step.COM("sel_resize,size=-2000,corner_ctl=no")
                step.COM("clip_area_strt")
                step.COM("clip_area_xy,x=%s,y=%s" % (clip_rout_xmin, clip_rout_ymax))
                step.COM("clip_area_xy,x=%s,y=%s" % (clip_rout_xmax, clip_rout_ymin))
                step.COM(
                    "clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,contour_cut=no,margin=0,feat_types=line\;pad\;surface\;arc\;text")
                step.clearAll()

                back_layer = 'surfacedu_clip'
                step.removeLayer(back_layer)
                step.createLayer(back_layer)
                # check_lay = ['l1']
                for layer in check_lay:
                    step.clearAll()
                    step.resetFilter()
                    step.affect(back_layer)
                    step.selectDelete()
                    step.clearAll()
                    step.affect(layer)
                    if layer not in ['gold-c', 'gold-s']:
                        step.COM("set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=no,attribute=.pattern_fill")
                    step.filter_set(feat_types="surface")
                    step.selectAll()

                    if not step.featureSelected():
                        log = u"{0}层未获取到铺铜区域，请检查surface是否含有属性.pattern_fill".format(layer)
                        arraylist.append(log)
                        continue
                    step.copyToLayer(back_layer)
                    step.clearAll()
                    step.affect(back_layer)
                    # 确定电金夹头位置，获取哪一边超出板外

                    step.COM("sel_resize,size=2000,corner_ctl=no")
                    step.COM("sel_resize,size=-2000,corner_ctl=no")

                    for zb in [(sr_info['sr_xmax'], sr_info['sr_ymax'], pf_xmax + 20, pf_ymax + 20),
                               (sr_info['sr_xmax'], sr_info['sr_ymin'], pf_xmax + 20, pf_ymin - 20),
                               (sr_info['sr_xmin'], sr_info['sr_ymax'], pf_xmin - 20, pf_ymax + 20),
                               (sr_info['sr_xmin'], sr_info['sr_ymin'], pf_xmin - 20, pf_ymin - 20)]:
                        step.COM("clip_area_strt")
                        step.COM("clip_area_xy,x=%s,y=%s" % (zb[0], zb[1]))
                        step.COM("clip_area_xy,x=%s,y=%s" % (zb[2], zb[3]))
                        step.COM( "clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=inside,contour_cut=no,margin=0,feat_types=line\;pad\;surface\;arc\;text")

                    step.clearAll()
                    for eg_fx in ['l', 'r', 't', 'b']:
                        if eg_fx == 'l':
                            x1, y1 = pf_xmin, pf_ymax
                            x2, y2 = sr_info['sr_xmin'], pf_ymin
                        elif eg_fx == 'r':
                            x1, y1 = sr_info['sr_xmax'], pf_ymax
                            x2, y2 = pf_xmax, pf_ymin
                        elif eg_fx == 't':
                            x1, y1 = pf_xmin, pf_ymax
                            x2, y2 = pf_xmax, sr_info['sr_ymax']
                        else:
                            x1, y1 = pf_xmin, sr_info['sr_ymin']
                            x2, y2 = pf_xmax, pf_ymin
                        # 每个方位重新COPY铜皮位
                        back_layer_reg = back_layer  + '_reg'
                        step.copyLayer(job=jobname, step=step.name, lay=back_layer, dest_lay=back_layer_reg)
                        step.affect(back_layer_reg)
                        step.COM("clip_area_strt")
                        step.COM("clip_area_xy,x=%s,y=%s" % (x1, y1))
                        step.COM("clip_area_xy,x=%s,y=%s" % (x2, y2))
                        step.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,contour_cut=no,margin=0,feat_types=line\;pad\;surface\;arc\;text")

                        # 将铜皮层和开窗层合并
                        step.clearAll()
                        step.affect(back_layer_reg)
                        step.COM("clip_area_strt")
                        step.COM("clip_area_xy,x=%s,y=%s" % (clip_rout_xmin, clip_rout_ymax))
                        step.COM("clip_area_xy,x=%s,y=%s" % (clip_rout_xmax, clip_rout_ymin))
                        step.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,contour_cut=no,margin=0,feat_types=line\;pad\;surface\;arc\;text")

                        step.clearAll()
                        surface_layer_other = layer_surface + '_other'
                        back_layer_reg1 = back_layer_reg + '_1'
                        step.removeLayer(surface_layer_other)
                        step.removeLayer(back_layer_reg1)
                        # layer_surface阻焊开窗层
                        step.copyLayer(job=jobname, step=step.name, lay=layer_surface, dest_lay=surface_layer_other)
                        step.copyLayer(job=jobname, step=step.name, lay=back_layer_reg, dest_lay=back_layer_reg1)
                        step.affect(back_layer_reg)
                        # gold切除后可能为空，跳过
                        step.selectAll()
                        if not step.featureSelected():
                            step.removeLayer(back_layer_reg)
                            step.removeLayer(surface_layer_other)
                            continue
                        # 第一步拿开窗套铜皮
                        step.clearAll()
                        step.affect(surface_layer_other)
                        step.copyToLayer(back_layer_reg1, invert='yes')
                        step.clearAll()
                        # if 'ynh' in jobname:
                        #     step.PAUSE("11")
                        step.affect(back_layer_reg1)
                        step.contourize(units='mm')
                        step.filter_set(polarity='positive')
                        step.selectAll()
                        if step.featureSelected():
                        #     if 'ynh' in jobname:
                        #         step.PAUSE("11")
                            step.copyToLayer(back_layer_reg, invert='yes')
                            step.clearAll()
                        step.resetFilter()
                        step.clearAll()
                        step.affect(back_layer_reg)
                        step.contourize(units='mm')
                        # if 'ynh' in jobname:
                        #     step.PAUSE("12")
                        info_limits = step.DO_INFO(
                            "-t layer -e %s/panel/%s -d LIMITS , units=mm" % (jobname, back_layer_reg))
                        cent_x = float(info_limits['gLIMITSxmin']) + (
                                    float(info_limits['gLIMITSxmax']) - float(info_limits['gLIMITSxmin'])) / 2
                        cent_y = float(info_limits['gLIMITSymin']) + (
                                    float(info_limits['gLIMITSymax']) - float(info_limits['gLIMITSymin'])) / 2
                        allsymbols = []
                        allsymbols.append((cent_x, cent_y, "surface"))
                        if eg_fx in ['l', 'r']:
                            wide_surface = float(info_limits['gLIMITSxmax']) - float(info_limits['gLIMITSxmin'])
                        else:
                            wide_surface = float(info_limits['gLIMITSymax']) - float(info_limits['gLIMITSymin'])


                        if wide_surface < 7.9 or wide_surface > 10.1:
                            log = u"{0}层电金夹头最后一次锣边后开窗区域不在8-10MM范围内，请检查".format(layer)
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                                 [layer, org_sm, last_rout], log,
                                                                                 dic_zu_layer, add_note_layer=layer,
                                                                                 allsymbol_xy=allsymbols)
                        step.removeLayer(surface_layer_other)
                        step.removeLayer(back_layer_reg)
                        step.removeLayer(back_layer_reg1)
                step.removeLayer(back_layer)
        step.clearAll()
        step.resetFilter()
        step.removeLayer(top_sm_surface)
        step.removeLayer(bot_sm_surface)
        step.removeLayer(compen_rout)

        if arraylist:
            return arraylist, dic_zu_layer
        return "success", None

    def check_not_ring_outer(self):
        """
        检测对应的外层PTH孔是否有PAD--outer
        """
        arraylist = []
        dic_zu_layer = {}

        # 只检测到edit和set
        check_steps = [s for s in matrixinfo["gCOLstep_name"] if s in ['edit', 'set']]
        if not check_steps:
            return "success", None

        #获取需要检测的孔层
        check_drl_layers = []
        for i, lay in enumerate(matrixInfo["gROWname"]):
            if matrixInfo["gROWcontext"][i] == "board" and matrixInfo["gROWlayer_type"][i] == "drill":
                if lay in ['drl', '2nd', '3nd']:
                    check_drl_layers.append(lay)
                elif re.match("^s\d{1,2}-\d{1,2}$", lay):
                    num1, num2 = lay[1:].split('-')
                    if int(num1) in [1, int(jobname[4:6])]:
                        check_drl_layers.append(lay)

        for step_name in check_steps:
            step = gClasses.Step(job, step_name)
            step.open()
            step.resetFilter()
            step.clearAll()
            step.COM("units,type=inch")
            for lay in outsignalLayers:
                tmp_layer = lay + '_pad_rcheck_'
                # step.removeLayer(tmp_layer)
                step.copyLayer(job.name, step_name, lay, tmp_layer)
                step.affect(tmp_layer)
            step.contourize(units='inch')
            step.clearAll()
            for drl_layer in check_drl_layers:
                tmp_drllayer = drl_layer + '_tmp_noring_'
                step.copyLayer(jobname, step_name, drl_layer, tmp_drllayer)
                if drl_layer not in laser_drill_layers:
                    step.resetFilter()
                    step.clearAll()
                    step.affect(drl_layer)
                    for attr in ['via', 'non_plated', 'plated']:
                        step.resetFilter()
                        step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.drill,option={0}".format(attr))
                        step.selectAll()
                    step.resetFilter()
                    step.COM("sel_reverse")
                    if step.featureSelected():
                        log = '{0}层钻带部分钻孔未定义属性'.format(drl_layer)
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step_name, step, drl_layer, drl_layer,log,
                                                                             dic_zu_layer, add_note_layer=drl_layer)
                    # 检测定义了属性的钻孔
                    step.clearAll()
                    step.affect(tmp_drllayer)
                    step.resetFilter()
                    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.drill,option=via")
                    step.selectAll()
                    step.resetFilter()
                    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.drill,option=plated")
                    step.selectAll()
                    if step.featureSelected():
                        step.COM("sel_reverse")
                        if step.featureSelected():
                            step.selectDelete()
                    step.resetFilter()
                    check_signals = outsignalLayers
                else:
                    num1, num2 = str(drl_layer[1:]).split('-')
                    check_signals = ['l{0}'.format(num1)]

                step.resetFilter()
                for lay in check_signals:
                    tmp_layer = lay + '_pad_rcheck_'
                    tmp_nopad = lay + '_no_pad_'
                    step.removeLayer(tmp_nopad)
                    step.clearAll()
                    step.affect(tmp_drllayer)
                    step.refSelectFilter(tmp_layer, polarity='positive', mode='cover')
                    step.COM("sel_reverse")
                    if step.featureSelected():
                        step.copyToLayer(tmp_nopad)
                        step.clearAll()
                        step.resetFilter()
                        step.affect(drl_layer)
                        step.refSelectFilter(tmp_nopad, mode='cover')
                        if step.featureSelected():
                            log = '{0}钻孔对应{1}层少PAD'.format(drl_layer, lay)
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step_name, step, drl_layer, lay,
                                                                            log,dic_zu_layer, add_note_layer=drl_layer)
                    step.removeLayer(tmp_nopad)
                step.removeLayer(tmp_drllayer)
            # 删除备份层
            for lay in outsignalLayers:
                tmp_layer = lay + '_pad_rcheck_'
                step.removeLayer(tmp_layer)

            if arraylist:
                return arraylist, dic_zu_layer
            else:
                return "success", None

    def check_by_bar_design(self):
        """检测备用靶间距是否足够20-110MM"""
        arraylist = []
        dic_zu_layer = {}
        if not 'panel' in matrixinfo["gCOLstep_name"]:
            return "success", None
        step = gClasses.Step(job, 'panel')
        step.open()
        step.clearAll()
        step.resetFilter()
        pf = step.getProfile()
        pf_xcent = pf.xcenter * 25.4
        pf_ycent = pf.ycenter * 25.4
        pf_xsize = pf.xsize * 25.4
        pf_ysize = pf.ysize * 25.4

        # 获取sr的坐标
        sr_info = self.get_sr_limits()

        dict_info = {}
        for layer in innersignalLayers:
            step.clearAll()
            step.affect(layer)
            step.resetFilter()
            step.filter_set(include_syms='hdi1-by*', feat_types='pad', polarity='positive')
            step.COM("reset_filter_criteria,filter_name=popup,criteria=exc_attr")
            step.COM("set_filter_attributes,filter_name=popup,exclude_attributes = yes,condition=yes,attribute=.string,min_int_val=0,"
                 "max_int_val=0,min_float_val=0,max_float_val=0,option=,text = yh_py_pad")
            step.selectAll()
            if step.featureSelected():
                lay_cmd = gClasses.Layer(step, layer)
                features = lay_cmd.featout_dic_Index(options='feat_index+select', units='mm')['pads']
                dict_info[layer] = features
            step.resetFilter()
            step.clearAll()

        inplan = InPlan(jobname)
        mrp_info = inplan.get_inplan_mrp_info()
        if dict_info:
            fea_top = []
            for objs in dict_info.values():
                for obj in objs:
                    if obj.x < pf_xcent and obj.y > pf_ycent:
                        fea_top.append(obj)
            feaxs = [obj.x for obj in fea_top]
            feays = [obj.y for obj in fea_top]
            if abs((abs(feaxs[0] - feaxs[1])) - abs(abs(feays[0] - feays[1]))) > 1 :
                if abs(feaxs[0] - feaxs[1]) < abs(feays[0] - feays[1]):
                    wd = 'y'
                else:
                    wd = 'x'

            else:

                if feays[0] < sr_info['sr_ymax'] and feaxs[0] <  sr_info['sr_xmin']:
                    wd = 'y'
                else:
                    wd = 'x'

            for layer, objs in dict_info.items():
                for mrp in mrp_info:
                    pnlrout_x = mrp['PNLROUTX'] * 25.4
                    pnlrout_y = mrp['PNLROUTY'] * 25.4
                    num = mrp['PROCESS_NUM'] - 1
                    pnl_rout_layer = 'pnl_rout{0}'.format(num)

                    fromLay = mrp['FROMLAY'].lower()
                    toLay =mrp['TOLAY'].lower()
                    if fromLay and toLay:
                        start_num = int(fromLay[1:])
                        end_num = int(toLay[1:])
                        fromLay_next ='l{0}'.format(start_num +1)
                        to_next = 'l{0}'.format(end_num - 1)
                        if layer in [fromLay_next, to_next]:
                            if wd == 'x':
                                cut_x =(pf_xsize - pnlrout_x) / 2
                                for obj in objs:
                                    if obj.x < pf_xcent :
                                        x_space = obj.x - pf.xmin * 25.4 - cut_x
                                    else:
                                        x_space = pf.xmax * 25.4 - cut_x - obj.x
                                    if  x_space < 20 or x_space > 110:
                                        step.clearAll()
                                        step.resetFilter()
                                        step.affect(layer)
                                        step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(layer, obj.feat_index))
                                        if step.featureSelected():
                                            log = u"{0}层备用靶距离Y锣边{1}mm，不在20-110MM范围".format(layer, x_space)
                                            arraylist.append(log)
                                            show_layers = [layer]
                                            if step.isLayer(pnl_rout_layer):
                                                show_layers = [pnl_rout_layer, layer]
                                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer, show_layers, log, dic_zu_layer,add_note_layer=layer)

                            else:
                                cut_y = (pf_ysize - pnlrout_y) / 2
                                for obj in objs:
                                    if obj.y < pf_ycent:
                                        y_space = obj.y - pf.ymin * 25.4 - cut_y
                                    else:
                                        y_space = pf.ymax * 25.4 - cut_y - obj.y

                                    if y_space < 20 or y_space > 110:
                                        step.clearAll()
                                        step.resetFilter()
                                        step.affect(layer)
                                        step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(layer, obj.feat_index))
                                        if step.featureSelected():
                                            show_layers = [layer]
                                            if step.isLayer(pnl_rout_layer):
                                                show_layers = [pnl_rout_layer, layer]
                                            log = u"{0}层备用靶距离X锣边{1}mm，不在20-110MM范围".format(layer, y_space)
                                            arraylist.append(log)
                                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer, show_layers,log, dic_zu_layer,add_note_layer=layer)
        step.clearAll()
        step.resetFilter()
        if arraylist:
            return arraylist, dic_zu_layer
        return "success", None



    def check_mi_cam_toollist(self):
        """
        检测CAM和MI工具是否一致
        """
        # 查看MI料号的制作时间
        mysql = MySql()
        pd_data = mysql.get_job_production_data(jobname)
        if pd_data:
            try:
                mi_time = pd_data[-1]['mi_time']
                start_time = datetime.strptime('2025-4-20 12:00:00', "%Y-%m-%d %H:%M:%S")
                mi_start_time = datetime.strptime(mi_time, "%Y-%m-%d %H:%M:%S")
                if mi_start_time < start_time:
                    update_current_job_check_log(os.environ.get("CHECK_ID", "NULL"),u"forbid_or_information='{0}'".format(u"提示"))
                    return u"success:旧单不纳入检测", None
            except:
                return "success", None

        res = os.environ.get("INNER_OUTER", "")
        if res == 'outer':
            send_type = 'auto_check_outer'
        else:
            send_type = 'auto_check_inner'
        os.system("python /incam/server/site_data/scripts/ynh/toolName_compare/compare_tool_names_new.py {0}".format(send_type))
        error_log = "/tmp/check_toolName_micam_{0}.log".format(job.name)
        # success_log = "/tmp/check_flj_success_{0}.log".format(job.name)
        if os.path.exists(error_log):
            lines = file(error_log).readlines()
            os.unlink(error_log)
            return [line.strip() for line in lines], None
        return "success", None


    def check_not_ring_signal(self):
        """
        检测盲埋孔是否有孔环--inner
        """
        arraylist = []
        dic_zu_layer = {}
        stepname = 'edit'
        if not stepname in matrixinfo["gCOLstep_name"]:
            return "success", None
        step = gClasses.Step(job, stepname)
        step.open()
        step.resetFilter()
        step.clearAll()
        step.COM("units,type=inch")

        cleck_layers = laser_drill_layers + mai_drill_layers + mai_man_drill_layers
        # 获取检查哪些线路层
        check_signal = []
        for drl_layer in cleck_layers:
            num1, num2 = str(drl_layer[1:]).split('-')
            lay1, lay2 = 'l{0}'.format(num1), 'l{0}'.format(num2)
            if lay1 not in check_signal:
                check_signal.append(lay1)
            if lay2 not in check_signal:
                check_signal.append(lay2)

        # 一次性备份线路层
        for lay in check_signal:
            tmp_layer = lay + '_pad_rcheck_'
            step.removeLayer(tmp_layer)
            step.copyLayer(job.name,stepname, lay, tmp_layer)
            step.affect(tmp_layer)
        step.contourize(units='inch')
        step.clearAll()

        for drl_layer in cleck_layers:
            num1, num2 = str(drl_layer[1:]).split('-')
            lay1, lay2 = 'l{0}'.format(num1), 'l{0}'.format(num2)
            for lay in [lay1, lay2]:
                tmp_lay = lay + '_pad_rcheck_'
                tmp_nopad = lay + '_no_pad_'
                step.clearAll()
                step.affect(drl_layer)
                step.refSelectFilter(tmp_lay, polarity='positive', mode='cover')
                step.COM("sel_reverse")
                if step.featureSelected():
                    step.copyToLayer(tmp_nopad)
                    step.clearAll()
                    step.resetFilter()
                    step.affect(drl_layer)
                    step.refSelectFilter(tmp_nopad, mode='cover')
                    if step.featureSelected():
                        log = '{0}钻孔对应{1}层少PAD'.format(drl_layer, lay)
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepname, step, drl_layer, lay,
                                                                             log,dic_zu_layer, add_note_layer=drl_layer)
                step.removeLayer(tmp_nopad)
        step.clearAll()
        # 删除备份的线路层
        for lay in check_signal:
            tmp_layer = lay + '_pad_rcheck_'
            step.removeLayer(tmp_layer)

        if arraylist:
            return arraylist, dic_zu_layer
        else:
            return "success", None

    def check_183_desiger_test(self):
        """
        183客户指定检测项目
        1. 检测工艺边是否添加客户料号名, 检查是否添加在完整铜面上
        2. 选化板检测MIC孔开窗，光学点是否按化金制作
        3. 检测是否添加泪滴
        4. 检测是否定义光学点属性
        5. 检测是否漏加coupon  防焊偏位，锣板偏位，防焊爆偏，防漏接
        6. 检测批次号前面是否加'-' 周期-批次号
        """
        if jobname[1:4] != '183':
            return "success", None
        arraylist = []
        dic_zu_layer = {}
        try:
            res = os.environ.get("INNER_OUTER", "inner")
        except:
            res = 'outer'
        # 检测是否运行过检测铜面PAD
        if res != 'inner':
            # get_status = get_topcam_status(1810, jobname)
            # if not get_status:
            #     log = u'检测到未运行8.13是否检测铜面开窗是否一致！'
            #     arraylist.append(log)
            #检测是否添加各类测试coupon
            if 'set' in job.getSteps().keys():
                inser_steps = get_panelset_sr_step(jobname, 'set')
                floujies = [s for s in inser_steps if 'floujie' in s]
                if laser_drill_layers and not floujies:
                    log = u'检测到SET边未添加防漏接测试coupon！'
                    arraylist.append(log)
                if 'sm4-coupon' not in ';'.join(inser_steps):
                    log = u'检测到SET边未添加防爆偏(sm4-coupon)！'
                    arraylist.append(log)
                set_cmd = gClasses.Step(job,'set')
                for sm in ['m1', 'm2']:
                    if set_cmd.isLayer(sm):
                        infolines = set_cmd.INFO("-t layer -e %s/set/%s -d FEATURES" % (jobname, sm))
                        if not '3mil' in ''.join(infolines) or not '7mil' in ''.join(infolines):
                            log = u'检测到SET边{0}层未添加防切偏coupon！'.format(sm)
                            arraylist.append(log)
                #锣板偏位检测
                sr_set = get_sr_area_for_step_include('set',include_sr_step=['edit'])
                sr_xmin = min([li[0] for li in sr_set])
                sr_ymin = min([li[1] for li in sr_set])
                sr_xmax = max([li[2] for li in sr_set])
                sr_ymax = max([li[3] for li in sr_set])
                pf_xmin, pf_ymin, pf_xmax, pf_ymax = get_profile_limits(set_cmd)
                # 确定方位
                add_fw = {}
                if sr_xmin - pf_xmin > 2:
                    add_fw['l'] = '左工艺边'
                if pf_xmax - sr_xmax > 2:
                    add_fw['r'] = '右工艺边'
                if sr_ymin - pf_ymin > 2:
                    add_fw['d'] = '下工艺边'
                if pf_ymax - sr_ymax > 2:
                    add_fw['w'] = '上工艺边'
               
                for slyr in outsignalLayers:
                    job_add_s20 = []
                    layer_cmd = gClasses.Layer(set_cmd, slyr)
                    syl_info = layer_cmd.featCurrent_LayerOut(units='mm')['pads']
                    s20_symbol = [obj for obj in syl_info if obj.symbol == 's508']
                    for obj_i in s20_symbol:
                        for obj_j in s20_symbol:
                            s20_space = math.sqrt((obj_j.x - obj_i.x) ** 2 + (obj_j.y - obj_i.y) ** 2)
                            if abs(s20_space - 5) < 0.1:
                                if abs(obj_i.y - obj_j.y) < 0.1:
                                    if obj_i.y > sr_ymax:
                                        job_add_s20.append('w')
                                    elif obj_i.y < sr_ymin:
                                        job_add_s20.append('d')
                                elif abs(obj_i.x - obj_j.x) < 0.1:
                                    if obj_i.x < sr_xmin:
                                        job_add_s20.append('l')
                                    elif obj_i.x > sr_xmax:
                                        job_add_s20.append('r')
                    for sym_fw in add_fw.keys():
                        if sym_fw not in job_add_s20:
                            log = u'检测到SET边{0}层{1}未添加锣板偏位测试coupon！'.format(slyr, add_fw[sym_fw])
                            arraylist.append(log)


        if "set" in matrixinfo["gCOLstep_name"]:
            stepName = 'set'
            step = gClasses.Step(job, 'set')
        elif "edit" in matrixinfo["gCOLstep_name"]:
            stepName = 'edit'
            step = gClasses.Step(job, 'edit')
        else:
            return "success", None
        # 检测是否运行过添加泪滴
        # if res == 'inner':
        #     get_status = get_topcam_status(330, jobname)
        # else:
        #     get_status = get_topcam_status(370, jobname)
        # if not get_status:
        #     log = u'检测到未用程序添加泪滴！'
        #     arraylist.append(log)

        #只有外层检测其它项目
        if res != 'inner':
            # 检测是否定义SMD和BGA属性
            # statu_dones = False
            # for ind in [294, 363]:
            #     get_status = get_topcam_status(ind, jobname)
            #     if get_status:
            #         statu_dones = True
            #         continue
            # if not statu_dones:
            #     log = u'检测到未用程序定义SMD和BGA属性！'
            #     arraylist.append(log)
            #
            # # 检测是否定义光学点属性
            # for layer_signal in outsignalLayers:
            #     get_info = step.INFO('-t layer -e %s/%s/%s -d FEATURES  -o break_sr' % (jobname, step.name, layer_signal))
            #     if not 'fiducial_name=mark' in ''.join(get_info):
            #         log = u'检测到{0}面未定义光学点属性'.format(layer_signal)
            #         arraylist.append(log)
            # 检测是否在批次号前面添加'-',有两种方式-可能分开添加了，需要获取批次号的位置，如果不带-则看批次号的前置位有没有-
            check_picihao_steps = get_panelset_sr_step(jobname, stepName)
            check_picihao_steps.append(stepName)
            for stp in check_picihao_steps:
                stp_cmd = gClasses.Step(job, stp)
                stp_cmd.open()
                stp_cmd.resetFilter()
                for lay in outsignalLayers + solderMaskLayers + silkscreenLayers:
                    stp_cmd.clearAll()
                    stp_cmd.affect(lay)
                    stp_cmd.COM("units,type=inch")
                    picihao_cmd = gClasses.Layer(stp_cmd, lay)
                    info_texts = picihao_cmd.featout_dic_Index(options='feat_index', units='inch')['text']
                    for obj in info_texts:
                        #T -0.7206931 -4.1551378 vgt_date P 0 N 0.031 0.04 0.67000 '-$$picihao' 1;.nomenclature
                        if 'picihao' in obj.text:
                            # 框选前置位有没有-
                            res_pic = False
                            if '-$$picihao' not in obj.text:
                                x1 = obj.x - 0.4
                                y1 = obj.y - 0.4
                                x2 = obj.x + 0.4
                                y2 = obj.y + 0.4
                                stp_cmd.filter_set(feat_types='text', polarity='positive')
                                stp_cmd.COM("filter_area_strt")
                                stp_cmd.COM("filter_area_xy,x=%s,y=%s" % (x1, y1))
                                stp_cmd.COM("filter_area_xy,x=%s,y=%s" % (x2, y2))
                                stp_cmd.COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,"
                                            "inside_area=yes,intersect_area=no")
                                # stp_cmd.PAUSE("222")
                                if stp_cmd.featureSelected():
                                    info_text_1 = picihao_cmd.featSelOut(units='inch')['text']
                                    exist_1 = [ibj for ibj in info_text_1 if ibj.text == "'-'"]
                                    if exist_1:
                                        res_pic = True
                            else:
                                res_pic = True
                            stp_cmd.resetFilter()
                            stp_cmd.selectNone()
                            if not res_pic:
                                stp_cmd.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(lay, obj.feat_index))
                    if stp_cmd.featureSelected():
                        log = u'{0}中{1}批次号前面没有添加横杠-'.format(stp, lay)
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stp, stp_cmd, lay,
                                                                             lay, log, dic_zu_layer, add_note_layer=lay)
            if stepName == 'set':
                # 检测客户品名
                inplan = InPlan(jobname)
                getstr = str(inplan.get_job_customer())
                if len(getstr.split()) == 2:
                    customer = getstr.split()[1].strip()
                else:
                    return "success", None
                step.open()
                step.clearAll()
                step.resetFilter()
                step.COM("units,type=inch")
                # 检查是否加客户料号名
                for sm in ['m1', 'm2']:
                    if sm not in step.getLayers():
                        log = u'资料中没有{0}层'.format(sm)
                        arraylist.append(log)
                        continue
                    info = step.INFO(" -t layer -e %s/%s/%s -d FEATURES  -o feat_index" % (jobname, step.name, sm))
                    customer_names = {}
                    for line in info:
                        # cus_list = line.split()
                        if '\'' + customer + '\'' in line.split():
                            index = line.split("#T")[0].strip().replace('#', '')
                            customer_names[index] = customer
                    if not customer_names:
                        log = u'客户品名为{0}，但{1}层中未添加'.format(customer, sm)
                        arraylist.append(log)
                    elif len(customer_names) > 1:
                        log = u'{0}层添加了{1}客户品名'.format(sm, len(customer_names))
                        arraylist.append(log)
                    else:
                        #  检查是否添加在铜面上
                        if sm == 'm1':
                            des_sginal = 'l1'
                            sg_layer = 'sgt-c'
                        else:
                            des_sginal = 'l{0}'.format(int(jobname[4:6]))
                            sg_layer = 'sgt-s'
                        des_back = des_sginal + '-overcuster'
                        ref_sm = sm + '-overcuster'
                        if step.isLayer(ref_sm):
                            step.affect(ref_sm)
                            step.selectDelete()
                            step.clearAll()
                        step.copyLayer(jobname, step.name, des_sginal, des_back)
                        step.clearAll()
                        step.affect(des_back)
                        step.contourize(units='inch', accuracy='0.01')
                        step.clearAll()
                        step.affect(sm)
                        step.selectFeatureIndex(sm, customer_names.keys()[0])
                        if step.featureSelected():
                            step.copyToLayer(ref_sm)
                            step.clearAll()
                            step.affect(ref_sm)
                            step.resetFilter()
                            step.refSelectFilter(des_back, mode='cover')
                            if not step.featureSelected():
                                log = u'{0}层客户品名未完全添加在铜面上，请检查'.format(sm)
                                arraylist.append(log)
                                step.clearAll()
                                step.affect(sm)
                                step.selectFeatureIndex(sm, customer_names.keys()[0])
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepName, step, sm,des_sginal, log,
                                                                                     dic_zu_layer, add_note_layer=sm)
                            step.resetFilter()
                            step.clearAll()
                            step.removeLayer(sg_layer + '_bh_')
                            if step.isLayer(sg_layer):
                                step.affect(sg_layer)
                                step.copyToLayer(sg_layer + '_bh_')
                                step.clearAll()
                                step.affect(sg_layer + '_bh_')
                                step.contourize(units='inch')
                                step.clearAll()
                                step.affect(ref_sm)
                                # step.selectNone()
                                step.refSelectFilter(sg_layer + '_bh_', mode='cover')
                                step.COM("sel_reverse")
                                if step.featureSelected():
                                    step.clearAll()
                                    step.affect(sm)
                                    step.selectFeatureIndex(sm, customer_names.keys()[0])
                                    log = u'{0}层客户品名需要全部按化金制作，请检查'.format(sm)
                                    arraylist.append(log)
                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepName, step, sm,
                                                                                         des_sginal, log,
                                                                                         dic_zu_layer,
                                                                                         add_note_layer=sm)

                        step.clearAll()
                        step.resetFilter()
                        step.removeLayer(des_back)
                        step.removeLayer(ref_sm)
            step.clearAll()
            step.resetFilter()
            MIChole = {}
            gen = genCOM_26.GEN_COM()
            if "edit" in matrixinfo["gCOLstep_name"]:
                edit_step = gClasses.Step(job, 'edit')
                for drl_name in ['drl', 'cdc', 'cds']:
                    if edit_step.isLayer(drl_name):
                        d_sizes = gen.DO_INFO("-t layer -e %s/%s/%s -d TOOL -p drill_size"
                                              % (jobname, 'edit', drl_name),units='mm')['gTOOLdrill_size']
                        hole_end7 = ['r' + i for i in d_sizes if i[-1] is '7']

                        if hole_end7:
                            MIChole[drl_name] = hole_end7
                # if MIChole:
                #     # 检测有没有加MIC孔环属性，暂时取消
                #         for slayer in outsignalLayers:
                #             s_info = edit_step.INFO('-t layer -e %s/%s/%s -d FEATURES' % (jobname, edit_step.name, slayer))
                #             if not 'fiducial_name=mic_pad' in ''.join(s_info):
                #                 log = u'检测到{0}面未定义MIC孔环属性'.format(slayer)
                #                 arraylist.append(log)

            if 'sgt-c' in matrixinfo["gROWname"] or 'sgt-s' in matrixinfo["gROWname"]:
                # 存在选化层检测MIC孔开窗和光学点开窗是否做化金
                step.open()
                step.COM("units,type=mm")
                step.clearAll()
                step.resetFilter()

                for stg in ['sgt-c', 'sgt-s']:
                    stg_back = stg + '_check_'
                    if not step.isLayer(stg):
                        continue
                    if stg == 'sgt-c':
                        line_name = 'l1'
                        soder_masks = [i for i in solderMaskLayers if 'm1' in i]
                    else:
                        soder_masks = [i for i in solderMaskLayers if 'm2' in i]
                        line_name = 'l{0}'.format(int(jobname[4:6]))

                    get_info_line = step.INFO('-t layer -e %s/%s/%s -d FEATURES' % (jobname, step.name, line_name))
                    if 'fiducial_name=mark' in ''.join(get_info_line):

                        step.open()
                        step.clearAll()
                        step.resetFilter()
                        step.flatten_layer(stg, stg_back)
                        step.affect(stg_back)
                        step.contourize(units='mm')
                        step.clearAll()
                        # step.affect(line_name)
                        step.removeLayer(line_name + '-bmark')
                        step.removeLayer(line_name + '-fmark')
                        step.flatten_layer(line_name,line_name + '-fmark')
                        step.affect(line_name + '-fmark')
                        step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.fiducial_name,text=mark")
                        step.selectAll()
                        if step.featureSelected():
                            step.copyToLayer(line_name + '-bmark')
                            step.clearAll()
                            step.affect(line_name + '-bmark')
                            step.resetFilter()
                            step.refSelectFilter(stg_back, mode='cover')
                            if step.featureSelected():
                                step.selectDelete()
                            step.selectAll()
                            if step.featureSelected():
                                step.clearAll()
                                step.affect(line_name)
                                step.refSelectFilter(line_name + '-bmark', mode='cover')
                                if step.featureSelected():
                                    log = u'{0}层光学点没有按化金制作，请检查'.format(line_name)
                                    arraylist.append(log)
                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name,
                                                                                         step, line_name,
                                                                                         stg, log, dic_zu_layer,
                                                                                         add_note_layer=line_name)

                        step.removeLayer(line_name + '-bmark')
                        step.removeLayer(line_name + '-fmark')
                        step.removeLayer(stg_back)
                        step.clearAll()
                        step.resetFilter()

                    if MIChole:
                        mic_hole = 'mic-hole-back'
                        step.removeLayer(mic_hole)
                        # mic孔只取edit中的
                        if "edit" in matrixinfo["gCOLstep_name"]:
                            edit_step = gClasses.Step(job, 'edit')
                            edit_step.open()
                            edit_step.flatten_layer(stg, stg_back)
                            for key, val in MIChole.items():
                                edit_step.clearAll()
                                edit_step.resetFilter()
                                edit_step.affect(key)
                                edit_step.filter_set(include_syms='\;'.join(val))
                                edit_step.selectAll()
                                if not edit_step.featureSelected():
                                    continue
                                edit_step.copyToLayer(mic_hole)
                                edit_step.clearAll()
                                edit_step.resetFilter()
                                for sm_layer in soder_masks:
                                    sm_layer_back = sm_layer + '-sm-fle'
                                    edit_step.flatten_layer(sm_layer, sm_layer_back)
                                    edit_step.clearAll()
                                    edit_step.affect(sm_layer_back)
                                    edit_step.contourize(units='mm')
                                    edit_step.filter_set(polarity='positive')
                                    edit_step.refSelectFilter(mic_hole)
                                    if edit_step.featureSelected():
                                        edit_step.COM("sel_reverse")
                                        edit_step.selectDelete()
                                        edit_step.clearAll()
                                        edit_step.resetFilter()
                                        edit_step.affect(stg_back)
                                        edit_step.contourize(units='mm')
                                        edit_step.clearAll()
                                        edit_step.affect(sm_layer_back)
                                        edit_step.refSelectFilter(stg_back, mode='cover')
                                        if edit_step.featureSelected():
                                            edit_step.selectDelete()
                                        edit_step.clearAll()
                                        edit_step.affect(key)
                                        edit_step.refSelectFilter(sm_layer_back, mode='cover')
                                        if edit_step.featureSelected():
                                            log = u'MIC孔在{0}开窗，没有按化金制作，请检查'.format(sm_layer)
                                            arraylist.append(log)
                                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, edit_step.name, edit_step, key,
                                                                                                 stg, log,dic_zu_layer,add_note_layer=key)
                                    edit_step.removeLayer(sm_layer_back)
                            edit_step.removeLayer(stg_back)
                            edit_step.removeLayer(mic_hole)
                            edit_step.clearAll()
                            edit_step.resetFilter()
                            edit_step.close()
        if arraylist:
            return arraylist, dic_zu_layer
        return "success", None

    def check_183_desiger(self):
        """
        183客户指定检测项目
        1. 检测工艺边是否添加客户料号名, 检查是否添加在完整铜面上
        2. 选化板检测MIC孔开窗，光学点是否按化金制作
        3. 检测是否添加泪滴
        4. 检测是否定义光学点属性
        5. 检测是否漏加coupon  防焊偏位，锣板偏位，防焊爆偏，防漏接
        6. 检测批次号前面是否加'-' 周期-批次号
        """
        if jobname[1:4] != '183':
            return "success", None
        arraylist = []
        dic_zu_layer = {}
        res = os.environ.get("INNER_OUTER", "")
        # try:
        #     res = os.environ.get("INNER_OUTER", "inner")
        # except:
        #     res = 'outer'
        # 检测是否运行过检测铜面PAD

        # 检测是否添加各类测试coupon
        if 'set' in job.getSteps().keys():
            inser_steps = get_panelset_sr_step(jobname, 'set')
            floujies = [s for s in inser_steps if 'floujie' in s]
            if laser_drill_layers and not floujies:
                log = u'检测到SET边未添加防漏接测试coupon！'
                arraylist.append(log)
            if 'sm4-coupon' not in ';'.join(inser_steps):
                log = u'检测到SET边未添加防爆偏(sm4-coupon)！'
                arraylist.append(log)
            set_cmd = gClasses.Step(job, 'set')
            if res == 'outer':
                for sm in ['m1', 'm2']:
                    if set_cmd.isLayer(sm):
                        infolines = set_cmd.INFO("-t layer -e %s/set/%s -d FEATURES" % (jobname, sm))
                        if not '3mil' in ''.join(infolines) or not '7mil' in ''.join(infolines):
                            log = u'检测到SET边{0}层未添加防切偏coupon！'.format(sm)
                            arraylist.append(log)
                # 锣板偏位检测
                for slyr in outsignalLayers:
                    layer_cmd = gClasses.Layer(set_cmd, slyr)
                    syl_info = layer_cmd.featCurrent_LayerOut(units='mm')['pads']
                    s20_symbol = [obj for obj in syl_info if obj.symbol == 's508']
                    space_exits = False
                    for obj_i in s20_symbol:
                        for obj_j in s20_symbol:
                            s20_space = math.sqrt((obj_j.x - obj_i.x) ** 2 + (obj_j.y - obj_i.y) ** 2)
                            if s20_space - 5 < 0.1:
                                space_exits = True
                                break
                    if space_exits == False:
                        log = u'检测到SET边{0}层未添加锣板偏位测试coupon！'.format(slyr)
                        arraylist.append(log)

        if "set" in matrixinfo["gCOLstep_name"]:
            stepName = 'set'
            step = gClasses.Step(job, 'set')
        elif "edit" in matrixinfo["gCOLstep_name"]:
            stepName = 'edit'
            step = gClasses.Step(job, 'edit')
        else:
            return "success", None
        # 检测是否运行过添加泪滴
        # if res == 'inner':
        #     get_status = get_topcam_status(330, jobname)
        # else:
        #     get_status = get_topcam_status(370, jobname)
        # if not get_status:
        #     log = u'检测到未用程序添加泪滴！'
        #     arraylist.append(log)

        #只有外层检测其它项目
        if res == 'outer':
            # 检测是否定义SMD和BGA属性
            # statu_dones = False
            # for ind in [294, 363]:
            #     get_status = get_topcam_status(ind, jobname)
            #     if get_status:
            #         statu_dones = True
            #         continue
            # if not statu_dones:
            #     log = u'检测到未用程序定义SMD和BGA属性！'
            #     arraylist.append(log)
            #
            # # 检测是否定义光学点属性
            # for layer_signal in outsignalLayers:
            #     get_info = step.INFO('-t layer -e %s/%s/%s -d FEATURES  -o break_sr' % (jobname, step.name, layer_signal))
            #     if not 'fiducial_name=mark' in ''.join(get_info):
            #         log = u'检测到{0}面未定义光学点属性'.format(layer_signal)
            #         arraylist.append(log)
            # 检测是否在批次号前面添加'-',有两种方式-可能分开添加了，需要获取批次号的位置，如果不带-则看批次号的前置位有没有-，还有可能是线条-
            check_picihao_steps = get_panelset_sr_step(jobname, stepName)
            check_picihao_steps.append(stepName)
            for stp in check_picihao_steps:
                stp_cmd = gClasses.Step(job, stp)
                stp_cmd.open()
                stp_cmd.resetFilter()
                for lay in outsignalLayers + solderMaskLayers + silkscreenLayers:
                    stp_cmd.clearAll()
                    stp_cmd.affect(lay)
                    stp_cmd.COM("units,type=inch")
                    picihao_cmd = gClasses.Layer(stp_cmd, lay)
                    info_texts = picihao_cmd.featout_dic_Index(options='feat_index', units='inch')['text']
                    for obj in info_texts:
                        #T -0.7206931 -4.1551378 vgt_date P 0 N 0.031 0.04 0.67000 '-$$picihao' 1;.nomenclature
                        if 'picihao' in obj.text:
                            # 框选前置位有没有-
                            res_pic = False
                            if '-$$picihao' not in obj.text:
                                x1 = obj.x - 0.4
                                y1 = obj.y - 0.4
                                x2 = obj.x + 0.4
                                y2 = obj.y + 0.4
                                stp_cmd.filter_set(feat_types='text', polarity='positive')
                                stp_cmd.COM("filter_area_strt")
                                stp_cmd.COM("filter_area_xy,x=%s,y=%s" % (x1, y1))
                                stp_cmd.COM("filter_area_xy,x=%s,y=%s" % (x2, y2))
                                stp_cmd.COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,"
                                            "inside_area=yes,intersect_area=no")
                                # stp_cmd.PAUSE("222")
                                if stp_cmd.featureSelected():
                                    info_text_1 = picihao_cmd.featSelOut(units='inch')['text']
                                    exist_1 = [ibj for ibj in info_text_1 if ibj.text == "'-'"]
                                    if exist_1:
                                        res_pic = True
                            else:
                                res_pic = True
                            stp_cmd.resetFilter()
                            stp_cmd.selectNone()
                            if not res_pic:
                                stp_cmd.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(lay, obj.feat_index))
                    if stp_cmd.featureSelected():
                        log = u'{0}中{1}批次号前面没有添加横杠-'.format(stp, lay)
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stp, stp_cmd, lay,
                                                                             lay, log, dic_zu_layer, add_note_layer=lay)
            if stepName == 'set':
                # 检测客户品名
                inplan = InPlan(jobname)
                getstr = str(inplan.get_job_customer())
                if len(getstr.split()) == 2:
                    customer = getstr.split()[1].strip()
                else:
                    return "success", None
                step.open()
                step.clearAll()
                step.resetFilter()
                step.COM("units,type=inch")
                # 检查是否加客户料号名
                for sm in ['m1', 'm2']:
                    if sm not in step.getLayers():
                        log = u'资料中没有{0}层'.format(sm)
                        arraylist.append(log)
                        continue
                    info = step.INFO(" -t layer -e %s/%s/%s -d FEATURES  -o feat_index" % (jobname, step.name, sm))
                    customer_names = {}
                    for line in info:
                        # cus_list = line.split()
                        if '\'' + customer + '\'' in line.split():
                            index = line.split("#T")[0].strip().replace('#', '')
                            customer_names[index] = customer
                    if not customer_names:
                        log = u'客户品名为{0}，但{1}层中未添加'.format(customer, sm)
                        arraylist.append(log)
                    elif len(customer_names) > 1:
                        log = u'{0}层添加了{1}客户品名'.format(sm, len(customer_names))
                        arraylist.append(log)
                    else:
                        #  检查是否添加在铜面上
                        if sm == 'm1':
                            des_sginal = 'l1'
                            sg_layer = 'sgt-c'
                        else:
                            des_sginal = 'l{0}'.format(int(jobname[4:6]))
                            sg_layer = 'sgt-s'
                        des_back = des_sginal + '-overcuster'
                        ref_sm = sm + '-overcuster'
                        if step.isLayer(ref_sm):
                            step.affect(ref_sm)
                            step.selectDelete()
                            step.clearAll()
                        step.copyLayer(jobname, step.name, des_sginal, des_back)
                        step.clearAll()
                        step.affect(des_back)
                        step.contourize(units='inch', accuracy='0.01')
                        step.clearAll()
                        step.affect(sm)
                        step.selectFeatureIndex(sm, customer_names.keys()[0])
                        if step.featureSelected():
                            step.copyToLayer(ref_sm)
                            step.clearAll()
                            step.affect(ref_sm)
                            step.resetFilter()
                            step.refSelectFilter(des_back, mode='cover')
                            if not step.featureSelected():
                                log = u'{0}层客户品名未完全添加在铜面上，请检查'.format(sm)
                                arraylist.append(log)
                                step.clearAll()
                                step.affect(sm)
                                step.selectFeatureIndex(sm, customer_names.keys()[0])
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepName, step, sm,des_sginal, log,
                                                                                     dic_zu_layer, add_note_layer=sm)
                            step.resetFilter()
                            step.clearAll()
                            step.removeLayer(sg_layer + '_bh_')
                            if step.isLayer(sg_layer):
                                step.affect(sg_layer)
                                step.copyToLayer(sg_layer + '_bh_')
                                step.clearAll()
                                step.affect(sg_layer + '_bh_')
                                step.contourize(units='inch')
                                step.clearAll()
                                step.affect(ref_sm)
                                # step.selectNone()
                                step.refSelectFilter(sg_layer + '_bh_', mode='cover')
                                step.COM("sel_reverse")
                                if step.featureSelected():
                                    step.clearAll()
                                    step.affect(sm)
                                    step.selectFeatureIndex(sm, customer_names.keys()[0])
                                    log = u'{0}层客户品名需要全部按化金制作，请检查'.format(sm)
                                    arraylist.append(log)
                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, stepName, step, sm,
                                                                                         des_sginal, log,
                                                                                         dic_zu_layer,
                                                                                         add_note_layer=sm)

                        step.clearAll()
                        step.resetFilter()
                        step.removeLayer(des_back)
                        step.removeLayer(ref_sm)
            step.clearAll()
            step.resetFilter()
            MIChole = {}
            gen = genCOM_26.GEN_COM()
            if "edit" in matrixinfo["gCOLstep_name"]:
                edit_step = gClasses.Step(job, 'edit')
                for drl_name in ['drl', 'cdc', 'cds']:
                    if edit_step.isLayer(drl_name):
                        d_sizes = gen.DO_INFO("-t layer -e %s/%s/%s -d TOOL -p drill_size"
                                              % (jobname, 'edit', drl_name),units='mm')['gTOOLdrill_size']
                        hole_end7 = ['r' + i for i in d_sizes if i[-1] is '7']

                        if hole_end7:
                            MIChole[drl_name] = hole_end7
                # if MIChole:
                #     # 检测有没有加MIC孔环属性，暂时取消
                #         for slayer in outsignalLayers:
                #             s_info = edit_step.INFO('-t layer -e %s/%s/%s -d FEATURES' % (jobname, edit_step.name, slayer))
                #             if not 'fiducial_name=mic_pad' in ''.join(s_info):
                #                 log = u'检测到{0}面未定义MIC孔环属性'.format(slayer)
                #                 arraylist.append(log)

            if 'sgt-c' in matrixinfo["gROWname"] or 'sgt-s' in matrixinfo["gROWname"]:
                # 存在选化层检测MIC孔开窗和光学点开窗是否做化金
                step.open()
                step.COM("units,type=mm")
                step.clearAll()
                step.resetFilter()

                for stg in ['sgt-c', 'sgt-s']:
                    stg_back = stg + '_check_'
                    if not step.isLayer(stg):
                        continue
                    if stg == 'sgt-c':
                        line_name = 'l1'
                        soder_masks = [i for i in solderMaskLayers if 'm1' in i]
                    else:
                        soder_masks = [i for i in solderMaskLayers if 'm2' in i]
                        line_name = 'l{0}'.format(int(jobname[4:6]))

                    get_info_line = step.INFO('-t layer -e %s/%s/%s -d FEATURES' % (jobname, step.name, line_name))
                    if 'fiducial_name=mark' in ''.join(get_info_line):

                        step.open()
                        step.clearAll()
                        step.resetFilter()
                        step.flatten_layer(stg, stg_back)
                        step.affect(stg_back)
                        step.contourize(units='mm')
                        step.clearAll()
                        # step.affect(line_name)
                        step.removeLayer(line_name + '-bmark')
                        step.removeLayer(line_name + '-fmark')
                        step.flatten_layer(line_name,line_name + '-fmark')
                        step.affect(line_name + '-fmark')
                        step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.fiducial_name,text=mark")
                        step.selectAll()
                        if step.featureSelected():
                            step.copyToLayer(line_name + '-bmark')
                            step.clearAll()
                            step.affect(line_name + '-bmark')
                            step.resetFilter()
                            step.refSelectFilter(stg_back, mode='cover')
                            if step.featureSelected():
                                step.selectDelete()
                            step.selectAll()
                            if step.featureSelected():
                                step.clearAll()
                                step.affect(line_name)
                                step.refSelectFilter(line_name + '-bmark', mode='cover')
                                if step.featureSelected():
                                    log = u'{0}层光学点没有按化金制作，请检查'.format(line_name)
                                    arraylist.append(log)
                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name,
                                                                                         step, line_name,
                                                                                         stg, log, dic_zu_layer,
                                                                                         add_note_layer=line_name)

                        step.removeLayer(line_name + '-bmark')
                        step.removeLayer(line_name + '-fmark')
                        step.removeLayer(stg_back)
                        step.clearAll()
                        step.resetFilter()

                    if MIChole:
                        mic_hole = 'mic-hole-back'
                        step.removeLayer(mic_hole)
                        # mic孔只取edit中的
                        if "edit" in matrixinfo["gCOLstep_name"]:
                            edit_step = gClasses.Step(job, 'edit')
                            edit_step.open()
                            edit_step.flatten_layer(stg, stg_back)
                            for key, val in MIChole.items():
                                edit_step.clearAll()
                                edit_step.resetFilter()
                                edit_step.affect(key)
                                edit_step.filter_set(include_syms='\;'.join(val))
                                edit_step.selectAll()
                                if not edit_step.featureSelected():
                                    continue
                                edit_step.copyToLayer(mic_hole)
                                edit_step.clearAll()
                                edit_step.resetFilter()
                                for sm_layer in soder_masks:
                                    sm_layer_back = sm_layer + '-sm-fle'
                                    edit_step.flatten_layer(sm_layer, sm_layer_back)
                                    edit_step.clearAll()
                                    edit_step.affect(sm_layer_back)
                                    edit_step.contourize(units='mm')
                                    edit_step.filter_set(polarity='positive')
                                    edit_step.refSelectFilter(mic_hole)
                                    if edit_step.featureSelected():
                                        edit_step.COM("sel_reverse")
                                        edit_step.selectDelete()
                                        edit_step.clearAll()
                                        edit_step.resetFilter()
                                        edit_step.affect(stg_back)
                                        edit_step.contourize(units='mm')
                                        edit_step.clearAll()
                                        edit_step.affect(sm_layer_back)
                                        edit_step.refSelectFilter(stg_back, mode='cover')
                                        if edit_step.featureSelected():
                                            edit_step.selectDelete()
                                        edit_step.clearAll()
                                        edit_step.affect(key)
                                        edit_step.refSelectFilter(sm_layer_back, mode='cover')
                                        if edit_step.featureSelected():
                                            log = u'MIC孔在{0}开窗，没有按化金制作，请检查'.format(sm_layer)
                                            arraylist.append(log)
                                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, edit_step.name, edit_step, key,
                                                                                                 stg, log,dic_zu_layer,add_note_layer=key)
                                    edit_step.removeLayer(sm_layer_back)
                            edit_step.removeLayer(stg_back)
                            edit_step.removeLayer(mic_hole)
                            edit_step.clearAll()
                            edit_step.resetFilter()
                            edit_step.close()
        if arraylist:
            return arraylist, dic_zu_layer
        return "success", None

    def check_fbk_to_rhk_space(self):
        """
        检查防爆孔和热熔快的间距是否偏差在20mil以上
        """
        if "panel" not in matrixinfo["gCOLstep_name"]:
            return u"panel不存在", None
        stepname = "panel"
        step = gClasses.Step(job, stepname)
        step.open()
        step.resetFilter()
        step.clearAll()
        step.COM("units,type=inch")
        tmp_layer = {'rhk':'rhk_tmp_1_', 'fbk':'fbk_tmp_1_'}
        res = False
        log = []
        step.removeLayer(tmp_layer['fbk'])
        step.createLayer(tmp_layer['fbk'])
        step.removeLayer(tmp_layer['rhk'])
        step.createLayer(tmp_layer['rhk'])
        if step.isLayer('drl'):
            step.affect('drl')
        if step.isLayer('cdc'):
            step.affect('cdc')
        elif step.isLayer('cds'):
            step.affect('cds')
        # step.setAttrFilter(attr='.string')
        step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=fbk")
        step.selectAll()
        if step.featureSelected():
            step.resetAttr()
            step.copySel(tmp_layer['fbk'])
            step.clearAll()
            for layer in innersignalLayers:
                step.affect(tmp_layer['rhk'])
                step.selectDelete()
                step.unaffect(tmp_layer['rhk'])
                step.affect(layer)
                step.resetFilter()
                step.filter_set(include_syms='chris-rjpad')
                step.selectAll()
                if step.featureSelected():
                    step.copySel(tmp_layer['rhk'])
                    step.clearAll()
                    step.affect(tmp_layer['rhk'])
                    step.COM("sel_break")
                    step.filter_set(polarity='negative', reset='yes')
                    step.selectAll()
                    if step.featureSelected():
                        step.selectDelete()
                    step.resetFilter()
                    step.COM("sel_resize,size=40,corner_ctl=no")
                    step.contourize(units='inch')
                    step.unaffect(tmp_layer['rhk'])
                    step.affect(tmp_layer['fbk'])
                    step.refSelectFilter(tmp_layer['rhk'], mode='cover')
                    if step.featureSelected():
                        step.selectDelete()
                    step.COM("sel_reverse")
                    if step.featureSelected():
                        res = True
                        log.append(u"%s层存在防爆孔和热熔块间距大于20mil")
                    step.unaffect(tmp_layer['fbk'])
        step.resetFilter()
        step.clearAll()
        step.removeLayer(tmp_layer['fbk'])
        step.removeLayer(tmp_layer['rhk'])
        return res, log

    def check_pad_resize(self, check_step_name):
        """
        1.将原稿需补偿pad单独复制到a和aa层，a层按规范补偿，aa层多补偿0.1mil；
        2.将工作稿已补偿的smd pad 复制到一层b；
        3.使用参考选择命令用b层包围a层，包围到的资料全部删除，未被包围到的即为补偿不足。
        4.使用参考选择命令用aa层包围b层，包围到的资料全部删除，未被包围到的即为补偿过多。
        """
        arraylist = []
        dic_zu_layer = {}
        if 'net' not in job.getSteps():
            return
        step = gClasses.Step(job, check_step_name)
        step.open()
        step.clearAll()
        step.resetFilter()
        for sg in outsignalLayers:
            sgLayer = {'org' : sg + '-org-netlayer','wk': sg + '-wblayer'}
            step.removeLayer(sgLayer['wk'])
            step.copyLayer(job=jobname, step='net', lay=sg, dest_lay=sgLayer['org'])
            step.affect(sgLayer['org'])
            step.filter_set(feat_types='line;arc;text;surface')
            step.selectAll()
            if step.featureSelected():
                step.selectDelete()
            step.resetFilter()
            step.clearAll()
            step.affect(sg)
            step.setAttrFilter(attr='.smd')
            step.selectAll()
            if step.featureSelected():
                step.copyToLayer(sgLayer['wk'])
            step.resetFilter()
            step.setAttrFilter(attr='.bga')
            step.selectAll()
            if step.featureSelected():
                step.copyToLayer(sgLayer['wk'])
            step.resetFilter()
        if arraylist:
            return arraylist, dic_zu_layer
        return "success", None

    def check_pad_attr(self, check_step_name):
        """
        检查PAD属性定义是否正确
        """
        arraylist = []
        dic_zu_layer = {}
        step = gClasses.Step(job, check_step_name)
        step.open()
        step.clearAll()
        step.resetFilter()
        step.COM("units,type=inch")
        tmp_drill = 'drl_pad_attr'
        step.removeLayer(tmp_drill)
        step.createLayer(tmp_drill)
        for drl in tongkongDrillLayer:
            # tmp层只挑出槽孔和大孔0.65以上
            info = step.DO_INFO("-t layer -e %s/%s/%s -d TOOL -p drill_size" % (jobname, step.name, drl))['gTOOLdrill_size']
            drl_size = list(set(['r{0}'.format(s) for s in info if float(s) > 650/25.4 ]))
            step.clearAll()
            step.affect(drl)
            step.filter_set(feat_types='line')
            step.selectAll()
            if step.featureSelected():
                step.copyToLayer(tmp_drill)
            step.resetFilter()
            step.filter_set(include_syms='oval*')
            step.selectAll()
            if step.featureSelected():
                step.copyToLayer(tmp_drill)
            step.resetFilter()
            if drl_size:
                step.filter_set(include_syms='\\;'.join(drl_size))
                step.selectAll()
                if step.featureSelected():
                    step.copyToLayer(tmp_drill)
        step.resetFilter()
        step.clearAll()
        for layer in outsignalLayers:
            if layer == 'l1':
                if 'm1' in solderMaskLayers:
                    smlayer = 'm1'
                else:continue
            else:
                if 'm2' in solderMaskLayers:
                    smlayer = 'm2'
                else:continue
            tmp_layer = layer + '_pad_attr'
            tmp_smlayer = smlayer + '_pad_attr'
            step.removeLayer(tmp_layer)
            step.createLayer(tmp_layer)
            step.removeLayer(tmp_smlayer)
            step.createLayer(tmp_smlayer)
            step.copyLayer(jobname, check_step_name, smlayer, tmp_smlayer)
            step.affect(layer)
            step.filter_set(feat_types='pad')
            step.selectAll()
            if step.featureSelected():
                step.copyToLayer(tmp_layer)
            step.clearAll()
            step.resetFilter()
            step.affect(tmp_smlayer)
            step.contourize(units='inch')
            step.refSelectFilter(tmp_layer,mode='disjoint')
            if step.featureSelected():
                step.selectDelete()
            step.clearAll()
            # 删除对应孔PAD
            step.affect(tmp_layer)
            step.refSelectFilter(refLay=tmp_drill, mode='include')
            if step.featureSelected():
                step.selectDelete()
            for dn in laser_drill_layers + tongkongDrillLayer:
                if (layer == 'l1' and 's1-' in dn) or \
                        (layer == 'l{0}'.format(int(jobname[4:6])) and 's{0}-'.format(int(jobname[4:6])) in dn) or \
                        dn in tongkongDrillLayer:
                    step.resetFilter()
                    step.refSelectFilter(dn, mode='cover')
                    if step.featureSelected():
                        step.selectDelete()
                    step.resetFilter()
                    step.filter_set(feat_types='pad', include_syms='r*', exclude_syms='rect*')
                    step.COM(
                        "set_filter_attributes,filter_name=popup,exclude_attributes=yes,condition=no,attribute=.bga,"
                        "min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=")
                    step.COM(
                        "set_filter_attributes,filter_name=popup,exclude_attributes=yes,condition=no,attribute=.smd,"
                        "min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=")
                    step.refSelectFilter(refLay=dn, mode='include')
                    if step.featureSelected():
                        step.selectDelete()
                    step.resetFilter()
            step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.smd")
            step.selectAll()
            step.resetFilter()
            step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.bga")
            step.selectAll()
            step.resetFilter()
            if step.featureSelected():
                step.selectDelete()
            step.resetFilter()
            step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.bga")
            step.selectAll()
            if step.featureSelected():
                step.selectDelete()
            step.resetFilter()
            step.refSelectFilter(tmp_smlayer, mode='cover')
            if step.featureSelected():
                step.COM("sel_reverse")
                if step.featureSelected():
                    step.selectDelete()
                step.clearAll()
                step.affect(layer)
                step.filter_set(feat_types='pad', polarity='positive')
                step.refSelectFilter(tmp_layer, mode='include')
                if step.featureSelected():
                    log = u"{0}疑似部分PAD漏定义属性，请查看！".format(layer)
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, check_step_name, step, layer,
                                                                         smlayer, log, dic_zu_layer, add_note_layer=layer)
            step.clearAll()
            step.resetFilter()
            # step.removeLayer(tmp_layer)
            step.removeLayer(tmp_smlayer)
        step.removeLayer(tmp_drill)
        if arraylist:
            return arraylist, dic_zu_layer
        return "success", None

    def check_icg_surface_width(self):
        """
        检测阻抗条是否含有8MIL以下的细丝
        """
        arraylist = []
        dic_zu_layer = {}
        icg_coupons = [d for d in matrixinfo["gCOLstep_name"] if re.match('icg', d)]
        ctr_width = 8
        surface_lay = 'icg_8mil_surface'
        line_lay = 'icg_8mil_linew_'
        for icg in icg_coupons:
            step = gClasses.Step(job, icg)
            step.open()
            step.clearAll()
            step.resetFilter()
            step.removeLayer(surface_lay)
            step.removeLayer(line_lay)
            step.createLayer(surface_lay)
            step.createLayer(line_lay)
            step.COM("units,type=inch")

            for lay in outsignalLayers + innersignalLayers:
                step.clearAll()
                step.resetFilter()
                step.affect(surface_lay)
                step.affect(line_lay)
                step.selectDelete()
                step.clearAll()
                step.affect(lay)
                step.resetFilter()
                step.filter_set(feat_types='surface', polarity='positive')
                step.selectAll()
                if not step.featureSelected():
                    step.clearAll()
                    continue
                step.copyToLayer(surface_lay)
                step.resetFilter()
                step.filter_set( polarity='negative')
                # step.filter_set(feat_types='line;arc', polarity='negative')
                step.selectAll()
                if not step.featureSelected():
                    step.clearAll()
                    continue
                step.copyToLayer(surface_lay)
                step.resetFilter()
                step.filter_set(feat_types='line;arc', polarity='positive')
                step.selectAll()
                if step.featureSelected():
                    step.copyToLayer(line_lay)
                    step.clearAll()
                    step.resetFilter()
                    step.affect(line_lay)
                    step.contourize(units='inch')
                    # self.reset_touch_features(step)
                    step.refSelectFilter(refLay=lay, f_types= "pad\;text", polarity='positive', mode='disjoint')
                    # if  'ynh' in jobname and icg == 'icg1' and lay == 'l5':
                    #     step.PAUSE(line_lay)
                    if step.featureSelected():
                        step.copyToLayer(surface_lay)
                step.clearAll()
                step.resetFilter()
                step.affect(line_lay)
                step.selectDelete()
                step.clearAll()
                step.affect(surface_lay)

                # step.COM("sel_contourize,accuracy=0,break_to_islands=no,clean_hole_size=3,clean_hole_mode=x_and_y,validate_result=no")
                step.contourize(units='inch')
                step.copyLayer(jobname, step.name, surface_lay, line_lay)
                step.clearAll()

                step.affect(line_lay)
                # step.contourize(units='inch')
                step.COM("sel_contourize,accuracy=0,break_to_islands=no,clean_hole_size=3,clean_hole_mode=x_and_y,validate_result=no")
                step.COM("sel_resize,size=-{0},corner_ctl=no".format(ctr_width - 0.05))
                step.COM("sel_resize,size={0},corner_ctl=no".format(ctr_width + 1))

                step.copyToLayer(surface_lay, invert='yes')
                step.clearAll()
                step.affect(surface_lay)
                step.contourize(units='inch')
                step.clearAll()
                step.affect(line_lay)
                step.selectDelete()
                step.copyLayer(jobname, step.name, surface_lay, line_lay)
                step.clearAll()
                # surface转线条
                step.affect(surface_lay)

                step.COM("sel_surf2outline,width=1")
                lay_cmd = gClasses.Layer(step, surface_lay)
                features = lay_cmd.featout_dic_Index(options='feat_index', units='inch')['lines']
                sel_index = []
                if features:
                    for obj in features:
                        if obj.len > 1:
                            sel_index.append(obj.feat_index)

                if not sel_index:
                    step.clearAll()
                    continue

                for index in sel_index:
                    step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(surface_lay, index))

                step.COM("sel_reverse")
                if step.featureSelected():
                    step.selectDelete()
                step.clearAll()
                step.affect(line_lay)
                # self.reset_touch_features(step)
                step.refSelectFilter(surface_lay, mode='disjoint')
                # step.COM("sel_ref_feat,layers={0},use=filter,mode=disjoint,pads_as=shape,"
                #          "f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=".format(
                #     surface_lay))


                # step.refSelectFilter(surface_lay)
                # step.COM("sel_reverse")
                if step.featureSelected():
                    step.selectDelete()
                step.selectAll()

                # 获取surface铜皮的中心allsymbol_xy.append((Obj.x, Obj.y, "surface"))
                lay_cmd = gClasses.Layer(step, line_lay)
                info_indexs= lay_cmd.featSelIndex()
                # step.selectNone()
                allsymbols = []
                if info_indexs:
                    for index in info_indexs:
                        step.selectNone()
                        step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(line_lay, index))
                        limit = step.DO_INFO("-t layer -e %s/%s/%s -d LIMITS, units=mm" % (jobname, icg, line_lay))
                        cent_x, cent_y = float(limit['gLIMITSxcenter']),  float(limit['gLIMITSycenter']) + 0.02
                        allsymbols.append((cent_x, cent_y, "surface"))
                    log = u"阻抗条:{0}, {1}层标记处铜皮线宽度不足8MIL".format(icg, lay)
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, lay, lay, log,
                                                                         dic_zu_layer, add_note_layer=lay, allsymbol_xy= allsymbols)


                step.clearAll()
                step.resetFilter()
            step.removeLayer(surface_lay)
            step.removeLayer(line_lay)

        if arraylist:
            return arraylist, dic_zu_layer

        return "success", None

    def check_8888_hole_touch_other_symbol(self):
        """
        检测添加的字麦孔是否和其它物件接触
        """
        arraylist = []
        dic_zu_layer = {}
        if "panel" not in matrixinfo["gCOLstep_name"]:
            return "success", None
        stepname = "panel"
        step = gClasses.Step(job, stepname)
        step.open()
        step.clearAll()
        step.resetFilter()
        # 获取钻带中含有TEXT字样的孔层
        jxz_list = tongkongDrillLayer + mai_drill_layers + mai_man_drill_layers + bd_drillLayer + ksz_layers
        if step.isLayer('2nd'):
            jxz_list.append('2nd')
        if step.isLayer('3nd'):
            jxz_list.append('3nd')
        # 加入铝片层和导气层的检测
        all_layers = step.getLayers().keys()
        for lay in all_layers:
            if re.match('sz.*lp\d?', lay) or re.match('sz.*dq\d?', lay):
                pass

        check_text_layers = []
        for drl_name in jxz_list:
            lay_cmd = gClasses.Layer(step, drl_name)
            features_info = lay_cmd.featCurrent_LayerOut()['text']
            if features_info:
                check_text_layers.append(drl_name)
        if not check_text_layers:
            return "success", None
        # 生成内层需要避开的物件层
        tmpLayers = {'inner': 'inner_tmp_br_',
                     'outer': 'outer_tmp_br_',
                      'fill': 'fill_tmp_br_',
                     'text': 'text_tmp_br_',}
        for layer in tmpLayers.values():
            step.removeLayer(layer)
            step.createLayer(layer)
        step.clearAll()
        step.affect(tmpLayers['fill'])
        step.COM("units,type=mm")
        step.COM(
            "fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=25.4,use_arcs=yes,"
            "symbol=,dx=2.54,dy=2.54,std_angle=45,std_line_width=254,std_step_dist=1270,std_indent=odd,break_partial=yes,"
            "cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no")
        step.COM(
            "sr_fill,type=solid,solid_type=surface,min_brush=25.4,use_arcs=yes,cut_prims=no,outline_draw=no,outline_width=0,"
            "outline_invert=no,polarity=positive,step_margin_x=0,step_margin_y=0,step_max_dist_x=2540,step_max_dist_y=2540,"
            "sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,consider_feat=no,feat_margin=0,consider_drill=no,"
            "drill_margin=0,consider_rout=no,dest=affected_layers,layer=.affected,stop_at_steps=")
        step.clearAll()
        #内层钻孔需要避开的物件层
        if innersignalLayers:
            for layer in innersignalLayers:
                step.affect(layer)
            step.resetFilter()
            step.filter_set(include_syms='et_rj_pad*\;chris-rjpad')
            step.selectAll()
            if step.featureSelected():
                step.copyToLayer(tmpLayers['inner'])
                step.clearAll()
                step.resetFilter()
                step.affect(tmpLayers['inner'])
                step.COM("sel_break")
                step.filter_set(include_syms='S15000')
                step.selectAll()
                if step.featureSelected():
                    step.selectDelete()

            step.clearAll()
            step.resetFilter()

            for layer in innersignalLayers:
                step.affect(layer)

            step.filter_set(feat_types='pad;line;arc;text', exclude_syms='et_rj_pad*\;chris-rjpad')
            step.selectAll()
            if step.featureSelected():
                step.copyToLayer(tmpLayers['inner'])
            step.clearAll()
            step.resetFilter()
            step.affect(tmpLayers['inner'])
            step.filter_set(include_syms='r1', polarity='negative')
            step.selectAll()
            if step.featureSelected():
                step.selectDelete()

        step.resetFilter()
        step.clearAll()
        # 制作外层钻带需要避开的物件层
        for layer in outsignalLayers + solderMaskLayers + silkscreenLayers:
            step.affect(layer)
        step.resetFilter()
        step.filter_set(feat_types='pad;line;arc;text')
        step.selectAll()
        if step.featureSelected():
            step.copyToLayer(tmpLayers['outer'])

        step.clearAll()
        step.resetFilter()
        # 所有的钻孔层copy到内外层物件中
        step.filter_set(feat_types='pad;line;arc')
        for lay in jxz_list:
            step.affect(lay)
        step.selectAll()
        if step.featureSelected():
            step.copyToLayer(tmpLayers['inner'])
        step.selectNone()
        step.selectAll()
        if step.featureSelected():
            step.copyToLayer(tmpLayers['outer'])
        step.clearAll()
        for drl_name in check_text_layers:
            step.resetFilter()
            step.clearAll()
            step.filter_set(feat_types='text')
            step.affect(drl_name)
            step.refSelectFilter(refLay=tmpLayers['fill'], mode='cover')
            step.COM("sel_reverse")
            step.resetFilter()
            step.filter_set(feat_types='pad;line;arc')
            step.COM("filter_area_strt")
            step.COM("filter_area_end,filter_name=popup,operation=unselect")
            if step.featureSelected():
                log = u"{0}层钻字接触到其它COUPON,请移动到合适位置".format(drl_name)
                arraylist.append(log)
                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, drl_name, drl_name, log,
                                                                     dic_zu_layer, add_note_layer=drl_name)


            step.resetFilter()
            step.selectNone()
            step.filter_set(feat_types='text')
            if drl_name in mai_man_drill_layers + mai_drill_layers:
                step.refSelectFilter(refLay=tmpLayers['inner'])
            else:
                step.refSelectFilter(refLay=tmpLayers['outer'])
            if step.featureSelected():
                log = u"{0}层钻字接触到其它层物件,请移动到合适位置".format(drl_name)
                arraylist.append(log)
                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, drl_name, drl_name, log, dic_zu_layer, add_note_layer=drl_name)

        step.clearAll()
        for layer in tmpLayers.values():
            if 'ynh' not in jobname:
                step.removeLayer(layer)

        if arraylist:
            return arraylist, dic_zu_layer

        return "success", None

    def check_sklp_hole_space(self):
        """
        检测塞孔铝片间距 http://192.168.2.120:82/zentao/story-view-7838.html
        """
        check_type = os.environ.get("INNER_OUTER", '')
        if check_type =='coreinner' or "panel" not in matrixinfo["gCOLstep_name"]:
            return "success", None
        #获取塞孔铝片流程对应的工具名称

    def check_etch_cs_2dbc(self):
        """
        检测etch层的靶点是否和其它层如激光打码层共用靶点
        """
        arraylist = []
        dic_zu_layer = {}
        if "panel" not in matrixinfo["gCOLstep_name"]:
            return "success", None
        step = gClasses.Step(job, 'panel')
        step.open()
        step.clearAll()
        step.resetFilter()
        inplan = InPlan(jobname)
        figer_dp_positive = False
        dbc_flow = False
        inplan_etch = []
        inflow = inplan.get_inplan_all_flow()
        for d in inflow:
            if (d['PROCESS_DESCRIPTION'] == u'碱性蚀刻') and (d['WORK_CENTER_CODE'] and u'金手指去导线' in d['WORK_CENTER_CODE'].decode("utf8")):
                figer_dp_positive = True

            if (d['WORK_CENTER_CODE'] and u'金手指去导线图形' in d['WORK_CENTER_CODE'].decode("utf8")) \
                    and (d['WORK_DESCRIPTION'] and u'使用曝光资料' in d['WORK_DESCRIPTION'].decode("utf8")):
                    figer_etch_value = str(d['VALUE_AS_STRING']).strip()
                    if '，' in figer_etch_value:
                        inplan_etch = [i.strip() for i in figer_etch_value.split('，')]
                    else:
                        inplan_etch = [i.strip() for i in figer_etch_value.split(',')]

            elif d['WORK_CENTER_CODE'] and u'激光打标' in d['WORK_CENTER_CODE'].decode("utf8"):
                dbc_flow = True
        if figer_dp_positive and dbc_flow:
            pass
        else:
            return "success", None
        etch_c, etch_s = '', ''
        if inplan_etch:
            for lay in inplan_etch:
                if step.isLayer(lay):
                    if 'etch-c' in lay:
                        etch_c = lay
                    elif 'etch-s' in lay:
                        etch_s = lay
        else:
            if step.isLayer('etch-c'):
                etch_c = 'etch-c'
            if step.isLayer('etch-s'):
                etch_s = 'etch-s'
        if not etch_c and not etch_s:
            return u"资料中未发现蚀刻引线层，请检查命名是否为etch-c/etch-s", None
        for lay in [etch_c, etch_s]:
            if not lay:
                continue
            check_layer = []
            if lay == etch_c:
                if step.isLayer('2dbc-c'):
                    check_layer.append('2dbc-c')
            else:
                if step.isLayer('2dbc-s'):
                    check_layer.append('2dbc-s')
            step.clearAll()
            step.resetFilter()
            step.filter_set(include_syms='sh-dwsig2014')
            step.affect(lay)
            step.refSelectFilter(refLay=','.join(check_layer), f_types='pad')
            if step.featureSelected():
                log = u"{0}层靶点和后工序的其它物件接触，请检查".format(lay)
                arraylist.append(log)
                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, lay, [lay]+check_layer, log,
                                                                     dic_zu_layer, add_note_layer=lay)
            step.clearAll()
            step.resetFilter()

        if arraylist:
            return arraylist, dic_zu_layer

        return "success", None

    def check_sgt_cs_disgin(self):
        """检测化金加电金流程的金手指sgt-c,stg-s制作是否正确"""
        arraylist = []
        dic_zu_layer = {}
        if "panel" not in matrixinfo["gCOLstep_name"]:
            return "success", None
        step = gClasses.Step(job, 'panel')
        step.open()
        step.clearAll()
        step.resetFilter()
        inplan = InPlan(jobname)
        inflow = inplan.get_inplan_all_flow()
        mrp_info = [i for i in inflow if '-' not in i]
        nAu = False
        cAu = False
        for info in mrp_info:
            if '电镀镍金' in info['WORK_CENTER_CODE']:
                nAu = True
            elif '沉金' in info['WORK_CENTER_CODE']:
                cAu = True
        if nAu and cAu:
           pass
        else:
            return "success", None
        check_dict = {}
        for layer in outsignalLayers:
            if layer == 'l1':
                check_stg = 'sgt-c'
            else:
                check_stg = 'sgt-s'
            tmp_gf = layer + '-gf-tmp+'
            tmp_pad = layer + '-pad-tmp+'
            step.removeLayer(tmp_gf)
            step.createLayer(tmp_gf)
            step.removeLayer(tmp_pad)
            step.createLayer(tmp_pad)
            check_dict[layer] = check_stg
        step_in_panel = get_panelset_sr_step(jobname, step.name)
        for stepName in step_in_panel:
            step_pcs = gClasses.Step(job, stepName)
            step_pcs.open()
            step_pcs.COM("units,type=inch")
            step_pcs.clearAll()
            step_pcs.resetFilter()
            for lay, sgt_lay in check_dict.items():
                tmp_gf = lay + '-gf-tmp+'
                tmp_pad = lay + '-pad-tmp+'
                step_pcs.clearAll()
                step_pcs.resetFilter()
                step_pcs.affect(lay)
                step_pcs.filter_set(feat_types='pad', polarity='positive')
                step_pcs.selectAll()
                if step_pcs.featureSelected():
                    step_pcs.copyToLayer(tmp_pad)
                    step_pcs.clearAll()
                    step_pcs.resetFilter()
                    step_pcs.affect(tmp_pad)
                    # 把非开窗的部分去除
                    ref_sm = ''
                    if lay == 'l1':
                        if step_pcs.isLayer('m1'):
                            ref_sm = 'm1'
                        elif step_pcs.isLayer('m1-1'):
                            ref_sm = 'm1-1'
                    else:
                        if step_pcs.isLayer('m1'):
                            ref_sm = 'm2'
                        elif step_pcs.isLayer('m1-1'):
                            ref_sm = 'm2-1'
                    if ref_sm:
                        step_pcs.refSelectFilter(ref_sm, mode='cover')
                        step_pcs.COM("sel_reverse")
                        if step_pcs.featureSelected():
                            step_pcs.selectDelete()
                    step_pcs.COM("set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=yes,attribute=.string,text=gf")
                    step_pcs.selectAll()
                    if step_pcs.featureSelected():
                        step_pcs.moveSel(tmp_gf)
                        step_pcs.resetFilter()
                        step_pcs.clearAll()
                        step_pcs.affect(lay)
                        step_pcs.filter_set(feat_types='line', polarity='negative')
                        step_pcs.selectAll()
                        step_pcs.copyToLayer(tmp_gf)
                        step_pcs.clearAll()
                        step_pcs.resetFilter()
                        step_pcs.affect(tmp_gf)
                        step_pcs.contourize(units='inch')
                        # step_pcs.refSelectFilter(sgt_lay, mode='disjoint')
                        # if step_pcs.featureSelected():
                        #     step_pcs.selectDelete()
                        # step_pcs.selectAll()
                        # if step_pcs.featureSelected():
                        #     step_pcs.clearAll()
                        #     step_pcs.affect(lay)
                        #     step_pcs.filter_set(feat_types='pad', polarity='positive')
                        #     step_pcs.COM(
                        #         "set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=yes,attribute=.string,text=gf")
                        #     step_pcs.refSelectFilter(tmp_gf)
                        #
                        #     if step_pcs.featureSelected():
                        #         log = u"{0}层金手指不能被{1}层覆盖，请检查".format(lay, sgt_lay)
                        #         arraylist.append(log)
                        #         dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step_pcs.name, step_pcs,
                        #                                                              lay, [lay, sgt_lay], log, dic_zu_layer,
                        #                                                              add_note_layer=lay)
                        step_pcs.clearAll()
                        step_pcs.resetFilter()
                    step_pcs.clearAll()
                    step_pcs.resetFilter()
                    step_pcs.affect(lay)
                    step_pcs.filter_set(feat_types='line', polarity='negative')
                    step_pcs.selectAll()
                    if step_pcs.featureSelected():
                        step_pcs.copyToLayer(tmp_pad)
                    step_pcs.clearAll()
                    step_pcs.resetFilter()
                    step_pcs.affect(tmp_pad)
                    step_pcs.contourize(units='inch')
                    step_pcs.COM("sel_resize,size=10,corner_ctl=no")
                    # step_pcs.refSelectFilter(sgt_lay, mode='cover')
                    # if step_pcs.featureSelected():
                    #     step_pcs.selectDelete()
                    # step_pcs.clearAll()
                    # step_pcs.resetFilter()
                    # step_pcs.affect(tmp_pad)
                    # step_pcs.selectAll()
                    # if step_pcs.featureSelected():
                    #     step_pcs.clearAll()
                    #     step_pcs.resetFilter()
                    #     step_pcs.affect(lay)
                    #     step_pcs.filter_set(feat_types='pad', polarity='positive')
                    #     step_pcs.refSelectFilter(tmp_pad, mode='cover')
                    #     if step_pcs.featureSelected():
                    #         log = u"{0}层沉金PAD需要保证被{1}覆盖单边5mil以上".format(lay, sgt_lay)
                    #         arraylist.append(log)
                    #         dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step_pcs.name, step_pcs,
                    #                                                              lay, [lay, sgt_lay], log, dic_zu_layer,
                    #                                                              add_note_layer=lay)
                    step_pcs.clearAll()
                    step_pcs.resetFilter()

        step.open()
        # step.PAUSE("55")
        for lay, sgt_lay in check_dict.items():
            gf_lay_flatten = lay + '-gf-touch-sgt'
            pad_lay_flatten = lay + '-pad-notcover-sgt'
            tmp_gf = lay + '-gf-tmp+'
            tmp_pad = lay + '-pad-tmp+'
            step.removeLayer(gf_lay_flatten)
            step.removeLayer(pad_lay_flatten)
            step.flatten_layer(tmp_gf, gf_lay_flatten)
            step.flatten_layer(tmp_pad, pad_lay_flatten)
            tmp_sgt = sgt_lay + '-tmp-sgt++'
            step.flatten_layer(sgt_lay, tmp_sgt)
            step.clearAll()
            step.resetFilter()
            step.affect(tmp_sgt)
            step.COM("units,type=inch")
            step.contourize(units='inch')
            step.clearAll()
            # 删除掉gf和sgt不接触的部分
            step.affect(gf_lay_flatten)
            step.refSelectFilter(tmp_sgt, mode='disjoint')
            if step.featureSelected():
                step.selectDelete()
            step.refSelectFilter(tmp_sgt)
            if step.featureSelected():
                log = u"{0}层金手指不能被{1}层覆盖，请检查".format(lay, sgt_lay)
                arraylist.append(log)
                self.get_view_dic_layers(job.name, step.name, step,
                                         worklayer="view_layer_" + gf_lay_flatten, dic_layer_list={log: [sgt_lay]},
                                         dic_zu_layer=dic_zu_layer)

                # dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, gf_lay,
                #                                                      [gf_lay, lay, sgt_lay], log, dic_zu_layer,add_note_layer=gf_lay)
            else:
                step.removeLayer(gf_lay_flatten)
            step.clearAll()
            step.resetFilter()
            step.affect(pad_lay_flatten)
            # step.COM("units,type=inch")
            # step.COM("sel_resize,size=10,corner_ctl=no")
            step.refSelectFilter(tmp_sgt, mode='cover')
            if step.featureSelected():
                step.selectDelete()
            step.selectAll()
            if step.featureSelected():
                log = u"{0}层沉金PAD需要保证被{1}覆盖单边5mil以上".format(lay, sgt_lay)
                arraylist.append(log)
                self.get_view_dic_layers(job.name, step.name, step,
                                         worklayer="view_layer_" + pad_lay_flatten, dic_layer_list={log: [sgt_lay]},
                                         dic_zu_layer=dic_zu_layer)
                # dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, pad_lay, [pad_lay, sgt_lay], log, dic_zu_layer, add_note_layer=lay)
            else:
                step.removeLayer(pad_lay_flatten)

            step.removeLayer(tmp_gf)
            step.removeLayer(tmp_pad)

        if arraylist:
            return arraylist, dic_zu_layer

        return "success", None


    def check_gk_film(self):
        """
        检测盖孔菲林制作是否正确
        """
        arraylist = []
        dic_zu_layer = {}

        if "panel" not in matrixinfo["gCOLstep_name"]:
            return "success", None
        step = gClasses.Step(job, 'panel')
        all_layers = step.getLayers()
        gk_films = [lay for lay in all_layers if re.match('l\d{1,2}-gk$', lay)]
        if not gk_films:
            return "success", None
        tk_drl = ''
        if 'kt.ykj' in all_layers:
            tk_drl = 'kt.ykj'
        elif 'drl' in all_layers:
            tk_drl = 'drl'
        lr_layes = [lay for lay in all_layers if re.match('lr\d+-\d+$', lay)]

        res = os.environ.get("INNER_OUTER", "")

        # 获取盖孔层对应的钻孔层
        gk_dict = {}
        lay_num = int(jobname[4:6])
        for gk_lay in gk_films:
            add_drills = []
            num = int(gk_lay.replace('-gk', '').replace('l', ''))
            for laser_lay in laser_drill_layers:
                num1, num2 = laser_lay.replace('s', '').split('-')
                if int(num1) == num:
                    add_drills.append(laser_lay)
                #开料钻镭射反面也要加上
                if int(num1) == lay_num/2 and num == int(num2):
                    add_drills.append(laser_lay)
            for lay in mai_drill_layers + mai_man_drill_layers + lr_layes:
                if lay in lr_layes:
                    num1, num2 = lay.replace('lr', '').split('-')
                else:
                    num1 , num2 = lay[1:].split('-')
                if num in [int(num1), int(num2)]:
                    add_drills.append(lay)
            if num in [1, lay_num] and tk_drl:
                add_drills.append(tk_drl)
            if res <> 'outer' and num in [1, lay_num]:
                continue
            gk_dict[gk_lay] = add_drills

        if not gk_dict:
            return "success", None

        # 获取panel中所有的拼版
        step_in_panels = get_panelset_sr_step(jobname, 'panel')
        for stepname in step_in_panels:
            # 尾孔不做盖孔，排除掉、
            if stepname == 'drl' or re.match('^[bm]\d+-\d+$', stepname):
                continue
            step_cmd = gClasses.Step(job, stepname)
            step_cmd.open()
            step_cmd.resetFilter()
            step_cmd.clearAll()
            step_cmd.COM("units,type=mm")
            tmp_gk = 'check_gk_tmp+'
            comp_gk = 'check_gk_comp+'
            flt_pth = 'del_npt_gk'
            right_hole = 'gk_right_hole'
            for gklay, drill_list in gk_dict.items():
                step_cmd.resetFilter()
                step_cmd.clearAll()
                step_cmd.removeLayer(tmp_gk)
                step_cmd.createLayer(tmp_gk)
                step_cmd.removeLayer(comp_gk)
                step_cmd.createLayer(comp_gk)
                step_cmd.removeLayer(flt_pth)
                step_cmd.createLayer(flt_pth)
                step_cmd.removeLayer(right_hole)
                step_cmd.createLayer(right_hole)
                step_cmd.affect(tmp_gk)
                step_cmd.selectDelete()
                step_cmd.clearAll()
                step_cmd.affect(gklay)
                step_cmd.filter_set(feat_types='pad;line', polarity='negative')
                step_cmd.selectAll()
                if step_cmd.featureSelected():
                    step_cmd.copyToLayer(comp_gk, invert='yes')
                step_cmd.clearAll()
                step_cmd.resetFilter()
                for drl_name in drill_list:
                    if re.match('s\d+-\d+', drl_name):
                        step_cmd.clearAll()
                        step_cmd.resetFilter()
                        lay_cmd = gClasses.Layer(step_cmd, drl_name)
                        features_info = lay_cmd.featCurrent_LayerOut(units='mm')['pads']
                        symbols = list(set([obj.symbol for obj in features_info if float(obj.symbol[1:]) >= 127 and obj.symbol not in ['r515']]))
                        if symbols:
                            step_cmd.filter_set(include_syms='\\;'.join(symbols))
                            step_cmd.affect(drl_name)
                            step_cmd.selectAll()
                            if step_cmd.featureSelected():
                                step_cmd.copyToLayer(tmp_gk, size=3 * 25.4 * 2)
                    else:
                        step_cmd.copyLayer(jobname, stepname, drl_name, flt_pth)
                        step_cmd.clearAll()
                        step_cmd.resetFilter()
                        step_cmd.affect(flt_pth)
                        step_cmd.setAttrFilter(".drill,option=non_plated")
                        step_cmd.selectAll()
                        if step_cmd.featureSelected():
                            step_cmd.selectDelete()
                        lay_cmd = gClasses.Layer(step_cmd, flt_pth)
                        feat_out = lay_cmd.featCurrent_LayerOut(units="mm")["pads"]
                        feat_out += lay_cmd.featCurrent_LayerOut(units="mm")["lines"]
                        symbols1 = list(set([obj.symbol for obj in feat_out if float(obj.symbol[1:]) < 1810]))
                        symbols2 = list(set([obj.symbol for obj in feat_out if float(obj.symbol[1:]) >= 1810]))
                        if symbols1:
                            step_cmd.selectNone()
                            step_cmd.resetFilter()
                            step_cmd.filter_set(include_syms='\\;'.join(symbols1))
                            step_cmd.selectAll()

                            if step_cmd.featureSelected():
                                step_cmd.copyToLayer(tmp_gk, size=3 * 25.4 * 2)

                        if symbols2:
                            step_cmd.selectNone()
                            step_cmd.resetFilter()
                            step_cmd.filter_set(include_syms='\\;'.join(symbols2))
                            step_cmd.selectAll()
                            if step_cmd.featureSelected():
                                step_cmd.copyToLayer(tmp_gk, size=6 * 25.4 * 2)

                        step_cmd.selectNone()
                        feat_out = lay_cmd.featout_dic_Index(units="mm", options="feat_index")["lines"]
                        symbols3 = [obj for obj in feat_out if (float(obj.symbol[1:]) / 1000 + obj.len) > 1.8]

                        for obj in symbols3:
                            step_cmd.selectFeatureIndex(flt_pth, obj.feat_index)
                            if step_cmd.featureSelected():
                                step_cmd.copyToLayer(tmp_gk, size=6 * 25.4 * 2)
                step_cmd.clearAll()
                step_cmd.resetFilter()
                step_cmd.affect(flt_pth)
                step_cmd.selectDelete()
                step_cmd.clearAll()

                if 'ynh' in jobname and 'edit' in step_cmd.name:
                    step_cmd.PAUSE(step_cmd.name)
                step_cmd.affect(comp_gk)
                step_cmd.refSelectFilter(tmp_gk, mode='cover')
                if step_cmd.featureSelected():
                    step_cmd.moveSel(flt_pth)
                step_cmd.clearAll()
                step_cmd.affect(flt_pth)
                step_cmd.refSelectFilter(tmp_gk, mode='include')
                # 这里面是正确的孔
                if step_cmd.featureSelected():
                    step_cmd.moveSel(right_hole)
                step_cmd.selectAll()
                if step_cmd.featureSelected():
                    step_cmd.moveSel(comp_gk)
                step_cmd.clearAll()
                # 然后把gk层的孔和正确的比对
                step_cmd.affect(tmp_gk)
                step_cmd.refSelectFilter(right_hole, mode='disjoint')
                if step_cmd.featureSelected():
                    step_cmd.copyToLayer(comp_gk)
                step_cmd.clearAll()
                step_cmd.affect(comp_gk)
                step_cmd.selectAll()
                if step_cmd.featureSelected():
                    for lay1 in drill_list:
                        step_cmd.clearAll()
                        step_cmd.affect(lay1)
                        step_cmd.refSelectFilter(comp_gk)
                        if step_cmd.featureSelected():
                            log = u"{0} 中{1}层盖孔制作有误，请查看标记位置".format(step_cmd.name, gklay)
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step_cmd.name, step_cmd,
                                                                                 lay1, gklay, log, dic_zu_layer, add_note_layer=lay1)
                step_cmd.clearAll()
                step_cmd.resetFilter()
            step_cmd.removeLayer(tmp_gk)
            step_cmd.removeLayer(comp_gk)
            step_cmd.removeLayer(flt_pth)
            step_cmd.removeLayer(right_hole)
            step_cmd.close()

        if arraylist:
            return arraylist, dic_zu_layer
        return "success", None


    def check_rout_fd_pin(self):
        """
        检测锣板防呆孔防呆间距是否足够
        """
        arraylist = []
        dic_zu_layer = {}
        if "panel" not in matrixinfo["gCOLstep_name"]:
            return "success", None
        stepname = "panel"
        step = gClasses.Step(job, stepname)
        step.open()
        step.clearAll()
        step.resetFilter()
        # 确定要检测的钻孔层
        board_drills = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                              if matrixInfo["gROWcontext"][i] == "board"
                              and matrixInfo["gROWlayer_type"][i] == "drill"]

        if 'drl' in board_drills:
            check_drill = 'drl'
        elif 'cdc' in board_drills:
            check_drill = 'cdc'
        elif 'cds' in board_drills:
            check_drill = 'cds'
        else:
            return "success", None

        # features = lay_cmd.featout_dic_Index(units='mm', options="feat_index")['pads']
        info_lines = step.INFO("-t layer -e %s/panel/%s -d FEATURES -o feat_index, units=mm" % (jobname, check_drill))
        features_fdk, features_3175 = [], []
        for line in info_lines:
            #2903 #P 91.5021 69.8582375 r554 P 14 0 N;.bit=slot_pre_hole,.drill=non_plated
            # if not line.startswith("#P"):
            if "#P" not in line:
                continue
                
            split_line = line.strip().split('#P')
            line_index = split_line[0].strip().replace('#','')
            #91.5021 69.8582375 r554 P 14 0 N;.bit=slot_pre_hole,.drill=non_plated
            line_list = split_line[1].strip().split()
            tuple_info = (float(line_list[0]), float(line_list[1]), line_index)
            if 'rout_fd_fxk' in line:
                features_fdk.append(tuple_info)
            elif line_list[2] in ['r3175', 'r3176']:
                features_3175.append(tuple_info)

        # print features_fdk, features_3175

        if not features_fdk:
            return "success", None
        if len(features_fdk) > 1:
            log = u"{0}中添加了{1}个锣板防呆孔（限添加1个），请检查是否多加或是属性不正确（防呆孔属性:rout_fd_fxk）！".format(check_drill, step.featureSelected())
            arraylist.append(log)
        else:
            fdk_x, fdk_y, fdk_index = features_fdk[0]
            # 获取profile中心
            pf = step.getProfile()
            pf_xcent, pf_ycent = pf.xcenter * 25.4, pf.ycenter * 25.4

            long_x = fdk_x - pf_xcent
            long_y = fdk_y - pf_ycent

            if features_3175:
                for check_type in ['180度旋转', 'X轴镜像', 'Y轴镜像']:
                    if check_type == 'Y轴镜像':
                        fdk_change_x = fdk_x - long_x * 2
                        fdk_change_y = fdk_y

                    elif check_type == 'X轴镜像':
                        fdk_change_x = fdk_x
                        fdk_change_y = fdk_y - long_y * 2

                    else:
                        fdk_change_x = fdk_x - long_x * 2
                        fdk_change_y = fdk_y - long_y * 2

                    for i in features_3175:
                        if abs(fdk_change_x - i[0]) < 3.175 and abs(fdk_change_y - i[1]) < 3.175:
                            log = u"锣板防呆孔在{0}后防呆间距小于3.175MM".format(check_type)
                            arraylist.append(log)
                            step.clearAll()
                            step.affect(check_drill)
                            step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(check_drill, i[2]))
                            step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(check_drill, fdk_index))
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, check_drill, check_drill, log, dic_zu_layer,                                                add_note_layer=check_drill)
                            break

        step.clearAll()
        if arraylist:
            return arraylist, dic_zu_layer

        return "success", None

    def job_foolproof_detection(self, check_type=None):
        """
        单板防呆检测
        """

        if not check_type:
            try:
                res = os.environ.get("INNER_OUTER", "")
            except:
                res = 'all'
        else:
            res = check_type

        # res = 'all'  # 周涌通知全部项目都要内外层检测
        arraylist = []
        dic_zu_layer = {}
        update_current_job_check_log(os.environ.get("CHECK_ID", "NULL"),
                                     u"forbid_or_information='{0}'".format(u"拦截"))
        # 检测5代靶, ccd, dld钻孔等
        #laser_bar --镭射对位孔
        checklist = ['v5bar', 'drl_ccd', 'dld', 'by_bar',
                     'laser_bar', 'bd_drl', '2nd_cd_inn',
                     'cm_dw', 'lr_laser', 'outer' ,'bs']
        for check in checklist:
            if check == 'v5bar':
                arr, dic = self.check_v5laser_targe('all', dic_zu_layer)
            elif check == 'drl_ccd':
                arr, dic = self.check_fxk_targe('all', dic_zu_layer)
            elif check == 'dld':
                arr, dic = self.check_dld_targe(dic_zu_layer)
            elif check == 'by_bar':
                arr, dic = self.check_bybar('all',dic_zu_layer)
            elif check == 'laser_bar':
                arr, dic = self.check_laser_targe(dic_zu_layer)
            # elif check == 'bd_drl':
            #     arr, dic = self.check_bd_drl_targe(res)
            elif check == '2nd_cd_inn':
                arr, dic = self.check_2ndcd_inn_targe('all',dic_zu_layer)
            elif check == 'cm_dw':
                arr, dic = self.check_pnl_rout_targe(dic_zu_layer)
            elif check == 'lr_laser':
                arr, dic = self.check_lrlaser_pin_targe('all', dic_zu_layer)
            elif check == 'outer':
                arr, dic = self.check_outer_layer_targe(res, dic_zu_layer)

            if arr != 'success':
                arraylist += arr
                dic_zu_layer = dic

        if arraylist:
            # showMessageInfo(*(arraylist))
            return list(set(arraylist)), dic_zu_layer

        return "success", None

    def check_outer_layer_targe(self, type='all', dic = {}):
        """
        检测外层，阻焊，字符，选化等菲林对位PAD是否防呆
        线路选化CCD sh-dwsig2014 ,阻焊字符CCD sh-dwsd2014 文字网印 sh-fxpad
        内层镀孔l1-dk , sh-dwtop2013 sh-dwbot2013
        """
        arraylist = []
        dic_zu_layer = dic
        out_check = outsignalLayers + solderMaskLayers + silkscreenLayers
        if "panel" not in matrixinfo["gCOLstep_name"]:
            return "success", None
        step = gClasses.Step(job, 'panel')
        dk_outers = [lay for lay in step.getLayers() if
                     re.search('^l\d+-dk$|^l\d+-gk$', lay) and lay.split('-')[0] in outsignalLayers]
        dk_inners = [lay for lay in step.getLayers() if
                     re.search('^l\d+-dk$|^l\d+-gk$', lay) and lay.split('-')[0] in innersignalLayers]
        sgt_layers = ['stg-c', 'stg-s']
        gold_layers = ['gold-c', 'gold-s']
        xlym_layers = ['xlym-c', 'xlym-s']
        md_layers = ['md1', 'md2']
        out_check = sgt_layers + gold_layers + dk_outers + out_check + md_layers + xlym_layers
        step.open()

        if type == 'coreinner':
            info_layer = 'l2'
            checklist = dk_inners
        else:
            info_layer = 'l1'
            checklist = out_check + dk_inners

        # if type == 'outer':
        #     info_layer = 'l1'
        #     checklist =  out_check
        # elif type == 'inner':
        #     info_layer = 'l2'
        #     checklist = dk_inners
        # else:
        #     info_layer = 'l1'
        #     checklist = out_check + dk_inners
        # 考虑到分割靶，从角线标记获取sr的范围
        # 用角线来确定sr区域角线有两类 sh-con,sh-con2
        info = step.INFO("-t layer -e %s/%s/%s  -d FEATURES" % (jobname, step.name, info_layer))
        lines = [gFeatures.Pad(line) for line in info if 'sh-con2' in line or 'sh-con' in line]
        if lines:
            feax = [fea.x * 25.4 for fea in lines]
            feay = [fea.y * 25.4 for fea in lines]
            sr_xmin, sr_ymin, sr_xmax, sr_ymax = min(feax) + 1, min(feay) + 1, max(feax) - 1, max(feay) - 1
        for layer in checklist:
            if not step.isLayer(layer):
                continue
            step.clearAll()
            step.resetFilter()
            step.affect(layer)
            step.filter_set(feat_types='pad')
            # 判断是否分割型号
            fg_type = False
            step.COM("set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=yes,attribute=.string,text=split_panel")
            step.selectAll()
            if step.featureSelected():
                fg_type = True
            step.clearAll()
            step.resetFilter()
            step.filter_set(feat_types='pad')
            step.affect(layer)
            step.COM("set_filter_attributes,filter_name=popup,exclude_attributes=yes,condition=yes,attribute=.string,text=split_panel")
            step.selectAll()
            # if 'ynh' in jobname:
            #     step.PAUSE("11")
            lay_cmd = gClasses.Layer(step, layer)
            features = lay_cmd.featout_dic_Index(options='feat_index+select', units='mm')['pads']
            step.resetFilter()
            # 第一部分检测CCD对位PAD
            if layer  in outsignalLayers + sgt_layers + gold_layers + solderMaskLayers + silkscreenLayers and lines:
                if layer in outsignalLayers + sgt_layers + gold_layers:
                    sym = ['sh-dwsig2014']
                else:
                    sym = ['sh-dwsd2014']
                check_list = []
                features_sel = [obj for obj in features if obj.symbol in sym]

                if features_sel:
                    step.clearAll()
                    step.resetFilter()
                    step.affect(layer)
                    for obj in features_sel:
                        step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(layer, obj.feat_index))

                if not features_sel:
                    log = u'{0}层对位PAD数量为0'.format(layer)
                    arraylist.append(log)
                elif len(features_sel) < 4:
                    log = u'{0}层对位PAD数量少于4颗'.format(layer)
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer, layer, log, dic_zu_layer, add_note_layer=layer)


                # if len(features_sel) > 4 and layer in  outsignalLayers + sgt_layers + solderMaskLayers + silkscreenLayers + gold_layers:
                #     features_short = [obj for obj in features_sel if obj.y > sr_ymax or obj.y < sr_ymin]
                features_short, features_long = [], []
                if len(features_sel) > 4:
                    features_short = [obj for obj in features_sel if obj.y > sr_ymax or obj.y < sr_ymin]
                    features_long = [obj for obj in features_sel if obj.x > sr_xmax or obj.x < sr_xmin]
                    if not features_short and len(features_long) == 4:
                        features_short = [obj for obj in features_sel if sr_xmin < obj.x < sr_xmax]
                    if not features_long and len(features_short) == 4:
                        features_long = [obj for obj in features_sel if sr_ymin < obj.y < sr_ymax]

                    check_list.append(features_short)
                    if not fg_type:
                        check_list.append(features_long)

                elif len(features_sel) == 4:
                    check_list.append(features_sel)

                for features_sel in check_list:
                    show_text = 'CCD靶'
                    if len(check_list) == 2:
                        if features_sel == features_short:
                            show_text = '短边CCD靶'
                        else:
                            show_text = '长边CCD靶'

                    if features_sel:
                        step.clearAll()
                        step.resetFilter()
                        step.affect(layer)
                        for obj in features_sel:
                            step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(layer, obj.feat_index))

                    if not features_sel:
                        log = u'{0}层{1}数量为0'.format(layer, show_text)
                        arraylist.append(log)
                    elif len(features_sel) < 4:
                        log = u'{0}层{1}数量少于4颗，请检查长短边靶标添加的区域是否不符合规则，造成冲突'.format(layer, show_text)
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                             layer, log, dic_zu_layer,
                                                                             add_note_layer=layer)
                    else:
                        # 检查防呆，右上角防呆
                        # 检测是否防呆1mm以上 ,右上角防呆
                        features_dict = self.get_fea_point(features_sel)
                        get_point_rect, show_warning = self.get_point_rect_type(features_dict, check_fd=True)
                        if show_warning:
                            log = u"{0}层{1}".format(layer, show_text) + show_warning
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                                 layer, log, dic_zu_layer,
                                                                                 add_note_layer=layer)
                        else:
                            # 判断是否右上角防呆
                            show_1mm, show_1um = self.set_fd_space_1mm('3', get_point_rect)
                            if show_1mm:
                                log = u"{0}层{1}".format(layer, show_text) + show_1mm
                                arraylist.append(log)
                                step.clearAll()
                                step.resetFilter()
                                step.affect(layer)
                                for obj in features_sel:
                                    step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(layer,obj.feat_index))
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                                     layer, log, dic_zu_layer,
                                                                                     add_note_layer=layer)

                            if show_1um:
                                log = u"{0}层{1}".format(layer, show_text) + show_1um
                                arraylist.append(log)
                                step.clearAll()
                                step.resetFilter()
                                step.affect(layer)
                                for obj in features_sel:
                                    step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(layer, obj.feat_index))
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                                     layer, log, dic_zu_layer,
                                                                                     add_note_layer=layer)


            if layer in dk_inners + dk_outers:
                # 检测镀孔层
                sym = ['sh-dwtop2013', 'sh-dwbot2013']
                features_sel = [obj for obj in features if obj.symbol in sym]

                if not features_sel:
                    log = u'{0}层对位PAD数量为0'.format(layer)
                    arraylist.append(log)
                else:
                    step.clearAll()
                    step.resetFilter()
                    step.affect(layer)
                    step.filter_set(include_syms='\\;'.join(sym))
                    step.selectAll()
                    if step.featureSelected() != 4:
                        log = u'{0}层对位PAD数量不等于4颗'.format(layer)
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                             tongkongDrillLayer, log, dic_zu_layer,add_note_layer=layer)
                    else:
                        features_dict = self.get_fea_point(features_sel)
                        # 检测是否防呆1mm以上, 左下角防呆
                        get_point_rect, show_warning = self.get_point_rect_type(features_dict, check_fd=True)
                        if show_warning:
                            log = u"{0}对位孔".format(layer) + show_warning
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                                 layer, log, dic_zu_layer,
                                                                                 add_note_layer=layer)

                        else:
                            # 判断是否有任意防呆距离大于1mm
                            show_1mm, show_1um = self.set_fd_space_1mm('1', get_point_rect)
                            # 判断是否左下角防呆
                            if show_1mm:
                                log = u"{0}对位孔".format(layer) + show_1mm
                                arraylist.append(log)
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer, layer, log, dic_zu_layer,add_note_layer=layer)
                            if show_1um:
                                log = u"{0}对位孔".format(layer) + show_1um
                                arraylist.append(log)
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer, layer, log, dic_zu_layer,add_note_layer=layer)

                        # 检测是否和孔中心对齐
                        ref_drill = ''
                        if layer in dk_outers:
                            ref_drill = 'inn'
                        else:
                            num = layer.split('-')[0].replace('l', '')
                            for lay in step.getLayers():
                                if re.search('^inn\d+$', lay):
                                    num_re = lay.replace('inn', '')
                                    if len(num_re) == 2:
                                        f_num, t_num = num_re[0], num_re[1:]
                                    elif len(num_re) == 3:
                                        f_num, t_num = num_re[0], num_re[1:]
                                    else:
                                        f_num, t_num = num_re[0:2], num_re[2:]
                                    if num in [f_num, t_num]:
                                        ref_drill = lay

                        if ref_drill:
                            step.selectNone()
                            step.refSelectFilter(ref_drill)
                            if step.featureSelected() != 4:
                                log = u'{0}层对位PAD和{1}层孔不在同一中心'.format(layer, ref_drill)
                                arraylist.append(log)
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step,layer, ref_drill, log,dic_zu_layer, add_note_layer=layer)

            # 检测文字层加md1,md2
            if layer in silkscreenLayers + ['md1', 'md2']:
                features_sel = [obj for obj in features if obj.symbol =='sh-fxpad']
                step.clearAll()
                step.resetFilter()
                if len(features_sel) == 0 and layer in silkscreenLayers:
                    continue
                if len(features_sel) == 0 and layer in ['md1', 'md2']:
                    log = u'{0}层对位PAD数量为0'.format(layer)
                    arraylist.append(log)
                else:
                    step.affect(layer)
                    step.filter_set(include_syms='sh-fxpad')

                    tk_drls = []
                    for dname in ['cdc', 'cds', 'drl']:
                        if step.isLayer(dname):
                            tk_drls.append(dname)

                    step.refSelectFilter('\\;'.join(tk_drls), mode='include')
                    if step.featureSelected() < 5:
                        log = u'{0}层对位PAD少于5颗'.format(layer)
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                             tk_drls, log, dic_zu_layer, add_note_layer=layer)
                    else:
                        #  最外围不防呆
                        features_dict = self.get_fea_point(features_sel)
                        point_4space, show_warning = self.get_point_rect_type(features_dict)
                        more_than_1um = [i for i in point_4space.values() if i > 0.01]
                        # 工具孔（方向孔）不防呆
                        if more_than_1um:
                            log = u"{0}层方向孔四角未在水平直线上".format(layer)
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                                 layer, log, dic_zu_layer, add_note_layer=layer)
            step.clearAll()
            step.resetFilter()
        if arraylist:
            # showMessageInfo(*(arraylist))
            return arraylist, dic_zu_layer
        else:
            return "success", None

    def check_lrlaser_pin_targe(self, type='all', dic = {}):
        """
        检测开料钻镭射孔定位孔和对位孔
        """
        arraylist = []
        dic_zu_layer = dic
        if "panel" not in matrixinfo["gCOLstep_name"]:
            return "success", None
        step = gClasses.Step(job, 'panel')
        check_layers = []
        inn_check = []
        out_check = []
        for layer in step.getLayers():
            regx = '^lr(\d+)-(\d+)$'
            res =  re.search(regx, layer)
            if res:
                check_layers.append(layer)
                num1,num2 = res.groups()
                if int(num1) in [1 , int(jobname[4:6])]:
                    out_check.append(layer)
                else:
                    inn_check.append(layer)
        if type == 'inner':
            check_list = inn_check
        elif type == 'outer':
            check_list = out_check
        else:
            check_list = check_layers
        if not check_list:
            return "success", None
        step.open()
        step.clearAll()
        step.resetFilter()
        step.COM("units,type=mm")
        for layer in check_list:
            ref_layer = 'l{0}'.format(layer.replace('lr','').split('-')[0])
            step.affect(layer)
            step.filter_set(include_syms='r3175')
            step.refSelectFilter(ref_layer, mode='cover', include_syms='sh-dwtop2013\;sh-dwbot2013')
            #  工具孔不设防呆
            if not step.featureSelected():
                log = u"{0}层工具孔数量为0".format(layer)
                arraylist.append(log)
            elif step.featureSelected() < 5:
                log = u"{0}层工具孔数量不等于5颗,请检查和{1}层对应symbol:(sh-dwtop2023\;sh-dwbot2023)是否在同一中心".format(layer,ref_layer)
                arraylist.append(log)
                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                     ref_layer, log, dic_zu_layer, add_note_layer=layer)
            else:
                lay_cmd = gClasses.Layer(step, layer)
                features = lay_cmd.featSelOut(units='mm')['pads']
                features_dict = self.get_fea_point(features)
                point_4space, show_warning = self.get_point_rect_type(features_dict)
                more_than_1um = [i for i in point_4space.values() if i > 0.01]
                # 工具孔（方向孔）不防呆
                if more_than_1um:
                    log = u"{0}层工具孔四角未在水平直线上".format(layer)
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                         layer, log, dic_zu_layer,
                                                                         add_note_layer=layer)
             #  检测对位孔，左下角防呆
            step.clearAll()
            step.resetFilter()
            step.affect(layer)
            step.filter_set(include_syms='r3175')
            step.refSelectFilter(ref_layer, mode='cover', include_syms='sh-dwtop2023\;sh-dwbot2023')
            if not step.featureSelected():
                log = u"{0}层对位孔数量为0".format(layer)
                arraylist.append(log)
            elif step.featureSelected() < 4:
                log = u"{0}层对位孔数量不等于4颗，请检查和{1}层对应symbol:(sh-dwtop2023\;sh-dwbot2023)是否在同一中心 ".format(layer, ref_layer)
                arraylist.append(log)
                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                     ref_layer, log, dic_zu_layer, add_note_layer=layer)
            else:
                lay_cmd = gClasses.Layer(step, layer)
                features = lay_cmd.featSelOut(units='mm')['pads']
                features_dict = self.get_fea_point(features)
                # 检测是否防呆1mm以上, 左下角防呆
                # get_point_rect = self.get_point_rect_type(features_dict)
                get_point_rect, show_warning = self.get_point_rect_type(features_dict, check_fd=True)
                if show_warning:
                    log = u"{0}对位孔".format(layer) + show_warning
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                         layer, log, dic_zu_layer,
                                                                         add_note_layer=layer)
                else:
                    # 判断是否有任意防呆距离大于1mm
                    show_1mm, show_1um = self.set_fd_space_1mm('1', get_point_rect)
                    # 判断是否左下角防呆
                    if show_1mm:
                        log = u"{0}对位孔".format(layer) + show_1mm
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                             layer, log, dic_zu_layer,
                                                                             add_note_layer=layer)
                    if show_1um:
                        log = u"{0}对位孔".format(layer) + show_1um
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                             layer, log, dic_zu_layer,
                                                                             add_note_layer=layer)
                    # 判断是否有任意防呆距离大于1mm
                    show_1mm, show_1um = self.set_fd_space_1mm('1', get_point_rect)
                    # 判断是否左下角防呆
                    if show_1mm:
                        log = u"{0}对位孔".format(layer) + show_1mm
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                             layer, log, dic_zu_layer,
                                                                             add_note_layer=layer)
                    if show_1um:
                        log = u"{0}对位孔".format(layer) + show_1um
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                             layer, log, dic_zu_layer,
                                                                             add_note_layer=layer)
        if arraylist:
            return arraylist,dic_zu_layer

        return "success", None



    def check_pnl_rout_targe(self, dic = {}):
        """
        检测裁磨对位孔是否呈L形状
        """
        arraylist = []
        dic_zu_layer = dic
        if "panel" not in matrixinfo["gCOLstep_name"]:
            return "success", None
        step = gClasses.Step(job, 'panel')
        check_layers = [layer for layer in step.getLayers() if re.search('^pnl_rout\d$', layer)]
        step.open()
        step.COM("units,type=mm")
        pro = step.getProfile()
        pro_centx, pro_centy = pro.xcenter * 25.4, pro.ycenter * 25.4
        for layer in check_layers:
            step.clearAll()
            step.resetFilter()
            step.affect(layer)
            step.filter_set(include_syms='r3125')
            step.selectAll()
            if not step.featureSelected():
                log = u"{0}层靶孔数量不等于3".format(layer)
                arraylist.append(log)
            elif step.featureSelected() < 3:
                log = u"{0}层靶孔数量不等于3".format(layer)
                arraylist.append(log)
                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                     layer, log, dic_zu_layer, add_note_layer=layer)
            else:
                # 检测3孔要是否呈L型 ,下方为1，上轴为2，左边防呆为3 ，1-2 Y方向直线，2-3X方向直线
                lay_cmd = gClasses.Layer(step, layer)
                features = lay_cmd.featSelOut(units='mm')['pads']
                min_x = min([obj.x for obj in features if obj.y > pro_centy])
                min_y = min([obj.y for obj in features if obj.y < pro_centy])
                for obj in features:
                    if obj.y < pro_centx:
                        if obj.y == min_y:
                            pin_x1, pin_y1 = obj.x, obj.y
                    else:
                        if obj.x == min_x:
                            pin_x3, pin_y3 = obj.x, obj.y
                        else:
                            pin_x2, pin_y2 = obj.x, obj.y
                if pin_x2 - pin_x1 > 0.01 or pin_y3 - pin_y2 > 0.01:
                    log = u"{0}层pin孔不在水平线上".format(layer)
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                         layer, log, dic_zu_layer,
                                                                         add_note_layer=layer)
        step.clearAll()
        step.resetFilter()
        if arraylist:
            return arraylist ,dic_zu_layer
        else:
            return "success", None

    def check_2ndcd_inn_targe(self, type='all', dic = {}):
        """
        检测2钻,cdc, cds 定位孔inn 左下角防呆
        """
        arraylist = []
        dic_zu_layer = dic
        if type == 'inner' or "panel" not in matrixinfo["gCOLstep_name"]:
            return "success", None
        step = gClasses.Step(job, 'panel')
        inn_check = ['2nd.inn', 'cdc.inn', 'cds.inn', 'bdc_ccd.inn', 'bds_ccd.inn']
        for inn_layer in inn_check:
            if step.isLayer(inn_layer):
                step.clearAll()
                step.resetFilter()
                step.affect(inn_layer)
                step.selectAll()
                if not step.featureSelected():
                    log = u"{0}层定位孔数量不等于4".format(inn_layer)
                    arraylist.append(log)

                elif step.featureSelected() != 4:
                    log = u"{0}层定位孔数量不等于4".format(inn_layer)
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, inn_layer,
                                                                         inn_layer, log, dic_zu_layer,
                                                                         add_note_layer=inn_layer)
                else:
                    lay_cmd = gClasses.Layer(step, inn_layer)
                    features = lay_cmd.featSelOut(units='mm')['pads']
                    features_dict = self.get_fea_point(features)
                    # 检测是否防呆1mm以上, 左下角防呆
                    get_point_rect, show_warning = self.get_point_rect_type(features_dict, check_fd=True)
                    if show_warning:
                        log = u"{0}定位孔".format(inn_layer) + show_warning
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, inn_layer,
                                                                             inn_layer, log, dic_zu_layer,
                                                                             add_note_layer=inn_layer)
                    else:
                        # 判断是否有任意防呆距离大于1mm
                        show_1mm, show_1um = self.set_fd_space_1mm('1', get_point_rect)
                        # 判断是否左下角防呆
                        if show_1mm:
                            log = u"{0}定位孔".format(inn_layer) + show_1mm
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, inn_layer,
                                                                                 inn_layer, log, dic_zu_layer,
                                                                                 add_note_layer=inn_layer)
                        if show_1um:
                            log = u"{0}定位孔".format(inn_layer) + show_1um
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, inn_layer,
                                                                                 inn_layer, log, dic_zu_layer,
                                                                                 add_note_layer=inn_layer)
        step.clearAll()
        step.resetFilter()
        if arraylist:
            return arraylist, dic_zu_layer
        else:
            return "success", None

    def check_bd_dill_targe(self, type='all'):
        """
        检测背钻定位孔是否正确
        """
        arraylist = []
        dic_zu_layer = {}
        inn_bd = []
        out_bd = []
        for bd in bd_drillLayer:
            if re.search('bd\d+-\d+', bd):
                if str(bd).replace('bd', '').split('-')[0] not in ['1', str(int(jobname[4:6]))]:
                    inn_bd.append(bd)
                else:
                    out_bd.append(bd)
            else:
                out_bd.append(bd)
        if type == 'inner':
            check_list = inn_bd
        elif type == 'outer':
            check_list = out_bd
        else:
            check_list = bd_drillLayer

        if not "panel" in matrixinfo["gCOLstep_name"] or check_list:
            return "success", None
        step = gClasses.Step(job,'panel')
        step.open()
        step.clearAll()
        step.resetFilter()

    def check_laser_targe(self, dic = {}):
        """
        检测镭射层对位孔是否防呆,同步检测线路层对位标靶
        """
        arraylist = []
        dic_zu_layer = dic
        if not "panel" in matrixinfo["gCOLstep_name"]:
            return "success", None
        stepName = 'panel'
        step = gClasses.Step(job, stepName)
        step.open()
        step.COM("units,type=mm")
        step.clearAll()
        step.resetFilter()
        for laser in laser_drill_layers:
            num1, num2 = laser.replace('s', '').split('-')
            if int(num1) > int(num2):
                ref_signal = 'l{0}'.format(int(num1) - 1)
            else:
                ref_signal = 'l{0}'.format(int(num1) + 1)
            step.clearAll()
            step.resetFilter()
            step.affect(laser)
            step.filter_set(include_syms='r3175')
            step.refSelectFilter(ref_signal,include_syms='hdi1-ba*\;hdi1-bs*\;sh-dw*')
            if step.featureSelected() != 4:
                log = u"{0}层镭射对位孔数量不等于4,请检查和{1}层对应symbol:(hdi1-ba*\;hdi1-bs*\;sh-dw*)是否在同一中心".format(laser,ref_signal )
                arraylist.append(log)
                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, laser,
                                                                     ref_signal, log, dic_zu_layer,add_note_layer=laser)
            else:
                lay_cmd = gClasses.Layer(step, laser)
                features = lay_cmd.featSelOut(units='mm')['pads']
                features_dict = self.get_fea_point(features)
                # 检测是否防呆1mm以上, 左下角防呆
                # get_point_rect = self.get_point_rect_type(features_dict)
                get_point_rect, show_warning = self.get_point_rect_type(features_dict, check_fd=True)
                if show_warning:
                    log = u"{0}层镭射对位孔".format(laser) + show_warning
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, laser,
                                                                         laser, log, dic_zu_layer,
                                                                         add_note_layer=laser)
                else:
                    # 判断是否有任意防呆距离大于1mm
                    show_1mm, show_1um = self.set_fd_space_1mm('1', get_point_rect)
                    # 判断是否左下角防呆
                    if show_1mm:
                        log = u"{0}层镭射对位孔".format(laser) + show_1mm
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, laser,
                                                                             laser, log, dic_zu_layer,
                                                                             add_note_layer=laser)
                    if show_1um:
                        log = u"{0}层镭射对位孔".format(laser) + show_1um
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, laser,
                                                                             laser, log, dic_zu_layer,
                                                                             add_note_layer=laser)
        step.clearAll()
        step.resetFilter()
        if arraylist:
            return arraylist, dic_zu_layer
        return "success", None

    def check_bybar(self,type='all', dic = {}):
        """
        检测备用靶,及TT靶，22靶之类的是否防呆
        """
        if type == 'inner':
            check_list = innersignalLayers
        elif type == 'outer':
            check_list = outsignalLayers
        else:
            check_list = innersignalLayers + outsignalLayers
        arraylist = []

        dic_zu_layer = dic
        if not "panel" in matrixinfo["gCOLstep_name"]:
            return "success", None
        step = gClasses.Step(job, 'panel')
        pro = step.getProfile()
        pro_centx, pro_centy = pro.xcenter * 25.4, pro.ycenter * 25.4
        step.open()
        step.clearAll()
        step.resetFilter()
        for layer in check_list:
            lay_cmd = gClasses.Layer(step, layer)
            step.clearAll()
            step.resetFilter()
            step.affect(layer)
            step.filter_set(include_syms='hdi1-ba*')
            step.selectAll()
            if step.featureSelected() == 7:
                # 排除板角4颗
                bar_3 = []
                features = lay_cmd.featout_dic_Index(options='feat_index+select', units='mm')['pads']
                feaxs_top = [obj.x for obj in features if obj.y > pro_centy]
                feaxs_bot = [obj.x for obj in features if obj.y < pro_centy]
                for obj in features:
                    if obj.x not in [min(feaxs_top), min(feaxs_bot),max(feaxs_top), max(feaxs_bot)]:
                        bar_3.append(obj)
                min_x = min([obj.x for obj in bar_3 if obj.y > pro_centy])
                min_y = min([obj.y for obj in bar_3 if obj.y < pro_centy])
                for obj in bar_3:
                    if obj.y < pro_centx:
                        if obj.y == min_y:
                            pin_x1, pin_y1 = obj.x, obj.y
                    else:
                        if obj.x == min_x:
                            pin_x3, pin_y3 = obj.x, obj.y
                        else:
                            pin_x2, pin_y2 = obj.x, obj.y
                if pin_x2 - pin_x1 > 0.01 or pin_y3 - pin_y2 > 0.01:
                    step.clearAll()
                    step.affect(layer)
                    for obj in bar_3:
                        step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(layer, obj.feat_index))
                    log = u"{0}层裁磨靶孔不在水平线上".format(layer)
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                         layer, log, dic_zu_layer,
                                                                         add_note_layer=layer)


            for symstr in ['hdi1-by*', 'hdi1-bs*']:
                step.clearAll()
                step.resetFilter()
                step.affect(layer)
                step.filter_set(include_syms = symstr)
                step.selectAll()
                if symstr == 'hdi1-by*':
                    showlog = u"{0}层备用靶".format(layer)
                    num = 4
                else:
                    showlog = u"{0}层外四靶(TT/11/22靶...)".format(layer)
                    num = 4
                if step.featureSelected():
                    if step.featureSelected() < num:
                        log = u"{0}小于{1}".format(showlog, num)
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                             layer, log, dic_zu_layer,
                                                                             add_note_layer=layer)
                    else:
                        features = lay_cmd.featSelOut(units='mm')['pads']
                        features_dict = self.get_fea_point(features)
                        # 检测是否防呆1mm以上
                        # get_point_rect = self.get_point_rect_type(features_dict)
                        get_point_rect, show_warning = self.get_point_rect_type(features_dict, check_fd=True)
                        if show_warning:
                            log = showlog + show_warning
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                                 layer, log, dic_zu_layer,
                                                                                 add_note_layer=layer)
                        else:
                            # 判断是否左下角防呆
                            show_1mm, show_1um = self.set_fd_space_1mm('1', get_point_rect)
                            if show_1mm:
                                log = showlog + show_1mm
                                arraylist.append(log)
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                                     layer, log, dic_zu_layer,
                                                                                     add_note_layer=layer)
                            if show_1um:
                                log = showlog + show_1um
                                arraylist.append(log)
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                                     layer, log, dic_zu_layer,
                                                                                     add_note_layer=layer)
        step.clearAll()
        step.resetFilter()
        if arraylist:
            return arraylist, dic_zu_layer
        return "success", None

    def check_dld_targe(self, dic = {}):
        """
        检测镭射dld层是否防呆,和对应线路层标靶同步检测，跨层的dld线路层需要检测n+1,或者n+2层
        """
        arraylist = []
        dic_zu_layer = dic
        if not "panel" in matrixinfo["gCOLstep_name"]:
            return "success", None
        stepName = 'panel'
        step = gClasses.Step(job, stepName)
        step.open()
        step.clearAll()
        step.resetFilter()
        step.COM("units,type=mm")
        all_layers = step.getLayers()
        inn_dld = []
        for layer in all_layers:
            if re.search('^dld\d+-\d+$', layer):
                laser_name = layer.replace('dld', 's')
                if laser_name in laser_drill_layers:
                    inn_dld.append(layer)
        for dld_name in inn_dld:
            dld_features_dict, ref_features_dict = None, None
            num1, num2 = dld_name.replace('dld', '').split('-')
            num_abs = abs(int(num2) - int(num1))
            if int(num1) < int(num2):
                if int(num2) - int(num1) == 1:
                    ref_signal = 'l{0}'.format(int(num1) + 1)
                    ref_dld_layers = ['l{0}'.format(int(num1) + 1)]
                else:
                    ref_signal = 'l{0}'.format(int(num1) + 2)
                    ref_dld_layers = ['l{0}'.format(int(num1) + 1), 'l{0}'.format(int(num1) + num_abs)]
            else:
                if int(num1) - int(num2) == 1:
                    ref_signal = 'l{0}'.format(int(num1) - 1)
                    ref_dld_layers = ['l{0}'.format(int(num1) - 1)]
                else:
                    ref_signal = 'l{0}'.format(int(num1) - 2)
                    ref_dld_layers = ['l{0}'.format(int(num1) - 1), 'l{0}'.format(int(num1) - num_abs)]

            step.affect(dld_name)
            step.selectAll()
            if not step.featureSelected():
                log = u"{0}层对位孔数量为0".format(dld_name)
                arraylist.append(log)
            elif step.featureSelected() < 4:
                log = u"{0}层对位孔数量数量低于4颗".format(dld_name)
                arraylist.append(log)
                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, dld_name,
                                                                     dld_name, log, dic_zu_layer,
                                                                     add_note_layer=dld_name)
            else:
                layer_cmd = gClasses.Layer(step, dld_name)
                features = layer_cmd.featSelOut(units='mm')['pads']
                dld_features_dict = self.get_fea_point(features)
                step.clearAll()
                for ref_lay in ref_dld_layers:
                    step.affect(ref_lay)
                    step.filter_set(include_syms='sh-ldi')
                    step.refSelectFilter(dld_name)
                if step.featureSelected() < 4:
                    log = u"{0}对应的镭射对位靶标数量低于4颗,请检查是否在同一中心".format(dld_name)
                    arraylist.append(log)
                else:
                    for ref_dldlay in ref_dld_layers:
                        layer_cmd = gClasses.Layer(step, ref_dldlay)
                        features = layer_cmd.featSelOut(units='mm')['pads']
                        if not features:
                            step.unaffect(ref_dldlay)
                            continue
                        ref_features_dict = self.get_fea_point(features)
                        # 如果数量大于等于4颗检测是否在同一位置
                        err_point_keys = []
                        if dld_features_dict and ref_features_dict:
                            for k, v in dld_features_dict.items():
                                if ref_features_dict[k] - v > 0.01:
                                    err_point_keys.append(k[1:])
                        err_numbers = list(set(err_point_keys))
                        if err_numbers:
                            step.clearAll()
                            step.affect(dld_name)
                            err_points = [(dld_features_dict['x' + i], dld_features_dict['y' + i]) for i in err_numbers]
                            for point in err_points:
                                step.COM(
                                    "sel_single_feat,operation=select,x={0},y={1},tol=10,cyclic=yes".format(point[0],point[1]))
                            if step.featureSelected():
                                log = u"{0}层对位孔和线路层标靶不在同一中心".format(dld_name)
                                arraylist.append(log)
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step,
                                                                                     dld_name,ref_dldlay, log, dic_zu_layer,
                                                                                     add_note_layer=dld_name)
                        else:
                            step.clearAll()
                            step.resetFilter()
                            step.affect(dld_name)
                            step.selectAll()
                            # 检测是否防呆1mm以上 ,右上角防呆
                            # get_point_rect = self.get_point_rect_type(dld_features_dict)
                            get_point_rect, show_warning = self.get_point_rect_type(dld_features_dict, check_fd=True)
                            if show_warning:
                                log = u"{0}层对位孔".format(dld_name) + show_warning
                                arraylist.append(log)
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step,
                                                                                     dld_name,
                                                                                     dld_name, log, dic_zu_layer,
                                                                                     add_note_layer=dld_name)
                            else:
                                # 判断是否右上角防呆
                                show_1mm, show_1um = self.set_fd_space_1mm('3', get_point_rect)
                                if show_1mm:
                                    log = u"{0}层对位孔".format(dld_name) + show_1mm
                                    arraylist.append(log)
                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step,
                                                                                         dld_name,
                                                                                         dld_name, log, dic_zu_layer,
                                                                                         add_note_layer=dld_name)

                                if show_1um:
                                    log = u"{0}层对位孔".format(dld_name) + show_1um
                                    arraylist.append(log)
                                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step,
                                                                                         dld_name,
                                                                                         dld_name, log, dic_zu_layer,
                                                                                         add_note_layer=dld_name)



            step.clearAll()
            step.resetFilter()
        if arraylist:
            return arraylist, dic_zu_layer
        else:
            return "success", None

    def check_fxk_targe(self, type='all' ,dic = {}):
        """
        检测机械钻孔方向孔是否在同一水平线上面
        检测开料钻pin孔，双面板和开料钻埋孔是否呈L形  -- 钻孔对应层inn，dbk
        检测机械钻CCD挂孔是否防呆大于1mm，适用类型 通孔，开料钻埋孔
        检测压合机械钻定位孔，排除开料钻埋孔，双面通孔 inn,inn3-6 ,二钻inn
        通孔按属性区分，埋孔用线路层d对应标记cover
        """
        if type == 'inner':
            check_list = mai_drill_layers
        elif type == 'outer':
            check_list = tongkongDrillLayer
        else:
            check_list = mai_drill_layers + tongkongDrillLayer
        arraylist = []
        dic_zu_layer = dic
        if not "panel" in matrixinfo["gCOLstep_name"]:
            return "success", None
        stepName = 'panel'
        step = gClasses.Step(job,stepName)
        step.open()
        step.COM("units,type=mm")
        pro = step.getProfile()
        pro_centx, pro_centy = pro.xcenter * 25.4, pro.ycenter * 25.4
        for drlname in check_list:
            drl_cmd = gClasses.Layer(step, drlname)
            regx = 'b(\d+)-(\d+)'
            res = re.search(regx, drlname)
            step.resetFilter()
            step.clearAll()
            step.affect(drlname)
            # 设置可选项条件
            check_ccd = False  #检测CCD 挂孔
            check_pin = False  #开料钻pin孔，双面板和开料钻埋孔
            check_inn_pin = False  #检测压合机械钻定位孔，排除开料钻埋孔，双面通孔
            if res:
                top_num, bot_num = res.groups()
                ref_signal = 'l{0}'.format(top_num)
                ref_ccd_signal = ref_signal
                if abs(int(bot_num) - int(top_num)) == 1:
                    check_ccd = True
                    check_pin = 'inn{0}{1}'.format(top_num,bot_num)
                else:
                    check_inn_pin = 'inn{0}{1}'.format(top_num,bot_num)
                    ref_inn_layer = 'l{0}'.format(int(top_num) + 1)
            else:
                if int(jobname[4:6]) == 2:
                    check_pin = 'dbk'
                else:
                    check_inn_pin = 'inn'
                    ref_inn_layer = 'l2'
                check_ccd = True
                ref_signal = 'l2'
                ref_ccd_signal = 'l1'
            # 先检测方向孔,不同检测pin孔inn ,双面板为dbk层# 双面板直接按属性获取数量
            step.filter_set(include_syms='r3175')
            if int(jobname[4:6]) == 2:
                step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=drl_fxk")
                step.selectAll()
            else:
                step.COM("sel_ref_feat,layers={0},use=filter,mode=cover,pads_as=limits,f_types="
                         "line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=sh-pindonut*\;sh-dwtop2013\;sh-dwbot2013,exclude_syms=".format(ref_signal))
                # step.refSelectFilter(ref_signal, mode='cover', include_syms='sh-pindonut*')

            if step.featureSelected() != 5:
                if int(jobname[4:6]) == 2:
                    log = u"{0}层方向孔数量不等于5颗".format(drlname)
                else:
                    log = u"{0}层方向孔数量不等于5颗，请检查是否漏加或者和{1}层对应的symbol:sh-pindonut不在同一中心".format(drlname, ref_signal)
                arraylist.append(log)
                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, drlname,
                                                                     drlname, log, dic_zu_layer,
                                                                     add_note_layer=drlname)
            else:
                features = drl_cmd.featSelOut(units='mm')['pads']
                features_dict = self.get_fea_point(features)
                point_4space, show_warning = self.get_point_rect_type(features_dict)
                more_than_1um = [i for i in point_4space.values() if i > 0.01]
                # 工具孔（方向孔）不防呆
                if more_than_1um:
                    log = u"{0}层方向孔四角未在水平直线上".format(drlname)
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, drlname,
                                                                         drlname, log, dic_zu_layer,
                                                                        add_note_layer=drlname)
            step.clearAll()
            step.resetFilter()
            # 检测开料钻埋孔pin定位孔
            if check_pin and step.isLayer(check_pin):
                step.clearAll()
                step.resetFilter()
                step.affect(check_pin)
                step.filter_set(include_syms='r3100\;r3175')
                step.selectAll()
                if step.featureSelected() != 3:
                    log = u"{0}层pin孔数量不等于3".format(check_pin)
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, check_pin,
                                                                         check_pin, log, dic_zu_layer,
                                                                        add_note_layer=check_pin)
                else:
                    # 检测3孔要是否呈L型 ,下方为1，上轴为2，左边防呆为3 ，1-2 Y方向直线，2-3X方向直线
                    lay_cmd = gClasses.Layer(step, check_pin)
                    features = lay_cmd.featSelOut(units='mm')['pads']
                    min_x = min([obj.x for obj in features if obj.y > pro_centy])
                    min_y = min([obj.y for obj in features if obj.y < pro_centy])
                    for obj in features:
                        if obj.y < pro_centx:
                            if obj.y == min_y:
                                pin_x1, pin_y1 = obj.x, obj.y
                        else:
                            if obj.x == min_x:
                                pin_x3, pin_y3 = obj.x, obj.y
                            else:
                                pin_x2, pin_y2 = obj.x, obj.y
                    if pin_x2 - pin_x1  > 0.01 or pin_y3 - pin_y2 > 0.01:
                        log = u"{0}层pin孔不在水平线上".format(check_pin)
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, check_pin,
                                                                             check_pin, log, dic_zu_layer,
                                                                             add_note_layer=check_pin)
            step.clearAll()
            step.resetFilter()
            # 检测inn定位孔和对应线路层合并检测
            if check_inn_pin and step.isLayer(check_inn_pin):
                step.affect(check_inn_pin)
                # step.filter_set(include_syms='r3175')
                step.refSelectFilter(ref_inn_layer, include_syms='hdi1-ba*')
                if step.featureSelected() < 4:
                    log = u"{0}层定位孔数量少于4".format(check_inn_pin)
                    arraylist.append(log)
                    dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, check_inn_pin,
                                                                         check_inn_pin, log, dic_zu_layer,
                                                                        add_note_layer=check_inn_pin)
                else:
                    lay_cmd = gClasses.Layer(step, check_inn_pin)
                    features = lay_cmd.featSelOut(units='mm')['pads']
                    feature_dict = self.get_fea_point(features)
                    # get_point_rect = self.get_point_rect_type(feature_dict)
                    get_point_rect, show_warning = self.get_point_rect_type(feature_dict, check_fd=True)
                    if show_warning:
                        log = u"{0}层".format(check_inn_pin) + show_warning
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step,
                                                                             check_inn_pin,
                                                                             check_inn_pin, log, dic_zu_layer,
                                                                             add_note_layer=check_inn_pin)
                    else:
                        # 判断是有任意防呆距离大于1mm ，左下角防呆
                        show_1mm, show_1um = self.set_fd_space_1mm('1', get_point_rect)
                        if show_1mm:
                            log = u"{0}层".format(check_inn_pin) + show_1mm
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step,
                                                                                 check_inn_pin,
                                                                                 check_inn_pin, log, dic_zu_layer,
                                                                                 add_note_layer=check_inn_pin)
                        if show_1um:
                            log = u"{0}层".format(check_inn_pin) + show_1um
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step,
                                                                                 check_inn_pin,
                                                                                 check_inn_pin, log, dic_zu_layer,
                                                                                 add_note_layer=check_inn_pin)

            #检测CCD挂孔
            step.clearAll()
            step.resetFilter()
            if check_ccd:
                # 如果对应层没有对位标无法确定位置不检测
                step.clearAll()
                step.affect(ref_ccd_signal)
                step.filter_set(include_syms='sh-dwtop*\;sh-dwbot*')
                step.selectAll()
                if step.featureSelected() < 4:
                    pass
                else:
                    step.clearAll()
                    step.resetFilter()
                    step.affect(drlname)
                    step.filter_set(include_syms='r3175')
                    step.refSelectFilter(ref_ccd_signal, include_syms='sh-dwtop*\;sh-dwbot*')

                    if step.featureSelected() < 4:
                        log = u"{0}层CCD挂板孔少于4个,请检查是否和{1}层对应的symbol在同一中心".format(drlname,ref_ccd_signal )
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, drlname,
                                                                             drlname, log, dic_zu_layer,
                                                                             add_note_layer=drlname)
                    else:
                        features = drl_cmd.featSelOut(units='mm')['pads']
                        feature_dict = self.get_fea_point(features)
                        # get_point_rect = self.get_point_rect_type(feature_dict)
                        get_point_rect, show_warning = self.get_point_rect_type(feature_dict, check_fd=True)
                        if show_warning:
                            log = u"{0}层CCD挂板孔".format(drlname) + show_warning
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, drlname,
                                                                                 drlname, log, dic_zu_layer,
                                                                                 add_note_layer=drlname)
                        else:
                            # 判断是有任意防呆距离大于1mm ,左下角防呆
                            show_1mm, show_1um = self.set_fd_space_1mm('1', get_point_rect)
                            if show_1mm:
                                log = u"{0}层CCD挂板孔".format(drlname) + show_1mm
                                arraylist.append(log)
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, drlname,
                                                                                     drlname, log, dic_zu_layer,
                                                                                     add_note_layer=drlname)
                            if show_1um:
                                log = u"{0}层CCD挂板孔".format(drlname) + show_1um
                                arraylist.append(log)
                                dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, drlname,
                                                                                     drlname, log, dic_zu_layer,
                                                                                     add_note_layer=drlname)

            step.clearAll()
            step.resetFilter()
        if arraylist:
            return arraylist, dic_zu_layer
        return "success", None


    def set_fd_space_1mm(self, fx, dict_data):
        # 按传入的防呆方向返回相应的提示1左下角防呆,2,左上角。。
        log_space, log_zx = None, None
        if  fx == '1':
            if dict_data['l'] < 1 and dict_data['b'] < 1:
                log_space = u"左下角防呆距离小于1mm"
            elif dict_data['l'] > 0.01 and dict_data['b'] > 0.01:
                log_space = u"左下角不能在X和Y方向同时防呆"

            if dict_data['t'] > 0.01 and dict_data['r'] > 0.01:
                log_zx = u"上边和右边不在一条水平直线上"
            elif dict_data['t'] > 0.01:
                log_zx = u"上边不在一条水平直线上"
            elif dict_data['r'] > 0.01:
                log_zx = u"右边不在一条水平直线上"
        elif  fx == '2':
            if dict_data['t'] < 1 and dict_data['l'] < 1:
                log_space = u"左上角防呆距离小于1mm"
            elif dict_data['l'] > 0.01 and dict_data['t'] > 0.01:
                log_space = u"左上角不能在X和Y方向同时防呆"
            if dict_data['r'] > 0.01 and dict_data['b'] > 0.01:
                log_zx = u"右边和下边不在一条水平直线上"
            elif dict_data['r'] > 0.01:
                log_zx = u"右边不在一条水平直线上"
            elif dict_data['b'] > 0.01:
                log_zx = u"下边不在一条水平直线上"
        elif  fx == '3':
            if dict_data['t'] < 1 and dict_data['r'] < 1:
                log_space = u"右上角防呆距离小于1mm"
            elif dict_data['t'] > 0.01 and dict_data['r'] > 0.01:
                log_space = u"右上角不能在X和Y方向同时防呆"
            if dict_data['l'] > 0.01 and dict_data['b'] > 0.01:
                log_zx = u"左边和下边不在一条水平直线上"
            elif dict_data['l'] > 0.01:
                log_zx = u"左边不在一条水平直线上"
            elif dict_data['b'] > 0.01:
                log_zx = u"下边不在一条水平直线上"
        elif  fx == '4':
            if dict_data['r'] < 1 and dict_data['b'] < 1:
                log_space = u"右下角防呆距离小于1mm"
            elif dict_data['r'] > 0.01 and dict_data['b'] > 0.01:
                log_space = u"右下角不能在X和Y方向同时防呆"
            if dict_data['l'] > 0.01 and dict_data['t'] > 0.01:
                log_zx = u"左边和上边不在一条水平直线上"
            elif dict_data['l'] > 0.01:
                log_zx = u"左边不在一条水平直线上"
            elif dict_data['t'] > 0.01:
                log_zx = u"上边不在一条水平直线上"
        if re.search('fa8622o6784f6', job.name):
            return None,None
        return log_space, log_zx


    def check_v5laser_targe(self, type='all', dic = {}):
        """
        检测5代靶是否防呆
        """
        if type == 'inner':
            res_layers = innersignalLayers
        elif type == 'outer':
            res_layers = outsignalLayers
        else:
            res_layers = outsignalLayers + innersignalLayers
        # 5代靶防呆检测  "hdi-dwpad"
        arraylist = []
        dic_zu_layer = dic
        if "panel" in matrixinfo["gCOLstep_name"]:
            step = gClasses.Step(job, 'panel')
            step.open()
            for layer in res_layers:
                # 获取hdi-dwpad是否存在
                layer_errs = []
                layer_cmd = gClasses.Layer(step, layer)
                step.clearAll()
                step.resetFilter()
                step.affect(layer)
                step.filter_set(include_syms='hdi-dwpad*')
                step.selectAll()
                if not step.featureSelected():
                    continue
                # if step.featureSelected() != 4:
                #     log = u'{0}层5代靶数量不等于4'.format(layer)
                #     arraylist.append(log)
                #     dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                #                                                          layer, log, dic_zu_layer,
                #                                                          add_note_layer=layer)
                else:
                    features = layer_cmd.featSelOut(units='mm')['pads']
                    features_dict = self.get_fea_point(features)
                    # get_point_rect = self.get_point_rect_type(features_dict)
                    get_point_rect, show_warning = self.get_point_rect_type(features_dict, check_fd=True)
                    if show_warning:
                        log = u"{0}层5代靶".format(layer) + show_warning
                        arraylist.append(log)
                        dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                             layer, log, dic_zu_layer,
                                                                             add_note_layer=layer)
                    else:
                        # 五代靶右上角防呆
                        show_1mm, show_1um = self.set_fd_space_1mm('3', get_point_rect)
                        if show_1mm:
                            log = u"{0}层5代靶".format(layer) + show_1mm
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                                 layer, log, dic_zu_layer,
                                                                                 add_note_layer=layer)

                        if show_1um:
                            log = u"{0}层5代靶".format(layer) + show_1um
                            arraylist.append(log)
                            dic_zu_layer = self.get_selected_dic_note_coordinate(job.name, step.name, step, layer,
                                                                                 layer, log, dic_zu_layer,
                                                                                 add_note_layer=layer)

                step.clearAll()
                step.resetFilter()
        if arraylist:
            return arraylist, dic_zu_layer
        return "success", None

    def get_point_rect_type(self,dict_data, check_fd = False):
        # 获取4点上下左右的边距,
        # 检测是否在X,Y,以及旋转防呆--20250106加入
        left = abs(dict_data['x2'] - dict_data['x1'])
        top = abs(dict_data['y2'] - dict_data['y3'])
        right = abs(dict_data['x3'] - dict_data['x4'])
        bot = abs(dict_data['y4'] - dict_data['y1'])
        dict = {'l' : left ,
                't' : top ,
                'r' : right ,
                'b' : bot
                }
        show_str = ''
        if check_fd:
            # step = gClasses.Step(job, 'panel')
            # pro = step.getProfile()
            # pro_centx, pro_centy = pro.xcenter * 25.4, pro.ycenter * 25.4

            # len_top = math.sqrt((dict_data['x3'] - dict_data['x2']) ** 2 + (dict_data['y3'] - dict_data['y2']) ** 2)
            # len_bot = math.sqrt((dict_data['x4'] - dict_data['x1']) ** 2 + (dict_data['y4'] - dict_data['y1']) ** 2)
            # len_left = math.sqrt((dict_data['x2'] - dict_data['x1']) ** 2 + (dict_data['y2'] - dict_data['y1']) ** 2)
            # len_right = math.sqrt((dict_data['x3'] - dict_data['x4']) ** 2 + (dict_data['y3'] - dict_data['y4']) ** 2)

            if left < 0.1 and right < 0.1 and top < 0.1 and bot < 0.1:
                show_str = u'X,Y方向镜像以及旋转180度后均不防呆'
            elif top < 0.1 and bot < 0.1:
                xspace_left = dict_data['x2'] - dict_data['x1']
                xspace_right = dict_data['x3'] - dict_data['x4']
                if -1 < abs(xspace_left) - abs(xspace_right) < 1:
                    if -0.01 < abs(xspace_left) - abs(xspace_right) < 0.01:
                        if (xspace_left < 0 and xspace_right < 0) or (xspace_left > 0 and xspace_right > 0):
                            show_str = u'旋转方向不防呆'
                        else:
                            show_str = u'X方向镜像后不防呆'
                    else:
                        if (xspace_left < 0 and xspace_right < 0) or (xspace_left > 0 and xspace_right > 0):
                            show_str = u'防呆间距不足1MM，旋转后易混板'
                        else:
                            show_str = u'防呆间距不足1MM，X方向镜像后易混板'

            elif left < 0.1 and right < 0.1:
                yspace_top = dict_data['y2'] - dict_data['y3']
                yspace_bot = dict_data['y1'] - dict_data['y4']
                if -1 < abs(yspace_top) - abs(yspace_bot) < 1:
                    if -0.01 < abs(yspace_top) - abs(yspace_bot) < 0.01:
                        if (yspace_top < 0 and yspace_bot < 0) or (yspace_top > 0 and yspace_bot > 0):
                            show_str = u'旋转方向不防呆'
                        else:
                            show_str = u'Y方向镜像后不防呆'
                    else:
                        if (yspace_top < 0 and yspace_bot < 0) or (yspace_top > 0 and yspace_bot > 0):
                            show_str = u'防呆间距不足1MM，旋转后易混板'
                        else:
                            show_str = u'防呆间距不足1MM，Y方向镜像后易混板'
            else:
                if not re.search('hb1312pha99', jobname):
                    show_str = u'相邻两个方向都不在一条水平直线上，违反设计准则'

        if show_str:
            update_current_job_check_log(os.environ.get("CHECK_ID", "NULL"),
                                         u"forbid_or_information='{0}'".format(u"拦截(不放行)"))

        return dict, show_str

    def get_fea_point(self, features_dict):
        # 获取panel4角最外围点的坐标,4点坐标
        step = gClasses.Step(job, 'panel')
        pro = step.getProfile()
        pro_centx, pro_centy = pro.xcenter * 25.4, pro.ycenter * 25.4
        dict = {'x1' : None,
                'y1': None,
                'x2': None,
                'y2': None,
                'x3': None,
                'y3': None,
                'x4': None,
                'y4': None,
                }
        for obj in features_dict:
            # 左下1
            if obj.x < pro_centx and obj.y < pro_centy:
                if dict['x1'] == None:
                    dict['x1'], dict['y1'] = obj.x , obj.y
                else:
                    if abs(obj.y - dict['y1']) < abs(obj.x - dict['x1']):
                        if obj.x < dict['x1']:
                            dict['x1'], dict['y1'] = obj.x , obj.y
                    else:
                        if obj.y < dict['y1']:
                            dict['x1'], dict['y1'] = obj.x , obj.y
            # 左上2
            elif obj.x < pro_centx and obj.y > pro_centy:
                if dict['x2'] == None:
                    dict['x2'], dict['y2'] = obj.x , obj.y
                else:
                    if abs(obj.y - dict['y2']) < abs(obj.x - dict['x2']):
                        if obj.x < dict['x2']:
                            dict['x2'], dict['y2'] = obj.x , obj.y
                    else:
                        if obj.y > dict['y2']:
                            dict['x2'], dict['y2'] = obj.x , obj.y
            # 右上3
            elif obj.x > pro_centx and obj.y > pro_centy:
                if dict['x3'] == None:
                    dict['x3'], dict['y3'] = obj.x , obj.y
                else:
                    if abs(obj.y - dict['y3']) < abs(obj.x - dict['x3']):
                        if obj.x > dict['x3']:
                            dict['x3'], dict['y3'] = obj.x , obj.y
                    else:
                        if obj.y > dict['y3']:
                            dict['x3'], dict['y3'] = obj.x, obj.y
            # 右下4
            else:
                if dict['x4'] == None:
                    dict['x4'], dict['y4'] = obj.x, obj.y
                else:
                    if abs(obj.y - dict['y4']) < abs(obj.x - dict['x4']):
                        if obj.x > dict['x4']:
                            dict['x4'], dict['y4'] = obj.x , obj.y
                    else:
                        if obj.y < dict['y4']:
                            dict['x4'], dict['y4'] = obj.x , obj.y

        return dict

if __name__ == "__main__":
    main = CheckParts()
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
    if func is None:
        func = "check_set_slotMark"
        # args = ['all']
    ###

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
                    main.create_log_and_update_coordinate(job.name, func + " " + " ".join(args), *result)
                else:
                    main.create_log_and_update_coordinate(job.name, func, *result)
    sys.exit()
