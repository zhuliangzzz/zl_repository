# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'TemporaryLayerComparsionUI.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(562, 624)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        Form.setFont(font)
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.groupBox_7 = QtWidgets.QGroupBox(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox_7.setFont(font)
        self.groupBox_7.setObjectName("groupBox_7")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout(self.groupBox_7)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.radioButton = QtWidgets.QRadioButton(self.groupBox_7)
        self.radioButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.radioButton.setChecked(True)
        self.radioButton.setObjectName("radioButton")
        self.horizontalLayout_8.addWidget(self.radioButton)
        self.radioButton_2 = QtWidgets.QRadioButton(self.groupBox_7)
        self.radioButton_2.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.radioButton_2.setObjectName("radioButton_2")
        self.horizontalLayout_8.addWidget(self.radioButton_2)
        self.verticalLayout_7.addWidget(self.groupBox_7)
        self.stackedWidget = QtWidgets.QStackedWidget(Form)
        self.stackedWidget.setObjectName("stackedWidget")
        self.page = QtWidgets.QWidget()
        self.page.setObjectName("page")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.page)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_5.setSpacing(4)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.groupBox = QtWidgets.QGroupBox(self.page)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.groupBox.setFont(font)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.groupBox)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_2.addWidget(self.label_3)
        self.comboBox_temp = QtWidgets.QComboBox(self.groupBox)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.comboBox_temp.setFont(font)
        self.comboBox_temp.setObjectName("comboBox_temp")
        self.horizontalLayout_2.addWidget(self.comboBox_temp)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.horizontalLayout_2.setStretch(1, 1)
        self.horizontalLayout_2.setStretch(2, 1)
        self.horizontalLayout.addWidget(self.groupBox)
        self.verticalLayout_5.addLayout(self.horizontalLayout)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setSpacing(6)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.splitter = QtWidgets.QSplitter(self.page)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setOpaqueResize(True)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setObjectName("splitter")
        self.groupBox_2 = QtWidgets.QGroupBox(self.splitter)
        self.groupBox_2.setMinimumSize(QtCore.QSize(0, 400))
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.listWidget = QtWidgets.QListWidget(self.groupBox_2)
        self.listWidget.viewport().setProperty("cursor", QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout.addWidget(self.listWidget)
        self.groupBox_3 = QtWidgets.QGroupBox(self.splitter)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tableWidget = QtWidgets.QTableWidget(self.groupBox_3)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.verticalLayout_2.addWidget(self.tableWidget)
        self.horizontalLayout_6.addWidget(self.splitter)
        self.checkBox_all = QtWidgets.QCheckBox(self.page)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        self.checkBox_all.setFont(font)
        self.checkBox_all.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.checkBox_all.setObjectName("checkBox_all")
        self.horizontalLayout_6.addWidget(self.checkBox_all)
        self.verticalLayout_5.addLayout(self.horizontalLayout_6)
        self.verticalLayout_5.setStretch(1, 1)
        self.stackedWidget.addWidget(self.page)
        self.page_2 = QtWidgets.QWidget()
        self.page_2.setObjectName("page_2")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.page_2)
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_6.setSpacing(4)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.groupBox_6 = QtWidgets.QGroupBox(self.page_2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.groupBox_6.setFont(font)
        self.groupBox_6.setObjectName("groupBox_6")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout(self.groupBox_6)
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.label_4 = QtWidgets.QLabel(self.groupBox_6)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_10.addWidget(self.label_4)
        self.comboBox_temp_2 = QtWidgets.QComboBox(self.groupBox_6)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.comboBox_temp_2.setFont(font)
        self.comboBox_temp_2.setObjectName("comboBox_temp_2")
        self.horizontalLayout_10.addWidget(self.comboBox_temp_2)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_10.addItem(spacerItem1)
        self.horizontalLayout_10.setStretch(1, 1)
        self.horizontalLayout_10.setStretch(2, 1)
        self.horizontalLayout_9.addWidget(self.groupBox_6)
        self.verticalLayout_6.addLayout(self.horizontalLayout_9)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setSpacing(6)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.splitter_2 = QtWidgets.QSplitter(self.page_2)
        self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_2.setOpaqueResize(True)
        self.splitter_2.setChildrenCollapsible(False)
        self.splitter_2.setObjectName("splitter_2")
        self.groupBox_4 = QtWidgets.QGroupBox(self.splitter_2)
        self.groupBox_4.setMinimumSize(QtCore.QSize(0, 400))
        self.groupBox_4.setObjectName("groupBox_4")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox_4)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.listWidget_2 = QtWidgets.QListWidget(self.groupBox_4)
        self.listWidget_2.viewport().setProperty("cursor", QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.listWidget_2.setObjectName("listWidget_2")
        self.verticalLayout_3.addWidget(self.listWidget_2)
        self.groupBox_5 = QtWidgets.QGroupBox(self.splitter_2)
        self.groupBox_5.setObjectName("groupBox_5")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.groupBox_5)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.tableWidget_2 = QtWidgets.QTableWidget(self.groupBox_5)
        self.tableWidget_2.setObjectName("tableWidget_2")
        self.tableWidget_2.setColumnCount(0)
        self.tableWidget_2.setRowCount(0)
        self.verticalLayout_4.addWidget(self.tableWidget_2)
        self.horizontalLayout_7.addWidget(self.splitter_2)
        self.checkBox_all_2 = QtWidgets.QCheckBox(self.page_2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        self.checkBox_all_2.setFont(font)
        self.checkBox_all_2.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.checkBox_all_2.setObjectName("checkBox_all_2")
        self.horizontalLayout_7.addWidget(self.checkBox_all_2)
        self.verticalLayout_6.addLayout(self.horizontalLayout_7)
        self.verticalLayout_6.setStretch(1, 1)
        self.stackedWidget.addWidget(self.page_2)
        self.verticalLayout_7.addWidget(self.stackedWidget)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label = QtWidgets.QLabel(Form)
        self.label.setObjectName("label")
        self.horizontalLayout_4.addWidget(self.label)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(2)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.comboBox_resolution = QtWidgets.QComboBox(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        self.comboBox_resolution.setFont(font)
        self.comboBox_resolution.setEditable(True)
        self.comboBox_resolution.setObjectName("comboBox_resolution")
        self.horizontalLayout_3.addWidget(self.comboBox_resolution)
        self.label_2 = QtWidgets.QLabel(Form)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_3.addWidget(self.label_2)
        self.horizontalLayout_4.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_4.setStretch(1, 1)
        self.verticalLayout_7.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.pushButton_exec = QtWidgets.QPushButton(Form)
        self.pushButton_exec.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.pushButton_exec.setObjectName("pushButton_exec")
        self.horizontalLayout_5.addWidget(self.pushButton_exec)
        self.pushButton_exit = QtWidgets.QPushButton(Form)
        self.pushButton_exit.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.pushButton_exit.setObjectName("pushButton_exit")
        self.horizontalLayout_5.addWidget(self.pushButton_exit)
        self.verticalLayout_7.addLayout(self.horizontalLayout_5)

        self.retranslateUi(Form)
        self.stackedWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "临时层/备份层比对"))
        self.groupBox_7.setTitle(_translate("Form", "类型"))
        self.radioButton.setText(_translate("Form", "临时层"))
        self.radioButton_2.setText(_translate("Form", "备份层"))
        self.groupBox.setTitle(_translate("Form", "临时层后缀"))
        self.label_3.setText(_translate("Form", "筛选后缀："))
        self.groupBox_2.setTitle(_translate("Form", "临时层"))
        self.groupBox_3.setTitle(_translate("Form", "正式层"))
        self.checkBox_all.setText(_translate("Form", "全选"))
        self.groupBox_6.setTitle(_translate("Form", "备份层后缀"))
        self.label_4.setText(_translate("Form", "筛选后缀："))
        self.groupBox_4.setTitle(_translate("Form", "备份层"))
        self.groupBox_5.setTitle(_translate("Form", "正式层"))
        self.checkBox_all_2.setText(_translate("Form", "全选"))
        self.label.setText(_translate("Form", "比对精度："))
        self.label_2.setText(_translate("Form", "mil"))
        self.pushButton_exec.setText(_translate("Form", "执行"))
        self.pushButton_exit.setText(_translate("Form", "非正常退出"))
