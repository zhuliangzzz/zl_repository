#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:ScriptsSet_xml.py
   @author:zl
   @time:2023/08/21 09:19
   @software:PyCharm
   @desc:
"""
import os
import socket
import sys

import qtawesome

import ScriptsSetUI as ui

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# sys.path.append('/genesis/sys/scripts/zl/lib')
import genClasses as gen
import ZL_mysqlCon as zlmysql
import res_rc


class ScriptsSet(QMainWindow, ui.Ui_MainWindow):
    dbcls = zlmysql.DBConnect()
    dbconn = dbcls.connection
    cursor = dbcls.cursor

    def __init__(self):
        super(ScriptsSet, self).__init__()
        self.setupUi(self)
        self.render()

    def __getattr__(self, item):
        self.modules = self.getModules()
        return self.modules

    def render(self):
        self.label_logo.setPixmap(QPixmap(":/res/logo.png"))
        # self.label_logo.setScaledContents(True)
        self.menubar.hide()
        # self.statusbar.hide()
        sfont = QFont("Liberation Serif", 11)
        self.jobLabel.setText(f"JOB: {jobname}")
        # self.stepSelect.addItems(job.steps)
        # if stepname:
        #     self.stepSelect.setCurrentText(stepname)
        self.userLabel.setText(f"USER: {user}")
        self.pidLabel.setText(f"PID:  {pid}")
        self.tree.setColumnCount(1)
        # 设置树形控件头部的标题
        self.tree.setHeaderLabels(['Modules'])
        self.tree.headerItem().setTextAlignment(0, Qt.AlignCenter)
        self.tree.headerItem().setBackground(0, QColor(49, 194, 124))
        self.tree.headerItem().setFont(0, QFont("Liberation Serif", 11, QFont.Bold))
        self.tree.itemDoubleClicked.connect(self.run)
        # 设置根节点
        # self.root = QTreeWidgetItem(self.tree)
        total = 0
        for id, module, count in self.modules:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, module + f'({count})')
            item.setSizeHint(0, QSize(100, 26))
            item.setIcon(0, qtawesome.icon('fa.folder-open', scale_factor=1, color='orange'))
            item.setBackground(0, QColor(49, 194, 124))
            item.flag = 'module'
            scripts = self.getScripts(id)
            total += count
            for name, path in scripts:
                script_item = QTreeWidgetItem()
                script_item.setText(0, name)
                script_item.setFont(0, sfont)
                script_item.setSizeHint(0, QSize(100, 22))
                script_item.setIcon(0, qtawesome.icon('fa.file', scale_factor=1, color='orange'))
                script_item.flag = None
                script_item.path = path
                item.addChild(script_item)
        self.statusbar.showMessage(f"Scripts count: {total}")
        self.tree.expandAll()
        self.pushButton.setIcon(qtawesome.icon('fa.pause-circle', scale_factor=1, color='cyan'))
        self.pushButton_2.setIcon(qtawesome.icon('fa.arrow-circle-o-right', scale_factor=1, color='cyan'))
        self.pushButton.clicked.connect(self.pause)
        self.pushButton_2.clicked.connect(lambda: sys.exit(0))
        # self.move((app.desktop().width() - self.geometry().width()) / 2,
        #           (app.desktop().height() - self.geometry().height()) / 2)
        self.setStyleSheet(
            'QPushButton{font:11pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

    def getModules(self):
        # sql = 'select id,module_name from fpc_script_module'
        sql = 'select a.id,module_name,count(1) from fpc_script_module a left join fpc_script_file b on a.id = b.module_id where module_id is not null GROUP BY module_id'
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        return results

    def getScripts(self, id):
        sql = "select script_name,script_path from fpc_script_file where module_id = %s order by CONVERT(script_name USING GBK);"
        self.cursor.execute(sql, id)
        results = self.cursor.fetchall()
        return results

    def pause(self):
        self.hide()
        job.PAUSE("script pause and please click 'Continue Script' to be continue")
        self.show()

    def run(self, item):
        if item.flag == 'module':
            return
        script_name = item.text(0)
        script_path = item.path
        self.close()
        self.save_record(script_name, script_path)
        status = job.COM(
            f'script_run,name={script_path},dirmode=global,params=,env1=JOB={jobname},env2=STEP={stepname}')
        if status:
            sys.exit()
        sys.exit()
        # app.processEvents()
        # self.show()

    @classmethod
    def save_record(cls, name, path):
        host = socket.gethostbyname(socket.gethostname())
        sql = 'insert into fpc_script_record(script_name, script_path, host, user, jobname) values(%s, %s, %s, %s, %s)'
        try:
            cls.cursor.execute(sql, (name, path, host, user, jobname))
            cls.dbconn.commit()
        except Exception as e:
            print(e)
            cls.dbconn.rollback()
        finally:
            cls.dbcls.close_con()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setWindowIcon(QIcon(':/res/demo.png'))
    # app.setStyleSheet('*{font:12pt;font-family:"Liberation Serif";}')
    app.setStyleSheet('*{font:11pt;font-family:"微软雅黑";}')
    if not os.environ.get('JOB'):
        QMessageBox.warning(None, 'tips', "请打开料号执行！")
        sys.exit()
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    user = job.getUser()
    pid = job.pid
    stepname = None
    if os.environ.get('STEP'):
        stepname = os.environ.get('STEP')
    scripts_set = ScriptsSet()
    scripts_set.show()
    sys.exit(app.exec_())
