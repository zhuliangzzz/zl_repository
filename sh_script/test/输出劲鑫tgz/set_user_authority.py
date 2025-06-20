#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__    = "20230912"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""设置用户权限 """

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
    #jobname = os.environ.get("JOB", "c89804pi375a1-lyh")
    #if os.environ.get("JOB", None) is None:
        #os.environ["JOB"] = jobname
        
import pic
import time

from create_ui_model import app, showQuestionMessageInfo, \
     showMessageInfo
from PyQt4 import QtCore, QtGui, Qt

from oracleConnect import oracleConn
erp_conn=oracleConn("topprod")

import MySQL_DB
conn = MySQL_DB.MySQL()
dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                           username='root', passwd='k06931!')
dbc_p = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='project_status', prod=3306,
                           username='root', passwd='k06931!')

try:
    from TOPCAM_IKM import IKM
    ikm_fun = IKM()
except Exception, e:
    showMessageInfo(u"连接topcam数据库异常，请联系程序组处理:", str(e))
    sys.exit()
    
dic_zu = {u"序号": "id",
          u"用户工号": "user_id",
          u"用户姓名": "user_name",
          u"权限类型": "Authority_Name",
          u"权限状态": "Authority_Status",}

class set_authority_ui(QtGui.QDialog):
    def __init__(self,parent = None):
        super(set_authority_ui,self).__init__(parent)
        self.setWindowFlags(Qt.Qt.Window|Qt.Qt.WindowStaysOnTopHint)    

        self.setGeometry(700, 200, 500, 600)            
        self.setObjectName("mainWindow")        
        
        self.groupBox1 = QtGui.QGroupBox()
        self.tableWidget = QtGui.QTableView()
        self.create_new_btn = QtGui.QPushButton(u"新建序号")
        self.update_check_data_btn = QtGui.QPushButton(u"上传项目")
        self.update_check_current_job_data_btn = QtGui.QPushButton(u"更新项目")
        
        self.filter_label = QtGui.QLabel(u"按用户过滤:")
        self.filter_combox = QtGui.QComboBox()
        self.filter_combox.addItem("")
        
        group_layout1 = QtGui.QGridLayout()        
        group_layout1.addWidget(self.tableWidget, 1, 0, 1, 8) 
        group_layout1.addWidget(self.create_new_btn, 2, 0, 1, 1)
        group_layout1.addWidget(self.update_check_data_btn, 2, 1, 1, 1)            
            
        group_layout1.setSpacing(5)
        group_layout1.setContentsMargins(5, 5, 5, 5)
        self.groupBox1.setLayout(group_layout1)
        
        self.dic_editor = {}
        self.dic_label = {}        
        self.show_job_item_list = [u"序号", u"检测项目描述", u"检测状态"]        

        arraylist1 = [            
            {u"序号": "QLineEdit"},
            {u"用户工号": "QLineEdit"},
            {u"用户姓名": "QLineEdit"},
            #{u"权限类型": "QComboBox"},
            #{u"权限状态": "QComboBox"},
        ]
        
        self.arraylist2 = [{u"审核人权限": "QCheckBox"},
                           {u"解锁内外层": "QCheckBox"},
                           {u"更改正式型号名": "QCheckBox"},
                           {u"修改net名": "QCheckBox"},
                           {u"管理用户权限": "QCheckBox"}, 
                           {u"NV资料查看权限": "QCheckBox"},
                           {u"手动输出TGZ权限": "QCheckBox"},
                           {u"审批放行权限": "QCheckBox"},
                           {u"删除用户": "QCheckBox"},
                           {u"解锁临时层": "QCheckBox"},
                           ]
            
        group_box_font = QtGui.QFont()
        group_box_font.setBold(True)    
        widget1 = self.set_widget(group_box_font,
                                  arraylist1,
                                   u"基本信息确认",
                                   "")
        
        widget2 = self.set_widget(group_box_font,
                                  self.arraylist2,
                                   u"权限信息",
                                   "")
        
        main_layout =  QtGui.QVBoxLayout()          
        main_layout.addWidget(widget1)
        main_layout.addWidget(widget2)
        main_layout.addWidget(self.groupBox1)        
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self.setMainUIstyle()        

        self.tableWidget.setMouseTracking(True)
        self.tableWidget.entered.connect(self.showToolTip)
        self.tableWidget.clicked.connect(self.change_editor_text)
        self.update_check_data_btn.clicked.connect(self.uploading_data_message)
        # self.update_check_current_job_data_btn.clicked.connect(self.uploading_current_job_data)
        self.create_new_btn.clicked.connect(self.create_new_data_line)
        self.filter_combox.currentIndexChanged.connect(self.filter_data)

        self.setTableWidget()
        self.initGenesisData()        
        self.get_check_data()
        self.set_btn_enabled()
        self.setWindowTitle(u"HDI程序权限维护 %s" % __version__)    
        
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
            elif isinstance(self.dic_editor[key], QtGui.QCheckBox):
                self.dic_item_value[key] = u"是" if self.dic_editor[key].isChecked() else u"否"
                
    def set_btn_enabled(self):
        """设置是否有权限更新上传"""
        self.update_check_data_btn.setEnabled(False)        
        for dic_info in self.check_data_info:
            if str(dic_info["user_id"]) == user:
                if dic_info["Authority_Name"] == u"管理用户权限" and \
                   dic_info["Authority_Status"] ==u"是":
                    self.update_check_data_btn.setEnabled(True)
                    
    def get_user_name(self,user_id): 
        sql=u"SELECT gen02 姓名 FROM s01.gen_file WHERE gen01='{0}'".format(user_id)
        data_info=erp_conn.executeSql(sql)     
        return data_info[0][0].decode("utf8") if data_info else ""
    
    def set_user_name(self, value):
        name = self.get_user_name(value)
        self.dic_editor[u"用户姓名"].setText(name)
                
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
    
    def uploading_data_message(self):
        self.get_item_value()
        for key in (u"序号", u"用户姓名", u"用户工号"):            
            if self.dic_item_value[key] == "":
                showMessageInfo(u"{0}不能为空，请检查".format(key))
                return
        
        arraylist = [u"确认要上传更新此用户 {0} 权限状态:".format(self.dic_item_value[u"用户姓名"])]
        for key, value in self.dic_item_value.iteritems():
            #if key in [u"审核人权限",u"解锁内外层",
                       #u"更改正式型号名",u"修改net名",
                       #u"管理用户权限"]:
            if key in [x.keys()[0] for x in self.arraylist2]:
                
                log = key + ":   " + value
                arraylist.append(log)
        
        # print(self.dic_item_value)
        if arraylist:
            res = showQuestionMessageInfo(*arraylist)
            if not res:
                return
            
            dic_value = {"user_id": self.dic_item_value[u"用户工号"],"user_name": self.dic_item_value[u"用户姓名"],}
            #for key, value in self.dic_item_value.iteritems():
                #for key in [u"用户姓名", u"用户工号"]:  
                    #dic_value[dic_zu[key]] = value
                
            dic_value["create_user"] = user
            # print(json.dumps(dic_value))            
            # return
            update_all_status = False
            for key, value in self.dic_item_value.iteritems():
                #if key in [u"审核人权限",u"解锁内外层",
                           #u"更改正式型号名",u"修改net名",
                           #u"管理用户权限"]:
                if key in [x.keys()[0] for x in self.arraylist2]:
                    dic_value["Authority_Name"] = key
                    dic_value["Authority_Status"] = value
                    self.uploading_data(dic_value)
                    if key == u"删除用户" and value == u"是":
                        update_all_status = True
            
            if update_all_status:
                sql = u"""update hdi_engineering.incam_user_authority
                set Authority_Status = '否',create_time=now(),notes='被用户{1}更新状态'
                where user_id = '{0}' and Authority_Name <> '删除用户'"""
                conn.SQL_EXECUTE(dbc_m, sql.format(dic_value["user_id"], user))
                
            showMessageInfo(u"上传成功")
            
            self.get_check_data()
            self.create_new_data_line()

    def uploading_data(self, dic_value, database="hdi_engineering.incam_user_authority"):
        """上传数据到mysql系统"""
        sql = u"select * from {1} where user_id = '{0}' and Authority_Name = '{2}'"
        data_info = conn.SQL_EXECUTE(dbc_m, sql.format(dic_value["user_id"], database, dic_value["Authority_Name"]))
        if data_info:
            arraylist = []
            for key, value in dic_value.iteritems():
                arraylist.append(u"{0}='{1}'".format(key, value))                
                
            sql = u"""update {2} set {1},create_time=now(),notes='被用户{3}更新状态' where user_id = '{0}' and Authority_Name = '{4}'"""
            conn.SQL_EXECUTE(dbc_m, sql.format(dic_value["user_id"], ",".join(arraylist), database,user, dic_value["Authority_Name"]))              
                
        else:
            arraylist_key = []
            arraylist_value = []
            for key, value in dic_value.iteritems():
                arraylist_key.append(key)
                arraylist_value.append(value)

            insert_sql = u"insert into {2} ({0}) values ({1})"
            conn.SQL_EXECUTE(dbc_m, insert_sql.format(",".join(arraylist_key),",".join(["%s"]*len(arraylist_key)), database), arraylist_value) 
                
    def create_new_data_line(self):
        for key, editor in self.dic_editor.iteritems():
            if isinstance(editor, QtGui.QLineEdit):
                editor.clear()                
            if isinstance(editor, QtGui.QComboBox):
                editor.setCurrentIndex(0)
                
            if isinstance(editor, QtGui.QCheckBox):
                editor.setChecked(False)     
                
            if key in (u"用户姓名", u"用户工号"):
                editor.setEnabled(True)            
                
        self.dic_editor[u"序号"].setText(str(len(self.check_data_info) + 1))
        
    def change_editor_text(self, index):
        if index.data() is None: return
        data = index.model().item(index.row(), 0)
        if data is None:
            return
        
        dic_authority_info = index.model().item(index.row(), 3).text()
        #for dic_info in self.check_data_info:
            #if dic_info["id"] == check_id:
        for key, editor in self.dic_editor.iteritems():
            if isinstance(editor, QtGui.QLineEdit):
                editor.clear()    
                
                if key == u"序号":
                    editor.setText(index.model().item(index.row(), 0).text())
                elif key == u"用户工号":
                    editor.setText(index.model().item(index.row(), 1).text())
                elif key == u"用户姓名":
                    editor.setText(index.model().item(index.row(), 2).text())                        
                    
                if key in (u"用户姓名", u"用户工号"):
                    editor.setEnabled(False)
                
            if isinstance(editor, QtGui.QCheckBox):
                if key in dic_authority_info:                    
                    editor.setChecked(True)
                else:
                    editor.setChecked(False)
        
    def initGenesisData(self):
        #for item in ["", u"审核人权限",
                     #u"解锁内外层", u"更改正式型号名",
                     #u"修改net名", u"管理用户权限"]:
            #self.dic_editor[u"权限类型"].addItem(item)
            
        #for item in [u"是", u"否"]:
            #self.dic_editor[u"权限状态"].addItem(item)
            
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
                
                if key in (u"用户姓名", u"用户工号"):
                    self.dic_editor[key].setEnabled(False)                
                    
                if key == u"用户工号":
                    self.dic_editor[key].textChanged.connect(self.set_user_name)                
                    
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
        columnHeader = [u"序号",u"工号", u"姓名", u"已开权限", u"权限明细"]            
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
        table.setColumnWidth(1, 100)
        table.setColumnWidth(2, 100)
        table.hideColumn(4)
   
    def get_check_data(self):
        sql = "select id,user_id,user_name,Authority_Name,Authority_Status from hdi_engineering.incam_user_authority "
        self.check_data_info = conn.SELECT_DIC(dbc_m, sql)
        
        # self.check_data_info = get_user_data_info()        
        self.set_model_data(self.check_data_info)

    def set_model_data(self, data_info):
        """设置表内数据"""
        self.model = self.tableWidget.model()        
        users = [x["user_id"] for x in data_info]
        new_users = []
        for i, user_id in enumerate(set(users)):
            user_name = [x["user_name"] for x in data_info
                         if x["user_id"] == user_id][0]
            Authority_Names = [x["Authority_Name"] for x in data_info
                               if x["user_id"] == user_id
                               and x["Authority_Status"] == u"是"]
            
            if u"删除用户" in Authority_Names:
                continue   
            new_users.append(user_id)
        
        self.model.setRowCount(len(set(new_users)))
        
        for i, user_id in enumerate(set(new_users)):
            user_name = [x["user_name"] for x in data_info
                         if x["user_id"] == user_id][0]
            Authority_Names = [x["Authority_Name"] for x in data_info
                               if x["user_id"] == user_id
                               and x["Authority_Status"] == u"是"]            
            
            Authority_info = [x for x in data_info
                              if x["user_id"] == user_id]
            
            index = self.model.index(i,0, QtCore.QModelIndex())
            self.model.setData(index, i+1)

            index1 = self.model.index(i, 1, QtCore.QModelIndex())
            self.model.setData(index1, user_id)
            
            index1 = self.model.index(i, 2, QtCore.QModelIndex())
            self.model.setData(index1, user_name)
            
            index1 = self.model.index(i, 3, QtCore.QModelIndex())
            self.model.setData(index1, ";".join(Authority_Names))
            
            index1 = self.model.index(i, 4, QtCore.QModelIndex())
            self.model.setData(index1, json.dumps(Authority_info)) 
                
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
    main_widget = set_authority_ui()
    main_widget.show()
    sys.exit(app.exec_())
    

