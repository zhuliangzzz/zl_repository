#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :
# @Date         :    2020/07/01
# @Revision     :    1.0
# @File         :    make_lp.py
# @Software     :    PyCharm
# @Usefor       :    HDI挡点制作
# @Revision     :    1.0增加挡点制作
#
# ---------------------------------------------------------#

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
import makelpUI as Mui
import json
import csv
from PyQt4 import QtCore, QtGui
import platform
import random

import string

if platform.system() == "Windows":
    # sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"D:/genesis/sys/scripts/Package")

else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genCOM_26
# from package import msgBox
import Oracle_DB

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


class MyApp(object):
    def __init__(self):
        self.job_name = os.environ.get('JOB')
        self.step_name = os.environ.get('STEP')
        self.boardthick = 0
        self.tmplp = '__tmplp__'
        self.smlist = GEN.GET_ATTR_LAYER('solder_mask')
        self.dotdict = {}
        self.signallist = GEN.GET_ATTR_LAYER('signal')
        self.layer_num = len(self.signallist)
        #
        # self.dotdict =  {
        #     "m1": {
        #         "SIDE": "top",
        #         "drltmp": "drl-m1",
        #         "filloilnum": 1556,
        #         "halftouchnum": 29,
        #         "smtmp": "m1-lp"
        #     }
        # }

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


