# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'lossRunUI_v3.ui'
#
# Created: Fri Aug  2 14:19:00 2024
#      by: PyQt4 UI code generator 4.11.3
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

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(800, 670)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("sh_log.xpm")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.gridLayout_5 = QtGui.QGridLayout(MainWindow)
        self.gridLayout_5.setObjectName(_fromUtf8("gridLayout_5"))
        self.bottomLabel = QtGui.QLabel(MainWindow)
        self.bottomLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.bottomLabel.setObjectName(_fromUtf8("bottomLabel"))
        self.gridLayout_5.addWidget(self.bottomLabel, 4, 0, 1, 1)
        self.label_title = QtGui.QLabel(MainWindow)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_title.sizePolicy().hasHeightForWidth())
        self.label_title.setSizePolicy(sizePolicy)
        self.label_title.setMinimumSize(QtCore.QSize(200, 30))
        self.label_title.setMaximumSize(QtCore.QSize(1080, 200))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Arial"))
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.label_title.setFont(font)
        self.label_title.setAlignment(QtCore.Qt.AlignCenter)
        self.label_title.setObjectName(_fromUtf8("label_title"))
        self.gridLayout_5.addWidget(self.label_title, 0, 0, 1, 1)
        self.gridLayout_4 = QtGui.QGridLayout()
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.groupBox = QtGui.QGroupBox(MainWindow)
        self.groupBox.setMinimumSize(QtCore.QSize(100, 150))
        self.groupBox.setMaximumSize(QtCore.QSize(800, 300))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridLayout_2 = QtGui.QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.label_via = QtGui.QLabel(self.groupBox)
        self.label_via.setMinimumSize(QtCore.QSize(80, 0))
        self.label_via.setMaximumSize(QtCore.QSize(80, 35))
        self.label_via.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_via.setObjectName(_fromUtf8("label_via"))
        self.gridLayout_2.addWidget(self.label_via, 0, 0, 1, 1)
        self.viaSize = QtGui.QLineEdit(self.groupBox)
        self.viaSize.setMinimumSize(QtCore.QSize(20, 25))
        self.viaSize.setMaximumSize(QtCore.QSize(60, 25))
        self.viaSize.setStyleSheet(_fromUtf8("font: 11pt \"Times New Roman\";\n"
"\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgb(137, 200, 255);\n"
"border-style:none;\n"
"\n"
"padding:5px;\n"
"min-height:15px;\n"
"border-radius:3px;"))
        self.viaSize.setObjectName(_fromUtf8("viaSize"))
        self.gridLayout_2.addWidget(self.viaSize, 0, 1, 1, 1)
        self.label_tilt_via = QtGui.QLabel(self.groupBox)
        self.label_tilt_via.setMaximumSize(QtCore.QSize(100, 35))
        self.label_tilt_via.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_tilt_via.setObjectName(_fromUtf8("label_tilt_via"))
        self.gridLayout_2.addWidget(self.label_tilt_via, 0, 2, 1, 1)
        self.viaTilt = QtGui.QLineEdit(self.groupBox)
        self.viaTilt.setMinimumSize(QtCore.QSize(20, 25))
        self.viaTilt.setMaximumSize(QtCore.QSize(120, 25))
        self.viaTilt.setStyleSheet(_fromUtf8("font: 11pt \"Times New Roman\";\n"
"\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgb(137, 200, 255);\n"
"border-style:none;\n"
"\n"
"padding:5px;\n"
"min-height:15px;\n"
"border-radius:3px;"))
        self.viaTilt.setObjectName(_fromUtf8("viaTilt"))
        self.gridLayout_2.addWidget(self.viaTilt, 0, 3, 1, 1)
        self.line = QtGui.QFrame(self.groupBox)
        self.line.setMinimumSize(QtCore.QSize(20, 0))
        self.line.setFrameShape(QtGui.QFrame.VLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.gridLayout_2.addWidget(self.line, 0, 4, 3, 1)
        self.label_unit = QtGui.QLabel(self.groupBox)
        self.label_unit.setMaximumSize(QtCore.QSize(120, 30))
        self.label_unit.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_unit.setObjectName(_fromUtf8("label_unit"))
        self.gridLayout_2.addWidget(self.label_unit, 0, 5, 1, 1)
        self.unit_mil = QtGui.QRadioButton(self.groupBox)
        self.unit_mil.setObjectName(_fromUtf8("unit_mil"))
        self.gridLayout_2.addWidget(self.unit_mil, 0, 6, 1, 1)
        self.unit_mm = QtGui.QRadioButton(self.groupBox)
        self.unit_mm.setMaximumSize(QtCore.QSize(180, 16777215))
        self.unit_mm.setObjectName(_fromUtf8("unit_mm"))
        self.gridLayout_2.addWidget(self.unit_mm, 0, 7, 1, 1)
        self.label_np = QtGui.QLabel(self.groupBox)
        self.label_np.setMaximumSize(QtCore.QSize(100, 35))
        self.label_np.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_np.setObjectName(_fromUtf8("label_np"))
        self.gridLayout_2.addWidget(self.label_np, 1, 0, 1, 1)
        self.npSize = QtGui.QLineEdit(self.groupBox)
        self.npSize.setMinimumSize(QtCore.QSize(20, 25))
        self.npSize.setMaximumSize(QtCore.QSize(60, 25))
        self.npSize.setStyleSheet(_fromUtf8("font: 11pt \"Times New Roman\";\n"
"\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgb(137, 200, 255);\n"
"border-style:none;\n"
"\n"
"padding:5px;\n"
"min-height:15px;\n"
"border-radius:3px;"))
        self.npSize.setReadOnly(True)
        self.npSize.setObjectName(_fromUtf8("npSize"))
        self.gridLayout_2.addWidget(self.npSize, 1, 1, 1, 1)
        self.label_anti = QtGui.QLabel(self.groupBox)
        self.label_anti.setMaximumSize(QtCore.QSize(120, 35))
        self.label_anti.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_anti.setObjectName(_fromUtf8("label_anti"))
        self.gridLayout_2.addWidget(self.label_anti, 1, 2, 1, 1)
        self.antiSize = QtGui.QLineEdit(self.groupBox)
        self.antiSize.setMinimumSize(QtCore.QSize(20, 25))
        self.antiSize.setMaximumSize(QtCore.QSize(120, 25))
        self.antiSize.setStyleSheet(_fromUtf8("font: 11pt \"Times New Roman\";\n"
"\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgb(137, 200, 255);\n"
"border-style:none;\n"
"\n"
"padding:5px;\n"
"min-height:15px;\n"
"border-radius:3px;"))
        self.antiSize.setObjectName(_fromUtf8("antiSize"))
        self.gridLayout_2.addWidget(self.antiSize, 1, 3, 1, 1)
        self.label_loss_type = QtGui.QLabel(self.groupBox)
        self.label_loss_type.setMaximumSize(QtCore.QSize(120, 30))
        self.label_loss_type.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_loss_type.setObjectName(_fromUtf8("label_loss_type"))
        self.gridLayout_2.addWidget(self.label_loss_type, 1, 5, 1, 1)
        self.std_type = QtGui.QRadioButton(self.groupBox)
        self.std_type.setObjectName(_fromUtf8("std_type"))
        self.buttonGroup = QtGui.QButtonGroup(MainWindow)
        self.buttonGroup.setObjectName(_fromUtf8("buttonGroup"))
        self.buttonGroup.addButton(self.std_type)
        self.gridLayout_2.addWidget(self.std_type, 1, 6, 1, 1)
        self.less_type = QtGui.QRadioButton(self.groupBox)
        self.less_type.setMaximumSize(QtCore.QSize(180, 16777215))
        self.less_type.setObjectName(_fromUtf8("less_type"))
        self.buttonGroup.addButton(self.less_type)
        self.gridLayout_2.addWidget(self.less_type, 1, 7, 1, 1)
        self.label_pth = QtGui.QLabel(self.groupBox)
        self.label_pth.setMaximumSize(QtCore.QSize(100, 35))
        self.label_pth.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_pth.setObjectName(_fromUtf8("label_pth"))
        self.gridLayout_2.addWidget(self.label_pth, 2, 0, 1, 1)
        self.pthSize = QtGui.QLineEdit(self.groupBox)
        self.pthSize.setMinimumSize(QtCore.QSize(20, 25))
        self.pthSize.setMaximumSize(QtCore.QSize(60, 25))
        self.pthSize.setStyleSheet(_fromUtf8("font: 11pt \"Times New Roman\";\n"
"\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgb(137, 200, 255);\n"
"border-style:none;\n"
"\n"
"padding:5px;\n"
"min-height:15px;\n"
"border-radius:3px;"))
        self.pthSize.setReadOnly(True)
        self.pthSize.setObjectName(_fromUtf8("pthSize"))
        self.gridLayout_2.addWidget(self.pthSize, 2, 1, 1, 1)
        self.label_test = QtGui.QLabel(self.groupBox)
        self.label_test.setMaximumSize(QtCore.QSize(120, 35))
        self.label_test.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_test.setObjectName(_fromUtf8("label_test"))
        self.gridLayout_2.addWidget(self.label_test, 2, 2, 1, 1)
        self.testSize = QtGui.QLineEdit(self.groupBox)
        self.testSize.setMinimumSize(QtCore.QSize(20, 25))
        self.testSize.setMaximumSize(QtCore.QSize(120, 25))
        self.testSize.setStyleSheet(_fromUtf8("font: 11pt \"Times New Roman\";\n"
"\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgb(137, 200, 255);\n"
"border-style:none;\n"
"\n"
"padding:5px;\n"
"min-height:15px;\n"
"border-radius:3px;"))
        self.testSize.setObjectName(_fromUtf8("testSize"))
        self.gridLayout_2.addWidget(self.testSize, 2, 3, 1, 1)
        self.label_place = QtGui.QLabel(self.groupBox)
        self.label_place.setMaximumSize(QtCore.QSize(90, 30))
        self.label_place.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_place.setObjectName(_fromUtf8("label_place"))
        self.gridLayout_2.addWidget(self.label_place, 2, 5, 1, 1)
        self.loss_place = QtGui.QComboBox(self.groupBox)
        self.loss_place.setEnabled(False)
        self.loss_place.setMinimumSize(QtCore.QSize(90, 30))
        self.loss_place.setMaximumSize(QtCore.QSize(90, 30))
        self.loss_place.setStyleSheet(_fromUtf8("font: 10pt \"Agency FB\";\n"
"\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgb(137, 200, 255);\n"
"border-style:none;\n"
"\n"
"padding:5px;\n"
"min-height:20px;\n"
"border-radius:3px;"))
        self.loss_place.setObjectName(_fromUtf8("loss_place"))
        self.loss_place.addItem(_fromUtf8(""))
        self.loss_place.addItem(_fromUtf8(""))
        self.gridLayout_2.addWidget(self.loss_place, 2, 6, 1, 1)
        self.gridLayout_4.addWidget(self.groupBox, 0, 0, 1, 1)
        self.gridLayout_5.addLayout(self.gridLayout_4, 1, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.groupBox_3 = QtGui.QGroupBox(MainWindow)
        self.groupBox_3.setMinimumSize(QtCore.QSize(200, 400))
        self.groupBox_3.setMaximumSize(QtCore.QSize(1920, 1000))
        self.groupBox_3.setObjectName(_fromUtf8("groupBox_3"))
        self.gridLayout = QtGui.QGridLayout(self.groupBox_3)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.tableWidget = QtGui.QTableWidget(self.groupBox_3)
        self.tableWidget.setMaximumSize(QtCore.QSize(1800, 920))
        self.tableWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableWidget.setGridStyle(QtCore.Qt.DotLine)
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        self.tableWidget.setColumnCount(10)
        self.tableWidget.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(4, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(5, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(6, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(7, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(8, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(9, item)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(95)
        self.tableWidget.horizontalHeader().setMinimumSectionSize(21)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setDefaultSectionSize(30)
        self.tableWidget.verticalHeader().setMinimumSectionSize(21)
        self.gridLayout.addWidget(self.tableWidget, 0, 0, 1, 1)
        self.horizontalLayout.addWidget(self.groupBox_3)
        self.gridLayout_5.addLayout(self.horizontalLayout, 2, 0, 1, 1)
        self.gridLayout_6 = QtGui.QGridLayout()
        self.gridLayout_6.setObjectName(_fromUtf8("gridLayout_6"))
        self.exit_btn = QtGui.QPushButton(MainWindow)
        self.exit_btn.setMinimumSize(QtCore.QSize(100, 30))
        self.exit_btn.setMaximumSize(QtCore.QSize(70, 35))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.exit_btn.setFont(font)
        self.exit_btn.setStyleSheet(_fromUtf8("color: rgb(255, 255, 255);\n"
"background-color: rgb(137, 200, 255);"))
        self.exit_btn.setObjectName(_fromUtf8("exit_btn"))
        self.gridLayout_6.addWidget(self.exit_btn, 0, 3, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_6.addItem(spacerItem, 0, 2, 1, 1)
        self.create_btn = QtGui.QPushButton(MainWindow)
        self.create_btn.setMinimumSize(QtCore.QSize(100, 30))
        self.create_btn.setMaximumSize(QtCore.QSize(90, 35))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.create_btn.setFont(font)
        self.create_btn.setStyleSheet(_fromUtf8("color: rgb(255, 255, 255);\n"
"background-color: rgb(137, 200, 255);"))
        self.create_btn.setObjectName(_fromUtf8("create_btn"))
        self.gridLayout_6.addWidget(self.create_btn, 0, 1, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(40, 25, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_6.addItem(spacerItem1, 0, 0, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_6.addItem(spacerItem2, 0, 4, 1, 1)
        self.gridLayout_5.addLayout(self.gridLayout_6, 3, 0, 1, 1)

        self.retranslateUi(MainWindow)
        QtCore.QObject.connect(self.exit_btn, QtCore.SIGNAL(_fromUtf8("clicked()")), MainWindow.close)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "自动创建loss_coupon", None))
        self.bottomLabel.setText(_translate("MainWindow", "版权所有：胜宏科技 作者：Michael & Chuang 日期：2021.7.6", None))
        self.label_title.setText(_translate("MainWindow", "Auto Loss Coupon", None))
        self.groupBox.setTitle(_translate("MainWindow", "参数选择（单位：mil）", None))
        self.label_via.setText(_translate("MainWindow", "VIA孔大小：", None))
        self.label_tilt_via.setText(_translate("MainWindow", "伴地孔大小：", None))
        self.label_unit.setText(_translate("MainWindow", "单位：", None))
        self.unit_mil.setText(_translate("MainWindow", "mil", None))
        self.unit_mm.setText(_translate("MainWindow", "mm", None))
        self.label_np.setText(_translate("MainWindow", "NP孔大小：", None))
        self.label_anti.setText(_translate("MainWindow", "Anti Pad 大小：", None))
        self.label_loss_type.setText(_translate("MainWindow", "loss条长度：", None))
        self.std_type.setText(_translate("MainWindow", "2/5/10inch", None))
        self.less_type.setText(_translate("MainWindow", "2/6inch", None))
        self.label_pth.setText(_translate("MainWindow", "PTH孔大小：", None))
        self.label_test.setText(_translate("MainWindow", "测试 Pad 大小：", None))
        self.label_place.setText(_translate("MainWindow", "loss排列方式：", None))
        self.loss_place.setItemText(0, _translate("MainWindow", "横排", None))
        self.loss_place.setItemText(1, _translate("MainWindow", "品字形", None))
        self.groupBox_3.setTitle(_translate("MainWindow", "阻抗列表", None))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "层别", None))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "线宽", None))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "间距", None))
        item = self.tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("MainWindow", "参考1", None))
        item = self.tableWidget.horizontalHeaderItem(4)
        item.setText(_translate("MainWindow", "参考2", None))
        item = self.tableWidget.horizontalHeaderItem(5)
        item.setText(_translate("MainWindow", "原稿线宽", None))
        item = self.tableWidget.horizontalHeaderItem(6)
        item.setText(_translate("MainWindow", "原稿间距", None))
        item = self.tableWidget.horizontalHeaderItem(7)
        item.setText(_translate("MainWindow", "欧姆值(Ω)", None))
        item = self.tableWidget.horizontalHeaderItem(8)
        item.setText(_translate("MainWindow", "补偿值", None))
        item = self.tableWidget.horizontalHeaderItem(9)
        item.setText(_translate("MainWindow", "客户原稿(线宽/线距)", None))
        self.exit_btn.setText(_translate("MainWindow", "退出", None))
        self.create_btn.setText(_translate("MainWindow", "创建", None))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QWidget()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

