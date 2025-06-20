#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:GenerateUserXml.py
   @author:zl
   @time: 2024/12/27 18:07
   @software:PyCharm
   @desc:
   更新user.xml
"""
import os
import pprint
import sys
from hashlib import md5

import qtawesome, xmltodict
import pandas as pd

import GenerateUserXmlUI as ui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from TOPCAM_IKM import IKM
import res_rc

class GenerateUserXml(QMainWindow, ui.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.xml_dict = {}
        self.update_data = []
        # export path
        self.export_path = './new.xml'
        self.ikm_fun = IKM()
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        # xml信息
        header = ['工号', '姓名', 'topcam密码', 'incam密码']
        self.tableWidget.setColumnCount(len(header))
        self.tableWidget.setHorizontalHeaderLabels(header)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        header = ['工号', '姓名', 'topcam密码', 'incam密码', 'incam加密密码']
        self.tableWidget_2.setColumnCount(len(header))
        self.tableWidget_2.setHorizontalHeaderLabels(header)
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget_2.verticalHeader().hide()
        self.tableWidget.setItemDelegateForColumn(0, EmptyDelegate(self))
        self.tableWidget.setItemDelegateForColumn(2, EmptyDelegate(self))
        self.tableWidget_2.setItemDelegateForColumn(3, EmptyDelegate(self))
        self.tableWidget_2.setItemDelegateForColumn(4, EmptyDelegate(self))
        self.actionLoadUserXml.setIcon(qtawesome.icon('fa.folder-open', color='orange'))
        self.actionImportXlsx.setIcon(qtawesome.icon('fa.download', color='orange'))
        self.actionAddUser.setIcon(qtawesome.icon('ri.user-add-line', color='orange'))
        self.actionUpdateUser.setIcon(qtawesome.icon('fa.play-circle', color='orange'))
        self.actionExportXml.setIcon(qtawesome.icon('fa.sign-out', color='orange'))
        self.menu.triggered.connect(self.pressAction)
        self.setStyleSheet('QStatusBar {color:green;}')

    def pressAction(self, act):
        if act.text() == '打开UserXml':
            file_dialog = QFileDialog()
            OpenFilename = file_dialog.getOpenFileName(self, "选择xml文件", os.getcwd(), 'All Files(*.xml)')
            filename = OpenFilename[0]
            if filename:
                self.parseFile(filename)
        elif act.text() == '导入待更新xlsx':
            self.import_xlsx()
        elif act.text() == '添加用户':
            self.add_user()
        elif act.text() == '更新用户':
            self.update_table()
        elif act.text() == '导出xml':
            self.export_xml()

    def parseFile(self, filename):
        with open(filename, 'r', encoding='utf8') as f:
            xml_content = f.read()
        self.xml_dict = xmltodict.parse(xml_content)
        # pprint.pprint(self.xml_dict)
        users_info = self.xml_dict.get('Users').get('user')
        self.tableWidget.setRowCount(len(users_info))
        for row, user in enumerate(users_info):
            self.tableWidget.setItem(row, 0, QTableWidgetItem(user.get('@name')))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(user.get('properties').get('@fullName')))
            self.tableWidget.setItem(row, 2, QTableWidgetItem('******'))
            self.tableWidget.setItem(row, 3, QTableWidgetItem(user.get('properties').get('@password')))

    def import_xlsx(self):
        file_dialog = QFileDialog()
        OpenFilename = file_dialog.getOpenFileName(self, "选择xlsx文件", os.getcwd(), 'All Files(*.xlsx)')
        filename = OpenFilename[0]
        if not filename:
            QMessageBox.warning(self, '提示', '请选择xlsx文件')
            return
        data = pd.read_excel(filename, dtype={'工号': 'Int64'})
        # print(data)
        # df = data.iloc[:, [0, 2, 5, 7]]
        df = data.iloc[:, :11]
        # print(df)
        self.update_data.clear()
        for index, row in df.iterrows():
            if not pd.isna(row.values[:5]).any():
                self.update_data.append(row.values[:5])
            if not pd.isna(row.values[5:]).any():
                self.update_data.append(row.values[5:])
        # print(self.update_data)
        self.tableWidget_2.setRowCount(len(self.update_data))
        for row, user in enumerate(self.update_data):
            self.tableWidget_2.setItem(row, 0, QTableWidgetItem(str(user[0])))
            self.tableWidget_2.setItem(row, 1, QTableWidgetItem(str(user[1])))
            self.tableWidget_2.setItem(row, 2, QTableWidgetItem(str(user[2])))
            self.tableWidget_2.setItem(row, 3, QTableWidgetItem(str(user[3])))
            self.tableWidget_2.setItem(row, 4, QTableWidgetItem(str(user[4])))

    def add_user(self):
        AddUser(self)

    def update_table(self):
        for row in range(self.tableWidget.rowCount()):
            name = self.tableWidget.item(row, 0).text()
            user_list = list(filter(lambda data: str(data[0]) == name, self.update_data))
            if user_list:
                user = user_list[-1]
                self.tableWidget.setItem(row, 1, QTableWidgetItem(str(user[1])))
                self.tableWidget.setItem(row, 2, QTableWidgetItem(str(user[2])))
                self.tableWidget.setItem(row, 3, QTableWidgetItem(str(user[4])))

        if self.update_data:
            count = self.update_topcam()
            self.statusbar.showMessage('topcam密码更新成功！更新数量：%s' % count)
        else:
            self.statusbar.showMessage('请导入或添加用户信息')

    def update_topcam(self):
        update_count = 0
        for staffid, _, topcam_pwd, _, _ in self.update_data:
            pwd = pwd.strip()
            sql = """update sys_user set password='%s' where staffid='%s'""" % (self.get_md5(pwd), staffid)
            data_info = self.ikm_fun.PG.SQL_EXECUTE(self.ikm_fun.dbc_p, sql)
            if data_info:
                print('%s已更新密码%s' % (staffid, pwd))
                update_count += 1
        return update_count

    def export_xml(self):
        for row in range(self.tableWidget.rowCount()):
            name = self.tableWidget.item(row, 0).text()
            fullName = self.tableWidget.item(row, 1).text()
            password = self.tableWidget.item(row, 3).text()
            for user in self.xml_dict.get('Users').get('user'):
                if name == user.get('@name'):
                    user['properties']['@fullName'] = fullName
                    user['properties']['@password'] = password
        if self.xml_dict:
            data = xmltodict.unparse(self.xml_dict, pretty=True)
            with open(self.export_path, mode='w', encoding='utf8') as w:
                w.write(data)
            self.statusbar.showMessage('导出成功！%s' % self.export_path)
        else:
            self.statusbar.showMessage('请导入用户xml信息')

    @classmethod
    def get_md5(cls, s):
        return md5(s.encode()).hexdigest()

class AddUser(QDialog):
    def __init__(self, parent):
        super(AddUser, self).__init__(parent)
        self.render()
        self.exec_()

    def render(self):
        self.setWindowTitle('添加用户')
        self.resize(260, 240)
        layout = QVBoxLayout(self)
        flayout = QFormLayout()
        self.user = QLineEdit()
        self.user.setValidator(QDoubleValidator())
        self.fullname = QLineEdit()
        self.topcamword = QLineEdit()
        self.incampwd = QLineEdit()
        self.incampwd2 = QLineEdit()
        flayout.addRow('工号：', self.user)
        flayout.addRow('姓名：', self.fullname)
        flayout.addRow('topcam密码：', self.topcamword)
        flayout.addRow('incam密码：', self.incampwd)
        flayout.addRow('incam密文：', self.incampwd2)
        btn_box = QHBoxLayout()
        ok = QPushButton(self)
        ok.setText('OK')
        ok.setStyleSheet('background-color:#0081a6;color:white;')
        ok.setObjectName('dialog_ok')
        ok.setCursor(QCursor(Qt.PointingHandCursor))
        ok.clicked.connect(self.user_add)
        close = QPushButton(self)
        close.setText('Close')
        close.setStyleSheet('background-color:#464646;color:white;')
        close.setObjectName('dialog_close')
        close.setCursor(QCursor(Qt.PointingHandCursor))
        close.clicked.connect(lambda: self.close())
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_box.addItem(spacerItem1)
        btn_box.addWidget(ok)
        btn_box.addWidget(close)
        layout.addLayout(flayout)
        layout.addLayout(btn_box)
        self.setStyleSheet('font-family:黑体;font-size:10pt;')

    def user_add(self):
        user = self.user.text().strip()
        fullname = self.fullname.text().strip()
        topcamword = self.topcamword.text().strip()
        incampwd = self.incampwd.text().strip()
        incampwd2 = self.incampwd2.text().strip()
        if not user or not topcamword or not incampwd or not incampwd2:
            QMessageBox.warning(self, '提示', '工号、topcam/incam密码、密文不能为空！')
            return
        new_row = generateUserXml.tableWidget_2.rowCount()
        generateUserXml.tableWidget_2.insertRow(new_row)  # 添加新行
        generateUserXml.tableWidget_2.setItem(new_row, 0, QTableWidgetItem(user))
        generateUserXml.tableWidget_2.setItem(new_row, 1, QTableWidgetItem(fullname))
        generateUserXml.tableWidget_2.setItem(new_row, 2, QTableWidgetItem(topcamword))
        generateUserXml.tableWidget_2.setItem(new_row, 3, QTableWidgetItem(incampwd))
        generateUserXml.tableWidget_2.setItem(new_row, 4, QTableWidgetItem(incampwd2))

        self.close()


# 代理类
class EmptyDelegate(QItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        return None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setWindowIcon(QIcon(':res/demo.png'))
    generateUserXml = GenerateUserXml()
    generateUserXml.show()
    sys.exit(app.exec_())