class MainWindowShow(QtGui.QDialog, MyApp):
    """
    窗体主方法
    """

    def __init__(self):
        super(MainWindowShow, self).__init__()
        # 初始数据
        MyApp.__init__(self)
        if not self.job_name or not self.step_name:
            MB = M_Box()
            showText = MB.msgText(u'提示', u"必须打开料号及需添加的Step,程序退出!", showcolor='red')
            MB.msgBox(showText)
            exit(0)
        self.appVer = "V2.4"
        self.scrDir = os.path.split(os.path.abspath(sys.argv[0]))[0]
        self.drl = 'drl'
        # === 2020.09.28 当有验孔层存在时，tk.ykj层别，使用此层别作为钻孔的参考层，为了使用槽孔旋转之前的数据 ===
        self.change_drl_layer()
        # === 2022.03.15 增加提示信息收集器，用于提醒信息收集 ===
        self.info_mess = []
        self.DB_O = Oracle_DB.ORACLE_INIT()
        # M = Oracle_DB.ORACLE_INIT()
        dbc_o = self.DB_O.DB_CONNECT("172.20.218.193", "inmind.fls", '1521', 'GETDATA', 'InplanAdmin')
        if dbc_o is None:
            MB = M_Box()
            showText = MB.msgText(u'警告', u'HDI InPlan 无法连接, 程序退出！', showcolor='red')
            MB.msgBox(showText)
            exit(0)
        self.strJobName = self.job_name.upper()[:13]  # --截取前十三位料号名
        self.layerInfo = self.DB_O.getLayerThkInfo(dbc_o, self.strJobName)
        self.get_mic = self.getjobmic(dbc_o)
        if dbc_o:
            self.DB_O.DB_CLOSE(dbc_o)
        self.top_layer = 'l1'
        self.bot_layer = 'l%s' % int(self.layer_num)
        self.outer_layers = [self.top_layer, self.bot_layer]
        top_cal_cu_thk = [i['CAL_CU_THK'] for i in self.layerInfo if i['LAYER_NAME'].lower() == self.top_layer][0]
        bot_cal_cu_thk = [i['CAL_CU_THK'] for i in self.layerInfo if i['LAYER_NAME'].lower() == self.bot_layer][0]
        self.outer_cu_same = False
        if top_cal_cu_thk == bot_cal_cu_thk:
            self.outer_cu_same = True
        self.npth_special_deal = False
        # === 515系列，且两面铜厚不一致时NPTH孔的挡点特殊处理 ===
        if self.job_name[1:4] == '515' and not self.outer_cu_same:
            self.npth_special_deal = True
        self.ui = Mui.Ui_Dialog()
        self.ui.setupUi(self)
        self.addUiDetail()

    def addUiDetail(self):
        """
        在原框架基础上继续加载窗体
        :return:None
        """
        # 增加板厚输入限制，个位数加小数点后三位
        self.ui.label.setText(_translate("Dialog", "HDI一厂挡点制作\n"
                                                   " 版本：%s" % self.appVer, None))
        self.setWindowTitle(_translate("Dialog", "挡点制作", None))
        self.ui.checkBox_dot2cu.setText(u"削npth挡点保证到铜10mil")
        my_regex = QtCore.QRegExp("^[0-3]\.[0-9][0-9]?[0-9]?$")
        my_validator = QtGui.QRegExpValidator(my_regex, self.ui.lineEdit)
        self.ui.lineEdit.setValidator(my_validator)
        # HDI一厂不需要输入板厚
        self.ui.lineEdit.hide()
        self.ui.label_2.hide()
        self.ui.checkBox.setChecked(True)
        #翟鸣通知取消缩档点 20250606 by lyh
        self.ui.checkBox_dot2cu.setChecked(False)
        self.ui.checkBox.hide()
        self.ui.checkBox_dot2cu.hide()
        # === 判断是否有mic孔设计
        self.ui.tableWidget.hide()
        # self.ui.label_3.hide()

        if self.get_mic:
            if self.get_mic['ES_MIC_HOLE_'] == 1:
                self.ui.label_3.setText(_translate("Dialog", "注意:存在mic孔设计,完成后手动处理mic挡点", None))
            elif self.get_mic['ES_MIC_HOLE_'] == 0:
                self.ui.label_3.setText(_translate("Dialog", "提示:不存在mic孔设计", None))
            else:
                self.ui.label_3.setText(_translate("Dialog", "注意:未准确获取mic孔信息", None))
        else:
            self.ui.label_3.setText(_translate("Dialog", "注意:未从InPlan获取mic孔信息", None))
        # HDI一厂不需要Table

        if not self.outer_cu_same:
            text1 = self.ui.label_3.text()
            self.ui.label_3.setText((_translate("Dialog", "%s\n%s" % (text1, '两面铜厚不一致') , None)))
        else:
            text1 = self.ui.label_3.text()
            self.ui.label_3.setText((_translate("Dialog", "%s\n%s" % (text1, '两面铜厚一致') , None)))
        # self.ui.checkBox_dot2cu.hide()
        QtCore.QObject.connect(self.ui.pushButton_apply, QtCore.SIGNAL("clicked()"), self.main_run)
        # QtCore.QObject.connect(self.ui.pushButton_apply, QtCore.SIGNAL("clicked()"), self.check_dot_dist)

    def closeEvent(self, event):
        GEN.FILTER_RESET()
        GEN.CLEAR_LAYER()
        # if self.lpdict:
        #     # print json.dumps (self.lpdict, sort_keys=True, indent=2, separators=(',', ': '))
        #     for i in self.lpdict:
        #         if self.lpdict[i]:
        #             GEN.DELETE_LAYER(self.lpdict[i]['drltmp'])
        #             GEN.DELETE_LAYER(self.lpdict[i]['smtmp'])
        event.accept()

    def change_drl_layer(self):
        # === tk.ykj 是否存在 ===

        if GEN.LAYER_EXISTS('tk.ykj', job=self.job_name, step=self.step_name) == 'yes':
            self.drl = 'tk.ykj'
            # === 增加防呆判断是否与drl层别钻孔数量是否相同 ===
            gdrl = GEN.DO_INFO('-t layer -e %s/%s/%s -d FEAT_HIST' % (self.job_name, self.step_name, 'drl'))
            gyk = GEN.DO_INFO('-t layer -e %s/%s/%s -d FEAT_HIST' % (self.job_name, self.step_name, 'tk.ykj'))
            if int(gdrl["gFEAT_HISTtotal"]) != int(gyk["gFEAT_HISTtotal"]):
                M = M_Box()
                showText = M.msgText(u'提示', u"tk.ykj层别存在数:%s，且与drl层别物件数量%s不相同,程序退出!" %
                                     (int(gdrl["gFEAT_HISTtotal"]), int(gyk["gFEAT_HISTtotal"])), showcolor='red')
                M.msgBox(showText)
                exit(0)

    def getjobmic(self,dbc_o):
        # 连接HDI InPlan

        sql = """
                select a.job_name, a.ES_MIC_HOLE_
                from vgt_hdi.rpt_job_list a
                where a.job_name = '%s'""" % self.strJobName
        # 1 为存在，0为不存在
        dataval = self.DB_O.SELECT_DIC(dbc_o, sql)

        print json.dumps(dataval[0], indent=2)
        return dataval[0]

    def makeCopylayer(self, source_layer, suffix):
        dislayer = '%s-%s' % (source_layer, suffix)
        GEN.DELETE_LAYER(dislayer)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(source_layer, 'yes')
        GEN.SEL_COPY(dislayer)
        GEN.CLEAR_LAYER()
        return dislayer

    def mvhole(self, sourcelayer, orgSymSize, desSymSize, destlayer):
        """
        通过中间辅助层，进行大小变更，移动到目标层
        :param sourcelayer:
        :param orgSymSize:
        :param desSymSize:
        :param destlayer:
        :return:
        """

        mytmplayer = '__tmpchangehole__'
        GEN.DELETE_LAYER(mytmplayer)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(sourcelayer, 'yes')
        GEN.FILTER_RESET()
        GEN.FILTER_SET_INCLUDE_SYMS('r%s' % orgSymSize)
        GEN.FILTER_SELECT()
        if int(GEN.GET_SELECT_COUNT()) == 0:
            M = M_Box()
            showText = M.msgText(u'提示', u"有没有搞错，怎么会选不到呢!", showcolor='red')
            M.msgBox(showText)
            return False
        GEN.SEL_MOVE(mytmplayer)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(mytmplayer, 'yes')
        GEN.SEL_CHANEG_SYM('r%s' % desSymSize)
        GEN.SEL_COPY(destlayer)
        GEN.DELETE_LAYER(mytmplayer)
        GEN.CLEAR_LAYER()
        return

    def mvhole_withattr(self, sourcelayer, orgSymSize, desSymSize, destlayer, invertyorn='no', attr='tg_point'):
        """
        通过中间辅助层，进行大小变更，添加属性，并移动到目标层
        :param sourcelayer:
        :param orgSymSize:
        :param desSymSize:
        :param destlayer:
        :param invertyorn:
        :param attr:
        :return:
        """
        mytmplayer = '__tmpchangehole__'
        GEN.DELETE_LAYER(mytmplayer)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(sourcelayer, 'yes')
        GEN.FILTER_RESET()
        GEN.FILTER_SET_INCLUDE_SYMS('r%s' % orgSymSize)
        GEN.FILTER_SELECT()
        if int(GEN.GET_SELECT_COUNT()) == 0:
            M = M_Box()
            showText = M.msgText(u'提示', u"有没有搞错，怎么会选不到呢!", showcolor='red')
            M.msgBox(showText)
            return False
        GEN.SEL_MOVE(mytmplayer)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(mytmplayer, 'yes')
        GEN.SEL_CHANEG_SYM('r%s' % desSymSize)
        GEN.COM('cur_atr_set, attribute=.bit, text=%s' % attr)
        GEN.COM('sel_change_atr, mode=add')

        GEN.SEL_COPY(destlayer, invert=invertyorn)
        GEN.DELETE_LAYER(mytmplayer)
        GEN.CLEAR_LAYER()
        return

    def makeCopylayer(self, source_layer, suffix):
        dislayer = '%s-%s' % (source_layer, suffix)

        GEN.DELETE_LAYER(dislayer)

        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(source_layer, 'yes')
        GEN.SEL_COPY(dislayer)
        GEN.CLEAR_LAYER()
        return dislayer

    def createdotdict(self):
        """
        用于生成临时防焊层别
        :return:
        """
        # 制作防焊临时层，用于后续使用
        for sm in self.smlist:
            self.dotdict[sm] = {}
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER(sm, 'yes')
            self.dotdict[sm]['smtmp'] = self.makeCopylayer(sm, 'dot')
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER(self.dotdict[sm]['smtmp'], 'yes')
            # 先删除透光点
            GEN.FILTER_RESET()
            GEN.FILTER_SET_FEAT_TYPES('pad')
            GEN.FILTER_SET_POL('negative')
            GEN.COM('filter_atr_reset')
            GEN.COM('filter_atr_set, filter_name=popup, condition=yes, attribute=.bit, option=tg_point')
            GEN.FILTER_SELECT()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_DELETE()

            # 整体化临时防焊层，用于去除负片
            GEN.COM('sel_contourize, accuracy=0.1, break_to_islands=yes, clean_hole_size=3, clean_hole_mode=x_or_y')
            GEN.AFFECTED_LAYER(self.dotdict[sm]['smtmp'], 'no')

    def checkdotsolderopen(self, tmplayer):
        """
        用于检查，是否有做挡点的钻孔未开窗的情形
        :return:
        """
        tmpchklayer = '__checkdotopen__'
        dotnoopen = '__%serrordotopen__' % self.step_name
        GEN.DELETE_LAYER(dotnoopen)

        gFEAT_HIST = GEN.DO_INFO('-t layer -e %s/%s/%s -d FEAT_HIST' % (self.job_name, self.step_name, tmplayer))
        dotcount = int(gFEAT_HIST["gFEAT_HISTtotal"])
        GEN.DELETE_LAYER(tmpchklayer)
        GEN.CLEAR_LAYER()
        for sm in self.dotdict:
            GEN.AFFECTED_LAYER(self.dotdict[sm]['smtmp'], 'yes')
            GEN.SEL_COPY(tmpchklayer)
            GEN.AFFECTED_LAYER(self.dotdict[sm]['smtmp'], 'no')

        GEN.AFFECTED_LAYER(tmplayer, 'yes')
        GEN.FILTER_RESET()
        GEN.SEL_REF_FEAT(tmpchklayer, 'cover')
        GEN.SEL_REF_FEAT(tmpchklayer, 'include')
        if int(GEN.GET_SELECT_COUNT()) != dotcount:
            M = M_Box()
            showText = M.msgText(u'提示', u"有做挡点的钻孔未开窗的情形,check %s !" % (dotnoopen), showcolor='red')
            M.msgBox(showText)
            GEN.SEL_REVERSE()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_COPY(dotnoopen)
        else:
            GEN.DELETE_LAYER(tmpchklayer)
        GEN.CLEAR_LAYER()

    def mvhole_currentLayer(self, currentLayer, reSize, destlayer, invertyorn='no', attr='dot_shrink'):
        # 通过中间辅助层，进行大小变更，移动到目标层
        mytmplayer = '__tmpchangehole__'
        GEN.DELETE_LAYER(mytmplayer)
        GEN.SEL_MOVE(mytmplayer)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(mytmplayer, 'yes')
        GEN.SEL_RESIZE(reSize)
        GEN.COM('cur_atr_reset')
        GEN.COM('cur_atr_set, attribute =.bit, text=%s' % attr)
        GEN.COM('sel_change_atr, mode=add')
        GEN.SEL_COPY(destlayer, invert=invertyorn)
        GEN.DELETE_LAYER(mytmplayer)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(currentLayer, 'yes')
        return

    def make_dot(self):
        """
        制作挡点
        :return:
        """
        GEN.CLEAR_LAYER()
        cdot = '__tmpcdot__'
        sdot = '__tmpsdot__'
        tmpdrl = '__tmpdrl__'
        cd_tmp_drl = '__tmp_drl__'
        nptdrl = '__npthdrl__'
        pthdrl = '__pthdrl__'
        slotdrl = '__slotdrl__'
        ctkdrl = '__ctkdrl__'
        dotdrl = '__dotdrl__'
        cOverSize = '__cdotbig__'
        sOverSize = '__sdotbig__'
        # 钻孔层里不做lp的钻孔
        GEN.DELETE_LAYER(tmpdrl)
        GEN.DELETE_LAYER(dotdrl)
        GEN.DELETE_LAYER(nptdrl)
        GEN.DELETE_LAYER(slotdrl)
        GEN.DELETE_LAYER(pthdrl)
        GEN.DELETE_LAYER(ctkdrl)

        GEN.DELETE_LAYER(cdot)
        GEN.DELETE_LAYER(sdot)
        GEN.DELETE_LAYER(cOverSize)
        GEN.DELETE_LAYER(sOverSize)
        # === 2021.04.13 === 控深钻孔的已经处理层
        tmp_cdc_drl = '__tmpcdc__'
        tmp_cds_drl = '__tmpcds__'

        # === 2020.06.17 === 跑挡点前清空挡点层
        # === 2020.06.18 === 判断挡点层是否存在，不存在创建，存在则清空
        if GEN.LAYER_EXISTS('md1', job=self.job_name, step=self.step_name) == 'yes':
            GEN.AFFECTED_LAYER('md1', 'yes')
            GEN.SEL_DELETE()
        elif GEN.LAYER_EXISTS('c1', job=self.job_name, step=self.step_name) == 'yes':
            GEN.CREATE_LAYER('md1', ins_lay='c1', context='board', add_type='solder_paste', pol='positive',
                             location='before')
        elif GEN.LAYER_EXISTS('m1', job=self.job_name, step=self.step_name) == 'yes':
            GEN.CREATE_LAYER('md1', ins_lay='m1', context='board', add_type='solder_paste', pol='positive',
                             location='before')

        if GEN.LAYER_EXISTS('md2', job=self.job_name, step=self.step_name) == 'yes':
            GEN.AFFECTED_LAYER('md2', 'yes')
            GEN.SEL_DELETE()
        elif GEN.LAYER_EXISTS('c2', job=self.job_name, step=self.step_name) == 'yes':
            GEN.CREATE_LAYER('md2', ins_lay='c2', context='board', add_type='solder_paste', pol='positive',
                             location='after')
        elif GEN.LAYER_EXISTS('m2', job=self.job_name, step=self.step_name) == 'yes':
            GEN.CREATE_LAYER('md2', ins_lay='m2', context='board', add_type='solder_paste', pol='positive',
                             location='after')
        GEN.CHANGE_UNITS('mm')
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(self.drl, 'yes')
        # === 二钻孔需增加挡点 ===
        # 有槽孔在2nd内的情况 优先以2nd.ykj层为准 20231006 by lyh
        if GEN.LAYER_EXISTS('2nd', job=self.job_name, step=self.step_name) == 'yes':
            if GEN.LAYER_EXISTS('2nd.ykj', job=self.job_name, step=self.step_name) == 'yes':
                GEN.AFFECTED_LAYER('2nd.ykj', 'yes')
            else:
                GEN.AFFECTED_LAYER('2nd', 'yes')
        if GEN.LAYER_EXISTS(cd_tmp_drl, job=self.job_name, step=self.step_name) == 'yes':
            GEN.AFFECTED_LAYER(cd_tmp_drl, 'yes')

        GEN.SEL_COPY(tmpdrl)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(tmpdrl, 'yes')
        # === 删除.rout_chain属性
        GEN.COM('sel_delete_atr, attributes=.rout_chain')
        lp_exists_yn = GEN.LAYER_EXISTS('lp', job=self.job_name, step=self.step_name)
        # 判断铝片层是否存在，如果不存在则不不需要进行lp层的判断
        if lp_exists_yn == 'yes':
            GEN.FILTER_RESET()
            GEN.SEL_REF_FEAT('lp', 'touch')
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_DELETE()
        # === 2022.03.01 V2.1 判断树脂铝片层是否存在，如果不存在则不不需要进行lp层的判断
        sz_lp_exists_yn = GEN.LAYER_EXISTS('sz.lp', job=self.job_name, step=self.step_name)
        if sz_lp_exists_yn == 'yes':
            GEN.FILTER_RESET()
            GEN.SEL_REF_FEAT('sz.lp', 'touch')
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_DELETE()
        # === V2.1 均不存在时，才提醒 ===
        if lp_exists_yn == 'no' and sz_lp_exists_yn == 'no':
            M = M_Box()
            showText = M.msgText(u'提示', u"lp、sz.lp均不存在，程序继续!", showcolor='red')
            M.msgBox(showText)
        # 槽孔引导孔不加挡点，选择当前层别被当前层别的line，cover的pad，
        GEN.COM('filter_atr_reset')
        GEN.FILTER_SET_FEAT_TYPES('pad', reset=1)
        GEN.SEL_REF_FEAT(tmpdrl, 'cover', pol='positive;negative', f_type='line')
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.SEL_DELETE()

        gSymtmpdrl = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, tmpdrl))
        if len(gSymtmpdrl["gSYMS_HISTsymbol"]) == 0:
            # === 挡点层为空，制作假层 ===

            if GEN.LAYER_EXISTS(tmp_cdc_drl) == 'yes' or GEN.LAYER_EXISTS(tmp_cds_drl) == 'yes':
                GEN.AFFECTED_LAYER(tmpdrl, 'yes')
                GEN.SEL_COPY(dotdrl)
                # ===  增加cdc、cds层别的挡点 2021.04.13 ===
                if GEN.LAYER_EXISTS(tmp_cdc_drl) == 'yes':
                    GEN.CLEAR_LAYER()
                    # 获取层别物件
                    gSym = GEN.DO_INFO(
                        '-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, tmp_cdc_drl))
                    symlist = [self.stringtonum(i.strip('r')) for i in gSym["gSYMS_HISTsymbol"]]
                    for i in symlist:
                        if i < 1010:
                            destsize = i + 152.4
                            self.mvhole_withattr(tmp_cdc_drl, i, destsize, cdot, attr='npth_dot')
                        elif i >= 1010:
                            destsize = i - 203.2
                            if self.npth_special_deal and i <= 1510:
                                destsize = i
                            self.mvhole_withattr(tmp_cdc_drl, i, destsize, cdot, attr='npth_dot')
                    siglayer = 'l1'
                    tmpchecklayer = ''
                    if self.ui.checkBox_dot2cu.isChecked():
                        tmpchecklayer = self.makenpthDot10toCopper(dotdrl, 'top', cdot, siglayer, tmpchecklayer)

                if GEN.LAYER_EXISTS(tmp_cds_drl) == 'yes':
                    GEN.CLEAR_LAYER()
                    # 获取层别物件
                    gSym = GEN.DO_INFO(
                        '-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, tmp_cds_drl))
                    symlist = [self.stringtonum(i.strip('r')) for i in gSym["gSYMS_HISTsymbol"]]
                    for i in symlist:
                        if i < 1010:
                            destsize = i + 152.4
                            self.mvhole_withattr(tmp_cds_drl, i, destsize, sdot, attr='npth_dot')
                        elif i >= 1010:
                            destsize = i - 203.2
                            if self.npth_special_deal and i <= 1510:
                                destsize = i
                            self.mvhole_withattr(tmp_cds_drl, i, destsize, sdot, attr='npth_dot')
                    siglayer = 'l' + str(int(self.job_name[4:6]))
                    tmpchecklayer = ''
                    if self.ui.checkBox_dot2cu.isChecked():
                        tmpchecklayer = self.makenpthDot10toCopper(dotdrl, 'bottom', sdot, siglayer, tmpchecklayer)

                if GEN.LAYER_EXISTS(cdot) == 'yes':
                    GEN.AFFECTED_LAYER(cdot, 'yes')
                    GEN.SEL_COPY('md1')
                    GEN.CLEAR_LAYER()
                    GEN.DELETE_LAYER(cdot)
                if GEN.LAYER_EXISTS(sdot) == 'yes':
                    GEN.AFFECTED_LAYER(sdot, 'yes')
                    GEN.SEL_COPY('md2')
                    GEN.CLEAR_LAYER()
                    GEN.DELETE_LAYER(sdot)
                GEN.DELETE_LAYER(dotdrl)
                return True
            else:
                # 无需做挡点检测
                M = M_Box()
                showText = M.msgText(u'提示', u"没有需做挡点的钻孔，程序退出!", showcolor='red')
                M.msgBox(showText)
                return True
        GEN.AFFECTED_LAYER(tmpdrl, 'no')
        # 生成防焊辅助层
        self.createdotdict()
        # 增加检测，需做挡点的钻孔存在双面均未开窗的情况，注意考虑透光点的影响
        self.checkdotsolderopen(tmpdrl)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(tmpdrl, 'yes')
        # === 选出独立槽孔，单独处理 ===
        GEN.FILTER_RESET()
        GEN.FILTER_SET_FEAT_TYPES('line', reset=1)
        GEN.COM('filter_atr_reset')
        GEN.FILTER_SELECT()
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.SEL_MOVE(slotdrl)
            # 满足孤立条件的槽孔保留在slotdrl层，不满足的回退给tmpdrl层
            self.sel_isolate_slot(slotdrl, tmpdrl)
            # === 处理slotdrl层，处理好的移至dotdrl层别
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER(slotdrl, 'yes')
            # === 0长度的line移回去
            GEN.FILTER_RESET()
            GEN.FILTER_SET_FEAT_TYPES('line', reset=1)
            GEN.COM('filter_set,filter_name=popup,update_popup=yes,slot=line,slot_by=length,min_len=0,max_len=0')
            GEN.FILTER_SELECT()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_MOVE(tmpdrl)
            # === 2020.09.25 NPTH槽不进行槽孔挡点的拉长处理
            GEN.FILTER_RESET()
            GEN.COM('filter_atr_reset')
            GEN.COM('filter_atr_set, filter_name=popup, condition=yes, attribute=.drill, option=non_plated')
            GEN.FILTER_SELECT()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_MOVE(tmpdrl)
            GEN.SEL_REVERSE()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                # === 两端延长D+4，考虑后续要D-4,延长D+8mil
                GEN.COM('sel_extend_slots, mode=ext_by, size=203.2,from=center')
                # === 独立槽孔中线部分挡点大小D-4mil
                GEN.SEL_COPY(dotdrl, size='-101.6')
                # === 独立槽孔两端做到D+4mil
                # self.get_line_two_side(slotdrl)
                # GEN.CLEAR_LAYER ()
                # GEN.AFFECTED_LAYER (slotdrl, 'yes')
                # GEN.SEL_COPY(dotdrl,size='101.6')
            GEN.DELETE_LAYER(slotdrl)
            GEN.FILTER_RESET()
            GEN.COM('filter_atr_reset')
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(tmpdrl, 'yes')
        # 选择npth 移出
        GEN.FILTER_RESET()
        GEN.COM('filter_atr_reset')
        GEN.COM('filter_atr_set, filter_name=popup, condition=yes, attribute=.drill, option=non_plated')
        GEN.FILTER_SELECT()
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.SEL_MOVE(nptdrl)
        # 选择pth及via孔移至pth层
        GEN.FILTER_RESET()
        GEN.COM('filter_atr_reset')
        GEN.COM('filter_atr_set, filter_name=popup, condition=yes, attribute=.drill, option=plated')
        GEN.COM('filter_atr_set, filter_name=popup, condition=yes, attribute=.drill, option=via')
        GEN.COM('filter_atr_logic, filter_name=popup, logic=or')
        GEN.FILTER_SELECT()
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.SEL_MOVE(pthdrl)
        # 判断钻孔层是否还有内容，如有则保留层别
        gSymtmpdrl = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, tmpdrl))
        if len(gSymtmpdrl["gSYMS_HISTsymbol"]) != 0:
            M = M_Box()
            showText = M.msgText(u'提示', u"Info006:钻孔层%s有未定义属性的钻孔，请检查层%s!" % (self.drl, tmpdrl), showcolor='green')
            M.msgBox(showText)
        else:
            GEN.DELETE_LAYER(tmpdrl)

        if GEN.LAYER_EXISTS(nptdrl) == 'yes':
            GEN.CLEAR_LAYER()
            # 获取层别物件
            gSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, nptdrl))
            symlist = [self.stringtonum(i.strip('r')) for i in gSym["gSYMS_HISTsymbol"]]
            for i in symlist:
                if i < 1010:
                    # self.mvhole(nptdrl, i, i, dotdrl)
                    destsize = i + 152.4
                    self.mvhole_withattr(nptdrl, i, destsize, dotdrl, attr='npth_dot')
                elif i >= 1010:
                    # === -101.6 --> -203.2  2020.09.17 # V2.4 1.5以下的npth孔做等大
                    destsize = i - 203.2
                    if self.npth_special_deal and i <= 1510:
                        destsize = i
                    # self.mvhole(nptdrl, i, destsize, dotdrl)
                    self.mvhole_withattr(nptdrl, i, destsize, dotdrl, attr='npth_dot')

            GEN.DELETE_LAYER(nptdrl)

        if GEN.LAYER_EXISTS(pthdrl) == 'yes':
            # 获取层别物件
            # === 2022.03.07 区分单双面开窗 http://192.168.2.120:82/zentao/story-view-4037.html ===
            gSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, pthdrl))
            symlist = [self.stringtonum(i.strip('r')) for i in gSym["gSYMS_HISTsymbol"]]
            for i in symlist:
                if i <= 410:
                    # === 360 --> 410 2020.09.17
                    destsize = i + 254
                    self.mvhole(pthdrl, i, destsize, dotdrl)
                elif 410 < i < 510:
                    # === 390 --> 410 2020.09.17
                    destsize = i + 76.2,
                    self.mvhole(pthdrl, i, destsize, dotdrl)

            GEN.CLEAR_LAYER()
            #  === 可能存在料号中无NPTH也无小于0.510的pth，无dotdrl层别存在的情况
            if GEN.LAYER_EXISTS(dotdrl) == 'yes':
                GEN.AFFECTED_LAYER(dotdrl, 'yes')
                GEN.SEL_COPY(cdot)
                GEN.SEL_COPY(sdot)
                GEN.DELETE_LAYER(dotdrl)

            c_side_drl = "__c_side_drl__"
            s_side_drl = "__s_side_drl__"
            GEN.DELETE_LAYER(c_side_drl)
            GEN.DELETE_LAYER(s_side_drl)

            for sm_layer in self.dotdict:
                # === 获取防焊层方向 ===
                get_side = GEN.DO_INFO("-t layer -e %s/%s/%s -d SIDE" % (self.job_name, self.step_name, sm_layer))
                cur_side = get_side['gSIDE']
                if cur_side == 'top':
                    sm_side = 'c'
                    one_side_drl = c_side_drl
                elif cur_side == 'bottom':
                    sm_side = 's'
                    one_side_drl = s_side_drl
                else:
                    M = M_Box()
                    showText = M.msgText(u'提示', u"防焊层:%s,面次获取错误，非bottom，top，当前为!" % cur_side, showcolor='red')
                    M.msgBox(showText)
                    return False
                GEN.CLEAR_LAYER()
                GEN.FILTER_RESET()
                GEN.AFFECTED_LAYER(pthdrl, 'yes')
                GEN.SEL_REF_FEAT(self.dotdict[sm_layer]['smtmp'], 'disjoint')
                if int(GEN.GET_SELECT_COUNT()) > 0:
                    GEN.SEL_MOVE(one_side_drl)
                    GEN.AFFECTED_LAYER(pthdrl, 'no')
                else:
                    GEN.AFFECTED_LAYER(pthdrl, 'no')
            gSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, pthdrl))
            symlist = [self.stringtonum(i.strip('r')) for i in gSym["gSYMS_HISTsymbol"]]
            for i in symlist:
                if 510 < i < 910:
                    # === -101.6 --> +101.6
                    destsize = i + 101.6,
                    self.mvhole(pthdrl, i, destsize, dotdrl)
                elif i > 910:
                    destsize = i - 203.2
                    self.mvhole(pthdrl, i, destsize, dotdrl)
            if GEN.LAYER_EXISTS(c_side_drl) == 'yes':
                GEN.CLEAR_LAYER()
                GEN.AFFECTED_LAYER(c_side_drl, 'yes')
                GEN.SEL_COPY(cdot, size='-101.6')
                GEN.AFFECTED_LAYER(c_side_drl, 'no')

                gSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, c_side_drl))
                symlist = [self.stringtonum(i.strip('r')) for i in gSym["gSYMS_HISTsymbol"]]
                self.info_mess.append(
                    u'Step:%s C面有单面开窗的孔径%s，注意不允许入孔(接受每边4mil(MAX)露铜ring的做法)。' % (self.step_name, symlist))
                for i in symlist:
                    if 510 < i < 910:
                        # === -101.6 --> +101.6
                        destsize = i + 101.6,
                        self.mvhole(c_side_drl, i, destsize, sdot)
                    elif i > 910:
                        destsize = i - 203.2
                        self.mvhole(c_side_drl, i, destsize, sdot)
            if GEN.LAYER_EXISTS(s_side_drl) == 'yes':
                GEN.CLEAR_LAYER()
                GEN.AFFECTED_LAYER(s_side_drl, 'yes')
                GEN.SEL_COPY(sdot, size='-101.6')
                GEN.AFFECTED_LAYER(s_side_drl, 'no')

                gSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, s_side_drl))
                symlist = [self.stringtonum(i.strip('r')) for i in gSym["gSYMS_HISTsymbol"]]
                for i in symlist:
                    if 510 < i < 910:
                        # === -101.6 --> +101.6
                        destsize = i + 101.6,
                        self.mvhole(s_side_drl, i, destsize, cdot)
                    elif i > 910:
                        destsize = i - 203.2
                        self.mvhole(s_side_drl, i, destsize, cdot)
                self.info_mess.append(
                    u'Step:%s S面有单面开窗的孔径%s，注意不允许入孔(接受每边4mil(MAX)露铜ring的做法)。' % (self.step_name, symlist))

            gSymend = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, pthdrl))
            if len(gSymend["gSYMS_HISTsymbol"]) != 0:
                M = M_Box()
                showText = M.msgText(u'提示', u"Error018:挡点制作过程中，有超出规范定义区间，请检查层%s!" % pthdrl, showcolor='green')
                M.msgBox(showText)
                return False
            else:
                GEN.DELETE_LAYER(pthdrl)

        # ===  增加cdc、cds层别的挡点 2021.04.13 ===
        if GEN.LAYER_EXISTS(tmp_cdc_drl) == 'yes':
            GEN.CLEAR_LAYER()
            # 获取层别物件
            gSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, tmp_cdc_drl))
            symlist = [self.stringtonum(i.strip('r')) for i in gSym["gSYMS_HISTsymbol"]]
            for i in symlist:
                if i < 1010:
                    destsize = i + 152.4
                    self.mvhole_withattr(tmp_cdc_drl, i, destsize, cdot, attr='npth_dot')
                elif i >= 1010:
                    destsize = i - 203.2
                    self.mvhole_withattr(tmp_cdc_drl, i, destsize, cdot, attr='npth_dot')

        if GEN.LAYER_EXISTS(tmp_cds_drl) == 'yes':
            GEN.CLEAR_LAYER()
            # 获取层别物件
            gSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, tmp_cds_drl))
            symlist = [self.stringtonum(i.strip('r')) for i in gSym["gSYMS_HISTsymbol"]]
            for i in symlist:
                if i < 1010:
                    destsize = i + 152.4
                    self.mvhole_withattr(tmp_cds_drl, i, destsize, sdot, attr='npth_dot')
                elif i >= 1010:
                    destsize = i - 203.2
                    self.mvhole_withattr(tmp_cds_drl, i, destsize, sdot, attr='npth_dot')

        # 挡点制作后检查
        for smlayer in self.dotdict:
            glyrside = GEN.DO_INFO("-t layer -e %s/%s/%s -d SIDE" % (self.job_name, self.step_name, smlayer))
            if glyrside['gSIDE'] == 'top' or glyrside['gSIDE'] == 'bottom':
                self.dotdict[smlayer]['SIDE'] = glyrside['gSIDE']
            side = self.dotdict[smlayer]['SIDE']
            tmpchecklayer = ''

            if self.ui.checkBox_dot2cu.isChecked():
                # === 2020.07.08 薛工提议缩挡点至最小0.5mm，更改此方案
                if self.dotdict[smlayer]['SIDE'] == 'top':
                    siglayer = 'l1'
                    cdot = '__tmpcdot__'
                    # 如果是在set 里面那么将层flatten 一层出来 2021.04.13 唐成
                    sig_flatten_name = "%s_flatten_%s" % (siglayer, str(random.randint(100, 999)))
                    if self.step_name == 'set':
                        GEN.COM("flatten_layer, source_layer=%s,target_layer=%s" % (siglayer, sig_flatten_name))
                        siglayer = sig_flatten_name
                    tmpchecklayer = self.makenpthDot10toCopper(dotdrl, 'top', cdot, siglayer, tmpchecklayer)
                    # 如果是在set 需要将flatten出来的层删除 2021.04.13 唐成
                    if self.step_name == 'set':
                        GEN.COM("delete_layer,layer=%s" % sig_flatten_name)
                elif self.dotdict[smlayer]['SIDE'] == 'bottom':
                    siglayer = 'l' + str(int(self.job_name[4:6]))
                    sdot = '__tmpsdot__'
                    # 如果是在set 里面那么将层flatten 一层出来 2021.04.13 唐成
                    sig_flatten_name = "%s_flatten_%s" % (siglayer, str(random.randint(100, 999)))
                    if self.step_name == 'set':
                        GEN.COM("flatten_layer, source_layer=%s,target_layer=%s" % (siglayer, sig_flatten_name))
                        siglayer = sig_flatten_name
                    tmpchecklayer = self.makenpthDot10toCopper(dotdrl, 'bottom', sdot, siglayer, tmpchecklayer)
                    # 如果是在set 需要将flatten出来的层删除 2021.04.13 唐成
                    if self.step_name == 'set':
                        GEN.COM("delete_layer,layer=%s" % sig_flatten_name)
            else:
                if GEN.LAYER_EXISTS(dotdrl) == 'yes':
                    GEN.AFFECTED_LAYER(dotdrl, 'yes')
                    GEN.SEL_COPY('md1')
                    GEN.SEL_COPY('md2')
                    GEN.CLEAR_LAYER()
                if GEN.LAYER_EXISTS(cdot) == 'yes':
                    GEN.AFFECTED_LAYER(cdot, 'yes')
                    GEN.SEL_COPY('md1')
                    GEN.CLEAR_LAYER()
                    GEN.DELETE_LAYER(cdot)
                if GEN.LAYER_EXISTS(sdot) == 'yes':
                    GEN.AFFECTED_LAYER(sdot, 'yes')
                    GEN.SEL_COPY('md2')
                    GEN.CLEAR_LAYER()
                    GEN.DELETE_LAYER(sdot)
        # === 2020.07.08 以下方案更改为缩挡点，更改的代码在上方
        # if self.ui.checkBox_dot2cu.isChecked ():
        # 挡点距不同网络铜皮线路间距需≥12mil（极限10MIL）间距不够削挡点
        # self.shavenpthdot2cu()
        GEN.DELETE_LAYER(dotdrl)
        # GEN.PAUSE('XXXXXXXXXXXXXXXXXXXXXXXXXXX')
        # 版本 1.6.1 2020-10-20 唐成 （按照 story-view-2167，要求 ≤ 0.4加档点比防焊大时，缩小至比阻焊单边小1mil）
        self.check_md_layer_large_maskl()
        # 版本V2.2 2022.07.01 宋超 （增加挡点运行完成后距离是否大于5mil的检查）
        self.check_dot_dist()

        return True

    def check_md_layer_large_maskl(self):
        """
        处理 ≤0.4 的过孔档点
        :return:
        """
        # 清理掉以前的过滤器设置
        GEN.FILTER_RESET()
        # 选择via 孔，复制到另一层
        GEN.AFFECTED_LAYER(self.drl, "yes")
        GEN.COM("filter_set, filter_name=popup, update_popup=yes, feat_types=pad")
        GEN.COM("filter_atr_set, filter_name=popup, condition=yes, attribute=.drill, option=via")
        GEN.FILTER_SELECT()
        GEN.FILTER_RESET()

        if (GEN.GET_SELECT_COUNT() > 0):  # 如果选中了就复制到另一层
            # === 2022.07.01 由于原程序缩进结构太多，不改变原判断的情况下，更改缩进结构
            pass
        else:
            return True
        my_tmp_via_layer = "tmp_via_%s" % (random.randint(111, 999));
        GEN.SEL_COPY(target_layer=my_tmp_via_layer);
        GEN.AFFECTED_LAYER(self.drl, "no");

        dic_info = GEN.DO_INFO("-t layer -e %s/%s/drl -d SYMS_HIST,units=mm" % (self.job_name, self.step_name));
        drl_size_list = dic_info["gSYMS_HISTsymbol"];
        # 选出≤0.4的孔 str
        need_deal_with_list = "";
        for hole_size in drl_size_list:
            my_splitd = hole_size.split("r");
            if (len(my_splitd) == 2 and float(my_splitd[1]) <= 409):
                need_deal_with_list += "%s;" % (hole_size)

        # 如果找到了钻孔就处理
        if (len(need_deal_with_list) > 1):
            # === 2022.07.01 由于原程序缩进结构太多，不改变原判断的情况下，更改缩进结构
            pass
        else:
            return True
        # 选中需要处理的孔，反选如果有就删除掉
        GEN.AFFECTED_LAYER(my_tmp_via_layer, "yes")
        GEN.COM("filter_set, filter_name=popup, update_popup=no, polarity=positive")
        GEN.COM("filter_set, filter_name=popup, update_popup=no, include_syms=%s" % (need_deal_with_list))
        GEN.FILTER_SELECT()
        GEN.FILTER_RESET()
        select_via_num = GEN.GET_SELECT_COUNT()
        GEN.COM("sel_reverse")
        if (GEN.GET_SELECT_COUNT() > 0):
            GEN.COM("sel_delete")
        GEN.AFFECTED_LAYER(my_tmp_via_layer, "no")
        # 取得mask 和 md 档点层
        matrix_info_dic = GEN.DO_INFO("-t matrix -e %s/matrix -d ROW" % (self.job_name))
        row_name_list = matrix_info_dic.get("gROWname")
        row_contect_list = matrix_info_dic.get("gROWcontext")
        row_layer_type_list = matrix_info_dic.get("gROWlayer_type")

        row_index = 0
        mask_md_layer_dic = {}
        while (row_index < len(row_name_list)):
            if (row_name_list[row_index] == "m1" or row_name_list[row_index] == "m2"):
                mask_layer = row_name_list[row_index]
                if (row_contect_list[row_index] == "board" and row_layer_type_list[row_index] == "solder_mask"):
                    row_index_md = 0
                    while (row_index_md < len(row_name_list)):
                        if (row_contect_list[row_index_md] == "board"):
                            if (mask_layer == "m1" and row_name_list[row_index_md] == "md1"):
                                mask_md_layer_dic[mask_layer] = row_name_list[row_index_md]
                            elif (mask_layer == "m2" and row_name_list[row_index_md] == "md2"):
                                mask_md_layer_dic[mask_layer] = row_name_list[row_index_md]
                        row_index_md += 1
            row_index += 1

        # 处理 ≤ 0.4 的过孔档点
        for key, value in mask_md_layer_dic.items():
            mask_layer = key;
            md_layer = value;
            if (mask_layer.startswith("m") and md_layer.startswith("m")):
                # 复制出来的阻焊pad层和md 层
                mask_pad_layer = ""
                md_pad_layer = "";
                GEN.AFFECTED_LAYER(my_tmp_via_layer, "yes");
                GEN.SEL_RESIZE("279.4");
                GEN.AFFECTED_LAYER(my_tmp_via_layer, "no");

                # 覆盖选中mask层的档点
                my_tmp_mask_layer = "tmp_mask_layer_%s" % (random.randint(111, 999));
                GEN.AFFECTED_LAYER(mask_layer, "yes");
                # 将组焊层复制到另一层清理点铜皮里面的焊盘
                GEN.SEL_COPY(my_tmp_mask_layer);
                GEN.AFFECTED_LAYER(mask_layer, "no");

                # 删除覆盖的焊盘 checklist
                checklist_name = "checklist_nfp_%s" % (random.randint(111, 999));
                GEN.COM("chklist_single, action = valor_dfm_nfpr, show = yes");
                GEN.COM("chklist_pclear");
                GEN.COM("chklist_cupd, chklist = valor_dfm_nfpr, nact = 1, params = "
                        "((pp_layer=%s)(pp_delete=Covered)(pp_work=Copper)"
                        "(pp_drill=PTH\;NPTH\;Via\;PTH - Pressfit\;Via - Laser\;Via - Photo)(pp_non_drilled=No)"
                        "(pp_in_selected=All)(pp_remove_mark=Remove)), mode = regular" % (my_tmp_mask_layer));
                GEN.COM("chklist_pcopy, chklist = valor_dfm_nfpr, nact = 1");
                GEN.COM("chklist_create, chklist = %s" % (checklist_name));
                GEN.COM("chklist_show, chklist = %s" % (checklist_name));
                GEN.COM("chklist_close, chklist = valor_dfm_nfpr, mode = hide");
                GEN.COM("chklist_ppaste, chklist = %s, row = 0" % (checklist_name));
                GEN.COM("chklist_cupd, chklist = %s, nact = 1, params = "
                        "((pp_layer=%s)(pp_delete=Covered)(pp_work=Copper)"
                        "(pp_drill=PTH\;NPTH\;Via\;PTH - Pressfit\;Via - Laser\;Via - Photo)(pp_non_drilled=No)"
                        "(pp_in_selected=All)(pp_remove_mark=Remove)), mode = regular" % (
                            checklist_name, my_tmp_mask_layer));
                GEN.COM("chklist_run, chklist = %s, nact = a, area =global" % (checklist_name));

                if platform.system() == "Windows":
                    GEN.COM("chklist_close, chklist = %s" % (checklist_name));
                else:
                    GEN.COM("show_tab,tab=Checklists,show=no");

                # 设置只选中正性
                GEN.COM("filter_set, filter_name = popup, update_popup = no, polarity = positive");
                GEN.AFFECTED_LAYER(my_tmp_mask_layer, "yes");
                GEN.SEL_REF_FEAT(my_tmp_via_layer, "cover");
                if (GEN.GET_SELECT_COUNT() > 0):
                    mask_pad_layer = "mask_pad_%s" % (random.randint(111, 999));
                    GEN.SEL_COPY(mask_pad_layer);
                GEN.AFFECTED_LAYER(my_tmp_mask_layer, "no");
                GEN.COM("filter_reset, filter_name = popup");
                # 删除复制的零时mask layer
                GEN.DELETE_LAYER(my_tmp_mask_layer);

                # 覆盖选中md层的档点
                GEN.AFFECTED_LAYER(md_layer, "yes");
                GEN.SEL_REF_FEAT(my_tmp_via_layer, "cover");
                if (GEN.GET_SELECT_COUNT() > 0):
                    md_pad_layer = "md_pad_%s" % (random.randint(111, 999));
                    GEN.SEL_COPY(md_pad_layer);
                GEN.AFFECTED_LAYER(md_layer, "no");
                # 将钻孔返回尺寸
                GEN.AFFECTED_LAYER(my_tmp_via_layer, "yes");
                GEN.SEL_RESIZE("-279.4");
                GEN.AFFECTED_LAYER(my_tmp_via_layer, "no");

                # 如果mask pad 和 md pad 都有就处理
                if (len(md_pad_layer) > 1 and len(mask_pad_layer) > 1):
                    GEN.AFFECTED_LAYER(mask_pad_layer, "yes");
                    GEN.SEL_REF_FEAT(md_pad_layer, "cover");

                    maskcover_md_pad_layer = "";
                    if (GEN.GET_SELECT_COUNT() > 0):  # 如果有被焊盘完全覆盖的焊盘就处理
                        GEN.COM("sel_reverse");
                        if (GEN.GET_SELECT_COUNT() > 0):  # 如果被覆盖以外有焊盘删除处理
                            GEN.COM("sel_delete");
                        GEN.AFFECTED_LAYER(mask_pad_layer, "no");

                        # 加大 mask layer size
                        GEN.AFFECTED_LAYER(mask_pad_layer, "yes");
                        GEN.SEL_RESIZE("254");
                        GEN.AFFECTED_LAYER(mask_pad_layer, "no");

                        # 选中 md layer 被 mask layer 覆盖的删除
                        GEN.AFFECTED_LAYER(md_pad_layer, "yes");
                        GEN.SEL_REF_FEAT(mask_pad_layer, "cover");

                        if (GEN.GET_SELECT_COUNT() > 0):  # 如果有被cover 的就处理
                            GEN.COM("sel_reverse");
                            if (GEN.GET_SELECT_COUNT() > 0):  # 如果被覆盖以外还有pad 复制到另一层参考铜皮覆盖的，制作
                                # GEN.COM("sel_delete");
                                maskcover_md_pad_layer = "mask_cover_pad_%s" % (random.randint(111, 999));
                                GEN.SEL_MOVE(target_layer=maskcover_md_pad_layer);
                            GEN.AFFECTED_LAYER(md_pad_layer, "no");

                            # 缩回 mask layer size
                            GEN.AFFECTED_LAYER(mask_pad_layer, "yes");
                            GEN.SEL_RESIZE("-254");
                            GEN.AFFECTED_LAYER(mask_pad_layer, "no");

                            # 选中 mask layer 再次被 md layer 覆盖的，就是被mask覆盖的
                            GEN.AFFECTED_LAYER(mask_pad_layer, "yes");
                            GEN.SEL_REF_FEAT(md_pad_layer, "cover");
                            if (GEN.GET_SELECT_COUNT() > 0):
                                GEN.COM("sel_reverse");
                                if (GEN.GET_SELECT_COUNT() > 0):  # 如果有没有被完全覆盖的就删除
                                    GEN.COM("sel_delete");
                            GEN.AFFECTED_LAYER(mask_pad_layer, "no");

                            # 加大mask pad  layer 去覆盖 md pad layer
                            GEN.AFFECTED_LAYER(mask_pad_layer, "yes");
                            GEN.SEL_RESIZE("254");
                            GEN.AFFECTED_LAYER(mask_pad_layer, "no");

                            # 制作 md layer
                            GEN.AFFECTED_LAYER(md_layer, "yes");
                            GEN.SEL_REF_FEAT(mask_pad_layer, "cover");
                            if (GEN.GET_SELECT_COUNT() > 0):  # 如果有被cover的那么就删除，并将mask pad layer 的焊盘复制过去
                                GEN.COM("sel_delete");
                                GEN.AFFECTED_LAYER(md_layer, "no");

                                # 缩回 mask pad  layer size 复制到 md layer
                                GEN.AFFECTED_LAYER(mask_pad_layer, "yes");
                                GEN.SEL_RESIZE("-254");
                                GEN.SEL_COPY(target_layer=md_layer, size="-50.8");
                                GEN.AFFECTED_LAYER(mask_pad_layer, "no");

                            GEN.AFFECTED_LAYER(md_layer, "no");

                    # 处理被阻焊铜皮开窗覆盖的焊盘
                    if (len(maskcover_md_pad_layer) > 1):
                        GEN.COM("affected_layer, name =, mode = all, affected = no")
                        GEN.AFFECTED_LAYER(mask_layer, "yes")
                        # 选择铜皮
                        GEN.FILTER_RESET()
                        GEN.FILTER_SET_TYP('surface')
                        GEN.FILTER_SELECT()
                        GEN.FILTER_RESET()
                        if (GEN.GET_SELECT_COUNT() > 0):
                            mask_surface_layer = "mask_surface_layer_%s" % (random.randint(111, 999));
                            GEN.SEL_COPY(mask_surface_layer);
                            GEN.AFFECTED_LAYER(mask_layer, "no");
                            GEN.AFFECTED_LAYER(mask_surface_layer, "yes");
                            GEN.SEL_CONTOURIZE();
                            GEN.AFFECTED_LAYER(mask_surface_layer, "no");

                            GEN.AFFECTED_LAYER(my_tmp_via_layer, "yes");
                            GEN.SEL_REF_FEAT(mask_surface_layer, "cover");
                            # GEN.PAUSE("fffffffffffff");
                            if (GEN.GET_SELECT_COUNT() > 0):
                                mask_sur_coverd_via = "mask_sur_coverd_via_%s" % (random.randint(111, 999));
                                GEN.SEL_COPY(target_layer=mask_sur_coverd_via);
                                GEN.AFFECTED_LAYER(my_tmp_via_layer, "no");

                                # 将钻孔属性取消，定义复制出来的为钻孔属性，分析过孔开窗小于5mil的处理.
                                GEN.COM(
                                    "matrix_layer_context, job=%s, matrix=matrix, layer=%s, context=misc" % (
                                        self.job_name, self.drl))

                                GEN.COM(
                                    "matrix_layer_context,job=%s,matrix = matrix,layer = %s,context = board" % (
                                        self.job_name, mask_sur_coverd_via))
                                GEN.COM(
                                    "matrix_layer_type,job=%s, matrix = matrix, layer = %s, type = drill" % (
                                        self.job_name, mask_sur_coverd_via))

                                GEN.COM(
                                    "matrix_layer_context,job=%s,matrix = matrix,layer = %s,context = board" % (
                                        self.job_name, mask_surface_layer))
                                GEN.COM(
                                    "matrix_layer_type,job=%s, matrix = matrix, layer = %s, type = solder_mask" % (
                                        self.job_name, mask_surface_layer))

                                # check list 分析
                                My_unit = GEN.GET_UNITS();
                                GEN.CHANGE_UNITS("inch");
                                checklist_name = "mask_sur_via__run_%s" % (random.randint(111, 999));
                                GEN.COM("chklist_create, chklist=%s" % (checklist_name));
                                GEN.COM("chklist_show, chklist=%s" % (checklist_name));
                                GEN.COM("chklist_single, action = valor_analysis_sm, show = yes");
                                GEN.COM("chklist_pclear");
                                GEN.COM("chklist_cupd, chklist = valor_analysis_sm, nact = 1, params = "
                                        "((pp_layers=%s)(pp_ar=5)(pp_coverage=3)(pp_sm2r=6)"
                                        "(pp_sliver=6)(pp_spacing=6)(pp_bridge=6)(pp_min_clear_overlap=5)"
                                        "(pp_tests=Drill\;Pads\;Clearance Connection)(pp_selected=All)"
                                        "(pp_use_compensated_rout=No)), mode = regular" % (mask_surface_layer));
                                GEN.COM("chklist_pcopy, chklist = valor_analysis_sm, nact = 1");
                                GEN.COM("chklist_close, chklist = valor_analysis_sm, mode = hide");
                                GEN.COM("chklist_ppaste, chklist = %s, row = 0" % (checklist_name));
                                GEN.COM("chklist_cupd, chklist = %s, nact = 1, params = ((pp_layers=%s)"
                                        "(pp_ar=5)(pp_coverage=3)(pp_sm2r=6)(pp_sliver=6)(pp_spacing=6)(pp_bridge=6)"
                                        "(pp_min_clear_overlap=5)(pp_tests=Drill\;Pads\;Clearance Connection)"
                                        "(pp_selected=All)(pp_use_compensated_rout=No)), mode = regular" % (
                                            checklist_name, mask_surface_layer));
                                GEN.COM("chklist_run, chklist = %s, nact = a, area =global" % (checklist_name));
                                if platform.system() == "Windows":
                                    GEN.COM("chklist_close, chklist = %s" % (checklist_name));
                                else:
                                    GEN.COM("show_tab,tab=Checklists,show=no");

                                # 读取分析数据，参考选择via
                                # 检测check list
                                check_args = "-t check -e %s/%s/%s -d MEAS -o action=1" % (
                                    self.job_name, self.step_name, checklist_name);
                                my_via_pad_run_list = GEN.INFO(args=check_args, units="inch");
                                # 分析完成后将属性还原
                                GEN.COM(
                                    "matrix_layer_context, job = %s, matrix = matrix, layer = %s, context = board" % (
                                        self.job_name, self.drl));

                                GEN.COM(
                                    "matrix_layer_context,job=%s,matrix = matrix,layer = %s,context = misc" % (
                                        self.job_name, mask_sur_coverd_via));
                                GEN.COM(
                                    "matrix_layer_type,job=%s, matrix = matrix, layer = %s, type = drill" % (
                                        self.job_name, mask_sur_coverd_via));

                                GEN.COM(
                                    "matrix_layer_context,job=%s,matrix = matrix,layer = %s,context = misc" % (
                                        self.job_name, mask_surface_layer));
                                GEN.COM(
                                    "matrix_layer_type,job=%s, matrix = matrix, layer = %s, type = solder_mask" % (
                                        self.job_name, mask_surface_layer));

                                ar_via_list = [];
                                for row in my_via_pad_run_list:
                                    if (row.startswith("ar_via")):
                                        splitd_str = row.split(" ");
                                        # 如果小于等于5.0的选出来处理
                                        if (float(splitd_str[2]) <= 5.00 and splitd_str[0] == "ar_via"):
                                            ar_via_list.append(row);
                                # 如果铜皮过孔开窗有小于5mil的，需要处理
                                if (len(ar_via_list)):
                                    via_rin_layer = "via_rin_layer_%s" % random.randint(111, 999);
                                    my_drl_via_rin_layer = "my_drl_via_rin_layer_%s" % (
                                        random.randint(111, 999));
                                    GEN.CREATE_LAYER(via_rin_layer);
                                    GEN.AFFECTED_LAYER(via_rin_layer, "yes");
                                    # 添加焊盘参考选择via孔
                                    for mask_sur_rin in ar_via_list:
                                        splitd_rin = mask_sur_rin.split(" ");
                                        GEN.ADD_PAD(add_x=float(splitd_rin[6]), add_y=float(splitd_rin[7]),
                                                    symbol="r2");
                                    GEN.AFFECTED_LAYER(via_rin_layer, "no");

                                    # 如果选出来有那么参考 md_pad,有接触的证明已经处理过了不需要处理
                                    GEN.AFFECTED_LAYER(via_rin_layer, "yes");
                                    GEN.SEL_REF_FEAT(md_pad_layer, "touch");
                                    if (GEN.GET_SELECT_COUNT() > 0):
                                        GEN.COM("sel_delete");
                                    GEN.AFFECTED_LAYER(via_rin_layer, "no");

                                    GEN.AFFECTED_LAYER(my_tmp_via_layer, "yes");
                                    GEN.SEL_REF_FEAT(via_rin_layer, "touch");
                                    if (GEN.GET_SELECT_COUNT() > 0):

                                        GEN.SEL_COPY(my_drl_via_rin_layer);
                                        GEN.AFFECTED_LAYER(my_tmp_via_layer, "no");
                                        GEN.AFFECTED_LAYER(my_drl_via_rin_layer, "yes");
                                        GEN.SEL_RESIZE("16");
                                        GEN.AFFECTED_LAYER(my_drl_via_rin_layer, "no");
                                        GEN.AFFECTED_LAYER(md_layer, "yes");
                                        GEN.SEL_REF_FEAT(my_drl_via_rin_layer, "cover");
                                        if (GEN.GET_SELECT_COUNT() > 0):
                                            md_mask_sur_via_coverd_layer = "md_mask_sur_via_coverd_layer_%s" % (
                                                random.randint(111, 999));
                                            # 将完全覆盖的移到林外一层
                                            GEN.SEL_MOVE(target_layer=md_mask_sur_via_coverd_layer);
                                            GEN.AFFECTED_LAYER(md_layer, "no");

                                            # 反过来参考选择（有可能有些过孔在md没有添加档点）
                                            GEN.AFFECTED_LAYER(my_drl_via_rin_layer, "yes");
                                            GEN.SEL_REF_FEAT(md_mask_sur_via_coverd_layer, "touch");
                                            if (GEN.GET_SELECT_COUNT() > 0):
                                                GEN.COM("sel_reverse");
                                                if (GEN.GET_SELECT_COUNT() > 0):
                                                    GEN.COM("sel_delete");
                                                GEN.SEL_RESIZE("-16");
                                                GEN.SEL_COPY(target_layer=md_layer, size="4");
                                                GEN.AFFECTED_LAYER(my_drl_via_rin_layer, "no");
                                                GEN.DELETE_LAYER(my_drl_via_rin_layer);
                                            else:
                                                GEN.SEL_RESIZE("-16");
                                                GEN.AFFECTED_LAYER(my_drl_via_rin_layer, "no");
                                                GEN.DELETE_LAYER(my_drl_via_rin_layer);
                                            GEN.DELETE_LAYER(md_mask_sur_via_coverd_layer);
                                        GEN.AFFECTED_LAYER(md_layer, "no");
                                    else:
                                        GEN.AFFECTED_LAYER(my_tmp_via_layer, "no");
                                    GEN.DELETE_LAYER(via_rin_layer);
                                # 删除层
                                GEN.DELETE_LAYER(mask_sur_coverd_via);
                                GEN.CHANGE_UNITS(My_unit);

                            GEN.AFFECTED_LAYER(my_tmp_via_layer, "no");
                            GEN.AFFECTED_LAYER(maskcover_md_pad_layer, "no");
                        GEN.AFFECTED_LAYER(mask_layer, "no");
                        GEN.DELETE_LAYER(maskcover_md_pad_layer);
                        GEN.DELETE_LAYER(mask_surface_layer);

                    GEN.AFFECTED_LAYER(mask_pad_layer, "no");
                # 删除创建的层
                GEN.DELETE_LAYER(my_tmp_mask_layer);
                if (len(md_pad_layer) > 1):
                    GEN.DELETE_LAYER(md_pad_layer);
                if (len(mask_pad_layer) > 1):
                    GEN.DELETE_LAYER(mask_pad_layer);
        # 删除 tmp via layer
        GEN.DELETE_LAYER(my_tmp_via_layer)

        GEN.AFFECTED_LAYER(self.drl, "no")

    def check_dot_dist(self):
        """
        通过checklist分析是否挡点间距小于 5mil http://192.168.2.120:82/zentao/story-view-4283.html
        :return:
        """
        GEN.CHANGE_UNITS("inch")
        checklist_name = "dotchk_%s" % (random.randint(111, 999))
        GEN.COM("chklist_create, chklist=%s" % (checklist_name))
        GEN.COM('chklist_cadd,chklist=%s,action=valor_analysis_signal,erf=,params=,row=0' % checklist_name)
        GEN.COM(
            'chklist_cupd,chklist=%s,nact=1,params=((pp_layer=md1\;md2)(pp_spacing=10)(pp_r2c=10)(pp_d2c=10)'
            '(pp_sliver=4)(pp_min_pad_overlap=5)(pp_tests=Spacing)(pp_selected=All)'
            '(pp_check_missing_pads_for_drills=Yes)(pp_use_compensated_rout=No)(pp_sm_spacing=No)),mode=regular' % checklist_name)
        for settings in ['classify_c2c', 'classify_smd2c', 'v_separate_p2c', 'v_report_encap_pad']:
            GEN.COM(
                'chklist_erf_variable,chklist=%s, nact=1, variable=%s, value=0, options=0' % (checklist_name, settings))
        GEN.COM('chklist_run, chklist=%s, nact=1, area=global, async_run=no' % checklist_name)
        get_sp_result = GEN.INFO("-t check -e %s/%s/%s -d MEAS -o index+action=1+category=general_sp" % (
            self.job_name, self.step_name, checklist_name),units='inch')
        result_list = [i.split()[2] for i in get_sp_result]
        warn_list = []
        for r_value in result_list:
            if float(r_value) < 5.0:
                warn_list.append(r_value)
        if len(warn_list) == 0:
            GEN.COM('chklist_delete,chklist=%s' % checklist_name)
        else:
            M = M_Box()
            showText = M.msgText(u'需手动削档点使间距≥5MIL', u"Step:%s有挡点间距小于5mil,详见checklist：%s!" % (self.step_name,checklist_name), showcolor='red')
            M.msgBox(showText)

    def makenpthDot10toCopper(self, dotdrl, side, tmpdot, siglayer, tmpchecklayer):
        """
        :param dotdrl: 需做挡点的钻孔层
        :param side: top or bottom
        :param tmpdot: cdot或者sdot
        :return:
        """
        # 阻焊层名字
        mask_name = None
        mdlayer = None
        if side == 'top':
            mdlayer = 'md1'
            mask_name = 'm1'
        elif side == 'bottom':
            mdlayer = 'md2'
            mask_name = 'm2'
        checklayer = '__tmpcheck%s' % mdlayer
        sigtmplayer = '__tmp' + siglayer + '__'
        GEN.DELETE_LAYER(sigtmplayer)
        GEN.CLEAR_LAYER()
        # === V2.2 add by Song ===
        if GEN.LAYER_EXISTS(dotdrl) == 'yes':
            GEN.AFFECTED_LAYER(dotdrl, 'yes')
            GEN.SEL_COPY(tmpdot)
            GEN.CLEAR_LAYER()
        # === 信号层做临时层，用于去除负片并更改
        GEN.AFFECTED_LAYER(siglayer, 'yes')
        # TODO === for test 2021.12.03 ===
        GEN.SEL_COPY(sigtmplayer)
        GEN.AFFECTED_LAYER(siglayer, 'no')

        # 将tmpdot 复制到另一层加大参考
        copy_tmpdot = "%s_%s" % (tmpdot, random.randint(100, 999))
        if GEN.LAYER_EXISTS(copy_tmpdot, job=self.job_name, step=self.step_name) == 'yes':
            GEN.DELETE_LAYER(copy_tmpdot)
        GEN.AFFECTED_LAYER(tmpdot, 'yes')
        GEN.SEL_COPY(target_layer=copy_tmpdot, size='1016')
        GEN.AFFECTED_LAYER(tmpdot, 'no')
        GEN.AFFECTED_LAYER(sigtmplayer, 'yes')
        GEN.COM("filter_reset, filter_name = popup")
        GEN.COM("filter_set,filter_name=popup,update_popup=no,polarity=positive")
        GEN.SEL_REF_FEAT(copy_tmpdot, 'disjoint')
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.COM("sel_delete")
        GEN.COM("filter_reset, filter_name = popup")
        GEN.AFFECTED_LAYER(sigtmplayer, 'no')
        GEN.DELETE_LAYER(copy_tmpdot)

        # 将阻焊层复制到线路零时层叠掉阻焊开窗的铜  2024.04.14 唐成
        if self.step_name == "edit" and GEN.LAYER_EXISTS(mask_name, job=self.job_name, step=self.step_name) == 'yes':
            temp_mask = "%s_tmp_%s" % (mask_name, random.randint(100, 999));
            if GEN.LAYER_EXISTS(temp_mask, job=self.job_name, step=self.step_name) == 'yes':
                GEN.DELETE_LAYER(temp_mask)
            GEN.AFFECTED_LAYER(mask_name, 'yes')
            GEN.SEL_COPY(temp_mask)
            GEN.AFFECTED_LAYER(mask_name, 'no')
            # 复制档点层加大5mil
            copy_tmpdot_2 = "%s_%s" % (tmpdot, random.randint(100, 999))
            GEN.AFFECTED_LAYER(tmpdot, 'yes')
            if GEN.LAYER_EXISTS(copy_tmpdot_2, job=self.job_name, step=self.step_name) == 'yes':
                GEN.DELETE_LAYER(copy_tmpdot_2)
            GEN.SEL_COPY(target_layer=copy_tmpdot_2, size='254')
            GEN.AFFECTED_LAYER(tmpdot, 'no')

            # 被档点完全覆盖的删除在用阻焊叠线路
            GEN.AFFECTED_LAYER(temp_mask, 'yes')
            GEN.SEL_REF_FEAT(copy_tmpdot_2, 'cover')
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.COM("sel_delete")

            self.contourizeFill(fill='no', twicecont='no', decompose='no')
            GEN.SEL_COPY(target_layer=sigtmplayer, invert='yes')
            GEN.AFFECTED_LAYER(temp_mask, 'no')

            # 整合后加大线路
            GEN.AFFECTED_LAYER(sigtmplayer, 'yes')
            self.contourizeFill(fill='no', twicecont='no', decompose='no')
            # === npth dot  到铜10 mil 线路层加大20mil
            GEN.SEL_RESIZE('508')
            GEN.AFFECTED_LAYER(sigtmplayer, 'no')
            # 加大后再用阻焊去叠
            GEN.AFFECTED_LAYER(temp_mask, 'yes')
            GEN.SEL_COPY(target_layer=sigtmplayer, invert='yes')
            GEN.AFFECTED_LAYER(temp_mask, 'no')

            GEN.DELETE_LAYER(copy_tmpdot_2)
            GEN.DELETE_LAYER(temp_mask)
        elif self.step_name == "set" and GEN.LAYER_EXISTS(mask_name, job=self.job_name, step=self.step_name) == 'yes':
            temp_mask = "%s_tmp_%s" % (mask_name, random.randint(100, 999))
            GEN.COM("flatten_layer, source_layer=%s,target_layer=%s" % (mask_name, temp_mask))
            # 复制档点层加大5mil
            copy_tmpdot_2 = "%s_%s" % (tmpdot, random.randint(100, 999))
            GEN.AFFECTED_LAYER(tmpdot, 'yes')
            if GEN.LAYER_EXISTS(copy_tmpdot_2, job=self.job_name, step=self.step_name) == 'yes':
                GEN.DELETE_LAYER(copy_tmpdot_2)
            GEN.SEL_COPY(target_layer=copy_tmpdot_2, size='254')
            GEN.AFFECTED_LAYER(tmpdot, 'no')
            # 被档点完全覆盖的删除在用阻焊叠线路
            GEN.AFFECTED_LAYER(temp_mask, 'yes')
            GEN.SEL_REF_FEAT(copy_tmpdot_2, 'cover')
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.COM("sel_delete")
            self.contourizeFill(fill='no', twicecont='no', decompose='no')
            GEN.SEL_COPY(target_layer=sigtmplayer, invert='yes')
            GEN.AFFECTED_LAYER(temp_mask, 'no')

            # 整合后加大线路
            GEN.AFFECTED_LAYER(sigtmplayer, 'yes')
            self.contourizeFill(fill='no', twicecont='no', decompose='no')
            # === npth dot  到铜10 mil 线路层加大20mil
            GEN.SEL_RESIZE('508')
            GEN.AFFECTED_LAYER(sigtmplayer, 'no')
            # 加大后再用阻焊去叠
            GEN.AFFECTED_LAYER(temp_mask, 'yes')
            GEN.SEL_COPY(target_layer=sigtmplayer, invert='yes')
            GEN.AFFECTED_LAYER(temp_mask, 'no')

            GEN.DELETE_LAYER(copy_tmpdot_2)
            GEN.DELETE_LAYER(temp_mask)

        GEN.AFFECTED_LAYER(sigtmplayer, 'yes')
        self.contourizeFill(fill='no', twicecont='no', decompose='no')
        # 处理掉变形的铜皮
        GEN.SEL_RESIZE('-127')
        GEN.SEL_RESIZE('127')
        self.contourizeFill(fill='yes', twicecont='no', decompose='no')
        # == Bug 只有负片时，无法整体化 === 判断此层别是否仅有负性，如果是，删除内容
        GEN.FILTER_RESET()
        GEN.FILTER_SET_POL('negative')
        GEN.FILTER_SELECT()
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.SEL_REVERSE()
            if int(GEN.GET_SELECT_COUNT()) == 0:
                # === 此时，无正极性物件 ===执行以下语句达到所有物件删除的作用
                GEN.SEL_DELETE()
        GEN.FILTER_RESET()
        GEN.AFFECTED_LAYER(sigtmplayer, 'no')
        GEN.AFFECTED_LAYER(tmpdot, 'yes')
        # 非NPTH的挡点先移动到挡点层
        # 过滤npth孔的挡点
        GEN.FILTER_RESET()
        # .bit=npth_dot
        GEN.COM('filter_atr_reset')
        GEN.COM('filter_atr_set, filter_name = popup, condition = yes, attribute =.bit, text = npth_dot')
        GEN.FILTER_SELECT()
        if int(GEN.GET_SELECT_COUNT()) != 0:
            GEN.SEL_REVERSE()
            if int(GEN.GET_SELECT_COUNT()) != 0:
                GEN.SEL_MOVE(mdlayer)
        else:
            # 无NPTH的挡点，退出
            # === 2020.09.24 无NPTH孔，移动到挡点层
            GEN.SEL_REVERSE()
            if int(GEN.GET_SELECT_COUNT()) != 0:
                GEN.SEL_MOVE(mdlayer)
            return ""
        GEN.SEL_REF_FEAT(sigtmplayer, 'disjoint')
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.SEL_MOVE(mdlayer)
        gSymend = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, tmpdot))
        if len(gSymend["gSYMS_HISTsymbol"]) != 0:
            GEN.SEL_COPY(checklayer)
            tmpchecklayer = checklayer + tmpchecklayer

        # 按固定值缩小，缩小到距离铜10mil为止
        while True:
            # 直到tmpdot层为空则退出
            gSymend = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, tmpdot))
            if len(gSymend["gSYMS_HISTsymbol"]) == 0:
                break
            # 挡点已经小于0.5的，直接移动到挡点层
            symlist = [self.stringtonum(i.strip('r')) for i in gSymend["gSYMS_HISTsymbol"]]
            for i in symlist:
                if i <= 500:
                    GEN.FILTER_RESET()
                    GEN.FILTER_SET_INCLUDE_SYMS('r' + str(i))
                    GEN.FILTER_SELECT()
                    self.mvhole_currentLayer(tmpdot, '0', mdlayer)
                    GEN.FILTER_RESET()
            gSymend = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, tmpdot))
            if len(gSymend["gSYMS_HISTsymbol"]) == 0:
                break
            # 每次缩10微米，添加个属性，便于区分
            GEN.COM('sel_resize,size=-10,corner_ctl=no')
            GEN.FILTER_RESET()
            GEN.COM('filter_atr_reset')
            GEN.SEL_REF_FEAT(sigtmplayer, 'disjoint')
            if int(GEN.GET_SELECT_COUNT()) > 0:
                # 带属性移至正式挡点层
                self.mvhole_currentLayer(tmpdot, '0', mdlayer)

        GEN.CLEAR_LAYER()
        GEN.DELETE_LAYER(sigtmplayer)
        GEN.DELETE_LAYER(tmpdot)
        return '' + tmpchecklayer


    def shavenpthdot2cu(self):
        """
        npth的挡点距离铜皮需大于10mil
        :return:
        """
        for sm in self.dotdict:
            glyrside = GEN.DO_INFO("-t layer -e %s/%s/%s -d SIDE" % (self.job_name, self.step_name, sm))
            if glyrside['gSIDE'] == 'top' or glyrside['gSIDE'] == 'bottom':
                self.dotdict[sm]['SIDE'] = glyrside['gSIDE']
            side = self.dotdict[sm]['SIDE']
            if self.dotdict[sm]['SIDE'] == 'top':
                mdlayer = 'md1'
                siglayer = 'l1'
            elif self.dotdict[sm]['SIDE'] == 'bottom':
                mdlayer = 'md2'
                siglayer = 'l' + str(int(self.job_name[4:6]))
            dot20 = '__' + side + 'dot20__'
            sigtmpneg = '__' + side + 'signeg__'
            sigtmppos = '__' + side + 'sigpos__'
            smtmplayer = self.dotdict[sm]['smtmp']
            GEN.DELETE_LAYER(dot20)
            GEN.DELETE_LAYER(sigtmpneg)
            GEN.DELETE_LAYER(sigtmppos)

            # 信号层辅助层处理
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER(mdlayer, 'yes')
            # 过滤npth孔的挡点
            GEN.FILTER_RESET()
            # .bit=npth_dot
            GEN.COM('filter_atr_reset')
            GEN.COM('filter_atr_set, filter_name = popup, condition = yes, attribute =.bit, text = npth_dot')
            GEN.FILTER_SELECT()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_COPY(dot20)
                GEN.AFFECTED_LAYER(mdlayer, 'no')
                GEN.AFFECTED_LAYER(dot20, 'yes')
                self.contourizeFill(twicecont='no', decompose='no')
                # 1.挡点层加大22mil  --> touch后再减小2mil
                GEN.SEL_RESIZE('558.8')
                GEN.CLEAR_LAYER()
                GEN.AFFECTED_LAYER(siglayer, 'yes')
                GEN.SEL_COPY(sigtmpneg)
                GEN.AFFECTED_LAYER(siglayer, 'no')
                GEN.AFFECTED_LAYER(sigtmpneg, 'yes')
                self.contourizeFill(fill='no', twicecont='no', decompose='yes')
                GEN.FILTER_RESET()
                GEN.SEL_REF_FEAT(dot20, 'touch')
                if int(GEN.GET_SELECT_COUNT()) > 0:
                    GEN.SEL_REVERSE()
                    if int(GEN.GET_SELECT_COUNT()) > 0:
                        GEN.SEL_DELETE()
                GEN.SEL_COPY(sigtmppos)
                GEN.CLEAR_LAYER()

                GEN.AFFECTED_LAYER(dot20, 'yes')
                # 减小2mil
                GEN.SEL_RESIZE('-50.8')
                GEN.SEL_COPY(sigtmpneg, size='2.54', invert='yes')
                GEN.AFFECTED_LAYER(dot20, 'no')
                GEN.AFFECTED_LAYER(sigtmpneg, 'yes')
                self.contourizeFill(fill='no', twicecont='no', decompose='yes')
                GEN.SEL_COPY(sigtmppos, size='2.54', invert='yes')
                GEN.AFFECTED_LAYER(sigtmpneg, 'no')
                GEN.AFFECTED_LAYER(sigtmppos, 'yes')
                self.contourizeFill()
                # sigtmppos -- 得到挡点加大10mil后覆盖外层图形的部分
                GEN.FILTER_RESET()
                # NPTH孔距外层同不考虑防焊开窗的情况
                # GEN.SEL_REF_FEAT(smtmplayer,'touch')
                # if int(GEN.GET_SELECT_COUNT()) > 0:
                #     GEN.SEL_DELETE()
                GEN.SEL_REVERSE()
                if int(GEN.GET_SELECT_COUNT()) > 0:
                    GEN.SEL_COPY(mdlayer, size='508', invert='yes')
                # 删除无用层
                GEN.DELETE_LAYER(dot20)
                GEN.DELETE_LAYER(sigtmpneg)
                GEN.DELETE_LAYER(sigtmppos)


    def contourizeFill(self, fill='yes', twicecont='yes', decompose='yes'):
        """
        unit in mm
        :param fill:
        :param twicecont:
        :param decompose:
        :return:
        """
        GEN.COM('sel_contourize,accuracy=0,break_to_islands=no,clean_hole_size=3,clean_hole_mode=x_or_y')
        if fill == 'yes':
            GEN.COM('fill_params, type=solid, origin_type=datum, solid_type=fill, std_type=line, min_brush=35,'
                    'use_arcs=yes, symbol=, dx=2.54, dy=2.54, std_angle=45, std_line_width=254, std_step_dist=1270,'
                    'std_indent=odd, break_partial=yes, cut_prims=no, outline_draw=no, outline_width=0,'
                    'outline_invert=no')
            GEN.COM('sel_fill')
        if twicecont == 'yes':
            GEN.COM('sel_contourize,accuracy=0,break_to_islands=no,clean_hole_size=3,clean_hole_mode=x_or_y')
        if decompose == 'yes':
            GEN.COM('sel_decompose, overlap = yes')


    def sel_isolate_slot(self, iplayer, oplayer):
        """
        选出独立槽孔
        :param iplayer: 需要处理的层别
        :param oplayer: 不满足条件的参槽孔的返回层，此层别应已存在
        :return:
        """
        tmplayer1 = '__isoslotcu++__'  # 用于整体化的层别
        tmplayer2 = '__orginput++__'  # 用于存储原始的层别
        GEN.DELETE_LAYER(tmplayer1)
        GEN.DELETE_LAYER(tmplayer2)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(iplayer, 'yes')
        GEN.SEL_COPY(tmplayer1)
        GEN.SEL_MOVE(tmplayer2)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(tmplayer1, 'yes')
        GEN.SEL_CONTOURIZE()
        GEN.SEL_RESIZE('-1')
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(tmplayer2, 'yes')
        GEN.FILTER_RESET()
        GEN.COM('filter_atr_reset')
        GEN.SEL_REF_FEAT(tmplayer1, 'include')
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.SEL_MOVE(iplayer)
        # === 本层剩余的物件移动到需要处理的铝片层 ===
        GEN.SEL_MOVE(oplayer)
        GEN.DELETE_LAYER(tmplayer1)
        GEN.DELETE_LAYER(tmplayer2)


    def get_line_two_side(self, deal_layer):
        """
        使线保留两端端点，直接处理传入层
        :param deal_layer:
        :return:
        """
        tmplayer1 = '__tmp1__'  # 用于整体化的层别
        tmplayer2 = '__tmp2__'  # 用于存储原始的层别
        GEN.DELETE_LAYER(tmplayer1)
        GEN.DELETE_LAYER(tmplayer2)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(deal_layer, 'yes')
        GEN.SEL_COPY(tmplayer1)
        GEN.SEL_MOVE(tmplayer2)
        GEN.FILTER_RESET()
        GEN.COM('filter_atr_reset')
        gSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, tmplayer1))
        symlist = [i for i in gSym["gSYMS_HISTsymbol"]]
        for i in symlist:
            chg_size = i.strip('r')
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER(tmplayer1, 'yes')
            GEN.FILTER_RESET()
            GEN.FILTER_SET_INCLUDE_SYMS(i)
            GEN.FILTER_SELECT()
            if int(GEN.GET_SELECT_COUNT()) <= 0:
                M = M_Box()
                showText = M.msgText(u'提示', u"Error019:挡点制作过程中，未能正确处理独立槽!", showcolor='green')
                M.msgBox(showText)
                return False
            GEN.COM("sel_extend_slots, mode=ext_to, size=%s,from=end" % chg_size)
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER(tmplayer2, 'yes')
            GEN.FILTER_RESET()
            GEN.FILTER_SET_INCLUDE_SYMS(i)
            GEN.FILTER_SELECT()
            if int(GEN.GET_SELECT_COUNT()) <= 0:
                M = M_Box()
                showText = M.msgText(u'提示', u"Error020:挡点制作过程中，未能正确处理独立槽!", showcolor='green')
                M.msgBox(showText)
                return False
            GEN.COM("sel_extend_slots,mode=ext_to,size=%s,from=start" % chg_size)
            GEN.CLEAR_LAYER()
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(tmplayer1, 'yes')
        GEN.AFFECTED_LAYER(tmplayer2, 'yes')
        # === 添加属性，备查 ===
        GEN.COM('cur_atr_reset')
        GEN.COM('cur_atr_set, attribute=.bit, text=%s' % 'slot_point')
        GEN.COM('sel_change_atr, mode=add')
        GEN.COM('cur_atr_reset')
        GEN.SEL_COPY(deal_layer)
        GEN.DELETE_LAYER(tmplayer1)
        GEN.DELETE_LAYER(tmplayer2)


    def deal_control_depth_drill(self):
        """
        用于处理控深钻孔的挡点，包含层别cdc，cds。可能合并了通孔钻带
        :return:
        """
        cdYN = 'no'
        tmpdrl = '__control_depth_drl__'
        GEN.CLEAR_LAYER()
        if GEN.LAYER_EXISTS('cdc', job=self.job_name, step=self.step_name) == 'yes':
            cdYN = 'yes'
            GEN.AFFECTED_LAYER('cdc', 'yes')
        if GEN.LAYER_EXISTS('cds', job=self.job_name, step=self.step_name) == 'yes':
            cdYN = 'yes'
            GEN.AFFECTED_LAYER('cds', 'yes')

        ctmpdrl = '__ctmpdrl__'
        stmpdrl = '__stmpdrl__'
        GEN.DELETE_LAYER(ctmpdrl)
        GEN.DELETE_LAYER(stmpdrl)
        BackdrlDepth = self.getBackDrillDepth()
        GEN.SEL_COPY(tmpdrl)


    def main_run(self):
        # === 2021.04.13 cdc.cds增加挡点 ===
        cddotStatus = self.dealwithcontroldepthdrill()
        dotStatus = False
        # 挡点引导
        if cddotStatus:
            dotStatus = self.make_dot()

        if dotStatus:
            pre_step = self.step_name
            # M = M_Box ()
            # showText = M.msgText (u'提示', u"程序运行完成，请检查!", showcolor='green')
            # M.msgBox (showText)
            # 继续运行set挡点引导
            if self.step_name != 'set' and GEN.STEP_EXISTS(job=self.job_name, step='set') == 'yes':
                self.step_name = 'set'
                GEN.COM('editor_page_close')
                GEN.COM('open_entity,job=%s,type=step,name=%s,iconic=no' % (self.job_name, self.step_name))
                GEN.AUX('set_group, group=%s' % GEN.COMANS)

                M = M_Box()
                showText = M.msgText(u'提示', u"%s 运行完成，set step存在，程序现在运行set挡点!" % pre_step, showcolor='green')
                M.msgBox(showText)
                # === 2021.04.13 cdc.cds增加挡点 ===
                cddotStatus = self.dealwithcontroldepthdrill()
                dotsetStatus = False
                if cddotStatus:
                    dotsetStatus = self.make_dot()
                if dotsetStatus:
                    M = M_Box()
                    showText = M.msgText(u'程序运行完成，请检查!', u"%s" % '\n'.join(self.info_mess), showcolor='green')
                    M.msgBox(showText)
                else:
                    M = M_Box()
                    showText = M.msgText(u'提示', u"程序运行过程中有异常抛出，程序退出!", showcolor='red')
                    M.msgBox(showText)
        else:
            M = M_Box()
            showText = M.msgText(u'提示', u"程序运行过程中有异常抛出，程序退出!", showcolor='red')
            M.msgBox(showText)

        self.close()
        exit(0)


    def dealwithcontroldepthdrill(self):
        inplanBkDrlData = self.getBackDrillDepth()
        # print json.dumps (inplanBkDrlData, sort_keys=True, indent=2, separators=(',', ': '))
        drillDepthDic = self.redealWithInplanData(inplanBkDrlData)

        tmpdrl = '__tmp_drl__'
        GEN.DELETE_LAYER(tmpdrl)

        for cd_layer in ['cdc', 'cds']:
            # === tmp_cd_drl 会用于make_dot 主程序中 ===
            tmp_cd_drl = ''
            start_layer = ''

            if cd_layer == 'cdc':
                tmp_cd_drl = '__tmpcdc__'
                start_layer = '1'
            elif cd_layer == 'cds':
                tmp_cd_drl = '__tmpcds__'
                start_layer = str(self.layer_num)

            GEN.DELETE_LAYER(tmp_cd_drl)

            # print json.dumps (drillDepthDic, sort_keys=True, indent=2, separators=(',', ': '))
            # === 判断cdc，cds层别是否存在 === 如果存在根据孔径分层 ===
            if GEN.LAYER_EXISTS(cd_layer, job=self.job_name, step=self.step_name) == 'yes':
                GEN.CLEAR_LAYER()
                gSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, cd_layer))
                symlist = [str(self.stringtonum(i.strip('r'))) for i in gSym["gSYMS_HISTsymbol"]]
                GEN.AFFECTED_LAYER(cd_layer, 'yes')
                GEN.SEL_COPY(tmp_cd_drl)
                GEN.CLEAR_LAYER()
                GEN.CHANGE_UNITS('mm')
                for hsize in symlist:
                    if hsize not in drillDepthDic[start_layer]:
                        M = M_Box()
                        showText = M.msgText(u'提示', u"Error301:%s 钻带中的%s,未能匹配到inplan中的钻孔深度!" % (cd_layer, hsize),
                                             showcolor='green')
                        M.msgBox(showText)
                        return False
                    else:
                        if drillDepthDic[start_layer][hsize]['iDepth'] == 0:
                            GEN.CLEAR_LAYER()
                            GEN.AFFECTED_LAYER(tmp_cd_drl, 'yes')
                            GEN.FILTER_RESET()
                            GEN.FILTER_SET_INCLUDE_SYMS('r' + hsize)
                            GEN.FILTER_SELECT()

                            if int(GEN.GET_SELECT_COUNT()) <= 0:
                                M = M_Box()
                                showText = M.msgText(u'提示', u"Error302:挡点制作过程中，未能正确处理%s层别的钻孔!" % cd_layer,
                                                     showcolor='green')
                                M.msgBox(showText)
                                return False
                            else:
                                self.mvhole_currentLayer(tmp_cd_drl, 0, tmpdrl, attr='%s_drl' % cd_layer)
                                GEN.CLEAR_LAYER()
                        elif drillDepthDic[start_layer][hsize]['iDepth'] == 'NotSingleDrlDepth':
                            M = M_Box()
                            showText = M.msgText(u'提示', u"Error303:挡点制作过程中，层别：%s的钻孔：%s未能匹配到单一深度!" % (cd_layer, hsize),
                                                 showcolor='green')
                            M.msgBox(showText)
                            return False
                gSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, tmp_cd_drl))
                symlist = [str(self.stringtonum(i.strip('r'))) for i in gSym["gSYMS_HISTsymbol"]]
                if len(symlist) == 0:
                    GEN.DELETE_LAYER(tmp_cd_drl)
        return True


    def getBackDrillDepth(self):
        dbc_o = self.DB_O.DB_CONNECT("172.20.218.193", "inmind.fls", '1521', 'GETDATA', 'InplanAdmin')

        sql = """select a.item_name job_name_,
                   c.item_name layer_name_,
                    decode(d.drill_technology,1,'Controll Depth',5,'Countersink',6,'Counterbore',7,'Backdrill') as drill_type,
                    f.name tnum,
                    ROUND(f.finished_size/39.37,4) as finished_size,
                    ROUND(f.actual_drill_size/39.37,4) as actual_drill_size,
                    decode(f.type,4,'Plated Slot',0,'PTH',1,'Via',2,'NPTH',3,'Micro Via',5,'Non-Plated Slot') as hole_type,
                    ROUND(g.BACK_DRILL_FOR_THROUGH_HOLE_/39.37,4) as BKDRL_THROUGH_HOLE_,
                    g.DRILL_TOL_,
                    ROUND(e.VONDER_DRILL_DEPTH_/39.37,4) as VONDER_DRL_DEPTH_,
                    d.start_index,
                    e.non_drill_layer_,
                    d.end_index,
                    ROUND(e.cus_drill_depth_/39.37,4) as cus_drill_depth_,
                    ROUND(e.stub_drill_depth_/39.37,4) as stub_drill_depth_,
                    f.pcb_count,
                    g.hole_qty_,
                    --g.drill_notes_
                    g.erp_finish_size_
            from vgt_hdi.items a
                 inner join vgt_hdi.job b
                 on a.item_id = b.item_id
                and  a.last_checked_in_rev = b.revision_id
                 inner join vgt_hdi.items c
                 on a.root_id = c.root_id
                 inner join vgt_hdi.drill_program d
                 on c.item_id = d.item_id 
                and c.last_checked_in_rev = d.revision_id
                 inner join vgt_hdi.drill_program_da e
                 on d.item_id = e.item_id 
                and d.revision_id = e.revision_id
                 inner join vgt_hdi.drill_hole f
                 on d.item_id = f.item_id 
                and d.revision_id = f.revision_id
                 inner join vgt_hdi.drill_hole_da g
                 on f.item_id = g.item_id 
                and f.revision_id = g.revision_id
                and f.sequential_index=g.sequential_index
                where  d.drill_technology in (1,5,6,7) and a.item_name = '%s'
               order by c.item_name,f.name""" % self.job_name.upper()[:13]

        # 1 为存在，0为不存在
        dataval = self.DB_O.SELECT_DIC(dbc_o, sql)
        # print 'x' * 40
        # print json.dumps(dataval,indent=2)
        # print 'c' * 40
        if dbc_o:
            self.DB_O.DB_CLOSE(dbc_o)

        return dataval


    def redealWithInplanData(self, inplanData):
        # 模型
        # [
        #     {
        #         "ACTUAL_DRILL_SIZE": 0.5,
        #         "BKDRL_THROUGH_HOLE_": 0,
        #         "CUS_DRILL_DEPTH_": 1.1000000000000001,
        #         "DRILL_NOTES_": "\u63a7\u6df1\u6df1\u5ea6\u6d4b\u8bd5\u5b54",
        #         "DRILL_TOL_": "/",
        #         "DRILL_TYPE": "Controll Depth",
        #         "END_INDEX": 2,
        #         "FINISHED_SIZE": 0.5,
        #         "HOLE_QTY_": 2,
        #         "HOLE_TYPE": "NPTH",
        #         "JOB_NAME_": "H20504GI005A2",
        #         "LAYER_NAME_": "cd4-2",
        #         "NON_DRILL_LAYER_": 3,
        #         "PCB_COUNT": 0,
        #         "START_INDEX": 4,
        #         "STUB_DRILL_DEPTH_": 0,
        #         "TNUM": "T01",
        #         "VONDER_DRL_DEPTH_": 1.25
        #     }
        # ]
        # 有效键 TNUM "ACTUAL_DRILL_SIZE": 0.5,"DRILL_NOTES_" "VONDER_DRL_DEPTH_": 1.25
        # 不考虑排刀的情况下，以实际钻孔大小确认背钻的深度。以钻孔孔径为key 内容为深度，出现次数
        # 20200423 根据周涌提供的规则，当备注栏里出现了以下字样，认为为通孔
        # 印刷对位孔-通孔，限位孔-通孔，工艺边上孔-通孔，控深漏钻检测孔-通孔；料号孔-通孔，批号孔-通孔
        # === 2020.06.09 增加 背钻可视孔 ===
        drillDepthDic = {}
        for i in range(len(inplanData)):
            change_depth = ''
            drill_start_lay = str(inplanData[i]['START_INDEX'])
            if drill_start_lay not in drillDepthDic:
                drillDepthDic[drill_start_lay] = {}
            drillSize = round(inplanData[i]['ACTUAL_DRILL_SIZE'], 3)
            through_note = ['曝光对位孔', '印刷对位孔', '限位孔', '工艺边上孔', '控深漏钻检测孔', '控深漏钻监测孔',
                            '料号孔', '批号孔', '工艺边定位孔', '背钻漏钻监测孔', '背钻可视孔', 'HCT coupon定位孔',
                            '料号孔和批号孔', '通孔HCT定位', '通孔']
            if inplanData[i]['ERP_FINISH_SIZE_']:
                through_list = [t for t in through_note if t in inplanData[i]['ERP_FINISH_SIZE_']]
                if len(through_list) != 0:
                    change_depth = 0

            # 更改限位孔ERP尺寸为0.45，对应钻带为0.452,料号孔ERP尺寸为0.45，对应钻带为0.452，批号孔ERP尺寸为0.45，对应钻带为0.46
            if abs(drillSize - 0.45) < 0.0001 and inplanData[i]['ERP_FINISH_SIZE_'] == '限位孔':
                drillSize = 0.452
            if abs(drillSize - 0.45) < 0.0001 and inplanData[i]['ERP_FINISH_SIZE_'] == '料号孔':
                drillSize = 0.452
            if abs(drillSize - 0.45) < 0.0001 and inplanData[i]['ERP_FINISH_SIZE_'] == '批号孔':
                drillSize = 0.46
            # === 2020.01.08 增加料号孔和批号孔合刀的情况 ===
            if abs(drillSize - 0.45) < 0.0001 and inplanData[i]['ERP_FINISH_SIZE_'] == '料号孔和批号孔':
                drillSize = 0.46
            # ==2020.04.28 Song==
            # 增加控深深度测试孔的深度添加判断，当备注信息为控深深度测试孔，在inplan的钻咀信息的钻径大小上减0.001
            if inplanData[i]['ERP_FINISH_SIZE_'] == '控深深度测试孔' \
                    or inplanData[i]['ERP_FINISH_SIZE_'] == '背钻深度测试孔' \
                    or inplanData[i]['ERP_FINISH_SIZE_'] == '背钻对准测试孔':
                drillSize = drillSize - 0.001

            # === 更改为整数的symbol尺寸，便于后续匹配 ===
            drillSize = '%0.f' % (drillSize * 1000)
            drillSize = str(drillSize)

            if drillSize in drillDepthDic[drill_start_lay]:
                if change_depth != '':
                    if change_depth == drillDepthDic[drill_start_lay][drillSize]['iDepth']:
                        drillDepthDic[drill_start_lay][drillSize]['iTimes'] = drillDepthDic[drill_start_lay][drillSize][
                                                                                  'iTimes'] + 1
                    else:
                        drillDepthDic[drill_start_lay][drillSize]['iDepth'] = 'NotSingleDrlDepth'
                        drillDepthDic[drill_start_lay][drillSize]['iTimes'] = drillDepthDic[drill_start_lay][drillSize][
                                                                                  'iTimes'] + 1
                else:
                    if inplanData[i]['VONDER_DRL_DEPTH_'] == drillDepthDic[drill_start_lay][drillSize]['iDepth']:
                        drillDepthDic[drill_start_lay][drillSize]['iTimes'] = drillDepthDic[drill_start_lay][drillSize][
                                                                                  'iTimes'] + 1
                    else:
                        drillDepthDic[drill_start_lay][drillSize]['iDepth'] = 'NotSingleDrlDepth'
                        drillDepthDic[drill_start_lay][drillSize]['iTimes'] = drillDepthDic[drill_start_lay][drillSize][
                                                                                  'iTimes'] + 1
            else:
                drillDepthDic[drill_start_lay][drillSize] = {}
                if change_depth != '':
                    drillDepthDic[drill_start_lay][drillSize] = {'iDepth': change_depth, 'iTimes': 1}
                else:
                    drillDepthDic[drill_start_lay][drillSize] = {'iDepth': inplanData[i]['VONDER_DRL_DEPTH_'],
                                                                 'iTimes': 1}
            print json.dumps(drillDepthDic, indent=2)
        return drillDepthDic
        # {
        #     "6": {
        #         "0.452": {
        #             "iDepth": 0,
        #             "iTimes": 1
        #         },
        #         "0.46": {
        #             "iDepth": 0,
        #             "iTimes": 1
        #         },
        #         "0.699": {
        #             "iDepth": 1.3500000000000001,
        #             "iTimes": 1
        #         },
        #         "0.7": {
        #             "iDepth": 1.3500000000000001,
        #             "iTimes": 1
        #         },
        #     }
        # }


