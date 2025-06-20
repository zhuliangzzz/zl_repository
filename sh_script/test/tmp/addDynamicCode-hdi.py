#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2020/04/01
# @Revision     :    2.0.0
# @File         :    addDynamicCode.py
# @Software     :    PyCharm
# @Usefor       :    用于添加料号中存在的所有动态码
# http://192.168.2.120:82/zentao/story-view-667.html
# 1.lot号， symbol名称为barcode长度值x高度值（单位：mm)，长高可随意调节大小，产线机台可根据实际MI指示变更lot号，属性：id=250
# 2.周期，symbol名称为barcode长度值x高度值（单位：mm)，
# 长高可随意调节大小，
# 属性:id=350/351/352 因周期较为常见，故将其固定属性如下：
# id=350   YYWW
# id=351   WWYY
# id=352   YYWWD
# 其他周期格式待定。
# 3.二维码，symbol名称为barcode长度值x高度值（单位：mm)，长高可随意调节大小，属性：id=360  二维码信息因客户需求信息不固定，
# 且产线机台输入难免会存在误差，所以暂时由工程提供白油块二维码，待日后商讨再做决定。
# 以上symbol的0点皆为左下角，且S面需镜像添加，角度可根据实际资料添加无限定。
# 版本V2.0 Chao.Song 2020.04.06
# 增加汉印序列号添加支持：
# panel中自助添加num260 symbol，属性out_flag=260，增加板角四个pad，大小2mil
# 根据添加的镜像关系，判断添加的是否镜像
# 判断添加层的r0对位点，如果数量不正确，删除并从外层copy，copy不成功时提醒
# 版本V2.1 Chao.Song 2020.04.27
# 增加劲鑫喷墨自定义二维码
# 版本V2.2 Chao.Song 2020.06.22
# 增加序列号 260
# 版本V3.0  Chao.Song 2020.08.10
# 增加升达康二维码添加
# 版本V3.1  Chao.Song 2020.09.27
# 镭雕二维码程序明码问题修复
# 版本V3.3  Chao.Song 2020.11.20
# 劲鑫喷墨增加F显示
# 版本V3.4  Chao.Song 2020.12.23
# 1.添加二维码时可选择手动选择光点
# 2.光点选择由随机更改为短边上的对位光点

# 版本V3.5  AresHe 2021.9.13
# 1.新增HDI、多层A86、A81等系列新属性参数
# 2.修复了bug,当选择喷墨类型时,不自动刷新ID参数问题

# 版本V3.6  Chao.Song 2021.10.28
# 1.增加奥宝类二维码，蚀刻二维码，明码，包装二维码，B74系列二维码

# 20241120 A86hdi不限制料号名  且barcode加上F
# ---------------------------------------------------------#


import sys
import os
import re
import json
import socket
dirname, filename = os.path.split (os.path.abspath (sys.argv[0]))

imgpath = dirname + '/img/'
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
import MainUIV7 as Mui

from PyQt4 import QtCore, QtGui
import platform

import string

