# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'set_size_ui.ui'
#
# Created: Wed Nov 01 16:09:52 2023
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
        Form.resize(255, 146)
        self.verticalLayout = QtGui.QVBoxLayout(Form)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(Form)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.yx_size = QtGui.QLineEdit(Form)
        self.yx_size.setObjectName(_fromUtf8("yx_size"))
        self.gridLayout.addWidget(self.yx_size, 2, 1, 1, 1)
        self.lx_size = QtGui.QLineEdit(Form)
        self.lx_size.setObjectName(_fromUtf8("lx_size"))
        self.gridLayout.addWidget(self.lx_size, 1, 1, 1, 1)
        self.yx_space = QtGui.QLineEdit(Form)
        self.yx_space.setObjectName(_fromUtf8("yx_space"))
        self.gridLayout.addWidget(self.yx_space, 2, 2, 1, 1)
        self.label_2 = QtGui.QLabel(Form)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.fx_size = QtGui.QLineEdit(Form)
        self.fx_size.setObjectName(_fromUtf8("fx_size"))
        self.gridLayout.addWidget(self.fx_size, 3, 1, 1, 1)
        self.lx_space = QtGui.QLineEdit(Form)
        self.lx_space.setObjectName(_fromUtf8("lx_space"))
        self.gridLayout.addWidget(self.lx_space, 1, 2, 1, 1)
        self.label_4 = QtGui.QLabel(Form)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_4.setFont(font)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout.addWidget(self.label_4, 0, 1, 1, 1)
        self.label_3 = QtGui.QLabel(Form)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)
        self.fx_space = QtGui.QLineEdit(Form)
        self.fx_space.setObjectName(_fromUtf8("fx_space"))
        self.gridLayout.addWidget(self.fx_space, 3, 2, 1, 1)
        self.label_5 = QtGui.QLabel(Form)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_5.setFont(font)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 0, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.pushButton_apply = QtGui.QPushButton(Form)
        self.pushButton_apply.setObjectName(_fromUtf8("pushButton_apply"))
        self.horizontalLayout.addWidget(self.pushButton_apply)
        self.pushButton_exit = QtGui.QPushButton(Form)
        self.pushButton_exit.setObjectName(_fromUtf8("pushButton_exit"))
        self.horizontalLayout.addWidget(self.pushButton_exit)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.label.setText(_translate("Form", "菱形铜块", None))
        self.label_2.setText(_translate("Form", "圆形铜豆", None))
        self.label_4.setText(_translate("Form", "尺寸(MIL)", None))
        self.label_3.setText(_translate("Form", "方形铜块", None))
        self.label_5.setText(_translate("Form", "间距(mil)", None))
        self.pushButton_apply.setText(_translate("Form", "保存and关闭", None))
        self.pushButton_exit.setText(_translate("Form", "取消", None))

