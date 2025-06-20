#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2021/12/01
# @Revision     :    1.0.0
# @File         :    job_lock_main.py
# @Software     :    PyCharm
# @Usefor       :    料号锁定及解锁
# @Modify：2022.05.30 增加资料审批时的窗口最小化及还原
# ---------------------------------------------------------#
import os
import sys
import platform
import sip
sip.setapi('QVariant', 2)
from PyQt4 import QtCore, QtGui, Qt
import jobTableUI as JTUI
import json
import time
import ast

from Packages import GetData
# from Packages import BackupData

# reload (sys)
# sys.setdefaultencoding ('utf-8')

# --导入Package
sysstr = platform.system()
if sysstr == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    # sys.path.append (r"D:/genesis/sys/scripts/Package")

elif sysstr == "Linux":
    sys.path.append(r"/incam/server/site_data/scripts/Package")
else:
    print ("Other System tasks")
import genCOM_26
import Oracle_DB
# === 以下包用于评审 ===
from mwClass_V2 import *

import pic
import gClasses

import MySQL_DB
conn = MySQL_DB.MySQL()
dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                           username='root', passwd='k06931!')
dbc_p = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='project_status', prod=3306,
                           username='root', passwd='k06931!')


def unicode_convert(input):
    """
    用于解决json.load json中带u开头的问题
    :param input:
    :return:
    """
    if isinstance(input, dict):
        new_dict = {}
        for key, value in input.iteritems():
            new_dict[unicode_convert(key)] = unicode_convert(value)
        return new_dict
        # return {unicode_convert (key): unicode_convert (value) for key, value in input.iteritems ()}
    elif isinstance(input, list):
        return [unicode_convert(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input


class QHeaderView(QtGui.QHeaderView):
    def __init__(self, Orientation, parent=None, dic_color={}):
        super(QHeaderView, self).__init__(Orientation, parent)
        self.Orientation = Orientation
        self.dic_color = dic_color
        self.selected_section = []
        self.control_key_press = False

    def paintSection(self, painter, rect, logicalIndex):  # QPaintEvent *
        model = self.parent().model()
        text = model.headerData(logicalIndex, self.Orientation, QtCore.Qt.DisplayRole)
        if self.dic_color.get(logicalIndex) is None:        
            return

        if self.Orientation == Qt.Vertical:
            painter.setPen(QtGui.QColor(111, 156, 207)) # 分隔线颜色
            painter.setBrush(QtGui.QColor(111, 156, 207))
            painter.drawRect(rect)
            
            rect.setHeight(rect.height() - 1.01)
            rect.setWidth(rect.width() - 1.01)
            modelIndexes = self.parent().selectedIndexes()

            selecteditems = [modelIndex.row() for modelIndex in modelIndexes if modelIndex.row() == logicalIndex]
            # print 'len(selecteditems)',len(selecteditems),'self.parent().columnCount()',self.parent().columnCount()
            if len(selecteditems) == self.parent().columnCount() - 1:
                painter.setPen(QtGui.QColor(6, 94, 187)) # 整行选中时头颜色
                painter.setBrush(QtGui.QColor(6, 94, 187))
                painter.drawRect(rect)
                painter.setPen(Qt.white)
                painter.drawText(rect, Qt.AlignCenter,
                                 str(text) if isinstance(text, int) else text)
                return
        else:
            modelIndexes = self.parent().selectedIndexes()
            selecteditems = [modelIndex.column() for modelIndex in modelIndexes if modelIndex.column() == logicalIndex]
            if len(selecteditems) == self.parent().rowCount():
                painter.setPen(Qt.white) # 列头颜色
                painter.setBrush(Qt.white)
                painter.drawRect(rect)
                painter.setPen(Qt.black)
                painter.drawText(rect, Qt.AlignCenter,
                                 str(text) if isinstance(text, int) else text)
                return
        # print 'rect',rect

        painter.setPen(self.dic_color[logicalIndex])
        # painter.setPen(QtGui.QColor(216, 216, 216))
        # painter.setPen(QtGui.QColor(253, 199, 77))
        painter.setBrush(self.dic_color[logicalIndex])
        painter.drawRect(rect)
        painter.setPen(Qt.black)
        painter.drawText(rect, Qt.AlignCenter,
                         str(text) if isinstance(text, int) else text)

    def mousePressEvent(self, event):
        pos = event.pos()
        modelIndexes = self.parent().selectedIndexes()
        if len(modelIndexes) == 1 and not self.control_key_press:
            self.parent().clearSelection()

        self.parent().setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        if self.Orientation == Qt.Horizontal:
            section = self.parent().horizontalHeader().logicalIndexAt(pos)
            self.parent().selectColumn(section)
        else:
            section = self.parent().verticalHeader().logicalIndexAt(pos)
            self.parent().selectRow(section)

        self.selected_section = [section]
        # print "control", self.control_key_press         

    def mouseMoveEvent(self, event):
        pos = event.pos()
        if event.buttons() == QtCore.Qt.LeftButton:
            self.parent().setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
            if self.Orientation == Qt.Horizontal:
                section = self.parent().horizontalHeader().logicalIndexAt(pos)
            else:
                section = self.parent().verticalHeader().logicalIndexAt(pos)
                    
            if not self.control_key_press:                
                self.parent().clearSelection()
                
            if section < self.selected_section[0]:
                pre = section
                suffix = self.selected_section[0] + 1
            else:
                pre = self.selected_section[0]
                suffix = section + 1
                
            if self.Orientation == Qt.Horizontal:
                for col in range(pre, suffix):
                    self.parent().selectColumn(col)
            else:
                for row in range(pre, suffix):
                    self.parent().selectRow(row)                

            if section not in self.selected_section:
                self.selected_section.append(section)

    def mouseReleaseEvent(self, event):
        self.selected_section = []
        self.parent().setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)


class MyApp(QtGui.QWidget):
    def __init__(self, parent=None):
        super(MyApp, self).__init__(parent)
        # QtGui.QWidget.__init__(self, parent)
        self.job_name = os.environ.get('JOB')

        PRODUCT = os.environ.get('INCAM_PRODUCT', None)
        if platform.system() == "Windows":
            self.userDir = "%s/fw/jobs/%s/user" % (os.environ.get('GENESIS_DIR', 'D:/genesis'), self.job_name)
        else:
            self.userDir = os.environ.get('JOB_USER_DIR', None)
            if not PRODUCT and not self.userDir:
                # --Linux环境下网络版genesis没有定义INCAM_PRODUCT环境变量
                self.userDir = "%s/fw/jobs/%s/user" % (os.environ.get('GENESIS_DIR', '/genesis'), self.job_name)
        self.cwd = os.path.dirname(sys.argv[0])
        self.job_lock = '%s_job_lock.json' % self.job_name
        
        # --接收TL_PUB_run_source_script_new.pl 传递过来的环境变量，并转化
        self.paramJson = json.loads(os.environ.get('PARAM').replace(';', ','))
        self.processID = int(self.paramJson['process_id'])
        self.jobID = int(self.paramJson['job_id'])
        self.userID = self.paramJson['user']   

        self.ui = JTUI.Ui_widget()
        self.ui.setupUi(self)
        self.setObjectName("mainWindow")
        self.redealui()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)  # 窗口总是在前
        # step_name = os.environ.get ('STEP')
        self.getDATA = GetData.Data()
        self.GEN = genCOM_26.GEN_COM()
        
        # --从数据库中获取lock记录 获取不到在从文件内获取 20230904 by lyh
        self.pre_lock = self.getJOB_LockInfo(dataType='locked_info')
        if not self.pre_lock:
            self.pre_lock = self.read_file(sour_file=self.job_lock)
            
        if "lock_panelization_status" in self.pre_lock:
            if "yes" in self.pre_lock["lock_panelization_status"]:                
                self.ui.lock_panelization.setChecked(True)            
        
        self.step_list, self.layer_list = self.get_job_matrix()
        self.GEN.COM('get_user_name')
        self.cam_user = self.GEN.COMANS
        self.job_users = self.get_authorization()
        self.inner_checker = None
        if self.job_users:
            self.inner_checker = self.get_ERP_user_code(self.job_users[u'内层审核人'])

        self.ui.tableWidget.horizontalHeader().setVisible(True)
        self.ui.tableWidget.verticalHeader().setVisible(True)
        self.ui.tableWidget.setColumnHidden(0, True)  # 隐藏第一列
        self.ui.tableWidget.setRowHidden(0, True)  # 隐藏第一行
        
        self.setMainUIstyle()        

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Control:
                if getattr(self, "myvHeader", None):                    
                    self.myvHeader.control_key_press = True
                if getattr(self, "myhHeader", None):  
                    self.myhHeader.control_key_press = True

        if event.type() == QtCore.QEvent.KeyRelease:
            if event.key() == QtCore.Qt.Key_Control:
                if getattr(self, "myvHeader", None):   
                    self.myvHeader.control_key_press = False
                if getattr(self, "myhHeader", None):  
                    self.myhHeader.control_key_press = False
                
        if event.type() == QtCore.QEvent.Paint:
            # 设置表格左上角文字
            if source.objectName() == "corner_btn":
                opt = QtGui.QStyleOptionHeader()
                opt.init(source)
                
                state = QtGui.QStyle.State_None
                if source.isEnabled():
                    state = QtGui.QStyle.State_Enabled
                if source.isActiveWindow():
                    state = QtGui.QStyle.State_Active
                if source.isDown():
                    state = QtGui.QStyle.State_Sunken
                    
                opt.state = state                
                opt.rect = source.rect()
                opt.text = source.text()
                opt.textAlignment = QtCore.Qt.AlignCenter
                opt.position = QtGui.QStyleOptionHeader.OnlyOneSection
                painter = QtGui.QStylePainter(source)
                painter.drawControl(QtGui.QStyle.CE_Header, opt)
                return True

        return QtGui.QMainWindow.eventFilter(self, source, event)
    
    def setMainUIstyle(self):#设置风格
        file = QtCore.QFile(':/pic/fblue.qss')
        file.open(QtCore.QFile.ReadOnly)
        styleSheet = file.readAll()
        styleSheet = unicode(styleSheet, encoding='gb2312')
        old_string = """QTableView::item {"""
        new_string = """QTableView#my_no_color::item {"""
        styleSheet = styleSheet.replace(old_string, new_string)        
        QtGui.qApp.setStyleSheet(styleSheet)        

    def getJOB_LockInfo(self, dataType='locked_info'):
        """
        从数据库中获取料号的锁记录
        :param dataType: 获取的数据类型（status:locked_info log:locked_log）
        :return:dict
        """
        lockData = self.getDATA.getLock_Info(self.job_name.split("-")[0])

        try:
            return json.loads(lockData[dataType], encoding='utf8')
        except:
            # print u'传入的数据参数异常'
            return {}
    
    def redealui(self):
        self.resize(1080, 900)
        # --重新加载ico 图标
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(r"%s/logo.ico" % self.cwd), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
        self.ui.tableWidget_log.hide()
        self.setWindowTitle(u'料号锁定与解锁--%s' % self.job_name.upper())

        # self.ui.tableWidget.verticalScrollBar().valueChanged.connect(self.setValue)
        # self.ui.tableWidget.horizontalScrollBar().valueChanged.connect(self.setValue)
        QtCore.QObject.connect(self.ui.pushButton_close, QtCore.SIGNAL("clicked()"), self.close)
        QtCore.QObject.connect(self.ui.pushButton_lock, QtCore.SIGNAL('clicked()'), self.add_lock)
        QtCore.QObject.connect(self.ui.pushButton_unlock, QtCore.SIGNAL('clicked()'), self.add_unlock)
        QtCore.QObject.connect(self.ui.pushButton_apply, QtCore.SIGNAL('clicked()'), self.save_ui)
        # QtCore.QObject.connect(self.ui.tableWidget, QtCore.SIGNAL('itemSelectionChanged()'), self.selectrows_column)
        # QtCore.QObject.connect(self.ui.tableWidget, QtCore.SIGNAL('itemClicked(QTableWidgetItem*)'), self.selectcell)
        # QtCore.QObject.connect(self.ui.tableWidget, QtCore.SIGNAL('itemEntered(QTableWidgetItem*)'), self.selectcell)
        # self.ui.tableWidget.setMouseTracking(True)
        # QtCore.QObject.connect(self.ui.tableWidget, QtCore.SIGNAL('itemEntered(QTableWidgetItem*)'), self.selectcell)
        # QtCore.QObject.connect(self.ui.tableWidget, QtCore.SIGNAL('itemPressed(QTableWidgetItem*)'), self.selectcell2)

        QtCore.QObject.connect(self.ui.pushButton_showlog, QtCore.SIGNAL('clicked()'), self.showLog)
        QtCore.QObject.connect(self.ui.pushButton_closelog, QtCore.SIGNAL('clicked()'), self.hideLog)


    def setValue(self):
        """
        模仿首行冻结功能，动态显示列标题
        :return:
        """
        # print self.ui.tableWidget.verticalScrollBar().value()

        if self.ui.tableWidget.verticalScrollBar().value() == 0:
            self.ui.tableWidget.horizontalHeader().setVisible(False)
        else:
            self.ui.tableWidget.horizontalHeader().setVisible(True)

        # self.ui.tableWidget.horizontalHeader().setVisible(True)
        if self.ui.tableWidget.horizontalScrollBar().value() == 0:
            self.ui.tableWidget.verticalHeader().setVisible(False)
        else:
            self.ui.tableWidget.verticalHeader().setVisible(True)


    # def keyPressEvent(self, event):
    #     """ Ctrl + C复制表格内容 """
    #     if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
    #         # 获取表格的选中行
    #         selected_ranges = self.ui.tableWidget_log.selectedRanges()[0]  # 只取第一个数据块,其他的如果需要要做遍历,简单功能就不写得那么复杂了
    #         text_str = ""  # 最后总的内容
    #         # 行（选中的行信息读取）
    #         for row in range(selected_ranges.topRow(), selected_ranges.bottomRow() + 1):
    #             row_str = ""
    #             # 列（选中的列信息读取）
    #             for col in range(selected_ranges.leftColumn(), selected_ranges.rightColumn() + 1):
    #                 item = self.ui.tableWidget_log.item(row, col)
    #                 row_str += item.text() + '\t'  # 制表符间隔数据
    #             text_str += row_str + '\n'  # 换行
    #         clipboard = QApplication.clipboard()  # 获取剪贴板
    #         clipboard.setText(text_str)  # 内容写入剪贴板

    def hideLog(self):
        self.ui.tableWidget_log.hide()

    def showLog(self):
        pre_log_dict = self.read_file(sour_file='job_lock_log.json')
        # print pre_log_dict
        status_change = {'lock_add': u'锁定', 'unlock': u'解锁'}
        self.ui.tableWidget_log.show()
        row_num_list = [len(pre_log_dict[i][j]) for i in pre_log_dict for j in pre_log_dict[i] if
                        j in ['lock_add', 'unlock']]
        rs = 0
        for i in row_num_list:
            rs = i + rs
        self.ui.tableWidget_log.clearContents()
        self.ui.tableWidget_log.setRowCount(rs)

        key_array = sorted(pre_log_dict.keys(), reverse=True)
        cur_row_num = 0
        for time_key in key_array:
            item = QtGui.QTableWidgetItem()
            item.setText(str(pre_log_dict[time_key]['time']))
            self.ui.tableWidget_log.setItem(cur_row_num, 0, item)

            item = QtGui.QTableWidgetItem()
            item.setText(str(pre_log_dict[time_key]['user']))
            self.ui.tableWidget_log.setItem(cur_row_num, 1, item)
            for lock_status in status_change:
                if len(pre_log_dict[time_key][lock_status]) != 0:
                    # === 显示锁定变更 ===
                    item = QtGui.QTableWidgetItem()
                    item.setText(status_change[lock_status])
                    self.ui.tableWidget_log.setItem(cur_row_num, 2, item)
                    for lock_i, lock_detail in enumerate(pre_log_dict[time_key][lock_status]):
                        # === 显示锁定的Step ===
                        item = QtGui.QTableWidgetItem()
                        item.setText(str(lock_detail['step']))
                        self.ui.tableWidget_log.setItem(cur_row_num, 3, item)
                        # === 显示锁定的层别 ===
                        item = QtGui.QTableWidgetItem()
                        item.setText(str(lock_detail['layers']))
                        self.ui.tableWidget_log.setItem(cur_row_num, 4, item)
                        cur_row_num += 1
        self.ui.tableWidget_log.resizeColumnsToContents()
        self.ui.tableWidget_log.resizeRowsToContents()
        # self.ui.tableWidget_log.setRowCount(cur_row_num)

    def refresh_ui(self):
        # print 'c' * 40
        self.pre_lock = self.read_file(sour_file=self.job_lock)
        #self.ui.tableWidget.clearContents()
        #self.get_job_matrix()

        for i, layer in enumerate(self.layer_list, 1):
            for j, cur_step in enumerate(self.step_list, 1):
                if cur_step in self.pre_lock and layer in self.pre_lock[cur_step]:
                    self.add_lock(i=i, j=j)
                else:
                    self.clear_pass_labels(i, j)


        self.ui.tableWidget.resizeColumnsToContents()
        self.ui.tableWidget.resizeRowsToContents()

    def get_authorization(self):
        """
        在MySQL数据库中获取授权用户
        :return:
        """
        job_str = self.job_name
        DB_M = MySQL_DB.MySQL()
        dbc_m = DB_M.MYSQL_CONNECT(hostName='192.168.2.19', database='project_status', prod=3306, username='root',
                                   passwd='k06931!', )
        query_sql = u"""
        select   cam_d_checker	CAM外层复审人,
            cam_d_innerChecker	CAM内层复审人,
            panel_maker	拼版人,
            inner_maker	内层制作人,
            outer_maker	外层制作人,
            icheck_maker	内层审核人,
            ocheck_maker	外层审核人,
            input_maker	Input人,
            input_checker	input审核人,
            rout_maker	锣带制作人,
            rout_checker	锣带检查人,
            sub_maker	次外层制作人,
            sub_check_maker	次外层审核人
            from project_status_jobmanage psj
            --  and project_status_jobmanage.COLUMNS cname
        WHERE job = '%s'
        order by id desc """ % job_str.upper()
        query_result = DB_M.SELECT_DIC(dbc_m, query_sql)
        dbc_m.close()
        if not query_result:
            return None
        result_dict = query_result[0]
        # === 键为中文，需要带上u字符
        # for key in result_dict:
        #     if key == u'内层制作人':
        return result_dict

    def get_ERP_user_code(self, cam_user_name):
        """

        :return:
        """
        # === TODO ERP连接 ===
        DB_O = Oracle_DB.ORACLE_INIT()
        dbc_e = DB_O.DB_CONNECT(host='172.20.218.247', servername='topprod', port='1521',
                                username='zygc', passwd='ZYGC@2019')
        query_sql = """
         SELECT gen01 工号 FROM s01.gen_file WHERE gen02='%s'
         """ % cam_user_name
        query_result = DB_O.SQL_EXECUTE(dbc_e, query_sql)
        DB_O.DB_CLOSE(dbc_e)

        if query_result:
            e_user_name = query_result[0][0]
            # print  e_user_name.decode('utf8').encode('gbk') # 在Genesis下调试用
            return e_user_name.decode('utf8')
        else:
            return False

    def get_job_matrix(self):
        job_matrix = self.GEN.DO_INFO("-t matrix -e %s/matrix" % self.job_name)
        step_list = job_matrix['gCOLstep_name']
        layer_list = job_matrix['gROWname']
        self.ui.tableWidget.setRowCount(len(layer_list) + 1)
        self.ui.tableWidget.setColumnCount(len(step_list) + 1)
        # self.ui.tableWidget.setStyleSheet('QHeaderView::section{background:rgb(154,218,218);}')
        item = QtGui.QTableWidgetItem()
        item.setText(u"层别|STEP")
        self.ui.tableWidget.setItem(0, 0, item)
        self.ui.tableWidget.setHorizontalHeaderItem(0, item)
        self.ui.tableWidget.setVerticalHeaderItem(0, item)
        dic_color = {}
        for i, cur_step in enumerate(step_list, 1):
            item = QtGui.QTableWidgetItem()
            item.setText(str(cur_step))
            brush = QtGui.QBrush(QtGui.QColor(172, 172, 172))
            brush.setStyle(QtCore.Qt.SolidPattern)
            item.setBackground(brush)
            self.ui.tableWidget.setItem(0, i, item)
            # dic_color[i] = brush

            item = QtGui.QTableWidgetItem()
            item.setText(str(cur_step))
            # if i == 2:
            #     brush = QtGui.QBrush(QtGui.QColor(253, 199, 77))
            #     brush.setStyle(QtCore.Qt.SolidPattern)
            #     item.setForeground(brush)
            #     item.setBackground(brush)
            #     item.setBackgroundColor(QtGui.QColor(253, 199, 77))
            self.ui.tableWidget.setHorizontalHeaderItem(i, item)
            # item = QtWidgets.QTableWidgetItem()
            # brush = QtGui.QBrush(QtGui.QColor(76, 140, 255))
            # brush.setStyle(QtCore.Qt.SolidPattern)
            # item.setForeground(brush)
            # self.tableWidget.setHorizontalHeaderItem(6, item)

        # self.ui.tableWidget.setStyleSheet('QHeaderView::section{background:rgb(172, 172, 172);}')
        # self.ui.tableWidget.horizontalHeader().setStyleSheet('QHeaderView::section{background:rgb(172, 172, 172);}')
        # self.ui.tableWidget.verticalHeader().setStyleSheet('QHeaderView::section{background:rgb(255, 255, 255);}')
        # self.ui.tableWidget.verticalHeader().setStyleSheet("""QHeaderView::section:horizontal{border: none;}""")
        self.ui.tableWidget.setStyleSheet("""QTableView QTableCornerButton::section
        {background-color:rgb(224, 238, 255);
        color:black;
        border: 1px solid rgb(111, 156, 207);}""")
        btn = self.ui.tableWidget.findChild(QtGui.QAbstractButton)
        btn.setText(u"全选")
        btn.setObjectName("corner_btn")
        btn.installEventFilter(self)        
        

        # myvHeader = QHeaderView(Qt.Horizontal, self.ui.tableWidget, dic_color)
        # self.ui.tableWidget.setHorizontalHeader(myvHeader)
        # dic_color = {0: Qt.red,
        #              1: Qt.yellow,
        #              2: Qt.blue, }
        dic_color = {}
        for i, layer in enumerate(layer_list, 1):
            item = QtGui.QTableWidgetItem()
            item.setText(str(layer))
            brush = QtGui.QBrush(QtGui.QColor(154, 218, 218))
            dic_color[i] = QtGui.QColor(154, 218, 218)

            if job_matrix['gROWcontext'][i - 1] == 'board':
                if job_matrix['gROWlayer_type'][i - 1] == 'silk_screen':
                    brush = QtGui.QBrush(QtGui.QColor('white'))
                    dic_color[i] = QtGui.QColor('white')
                elif job_matrix['gROWlayer_type'][i - 1] == 'solder_paste':
                    brush = QtGui.QBrush(QtGui.QColor(255, 255, 206))
                    dic_color[i] = QtGui.QColor(255, 255, 206)

                elif job_matrix['gROWlayer_type'][i - 1] == 'drill':
                    brush = QtGui.QBrush(QtGui.QColor(155, 181, 191))
                    dic_color[i] = QtGui.QColor(155, 181, 191)
                elif job_matrix['gROWlayer_type'][i - 1] == 'signal':
                    brush = QtGui.QBrush(QtGui.QColor(253, 199, 77))
                    dic_color[i] = QtGui.QColor(253, 199, 77)
                elif job_matrix['gROWlayer_type'][i - 1] == 'solder_mask':
                    brush = QtGui.QBrush(QtGui.QColor(0, 165, 124))
                    dic_color[i] = QtGui.QColor(0, 165, 124)

                elif job_matrix['gROWlayer_type'][i - 1] == 'rout':
                    brush = QtGui.QBrush(QtGui.QColor(217, 217, 217))
                    dic_color[i] = QtGui.QColor(217, 217, 217)

            item.setBackground(brush)
            self.ui.tableWidget.setItem(i, 0, item)
            item = QtGui.QTableWidgetItem()
            item.setText(str(layer))
            # item.setForeground(brush)
            self.ui.tableWidget.setVerticalHeaderItem(i, item)

            for j, cur_step in enumerate(step_list, 1):
                item = QtGui.QTableWidgetItem()
                item.setBackground(brush)
                self.ui.tableWidget.setItem(i, j, item)
                if cur_step in self.pre_lock and layer in self.pre_lock[cur_step]:
                    self.add_lock(i=i, j=j)

        self.myvHeader = QHeaderView(Qt.Vertical, self.ui.tableWidget, dic_color)
        self.ui.tableWidget.setVerticalHeader(self.myvHeader)
        self.ui.tableWidget.installEventFilter(self)

        self.ui.tableWidget.resizeColumnsToContents()
        self.ui.tableWidget.resizeRowsToContents()
        return step_list, layer_list    

    def add_lock(self, i=None, j=None):
        """
        选择的单元格，添加禁止图标以及lock字样
        :return:
        """
        if i is None and j is None:
            for k in self.ui.tableWidget.selectedItems():
                # k.text()
                i = self.ui.tableWidget.row(k)
                j = self.ui.tableWidget.column(k)

                if i != 0 and j != 0:
                    lbp = QtGui.QLabel()
                    lbp.setPixmap(QtGui.QPixmap(r"%s/lock.ico" % self.cwd))
                    lbp.setAlignment(QtCore.Qt.AlignRight)
                    self.ui.tableWidget.setCellWidget(i, j, lbp)
                    self.ui.tableWidget.item(i, j).setText('lock')
                    k.setForeground(QtGui.QBrush(QtGui.QColor('red')))
        else:
            if i != 0 and j != 0:
                lbp = QtGui.QLabel()
                lbp.setPixmap(QtGui.QPixmap(r"%s/lock.ico" % self.cwd))
                lbp.setAlignment(QtCore.Qt.AlignRight)
                self.ui.tableWidget.setCellWidget(i, j, lbp)
                self.ui.tableWidget.item(i, j).setText('lock')
                self.ui.tableWidget.item(i, j).setForeground(QtGui.QBrush(QtGui.QColor('red')))

    def add_unlock(self):
        """
        选择的单元格，添加解锁图标以及pass字样
        :return:
        """
        for k in self.ui.tableWidget.selectedItems():
            i = self.ui.tableWidget.row(k)
            j = self.ui.tableWidget.column(k)
            if i != 0 and j != 0:
                if str(k.text()) == 'lock':
                    lbp = QtGui.QLabel()
                    lbp.setPixmap(QtGui.QPixmap(r"%s/pass.ico" % self.cwd))
                    lbp.setAlignment(QtCore.Qt.AlignRight)
                    self.ui.tableWidget.setCellWidget(i, j, lbp)
                    self.ui.tableWidget.item(i, j).setText('pass')
                    k.setForeground(QtGui.QBrush(QtGui.QColor(104, 166, 230)))

    def clear_pass_labels(self, row_num, column_num):
        i = row_num
        j = column_num
        current_text = self.ui.tableWidget.item(i, j).text()
        cur_cellWidget = self.ui.tableWidget.cellWidget(i, j)
        # # === cur_cellwidget 非None 则认为此单元格有图片 <PyQt4.QtGui.QLabel object at 0x0426DC90>
        # isinstance() 可以用来判断类型，暂时未用，
        # # === TODO 暂时不能知此单元格中图片是锁定还是解锁，可以根据size判断'lock' (10，10)  'pass' (16,17)
        if cur_cellWidget and str(current_text) in ['pass']:
            self.ui.tableWidget.item(i, j).setText('')
            lbp = QtGui.QLabel()
            lbp.setAlignment(QtCore.Qt.AlignRight)
            self.ui.tableWidget.setCellWidget(i, j, lbp)

    def selectrows_column(self):
        """
        选择标题行列时，扩展选择整行或整列
        :return:
        """
        QtCore.QObject.disconnect(self.ui.tableWidget, QtCore.SIGNAL('itemSelectionChanged()'),
                                  self.selectrows_column)

        for k in self.ui.tableWidget.selectedItems():
            # k.text()
            i = self.ui.tableWidget.row(k)
            j = self.ui.tableWidget.column(k)
            if i == 0 and j == 0:
                break
            else:
                if i == 0:
                    # self.ui.tableWidget.selectColumn(j)
                    for row in range(self.ui.tableWidget.rowCount()):
                        self.ui.tableWidget.setItemSelected(self.ui.tableWidget.item(row, j), True)

                if j == 0:
                    for col in range(self.ui.tableWidget.columnCount()):
                        self.ui.tableWidget.setItemSelected(self.ui.tableWidget.item(i, col), True)

                    # self.ui.tableWidget.selectRow(i)
        QtCore.QObject.connect(self.ui.tableWidget, QtCore.SIGNAL('itemSelectionChanged()'), self.selectrows_column)

    def selectcell(self, item):
        """
        选择标题行列时，扩展选择整行或整列
        :return:
        """
        print 'item'
        # if item.column() != 0:
        #     return
        QtCore.QObject.disconnect(self.ui.tableWidget, QtCore.SIGNAL('itemEntered(QTableWidgetItem*)'), self.selectcell)

        # print 'select', self.ui.tableWidget.selectedItems()
        for k in self.ui.tableWidget.selectedItems():
            print k.text()
            i = self.ui.tableWidget.row(k)
            j = self.ui.tableWidget.column(k)
            if i == 0 and j == 0:
                break
            else:
                if i == 0:
                    # self.ui.tableWidget.selectColumn(j)
                    for row in range(self.ui.tableWidget.rowCount()):
                        self.ui.tableWidget.setItemSelected(self.ui.tableWidget.item(row, j), True)
                        print 'xxxxxxxxxxxx'
                if j == 0:
                    for col in range(self.ui.tableWidget.columnCount()):
                        self.ui.tableWidget.setItemSelected(self.ui.tableWidget.item(i, col), True)
                        print 'cccccccccc'
        QtCore.QObject.connect(self.ui.tableWidget, QtCore.SIGNAL('itemEntered(QTableWidgetItem*)'), self.selectcell)

        # print self.ui.tableWidget.isItemSelected(item)
        # # print self.ui.tableWidget.setMouseTracking()
        # # if not self.ui.tableWidget.isItemSelected(item):
        # #     return
        # print 'item',item
        # print 'row',item.row(),'col',item.column(),'text',item.text()


    def selectcell2(self, item):
        """
        选择标题行列时，扩展选择整行或整列
        :return:
        """
        print 'item2',item
        print 'row',item.row(),'col',item.column(),'text',item.text()
        
    def get_rename_job_previs(self, user, authority_name):
        sql = "select * from hdi_engineering.incam_user_authority "
        self.check_data_info = conn.SELECT_DIC(dbc_m, sql)
        for dic_info in self.check_data_info:
            if str(dic_info["user_id"]) == user:
                if dic_info["Authority_Name"] == authority_name and \
                   dic_info["Authority_Status"] ==u"是":
                    return True
                
        return False

    def save_ui(self):
        """
        保存界面锁定数据
        :return:
        """
        job_lock = {}
        unlock_layers = []
        unlock_steps = []
        for j, cur_step_name in enumerate(self.step_list, 1):
            for i, cur_layer_name in enumerate(self.layer_list, 1):
                current_text = self.ui.tableWidget.item(i, j).text()
                cur_cellWidget = self.ui.tableWidget.cellWidget(i, j)
                # # === cur_cellwidget 非None 则认为此单元格有图片 <PyQt4.QtGui.QLabel object at 0x0426DC90>
                # # === TODO 暂时不能知此单元格中图片是锁定还是解锁，可以根据size判断'lock' (10，10)  'pass' (16,17)
                # if cur_cellWidget and str(current_text) in ['lock', 'pass'] :
                #     print current_text
                #     if cur_cellWidget.pixmap().size() == QtCore.QSize(16, 17):
                #         print 'check_pass'
                #     elif cur_cellWidget.pixmap().size() == QtCore.QSize(10, 10):
                #         print 'check_lock'
                #     else:
                #         print i, j, cur_cellWidget  # <PyQt4.QtGui.QLabel object at 0x02DAFFA8>
                #         print cur_cellWidget.pixmap().toImage()  # 获取Qlabel图片
                #         print cur_cellWidget.pixmap()  # <PyQt4.QtGui.QImage object at 0x02DA7110>
                #         print cur_cellWidget.pixmap().size()  # <PyQt4.QtGui.QPixmap object at 0x02D55FB8>

                if current_text == 'lock':
                    # print cur_cellWidget
                    # print cur_cellWidget.type()
                    if cur_step_name not in job_lock:
                        job_lock[cur_step_name] = [cur_layer_name]
                    else:
                        job_lock[cur_step_name].append(cur_layer_name)
                        
                if current_text == 'pass':
                    if cur_layer_name not in unlock_layers:                        
                        unlock_layers.append(cur_layer_name)
                    
                    if cur_step_name not in unlock_steps:                        
                        unlock_steps.append(cur_step_name)
        
        if self.ui.lock_panelization.isChecked():
            if "unlock_panelization_status" in job_lock:
                del job_lock["unlock_panelization_status"]            
            job_lock["lock_panelization_status"] = ["yes"]
        else:
            if "lock_panelization_status" in job_lock:
                del job_lock["lock_panelization_status"]
            job_lock["unlock_panelization_status"] = ["yes"]
            
        M = DiffDict(job_lock, self.pre_lock)
        lock_add = M.get_added()
        lock_change = M.get_changed()
        unlock = M.get_removed()
        time_key = int(time.time())
        time_form = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_key))

        o_lock_add, o_unlock = self.separate_lock_changes(lock_change)
        lock_add += o_lock_add
        unlock += o_unlock
        #
        log_dict = {time_key: {'user': self.cam_user, 'lock_add': lock_add, 'unlock': unlock, 'time': time_form}}
        pre_log_dict = self.read_file('job_lock_log.json')
        # === TODO Freeze功能有Bug，Freeze之后，在未更改的情况下，始终始终有更改
        # === Freeze会保存资料，增加资料是否保存的提醒
        # if len(lock_add) + len(unlock) > 0:
        #     # === 检查料号是否更改，有更改则需要保存 ===
        #     change_check_stauts = self.change_check()
        #     if not change_check_stauts:
        #         return False
        # === 增加审批流程，如果UI unlock有值，则需要在工程管理系统中审批 ===        
        if len(unlock) > 0 and not self.get_rename_job_previs(self.cam_user, u"解锁内外层"):
            self.showMinimized()
            # jstr1 = '<span><table border="1" style="background-color: #ffffff; color: #000000; font-size: 12px">'
            # jstr1 += '<caption>资料锁定有变更,时间：%s,CAM用户:%s明细如下</caption>' % (time_form, self.cam_user)
            jstr1 = '<span>资料解锁.时间:%s,CAM用户:%s明细如下</span>' % (time_form, self.cam_user)
            jstr1 += '<span><table border="1" style="background-color: #ffffff; color: #000000; font-size: 12px">'
            jstr1 += '<tr><th>操作</th><th>相关step</th><th>相关层别</th></tr>'
            if len(unlock) > 0:
                ctr1 = ''
                for s_i in unlock:
                    ctr1 += '<tr><td>解锁</td><td>%s</td><td>%s</td></tr>' % (
                    s_i['step'], str(s_i['layers']).replace(',', '.').replace('\'', ''))
                jstr1 += ctr1
            jstr1 += '</table></span>'
            # jstr1 = jstr1.replace("unlock-panel", "解锁拼版").replace("lock-panel", "锁定拼版")
            # print jstr1
            # === 发送评审请求 ===
            submitData = {
                'site': u'HDI板事业部',
                'job_name': self.job_name,
                'pass_tpye': 'CAM',
                'pass_level': 8,
                'assign_approve': '44813|44566|44926|44024|68027|84310|83288|65389|%s' % self.inner_checker,
                'pass_title': u"%s" % jstr1,
            }
            Dialog = AboutDialog(submitData['pass_title'], cancel=True, appCheck=True, appData=submitData,
                                 style='other')
            Dialog.exec_()
            # endregion
            print Dialog.selBut
            self.showNormal()
            # --根据审批的结果返回值
            if Dialog.selBut == 'cancel':
                return False
            if Dialog.selBut == 'x':
                return False
            # 结果为OK时，则继续运行
            # if Dialog.selBut == 'ok':
            #     return True
        
        # 解锁时备份解锁的层 20240108 by lyh
        # 翟鸣 通知暂时不备份 20240110 by lyh
        #job = gClasses.Job(self.job_name)
        #matrix_info = job.matrix.getInfo()        
        #day_time = time.strftime("%m%d", time.localtime(time.time()))
        #dic_bf_layer = {}
        #for layer in unlock_layers:
            #if "_unlock_bf" in layer:
                #continue
            #stepname = matrix_info["gCOLstep_name"][0]
            #step = gClasses.Step(job, stepname)
            #step.open()
            #if step.isLayer(layer) and dic_bf_layer.get(layer, None) is None:                    
                #for i in [""] + range(1, 10):
                    #if not i:
                        #bf_layer = layer+"_unlock_bf{0}".format(day_time)
                    #else:
                        #bf_layer = layer+"_unlock_bf{0}_{1}".format(day_time, i)
                    #if not step.isLayer(bf_layer):                        
                        #dic_bf_layer[layer] = bf_layer
                        #break
                        
        #if dic_bf_layer:
            #self.hide()
            #for layer in unlock_layers:
                #stepname = matrix_info["gCOLstep_name"][0]
                #step = gClasses.Step(job, stepname)
                #step.open()
                #if step.isLayer(layer):
                    #if step.isLayer(layer+"+1"):
                        #step.removeLayer(layer+"+1")
                    #index = matrix_info["gROWname"].index(layer)
                    #row = matrix_info["gROWrow"][index]
                    #step.COM("matrix_dup_row,job={0},matrix=matrix,row={1}".format(self.job_name, row))
                    #if step.isLayer(layer+"+1"):
                        #step.COM("matrix_rename_layer,job={0},matrix=matrix,layer={1},new_name={2}".format(self.job_name, layer+"+1", dic_bf_layer[layer]))
                        #matrix_info = job.matrix.getInfo()
            
            #for key in unlock_steps:                
                #if key not in ["unlock_panelization_status", "lock_panelization_status"]:                    
                    #job_lock[key] = job_lock.get(key, []) + dic_bf_layer.values()
                    
            #job.save(1)
            #self.show()
        # TODO 由于Freeze的Bug，暂时不用以下方法
        # self.freeze_layers_by_ui(log_dict)
        # --将收集到的数据以json的格式写入数据库中-写锁记录
        self.getDATA.uploadLock_Layers(self.job_name.split("-")[0], lockJson=job_lock, userId=self.userID)
        # === 测试阶段，暂时退出 ===
        # # 将收集到的数据以json的格式写入user/
        self.write_file(job_lock,desfile=self.job_lock)
        log_dict.update(pre_log_dict)
        
        
        self.getDATA.uploadLock_Layers(self.job_name.split("-")[0], logJson=log_dict, userId=self.userID)        
        self.write_file(log_dict, 'job_lock_log.json')
        self.ui.label_tips.setText(u'%s 执行已生效，详细请查看Log' % time_form)
        self.ui.label_tips.setStyleSheet("color:rgb(82,176,136)")
        self.showLog()        
        self.refresh_ui()
        #self.hide()
        #os.system("python {0}".format(sys.argv[0]))        
        app.quit()

    def change_check(self):
        """
        判断资料是否更改，并show出更改给用户确认
        :return:
        """
        Save = Job_Save_log(self.job_name)
        # {'panel': ['inn']}
        # create_dict
        # {'cou1': ['123'], 'hct-coupon': ['123'], 'set': ['123'], 'b2-3': ['123'], 'drill_test_coupon': ['123'],
        #  'edit': ['123'], 'icg': ['123'], 'sm4-coupon': ['123'], 'plus1-floujie': ['123'], 'drl': ['123'],
        #  'xllc-coupon': ['123'], 'dzd_cp': ['123'], 'panel': ['inn'], 'net': ['123'], 'orig': ['123']}

        change_dict, del_dict, create_dict = Save.get_job_changes()

        if change_dict or del_dict or create_dict:
            mesg1 = u'即将保存料号：%s,有如下更改，是否继续：' % self.job_name
            msg1 = """
                    <p>
                        <span style="background-color:#E53333;color:#fff;font-size:16px"><strong>%s<strong></span>                    
                    </p>""" % mesg1

            jstr1 = u'<span><table border="1" style="background-color: #ffffff; color: #000000; font-size: 12px">'
            jstr1 += u'<tr><th>操作</th><th>相关step</th><th>相关层别</th></tr>'

            if change_dict:
                ctr1 = ''
                for s_i in change_dict:
                    ctr1 += u'<tr><td>变更</td><td>%s</td><td>%s</td></tr>' % (
                        s_i, str(change_dict[s_i]))
                jstr1 += ctr1
            if del_dict:
                ctr1 = ''
                for s_i in del_dict:
                    ctr1 += u'<tr><td>删除</td><td>%s</td><td>%s</td></tr>' % (
                        s_i, str(del_dict[s_i]))
                jstr1 += ctr1
            if create_dict:
                ctr1 = ''
                for s_i in create_dict:
                    ctr1 += u'<tr><td>新增</td><td>%s</td><td>%s</td></tr>' % (
                        s_i, str(create_dict[s_i]))
                jstr1 += ctr1
            jstr1 += '</table></span>'
            msg2 = jstr1
            print msg2

            Dialog = AboutDialog(msg1, Msg2=msg2, style='other', cancel=True, )
            Dialog.exec_()
            if Dialog.selBut == 'cancel':
                return False
            if Dialog.selBut == 'x':
                return False
        return True

    def freeze_layers_by_ui(self, log_dict):
        """
        根据界面，对料号中的层别进行freeze
        :param log_dict:
        :return:
        """
        # === 以下语句，仅在incam下生效，Genesis不适用 ===
        # === TODO 保存料号,并写保存Log ===
        Save = Job_Save_log(self.job_name)
        change_dict, del_dict, create_dict = Save.get_job_changes()
        Save.write_job_save_log(change_dict, del_dict, create_dict, self.userDir)
        # === 循环step 在job_lock中的锁定，不在job_lock中的不锁定，
        # === 或者增加锁定状态查询，每个step中每个层别，当前状态是锁定还是解锁。
        # print log_dict
        # === 仅一个key
        time_key = log_dict.keys()[0]
        changes = log_dict[time_key]
        check_num = len(changes['lock_add']) + len(changes['unlock'])
        # print check_num

        for cur_lock_change in changes['lock_add']:
            current_step = cur_lock_change['step']
            for cur_layer in cur_lock_change['layers']:
                # str1 = '锁定step:%s 层别：%s' % (current_step, cur_layer)
                str1 = 'Lock Step:%s Layer：%s' % (current_step, cur_layer)
                print str1.decode()
                self.GEN.COM('freeze_ent,job_name=%s,ent=%s,parent=%s,ent_type=layer,mode=freeze' % (
                    self.job_name, cur_layer, current_step))
                self.GEN.COM('save_job,job=%s,override=no,skip_upgrade=no,upgradeToInCAMPro=no' % self.job_name)
                self.GEN.COM('check_inout,job=%s,mode=in,ent_type=job' % self.job_name)
                self.GEN.COM('check_inout,job=%s,mode=out,ent_type=job' % self.job_name)

        for cur_lock_change in changes['unlock']:
            current_step = cur_lock_change['step']
            for cur_layer in cur_lock_change['layers']:
                # str1 = '解锁step:%s 层别：%s' % (current_step, cur_layer)
                str1 = 'Unlock step:%s Layer:%s' % (current_step, cur_layer)
                print str1.decode()
                self.GEN.COM('check_inout,job=%s,mode=out,ent_type=job' % self.job_name)
                self.GEN.COM('freeze_ent,job_name=%s,ent=%s,parent=%s,ent_type=layer,mode=unfreeze' % (
                    self.job_name, cur_layer, current_step))
                self.GEN.COM('save_job,job=%s,override=no,skip_upgrade=no,upgradeToInCAMPro=no' % self.job_name)

        self.GEN.COM('save_job,job=%s,override=no,skip_upgrade=no,upgradeToInCAMPro=yes' % self.job_name)
        self.GEN.COM('check_inout,job=%s,mode=in,ent_type=job' % self.job_name)
        self.GEN.COM('check_inout,job=%s,mode=out,ent_type=job' % self.job_name)

    def separate_lock_changes(self, ip_lock_change):
        """
        锁定变更，细化为锁定与解锁
        :param ip_lock_change: [{step:'',layers:"['','']->['',]"(字符串类型)}]
        :return:
        """
        lock_add = []
        unlock = []
        for cur_lock_change in ip_lock_change:
            current_step = cur_lock_change['step']
            before_layers = ast.literal_eval(cur_lock_change['layers'].split(' -> ')[0])
            after_layers = ast.literal_eval(cur_lock_change['layers'].split(' -> ')[1])
            # print before_layers
            # print after_layers
            # === 对比，新增与减少 （锁定与解锁）
            lmode = DiffArray(after_layers, before_layers)
            add_lock_layers = lmode.get_list_added()
            unlock_layers = lmode.get_list_remove()
            if len(add_lock_layers) > 0:
                lock_add.append({'layers': add_lock_layers, 'step': current_step})
            if len(unlock_layers) > 0:
                unlock.append({'layers': unlock_layers, 'step': current_step})
        return lock_add, unlock

    def write_file(self, job_lock, desfile='job_lock.json'):
        """
        用json把参数字典直接写入user文件夹中的job_lock.json 2022.04.11 文件夹前加上料号名
        json_str = json.dumps(self.parm)将字典dump成string的格式
        :return:
        :rtype:
        """
        # 将收集到的数据以json的格式写入user/param
        stat_file = os.path.join(self.userDir, desfile)
        fd = open(stat_file, 'w')
        json.dump(job_lock, fd, ensure_ascii=False, indent=4, separators=(', ', ': '), sort_keys=True)
        fd.close()

    def read_file(self, sour_file='job_lock.json'):
        """
        用json从user文件夹中的job_lock.json中读取字典 2022.04.11 文件夹前加上料号名
        :return:
        :rtype:
        """
        json_dict = {}
        stat_file = os.path.join(self.userDir, sour_file)
        if os.path.exists(stat_file):
            fd = open(stat_file, 'r')
            json_dict = json.load(fd, encoding='utf8')
            fd.close()

        conver_dict = unicode_convert(json_dict)
        return conver_dict


