# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'RemoveSlightSectionUI20241203.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(264, 375)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        Form.setFont(font)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_2.setSpacing(8)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.groupBox = QtWidgets.QGroupBox(Form)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tableWidget = QtWidgets.QTableWidget(self.groupBox)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.verticalLayout.addWidget(self.tableWidget)
        self.checkBox = QtWidgets.QCheckBox(self.groupBox)
        self.checkBox.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.checkBox.setObjectName("checkBox")
        self.verticalLayout.addWidget(self.checkBox)
        self.verticalLayout_2.addWidget(self.groupBox)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(Form)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.lineEdit_size = QtWidgets.QLineEdit(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.lineEdit_size.setFont(font)
        self.lineEdit_size.setObjectName("lineEdit_size")
        self.horizontalLayout.addWidget(self.lineEdit_size)
        self.label_2 = QtWidgets.QLabel(Form)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_3 = QtWidgets.QLabel(Form)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_2.addWidget(self.label_3)
        self.lineEdit_bak_name = QtWidgets.QLineEdit(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.lineEdit_bak_name.setFont(font)
        self.lineEdit_bak_name.setReadOnly(True)
        self.lineEdit_bak_name.setObjectName("lineEdit_bak_name")
        self.horizontalLayout_2.addWidget(self.lineEdit_bak_name)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.pushButton_exec = QtWidgets.QPushButton(Form)
        self.pushButton_exec.setMinimumSize(QtCore.QSize(0, 26))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.pushButton_exec.setFont(font)
        self.pushButton_exec.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.pushButton_exec.setObjectName("pushButton_exec")
        self.horizontalLayout_3.addWidget(self.pushButton_exec)
        self.pushButton_exit = QtWidgets.QPushButton(Form)
        self.pushButton_exit.setMinimumSize(QtCore.QSize(0, 26))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.pushButton_exit.setFont(font)
        self.pushButton_exit.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.pushButton_exit.setObjectName("pushButton_exit")
        self.horizontalLayout_3.addWidget(self.pushButton_exit)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.verticalLayout_2.setStretch(0, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "panel板边去细丝"))
        self.groupBox.setTitle(_translate("Form", "选择层"))
        self.checkBox.setText(_translate("Form", "全选"))
        self.label.setText(_translate("Form", "细丝范围："))
        self.label_2.setText(_translate("Form", "mil"))
        self.label_3.setText(_translate("Form", "备份层："))
        self.pushButton_exec.setText(_translate("Form", "执行"))
        self.pushButton_exit.setText(_translate("Form", "退出"))
