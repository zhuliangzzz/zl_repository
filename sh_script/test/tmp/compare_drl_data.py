#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2023/02/08
# @Revision     :    1.0.0
# @File         :    compare_drl_data.py
# @Software     :    PyCharm
# @Usefor       :    
# ---------------------------------------------------------#

import os
import platform
import re
import sys
from PyQt4 import QtCore, QtGui, Qt
from PyQt4.QtGui import QMessageBox
import sys
import json
import math

from Compare import Ui_mainWindow
from datetime import datetime

# --加载相对位置，以实现InCAM与Genesis共用
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genCOM_26 as genCOM
import Oracle_DB
from messageBoxPro import msgBox
from mwClass_V2 import AboutDialog
from connect_database_all import MySql
from reorder_drill_order_from_inplan_for_laser import reorder_drill
import gClasses
top = gClasses.Top()

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class Get_ERP:
    def __init__(self, job_name):
        self.DB_O = Oracle_DB.ORACLE_INIT()
        self.dbc_e = self.DB_O.DB_CONNECT(host='172.20.218.247', servername='topprod', port='1521', username='zygc',
                                          passwd='ZYGC@2019')
        self.job_name = job_name

    def get_erp_drl(self):
        sql = """SELECT
            TC_AAF00 ERP_JOB,
            TC_AAF01 ERP_DRILL_NAME,
            TC_AAF03 T_NUM,
            TC_AAF04 DRILL_SIZE,
            TC_AAF06 DRILL_NUM,
            TC_AAF05 DRILL_TYPE,
            TC_AAF09 NOTE,
            TC_AAF32 OTHER
        FROM
            TC_AAF_FILE 
        WHERE
            (TC_AAF00 = '{0}A' OR TC_AAF00 LIKE '{1}-%%A' )
						AND  TC_AAF00 NOT LIKE '{2}-C-%%' 
        ORDER BY
            TC_AAF01,
            TC_AAF03            
          
        """ .format(self.job_name, self.job_name,self.job_name)

        query_result = self.DB_O.SELECT_DIC(self.dbc_e, sql)
        # print query_result
        return query_result

    def __del__(self):
        self.DB_O.DB_CLOSE(self.dbc_e)

    def erp_drill_name_translate(self, ip_name):

        lrReg = re.compile(r'L([0-9][0-9]?-[0-9][0-9]?)镭射定位孔')
        BlindReg = re.compile(r'L([0-9][0-9]?-[0-9][0-9]?)镭射')
        BuryReg = re.compile(r'L([0-9][0-9]?-[0-9][0-9]?)埋孔')
        buryreg_mang = re.compile(r'L([0-9][0-9]?-[0-9][0-9]?)机械盲孔')
        cdsReg = re.compile(r'BOTTOM面控深盲孔-?\(cds\)')
        cds1Reg = re.compile(r'BOTTOM面控深盲孔-?\(cds-1\)')
        cdcReg = re.compile(r'TOP面控深盲孔-?\(cdc\)')
        cdc1Reg = re.compile(r'TOP面控深盲孔-?\(cdc-1\)')
        otherReg = re.compile(r'bd|b|drl2|drl-2|RVC([0-9][0-9]?-[0-9][0-9]?)')
        op_name = 'error'
        if lrReg.match(ip_name):
            op_name = 'lr%s' % lrReg.match(ip_name).group(1)
        elif BlindReg.match(ip_name):
            op_name = 's%s' % BlindReg.match(ip_name).group(1)
        elif BuryReg.match(ip_name):
            op_name = 'b%s' % BuryReg.match(ip_name).group(1)
        elif buryreg_mang.match(ip_name):
            op_name = 'm%s' % buryreg_mang.match(ip_name).group(1)            
        elif cdsReg.match(ip_name):
            op_name = 'cds'
        elif cds1Reg.match(ip_name):
            op_name = 'cds-1'
        elif cdcReg.match(ip_name):
            op_name = 'cdc'
        elif cdc1Reg.match(ip_name):
            op_name = 'cdc-1'
        elif ip_name == "一次钻孔":
            op_name = "drl"
        elif ip_name == "二次钻孔" or ip_name == '2nd':
            op_name = "2nd"
        elif ip_name == "三次钻孔":
            op_name = "3nd"
        elif ip_name == "铝片钻带":
            op_name = "lp"
        elif ip_name == "BOTTOM面控深盲孔":
            op_name = "cds"
        elif ip_name == "TOP面控深盲孔":
            op_name = "cdc"
        elif ip_name == "BOTTOM面背钻":
            op_name = "bds"
        elif ip_name == "TOP面背钻":
            op_name = "bdc"
        elif otherReg.match(ip_name):
            op_name = ip_name.lower()

        return op_name

    def combine_T_note(self, ip_data):
        """
        合并ERP中的同一把T
        :param ip_data:
        :return: op_data
        """
        op_data = {}
        for i_line in ip_data:
            # print i_line
            drill_name = self.erp_drill_name_translate(i_line['ERP_DRILL_NAME'])
            if drill_name == 'error':
                if '背钻' in i_line['ERP_DRILL_NAME']:
                    continue
                # msg_box = msgBox()
                # msg_box.critical(self, '错误', '料号:%s ERP钻带名:%s 不在已知范围内' % (self.job_name, i_line['ERP_DRILL_NAME']),
                #                  QMessageBox.Ok)
            D_Reg = re.compile('([0-9].*)\*([0-9].*)')
            if D_Reg.match(i_line['DRILL_SIZE']):
                drill_size = D_Reg.match(i_line['DRILL_SIZE']).group(1)
                drill_detail = '%s%s' % (drill_size, i_line['DRILL_TYPE'])
            else:
                drill_size = i_line['DRILL_SIZE']
                drill_detail = i_line['DRILL_TYPE']
            note_str = '' if not i_line['NOTE'] else i_line['NOTE']
            # d-coupon会分一把刀 实际cam会做成0.127 20240929 by lyh
            # if "-lyh" in os.environ["JOB"]:
            if float(drill_size) in [0.103, 0.115] and i_line['T_NUM'] == 'T20':
                drill_size = '0.127'
            if float(drill_size) in [0.128] and i_line['T_NUM'] == 'T20':
                drill_size = '0.140'
                # top.PAUSE(str([i_line['T_NUM'], drill_size]))
            try:
                float(drill_size)
            except:
                print i_line                     
            # if float(drill_size) > 0.3 and i_line['T_NUM'] == 'T03':
            #   # 孔径大于0.3时，认为绕烧
                # drill_size = '0.102'
            #try:
                #float(drill_size)
            #except:
                #print i_line            
            if drill_name in op_data:
                #if "s15-14" in drill_name:                    
                    #print drill_name, i_line
                if i_line['T_NUM'] in op_data[drill_name]:
                    if op_data[drill_name][i_line['T_NUM']]['DRILL_SIZE'] == drill_size:
                        op_data[drill_name][i_line['T_NUM']]['DRILL_NUM'] += int(i_line['DRILL_NUM'])
                        op_data[drill_name][i_line['T_NUM']]['DRILL_TYPE'] += '/%s' % drill_detail
                        op_data[drill_name][i_line['T_NUM']]['NOTE'] += '/%s' % note_str
                    else:
                        # 测试
                        #if i_line['T_NUM'] == "T23" and "s15-14" in drill_name and (float(drill_size) == 0.114 or float(drill_size) == 0.102):
                            #continue
                        op_data[drill_name][i_line['T_NUM']]['DRILL_SIZE'] += (";" + str(i_line['DRILL_SIZE']))
                        op_data[drill_name][i_line['T_NUM']]['DRILL_NUM'] += int(i_line['DRILL_NUM'])
                        op_data[drill_name][i_line['T_NUM']]['DRILL_TYPE'] += '/%s' % drill_detail
                        op_data[drill_name][i_line['T_NUM']]['NOTE'] += '/%s' % note_str

                else:
                    op_data[drill_name][i_line['T_NUM']] = dict(
                        T_NUM=i_line['T_NUM'],
                        DRILL_SIZE=drill_size,
                        DRILL_NUM=i_line['DRILL_NUM'],
                        DRILL_TYPE=drill_detail,
                        NOTE=note_str,
                        ERP_DRILL_NAME=i_line['ERP_DRILL_NAME'])
            else:
                op_data[drill_name] = {i_line['T_NUM']: dict(
                    T_NUM=i_line['T_NUM'],
                    DRILL_SIZE=drill_size,
                    DRILL_NUM=i_line['DRILL_NUM'],
                    DRILL_TYPE=drill_detail,
                    NOTE=note_str,
                    ERP_DRILL_NAME=i_line['ERP_DRILL_NAME'])}

        # 如果传入的输出层不是合并层不执行合并的逻辑
        try:
            output_laser_layer = sys.argv[6]
            if re.match("s\d+-\d+$",output_laser_layer) or re.match("s\d+-\d+-ls.*",output_laser_layer) :
                return op_data
            if output_laser_layer == 's18-17-2' and 'sd1024e6t96a1' in self.job_name:
                return op_data
        except:
            pass

        # === 如果同时存在s1-2，s1-3，类，则生成合并后的ERP数据
        laser_reg = re.compile('s([0-9][0-9]?)-([0-9][0-9]?)')
        laser_layers = [(i, laser_reg.match(i).group(1), laser_reg.match(i).group(2)) for i in op_data.keys() if
                        laser_reg.match(i)]
        # a = [laser_reg.match(i).group(1) for i in laser_layers if laser_reg.match(i)]
        print laser_layers
        print json.dumps(op_data)
        # print "-------------->1"
        # num_dict = {}
        start_index_list = [i[1] for i in laser_layers]


        # 20250407  'SD1022P6340A1' 合并层两层都在TOP面，旧逻辑不适用，调整逻辑 by -ynh
        mrg_index = self.extract_duplicates(start_index_list)
        if len(set(start_index_list)) < len(set(laser_layers)):
            for index in mrg_index:
                num_list = []
                mrg_layers = []
                reverse_list = False
                for laser_tuple in laser_layers:
                    layer = laser_tuple[0]
                    first = laser_tuple[1]
                    end = laser_tuple[2]
                    if first == index:
                        if int(first) < int(end):
                            reverse_list = False
                        else:
                            reverse_list = True
                        num_list.append(first)
                        num_list.append(end)
                        mrg_layers.append(layer)
                        num_list = list(set(num_list))

                    if not reverse_list:
                        mrg_layers.sort(key=lambda x: int(x.split('-')[1]))
                        num_list.sort(key=lambda x: int(x))
                    else:
                        mrg_layers.sort(key=lambda x: int(x.split('-')[1]), reverse=True)
                        num_list.sort(key=lambda x: int(x), reverse=True)

                if len(num_list) > 0:
                    new_name = 's%s' % '-'.join(num_list)
                    op_data = self.deal_op_dict(op_data, new_name, mrg_layers)
        # if len(set(start_index_list)) < len(set(laser_layers)):
        #     # === 存在同层开始的钻带
        #     num_dict = {}
        #     for key in start_index_list:
        #         num_dict[key] = num_dict.get(key, 0) + 1
        #     top_list = []
        #     bot_list = []
        #     top_layers = []
        #     bot_layers = []
        #     for laser_tuple in laser_layers:
        #         layer = laser_tuple[0]
        #         first = laser_tuple[1]
        #         end = laser_tuple[2]
        #         if first in num_dict:
        #             if num_dict[first] > 1:
        #                 if int(first) > int(end):
        #                     bot_list.append(end)
        #                     bot_list.append(first)
        #                     bot_layers.append(layer)
        #                 else:
        #                     top_list.append(end)
        #                     top_list.append(first)
        #                     top_layers.append(layer)
        #     top_layers.sort(key=lambda x: int(x.split('-')[1]))
        #     bot_layers.sort(key=lambda x: int(x.split('-')[1]), reverse=True)
        #     top_list = list(set(top_list))
        #     top_list.sort(key=lambda x: int(x))
        #
        #     bot_list = list(set(bot_list))
        #     bot_list.sort(key=lambda x: int(x), reverse=True)
        #     # print 'top_new_name',top_new_name
        #     # print 'bot_new_name',bot_new_name
        #     # print 'top_layers',top_layers
        #     # print 'bot_layers',bot_layers
        #     # print 'top_list',top_list
        #     # print 'bot_list',bot_list
        #     # 2023.03.08 Song 1.多层料号：HB1308PL517A1 非对称合并层，合并ERP数据报错，增加判断
        #     if len(top_list) > 0:
        #         top_new_name = 's%s' % '-'.join(top_list)
        #         op_data = self.deal_op_dict(op_data, top_new_name, top_layers)
        #     # print 'bot_list',bot_list
        #     if len(bot_list) > 0:
        #         bot_new_name = 's%s' % '-'.join(bot_list)
        #         op_data = self.deal_op_dict(op_data, bot_new_name, bot_layers)
        # print json.dumps(op_data)
        # print "-------------->2"
        return op_data

    def extract_duplicates(self,lst):
        seen = set()
        duplicates = set()
        for item in lst:
            if item in seen:
                duplicates.add(item)
            else:
                seen.add(item)
        return list(duplicates)

    def deal_op_dict(self, op_data, one_side_new_name, one_side_layers):
        """
        合并单面镭射，如果8mil和10mil同时存在10mil排刀从T15开始
        :param op_data:
        :param one_side_new_name:
        :param one_side_layers:
        :return:
        """
        print 'one_side_new_name',one_side_new_name
        print 'one_side_layers',one_side_layers
        grow_index = 3
        for index, bot_laser in enumerate(one_side_layers):
            if index == 0:
                op_data[one_side_new_name] = op_data[bot_laser]
            else:
                # if op_data[bot_laser].get("T03", None):
                # 全部按inplan的刀序来排列 20240118 by lyh
                for key in op_data[bot_laser].keys():
                    if key in ["T01", "T02", "T21", "T22", "T23"]:
                        continue
                 
                    op_data[one_side_new_name][key] = op_data[bot_laser][key]
                    op_data[one_side_new_name][key]['T_NUM'] = key
                    
                    #if float(op_data[bot_laser][key]['DRILL_SIZE']) > 0.3:
                        ## 绕烧的情况
                        #grow_index += 1
                        #if grow_index < 9:
                            #Tnum = 'T0%s' % grow_index
                        #else:
                            #Tnum = 'T%s' % grow_index
                        #op_data[one_side_new_name][Tnum] = op_data[bot_laser][key]
                        #op_data[one_side_new_name][Tnum]['T_NUM'] = Tnum
                        #op_data[one_side_new_name][Tnum]['DRILL_SIZE'] = '0.102'
                    #仅d10 a86客户需打五遍 20240117 by lyh
                    #elif 0.25 > float(op_data[bot_laser][key]['DRILL_SIZE']) > 0.2 and self.job_name[1:4] in ['a86', 'd10']:
                        #op_data[one_side_new_name]['T10'] = op_data[bot_laser][key]
                    #elif float(op_data[bot_laser][key]['DRILL_SIZE']) > 0.25 and self.job_name[1:4] in ['a86', 'd10']:
                        #op_data[one_side_new_name]['T15'] = op_data[bot_laser][key]
                    #else:
                        #grow_index += 1
                        #if grow_index <= 9:
                            #Tnum = 'T0%s' % grow_index
                        #else:
                            #Tnum = 'T%s' % grow_index                                
                        #op_data[one_side_new_name][Tnum] = op_data[bot_laser][key]
                        #op_data[one_side_new_name][Tnum]['T_NUM'] = Tnum
                #else:
                    #if op_data[bot_laser].get("T15", None):
                        #op_data[one_side_new_name]['T15'] = op_data[bot_laser]['T15']
                        
        #if 'T10' in op_data[one_side_new_name] and 'T15' in op_data[one_side_new_name]:
            ## === 8mil 10mil同时存在才排T15
            #new_dict = op_data[one_side_new_name]['T10']
            #del op_data[one_side_new_name]['T10']
            #calc_num = 0
            #grow_index = 4
            #for cc in range(10):
                #grow_index += 1
                #if grow_index < 9:
                    #Tnum = 'T0%s' % grow_index
                #else:
                    #Tnum = 'T%s' % grow_index
                #if op_data[one_side_new_name].has_key(Tnum):
                    #continue
                #calc_num += 1                    
                #op_data[one_side_new_name][Tnum] = new_dict
                #op_data[one_side_new_name][Tnum]['T_NUM'] = Tnum
                #if calc_num >= 5:
                    #break
                
            #new_dict2 = op_data[one_side_new_name]['T15']
            #op_data[one_side_new_name]['T15']['T_NUM'] = 'T15'
            #grow_index = 15
            #for cc in range(4):
                #grow_index += 1
                #if grow_index < 9:
                    #Tnum = 'T0%s' % grow_index
                #else:
                    #Tnum = 'T%s' % grow_index
                #op_data[one_side_new_name][Tnum] = new_dict2
                #op_data[one_side_new_name][Tnum]['T_NUM'] = Tnum
        #elif 'T10' in op_data[one_side_new_name]:
            #new_dict = op_data[one_side_new_name]['T10']
            #del op_data[one_side_new_name]['T10']
            #calc_num = 0
            #grow_index = 4
            #for cc in range(10):
                #grow_index += 1
                #if grow_index <= 9:
                    #Tnum = 'T0%s' % grow_index
                #else:
                    #Tnum = 'T%s' % grow_index
                #if op_data[one_side_new_name].has_key(Tnum):
                    #continue
                #calc_num += 1
                #op_data[one_side_new_name][Tnum] = dict(new_dict)
                #op_data[one_side_new_name][Tnum]["T_NUM"] = '%s' % Tnum
                #if calc_num >= 5:
                    #break
                
        #elif 'T15' in op_data[one_side_new_name]:
            #grow_index = 14
            #new_dict = op_data[one_side_new_name]['T15']
            #del op_data[one_side_new_name]['T15']
            #for cc in range(5):
                #grow_index += 1
                #if grow_index <= 9:
                    #Tnum = 'T0%s' % grow_index
                #else:
                    #Tnum = 'T%s' % grow_index
                #op_data[one_side_new_name][Tnum] = dict(new_dict)
                #op_data[one_side_new_name][Tnum]['T_NUM'] = Tnum
        return op_data


