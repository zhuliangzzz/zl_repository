#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
__author__ = "Song"
__date__ = "20200106"
__version__ = "Revision: 5.3.0 "
__credits__ = u"""HDI一厂跑阻抗条，合并及补偿"""
__software__ = 'PyCharm'
# ---------------------------------------------------------#

import string
import threading
import math
# import datetime
from datetime import datetime

from decimal import Decimal
import copy
import os
import re
import platform
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sysstr = platform.system()
import impRunUI_v9 as FormUi
import b20ArrayImpCoupon as b20Imp
from PyQt4 import QtCore, QtGui
import json
import csv



if sysstr == "Windows":
    print ("Call Windows tasks")
    # sys.path.append(os.environ['GENESIS_DIR'] + '/sys/scripts/Package')
    sys.path.append('D:/genesis/sys/scripts/Package')
elif sysstr == "Linux":
    sys.path.append('/incam/server/site_data/scripts/Package')

else:
    print ("Other System tasks")
import Oracle_DB
import genCOM_26
from messageBox import msgBox

GEN = genCOM_26.GEN_COM()

from get_erp_job_info import get_inplan_all_flow

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


try:
    if sys.argv[1] == 'dr_type':
        run_dr_type = True
    else:
        run_dr_type = False
except:
    run_dr_type = False


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


class MyApp(object):
    def __init__(self):
        self.job_name = os.environ.get('JOB', None)
        self.step_name = os.environ.get('STEP', None)
        self.scr_file = os.getcwd()  # 获取当前工作目录路径
        self.appVer = '5.3.3'

        self.updatetime = '2023.01.11'
        # 增加线到铜皮的间距值管控，根据规范，设定为3mil
        self.l2cspcControl = 3
        self.b20job = 'no'
        if self.job_name[1:4].lower() == 'b20':
            self.b20job = 'yes'
            self.b20checlist = {}
        # === 获取inplan数据信息 ===
        M = Oracle_DB.ORACLE_INIT()
        dbc_o = M.DB_CONNECT("172.20.218.193", "inmind.fls", '1521', 'GETDATA', 'InplanAdmin')

        if dbc_o is None:
            msg_box = msgBox()
            msg_box.critical(self, '警告', 'HDI InPlan 无法连接, 程序退出！', QtGui.QMessageBox.Ok)
            exit(0)
        self.strJobName = self.job_name.split('-')[0].upper()
        # inplan中无数据返回时应提示inplan中查询不到数据，MI数据中的X及Y个数，拼版方向，最小值
        self.panelSRtable = M.getPanelSRTable(dbc_o, self.strJobName)
        if not self.panelSRtable:
            msg_box = msgBox()
            msg_box.critical(self, '警告', u'HDI InPlan无料号%s数据, 程序退出！' % self.job_name, QtGui.QMessageBox.Ok)
            exit(0)

        try:
            self.sig_layers, self.icgCamData = self.getJobMatrix()
            self.icgCamData = self.redealcoupon_place()

        except TypeError:
            msg_box = msgBox()
            msg_box.critical(self, '警告', u'运行失败, 程序退出！', QtGui.QMessageBox.Ok)
            exit(0)
        self.coupon_area = self.split_coupon_area()
        # 分割分组
        # print json.dumps (self.icgCamData, sort_keys=True, indent=2, separators=(',', ': '))
        # === 如果分组数据中有信息，且角度均一，使用数据中值，进行预填写 Song 2020.05.15
        # === 增加较小值分组判断，当x为5，y为2时，增加y其中一值的数据循环 ===
        # === 阻抗排列情况，X个数,Y个数
        # === 使用MI数据，进行阻抗分组获取 ===
        # xcorlist = [i['start_x_inch'] for i in self.icgCamData.values()]
        # ycorlist = [i['start_y_inch'] for i in self.icgCamData.values()]
        self.icgAngleData = [i['icg_angle'] for i in self.icgCamData.values()]
        self.icgHeightData = [i['icgHeight'] / 1000 for i in self.icgCamData.values()]
        self.icgLenghtData = [i['icgLength'] / 1000 for i in self.icgCamData.values()]
        self.ang_list = list(set(self.icgAngleData))
        self.xcorlist, self.ycorlist = self.get_icg_place()
        self.h_num = len(self.xcorlist)
        self.v_num = len(self.ycorlist)
        self.job_layer_num = len(self.sig_layers)
        self.scrDir = os.path.split(os.path.abspath(sys.argv[0]))[0]
        os.path.realpath(sys.argv[0])
        # self.job_layer_num = len(self.sig_layers)
        # strJobName = 'S02906PE262B1'
        # strJobName = 'S94006PF009A9'
        self.JobData = M.getJobData(dbc_o, self.strJobName)
        self.ip_data = M.get_inplan_imp(dbc_o, self.strJobName)

        self.ip_data, self.teamc, self.coupon_num = self.deal_with_sqldata(self.ip_data)
        # === 2022.12.23 增加阻抗分组数不相同的检测 ===
        if len(self.icgCamData.keys()) != self.coupon_num:
            msg_box = msgBox()
            msg_box.critical(self, '警告', u'阻抗分组数：%s 与阻抗拼版数：%s 不一致, 程序退出！' % (self.coupon_num,len(self.icgCamData.keys())), QtGui.QMessageBox.Ok)
            exit(1)
        if not self.ip_data:
            exit(1)
        # 此处记录原始的分组数
        self.recode_groups = [(d['IGROUP'], d['WGROUP'][2]) for d in self.ip_data]

        # 樊后星通知：20240326 by lyh
        # 线路补偿 由计算完成厚度CAL_CU_THK_，改为计算完成厚度(不考虑树脂塞孔补偿)CAL_CU_THK_PLATE_
        self.layerInfo = M.getLayerThkInfo_plate(dbc_o, self.strJobName)        
        self.stackupInfo = self.get_inplan_stackup_info(M, dbc_o)
        self.stackupInfo = self.dealWithStackUpData(self.stackupInfo)
        M.DB_CLOSE(dbc_o)

        self.tool_size_rule = []
        with open(self.scrDir + '/tool_size.csv') as f:
            f_csv = csv.DictReader(f)
            for row in f_csv:
                self.tool_size_rule.append(row)
        # print json.dumps(self.drl_info, sort_keys=True, indent=2, separators=(',', ': '))

        # print json.dumps (self.ip_data, sort_keys=True, indent=2, separators=(',', ': '))
        # print json.dumps (self.teamc, sort_keys=True, indent=2, separators=(',', ': '))
        # self.coupon_num = 6
        # --初始化信息
        # 阻抗测点x方向距离
        self.cedian_spc_x = 100
        # 阻抗测点y方向距离
        self.cedian_spc_y = 100
        # 阻抗测点大小
        # 测点孔径
        self.hole_wid = 29.528
        # === 内层添加测试点
        self.inner_test_add = False
        # 挡点大小
        self.md_wid = self.hole_wid + 4
        # 测点pad
        self.cedian_wid = self.hole_wid + 12
        # 测点套铜
        self.neg_wid = self.cedian_wid + 12
        # 防焊pad
        self.sm_pad = self.cedian_wid + 6
        # 阻抗线与测点距离
        self.min_p2line = 20
        # 定位孔大小
        self.dingwei_wid = 78.74

        # 阻抗线长度
        self.imp_line_length = 4000
        self.zkLength = 7000

        # === 间距控制 ===
        self.etch_space = 1.4

        # --初始化图片存储目录
        jpg_path = '/id/workfile/film'
        # TODO 增加判断信号层层数，同时与料号名中的层数进行比对
        # 获取外层补偿规则
        self.compFileexist = 'yes'
        # V2.5版本的内层及外层版本 2021.03.05 '/impCouponComp_Outer_v20.05.29.ini'
        # V4.2 版本outer_file = self.scrDir + '/impCouponComp_Outer_v22.06.16.csv'
        outer_file = self.scrDir + '/impCouponComp_Outer_v22.09.26.csv'
        # === V4.2 转换外层配置参数为csv文件，并在csv文件中添加表头。
        # ====解析方式仍然不变（暂不使用csv直接解析，不变更后续程序使用），
        if os.path.exists(outer_file):
            f = open(outer_file)
            self.comp_data_outer = map(lambda x: x.strip().split(","), f.readlines()[1:])
            self.comp_data_outer = [sepByAttr(x) for x in self.comp_data_outer]
        else:
            msg_box = msgBox()
            msg_box.critical(self, '警告', u'没有外层补偿配置文件, 程序退出！', QtGui.QMessageBox.Ok)
            self.compFileexist = 'no'
            exit(0)

        # 获取内层补偿规则
        # === 2021.03.05 /impCouponComp_Inner_v20.09.10.ini
        if os.path.exists(self.scrDir + '/test-V5.5/impCouponComp_Inner_v5.5.ini'):
            # f = open (r'impCouponComp_Inner.ini')
            f = open(self.scrDir + '/test-V5.5/impCouponComp_Inner_v5.5.ini')

            self.comp_data_inner = map(lambda x: x.strip().split("\t"), f.readlines())
            self.comp_data_inner = [sepByAttr(x) for x in self.comp_data_inner]
        else:
            msg_box = msgBox()
            msg_box.critical(self, '警告', u'没有内层补偿配置文件, 程序退出！', QtGui.QMessageBox.Ok)
            self.compFileexist = 'no'
            exit(0)

        # === 获取次一层/内一层的补偿参数
        # === 2021.03.05 /impCouponComp_Sec1_v20.09.10.ini
        if os.path.exists(self.scrDir + '/test-V5.5/impCouponComp_Sec1_v5.5.ini'):
            f = open(self.scrDir + '/test-V5.5/impCouponComp_Sec1_v5.5.ini')
            self.comp_data_sec1 = map(lambda x: x.strip().split("\t"), f.readlines())
            self.comp_data_sec1 = [sepByAttr(x) for x in self.comp_data_sec1]
        else:
            msg_box = msgBox()
            msg_box.critical(self, '警告', u'没有次一层补偿配置文件, 程序退出！', QtGui.QMessageBox.Ok)
            self.compFileexist = 'no'
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

    def getJobMatrix(self):
        """
        获取料号信号层列表，以及阻抗条信息
        :return:
        """
        getInfo = GEN.DO_INFO('-t matrix -e  %s/matrix' % self.job_name)
        numCount = len(getInfo['gROWname'])
        rType = getInfo['gROWlayer_type']
        rName = getInfo['gROWname']
        rContext = getInfo['gROWcontext']
        signalLayers = []

        # 获取信号层列表
        for x in range(numCount):
            if rContext[x] == 'board' and re.match(r'l[0-9][0-9]?', rName[x]):
                if rType[x] == 'signal':
                    signalLayers.append(rName[x])

        step_count = len(getInfo['gCOLcol'])
        gCOLstep_name = getInfo['gCOLstep_name']
        icgCAMData = {}
        icg_exist = 'no'
        icg_reg = re.compile(r'([i|I][c|C][g|G])_(0.[0-9][0-9]?)_([0-9][0-9]?)')
        for x in range(step_count):
            m_job = icg_reg.match(gCOLstep_name[x])
            if m_job:
                icg_exist = 'yes'
                # m = re.match (r'([i|I][c|C][g|G])_(0.[0-9][0-9]?)_([0-9]*)', gCOLstep_name[x])
                coupon_index = int(m_job.group(3))
                icgCAMData[coupon_index] = {}
                icgCAMData[coupon_index]['id'] = coupon_index
                icgCAMData[coupon_index]['icgStart'] = m_job.group(1)
                icgCAMData[coupon_index]['icgHeight'] = float(m_job.group(2)) * 1000
                icgCAMData[coupon_index]['icgName'] = gCOLstep_name[x]
                icgCAMData[coupon_index]['icgLength'] = 7000
                # === 以下应用一部分inplan数据 ===
                for line in range(len(self.panelSRtable)):
                    m_inplan = icg_reg.match(self.panelSRtable[line]['OP_STEP'])
                    if m_inplan:
                        if coupon_index == int(m_inplan.group(3)):
                            icgCAMData[coupon_index]['start_x_inch'] = self.panelSRtable[line]['START_X']
                            icgCAMData[coupon_index]['start_y_inch'] = self.panelSRtable[line]['START_Y']
                            icgCAMData[coupon_index]['icg_angle'] = self.panelSRtable[line]['ROTATION_ANGLE']
                            
                            icgCAMData[coupon_index]['COUPON_HEIGHT'] = self.panelSRtable[line]['COUPON_HEIGHT']
                            icgCAMData[coupon_index]['COUPON_LENGTH'] = self.panelSRtable[line]['COUPON_LENGTH']
                            icgCAMData[coupon_index]['START_X'] = self.panelSRtable[line]['START_X']
                            icgCAMData[coupon_index]['START_Y'] = self.panelSRtable[line]['START_Y']
                            icgCAMData[coupon_index]['ROTATION_ANGLE'] = self.panelSRtable[line]['ROTATION_ANGLE']                              
                # ==============================
                # DO_INFO获取阻抗条长宽
                try:
                    getlength, getheight = self.getCouponSize(gCOLstep_name[x])
                except False:
                    msg_box = msgBox()
                    msg_box.warning(self, '警告', u'获取阻抗条 %s 长宽失效!' % (gCOLstep_name[x]), QtGui.QMessageBox.Ok)
                    return False
                if round(getheight, 3) - round(float(icgCAMData[coupon_index]['icgHeight']), 3) > 0.1:
                    msg_box = msgBox()
                    msg_box.warning(self, '警告', u'Coupon %s 命名和实际资料中的阻抗条高度不符，请修改!' % (gCOLstep_name[x]),
                                    QtGui.QMessageBox.Ok)
                    return False
                if int(getlength) != 7000:
                    msg_box = msgBox()
                    msg_box.warning(self, '警告', u'Coupon %s 与默认阻抗条长度7英寸不符，使用实际阻抗条长度：%s!' % (
                        gCOLstep_name[x], getlength * 0.001),
                                    QtGui.QMessageBox.Ok)
                    # return False
                    icgCAMData[coupon_index]['icgLength'] = getlength                                      

        if icg_exist == 'no':
            # icg不存在料号中时，使用inplan数据
            l_index = 1
            for line in range(len(self.panelSRtable)):
                llc_reg = re.compile(r'([i|I][c|C][g|G])_(0.[0-9][0-9]?)_([0-9][0-9]?)|Coupon_LLC')
                # llc_reg = re.compile(r'(Coupon_LLC)')

                m = llc_reg.match(self.panelSRtable[line]['OP_STEP'])
                if m:
                    # coupon_index = int(m.group(3))
                    # coupon_index = int(l_index)
                    x_num = self.panelSRtable[line]['X_NUM']
                    y_num = self.panelSRtable[line]['Y_NUM']
                    delta_x = self.panelSRtable[line]['DELTA_X']
                    delta_y = self.panelSRtable[line]['DELTA_Y']
                    for x_order in range(x_num):
                        for y_order in range(y_num):
                            
                            coupon_index = int(l_index)
                            icgCAMData[coupon_index] = {}
                            icgCAMData[coupon_index]['start_x_inch'] = self.panelSRtable[line]['START_X'] + x_order * delta_x
                            icgCAMData[coupon_index]['start_y_inch'] = self.panelSRtable[line]['START_Y'] + y_order * delta_y
                            
                            
                            icgCAMData[coupon_index]['id'] = coupon_index
                            icgCAMData[coupon_index]['icgStart'] = m.group(1)
                            icgCAMData[coupon_index]['icgHeight'] = float(self.panelSRtable[line]['COUPON_HEIGHT']) * 1000
                            icgCAMData[coupon_index]['icgName'] = '%s_%s' % (
                                self.panelSRtable[line]['OP_STEP'].lower(), coupon_index)
                            icgCAMData[coupon_index]['icgLength'] = float(self.panelSRtable[line]['COUPON_LENGTH']) * 1000
                            icgCAMData[coupon_index]['start_x_inch'] = self.panelSRtable[line]['START_X'] + x_order * delta_x
                            icgCAMData[coupon_index]['start_y_inch'] = self.panelSRtable[line]['START_Y'] + y_order * delta_y
                            icgCAMData[coupon_index]['icg_angle'] = self.panelSRtable[line]['ROTATION_ANGLE']
                            
                            
                            icgCAMData[coupon_index]['COUPON_HEIGHT'] = self.panelSRtable[line]['COUPON_HEIGHT']
                            icgCAMData[coupon_index]['COUPON_LENGTH'] = self.panelSRtable[line]['COUPON_LENGTH']
                            icgCAMData[coupon_index]['START_X'] = self.panelSRtable[line]['START_X'] + x_order * delta_x
                            icgCAMData[coupon_index]['START_Y'] = self.panelSRtable[line]['START_Y'] + y_order * delta_y
                            icgCAMData[coupon_index]['ROTATION_ANGLE'] = self.panelSRtable[line]['ROTATION_ANGLE']
                            
                            l_index += 1
                    
        return signalLayers, icgCAMData

    def redealcoupon_place(self):
        """
        计算出每个coupon的最大值，最小值，用于后续分割分组
        :return:
        """
        new_array = {}
        # icg_reg = re.compile('(ICG|icg)_(0.\d+?)_(\d+?)')
        icg_reg = re.compile('(ICG|icg)_(0.[0-9][0-9]?)_([0-9][0-9]?)|Coupon_LLC')
        # icg_reg = re.compile('Coupon_LLC')
        # icg_reg = re.compile(r'[i|I][c|C][g|G]_0.[0-9][0-9]?_[0-9]*')
        m = 1
        # for sr_info in self.panelSRtable:
        for key in sorted(self.icgCamData.keys()):
            
            # if icg_reg.match(sr_info['OP_STEP']):
                # cur_coupon_num = icg_reg.match(i['OP_STEP']).group(3)
            sr_info = self.icgCamData[key]
            cur_coupon_num = m
            sr_info['coupon_num'] = int(cur_coupon_num)
            if sr_info.get("COUPON_HEIGHT", None) is None:
                msg_box = msgBox()
                msg_box.warning(self, '警告', u'资料内存在阻抗step跟inplan内的阻抗step命名不一致，请修改!',
                                QtGui.QMessageBox.Ok)
                sys.exit()
                
            coupon_height = float(sr_info['COUPON_HEIGHT'])
            coupon_length = float(sr_info['COUPON_LENGTH'])
            coupon_angle = sr_info['ROTATION_ANGLE']
            coupon_angle = sr_info['ROTATION_ANGLE']
            if coupon_angle == 0:
                c_xmin = sr_info['START_X']
                c_ymin = sr_info['START_Y']
                c_xmax = sr_info['START_X'] + coupon_length
                c_ymax = sr_info['START_Y'] + coupon_height
            elif coupon_angle == 90:
                c_xmin = sr_info['START_X']
                c_ymin = sr_info['START_Y'] - coupon_length
                c_xmax = sr_info['START_X'] + coupon_height
                c_ymax = sr_info['START_Y']
            elif coupon_angle == 180:
                c_xmin = sr_info['START_X'] - coupon_length
                c_ymin = sr_info['START_Y'] - coupon_height
                c_xmax = sr_info['START_X']
                c_ymax = sr_info['START_Y']
            elif coupon_angle == 270:
                c_xmin = sr_info['START_X'] - coupon_height
                c_ymin = sr_info['START_Y']
                c_xmax = sr_info['START_X']
                c_ymax = sr_info['START_Y'] + coupon_length
            else:
                msg_box = msgBox()
                msg_box.critical(self, '警告', u"阻抗条角度%s不在定义范围，程序按0度计算，运行完毕后请留意阻抗拼版方向!" % (coupon_angle), QtGui.QMessageBox.Ok)
                coupon_angle = 0
                c_xmin = sr_info['START_X']
                c_ymin = sr_info['START_Y']
                c_xmax = sr_info['START_X'] + coupon_length
                c_ymax = sr_info['START_Y'] + coupon_height
                # return False
            c_center_x = (c_xmax - c_xmin) * 0.5
            c_center_y = (c_ymax - c_ymin) * 0.5

            dx = c_xmax - c_xmin
            dy = c_ymax - c_ymin
            sr_info['xmin'] = Decimal(str(c_xmin))
            sr_info['ymin'] = Decimal(str(c_ymin))
            sr_info['xmax'] = Decimal(str(c_xmax))
            sr_info['ymax'] = Decimal(str(c_ymax))
            sr_info['dx'] = Decimal(str(dx))
            sr_info['dy'] = Decimal(str(dy))
            sr_info['center_x'] = Decimal(str(c_center_x))
            sr_info['center_y'] = Decimal(str(c_center_y))

            new_array[sr_info['coupon_num']] = sr_info
            m += 1
        # self.new_array = new_array
        # 合并到icgCAMData
        dest_dict = {}
        for a in self.icgCamData:
            # === a为阻抗编号 ===
            if a in new_array:
                # === 合并dict ===
                tmpdict = dict(self.icgCamData[a], **new_array[a])
                dest_dict[a] = tmpdict
            else:
                tmpdict = a
                dest_dict[a] = tmpdict
        return dest_dict

    def getCouponSize(self, ip_coupon):
        getStepSize = GEN.DO_INFO("-t step -e %s/%s -d PROF_LIMITS,units=inch" % (self.job_name, ip_coupon))
        gPROF_LIMITSxmin = getStepSize['gPROF_LIMITSxmin']
        gPROF_LIMITSymin = getStepSize['gPROF_LIMITSymin']
        gPROF_LIMITSxmax = getStepSize['gPROF_LIMITSxmax']
        gPROF_LIMITSymax = getStepSize['gPROF_LIMITSymax']
        if gPROF_LIMITSxmin != '0':
            msg_box = msgBox()
            msg_box.critical(self, '警告', u"Coupon %s 原点不在零点处，请修改!" % (ip_coupon), QtGui.QMessageBox.Ok)
            return False
        elif gPROF_LIMITSymin != '0':
            msg_box = msgBox()
            msg_box.critical(self, '警告', u"Coupon %s 原点不在零点处，请修改!" % (ip_coupon), QtGui.QMessageBox.Ok)
            return False
        coupon_length = round(float(gPROF_LIMITSxmax) * 1000, 0)
        coupon_height = round(float(gPROF_LIMITSymax) * 1000, 0)
        return coupon_length, coupon_height

    def split_coupon_area(self):
        """
        定义分割阻抗数据，如料号不分割，应该存在键值1
        :return:
        """
        # print self.icgCamData
        # GEN.PAUSE('XXXXXXXXXXXXXXXXXX')
        # ===增加排序，否则会造成区域分裂 Bug料号：B69-045C4(应为2区域，由于阻抗1、3不挨着，导致分成3个阻抗条区域）
        get_list = sorted(self.icgCamData, key=lambda x: (self.icgCamData[x]['xmin'], self.icgCamData[x]['ymin']))

        coupon_area = {}
        for k in get_list:
            i = self.icgCamData[k]
            if 1 not in coupon_area:
                coupon_area[1] = dict(xmin=i['xmin'], ymin=i['ymin'], xmax=i['xmax'], ymax=i['ymax'],
                                      numlist=[i['coupon_num'], ])
                continue
            get_ip_in_num = self.check_touch(i, coupon_area)
            if get_ip_in_num == 'no':
                coupon_area[len(coupon_area) + 1] = dict(xmin=i['xmin'], ymin=i['ymin'], xmax=i['xmax'], ymax=i['ymax'],
                                                         numlist=[i['coupon_num'], ])
            else:
                coupon_area[get_ip_in_num]['xmin'] = min(i['xmin'], coupon_area[get_ip_in_num]['xmin'])
                coupon_area[get_ip_in_num]['xmax'] = max(i['xmax'], coupon_area[get_ip_in_num]['xmax'])
                coupon_area[get_ip_in_num]['ymin'] = min(i['ymin'], coupon_area[get_ip_in_num]['ymin'])
                coupon_area[get_ip_in_num]['ymax'] = max(i['ymax'], coupon_area[get_ip_in_num]['ymax'])
                coupon_area[get_ip_in_num]['numlist'].append(i['coupon_num'])

        for area_i in coupon_area:
            current_array_coupon = [self.icgCamData[k] for k in coupon_area[area_i]['numlist']]
            icgAngleData = [k['ROTATION_ANGLE'] for k in current_array_coupon]
            icgHeightList = [k['COUPON_HEIGHT'] for k in current_array_coupon]
            icgHeightData = float(icgHeightList[0])
            icgLenghtList = [k['COUPON_LENGTH'] for k in current_array_coupon]
            icgLenghtData = float(icgLenghtList[0])

            # print icgAngleData
            # 以x坐标为key的字典
            xcordict = {}
            # 以y坐标为key的字典
            ycordict = {}
            for data in current_array_coupon:
                # data = current_array_coupon[i]
                if data['START_X'] in xcordict:
                    xcordict[data['START_X']].append(data['START_Y'])
                else:
                    xcordict[data['START_X']] = [data['START_Y']]

                if data['START_Y'] in ycordict:
                    ycordict[data['START_Y']].append(data['START_X'])
                else:
                    ycordict[data['START_Y']] = [data['START_X']]
            # == 取dict中key值少的那个
            use_mode = 'y'
            ycorlist = ycordict.keys()
            xcorlist = []
            # == 取每个key最长的那个
            for k in ycordict:
                if len(ycordict[k]) > len(xcorlist):
                    xcorlist = ycordict[k]
            # == 判断ycorlist中的差值是否为阻抗条的长或者宽
            if len(xcorlist) > 1:
                tmplist = sorted(xcorlist)
                if abs(tmplist[1] - tmplist[0] - icgHeightData) <= 0.001 or abs(
                        tmplist[1] - tmplist[0] - icgLenghtData) <= 0.001:
                    pass
                else:
                    use_mode = 'x'
            if len(ycorlist) > 1:
                tmplist = sorted(ycorlist)
                if abs(tmplist[1] - tmplist[0] - icgHeightData) <= 0.001 or abs(
                        tmplist[1] - tmplist[0] - icgLenghtData) <= 0.001:
                    pass
                else:
                    use_mode = 'x'
            if use_mode == 'x':
                xcorlist = xcordict.keys()
                ycorlist = []
                # == 取每个key最长的那个
                for k in xcordict:
                    if len(xcordict[k]) > len(ycorlist):
                        ycorlist = xcordict[k]
            h_num = len(xcorlist)
            v_num = len(ycorlist)
            if len(list(set(icgAngleData))) == 1:
                angle = icgAngleData[0]
                if angle == 90 or angle == 270:
                    h_num, v_num = v_num, h_num
            coupon_area[area_i]['h_num'] = h_num
            coupon_area[area_i]['v_num'] = v_num
            coupon_area[area_i]['use_mode'] = use_mode
            coupon_area[area_i]['xcorlist'] = xcorlist
            coupon_area[area_i]['ycorlist'] = ycorlist
            coupon_area[area_i]['ang_list'] = list(set(icgAngleData))

            getMaxLength = max([float(v['icgLength']) for v in current_array_coupon])
            zkLength = float(h_num * getMaxLength - 900) / h_num
            coupon_area[area_i]['each_coupon_length'] = zkLength
            for k in coupon_area[area_i]['numlist']:
                self.icgCamData[k]['each_coupon_length'] = zkLength
        return coupon_area

    def check_touch(self, ip_coupon, exist_area):
        """
        传入的单只阻抗条数据，是否在已有区域划分内，不在回传'no',在则回传区域编号
        :param ip_coupon:
        :param exist_area:
        :return:
        """
        ip_in_exist_yn = 'no'
        touch_length = None
        ip_coupon_x = ip_coupon['xmax'] - ip_coupon['xmin']
        ip_coupon_y = ip_coupon['ymax'] - ip_coupon['ymin']
        if ip_coupon_y < ip_coupon_x:
            ip_fx = 'x'
        else:
            ip_fx = 'y'

        for c in exist_area:
            x_sort_num = list(set([ip_coupon['xmin'], ip_coupon['xmax'], exist_area[c]['xmin'], exist_area[c]['xmax']]))
            y_sort_num = list(set([ip_coupon['ymin'], ip_coupon['ymax'], exist_area[c]['ymin'], exist_area[c]['ymax']]))
            if len(x_sort_num) <= 3 and len(y_sort_num) <= 3:
                # 判断长边接触或是短边接触,短边接触的直接pass，长边接触的exist_area中不能超过2个元素
                if self.job_name[1:4].lower() in ['a86', 'd10']:
                    if len(x_sort_num) == 2:
                        touch_length = ip_coupon['xmax'] - ip_coupon['xmin']

                    elif len(y_sort_num) == 2:
                        touch_length = ip_coupon['ymax'] - ip_coupon['ymin']

                    if touch_length:
                        if (ip_fx == 'x' and touch_length == ip_coupon_x) or (
                                ip_fx == 'y' and touch_length == ip_coupon_y):
                            if len(exist_area[c]['numlist']) < 4:
                                ip_in_exist_yn = c
                else:
                    ip_in_exist_yn = c

            else:
                # === 增加品字形阻抗条排列的判断，使用以上判断会被判断成两个区域 ===
                if (exist_area[c]['xmin'] - ip_coupon['dx']) <= ip_coupon['xmin'] < ip_coupon['xmax'] <= (exist_area[c]['xmax'] + ip_coupon['dx']) \
                        and (exist_area[c]['ymin'] - ip_coupon['dy']) <= ip_coupon['ymin'] < ip_coupon['ymax'] <= (exist_area[c]['ymax'] + ip_coupon['dy']):
                    ip_in_exist_yn = c

        return ip_in_exist_yn


    def get_icg_place(self):
        """
        或者阻抗排列，x方向几个，Y方向几个
        :return:
        """
        # 以x坐标为key的字典
        xcordict = {}
        # 以y坐标为key的字典
        ycordict = {}
        for i in self.icgCamData:
            data = self.icgCamData[i]
            if data['start_x_inch'] in xcordict:
                xcordict[data['start_x_inch']].append(data['start_y_inch'])
            else:
                xcordict[data['start_x_inch']] = [data['start_y_inch']]

            if data['start_y_inch'] in ycordict:
                ycordict[data['start_y_inch']].append(data['start_x_inch'])
            else:
                ycordict[data['start_y_inch']] = [data['start_x_inch']]
        # == 取dict中key值少的那个
        use_mode = 'y'
        ycorlist = ycordict.keys()
        xcorlist = []
        # == 取每个key最长的那个
        for k in ycordict:
            if len(ycordict[k]) > len(xcorlist):
                xcorlist = ycordict[k]
        # == 判断ycorlist中的差值是否为阻抗条的长或者宽
        if len(xcorlist) > 1:
            tmplist = sorted(xcorlist)
            if abs(tmplist[1] - tmplist[0] - self.icgHeightData[0]) <= 0.001 or abs(
                    tmplist[1] - tmplist[0] - self.icgLenghtData[0]) <= 0.001:
                pass
            else:
                use_mode = 'x'
        if len(ycorlist) > 1:
            tmplist = sorted(ycorlist)
            if abs(tmplist[1] - tmplist[0] - self.icgHeightData[0]) <= 0.001 or abs(
                    tmplist[1] - tmplist[0] - self.icgLenghtData[0]) <= 0.001:
                pass
            else:
                use_mode = 'x'
        if use_mode == 'x':
            xcorlist = xcordict.keys()
            ycorlist = []
            # == 取每个key最长的那个
            for k in xcordict:
                if len(xcordict[k]) > len(ycorlist):
                    ycorlist = xcordict[k]
        return xcorlist, ycorlist

    def deal_with_sqldata(self, inpVal):
        """
        从InPlan获取数据，并对数据进行简单分组
        :param inpVal:
        :return:
        """
        # global teamc,coupon_num
        teamc = {}
        # 1.从InPlan获取数据，并对数据进行简单分组
        # 1.所有阻抗的排列存入teamc字典中，包含阻抗大分组IGROUP，阻抗小序号WGROUP，阻抗信号层
        # 2.增加参考层写入
        # 对字典数据进行根据信号层别排序（去除首字母，依照数字方式排序）
        x = inpVal
        # == 测试如果不重新排序是否会有问题 Song 2020.05.15===
        # === 存在InPlan数据不完整时，无法继续运行的情况
        try:
            dataVal = sorted(x, key=lambda x: int(x['TRACE_LAYER_'][1:]))
        except TypeError:
            get_info = [i['ORD_INDEX'] for i in x if i['TRACE_LAYER_'] is None]
            msg_box = msgBox()
            msg_box.critical(self, '程序将以10004退出', u"InPlan数据中序号：%s，有阻抗的层别信息为空,无法继续跑阻抗条!" % get_info, QtGui.QMessageBox.Ok)
            return None,None,None
        # == 测试结束，以上排序会分布同层阻抗线连续排列，不能更改以上语句 ===
        ind = 1
        for line in range(len(dataVal)):
            # 转化浮点数保留四位小数
            dataVal[line]['FINISH_LS_'] = round(dataVal[line]['FINISH_LS_'], 4)
            dataVal[line]['WORK_WIDTH'] = round(dataVal[line]['WORK_WIDTH'], 4)
            dataVal[line]['FINISH_LW_'] = round(dataVal[line]['FINISH_LW_'], 4)            
                
            dataVal[line]['ORG_WIDTH'] = round(dataVal[line]['ORG_WIDTH'], 2)
            try:                
                dataVal[line]['ORG_SPC'] = round(dataVal[line]['ORG_SPC'], 2)
            except:
                dataVal[line]['ORG_SPC'] = 0
            try:                
                dataVal[line]['ORG_CU_SPC'] = round(dataVal[line]['ORG_CU_SPC'], 2)
            except:
                dataVal[line]['ORG_CU_SPC'] = 0
            # 如果有EQ线宽 则要把成品显示为EQ线宽 
            # 翟鸣通知 此eq线宽只显示在阻抗条上 实际还是按成品线宽来补偿 20240827 by lyh
            dataVal[line]['EQ_LW_'] = round(dataVal[line]['EQ_LW_'], 2)
            dataVal[line]['EQ_LS_'] = round(dataVal[line]['EQ_LS_'], 2)
            dataVal[line]['EQ_SPACING_2_COPPER_'] = round(dataVal[line]['EQ_SPACING_2_COPPER_'], 2)            
            #if dataVal[line]['EQ_LW_'] != 0:
                #dataVal[line]['FINISH_LW_'] = round(dataVal[line]['EQ_LW_'], 4)
            #if dataVal[line]['EQ_LS_'] != 0:
                #dataVal[line]['FINISH_LS_'] = round(dataVal[line]['EQ_LS_'], 4)
            #if dataVal[line]['EQ_SPACING_2_COPPER_'] != 0:
                #dataVal[line]['SPC2CU'] = round(dataVal[line]['EQ_SPACING_2_COPPER_'], 4)
            # 记录所有阻抗序号
            # dataVal[line]['ID'] = ind
            dataVal[line]['ID'] = int(dataVal[line]['ORD_INDEX'])
            dataVal[line]['midlyrs'] = []
            # 判断参考层中是否存在&符号，如存在则区分上下参考层
            if dataVal[line]['REF_LAYER_'] == '' or not dataVal[line]['REF_LAYER_']:
                # 空层无法判断，默认为正
                dataVal[line]['textmir'] = 'no'
                dataVal[line]['REF_TOP'] = ''
                dataVal[line]['REF_BOT'] = ''
                # 写入所有信号层均为midlyrs
                dataVal[line]['midlyrs'] = [i for i in self.sig_layers]
            elif '&' in dataVal[line]['REF_LAYER_']:
                # print line
                ref_top = dataVal[line]['REF_LAYER_'].split('&')[0]
                ref_bot = dataVal[line]['REF_LAYER_'].split('&')[1]
                dataVal[line]['REF_TOP'] = ref_top
                dataVal[line]['REF_BOT'] = ref_bot
                # 定义中间层，包含信号层，不包含参考层,用于后续是否有交叉层判断
                if int(ref_bot[1:]) - int(ref_top[1:]) > 1:
                    # 参考层底层大于顶层，添加字正字
                    dataVal[line]['textmir'] = 'no'
                    for i in range(int(ref_top[1:]) + 1, int(ref_bot[1:])):
                        dataVal[line]['midlyrs'].append("l%s" % i)
                elif int(ref_bot[1:]) - int(ref_top[1:]) < -1:
                    # 参考层顶层大于底层，添加字反字
                    dataVal[line]['textmir'] = 'yes'
                    for i in range(int(ref_bot[1:]) + 1, int(ref_top[1:])):
                        dataVal[line]['midlyrs'].append("l%s" % i)
            else:
                # 单层参考层的情况
                ref_layer_num = dataVal[line]['REF_LAYER_'][1:]
                work_layer_num = dataVal[line]['TRACE_LAYER_'][1:]
                dataVal[line]['midlyrs'].append(dataVal[line]['TRACE_LAYER_'].lower())
                if int(ref_layer_num) > int(work_layer_num):
                    dataVal[line]['textmir'] = 'no'
                    dataVal[line]['REF_TOP'] = ''
                    dataVal[line]['REF_BOT'] = dataVal[line]['REF_LAYER_']
                    top = work_layer_num
                    bot = ref_layer_num
                    # 单层参考为非top、bot层别时，增加其他层别为中间层
                    if int(work_layer_num) != 1:
                        for i in range(1, int(top)):
                            dataVal[line]['midlyrs'].append("l%s" % i)
                else:
                    dataVal[line]['textmir'] = 'yes'
                    dataVal[line]['REF_TOP'] = dataVal[line]['REF_LAYER_']
                    dataVal[line]['REF_BOT'] = ''
                    top = ref_layer_num
                    bot = work_layer_num
                    if int(work_layer_num) != int(self.job_layer_num):
                        for i in range(int(bot), int(self.job_layer_num) + 1):
                            dataVal[line]['midlyrs'].append("l%s" % i)
                # 信号层与参考层中间有空层
                if int(bot) - int(top) >= 2:
                    for i in range(int(top) + 1, int(bot)):
                        dataVal[line]['midlyrs'].append("l%s" % i)

            # 数据二次分组，区分上中下小分组 #
            dataVal[line]['WGROUP'] = []
            fir_group = dataVal[line]['IGROUP']
            sec_group = 0
            # 进行分组，如果中间层别不存在交叉，则添加到已有分组
            if fir_group in teamc:
                check_add = 'no'
                for i in teamc[fir_group]['sec_g']:
                    list1 = teamc[fir_group][i]
                    list2 = [x for x in dataVal[line]['midlyrs']]
                    # 增加参考层是否已在列表中的判断，排除Bug L5参考L6，L6参考L5分到一组的情况
                    if dataVal[line]['REF_TOP'] != '':
                        list2.append(dataVal[line]['REF_TOP'].lower())
                    if dataVal[line]['REF_BOT'] != '':
                        list2.append(dataVal[line]['REF_BOT'].lower())
                    a = [x for x in list1 if x in list2]  # 两个列表表都存在
                    if len(a) == 0:
                        check_add = 'yes'
                        teamc[fir_group][i].extend(dataVal[line]['midlyrs'])
                        teamc[fir_group]['siglyr'].append(dataVal[line]['TRACE_LAYER_'])
                        sec_group = i
                        break
                # 如果中间层别存在交叉，则新建分组
                if check_add == 'no':
                    sec_group = len(teamc[fir_group]['sec_g']) + 1
                    # teamc[fir_group] = {'count': [1], 1: dataVal[line]['midlyrs']}
                    teamc[fir_group][sec_group] = []
                    teamc[fir_group][sec_group].extend(dataVal[line]['midlyrs'])
                    teamc[fir_group]['sec_g'].append(sec_group)
                    teamc[fir_group]['siglyr'].append(dataVal[line]['TRACE_LAYER_'])
                teamc[fir_group]['sec_detail'].append(sec_group)
                teamc[fir_group]['id_g'].append(ind)
                tmp_count = len(teamc[fir_group]['siglyr'])
                dataVal[line]['WGROUP'] = [fir_group, tmp_count, sec_group]
            else:
                # 当阻抗信息一次添加时，创建分组信息,
                # sec_g 已存在二分组
                # 数字，对应二分组中间层及信号层列表
                # siglyr：信号层列表
                # id_g: 信号层列表一一对应所有阻抗信息ID列表
                # sec_detail: 信号层列表一一对应的二分组信息
                # model 阻抗类型
                teamc[fir_group] = {'sec_g': [1],
                                    1: [x for x in dataVal[line]['midlyrs']],
                                    'siglyr': [dataVal[line]['TRACE_LAYER_']],
                                    'sec_detail': [1],
                                    'id_g': [ind],
                                    # 'model': dataVal[line]['IMODEL']
                                    }
                dataVal[line]['WGROUP'] = [dataVal[line]['IGROUP'], 1, 1]
            ind += 1
        # print json.dumps(dataVal, sort_keys=True, indent=2, separators=(',', ': '))
        tmp_num = list(map(int, teamc.keys()))
        coupon_num = max(tmp_num)
        return dataVal, teamc, coupon_num

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

            # 由于可能存在work_name 没有匹配到，重复的干膜信息，当已经获取到key了，跳出循环
            if not layerMode and (stack_data.has_key(top_bot_lay[0]) or stack_data.has_key(top_bot_lay[1])):
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
                # stack_data[top_bot_lay[0]]['film_bg'] = top_bot_lay[1]

                stack_data[top_bot_lay[1]]['layerSide'] = 'bot'
                stack_data[top_bot_lay[1]]['layerMode'] = layerMode
                stack_data[top_bot_lay[1]]['materialType'] = materialType
                stack_data[top_bot_lay[1]]['df_type'] = df_type
                # stack_data[top_bot_lay[1]]['film_bg'] = top_bot_lay[0]
        return stack_data


