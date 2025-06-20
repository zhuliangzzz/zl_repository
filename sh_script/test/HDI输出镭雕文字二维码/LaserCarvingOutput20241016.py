#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:LaserCarvingOutput.py
   @author:zl
   @time: 2024/10/14 16:53
   @software:PyCharm
   @desc:
"""
import json
import os
import re
import sys
from PyQt4 import QtGui, QtCore
import LaserCarvingOutputUI_pyqt4 as ui
import platform

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genesisPackages
import gClasses
import Oracle_DB
import genCOM_26

GEN = genCOM_26.GEN_COM()

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class LaserCarvingOutput(QtGui.QWidget, ui.Ui_Form):
    def __init__(self):
        super(LaserCarvingOutput, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.AppVer = '1.5'
        self.job_name = os.environ.get('JOB')
        self.step_name = os.environ.get('STEP')
        self.pnl_step = 'panel'
        self.job = gClasses.Job(self.job_name)
        self.op_2dbc_dict = {}
        self.DB_O = Oracle_DB.ORACLE_INIT()
        # 连接ERP 获取板厚信息
        self.dbc_o = self.DB_O.DB_CONNECT(host='172.20.218.247', servername='topprod', port='1521',
                                          username='zygc', passwd='ZYGC@2019')
        thickdict = self.geterpthickness(self.dbc_o, self.job_name)
        self.boardthick = ''
        if 'THICKNESS' in thickdict[0]:
            self.boardthick = thickdict[0]['THICKNESS']

        self.lineEdit_matrix.setText('0')
        if platform.system() == "Windows":
            self.output_dir = 'D:/disk/film/' + self.job_name
        elif platform.system() == "Linux":
            self.output_dir = '/id/workfile/film/' + self.job_name
        self.pre_show_ui()
        if self.dbc_o:
            self.DB_O.DB_CLOSE(self.dbc_o)
        self.label_job.setText('Job:' + self.job_name)
        symbols = list(filter(lambda symbol: symbol.startswith('2dbc'), os.listdir('/incam/server/site_data/library/symbols')))
        orientions = ['0', '90', '180', '270']
        self.comboBox_topSize.addItems(symbols)
        self.comboBox_botSize.addItems(symbols)
        self.comboBox_topOrient.addItems(orientions)
        self.comboBox_botOrient.addItems(orientions)
        self.lineEdit.setReadOnly(True)
        # self.comboBox_botOrient.setEnabled(False)
        self.comboBox_topSize.currentIndexChanged.connect(self.asyncToBot)
        self.pushButton_addcode.clicked.connect(self.addCode)
        self.pushButton_output.clicked.connect(self.output)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)
        # self.setStyleSheet('QGroupBox{border:1px sold black;}')
    def pre_show_ui(self):
        proflie_info = GEN.getProMinMax(self.job_name, self.pnl_step)
        if proflie_info['proXmin'] != '0' or proflie_info['proYmin'] != '0':
            M = M_Box()
            showText = M.msgText(u'提示', u"Step %s 原点未在 0 0 位置,请注意!" % self.pnl_step, showcolor='red')
            M.msgBox(showText)
        pnlx = float(proflie_info['proXmax']) - float(proflie_info['proXmin'])
        pnly = float(proflie_info['proYmax']) - float(proflie_info['proYmin'])
        self.lineEdit_pnlx.setText(str(pnlx))
        self.lineEdit_pnly.setText(str(pnly))
        if self.boardthick:
            self.lineEdit_boardthickness.setText(str(self.boardthick))

        # 20241015 获取二维码面次相关信息
        self.dbc_h = self.DB_O.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
                                          username='GETDATA', passwd='InplanAdmin')
        sql = """SELECT
                i.ITEM_NAME AS JobName,
                p.value
            FROM
                VGT_hdi.PUBLIC_ITEMS i,
                VGT_hdi.JOB_DA job,
                VGT_HDI.field_enum_translate p   
            where  
                i.ITEM_NAME = '%s'
                AND i.item_id = job.item_id
                AND i.revision_id = job.revision_id
                and p.fldname = 'CI_2D_BARCODE_POSITION_SET_'
                and p.enum=job.CI_2D_BARCODE_POSITION_SET_
                and p.intname = 'JOB'""" % self.job_name.upper()[:13]  # --截取前十三位料号名
        dataVal = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        self.lineEdit.setText(dataVal[0].get('VALUE').decode('utf-8'))

    def asyncToBot(self):
        self.comboBox_botSize.setCurrentIndex(self.comboBox_topSize.currentIndex())

    def addCode(self):
        self.hide()
        layer = self.lineEdit.text()
        top_symbol, top_angle = self.comboBox_topSize.currentText(), int(self.comboBox_topOrient.currentText())
        bot_symbol, bot_angle = self.comboBox_botSize.currentText(), int(self.comboBox_botOrient.currentText())
        step = 'set'
        GEN.COM('open_entity,job=%s,type=step,name=%s,iconic=no' % (self.job_name, step))
        GEN.AUX('set_group,group=%s' % GEN.COMANS)
        GEN.CHANGE_UNITS('mm')
        GEN.CLEAR_LAYER()
        layer_c, layer_s = '2dbc-c', '2dbc-s'
        # if 'C面' in self.lineEdit.text():
        #     GEN.CREATE_LAYER(layer_c)
        # if 'S面' in self.lineEdit.text():
        #     GEN.CREATE_LAYER(layer_s)
        GEN.VOF()
        GEN.DELETE_LAYER(layer_c)
        GEN.DELETE_LAYER(layer_s)
        GEN.VON()
        GEN.CREATE_LAYER(layer_c)
        GEN.CREATE_LAYER(layer_s)
        GEN.WORK_LAYER(layer_c)
        GEN.MOUSE('点击选择添加位置')
        x,y = GEN.MOUSEANS.split()
        x,y  = float(x), float(y)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(layer_c, 'yes')
        # GEN.FILTER_OPTION_ATTR('.string','2dmark')
        GEN.COM('cur_atr_set,attribute=.string,text=2dmark')
        GEN.ADD_PAD(x,y, top_symbol, angle=top_angle, attr='yes')
        GEN.COM('cur_atr_reset')
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(layer_s, 'yes')
        GEN.COM('cur_atr_set,attribute=.string,text=2dmark')
        GEN.ADD_PAD(x, y, bot_symbol, angle=top_angle, attr='yes')
        GEN.COM('sel_transform,oper=rotate;mirror,x_anchor=0,y_anchor=0,angle=180,direction=ccw,x_scale=1,y_scale=1,x_offset=0,y_offset=0,mode=axis,duplicate=no')
        GEN.COM('cur_atr_reset')
        GEN.CLEAR_LAYER()
        GEN.COM('open_entity,job=%s,type=step,name=%s,iconic=no' % (self.job_name, self.pnl_step))
        GEN.AUX('set_group,group=%s' % GEN.COMANS)
        GEN.CHANGE_UNITS('mm')
        GEN.CLEAR_LAYER()
        # 获取panel上下板边y值
        yminList, ymaxList = [], []
        info =  self.job.DO_INFO('-t step -e ' + self.job.name + '/' + self.pnl_step + ' -d SR,units=mm')
        pnl_step = self.job.steps.get(self.pnl_step)
        for step, ymin, ymax in zip(info.get('gSRstep'), info.get('gSRymin'), info.get('gSRymax')):
            if step == 'set':
                yminList.append(ymin)
                ymaxList.append(ymax)
        ymin, ymax = min(yminList), max(ymaxList)
        coors = []
        if GEN.LAYER_EXISTS(layer_c, self.job_name, self.pnl_step):
            signal_layer = 'l1'
            GEN.AFFECTED_LAYER(signal_layer, 'yes')
            GEN.FILTER_RESET()
            GEN.FILTER_SET_INCLUDE_SYMS('sh-dwsig*')
            GEN.FILTER_SELECT()
            if GEN.GET_SELECT_COUNT() > 0:
                # 找出四个光点
                info = pnl_step.INFO('-t layer -e %s/%s/%s -d FEATURES -o select, units=mm' % (self.job_name, self.pnl_step, signal_layer))
                del info[0]
                for line in info:
                    x, y = float(line.split()[1]), float(line.split()[2])
                    if y < ymin or y > ymax:
                        coors.append((x,y))
            GEN.FILTER_RESET()
            GEN.CLEAR_LAYER()
            if coors:
                GEN.AFFECTED_LAYER(layer_c, 'yes')
                for coor in coors:
                    pnl_step.addPad(coor[0], coor[1], 'r0.2')
                GEN.CLEAR_LAYER()
        coors = []
        if GEN.LAYER_EXISTS(layer_s, self.job_name, self.pnl_step):
            signal_layer = 'l%s' % len(self.job.matrix.returnRows('board', 'signal|power_ground'))
            GEN.AFFECTED_LAYER(signal_layer, 'yes')
            GEN.FILTER_RESET()
            GEN.FILTER_SET_INCLUDE_SYMS('sh-dwsig*')
            GEN.FILTER_SELECT()
            if GEN.GET_SELECT_COUNT() > 0:
                # 找出四个光点
                info = pnl_step.INFO(
                    '-t layer -e %s/%s/%s -d FEATURES -o select, units=mm' % (self.job_name, self.pnl_step, signal_layer))
                del info[0]
                for line in info:
                    x, y = float(line.split()[1]), float(line.split()[2])
                    if y < ymin or y > ymax:
                        coors.append((x, y))
            GEN.FILTER_RESET()
            GEN.CLEAR_LAYER()
            if coors:
                GEN.AFFECTED_LAYER(layer_s, 'yes')
                for coor in coors:
                    pnl_step.addPad(coor[0], coor[1], 'r0.2')
                GEN.CLEAR_LAYER()
        GEN.PAUSE('请确认')
        M = M_Box()
        showText = M.msgText(u'提示', u"添加二维码完成", showcolor='green')
        M.msgBox(showText)
        self.show()



    def output(self):
        self.hide()
        self.get_add_2dbc()
        if len(self.op_2dbc_dict.keys()) == 0:
            M = M_Box()
            showText = M.msgText(u'提示', u"无二维码及明码设计!", showcolor='red')
            M.msgBox(showText)
            exit(0)
        elif len(self.op_2dbc_dict.keys()) == 1:
            self.label_tips.setText(u"Tips:常规设计，仅%s 面次设计二维码" % self.op_2dbc_dict.keys()[0])
            # 常规：蓝色
            self.label_tips.setStyleSheet(_fromUtf8("color:rgb(0, 0, 255)"))
        elif len(self.op_2dbc_dict.keys()) == 2:
            self.label_tips.setText(u"Tips特殊设计，两面次均设计二维码")
            # 非常规：红色
            self.label_tips.setStyleSheet(_fromUtf8("color:rgb(255, 0, 0)"))

        # === 增加光点数量判断，如果不为4，程序退出 ===
        get_mark_result = [self.op_2dbc_dict[i]['mark_num'] for i in self.op_2dbc_dict]
        for key in self.op_2dbc_dict:
            if self.op_2dbc_dict[key]['mark_num'] == '':
                M = M_Box()
                showText = M.msgText(u'提示', u"面次%s,未设计光点，程序退出!" % key, showcolor='red')
                M.msgBox(showText)
                exit(0)
            if int(self.op_2dbc_dict[key]['mark_num']) != 4:
                M = M_Box()
                showText = M.msgText(u'提示',
                                     u"面次%s,光点数量为%s,应为4，程序退出!" % (key, self.op_2dbc_dict[key]['mark_num']),
                                     showcolor='red')
                M.msgBox(showText)
                exit(0)

        # === 二维码行列矩阵 ===
        coderulex = self.lineEdit_matrix.text()
        pnlx = self.lineEdit_pnlx.text()
        pnly = self.lineEdit_pnly.text()
        thick = self.lineEdit_boardthickness.text()
        coderule2x = coderulex

        # 脚本运行时不显示##
        GEN.COM('disp_off')
        step_datum = self.all_step_fill_copper()
        GEN.OPEN_STEP(self.pnl_step)
        GEN.CLEAR_LAYER()
        GEN.CHANGE_UNITS('mm')
        GEN.FILTER_RESET()

        for side in self.op_2dbc_dict.keys():
            all_cor, pnl_cor, mark_cor = self.get_all_cor(side)
            # print json.dumps(all_cor,indent=2)
            # print json.dumps(pnl_cor,indent=2)
            # print json.dumps(mark_cor,indent=2)
            op_file_name = self.write_2dbc_file(side, coderulex, coderule2x, thick, pnlx, pnly, mark_cor, all_cor,
                                                pnl_cor)
            self.reread_2dbc_file(op_file_name, side)

        GEN.DELETE_LAYER('dc_s_ck')
        GEN.DELETE_LAYER('dc_p_ck')
        GEN.DELETE_LAYER('pcs_s_ck')

        GEN.COM('disp_on')
        # GEN.PAUSE('OK')
        M = M_Box()
        showText = M.msgText(u'提示', u"输出二维码坐标完成", showcolor='green')
        M.msgBox(showText)

    def get_add_2dbc(self):
        # 判断2dbc-c是否存在##
        op_type = []
        # flatten 层别及确定面次
        GEN.OPEN_STEP(self.pnl_step, job=self.job_name)
        GEN.CHANGE_UNITS('mm')
        GEN.CLEAR_LAYER()
        GEN.DELETE_LAYER('2dbc-pnl-top')
        GEN.DELETE_LAYER('2dbc-pnl-bot')
        pnl_silk_top = '2dbc-top-silk'
        pnl_silk_bot = '2dbc-bot-silk'
        GEN.DELETE_LAYER(pnl_silk_top)
        GEN.DELETE_LAYER(pnl_silk_bot)

        # === 获取所有的top面文字及bot面文字，在panel中合并为top silk 及bot silk 替换以下的c1及c2层别
        all_silk_layers = GEN.GET_ATTR_LAYER('silk_screen', job=self.job_name)
        top_silk_layer = []
        bot_silk_layer = []
        for slayer in all_silk_layers:
            # === 获取文字层面次，加到不同的列表里 ===
            if GEN.DO_INFO("-t layer -e %s/%s/%s -d SIDE" % (self.job_name, self.step_name, slayer))['gSIDE'] == 'top':
                top_silk_layer.append(slayer)
            elif GEN.DO_INFO("-t layer -e %s/%s/%s -d SIDE" % (self.job_name, self.step_name, slayer))[
                'gSIDE'] == 'bottom':
                bot_silk_layer.append(slayer)
            else:
                M = M_Box()
                showText = M.msgText(u'提示', u"无法获取文字层%s 面次，程序退出!" % slayer, showcolor='red')
                M.msgBox(showText)
                exit(0)

        if len(top_silk_layer) != 0:
            for l_index, l_item in enumerate(top_silk_layer):
                tmp_layer = '__tmp_2dbc_silk_%s__' % l_index
                GEN.CLEAR_LAYER()
                GEN.DELETE_LAYER(tmp_layer)
                GEN.COM('flatten_layer,source_layer=%s,target_layer=%s' % (l_item, tmp_layer))
                GEN.AFFECTED_LAYER(tmp_layer, 'yes')
                GEN.SEL_COPY(pnl_silk_top)
                GEN.DELETE_LAYER(tmp_layer)
                GEN.CLEAR_LAYER()

        if len(bot_silk_layer) != 0:
            for l_index, l_item in enumerate(bot_silk_layer):
                tmp_layer = '__tmp_2dbc_silk_%s__' % l_index
                GEN.CLEAR_LAYER()
                GEN.DELETE_LAYER(tmp_layer)
                GEN.COM('flatten_layer,source_layer=%s,target_layer=%s' % (l_item, tmp_layer))
                GEN.AFFECTED_LAYER(tmp_layer, 'yes')
                GEN.SEL_COPY(pnl_silk_bot)
                GEN.DELETE_LAYER(tmp_layer)
                GEN.CLEAR_LAYER()

        # === 进行二维码及明码是否有被top及bot文字层cover的检测
        type_code = self.flattendc('2dbc-c', pnl_silk_top, '2dbc-pnl-top')
        if type_code == 'yes':
            op_type.append('top')

        type_code = self.flattendc('2dbc-s', pnl_silk_bot, '2dbc-pnl-bot')
        if type_code == 'yes':
            op_type.append('bot')
        # === 2020.12.22 回收无用层 ===
        GEN.DELETE_LAYER(pnl_silk_top)
        GEN.DELETE_LAYER(pnl_silk_bot)

        if len(op_type) == 0:
            GEN.COM('disp_on')
            # GEN.PAUSE('No 2d code layer or symbol Now Exit')
            M = M_Box()
            showText = M.msgText(u'提示', u"无二维码symbol及层别设计，程序退出!", showcolor='red')
            M.msgBox(showText)

            exit(0)
            # exit()

        # === 判断输出的二维码及明码类型，
        # === 二维码，明码，二维码及明码
        # === 二维码有几种，明码几种，
        pre_2dbc_info = {'2dbc_add': False, '2dbc_type': 1, 'mm_add': False, 'mm_type': 1}
        for side in op_type:
            check_layer = '2dbc-pnl-%s' % side
            pre_2dbc_info['2dbc_add'] = True
            g_symbol_hist = GEN.DO_INFO(
                "-t layer -e %s/%s/%s -d SYMS_HIST" % (self.job_name, self.pnl_step, check_layer))
            # === 分割明码及二维码数量，
            list_mm = []
            list_2dbc = []
            other_list = []
            size_2dbc = []
            size_mm = []
            num_2dbc = []
            num_mm = []
            mark_num = ''
            for index, item in enumerate(g_symbol_hist['gSYMS_HISTsymbol']):
                if re.match(r"2dbc_(\d\d?.?\d?\d?)mm_?(\d?\d?.?\d?\d?)$", item):
                    list_2dbc.append(item)
                    num_2dbc.append(g_symbol_hist['gSYMS_HISTpad'][index])
                    size_2dbc.append(re.match(r"2dbc_(\d\d?.?\d?\d?)mm_?(\d?\d?.?\d?\d?)$", item).group(1))
                elif re.match(r"2dtext_(\d\d?.?\d?\d?x\d\d?.?\d?\d?)mm_?(\d?\d?.?\d?\d?)$", item):
                    list_mm.append(item)
                    num_mm.append(g_symbol_hist['gSYMS_HISTpad'][index])
                    size_mm.append(
                        re.match(r"2dtext_(\d\d?.?\d?\d?x\d\d?.?\d?\d?)mm_?(\d?\d?.?\d?\d?)$", item).group(1))
                elif re.match(r"r0.2", item):
                    mark_num = g_symbol_hist['gSYMS_HISTpad'][index]
                else:
                    other_list.append(item)

            self.op_2dbc_dict[side] = {}
            self.op_2dbc_dict[side]['num_2dbc_op'] = num_2dbc
            self.op_2dbc_dict[side]['type_num_2dbc'] = len(list_2dbc)
            self.op_2dbc_dict[side]['num_mm_op'] = num_mm
            self.op_2dbc_dict[side]['type_num_mm'] = len(list_mm)
            self.op_2dbc_dict[side]['size_2dbc'] = size_2dbc
            self.op_2dbc_dict[side]['size_mm'] = size_mm
            self.op_2dbc_dict[side]['mark_num'] = mark_num
            if len(other_list) != 0:
                M = M_Box()
                showText = M.msgText(u'提示', u"面次%s二维码层别添加的symbol不符合要求!" % side, showcolor='red')
                M.msgBox(showText)
                self.op_2dbc_dict[side]['errors'] = [u"面次%s二维码层别添加的symbol不符合要求!" % side, ]
        # print json.dumps(self.op_2dbc_dict)

    def flattendc(self, fir_pcs_lay, sec_pcs_lay, pnl_lay):
        # === 先打散，再过滤是否满足条件
        tmp_layer = 'tmp_' + pnl_lay
        type_code = 'no'
        GEN.DELETE_LAYER(tmp_layer)
        # === 2020.12.22 增加层别类型的定义。用于判断添加的2dbc是否被文字层cover ===
        dc_layer_type = ''
        # === 第一种层别存在，则不考虑第二层
        if GEN.LAYER_EXISTS(fir_pcs_lay, job=self.job_name, step=self.pnl_step) == 'yes':
            GEN.COM('flatten_layer,source_layer=%s,target_layer=%s' % (fir_pcs_lay, tmp_layer))
            dc_layer_type = 'one'
        else:
            if GEN.LAYER_EXISTS(sec_pcs_lay, job=self.job_name, step=self.pnl_step) == 'yes':
                GEN.COM('flatten_layer,source_layer=%s,target_layer=%s' % (sec_pcs_lay, tmp_layer))
                dc_layer_type = 'two'
        if GEN.LAYER_EXISTS(tmp_layer, job=self.job_name, step=self.pnl_step) == 'yes':
            GEN.CLEAR_LAYER()
            GEN.CHANGE_UNITS('mm')
            GEN.AFFECTED_LAYER(tmp_layer, 'yes')
            GEN.FILTER_RESET()
            GEN.FILTER_SET_INCLUDE_SYMS('2dbc*\;2dtext*')
            GEN.FILTER_SELECT()
            sel_num = GEN.GET_SELECT_COUNT()

            if int(sel_num) != 0:
                type_code = 'yes'
                GEN.SEL_MOVE(pnl_lay)
                GEN.FILTER_RESET()
                GEN.FILTER_SET_INCLUDE_SYMS('r0.2')  # mm
                GEN.FILTER_SELECT()
                if int(GEN.GET_SELECT_COUNT()) > 0:
                    GEN.SEL_MOVE(pnl_lay)
            else:
                type_code = 'no'

            GEN.FILTER_RESET()
            # GEN.FILTER_OPTION_ATTR(attr='.string\,text=2dmark')
            GEN.FILTER_TEXT_ATTR('.string', '2dmark')
            GEN.FILTER_SELECT()
            sel_num = GEN.GET_SELECT_COUNT()
            if int(sel_num) != 0:
                GEN.COM('disp_on')
                M = M_Box()
                showText = M.msgText(u'提示', u'%s layer have pad with attribute .string=2dmark is not 2d symbol name'
                                     % tmp_layer, showcolor='red')
                M.msgBox(showText)
                exit(0)
            # === 增加镭雕码，是否有白油块的检测 ===
            silk_area_check = 'yes'
            if type_code == 'yes':
                chk_source_layer = ''
                if dc_layer_type == 'one':
                    chk_source_layer = sec_pcs_lay
                    if GEN.LAYER_EXISTS(sec_pcs_lay, job=self.job_name, step=self.pnl_step) == 'no':
                        silk_area_check = 'no'
                elif dc_layer_type == 'two':
                    chk_source_layer = tmp_layer
                if silk_area_check == 'yes':
                    GEN.CLEAR_LAYER()
                    GEN.AFFECTED_LAYER(pnl_lay, 'yes')
                    GEN.FILTER_RESET()
                    GEN.COM('adv_filter_reset, filter_name = popup')
                    GEN.COM('filter_atr_reset')
                    GEN.SEL_REF_FEAT(chk_source_layer, 'cover')
                    if int(GEN.GET_SELECT_COUNT()) == 0:
                        M = M_Box()
                        showText = M.msgText(u'提示',
                                             u'Error:001 层别:%s 没有白油包含镭雕码，程序退出'
                                             % chk_source_layer, showcolor='red')
                        M.msgBox(showText)
                        exit(0)
                    else:
                        GEN.SEL_REVERSE()
                        GEN.FILTER_RESET()
                        GEN.FILTER_SET_INCLUDE_SYMS('r0.2')  # mm
                        GEN.FILTER_SELECT(op='unselect')
                        if int(GEN.GET_SELECT_COUNT()) > 0:
                            M = M_Box()
                            showText = M.msgText(u'提示',
                                                 u'Error:002 层别:%s 没有白油包含镭雕码，程序退出'
                                                 % chk_source_layer, showcolor='red')
                            M.msgBox(showText)
                            # exit(0)
                else:
                    M = M_Box()
                    showText = M.msgText(u'提示',
                                         u'文字层不存在，不检测“白油块包含镭雕码”，继续', showcolor='green')
                    M.msgBox(showText)

            GEN.DELETE_LAYER(tmp_layer)
        return type_code
    def get_mark_cor(self, work_layer):
        """
        获取光学点坐标
        :param work_layer:
        :return:
        """
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(work_layer,'yes')
        GEN.FILTER_RESET()
        GEN.FILTER_SET_INCLUDE_SYMS('r0.2')
        GEN.FILTER_SELECT()
        pnli = GEN.DO_INFO ('-t step -e %s/%s -d PROF_LIMITS, units=mm' % (self.job_name, self.pnl_step))
        # pnl_xmax = float(pnli['gPROF_LIMITSxmax'])
        # pnl_ymax = float(pnli['gPROF_LIMITSymax'])
        # pnl_x_center = pnl_xmax * 0.5
        # pnl_y_center = pnl_ymax * 0.5
        # 坐标不在原点位置要计算坐标 -ynh20230826
        pnl_xmax = float(pnli['gPROF_LIMITSxmax']) - float(pnli['gPROF_LIMITSxmin'])
        pnl_ymax = float(pnli['gPROF_LIMITSymax']) - float(pnli['gPROF_LIMITSymin'])
        pnl_x_center = float(pnli['gPROF_LIMITSxmin']) + pnl_xmax * 0.5
        pnl_y_center = float(pnli['gPROF_LIMITSymin']) + pnl_ymax * 0.5
        get_mark_cor = GEN.INFO('-t layer -e %s/%s/%s -d FEATURES -o select, units=mm' % (self.job_name, self.pnl_step, work_layer))
        mark_cor_dict = {}

        for mark_line in get_mark_cor[1:]:
            cur_x_cor = float(mark_line.split(' ')[1])
            cur_y_cor = float(mark_line.split(' ')[2])
            # === 左下
            if cur_x_cor < pnl_x_center and cur_y_cor < pnl_y_center:
                mark_cor_dict['ws'] = [cur_x_cor, cur_y_cor]
            # === 右下
            elif cur_x_cor > pnl_x_center and cur_y_cor < pnl_y_center:
                mark_cor_dict['es'] = [cur_x_cor, cur_y_cor]
            # === 左上
            elif cur_x_cor < pnl_x_center and cur_y_cor > pnl_y_center:
                mark_cor_dict['wn'] = [cur_x_cor, cur_y_cor]
            # === 右上
            elif cur_x_cor > pnl_x_center and cur_y_cor > pnl_y_center:
                mark_cor_dict['en'] = [cur_x_cor, cur_y_cor]
        GEN.AFFECTED_LAYER(work_layer,'no')

        return mark_cor_dict
    def write_2dbc_file(self, side, coderulex, coderule2x, thick, pnlx, pnly, mark_cor_dict, al_cor, pnl_cor):
        # 写表头
        # === 1.行列矩阵，默认为14x14，可支持两种类型 ===
        heads = []
        marks = []
        r_cors = []
        r_pnl_cors = []

        # === 4.写光点坐标 ===#
        # heads.append('#####\n')
        for direct in ['ws', 'es', 'wn', 'en']:
            if side == 'top':
                mark_x = mark_cor_dict[direct][0]
                mark_y = mark_cor_dict[direct][1]
            else:
                mark_x = -mark_cor_dict[direct][0]
                mark_y = mark_cor_dict[direct][1]
            marks.append('X=%.3f;Y=%.3f\n' % (mark_x, mark_y))
            # GEN.ADD_TEXT(mark_x, mark_y, 'Fp', 1.27, 2.54, angle='0')

        # f.write('#####\n')
        # === 5.写所有坐标 ===#
        # print al_cor
        set_cor_exist = 'no'
        for i in range(len(al_cor)):
            r_cors.append("X=%.3f;Y=%.3f;Ang=%s;Type=%s;Set=%s;Unit=%s;UseBarcodeSize=%s;UseTextSize=%s\n"
                          % (al_cor[i]['x'], al_cor[i]['y'], al_cor[i]['angle'], al_cor[i]['bc_type'],
                             al_cor[i]['set_index'],
                             al_cor[i]['unit_index'], al_cor[i]['use_bc_size'], al_cor[i]['use_text_size']))
            if al_cor[i]['unit_index'] == 0:
                set_cor_exist = 'yes'
        for pn_ii in range(len(pnl_cor)):
            print
            pn_ii
            r_pnl_cors.append("X=%.3f;Y=%.3f;Ang=%s;Type=%s;Set=%s;Unit=%s;UseBarcodeSize=%s;UseTextSize=%s\n"
                              % (pnl_cor[pn_ii]['x'], pnl_cor[pn_ii]['y'], pnl_cor[pn_ii]['angle'],
                                 pnl_cor[pn_ii]['bc_type'],
                                 pnl_cor[pn_ii]['set_index'], pnl_cor[pn_ii]['unit_index'],
                                 pnl_cor[pn_ii]['use_bc_size'],
                                 pnl_cor[pn_ii]['use_text_size']))

        heads.append('Coderule=%s*%s\n' % (coderulex, coderulex))
        heads.append('Coderule2=%s*%s\n' % (coderule2x, coderule2x))

        # print self.op_2dbc_dict
        if 'size_2dbc' in self.op_2dbc_dict[side] and len(self.op_2dbc_dict[side]['size_2dbc']) > 0:
            codesize = self.op_2dbc_dict[side]['size_2dbc'][0]
            if self.op_2dbc_dict[side]['type_num_2dbc'] == 2:
                codesize2 = self.op_2dbc_dict[side]['size_2dbc'][1]
            else:
                codesize2 = codesize
        else:
            codesize = 0
            codesize2 = 0
        heads.append('CodeSize=%s*%s\n' % (codesize, codesize))
        heads.append('CodeSize2=%s*%s\n' % (codesize2, codesize2))

        try:
            txtsize = 'TxtSize=%s' % (re.sub(r"x", "*", self.op_2dbc_dict[side]['size_mm'][0]))
        except IndexError:
            txtsize = 'TxtSize=%s*%s' % (0, 0)
        # f.write('TxtSize2=%s*%s\n' % (txtsize2x, txtsize2y))
        try:
            txtsize2 = 'TxtSize2=%s' % (
                re.sub(r"x", "*", self.op_2dbc_dict[side]['size_mm'][1]) if self.op_2dbc_dict[side][
                                                                                'type_num_mm'] == 2 else re.sub(r"x",
                                                                                                                "*",
                                                                                                                self.op_2dbc_dict[
                                                                                                                    side][
                                                                                                                    'size_mm'][
                                                                                                                    0]))
        except IndexError:
            txtsize2 = 'TxtSize2=%s*%s' % (0, 0)
        heads.append('%s\n' % txtsize)
        heads.append('%s\n' % txtsize2)

        if set_cor_exist == 'yes':
            heads.append('SETCodeSize=%s*%s\n' % (codesize, codesize))
            heads.append('SETCodeSize2=%s*%s\n' % (codesize2, codesize2))
            heads.append('SET%s\n' % txtsize)
            heads.append('SET%s\n' % txtsize2)
        if len(pnl_cor) != 0:
            heads.append('PNLCodeSize=%s*%s\n' % (codesize, codesize))
            heads.append('PNLCodeSize2=%s*%s\n' % (codesize2, codesize2))
            heads.append('PNL%s\n' % txtsize)
            heads.append('PNL%s\n' % txtsize2)

        heads.append('Thick=%s\n' % thick)
        heads.append('Width=%s\n' % pnlx)
        heads.append('Length=%s\n' % pnly)

        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)
        # #song change in 20170815 for SOP change bot to bottom ##
        file_name = ''
        if side == 'top':
            file_name = self.output_dir + '/' + self.job_name + '_' + side + '.txt'
        elif side == 'bot':
            file_name = self.output_dir + '/' + self.job_name + '_bottom.txt'
        f = open(file_name, "w")
        f.writelines(heads)
        f.write('#####\n')
        f.writelines(marks)
        f.write('#####\n')
        f.writelines(r_cors)
        f.writelines(r_pnl_cors)
        f.close()
        return file_name

    def reread_2dbc_file(self, file_name, side):
        pnl_check_layer = 'f_dc-%s' % side
        GEN.DELETE_LAYER(pnl_check_layer)
        GEN.CREATE_LAYER(pnl_check_layer)
        heads = []
        marks = []
        all_cors = []
        pnl_cors = []
        head_end = 'no'
        mark_start = 'no'
        mark_end = 'no'
        with open(file_name, 'r') as f1:
            list1 = f1.readlines()

        for line in list1:
            cur_line = line.strip('\n')
            if head_end == 'no':
                heads.append(cur_line)

            if cur_line == '#####':
                if head_end == 'no':
                    mark_start = 'yes'
                    head_end = 'yes'
                elif head_end == 'yes' and mark_start == 'yes':
                    mark_end = 'yes'

            if mark_start == 'yes' and mark_end == 'no' and cur_line != '#####':
                # marks.append(cur_line)
                cur_cor = self.parse_cor(cur_line, type='mark_cor')
                marks.append(cur_cor)

            if head_end == 'yes' and mark_end == 'yes' and cur_line != '#####':
                # all_cors.append(cur_line)
                cur_cor = self.parse_cor(cur_line)
                all_cors.append(cur_cor)

        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(pnl_check_layer, 'yes')
        for al_cor in all_cors:
            GEN.ADD_TEXT(al_cor['x'], al_cor['y'], 'Fset%s-pcs%s' % (al_cor['set_index'], al_cor['unit_index']),
                         1.27, 2.54, angle=al_cor['angle'], mirr='no')
        for m_cor in marks:
            GEN.ADD_TEXT(m_cor['x'], m_cor['y'], 'Fp', 1.27, 2.54, angle='0')
        GEN.AFFECTED_LAYER(pnl_check_layer, 'no')
    def parse_cor(self, ip_line, type='bc_cor'):
        if type == 'bc_cor':
            m = re.match('X=(.*);Y=(.*);Ang=(.*);Type=(\d);Set=(.*);Unit=(.*);UseBarcodeSize=(\d);UseTextSize=(\d)', ip_line)
            if m:
                cordict = dict(x=m.group(1), y=m.group(2), angle=m.group(3), bc_type=m.group(4), set_index=m.group(5),
                               unit_index=m.group(6), use_bc_size=m.group(7), use_text_size=m.group(8))
        if type == 'mark_cor':
            m = re.match ('X=(.*);Y=(.*)', ip_line)
            if m:
                cordict = dict(x=m.group(1), y=m.group(2))
        return cordict
    def get_all_cor(self, side):
        ss = 1
        jj = 0
        # pp = 0
        # mm code pcs index ##
        # dd = 0
        al_cor = {}
        pnl_cor = {}
        pnl_ind = 0
        # === TODO 增加匹配的命名，实际没有使用，后续可能用到
        sym_reg = re.compile(r'2d(?P<bc_type>bc|text)_(?P<bc_size>\d\d?\.?\d?\d?|\d\d?.?\d?\d?x\d\d?.?\d?\d?)mm_?(?P<bc_ang>\d?\d?\.?\d?\d?)$')
        # === 获取光点坐标
        cur_pnl_dc = '2dbc-pnl-%s' % side
        mark_cor_dict = self.get_mark_cor(cur_pnl_dc)
        cur_pnl_dc = '2dbc-pnl-%s' % side

        # === 增加判断是否有子母码拼版 ===
        set_sr_exist = 'no'
        pcscu = 'pcs_s_ck'
        pcscu_in_pnl = ''
        if GEN.LAYER_EXISTS(pcscu, job=self.job_name,step=self.pnl_step) == 'yes':
            set_sr_exist = 'yes'
            pcscu_in_pnl = '__tmppnl_%s__' % pcscu
            GEN.DELETE_LAYER (pcscu_in_pnl)
            GEN.COM ('flatten_layer,source_layer=%s,target_layer=%s' % (pcscu, pcscu_in_pnl))
        setcu = 'dc_s_ck'
        setcu_in_pnl = '__tmppnl_%s__' % setcu
        GEN.DELETE_LAYER (setcu_in_pnl)
        GEN.COM ('flatten_layer,source_layer=%s,target_layer=%s' % (setcu, setcu_in_pnl))
        # === 获取setcu_inpnl 的index，并取属性 ===
        info = GEN.INFO (
            '-t layer -e %s/%s/%s -m script -d FEATURES -o feat_index' % (self.job_name, self.pnl_step, setcu_in_pnl))
        index_list = []
        cu_step_list = []
        cu_index_reg = re.compile (r'^#(\d+)\s+#S P 0;.pattern_fill,.string=(.*)\n')
        for line in info:
            match_obj = cu_index_reg.match(line)
            if match_obj:
                cu_index = match_obj.group(1)
                index_list.append(cu_index)
                cu_step_list.append(match_obj.group(2))
        # 20241016 zl 按拼版顺序依次获取
        number_layer = None
        search_layers = genesisPackages.outsignalLayers + genesisPackages.silkscreenLayers + genesisPackages.solderMaskLayers
        for search_layer in search_layers:
            GEN.AFFECTED_LAYER(search_layer, 'yes')
            GEN.FILTER_RESET()
            GEN.COM('set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=yes,attribute=.string,min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=panel')
            GEN.FILTER_SELECT()
            GEN.FILTER_RESET()
            if GEN.GET_SELECT_COUNT():
                number_layer = search_layer
                GEN.CLEAR_LAYER()
                break
            GEN.CLEAR_LAYER()
        set_map = {}
        for cu_i, cur_index in enumerate(index_list):
            GEN.AFFECTED_LAYER(setcu_in_pnl, 'yes')
            cu_step = cu_step_list[cu_i]
            GEN.VOF()
            GEN.COM('sel_layer_feat,operation=select,layer=%s,index=%s' % (setcu_in_pnl, cur_index))
            GEN.VON()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_COPY('dc_p_ck')
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER(number_layer, 'yes')
            GEN.FILTER_RESET()
            GEN.COM('filter_atr_reset')
            # === 不包含光点的设定 ===
            GEN.COM('filter_set, filter_name=popup, update_popup=no, exclude_syms=r0.2')
            GEN.SEL_REF_FEAT('dc_p_ck', 'touch')
            # sel_num = int(GEN.GET_SELECT_COUNT())
            # GEN.PAUSE('sel_num %s' % sel_num)
            # 获取touch到的set序号
            if GEN.GET_SELECT_COUNT():
                number_info = GEN.INFO('-t layer -e %s/%s/%s -d FEATURES -o select,units=mm' % (self.job_name, self.pnl_step, number_layer))
                del number_info[0]
                for line in number_info:
                    if line.startswith('#T'):
                        number = line.split()[10]
                        set_map[cur_index + '_' + cu_step] = int(number.replace("'", ''))
                        break
            GEN.CLEAR_LAYER()
            GEN.VOF()
            GEN.COM('truncate_layer,layer=dc_p_ck')
            GEN.VON()
        # print(set_map)
        # 按set_map value值排序
        number_map = [i[0] for i in sorted(set_map.items(), key=lambda k: k[1])]
        for k in number_map:
            GEN.AFFECTED_LAYER (setcu_in_pnl, 'yes')
            cur_index = k.split('_', 1)[0]
            cu_step = k.split('_', 1)[1]
            GEN.VOF()
            GEN.COM('sel_layer_feat,operation=select,layer=%s,index=%s' % (setcu_in_pnl, cur_index))
            GEN.VON()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_MOVE('dc_p_ck')
            GEN.WORK_LAYER(cur_pnl_dc)
            GEN.FILTER_RESET()
            GEN.COM('filter_atr_reset')
            # === 不包含光点的设定 ===
            GEN.COM('filter_set, filter_name=popup, update_popup=no, exclude_syms=r0.2')
            GEN.SEL_REF_FEAT('dc_p_ck', 'touch')
            sel_num = int(GEN.GET_SELECT_COUNT())
            # GEN.PAUSE('sel_num %s' % sel_num)
            if sel_num > 0:
                tmp_layer = '__tmpget_dccor__'
                GEN.DELETE_LAYER(tmp_layer)
                GEN.SEL_MOVE(tmp_layer)
                GEN.CLEAR_LAYER()
                GEN.AFFECTED_LAYER(tmp_layer, 'yes')
                if set_sr_exist == 'yes':
                    GEN.SEL_REF_FEAT(pcscu_in_pnl, 'touch')
                else:
                    GEN.SEL_REVERSE()
                if int(GEN.GET_SELECT_COUNT()) > 0:
                    get_pnl_co = GEN.INFO('-t layer -e %s/%s/%s -d FEATURES -o select,units=mm' % (self.job_name, self.pnl_step, tmp_layer))
                    dc_cor = get_pnl_co[1:]
                    # 以set跳码
                    pp = 0      # 二维码跳码序号
                    dd = 0      # 明码跳码序号
                    for i in dc_cor:
                        use_barcode_size = 1
                        use_text_size = 1
                        if side == 'top':
                            cur_x_cor = float(i.split(' ')[1])
                        elif side == 'bot':
                            cur_x_cor = -float(i.split(' ')[1])

                        cur_y_cor = float(i.split(' ')[2])
                        cur_sym_name = i.split (' ')[3]
                        ad_agl = 0
                        bc_type = ''
                        m = sym_reg.match(cur_sym_name)
                        if m:
                            # === 二维码类型 ===
                            if m.group(1) == 'bc':
                                bc_type = 1
                                # tdbc_sz.append(m.group(2))
                                if m.group(2) == self.op_2dbc_dict[side]['size_2dbc'][0]:
                                    use_barcode_size = 1
                                elif m.group(2) == self.op_2dbc_dict[side]['size_2dbc'][1]:
                                    use_barcode_size = 2
                                if cu_step != 'ewm-coupon':
                                    pp += 1
                            # === 明码 ===
                            elif m.group(1) == 'text':
                                bc_type = 0
                                # text_sz.append(m.group(2))
                                if m.group(2) == self.op_2dbc_dict[side]['size_mm'][0]:
                                    use_text_size = 1
                                elif m.group(2) == self.op_2dbc_dict[side]['size_mm'][1]:
                                    use_text_size = 2
                                if cu_step != 'ewm-coupon':
                                    dd += 1
                            else:
                                GEN.PAUSE ('Symbol Error')
                            if m.group(3):
                                ad_agl = m.group(3)
                        else:
                            M = M_Box ()
                            showText = M.msgText (u'提示', u"层别:%s中的symbol:%s不符合二维码及明码命名" % (tmp_layer, cur_sym_name), showcolor='red')
                            M.msgBox (showText)

                        if float(i.split(' ')[6])+float(ad_agl) > 360:
                            sym_agl = float(i.split(' ')[6])+float(ad_agl)-360
                        else:
                            sym_agl = float(i.split(' ')[6])+float(ad_agl)
                        if cu_step == 'ewm-coupon':
                            crs_ind = 0
                            crs_ss = 0
                            pnl_ind += 1
                        else:
                            crs_ss = ss
                            if bc_type == 1:
                                crs_ind = pp
                            elif bc_type == 0:
                                crs_ind = dd
                        al_cor[jj] = dict(x=cur_x_cor, y=cur_y_cor, angle=sym_agl, set_index=crs_ss, unit_index=crs_ind,
                                          bc_type=bc_type,use_bc_size=use_barcode_size,use_text_size=use_text_size)
                        jj += 1
                    # job.PAUSE(str(jj))
                    GEN.COM('sel_delete')
                get_pnl_co = GEN.INFO ('-t layer -e %s/%s/%s  -d FEATURES ,units=mm' % (self.job_name, self.pnl_step, tmp_layer))
                #  === 存在set上的母码 ===
                if len (get_pnl_co) > 0:
                    dc_cor = get_pnl_co[1:]
                    # 以set跳码
                    pp = 0      # 二维码跳码序号
                    dd = 0      # 明码跳码序号
                    for i in dc_cor:
                        use_barcode_size = 1
                        use_text_size = 1
                        cur_sym_name = i.split (' ')[3]
                        cur_ang = float(i.split (' ')[6])
                        if side == 'top':
                            cur_x_cor = float(i.split(' ')[1])
                        elif side == 'bot':
                            cur_x_cor = -float(i.split(' ')[1])

                        cur_y_cor = float(i.split(' ')[2])
                        ad_agl = 0
                        bc_type = ''
                        m = sym_reg.match(cur_sym_name)
                        if m:
                            # === 二维码类型 ===
                            if m.group(1) == 'bc':
                                bc_type = 1
                                # tdbc_sz.append(m.group(2))
                                if m.group(2) == self.op_2dbc_dict[side]['size_2dbc'][0]:
                                    use_barcode_size = 1
                                elif m.group(2) == self.op_2dbc_dict[side]['size_2dbc'][1]:
                                    use_barcode_size = 2
                                #
                                # if cu_step != 'ewm-coupon':
                                #     pp += 1
                            # === 明码 ===
                            elif m.group(1) == 'text':
                                bc_type = 0
                                # text_sz.append(m.group(2))

                                if m.group(2) == self.op_2dbc_dict[side]['size_mm'][0]:
                                    use_text_size = 1
                                elif m.group(2) == self.op_2dbc_dict[side]['size_mm'][1]:
                                    use_text_size = 2

                                # if cu_step != 'ewm-coupon':
                                #     dd += 1
                            else:
                                GEN.PAUSE ('Symbol Error')
                            if m.group(3):
                                ad_agl = float(m.group(3))
                        else:
                            M = M_Box ()
                            showText = M.msgText (u'提示', u"层别:%s中的symbol:%s不符合二维码及明码命名" % (tmp_layer,cur_sym_name), showcolor='red')
                            M.msgBox (showText)

                        if cur_ang + ad_agl > 360:
                            sym_agl = cur_ang + ad_agl - 360
                        else:
                            sym_agl = cur_ang + ad_agl
                        if cu_step == 'ewm-coupon':
                            crs_ind = 0
                            crs_ss = 0
                            pnl_ind += 1
                        else:
                            crs_ss = ss
                            if bc_type == 1:
                                crs_ind = pp
                            elif bc_type == 0:
                                crs_ind = dd

                        al_cor[jj] = dict(x=cur_x_cor, y=cur_y_cor, angle=sym_agl, set_index=crs_ss, unit_index=crs_ind,
                                          bc_type=bc_type,use_bc_size=use_barcode_size,use_text_size=use_text_size)
                        jj += 1
                    GEN.SEL_DELETE()
                    GEN.CLEAR_LAYER()
                # 以set跳码
                GEN.DELETE_LAYER(tmp_layer)
                ss += 1
            GEN.WORK_LAYER('dc_p_ck')
            GEN.SEL_DELETE()

        # === 未添加在板内，直接添加在板边的坐标获取
        get_pnl_co = GEN.INFO('-t layer -e %s/%s/2dbc-pnl-%s  -d FEATURES ,units=mm' % (self.job_name, self.pnl_step, side))
        if len(get_pnl_co) > 0:
            dc_cor = get_pnl_co[1:]
            for i in dc_cor:
                use_barcode_size = 1
                use_text_size = 1
                sym_ang = float (i.split (' ')[6])
                if side == 'top':
                    sym_x = float (i.split (' ')[1])
                elif side == 'bot':
                    sym_x = -float (i.split (' ')[1])

                sym_y = float (i.split (' ')[2])
                cur_sym_name = i.split (' ')[3]
                m = sym_reg.match (cur_sym_name)
                match_mark = re.match(r'0.2', cur_sym_name)
                if m:
                    if m.group(3):
                        ad_agl = float(m.group(3))
                    else:
                        ad_agl = 0
                    # === 二维码类型 ===
                    if m.group (1) == 'bc':
                        bc_type = 1
                        # tdbc_sz = m.group (2)
                        if m.group (2) == self.op_2dbc_dict[side]['size_2dbc'][0]:
                            use_barcode_size = 1
                        elif m.group (2) == self.op_2dbc_dict[side]['size_2dbc'][1]:
                            use_barcode_size = 2

                    # === 明码 ===
                    elif m.group (1) == 'text':
                        bc_type = 0
                        # text_sz.append (m.group (2))
                        if m.group (2) == self.op_2dbc_dict[side]['size_mm'][0]:
                            use_text_size = 1
                        elif m.group (2) == self.op_2dbc_dict[side]['size_mm'][1]:
                            use_text_size = 2
                    else:
                        GEN.PAUSE ('Symbol Error')

                    if sym_ang + ad_agl > 360:
                        sym_agl = sym_ang + ad_agl - 360
                    else:
                        sym_agl = sym_ang + ad_agl
                    pnl_cor[pnl_ind] = dict (x=sym_x, y=sym_y, angle=sym_agl, set_index=0, unit_index=pnl_ind + 1,
                                       bc_type=bc_type, use_bc_size=use_barcode_size, use_text_size=use_text_size)
                    pnl_ind += 1
                elif match_mark:
                    pass
        if pcscu_in_pnl:
            GEN.DELETE_LAYER(pcscu_in_pnl)
        GEN.DELETE_LAYER(setcu_in_pnl)
        return al_cor, pnl_cor, mark_cor_dict

    def all_step_fill_copper(self):
        # 在所有step中填铜
        # 获取panel的拼版列表 获取坐标#
        # 获取panel中的所有内容#
        # === 通过板内填铜确认序号
        GEN.DELETE_LAYER('f_dc-top')
        GEN.DELETE_LAYER('f_dc-bot')
        GEN.DELETE_LAYER('dc_s_ck')
        GEN.DELETE_LAYER('dc_p_ck')
        GEN.DELETE_LAYER ('pcs_s_ck')

        GEN.CREATE_LAYER('dc_s_ck')
        GEN.CREATE_LAYER('dc_p_ck')
        pnl_sr = GEN.DO_INFO('-t step -e %s/%s -d REPEAT' % (self.job_name, self.pnl_step))
        step_list = list(set(pnl_sr['gREPEATstep']))
        array_sr = {}
        step_datum = {}
        add_cu_steps = []
        # 获取panel单元的拼版数量，并在每个单元内铺铜，为后续序号做准备#
        GEN.CREATE_LAYER('pcs_s_ck')
        for stepu in step_list:
            if stepu in add_cu_steps:
                continue
            stepinfo = GEN.DO_INFO('-t step -e %s/%s -d REPEAT -p step' % (self.job_name, stepu))
            # === 检查是否有二级拼版，如果有，在二级拼版内填铜
            if len(stepinfo['gREPEATstep']) != 0:
                array_sr[stepu] = {'num': len(stepinfo['gREPEATstep']), 'unlist': list(set(stepinfo['gREPEATstep']))}

                for pcs in list(set(stepinfo['gREPEATstep'])):
                    if pcs in add_cu_steps:
                        continue
                    GEN.OPEN_STEP(pcs)
                    GEN.CLEAR_LAYER()
                    GEN.CHANGE_UNITS('mm')
                    # GEN.WORK_LAYER('pcs_s_ck')
                    GEN.AFFECTED_LAYER('pcs_s_ck', 'yes')
                    GEN.FILL_SUR_PARAMS()
                    GEN.SR_FILL('positive', -0.2, -0.2, 2540, 2540)
                    GEN.COM ('cur_atr_reset')
                    GEN.COM ('cur_atr_set,attribute=.string,text=%s' % pcs)
                    GEN.COM ('sel_change_atr,mode=add')
                    add_cu_steps.append(pcs)
                    GEN.AFFECTED_LAYER('pcs_s_ck', 'no')
                    GEN.COM('editor_page_close')
                GEN.OPEN_STEP(stepu)
                GEN.CLEAR_LAYER()
                GEN.CHANGE_UNITS('mm')
                GEN.COM('flatten_layer,source_layer=pcs_s_ck,target_layer=dc_s_ck')
                # GEN.WORK_LAYER('dc_s_ck')
                GEN.AFFECTED_LAYER ('dc_s_ck', 'yes')
                GEN.FILL_SUR_PARAMS()
                GEN.SR_FILL('positive', -0.2, -0.2, 2540, 2540)
                GEN.COM('sel_contourize,accuracy=6.35,break_to_islands=yes,clean_hole_size=127,clean_hole_mode=x_or_y')
                GEN.COM('sel_all_feat')
                sel_num = GEN.GET_SELECT_COUNT()
                if sel_num != 1:
                    GEN.PAUSE('ERROR')
                    exit()
                GEN.COM('cur_atr_reset')
                GEN.COM('cur_atr_set,attribute=.string,text=%s' % stepu)
                GEN.COM('sel_change_atr,mode=add')
                # GEN.CLEAR_LAYER()
                add_cu_steps.append (stepu)
                GEN.AFFECTED_LAYER('dc_s_ck', 'no')
                GEN.COM('editor_page_close')
                step_datum[stepu] = GEN.DO_INFO('-t step -e %s/%s -d DATUM,  units=mm' % (self.job_name, stepu))
            else:
                GEN.OPEN_STEP(stepu)
                GEN.CLEAR_LAYER()
                GEN.CHANGE_UNITS('mm')
                # GEN.WORK_LAYER('dc_s_ck')
                GEN.AFFECTED_LAYER('dc_s_ck', 'yes')
                GEN.FILL_SUR_PARAMS()
                GEN.SR_FILL('positive', -0.2, -0.2, 2540, 2540)
                GEN.COM('cur_atr_reset')
                GEN.COM('cur_atr_set,attribute=.string,text=%s' % stepu)
                GEN.COM('sel_change_atr,mode=add')
                add_cu_steps.append (stepu)
                GEN.AFFECTED_LAYER('dc_s_ck', 'no')
                step_datum[stepu] = GEN.DO_INFO('-t step -e %s/%s -d DATUM,  units=mm' % (self.job_name, stepu))
                # GEN.CLEAR_LAYER()
                GEN.COM('editor_page_close')

        return step_datum
    def geterpthickness(self, dbc, ipjobname):

        sql = """SELECT
                TC_AAC01 AS job,
                TC_AAC56 AS thickness
            FROM
                TC_AAC_FILE
            WHERE
                TC_AAC01 = '%s'""" % ipjobname.upper()[:13]  # --截取前十三位料号名
        dataVal = self.DB_O.SELECT_DIC(dbc, sql)
        return dataVal


class M_Box(QtGui.QMessageBox):
    """
    MesageBox提示界面
    """

    def __init__(self, parent=None):
        QtGui.QMessageBox.__init__(self, parent)

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

    def msgText(self, body1, body2, body3=None, showcolor='#E53333'):
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
                    <span style="background-color:%s;color:'#FFFFFF';font-size:18px;"><strong>%s：</strong></span>
                </p>
                <p>
                    <span style="font-size:18px;">&nbsp;&nbsp;</span>
                    <span style="color:#E53333;font-size:18px;">&nbsp;&nbsp;</span>
                    <span style="color:#E53333;font-size:18px;">&nbsp; &nbsp; </span>
                    <span style="color:#E53333;font-size:16px;">%s</span>
                </p>""" % (showcolor, body1, body2)

        # --返回HTML样式文本
        return textInfo


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    laserCarvingOutput = LaserCarvingOutput()
    laserCarvingOutput.show()
    sys.exit(app.exec_())