class Job_Save_log(object):
    def __init__(self, job_name=None):
        if job_name is None:
            job_name = os.environ.get('JOB', None)
        self.job_name = job_name
        self.GEN = genCOM_26.GEN_COM()

    def get_job_changes(self):
        change_dict = {}
        del_dict = {}
        create_dict = {}
        getData = self.GEN.INFO("-t job -e %s -d CHANGES" % self.job_name)
        # --循环所有保存信息内容
        reName = False
        # === Modify 相关 ===
        Modif = False
        lineExists = False
        modifDetail = ""
        # === Delete 相关 ===
        Delete = False
        dlineExists = False
        delDetail = ""
        # === Create 相关 ===
        Create = False
        clineExists = False
        createDetail = ""
        for info in getData:
            # --去除结尾的回车及Tab
            info.strip()

            if 'Created Entities' in info:
                Create = True
            if Create is True and clineExists is False and '----' in info:
                clineExists = True
                continue
            if clineExists is True and '----' in info:
                Create = False
                continue

            # --当已进入'Modified Entities'区域信息时，
            if 'Modified Entities' in info:
                reName = False
                Modif = True
                continue

            # --进入'Modified Entities'区域信息时，下面的 ‘----’
            if Modif is True and lineExists is False and '----' in info:
                lineExists = True
                continue
            # --当已进入'Modified Entities'区域，但又出现“----”默认跳出了'Modified Entities'区域
            if lineExists is True and '----' in info:
                Modif = False
                continue

            if 'Deleted Entities' in info:
                Delete = True
            if Delete is True and dlineExists is False and '----' in info:
                dlineExists = True
                continue
            if dlineExists is True and '----' in info:
                Delete = False
                continue
            repInfo = info.replace(' ', '')  # --分割后的数据，类似step=net,layer=l2,relation=relation

            # --当在'Created Entities'区域检测是否有修改的操作
            if Create is True and 'step=' in repInfo and 'ent_attributes' not in repInfo:
                createDetail += repInfo
                # --统计修改了哪几层，以便后面查看修改内容，还原现场用
                stepN = (repInfo.split(',')[0]).split('=')[1].replace('\n', '')
                if stepN not in create_dict:
                    create_dict[stepN] = []
                try:
                    layN = (repInfo.split(',')[1]).split('=')[1].replace('\n', '')
                    create_dict[stepN].append(layN)
                    # --保证无重复的数组元素
                    create_dict[stepN] = list(set(create_dict[stepN]))
                except:
                    pass
            # --当在'Modified Entities'区域检测(仅修改到了属性，可忽略)
            # if Modif is True and 'step=net' in repInfo and 'ent_attributes' not in repInfo:
            if Modif is True and 'step=' in repInfo and 'ent_attributes' not in repInfo:
                modifDetail += repInfo
                # --统计修改了哪几层，以便后面查看修改内容，还原现场用
                stepN = (repInfo.split(',')[0]).split('=')[1].replace('\n', '')
                if stepN not in change_dict:
                    change_dict[stepN] = []
                try:
                    layN = (repInfo.split(',')[1]).split('=')[1].replace('\n', '')
                    change_dict[stepN].append(layN)
                    change_dict[stepN] = list(set(change_dict[stepN]))
                    # --保证无重复的数组元素
                    # self.changeNetLay = list(set(self.changeNetLay))
                except:
                    pass

            # --当在'Deleted Entities'区域检测是否有修改的操作
            if Delete is True and 'step=' in repInfo:
                delDetail += repInfo
                # --统计修改了哪几层，以便后面查看修改内容，还原现场用
                stepN = (repInfo.split(',')[0]).split('=')[1].replace('\n', '')
                if stepN not in del_dict:
                    del_dict[stepN] = []
                try:
                    layN = (repInfo.split(',')[1]).split('=')[1].replace('\n', '')
                    del_dict[stepN].append(layN)
                    del_dict[stepN] = list(set(del_dict[stepN]))
                    # --保证无重复的数组元素
                    # self.changeNetLay = list(set(self.changeNetLay))
                except:
                    pass

        # --当修改内容不为空时
        if modifDetail != "":
            print change_dict
        if delDetail != "":
            print 'del_dict'
            print del_dict
        if createDetail != "":
            print 'create_dict'
            print create_dict
        return change_dict, del_dict, create_dict

    def write_job_save_log(self, create_dict, change_dict, del_dict, user_dir):

        cur_time = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime())

        str_modify = ["######## Modifier %s %s %s ########\n" % (self.job_name, 'lock_script', cur_time), ]
        # modify
        if change_dict:
            for index, s_i in enumerate(change_dict):
                if index == 0:
                    str_modify.append("Modified ==>> STEP --> %s LAYER --> %s\n" % (s_i, ','.join(change_dict[s_i])))

                else:
                    str_modify.append("              STEP --> %s LAYER --> %s\n" % (s_i, ','.join(change_dict[s_i])))
        # create
        if create_dict:
            for index, s_i in enumerate(create_dict):
                if index == 0:
                    str_modify.append("Created  ==>> STEP --> %s LAYER --> %s\n" % (s_i, ','.join(create_dict[s_i])))

                else:
                    str_modify.append("              STEP --> %s LAYER --> %s\n" % (s_i, ','.join(create_dict[s_i])))
        # del
        if del_dict:
            for index, s_i in enumerate(del_dict):
                if index == 0:
                    str_modify.append("Deleted  ==>> STEP --> %s LAYER --> %s\n" % (s_i, ','.join(del_dict[s_i])))
                else:
                    str_modify.append("              STEP --> %s LAYER --> %s\n" % (s_i, ','.join(del_dict[s_i])))
        if len(str_modify) > 1:
            desfile = 'save_log'
            stat_file = os.path.join(user_dir, desfile)
            fd = open(stat_file, 'a+')
            fd.writelines(str_modify)
            fd.close()


