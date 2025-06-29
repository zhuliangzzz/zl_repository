# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SetEdgeSealingUI.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(363, 309)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        Form.setFont(font)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label_logo = QtWidgets.QLabel(Form)
        self.label_logo.setMinimumSize(QtCore.QSize(0, 50))
        self.label_logo.setObjectName("label_logo")
        self.horizontalLayout.addWidget(self.label_logo)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout_3.addWidget(self.label)
        self.label_jobname = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.label_jobname.setFont(font)
        self.label_jobname.setObjectName("label_jobname")
        self.horizontalLayout_3.addWidget(self.label_jobname)
        self.horizontalLayout_3.setStretch(1, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.lineEdit_set_w = QtWidgets.QLineEdit(Form)
        self.lineEdit_set_w.setMaximumSize(QtCore.QSize(16777215, 20))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.lineEdit_set_w.setFont(font)
        self.lineEdit_set_w.setReadOnly(True)
        self.lineEdit_set_w.setObjectName("lineEdit_set_w")
        self.horizontalLayout_2.addWidget(self.lineEdit_set_w)
        self.label_3 = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_2.addWidget(self.label_3)
        self.lineEdit_set_h = QtWidgets.QLineEdit(Form)
        self.lineEdit_set_h.setMaximumSize(QtCore.QSize(16777215, 20))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.lineEdit_set_h.setFont(font)
        self.lineEdit_set_h.setReadOnly(True)
        self.lineEdit_set_h.setObjectName("lineEdit_set_h")
        self.horizontalLayout_2.addWidget(self.lineEdit_set_h)
        self.label_11 = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_11.setFont(font)
        self.label_11.setObjectName("label_11")
        self.horizontalLayout_2.addWidget(self.label_11)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_4 = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_4.addWidget(self.label_4)
        self.label_type = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.label_type.setFont(font)
        self.label_type.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.label_type.setObjectName("label_type")
        self.horizontalLayout_4.addWidget(self.label_type)
        self.horizontalLayout_4.setStretch(1, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_5 = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_5.addWidget(self.label_5)
        self.label_product = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.label_product.setFont(font)
        self.label_product.setObjectName("label_product")
        self.horizontalLayout_5.addWidget(self.label_product)
        self.horizontalLayout_5.setStretch(1, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.label_14 = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.label_14.setFont(font)
        self.label_14.setObjectName("label_14")
        self.horizontalLayout_10.addWidget(self.label_14)
        self.radioButton_yellow = QtWidgets.QRadioButton(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.radioButton_yellow.setFont(font)
        self.radioButton_yellow.setChecked(True)
        self.radioButton_yellow.setObjectName("radioButton_yellow")
        self.horizontalLayout_10.addWidget(self.radioButton_yellow)
        self.radioButton_other = QtWidgets.QRadioButton(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.radioButton_other.setFont(font)
        self.radioButton_other.setObjectName("radioButton_other")
        self.horizontalLayout_10.addWidget(self.radioButton_other)
        self.horizontalLayout_10.setStretch(1, 1)
        self.horizontalLayout_10.setStretch(2, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_10)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label_7 = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.label_7.setFont(font)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout_8.addWidget(self.label_7)
        self.comboBox_method = QtWidgets.QComboBox(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.comboBox_method.setFont(font)
        self.comboBox_method.setObjectName("comboBox_method")
        self.horizontalLayout_8.addWidget(self.comboBox_method)
        self.horizontalLayout_8.setStretch(1, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_8)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setSpacing(4)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.label_8 = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.label_8.setFont(font)
        self.label_8.setObjectName("label_8")
        self.horizontalLayout_9.addWidget(self.label_8)
        self.label_9 = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_9.setFont(font)
        self.label_9.setObjectName("label_9")
        self.horizontalLayout_9.addWidget(self.label_9)
        self.lineEdit_margin_x = QtWidgets.QLineEdit(Form)
        self.lineEdit_margin_x.setMaximumSize(QtCore.QSize(16777215, 20))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.lineEdit_margin_x.setFont(font)
        self.lineEdit_margin_x.setReadOnly(False)
        self.lineEdit_margin_x.setObjectName("lineEdit_margin_x")
        self.horizontalLayout_9.addWidget(self.lineEdit_margin_x)
        self.label_12 = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_12.setFont(font)
        self.label_12.setObjectName("label_12")
        self.horizontalLayout_9.addWidget(self.label_12)
        self.label_10 = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_10.setFont(font)
        self.label_10.setObjectName("label_10")
        self.horizontalLayout_9.addWidget(self.label_10)
        self.lineEdit_margin_y = QtWidgets.QLineEdit(Form)
        self.lineEdit_margin_y.setMaximumSize(QtCore.QSize(16777215, 20))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.lineEdit_margin_y.setFont(font)
        self.lineEdit_margin_y.setReadOnly(False)
        self.lineEdit_margin_y.setObjectName("lineEdit_margin_y")
        self.horizontalLayout_9.addWidget(self.lineEdit_margin_y)
        self.label_13 = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_13.setFont(font)
        self.label_13.setObjectName("label_13")
        self.horizontalLayout_9.addWidget(self.label_13)
        self.verticalLayout.addLayout(self.horizontalLayout_9)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setSpacing(10)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.pushButton_run = QtWidgets.QPushButton(Form)
        self.pushButton_run.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.pushButton_run.setObjectName("pushButton_run")
        self.horizontalLayout_7.addWidget(self.pushButton_run)
        self.pushButton_exit = QtWidgets.QPushButton(Form)
        self.pushButton_exit.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.pushButton_exit.setObjectName("pushButton_exit")
        self.horizontalLayout_7.addWidget(self.pushButton_exit)
        self.verticalLayout.addLayout(self.horizontalLayout_7)
        self.verticalLayout.setStretch(0, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "set封边"))
        self.label_logo.setText(_translate("Form", "TextLabel"))
        self.label.setText(_translate("Form", "料号："))
        self.label_jobname.setText(_translate("Form", "TextLabel"))
        self.label_2.setText(_translate("Form", "set尺寸："))
        self.label_3.setText(_translate("Form", "x"))
        self.label_11.setText(_translate("Form", "mm"))
        self.label_4.setText(_translate("Form", "类型："))
        self.label_type.setText(_translate("Form", "TextLabel"))
        self.label_5.setText(_translate("Form", "板类型："))
        self.label_product.setText(_translate("Form", "TextLabel"))
        self.label_14.setText(_translate("Form", "覆盖膜颜色："))
        self.radioButton_yellow.setText(_translate("Form", "黄色"))
        self.radioButton_other.setText(_translate("Form", "其他"))
        self.label_7.setText(_translate("Form", "铺铜方式："))
        self.label_8.setText(_translate("Form", "s & r Margin:"))
        self.label_9.setText(_translate("Form", "x："))
        self.label_12.setText(_translate("Form", "mm"))
        self.label_10.setText(_translate("Form", "y："))
        self.label_13.setText(_translate("Form", "mm"))
        self.pushButton_run.setText(_translate("Form", "执行"))
        self.pushButton_exit.setText(_translate("Form", "退出"))