if platform.system () == "Windows":
    sys.path.append (r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append (r"/incam/server/site_data/scripts/Package")

import genCOM_26

GEN = genCOM_26.GEN_COM ()

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QtGui.QApplication.translate (context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate (context, text, disambig)


class M_Box (QtGui.QMessageBox):
    """
    MesageBox提示界面
    """

    def __init__(self, parent=None):
        QtGui.QMessageBox.__init__ (self, parent)

    def msgBox_option(self, body, title=u'提示信息', msgType='information'):
        """
        可供提示选择的MessagesBox
        :param body:显示内容（支持html样式）
        :param title:标题
        :param msgType:显示类型（包括information, question, warning）QtGui.QMessageBox.ButtonMask 可查看所有
        :return:
        """
        msg = QtGui.QMessageBox.information (self, u"信息", body, QtGui.QMessageBox.Ok,
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
            QtGui.QMessageBox.information (self, title, body, u'确定')
        elif msgType == 'warning':
            QtGui.QMessageBox.warning (self, title, body, u'确定')
        elif msgType == 'question':
            QtGui.QMessageBox.question (self, title, body, u'确定')

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


class MainWindowShow (QtGui.QMainWindow):
    """
    窗体主方法
    """

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__ (self, parent)
        # 初始数据
        self.AppVer = '3.6'
        self.barcode_x = 5
        self.barcode_y = 5
        self.symbol_attr = 250
        self.add_angle = 0
        self.add_mir = 'no'
        self.attr_words = 'id'
        self.supply = 'jinxin'
        self.job_name = os.environ.get ('JOB')
        self.step_name = os.environ.get ('STEP')
        self.pnl_codex = 3
        self.pnl_codey = 12
        self.hostname = socket.gethostname()
        if self.job_name and self.step_name:
            pass
        else:
            M = M_Box ()
            showText = M.msgText (u'提示', u"必须打开料号及需添加的Step,程序退出!", showcolor='red')
            M.msgBox (showText)
            exit (0)
        self.barcode_symbol = 'barcode%sx%s' % (self.barcode_x, self.barcode_y)
        self.ui = Mui.Ui_MainWindow ()
        self.ui.setupUi (self)
        self.addUiDetail ()

    def addUiDetail(self):
        """
        在原框架基础上继续加载窗体
        :return:None
        """
        silk_layers = self.getLayerList ()
        self.ui.listWidget_layerlist.addItems (silk_layers)
        self.ui.listWidget_layerlist.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

        self.ui.label_attr.setText (
            _translate ("MainWindow", "属性id=%s" % (self.symbol_attr), None))
        #  长宽输入值的大小 保留个位数及小数
        my_regex = QtCore.QRegExp ("[1-9][0-9]?(\.\d{1,3})?")
        self.area = PainArea ()
        self.ui.gridLayout_4.addWidget (self.area, 2, 2, 3, 2)

        my_validator = QtGui.QRegExpValidator (my_regex, self.ui.lineEdit_width)
        self.ui.lineEdit_width.setValidator (my_validator)
        self.ui.lineEdit_width.setText (str (self.barcode_x))

        my_validator = QtGui.QRegExpValidator (my_regex, self.ui.lineEdit_length)
        self.ui.lineEdit_length.setValidator (my_validator)
        self.ui.lineEdit_length.setText (str (self.barcode_y))

        my_validator = QtGui.QRegExpValidator (my_regex, self.ui.lineEdit_ob2dbc)
        self.ui.lineEdit_ob2dbc.setValidator (my_validator)
        self.ui.lineEdit_length.setText (str (5))

        my_regex_abc = QtCore.QRegExp ("[\$WYMD]{1,12}")
        my_validator = QtGui.QRegExpValidator (my_regex_abc, self.ui.bz_other_date)
        self.ui.bz_other_date.setValidator (my_validator)
        # self.ui.bz_other_date.setText (str (5))

        # 隐藏panel添加frame
        self.ui.frame_pnl.hide ()
        # === 二维码白油块设置输入限制
        # === 明码白油块 1.5x10
        my_regex = QtCore.QRegExp ("[1-9][0-9]?(\.\d+)?x[1-9][0-9]?(\.\d+)?")
        my_validator = QtGui.QRegExpValidator (my_regex, self.ui.lineEdit_mm_by)
        self.ui.lineEdit_mm_by.setValidator (my_validator)
        my_regex = QtCore.QRegExp ("[1-9][0-9]?(\.\d+)?")
        my_validator = QtGui.QRegExpValidator (my_regex, self.ui.lineEdit_2dbc_by)
        self.ui.lineEdit_2dbc_by.setValidator (my_validator)
        my_validator = QtGui.QRegExpValidator (my_regex, self.ui.lineEdit_mmlength)
        self.ui.lineEdit_mmlength.setValidator (my_validator)
        my_regex = QtCore.QRegExp ("[1-9][0-9]?(\.\d+)?|0\.\d+")
        my_validator = QtGui.QRegExpValidator (my_regex, self.ui.lineEdit_mmheight)
        self.ui.lineEdit_mmheight.setValidator (my_validator)

        # === 隐藏明码添加groupBox
        self.ui.groupBox_mm.hide ()
        # === 隐藏奥宝类groupBox 包装周期界面不可编辑状态，直接在ui中设定为False信号和槽不生效，故在此处设定
        self.ui.widget_bzdate.setEnabled(False)
        self.ui.label_dateformat.setVisible(False)
        self.ui.comboBox_date.setVisible(False)
        self.ui.groupBox_ob.hide()
        self.resize(350,450)

        self.ui.label_bottom.setText (
            _translate ("MainWindow", "版权所有：胜宏科技 版本：%s" % (self.AppVer), None))
        self.ui.lineEdit_width.textChanged.connect (self.Change_draw)
        self.ui.lineEdit_length.textChanged.connect (self.Change_draw)
        self.ui.lineEdit_freeangle.textChanged.connect (self.Change_draw)
        # === 2020.11.20 更改信号，为editing Finished 体验并不好 returnPressed 有无法更新的情况出现
        # self.ui.lineEdit_width.returnPressed.connect(self.Change_draw)
        # self.ui.lineEdit_length.returnPressed.connect(self.Change_draw)
        QtCore.QObject.connect(self.ui.radioButton_b74, QtCore.SIGNAL("clicked(bool)"),  self.baozhuang_ui)
        QtCore.QObject.connect(self.ui.radioButton_normal, QtCore.SIGNAL("clicked(bool)"),  self.baozhuang_ui)
        QtCore.QObject.connect(self.ui.checkBox_obmm, QtCore.SIGNAL("clicked(bool)"),  self.etch_ui)
        QtCore.QObject.connect(self.ui.checkBox_ob2dbc, QtCore.SIGNAL("clicked(bool)"),  self.etch_ui)
        QtCore.QObject.connect(self.ui.checkBox_baozhuang, QtCore.SIGNAL("clicked(bool)"),  self.etch_ui)

        self.ui.label_tips.setText (
            _translate ("MainWindow", "Tips:Symbol名称barcode%sx%s" % (self.barcode_x, self.barcode_y), None))
        QtCore.QObject.connect(self.ui.comboBox_mode, QtCore.SIGNAL("currentIndexChanged(int)"), self.Change_attr)
        QtCore.QObject.connect(self.ui.comboBox_date, QtCore.SIGNAL("currentIndexChanged(int)"), self.Change_attr)
        QtCore.QObject.connect(self.ui.comboBox_bz_date, QtCore.SIGNAL("currentIndexChanged(int)"), self.change_baozhuang)

        QtCore.QObject.connect(self.ui.comboBox_angle, QtCore.SIGNAL("currentIndexChanged(int)"), self.Change_draw)
        QtCore.QObject.connect(self.ui.comboBox_mirror, QtCore.SIGNAL("currentIndexChanged(int)"), self.Change_draw)
        QtCore.QObject.connect(self.ui.comboBox_supply, QtCore.SIGNAL("currentIndexChanged(int)"), self.change_supply)

        QtCore.QObject.connect(self.ui.pushButton_apply, QtCore.SIGNAL("clicked()"), self.main_run)

    def stringtonum(self, instr):
        """
        转换字符串为数字优先转换为整数，不成功则转换为浮点数
        :param instr:
        :return:
        """
        try:
            num = string.atoi (instr)
            return num
        except (ValueError, TypeError):
            try:
                num = string.atof (instr)
                return num
            except ValueError:
                return False

    def baozhuang_ui(self):
        cus_name = self.job_name[1:4]
        if cus_name in ['b74'] and self.ui.radioButton_normal.isChecked():
            M = M_Box ()
            showText = M.msgText (u'警告', u"b74系列不可勾选普通二维码，返回界面!",showcolor='red')
            M.msgBox (showText)
            self.ui.radioButton_b74.animateClick()
            return
        if cus_name not in ['b74'] and self.ui.radioButton_b74.isChecked():
            M = M_Box ()
            showText = M.msgText (u'警告', u"不是b74系列，勾选了b74!",showcolor='red')
            M.msgBox (showText)
        if self.ui.radioButton_b74.isChecked():
            self.ui.widget_etch_side.setEnabled(True)
            self.ui.widget_cu_thick.setEnabled(False)
            self.ui.widget_cu_thick.setEnabled(True)
            if self.ui.checkBox_baozhuang.isChecked():
                self.ui.checkBox_baozhuang.setChecked(False)
                self.ui.widget_bzlayer.setEnabled(False)
                self.ui.widget_bzside.setEnabled(False)
                self.ui.widget_bzdate.setEnabled(False)

    def etch_ui(self):
        if self.ui.checkBox_obmm.isChecked() or self.ui.checkBox_ob2dbc.isChecked():
            self.ui.widget_etch_side.setEnabled(True)
        elif not self.ui.checkBox_obmm.isChecked() and not self.ui.checkBox_ob2dbc.isChecked():
            self.ui.widget_etch_side.setEnabled(False)
            self.ui.checkBox_icg.setChecked(False)
            self.ui.checkBox_edit.setChecked(False)

        if self.ui.checkBox_baozhuang.isChecked():
            self.ui.checkBox_set.setChecked(True)

        if not self.ui.checkBox_obmm.isChecked () and not self.ui.checkBox_ob2dbc.isChecked ():
            self.ui.checkBox_icg.setChecked(False)
            self.ui.checkBox_edit.setChecked(False)

    def change_baozhuang(self):
        if self.ui.comboBox_bz_date.currentText() == u'其他':
            self.ui.bz_other_date.setEnabled(True)
        else:
            self.ui.bz_other_date.setEnabled(False)

    def Change_draw(self):
        # Barcode的小数点问题barcode5x5和barcode5.0x5.0 使用stringtonum函数解决
        gwidth = self.stringtonum (str (self.ui.lineEdit_width.text ()))
        if not gwidth:
            gwidth = 5
        glength = self.stringtonum (str (self.ui.lineEdit_length.text ()))
        if not glength:
            glength = 5
        factor1 = 1
        factor2 = 1
        # print 'gwidth:%s,glength:%s' % (gwidth,glength)
        if gwidth and glength:
            factor1 = float (gwidth) / float (glength)

        if self.ui.comboBox_mirror.currentText () == u'是':
            self.add_mir = 'yes'
        elif self.ui.comboBox_mirror.currentText () == u'否':
            self.add_mir = 'no'

        # self.add_angle = ''
        if self.ui.comboBox_angle.currentText () == u'其他':
            self.ui.lineEdit_freeangle.setEnabled (True)
            try:
                self.add_angle = float (self.ui.lineEdit_freeangle.text ())
            except ValueError:
                return
        elif str (self.ui.comboBox_angle.currentText ()) == '0':
            self.add_angle = 0
            self.ui.lineEdit_freeangle.setEnabled (False)
        elif str (self.ui.comboBox_angle.currentText ()) == '90':
            self.add_angle = 90
            self.ui.lineEdit_freeangle.setEnabled (False)
        elif str (self.ui.comboBox_angle.currentText ()) == '180':
            self.add_angle = 180
            self.ui.lineEdit_freeangle.setEnabled (False)
        elif str (self.ui.comboBox_angle.currentText ()) == '270':
            self.add_angle = 270
            self.ui.lineEdit_freeangle.setEnabled (False)
        ui_angle = self.add_angle
        if self.add_mir == 'yes':
            ui_angle = self.add_angle * (-1)
        self.area.setMir (self.add_mir)
        self.barcode_x = glength
        self.barcode_y = gwidth
        self.barcode_symbol = 'barcode%sx%s' % (self.barcode_x, self.barcode_y)

        if self.ui.comboBox_supply.currentText () == u'劲鑫喷墨':
            self.supply = 'jinxin'
            self.attr_words = 'id'
            self.barcode_symbol = 'barcode%sx%s' % (self.barcode_x, self.barcode_y)

            self.Change_tips ()
            self.resize (350, 450)
            self.update()

        elif self.ui.comboBox_supply.currentText () == u'汉印喷墨':
            self.supply = 'hanyin'
            self.attr_words = '.out_flag'
            self.barcode_symbol = 'num_250'

            self.Change_tips ()
            self.resize (350, 500)
            self.update()

        elif self.ui.comboBox_supply.currentText () == u'升达康镭雕':
            self.supply = 'shengdakang'
            self.attr_words = '.string'
            if self.barcode_x != self.barcode_y:
                M = M_Box ()
                showText = M.msgText (u'警告', u"升达康镭雕二维码长高不一致，跳过!")
                M.msgBox (showText)
                self.ui.comboBox_mode.setCurrentIndex (0)
                self.barcode_symbol = 'None'
            else:
                self.barcode_symbol = '2dbc_%smm' % self.barcode_x

        elif self.ui.comboBox_supply.currentText () == u'A86文字喷墨(MLB)':
            self.supply = 'a86silk_mlb'
            self.attr_words = '.out_flag'
            self.barcode_symbol = 'barcode%sx%s' % (self.barcode_x, self.barcode_y)

            self.Change_tips()
            self.resize(350, 450)
            self.update()

        elif self.ui.comboBox_supply.currentText () == u'A86文字喷墨(HDI)':
            self.supply = 'a86silk_hdi'
            # self.attr_words = '.out_flag'
            self.attr_words = 'id'
            self.barcode_symbol = 'barcode%sx%s' % (self.barcode_x, self.barcode_y)

            self.Change_tips()
            self.resize(350, 450)
            self.update()

        elif self.ui.comboBox_supply.currentText () == u'A81文字喷墨(HDI)':
            self.supply = 'a81silk_hdi'
            # self.attr_words = '.out_flag'
            self.attr_words = 'id'
            self.barcode_symbol = 'barcode%sx%s' % (self.barcode_x, self.barcode_y)

            self.Change_tips()
            self.resize(350, 450)
            self.update()

        # 添加的内容角度，Genesis和InCAM对比角度，显示角度值不同，但与界面相同
        self.area.setRotate (ui_angle)
        self.area.setScale (factor2, factor1)
        self.Change_tips ()

    def change_supply(self):
        if self.ui.comboBox_supply.currentText () == u'奥宝':
            self.ui.frame_pnl.hide ()
            self.ui.groupBox_mm.hide()
            self.ui.frame_3.hide()
            self.ui.frame_2.hide()
            self.supply = 'aobao'
            self.ui.groupBox_ob.show()
            self.Change_tips()
            self.resize (350, 330)
            self.update ()
        else:
            self.ui.frame_3.show()
            self.ui.groupBox_ob.hide()
            self.ui.frame_2.show()

        if self.ui.comboBox_supply.currentText () == u'劲鑫喷墨':
            self.supply = 'jinxin'
            self.attr_words = 'id'
            self.ui.frame_pnl.hide ()
            self.ui.groupBox_mm.hide()
            add_types = ["序列号", "序列号2", "周期", "二维码"]
            self.ui.comboBox_mode.clear ()
            for addi in range(len(add_types)):
                self.ui.comboBox_mode.addItem (_fromUtf8 (""))
                self.ui.comboBox_mode.setItemText (addi, _translate ("MainWindow", add_types[addi], None))
            self.Change_tips ()
            self.resize (350, 450)
            self.update()

        elif self.ui.comboBox_supply.currentText () == u'汉印喷墨':
            self.supply = 'hanyin'
            self.attr_words = '.out_flag'
            add_types = ["序列号"]
            self.ui.comboBox_mode.clear ()
            self.ui.groupBox_mm.hide()

            for addi in range(len(add_types)):
                self.ui.comboBox_mode.addItem (_fromUtf8 (""))
                self.ui.comboBox_mode.setItemText (addi, _translate ("MainWindow", add_types[addi], None))
            self.ui.comboBox_mode.setCurrentIndex (0)
            self.ui.frame_pnl.show ()
            self.Change_tips ()
            self.resize (350, 500)
            self.update()

        elif self.ui.comboBox_supply.currentText () == u'升达康镭雕':
            self.supply = 'shengdakang'
            self.attr_words = '.string'
            add_types = ["二维码", "明码", "二维码及明码"]
            self.ui.comboBox_mode.clear ()
            for addi in range(len(add_types)):
                self.ui.comboBox_mode.addItem (_fromUtf8 (""))
                self.ui.comboBox_mode.setItemText (addi, _translate ("MainWindow", add_types[addi], None))
            self.ui.comboBox_mode.setCurrentIndex (0)
            self.ui.groupBox_mm.show()
            if self.barcode_x != self.barcode_y:
                M = M_Box ()
                showText = M.msgText (u'警告', u"升达康镭雕二维码长高不一致，跳过!")
                M.msgBox (showText)
                self.ui.comboBox_mode.setCurrentIndex (0)
                self.barcode_symbol = 'None'
            else:
                self.barcode_symbol = '2dbc_%smm' % self.barcode_x
            self.shengdakanguichange()
            self.ui.frame_pnl.show ()
            self.Change_tips ()
            self.resize (350, 580)
            self.update()

        elif self.ui.comboBox_supply.currentText () == u'A86文字喷墨(MLB)':
            self.supply = 'a86silk_mlb'
            self.attr_words = '.out_flag'
            self.ui.frame_pnl.hide ()
            self.ui.groupBox_mm.hide()
            add_types = ["二维码","序列号"]
            self.ui.comboBox_mode.clear ()
            for addi in range(len(add_types)):
                self.ui.comboBox_mode.addItem (_fromUtf8 (""))
                self.ui.comboBox_mode.setItemText (addi, _translate ("MainWindow", add_types[addi], None))
            self.Change_tips ()
            self.resize (350, 450)
            self.update()

        elif self.ui.comboBox_supply.currentText () == u'A86文字喷墨(HDI)':
            self.supply = 'a86silk_hdi'
            # self.attr_words = '.out_flag'
            self.attr_words = 'id'
            self.ui.frame_pnl.hide ()
            self.ui.groupBox_mm.hide()
            add_types = ["二维码","序列号"]
            self.ui.comboBox_mode.clear ()
            for addi in range(len(add_types)):
                self.ui.comboBox_mode.addItem (_fromUtf8 (""))
                self.ui.comboBox_mode.setItemText (addi, _translate ("MainWindow", add_types[addi], None))
            self.Change_tips ()
            self.resize (350, 450)
            self.update()

        elif self.ui.comboBox_supply.currentText () == u'A81文字喷墨(HDI)':
            self.supply = 'a81silk_hdi'
            # self.attr_words = '.out_flag'
            self.attr_words = 'id'
            self.ui.frame_pnl.hide ()
            self.ui.groupBox_mm.hide()
            add_types = ["二维码","序列号"]
            self.ui.comboBox_mode.clear ()
            for addi in range(len(add_types)):
                self.ui.comboBox_mode.addItem (_fromUtf8 (""))
                self.ui.comboBox_mode.setItemText (addi, _translate ("MainWindow", add_types[addi], None))
            self.Change_tips ()
            self.resize (350, 450)
            self.update()

        # === 2021.10.25 Song 新增奥宝类型，不做界面刷新
        if self.ui.comboBox_supply.currentText () != u'奥宝':
            # --改变喷墨类型时,自动刷新其他参数    AresHe 2021.9.13
            self.Change_attr()
            self.Change_draw()

    def Change_attr(self):
        self.resize (354, 450)
        if self.supply == 'hanyin':
            # if self.ui.comboBox_mode.currentText () == u'周期' or self.ui.comboBox_mode.currentText () == u'二维码':
            if self.ui.comboBox_mode.currentText () != u'序列号' :
                M = M_Box ()
                showText = M.msgText (u'警告', u"汉印喷墨暂不可选择周期、二维码，跳过!")
                M.msgBox (showText)
                self.ui.comboBox_mode.setCurrentIndex (0)

        if self.ui.comboBox_mode.currentText () == u'周期':
            self.ui.comboBox_date.setEnabled (True)
            self.ui.comboBox_date.setVisible(True)
            self.ui.label_dateformat.setVisible(True)
            self.Change_window_length(5,5)
        elif self.ui.comboBox_mode.currentText () == u'序列号':
            # self.ui.comboBox_date.setEnabled (False)
            self.ui.comboBox_date.setVisible(False)
            self.ui.label_dateformat.setVisible(False)
            self.symbol_attr = 250

            # --当选择A86、A81系列时,序列号宽为3,高为1   AresHe 2021.9.13
            if self.ui.comboBox_supply.currentText() == u'A86文字喷墨(MLB)':
                self.Change_window_length(1,3)
            elif self.ui.comboBox_supply.currentText() == u'A86文字喷墨(HDI)':
                self.Change_window_length(1,3)
            elif self.ui.comboBox_supply.currentText() == u'A81文字喷墨(HDI)':
                self.Change_window_length(1,3)
            else:
                self.Change_window_length(5,5)

        elif self.ui.comboBox_mode.currentText () == u'序列号2':
            # self.ui.comboBox_date.setEnabled (False)
            self.ui.comboBox_date.setVisible(False)
            self.ui.label_dateformat.setVisible(False)
            self.symbol_attr = 260
            self.Change_window_length(5,5)
        elif self.ui.comboBox_mode.currentText () == u'二维码':
            # self.ui.comboBox_date.setEnabled (False)
            self.ui.comboBox_date.setVisible(False)
            self.ui.label_dateformat.setVisible(False)
            self.symbol_attr = 360
            self.Change_window_length(5,5)

            # --新增多层、HDI A86、A81系列属性    AresHe 2021.9.13
            if self.ui.comboBox_supply.currentText () == u'A86文字喷墨(MLB)':
                # self.ui.comboBox_date.setEnabled(False)
                self.ui.comboBox_date.setVisible(False)
                self.ui.label_dateformat.setVisible(False)
                self.symbol_attr = 350
            elif self.ui.comboBox_supply.currentText() == u'A86文字喷墨(HDI)':
                # self.ui.comboBox_date.setEnabled(False)
                self.ui.comboBox_date.setVisible(False)
                self.ui.label_dateformat.setVisible(False)
                self.symbol_attr = 400
            elif self.ui.comboBox_supply.currentText() == u'A81文字喷墨(HDI)':
                # self.ui.comboBox_date.setEnabled(False)
                self.ui.comboBox_date.setVisible(False)
                self.ui.label_dateformat.setVisible(False)
                self.symbol_attr = 500

        # === 增加升达康镭雕二维码的分类，升达康与以上规则不相同
        if self.supply == 'shengdakang':
            self.symbol_attr = '2dmark'
            self.shengdakanguichange ()
            self.resize (350, 580)
            self.ui.groupBox_mm.show()

        if self.ui.comboBox_date.isEnabled ():
            if str (self.ui.comboBox_date.currentText ()) == 'WWYY':
                self.symbol_attr = 351
            elif str (self.ui.comboBox_date.currentText ()) == 'YYWW':
                self.symbol_attr = 350
            elif str (self.ui.comboBox_date.currentText ()) == 'YYWWD':
                self.symbol_attr = 352
        self.Change_tips ()

    def Change_window_length(self,width,length):
        # --修改序列号symbol高、宽度 AresHe 2021.9.13
        self.ui.lineEdit_width.setText(str(width))
        self.ui.lineEdit_length.setText(str(length))

    def Change_tips(self):
        self.ui.label_tips.setText (
            _translate ("MainWindow", "Tips:Symbol名称%s" % (self.barcode_symbol), None))
        self.ui.label_attr.setText (
            _translate ("MainWindow", "属性%s=%s" % (self.attr_words, self.symbol_attr), None))
        if self.supply == 'hanyin':
            self.ui.label_pnl.setText (
                _translate ("MainWindow", "Panel添加，长%sx宽%s,旋转270°添加\nSymbol：num_260属性.out_flag=260" %
                            (self.pnl_codex, self.pnl_codey), None))
        if self.supply == 'shengdakang':
            self.ui.label_pnl.setText (
                _translate ("MainWindow", "注意事项：\nPanel添加r0.2光点，位置为防焊对位pad;\n如需板内位置对位请手动移动;\n实际二维码明码添加层别为2dbc-c或2dbc-s.", None))
        if self.supply == 'aobao':
            self.ui.label_tips.setText (
                _translate ("MainWindow", "说明:\n1.包装码默认set，负性;\n2.常规二维码默认为负,同步添加底套铜及底pad;\n3.B74二维码默认为正;\n4.在临时层别可以加大缩小位置pad" , None))

    def shengdakanguichange(self):
        if self.ui.comboBox_mode.currentText () == u'二维码':
            self.ui.lineEdit_mmheight.setDisabled (True)
            self.ui.lineEdit_mmlength.setDisabled (True)
            self.ui.lineEdit_mm_by.setDisabled (True)
            self.ui.lineEdit_2dbc_by.setDisabled (False)
            self.ui.checkBox_mm_by.setDisabled (True)
            self.ui.checkBox_2dbc_by.setDisabled (False)

            if self.ui.checkBox_2dbc_by.isChecked():
                self.ui.lineEdit_2dbc_by.setDisabled (False)
            else:
                self.ui.lineEdit_2dbc_by.setDisabled (True)

        elif self.ui.comboBox_mode.currentText () == u'明码':
            self.ui.lineEdit_mmheight.setDisabled (False)
            self.ui.lineEdit_mmlength.setDisabled (False)
            self.ui.lineEdit_mm_by.setDisabled (False)
            self.ui.lineEdit_2dbc_by.setDisabled (True)
            self.ui.checkBox_mm_by.setDisabled (False)
            self.ui.checkBox_2dbc_by.setDisabled (True)

        elif self.ui.comboBox_mode.currentText () == u'二维码及明码':
            self.ui.lineEdit_mmheight.setDisabled (False)
            self.ui.lineEdit_mmlength.setDisabled (False)
            self.ui.lineEdit_mm_by.setDisabled (False)
            self.ui.lineEdit_2dbc_by.setDisabled (False)
            self.ui.checkBox_mm_by.setDisabled (False)
            self.ui.checkBox_2dbc_by.setDisabled (False)

    def getLayerList(self):
        silk_layers = GEN.GET_ATTR_LAYER ('silk_screen')
        # silk_layers = ['c1']
        return silk_layers

    # --根据属性获取Board层
    def get_all_outer_layers(self):
        """
        获取外层、防焊、文字层别，区分top及bottom
        :return:
        """
        m_info = GEN.DO_INFO('-t matrix -e %s/matrix' % self.job_name)
        LayValues = dict(silk_screen=dict(), solder_mask=dict(), signal=dict())
        for row in m_info['gROWrow']:
            num = m_info['gROWrow'].index(row)
            lay_type = m_info['gROWlayer_type'][num]

            if lay_type in ['silk_screen','solder_mask','signal']:
                if m_info['gROWcontext'][num] == 'board' and m_info['gROWside'][num] in ['top', 'bottom']:
                    LayValues[lay_type][m_info['gROWname'][num]] = m_info['gROWside'][num]

        # --返回对应数组信息
        return LayValues

    def add_rectangle(self, width, height, add_sym='r0', add_attr='yes'):
        GEN.COM ("add_polyline_strt")

        # --按需求A86、A81系列按顺时针顺序添加symbol
        if self.ui.comboBox_supply.currentText() == u'A86文字喷墨(MLB)' or self.ui.comboBox_supply.currentText() == u'A86文字喷墨(HDI)' or self.ui.comboBox_supply.currentText() == u'A81文字喷墨(HDI)':
            GEN.COM("add_polyline_xy,x=0,y=0")
            GEN.COM("add_polyline_xy,x=0,y=%s" % height)
            GEN.COM ("add_polyline_xy,x=%s,y=%s" % (width, height))
            GEN.COM("add_polyline_xy,x=%s,y=0" % width)
            GEN.COM ("add_polyline_xy,x=0,y=0")
        else:
            GEN.COM("add_polyline_xy,x=0,y=0")
            GEN.COM("add_polyline_xy,x=%s,y=0" % width)
            GEN.COM("add_polyline_xy,x=%s,y=%s" % (width, height))
            GEN.COM("add_polyline_xy,x=0,y=%s" % height)
            GEN.COM("add_polyline_xy,x=0,y=0")

        GEN.COM ("add_polyline_end,attributes=%s,symbol=%s,polarity=positive,"
                 "bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left" % (add_attr, add_sym))

    def add_f(self, width, height, add_sym='r0', add_attr='no',add_pol='negative'):
        width = float(width)
        height = float(height)
        hlist = (height / 3, height / 2, height * 2 / 3)
        wlist = (width / 3, width / 2, width * 2 / 3)
        GEN.COM ("add_polyline_strt")
        GEN.COM ("add_polyline_xy,x=%s,y=%s" % (wlist[2], hlist[2]))
        GEN.COM ("add_polyline_xy,x=%s,y=%s" % (wlist[0], hlist[2]))
        GEN.COM ("add_polyline_xy,x=%s,y=%s" % (wlist[0], hlist[0]))
        GEN.COM ("add_polyline_xy,x=%s,y=%s" % (wlist[0], hlist[1]))
        GEN.COM ("add_polyline_xy,x=%s,y=%s" % (wlist[1], hlist[1]))
        GEN.COM ("add_polyline_end,attributes=%s,symbol=%s,polarity=%s,"
                 "bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left" % (add_attr, add_sym,add_pol))

    def create_2dbc_sym(self, bc_size):
        sl1 = bc_size * 0.5
        current_unit = GEN.GET_UNITS()
        GEN.CLEAR_LAYER()
        GEN.CHANGE_UNITS('mm')
        GEN.DELETE_LAYER('tmp_song_2dbc')
        GEN.CREATE_LAYER('tmp_song_2dbc')
        GEN.AFFECTED_LAYER('tmp_song_2dbc','yes')
        self.add_rectangle (bc_size, bc_size, add_sym='r152.4', add_attr='no')
        self.add_f(bc_size,bc_size,add_sym='r152.4',add_pol='positive')
        GEN.COM('sel_create_sym,symbol=2dbc_%smm,x_datum=%s,y_datum=%s,delete=no,fill_dx=2.54,fill_dy=2.54,'
                'attach_atr=no,retain_atr=no' % (bc_size, sl1, sl1 ))
        GEN.CHANGE_UNITS(current_unit)
        GEN.DELETE_LAYER('tmp_song_2dbc')

    def create_2dtext_sym(self, symbol_length, symbol_height):
        sl1 = symbol_length * 0.5
        sl2 = symbol_height * 0.5
        current_unit = GEN.GET_UNITS()
        GEN.CLEAR_LAYER()
        GEN.CHANGE_UNITS('mm')
        GEN.DELETE_LAYER('tmp_song_2dbc')
        GEN.CREATE_LAYER('tmp_song_2dbc')
        GEN.AFFECTED_LAYER('tmp_song_2dbc','yes')
        self.add_rectangle (symbol_length, symbol_height, add_sym='r152.4', add_attr='no')
        self.add_f(symbol_length,symbol_height,add_sym='r152.4',add_pol='positive')
        GEN.COM('sel_create_sym,symbol=2dtext_%sx%smm,x_datum=%s,y_datum=%s,delete=no,fill_dx=2.54,fill_dy=2.54,'
                'attach_atr=no,retain_atr=no' % (symbol_length, symbol_height,sl1, sl2 ))
        GEN.CHANGE_UNITS(current_unit)
        GEN.DELETE_LAYER('tmp_song_2dbc')

    def Create_symbol(self, mode='jinxin', add_pnl='no'):
        """mode='jinxin'or mode='hanyin' add_pnl='yes' 当汉印序列号添加时，自动在板边添加"""
        # 生成symbol语句
        GEN.COM ("editor_group,job=%s,is_step=yes,name=%s" % (self.job_name, self.step_name))
        edit_com = GEN.COMANS
        code_name = self.barcode_symbol
        code_num = self.symbol_attr
        code_length = self.barcode_x
        code_height = self.barcode_y
        GEN.COM ("disp_off")
        GEN.VOF ()
        if add_pnl == 'yes':
            code_name = 'num_260'
            code_num = 260
            code_length = 12
            code_height = 3
        GEN.COM ("create_entity,job=%s,is_fw=no,type=symbol,name=%s,db=,fw_type=form" % (
            self.job_name, code_name))

        GEN.VON ()
        GEN.COM ("open_entity,job=%s,type=symbol,name=%s,iconic=no" % (self.job_name, code_name))
        GEN.COM ("work_layer,name=%s" % code_name)
        GEN.SEL_DELETE ()
        GEN.CHANGE_UNITS ('mm')
        GEN.COM ("cur_atr_set,attribute=%s,int=%s" % (self.attr_words, code_num))

        GEN.COM ("add_pad,attributes=yes,x=0,y=0,symbol=r0,polarity=positive,"
                 "angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1")

        self.add_rectangle (code_length, code_height, add_sym='r0', add_attr='yes')
        GEN.COM ("cur_atr_reset")
        if mode == 'hanyin' or mode == 'jinxin' or mode == 'a86silk_hdi':
            self.add_f (code_length, code_height, add_sym='r0', add_attr='no')
        GEN.COM ("editor_page_close")
        GEN.COM ("disp_on")

        GEN.COM ("open_entity,job=%s,type=step,name=%s,iconic=no" % (self.job_name, self.step_name))
        GEN.AUX ("set_group, group =%s" % (edit_com))

    def add_symbol(self, layerlist):
        for wlayer in layerlist:
            # 1.添加检测根据层别检测是否镜像
            glyrside = GEN.DO_INFO ("-t layer -e %s/%s/%s -d SIDE" % (self.job_name, self.step_name, wlayer))
            check_mir = ''
            if glyrside['gSIDE'] == 'top':
                check_mir = 'no'
            elif glyrside['gSIDE'] == 'bottom':
                check_mir = 'yes'
            if check_mir != self.add_mir:
                M = M_Box ()
                showText = M.msgText (u'警告', u"%s层别镜像添加不正确，跳过!" % (wlayer))
                M.msgBox (showText)
                continue
            GEN.WORK_LAYER (wlayer)
            GEN.COM ('snap_mode, mode = off')
            GEN.MOUSE ("please point the positon add the symbol", mode='p')
            pos_x = GEN.MOUSEANS.split (' ')[0]
            pos_y = GEN.MOUSEANS.split (' ')[1]
            GEN.COM ('cur_atr_reset')
            GEN.COM ("cur_atr_set,attribute=%s,int=%s" % (self.attr_words, self.symbol_attr))
            GEN.COM ("add_pad,attributes=yes,x=%s,y=%s,symbol=%s,polarity=positive,"
                     "angle=%s,mirror=%s,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1" % (
                         pos_x, pos_y, self.barcode_symbol, self.add_angle, self.add_mir))

    def add_pnl_symbol(self, layerlist):
        # 判断panel是否存在
        # 获取panel整个大小，获取坐标，放大左上角
        # 判断panel的边缘值，加2mil大小的四个点
        # 如panel对应层别没有r0对位点，从外层过滤复制
        pnlStep = 'panel'
        if GEN.STEP_EXISTS (self.job_name, pnlStep) == 'no':
            M = M_Box ()
            showText = M.msgText (u'警告', u"panel Step 不存在，不进行板边序列号添加")
            M.msgBox (showText)
            return False
        # 打开panel step
        profx, profy = GEN.GET_PROFILE_SIZE (self.job_name, pnlStep)
        GEN.OPEN_STEP (pnlStep, job=self.job_name)
        GEN.CHANGE_UNITS ('mm')
        pnlRoutLayer = 'pnl_rout'
        all_layer_list = GEN.GET_ATTR_LAYER ('all', job=self.job_name)
        pnlRoutLayer = 'pnl_rout'
        record_index = 0
        for index in all_layer_list:
            m = re.match ("^pnl_rout([0-9])$", index)
            if m:
                record_index = int (m.group (1)) if int (m.group (1)) > record_index else record_index
            elif re.match ("^pnl_rout$", index):
                record_index = -1
        pnlxmin, pnlymin, pnlxmax, pnlymax = 0, 0, profx, profy
        # 获取序号最大的pnl_rout层
        if record_index == 0:
            M = M_Box ()
            showText = M.msgText (u'警告', u"panel Step 中不存在pnl_rout类层别，添加有效区域标记点以profile为准")
            M.msgBox (showText)
        else:
            if record_index == -1:
                pnlRoutLayer = 'pnl_rout'
            else:
                pnlRoutLayer = 'pnl_rout' + str (record_index)
            getLF = self.getLayerFeature (pnlStep, pnlRoutLayer)
            xmin, xmax, ymin, ymax = self.getMinMaxCor (getLF)
            pnlxmin, pnlymin, pnlxmax, pnlymax = xmin + 0.5, ymin + 0.5, xmax - 0.5, ymax - 0.5

        for wlayer in layerlist:
            # 1.添加检测根据层别检测是否镜像
            glyrside = GEN.DO_INFO ("-t layer -e %s/%s/%s -d SIDE" % (self.job_name, pnlStep, wlayer))
            check_mir = ''
            if glyrside['gSIDE'] == 'top':
                check_mir = 'no'
            elif glyrside['gSIDE'] == 'bottom':
                check_mir = 'yes'
            if check_mir != self.add_mir:
                M = M_Box ()
                showText = M.msgText (u'警告', u"%s层别镜像添加不正确，跳过!" % (wlayer))
                M.msgBox (showText)
                continue
            GEN.WORK_LAYER (wlayer)
            GEN.COM ('zoom_area, x1 = %s, y1 = %s, x2 = %s, y2 = %s' % (
            -10, float (profy) * 1.125, 40, float (profy) * 0.725))
            GEN.COM ('snap_mode, mode = off')
            GEN.MOUSE ("please point the positon add the symbol", mode='p')
            pos_x = GEN.MOUSEANS.split (' ')[0]
            pos_y = GEN.MOUSEANS.split (' ')[1]
            GEN.COM ('cur_atr_reset')
            GEN.COM ("cur_atr_set,attribute=%s,int=%s" % (self.attr_words, '260'))
            GEN.COM ("add_pad,attributes=yes,x=%s,y=%s,symbol=%s,polarity=positive,"
                     "angle=%s,mirror=%s,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1" % (
                         pos_x, pos_y, 'num_260', '270', self.add_mir))
            # 添加四个区域大小标识点，加在四角，大小2mil
            GEN.ADD_PAD (pnlxmin, pnlymin, 'r50', attr='no')
            GEN.ADD_PAD (pnlxmin, pnlymax, 'r50', attr='no')
            GEN.ADD_PAD (pnlxmax, pnlymax, 'r50', attr='no')
            GEN.ADD_PAD (pnlxmax, pnlymin, 'r50', attr='no')
            # 判断添加层别是否有r0的对位点
            getFeatureInfo = self.getLayerFeature (pnlStep, wlayer)
            # print json.dumps (getFeatureInfo, sort_keys=True, indent=2, separators=(',', ': '))

            getr0FL = [i for i in getFeatureInfo if i['type'] == 'pad' and i["symbol"] == 'r0' and (
                        ".out_flag=233" in i['attributes'] or ".out_flag=226" in i['attributes'])]
            # print len (getr0FL)
            # print json.dumps (getr0FL, sort_keys=True, indent=2, separators=(',', ': '))
            if len (getr0FL) != 4:
                M = M_Box ()
                showText = M.msgText (u'提示', u"层别%s中r0属性.out_flag=233或226的点数量不是4个，实际为%s，程序自动copy外层r0点!" % (
                wlayer, len (getr0FL)), showcolor='green')
                M.msgBox (showText)
                # 删除添加层的r0点
                GEN.CLEAR_LAYER()
                GEN.WORK_LAYER(wlayer)
                GEN.FILTER_RESET()
                GEN.COM('filter_atr_reset')
                GEN.FILTER_SET_TYP('pad')
                GEN.FILTER_SET_INCLUDE_SYMS('r0')
                GEN.COM('filter_atr_set, filter_name = popup, condition = yes, attribute =.out_flag, min_int_val = 226, max_int_val = 233')
                GEN.FILTER_SELECT()
                if int(GEN.GET_SELECT_COUNT()) != 0:
                    GEN.SEL_DELETE()
                GEN.CLEAR_LAYER()

                # copy外层的0点或者根据外层symbol自动添加r0的对位点
                out_layer = 'l1'
                if glyrside['gSIDE'] == 'bottom':
                    out_layer_list = GEN.GET_ATTR_LAYER('outer')
                    out_layer = [i for i in out_layer_list if i != 'l1']
                out_layer = out_layer[0]
                GEN.CLEAR_LAYER()
                GEN.WORK_LAYER(out_layer)
                GEN.FILTER_RESET()
                GEN.COM('filter_atr_reset')
                GEN.FILTER_SET_TYP('pad')
                GEN.FILTER_SET_INCLUDE_SYMS('r0')
                GEN.COM('filter_atr_set, filter_name = popup, condition = yes, attribute =.out_flag, min_int_val = 226, max_int_val = 233')
                GEN.FILTER_SELECT()
                tmp_count = int(GEN.GET_SELECT_COUNT())
                if int(GEN.GET_SELECT_COUNT()) == 4:
                    GEN.SEL_COPY(wlayer)
                else:
                    M = M_Box ()
                    showText = M.msgText (u'手动添加警告', u"层别%s中r0属性.out_flag=233或226的点数量不是4个，实际为%s\n请手动添加%s对位点!" % (
                        out_layer, tmp_count,wlayer), showcolor='red')
                    M.msgBox (showText)
            GEN.CLEAR_LAYER ()

    def getLayerFeature(self, istep, ilayar):
        allFeatureInfo = GEN.INFO ('-t layer -e %s/%s/%s -d FEATURES' % (self.job_name, istep, ilayar))
        layerinfo = []
        for i in allFeatureInfo:
            # print i
            if re.match ("^###", i): continue
            if re.match ("^\s+$", i): continue
            i = i.strip ('\n')
            if re.match ("^#[PLATS]", i):
                tmp = i.split (';')
                info = tmp[0]
                attributes = []
                try:
                    attributes = tmp[1].split (',')
                except IndexError:
                    attributes = []
                tmphash = {}
                infos = info.split (' ')
                if infos[0] == '#P':
                    tmphash['type'] = 'pad'
                    tmphash['x'] = infos[1]
                    tmphash['y'] = infos[2]
                    tmphash['symbol'] = infos[3]
                    tmphash['polarity'] = 'positive' if infos[4] == 'P' else 'negative',
                    tmphash['dcode'] = infos[5]
                    tmphash['angle'] = infos[6]
                    tmphash['mirror'] = 'yes' if infos[7] == 'Y' else 'no'
                    tmphash['attributes'] = attributes
                elif infos[0] == '#L':
                    tmphash['type'] = 'line'
                    tmphash['xs'] = infos[1]
                    tmphash['ys'] = infos[2]
                    tmphash['xe'] = infos[3]
                    tmphash['ye'] = infos[4]
                    tmphash['symbol'] = infos[5]
                    tmphash['polarity'] = 'positive' if infos[6] == 'P' else 'negative'
                    tmphash['dcode'] = infos[7]
                    tmphash['attributes'] = attributes

                elif infos[0] == '#A':
                    tmphash['type'] = 'arc'
                    tmphash['xs'] = infos[1]
                    tmphash['ys'] = infos[2]
                    tmphash['xe'] = infos[3]
                    tmphash['ye'] = infos[4]
                    tmphash['xc'] = infos[5]
                    tmphash['yc'] = infos[6]
                    tmphash['symbol'] = infos[7]
                    tmphash['polarity'] = 'positive' if infos[8] == 'P' else 'negative'
                    tmphash['dcode'] = infos[9]
                    tmphash['direction'] = 'cw' if infos[10] == 'Y' else 'ccw'
                    tmphash['attributes'] = attributes

                elif infos[0] == '#T':
                    tmphash['type'] = 'text'
                    tmphash['x'] = infos[1]
                    tmphash['y'] = infos[2]
                    tmphash['fontname'] = infos[3]
                    tmphash['polarity'] = 'positive' if infos[4] == 'P' else 'negative'
                    tmphash['angle'] = infos[5]
                    tmphash['mirror'] = 'yes' if infos[6] == 'Y' else 'no'
                    tmphash['x_size'] = infos[7]
                    tmphash['y_size'] = infos[8]
                    tmphash['w_factor'] = infos[9]
                    tmphash['text'] = infos[10:]
                    tmphash['attributes'] = attributes

                else:
                    tmphash['type'] = 'surface'
                    tmphash['feats'] = infos
                if tmphash:
                    layerinfo.append (tmphash)
        if layerinfo:
            return layerinfo
        else:
            return False

    def add_2dbc(self):
        """
        镭雕二维码及明码添加程序
        :return:
        """
        # 确认变量，是否添加明码，是否添加明码白油块，1为添加，0为不添加
        add_2dbc = 0
        if self.ui.comboBox_mode.currentText() == u'明码' or self.ui.comboBox_mode.currentText() == u'二维码及明码':
            mm_add = 1
            if self.ui.checkBox_mm_by.isChecked() and self.ui.checkBox_mm_by.isEnabled():
                mm_by = 1
            else:
                mm_by = 0
        else:
            mm_add = 0
            mm_by = 0
        if self.ui.comboBox_mode.currentText () == u'二维码' or self.ui.comboBox_mode.currentText () == u'二维码及明码':
            add_2dbc = 1
        if self.ui.checkBox_2dbc_by.isChecked() and self.ui.checkBox_2dbc_by.isEnabled():
            by_2dbc = 1
        else:
            by_2dbc = 0
        if self.ui.checkBox_pnl_2dbc.isChecked():
            coup_add = 1
        else:
            coup_add = 0

        dc_sym = '2dbc_%smm' % self.ui.lineEdit_length.text()

        if dc_sym != self.barcode_symbol:
            M = M_Box ()
            showText = M.msgText (u'提示', u"界面symbol %s 和后台生成symbol %s不一致，请选择!" % (self.barcode_symbol,dc_sym), showcolor='green')
            M.msgBox (showText)
            self.show()
            return 'UIError'
        # 创建二维码symbol #
        info = GEN.DO_INFO ('-t symbol -e %s/%s -d EXISTS' % (self.job_name, dc_sym))
        if info['gEXISTS'] == 'no':
            sym_size = unicode (self.ui.lineEdit_length.text().toUtf8 (), 'utf-8', 'ignore')
            sym_size = sym_size.strip ('mm')
            sym_size = self.stringtonum (sym_size)
            if sym_size != 'Error':
                self.create_2dbc_sym (sym_size)
            else:
                M = M_Box ()
                showText = M.msgText (u'提示', u"二维码尺寸选择错误!", showcolor='red')
                M.msgBox (showText)
                return 'UIError'
        # === 当添加二维码白油块状态为激活时，才判断尺寸是否正确 2020.09.27 Song ===
        baiyou_size = self.ui.lineEdit_2dbc_by.text()
        baiyou_size = self.stringtonum (baiyou_size)
        if by_2dbc == 1:
            if baiyou_size is not False:
                baiyou_sym = str (baiyou_size * 1000)
            else:
                M = M_Box ()
                showText = M.msgText (u'提示', u"白油块尺寸选择错误!", showcolor='red')
                M.msgBox (showText)
                return 'UIError'
        text_by_sym = ''
        if mm_by == 1:
            get_size = self.ui.lineEdit_mm_by.text()
            if 'x' in str(get_size):
                get_data = get_size.split('x')
                get_lenght = self.stringtonum (get_data[0])
                get_height = self.stringtonum (get_data[1])
            else:
                get_lenght = self.stringtonum (get_size)
                get_height = self.stringtonum (get_size)
            if get_lenght is not False and get_height is not False:
                text_by_sym = 'rect%sx%s' % (get_lenght * 1000, get_height*1000)
            else:
                M = M_Box ()
                showText = M.msgText (u'提示', u"明码白油块尺寸选择错误!", showcolor='red')
                M.msgBox (showText)
                return 'UIError'
        # sel_sm = self.listWidget.selectedItems ()
        # ad_layer = sel_sm[0].text ()
        # === 检查镜像关系 ===
        for ad_layer in self.addLayerList:

            top_silk_layers = ('lc', 'c1', 'c1-2', 'cc', 'c1-1', 'c1-3')
            bot_silk_layers = ('ls', 'c2', 'c2-2', 'cc2', 'c2-1', 'c2-3')
            if ad_layer in top_silk_layers:
                ad_mir = 'no'
            elif ad_layer in bot_silk_layers:
                ad_mir = 'yes'
            else:
                # GEN.PAUSE ('NOT silk screen name layers ! Now exit ')
                M = M_Box ()
                showText = M.msgText (u'提示', u"%s不是文字层命名!"% ad_layer, showcolor='red')
                M.msgBox (showText)
                return 'UIError'

            if self.add_mir == ad_mir:
                pass
            else:
                # GEN.PAUSE ('C layer add no mirror ,S layer add mirror, Exit')
                # exit ()
                M = M_Box ()
                showText = M.msgText(u'提示', u"%s层别的镜像添加应为%s，不是%s!" % (ad_layer, ad_mir, self.add_mir), showcolor='red')
                M.msgBox (showText)
                return 'UIError'

            GEN.CLEAR_LAYER()
            # TODO === 获取添加面次的正反面，关联2dbc-c，2dbc-s层别
            glyrside = GEN.DO_INFO ("-t layer -e %s/%s/%s -d SIDE" % (self.job_name, self.step_name, ad_layer))
            check_mir = ''
            if glyrside['gSIDE'] == 'top':
                check_mir = 'no'
                related_layer = '2dbc-c'
            elif glyrside['gSIDE'] == 'bottom':
                check_mir = 'yes'
                related_layer = '2dbc-s'
            if check_mir != self.add_mir:
                M = M_Box ()
                showText = M.msgText (u'提示', u"镜像选择%s与层别上下面次%s不符!" % (self.add_mir, check_mir), showcolor='red')
                M.msgBox (showText)
                return 'UIError'

            if GEN.LAYER_EXISTS(related_layer, self.job_name, self.step_name) == 'no':
                GEN.CREATE_LAYER(related_layer)
            else:
                GEN.CLEAR_LAYER()
                GEN.AFFECTED_LAYER(related_layer, 'yes')
                GEN.SEL_DELETE()
            GEN.CLEAR_LAYER()
            GEN.WORK_LAYER(ad_layer)
            if add_2dbc == 1:
                GEN.MOUSE ('Please select the 2d-code kuang', mode='p')
                GEN.COM ('get_select_count')
                if GEN.COMANS == '0':
                    M = M_Box ()
                    showText = M.msgText (u'提示', u"未选择任何物件，程序退出!" , showcolor='red')
                    M.msgBox (showText)
                    # GEN.PAUSE ("You not select any feature ! Now Exit !")
                    # exit ()
                    return 'Error'

                GEN.COM ('get_work_layer')
                wk_layer = GEN.COMANS

                dcsel = GEN.DO_INFO ('-t layer -e %s/%s/%s -d LIMITS -o select,units=mm' % (self.job_name, self.step_name, wk_layer))
                dc_p_x, dc_p_y = float (dcsel['gLIMITSxcenter']), float (dcsel['gLIMITSycenter'])
                dc_m_x, dc_m_y, dc_c_x, dc_c_y = self.get_2dbc_mm_cor(self.add_mir,self.add_angle,dc_p_x, dc_p_y,by_2dbc_size=baiyou_size,by_mm_size=1.6)

            if mm_add == 1:
                text_length = self.stringtonum (str(self.ui.lineEdit_mmlength.text()))
                text_height = self.stringtonum (str(self.ui.lineEdit_mmheight.text()))
                text_symbol = '2dtext_%sx%smm' % (text_length,text_height)

                info = GEN.DO_INFO ('-t symbol -e %s/%s -d EXISTS' % (self.job_name, text_symbol))
                if info['gEXISTS'] == 'no':
                    self.create_2dtext_sym(text_length,text_height)
                dc_c_add = 'yes'
                GEN.WORK_LAYER (ad_layer)
                GEN.COM ('clear_highlight')
                GEN.COM ('sel_clear_feat')
                GEN.MOUSE ('Please select the mm-code kuang', mode='p')
                GEN.COM ('get_select_count')
                if GEN.COMANS == '0':
                    if add_2dbc == 0:
                        M = M_Box ()
                        showText = M.msgText (u'提示', u"未选择任何物件，程序退出!", showcolor='red')
                        M.msgBox (showText)
                        # GEN.PAUSE ("You not select any feature ! Now Exit !")
                        # exit ()
                        return 'Error'
                    else:
                        # GEN.PAUSE ('You not select any feature ! Use 2d code position below !')
                        M = M_Box ()
                        showText = M.msgText (u'提示', u"未选择任何物件，使用二维码坐标下方添加!", showcolor='green')
                        M.msgBox (showText)
                else:
                    GEN.COM ('get_work_layer')
                    wk_layer = GEN.COMANS

                    mmsel = GEN.DO_INFO (
                        '-t layer -e %s/%s/%s -d LIMITS -o select,units=mm' % (self.job_name, self.step_name, wk_layer))
                    dc_m_x = float (mmsel['gLIMITSxcenter'])
                    dc_m_y = float (mmsel['gLIMITSycenter'])
                    dc_c_add = 'no'

        GEN.CLEAR_FEAT ()
        GEN.CLEAR_LAYER ()
        GEN.WORK_LAYER (ad_layer)

        GEN.COM ('cur_atr_reset')
        GEN.COM ('cur_atr_set,attribute=.string,text=2dmark')

        GEN.COM ('units,type=mm')
        # === 白油块添加在工作层 ===
        if by_2dbc == 1:
            GEN.ADD_PAD (dc_p_x, dc_p_y, 'rect' + baiyou_sym + 'x' + baiyou_sym, angle=self.add_angle, mir=self.add_mir, attr='yes')
        if mm_add == 1:
            if mm_by == 1:
                GEN.ADD_PAD (dc_m_x, dc_m_y, text_by_sym, angle=self.add_angle, mir=self.add_mir, attr='yes')
        GEN.CLEAR_LAYER ()
        # === 二维码添加在2dbc-c/s 层 ===
        GEN.AFFECTED_LAYER (related_layer,'yes')
        if add_2dbc == 1:
            GEN.ADD_PAD (dc_p_x, dc_p_y, dc_sym, angle=self.add_angle, mir=self.add_mir, attr='yes')
        if mm_add == 1:
            # if mm_by == 1:
            #     GEN.ADD_PAD (dc_m_x, dc_m_y, text_by_sym, angle=self.add_angle, mir=self.add_mir, attr='yes')
            GEN.ADD_PAD (dc_m_x, dc_m_y, text_symbol, angle=self.add_angle, mir=self.add_mir, attr='yes')
        GEN.AFFECTED_LAYER (related_layer,'no')
        GEN.COM ('cur_atr_reset')
        GEN.COM ('editor_page_close')
        # TODO === 二维码coupon不是按照界面数据生成
        # === 暂无规则，留作待办 ===
        if coup_add == 1:
            coup_name = 'ewm-coupon'
            if GEN.STEP_EXISTS (step=coup_name) == 'no':
                GEN.CREATE_ENTITY ('db1', self.job_name, step=coup_name)
            # else:
            #     GEN.PAUSE ('All features in step %s will be delete' % coup_name)

            GEN.OPEN_STEP (coup_name)
            GEN.CLEAR_FEAT ()
            GEN.CLEAR_LAYER ()
            GEN.COM ('affected_layer,mode=all,affected=yes')
            GEN.SEL_DELETE ()
            GEN.CHANGE_UNITS ('mm')

            pro_area = (0, 0, 7.1, 7.1)
            if mm_add == 1:
                pro_area = (-1.45, -1.5, 8.55, 7.1)
            GEN.COM ('profile_rect,x1=%s,y1=%s,x2=%s,y2=%s' % (pro_area[0], pro_area[1], pro_area[2], pro_area[3]))
            GEN.COM ('profile_to_rout,layer=outline,width=6')
            GEN.WORK_LAYER (ad_layer)
            GEN.COM ('cur_atr_reset')
            GEN.COM ('cur_atr_set,attribute=.string,text=2dmark')
            c_dc_p = (3.55, 3.55)
            c_dc_m = (3.55, -0.75)
            GEN.ADD_PAD (c_dc_p[0], c_dc_p[1], 'rect7100x7100', mir=ad_mir, attr='yes')
            GEN.ADD_PAD (c_dc_p[0], c_dc_p[1], dc_sym, mir=ad_mir, attr='yes')
            if mm_add == 1:
                # GEN.ADD_PAD (c_dc_m[0], 0, text_by_sym, mir=ad_mir, attr='yes')
                GEN.ADD_PAD (c_dc_m[0], c_dc_m[1], text_by_sym, mir=ad_mir, attr='yes')
                GEN.ADD_PAD (c_dc_m[0], c_dc_m[1], text_symbol, mir=ad_mir, attr='yes')
            GEN.CLEAR_LAYER ()
            GEN.COM ('cur_atr_reset')
            GEN.COM ('affected_filter,filter=(context=board&side=inner&pol=positive)')
            GEN.COM ('get_affect_layer')
            if GEN.COMANS != 0:
                GEN.SR_FILL ('positive', 0, 0, 2540, 2540)
            GEN.CLEAR_LAYER ()
        self.add_pnl_2dbc_marK(related_layer)
        return True
        # GEN.PAUSE ('Please check !')

    def add_ob_2dbc(self):
        """
        蚀刻二维码明码，文字的包装分堆码
        :return:
        """
        # === 使用默认大小添加至辅助层，需要CAM移动，并添加程序防呆，如位置可行则进行线路层的添加，如大小不合适则CAM可进行修改，
        # === 使用参考层大小进行添加。
        add_mode = ''
        if self.ui.radioButton_b74.isChecked():
            add_mode = 'b74'
        elif self.ui.radioButton_normal.isChecked():
            add_mode = 'normal'
        if not add_mode:
            M = M_Box ()
            showText = M.msgText (u'提示', u"未勾选添加类型!", showcolor='red')
            M.msgBox (showText)
            return 'UIError'
        add_types = []
        if self.ui.checkBox_ob2dbc.isChecked():
            add_types.append('ob2dbc')
        if self.ui.checkBox_obmm.isChecked():
            add_types.append('obtext')
        if self.ui.checkBox_baozhuang.isChecked():
            add_types.append('baozhuang')
        if len(add_types) == 0:
            M = M_Box ()
            showText = M.msgText (u'提示', u"未勾选添加内容!", showcolor='red')
            M.msgBox (showText)
            return 'UIError'
        if self.ui.widget_bzside.isEnabled():
            if self.ui.radioButton_bztop.isChecked():
                bzside = 'top'
                bz_mir = 'no'
            elif self.ui.radioButton_bzbot.isChecked():
                bzside = 'bottom'
                bz_mir = 'yes'
            else:
                M = M_Box ()
                showText = M.msgText (u'提示', u"包装未选择面次!", showcolor='red')
                M.msgBox (showText)
                return 'UIError'
        else:
            bzside = None

        if self.ui.widget_bzlayer.isEnabled():
            if self.ui.radioButton_sm.isChecked():
                bz_layer = 'solder_mask'
            elif self.ui.radioButton_ss.isChecked():
                bz_layer = 'silk_screen'
            else:
                M = M_Box ()
                showText = M.msgText (u'提示', u"包装未选择层别!", showcolor='red')
                M.msgBox (showText)
                return 'UIError'
        else:
            bz_layer = None
        if self.ui.widget_bzdate.isEnabled():
            if self.ui.comboBox_bz_date.currentText() == u'其他':
                bz_date = str(self.ui.bz_other_date.text())
            else:
                bz_date = str(self.ui.comboBox_bz_date.currentText())
        else:
            bz_date = None
        # === 获取外层，防焊，文字
        bclyr_dict = self.get_all_outer_layers()
        # print json.dumps(bclyr_dict, indent=2)
        baozhuang_layer = None
        if 'baozhuang' in add_types:
            try:
                baozhuang_layer = [i for i in bclyr_dict[bz_layer] if bclyr_dict[bz_layer][i] == bzside][0]
            except IndexError:
                M = M_Box ()
                showText = M.msgText (u'提示', u"料号中无选择的包装层!", showcolor='red')
                M.msgBox (showText)
                return 'UIError'

        # === 判断系列，用于添加内容的确定
        if self.ui.radioButton_obtop.isChecked():
            etch_side = 'top'
        elif self.ui.radioButton_obbot.isChecked():
            etch_side = 'bottom'
        else:
            etch_side = None

        try:
            des_etch = [i for i in bclyr_dict['signal'] if bclyr_dict['signal'][i] == etch_side][0]
        except IndexError:
            des_etch = None

        if ('ob2dbc' in add_types or 'obtext' in add_types) and des_etch is None:
            M = M_Box ()
            showText = M.msgText (u'提示', u"蚀刻面次未选择!", showcolor='red')
            M.msgBox (showText)
            return 'UIError'
        etch_big_bc = 'no'
        if self.ui.checkBox_cuthick.isChecked():
            etch_big_bc = 'yes'

        # === 判断添加内容，二维码，明码。包装分堆码
        tmp_layer = '__etchtmp2dbc__'
        add_steps = []
        if add_mode == 'b74':
            add_steps = ['edit', 'set']
        elif add_mode == 'normal':
            if self.ui.checkBox_edit.isChecked():
                add_steps.append('edit')
            if self.ui.checkBox_set.isChecked():
                add_steps.append('set')
            if self.ui.checkBox_icg.isChecked():
                add_steps.append('icg')
        if len(add_steps) == 0:
            M = M_Box ()
            showText = M.msgText (u'提示', u"未选择添加Step!", showcolor='red')
            M.msgBox (showText)
            return 'UIError'
        get_ob_2dbc_size = None
        if 'ob2dbc' in add_types:
            get_ob_2dbc_size = self.ui.lineEdit_ob2dbc.text()
            get_ob_2dbc_size = GEN.convertToNumber(str(get_ob_2dbc_size))
            if self.ui.checkBox_cuthick.isChecked():
                if get_ob_2dbc_size < 5.0:
                    M = M_Box ()
                    showText = M.msgText (u'提示', u"勾选面铜大于1.18mil，二维码应大于5mm!", showcolor='red')
                    M.msgBox (showText)
                    return 'UIError'
            else:
                if add_mode == 'normal':
                    check_num = 4.0
                else:
                    check_num = 3.0
                if get_ob_2dbc_size < check_num:
                    M = M_Box ()
                    showText = M.msgText (u'提示', u"二维码应大于%smm!" % check_num, showcolor='red')
                    M.msgBox (showText)
                    return 'UIError'
        etch_text_pol = None
        if 'obtext' in add_types:
            if self.ui.radioButton_pos.isChecked():
                etch_text_pol = 'positive'
            elif self.ui.radioButton_neg.isChecked():
                etch_text_pol = 'negative'
            if etch_text_pol is None:
                M = M_Box ()
                showText = M.msgText (u'提示', u"未勾选蚀刻字极性!", showcolor='red')
                M.msgBox (showText)
                return 'UIError'
        # === 获取step列表，并对目标step进行匹配 ===
        job_step_list = GEN.GET_STEP_LIST(job=self.job_name)
        # print job_step_list
        match_word = '|'.join(add_steps)
        prog = re.compile(match_word)
        no_need_steps = re.compile('org|orig')
        all_add_steps = []
        for step in job_step_list:
            if prog.match(step) and not no_need_steps.search(step):
                all_add_steps.append(step)
        # print all_add_steps
        # TODO 删除层别并新建层别，在循环step中会错误的跳转到其他step，比如程序运行到在set中运行加层，再切换至edit运行程序，surface pad就会加至edit中
        get_exist = GEN.LAYER_EXISTS (tmp_layer, job=self.job_name,step=self.step_name)
        if get_exist == 'yes':
            GEN.DELETE_LAYER (tmp_layer)
        GEN.CREATE_LAYER (tmp_layer)
        GEN.WORK_LAYER (tmp_layer, number=1)
        GEN.CLOSE_STEP ()
        for cur_step in all_add_steps:
            open_status = GEN.OPEN_STEP(cur_step, job=self.job_name)
            # print 'open_status%s' % open_status
            for cur_add_type in add_types:
                if cur_add_type == 'baozhuang' and not re.match(r'^set', cur_step):
                    continue
                GEN.CLEAR_LAYER()
                GEN.CHANGE_UNITS('mm')
                GEN.COM('snap_mode,mode=off')
                GEN.COM('zoom_home')

                des_layer = None
                # GEN.ADD_PAD(0,0,'s5000')
                if etch_side == 'top':
                    ad_mir = 'no'
                elif etch_side == 'bottom':
                    ad_mir = 'yes'

                if cur_add_type == 'baozhuang':
                    des_layer = baozhuang_layer
                    ad_mir = bz_mir
                else:
                    des_layer = des_etch
                GEN.WORK_LAYER (tmp_layer, number=1)
                GEN.SEL_DELETE ()
                self.add_surface_pad(x=0, y=0, type=cur_add_type, etch_big_bc_yn=etch_big_bc, etch_bc_size=get_ob_2dbc_size,mir=ad_mir)
                GEN.WORK_LAYER(des_layer,number=2)

                ref_cor_array = self.check_position(tmp_layer, des_layer, type=cur_add_type, ad_step=cur_step,
                                                    mode=add_mode, etch_big_bc_yn=etch_big_bc, ref_lyr_dict=bclyr_dict)
                # print json.dumps(ref_cor_array,indent=2)
                # GEN.PAUSE('XXXXXXXXXXXXXXXXXXX')
                if ref_cor_array:
                    # === 获取坐标，获取大小，进行添加，需判断阴阳字
                    print json.dumps(ref_cor_array,indent=2)
                    for index, item in enumerate(ref_cor_array):
                        print json.dumps(item)
                        x_cent = item['x_cent']
                        y_cent = item['y_cent']
                        x_size = item['x_size']
                        y_size = item['y_size']
                        cur_height = item['height']
                        text_x = x_cent - x_size * 0.5
                        text_y = y_cent - y_size * 0.5
                        ad_fir_pad_size = x_size * 1000
                        ad_sec_pad_size = ad_fir_pad_size - 152.4
                        margin = 500 + 152.4
                        if add_mode == 'b74':
                            # === 实际不添加此pad ===
                            # ad_sec_pad_size = ad_fir_pad_size
                            margin = 500
                        if cur_add_type in ['obtext']:
                            margin = 0
                        # ad_size = x_size
                        ad_size = (ad_fir_pad_size - margin) * 0.001

                        if cur_add_type in ['ob2dbc', 'baozhuang']:
                            text_y = text_y + margin * 0.001 * 0.5
                            text_x = x_cent - ad_size * 0.5

                        if ad_mir == 'yes':
                            text_x = x_cent + ad_size * 0.5
                        # pass
                        GEN.WORK_LAYER (des_layer, number=1)

                        # === 奥宝二维码 orb_plot_stamp_bar
                        text_type = 'orb_plot_stamp_bar'
                        text_pol = 'negative'
                        ad_ang = '0'
                        text_attr_yn = 'yes'
                        if add_mode == 'b74':
                            ad_text = 'KYMDD8MS001a1'
                            text_pol = 'positive'
                            if re.match(r'^set',cur_step):
                                ad_text = 'KSSSSSSSS01A1'
                        else:
                            ad_text = 'B2123123SSS'
                            if cur_add_type == 'obtext':
                                text_pol = etch_text_pol
                                text_type = 'orb_plot_stamp_str'
                                if index == 0:
                                    other_index = 1
                                elif index == 1:
                                    other_index = 0
                                else:
                                    M = M_Box ()
                                    showText = M.msgText (u'提示', u"非正常明码数量", showcolor='red')
                                    M.msgBox (showText)
                                cur_length = item['length']
                                three_s_up = 'no'
                                if cur_length > ref_cor_array[other_index]['length']:
                                    ad_text = 'B1001001'
                                    ad_width = cur_length * 0.125
                                    if y_cent < ref_cor_array[other_index]['y_cent']:
                                        three_s_up = 'yes'
                                else:
                                    ad_text = '-SSS'
                                    ad_width = cur_length * 0.25
                                    if y_cent > ref_cor_array[other_index]['y_cent']:
                                        three_s_up = 'yes'
                                if x_size != cur_length:
                                    # === 旋转添加时 ===
                                    ad_ang = 270
                                    if ad_mir == 'no':
                                        if three_s_up == 'no':
                                            ad_ang = 90
                                            text_x = text_x
                                            text_y = text_y + y_size
                                        else:
                                            ad_ang = 270
                                            text_x = text_x + x_size
                                    elif ad_mir == 'yes':
                                        ad_ang = 90
                                        if three_s_up == 'no':
                                            text_x = text_x
                                            text_y = text_y + y_size
                                        else:
                                            ad_ang = 270
                                            text_x = text_x - x_size

                        GEN.CHANGE_UNITS ('mm')
                        bar_type = 'ecc-200'
                        ad_matrix = 'minimal'

                        # print 'add_mode%s,add_mir%s' % (add_mode,ad_mir)
                        # GEN.PAUSE(add_mode)
                        if cur_add_type == 'ob2dbc':
                            GEN.COM('cur_atr_reset')
                            GEN.COM('cur_atr_set,attribute=.string,text=auto_barcode')
                            GEN.ADD_PAD(x_cent,y_cent,'s%s' % ad_fir_pad_size,pol='negative',attr='yes')
                            if add_mode == 'normal':
                                GEN.ADD_PAD(x_cent,y_cent,'s%s' % ad_sec_pad_size,pol='positive',attr='yes')
                            # text_x, text_y = x_cent - ad_size * 0.5, y_cent - ad_size * 0.5
                            GEN.COM('cur_atr_reset')
                            GEN.COM('cur_atr_set,attribute=.deferred')
                            GEN.COM('add_text,type=%s,polarity=%s,attributes=%s,x=%s,y=%s,text=%s,mirror=%s,angle=%s,direction=cw,'
                                    'bar_type=%s,matrix=%s,x_size=0.0002,y_size=%s,bar_marks=no' % (
                                text_type, text_pol, text_attr_yn, text_x, text_y, ad_text,ad_mir,ad_ang,bar_type,ad_matrix,ad_size))

                            # === 线路二维码需添加防焊开窗
                            if etch_side == 'top':
                                etch_sm = 'm1'
                            elif etch_side == 'bottom':
                                etch_sm = 'm2'
                            sm_open_size = ad_sec_pad_size + 50.8
                            GEN.CLEAR_LAYER()
                            GEN.AFFECTED_LAYER(etch_sm,'yes')
                            GEN.COM('cur_atr_reset')
                            GEN.COM('cur_atr_set,attribute=.string,text=auto_barcode')
                            GEN.ADD_PAD (x_cent, y_cent, 's%s' % sm_open_size, pol='positive', attr='yes')
                            GEN.CLEAR_LAYER()
                        elif cur_add_type == 'obtext':
                            ad_fontname = 'standard'
                            ad_height = cur_height
                            # ad_width = cur_length * 0.125
                            ad_factor = 0.5
                            GEN.COM('cur_atr_reset')
                            GEN.COM('cur_atr_set,attribute=.deferred')
                            GEN.COM('add_text,type=%s,polarity=%s,attributes=%s,x=%s,y=%s,text=%s,fontname=%s,x_size=%s,'
                                    'y_size=%s,mirror=%s,angle=%s,w_factor=%s' % (
                                    text_type, text_pol, text_attr_yn, text_x, text_y, ad_text,ad_fontname,ad_width,
                                    ad_height, ad_mir, ad_ang, ad_factor))
                        elif cur_add_type == 'baozhuang':
                            text_type = 'barcode'
                            # === 界面获取周期格式 ===
                            ad_text = '"\$\$"{JOB} %s' % bz_date.upper()
                            ad_background = 'no'
                            ad_bar_string = 'no'
                            ad_bar_mark = 'no'
                            ad_height = ad_size
                            text_attr_yn = 'yes'
                            GEN.COM('cur_atr_reset')
                            GEN.COM('cur_atr_set,attribute=.string,text=auto_barcode')
                            GEN.ADD_PAD(x_cent,y_cent,'s%s' % ad_fir_pad_size,pol='positive',attr='yes')
                            GEN.COM('add_text,type=%s,polarity=%s,attributes=%s,x=%s,y=%s,text=%s,mirror=%s,angle=%s,'
                                    'bar_type=%s,matrix=%s,bar_background=%s,bar_add_string=%s,bar_marks=%s,'
                                    'bar_width=0.2032,bar_height=%s' % (
                                text_type, text_pol, text_attr_yn, text_x, text_y,ad_text, ad_mir, ad_ang, bar_type,
                            ad_matrix, ad_background, ad_bar_string, ad_bar_mark, ad_height))
                        GEN.CLEAR_LAYER()
                else:
                    M = M_Box ()
                    showText = M.msgText (u'提示', u"非正常退出循环", showcolor='red')
                    M.msgBox (showText)
                    return 'Error'

            GEN.CLOSE_STEP()
        return True

    def add_surface_pad(self, x=0, y=0, ad_attr='no', ad_pol='positive', type='ob2dbc',etch_big_bc_yn = 'no',etch_bc_size='5',mir=None):
        """
        实际为surface的四边形，为了按profile选择时可以被包含进profile（而pad使用的是圆心被包含，不准确）
        :param x:
        :param y:

        :return:
        """
        if type == 'ob2dbc':
            size_x = etch_bc_size + 0.1524 + 0.5
            size_y = etch_bc_size + 0.1524 + 0.5
            # if etch_big_bc_yn == 'yes':
            #     size_x = 5.653
            #     size_y = 5.653
        elif type == 'obtext':
            size_x = x + 6.096
            size_y = y + 0.76
            x3 = size_x + 0.304
            if mir == 'yes':
                x3 = x - x3
        elif type == 'baozhuang':
            size_x = 5.5
            size_y = 5.5
        x1 = x - size_x * 0.5
        x2 = x + size_x * 0.5
        y1 = y - size_y * 0.5
        y2 = y + size_y * 0.5
        GEN.COM('add_surf_strt,surf_type=feature')
        GEN.COM('add_surf_poly_strt,x=%s,y=%s' % (x1, y1))
        GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (x1, y2))
        GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (x2, y2))
        GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (x2, y1))
        GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (x1, y1))
        GEN.COM('add_surf_poly_end')
        GEN.COM('add_surf_end,attributes=%s,polarity=%s' % (ad_attr,ad_pol))
        if type == 'obtext':
            if mir != 'yes':
                GEN.COM ('add_surf_strt,surf_type=feature')
                GEN.COM ('add_surf_poly_strt,x=%s,y=%s' % (x2, y1))
                GEN.COM ('add_surf_poly_seg,x=%s,y=%s' % (x3, y1))
                GEN.COM ('add_surf_poly_seg,x=%s,y=%s' % (x3, y2))
                GEN.COM ('add_surf_poly_seg,x=%s,y=%s' % (x2, y2))
                GEN.COM ('add_surf_poly_seg,x=%s,y=%s' % (x2, y1))
                GEN.COM ('add_surf_poly_end')
                GEN.COM ('add_surf_end,attributes=%s,polarity=%s' % (ad_attr, ad_pol))
            else:
                GEN.COM ('add_surf_strt,surf_type=feature')
                GEN.COM ('add_surf_poly_strt,x=%s,y=%s' % (x1, y1))
                GEN.COM ('add_surf_poly_seg,x=%s,y=%s' % (x3, y1))
                GEN.COM ('add_surf_poly_seg,x=%s,y=%s' % (x3, y2))
                GEN.COM ('add_surf_poly_seg,x=%s,y=%s' % (x1, y2))
                GEN.COM ('add_surf_poly_seg,x=%s,y=%s' % (x1, y1))
                GEN.COM ('add_surf_poly_end')
                GEN.COM ('add_surf_end,attributes=%s,polarity=%s' % (ad_attr, ad_pol))

    def check_position(self, tmp_layer, des_etch, type='ob2dbc', ad_step=None, mode=None, etch_big_bc_yn=None, ref_lyr_dict=None):
        """
        预添加symbol可用性检测
        :param tmp_layer: 临时层——symbol预添加层
        :param des_etch: 目标层
        :param type: ob2dbc，obtext，baozhuang 定义类型
        :param ad_step: 当前添加的step，无实际用途，由于此前测试时有step未正常跳转的Bug，此处show出查看
        :param mode: 常规还是b74系列
        :param etch_big_bc_yn: 是否添加大二维码
        :param ref_lyr_dict: 外层相关层别的dict
        :return: 坐标信息列表
        """
        # === 检查层别中内容是否在profile内
        error_list = []
        ref_cor_array = []
        GEN.FILTER_RESET ()
        GEN.COM('sel_single_feat,operation=select,x=0,y=0,tol=200,cyclic=no')
        type_cn = dict(ob2dbc='二维码', obtext='蚀刻字', baozhuang='包装码')
        GEN.PAUSE('请移动Step:%s层%s中的symbol位置，可按需更改此symbol大小，比对层别%s依此为基准添加%s' %
                  (ad_step, tmp_layer, des_etch, type_cn[type]))
        control_num = 1
        if type == 'obtext':
            control_num = 2
        GEN.CLEAR_LAYER()
        GEN.CHANGE_UNITS ('mm')
        GEN.WORK_LAYER(tmp_layer, number=1)
        GEN.CLEAR_FEAT ()
        GEN.FILTER_RESET ()
        GEN.FILTER_SET_TYP ('surface')
        GEN.FILTER_SET_PRO ('in')
        GEN.FILTER_SELECT ()
        count1 = int (GEN.GET_SELECT_COUNT ())
        if count1 != control_num:
            error_list.append(u'超出profile!|\n')
        GEN.CLEAR_FEAT ()
        if len(error_list) == 0:
            # === 检测目标层相交 ===
            if type in ['ob2dbc', 'obtext']:
                cur_layer_syms = "line;pad;arc;text"
            elif type in ['baozhuang']:
                cur_layer_syms = "line;pad;surface;arc;text"
            else:
                error_list.append(u'当前层相交检测不识别类型:%s|' % type)
            GEN.FILTER_RESET ()
            GEN.SEL_REF_FEAT (des_etch, 'touch', f_type=cur_layer_syms)
            count2 = int (GEN.GET_SELECT_COUNT ())
            if count2 > 0:
                error_list.append(u'与目标层:%s非surface相交|' % des_etch)
            GEN.CLEAR_FEAT ()

        if len(error_list) == 0:
            # === 检测其他层相交 ===
            # ref_layers = []
            if type in ['ob2dbc', 'obtext']:
                get_side = ref_lyr_dict['signal'][des_etch]
                ref_layers = [k for i in ref_lyr_dict for k in ref_lyr_dict[i] if ref_lyr_dict[i][k] == get_side and k != des_etch]
                ref_str = ';' .join(ref_layers)

                GEN.FILTER_RESET ()
                ref_layer_syms = "line;pad;surface;arc;text"
                GEN.SEL_REF_FEAT (ref_str, 'touch', f_type=ref_layer_syms)
                count3 = int (GEN.GET_SELECT_COUNT ())
                if count3 > 0:
                    error_list.append(u'与参考层:%s相交|' % ref_str)
                GEN.CLEAR_FEAT ()

            elif type in ['baozhuang']:
                # === 判断是否与参考层相交，省略写法，包含了目标层
                get_type, get_side = [(i, ref_lyr_dict[i][k]) for i in ref_lyr_dict for k in ref_lyr_dict[i] if k == des_etch][0]
                ref_layers = [k for i in ['solder_mask', 'silk_screen'] for k in ref_lyr_dict[i] if ref_lyr_dict[i][k] == get_side]

                ref_str = ';'.join (ref_layers)
                GEN.FILTER_RESET ()
                ref_layer_syms = "line;pad;surface;arc;text"
                GEN.SEL_REF_FEAT (ref_str, 'touch', f_type=ref_layer_syms)
                count3 = int (GEN.GET_SELECT_COUNT ())
                if count3 > 0:
                    error_list.append(u'与参考层:%s相交|' % ref_str)
                GEN.CLEAR_FEAT()
                if len(error_list) == 0:
                    ref_out = [k for k in ref_lyr_dict['signal'] if ref_lyr_dict['signal'][k] == get_side][0]
                    GEN.FILTER_RESET()
                    ref_layer_syms = "line;pad;arc;text"
                    GEN.SEL_REF_FEAT (ref_out, 'touch', f_type=ref_layer_syms)
                    count4 = int (GEN.GET_SELECT_COUNT ())
                    if count4 > 0:
                        error_list.append(u'与外层:%s非surface相交|' % ref_out)
                    GEN.CLEAR_FEAT()

                    GEN.FILTER_RESET()
                    ref_out_syms = "surface"
                    GEN.SEL_REF_FEAT(ref_out, 'cover', f_type=ref_out_syms, pol='positive')
                    count5 = int(GEN.GET_SELECT_COUNT())
                    if count5 != control_num:
                        error_list.append(u'包装码没有被外层:%s铜皮包含|' % ref_out)

        GEN.CLEAR_FEAT ()
        # === 检查symbol数量及symbol大小 ===
        if len (error_list) == 0:
            get_feat_num = GEN.DO_INFO ("-t layer -e  %s/%s/%s -d FEAT_HIST" % (self.job_name, ad_step, tmp_layer))
            if type == 'ob2dbc':
                if int (get_feat_num['gFEAT_HISTtotal']) != 1:
                    error_list.append (u'模式为二维码时，临时层标识数量不为1|')
            elif type == 'obtext':
                if int (get_feat_num['gFEAT_HISTtotal']) != 2:
                    error_list.append (u'模式为蚀刻码时，临时层标识数量不为2|')
            elif type == 'baozhuang':
                if int (get_feat_num['gFEAT_HISTtotal']) != 1:
                    error_list.append (u'模式为包装码时，临时层标识数量不为1|')
            if len(error_list) == 0:
                info = GEN.INFO ('-t layer -e %s/%s/%s -m script -d FEATURES -o feat_index' %(self.job_name, ad_step, tmp_layer))
                indexRegex = re.compile (r'^#(\d+)\s+#S P 0')
                for line in info:
                    if re.match (indexRegex, line):
                        match_obj = re.match (indexRegex, line)
                        index = match_obj.groups ()[0]
                        GEN.VOF()
                        GEN.COM(
                            'sel_layer_feat,operation=select,layer=%s,index=%s' % (tmp_layer, index))
                        GEN.VON()
                        count = GEN.GET_SELECT_COUNT ()
                        if count > 0:
                            get_feature = GEN.DO_INFO (
                                "-t layer -e %s/%s/%s -d LIMITS -o select" % (self.job_name, ad_step, tmp_layer), units="mm")
                            tmp_dict = dict (
                                x_size=float (get_feature['gLIMITSxmax']) - float (get_feature['gLIMITSxmin']),
                                y_size=float (get_feature['gLIMITSymax']) - float (get_feature['gLIMITSymin']),
                                x_cent=float (get_feature['gLIMITSxcenter']),
                                y_cent=float (get_feature['gLIMITSycenter']),
                            )
                            tmp_dict['length'] = max (tmp_dict['x_size'], tmp_dict['y_size'])
                            tmp_dict['height'] = min (tmp_dict['x_size'], tmp_dict['y_size'])
                            ref_cor_array.append (tmp_dict)
                            GEN.CLEAR_FEAT ()
                            if type in ['ob2dbc']:
                                if mode == 'normal':
                                    if etch_big_bc_yn == 'yes':
                                        if tmp_dict['height'] < 5 + 0.152 + 0.5:
                                            error_list.append (u'面铜大于1.18mil时，二维码大小应大于5.652mm(包含底pad)|')

                                    else:
                                        if tmp_dict['height'] < 4 + 0.1524 + 0.5:
                                            error_list.append (u'二维码大小应大于4.652mm(包含底pad)|')

                                else:
                                    if tmp_dict['height'] < 3:
                                        error_list.append (u'二维码大小应大于3mm!')

        # 检查层别中的内容是否和目标层相交
        if len(error_list) == 0:
            GEN.CLEAR_LAYER ()
            return ref_cor_array
        else:
            GEN.WORK_LAYER(des_etch,number=2)
            M = M_Box ()
            showText = M.msgText (u'提示', u"%s!" % ','.join(error_list), showcolor='red')
            M.msgBox (showText)
            return self.check_position(tmp_layer, des_etch, type=type, ad_step=ad_step, mode=mode,
                                       etch_big_bc_yn=etch_big_bc_yn, ref_lyr_dict=ref_lyr_dict)

    def add_pnl_2dbc_marK(self, related_layer):
        """
        在pnl中选取光点位置，并在2dbc-c/2dbc-s 层别添加光点
        :return:None
        """
        # 判断panel是否存在
        # 获取panel整个大小，获取坐标，放大左上角
        # 判断panel的边缘值，加2mil大小的四个点
        # 如panel对应层别没有r0对位点，从外层过滤复制
        pnlStep = 'panel'
        if GEN.STEP_EXISTS (self.job_name, pnlStep) == 'no':
            M = M_Box ()
            showText = M.msgText (u'警告', u"panel Step 不存在，不进行二维码对位光点添加")
            M.msgBox (showText)
            return False
        # 打开panel step
        GEN.OPEN_STEP (pnlStep, job=self.job_name)
        GEN.CHANGE_UNITS ('mm')
        GEN.COM('snap_mode, mode = off')

        solder_layer = ''
        # 判断防焊C面是否存在##
        if related_layer == '2dbc-c':
            solder_layer = "m1"
        elif related_layer == '2dbc-s':
            solder_layer = "m2"

        # === 增加判断，是否已添加r0.2的点，如果已添加则跳过 ===
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(related_layer, 'yes')
        GEN.FILTER_RESET()
        GEN.FILTER_SET_INCLUDE_SYMS('r0.2')
        GEN.FILTER_SELECT()
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.CLEAR_LAYER ()
            if self.ui.checkBox_manumark.isChecked():
                M = M_Box ()
                showText = M.msgText (u'警告', u"panel中层别%s 已添加二维码对位光点，跳过添加步骤" % related_layer)
                M.msgBox (showText)
            return

        if self.ui.checkBox_manumark.isChecked():
            mark_c_cor = {}
            tmp_select_layer = '___tmp_%s___' % solder_layer
            GEN.CLEAR_LAYER()
            GEN.COM ('flatten_layer,source_layer=%s,target_layer=%s' % (solder_layer, tmp_select_layer))
            GEN.WORK_LAYER(tmp_select_layer)
            GEN.MOUSE ('Please Select 4 pad use for Mark', mode='p')
            GEN.COM ('get_select_count')
            i = 1
            while int(GEN.GET_SELECT_COUNT()) != 4 and i <= 3:
                GEN.MOUSE ('Select Num Not 4,Try 3-%s Times Select 4 pad use for Mark' % i, mode='p')
                i += 1
            if i == 4:
                M = M_Box ()
                showText = M.msgText (u'警告', u"循环三次，仍未选择到光点，使用板边pad默认选择")
                M.msgBox (showText)
                GEN.CLEAR_LAYER ()
                GEN.WORK_LAYER (solder_layer)
                GEN.FILTER_RESET ()
                GEN.FILTER_SET_INCLUDE_SYMS ('sh-dwsd2014')
                GEN.FILTER_SELECT ()
                mark_c_cor = self.get_4_mark_cor(solder_layer, pnlStep)
            else:
                mark_c_cor = self.get_4_mark_cor(tmp_select_layer, pnlStep)
            # === 删除临时层别 ===
            GEN.DELETE_LAYER(tmp_select_layer)
            if len(mark_c_cor) != 4:
                M = M_Box ()
                showText = M.msgText (u'警告', u"二维码对位点参考点数量不为4，请在层别%s 中手动添加r0.2的点" % related_layer)
                M.msgBox (showText)
                return False
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER (related_layer,'yes')
            for mark_index in range(4):
                # if kk == 'top':
                GEN.ADD_PAD (float (mark_c_cor[mark_index][0]), float (mark_c_cor[mark_index][1]), 'r0.2', attr='no')
            GEN.CLEAR_LAYER ()

        else:
            GEN.CLEAR_LAYER()
            GEN.WORK_LAYER(solder_layer)
            GEN.FILTER_RESET()
            GEN.FILTER_SET_INCLUDE_SYMS('sh-dwsd2014')
            GEN.FILTER_SELECT()
            mark_c_cor = {}
            mark_c_cor = self.get_4_mark_cor(solder_layer, pnlStep)
            # pnli = GEN.DO_INFO('-t step -e %s/%s -d PROF_LIMITS, units=mm' % (self.job_name, pnlStep))
            #
            # sc_cor = GEN.INFO('-t layer -e %s/%s/%s -d FEATURES -o select, units=mm' % (self.job_name, pnlStep, solder_layer))
            # mark_c_cor = {}
            # all_sc_cor = [[float(cc.split(' ')[1]), float(cc.split(' ')[2])] for cc in sc_cor[1:]]
            # # === 按以下格式重新进行坐标分类,用于筛选出光点在长边还是短边 ===
            # half_pnl_x = float(pnli['gPROF_LIMITSxmax'])/2
            # half_pnl_y = float(pnli['gPROF_LIMITSymax'])/2
            # cor = {'down_left': [], 'down_right': [], 'up_right': [], 'up_left': []}
            # for c_cor in all_sc_cor:
            #     if c_cor[0] < half_pnl_x and c_cor[1] < half_pnl_y:
            #         cor['down_left'].append(c_cor)
            #     elif c_cor[0] > half_pnl_x and c_cor[1] < half_pnl_y:
            #         cor['down_right'].append(c_cor)
            #     elif c_cor[0] > half_pnl_x and c_cor[1] > half_pnl_y:
            #         cor['up_right'].append(c_cor)
            #     elif c_cor[0] < half_pnl_x and c_cor[1] > half_pnl_y:
            #         cor['up_left'].append(c_cor)
            # # === 2020.12.23 以下，用于取长边的对位光点 ===
            # mark_c_cor[0] = [i for i in cor['down_left'] if i[1] == min([c[1] for c in cor['down_left']])][0]
            # mark_c_cor[1] = [i for i in cor['down_right'] if i[1] == min([c[1] for c in cor['down_right']])][0]
            # mark_c_cor[2] = [i for i in cor['up_right'] if i[1] == max([c[1] for c in cor['up_right']])][0]
            # mark_c_cor[3] = [i for i in cor['up_left'] if i[1] == max([c[1] for c in cor['up_left']])][0]

            if len(mark_c_cor) != 4:
                M = M_Box ()
                showText = M.msgText (u'警告', u"二维码对位点参考点数量不为4，请在层别%s 中手动添加r0.2的点" % related_layer)
                M.msgBox (showText)
                return False
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER (related_layer,'yes')
            for mark_index in range (4):
                # if kk == 'top':
                GEN.ADD_PAD (float (mark_c_cor[mark_index][0]), float (mark_c_cor[mark_index][1]), 'r0.2', attr='no')
            GEN.CLEAR_LAYER ()
        return True

    def get_4_mark_cor(self, work_layer, work_step):
        """
        选中状态下运行此子程序，字典，字典key由0到3（左下起逆时针）
        :param work_layer:
        :param work_step:
        :return:
        """
        pnli = GEN.DO_INFO ('-t step -e %s/%s -d PROF_LIMITS, units=mm' % (self.job_name, work_step))

        sc_cor = GEN.INFO (
            '-t layer -e %s/%s/%s -d FEATURES -o select, units=mm' % (self.job_name, work_step, work_layer))
        mark_c_cor = {}
        all_sc_cor = [[float (cc.split (' ')[1]), float (cc.split (' ')[2])] for cc in sc_cor[1:]]
        # === 按以下格式重新进行坐标分类,用于筛选出光点在长边还是短边 ===
        half_pnl_x = float (pnli['gPROF_LIMITSxmax']) / 2
        half_pnl_y = float (pnli['gPROF_LIMITSymax']) / 2
        cor = {'down_left': [], 'down_right': [], 'up_right': [], 'up_left': []}
        for c_cor in all_sc_cor:
            if c_cor[0] < half_pnl_x and c_cor[1] < half_pnl_y:
                cor['down_left'].append (c_cor)
            elif c_cor[0] > half_pnl_x and c_cor[1] < half_pnl_y:
                cor['down_right'].append (c_cor)
            elif c_cor[0] > half_pnl_x and c_cor[1] > half_pnl_y:
                cor['up_right'].append (c_cor)
            elif c_cor[0] < half_pnl_x and c_cor[1] > half_pnl_y:
                cor['up_left'].append (c_cor)
        # === 2020.12.23 以下，用于取长边的对位光点 ===
        mark_c_cor[0] = [i for i in cor['down_left'] if i[1] == min ([c[1] for c in cor['down_left']])][0]
        mark_c_cor[1] = [i for i in cor['down_right'] if i[1] == min ([c[1] for c in cor['down_right']])][0]
        mark_c_cor[2] = [i for i in cor['up_right'] if i[1] == max ([c[1] for c in cor['up_right']])][0]
        mark_c_cor[3] = [i for i in cor['up_left'] if i[1] == max ([c[1] for c in cor['up_left']])][0]

        return mark_c_cor

    def get_2dbc_mm_cor(self,dc_mir,dc_angle,dc_p_x, dc_p_y,by_2dbc_size=7,by_mm_size=1.6):
        """
        用于旋转及镜像的坐标偏移计算
        :param dc_mir:镜像
        :param dc_angle:角度
        :param dc_p_x:坐标
        :param dc_p_y:坐标
        :param by_2dbc_size:二维码尺寸
        :param by_mm_size:明码尺寸
        :return:dc_m_x,dc_m_y,dc_c_x,dc_c_y 四个坐标
        """
        if dc_mir == 'no' and dc_angle == 0:
            dc_m_x, dc_m_y, dc_c_x, dc_c_y = (dc_p_x, dc_p_y - (by_2dbc_size + by_mm_size) * 0.5, dc_p_x, dc_p_y - (by_2dbc_size * 0.5 + 0.05))
        elif dc_mir == 'no' and dc_angle == 90:
            dc_m_x, dc_m_y, dc_c_x, dc_c_y = dc_p_x - (by_2dbc_size + by_mm_size) * 0.5, dc_p_y, (by_2dbc_size * 0.5 + 0.05), dc_p_y
        elif dc_mir == 'no' and  dc_angle == 180:
            dc_m_x, dc_m_y, dc_c_x, dc_c_y = dc_p_x, dc_p_y + (by_2dbc_size + by_mm_size) * 0.5, dc_p_x, dc_p_y + (by_2dbc_size * 0.5 + 0.05)
        elif dc_mir == 'no'  and  dc_angle == 270:
            dc_m_x, dc_m_y, dc_c_x, dc_c_y = dc_p_x + (by_2dbc_size + by_mm_size) * 0.5, dc_p_y, dc_p_x + (by_2dbc_size * 0.5 + 0.05), dc_p_y
        elif dc_mir == 'yes'and dc_angle == 0 :
            dc_m_x, dc_m_y, dc_c_x, dc_c_y = dc_p_x, (by_2dbc_size + by_mm_size) * 0.5, dc_p_x, dc_p_y -  (by_2dbc_size * 0.5 + 0.05)
        elif dc_mir == 'yes' and dc_angle == 90:
            dc_m_x, dc_m_y, dc_c_x, dc_c_y = (dc_p_x + (by_2dbc_size + by_mm_size) * 0.5, dc_p_y, dc_p_x + (by_2dbc_size * 0.5 + 0.05), dc_p_y)
        elif dc_mir == 'yes' and  dc_angle == 180:
            dc_m_x, dc_m_y, dc_c_x, dc_c_y = dc_p_x, dc_p_y + (by_2dbc_size + by_mm_size) * 0.5, dc_p_x, dc_p_y + (by_2dbc_size * 0.5 + 0.05)
        elif dc_mir == 'yes' and  dc_angle == 270:
            dc_m_x, dc_m_y, dc_c_x, dc_c_y = dc_p_x - (by_2dbc_size + by_mm_size) * 0.5, dc_p_y, dc_p_x - (by_2dbc_size * 0.5 + 0.05), dc_p_y
        return dc_m_x,dc_m_y,dc_c_x,dc_c_y

    def getMinMaxCor(self, FeatInfo):
        # 获取层别中所有最小值，最大值（单独定义函数）
        # 通过传入的层别物件进行最大值最小值分类
        # allFeatureInfo = self.getLayerFeature(pnlStep,pnlRoutLayer)
        # print json.dumps(FeatInfo,indent=1)
        print json.dumps (FeatInfo, sort_keys=True, indent=2, separators=(',', ': '))

        x1cor = [float (x['xs']) for x in FeatInfo if x['type'] == 'line']
        x2cor = [float (x['xe']) for x in FeatInfo if x['type'] == 'line']
        xcor = x1cor + x2cor
        xmin = min (xcor)
        xmax = max (xcor)
        y1cor = [float (x['ys']) for x in FeatInfo if x['type'] == 'line']
        y2cor = [float (x['ye']) for x in FeatInfo if x['type'] == 'line']
        ycor = y1cor + y2cor
        ymin = min (ycor)
        ymax = max (ycor)
        return xmin, xmax, ymin, ymax

    def reset_genesis_config(self, value=1):
        # --重置config参数
        GEN.VOF ()
        GEN.COM ('config_edit,name=gen_line_skip_post_hooks,value=%s,mode=user' % value)
        GEN.COM ('config_edit,name=gen_line_skip_pre_hooks,value=%s,mode=user' % value)
        GEN.VON ()

    def main_run(self):
        # 20250422 在周期visible的时候 先判断周期是否为空
        if self.ui.comboBox_date.isVisible() and self.ui.comboBox_date.currentText() == '':
            M = M_Box()
            showText = M.msgText(u'提示', u"请选择周期格式", showcolor='red')
            M.msgBox(showText)
            return
        # 获取界面数据
        #  -添加层别列表获取
        if self.supply != 'aobao':
            self.addLayerList = [it.text () for it in self.ui.listWidget_layerlist.selectedItems ()]
            if len (self.addLayerList) == 0:
                M = M_Box ()
                showText = M.msgText (u'提示', u"未选择输出层别，请选择!", showcolor='green')
                M.msgBox (showText)
                return

            # 判断长度不能小于高度
            if float (self.barcode_x) - float (self.barcode_y) < 0:
                M = M_Box ()
                showText = M.msgText (u'警告', u"长度不应小于宽度，请选择!", showcolor='red')
                M.msgBox (showText)
                return

            # --添加监控系列防呆 AresHe 2021.9.13
            client_num = self.job_name[1:4]
            # # --新增多层、HDI A86、A81系列属性    AresHe 2021.9.13
            # if self.ui.comboBox_supply.currentText() == u'A86文字喷墨(MLB)' or self.ui.comboBox_supply.currentText() == u'A86文字喷墨(HDI)':
            #     if client_num != "a86":
            #         M = M_Box()
            #         showText = M.msgText(u'警告', u"当前料号不是A86系列,请重新选择!", showcolor='red')
            #         M.msgBox(showText)
            #         return
            # elif self.ui.comboBox_supply.currentText() == u'A81文字喷墨(HDI)':
            #     if client_num != 'a81':
            #         M = M_Box()
            #         showText = M.msgText(u'警告', u"当前料号不是A81系列,请重新选择!", showcolor='red')
            #         M.msgBox(showText)
            #         return
        self.reset_genesis_config (value=2)
        self.hide ()
        get_result = 'ok'
        if self.supply not in  ['shengdakang', 'aobao']:
            self.Create_symbol (mode=self.supply)
            self.add_symbol (self.addLayerList)

            if self.supply == 'hanyin':
                self.Create_symbol (mode='hanyin', add_pnl='yes')
                self.add_pnl_symbol (self.addLayerList)
        elif self.supply == 'shengdakang':
            # 升达康镭雕二维码添加过程
            get_result = self.add_2dbc()
        elif self.supply == 'aobao':
            get_result = self.add_ob_2dbc ()
        # 程序的完成提醒
        M = M_Box ()
        if get_result == "UIError":
            self.show()
            return
        elif get_result == "Error":
            showText = M.msgText (u'提示', u"程序运行过程中有报警，运行结束!", showcolor='red')
        else:
            showText = M.msgText (u'提示', u"程序运行完成!", showcolor='green')
        M.msgBox (showText)
        self.close ()
        sys.exit(0)

