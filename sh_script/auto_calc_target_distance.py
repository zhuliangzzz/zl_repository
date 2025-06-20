#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20230428"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""自动计算靶距 """

import os
import sys
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
    
import MySQL_DB
import time
import gClasses
import numpy
import random
import datetime
from get_erp_job_info import get_inplan_mrp_info, \
     get_outer_target_condition, get_laser_fg_type, \
     get_ks_bd_target_info, get_ks_bd_target_info_detail, \
     get_mysql_ks_bd_target_info, get_StackupData, \
     get_all_job_creation_date

from genesisPackages import get_profile_limits, \
     get_sr_limits,job, top, mai_drill_layers, \
     mai_man_drill_layers
from scriptsRunRecordLog import uploadinglog
# from send_html_request_to_tc_aac_file import post_message

from showTargetDistanceInformation import TargetDistance_UI, QtGui, Qt

dic_job_date = {}
for dic_info in get_all_job_creation_date():       
    dic_job_date[dic_info["JOB_NAME"]] = dic_info["CREATION_DATE"]

conn = MySQL_DB.MySQL()
dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                           username='root', passwd='k06931!')

class get_target_distance(object):
    """"""

    def __init__(self, jobname, stepname):
        """Constructor"""       
        self.stepname = stepname
        self.jobname = jobname
        self.job = gClasses.Job(jobname)
        self.step = gClasses.Step(self.job, stepname)
        self.step.open() 
        
    def get_same_size_jobs_info(self,jobname, panel_x, panel_y):
        """获取相同尺寸的型号"""
        #sql = """select a.target_x1 TARGET_X1,a.target_y1 TARGET_Y1 ,a.job_name JOB_NAME
        #from engineering.hdi_target_info a
        #where ABS(a.panel_sizex-{0}) < 10
        #and ABS(a.panel_sizey-{1}) < 10
        #and a.job_name <>'{2}'"""
        sql = """select a.bar4x1 TARGET_X1,a.bar4y1 TARGET_Y1 ,a.job_name JOB_NAME
        from hdi_engineering.incam_process_info a
        where ABS(a.pnlxinch*25.4-{0}) < 10
        and ABS(a.pnlyinch*25.4-{1}) < 10
        and a.mrpname not like '%-%'
        and a.job_name <>'{2}'"""        
        data_info1 = conn.SELECT_DIC(dbc_m, sql.format(panel_x, panel_y, jobname.split("-")[0]))
        
        sql = """select a.bar4x1 TARGET_X1,a.bar4y1 TARGET_Y1 ,a.job_name JOB_NAME
        from hdi_engineering.incam_process_info_temp a
        where ABS(a.pnlxinch*25.4-{0}) < 10
        and ABS(a.pnlyinch*25.4-{1}) < 10
        and a.mrpname not like '%-%'
        and a.job_name <>'{2}'"""    #
        # and datediff(now(),create_time) < 10临时库只取最近10天的数据
        
        data_info2 = conn.SELECT_DIC(dbc_m, sql.format(panel_x, panel_y, jobname.split("-")[0]))        
        if data_info1 and data_info2:
            return data_info1 + data_info2
        else:
            return data_info1 or data_info2        
    
    def check_is_outer_target_condition(self):
        """检测是否有外四靶条件"""
        
        data_info = get_outer_target_condition(self.jobname.upper())        
        fg_info = get_laser_fg_type(self.jobname.upper())
        
        self.dic_outer_target_info = {}
        
        fg_type = [x for x in fg_info if x["PNL_PARCELLATION_METHOD_"] > 1]
        for index, dic_target_info in enumerate(sorted(data_info, key=lambda x: x["PROCESS_LEVEL"] * -1)):
            mrp_name = dic_target_info["MRP_NAME"]
            # 机械盲埋共存的情况 且不存在镭射烧靶的情况
            if dic_target_info["DRL_NAME"] and dic_target_info["LASER_NAME"] and not dic_target_info["LASER_BURN_TARGET"]:                
                self.dic_outer_target_info[mrp_name] = dic_target_info
            
            # 测试临时用 20230817 by lyh
            #if "EA1908GC903A3" == mrp_name:
                #self.dic_outer_target_info[mrp_name] = dic_target_info
        
            if fg_type:
                # 存在镭射分割 且N-1 层无镭射的情况
                if dic_target_info["LASER_NAME"] and index < len(data_info) - 1:
                    if not data_info[index+1]["LASER_NAME"]:
                        self.dic_outer_target_info[mrp_name] = dic_target_info
                        
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
        
    def start_calc(self):
        step = self.step       
        
        self.ui = TargetDistance_UI()
        
        self.check_is_outer_target_condition()
        
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
        sr_xmin,sr_ymin,sr_xmax,sr_ymax = get_sr_limits(step)
        #all_x = [x1 for x1, y1, x2, y2 in rect_area]
        #all_x += [x2 for x1, y1, x2, y2 in rect_area]
        #all_y = [y1 for x1, y1, x2, y2 in rect_area]
        #all_y += [y1 for x1, y1, x2, y2 in rect_area]
        #sr_ymax = max(all_y)
        #sr_ymin = min(all_y)
        self.array_mrp_info = get_inplan_mrp_info(self.jobname.upper())
        
        self.core_mrp_info = get_inplan_mrp_info(self.jobname.upper(), condtion="d.proc_subtype IN ( 27 ) ")
        
        self.ganmo_size_info = get_StackupData(self.jobname.upper())

        
        if not self.array_mrp_info:
            log = u"型号{0} 抓取inplan信息为空，请确认型号是否正确或者反馈MI检查型号是否checkin！".format(self.jobname.upper().split("-")[0])
            
            try:
                uploadinglog(__credits__, log, self.stepname, GEN_USER=top.getUser())
            except:
                pass
            
            return log
        
        self.array_list_ganmo_area = []
        for i, dic_info in enumerate(sorted(self.array_mrp_info, key=lambda x: x["PROCESS_NUM"] * -1)): 
            mrp_name = dic_info["MRPNAME"]
            input_rout_x = dic_info["PNLROUTX"] * 25.4
            input_rout_y = dic_info["PNLROUTY"] * 25.4
            panel_x = dic_info["PNLXINCH"] * 25.4
            panel_y = dic_info["PNLYINCH"] * 25.4              
            for ganmo_info in self.ganmo_size_info:
                if ganmo_info["MRP_NAME"] == mrp_name:
                    current_gm_size = ganmo_info['DF_WIDTH'] * 25.4
                    if input_rout_x < current_gm_size <= input_rout_y:
                        gm_startx = (panel_x - input_rout_x) * 0.5
                        gm_starty = (panel_y - current_gm_size) * 0.5
                        gm_endx = gm_startx + input_rout_x
                        gm_endy = gm_starty + current_gm_size
                        self.array_list_ganmo_area.append([gm_startx, gm_starty, gm_endx, gm_endy])
                    elif current_gm_size <= input_rout_x:
                        gm_startx = (panel_x - current_gm_size) * 0.5
                        gm_starty = (panel_y - input_rout_y) * 0.5
                        gm_endx = gm_startx + current_gm_size
                        gm_endy = gm_starty + input_rout_y
                        self.array_list_ganmo_area.append([gm_startx, gm_starty, gm_endx, gm_endy])

        outer_process_num = None
        for i, dic_info in enumerate(sorted(self.array_mrp_info, key=lambda x: x["PROCESS_NUM"] * -1)): 
            mrp_name = dic_info["MRPNAME"]
            rout_x = dic_info["PNLROUTX"] * 25.4
            rout_y = dic_info["PNLROUTY"] * 25.4            
            if "-" not in dic_info["MRPNAME"]:
                outer_process_num = dic_info["PROCESS_NUM"]
                break
        
        for dic_info in self.array_mrp_info:
            rout_x = dic_info["PNLROUTX"] * 25.4
            rout_y = dic_info["PNLROUTY"] * 25.4
            panel_x = dic_info["PNLXINCH"] * 25.4
            panel_y = dic_info["PNLYINCH"] * 25.4   
            
            #实际上只要计算外层的前一次压合即可
            if len(self.array_mrp_info) == 1:
                # 一次压合的 按芯板上来计算
                lb_x = 0
                lb_y = 0              
                break
            else:
                if dic_info["PROCESS_NUM"] == outer_process_num - 1:
                    lb_x = (panel_x - rout_x) * 0.5
                    lb_y = (panel_y - rout_y) * 0.5
                    break
        
        add_to_edge = u"系统判断"
        if "-lyh" in self.jobname or "manual_set_position" in sys.argv[1:]:            
            items = [u"长边", u"短边",]    
            item, okPressed = QtGui.QInputDialog.getItem(QtGui.QWidget(), u"提示", u"靶距加长短边选择，请选择下拉列表中的长边或短边:",
                                                         items, 0, False, Qt.Qt.WindowStaysOnTopHint)    
            add_to_edge = unicode(item.toUtf8(), 'utf8', 'ignore').encode(
                        'gb2312').decode("cp936").strip()
            
            if not okPressed:
                sys.exit()
        
        manul_select = False        
        if add_to_edge == u"系统判断":            
            
            if len(self.core_mrp_info) >= 2 or (f_xmax <= 622.3 and f_ymax <= 622.3):
                add_to_edge=u"短边"
            else:
                add_to_edge=u"长边"
            
            res = self.get_add_target_area(add_to_edge, defender_same_size=True)
            if not res:
                res = self.get_add_target_area(add_to_edge, defender_same_size=False)                
            
            if not res:
                add_to_edge=u"长边" if add_to_edge == u"短边" else u"短边"
                res = self.get_add_target_area(add_to_edge, defender_same_size=True)                
                if not res:
                    res = self.get_add_target_area(add_to_edge, defender_same_size=False)
                
            #若最后还是没有合适位置，把避开孔的区域去掉20230828 by lyh
            if not res:
                if len(self.core_mrp_info) >= 2 or (f_xmax <= 622.3 and f_ymax <= 622.3):
                    add_to_edge=u"短边"
                else:
                    add_to_edge=u"长边"
                
                res = self.get_add_target_area(add_to_edge, defender_same_size=True, check_avoid_hole_area=False)
                if not res:
                    res = self.get_add_target_area(add_to_edge, defender_same_size=False, check_avoid_hole_area=False)
                    
                if not res:
                    add_to_edge=u"长边" if add_to_edge == u"短边" else u"短边"
                    res = self.get_add_target_area(add_to_edge, defender_same_size=True, check_avoid_hole_area=False)                
                    if not res:
                        res = self.get_add_target_area(add_to_edge, defender_same_size=False, check_avoid_hole_area=False)                    
                
        else:
            manul_select = True
            res = self.get_add_target_area(add_to_edge, defender_same_size=True)
            if not res:
                res = self.get_add_target_area(add_to_edge, defender_same_size=False)
                
        rand = random.random()
        outer_array_xy_coord = []
        log = ""
        if res:
            all_add_position = []
            dic_uploading_info = {}
            dic_uploading_erp_info = {}
            if add_to_edge ==u"短边":                
                # array_xy_coord = sorted(res[0], key=lambda x: x[0] * -1)
                # array_xy_coord = sorted(res[0], key=lambda x: x[0])
                array_xy_coord, array_xy_coord_all,defender_type = res
                
                all_bar4x = [x2 for x2, y2 in array_xy_coord[:len(self.array_mrp_info)]]
                if all_bar4x[0] < all_bar4x[-1]:
                    flag = 1 # 内四靶从外往内加
                else:
                    flag = -1 # 内四靶从内往外加
                    
                for i, dic_info in enumerate(sorted(self.array_mrp_info, key=lambda x: x["PROCESS_NUM"] * -1)):                  
                    for j, xy in enumerate(array_xy_coord[:len(self.array_mrp_info)]):
                        if i == j:
                            mrp_name = dic_info["MRPNAME"]
                            x, y = xy
                            bar4x1 = f_xmax - x * 2 + flag * 0.04 * i
                            bar4x2 = f_xmax - x * 2 + flag * 0.04 * i
                            bar4y1 = f_ymax - y * 2
                            bar4y2 = bar4y1 + 2
                            bar3y = bar4y1
                            
                            if bar3y + 5.08 - (rout_y - 10 * 2) > 0:
                                # 改为距板内1mm即可
                                bar3y = (sr_ymax - sr_ymin) +  2 + 5.08
                                
                            try:                                
                                bar3x = 3 + (int(self.jobname[9]) + int(self.jobname[10])) * 0.01 + \
                                    0.13 * (int(self.jobname[12]) % 2) + (dic_info["PROCESS_NUM"] - 2) * 0.4
                            except Exception, e:
                                print e
                                bar3x = 3 + rand * 10 * 0.01 + (dic_info["PROCESS_NUM"] - 2) * 0.4
                                
                            dic_uploading_info[mrp_name] = {"BAR4X1": bar4x1,"BAR4X2": bar4x2,
                                                            "BAR4Y1": bar4y1,"BAR4Y2": bar4y2,
                                                            "BAR3Y": bar3y ,"BAR3X": bar3x* 25.4,}
                            dic_uploading_erp_info[mrp_name] = {"TC_AAC231": bar4x1,"TC_AAC233": bar4x2,
                                                                "TC_AAC232": bar4y1,"TC_AAC234": bar4y2,
                                                                "TC_AAC28": bar3y ,"TC_AAC27": bar3x* 25.4,}
                            if x == 0 and y == 0:
                                dic_uploading_info[mrp_name] = {"BAR4X1": 0,"BAR4X2": 0,
                                                                "BAR4Y1": 0,"BAR4Y2": 0,
                                                                "BAR3Y": 0 ,"BAR3X": 0,}
                                dic_uploading_erp_info[mrp_name] = {"TC_AAC231": 0,"TC_AAC233": 0,
                                                                    "TC_AAC232": 0,"TC_AAC234": 0,
                                                                    "TC_AAC28": 0 ,"TC_AAC27": 0,}                                
                            
                            all_add_position.append(xy)
                            # 外四靶计算
                            # 先把外四靶数据清零
                            outer_ba_info = {"SIG4X1": 0,"SIG4X2": 0,
                                             "SIG4Y1": 0,"SIG4Y2": 0,}
                            dic_uploading_info[mrp_name].update(outer_ba_info)
                            
                            if self.dic_outer_target_info:
                                    mrp_name = dic_info["MRPNAME"] 
                                    if self.dic_outer_target_info.has_key(mrp_name):
                                        for t, outer_ba_xy in enumerate(array_xy_coord_all[::flag]):
                                            x1, y1 = outer_ba_xy
                                            
                                            if outer_array_xy_coord :
                                                for exists_x, exists_y in outer_array_xy_coord:
                                                    if abs(x1 - exists_x) > 5.08:
                                                        break
                                                else:
                                                    continue
                                            
                                            if y1 == y:                                                
                                                outer_bar4x1 = f_xmax - x1 * 2
                                                outer_bar4x2 = f_xmax - x1 * 2
                                                outer_bar4y1 = f_ymax - y1 * 2
                                                outer_bar4y2 = outer_bar4y1 + 2
                                                if flag > 0 and x1 <= all_bar4x[0] - 5.08 and outer_bar4x1 - bar4x1 >= 30 :
                                                    break
                                                
                                                if flag < 0 and x1 <= all_bar4x[-1] - 5.08 and outer_bar4x1 - bar4x1 >= 30:
                                                    break
                                        
                                        outer_array_xy_coord.append(outer_ba_xy)
                                        all_add_position.append(outer_ba_xy)
                                        outer_ba_info = {"SIG4X1": outer_bar4x1,"SIG4X2": outer_bar4x2,
                                                         "SIG4Y1": outer_bar4y1,"SIG4Y2": outer_bar4y2,}
                                        dic_uploading_info[mrp_name].update(outer_ba_info)
                                        
                                        outer_ba_erp_info = {"TC_AAC235": outer_bar4x1,"TC_AAC237": outer_bar4x2,
                                                             "TC_AAC236": outer_bar4y1,"TC_AAC238": outer_bar4y2,}
                                        dic_uploading_erp_info[mrp_name].update(outer_ba_erp_info)
                                        #if "-lyh" in self.jobname:
                                            #step.PAUSE(str([outer_array_xy_coord, outer_ba_info, ]))
                                        
            else:
                # array_xy_coord = sorted(res[0], key=lambda x: x[1] * -1)
                # array_xy_coord = sorted(res[0], key=lambda x: x[1])
                array_xy_coord,array_xy_coord_all,defender_type = res
                
                all_bar4y = [y2 for x2, y2 in array_xy_coord[:len(self.array_mrp_info)]]
                if all_bar4y[0] < all_bar4y[-1]:
                    flag = 1 # 内四靶从外往内加
                else:
                    flag = -1 # 内四靶从内往外加
                    
                for i, dic_info in enumerate(sorted(self.array_mrp_info, key=lambda x: x["PROCESS_NUM"] * -1)): 
                    for j, xy in enumerate(array_xy_coord[:len(self.array_mrp_info)]):
                        if i == j:
                            mrp_name = dic_info["MRPNAME"]
                            x, y = xy
                            bar4x1 = f_xmax - x * 2
                            bar4x2 = f_xmax - x * 2
                            bar4y1 = f_ymax - y * 2 + flag * 0.04 * i
                            bar4y2 = bar4y1 + 2
                            bar3y = sr_ymax - sr_ymin + 5.6 * 2
                            if bar3y < 520 and sr_ymin > 14:
                                bar3y = f_ymax - 7 * 2
                                
                            # job.PAUSE(str([bar3y, (rout_y - 10 * 2)]))
                            if bar3y + 5.08 - (rout_y - 10 * 2) > 0:
                                # 改为距板内1mm即可
                                bar3y = (sr_ymax - sr_ymin) +  2 + 5.08
                                # job.PAUSE(str([bar3y, (sr_ymax - sr_ymin) +  2 + 5.08]))
                                
                            try:                                
                                bar3x = 3 + (int(self.jobname[9]) + int(self.jobname[10])) * 0.01 + \
                                    0.13 * (int(self.jobname[12]) % 2) + (dic_info["PROCESS_NUM"] - 2) * 0.4
                            except:
                                bar3x = 3 + rand * 10 * 0.01 + (dic_info["PROCESS_NUM"] - 2) * 0.4
                                
                            dic_uploading_info[mrp_name] = {"BAR4X1": bar4x1,"BAR4X2": bar4x2,
                                                            "BAR4Y1": bar4y1,"BAR4Y2": bar4y2,
                                                            "BAR3Y": bar3y ,"BAR3X": bar3x* 25.4,}
                            dic_uploading_erp_info[mrp_name] = {"TC_AAC231": bar4x1,"TC_AAC233": bar4x2,
                                                                "TC_AAC232": bar4y1,"TC_AAC234": bar4y2,
                                                                "TC_AAC28": bar3y ,"TC_AAC27": bar3x* 25.4,}                            
                            if x == 0 and y == 0:
                                dic_uploading_info[mrp_name] = {"BAR4X1": 0,"BAR4X2": 0,
                                                                "BAR4Y1": 0,"BAR4Y2": 0,
                                                                "BAR3Y": 0 ,"BAR3X": 0,}
                                dic_uploading_erp_info[mrp_name] = {"TC_AAC231": 0,"TC_AAC233": 0,
                                                                    "TC_AAC232": 0,"TC_AAC234": 0,
                                                                    "TC_AAC28": 0 ,"TC_AAC27": 0,}
                            all_add_position.append(xy)
                            # 外四靶计算
                            # 先把外四靶数据清零
                            outer_ba_info = {"SIG4X1": 0,"SIG4X2": 0,
                                             "SIG4Y1": 0,"SIG4Y2": 0,}
                            dic_uploading_info[mrp_name].update(outer_ba_info)
                            
                            if self.dic_outer_target_info:
                                    mrp_name = dic_info["MRPNAME"]                                       
                                        
                                    if self.dic_outer_target_info.has_key(mrp_name):
                                        for t, outer_ba_xy in enumerate(array_xy_coord_all[::flag]):
                                            x1, y1 = outer_ba_xy
                                            
                                            if outer_array_xy_coord :
                                                for exists_x, exists_y in outer_array_xy_coord:
                                                    if abs(y1 - exists_y) > 5.08:
                                                        break
                                                else:
                                                    continue
                                            
                                            if x1 == x:                                                
                                                outer_bar4x1 = f_xmax - x1 * 2
                                                outer_bar4x2 = f_xmax - x1 * 2
                                                outer_bar4y1 = f_ymax - y1 * 2
                                                outer_bar4y2 = outer_bar4y1 + 2
                                                if flag > 0 and y1 <= all_bar4y[0] - 5.08 and outer_bar4y1 - bar4y1 >= 30 :
                                                    break
                                                
                                                if flag < 0 and y1 <= all_bar4y[-1] - 5.08 and outer_bar4y1 - bar4y1 >= 30:
                                                    break
                                        
                                        outer_array_xy_coord.append(outer_ba_xy)
                                        all_add_position.append(outer_ba_xy)
                                        outer_ba_info = {"SIG4X1": outer_bar4x1,"SIG4X2": outer_bar4x2,
                                                         "SIG4Y1": outer_bar4y1,"SIG4Y2": outer_bar4y2,}
                                        dic_uploading_info[mrp_name].update(outer_ba_info)
                                        
                                        outer_ba_erp_info = {"TC_AAC235": outer_bar4x1,"TC_AAC237": outer_bar4x2,
                                                             "TC_AAC236": outer_bar4y1,"TC_AAC238": outer_bar4y2,}
                                        dic_uploading_erp_info[mrp_name].update(outer_ba_erp_info)                                        
            
            if dic_uploading_info:
                new_array_mrp_info = []
                for dic_info in self.array_mrp_info:
                    mrp_name = dic_info["MRPNAME"]
                    dic_info.update(dic_uploading_info[mrp_name])
                    dic_info["CAM_NOTES"] = defender_type
                    dic_info["TARGET_DESIGNREGION"] = add_to_edge.encode("utf8")
                    if self.outer_target_position:                        
                        dic_info["CAM_NOTES"] = defender_type # + " ".join(self.dic_outer_target_info.keys())                        
                        if self.dic_outer_target_info.has_key(mrp_name):
                            dic_info["Has_Outer4Target"] = "1"
                        
                    new_array_mrp_info.append(dic_info)
                    
                self.calc_bd_target_info(all_add_position, array_xy_coord_all,
                                         flag, add_to_edge, f_xmax, f_ymax,
                                         dic_uploading_info)
                
                self.uploading_data(self.jobname, new_array_mrp_info)                    
                self.ui.set_model_data(1, new_array_mrp_info, ["JOB_NAME", "MRPNAME",
                                                               "BAR4X1", "BAR4Y1", "BAR4X2", "BAR4Y2",
                                                               "BAR3X", "BAR3Y",
                                                               "SIG4X1", "SIG4Y1", "SIG4X2", "SIG4Y2",
                                                               "FROMLAY", "TOLAY"])                
                self.ui.exec_()

            if "-lyh" in self.jobname:                
                step.open()
                step.removeLayer("bk_area")
                step.createLayer("bk_area")
                step.clearAll()
                step.display("bk_area")
                i = 0
                # step.PAUSE(str(outer_array_xy_coord))
                for x, y in res[0][:len(self.array_mrp_info)] + outer_array_xy_coord:
                    step.addPad(x, y, "hdi1-bat")
                    i += 1
                    step.addText(x, y, str(i), 1.5, 2, 0.6666)
                    # if add_to_edge == u"短边":
                    # step.addPad(x, y-2, "hdi1-bat")
                    
        else:
            log += u"\n靶标坐标位置自动计算异常，找不到合适的坐标区域，请使用4.6 手动选择加长边或短边，\n此方式靶标会超距长边40mm区域，请务必反馈领导判断！"
            if manul_select:
                log = u"警告:手动选择 {0} 区域无法添加靶标，请选择 系统判断 来计算靶标！".format(add_to_edge)
            
            
        if log:
            
            try:
                uploadinglog(__credits__, log, self.stepname, GEN_USER=top.getUser())
            except:
                pass
            
        return log
    
    def calc_bd_target_info(self, all_add_position,
                            array_xy_coord_all,
                            flag,
                            add_to_edge,
                            f_xmax,
                            f_ymax, 
                            dic_uploading_target_info={}):
        """计算背钻靶距信息"""
        array_bd_mrp_info = get_ks_bd_target_info(self.jobname.upper())
        if not array_bd_mrp_info:
            return
        
        array_bd_mrp_info_detail = get_ks_bd_target_info_detail(self.jobname.upper())
        dic_exists_target_info = {}
        dic_mrp_same_target_info = {}# 同一层次共用靶记录
        num = 0
        for i, dic_info in enumerate(sorted(array_bd_mrp_info, key=lambda x: x["PROCESS_LEVEL"] * -1)):
            mrp_name = dic_info["MRP_NAME"]
            drill_layer = dic_info["DRILL_LAYER_"]
            if dic_exists_target_info.has_key(drill_layer):
                dic_info["TARGET_X1"] = dic_exists_target_info[drill_layer]["TARGET_X1"]
                dic_info["TARGET_X2"] = dic_exists_target_info[drill_layer]["TARGET_X2"]
                dic_info["TARGET_Y1"] = dic_exists_target_info[drill_layer]["TARGET_Y1"]
                dic_info["TARGET_Y2"] = dic_exists_target_info[drill_layer]["TARGET_Y2"]
                continue
            
            if not dic_mrp_same_target_info.has_key(mrp_name):                
                dic_mrp_same_target_info[mrp_name] = []
                
            if dic_info["DRILL_TYPE"] == "Backdrill":
                has_drl_layer = [x["ODB_DRILL_NAME"] for x in array_bd_mrp_info_detail
                                 if x["DRILL_TYPE"] == "Mechanical"
                                 and x["MRP_NAME"] == mrp_name]
                if not has_drl_layer:
                    if dic_mrp_same_target_info[mrp_name] and drill_layer not in dic_mrp_same_target_info[mrp_name]:
                        # 同一层次有多个背钻及控深的情况 在添加一套靶距
                        pass
                    else:
                        dic_info["TARGET_X1"] = dic_uploading_target_info[mrp_name]["BAR4X1"]
                        dic_info["TARGET_X2"] = dic_uploading_target_info[mrp_name]["BAR4X2"]
                        dic_info["TARGET_Y1"] = dic_uploading_target_info[mrp_name]["BAR4Y1"]
                        dic_info["TARGET_Y2"] = dic_uploading_target_info[mrp_name]["BAR4Y2"]
                        dic_info["CAM_NOTES"] = u"共用机械靶孔".encode("utf8")
                        dic_mrp_same_target_info[mrp_name].append(drill_layer)
                        continue
                    
            else:
                has_drl_layer = [x["ODB_DRILL_NAME"] for x in array_bd_mrp_info_detail                                 
                                 if x["DRILL_TYPE"] == "Mechanical"
                                 and x["MRP_NAME"] == mrp_name
                                 and x["TYPE_T"] in '\"PTH\",\"Via\",\"Micro Via\",\"Plated Slot\"'
                                 and x["PCB_COUNT"] > 0]                
                if not has_drl_layer:
                    if dic_mrp_same_target_info[mrp_name] and drill_layer not in dic_mrp_same_target_info[mrp_name]:
                        # 同一层次有多个背钻及控深的情况 在添加一套靶距
                        pass
                    else:                    
                        dic_info["TARGET_X1"] = dic_uploading_target_info[mrp_name]["BAR4X1"]
                        dic_info["TARGET_X2"] = dic_uploading_target_info[mrp_name]["BAR4X2"]
                        dic_info["TARGET_Y1"] = dic_uploading_target_info[mrp_name]["BAR4Y1"]
                        dic_info["TARGET_Y2"] = dic_uploading_target_info[mrp_name]["BAR4Y2"]
                        dic_info["CAM_NOTES"] = u"共用机械靶孔".encode("utf8")
                        dic_mrp_same_target_info[mrp_name].append(drill_layer)
                        continue
                
            x, y = all_add_position[0]
            for t, xy in enumerate(array_xy_coord_all):
                x1, y1 = xy
                is_continue = False
                for x2, y2 in all_add_position:
                    if max(x1-5.08*0.5, x2-5.08*0.5) < min(x1+5.08*0.5, x2+5.08*0.5) and \
                       max(y1-5.08*0.5, y2-5.08*0.5) < min(y1+5.08*0.5, y2+5.08*0.5):
                        is_continue = True
                        break
                    
                if is_continue:
                    continue
                    
                if xy in all_add_position:
                    continue
                
                if add_to_edge == u"短边":
                    if y1 == y:                                                
                        outer_bar4x1 = f_xmax - x1 * 2
                        outer_bar4x2 = f_xmax - x1 * 2
                        outer_bar4y1 = f_ymax - y1 * 2
                        outer_bar4y2 = outer_bar4y1 + 2
                        dic_info["TARGET_X1"] = outer_bar4x1
                        dic_info["TARGET_X2"] = outer_bar4x2
                        dic_info["TARGET_Y1"] = outer_bar4y1
                        dic_info["TARGET_Y2"] = outer_bar4y2
                        all_add_position.append(xy)
                        break
                    
                else:
                    if x1 == x:                                                
                        outer_bar4x1 = f_xmax - x1 * 2
                        outer_bar4x2 = f_xmax - x1 * 2
                        outer_bar4y1 = f_ymax - y1 * 2
                        outer_bar4y2 = outer_bar4y1 + 2
                        dic_info["TARGET_X1"] = outer_bar4x1
                        dic_info["TARGET_X2"] = outer_bar4x2
                        dic_info["TARGET_Y1"] = outer_bar4y1
                        dic_info["TARGET_Y2"] = outer_bar4y2
                        all_add_position.append(xy)
                        break
            else:
                if add_to_edge == u"短边":                    
                    if flag > 1:
                        x1 = max([x2 for x2, y2 in all_add_position]) + 5.08 * (num + 1)
                    else:
                        x1 = max([x2 for x2, y2 in all_add_position]) + (len(array_bd_mrp_info) - num) * 5.08
                    y1 = y
                else:
                    if flag > 1:
                        y1 = max([y2 for x2, y2 in all_add_position]) + 5.08 * (num + 1)
                    else:
                        y1 = max([y2 for x2, y2 in all_add_position]) + (len(array_bd_mrp_info) - num) * 5.08
                    x1 = y                    
                    
                outer_bar4x1 = f_xmax - x1 * 2
                outer_bar4x2 = f_xmax - x1 * 2
                outer_bar4y1 = f_ymax - y1 * 2
                outer_bar4y2 = outer_bar4y1 + 2
                dic_info["TARGET_X1"] = outer_bar4x1
                dic_info["TARGET_X2"] = outer_bar4x2
                dic_info["TARGET_Y1"] = outer_bar4y1
                dic_info["TARGET_Y2"] = outer_bar4y2
                dic_info["CAM_NOTES"] = u"超范围".encode("utf8")
                all_add_position.append((x1, y1))
            
                num += 1
                
            dic_exists_target_info[drill_layer] = {"TARGET_X1": dic_info["TARGET_X1"],
                                                   "TARGET_X2": dic_info["TARGET_X2"],
                                                   "TARGET_Y1": dic_info["TARGET_Y1"],
                                                   "TARGET_Y2": dic_info["TARGET_Y2"],}
                
        self.uploading_data(self.jobname, array_bd_mrp_info, database="hdi_engineering.incam_drillprogram_info_temp")
        #因南通网络有延时 这里需等待0.5s
        time.sleep(0.5)
        array_bd_mrp_info = get_mysql_ks_bd_target_info(self.jobname, "hdi_engineering.incam_drillprogram_info_temp")
        
        self.ui.set_model_data(2, array_bd_mrp_info, ["JOB_NAME", "MRP_NAME", "ODB_DRILL_NAME",
                                                      "TARGET_X1", "TARGET_Y1", "TARGET_X2", "TARGET_Y2",
                                                      "START_INDEX", "END_INDEX", "ID"])        
                    
    def uploading_data(self, jobname, arraylist_data, database="hdi_engineering.incam_process_info_temp"):
        
        sql = "select * from {1} where job_name = '{0}'"
        data_info = conn.SQL_EXECUTE(dbc_m, sql.format(jobname.split("-")[0], database))
        if data_info:
            sql = "delete from {1} where job_name = '{0}'"
            conn.SQL_EXECUTE(dbc_m, sql.format(jobname.split("-")[0], database))
            
        for dic_info in arraylist_data:
            arraylist_key = []
            arraylist_value = []
            for key, value in dic_info.iteritems():
                arraylist_key.append(key)
                if isinstance(value, (float)):
                    if key in ["PNLXINCH", "PNLYINCH"]:
                        arraylist_value.append(str(value))
                    else:
                        arraylist_value.append("%.3f"%(value))
                else:
                    arraylist_value.append(str(value))

            insert_sql = u"insert into {2} ({0}) values ({1})"
            conn.SQL_EXECUTE(dbc_m, insert_sql.format(",".join(arraylist_key),",".join(["%s"]*len(arraylist_key)), database), arraylist_value)        
        
    def get_add_target_area(self, add_to_edge=u"短边", defender_same_size=True, check_avoid_hole_area=True):
        """获取添加靶标区域"""
        #只计算左下角 其他区域可以镜像即可
        # 1.避开电镀夹头区域 从中心开始计算 range_list=[(0, 45), (60, 70), (160, 225)]
        # 夹头区域改为 0-80 155-225 左右两边35 20230612 by lyh
        # 2.靶标中心距板边的距离控制在20-110mm范围内（优先保证一压的位置），优先拉大靶距        
        
        step = self.step
        step.COM("units,type=mm")        
        sr_xmin,sr_ymin,sr_xmax,sr_ymax = get_sr_limits(step)
        #all_x = [x1 for x1, y1, x2, y2 in rect_area]
        #all_x += [x2 for x1, y1, x2, y2 in rect_area]
        #all_y = [y1 for x1, y1, x2, y2 in rect_area]
        #all_y += [y1 for x1, y1, x2, y2 in rect_area]
        #sr_ymin = min(all_y)
        #sr_xmin = min(all_x)
        #if "-lyh" in job.name:
            #step.PAUSE(str([sr_xmin,sr_ymin,sr_xmax,sr_ymax]))
            
        same_job_info_path = os.path.join(job.dbpath, "user", "same_size_info.json")
        
        avoid_area = []
                
        self.outer_target_num = len(self.dic_outer_target_info) + 2 if self.dic_outer_target_info else 0
        self.outer_target_position = []
        outer_process_num = None
        for i, dic_info in enumerate(sorted(self.array_mrp_info, key=lambda x: x["PROCESS_NUM"] * -1)): 
            mrp_name = dic_info["MRPNAME"]
            rout_x = dic_info["PNLROUTX"] * 25.4
            rout_y = dic_info["PNLROUTY"] * 25.4
            panel_x = dic_info["PNLXINCH"] * 25.4
            panel_y = dic_info["PNLYINCH"] * 25.4
            
            if self.dic_outer_target_info.has_key(mrp_name):
                self.outer_target_position.append(i+1)
                
            if "-" not in dic_info["MRPNAME"]:
                outer_process_num = dic_info["PROCESS_NUM"]
                
                if rout_x == 0 and rout_y == 0:
                    # 双面板 直接返回0 0
                    return [(0, 0)], None ,"defender success"                   
        
        for dic_info in self.array_mrp_info:
            rout_x = dic_info["PNLROUTX"] * 25.4
            rout_y = dic_info["PNLROUTY"] * 25.4
            panel_x = dic_info["PNLXINCH"] * 25.4
            panel_y = dic_info["PNLYINCH"] * 25.4
            lb_x = (panel_x - rout_x) * 0.5
            lb_y = (panel_y - rout_y) * 0.5       
            
            #if "-" in dic_info["MRPNAME"]:
                #continue
            # 实际上只要计算外层的前一次压合即可
            if len(self.array_mrp_info) == 1:
                # 一次压合的 按芯板上来计算
                lb_x = 0
                lb_y = 0
            else:
                if dic_info["PROCESS_NUM"] != outer_process_num - 1:
                    continue            
            
            f_xmin, f_ymin, f_xmax, f_ymax = 0, 0, panel_x, panel_y
            
            arraylist_same_size_info = self.get_same_size_jobs_info(self.jobname, panel_x, panel_y)
            #计算只保留最新版本
            new_arraylist_same_size_info = []
            jobnames = [x["JOB_NAME"][:11] for x in arraylist_same_size_info]
            exists_check_jobs = []
            for i, same_size_info in enumerate(arraylist_same_size_info):
                name = same_size_info["JOB_NAME"][:11]
                if name in exists_check_jobs:
                    continue
                
                if name in jobnames[i+1:] and name not in exists_check_jobs:
                    find_job_info = sorted([x for x in arraylist_same_size_info if x["JOB_NAME"][:11] == name], key=lambda t: t["JOB_NAME"])
                    # print find_job_info[-1]["JOB_NAME"], [x["JOB_NAME"] for x in find_job_info]
                    new_arraylist_same_size_info.append(find_job_info[-1])
                    exists_check_jobs.append(name)
                else:
                    new_arraylist_same_size_info.append(same_size_info)
                    exists_check_jobs.append(name)                    
            # step.PAUSE(str([lb_x, lb_y, outer_process_num]))
            try:
                with open(same_job_info_path, "w") as f:
                    f.write(str(new_arraylist_same_size_info))
            except Exception, e:
                print e            
                
            if "-lyh" in self.jobname:                
                step.clearAll()
                if add_to_edge == u"短边":
                    step.removeLayer("jiatou_tmp")
                    step.createLayer("jiatou_tmp")
                    
                if not step.isLayer("jiatou_tmp"):
                    step.createLayer("jiatou_tmp")
                    
                step.affect("jiatou_tmp")
                
                for x1, y1, x2, y2 in self.array_list_ganmo_area:
                    x1, y1, x2, y2 = x1 + 2.5, y1 + 2.5, x2 - 2.5, y2 - 2.5
                    step.addLine(x1, y1, x2, y1, "r127")
                    step.addLine(x2, y1, x2, y2, "r127")
                    step.addLine(x2, y2, x1, y2, "r127")
                    step.addLine(x1, y2, x1, y1, "r127")                
                
            #避开夹头区域
            if dic_info["PNLROUTY"] < 24.5:
                # range_list=[(0, 45), (60, 70), (160, 225)]
                range_list = [(2.5, 80), (155, 225), ((f_xmax+f_xmin)*0.5 - lb_y - 35, (f_xmax+f_xmin)*0.5 - lb_y)]
                # y方向锣边后小于等于24.5的夹短边
                for cur_range in range_list:
                    for cur_dis_y in [(0, 10+lb_y), (f_ymax, f_ymax - 10-lb_y)]:
                        y1 = cur_dis_y[0]
                        y2 = cur_dis_y[1]
                        for cur_dis_x in [((f_xmax+f_xmin)*0.5 + cur_range[0],
                                           (f_xmax+f_xmin)*0.5 + cur_range[1]),
                                          ((f_xmax+f_xmin)*0.5 - cur_range[1],
                                           (f_xmax+f_xmin)*0.5 - cur_range[0])]:
                            x1 = cur_dis_x[0]
                            x2 = cur_dis_x[1]                        
                            # 因y方向要错开2mm 这里夹头要加2
                            avoid_area.append([x1, y1,x2, y2 + 2])
            else:
                # range_list=[(0, 45), (60, 70), (160, 225)]
                range_list = [(2.5, 80), (155, 225), ((f_ymax+f_ymin)*0.5 - lb_x - 37.5, (f_ymax+f_ymin)*0.5 - lb_x)]
                # y方向锣边后大于24.5的夹长边
                for cur_range in range_list:
                    for cur_dis_x in [(0, 10+lb_x), (f_xmax, f_xmax - 10 - lb_x)]:
                        x1 = cur_dis_x[0]
                        x2 = cur_dis_x[1]
                        for cur_dis_y in [((f_ymax+f_ymin)*0.5 + cur_range[0],
                                           (f_ymax+f_ymin)*0.5 + cur_range[1]),
                                          ((f_ymax+f_ymin)*0.5 - cur_range[1],
                                           (f_ymax+f_ymin)*0.5 - cur_range[0])]:
                            y1 = cur_dis_y[0]
                            y2 = cur_dis_y[1]
                            # 因y方向要错开2mm 这里夹头要加2
                            avoid_area.append([x1, y1 - 2,x2, y2 + 2])                
                    
            find_xy = []
            if add_to_edge == u"短边":
                
                avoid_hole_area = self.get_drill_layer_hole_position(sr_xmin, sr_ymin, sr_xmax, sr_ymax, 70, 6)
                #不防呆后 在次计算板内6mm区域是否有孔 把这些孔的区域计算出来 靶标边缘距板内改为1mm
                if check_avoid_hole_area:                    
                    avoid_area += avoid_hole_area
                
                if not defender_same_size:
                    to_sr_size = 5.08 * 0.5 + 1                 
                else:
                    to_sr_size = 5.6
                    
                if "-lyh" in self.jobname:                
                    step.clearAll()
                    step.affect("jiatou_tmp")                    
                    
                # 加在短边的情况添加位置为20-100
                # max_add_y = 110
                # http://192.168.2.120:82/zentao/story-view-6309.html 工艺要求改为70
                max_add_y = 70
                min_add_y = 20
                
                # 人工选择加长边还是短板不考虑避开区域 用户加完后手动调整
                if "manual_set_position" in sys.argv[1:]:                    
                    avoid_area = []
                    if not defender_same_size:
                        self.array_list_ganmo_area = []                

                # 避开距成型线 及距板外的区域
                avoid_area.append([lb_x + min_add_y - 5.08 * 0.5, sr_ymin - to_sr_size + 5.08 * 0.5,
                                   lb_x + max_add_y + 5.08 * 0.5, sr_ymin])
                # 因y方向要错开2mm 这里距板边要加2
                avoid_area.append([lb_x + min_add_y - 5.08 * 0.5, f_ymin + lb_y,
                                   lb_x + max_add_y + 5.08 * 0.5, f_ymin + lb_y + 6.5 - 5.08 * 0.5 + 2])
                
                #if "-lyh" in self.jobname:
                    #step.PAUSE(str([avoid_area, to_sr_size]))                
            
                for y in numpy.arange(sr_ymin - to_sr_size, f_ymin+6.5, -1):                
                        for x in numpy.arange(lb_x + min_add_y, lb_x + max_add_y, 0.1):
                            x1 = x - 5.08 * 0.5
                            y1 = y - 5.08 * 0.5
                            x2 = x + 5.08 * 0.5
                            y2 = y + 5.08 * 0.5
                            # 两个区间有交集的 区域不添加
                            for rt_xmin, rt_ymin, rt_xmax, rt_ymax in avoid_area:
                                #if [rt_xmin, rt_ymin, rt_xmax, rt_ymax] in avoid_hole_area:
                                    ## 周涌通知 避开板内孔按靶孔中心来计算20231128 by lyh
                                    #if rt_xmin< x < rt_xmax and rt_ymin< y < rt_ymax:
                                        #break
                                #else:
                                if max(x1, rt_xmin) < min(x2, rt_xmax) and \
                                   max(y1, rt_ymin) < min(y2, rt_ymax):
                                    break
                            else:
                                # 检测靶标中心是否在干膜5mm区域内 20230808 by lyh
                                for gm_xmin, gm_ymin, gm_xmax, gm_ymax in self.array_list_ganmo_area:
                                    if gm_xmin + 2.5 > x1 or gm_ymin + 2.5 > y1 - 2:
                                        break
                                else:   
                                    find_xy.append([x, y])
                                    
                #if "-lyh" in job.name:
                    #if "-lyh" in self.jobname:
                        #for x1, y1, x2, y2 in avoid_area:
                            #step.addRectangle(x1, y1, x2, y2)                    
                    #step.PAUSE(str([len(arraylist_same_size_info), len(find_xy), 1]))
                    
                if not find_xy and not defender_same_size:
                    #avoid_area[-1] =[lb_x + min_add_y - 5.08 * 0.5, f_ymin + lb_y,
                                   #lb_x + max_add_y + 5.08 * 0.5, f_ymin + lb_y + 4 - 5.08 * 0.5 + 2]
                    
                    ## 有些型号溜边很少的 距板外改为4 优先保证距板内的间距5.6
                    #for y in numpy.arange(f_ymin+4, sr_ymin - to_sr_size, 1):                
                            #for x in numpy.arange(lb_x + min_add_y, lb_x + max_add_y, 0.1):
                                #x1 = x - 5.08 * 0.5
                                #y1 = y - 5.08 * 0.5
                                #x2 = x + 5.08 * 0.5
                                #y2 = y + 5.08 * 0.5  
                                ## 两个区间有交集的 区域不添加                            
                                #for rt_xmin, rt_ymin, rt_xmax, rt_ymax in avoid_area:                            
                                    #if max(x1, rt_xmin) < min(x2, rt_xmax) and \
                                       #max(y1, rt_ymin) < min(y2, rt_ymax):
                                        #break
                                #else:
                                    #find_xy.append([x, y])
                                    
                    #if not find_xy:
                    # 有些型号留边只有8mm多 这种再优化下 居中设计
                    midle_size = (sr_ymin - lb_y - 5.08 - 2) * 0.5
                    avoid_area[-2] = [lb_x + min_add_y - 5.08 * 0.5, sr_ymin - midle_size + 0.5,
                               lb_x + max_add_y + 5.08 * 0.5, sr_ymin]                        
                    avoid_area[-1] = [lb_x + min_add_y - 5.08 * 0.5, f_ymin + lb_y,
                                      lb_x + max_add_y + 5.08 * 0.5, f_ymin + lb_y + midle_size - 0.5 + 2]
                    
                    for y in numpy.arange(sr_ymin - midle_size, f_ymin+midle_size, -1):                
                            for x in numpy.arange(lb_x + min_add_y, lb_x + max_add_y, 0.1):
                                x1 = x - 5.08 * 0.5
                                y1 = y - 5.08 * 0.5
                                x2 = x + 5.08 * 0.5
                                y2 = y + 5.08 * 0.5  
                                # 两个区间有交集的 区域不添加                            
                                for rt_xmin, rt_ymin, rt_xmax, rt_ymax in avoid_area:
                                    #if [rt_xmin, rt_ymin, rt_xmax, rt_ymax] in avoid_hole_area:
                                        ## 周涌通知 避开板内孔按靶孔中心来计算20231128 by lyh
                                        #if rt_xmin< x < rt_xmax and rt_ymin< y < rt_ymax:
                                            #break
                                    #else:                                    
                                    if max(x1, rt_xmin) < min(x2, rt_xmax) and \
                                       max(y1, rt_ymin) < min(y2, rt_ymax):
                                        break
                                else:
                                    # 检测靶标中心是否在干膜5mm区域内 20230808 by lyh
                                    for gm_xmin, gm_ymin, gm_xmax, gm_ymax in self.array_list_ganmo_area:
                                        if gm_xmin + 2.5 > x1 or gm_ymin + 2.5 > y1 - 2:
                                            break
                                    else:                                     
                                        find_xy.append([x, y])
                                        
                if "-lyh" in self.jobname:
                    for x1, y1, x2, y2 in avoid_area:
                        step.addRectangle(x1, y1, x2, y2)
                        
                all_x = [x for x,y in find_xy]
                all_y = [y for x,y in find_xy]
                
                #if "-lyh" in job.name:
                    #for x1, y1 in find_xy:
                        #step.addPad(x1, y1, "hdi1-bat")
                    #step.PAUSE("1111")
                
                if defender_same_size:
                    # 相同尺寸防呆 先找出起始位置 然后计算此位置后的数量满足压合次数
                    # 找不到的就按不防呆来处理                    
                    new_array_xy = []
                    for x, y in sorted(find_xy, key=lambda t: t[1]):
                        bar4x1 = f_xmax - x * 2
                        bar4y1 = f_ymax - y * 2
                        if bar4y1 + 2 >= 600:
                            continue
                        
                        if f_ymax > 525 and bar4y1 < 520:
                            continue
                        
                        if sr_ymin - lb_y - 12 - to_sr_size + 5.08 * 0.5  > 5.08 + 1:
                            # 当留边区域够两排位置时 优先考虑加在夹头上方 （夹头两侧也有区域但后续分配区域不方便）
                            if y - 5.08 *0.5 < lb_y + 12:
                                continue                            
                            
                        for dic_target_size in new_arraylist_same_size_info:
                            target_x1 = dic_target_size["TARGET_X1"]
                            target_y1 = dic_target_size["TARGET_Y1"]

                            if abs(bar4y1 - target_y1) < 1 and abs(bar4x1 - target_x1) < 1:
                                break
                        else:
                            new_array_xy = self.get_target_coordinte_num_duan(x, y, find_xy, all_x)
                            if new_array_xy:                                    
                                break
                            
                        # http://192.168.2.120:82/zentao/story-view-6141.html
                        if not new_array_xy:
                            # 优先保证与WIP在线板防呆，其次2年内料号防呆，再次1年内料号防呆。
                            # 筛选2年内的情况
                            for dic_target_size in new_arraylist_same_size_info:
                                job_create_time = dic_job_date.get(dic_target_size["JOB_NAME"], datetime.datetime.now())
                                timestamp = time.mktime(job_create_time.timetuple()) 
                                diff_time = time.time() - timestamp
                                if diff_time / (24 * 3600) > 720:
                                    continue
                                
                                target_x1 = dic_target_size["TARGET_X1"]
                                target_y1 = dic_target_size["TARGET_Y1"]
    
                                if abs(bar4y1 - target_y1) < 1 and abs(bar4x1 - target_x1) < 1:
                                    break
                            else:
                                new_array_xy = self.get_target_coordinte_num_duan(x, y, find_xy, all_x)
                                if new_array_xy:                                    
                                    break
                                
                            if not new_array_xy:
                                # 筛选1年内的情况
                                for dic_target_size in new_arraylist_same_size_info:
                                    job_create_time = dic_job_date.get(dic_target_size["JOB_NAME"], datetime.datetime.now())
                                    timestamp = time.mktime(job_create_time.timetuple()) 
                                    diff_time = time.time() - timestamp
                                    if diff_time / (24 * 3600) > 360:
                                        continue
                                    
                                    target_x1 = dic_target_size["TARGET_X1"]
                                    target_y1 = dic_target_size["TARGET_Y1"]
        
                                    if abs(bar4y1 - target_y1) < 1 and abs(bar4x1 - target_x1) < 1:
                                        break
                                else:
                                    new_array_xy = self.get_target_coordinte_num_duan(x, y, find_xy, all_x)
                                    if new_array_xy:                                    
                                        break
                    
                    # step.PAUSE(str([len(new_arraylist_same_size_info), new_array_xy,bar4x1,bar4y1, 1]))
                    if new_array_xy:
                        return new_array_xy, find_xy, "defender true"     
                    else:
                        if all_y:
                            for y2 in sorted(list(set(all_y))):                            
                                new_array_xy =[]
                                for x1, y1 in sorted(find_xy, key=lambda t: t[1]):
                                    if y1 == y2:

                                        if sr_ymin - lb_y - 12 - to_sr_size + 5.08 * 0.5 > 5.08 + 1:
                                            # 当留边区域够两排位置时 优先考虑加在夹头上方 （夹头两侧也有区域但后续分配区域不方便）
                                            if y1 - 5.08 *0.5 < lb_y + 12:
                                                continue
                                        
                                        new_array_xy = self.get_target_coordinte_num_duan(x1, y1, find_xy, all_x)
                                        if new_array_xy:                                    
                                            break                                     
                                        
                                if new_array_xy:
                                    return new_array_xy, find_xy, "defender false"                               
                else:
                    if all_y:
                        for y2 in sorted(list(set(all_y))):                            
                            new_array_xy =[]
                            for x1, y1 in sorted(find_xy, key=lambda t: t[1]):
                                if y1 == y2:
    
                                    if sr_ymin - lb_y - 12 - to_sr_size + 5.08 * 0.5  > 5.08 + 1:
                                        # 当留边区域够两排位置时 优先考虑加在夹头上方 （夹头两侧也有区域但后续分配区域不方便）
                                        if y1 - 5.08 *0.5 < lb_y + 12:
                                            continue
                                    
                                    new_array_xy = self.get_target_coordinte_num_duan(x1, y1, find_xy, all_x)
                                    if new_array_xy:                                    
                                        break                                     
                                    
                            if new_array_xy:
                                return new_array_xy, find_xy , "defender false"                                    
                    
            if add_to_edge == u"长边":
                
                avoid_hole_area = self.get_drill_layer_hole_position(sr_xmin, sr_ymin, sr_xmax, sr_ymax, 6, 70)
                #不防呆后 在次计算板内6mm区域是否有孔 把这些孔的区域计算出来 靶标边缘距板内改为1mm
                if check_avoid_hole_area:
                    avoid_area += avoid_hole_area
                    
                if not defender_same_size:
                    to_sr_size = 5.08 * 0.5 + 1                 
                else:
                    to_sr_size = 5.6
                    
                if "-lyh" in self.jobname:                
                    step.clearAll()
                    step.affect("jiatou_tmp")                      
                    
                # if f_xmax > 622.3 or f_ymax > 622.3:
                if (len(self.core_mrp_info) >= 2 or (f_xmax <= 622.3 and f_ymax <= 622.3)):                    
                    # 彭课通知 短边加不下的情况 加到长边位置为10-40
                    if "-test" in job.name:
                        max_add_y = 70
                    else:
                        max_add_y = 40 # if len(self.array_mrp_info) <= 4 else 60
                    min_add_y = 10
                else:
                    # 本身加在长边的情况添加位置为20-100
                    # max_add_y = 110
                    # http://192.168.2.120:82/zentao/story-view-6309.html 工艺要求改为70
                    max_add_y = 70                    
                    min_add_y = 20                    
                    
                # 人工选择加长边还是短板不考虑避开区域 用户加完后手动调整
                if "manual_set_position" in sys.argv[1:]:                    
                    avoid_area = []
                    if not defender_same_size:
                        self.array_list_ganmo_area = []                    
                    
                # step.PAUSE(str([min_add_y, max_add_y, defender_same_size]))
                # 避开距成型线 及距板外的区域
                avoid_area.append([sr_xmin - to_sr_size + 5.08 * 0.5, lb_y + min_add_y - 5.08 * 0.5, 
                                   sr_xmin, lb_y + max_add_y + 5.08 * 0.5])
                avoid_area.append([f_xmin + lb_x, lb_y + min_add_y - 5.08 * 0.5, 
                                   f_xmin + lb_x + 6.5 - 5.08 * 0.5, lb_y + max_add_y + 5.08 * 0.5])                                
            
                for x in numpy.arange(sr_xmin - to_sr_size, f_xmin+6.5, -1):                
                        for y in numpy.arange(lb_y + min_add_y+2, lb_y + max_add_y, 0.1):
                            x1 = x - 5.08 * 0.5
                            y1 = y - 5.08 * 0.5
                            x2 = x + 5.08 * 0.5
                            y2 = y + 5.08 * 0.5  
                            # 两个区间有交集的 区域不添加                            
                            for rt_xmin, rt_ymin, rt_xmax, rt_ymax in avoid_area:
                                #if [rt_xmin, rt_ymin, rt_xmax, rt_ymax] in avoid_hole_area:
                                    ## 周涌通知 避开板内孔按靶孔中心来计算20231128 by lyh
                                    #if rt_xmin< x < rt_xmax and rt_ymin< y < rt_ymax:
                                        #break
                                #else:                                
                                if max(x1, rt_xmin) < min(x2, rt_xmax) and \
                                   max(y1, rt_ymin) < min(y2, rt_ymax):
                                    break
                            else:
                                # 检测靶标中心是否在干膜5mm区域内 20230808 by lyh
                                for gm_xmin, gm_ymin, gm_xmax, gm_ymax in self.array_list_ganmo_area:
                                    if gm_xmin + 2.5 > x1 or gm_ymin + 2.5 > y1 - 2:
                                        break
                                else:
                                    find_xy.append([x, y])
                                    
                #if "-lyh" in self.jobname:
                    #for x1, y1 in find_xy:
                        #step.addPad(x1, y1, "hdi1-bat")
                    #step.PAUSE("1111")
                                
                if not find_xy and not defender_same_size:
                    avoid_area[-1] = [f_xmin + lb_x, lb_y + min_add_y - 5.08 * 0.5, 
                                      f_xmin + lb_x + 4 - 5.08 * 0.5, lb_y + max_add_y + 5.08 * 0.5]                    
                    # 有些型号溜边很少的 距板外改为4 优先保证距板内的间距5.6
                    for x in numpy.arange(sr_xmin - to_sr_size, f_xmin+4, -1):                
                            for y in numpy.arange(lb_y + min_add_y+2, lb_y + max_add_y, 0.1):
                                x1 = x - 5.08 * 0.5
                                y1 = y - 5.08 * 0.5
                                x2 = x + 5.08 * 0.5
                                y2 = y + 5.08 * 0.5  
                                # 两个区间有交集的 区域不添加                            
                                for rt_xmin, rt_ymin, rt_xmax, rt_ymax in avoid_area:
                                    #if [rt_xmin, rt_ymin, rt_xmax, rt_ymax] in avoid_hole_area:
                                        ## 周涌通知 避开板内孔按靶孔中心来计算20231128 by lyh
                                        #if rt_xmin< x < rt_xmax and rt_ymin< y < rt_ymax:
                                            #break
                                    #else:                                    
                                    if max(x1, rt_xmin) < min(x2, rt_xmax) and \
                                       max(y1, rt_ymin) < min(y2, rt_ymax):
                                        break
                                else:
                                    # 检测靶标中心是否在干膜5mm区域内 20230808 by lyh
                                    for gm_xmin, gm_ymin, gm_xmax, gm_ymax in self.array_list_ganmo_area:
                                        if gm_xmin + 2.5 > x1 or gm_ymin + 2.5 > y1 - 2:
                                            break
                                    else:                                     
                                        find_xy.append([x, y])                                                              
                                    
                    if not find_xy:
                        # 有些型号留边只有8mm多 这种再优化下 居中设计
                        midle_size = (sr_xmin - lb_x - 5.08) * 0.5
                        avoid_area[-2] = [sr_xmin - midle_size + 0.5, lb_y + min_add_y - 5.08 * 0.5, 
                                           sr_xmin, lb_y + max_add_y + 5.08 * 0.5]                      
                        avoid_area[-1] = [f_xmin + lb_x, lb_y + min_add_y - 5.08 * 0.5, 
                                          f_xmin + lb_x + midle_size - 0.5, lb_y + max_add_y + 5.08 * 0.5]                    
                        for x in numpy.arange(sr_xmin - midle_size, f_xmin + midle_size, -0.1):                
                                for y in numpy.arange(lb_y + min_add_y+2, lb_y + max_add_y, 0.1):
                                    x1 = x - 5.08 * 0.5
                                    y1 = y - 5.08 * 0.5
                                    x2 = x + 5.08 * 0.5
                                    y2 = y + 5.08 * 0.5  
                                    # 两个区间有交集的 区域不添加                            
                                    for rt_xmin, rt_ymin, rt_xmax, rt_ymax in avoid_area:
                                        #if [rt_xmin, rt_ymin, rt_xmax, rt_ymax] in avoid_hole_area:
                                            ## 周涌通知 避开板内孔按靶孔中心来计算20231128 by lyh
                                            #if rt_xmin< x < rt_xmax and rt_ymin< y < rt_ymax:
                                                #break
                                        #else:                                        
                                        if max(x1, rt_xmin) < min(x2, rt_xmax) and \
                                           max(y1, rt_ymin) < min(y2, rt_ymax):
                                            break
                                    else:
                                        # 检测靶标中心是否在干膜5mm区域内 20230808 by lyh
                                        for gm_xmin, gm_ymin, gm_xmax, gm_ymax in self.array_list_ganmo_area:
                                            if gm_xmin + 2.5 > x1 or gm_ymin + 2.5 > y1 - 2:
                                                break
                                        else:                                         
                                            find_xy.append([x, y])
                                        
                if "-lyh" in self.jobname:
                    for x1, y1, x2, y2 in avoid_area:
                        step.addRectangle(x1, y1, x2, y2)                   
                            
                    # step.PAUSE(str([len(arraylist_same_size_info), len(find_xy), 2]))
                    
                all_x = [x for x,y in find_xy]
                all_y = [y for x,y in find_xy]                
                if defender_same_size:
                    # 相同尺寸防呆 先找出起始位置 然后计算此位置后的数量满足压合次数
                    # 找不到的就按不防呆来处理
                    new_array_xy = []
                    # all_y = [y for x, y in find_xy]
                    for x, y in sorted(find_xy, key=lambda t: t[0]):
                        bar4x1 = f_xmax - x * 2
                        bar4y1 = f_ymax - y * 2
                        if bar4y1 + 2 >= 600:
                            continue
                        
                        if dic_info["PNLROUTY"] >= 24.5:
                            # 夹头在长边时才考虑此种情况 20230810 by lyh
                            if sr_xmin - lb_x - 12 - to_sr_size + 5.08 * 0.5  > 5.08 + 1:
                                # 当留边区域够两排位置时 优先考虑加在夹头上方 （夹头两侧也有区域但后续分配区域不方便）
                                if x - 5.08 *0.5 < lb_x + 12:
                                    continue                        

                        for dic_target_size in new_arraylist_same_size_info:
                            target_x1 = dic_target_size["TARGET_X1"]
                            target_y1 = dic_target_size["TARGET_Y1"]                        
                            if abs(bar4y1 - target_y1) < 1 and abs(bar4x1 - target_x1) < 1:
                                break
                        else:
                            new_array_xy = self.get_target_coordinte_num_chang(x, y, find_xy, all_y)
                            if new_array_xy:                                    
                                break                            
                        
                        # http://192.168.2.120:82/zentao/story-view-6141.html
                        if not new_array_xy:
                            # 优先保证与WIP在线板防呆，其次2年内料号防呆，再次1年内料号防呆。
                            # 筛选2年内的情况
                            num = 1
                            for dic_target_size in new_arraylist_same_size_info:
                                job_create_time = dic_job_date.get(dic_target_size["JOB_NAME"], datetime.datetime.now())
                                timestamp = time.mktime(job_create_time.timetuple()) 
                                diff_time = time.time() - timestamp
                                if diff_time / (24 * 3600) > 720 :
                                    num += 1
                                    continue
                                
                                target_x1 = dic_target_size["TARGET_X1"]
                                target_y1 = dic_target_size["TARGET_Y1"]                        
                                if abs(bar4y1 - target_y1) < 1 and abs(bar4x1 - target_x1) < 1:                                
                                    break
                            else:
                                new_array_xy = self.get_target_coordinte_num_chang(x, y, find_xy, all_y)
                                if new_array_xy:                                    
                                    break
                                
                            # job.PAUSE(str(num))
                            num = 1
                            if not new_array_xy:
                                # 筛选1年内的情况
                                for dic_target_size in new_arraylist_same_size_info:
                                    job_create_time = dic_job_date.get(dic_target_size["JOB_NAME"], datetime.datetime.now())
                                    timestamp = time.mktime(job_create_time.timetuple()) 
                                    diff_time = time.time() - timestamp
                                    if diff_time / (24 * 3600) > 360 :
                                        num += 1
                                        continue
                                    
                                    target_x1 = dic_target_size["TARGET_X1"]
                                    target_y1 = dic_target_size["TARGET_Y1"]                        
                                    if abs(bar4y1 - target_y1) < 1 and abs(bar4x1 - target_x1) < 1:
                                        break
                                else:
                                    new_array_xy = self.get_target_coordinte_num_chang(x, y, find_xy, all_y)
                                    if new_array_xy:                                    
                                        break
                                    
                            #job.PAUSE(str(num))
                            
                    # step.PAUSE(str([len(new_arraylist_same_size_info), len(new_array_xy), 2]))                    
                    if new_array_xy:
                        return new_array_xy, find_xy, "defender true"
                    else:
                        if all_x:                        
                            for x2 in sorted(list(set(all_x))): 
                                new_array_xy =[]
                                for x1, y1 in sorted(find_xy, key=lambda t: t[0]):
                                    if x1 == x2:                            
                                        bar4x1 = f_xmax - x1 * 2
                                        bar4y1 = f_ymax - y1 * 2
                                        #if bar4y1 + 2 >= 600:
                                            #continue
                                        if dic_info["PNLROUTY"] >= 24.5:
                                            # 夹头在长边时才考虑此种情况 20230810 by lyh                                        
                                            if sr_xmin - lb_x - 12 - to_sr_size + 5.08 * 0.5  > 5.08 + 1:
                                                # 当留边区域够两排位置时 优先考虑加在夹头上方 （夹头两侧也有区域但后续分配区域不方便）
                                                if x1 - 5.08 *0.5 < lb_x + 12:
                                                    continue                                            
                                        
                                        new_array_xy = self.get_target_coordinte_num_chang(x1, y1, find_xy, all_y)
                                        if new_array_xy:                                    
                                            break                                    
                                        
                                if new_array_xy:
                                    return new_array_xy, find_xy, "defender false"                         
                    
                else:                    
                    if all_x:                        
                        for x2 in sorted(list(set(all_x))): 
                            new_array_xy =[]
                            for x1, y1 in sorted(find_xy, key=lambda t: t[0]):
                                if x1 == x2:                            
                                    bar4x1 = f_xmax - x1 * 2
                                    bar4y1 = f_ymax - y1 * 2
                                    #if bar4y1 + 2 >= 600:
                                        #continue
                                    if dic_info["PNLROUTY"] >= 24.5:
                                        # 夹头在长边时才考虑此种情况 20230810 by lyh                                        
                                        if sr_xmin - lb_x - 12 - to_sr_size + 5.08 * 0.5  > 5.08 + 1:
                                            # 当留边区域够两排位置时 优先考虑加在夹头上方 （夹头两侧也有区域但后续分配区域不方便）
                                            if x1 - 5.08 *0.5 < lb_x + 12:
                                                continue                                        
                                    
                                    new_array_xy = self.get_target_coordinte_num_chang(x1, y1, find_xy, all_y)
                                    if new_array_xy:                                    
                                        break                                    
                                    
                            if new_array_xy:
                                return new_array_xy, find_xy, "defender false"                                
                    
        return None
    
    def get_target_coordinte_num_duan(self,x, y, find_xy, all_x):
        """计算短边的靶标数量是否符合要求"""
        #从大到小的情况 
        all_xy =[[x, y]]
        for x1, y1 in find_xy[::-1]:
            if y1 == y and x1 <= x:
                if abs(x1 - all_xy[-1][0]) >= 5.08:
                    all_xy.append([x1, y1])

        #直接计算此排的x值
        all_x = [x1 for x1, y1 in find_xy if y1 == y]
        
        if self.outer_target_position:
            if max(self.outer_target_position) == len(self.array_mrp_info):
                if len(self.dic_outer_target_info) >= 3:
                    index = 0
                if len(self.dic_outer_target_info) == 2:
                    index = 1
                else:
                    index = 2                
                if len(all_xy) >= len(self.array_mrp_info) + len(self.dic_outer_target_info) + index:
                    return all_xy
            else:
                if len(all_xy) >= len(self.array_mrp_info) + len(self.dic_outer_target_info) + 1:
                    return all_xy
        else:            
            if len(all_xy) >= len(self.array_mrp_info):
                return all_xy
        
        #if "-lyh" in job.name:
            #step=gClasses.Step(job, "panel")
            #for x, y in all_xy:                
                #step.addPad(x, y, "hdi1-bat")
            #step.PAUSE("1111")
                
        # 从小到大的情况
        all_xy =[[x, y]]
        # 有外四靶的情况
        if self.outer_target_position:
            if min(self.outer_target_position) == 1:
                if len(self.dic_outer_target_info) >= 3:
                    index = 0
                if len(self.dic_outer_target_info) == 2:
                    index = 1
                else:
                    index = 2                
                if x - min(all_x) < (len(self.dic_outer_target_info) + index) * 5.08:
                    return []
            else:
                if x - min(all_x) < (len(self.dic_outer_target_info) + 1) * 5.08:
                    return []
                
        for x1, y1 in find_xy:
            if y1 == y and x1 >= x:
                if abs(x1 - all_xy[-1][0]) >= 5.08:
                    all_xy.append([x1, y1])                    

        if len(all_xy) >= len(self.array_mrp_info):
            return all_xy
        
        return []
    
    def get_target_coordinte_num_chang(self,x, y, find_xy, all_y):
        """计算长边的靶标数量是否符合要求"""

        #从大到小的情况
        all_xy =[[x, y]]                           
        for x1, y1 in find_xy[::-1]:
            if x1 == x and y1 <= y:
                if abs(y1 - all_xy[-1][1]) >= 5.08:
                    all_xy.append([x1, y1])
                    
        #直接计算此排的y值
        all_y = [y1 for x1, y1 in find_xy if x1 == x]                      

        if self.outer_target_position:
            if max(self.outer_target_position) == len(self.array_mrp_info):
                if len(self.dic_outer_target_info) >= 3:
                    index = 0
                if len(self.dic_outer_target_info) == 2:
                    index = 1
                else:
                    index = 2                 
                if len(all_xy) >= len(self.array_mrp_info) + len(self.dic_outer_target_info) + index:
                    return all_xy
            else:
                if len(all_xy) >= len(self.array_mrp_info) + len(self.dic_outer_target_info) + 1:
                    return all_xy                
        else:           
            if len(all_xy) >= len(self.array_mrp_info):
                return all_xy
            
        # 从小到大的情况
        all_xy =[[x, y]]        
        # 有外四靶的情况
        if self.outer_target_position:
            if min(self.outer_target_position) == 1:
                if len(self.dic_outer_target_info) >= 3:
                    index = 0
                if len(self.dic_outer_target_info) == 2:
                    index = 1
                else:
                    index = 2
                if abs(y - min(all_y)) < (len(self.dic_outer_target_info) + index) * 5.08:
                    return []
            else:
                if abs(y - min(all_y)) < (len(self.dic_outer_target_info) + 1) * 5.08:
                    return []

        for x1, y1 in find_xy:
            if x1 == x and y1 >= y:
                if abs(y1 - all_xy[-1][1]) >= 5.08:
                    all_xy.append([x1, y1])
                    
                       
        if len(all_xy) >= len(self.array_mrp_info):
            return all_xy
        
        return []
    
    def get_drill_layer_hole_position(self, sr_xmin,sr_ymin,sr_xmax,sr_ymax, x_size, y_size):
        """获取四个角6mm范围内的孔 全部镜像到左下角并获取避开区域
        增加埋孔层次 20230808 by lyh"""
        drl = "drl"
        step = self.step
        if not step.isLayer(drl):
            drl = "cdc"
            if not step.isLayer(drl):
                drl = "cds"
                
        select_area = []
        # 测试用 此型号先不考虑孔 用户手动移 20230908
        if "mc1810obt08a1".lower() in job.name:
            return select_area
        
        for drill_layer in [drl] + mai_drill_layers + mai_man_drill_layers:            
            if step.isLayer(drill_layer):
                # layer_cmd = gClasses.Layer(step, drill_layer)
                step.removeLayer(drill_layer+"_tmp")
                step.flatten_layer(drill_layer, drill_layer+"_tmp")
                step.clearAll()
                step.affect(drill_layer+"_tmp")
                step.COM("sel_delete_atr,attributes=.rout_chain")   
                step.resetFilter()
                step.selectSymbol("val*", 1, 1)
                if step.featureSelected():
                    step.COM("sel_break")
                
                center_x = (sr_xmin + sr_xmax) * 0.5
                center_y = (sr_ymin + sr_ymax) * 0.5
                step.selectRectangle(sr_xmin, sr_ymax, sr_xmin+x_size, sr_ymax-y_size, intersect='yes')
                if step.featureSelected():
                    step.COM("sel_transform,mode=anchor,oper=rotate;mirror,"
                             "duplicate=no,x_anchor={0},y_anchor={1},"
                             "angle=180,x_scale=1,y_scale=1,x_offset=0,y_offset=0".format(center_x, center_y))
                    
                step.selectRectangle(sr_xmax-x_size, sr_ymax, sr_xmax, sr_ymax-y_size, intersect='yes')
                if step.featureSelected():
                    step.COM("sel_transform,mode=anchor,oper=rotate;mirror,"
                             "duplicate=no,x_anchor={0},y_anchor={1},"
                             "angle=180,x_scale=1,y_scale=1,x_offset=0,y_offset=0".format(center_x, center_y))
                    
                step.selectRectangle(sr_xmax-x_size, sr_ymin, sr_xmax, sr_ymin+y_size, intersect='yes')
                if step.featureSelected():
                    step.COM("sel_transform,mode=anchor,oper=mirror,"
                             "duplicate=no,x_anchor={0},y_anchor={1},"
                             "angle=0,x_scale=1,y_scale=1,x_offset=0,y_offset=0".format(center_x, center_y))
            
                # step.contourize()
                step.selectRectangle(sr_xmin, sr_ymin, sr_xmin+x_size, sr_ymin+y_size, intersect='yes')            
                if step.featureSelected():
                    # 改为距靶孔中心的6mm来计算 20231213
                    step.COM("sel_resize,size={0}".format(12000-5080))
                    
                    step.selectRectangle(sr_xmin, sr_ymin, sr_xmin+x_size, sr_ymin+y_size, intersect='yes')
                    if step.featureSelected():

                        layer_cmd = gClasses.Layer(step, drill_layer+"_tmp")
                        feat_obj_pad = layer_cmd.featSelOut(units="mm")["pads"]                        
                        for obj in feat_obj_pad:
                            symbol_size = float(obj.symbol[1:]) / 1000.0
                            rect = [obj.x - symbol_size * 0.5, obj.y - symbol_size * 0.5,
                                    obj.x + symbol_size * 0.5, obj.y + symbol_size * 0.5,]
                            select_area.append(rect)
                            
                        feat_obj_line = layer_cmd.featSelOut(units="mm")["lines"]
                        for obj in feat_obj_line:
                            symbol_size = float(obj.symbol[1:]) / 1000.0
                            min_x = min([obj.xe, obj.xs])
                            max_x = max([obj.xe, obj.xs])
                            min_y = min([obj.ye, obj.ys])
                            max_y = max([obj.ye, obj.ys])                        
                            rect = [min_x - symbol_size * 0.5, min_y - symbol_size * 0.5,
                                    max_x + symbol_size * 0.5, max_y + symbol_size * 0.5,]
                            select_area.append(rect) 
                    
                step.removeLayer(drill_layer+"_tmp")
            
        return select_area

    
if __name__ == "__main__":
    from create_ui_model import showMessageInfo
    
    main = get_target_distance(job.name, "panel")
    # try:        
    res = main.start_calc()
    try:
        if res:                    
            showMessageInfo(res)
    except:
        pass
    #except Exception, e:
        #try:
            #uploadinglog(__credits__, str(e), "panel", GEN_USER=top.getUser())
        #except:
            #pass         