#!/bin/env python 
# -*- coding: utf-8 -*-
import string
import threading
import math
import datetime
import sys
import time

import re
# --导入Package
import os
import innerEtch_UiV2 as Mui
import json
import csv
from PyQt4 import QtCore, QtGui
# from PyQt4.QtGui import *

import platform

import string

if platform.system() == "Windows":
    # sys.path.append (r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"D:/genesis/sys/scripts/Package")

    # sys.path.append(r'D:/genesis/sys/scripts/pythondir/')

else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
    sys.path.append('/incam/server/site_data/scripts/pythondir/')

import genCOM_26
import Oracle_DB
from messageBox import msgBox
from copyfile import mycopyfile

reload(sys)
sys.setdefaultencoding("utf-8")

# --实例化genesis com对象
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


# QTextCodec.setCodecForTr(QTextCodec.codecForName("utf8"))

class MyApp(object):
    def __init__(self):
        self.job_name = os.environ.get('JOB', None)
        self.step_name = os.environ.get('STEP', None)

        # jobname = genClasses.Top().currentJob()
        # stepname = genClasses.Top().currentStep()
        # job = genClasses.Job(os.environ['JOB'])
        if not self.job_name:
            msg_box = msgBox()
            msg_box.critical(self, '警告', '未打开JOB程序无法运行，请先打开JOB！', QtGui.QMessageBox.Ok)
            sys.exit(1)
        if not self.step_name:
            msg_box = msgBox()
            msg_box.critical(self, '警告', '未打开STEP程序无法运行，请先打开STEP！', QtGui.QMessageBox.Ok)
            sys.exit(1)

        self.scrDir = os.path.split(os.path.abspath(sys.argv[0]))[0]

        GEN.COM('get_user_name')
        self.softUser = GEN.COMANS
        # === 从料号名获取信号层数

        signal_layers = GEN.GET_ATTR_LAYER('signal')
        self.signalLayerNum = self.job_name[4:6]

        try:
            self.signalLayerNum = int(self.signalLayerNum)
        except ValueError:
            # 无法获取数据时，使用默认值
            wrong_word = self.signalLayerNum
            self.signalLayerNum = len(signal_layers)

            msg_box = msgBox()
            msg_box.critical(self, '警告', '未从料号名中获取层数，异常字符：%s,使用层数%s调整孔到铜数据！' %
                             (wrong_word, self.signalLayerNum), QtGui.QMessageBox.Ok)

        # self.npth2cu = 8
        # 孔到铜按5mil管控 + 0.2mil安全间距 http://192.168.2.120:82/zentao/story-view-6951.html
        self.npth2cu = 5.2
        self.pth2cu = 5.2
        self.via2cu = 5.2
        # if self.signalLayerNum < 10:
        #     self.pth2cu = 6
        #     self.via2cu = 6
        # else:
        #     self.pth2cu = 7
        #     self.via2cu = 7
        self.col_names = ['layName', 'layer_mode', 'show_range', 'space_control', 'selMaxLine', 'normal_etch_file',
                          'single_etch_file', 'double_etch_file', 'coplanar_single_file', 'coplanar_diff_file',
                          'normal_post_file', 'fill_via2cu', 'pth2cu', 'npth2cu', 'special_22', 'pad2line', 'line2line',
                          'line2cu']
        self.inn_etch_rule = []
        with open(self.scrDir + '/etch_data-hdi1-inn_max_spacing.csv') as f:
            f_csv = csv.DictReader(f)
            for row in f_csv:
                self.inn_etch_rule.append(row)

        self.sec1_etch_rule = []
        with open(self.scrDir + '/etch_data-hdi1-sec1_max_spacing.csv') as f:
            f_csv = csv.DictReader(f)
            for row in f_csv:
                self.sec1_etch_rule.append(row)

        self.sec_etch_rule = []
        with open(self.scrDir + '/etch_data-hdi1-out.csv') as f:
            f_csv = csv.DictReader(f)
            for row in f_csv:
                self.sec_etch_rule.append(row)

        self.out_gm_rule = []
        with open(self.scrDir + '/out_gm_space.csv') as f:
            f_csv = csv.DictReader(f)
            for row in f_csv:
                self.out_gm_rule.append(row)
        self.inn_gm_rule = []
        with open(self.scrDir + '/inn_gm_space.csv') as f:
            f_csv = csv.DictReader(f)
            for row in f_csv:
                self.inn_gm_rule.append(row)
        # print '_x' * 20
        # print self.out_gm_rule

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
                return num
            except ValueError:
                return False