class MainWindowShow(QtGui.QWidget, MyApp):
    """
    窗体主方法
    """

    def __init__(self, parent=None):
        # MainWindow = QtGui.QMainWindow ()
        QtGui.QWidget.__init__(self, parent)
        MyApp.__init__(self)
        self.ui = FormUi.Ui_MainWindow()
        self.ui.setupUi(self)
        self.resize(1280, 700)
        # MainWindow.show ()
        self.addUiDetail()

    def addUiDetail(self):
        """
        在原框架基础上继续加载窗体
        :return:None
        """
        # === V5.1 暂时不勾选 添加孔
        self.ui.checkBox_innerpad.setChecked(True)
        self.ui.label_title.setText(_translate("MainWindow", "HDI一厂阻抗条程序 料号：%s" % (self.job_name), None))
        
        if self.job_name[1:4] in ["a86", "d10"]:
            self.ui.laser_inner_hole.setChecked(True)
            
        self.ui.pushButton_change_sec.setFixedHeight(25)

        # self.ui.bottomLabel.setText(
        #     _translate("MainWindow", "版权所有：胜宏科技 版本：%s 作者：Chao.Song 更新日期：%s" % (self.appVer, self.updatetime), None))

        for tmp_x in range(1, self.coupon_num + 1):
            self.ui.comboBox_xDirec.addItem(str(tmp_x))

        for tmp_y in range(1, self.coupon_num + 1):
            self.ui.comboBox_yDirec.addItem(str(tmp_y))
        self.changeShow2('Y')

        if len(self.ang_list) == 1:
            if self.ang_list[0] == 0 or self.ang_list[0] == 180:
                self.ui.comboBox_xDirec.setCurrentIndex(self.h_num - 1)
                self.ui.comboBox_yDirec.setCurrentIndex(self.v_num - 1)
            elif self.ang_list[0] == 90 or self.ang_list[0] == 270:
                self.ui.comboBox_xDirec.setCurrentIndex(self.v_num - 1)
                self.ui.comboBox_yDirec.setCurrentIndex(self.h_num - 1)

        my_regex = QtCore.QRegExp("[1-9][0-9]?\.[0-9][0-9][0-9]?")
        my_validator = QtGui.QRegExpValidator(my_regex, self.ui.lineEdit_dingweiMil)
        self.ui.lineEdit_dingweiMil.setValidator(my_validator)
        self.ui.lineEdit_dingweiMil.setText(str(self.dingwei_wid))

        my_validator = QtGui.QRegExpValidator(my_regex, self.ui.lineEdit_dingweiMM)
        self.ui.lineEdit_dingweiMM.setValidator(my_validator)
        self.ui.lineEdit_dingweiMM.setText(str(self.dingwei_wid))
        self.chglinedingweiMil()
        self.ui.lineEdit_dingweiMil.setDisabled(True)

        my_regex = QtCore.QRegExp("[0-9]\.[0-9]?")
        my_validator = QtGui.QRegExpValidator(my_regex, self.ui.lineEdit_Xpitch)
        self.ui.lineEdit_Xpitch.setValidator(my_validator)
        self.ui.lineEdit_Xpitch.setText(str(self.cedian_spc_x))
        self.ui.lineEdit_Xpitch.setDisabled(True)

        my_regex = QtCore.QRegExp("[0-9]\.[0-9]?")
        my_validator = QtGui.QRegExpValidator(my_regex, self.ui.lineEdit_Ypitch)
        self.ui.lineEdit_Ypitch.setValidator(my_validator)
        self.ui.lineEdit_Ypitch.setText(str(self.cedian_spc_y))
        self.ui.lineEdit_Ypitch.setDisabled(True)

        my_validator = QtGui.QRegExpValidator(my_regex, self.ui.lineEdit_ceshiMil)
        self.ui.lineEdit_ceshiMil.setValidator(my_validator)
        self.ui.lineEdit_ceshiMil.setText(str(self.hole_wid))
        my_regex = QtCore.QRegExp("[0-9]\.[0-9][0-9]?[0-9]?")
        my_validator = QtGui.QRegExpValidator(my_regex, self.ui.lineEdit_ceshiMM)
        self.ui.lineEdit_ceshiMM.setValidator(my_validator)
        self.ui.lineEdit_ceshiMM.setText(str(self.hole_wid))
        self.chglineceshiMil()
        self.ui.lineEdit_ceshiMil.setDisabled(True)

        # === 更改层别列表定义 ===
        self.table_laylist_set()

        # === 2021.03.01 增加阻抗分组连续监测（序号连续） ===
        check_all_coupon_num = [i['IGROUP'] for i in self.ip_data]
        check_all_coupon_num = list(set(check_all_coupon_num))
        check_all_coupon_num.sort()

        if check_all_coupon_num == range(1, len(check_all_coupon_num) + 1, 1):
            pass
        else:
            showText = u"阻抗分组不连续，现在为%s, 当阻抗分组为0时，认为未分组，请联系MI处理!" % (check_all_coupon_num)
            msg_box = msgBox()
            msg_box.warning(self, '警告', showText, QtGui.QMessageBox.Ok)
            self.ui.pushButton_3.hide()
        # TODO === 同一阻抗条中，有多个阻抗类型 2022.11.01 屏蔽 ===
        self.check_all_mode = {}
        for ig in check_all_coupon_num:
            check_current_mode = [i['IMODEL'] for i in self.ip_data if i['IGROUP'] == ig]
            check_current_mode = list(set(check_current_mode))
            # === 如果都是是特性+差分的组合，或者差动共面+特性共面的组合则pass，否则NG
            check_result = False
            if len(check_current_mode) >= 3:
                check_result = False
            elif len(check_current_mode) == 2:
                if set(check_current_mode) == set(['特性', '差动']) or set(check_current_mode) == set(['差动共面', '特性共面']):
                    check_result = True
            elif len(check_current_mode) == 1:
                check_result = True
            self.check_all_mode[ig] = check_result
            if not self.check_all_mode[ig]:
                self.ui.pushButton_3.hide()

        # === 2021.03.04 增加阻抗组数不相同判断 ===
        if self.coupon_num != len(check_all_coupon_num):
            showText = u"阻抗分组数据不相同，inplan中为：%s，CAM获取为%s!" % (len(check_all_coupon_num), self.coupon_num)
            msg_box = msgBox()
            msg_box.warning(self, '警告', showText, QtGui.QMessageBox.Ok)
            self.ui.pushButton_3.hide()

        # === 阻抗线表确定=== ()
        self.imp_table_set()

        # === V4.0.1 增加分割阻抗，界面做变更 ===
        if len(self.coupon_area) > 1:
            self.ui.comboBox_xDirec.hide()
            self.ui.comboBox_yDirec.hide()
            self.ui.label_xDirec.setText(_translate("MainWindow", u'分割阻抗条', None))
            self.ui.label_yDirec.setText(_translate("MainWindow", u'不选择排列', None))
            self.ui.label_xDirec.setMaximumSize(QtCore.QSize(100, 25))
            self.ui.label_yDirec.setMaximumSize(QtCore.QSize(100, 25))
            self.ui.label_xDirec.setStyleSheet('QLabel{color: blue}')
            self.ui.label_yDirec.setStyleSheet('QLabel{color: blue}')
        else:
            self.ui.comboBox_xDirec.hide()
            self.ui.comboBox_yDirec.hide()
            self.ui.label_xDirec.setText(_translate("MainWindow", u'使用InPlan数据', None))
            self.ui.label_yDirec.setText(_translate("MainWindow", u'不选择XY排列', None))
            self.ui.label_xDirec.setMaximumSize(QtCore.QSize(100, 25))
            self.ui.label_yDirec.setMaximumSize(QtCore.QSize(100, 25))
            self.ui.label_xDirec.setStyleSheet('QLabel{color: blue}')
            self.ui.label_yDirec.setStyleSheet('QLabel{color: blue}')

        # 定义其他信号
        QtCore.QObject.connect(self.ui.pushButton_4, QtCore.SIGNAL("clicked()"), self.close)
        QtCore.QObject.connect(self.ui.comboBox_xDirec, QtCore.SIGNAL("currentIndexChanged(int)"), self.changeShowX)
        QtCore.QObject.connect(self.ui.comboBox_yDirec, QtCore.SIGNAL("currentIndexChanged(int)"), self.changeShowY)
        QtCore.QObject.connect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"), self.cellChange)
        QtCore.QObject.connect(self.ui.pushButton_change_sec, QtCore.SIGNAL("clicked()"), self.change_table_laylist)

        # 填写值更改的信号

        self.ui.lineEdit_ceshiMM.textChanged.connect(self.chglineceshiMM)
        self.ui.lineEdit_dingweiMM.textChanged.connect(self.chglinedingweiMM)

        QtCore.QObject.connect(self.ui.pushButton_3, QtCore.SIGNAL("clicked()"), self.MAIN_RUN)

    def imp_table_set(self):

        # 定义阻抗列表
        self.ui.tableWidget.setRowCount(len(self.ip_data))
        # self.ui.tableWidget.setColumnCount (len (tableList))
        if self.b20job == 'yes' and run_dr_type:
            msg_box = msgBox()
            msg_box.critical(self, '警告', u"B20客户不能选择勾选模式!", QtGui.QMessageBox.Ok)
            sys.exit(0)
        if self.b20job == 'yes' or run_dr_type:
            self.ui.tableWidget.setColumnCount(18)
        else:
            self.ui.tableWidget.setColumnCount(17)

        # self.ui.tableWidget.setHorizontalHeaderLabels (tableList)
        if not run_dr_type:
            self.ui.tableWidget.setEditTriggers(QtGui.QTableWidget.NoEditTriggers)
            self.ui.tableWidget.setSelectionBehavior(QtGui.QTableWidget.SelectRows)
            self.ui.tableWidget.setSelectionMode(QtGui.QTableWidget.SingleSelection)
        # self.ui.tableWidget.verticalHeader.hide ()
        self.ui.tableWidget.setAlternatingRowColors(True)

        tableRowWidth = [65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 95, 65, 65, 65, 65, 60, 60, 60, 75]
        for rr in range(len(tableRowWidth)):
            self.ui.tableWidget.setColumnWidth(rr, tableRowWidth[rr])

        index_s0, index_s9 = [], []

        for x, line in enumerate(self.ip_data):

            x_layer = line["TRACE_LAYER_"].lower()
            # === 先计算出阻抗线补偿后的值
            for l_index, lyr_data in enumerate(self.layerInfo):
                l_layer = lyr_data['LAYER_NAME'].lower()
                if l_layer == x_layer:
                    # === 计算补偿值 ===
                    self.imp_comp(x, l_layer, l_index)
                    x_l2lspcControl = self.layerInfo[l_index]['compData'].l2lspcControl * 1
            # === 列表达式
            column_keys = ['IGROUP', "TRACE_LAYER_", "FINISH_LW_", "FINISH_LS_", "SPC2CU", "REF_TOP", "REF_BOT",
                           "ORG_WIDTH", "IMODEL", "WGROUP2", "SOLDEROPEN", "CUSIMP", 'workLineWid', 'workLineSpc',
                           'workSpc2Cu', 'WGROUP1', 'ID']
            for c_index, c_key in enumerate(column_keys):
                if c_key not in ['WGROUP1', 'WGROUP2', "FINISH_LW_", "FINISH_LS_", "SPC2CU",]:
                    self.table_item_set(x, c_index, text=line[c_key])                
                if c_key == "IGROUP" and line[c_key] == 0:
                    self.table_item_set(x, c_index, bg='red')
                if c_key == 'TRACE_LAYER_':
                    self.table_item_set(x, c_index, text=x_layer)

                if c_key == "IMODEL" and not self.check_all_mode[line["IGROUP"]]:
                    self.table_item_set(x, c_index, bg='red')
                if c_key == "WGROUP2":  # 是个列表
                    g_key = "WGROUP"
                    self.table_item_set(x, c_index, text=line[g_key][2])
                    if line[g_key][2] >= 4:
                        self.table_item_set(x, c_index, bg='red')
                        # self.ui.pushButton_3.hide()
                if c_key == 'SOLDEROPEN' and line[c_key] == '是':
                    self.table_item_set(x, c_index, bg='green', fg='white')
                if c_key == 'workLineSpc' and line[c_key] <= x_l2lspcControl and line[c_key] != 0:
                    self.table_item_set(x, c_index, bg='yellow')
                if c_key == 'workSpc2Cu' and line[c_key] <= self.l2cspcControl and line[c_key] != 0:
                    self.table_item_set(x, c_index, bg='yellow')

                if c_key == "WGROUP1":  # 是个列表
                    g_key = "WGROUP"
                    self.table_item_set(x, c_index, text=line[g_key][1])
                    
                if c_key == "FINISH_LW_":
                    if run_dr_type:
                        if line["EQ_LW_"] != 0:
                            self.table_item_set(x, c_index, text=line["EQ_LW_"])
                        else:
                            if line["ORG_WIDTH"] != 0:
                                self.table_item_set(x, c_index, text=line["ORG_WIDTH"])
                            else:
                                self.table_item_set(x, c_index, text=line[c_key])
                    else:
                        self.table_item_set(x, c_index, text=line[c_key])

                if c_key == "FINISH_LS_":
                    if run_dr_type:
                        if line["EQ_LS_"] != 0:
                            self.table_item_set(x, c_index, text=line["EQ_LS_"])
                        else:
                            if line["ORG_SPC"] != 0:
                                self.table_item_set(x, c_index, text=line["ORG_SPC"])
                            else:
                                self.table_item_set(x, c_index, text=line[c_key])
                    else:
                        self.table_item_set(x, c_index, text=line[c_key])

                if c_key == "SPC2CU":
                    if run_dr_type:
                        if line["EQ_SPACING_2_COPPER_"] != 0:
                            self.table_item_set(x, c_index, text=line["EQ_SPACING_2_COPPER_"])
                        else:
                            if line["ORG_CU_SPC"] != 0:
                                self.table_item_set(x, c_index, text=line["ORG_CU_SPC"])
                            else:
                                self.table_item_set(x, c_index, text=line[c_key])
                    else:
                        self.table_item_set(x, c_index, text=line[c_key])

                if c_key == "FINISH_LW_" and float(line[c_key]) > 20:
                    self.table_item_set(x, c_index, bg='green', fg='white', tool_tip='底色绿色时为非常规设计,注意检查.')
                if c_key == "FINISH_LS_" and float(line[c_key]) > 20:
                    self.table_item_set(x, c_index, bg='green', fg='white', tool_tip='底色绿色时为非常规设计,注意检查.')
                if c_key == "SPC2CU" and float(line[c_key]) > 20:
                    self.table_item_set(x, c_index, bg='green', fg='white', tool_tip='底色绿色时为非常规设计,注意检查.')

            # 增加B20 阻抗序号列
            if self.b20job == 'yes':
                item = self.ui.tableWidget.horizontalHeaderItem(17)
                item.setText(_translate("MainWindow", u"客户分组", None))
                self.ui.tableWidget.setColumnWidth(17, 60)
                # lineitem = QtGui.QLineEdit()

                # item = QtGui.QTableWidgetItem ()
                # item.setTextAlignment (QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter)
                # # item.setCheckState (QtCore.Qt.Checked )
                # self.ui.tableWidget.setItem (x, 17, item)
                #
                my_regex = QtCore.QRegExp("[0-9]")
                self.b20checlist[x] = QtGui.QLineEdit()

                my_validator = QtGui.QRegExpValidator(my_regex, self.b20checlist[x])
                self.b20checlist[x].setValidator(my_validator)
                self.ui.tableWidget.setCellWidget(x, 17, self.b20checlist[x])
                if x != 0:
                    self.ui.tableWidget.setTabOrder(self.b20checlist[x - 1], self.b20checlist[x])

            if run_dr_type:
                item = self.ui.tableWidget.horizontalHeaderItem(17)
                item.setText(_translate("MainWindow", u"勾选阻抗条", None))
                self.ui.tableWidget.setColumnWidth(17, 60)
                ck_box = self.addCheckBox(False)
                self.ui.tableWidget.setCellWidget(x, 17, ck_box)
                ck_box.clicked.connect(self.reset_coupon_group)


    def reset_coupon_group(self):
        """
        对勾选的阻抗条重新进行大分组,取消勾选时候要还原成原始分组，需要先记录 未勾选时候的数据
        """
        rows = self.ui.tableWidget.rowCount()
        checked_sel = []
        sel_ipdata = []
        send_ipdata = []
        normal_ipdata = []
        self.sel_ip_data, self.sel_teamc, self.sel_coupon_num = [], [], []
        self.mormal_ip_data = []

        for i in range(rows):
            # 清除分组信息
            # self.ui.tableWidget.setItem(i, 0, QtGui.QTableWidgetItem(''))
            # self.ui.tableWidget.setItem(i, 9, QtGui.QTableWidgetItem(''))
            wgt = self.ui.tableWidget.cellWidget(i, 17)
            if wgt.isChecked():
                checked_sel.append(i)
                sel_ipdata.append(self.ip_data[i])
            else:
                normal_ipdata.append(self.ip_data[i])
                color_bg = QtGui.QColor(255, 255, 255)
                IGROUP_ORG =  str(self.recode_groups[i][0])
                item = QtGui.QTableWidgetItem(IGROUP_ORG)
                item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
                item.setBackground(color_bg)
                self.ui.tableWidget.setItem(i, 0, item)
                wgroup_org = str(self.recode_groups[i][1])
                item = QtGui.QTableWidgetItem(wgroup_org)
                item.setBackground(color_bg)
                item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
                self.ui.tableWidget.setItem(i, 9, item)

        #对选择的阻抗进行分组排序
        # 取出最大的分组数
        if checked_sel:
            group_nums = list(set([d['IGROUP'] for d in self.ip_data]))
            max_group = 0
            for num in group_nums:
                groups = [d for d in self.ip_data if d['IGROUP'] == num]
                if len(groups) > max_group:
                    max_group = len(groups)
            mode_ip = list(set([d['IMODEL'] for d in self.ip_data]))   #INPLAN数据
            # sel_mode_ip = list(set([d['IMODEL'] for d in sel_ipdata])) #勾选数据
            # 1,如果原始inplan分组仅分一组则沿用原始分组,2.如果原始inplan分组中仅存在两分组并同时存在共面和非共面则直接沿用原始大分组
            if max_group == 1 or (max_group == 2 and (('特性' in mode_ip or '差动' in mode_ip) and ('特性共面' in mode_ip or '差动共面' in mode_ip))):
                send_ipdata = sel_ipdata
            else:
                # 选择的阻抗数据更新大分组从1开始排序
                sel_group_nums = sorted(list(set([d['IGROUP'] for d in sel_ipdata])))
                for d in sel_ipdata:
                    index_d = sel_group_nums.index(d['IGROUP']) + 1
                    d['IGROUP'] = index_d
                #计算能否合并大分组
                zk_gm_n = [d for d in sel_ipdata if d['IMODEL'] in ['特性', '差动']]
                zk_gm = [d for d in sel_ipdata if d['IMODEL'] in ['特性共面', '差动共面']]
                for data in [zk_gm, zk_gm_n]:
                    if data:
                        get_ip = self.tar_groups(data)
                        send_ipdata += get_ip

            # 更改分组为1,2,3的顺序
            group_nums = sorted(list(set([d['IGROUP'] for d in sel_ipdata])))
            for i, num in enumerate(group_nums):
                for j, d in enumerate(sel_ipdata):
                    if d['IGROUP'] == num:
                        sel_ipdata[j]['IGROUP'] = i + 1

            # sel_ipdata, v, k = self.deal_with_sqldata(sel_ipdata)
            self.sel_ip_data, self.sel_teamc, self.sel_coupon_num = self.deal_with_sqldata(sel_ipdata)
            self.mormal_ip_data, self.teamc, self.coupon_num = self.deal_with_sqldata(normal_ipdata)
            for i, index in enumerate(checked_sel):
                color_bg = QtGui.QColor(255, 165, 0)
                item = QtGui.QTableWidgetItem(str(sel_ipdata[i]['IGROUP']))
                item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
                item.setBackground(color_bg)
                self.ui.tableWidget.setItem(index, 0, item)
                wgroup = str(sel_ipdata[i]['WGROUP'][2])
                item = QtGui.QTableWidgetItem(wgroup)
                item.setBackground(color_bg)
                item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
                self.ui.tableWidget.setItem(index, 9, item)

    def tar_groups(self, ipdata):
        # 设定分组数最小的数为初始分组
        number_index = sorted(list(set([d['IGROUP'] for d in ipdata])))
        groups_first = [d for d in ipdata if d['IGROUP'] == number_index[0]]
        groups = {str(number_index[0]) : groups_first}
        # 循环后面的分组看能否满足和其它组合并的条件，有一组不满足则维持现状不合并
        for index in number_index[1:]:
            zw_tb = False
            # 现有目标占用层统计
            groups_index = [d for d in ipdata if d['IGROUP'] == index]
            layer_b = []
            for k in groups_index:
                zwb_layers = list(k['midlyrs'])
                if k['REF_TOP']:
                    zwb_layers.append(str(k['REF_TOP']).lower())
                if k['REF_BOT']:
                    zwb_layers.append(str(k['REF_BOT']).lower())
                layer_b += zwb_layers
            # 合并分组目标层统计
            for key, list_t in groups.items():
                layer_t = []
                for j in list_t:
                    zwt_layers = list(j['midlyrs'])
                    if j['REF_TOP']:
                        zwt_layers.append(str(j['REF_TOP']).lower())
                    if j['REF_BOT']:
                        zwt_layers.append(str(j['REF_BOT']).lower())
                    layer_t += zwt_layers
                # 合并中有超过4种相同元素的则不合并
                all_tb = layer_b + layer_t
                # GEN.PAUSE(str(all_tb))
                tb_set = list(set(all_tb))
                group_zip = True
                for tb in tb_set:
                    if all_tb.count(tb) > 3:
                        group_zip = False
                if not group_zip:
                    continue
                else:
                    # 可以合并则更改分组为目标index并加入到目标分组并跳出当次循环
                    for group in groups_index:
                        group['IGROUP'] = int(key)
                    groups[key] += groups_index
                    zw_tb = True
                    break
            if not zw_tb:
                groups.update({str(index) : groups_index})
        get_group_values = []
        for v in groups.values():
            get_group_values += v
        return get_group_values

    def addCheckBox(self, check_type):
        """
        在表格中加入checkBOX，必须先放入一个容器widget
        :param check:
        :return:
        """
        widget = QtGui.QWidget()
        checkbox = QtGui.QCheckBox()
        checkbox.setChecked(check_type)
        checkbox.setStyleSheet("QCheckBox::indicator { width: 18px; height: 18px; }" 
                               "QCheckBox:disabled { color: grey; }")
        widget.setChecked = checkbox.setChecked
        widget.checkState = checkbox.checkState
        widget.isChecked = checkbox.isChecked
        widget.clicked = checkbox.clicked
        h = QtGui.QHBoxLayout()
        h.addWidget(checkbox)
        h.setAlignment(QtCore.Qt.AlignHCenter)
        widget.setLayout(h)
        return widget

    def table_laylist_set(self):
        # 层别列表定义
        self.ui.tableWidget_LyrList.setAlternatingRowColors(True)
        # === 隐藏行标题
        self.ui.tableWidget_LyrList.verticalHeader().hide()
        # 显示共面差分列 7 --> 8
        self.ui.tableWidget_LyrList.setColumnCount(11)
        self.ui.tableWidget_LyrList.setRowCount(len(self.sig_layers))
        tableLyrRowWidth = [52, 38, 45, 85, 65, 85, 85, 85, 75,75,70]
        for rr in range(len(tableLyrRowWidth)):
            self.ui.tableWidget_LyrList.setColumnWidth(rr, tableLyrRowWidth[rr])

        for x in range(len(self.sig_layers)):
            if not self.stackupInfo.has_key(self.sig_layers[x]):
                msg_box = msgBox()
                msg_box.warning(self, '警告', '未获取到{0}层干膜信息，请反馈MI上传'.format(self.sig_layers[x]), QtGui.QMessageBox.Ok)
                sys.exit(0)
            # === layer_mode out|sec|sec1|inn
            layer_mode = self.stackupInfo[self.sig_layers[x]]['layerMode']
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
            item.setText(str(self.sig_layers[x]))
            item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
            # print 'x' * 40,self.sig_layers[x],'x' * 40
            for index in range(len(self.layerInfo)):
                layName = self.layerInfo[index]['LAYER_NAME'].lower()
                if layName == self.sig_layers[x]:
                    item = QtGui.QTableWidgetItem(str(self.layerInfo[index]['CAL_CU_THK']))
                    item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
                    self.ui.tableWidget_LyrList.setItem(x, 2, item)

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
                            self.ui.tableWidget_LyrList.item(x, 2).setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 0)))
                            showText = u"料号:%s层别:%s无法获取补偿信息，层别类型:%s基铜:%s完成铜厚:%s,使用完成铜厚0.6进行补偿!" % (
                                self.job_name, self.sig_layers[x], self.stackupInfo[self.sig_layers[x]]['layerMode'],
                                self.layerInfo[index]['CU_WEIGHT'], self.layerInfo[index]['CAL_CU_THK'])
                            msg_box = msgBox()
                            msg_box.warning(self, '警告', showText, QtGui.QMessageBox.Ok)
                        else:
                            showText = u"料号:%s层别:%s无法获取补偿信息，层别类型:%s基铜:%s完成铜厚:%s,程序退出!" % (
                                self.job_name, self.sig_layers[x], self.stackupInfo[self.sig_layers[x]]['layerMode'],
                                self.layerInfo[index]['CU_WEIGHT'], self.layerInfo[index]['CAL_CU_THK'])
                            msg_box = msgBox()
                            msg_box.critical(self, '警告', showText, QtGui.QMessageBox.Ok)
                            exit(1)
                    l2lspc = float(compData.l2lspcControl) * 1.0

                    # === TODO 外层次外层增加解析度的比对，inn类型Hoz增加成品线宽，成品线距的条件
                    w_line_width = self.layerInfo[index]['成品线宽']
                    w_line_space = self.layerInfo[index]['成品线距']
                    self.ui.tableWidget_LyrList.setItem(x, 9, QtGui.QTableWidgetItem(str(w_line_width)))
                    self.ui.tableWidget_LyrList.setItem(x, 10, QtGui.QTableWidgetItem(str(w_line_space)))
                    if layer_mode == 'inn':
                        if 0.01 < cu_thick < 0.53:
                            if w_line_width == 0 or w_line_space == 0:
                                showText = []
                                if w_line_width == 0:
                                    showText.append(u'铜厚HOZ未能获取层别：%s 成品线宽，按默认值控制，请确认！' % (layName))
                                if w_line_space == 0:
                                    showText.append(u'铜厚HOZ未能获取层别：%s 成品线距，按默认值控制，请确认！' % (layName))
                                if showText:
                                    msg_box = msgBox()
                                    msg_box.warning(self, '警告', '\n'.join(showText), QtGui.QMessageBox.Ok)
                            elif 1.8 >= float(w_line_width) > 1.5 and 1.8 >= float(w_line_space) > 1.5:
                                l2lspc = 1.4
                                compData.impBaseComp = 0.5
                            elif 2.0 >= float(w_line_width) > 1.8 and 2.0 >= float(w_line_space) > 1.8:
                                l2lspc = 1.6
                                compData.impBaseComp = 0.6
                            # 同一芯板取最小的一组线宽线距
                            # if self.stackupInfo[layName].has_key('film_bg') and self.stackupInfo[layName]['film_bg']:
                            #     for d in self.layerInfo:
                            #         if str(d['LAYER_NAME']).strip().upper() == str(self.stackupInfo[layName]['film_bg']).strip().upper():
                            #             w_line_width_bg = d['成品线宽']
                            #             w_line_space_bg = d['成品线距']
                            #             if float(w_line_width) == 0 or float(w_line_space) == 0:
                            #                 if float(w_line_width_bg) > 1.5 and float(w_line_space_bg) > 1.5:
                            #                     w_line_width = w_line_width_bg
                            #                     w_line_space = w_line_space_bg
                            #             else:
                            #                 if w_line_width_bg > 1.5 and w_line_space > 1.5:
                            #                     if float(w_line_width) > float(w_line_width_bg) and float(w_line_space) > float(w_line_space_bg):
                            #                         w_line_width = w_line_width_bg
                            #                         w_line_space = w_line_space_bg
                            # elif 2.0 >= float(w_line_width) and 2.0 >= float(w_line_space):
                            #     l2lspc = 1.6
                    compData.l2lspcControl = l2lspc * 1.0

                    df_type = self.stackupInfo[layName]['df_type']
                    if layer_mode == 'sec' or layer_mode == 'out':
                        get_gm_min_space = None
                        for gm_line in self.out_gm_rule:
                            if df_type == gm_line['gm_type']:
                                get_gm_min_space = float(gm_line['min_space'])
                        if get_gm_min_space:
                            l2lspc = max(compData.l2lspcControl, get_gm_min_space)
                        else:
                            showText = u'未能获取层别：%s干膜：%s的解析度，使用规范中最小间距，需确认！' % (layName, df_type)
                            msg_box = msgBox()
                            msg_box.warning(self, '警告', showText, QtGui.QMessageBox.Ok)
                    if layer_mode == 'sec1' or layer_mode == 'inn':
                        get_gm_min_space = None
                        for gm_line in self.inn_gm_rule:
                            if df_type == gm_line['gm_type']:
                                get_gm_min_space = float(gm_line['min_space'])

                        if get_gm_min_space:
                            l2lspc = max(compData.l2lspcControl, get_gm_min_space)
                        else:
                            showText = u'未能获取层别：%s干膜：%s的解析度，使用规范中最小间距，需确认！' % (layName, df_type)
                            msg_box = msgBox()
                            msg_box.warning(self, '警告', showText, QtGui.QMessageBox.Ok)

                    # ======================================

                    self.layerInfo[index]['compData'] = compData
                    self.ui.tableWidget_LyrList.setItem(x, 3, QtGui.QTableWidgetItem('%s' % compData.impBaseComp))
                    self.ui.tableWidget_LyrList.setItem(x, 4, QtGui.QTableWidgetItem('%s' % compData.SingleComp))
                    self.ui.tableWidget_LyrList.setItem(x, 5, QtGui.QTableWidgetItem('%s' % compData.DiffComp))
                    self.ui.tableWidget_LyrList.setItem(x, 6, QtGui.QTableWidgetItem('%s' % compData.CopSingleComp))
                    self.ui.tableWidget_LyrList.setItem(x, 7, QtGui.QTableWidgetItem('%s' % compData.CopDiffComp))
                    self.ui.tableWidget_LyrList.setItem(x, 8, QtGui.QTableWidgetItem('%s' % l2lspc))
                    if layer_mode == 'inn' and  0.01 < cu_thick < 0.53:
                        if w_line_width == 0 or w_line_space == 0:
                            brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
                            brush.setStyle(QtCore.Qt.NoBrush)
                            self.ui.tableWidget_LyrList.item(x, 8).setForeground(brush)
                            self.ui.tableWidget_LyrList.item(x, 8).setToolTip(u"未获取到原稿线宽或线距，按默认最高区间控制")
            # print json.dumps (layerInfo, sort_keys=True, indent=2, separators=(',', ': '))
            item = QtGui.QTableWidgetItem('%s' % layer_mode)
            item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
            self.ui.tableWidget_LyrList.setItem(x, 1, item)

    def change_table_laylist(self):
        msg_box = msgBox()
        get_result = msg_box.question(self, '层别类型更改确认', '执行此按钮，会更改sec类型为sec1类型，是否继续?', QtGui.QMessageBox.Yes,QtGui.QMessageBox.No)
        if get_result == 1:
            return
        for a_layer in self.stackupInfo:
            if self.stackupInfo[a_layer]['layerMode'] == 'sec':
                self.stackupInfo[a_layer]['layerMode'] = 'sec1'
        # self.ui.tableWidget_LyrList.clear()
        # === 不直接使用self.ui.tableWidget.clear() 方法，用于保留标题行
        for row in range(self.ui.tableWidget_LyrList.rowCount()):
            self.ui.tableWidget_LyrList.removeRow(0)
        self.table_laylist_set()
        for row in range(self.ui.tableWidget.rowCount()):
            self.ui.tableWidget.removeRow(0)
        self.imp_table_set()

    def table_item_set(self, row, colum, bg='', fg='', tool_tip=None, text=None):
        """
        设定table单元格，文本，颜色，小提示
        :param row: 行index
        :param colum: 列index
        :param bg: 背景色
        :param fg: 文字色
        :param tool_tip: 单元格提示
        :param text: 单元格文本
        :return:
        """
        if text:
            if type(text) == int or type(text) == float:
                item = QtGui.QTableWidgetItem(str(text))
                item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
                self.ui.tableWidget.setItem(row, colum, item)
            else:
                item = QtGui.QTableWidgetItem(_fromUtf8(text))
                item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
                self.ui.tableWidget.setItem(row, colum, item)
                # self.ui.tableWidget.setItem(row, colum, QtGui.QTableWidgetItem(_fromUtf8(text)))

        
        if bg == 'green':
            self.ui.tableWidget.item(row, colum).setBackground(QtGui.QBrush(QtGui.QColor('green')))
        elif bg == 'red':
            self.ui.tableWidget.item(row, colum).setBackground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
        elif bg == 'yellow':
            self.ui.tableWidget.item(row, colum).setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 0)))

        if fg == 'white':
            self.ui.tableWidget.item(row, colum).setForeground(QtGui.QBrush(QtGui.QColor('white')))

        if tool_tip:
            self.ui.tableWidget.item(row, colum).setToolTip(
                _translate("MainWindow",
                           "<html><head/><body><p>%s</p></body></html>" % tool_tip, None))
        return


    def cellChange(self):
        # --先断开信号的连接,以免在下面再次修改item时发生递归死循环事件发生
        QtCore.QObject.disconnect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"),
                                  self.cellChange)
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
        selText = str(items[0].text())
        selRow = items[0].row()
        selCol = items[0].column()
        item_text = self.ui.tableWidget_LyrList.item(selRow, selCol).text()

        # --获取选择行的完成铜厚信息
        try:
            finishComp = float(item_text)
            # print finishComp
            if finishComp < 0:
                showText = u"'第%d行%d列' 补偿值 '%s' 不是正数，请修改!" % (selRow + 1, selCol + 1, item_text)
                msg_box = msgBox()
                msg_box.warning(self, '警告', showText, QtGui.QMessageBox.Ok)
                self.ui.tableWidget_LyrList.item(selRow, selCol).setForeground(
                    QtGui.QBrush(QtGui.QColor(255, 0, 0)))

                QtCore.QObject.connect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"),
                                       self.cellChange)
                return False

            selLayer = self.ui.tableWidget_LyrList.item(selRow, 0).text()
            self.ui.tableWidget_LyrList.item(selRow, selCol).setForeground(QtGui.QBrush(QtGui.QColor('blue')))
            self.refreshTableWidget(selLayer, selRow, selCol, finishComp)
        except ValueError:
            self.ui.tableWidget_LyrList.item(selRow, selCol).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
            showText = u"第%d行%d列 补偿值 %s 不是有效数字，请修改!" % (selRow + 1, selCol + 1, item_text)
            msg_box = msgBox()
            msg_box.warning(self, '警告', showText, QtGui.QMessageBox.Ok)
            # --退出前，再次启动信号连接
            # self.ui.connect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"), self.cellChange)
            QtCore.QObject.connect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"),
                                   self.cellChange)
            return False

            # --重新更新UI数据
        # --退出前，再次启动信号连接
        QtCore.QObject.connect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"), self.cellChange)

    def refreshTableWidget(self, changeLayer, changeRow, changeCol, changeValue):
        #  changeCol = 3,所有补偿 4,特性 5, 差分 6，共面特性 7，共面差分
        if changeCol == 3:
            self.layerInfo[changeRow]['compData'].impBaseComp = changeValue
        elif changeCol == 4:
            self.layerInfo[changeRow]['compData'].SingleComp = changeValue
        elif changeCol == 5:
            self.layerInfo[changeRow]['compData'].DiffComp = changeValue
        elif changeCol == 6:
            self.layerInfo[changeRow]['compData'].CopSingleComp = changeValue
        elif changeCol == 7:
            self.layerInfo[changeRow]['compData'].CopDiffComp = changeValue
        elif changeCol == 8:
            self.layerInfo[changeRow]['compData'].l2lspcControl = changeValue
        # elif changeCol == 6:
        #     layerInfo[changeRow]['compData'].DiffComp = changeValue

        for x in range(len(self.ip_data)):
            trace_layer = self.ui.tableWidget.item(x, 1).text()
            if trace_layer == changeLayer:
                # === 根据更改重新计算补偿值 ===
                self.imp_comp(x, str(trace_layer), changeRow)
                # 获取值，如果有变动则更改颜色
                current_12 = self.ui.tableWidget.item(x, 12).text()
                current_13_yn = self.ui.tableWidget.item(x, 13)
                if current_13_yn:
                    current_13 = self.ui.tableWidget.item(x, 13).text()
                current_14_yn = self.ui.tableWidget.item(x, 14)
                if current_14_yn:
                    current_14 = self.ui.tableWidget.item(x, 14).text()
                # self.ui.tableWidget.setItem (x, 12, QtGui.QTableWidgetItem (str (self.ip_data[x]['workLineWid'])))
                # === 2020.06.04 Song 更改写法，直接更新单元格的文本，用来保留字体颜色 ===
                self.ui.tableWidget.item(x, 12).setText(str(self.ip_data[x]['workLineWid']))
                if str(current_12) != str(self.ip_data[x]['workLineWid']):
                    self.ui.tableWidget.item(x, 12).setForeground(QtGui.QBrush(QtGui.QColor('blue')))
                # self.ui.tableWidget.setItem (x, 13, QtGui.QTableWidgetItem (str (self.ip_data[x]['workLineSpc'])))
                if current_13_yn:
                    self.ui.tableWidget.item(x, 13).setText(str(self.ip_data[x]['workLineSpc']))
                    if str(current_13) != str(self.ip_data[x]['workLineSpc']):
                        self.ui.tableWidget.item(x, 13).setForeground(QtGui.QBrush(QtGui.QColor('blue')))
                        if self.ip_data[x]['workLineSpc'] < self.layerInfo[changeRow]['compData'].l2lspcControl and \
                                self.ip_data[x]['workLineSpc'] != 0:
                            self.ui.tableWidget.item(x, 13).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                # self.ui.tableWidget.setItem (x, 14, QtGui.QTableWidgetItem (str (self.ip_data[x]['workSpc2Cu'])))
                if current_14_yn:
                    self.ui.tableWidget.item(x, 14).setText(str(self.ip_data[x]['workSpc2Cu']))
                    if str(current_14) != str(self.ip_data[x]['workSpc2Cu']):
                        self.ui.tableWidget.item(x, 14).setForeground(QtGui.QBrush(QtGui.QColor('blue')))
                        if self.ip_data[x]['workSpc2Cu'] < self.l2cspcControl and self.ip_data[x]['workSpc2Cu'] != 0:
                            self.ui.tableWidget.item(x, 14).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))

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
            msg_box = msgBox()
            msg_box.warning(self, '警告', showText, QtGui.QMessageBox.Ok)

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

    def dynamic_etch(self, line_width, line_space, line2cu_space, line_base_comp, line_comp):
        """
        根据线宽线距线到铜模拟动态补偿，卡self.etch_space间距进行补偿，不满足间距则不补
        未使用，最新使用为dynamic_etch_space_enough
        :param line_width:
        :param line_space:
        :param line2cu_space:
        :param line_comp:动态补偿值
        :param line_base_comp:正常补偿值
        :return:end_line_width,end_line_space,end_line2cu_space
        """
        line_comp1 = 0
        line_comp2 = 0

        line_first = line_space - line_base_comp
        if line_first <= self.etch_space:
            line_comp1 = 0
        elif self.etch_space < line_first < self.etch_space + line_comp:
            line_comp1 = (line_first - self.etch_space) * 0.5
        elif line_first >= self.etch_space + line_comp:
            line_comp1 = 0.5 * line_comp
        space_first = line2cu_space - line_base_comp
        if space_first <= self.etch_space:
            line_comp2 = 0
        elif self.etch_space < space_first < self.etch_space + line_comp * 0.5:
            line_comp2 = space_first - self.etch_space
        elif space_first >= self.etch_space + line_comp * 0.5:
            line_comp2 = 0.5 * line_comp
        if line2cu_space == 0:
            line_comp2 = 0.5 * line_comp

        end_line_width = line_width + line_base_comp + line_comp1 + line_comp2
        end_line_space = line_first - line_comp1 * 2
        end_line2cu_space = space_first - line_comp2

        if line2cu_space == 0:
            end_line2cu_space = 0
        if line_space == 0:
            end_line_width = line_width + line_base_comp + line_comp2 * 2

        return end_line_width, end_line_space, end_line2cu_space

    def dynamic_etch_new(self, line_width, line_space, line2cu_space, line_base_comp, line_comp, layer_spc_control):
        """
        2021.03.08 新算法，根据线宽线距线到铜模拟动态补偿，采用侧补方式，无论如何卡最小间距且补偿足够
        暂未使用
        :param line_width:
        :param line_space:
        :param line2cu_space:
        :param line_comp:动态补偿值
        :param line_base_comp:正常补偿值
        :param layer_spc_control 间距管控值
        :return:end_line_width,end_line_space,end_line2cu_space
        """
        end_line_width = 0
        end_line_space = 0
        end_line2cu_space = 0
        end_line_width = line_width + line_base_comp + line_comp
        # comp_i = 0
        # comp_o = 0
        end_line_space = line_space - (line_base_comp + line_comp)
        if end_line_space >= layer_spc_control:
            comp_i = (line_base_comp + line_comp) * 0.5
            comp_o = (line_base_comp + line_comp) - comp_i
            line2cu_space_cal = line2cu_space - line_base_comp * 0.5 - comp_o
            if line2cu_space_cal < layer_spc_control:
                # === 铜距不满足最小间距时，拉至最小间距，此时如线距还有剩余，可线距内层多补 ===
                end_line2cu_space = layer_spc_control
                # === 线距为原本计算出的线距，再减去铜距侧补多补值，两根线减双边 ===
                end_line_space = end_line_space - (end_line2cu_space - line2cu_space_cal) * 2
                # === 再次计算出的线距若小于最小间距，拉至最小间距 ===
                if end_line_space < layer_spc_control:
                    end_line_space = layer_spc_control
            else:
                end_line2cu_space = line2cu_space_cal
        elif end_line_space < layer_spc_control:
            end_line_space = layer_spc_control
            comp_i = (line_space - end_line_space) * 0.5
            comp_o = (line_base_comp + line_comp) - comp_i
            line2cu_space_cal = line2cu_space - line_base_comp * 0.5 - comp_o
            if line2cu_space_cal < layer_spc_control:
                end_line2cu_space = layer_spc_control
            else:
                end_line2cu_space = line2cu_space_cal

        if line2cu_space == 0:
            end_line2cu_space = 0
            end_line_space = line_space - (line_base_comp + line_comp)
            if end_line_space < layer_spc_control:
                end_line_space = layer_spc_control

        if line_space == 0:
            end_line_width = line_width + line_base_comp + line_comp
            if line2cu_space != 0:
                end_line2cu_space = line2cu_space - line_base_comp - line_comp * 0.5
                if end_line2cu_space < layer_spc_control:
                    end_line2cu_space = layer_spc_control

        return end_line_width, end_line_space, end_line2cu_space

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

    def changeShowX(self):
        self.changeShow2('X')

    def changeShowY(self):
        self.changeShow2('Y')

    def changeShow2(self, changeDirect):

        xNum = str(self.ui.comboBox_xDirec.currentText())
        yNum = str(self.ui.comboBox_yDirec.currentText())
        # TODO 更改判断2020.01.02
        if changeDirect == "X":
            if int(self.coupon_num) % int(xNum) != 0:
                yNum = int(self.coupon_num) / int(xNum) + 1
            else:
                yNum = int(self.coupon_num) / int(xNum)
        elif changeDirect == "Y":
            if int(self.coupon_num) % int(yNum) != 0:
                xNum = int(self.coupon_num) / int(yNum) + 1
            else:
                xNum = int(self.coupon_num) / int(yNum)
        # print str(xNum) + " " + str(yNum)
        tmp_x = int(xNum) - 1
        tmp_y = int(yNum) - 1
        self.ui.comboBox_xDirec.setCurrentIndex(int(tmp_x))
        self.ui.comboBox_yDirec.setCurrentIndex(int(tmp_y))

    def chglineceshiMil(self):
        showTextMil = float(self.ui.lineEdit_ceshiMil.text())
        showTextMM = showTextMil / 39.37
        self.ui.lineEdit_ceshiMM.setText('%.3f' % (showTextMM))

    def chglineceshiMM(self):
        showTextMM = float(self.ui.lineEdit_ceshiMM.text())
        showTextMil = showTextMM * 39.37
        self.ui.lineEdit_ceshiMil.setText('%.3f' % (showTextMil))

    def chglinedingweiMil(self):
        showTextMil = float(self.ui.lineEdit_dingweiMil.text())
        showTextMM = showTextMil / 39.37
        self.ui.lineEdit_dingweiMM.setText('%.3f' % (showTextMM))

    def chglinedingweiMM(self):
        showTextMM = float(self.ui.lineEdit_dingweiMM.text())
        showTextMil = showTextMM * 39.37
        self.ui.lineEdit_dingweiMil.setText('%.3f' % (showTextMil))

    def stringtonum(self, instr):
        """
        转换字符串为数字优先转换为整数，不成功则转换为浮点数
        :param instr:
        :return:
        """
        try:
            num = string.atoi(instr)
            return num
        except (ValueError, TypeError):
            try:
                num = string.atof(instr)
                # 增加判断，当字符串取整与浮点数相同时，则取整 90.0->90 90.5->90.5
                if int(num) == num:
                    return int(num)
                else:
                    return num
            except ValueError:
                opstr = str(instr)
                return opstr

    def get_Window_imp(self):
        # 获取Table数据，存入字典中
        getDict = {'normal': [], 'dy': []}
        for y in range(len(self.ip_data)):
            # 添加str字符串类型可以转换Qstring为 String
            # key_num = y+1
            showline = {}
            showline['id'] = y + 1
            column_keys = ['igroup', 'worklay', 'showwid', 'showlspc', 'showspc2cu', 'reftop', 'refbot', 'orwid',
                           'imodel',
                           'wgroup', 'solderopen', 'ohm', 'workwidth', 'worklspc', 'workspc2cu', 'gindex', 'miindex']
            # === 界面数据收集  ====
            for i, c_key in enumerate(column_keys):
                try:
                    get_text = self.stringtonum(self.ui.tableWidget.item(y, i).text().toUtf8())
                except AttributeError:
                    if not self.ui.tableWidget.item(y, i):
                        if c_key in ['showwid', 'showlspc', 'showspc2cu', 'orwid', 'ohm', 'workwidth', 'worklspc',
                                     'workspc2cu', 'gindex', 'miindex']:
                            get_text = 0
                        else:
                            get_text = ''
                    else:
                        get_text = self.stringtonum(self.ui.tableWidget.item(y, i).text())

                # print i, c_key, get_text
                showline[c_key] = get_text

            if self.b20job == 'yes':
                # 直接填入分组信息
                # showline['arrayimp'] = str(self.ui.tableWidget.item(y,16).checkState())
                # === 存储array 分组信息
                showline['arrayimp'] = self.stringtonum(str(self.b20checlist[y].text()))

            showline['midlyrs'] = []
            if self.stackupInfo[showline['worklay']]['layerSide'] == 'top':
                showline['textmir'] = 'no'
            elif self.stackupInfo[showline['worklay']]['layerSide'] == 'bot':
                showline['textmir'] = 'yes'
            # 定义中间层
            if showline['reftop'] == '' and showline['refbot'] == '':
                showline['midlyrs'] = [i for i in self.sig_layers]
                showline['refmark'] = ''

            elif showline['reftop'] != '' and showline['refbot'] != '':
                showline['refmark'] = showline['reftop'].upper() + '&' + showline['refbot'].upper()

                if int(showline['refbot'][1:]) - int(showline['reftop'][1:]) > 1:
                    for i in range(int(showline['reftop'][1:]) + 1, int(showline['refbot'][1:])):
                        showline['midlyrs'].append("l%s" % i)
                elif int(showline['refbot'][1:]) - int(showline['reftop'][1:]) < -1:
                    for i in range(int(showline['refbot'][1:]) + 1, int(showline['reftop'][1:])):
                        showline['midlyrs'].append("l%s" % i)
            else:
                # 单层参考层的情况
                if showline['refbot'] != '':
                    showline['refmark'] = showline['refbot'].upper()
                    # 单层参考为非top、bot层别时，增加其他层别为中间层
                    if int(showline['worklay'][1:]) != 1:
                        for i in range(1, int(showline['worklay'][1:])):
                            showline['midlyrs'].append("l%s" % i)
                    if int(showline['refbot'][1:]) - int(showline['worklay'][1:]) >= 2:
                        for i in range(int(showline['worklay'][1:]) + 1, int(showline['refbot'][1:])):
                            showline['midlyrs'].append("l%s" % i)
                elif showline['reftop'] != '':
                    showline['refmark'] = showline['reftop'].upper()
                    if int(showline['worklay'][1:]) != int(self.job_layer_num):
                        # modified by song 需包含底层
                        for i in range(int(showline['worklay'][1:]), int(self.job_layer_num) + 1):
                            showline['midlyrs'].append("l%s" % i)
                    if int(showline['worklay'][1:]) - int(showline['reftop'][1:]) >= 2:
                        for i in range(int(showline['reftop'][1:]) + 1, int(showline['worklay'][1:])):
                            showline['midlyrs'].append("l%s" % i)
                else:
                    return False

            # 定义中间层结束
            if run_dr_type:
                if self.ui.tableWidget.cellWidget(y, 17).isChecked():
                    getDict['dy'].append(showline)
                else:
                    getDict['normal'].append(showline)
            else:
                getDict['normal'].append(showline)
            # print json.dumps (getDict[y], sort_keys=True, indent=2, separators=(',', ': '))
        # print json.dumps (getDict, sort_keys=True, indent=2, separators=(',', ': '))
        return getDict

    def getWindowInfo(self):
        # 阻抗测点大小
        # 测点孔径
        self.hole_wid = float(str(self.ui.lineEdit_ceshiMil.text()))
        # 定位孔大小
        self.dingwei_wid = float(str(self.ui.lineEdit_dingweiMil.text()))
        # 定义阻抗线长度
        self.imp_coupon_line_length = float(str(self.ui.lineEdit_cou_line_length.text()))
        # 定义阻抗加长长度
        self.extra_strech_coupon_length = float(str(self.ui.lineEdit_extra_strech_coupon_length.text()))        
        
        if self.ui.checkBox_innerpad.isChecked():
            self.inner_test_add = True
        else:
            self.inner_test_add = False

        if self.ui.laser_inner_hole.isChecked():
            self.laser_test_add = True
        else:
            self.laser_test_add = False
            
    def get_imp_all_length(self, imp_data, cam_data):
        """
        imp_data 阻抗线信息
        cam_data 拼版信息
        """
        # 分组匹配 ,计算出每组阻抗条中含有几组差分或特性阻抗
        imp_index_leng = {}
        for k, v in cam_data.items():
            imp_index_leng[k] = v['icgLength']
        groups = {}
        for dict in imp_data:
            if dict['igroup'] not in groups.keys():
                groups[dict['igroup']] = [dict['imodel']]
            else:
                groups[dict['igroup']] += [dict['imodel']]
        min_imp_dict = {}
        for key,val in groups.items():
            imp_s = [moder for moder in val if '特性' in moder]
            imp_d = [moder for moder in val if '差动' in moder]
            # 计算出每一组需要添加孔所占长度，差动是特性两倍
            drl_groups = len(imp_s) + len(imp_d)  + len(imp_d)
            leng_drl_groups = 0.1 * (drl_groups - 1)
            cam_icg_leng = imp_index_leng[key] / 1000
            min_imp_leng = cam_icg_leng - 0.65 - leng_drl_groups - 0.14
            min_imp_dict[key] = min_imp_leng
        min_leng_imp = min(min_imp_dict.values()) + self.extra_strech_coupon_length
        get_resize_leng = round(150/25.4 - min(min_imp_dict.values()), 2)
        if min_leng_imp < 150/25.4:
            showText = u'B27客户阻抗线长度最少需要150mm!\n' +\
                       u'请将阻抗线加长{0} inch以上!'.format(get_resize_leng)
            msg_box = msgBox()
            msg_box.information(self, '提示', showText, QtGui.QMessageBox.Ok)
            self.ui.lineEdit_extra_strech_coupon_length.setStyleSheet("color: rgb(255, 0, 0);")
            self.ui.lineEdit_extra_strech_coupon_length.setFocus()
            return False
        else:
            return True

    def MAIN_RUN(self):
        GEN.COM('disp_off')
        GEN.COM('origin_off')
        get_imp_data = self.get_Window_imp()
        # 对界面获得的数据进行逆向排序，使得仅有一组时为中间走线。
        # 如果是运行的勾选模式，传入的是一个字典，常规模式是一个列表包含所有数据
        x_n = get_imp_data['normal']
        x_dy = get_imp_data['dy']
        getwarns = []
        for group_x in [x_n,x_dy]:
            if not group_x:
                continue
            rever_imp_data = sorted(group_x, key=lambda x: x['id'], reverse=True)
            if group_x == x_dy:
                mode_run = 'dy'
                zu_areas = {}
                zu_imp = sorted(list(set([i['igroup'] for i in rever_imp_data])))
                # 找出self.coupon_area中最大分组数
                max_imp = max([len(val['numlist']) for key, val in self.coupon_area.items()])
                # if len(zu_imp) < max_imp:
                zu_areas_leng = len(zu_imp) / max_imp
                if len(zu_imp) % max_imp:
                    zu_areas_leng += 1

                # 去除允许分组的最大值
                max_area_data = None
                for key, val in self.coupon_area.items():
                    if len(val['numlist']) == max_imp:
                        max_area_data = val
                        del max_area_data['numlist']

                if max_area_data:
                    for zu_idex in range(zu_areas_leng):
                        area_data = copy.deepcopy(max_area_data)
                        numlist_zu = [ii + max_imp * zu_idex for ii in range(1, max_imp + 1)]
                        area_data['numlist'] = numlist_zu
                        # set_numlist = list(set(area_zu) & set(zu_imp))
                        zu_areas[zu_idex + 1] = area_data

                send_coupon_area = zu_areas
                send_coupon_num = self.sel_coupon_num
                send_teamc = self.sel_teamc

            else:
                mode_run = 'normal'
                #如果有分组低压，则重新获取分组值
                send_coupon_area = self.coupon_area
                send_coupon_num = self.coupon_num
                send_teamc = self.teamc

            if get_imp_data.has_key('dy'):
                # 选择了低压阻抗则需要进一步重组数据
                for k1, v1 in send_coupon_area.items():
                    set_numlist = list(set(v1['numlist']) & set(send_teamc.keys()))
                    if not set_numlist:
                        del send_coupon_area[k1]
                        continue
                    diff_number = len(v1['numlist']) - len(set_numlist)
                    if diff_number:
                        send_coupon_area[k1]['numlist'] = set_numlist
                        h_num = v1['h_num']
                        v_num = v1['v_num']
                        # 任意一边能整除则缩减能整除的一边，否则缩减至一边为1后则需要计算另外一边的缩减值
                        if diff_number % h_num == 0:
                            if h_num > 1:
                                send_coupon_area[k1]['h_num'] = h_num - diff_number / h_num
                                if send_coupon_area[k1]['ang_list'][0] == 90 or send_coupon_area[k1]['ang_list'][0] == 180:
                                    send_coupon_area[k1]['ycorlist'] = send_coupon_area[k1]['ycorlist'][:-(diff_number / h_num)]
                                else:
                                    send_coupon_area[k1]['xcorlist'] = send_coupon_area[k1]['xcorlist'][:-(diff_number / h_num)]
                            elif h_num == 1:
                                send_coupon_area[k1]['v_num'] = v_num - diff_number / h_num
                                if send_coupon_area[k1]['ang_list'][0] == 90 or send_coupon_area[k1]['ang_list'][0] == 180:
                                    send_coupon_area[k1]['xcorlist'] = send_coupon_area[k1]['xcorlist'][:-diff_number]
                                else:
                                    send_coupon_area[k1]['ycorlist'] = send_coupon_area[k1]['ycorlist'][:-diff_number]

                        elif diff_number % v_num == 0:
                            if v_num > 1:
                                send_coupon_area[k1]['v_num'] = v_num - diff_number / v_num
                                if send_coupon_area[k1]['ang_list'][0] == 90 or send_coupon_area[k1]['ang_list'][0] == 180:
                                    send_coupon_area[k1]['xcorlist'] = send_coupon_area[k1]['xcorlist'][:-(diff_number / v_num)]
                                else:
                                    send_coupon_area[k1]['ycorlist'] = send_coupon_area[k1]['ycorlist'][:-(diff_number / v_num)]
                            elif v_num == 1:
                                send_coupon_area[k1]['h_num'] = h_num - diff_number / v_num
                                if send_coupon_area[k1]['ang_list'][0] == 90 or send_coupon_area[k1]['ang_list'][0] == 180:
                                    send_coupon_area[k1]['ycorlist'] = send_coupon_area[k1]['ycorlist'][:-diff_number]
                                else:
                                    send_coupon_area[k1]['xcorlist'] = send_coupon_area[k1]['xcorlist'][:-diff_number]
                        else:
                            # 两边都不能整除，因为目前仅a86和d10需要运行低压阻抗，且固定一边只有1，暂不存在，暂不考虑
                            pass


            # rever_imp_data = sorted (x, key=lambda x: int (x['ID']), reverse=True)
            self.getWindowInfo()
            # 运行前先预算处阻抗线长度，对低于不符合要求值的提示更改后运行 b27 客户最短需要150mm
            if self.job_name[1:4] == 'b27':
                if self.get_imp_all_length(rever_imp_data, self.icgCamData):
                    pass
                else:
                    return
            # 如果差分种类为bot的提示MI更改分组
            show_erros = []
            for d in rever_imp_data:
                if d['imodel'] in [u'差动', u'差动共面', u'特性', u'特性共面'] and d['wgroup'] > 3:
                    showText = u'第{0}组阻抗 {1}-{2}  OHM无位置添加，请让MI更改大分组'.format(d['id'], d['worklay'], d['ohm'])
                    show_erros.append(showText)
            if show_erros:
                msg_box = msgBox()
                msg_box.warning(self, '提示', ';'.join(show_erros), QtGui.QMessageBox.Ok)
            else:
                self.close()
                pass_list = [self.hole_wid, self.dingwei_wid, self.cedian_spc_x, self.cedian_spc_y, self.min_p2line,
                             self.job_layer_num, self.inner_test_add, self.imp_coupon_line_length,
                             self.extra_strech_coupon_length, self.laser_test_add]
                #if "-lyh" in self.job_name and group_x == x_dy:
                    #print(send_teamc)
                    #print(send_coupon_area)
                    #print(send_coupon_num)
                    #GEN.PAUSE("ddd")
                    
                CouponRun = ImpRun(rever_imp_data, self.icgCamData, send_teamc, send_coupon_area, send_coupon_num,
                                   self.sig_layers, pass_list, self.tool_size_rule, mode=mode_run)

                getwarn = CouponRun.icgCouponRun()

                # all_imp_data = self.deal_with_sqldata (get_imp_data)
                if self.b20job == 'yes':
                    b20Run = b20Imp.MyApp(self.job_name, rever_imp_data)
                    getwarn2 = b20Run.runB20Coupon(rever_imp_data)
                    if getwarn2 == 'retry':
                        self.show()
                        return
                    if getwarn2 is not None:
                        if getwarn is None:
                            getwarn = getwarn2
                        else:
                            getwarn += getwarn2
                if getwarn:
                    getwarns.append(getwarn)

                GEN.COM('disp_on')
                GEN.COM('origin_on')

        if getwarns is not None:
            show_getwarn = '\n'.join(getwarns)
            self.tran_run_result_to_topcam(show_getwarn)
            # showText = u'%s 程序已运行完成，请检查.' % show_getwarn
            # msg_box = msgBox()
            # msg_box.warning(self, '警告', showText, QtGui.QMessageBox.Ok)

        else:
            showText = u'程序运行完成，请检查.'
            msg_box = msgBox()
            msg_box.critical(self, '提示', showText, QtGui.QMessageBox.Ok)



    def tran_run_result_to_topcam(self, warn_text):
        exit_num = 0
        msgInfo = u'<table border="1"><tr><th>类型</th><th>内容</th></tr>'
        warn_list = warn_text.split('|')
        for warn_line in warn_list:
            if '检查项' in warn_line:
                msgInfo += u'<tr><td bgcolor=%s><font color="#FFFFFF">%s</td><td>%s</td></tr>' % (
                    'orange', u'检查', warn_line)
                # exit_num = 1
            elif '检测到' in warn_line or '未运行B20阻抗条' in warn_line:
                msgInfo += u'<tr><td bgcolor=%s><font color="#FFFFFF">%s</td><td>%s</td></tr>' % (
                    'red', u'警告', warn_line)
                exit_num = 1
            else:
                msgInfo += u'<tr><td bgcolor=%s><font color="#FFFFFF">%s</td><td>%s</td></tr>' % (
                    'green', u'提示', warn_line)

        date_time = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
        msgInfo += u'</table><br><br>%s 以上警告信息，请注意检查！！！' % date_time
        msg_box = msgBox()
        msg_box.warning(self, '警告', msgInfo, QtGui.QMessageBox.Ok)
        import TOPCAM_IKM
        param_exist = os.environ.get('PARAM')
        if param_exist:
            paramJson = json.loads(param_exist.replace(';', ','))
            processID = int(paramJson['process_id'])
            jobID = int(paramJson['job_id'])
            IKM = TOPCAM_IKM.IKM()
            IKM.update_flow_report(processID, jobid=jobID, report=msgInfo)

