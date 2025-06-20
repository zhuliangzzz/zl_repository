#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2021/01/04
# @Revision     :    1.0.0
# @File         :    solder_mask_opt
# @Software     :    PyCharm
# @Usefor       :    防焊优化
# ---------------------------------------------------------#

import datetime
import sys
import json
from PyQt4 import QtCore, QtGui
# from PyQt4.QtGui import *
# --导入Package
import os
import platform
import string
import csv

if platform.system () == "Windows":
    # sys.path.append (r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append (r"C:/genesis/sys/scripts/Package")
else:
    sys.path.append (r"/incam/server/site_data/scripts/Package")
import genCOM_26
GEN = genCOM_26.GEN_COM ()
import UI.mainWindowV1 as FormUi
import Oracle_DB
import run_smDFM as R_DFM
from messageBox import msgBox
reload(sys)
sys.setdefaultencoding("utf-8")

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


_revisions = {
    'v1.0': '''
    1> Chao.Song 开发日期：2020.01.05
    2> 重构程序：增加外层铜厚获取SQL；外层铜厚对应的BGA及SMD补偿值；关联是否树脂塞孔，样品及量产''',
    'v1.1': '''
    1> Chao.Song 开发日期：2022.06.29
    2> SMD及BGA区域为默认勾选项：http://192.168.2.120:82/zentao/story-view-4285.html''',
    'v1.2': '''
    1> Chao.Song 开发日期：2022.07.07
    2> SMD开窗尺寸变为1.6-->2.0 预设pad开窗尺寸单边0.8-->1.0：http://192.168.2.120:82/zentao/story-view-4413.html'''
}


class MyApp (object):
    def __init__(self):
        self.appVer = 'V1.2'
        self.modify_data = '2021.01.06'
        self.job_name = os.environ.get('JOB')
        self.step_name = os.environ.get('STEP', 'edit')
        # === 防墓碑对应区域 ===
        self.sel_tx_frm = ''
        # === 产品类别 ===
        self.sel_fac_mode = ''
        # === 预设pad开窗尺寸 === V1.2 0.8-->1.0
        self.pad_open_size = "1.0"

        # === 获取HDI InPLan 油墨颜色 ===
        self.sm_color = ''
        M = Oracle_DB.ORACLE_INIT ()
        dbc_o = M.DB_CONNECT ("172.20.218.193", "inmind.fls", '1521', 'GETDATA', 'InplanAdmin')
        if dbc_o is None:
            # Mess = msgBox.Main ()
            msg_box = msgBox()
            msg_box.critical(self, '警告', 'HDI InPlan 无法连接, 程序退出！', QtGui.QMessageBox.Ok)
            exit (0)
        self.strJobName = self.job_name.split ('-')[0].upper ()
        self.JobData = M.getJobData (dbc_o, self.strJobName)
        if self.JobData:
            self.sm_color = self.JobData[0]['阻焊颜色']
        else:
            msg_box = msgBox()
            msg_box.critical(self, '警告', 'HDI InPlan无料号%s数据, 程序退出！' % self.job_name, QtGui.QMessageBox.Ok)
            exit (0)
        self.layerInfo = M.getLayerThkInfo (dbc_o, self.strJobName)
        # === 获取外层完成铜厚并匹配补偿表，界面带入BGA及SMD补偿值 ===
        self.scrDir = os.path.split (os.path.abspath (sys.argv[0]))[0]
        self.out_etch_rule = []
        with open (self.scrDir + '/outer_comp.csv') as f:
            f_csv = csv.DictReader (f)
            for row in f_csv:
                self.out_etch_rule.append(row)

        # === 获取外层层别名 ===
        self.outer_layers = GEN.GET_ATTR_LAYER('outer')
        self.bga_comp = ''
        self.smd_comp = ''

        for layName in self.outer_layers:
            for l_index in self.layerInfo:
                if layName == l_index['LAYER_NAME']:
                    getthick = l_index['CAL_CU_THK']
                    for line in self.out_etch_rule:
                        if float (line['cuLower']) <= float (getthick) < float (line['cuUpper']):
                            self.bga_comp = line['normalBGA']
                            self.smd_comp = line['normalSMD']

        if not self.bga_comp or not self.smd_comp:
            msg_box = msgBox()
            msg_box.warning(self, '警告', '料号：%s.未能根据铜厚获取到SMD及BGA补偿值, 请手动填入！', QtGui.QMessageBox.Ok)

        # print json.dumps(self.layerInfo, indent=2)
        # print json.dumps(self.out_etch_rule, indent=2)
        M.DB_CLOSE (dbc_o)

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