class MainWindowShow(QtGui.QDialog, MyApp):
    """
    窗体主方法
    """

    def __init__(self):
        super(MainWindowShow, self).__init__()
        # 初始数据
        MyApp.__init__(self)

        self.appVer = "V3.7"
        # === 记录字典 ===
        self.logdict = {'user': self.softUser}
        # === 统一配参，如后续有需求，定义多个参数 ===
        # self.selMaxLine = '15'
        self.diff2diff = 8
        self.compMethod = "Contour-based patch"
        self.ui = Mui.Ui_Form()
        self.ui.setupUi(self)
        # === 根据层数调整界面 ===
        if self.signalLayerNum > 6:
            window_height = 460 + 22 * (self.signalLayerNum - 6)
            if window_height > 800:
                window_height = 800
            self.resize(850, window_height)

        M = Oracle_DB.ORACLE_INIT()
        dbc_o = M.DB_CONNECT("172.20.218.193", "inmind.fls", '1521', 'GETDATA', 'InplanAdmin')
        if dbc_o is None:
            # Mess = msgBox.Main ()
            msg_box = msgBox()
            msg_box.critical(self, '警告', 'HDI InPlan 无法连接, 程序退出！', QtGui.QMessageBox.Ok)
            exit(0)
        self.strJobName = self.job_name.split('-')[0].upper()
        self.JobData = M.getJobData(dbc_o, self.strJobName)
        if self.JobData:
            pass
        else:
            msg_box = msgBox()
            msg_box.critical(self, '警告', 'HDI InPlan无料号%s数据, 程序退出！' % self.job_name, QtGui.QMessageBox.Ok)
            exit(0)

        # 樊后星通知：20240326 by lyh
        # 线路补偿 由计算完成厚度CAL_CU_THK_，改为计算完成厚度(不考虑树脂塞孔补偿)CAL_CU_THK_PLATE_
        self.layerInfo = M.getLayerThkInfo_plate(dbc_o, self.strJobName, "inner")

        self.stackupInfo = self.get_inplan_stackup_info(M, dbc_o)
        self.twice_mrp = self.judge_mrp_two_same(self.stackupInfo)
        self.stackupInfo = self.dealWithStackUpData(self.stackupInfo)
        if len(self.twice_mrp) > 0:
            msg_box = msgBox()
            msg_box.critical(self, '警告', 'HDI InPlan中记录MRP：%s不单一，会影响层别类型的判断，需确认！' % self.twice_mrp, QtGui.QMessageBox.Ok)
        # print json.dumps(self.stackupInfo, indent=2)
        self.comBox_type = {}
        # ====
        # layerLineType = [u'请选择', u'是', u'否']
        # self.gm_info = self.get_inplan_gm_info(M, dbc_o)
        # === 2021.01.22 取消重定义部分，直接在dealWithStackUpData中定义好内一层 ===
        # self.stackupInfo = self.redeal_layer_mode(self.stackupInfo)
        M.DB_CLOSE(dbc_o)

        self.miscdrilllayers = self.get_misc_drill_layers()
        bottom_text = self.ui.bottomLabel.text()
        if len(self.miscdrilllayers) > 0:
            self.ui.bottomLabel.setText(bottom_text+u"\n动补过程中，需要misc掉以下钻孔层：%s" % ','.join(self.miscdrilllayers))
        # self.ui.groupBox.setTitle(u'动补过程中，需要misc掉以下钻孔层：%s' % ','.join(self.miscdrilllayers))
        # top_title = self.ui.topLabel.text()
        self.ui.topLabel.setText(u'HDI内层动态补偿——%s' % self.job_name.upper())
        # === 在hash中取出满足条件的内层列表 ===
        inn_layers = [i.lower() for i in self.stackupInfo if self.stackupInfo[i]['layerMode'] != 'out']
        inn_layers.sort(key=lambda x: int(x[1:]))
        all_inner_mode_list = self.set_table_detail(inn_layers)
        # === 隐藏列，数据太长，不需要给用户看, 但不能删除，后续从这里取数 ===
        # === TODO 测试阶段完成待隐藏
        self.ui.tableWidget.hideColumn(5)
        self.ui.tableWidget.hideColumn(6)
        self.ui.tableWidget.hideColumn(7)
        self.ui.tableWidget.hideColumn(8)
        self.ui.tableWidget.hideColumn(9)
        self.ui.tableWidget.hideColumn(10)
        # 需求中未提及可以修改sec层别以及sec1层别的via到铜，此编辑隐藏以备后用 ===
        self.ui.label_sec12cu.setHidden(True)
        self.ui.lineEdit_sec1_via2cu.hide()
        self.ui.label_sec2cu.setHidden(True)
        self.ui.lineEdit_sec_via2cu.hide()

        # === 获取当前程序路径
        # self.selMaxLine = '15'
        # self.dataIndex = ''
        # self.normal_etchFile = ''
        # self.single_etchFile = ''
        # self.diff_etchFile = ''
        # self.spcValue = ''
        if 'inn' not in all_inner_mode_list:
            self.ui.checkBox_inn2cu.hide()
        elif 'sec' not in all_inner_mode_list:
            self.ui.checkBox_sec2cu.hide()
        elif 'sec1' not in all_inner_mode_list:
            self.ui.checkBox_sec12cu.hide()

        self.addUiDetail()

    def set_table_detail(self, inn_layers):

        # ===table的行数量
        self.ui.tableWidget.setRowCount(len(inn_layers))
        all_inner_mode_list = []
        for rowNum, layName in enumerate(inn_layers):
            # --获取层名
            # --获取铜厚
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
            self.ui.tableWidget.setItem(rowNum, 0, item)
            item = self.ui.tableWidget.item(rowNum, 0)
            # --设置文字居中
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter)
            # --设置此列不可修改
            # self.ui.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
            # self.ui.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
            # --写入文本信息
            item.setText(_translate("Form", layName, None))
            layer_mode = self.stackupInfo[layName]['layerMode']
            all_inner_mode_list.append(layer_mode)
            df_type = self.stackupInfo[layName]['df_type']

            self.item_set(rowNum, 1, layer_mode)

            # print json.dumps(self.layerInfo,indent=2)
            # print json.dumps(self.inn_etch_rule,indent=2)
            show_range = None
            normal_etch_file = None
            single_etch_file = None
            double_etch_file = None
            normal_post_file = None
            space_control = None
            buried_via_ring = None
            fill_via2cu = None
            selMaxLine = None
            pad2line = None
            line2line = None
            line2cu = None
            diff2diff = None
            table_row_width = [40, 60, 90, 60, 80, 100, 150, 150, 150, 150, 90, 75, 75, 75, 75, 75, 75, 75]
            for c_width in range(len(table_row_width)):
                self.ui.tableWidget.setColumnWidth(c_width, table_row_width[c_width])

            for l_index in self.layerInfo:
                w_line_width = l_index['成品线宽']
                w_line_space = l_index['成品线距']
                if layName == l_index['LAYER_NAME']:
                    if layer_mode == 'inn':
                        getthick = l_index['CU_WEIGHT']
                        for inn_line in self.inn_etch_rule:
                            if float(inn_line['lower_thick']) < float(getthick) < float(inn_line['upper_thick']):
                                show_range = inn_line['range_type']
                                normal_etch_file = inn_line['normal_etch_file']
                                single_etch_file = inn_line['single_etch_file']
                                double_etch_file = inn_line['diff_etch_file']
                                space_control = inn_line['space_control']
                                # === HOZ 分了三个区段，出货线宽出货间距 ===
                                if show_range == '<=H/HOZ':
                                    if (w_line_width == '0' and w_line_space == '0') or (w_line_width == 0 and w_line_space == 0):
                                        pass
                                    elif 1.8 > float(w_line_width) > 1.5 and 1.8 > float(w_line_space) > 1.5:
                                        space_control = '1.4'
                                    elif 2.0 > float(w_line_width) and 2.0 > float(w_line_space):
                                        space_control = '1.6'
                                selMaxLine = inn_line['max_line']
                        get_gm_min_space = None
                        for gm_line in self.inn_gm_rule:
                            if df_type == gm_line['gm_type']:
                                get_gm_min_space = gm_line['min_space']
                        if get_gm_min_space:
                            space_control = max(space_control, get_gm_min_space)
                        else:
                            msg_box = msgBox()
                            msg_box.critical(self, '警告', '未能获取层别：%s干膜：%s的解析度，使用规范中最小间距，需确认！' % (layName, df_type),
                                             QtGui.QMessageBox.Ok)
                    else:
                        getthick = l_index['CAL_CU_THK']
                        if layer_mode == 'sec1':
                            for sec1_line in self.sec1_etch_rule:
                                if float(sec1_line['lower_thick']) <= float(getthick) < float(sec1_line['upper_thick']):
                                    show_range = sec1_line['range_type']
                                    normal_etch_file = sec1_line['normal_etch_file']
                                    single_etch_file = sec1_line['single_etch_file']
                                    double_etch_file = sec1_line['diff_etch_file']
                                    normal_post_file = sec1_line['normal_post_file']
                                    # 如果原稿间距小于1.8且铜厚在0.6-0.8区间的更改动补指向文件
                                    if float(getthick) < 0.8 and l_index['原稿线距']:
                                        if float(l_index['原稿线距']) < 1.8:
                                            normal_etch_file = 'max-spacing-sec1_etch_c0.4_1_v3.7'
                                            single_etch_file = 'max-spacing-sec1_single_etch_c0.4_1_v3.7'
                                            double_etch_file = 'max-spacing-sec1_diff_etch_c0.4_1_v3.7'
                                    space_control = sec1_line['space_control']
                                    buried_via_ring = sec1_line['buried_via_ring']
                                    selMaxLine = sec1_line['max_line']
                        elif layer_mode == 'sec':
                            for sec_line in self.sec_etch_rule:
                                if float(sec_line['lower_thick']) <= float(getthick) < float(sec_line['upper_thick']):
                                    show_range = sec_line['range_type']
                                    normal_etch_file = sec_line['normal_etch_file']
                                    single_etch_file = sec_line['single_etch_file']
                                    double_etch_file = sec_line['diff_etch_file']
                                    space_control = sec_line['space_control']
                                    buried_via_ring = sec_line['buried_via_ring']
                                    selMaxLine = sec_line['max_line']
                                    pad2line = sec_line['pad2line']
                                    line2line = sec_line['line2line']
                                    line2cu = sec_line['line2cu']
                                    diff2diff = sec_line['diff2diff']
                        if layer_mode == 'sec':
                            get_gm_min_space = None
                            for gm_line in self.out_gm_rule:
                                if df_type == gm_line['gm_type']:
                                    get_gm_min_space = gm_line['min_space']
                            if get_gm_min_space:
                                space_control = max(space_control, get_gm_min_space)
                                pad2line = max(pad2line, get_gm_min_space)
                                line2line = max(line2line, get_gm_min_space)
                                line2cu = max(line2cu, get_gm_min_space)
                            else:
                                msg_box = msgBox()
                                msg_box.critical(self, '警告', '未能获取层别：%s干膜：%s的解析度，使用规范中最小间距，需确认！' % (layName, df_type),
                                                 QtGui.QMessageBox.Ok)
                        if layer_mode == 'sec1':
                            get_gm_min_space = None
                            for gm_line in self.inn_gm_rule:
                                if df_type == gm_line['gm_type']:
                                    get_gm_min_space = gm_line['min_space']
                                    print get_gm_min_space

                            if get_gm_min_space:
                                space_control = max(space_control, get_gm_min_space)
                            else:
                                msg_box = msgBox()
                                msg_box.critical(self, '警告', '未能获取层别：%s干膜：%s的解析度，使用规范中最小间距，需确认！' % (layName, df_type),
                                                 QtGui.QMessageBox.Ok)
                    self.item_set(rowNum, 2, show_range)
                    self.item_set(rowNum, 3, space_control)

                    need_gm_list = ['杜邦DI9325', '杜邦DI9320']

                    if df_type in need_gm_list:
                        if layer_mode == 'inn':
                            self.item_set(rowNum, 14, '%s/%s' % (w_line_width, w_line_space))

                            if w_line_width != '0' and w_line_space != '0':
                                if 2.0 >= float(w_line_width) > 0 and 2.0 >= float(w_line_space) > 0:
                                    self.item_set(rowNum, 15, str(1.4))

                        else:
                            if float(getthick) <= 0.984:
                                self.item_set(rowNum, 15, str(1.4))

                    if layer_mode == 'sec':
                        self.item_set(rowNum, 15, pad2line)

                    self.item_set(rowNum, 4, selMaxLine)
                    self.item_set(rowNum, 5, normal_etch_file)
                    self.item_set(rowNum, 6, single_etch_file)
                    self.item_set(rowNum, 7, double_etch_file)

                    if layer_mode == 'inn' or layer_mode == 'sec1':
                        self.item_set(rowNum, 8, single_etch_file)
                        self.item_set(rowNum, 9, double_etch_file)
                    if layer_mode == 'inn':
                        fill_via2cu = self.via2cu

                    if layer_mode == 'sec' or layer_mode == 'sec1':
                        fill_via2cu = float(space_control) + float(buried_via_ring)

                    if normal_post_file is not None:
                        self.item_set(rowNum, 10, normal_post_file)
                    self.item_set(rowNum, 11, fill_via2cu)
                    self.item_set(rowNum, 12, self.pth2cu)
                    self.item_set(rowNum, 13, self.npth2cu)

            if layer_mode == 'sec':
                self.item_set(rowNum, 16, line2line)
                self.item_set(rowNum, 17, line2cu)

            if show_range is None:
                msg_box = msgBox()
                msg_box.critical(self, '警告', 'HDI InPlan 无法获取层别%s信息, 程序退出！' % layName, QtGui.QMessageBox.Ok)
                exit(0)

        return all_inner_mode_list

    def item_set(self, rowInt, colInt, text):
        item = QtGui.QTableWidgetItem(str(text))
        item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter)
        item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
        self.ui.tableWidget.setItem(rowInt, colInt, item)

    def addUiDetail(self):

        # === sec层的线路补偿范围显示，取消
        self.ui.groupBox_2.hide()
        # === 孔到铜修改，窗口默认取消
        self.ui.widget_inn2cu.hide()
        self.ui.widget_sec2cu.hide()
        self.ui.widget_sec12cu.hide()
        # === kong到铜栏位，限制输入数量，并限制输入为数字 ===
        my_regex = QtCore.QRegExp("[1-9][0-9]?\.[0-9][0-9]?")
        my_validator = QtGui.QRegExpValidator(my_regex, self.ui.lineEdit_inn_pth2cu)
        self.ui.lineEdit_inn_pth2cu.setValidator(my_validator)
        my_validator = QtGui.QRegExpValidator(my_regex, self.ui.lineEdit_inn_via2cu)
        self.ui.lineEdit_inn_via2cu.setValidator(my_validator)
        my_validator = QtGui.QRegExpValidator(my_regex, self.ui.lineEdit_sec_pth2cu)
        self.ui.lineEdit_sec_pth2cu.setValidator(my_validator)
        my_validator = QtGui.QRegExpValidator(my_regex, self.ui.lineEdit_sec_pth2cu)
        self.ui.lineEdit_sec_pth2cu.setValidator(my_validator)
        my_validator = QtGui.QRegExpValidator(my_regex, self.ui.lineEdit_sec1_pth2cu)
        self.ui.lineEdit_sec1_pth2cu.setValidator(my_validator)
        my_validator = QtGui.QRegExpValidator(my_regex, self.ui.lineEdit_sec1_via2cu)
        self.ui.lineEdit_sec1_via2cu.setValidator(my_validator)

        # --加载动态step列表
        usefulSteps, defaultSel = self.getJOB_steps()
        #增加被其他程序调用时用指定的step 20230920 by lyh
        if os.environ.get("ADD_LINE_SPACING_COUPON", None) == "yes":
            usefulSteps, defaultSel = [os.environ["STEP"]], [os.environ["STEP"]]
        # usefulSteps, defaultSel = ['a', 'b'], ['a']
        self.ui.listWidget_SelStep.addItems(usefulSteps)
        # === Song 2021.02.04 设置层别名不可编辑 ===
        self.ui.tableWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        # --默认选择的STEP
        for sStep in defaultSel:
            matching_items = self.ui.listWidget_SelStep.findItems(sStep, QtCore.Qt.MatchExactly)
            for item in matching_items:
                item.setSelected(True)
        self.sel_step_tips()
        self.ui.bottomLabel.setText(u"版权所有：胜宏科技 作者：Chao.Song 版本：%s 日期：2021.02.02" % self.appVer)

        QtCore.QObject.connect(self.ui.listWidget_SelStep, QtCore.SIGNAL("itemSelectionChanged()"), self.sel_step_tips)
        QtCore.QObject.connect(self.ui.applyButton, QtCore.SIGNAL("clicked()"), self.main_run)
        # QtCore.QObject.connect(self.ui.lineEdit_sec1_pth2cu, QtCore.SIGNAL("editingFinished()"), self.change_hole2cu)
        # QtCore.QObject.connect(self.ui.lineEdit_inn_pth2cu, QtCore.SIGNAL("textChanged()"), self.change_hole2cu)
        self.ui.lineEdit_inn_pth2cu.textChanged.connect(self.change_hole2cu)
        self.ui.lineEdit_sec_pth2cu.textChanged.connect(self.change_hole2cu)
        self.ui.lineEdit_sec1_pth2cu.textChanged.connect(self.change_hole2cu)
        self.ui.lineEdit_inn_via2cu.textChanged.connect(self.change_hole2cu)
        self.ui.lineEdit_sec_via2cu.textChanged.connect(self.change_hole2cu)
        self.ui.lineEdit_sec1_via2cu.textChanged.connect(self.change_hole2cu)
        QtCore.QObject.connect(self.ui.pushButton_change_sec, QtCore.SIGNAL("clicked()"), self.change_table)

    def change_table(self):
        msg_box = msgBox()
        get_result = msg_box.question(self, '层别类型更改确认', '执行此按钮，会更改sec类型为sec1类型，是否继续?', QtGui.QMessageBox.Yes,QtGui.QMessageBox.No)
        if get_result == 1:
            return
        all_info = self.get_window_info(None, mode='all')

        print json.dumps(self.stackupInfo, indent=2)
        for a_layer in self.stackupInfo:
            if self.stackupInfo[a_layer]['layerMode'] == 'sec':
                self.stackupInfo[a_layer]['layerMode'] = 'sec1'
        inn_layers = [i.lower() for i in self.stackupInfo if self.stackupInfo[i]['layerMode'] != 'out']
        inn_layers.sort(key=lambda x: int(x[1:]))
        # === 不直接使用self.ui.tableWidget.clear() 方法，用于保留标题行
        for row in range(self.ui.tableWidget.rowCount()):
            self.ui.tableWidget.removeRow(0)
        self.set_table_detail(inn_layers)

    def sel_step_tips(self):
        self.ui.labeltips.setText(
            u"Tips:当前选择的Step:%s" % ([str(i.text()) for i in self.ui.listWidget_SelStep.selectedItems()]))

    def change_hole2cu(self):
        print 'self.sender().objectName()', self.sender().objectName()
        ob_name = self.sender().objectName()
        change_mode = None
        change_col = None
        ip_split = ob_name.split('_')
        change_mode = ip_split[1]
        change_item = ip_split[2]
        if change_item == 'via2cu':
            change_col = 11
        elif change_item == 'pth2cu':
            change_col = 12
        print self.ui.tableWidget.rowCount()
        for row_num in range(self.ui.tableWidget.rowCount()):
            if str(self.ui.tableWidget.item(row_num, 1).text()) == change_mode:
                self.ui.tableWidget.item(row_num, change_col).setText(str(self.sender().text()))
                self.ui.tableWidget.item(row_num, change_col).setForeground(QtGui.QBrush(QtGui.QColor('blue')))

    def change_line2pad(self):
        # print self.sender()
        # print int(self.sender().objectName())
        rou_num = int(self.sender().objectName())
        # self.ui.tableWidget
        item = QtGui.QTableWidgetItem(str(1.4))
        item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter)
        item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
        self.ui.tableWidget.setItem(rou_num, 15, item)
        if self.sender().currentText() == u'是':
            self.ui.tableWidget.item(rou_num, 15).setText(str(1.4))
        else:
            self.ui.tableWidget.item(rou_num, 15).setText('')

    def get_misc_drill_layers(self):
        """
        获取料号中的钻孔列表，并返回导气及铝片层
        :return:
        """
        # === 获取钻孔列表，并获取排除的层别：sz*-*.lp及sz*-*...dq类层别
        all_drill_layers = GEN.GET_ATTR_LAYER('drill')
        need_misc_reg = re.compile('sz([0-9][0-9]?-[0-9][0-9]?)?...dq|sz([0-9][0-9]?-[0-9][0-9]?)?.lp')
        need_misc_list = []
        for dlayer in all_drill_layers:
            if need_misc_reg.match(dlayer):
                need_misc_list.append(dlayer)
        return need_misc_list

    def get_window_info(self, items,mode='select'):
        """
        提取table widget info
        :param items: 选中的元素，mode为select时需传入，
        :param mode: select|all
        :return: all_info mode为select时返回dict，mode为all时范围array
        """
        all_info = None
        # print self.comBox_type
        if mode == 'select':
            all_info = {}

            for selObj in items:
                # --获取选中的行信息，行号，列号
                selText = str(selObj.text())
                selRow = selObj.row()
                selCol = selObj.column()
                current_info = {}
                # item_text = self.ui.tableWidget.item (selRow, selCol).text ()
                for c_index, item in enumerate(self.col_names):
                    try:
                        item_text = str(self.ui.tableWidget.item(selRow, c_index).text())
                    except AttributeError:
                        item_text = None
                    current_info[item] = item_text

                # --不允许选择其它列
                if selCol > 0:
                    msg_box = msgBox()
                    msg_box.warning(self, '警告', u'执行前，请选择第一列层别，勿选择其它列！', QtGui.QMessageBox.Ok)
                    self.ui.tableWidget.clearSelection()
                    return False

                all_info[current_info[self.col_names[0]]] = current_info
        elif mode == 'all':
            all_info = []
            row_num = self.ui.tableWidget.rowCount()
            for selRow in range(row_num):
                current_info = {}
                # item_text = self.ui.tableWidget.item (selRow, selCol).text ()
                for c_index, item in enumerate(self.col_names):
                    try:
                        item_text = str(self.ui.tableWidget.item(selRow, c_index).text())
                    except AttributeError:
                        item_text = None
                    current_info[item] = item_text

                # all_info[current_info[self.col_names[0]]] = current_info
                all_info.append(current_info)
        print json.dumps(all_info, indent=2)

        return all_info

    def check_imp_attrs(self, sel_steps, layerlist):
        # 16938#L -0.5654528 2.7052165 -0.5561024 2.7145669 r4.52 P 146 ;.imp_line,.imp_info=single-ended,.imp_type=single-ended
        # 16961#L -0.5764195 2.7052165 -0.5757874 2.7052165 r4.52 P 146 ;.imp_line,.imp_info=single-ended,.imp_type=single-ended
        for stepName in sel_steps:
            GEN.OPEN_STEP(job=self.job_name, step=stepName)
            GEN.FILTER_RESET()
            GEN.CLEAR_LAYER()
            GEN.FILTER_SET_FEAT_TYPES('line\;arc')
            GEN.FILTER_SET_POL(pol="positive")
            GEN.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.imp_line")
            for layer in layerlist:
                notinfo_index = []
                GEN.AFFECTED_LAYER(layer,affected='yes')
                GEN.FILTER_SELECT()
                if GEN.GET_SELECT_COUNT():
                    info = GEN.INFO(" -t layer -e %s/%s/%s -d FEATURES -o feat_index+select" % (self.job_name, stepName, layer))
                    for line in info[1:]:
                        if 'imp_type' not in line:
                            index = line.split("#")[1].strip()
                            notinfo_index.append(index)
                if notinfo_index:
                    GEN.FILTER_RESET()
                    GEN.CLEAR_LAYER()
                    GEN.AFFECTED_LAYER(layer,affected='yes')
                    for i in notinfo_index:
                        GEN.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(layer, i))
                    msg_box = msgBox()
                    msg_box.information(self, '警告', u'%s层中点亮的阻抗线属性不全，请检查' % layer, QtGui.QMessageBox.Ok)
                    sys.exit(0)
            GEN.FILTER_RESET()
            GEN.CLEAR_LAYER()


    def main_run(self):
        """
        主程序
        :return:
        """
        items = self.ui.tableWidget.selectedItems()



        all_info = self.get_window_info(items)



        # === TODO 2022.11.21 测试阶段，暂时退出
        # exit(1)

        # --点击“执行”按钮，运行部分
        if len(items) == 0:
            msg_box = msgBox()
            msg_box.information(self, '警告', u'未选择任何优化层，请从第一列选择需要动补的层！', QtGui.QMessageBox.Ok)
            return True

        # --选择的STEP
        sel_items = self.ui.listWidget_SelStep.selectedItems()
        sel_step_list = [str(i.text()) for i in list(sel_items)]
        if len(sel_step_list) == 0:
            showText = self.msgText(u'提醒', "请选择需要动补的STEP！")
            self.msgBox(showText)
            return False

        # 检测是否有阻抗线属性定义不完整
        self.check_imp_attrs(sel_step_list, all_info.keys())

        # === V3.2.1 在此处增加层别的misc
        for dlayer in self.miscdrilllayers:
            GEN.COM('matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=misc' % (self.job_name, dlayer))

        # print 'x' * 40
        # print json.dumps(all_info, indent=2)
        # === 生成的hash根据层别，层别类型，区间定义进行归类 ===

        # === 归类后进行不同层别类型的预处理
        all_check_items = [(all_info[i]['layer_mode'], all_info[i]['show_range']) for i in all_info]
        # === 根据归类后的层别，建立checklist带入主界面参数，动态补偿文件信息， 参数间距控制 ===
        all_check_items = list(set(all_check_items))
        # [('sec1', '0.8<=C<1.0'), ('inn', '<=H/HOZ'), ('sec', '0.8<=C<1.0')]
        run_dict = {}
        for a_index, a_array in enumerate(all_check_items):
            run_dict[a_index + 1] = dict(mode=a_array, layer_mode=a_array[0], show_range=a_array[1],
                                         sel_layers=[all_info[i]['layName'] for i in all_info
                                                     if all_info[i]['layer_mode'] == a_array[0]
                                                     and all_info[i]['show_range'] == a_array[1]])

        # print json.dumps(run_dict, indent=2)
        self.logdict['sel_step_list'] = []
        self.logdict['copy_files'] = []
        self.logdict['sel_step_list'] = sel_step_list
        for work_step in sel_step_list:
            GEN.OPEN_STEP(work_step, self.job_name)
            GEN.CHANGE_UNITS('inch')
            GEN.CLEAR_LAYER()
            GEN.VOF()
            GEN.COM("chklist_delete,chklist=adetch")
            GEN.COM("chklist_from_lib,chklist=adetch,profile=none,customer=")
            GEN.VON()

            # 在料号中建立好checklist
            if len(all_check_items) > 1:
                GEN.COM('chklist_pclear')
                GEN.COM('chklist_pcopy,chklist=adetch,nact=1')
                for i in range(2, len(all_check_items) + 1):
                    GEN.COM('chklist_ppaste_act,chklist=adetch,row=%s' % i)
                    # print i

            for act_num in run_dict:
                self.logdict[act_num] = {}
                self.logdict[act_num]['sel_layers'] = []
                self.logdict[act_num]['sel_layers'] = run_dict[act_num]['sel_layers']
                self.logdict[act_num]['all_info'] = {}
                self.logdict[act_num]['all_info'] = all_info[run_dict[act_num]['sel_layers'][0]]
                self.set_hole2cu(act_num, run_dict[act_num]['sel_layers'], all_info[run_dict[act_num]['sel_layers'][0]])
                if run_dict[act_num]['layer_mode'] == 'inn':
                    self.innetch_set(act_num, run_dict[act_num]['sel_layers'],
                                     all_info[run_dict[act_num]['sel_layers'][0]])
                elif run_dict[act_num]['layer_mode'] == 'sec1':
                    self.sec1_etch_set(act_num, run_dict[act_num]['sel_layers'],
                                       all_info[run_dict[act_num]['sel_layers'][0]])
                elif run_dict[act_num]['layer_mode'] == 'sec':
                    self.sec_etch_set(act_num, run_dict[act_num]['sel_layers'],
                                      all_info[run_dict[act_num]['sel_layers'][0]],
                                      show_range=run_dict[act_num]['show_range'])

            # ===  整体运行
            prechangedrl = self.change_drl_via_to_pth()
            GEN.PAUSE('inn_etch')
            GEN.COM("chklist_run,chklist=adetch,nact=s,area=global,async_run=yes")
            if prechangedrl is True:
                self.return_drl_pth_to_via()
            warn_info = ''
            # === 挨个获取结果，归类直接报出 ===
            for act_num in run_dict:
                runStatus = GEN.DO_INFO("-t check -e %s/%s/adetch -d STATUS -o action=%s"
                                        % (self.job_name, work_step, act_num))
                if runStatus['gSTATUS'] == 'ERROR':
                    warn_info += 'Step:%s checklist %s 动态补偿失效！' % (work_step, act_num)
                self.logdict['runStatus_%s_%s' % (work_step, act_num)] = runStatus['gSTATUS']

            if warn_info:
                msg_box = msgBox()
                msg_box.critical(self, '警告', '%s' % warn_info, QtGui.QMessageBox.Ok)

            GEN.FILTER_RESET()
            GEN.COM('adv_filter_reset, filter_name=popup')
            GEN.CLEAR_LAYER()

        # print json.dumps (self.logdict, indent=2)
        self.writeLog()
        self.close()
        # === V3.2.1 在此处增加层别属性还原的操作 ===
        for dlayer in self.miscdrilllayers:
            GEN.COM('matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=board' % (self.job_name, dlayer))

        msg_box = msgBox()
        msg_box.information(self, '提示', '动态补偿程序运行完成', QtGui.QMessageBox.Ok)
        exit(0)

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

    def redeal_layer_mode(self, stack_data):
        """
        http://192.168.2.120:82/zentao/story-view-1913.html
        更改原程序逻辑，更改为最靠内的sec为sec1即新增定义次一层，使用次一层补偿
        :return:
        """
        half_signal_num = self.signalLayerNum / 2
        # 由中间层向top面寻找第一个次外层定义，更改为次一层定义
        for i in range(int(half_signal_num), 0, -1):
            if stack_data['l%s' % i]['layerMode'] == 'sec':
                stack_data['l%s' % i]['layerMode'] = 'sec1'
                break

        for i in range(int(half_signal_num) + 1, int(self.signalLayerNum), 1):
            if stack_data['l%s' % i]['layerMode'] == 'sec':
                stack_data['l%s' % i]['layerMode'] = 'sec1'
                break
        return stack_data

    def change_drl_via_to_pth(self):
        # === 判断drl层是否存在
        if GEN.LAYER_EXISTS('drl', job=self.job_name, step=self.step_name) == 'yes':
            tmp_via_bak_layer = '__tmp_drl_via__'
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER('drl', 'yes')
            # === 判断drl是否有via
            GEN.FILTER_RESET()
            GEN.COM('adv_filter_reset, filter_name = popup')
            GEN.COM('filter_atr_reset')
            GEN.FILTER_OPTION_ATTR('.drill', 'via')
            GEN.FILTER_SELECT()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                # === 增加另一属性，后续恢复属性时可用
                GEN.COM('cur_atr_reset')
                GEN.COM('cur_atr_set,attribute=.string,text=etch_via_bak')
                GEN.COM('sel_change_atr, mode = add')
                # === 再次选择，follow以上过滤器
                GEN.FILTER_SELECT()
                if int(GEN.GET_SELECT_COUNT()) > 0:
                    # === 选中via属性钻孔，替换属性
                    GEN.COM('cur_atr_reset')
                    GEN.COM('cur_atr_set,attribute=.drill, option = plated')
                    GEN.COM('sel_change_atr, mode = add')
                    GEN.CLEAR_LAYER()
                    return True
                else:
                    msg_box = msgBox()
                    msg_box.critical(self, '警告', '%s' % '不可能选不到via孔，请确认哪里出错了', QtGui.QMessageBox.Ok)
                    return "Error"
            else:
                GEN.CLEAR_LAYER()
                return 'no_via'
        else:
            GEN.CLEAR_LAYER()
            return 'no_drl_layer'

    def return_drl_pth_to_via(self):
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER('drl', 'yes')

        GEN.FILTER_RESET()
        GEN.COM('adv_filter_reset, filter_name = popup')
        GEN.COM('filter_atr_reset')
        GEN.FILTER_TEXT_ATTR('.string', 'etch_via_bak')
        GEN.FILTER_SELECT()
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.COM('cur_atr_reset')
            GEN.COM('cur_atr_set,attribute=.drill, option = via')
            GEN.COM('sel_change_atr, mode = add')
            GEN.CLEAR_LAYER()
            return True
        else:
            msg_box = msgBox()
            msg_box.critical(self, '警告', '%s' % '未能还原drl层via孔属性，请确认哪里出错了', QtGui.QMessageBox.Ok)
            return "Error"

    def set_hole2cu(self, ip_index, ip_layers, ip_dict):
        """
        动态补偿预设孔到铜
        :param ip_index: checklist的编号
        :param ip_layers: 列表，需运行动态补偿的层别
        :param ip_dict: 输入信息dict，包含运行的所有参数
        :return:
        """

        via2cu = ip_dict['fill_via2cu']
        pth2cu = ip_dict['pth2cu']
        npth2cu = ip_dict['npth2cu']

        hole2cu = dict(min_spacing_laser_to_copper=0, min_spacing_via_to_copper=via2cu,
                       min_spacing_pth_to_copper=pth2cu, min_spacing_npth_to_copper=npth2cu)
        # ===设定孔到铜管控=== 2020.05.19 by song
        for hole2cu_mode in hole2cu:
            GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=%s,value=%s,options=0" % (
                ip_index, hole2cu_mode, hole2cu[hole2cu_mode]))

        # self.innetch(ip_index, ip_layers, ip_dict)
        # self.Message('完成')
        # exit()

    def innetch_set(self, ip_index, ip_layers, ip_dict):
        """
        内层动补设定
        :param ip_index:
        :param ip_layers:
        :param ip_dict:
        :return:
        """

        selMaxLine = ip_dict['selMaxLine']
        spcValue = ip_dict['space_control']
        normal_etchFile = ip_dict['normal_etch_file']
        single_etchFile = ip_dict['single_etch_file']
        diff_etchFile = ip_dict['double_etch_file']
        if ip_dict['pad2line']:
            # === 加大0.01mil避免优化后，间距值小于1.4
            pad2line = float(ip_dict['pad2line']) + 0.01
        else:
            pad2line = spcValue
        GEN.CHANGE_UNITS('inch')
        GEN.CLEAR_LAYER()
        for wk_lay in ip_layers:
            GEN.AFFECTED_LAYER(wk_lay, 'yes')
            # == 删除动补属性的物件 ==
            GEN.FILTER_RESET()
            GEN.COM('adv_filter_reset, filter_name = popup')
            GEN.FILTER_SET_ATR_SYMS('.detch_comp')
            GEN.FILTER_SELECT()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_DELETE()
            GEN.FILTER_RESET()
            GEN.COM('adv_filter_reset, filter_name = popup')
            # == 删除层别中已定义的属性 .bit
            GEN.COM('sel_delete_atr,mode=list,attributes=.bit,attr_vals=etchline<=%smil' % selMaxLine)
            GEN.COM("adv_filter_reset")
            GEN.FILTER_RESET()
            # == 动补前备份层别 ==
            tmp_value = "etch-"
            bak_layer = '%s%s' % (tmp_value, wk_lay)
            GEN.VOF()
            GEN.DELETE_LAYER(bak_layer)
            GEN.VON()
            GEN.SEL_COPY(bak_layer)
            GEN.CLEAR_LAYER()
        GEN.CLEAR_LAYER()
        for wk_lay in ip_layers:
            GEN.AFFECTED_LAYER(wk_lay, 'yes')
        # === 选择影响层补偿范围内的线 ====
        GEN.COM("reset_filter_criteria,filter_name=,criteria=all")
        GEN.COM("set_filter_type,filter_name=,lines=yes,pads=no,surfaces=no,arcs=yes,text=yes")
        GEN.COM("set_filter_polarity,filter_name=,positive=yes,negative=no")
        GEN.COM("reset_filter_criteria,filter_name=,criteria=profile")
        GEN.COM("reset_filter_criteria,filter_name=popup,criteria=inc_attr")
        GEN.COM("reset_filter_criteria,filter_name=popup,criteria=exc_attr")
        # change 2-->0.1
        GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=no,symbols=r0.1:r%s;s0.1:s%s" % (selMaxLine,selMaxLine))
        GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=yes,symbols=")
        GEN.COM("reset_filter_criteria,filter_name=,criteria=text")
        GEN.COM("reset_filter_criteria,filter_name=,criteria=dcode")
        GEN.COM("reset_filter_criteria,filter_name=,criteria=net")
        GEN.COM("set_filter_length")
        GEN.COM("set_filter_angle")
        GEN.COM("adv_filter_reset")
        GEN.COM("filter_area_strt")
        GEN.COM("filter_area_end,filter_name=popup,operation=select")
        GEN.COM("get_select_count")
        # === 更改此部分写法 ===
        if int(GEN.COMANS) > 0:
            list_attri = [".patch", ".imp_line", ".imp_info", ".tear_drop", ".sliver_fill"]
            for attr in list_attri:
                GEN.COM("reset_filter_criteria, filter_name = popup , criteria = exc_attr")
                GEN.COM("reset_filter_criteria, filter_name = popup, criteria = inc_attr")
                GEN.COM("set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=no,attribute=%s,"
                        "min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=" % (attr))
                GEN.COM("set_filter_and_or_logic, filter_name = , criteria = inc_attr, logic = and")
                GEN.COM("filter_area_strt")
                GEN.COM("filter_area_end,filter_name=popup,operation=unselect")
        GEN.COM("get_select_count")
        if int(GEN.COMANS) > 0:
            # === 不直接运行checklist，改为设定属性，进行多种属性线同时补偿
            addBit = 'etchline<=%smil' % selMaxLine
            GEN.COM('cur_atr_reset')
            GEN.COM('cur_atr_set,attribute=.bit,text=%s' % addBit)
            GEN.COM('sel_change_atr,mode=add')

        # == 进行三个区间进行直接动补，具有.bit属性的一般线路
        # == 单端阻抗线
        # == 差分阻抗线
        # --参数一：普通线
        pp_feature1 = 'Traces'
        # --参数二：板内特性阻抗线
        pp_feature2 = 'Traces'
        # --参数三：板内差分阻抗线
        pp_feature3 = 'Traces'
        # --定义Etch comp functions里的参数
        # == 优先级数字越小，级别越高 == note by song 2020.05.23
        # == 补偿优先级 差分>特性>一般线路
        parm1 = "(pp_feature1=%s)(pp_attr1=.bit = %s)(pp_func1=%s)(pp_func_w1=.zero)(pp_priority1=4)" \
                "(pp_method1=Contour-based patch)" % (pp_feature1, 'etchline<=%smil' % selMaxLine, normal_etchFile)
        parm2 = "(pp_feature2=%s)(pp_attr2=.imp_type=single-ended)(pp_func2=%s)(pp_func_w2=.zero)(pp_priority2=3)" \
                "(pp_method2=Contour-based patch)" % (pp_feature2, single_etchFile)
        parm3 = "(pp_feature3=%s)(pp_attr3=.imp_type=differential)(pp_func3=%s)(pp_func_w3=.zero)(pp_priority3=2)" \
                "(pp_method3=Contour-based patch)" % (pp_feature3, diff_etchFile)
        parm4 = "(pp_feature4=%s)(pp_attr4=.imp_type=single-ended coplanar)(pp_func4=%s)(pp_func_w4=.zero)(pp_priority4=5)" \
                "(pp_method4=Contour-based patch)" % (pp_feature2, single_etchFile)
        parm5 = "(pp_feature5=%s)(pp_attr5=.imp_type=differential coplanar)(pp_func5=%s)(pp_func_w5=.zero)(pp_priority5=6)" \
                "(pp_method5=Contour-based patch)" % (pp_feature2, diff_etchFile)
        parm6 = "(pp_feature6=%s)(pp_attr6=.imp_line;.imp_info;.patch)(pp_func6=%s)(pp_func_w6=.zero)(pp_priority6=7)" \
                "(pp_method6=Contour-based patch)" % (pp_feature2, diff_etchFile)        
        ParM = parm1 + parm2 + parm3 + parm4 + parm5 + parm6
        self.logdict['copy_files'].append(normal_etchFile)
        self.logdict['copy_files'].append(single_etchFile)
        self.logdict['copy_files'].append(diff_etchFile)

        inn_param_num = 5
        # --加载所有高级参数
        GEN.COM("chklist_cupd,chklist=adetch,nact=%s,params=((pp_layer=%s)(pp_min_spacing=%s)(pp_select=)%s),"
                "mode=regular" % (ip_index, '\;'.join(ip_layers), pad2line, ParM))
        GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=min_spacing_trace_to_pad,value=%s,options=0"
                % (ip_index, pad2line))
        GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=min_spacing_trace_to_trace,value=%s,options=0"
                % (ip_index, spcValue))
        # === 补偿区间的间距控制 ===
        for x in range(1, inn_param_num + 1):
            for y in range(x, inn_param_num + 1):
                GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=min_spacing_%s_%s,value=%s,options=0"
                        % (ip_index, x, y, spcValue))

        GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=min_spacing_surface_to_trace,value=%s,options=0"
                % (ip_index, spcValue))
        # == 不忽略属性 ==
        GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=omit_feature_attr,value=,options=0" % (ip_index))
        GEN.COM("top_tab,tab=Checklists")
        GEN.COM("chklist_open,chklist=adetch")
        GEN.COM("chklist_show,chklist=adetch,nact=%s,pinned=yes,pinned_enabled=yes" % ip_index)
        GEN.COM("show_tab,tab=Checklists,show=yes")
        GEN.COM("top_tab,tab=Checklists")
        GEN.CLEAR_LAYER()

    def sec1_etch_set(self, ip_index, ip_layers, ip_dict):
        selMaxLine = ip_dict['selMaxLine']
        spcValue = ip_dict['space_control']
        normal_etchFile = ip_dict['normal_etch_file']
        single_etchFile = ip_dict['single_etch_file']
        diff_etchFile = ip_dict['double_etch_file']
        normal_post_file = ip_dict['normal_post_file']
        if ip_dict['pad2line']:
            pad2line = float(ip_dict['pad2line']) + 0.01
        else:
            pad2line = spcValue
        GEN.CHANGE_UNITS('inch')
        GEN.CLEAR_LAYER()
        for wk_lay in ip_layers:
            GEN.AFFECTED_LAYER(wk_lay, 'yes')
            # == 删除动补属性的物件 ==
            GEN.FILTER_RESET()
            GEN.COM('adv_filter_reset, filter_name = popup')
            GEN.FILTER_SET_ATR_SYMS('.detch_comp')
            GEN.FILTER_SELECT()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_DELETE()
            GEN.FILTER_RESET()
            GEN.COM('adv_filter_reset, filter_name = popup')
            # == 删除层别中已定义的属性 .bit
            GEN.COM('sel_delete_atr,mode=list,attributes=.bit,attr_vals=etchline<=%smil' % selMaxLine)
            GEN.COM("adv_filter_reset")
            GEN.FILTER_RESET()
            # == 动补前备份层别 ==
            tmp_value = "etch-"
            bak_layer = '%s%s' % (tmp_value, wk_lay)
            GEN.VOF()
            GEN.DELETE_LAYER(bak_layer)
            GEN.VON()
            GEN.SEL_COPY(bak_layer)
            GEN.CLEAR_LAYER()
        GEN.CLEAR_LAYER()
        for wk_lay in ip_layers:
            GEN.AFFECTED_LAYER(wk_lay, 'yes')
        # === 选择影响层补偿范围内的线 ====
        GEN.COM("reset_filter_criteria,filter_name=,criteria=all")
        GEN.COM("set_filter_type,filter_name=,lines=yes,pads=no,surfaces=no,arcs=yes,text=yes")
        GEN.COM("set_filter_polarity,filter_name=,positive=yes,negative=no")
        GEN.COM("reset_filter_criteria,filter_name=,criteria=profile")
        GEN.COM("reset_filter_criteria,filter_name=popup,criteria=inc_attr")
        GEN.COM("reset_filter_criteria,filter_name=popup,criteria=exc_attr")
        # change 2-->0.1
        GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=no,symbols=r0.1:r%s;s0.1:s%s" % (selMaxLine,selMaxLine))
        GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=yes,symbols=")
        GEN.COM("reset_filter_criteria,filter_name=,criteria=text")
        GEN.COM("reset_filter_criteria,filter_name=,criteria=dcode")
        GEN.COM("reset_filter_criteria,filter_name=,criteria=net")
        GEN.COM("set_filter_length")
        GEN.COM("set_filter_angle")
        GEN.COM("adv_filter_reset")
        GEN.COM("filter_area_strt")
        GEN.COM("filter_area_end,filter_name=popup,operation=select")
        if int(GEN.GET_SELECT_COUNT()) > 0:
            list_attri = [".patch", ".imp_line", ".imp_info", ".tear_drop", ".sliver_fill"]
            for attr in list_attri:
                GEN.COM("reset_filter_criteria, filter_name = popup , criteria = exc_attr")
                GEN.COM("reset_filter_criteria, filter_name = popup, criteria = inc_attr")
                GEN.COM("set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=no,attribute=%s,"
                        "min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=" % (attr))
                GEN.COM("set_filter_and_or_logic, filter_name = , criteria = inc_attr, logic = and")
                GEN.COM("filter_area_strt")
                GEN.COM("filter_area_end,filter_name=popup,operation=unselect")
        if int(GEN.GET_SELECT_COUNT()) > 0:
            # === 不直接运行checklist，改为设定属性，进行多种属性线同时补偿
            addBit = 'etchline<=%smil' % selMaxLine
            GEN.COM('cur_atr_reset')
            GEN.COM('cur_atr_set,attribute=.bit,text=%s' % addBit)
            GEN.COM('sel_change_atr,mode=add')

        # === 2020.11.25 大于最大动补线路的线也需补偿 ===
        # === 选择影响层补偿范围内的线 ====
        GEN.COM("reset_filter_criteria,filter_name=,criteria=all")
        GEN.COM("set_filter_type,filter_name=,lines=yes,pads=no,surfaces=no,arcs=yes,text=yes")
        GEN.COM("set_filter_polarity,filter_name=,positive=yes,negative=no")
        GEN.COM("reset_filter_criteria,filter_name=,criteria=profile")
        GEN.COM("reset_filter_criteria,filter_name=popup,criteria=inc_attr")
        GEN.COM("reset_filter_criteria,filter_name=popup,criteria=exc_attr")
        # change 2-->0.1 === 2020.11.25 不包含此区间
        GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=yes,symbols=r0.1:r%s;s0.1:s%s" % (selMaxLine,selMaxLine))
        GEN.COM("reset_filter_criteria,filter_name=,criteria=text")
        GEN.COM("reset_filter_criteria,filter_name=,criteria=dcode")
        GEN.COM("reset_filter_criteria,filter_name=,criteria=net")
        GEN.COM("set_filter_length")
        GEN.COM("set_filter_angle")
        GEN.COM("adv_filter_reset")
        GEN.COM("filter_area_strt")
        GEN.COM("filter_area_end,filter_name=popup,operation=select")
        if int(GEN.GET_SELECT_COUNT()) > 0:
            list_attri = [".patch", ".imp_line", ".imp_info", ".tear_drop", ".sliver_fill"]
            for attr in list_attri:
                GEN.COM("reset_filter_criteria, filter_name = popup , criteria = exc_attr")
                GEN.COM("reset_filter_criteria, filter_name = popup, criteria = inc_attr")
                GEN.COM("set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=no,attribute=%s,"
                        "min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=" % (attr))
                GEN.COM("set_filter_and_or_logic, filter_name = , criteria = inc_attr, logic = and")
                GEN.COM("filter_area_strt")
                GEN.COM("filter_area_end,filter_name=popup,operation=unselect")
        if int(GEN.GET_SELECT_COUNT()) > 0:
            # === 不直接运行checklist，改为设定属性，进行多种属性线同时补偿
            addBit2 = 'etchline>%smil' % selMaxLine
            GEN.COM('cur_atr_reset')
            GEN.COM('cur_atr_set,attribute=.bit,text=%s' % addBit2)
            GEN.COM('sel_change_atr,mode=add')

        # == 进行三个区间进行直接动补，具有.bit属性的一般线路
        # --参数一：普通线
        pp_feature1 = 'Traces'
        # --参数二：板内特性阻抗线
        pp_feature2 = 'Traces'
        # --参数三：板内差分阻抗线
        pp_feature3 = 'Traces'
        # --定义Etch comp functions里的参数
        # == 优先级数字越小，级别越高 == note by song 2020.05.23
        # == 补偿优先级 差分>特性>一般线路
        parm1 = "(pp_feature1=%s)(pp_attr1=.bit = %s)(pp_func1=%s)(pp_func_w1=.zero)(pp_priority1=4)" \
                "(pp_method1=Contour-based patch)" % (pp_feature1, 'etchline<=%smil' % selMaxLine, normal_etchFile)
        parm2 = "(pp_feature2=%s)(pp_attr2=.imp_type=single-ended)(pp_func2=%s)(pp_func_w2=.zero)(pp_priority2=3)" \
                "(pp_method2=Contour-based patch)" % (pp_feature2, single_etchFile)
        parm3 = "(pp_feature3=%s)(pp_attr3=.imp_type=differential)(pp_func3=%s)(pp_func_w3=.zero)(pp_priority3=2)" \
                "(pp_method3=Contour-based patch)" % (pp_feature3, diff_etchFile)
        parm4 = "(pp_feature4=%s)(pp_attr4=.imp_type=single-ended coplanar)(pp_func4=%s)(pp_func_w4=.zero)(pp_priority4=5)" \
                "(pp_method4=Contour-based patch)" % (pp_feature2, single_etchFile)
        parm5 = "(pp_feature5=%s)(pp_attr5=.imp_type=differential coplanar)(pp_func5=%s)(pp_func_w5=.zero)(pp_priority5=6)" \
                "(pp_method5=Contour-based patch)" % (pp_feature2, diff_etchFile)
        parm6 = "(pp_feature6=%s)(pp_attr6=.bit = %s)(pp_func6=%s)(pp_func_w6=.zero)(pp_priority6=7)" \
                "(pp_method6=Contour-based patch)" % (pp_feature1, 'etchline>%smil' % selMaxLine, normal_post_file)
        parm7 = "(pp_feature7=%s)(pp_attr7=.imp_line;.imp_info;.patch)(pp_func7=%s)(pp_func_w7=.zero)(pp_priority7=8)" \
                "(pp_method7=Contour-based patch)" % (pp_feature3, diff_etchFile)
        
        ParM = parm1 + parm2 + parm3 + parm4 + parm5 + parm6 + parm7
        self.logdict['copy_files'].append(normal_etchFile)
        self.logdict['copy_files'].append(single_etchFile)
        self.logdict['copy_files'].append(diff_etchFile)
        self.logdict['copy_files'].append(normal_post_file)

        sec1_param_num = 6
        # --加载所有高级参数
        GEN.COM("chklist_cupd,chklist=adetch,nact=%s,params=((pp_layer=%s)(pp_min_spacing=%s)(pp_select=)%s),"
                "mode=regular" % (ip_index, '\;'.join(ip_layers), pad2line, ParM))
        GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=min_spacing_trace_to_pad,value=%s,options=0"
                % (ip_index, pad2line))
        GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=min_spacing_trace_to_trace,value=%s,options=0"
                % (ip_index, spcValue))
        # === 补偿区间的间距控制 ===
        for x in range(1, sec1_param_num + 1):
            for y in range(x, sec1_param_num + 1):
                GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=min_spacing_%s_%s,value=%s,options=0"
                        % (ip_index, x, y, spcValue))

        GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=min_spacing_surface_to_trace,value=%s,options=0"
                % (ip_index, spcValue))
        # == 不忽略属性 ==
        GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=omit_feature_attr,value=,options=0" % ip_index)
        GEN.COM("top_tab,tab=Checklists")
        GEN.COM("chklist_open,chklist=adetch")
        GEN.COM("chklist_show,chklist=adetch,nact=%s,pinned=yes,pinned_enabled=yes" % ip_index)
        GEN.COM("show_tab,tab=Checklists,show=yes")
        GEN.COM("top_tab,tab=Checklists")
        GEN.CLEAR_LAYER()

    def sec_etch_set(self, ip_index, ip_layers, ip_dict, show_range=None):
        """
        次外层动态补偿checklist设定及层别处理
        :param ip_index:
        :param ip_layers:
        :param ip_dict:
        :param show_range: 动补区间，由于0.6-0.8，0.8-1.0的区间需要区分线到线、线到pad为不同值，传入此值用于判断
        :return:
        """
        selMaxLine = ip_dict['selMaxLine']
        selMidLine = 8.0
        spcValue = float(str(ip_dict['space_control'])) + 0.01
        line2line = float(ip_dict['line2line'])
        line2cu = float(ip_dict['line2cu'])
        # if show_range in ['0.6<=C<0.8']:
        #     line2line = 1.6 + 0.01
        # elif show_range in ['0.8<=C<1.0']:
        #     line2line = 1.77 + 0.01
        normal_etchFile = ip_dict['normal_etch_file']
        single_etchFile = ip_dict['single_etch_file']
        diff_etchFile = ip_dict['double_etch_file']
        # V3.4 单线、差分以及共面使用同一个动补参数
        imp_etch_file = single_etchFile
        if ip_dict['pad2line']:
            pad2line = float(ip_dict['pad2line']) + 0.01
        else:
            pad2line = spcValue
        GEN.CHANGE_UNITS('inch')
        GEN.CLEAR_LAYER()
        for wk_lay in ip_layers:
            GEN.AFFECTED_LAYER(wk_lay, 'yes')
            # == 删除动补属性的物件 ==
            GEN.FILTER_RESET()
            GEN.COM('adv_filter_reset, filter_name = popup')
            GEN.FILTER_SET_ATR_SYMS('.detch_comp')
            GEN.FILTER_SELECT()
            GEN.COM('adv_filter_reset, filter_name = popup')
            # -->.smd属性物件不选择 AresHe 2020-6-19
            GEN.FILTER_SET_ATR_SYMS('.smd')
            GEN.FILTER_SELECT(op='unselect')
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_DELETE()

            GEN.FILTER_RESET()
            GEN.COM('adv_filter_reset, filter_name = popup')
            # == 删除层别中已定义的属性 .bit
            # === TODO 增加类似外层补偿的，区分5mil以上即5mil以下的线
            # GEN.COM('sel_delete_atr,mode=list,attributes=.bit,attr_vals=etchline<=%smil' % selMaxLine)
            GEN.COM('sel_delete_atr,mode=list,attributes=.bit,attr_vals=etchline*')
            GEN.COM('sel_delete_atr,mode=list,attributes=.bit\;.bit\;.bit,attr_vals='
                    'etchline<%s_%smil>\;etchline<=%smil\;etchline<=%smil' % (
                    selMidLine, selMaxLine, selMidLine, selMaxLine))
            GEN.COM("adv_filter_reset")
            GEN.FILTER_RESET()
            # == 动补前备份层别 ==
            tmp_value = "etch-"
            bak_layer = '%s%s' % (tmp_value, wk_lay)
            GEN.VOF()
            GEN.DELETE_LAYER(bak_layer)
            GEN.VON()
            GEN.SEL_COPY(bak_layer)
            GEN.CLEAR_LAYER()
        GEN.CLEAR_LAYER()
        for wk_lay in ip_layers:
            GEN.AFFECTED_LAYER(wk_lay, 'yes')
        # === 2022.06.08 重写过滤语句 ===
        # === 5~15mil的线设定属性 ===
        GEN.COM('reset_filter_criteria,filter_name=,criteria=all')
        GEN.COM('set_filter_type,filter_name=,lines=yes,pads=no,surfaces=no,arcs=yes,text=yes')
        GEN.COM('set_filter_polarity,filter_name=,positive=yes,negative=no')
        GEN.COM('reset_filter_criteria,filter_name=,criteria=profile')
        GEN.COM('reset_filter_criteria,filter_name=popup,criteria=inc_attr')
        GEN.COM('reset_filter_criteria,filter_name=popup,criteria=exc_attr')
        list_attri = [".patch", ".imp_line", ".imp_info", ".tear_drop", ".sliver_fill"]
        for attr in list_attri:
            GEN.COM('set_filter_attributes,filter_name=popup,exclude_attributes=yes,condition=no,attribute=%s,'
                    'min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=' % attr)
        GEN.COM('set_filter_and_or_logic,filter_name=popup,criteria=exc_attr,logic=or')
        # GEN.COM('set_filter_symbols,filter_name=,exclude_symbols=no,symbols=')
        # === 使用线宽进行过滤（使用高级过滤器，无法选中到弧） ===
        GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=no,symbols=r%s:r%s;s%s:s%s" % (selMidLine,selMaxLine,selMidLine,selMaxLine))

        GEN.COM('set_filter_symbols,filter_name=,exclude_symbols=yes,symbols=')
        GEN.COM('reset_filter_criteria,filter_name=,criteria=text')
        GEN.COM('reset_filter_criteria,filter_name=,criteria=dcode')
        GEN.COM('reset_filter_criteria,filter_name=,criteria=net')
        GEN.COM('set_filter_length')
        GEN.COM('set_filter_angle')
        GEN.COM('adv_filter_reset')
        # GEN.COM('adv_filter_set,filter_name=popup,active=yes,limit_box=no,bound_box=yes,min_width=%s,max_width=%s,'
        #         'min_length=0,max_length=0,srf_values=no,srf_area=no,mirror=any,ccw_rotations=' %
        #         (float(selMidLine) * 0.001, float(selMaxLine) * 0.001))
        GEN.COM('filter_area_strt')
        GEN.COM('filter_area_end,filter_name=popup,operation=select')

        if int(GEN.COMANS) > 0:
            # === 不直接运行checklist，改为设定属性，进行多种属性线同时补偿
            addBit = 'etchline<%s_%s>mil' % (selMidLine, selMaxLine)
            GEN.COM('cur_atr_reset')
            GEN.COM('cur_atr_set,attribute=.bit,text=%s' % addBit)
            GEN.COM('sel_change_atr,mode=add')
        # === <=5mil的线设定属性 ===
        GEN.COM('reset_filter_criteria,filter_name=,criteria=all')
        GEN.COM('set_filter_type,filter_name=,lines=yes,pads=no,surfaces=no,arcs=yes,text=yes')
        GEN.COM('set_filter_polarity,filter_name=,positive=yes,negative=no')
        GEN.COM('reset_filter_criteria,filter_name=,criteria=profile')
        GEN.COM('reset_filter_criteria,filter_name=popup,criteria=inc_attr')
        GEN.COM('reset_filter_criteria,filter_name=popup,criteria=exc_attr')
        list_attri = [".patch", ".imp_line", ".imp_info", ".tear_drop", ".sliver_fill"]
        for attr in list_attri:
            GEN.COM('set_filter_attributes,filter_name=popup,exclude_attributes=yes,condition=no,attribute=%s,'
                    'min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=' % attr)
        GEN.COM('set_filter_and_or_logic,filter_name=popup,criteria=exc_attr,logic=or')
        # GEN.COM('set_filter_symbols,filter_name=,exclude_symbols=no,symbols=')
        # === 使用线宽进行过滤（使用高级过滤器，无法选中到弧） ===
        GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=no,symbols=r0.1:r%s;s0.1:s%s" % (selMidLine,selMidLine))

        GEN.COM('set_filter_symbols,filter_name=,exclude_symbols=yes,symbols=')
        GEN.COM('reset_filter_criteria,filter_name=,criteria=text')
        GEN.COM('reset_filter_criteria,filter_name=,criteria=dcode')
        GEN.COM('reset_filter_criteria,filter_name=,criteria=net')
        GEN.COM('set_filter_length')
        GEN.COM('set_filter_angle')
        GEN.COM('adv_filter_reset')
        # GEN.COM('adv_filter_set,filter_name=popup,active=yes,limit_box=no,bound_box=yes,min_width=0,max_width=%s,'
        #         'min_length=0,max_length=0,srf_values=no,srf_area=no,mirror=any,ccw_rotations=' % (
        #                     float(selMidLine) * 0.001))
        GEN.COM('filter_area_strt')
        GEN.COM('filter_area_end,filter_name=popup,operation=select')

        if int(GEN.COMANS) > 0:
            # === 不直接运行checklist，改为设定属性，进行多种属性线同时补偿
            addBit = 'etchline<=%smil' % selMidLine
            GEN.COM('cur_atr_reset')
            GEN.COM('cur_atr_set,attribute=.bit,text=%s' % addBit)
            GEN.COM('sel_change_atr,mode=add')

        # == 进行三个区间进行直接动补，具有.bit属性的一般线路
        # --参数一：普通线
        pp_feature1 = 'Traces'
        # --参数二：板内特性阻抗线
        pp_feature2 = 'Traces'
        # --参数三：板内差分阻抗线
        pp_feature3 = 'Traces'
        # --定义Etch comp functions里的参数
        # == 优先级数字越小，级别越高 == note by song 2020.05.23
        # == 补偿优先级 差分>特性>一般线路
        parm1 = "(pp_feature1=%s)(pp_attr1=.bit = %s)(pp_func1=%s)(pp_func_w1=.zero)(pp_priority1=3)" \
                "(pp_method1=%s)" % (pp_feature1, 'etchline<=%smil' % selMidLine, normal_etchFile, self.compMethod)
        # parm2 = "(pp_feature2=%s)(pp_attr2=.imp_type=single-ended)(pp_func2=%s)(pp_func_w2=.zero)(pp_priority2=2)" \
        #         "(pp_method2=%s)" % (pp_feature2, single_etchFile, self.compMethod)
        # parm3 = "(pp_feature3=%s)(pp_attr3=.imp_type=differential)(pp_func3=%s)(pp_func_w3=.zero)(pp_priority3=1)" \
        #         "(pp_method3=%s)" % (pp_feature3, diff_etchFile, self.compMethod)
        parm2 = "(pp_feature2=%s)(pp_attr2=.imp_line;.imp_info;.patch)(pp_func2=%s)(pp_func_w2=.zero)(pp_priority2=5)" \
                "(pp_method2=%s)" % (pp_feature2, imp_etch_file, self.compMethod)
        # parm3 = "(pp_feature3=%s)(pp_attr3=.imp_type=differential)(pp_func3=%s)(pp_func_w3=.zero)(pp_priority3=1)" \
        #         "(pp_method3=%s)" % (pp_feature3, diff_etchFile, self.compMethod)
        parm4 = "(pp_feature4=%s)(pp_attr4=.bit = %s)(pp_func4=%s)(pp_func_w4=.zero)(pp_priority4=4)" \
                "(pp_method4=%s)" % (pp_feature1, 'etchline<%s_%s>mil' % (selMidLine, selMaxLine), normal_etchFile, self.compMethod)
        parm5 = "(pp_feature5=Pads)(pp_attr5=.pth_pad)(pp_func5=.zero)(pp_func_w5=.zero)(pp_priority5=10)(pp_method5=None)"
        parm6 = "(pp_feature6=Pads)(pp_attr6=.via_pad)(pp_func6=.zero)(pp_func_w6=.zero)(pp_priority6=10)(pp_method6=None)"
        parm7 = "(pp_feature7=Surfaces)(pp_attr7=.surface)(pp_func7=.zero)(pp_func_w7=.zero)(pp_priority7=10)(pp_method7=None)"

        ParM = ''
        if normal_etchFile:
            ParM += parm1
            self.logdict['copy_files'].append(normal_etchFile)

        if single_etchFile:
            ParM += parm2
            self.logdict['copy_files'].append(single_etchFile)

        # if diff_etchFile:
        #     ParM += parm3
        #     self.logdict['copy_files'].append(diff_etchFile)
        ParM += parm4 + parm5 + parm6 + parm7
        # sec_param_num = 3
        sec_param_num = 7
        # --加载所有高级参数
        GEN.COM("chklist_cupd,chklist=adetch,nact=%s,params=((pp_layer=%s)(pp_min_spacing=%s)(pp_select=)%s),"
                "mode=regular" % (ip_index, '\;'.join(ip_layers), pad2line, ParM))
        GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=min_spacing_trace_to_pad,value=%s,options=0"
                % (ip_index, pad2line))
        GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=min_spacing_trace_to_trace,value=%s,options=0"
                % (ip_index, line2line))
        GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=min_spacing_surface_to_trace,value=%s,options=0"
                % (ip_index, line2cu))
        # === 补偿区间的间距控制 ===
        for x in range(1, sec_param_num + 1):
            for y in range(x, sec_param_num + 1):
                set_space = line2line
                if x == 4:
                    set_space = line2line + 0.2

                GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=min_spacing_%s_%s,value=%s,options=0"
                        % (ip_index, x, y, set_space))
                # === 此处屏蔽，目的是差分与差分间距暂时按line2line管控，由于间距3mil以上才补偿，低区间暂不会出现多补偿情况
                # if x == 3 and y == 3:
                #     GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=min_spacing_%s_%s,value=%s,options=0"
                #             % (ip_index, x, y, self.diff2diff))

        GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=min_spacing_surface_to_trace,value=%s,options=0"
                % (ip_index, spcValue))
        # == 不忽略属性 ==
        GEN.COM("chklist_erf_variable,chklist=adetch,nact=%s,variable=omit_feature_attr,value=,options=0" % ip_index)

        GEN.COM("top_tab,tab=Checklists")
        GEN.COM("chklist_open,chklist=adetch")
        GEN.COM("chklist_show,chklist=adetch,nact=%s,pinned=yes,pinned_enabled=yes" % ip_index)
        GEN.COM("show_tab,tab=Checklists,show=yes")
        GEN.COM("top_tab,tab=Checklists")
        GEN.CLEAR_LAYER()

    def getJOB_steps(self):
        """
        从JOB中获取step列表，并返回两个列表，一个所有step列表，一个需要默认选择的列表
        :return: list,list
        """
        usefulSteps, defaultSel = [], []
        for gsl in GEN.GET_STEP_LIST():
            if gsl == "": continue
            searchObj = re.search(r'^(org|orig|panel|net|drl|lp|2nd|fa|coupon-cp|\s+)', gsl, re.M | re.I)
            # --需要显示在列表中的step名
            if not searchObj:
                usefulSteps.append(gsl)
                # --需要默认选择的step
                if re.search(r'(edit)', gsl, re.M | re.I):
                    defaultSel.append(gsl)
        # --返回两个数组
        return usefulSteps, defaultSel

    def writeLog(self):
        detchDir = os.environ['INCAM_SERVER'] + '/site_data/frontline_prog/dfm/detch.fnc/'
        # user_dir = os.environ['JOB_USER_DIR']
        # 在user文件夹创建动补文件夹，用于存放调用的参数 格式为实际动补参数-日期时间
        userDetchDir = os.environ['JOB_USER_DIR'] + '/detch.fnc'
        if not os.path.exists(userDetchDir):
            os.mkdir(userDetchDir)
        current_time = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())
        current_time1 = time.strftime("%Y%m%d%H%M%S", time.localtime())
        print json.dumps(self.logdict, indent=2)
        for etch_file in self.logdict['copy_files']:
            mycopyfile(detchDir + '/' + etch_file, userDetchDir + '/' + etch_file + '_' + current_time)

        stat_file = os.path.join(userDetchDir, 'detch_log_%s.json' % (current_time1))
        fd = open(stat_file, 'w')
        json.dump(self.logdict, fd, ensure_ascii=False, indent=4, separators=(', ', ': '), sort_keys=True)
        fd.close()

    # def write_file(self):
    #     """
    #     用json把参数字典直接写入user文件夹中的panel_parameter.json
    #     json_str = json.dumps(self.parm)将字典dump成string的格式
    #     :return:
    #     :rtype:
    #     """
    #     # 将收集到的数据以json的格式写入user/param
    #     stat_file = os.path.join(self.userDir, 'panel_parameter.json')
    #     fd = open(stat_file, 'w')
    #     json.dump(self.parm, fd, ensure_ascii=False, indent=4, separators=(', ', ': '), sort_keys=True)
    #     fd.close()

    # def read_file(self):
    #     """
    #     用json从user文件夹中的panel_parameter.json中读取字典
    #     :return:
    #     :rtype:
    #     """
    #     json_dict = {}
    #     stat_file = os.path.join(self.userDir, 'panel_parameter.json')
    #     if os.path.exists(stat_file):
    #         fd = open(stat_file,'r')
    #         json_dict = json.load(fd)
    #         fd.close()
    #     return json_dict


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MainWindowShow()
    myapp.show()
    app.exec_()
    sys.exit(0)