class DiffDict(object):
    """获取两个dict的差异"""

    def __init__(self, current, last):
        self.current = current
        self.last = last
        self.set_current = set(current)
        self.set_last = set(last)
        self.intersect_keys = self.set_current & self.set_last

    def get_added(self):
        """current - 交集 = 新增的key"""
        added_keys = self.set_current - self.intersect_keys
        return [{'step': key, 'layers': self.current.get(key)} for key in added_keys]

    def get_removed(self):
        """last - 交集 = 减去的key"""
        removed_keys = self.set_last - self.intersect_keys
        return [{'step': key, 'layers': self.last.get(key)} for key in removed_keys
                if key not in ["lock_panelization_status", "unlock_panelization_status"]]

    def get_changed(self):
        """用交集中的key去两个dict中找出值不相等的"""
        changed_keys = set(o for o in self.intersect_keys if self.current.get(o) != self.last.get(o))
        return [{
            'step': key,
            'layers': '%s -> %s' % (self.last.get(key), self.current.get(key))
        } for key in changed_keys]


class DiffArray(object):
    """两个列表，求增加减少"""

    def __init__(self, current, last):
        self.current_list = current
        self.last_list = last
        # === 以下，在转换为set模式时，保持排序
        self.set_current_list = set(self.current_list)
        self.set_last_list = set(self.last_list)
        self.intersect_items = self.set_current_list.intersection(self.set_last_list)

    def get_list_added(self):
        return sorted(list(self.set_current_list - self.intersect_items), key=lambda x: self.current_list.index(x))

    def get_list_remove(self):
        return sorted(list(self.set_last_list - self.intersect_items), key=lambda x: self.last_list.index(x))


# # # # --程序入口
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MyApp()
    # myapp.get_job_matrix()
    myapp.show()
    sys.exit(app.exec_())
