# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SelectWrappedPadsUI.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(273, 137)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        Form.setFont(font)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_7 = QtWidgets.QLabel(Form)
        self.label_7.setMinimumSize(QtCore.QSize(0, 50))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label_7.setFont(font)
        self.label_7.setAlignment(QtCore.Qt.AlignCenter)
        self.label_7.setObjectName("label_7")
        self.verticalLayout.addWidget(self.label_7)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label_5 = QtWidgets.QLabel(Form)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 0, 2, 1, 1)
        self.label = QtWidgets.QLabel(Form)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.lineEdit_rate = QtWidgets.QLineEdit(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.lineEdit_rate.setFont(font)
        self.lineEdit_rate.setText("")
        self.lineEdit_rate.setObjectName("lineEdit_rate")
        self.gridLayout.addWidget(self.lineEdit_rate, 0, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_exec = QtWidgets.QPushButton(Form)
        self.pushButton_exec.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.pushButton_exec.setObjectName("pushButton_exec")
        self.horizontalLayout.addWidget(self.pushButton_exec)
        self.pushButton_exit = QtWidgets.QPushButton(Form)
        self.pushButton_exit.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.pushButton_exit.setObjectName("pushButton_exit")
        self.horizontalLayout.addWidget(self.pushButton_exit)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_7.setText(_translate("Form", "补偿包裹和非包裹bgaPad"))
        self.label_5.setText(_translate("Form", "%"))
        self.label.setText(_translate("Form", "包裹比例(以上）："))
        self.pushButton_exec.setText(_translate("Form", "执行"))
        self.pushButton_exit.setText(_translate("Form", "退出"))