# # # # --程序入口
if __name__ == "__main__":
    # 名词解释：半塞孔即为单面塞孔
    app = QtGui.QApplication(sys.argv)
    myapp = MainWindowShow()
    myapp.show()
    app.exec_()
    sys.exit(0)

"""
版本：V1.0
更改为HDI一厂挡点制作

版本：V1.1
2020.07.08
宋超
1.NPTH挡点为缩开窗制作

版本：V1.2
2020.09.17
宋超
1.挡点规则更改，更改程序
2.槽孔挡点单独处理
2020.09.18
宋超
1.槽的挡点是两端延长

版本：V1.3
2020.09.24
1.考虑只有NPTH槽的情况,不存在npth孔的情形

版本：V1.4
2020.09.25
1.仅PTH槽适用于独立槽孔的挡点规则http://192.168.2.120:82/zentao/story-view-2106.html

版本：V1.5
2020.09.28
1.挡点使用tk.ykj进行挡点添加动作

版本：V1.5.1
2020.09.30
1.增加从inplan获取mic印章的语句，当有mic存在时，提醒人员手动处理

#版本 1.6.1 
2020-10-20 唐成 
1:（按照 story-view-2167，要求 ≤ 0.4加档点比防焊大时，缩小至比阻焊单边小1mil）

版本：V1.7
2020.12.10
宋超
1.增加单只跑完跑set 
http://192.168.2.120:82/zentao/story-view-2393.html 


版本：V1.8 测试版本
2021.04.13
唐成
1.增加 set npth 孔到铜10mil，不足减小档点
http://192.168.2.120:82/zentao/story-view-2871.html


版本：V1.9 测试版本
2021.04.14
宋超
1.cdc，cds加挡点；http://192.168.2.120:82/zentao/story-view-2870.html

版本：V2.0
2021.12.03
宋超
1.挡点运行时，处理NPTH孔开窗铜皮时，当辅助层别均为负极性，整体化不能消除负片，增加判断层别中是否均为负片，是则清空层别
Bug料号：S51502HN009B7

版本：V2.1
2022.03.01
宋超
http://192.168.2.120:82/zentao/story-view-4004.html
1.sz.lp不制作挡点
2.lp与sz.lp均不存在时弹出窗提醒


版本：V2.3
2022.07.01 转正日期 2022.07.05 16：40
宋超
http://192.168.2.120:82/zentao/story-view-4283.html
1.检测挡点距离小于5mil

2022.08.17  
song
#B81*044A1  === 可能存在料号中无NPTH也无小于0.510的pth，无dotdrl层别存在的情况

版本：V2.4
2022.11.21 转正日期 2022.11.23
宋超
http://192.168.2.120:82/zentao/story-view-4225.html
1.515系列两面铜厚不一致时，NPTH孔挡点的特殊处理方式
"""
