# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'testcouponV.ui'
#
# Created: Mon Apr 24 10:53:59 2023
#      by: PyQt4 UI code generator 4.9.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

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

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(463, 353)
        Form.setStyleSheet(_fromUtf8(""))
        self.gridLayout_2 = QtGui.QGridLayout(Form)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.label = QtGui.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Microsoft YaHei UI"))
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.pushButton_2 = QtGui.QPushButton(Form)
        self.pushButton_2.setMinimumSize(QtCore.QSize(0, 30))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Microsoft YaHei UI"))
        font.setPointSize(10)
        self.pushButton_2.setFont(font)
        self.pushButton_2.setStyleSheet(_fromUtf8("QPushButton{border:1px solid #fff;border-radius:11px;color: rgb(255, 255, 255);background:rgb(61,89,171)}\n"
"QPushButton:hover{border-color:#fff;border-radius:11px;color: rgb(0, 0, 0);background:transparent}\n"
"QPushButton:pressed{background:lightblue;border-style:hidden;color:#000}"))
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.horizontalLayout_2.addWidget(self.pushButton_2)
        self.pushButton_upload = QtGui.QPushButton(Form)
        self.pushButton_upload.setMinimumSize(QtCore.QSize(0, 30))
        self.pushButton_upload.setStyleSheet(_fromUtf8("QPushButton{border:1px solid #fff;border-radius:11px;color: rgb(255, 255, 255);background:rgb(61,89,171)}\n"
"QPushButton:hover{border-color:#fff;border-radius:11px;color: rgb(0, 0, 0);background:transparent}\n"
"QPushButton:pressed{background:lightblue;border-style:hidden;color:#000}"))
        self.pushButton_upload.setObjectName(_fromUtf8("pushButton_upload"))
        self.horizontalLayout_2.addWidget(self.pushButton_upload)
        self.pushButton_apply = QtGui.QPushButton(Form)
        self.pushButton_apply.setMinimumSize(QtCore.QSize(0, 30))
        self.pushButton_apply.setStyleSheet(_fromUtf8("QPushButton{border:1px solid #fff;border-radius:11px;color: rgb(255, 255, 255);background:rgb(61,89,171)}\n"
"QPushButton:hover{border-color:#fff;border-radius:11px;color: rgb(0, 0, 0);background:transparent}\n"
"QPushButton:pressed{background:lightblue;border-style:hidden;color:#000}"))
        self.pushButton_apply.setObjectName(_fromUtf8("pushButton_apply"))
        self.horizontalLayout_2.addWidget(self.pushButton_apply)
        self.pushButton_close = QtGui.QPushButton(Form)
        self.pushButton_close.setMinimumSize(QtCore.QSize(0, 30))
        self.pushButton_close.setStyleSheet(_fromUtf8("QPushButton{border:1px solid #fff;border-radius:11px;color: rgb(255, 255, 255);background:rgb(255,44,44)}\n"
"QPushButton:hover{border-color:#fff;border-radius:11px;color: rgb(255,44,44);background:transparent}\n"
"QPushButton:pressed{background:lightblue;border-style:hidden;color:#000}"))
        self.pushButton_close.setObjectName(_fromUtf8("pushButton_close"))
        self.horizontalLayout_2.addWidget(self.pushButton_close)
        self.gridLayout_2.addLayout(self.horizontalLayout_2, 7, 0, 1, 1)
        self.tableWidget = QtGui.QTableWidget(Form)
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, item)
        self.gridLayout_2.addWidget(self.tableWidget, 6, 0, 1, 1)
        self.label_tips = QtGui.QLabel(Form)
        self.label_tips.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_tips.setObjectName(_fromUtf8("label_tips"))
        self.gridLayout_2.addWidget(self.label_tips, 1, 0, 1, 1)
        self.gridLayout_3 = QtGui.QGridLayout()
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.checkBox_3 = QtGui.QCheckBox(Form)
        self.checkBox_3.setChecked(True)
        self.checkBox_3.setObjectName(_fromUtf8("checkBox_3"))
        self.gridLayout_3.addWidget(self.checkBox_3, 0, 3, 1, 1)
        self.checkBox = QtGui.QCheckBox(Form)
        self.checkBox.setChecked(True)
        self.checkBox.setObjectName(_fromUtf8("checkBox"))
        self.gridLayout_3.addWidget(self.checkBox, 0, 1, 1, 1)
        self.label_2 = QtGui.QLabel(Form)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout_3.addWidget(self.label_2, 0, 0, 1, 1)
        self.checkBox_2 = QtGui.QCheckBox(Form)
        self.checkBox_2.setChecked(True)
        self.checkBox_2.setObjectName(_fromUtf8("checkBox_2"))
        self.gridLayout_3.addWidget(self.checkBox_2, 0, 2, 1, 1)
        self.checkBox_4 = QtGui.QCheckBox(Form)
        self.checkBox_4.setChecked(True)
        self.checkBox_4.setObjectName(_fromUtf8("checkBox_4"))
        self.gridLayout_3.addWidget(self.checkBox_4, 1, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout_3, 2, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "板边各类模块添加程序", None))
        self.label.setText(_translate("Form", "试钻孔模块添加程序", None))
        self.pushButton_2.setText(_translate("Form", "分析板内并填写RIng", None))
        self.pushButton_upload.setText(_translate("Form", "载入上次数据", None))
        self.pushButton_apply.setText(_translate("Form", "执行", None))
        self.pushButton_close.setText(_translate("Form", "退出", None))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Form", "钻带", None))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Form", "模块孔径（um）", None))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("Form", "板内孔径（um）", None))
        item = self.tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("Form", "模块最小RIng（mil）", None))
        self.label_tips.setText(_translate("Form", "版权所有：胜宏科技", None))
        self.checkBox_3.setText(_translate("Form", "添加对准度模块", None))
        self.checkBox.setText(_translate("Form", "添加试钻模块", None))
        self.label_2.setText(_translate("Form", "选择要添加的模块", None))
        self.checkBox_2.setText(_translate("Form", "添加防漏接模块", None))
        self.checkBox_4.setText(_translate("Form", "邮票切片孔模块", None))

