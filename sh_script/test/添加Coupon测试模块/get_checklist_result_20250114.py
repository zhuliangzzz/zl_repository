#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2022/08/16
# @Revision     :    1.0.0
# @File         :    get_checklist_result.py
# @Software     :    PyCharm
# @Usefor       :    
# ---------------------------------------------------------#

import os
import platform
import re
import sys
from PyQt4 import QtCore, QtGui
import time

# --加载相对位置，以实现InCAM与Genesis共用
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import Oracle_DB
import genCOM_26 as genCOM
import json
from PyQt4.QtGui import *
from messageBoxPro import msgBox
from mwClass_V2 import *

from genesisPackages import  getSmallestHole_and_step

from get_erp_job_info import get_job_type, get_job_product_type

import gClasses
from genesisPackages import job, matrixInfo

array_jobtype_info = get_job_type(os.environ.get('JOB', None))
car_type = [info for info in array_jobtype_info
            if (info["JOB_PRODUCT_LEVEL1_"] and u"汽车" in info["JOB_PRODUCT_LEVEL1_"].decode("utf8"))
            or info["ES_CAR_BOARD_"] == 1]
battery_type = [info for info in array_jobtype_info
            if (info["JOB_PRODUCT_LEVEL1_"] and u"电池" in info["JOB_PRODUCT_LEVEL1_"].decode("utf8"))
            or info["ES_BATTERY_BOARD_"] == 1]

product_level_info = get_job_product_type(os.environ.get('JOB', None))
ai_server_type = [info for info in product_level_info
                  if info["PRODUCT_LEVEL_TYPE"] and
                  (u"算力" in info["PRODUCT_LEVEL_TYPE"].decode("utf8") or
                   u"服务器" in info["PRODUCT_LEVEL_TYPE"].decode("utf8"))]
check_ai_server_type = 0
if ai_server_type:
    check_ai_server_type = 1

check_car_type = 0
if os.environ.get('JOB', "").startswith("q") or car_type:
    check_car_type = 1
    
check_battery_type = 0
if battery_type:
    check_battery_type = 1
    
check_nv_type = 0
if os.environ.get('JOB', "")[1:4] in ["a86", "d10"]:
    check_nv_type = 1
    
if check_car_type or check_battery_type:
    max_laser_ar = 10
else:
    max_laser_ar = 10  