class ImpRun:
    """
    跑出阻抗条，主程序
    """

    def __init__(self, rever_imp_data, icgCamData, teamc, coupon_area, coupon_num, sig_layers, ui_info_list,tool_size_rule, mode):
        self.mode = mode
        self.rever_imp_data = rever_imp_data
        self.icgCamData = icgCamData
        self.teamc = teamc
        self.coupon_area = coupon_area
        self.coupon_num = coupon_num
        self.sig_layers = sig_layers
        self.job_name = os.environ.get('JOB', None)
        
        (self.hole_wid, self.dingwei_wid,
         self.cedian_spc_x, self.cedian_spc_y,
         self.min_p2line, self.job_layer_num,
         self.inner_test_add, self.imp_coupon_line_length,
         self.extra_strech_coupon_length, self.laser_test_add) = ui_info_list
        
        self.tool_size_rule = tool_size_rule

        self.set_exists = GEN.STEP_EXISTS(job=self.job_name,step='set')
        if self.set_exists == 'yes':
            self.set_step = 'set'
        else:
            self.set_step = 'edit'
        self.add_other_hole = False

        if self.inner_test_add:
            self.drl_info = self.getdrillLayers()
            # print self.drl_info
            self.inner_burry_layer, self.inner_pad_layer = self.get_min_through_burry()
            if not self.inner_burry_layer:
                # showText = u'勾选了内层加Pad，但是未匹配到对应的埋孔钻带，按不添加制作.'
                # msg_box = msgBox()
                # msg_box.critical(self, '不添加埋孔测试pad', showText, QtGui.QMessageBox.Ok)
                self.inner_test_add = False

        # 挡点大小
        self.md_wid = self.hole_wid + 4
        # 测点pad
        self.cedian_wid = self.hole_wid + 12
        # 测点套铜
        self.neg_wid = self.cedian_wid + 12
        # 防焊pad
        self.sm_pad = self.cedian_wid + 6

        # 差分阻抗线圆弧值
        self.arc_d = 10

    def get_min_through_burry(self):
        burry_list = [k for k in self.drl_info['drl_layer'] if re.match('b[0-9]', k)]
        print burry_list
        burry_reg = re.compile('b([0-9][0-9]?)-([0-9][0-9]?)')
        inn_burry = None
        min_through_num = 999
        burry_out_layer = []
        for bu in burry_list:
            m = burry_reg.match(bu)
            if m:
                start = int(m.group(1))
                end = int(m.group(2))
                through_layer_num = end - start
                if through_layer_num == 1:
                    pass
                else:
                    if through_layer_num == min_through_num:
                        showText = u'存在两个相同贯穿层数量的埋孔钻带，会对内层加钻孔有影响.'
                        msg_box = msgBox()
                        msg_box.critical(self, '程序暂不支持提醒', showText, QtGui.QMessageBox.Ok)
                    else:
                        min_through_num = min(min_through_num, through_layer_num)
                        if through_layer_num == min_through_num:
                            inn_burry = bu
                            burry_out_layer = ['l%s' % start,'l%s' % end]

        if len(self.drl_info['drl_layer']) > 1:
            self.add_other_hole = True          
            burry_drl_list = [float(self.drl_info['min_list'][i]) for i, k in enumerate(self.drl_info['drl_layer']) if re.match('b[0-9]', k)]                
            if len(burry_drl_list) == 0:
                self.max_burry_size = 0
            else:
                self.max_burry_size = max(burry_drl_list)/25.4
            print burry_drl_list
        print 'min_through_num',min_through_num
        print 'inn_burry',inn_burry
        return inn_burry,burry_out_layer

    def icgCouponRun(self):
        rever_imp_data = self.rever_imp_data
        warn_text = ''
        # print self.icgCamData
        getMaxLength = float(max([float(v['icgLength']) for v in self.icgCamData.values()]))
        # self.zkLength = float(xNumMax * getMaxLength - 900) / xNumMax
        # coupon_length = self.zkLength
        # === 增加阻抗序号层别 Song 2020.05.15====
        GEN.DELETE_LAYER('icg_index_mark')
        GEN.CREATE_LAYER('icg_index_mark')
        # ======================================
        # print json.dumps(rever_imp_data, sort_keys=True, indent=2, separators=(',', ': '))
        # === 2021.01.19 Chao.Song 获取zkCoupon中阻抗数量最少的那组 ===
        group_num_list = [len(self.teamc[i]['siglyr']) for i in self.teamc]
        # print json.dumps(self.teamc, indent=2)
        # === 2021.12.23 增加分割阻抗分组的
        for split_i in self.coupon_area:
            current_ids = self.coupon_area[split_i]['numlist']
            group_num_list = [len(self.teamc[i]['siglyr']) for i in current_ids]
            min_icg_num = min(group_num_list)
            get_min_ind = group_num_list.index(min_icg_num)
            min_icg_ind = current_ids[get_min_ind]
            self.icgCamData[min_icg_ind]['min_icg'] = 'yes'

        self.laser_add_pad_layers = []# 定义镭射对应内层pad的层
        
        # 在各couponstep每层铺铜，并增加负性铜皮
        # === i 阻抗条编号，从1开始

        # print rever_imp_data

        # 在处理低压区阻抗条没有阻抗数据 这种再合并阻抗时需要删除处理
        self.delete_icg_name = []
        self.exists_icg_name = []
        numlist_numbers = []
        for k_v in self.coupon_area:
            numlist_numbers += self.coupon_area[k_v]['numlist']
        numlist_numbers = sorted(numlist_numbers)
        # for i in range(1, self.coupon_num + 1):
        for i in numlist_numbers:
            coupon_name = self.icgCamData[i]['icgName']
            if self.mode == 'dy':
                coupon_name = coupon_name + '-d'
            coupon_data = [cc for cc in rever_imp_data if cc['igroup'] == i]
            
            if not coupon_data:
                self.delete_icg_name.append(coupon_name)
            else:
                self.exists_icg_name.append(coupon_name)


            coupon_length = self.icgCamData[i]['each_coupon_length'] + self.extra_strech_coupon_length * 1000
            coupon_height = self.icgCamData[i]['icgHeight']
            coupon_length_inch = coupon_length * 0.001
            coupon_height_inch = coupon_height * 0.001
            # coupon_length = self.icgCamData[i]['icgLength']
            if GEN.STEP_EXISTS(job=self.job_name, step=coupon_name) == 'yes':
                self.GOPEN_STEP(coupon_name, job=self.job_name)
            else:
                GEN.CREATE_ENTITY('', job=self.job_name, step=coupon_name)
                self.GOPEN_STEP(coupon_name, job=self.job_name)
            GEN.CHANGE_UNITS(units='inch')
            GEN.COM('profile_rect, x1=0, y1=0, x2=%s, y2=%s' % (coupon_length_inch, coupon_height_inch))
            # 增加ww层的外形线
            self.gCreateLayer('ww', coupon_name, ins_lay='drl', atype='signal', context='misc', location='after')
            GEN.COM('profile_to_rout,layer=ww,width=5')
            # 增加挡点层
            self.gCreateLayer('md1', coupon_name, ins_lay='m1', atype='solder_paste', context='board',
                              location='before')
            self.gCreateLayer('md2', coupon_name, ins_lay='m2', atype='solder_paste', context='board', location='after')

            GEN.CLEAR_LAYER()
            GEN.COM("affected_layer,name=,mode=all,affected=yes")
            GEN.COM("sel_delete")
            imp_num = len(self.teamc[i]['siglyr'])
            start_x0 = 1 * self.cedian_spc_x * 0.001 * 2
            add_start_x0 = start_x0
            start_y0 = coupon_height * 0.001 * 0.5 - self.cedian_spc_y * 0.001 * 0.5
            add_nx = imp_num * 2
            add_dx = self.cedian_spc_x
            add_ny = 2
            add_dy = self.cedian_spc_y
            add_pol = 'negative'
            c_start_x0 = start_x0 * 1.0
            # === 计算出位置，并添加到字典中 ===
            for index, line in enumerate(coupon_data):
                if line['wgroup'] == 1:
                    place = 'mid'
                elif line['wgroup'] == 2:
                    place = 'up'
                elif line['wgroup'] == 3:
                    place = 'down'
                else:
                    place = 'bot'
                coupon_data[index]['place'] = place
                if line['imodel'] in [u'特性', u'特性共面']:
                    c_add_nx = 1
                    c_model = 'single'
                    coupon_data[index]['start_x0'] = c_start_x0
                    coupon_data[index]['start_y0'] = start_y0
                    coupon_data[index]['neg_wid'] = self.neg_wid
                    coupon_data[index]['add_nx'] = c_add_nx
                    coupon_data[index]['add_ny'] = add_ny
                    coupon_data[index]['add_dx'] = add_dx
                    coupon_data[index]['add_dy'] = add_dy
                    coupon_data[index]['mode'] = c_model
                    if self.add_other_hole is True:
                        coupon_data[index]['hx1'] = c_start_x0 - (self.hole_wid + self.max_burry_size) * 0.25 * 0.001
                        coupon_data[index]['hx2'] = c_start_x0 + (self.hole_wid + self.max_burry_size) * 0.25 * 0.001
                        coupon_data[index]['hy1'] = start_y0 - (self.hole_wid + self.max_burry_size) * 0.25 * 0.001
                        coupon_data[index]['hy2'] = start_y0 + (self.hole_wid + self.max_burry_size) * 0.25 * 0.001
                    c_start_x0 = c_start_x0 * 1.0 + add_dx * 0.001
                elif line['imodel'] in [u'差动', u'差动共面']:
                    c_add_nx = 2
                    c_model = 'double'
                    coupon_data[index]['start_x0'] = c_start_x0
                    coupon_data[index]['start_y0'] = start_y0
                    coupon_data[index]['neg_wid'] = self.neg_wid
                    coupon_data[index]['add_nx'] = c_add_nx
                    coupon_data[index]['add_ny'] = add_ny
                    coupon_data[index]['add_dx'] = add_dx
                    coupon_data[index]['add_dy'] = add_dy
                    coupon_data[index]['mode'] = c_model
                    if self.add_other_hole is True:
                        coupon_data[index]['hx1'] = c_start_x0 - (self.hole_wid + self.max_burry_size) * 0.25 * 0.001
                        coupon_data[index]['hx2'] = c_start_x0 + (self.hole_wid + self.max_burry_size) * 0.25 * 0.001
                        coupon_data[index]['hy1'] = start_y0 - (self.hole_wid + self.max_burry_size) * 0.25 * 0.001
                        coupon_data[index]['hy2'] = start_y0 + (self.hole_wid + self.max_burry_size) * 0.25 * 0.001
                    c_start_x0 = c_start_x0 * 1.0 + add_dx * 0.001 * 2

            GEN.COM("affected_filter,filter=(type=signal&context=board)")
            self.Add_put_surface(dis_to_p_x=0.01, dis_to_p_y=0.01)
            each_cor_keys = ['start_x0', 'start_y0', 'add_nx', 'add_ny', 'add_dx', 'add_dy', 'mode', 'place']
            # 信号层加负性pad
            for index, line in enumerate(coupon_data):
                each_cor_list = [self.neg_wid] + [line[ck] for ck in each_cor_keys] + [add_pol]
                self.Add_cedian_pad(*each_cor_list, atype='neg')
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER('drl', 'yes')
            # 钻孔层加孔
            for index, line in enumerate(coupon_data):
                each_cor_list = [self.hole_wid] + [line[ck] for ck in each_cor_keys] + ['positive']
                self.Add_cedian_pad(*each_cor_list, atype='pad')

            # === TODO 添加其他层的钻孔
            if self.inner_test_add is True:
                # oth_index = 1
                for h_index,hole_layer in enumerate(self.drl_info['drl_layer']):
                    if hole_layer == self.inner_burry_layer:
                        GEN.CLEAR_LAYER()
                        GEN.AFFECTED_LAYER(hole_layer, 'yes')
                        # 埋孔层加孔
                        drl_size = float(self.drl_info['min_list'][h_index])/25.4
                        
                        if self.laser_test_add:
                            
                            move_size = 750 * 0.5 / 25.4 - 4 - drl_size * 0.5
                            
                            for s, layer in enumerate(self.sig_layers):                                
                                if s + 1 <= self.job_layer_num * 0.5:
                                    flag = 1
                                else:
                                    flag = -1
                                    
                                if layer in GEN.GET_ATTR_LAYER('outer'):
                                    continue
                                
                                for j in range(1, 5):
                                    laser_drill = "s{0}-{1}".format(s+1, s+1+flag*j)
                                    
                                    # 有1to3 1to4的优先用
                                    for m in range(1, 5):                        
                                        laser_drill_skipvia = "s{0}-{1}".format(s+1, s+1+flag*(j+m))
                                        if laser_drill_skipvia in self.drl_info['drl_layer']:                            
                                            laser_drill = laser_drill_skipvia[::]
                
                                    if laser_drill in self.drl_info['drl_layer']:
                                        # 镭射在埋孔内的不添加
                                        is_add_hole = True
                                        for h_index,mai_hole_layer in enumerate(self.drl_info['drl_layer']):
                                            if mai_hole_layer == hole_layer:
                                                if laser_drill.split("-")[0].replace("s", "b") in mai_hole_layer or \
                                                   "-" + laser_drill.split("-")[0][1:] in mai_hole_layer:
                                                    is_add_hole = False
                                                    
                                        # 镭射底层钻在埋孔对应的起始层时
                                        is_laser_drill_mai_hole_layer = False
                                        for h_index,mai_hole_layer in enumerate(self.drl_info['drl_layer']):
                                            if mai_hole_layer == hole_layer:
                                                if "b" + laser_drill.split("-")[1] in mai_hole_layer or \
                                                   "-" + laser_drill.split("-")[1] in mai_hole_layer:
                                                    is_laser_drill_mai_hole_layer = True
                                                    
                                        if is_add_hole and is_laser_drill_mai_hole_layer:
                                            
                                            h_index = self.drl_info['drl_layer'].index(laser_drill)
                                            hole_size = float(self.drl_info['min_list'][h_index])/25.4
                                            
                                            if drl_size + hole_size * 2 + 4 * 2  + 2 * 2  < 750 / 25.4:
                                                move_size = 0
                                            
                                            if drl_size + hole_size + 4  + 2 * 2  > 750 / 25.4:
                                                move_size = 0
                            
                            if drl_size * 25.4 > 250 and move_size > 0:
                                move_size = 750 * 0.5 / 25.4 - 2 - drl_size * 0.5
                                
                            for index, line in enumerate(coupon_data):
                                each_cor_list = [drl_size] + [line["start_x0"]] +\
                                    [line["start_y0"] - move_size*0.001] +\
                                    [line[ck] for ck in each_cor_keys if ck not in ["start_x0", "start_y0"]] + ['positive']
                                self.Add_cedian_pad(*each_cor_list, atype='pad')
                        else:
                            for index, line in enumerate(coupon_data):
                                each_cor_list = [drl_size] + [line[ck] for ck in each_cor_keys] + ['positive']
                                self.Add_cedian_pad(*each_cor_list, atype='pad')
                            
            # if "-lyh" in self.job_name:
            # GEN.PAUSE(str([self.drl_info['drl_layer']]))
            # http://192.168.2.120:82/zentao/story-view-7237.html 20240731 by lyh 镭射孔导通内层
            if self.laser_test_add:
                
                data_info = get_inplan_all_flow(self.job_name, select_dic=True)
                plug_process = ['HDI122','HDI172']
                gk_process = ['HDI153']                              
                
                for s, layer in enumerate(self.sig_layers):
                    
                    if s + 1 <= self.job_layer_num * 0.5:
                        flag = 1
                    else:
                        flag = -1
                        
                    if layer in GEN.GET_ATTR_LAYER('outer'):
                        continue
                    
                    for j in range(1, 5):
                        laser_drill = "s{0}-{1}".format(s+1, s+1+flag*j)
                        
                        # 有1to3 1to4的优先用
                        for m in range(1, 5):                        
                            laser_drill_skipvia = "s{0}-{1}".format(s+1, s+1+flag*(j+m))
                            if laser_drill_skipvia in self.drl_info['drl_layer']:                            
                                laser_drill = laser_drill_skipvia[::]
    
                        if laser_drill in self.drl_info['drl_layer']:
                            # 镭射在埋孔内的不添加
                            is_add_hole = True
                            for h_index,hole_layer in enumerate(self.drl_info['drl_layer']):
                                if hole_layer == self.inner_burry_layer:
                                    if laser_drill.split("-")[0].replace("s", "b") in hole_layer or \
                                       "-" + laser_drill.split("-")[0][1:] in hole_layer:
                                        is_add_hole = False
                                        
                            # 镭射底层钻在埋孔对应的起始层时
                            is_laser_drill_mai_hole_layer = False
                            mai_hole_size = 0
                            exists_plug_gk_process = False
                            for h_index,hole_layer in enumerate(self.drl_info['drl_layer']):
                                if hole_layer == self.inner_burry_layer:
                                    if "b" + laser_drill.split("-")[1] in hole_layer or \
                                       "-" + laser_drill.split("-")[1] in hole_layer:
                                        is_laser_drill_mai_hole_layer = True                                        
                                        mai_hole_size = float(self.drl_info['min_list'][h_index])/25.4
                                        suffix = "0000"
                                        if len(hole_layer) == 4:
                                            suffix = "0{1}0{3}".format(*list(hole_layer))
                                        if len(hole_layer) == 5:
                                            suffix = "0{1}{3}{4}".format(*list(hole_layer))
                                        if len(hole_layer) == 6:
                                            suffix = "{1}{2}{4}{5}".format(*list(hole_layer))
                                        #if "-lyh" in self.job_name:
                                            #GEN.PAUSE(str([suffix]))
                                        exists_gk_process = [dic_info for dic_info in data_info
                                                             if gk_process[0] in dic_info["OPERATION_CODE"]
                                                             and suffix in dic_info["MRP_NAME"]]
                                        exists_plug_process = [dic_info for dic_info in data_info
                                                               if (plug_process[0] in dic_info["OPERATION_CODE"]
                                                               or plug_process[1] in dic_info["OPERATION_CODE"])
                                                               and suffix in dic_info["MRP_NAME"]]
                                        
                                        if exists_gk_process and exists_plug_process:                                            
                                            exists_plug_gk_process = True
                                            break
                            
                            #if "-lyh" in self.job_name:
                                #GEN.PAUSE(str([laser_drill, exists_plug_gk_process, is_laser_drill_mai_hole_layer]))
                                
                            if is_add_hole:
                                
                                h_index = self.drl_info['drl_layer'].index(laser_drill)
                                hole_size = float(self.drl_info['min_list'][h_index])/25.4
                                
                                GEN.CLEAR_LAYER()
                                GEN.AFFECTED_LAYER(laser_drill, 'yes')
                                
                                move_size = 750 * 0.5 / 25.4 - 2 - hole_size * 0.5
                                if hole_size * 25.4 >= 250 and not is_laser_drill_mai_hole_layer:
                                    move_size = 0
                                
                                # 非树脂塞+盖孔电镀时 间距不满足时不加镭射
                                if mai_hole_size + hole_size + 4  + 2 * 2  > 750 / 25.4 and not exists_plug_gk_process:
                                    continue
                                
                                two_hole = False
                                if mai_hole_size + hole_size * 2 + 4 * 2  + 2 * 2  < 750 / 25.4:
                                    two_hole = True                                
                                
                                if exists_plug_gk_process:
                                    two_hole = True
                                    if hole_size * 25.4 >= 250:
                                        move_size = 0
                                    
                                for index, line in enumerate(coupon_data):
                                    if hole_size * 25.4 < 250 and two_hole:                                        
                                        each_cor_list = [hole_size] + [line["start_x0"] + move_size*0.001] + [line[ck] for ck in each_cor_keys if ck != "start_x0"] + ['positive']
                                        self.Add_cedian_pad(*each_cor_list, atype='pad')
                                        each_cor_list = [hole_size] + [line["start_x0"] - move_size*0.001] + [line[ck] for ck in each_cor_keys if ck != "start_x0"] + ['positive']
                                        self.Add_cedian_pad(*each_cor_list, atype='pad')
                                    else:
                                        # 在埋孔上方加一个镭射
                                        each_cor_list = [hole_size] + [line["start_x0"]] +\
                                            [line["start_y0"] + move_size*0.001] +\
                                            [line[ck] for ck in each_cor_keys if ck not in ["start_x0", "start_y0"]] + ['positive']
                                        self.Add_cedian_pad(*each_cor_list, atype='pad')                                        
                                    
                                #线路层加孔pad
                                sig_layer1 = laser_drill.split("-")[0].replace("s", "l")
                                sig_layer2 = "l" + laser_drill.split("-")[1]
                                self.laser_add_pad_layers.append(sig_layer1)
                                self.laser_add_pad_layers.append(sig_layer2)
                                
            # 取消2020.03.11
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER('md1', 'yes')
            GEN.AFFECTED_LAYER('md2', 'yes')
            for index, line in enumerate(coupon_data):
                each_cor_list = [self.md_wid] + [line[ck] for ck in each_cor_keys] + ['positive']
                self.Add_cedian_pad(*each_cor_list, atype='pad')

            # 2019.11.27 挡点等大 取消2020.03.11
            # self.Add_dingwei_pad (0.15, coupon_height * 0.001 * 0.5, self.dingwei_wid, coupon_length * 0.001)
            GEN.CLEAR_LAYER()

            # 防焊层加开窗
            # 20190916 需更改此位置，防焊所有接地pad均为方pad
            GEN.COM("affected_filter, filter=(type=solder_mask&context=board&side=top|bottom)")
            # self.Add_cedian_pad (start_x0, start_y0, sm_pad, add_nx, add_ny, add_dx, add_dy, 'positive', type='pad',
            #                      mode=imodel)
            for index, line in enumerate(coupon_data):
                each_cor_list = [self.sm_pad] + [line[ck] for ck in each_cor_keys] + ['positive']
                self.Add_cedian_pad(*each_cor_list, atype='neg')

            # 开窗单边5， 2019.11.27 取消2020.03.11
            # self.Add_dingwei_pad (0.15, coupon_height * 0.001 * 0.5, 78.74 + 10, coupon_length * 0.001)
            GEN.CLEAR_LAYER()

            ginfo = GEN.DO_INFO("-t layer -e %s/%s/%s -d EXISTS" % (self.job_name, coupon_name, 'imp_mark'))
            # print ginfo
            if ginfo['gEXISTS'] == 'no':
                GEN.CREATE_LAYER('imp_mark')
            GEN.AFFECTED_LAYER('imp_mark', 'yes')
            GEN.SEL_DELETE()
            # 先添加ZK Step标记
            GEN.ADD_TEXT(0.035, coupon_height * 0.001 * 0.5 - 0.01, str('ZK') + str(i), 0.03,
                         0.03, w_factor='0.4167', polarity='negative', mirr='no')
            GEN.CLEAR_LAYER()
            # === 上移此预定义值 ===
            chg_text_dy = 0
            if coupon_height > 450:
                chg_text_dy = 0.0075
            for c_index, line in enumerate(coupon_data):
                # print json.dumps(line, sort_keys=True)
                kk = line['igroup']
                # --开始添加阻抗线--
                imp_num = len(self.teamc[line['igroup']]['siglyr'])
                line1_wid = line['workwidth']
                GEN.CHANGE_UNITS(units='inch')
                work_minp2line = self.min_p2line

                if coupon_height > 450:
                    work_minp2line = 40

                start_y0 = coupon_height * 0.001 * 0.5 - self.cedian_spc_y * 0.001 * 0.5
                GEN.CLEAR_LAYER()
                signal_layer = line['worklay'].lower()
                GEN.WORK_LAYER(signal_layer)
                text_y1 = start_y0 - 0.015 - chg_text_dy
                # === V5.3.2 增加一些走线对接地pad影响的检测 ===
                top_places_check = []
                bot_places_check = []

                for tmpi, tmpC in enumerate(coupon_data):
                    # if tmpi < c_index:
                    tmp_work_lyr = tmpC['worklay'].lower()
                    if line['reftop'] != '':
                        ref_top = line['reftop'].lower()
                        if tmp_work_lyr == ref_top:
                            top_places_check.append(tmpC['place'])
                        elif ref_top in tmpC['midlyrs']:
                            top_places_check.append(tmpC['place'])

                    if line['refbot'] != '':
                        ref_bot = line['refbot'].lower()
                        if tmp_work_lyr == ref_bot:
                            bot_places_check.append(tmpC['place'])
                        elif ref_bot in tmpC['midlyrs']:
                            top_places_check.append(tmpC['place'])                
                
                if len(top_places_check) >= 2:
                    warn_text += u"检测到：ZK%s 层 %s 的参考层:%s接地pad可能未与大铜皮相接.|\n" % (line['igroup'], line['worklay'], line['reftop'])
                if len(bot_places_check) >= 2:
                    warn_text += u"检测到：ZK%s 层 %s 的参考层:%s接地pad可能未与大铜皮相接.|\n" % (line['igroup'], line['worklay'], line['refbot'])
                if line['workspc2cu'] == '' or line['workspc2cu'] == 0:
                    # 工艺通知线到铜最大为9mil 20230414 by lyh 暂时屏蔽 等工艺通知 20230620
                    linetocu = max([20, line['workwidth'] * 2])
                    # linetocu = max([9, line['workwidth'] * 2])
                else:
                    linetocu = line['workspc2cu']
                if line['imodel'] == '特性' or line['imodel'] == '特性共面':
                    start_x0 = line['start_x0']
                    # 增加阻抗线长
                    imp_line_length = (coupon_length * 0.001 - start_x0 - 0.2) * 1000
                    if self.imp_coupon_line_length > 0:
                        imp_line_length = self.imp_coupon_line_length * 1000
                        if self.imp_coupon_line_length > coupon_length * 0.001 - start_x0 - 0.2:
                            warn_text += u"检测到：ZK%s 层 %s 线超出阻抗模块长度,请检查阻抗线长度[%.3f]输入是否正确.|\n" % (line['igroup'], line['worklay'],
                                                                                                                        self.imp_coupon_line_length)
                        
                    if imp_line_length < 4500:
                        warn_text += u"检测到：ZK%s 层 %s 线长小于4.5英寸.|\n" % (line['igroup'], line['worklay'])
                    # V2.0.3增加判断，当阻抗线按上下走线且阻抗条较宽时，加大上下线走线距离测点盘y方向的距离
                    if line['wgroup'] == 1:
                        work_minp2line = self.min_p2line
                    elif line['wgroup'] == 2:
                        text_y1 = start_y0 - 0.015 + chg_text_dy + self.cedian_spc_y * 0.001

                    place = line['place']
                    #  === Song  2020.06.12 增加此中间隔离层的套铜宽度，注意midlyrs中间包含阻抗线信号层
                    # http://192.168.2.120:82/zentao/story-view-1367.html
                    get_neg_width = self.add_sig_imp_line(start_x0, start_y0, line1_wid, self.cedian_spc_x, self.cedian_spc_y,
                                          self.cedian_wid, work_minp2line, imp_line_length, type='negline',
                                          spctocu=linetocu, add_locate=place,
                                          neg_attr_text=coupon_name + "_jxpad_" + line['worklay'] + "_" + str(c_index))
                    if signal_layer == 'l1' and get_neg_width > 84 and line['wgroup'] == 1:
                        # === 当隔离线宽大于84mil时，添加的参考层文字会被覆盖
                        # === 当前层是否还有下走线，如果有，不能移动
                        tmp_check_list = [tmpC for tmpC in rever_imp_data if tmpC['worklay'] == signal_layer
                                          and tmpC['igroup'] == kk and tmpC['wgroup'] == 3]
                        if len(tmp_check_list) > 0:
                            pass
                        else:
                            text_y1 = text_y1 - (get_neg_width - 84) * 0.5 * 0.001 - 0.01
                            # text_y1 = 0.02

                    if len(line['midlyrs']) == 1 and signal_layer in line['midlyrs']:
                        pass
                    elif len(line['midlyrs']) > 0:
                        GEN.CLEAR_LAYER()
                        self.GAFFECT_LAYERS(line['midlyrs'])
                        GEN.AFFECTED_LAYER(signal_layer, 'no')
                        # 隔离层在原有基础上加大10mil
                        self.add_sig_imp_line(start_x0, start_y0, line1_wid, self.cedian_spc_x, self.cedian_spc_y,
                                              self.cedian_wid, work_minp2line, imp_line_length, type='midneg',
                                              spctocu=linetocu, add_locate=place)
                        GEN.COM('affected_layer,mode=all,affected=no')
                        GEN.WORK_LAYER(signal_layer)

                    self.add_sig_imp_line(start_x0, start_y0, line1_wid, self.cedian_spc_x, self.cedian_spc_y,
                                          self.cedian_wid, work_minp2line,
                                          imp_line_length, spctocu=linetocu, add_locate=place, add_attr='yes', ohm=line['ohm'],
                                          orig_width=line['showwid'], orig_spc=line["showlspc"], orig_spc2cu=line["showspc2cu"])
                    # 2020.03.14 更改添加字样的判断由单根阻抗条，更改为单层序号 line['gindex'] --> line['wgroup']
                    if line['textmir'] == 'no':
                        text_x1 = 0.2 + imp_num * 2 * self.cedian_spc_x * 0.001 + line['wgroup'] // 2 * 1.2
                    elif line['textmir'] == 'yes':
                        text_x1 = 0.2 + imp_num * 2 * self.cedian_spc_x * 0.001 + line['wgroup'] // 2 * 1.2 + 1.2

                    # --添加测试点--
                    # ----增加测点添加层别当中间层包含顶层及底层时，为防止外层pad被套空，增加pad
                    self.GAFFECT_LAYERS(line['midlyrs'], mode='topbot')
                    start_y1 = start_y0 + self.cedian_spc_y * 0.001

                    if place in ['up', 'mid']:
                        sig_pad_cor = [start_x0, start_y1, 'r%s' % self.cedian_wid]
                        pow_pad_cor = [start_x0, start_y0, 's%s' % self.cedian_wid]
                    else:
                        sig_pad_cor = [start_x0, start_y0, 'r%s' % self.cedian_wid]
                        pow_pad_cor = [start_x0, start_y1, 's%s' % self.cedian_wid]
                    # === V5.1 所有层加pad
                    GEN.ADD_PAD(*sig_pad_cor, nx=1, ny=1)
                    GEN.COM('affected_layer,mode=all,affected=no')
                    # === V5.1 所有层加pad
                    GEN.ADD_PAD(*pow_pad_cor, nx=1, ny=1)

                    # 在影响层添加接地点pad及铜皮连接
                    GEN.CLEAR_LAYER()
                    # === 判断是否开窗阻抗，开窗阻抗做法 ===
                    if line['solderopen'] == '是':
                        if signal_layer != 'l1':
                            GEN.AFFECTED_LAYER('m2', 'yes')
                        else:
                            GEN.AFFECTED_LAYER('m1', 'yes')

                        self.add_sig_imp_line(start_x0, start_y0, line1_wid, self.cedian_spc_x, self.cedian_spc_y,
                                              self.cedian_wid, work_minp2line, imp_line_length, type='maskline',
                                              spctocu=linetocu, add_locate=place)
                        GEN.CLEAR_LAYER()
                    # === 2021.06.08 Song 增加判断，无参考层不添加 ===
                    if line['reftop'] == "" and line['refbot'] == "":
                        pass
                    else:
                        self.GAFFECT_LAYERS([line['reftop'].lower(), line['refbot'].lower()])
                        # === V5.1 所有层加pad
                        GEN.COM('cur_atr_reset')
                        GEN.COM('cur_atr_set, attribute=.string, text=' + coupon_name + "_jxpad_" + line['worklay'] + "_" + str(c_index))
                        GEN.ADD_PAD(*pow_pad_cor, nx=1, ny=1, attr="yes")
                        GEN.COM('cur_atr_reset')
                        # --增加交叉线,不要pow_pad_cor里的最后一位symbol
                        jx_list = pow_pad_cor[:-1] + [self.cedian_wid + 20, 15]
                        self.add_jx_line(*jx_list, addnum=4)
                    # 共面阻抗当前层需增加交叉线接地线
                    # === V5.1 由于增加了交叉线的特别处理，以及交叉线由x改为+ 取消以下差动共面，交叉线三根线的加法
                    if line['imodel'] == '特性共面':
                        GEN.CLEAR_LAYER()
                        self.GAFFECT_LAYERS([line['worklay'].lower()])
                        # --增加交叉线
                        # 增加判断，当前添加的添加的阻抗序号为2，且当前层存在阻抗序号为3时，仅增加三段线
                        # tmp_check_list = [tmpC for tmpC in rever_imp_data if tmpC['worklay'] == line['worklay']
                        #                   and tmpC['igroup'] == kk and tmpC['wgroup'] == 3]
                        # if line['wgroup'] == 2 and len(tmp_check_list) != 0:
                        #     jx_num = 3
                        # else:
                        #     jx_num = 4
                        jx_num = 4
                        jx_list = pow_pad_cor[:-1] + [self.cedian_wid + 20, 15]
                        self.add_jx_line(*jx_list, addnum=jx_num)
                    GEN.CLEAR_LAYER()

                elif line['imodel'] == '差动' or line['imodel'] == '差动共面':
                    start_x0 = line['start_x0'] + line['add_dx'] * 0.001
                    # 增加阻抗线长
                    imp_line_length = (coupon_length * 0.001 - start_x0 - 0.2) * 1000
                    if self.imp_coupon_line_length > 0:
                        imp_line_length = self.imp_coupon_line_length * 1000
                        if self.imp_coupon_line_length > coupon_length * 0.001 - start_x0 - 0.2:
                            warn_text += u"检测到：ZK%s 层 %s 线超出阻抗模块长度,请检查阻抗线长度[%.3f]输入是否正确.|\n" % (line['igroup'], line['worklay'],
                                                                                                                        self.imp_coupon_line_length)

                    if imp_line_length < 4500:
                        warn_text += u"检测到：ZK%s 层 %s 线长小于4.5英寸。|" % (line['igroup'], line['worklay'])
                    if line['wgroup'] == 1:
                        work_minp2line = self.min_p2line
                    elif line['wgroup'] == 2:
                        text_y1 = start_y0 - 0.015 + chg_text_dy + self.cedian_spc_y * 0.001

                    place = line['place']
                    #  === Song  2020.06.12 增加此中间隔离层的套铜宽度，注意midlyrs中间包含阻抗线信号层
                    # http://192.168.2.120:82/zentao/story-view-1367.html

                    self.add_two_imp_line(start_x0, start_y0, line['workwidth'], line['worklspc'],
                                          self.cedian_spc_x, self.cedian_spc_y,
                                          self.cedian_wid, work_minp2line, imp_line_length, self.arc_d,
                                          type='negline', spctocu=linetocu, add_locate=place,
                                          neg_attr_text=coupon_name + "_jxpad_" + line['worklay'] + "_" + str(c_index))
                    if len(line['midlyrs']) == 1 and signal_layer in line['midlyrs']:
                        pass
                    elif len(line['midlyrs']) > 0:

                        GEN.CLEAR_LAYER()
                        self.GAFFECT_LAYERS(line['midlyrs'])
                        GEN.AFFECTED_LAYER(signal_layer, 'no')
                        self.add_two_imp_line(start_x0, start_y0, line['workwidth'], line['worklspc'],
                                              self.cedian_spc_x, self.cedian_spc_y,
                                              self.cedian_wid, work_minp2line, imp_line_length, self.arc_d,
                                              type='midneg', spctocu=linetocu, add_locate=place)
                        GEN.COM('affected_layer,mode=all,affected=no')
                        GEN.WORK_LAYER(signal_layer)

                    self.add_two_imp_line(start_x0, start_y0, line['workwidth'], line['worklspc'],
                                          self.cedian_spc_x, self.cedian_spc_y,
                                          self.cedian_wid, work_minp2line, imp_line_length, self.arc_d,
                                          add_locate=place, add_attr='yes', ohm=line['ohm'],
                                          orig_width=line['showwid'], orig_spc=line["showlspc"], orig_spc2cu=line["showspc2cu"])

                    # 2020.03.14 更改添加字样的判断由单根阻抗条，更改为单层序号 line['gindex'] --> line['wgroup']
                    if line['textmir'] == 'no':
                        text_x1 = 0.2 + imp_num * 2 * self.cedian_spc_x * 0.001 + line['wgroup'] // 2 * 1.2
                    elif line['textmir'] == 'yes':
                        text_x1 = 0.2 + imp_num * 2 * self.cedian_spc_x * 0.001 + line['wgroup'] // 2 * 1.2 + 1.2

                    self.GAFFECT_LAYERS(line['midlyrs'], mode='topbot')
                    if place == 'mid':
                        sig_pad_cor = [start_x0, start_y0, 'r%s' % self.cedian_wid]
                        pow_pad_cor1 = [start_x0 - self.cedian_spc_x*0.001, start_y0]
                        pow_pad_cor2 = [start_x0 - self.cedian_spc_x*0.001, start_y0 + self.cedian_spc_y * 0.001]
                        sig_dict = dict(nx=1, ny=2, dx=self.cedian_spc_x,dy=self.cedian_spc_y)
                    elif place == 'up':
                        sig_pad_cor = [start_x0 - self.cedian_spc_x*0.001, start_y0 + self.cedian_spc_y * 0.001, 'r%s' % self.cedian_wid]
                        pow_pad_cor1 = [start_x0 - self.cedian_spc_x*0.001, start_y0]
                        pow_pad_cor2 = [start_x0, start_y0]
                        sig_dict = dict(nx=2, ny=1, dx=self.cedian_spc_x,dy=self.cedian_spc_y)
                    else:
                        # place == 'down':
                        sig_pad_cor = [start_x0 - self.cedian_spc_x * 0.001, start_y0, 'r%s' % self.cedian_wid]
                        pow_pad_cor1 = [start_x0 - self.cedian_spc_x*0.001, start_y0 + self.cedian_spc_y * 0.001]
                        pow_pad_cor2 = [start_x0, start_y0 + self.cedian_spc_y * 0.001]
                        sig_dict = dict(nx=2, ny=1, dx=self.cedian_spc_x,dy=self.cedian_spc_y)
                    pow_pad_cor = pow_pad_cor1 + ['s%s' % self.cedian_wid]
                    # ===添加测试点===
                    GEN.ADD_PAD(*pow_pad_cor, **sig_dict)
                    # ===增加测点添加层别当中间层包含顶层及底层时，为防止外层pad被套空，增加pad
                    GEN.ADD_PAD(*sig_pad_cor, **sig_dict)

                    # 在影响层添加接地点pad及铜皮连接
                    GEN.CLEAR_LAYER()
                    # === 判断是否开窗阻抗，开窗阻抗做法 ===
                    if line['solderopen'] == '是':
                        if signal_layer != 'l1':
                            GEN.AFFECTED_LAYER('m2', 'yes')
                        else:
                            GEN.AFFECTED_LAYER('m1', 'yes')

                        self.add_two_imp_line(start_x0, start_y0, line['workwidth'], line['worklspc'],
                                              self.cedian_spc_x, self.cedian_spc_y,
                                              self.cedian_wid, work_minp2line, imp_line_length, self.arc_d,
                                              type='maskline', spctocu=linetocu, add_locate=place, add_attr='no')
                        GEN.CLEAR_LAYER()

                    # === 2021.06.08 Song 增加判断，无参考层不添加 ===
                    if line['reftop'] == "" and line['refbot'] == "":
                        pass
                    else:
                        self.GAFFECT_LAYERS([line['reftop'].lower(), line['refbot'].lower()])
                        pad_c1 = pow_pad_cor1 + ['s%s' % self.cedian_wid]
                        pad_c2 = pow_pad_cor2 + ['s%s' % self.cedian_wid]
                        GEN.COM('cur_atr_reset')
                        GEN.COM('cur_atr_set, attribute=.string, text=' + coupon_name + "_jxpad_" + line['worklay'] + "_" + str(c_index))
                        GEN.ADD_PAD(*pad_c1, nx=1, ny=1, dx=self.cedian_spc_x, dy=self.cedian_spc_y, attr="yes")
                        GEN.ADD_PAD(*pad_c2, nx=1, ny=1, dx=self.cedian_spc_x, dy=self.cedian_spc_y, attr="yes")
                        GEN.COM('cur_atr_reset')
                        # 增加交叉线，接地pad连接
                        jx1 = pow_pad_cor1 + [self.cedian_wid + 20, 15]
                        jx2 = pow_pad_cor2 + [self.cedian_wid + 20, 15]
                        self.add_jx_line(*jx1)
                        self.add_jx_line(*jx2)

                    # === V5.1 由于增加了交叉线的特别处理，以及交叉线由x改为+ 取消以下差动共面，交叉线三根线的加法
                    if line['imodel'] == '差动共面':
                        GEN.CLEAR_LAYER()
                        self.GAFFECT_LAYERS([line['worklay'].lower()])
                            # --增加交叉线
                            # 增加判断，当前添加的添加的阻抗序号为2，且当前层存在阻抗序号为3时，仅增加三段线
                            # tmp_check_list = [tmpC for tmpC in rever_imp_data if
                            #                   tmpC['worklay'] == line['worklay'] and tmpC['igroup'] == kk and
                            #                   tmpC['wgroup'] == 3]
                            # if line['wgroup'] == 2 and len(tmp_check_list) != 0:
                            #     jx_num = 3
                            # else:
                            #     jx_num = 4
                        jx_num = 4
                        jx1 = pow_pad_cor1 + [self.cedian_wid + 20, 15]
                        jx2 = pow_pad_cor2 + [self.cedian_wid + 20, 15]
                        self.add_jx_line(*jx1, addnum=jx_num)
                        self.add_jx_line(*jx2, addnum=jx_num)

                    GEN.CLEAR_LAYER()
                else:
                    # 增加无阻抗线宽类型提醒
                    warn_text += u"检测到：coupon %s 无阻抗线宽类型.|" % (i)
                    pass

                # 增加阻抗线宽，参考层字样
                self.GAFFECT_LAYERS([line['worklay'].lower()])
                if line['showlspc'] == 0:
                    mark_spc = '\\'
                else:
                    mark_spc = line['showlspc']
                if line['showspc2cu'] == 0:
                    mark_cu = '\\'
                else:
                    mark_cu = line['showspc2cu']
                if mark_cu == '\\' and mark_spc == '\\':
                    markText = str(line['showwid'])
                elif mark_cu == '\\' and mark_spc != '\\':
                    markText = str(line['showwid']) + '/' + str(mark_spc)
                elif mark_cu != '\\' and mark_spc == '\\':
                    markText = str(line['showwid']) + '/' + '/' + str(mark_cu)
                elif mark_cu != '\\' and mark_spc != '\\':
                    markText = str(line['showwid']) + '/' + str(mark_spc) + '/' + str(mark_cu)

                a_text = "%s REF %s %s %s OHM" % (line['worklay'].upper(), line['refmark'], markText, line['ohm'])
                GEN.ADD_TEXT(text_x1, text_y1, a_text, 0.03, 0.03,
                             w_factor='0.4167', polarity='negative', mirr=line['textmir'])
                
                #增加判断当前层是否还有同阻值的阻抗线 需加箭头标识给产线识别20231102 by lyh
                #exists_same_ohm = [tmpC for tmpC in rever_imp_data if tmpC['worklay'].lower() == signal_layer
                                  #and tmpC['igroup'] == kk and tmpC['ohm'] == line['ohm'] and tmpC != line]
                #if exists_same_ohm:
                # 周涌通知 全部加三角 http://192.168.2.120:82/zentao/story-view-6146.html 20240619 by lyh
                tri_angle = 0
                if line['wgroup'] == 2:
                    tri_angle = 0
                if line['wgroup'] == 1:
                    if text_y1 > coupon_height_inch * 0.5:
                        tri_angle = 180
                    else:
                        tri_angle = 0
                if line['wgroup'] == 3:
                    tri_angle = 180
                
                flag = -1
                if line['textmir'] == "yes":
                    flag = 1
                    
                GEN.ADD_PAD(text_x1+0.035*flag, text_y1+0.014, "tri19.685x27.559", pol='negative', angle=tri_angle)                            
                
                GEN.CLEAR_LAYER()
                GEN.WORK_LAYER('imp_mark')

                # 层别坐标计算
                mark_y1 = start_y0 + self.cedian_spc_y * 0.001 + 0.1
                if mark_y1 > coupon_height * 0.001 - 0.030:
                    mark_y1 = coupon_height * 0.001 - 0.030 - 0.02
                # 欧姆坐标计算
                mark_y0 = start_y0 - 0.13
                if mark_y0 < 0:
                    mark_y0 = 0.02
                # 加层别字样
                # 第一层增加添加字样判断，当L1层有上走线，层别会与负片相交，当L1层有下走线，层别会与欧姆相交 Bug料号：710-124A1
                # 如果为当前小分组1且存在小分组2，则需移动层别字样坐标
                # 如果为当前小分组2且存在小分组2，则需移动层别字样坐标,2021-11-03 差分阻抗条时欧姆值也需左移,Bug料号：940-243cb
                # 如果为当前小分组1且存在小分组3，则需移动欧姆坐标；
                # 如果为当前小分组2且存在小分组3，则需移动欧姆坐标；
                # 如果当前小分组为3，则移动欧姆坐标
                # 如果当前小分组为2且为差分，层别坐标移动
                layerTextAdddx = -0.015
                omTextAdddx = -0.015
                if line['worklay'].lower() == 'l1' :
                    if line['wgroup'] == 1:
                        tmp_check_list = [tmpC for tmpC in rever_imp_data if tmpC['worklay'] == line['worklay']
                                          and tmpC['igroup'] == kk and tmpC['wgroup'] == 2]
                        if len(tmp_check_list) != 0:
                            if coupon_height <= 450:
                                # 层别text 右移67mil，下移62mil
                                layerTextAdddx = layerTextAdddx + 0.067
                                mark_y1 = mark_y1 - 0.062
                            else:
                                mark_y1 = coupon_height * 0.001 - 0.030 - 0.02
                        tmp_check_list = [tmpC for tmpC in rever_imp_data if tmpC['worklay'] == line['worklay']
                                          and tmpC['igroup'] == kk and tmpC['wgroup'] == 3]
                        if len(tmp_check_list) != 0:
                            if coupon_height <= 450:
                                # 欧姆坐标上移 65mil，右移47mil
                                mark_y0 = mark_y0 + 0.065
                                omTextAdddx = 0.047 + omTextAdddx
                            else:
                                mark_y0 = 0.02

                    elif line['wgroup'] == 2:
                        tmp_check_list = [tmpC for tmpC in rever_imp_data if tmpC['worklay'] == line['worklay']
                                          and tmpC['igroup'] == kk and tmpC['wgroup'] == 2]
                        if len(tmp_check_list) != 0:
                            # 层别text左移 20mil
                            if coupon_height <= 450:
                                layerTextAdddx = layerTextAdddx - 0.020
                                if line['mode'] == 'double':
                                    # 差动类阻抗条才左移，如特性左移有与第三组线相交可能 V3.7.5 # V5.0 移到差分线最左侧
                                    # omTextAdddx = omTextAdddx - 0.065
                                    layerTextAdddx = layerTextAdddx - self.cedian_spc_x * 0.001
                            else:
                                mark_y1 = coupon_height * 0.001 - 0.030 - 0.02
                        tmp_check_list = [tmpC for tmpC in rever_imp_data if tmpC['worklay'] == line['worklay']
                                          and tmpC['igroup'] == kk and tmpC['wgroup'] == 3]
                        if len(tmp_check_list) != 0:
                            if coupon_height <= 450:
                                # 欧姆坐标上移 111mil
                                mark_y0 = mark_y0 + 0.111
                            else:
                                mark_y0 = 0.02

                    elif line['wgroup'] == 3:
                        if coupon_height <= 450:
                            mark_y0 = mark_y0 + 0.111
                        else:
                            mark_y0 = 0.02

                GEN.ADD_TEXT(start_x0 + layerTextAdddx, mark_y1, "%s" % (line['worklay']), 0.03,
                             0.03, w_factor='0.4167', polarity='negative', mirr='no')
                # 加欧姆字样
                ohm_width = 0.03
                if len(str(line['ohm'])) > 2:
                    ohm_width = 0.020
                GEN.ADD_TEXT(start_x0 + omTextAdddx, mark_y0, line['ohm'], ohm_width, 0.03,
                             w_factor='0.4167', polarity='negative', mirr='no')
                GEN.CLEAR_LAYER()
                # === 增加阻抗序号在其他层别 icg_index_mark Song  2020.05.15 ====
                GEN.AFFECTED_LAYER('icg_index_mark', 'yes')
                index_y0 = start_y0 + 0.035
                GEN.ADD_TEXT(start_x0 + omTextAdddx, index_y0, line['miindex'], ohm_width, 0.03,
                             w_factor='0.4167', polarity='positive', mirr='no')
                GEN.CLEAR_LAYER()
                GEN.WORK_LAYER('imp_mark')
                GEN.COM("sel_reverse")
                GEN.GET_SELECT_COUNT()
                # 2020.03.11 增加和外层物件touch的判断，不能碰到线，碰到负片需报警，尽量被铜皮包裹
                if int(GEN.COMANS) != 0:
                    GEN.COM("affected_filter, filter=(type=signal & context=board & side=top)")
                    GEN.FILTER_RESET()
                    GEN.COM('filter_set, filter_name=popup, update_popup=no, feat_types=line\;arc\;text')
                    GEN.COM("affected_filter, filter=(type=signal&context=board&side=top)")
                    GEN.COM('sel_ref_feat, layers=, use=select, mode=touch, pads_as=shape, '
                            'f_types=line\;pad\;surface\;arc\;text, polarity=positive\;negative,'
                            'include_syms=, exclude_syms=')
                    GEN.GET_SELECT_COUNT()
                    if int(GEN.COMANS) != 0:
                        warn_text += u"检测到：ZK%s从右向左序号%s位置有相交字.|" % (i, line['gindex'])
                    GEN.CLEAR_LAYER()
                    GEN.AFFECTED_LAYER('imp_mark', 'yes')
                    GEN.SEL_REVERSE()
                    # 偷懒写法，直接移动到L1
                    GEN.SEL_MOVE('l1')
                GEN.CLEAR_LAYER()
            # === 2020.06.12 更改添加外层pad 到最后位置
            if self.inner_test_add is False:
                # 外层加pad
                GEN.COM("affected_filter, filter=(type=signal&context=board&side=top|bottom)")
                if self.laser_test_add:
                    for s_layer in self.laser_add_pad_layers:
                        GEN.AFFECTED_LAYER(s_layer,'yes')    
            else:
                # === V5.1 所有层加pad
                GEN.COM("affected_filter, filter=(type=signal&context=board&side=top|bottom)")
                for b_layer in self.inner_pad_layer:
                    GEN.AFFECTED_LAYER(b_layer,'yes')
                    
                if self.laser_test_add:
                    for s_layer in self.laser_add_pad_layers:
                        GEN.AFFECTED_LAYER(s_layer,'yes')                       
                # GEN.COM("affected_filter, filter=(type=signal&context=board)")
            for index, line in enumerate(coupon_data):
                each_cor_list = [self.cedian_wid] + [line[ck] for ck in each_cor_keys] + ['positive']
                self.Add_cedian_pad(*each_cor_list, atype='neg')

            GEN.CLEAR_LAYER()
            # === 2021.01.19 添加料号名 ===
            GEN.COM("affected_filter, filter=(type=signal & context=board & side=top)")
            # if i == min_icg_ind:
            if 'min_icg' in self.icgCamData[i]:
                textjob_x1 = 0.2 + min_icg_num * 2 * self.cedian_spc_x * 0.001 + 2 * 1.2
                text_y1 = start_y0 - 0.015 + chg_text_dy + self.cedian_spc_y * 0.001
                textjob_y1 = text_y1
                GEN.ADD_TEXT(textjob_x1, textjob_y1, '$$JOB', '0.03', '0.03', w_factor='0.4166666567',
                             polarity='negative')
            GEN.CLEAR_LAYER()
        warn_array = self.split_combineCoupon()              

        if warn_array is not None:
            warn_text += '\n%s' % (''.join(warn_array))
        if warn_text:
            # showText = self.msgText (u'警告', warn_text)
            # self.msgBox (showText)
            return warn_text
        else:
            return None

    def gCreateLayer(self, layer, step_name, ins_lay=None, atype=None, context=None, location='after'):
        if GEN.LAYER_EXISTS(layer, job=self.job_name, step=step_name) == "no":
            GEN.CREATE_LAYER(layer, ins_lay=ins_lay, context=context, add_type=atype, location=location)
        GEN.COM('profile_to_rout,layer=ww,width=5')

    def GOPEN_STEP(self, step, job=None):
        if 'INCAM_SERVER' in os.environ.keys():
            GEN.COM("set_step, name=%s" % step)
            GEN.COM("open_group, job=%s, step=%s, is_sym=no" % (job, step))
            GEN.AUX("set_group, group=%s" % GEN.COMANS)
            GEN.COM("open_entity, job=%s, type=step, name=%s, iconic=no" % (job, step))
            status = GEN.STATUS
            return status
        else:
            GEN.COM('open_entity, job=%s, type=step, name=%s ,iconic=no' % (job, step))
            GEN.AUX('set_group, group=%s' % GEN.COMANS)
            status = GEN.STATUS
            return status

    def GAFFECT_LAYERS(self, layers, mode='all'):
        if mode == 'all':
            for onelay in layers:
                if onelay != '':
                    GEN.AFFECTED_LAYER(onelay, 'yes')
        elif mode == 'topbot':
            for onelay in layers:
                if onelay == 'l1' or onelay == 'l' + str(self.job_layer_num):
                    GEN.AFFECTED_LAYER(onelay, 'yes')

    def Add_put_surface(self, dis_to_p_x=0.02, dis_to_p_y=0.02):
        """
        铺铜
        :param dis_to_p_x:
        :param dis_to_p_y:
        :return:
        """
        GEN.COM("sr_fill, polarity=positive, step_margin_x=%s, step_margin_y=%s, step_max_dist_x=100, "
                "step_max_dist_y=100, sr_margin_x=0.01, sr_margin_y=0.01, sr_max_dist_x=0, sr_max_dist_y=0, "
                "nest_sr=yes, stop_at_steps =, consider_feat=no, consider_drill=no, consider_rout=no, "
                "dest=affected_layers, attributes=no" % (dis_to_p_x, dis_to_p_y))

    def Add_cedian_pad(self, sym_size, start_x0, start_y0, add_nx, add_ny, add_dx, add_dy, mode, place, add_pol, atype='neg'):
        """
        添加测试pad位置，
        :param sym_size: symbol尺寸 mil
        :param start_x0: 单位inch 一组测试点，左侧坐标
        :param start_y0: 单位inch 一组测试点，下坐标
        :param add_nx: x方向数量
        :param add_ny: y方向数量
        :param add_dx: 单位mil 测点间距x
        :param add_dy: 单位mil 测点间距y
        :param mode: double|single
        :param place:'up|mid|down' 预留拓展 bot
        :param add_pol: 物件极性
        :param atype: neg|pad neg为圆pad与方pad组合（例测试pad与接地pad），pad为仅添加圆pad（例钻孔，挡点）
        :return:
        """
        if mode == 'double':
            # 差分每组四个孔
            # 增加测点pad
            if atype == 'pad':
                sym_r = 'r%s' % sym_size
                GEN.ADD_PAD(start_x0, start_y0, sym_r, pol=add_pol, nx=add_nx, ny=add_ny, dx=add_dx, dy=add_dy)
            elif atype == 'neg':
                sym_s = 's%s' % sym_size
                sym_r = 'r%s' % sym_size
                start_x1 = start_x0 + add_dx * 0.001
                if place == 'up':
                    start_y1 = start_y0 + add_dx * 0.001
                    GEN.ADD_PAD(start_x0, start_y0, sym_s, pol=add_pol, nx=add_nx, ny=add_ny/2, dx=add_dx, dy=add_dy)
                    GEN.ADD_PAD(start_x0, start_y1, sym_r, pol=add_pol, nx=add_nx, ny=add_ny/2, dx=add_dx, dy=add_dy)
                elif place == 'mid':
                    GEN.ADD_PAD(start_x0, start_y0, sym_s, pol=add_pol, nx=add_nx/2, ny=add_ny, dx=add_dx * 2, dy=add_dy)
                    GEN.ADD_PAD(start_x1, start_y0, sym_r, pol=add_pol, nx=add_nx/2, ny=add_ny, dx=add_dx * 2, dy=add_dy)
                else:  # down
                    start_y1 = start_y0 + add_dx * 0.001
                    GEN.ADD_PAD(start_x0, start_y0, sym_r, pol=add_pol, nx=add_nx, ny=add_ny/2, dx=add_dx, dy=add_dy)
                    GEN.ADD_PAD(start_x0, start_y1, sym_s, pol=add_pol, nx=add_nx, ny=add_ny/2, dx=add_dx, dy=add_dy)

        elif mode == 'single':
            # 单线每组两个孔，上圆孔，下方孔
            # 增加测点pad
            if atype == 'pad':
                sym_r = 'r%s' % sym_size
                GEN.ADD_PAD(start_x0, start_y0, sym_r, pol=add_pol, nx=add_nx, ny=add_ny, dx=add_dx, dy=add_dy)
            elif atype == 'neg':
                sym_s = 's%s' % sym_size
                sym_r = 'r%s' % sym_size
                start_y1 = start_y0 + add_dy * 0.001
                if place in ['up', 'mid']:
                    GEN.ADD_PAD(start_x0, start_y0, sym_s, pol=add_pol, nx=add_nx, ny=add_ny / 2, dx=add_dx, dy=add_dy)
                    GEN.ADD_PAD(start_x0, start_y1, sym_r, pol=add_pol, nx=add_nx, ny=add_ny / 2, dx=add_dx, dy=add_dy)
                else:
                    GEN.ADD_PAD(start_x0, start_y1, sym_s, pol=add_pol, nx=add_nx, ny=add_ny / 2, dx=add_dx, dy=add_dy)
                    GEN.ADD_PAD(start_x0, start_y0, sym_r, pol=add_pol, nx=add_nx, ny=add_ny / 2, dx=add_dx, dy=add_dy)

    def Add_dingwei_pad(self, start_x0, start_y0, sym_size, coupon_length, adnum=2, type='pad', add_attr='no'):
        """
        增加定位pad，包含孔，套铜
        :param start_x0:
        :param start_y0:
        :param sym_size: 英制symbol大小
        :param coupon_length:
        :param adnum:
        :param type:
        :param add_attr:
        :return:
        """
        add_pol = None
        if type == 'pad':
            add_pol = 'positive'
        elif type == 'neg':
            add_pol = 'negative'
        GEN.COM(
            "add_pad, attributes=%s, x=%s, y=%s, symbol=r%s, polarity=%s, angle=0, mirror=no, nx=1,"
            "ny=1, dx=0, dy=0, xscale=1, yscale=1" % (add_attr, start_x0, start_y0, sym_size, add_pol))
        if adnum == 2:
            GEN.COM(
                "add_pad, attributes=%s, x=%s, y=%s, symbol=r%s, polarity=%s, angle=0, mirror=no, nx=1,"
                "ny=1, dx=0, dy=0, xscale=1, yscale=1" % (
                    add_attr, coupon_length - start_x0, start_y0, sym_size, add_pol))

    def add_jx_line(self, start_x0, start_y0, line_len, line_width, addnum=4, ad_mode=90):
        """
         添加交叉线
        :param start_x0: 交叉线中心点坐标
        :param start_y0:
        :param line_len: 线长
        :param line_width: 线宽
        :param addnum: 添加数量 20200426更改，增加此参数，为了控制左下交叉线的添加与否
        :param ad_mode: 45|90 45 为'X'形交叉线交叉线 90为'+'交叉线
        :return:
        """
        GEN.COM('cur_atr_reset')
        GEN.COM('cur_atr_set, attribute=.string, text=jx_line')
        if ad_mode == 45:
            start_x1s = start_x0 - 0.707 * 0.5 * line_len * 0.001
            start_x1e = start_x0 + 0.707 * 0.5 * line_len * 0.001
            start_y1s = start_y0 - 0.707 * 0.5 * line_len * 0.001
            start_y1e = start_y0 + 0.707 * 0.5 * line_len * 0.001

            GEN.COM('add_line, attributes=yes, xs=%s, ys=%s, xe=%s, ye=%s, symbol=r%s, polarity=positive,'
                    ' bus_num_lines=0, bus_dist_by=pitch, bus_distance=0, bus_reference=left' % (
                        start_x1s, start_y1e, start_x0, start_y0, line_width))
            GEN.COM('add_line, attributes=yes, xs=%s, ys=%s, xe=%s, ye=%s, symbol=r%s, polarity=positive,'
                    ' bus_num_lines=0, bus_dist_by=pitch, bus_distance=0, bus_reference=left' % (
                        start_x0, start_y0, start_x1e, start_y1s, line_width))
            if addnum == 3:
                pass
            else:
                GEN.COM('add_line, attributes=yes, xs=%s, ys=%s, xe=%s, ye=%s, symbol=r%s, polarity=positive,'
                        ' bus_num_lines=0, bus_dist_by=pitch, bus_distance=0, bus_reference=left' % (
                            start_x1s, start_y1s, start_x0, start_y0, line_width))
            GEN.COM('add_line, attributes=yes, xs=%s, ys=%s, xe=%s, ye=%s, symbol=r%s, polarity=positive,'
                    ' bus_num_lines=0, bus_dist_by=pitch, bus_distance=0, bus_reference=left' % (
                        start_x0, start_y0, start_x1e, start_y1e, line_width))
        else:
            start_x1s = start_x0 - 0.5 * line_len * 0.001
            start_x1e = start_x0 + 0.5 * line_len * 0.001
            start_y1s = start_y0 - 0.5 * line_len * 0.001
            start_y1e = start_y0 + 0.5 * line_len * 0.001

            GEN.COM('add_line, attributes=yes, xs=%s, ys=%s, xe=%s, ye=%s, symbol=r%s, polarity=positive,'
                    ' bus_num_lines=0, bus_dist_by=pitch, bus_distance=0, bus_reference=left' % (
                        start_x1s, start_y0, start_x0, start_y0, line_width))
            GEN.COM('add_line, attributes=yes, xs=%s, ys=%s, xe=%s, ye=%s, symbol=r%s, polarity=positive,'
                    ' bus_num_lines=0, bus_dist_by=pitch, bus_distance=0, bus_reference=left' % (
                        start_x1e, start_y0, start_x0, start_y0,  line_width))
            if addnum == 3:
                pass
            else:
                GEN.COM('add_line, attributes=yes, xs=%s, ys=%s, xe=%s, ye=%s, symbol=r%s, polarity=positive,'
                        ' bus_num_lines=0, bus_dist_by=pitch, bus_distance=0, bus_reference=left' % (
                    start_x0, start_y1s, start_x0, start_y0, line_width))
            GEN.COM('add_line, attributes=yes, xs=%s, ys=%s, xe=%s, ye=%s, symbol=r%s, polarity=positive,'
                    ' bus_num_lines=0, bus_dist_by=pitch, bus_distance=0, bus_reference=left' % (
                        start_x0, start_y1e, start_x0, start_y0,line_width))
        GEN.COM('cur_atr_reset')

    def add_two_imp_line(self, start_x0, start_y0, line1_wid, line1_spc, cedian_spc_x, cedian_spc_y, cedian_wid,
                         min_p2line, imp_line_length, arc_d, type='posline', spctocu=20, add_locate='up',
                         add_attr='no', ohm="", orig_width="", orig_spc="", orig_spc2cu="", neg_attr_text=""):
        """
        :param start_x0: 测试点X
        :param start_y0: 下测试点中心Y
        :param line1_wid: 线宽
        :param line1_spc:
        :param cedian_spc_x:
        :param cedian_spc_y:
        :param cedian_wid:
        :param min_p2line:
        :param imp_line_length:
        :param arc_d:
        :param type: negline 信号层套铜线 |midneg 中间层套铜线|maskline开窗阻抗线
        :param spctocu: 线到铜距离
        :param add_locate: up|mid|down 走线位置
        :param add_attr: yes|no 是否增加属性
        :return:
        """

        if type == 'negline':
            add_pol = 'negative'
            line2_wid = line1_wid + spctocu * 2
            line3_wid = line1_spc
        elif type == 'midneg':
            # 2020.06.12 增加中间层套铜距离
            add_pol = 'negative'
            line2_wid = line1_wid + spctocu * 2 + 10
            line3_wid = line1_spc
        elif type == 'maskline':
            # === 2021.11.19新增 用于开窗阻抗线 ===
            add_pol = 'positive'
            line2_wid = line1_wid + spctocu * 2
            line3_wid = line1_spc
        else:
            add_pol = 'positive'
            line2_wid = line1_wid
        fir_line_dx = (cedian_spc_x - line1_wid - line1_spc) * 0.5 * 0.001
        fir_line_dy = (cedian_spc_y - line1_wid - line1_spc) * 0.5 * 0.001
        if add_attr == 'yes':
            GEN.COM('cur_atr_reset')
            GEN.COM('cur_atr_set, attribute =.imp_line')
            GEN.COM('cur_atr_set, attribute =.imp_info, text = differential')
            GEN.COM('cur_atr_set, attribute =.string, text ={0}_{1}_{2}_{3}'.format(orig_width, orig_spc,orig_spc2cu, ohm))

        if neg_attr_text:
            add_attr = "yes"
            GEN.COM('cur_atr_reset')
            GEN.COM('cur_atr_set, attribute =.string, text ='+neg_attr_text)

        if add_locate == 'up':
            start_x0_w = start_x0 - cedian_spc_x * 0.001
            start_x1_w = start_x0_w + fir_line_dx
            start_x2 = start_x0 + fir_line_dx
            start_x3 = start_x0 + cedian_spc_x * 0.001 - fir_line_dx
            start_x4 = start_x3 + imp_line_length * 0.001

            start_y3 = start_y0 + cedian_spc_y * 0.001
            start_y4 = start_y3 + (cedian_wid * 0.5 + min_p2line + line1_wid * 0.5) * 0.001
            start_y5 = start_y4 + (line1_spc + line1_wid) * 0.001
            # ==左w差分第1根线--
            GEN.ADD_LINE(start_x0_w, start_y3, start_x1_w, start_y5, 'r' + str(line2_wid), pol=add_pol, attr=add_attr)
            # --右差分第1根线--
            GEN.ADD_LINE(start_x0, start_y3, start_x2, start_y4, 'r' + str(line2_wid), pol=add_pol, attr=add_attr)
            # --左差分第2根线--
            GEN.ADD_LINE(start_x1_w, start_y5, start_x4, start_y5, 'r' + str(line2_wid), pol=add_pol, attr=add_attr)
            # --右差分第2根线--
            GEN.ADD_LINE(start_x2, start_y4, start_x4, start_y4, 'r' + str(line2_wid), pol=add_pol, attr=add_attr)
            # 第三根弧 增加负性套铜的差分中间走线
            if type == 'negline':
                neg_y45n = (start_y4 + start_y5) * 0.5
                GEN.ADD_LINE(start_x2, neg_y45n, start_x4, neg_y45n, 'r' + str(line3_wid), pol=add_pol,
                             attr=add_attr)
        elif add_locate == 'mid':
            start_x1 = start_x0 + fir_line_dx * 0.25
            start_x3 = start_x0 + cedian_spc_x * 0.001 - fir_line_dx
            start_x4 = start_x3 + imp_line_length * 0.001
            start_y1 = start_y0 + fir_line_dy
            start_y2 = start_y0 + cedian_spc_y * 0.001 - fir_line_dy
            start_y3 = start_y0 + cedian_spc_y * 0.001
            # --下差分第1根线--
            GEN.ADD_LINE(start_x0, start_y0, start_x1, start_y1, 'r' + str(line2_wid), pol=add_pol, attr=add_attr)
            # --上差分第2根线--
            GEN.ADD_LINE(start_x0, start_y3, start_x1, start_y2, 'r' + str(line2_wid), pol=add_pol, attr=add_attr)
            # --上差分第1根线--
            GEN.ADD_LINE(start_x1, start_y2, start_x4, start_y2, 'r' + str(line2_wid), pol=add_pol, attr=add_attr)
            # --下差分第2根线--
            GEN.ADD_LINE(start_x1, start_y1, start_x4, start_y1, 'r' + str(line2_wid), pol=add_pol, attr=add_attr)
            # 第二根线 增加负性套铜的差分中间走线
            if type == 'negline':
                neg_y12n = (start_y1 + start_y2) * 0.5
                GEN.ADD_LINE(start_x1, neg_y12n, start_x4, neg_y12n, 'r%s' % line3_wid, pol=add_pol, attr=add_attr)

        elif add_locate == 'down':
            start_x0_w = start_x0 - cedian_spc_x * 0.001
            start_x1_w = start_x0_w + fir_line_dx
            start_x3 = start_x0 + fir_line_dx
            start_x4 = start_x3 + imp_line_length * 0.001
            start_y3 = start_y0
            start_y4 = start_y3 - (cedian_wid * 0.5 + min_p2line + line1_wid * 0.5) * 0.001
            start_y5 = start_y4 - (line1_spc + line1_wid) * 0.001

            # ==左w差分第1根线--
            GEN.ADD_LINE(start_x0_w, start_y3, start_x1_w, start_y5, 'r' + str(line2_wid), pol=add_pol, attr=add_attr)
            # --右差分第1根线--
            GEN.ADD_LINE(start_x0, start_y3, start_x3, start_y4, 'r' + str(line2_wid), pol=add_pol, attr=add_attr)
            # --左差分第2根线--
            GEN.ADD_LINE(start_x1_w, start_y5, start_x4, start_y5, 'r' + str(line2_wid), pol=add_pol, attr=add_attr)
            # --右差分第2根线--
            GEN.ADD_LINE(start_x3, start_y4, start_x4, start_y4, 'r' + str(line2_wid), pol=add_pol, attr=add_attr)
            # 第三根弧 增加负性套铜的差分中间走线
            if type == 'negline':
                neg_y45n = (start_y4 + start_y5) * 0.5
                GEN.ADD_LINE(start_x3, neg_y45n, start_x4, neg_y45n, 'r' + str(line3_wid), pol=add_pol, attr=add_attr)

        GEN.COM('cur_atr_reset')

    def add_sig_imp_line(self, start_x0, start_y0, line1_wid, cedian_spc_x, cedian_spc_y, cedian_wid, min_p2line,
                         imp_line_length, type='posline', spctocu=20, add_locate='up', add_attr='no', ohm="",
                         orig_width="", orig_spc="", orig_spc2cu="", neg_attr_text=""):
        """
        单线阻抗程序
        :param start_x0:
        :param start_y0:
        :param line1_wid:
        :param cedian_spc_x:
        :param cedian_spc_y:
        :param cedian_wid:
        :param min_p2line:
        :param imp_line_length:
        :param type:
        :param spctocu:
        :param add_locate:
        :param add_attr:
        :return: 添加的线宽
        """
        # GEN.PAUSE("%s %s" % (type,spctocu))
        if type == 'negline':
            add_pol = 'negative'
            line2_wid = line1_wid + spctocu * 2
        elif type == 'midneg':
            # 2020.06.12 增加中间层套铜距离
            add_pol = 'negative'
            line2_wid = line1_wid + spctocu * 2 + 10
        elif type == 'maskline':
            add_pol = 'positive'
            line2_wid = line1_wid + spctocu * 2
        else:
            add_pol = 'positive'
            line2_wid = line1_wid

        start_y3 = start_y0 + cedian_spc_y * 0.001
        if add_locate == 'down':
            start_y3 = start_y0
            fir_line_dx = cedian_spc_x * 0.5 * 0.001 + (
                    (min_p2line + line1_wid * 0.5 + cedian_wid * 0.5) * cedian_spc_x * 0.5 * 0.001) / cedian_spc_y
            fir_line_dy = (min_p2line + line1_wid * 0.5 + cedian_wid * 0.5)  * -0.001
        elif add_locate == 'up':
            fir_line_dx = (min_p2line + line1_wid * 0.5 + cedian_wid * 0.5) * 0.001
            fir_line_dy = (min_p2line + line1_wid * 0.5 + cedian_wid * 0.5) * 0.001
        elif add_locate == 'mid':
            fir_line_dx = (min_p2line + line1_wid * 0.5 + cedian_wid * 0.5) * 0.001
            fir_line_dy = cedian_spc_y * 0.5 * -0.001
        elif add_locate == 'bot':
            start_y3 = start_y0
            # 增加第四根阻抗线走法，需在原有的基础上再向下走70mil ,dx算法解析，使用tan角的值相同
            fir_line_dx = cedian_spc_x * 0.5 * 0.001 + (
                    (min_p2line + line1_wid * 0.5 + cedian_wid + 70) * cedian_spc_x * 0.5 * 0.001) / cedian_spc_y
            fir_line_dy = (min_p2line + line1_wid * 0.5 + cedian_wid * 0.5 + 70) * -0.001

        start_x1 = start_x0 + fir_line_dx
        start_y1 = start_y3 + fir_line_dy
        start_x2 = start_x1 + imp_line_length * 0.001
        if add_attr == 'yes':
            GEN.COM('cur_atr_reset')
            GEN.COM('cur_atr_set, attribute=.imp_line')
            GEN.COM('cur_atr_set, attribute=.imp_info, text=single-ended')            
            GEN.COM('cur_atr_set, attribute =.string, text ={0}_{1}_{2}_{3}'.format(orig_width, orig_spc,orig_spc2cu, ohm))

        if neg_attr_text:
            add_attr = "yes"
            GEN.COM('cur_atr_reset')
            GEN.COM('cur_atr_set, attribute =.string, text ='+neg_attr_text)

        # --第一根线--
        GEN.ADD_LINE(start_x0, start_y3, start_x1, start_y1, 'r' + str(line2_wid), pol=add_pol, attr=add_attr)
        # --第二根线--
        GEN.ADD_LINE(start_x1, start_y1, start_x2, start_y1, 'r' + str(line2_wid), pol=add_pol, attr=add_attr)
        GEN.COM('cur_atr_reset')

        return line2_wid

    def split_combineCoupon(self):
        """
        合并多个coupon为一个icg
        :return:
        """
        # GEN.PAUSE('XXXXXXXX')
        coupon_area = self.coupon_area

        combine_warn_text = []
        # === V5.1 删除Coupon_LLC step
        if sysstr == "Linux":
            # === Windows下不支持大写的Step
            if GEN.STEP_EXISTS(job=self.job_name, step='Coupon_LLC') == 'yes':
                GEN.DELETE_ENTITY('step', 'Coupon_LLC', job=self.job_name)

        # === 先获取panel中的panel Repeat ===
        g_info = GEN.DO_INFO("-t step -e %s/panel -d REPEAT" % self.job_name,units='inch')

        use_list = []
        for index, g_step in enumerate(g_info['gREPEATstep']):
            if re.match('icg', g_step):
                tmp_dict = dict(zip(g_info.keys(), map(lambda x:g_info[x][index], g_info.keys())))
                use_list.append(tmp_dict)
        print use_list
        # TODO V5.3 测试阶段，暂时退出


        for coupon_tail in coupon_area:
            current_array_coupon = [self.icgCamData[k] for k in coupon_area[coupon_tail]['numlist']]
            allicg = 'icg%s' % coupon_tail
            if len(coupon_area) == 1:
                # === 仅一个区域时，使用标准命名 ===
                allicg = 'icg'
            if self.mode=='dy':
                allicg = allicg + '-d'
            GEN.VOF()
            GEN.DELETE_ENTITY('step', allicg, job=self.job_name)
            GEN.VON()

            GEN.COM(
                'create_entity,job=%s,is_fw=no,type=step,name=%s,db=,fw_type=form' % (self.job_name, allicg))
            GEN.OPEN_STEP(allicg, self.job_name)
            GEN.CHANGE_UNITS('inch')
            # 取coupon合拼变量，进行coupon排布，使用inplan拼版数据。
            xNumMax = coupon_area[coupon_tail]['h_num']
            yNumMax = coupon_area[coupon_tail]['v_num']

            zkWidth = max([float(v['icgHeight']) for v in current_array_coupon])
            zkLength = coupon_area[coupon_tail]['each_coupon_length'] + self.extra_strech_coupon_length * 1000
            # for zkIndex in range (1, self.coupon_num + 1):
            coupon_id_list = coupon_area[coupon_tail]['numlist']
            
            has_steps = False

            for place_i in range(1, len(coupon_id_list) + 1):
                # zkIndex = coupon_area[coupon_tail]['numlist'][zkIndex]
                couponName = current_array_coupon[place_i - 1]['icgName']
                if self.mode == 'dy':
                    couponName += '-d'
                    
                if couponName in self.delete_icg_name:
                    continue

                if couponName not in self.exists_icg_name:
                    continue

                has_steps = True
                corX = (place_i - 1) % xNumMax * zkLength * 0.001 + 0.45
                corY = (place_i - 1) / xNumMax * zkWidth * 0.001
                GEN.COM('sr_tab_add, line=0, step=%s, x=%s, y=%s, nx=1, ny=1' % (couponName, corX, corY))
            
            #有多个阻抗时 某些低压阻抗会没有阻抗线在其内 这里要删除掉20240827 by lyh            
            if not has_steps:
                for place_i in range(len(coupon_area[coupon_tail]['numlist'])):
                    couponName = current_array_coupon[place_i]['icgName']
                    if self.mode == 'dy':
                        couponName = couponName + '-d'
                    GEN.VOF()
                    GEN.DELETE_ENTITY('step', couponName, job=self.job_name)
                    GEN.VON()

                GEN.VOF()
                GEN.DELETE_ENTITY('step', allicg, job=self.job_name)
                GEN.VON()
                continue
                
            GEN.COM('profile_rect, x1=0, y1=0, x2=%s, y2=%s' % (
                zkLength * 0.001 * xNumMax + 0.9, zkWidth * yNumMax * 0.001))
            # 所有信号层铺铜                
            GEN.CLEAR_LAYER()
            GEN.COM("affected_filter,filter=(type=signal&context=board)")
            self.Add_put_surface(dis_to_p_x=0.01, dis_to_p_y=0.01)
            self.Add_dingwei_pad(0.225, zkWidth * yNumMax * 0.001 * 0.5, self.dingwei_wid + 20,
                                 zkLength * 0.001 * xNumMax + 0.9, type='neg')         
            # === 报废coupon ===
            for zkIndex in range(1, len(coupon_id_list) + 1):
                GEN.CLEAR_LAYER()
                GEN.COM("affected_filter,filter=(type=signal&context=board)")
                if (zkIndex - 1) % xNumMax == 0:
                    corX = 0.1
                    bf_angle = 90
                if xNumMax > 2 and (zkIndex - 1) % xNumMax == 1:
                    corX = 0.360
                    bf_angle = 90
                elif xNumMax == 2 and (zkIndex - 1) % xNumMax == 1:
                    corX = zkLength * 0.001 * xNumMax + 0.9 - 0.1
                    bf_angle = 270
                elif xNumMax == 4 and (zkIndex - 1) % xNumMax == 2:
                    corX = zkLength * 0.001 * xNumMax + 0.9 - 0.360
                    bf_angle = 270
                elif xNumMax > 2 and (zkIndex - 1) % xNumMax == xNumMax - 1:
                    corX = zkLength * 0.001 * xNumMax + 0.9 - 0.1
                    bf_angle = 270
                corY = (zkIndex - 1) / xNumMax * zkWidth * 0.001 + zkWidth * 0.001 * 0.5
                GEN.ADD_PAD(corX, corY, 'bf-icg-lay', pol='negative', angle=bf_angle)
                GEN.CLEAR_LAYER()
                GEN.COM("affected_filter, filter=(type=solder_mask & context=board & side=top | bottom)")
                GEN.ADD_PAD(corX, corY, 'bf-icg-sm', pol='positive', angle=bf_angle)
                GEN.CLEAR_LAYER()

            GEN.CLEAR_LAYER()
            # 添加定位孔，防焊开窗，挡点
            GEN.AFFECTED_LAYER('drl', 'yes')
            GEN.COM('cur_atr_reset')
            GEN.COM('cur_atr_set, attribute =.drill, option=non_plated')
            self.Add_dingwei_pad(0.225, zkWidth * yNumMax * 0.001 * 0.5, self.dingwei_wid,
                                 zkLength * 0.001 * xNumMax + 0.9, add_attr='yes')
            GEN.COM('cur_atr_reset')

            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER('md1', 'yes')
            GEN.AFFECTED_LAYER('md2', 'yes')
            # === V4.0.1 修改NPTH孔挡点与规范相同 ===
            if self.dingwei_wid > 39.37:
                md_size = self.dingwei_wid - 8
            else:
                md_size = self.dingwei_wid + 6
            self.Add_dingwei_pad(0.225, zkWidth * yNumMax * 0.001 * 0.5, md_size,
                                 zkLength * 0.001 * xNumMax + 0.9)
            GEN.CLEAR_LAYER()
            GEN.COM("affected_filter, filter=(type=solder_mask & context=board & side=top | bottom)")
            self.Add_dingwei_pad(0.225, zkWidth * yNumMax * 0.001 * 0.5, self.dingwei_wid + 10,
                                 zkLength * 0.001 * xNumMax + 0.9)
            GEN.CLEAR_LAYER()

            # === V3.3 在top面信号层增加料号名 V3.4 更改为加在阻抗条内
            # GEN.CLEAR_LAYER ()
            # GEN.COM ("affected_filter, filter=(type=signal & context=board & side=top)")
            # GEN.ADD_TEXT('0.04', '0.03', '$$JOB', '0.03', '0.03', w_factor='0.4166666567', polarity='negative')
            # GEN.CLEAR_LAYER ()

            GEN.COM('sredit_reduce_nesting, mode=one_highest')
            GEN.AFFECTED_LAYER('ww', 'yes')
            GEN.SEL_DELETE()
            GEN.COM('profile_to_rout,layer=ww,width=5')
            GEN.AFFECTED_LAYER('ww', 'no')

            # === V3.7.4 选化层制作
            GEN.VOF()
            GEN.AFFECTED_LAYER('sgt-c', 'yes')
            GEN.AFFECTED_LAYER('sgt-s', 'yes')
            #周涌通知增加此两层 20240801 by lyh
            GEN.AFFECTED_LAYER('etch-c', 'yes')
            GEN.AFFECTED_LAYER('etch-s', 'yes')
            GEN.VON()
            GEN.COM('get_affect_layer')
            layers = GEN.COMANS.split()
            if len(layers) > 0:
                self.Add_put_surface(dis_to_p_x=-0.01, dis_to_p_y=-0.01)
                # === V4.0.2 选化层的NPTH孔一板都大于1.0，不套开选化层铜皮
                # self.Add_dingwei_pad(0.225, zkWidth * yNumMax * 0.001 * 0.5, self.dingwei_wid + 20,
                #                      zkLength * 0.001 * xNumMax + 0.9, type='neg')
            GEN.CLEAR_LAYER()

            # === 2021.01.19 增加外层字样检测，字体碰 pad line ===

            GEN.COM("affected_filter, filter=(type=signal & context=board & side=top)")
            GEN.FILTER_RESET()
            GEN.COM('filter_set, filter_name=popup, update_popup=no, feat_types=text')
            GEN.FILTER_SELECT()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.FILTER_RESET()
                GEN.COM('filter_set, filter_name=popup, update_popup=no, feat_types=line\;pad\;arc')
                GEN.COM('sel_ref_feat, layers =, use=select, mode=touch, pads_as=shape, '
                        'f_types=line\;pad\;arc, polarity=positive\;negative, include_syms =, exclude_syms =')
                if int(GEN.GET_SELECT_COUNT()) != 0:

                    combine_warn_text.append('检测到：添加字样与Line Pad有相交，请注意避让。|\n')

            GEN.CLEAR_LAYER()
            GEN.FILTER_RESET()

            #翟鸣 通知低压区阻抗条上加个D字样 2024831
            if self.mode == 'dy':
                GEN.AFFECTED_LAYER('l1', 'yes')
                GEN.COM("add_text,type=string,polarity=negative,x=0.339835,y=0.194356,text=D,"
                        "fontname=standard,height=0.07873996,width=normal,"
                        "mirror=no,angle=0,direction=cw,w_factor=0.98425198")
                GEN.CLEAR_LAYER()
                GEN.FILTER_RESET()            
            # for zkIndex in range (1, self.coupon_num + 1):
            #     couponName = self.icgCamData[zkIndex]['icgName']
            #     GEN.DELETE_ENTITY ('step', couponName, job=self.job_name)

            for place_i in range(len(coupon_area[coupon_tail]['numlist'])):
                couponName = current_array_coupon[place_i]['icgName']
                if self.mode == 'dy':
                    couponName = couponName + '-d'
                GEN.VOF()
                GEN.DELETE_ENTITY('step', couponName, job=self.job_name)
                GEN.VON()

            # === V3.7.5 处理阻抗条中细丝，使用整体化缩小加大方案 ===
            get_add_neg_layers = self.remove_negative_surface(allicg)
            if len(get_add_neg_layers) > 0:
                combine_warn_text.append(u'检查项：Step:%s层别%s进行了细丝修补，负片属性.string=shave_surface,请检查。|\n'
                                         % (allicg, ','.join(get_add_neg_layers)))

            # === 如果分组数据中有信息，且角度均一，使用数据中值，进行预填写 Song 2020.05.15
            # === 使用MI数据，进行阻抗分组获取 ===

            xICGCor = min(coupon_area[coupon_tail]['xcorlist'])
            yICGCor = min(coupon_area[coupon_tail]['ycorlist'])
            addICGangle = 0
            ang_list = coupon_area[coupon_tail]['ang_list']
            if len(ang_list) == 1:
                addICGangle = ang_list[0]
                # === 以下角度，使用顺时针旋转(Incam)
                if addICGangle == 270:
                    xICGCor = max(coupon_area[coupon_tail]['xcorlist'])
                    yICGCor = min(coupon_area[coupon_tail]['ycorlist'])
                elif addICGangle == 180:
                    xICGCor = max(coupon_area[coupon_tail]['xcorlist'])
                    yICGCor = max(coupon_area[coupon_tail]['ycorlist'])
                elif addICGangle == 90:
                    xICGCor = min(coupon_area[coupon_tail]['xcorlist'])
                    yICGCor = max(coupon_area[coupon_tail]['ycorlist'])


            # 检测接地pad是否跟大铜皮相连 20230620 by lyh
            os.system(
                "python /incam/server/site_data/scripts/lyh/auto_sh_hdi_check_rules.py check_coupon_netpoint_pad_connetion no yes {0}".format(allicg))
    
            # 阻抗条铺铜修改 20240516 by lyh
            if self.mode == 'dy':
                os.system("python /incam/server/site_data/scripts/ynh/no_gui/change_icg_copper_pattern.py show_manual_copper_usage {0}".format(allicg))
                
            # 打开panel Step 单位为inch
            if GEN.STEP_EXISTS(job=self.job_name, step='panel') == 'yes':
                if self.mode == 'dy':
                    continue
                
                GEN.OPEN_STEP('panel', job=self.job_name)
                GEN.CHANGE_UNITS('inch')
                # === 以下角度，使用逆时针添加（如90），InCAM中显示的角度为顺时针（如270），添加icg无异常
                GEN.COM('sr_tab_add, line=0, step=%s, x=%s, y=%s, nx=1, ny=1, angle=%s'
                        % (allicg, xICGCor, yICGCor, addICGangle))
                print use_list
                if len(use_list) > 0:
                    check_ok = False
                    step_new_same = False
                    for u_l in use_list:
                        if u_l['gREPEATstep'] == allicg:
                            step_new_same = True
                            if Decimal(str(u_l['gREPEATxa'])) == Decimal(str(xICGCor)) and Decimal(str(u_l['gREPEATya'])) == Decimal(str(yICGCor)):
                                check_ok = True
                            if step_new_same is True and check_ok is False:
                                combine_warn_text.append('原有Step:%s 存在于Panel中，但拼入位置变动.\n前:X:%s Y:%s 后:X:%s Y:%s。|\n' % (allicg,  u_l['gREPEATxa'], u_l['gREPEATya'],xICGCor,yICGCor,))

                if len(ang_list) != 1:
                    combine_warn_text.append('阻抗条%s自动拼入panel，由于信息不完整，请检查。|\n' % allicg)
            else:
                combine_warn_text.append('无panel，不拼入%s.|\n' % allicg)
        if len(combine_warn_text) > 0:
            return combine_warn_text
        else:
            return None

    def remove_negative_surface(self, icg_step):
        """
        用于去除阻抗条中的负性，并去除细丝类 | 增加去掉影响线路负片的交叉线
        :return:
        """
        add_neg_layers = []
        for cur_layer in self.sig_layers:
            # ====处理交叉线 ====
            get_result = self.deal_jx_line(cur_layer)
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER(cur_layer, 'yes')
            GEN.FILTER_RESET()
            GEN.FILTER_SET_TYP('line\;pad\;surface\;arc')
            GEN.FILTER_SET_POL('negative')
            GEN.FILTER_SELECT()
            neg_num = int(GEN.GET_SELECT_COUNT())
            if neg_num == 0:
                GEN.CLEAR_LAYER()
                continue
            GEN.FILTER_RESET()
            GEN.FILTER_SET_TYP('surface')
            GEN.FILTER_SELECT()
            sum_num = int(GEN.GET_SELECT_COUNT())
            if sum_num == neg_num:
                GEN.CLEAR_LAYER()
                continue
            tmp_layer = '__neg_%s__' % cur_layer
            before_resize = '__befor_%s__' % cur_layer
            GEN.DELETE_LAYER(tmp_layer)
            GEN.DELETE_LAYER(before_resize)

            GEN.SEL_COPY(tmp_layer)
            GEN.AFFECTED_LAYER(cur_layer, 'no')
            GEN.AFFECTED_LAYER(tmp_layer, 'yes')
            GEN.SEL_COPY(before_resize)
            GEN.AFFECTED_LAYER(before_resize, 'yes')
            GEN.SEL_CONTOURIZE(accuracy=0, clean_hole_size=0, breakSurface='yes')
            GEN.AFFECTED_LAYER(before_resize, 'no')
            GEN.SEL_RESIZE(-5)
            GEN.SEL_RESIZE(5)
            GEN.SEL_MOVE(before_resize, invert='yes', size=1)
            GEN.AFFECTED_LAYER(tmp_layer, 'no')
            GEN.AFFECTED_LAYER(before_resize, 'yes')
            GEN.SEL_CONTOURIZE(accuracy=0, clean_hole_size=3, breakSurface='yes')
            GEN.VOF()
            GEN.COM('sel_decompose,overlap=yes')
            GEN.VON()
            # GEN.COM('sel_contourize,accuracy=0,break_to_islands=yes,clean_hole_size=10,clean_hole_mode=x_and_y')
            GEN.COM('sel_clean_surface,accuracy=0,clean_size=10,clean_mode=x_and_y,max_fold_len=10')
            GEN.SEL_REVERSE()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.COM('cur_atr_reset')
                GEN.COM('cur_atr_set, attribute=.string, text=shave_surface')
                GEN.COM('sel_change_atr,mode=add')
                GEN.COM('cur_atr_reset')
                add_neg_layers.append(cur_layer)
                GEN.SEL_MOVE(cur_layer, invert='yes', size=1)
                GEN.AFFECTED_LAYER(before_resize, 'no')
            GEN.FILTER_RESET()
            GEN.DELETE_LAYER(tmp_layer)
            GEN.DELETE_LAYER(before_resize)
        return add_neg_layers

    def deal_jx_line(self, ip_layer):
        """
        处理交叉线超出阻抗负片的的情况
        :return:
        """
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(ip_layer, 'yes')
        tmp_layer = '__deal_jx_line__'
        GEN.DELETE_LAYER(tmp_layer)
        GEN.FILTER_RESET()
        GEN.FILTER_SET_TYP('line')
        GEN.FILTER_SET_INCLUDE_SYMS('r%s' % '15')
        GEN.FILTER_SET_POL('positive')
        GEN.FILTER_TEXT_ATTR('.string', 'jx_line')
        GEN.SEL_REF_FEAT(ip_layer, 'touch', pol='negative', f_type='line')
        if int(GEN.GET_SELECT_COUNT()) == 0:
            GEN.FILTER_RESET()
            GEN.CLEAR_LAYER()
            return True
        GEN.SEL_MOVE(tmp_layer)
        GEN.FILTER_RESET()
        GEN.FILTER_SET_TYP('line')
        GEN.FILTER_SET_POL('negative')
        GEN.FILTER_SELECT()
        if int(GEN.GET_SELECT_COUNT()) == 0:
            return False
        GEN.SEL_COPY(tmp_layer)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(tmp_layer, 'yes')
        GEN.SEL_CONTOURIZE(accuracy=0, clean_hole_size=0)  # 此处需设为0，包中依mm为单位
        GEN.SEL_MOVE(ip_layer)
        GEN.CLEAR_LAYER()
        GEN.FILTER_RESET()
        GEN.DELETE_LAYER(tmp_layer)
        return True

    def getdrillLayers(self):
        """
        获取埋孔钻带名称列表
        :return:
        """

        drill_layers = GEN.GET_ATTR_LAYER('drill')
        # print drill_layers
        drl_info = {}
        drl_info['drl_layer'] = []
        drl_info['min_pth'] = []
        drl_info['min_list'] = []
        hole_reg = re.compile(r'b[0-9]{1,2}-[0-9]{1,2}$')
        laser_reg = re.compile(r's[0-9]{1,2}-[0-9]{1,2}$')

        for item in drill_layers:
            msg_list = []
            if hole_reg.match(item) or laser_reg.match(item):
                getlist = GEN.DO_INFO("-t layer -e %s/%s/%s -d TOOL -p drill_size+type -o break_sr" %
                                      (self.job_name, self.set_step, item))
                if len(getlist['gTOOLdrill_size']) != 0:
                    # 只选pth孔
                    pth_tool = []
                    for i in range(len(getlist['gTOOLdrill_size'])):
                        if getlist['gTOOLtype'][i] in ['via', 'plated']:
                            pth_tool.append(getlist['gTOOLdrill_size'][i])
                    if len(pth_tool):
                        # 按孔径大小取最小值，而不是按str格式取最小值
                        mintool = min(pth_tool, key=lambda x: float(x))
                        if float(mintool) > 500:
                            drl_info['min_pth'].append('500')
                            drl_info['min_list'].append(mintool)
                        else:
                            min_pth = ''
                            if not item.startswith('s'):
                                try:
                                    int_min_tool = int(mintool)
                                except ValueError:
                                    msg_list.append(u"钻孔:%s非整数:" % mintool)
                                    int_min_tool = int(float(mintool))
                                for t_line in self.tool_size_rule:
                                    if int(t_line['tool_low']) < int_min_tool < int(t_line['tool_up']):
                                        min_pth = t_line['test_size']
                            else:
                                min_pth = mintool
                            drl_info['min_pth'].append(min_pth)
                            drl_info['min_list'].append(mintool)
                        drl_info['drl_layer'].append(item)
                    else:
                        mintool = ''
                else:
                    mintool = ''
            if len(msg_list) > 0:
                msg_box = msgBox()
                get_result = msg_box.question(self, '埋孔钻带：%s未补偿,继续吗' % item, u'%s' % '\n'.join(msg_list), QtGui.QMessageBox.No,QtGui.QMessageBox.Yes)
                if get_result == 0:
                    exit(0)
                elif get_result == 1:
                    pass

        return drl_info

