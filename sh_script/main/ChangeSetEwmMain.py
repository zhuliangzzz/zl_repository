#!/usr/bin/env python26
# -*- coding: utf-8 -*-
# --------------------------------------------------------- #
#                VTG.SH SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    consenmy(吕康侠)
# @Mail         :    1943719064qq.com
# @Date         :    2022/03/04
# @Revision     :    1.0.0
# @File         :    ChangeSetEwmMain.py
# @Software     :    PyCharm
# @Usefor       :


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
# --------------------------------------------------------- #
import time
import platform

import os
import re
import sys
from PyQt4.QtGui import QMessageBox
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QTimer, QDateTime, Qt

if platform.system() == "Windows":
    pass
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
from messageBoxPro import msgBox
import Mainwindows.MainWindowsUI as UI

import ChangeEWMBll

bll = ChangeEWMBll.ChangeEWMBll()


class MainWin():
    def __init__(self):

        self.JOB = bll.JOB
        self.User=bll.User
        if self.JOB[1:4] != "a79":self.errorbox("该料号不是A79系列料号，程序退出！")
        self.STEP = bll.STEP
        self.ui = UI.Ui_Form()
        self.form=self.ui.setupUi(Form)
        if  not platform.system() == "Windows":

            FileAbsPath=os.path.dirname(os.path.abspath(__file__))
            self.ui.label_logo.setPixmap(QtGui.QPixmap(FileAbsPath+"/Mainwindows/img/logo1.png"))
            Form.setWindowIcon(QtGui.QIcon(FileAbsPath+"/Mainwindows/img/logoico.png"))

        self.ui.label_2.setText("step:%s" % self.STEP)
        self.ui.label_3.setText("job:%s" % self.JOB)
        self.ui.label_7.setText(u"添加的周期")
        #self.ttime = QtCore.QTimer()
        self.ui.ttime.timeout.connect(self.showtime)
        self.ui.ttime.start(0)
        self.NowWeek = self.GetNowWeek()
        self.ui.lineEdit.setText(self.NowWeek)

        (self.zqdata,self.gs)=bll.GeteditWeek()
        if not self.zqdata :self.errorbox(u"获取板内周期失败!")
        data = ChangeEWMBll.GetInplanData().Getinplanzq(self.JOB.upper()[:13])
        if not data:self.errorbox(u"获取Iplan周期失败!")
        if data[0]["DC_TYPE"]== "YYWW":self.editWeek = r"D$${yy}$${ww};VLVGT4;"
        elif data[0]["DC_TYPE"]== "WWYY":self.editWeek = r"D$${ww}$${yy};VLVGT4;"
        else:self.editWeek="D%s;VLVGT4;" %self.zqdata
        self.gss=data[0]["DC_TYPE"]
        self.ui.lineEdit_2.setText(self.zqdata)
        # self.ui.lineEdit_3 .setPlaceholderText("self.editWeek")
        self.ui.lineEdit_3.setText(self.editWeek)
        self.ui.comboBox.clear()
        self.ui.comboBox.addItem(u"新方式")
        self.ui.pushButton_run.clicked.connect(self.RunIt)
        self.ui.radioButton_2.toggled.connect(self.HideKJ)
        self.ui.radioButton.toggled.connect(self.HideKJ)


        self.ex3=bll.GetSetEWMGS()
    def HideKJ(self):
        """
        setVisible(bool)      设置控件是否可
        button.setVisible(True)     True 可
        setHidden(bool)    设置控件是否隐藏
        Ture  隐藏
        show()   显示控件
        hide()   隐藏控件"""
        if self.ui.radioButton_2.isChecked():
            self.ui.comboBox .setVisible(False)
            self.ui.comboBox_2.setVisible(False)
            self.ui.label_8.setVisible(False)
            self.ui.label_9.setVisible(False)

            data="%s%s;%s"%(self.ex3.split("\;")[0][:1],self.zqdata,self.ex3.split(";",1)[1])
            self.ui.lineEdit_3.setText(data)
        else:
            self.ui.comboBox.setVisible(True)
            self.ui.comboBox_2.setVisible(True)
            self.ui.label_8.setVisible(True)
            self.ui.label_9.setVisible(True)
            self.ui.lineEdit_3.setText(str(self.editWeek))


    def showtime(self):
        """
        定时器获取动态时间
        :return:
        """

        datetime = QDateTime.currentDateTime()
        text = datetime.toString("yyyy-MM-dd hh:mm:ss ddd")
        self.ui.label.setText(u"机台：%s||用户：%s||时间：%s||周期：第%s周" % (os.popen('hostname').read().strip(), self.User, text, time.strftime("%W")))

    def GetNowWeek(self):
        """
        实时周期
        :return: 
        """""
        # return QDateTime.currentDateTime().toString("yyyy")[-2:]+time.strftime("%W")
        str = u"20%s年第%s周" % (QDateTime.currentDateTime().toString("yyyy")[-2:], time.strftime("%W"))
        return str

    def RunIt(self):
        """
        确定运行事件
        :return:
        """
        Form.hide()
        #Form.setCursor(Qt.CrossCursor)
        editzq = self.ui.lineEdit_2.text()
        setzq = self.ui.lineEdit_3.text()
        OldOrNew=self.ui.comboBox.currentText()
        NewRadio=self.ui.radioButton.isChecked()
        ChangeRadio=self.ui.radioButton_2 .isChecked()
        AddMX=self.ui.comboBox_2.currentText()
        ErrorList = bll.CheckRun(editzq, setzq)
        if ErrorList: self.errorbox("\n".join(ErrorList))
        #bll.Mainrun(setzq,OldOrNew,NewRadio,ChangeRadio,AddMX)
        if NewRadio:bll.CreadEWM(setzq,AddMX,self.gss)
        if ChangeRadio :bll.ChangeEwm(setzq,self.ui.lineEdit_2.text())
        exit(0)

    def errorbox(self, str):
        msg_box = msgBox()
        msg_box.critical(self, u"错误",str , QMessageBox.Ok)
        exit(0)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    Form = QtGui.QWidget()
   # Form.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    mw = MainWin()
    desktop = QtGui.QApplication.desktop()
    width = desktop.width()
    height = desktop.height()
    Form.move((width - Form.width()) / 2, (height - Form.height()) / 2)
    Form.show()
    sys.exit(app.exec_())
