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
import re
import sys
import time
from hashlib import md5

import qtawesome, xmltodict
import pandas as pd
import numpy as np
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
        header = ['工号', '姓名', '角色id', 'topcam密码', 'incam密码', 'incam加密密码']
        self.tableWidget_2.setColumnCount(len(header))
        self.tableWidget_2.setHorizontalHeaderLabels(header)
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget_2.verticalHeader().hide()
        self.tableWidget.setItemDelegateForColumn(0, EmptyDelegate(self))
        self.tableWidget.setItemDelegateForColumn(2, EmptyDelegate(self))
        self.tableWidget_2.setItemDelegateForColumn(2, EmptyDelegate(self))
        self.tableWidget_2.setItemDelegateForColumn(4, EmptyDelegate(self))
        self.tableWidget_2.setItemDelegateForColumn(5, EmptyDelegate(self))
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
        # print(self.curScr_row)
        # 弹出菜单
        popMenu = QMenu()
        runLocal = QAction("编辑", icon=qtawesome.icon('fa.play-circle', scale_factor=1, color='orange'))
        removeLocal = QAction("删除", icon=qtawesome.icon('mdi.delete-circle-outline', scale_factor=1, color='#B54747'))
        if self.tableWidget_2.itemAt(position):
            popMenu.addAction(runLocal)
            popMenu.addAction(removeLocal)
        action = popMenu.exec_(self.tableWidget_2.mapToGlobal(position))
        if action == runLocal:  # 本地运行
            # QApplication.processEvents()
            AddUser(self)
        elif action == removeLocal:
            self.tableWidget_2.removeRow(self.curScr_row)
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
                self.update_data.append(list(row.values[:5]))
            if not pd.isna(row.values[5:]).any():
                self.update_data.append(list(row.values[5:]))
        self.tableWidget_2.setRowCount(len(self.update_data))
        for row, user in enumerate(self.update_data):
            role_ids = self.get_roleid(user[0])
            self.tableWidget_2.setItem(row, 0, QTableWidgetItem(str(user[0])))
            self.tableWidget_2.setItem(row, 1, QTableWidgetItem(str(user[1])))
            self.tableWidget_2.setItem(row, 2, QTableWidgetItem(str(role_ids)))  # 默认
            self.tableWidget_2.setItem(row, 3, QTableWidgetItem(str(user[2])))
            self.tableWidget_2.setItem(row, 4, QTableWidgetItem(str(user[3])))
            self.tableWidget_2.setItem(row, 5, QTableWidgetItem(str(user[4])))
            user.insert(2, role_ids)

    def get_roleid(self, staffid):
        sql = """select id from sys_user where staffid='%s'""" % staffid
        user_info = self.ikm_fun.PG.SELECT_DIC(self.ikm_fun.dbc_p, sql)
        if user_info:
            userid = user_info[0].get('id')
            sql = """select * from sys_role_map_user where user_id='%s'""" % userid
            user_info = self.ikm_fun.PG.SELECT_DIC(self.ikm_fun.dbc_p, sql)
            print(user_info)
            if user_info:
                ids = [info['role_id'] for info in user_info]
            else:
                ids = [7] # 默认
        else:
            ids = [7]  # 默认
        return ids
    def add_user(self):
        self.curScr_row = None
        AddUser(self)

    def update_table(self):
        self.update_data.clear()
        for row in range(self.tableWidget_2.rowCount()):
            user = self.tableWidget_2.item(row, 0).text()
            fullname = self.tableWidget_2.item(row, 1).text()
            role_idstr = self.tableWidget_2.item(row, 2).text()
            topcamword = self.tableWidget_2.item(row, 3).text()
            incampwd = self.tableWidget_2.item(row, 4).text()
            incampwd2 = self.tableWidget_2.item(row, 5).text()
            role_ids = [int(id) for id in re.sub('[\[\]]', '', role_idstr).split(',')]
            self.update_data.append([user, fullname, role_ids, topcamword, incampwd, incampwd2])
        # 优化  按待更新的去找table里的数据
        table_rows = self.tableWidget.rowCount()
        new_row = self.tableWidget.rowCount()
        print(self.update_data)
        for data in self.update_data:
            update_flag = False
            for row in range(table_rows):
                name = self.tableWidget.item(row, 0).text()
                if data[0] == name:  # table中找到就break
                    self.tableWidget.setItem(row, 1, QTableWidgetItem(str(data[1])))
                    self.tableWidget.setItem(row, 2, QTableWidgetItem(str(data[3])))
                    self.tableWidget.setItem(row, 3, QTableWidgetItem(str(data[5])))
                    update_flag = True
                    break
            if not update_flag:  # 没有找到 则新增
                self.tableWidget.insertRow(new_row)  # 添加新行
                self.tableWidget.setItem(new_row, 0, QTableWidgetItem(str(data[0])))
                self.tableWidget.setItem(new_row, 1, QTableWidgetItem(data[1]))
                self.tableWidget.setItem(new_row, 2, QTableWidgetItem(data[3]))
                self.tableWidget.setItem(new_row, 3, QTableWidgetItem(data[5]))
                new_row += 1

        if self.update_data:
            count = self.update_topcam()
            self.statusbar.showMessage('topcam密码更新成功！更新数量：%s' % count)
        else:
            self.statusbar.showMessage('请导入或添加用户信息')

    def update_topcam(self):
        update_count = 0
        for staffid, name, roleids, topcam_pwd, _, _ in self.update_data:
            pwd = topcam_pwd.strip()
            # print(roleids)
            sql = """select * from sys_user where staffid='%s'""" % staffid
            user_info = self.ikm_fun.PG.SELECT_DIC(self.ikm_fun.dbc_p, sql)
            if not user_info:
                try:
                    sql = """insert into sys_user(staffid,fullname,username,password,status,remark,attr_data,product_category) values('%s', '%s', '%s', '%s', 'active', '','{"effective_date": "%s", "validity_period": "", "password_validity_control": 0}', '{}')""" % (
                    staffid, name, staffid, self.get_md5(pwd), datetime.datetime.now().strftime('%Y-%m-%d'))
                    data_info = self.ikm_fun.PG.SQL_EXECUTE(self.ikm_fun.dbc_p, sql)
                    if data_info:
                        print('已新增用户%s' % staffid)
                        update_count += 1
                    sql = 'select max(id) as id from sys_user'
                    data_info = self.ikm_fun.PG.SELECT_DIC(self.ikm_fun.dbc_p, sql)
                    userid = data_info[0]['id']
                    # 所有product_category
                    product_category_list = []
                    for roleid in roleids:
                        sql = "select name, product_category from sys_role where id = '%s'" % roleid
                        data_info = self.ikm_fun.PG.SELECT_DIC(self.ikm_fun.dbc_p, sql)
                        role_name = data_info[0]['name']
                        product_category_list.append( data_info[0]['product_category'])
                        sql = "insert into sys_role_map_user(role_id,user_id) values('%s','%s')" % (roleid, userid)
                        data_info = self.ikm_fun.PG.SQL_EXECUTE(self.ikm_fun.dbc_p, sql)
                        if data_info:
                            print('%s已增加角色->%s' % (staffid, role_name))
                    category = '{*}' if '{*}' in product_category_list else '{top-dfm}'
                    # 补充user表数据
                    sql = """update sys_user set contcat_id='%s',product_category='%s' where id='%s'""" % (userid, category, userid)
                    self.ikm_fun.PG.SQL_EXECUTE(self.ikm_fun.dbc_p, sql)
                except Exception as e:
                    print(e)
            else:
                # print(user_info[0]['id'])
                userid = user_info[0]['id']
                for roleid in roleids:
                    sql = "select user_id,role_id from sys_role_map_user where user_id = '%s' and role_id = '%s'" % (userid, roleid)
                    role_user_info = self.ikm_fun.PG.SELECT_DIC(self.ikm_fun.dbc_p, sql)
                    # print(role_user_info)
                    if not role_user_info:
                        sql = "select name from sys_role where id = '%s'" % roleid
                        data_info = self.ikm_fun.PG.SELECT_DIC(self.ikm_fun.dbc_p, sql)
                        role_name = data_info[0]['name']
                        sql = "insert into sys_role_map_user(role_id,user_id) values('%s','%s')" % (roleid, userid)
                        data_info = self.ikm_fun.PG.SQL_EXECUTE(self.ikm_fun.dbc_p, sql)
                        if data_info:
                            print('%s已增加角色->%s' % (staffid, role_name))
                # 清除掉userid其他的roleid
                sql = """delete from sys_role_map_user where user_id = '%s' and role_id not in (%s)""" % (userid, ','.join([str(roleid) for roleid in roleids]))
                data_info = self.ikm_fun.PG.SQL_EXECUTE(self.ikm_fun.dbc_p, sql)
                if data_info:
                    print('%s已清除其他角色%s' % (staffid, len(data_info)))
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
        self.staffid = None
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
            self.staffid = staffid
            # role_idstr = generateUserXml.tableWidget_2.item(generateUserXml.curScr_row, 2).text()
            # self.role_ids = [int(id) for id in re.sub('[\[\]]', '', role_idstr).split(',')]
            topcamword = generateUserXml.tableWidget_2.item(generateUserXml.curScr_row, 3).text()
            incampwd = generateUserXml.tableWidget_2.item(generateUserXml.curScr_row, 4).text()
            incampwd2 = generateUserXml.tableWidget_2.item(generateUserXml.curScr_row, 5).text()
            self.user.setText(staffid)
            self.fullname.setText(name)
            self.topcamword.setText(topcamword)
            self.incampwd.setText(incampwd)
            self.incampwd2.setText(incampwd2)
        self.role_ids = self.get_role_ids()

    def get_role_ids(self):
        role_ids = []
        if self.staffid:
            sql = """select id from sys_user where staffid='%s'""" % self.staffid
            user_info = generateUserXml.ikm_fun.PG.SELECT_DIC(generateUserXml.ikm_fun.dbc_p, sql)
            print(user_info)
            if user_info:
                userid = user_info[0].get('id')
                sql = """select * from sys_role_map_user where user_id='%s'""" % userid
                user_info = generateUserXml.ikm_fun.PG.SELECT_DIC(generateUserXml.ikm_fun.dbc_p, sql)
                print(user_info)
                if user_info:
                    role_ids = [info['role_id'] for info in user_info]
                else:
                    role_ids = [7]  # 默认
            else:
                role_ids = [7]  # 默认
        return role_ids
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
            if not self.role_ids:
                self.role_ids = [7]  # 默认
            new_row = generateUserXml.tableWidget_2.rowCount()
            generateUserXml.tableWidget_2.insertRow(new_row)  # 添加新行
            generateUserXml.tableWidget_2.setItem(new_row, 0, QTableWidgetItem(user))
            generateUserXml.tableWidget_2.setItem(new_row, 1, QTableWidgetItem(fullname))
            generateUserXml.tableWidget_2.setItem(new_row, 2, QTableWidgetItem(str(self.role_ids)))
            generateUserXml.tableWidget_2.setItem(new_row, 3, QTableWidgetItem(topcamword))
            generateUserXml.tableWidget_2.setItem(new_row, 4, QTableWidgetItem(incampwd))
            generateUserXml.tableWidget_2.setItem(new_row, 5, QTableWidgetItem(incampwd2))
            # generateUserXml.update_data.append([user, fullname, self.role_ids, topcamword, incampwd, incampwd2])
        else:
            new_row = generateUserXml.curScr_row
            # generateUserXml.tableWidget_2.insertRow(new_row)  # 添加新行
            generateUserXml.tableWidget_2.setItem(new_row, 0, QTableWidgetItem(user))
            generateUserXml.tableWidget_2.setItem(new_row, 1, QTableWidgetItem(fullname))
            generateUserXml.tableWidget_2.setItem(new_row, 2, QTableWidgetItem(str(self.role_ids)))
            generateUserXml.tableWidget_2.setItem(new_row, 3, QTableWidgetItem(topcamword))
            generateUserXml.tableWidget_2.setItem(new_row, 4, QTableWidgetItem(incampwd))
            generateUserXml.tableWidget_2.setItem(new_row, 5, QTableWidgetItem(incampwd2))
            # generateUserXml.update_data[new_row] = [user, fullname, self.role_ids, topcamword, incampwd, incampwd2]
        self.close()

    def loaduser(self):
        self.staffid = self.user.text()
        self.role_ids = self.get_role_ids()
        sql = """select id, fullname,password from sys_user where staffid='%s'""" % self.staffid
        user_info = generateUserXml.ikm_fun.PG.SELECT_DIC(generateUserXml.ikm_fun.dbc_p, sql)
        if user_info:
            self.fullname.setText(user_info[-1]['fullname'])
            # self.topcamword.setText(user_info[-1]['password'])  # 没有原始密码 只有加密后的，且无法解密回原始密码 所以这里不显示

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            pass
        else:
            super(AddUser, self).keyPressEvent(event)

    def role_edit(self):
        role = Role(self, id=self.role_ids)
        role.edit_role.connect(self.set_role)
        role.exec_()

    def set_role(self, role_ids):
        self.role_ids = role_ids

