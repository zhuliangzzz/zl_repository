# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'LaserCarvingInputUI.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8


    def _translate(context, text, disambig=None):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig=None):
        return QtGui.QApplication.translate(context, text, disambig)


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(389, 531)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        Form.setFont(font)
        self.verticalLayout = QtGui.QVBoxLayout(Form)
        self.verticalLayout.setSpacing(8)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.groupBox = QtGui.QGroupBox(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox.setFont(font)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.groupBox)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.comboBox_temp = QtGui.QComboBox(self.groupBox)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.comboBox_temp.setFont(font)
        self.comboBox_temp.setObjectName("comboBox_temp")
        self.horizontalLayout_2.addWidget(self.comboBox_temp)
        self.horizontalLayout.addWidget(self.groupBox)
        self.groupBox_2 = QtGui.QGroupBox(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox_2.setFont(font)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout = QtGui.QGridLayout(self.groupBox_2)
        self.gridLayout.setObjectName("gridLayout")
        self.checkBox_outer_signal = QtGui.QCheckBox(self.groupBox_2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.checkBox_outer_signal.setFont(font)
        self.checkBox_outer_signal.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.checkBox_outer_signal.setObjectName("checkBox_outer_signal")
        self.gridLayout.addWidget(self.checkBox_outer_signal, 0, 0, 1, 1)
        self.checkBox_inner_signal = QtGui.QCheckBox(self.groupBox_2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.checkBox_inner_signal.setFont(font)
        self.checkBox_inner_signal.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.checkBox_inner_signal.setObjectName("checkBox_inner_signal")
        self.gridLayout.addWidget(self.checkBox_inner_signal, 0, 1, 1, 1)
        self.checkBox_silk_screen = QtGui.QCheckBox(self.groupBox_2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.checkBox_silk_screen.setFont(font)
        self.checkBox_silk_screen.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.checkBox_silk_screen.setObjectName("checkBox_silk_screen")
        self.gridLayout.addWidget(self.checkBox_silk_screen, 0, 2, 1, 1)
        self.checkBox_solder_mask = QtGui.QCheckBox(self.groupBox_2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.checkBox_solder_mask.setFont(font)
        self.checkBox_solder_mask.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.checkBox_solder_mask.setObjectName("checkBox_solder_mask")
        self.gridLayout.addWidget(self.checkBox_solder_mask, 0, 3, 1, 1)
        self.checkBox_drill = QtGui.QCheckBox(self.groupBox_2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.checkBox_drill.setFont(font)
        self.checkBox_drill.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.checkBox_drill.setObjectName("checkBox_drill")
        self.gridLayout.addWidget(self.checkBox_drill, 1, 0, 1, 1)
        self.checkBox_board = QtGui.QCheckBox(self.groupBox_2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.checkBox_board.setFont(font)
        self.checkBox_board.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.checkBox_board.setObjectName("checkBox_board")
        self.gridLayout.addWidget(self.checkBox_board, 1, 1, 1, 1)
        self.checkBox_all = QtGui.QCheckBox(self.groupBox_2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.checkBox_all.setFont(font)
        self.checkBox_all.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.checkBox_all.setObjectName("checkBox_all")
        self.gridLayout.addWidget(self.checkBox_all, 1, 2, 1, 1)
        self.horizontalLayout.addWidget(self.groupBox_2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.listWidget = QtGui.QListWidget(Form)
        self.listWidget.viewport().setProperty("cursor", QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout.addWidget(self.listWidget)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label = QtGui.QLabel(Form)
        self.label.setObjectName("label")
        self.horizontalLayout_4.addWidget(self.label)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(2)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.lineEdit_resolution = QtGui.QLineEdit(Form)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        self.lineEdit_resolution.setFont(font)
        self.lineEdit_resolution.setObjectName("lineEdit_resolution")
        self.horizontalLayout_3.addWidget(self.lineEdit_resolution)
        self.label_2 = QtGui.QLabel(Form)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_3.addWidget(self.label_2)
        self.horizontalLayout_4.addLayout(self.horizontalLayout_3)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.pushButton_exec = QtGui.QPushButton(Form)
        self.pushButton_exec.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.pushButton_exec.setObjectName("pushButton_exec")
        self.horizontalLayout_5.addWidget(self.pushButton_exec)
        self.pushButton_exit = QtGui.QPushButton(Form)
        self.pushButton_exit.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.pushButton_exit.setObjectName("pushButton_exit")
        self.horizontalLayout_5.addWidget(self.pushButton_exit)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        # _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "临时层比对"))
        self.groupBox.setTitle(_translate("Form", "临时层后缀"))
        self.groupBox_2.setTitle(_translate("Form", "层类型"))
        self.checkBox_outer_signal.setText(_translate("Form", "外层线路"))
        self.checkBox_inner_signal.setText(_translate("Form", "内层线路"))
        self.checkBox_silk_screen.setText(_translate("Form", "文字"))
        self.checkBox_solder_mask.setText(_translate("Form", "防焊"))
        self.checkBox_drill.setText(_translate("Form", "钻孔"))
        self.checkBox_board.setText(_translate("Form", "board层"))
        self.checkBox_all.setText(_translate("Form", "全选"))
        self.label.setText(_translate("Form", "比对精度："))
        self.label_2.setText(_translate("Form", "mil"))
        self.pushButton_exec.setText(_translate("Form", "执行"))
        self.pushButton_exit.setText(_translate("Form", "退出"))

