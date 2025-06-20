#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__    = "20230107"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""更新检测项目 """

import os
import sys
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")
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
    user = "system"
    jobname = os.environ.get("JOB", "c89804pi375a1-lyh")
    if os.environ.get("JOB", None) is None:
        os.environ["JOB"] = jobname
        
import pic
import time
from sh_hdi_auto_check_list import get_check_data_info, \
     uploading_data, get_current_job_check_data_info, \
     update_current_job_check_log, get_user_data_info
from create_ui_model import app, showQuestionMessageInfo, \
     showMessageInfo
from PyQt4 import QtCore, QtGui, Qt

user_info_list = get_user_data_info()

dic_zu = {u"序号": "id",
          u"程序函数名称": "check_function_name",
          u"检测项目描述": "function_description",
          u"检测状态": "check_status",
          u"CAM制作运行": "for_cam_maker",
          u"CAM审核运行": "for_cam_director",
          u"检测内外层": "check_inn_or_out",
          u"程序完整路径": "script_path",
          u"备注": "note",
          u"用户工号": "person_number",
          u"用户姓名": "person_name",
          u"用户职能": "person_role",
          u"提示或拦截": "forbid_or_information",}

class update_check_data_ui(QtGui.QDialog):
    def __init__(self,parent = None, check_type=None):
        super(update_check_data_ui,self).__init__(parent)
        self.setWindowFlags(Qt.Qt.Window|Qt.Qt.WindowStaysOnTopHint)
        
        self.check_type = check_type

        self.setGeometry(700, 200, 500, 600)
        if self.check_type == "view_job":
            self.setGeometry(700, 200, 800, 600)
            
        self.setObjectName("mainWindow")        
        
        self.groupBox1 = QtGui.QGroupBox()
        self.tableWidget = QtGui.QTableView()
        self.create_new_btn = QtGui.QPushButton(u"新建序号")
        self.update_check_data_btn = QtGui.QPushButton(u"上传项目")
        self.update_check_current_job_data_btn = QtGui.QPushButton(u"更新项目")
        if self.check_type == "view_job":
            self.update_check_current_job_data_btn.hide()
            
        if self.check_type == "add_user":
            self.update_check_data_btn.setText(u"上传用户")
        
        self.filter_label = QtGui.QLabel(u"按用户过滤")
        self.filter_combox = QtGui.QComboBox()
        self.filter_combox.addItem("")
        
        group_layout1 = QtGui.QGridLayout()        
        group_layout1.addWidget(self.tableWidget, 1, 0, 1, 8)        
        if self.check_type in ("job", "view_job"):
            group_layout1.addWidget(self.filter_label, 0, 0, 1, 1)
            group_layout1.addWidget(self.filter_combox, 0, 1, 1, 2)            
            group_layout1.addWidget(self.update_check_current_job_data_btn, 2, 0, 1, 2)
        else:            
            group_layout1.addWidget(self.create_new_btn, 2, 0, 1, 1)
            group_layout1.addWidget(self.update_check_data_btn, 2, 1, 1, 1)
            
        if ".exe" in sys.argv[0]:
            self.filter_job_label = QtGui.QLabel(u"按型号过滤")
            self.filter_job_editor = QtGui.QLineEdit()
            self.filter_job_button = QtGui.QPushButton(u"查询")
            
        group_layout1.setSpacing(5)
        group_layout1.setContentsMargins(5, 5, 5, 5)
        self.groupBox1.setLayout(group_layout1)
        
        self.dic_editor = {}
        self.dic_label = {}        
        self.show_job_item_list = [u"序号", u"检测项目描述", u"检测状态"]
        
        arraylist1 = [{u"序号": "QLineEdit"},
                      {u"程序函数名称": "QLineEdit"},
                      {u"检测项目描述": "QLineEdit"},
                      {u"检测状态": "QComboBox"},
                      {u"CAM制作运行": "QComboBox"},
                      {u"CAM审核运行": "QComboBox"},
                      {u"检测内外层": "QComboBox"},
                      {u"程序完整路径": "QLineEdit"},
                      {u"提示或拦截": "QComboBox"},
                      {u"备注": "QLineEdit"},
                      ]
        
        if self.check_type == "add_user":
            arraylist1 = [
                {u"序号": "QLineEdit"},
                {u"用户工号": "QLineEdit"},
                {u"用户姓名": "QLineEdit"},
                {u"用户职能": "QComboBox"},]            

        group_box_font = QtGui.QFont()
        group_box_font.setBold(True)    
        widget1 = self.set_widget(group_box_font,
                                  arraylist1,
                                   u"基本信息确认",
                                   "")

        main_layout =  QtGui.QVBoxLayout()
        
        if self.check_type in ("job", "system", "add_user"):            
            main_layout.addWidget(widget1)
            
        main_layout.addWidget(self.groupBox1)        
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self.setMainUIstyle()        

        self.tableWidget.setMouseTracking(True)
        self.tableWidget.entered.connect(self.showToolTip)
        self.tableWidget.clicked.connect(self.change_editor_text)
        self.update_check_data_btn.clicked.connect(self.uploading_data)
        self.update_check_current_job_data_btn.clicked.connect(self.uploading_current_job_data)
        self.create_new_btn.clicked.connect(self.create_new_data_line)
        self.filter_combox.currentIndexChanged.connect(self.filter_data)

        self.setTableWidget()
        self.initGenesisData()
        
        self.get_check_data()
        
        if self.check_type == "system":
            self.setWindowTitle(u"HDI检测项目维护 %s" % __version__)
        elif self.check_type == "job":
            self.setWindowTitle(u"HDI当前型号检测项目维护 %s" % __version__)
        elif self.check_type == "view_job":
            self.setWindowTitle(u"HDI查看当前型号检测结果 %s" % __version__)
        elif self.check_type == "add_user":
            self.setWindowTitle(u"维护用户信息 %s" % __version__)        
        
    def get_item_value(self):
        """获取界面参数"""	
        self.dic_item_value = {}
        for key, value in self.dic_editor.iteritems():
            if isinstance(self.dic_editor[key], QtGui.QLineEdit):
                self.dic_item_value[key] = unicode(self.dic_editor[key].text(
                    ).toUtf8(), 'utf8', 'ignore').encode('cp936').decode("cp936")
            elif isinstance(self.dic_editor[key], QtGui.QComboBox):
                self.dic_item_value[key] = unicode(self.dic_editor[key].currentText(
                    ).toUtf8(), 'utf8', 'ignore').encode('cp936').decode("cp936")
                
    def filter_data(self):        
        user = self.filter_combox.currentText()
        row = self.model.rowCount()                
        for i in range(row):            
            self.tableWidget.showRow(i)            
        self.tableWidget.viewport().update() 
        recordStyleList = self.model.findItems(user, QtCore.Qt.MatchContains, 2)        
        recordStyleIndex = [item.row() for item in recordStyleList]        
        for i in range(row):            
            if i not in recordStyleIndex:                
                self.tableWidget.hideRow(i)                      
    
    def uploading_data(self):
        self.get_item_value()
        if self.dic_item_value[u"序号"] == "":
            showMessageInfo(u"序号不能为空，请检查")
            return
        
        arraylist = [u"确认要上传更新此检测项目:"]
        for key, value in self.dic_item_value.iteritems():
            log = key + ":   " + value
            arraylist.append(log)
        
        if arraylist:
            res = showQuestionMessageInfo(*arraylist)
            if not res:
                return            
            
            dic_value = {}
            for key, value in self.dic_item_value.iteritems():
                dic_value[dic_zu[key]] = value
            
            tablename = None
            if self.check_type == "system":                
                tablename = "pdm_job_check_function_list"
            elif self.check_type == "add_user":
                tablename = "pdm_job_check_user_list"
                
            uploading_data(tablename, dic_value)
            
            showMessageInfo(u"上传成功")
            
            self.get_check_data()
            
    def uploading_current_job_data(self):
        self.get_item_value()
        arraylist = [u"确认要上传更新此检测项目:"]
        for key, value in self.dic_item_value.iteritems():
            if key in self.show_job_item_list:                
                log = key + ":   " + value
                arraylist.append(log)
        
        if arraylist:
            res = showQuestionMessageInfo(*arraylist)
            if not res:
                return
            
            check_id = self.dic_item_value[u"序号"]
            time_format = time.strftime("%Y%m%d %H:%M", time.localtime())
            note = u"{2} 检测状态被用户{0}修改为{1}".format(user, self.dic_item_value[u"检测状态"], time_format)
            params = u"check_status='{0}',note='{1}'".format(self.dic_item_value[u"检测状态"], note)
            update_current_job_check_log(check_id, params)
            showMessageInfo(u"更新成功")
            self.get_check_data()
            
    def create_new_data_line(self):
        for key, editor in self.dic_editor.iteritems():
            if isinstance(editor, QtGui.QLineEdit):
                editor.clear()                
            if isinstance(editor, QtGui.QComboBox):
                editor.setCurrentIndex(0)
                
        self.dic_editor[u"序号"].setText(str(len(self.check_data_info) + 1))
        
    def change_editor_text(self, index):
        if index.data() is None: return
        data = index.model().item(index.row(), 0)
        if data is None:
            return
        
        if self.check_type == "view_job":
            return
        
        check_id = int(data.text())
        for dic_info in self.check_data_info:
            if dic_info["id"] == check_id:
                for key, editor in self.dic_editor.iteritems():
                    if isinstance(editor, QtGui.QLineEdit):
                        editor.clear()    
                        if dic_info[dic_zu[key]] is not None:
                            if key in (u"序号", u"用户工号"):
                                editor.setText(str(dic_info[dic_zu[key]]))
                            else:
                                editor.setText(dic_info[dic_zu[key]].decode("utf8"))
                        
                    if isinstance(editor, QtGui.QComboBox):
                        if dic_info[dic_zu[key]] is not None:                            
                            pos = editor.findText(dic_info[dic_zu[key]].decode("utf8"), QtCore.Qt.MatchExactly)
                            editor.setCurrentIndex(pos)                        
        
    def initGenesisData(self):	
        
        if self.check_type == "add_user":                
            for item in ["", u"制作人", u"审核人", u"测试员", u"管理员"]:
                self.dic_editor[u"用户职能"].addItem(item)
                
            self.dic_editor[u"序号"].setEnabled(False)
        else:            
            for item in ["", "normal", "test", "cancel"]:
                self.dic_editor[u"检测状态"].addItem(item)
                
            for item in ["", u"是", u"否"]:
                self.dic_editor[u"CAM制作运行"].addItem(item)
                self.dic_editor[u"CAM审核运行"].addItem(item)
                
            for item in ["", u"提示", u"拦截", u"拦截(不放行)"]:
                self.dic_editor[u"提示或拦截"].addItem(item)          
    
            for item in ["","all", "inner", "outer"]:
                self.dic_editor[u"检测内外层"].addItem(item)
                
            self.dic_editor[u"序号"].setEnabled(False)
        
    def set_widget(self, font, arraylist, title, checkbox):
        groupbox = QtGui.QGroupBox()
        groupbox.setTitle(title)
        groupbox.setStyleSheet("QGroupBox:title{color:green}")
        groupbox.setFont(font)	
        gridlayout = self.get_layout(arraylist, checkbox)
        groupbox.setLayout(gridlayout)
        return groupbox         

    def get_layout(self, arraylist, checkbox):
        gridlayout = QtGui.QGridLayout()
        for i, name in enumerate(arraylist):
            for key, value in name.iteritems():
                self.dic_label[key] = QtGui.QLabel()
                self.dic_label[key].setText(key)
                self.dic_editor[key] = getattr(QtGui, value)()
                
                if self.check_type == "job":
                    if key == u"检测状态":
                        self.dic_editor[key].setFixedWidth(120)
                        
                    if key not in self.show_job_item_list:
                        self.dic_label[key].hide()
                        self.dic_editor[key].hide()
                    
                col = 2 if i % 2 else 0
                row = -1 if col else 0
                gridlayout.addWidget(self.dic_label[key], i + 1 + row, 1 + col, 1, 1)
                gridlayout.addWidget(self.dic_editor[key], i + 1 + row, 2 + col, 1, 1)

        gridlayout.setSpacing(5)
        gridlayout.setContentsMargins(5, 5,5, 5)
        gridlayout.setAlignment(QtCore.Qt.AlignTop)

        return gridlayout  
        
    def setTableWidget(self):
        table = self.tableWidget
        if self.check_type == "system": 
            columnHeader = [u"序号", u"检测项目", u"检测状态"]
        elif self.check_type == "job":
            columnHeader = [u"序号", u"检测项目", u"用户"]
        elif self.check_type == "view_job":
            columnHeader = [u"序号", u"检测项目",u"用户", u"检测时间", u"检测结果", u"警报信息"]
        elif self.check_type == "add_user":
            columnHeader = [u"序号",u"工号", u"姓名", u"职能"]
            
        self.tableModel = QtGui.QStandardItemModel(table)
        self.tableModel.setColumnCount(len(columnHeader))
        for j in range(len(columnHeader)):
            self.tableModel.setHeaderData(
                j, Qt.Qt.Horizontal, columnHeader[j])
        table.setModel(self.tableModel)
        table.setEditTriggers(QtGui.QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        table.verticalHeader().setVisible(False)
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setDefaultAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        header.setTextElideMode(QtCore.Qt.ElideRight)
        header.setClickable(True)
        header.setMouseTracking(True)
        table.setColumnWidth(0, 40)
        table.setColumnWidth(1, 350)
        if self.check_type == "view_job":
            table.setColumnWidth(1, 200)
        if self.check_type == "add_user":
            table.setColumnWidth(1, 120)
        table.setColumnWidth(2, 60) 
   
    def get_check_data(self):
        if self.check_type == "system":            
            self.check_data_info = get_check_data_info()
        elif self.check_type in ('job', "view_job"):
            self.check_data_info = get_current_job_check_data_info(condition="jobname='{0}'".format(os.environ.get("JOB", "NULL")))
            # 测试
            # self.check_data_info = get_current_job_check_data_info(condition="jobname='c18304of733b1-lyh'")
        elif self.check_type == "add_user":
            self.check_data_info = get_user_data_info()
        
        self.set_model_data(self.check_data_info)

    def set_model_data(self, data_info):
        """设置表内数据"""
        self.model = self.tableWidget.model()
        self.model.setRowCount(len(data_info))
        users = []
        for i, dic_info in enumerate(sorted(data_info, key= lambda x: x["id"])):
            if dic_info:
                index = self.model.index(i,0, QtCore.QModelIndex())
                self.model.setData(index, dic_info["id"])
                
                if self.check_type == "add_user":
                    index1 = self.model.index(i, 1, QtCore.QModelIndex())
                    self.model.setData(index1, dic_info["person_number"])
                    
                    index1 = self.model.index(i, 2, QtCore.QModelIndex())
                    self.model.setData(index1, dic_info["person_name"].decode("utf8"))
                    
                    index1 = self.model.index(i, 3, QtCore.QModelIndex())
                    self.model.setData(index1, dic_info["person_role"].decode("utf8"))                      
                    
                else:
                    index1 = self.model.index(i, 1, QtCore.QModelIndex())
                    self.model.setData(index1, dic_info["function_description"].decode("utf8"))
                
                if self.check_type in ("job", "view_job"):    
                    index1 = self.model.index(i, 2, QtCore.QModelIndex())
                    self.model.setData(index1, dic_info["check_user"].decode("utf8"))
                    user = ""
                    for dic_user_info in user_info_list:
                        if str(dic_info["check_user"]) == str(dic_user_info["person_number"]):
                            self.model.setData(index1, dic_user_info["person_name"].decode("utf8"))                   
                            user = dic_user_info["person_name"].decode("utf8")
                            
                    if not user:                        
                        user = dic_info["check_user"].decode("utf8")
                    if user not in users:
                        users.append(user)
                        self.filter_combox.addItem(user)
                
                if self.check_type in ('system'):
                    index1 = self.model.index(i, 2, QtCore.QModelIndex())
                    self.model.setData(index1, dic_info["check_status"].decode("utf8"))                    
                        
                if self.check_type == "view_job":                    
                    index = self.model.index(i,3, QtCore.QModelIndex())
                    self.model.setData(index, "" if dic_info["check_time"] is None else str(dic_info["check_time"]))                    
                    
                    index = self.model.index(i,4, QtCore.QModelIndex())
                    self.model.setData(index, "" if dic_info["check_process"] is None else dic_info["check_process"].decode("utf8"))
                    
                    index = self.model.index(i,5, QtCore.QModelIndex())
                    self.model.setData(index, "" if dic_info["check_log"] is None else dic_info["check_log"].decode("utf8"))                
                
    def eventFilter(self,  source,  event):
        if event.type() == QtCore.QEvent.HoverMove:#表头气泡提示                        
            pos = event.pos()
            section = self.tableWidget.horizontalHeader().logicalIndexAt(pos)
            if section < 0:
                return QtGui.QMainWindow.eventFilter(self,  source,  event)
            model = self.tableWidget.model()
            QtGui.QToolTip.showText(QtGui.QCursor.pos(),
                                    model.headerData(section,QtCore.Qt.Horizontal,QtCore.Qt.DisplayRole))
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
    main_widget = update_check_data_ui(check_type="view_job")
    main_widget.show()
    sys.exit(app.exec_())
    