class Role(QDialog):
    edit_role = pyqtSignal(list)
    def __init__(self, parent=None, id=None):
        super(Role, self).__init__(parent)
        self.role_ids = id
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
        self.role_table.verticalHeader().hide()
        self.role_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.role_table)
        # role_ids = []
        # if self.staffid:
        #     sql = """select id from sys_user where staffid='%s'""" % self.staffid
        #     user_info = generateUserXml.ikm_fun.PG.SELECT_DIC(generateUserXml.ikm_fun.dbc_p, sql)
        #     print(user_info)
        #     if user_info:
        #         userid = user_info[0].get('id')
        #         sql = """select * from sys_role_map_user where user_id='%s'""" % userid
        #         user_info = generateUserXml.ikm_fun.PG.SELECT_DIC(generateUserXml.ikm_fun.dbc_p, sql)
        #         print(user_info)
        #         if user_info:
        #             role_ids = [info['role_id'] for info in user_info]
        #         else:
        #             role_ids = [7]  # 默认
        #     else:
        #         role_ids = [7]  # 默认
        #     # for role in role_info:
        #     #     role_ids.append(role['role_id'])
        # print(role_ids)
        sql = 'SELECT id,name,description FROM sys_role order by id'
        role_info = generateUserXml.ikm_fun.PG.SELECT_DIC(generateUserXml.ikm_fun.dbc_p, sql)
        self.role_table.setRowCount(len(role_info))
        print(role_info)
        select_rows = []
        for row, role in enumerate(role_info):
            self.role_table.setItem(row, 0, QTableWidgetItem(role['name']))
            self.role_table.setItem(row, 1, QTableWidgetItem(role['description']))
            self.role_table.setItem(row, 2, QTableWidgetItem(str(role['id'])))
            if self.role_ids and role['id'] in self.role_ids:
                select_rows.append(row)
        if select_rows:
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
