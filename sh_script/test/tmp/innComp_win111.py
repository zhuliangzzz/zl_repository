#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2020/03/16
# @Revision     :    1.0.2
# @File         :    innComp_win.py
# @Software     :    PyCharm
# @Usefor       :    HDI一厂内层线路补偿程序
# ---------------------------------------------------------#
# pragma execution_character_set("utf-8")
import string
import threading
import math
import datetime
import sys

_header = {
    'description': '''
    -> 本程序主要服务于胜宏科技（惠州），任何其他团体或个人如需使用，必须经胜宏科技（惠州）相关负责
       人及作者的批准，并遵守以下约定；
    1> 本着尊重创作者的劳动成果，任何团体或个人在使用此程序的时候，均需要知会此程序的原始创作者；
    2> 在任何场合宣导、宣传，在任何文件、报告、邮件中提及本程序的全部或部分功能，均需要声明此程序的
       原始创作者；
    3> 在任何时候对本程序做部分修改或者是升级时，必须要保留文件的原始信息，包括原始文件名、创作者及
       联系方式、创作日期等信息，且不得删除程序中的源代码，只能进行注释处理；
'''
}

# --导入Package
import os
import re
import sys
# import genCOM_26
import innCompUI as FormUi

from PyQt4 import QtCore, QtGui
# from PyQt4.QtGui import *
# import msgBox
import json
import platform

sysstr = platform.system()

if sysstr == "Windows":
    print ("Call Windows tasks")
    sys.path.append(os.environ['GENESIS_DIR'] + '/sys/scripts/Package')

elif sysstr == "Linux":
    os.environ['GENESIS_DIR'] = '/frontline/incam'
    os.environ['GENESIS_EDIR'] = '/frontline/incam/release'
    os.environ['GENESIS_TMP'] = '/tmp'
    sys.path.append('/incam/server/site_data/scripts/Package')

else:
    print ("Other System tasks")
import Oracle_DB
import genCOM_26

import gClasses
from genesisPackages import innersignalLayers

GEN = genCOM_26.GEN_COM()

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class MyApp(object):
    def __init__(self):
        self.job_name = os.environ.get('JOB')
        # self.job_name = 's94006pf009a9'
        self.step_name = os.environ.get('STEP')
        self.scr_file = os.getcwd()  # 获取当前工作目录路径
        self.appVer = '1.4.2'


class sepByAttr:  # 自定义的元素
    def __init__(self, (thk_dowm, thk_up, rangeSpc, minWorkSpc, impBaseComp, baseLineComp)):
        self.thk_dowm = float(thk_dowm)
        self.thk_up = float(thk_up)
        self.rangeSpc = rangeSpc
        self.minWorkSpc = float(minWorkSpc)
        self.impBaseComp = float(impBaseComp) if impBaseComp != 'None' else 0
        self.baseLineComp = float(baseLineComp) if baseLineComp != 'None' else 0


class M_Box:
    """
    MesageBox提示界面
    """

    def __init__(self):
        pass

    def msgBox_option(self, body, title=u'提示信息', msgType='information'):
        """
        可供提示选择的MessagesBox
        :param body:显示内容（支持html样式）
        :param title:标题
        :param msgType:显示类型（包括information, question, warning）QtGui.QMessageBox.ButtonMask 可查看所有
        :return:
        """
        msg = QtGui.QMessageBox.information(self, u"信息", body, QtGui.QMessageBox.Ok,
                                            QtGui.QMessageBox.Cancel)  # , )
        # --返回相应信息
        if msg == QtGui.QMessageBox.Ok:
            return 'Ok'
        else:
            return 'Cancel'

    def msgBox(self, body, title=u'提示信息', msgType='information', ):
        """
        可供提示选择的MessagesBox
        :param body:显示内容（支持html样式）
        :param title:标题
        :param msgType:显示类型（包括information, question, warning）
        :return:
        """
        if msgType == 'information':
            QtGui.QMessageBox.information(self, title, body, u'确定')
        elif msgType == 'warning':
            QtGui.QMessageBox.warning(self, title, body, u'确定')
        elif msgType == 'question':
            QtGui.QMessageBox.question(self, title, body, u'确定')

    def msgText(self, body1, body2, body3=None):
        """
        转换HTML格式
        :param body1:文本1
        :param body2:文本2
        :param body3:文本3
        :return:转换后的文本
        """
        # --转换为Html文本
        textInfo = u"""
                <p>
                    <span style="background-color:#E53333;color:#FFFFFF;font-size:18px;"><strong>%s：</strong></span>
                </p>
                <p>
                    <span style="font-size:18px;">&nbsp;&nbsp;</span>
                    <span style="color:#E53333;font-size:18px;">&nbsp;&nbsp;</span>
                    <span style="color:#E53333;font-size:18px;">&nbsp; &nbsp; </span>
                    <span style="color:#E53333;font-size:16px;">%s</span>
                </p>""" % (body1, body2)

        # --返回HTML样式文本
        return textInfo