# # # # --程序入口
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MainWindowShow()
    # 界面设置居中，改变linux时候不居中的情况
    screen = QtGui.QDesktopWidget().screenGeometry()
    size = myapp.geometry()
    myapp.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)
    myapp.show()
    app.exec_()
    sys.exit(0)


#  脱离teamc变量，使用界面数据生成所有 done
#
#
# 版本 V1.1.1
# 2020.03.02
# 更改Bug 共面特性更改为 特性共面
# 版本 V1.1.2
# 2020.03.06
# 周涌需求 Bug料号 968-076A1
# profile定义有差异
# 差分阻抗线的补偿 应为单边0.15

# 版本 V2.0
# 仅保留两侧定位孔，中间的定位孔去除
# 增加外层字touch负片或线路防呆
# 更改阻抗条长度，使用去除两边定位孔的计算方式
# 版本 V2.0.1
# 共面阻抗的值跑出来不正确，用错了字典中的线宽数据，修复此Bug
# 版本 V2.0.2
# 2020.03.14
# 作者：宋超
# 更改阻抗条的添加字样判断，改为当前层序号的判断，避免加于阻抗条外
# 更改添加字样的判断 text_y1 下移0.05，居中添加
# 增加阻抗线长判断
# 版本 V2.0.3
# 2020.03.14
# 作者：宋超
# 阻抗宽度较宽时，上下走线距离增加20 text_y1 下移0.075，（pad到线的距离20 更改为40）
#
# 版本 V2.0.4
# 2020.03.20
# 作者：宋超
# 1.10层板 L9->L8 时 L10层未套铜，L2->L3 L1层套铜，但是无pad
# 2.修改阻抗字样不对应问题

