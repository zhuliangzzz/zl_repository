#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :
# @Date         :    2020/03/17
# @Revision     :    1.0.1
# @File         :    output_backdrill-hdi.py
# @Software     :    PyCharm
# @Usefor       :    HDI一厂背钻输出程序
# ---------------------------------------------------------#
# pragma execution_character_set("utf-8")
import string
import threading
import math
import datetime
import sys

_header = {
    'description': '''
    -> 本程序主要服务于胜宏科技（惠州），任何其他团体或个人如需使用，必须经胜宏科技（惠州）相关负责
       人及作者的批准，并遵守以下约定；
    1> 本着尊重创作者的劳动成果，任何团体或个人在使用此程序的时候，均需要知会此程序的原始创作者；
    2> 在任何场合宣导、宣传，在任何文件、报告、邮件中提及本程序的全部或部分功能，均需要声明此程序的
       原始创作者；
    3> 在任何时候对本程序做部分修改或者是升级时，必须要保留文件的原始信息，包括原始文件名、创作者及
       联系方式、创作日期等信息，且不得删除程序中的源代码，只能进行注释处理；
'''
}

# --导入Package
import os
import re
import sys
# import genCOM_26
import op_bkdrlUIV3 as FormUi
import depth_table as TableUi
from outputMain import outputDrill
from PyQt4 import QtCore, QtGui, Qt
# from PyQt4.QtGui import *
# import msgBox
import json
import platform

sysstr = platform.system ()

if sysstr == "Windows":
    sys.path.append (r"Z:/incam/genesis/sys/scripts/Package")
elif sysstr == "Linux":
    sys.path.append (r"/incam/server/site_data/scripts/Package")
else:
    print ("Other System tasks")

