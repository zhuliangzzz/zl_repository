#!/usr/bin/python
# -*- coding: UTF-8 -*-
# --------------------------------------------------------- #
#                VTG.SH SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    AresHe
# @Mail         :    502614708@qq.com
# @Date         :    2022.1.6
# @Revision     :    1.0.0
# @File         :    change_week.py
# @Software     :    PyCharm
# @Usefor       :
# --------------------------------------------------------- #

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
'''
                   _ooOoo_
                  o8888888o
                  88" . "88
                  (| -_- |)
                  O\  =  /O
               ____/`---'\____
             .'  \\|     |//  `.
            /  \\|||  :  |||//  \
           /  _||||| -:- |||||-  \
           |   | \\\  -  /// |   |
           | \_|  ''\---/''  |   |
           \  .-\__  `-`  ___/-. /
         ___`. .'  /--.--\  `. . __
      ."" '<  `.___\_<|>_/___.'  >'"".
     | | :  `- \`.;`\ _ /`;.`/ - ` : | |
     \  \ `-.   \_ __\ /__ _/   .-` /  /
======`-.____`-.___\_____/___.-`____.-'======
                   `=---='
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           佛祖保佑       永无BUG
'''

import platform, socket, getpass, time, sys, os, re, pprint

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genCOM_26 as genCOM
from PyQt4 import QtCore, QtGui
from messageBoxPro import msgBox
from ui.win import *
import ui.icon
import datetime
import time

import Oracle_DB

try:    
    from scriptsRunRecordLog import uploadinglog
except:
    pass

# --所有与ERP查询相关的全部写到ERP类中
class ERP():
    def __init__(self, job_name=None):
        self.job_name = job_name.upper()[0:13]
        # --Oracle相关参数定义
        self.DB_O = Oracle_DB.ORACLE_INIT()
        self.dbc_e = self.DB_O.DB_CONNECT(host='172.20.218.247', servername='topprod', port='1521',
                                          username='zygc', passwd='ZYGC@2019')
        if not self.dbc_e:
            # --sid连接模式
            self.DB_O = Oracle_DB.ORACLE_INIT(tnsName='sid')
            self.dbc_e = self.DB_O.DB_CONNECT(host='172.20.218.247', servername='topprod1', port='1521',
                                              username='zygc', passwd='ZYGC@2019')

    def __del__(self):
        # --关闭数据库连接
        if self.dbc_e:
            self.DB_O.DB_CLOSE(self.dbc_e)

    def get_client_name(self):
        """
        从InPlan中获取铜厚及层别正反的数据
        :return:sql后的字典
        """
        sql = """
                SELECT DISTINCT
                    A.TA_IMA01,
                    B.OCC02,
                    A.TA_IMA02,
                    C.TC_ABT03 
                FROM
                    s01.ima_file A,
                    S01.OCC_FILE B,
                    S01.tc_abt_file C 
                WHERE
                    A.TA_IMA01 = B.OCC01 
                    AND A.Ta_Ima61 = C.TC_ABT02 
                    AND A.ima01 = '%s'""" % self.job_name

        # --返回数据字典
        return self.DB_O.SQL_EXECUTE(self.dbc_e, sql)

