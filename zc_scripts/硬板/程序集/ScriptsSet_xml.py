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
import sys

import qtawesome
from lxml import etree

import ScriptsSetUI as ui

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# sys.path.append('/genesis/sys/scripts/zl/lib')
import genClasses as gen
import res_rc


class ScriptsSet(QMainWindow, ui.Ui_MainWindow):
    def __init__(self):
        super(ScriptsSet, self).__init__()
        self.config_file = '//172.16.0.106/scripts/HDI/cam_config_hdi.xml'
        self.setupUi(self)
        self.render()

    def __getattr__(self, item):
        if item == 'script_map':
            self.script_map = self.get_script_hashmap()
            return self.script_map

    def get_script_hashmap(self):
        id_module, hashmap = {}, {}
        with open(self.config_file, encoding='utf-8') as r:
            content = r.read()
        xml_parser = etree.XMLParser()
        fromstring = etree.fromstring(content, parser=xml_parser)
        for record in fromstring.findall('RECORD'):
            id = int(record.find('module_id').text)
            module = record.find('module_name').text
            name = record.find('script_name').text
            path = record.find('script_path').text
            id_module[id] = module
            if not hashmap.get(module):
                hashmap[module] = []
            hashmap[module].append((name, path))
        return {'id_module': id_module, 'module': hashmap}

    def render(self):
        self.label_logo.setPixmap(QPixmap(":/res/logo.png"))
        # self.label_logo.setScaledContents(True)
        self.menubar.hide()
        self.setWindowTitle('HDI脚本')
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
        self.tree.headerItem().setBackground(0, QColor('#32A7C8'))
        self.tree.headerItem().setFont(0, QFont("Liberation Serif", 11, QFont.Bold))
        self.tree.itemDoubleClicked.connect(self.run)
        self.tree.setStyleSheet(':selected{background-color: rgb(49,194,124);}')
        # 设置根节点
        # self.root = QTreeWidgetItem(self.tree)
        total = 0
        # 20240727 对module排序
        module_ids = sorted(self.script_map['id_module'])
        for id in module_ids:
            module = self.script_map['id_module'].get(id)
            count = len(self.script_map['module'].get(module))
            # item = QTreeWidgetItem(self.tree)
            item = QTreeWidgetItem()
            self.tree.addTopLevelItem(item)
            item.setText(0, module + f'({count})')
            item.setSizeHint(0, QSize(100, 26))
            item.setIcon(0, qtawesome.icon('fa.folder-open', scale_factor=1, color='orange'))
            item.setBackground(0, QColor('#32A7C8'))
            item.flag = 'module'
            total += count
            for name, path in self.script_map['module'].get(module):
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
        self.setStyleSheet('QPushButton{font:11pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;} #QTreeWidget::item:selected{background-color:rgb(49,194,124);color:black;}')
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

    def pause(self):
        self.hide()
        job.PAUSE("script pause and please click 'Continue Script' to be continue")
        self.show()

    def run(self, item):
        if item.flag == 'module':
            return
        script_path = item.path
        self.close()
        status = job.COM(f'script_run,name={script_path},dirmode=global,params=,env1=JOB={jobname},env2=STEP={stepname}')
        if status:
            sys.exit()
        sys.exit()
        # app.processEvents()
        # self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setWindowIcon(QIcon(':/res/demo.png'))
    # app.setStyleSheet('*{font:12pt;font-family:"Liberation Serif";}')
    app.setStyleSheet('*{font:12pt;font-family:"微软雅黑";}')
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
