#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:OuterCheckViewForReviewer.py
   @author:zl
   @time: 2024/11/19 17:10
   @software:PyCharm
   @desc:
"""
import os
import sys
import platform

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

from TOPCAM_IKM import IKM

import genClasses_zl as gen

from PyQt4 import QtCore, QtGui
import OuterCheckViewForReviewerUI_pyqt4 as ui
import pic

class OuterCheckViewForReviewer(QtGui.QWidget, ui.Ui_Form):
    def __init__(self):
        super(OuterCheckViewForReviewer, self).__init__()
        self.user = job.user
        try:
            self.ikm_fun = IKM()
        except Exception as e:
            QtGui.QMessageBox.warning(self, u"连接topcam数据库异常，请联系程序组处理:", str(e))
            sys.exit()
        self.setupUi(self)
        self.render()

    def render(self):
        users = self.getUsers()
        if users:
            self.comboBox.addItems(users)
        header = [u'序号', u'检测项目', u'用户', u'检测时间', u'检测结果', u'警报信息']
        self.tableWidget.setColumnCount(len(header))
        self.tableWidget.setHorizontalHeaderLabels(header)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tableWidget.setColumnWidth(0, 40)
        self.tableWidget.setColumnWidth(2, 70)
        self.tableWidget.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setResizeMode(5, QtGui.QHeaderView.Stretch)
        self.radioButton.clicked.connect(self.loadTable)
        self.radioButton_2.clicked.connect(self.loadTable)
        self.comboBox.currentIndexChanged.connect(self.loadTable)
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)
        self.loadTable()
        self.setMainUIstyle()

    def getUsers(self):
        sql = "select distinct check_user from pdm_job_check_log_list where jobname='%s'" % jobname
        data = self.ikm_fun.PG.SELECT_DIC(self.ikm_fun.dbc_p, sql)
        return [d.get('check_user') for d in data]

    def loadTable(self):
        check_inn_or_out = 'inner' if self.radioButton.isChecked() else 'outer'
        self.tableWidget.clearContents()
        sql = "select function_description,check_user,check_time, check_process, check_log from pdm_job_check_log_list where check_user = '%s' and jobname = '%s' and check_inn_or_out = '%s'" % (
        self.comboBox.currentText(), jobname, check_inn_or_out)
        datas = self.ikm_fun.PG.SELECT_DIC(self.ikm_fun.dbc_p, sql)
        row = 0
        self.tableWidget.setRowCount(len(datas))
        for data in datas:
            self.tableWidget.setItem(row, 0, QtGui.QTableWidgetItem(str(row + 1)))
            self.tableWidget.setItem(row, 1, QtGui.QTableWidgetItem(
                str(data.get('function_description')).decode('utf-8') if data.get('function_description') else ''))
            self.tableWidget.setItem(row, 2, QtGui.QTableWidgetItem(
                str(data.get('check_user')).decode('utf-8') if data.get('check_user') else ''))
            self.tableWidget.setItem(row, 3, QtGui.QTableWidgetItem(
                str(data.get('check_time')).decode('utf-8') if data.get('check_time') else ''))
            self.tableWidget.setItem(row, 4, QtGui.QTableWidgetItem(
                str(data.get('check_process')).decode('utf-8') if data.get('check_process') else ''))
            self.tableWidget.setItem(row, 5, QtGui.QTableWidgetItem(
                str(data.get('check_log')).decode('utf-8') if data.get('check_log') else ''))
            row += 1

    def setMainUIstyle(self):  # 设置风格
        file = QtCore.QFile(':/pic/fblue.qss')
        file.open(QtCore.QFile.ReadOnly)
        styleSheet = file.readAll()
        styleSheet = unicode(styleSheet, encoding='gb2312')
        # old_string = """QTableWidget::item {"""
        # new_string = """QTableWidget#my_no_color::item {"""
        # styleSheet = styleSheet.replace(old_string, new_string)
        QtGui.qApp.setStyleSheet(styleSheet)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    reviewer = OuterCheckViewForReviewer()
    reviewer.show()
    sys.exit(app.exec_())
