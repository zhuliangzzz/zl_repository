#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__    = "20230107"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""检查项目界面 """
import sip
sip.setapi('QVariant', 2)

import os
import sys
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
    
import json
try:            
    paramJson = json.loads(os.environ.get('PARAM').replace(';', ','))
    processID = int(paramJson['process_id'])
    jobID = int(paramJson['job_id'])
    user = paramJson['user']
    jobname = os.environ["JOB"]
except:
    # 手动测试用
    processID = -1
    jobID = -1
    user = "84310"
    jobname = os.environ.get("JOB", "sd1010gh082a1-lyh")
    if os.environ.get("JOB", None) is None:
        os.environ["JOB"] = jobname
    
import pic
import re
import time
from sh_hdi_auto_check_list import set_check_function_name_from_erp, \
     get_check_function_list, update_current_job_check_log, \
     delete_current_job_check_item, get_user_data_info, \
     get_process_is_running

from create_ui_model import app, showMessageInfo, \
     showQuestionMessageInfo
    
from PyQt4 import QtCore, QtGui, Qt
from mainTableDelegate_check_log import itemDelegate    
from sh_hdi_check_data_ui import update_check_data_ui
from QstandardItemModel_hdi_check import ModelDelegate

try:
    persona, inn_or_out = sys.argv[1:]
except:
    persona = "for_cam_maker"
    inn_or_out = "inner"