class MainInnComp(MyApp, M_Box):
    def __init__(self):
        MyApp.__init__(self)
        M_Box.__init__(self)

        M = Oracle_DB.ORACLE_INIT()
        dbc_o = M.DB_CONNECT("172.20.218.193", "inmind.fls", '1521', 'GETDATA', 'InplanAdmin')

        self.warn_list = []
        
        if dbc_o == None:
            # Mess = msgBox.Main ()
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(u'HDI InPlan 无法连接, 程序退出！')
                return
            else:
                showText = self.msgText(u'警告', u'HDI InPlan 无法连接, 程序退出！')
                self.msgBox(showText)
                exit(0)

        
        # 更改从inplan中获取的料号名应该排除后缀,本该用匹配，暂时直接使用此方法
        self.strJobName = self.job_name.split('-')[0].upper()
        # inplan中无数据返回时应提示inplan中查询不到数据
        # TODO test for show
        # self.sig_layers = ['l1', 'l2', 'l3', 'l4', 'l5', 'l6','l7','l8','l9','l10','l11','l12','l13','l14']
        # self.sig_layers = ['l1', 'l2', 'l3', 'l4', 'l5', 'l6']
        try:
            self.sig_layers = self.getJobMatrix()
        except TypeError:
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(u'运行失败, 程序退出！')
                return
            else:
                showText = self.msgText(u'警告', u'运行失败, 程序退出！')
                self.msgBox(showText)
                exit(0)

        
        self.job_layer_num = len(self.sig_layers)
        self.scrDir = os.path.split(os.path.abspath(sys.argv[0]))[0]
        os.path.realpath(sys.argv[0])
        # self.job_layer_num = len(self.sig_layers)
        self.JobData = M.getJobData(dbc_o, self.strJobName)
        if self.JobData:
            pass
        else:
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(u'HDI InPlan无料号%s数据, 程序退出！' % self.job_name)
                return
            else:                
                showText = self.msgText(u'警告', u'HDI InPlan无料号%s数据, 程序退出！' % self.job_name)
                self.msgBox(showText)
                exit(0)

        
        # 樊后星通知：20240326 by lyh
        # 线路补偿 由计算完成厚度CAL_CU_THK_，改为计算完成厚度(不考虑树脂塞孔补偿)CAL_CU_THK_PLATE_
        self.layerInfo = M.getLayerThkInfo_plate(dbc_o, self.strJobName, "inner")
        self.stackupInfo = self.get_inplan_stackup_info(M, dbc_o)
        self.twice_mrp = self.judge_mrp_two_same(self.stackupInfo)
        self.stackupInfo = self.dealWithStackUpData(self.stackupInfo)
        if len(self.twice_mrp) > 0:
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(u'HDI InPlan中记录MRP：%s不单一，会影响层别类型的判断，需确认！' % self.twice_mrp)
            else:
                showText = self.msgText(u'警告', u'HDI InPlan中记录MRP：%s不单一，会影响层别类型的判断，需确认！' % self.twice_mrp)
                self.msgBox(showText)
            

        # === 2021.01.22 取消重定义部分，直接在dealWithStackUpData中定义好内一层 ===
        # self.stackupInfo = self.reeal_layer_mode(self.stackupInfo)
        M.DB_CLOSE(dbc_o)

        # TODO 增加判断信号层层数，同时与料号名中的层数进行比对
        # 获取外层补偿规则
        self.compFileexist = 'yes'
        Outer_data = self.scrDir + '/innComp_Outer.csv'
        if os.path.exists(Outer_data):
            f = open(Outer_data)
            self.comp_data_outer = map(lambda x: x.strip().split(","), f.readlines()[1:])
            self.comp_data_outer = [sepByAttr(x) for x in self.comp_data_outer]
        else:
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(u'没有外层补偿配置文件, 程序退出！')
                return
            else:                
                showText = self.msgText(u'警告', u'没有外层补偿配置文件, 程序退出！')
                self.msgBox(showText)
                self.compFileexist = 'no'
                exit(0)


        # 获取内层补偿规则
        if os.path.exists(self.scrDir + '/innComp_Inner.ini'):
            f = open(self.scrDir + '/innComp_Inner.ini')

            self.comp_data_inner = map(lambda x: x.strip().split("\t"), f.readlines())
            self.comp_data_inner = [sepByAttr(x) for x in self.comp_data_inner]
        else:
            # Mess = msgBox.Main ()
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(u'没有内层补偿配置文件, 程序退出！')
                return
            else:                
                showText = self.msgText(u'警告', u'没有内层补偿配置文件, 程序退出！')
                self.msgBox(showText)
                self.compFileexist = 'no'
                exit(0)
         

        # 获取次一层补偿规则
        if os.path.exists(self.scrDir + '/innComp_Sec1.ini'):
            f = open(self.scrDir + '/innComp_Sec1.ini')

            self.comp_data_sec1 = map(lambda x: x.strip().split("\t"), f.readlines())
            self.comp_data_sec1 = [sepByAttr(x) for x in self.comp_data_sec1]
        else:
            # Mess = msgBox.Main ()
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(u'没有次一层补偿配置文件, 程序退出！')
                return
            else:                
                showText = self.msgText(u'警告', u'没有次一层补偿配置文件, 程序退出！')
                self.msgBox(showText)
                self.compFileexist = 'no'
                exit(0)
              

    def getJobMatrix(self):
        getInfo = GEN.DO_INFO('-t matrix -e  %s/matrix' % self.job_name)
        numCount = len(getInfo['gROWname'])
        rType = getInfo['gROWlayer_type']
        rName = getInfo['gROWname']
        rContext = getInfo['gROWcontext']
        signalLayers = []

        # 获取信号层列表
        for x in range(numCount):
            if rContext[x] == 'board' and (re.match(r'l[0-9]{1}', rName[x]) or re.match(r'l[0-9]{2}', rName[x])):
                if rType[x] == 'signal':
                    signalLayers.append(rName[x].split("-ls")[0])

        return signalLayers

    def getCouponCompListOuter(self, joblayerThk):
        # 声明一个空字典，来保存文本文件数据
        joblayerThk = float(joblayerThk)
        for line in self.comp_data_outer:  # type: sepByAttr
            if line.thk_dowm <= joblayerThk < line.thk_up:
                print 'Outer:%s,%s,%s,%s' % (joblayerThk,line.thk_dowm,line.thk_up,line.impBaseComp)
                return line

    def getCouponCompListSec1(self, joblayerThk):
        # 声明一个空字典，来保存文本文件数据
        joblayerThk = float(joblayerThk)
        for line in self.comp_data_sec1:  # type: sepByAttr
            if line.thk_dowm <= joblayerThk < line.thk_up:
                print 'Sec1:%s,%s,%s,%s' % (joblayerThk,line.thk_dowm,line.thk_up,line.impBaseComp)
                return line

    def getCouponCompListInner(self, joblayerThk):
        # 声明一个空字典，来保存文本文件数据
        joblayerThk = float(joblayerThk)
        for line in self.comp_data_inner:  # type: sepByAttr
            if line.thk_dowm <= joblayerThk < line.thk_up:
                # print 'Inner:%s,%s,%s,%s,%s' % (line.CopDiffComp,line.CopSingleComp,line.SingleComp,line.DiffComp,line.impBaseComp)
                return line

    def dealWithStackUpData(self, InpDict):
        """
        处理叠构信息
        :param InpDict:
        :return:
        """
        dataVal = InpDict
        stack_data = {}
        # 根据压合叠构整理层别类型
        for index in dataVal:
            if index['FILM_BG_'] is None:
                continue
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

            # 由于可能存在work_name 没有匹配到，重复的干膜信息，当已经获取到key了，跳出循环
            if not layerMode and (stack_data.has_key(top_bot_lay[0]) or stack_data.has_key(top_bot_lay[0])):
                continue
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

                stack_data[top_bot_lay[1]]['layerSide'] = 'bot'
                stack_data[top_bot_lay[1]]['layerMode'] = layerMode
                stack_data[top_bot_lay[1]]['materialType'] = materialType
                stack_data[top_bot_lay[1]]['df_type'] = df_type
                
        if self.job_name == "DA8608PI999A1".lower():
            top_bot_lay = ["l4", "l5"]
            stack_data[top_bot_lay[0]] = {}
            stack_data[top_bot_lay[1]] = {}
            stack_data[top_bot_lay[0]]['layerSide'] = 'top'
            stack_data[top_bot_lay[0]]['layerMode'] = 'inn'
            stack_data[top_bot_lay[0]]['materialType'] = 'core'
            stack_data[top_bot_lay[0]]['df_type'] = "Unknown"

            stack_data[top_bot_lay[1]]['layerSide'] = 'bot'
            stack_data[top_bot_lay[1]]['layerMode'] = 'inn'
            stack_data[top_bot_lay[1]]['materialType'] = 'core'
            stack_data[top_bot_lay[1]]['df_type'] = "Unknown"                

        return stack_data

    def get_inplan_stackup_info(self, M, dbc_o):
        """
        获取inplan干膜信息
        :return:
        """
        # sql = """
        #     SELECT
        #         a.item_name,
        #         c.item_name,
        #         e.film_bg_,
        #         e.DRILL_CS_LASER_ ,
        #         ENUM_DF_TYPE.value DF_TYPE_
        #     FROM
        #         vgt_hdi.public_items a
        #         INNER JOIN vgt_hdi.job b ON a.item_id = b.item_id
        #         AND a.revision_id = b.revision_id
        #         INNER JOIN vgt_hdi.public_items c ON a.root_id = c.root_id
        #         INNER JOIN vgt_hdi.process d ON c.item_id = d.item_id
        #         AND c.revision_id = d.revision_id
        #         INNER JOIN vgt_hdi.process_da e ON d.item_id = e.item_id
        #         AND d.revision_id = e.revision_id
        #         INNER JOIN VGT_HDI.field_enum_translate ENUM_DF_TYPE ON ENUM_DF_TYPE.fldname = 'DF_TYPE_'
        #         AND ENUM_DF_TYPE.enum = e.DF_TYPE_
        #         AND ENUM_DF_TYPE.intname = 'PROCESS'
        #     WHERE
        #         a.item_name = '%s'
        #         AND d.proc_type = 1
        #         AND c.item_name NOT LIKE '%%光板%%'
        #     ORDER BY
        #         e.process_num_ DESC
        # """ % self.strJobName
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

    def judge_mrp_two_same(self, stack_data):
        """
        在inplan中的AQL获取by流程的mrp，可能存在两次干膜的情况，导致取出的MRP有相同项，此处做判断，如果有相同MRP，则
        :return:
        """
        all_mrp_name = []
        twice_mrp_name = []
        for i in stack_data:
            if i['MRP_NAME'] not in all_mrp_name:
                all_mrp_name.append(i['MRP_NAME'])
            else:
                twice_mrp_name.append(i['MRP_NAME'])
        return twice_mrp_name

    def reeal_layer_mode(self, stack_data):
        """
        http://192.168.2.120:82/zentao/story-view-1913.html
        更改原程序逻辑，更改为最靠内的sec为sec1即新增定义次一层，使用次一层补偿
        :return:
        """
        half_signal_num = self.job_layer_num / 2
        # 由中间层向top面寻找第一个次外层定义，更改为次一层定义
        for i in range(int(half_signal_num), 0, -1):
            if stack_data['l%s' % i]['layerMode'] == 'sec':
                stack_data['l%s' % i]['layerMode'] = 'sec1'
                break

        for i in range(int(half_signal_num) + 1, int(self.job_layer_num), 1):
            if stack_data['l%s' % i]['layerMode'] == 'sec':
                stack_data['l%s' % i]['layerMode'] = 'sec1'
                break
        return stack_data

    def GOPEN_STEP(self, step, job=os.environ.get('JOB', None)):
        if 'INCAM_SERVER' in os.environ.keys():
            GEN.COM("set_step, name = %s" % step)
            GEN.COM("open_group, job = %s, step = %s, is_sym = no" % (job, step))
            GEN.AUX("set_group, group = %s" % GEN.COMANS)
            GEN.COM("open_entity, job = %s, type = step, name = %s, iconic = no" % (job, step))
            status = GEN.STATUS
            return status
        else:
            GEN.COM('open_entity, job=%s, type=step, name=%s ,iconic=no' % (job, step))
            GEN.AUX('set_group, group=%s' % GEN.COMANS)
            status = GEN.STATUS
            return status

    def GAFFECT_LAYERS(self, layers):
        for onelay in layers:
            if onelay != '':
                GEN.AFFECTED_LAYER(onelay, 'yes')

    def Adv_filter(self, select_type='bgapad', usesize='no', minwitdh='0', maxwidth='0.012', select_mode='yes',max_line=None):
        in_logic = "and"
        ex_logic = "or"
        include_attr = []
        exclude_attr = []
        if select_type == 'bgapad':
            filter_type = "lines=no,pads=yes,surfaces=no,arcs=no,text=no"
            include_attr.append(".bga")
        elif select_type == 'smdpad':
            filter_type = "lines=no,pads=yes,surfaces=no,arcs=no,text=no"
            include_attr.append(".smd")
        elif select_type == 'impline':
            filter_type = "lines=yes,pads=no,surfaces=no,arcs=yes,text=yes"
            include_attr.append(".imp_line")
        elif select_type == 'yibanline':
            filter_type = "lines=yes,pads=no,surfaces=no,arcs=yes,text=yes"
            exclude_attr.append(".imp_line")
        elif select_type == 'yibanpad':
            filter_type = "lines=no,pads=yes,surfaces=no,arcs=no,text=no"
            exclude_attr.append(".bga")
            exclude_attr.append(".smd")
            ex_logic = "or"
        elif select_type == 'surfacecu':
            filter_type = "lines=no,pads=no,surfaces=yes,arcs=no,text=no"

        if select_mode == "yes":
            select_opt = 'select'
        elif select_mode == "no":
            select_opt = 'unselect'

        GEN.COM("reset_filter_criteria,filter_name=,criteria=all")
        # 五种类型选哪个
        GEN.COM("set_filter_type,filter_name=,%s" % filter_type)
        # 正极性还是负极性
        GEN.COM("set_filter_polarity,filter_name=,positive=yes,negative=no")
        # profile内外
        GEN.COM("reset_filter_criteria,filter_name=,criteria=profile")
        GEN.COM("reset_filter_criteria,filter_name=popup,criteria=inc_attr")
        # 包含的属性
        if len(include_attr) != 0:
            for ii in include_attr:
                GEN.COM("set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=no,attribute=%s,"
                        "min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=" % ii)
            # 包含的属性是以及还是或者的关系
            GEN.COM("set_filter_and_or_logic,filter_name=popup,criteria=inc_attr,logic=%s" % in_logic)
        # 不包含的属性
        GEN.COM("reset_filter_criteria,filter_name=popup,criteria=exc_attr")
        if len(exclude_attr) != 0:
            for ee in exclude_attr:
                GEN.COM("set_filter_attributes,filter_name=popup,exclude_attributes=yes,condition=no,attribute=%s,"
                        "min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=" % ee)
            GEN.COM("set_filter_and_or_logic,filter_name=popup,criteria=exc_attr,logic=%s" % ex_logic)

        # 不包含的symbol
        if max_line:
            GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=no,symbols=r0.1:r%s;s0.1:s%s" % (
                max_line, max_line))
        else:
            GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=no,symbols=")
        GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=yes,symbols=")
        GEN.COM("reset_filter_criteria,filter_name=,criteria=text")
        GEN.COM("reset_filter_criteria,filter_name=,criteria=dcode")
        GEN.COM("reset_filter_criteria,filter_name=,criteria=net")
        GEN.COM("set_filter_length")
        GEN.COM("set_filter_angle")
        GEN.COM("adv_filter_reset")
        # 大小过滤 0-12mil box size设定
        if usesize != 'no':
            GEN.COM("adv_filter_set,filter_name=popup,active=yes,limit_box=no,bound_box=yes,min_width=%s,max_width=%s,"
                    "min_length=0,max_length=0,srf_values=no,srf_area=no,mirror=any,ccw_rotations=" % (
                    minwitdh, maxwidth))

        GEN.COM("filter_area_strt")
        # 选择 还是不选择
        GEN.COM("filter_area_end,filter_name=popup,operation=%s" % select_opt)