class MyApp(object):
    def __init__(self):
        global  check_nv_type
        
        self.job_name = os.environ.get('JOB')
        self.GEN = genCOM.GEN_COM()
        self.step_name = 'edit'
        self.chklist_name = 'signal_drill_check'
        if self.GEN.STEP_EXISTS(job=self.job_name,step=self.step_name) == 'no':
            sys.exit(0)
        try:
            self.job_layer_num = int(self.job_name[4:6])
        except ValueError:
            self.job_layer_num = len(self.GEN.GET_ATTR_LAYER('signal'))
        # --初始化jobsuse 目录
        if os.environ.get('JOB_USER_DIR'):
            self.userPath = os.environ.get('JOB_USER_DIR')
        else:
            self.userPath = os.path.join(os.environ.get('GENESIS_DIR'), 'fw', 'jobs', self.job_name, 'user')
        # --初始化记录文件
        self.jsonFile = 'HDI_TestCoupon.json'
        
        filepath = os.path.join(self.userPath, self.jsonFile)
        if os.path.exists(filepath):            
            with open(filepath, 'r') as f:
                self.jsonData = json.load(f)
            
            #if check_nv_type == 1:
                #check_nv_type = 0
                #if self.jsonData.get("run_test_type", None):                
                    #if self.jsonData["run_test_type"]["flj_coupon"] == "new_20241009":
                        #check_nv_type = 1
                
            # self.GEN.PAUSE(str(self.jsonData.get("run_test_type", None)))
            
        # === 镭射ring的分析结果的各项值 ===
        self.result_list = ['c_type', 'sig_layer', 'result', 'r_unit', 'hole_symbol', 'pad_symbol', 'r_show', 'r_line_xs',
                            'r_line_ys', 'r_line_xe', 'r_line_ye', 'r_disp_id', 'r_color', 'r_index']
        # lvia2c l2 253.92 micron r102 r0 SG 3.5069 0.7130775 3.578625 0.4695 2 Y
        # pth2c l9 53.5 micron r102 r0 SG 1.51002 0.7498 1.561965 0.737 2 R 33
        self.warn_list = []
        self.laser_ar_range = [{'ar_down':2.0,'ar_up':2.2,'dest_ar':2.2},
                               {'ar_down':2.2,'ar_up':2.4,'dest_ar':2.4},
                               {'ar_down':2.4,'ar_up':2.6,'dest_ar':2.6},
                               {'ar_down':2.6,'ar_up':2.8,'dest_ar':2.8},
                               {'ar_down':2.8,'ar_up':3.0,'dest_ar':3.0}]
        self.drill_layers = self.GEN.GET_ATTR_LAYER('drill')
        # === 获取 镭射层别列表 ===
        self.blind_layers = [i for i in self.drill_layers if re.match('s[1-9][0-9]?-?[1-9][0-9]?', i)]
        self.GEN.COM('get_user_name')
        self.cam_user = self.GEN.COMANS

    def run_checklist(self, stepname=None):
        gc_exist = self.GEN.DO_INFO("-t check -e %s/%s/%s -d EXISTS" % (self.job_name, stepname if stepname else self.step_name, self.chklist_name))
        if gc_exist["gEXISTS"] == 'yes':
            self.GEN.COM('chklist_delete,chklist=%s' % self.chklist_name)

        self.GEN.COM('chklist_from_lib,chklist=%s,profile=none,customer=' % self.chklist_name)
        self.GEN.COM('chklist_run,chklist=%s,nact=1,area=global,async_run=no' % self.chklist_name)

    def get_checklist_result(self,result_type=['laser_via_ar'], stepname=None):
        """
        取分析结果中的镭射ring
        :return:
        """
        all_rdict = {}

        all_result = self.GEN.INFO("-t check -e %s/%s/%s -d MEAS -o index+action=1" % (
            self.job_name, stepname if stepname else self.step_name, self.chklist_name), units='inch')
        for r_line in all_result:
            r_list = r_line.split()
            if r_list[0] in result_type:
                r_dict = dict(zip(self.result_list, r_list))
                # print r_dict
                sig_layer = r_dict['sig_layer']
                r_disp_id = r_dict['r_disp_id']
                r_value = float(r_dict['result'])
                if sig_layer not in all_rdict:
                    all_rdict[sig_layer] = {r_disp_id:[r_value]}
                else:
                    if r_disp_id in all_rdict[sig_layer]:
                        all_rdict[sig_layer][r_disp_id].append(r_value)
                    else:
                        all_rdict[sig_layer][r_disp_id] = [r_value]
        return all_rdict

    def coupon_check_run(self):

        # === 1. 获取Step 列表
        step_list = self.GEN.GET_STEP_LIST(job=self.job_name)
        # === 2. 取出所有防漏接coupon
        for c_step in step_list:
            if re.match('plus\d-floujie',c_step):
                self.step_name = c_step
                self.GEN.OPEN_STEP(self.step_name, job=self.job_name)
                self.GEN.CLEAR_LAYER()
                self.GEN.CHANGE_UNITS('inch')
                self.run_checklist()
                result1 = self.get_checklist_result(['lvia2c', 'pth2c'])
                blind_dict1 = self.get_disp_id(self.blind_layers, result1)
                print json.dumps(blind_dict1, indent=2)
                # result2 = self.get_checklist_result('pth2c')
                # blind_dict12 = self.get_disp_id(self.blind_layers, result2)
                # print json.dumps(blind_dict12, indent=2)

        # === 3. 循环运行chklist

        # === 4. 循环取出chklist 运行结果

    def get_disp_id(self,drill_layers, all_rdict, stepname=None):
        """
        通过分析结果，取出镭射底层的ring大小
        :param drill_layers: list 镭射层
        :param all_rdict: 分析结果
        :return:
        """
        blind_dict = {}
        dp = self.GEN.INFO("-t check -e %s/%s/%s -d MEAS_DISP_ID -o action=1,  angle_direction=ccw" % (
            self.job_name, stepname if stepname else self.step_name, self.chklist_name), units='inch')
        for d_line in dp:
            d_list = d_line.split()
            if len(d_list) == 4:
                if d_list[3] in drill_layers:
                    laser_end_layer = 'l' + d_list[3].split('-')[1]
                    if laser_end_layer == d_list[0]:
                        get_laser_ar = None
                        if laser_end_layer in all_rdict:
                            get_laser_ar = min(all_rdict[laser_end_layer].get(d_list[1], [0]))
                        dest_laser_ar = None
                        for line in self.laser_ar_range:
                            if line['ar_down'] <= get_laser_ar < line['ar_up']:
                                dest_laser_ar = line['dest_ar']
                        if not dest_laser_ar: dest_laser_ar = get_laser_ar
                        blind_dict[d_list[3]] = {'end_layer': laser_end_layer, 'disp_id': d_list[1], 'laser_ar': dest_laser_ar}
        return blind_dict

    def run(self):

        if len(self.blind_layers) == 0:
            # === 无镭射层，不进行防漏接检测 ===
            return True

        #if not os.path.exists(os.path.join(self.userPath, self.jsonFile)):
            #step_list = self.GEN.GET_STEP_LIST(job=self.job_name)
            #plus_exist = 'no'
            #for c_step in step_list:
                #if re.match('plus\d-floujie', c_step):
                    #plus_exist = 'yes'
            #if plus_exist == 'yes':
                #self.warn_list.append({
                    #'type': 'warn',
                    #'text': u'未找到最后一次的参数记录，无法比对Ring信息！'
                #})
            ## 暂时不进行防漏接的分析
            ## self.coupon_check_run()
        #else:        
        
        self.GEN.OPEN_STEP(self.step_name, job=self.job_name)
        self.GEN.CLEAR_LAYER()
        self.GEN.CHANGE_UNITS('inch')
        for drill_layer in self.blind_layers:
            self.GEN.AFFECTED_LAYER(drill_layer, "yes")
        
        if "auto_check" not in sys.argv[1:]:            
            self.GEN.COM('cur_atr_reset')
            self.GEN.COM('cur_atr_set,attribute=.drill,option=via')
            self.GEN.COM('cur_atr_set,attribute=.via_type,option=laser')
            self.GEN.COM('sel_change_atr,mode=add')
            self.GEN.COM('cur_atr_reset')
        
        self.GEN.CLEAR_LAYER()
        # === 内层分析，仅分析钻孔 分析结果
        self.run_checklist()
        all_rdict = self.get_checklist_result()
        blind_dict = self.get_disp_id(self.blind_layers, all_rdict)
        # print json.dumps(blind_dict,indent=2)
        # self.GEN.PAUSE(str(blind_dict))
        # --读取存储的记录信息
        #with open(os.path.join(self.userPath, self.jsonFile), 'r') as f:
            #self.jsonData = json.load(f)
        # 按工艺修改的防漏接模块3 为2025.1最新要求 2为2024.6月要求 1为以前的要求 最后一次以最新的规范检测20250111 by lyh
        self.warn_list_check_open = []
        if check_nv_type or check_ai_server_type:
            # NV的只能按最新的来检测 20250113 by lyh
            arraylist_mode = [3]
        else:
            arraylist_mode = [3, 2, 1, 3]
            
        for check_mode in arraylist_mode:
            self.warn_list = []
            self.warn_list_check_open = []
            dic_flj_pad_info = self.check_ring_new(check_mode)
            
            for s_layer in self.blind_layers:
                if '-' in s_layer:
                    # 层别名中带"-"
                    digt_s = int(re.split(r'[s,-]', s_layer)[1])
                    digt_e = int(re.split(r'[s,-]', s_layer)[2])
                    if s_layer in blind_dict:
                        min_ring = blind_dict[s_layer]['laser_ar']
                    # === 非芯板镭射，进行Ring检测 ===
                    #if digt_s != self.job_layer_num * 0.5:                            
                        #if s_layer in self.jsonData and s_layer not in blind_dict:
                    arraylist = getSmallestHole_and_step(self.job_name, "", s_layer, return_all_step=True)
                    mintool,stepname = sorted(arraylist, key=lambda x: x[0])[0]
                    analysis_step = "edit"
                    if s_layer not in blind_dict:
                        # 单元内没有 但coupon内有的情况
                        print("---------->", arraylist)
                        if mintool:
                            min_ring = None
                            analysis_step = None
                            for stepname in [x[1] for x in arraylist if x[0] == mintool]:
                                # 去掉厂内加的测试coupon
                                for exclude_name in ["hct-coupon", "hct_coupon", "hct_coupon_new","drill_test_coupon", 
                                                     "dzd_cp","cu-coupon","vip_coupon","qie_hole_coupon",
                                                     "coupon-qp", "floujie"]:
                                    if exclude_name.lower() in stepname:
                                        break
                                else:                                
                                    self.GEN.OPEN_STEP(stepname, job=self.job_name)
                                    self.GEN.CLEAR_LAYER()
                                    self.GEN.CHANGE_UNITS('inch')
                                    
                                    self.GEN.AFFECTED_LAYER(s_layer, "yes")
                                    if "auto_check" not in sys.argv[1:]:    
                                        self.GEN.COM('cur_atr_reset')
                                        self.GEN.COM('cur_atr_set,attribute=.drill,option=via')
                                        self.GEN.COM('cur_atr_set,attribute=.via_type,option=laser')
                                        self.GEN.COM('sel_change_atr,mode=add')
                                        self.GEN.COM('cur_atr_reset')
                                    
                                    self.run_checklist(stepname=stepname)
                                    new_all_rdict = self.get_checklist_result(stepname=stepname)
                                    new_drl_dict = self.get_disp_id([s_layer], new_all_rdict, stepname=stepname)
                                    # GEN.PAUSE(str([stepname, new_drl_dict]))
                                    for key, value in new_drl_dict.iteritems():
                                        if min_ring is None:
                                            min_ring = value["laser_ar"]
                                            analysis_step = stepname
                                        else:
                                            if value["laser_ar"] is not None and value["laser_ar"] < min_ring:
                                                min_ring = value["laser_ar"]
                                                analysis_step = stepname
                        else:
                            # 其他step都没有孔 也就是此层为空 不检测
                            continue
                        
                    # print self.jsonData[s_layer]['minRing'],'xxx',min_ring
                    if min_ring is None:
                        min_ring = 10
                        
                    if analysis_step is None:
                        continue
                        
                    #compare_tol = 0.02
                    #if min_ring > 3:
                    # 周涌通知公差全部按0.1来 20241017 by lyh
                    compare_tol = 0.1
                            
                    if min_ring > 10:
                        min_ring = 10
                    
                    # 跟跑防漏接测试模块精度保持一致 20241029 by lyh
                    min_ring = float("%.1f" % min_ring)
                    
                    for laser_drill, drill_info in dic_flj_pad_info.iteritems():
                        if s_layer == laser_drill:
                            for attr, check_size, pad1_pad2_pad3_size,flj_step in drill_info:
                                # print(attr, check_size, pad1_pad2_pad3_size)
                                if "pad1" in attr:
                                    pad_size = pad1_pad2_pad3_size[0]
                                    position = "A"
                                elif "pad2" in attr:
                                    pad_size = pad1_pad2_pad3_size[1]
                                    position = "B"
                                else:
                                    pad_size = pad1_pad2_pad3_size[2]
                                    position = "C"
                                
                                # self.GEN.PAUSE(str([s_layer, attr, check_size, pad1_pad2_pad3_size, mintool/25.4, min_ring]))
                                print([s_layer, attr, check_size, pad_size, mintool/25.4, min_ring, check_mode])
                                calc_size = round(mintool/25.4+min_ring*2 - pad_size, 2)                            
                                if abs(calc_size - check_size) > compare_tol:
                                    self.warn_list.append({
                                        'type': 'warn',
                                        'text': u'层别:%s 测试模块%s 的%s点实际Ring为:%s,%s板内分析[最小孔%.2f+最小ring%.2f*2]后计算Ring为:%s，二者不相同,相差:%.2f'
                                        % (s_layer,flj_step, position, check_size,analysis_step, mintool/25.4, min_ring, calc_size, abs(calc_size - check_size))
                                    })
                                if abs(check_size - mintool/25.4) <= 2 or check_size < mintool/25.4:
                                    self.warn_list_check_open.append({
                                        'type': 'warn',
                                        'text': u'层别:%s 测试模块%s 的%s点开窗尺寸 - 镭射孔径单边为:%.2f,工艺要求 开窗尺寸 - 镭射孔径 单边≤1.0mil时，优先优化加大板内镭射ring，无法加大提评审'
                                        % (s_layer,flj_step, position, abs(check_size - mintool/25.4) *0.5)
                                    })
                                if check_size < mintool/25.4:
                                    self.warn_list_check_open.append({
                                        'type': 'warn',
                                        'text': u'层别:%s 测试模块%s 的%s点开窗尺寸%.2f 比 镭射孔径%.2f 小, 优先优化加大板内镭射ring，无法加大提评审'
                                        % (s_layer,flj_step, position, check_size , mintool/25.4)
                                    })                                    
                    #if abs(float(self.jsonData[s_layer]['minRing']) - min_ring) > compare_tol:
                        #print self.jsonData[s_layer]['minRing'],min_ring
                        #self.warn_list.append({
                            #'type': 'warn',
                            #'text': u'层别:%s 测试模块后台记录Ring为:%s,%s板内分析结果Ring为:%s，二者不相同!' % (s_layer,self.jsonData[s_layer]['minRing'],analysis_step, min_ring)
                        #})
                                
                    #if s_layer in self.jsonData and s_layer in blind_dict:
                        
                        #compare_tol = 0.02
                        ## === 周涌 2022.08.26 大于3mil公差按小数点后一位
                        #if blind_dict[s_layer]['laser_ar'] > 3:
                            #compare_tol = 0.1
                                       
                        #print s_layer
                        #print self.jsonData[s_layer]['minRing'],'xxx',blind_dict[s_layer]['laser_ar']
                        ## === 可能无分析结果，暂时不对比无分析结果的 ====
                        #if blind_dict[s_layer]['laser_ar']:
                            #if float(self.jsonData[s_layer]['minRing']) == max_laser_ar and float(blind_dict[s_layer]['laser_ar']) > max_laser_ar:
                                #continue
                            #if abs(float(self.jsonData[s_layer]['minRing']) - blind_dict[s_layer]['laser_ar']) > compare_tol:
                                #print self.jsonData[s_layer]['minRing'],blind_dict[s_layer]['laser_ar']
                                #self.warn_list.append({
                                    #'type': 'warn',
                                    #'text': u'层别:%s 测试模块后台记录Ring为:%s,板内分析结果Ring为:%s，二者不相同!' % (s_layer,self.jsonData[s_layer]['minRing'],blind_dict[s_layer]['laser_ar'])
                                #})
                    #else:
                        ## === 层别不在列表中，表示板内无孔，不对比数据
                        #pass
            
            if not self.warn_list:
                break
            
            #if check_mode == 3:
                #exit(0)
        self.warn_list += self.warn_list_check_open
            
    def getCopperReductionFlow(self):
        """
        获取inplan中的减铜流程的MRP，并拆解core层的层名，忽略其他层
        :return:
        """
        get_layers = []
        sql = """SELECT
            p.MRP_NAME,
            ( b.op_index_ * 10 + a.traveler_ordering_index ) num,
            a.operation_code,
            a.description,
            a.work_center_code 
        FROM
            VGT_HDI.rpt_job_trav_sect_list a,
            VGT_HDI.rpt_trav_sect_info b,
            VGT_HDI.Rpt_Process_Info p 
            WHERE
            a.job_name = '%s' 
            AND b.item_id = a.item_id 
            AND b.revision_id = a.revision_id 
            AND a.traveler_ordering_index = b.traveler_ordering_index 
            AND b.mrp_step_item_id = a.mrp_step_item_id 
            AND b.mrp_step_revision_id = a.mrp_step_revision_id 
            AND p.ITEM_ID = a.PROC_ITEM_ID 
            AND p.REVISION_ID = a.PROC_REVISION_ID 
            AND a.description = '减铜' 
            AND b.op_index_ > 10 
            AND b.op_index_ < 30 
        ORDER BY
            num""" % (self.job_name[0:13].upper())
        getResult = self.DB_O.SELECT_DIC(self.dbc_o, sql)

        for data in getResult:
            if '-' in data['MRP_NAME']:
                # eg. M19006OB148G1-20304
                part2 = data['MRP_NAME'].split('-')[1]
                part3 = int(part2[1:3])
                part4 = int(part2[3:5])
                if part4 - part3 == 1:
                    get_layers.append('l%s' % part3)
                    get_layers.append('l%s' % part4)
        return get_layers
    
    def getCuWeight(self):
        """
        获取型号各层的铜厚信息
        :return: dict
        """
        tmpWeight = {}
        sql = """SELECT
                        a.item_name 料号名,
                        lower( c.item_name ) 层别名,
                        round( d.required_cu_weight / 28.3495, 1 ) 基铜 
                    FROM
                        vgt_hdi.items a,
                        vgt_hdi.job b,
                        vgt_hdi.items c,
                        vgt_hdi.copper_layer d 
                    WHERE
                        a.item_id = b.item_id 
                        AND a.last_checked_in_rev = b.revision_id 
                        AND a.root_id = c.root_id 
                        AND c.item_id = d.item_id 
                        AND c.last_checked_in_rev = d.revision_id 
                        AND a.item_name = '%s' 
                    ORDER BY
                        d.layer_index""" % (self.job_name[0:13].upper())
        getResult = self.DB_O.SELECT_DIC(self.dbc_o, sql)
        # --整理出层对应的铜厚信息
        for lay_oz in getResult:
            tmpWeight[lay_oz['层别名']] = lay_oz['基铜']

        return tmpWeight

    def getCoreLayers(self):
        """
        获取core层
        :return: list
        """
        tmpCore = []
        sql = """SELECT
                    C.ITEM_NAME,
                    E.FILM_BG_,
                    E.DRILL_CS_LASER_ 
                FROM
                    VGT_HDI.PUBLIC_ITEMS A
                    INNER JOIN VGT_HDI.JOB B ON A.ITEM_ID = B.ITEM_ID 
                    AND A.REVISION_ID = B.REVISION_ID
                    INNER JOIN VGT_HDI.PUBLIC_ITEMS C ON A.ROOT_ID = C.ROOT_ID
                    INNER JOIN VGT_HDI.PROCESS D ON C.ITEM_ID = D.ITEM_ID 
                    AND C.REVISION_ID = D.REVISION_ID
                    INNER JOIN VGT_HDI.PROCESS_DA E ON D.ITEM_ID = E.ITEM_ID 
                    AND D.REVISION_ID = E.REVISION_ID 
                WHERE
                    A.ITEM_NAME = '%s' 
                    AND D.PROC_TYPE = 1 
                ORDER BY
                    E.PROCESS_NUM_ DESC""" % self.job_name[0:13].upper()

        getResult = self.DB_O.SELECT_DIC(self.dbc_o, sql)
        for dic in getResult:
            # --判断是否为Core的条件
            if 'Core' in dic["ITEM_NAME"] or "Buried Via" in dic["ITEM_NAME"]:
                # --小写，分割并合并到数组中
                if dic['FILM_BG_'] is None:
                    # 光板会没有层 需跳过 20230605 by lyh
                    continue
                tmpCore += dic['FILM_BG_'].lower().split(',')
        # --测试用
        # self.coreLayers.append('l3')
        return tmpCore
    
    def check_ring_new(self, check_mode):
        """按新的逻辑来检查防漏接"""
        flj_steps = [name for name in matrixInfo["gCOLstep_name"]
                     if name.endswith("floujie")]
        
        # --最新标准中要求当core层与非core层的钻穿层数据参数
        self.resizeDic = {
            'IsNotCore': {
                'pad1': 45, 'pad2': 25, 'pad3': 35
            },
            # --工艺第N次修正数据
            'IsCore': {
                # 'pad1': 85, 'pad2': 55, 'pad3': 70
                'pad1': 65, 'pad2': 35, 'pad3': 50
            }
        }        
        
        self.DB_O = Oracle_DB.ORACLE_INIT()
        self.dbc_o = self.DB_O.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port=1521, username='GETDATA',
            passwd='InplanAdmin')
        # 线路补偿 由计算完成厚度CAL_CU_THK_，改为计算完成厚度(不考虑树脂塞孔补偿)CAL_CU_THK_PLATE_
        self.layerInfo = self.DB_O.getLayerThkInfo_plate(self.dbc_o, self.job_name.split("-")[0].upper())
        self.mi_compensate_info = self.DB_O.get_mi_lot_compensate_value(self.dbc_o, self.job_name.split("-")[0].upper())
        
        self.core_cu_down_layers = self.getCopperReductionFlow()
        # --从InPlan中获取对应的铜厚信息（用于计算开窗大小）
        self.layerWeight = self.getCuWeight()
        # --从InPlan中获取对应的数据（用于判断是否为core层）
        self.coreLayers = self.getCoreLayers()        
        
        dic_flj_pad_info = {}
        
        for stepname in flj_steps:
            step = gClasses.Step(job, stepname)
            step.open()
            for drill_layer in self.blind_layers:
                layer_cmd = gClasses.Layer(step, drill_layer)
                feat_out = layer_cmd.featCurrent_LayerOut(units="mm")
                if feat_out:
                    layer1 = drill_layer.split("-")[0].replace("s", "l")
                    layer2 = "l" + drill_layer.split("-")[1]
                    
                    worklayer = layer2
                    # for worklayer in [layer1, layer2]:
                    step.clearAll()
                    step.resetFilter()
                    step.affect(worklayer)
                    step.filter_set(feat_types='pad', polarity='negative')
                    step.setAttrFilter(".bit,text=flj_inner_tpad1")
                    step.setAttrFilter(".bit,text=flj_inner_tpad2")
                    step.setAttrFilter(".bit,text=flj_inner_tpad3")
                    step.setAttrFilter(".bit,text=flj_inner_bpad1")
                    step.setAttrFilter(".bit,text=flj_inner_bpad2")
                    step.setAttrFilter(".bit,text=flj_inner_bpad3")                
                    step.COM("filter_atr_logic,filter_name=popup,logic=or")
                    # step.selectAll()
                    step.refSelectFilter(drill_layer)
                    if step.featureSelected():
                        
                        layer_cmd1 = gClasses.Layer(step, worklayer)
                        feat_out1 = layer_cmd1.featout_dic_Index(units="inch",
                                                                 options="feat_index+select")["pads"]
                        # step.PAUSE(str(len(feat_out1)))
                        if check_mode == 1:
                            pad1, pad2, pad3 = self.get_pad1_pad2_pad3_size_1(worklayer)
                        elif check_mode == 2:
                            pad1, pad2, pad3 = self.get_pad1_pad2_pad3_size_2(worklayer)
                        else:
                            pad1, pad2, pad3 = self.get_pad1_pad2_pad3_size_3(worklayer)
                        # pad1, pad2, pad3 = self.get_pad1_pad2_pad3_size(worklayer)
                        dic_flj_pad_info[drill_layer] = []
                        # step.PAUSE(str([drill_layer, pad1, pad2, pad3]))
                        for i, obj in enumerate(sorted(feat_out1, key= lambda x: getattr(x, "bit", None))):
                            attr = getattr(obj, "bit", None)
                            work_size = round(float(obj.symbol[1:]), 2)
                            pad_size = (round(pad1 / 25.4, 2), round(pad2 / 25.4, 2), round(pad3 / 25.4, 2))
                            if (attr, work_size, pad_size, stepname) not in dic_flj_pad_info[drill_layer]:                                
                                dic_flj_pad_info[drill_layer] += [(attr, work_size, pad_size, stepname)]

            step.clearAll()
            
        return dic_flj_pad_info
    
    def get_pad1_pad2_pad3_size_1(self, E_layer):
        """获取三个pad的补偿值"""
        # region # --判断当前层是否为core层,且对应层铜厚是否为>=0.5OZ并加载对应的扣减参数
        if (E_layer in self.coreLayers and E_layer not in self.core_cu_down_layers) and float(self.layerWeight[E_layer]) >= 0.5:
            pad1 = self.resizeDic['IsCore']['pad1']
            pad2 = self.resizeDic['IsCore']['pad2']
            pad3 = self.resizeDic['IsCore']['pad3']
        else:
            pad1 = self.resizeDic['IsNotCore']['pad1']
            pad2 = self.resizeDic['IsNotCore']['pad2']
            pad3 = self.resizeDic['IsNotCore']['pad3']            
                            
        return pad1, pad2, pad3
    
    def get_pad1_pad2_pad3_size_2(self, E_layer):
        """获取三个pad的补偿值"""
        # region # --判断当前层是否为core层,且对应层铜厚是否为>=0.5OZ并加载对应的扣减参数
        if (E_layer in self.coreLayers and E_layer not in self.core_cu_down_layers) and float(self.layerWeight[E_layer]) >= 0.5:
            pad1 = self.resizeDic['IsCore']['pad1']
            pad2 = self.resizeDic['IsCore']['pad2']
            pad3 = self.resizeDic['IsCore']['pad3']
        else:
            pad1 = self.resizeDic['IsNotCore']['pad1']
            pad2 = self.resizeDic['IsNotCore']['pad2']
            pad3 = self.resizeDic['IsNotCore']['pad3']
            
        # 增加1oz以上铜厚判断逻辑 http://192.168.2.120:82/zentao/story-view-7047.html 20240621 by lyh
        # print(self.layerInfo, "------------------>")
        # 暂时先在汽车板 跟电池板上更新 20240622 
        for l_index in self.layerInfo:
            # print("---------------------->", l_index)
            if E_layer == l_index['LAYER_NAME'].lower():
                # if E_layer in self.coreLayers:
                if "OZ" in self.mi_compensate_info.get(E_layer, ""):                        
                    getthick = float(l_index['CU_WEIGHT'])
                    if getthick <= 0.5:
                        pad1 = 45
                        pad2 = 25
                        pad3 = 35                    
                    elif 0.5< getthick <= 1:
                        pad1 = 65
                        pad2 = 35
                        pad3 = 50
                    elif 1< getthick <= 1.5:
                        pad1 = 135
                        pad2 = 105
                        pad3 = 120
                    elif 1.5< getthick <= 2:
                        pad1 = 175
                        pad2 = 145
                        pad3 = 160
                    elif 2< getthick <= 2.5:
                        pad1 = 240
                        pad2 = 210
                        pad3 = 225
                    elif 2.5< getthick :
                        pad1 = 305
                        pad2 = 275
                        pad3 = 290
                else:
                    getthick = float(l_index['CAL_CU_THK'])
                    
                    if getthick <= 0.689:
                        pad1 = 45
                        pad2 = 25
                        pad3 = 35                    
                    elif 0.689< getthick <= 1.378:
                        pad1 = 65
                        pad2 = 35
                        pad3 = 50
                    elif 1.378< getthick <= 2.067:
                        pad1 = 135
                        pad2 = 105
                        pad3 = 120
                    elif 2.067< getthick <= 2.756:
                        pad1 = 175
                        pad2 = 145
                        pad3 = 160
                    elif 2.756< getthick <= 3.444:
                        pad1 = 240
                        pad2 = 210
                        pad3 = 225
                    elif 3.444< getthick :
                        pad1 = 305
                        pad2 = 275
                        pad3 = 290  
                        
        return pad1, pad2, pad3
    
    def get_pad1_pad2_pad3_size_3(self, E_layer):
        """获取三个pad的补偿值"""
        # region # --判断当前层是否为core层,且对应层铜厚是否为>=0.5OZ并加载对应的扣减参数
        if (E_layer in self.coreLayers and E_layer not in self.core_cu_down_layers) and float(self.layerWeight[E_layer]) >= 0.5:
            pad1 = self.resizeDic['IsCore']['pad1']
            pad2 = self.resizeDic['IsCore']['pad2']
            pad3 = self.resizeDic['IsCore']['pad3']
        else:
            pad1 = self.resizeDic['IsNotCore']['pad1']
            pad2 = self.resizeDic['IsNotCore']['pad2']
            pad3 = self.resizeDic['IsNotCore']['pad3']
            
        # 增加1oz以上铜厚判断逻辑 http://192.168.2.120:82/zentao/story-view-7047.html 20240621 by lyh
        # print(self.layerInfo, "------------------>")
        # 暂时先在汽车板 跟电池板上更新 20240622 
        for l_index in self.layerInfo:
            # print("---------------------->", l_index)
            if E_layer == l_index['LAYER_NAME'].lower():
                # if E_layer in self.coreLayers:
                if "OZ" in self.mi_compensate_info.get(E_layer, ""):                        
                    getthick = float(l_index['CU_WEIGHT'])
                    if getthick <= 0.53:
                        pad1 = 1.771 * 25.4
                        pad2 = 0.984 * 25.4
                        pad3 = 1.377 * 25.4                    
                    elif 0.53< getthick <= 1.07:
                        pad1 = 2.559 * 25.4
                        pad2 = 1.377 * 25.4
                        pad3 = 1.968 * 25.4
                    elif 1.07< getthick <= 1.61:
                        pad1 = 3.814 * 25.4
                        pad2 = 2.633 * 25.4
                        pad3 = 3.224 * 25.4
                    elif 1.61< getthick <= 2.13:
                        pad1 = 4.889 * 25.4
                        pad2 = 3.708 * 25.4
                        pad3 = 4.299 * 25.4
                    elif 2.13< getthick <= 2.69:
                        pad1 = 6.948 * 25.4
                        pad2 = 6.067 * 25.4
                        pad3 = 6.358 * 25.4
                    elif 2.69< getthick :
                        pad1 = 9.507 * 25.4
                        pad2 = 8.326 * 25.4
                        pad3 = 8.917 * 25.4 
                else:
                    getthick = float(l_index['CAL_CU_THK'])
                    
                    if getthick <= 0.689:
                        pad1 = 1.771 * 25.4
                        pad2 = 0.984 * 25.4
                        pad3 = 1.377 * 25.4                    
                    elif 0.689< getthick <= 1.390:
                        pad1 = 2.559 * 25.4
                        pad2 = 1.377 * 25.4
                        pad3 = 1.968 * 25.4
                    elif 1.390< getthick <= 2.100:
                        pad1 = 3.814 * 25.4
                        pad2 = 2.633 * 25.4
                        pad3 = 3.224 * 25.4
                    elif 2.100< getthick <= 2.770:
                        pad1 = 4.889 * 25.4
                        pad2 = 3.708 * 25.4
                        pad3 = 4.299 * 25.4
                    elif 2.770< getthick <= 3.500:
                        pad1 = 6.948 * 25.4
                        pad2 = 6.067 * 25.4
                        pad3 = 6.358 * 25.4
                    elif 3.500< getthick :
                        pad1 = 9.507 * 25.4
                        pad2 = 8.326 * 25.4
                        pad3 = 8.917 * 25.4  
                            
        return pad1, pad2, pad3    
            
