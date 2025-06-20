#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:FpcOneKey.py
   @author:zl
   @time:2024/06/29 08:21
   @software:PyCharm
   @desc:
"""
import json
import os
import re
import sys
import time

import qtawesome
from qtawesome import icon_browser

import FpcOneKeyUI as ui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import res_rc
import genClasses as gen
import ZL_mysqlCon as zlmysql


class QaeOneKey(QMainWindow, ui.Ui_MainWindow):
    def __init__(self):
        super(QaeOneKey, self).__init__()
        self.setupUi(self)
        self.setdata()

    def setdata(self):
        self.jobname.setText(jobname)
        self.username.setText(user_name)
        # 开始检测
        self.exec_btn.setIcon(qtawesome.icon('msc.debug-start', color='white'))
        self.exec_btn.clicked.connect(self.ExecAllCheck)
        # 保存状态
        self.save_status_btn.setIcon(qtawesome.icon('fa.save', color='white'))
        self.save_status_btn.clicked.connect(self.SaveStatus)
        # 暂停脚本
        self.pause_btn.setIcon(qtawesome.icon('fa.pause-circle-o', color='white'))
        self.pause_btn.clicked.connect(self.PauseScript)
        # 退出
        self.exit_btn.setIcon(qtawesome.icon('mdi.exit-to-app', color='white'))
        self.exit_btn.clicked.connect(self.do_exit)
        # 关闭结果
        self.close_btn.setIcon(qtawesome.icon('fa.close', color='white'))
        self.close_btn.clicked.connect(self.close_table)
        # 窗口关闭事件
        self.closeEvent = self.closeEvent  # 重写closeevent
        self.dataHaveChange = False  # 数据是否有变动
        # 检查列表table表头和样式
        self.icon_run = qtawesome.icon('fa.play-circle', scale_factor=1, color='orange')
        self.icon_ok = qtawesome.icon('ei.ok-circle', scale_factor=1, color='#51cbac')
        self.icon_ng = qtawesome.icon('fa.warning', scale_factor=1, color='#b55090')
        self.icon_delall = qtawesome.icon('mdi.delete', scale_factor=1, color='red')
        self.icon_search1 = qtawesome.icon('fa.search', scale_factor=1, color='green')
        self.icon_search2 = qtawesome.icon('fa.search', scale_factor=1, color='brown')
        self.icon_search3 = qtawesome.icon('fa.search', scale_factor=1, color='blue')
        self.icon_del = qtawesome.icon('mdi.delete-circle-outline', scale_factor=1, color='#B54747')
        self.icon_empty = QIcon(QPixmap(''))
        header = ['key', '检测内容', '结果', '用户', '执行日期', '备注', '耗时']
        self.tableWidget.setColumnCount(len(header))
        self.tableWidget.setSortingEnabled(True)
        self.tableWidget.setColumnWidth(0, 80)
        self.tableWidget.setColumnWidth(1, 320)
        self.tableWidget.setColumnWidth(2, 80)
        self.tableWidget.setColumnWidth(3, 150)
        self.tableWidget.setColumnWidth(4, 220)
        self.tableWidget.setColumnWidth(5, 120)
        self.tableWidget.setColumnWidth(6, 120)
        self.tableWidget.setHorizontalHeaderLabels(header)
        self.tableWidget.setColumnHidden(0, True)  # 隐藏第0列
        self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableWidget.customContextMenuRequested.connect(self.DoScrClickMouseRight)
        self.tableWidget.currentItemChanged.connect(self.DoTableScrChange)
        self.tableWidget.doubleClicked.connect(self.DoShowMore)
        self.tableWidget.itemClicked.connect(self.DoTableResuChange)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget.setStyleSheet('''
                  /* gridline-color:#bbd2ee;  */      /*表格中的网格线条颜色*/
                   selection-color:#000000;    /*鼠标选中时前景色：文字颜色*/
                   selection-background-color:#fcf0bc;   /*鼠标选中时背景色*/   
               ''')
        # 初始化table数据
        self.table_render()
        # 数量
        self.DoChangeTextNumber()
        self.tabWidget.setStyleSheet('font-size:9pt;')
        self.textEdit_info.setReadOnly(True)
        self.textEdit_result.setReadOnly(True)
        self.tabWidget.setCurrentIndex(2)
        header = ['job', 'step', 'layer', '位置', 'checklist']
        self.tableWidget_more_result.setColumnCount(len(header))
        self.tableWidget_more_result.setHorizontalHeaderLabels(header)
        self.tableWidget_more_result.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget_more_result.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget_more_result.setFocusPolicy(Qt.NoFocus)
        self.tableWidget_more_result.itemClicked.connect(self.DoTableResuChange)
        self.tableWidget_more_result.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget_more_result.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        header = ['料号', '检查项', '执行人', '日期', '结果', '备注']
        self.tableWidget_more_history.setColumnCount(len(header))
        self.tableWidget_more_history.setHorizontalHeaderLabels(header)
        self.tableWidget_more_history.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget_more_history.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget_more_history.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget_more_history.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget_more_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.splitter.setSizes([800, 160])
        # status bar
        # self.timer = QTimer(self)
        # self.timer.start(1000)
        # self.timer.timeout.connect(self.showStatusbarMsg)
        # self.showStatusbarMsg()
        # 窗口居中
        cent_x = (app.desktop().width() - self.geometry().width()) / 2
        cent_y = (app.desktop().height() - self.geometry().height()) / 2
        # self.move(cent_x, cent_y)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        # self.label_logo.setScaledContents(True)
        self.setStyleSheet('#label_logo{color:#eee;border-radius:5px;background-color:#0081a6;} QPushButton{font:9pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')
        # self.setStyleSheet('QPushButton{font:9pt;background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')

    def table_render(self):
        self.scr_dict = {}
        Sql = "select ScriptKey,ScriptPath,ScriptInfo,ScriptLevel,ScriptName,ScriptClass,TestUser from fpc_onekey_config"
        cursor.execute(Sql)
        tmp = cursor.fetchall()
        alldata = []
        for line in tmp:
            if line[6] and line[6] != '':
                if line[6] == user_name:
                    alldata.append(line)
            else:
                alldata.append(line)

        self.tableWidget.setRowCount(len(alldata))
        # List = ['key', '项目', '级别', '检测内容', '结果', '执行日期', '备注', '用户', '脚本用时']
        # List = ['key', '项目', '级别', '检测内容', '结果', '用户', '执行日期', '备注', '脚本用时']
        self.scr_list = []
        row = 0
        for line in alldata:
            mScriptKey = line[0]
            mScriptPath = line[1]
            mScriptInfo = line[2]
            mScriptLevel = line[3]
            mScriptName = line[4]
            mScriptClass = '[' + line[5] + ']'
            self.scr_list.append(mScriptKey)
            self.scr_dict[mScriptKey] = {}
            self.scr_dict[mScriptKey]['path'] = mScriptPath
            self.scr_dict[mScriptKey]['info'] = mScriptInfo
            self.scr_dict[mScriptKey]['name'] = mScriptName
            self.scr_dict[mScriptKey]['level'] = mScriptLevel
            self.scr_dict[mScriptKey]['lass'] = mScriptClass
            item_0 = QTableWidgetItem(mScriptKey)
            item_1 = QTableWidgetItem(mScriptName)
            item_2 = QTableWidgetItem('')
            item_3 = QTableWidgetItem('')
            item_4 = QTableWidgetItem('')
            item_5 = QTableWidgetItem('')
            item_6 = QTableWidgetItem('')
            item_2.setTextAlignment(Qt.AlignCenter)
            item_3.setTextAlignment(Qt.AlignCenter)
            item_4.setTextAlignment(Qt.AlignCenter)
            item_5.setTextAlignment(Qt.AlignCenter)
            item_6.setTextAlignment(Qt.AlignCenter)

            self.tableWidget.setItem(row, 0, item_0)
            self.tableWidget.setItem(row, 1, item_1)
            self.tableWidget.setItem(row, 2, item_2)
            self.tableWidget.setItem(row, 3, item_3)
            self.tableWidget.setItem(row, 4, item_4)
            self.tableWidget.setItem(row, 5, item_5)
            self.tableWidget.setItem(row, 6, item_6)

            row += 1

        jobJsonPath = 'D:/scripts/oneKey/onekey_file/' + jobname
        if os.path.exists(jobJsonPath):
            topDict = self.json_to_dict(jobJsonPath)
            # topDict = {}
            # List = ['key', '项目', '级别', '检测内容', '结果', '执行日期', '备注', '用户', '脚本用时']
            # List = ['key', '项目', '级别', '检测内容', '结果', '用户', '执行日期', '备注', '脚本用时']
            for row in range(self.tableWidget.rowCount()):
                key = self.tableWidget.item(row, 0).text()
                if key in topDict.keys():
                    self.tableWidget.item(row, 2).setText(topDict[key]['result'])
                    self.tableWidget.item(row, 3).setText(topDict[key]['username'])
                    self.tableWidget.item(row, 4).setText(topDict[key]['runndate'])
                    self.tableWidget.item(row, 5).setText(topDict[key]['mark'])
                    self.tableWidget.item(row, 6).setText(topDict[key]['usetime'])

                    if topDict[key]['result'] == 'OK':
                        self.tableWidget.item(row, 2).setBackground(QColor('#51cbac'))
                    elif topDict[key]['result'] == 'NG':
                        self.tableWidget.item(row, 2).setBackground(QColor('#b55090'))
        # 读取历史记录 - more模块
        self.history_dict = {}
        Sql = "select h_job,h_user,h_item,h_key,h_result,h_rundate,h_usetime,h_mark from fpc_onekey_history where h_job = '%s'" % jobname
        cursor.execute(Sql)
        alldata = cursor.fetchall()
        for line in alldata:
            h_job = line[0]
            h_user = line[1]
            h_item = line[2]
            h_key = line[3]
            h_result = line[4]
            h_rundate = line[5]
            h_usetime = line[6]
            h_mark = line[7]
            if h_key not in self.history_dict.keys():
                self.history_dict[h_key] = []
                # List = ['料号', '检查项', '执行人', '日期', '结果', '备注']
            self.history_dict[h_key].append([h_job, h_item, h_user, h_rundate, h_result, h_mark])

        # 脚本结果 - more模块
        self.result_dict = {}
        for k in self.scr_list:
            self.result_dict[k] = {}
            self.result_dict[k]['text'] = ''
            self.result_dict[k]['list'] = []

    # 执行数量
    def DoChangeTextNumber(self):
        """刷新数量"""
        ok_num = 0
        ng_num = 0
        norun_num = 0
        for row in range(0, self.tableWidget.rowCount()):
            hResult = self.tableWidget.item(row, 2).text()
            if hResult == 'OK':
                ok_num += 1
            elif hResult == 'NG':
                ng_num += 1
            else:
                norun_num += 1
        self.unfinished_label.setText("<font style='color:red;font-weight:bold;'>%s</font>" % norun_num)
        self.finished_label.setText("<font style='color:green;font-weight:bold;'>%s</font>" % (ok_num + ng_num))

    def DoScrClickMouseRight(self, position):
        # 弹出菜单
        popMenu = QMenu()
        runLocal = QAction("单项运行", icon=self.icon_run)
        runIsOK = QAction("手动确认OK", icon=self.icon_ok)
        runIsNG = QAction("手动确认NG", icon=self.icon_ng)
        runEmpty = QAction('清空状态', icon=self.icon_del)
        runResult = QAction('查看结果', icon=self.icon_search1)
        runHistory = QAction('查看历史记录', icon=self.icon_search2)
        runInfo = QAction('查看检测说明', icon=self.icon_search3)

        if self.tableWidget.itemAt(position):
            popMenu.addAction(runLocal)
            popMenu.addSeparator()
            popMenu.addAction(runIsOK)
            popMenu.addSeparator()
            popMenu.addAction(runIsNG)
            popMenu.addSeparator()
            popMenu.addAction(runEmpty)
            popMenu.addSeparator()
            popMenu.addAction(runResult)
            popMenu.addAction(runHistory)
            popMenu.addAction(runInfo)
        action = popMenu.exec_(self.tableWidget.mapToGlobal(position))
        row_num = -1
        for i in self.tableWidget.selectionModel().selection().indexes():
            row_num = i.row()

        cur_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # 脚本执行时间
        if action == runLocal:  # 本地运行
            self.hide()
            self.DoRunOneScr()  # 运行单个脚本
            QApplication.processEvents()
            self.show()
        elif action == runIsOK:  # 手动确认ok
            # List = ['key', '项目', '级别', '检测内容', '结果', '执行日期', '备注', '用户', '脚本用时']
            text = '由%s手动确认OK' % user_name
            self.tableWidget.item(self.curScr_row, 4).setText('OK')
            self.tableWidget.item(self.curScr_row, 4).setBackground(QColor('#51cbac'))
            self.tableWidget.item(self.curScr_row, 5).setText(user_name)
            self.tableWidget.item(self.curScr_row, 6).setText(cur_time)
            self.tableWidget.item(self.curScr_row, 7).setText(text)
            self.tableWidget.item(self.curScr_row, 8).setText('0 秒')
        elif action == runIsNG:  # 手动确认ng
            text = '由%s手动确认NG' % user_name
            self.tableWidget.item(self.curScr_row, 4).setText('NG')
            self.tableWidget.item(self.curScr_row, 4).setBackground(QColor('#b55090'))
            self.tableWidget.item(self.curScr_row, 5).setText(user_name)
            self.tableWidget.item(self.curScr_row, 6).setText(cur_time)
            self.tableWidget.item(self.curScr_row, 7).setText(text)
            self.tableWidget.item(self.curScr_row, 8).setText('0 秒')
        elif action == runEmpty:  # 清空
            text = '由%s手动清空' % user_name
            self.tableWidget.item(self.curScr_row, 2).setText('')
            self.tableWidget.item(self.curScr_row, 2).setBackground(QColor('#ffffff'))
            self.tableWidget.item(self.curScr_row, 3).setText(user_name)
            self.tableWidget.item(self.curScr_row, 4).setText(cur_time)
            self.tableWidget.item(self.curScr_row, 5).setText(text)
            self.tableWidget.item(self.curScr_row, 6).setText('0 秒')
        elif action == runResult:
            self.DoShowMore()
            self.tabWidget.setCurrentIndex(0)
        elif action == runHistory:
            self.DoShowMore()
            self.tabWidget.setCurrentIndex(1)
        elif action == runInfo:
            self.DoShowMore()
            self.tabWidget.setCurrentIndex(2)
        else:
            return
        if action == runLocal or action == runEmpty:
            self.DoChangeTextNumber()
            self.DoSetMore()
            self.DoUpLoadData()
            self.dataHaveChange = True

    def DoUpLoadData(self):
        """上传记录"""
        if self.curScr_row >= 0:
            m_key = self.tableWidget.item(self.curScr_row, 0).text()
            m_item = self.tableWidget.item(self.curScr_row, 1).text()
            m_result = self.tableWidget.item(self.curScr_row, 2).text()
            m_usename = self.tableWidget.item(self.curScr_row, 3).text()
            m_rundate = self.tableWidget.item(self.curScr_row, 4).text()
            m_mark = self.tableWidget.item(self.curScr_row, 5).text()
            m_usetime = self.tableWidget.item(self.curScr_row, 6).text()

        sql = "insert into fpc_onekey_history (h_job,h_user,h_item,h_key,h_result,h_rundate,\
               h_usetime,h_mark) values ('%s','%s','%s','%s','%s','%s','%s','%s')" % (
            jobname, m_usename, m_item, m_key, m_result, m_rundate, m_usetime, m_mark)
        try:
            cursor.execute(sql)
            connect.commit()
        except Exception as e:
            connect.rollback()
            print(e)

    def DoTableScrChange(self):
        """检查项目点击"""
        cur_row = self.tableWidget.currentRow()
        if cur_row < 0:
            self.curScr = ''
            self.curScr_key = ''
        else:
            self.curScr_row = cur_row
            self.curScr_key = self.tableWidget.item(cur_row, 0).text()
            self.DoSetMore()

    def DoTableResuChange(self):
        # print(self.curScr_key)
        if self.curScr_key:
            resu_row = self.tableWidget_more_result.currentRow()
            # print(resu_row)
            if resu_row >= 0:
                mJobName = self.tableWidget_more_result.item(resu_row, 0).text()
                mStepName = self.tableWidget_more_result.item(resu_row, 1).text()
                mLayerName = self.tableWidget_more_result.item(resu_row, 2).text()
                mXY = self.tableWidget_more_result.item(resu_row, 3).text()
                mChecklist = self.tableWidget_more_result.item(resu_row, 4).text()
                if mStepName:
                    # s.VOF()
                    # s.close()
                    # s.close()
                    # s.close()
                    # s.VON()
                    # ss = job.steps[mStepName]
                    # 需要重新doinfo,job.steps在检查外初始化后在这里取到的不是最新的step数据
                    # job.getSteps()
                    # steps = job.getInfo()
                    # s.PAUSE(str(steps['gSTEPS_LIST']))
                    ss = gen.Step(job, mStepName)
                    ss.initStep()
                    ss.setUnits('mm')
                    if mLayerName:
                        if ' ' in mLayerName:
                            i = 1
                            for layName in mLayerName.split():
                                ss.display_layer(layName, i)
                                if i == 2:
                                    info = job.DO_INFO(
                                        '-t layer -e %s/%s/%s -d LIMITS,units=mm' % (mJobName, mStepName, layName))
                                    x1 = info['gLIMITSxmin'] - 0.5 * 25.4
                                    x2 = info['gLIMITSxmax'] + 0.5 * 25.4
                                    y1 = info['gLIMITSymin'] - 0.5 * 25.4
                                    y2 = info['gLIMITSymax'] + 0.5 * 25.4
                                    ss.zoomArea(x1, y1, x2, y2)
                                i += 1
                        else:
                            ss.display_layer(mLayerName, 1, 1)
                            ss.zoomHome()
                    QApplication.processEvents()
                    self.hide()
                    if mXY:
                        layer = mLayerName if len(mLayerName.split()) == 1 else mLayerName.split()[0]
                        ss.COM("pan_feat,layer=%s,index=%s,auto_zoom=yes " % (layer, mXY))
                        ss.COM("sel_layer_feat,operation=select,layer=%s,index=%s" % (layer, mXY))
                    if mChecklist:
                        checklist = ss.checks.get(mChecklist)
                        checklist.open()
                        checklist.show()
                        checklist.res_show()
                        checklist.hide()
                        # job.COM('chklist_open,chklist=%s' % mChecklist)
                        # job.COM('chklist_show,chklist=%s' % mChecklist)
                        # job.COM('chklist_res_show,chklist=%s,nact=1,x=500,y=400,w=0,h=0' % mChecklist)
                        # job.COM('chklist_close,chklist=%s,mode=hide' % mChecklist)
                    ss.PAUSE('PAUSE ,%s' % mLayerName)
                    self.show()

    # 单选运行
    def DoRunOneScr(self):
        """运行一个脚本"""
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.dataHaveChange = True
        tima_a = int(time.time())  # 开始时间
        cur_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # 脚本执行时间
        self.tableWidget.item(self.curScr_row, 2).setText('正在执行..')
        self.tableWidget.item(self.curScr_row, 3).setText('')
        self.tableWidget.item(self.curScr_row, 4).setText('')
        self.tableWidget.item(self.curScr_row, 5).setText('')
        self.tableWidget.item(self.curScr_row, 6).setText('')
        self.result_dict[self.curScr_key]['text'] = ''  # 清空脚本结果
        self.result_dict[self.curScr_key]['list'] = []
        scp_path = self.scr_dict[self.curScr_key]['path']
        scp_name = self.scr_dict[self.curScr_key]['name']
        if not os.path.exists(scp_path):
            QMessageBox.warning(self, "warning", '抱歉,该脚本路径不存在!', QMessageBox.Close)
            sys.exit()
            return
        self.statusbar.showMessage('正在执行: %s, 请稍等..' % (scp_name))
        returnXML = 'D:/tmp/fpcchecklist/%s_return.xml' % (mypid)
        if os.path.exists(returnXML):
            os.system('rm %s' % returnXML)
        top.COM('script_run,name=%s,dirmode=global,params=%s,env1=JOB=%s,env2=STEP=' % (scp_path, mypid, jobname))
        QApplication.processEvents()
        self.tableWidget.item(self.curScr_row, 4).setText('')
        if os.path.exists(returnXML):
            with open(returnXML, 'r', encoding='utf-8') as file:
                json_response = file.read()
            os.system('rm %s' % returnXML)
            dict_json = json.loads(json_response)

            state = dict_json['state']
            mark = dict_json['mark']
            msg = dict_json['msg']
        else:
            state = ''
            mark = '遇到错误,没有返回结果'
            msg = []
            # err_msg = '错误,没有返回结果'
        self.result_dict[self.curScr_key]['text'] = mark
        self.result_dict[self.curScr_key]['list'] = msg
        tima_b = int(time.time())  # 结束时间
        # List = ['key', '项目', '级别', '检测内容', '结果', '执行日期', '备注', '用户', '脚本用时']
        # List = ['key', '项目', '级别', '检测内容', '结果', '用户', '执行日期', '备注', '脚本用时']
        self.tableWidget.item(self.curScr_row, 2).setText(state)
        self.tableWidget.item(self.curScr_row, 3).setText(user_name)
        self.tableWidget.item(self.curScr_row, 4).setText(cur_time)
        self.tableWidget.item(self.curScr_row, 5).setText(mark)
        self.tableWidget.item(self.curScr_row, 6).setText('%s 秒' % (tima_b - tima_a))
        if state == 'OK':
            self.tableWidget.item(self.curScr_row, 2).setBackground(QColor('#51cbac'))
        elif state == 'NG':
            self.tableWidget.item(self.curScr_row, 2).setBackground(QColor('#b55090'))
        self.statusbar.showMessage('')

    # 开始检测
    def ExecAllCheck(self):
        """开始检查"""
        messageBox = QMessageBox()
        messageBox.setWindowFlags(Qt.WindowStaysOnTopHint)  # 置顶
        messageBox.setStyleSheet(
            "background:#DFE8F6;font-size:14px;"
        )
        messageBox.setWindowTitle('Question')
        messageBox.setText('注意: 即将检查所有项目,请确认？\t\t\n\n')
        messageBox.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        buttonY = messageBox.button(QMessageBox.Ok)
        buttonY.setText('确定')
        buttonC = messageBox.button(QMessageBox.Cancel)
        buttonC.setText('取消')
        messageBox.exec_()
        if messageBox.clickedButton() == buttonC:
            return
        for row in range(self.tableWidget.rowCount()):
            self.tableWidget.selectRow(row)
            self.DoRunOneScr()
            QApplication.processEvents()
            self.DoUpLoadData()
            self.DoChangeTextNumber()

    # 保存状态
    def SaveStatus(self):
        """保存状态"""
        """
        topDict{
           '*key*':{
               'name':name,
               'result':result,
               'runndate':runndate,
               'mark':mark,
               'username':username,
               'usetime':usetime,
           }
           ...                
        }
        """
        topDict = {}
        jobJsonPath = 'D:/scripts/oneKey/onekey_file/' + jobname
        # List = ['key', '项目', '级别', '检测内容', '结果', '执行日期', '备注', '用户', '脚本用时']
        for row in range(self.tableWidget.rowCount()):
            key = self.tableWidget.item(row, 0).text()
            name = self.tableWidget.item(row, 1).text()
            result = self.tableWidget.item(row, 2).text()
            username = self.tableWidget.item(row, 3).text()
            rundate = self.tableWidget.item(row, 4).text()
            mark = self.tableWidget.item(row, 5).text()
            usetime = self.tableWidget.item(row, 6).text()
            topDict[key] = {}
            topDict[key]['name'] = name
            topDict[key]['result'] = result
            topDict[key]['runndate'] = rundate
            topDict[key]['mark'] = mark
            topDict[key]['username'] = username
            topDict[key]['usetime'] = usetime
        if os.path.exists(jobJsonPath):
            os.unlink(jobJsonPath)
        self.dict_to_json(topDict, jobJsonPath)
        self.dataHaveChange = False
        if os.path.exists(jobJsonPath):
            self.statusbar.showMessage('保存完成!')

    def PauseScript(self):
        self.hide()
        job.PAUSE('Pause Script')
        self.show()
        # 退出

    def do_exit(self):
        if self.dataHaveChange:
            messageBox = QMessageBox()
            messageBox.setWindowFlags(Qt.WindowStaysOnTopHint)  # 置顶
            messageBox.setStyleSheet(
                "background:#DFE8F6;font-size:14px"
            )
            messageBox.setWindowTitle('Question')
            messageBox.setText('提醒:当前检测状态已变更,请确认是否需要保存？\t\t\n\n')
            messageBox.setStandardButtons(QMessageBox.Cancel | QMessageBox.No | QMessageBox.Ok)
            buttonY = messageBox.button(QMessageBox.Ok)
            buttonY.setText('保存并退出')
            buttonC = messageBox.button(QMessageBox.Cancel)
            buttonC.setText('取消')
            buttonN = messageBox.button(QMessageBox.No)
            buttonN.setText('直接退出')
            messageBox.exec_()
            if messageBox.clickedButton() == buttonY:
                self.SaveStatus()
            elif messageBox.clickedButton() == buttonC:
                return
        # 直接退出 清除+++结尾的临时层 2021-11-15 13:41:07 dyj
        layers = job.matrix.returnRows()
        for lay in layers:
            if re.search(r"\+\+\+", str(lay)):
                job.matrix.deleteRow(lay)
        sys.exit()

    def close_table(self):
        self.splitter.setSizes([800, 0])

    # 关闭窗口事件
    def closeEvent(self, event):
        if self.dataHaveChange:
            messageBox = QMessageBox()
            messageBox.setWindowFlags(Qt.WindowStaysOnTopHint)  # 置顶
            messageBox.setStyleSheet(
                "font-size:14px"  # background:#DFE8F6;
            )
            messageBox.setWindowTitle('Question')
            messageBox.setText('提醒:当前检测状态已变更,请确认是否需要保存？\t\t\n\n')
            messageBox.setStandardButtons(QMessageBox.Cancel | QMessageBox.No | QMessageBox.Ok)
            buttonY = messageBox.button(QMessageBox.Ok)
            buttonY.setText('保存并退出')
            buttonC = messageBox.button(QMessageBox.Cancel)
            buttonC.setText('取消')
            buttonN = messageBox.button(QMessageBox.No)
            buttonN.setText('直接退出')
            messageBox.exec_()
            if messageBox.clickedButton() == buttonY:
                self.SaveStatus()
            elif messageBox.clickedButton() == buttonC:
                event.ignore()
            # 直接退出 清除+++结尾的临时层
            layers = job.matrix.returnRows()
            for lay in layers:
                if re.search(r"\+\+\+", str(lay)):
                    job.matrix.deleteRow(lay)

    def DoSetMore(self):
        """设置more模块参数"""
        self.textEdit_info.setText('')
        # self.commandLinkButton_2.setEnabled(False)
        self.tableWidget_more_history.clearContents()
        if self.curScr_key:
            # 需求
            # if self.curScr_key and os.path.exists('../image/fpcCheckList_image/%s.png' % self.curScr_key):
            #     self.commandLinkButton_2.setEnabled(True)
            #     self.commandLinkButton_2.setText(self.curScr_key)
            # else:
            #     self.commandLinkButton_2.setEnabled(False)
            #     self.commandLinkButton_2.setText(self.curScr_key)
            # 脚本说明
            text = self.scr_dict[self.curScr_key]['info']
            if text:
                text = text.replace('\\n', '<br/>')
                self.textEdit_info.setText(text)
            # 历史记录
            self.tableWidget_more_history.clearContents()
            self.tableWidget_more_history.setRowCount(0)
            if self.curScr_key in self.history_dict.keys():
                self.tableWidget_more_history.setRowCount(len(self.history_dict[self.curScr_key]))
                #
                row = 0
                for line in self.history_dict[self.curScr_key]:
                    col = 0
                    for text in line:
                        self.tableWidget_more_history.setItem(row, col, QTableWidgetItem(str(text)))
                        col += 1
                    row += 1
            # 脚本结果
            self.textEdit_result.setText(self.result_dict[self.curScr_key]['text'])
            self.textEdit_result.setTextColor(QColor('#990000'))

            self.tableWidget_more_result.clearContents()
            self.tableWidget_more_result.setRowCount(len(self.result_dict[self.curScr_key]['list']))
            row = 0
            for d in self.result_dict[self.curScr_key]['list']:
                self.tableWidget_more_result.setItem(row, 0, QTableWidgetItem(str(d['job'])))
                self.tableWidget_more_result.setItem(row, 1, QTableWidgetItem(str(d['step'])))
                self.tableWidget_more_result.setItem(row, 2, QTableWidgetItem(str(' '.join(d['lay']))))
                self.tableWidget_more_result.setItem(row, 3, QTableWidgetItem(str(' '.join(d['xy']))))
                self.tableWidget_more_result.setItem(row, 4, QTableWidgetItem(str(d['chelist'])))
                row += 1

    def DoShowMore(self):
        """显示more模块"""
        self.splitter.setSizes([800, 160])

    def dict_to_json(self, myDict, file_path):
        """将字典转json保存到文件中"""
        str_json = json.dumps(myDict, ensure_ascii=False)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(str_json)

    def json_to_dict(self, file_path):
        """将文件中的json转换为字典"""
        with open(file_path, 'r', encoding='utf-8') as file:
            json_response = file.read()
        dict_json = json.loads(json_response)
        return dict_json

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(':/res/demo.png'))
    app.setStyle('Fusion')
    if 'JOB' not in os.environ.keys() or not os.environ.get('JOB'):
        QMessageBox.warning(None, 'infomation', '请先打开料号', QMessageBox.Ok)
        sys.exit()
    jobname = os.environ.get('JOB')
    top = gen.Top()
    user_name = top.getUser()
    mypid = top.pid
    job = gen.Job(jobname)
    dbcon = zlmysql.DBConnect()
    connect = dbcon.connection
    cursor = dbcon.cursor
    key = QaeOneKey()
    key.show()
    sys.exit(app.exec_())