class MainWindowShow(QtGui.QWidget, MainInnComp, MyApp, M_Box):
    """
    窗体主方法
    """

    def __init__(self, parent=None):
        # MainWindow = QtGui.QMainWindow ()
        QtGui.QWidget.__init__(self, parent)
        MainInnComp.__init__(self)

        M_Box.__init__(self)
        self.ui = FormUi.Ui_MainWindow()
        self.ui.setupUi(self)
        # MainWindow.show ()
        self.addUiDetail()

    def addUiDetail(self):
        """
        在原框架基础上继续加载窗体
        :return:None
        """
        self.ui.label_title.setText(_translate("MainWindow", "HDI一厂内层线路补偿程序 料号：%s" % (self.strJobName), None))
        self.ui.bottomLabel.setText(
            _translate("MainWindow", "版权所有：胜宏科技 版本：%s 作者：Chao.Song 日期：2020.3.16" % (self.appVer), None))

        # 层别列表定义
        self.ui.tableWidget_LyrList.setAlternatingRowColors(True)
        self.ui.tableWidget_LyrList.setColumnCount(5)
        showLine = len(self.sig_layers) - 2
        self.ui.tableWidget_LyrList.setRowCount(showLine)
        # tableLyrRowWidth = [55,40,50,95,95]
        # for rr in range(len(tableLyrRowWidth)):
        #     self.ui.tableWidget_LyrList.setColumnWidth (rr, tableLyrRowWidth[rr])
        x = 0
        for k in range(len(self.sig_layers)):
            # print 'k:%s,x:%s' %(k,x)
            if self.stackupInfo[self.sig_layers[k]]['layerMode'] == 'out':
                continue
            item = QtGui.QTableWidgetItem()
            # --样式（背景色）
            brush = QtGui.QBrush(QtGui.QColor(253, 199, 77))
            brush.setStyle(QtCore.Qt.SolidPattern)
            item.setBackground(brush)
            # --样式（前景色）
            brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
            brush.setStyle(QtCore.Qt.NoBrush)
            item.setForeground(brush)
            # --位置
            self.ui.tableWidget_LyrList.setItem(x, 0, item)
            item = self.ui.tableWidget_LyrList.item(x, 0)
            # --设置文字居中
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter)
            item.setText(str(self.sig_layers[k]))
            item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
            print('aaaaaaaa', self.layerInfo)
            for index in range(len(self.layerInfo)):
                if self.layerInfo[index]['LAYER_NAME'] == self.sig_layers[k]:
                    item = QtGui.QTableWidgetItem(str(self.layerInfo[index]['CAL_CU_THK']))
                    item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
                    self.ui.tableWidget_LyrList.setItem(x, 2, item)

                    # compData = None
                    if self.stackupInfo[self.sig_layers[k]]['layerMode'] == 'out' or \
                            self.stackupInfo[self.sig_layers[k]]['layerMode'] == 'sec':
                        compData = self.getCouponCompListOuter(self.layerInfo[index]['CAL_CU_THK'])
                        self.layerInfo[index]['compData'] = compData
                        self.ui.tableWidget_LyrList.setItem(x, 4, QtGui.QTableWidgetItem(str(self.layerInfo[index]['compData'].impBaseComp)))
                        self.ui.tableWidget_LyrList.setItem(x, 3, QtGui.QTableWidgetItem(str(self.layerInfo[index]['compData'].baseLineComp)))

                    elif self.stackupInfo[self.sig_layers[k]]['layerMode'] == 'inn':
                        # print("--------------------->", self.sig_layers[k], self.layerInfo[index]['CU_WEIGHT'])
                        compData = self.getCouponCompListInner(self.layerInfo[index]['CU_WEIGHT'])
                        if compData is None:
                            showText = self.msgText(u'警告', u'{0}层 铜厚 {1} OZ超出补偿范围，请反馈主管确认, 程序退出！'.format(
                                self.sig_layers[k], self.layerInfo[index]['CU_WEIGHT']
                            ))
                            self.msgBox(showText)
                            self.compFileexist = 'no'
                            exit(0)
                            
                        self.layerInfo[index]['compData'] = compData
                        self.ui.tableWidget_LyrList.setItem(x, 4, QtGui.QTableWidgetItem(str(self.layerInfo[index]['compData'].impBaseComp)))
                        self.ui.tableWidget_LyrList.setItem(x, 3, QtGui.QTableWidgetItem(str(self.layerInfo[index]['compData'].baseLineComp)))

                    elif self.stackupInfo[self.sig_layers[k]]['layerMode'] == 'sec1':
                        compData = self.getCouponCompListSec1(self.layerInfo[index]['CAL_CU_THK'])
                        self.layerInfo[index]['compData'] = compData
                        self.ui.tableWidget_LyrList.setItem(x, 4, QtGui.QTableWidgetItem(str(self.layerInfo[index]['compData'].impBaseComp)))
                        self.ui.tableWidget_LyrList.setItem(x, 3, QtGui.QTableWidgetItem(str(self.layerInfo[index]['compData'].baseLineComp)))

            item = QtGui.QTableWidgetItem(str(self.stackupInfo[self.sig_layers[k]]['layerMode']))
            item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
            self.ui.tableWidget_LyrList.setItem(x, 1, item)
            x += 1
        # 定义其他信号
        QtCore.QObject.connect(self.ui.pushButton_4, QtCore.SIGNAL("clicked()"), self.close)
        QtCore.QObject.connect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"), self.cellChange)
        QtCore.QObject.connect(self.ui.pushButton_change_sec, QtCore.SIGNAL("clicked()"), self.change_table)

        # 填写值更改的信号
        QtCore.QObject.connect(self.ui.pushButton_3, QtCore.SIGNAL("clicked()"), self.MAIN_RUN)

    def change_table(self):
        get_result = self.msgBox_option(u"执行此按钮，会更改sec类型为sec1类型，请确认!", title=u'警告')
        if get_result == 'Cancel':
            return
        get_dict = self.getWindowInfo()
        # showline['id'] = y + 1
        # showline['worklay'] = str(self.ui.tableWidget_LyrList.item(y, 0).text())
        # showline['layerMode'] = str(self.ui.tableWidget_LyrList.item(y, 1).text())
        # showline['basecu'] = float(self.ui.tableWidget_LyrList.item(y, 2).text())
        # showline['baseComp'] = float(self.ui.tableWidget_LyrList.item(y, 3).text())
        # showline['impComp'] = float(self.ui.tableWidget_LyrList.item(y, 4).text())
        for index,line_data in enumerate(get_dict):
            if line_data['layerMode'] == 'sec':
                # item = QtGui.QTableWidgetItem(str(self.stackupInfo[self.sig_layers[k]]['layerMode']))
                # item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
                # self.ui.tableWidget_LyrList.setItem(item, 1, 'sec1')
                self.ui.tableWidget_LyrList.item(index, 1).setText('sec1')
                self.ui.tableWidget_LyrList.item(index, 1).setForeground(QtGui.QBrush(QtGui.QColor('blue')))
                print line_data['basecu']
                compData = self.getCouponCompListSec1(line_data['basecu'])
                print
                self.ui.tableWidget_LyrList.item(index, 4).setText(str(compData.impBaseComp))
                self.ui.tableWidget_LyrList.item(index, 3).setText(str(compData.baseLineComp))
                self.ui.tableWidget_LyrList.item(index, 4).setForeground(QtGui.QBrush(QtGui.QColor('blue')))
                self.ui.tableWidget_LyrList.item(index, 3).setForeground(QtGui.QBrush(QtGui.QColor('blue')))


    def cellChange(self):
        # --先断开信号的连接,以免在下面再次修改item时发生递归死循环事件发生
        QtCore.QObject.disconnect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"), self.cellChange)
        # --循环所有层并加入行
        # --获取完成铜厚 （直接从itemWidget中获取）
        items = self.ui.tableWidget_LyrList.selectedItems()
        if len(items) == 0:
            # --退出前，再次启动信号连接
            # self.ui.connect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"), self.cellChange)
            QtCore.QObject.connect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"),
                                   self.cellChange)
            return
        # --获取选中的行信息，行号，列号
        selRow = items[0].row()
        selCol = items[0].column()
        try:
            selText = str(items[0].text())
        except UnicodeEncodeError:
            showText = self.msgText(u'警告', u"'第%d行%d列' 补偿值非数字，请修改!" % (
                selRow + 1, selCol + 1))
            self.msgBox(showText)
            self.ui.tableWidget_LyrList.item(selRow, selCol).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
            QtCore.QObject.connect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"),
                                   self.cellChange)
            return False
        item_text = self.ui.tableWidget_LyrList.item(selRow, selCol).text()

        # --获取选择行的完成铜厚信息
        try:
            finishComp = float(item_text)
            # print finishComp
            if finishComp < 0:
                showText = self.msgText(u'警告', u"'第%d行%d列' 补偿值 '%s' 不是正数，请修改!" % (
                    selRow + 1, selCol + 1, item_text))
                self.msgBox(showText)
                self.ui.tableWidget_LyrList.item(selRow, selCol).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))

                QtCore.QObject.connect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"),
                                       self.cellChange)
                return False

        except ValueError:
            # Mess = msgBox.Main ()
            showText = self.msgText(u'警告', u"第%d行%d列 补偿值 %s 不是有效数字，请修改!" % (
                selRow + 1, selCol + 1, item_text))
            self.ui.tableWidget_LyrList.item(selRow, selCol).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))

            self.msgBox(showText)
            # --退出前，再次启动信号连接
            # self.ui.connect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"), self.cellChange)
            QtCore.QObject.connect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"),
                                   self.cellChange)
            return False

            # --重新更新UI数据
        # --退出前，再次启动信号连接
        QtCore.QObject.connect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"), self.cellChange)

    def getWindowInfo(self):
        # 获取Table数据，存入字典中
        getDict = []
        for y in range(len(self.sig_layers) - 2):
            # 添加str字符串类型可以转换Qstring为 String
            # key_num = y+1
            showline = {}
            showline['id'] = y + 1
            showline['worklay'] = str(self.ui.tableWidget_LyrList.item(y, 0).text())
            showline['layerMode'] = str(self.ui.tableWidget_LyrList.item(y, 1).text())
            showline['basecu'] = float(self.ui.tableWidget_LyrList.item(y, 2).text())
            showline['baseComp'] = float(self.ui.tableWidget_LyrList.item(y, 3).text())
            showline['impComp'] = float(self.ui.tableWidget_LyrList.item(y, 4).text())
            # 定义中间层结束
            getDict.append(showline)
            # print json.dumps (getDict[y], sort_keys=True, indent=2, separators=(',', ': '))
        print json.dumps(getDict, sort_keys=True, indent=2, separators=(',', ': '))
        return getDict

    def redealdictInfo(self, dictList):
        # newDict = {"baseComp":None,'impComp':None,'layerList':[]}
        # for y in range(len(dictList)):
        #     self.merge_two_dicts(dictList[y],newDict)
        newHash = {}
        # === V1.4.1 次外层单独补偿，次外层的大于等于8mil的线不需要补偿
        secHash = {}
        for hash in dictList:
            # print (hash)
            # print ("%s:%s" % (hash['worklay'], str (hash['baseComp']) + '|' + str (hash['impComp'])))
            newKey = str(hash['baseComp']) + '|' + str(hash['impComp'])
            if hash['layerMode'] == 'sec':
                if not newKey in secHash.keys():
                    secHash[newKey] = []
                secHash[newKey].append(hash['worklay'])
            else:
                if not newKey in newHash.keys():
                    newHash[newKey] = []
                newHash[newKey].append(hash['worklay'])
        return newHash,secHash
    
    def add_orig_line_width_attr(self):
        """运行补偿前把线路的原稿尺寸记录在属性内 20240926 by lyh"""
        job = gClasses.Job(self.job_name)
        step = gClasses.Step(job, self.step_name)
        step.open()
        step.COM("units,type=inch")
        for worklayer in innersignalLayers:
            step.clearAll()
            step.affect(worklayer)
            step.resetFilter()
            step.filter_set(feat_types='line;arc', polarity='positive')
            step.selectAll()
            step.resetAttr()
            if step.featureSelected():
                layer_cmd = gClasses.Layer(step, worklayer)
                feat_out = layer_cmd.featSelOut(units="inch")["lines"]
                line_symbols = list(set([obj.symbol for obj in feat_out]))
                for symbolname in line_symbols:
                    step.selectNone()
                    step.selectSymbol(symbolname)
                    if step.featureSelected():
                        step.addAttr(".orig_size_inch", attrVal=symbolname, valType='text', change_attr="yes")
                        
                    step.selectSymbol(symbolname)
                    if step.featureSelected():
                        step.addAttr(".string", attrVal="set_orig_size", valType='text', change_attr="yes")
            step.resetAttr()
                        
        step.clearAll()
        step.resetFilter()
        
    def check_compensate_is_right(self):
        """检测补偿是否一致"""
        job = gClasses.Job(self.job_name)
        step = gClasses.Step(job, self.step_name)
        step.open()
        step.COM("units,type=inch")
        
        compDict = self.getWindowInfo()
        layerCompInfo,secCompInfo = self.redealdictInfo(compDict)
        
        for dic_layer_comp in [layerCompInfo,secCompInfo]:            
            for comTwoValue in dic_layer_comp.keys():            
                for layer in dic_layer_comp[comTwoValue]:
                    #if layer not in ["l4", "l8"]:
                        #continue
                    step.removeLayer(layer+"_base_compensate_error_+++")
                    step.clearAll()
                    step.copyLayer(job.name, step.name, layer, layer+"_check")
                    step.affect(layer+"_check")
                    
                    layer_cmd = gClasses.Layer(step, layer+"_check")
                    yiban_lbc = comTwoValue.split('|')[0]
                    imp_lbc = comTwoValue.split('|')[1]
                    dic_size = {"yibanline": yiban_lbc,"impline": imp_lbc,}
                    base_compensate_not_same_indexes = {}
                    not_orig_size_lines_info = {}
                    for line_type in ["yibanline", 'impline']:
                        step.removeLayer(layer+"_"+line_type+"_"+dic_size[line_type])
                        not_orig_size_lines_info[line_type] = []
                        step.selectNone()
                        self.Adv_filter(select_type=line_type)
                        if step.featureSelected():
                            select_feat = layer_cmd.featout_dic_Index(units="inch", options="feat_index+select")
                            feat_out = select_feat["lines"]
                            feat_out += select_feat["arcs"]                    
                            
                            for obj in feat_out:
                                if getattr(obj, "orig_size_inch", None) is None:
                                    if not getattr(obj, "patch", None) and not getattr(obj, "tear_drop", None):
                                        not_orig_size_lines_info[line_type].append(int(obj.feat_index))
                                    continue
                                
                                orig_size = getattr(obj, "orig_size_inch", None)
                                if orig_size:
                                    # print(obj.symbol , orig_size , dic_size[line_type] , 111111111111111)
                                    if abs(float(obj.symbol[1:]) - float(orig_size[1:]) - 0.2 ) > 0.05 and \
                                       float(obj.symbol[1:]) < float(orig_size[1:]) + 0.2:
                                        if base_compensate_not_same_indexes.has_key(orig_size):
                                            base_compensate_not_same_indexes[orig_size].append(int(obj.feat_index))
                                        else:
                                            base_compensate_not_same_indexes[orig_size] = [int(obj.feat_index)]
                    
                    if base_compensate_not_same_indexes:
                        step.selectNone()
                        bc_value = dic_size[line_type]
                        for orig_size, indexes in base_compensate_not_same_indexes.iteritems():
                            step.selectNone()
                            step.resetFilter()
                            group_indexes = self.group_and_limit_numbers(indexes)
                            for group in group_indexes:
                                step.resetFilter()
                                step.COM("adv_filter_reset")
                                step.COM("adv_filter_set,filter_name=popup,active=yes,limit_box=no,bound_box=no,"
                                         "indexes={0},srf_values=no,srf_area=no,mirror=any,ccw_rotations=".format(group))
                                step.selectAll()                    
                                if step.featureSelected():
                                    step.addAttr(".orig_size_inch", attrVal="orig_size={0} bc_vaule={1}"
                                                 .format(orig_size, bc_value), valType='text', change_attr="yes")
                                
                                step.COM("adv_filter_reset")
                                step.COM("adv_filter_set,filter_name=popup,active=yes,limit_box=no,bound_box=no,"
                                         "indexes={0},srf_values=no,srf_area=no,mirror=any,ccw_rotations=".format(group))
                                step.selectAll()
                                if step.featureSelected():                       
                                    step.copyToLayer(layer+"_base_compensate_error_+++")
                        
                        self.warn_list.append(u"{2}检测到{0}层线路基础补偿跟程序自动补偿有差异，请到{1}层比对检查异常位置(每根线中的属性orig_size为原稿大小，bc_vaule为自动补偿值)！！"
                                              .format(layer, layer+"_base_compensate_error_+++", step.name))
                    
                    step.selectNone()                    
                    for line_type, indexes in not_orig_size_lines_info.iteritems():
                        step.selectNone()
                        if indexes:
                            group_indexes = self.group_and_limit_numbers(indexes)                            
                            for group in group_indexes:
                                step.resetFilter()
                                step.COM("adv_filter_reset")
                                step.COM("adv_filter_set,filter_name=popup,active=yes,limit_box=no,bound_box=no,"
                                         "indexes={0},srf_values=no,srf_area=no,mirror=any,ccw_rotations=".format(group))
                                step.selectAll()
                                if step.featureSelected():
                                    step.copySel(layer+"_"+line_type+"_check_"+dic_size[line_type])
                        
                    step.removeLayer(layer+"_check")
                                
        step.clearAll()
        
    def group_and_limit_numbers(self, numbers, max_length=198):
        if not numbers:
            return []
        
        # 1. 先对数字进行排序并分组连续数字
        sorted_numbers = sorted(numbers)
        groups = []
        start = sorted_numbers[0]
        prev = start
    
        for num in sorted_numbers[1:]:
            if num == prev + 1:
                prev = num
            else:
                if start == prev:
                    groups.append(str(start))
                else:
                    groups.append("%d:%d" % (start, prev))
                start = num
                prev = num
    
        # 处理最后一组
        if start == prev:
            groups.append(str(start))
        else:
            groups.append("%d:%d" % (start, prev))
    
        # 2. 将分组用分号连接，同时限制字符串长度
        result = []
        current_str = ""
    
        for group in groups:
            # 如果是第一个分组，直接添加
            if not current_str:
                current_str = group
            else:
                # 检查添加分号和新分组后是否超过长度限制
                if len(current_str) + len(group) + 1 <= max_length:
                    current_str += ";" + group
                else:
                    result.append(current_str)
                    current_str = group
    
        # 添加最后一个字符串
        if current_str:
            result.append(current_str)
    
        return result  
        
    def MAIN_RUN(self):
        self.close()
        GEN.COM('disp_off')
        GEN.COM('origin_off')
        
        self.add_orig_line_width_attr()
        
        compDict = self.getWindowInfo()
        layerCompInfo,secCompInfo = self.redealdictInfo(compDict)
        # print json.dumps(layerCompInfo, sort_keys=True, indent=2, separators=(',', ': '))

        GEN.CLEAR_LAYER()
        GEN.CHANGE_UNITS('inch')
        for comTwoValue in layerCompInfo.keys():
            GEN.CLEAR_LAYER()
            for layer in layerCompInfo[comTwoValue]:
                GEN.COM("affected_layer,name=%s,mode=single,affected=yes" % (layer))
            yiban_lbc = comTwoValue.split('|')[0]
            imp_lbc = comTwoValue.split('|')[1]
            # 一般线路补偿
            self.Adv_filter(select_type='yibanline')
            if GEN.GET_SELECT_COUNT() != 0:
                # job.PAUSE('yiban_lbc')
                GEN.COM("sel_resize,size=%s,corner_ctl=no" % (yiban_lbc))
                GEN.COM("clear_layers")
            # 阻抗线补偿
            self.Adv_filter(select_type='impline')
            if GEN.GET_SELECT_COUNT() != 0:
                # job.PAUSE('imp_lbc')
                GEN.COM("sel_resize,size=%s,corner_ctl=no" % (imp_lbc))
                GEN.COM("clear_layers")

            GEN.CLEAR_LAYER()
        for comTwoValue in secCompInfo.keys():
            GEN.CLEAR_LAYER()
            for layer in secCompInfo[comTwoValue]:
                GEN.COM("affected_layer,name=%s,mode=single,affected=yes" % (layer))
            yiban_lbc = comTwoValue.split('|')[0]
            imp_lbc = comTwoValue.split('|')[1]
            # 一般线路补偿
            # V1.4.1 大于等于8mil的不基础补偿
            # 取消次外层大于等于8mil线不补偿  http://192.168.2.120:82/zentao/story-view-7205.html
            # self.Adv_filter(select_type='yibanline',max_line=7.99)
            self.Adv_filter(select_type='yibanline')
            if GEN.GET_SELECT_COUNT() != 0:
                # job.PAUSE('yiban_lbc')
                GEN.COM("sel_resize,size=%s,corner_ctl=no" % (yiban_lbc))
                GEN.COM("clear_layers")
            # 阻抗线补偿
            self.Adv_filter(select_type='impline')
            if GEN.GET_SELECT_COUNT() != 0:
                # job.PAUSE('imp_lbc')
                GEN.COM("sel_resize,size=%s,corner_ctl=no" % (imp_lbc))
                GEN.COM("clear_layers")

            GEN.CLEAR_LAYER()
        GEN.CLEAR_LAYER()

        showText = self.msgText(u'提示', u'程序运行完成，请检查')
        self.msgBox(showText)
        GEN.COM('disp_on')
        GEN.COM('origin_on')