class CompareDrl(QtGui.QWidget, Ui_mainWindow):
    def __init__(self):
        super(CompareDrl, self).__init__()
        # print '123'
        self.setupUi(self)
        self.cwd = os.path.dirname(sys.argv[0])

        f = QtCore.QFile('%s/ui_qss.qss' % self.cwd)
        f.open(QtCore.QFile.ReadOnly)
        styleSheet = f.readAll()
        styleSheet = unicode(styleSheet, encoding='utf8')
        QtGui.qApp.setStyleSheet(styleSheet)
        
        self.reorder_t_header.clicked.connect(self.change_t_header)
        self.reorder_t_header.setFixedWidth(120)

        # self.job_name = 'sb8708gc009d1'
        # self.job_name = 'c18306oi760a1'
        self.job_name = sys.argv[1]
        # self.cam_drl_name = 's1-2'
        self.cam_drl_name = sys.argv[2]
        self.file_path = sys.argv[3]
        self.lr_laser = sys.argv[4]
        self.user = None
        if len(sys.argv) > 5:
            self.user = sys.argv[5]
        
        self.output_laser_layer = "none"
        if len(sys.argv) > 6:
            self.output_laser_layer = sys.argv[6]
            
        self.job_name_Upper = self.job_name.upper().split('-')[0]
        self.GE = Get_ERP(self.job_name_Upper)

        # self.cam_drl_name = 'drl'
        self.erp_array = self.GE.get_erp_drl()
        if not self.erp_array:
            msg_box = msgBox()
            msg_box.critical(self, '错误', '未在ERP数据中获取料号:%s钻带:%s的数据(请让MI制作人确认是否保存钻带?)，输出完后请手动回读比对！！' % (self.job_name_Upper, self.cam_drl_name),
                             QMessageBox.Ok)
            sys.exit(0)

        self.erp_dict = self.GE.combine_T_note(self.erp_array)
        # print json.dumps(self.erp_dict)
        self.ERP_cols = ['T_NUM', 'DRILL_SIZE', 'DRILL_NUM', 'ERP_DRILL_NAME', 'NOTE']
        self.erp_col_width_list = [60, 50, 50, 60, 50, 190]
        self.cam_col_width_list = [50, 50, 50]
        self.tableWidget_CAM.verticalHeader().hide()
        self.tableWidget_ERP.verticalHeader().hide()
        self.readERP()
        self.exit_code = 0
        # if platform.system() == "Windows":
        #     self.file_path = "d:/disk/film/%s" % self.job_name
        # else:
        #     self.file_path = "/id/workfile/film/%s" % self.job_name

        self.job_drl_file = []
        job_dir_tmp = os.listdir(self.file_path)

        for dir in job_dir_tmp:
            if dir == "." or dir == ".." or '~' in dir:
                continue
            drl_list = ['%s.drl' % self.job_name, "%s.drl2" % self.job_name, "%s.lp" % self.job_name]
            drl_Reg = re.compile(
                '%s.([2-4]{1}nd|[mb][0-9][0-9]?-?[0-9][0-9]?$|b[0-9]{2,4}|[s][0-9][0-9]?(-[0-9][0-9]?){1,9}.write$|bd[0-9]{1,4}|sz|[bc]d[cs]$)' % self.job_name)
            # drl_Reg = re.compile('([2-4]{1}nd|[mb][0-9][0-9]?-?[0-9][0-9]?$|b[0-9]{2,4}|[s][0-9][0-9]?(-[0-9][0-9]?){1,9}.write$|bd[0-9]{1,4}|sz|[bc]d[cs]$)')
            if dir in drl_list or drl_Reg.match(dir):
                self.job_drl_file.append(dir)
        # print self.job_drl_file
        
        self.start_read_file_and_show_ui()
        
    def start_read_file_and_show_ui(self):
        if re.match('[s][0-9][0-9]?-?[0-9][0-9]?', self.cam_drl_name):
            check_file_name = '%s.%s.write' % (self.job_name, self.cam_drl_name)
        else:
            check_file_name = '%s.%s' % (self.job_name, self.cam_drl_name)
        # print check_file_name
        self.read_cam_drl(check_file_name)
        self.compare_two_table()

        self.add_ui()        

    def closeEvent(self, event):

        print 'exit_code', self.exit_code, 'xxxxxxxxxxxxxxxxxxx'
        if self.exit_code > 0:
            with open("/tmp/{0}_laser_exit_result.log", "w") as f:
                f.write("normal")
        sys.exit(self.exit_code)

    def add_ui(self):
        """
        界面设置项
        :return:
        """
        # print('erp', self.cam_drl_name, self.erp_dict)
        self.lineEdit_cam_drl_name.setText(self.cam_drl_name)
        # 取其中一个T的ERP描述，默认T01存在，直接取T01
        if self.cam_drl_name in self.erp_dict:
            if self.erp_dict[self.cam_drl_name].get('T01'):  # 20250523 zl 优化：SF3210GET02A1 s5-6没有T01
                self.lineEdit_erp_drl_name.setText(_fromUtf8(self.erp_dict[self.cam_drl_name]['T01']['ERP_DRILL_NAME']))
        self.lineEdit_job_name.setText(self.job_name_Upper)
        self.tableWidget_ERP.hideColumn(4)
        self.tableWidget_CAM.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tableWidget_ERP.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)

        # 多层代工的不走审批流程
        mysql = MySql()
        if not mysql.get_job_org_code(jobname=self.job_name[:13]):
            self.exit_code = 0

        if self.exit_code == 1:
            self.pushButton_close.setText(_fromUtf8('比对未通过_点击将删除已输出镭射'))
            QtCore.QObject.connect(self.pushButton_sendcheck, QtCore.SIGNAL(_fromUtf8("clicked()")), self.sendcheck)
        else:
            self.pushButton_sendcheck.hide()

    def sendcheck(self):
        """发送审批结果界面 """
        get_message = self.table_2_html()
        submitData = {
            'site': u'HDI板事业部',
            'job_name': self.job_name,
            'pass_tpye': 'CAM',
            'pass_level': 8,
            'assign_approve': '43982|44566|44024|84310|83288|44839|68027',
            'pass_title': get_message,
        }
        Dialog = AboutDialog(submitData['pass_title'], cancel=True, appCheck=True, appData=submitData)
        Dialog.exec_()
        # endregion

        # --根据审批的结果返回值
        if Dialog.selBut in ['x', 'cancel']:
            # sys.exit(self.exit_code)
            # return False
            pass
        if Dialog.selBut == 'ok':
            self.exit_code = 0
            # return True
            # sys.exit(self.exit_code)

        # return False
        # sys.exit(self.exit_code)
        self.close()

    def table_2_html(self):
        """
        table_widget转换为html
        :return:
        """
        title_list = [u'CAM_T刀序', u'刀径', u'数量', u"ERP比对结果", u"ERP_T刀序", u'刀径', u'数量']
        title = u'<table border="1"><tr><th>{0}</th><th>{1}</th><th>{2}</th><th>{3}</th><th>{4}</th><th>{5}</th><th>{6}</th></tr>'.format(
            *title_list)

        body = ''
        erp_row_num = self.tableWidget_ERP.rowCount()
        for row_i in range(erp_row_num):
            g_list = []
            for column_i in range(3):
                g_text = ''
                if self.tableWidget_CAM.item(row_i,column_i):
                    g_text = self.tableWidget_CAM.item(row_i,column_i).text()
                g_list.append(g_text)
            for column_i in range(4):
                g_text = ''
                if self.tableWidget_ERP.item(row_i,column_i):
                    g_text = self.tableWidget_ERP.item(row_i,column_i).text()
                g_list.append(g_text)
            body += u'<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6}</td></tr>'.format(*g_list)
        date_time = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
        tail = u'</table><br><br>%s CAM用户：%s 镭射：%s 输出检查未通过！！！' % (date_time, self.user,self.cam_drl_name)
        message = title + body + tail
        return message

    def redeal_ERP_Data(self):
        """
        转换ERP钻带名（此函数未使用）
        :return:
        """
        erp_dict = {}
        for line in self.erp_array:
            erp_name = line['ERP_DRILL_NAME']
            erp2camdrl_name = self.GE.erp_drill_name_translate(erp_name)
            if erp2camdrl_name not in erp_dict:
                erp_dict[erp2camdrl_name] = []
            erp_dict[erp2camdrl_name].append(line)
        return erp_dict

    def readERP(self):
        """
        获取指定钻带在ERP的信息，并写入前台界面
        :return:
        """
        if self.cam_drl_name not in self.erp_dict:
            msg_box = msgBox()
            msg_box.critical(self, '错误', '未在ERP数据中获取料号:%s钻带:%s的数据' % (self.job_name_Upper, self.cam_drl_name),
                             QMessageBox.Ok)
            return 0
        row_num = len(self.erp_dict[self.cam_drl_name])
        self.tableWidget_ERP.setRowCount(row_num)  # 设置model的列数
        key_list = self.erp_dict[self.cam_drl_name].keys()
        key_list.sort(key=lambda x: int((x[1:])))
        print json.dumps(self.erp_dict[self.cam_drl_name], indent=2)
        for row, t_num in enumerate(key_list):
            cur_dict = self.erp_dict[self.cam_drl_name][t_num]
            if row == 0:
                self.tableWidget_ERP.setColumnCount(len(self.ERP_cols) + 1)
                for c_index, clwd in enumerate(self.erp_col_width_list):
                    self.tableWidget_ERP.setColumnWidth(c_index, clwd)
            line2 = [cur_dict[i] for i in self.ERP_cols]
            linelen = len(line2)
            for col in range(0, linelen):
                if not line2[col]:
                    continue
                data = _fromUtf8(str(line2[col]))
                item = QtGui.QTableWidgetItem(data)
                self.tableWidget_ERP.setItem(row, col + 1, item)

    def read_cam_drl(self, ip_drl):
        """
        读取CAM输出文件夹，并显示T刀序在界面
        :param ip_drl:
        :return:
        """

        job_drl_file = self.job_drl_file
        drl_layer_name = []
        file_path = self.file_path
        T_Reg = re.compile("^(T[0-9]{2}[0-9]?)")
        # for dir in job_drl_file:
        # print job_drl_file
        if ip_drl not in job_drl_file:
            # print 'not such drill:%s' % ip_drl
            msg_box = msgBox()
            msg_box.critical(self, '错误', '根据条件匹配，未找到此钻带文件：%s' % ip_drl, QMessageBox.Ok)
            return False
        # print 'xxxxxxxxxxxx'
        tmp_name = ip_drl.split('.')
        name = tmp_name[1]
        drl_layer_name.append(name)
        self.laser_file_path = '%s/%s' % (file_path, ip_drl)
        if "-lyh" in self.job_name:
            res = self.check_laser_file_is_right(self.laser_file_path)
            if res:
                msg_box = msgBox()
                msg_box.critical(self, '错误', res, QMessageBox.Ok)
                return False

        get_tool = self.seprateDrlFile('%s/%s' % (file_path, ip_drl))
        # print get_tool
        key_list = get_tool['t_list']
        row_num = len(key_list)
        self.tableWidget_CAM.setRowCount(row_num)  # 设置model的列数
        # key_list = self.erp_dict[self.cam_drl_name].keys()
        # CAM_cols = []
        for row, t_num in enumerate(key_list):
            cur_dict = get_tool[t_num]
            if row == 0:
                for c_index, clwd in enumerate(self.cam_col_width_list):
                    self.tableWidget_CAM.setColumnWidth(c_index, clwd)
            data = _fromUtf8(str(t_num))
            item = QtGui.QTableWidgetItem(data)
            self.tableWidget_CAM.setItem(row, 0, item)
            data = _fromUtf8(str(cur_dict['T_Size_mm']))
            item = QtGui.QTableWidgetItem(data)
            self.tableWidget_CAM.setItem(row, 1, item)
            data = _fromUtf8(str(cur_dict['Coord_Num']))
            item = QtGui.QTableWidgetItem(data)
            self.tableWidget_CAM.setItem(row, 2, item)
            
    def check_laser_file_is_right(self, drill_file_path):
        """检测镭射文件是否异常"""
        
        lines = file(drill_file_path).readlines()
        
        self.genesis_headers = []
        for line in lines:
            if re.match("(^T\d+)C(.*)", line):
                break
            self.genesis_headers.append(line)
            
        headerIndex = lines.index('%\n')        
        Holes_T = []
        Holes_size = {}
        for i in range(headerIndex):
            if re.match('^T.*', lines[i]):
                result = re.findall("(^T\d+)C(.*)", lines[i])
                if result:
                    Holes_T.append(result[0][0])
                    Holes_size[result[0][0]] = float(result[0][1])
                   
        Holes_T_body = {}
        for i, line in enumerate(lines):
            if i >= headerIndex:                
                if line == '%\n':
                    key = "T01"
                elif line.strip() in Holes_T:
                    key = line.strip()
                if line == 'M30\n':
                    break
                
                if Holes_T_body.has_key(key):
                    Holes_T_body[key].append(line)
                else:
                    Holes_T_body[key] = []
                    
        self.fg_t_headers = []
        
        for name in Holes_T:
            if lines.count(name+"\n") >= 2:
                self.fg_t_headers.append(name)
        
        if self.fg_t_headers:
            # if "sd1016gi169a1" not in self.job_name:
                
            if "T10\n" not in lines:
                return u"检测到此型号{0}有分割，但资料内未发现T10内靶刀头，请检查！".format(self.output_laser_layer)
            
            count = 0
            start = False
            for line in lines:
                if line == "T500\n":
                    start = True
                
                if start and ("g82" in line.lower() or "g83" in line.lower()):
                    count += 1
            
            if count != 4 * lines.count(self.fg_t_headers[0]+"\n"):
                return u"检测到此型号{0}有分割，但资料内g82/g83内靶坐标数量异常，\
                正常要{1}个，实际为{2}个，请检查！".format(self.output_laser_layer,
                                                        4 * lines.count(self.fg_t_headers[0]+"\n"),
                                                        count)  
    def cor_to_float(self, ip_cor):
        """33制转为浮点数类型字符串"""
        if '-' in ip_cor:
            ee = ip_cor[0:4]
            ff = ip_cor[4:7]
            op_float = "%s.%s" % (ee, ff)
        else:
            ee = ip_cor[0:3]
            ff = ip_cor[3:6]
            op_float = "%s.%s" % (ee, ff)
        return op_float

    def seprateDrlFile(self, file):
        """seprate Drl File into hash """
        # tool_dict = {}
        tool_dict = dict(t_list=[])
        # === %后为主体程序 ===
        body_start = "no"
        # === 2020.09.01 增加排刀表的获取 ===
        paidao_start = "no"
        search_key = ""
        f = open(file)
        for info in f.readlines():
            info = info.strip()
            if info.find('T') == 0 and 'C' in info[3:5]:
                # === 由于T500存在，C查找范围放大一位
                # --取出T-CODE 和 对应大小
                t_code = info[info.find('T'): info.find('C')]  # 截取T与C中间的部分
                size = info[info.find('C'):]
                tool_dict['t_list'].append(t_code)
                if t_code not in tool_dict:
                    size_mm = re.match('C(\d\.\d+)', size).group(1)
                    tool_dict[t_code] = dict(T_Info=info, T_Size=size, T_Size_mm=size_mm, Coord_Num=0)
                else:
                    msg_box = msgBox()
                    msg_box.critical(self, '错误', '钻带文件：%s 中T刀序:%s 存在超过一行数据' % (file, info), QMessageBox.Ok)
                paidao_start = "yes"
            elif info == '%':
                body_start = 'yes'
                paidao_start = "no"
            elif body_start == 'yes':
                if info in tool_dict:
                    search_key = info
                elif info == str('M30'):
                    pass
                else:
                    if search_key == "":
                        search_key = "T01"
                    if "G82" in info or "G83" in info and tool_dict['T01']['T_Size_mm'] == '3.175':
                        # === 镭射分割料号在每个正式T前均有G82及G83指令
                        if search_key != 'T500':
                            search_key = "T01"
                        
                            if (tool_dict.get("T500") and tool_dict["T500"]['Coord_Num'] == 0) or \
                               tool_dict.get("T500", None) is None:                            
                                tool_dict[search_key]['Coord_Num'] += self.get_drl_num(info,
                                                                                           tool_dict[search_key]['T_Size_mm'])
                        else:
                            if tool_dict.get("T500") and tool_dict["T500"]['Coord_Num'] <= 4:                            
                                tool_dict[search_key]['Coord_Num'] += self.get_drl_num(info,
                                                                                           tool_dict[search_key]['T_Size_mm'])                            
                    elif search_key and info not in tool_dict:
                        tool_dict[search_key]['Coord_Num'] += self.get_drl_num(info,
                                                                               tool_dict[search_key]['T_Size_mm'])
            else:
                if paidao_start == 'yes':
                    if 'paidao_file' not in tool_dict:
                        tool_dict['paidao_file'] = info
                    elif 'paidao_file' in tool_dict:
                        tool_dict['paidao_file'] = tool_dict['paidao_file'] + '\n' + info
                else:
                    if 'head_file' not in tool_dict:
                        tool_dict['head_file'] = info
                    elif 'head_file' in tool_dict:
                        tool_dict['head_file'] = tool_dict['head_file'] + '\n' + info
        f.close()
        # print json.dumps (tool_dict, sort_keys=True, indent=2, separators=(',', ': '))
        return tool_dict

    def get_drl_num(self, row, slot_d_data):
        """
        坐标文件获取槽孔数量
        :param row: 钻孔输出的单行文件
        :param slot_d_data: 槽孔孔径
        :return: int，数量
        """

        if re.search("G85", row):
            tmp_data = row.split('G85')
            tmp_data1 = tmp_data[0].strip()
            tmp_data2 = tmp_data[1].strip()

            tmp_data3 = tmp_data1.split('Y')
            tmp_data4 = tmp_data2.split('Y')
            tmp_data5 = tmp_data3[0].strip().strip("X")
            tmp_data6 = tmp_data3[1].strip()
            tmp_data7 = tmp_data4[0].strip().strip("X")
            tmp_data8 = tmp_data4[1].strip()
            cor1_x = self.cor_to_float(tmp_data5)
            cor1_y = self.cor_to_float(tmp_data6)
            cor2_x = self.cor_to_float(tmp_data7)
            cor2_y = self.cor_to_float(tmp_data8)

            slot_l = Line(Point(cor1_x, cor1_y), Point(cor2_x, cor2_y)).getLen()
            # print slot_l

            # t = d - 1
            # slot_d_data = drl_order[t]
            # tmp_d_data = float(slot_d_data.split('C')
            slot_d = float(slot_d_data)
            slot_ll = float(slot_l + slot_d)
            multiple = float(slot_ll / slot_d)
            # multiple_data = []
            if multiple >= 3:
                multiple_data = [2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193]
            else:
                multiple_data = [2, 3, 5, 9, 17, 33, 65, 129, 257]

            tmp_bfg = math.sqrt(slot_d * 1000 * 16)
            slot_drl_no = float(slot_ll * 1000 / (2 * tmp_bfg))
            for value in multiple_data:
                if slot_drl_no <= value:
                    slot_drl_no = value
                    break
            return slot_drl_no
            # n = n + slot_drl_no
            # goto make_loop
        elif 'X' in row and 'Y' in row:
            return 1
        else:
            return 0

    def compare_two_table(self):
        """
        两个表格比较
        :return:
        """
        cam_row_num = self.tableWidget_CAM.rowCount()
        erp_row_num = self.tableWidget_ERP.rowCount()
        
        dic_layer_hole_info = self.get_pcs_pnl_hole_count_info(self.job_name, "panel", self.output_laser_layer)
        
        # === 1.判断两个表格的row是否一致，如果不一致需要在ERP的表中增加行（如果ERP行少），并在首位置打颜色标签
        if cam_row_num > erp_row_num:
            self.tableWidget_ERP.setRowCount(cam_row_num)
            for i in range(erp_row_num, cam_row_num + 1):
                self.exit_code = 1
                item = self.item_set('NG', forground_color='White', background_color='Red')
                self.tableWidget_ERP.setItem(i, 0, item)
        elif cam_row_num < erp_row_num:
            # self.tableWidget_ERP.setRowCount(cam_row_num)
            for i in range(cam_row_num - 1, erp_row_num):
                self.exit_code = 1
                item = self.item_set('NG', forground_color='White', background_color='Red')
                self.tableWidget_ERP.setItem(i, 0, item)

        arraylist_log = []
        dic_8mil_hole = {}
        dic_9mil_hole = {}
        dic_10mil_hole = {}
        for row in range(min(cam_row_num, erp_row_num)):
            cam_T_num = self.tableWidget_CAM.item(row, 0).text()
            erp_T_num = self.tableWidget_ERP.item(row, 1).text()

            cam_T_Size = self.tableWidget_CAM.item(row, 1).text()
            erp_T_Size = self.tableWidget_ERP.item(row, 2).text()

            cam_T_count = self.tableWidget_CAM.item(row, 2).text()
            erp_T_count = self.tableWidget_ERP.item(row, 3).text() if self.tableWidget_ERP.item(row, 3) else 0
            
            # if "-lyh" in self.job_name:
            if dic_layer_hole_info.get(str(cam_T_Size)) and dic_layer_hole_info.get(str(cam_T_Size)) != float(cam_T_count):  
                if str(cam_T_num) != "T23" and 'DA8620OC903B3'.lower() not in self.job_name:
                    log = "检测到{0}层孔径{1}资料内孔数:{2} 跟输出文件内孔数:{3}不一致,请检查回读文件是否异常!"
                    #if str(cam_T_num) == "T01" and float(cam_T_count) / dic_layer_hole_info.get(str(cam_T_Size)) in (2, 4, 6, 8):                        
                        #log = ""
                    
                    #if log:                        
                    arraylist_log.append(log.format(self.output_laser_layer, cam_T_Size,
                                                    dic_layer_hole_info.get(str(cam_T_Size)),
                                                    cam_T_count))
                    self.exit_code = 1
                
            #检测文件内打五遍的孔数是否一致 20240105 by lyh
            if str(cam_T_Size) in ("0.203", "0.204","0.205","0.206","0.207","0.208"):
                dic_8mil_hole[str(cam_T_Size)] = float(cam_T_count)
                
            if str(cam_T_Size) in ("0.229", "0.230","0.231","0.232","0.233","0.234"):
                dic_9mil_hole[str(cam_T_Size)] = float(cam_T_count)
                
            if str(cam_T_Size) in ("0.253","0.254","0.255","0.256","0.257","0.258", "0.259"):
                dic_10mil_hole[str(cam_T_Size)] = float(cam_T_count)
                
            print cam_T_num, cam_T_Size, erp_T_Size
            try:                
                if cam_T_num == erp_T_num and abs(float(cam_T_Size) - float(erp_T_Size)) < 0.01:
                    if cam_T_count == erp_T_count:
                        item = self.item_set('Pass', forground_color='White', background_color='Green')
                        self.tableWidget_ERP.setItem(row, 0, item)
                    else:
                        if int(cam_T_count) == 0:
                            # 增加丢孔的情况拦截 20230824 by lyh
                            self.exit_code = 1
                            item = self.item_set('NG', forground_color='White', background_color='Red')
                            self.tableWidget_ERP.setItem(row, 0, item)
                        else:
                            item = self.item_set('Check', forground_color='White', background_color='Orange')
                            self.tableWidget_ERP.setItem(row, 0, item)
                else:
                    if cam_T_num == 'T500' and erp_T_num == "T02" and cam_T_Size == erp_T_Size:
                        item = self.item_set('Pass', forground_color='White', background_color='Green')
                        self.tableWidget_ERP.setItem(row, 0, item)
                    elif cam_T_num == 'T28' and erp_T_num == "T28" and cam_T_Size != erp_T_Size:
                        # T28 此刀会存在孔径不一致的情况 这里不做孔径大小比对20241101
                        item = self.item_set('Check', forground_color='White', background_color='Orange')
                        self.tableWidget_ERP.setItem(row, 0, item)                        
                    else:
                        self.exit_code = 1
                        item = self.item_set('NG', forground_color='White', background_color='Red')
                        self.tableWidget_ERP.setItem(row, 0, item)
            except Exception, e:
                print "error:-------------->", e
                self.exit_code = 1
                item = self.item_set('NG', forground_color='White', background_color='Red')
                self.tableWidget_ERP.setItem(row, 0, item)                

        if arraylist_log:            
            msg_box = msgBox()
            msg_box.critical(self, '错误', "\n".join(arraylist_log), QMessageBox.Ok)
            # self.exit_code = 1
            
               
        if len(dic_8mil_hole.keys()) >=5:
            if len(set(dic_8mil_hole.values())) != 1:
                msg_box = msgBox()
                msg_box.critical(self, '错误', "检测到8mil孔打五遍孔数异常，五把刀的孔数有不一致的情况，请检查回读文件是否异常！{0}".format(dic_8mil_hole), QMessageBox.Ok)                
                self.exit_code = 1
                
        #
        if len(dic_9mil_hole.keys()) >=5:
            if len(set(dic_9mil_hole.values())) != 1:
                msg_box = msgBox()
                msg_box.critical(self, '错误', "检测到9mil孔打五遍孔数异常，五把刀的孔数有不一致的情况，请检查回读文件是否异常！{0}".format(dic_9mil_hole), QMessageBox.Ok)                
                self.exit_code = 1        
                
        if len(dic_10mil_hole.keys()) >=5:
            if len(set(dic_10mil_hole.values())) != 1:
                msg_box = msgBox()
                msg_box.critical(self, '错误', "检测到10mil孔打五遍孔数异常，五把刀的孔数有不一致的情况，请检查回读文件是否异常！{0}".format(dic_10mil_hole), QMessageBox.Ok)                
                self.exit_code = 1
                    
    def change_t_header(self):        
        lines = file(self.laser_file_path).readlines()
        if "T10\n" in lines and "T10C" not in "".join(lines):
            msg_box = msgBox()
            msg_box.critical(self, '错误', '分割钻带暂时不支持手动排刀序！' , QMessageBox.Ok)
            if top.getUser() not in ["84310", "44566"]:                
                return
        
        self.hide()
        main = reorder_drill(parent=None,file_path=self.laser_file_path, inplan_drill_info=self.erp_dict, drillname=self.cam_drl_name)
        main.exec_()
        self.exit_code = 0
        self.start_read_file_and_show_ui()
        self.show()
        
        if self.exit_code == 0:
            self.reorder_t_header.hide()
            self.pushButton_close.setText(_fromUtf8('继续'))
            
    def get_pcs_pnl_hole_count_info(self, jobname, stepname, drill_layer):
        """"""
        job = gClasses.Job(jobname)
        matrixinfo = job.matrix.getInfo()
        dic_layer_hole_info = {}
        if stepname in matrixinfo["gCOLstep_name"]:
            step = gClasses.Step(job, stepname)
            step.open()

            if drill_layer in matrixinfo["gROWname"]:
                STR = r'-t layer -e %s/%s/%s -d TOOL -o break_sr,units=mm' % (jobname, stepname, drill_layer)
                gTOOLdrill_size = step.DO_INFO(STR)['gTOOLdrill_size']
                gTOOLslot_len = step.DO_INFO(STR)['gTOOLslot_len']
                gTOOLcount = step.DO_INFO(STR)['gTOOLcount']
                gTOOLtype = step.DO_INFO(STR)['gTOOLtype']
                for size, slot_len, pnl_count,tool_type in zip(gTOOLdrill_size, gTOOLslot_len, gTOOLcount, gTOOLtype):
                    if dic_layer_hole_info.has_key(str(size*0.001)):
                        dic_layer_hole_info[str(size*0.001)] += pnl_count
                    else:
                        dic_layer_hole_info[str(size*0.001)] = pnl_count                                    
        
        return dic_layer_hole_info
            
    def item_set(self, text, forground_color='Black', background_color='White'):
        """
        构造表格item，并添加前后背景色
        :param text:
        :param forground_color:
        :param background_color:
        :return:
        """
        item = QtGui.QTableWidgetItem(text)
        brush = QtGui.QBrush(QtGui.QColor(background_color))
        brush.setStyle(QtCore.Qt.SolidPattern)
        item.setBackground(brush)
        brush = QtGui.QBrush(QtGui.QColor(forground_color))
        brush.setStyle(QtCore.Qt.NoBrush)
        item.setForeground(brush)
        return item


class Point(object):
    """创建一个点的类"""

    def __init__(self, x=0, y=0):
        """初始化点的坐标（x,y）"""
        self.x = float(x)
        self.y = float(y)

    def getX(self):
        """获取点的X轴坐标"""
        return self.x

    def getY(self):
        """获取点的Y轴坐标"""
        return self.y


class Line(object):
    """
    定义一个线类
    """

    def __init__(self, p1, p2):
        """初始化线的两个点"""
        self.x = p1.getX() - p2.getX()
        self.y = p1.getY() - p2.getY()
        # 勾股定理计算
        self.len = math.sqrt(abs(self.x) * abs(self.x) + abs(self.y) * abs(self.y))

    def getLen(self):
        """获取直线长度"""
        return self.len


# # # # --程序入口
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    W = CompareDrl()
    W.show()
    sys.exit(app.exec_())


# 2023.03.08 Song 1.多层料号：HB1308PL517A1 非对称合并层，合并ERP数据报错，增加判断