# 版本:V2.1
# 修改日期：2020.04.13~2020.04.26
# 作者：宋超
# 1.更改阻抗条逻辑，一次打开step
# ————>更改阻抗条主程序写法，从每条阻抗信息跑阻抗，更改为根据阻抗条跑跑阻抗，避免重复打开Step；
# 2.更改接地pad的交叉线添加方式，由2段线更改为4段线；
# 3.共面阻抗存在第三组线时，会有交叉线头伸出的情况；Bug料号：710-124
# ————>增加逻辑判断，当添加为中间走线的共面阻抗线时，判断是否有下方走线的阻抗线，有则不添加本层别的接地pad的左下角交叉线。
# 4.共面差分线套铜负片不够宽：Bug料号：318*435A1
# ————>增加差分线的线间套铜线，避免共面差分中间有铜丝；
# 5.更改特性阻抗的下路阻抗线添加方式，靠近接地pad添加，保证有护卫铜皮；Bug料号：A29-015
# 6.L1层存在三组线时，欧姆值标注会与第三组线相交；Bug料号：710-124
# —————>更改层别字样添加逻辑，避开外层阻抗走线；
#
# 版本：V2.2
# 2020.05.11
# 作者：宋超
# 1.修改dealWithStackUpData，增加Core+Core叠构支持
#
# 版本：V2.3
# 2020.05.12
# 作者：宋超
# 1.欧姆值如果为小数，保持为小数，周涌：519-972C1
# 2.当欧姆值超过两位时，缩小字体宽度0.03-->0.020
#
# 版本：V2.4
# 2020.05.15
# 作者：宋超
# 1.获取inplan中的拼版，自动拼入panel
# S94008GB168C1 拼第五个，坐标不能直接归类计算 由于第五根阻抗条拼在中间，
# S31804PN182A9
# 2.获取inplan中的序号，跑出序号层,测试，更新本机的Package，增加序号