class CHANGE_WEEK():
    def __init__(self):
        '''
        初始化类
        '''
        self.GEN = genCOM.GEN_COM()
        self.JOB = os.environ.get("JOB")
        self.STEP = os.environ.get("STEP")
        self.GENESIS_DIR = os.environ.get('GENESIS_DIR')
        
        # --创建ERP连接，获取客户料号
        gERP = ERP(self.JOB)
        self.client_name = gERP.get_client_name()        

        self.get_layer()
        self.show_win()
        self.slot_fun()
        self.get_week_info()
        self.set_week_info()

        # --设置周期区间在1-52
        self.ui.spinBox_2.setRange(1,52)
        
        self.change_week_text()

    def set_week_info(self):
        '''
        设置日期、周期信息
        :return:
        '''
        # --获取当前时间戳,并设定选中的日期
        i = datetime.datetime.now()
        # --年、月、日
        self.ui.calendarWidget.setSelectedDate(QtCore.QDate(i.year, i.month,i.day))
        self.ui.calendarWidget.setFirstDayOfWeek(QtCore.Qt.Sunday)

        # # --设定当前日期
        dateTime = self.ui.calendarWidget.selectedDate().getDate()
        self.ui.spinBox.setValue(int(str(dateTime[0])[2:]))
        # self.ui.lineEdit.setText(str(dateTime[0])[2:])

        # # --设定当前周期
        week = self.ui.calendarWidget.selectedDate().weekNumber()
        self.ui.spinBox_2.setValue(week[0])
        # self.ui.lineEdit_2.setText(str(week[0]))

        # --选中时触发calendarWidget事件
        self.ui.calendarWidget.clicked.connect(self.set_date)

        self.set_lcd(self.ui.label_4.text(),str(dateTime[0])[2:],str(week[0]))

        self.ui.spinBox_2.valueChanged[str].connect(self.change_spinbox)

    def change_spinbox(self):
        '''
        设置步长选择器
        :return:
        '''
        fromat = self.ui.label_4.text()
        year   = str(self.ui.spinBox.value())
        week   = str(self.ui.spinBox_2.value())

        if fromat == 'yyww':
            week_fromat = year + week
            if len(week) == 1:
                week_fromat = year + '0' + week
            self.ui.lcdNumber_3.display(week_fromat)
            
        if fromat == 'wwyy':
            week_fromat = week + year
            if len(week) == 1:
                week_fromat = '0' + week + year
            self.ui.lcdNumber_3.display(week_fromat)
            
        self.change_week_text()

    def set_date(self):
        '''
        设置年、周期标签显示栏
        :return:
        '''
        # --修改选中后日期
        dateTime =  self.ui.calendarWidget.selectedDate().getDate()
        self.ui.spinBox.setValue(int(str(dateTime[0])[2:]))
        # self.ui.lineEdit.setText(str(dateTime[0])[2:])

        # # --修改选中后周期
        week = self.ui.calendarWidget.selectedDate().weekNumber()
        self.ui.spinBox_2.setValue(week[0])
        # self.ui.lineEdit_2.setText(str(week[0]))

        self.set_lcd(self.ui.label_4.text(), str(dateTime[0])[2:], str(week[0]))
        
        self.change_week_text()

    def set_lcd(self,fromat,year,week):
        '''
        设置lcd显示
        :param fromat:格式
        :param year:年份
        :param week:周期
        :return:
        '''
        if fromat == 'yyww':
            week_fromat = year + week
            if len(week) == 1:
                week_fromat = year + '0' + week
            self.ui.lcdNumber_3.display(week_fromat)
            
        if fromat == 'wwyy':
            week_fromat = week + year
            if len(week) == 1:
                week_fromat = '0' + week + year
            self.ui.lcdNumber_3.display(week_fromat)

    def show_win(self):
        '''
        显示界面
        :return:
        '''
        self.Form = QtGui.QWidget()
        self.ui = Ui_Form()
        self.ui.setupUi(self.Form)
        self.Form.show()    
        
        #判断是否是A79 940 系列
        if self.JOB[1:4] in ["a79", "940"]:
            self.ui.week_group_box.show()
            if self.JOB[1:4] == "a79":
                self.ui.mA79_week_btn.setChecked(True)
            if self.JOB[1:4] == "940": 
                self.ui.m940_week_btn.setChecked(True)
        else:
            self.ui.no_week_btn.setChecked(True)
            self.ui.week_group_box.hide()

    def slot_fun(self):
        '''
        信号槽函数
        :return:
        '''
        self.ui.pushButton_2.clicked.connect(sys.exit)
        self.ui.pushButton.clicked.connect(self.start_run)
        
        self.ui.no_week_btn.clicked.connect(self.change_week_text)
        self.ui.mA79_week_btn.clicked.connect(self.change_week_text)
        self.ui.m940_week_btn.clicked.connect(self.change_week_text)
        
    def change_week_text(self):
        week = int(self.ui.lcdNumber_3.value())
        if week < 1000:
            week = '0' + str(week)
        else:
            week = str(week)
            
        if self.ui.no_week_btn.isChecked():
            self.ui.modify_week_editor.setText("")
            
        if self.ui.mA79_week_btn.isChecked():
            self.ui.modify_week_editor.setText("D{0};VLVGT4;".format(week))
            
        if self.ui.m940_week_btn.isChecked():            
            self.ui.modify_week_editor.setText("{0};VGT-VGT;{1}".format(self.client_name[0][2], week))        
        
    def start_run(self):
        """开始执行"""
        week = int(self.ui.lcdNumber_3.value())
        if week == 0:
            msg_box = msgBox()
            msg_box.warning(None, '提示信息', u'周期{0}格式错误，程序不能修改'.format(week), QtGui.QMessageBox.Yes)
            sys.exit(0)
            
        self.run_change()
        setzq = str(self.ui.modify_week_editor.text())
        if self.ui.mA79_week_btn.isChecked() or \
           self.ui.m940_week_btn.isChecked():
            barcode_type = "a79" if self.ui.mA79_week_btn.isChecked() else "940"
        else:
            barcode_type = "other"
            
        self.ChangeEwm(setzq, barcode_type, "set+flip")
        
        self.ChangeEwm(setzq, barcode_type, "set") 
            
    def ChangeEwm(self,setzq, barcode_type, set_stepname):
        """开始修改A79 940 系列周期 20221101 by lyh"""
        ##symbol 形式
        week = int(self.ui.lcdNumber_3.value())
        if week < 1000:
            week = '0' + str(week)
        else:
            week = str(week)
            
        #检查是否有set 没有set直接返回
        info = self.GEN.DO_INFO('-t job -e %s -m script -d STEPS_LIST' % self.JOB)
        for s in info['gSTEPS_LIST']:
            if s == set_stepname:
                break
        else:
            if set_stepname != "set+flip":                
                msg_box = msgBox()
                msg_box.warning(None, '提示信息', u'修改周期已完成!', QtGui.QMessageBox.Yes)
                sys.exit(0)
            else:
                return
        
        g = self.GEN
        g.OPEN_STEP(set_stepname)
        g.CHANGE_UNITS("mm")
        zqLayer = self.GetZQBoardLayer()
        
        #先清理所有的临时层 20221103
        for tmp_layer in zqLayer:
            self.delete_layer([tmp_layer+"_bakk"])
            
        symbollist=[]
        baklayer = []
        for ss in zqLayer:
            symboldictmp = g.DO_INFO("-t layer -e %s/%s/%s -m script -d SYMS_HIST" % (self.JOB,set_stepname, ss))
            symbollist=symbollist+symboldictmp["gSYMS_HISTsymbol"]
        pd = 1
        new_list = list(set(symbollist))
        ##备份###
        for lay in zqLayer:
            g.CLEAR_LAYER()
            g.DELETE_LAYER(lay+"_bakk")
            g.AFFECTED_LAYER(lay,"yes")
            for sy in new_list:
                if re .search("zq-(2wm|ewm|wm)",sy):
                    g.FILTER_SET_INCLUDE_SYMS(sy,reset=1)
                    g.FILTER_SELECT()
                    if g.GET_SELECT_COUNT()>0:
                        baklayer.append(lay)
            g.CLEAR_LAYER()
        layerbak = list(set(baklayer))
        for bakl in layerbak:
            g.CLEAR_LAYER()
            g.AFFECTED_LAYER(bakl, "yes")
            g.FILTER_RESET()
            #symbol的周期这里只备份周期symbol
            g.COM("filter_set,filter_name=popup,update_popup=no,include_syms=zq-2wm;zq-ewm;zq-wm")
            g.FILTER_SELECT()
            if g.GET_SELECT_COUNT()>0:
                g.SEL_COPY("%s_bakk"%bakl)
                g.CLEAR_LAYER()
                g.AFFECTED_LAYER("%s_bakk"%bakl, "yes")
                g.COM("sel_break")
            g.CLEAR_LAYER()

        for sym in new_list:
            if re.search("zq-(2wm|ewm|wm)", sym):
                g.COM("open_entity,job=%s,type=symbol,name=%s,iconic=no" % (self.JOB, sym))
                g.AUX("set_group,group=" + g.COMANS)
                g.COM("units,type=mm")
                g.COM("display_layer,name=%s,display=yes,number=1" % sym)

                g.COM("work_layer,name=" + sym)

                g.FILTER_SELECT()
                g.COM(
                    "sel_change_txt,text=%s,x_size=-1,y_size=-1,w_factor=-1,polarity=no_change,mirror=no_change,fontname=" % setzq)
                g.COM("editor_page_close")

                pd = 2
        
        pointlist = []
        layerpoint = {}        
        if pd == 2:
            #zqLayer = self.GetZQBoardLayer()
            for lay in zqLayer:
                line = g.INFO("-t layer -e %s/%s/%s -m display -d FEATURES" % (self.JOB, set_stepname, lay))
                for lin in line:
                    if re.search("zq-(2wm|ewm|wm)", lin):
                        linelist = lin.strip().split(' ')
                        pointlist.append([linelist[1], linelist[2]])
                        layerpoint[lay] = pointlist                        
                        
        #文字形式
        zqLayer = self.GetZQBoardLayer()        
        new_layerpoint = {}
        baklayer = []
        
        for lay in zqLayer:
            # 把变量放到循环内 避免不同层的周期在同一层内循环修改 导致index相同的会误改 20230103 by lyh
            new_pointlist = []
            line = g.INFO("-t layer -e %s/%s/%s -m display -d FEATURES -o feat_index+f0" % (self.JOB,set_stepname, lay))
            for lin in line:
                if barcode_type == "a79" and \
                   re.search("(barcode|#\d.*#B.*VLVGT4)", lin) and \
                   re.search("VLVGT4", lin) and \
                   re.search("\sP\s",lin):
                    if ("$$YY" in lin.upper() and "$$WW" in lin.upper()) or \
                        ("$${YY}" in lin.upper() and "$${WW}" in lin.upper()) or \
                        ("$${YY}" in lin.upper() and "$$WW" in lin.upper()) or \
                        ("$$YY" in lin.upper() and "$${WW}" in lin.upper()):                     
                        linelist = lin.strip().split()
                        new_pointlist.append([linelist[2], linelist[3], linelist[0][1:], setzq])
                        baklayer.append(lay)
                        new_layerpoint[lay] = new_pointlist
                        continue
                
                # 940程序默认加负的极性
                if barcode_type == "940" and \
                   re.search("(barcode|#\d.*#B.*VGT-VGT)", lin) and \
                   re.search("VGT-VGT", lin) and \
                   re.search("\sN\s",lin):
                    if ("$$YY" in lin.upper() and "$$WW" in lin.upper()) or \
                        ("$${YY}" in lin.upper() and "$${WW}" in lin.upper()) or \
                        ("$${YY}" in lin.upper() and "$$WW" in lin.upper()) or \
                        ("$$YY" in lin.upper() and "$${WW}" in lin.upper()):                    
                        linelist = lin.strip().split()
                        new_pointlist.append([linelist[2], linelist[3], linelist[0][1:], setzq])
                        baklayer.append(lay)
                        new_layerpoint[lay] = new_pointlist
                        continue
                
                # 20221102 增加修改分堆动态二维码的判断 by lyh
                if re.search("(barcode|#\d.*#B.*\$\$|#\d.*#B.*\w{2}\d{4}\w{2}\d{3}\w\d\s\d{4})", lin) and \
                   not re.search("VLVGT4", lin) and \
                   not re.search("VGT-VGT", lin) and \
                   re.search("\sN\s", lin):
                    if ("$$YY" in lin.upper() and "$$WW" in lin.upper()) or \
                        ("$${YY}" in lin.upper() and "$${WW}" in lin.upper()) or \
                        ("$${YY}" in lin.upper() and "$$WW" in lin.upper()) or \
                        ("$$YY" in lin.upper() and "$${WW}" in lin.upper()):   
                        linelist = lin.strip().split()
                        
                        result = re.findall("'(.*)'", lin)
                        if result:
                            week_text = result[0]                                                       
                            change_text = week_text.replace("'", "")
                            for y in ["YY", "yy"]:
                                for w in ["WW", "ww"]:                                
                                    change_text = change_text.replace("$$%s$$%s" % (y, w), week).replace("$$%s$$%s" % (w, y), week)
                                    change_text = change_text.replace("$${%s}$${%s}" % (y, w), week).replace("$${%s}$${%s}" % (w, y), week)
                                    change_text = change_text.replace("$${%s}$$%s" % (y, w), week).replace("$${%s}$$%s" % (w, y), week)
                                    change_text = change_text.replace("$$%s$${%s}" % (y, w), week).replace("$$%s$${%s}" % (w, y), week)                             
                            
                            new_pointlist.append([linelist[2], linelist[3], linelist[0][1:], change_text])
                            baklayer.append(lay)
                            new_layerpoint[lay] = new_pointlist
                            continue                
                    
        if not new_layerpoint:            
            # 前面已修改的 移到这里提示
            if pd == 2:                
                msg_box = msgBox()
                msg_box.information(self, u"提示", u"{0}修改完成请检查！".format(set_stepname), QtGui.QMessageBox.Yes)
                g.OPEN_STEP(set_stepname)
                exists_point = []
                for k, v in layerpoint.items():
                    g.WORK_LAYER(k)
                    g.WORK_LAYER(k+"_bakk",2)
                    for point in v:
                        try:                        
                            x1 = float(point[0]) - 10
                            y1 = float(point[1]) + 23
                            x2 = float(point[0]) + 10
                            y2 = float(point[1]) - 23
                        except:
                            continue
                        if (point[0], point[1]) in exists_point:
                            continue
                        exists_point.append((point[0], point[1]))                    
                        g.COM("zoom_area,x1=%s,y1=%s,x2=%s,y2=%s" % (x1, y1, x2, y2))
                        g.PAUSE("Please Check")
                if set_stepname != "set+flip":                    
                    sys.exit()
                    
            if set_stepname != "set+flip":   
                if self.ui.no_week_btn.isChecked():  
                    msg_box = msgBox()
                    msg_box.warning(None, '提示信息', u'修改周期已完成!', QtGui.QMessageBox.Yes)
                    sys.exit(0)
                    
                msg_box = msgBox()
                msg_box.warning(None, '提示信息', u'set 里没有找到二维码，请确定symbol名字!', QtGui.QMessageBox.Yes)
                sys.exit(0)
        
        ##备份###
        g.OPEN_STEP(set_stepname)
        layerbak = list(set(baklayer))
        for bakl in layerbak:
            g.CLEAR_LAYER()
            g.AFFECTED_LAYER(bakl, "yes")
            g.FILTER_RESET()
            #symbol的周期前面已备份 这里剔除掉 以免重复备份
            g.COM("filter_set,filter_name=popup,update_popup=no,exclude_syms=zq-2wm;zq-ewm;zq-wm")
            g.FILTER_SELECT()
            if g.GET_SELECT_COUNT()>0:
                g.SEL_COPY("%s_bakk" % bakl)
            g.CLEAR_LAYER()
            
        for k, v in new_layerpoint.items():
            g.CLEAR_LAYER()
            g.AFFECTED_LAYER(k, "yes")
            for point in v:
                #g.COM("sel_single_feat,operation=select,x=%s,y=%s,tol=367.47,cyclic=no" % (point[0], point[1]))
                #aa = g.GET_SELECT_COUNT()
                #if not aa:
                g.VOF()
                g.COM('sel_layer_feat,operation=select,layer=%s,index=%s'%(k,point[2]))
                if g.STATUS > 0:
                    continue
                g.VON()
                if g.GET_SELECT_COUNT() > 0:
                    g.COM(
                        "sel_change_txt,text=%s,x_size=-1,y_size=-1,w_factor=-1,polarity=no_change,mirror=no_change,fontname=" % point[3])
            g.CLEAR_LAYER()            
                
        msg_box = msgBox()
        msg_box.information(self, u"提示", u"{0}修改完成请检查！".format(set_stepname), QtGui.QMessageBox.Yes)
        g.CLEAR_LAYER()
        exists_point = []              
        for k, v in new_layerpoint.items() + layerpoint.items():
            g.WORK_LAYER(k)
            g.WORK_LAYER(k+"_bakk",2)            
            for point in v:
                try:                    
                    x1 = float(point[0]) - 10
                    y1 = float(point[1]) + 23
                    x2 = float(point[0]) + 10
                    y2 = float(point[1]) - 23
                except:
                    continue
                if (point[0], point[1]) in exists_point:
                    continue
                exists_point.append((point[0], point[1]))
                g.COM("zoom_area,x1=%s,y1=%s,x2=%s,y2=%s" % (x1, y1, x2, y2))
                g.PAUSE("Please Check")
                
        try:
            user = g.getUser()
            uploadinglog(u"自动改周期", " %s %s %s %s" %
                         (barcode_type, setzq, new_layerpoint, layerpoint), os.environ.get("STEP", ""), GEN_USER=user)
        except Exception, e:
            print e
            
        if set_stepname != "set+flip":   
            sys.exit(0)
    
    def GetZQBoardLayer(self):
        return self.GEN.GET_ATTR_LAYER('silk_screen')+self.GEN.GET_ATTR_LAYER('solder_mask')+self.GEN.GET_ATTR_LAYER('outer')    
        

    def get_week_info(self):
        '''
        开始获取周期格式
        :return:None
        '''
        week_fromat = None
        patten = re.compile('net|orig')
        info = self.GEN.DO_INFO('-t job -e %s -m script -d STEPS_LIST' %self.JOB)
        for s in info['gSTEPS_LIST']:
            # --不匹配,返回None
            if patten.search(s) is None:
                self.GEN.OPEN_STEP(s)
                week_fromat = self.get_week_fromat(s)
                if week_fromat:
                    self.ui.label_4.setText(week_fromat.lower())
                    # print week_fromat
                    return None
                if s != self.STEP:
                    self.GEN.CLOSE_STEP()

        if week_fromat is None:
            msg_box = msgBox()
            msg_box.warning(None, '提示信息', u'没有检测到$WW$$YY|$$YY$$WW格式周期，请检查并手动更改!', QtGui.QMessageBox.Yes)
            sys.exit(0)

    def get_week_fromat(self,STEP):
        '''
        获取周期格式
        :param STEP:step name
        :return: wwyy|yyww
        '''
        self.GEN.CLEAR_LAYER()
        self.GEN.FILTER_RESET()

        # --将所有keys循环出来
        for layer_keys in self.layer.keys():

            # --通过keys获取所有层
            for layer in self.layer[layer_keys]:
                self.GEN.AFFECTED_LAYER(layer,'yes')
                self.GEN.FILTER_SET_TYP('text')
                self.GEN.FILTER_SELECT()

                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    file_path = '/tmp/get_week_fromat_++++++++'
                    if platform.system() == "Windows":
                        file_path = 'C:/tmp/get_week_fromat_++++++++'
                    self.GEN.COM('info, out_file=%s,args= -t layer -e %s/%s/%s -m script -d FEATURES -o select'%(file_path,self.JOB,STEP,layer))

                    patten = re.compile('^#T')
                    patten_week = re.compile('\$\$[{]?(.*)[}]?\$\$[{]?(.*)[}]?')
                    with open(file_path,'r') as f:
                        for line in  f.readlines():
                            if patten.search(line):
                                info =  line.split(' ')
                                if patten_week.search(info[10]):
                                    print info[10]
                                    # --删除两旁'符号
                                    cut_flag = info[10].strip("'")
                                    print cut_flag
                                    lists = re.findall('\$\$[{]?(.*)[}]?\$\$[{]?(.*)[}]?',cut_flag)
                                    print lists[0][0][:2]
                                    print lists[0][1][:2]
                                    self.GEN.AFFECTED_LAYER(layer, 'no')
                                    return lists[0][0][:2] + lists[0][1][:2]
                self.GEN.AFFECTED_LAYER(layer, 'no')

    def get_layer(self):
        '''
        获取层
        :return:None
        '''
        self.layer = dict()
        info = self.GEN.DO_INFO('-t matrix -e %s/matrix -m script -d ROW' % self.JOB)
        for i in range(len(info['gROWname'])):
            if info['gROWcontext'][i] == 'board':

                if info['gROWlayer_type'][i] == 'signal':
                    # --判断键是否在字典内
                    if 'signal' not in self.layer:
                        self.layer['signal'] = []
                        
                    if info['gROWside'][i] != "inner":
                        self.layer['signal'].append(info['gROWname'][i])

                elif info['gROWlayer_type'][i] == 'solder_mask':
                    if 'mask' not in self.layer:
                        self.layer['mask'] = []
                    self.layer['mask'].append(info['gROWname'][i])

                elif info['gROWlayer_type'][i] == 'silk_screen':
                    if 'silk' not in self.layer:
                        self.layer['silk'] = []
                    self.layer['silk'].append(info['gROWname'][i])


    def run_change(self):
        '''
        开始修改
        :return:None
        '''
        self.point = []
        self.ZQlayerdic = {}
        
        patten = re.compile('net|orig|panel')
        info = self.GEN.DO_INFO('-t job -e %s -m script -d STEPS_LIST' % self.JOB)
        print info
        for s in info['gSTEPS_LIST']:
            # --不匹配,返回None
            if patten.search(s) is None:
                self.GEN.OPEN_STEP(s)
                for k in self.layer.keys():
                    for layer in self.layer[k]:
                        self.change_week(int(self.ui.lcdNumber_3.value()),layer,s)
                if s != self.STEP:
                    self.GEN.CLOSE_STEP() 

    def change_week(self,week,layer,step):
        '''
        开始更改周期
        :param week: 周期
        :param layer:层别
        :return:None
        '''
        self.GEN.CLEAR_LAYER()
        self.GEN.FILTER_RESET()
        if week < 1000:
            week = '0' + str(week)
        else:
            week = str(week)
        self.GEN.AFFECTED_LAYER(layer,'yes')
        tmp_layer = layer + '___change_week_bak_layer+++++'
        self.GEN.SEL_COPY(tmp_layer)
        self.GEN.FILTER_SET_TYP('text')
        self.GEN.FILTER_SELECT()
        bak_layer = layer + '__________week_bak'
        week_count = int(self.GEN.GET_SELECT_COUNT())
        if week_count > 0:
            ref_layer = layer + '____ref___'
            #self.GEN.SEL_COPY(ref_layer)
            #self.GEN.FILTER_RESET()
            #self.GEN.FILTER_SET_TYP('text')
            #self.GEN.SEL_REF_FEAT(ref_layer,'touch')
            #周涌通知 只移出text来修改 接触的负片不移出来 20221222 by lyh
            #self.GEN.FILTER_RESET()
            #self.GEN.FILTER_SET_POL('negative')
            #self.GEN.SEL_REF_FEAT(ref_layer,'touch')
            #sel_count = int(self.GEN.GET_SELECT_COUNT())
            #self.GEN.SEL_MOVE(bak_layer)
            #self.GEN.AFFECTED_LAYER(layer, 'no')
            #self.GEN.WORK_LAYER(bak_layer)
            infolist = self.GEN.INFO("-t layer -e %s/%s/%s -m display -d FEATURES -o feat_index+select+f0" % (self.JOB,step, layer))
            self.GEN.AFFECTED_LAYER(layer, 'no')
            self.GEN.WORK_LAYER(layer)
            for line in infolist:
                # nCount = n + 1
                if not re.match("^#\d+", line):
                    continue                
                
                linelist = line.strip().split()
                index = linelist[0][1:]
                # --index物件筛选功能
                self.GEN.COM('sel_layer_feat,operation=select,layer=%s,index=%s'%(layer,index))
                self.GEN.COM('pan_feat,layer=%s,index=%s,auto_zoom=yes' % (layer, index))

                filePath = 'C:/tmp/get_text_format_file_tmp'
                if platform.system() != "Windows":
                    filePath = '/tmp/get_text_format_file_tmp'

                self.GEN.COM('info,args=-t layer -e %s/%s/%s -m script -d FEATURES -o select,out_file=%s,write_mode=replace,units=inch'%(self.JOB,step,layer,filePath))
                with open(filePath,'r') as f:
                    textData = f.readlines()

                # --获取信息栏消息
                # self.GEN.COM('get_message_bar')
                # info = self.GEN.READANS
                # info_split = info.split(',')
                info_split = textData[1].split(' ')
                
                week_text = ""
                result = re.findall("'(.*)'", textData[1])
                if result:
                    week_text = result[0]

                mirror = 'no'
                polarity = 'positive'
                if len(info_split) > 0:
                    if info_split[0] != '#T':
                        self.GEN.COM('clear_highlight')
                        self.GEN.COM('sel_clear_feat')
                        continue
                    if info_split[6] == 'Y':
                        mirror = 'yes'

                    if info_split[4] == 'N':
                        polarity = 'negative'
                        
                patten_week = re.compile('\$\$[{]?(.*)[}]?\$\$[{]?(.*)[}]?')
                if patten_week.search(info_split[10]):
                    change_week_text = week
                    if week_text:
                        # 此处修改用替换的形式 将动态的替换成静态 避免动态周期后加有静态字 导致静态字丢失 20221223 by lyh
                        change_week_text = week_text.replace("'", "")
                        for y in ["YY", "yy"]:
                            for w in ["WW", "ww"]:                                
                                change_week_text = change_week_text.replace("$$%s$$%s" % (y, w), week).replace("$$%s$$%s" % (w, y), week)
                                change_week_text = change_week_text.replace("$${%s}$${%s}" % (y, w), week).replace("$${%s}$${%s}" % (w, y), week)
                                change_week_text = change_week_text.replace("$${%s}$$%s" % (y, w), week).replace("$${%s}$$%s" % (w, y), week)
                                change_week_text = change_week_text.replace("$$%s$${%s}" % (y, w), week).replace("$$%s$${%s}" % (w, y), week)                               
                        
                    # self.GEN.PAUSE(str([change_week_text, week_text, textData[1], result]))
                    self.GEN.COM('sel_change_txt,text=%s,x_size=-1,y_size=-1,w_factor=-1,polarity=no_change,mirror=no_change,fontname='%(change_week_text))
                else:
                    # --清除选中和高亮
                    self.GEN.COM('clear_highlight')
                    self.GEN.COM('sel_clear_feat')

            # --移动回原始层
            # self.GEN.SEL_MOVE(layer)
            self.delete_layer([ref_layer])

        self.delete_layer([bak_layer])
        self.GEN.AFFECTED_LAYER(layer, 'no')

    def delete_layer(self,info):
        '''
        删除层
        :param info:删除层列表
        :return:None
        '''
        for layer in info:
            if self.GEN.LAYER_EXISTS(layer) == 'yes':
                self.GEN.DELETE_LAYER(layer)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    CW = CHANGE_WEEK()
    sys.exit(app.exec_())