# # # # --程序入口
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MainWindowShow()
    if "autocheck" in sys.argv[1:]:        
        myapp.check_compensate_is_right()
        if len(myapp.warn_list) > 0:
            #arraylist_log = []
            #for s_i in myapp.warn_list:
                #arraylist_log.append(s_i['text'])
            
            with open("/tmp/check_inner_compensate_error_{0}.log".format(myapp.job_name), "w") as f:
                f.write("<br>".join(myapp.warn_list).encode("cp936"))
        else:
            with open("/tmp/check_inner_compensate_success_{0}.log".format(myapp.job_name), "w") as f:
                f.write("yes")
            
        sys.exit(0)
    else:
        myapp.show()
    
        app.exec_()
        sys.exit(0)

"""
作者：宋超
版本：V1.0.2
时间：2020.05.09
1.修改获取叠构函数，增加Core+Core支持dealWithStackUpData

作者：宋超
版本：V1.1.0
时间：2020.08.27（估计）
1.增加了内一层补偿参数获取

作者：宋超
版本：V1.2.0
时间：2021.02.02
1.更改了内一层的判断逻辑http://192.168.2.120:82/zentao/story-view-2629.html

作者：宋超
版本：V1.3.0
时间：2021.03.15
1.更改了内一层及内层部分规范http://192.168.2.120:82/zentao/story-view-2732.html

作者：宋超
版本：V1.3.1
时间：2022.04.20
1.层别类型 inn sec sec1 out的类型判断，变更为根据流程判断，可能存在MRP_NAME相同的情况，增加判断并预警；
# http://192.168.2.120:82/zentao/story-view-4199.html

作者：宋超
版本：V1.4.1
时间：2022.10.19
1.外层补偿规范变更，大于8mil的线不基础补偿
# http://192.168.2.120:82/zentao/story-view-4458.html
"""
