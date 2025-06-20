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
# 版本V3.6  Chao.Song 2021.10.28
# 1.增加奥宝类二维码，蚀刻二维码，明码，包装二维码，B74系列二维码
# ---------------------------------------------------------#


import sys
import os
import re
import json
reload(sys)
sys.setdefaultencoding('utf8')
dirname, filename = os.path.split(os.path.abspath(sys.argv[0]))

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
import OBUIV1 as Mui

from PyQt4 import QtCore, QtGui, Qt
import platform

import string

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    # === TODO 本地测试阶段 ===
    sys.path.append (r"D:/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genCOM_26
import Oracle_DB

GEN = genCOM_26.GEN_COM()

from get_erp_job_info import get_cu_weight

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


class M_Box(QtGui.QWidget):
    """
    MesageBox提示界面
    """

    def __init__(self, parent=None):
        QtGui.QMessageBox.__init__(self, parent)
        self.setWindowFlags(Qt.Qt.WindowStaysOnTopHint)
        self.setGeometry(700, 300, 0, 0)

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


class MainWindowShow(QtGui.QMainWindow):
    """
    窗体主方法
    """

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        # 初始数据
        self.AppVer = '1.0'
        # self.symbol_attr = 250
        self.job_name = os.environ.get('JOB')
        self.JOB_SQL = self.job_name.upper().split('-')[0] if '-' in self.job_name else self.job_name.upper()

        self.step_name = os.environ.get('STEP')
        self.supply = 'aobao'
        # --Oracle相关参数定义
        self.DB_O = Oracle_DB.ORACLE_INIT()
        self.dbc_h = self.DB_O.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
                                          username='GETDATA', passwd='InplanAdmin')
        self.bc_data, self.dc_side, self.dc_type = self.get_InPlan_bc_side()

        self.layer_Info = self.DB_O.getLayerThkInfo(self.dbc_h,self.JOB_SQL)
        print json.dumps(self.layer_Info, indent=2)
        if self.dbc_h:
            self.DB_O.DB_CLOSE(self.dbc_h)
        if self.job_name and self.step_name:
            pass
        else:
            M = M_Box()
            showText = M.msgText(u'提示', u"必须打开料号及需添加的Step,程序退出!", showcolor='red')
            M.msgBox(showText)
            exit(0)
        # self.barcode_symbol = 'barcode%sx%s' % (self.barcode_x, self.barcode_y)
        self.ui = Mui.Ui_MainWindow()
        self.ui.setupUi(self)        
        self.addUiDetail()
        self.set_UI_by_SQL()
        self.all_add_steps, self.baozhuang_steps = self.set_UI_by_JOB()
        self.update()
        
        self.ui.checkBox_ob2dbc.setText(u"追溯二维码")
        self.ui.comboBox_mm.setEnabled(False)
        self.ui.comboBox_bz_date.setEnabled(False)

    def get_InPlan_bc_side(self):
        """
        在inplan数据库中获取二维码明码面次
        :return:
        """

        # self.lamination,self.lam_rout = self.get_lamination_info()
        if not self.dbc_h:
            M = M_Box()
            showText = M.msgText(u'错误', u'InPlan无法连接，自行确认包装码信息', showcolor='red')
            M.msgBox(showText)
            return
        # ====1.获取二维码面次 ===
        sql1 = """
            SELECT
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
                and p.intname = 'JOB'""" % self.JOB_SQL

        job_data = self.DB_O.SELECT_DIC(self.dbc_h, sql1)
        bc_side_dict = job_data[0]
        # === 获取周期面次 ===
        sql2 = """
            SELECT
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
                and p.fldname = 'DC_SIDE_'
                and p.enum=job.DC_SIDE_
                and p.intname = 'JOB'		""" % self.JOB_SQL
        job_data2 = self.DB_O.SELECT_DIC(self.dbc_h, sql2)
        dc_side_dict = job_data2[0]
        # === 获取周期类型 ===
        sql3 = """
            SELECT
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
                and p.fldname = 'DC_TYPE_'
                and p.enum=job.DC_TYPE_
                and p.intname = 'JOB'""" % self.JOB_SQL
        job_data3 = self.DB_O.SELECT_DIC(self.dbc_h, sql3)
        dc_type_dict = job_data3[0]

        return bc_side_dict, dc_side_dict, dc_type_dict

    def set_UI_by_SQL(self):
        layer_value = self.bc_data["VALUE"]
        # print self.ui.layer_bc.count()
        if self.bc_data["VALUE"] in ['防焊C面', '防焊S面', '蚀刻C面', '蚀刻S面']:
            # self.ui.checkBox_set.setChecked(True)
            des_value = None
            if 'C面' in layer_value:
                des_value = u'正面'
            elif 'S面' in layer_value:
                des_value = u'反面'
            for i in range(self.ui.side_mm.count()):
                if self.ui.side_mm.itemText(i) == des_value:
                    self.ui.side_mm.setCurrentIndex(i)
            for i in range(self.ui.side_bc.count()):
                if self.ui.side_bc.itemText(i) == des_value:
                    self.ui.side_bc.setCurrentIndex(i)
            type_value = None

            if '蚀刻' in layer_value:
                type_value = u'线路'
            if '防焊' in layer_value:
                type_value = u'防焊'
            for i in range(self.ui.layer_bc.count()):
                if self.ui.layer_bc.itemText(i) == type_value:
                    self.ui.layer_bc.setCurrentIndex(i)
                if self.ui.layer_mm.itemText(i) == type_value:
                    self.ui.layer_mm.setCurrentIndex(i)

        if self.dc_side["VALUE"] in ['防焊C面', '防焊S面', '文字C面', '文字S面']:
            get_dc_value = self.dc_side["VALUE"]
            dc_value = None
            if 'C面' in get_dc_value:
                dc_value = u'正面'
            elif 'S面' in get_dc_value:
                dc_value = u'反面'
            for i in range(self.ui.side_bz.count()):
                if self.ui.side_bz.itemText(i) == dc_value:
                    self.ui.side_bz.setCurrentIndex(i)
            type_value = None
            if '文字' in get_dc_value:
                type_value = u'文字'
            if '防焊' in get_dc_value:
                type_value = u'防焊'
            for i in range(self.ui.layer_bz.count()):
                if self.ui.layer_bz.itemText(i) == type_value:
                    self.ui.layer_bz.setCurrentIndex(i)

        if self.dc_type['VALUE'] in ['WWYY', "YYWW"]:
            get_dc_type = self.dc_type['VALUE']
            type_value = get_dc_type.replace("WW", "$$WW").replace("YY", "$$YY")
            for i in range(self.ui.comboBox_bz_date.count()):
                if self.ui.comboBox_bz_date.itemText(i) == type_value:
                    self.ui.comboBox_bz_date.setCurrentIndex(i)
        else:
            get_dc_type = self.dc_type['VALUE']
            type_value = get_dc_type.replace("WW", "$$WW").replace("YY", "$$YY").replace("DD", "$$DD")
            self.ui.bz_other_date.setText(type_value)  

        get_text = self.ui.label_tips.text()
        self.ui.label_tips.setText(
            _translate("MainWindow",
                       "%s\n5.InPlan中周期面次为%s.周期格式为%s.请按需选择包装码" % (get_text,self.dc_side['VALUE'],self.dc_type["VALUE"]),None))

    def set_UI_by_JOB(self):
        """
        根据料号类型设定界面，并根据step存在情况，设定是否勾选
        :return: 所有可添加明码二维码的step，包装可添加的step
        """
        cus_name = self.job_name[1:4]
        if cus_name in ['b74']:
            self.ui.radioButton_b74.animateClick()
        else:
            self.ui.radioButton_normal.animateClick()

        # need_add_step = ['edit', 'set', 'icg']
        # === 获取step列表，并对目标step进行匹配 ===
        job_step_list = GEN.GET_STEP_LIST(job=self.job_name)
        # print job_step_list
        # match_word = '|'.join(need_add_step)
        # prog = re.compile(match_word)
        data_info = get_cu_weight(self.job_name.upper())
        self.cu_weight = 25
        if data_info:            
            for info in data_info:
                if info[1] == "l1":                    
                    self.cu_weight = info[7]
                    
        if self.cu_weight > 50:
            M = M_Box()
            showText = M.msgText(u'提示', u"面铜超出50UM则提示需mi评审", showcolor='red')
            M.msgBox(showText)                      
                    
        edit_exist = 'no'
        set_exist = 'no'
        icg_exist = 'no'
        no_need_steps = re.compile('org|orig')
        all_add_steps = []
        baozhuang_steps = []
        for step in job_step_list:
            if re.match('edit', step) and not no_need_steps.search(step):
                edit_exist = 'yes'
                all_add_steps.append(step)
            elif re.match('set', step) and not no_need_steps.search(step):
                set_exist = 'yes'
                all_add_steps.append(step)
                baozhuang_steps.append(step)
            elif re.match('icg', step) and not no_need_steps.search(step):                
                icg_exist = 'yes'
                all_add_steps.append(step)
        
        if edit_exist == 'no':
            self.ui.checkBox_edit.setChecked(False)
            self.ui.checkBox_edit.setDisabled(True)
        if icg_exist == 'no':
            self.ui.checkBox_icg.setChecked(False)
            self.ui.checkBox_icg.setDisabled(True)
        if set_exist == 'no':
            self.ui.checkBox_set.setChecked(False)
            self.ui.checkBox_set.setDisabled(True)
            
        return all_add_steps,baozhuang_steps

    def addUiDetail(self):
        """
        在原框架基础上继续加载窗体
        :return:None
        """
        my_regex_abc = QtCore.QRegExp("[\$WYMD]{1,12}")
        my_validator = QtGui.QRegExpValidator(my_regex_abc, self.ui.bz_other_date)
        self.ui.bz_other_date.setValidator(my_validator)

        self.ui.label_bottom.setText(
            _translate("MainWindow", "版权所有：胜宏科技 版本：%s" % (self.AppVer), None))
        if self.supply == 'aobao':
            self.ui.label_tips.setText(
                _translate("MainWindow",
                           "说明:\n1.包装码默认set，负性;\n2.常规二维码默认为负,同步添加底套铜及底pad;\n3.B74二维码默认为正;\n4.临时层别不可变动pad大小", None))
        QtCore.QObject.connect(self.ui.radioButton_b74, QtCore.SIGNAL("clicked(bool)"), self.ui_connect)
        QtCore.QObject.connect(self.ui.pushButton_apply, QtCore.SIGNAL("clicked()"), self.main_run)
        QtCore.QObject.connect(self.ui.comboBox_bz_date, QtCore.SIGNAL("currentIndexChanged(int)"), self.chg_bz_date)
        self.ui.mm_polarity.currentIndexChanged.connect(self.change_text_size)
        
    def change_text_size(self, index):
        self.ui.comboBox_mm.setEnabled(True)
        if index == 1:
            if self.ui.comboBox_mm.findText("2/6", QtCore.Qt.MatchContains) < 0:                
                self.ui.comboBox_mm.addItem(_fromUtf8(""))
                self.ui.comboBox_mm.setItemText(2, _translate("MainWindow", "2/6制_4.4704x0.5588mm", None))
                
            if self.cu_weight <= 25:
                self.ui.comboBox_mm.setCurrentIndex(2)
            else:
                self.ui.comboBox_mm.setCurrentIndex(1)
                
        if index == 2:
            self.ui.comboBox_mm.removeItem(2)
            if self.cu_weight <= 25:
                self.ui.comboBox_mm.setCurrentIndex(1)
            else:
                self.ui.comboBox_mm.setCurrentIndex(0) 

    def chg_bz_date(self):
        if self.ui.comboBox_bz_date.currentText() == u'其他':
            self.ui.bz_other_date.setEnabled(True)
        else:
            self.ui.bz_other_date.setEnabled(False)

    def ui_connect(self):

        cus_name = self.job_name[1:4]
        if cus_name in ['b74'] and self.ui.radioButton_normal.isChecked():
            M = M_Box()
            showText = M.msgText(u'警告', u"b74系列不可勾选普通二维码，返回界面!", showcolor='red')
            M.msgBox(showText)
            self.ui.radioButton_b74.animateClick()
            return
        if cus_name not in ['b74'] and self.ui.radioButton_b74.isChecked():
            M = M_Box()
            showText = M.msgText(u'警告', u"不是b74系列，勾选了b74!", showcolor='red')
            M.msgBox(showText)
        if self.ui.radioButton_b74.isChecked():
            self.ui.checkBox_baozhuang.setChecked(False)
            self.ui.checkBox_obmm.setChecked(False)

        if self.ui.checkBox_ob2dbc.isChecked():
            self.ui.widget_ob_bc.setEnabled(True)
        else:
            self.ui.widget_ob_bc.setEnabled(False)

        if self.ui.checkBox_obmm.isChecked():
            self.ui.widget_ob_mm.setEnabled(True)
        else:
            self.ui.widget_ob_mm.setEnabled(False)

        if self.ui.checkBox_baozhuang.isChecked():
            self.ui.widget_ob_bz.setEnabled(True)
        else:
            self.ui.widget_ob_bz.setEnabled(False)

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

    def add_ob_2dbc(self):
        """
        蚀刻二维码明码，文字的包装分堆码
        :return:
        """
        # === 使用默认大小添加至辅助层，需要CAM移动，并添加程序防呆，如位置可行则进行线路层的添加，
        add_mode = None
        if self.ui.radioButton_b74.isChecked():
            add_mode = 'b74'
        elif self.ui.radioButton_normal.isChecked():
            add_mode = 'normal'
        if not add_mode:
            M = M_Box()
            showText = M.msgText(u'提示', u"未勾选添加类型!", showcolor='red')
            M.msgBox(showText)
            return 'UIError'
        add_types = []
        if self.ui.checkBox_ob2dbc.isChecked():
            add_types.append('ob2dbc')
        if self.ui.checkBox_obmm.isChecked():
            add_types.append('obtext')
        if self.ui.checkBox_baozhuang.isChecked():
            add_types.append('baozhuang')
        if len(add_types) == 0:
            M = M_Box()
            showText = M.msgText(u'提示', u"未勾选添加内容!", showcolor='red')
            M.msgBox(showText)
            return 'UIError'
        bzside = None
        bz_layer = None
        bz_date = None
        if self.ui.checkBox_baozhuang.isChecked():
            if self.ui.side_bz.currentText() == u'正面':
                bzside = 'top'
                bz_mir = 'no'
            elif self.ui.side_bz.currentText() == u'反面':
                bzside = 'bottom'
                bz_mir = 'yes'
            else:
                M = M_Box()
                showText = M.msgText(u'提示', u"包装未选择面次!", showcolor='red')
                M.msgBox(showText)
                return 'UIError'
            if self.ui.layer_bz.currentText() == u'防焊':
                bz_layer = 'solder_mask'
            elif self.ui.layer_bz.currentText() == u'文字':
                bz_layer = 'silk_screen'
            else:
                M = M_Box()
                showText = M.msgText(u'提示', u"包装未选择层别!", showcolor='red')
                M.msgBox(showText)
                return 'UIError'
            if self.ui.comboBox_bz_date.currentText() == u'其他':
                bz_date = str(self.ui.bz_other_date.text())
            else:
                bz_date = str(self.ui.comboBox_bz_date.currentText())

        # === 获取外层，防焊，文字
        bclyr_dict = self.get_all_outer_layers()
        # print json.dumps(bclyr_dict, indent=2)
        # print add_types
        baozhuang_layer = None
        if 'baozhuang' in add_types:
            try:
                baozhuang_layer = [i for i in bclyr_dict[bz_layer] if bclyr_dict[bz_layer][i] == bzside][0]
            except IndexError:
                M = M_Box()
                showText = M.msgText(u'提示', u"料号中无选择的包装层!", showcolor='red')
                M.msgBox(showText)
                return 'UIError'
        etch_side = None
        bc_layer = None
        # === 判断系列，用于添加内容的确定
        if self.ui.checkBox_ob2dbc.isChecked():
            if self.ui.side_bc.currentText() == u'正面':
                etch_side = 'top'
            elif self.ui.side_bc.currentText() == u'反面':
                etch_side = 'bottom'
            else:
                M = M_Box()
                showText = M.msgText(u'提示', u"未选择二维码添加面次!", showcolor='red')
                M.msgBox(showText)
                return 'UIError'
            if self.ui.layer_bc.currentText() == u'防焊':
                bc_layer = 'solder_mask'
            elif self.ui.layer_bc.currentText() == u'线路':
                bc_layer = 'signal'
            else:
                M = M_Box()
                showText = M.msgText(u'提示', u"二维码未选择层别!", showcolor='red')
                M.msgBox(showText)
                return 'UIError'
        try:
            des_etch = [i for i in bclyr_dict[bc_layer] if bclyr_dict[bc_layer][i] == etch_side][0]
        except (IndexError, KeyError):
            des_etch = None
        mm_side = None
        mm_layer = None
        if self.ui.checkBox_obmm.isChecked():
            if self.ui.side_mm.currentText() == u'正面':
                mm_side = 'top'
            elif self.ui.side_mm.currentText() == u'反面':
                mm_side = 'bottom'
            else:
                M = M_Box()
                showText = M.msgText(u'提示', u"未选择明码添加面次!", showcolor='red')
                M.msgBox(showText)
                return 'UIError'
            if self.ui.layer_mm.currentText() == u'防焊':
                mm_layer = 'solder_mask'
            elif self.ui.layer_mm.currentText() == u'线路':
                mm_layer = 'signal'
            else:
                M = M_Box()
                showText = M.msgText(u'提示', u"明码未选择层别!", showcolor='red')
                M.msgBox(showText)
                return 'UIError'
        if des_etch is None:
            try:
                des_etch = [i for i in bclyr_dict[mm_layer] if bclyr_dict[mm_layer][i] == mm_side][0]
            except (IndexError, KeyError):
                des_etch = None

        if mm_side is not None and etch_side is not None:
            if mm_side != etch_side:
                M = M_Box()
                showText = M.msgText(u'提示', u"二维码及明码同时添加，选择面次应相同!", showcolor='red')
                M.msgBox(showText)
                return 'UIError'
        if etch_side is None:
            etch_side = mm_side
        if mm_layer is not None and bc_layer is not None:
            if mm_layer != bc_layer:
                M = M_Box()
                showText = M.msgText(u'提示', u"二维码及明码同时添加，选择层别类型应相同!", showcolor='red')
                M.msgBox(showText)
                return 'UIError'
        if bc_layer is None and mm_layer is not None:
            bc_layer = mm_layer

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
            M = M_Box()
            showText = M.msgText(u'提示', u"未选择添加Step!", showcolor='red')
            M.msgBox(showText)
            return 'UIError'
        get_ob_2dbc_size = None
        if 'ob2dbc' in add_types:
            # get_ob_2dbc_size = self.ui.lineEdit_ob2dbc.text()
            get_ob_2dbc_size = self.ui.comboBox_bc.currentText()
            get_ob_2dbc_size = GEN.convertToNumber(str(get_ob_2dbc_size))
            # print get_ob_2dbc_size
            # print type(get_ob_2dbc_size)

        etch_text_pol = None
        get_text_size = None
        if 'obtext' in add_types:
            if self.ui.mm_polarity.currentText() == u'阳字':
                etch_text_pol = 'positive'
            elif self.ui.mm_polarity.currentText() == u'阴字':
                etch_text_pol = 'negative'
            else:
                M = M_Box()
                showText = M.msgText(u'提示', u"未勾选明码字极性!", showcolor='red')
                M.msgBox(showText)
                return 'UIError'
            get_text_size = self.ui.comboBox_mm.currentText()
        # print str(get_text_size)
        if get_text_size:
            get_text_size = str(get_text_size).split('_')[1].strip('m')
            # print get_text_size
        select_step_types = "|".join(add_steps)
        step_reg = re.compile(select_step_types)
        cur_all_add_steps = []
        for astep in self.all_add_steps:
            if step_reg.match(astep):
                cur_all_add_steps.append(astep)

        # TODO 删除层别并新建层别，在循环step中会错误的跳转到其他step，比如程序运行到在set中运行加层，再切换至edit运行程序，surface pad就会加至edit中
        get_exist = GEN.LAYER_EXISTS(tmp_layer, job=self.job_name, step=self.step_name)
        if get_exist == 'yes':
            GEN.DELETE_LAYER(tmp_layer)
        GEN.CREATE_LAYER(tmp_layer)
        GEN.WORK_LAYER(tmp_layer, number=1)
        GEN.CLOSE_STEP()
        #  === 类1为明码二维码，类2为包装码，step归类使用一次循环。
        f_all_step = list(set(cur_all_add_steps+self.baozhuang_steps))
        
        text_size_index = self.ui.comboBox_mm.currentIndex()

        for cur_step in f_all_step:
            open_status = GEN.OPEN_STEP(cur_step, job=self.job_name)
            # print 'open_status%s' % open_status
            for cur_add_type in add_types:
                if cur_add_type == 'baozhuang' and not re.match(r'^set', cur_step):
                    continue
                if cur_add_type != 'baozhuang' and cur_step not in cur_all_add_steps:
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
                GEN.WORK_LAYER(tmp_layer, number=1)
                GEN.SEL_DELETE()
                if cur_add_type == 'obtext':
                    # 奥宝明码需将字高字宽按面铜厚度来确定 20221206 by lyh
                    aobao_x_size, aobao_y_size, aobao_factor,line_width,two_surface_spacing = self.get_add_text_size(self.job_name, text_size_index)                
                    self.add_surface_pad_new(self.job_name, cur_step, tmp_layer,
                                             etch_text_pol, ad_mir, "no",
                                             aobao_x_size, aobao_y_size, aobao_factor,
                                             line_width, two_surface_spacing)
                else:
                    self.add_surface_pad(x=0, y=0, type=cur_add_type, etch_bc_size=get_ob_2dbc_size, etch_text_size=get_text_size, mir=ad_mir)
                GEN.WORK_LAYER(des_layer, number=2)

                ref_cor_array = self.check_position(tmp_layer, des_layer, type=cur_add_type, ad_step=cur_step,
                                                    mode=add_mode, ref_lyr_dict=bclyr_dict,des_type=bc_layer)

                if ref_cor_array:
                    # === 获取坐标，获取大小，进行添加，需判断阴阳字
                    # print json.dumps(ref_cor_array, indent=2)
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
                        GEN.WORK_LAYER(des_layer, number=1)

                        # === 奥宝二维码 orb_plot_stamp_bar
                        text_type = 'orb_plot_stamp_bar'
                        text_pol = 'negative'
                        ad_ang = '0'
                        text_attr_yn = 'yes'
                        if add_mode == 'b74':
                            ad_text = 'KYMDD8MS001a1'
                            text_pol = 'positive'
                            if re.match(r'^set', cur_step):
                                ad_text = 'KSSSSSSSS01A1'
                        else:
                            # 183系列固定修改  http://192.168.2.120:82/zentao/story-view-7290.html ynh
                            if self.job_name[1:4] == '183':
                                ad_text = '2003000088A129YMD000SSS01'
                            else:
                                ad_text = 'H1SSSSSS11111SSS'
                            if cur_add_type == 'obtext':
                                text_pol = etch_text_pol
                                text_type = 'orb_plot_stamp_str'
                                if index == 0:
                                    other_index = 1
                                elif index == 1:
                                    other_index = 0
                                else:
                                    M = M_Box()
                                    showText = M.msgText(u'提示', u"非正常明码数量", showcolor='red')
                                    M.msgBox(showText)
                                cur_length = item['length']
                                three_s_up = 'no'
                                if cur_length > ref_cor_array[other_index]['length']:
                                    ad_text = 'B1001001'                                    
                                    ad_width = cur_length * 0.125
                                    if y_cent < ref_cor_array[other_index]['y_cent']:
                                        three_s_up = 'yes'
                                else:
                                    # ad_text = '-SSS'
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

                        GEN.CHANGE_UNITS('mm')
                        bar_type = 'ecc-200'
                        ad_matrix = 'minimal'

                        # print 'add_mode%s,add_mir%s' % (add_mode,ad_mir)
                        # GEN.PAUSE(add_mode)
                        if cur_add_type == 'ob2dbc':
                            GEN.COM('cur_atr_reset')
                            GEN.COM('cur_atr_set,attribute=.string,text=auto_barcode')
                            GEN.ADD_PAD(x_cent, y_cent, 's%s' % ad_fir_pad_size, pol='negative', attr='yes')
                            if add_mode == 'normal':
                                GEN.ADD_PAD(x_cent, y_cent, 's%s' % ad_sec_pad_size, pol='positive', attr='yes')
                            # text_x, text_y = x_cent - ad_size * 0.5, y_cent - ad_size * 0.5
                            GEN.COM('cur_atr_reset')
                            GEN.COM('cur_atr_set,attribute=.deferred')
                            # GEN.COM(
                            #     'add_text,type=%s,polarity=%s,attributes=%s,x=%s,y=%s,text=%s,mirror=%s,angle=%s,direction=cw,'
                            #     'bar_type=%s,matrix=%s,x_size=0.0002,y_size=%s,bar_marks=no' % (
                            #         text_type, text_pol, text_attr_yn, text_x, text_y, ad_text, ad_mir, ad_ang,
                            #         bar_type, ad_matrix, ad_size))
                            # === TODO 按比例添加如下 === 2021.12.20 == ad_size 应该为比例 ===
                            # 二维码尺寸按添加的PAD尺寸调整一下
                            text_size = str(get_ob_2dbc_size - 0.055)
                            GEN.COM('add_text,type=%s,polarity=%s,attributes=%s,x=%s,y=%s,text=%s,mirror=%s,angle=%s,'
                                    'bar_type=%s,matrix=%s,x_size=%s,y_size=%s,w_factor=%s,bar_marks=no' % (
                                        text_type, text_pol, text_attr_yn, text_x, text_y, ad_text, ad_mir, ad_ang,
                                        bar_type, ad_matrix, text_size,text_size,'2'))
                            # GEN.COM('add_text,type=%s,polarity=%s,attributes=%s,x=%s,y=%s,text=%s,mirror=%s,angle=%s,'
                            #         'bar_type=%s,matrix=%s,x_size=4.445,y_size=4.445,w_factor=%s,bar_marks=no' % (
                            #          text_type, text_pol, text_attr_yn, text_x, text_y, ad_text, ad_mir, ad_ang,
                            #          bar_type, ad_matrix, '2'))
                            # === 线路二维码需添加防焊开窗
                            if des_layer not in ["m1", "m2"]:                                
                                if etch_side == 'top':
                                    etch_sm = 'm1'
                                elif etch_side == 'bottom':
                                    etch_sm = 'm2'
                                sm_open_size = ad_sec_pad_size + 50.8
                                GEN.CLEAR_LAYER()
                                GEN.AFFECTED_LAYER(etch_sm, 'yes')
                                GEN.COM('cur_atr_reset')
                                GEN.COM('cur_atr_set,attribute=.string,text=auto_barcode')
                                GEN.ADD_PAD(x_cent, y_cent, 's%s' % sm_open_size, pol='positive', attr='yes')
                                GEN.CLEAR_LAYER()
                                
                        elif cur_add_type == 'obtext':
                            ad_fontname = 'standard'
                            ad_height = cur_height
                            # ad_width = cur_length * 0.125
                            ad_factor = None
                            #if abs(cur_height - 0.5588) < 0.001:
                                #ad_factor = 0.25
                            #elif abs(cur_height - 0.8382) < 0.001:
                                #ad_factor = 0.3333333433
                            #elif abs(cur_height - 1.1176) < 0.001:
                                #ad_factor = 0.5
                            #print y_size
                            #print cur_height
                            #print '+++++++++' * 5
                            
                            ad_height = aobao_y_size
                            ad_width = aobao_x_size
                            ad_factor = aobao_factor
                            
                            GEN.COM('cur_atr_reset')
                            GEN.COM('cur_atr_set,attribute=.deferred')
                            # === 在Genesis下不加ver=1 字体添加时会按字最小范围的左下角添加，而不是字体的左下角 ===
                            GEN.COM(
                                'add_text,type=%s,polarity=%s,attributes=%s,x=%s,y=%s,text=%s,fontname=%s,x_size=%s,'
                                'y_size=%s,mirror=%s,angle=%s,w_factor=%s,ver=1' % (
                                    text_type, text_pol, text_attr_yn, text_x, text_y, ad_text, ad_fontname, ad_width,
                                    ad_height, ad_mir, ad_ang, ad_factor))
                            # 3/6 x_size = 0.8382, y_size = 0.8382,w_factor=0.3333333433
                            # x_size = 0.5588, y_size = 0.5588, w_factor = 0.25
                            # (add_text,type=%s,attributes=%s,x=%s,y=%s,text=%s,x_size=%s,y_size=%s,w_factor=%s,
                            # polarity=%s,angle=%s,mirror=%s,fontname=%s,ver=1)
                            # 2/6 inch 单位 x_size=0.022,y_size=0.022,w_factor=0.25 mm单位  x_size=0.5588,y_size=0.5588,w_factor=0.25
                            # 3/6 inch 单位 x_size=0.033,y_size=0.033,w_factor=0.3333333433 mm单位 x_size=0.8382,y_size=0.8382,w_factor=0.3333333433
                            # 4/6 inch 单位 x_size=0.044,y_size=0.044,w_factor=0.5 mm单位 x_size=1.1176,y_size=1.1176,w_factor=0.5

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
                            GEN.ADD_PAD(x_cent, y_cent, 's%s' % ad_fir_pad_size, pol='positive', attr='yes')
                            GEN.COM('add_text,type=%s,polarity=%s,attributes=%s,x=%s,y=%s,text=%s,mirror=%s,angle=%s,'
                                    'bar_type=%s,matrix=%s,bar_background=%s,bar_add_string=%s,bar_marks=%s,'
                                    'bar_width=0.2032,bar_height=%s' % (
                                        text_type, text_pol, text_attr_yn, text_x, text_y, ad_text, ad_mir, ad_ang,
                                        bar_type,
                                        ad_matrix, ad_background, ad_bar_string, ad_bar_mark, ad_height))
                        GEN.CLEAR_LAYER()
                else:
                    M = M_Box()
                    showText = M.msgText(u'提示', u"非正常退出循环", showcolor='red')
                    M.msgBox(showText)
                    return 'Error'

            GEN.CLOSE_STEP()
        return True
    
    def get_add_text_size(self, jobname, text_size_index):

        if text_size_index == 2:                
            x_size = 22 * 0.0254
            y_size = 22 * 0.0254
            factor = 0.25
            line_width = 3 * 0.0254
            two_surface_spacing = 0.25
        if text_size_index == 1: 
            x_size = 33 * 0.0254
            y_size = 33 * 0.0254
            factor = 0.3333333433
            line_width = 4 * 0.0254
            two_surface_spacing = 0.25
        if text_size_index == 0: 
            x_size = 44 * 0.0254
            y_size = 44 * 0.0254
            factor = 0.5
            line_width = 6 * 0.0254
            two_surface_spacing = 0.33
                
        return x_size, y_size, factor, line_width, two_surface_spacing
                
    def add_surface_pad_new(self, jobname, stepname, worklayer,
                            text_polarity, mirror, ad_attr,
                            x_size, y_size, factor, line_width,
                            two_surface_spacing):
        """抓取面铜区间，自动带出对应面铜的字体，字体按照两行添加 20221206 by lyh"""                
        GEN.DELETE_LAYER(worklayer+"_tmp")
        GEN.CREATE_LAYER(worklayer+"_tmp")
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(worklayer+"_tmp", "yes")
        GEN.ADD_TEXT(0, 0, 'B1001001', x_size, y_size, w_factor=factor, mirr=mirror)        
        get_feature = GEN.DO_INFO (
            "-t layer -e %s/%s/%s -d LIMITS" % (jobname, stepname, worklayer+"_tmp"), units="mm")
        xmin1 = float (get_feature['gLIMITSxmin'])
        ymin1 = float (get_feature['gLIMITSymin'])
        xmax1 = float (get_feature['gLIMITSxmax']) + line_width * 0.5 + 0.05
        ymax1 = float (get_feature['gLIMITSymax'])
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(worklayer, "yes")
        GEN.COM ('add_surf_strt,surf_type=feature')        
        GEN.COM ('add_surf_poly_strt,x=%s,y=%s' % (xmin1, ymin1))
        GEN.COM ('add_surf_poly_seg,x=%s,y=%s' % (xmax1, ymin1))
        GEN.COM ('add_surf_poly_seg,x=%s,y=%s' % (xmax1, ymax1))
        GEN.COM ('add_surf_poly_seg,x=%s,y=%s' % (xmin1, ymax1))
        GEN.COM ('add_surf_poly_seg,x=%s,y=%s' % (xmin1, ymin1))                
        GEN.COM ('add_surf_poly_end')
        GEN.COM ('add_surf_end,attributes=%s,polarity=%s' % (ad_attr, "positive"))
        
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(worklayer+"_tmp", "yes")
        GEN.SEL_DELETE()
        if mirror == "no":            
            GEN.ADD_TEXT(xmax1, ymin1-y_size-two_surface_spacing, '-SSS', x_size, y_size, w_factor=factor, mirr="yes")
        else:
            GEN.ADD_TEXT(xmin1, ymin1-y_size-two_surface_spacing, '-SSS', x_size, y_size, w_factor=factor, mirr="no")
            
        get_feature = GEN.DO_INFO (
            "-t layer -e %s/%s/%s -d LIMITS" % (jobname, stepname, worklayer+"_tmp"), units="mm")
        xmin2 = float (get_feature['gLIMITSxmin'])
        ymin2 = float (get_feature['gLIMITSymin'])
        xmax2 = float (get_feature['gLIMITSxmax'])
        ymax2 = float (get_feature['gLIMITSymax'])
        if mirror == "no":
            xmax2 = xmax1
        else:
            xmin2 = xmin1
            
        GEN.CLEAR_LAYER()
        GEN.WORK_LAYER(worklayer)
        GEN.COM ('add_surf_strt,surf_type=feature')        
        GEN.COM ('add_surf_poly_strt,x=%s,y=%s' % (xmin2, ymin2))
        GEN.COM ('add_surf_poly_seg,x=%s,y=%s' % (xmax2, ymin2))
        GEN.COM ('add_surf_poly_seg,x=%s,y=%s' % (xmax2, ymax2))
        GEN.COM ('add_surf_poly_seg,x=%s,y=%s' % (xmin2, ymax2))
        GEN.COM ('add_surf_poly_seg,x=%s,y=%s' % (xmin2, ymin2))                
        GEN.COM ('add_surf_poly_end')
        GEN.COM ('add_surf_end,attributes=%s,polarity=%s' % (ad_attr, "positive"))
        GEN.DELETE_LAYER(worklayer+"_tmp")

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

            if lay_type in ['silk_screen', 'solder_mask', 'signal']:
                if m_info['gROWcontext'][num] == 'board' and m_info['gROWside'][num] in ['top', 'bottom']:
                    LayValues[lay_type][m_info['gROWname'][num]] = m_info['gROWside'][num]

        # --返回对应数组信息
        return LayValues

    def add_surface_pad(self, x=0, y=0, ad_attr='no', ad_pol='positive', type='ob2dbc', etch_bc_size='5',etch_text_size='6.096x0.76',mir=None):
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
            etch_text_size_x = self.stringtonum(etch_text_size.split('x')[0])
            etch_text_size_y = self.stringtonum(etch_text_size.split('x')[1])
            size_x = x + etch_text_size_x
            size_y = y + etch_text_size_y
            x3 = size_x
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
        GEN.COM('add_surf_end,attributes=%s,polarity=%s' % (ad_attr, ad_pol))
        if type == 'obtext':
            if mir != 'yes':
                GEN.COM('add_surf_strt,surf_type=feature')
                GEN.COM('add_surf_poly_strt,x=%s,y=%s' % (x2, y1))
                GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (x3, y1))
                GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (x3, y2))
                GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (x2, y2))
                GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (x2, y1))
                GEN.COM('add_surf_poly_end')
                GEN.COM('add_surf_end,attributes=%s,polarity=%s' % (ad_attr, ad_pol))
            else:
                GEN.COM('add_surf_strt,surf_type=feature')
                GEN.COM('add_surf_poly_strt,x=%s,y=%s' % (x1, y1))
                GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (x3, y1))
                GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (x3, y2))
                GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (x1, y2))
                GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (x1, y1))
                GEN.COM('add_surf_poly_end')
                GEN.COM('add_surf_end,attributes=%s,polarity=%s' % (ad_attr, ad_pol))

    def check_position(self, tmp_layer, des_etch, type='ob2dbc', ad_step=None, mode=None, etch_big_bc_yn=None,
                       ref_lyr_dict=None, des_type='signal'):
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
        GEN.FILTER_RESET()
        GEN.COM('sel_single_feat,operation=select,x=0,y=0,tol=200,cyclic=no')
        type_cn = dict(ob2dbc='二维码', obtext='蚀刻字', baozhuang='包装码')
        GEN.PAUSE('请移动Step:%s层%s中的symbol位置，可按需更改此symbol大小，比对层别%s依此为基准添加%s' %
                  (ad_step, tmp_layer, des_etch, type_cn[type]))
        control_num = 1
        if type == 'obtext':
            control_num = 2
        GEN.CLEAR_LAYER()
        GEN.CHANGE_UNITS('mm')
        GEN.WORK_LAYER(tmp_layer, number=1)
        GEN.CLEAR_FEAT()
        GEN.FILTER_RESET()
        GEN.FILTER_SET_TYP('surface')
        GEN.FILTER_SET_PRO('in')
        GEN.FILTER_SELECT()
        count1 = int(GEN.GET_SELECT_COUNT())
        if count1 != control_num:
            error_list.append(u'超出profile!|\n')
            # GEN.PAUSE(str([count1, control_num, type]))
        GEN.CLEAR_FEAT()
        if len(error_list) == 0:
            # === 检测目标层相交 ===
            if type in ['ob2dbc', 'obtext']:
                cur_layer_syms = "line;pad;arc;text"
            elif type in ['baozhuang']:
                cur_layer_syms = "line;pad;surface;arc;text"
            else:
                error_list.append(u'当前层相交检测不识别类型:%s|' % type)
            GEN.FILTER_RESET()
            GEN.SEL_REF_FEAT(des_etch, 'touch', f_type=cur_layer_syms)
            count2 = int(GEN.GET_SELECT_COUNT())
            if count2 > 0:
                error_list.append(u'与目标层:%s非surface相交|' % des_etch)
            GEN.CLEAR_FEAT()

        if len(error_list) == 0:
            # === 检测其他层相交 ===
            # ref_layers = []
            if type in ['ob2dbc', 'obtext']:
                get_side = ref_lyr_dict[des_type][des_etch]
                ref_layers = [k for i in ref_lyr_dict for k in ref_lyr_dict[i] if
                              ref_lyr_dict[i][k] == get_side and k != des_etch]
                ref_str = ';'.join(ref_layers)

                GEN.FILTER_RESET()
                ref_layer_syms = "line;pad;surface;arc;text"
                GEN.SEL_REF_FEAT(ref_str, 'touch', f_type=ref_layer_syms)
                count3 = int(GEN.GET_SELECT_COUNT())
                if count3 > 0:
                    error_list.append(u'与参考层:%s相交|' % ref_str)
                GEN.CLEAR_FEAT()

            elif type in ['baozhuang']:
                # === 判断是否与参考层相交，省略写法，包含了目标层
                get_type, get_side = \
                [(i, ref_lyr_dict[i][k]) for i in ref_lyr_dict for k in ref_lyr_dict[i] if k == des_etch][0]
                ref_layers = [k for i in ['solder_mask', 'silk_screen'] for k in ref_lyr_dict[i] if
                              ref_lyr_dict[i][k] == get_side]

                ref_str = ';'.join(ref_layers)
                GEN.FILTER_RESET()
                ref_layer_syms = "line;pad;surface;arc;text"
                GEN.SEL_REF_FEAT(ref_str, 'touch', f_type=ref_layer_syms)
                count3 = int(GEN.GET_SELECT_COUNT())
                if count3 > 0:
                    error_list.append(u'与参考层:%s相交|' % ref_str)
                GEN.CLEAR_FEAT()
                if len(error_list) == 0:
                    ref_out = [k for k in ref_lyr_dict['signal'] if ref_lyr_dict['signal'][k] == get_side][0]
                    GEN.FILTER_RESET()
                    ref_layer_syms = "line;pad;arc;text"
                    GEN.SEL_REF_FEAT(ref_out, 'touch', f_type=ref_layer_syms)
                    count4 = int(GEN.GET_SELECT_COUNT())
                    if count4 > 0:
                        error_list.append(u'与外层:%s非surface相交|' % ref_out)
                    GEN.CLEAR_FEAT()

                    GEN.FILTER_RESET()
                    ref_out_syms = "surface"
                    GEN.SEL_REF_FEAT(ref_out, 'cover', f_type=ref_out_syms, pol='positive')
                    count5 = int(GEN.GET_SELECT_COUNT())
                    if count5 != control_num:
                        error_list.append(u'包装码没有被外层:%s铜皮包含|' % ref_out)

        GEN.CLEAR_FEAT()
        # === 检查symbol数量及symbol大小 ===
        if len(error_list) == 0:
            get_feat_num = GEN.DO_INFO("-t layer -e  %s/%s/%s -d FEAT_HIST" % (self.job_name, ad_step, tmp_layer))
            if type == 'ob2dbc':
                if int(get_feat_num['gFEAT_HISTtotal']) != 1:
                    error_list.append(u'模式为二维码时，临时层标识数量不为1|')
            elif type == 'obtext':
                if int(get_feat_num['gFEAT_HISTtotal']) != 2:
                    error_list.append(u'模式为蚀刻码时，临时层标识数量不为2|')
            elif type == 'baozhuang':
                if int(get_feat_num['gFEAT_HISTtotal']) != 1:
                    error_list.append(u'模式为包装码时，临时层标识数量不为1|')
            if len(error_list) == 0:
                info = GEN.INFO(
                    '-t layer -e %s/%s/%s -m script -d FEATURES -o feat_index' % (self.job_name, ad_step, tmp_layer))
                indexRegex = re.compile(r'^#(\d+)\s+#S P 0')
                for line in info:
                    if re.match(indexRegex, line):
                        match_obj = re.match(indexRegex, line)
                        index = match_obj.groups()[0]
                        GEN.VOF()
                        GEN.COM(
                            'sel_layer_feat,operation=select,layer=%s,index=%s' % (tmp_layer, index))
                        GEN.VON()
                        count = GEN.GET_SELECT_COUNT()
                        if count > 0:
                            get_feature = GEN.DO_INFO(
                                "-t layer -e %s/%s/%s -d LIMITS -o select" % (self.job_name, ad_step, tmp_layer),
                                units="mm")
                            tmp_dict = dict(
                                x_size=float(get_feature['gLIMITSxmax']) - float(get_feature['gLIMITSxmin']),
                                y_size=float(get_feature['gLIMITSymax']) - float(get_feature['gLIMITSymin']),
                                x_cent=float(get_feature['gLIMITSxcenter']),
                                y_cent=float(get_feature['gLIMITSycenter']),
                            )
                            tmp_dict['length'] = max(tmp_dict['x_size'], tmp_dict['y_size'])
                            tmp_dict['height'] = min(tmp_dict['x_size'], tmp_dict['y_size'])
                            ref_cor_array.append(tmp_dict)
                            GEN.CLEAR_FEAT()
                            if type in ['ob2dbc']:
                                if mode == 'normal':
                                    if etch_big_bc_yn == 'yes':
                                        if tmp_dict['height'] < 5 + 0.152 + 0.5:
                                            error_list.append(u'面铜大于1.18mil时，二维码大小应大于5.652mm(包含底pad)|')

                                    else:
                                        if tmp_dict['height'] < 4 + 0.1524 + 0.5:
                                            error_list.append(u'二维码大小应大于4.652mm(包含底pad)|')

                                else:
                                    if tmp_dict['height'] < 3:
                                        error_list.append(u'二维码大小应大于3mm!')

        # 检查层别中的内容是否和目标层相交
        if len(error_list) == 0:
            GEN.CLEAR_LAYER()
            return ref_cor_array
        else:
            GEN.WORK_LAYER(des_etch, number=2)
            M = M_Box()
            showText = M.msgText(u'提示', u"%s!" % ','.join(error_list), showcolor='red')
            M.msgBox(showText)
            return self.check_position(tmp_layer, des_etch, type=type, ad_step=ad_step, mode=mode,
                                       etch_big_bc_yn=etch_big_bc_yn, ref_lyr_dict=ref_lyr_dict,des_type=des_type)

    def main_run(self):
        if self.supply == 'aobao':
            get_result = self.add_ob_2dbc()
        # 程序的完成提醒
        M = M_Box()
        if get_result == "UIError":
            self.show()
            return
        elif get_result == "Error":
            showText = M.msgText(u'提示', u"程序运行过程中有报警，运行结束!", showcolor='red')
        else:
            showText = M.msgText(u'提示', u"程序运行完成!", showcolor='green')
        M.msgBox(showText)
        self.close()
        sys.exit(0)


# # # # --程序入口
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MainWindowShow()
    myapp.show()
    app.exec_()
    sys.exit(0)