import Oracle_DB
import genCOM_26
import time
GEN = genCOM_26.GEN_COM ()

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QtGui.QApplication.translate (context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate (context, text, disambig)


class M_Box:
    """
    MesageBox提示界面
    """

    def __init__(self):
        pass

    def msgBox_option(self, body, title=u'提示信息', msgType='information'):
        """
        可供提示选择的MessagesBox
        :param body:显示内容（支持html样式）
        :param title:标题
        :param msgType:显示类型（包括information, question, warning）QtGui.QMessageBox.ButtonMask 可查看所有
        :return:
        """
        msg = QtGui.QMessageBox.information (QtGui.QWidget(), u"信息", body, QtGui.QMessageBox.Ok,
                                             QtGui.QMessageBox.Cancel)  # , )
        # --返回相应信息
        if msg == QtGui.QMessageBox.Ok:
            return 'Ok'
        else:
            return 'Cancel'

    def msgBox(self, body, title=u'提示信息', msgType='information', ):
        """
        可供提示选择的MessagesBox
        :param body:显示内容（支持html样式）
        :param title:标题
        :param msgType:显示类型（包括information, question, warning）
        :return:
        """
        if msgType == 'information':
            QtGui.QMessageBox.information (QtGui.QWidget(), title, body, u'确定')
        elif msgType == 'warning':
            QtGui.QMessageBox.warning (QtGui.QWidget(), title, body, u'确定')
        elif msgType == 'question':
            QtGui.QMessageBox.question (QtGui.QWidget(), title, body, u'确定')

    def msgText(self, body1, body2, body3=None, showcolor = '#E53333'):
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
                    <span style="background-color:%s;color:'#FFFFFF';font-size:18px;"><strong>%s：</strong></span>
                </p>
                <p>
                    <span style="font-size:18px;">&nbsp;&nbsp;</span>
                    <span style="color:#E53333;font-size:18px;">&nbsp;&nbsp;</span>
                    <span style="color:#E53333;font-size:18px;">&nbsp; &nbsp; </span>
                    <span style="color:#E53333;font-size:16px;">%s</span>
                </p>""" % (showcolor,body1, body2)

        # --返回HTML样式文本
        return textInfo


class MainbackOutput (M_Box):
    def __init__(self):
        self.job_name = os.environ.get ('JOB')
        # self.job_name = 's94006pf009a9'
        # self.job_name = 'SA1008AH004A2'
        self.step_name = os.environ.get ('STEP')
        self.scr_file = os.getcwd ()  # 获取当前工作目录路径
        self.appVer = '1.2.7'
        M_Box.__init__ (self)
        self.strJobName = self.job_name.split ('-')[0].upper ()
        self.scrDir = os.path.split (os.path.abspath (sys.argv[0]))[0]
        os.path.realpath (sys.argv[0])
        self.genUser = GEN.getUser()
        # TODO test for show
        # self.sig_layers = ['l1', 'l2', 'l3', 'l4', 'l5', 'l6','l7','l8','l9','l10','l11','l12','l13','l14']
        # self.sig_layers = ['l1', 'l2', 'l3', 'l4', 'l5', 'l6', 'l7', 'l8']

        if GEN.STEP_EXISTS (job=self.job_name, step='panel') == 'yes':
            self.opStep = 'panel'
        else:
            showText = self.msgText (u'警告', u'无panel Step存在, 程序退出！')
            self.msgBox (showText)
            exit (0)

        try:
            self.sig_layers, self.topDrlList, self.botDrlList, self.innDrlList = self.getJobMatrix ()
        except TypeError:
            showText = self.msgText (u'警告', u'运行失败, 程序退出！')
            self.msgBox (showText)
            exit (0)
        self.job_layer_num = len (self.sig_layers)
        self.getInPlanInfo ()

    def getInPlanInfo(self, mode='jobExist'):
        M = Oracle_DB.ORACLE_INIT ()
        dbc_o = M.DB_CONNECT ("172.20.218.193", "inmind.fls", '1521', 'GETDATA', 'InplanAdmin')

        if dbc_o == None:
            # Mess = msgBox.Main ()
            showText = self.msgText (u'警告', u'HDI InPlan 无法连接, 程序退出！')
            self.msgBox (showText)
            exit (0)

        # inplan中无数据返回时应提示inplan中查询不到数据

        if mode == 'jobExist':
            InplanJobExist = self.getJobExist (M, dbc_o, self.strJobName)
            if InplanJobExist:
                pass
            else:
                showText = self.msgText (u'警告', u'HDI InPlan无料号%s数据, 程序退出！' % self.job_name)
                self.msgBox (showText)
                exit (0)
        elif mode == 'drlDepth':
            BackdrlDepth = self.getBackDrillDepth (M, dbc_o, self.strJobName)
            if BackdrlDepth:
                pass
            else:
                showText = self.msgText (u'警告', u'HDI InPlan无料号%s背钻数据, 程序退出！' % self.job_name)
                self.msgBox (showText)
                exit (0)
            return BackdrlDepth

        M.DB_CLOSE (dbc_o)

    def getJobExist(self, M, dbc, strJOB):
        sql = """
        SELECT A .item_name
        FROM vgt_hdi.public_items A 
        WHERE A .item_name = '%s' 
        """ % strJOB
        dataVal = M.SELECT_DIC (dbc, sql)
        return dataVal

    def getBackDrillDepth(self, M, dbc, strJOB):
        '''
        获取inplan中的背钻深度，20200423更改获取的栏位为ERP的备注项目
        :param M:
        :param dbc:
        :param strJOB:
        :return:
        '''
        sql = """select a.item_name job_name_,
        c.item_name layer_name_,
        decode(d.drill_technology,1,'Controll Depth',5,'Countersink',6,'Counterbore',7,'Backdrill') as drill_type,
        f.name tnum,
        e.drill_layer_ drill_combine_layer,
        ROUND(f.finished_size/39.37,4) as finished_size,
        ROUND(f.actual_drill_size/39.37,4) as actual_drill_size,
        decode(f.type,4,'Plated Slot',0,'PTH',1,'Via',2,'NPTH',3,'Micro Via',5,'Non-Plated Slot') as hole_type,
        ROUND(g.BACK_DRILL_FOR_THROUGH_HOLE_/39.37,4) as BKDRL_THROUGH_HOLE_,
        g.DRILL_TOL_,
        ROUND(e.VONDER_DRILL_DEPTH_/39.37,4) as VONDER_DRL_DEPTH_,
        d.start_index,
        e.non_drill_layer_,
        d.end_index,
        ROUND(e.cus_drill_depth_/39.37,4) as cus_drill_depth_,
        ROUND(e.stub_drill_depth_/39.37,4) as stub_drill_depth_,
        f.pcb_count,
        g.hole_qty_,
        h.VALUE as set_hole_type_,
        --g.drill_notes_
        g.erp_finish_size_,
        g.is_addi_hole_,
        g.BIT_NAME_
        from vgt_hdi.items a
        inner join vgt_hdi.job b  on a.item_id = b.item_id  and  a.last_checked_in_rev = b.revision_id
        inner join vgt_hdi.public_items c  on a.root_id = c.root_id
        inner join vgt_hdi.drill_program d  on c.item_id = d.item_id and c.revision_id = d.revision_id
        inner join vgt_hdi.drill_program_da e on d.item_id = e.item_id  and d.revision_id = e.revision_id
        inner join vgt_hdi.drill_hole f   on d.item_id = f.item_id    and d.revision_id = f.revision_id
        inner join vgt_hdi.drill_hole_da g   on f.item_id = g.item_id    and f.revision_id = g.revision_id  and f.sequential_index=g.sequential_index
        left join vgt_hdi.enum_values h on g.set_hole_type_ = h.enum and h.enum_type = '1042'
        and  g.set_hole_type_ = h.enum
        and h.enum_type = '1042'
        where  d.drill_technology in (1,5,6,7) and a.item_name = upper('%s')  
        order by c.item_name,f.name""" % strJOB
        dataVal = M.SELECT_DIC (dbc, sql)
        return dataVal

    def getJobMatrix(self):
        # add for test
        # signalLayers = ['l1', 'l2', 'l3', 'l4', 'l5', 'l6', 'l7', 'l8']
        # topDrlList = []
        # botDrlList = []
        # innDrlList = []
        # return signalLayers,topDrlList,botDrlList,innDrlList
        # test End
        getInfo = GEN.DO_INFO ('-t matrix -e  %s/matrix' % self.job_name)
        numCount = len (getInfo['gROWname'])
        rType = getInfo['gROWlayer_type']
        rName = getInfo['gROWname']
        rContext = getInfo['gROWcontext']
        signalLayers = []
        topDrlList = []
        botDrlList = []
        innDrlList = []
        # 获取信号层列表
        for x in range (numCount):
            if rContext[x] == 'board' and (re.match (r'l[0-9]{1}', rName[x]) or re.match (r'l[0-9]{2}', rName[x])):
                if rType[x] == 'signal':
                    signalLayers.append (rName[x])
            if rContext[x] == 'board' and rType[x] == 'drill':
                if re.match (r'[bc]dc', rName[x]):
                    topDrlList.append (rName[x])
                elif re.match (r'[bc]ds', rName[x]):
                    botDrlList.append ((rName[x]))
                elif re.match (r'[bc]d[0-9]', rName[x]):
                    innDrlList.append ((rName[x]))
        return signalLayers, topDrlList, botDrlList, innDrlList

    def GOPEN_STEP(self, step, job=os.environ.get ('JOB', None)):
        if 'INCAM_SERVER' in os.environ.keys ():
            GEN.COM ("set_step, name = %s" % step)
            GEN.COM ("open_group, job = %s, step = %s, is_sym = no" % (job, step))
            GEN.AUX ("set_group, group = %s" % GEN.COMANS)
            GEN.COM ("open_entity, job = %s, type = step, name = %s, iconic = no" % (job, step))
            status = GEN.STATUS
            return status
        else:
            GEN.COM ('open_entity, job=%s, type=step, name=%s ,iconic=no' % (job, step))
            GEN.AUX ('set_group, group=%s' % GEN.COMANS)
            status = GEN.STATUS
            return status

    def input_method(self,drlpath,job_name,step_name,inputlayername):
        GEN.COM('input_manual_reset')
        GEN.COM('input_manual_set,path=%s,job=%s,step=%s,format=Excellon2,data_type=ascii,\
            units=mm,coordinates=absolute,zeroes=trailing,nf1=3,nf2=3,decimal=no,\
            separator=nl,tool_units=mm,layer=%s,wheel=,wheel_template=,\
            nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,\
            break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3'
                % (drlpath,job_name,step_name,inputlayername))
        GEN.COM('input_manual,script_path=')
        GEN.COM('display_layer,name=%s,display=yes,number=2' % inputlayername)
        GEN.COM('work_layer,name=%s' % inputlayername )

    def exist4cor(self,iplayer):
        val = GEN.INFO ('-t layer -e %s/%s/%s -m display -d FEATURES' % (self.job_name, self.opStep, iplayer))
        if len(val) != 5:
            showText = self.msgText (u'提示', u'层别%s,钻孔数量不是4个，不能进行ccd输出！' % (iplayer), showcolor='red')
            self.msgBox (showText)
            self.ui.checkBox.click()
            return False
        else:
            return val
        # print json.dumps (val, sort_keys=True, indent=2, separators=(',', ': '))

    def write_ccd_file(self,mode,layer):
        # TODO 判断ccd层别的类型,获取层别坐标
        fourCor = self.exist4cor(layer)
        corWord = self.dealwith4Cor(fourCor)
        mode_word = ''
        if mode == 'drl':
            mode_word  = 'M47,\P:M01,I1,D3.175,T*CIRCLE*\n'
        elif mode == 'mark':
            mode_word = 'M47,\P:M01,I0,D2.0,T*CIRCLE*\n'
        ccdwords = 'M47,\P:M16,M2\n%s%sM47,\P:M99,K1,S1M09\n' % (mode_word, corWord)
        return ccdwords

    def dealwith4Cor(self,fourCor):
        corword = ''
        for i in range(len(fourCor)):
            if re.match('#P',fourCor[i]):
                print fourCor[i]
                Xcor = '%.3f' % float(fourCor[i].split(' ')[1])
                Ycor = '%.3f' % float(fourCor[i].split(' ')[2])

                print '%s,%s' % (Xcor, Ycor)
                x1 = Xcor.split('.')[0].zfill (3)
                x2 = Xcor.split('.')[1]

                y1 = Ycor.split ('.')[0].zfill (3)
                y2 = Ycor.split ('.')[1]

                corword += 'X%s%sY%s%s\n' % (x1,x2,y1,y2)
                print corword
        return corword

class MainWindowShow (QtGui.QWidget, MainbackOutput, M_Box):
    """
    窗体主方法
    """

    def __init__(self, parent=None):
        QtGui.QWidget.__init__ (self, parent)
        MainbackOutput.__init__ (self)

        M_Box.__init__ (self)
        self.ui = FormUi.Ui_MainWindow ()
        self.ui.setupUi (self)
        self.addUiDetail ()

    def addUiDetail(self):
        """
        在原框架基础上继续加载窗体
        :return:None
        """
        self.ui.bottomLabel.setText (
            _translate ("MainWindow", "版权所有：胜宏科技 版本：%s 作者：Chao.Song 日期：2020.3.16" % (self.appVer), None))
        self.ui.comboBox.addItem ((self.opStep))
        if len (self.topDrlList) == 0:
            self.ui.groupBox_2.hide ()
        else:
            self.ui.listWidget_top.addItems (self.topDrlList)
        if len (self.botDrlList) == 0:
            self.ui.groupBox_3.hide ()
        else:
            self.ui.listWidget_bot.addItems (self.botDrlList)
        if len (self.innDrlList) == 0:
            self.ui.groupBox_4.hide ()
        else:
            self.ui.listWidget_inn.addItems (self.innDrlList)
        # 限定两个拉伸框的输入值 (0.99980,1.00019)
        my_regex = QtCore.QRegExp ("^0\.999[8-9][0-9][0-9]?|^1\.000[01][0-9][0-9]?")
        my_validator = QtGui.QRegExpValidator (my_regex, self.ui.lineEdit)
        self.ui.lineEdit.setValidator (my_validator)
        my_validator = QtGui.QRegExpValidator (my_regex, self.ui.lineEdit_2)
        self.ui.lineEdit_2.setValidator (my_validator)

        # 定义其他信号
        QtCore.QObject.connect (self.ui.pushButton_close, QtCore.SIGNAL ("clicked()"), self.close)
        QtCore.QObject.connect(self.ui.checkBox,QtCore.SIGNAL("clicked()"), self.checkccd)

        # 填写值更改的信号
        QtCore.QObject.connect (self.ui.pushButton_run, QtCore.SIGNAL ("clicked()"), self.MAIN_RUN)

    def getMainWindowData(self):
        allOpData = {'uistep': '',
                     'topOpLayers': [],
                     'botOpLayers': [],
                     'innOpLayers': [],
                     'xscale': '',
                     'yscale': '',
                     'xscale_o': '',
                     'yscale_o': '',
                     'scalemode': ''}
        allOpData['uistep'] = str (self.ui.comboBox.currentText ())

        toplist = self.ui.listWidget_top.selectedItems ()
        for i in toplist:
            allOpData['topOpLayers'].append (str (i.text ()))
        botlist = self.ui.listWidget_bot.selectedItems ()
        for i in botlist:
            allOpData['botOpLayers'].append (str (i.text ()))
        innlist = self.ui.listWidget_inn.selectedItems ()
        for i in innlist:
            allOpData['innOpLayers'].append (str (i.text ()))
        if len (toplist) + len (botlist) + len (innlist) == 0:
            showText = self.msgText (u'警告', u"'未选择输出层别!")
            self.msgBox (showText)
            return False

        allOpData['xscale'] = str (self.ui.lineEdit.text ())
        allOpData['yscale'] = str (self.ui.lineEdit_2.text ())

        if self.ui.comboBox_2.currentText () == u'原点':
            allOpData['scalemode'] = 'orig'
            allOpData['xscale_o'] = '0'
            allOpData['yscale_o'] = '0'
        elif self.ui.comboBox_2.currentText () == u'中心':
            # todo 写或者输出step中心值的方法
            profx, profy = GEN.GET_PROFILE_SIZE (job=self.job_name, step=allOpData['uistep'])
            allOpData['scalemode'] = 'center'
            allOpData['xscale_o'] = float (profx) * 0.5
            allOpData['yscale_o'] = float (profy) * 0.5
        return allOpData

    def checkccd(self):
        if self.ui.checkBox.isChecked():
            if len (self.topDrlList) != 0:
                if GEN.LAYER_EXISTS('ccdc',job=self.job_name,step=self.opStep) == 'no':
                    showText = self.msgText (u'警告', u'ccdc层别不存在不能勾选CCD输出！' )
                    self.msgBox (showText)
                    self.ui.checkBox.setChecked(False)
                    return
                else:
                    self.exist4cor('ccdc')

            if len (self.botDrlList) != 0:
                if GEN.LAYER_EXISTS('ccds',job=self.job_name,step=self.opStep) == 'no':
                    showText = self.msgText (u'警告', u'ccds层别不存在不能勾选CCD输出！' )
                    self.msgBox (showText)
                    self.ui.checkBox.setChecked(False)
                    return
                else:
                    self.exist4cor('ccds')
            if len (self.innDrlList) != 0:
                if GEN.LAYER_EXISTS('ccdi',job=self.job_name,step=self.opStep) == 'no':
                    showText = self.msgText (u'警告', u'ccdi层别不存在不能勾选CCD输出！' )
                    self.msgBox (showText)
                    self.ui.checkBox.setChecked(False)
                    return
                else:
                    self.exist4cor('ccdi')
        # 激活comb
        if self.ui.checkBox.isChecked():
            self.ui.comboBox_ccd.setEnabled(True)
        elif not self.ui.checkBox.isChecked():
            self.ui.comboBox_ccd.setEnabled(False)




    def MAIN_RUN(self):
        self.outputDic = self.getMainWindowData ()
        myOpLayers = ''
        if self.outputDic:
            self.close ()
            B = outputDrill ()
            B.job_name = self.job_name
            B.op_step =  self.outputDic['uistep']
            B.xScale =  self.outputDic['xscale']
            B.yScale =  self.outputDic['yscale']
            B.xscale_o =  self.outputDic['xscale_o']
            B.yscale_o =  self.outputDic['yscale_o']
            if self.ui.comboBox_ccd.currentText() == u'钻孔':
                self.ccdmode = 'drl'
            elif self.ui.comboBox_ccd.currentText() == u'Mark':
                self.ccdmode = 'mark'
            else:
                showText = self.msgText (u'提示', u'获取CCD模式失败！', showcolor='red')
                self.msgBox (showText)
                exit(0)
            if not self.ui.checkBox.isChecked ():
                self.ccdcwords = None
                self.ccdswords = None
                self.ccdiwords = None
            if len(self.outputDic['topOpLayers']) != 0 and self.ui.checkBox.isChecked():
                self.ccdcwords = self.write_ccd_file(self.ccdmode,'ccdc')


            for sel_oplayer in  self.outputDic['topOpLayers']:
                B.op_layer = sel_oplayer
                myOpLayers = myOpLayers+','+sel_oplayer
                B.version = 1
                opVersion = 1
                B.mirror = 'no'
                # getOPData = B.OutputProcess()
                # self.Detail_data = [
                #     {'T':'T01',"Tool":'C3.175','Depth':'0'},
                #     {'T':'T02',"Tool":'C0.002','Depth':'0.1'},
                #     {'T': 'T03', "Tool": 'C0.020', 'Depth': None},
                #     {'T': 'T04', "Tool": 'C0.040', 'Depth': 33}
                # ]
                # 输出完成后，排刀序及添加深度
                ddetail_data, headwords, outfile = B.OutputProcess ()
                # print json.dumps (ddetail_data, sort_keys=True, indent=2, separators=(',', ': '))
                if re.search('inn',sel_oplayer):
                    opTable = TableWindowShow (ddetail_data, headwords, outfile, opVersion, None)
                    opTable.exec_ ()
                else:
                    opTable = TableWindowShow (ddetail_data, headwords, outfile, opVersion, self.ccdcwords)
                    opTable.exec_ ()
                MainbackOutput.input_method(self,outfile,self.job_name, self.outputDic['uistep'],self.job_name+sel_oplayer)

            if len(self.outputDic['botOpLayers']) != 0 and self.ui.checkBox.isChecked():
                self.ccdswords = self.write_ccd_file(self.ccdmode,'ccds')

            for sel_oplayer in  self.outputDic['botOpLayers']:
                B.op_layer = sel_oplayer
                myOpLayers = myOpLayers + ',' + sel_oplayer

                B.version = 1
                B.mirror = 'no'
                opVersion = 4

                # 输出完成后，排刀序及添加深度
                ddetail_data, headwords, outfile = B.OutputProcess ()
                print json.dumps (ddetail_data, sort_keys=True, indent=2, separators=(',', ': '))
                if re.search('inn',sel_oplayer):
                    opTable = TableWindowShow (ddetail_data, headwords, outfile, opVersion, None)
                    opTable.exec_ ()
                else:
                    opTable = TableWindowShow (ddetail_data, headwords, outfile, opVersion, self.ccdswords)
                    opTable.exec_ ()
                MainbackOutput.input_method(self,outfile,self.job_name, self.outputDic['uistep'],self.job_name+sel_oplayer)

            if len(self.outputDic['innOpLayers']) != 0 and self.ui.checkBox.isChecked():
                self.ccdiwords = self.write_ccd_file(self.ccdmode,'ccdi')

            for sel_oplayer in  self.outputDic['innOpLayers']:
                B.op_layer = sel_oplayer
                myOpLayers = myOpLayers + ',' + sel_oplayer
                # TODO 暂定为第一象限输出不镜像
                B.version = 1
                B.mirror = 'no'
                # B.version = 4
                # B.mirror = 'no'
                opVersion = 4
                m = re.search (r'[bc]d([0-9][0-9]?)-([0-9][0-9]?)', sel_oplayer)
                if m:
                    if int(m.group(1)) < int(m.group(2)):
                        opVersion = 1
                    elif int(m.group(1)) > int(m.group(2)):
                        opVersion = 4
                    else:
                        showText = self.msgText (u'提示', u'内层背钻钻带，层别%s,无法获取象限信息！' % (sel_oplayer), showcolor='red')
                        self.msgBox (showText)
                        exit(0)
                else:
                    showText = self.msgText (u'提示', u'内层背钻钻带，层别%s,不符合命名规则！' % (sel_oplayer), showcolor='red')
                    self.msgBox (showText)
                    exit(0)
                # 输出完成后，排刀序及添加深度
                ddetail_data, headwords, outfile = B.OutputProcess ()
                print json.dumps (ddetail_data, sort_keys=True, indent=2, separators=(',', ': '))
                if re.search('inn',sel_oplayer):
                    opTable = TableWindowShow (ddetail_data, headwords, outfile, opVersion, None)
                    opTable.exec_ ()
                else:
                    opTable = TableWindowShow (ddetail_data, headwords, outfile, opVersion, self.ccdiwords)
                    opTable.exec_ ()

                MainbackOutput.input_method(self,outfile,self.job_name, self.outputDic['uistep'],self.job_name+sel_oplayer)

        showText = self.msgText (u'提示', u'背钻输出完成，层别%s！'% (myOpLayers), showcolor='green')
        self.msgBox (showText)
        exit (0)



class TableWindowShow (QtGui.QDialog, MainbackOutput, M_Box):
    """
    窗体主方法
    """

    def __init__(self, Detail_data, headwords, outfile, opVersion,ccdwords,paidaowords):
        # MainWindow = QtGui.QMainWindow ()
        super (TableWindowShow, self).__init__ ()
        # QtGui.QWidget.__init__ (self, None)
        MainbackOutput.__init__ (self)
        M_Box.__init__ (self)
        BO = MainbackOutput()
        self.Detail_data = Detail_data
        self.headwords = headwords
        self.outfile = outfile
        self.opVersion = opVersion
        self.ccdwords = ccdwords
        self.paidaowords = paidaowords
        
        self.first_click = 3
        # Detail_data = [
        #     {'T':'T01',"Tool":'C3.175','Depth':'0',Coord,''},
        #     {'T':'T02',"Tool":'C0.002','Depth':'0.1',Coord,''},
        #     {'T': 'T03', "Tool": 'C0.020', 'Depth': None,Coord,''},
        #     {'T': 'T04', "Tool": 'C0.040', 'Depth': 33,Coord,''}
        # ]

        inplanBkDrlData = BO.getInPlanInfo(mode='drlDepth')
        # print json.dumps (inplanBkDrlData, sort_keys=True, indent=2, separators=(',', ': '))
        # print json.dumps (Detail_data, sort_keys=True, indent=2, separators=(',', ': '))
        # 通过在inplan中获取的数据，inplanBkDrlData与 Detail_data 对比
        # print json.dumps (self.Detail_data, sort_keys=True, indent=2, separators=(',', ': '))

        self.redealWithInplanData(inplanBkDrlData)
        # print json.dumps (self.Detail_data, sort_keys=True, indent=2, separators=(',', ': '))

        # 对inplan的值进行归类汇总，判断出同一种孔径大小（公差0.01）分布了几个T，如果为两个判断其中一个是否为测试孔，
        # exit(0)
        self.table = TableUi.Ui_Dialog ()
        self.table.setupUi (self)
        # MainWindow.show ()
        self.TableDetail ()

    def TableDetail(self):
        """
        在原框架基础上继续加载窗体
        :return:None
        """
        self.table.pushButton_up.setToolTip (
            u"""<html>
                   <body><p><span style=\" font-size:10pt\">往上移动</span></p></body>
               </html>""")
        self.table.pushButton_down.setToolTip (
            u"""<html>
                   <body><p><span style=\" font-size:10pt\">往下移动</span></p></body>
               </html>""")

        # self.tableWidget.setDragDropMode(QtGui.QAbstractItemView.InternalMove)

        self.table.label_title.setText (_translate ("MainWindow", "刀序排列及添加深度\n料号：%s " % (self.strJobName), None))
        self.table.label_filename.setText (_translate ("MainWindow", "输出路径：%s " % (self.outfile), None))

        self.table.bottomLabel.setText (
            _translate ("MainWindow", "版权所有：胜宏科技 版本：%s 作者：Chao.Song 日期：2020.3.16" % (self.appVer), None))

        # 如果传入的象限为空None，则认为是外部程序调用禁用排刀按钮
        if self.opVersion is None:
            self.table.pushButton_up.setDisabled(True)
            self.table.pushButton_down.setDisabled(True)
        self.table.tableWidget.setColumnCount (3)
        self.table.tableWidget.setRowCount (len (self.Detail_data))
        for index in range (len (self.Detail_data)):
            item = QtGui.QTableWidgetItem (str (self.Detail_data[index]['T']))
            item.setFlags (QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
            self.table.tableWidget.setItem (index, 0, item)
            item = QtGui.QTableWidgetItem (str (self.Detail_data[index]['Tool']))
            item.setFlags (QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
            self.table.tableWidget.setItem (index, 1, item)
            item = QtGui.QTableWidgetItem (str (self.Detail_data[index]['Depth']))
            self.table.tableWidget.setItem (index, 2, item)

        # 定义其他信号
        QtCore.QObject.connect (self.table.pushButton_close, QtCore.SIGNAL ("clicked()"), self.close)
        QtCore.QObject.connect (self.table.tableWidget, QtCore.SIGNAL ("cellChanged(int, int)"), self.cellChange)

        # 填写值更改的信号
        QtCore.QObject.connect (self.table.pushButton_run, QtCore.SIGNAL ("clicked()"), self.Deal_file)
        self.connect (self.table.pushButton_up, QtCore.SIGNAL ('clicked()'), self.Apply_UP)
        self.connect (self.table.pushButton_down, QtCore.SIGNAL ('clicked()'), self.Apply_Down)

    # --向上移动数据
    def Apply_UP(self):
        row = self.table.tableWidget.currentRow ()
        column = self.table.tableWidget.columnCount ()
        if row >= 1:
            # 获取当前行数据
            current_data = []
            for x in range (column):
                current_data.append (str (self.table.tableWidget.item (row, x).text ()))
            self.table.tableWidget.removeRow (row)
            self.table.tableWidget.insertRow (row - 1)
            for x in range (column):
                item = QtGui.QTableWidgetItem (str (current_data[x]))
                if x != 2:
                    item.setFlags (QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
                self.table.tableWidget.setItem (row - 1, x, item)

    # --向上移动数据
    def Apply_Down(self):
        row = self.table.tableWidget.currentRow ()
        all_row = self.table.tableWidget.rowCount ()
        column = self.table.tableWidget.columnCount ()

        if row < all_row - 1:
            current_data = []
            for x in range (column):
                current_data.append (str (self.table.tableWidget.item (row, x).text ()))
            self.table.tableWidget.removeRow (row)
            self.table.tableWidget.insertRow (row + 1)

            for x in range (column):
                item = QtGui.QTableWidgetItem (str (current_data[x]))
                if x != 2:
                    item.setFlags (QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
                self.table.tableWidget.setItem (row + 1, x, item)

    def cellChange(self):
        # --先断开信号的连接,以免在下面再次修改item时发生递归死循环事件发生
        QtCore.QObject.disconnect (self.table.tableWidget, QtCore.SIGNAL ("cellChanged(int, int)"), self.cellChange)
        # --循环所有层并加入行
        # --获取完成铜厚 （直接从itemWidget中获取）
        items = self.table.tableWidget.selectedItems ()
        if len (items) == 0:
            # --退出前，再次启动信号连接
            # self.ui.connect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"), self.cellChange)
            QtCore.QObject.connect (self.table.tableWidget, QtCore.SIGNAL ("cellChanged(int, int)"),
                                    self.cellChange)
            return
        # --获取选中的行信息，行号，列号
        selRow = items[0].row ()
        selCol = items[0].column ()
        try:
            selText = str (items[0].text ())
        except UnicodeEncodeError:
            showText = self.msgText (u'警告', u"'第%d行%d列' 深度值非数字，请修改!" % (
                selRow + 1, selCol + 1))
            self.msgBox (showText)
            self.table.tableWidget.item (selRow, selCol).setForeground (QtGui.QBrush (QtGui.QColor (255, 0, 0)))
            QtCore.QObject.connect (self.table.tableWidget, QtCore.SIGNAL ("cellChanged(int, int)"),
                                    self.cellChange)
            return False
        item_text = self.table.tableWidget.item (selRow, selCol).text ()

        # --获取选择行的完成铜厚信息
        try:
            finishComp = float (item_text)
            # print finishComp
            if finishComp < 0:
                showText = self.msgText (u'警告', u"'第%d行%d列' 深度值 '%s' 不是正数，请修改!" % (
                    selRow + 1, selCol + 1, item_text))
                self.msgBox (showText)
                self.table.tableWidget.item (selRow, selCol).setForeground (QtGui.QBrush (QtGui.QColor (255, 0, 0)))

                QtCore.QObject.connect (self.table.tableWidget, QtCore.SIGNAL ("cellChanged(int, int)"),
                                        self.cellChange)
                return False

        except ValueError:
            # Mess = msgBox.Main ()
            showText = self.msgText (u'警告', u"第%d行%d列 深度值 %s 不是有效数字，请修改!" % (
                selRow + 1, selCol + 1, item_text))
            self.table.tableWidget.item (selRow, selCol).setForeground (QtGui.QBrush (QtGui.QColor (255, 0, 0)))

            self.msgBox (showText)
            # --退出前，再次启动信号连接
            # self.ui.connect(self.ui.tableWidget_LyrList, QtCore.SIGNAL("cellChanged(int, int)"), self.cellChange)
            QtCore.QObject.connect (self.table.tableWidget, QtCore.SIGNAL ("cellChanged(int, int)"),
                                    self.cellChange)
            return False
            # --重新更新UI数据
        # --退出前，再次启动信号连接
        QtCore.QObject.connect (self.table.tableWidget, QtCore.SIGNAL ("cellChanged(int, int)"), self.cellChange)

    def redealWithInplanData(self,inplanData):
        # 模型
        # [
        #     {
        #         "ACTUAL_DRILL_SIZE": 0.5,
        #         "BKDRL_THROUGH_HOLE_": 0,
        #         "CUS_DRILL_DEPTH_": 1.1000000000000001,
        #         "DRILL_NOTES_": "\u63a7\u6df1\u6df1\u5ea6\u6d4b\u8bd5\u5b54",
        #         "DRILL_TOL_": "/",
        #         "DRILL_TYPE": "Controll Depth",
        #         "END_INDEX": 2,
        #         "FINISHED_SIZE": 0.5,
        #         "HOLE_QTY_": 2,
        #         "HOLE_TYPE": "NPTH",
        #         "JOB_NAME_": "H20504GI005A2",
        #         "LAYER_NAME_": "cd4-2",
        #         "NON_DRILL_LAYER_": 3,
        #         "PCB_COUNT": 0,
        #         "START_INDEX": 4,
        #         "STUB_DRILL_DEPTH_": 0,
        #         "TNUM": "T01",
        #         "VONDER_DRL_DEPTH_": 1.25
        #     }
        # ]
        # 有效键 TNUM "ACTUAL_DRILL_SIZE": 0.5,"DRILL_NOTES_" "VONDER_DRL_DEPTH_": 1.25
        # 不考虑排刀的情况下，以实际钻孔大小确认背钻的深度。以钻孔孔径为key 内容为深度，出现次数
        # 20200423 根据周涌提供的规则，当备注栏里出现了以下字样，认为为通孔
        # 印刷对位孔-通孔，限位孔-通孔，工艺边上孔-通孔，控深漏钻检测孔-通孔；料号孔-通孔，批号孔-通孔
        # === 2020.06.09 增加 背钻可视孔 ===
        drill_combine_layer_type = []
        drill_combine_layer = None
        # if "-lyh" in self.job_name:
        
        # 增加一面多次背钻的情况 需手动选择其中一次来获取深度 20240313 by lyh
        for i in range(len(inplanData)):
            
            if inplanData[i]['START_INDEX'] > self.job_layer_num / 2:
                if "bdc" in os.path.basename(self.outfile):
                    continue
                
            if inplanData[i]['START_INDEX'] < self.job_layer_num / 2:
                if "bds" in os.path.basename(self.outfile):
                    continue
            
            drill_combine_layer_type.append(inplanData[i]["DRILL_COMBINE_LAYER"].decode("utf8"))
            
        if len(set(drill_combine_layer_type)) > 1:
            showText = self.msgText (u'警告', u"检测到此面有多次背钻,请选择对应的一次进行控深深度对应获取！")
            self.msgBox (showText)
            
            items = [""] + list(set(drill_combine_layer_type))
            drill_combine_layer = ""
            while not drill_combine_layer:                
                item, okPressed = QtGui.QInputDialog.getItem(QtGui.QWidget(), u"提示", u"请选择输出背钻类型:",
                                                             items, 0, False, Qt.Qt.WindowStaysOnTopHint)
                
                drill_combine_layer = unicode(item.toUtf8(),'utf8', 'ignore').encode('utf8')          
                if not okPressed:
                    exit(1)  
    
        drillDepthDic = {}
        self.drillDepthDic_t_header = {}
        for i in range(len(inplanData)):
            
            if inplanData[i]['START_INDEX'] > self.job_layer_num / 2:
                if "bdc" in os.path.basename(self.outfile):
                    continue
                
            if inplanData[i]['START_INDEX'] < self.job_layer_num / 2:
                if "bds" in os.path.basename(self.outfile):
                    continue
                
            if drill_combine_layer is not None and inplanData[i]["DRILL_COMBINE_LAYER"] != drill_combine_layer:
                continue
            
            change_depth = ''
            drillSize = round(inplanData[i]['ACTUAL_DRILL_SIZE'], 3)
            through_note = ['曝光对位孔', '印刷对位孔', '限位孔', '工艺边上孔', '控深漏钻检测孔','控深漏钻监测孔',
                            '料号孔', '批号孔', '工艺边定位孔', '背钻漏钻监测孔', '背钻可视孔', 'HCT coupon定位孔',
                            '料号孔和批号孔','通孔HCT定位','通孔', '定位孔']
            if inplanData[i]['ERP_FINISH_SIZE_']:
                through_list = [t for t in through_note if t in inplanData[i]['ERP_FINISH_SIZE_']]
                if len(through_list) != 0:
                    change_depth = 0
            
            # 重新判断 按inplan提供新的逻辑 20240220 by lyh
            """if {DRILL_PROGRAM.DRILL_TECHNOLOGY} = "Backdrill" and {DRILL_HOLE_1.IS_ADDI_HOLE_} = false 
            then 显示厂内深度
            else if instr({DRILL_HOLE_1.ERP_FINISH_SIZE_},'深度测试孔')>0
            then 显示厂内深度
            else if  {DRILL_PROGRAM.DRILL_TECHNOLOGY} = "Controlled Depth" and {DRILL_HOLE_1.PCB_COUNT} > 0
            and (instr({DRILL_HOLE_1.ERP_FINISH_SIZE_},'控深')>0 or  instr({DRILL_HOLE_1.ERP_FINISH_SIZE_},'平头')>0
            or {DRILL_HOLE_1.SET_HOLE_TYPE_} = '控深普通钻咀' or {DRILL_HOLE_1.SET_HOLE_TYPE_} = '控深平头钻咀')
            then 显示厂内深度
            else  '/'"""
            #增加二钻合并背钻的情况 20241010 by lyh
            """DRILL_TECHNOLOGY = 'Backdrill' and (./@PCB_COUNT != 0 or ./@IS_ADDI_HOLE_ = 'false') and  ./@SET_HOLE_TYPE_ != '通孔(合并钻)'"""
            # GEN.PAUSE("{0} {1} {2} {3}".format(inplanData[i]['DRILL_TYPE'], inplanData[i]['PCB_COUNT'], inplanData[i]['ERP_FINISH_SIZE_'], inplanData[i]['SET_HOLE_TYPE_']))
            if inplanData[i]['DRILL_TYPE'] == "Backdrill" and inplanData[i]['IS_ADDI_HOLE_'] == 0 and \
               (inplanData[i]['SET_HOLE_TYPE_'] and inplanData[i]['SET_HOLE_TYPE_'] not in ["通孔(合并钻)"]):
                change_depth = ""                
            elif inplanData[i]['ERP_FINISH_SIZE_'] and "深度测试孔" in inplanData[i]['ERP_FINISH_SIZE_']:
                change_depth = ""
            elif inplanData[i]['DRILL_TYPE'] == "Controll Depth" and inplanData[i]['PCB_COUNT'] > 0 and \
                 ((inplanData[i]['ERP_FINISH_SIZE_'] and ("控深" in inplanData[i]['ERP_FINISH_SIZE_'] or "平头" in inplanData[i]['ERP_FINISH_SIZE_'])) or \
                   (inplanData[i]['SET_HOLE_TYPE_'] and inplanData[i]['SET_HOLE_TYPE_'] in ["控深平头钻咀" , "控深普通钻咀"])):
                change_depth = ""
            else:
                change_depth = 0
            
            # 定义刀头对应的深度
            if change_depth == "":
                self.drillDepthDic_t_header[inplanData[i]['BIT_NAME_']] = inplanData[i]['VONDER_DRL_DEPTH_']
                
            # 更改限位孔ERP尺寸为0.45，对应钻带为0.452,料号孔ERP尺寸为0.45，对应钻带为0.452，批号孔ERP尺寸为0.45，对应钻带为0.46
            if abs(drillSize - 0.45) < 0.0001 and inplanData[i]['ERP_FINISH_SIZE_'] == '限位孔':
                drillSize = 0.452
            if abs(drillSize - 0.45) < 0.0001 and inplanData[i]['ERP_FINISH_SIZE_'] == '料号孔':
                drillSize = 0.452
            if abs(drillSize - 0.45) < 0.0001 and inplanData[i]['ERP_FINISH_SIZE_'] == '批号孔':
                drillSize = 0.46
            # === 2020.01.08 增加料号孔和批号孔合刀的情况 ===
            if abs(drillSize - 0.45) < 0.0001 and inplanData[i]['ERP_FINISH_SIZE_'] == '料号孔和批号孔':
                drillSize = 0.46
            # ==2020.04.28 Song==
            # 增加控深深度测试孔的深度添加判断，当备注信息为控深深度测试孔，在inplan的钻咀信息的钻径大小上减0.001
            if inplanData[i]['ERP_FINISH_SIZE_']:
                if inplanData[i]['ERP_FINISH_SIZE_'] == '控深深度测试孔' \
                        or inplanData[i]['ERP_FINISH_SIZE_'] == '背钻深度测试孔' \
                        or inplanData[i]['ERP_FINISH_SIZE_'] == '背钻对准测试孔'\
                        or inplanData[i]['ERP_FINISH_SIZE_'] == '深度测试孔控深深度测试孔'\
                        or '控深深度测试孔' in inplanData[i]['ERP_FINISH_SIZE_']:
                    drillSize = drillSize - 0.001

            # edit in 2020.05.13 in V1.2.3 change float -> str
            # print os.path.basename(self.outfile)
            drillSize = str(drillSize)
            if drillDepthDic.has_key(drillSize):
                if change_depth != '':
                    # print 1, [inplanData[i]['START_INDEX'], drillSize, change_depth, drillDepthDic[drillSize]['iDepth']]
                    if change_depth == drillDepthDic[drillSize]['iDepth']:
                        drillDepthDic[drillSize]['iTimes'] = drillDepthDic[drillSize]['iTimes'] + 1
                    else:
                        drillDepthDic[drillSize]['iDepth'] = 'NotSingleDrlDepth'
                        drillDepthDic[drillSize]['iTimes'] = drillDepthDic[drillSize]['iTimes'] + 1
                else:
                    # print 2,  [inplanData[i]['START_INDEX'], drillSize, inplanData[i]['VONDER_DRL_DEPTH_'], drillDepthDic[drillSize]['iDepth']]
                    if inplanData[i]['VONDER_DRL_DEPTH_'] == drillDepthDic[drillSize]['iDepth']:
                        drillDepthDic[drillSize]['iTimes'] = drillDepthDic[drillSize]['iTimes'] + 1
                    else :
                        drillDepthDic[drillSize]['iDepth'] = 'NotSingleDrlDepth'
                        drillDepthDic[drillSize]['iTimes'] = drillDepthDic[drillSize]['iTimes'] + 1
            else:
                if change_depth != '':
                    drillDepthDic[drillSize] = {'iDepth': change_depth, 'iTimes': 1}
                else:
                    drillDepthDic[drillSize] = {'iDepth': inplanData[i]['VONDER_DRL_DEPTH_'],
                                                                     'iTimes':1}
        # return drillDepthDic
        #if "-lyh" in self.job_name:
            #print "------------>111", json.dumps (drillDepthDic, sort_keys=True, indent=2, separators=(',', ': '))
            #print "------------>222",json.dumps (inplanData, sort_keys=True, indent=2, separators=(',', ': '))
            #sys.exit(1)
        # ==已经输出的钻带文件中的钻径大小比对，如果inplan中存在key，则带入深度值
        for d in range(len(self.Detail_data)):
            # edit in 2020.05.13 in V1.2.3 change float -> str
            checkSize = str(round(float(self.Detail_data[d]['Tool'][1:]),3))
            if drillDepthDic.has_key(checkSize):
                self.Detail_data[d]['Depth'] = drillDepthDic[checkSize]['iDepth']

        return True


    def getTableInfo(self):
        tableinfo = []
        # column = self.table.tableWidget.columnCount()
        all_row = self.table.tableWidget.rowCount ()
        for cur_row in range (all_row):
            curcolumn0 = str (self.table.tableWidget.item (cur_row, 0).text ())
            curcolumn1 = str (self.table.tableWidget.item (cur_row, 1).text ())
            curcolumn2 = str (self.table.tableWidget.item (cur_row, 2).text ())
            try:
                selText = str (curcolumn2)
            except UnicodeEncodeError:
                showText = self.msgText (u'警告', u"'第%d行' 深度值非数字，请修改!" % (cur_row + 1))
                self.msgBox (showText)
                return False

            # --获取选择行的完成铜厚信息
            try:
                finishComp = float (curcolumn2)
                if finishComp < 0:
                    showText = self.msgText (u'警告', u"'第%d行' 深度值 '%s' 不是正数，请修改!" % (cur_row + 1, curcolumn2))
                    self.msgBox (showText)
                    return False
            except ValueError:
                showText = self.msgText (u'警告', u"第%d行 深度值 %s 不是有效数字，请修改!" % (cur_row + 1, curcolumn2))
                self.msgBox (showText)
                return False
            
            if float(curcolumn2) > 0:
                if abs(float(curcolumn2) - float(self.drillDepthDic_t_header.get(curcolumn0, 0))) > 0.01:
                    showText = self.msgText (u'警告', u"第%d行 %s 深度值 %s 跟inplan 要求的深度 %s 不一致1，请修改!" % (cur_row + 1, curcolumn0, curcolumn2, self.drillDepthDic_t_header.get(curcolumn0)))
                    self.msgBox (showText)
                    return False
            else:
                if self.drillDepthDic_t_header.get(curcolumn0):
                    showText = self.msgText (u'警告', u"第%d行 %s 深度值 %s 跟inplan 要求的深度 %s 不一致2，请修改!" % (cur_row + 1, curcolumn0, curcolumn2, self.drillDepthDic_t_header.get(curcolumn0)))
                    self.msgBox (showText)
                    return False                    

            tableinfo.append ({'T': curcolumn0, 'Tool': curcolumn1, 'Depth': curcolumn2})
        
        #有控深钻时再检测下 控深跟通孔相同孔径 排序错误时 提醒用户核对 20240313 by lyh
        # if "-lyh" in self.job_name:
        # GEN.PAUSE(str([self.job_name, self.outfile]))
        if "cdc" in self.outfile or "cds" in self.outfile:            
            for t_info in tableinfo:
                if not float(t_info["Tool"][1:]) * 1000 % 10 and float(t_info["Depth"]) > 0:
                    # GEN.PAUSE(str(t_info))
                    for other_t_info in tableinfo:
                        # GEN.PAUSE(str([t_info, other_t_info]))
                        if abs(float(t_info["Tool"][1:]) * 1000 - float(other_t_info["Tool"][1:]) * 1000) < 10 and \
                           float(other_t_info["Depth"]) == 0:
                            if self.first_click:
                                log =  u"检测到控深钻 第{0}刀 跟{1}刀同孔径{2} 控深值应该在第{1}刀上 ,注意孔径相同需将尾数加在控深孔上区分，通孔不能有尾数，请检查刀序是否异常，请确认{3}!"
                                showText = self.msgText (u'警告',log.format(t_info["T"], other_t_info["T"], t_info["Tool"][1:], self.first_click))
                                self.msgBox (showText)
                          
                                # self.first_click -= 1
                                return False
                        
        return tableinfo

    def Deal_file(self):
        # 再次检查输入的深度值是否正确
        TargetInfo = self.getTableInfo ()
        if TargetInfo:
            self.close ()
            # print json.dumps (TargetInfo, sort_keys=True, indent=2, separators=(',', ': '))
            # --判断修改文件是否存在
            # --再次检查或写入WIN目录文件时，需要转为GBK字集，因为可能存在中文目录
            new_file = str (self.outfile).decode ('UTF-8').encode ('GBK')
            # print new_file
            if os.path.exists (new_file):
                os.unlink (new_file)
            # --打印出文件头"%"前面部分
            f = open (new_file, 'a')
            if self.headwords:
                f.write (self.headwords + '\n')
            # 应用TOPCAM的外挂程序，没有象限传入，进行判断，没有象限传入时，不写入象限
            if self.opVersion is not None:
                f.write ('VER:'+ str(self.opVersion) + '\n')

            # --循环列表中的信息，打印出T-CODE部分
            for i in range (len (TargetInfo)):
                # --取出指定行信息
                if i <= 8:
                    new_code = 'T0' + str (i + 1) + TargetInfo[i]['Tool']
                else:
                    new_code = 'T' + str (i + 1) + TargetInfo[i]['Tool']
                # --从头开始打印
                f.write (new_code + '\n')
            # === 2020.09.01 写入排刀
            if self.paidaowords:
                f.write (self.paidaowords+'\n')
            # --写入‘%“
            f.write ('%\n')
            if self.ccdwords:
                f.write (self.ccdwords)

            # --再次循环写入坐标
            for i in range (len (TargetInfo)):
                if i <= 8:
                    new_code = 'T0' + str (i + 1)
                else:
                    new_code = 'T' + str (i + 1)
                # --从头开始打印
                f.write (new_code + '\n')
                if TargetInfo[i]['Depth'] != '0':
                    #不能为整数形式，修改为浮点数形式 http://192.168.2.120:82/zentao/story-view-8053.html
                    f.write ('M18Z' + str(float(TargetInfo[i]['Depth'])) + '\n')

                beforeT = str (TargetInfo[i]['T'])
                getbeforeCor = 'no'
                for j in range (len (self.Detail_data)):
                    if self.Detail_data[j]['T'] == beforeT:
                        f.write (self.Detail_data[j]['Coord'] + '\n')
                        getbeforeCor = 'yes'
                if getbeforeCor == 'no':
                    return False
                if TargetInfo[i]['Depth'] != '0':
                    f.write ('M19\n')

            # --写入最后一行停止信息“M30”结尾
            f.write ('M30' + '\n')
            f.close ()
            return True


# # # # --程序入口
if __name__ == "__main__":
    app = QtGui.QApplication (sys.argv)
    myapp = MainWindowShow ()
    myapp.show ()

    app.exec_ ()
    sys.exit (0)


"""
宋超
2020.04.20
增加星号的输出支持，更改outputMain.py程序
宋超
V1.1.0
2020.04.23
1.增加背钻与通孔钻带合并的深度选项；
2.增加根据ERP备注项修改相应钻咀大小；
3.外部程序调用时,禁用排刀按钮。
4.更改获取inplan语句，获取与ERP相同备注项
http://192.168.2.120:82/zentao/story-view-817.html
宋超
V1.2.0
2020.04.28
1.增加试钻孔深度添加，增加控深深度测试孔的深度添加判断，当备注信息为控深深度测试孔，在inplan的钻咀信息的钻径大小上减0.001 
宋超
V1.2.1
2020.04.28
备注描述不同：已有控深漏钻检测孔，增加控深漏钻监测孔
宋超
V1.2.2
2020.05.09
增加“工艺边定位孔”为通孔条件
V1.2.3
2020.05.13
更改字典的key值为字符串
V1.2.4
2020.06.09
1 A10-004A3为背钻料号，程序增加背钻料号支持
1.1 增加 '背钻漏钻监测孔', '背钻可视孔'为通孔钻的条件
1.2 增加 '背钻深度测试孔'、'背钻对准测试孔'为实际钻孔 -1微米的条件

版本：V1.2.5
日期：2021.01.08
作者：Chao.Song
1.增加'HCT coupon定位孔'、'料号孔和批号孔'不增加背钻深度；

版本：V1.2.6
日期：2021.02.09
作者：Chao.Song
1.增加“通孔HCT定位”；

版本：V1.2.7
日期：2021.02.24
作者：Chao.Song
1.增加“通孔”；

"""