class PainArea (QtGui.QWidget):
    def __init__(self):
        super (PainArea, self).__init__ ()
        self.setPalette (QtGui.QPalette (QtCore.Qt.white))
        self.setAutoFillBackground (True)
        self.setMinimumSize (50, 50)

        self.scalex = 1
        self.scaley = 1
        self.angle = 0
        self.translate = 0
        self.shear = 0
        self.xdis = 50
        self.ydis = 50
        self.mir = 'no'

    def setScale(self, x, y):
        self.scalex = x
        self.scaley = y
        self.update ()

    def setTranslate(self, x):
        self.translate = x
        self.update ()

    def setRotate(self, x):
        self.angle = x
        self.update ()

    def setShear(self, x):
        self.shear = (x - 10.0) / 10.0
        self.update ()

    def setRect(self, x, y):
        self.xdis = x
        self.ydis = y
        self.update ()

    def setMir(self, mir):
        self.mir = mir
        self.update ()

    def paintEvent(self, e):
        p = QtGui.QPainter (self)
        p.translate (50, 50)
        path = QtGui.QPainterPath ()
        p.rotate (self.angle)
        p.scale (self.scalex, self.scaley)
        p.translate (self.translate, self.translate)
        # p.shear(self.shear, self.shear)
        # p.shear(10, self.shear)
        p.setPen (QtCore.Qt.blue)
        drawfont = QtGui.QFont ('Arial', 40)
        p.setFont (drawfont)
        # p.drawText(-18, 20, "F")
        p.setPen (QtGui.QPen (QtCore.Qt.blue, 2))
        if self.mir == 'no':
            p.drawLine (-15, -15, -15, 15)
            p.drawLine (-15, 0, 0, 0)
            p.drawLine (-15, -15, 15, -15)
        elif self.mir == 'yes':
            p.drawLine (15, -15, 15, 15)
            p.drawLine (15, 0, 0, 0)
            p.drawLine (15, -15, -15, -15)
        # p.setPen (QtGui.QPen (QtCore.Qt.blue, 20))
        # rect = QtCore.QRect (-self.xdis * 0.5, -self.ydis * 0.5, self.xdis * 0.5, self.ydis * 0.5)
        # p.drawRect (rect)

        p.drawRect (-self.xdis * 0.5, -self.ydis * 0.5, self.xdis, self.ydis)
        p.drawPath (path)


# # # # --程序入口
if __name__ == "__main__":
    app = QtGui.QApplication (sys.argv)
    myapp = MainWindowShow ()
    myapp.show ()
    app.exec_ ()
    sys.exit (0)