# 版本：V2.5
# 2020.06.01
# 作者：宋超
# 更改界面增加间距管控值，更改类 sepByAttr 增加l2lspcControl
# 内层差分需补偿，更改内层补偿的ini文件，增加间距管控值，
# 外层补偿值更改，更改外层补偿的ini文件，增加层别相关补偿值，增加间距管控值
# 增加间距管控限制,颜色区分，
# 据薛工需求，
# 内层按照最小量产间距管控，
# 外层按照最小工作稿间距管控，
# 共面阻抗的情况按照线到铜皮3mil管控，定义全局变量
# 如果有做间距卡间距管控，则table中的字样使用差别颜色显示

# 版本：V2.6
# 2020.06.12
# 作者：宋超
# 1. 隔层参考的中间层大距离套铜整体10mil
# 1.1. 增加函数add_two_imp_line 中的midneg type 在现有线宽基础上加10mil
# 1.2. 增加函数add_sig_imp_line 中的midneg type 在现有线宽基础上加10mil
# 2.更改外层加测点pad，更改至本阻抗条最后，使用单独坐标计算方式，注意更改

# 版本：V2.7
# 2020.07.13
# 作者：宋超
# 1. 界面测试孔改为可输入三位小数；
# 2. 更改单位转换过程中造成的孔径偏差：525*BK6 2.3mm定位孔实际跑出2.229998mm

