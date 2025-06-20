#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:OrigCompare.py
   @author:zl
   @time:2025/5/27 14:36
   @software:PyCharm
   @desc:
"""
import csv
import os
import re
import sys, platform

reload(sys)
sys.setdefaultencoding('utf8')
from PyQt4.QtCore import *
from PyQt4.QtGui import *

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen
from genesisPackages_zl import outsignalLayers, innersignalLayers
import Oracle_DB
import OrigCompareUI_pyqt4 as ui


class OrigCompare(QWidget, ui.Ui_Form):
    def __init__(self):
        super(OrigCompare, self).__init__()
        self.setupUi(self)
        self.render()

    def __getattr__(self, item):
        if item == 'out_comp_rule':
            self.out_comp_rule = self.get_comp_rule()
            return self.out_comp_rule
        if item == 'layer_copper_chink':
            self.layer_copper_chink = self.get_layer_copper_chink()
            return self.layer_copper_chink
        if item == 'layerInfo':
            self.layerInfo = self.get_layer_info()
            return self.layerInfo
        if item == 'stackupInfo':
            self.stackupInfo = self.get_inplan_stackup_info()
            self.stackupInfo = self.dealWithStackUpData(self.stackupInfo)
            return self.stackupInfo

    def get_comp_rule(self):
        self.scrDir = '/incam/server/site_data/scripts/hdi_scr/Etch/outerBaseComp'
        self.config_file = self.scrDir + '/etch_data-hdi1-out.csv'
        if jobname[1:4] in ["a86", "d10"]:
            self.config_file = self.scrDir + '/etch_data-hdi1-out_nv.csv'
        out_comp_rule = []
        with open(self.config_file) as f:
            f_csv = csv.DictReader(f)
            for row in f_csv:
                out_comp_rule.append(row)
        return out_comp_rule

    def get_inplan_stackup_info(self):
        """
        获取inplan干膜信息
        :return:
        """
        sql = """
        SELECT
            a.JOB_NAME,
            b.PROCESS_NAME,
            b.MRP_NAME,
            a.WORK_CENTER_CODE,
            a.OPERATION_CODE,
            a.DESCRIPTION,
            b.FILM_BG_,
            b.DRILL_CS_LASER_,
            c.VALUE AS DF_TYPE_ 
        FROM
            vgt_hdi.rpt_job_trav_sect_list a
            INNER JOIN vgt_hdi.Rpt_Job_Process_List b ON a.ROOT_ID = b.ROOT_ID 
            AND a.PROC_ITEM_ID = b.ITEM_ID 
            AND a.PROC_REVISION_ID = b.REVISION_ID
            INNER JOIN vgt_hdi.enum_values c ON b.df_type_ = c.enum 
            AND c.enum_type = '1012' 
        WHERE
            ( a.DESCRIPTION = 'LDI' OR a.OPERATION_CODE IN ( 'HDI11703', 'HDI17403' ) ) 
            AND a.JOB_NAME = '%s' 
            AND b.MRP_NAME NOT LIKE '%%光板%%'
        """ % self.inplan_job

        dataVal = self.con.SELECT_DIC(self.dbc_h, sql)
        # print dataVal
        return dataVal

    def dealWithStackUpData(self, InpDict):
        """
        处理叠构信息
        :param InpDict:
        :return:
        """
        dataVal = InpDict
        stack_data = {}
        # 根据压合叠构整理层别类型
        for index in dataVal:
            if index['FILM_BG_'] is None:
                continue
            top_bot_lay = index['FILM_BG_'].lower().split(',')
            stackProcess = index['PROCESS_NAME'].split('-')
            df_type = index['DF_TYPE_']
            # 2020.05.11 增加Core+Core的条件
            get_two_layer = stackProcess[1]
            # 去除数据前后空格
            twice_top_bot_lay = get_two_layer.strip(' ').split('/')

            # layerMode = None
            materialType = None
            if stackProcess[0] == "Final Assembly ":
                # layerMode = 'out'
                materialType = 'cu'
            elif stackProcess[0] == "Sub Assembly ":
                # layerMode = 'sec'
                materialType = 'cu'
                # if not index['DRILL_CS_LASER_']:
                #     layerMode = 'sec1'
            elif stackProcess[0] == "Inner Layers Core ":
                # layerMode = 'inn'
                materialType = 'core'
            elif stackProcess[0] == "Buried Via ":
                # layerMode = 'sec1'
                materialType = 'core'
            elif stackProcess[0] == "Blind Via ":
                # layerMode = 'sec1'
                materialType = 'core'

            '''
            S51506HI070A2	Final Assembly - 1/6	L1,L6
            S51506HI070A2	Buried Via - 3/4	L3,L4
            S51506HI070A2	Blind Via - 1/2	L2
            S51506HI070A2	Blind Via - 5/6	L5
            '''
            # if self.JobData[0]['ES_ELIC_'] == 1 and layerMode != 'out':
            #     layerMode = 'sec'
            #     if int(twice_top_bot_lay[1]) - int(twice_top_bot_lay[0]) == 1:
            #         layerMode = 'sec1'

            #  === 2022.04.20 层别是内层，外层，次外层内，次外层外，使用流程进行判断
            layerMode = None
            # inn_Reg = re.compile('内层线路')
            # out_Reg = re.compile('外层线路')
            sec1_Reg = re.compile('次外层线路（内')
            sec_Reg = re.compile('次外层线路（外')

            work_name = index['WORK_CENTER_CODE']
            if work_name == '内层线路':
                layerMode = 'inn'
            elif work_name == '外层线路' or work_name == '外层图形':
                layerMode = 'out'
            elif sec1_Reg.match(work_name):
                layerMode = 'sec1'
            elif sec_Reg.match(work_name):
                layerMode = 'sec'

            if self.JobData[0]['ES_ELIC_'] == 1 and layerMode == 'inn':
                if int(twice_top_bot_lay[1]) - int(twice_top_bot_lay[0]) == 1:
                    layerMode = 'sec1'

            # 由于可能存在work_name 没有匹配到，重复的干膜信息，当已经获取到key了，跳出循环
            if not layerMode and (stack_data.has_key(top_bot_lay[0]) or stack_data.has_key(top_bot_lay[0])):
                continue
            if len(top_bot_lay) != 2:
                stack_data[top_bot_lay[0]] = {}
                get_top_lay = 'l' + twice_top_bot_lay[0]
                get_bot_lay = 'l' + twice_top_bot_lay[1]
                if top_bot_lay[0] == get_top_lay:
                    stack_data[top_bot_lay[0]]['layerSide'] = 'top'
                    stack_data[top_bot_lay[0]]['layerMode'] = layerMode
                    stack_data[top_bot_lay[0]]['materialType'] = materialType
                    stack_data[top_bot_lay[0]]['df_type'] = df_type
                elif top_bot_lay[0] == get_bot_lay:
                    stack_data[top_bot_lay[0]]['layerSide'] = 'bot'
                    stack_data[top_bot_lay[0]]['layerMode'] = layerMode
                    stack_data[top_bot_lay[0]]['materialType'] = materialType
                    stack_data[top_bot_lay[0]]['df_type'] = df_type
            else:
                stack_data[top_bot_lay[0]] = {}
                stack_data[top_bot_lay[1]] = {}
                stack_data[top_bot_lay[0]]['layerSide'] = 'top'
                stack_data[top_bot_lay[0]]['layerMode'] = layerMode
                stack_data[top_bot_lay[0]]['materialType'] = materialType
                stack_data[top_bot_lay[0]]['df_type'] = df_type

                stack_data[top_bot_lay[1]]['layerSide'] = 'bot'
                stack_data[top_bot_lay[1]]['layerMode'] = layerMode
                stack_data[top_bot_lay[1]]['materialType'] = materialType
                stack_data[top_bot_lay[1]]['df_type'] = df_type

        if jobname == "DA8608PI999A1".lower():
            top_bot_lay = ["l4", "l5"]
            stack_data[top_bot_lay[0]] = {}
            stack_data[top_bot_lay[1]] = {}
            stack_data[top_bot_lay[0]]['layerSide'] = 'top'
            stack_data[top_bot_lay[0]]['layerMode'] = 'inn'
            stack_data[top_bot_lay[0]]['materialType'] = 'core'
            stack_data[top_bot_lay[0]]['df_type'] = "Unknown"

            stack_data[top_bot_lay[1]]['layerSide'] = 'bot'
            stack_data[top_bot_lay[1]]['layerMode'] = 'inn'
            stack_data[top_bot_lay[1]]['materialType'] = 'core'
            stack_data[top_bot_lay[1]]['df_type'] = "Unknown"

        return stack_data

    def get_layer_copper_chink(self):
        think_dict = {}
        inplan_job = jobname[:13].upper()
        thick_list = self.con.getLayerThkInfo_plate(self.dbc_h, inplan_job, "outer")
        for d in thick_list:
            if d['LAYER_NAME'] and d['LAYER_NAME'] in outsignalLayers:
                think_dict[d['LAYER_NAME']] = d['CAL_CU_THK']
        thick_list = self.con.getLayerThkInfo_plate(self.dbc_h, inplan_job, "inner")
        for d in thick_list:
            if d['LAYER_NAME'] and d['LAYER_NAME'] in innersignalLayers:
                think_dict[d['LAYER_NAME']] = d['CAL_CU_THK']
        return think_dict

    def get_layer_info(self):
        inplan_job = jobname[:13].upper()
        thick_list = self.con.getLayerThkInfo_plate(self.dbc_h, inplan_job, "inner")
        return thick_list

    def render(self):
        self.con = Oracle_DB.ORACLE_INIT()
        self.dbc_h = self.con.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
                                         username='GETDATA', passwd='InplanAdmin')
        self.db1 = '/id/incamp_db1/jobs'

        self.jobs = [str(j) for j in gen.Top().listJobs()]
        print(len(self.jobs))
        self.inplan_job = jobname.split('-')[0].upper()
        self.JobData = self.con.getJobData(self.dbc_h, self.inplan_job)
        self.splitter.setStretchFactor(0, 1)
        self.lineEdit_jobname.setText(jobname)
        self.lineEdit_jobname.setCursorPosition(0)
        self.comboBox_steps.addItems(job.stepsList)
        if os.environ.get('STEP'):
            for index, val in enumerate(job.stepsList):
                if val == os.environ.get('STEP'):
                    self.comboBox_steps.setCurrentIndex(index)
        else:
            for index, val in enumerate(job.stepsList):
                if val == 'edit':
                    self.comboBox_steps.setCurrentIndex(index)
        self.comboBox_target_job.addItems(self.jobs)
        for index, _ in enumerate(self.jobs):
            if _ == jobname:
                self.comboBox_target_job.setCurrentIndex(index)
        self.comboBox_target_steps.addItems(job.stepsList)
        self.comboBox_target_steps.setCurrentIndex(self.comboBox_steps.currentIndex())
        # self.lineEdit_path.setText(f'D:/{jobname}')
        # self.lineEdit_path.setCursorPosition(0)
        #
        # self.checkBox_pad_as_circle.setVisible(False)
        # self.checkBox_merge.setVisible(False)
        # self.lineEdit_merge_name.setVisible(False)
        # 分段
        # self.comboBox_split.addItems(['', '上', '下'])
        # self.comboBox_split.currentIndexChanged.connect(self.changeRotateEnable)
        # self.checkBox_split_rotate.setEnabled(False)
        # self.comboBox_anchor.addItems(['Step Datum', 'Profile center'])
        self.header1 = [u'勾选', u'层列表', 'type', 'context', u'铜厚', u'一般线补偿', u'阻抗线补偿', u'铜皮补偿',
                        '<=12mil BGA', '>12mil BGA', '<=12mil SMD', '>12mil SMD', u'无SMD、BGA属性Pad']
        self.tableWidget.setColumnCount(len(self.header1))
        self.tableWidget.setHorizontalHeaderLabels(self.header1)
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.setSelectionMode(QHeaderView.NoSelection)
        self.tableWidget.setColumnWidth(0, 30)
        self.tableWidget.setColumnWidth(4, 50)
        self.tableWidget.setColumnWidth(5, 70)
        self.tableWidget.setColumnWidth(6, 70)
        self.tableWidget.setColumnWidth(7, 70)
        self.tableWidget.setColumnWidth(8, 80)
        self.tableWidget.setColumnWidth(9, 80)
        self.tableWidget.setColumnWidth(10, 80)
        self.tableWidget.setColumnWidth(11, 80)
        self.tableWidget.setColumnWidth(12, 110)
        self.tableWidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setResizeMode(2, QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setResizeMode(3, QHeaderView.Stretch)
        # self.tableWidget.horizontalHeader().setResizeMode(4, QHeaderView.Stretch)
        # self.tableWidget.horizontalHeader().setSectionResizeMode(9, QHeaderView.Stretch)
        # self.tableWidget.horizontalHeader().setSectionResizeMode(10, QHeaderView.Stretch)
        self.tableWidget.setItemDelegateForColumn(1, EmptyDelegate(self))
        self.tableWidget.setItemDelegateForColumn(2, EmptyDelegate(self))
        self.tableWidget.setItemDelegateForColumn(3, EmptyDelegate(self))
        self.tableWidget.setItemDelegateForColumn(4, EmptyDelegate(self))
        # 类型
        self.checkBox_signal.clicked.connect(self.check_type)
        self.checkBox_soldmask.clicked.connect(self.check_type)
        self.checkBox_silkscreen.clicked.connect(self.check_type)
        self.checkBox_drill.clicked.connect(self.check_type)
        self.checkBox_board.clicked.connect(self.check_type)
        #
        self.lineEdit_npth_comp.setText('0.5')
        self.lineEdit_pth_comp.setText('2')
        self.lineEdit_npth_comp.setValidator(QDoubleValidator(self.lineEdit_npth_comp))
        self.lineEdit_pth_comp.setValidator(QDoubleValidator(self.lineEdit_pth_comp))
        layer_extra = (u'前缀', u'后缀')
        self.comboBox_layer_extra.addItems(layer_extra)
        self.lineEdit_layer_extra.setText('+++compare')
        tolerance = ('1.0', '2.0')
        self.comboBox_tolerance.addItems(tolerance)
        self.comboBox_tolerance.lineEdit().setValidator(QDoubleValidator(self.comboBox_tolerance))
        self.comboBox_area.addItems(('global', 'profile'))
        self.comboBox_area.setCurrentIndex(1)
        #
        self.pushButton_run.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.checkBox_select_all.clicked.connect(self.check_all)
        self.comboBox_target_job.lineEdit().returnPressed.connect(self.target_job_returnPressed)
        self.comboBox_target_job.currentIndexChanged.connect(self.target_job_changed)
        self.setStyleSheet(
            '''QPushButton{font:10pt;background-color:#0081a6;color:white;border:none;} QPushButton:hover{background:black;} QTableWidgetItem{text-align:center;}''')
        # self.setStyleSheet(
        #     '''QPushButton{font:10pt;background-color:#459B81;color:white;} QPushButton:hover{background:black;}''')
        self.loadTable()
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)

    def check_type(self):
        layer_type = str(self.sender().text())
        state = self.sender().isChecked()
        print(state, layer_type)
        if layer_type == '线路':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 2).text() == 'signal' and self.tableWidget.item(row, 3).text() == 'board':
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row,
                                                                                                                   0).setChecked(
                        False)
        elif layer_type == '文字':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 2).text() == 'silk_screen' and self.tableWidget.item(row,
                                                                                                   3).text() == 'board':
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row,
                                                                                                                   0).setChecked(
                        False)
        elif layer_type == '钻孔':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 2).text() == 'drill' and self.tableWidget.item(row, 3).text() == 'board':
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row,
                                                                                                                   0).setChecked(
                        False)
        elif layer_type == '阻焊':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 2).text() == 'solder_mask' and self.tableWidget.item(row,
                                                                                                   3).text() == 'board':
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row,
                                                                                                                   0).setChecked(
                        False)
        elif layer_type == '板层':
            for row in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 3).text() == 'board':
                    self.tableWidget.cellWidget(row, 0).setChecked(True) if state else self.tableWidget.cellWidget(row,
                                                                                                                   0).setChecked(
                        False)

    def check_all(self):
        if self.checkBox_select_all.isChecked():
            for row in range(self.tableWidget.rowCount()):
                self.tableWidget.cellWidget(row, 0).setChecked(True)
        else:
            for row in range(self.tableWidget.rowCount()):
                self.tableWidget.cellWidget(row, 0).setChecked(False)

    def loadTable(self):
        self.getComp()
        # print(self.out_comp_rule)
        # print(self.layer_copper_chink)
        step = job.steps.get(self.comboBox_steps.currentText())
        self.tableWidget.setRowCount(0)
        self.tableWidget.clearContents()
        matrix_info = job.matrix.info
        tableData = []
        for name, context, type in zip(matrix_info.get('gROWname'), matrix_info.get('gROWcontext'),
                                       matrix_info.get('gROWlayer_type')):
            tableData.append([name, type, context])
        self.tableWidget.setRowCount(len(tableData))
        for row, data in enumerate(tableData):
            sig_layers = data[0]
            color = '#AFEEEE'
            if data[2] == 'misc':
                color = '#AFEEEE'
                size1 = size2 = 2
            else:
                if data[1] == 'signal':
                    color = '#FFA500'
                    # todo getComp
                    # self.getComp(data[0])
                    size1 = size2 = 2
                elif data[1] == 'solder_mask':
                    color = '#008080'
                    size1 = size2 = 2
                elif data[1] == 'drill':
                    color = '#A9A9A9'
                elif data[1] == 'silk_screen':
                    color = '#FFFFFF'
                    size1 = size2 = 2
            check = QCheckBox()
            check.setStyleSheet('margin-left:5px;')
            self.tableWidget.setCellWidget(row, 0, check)
            item = QTableWidgetItem(str(data[0]))
            item.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(row, 1, item)
            item = QTableWidgetItem(str(data[1]))
            item.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(row, 2, item)
            item = QTableWidgetItem(str(data[2]))
            item.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(row, 3, item)
            # input_ = QLineEdit(str(size1))
            # input_.setStyleSheet('background-color: transparent;margin:4px;')
            # self.tableWidget.setCellWidget(row, 4, input_)
            print(self.layer_copper_chink.get(str(sig_layers)))
            thickness = self.layer_copper_chink.get(str(sig_layers)) if self.layer_copper_chink.get(str(sig_layers)) else ''
            item = QTableWidgetItem(str(thickness))
            item.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(row, 4, item)
            ####
            if sig_layers in outsignalLayers:
                try:
                    # out_comp = [i['range_type'] for i in self.out_comp_rule]
                    for cur_dict in self.out_comp_rule:
                        rw = cur_dict['range_type']
                        min_num, max_num = float(rw[:3]), float(rw[-3:])
                        if min_num <= thickness < max_num:
                            item = QTableWidgetItem(cur_dict['base_comp'])
                            item.setTextAlignment(Qt.AlignCenter)
                            self.tableWidget.setItem(row, 5, item)
                            item = QTableWidgetItem(cur_dict['imp_comp'])
                            item.setTextAlignment(Qt.AlignCenter)
                            self.tableWidget.setItem(row, 6, item)
                            item = QTableWidgetItem('0')
                            item.setTextAlignment(Qt.AlignCenter)
                            self.tableWidget.setItem(row, 7, item)
                            item = QTableWidgetItem(cur_dict['bgalow12'])
                            item.setTextAlignment(Qt.AlignCenter)
                            self.tableWidget.setItem(row, 8, item)
                            item = QTableWidgetItem(cur_dict['bgaup12'])
                            item.setTextAlignment(Qt.AlignCenter)
                            self.tableWidget.setItem(row, 9, item)
                            item = QTableWidgetItem(cur_dict['smdlow12'])
                            item.setTextAlignment(Qt.AlignCenter)
                            self.tableWidget.setItem(row, 10, item)
                            item = QTableWidgetItem(cur_dict['smdup12'])
                            item.setTextAlignment(Qt.AlignCenter)
                            self.tableWidget.setItem(row, 11, item)
                            item = QTableWidgetItem(cur_dict['smdlow12'])
                            item.setTextAlignment(Qt.AlignCenter)
                            self.tableWidget.setItem(row, 12, item)
                except:
                    self.tableWidget.setItem(row, 5, QTableWidgetItem(''))
                    self.tableWidget.setItem(row, 6, QTableWidgetItem(''))
                    item = QTableWidgetItem('0')
                    item.setTextAlignment(Qt.AlignCenter)
                    self.tableWidget.setItem(row, 7, item)
                    self.tableWidget.setItem(row, 8, QTableWidgetItem(''))
                    self.tableWidget.setItem(row, 9, QTableWidgetItem(''))
                    self.tableWidget.setItem(row, 10, QTableWidgetItem(''))
                    self.tableWidget.setItem(row, 11, QTableWidgetItem(''))
                    self.tableWidget.setItem(row, 12, QTableWidgetItem(''))
            elif sig_layers in innersignalLayers:
                print(self.layer_copper_chink)
                for info in self.layerInfo:
                    if sig_layers == info['LAYER_NAME']:
                        if self.stackupInfo[sig_layers]['layerMode'] == 'out' or \
                                self.stackupInfo[sig_layers]['layerMode'] == 'sec':
                            compData = self.getCouponCompListOuter(info['CAL_CU_THK'])
                            # self.layerInfo[index]['compData'] = compData
                            item = QTableWidgetItem(str(compData.impBaseComp))
                            item.setTextAlignment(Qt.AlignCenter)
                            self.tableWidget.setItem(row, 6, item)
                            item = QTableWidgetItem(str(compData.baseLineComp))
                            item.setTextAlignment(Qt.AlignCenter)
                            self.tableWidget.setItem(row, 5, item)

                        elif self.stackupInfo[sig_layers]['layerMode'] == 'inn':
                            compData = self.getCouponCompListInner(info['CU_WEIGHT'])
                            if compData is None:
                                showText = self.msgText(u'警告',
                                                        u'{0}层 铜厚 {1} OZ超出补偿范围，请反馈主管确认, 程序退出！'.format(
                                                            sig_layers, data['CU_WEIGHT']
                                                        ))
                                self.msgBox(showText)
                                self.compFileexist = 'no'
                                exit(0)
                            item = QTableWidgetItem(str(compData.impBaseComp))
                            item.setTextAlignment(Qt.AlignCenter)
                            self.tableWidget.setItem(row, 6, item)
                            item = QTableWidgetItem(str(compData.baseLineComp))
                            item.setTextAlignment(Qt.AlignCenter)
                            self.tableWidget.setItem(row, 5, item)

                        elif self.stackupInfo[sig_layers]['layerMode'] == 'sec1':
                            compData = self.getCouponCompListSec1(info['CAL_CU_THK'])
                            item = QTableWidgetItem(str(compData.impBaseComp))
                            item.setTextAlignment(Qt.AlignCenter)
                            self.tableWidget.setItem(row, 6, item)
                            item = QTableWidgetItem(str(compData.baseLineComp))
                            item.setTextAlignment(Qt.AlignCenter)
                            self.tableWidget.setItem(row, 5, item)


            # input_ = QLineEdit(str(size2))
            # input_.setStyleSheet('background-color: transparent;margin:4px;')
            # self.tableWidget.setCellWidget(row, 5, input_)
            self.tableWidget.item(row, 1).setBackground(QColor(color))
            self.tableWidget.item(row, 2).setBackground(QColor(color))
            self.tableWidget.item(row, 3).setBackground(QColor(color))

            # self.tableWidget.item(row, 4).setBackground(QColor(color))

    def run(self):
        target_job = str(self.comboBox_target_job.currentText()).strip()
        if not target_job:
            QMessageBox.warning(self, u'提示', u'请选择目标料号！')
            return
        if target_job not in self.jobs:
            QMessageBox.warning(self, u'提示', u'目标料号不存在！')
            return
        target_step = str(self.comboBox_target_steps.currentText())
        target_steps = os.listdir(os.path.join(self.db1, target_job, 'steps'))
        if target_step not in target_steps:
            QMessageBox.warning(self, u'提示', u'输入料号需要回车更新目标step!')
            return
        tolerance = str(self.comboBox_tolerance.currentText()).strip()
        if not tolerance:
            QMessageBox.warning(self, u'提示', u'请输入或选择比对精度!')
            return
        flag = False
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.cellWidget(row, 0).isChecked():
                flag = True
                break
        if not flag:
            QMessageBox.information(self, u'提示', u'未勾选层')
            return
        step = job.steps.get(self.comboBox_steps.currentText())


    def getComp(self):
        # 获取外层补偿规则
        self.compFileexist = 'yes'
        self.scrDir = '/incam/server/site_data/scripts/hdi_scr/Etch/innerLayerComp'
        Outer_data = self.scrDir + '/innComp_Outer.csv'
        if os.path.exists(Outer_data):
            f = open(Outer_data)
            self.comp_data_outer = map(lambda x: x.strip().split(","), f.readlines()[1:])
            self.comp_data_outer = [sepByAttr(x) for x in self.comp_data_outer]
        else:
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(u'没有外层补偿配置文件, 程序退出！')
                return
            else:
                showText = self.msgText(u'警告', u'没有外层补偿配置文件, 程序退出！')
                self.msgBox(showText)
                self.compFileexist = 'no'
                exit(0)

        # 获取内层补偿规则
        if os.path.exists(self.scrDir + '/innComp_Inner.ini'):
            f = open(self.scrDir + '/innComp_Inner.ini')

            self.comp_data_inner = map(lambda x: x.strip().split("\t"), f.readlines())
            self.comp_data_inner = [sepByAttr(x) for x in self.comp_data_inner]
        else:
            # Mess = msgBox.Main ()
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(u'没有内层补偿配置文件, 程序退出！')
                return
            else:
                showText = self.msgText(u'警告', u'没有内层补偿配置文件, 程序退出！')
                self.msgBox(showText)
                self.compFileexist = 'no'
                exit(0)

        # 获取次一层补偿规则
        if os.path.exists(self.scrDir + '/innComp_Sec1.ini'):
            f = open(self.scrDir + '/innComp_Sec1.ini')

            self.comp_data_sec1 = map(lambda x: x.strip().split("\t"), f.readlines())
            self.comp_data_sec1 = [sepByAttr(x) for x in self.comp_data_sec1]
        else:
            # Mess = msgBox.Main ()
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(u'没有次一层补偿配置文件, 程序退出！')
                return
            else:
                showText = self.msgText(u'警告', u'没有次一层补偿配置文件, 程序退出！')
                self.msgBox(showText)
                self.compFileexist = 'no'
                exit(0)

    def getCouponCompListOuter(self, joblayerThk):
        # 声明一个空字典，来保存文本文件数据
        joblayerThk = float(joblayerThk)
        for line in self.comp_data_outer:  # type: sepByAttr
            if line.thk_dowm <= joblayerThk < line.thk_up:
                print 'Outer:%s,%s,%s,%s' % (joblayerThk,line.thk_dowm,line.thk_up,line.impBaseComp)
                return line

    def getCouponCompListSec1(self, joblayerThk):
        # 声明一个空字典，来保存文本文件数据
        joblayerThk = float(joblayerThk)
        for line in self.comp_data_sec1:  # type: sepByAttr
            if line.thk_dowm <= joblayerThk < line.thk_up:
                print 'Sec1:%s,%s,%s,%s' % (joblayerThk,line.thk_dowm,line.thk_up,line.impBaseComp)
                return line

    def getCouponCompListInner(self, joblayerThk):
        # 声明一个空字典，来保存文本文件数据
        joblayerThk = float(joblayerThk)
        for line in self.comp_data_inner:  # type: sepByAttr
            if line.thk_dowm <= joblayerThk < line.thk_up:
                # print 'Inner:%s,%s,%s,%s,%s' % (line.CopDiffComp,line.CopSingleComp,line.SingleComp,line.DiffComp,line.impBaseComp)
                return line


    def do_compare(self, layer, layer_after, x_scale, y_scale, mirror, x_anchor, y_anchor):
        map_layer = '%s+++compare' % layer
        self.step.affect(layer_after)
        if x_scale != 1 or y_scale != 1:
            self.step.Transform(oper='scale', x_anchor=x_anchor, y_anchor=y_anchor, x_scale=2 - x_scale,
                                y_scale=2 - y_scale)
        if mirror == 'yes':
            self.step.Transform(oper='mirror', x_anchor=x_anchor, y_anchor=y_anchor)
        self.step.unaffectAll()
        self.step.VOF()
        self.step.compareLayers(layer, jobname, self.step.name, layer_after, tol=25.4, map_layer=map_layer,
                                map_layer_res=200)
        self.step.VON()
        self.step.affect(map_layer)
        self.step.selectSymbol('r0')
        self.step.resetFilter()
        count = self.step.Selected_count()
        self.step.unaffectAll()
        self.step.removeLayer(map_layer)
        if count:
            return layer
        else:
            return None

    def target_job_changed(self, index):
        print('changed', index)
        if index >= len(self.jobs):
            return
        target_job = self.jobs[index]
        target_steps = os.listdir(os.path.join(self.db1, target_job, 'steps'))
        self.comboBox_target_steps.clear()
        self.comboBox_target_steps.addItems(target_steps)

    def target_job_returnPressed(self):
        print(self.comboBox_target_job.currentText())
        if self.comboBox_target_job.currentText() not in self.jobs:
            QMessageBox.warning(self, 'warning', u'该料号不存在')
            self.comboBox_target_job.clear()
            self.comboBox_target_job.addItems(self.jobs)
            for index, _ in enumerate(self.jobs):
                if _ == jobname:
                    self.comboBox_target_job.setCurrentIndex(index)
                    self.target_job_changed(index)
        else:
            for index, _ in enumerate(self.jobs):
                if _ == self.comboBox_target_job.currentText():
                    self.comboBox_target_job.setCurrentIndex(index)
                    self.target_job_changed(index)

    # def get_layer_copper_chink(self, sel_layers):
    #     think_dict = {}
    #     con = Oracle_DB.ORACLE_INIT()
    #     dbc_h = con.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
    #                            username='GETDATA', passwd='InplanAdmin')
    #     inplan_job = self.job_name[:13].upper()
    #     thick_list = con.getLayerThkInfo_plate(dbc_h, inplan_job, "outer")
    #     for d in thick_list:
    #         if d['LAYER_NAME'] and d['LAYER_NAME'] in sel_layers:
    #             think_dict[d['LAYER_NAME']] = d['CAL_CU_THK']
    #     return think_dict

    def msgBox(self, body, title=u'提示信息', msgType='information', ):
        """
        可供提示选择的MessagesBox
        :param body:显示内容（支持html样式）
        :param title:标题
        :param msgType:显示类型（包括information, question, warning）
        :return:
        """
        if msgType == 'information':
            QMessageBox.information(self, title, body, u'确定')
        elif msgType == 'warning':
            QMessageBox.warning(self, title, body, u'确定')
        elif msgType == 'question':
            QMessageBox.question(self, title, body, u'确定')

    def msgText(self, body1, body2, body3=None):
        """
        转换HTML格式
        :param body1:文本1
        :param body2:文本2
        :param body3:文本3
        :return:转换后的文本
        """
        # --转换为Html文本
        textInfo = u"""
                <p>
                    <span style="background-color:#E53333;color:#FFFFFF;font-size:18px;"><strong>%s：</strong></span>
                </p>
                <p>
                    <span style="font-size:18px;">&nbsp;&nbsp;</span>
                    <span style="color:#E53333;font-size:18px;">&nbsp;&nbsp;</span>
                    <span style="color:#E53333;font-size:18px;">&nbsp; &nbsp; </span>
                    <span style="color:#E53333;font-size:16px;">%s</span>
                </p>""" % (body1, body2)

        # --返回HTML样式文本
        return textInfo

class sepByAttr:  # 自定义的元素
    def __init__(self, (thk_dowm, thk_up, rangeSpc, minWorkSpc, impBaseComp, baseLineComp)):
        self.thk_dowm = float(thk_dowm)
        self.thk_up = float(thk_up)
        self.rangeSpc = rangeSpc
        self.minWorkSpc = float(minWorkSpc)
        self.impBaseComp = float(impBaseComp) if impBaseComp != 'None' else 0
        self.baseLineComp = float(baseLineComp) if baseLineComp != 'None' else 0

# 代理类
class EmptyDelegate(QItemDelegate):
    def __init__(self, parent):
        super(EmptyDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        return None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    # app.setWindowIcon(QIcon(':res/demo.png'))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    origCompare = OrigCompare()
    origCompare.show()
    sys.exit(app.exec_())