class workThread(QtCore.QThread):
    def __init__(self, parent=None):
        super(workThread, self).__init__(parent)
        
    def set_params(self, *args, **kwargs):
        self.PID = kwargs["pid"]
        self.script_path = kwargs["script_path"]
        self.function = kwargs["function"]
        self.jobname = kwargs["jobname"]
        self.stepname = kwargs["stepname"]
        self.check_row = kwargs["check_row"]
        self.check_id = kwargs["check_id"]
        self.check_inner_or_outer = kwargs["check_inner_or_outer"]
        
    def run(self):
        PID, script_path, function, jobname, stepname = \
            self.PID, self.script_path, self.function, self.jobname, self.stepname
        
        if not PID:
            return
        try:            
            if sys.platform == "win32":
                hostname = os.environ["COMPUTERNAME"]
                cmd = ("%s/misc/gateway %%%s@%s.%s 'COM script_run,name=%s,"
                "env1=JOB=%s,env2=STEP=%s,env3=CHECK_ID=%s,env4=INNER_OUTER=%s,params=%s'" % (
                    os.environ["GENESIS_EDIR"], PID, hostname, hostname, script_path, jobname, stepname,
                    self.check_id, self.check_inner_or_outer, function))    
                csh_script_path = "c:/tmp/run_script_{0}.csh".format(jobname)
                log_path = "c:/tmp/check_log_{0}_{1}.log".format(jobname, function)
                pause_log_path = "c:/tmp/check_log_{0}_{1}_pause.log".format(jobname, function)
            else:
                hostname = os.environ["HOST"]
                cmd = ("%s/gateway %%%s@%s.%s 'COM script_run,name=%s,"
                "env1=JOB=%s,env2=STEP=%s,env3=CHECK_ID=%s,env4=INNER_OUTER=%s,params=%s'" % (
                    "/incampro/release/bin", PID, hostname, hostname, script_path, jobname, stepname,
                    self.check_id, self.check_inner_or_outer, function))    
                csh_script_path = "/tmp/run_script_{0}.csh".format(jobname)
                log_path = "/tmp/check_log_{0}_{1}.log".format(jobname, function)
                pause_log_path = "/tmp/check_log_{0}_{1}_pause.log".format(jobname, function)
                
            if os.path.exists(csh_script_path):
                os.unlink(csh_script_path)
            if os.path.exists(log_path):
                os.unlink(log_path)
            if os.path.exists(pause_log_path):
                os.unlink(pause_log_path)                
                
            with open(csh_script_path, "a") as f:
                f.write("#!c:/bin/csh -f\n")
                f.write(cmd + "\n")
                f.write("exit\n")
    
            os.system("csh %s" % csh_script_path)
            try:
                os.unlink(csh_script_path)
            except:
                pass
            
            if os.path.exists(pause_log_path):
                # pause 暂停此处等待 pause后此文件会被删除 即可正常运行后续程序
                while os.path.exists(pause_log_path):
                    time.sleep(1)
            
            if os.path.exists(log_path):
                lines = file(log_path).readlines()
                try:
                    lines = [line.decode("cp936") for line in lines]
                except:
                    pass
                self.emit(QtCore.SIGNAL('output(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.check_row,self.check_id, lines)
                os.unlink(log_path)
            else:            
                self.emit(QtCore.SIGNAL('output(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.check_row,self.check_id, u"运行异常中断，请尝试手动运行试试！")
        except Exception, e:
            self.emit(QtCore.SIGNAL('output(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.check_row,self.check_id,str(e))

class show_check_ui(QtGui.QWidget):
    def __init__(self,parent = None):
        super(show_check_ui,self).__init__(parent)
        self.setWindowFlags(Qt.Qt.Window|Qt.Qt.WindowStaysOnTopHint)

        self.setGeometry(700, 200, 1000, 600)
        self.setObjectName("mainWindow")
        
        self.menuBar = QtGui.QMenuBar()
        self.groupBox1 = QtGui.QGroupBox()
        self.tableWidget = QtGui.QTableView()
        self.start_btn = QtGui.QPushButton(u"运行全部")
        self.partial_btn = QtGui.QPushButton(u"运行未检测项目")
        self.clear_log_btn = QtGui.QPushButton(u"清除选中行检测结果")
        self.clear_test_btn = QtGui.QPushButton(u"清除测试记录")
        self.end_btn = QtGui.QPushButton(u"退出")
        
        self.test_check_btn = QtGui.QCheckBox(u"测试项目")
        self.test_check_btn.setStyleSheet( """color: red;""")
                
        self.menuBar.setFixedWidth(80)
        
        group_layout1 = QtGui.QGridLayout()
        group_layout1.addWidget(self.test_check_btn, 0, 0, 1, 1)
        group_layout1.addWidget(self.tableWidget, 1, 0, 1, 8)
        group_layout1.addWidget(self.start_btn, 2, 0, 1, 1)
        group_layout1.addWidget(self.partial_btn, 2, 1, 1, 1)
        group_layout1.addWidget(self.clear_log_btn, 2, 3, 1, 2)
        group_layout1.addWidget(self.clear_test_btn, 2, 5, 1, 1)
        group_layout1.addWidget(self.end_btn, 2, 7, 1, 1)
        group_layout1.setSpacing(5)
        group_layout1.setContentsMargins(5, 5, 5, 5)
        self.groupBox1.setLayout(group_layout1)

        main_layout =  QtGui.QVBoxLayout()
        # main_layout.addLayout(self.horizontalLayout)
        main_layout.addWidget(self.menuBar)
        main_layout.addWidget(self.groupBox1)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self.setMainUIstyle()        

        self.tableWidget.setMouseTracking(True)
        self.tableWidget.entered.connect(self.showToolTip)
        self.start_btn.clicked.connect(self.start_run_all_check)
        self.partial_btn.clicked.connect(self.start_run_all_check)
        self.clear_log_btn.clicked.connect(self.clear_select_row_run_log)
        self.clear_test_btn.clicked.connect(self.clear_test_check_item)
        self.test_check_btn.clicked.connect(self.get_check_data)
        self.end_btn.clicked.connect(app.quit)
        
        #检测是否已运行过此项目 20230605 by lyh        
        is_running = get_process_is_running()        

        self.setTableWidget()
        self.createActions()
        self.createMenus()
        
        self.clear_test_btn.hide()
        self.test_check_btn.setEnabled(False)
        for dic_info in get_user_data_info():
            if user == str(dic_info["person_number"]) and \
               dic_info["person_role"].decode("utf8") in (u"管理员", u"测试员"):
                self.test_check_btn.setEnabled(True)            
                set_check_function_name_from_erp("('normal','test')")
            else:
                set_check_function_name_from_erp("('normal')")
            
        self.check_data_action.setEnabled(False)
        self.add_user_action.setEnabled(False)
        self.modify_current_job_data_action.setEnabled(False)
        self.view_current_job_data_action.setEnabled(False)    
        for dic_info in get_user_data_info():
            if user == str(dic_info["person_number"]) and \
               dic_info["person_role"].decode("utf8") in (u"管理员"):
                self.check_data_action.setEnabled(True)
                self.add_user_action.setEnabled(True)
                self.modify_current_job_data_action.setEnabled(True)
                self.view_current_job_data_action.setEnabled(True)  
                
        for dic_info in get_user_data_info():
            if user == str(dic_info["person_number"]) and \
               dic_info["person_role"].decode("utf8") in (u"测试员"):
                self.modify_current_job_data_action.setEnabled(True)
                
        for dic_info in get_user_data_info():
            if user == str(dic_info["person_number"]) and \
               dic_info["person_role"].decode("utf8") in (u"测试员", u"审核人"):
                self.view_current_job_data_action.setEnabled(True)    
        
        
        self.get_check_data()        
        
        self.info_label = QtGui.QLabel()
        self.info_label.setGeometry(750, 5, 500, 40)
        self.info_label.setWindowTitle(u"进度信息")
        self.info_label.setText(u"提示信息")
        self.info_label.setWindowFlags(Qt.Qt.Dialog|Qt.Qt.FramelessWindowHint|Qt.Qt.WindowStaysOnTopHint|Qt.Qt.Tool)
        self.info_label.setObjectName("mainWindow")
        self.info_label.setStyleSheet("color:red;")
        
        self.setWindowTitle(u"{0} HDI自动检测项目({2}) {1}".format(jobname, __version__, u"内层" if inn_or_out=="inner" else u"外层"))
        self.installEventFilter(self)
        
        #检测是否已运行过此项目 20230605 by lyh        
        if is_running:
            self.show()
        else:
            for dic_info in get_user_data_info():
                if user == str(dic_info["person_number"]) and \
                   dic_info["person_role"].decode("utf8") in (u"管理员", u"测试员"):
                    self.show()
                    break
            else:
                self.start_run_all_check(auto_run="yes")
        
    def closeEvent(self, e):
        app.quit()
        
    def createMenus(self):
        self.fileMenu = self.menuBar.addMenu(u"系统配置")
        self.fileMenu.addAction(self.check_data_action)
        self.fileMenu.addAction(self.add_user_action)
        self.fileMenu.addAction(self.modify_current_job_data_action)
        self.fileMenu.addAction(self.view_current_job_data_action)
        
    def createActions(self):
        self.check_data_action = QtGui.QAction(u"&更新系统检测项目", self, shortcut="Ctrl+Q", triggered=lambda:self.update_check_data("system"))
        self.add_user_action = QtGui.QAction(u"&添加用户信息", self, shortcut="Ctrl+Q", triggered=lambda:self.update_check_data("add_user"))        
        self.modify_current_job_data_action = QtGui.QAction(u"&修改当前型号检测项目", self, shortcut="Ctrl+A", triggered=lambda:self.update_check_data("job"))
        self.view_current_job_data_action = QtGui.QAction(u"&查看当前型号检测结果", self, shortcut="Ctrl+V", triggered=lambda:self.update_check_data("view_job"))
        
    def update_check_data(self, args):
        ui = update_check_data_ui(check_type=args)
        ui.exec_()

    def setTableWidget(self):
        table = self.tableWidget  
        self.columnHeader = [u"序号", u"检测项目",u"手动运行",u"查看标记", 
                        u"检测结果", u"警报信息",  u"坐标信息",
                        u"项目程序路径", u"项目函数", u"项目id"]
        # self.tableModel = QtGui.QStandardItemModel(table)
        self.tableModel = ModelDelegate(table)
        self.tableModel.setColumnCount(len(self.columnHeader))
        for j in range(len(self.columnHeader)):
            self.tableModel.setHeaderData(
                j, Qt.Qt.Horizontal, self.columnHeader[j])
        table.setModel(self.tableModel)
        #table.setEditTriggers(QtGui.QTableWidget.NoEditTriggers)
        #table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        table.verticalHeader().setVisible(False)
        header = table.horizontalHeader()
        # header.setStretchLastSection(True)
        header.setDefaultAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        header.setTextElideMode(QtCore.Qt.ElideRight)
        header.setClickable(True)
        header.setMouseTracking(True)
        table.setColumnWidth(0, 40)
        table.setColumnWidth(1, 400)
        table.setColumnWidth(2, 60)
        table.setColumnWidth(3, 60)
        table.setColumnWidth(4, 70)
        table.hideColumn(6)
        table.hideColumn(7)
        table.hideColumn(8)
        table.hideColumn(9)
        
        self.tableItemDelegate = itemDelegate(self)
        self.connect(self.tableItemDelegate, QtCore.SIGNAL(
            "view_note(PyQt_PyObject,PyQt_PyObject)"), self.view_note_detail)
        self.connect(self.tableItemDelegate, QtCore.SIGNAL(
            "manual_run(PyQt_PyObject,PyQt_PyObject)"), self.manual_run_script)        
        
        self.tableWidget.setItemDelegateForColumn(2, self.tableItemDelegate)
        self.tableWidget.setItemDelegateForColumn(3, self.tableItemDelegate)        
        
    def resizeEvent(self, event):
        super(show_check_ui, self).resizeEvent(event)
        tableSize = self.tableWidget.width()        
        sideHeaderWidth = self.tableWidget.verticalHeader().width()
        tableSize -= sideHeaderWidth
        if tableSize == 640:
            self.tableWidget.setColumnWidth(5, self.width()-630-15)
        else:            
            self.tableWidget.setColumnWidth(5, tableSize-630-5)
        
    def manual_run_script(self, index, button):
        """手动运行程序"""
        self.start_btn.setEnabled(False)
        self.partial_btn.setEnabled(False)
        self.clear_log_btn.setEnabled(False)
        self.clear_test_btn.setEnabled(False)
        self.manual_run_script_button = button
        self.manual_run_script_button.setEnabled(False)
        self.tableItemDelegate.set_editor_status_two(self.model.rowCount(), False)
        self.manual_run_script_status = True
        
        self.my_thread = workThread()           
        self.connect(self.my_thread, QtCore.SIGNAL(
            "output(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self.update_check_log)
        
        check_id = self.model.item(index.row(), 9).text()
        update_current_job_check_log(check_id, u"check_process='',check_log='',note_coordinate=''")
        self.get_check_data()
        
        self.run_script_in_thread(index.row())
        
    def view_note_detail(self, index, button):
        """查看打印标记"""
        self.setWindowState(Qt.Qt.WindowMinimized)
        
        self.get_check_data()
        
        row = index.row()
        info = self.model.item(row, 6)
        
        if info is not None:            
            path = str(self.model.item(row, 7).text())           
            check_id = self.model.item(row, 9).text()
            check_inner_or_outer = "all"
            self.my_thread = workThread()
            self.connect(self.my_thread, QtCore.SIGNAL(
                "output(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self.update_check_log_view)            
            self.my_thread.set_params(pid=os.environ.get("CURRENTPIDNUM", ""),
                                   function="view_note_detail",
                                   script_path=path,
                                   jobname=os.environ.get("JOB"),
                                   stepname=os.environ.get("STEP"),
                                   check_row=row,
                                   check_id=check_id,
                                   check_inner_or_outer=check_inner_or_outer)
            self.my_thread.start()            
        else:
            showMessageInfo(u"未发现此检查项目的标记！")
            
    def update_check_log_view(self):
        pass
        # showMessageInfo(u"查看完成！")
        
    def start_run_all_check(self, auto_run=None):
        """开始所有的检测"""
        self.start_btn.setEnabled(False)
        self.partial_btn.setEnabled(False)
        self.clear_log_btn.setEnabled(False)
        self.clear_test_btn.setEnabled(False)
        self.tableItemDelegate.set_editor_status_two(self.model.rowCount(), False)
        
        if auto_run == "yes" or \
           self.sender().text() == QtCore.QString(u"运行全部"):
            for row in range(self.model.rowCount()):
                check_id = self.model.item(row, 9).text()
                update_current_job_check_log(check_id, u"check_process='',check_log='',note_coordinate=''")
            self.get_check_data()
        
        self.my_thread = workThread()
        self.connect(self.my_thread, QtCore.SIGNAL(
            "output(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self.update_check_log)        
        
        self.run_script_in_thread()        
    
    def run_script_in_thread(self, manual_run_row=None):
        
        for row in range(self.model.rowCount()):
            if manual_run_row is not None and row != manual_run_row:
                continue
            
            path = str(self.model.item(row, 7).text())           
            function_name = str(self.model.item(row, 8).text())
            check_result = self.model.item(row, 4)
            check_id = self.model.item(row, 9).text()
            check_inner_or_outer = "all"
            if "(inner)" in self.model.item(row, 1).text():
                check_inner_or_outer ="inner"
            if "(outer)" in self.model.item(row, 1).text():
                check_inner_or_outer ="outer"                
            
            if check_result is None or check_result.text() == "" or manual_run_row == row:
                if not self.my_thread.isRunning():                
                    self.my_thread.set_params(pid=os.environ.get("CURRENTPIDNUM", ""),
                                           function=function_name,
                                           script_path=path,
                                           jobname=os.environ.get("JOB"),
                                           stepname=os.environ.get("STEP"),
                                           check_row=row,
                                           check_id=check_id,
                                           check_inner_or_outer = check_inner_or_outer)
                    #显示进度 及最小化主窗口
                    self.info_label.show()
                    self.setWindowState(Qt.Qt.WindowMinimized)                    
                    self.info_label.setText(u"进度{0}/{1}  项目:{2}  \n{3}检测中...".format(row+1, self.model.rowCount(),
                                                                                            self.model.item(row, 1).text(), " "*20))
                    
                    update_current_job_check_log(check_id, u"check_process='{0}'".format(u"检测中..."))
                    self.get_check_data()
                    self.my_thread.start()                    
                    break
        else:
            self.start_btn.setEnabled(True)
            self.partial_btn.setEnabled(True)
            self.clear_log_btn.setEnabled(True)
            self.clear_test_btn.setEnabled(True)
            self.tableItemDelegate.set_editor_status_two(self.model.rowCount(), True)
            if getattr(self, "manual_run_script_button", None):
                self.manual_run_script_button.setEnabled(True)
                self.manual_run_script_status = False
                
            self.get_check_data()
            
            self.info_label.hide()
            self.show()
            self.showNormal()
                
    def update_check_log(self, row,check_id, args):
        """更新运行结果"""
        #QtGui.QMessageBox.information(
            #self, u'警告', "".join(args), 1)
        
        try:
            if "success" in "".join(args):                
                status = u"检测完成"
            elif u"人工检查完毕" in "".join(args):
                status = u"人工检查"
            else:
                status = u"检测异常"            
            index = self.model.index(row,4, QtCore.QModelIndex())                
            self.model.setData(index, status)
            
            index = self.model.index(row,5, QtCore.QModelIndex())
            self.model.setData(index, "".join(args))          
            
            update_current_job_check_log(check_id, u"check_process='{0}',check_log='{1}'".format(status, "".join(args)))
            
            self.my_thread.quit()
            i = 0
            while self.my_thread.isRunning():
                QtGui.QMessageBox.information(
                    self, u'警告', str(self.my_thread.isRunning()), 1)
                i += 1
                self.my_thread.quit()
                if i > 5:
                    break
            
            if getattr(self, "manual_run_script_status", False):
                # 手动运行 要终止线程
                self.run_script_in_thread(100000)
            else:
                self.run_script_in_thread()
            
        except Exception, e:
            QtGui.QMessageBox.information(
                self, u'警告', str(e), 1)
            
    def clear_select_row_run_log(self):
        arraylist = set([index.row() for index in self.tableWidget.selectedIndexes()])
        res = showQuestionMessageInfo(u"确定要清除选择行 {0} 的运行结果！".format([row + 1 for row in arraylist]))
        if res:
            for row in arraylist:                
                check_id = self.model.item(row, 9).text()
                update_current_job_check_log(check_id, u"check_process='',check_log='',note_coordinate=''")
            
            self.get_check_data()
            
    def clear_test_check_item(self):
        """清除测试项目记录"""
        res = showQuestionMessageInfo(u"确定要清除该型号的所有测试项目记录！")
        if res:
            for row in range(self.model.rowCount()):
                check_id = self.model.item(row, 9).text()
                delete_current_job_check_item(check_id)
                
            self.get_check_data()
        
    def get_check_data(self):
        if self.test_check_btn.isChecked():
            self.clear_test_btn.show()
            data_info = get_check_function_list(user, jobname,
                                                "check_status = 'test' and check_inn_or_out in ('all','{0}') and {1} = '是'".format(inn_or_out, persona))
        else:
            self.clear_test_btn.hide()
            data_info = get_check_function_list(user, jobname,
                                                "check_status = 'normal' and check_inn_or_out in ('all','{0}') and {1} = '是'".format(inn_or_out, persona))
        
        if inn_or_out == "outer":
            data_info = [dic_info for dic_info in data_info
                         if "(inner)" not in dic_info["function_description"]]
            
        if inn_or_out == "inner":
            data_info = [dic_info for dic_info in data_info
                         if "(outer)" not in dic_info["function_description"]]
            
        self.set_model_data(data_info)

    def set_model_data(self, data_info):
        """设置表内数据"""
        self.model = self.tableModel# self.tableWidget.model()            
        self.model.setRowCount(len(data_info))
        for i, dic_info in enumerate(sorted(data_info, key=lambda x: x["id"])):
            if dic_info: 
                index = self.model.index(i,0, QtCore.QModelIndex())
                self.model.setData(index, i + 1)

                index1 = self.model.index(i, 1, QtCore.QModelIndex())
                self.model.setData(index1, dic_info["function_description"].decode("utf8"))
                
                index = self.model.index(i,4, QtCore.QModelIndex())
                self.model.setData(index, "" if dic_info["check_process"] is None else dic_info["check_process"].decode("utf8"))
                #if dic_info["note"] is not None and dic_info["note"].decode("utf8") == u"人工检查":
                    #self.model.setData(index,u"人工检查")
                
                index = self.model.index(i,5, QtCore.QModelIndex())
                self.model.setData(index, "" if dic_info["check_log"] is None else dic_info["check_log"].decode("utf8"))
                #if dic_info["note"] is not None and dic_info["note"].decode("utf8") == u"人工检查":
                    #self.model.setData(index,u"请点击手动运行，按提示步骤进行检查")
                    #if dic_info["check_log"] is not None and "success" in dic_info["check_log"]:
                        #self.model.setData(index,u"已检查完毕")
                    
                index = self.model.index(i,6, QtCore.QModelIndex())
                self.model.setData(index, "" if dic_info["note_coordinate"] is None else dic_info["note_coordinate"].decode("utf8"))
                
                index1 = self.model.index(i, 7, QtCore.QModelIndex())
                self.model.setData(index1, dic_info["script_path"].decode("utf8"))
                
                index1 = self.model.index(i, 8, QtCore.QModelIndex())
                self.model.setData(index1, dic_info["check_function_name"].decode("utf8"))
                
                index1 = self.model.index(i, 9, QtCore.QModelIndex())
                self.model.setData(index1, dic_info["id"])
        
        self.tableWidget.setModel(self.model)
       
        for row in range(len(data_info)):
            index = self.model.index(row,2, QtCore.QModelIndex())
            self.tableWidget.openPersistentEditor(index)

            index = self.model.index(row, 3, QtCore.QModelIndex())
            self.tableWidget.openPersistentEditor(index)
            
            self.tableItemDelegate.set_editor_status(index)            

    def eventFilter(self,  source,  event):
        if event.type() == QtCore.QEvent.HoverMove:#表头气泡提示                        
            pos = event.pos()
            section = self.tableWidget.horizontalHeader().logicalIndexAt(pos)
            if section < 0:
                return QtGui.QMainWindow.eventFilter(self,  source,  event)
            model = self.tableWidget.model()
            QtGui.QToolTip.showText(QtGui.QCursor.pos(),
                                    model.headerData(section,QtCore.Qt.Horizontal,QtCore.Qt.DisplayRole))
            
        if event.type() == QtCore.QEvent.WindowActivate:
            print "active"
            #pause_log_path = "/tmp/check_log_{0}_{1}_pause.log".format(jobname, function)
            for name in os.listdir("/tmp"):
                if re.match("check_log_{0}_.*_pause.log".format(jobname), name):
                    path = os.path.join("/tmp", name)
                    if os.path.exists(path):
                        os.unlink(path)
        
        return QtGui.QMainWindow.eventFilter(self,  source,  event)

    def GetItemValue(self,IndexText,row = ""):#获取表格内容
        if row != "":
            row = row
        else:
            row = self.tableWidget.currentIndex().row()
        for i in range(self.tableWidget.model().columnCount()):
            HeaderText = unicode(self.tableWidget.model().horizontalHeaderItem(
                i).text().toUtf8(), 'utf8', 'ignore').encode('gb2312')
            if IndexText.encode("gb2312") == HeaderText:
                item = self.tableWidget.model().item(row,i)
                if item == None:return ""
                TextValue = unicode(item.text().toUtf8(),'utf8', 'ignore').encode('gb2312').decode("cp936")
                return TextValue.strip()
        return ""
    
    def SetItemValue(self,IndexText,TextValue,row = 0,model = ""):#设置表格内容
        if row != 0:
            row = row
        else:
            row = 0
        if model:
            ItemModel = model
        else:
            ItemModel = self.tableModel
        for i in range(ItemModel.columnCount()):
            HeaderText = unicode(ItemModel.horizontalHeaderItem(i).text().toUtf8(),'utf8', 'ignore').encode('gb2312')
            if IndexText.encode("gb2312") == HeaderText:
                index = ItemModel.index(row, i, QtCore.QModelIndex())
                ItemModel.setData(index, TextValue)
                
    def setTableColumnWidth(self,Text,width):#设置列宽
        for i in range(self.tableWidget.model().columnCount()):
            HeaderText = unicode(self.tableWidget.model().horizontalHeaderItem(i).text().toUtf8(),'utf8', 'ignore').encode('gb2312')
            if Text.encode("gb2312") == HeaderText:
                self.tableWidget.setColumnWidth(i,width)
                
    def showToolTip(self, index):  # 设置气泡提示
        if index.data() is None: return
        data = index.model().item(index.row(), index.column())
        if data is None:
            return
        
        QtGui.QToolTip.showText(QtGui.QCursor.pos(), data.text())
        
    def setMainUIstyle(self):#设置风格
        file = QtCore.QFile(':/pic/fblue.qss')
        file.open(QtCore.QFile.ReadOnly)
        styleSheet = file.readAll()
        styleSheet = unicode(styleSheet, encoding='gb2312')
        old_string = """QTableView::item {"""
        new_string = """QTableView#my_no_color::item {"""
        styleSheet = styleSheet.replace(old_string, new_string)        
        QtGui.qApp.setStyleSheet(styleSheet)

if __name__ == "__main__":	
    main_widget = show_check_ui()
    # main_widget.show()    
    sys.exit(app.exec_())
    

