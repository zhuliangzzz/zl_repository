#!/bin/python
# -*- coding: utf-8 -*-
import os
import platform
import sys
import time
import re

reload(sys)
sys.setdefaultencoding('utf8')
import xlsxwriter
import xlwt

# sys.path.append('/incam/server/site_data/scripts/pythondir/')
# import genClasses
os.environ['GENESIS_DIR'] = '/frontline/incam'
os.environ['GENESIS_EDIR'] = '/frontline/incam/release'
os.environ['GENESIS_TMP'] = '/tmp'

# --加载相对位置，以实现InCAM与Genesis共用
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"D:/pyproject/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
    sys.path.append('/incam/server/site_data/scripts/pythondir/')

from xlrd import open_workbook
from xlutils.copy import copy
import gClasses
from copyfile import *
import json
import genCOM_26 as genCOM
from genesisPackages import innersignalLayers, outsignalLayers, tongkongDrillLayer, \
    laser_drill_layers, mai_drill_layers, ksz_layers
from create_ui_model import showMessageInfo, app
from drc_ui_183 import Ui_MainWindow
from PyQt4 import QtCore,QtGui
from PyQt4.QtGui import QMainWindow, QTableWidgetItem
from connect_database_all import MySql, InPlan



class Window(QMainWindow,Ui_MainWindow):
    def __init__(self, data, get_dict):
        super(Window,self).__init__()
        self.data = data
        self.dict = get_dict
        self.initUI()
        self.set_table()
        self.pushButton.clicked.connect(exit)

    def initUI(self):
        self.setupUi(self)
        self.setWindowTitle(u"分析结果")
        self.resize(450, 600)
        # self.setFixedSize(self.width(), self.height())
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

    def set_table(self):
        font = QtGui.QFont()
        font.setPointSize(11)
        table = self.tableWidget
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setVisible(False)
        add_list = [u'镭射-PTH孔',
                    u'镭射-NPTH孔',
                    u'埋孔-埋孔',
                    u'PTH-PTH',
                    u'PTH-NPTH孔',
                    u'地线-板边',
                    u'信号线-板边',
                    u'线宽（外层）',
                    u'线距（外层）',
                    u'线宽（内层）',
                    u'线距（内层）',
                    u'阻抗线宽',
                    u'镭射PAD间距',
                    u'盲孔PAD-rout',
                    u'埋孔-rout',
                    u'VIA孔径',
                    u'埋孔孔环ring',
                    u'通孔孔环ring'
                    ]
        count = len(add_list)
        table.setRowCount(count)
        table.setColumnCount(4)
        table.setColumnWidth(0 ,120)
        table.setColumnWidth(1, 101)
        table.setColumnWidth(2, 102)
        for i , tp in enumerate(self.data):
            show_type = add_list[i]
            item = QTableWidgetItem(show_type)
            item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
            item.setFont(font)
            table.setItem(i, 0, item)
            # 加入内容
            write_cot = str(tp[1])
            item_cot = QTableWidgetItem(write_cot)
            item_cot.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
            item_cot.setFont(font)
            table.setItem(i, 1, item_cot)
            #  写入数据
            key_val = self.dict[tp[0]]

            try:
                write_val = str(round(float(key_val), 2))
                if float(key_val) < tp[1]:
                    item_ng = QTableWidgetItem('NG')
                    item_ng.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
                    item_ng.setFont(font)
                    item_ng.setBackground(QtGui.QColor(255,0,0))
                    table.setItem(i, 3, item_ng)

            except:
                write_val = 'N/A'
            item_val = QTableWidgetItem(write_val)
            item_val.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
            item_val.setFont(font)
            table.setItem(i, 2, item_val)


