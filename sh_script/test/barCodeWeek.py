#!/usr/bin/python
# -*- coding: UTF-8 -*-
# --------------------------------------------------------- #
#                VTG.SH SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    AresHe
# @Mail         :    502614708@qq.com
# @Date         :    2020/12/16
# @Revision     :    1.0.0
# @File         :    AnalyseDrill.py
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
from PyQt4 import QtCore,QtGui
from resource.add_date_week import Ui_Form
from resource.icon import *
import shutil

import Oracle_DB
import MySQL_DB

# --所有与InPlan查询相关的全部写到InPlan类中
class InPlan():
    def __init__(self, job_name=None):
        self.job_name = job_name.upper()
        # --Oracle相关参数定义
        self.DB_O = Oracle_DB.ORACLE_INIT()
        self.dbc_o = self.DB_O.DB_CONNECT(host='192.168.2.18', servername='inmind.fls', port='1521',
                                          username='GETDATA', passwd='InplanAdmin')

    def __del__(self):
        # --关闭数据库连接
        if self.dbc_o:
            self.DB_O.DB_CLOSE(self.dbc_o)

    def get_week_format(self):
        """
        从InPlan中获取铜厚及层别正反的数据
        :return:sql后的字典
        """
        sql = """
                SELECT
                    c.VALUE 
                FROM
                    VGT.PUBLIC_ITEMS i,
                    VGT.JOB_DA j,
                    vgt.enum_values a,
                    vgt.enum_values b,
                    vgt.enum_values c,
                    vgt.enum_values d 
                WHERE
                    i.ITEM_NAME = '%s' 
                    AND i.item_id = j.item_id 
                    AND i.revision_id = j.revision_id 
                    AND j.UL_MARK_ = a.enum 
                    AND a.enum_type = '1008' 
                    AND j.UL_MARK_FACE_ = b.enum 
                    AND b.enum_type = '1009' 
                    AND j.PERIOD_TYPE_ = c.enum 
                    AND c.enum_type = '1024' 
                    AND j.period_face_ = d.enum 
                    AND d.enum_type = '1023'""" % self.job_name

        # --返回数据字典
        return self.DB_O.SQL_EXECUTE(self.dbc_o, sql)