# # # # --程序入口
if __name__ == "__main__":
    myapp = QtGui.QApplication(sys.argv)
    # === 此程序单位使用inch
    app = MyApp()
    app.run()
    
    #全自动检测调用 20240711 by lyh
    if "auto_check" in sys.argv[1:]:
        if len(app.warn_list) > 0:
            arraylist_log = []
            for s_i in app.warn_list:
                arraylist_log.append(s_i['text'])
            
            with open("/tmp/check_flj_error_{0}.log".format(app.job_name), "w") as f:
                f.write("<br>".join(arraylist_log).encode("cp936"))
        
        with open("/tmp/check_flj_success_{0}.log".format(app.job_name), "w") as f:
            f.write("yes")
            
        sys.exit(0)
            
    if len(app.warn_list) > 0:
        # === 增加审批开始
        time_key = int(time.time())
        time_form = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_key))

        jstr1 = '<span>镭射Ring检查.料号：%s,时间:%s,CAM用户:%s明细如下</span>' % (app.job_name,time_form, app.cam_user)
        jstr1 += '<span><table border="1" style="background-color: #ffffff; color: #000000; font-size: 12px">'
        jstr1 += '<tr><th>类型</th><th>内容</th></tr>'

        ctr1 = ''
        for s_i in app.warn_list:
            ctr1 += '<tr><td>%s</td><td>%s</td></tr>' % (s_i['type'],s_i['text'])
        jstr1 += ctr1
        jstr1 += '</table></span>'
        # print jstr1
        # === 发送评审请求 ===
        submitData = {
            'site': u'HDI板事业部',
            'job_name': app.job_name,
            'pass_tpye': 'CAM',
            'pass_level': 8,
            'assign_approve': '44566|44024|68027|83288|91259|84310|99234',
            'pass_title': u"%s" % jstr1,
        }
        Dialog = AboutDialog(submitData['pass_title'], cancel=True, appCheck=True, appData=submitData,
                             style='other')
        Dialog.exec_()
        # endregion
        print Dialog.selBut
        # --根据审批的结果返回值
        if Dialog.selBut == 'cancel':
            sys.exit(1)
        if Dialog.selBut == 'x':
            sys.exit(1)
        # === 增加审批结束
        # msg_box = msgBox()
        # msg_box.warning(None, '警告', '\n'.join([i['text'] for i in app.warn_list]), QMessageBox.Ok)
        # self.lin
        sys.exit(0)
    else:
        msg_box = msgBox()
        msg_box.information(None, '提示', '防漏接模块镭射Ring数据与板内镭射Ring分析结果比对程序运行完成！', QMessageBox.Ok)
        sys.exit(0)


