#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:GenerateUserXml.py
   @author:zl
   @time: 2024/12/27 18:07
   @software:PyCharm
   @desc:
   更新user.xml
   20250116 判断是否有用户 update/insert
"""
import datetime
import os
import pprint
import sys
import time
from hashlib import md5

import qtawesome, xmltodict
import pandas as pd
from docutils.parsers.rst.directives.misc import Role

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
        self.export_path = './users_now.xml'
        self.curScr_row = None
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
        self.actionResetData.setIcon(qtawesome.icon('mdi.delete-circle-outline', color='orange'))
        self.menu.triggered.connect(self.pressAction)
        self.tableWidget_2.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableWidget_2.customContextMenuRequested.connect(self.DoScrClickMouseRight)
        self.tableWidget_2.currentItemChanged.connect(self.DoTableScrChange)
        self.setStyleSheet('QStatusBar {color:green;}')


    def DoTableScrChange(self):
        cur_row = self.tableWidget_2.currentRow()
        if cur_row < 0:
            self.curScr_row = None
        else:
            self.curScr_row = cur_row
    def DoScrClickMouseRight(self, position):
        if self.curScr_row is None:
            return
        print(self.curScr_row)
        # 弹出菜单
        popMenu = QMenu()
        runLocal = QAction("编辑", icon=qtawesome.icon('fa.play-circle', scale_factor=1, color='orange'))
        if self.tableWidget_2.itemAt(position):
            popMenu.addAction(runLocal)
        action = popMenu.exec_(self.tableWidget_2.mapToGlobal(position))
        if action == runLocal:  # 本地运行
            QApplication.processEvents()
            AddUser(self)
        else:
            return
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
        elif act.text() == '重置数据':
            self.reset_data()

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
        self.curScr_row = None
        AddUser(self)

    def update_table(self):
        # for row in range(self.tableWidget.rowCount()):
        #     name = self.tableWidget.item(row, 0).text()
        #     user_list = list(filter(lambda data: str(data[0]) == name, self.update_data))
        #     if user_list:
        #         user = user_list[-1]
        #         self.tableWidget.setItem(row, 1, QTableWidgetItem(str(user[1])))
        #         self.tableWidget.setItem(row, 2, QTableWidgetItem(str(user[2])))
        #         self.tableWidget.setItem(row, 3, QTableWidgetItem(str(user[4])))
        # 优化  按待更新的去找table里的数据
        table_rows = self.tableWidget.rowCount()
        new_row = self.tableWidget.rowCount()
        for data in self.update_data:
            update_flag = False
            for row in range(table_rows):
                name = self.tableWidget.item(row, 0).text()
                if data[0] == name:  # table中找到就break
                    self.tableWidget.setItem(row, 1, QTableWidgetItem(str(data[1])))
                    self.tableWidget.setItem(row, 2, QTableWidgetItem(str(data[2])))
                    self.tableWidget.setItem(row, 3, QTableWidgetItem(str(data[4])))
                    update_flag = True
                    break
            if not update_flag:  # 没有找到 则新增
                self.tableWidget.insertRow(new_row)  # 添加新行
                self.tableWidget.setItem(new_row, 0, QTableWidgetItem(data[0]))
                self.tableWidget.setItem(new_row, 1, QTableWidgetItem(data[1]))
                self.tableWidget.setItem(new_row, 2, QTableWidgetItem(data[2]))
                self.tableWidget.setItem(new_row, 3, QTableWidgetItem(data[4]))
                new_row += 1
        print(self.update_data)
        # if self.update_data:
        #     # count = self.update_topcam()
        #     # self.statusbar.showMessage('topcam密码更新成功！更新数量：%s' % count)
        # else:
        #     self.statusbar.showMessage('请导入或添加用户信息')

    def update_topcam(self):
        update_count = 0
        for staffid, name, topcam_pwd, _, _ in self.update_data:
            pwd = topcam_pwd.strip()
            sql = """select * from sys_user where staffid='%s'""" % staffid
            user_info = self.ikm_fun.PG.SELECT_DIC(self.ikm_fun.dbc_p, sql)
            if not user_info:
                sql = """insert into sys_user(staffid,fullname,username,password,status,remark,attr_data,product_category) values('%s', '%s', '%s', '%s', 'active', 'HDI CAM制作','{"effective_date": "%s", "validity_period": "", "password_validity_control": 0}', '{top-dfm}')""" % (
                staffid, name, staffid, self.get_md5(pwd), datetime.datetime.now().strftime('%Y-%m-%d'))
                data_info = self.ikm_fun.PG.SQL_EXECUTE(self.ikm_fun.dbc_p, sql)
                if data_info:
                    print('已新增用户%s' % staffid)
                    update_count += 1
            else:
                sql = """update sys_user set password='%s',username='%s',fullname='%s' where staffid='%s'""" % (
                self.get_md5(pwd), staffid, name, staffid)
                data_info = self.ikm_fun.PG.SQL_EXECUTE(self.ikm_fun.dbc_p, sql)
                if data_info:
                    print('%s已更新密码%s' % (staffid, topcam_pwd))
                    update_count += 1
        return update_count

    def export_xml(self):
        pprint.pprint(self.xml_dict)
        if self.xml_dict:
            for row in range(self.tableWidget.rowCount()):
                name = self.tableWidget.item(row, 0).text()
                fullName = self.tableWidget.item(row, 1).text()
                password = self.tableWidget.item(row, 3).text()
                get_flag = False
                for user in self.xml_dict.get('Users').get('user'):
                    if name == user.get('@name'):
                        user['properties']['@fullName'] = fullName
                        user['properties']['@password'] = password
                        get_flag = True
                        break
                if not get_flag:  # update到self.xml_dict
                    self.xml_dict['Users']['user'].append({
                        '@name': f'{name}',
                        'properties': {'@autoLogin': 'no',
                                       '@encrypted': 'yes',
                                       '@fullName': f'{fullName}',
                                       '@group': 'Cam',
                                       '@obsolete': 'no',
                                       '@osUserName': '',
                                       '@password': f'{password}',
                                       '@priv': '50',
                                       '@profileNfsPath': f'/incam/server/users/{name}',
                                       '@profileWinPath': '',
                                       '@useOSUserName': 'no'}})
            data = xmltodict.unparse(self.xml_dict, pretty=True)
            with open(self.export_path, mode='w', encoding='utf8') as w:
                w.write(data)
            self.statusbar.showMessage('导出成功！%s' % self.export_path)
        else:
            self.statusbar.showMessage('请导入用户xml信息')

    def reset_data(self):
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)
        self.tableWidget_2.clearContents()
        self.tableWidget_2.setRowCount(0)
        self.update_data.clear()
        self.xml_dict.clear()

    @classmethod
    def get_md5(cls, s):
        return md5(s.encode()).hexdigest()


class AddUser(QDialog):
    def __init__(self, parent):
        super(AddUser, self).__init__(parent)
        self.render()
        self.exec_()

    def render(self):
        self.mode = 'add' if generateUserXml.curScr_row is None else 'edit'
        self.userid = None
        self.setWindowTitle('添加用户') if self.mode == 'add' else self.setWindowTitle('编辑用户')
        self.resize(260, 240)
        layout = QVBoxLayout(self)
        flayout = QFormLayout()
        self.user = QLineEdit()
        self.user.setValidator(QDoubleValidator())
        self.fullname = QLineEdit()
        self.role_btn = QPushButton('角色编辑')
        self.role_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.topcamword = QLineEdit()
        self.incampwd = QLineEdit()
        self.incampwd2 = QLineEdit()
        flayout.addRow('工号：', self.user)
        flayout.addRow('姓名：', self.fullname)
        flayout.addRow('角色：', self.role_btn)
        flayout.addRow('topcam密码：', self.topcamword)
        flayout.addRow('incam密码：', self.incampwd)
        flayout.addRow('incam密文：', self.incampwd2)
        btn_box = QHBoxLayout()
        ok_button = QPushButton()
        # ok_button.setAutoDefault(False)
        ok_button.setText('OK')
        ok_button.setStyleSheet('background-color:#0081a6;color:white;')
        ok_button.setObjectName('dialog_ok')
        ok_button.setCursor(QCursor(Qt.PointingHandCursor))
        close_button = QPushButton()
        close_button.setText('Close')
        close_button.setStyleSheet('background-color:#464646;color:white;')
        close_button.setObjectName('dialog_close')
        close_button.setCursor(QCursor(Qt.PointingHandCursor))
        close_button.clicked.connect(lambda: self.close())
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_box.addItem(spacerItem1)
        btn_box.addWidget(ok_button)
        btn_box.addWidget(close_button)
        layout.addLayout(flayout)
        layout.addLayout(btn_box)
        self.setStyleSheet('font-family:黑体;font-size:10pt;')
        # 输入完工号带出信息
        self.user.returnPressed.connect(self.loaduser)
        self.role_btn.clicked.connect(self.role_edit)
        ok_button.clicked.connect(self.user_add)
        # 编辑用户
        if self.mode == 'edit':
            staffid = generateUserXml.tableWidget_2.item(generateUserXml.curScr_row, 0).text()
            name = generateUserXml.tableWidget_2.item(generateUserXml.curScr_row, 1).text()
            topcamword = generateUserXml.tableWidget_2.item(generateUserXml.curScr_row, 2).text()
            incampwd = generateUserXml.tableWidget_2.item(generateUserXml.curScr_row, 3).text()
            incampwd2 = generateUserXml.tableWidget_2.item(generateUserXml.curScr_row, 4).text()
            self.user.setText(staffid)
            self.fullname.setText(name)
            self.topcamword.setText(topcamword)
            self.incampwd.setText(incampwd)
            self.incampwd2.setText(incampwd2)
    def user_add(self):
        user = self.user.text().strip()
        fullname = self.fullname.text().strip()
        topcamword = self.topcamword.text().strip()
        incampwd = self.incampwd.text().strip()
        incampwd2 = self.incampwd2.text().strip()
        if not user or (not topcamword and not incampwd2):
            QMessageBox.warning(self, '提示', '工号不能为空！topcam和incam密码不能都为空！')
            return
        if self.mode == 'add':
            new_row = generateUserXml.tableWidget_2.rowCount()
            generateUserXml.tableWidget_2.insertRow(new_row)  # 添加新行
            generateUserXml.tableWidget_2.setItem(new_row, 0, QTableWidgetItem(user))
            generateUserXml.tableWidget_2.setItem(new_row, 1, QTableWidgetItem(fullname))
            generateUserXml.tableWidget_2.setItem(new_row, 2, QTableWidgetItem(topcamword))
            generateUserXml.tableWidget_2.setItem(new_row, 3, QTableWidgetItem(incampwd))
            generateUserXml.tableWidget_2.setItem(new_row, 4, QTableWidgetItem(incampwd2))
            generateUserXml.update_data.append([user, fullname, topcamword, incampwd, incampwd2])
        else:
            new_row = generateUserXml.curScr_row
            # generateUserXml.tableWidget_2.insertRow(new_row)  # 添加新行
            generateUserXml.tableWidget_2.setItem(new_row, 0, QTableWidgetItem(user))
            generateUserXml.tableWidget_2.setItem(new_row, 1, QTableWidgetItem(fullname))
            generateUserXml.tableWidget_2.setItem(new_row, 2, QTableWidgetItem(topcamword))
            generateUserXml.tableWidget_2.setItem(new_row, 3, QTableWidgetItem(incampwd))
            generateUserXml.tableWidget_2.setItem(new_row, 4, QTableWidgetItem(incampwd2))
            generateUserXml.update_data[new_row] = [user, fullname, topcamword, incampwd, incampwd2]
        self.close()

    def loaduser(self):
        staffid = self.user.text()
        sql = """select id, fullname,password from sys_user where staffid='%s'""" % staffid
        user_info = generateUserXml.ikm_fun.PG.SELECT_DIC(generateUserXml.ikm_fun.dbc_p, sql)
        if user_info:
            self.fullname.setText(user_info[-1]['fullname'])
            self.userid = user_info[-1]['id']
            # self.topcamword.setText(user_info[-1]['password'])  # 没有原始密码 只有加密后的，且无法解密回原始密码 所以这里不显示

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            pass
        else:
            super(AddUser, self).keyPressEvent(event)

    def role_edit(self):
        role = Role(self, id=self.userid)
        role.edit_role.connect(self.set_role)
        role.exec_()

    def set_role(self, ids):
        print('aaa', ids)

class Role(QDialog):
    edit_role = pyqtSignal(list)
    def __init__(self, parent=None, id=None):
        super(Role, self).__init__(parent)
        self.userid = id
        self.render()

    def render(self):
        self.setWindowTitle('编辑角色')
        self.resize(260, 240)
        layout = QVBoxLayout(self)
        self.role_table = QTableWidget()
        cols = ['角色名称', '描述', 'id']
        self.role_table.setColumnCount(len(cols))
        self.role_table.setHorizontalHeaderLabels(cols)
        # 获取
        self.role_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.role_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.role_table.setColumnHidden(2, True)
        layout.addWidget(self.role_table)
        role_ids = []
        if self.userid:
            sql = "SELECT role_id FROM sys_role_map_user where user_id = '%s'" % self.userid
            role_info = generateUserXml.ikm_fun.PG.SELECT_DIC(generateUserXml.ikm_fun.dbc_p, sql)

            for role in role_info:
                role_ids.append(role['role_id'])
        print(role_ids)
        sql = 'SELECT id,name,description FROM sys_role order by id'
        role_info = generateUserXml.ikm_fun.PG.SELECT_DIC(generateUserXml.ikm_fun.dbc_p, sql)
        self.role_table.setRowCount(len(role_info))
        print(role_info)
        select_rows = []
        for row, role in enumerate(role_info):
            self.role_table.setItem(row, 0, QTableWidgetItem(role['name']))
            self.role_table.setItem(row, 1, QTableWidgetItem(role['description']))
            self.role_table.setItem(row, 2, QTableWidgetItem(str(role['id'])))
            if role['id'] in role_ids:
                select_rows.append(row)
        if role_ids:
            for select_row in select_rows:
                self.role_table.selectRow(select_row)
        else:
            # 默认为HDI CAM制作
            self.role_table.selectRow(5)

        btn_box = QHBoxLayout()
        ok_button = QPushButton()
        # ok_button.setAutoDefault(False)
        ok_button.setText('OK')
        ok_button.setStyleSheet('background-color:#0081a6;color:white;')
        ok_button.setObjectName('dialog_ok')
        ok_button.setCursor(QCursor(Qt.PointingHandCursor))
        ok_button.clicked.connect(self.role_ok)
        close_button = QPushButton()
        close_button.setText('Close')
        close_button.setStyleSheet('background-color:#464646;color:white;')
        close_button.setObjectName('dialog_close')
        close_button.setCursor(QCursor(Qt.PointingHandCursor))
        close_button.clicked.connect(lambda: self.close())
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_box.addItem(spacerItem1)
        btn_box.addWidget(ok_button)
        btn_box.addWidget(close_button)
        layout.addLayout(btn_box)

    def role_ok(self):
        selected_rows = [index.row() for index in self.role_table.selectionModel().selectedRows()]
        role_ids = [int(self.role_table.item(row, 2).text()) for row in selected_rows]
        print(role_ids)
        self.edit_role.emit(role_ids)
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