class DrcCheck:
    def __init__(self):
        self.get_cost_key = ["lvia2pth", "lvia2npth","mvia2mvia", "pth2pth",
                             "pth2npth", "dline2rout", "xline2rout",
                             "outlw", "outls", "intlw", "intls", "zkline",
                             "lvpad2lvpad", "lviapad2rout", "via2rout",
                              "min_dirll_size","min_via_ar","min_pth_ar"]
        self.get_cost_dict = dict(zip(self.get_cost_key, ['N/A']*len(self.get_cost_key)))
        # self.gen = genClasses.Job(os.environ['JOB'])
        # --实例化genesis com对象
        self.GEN = genCOM.GEN_COM()
        self.job_name = os.environ.get('JOB', None)
        self.step_name = os.environ.get('STEP', None)
        self.gen = gClasses.Job(self.job_name)

        if int(self.job_name[4:6]) != len(innersignalLayers + outsignalLayers):
            showMessageInfo(u"线路层和料号中层数不匹配，请检查")
            sys.exit(0)

        # --优化掉文字层中的文字的公差（直接缩小）
        self.resizwTol = 254

        self.checklist = 'hdi-drc-183'
        self.inn_define1 = {'min_line': 1, 'min_p2p': 4, 'min_p2line': 3, 'min_l2l': 2, 'min_pth_ar': 5,
                            'min_local_spacing': 6, 'min_npth2c': 7, 'min_r2c': 8}
        self.sig_range1 = {'min_line': 2.5, 'min_p2p': 3, 'min_p2line': 3, 'min_l2l': 3, 'min_pth_ar': 3,
                           'min_local_spacing': 3, 'min_npth2c': 7, 'min_r2c': 8, 'min_via_ar': 3,
                           'min_laser_via_ar': 3, 'min_bga2bga' : 5.7, 'min_bga2c' : 3.2, 'min_smd2smd' : 3.2, 'min_smd2c' : 3.2 }

        self.drill_space = {    'min_close_lvia2pth_diff_net': 9,
                                'min_close_lvia2via_diff_net': 9,
                                'min_close_pth_diff_net': 10.5,
                                'min_close_via_diff_net': 9,
                                'min_close_lvia_diff_net': 10,
                                'min_lvia2rout': 10,
                                'min_via_to_rout___': 11.5,
                                'min_pth_to_rout___': 12,
                                'min_npth_to_rout__': 7,
                                 'min_close_via2npth_conn': 10,
                                'min_close_pth2npth_conn': 10.5,
                                'min_close_lvia2npth_conn': 8.5}

        self.inn_define2 = {'min_via_ar': 11, 'min_laser_via_ar': 1}

        self.out_define1 = {'min_line': 1, 'min_p2p': 4, 'min_p2line': 3, 'min_l2l': 2, 'min_pth_ar': 5,
                            'min_local_spacing': 6, 'min_npth2c': 7, 'min_r2c': 8,
                            'min_bga2bga': 9, 'min_bga2c': 10, 'min_smd2smd': 11, 'min_smd2c': 12}

        self.line2rout_define = {'min_r2c' : 13}
        self.line2rout_space = {'min_r2c': 8}
        self.out_define2 = {'min_laser_via_ar': 1}
        self.out_define3 = {'min_bga_pad': 7}
        self.out_define4 = {'min_bga2bga': 24, 'min_smd_pad': 25, 'min_smd2smd': 26}
        self.sm_define1 = {'min_ar_pth': 2, 'min_ar_via': 3, 'min_ar_npth': 4, 'min_ar_smd': 5, 'min_ar_pth_pad': 6,
                           'min_ar_via_pad': 7, 'min_ar_npth_pad': 8, 'min_ar_ndrl_pad': 9, 'min_pad_to_pad': 10,
                           'min_pad_to_non': 11, 'min_non_to_non': 12, 'min_coverage': 13}
        self.sm_define2 = {'typ_ar_pth': 2, 'typ_ar_via': 3, 'typ_ar_npth': 4, 'typ_ar_smd': 5, 'typ_ar_pth_pad': 6,
                           'typ_ar_via_pad': 7, 'typ_ar_npth_pad': 8, 'typ_ar_ndrl_pad': 9, 'typ_coverage': 13}
        # 考虑到input还没有制作锣带，无孔到边的数据，去除，但是有定义via 和pth孔的区别，增加 min_close_lvia2via_diff_net 和 min_close_lvia2via_same_net选项
        self.bd_define = {'min_close_pth_diff_net': 1,
                          'min_close_pth_same_net': 2,
                          'min_close_via_diff_net': 3,
                          'min_close_via_same_net': 4,
                          'min_npth_to_npth__': 5,
                          'min_close_lvia_diff_net': 6,
                          'min_close_lvia_same_net': 7,
                          'min_close_lvia2pth_diff_net': 8,
                          'min_close_lvia2pth_same_net': 9,
                          'min_close_lvia2via_diff_net': 10,
                          'min_close_lvia2via_same_net': 11,
                          'min_close_pth2npth_conn': 12,
                          'min_close_via2npth_conn': 13,
                          'min_close_lvia2npth_conn': 14,
                          'min_via_to_rout___': 15,
                          'min_npth_to_rout__': 16,
                          'min_lvia2rout': 17,
                          'min_pth_to_rout___': 18 , }
        # self.drl_define = {'min_drill_to_outline': 15}
        # 加入3个模板对应层数-行数叠加
        if int(self.job_name[4:6]) <= 10:
            xls_file = 'drc_report_10.xls'
            self.start_drill = 21
            self.start_sm = 35
            self.start_line = 40
            self.start_drl_cu = 53
            self.start_space = 66
            self.start_ar = 79
        elif 10 < int(self.job_name[4:6]) <= 16:
            xls_file = 'drc_report_16.xls'
            self.start_drill = 21
            self.start_sm = 35
            self.start_line = 40
            self.start_drl_cu = 58
            self.start_space = 76
            self.start_ar = 94
        elif 16 < int(self.job_name[4:6]) <= 24:
            xls_file = 'drc_report_24.xls'
            self.start_drill = 24
            self.start_sm = 41
            self.start_line = 46
            self.start_drl_cu = 72
            self.start_space = 100
            self.start_ar = 126
        else:
            xls_file = 'drc_report_32.xls'
            self.start_drill = 29
            self.start_sm = 52
            self.start_line = 57
            self.start_drl_cu = 91
            self.start_space = 125
            self.start_ar = 159

        xls_file = 'drc_report_183_new.xls'

        # TODO 待更改此处为当前脚本路径
        self.orgfile = '/frontline/incam/server/site_data/scripts/hdi_scr/DRC/xls/{0}'.format(xls_file)
        # TODO 待更改此处为film路径

        self.desfile = '/home/Incam/output/drc/%s/%s/DRC_REPORT-%s.xls' % (self.job_name, self.step_name, self.job_name)
        self.outputpath = '/home/Incam/output/drc/%s/%s/' % (self.job_name, self.step_name)
        if not os.path.exists(self.outputpath):
            os.makedirs(self.outputpath)
        # === 复制模板到目标路径 ===
        mycopyfile(self.orgfile, self.desfile)
        self.guser = self.GEN.getUser()

        # #按类别写excel##
        # do info 属性合集#
        self.info_result = {}
        # 分析层别合集#
        self.info_layers = {}
        self.lyr_rcrd = {}
        self.reslt_all = {}
        self.layer_num = ''
        self.result_record = {}
        self.drl2cu_record = {}
        # inn_define区间范围##
        # index 分析分类  ##
        # line起始列，层别写入#
        # side写入行#
        # === AR 字典定义 ===
        self.ar_all = {}
        # === 间距区间定义 ===
        # === 2020.10.28 更改区间 ===
        # self.spc_chk = {'l2l': [1, 3.5, 0.5, 47, 1], 'p2line': [1, 3.5, 0.5, 47, 6], 'p2p': [1, 3.5, 0.5, 47, 11],
        # 		   'via_ar': [2, 4.5, 0.5, 63, 12], 'laser_via_ar': [1, 4.5, 0.5, 63, 2]}

        self.spc_chk = {
            'l2l': [1.6, 2.0, 0.1, self.start_line, 1],
            'p2line': [1.6, 2.0, 0.1, self.start_line, 6],
            'p2p': [1.6, 2.0, 0.1, self.start_line, 11],
            'via_ar': [2, 4.5, 0.5, self.start_ar, 12],
            'laser_via_ar': [1, 4.5, 0.5, self.start_ar, 2]
        }
        self.snap_mode = ['l2l', 'p2line', 'p2p']
        rexcel = open_workbook(self.desfile, formatting_info=True)  #
        sheet = rexcel.sheets()[0]
        rows = rexcel.sheets()[0].nrows  #
        self.excel = copy(rexcel)  #
        self.table = self.excel.get_sheet(0)  #

        # #表格设置##
        borders = xlwt.Borders()
        borders.left = 1
        borders.right = 1
        borders.top = 1
        borders.bottom = 1
        borders.bottom_colour = 0x3A
        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        pattern.pattern_fore_colour = 2

        self.style = xlwt.XFStyle()
        self.style.borders = borders

        self.style1 = xlwt.XFStyle()
        self.style1.borders = borders
        self.style1.pattern = pattern

        # === 定义层别背景色 ===
        self.style_layer = xlwt.XFStyle()
        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        pattern.pattern_fore_colour = 0x33
        self.style_layer.pattern = pattern
        self.style_layer.borders = borders

        print 'x1' * 40
        self.main_run()
        print 'x2' * 40

    def main_run(self):
        # 运行前先用profile线模拟一层rout
        self.creat_routlayer()
        # === 先runchecklist
        # TODO 测试阶段，先不跑checklist
        self.run_checklist()
        # === 写入各类分析结果 ===
        self.table_set()
        # === 孔到铜写入##
        self.drl_rxls(3)
        self.drl_rxls(4)
        # 层数添加#
        self.layer_num = len(self.info_layers[3]) + len(self.info_layers[4])
        self.table.write(1, 5, self.layer_num, self.style)

        # === 收集间距点数进excel#
        self.space(3)
        self.space(4)
        # print json.dumps(self.ar_all,indent=2)
        # self.gen.PAUSE('xxxxxxxxxxxxxxxxxxxxxxxx')
        # === 写间距点数进excel#
        self.write_space_matrix_to_excel()
        # === 写入最小孔径
        self.min_holes_and_all_num()
        # 分析线到rout的距离，单独挑选
        self.write_check_l2rout_excel_new()
        # 分析盲孔PAD到rout的距离，单独挑选
        self.check_lvia_rout()

        # 分析镭射孔到镭射孔PAD之间间距
        self.check_lviapad_space()
        # 分析阻抗线宽
        self.get_imp_width()
        # === AR点数统计#
        self.ar_wrt(self.inn_define2, 3)
        self.ar_wrt(self.out_define2, 4)
        # === 写入最小BGA ===
        self.get_min_bga()

        record_dict_drill = {
            'min_close_lvia2pth_diff_net' : 'lvia2pth',
            'min_close_lvia2npth_conn': 'lvia2npth',
            'min_close_via_diff_net': 'mvia2mvia',
            'min_close_pth_diff_net': 'pth2pth',
            'min_close_pth2npth_conn': 'pth2npth',
            'min_via_to_rout___': 'via2rout'}

        for layer, dict_data in self.result_record.items():
            for key, val in dict_data.items():
                if val == "N/A":
                    continue
                if layer in laser_drill_layers + mai_drill_layers + tongkongDrillLayer:
                    if key in record_dict_drill.keys():
                        if self.get_cost_dict[record_dict_drill[key]] == "N/A":
                            self.get_cost_dict[record_dict_drill[key]] = val
                        elif float(val) < float(self.get_cost_dict[record_dict_drill[key]]):
                            self.get_cost_dict[record_dict_drill[key]] = val
                elif layer in innersignalLayers + outsignalLayers:
                    cost_key = None
                    if layer in innersignalLayers:
                        if key == 'min_line':
                            cost_key = 'intlw'
                        elif key == 'min_l2l':
                            cost_key = 'intls'
                    else:
                        if key == 'min_line':
                            cost_key = 'outlw'
                        elif key == 'min_l2l':
                            cost_key = 'outls'
                    if key == 'min_via2via':
                        cost_key = 'lvpad2lvpad'

                    elif key in ['zkline','dline2rout', 'xline2rout', 'lviapad2rout','min_via_ar','min_pth_ar']:
                        cost_key = key

                    if cost_key:
                        if self.get_cost_dict[cost_key] == "N/A":
                            self.get_cost_dict[cost_key] = val
                        elif float(val) < float(self.get_cost_dict[cost_key]):
                            self.get_cost_dict[cost_key] = val
        print self.result_record
        print self.get_cost_dict
        # 将评审结果写入excel
        send_data = self.write_cost_dict_to_excel()
        self.excel.save(self.desfile)
        # print 'x1' * 40
        # print json.dumps(self.result_record,indent=2)
        # print 'x2' * 40
        # print json.dumps (self.drl2cu_record,indent=2)
        # print 'x3' * 40

        # --当在Net里运行时，需要分析出字符中白油块的占比（当大于24%时）不允许使用喷墨流程(写入当前STEP对应的层属性供InPlanSync对接)
        if "net" in self.step_name:
            self.Analysis_Silk_SurPersent()

        if "net" not in self.step_name:
            # === 分析结果拍图 ===
            get_snap_dict = self.run_snap_in_result()
            # === excel 添加图片===
            # self.add_new_sheet('l2')
            self.add_picture_to_excel(get_snap_dict)

        self.del_tmplayer()
        # self.gen.PAUSE('ok')
        # === 打开文件夹 ===
        if "net" not in self.step_name:
            tmp_path = self.outputpath + ">& NUL &"
            os.system("nautilus " + tmp_path)



        w = Window(send_data, self.get_cost_dict)
        # 界面设置居中，改变linux时候不居中的情况
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = w.geometry()
        w.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)
        w.show()
        sys.exit(app.exec_())

    def del_tmplayer(self):
        """删除临时层"""
        for lay in outsignalLayers + innersignalLayers:
            tmp_xline = lay  + '_xline_'
            tmp_dline = lay + '_dline_'
            if self.GEN.LAYER_EXISTS(tmp_xline) == 'yes':
                self.GEN.DELETE_LAYER(tmp_xline)
            if self.GEN.LAYER_EXISTS(tmp_dline) == 'yes':
                self.GEN.DELETE_LAYER(tmp_dline)

    def get_hdi_jie(self, laser_names):
        # 计算HDI阶数
        top_hdi_list = []
        bot_hdi_list = []
        for layer in laser_names:
            num1, num2 = layer[1:].split('-')
            if int(num1) < int(num2):
                top_hdi_list.append(layer)
            else:
                bot_hdi_list.append(layer)

        top_laser_num = len(set([x.split("-")[0] for x in top_hdi_list]))
        bot_laser_num = len(set([x.split("-")[0] for x in bot_hdi_list]))
        hdi_jie = max([top_laser_num, bot_laser_num])
        return hdi_jie

    def write_cost_dict_to_excel(self):
        # 获取主板和小板类型
        inplan = InPlan(self.job_name)
        type = inplan.get_type_board()
        if type  and '主板' in type:
            small_board = False
        else:
            small_board = True
        pp_1080 = False
        # 获取PP类型
        list_data = inplan.get_ppname_type()
        if list_data:
            for dict in list_data:
                if '1080' in dict['PP名称']:
                    pp_1080 = True
        space_mvia2mvia = 10.83
        if small_board:
            outlw, intlw = 2.56, 2.56
            outls, intls = 2.95, 2.95
        else:
            outlw, intlw = 1.97, 1.57
            outls, intls = 2.36, 1.97
        if not laser_drill_layers and not mai_drill_layers:
            if int(self.job_name[4:6]) == 2:
                space_pth2pth = 13.78
            else:
                space_pth2pth = 11.81
        else:
            hdi_2j = False
            hdi_jie = self.get_hdi_jie(laser_drill_layers)
            if hdi_jie and hdi_jie > 1:
                hdi_2j = True

            if hdi_2j:
                # 2阶
                if pp_1080:
                    space_mvia2mvia = 9.84
                    space_pth2pth = 10.83
                else:
                    space_mvia2mvia = 10.83
                    space_pth2pth = 11.81
            else:
                #1阶
                space_mvia2mvia = 10.83
                space_pth2pth = 11.78
        bic_num = [7.87, 8.27, space_mvia2mvia,space_pth2pth,
                   11.02, 7.87, 11.81, outlw, outls, intlw, intls,
                   1.57,1.97,7.87,11.81,7.87,3.94,3.94]

        set_data = list(zip(self.get_cost_key, bic_num))
        for i , tp in enumerate(set_data):
            start_row = 94 + i
            write_cot = str(tp[1])
            self.table.write(start_row, 2, write_cot, self.style)
            key_val = self.get_cost_dict[tp[0]]
            style = self.style
            try:
                write_val = str(round(float(key_val), 2))
                if float(key_val) < tp[1]:
                    style = self.style1
            except:
                write_val = 'N/A'
            self.table.write(start_row, 3, write_val, style)
        return set_data

    def creat_routlayer(self):
        """
        运行前将所有inn类钻带改为非board属性
        """
        all_board_layers = self.GEN.GET_ATTR_LAYER(lay_type='drill')
        for drl in all_board_layers:
            if 'inn' in drl:
                self.GEN.COM(
                    "matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(self.job_name, drl))
        drc_rout = 'rout_drc'
        self.GEN.DELETE_LAYER(drc_rout)
        self.gen.COM('units,type=inch')
        self.GEN.COM("profile_to_rout,layer={0},width=1".format(drc_rout))
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER(drc_rout, affected='yes')
        self.GEN.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=rout".format(self.job_name, drc_rout))
        self.GEN.COM(
            "matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(self.job_name, drc_rout))
        self.GEN.CLEAR_LAYER()

    def run_checklist(self):
        # ===进行DRC分析,如没有从库中复制 === #
        # 运行前过滤部分钻带层
        self.gen.COM('top_tab,tab=Checklists')
        self.gen.VOF()
        self.gen.COM('chklist_delete,chklist=%s' % self.checklist)
        self.gen.COM('chklist_from_lib,chklist=%s,profile=none,customer=' % self.checklist)
        self.gen.COM('chklist_open,chklist=%s' % self.checklist)
        self.gen.VON()
        self.gen.COM('units,type=inch')
        self.gen.COM('zoom_home')
        self.gen.COM('chklist_show,chklist=%s,nact=1,pinned=yes,pinned_enabled=yes' % self.checklist)
        self.gen.COM('chklist_run,chklist=%s,nact=s,area=local,async_run=yes' % self.checklist)

    def table_set(self):
        """
        在表格中写入基本信息，及内层外层防焊钻孔的分析结果
        :return:
        """
        # === 使用层别循环 i##
        # === 写入用户 ===
        self.table.write(2, 1, self.guser, self.style)
        # === 写入料号名 ===
        self.table.write(1, 1, self.job_name, self.style)
        # === 写入运行时间
        tm = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.table.write(2, 9, tm, self.style)
        # === 分别取每层数值##
        self.rtxls(self.inn_define1, 3, 0, 0)
        # === 外层分析结果写入##
        self.rtxls(self.out_define1, 4, 0, 0)
        # ==== 文字分析结果写入##
        self.rtxls(self.sm_define1, 5, 0, self.start_sm)
        self.rtxls(self.sm_define2, 5, 0, self.start_sm + 1)
        # === board钻孔分析结果##
        self.rtxls(self.bd_define, 2, 0, self.start_drill)
        # 孔到边间距分析
        # self.rtxls(self.drl_define, 1, 0, self.start_drill)
        # === 孔数信息写入 ===pass
        drllyrnum = len(self.info_layers[2])
        self.table.write(2, 5, drllyrnum, self.style)
        # 写入最小的smd数据
        self.write_min_smd_size()

    def get_imp_width(self):
        # 获取阻抗线宽度
        step = gClasses.Step(self.gen, self.step_name)
        for lay in innersignalLayers+outsignalLayers:
            step.clearAll()
            step.resetFilter()
            step.affect(lay)
            step.COM("set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=no,attribute=.imp_line")
            step.selectAll()
            if step.featureSelected():
                lay_cmd = gClasses.Layer(step,lay)
                info = lay_cmd.featSelOut(units='inch')
                symbols = [float(obj.symbol[1:]) for obj in info['lines']] + [float(obj.symbol[1:]) for obj in info['arcs']]
                # === 增加数据记录 ===
                if lay in self.result_record:
                    self.result_record[lay]["zkline"] = min(symbols)
                else:
                    self.result_record[lay] = {"zkline": min(symbols)}
        step.resetFilter()
        step.clearAll()

    def check_lviapad_space(self):
        """
        获取镭射PAD到PAD的间距
        """
        job = gClasses.Job(self.job_name)
        step = gClasses.Step(job, self.step_name)

        # for layer in tongkongDrillLayer + mai_drill_layers:
        #     self.GEN.COM("matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=misc" % (self.job_name, layer))

        for laser_layer in laser_drill_layers:
            tmp_layer = laser_layer + 'tmpooo'
            step.removeLayer(tmp_layer)
            step.createLayer(tmp_layer)
            num1, num2 = str(laser_layer).replace('s', '').split('-')
            layer1,layer2 = 'l{0}'.format(num1), 'l{0}'.format(num2)
            tmp_1,tmp_2 = layer1 + 'tmpoo', layer2 + 'tmpoo'
            step.removeLayer(tmp_1)
            step.createLayer(tmp_1)
            step.removeLayer(tmp_2)
            step.createLayer(tmp_2)
            step.clearAll()
            step.resetFilter()
            step.affect(laser_layer)
            step.refSelectFilter(refLay='\\;'.join([layer1,layer2]), f_types="surface", polarity='positive', mode='disjoint')
            if step.featureSelected():
                step.copyToLayer(tmp_layer)
            step.clearAll()
            step.resetFilter()
            step.affect(layer1)
            step.filter_set(feat_types='pad', polarity='positive')
            step.refSelectFilter(tmp_layer, mode='include')
            if step.featureSelected():
                step.copyToLayer(tmp_1)

            step.clearAll()
            step.resetFilter()
            step.affect(layer2)
            step.filter_set(feat_types='pad', polarity='positive')
            step.refSelectFilter(tmp_layer, mode='include')
            if step.featureSelected():
                step.copyToLayer(tmp_2)

            step.clearAll()
            step.resetFilter()
            self.GEN.COM(
                "matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=board" % (self.job_name, tmp_1))
            self.GEN.COM(
                "matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=board" % (self.job_name, tmp_2))
            step.affect(tmp_1)
            step.affect(tmp_2)

            self.GEN.COM("chklist_run,chklist={0},nact=8,area=local,async_run=no".format(self.checklist))
            self.GEN.COM(
                "matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=misc" % (self.job_name, tmp_1))
            self.GEN.COM(
                "matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=misc" % (self.job_name, tmp_2))
            # for layer in tongkongDrillLayer + mai_drill_layers:
            #     self.GEN.COM(
            #         "matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=board" % (self.job_name, layer))
            # self.GEN.COM("chklist_run,chklist={0},nact=8,area=local,async_run=no".format(self.checklist))
            # 取出分析结果
            check_info = self.GEN.DO_INFO(
                "-t check -e %s/%s/%s -d CHK_ATTR -o action=8" % (self.job_name, self.step_name, self.checklist))

            for i, name in enumerate(check_info['gCHK_ATTRname']):
                if 'N/A' in str(check_info['gCHK_ATTRval'][i]) or not check_info['gCHK_ATTRval'][i]:
                    continue
                if re.search('l.*_min_p2p$', name):
                    key_layername = str(name.split('_')[0]).replace('tmpoo', '')
                    # === 增加数据记录 ===
                    if key_layername in self.result_record:
                        self.result_record[key_layername]["min_via2via"] = float(check_info['gCHK_ATTRval'][i])
                    else:
                        self.result_record[key_layername] = {"min_via2via": float(check_info['gCHK_ATTRval'][i])}

                else:
                    continue
        step.clearAll()
        step.resetFilter()


    def check_lvia_rout(self):
        """
        分析盲孔PAD到rout的距离
        """
        step=gClasses.Step(self.gen, self.step_name)

        for drllay in laser_drill_layers:
            tmp_layer = drllay + '_tmp_pad_oppo'
            step.removeLayer(tmp_layer)
            step.createLayer(tmp_layer)
            num1, num2 = drllay[1:].split('-')
            layer1, layer2 = 'l{0}'.format(num1), 'l{0}'.format(num2)
            step.copyLayer(self.job_name,self.step_name,drllay,tmp_layer)
            step.clearAll()
            step.affect(tmp_layer)
            step.COM("sel_resize,size=12,corner_ctl=no")
            step.clearAll()
            for lay in [layer1, layer2]:
                step.clearAll()
                step.resetFilter()
                step.affect(lay)
                step.filter_set(feat_types='pad', polarity='positive')
                step.refSelectFilter(tmp_layer, mode='cover')

                if step.featureSelected():
                    step.COM("cur_atr_set,attribute=.string,text=oppo_mpad")
                    step.COM("sel_change_atr,mode=add")
            step.removeLayer(tmp_layer)
        step.resetFilter()
        step.clearAll()
        step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=oppo_mpad")
        for sglayer in innersignalLayers + outsignalLayers:
            step.affect(sglayer)
        step.selectAll()
        step.COM("chklist_run,chklist={0},nact=9,area=local,async_run=no".format(self.checklist))
        # 取消掉属性
        step.COM("sel_delete_atr,attributes=.string")
        step.clearAll()
        step.resetFilter()
        # 取出分析结果
        check_info = self.GEN.DO_INFO(
            "-t check -e %s/%s/%s -d CHK_ATTR -o action=8" % (self.job_name, self.step_name, self.checklist))

        for i, name in enumerate(check_info['gCHK_ATTRname']):
            if 'N/A' in str(check_info['gCHK_ATTRval'][i]) or not check_info['gCHK_ATTRval'][i]:
                continue
            if re.search('l.*_min_r2c$', name):
                key_layername = name.split('_')[0]
                # === 增加数据记录 ===
                if key_layername in self.result_record:
                    self.result_record[key_layername]["lviapad2rout"] = float(check_info['gCHK_ATTRval'][i])
                else:
                    self.result_record[key_layername] = {"lviapad2rout": float(check_info['gCHK_ATTRval'][i])}

            else:
                continue

    def insert_data(self, ly, key, index):
        # 取出分析结果
        check_info = self.GEN.DO_INFO(
            "-t check -e %s/%s/%s -d CHK_ATTR -o action=%s" % (self.job_name, self.step_name, self.checklist, index))
        val = None
        for i, name in enumerate(check_info['gCHK_ATTRname']):
            if 'N/A' in str(check_info['gCHK_ATTRval'][i]) or not check_info['gCHK_ATTRval'][i]:
                continue
            if re.search('l.*_min_r2c$', name):
                val = float(check_info['gCHK_ATTRval'][i])
                # === 增加数据记录 ===
                if ly in self.result_record:
                    self.result_record[ly][key] = float(check_info['gCHK_ATTRval'][i])
                else:
                    self.result_record[ly] = {key: float(check_info['gCHK_ATTRval'][i])}

            else:
                continue

        return val

    def write_check_l2rout_excel_new(self):
        """
        分析线路到rout的距离
        """
        step = gClasses.Step(self.gen, self.step_name)
        step.clearAll()
        step.resetFilter()
        d_line , x_line = 0, 0
        d_layer, x_layer = None, None
        for layer in innersignalLayers + outsignalLayers:
                step.clearAll()
                step.resetFilter()
                step.affect(layer)
                tmp_xline = layer + '_xline_'
                tmp_dline = layer + '_dline_'
                tmp_cu = layer + '_linecu_'
                step.removeLayer(tmp_xline)
                step.removeLayer(tmp_dline)
                step.removeLayer(tmp_cu)
                step.filter_set(feat_types='surface', polarity='positive')
                step.selectAll()
                if step.featureSelected():
                    step.copyToLayer(tmp_cu)
                else:
                    continue
                step.resetFilter()
                step.selectNone()
                step.filter_set(feat_types='line;arc', polarity='positive')
                step.selectAll()
                if step.featureSelected():
                    step.copyToLayer(tmp_xline)
                step.clearAll()
                step.resetFilter()
                step.affect(tmp_cu)
                step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.detch_comp")
                step.selectAll()
                if step.featureSelected():
                    step.selectDelete()
                step.resetFilter()
                step.clearAll()
                # 区分地线和信号线
                if not step.isLayer(tmp_xline):
                    continue
                step.affect(tmp_xline)
                step.refSelectFilter(tmp_cu)
                if step.featureSelected():
                    step.moveSel(tmp_dline)
                    step.clearAll()
                    step.resetFilter()
                    step.affect(tmp_dline)
                    step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(self.job_name,tmp_dline))
                    step.COM("chklist_run,chklist={0},nact=10,area=local,async_run=no".format(self.checklist))
                    get_val = self.insert_data(layer, 'dline2rout', 10)
                    if get_val:
                        if d_line == 0 or (d_line <> 0 and get_val < d_line):
                            d_line = get_val
                            d_layer = tmp_dline

                    step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(self.job_name, tmp_dline))
                step.clearAll()
                step.resetFilter()
                step.affect(tmp_xline)
                step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(self.job_name,tmp_xline))
                step.COM("chklist_run,chklist={0},nact=7,area=local,async_run=no".format(self.checklist))
                get_val = self.insert_data(layer, 'xline2rout', 7)
                if get_val:
                    if x_line == 0 or (x_line <> 0 and get_val < x_line):
                        x_line = get_val
                        x_layer = tmp_xline
                step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(self.job_name,tmp_xline))
                step.removeLayer(tmp_cu)
        step.clearAll()
        step.resetFilter()

        #获取最小的值dline层和xline层
        for line_lay in [d_layer, x_layer]:
            if line_lay == d_layer:
                index = 10
            else:
                index = 7
            if line_lay:
                step.affect(line_lay)
                step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(self.job_name, line_lay))
                step.COM("chklist_run,chklist={0},nact={1},area=local,async_run=no".format(self.checklist, index))
                step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(self.job_name, line_lay))
                step.clearAll()

    def write_check_l2rout_excel(self):
        """
        分析线路到rout的距离
        """
        # 信号线定义属性
        step = gClasses.Step(self.gen, self.step_name)
        step.clearAll()
        step.resetFilter()

        for layer in innersignalLayers + outsignalLayers:
            step.affect(layer)
        step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=oppo_xline")
        step.selectAll()
        # step.PAUSE("11")
        if step.featureSelected():
            step.COM("chklist_run,chklist={0},nact=7,area=local,async_run=no".format(self.checklist))
            self.rtxls(self.line2rout_define, 7, 0, 0)
        else:
            for layer in innersignalLayers + outsignalLayers:
                step.clearAll()
                step.resetFilter()
                step.affect(layer)
                tmp_xline = layer + '_xline_'
                tmp_cu = layer + '_xlinecu_'
                step.filter_set(feat_types='surface', polarity='positive')
                step.selectAll()
                if step.featureSelected():
                    step.copyToLayer(tmp_cu)
                step.resetFilter()
                step.selectNone()

                step.filter_set(feat_types='line;arc', polarity='positive')
                step.selectAll()
                if step.featureSelected():
                    step.copyToLayer(tmp_xline)
                step.clearAll()
                step.resetFilter()
                step.affect(tmp_cu)
                step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.detch_comp")
                step.selectAll()
                if step.featureSelected():
                    step.selectDelete()
                step.resetFilter()
                step.clearAll()
                step.affect(tmp_xline)
                step.refSelectFilter(tmp_cu)
                if step.featureSelected():
                    step.selectDelete()
                step.clearAll()
                step.affect(layer)
                step.filter_set(feat_types='line;arc', polarity='positive')
                step.refSelectFilter(tmp_xline, mode='cover')
                if step.featureSelected():
                    step.COM("cur_atr_set,attribute=.string,text=oppo_xline")
                    step.COM("sel_change_atr,mode=add")
                step.resetFilter()
                step.removeLayer(tmp_xline)
                step.createLayer(tmp_xline)
                step.removeLayer(tmp_cu)
                step.createLayer(tmp_cu)
            step.resetFilter()
            step.clearAll()
            for layer in innersignalLayers + outsignalLayers:
                step.affect(layer)
            step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=oppo_xline")
            step.selectAll()
            if step.featureSelected():
                step.COM("chklist_run,chklist={0},nact=7,area=local,async_run=no".format(self.checklist))
                self.rtxls(self.line2rout_define, 7, 0, 0)
        step.resetFilter()
        step.clearAll()

        # self.GEN.CLEAR_LAYER()
        # self.GEN.COM("affected_filter,filter=(type=signal|power_ground&context=board)")
        # self.GEN.FILTER_RESET()
        # self.GEN.FILTER_SET_POL(pol='positive')
        # self.GEN.FILTER_SET_FEAT_TYPES(feat_types='line')
        # self.GEN.FILTER_SELECT()
        # if self.GEN.GET_SELECT_COUNT():
        #     self.GEN.COM("chklist_run,chklist={0},nact=7,area=local,async_run=no".format(self.checklist))
        #     # === SMD分析结果写入##
        #     self.rtxls(self.line2rout_define, 7, 0, 0)
        # self.GEN.CLEAR_LAYER()
        # self.GEN.FILTER_RESET()

    def write_min_smd_size(self):
        # 写入最小的SMD大小，需要排除孔内的和未开窗的
        tmp_layer = {'top': 'drc_top_smd', 'bot': 'drc_bot_smd'}
        self.GEN.DELETE_LAYER(tmp_layer['top'])
        self.GEN.DELETE_LAYER(tmp_layer['bot'])
        top_res, bot_res = False, False
        self.GEN.CLEAR_LAYER()
        self.GEN.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.smd")
        self.GEN.COM("affected_filter,filter=(type=signal&context=board&side=top)")
        self.GEN.FILTER_SELECT()
        if self.GEN.GET_SELECT_COUNT():
            self.GEN.SEL_COPY(tmp_layer['top'])
            top_res = True
        self.GEN.CLEAR_LAYER()
        self.GEN.COM("affected_filter,filter=(type=signal&context=board&side=bottom)")
        self.GEN.FILTER_SELECT()
        if self.GEN.GET_SELECT_COUNT():
            self.GEN.SEL_COPY(tmp_layer['bot'])
            bot_res = True
        self.GEN.CLEAR_LAYER()
        self.GEN.FILTER_RESET()
        info_smd = []
        for sm in ['m1', 'm2']:
            if self.GEN.LAYER_EXISTS(sm) == 'yes':
                if top_res and sm == 'm1':
                    affLayer = tmp_layer['top']
                    refLayer = 'm1'
                elif bot_res and sm == 'm2':
                    affLayer = tmp_layer['bot']
                    refLayer = 'm2'
                else:
                    continue
                self.GEN.AFFECTED_LAYER(affLayer, affected='yes')
                self.GEN.SEL_REF_FEAT(refLayer, mode='disjoint', pol='positive')
                if self.GEN.GET_SELECT_COUNT():
                    self.GEN.SEL_DELETE()
                # 去除被包含的PAD，避免误报
                self.GEN.COM("chklist_single,action=valor_dfm_nfpr,show=no")
                self.GEN.COM(
                    "chklist_cupd, chklist = valor_dfm_nfpr, nact = 1, params = ((pp_layer=.affected)(pp_delete=Covered)(pp_work=Features)"
                    "(pp_drill=PTH\;Via)(pp_non_drilled=Yes)(pp_in_selected=All)(pp_remove_mark=Remove)), mode = regular")
                self.GEN.COM("chklist_cnf_act,chklist=valor_dfm_nfpr,nact=1,cnf=no")
                self.GEN.COM("chklist_run,chklist=valor_dfm_nfpr,nact=1,area=global,async_run=no")
                info = self.GEN.DO_INFO(
                    "-t layer -e %s/%s/%s -d SYMS_HIST -p symbol" % (self.job_name, self.step_name, affLayer),
                    units='inch')['gSYMS_HISTsymbol']
                for sym in info:
                    pattern_s = '^r\d*\.\d+$|^r\d+$|^s\d*\.\d+$|^s\d+$'
                    if re.search(pattern_s, sym):
                        info_smd.append(float(sym[1:]))
                    else:
                        res = re.match(r'(rect|oval)([0-9]+.?[0-9]+?)x([0-9]+.?[0-9]+?)x?', sym)
                        if res:
                            info_smd.append(min([float(res.groups()[1]), float(res.groups()[2])]))
                self.GEN.CLEAR_LAYER()
                self.GEN.FILTER_RESET()
        self.GEN.DELETE_LAYER(tmp_layer['top'])
        self.GEN.DELETE_LAYER(tmp_layer['bot'])
        try:
            min_smd_size = min(info_smd)
            if min_smd_size < 4.0:
                cell_style = self.style1
            else:
                cell_style = self.style
            self.table.write(6, 8, str(min_smd_size), cell_style)
        except Exception as e:
            print e

    def rtxls(self, inn_define, index, line, side):
        ichk_layers = self.gen.INFO('-t check -e %s/%s/%s -d MEAS_DISP_ID -o action=%s,angle_direction=ccw'
                                    % (self.job_name, self.step_name, self.checklist, str(index)))
        inn_layers = list(set([i.split(' ')[0] for i in ichk_layers]))
        rm_layers = []
        for i in inn_layers:
            if index == 5:
                if self.gen.DO_INFO('-t layer -e %s/%s/%s -d TYPE,angle_direction=ccw' %
                                    (self.job_name, self.step_name, str(i)))["gTYPE"] == 'solder_mask':
                    pass
                else:
                    rm_layers.append(i)
            elif index == 2:
                if self.gen.DO_INFO('-t layer -e %s/%s/%s -d EXISTS,angle_direction=ccw' %
                                    (self.job_name, self.step_name, str(i)))["gEXISTS"] == 'no':
                    rm_layers.append(i)
        for k in rm_layers:
            inn_layers.remove(k)

        self.info_layers[index] = inn_layers
        inn_attr = self.gen.DO_INFO('-t check -e  %s/%s/%s -d CHK_ATTR -o action=%s, angle_direction=ccw'
                                    % (self.job_name, self.step_name, self.checklist, str(index)))
        self.info_result[index] = inn_attr

        cell_style = self.style
        if index == 3 or index == 4:
            cell_style = self.style_layer
        # side初始行#

        for layer in inn_layers:
            # === 增加数据记录 ===
            if side != 0:
                row = side
                self.table.write(row, line, layer, cell_style)
            else:
                row = int(layer.strip('l')) + self.start_line
                self.table.write(row, line, layer, cell_style)
                row2 = int(layer.strip('l')) + self.start_drl_cu
                self.table.write(row2, line, layer, cell_style)
            if re.match("^s\d{1,2}-\d{1,2}$", layer):
                try:
                    result = self.check_skip_via(layer)
                    if result == "YES":
                        style = self.style1
                    else:
                        style = cell_style
                    self.table.write(row, 19, result, style)
                except Exception, e:
                    self.gen.PAUSE(str(e))
                    pass
            for k in inn_define:
                recode_key = k
                # k为分析项目#
                # 结果表示方式#层别加结果##
                # print i
                cc = str(layer + '_' + k).strip()

                # 取值序号
                if cc in inn_attr['gCHK_ATTRname']:
                    dd = inn_attr['gCHK_ATTRname'].index(cc)
                    # #取值#
                    bb = inn_attr['gCHK_ATTRval'][dd]

                    # uu=table.cell_value(inn_define[k],3)
                    # table.write(row,inn_define[k],bb,style)
                    # print cc, dd, bb
                    # === 表格中添加数据 ===
                    sty_val = self.style
                    if bb == 'N/A':
                        pass
                    else:
                        # if index == 7:
                        #     if k in self.line2rout_space:
                        #         if k == 'min_r2c':
                        #             recode_key = 'xline2rout'
                        #         chk_vl = self.line2rout_space[k]
                        #         if float(bb) - float(chk_vl) < 0:
                        #             sty_val = self.style1
                        if index == 2:
                            dict_def = self.drill_space
                            if k in dict_def:
                                chk_vl = dict_def[k]
                                if float(bb) - float(chk_vl) < 0:
                                    sty_val = self.style1
                        else:

                            if k in self.sig_range1:
                                chk_vl = self.sig_range1[k]
                                if float(bb) - float(chk_vl) < 0:
                                    sty_val = self.style1
                    self.table.write(row, inn_define[k], bb, sty_val)
                    # === 增加数据记录 ===
                    if layer in self.result_record:
                        self.result_record[layer][recode_key] = bb
                    else:
                        self.result_record[layer] = {recode_key: bb}

            if side != 0:
                if layer == 'm1' or layer == 'm2':
                    side += 2
                else:
                    side += 1

    def check_skip_via(self, drill_layer):
        """检测skip via 中间层是否有铜"""
        job = gClasses.Job(self.job_name)
        step = gClasses.Step(job, self.step_name)
        step.open()

        index1 = int(drill_layer.split("-")[0].replace("s", ""))
        index2 = int(drill_layer.split("-")[1])
        if abs(index2 - index1) > 1:
            for index in range(abs(index2 - index1) - 1):
                siglayer = "l{0}".format(min([index1, index2]) + index + 1)
                step.clearAll()
                step.copyLayer(job.name, step.name, siglayer, siglayer + "_skip_via_tmp")
                step.clearAll()
                step.affect(siglayer + "_skip_via_tmp")
                step.COM("sel_contourize,accuracy=0.1,break_to_islands=yes,clean_hole_size=3,clean_hole_mode=x_and_y")

                step.clearAll()
                step.affect(drill_layer)
                step.resetFilter()
                step.refSelectFilter(siglayer + "_skip_via_tmp")
                if step.featureSelected():
                    step.removeLayer(siglayer + "_skip_via_tmp")
                    return "YES"

                step.removeLayer(siglayer + "_skip_via_tmp")

        step.clearAll()

        return "N/A"

    def space(self, index):
        """
        对分析结果进行点阵数据统计
        :param index:
        :return:
        """
        for allo in self.reslt_all[index]:
            line = allo.strip('\n').split(' ')
            if line[0] in self.spc_chk:
                val = int((float(line[2]) - float(self.spc_chk[line[0]][0])) / float(self.spc_chk[line[0]][2]))
                # === 增加区间为0的定义，当分析结果小于self.spc_chk中定义最小区间时，使用key 0
                # @formatter:off
                check_times = int((float(self.spc_chk[line[0]][1]) - float(self.spc_chk[line[0]][0])) / float(
                    self.spc_chk[line[0]][2]))
                # @formatter:on
                if val <= 0:
                    val = 0
                elif val > check_times:
                    # 超过统计值的总数量时，归类为最后一个区间
                    val = check_times + 1
                # print ('%sline%spc_chkline%s')%(line[2],val,line[1])
                if line[1] + '_' + line[0] not in self.ar_all:
                    self.ar_all[line[1] + '_' + line[0]] = {}
                if val in self.ar_all[line[1] + '_' + line[0]]:
                    self.ar_all[line[1] + '_' + line[0]][val] += 1
                else:
                    self.ar_all[line[1] + '_' + line[0]][val] = 1

    def write_space_matrix_to_excel(self):
        for lyr in range(1, self.layer_num + 1):
            self.table.write(lyr + self.start_space, 0, 'l' + str(lyr), self.style_layer)
            self.table.write(lyr + self.start_ar, 0, 'l' + str(lyr), self.style_layer)
            self.table.write(lyr + self.start_ar, 10, 'l' + str(lyr), self.style_layer)
            # === 区分类别 线到线，pad到线， pad到pad 增加小于最小区间，及大于最大区间算法
            add_style1 = ['l2l', 'p2line', 'p2p']
            for rr in self.spc_chk:
                range_num = round((self.spc_chk[rr][1] - self.spc_chk[rr][0]) / self.spc_chk[rr][2])
                if rr in add_style1:
                    range_num += 1
                for cc in range(range_num):
                    col = self.spc_chk[rr][4] + cc
                    each = 'l' + str(lyr) + '_' + str(rr)
                    if each in self.ar_all:
                        if re.search('p2line|l2l|p2p', each):
                            row = lyr + self.start_space
                        else:
                            row = lyr + self.start_ar
                        if cc in self.ar_all[each]:
                            self.table.write(row, col, self.ar_all[each][cc], self.style)
                        else:
                            self.table.write(row, col, 'Null', self.style)
                    else:
                        if re.search('p2line|l2l|p2p', each):
                            row = lyr + self.start_space
                        else:
                            row = lyr + self.start_ar
                        self.table.write(row, col, 'Null', self.style)

    def min_holes_and_all_num(self):
        # print info_layers[2]
        drl_line = 6
        # 钻孔最小孔径及孔数添加#
        min_drills = []
        for dd in self.info_layers[2]:
            # @formatter:off
            drltool = self.gen.DO_INFO(
                '-t layer -e %s/%s/%s -d TOOL,angle_direction=ccw' % (self.job_name, self.step_name, dd))
            # @formatter:on
            if drltool['gTOOLdrill_size'] == []:
                min_drl = 'N/A'
            else:
                min_drl = min(drltool['gTOOLdrill_size'])
                if dd in mai_drill_layers + tongkongDrillLayer:
                    min_drills.append(min_drl)
            all_drlnum = sum(drltool['gTOOLcount'])
            self.table.write(drl_line, 0, dd, self.style)
            self.table.write(drl_line, 1, min_drl, self.style)
            self.table.write(drl_line, 2, all_drlnum, self.style)
            drl_line += 1
        self.get_cost_dict['min_dirll_size'] = min(min_drills)


    def drl_rxls(self, index):
        """
        钻孔孔到铜结果解析
        :param index:  当前dfm在总checklist的序号
        :return:
        """
        # === 所有分析结果 === #
        op_data1 = self.gen.INFO('-t check -e %s/%s/%s -m script -d MEAS -o index+action=%s'
                                 % (self.job_name, self.step_name, self.checklist, index))

        self.reslt_all[index] = op_data1

        op_count = len(op_data1)
        # === 所有分析结果的第11列，为序号，孔到铜 信号层与钻孔层对应关系，由以下语句获取 ===
        ichk_layers = self.gen.INFO('-t check -e %s/%s/%s -d MEAS_DISP_ID -o action=%s,angle_direction=ccw'
                                    % (self.job_name, self.step_name, self.checklist, index))

        inn_layers = list(set([i.split(' ')[0] for i in ichk_layers]))
        all_result = {}
        num_array = {}
        num_rslt = {}
        check_mode = {
            'pth2cu': ['pth2c', 'pth2l', 'pth2p'],
            'via2cu': ['via2c', 'via2l', 'via2p'],
            'lvia2cu': ['lvia2c', 'lvia2l', 'lvia2p']
        }
        for k in inn_layers:
            all_result[k] = []
            num_array[k] = {}
            num_rslt[k] = {}
            self.drl2cu_record[k] = {}

        # for nn in string.uppercase:
        for allo in op_data1:
            # 0-2	2-3	3-4	4-5	5-6	6-7 7-8	8-9	9-10	10-11
            line = allo.strip('\n').split(' ')
            if line[0] in check_mode['pth2cu'] or line[0] in check_mode['via2cu'] or line[0] in check_mode['lvia2cu']:
                if line[1] in inn_layers:
                    all_result[line[1]].append(line)
                    if line[11] not in num_array[line[1]]:
                        num_array[line[1]][line[11]] = [line[2]]
                        self.drl2cu_record[line[1]][line[11]] = {'g_value': line[2], 'g_index': line[13],
                                                                 'g_mode': line[0], 'chk_num': index}
                    else:
                        if float(line[2]) - float(num_array[line[1]][line[11]][0]) < 0:
                            num_array[line[1]][line[11]] = [line[2]]
                            self.drl2cu_record[line[1]][line[11]] = {'g_value': line[2], 'g_index': line[13],
                                                                     'g_mode': line[0], 'chk_num': index}
        st_line = 1
        for kk in ichk_layers:
            line = kk.strip('\n').split(' ')
            if line[0] in inn_layers:
                if str(line[1]) in num_array[line[0]]:
                    num_rslt[line[0]][line[1]] = line[3]
                    self.drl2cu_record[line[0]][line[1]]['drl_layer'] = line[3]
                    if line[3] in self.lyr_rcrd:
                        col = self.lyr_rcrd[line[3]]
                    else:
                        col = st_line
                        self.lyr_rcrd[line[3]] = st_line
                        st_line += 1
                    row = int(line[0].strip('l')) + self.start_drl_cu
                    row_drlname = self.start_drl_cu
                    self.table.write(row_drlname, col, line[3], self.style)

                    if float(str(num_array[line[0]][line[1]][0])) - 7.0 < 0:
                        self.table.write(row, col, num_array[line[0]][line[1]], self.style1)
                    else:
                        self.table.write(row, col, num_array[line[0]][line[1]], self.style)

    def ar_wrt(self, inn_define, index):
        ar_layers = self.info_layers[index]
        ar_attr = self.info_result[index]
        for i in ar_layers:
            row = int(i.strip('l')) + self.start_ar
            for k in inn_define:
                # k为分析项目#
                # 结果表示方式
                cc = i + '_' + k
                # #取值序号#
                dd = ar_attr['gCHK_ATTRname'].index(cc)
                # # 取值#
                bb = ar_attr['gCHK_ATTRval'][dd]
                # uu=table.cell_value(inn_define[k],3)
                self.table.write(row, inn_define[k], bb, self.style)
                if k == 'min_via_ar':
                    # === 增加数据记录 ===
                    try:
                        min_ar = float(bb)
                    except:
                        min_ar = "N/A"
                    if i in self.result_record.keys():
                        self.result_record[i]["min_via_ar"] = min_ar
                    else:
                        self.result_record[i] = {"min_via_ar": min_ar}


    def get_min_bga(self):
        bga_sizes = []
        bga_layers = self.info_layers[4]
        bga_attr = self.info_result[4]
        for i in bga_layers:
            # row = int(i.strip('l'))+st_line
            for k in self.out_define3:
                # k为分析项目#
                # 结果表示方式
                cc = i + '_' + k
                # 取值序号#
                dd = bga_attr['gCHK_ATTRname'].index(cc)
                # 取值#
                bb = bga_attr['gCHK_ATTRval'][dd]
                # uu=table.cell_value(inn_define[k],3)
                # table.write(row,inn_define[k],bb,style)
                if bb != 'N/A':
                    bga_sizes.append(bb)
        if not bga_sizes:
            min_bga = 'N/A'
        else:
            min_bga = min(bga_sizes)
        self.table.write(6, 7, min_bga, self.style)

    def run_snap_in_result(self):
        """
        循环已分析的层别，取出值最小的点，再运行拍图程序
        :return:
        """

        # === 取内层分析及外层分析，序号为3 及 4
        # === 循环内层层别 ===
        # info_result = {
        # 	"3": [
        # 		"p2p l7 3.126 mil r17.874 r17.874 SG 3.287037 3.096 3.290163 3.096 1 R 1\n",
        # 		"c2c l7 4.931 mil r0 r0 SG 1.698678 2.8286901 1.7021587 2.8321823 1 R 2\n",
        # 		"c2c l7 5.683 mil r0 r0 SG 3.0171074 2.6887742 3.0211279 2.684758 1 Y 3\n",]
        # 		}
        # === 取出拍图的index ===
        snap_dict = {}
        for layer in self.info_layers[3]:
            snap_dict[layer] = {}
            snap_dict[layer]['chk_num'] = 3
            for mode in self.snap_mode:
                min_mode = 'min_' + mode
                for line in self.reslt_all[3]:
                    l_list = line.strip('\n').split(' ')
                    # snap_dict[layer][mode] = ''
                    if l_list[0] == mode and l_list[1] == layer and abs(
                            float(l_list[2]) - float(self.result_record[layer][min_mode])) < 0.001:
                        get_index = l_list[13]
                        snap_dict[layer][mode] = dict(g_index=get_index, g_value=l_list[2])
                        # continue
        for layer in self.info_layers[4]:
            snap_dict[layer] = {}
            snap_dict[layer]['chk_num'] = 4
            for mode in self.snap_mode:
                min_mode = 'min_' + mode
                for line in self.reslt_all[4]:
                    l_list = line.strip('\n').split(' ')
                    # snap_dict[layer][mode] = ''
                    # if l_list[0] == mode and l_list[1] == layer:
                    if l_list[0] == mode and l_list[1] == layer and abs(
                            float(l_list[2]) - float(self.result_record[layer][min_mode])) < 0.001:
                        get_index = l_list[13]
                        snap_dict[layer][mode] = dict(g_index=get_index, g_value=l_list[2])
                        # continue
        print json.dumps(snap_dict, indent=2)
        for layer in snap_dict:
            for mode in self.snap_mode:
                if mode in snap_dict[layer]:
                    get_op_file = self.take_snapshot(snap_dict[layer]['chk_num'], layer,
                                                     snap_dict[layer][mode]['g_index'], mode,
                                                     snap_dict[layer][mode]['g_value'])
                    snap_dict[layer][mode]['op_file'] = get_op_file
        # self.drl2cu_record = {
        #    "l10": {
        #        "3": {
        #            "g_index": "83124",
        #            "g_value": "4.301",
        #            "drl_layer": "s10-9",
        #            "g_mode": "lvia2p"
        #        }
        #    },
        #    "l6": {
        #        "3": {
        #            "g_index": "6349",
        #            "g_value": "6.441",
        #            "drl_layer": "b3-8",
        #            "g_mode": "via2p"
        #        }
        #    }
        #   }
        for layer in self.drl2cu_record:
            # === 分析的序号，与钻孔层相关 ===
            for tmp_index in self.drl2cu_record[layer]:
                get_op_file = self.take_snapshot(self.drl2cu_record[layer][tmp_index]['chk_num'], layer,
                                                 self.drl2cu_record[layer][tmp_index]['g_index'],
                                                 self.drl2cu_record[layer][tmp_index]['g_mode'],
                                                 self.drl2cu_record[layer][tmp_index]['g_value'])
                tmp_mode = '%s_%s' % (self.drl2cu_record[layer][tmp_index]['drl_layer'],
                                      self.drl2cu_record[layer][tmp_index]['g_mode'])
                snap_dict[layer][tmp_mode] = {'op_file': get_op_file,
                                              'g_value': self.drl2cu_record[layer][tmp_index]['g_value']}
                self.snap_mode.append(tmp_mode)
        return snap_dict

    def take_snapshot(self, chk_num, lyr_name, f_ind, chk_mod, ip_value):
        """
        应用分析结果中的拍图
        :param chk_num: checklist位于总checklist的第几项，例chk_num = 3
        :param lyr_name:  层别名，例lyr_name = 'l2'
        :param f_ind:  分析项目在所有分析结果中的编号例f_ind = '581119'
        :param chk_mod:  分析项目，例chk_mod = 'p2p'
        :param ip_value: 拍图值 ip_value = '3.175'
        :return:
        """
        op_file = '%s/%s/%s_%s_%s.png' % (self.outputpath, 'DRC_IMG', chk_mod, lyr_name, ip_value)
        # @formatter:off
        self.gen.COM('clear_layers')
        self.gen.COM('top_tab,tab=Checklists')
        self.gen.COM('chklist_open,chklist=%s' % self.checklist)
        self.gen.COM('chklist_show,chklist=%s,nact=1,pinned=yes,pinned_enabled=yes' % self.checklist)
        self.gen.COM('chklist_res_show,chklist=%s,nact=%s,x=0,y=0,w=0,h=0,is_run_results=no,is_cf_resume=yes' % (
        self.checklist, chk_num))
        self.gen.COM('act_tab_select,chklist=%s,nact=%s' % (self.checklist, chk_num))
        self.gen.COM(
            'filter_view,object=ActTabResultsList,uniq_name=AnalysisResults,key=layers,values=%s,reset=no' % lyr_name)
        self.gen.COM('chklist_res_sel_category,layers_mode=replace,keep_work_lyr=no,display_mode=popview,'
                     'chklist=%s,nact=%s,category=%s' % (self.checklist, chk_num, chk_mod))
        self.gen.COM('chklist_res_goto_measure,layers_mode=replace,keep_work_lyr=no,display_mode=popview,'
                     'chklist=%s,nact=%s,ind=%s,show_orig=no' % (self.checklist, chk_num, f_ind))
        self.gen.COM('zoom_mode,zoom=none')
        self.gen.COM('zoom_home')

        self.gen.COM('save_snapshot,path=%s' % op_file)
        self.gen.COM('zoom_pv_close,all=yes,popview=1')
        self.gen.COM('clear_layers')
        # @formatter:on
        return op_file

    def add_picture_to_excel(self, ip_snap_dict):
        # === 循环拍图数据 ===
        # === 根据层别写入excel ===
        snaps_file = self.outputpath + "DRC_" + self.job_name.upper() + "_snaps.xlsx"

        # 创建一个新Excel文件并添加一个工作表。
        workbook = xlsxwriter.Workbook(snaps_file)
        self.snap_mode = list(set(self.snap_mode))
        layerlist = [i for i in ip_snap_dict]
        layerlist.sort(key=lambda x: int(x[1:]))
        # === 应用排序的层别 ===
        for layer in layerlist:
            worksheet = workbook.add_worksheet(layer)

            # 单元格合并后居中
            fmt = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True,
                                       'border': 6, 'fg_color': '#D7E4BC'})

            # sheet.merge_range(x1, y1, x2, y2, value, cell_format=None)
            worksheet.merge_range(0, 0, 0, 1, u'%s 层别分析截图' % layer.upper(), cell_format=fmt)
            worksheet.set_row(0, 30)

            # 加宽第一列使文本更清晰。
            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:B', 150)
            row_count = 2
            for mode in self.snap_mode:
                if mode in ip_snap_dict[layer]:
                    worksheet.set_row(row_count, 760)
                    # 插入一张图片。
                    info_grid = 'A%s' % row_count
                    imag_grid = 'B%s' % row_count
                    worksheet.write(info_grid, u'模式:%s 值:%s' % (mode, ip_snap_dict[layer][mode]['g_value']), fmt)

                    worksheet.insert_image(imag_grid, ip_snap_dict[layer][mode]['op_file'])
                    row_count += 3

        # self.drl2cu_record = {
        #     "l10": {
        #         "3": {
        #             "g_index": "83124",
        #             "g_value": "4.301",
        #             "drl_layer": "s10-9"
        #         }
        #     },
        #     "l6": {
        #         "3": {
        #             "g_index": "6349",
        #             "g_value": "6.441",
        #             "drl_layer": "b3-8"
        #         }
        #     }
        # }
        # TODO 孔到铜的拍图及添加到excel
        workbook.close()

    def Analysis_Silk_SurPersent(self):
        """
        分析文字白油块的占比
        :return:None
        """
        # --获取JOB中的文字层
        self.GEN.CLEAR_LAYER()
        orgUnit = self.GEN.GET_UNITS()
        if orgUnit != 'mm':
            self.GEN.CHANGE_UNITS('mm')

        # --获取文字层列表
        silkList = self.GEN.GET_ATTR_LAYER('silk_screen', job=self.job_name)
        for orgLay in silkList:
            # --判断属性值 是否存在
            getAtt = self.GEN.DO_INFO('-t layer -e %s/%s/%s -d ATTR -p name' % (self.job_name, self.step_name, orgLay))
            if 'silk_surface_persent' not in getAtt['gATTRname']:
                print getAtt['gATTRname']
                self.GEN.LOG(u'silk_surface_persent 料号中属性不存在，无法执行...')
                return False

            # --备份当前文字层，并转surface
            tmpLay = orgLay + "_++_"
            self.GEN.COPY_LAYER(self.job_name, self.step_name, orgLay, tmpLay)
            self.GEN.WORK_LAYER(tmpLay)
            # --去除板外
            self.GEN.COM('clip_area_strt')
            self.GEN.COM('clip_area_end,layers_mode=affected_layers,layer=,area=profile,area_type=rectangle,'
                         'inout=outside,contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text')
            # --通过选择网格线的功能挑出部分
            self.GEN.COM('sel_drawn,type=mixed,therm_analyze=yes')
            if self.GEN.GET_SELECT_COUNT() > 0:
                self.GEN.SEL_CONTOURIZE()
            # region # --TODO 仍然建议在DRC分析前，把字符里的白油块整体平面化（从整理后的文字层挑出是否有大于公差的线宽）；
            # @formatter:off
            getLaySymbolList = self.GEN.DO_INFO(
                '-t layer -e %s/%s/%s -d SYMS_HIST -p symbol' % (self.job_name, self.step_name, tmpLay))
            # @formatter:on
            # --初始化，是否存在小于公差范围的线
            isExist = False
            # --循环所有Symbol List,判断是否存在小于公差范围的线；
            for symbol in getLaySymbolList:
                # --"r"开头的symbol
                if symbol.startswith('r'):
                    try:
                        lineSize = float(symbol[1:])
                        if lineSize <= float(self.resizwTol):
                            isExist = True
                            break
                    except:
                        self.GEN.LOG(u'不是线，跳过...')
                        continue
                pass
            # endregion

            # --整体平面化
            self.GEN.SEL_CONTOURIZE()
            self.GEN.SEL_RESIZE(-self.resizwTol)
            # --判断原始文字层内是否有比10Mil线还粗的线，如果存在，刚不作+10Mil的动作（以防粗字被还原），如果没有，直接再次+10Mil，以还原白油块尺寸
            if isExist:
                self.GEN.SEL_RESIZE(self.resizwTol)
            # --分析面积占比
            self.GEN.COM('copper_area,layer1=%s,layer2=,drills=yes,consider_rout=no,ignore_pth_no_pad=no,'
                         'drills_source=matrix,thickness=0,resolution_value=1,x_boxes=3,y_boxes=3,area=no,dist_map=yes' % tmpLay)
            # --获取占比（第二个元素为百分比，第一个为实现面积）
            areaPersent = float(self.GEN.COMANS.split(" ")[1])

            # --写入对应的属性列表中(无论多少，都写入对应层属性中
            self.GEN.VOF()
            self.GEN.COM('set_attribute,type=layer,job=%s,name1=%s,name2=%s,name3=,attribute=silk_surface_persent,'
                         'value=%s,units=inch' % (self.job_name, self.step_name, orgLay, areaPersent))
            self.GEN.VON()

            # --删除辅助层
            self.GEN.DELETE_LAYER(tmpLay)

            # self.GEN.PAUSE("XXXXXXXXX")
        # --还原单位
        if orgUnit != 'mm':
            self.GEN.CHANGE_UNITS(orgUnit)


if __name__ == "__main__":
    main = DrcCheck()