class WINDOWS():
    def __init__(self):
        self.filePath = '/tmp/set_barcode_week_str_size'
        if platform.system() == "Windows":
            self.filePath = 'C:/tmp/set_barcode_week_str_size'
        self.readFile()

    def readFile(self):
        self.strSize = '200'
        if os.path.exists(self.filePath):
            with open(self.filePath, 'r') as f:
                self.strSize = f.read().strip()

    def getSyetemInfo(self):
        self.Form = QtGui.QWidget()
        # self.Form.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        ui = Ui_Form()
        ui.setupUi(self.Form)
        self.Form.show()

        # --设置事件信息
        self.changeWeekFormat()

        # --绑定按钮信号
        self.btnSignal()

        # --设置二维码参数
        self.setBarcodePara()

    def setBarcodePara(self):

        Aangle = self.Form.findChild(QtGui.QWidget, "comboBox_2")
        Mirror = self.Form.findChild(QtGui.QWidget, "comboBox")
        Matrix = self.Form.findChild(QtGui.QWidget, "comboBox_3")
        String = self.Form.findChild(QtGui.QWidget, "comboBox_4")
        Marker = self.Form.findChild(QtGui.QWidget, "comboBox_5")
        Polarity = self.Form.findChild(QtGui.QWidget, "comboBox_6")
        Height = self.Form.findChild(QtGui.QWidget, "lineEdit_5")

        Aangle.addItems(['0','90','180','270'])
        Mirror.addItems(['no','yes'])
        Matrix.addItems(['Minimal','10x10','12x12','14x14','16x16','10x10','18x18','20x20','24x24','26x26','32x32','40x40','44x44','48x48'
                         ,'52x52','64x64','72x72','80x80','88x88','96x96','104x104','132x132','144x144','8x18','8x32','12x36','16x36','16x48'])
        Height.setText(self.strSize)
        String.addItems(['yes', 'no'])
        Marker.addItems(['yes', 'no'])
        Polarity.addItems(['positive', 'negative'])

        dateWeek = self.Form.findChild(QtGui.QWidget, "calendarWidget")
        dateWeek.setFirstDayOfWeek(QtCore.Qt.Sunday)

        # print dateWeek.firstDayOfWeek()
        # print lcd.firstDayOfWeek()

    def btnSignal(self):
        btnExit = self.Form.findChild(QtGui.QWidget, "pushButton")
        btnRun = self.Form.findChild(QtGui.QWidget, "pushButton_2")

        btnExit.clicked.connect(sys.exit)
        btnRun.clicked.connect(self.addWeek)

    def addWeek(self):
        # --获取周期
        lcd = self.Form.findChild(QtGui.QWidget, "lcdNumber")
        getWeek = lcd.intValue()
        # QtCore.Qt.DayOfWeeK

        # --检查选中哪个按钮
        barcode = self.Form.findChild(QtGui.QWidget, "radioButton")
        if barcode.isChecked() == True:
            seceteFormat =  'wwyy'
        else:
            seceteFormat =  'yyww'

        Aangle = self.Form.findChild(QtGui.QWidget, "comboBox_2").currentText()
        Mirror = self.Form.findChild(QtGui.QWidget, "comboBox").currentText()
        Matrix = self.Form.findChild(QtGui.QWidget, "comboBox_3").currentText()
        String = self.Form.findChild(QtGui.QWidget, "comboBox_4").currentText()
        Marker = self.Form.findChild(QtGui.QWidget, "comboBox_5").currentText()
        Polarity = self.Form.findChild(QtGui.QWidget, "comboBox_6").currentText()
        Height = self.Form.findChild(QtGui.QWidget, "lineEdit_5").text()
        leftText = self.Form.findChild(QtGui.QWidget, "lineEdit_6").text()
        rightText = self.Form.findChild(QtGui.QWidget, "lineEdit_7").text()
        # self.Form.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        # self.Form.showMinimized()
        self.writeFile(Height)
        addweek = ADDWEEK()
        addweek.barcode_info(getWeek,seceteFormat,Aangle,Mirror,Matrix,String,Marker,Polarity,Height,leftText,rightText)
        # self.Form.showNormal()

    def writeFile(self,Height):
        # 打开一个文件
        fo = open(self.filePath, 'w')
        fo.write(Height)
        # 关闭打开的文件
        fo.close()

    def getDateFormat(self):
        wwyyconnect = self.Form.findChild(QtGui.QWidget, "radioButton")
        yywwconnect = self.Form.findChild(QtGui.QWidget, "radioButton_2")

        wwyyconnect.toggled.connect(self.wwyy)
        yywwconnect.toggled.connect(self.yyww)

        # --绑定信号
        if wwyyconnect.isChecked(): self.setLcdNumber('wwyy')
        if yywwconnect.isChecked(): self.setLcdNumber('yyww')

    def wwyy(self,st):
        if st == True:
            self.setLcdNumber('wwyy')

    def yyww(self,st):
        if st == True:
            self.setLcdNumber('yyww')

    def setLcdNumber(self,format):
        lcd = self.Form.findChild(QtGui.QWidget, "lcdNumber")
        yearFormat = self.Form.findChild(QtGui.QWidget, "lineEdit")
        weekFormat = self.Form.findChild(QtGui.QWidget, "lineEdit_4")

        year = (yearFormat.text())[2:4]
        week = weekFormat.text() if len(weekFormat.text()) > 1 else '0' + weekFormat.text()

        if format == 'wwyy':
            setweek = week + year
            lcd.display(setweek)
        elif format == 'yyww':
            setweek = year + week
            lcd.display(setweek)

    def changeWeekFormat(self):
        set_content = self.Form.findChild(QtGui.QWidget, "calendarWidget")

        # --刷新一次周期日期
        self.updateDate()

        if platform.system() == "Windows":
            # --连接信号，当触发时，更新日期
            set_content.clicked.connect(self.updateDate)
        else:
            set_content.clicked.connect(self.information)

    def information(self):
        self.Message(u'Linux环境仅需选择周期格式，周期按系统周期为准!...')

    def updateDate(self):

        set_content = self.Form.findChild(QtGui.QWidget, "calendarWidget")
        dateTime = set_content.selectedDate().getDate()
        yearFormat = self.Form.findChild(QtGui.QWidget, "lineEdit")
        yearFormat.setText(str(dateTime[0]))
        modFormat = self.Form.findChild(QtGui.QWidget, "lineEdit_3")
        modFormat.setText(str(dateTime[1]))
        dayFormat = self.Form.findChild(QtGui.QWidget, "lineEdit_2")
        dayFormat.setText(str(dateTime[2]))

        # --设置周期
        week = set_content.selectedDate().weekNumber()
        dayFormat = self.Form.findChild(QtGui.QWidget, "lineEdit_4")
        dayFormat.setText(str(week[0]))

        # --设定周期格式
        self.getDateFormat()

    def Message(self, text):
        """
        Msg窗口
        :param text: 显示的内容
        :return:None
        """
        # 警告信息提示框
        message = QtGui.QMessageBox.warning(None, u'提示信息!', text, QtGui.QMessageBox.Ok)