class MainWindow(QtGui.QWidget, MyApp):
    """
    窗体主方法
    """
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        MyApp.__init__(self)
        self.ui = FormUi.Ui_Form()
        self.ui.setupUi(self)
        self.ui.lineEdit_open.setText(self.pad_open_size)
        self.ui.lineEdit_color.setText(_fromUtf8(self.sm_color))

        # --重新加载ico 图标
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(r"%s/UI/Ico/Logo.ico" % self.scrDir)), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        self.retranslate_ui()

        if self.JobData[0]['是否树脂塞'] == '是':
            self.ui.radioButton_type3.setChecked(True)
        else:
            if self.JobData[0]['订单类型'] == '1:样品' or self.JobData[0]['订单类型'] == '5:快件样品':
                self.ui.radioButton_type1.setChecked (True)
            elif self.JobData[0]['订单类型'] == '2:量产' or self.JobData[0]['订单类型'] == '3:直接量产' \
                    or self.JobData[0]['订单类型'] == '4:样转量':
                self.ui.radioButton_type2.setChecked (True)

        self.ui.lineEdit_bga.setText(self.bga_comp)
        self.ui.lineEdit_smd.setText(self.smd_comp)

    def retranslate_ui(self):
        # === 增加line Edit类的输入限制 ===
        my_regex = QtCore.QRegExp ("^[0-5]\.[0-9][0-9]?[0-9]?$")
        my_validator = QtGui.QRegExpValidator (my_regex, self.ui.lineEdit_open)
        self.ui.lineEdit_open.setValidator (my_validator)
        my_regex = QtCore.QRegExp ("^[0-5]\.[0-9][0-9]?[0-9]?$")
        my_validator = QtGui.QRegExpValidator (my_regex, self.ui.lineEdit_smd)
        self.ui.lineEdit_smd.setValidator (my_validator)
        my_regex = QtCore.QRegExp ("^[0-5]\.[0-9][0-9]?[0-9]?$")
        my_validator = QtGui.QRegExpValidator (my_regex, self.ui.lineEdit_bga)
        self.ui.lineEdit_bga.setValidator (my_validator)
        my_regex = QtCore.QRegExp ("^[0-5]\.[0-9][0-9]?[0-9]?$")
        my_validator = QtGui.QRegExpValidator (my_regex, self.ui.lineEdit_bridge)
        self.ui.lineEdit_bridge.setValidator (my_validator)
        self.setWindowTitle(_translate("Form", "HDI一厂防墓碑优化", None))
        self.ui.label_bottom.setText(_fromUtf8("版权所有：胜宏科技 版本：%s 作者：Chao.Song 日期：%s" % (self.appVer, self.modify_data)))


        # toggled信号与槽函数绑定
        self.ui.radioButton_area1.toggled.connect(lambda: self.btnstate1(self.ui.radioButton_area1))
        self.ui.radioButton_area2.toggled.connect(lambda: self.btnstate1(self.ui.radioButton_area2))
        self.ui.radioButton_area3.toggled.connect(lambda: self.btnstate1(self.ui.radioButton_area3))

        # toggled信号与槽函数绑定
        self.ui.radioButton_type1.toggled.connect(lambda: self.btnstate2(self.ui.radioButton_type1))
        self.ui.radioButton_type2.toggled.connect(lambda: self.btnstate2(self.ui.radioButton_type2))
        self.ui.radioButton_type3.toggled.connect(lambda: self.btnstate2(self.ui.radioButton_type3))
        # ===2022.06.29 增加默认选择SMD与BGA区域的选项 http://192.168.2.120:82/zentao/story-view-4285.html===
        self.ui.radioButton_area3.setChecked(True)
        self.connect(self.ui.pushButton_apply, QtCore.SIGNAL(_fromUtf8("clicked()")), self.click_apply)

    def btnstate1(self, btn):
        # 输出按钮1与按钮2的状态，选中还是没选中
        self.sel_tx_frm = btn.text()

    def btnstate2(self, btn):
        # 输出按钮1与按钮2的状态，选中还是没选中
        self.sel_fac_mode = btn.text()

    def click_apply(self):
        # === 界面检测 ===
        # sel_tx_frm = self.ui.groupBox_2.isChecked()
        # === PAD开窗大小 ===
        pad_bridge_size = str(self.ui.lineEdit_bridge.text())
        # === BGA补偿大小 ===
        bga_out_addsize = str(self.ui.lineEdit_bga.text())
        # === SMD 补偿大小 ===
        smd_out_addsize = str(self.ui.lineEdit_smd.text())

        if not self.sel_tx_frm or not pad_bridge_size:
            msg_box = msgBox ()
            msg_box.critical (self, '警告', '未选择墓碑效应区域或未填入桥，请输入对应参数值！' , QtGui.QMessageBox.Ok)
            return False

        elif self.sel_tx_frm == u"BGA区域":
            if not bga_out_addsize:
                msg_box = msgBox ()
                msg_box.critical (self, '警告', '请在BGA参数项输入补偿值!', QtGui.QMessageBox.Ok)
                return False
        elif self.sel_tx_frm == u"BGA及SMD区域":
            if not bga_out_addsize or not smd_out_addsize:
                msg_box = msgBox ()
                msg_box.critical (self, '警告', '请在BGA参数项及SMD参数项输入补偿值!', QtGui.QMessageBox.Ok)
                return False

        if not self.sel_fac_mode :
            msg_box = msgBox ()
            msg_box.critical (self, '警告', '请选择订单类型!', QtGui.QMessageBox.Ok)
            return False

        # === 设定传递参数值，进行输出数据给外部数据 ===
        op_val = dict (pad_open_size=self.pad_open_size,
                       smd_out_addsize=smd_out_addsize,
                       bga_out_addsize=bga_out_addsize,
                       sel_tx_frm=self.sel_tx_frm,
                       pad_bridge_size=pad_bridge_size,
                       sel_fac_mode=self.sel_fac_mode
                       )
        self.close()
        run_dfm = R_DFM.DfmMain(op_val)
        run_dfm.run_sm_opt()


# # # # --程序入口
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MainWindow()
    myapp.show()
    app.exec_()
    sys.exit(0)
