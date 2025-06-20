#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20240731"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""阻抗线补偿值获取 """

import os
import sys
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")

import Oracle_DB
import csv
import re
import json
import copy
from create_ui_model import showMessageInfo
from genesisPackages import signalLayers

class sepByAttr:  # 自定义的元素
    def __init__(self,
                 (thk_dowm, thk_up, rangeSpc, minWorkSpc, impBaseComp, SingleComp, DiffComp, CopSingleComp, CopDiffComp, l2lspcControl)):
        self.thk_dowm = float(thk_dowm)
        self.thk_up = float(thk_up)
        self.rangeSpc = rangeSpc
        self.minWorkSpc = float(minWorkSpc)
        self.impBaseComp = float(impBaseComp) if impBaseComp != 'None' else 0
        self.SingleComp = float(SingleComp) if SingleComp != 'None' else 0
        self.DiffComp = float(DiffComp) if DiffComp != 'None' else 0
        self.CopSingleComp = float(CopSingleComp) if CopSingleComp != 'None' else 0
        self.CopDiffComp = float(CopDiffComp) if CopDiffComp != 'None' else 0
        self.l2lspcControl = float(l2lspcControl) if l2lspcControl != 'None' else 0
    

class icg_coupon_compensate_value(object):
    """"""

    def __init__(self):
        """Constructor"""
        
        self.job_name = os.environ["JOB"]
        # === 获取inplan数据信息 ===
        M = Oracle_DB.ORACLE_INIT()
        dbc_o = M.DB_CONNECT("172.20.218.193", "inmind.fls", '1521', 'GETDATA', 'InplanAdmin')
        
        self.warn_list = []
        
        if dbc_o is None:
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(u'HDI InPlan 无法连接, 程序退出！')
            else:
                showMessageInfo(u'HDI InPlan 无法连接, 程序退出！')
                exit(0)
            
        self.strJobName = self.job_name.split('-')[0].upper()
        # inplan中无数据返回时应提示inplan中查询不到数据，MI数据中的X及Y个数，拼版方向，最小值
        self.panelSRtable = M.getPanelSRTable(dbc_o, self.strJobName)
        if not self.panelSRtable:
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(u'HDI InPlan无料号%s数据, 程序退出！' % self.strJobName)
            else:            
                showMessageInfo(u'HDI InPlan无料号%s数据, 程序退出！' % self.strJobName)
                exit(0)
        
        self.JobData = M.getJobData(dbc_o, self.strJobName)
        self.ip_data = M.get_inplan_imp(dbc_o, self.strJobName)
        
        # 樊后星通知：20240326 by lyh
        # 线路补偿 由计算完成厚度CAL_CU_THK_，改为计算完成厚度(不考虑树脂塞孔补偿)CAL_CU_THK_PLATE_
        self.layerInfo = M.getLayerThkInfo_plate(dbc_o, self.strJobName)        
        self.stackupInfo = self.get_inplan_stackup_info(M, dbc_o)
        self.stackupInfo = self.dealWithStackUpData(self.stackupInfo)
        M.DB_CLOSE(dbc_o)
        
        self.scrDir = "/incam/server/site_data/scripts/hdi_scr/Coupon/"
        outer_file = self.scrDir + '/impCouponComp_Outer_v22.09.26.csv'
        # === V4.2 转换外层配置参数为csv文件，并在csv文件中添加表头。
        # ====解析方式仍然不变（暂不使用csv直接解析，不变更后续程序使用），
        if os.path.exists(outer_file):
            f = open(outer_file)
            self.comp_data_outer = map(lambda x: x.strip().split(","), f.readlines()[1:])
            self.comp_data_outer = [sepByAttr(x) for x in self.comp_data_outer]
        else:
            #msg_box = msgBox()
            #msg_box.critical(self, '警告', u'没有外层补偿配置文件, 程序退出！', QtGui.QMessageBox.Ok)
            #self.compFileexist = 'no'
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(u'没有外层补偿配置文件, 程序退出！')
            else:            
                showMessageInfo(u'没有外层补偿配置文件, 程序退出！')
                exit(0)
            
        # 获取内层补偿规则
        # === 2021.03.05 /impCouponComp_Inner_v20.09.10.ini
        if os.path.exists(self.scrDir + '/test-V5.5/impCouponComp_Inner_v5.5.ini'):
            # f = open (r'impCouponComp_Inner.ini')
            f = open(self.scrDir + '/test-V5.5/impCouponComp_Inner_v5.5.ini')

            self.comp_data_inner = map(lambda x: x.strip().split("\t"), f.readlines())
            self.comp_data_inner = [sepByAttr(x) for x in self.comp_data_inner]
        else:
            #msg_box = msgBox()
            #msg_box.critical(self, '警告', u'没有内层补偿配置文件, 程序退出！', QtGui.QMessageBox.Ok)
            #self.compFileexist = 'no'
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(u'没有内层补偿配置文件, 程序退出！')
            else:                
                showMessageInfo(u'没有内层补偿配置文件, 程序退出！')
                exit(0)

        # === 获取次一层/内一层的补偿参数
        # === 2021.03.05 /impCouponComp_Sec1_v20.09.10.ini
        if os.path.exists(self.scrDir + '/test-V5.5/impCouponComp_Sec1_v5.5.ini'):
            f = open(self.scrDir + '/test-V5.5/impCouponComp_Sec1_v5.5.ini')
            self.comp_data_sec1 = map(lambda x: x.strip().split("\t"), f.readlines())
            self.comp_data_sec1 = [sepByAttr(x) for x in self.comp_data_sec1]
        else:
            #msg_box = msgBox()
            #msg_box.critical(self, '警告', u'没有次一层补偿配置文件, 程序退出！', QtGui.QMessageBox.Ok)
            #self.compFileexist = 'no'
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(u'没有次一层补偿配置文件, 程序退出！')
            else:               
                showMessageInfo(u'没有次一层补偿配置文件, 程序退出！')
                exit(0)

        # === 增加外层及次外层干膜解析度的csv文件解析 ===
        self.out_gm_rule = []
        with open(self.scrDir + '/out_gm_space.csv') as f:
            f_csv = csv.DictReader(f)
            for row in f_csv:
                self.out_gm_rule.append(row)
        # === V5.3.3 inn及sec1考虑内层干膜解析度
        self.inn_gm_rule = []
        with open(self.scrDir + '/test-V5.5/inn_gm_space.csv') as f:
            f_csv = csv.DictReader(f)
            for row in f_csv:
                self.inn_gm_rule.append(row)            
            
    def get_dic_compensate_imp_info(self):
        """获取阻抗补偿后的线宽 线距返回值"""
        
        # if self.job_name != "DA8614P5886A1_yl".lower():
            
        self.table_laylist_set()
        self.imp_table_set()
        
        # === 列表达式
        column_keys = ['IGROUP', "TRACE_LAYER_", "FINISH_LW_", "FINISH_LS_", "SPC2CU", "REF_TOP", "REF_BOT",
                       "ORG_WIDTH", "IMODEL", "WGROUP2", "SOLDEROPEN", "CUSIMP", 'workLineWid', 'workLineSpc',
                       'workSpc2Cu', 'WGROUP1', 'ID']
        
        # print(json.dumps (self.ip_data, sort_keys=True, indent=2, separators=(',', ': ')))
        return self.ip_data
            
    def table_laylist_set(self):
        
        self.sig_layers = signalLayers
        for x in range(len(self.sig_layers)):
            if not self.stackupInfo.has_key(self.sig_layers[x]):
                if "autocheck" in sys.argv[1:]:
                    self.warn_list.append(u'未获取到{0}层干膜信息，请反馈MI上传'.format(self.sig_layers[x]))
                else:                 
                    showMessageInfo(u'未获取到{0}层干膜信息，请反馈MI上传'.format(self.sig_layers[x]))
                    sys.exit(0)
            # === layer_mode out|sec|sec1|inn
            layer_mode = self.stackupInfo[self.sig_layers[x]]['layerMode']
            
            for index in range(len(self.layerInfo)):
                layName = self.layerInfo[index]['LAYER_NAME'].lower()
                if layName == self.sig_layers[x]:
                    cu_thick = self.layerInfo[index]['CAL_CU_THK']
                    if layer_mode == 'inn':
                        cu_thick = self.layerInfo[index]['CU_WEIGHT']
                    # === V3.7.5 合并单个参数改为一个，简化代码
                    compData = self.getCouponCompList(cu_thick, layer_mode)
                    if compData is None:
                        if layer_mode == 'sec1' and float(cu_thick) < 0.6:
                            # === 2022.12.23 部分料号超出规范定义范围，但仍需补偿的，使用最小区间下限进行补偿 ===
                            cu_thick = 0.6
                            compData = self.getCouponCompList(cu_thick, layer_mode)
                            
                            showText = u"料号:%s层别:%s无法获取补偿信息，层别类型:%s基铜:%s完成铜厚:%s,使用完成铜厚0.6进行补偿!" % (
                                self.job_name, self.sig_layers[x], self.stackupInfo[self.sig_layers[x]]['layerMode'],
                                self.layerInfo[index]['CU_WEIGHT'], self.layerInfo[index]['CAL_CU_THK'])
                            if "autocheck" in sys.argv[1:]:
                                pass
                            else:                             
                                showMessageInfo(showText)
                        else:
                            showText = u"料号:%s层别:%s无法获取补偿信息，层别类型:%s基铜:%s完成铜厚:%s,程序退出!" % (
                                self.job_name, self.sig_layers[x], self.stackupInfo[self.sig_layers[x]]['layerMode'],
                                self.layerInfo[index]['CU_WEIGHT'], self.layerInfo[index]['CAL_CU_THK'])
                            if "autocheck" in sys.argv[1:]:
                                self.warn_list.append(showText)
                            else:                             
                                showMessageInfo(showText)
                                exit(1)
                    l2lspc = float(compData.l2lspcControl) * 1.0

                    # === TODO 外层次外层增加解析度的比对，inn类型Hoz增加成品线宽，成品线距的条件
                    w_line_width = self.layerInfo[index]['成品线宽']
                    w_line_space = self.layerInfo[index]['成品线距']
                    if layer_mode == 'inn':
                        if 0.01 < cu_thick < 0.53:
                            if w_line_width == 0 or w_line_space == 0:
                                pass
                            elif 1.8 >= float(w_line_width) > 1.5 and 1.8 >= float(w_line_space) > 1.5:
                                l2lspc = 1.4
                                compData.impBaseComp = 0.5
                            elif 2.0 >= float(w_line_width) > 1.8 and 2.0 >= float(w_line_space) > 1.8:
                                l2lspc = 1.6
                                compData.impBaseComp = 0.6

                    compData.l2lspcControl = l2lspc * 1.0
                    self.layerInfo[index]['compData'] = compData
                    
    def imp_table_set(self):
        
        for x, line in enumerate(self.ip_data):
            x_layer = line["TRACE_LAYER_"].lower()
            # === 先计算出阻抗线补偿后的值
            for l_index, lyr_data in enumerate(self.layerInfo):
                l_layer = lyr_data['LAYER_NAME'].lower()
                if l_layer == x_layer:
                    # === 计算补偿值 ===                    self.imp_comp(x, l_layer, l_index)

    def get_inplan_stackup_info(self, M, dbc_o):
        """
        获取inplan干膜信息
        :return:
        """
        # === 2022.04.20
        sql = """
        SELECT
            a.JOB_NAME,
            b.PROCESS_NAME,
            b.MRP_NAME,
            a.WORK_CENTER_CODE,
            a.OPERATION_CODE,
            a.DESCRIPTION,
            b.FILM_BG_,
            b.DRILL_CS_LASER_,
            c.VALUE AS DF_TYPE_ 
        FROM
            vgt_hdi.rpt_job_trav_sect_list a
            INNER JOIN vgt_hdi.Rpt_Job_Process_List b ON a.ROOT_ID = b.ROOT_ID 
            AND a.PROC_ITEM_ID = b.ITEM_ID 
            AND a.PROC_REVISION_ID = b.REVISION_ID
            INNER JOIN vgt_hdi.enum_values c ON b.df_type_ = c.enum 
            AND c.enum_type = '1012' 
        WHERE
            ( a.DESCRIPTION = 'LDI' OR a.OPERATION_CODE IN ( 'HDI11703', 'HDI17403' ) ) 
            AND a.JOB_NAME = '%s' 
            AND b.MRP_NAME NOT LIKE '%%光板%%'
        """ % self.strJobName

        dataVal = M.SELECT_DIC(dbc_o, sql)
        # print dataVal
        return dataVal
    
    def dealWithStackUpData(self, InpDict):
        """
        整合从inplan获取的层别信息，包括层别类型inn，sec1，sec，out
        :param InpDict:
        :return:
        """
        """
        处理叠构信息
        :param InpDict:
        :return:
        """
        dataVal = InpDict
        stack_data = {}
        # 根据压合叠构整理层别类型
        for index in dataVal:
            top_bot_lay = index['FILM_BG_'].lower().split(',')
            stackProcess = index['PROCESS_NAME'].split('-')
            df_type = index['DF_TYPE_']
            # 2020.05.11 增加Core+Core的条件
            get_two_layer = stackProcess[1]
            # 去除数据前后空格
            twice_top_bot_lay = get_two_layer.strip(' ').split('/')

            # layerMode = None
            materialType = None
            if stackProcess[0] == "Final Assembly ":
                # layerMode = 'out'
                materialType = 'cu'
            elif stackProcess[0] == "Sub Assembly ":
                # layerMode = 'sec'
                materialType = 'cu'
                # if not index['DRILL_CS_LASER_']:
                #     layerMode = 'sec1'
            elif stackProcess[0] == "Inner Layers Core ":
                # layerMode = 'inn'
                materialType = 'core'
            elif stackProcess[0] == "Buried Via ":
                # layerMode = 'sec1'
                materialType = 'core'
            elif stackProcess[0] == "Blind Via ":
                # layerMode = 'sec1'
                materialType = 'core'

            '''
            S51506HI070A2	Final Assembly - 1/6	L1,L6
            S51506HI070A2	Buried Via - 3/4	L3,L4
            S51506HI070A2	Blind Via - 1/2	L2
            S51506HI070A2	Blind Via - 5/6	L5
            '''
            # if self.JobData[0]['ES_ELIC_'] == 1 and layerMode != 'out':
            #     layerMode = 'sec'
            #     if int(twice_top_bot_lay[1]) - int(twice_top_bot_lay[0]) == 1:
            #         layerMode = 'sec1'

            #  === 2022.04.20 层别是内层，外层，次外层内，次外层外，使用流程进行判断
            layerMode = None
            # inn_Reg = re.compile('内层线路')
            # out_Reg = re.compile('外层线路')
            sec1_Reg = re.compile('次外层线路（内')
            sec_Reg = re.compile('次外层线路（外')

            work_name = index['WORK_CENTER_CODE']
            if work_name == '内层线路':
                layerMode = 'inn'
            elif work_name == '外层线路' or work_name == '外层图形':
                layerMode = 'out'
            elif sec1_Reg.match(work_name):
                layerMode = 'sec1'
            elif sec_Reg.match(work_name):
                layerMode = 'sec'

            if self.JobData[0]['ES_ELIC_'] == 1 and layerMode == 'inn':
                if int(twice_top_bot_lay[1]) - int(twice_top_bot_lay[0]) == 1:
                    layerMode = 'sec1'

            if len(top_bot_lay) != 2:
                stack_data[top_bot_lay[0]] = {}
                get_top_lay = 'l' + twice_top_bot_lay[0]
                get_bot_lay = 'l' + twice_top_bot_lay[1]
                if top_bot_lay[0] == get_top_lay:
                    stack_data[top_bot_lay[0]]['layerSide'] = 'top'
                    stack_data[top_bot_lay[0]]['layerMode'] = layerMode
                    stack_data[top_bot_lay[0]]['materialType'] = materialType
                    stack_data[top_bot_lay[0]]['df_type'] = df_type
                elif top_bot_lay[0] == get_bot_lay:
                    stack_data[top_bot_lay[0]]['layerSide'] = 'bot'
                    stack_data[top_bot_lay[0]]['layerMode'] = layerMode
                    stack_data[top_bot_lay[0]]['materialType'] = materialType
                    stack_data[top_bot_lay[0]]['df_type'] = df_type
            else:
                stack_data[top_bot_lay[0]] = {}
                stack_data[top_bot_lay[1]] = {}
                stack_data[top_bot_lay[0]]['layerSide'] = 'top'
                stack_data[top_bot_lay[0]]['layerMode'] = layerMode
                stack_data[top_bot_lay[0]]['materialType'] = materialType
                stack_data[top_bot_lay[0]]['df_type'] = df_type
                # stack_data[top_bot_lay[0]]['film_bg'] = top_bot_lay[1]

                stack_data[top_bot_lay[1]]['layerSide'] = 'bot'
                stack_data[top_bot_lay[1]]['layerMode'] = layerMode
                stack_data[top_bot_lay[1]]['materialType'] = materialType
                stack_data[top_bot_lay[1]]['df_type'] = df_type
                # stack_data[top_bot_lay[1]]['film_bg'] = top_bot_lay[0]
        return stack_data
        
    def getCouponCompList(self, job_layer_thk, layer_mode):
        """
        获取层别补偿参数
        :param job_layer_thk: 层别铜厚，inn类型层为基铜，其他类型层为完成铜厚
        :param layer_mode: 层别类型 inn|sec1|sec|out
        :return:
        """
        comp_data = ''
        if layer_mode == 'sec' or layer_mode == 'out':
            comp_data = copy.deepcopy(self.comp_data_outer)
        elif layer_mode == 'sec1':
            comp_data = copy.deepcopy(self.comp_data_sec1)
        elif layer_mode == 'inn':
            comp_data = copy.deepcopy(self.comp_data_inner)
        if not comp_data:
            # GEN.PAUSE('INPUT MODE ERROR')
            showText = u"函数getCouponCompList，输入的mode：%s不在定义范围!" % (layer_mode)
            #msg_box = msgBox()
            #msg_box.warning(self, '警告', showText, QtGui.QMessageBox.Ok)
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(showText)
            else:             
                showMessageInfo(showText)

        for line in comp_data:  # type: sepByAttr
            if line.thk_dowm <= job_layer_thk < line.thk_up:
                return line
        return None
    
    def imp_comp(self, x, trace_layer, index):
        """
        根据阻抗线类型进行分类
        :param x: 所有阻抗信息的序号，数据对应阻抗信息表的行
        :param trace_layer: 信号层
        :param index: 层别信息的序号，对应层别信息表的行
        :return: None 直接更改全局变量
        """
        layer_mode = self.stackupInfo[trace_layer]['layerMode']
        if self.ip_data[x]["IMODEL"] == "特性":
            self.ip_data[x]['workLineWid'] = self.ip_data[x]["FINISH_LW_"] + self.layerInfo[index][
                'compData'].impBaseComp + self.layerInfo[index]['compData'].SingleComp
            self.ip_data[x]['workLineSpc'] = 0
            self.ip_data[x]['workSpc2Cu'] = 0
        elif self.ip_data[x]["IMODEL"] == "差动":
            self.ip_data[x]['workLineWid'] = self.ip_data[x]["FINISH_LW_"] + self.layerInfo[index][
                'compData'].impBaseComp + self.layerInfo[index]['compData'].DiffComp * 0.5

            self.ip_data[x]['workLineSpc'] = self.ip_data[x]["FINISH_LS_"] - self.layerInfo[index][
                'compData'].impBaseComp
            self.ip_data[x]['workSpc2Cu'] = 0
            if layer_mode in ['sec', 'out']:
                # === 次外层外时，为保证和板内间距一致，增加动态补偿算法 3，5，8
                if self.layerInfo[index]['compData'].DiffComp > 0:
                    if 8 > float(self.ip_data[x]['workLineSpc']) >= 3.0:
                        self.ip_data[x]['workLineSpc'] = self.ip_data[x]['workLineSpc'] - 0.2
                        self.ip_data[x]['workLineWid'] = self.ip_data[x]["FINISH_LW_"] + self.layerInfo[index][
                            'compData'].impBaseComp + self.layerInfo[index]['compData'].DiffComp * 0.5 + 0.1
                    elif 15.0 > float(self.ip_data[x]['workLineSpc']) >= 8:
                        self.ip_data[x]['workLineSpc'] = self.ip_data[x]['workLineSpc'] - 0.3
                        self.ip_data[x]['workLineWid'] = self.ip_data[x]["FINISH_LW_"] + self.layerInfo[index][
                            'compData'].impBaseComp + self.layerInfo[index]['compData'].DiffComp * 0.5 + 0.15
                    elif float(self.ip_data[x]['workLineSpc']) >= 15:
                        self.ip_data[x]['workLineSpc'] = self.ip_data[x]['workLineSpc'] - 0.5
                        self.ip_data[x]['workLineWid'] = self.ip_data[x]["FINISH_LW_"] + self.layerInfo[index][
                            'compData'].impBaseComp + self.layerInfo[index]['compData'].DiffComp * 0.5 + 0.25

            if layer_mode in ['inn', 'sec1']:
                tmpnouse = ''
                self.ip_data[x]['workLineWid'], self.ip_data[x]['workLineSpc'], tmpnouse = \
                    self.dynamic_etch_space_enough(self.ip_data[x]["FINISH_LW_"], self.ip_data[x]["FINISH_LS_"], 0,
                                                   self.layerInfo[index]['compData'].impBaseComp,
                                                   self.layerInfo[index]['compData'].DiffComp,
                                                   self.layerInfo[index]['compData'].l2lspcControl)
            if self.ip_data[x]['workLineSpc'] < self.layerInfo[index]['compData'].l2lspcControl:
                self.ip_data[x]['workLineSpc'] = self.layerInfo[index]['compData'].l2lspcControl
        elif self.ip_data[x]["IMODEL"] == "差动共面":
            # 增加共面差动线宽更改
            self.ip_data[x]['workLineWid'] = self.ip_data[x]["FINISH_LW_"] + self.layerInfo[index][
                'compData'].impBaseComp + self.layerInfo[index]['compData'].CopDiffComp * 0.5
            self.ip_data[x]['workLineSpc'] = self.ip_data[x]["FINISH_LS_"] - self.layerInfo[index][
                'compData'].impBaseComp
            self.ip_data[x]['workSpc2Cu'] = self.ip_data[x]["SPC2CU"] - self.layerInfo[index][
                'compData'].impBaseComp - self.layerInfo[index]['compData'].CopDiffComp * 0.5
            if layer_mode in ['sec', 'out']:
                # === 次外层外时，为保证和板内间距一致，增加动态补偿算法 3，5，8
                self.ip_data[x]['workLineWid'], self.ip_data[x]['workLineSpc'], self.ip_data[x]['workSpc2Cu'] = \
                    self.coplane_dynamic_etch(self.ip_data[x]["FINISH_LW_"], self.ip_data[x]["FINISH_LS_"],
                                              self.ip_data[x]["SPC2CU"],
                                              self.layerInfo[index]['compData'].impBaseComp,
                                              self.layerInfo[index]['compData'].CopDiffComp,
                                              self.layerInfo[index]['compData'].l2lspcControl)
            if layer_mode in ['inn', 'sec1']:
                self.ip_data[x]['workLineWid'], self.ip_data[x]['workLineSpc'], self.ip_data[x]['workSpc2Cu'] = \
                    self.dynamic_etch_space_enough(self.ip_data[x]["FINISH_LW_"], self.ip_data[x]["FINISH_LS_"],
                                                   self.ip_data[x]["SPC2CU"],
                                                   self.layerInfo[index]['compData'].impBaseComp,
                                                   self.layerInfo[index]['compData'].CopDiffComp,
                                                   self.layerInfo[index]['compData'].l2lspcControl)
            if self.ip_data[x]['workLineSpc'] < self.layerInfo[index]['compData'].l2lspcControl:
                self.ip_data[x]['workLineSpc'] = self.layerInfo[index]['compData'].l2lspcControl
            if self.ip_data[x]['workSpc2Cu'] < self.layerInfo[index]['compData'].l2lspcControl:
                self.ip_data[x]['workSpc2Cu'] = self.layerInfo[index]['compData'].l2lspcControl

        elif self.ip_data[x]["IMODEL"] == "特性共面":
            self.ip_data[x]['workLineWid'] = self.ip_data[x]["FINISH_LW_"] + self.layerInfo[index][
                'compData'].impBaseComp + self.layerInfo[index]['compData'].CopSingleComp
            self.ip_data[x]['workLineSpc'] = 0
            self.ip_data[x]['workSpc2Cu'] = self.ip_data[x]["SPC2CU"] - self.layerInfo[index][
                'compData'].impBaseComp - self.layerInfo[index]['compData'].CopSingleComp * 0.5
            if layer_mode in ['sec', 'out']:
                self.ip_data[x]['workLineWid'], tmpnouse, self.ip_data[x]['workSpc2Cu'] = \
                    self.coplane_dynamic_etch(self.ip_data[x]["FINISH_LW_"], 0, self.ip_data[x]["SPC2CU"],
                                              self.layerInfo[index]['compData'].impBaseComp,
                                              self.layerInfo[index]['compData'].CopSingleComp,
                                              self.layerInfo[index]['compData'].l2lspcControl)
            if layer_mode in ['inn', 'sec1']:
                self.ip_data[x]['workLineWid'], tmpnouse, self.ip_data[x]['workSpc2Cu'] = \
                    self.dynamic_etch_space_enough(self.ip_data[x]["FINISH_LW_"], 0, self.ip_data[x]["SPC2CU"],
                                                   self.layerInfo[index]['compData'].impBaseComp,
                                                   self.layerInfo[index]['compData'].CopSingleComp,
                                                   self.layerInfo[index]['compData'].l2lspcControl)

            if self.ip_data[x]['workSpc2Cu'] < self.layerInfo[index]['compData'].l2lspcControl:
                self.ip_data[x]['workSpc2Cu'] = self.layerInfo[index]['compData'].l2lspcControl
                
    def dynamic_etch_space_enough(self, line_width, line_space, line2cu_space, line_base_comp, line_comp,
                                  layer_spc_control):
        """
        2021.03.11 阻抗条补偿算法，保证补偿值，间距不足最小间距时拉间距到最小间距
        :param line_width: 出货线宽
        :param line_space: 出货线距
        :param line2cu_space: 出货线到铜
        :param line_comp:动态补偿值
        :param line_base_comp:正常补偿值
        :param layer_spc_control 间距管控值
        :return:end_line_width,end_line_space,end_line2cu_space
        """
        end_line_width = line_width + line_base_comp + line_comp
        end_line_space = line_space - line_base_comp - line_comp
        if line_space == 0:
            # ===特性及特性共面===
            end_line_space = 0
        elif end_line_space < layer_spc_control:
            end_line_space = layer_spc_control

        end_line2cu_space = line2cu_space - line_base_comp - 0.5 * line_comp
        if line2cu_space == 0:
            # ===特性及差动===
            end_line2cu_space = 0
        elif end_line2cu_space < layer_spc_control:
            end_line2cu_space = layer_spc_control

        return end_line_width, end_line_space, end_line2cu_space    
        
    def coplane_dynamic_etch(self, line_width, line_space, line2cu_space, line_base_comp, line_comp,
                             layer_spc_control):
        """
        2022.09.27 按三个区间补偿判断补偿阻抗线
        :param line_width: 出货线宽
        :param line_space: 出货线距
        :param line2cu_space: 出货线到铜
        :param line_comp:动态补偿值
        :param line_base_comp:正常补偿值
        :param layer_spc_control 间距管控值
        :return:end_line_width,end_line_space,end_line2cu_space
        """
        before_line_width = line_width + line_base_comp
        before_line_space = line_space - line_base_comp
        before_line2cu_space = line2cu_space - line_base_comp
        comp_i = 0
        if before_line_space < 3:
            comp_i = 0
        elif before_line_space < layer_spc_control:
            comp_i = 0
        elif before_line_space >= 15:
            comp_i = 0.25
        elif before_line_space >= 8:
            comp_i = 0.15
        elif before_line_space >= 3:
            comp_i = 0.1

        if (layer_spc_control - 2 * comp_i) < (before_line_space - 2 * comp_i) < layer_spc_control:
            comp_i = (before_line_space - layer_spc_control) * 0.5

        comp_o = 0
        if before_line2cu_space < 3:
            comp_o = 0
        elif before_line2cu_space < layer_spc_control:
            comp_o = 0
        elif before_line2cu_space >= 15:
            comp_o = 0.25
        elif before_line2cu_space >= 8:
            comp_o = 0.15
        elif before_line2cu_space >= 3:
            comp_o = 0.1

        if line_space == 0:
            comp_i = comp_o

        if (layer_spc_control - comp_o) < (before_line2cu_space - comp_o) < layer_spc_control:
            comp_o = before_line2cu_space - layer_spc_control

        end_line_width = before_line_width + comp_i + comp_o
        end_line_space = before_line_space - comp_i * 2
        end_line2cu_space = before_line2cu_space - comp_o

        if line_space == 0:
            # ===特性及特性共面===
            end_line_space = 0
        elif end_line_space < layer_spc_control:
            end_line_space = layer_spc_control

        if line2cu_space == 0:
            # ===特性及差动===
            end_line2cu_space = 0
        elif end_line2cu_space < layer_spc_control:
            end_line2cu_space = layer_spc_control

        return end_line_width, end_line_space, end_line2cu_space        

if __name__ == "__main__":
    main = icg_coupon_compensate_value()
    main.get_dic_compensate_imp_info()