# 2020.07.15
# 作者：宋超
# 1.黎晨反馈H19002OF008A1无法跑阻抗，参考层为空，判断报NoneType，-->修改程序判断先后顺序，参考层为空条件前置

# 版本：V2.8
# 2020.07.21
# 作者：宋超
# 1. 更改界面布局
# 2. 增加B20客户跑阻抗条要求


# 版本：V2.9
# 2020.08.26
# 作者：宋超
# 1. 天珑阻抗条，板内无0.5mm钻孔时使用0.5mm孔径做测试孔 b20ArrayImpCoupon.py
# 2. 获取MI层别信息为大写时，导致匹配失效，增加此匹配项目

# 版本：V3.0
# 2020.08.28
# 作者：宋超
# 1. 更改中间层添加负片语句，避免信号层多次添加，影响共面的套铜

# 版本：V3.1.0
# self.appVer = '3.1.0'
# 开发开始日期：2020.09.09
# 作者：宋超
# http://192.168.2.120:82/zentao/story-view-1993.html
# 1.更改共面阻抗条的补偿，改为卡间距两线补偿；
# 2.增加内一层补偿

# 版本：V3.1.1
# self.appVer = '3.1.1'
# 开发开始日期：2020.09.11
# 作者：宋超
# 共面差分修正