# DO_INFO "-t check -e h19808gh931a5-zy/edit/inner-sum-slc -d MEAS  \
#          -o index+action=1,  \
#         angle_direction=ccw"
# chklist_res_goto_measure,layers_mode=replace,keep_work_lyr=no,display_mode=auto_zoom,chklist=inner-sum-slc,nact=1,ind=659,show_orig=no (0)
# laser_via_ar l7 3.245 mil r4.016 r13.488 SG 0.6671216 0.4664759 0.6649237 0.4688629 4 R 659
# c short for check, r short for result r_color:R->Red Y->Yellow G->Green  r_show unknown :SG|CR
# === 分析结果分类
# DO_INFO "-t check -e h19808gh931a5-zy/edit/inner-sum-slc -d MEAS_DISP_ID  \
#          -o action=1,  \
#         angle_direction=ccw"
# l7 1 l7
# l7 2 l7 b2-7
# l7 3 l7 s7-6
# l7 4 l7 s8-7
# l3 1 l3
# l3 2 l3 s2-3
# l3 3 l3 b2-7
# l5 1 l5
# l5 2 l5 b2-7
# l2 1 l2
# l2 2 l2 s1-2
# l2 3 l2 s2-3
# l2 4 l2 b2-7
# l4 1 l4
# l4 2 l4 b2-7
# l6 1 l6
# l6 2 l6 b2-7
# l6 3 l6 s7-6

# blind_dict = {
#  "s8-7": {
#    "end_layer": "l7",
#    "disp_id": "4",
#    "laser_ar": 3.7200000000000002
#  },
#  "s7-6": {
#    "end_layer": "l6",
#    "disp_id": "4",
#    "laser_ar": 3.2080000000000002
#  },
#  "s2-3": {
#    "end_layer": "l3",
#    "disp_id": "3",
#    "laser_ar": 3.1000000000000001
#  },
#  "s1-2": {
#    "end_layer": "l2",
#    "disp_id": "3",
#    "laser_ar": 3.504
#  }
# }
# self.jsonData = {
#     "b3-6": {
#         "minDrill": "222",
#         "minRing": "4"
#     },
#     "drl": {
#         "minDrill": "222",
#         "minRing": "4"
#     },
#     "s1-2": {
#         "minDrill": "76",
#         "minRing": "3.5"
#     },
#     "s2-3": {
#         "minDrill": "102",
#         "minRing": "3.1"
#     },
#     "s7-6": {
#         "minDrill": "102",
#         "minRing": "3.2"
#     },
#     "s8-7": {
#         "minDrill": "76",
#         "minRing": "3.7"
#     }
# }