class ADDWEEK(WINDOWS):
    def __init__(self):
        # -->初始化
        self.GEN = genCOM.GEN_COM()
        self.JOB = os.environ.get("JOB")
        self.STEP = os.environ.get("STEP")
        self.GENESIS_DIR = os.environ.get("GENESIS_DIR")

        if platform.system() == "Windows":
            # --更新属性文件
            sourceUser = '\\\\192.168.2.33\\incam-share\\incam\\genesis\\fw\\lib\\misc\\userattr'
            targetUser = self.GENESIS_DIR + '/fw/lib/misc/userattr'
            self.updateFile(sourceUser,targetUser)

            # --更新hooks文件
            source_open_job = '\\\\192.168.2.33\\incam-share\\incam\\genesis\\sys\\hooks\\line_hooks\\open_job.post'
            target_open_job = self.GENESIS_DIR + '/sys/hooks/line_hooks/open_job.post'
            self.updateFile(source_open_job,target_open_job)

    def updateFile(self,sourceFile,targetFIle):

        if os.path.exists(targetFIle + '_2021_07_01') is False:
            if os.path.exists(targetFIle):
                shutil.copyfile(targetFIle,targetFIle + '_2021_07_01')
            shutil.copyfile(sourceFile,targetFIle)

    def barcode_info(self,getWeek,seceteFormat,Aangle,Mirror,Matrix,String,Marker,Polarity,Height,leftText,rightText):
        self.GEN.OPEN_STEP(self.STEP)
        self.GEN.FILTER_RESET()
        workflayer = self.GEN.GET_WORK_LAYER()
        if workflayer:
            self.GEN.MOUSE('please select point')
            point = self.GEN.MOUSEANS
            point = point.split(' ')
            #resouceFormat = self.search_zq_code()
            resouceFormat = self.get_inplan_week()
            if seceteFormat == 'wwyy':
                if resouceFormat is None or resouceFormat == 'WWYY' or resouceFormat == 'wwyy':
                    if resouceFormat is None:
                        self.Message(u'(%s) InPlan周期格式为空，添加后请检查!...' %self.JOB)
                    Format = 'wwyy'
                    if platform.system() != "Windows":
                        getWeek = '$$WW$$YY'

                    self.add_barcode(Format,point[0],point[1],getWeek,Aangle,Mirror,Matrix,String,Marker,Polarity,Height,leftText,rightText)
                else:
                    #self.Message(u'与(zp-code)周期格式不符，请重新选择!...')
                    self.Message(u'周期格式与InPlan(%s)不符，请重新选择!...'%resouceFormat)
            else:
                if resouceFormat is None or resouceFormat == 'YYWW' or resouceFormat == 'yyww':
                    if resouceFormat is None:
                        self.Message(u'%s InPlan周期格式为空，添加后请检查!...' %self.JOB)
                    Format = 'yyww'
                    if platform.system() != "Windows":
                        getWeek = '$$YY$$WW'
                    self.add_barcode(Format,point[0], point[1], getWeek, Aangle, Mirror, Matrix, String, Marker, Polarity,Height,leftText,rightText)
                else:
                    self.Message(u'周期格式与InPlan(%s)不符，请重新选择!...'%resouceFormat)
        else:
            self.Message(u'请选择工作层!...')
            sys.exit()

    def add_barcode(self,Format,point1, point2, getWeek, Aangle, Mirror, Matrix, String, Marker, Polarity,Height,leftText,rightText):

        self.GEN.COM('cur_atr_reset')
        self.GEN.COM('cur_atr_set,attribute=date_format,text=%s' %Format)
        Height = float(Height) / 1000

        NewText = leftText + str(getWeek) + ' ' + rightText
        self.GEN.COM("add_text,attributes=yes,type=barcode,x=%s,y=%s,text=%s,x_size=0.2,y_size=0.2,w_factor=2,polarity=%s,angle=%s,mirror=%s,fontname=standard,\
        bar_type=ECC-200,matrix=%s,bar_checksum=no,bar_background=yes,bar_add_string=%s,bar_add_string_pos=top,bar_marks=%s,bar_width=0.008,bar_height=%s,ver=1" %(point1,point2,NewText,Polarity,Aangle,Mirror,Matrix,String,Marker,Height))
        self.GEN.PAUSE('Continue to add...！')


    def get_inplan_week(self):
        # --创建inplan连接
        connect = InPlan(self.JOB)
        # --获取inplan信息
        week_format = connect.get_week_format()
        if  week_format:
            # --返回InPlan周期格式
            return week_format[0][0]
        else:
            return None

    def search_zq_code(self):
        sym = 'zq-code'
        info = self.GEN.DO_INFO('-t symbol -e %s/%s -m script -d EXISTS'%(self.JOB,sym))
        if info['gEXISTS'] == 'yes':
            zqPath = '/tmp/zq_code_info'
            if platform.system() == "Windows":
                zqPath = 'C:/tmp/zq_code_info'
            self.GEN.COM('info, out_file=%s,args=  -t symbol -e %s/%s -m script -d FEATURES'%(zqPath,self.JOB,sym))
            with open(zqPath, "r") as f:
                fileInfo = f.readlines()

            # --$${YY}$${WW} or $$YY$$WW
            YYWW = re.compile('\$\$[{]?YY[}]?\$\$[{]?WW[}]?')
            WWYY = re.compile('\$\$[{]?WW[}]?\$\$[{]?YY[}]?')
            for lineinfo in fileInfo:
                if YYWW.search(lineinfo):
                    return 'YYWW'
                elif WWYY.search(lineinfo):
                    return 'WWYY'

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = WINDOWS()
    win.getSyetemInfo()
    sys.exit(app.exec_())