# 版本：V3.1.2
# self.appVer = '3.1.2'
# 开发开始日期：2020.09.14
# 作者：宋超
# 差分距铜间距小于在2.5与补偿值之间的增加0.5倍的计算

# 版本：V3.1.3
# self.appVer = '3.1.3'
# 开发开始日期：2020.09.14
# 作者：宋超
# 差分距铜间距小于在2.5与补偿值之间的增加0.5倍的计算

# 版本：V3.1.4
# self.appVer = '3.1.4'
# 开发开始日期：2020.09.14
# 作者：宋超
# 增加特性共面的卡间距动补的开发

# 版本：V3.2
# self.appVer = '3.2'
# 开发开始日期：2020.12.01
# 作者：宋超
# 阻抗条跑出报废coupon 新建symbol bf-icg-lay bf-lay-sm
# 上线时更改更新日期


# 版本：V3.3
# 2020.12.24 上线日期： 2021.01.10
# Chao.Song
# 1.阻抗条加料号名；
# 2.特性的套铜大小。

# 版本：V3.4
# 2021.01.19
# Chao.Song
# 1.Top面text与线、pad相交检测；
# 2.HDI取消了w层设计，新增层别以drl为基准

# 版本：V3.5
# 2021.02.02
# Chao.Song
# 更改内一层判断逻辑，无镭射的才为内一

# 版本：V3.6
# 2021.03.03
# Chao.Song
# 1.增加层别无补偿信息的判断；
# 2.增加阻抗不同类型分至一组的判断；
# 3.增加InpLan阻抗条不连续的判断。

# 版本：V3.7
# 2021.03.05
# Chao.Song
# 1.更改内层，内一层，外层补偿部分；

# 版本：V3.7.1
# 2021.03.08
# Chao.Song
# 1.内层部分解读异议，更改动补部分为优先整体补偿，不符合间距要求时，单边侧补；

# 版本：V3.7.2
# 2021.03.10
# Chao.Song
# 1.不论内层外层次外层，凡是补偿后间距不足的均拉至最小间距。


# 版本：V3.7.3
# 2021.03.11
# Chao.Song
# 1.动态补偿直接拉间距，不考虑侧补要求

# 版本：V3.7.4——未转正
# 2021.06.28
# Chao.Song
# 1.支持无参考层阻抗条跑出
# 版本：V3.7.4
# 开发日期：2021.08.03 转正日期：2021.08.25
# Chao.Song
# 1.选化层自动制作：http://192.168.2.120:82/zentao/story-view-3270.html
# 2.定位孔添加NPTH属性，用于在跑板边时选化层制作

# 版本：V3.7.5
# 开发日期：2021.10.18
# 上线日期：2021.11.04
# Chao.Song
# 1.阻抗间距补偿后等于层别间距时，底色变更为黄色，用于提醒。
# 2.开发备注：2.1 改写补偿部分，三个函数改成一个；2.2 部分代码格式优化
# 3.阻抗条合并后，补负片消除小于5mil的铜丝 http://192.168.2.120:82/zentao/story-view-3560.html
# 4.差动top面走三组线时，欧姆标注会与线相交，Bug料号：940-243cb

# 版本：V3.7.6
# 开发日期：2021.11.16
# 上线日期：2021.11.19
# Chao.Song
# 1.增加开窗阻抗支持,需更新VGT_Oracle包中获取阻抗信息的方法
# 2.增加非常规阻抗的界面样式为绿底白字，目前包含：完成线宽，线距，距铜大于20时，开窗阻抗。

# 版本：V4.0.1
# 开发日期：2021.12.20
# 上线日期：2022.01.05
# Chao.Song
# 1.分割阻抗条，直接按区域分割，跑出料号名，钻孔，挡点
# 2.阻抗条上挡点与孔等大的，更改为规范要求的孔径-8mil
# 3.阻抗条界面不勾选排列（直接使用inplan数据，无需勾选）
# http://192.168.2.120:82/zentao/story-view-3590.html
# http://192.168.2.120:82/zentao/story-view-3756.html
# http://192.168.2.120:82/zentao/story-view-3834.html

# 版本：V4.0.2
# 开发日期：2022.04.01
# 上线日期：2022.04.01
# Chao.Song
# 1.选化层NPTH孔不套铜
# http://192.168.2.120:82/zentao/story-view-4135.html

# 版本：V4.1.0
# 开发日期：2022.04.21
# 上线日期：2022.04.25
# Chao.Song
# 1.内层层别类型的获取By流程；http://192.168.2.120:82/zentao/story-view-4199.html
# 2.inn类型 Hoz的间距管控by成品线宽线距；http://192.168.2.120:82/zentao/story-view-4193.html
# 3.外层及次外层外的间距管控根据干膜解析度；http://192.168.2.120:82/zentao/story-view-4173.html
# 4.阻抗条的内测点。
# 2022.05.12 5.更新阻抗信息的二次处理的正则，修复大于等于10根阻抗时的解析异常。南通反馈料号：S28006PI217A1
# 2022.08.29 l2l的间距管控，使用浅copy会引起异常，使用变量方法。

# 版本：V4.3.0
# 开发日期：2022.09.16
# 上线日期：2022.10.19
# 更改外层补偿规则，更改外层（out，sec）类的阻抗线补偿规则 http://192.168.2.120:82/zentao/story-view-4458.html

# 版本：V5.2
# 开发日期：2022年11月 开发阶段已有部分料号在使用
# 上线日期：None
# 1.更改阻抗条排列方式：差动和特性可以放在一根阻抗条中（inplan中控制）; 两种共面也可以放置在一根中。共面不与普通放在一根中.
# 2.更改阻抗条走线方式
# 2.1 (共面)特性上中走线为上测试点,下接地点,下走线为下测试点，上接地点;
# 2.2 (共面)差动上走线为上二测试点，下二接地点；中走线为左二接地点，右二测试点；下走线为下二测试点，上二接地点；
# 3.增加内层测试点及钻孔添加选项：http://192.168.2.120:82/zentao/story-view-4010.html
# 4.更改外层及次外层的差分线补偿方法 http://192.168.2.120:82/zentao/story-view-4922.html
# 5.接地点交叉线由‘x’型改为‘+’型，增加与负性套铜位置的处理。


# 版本：V5.21
# Song
# 上线日期：2022.12.07
# 1. 修正不可更改补偿值的异常；
# 2. 外层差分额外补偿值小于0时，不进行间距动补（由于部分测试料号，不补偿）


# 版本：V5.3.0
# Song
# 开发日期：2022.12.13
# 上线日期：2022.12.15
# 1.阻抗条加孔,阻抗加孔的： http://192.168.2.120:82/zentao/story-view-4010.html
# 1.1 埋孔层（排除core埋孔并多次埋孔的最内层埋孔）加孔，对应所有阻抗线位置；
# 1.2.对应埋孔的外层加pad，例b3-6，在L3及L6层加pad。
# 2.增加sec类层别更改为sec1层别的快捷方式 http://192.168.2.120:82/zentao/story-view-4977.html
# 3.2022.12.23 增加阻抗数与拼版阻抗条数的防呆；增加sec1类完成铜厚小于0.6 按0.6计算的算法

# 版本：V5.3.1
# Song
# 开发日期：2022.12.23
# 上线日期：2022.12.27
# 1.阻抗条跑完，增加与前次跑出阻抗条位置的校验
# http://192.168.2.120:82/zentao/story-view-5014.html

# 版本：V5.3.2
# Song
# 开发日期：2022.12.30
# 上线日期：2022.12.31
# 1.增加接地点可能被套断的检测：接地层，如前面已添加阻抗已添加两组，则认为可能被套断。
# http://192.168.2.120:82/zentao/story-view-5014.html

# 版本：V5.3.3
# Song
# 开发日期：2023.01.10
# 上线日期：2023.01.11
# 1.内层(inn)及次外层内(sec1)考虑内层干膜解析度
# http://192.168.2.120:82/zentao/story-view-5032.html

# 版本：V5.5
# ynh
# 开发日期：2023.01.10
# 上线日期：2023.01.11
# http://192.168.2.120:82/zentao/story-view-6376.html