'''

# 2020.05.15
# Song 
# 临时方案，修改孔到铜
# 
# V2.2
# Song
# 1.界面增加via to cu，pth  to cu ,npth to cu 选项；
# 2.后台checklist增加此类值写入；


# V2.3
# Song
# 使用参数 etch_data-hdi1-inn_v20200611.txt
# 增加2oz以上的管控值

# V2.4
# Song
# 2020.08.14
# 稀疏区的判定更改为：稀疏区-0.5补偿值 --> 稀疏区 3.0
# 间距管控由3.01更改为2.51
#


# V2.5
# Song
# 2020.09.09
# 1.增加共面阻抗动态补偿

# V2.5.1
# Song
# 2020.09.11
# 1.共面阻抗的间距控制

# 2020.11.11
# 补充日志，未知时间，内一补偿增加
# http://192.168.2.120:82/zentao/story-view-2297.html

# 3.0.1
# Song
# 2020.12.21
# 1.动补前，drl的via孔变为pth，动补后还原drl的via属性;

# 3.0.2
# Song
# 2020.12.22
# 1.增加step选择


# 3.0.3
# Song
# 2020.12.24
# 1.取消界面勾选项目 

# 3.1
# Song
# 2021.02.02
# 更改内一层判断逻辑，无镭射的才为内一 

# 3.1.1
# Song
# 2021.02.04
# 界面更改，table里面的层别名不可编辑 （闯哥提供的解决方案）

# # http://192.168.2.120:82/zentao/story-view-2732.html

# 3.2.0
# Song
# 2022.04.01
# 1.增加与干膜相关的二列，隐藏配置参数列
# 2.内层inn类型，增加是否2/2线路类型的选择，用于单独定义pad to line 1.4mil
# 3.内层sec1及sec类型，如果铜厚在25um以下，则pad to line列增加1.4mil间距
# http://192.168.2.120:82/zentao/story-view-4084.html
# 4. 更新了Oracle_DB的包，增加了层别信息的获取


# 3.2.1
# Song
# 2022.04.18
# 1.动补时排除导气层的影响；http://192.168.2.120:82/zentao/story-view-4173.html
# 2.次外层在指定干膜类型中的解析度，取按规范中定义及解析度较大值。http://192.168.2.120:82/zentao/story-view-4173.html
# 3.层别类型 inn sec sec1 out的类型判断，变更为根据流程判断，可能存在MRP_NAME相同的情况，增加判断并预警；
# http://192.168.2.120:82/zentao/story-view-4199.html


# 3.2.2
# Song
# 2022.06.09
# 1.层别中存在方端线，增加线宽过滤时s开头的线路大小过滤方法：975-192A1 --> L5层
http://192.168.2.120:82/zentao/story-view-4345.html 

# 3.3
# Song
# 2022.06.15
# 1.外层准则变更：
# 1.1 更改补偿区间间距，更新etch_data-hdi1-out.csv
# 1.2 次外层外，细分pad2line
# 1.3 增加次外层外5mil的分界线
# 1.4 
http://192.168.2.120:82/zentao/story-view-4346.html
# 2022.07.19 增加sec（次外层外）干膜解析度对line2line，line2cu的约束条件

# V3.4
# song 
# 上线日期：2022.10.19
# 外层准则变更 http://192.168.2.120:82/zentao/story-view-4458.html

# V3.5
# song 
# 开发日期：2022.11.21 上线日期：2022.11.23
# 内层可更改孔到铜数据 http://192.168.2.120:82/zentao/story-view-4267.html

# V3.6
# Chao.Song
# 开发日期：2022.12.13 上线日期：2022.12.15
# 增加次外层在内层补偿&动补的程序
# http://192.168.2.120:82/zentao/story-view-4977.html

# V3.7
# Chao.Song
# 开发日期：2023.01.09 上线日期：None
# 增加内层动补对内层距离的管控
# http://192.168.2.120:82/zentao/story-view-5032.html
'''
