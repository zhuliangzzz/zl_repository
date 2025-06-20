#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__  = "tiger"
__date__    = "2023.11.1"
__version__ = "$Revision: 1.0 $"
__credits__ = "MI铜面积计算"

import os, sys
import platform
reload(sys)
sys.setdefaultencoding('utf8')
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
    sys.path.append(r"D:/pyproject/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
from create_ui_model import showMessageInfo,app
from PyQt4 import QtGui,QtCore
from PyQt4.QtGui import QMainWindow,QTableWidgetItem,QWidget,QHBoxLayout,QMessageBox
from window_ui import Ui_MainWindow
from set_size_ui import Ui_Form
from genCOM_26 import GEN_COM
import gClasses
import Oracle_DB
# import MySQL_DB
import math
from messageBoxPro import msgBox
import socket
import shutil

_file_path = os.path.dirname(os.path.abspath(__file__))
try:
    jobName = os.environ.get("JOB")
    job_cmd = gClasses.Job(jobName)
except:
    jobName = 'ha0112gi262a1'
if not jobName:
    showMessageInfo(u"必须打开料号再运行此程序")
GEN = GEN_COM()
_main_path = os.path.dirname(os.path.abspath(__file__))

def is_number(num):
    s = str(num)
    res = False
    if s.count('.') == 1:  # 小数
        new_s = s.split('.')
        left_num = new_s[0]
        right_num = new_s[1]
        if right_num.isdigit():
            if left_num.isdigit():
                res = True
            elif left_num.count('-') == 1 and left_num.startswith('-'):  # 负小数
                tmp_num = left_num.split('-')[-1]
                if tmp_num.isdigit():
                    res = True
    elif s.count(".") == 0:  # 整数
        if s.isdigit():
            res = True
        elif s.count('-') == 1 and s.startswith('-'):  # 负整数
            ss = s.split('-')[-1]
            if ss.isdigit():
                res = True
    return res


class Methon:

    def __init__(self):
        pass

    def setCheckBox(self, wgt):
        STR = ("#%s{\n"
                "font-size: 15px;\n"
                "}\n"
                " \n"
                "#%s::indicator {\n"
                "padding-top: 1px;\n"
               "width: 30px;\n"
               "height: 30px;border: none;\n"               
               "}\n"
               " \n"
               "#%s::indicator:unchecked {\n"
               "    image: url(:pic/png/unchecked.png);\n"
               "}\n"
               " \n"
               "#%s::indicator:checked {\n"
               "    image: url(:pic/png/right.png);\n"              
               "}" % (wgt, wgt, wgt, wgt))
        return STR

    def clip_area_copper(self, refLay = '', size = 0):
        GEN.COM("clip_area_strt")
        GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,"
                    "contour_cut=yes,margin=%s,ref_layer=%s,feat_types=line\;pad\;surface\;arc\;text" % (size,refLay))

    def set_fill_parm(self, typ ='solid', sym='', cut_p = 'no', d_x = 0.1,d_y=0.1):
        """
        typ ='solid','pattern'
        """
        GEN.COM("fill_params,type=%s,origin_type=datum,solid_type=surface,std_type=line,min_brush=1,"
                    "use_arcs=yes,symbol=%s,dx= %s,dy= %s,std_angle=45,std_line_width=10,std_step_dist=50,std_indent=odd,"
                    "break_partial=yes,cut_prims=%s,outline_draw=no,outline_width=0,outline_invert=no" % (typ,sym,d_x,d_y,cut_p))

    def sr_fill_surface(self, polarity='positive', step_margin_x = 0, step_margin_y = 0, step_max_dist_x =100, step_max_dist_y=100,
                        sr_margin_x=0, sr_margin_y=0, sr_max_dist_x=0, sr_max_dist_y=0, nest_sr='yes'):
        GEN.COM('fill_params,type=solid,origin_type=limits,solid_type=surface')
        GEN.COM('sr_fill, polarity=%s, step_margin_x=%s, step_margin_y=%s, step_max_dist_x=%s, step_max_dist_y=%s,'
                 'sr_margin_x=%s, sr_margin_y=%s, sr_max_dist_x=%s, sr_max_dist_y=%s, nest_sr=%s, stop_at_steps=,'
                 'consider_feat=no, consider_drill=no, consider_rout=no, dest=affected_layers, attributes=no'
                 % (polarity, step_margin_x, step_margin_y, step_max_dist_x, step_max_dist_y, sr_margin_x, sr_margin_y,
                    sr_max_dist_x, sr_max_dist_y, nest_sr))

    def fill_copper_type(self, sym, dsx, dsy , cut_p = 'yes'):
        GEN.COM("fill_params,type=pattern,origin_type=limits,solid_type=surface,std_type=line,min_brush=0.5,use_arcs=yes,symbol=%s,dx=%s,dy=%s,std_angle=45,"
                     "std_line_width=10,std_step_dist=50,std_indent=odd,break_partial=yes,cut_prims=%s,outline_draw=no,outline_width=0,outline_invert=no" % (sym, dsx, dsy,cut_p))
        GEN.COM("sel_fill")

    def createLayer(self, name, context='misc', laytype='document', polarity='positive', ins_layer=""):
        STR = 'create_layer,layer=%s,context=%s,type=%s,polarity=%s,ins_layer=%s' % (
            name, context, laytype, polarity, ins_layer)
        GEN.COM(STR)

class CONNECTMYSQL():
    def __init__(self,job_name):
        # --MySql,连接工程MySql数据库
        self.job_name = job_name
        self.DB_M = MySQL_DB.MySQL()
        self.dbc_m = self.DB_M.MYSQL_CONNECT()

    def __del__(self):
        '''
        程序结束时关闭数据库连接
        :return: None
        '''
        self.dbc_m.close()

    def insertData(self,**kwargs):
        """
        :return:
        :rtype:
        """
        # 插入数据库
        insert_sql = """
        INSERT INTO hdi_engineering.genesis_copper_usage 
            (job_name,layer_name,pnl_copper_usage,computer_name,cam_note)
        VALUES
            ( '%s', '%s','%s','%s','%s')
        """ % (self.job_name,kwargs['layer'],kwargs['values'], kwargs['computer'],kwargs['note'])
        self.DB_M.SQL_EXECUTE(self.dbc_m, insert_sql)


    # def insertData(self,values='',computer='', note = '',layer =''):
    #     """
    #     :return:
    #     :rtype:
    #     """
    #     # 插入数据库
    #     insert_sql = """
    #     INSERT INTO hdi_engineering.genesis_copper_usage
    #         (job_name,layer_name,pnl_copper_usage,computer_name,cam_note)
    #     VALUES
    #         ( '%s', '%s','%s','%s','%s')
    #     """ % (self.job_name,layer,values, computer,note)
    #     self.DB_M.SQL_EXECUTE(self.dbc_m, insert_sql)

    def checkData(self,layer):
        """
        检索数据库数据
        :return:
        """
        sql = """
                SELECT                     
                    layer_name
                FROM 
                    hdi_engineering.genesis_copper_usage
                WHERE 
                    job_name = '%s'
                    AND layer_name = '%s'
                """ % (self.job_name, layer)
        # --MySQL的SELECT_DIC方法有问题，此处用SQL_EXECUTE
        query_result = self.DB_M.SELECT_DIC(self.dbc_m, sql)
        if query_result:
            return True

    def upData(self,**kwargs):
        """
        更新数据库数据
        :param values:
        :return:
        """
        sql = """
                UPDATE 
                    hdi_engineering.genesis_copper_usage
                SET 
                    pnl_copper_usage='%s',
                    computer_name='%s',
                    cam_note='%s'
                WHERE 
                    job_name = '%s'
                    AND layer_name = '%s'
                """ % (kwargs['values'],kwargs['computer'], kwargs['note'],self.job_name, kwargs['layer'])
        # --MySQL的SQL_EXECUTE方法有问题，此处用SQL_EXECUTE
        self.DB_M.SQL_EXECUTE(self.dbc_m, sql)


class InPlan:

    def __init__(self, job):
        # --Oracle相关参数定义
        self.JOB_SQL = job.replace(jobName[13:], '').upper()
        self.DB_O = Oracle_DB.ORACLE_INIT()
        self.dbc_h = self.DB_O.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
                                          username='GETDATA', passwd='InplanAdmin')
        print 'aaaaaaaaaaaa'
        if not self.dbc_h:
            pass

    def __del__(self):
        # --关闭数据库连接
        if self.dbc_h:
            self.DB_O.DB_CLOSE(self.dbc_h)

    def get_Layer_Info(self):
        """
        铜厚信息
        """
        sql="""        
        SELECT            
            a.item_name,
            LOWER(c.item_name) AS LAYER_NAME, 
            round( d.required_cu_weight / 28.3495, 2 )  AS CU_WEIGHT           
            FROM
            vgt_hdi.ALL_ITEMS a,
             vgt_hdi.job b,
            vgt_hdi.ALL_ITEMS c,
            vgt_hdi.copper_layer d
            WHERE

            a.item_id = b.item_id  
             and a.revision_id= b.revision_id
             and a.ITEM_TYPE = 2
              AND a.root_id = c.root_id 
                and c.ITEM_TYPE = 3
            AND c.item_id = d.item_id 
            and c.revision_id = d.revision_id
         AND a.item_name = '%s' 
            ORDER BY
            d.layer_index
        """ % self.JOB_SQL
        process_data = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        return process_data

    def getLaminData(self):
        """
        获取压合信息
        :return:
        """
        sql = """
        SELECT            
         a.item_name AS job_name,
          p.mrp_name AS mrpName,
        d.process_num_ AS process_num,
        d.pressed_pnl_x_ / 1000 AS pnlroutx,
        d.pressed_pnl_y_ / 1000 AS pnlrouty,
        'L'|| d.layer_index_top_ AS fromLay, 
         'L'|| d.layer_index_bot_ AS toLay    
    FROM
        vgt_hdi.ALL_ITEMS a,
        vgt_hdi.job b,
         vgt_hdi.ALL_ITEMS c,
         vgt_hdi.process p,
         vgt_hdi.process_da d
    WHERE
            a.item_id = b.item_id  
            and a.revision_id= b.revision_id
            and a.ITEM_TYPE = 2
            AND a.root_id = c.root_id 
            and c.ITEM_TYPE = 7
            AND c.item_id = p.item_id 
            and c.revision_id = p.revision_id
            AND p.item_id = d.item_id 
            AND p.revision_id = d.revision_id 
            AND P.proc_subtype IN ( 28, 29 ) 
            AND a.item_name = '%s'
        ORDER BY
              d.process_num_ """ % self.JOB_SQL
        process_data = self.DB_O.SELECT_DIC(self.dbc_h,sql)

        return process_data

    # def getLaminData(self):
    #     """
    #     获取压合信息
    #     :return:
    #     """
    #     sql = """
    #     SELECT
    #         a.item_name AS job_name,
    #         d.mrp_name AS mrpName,
    #         e.process_num_ AS process_num,
    #         b.pnl_size_x / 1000 AS pnlXInch,
    #         b.pnl_size_Y / 1000 AS pnlYInch,
    #         e.pressed_pnl_x_ / 1000 AS pnlroutx,
    #         e.pressed_pnl_y_ / 1000 AS pnlrouty,
    #         (case when  e.film_bg_ not like '%%,%%' then
    #                     'L'|| TO_CHAR(TO_NUMBER(substr(REGEXP_SUBSTR( d.mrp_name, '[^-]+', 1,2 ),2,2), '99')) else
    #                     REGEXP_SUBSTR( e.film_bg_, '[^,]+', 1, 1 ) end) fromLay,
    #         (case when  e.film_bg_ not like '%%,%%' then
    #         'L'|| TO_CHAR(TO_NUMBER(substr(REGEXP_SUBSTR( d.mrp_name, '[^-]+', 1,2 ),4,2), '99')) else
    #         REGEXP_SUBSTR( e.film_bg_, '[^,]+', 1, 2 ) end) toLay,
    #         ROUND( e.PRESSED_THICKNESS_ / 39.37, 2 ) AS yhThick,
    #         ROUND( e.PRESSED_THICKNESS_TOL_PLUS_ / 39.37, 2 ) AS yhThkPlus,
    #         ROUND( e.PRESSED_THICKNESS_TOL_MINUS_ / 39.37, 2 ) AS yhThkDown,
    #         e.LASER_BURN_TARGET_ V5laser
    #     FROM
    #         vgt_hdi.items a
    #         INNER JOIN vgt_hdi.job b ON a.item_id = b.item_id
    #         AND a.last_checked_in_rev = b.revision_id
    #         INNER JOIN vgt_hdi.public_items c ON a.root_id = c.root_id
    #         INNER JOIN vgt_hdi.process d ON c.item_id = d.item_id
    #         AND c.revision_id = d.revision_id
    #         INNER JOIN vgt_hdi.process_da e ON d.item_id = e.item_id
    #         AND d.revision_id = e.revision_id
    #     WHERE
    #         a.item_name = '%s'
    #         AND d.proc_type = 1
    #         AND d.proc_subtype IN ( 28, 29 )
    #     ORDER BY
    #         e.process_num_""" % self.JOB_SQL
    #     process_data = self.DB_O.SELECT_DIC(self.dbc_h,sql)
    #
    #     return process_data


    def get_stuck_data(self):
        """
        获取排版尺寸信息
        """
        sql = """
            SELECT ITEM_NAME as JOB_NAME，
                (select Round(PCB_SIZE_X/39.37,3) from VGT_HDI.PART where item_id=ITEM.ITEM_ID   and REVISION_ID=ITEM.REVISION_ID) as PCB_X，
                (select Round(PCB_SIZE_Y/39.37,3) from VGT_HDI.PART where item_id=ITEM.ITEM_ID   and REVISION_ID=ITEM.REVISION_ID) as PCB_Y，
                 Round(SET_SIZE_X_/39.37,3) as SET_X，
                 Round(SET_SIZE_Y_/39.37,3) as SET_Y，
                 Round(PNL_SIZE_X/1000,2) as PNL_X，
                 Round(PNL_SIZE_Y/1000,2) as PNL_Y，
                 PCS_PER_SET_  as SET_PCS，
                 NUM_PCBS as Panel_PCS，
                 NUM_ARRAYS as Panel_SET，
                 SPACING_X_ as Spacing_X，
                 SPACING_Y_ as Spacing_Y
            FROM VGT_HDI.ALL_ITEMS ITEM,  VGT_HDI.JOB,  VGT_HDI.JOB_DA,   VGT_HDI.REV_CONTROLLED_LOB
            where ITEM.item_id=Job.item_id
                and  ITEM.revision_id=Job.REVISION_ID
                and ITEM.item_id=JOB_DA.item_id
                and  ITEM.revision_id=JOB_DA.REVISION_ID
                and JOB_DA.STACKUP_IMAGE_=REV_CONTROLLED_LOB.LOB_ID
                and ITEM_TYPE = 2
                and ITEM_NAME='%s'
                    """ % self.JOB_SQL
        job_data = self.DB_O.SELECT_DIC(self.dbc_h, sql)[0]
        return job_data


    def getPanelSRTable(self):
        sql='''select a.item_name JOB_NAME,
               e.item_name PANEL_STEP,
               case when d.coupon_sequential_index >0
               then (select coup.name from vgt_hdi.coupon coup
                     where coup.item_id = b.item_id
                       and coup.revision_id = b.revision_id
                       and d.coupon_sequential_index = coup.sequential_index)
               Else (select decode(count(*), 1, 'PCS', 2, 'SET', 3, 'SET', 4, 'SET')
                    from vgt_hdi.panel pnl, vgt_hdi.public_items im2
                    where im2.root_id = a.root_id
                    and pnl.item_id = im2.item_id
                    and pnl.revision_id = im2.revision_id)
               end OP_STEP,
               case when d.coupon_sequential_index >0
               then (select round(coup.size_y/1000,1)||'' from vgt_hdi.coupon coup
                     where coup.item_id = b.item_id
                       and coup.revision_id = b.revision_id
                       and d.coupon_sequential_index = coup.sequential_index)
               Else 'No'
               end COUPON_HEIGHT,
               case when d.coupon_sequential_index >0
               then (select round(coup.size_x/1000,1)||'' from vgt_hdi.coupon coup
                     where coup.item_id = b.item_id
                       and coup.revision_id = b.revision_id
                       and d.coupon_sequential_index = coup.sequential_index)
               Else 'No'
               end COUPON_LENGTH,
               round(d.start_x / 1000,4) start_x,--单位inch
               round(d.start_y / 1000,4) start_y,--单位inch
               d.number_x X_NUM,
               d.number_y Y_NUM,
               round(d.delta_x / 1000,4) delta_x,--单位inch
               round(d.delta_y / 1000,4) delta_y,--单位inch
               d.rotation_angle,--旋转角度
               d.flip--是否镜像
          from vgt_hdi.public_items  a,
               vgt_hdi.job           b,
               vgt_hdi.public_items  e,
               vgt_hdi.panel         c,
               vgt_hdi.layout_repeat d
         where a.item_id = b.item_id
           and a.revision_id = b.revision_id
           and a.root_id = e.root_id
           and e.item_id = c.item_id
           and e.revision_id = c.revision_id
           and c.item_id = d.item_id
           and c.revision_id = d.revision_id
           -- and e.item_name = 'Panel' --默认只筛选Panel
           and e.item_name like 'Panel%%' --默认只筛选Panel
           and a.item_name = '%s'--变量料号名
           and c.is_main = 1''' % self.JOB_SQL
        # 更新自动抓取AB板 新增条件 c.is_main = 1 20230424 by lyh
        dataVal = self.DB_O.SELECT_DIC (self.dbc_h,sql)
        return dataVal


    def get_Cu_thickness(self):
        """
        获取铜厚信息
        """
        ozList = ['1/3OZ', 'HOZ', '1OZ', '1.5OZ', '2OZ', '2.5OZ', '3OZ', '3.5OZ', '4OZ', '4.5OZ', '5OZ']
        ozDic = {
            '0.32': '1/3OZ', '0.33': '1/3OZ', '0.34': '1/3OZ',
            '0.49': 'HOZ', '0.50': 'HOZ', '0.51': 'HOZ',
            '0.99': '1OZ', '1.00': '1OZ', '1.01': '1OZ',
            '1.49': '1.5OZ', '1.50': '1.5OZ', '1.51': '1.5OZ',
            '1.99': '2OZ', '2.00': '2OZ', '2.01': '2OZ',
            '2.49': '2.5OZ', '2.50': '2.5OZ', '2.51': '2.5OZ',
            '2.99': '3OZ', '3.00': '3OZ', '3.01': '3OZ',
            '3.49': '3.5OZ', '3.50': '3.5OZ', '3.51': '3.5OZ',
            '3.99': '4OZ', '4.00': '4OZ', '4.01': '4OZ',
            '4.49': '4.5OZ', '4.50': '4.5OZ', '4.51': '4.5OZ',
            '4.99': '5OZ', '5.00': '5OZ', '5.01': '5OZ'
        }
        dict = {}
        list_data = self.get_Layer_Info()
        if list_data:
            for i in list_data:
                cu_oz = str("%0.2f" % i['CU_WEIGHT'])
                dict[i.get('LAYER_NAME')] = ozDic.get(cu_oz)
            return dict
        else:
            return None

class InfoJob:
    def __init__(self):
        self.inner = []
        res = self.checkJob()
        if res:
            self.getInfo()
        else:
            sys.exit(0)


    def checkJob(self):
        res_check = True
        inner_layers = GEN.GET_ATTR_LAYER('inner')
        inner_num = int(jobName[4:6]) - 2
        if inner_num != len(inner_layers):
            showMessageInfo(u"层数不对,请检查!")
            res_check = False
        try:
            list_numbers = [int(i[1:])-2 for i in inner_layers]
            list_numbers.sort()
            if list_numbers != range(inner_num):
                showMessageInfo(u"内层命名错误，请修正!")
                res_check = False
        except:
            showMessageInfo(u"内层命名错误，请修正1!")
            res_check = False
        return res_check

    def getInfo(self):
        matrixInfo = GEN.DO_INFO('-t matrix -e %s/matrix' % jobName)
        for i, lay in enumerate(matrixInfo["gROWname"]):
            if matrixInfo["gROWcontext"][i] == "board":
                if matrixInfo["gROWlayer_type"][i] == "signal" or matrixInfo["gROWlayer_type"][i] == "power_ground":
                    if matrixInfo["gROWside"][i] == "inner":
                        dict_signal = {}
                        dict_signal['name'] = lay
                        if matrixInfo["gROWpolarity"][i] == "positive":
                            dict_signal['pol'] = "positive"
                        else:
                            dict_signal['pol'] = "negative"
                        self.inner.append(dict_signal)

    def pnl_exits(self):
        if 'pnl_m' in GEN.GET_STEP_LIST():
            return True
        else:
            return False


class SelWindow(QWidget, Ui_Form):
    def __init__(self):
        super(SelWindow, self).__init__()
        self.lx,self.yx,self.fx = {'size':'40','space':'7.5'},{'size':'40','space':'7.5'},{'size':'40','space':'7.5'}
        self.initUI()
        self.signalControl()

    def initUI(self):
        self.setupUi(self)
        self.setWindowTitle(u'设置大小')
        for i in [self.lx_size,self.yx_size,self.fx_size]:
            i.setText('40')
        for i in [self.lx_space,self.yx_space,self.fx_space]:
            i.setText('7.5')

    def signalControl(self):
        self.pushButton_exit.clicked.connect(self.close)
        self.pushButton_apply.clicked.connect(self.run)

    def run(self):
        errors = []
        self.lx['size'] = str(self.lx_size.text())
        self.yx['size'] = str(self.yx_size.text())
        self.fx['size'] = str(self.fx_size.text())
        self.lx['space'] = str(self.lx_space.text())
        self.yx['space'] = str(self.yx_space.text())
        self.fx['space'] = str(self.fx_space.text())
        if not is_number(self.lx['size']):
            errors.append(u'菱形尺寸输出错误，')
        if not is_number(self.yx['size']):
            errors.append(u'圆形尺寸输出错误，')
        if not is_number(self.fx['size']):
            errors.append(u'方形尺寸输出错误，')
        if not is_number(self.lx['space']):
            errors.append(u'菱形间距输出错误，')
        if not is_number(self.yx['space']):
            errors.append(u'圆形间距输出错误，')
        if not is_number(self.fx['space']):
            errors.append(u'方形间距输出错误，')
        if errors:
            STR = ''.join(errors)
            showMessageInfo(STR)
        else:
            self.close()

class MyWindow(QMainWindow, Ui_MainWindow):
    """
    前端界面
    """
    show_res = {'copper': True,
                'pnl': True}
    icon_r = QtGui.QIcon()
    icon_r.addPixmap(QtGui.QPixmap("{0}/png/jtr.png".format(_main_path)), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    icon_d = QtGui.QIcon()
    icon_d.addPixmap(QtGui.QPixmap("{0}/png/jtd.png".format(_main_path)), QtGui.QIcon.Normal, QtGui.QIcon.Off)

    def __init__(self):
        super(MyWindow, self).__init__()

        self.set_copper_types = [u"实心铜皮", u"菱形铜块", u"圆形铜豆", u"方形铜块"]
        self.pnl_copper_types = [u"梯形", u"蜂窝",'None']
        self.initUI()
        self.setTable()
        self.signalControl()

    def initUI(self):
        """
        初始化各类设置
        """
        self.setupUi(self)
        # self.pushButton_copper.setEnabled(pb.pnl_exits())
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        # self.setWindowTitle(u'set制作流程')
        # 禁止窗口最大化和拉伸
        self.setFixedSize(self.width(), self.height())
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        styleSheet = 'QComboBox{font:12pt;background-color: rgb(253, 199, 77);margin:3px;border: 1px solid gray;' \
                     'border-radius: 3px;padding: 1px 2px 1px 2px}'
        self.comboBox_copper_type_set.addItems(self.set_copper_types)
        self.comboBox_copper_type_set.setStyleSheet(styleSheet)
        # self.comboBox_copper_type_pnl.addItems([u"梯形", u"蜂窝"])
        # self.comboBox_copper_type_pnl.hide()
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("{0}/png/set.png".format(_main_path)), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_set_size.setIcon(icon)
        self.pushButton_copper.setIcon(self.icon_d)
        self.pushButton_creat_pnl.setIcon(self.icon_d)
        pixmap = QtGui.QPixmap("{0}/png/sh_logo.png".format(_main_path))
        self.sh_log.setPixmap(pixmap)
        # 各类按钮样式
        for btn in self.findChildren(QtGui.QPushButton):
            btn.setStyleSheet('''QPushButton:hover{background:rgb(170, 255, 255);}''')

    def fill_pnl(self):
        """
        首先获取pnl信息
        """
        info = GEN.DO_INFO('-t step -e %s/pnl_m -d PROF_LIMITS' % jobName, units='mm')
        panel_x = float(info['gPROF_LIMITSxmax'])
        panel_y = float(info['gPROF_LIMITSymax'])
        cusNo = jobName[1:4]
        inplan_list = inplan.get_Cu_thickness()
        if inplan_list:
            for i, lay in enumerate(pb.inner):
                if inplan_list[lay['name']] in ['1/3OZ', 'HOZ', '1OZ', '1.5OZ']:
                    index = 0
                    if panel_x < 546.1 and panel_y < 622.3:
                        index = 1
                else:
                    if cusNo in ('940', '968'):
                        index = 0
                    else:
                        index = 1
                self.table_copper.cellWidget(i,3).setCurrentIndex(index)

    def setTable(self):
        """
        初始化表格
        :return:
        """
        # green = QtGui.QBrush(QtGui.QColor(34, 139, 34))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.table_copper.verticalHeader().setVisible(False)
        self.table_copper.horizontalHeader().setVisible(False)
        self.table_copper.setColumnCount(6)
        self.table_copper.setColumnWidth(0, 62)
        self.table_copper.setColumnWidth(1, 81)
        self.table_copper.setColumnWidth(2, 81)
        self.table_copper.setColumnWidth(3, 81)
        self.table_copper.setColumnWidth(4, 60)
        self.table_copper.setRowCount(len(pb.inner))
        color_bg = QtGui.QColor(255, 215, 0)
        for i , d in enumerate(pb.inner):
            self.table_copper.setRowHeight(i, 25)
            # 第一列
            item = QTableWidgetItem(d['name'])
            item.setBackground(color_bg)
            item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
            item.setFont(font)
            self.table_copper.setItem(i, 0, item)
            #第二列
            item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
            item.setBackground(color_bg)
            item = QTableWidgetItem(d['pol'])
            item.setFont(font)
            item.setBackground(color_bg)
            self.table_copper.setItem(i, 1, item)
            # 第三列
            wgt = QtGui.QComboBox()
            wgt.addItems(self.set_copper_types)
            # wgt.setAlignment(QtCore.Qt.AlignCenter)
            self.table_copper.setCellWidget(i, 2, wgt)
            # 第四列
            wgt = QtGui.QComboBox()
            wgt.addItems(self.pnl_copper_types)
            wgt.setCurrentIndex(2)
            # wgt.setAlignment(QtCore.Qt.AlignCenter)
            self.table_copper.setCellWidget(i, 3, wgt)
        if not pb.pnl_exits():
            self.frame_copper.hide()
            self.show_res['copper'] = False
        else:
            self.fill_pnl()
            self.fram_desiger.hide()
            self.show_res['pnl'] = False
        if set_inplan:
            self.pCSSETLineEdit.setText(str(set_inplan['num']))
            self.sET_XLineEdit.setText(str(set_inplan['x'])+ 'mm')
            self.sET_YLineEdit.setText(str(set_inplan['y'])+ 'mm')
        if pnl_inplan:
            self.pCSSETLineEdit_2.setText(str(pnl_inplan['num']))
            self.sET_XLineEdit_2.setText(str(pnl_inplan['x']) + 'inch')
            self.sET_YLineEdit_2.setText(str(pnl_inplan['y']) + 'inch')

    def signalControl(self):
        """
        信号控制槽函数
        """
        self.pushButton_exit.clicked.connect(sys.exit)
        self.pushButton_apply.clicked.connect(self.allApply)
        self.pushButton_desiger.clicked.connect(self.desigerApply)
        self.pushButton_set_size.clicked.connect(self.showWgt)
        self.pushButton_updata.clicked.connect(self.upArea)
        self.action.triggered.connect(self.getMenu)
        self.pushButton_back.clicked.connect(self.showWindow)
        # 展示和隐藏按钮
        self.pushButton_creat_pnl.clicked.connect(
            lambda: self.showSetLayer([self.pushButton_creat_pnl, self.fram_desiger, 'pnl']))
        self.pushButton_copper.clicked.connect(
            lambda: self.showSetLayer([self.pushButton_copper, self.frame_copper, 'copper']))
        # 同步切换表格内铺铜方式
        self.comboBox_copper_type_set.currentIndexChanged.connect(self.change_addcoppertable_in_type)
        # self.comboBox_copper_type_pnl.currentIndexChanged.connect(self.change_addcoppertable_out_type)
    def showWindow(self):
        self.hide()
        GEN.PAUSE("PAUSE,CLICK CONTINUE SCRIPT!")
        self.show()

    def upArea(self):
        up_data = CalculateCopperArea().main()
        eros = [d['name'] for d in up_data if not d['pc']]
        if eros:
            STR = ','.join(eros)
            showMessageInfo(u"%s没有获取到pnl边残铜率，请确认是否已运行铺铜程序！" % STR)
        else:
                mysql = CONNECTMYSQL(jobName)
                if platform.system() == "Windows":
                    # host_name = socket.gethostname()
                    host_name = os.environ.get("USERNAME")
                else:
                    host_name = GEN.getUser()
                file_path = os.path.dirname(os.path.abspath(__file__))

                try:
                    STR = [d['name'] + "=" + str(d['pc']) for d in up_data]
                    # with open(file_path + '/ww.txt', 'a') as f:
                    #     f.write(jobName + ':' + ','.join(STR) + '\n')
                    for d in up_data:
                        if d['ww']:
                            note_str = "%s,ww=True" % d['type']
                        else:
                            note_str = "%s,ww=Flase" % d['type']
                        if mysql.checkData(d['name']):
                            mysql.upData(values=d['pc'], computer=host_name, layer=d['name'] ,note=note_str)
                        else:
                            mysql.insertData(values=d['pc'], computer=host_name, layer=d['name'], note=note_str)
                    msg = msgBox()
                    msg.information(self, u"提示", u"数据上传成功!\n" + u'料号:' + jobName + '\n' + '\n'.join(STR),
                                    QMessageBox.Ok)
                    # GEN.CLOSE_JOB(jobName)
                    self.close()

                except:
                    msg = msgBox()
                    msg.warning(self, u"提示", u"数据上传失败", QMessageBox.Ok)


    def change_addcoppertable_in_type(self, index):
        for i in range(self.table_copper.rowCount()):
            self.table_copper.cellWidget(i, 2).setCurrentIndex(index)

    def change_addcoppertable_out_type(self, index):
        for i in range(self.table_copper.rowCount()):
            self.table_copper.cellWidget(i, 3).setCurrentIndex(index)


    def showWgt(self):
        # 禁止窗口最大化和拉伸
        wgt_win.setFixedSize(wgt_win.width(), wgt_win.height())
        wgt_win.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)
        wgt_win.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        wgt_win.show()

    def getMenu(self):
        # dlg = MyDialog()
        dlg.show()

    def desigerApply(self):
        if 'pnl_m' in GEN.GET_STEP_LIST():
            showMessageInfo(u"已经存在pnl_m拼版，重新拼版请先手动删除!")
        else:
            try:
                if not 'set_m' in GEN.GET_STEP_LIST():
                    if not 'orig' in GEN.GET_STEP_LIST():
                        showMessageInfo(u"没有名称为orig的STEP，请创建后再运行拼版!")
                    else:
                        Set_desiger()
                if 'set_m' in GEN.GET_STEP_LIST():
                    if not 'pnl_m' in GEN.GET_STEP_LIST():
                        res = Pnl_desiger()
                        if res.reback == True:
                            showMessageInfo(u"拼版已经完成，确认无误后点击下方按钮运行铺铜！")
                            self.pushButton_copper.setEnabled(True)
                            self.pushButton_copper.setIcon(self.icon_d)
                            self.frame_copper.show()
                            self.fill_pnl()
            except:
                pass

    def allApply(self):
        # 执行铺铜
        add_list = []
        add_outdata = {}
        table_add_rows = self.table_copper.rowCount()
        for i in range(table_add_rows):
            add_dict = {}
            add_dict['name'] = self.table_copper.item(i, 0).text()
            add_dict['pol'] = self.table_copper.item(i, 1).text()
            add_dict['set'] = self.table_copper.cellWidget(i, 2).currentText()
            add_dict['pnl'] = self.table_copper.cellWidget(i, 3).currentText()
            add_list.append(add_dict)
        add_outdata['list'] = add_list
        add_outdata['lx'] = wgt_win.lx
        add_outdata['yx'] = wgt_win.yx
        add_outdata['fx'] = wgt_win.fx
        if 'pnl_m' in GEN.GET_STEP_LIST() and not 'None' in [i['pnl'] for i in add_list]:
            # 检查是否有ww层
            eros = None
            if GEN.LAYER_EXISTS('ww', step='set_m') == 'yes':
                info = GEN.INFO("-t layer -e %s/set_m/ww  -d FEATURES" % os.environ.get("JOB"))
                if len(info) < 2:
                    eros= "set_m中ww层没有物件!"
            else:
                eros= "资料中没有ww层!"
            res = None
            if eros:
                msg = msgBox()
                qes = msg.question(self,"提示", "每set中含有%s单只;\n 程序中检测到:" % set_inplan['num'] +eros + '\n' + "请确认是否继续？" , QMessageBox.Yes , QMessageBox.No)
                if qes == '是':
                    res= Count_copper_area(add_outdata)
                    if res.res:
                        showMessageInfo(u"板边铺铜已完成")
            else:
                res= Count_copper_area(add_outdata)
                if res.res:
                    showMessageInfo(u"板边铺铜已完成")
            if res.pcr:
                for i in range(len(pb.inner)):
                    lay = self.table_copper.item(i, 0).text()
                    font = QtGui.QFont()
                    font.setPointSize(10)
                    var_pc = ''
                    var_note = ''
                    color_bg = QtGui.QColor(0, 195, 255)
                    for d in res.pcr:
                        if d['name'] == lay:
                            if not d['pc'] or d['pc']=='0':
                                color_bg = QtGui.QColor(255, 0, 0)
                                var_note = u'空值'
                            else:
                                var_pc = d['pc']
                                if float(d['pc']) < 30:
                                    var_note = u'过低'
                                    color_bg = QtGui.QColor(255, 0, 0)

                    item = QTableWidgetItem(var_pc)
                    item.setForeground(color_bg)
                    item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
                    item.setFont(font)
                    self.table_copper.setItem(i, 4, item)

                    item = QTableWidgetItem(var_note)
                    item.setForeground(color_bg)
                    item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
                    item.setFont(font)
                    self.table_copper.setItem(i, 5, item)

        else:
            if not 'pnl_m' in GEN.GET_STEP_LIST():
                showMessageInfo(u"请拼完PNL后运行此程序!")
            else:
                showMessageInfo(u"PNL中未选择正确的铺铜方式")

    def show_cut_insert_lj(self):
        if self.checkBox_addcopper_lj.isChecked():
            self.widget_lj.show()
        else:
            self.widget_lj.hide()


    def showSetLayer(self, d):
        obj = d[0]
        wgt = d[1]
        icon = self.set_icon_type()
        if self.show_res[d[2]] == False:
            icon.addPixmap(QtGui.QPixmap("{0}/png/jtd.png".format(_main_path)), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            wgt.show()
            self.show_res[d[2]] =True
        else:
            icon.addPixmap(QtGui.QPixmap("{0}/png/jtr.png".format(_main_path)), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            wgt.hide()
            self.show_res[d[2]] = False
        obj.setIcon(icon)

    def set_icon_type(self, boll = True):
        icon = QtGui.QIcon()
        if boll:
            icon.addPixmap(QtGui.QPixmap("{0}/png/jtd.png".format(_main_path)), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        else:
            icon.addPixmap(QtGui.QPixmap("{0}/png/jtr.png".format(_main_path)), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        return icon

    def change_addcopper_ischeck(self,index):
        row_count = self.table_copper.rowCount()
        for i in range(row_count):
            if index == 1:
              self.table_copper.cellWidget(i, 0).setChecked(True)
            elif index == 2:
                self.table_copper.cellWidget(i, 0).setChecked(False)

    def showAddFram(self, index):
        """
        点击按钮导入inplan钻孔的信息
        """
        if index==0:
            if self.cb_addSlotHole.isChecked():
                self.fram_slot.show()
            else:
                self.fram_slot.hide()
        elif index==1:
            if self.cb_tableHole.isChecked():
                self.fram_tablehole.show()
            else:
                self.fram_tablehole.hide()

    def addCheckBox(self, check_type):
        """
        在表格中加入checkBOX，必须先放入一个容器widget
        :param check:
        :return:
        """
        widget = QtGui.QWidget()
        checkbox = QtGui.QCheckBox()
        checkbox.setChecked(check_type)
        # self.meth.setCheckBox(checkbox)
        widget.setChecked = checkbox.setChecked
        widget.checkState = checkbox.checkState
        widget.isChecked = checkbox.isChecked
        widget.clicked = checkbox.clicked
        #checkbox.setStyleSheet(Methed().setCheckBox('checkbox'))
        h = QHBoxLayout()
        h.addWidget(checkbox)
        h.setAlignment(QtCore.Qt.AlignHCenter)
        widget.setLayout(h)
        return widget

    def setCheckBox(self, wgt):
        STR = ("#%s{\n"
                "font-size: 12px;\n"
                "}\n"
                " \n"
                "#%s::indicator {\n"
                "padding-top: 1px;\n"
               "width: 22px;\n"
               "height: 22px;border: none;\n"
               "}\n"
               " \n"
               "#%s::indicator:unchecked {\n"
               "    image: url(:/pic/images/uncheck.png);\n"
               "}\n"
               " \n"
               "#%s::indicator:checked {\n"
               "    image: url(:/pic/images/cb_checked.png);\n"
               "}" % (wgt, wgt, wgt, wgt))
        return STR


class MyDialog(QtGui.QDialog):
    def __init__(self):
        super(MyDialog,self).__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle(u"说明文件")
        self.resize(1400,850)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        # self.setGeometry(1000, 800, 300, 200)
        label = QtGui.QLabel("Hello World!", self)
        path = os.path.dirname(os.path.abspath(__file__))
        pixmap = QtGui.QPixmap(path + "/note.jpg")
        # proportion = pixmap.height() / self.height()
        # pixmap.setDevicePixelRatio(proportion)
        label.setPixmap(pixmap)
        label.move(100, 50)


class Pnl_desiger:
    def __init__(self):
        self.GEN = GEN_COM()
        self.reback = False
        self.pnl_name = 'pnl_m'
        self.creat_pnl()
        self.GEN.COM("zoom_home")

    def creat_pnl(self):
        if 'pnl_m' in self.GEN.GET_STEP_LIST():
            self.GEN.COM("delete_entity,job=%s,type=step,name=%s" % (jobName,self.pnl_name))
        self.GEN.COM("create_entity,job=%s,is_fw=no,type=step,name=%s,db=,fw_type=form" % (jobName, self.pnl_name))
        self.GEN.OPEN_STEP(self.pnl_name)
        self.GEN.CHANGE_UNITS('inch')
        self.GEN.FILTER_RESET()
        self.GEN.COM("profile_rect,x1=0,y1=0,x2=%s,y2=%s" % (pnl_inplan['x'], pnl_inplan['y']))
        n = 1
        for dict in pnl_inplan['set']:
            if dict.get('OP_STEP') == "SET":
                p = {}
                p['ang'] = dict['ROTATION_ANGLE']
                p['dx'] = dict['DELTA_X']
                p['dy'] = dict['DELTA_Y']
                p['point_x'] = dict['START_X']
                p['point_y'] = dict['START_Y']
                p['nx'] = dict['X_NUM']
                p['ny'] = dict['Y_NUM']
                self.add_setm(n, p)
                n += 1
        self.check_pnl()
        self.reback = True

    def check_pnl(self):
        xmid = pnl_inplan['x'] / 2
        ymid = pnl_inplan['y'] / 2
        self.GEN.COM("sredit_keep_sr_pattern,keep_sr_entry=yes")
        self.GEN.COM("sredit_keep_gap,keep_gap=yes")
        self.GEN.COM("sredit_keep_margin,keep_margin=yes")
        self.GEN.COM("sredit_sel_clear")
        self.GEN.COM("sredit_pack_steps, mode = vcenter,pos=%s" % ymid)
        self.GEN.COM("sredit_sel_clear")
        self.GEN.COM("sredit_pack_steps, mode = hcenter,pos=%s" % xmid)
        # self.GEN.COM(
        #     "sredit_pack_steps, mode = hcenter, hgap = 0.2, vgap = 0.2, pos = 9.19, pos2 = 0, overlap_tol = 0.0000007874")


    def add_setm(self, index, d):
        self.GEN.COM('sr_tab_add,line=%s,step=set_m,x=0,y=0,nx=1,ny=1' % (index))
        self.GEN.COM('sr_tab_change,line=%s,step=set_m,x=%s,y=%s,nx=%s,ny=%s,dx=%s,dy=%s,angle=%s' % (
            index, d['point_x'], d['point_y'], d['nx'], d['ny'], d['dx'], d['dy'], d['ang']))



class Set_desiger:
    def __init__(self):
        self.GEN = GEN_COM()
        self.set_name = 'set_m'
        if not 'set' in self.GEN.GET_STEP_LIST():
            if not 'pcs_m' in self.GEN.GET_STEP_LIST():
                # 检查原稿层有没有out层
                res = self.GEN.LAYER_EXISTS('out', job=jobName, step='orig')
                if res == 'no':
                    showMessageInfo(u"orig中没有out层!")
                else:
                    info = self.GEN.INFO("-t layer -e %s/orig/out -d FEATURES" % jobName)[1:]
                    if info:
                        self.creat_pcbm()
                        self.GEN.COM("create_entity,job=%s,is_fw=no,type=step,name=%s,db=,fw_type=form" % (
                        jobName, self.set_name))
                        self.main_run()
                    else:
                        showMessageInfo(u"orig中out层不正确，没有物件！")

        else:
            info_s = self.GEN.DO_INFO("-t step -e %s/set -d REPEAT" % jobName)
            if info_s['gREPEATstep']:
                self.GEN.COPY_ENTITY('step', jobName, 'set', jobName, 'set_m')
            else:
                showMessageInfo(u"单只拼版的不要命名为set，请先更名!")

    def main_run(self):
        set_x = set_inplan['x']
        set_y = set_inplan['y']
        num = set_inplan['num']
        # pcs_x, pcs_y = self.GEN.GET_PROFILE_SIZE(jobName,'pcs_m')
        self.GEN.OPEN_STEP(self.set_name)
        self.GEN.CHANGE_UNITS('mm')
        if jobName[1:4] == '815':
            s_mar = 1.2
        elif jobName[1:4] == '975':
            s_mar = 2
        else:
            s_mar = 0
        # self.GEN.COM("sr_auto,step=pcs_m,num_mode=multiple,xmin=0,ymin=0,width=%s,height=%s,panel_margin=0,step_margin=3,"
        #              "gold_plate=no,orientation=any,evaluate=no,active_margins=yes,top_active=0,bottom_active=0,left_active=0,"
        #              "right_active=0,step_xy_margin=no,step_margin_x=3,step_margin_y=3")
        self.GEN.COM("sr_auto,step=pcs_m,num_mode=multiple,xmin=0,ymin=0,width=%s,height=%s,panel_margin=0,step_margin=%s,"
                     "gold_plate=no,orientation=any,evaluate=no,active_margins=yes,top_active=0,bottom_active=0,left_active=0,"
                     "right_active=0,step_xy_margin=no,step_margin_x=%s,step_margin_y=%s" % (set_x,set_y,s_mar,s_mar,s_mar))

        #自动拼的需要
        info = self.GEN.DO_INFO("-t step -e %s/set_m -d REPEAT" % jobName , units='mm')

        for i in range(len(info['gREPEATstep'])):
            self.GEN.VOF()
            self.GEN.COM("sr_tab_break,line=1")
            # self.GEN.COM("sr_tab_break,line=%s" % str(i + 1))
            self.GEN.VON()

        if len(info['gREPEATstep']) != num:
            if len(info['gREPEATstep']) > num:
                # 打散后删除
                for i in range(len(info['gREPEATstep']) - num):
                    self.GEN.COM("sr_tab_del,line=%s" % str(i+1))
                    # self.GEN.COM("sredit_sel_clear")
                    # self.GEN.COM("sredit_sel_step_xy,x=%s,y=%s,select=yes,cyclic=yes" % (info['gREPEATxa'][i], info['gREPEATya'][i]))
                    # self.GEN.COM("sredit_del_steps")
            else:
                while True:
                    self.GEN.PAUSE("erros! please Manual layout!")
                    info_set = self.GEN.DO_INFO("-t step -e %s/set_m -d REPEAT", units='mm')['gREPEATstep']
                    if len(info_set) != num:
                        self.GEN.PAUSE("erros! please Manual layout!")
                    else:
                        break

    def creat_pcbm(self):
        self.GEN.COPY_ENTITY('step', jobName, 'orig', jobName, 'pcs_m')
        self.GEN.OPEN_STEP('pcs_m')
        self.GEN.CHANGE_UNITS('inch')
        self.GEN.FILTER_RESET()
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('out', affected='yes')
        self.GEN.FILTER_SET_POL("positive")
        self.GEN.FILTER_SET_FEAT_TYPES("line\;arc")
        self.GEN.FILTER_SELECT()
        if self.GEN.GET_SELECT_COUNT():
            self.GEN.COM("sel_create_profile")
        else:
            showMessageInfo(u"创建profile错误，请检查out层是否正确！")
            self.GEN.COM("delete_entity,job=%s,type=step,name=pcs_m" % (jobName))
            sys.exit(0)
        self.GEN.SEL_CHANEG_SYM('r20')
        # self.GEN.AFFECTED_LAYER('out', affected='no')
        self.GEN.FILTER_RESET()
        for lay in pb.inner:
            self.GEN.COM("clip_area_strt")
            self.GEN.COM("clip_area_end,layers_mode=layer_name,layer=%s,area=profile,area_type=rectangle,"
                         "inout=outside,contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text" % lay['name'])
            if lay['pol'] == 'positive':
                self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=yes"% lay['name'])
            else:
                self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no"% lay['name'])
        self.GEN.AFFECTED_LAYER('out', affected='no')
        self.GEN.CLOSE_STEP()
        # self.GEN.COM("clip_area_strt")
        # self.GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=profile,area_type=rectangle,"
        #              "inout=outside,contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
        # self.GEN.COM("display_layer,name=out,display=yes,number=1")
        # self.GEN.COM("work_layer,name=out")
        # self.GEN.COM("sel_copy_other,dest=affected_layers,target_layer=,invert=yes")
        # self.GEN.CLEAR_LAYER()


class Count_copper_area:
    """
    铺铜
    """
    def __init__(self, data):
        # 'list':'name','pol','set',pnl  'lx',;'yx'
        self.dict = data
        self.meth = Methon()
        self.add_process = False
        self.type_cu_list = [u"实心铜皮", u"菱形铜块", u"圆形铜豆", u"方形铜块"]
        self.tempLay = {
            'fill_cu': "fill_cu_tmp",
            'fill_cu_1': "fill_cu_tmp_1",
            'fill_cu_2': "fill_cu_tmp_2",
            'fill_parten': "fill_parten_tmp",
            'fill_ng': "fill_nagetive_tmp",
            'fill_out_flatten': "fill_out_flatten_tmp",
            'ww_bk': 'ww_bk_tmp'
        }
        # self.tempLj_layer = {'lj_evenlayer': "add_copper_enveljcao",'lj_oddlayer': "add_copper_eoddljcao"}
        # self.fill_set_copper()
        self.del_tmpLayer()
        self.res ,self.pcr = self.fill_pnl_copper()


    def fill_set_copper(self):
        """
        SET铺铜
        """
        lj_str = '39.37'
        list_lx, list_yx, list_fx, list_cu = [], [], [], []
        for d in self.dict['list']:
            # 内层和外层铺铜类型分下类，提高运行效率
            if d['set'] == self.type_cu_list[1]:
                list_lx.append(d)
            elif d['set'] == self.type_cu_list[2]:
                list_yx.append(d)
            elif d['set'] == self.type_cu_list[3]:
                list_fx.append(d)
            else:
                list_cu.append(d)
        stepName = 'set_m'
        step_cmd = gClasses.Step(job_cmd, stepName)
        # if list_cu:
        #     add_lj = True
        # else:
        #     add_lj = False
        step_cmd.open()
        step_cmd.clearAll()
        for lay in pb.inner:
            step_cmd.affect(lay['name'])
        step_cmd.resetFilter()
        # step_cmd.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.area_name,text=fill_copper')
        step_cmd.selectAll()
        if step_cmd.featureSelected():
            step_cmd.selectDelete()
        step_cmd.resetFilter()
        self.del_tmpLayer()
        self.creat_tmpLayer()
        step_cmd.COM("units,type=inch")
        pf_info = step_cmd.getProfile()
        pf_xmin = pf_info.xmin
        pf_xmax = pf_info.xmax
        pf_ymin = pf_info.ymin
        pf_ymax = pf_info.ymax
        # 处理辅助层
        step_cmd.clearAll()
        step_cmd.affect(self.tempLay['fill_cu'])
        self.meth.sr_fill_surface()
        step_cmd.COM("sel_resize,size=-40,corner_ctl=yes" )
        step_cmd.unaffect(self.tempLay['fill_cu'])
        step_cmd.COM('flatten_layer,source_layer=out,target_layer=%s' % self.tempLay['fill_out_flatten'])
        if step_cmd.isLayer('ww'):
            step_cmd.affect('ww')
            step_cmd.COM('sel_change_sym,symbol=r20,reset_angle=no')
            step_cmd.copySel(self.tempLay['fill_cu'], invert='yes')
            step_cmd.unaffect('ww')
        step_cmd.affect(self.tempLay['fill_out_flatten'])
        # 掏50mil
        step_cmd.COM('sel_change_sym,symbol=r100,reset_angle=no')
        step_cmd.copySel(self.tempLay['fill_cu'],invert='yes')
        step_cmd.unaffect(self.tempLay['fill_out_flatten'])
        step_cmd.affect(self.tempLay['fill_cu'])
        step_cmd.contourize(units ='inch')
        step_cmd.unaffect(self.tempLay['fill_cu'])

        # 处理单只里面锣空区
        # 合并out,ww层
        step_cmd.affect(self.tempLay['fill_cu_1'])
        self.meth.sr_fill_surface('positive', -0.001, -0.001, 100, 100,
                                  sr_margin_x=-100, sr_margin_y=-100, sr_max_dist_x=0.001, sr_max_dist_y=0.001,
                                  nest_sr='yes')
        step_cmd.copySel(self.tempLay['fill_cu_2'])
        step_cmd.COM("sel_resize,size=-6,corner_ctl=no")
        step_cmd.COM("sel_surf2outline,width=5")
        step_cmd.unaffect(self.tempLay['fill_cu_1'])
        step_cmd.COM("flatten_layer,source_layer=out,target_layer=%s" % self.tempLay['ww_bk'])
        if step_cmd.isLayer('ww'):
            step_cmd.affect('ww')
            step_cmd.copySel(self.tempLay['ww_bk'])
            step_cmd.unaffect('ww')
        step_cmd.affect(self.tempLay['ww_bk'])
        step_cmd.changeSymbol('r5')
        step_cmd.copySel(self.tempLay['fill_cu_2'], invert='yes')
        step_cmd.unaffect(self.tempLay['ww_bk'])
        step_cmd.affect(self.tempLay['fill_cu_2'])
        step_cmd.contourize(units='inch')
        # step_cmd.COM('sel_decompose,overlap=yes')
        step_cmd.refSelectFilter(self.tempLay['fill_cu_1'], mode='disjoint')
        if step_cmd.featureSelected():
            step_cmd.moveSel(self.tempLay['fill_cu'])
        step_cmd.unaffect(self.tempLay['fill_cu_2'])
        # 给fill_cu层定属性
        # step_cmd.resetFilter()
        # step_cmd.COM("cur_atr_set,attribute=.area_name,text=fill_copper")
        # step_cmd.resetFilter()
        # 分类型转铜
        if list_lx:
            # 菱形铜块,自建symbol
            wd_lx = self.dict['lx']['size']
            sp_lx = self.dict['lx']['space']
            symbol_lx = 'lx_copper_symbol' + '_' + wd_lx + '_' + sp_lx
            space_pad = math.sin(math.radians(45)) * ((float(wd_lx) + float(sp_lx)) / 1000)
            # 没有symbol则建立
            if step_cmd.DO_INFO("-t symbol -e %s/%s -d EXISTS" % (jobName, symbol_lx))['gEXISTS'] == 'no':
                symbol_layer = 'lx_symbol_angle_tmp'
                step_cmd.removeLayer(symbol_layer)
                self.meth.createLayer(symbol_layer)
                step_cmd.clearAll()
                step_cmd.affect(symbol_layer)
                leng_di = round(math.sqrt(float(wd_lx) ** 2 * 2), 3)
                symbol_pad = 'di%sx%s' % (leng_di, leng_di)
                step_cmd.COM("add_pad,attributes=no,x=%s,y=%s,symbol=%s,polarity=positive" % (0, 0, symbol_pad))
                step_cmd.COM(
                    "add_pad,attributes=no,x=%s,y=%s,symbol=%s,polarity=positive" % (space_pad, space_pad, symbol_pad))
                step_cmd.COM('sel_reverse')
                step_cmd.COM(
                    "sel_create_sym,symbol=%s,x_datum=%s,y_datum=%s,delete=no,fill_dx=0.1,fill_dy=0.1,attach_atr=no,retain_atr=no" % (
                        symbol_lx, space_pad / 2, space_pad / 2))
                step_cmd.unaffect(symbol_layer)
                step_cmd.removeLayer(symbol_layer)
            step_cmd.removeLayer(self.tempLay['fill_parten'])
            step_cmd.createLayer(self.tempLay['fill_parten'])
            step_cmd.copyLayer(jobName,stepName,self.tempLay['fill_cu'], self.tempLay['fill_parten'])
            step_cmd.affect(self.tempLay['fill_parten'])
            cut_yes_no = 'yes'
            self.meth.fill_copper_type(symbol_lx, space_pad + space_pad, space_pad + space_pad, cut_p=cut_yes_no)
            self.clip_fill_copper()
            step_cmd.resetFilter()
            step_cmd.COM("cur_atr_set,attribute=.area_name,text=fill_lx")
            step_cmd.COM("sel_change_atr,mode=add")
            step_cmd.resetFilter()
            for d in list_lx:
                step_cmd.copySel(d['name'])
            step_cmd.unaffect(self.tempLay['fill_parten'])

        if list_yx:
            # 圆形铜豆
            step_cmd.removeLayer(self.tempLay['fill_parten'])
            step_cmd.createLayer(self.tempLay['fill_parten'])
            step_cmd.copyLayer(jobName, stepName, self.tempLay['fill_cu'], self.tempLay['fill_parten'])
            step_cmd.affect(self.tempLay['fill_parten'])
            symbol_name = 'r' + self.dict['yx']['size']
            space_yx = (float(self.dict['yx']['size']) + float(self.dict['yx']['space'])) / 1000
            cut_yes_no = 'no'
            self.meth.fill_copper_type(symbol_name, space_yx, space_yx, cut_p= cut_yes_no)
            step_cmd.resetFilter()
            step_cmd.COM("cur_atr_set,attribute=.area_name,text=fill_yx")
            step_cmd.COM("sel_change_atr,mode=add")
            step_cmd.resetFilter()
            for d in list_yx:
                step_cmd.copySel(d['name'])
            step_cmd.unaffect(self.tempLay['fill_parten'])

        if list_fx:
            # 方形铜块
            step_cmd.removeLayer(self.tempLay['fill_parten'])
            step_cmd.createLayer(self.tempLay['fill_parten'])
            step_cmd.copyLayer(jobName, stepName, self.tempLay['fill_cu'], self.tempLay['fill_parten'])
            step_cmd.affect(self.tempLay['fill_parten'])
            symbol_name = 's' + self.dict['fx']['size']
            space_fx = (float(self.dict['fx']['size']) + float(self.dict['fx']['space'])) / 1000
            cut_yes_no = 'yes'
            self.meth.fill_copper_type(symbol_name, space_fx, space_fx, cut_p=cut_yes_no)
            self.clip_fill_copper()
            step_cmd.resetFilter()
            step_cmd.COM("cur_atr_set,attribute=.area_name,text=fill_fx")
            step_cmd.COM("sel_change_atr,mode=add")
            step_cmd.resetFilter()
            for d in list_fx:
                step_cmd.copySel(d['name'])
            step_cmd.unaffect(self.tempLay['fill_parten'])

        # 如果需要加内层流胶槽，则创建层
        if list_cu:
            # 开流胶槽
            step_cmd.removeLayer(self.tempLj_layer['lj_evenlayer'])
            step_cmd.removeLayer(self.tempLj_layer['lj_oddlayer'])
            self.meth.createLayer(self.tempLj_layer['lj_evenlayer'])
            self.meth.createLayer(self.tempLj_layer['lj_oddlayer'])
            lj_wd = float(lj_str) / 1000
            size_y = pf_ymax - pf_ymin
            size_x = pf_xmax - pf_xmin
            step_cmd.affect(self.tempLj_layer['lj_evenlayer'])
            step_cmd.addLine(xs=pf_xmin + ((size_x / 3) - (lj_wd * 3)), ys=pf_ymin,
                             xe=pf_xmin + ((size_x / 3) - (lj_wd * 3)), ye=pf_ymax,
                             symbol='s' + lj_str, polarity='positive')
            step_cmd.addLine(xs=pf_xmax - ((size_x / 3) - (lj_wd * 3)), ys=pf_ymin,
                             xe=pf_xmax - ((size_x / 3) - (lj_wd * 3)), ye=pf_ymax,
                             symbol='s' + lj_str, polarity='positive')
            step_cmd.addLine(xs=pf_xmin, ys=pf_ymin + ((size_y / 3) - (lj_wd * 3)),
                             xe=pf_xmax, ye=pf_ymin + ((size_y / 3) - (lj_wd * 3)),
                             symbol='s' + lj_str, polarity='positive')
            step_cmd.addLine(xs=pf_xmin, ys=pf_ymax - ((size_y / 3) - (lj_wd * 3)),
                             xe=pf_xmax, ye=pf_ymax - ((size_y / 3) - (lj_wd * 3)),
                             symbol='s' + lj_str, polarity='positive')
            step_cmd.unaffect(self.tempLj_layer['lj_evenlayer'])
            step_cmd.affect(self.tempLj_layer['lj_oddlayer'])
            step_cmd.addLine(xs=pf_xmin + ((size_x / 3) + (lj_wd * 3)), ys=pf_ymin,
                             xe=pf_xmin + ((size_x / 3) + (lj_wd * 3)), ye=pf_ymax,
                             symbol='s' + lj_str, polarity='positive')
            step_cmd.addLine(xs=pf_xmax - ((size_x / 3) + (lj_wd * 3)), ys=pf_ymin,
                             xe=pf_xmax - ((size_x / 3) + (lj_wd * 3)), ye=pf_ymax,
                             symbol='s' + lj_str, polarity='positive')
            step_cmd.addLine(xs=pf_xmin, ys=pf_ymin + ((size_y / 3) + (lj_wd * 3)),
                             xe=pf_xmax, ye=pf_ymin + ((size_y / 3) + (lj_wd * 3)),
                             symbol='s' + lj_str, polarity='positive')
            step_cmd.addLine(xs=pf_xmin, ys=pf_ymax - ((size_y / 3) + (lj_wd * 3)),
                             xe=pf_xmax, ye=pf_ymax - ((size_y / 3) + (lj_wd * 3)),
                             symbol='s' + lj_str, polarity='positive')
            step_cmd.unaffect(self.tempLj_layer['lj_oddlayer'])
            # 创建两层
            step_cmd.removeLayer('fill_cu_tmp1_')
            step_cmd.removeLayer('fill_cu_tmp2_')
            step_cmd.createLayer('fill_cu_tmp1_')
            step_cmd.createLayer('fill_cu_tmp2_')
            step_cmd.copyLayer(jobName, stepName, self.tempLay['fill_cu'],  'fill_cu_tmp1_')
            step_cmd.copyLayer(jobName, stepName, self.tempLay['fill_cu'], 'fill_cu_tmp2_')
            step_cmd.clearAll()
            step_cmd.affect('fill_cu_tmp1_')
            self.meth.clip_area_copper(refLay=self.tempLj_layer['lj_evenlayer'])
            step_cmd.resetFilter()
            step_cmd.COM("cur_atr_set,attribute=.area_name,text=fill_cu")
            step_cmd.COM("sel_change_atr,mode=add")
            step_cmd.resetFilter()
            step_cmd.unaffect('fill_cu_tmp1_')
            step_cmd.affect('fill_cu_tmp2_')
            self.meth.clip_area_copper(refLay=self.tempLj_layer['lj_oddlayer'])
            step_cmd.resetFilter()
            step_cmd.COM("cur_atr_set,attribute=.area_name,text=fill_cu")
            step_cmd.COM("sel_change_atr,mode=add")
            step_cmd.resetFilter()
            step_cmd.unaffect('fill_cu_tmp2_')
            for d in list_cu:
                if int(d['name'][1:]) % 2:
                    step_cmd.affect('fill_cu_tmp1_')
                    step_cmd.copySel(d['name'])
                    step_cmd.unaffect('fill_cu_tmp1_')
                else:
                    step_cmd.affect('fill_cu_tmp2_')
                    step_cmd.copySel(d['name'])
                    step_cmd.unaffect('fill_cu_tmp2_')
            step_cmd.removeLayer('fill_cu_tmp1_')
            step_cmd.removeLayer('fill_cu_tmp2_')
        step_cmd.resetFilter()
        # 将内层负性的反向
        for d in self.dict['list']:
            if d['pol'] == 'negative':
                step_cmd.affect(self.tempLay['fill_ng'])
                step_cmd.selectDelete()
                self.meth.sr_fill_surface(step_margin_x= -0.01,step_margin_y=-0.01)
                step_cmd.unaffect(self.tempLay['fill_ng'])
                step_cmd.affect(d['name'])
                step_cmd.moveSel(self.tempLay['fill_ng'], invert='yes')
                step_cmd.unaffect(d['name'])
                step_cmd.affect(self.tempLay['fill_ng'])
                step_cmd.moveSel(d['name'])
                step_cmd.unaffect(self.tempLay['fill_ng'])
        step_cmd.close()

    def clip_fill_copper(self):
        # 去除细丝
        GEN.COM("sel_resize,size=-10,corner_ctl=no")
        GEN.COM("sel_resize,size=10,corner_ctl=no")
        GEN.COM("fill_params,type=solid,origin_type=limits,solid_type=fill,std_type=line,min_brush=5,use_arcs=yes")
        GEN.COM("sel_fill")
        GEN.SEL_CONTOURIZE(accuracy=0.1,clean_hole_size=3)

    def fill_pnl_copper(self):
        # pnl边铺铜
        res = Pnl_fill_copper(self.dict['list'])
        # if res.re_back:
        #     showMessageInfo(u"板边铺铜已完成")
        return res.re_back, res.pc_areas

    def del_tmpLayer(self):
        for lay in self.tempLay.values():
            GEN.VOF()
            GEN.DELETE_LAYER(lay)
            GEN.VON()

    def creat_tmpLayer(self):
        for lay in self.tempLay.values():
            GEN.VOF()
            GEN.CREATE_LAYER(lay)
            GEN.VON()

    def __del__(self):
        # self.del_tmpLayer()
        pass

class Parm:
    def __init__(self):
        self.fill_array = []
        info_pr = GEN.getProMinMax(jobName, 'pnl_m')
        self.profile_xmin = float(info_pr['proXmin'])
        self.profile_ymin = float(info_pr['proYmin'])
        self.profile_xmax = float(info_pr['proXmax'])
        self.profile_ymax = float(info_pr['proYmax'])
        info_sr = GEN.getSrMinMax(jobName, 'pnl_m')
        self.sr_xmin = float(info_sr['srXmin'])
        self.sr_ymin = float(info_sr['srYmin'])
        self.sr_xmax = float(info_sr['srXmax'])
        self.sr_ymax = float(info_sr['srYmax'])
        self.lamin_data = lamin_data_check

        self.lamin_num = self.get_yh_number()
        self.yh_num = max([int(i['PROCESS_NUM']) for i in self.lamin_data]) - 1
        # --设置锣边后尺寸
        self.lam_rout= [
            (int(i['PROCESS_NUM']) - 1, float(i['PNLROUTX']) * 25.4, float(i['PNLROUTY']) * 25.4) for i in
            self.lamin_data]
        self.rout_x = [i['PNLROUTX'] for i in self.lamin_data if (int(i['PROCESS_NUM']) - 1) == self.yh_num][0] * 25.4
        self.rout_y = [i['PNLROUTY'] for i in self.lamin_data if (int(i['PROCESS_NUM']) - 1) == self.yh_num][0] * 25.4
        if self.rout_x == 0 and self.rout_y == 0:
            # === 双面板此项为0，四层板以上有检测
            self.top_after_margin = self.sr_ymin
            self.left_after_margin = self.sr_xmin
        else:
            self.top_after_margin = self.sr_ymin - (self.profile_ymax - self.rout_y) * 0.5
            self.left_after_margin = self.sr_xmin - (self.profile_xmax - self.rout_x) * 0.5

    def get_yh_number(self):
        dict = {}
        for i in self.lamin_data:
            dict[str(i.get('FROMLAY')).lower()] = i['PROCESS_NUM']
            dict[str(i.get('TOLAY')).lower()] = i['PROCESS_NUM']
        return dict

class Pnl_fill_copper:
    """
    pnl板边铺铜
    """

    def __init__(self, data):
        self.fill_array = data
        self.meth = Methon()
        self.re_back = False
        self.pc_areas = []
        self.parm = Parm()
        self.GEN = GEN_COM()
        self.GEN.OPEN_STEP('pnl_m')
        self.GEN.FILTER_RESET()
        self.GEN.CHANGE_UNITS('mm')
        self.JOB = os.environ.get('JOB', None)
        self.STEP = 'pnl_m'
        for d in data:
            self.GEN.AFFECTED_LAYER(d['name'],affected='yes')
        self.GEN.SEL_DELETE()
        self.GEN.CLEAR_LAYER()
        self.del_tmplayers()
        self.create_honeycomb_tmp()
        self.get_sr_honeycomb()
        self.cusNo = self.JOB[1:4]
        self.put_copper()


    def __del__(self):
        self.del_tmplayers()

    def del_tmplayers(self):
        # --删除临时层别
        self.GEN.VOF()
        self.GEN.DELETE_LAYER('honeycomb-t')
        self.GEN.DELETE_LAYER('honeycomb-b')
        self.GEN.DELETE_LAYER('honeycomb-tsr')
        self.GEN.DELETE_LAYER('honeycomb-bsr')
        self.GEN.DELETE_LAYER('honeycomb-tmp1')
        self.GEN.DELETE_LAYER('honeycomb-tmp2')
        self.GEN.DELETE_LAYER('honeycomb-tmp3')
        self.GEN.DELETE_LAYER('honeycomb-tmp4')
        self.GEN.DELETE_LAYER('honeycomb-tmp5')
        self.GEN.DELETE_LAYER('honeycomb-tok')
        self.GEN.DELETE_LAYER('honeycomb-bok')
        self.GEN.VON()

    def get_copper_area(self, lay_1):
        unit = self.GEN.GET_UNITS()
        if unit == 'mm':
            self.GEN.CHANGE_UNITS('inch')
        self.GEN.VOF()
        self.GEN.COM('copper_area, layer1 = %s, layer2 = , drills = no, consider_rout = no, ignore_pth_no_pad = no, drills_source = matrix,thickness = 0, '
                     'resolution_value = 1, x_boxes = 3, y_boxes = 3, area = no, dist_map = yes' % lay_1)
        Arec_V = self.GEN.COMANS
        area = self.GEN.STATUS
        self.GEN.VON()
        self.GEN.CHANGE_UNITS(unit)
        # --返回
        if area == 0:
            # --以空格分隔出数组
            # Area = '%.1f' % float(Arec_V.split(' ')[0])
            PerCent = '%.1f' % float(Arec_V.split(' ')[1])
            return PerCent
        else:
            return False

    def put_copper(self):
        """
        依据fill_array指定的铺铜方式进行铺铜
        :return:
        :rtype:
        """
        fill_sym_list = [d['pnl'] for d in self.fill_array]
        lam_rout = self.parm.lam_rout

        if u'蜂窝' in fill_sym_list:
            self.create_honeycomb_sym()
        if u'梯形' in fill_sym_list:
            self.create_ladder_sym()
            self.GEN.PAUSE("tt")
        print(self.fill_array)
        self.GEN.PAUSE('A')
        for d in self.fill_array:
            layer_name = str(d['name'])
            layer_side = d['pol']
            panel_fill = d['pnl']
            try:
                cur_lamin_num = self.parm.lamin_num[layer_name] - 1
            except:
                cur_lamin_num = 0
            source_layer = ''
            if panel_fill == u'梯形':
                layer_num = layer_name[1:]
                if int(layer_num) % 2 == 0:
                    source_layer = 'ladder_top%s' % cur_lamin_num
                else:
                    source_layer = 'ladder_bot%s' % cur_lamin_num
            elif panel_fill == u'蜂窝':
                layer_num = layer_name[1:]
                if int(layer_num) % 2 == 0:
                    source_layer = 'honeycomb-tok%s' % cur_lamin_num
                else:
                    source_layer = 'honeycomb-bok%s' % cur_lamin_num
            self.GEN.CLEAR_LAYER()
            self.GEN.FILTER_RESET()
            if layer_side == 'negative':
                self.GEN.AFFECTED_LAYER(layer_name, affected='yes')
                self.meth.sr_fill_surface(step_margin_x=-0.254,step_margin_y=-0.254,
                                          step_max_dist_x=2540, step_max_dist_y=2540,nest_sr='no')
                self.GEN.AFFECTED_LAYER(layer_name, affected='no')
                self.GEN.AFFECTED_LAYER(source_layer, affected='yes')
                self.GEN.SEL_COPY(layer_name, invert='yes')
                self.GEN.AFFECTED_LAYER(source_layer, affected='no')
            else:
                self.GEN.COPY_LAYER(jobName, 'pnl_m', source_layer, layer_name, invert='no')

        for i in range(len(lam_rout) + 1):
            self.GEN.DELETE_LAYER('ladder_top%s' % i)
            self.GEN.DELETE_LAYER('ladder_bot%s' % i)
            self.GEN.DELETE_LAYER('honeycomb-tok%s' % i)
            self.GEN.DELETE_LAYER('honeycomb-bok%s' % i)
        self.GEN.DELETE_LAYER('assist_copper')
        self.GEN.DELETE_LAYER('eagle-clear-pitch')
        self.GEN.DELETE_LAYER('eagle-cu-pitch')
        self.GEN.DELETE_LAYER('eagle-dot-pitch')
        # fill = CalculateCopperArea()
        # 计算铜面积

        for d in self.fill_array:
            disk = {}
            disk['name'] = str(d['name'])
            disk['pc'] = self.get_copper_area(disk['name'])
            self.pc_areas.append(disk)
            self.GEN.AFFECTED_LAYER(disk['name'], affected='yes')
            self.GEN.CHANGE_UNITS('inch')
            self.GEN.COM("cur_atr_set,attribute=.area_name,text=copper_persen")
            self.GEN.ADD_TEXT(0, -0.02, disk['pc'], 0.05, 0.05, attr='yes')
            self.GEN.FILTER_RESET()
            self.GEN.AFFECTED_LAYER(disk['name'], affected='no')
        self.re_back = True


    def create_PHOTOVOLTAIC_copper(self):
        """
        光电板sr2.5mm范围内铺铜
        :return:
        :rtype:
        """
        sr_xmin = self.parm.sr_xmin
        sr_xmax = self.parm.sr_xmax
        sr_ymin = self.parm.sr_ymin
        sr_ymax = self.parm.sr_ymax
        self.create_tmp_layer('photo_copper')
        self.GEN.CLEAR_LAYER()
        self.GEN.COM("affected_layer,name=photo_copper,mode=single,affected=yes")
        # --定义并添加bot砖块,从左至右
        x1_bot = sr_xmin + 1.6
        x2_bot = x1_bot + 1.25
        y1_bot = sr_ymin - 0.2 - 0.25 - 1.4
        y2_bot = y1_bot + 0.25 * 2 + 0.2
        dy1_bot = 1400
        dy2_bot = 0
        ny1_bot = 2
        ny2_bot = 1
        dx1_bot = 2500
        dx2_bot = 2500
        nx1_bot = (sr_xmax - 1.6 * 2 - sr_xmin) / 2.5
        nx1_bot = math.modf(nx1_bot)[1] + 1
        nx2_bot = (sr_xmax - 1.6 * 2 - sr_xmin - 2.5) / 2.5
        nx2_bot = math.modf(nx2_bot)[1] + 1
        self.GEN.ADD_PAD(x1_bot, y1_bot, 'rect2000x500', nx=nx1_bot, ny=ny1_bot, dx=dx1_bot, dy=dy1_bot)
        self.GEN.ADD_PAD(x2_bot, y2_bot, 'rect2000x500', nx=nx2_bot, ny=ny2_bot, dx=dx2_bot, dy=dy2_bot)

        # --定义并添加top砖块,从右至左
        x1_top = sr_xmax - 1.6
        x2_top = x1_top - 1.25
        y1_top = sr_ymax + 0.2 + 0.25
        y2_top = y1_top + 0.25 * 2 + 0.2
        dy1_top = 1400
        dy2_top = 0
        ny1_top = 2
        ny2_top = 1
        dx1_top = -2500
        dx2_top = -2500
        nx1_top = (sr_xmax - 1.6 * 2 - sr_xmin) / 2.5
        nx1_top = math.modf(nx1_top)[1] + 1
        nx2_top = (sr_xmax - 1.6 * 2 - sr_xmin - 2.5) / 2.5
        nx2_top = math.modf(nx2_top)[1] + 1
        self.GEN.ADD_PAD(x1_top, y1_top, 'rect2000x500', nx=nx1_top, ny=ny1_top, dx=dx1_top, dy=dy1_top)
        self.GEN.ADD_PAD(x2_top, y2_top, 'rect2000x500', nx=nx2_top, ny=ny2_top, dx=dx2_top, dy=dy2_top)

        # --定义并添加right砖块,从下至上
        y1_right = sr_ymin + 1.6
        y2_right = y1_right + 1.25
        x1_right = sr_xmax + 0.2 + 0.25
        x2_right = x1_right + 0.25 * 2 + 0.2
        dx1_right = 1400
        dx2_right = 0
        nx1_right = 2
        nx2_right = 1
        dy1_right = 2500
        dy2_right = 2500
        ny1_right = (sr_ymax - 1.6 * 2 - sr_ymin) / 2.5
        ny1_right = math.modf(ny1_right)[1] + 1
        ny2_right = (sr_ymax - 1.6 * 2 - sr_ymin - 2.5) / 2.5
        ny2_right = math.modf(ny2_right)[1] + 1
        self.GEN.ADD_PAD(x1_right, y1_right, 'rect500x2000', nx=nx1_right, ny=ny1_right, dx=dx1_right, dy=dy1_right)
        self.GEN.ADD_PAD(x2_right, y2_right, 'rect500x2000', nx=nx2_right, ny=ny2_right, dx=dx2_right, dy=dy2_right)

        # --定义并添加left砖块,从上至下
        y1_left = sr_ymax - 1.6
        y2_left = y1_left - 1.25
        x1_left = sr_xmin - 0.2 - 0.25 - 1.4
        x2_left = x1_left + 0.25 * 2 + 0.2
        dx1_left = 1400
        dx2_left = 0
        nx1_left = 2
        nx2_left = 1
        dy1_left = -2500
        dy2_left = -2500
        ny1_left = (sr_ymax - 1.6 * 2 - sr_ymin) / 2.5
        ny1_left = math.modf(ny1_left)[1] + 1
        ny2_left = (sr_ymax - 1.6 * 2 - sr_ymin - 2.5) / 2.5
        ny2_left = math.modf(ny2_left)[1] + 1
        self.GEN.ADD_PAD(x1_left, y1_left, 'rect500x2000', nx=nx1_left, ny=ny1_left, dx=dx1_left, dy=dy1_left)
        self.GEN.ADD_PAD(x2_left, y2_left, 'rect500x2000', nx=nx2_left, ny=ny2_left, dx=dx2_left, dy=dy2_left)
        self.GEN.COM("affected_layer,name=photo_copper,mode=single,affected=no")

    def create_assist_copper(self):
        """
        创建辅助层铺铜
        :return:
        :rtype:
        """
        profile_xmin = self.parm.profile_xmin
        profile_xmax = self.parm.profile_xmax
        profile_ymin = self.parm.profile_ymin
        profile_ymax = self.parm.profile_ymax
        xmin = profile_xmin - 0.254
        ymin = profile_ymin - 0.254
        xmax = profile_xmax + 0.254
        ymax = profile_ymax + 0.254
        self.create_tmp_layer('assist_copper')
        self.GEN.WORK_LAYER('assist_copper')
        self.GEN.COM("units,type=mm")
        self.GEN.COM("add_surf_strt,surf_type=feature")
        self.GEN.COM("add_surf_poly_strt,x=%s,y=%s" % (xmin, ymin))
        self.GEN.COM("add_surf_poly_seg,x=%s,y=%s" % (xmin, ymax))
        self.GEN.COM("add_surf_poly_seg,x=%s,y=%s" % (xmax, ymax))
        self.GEN.COM("add_surf_poly_seg,x=%s,y=%s" % (xmax, ymin))
        self.GEN.COM("add_surf_poly_seg,x=%s,y=%s" % (xmin, ymin))
        self.GEN.COM("add_surf_poly_end")
        self.GEN.COM("add_surf_end,attributes=no,polarity=positive")

    def create_ladder_sym(self):
        """
        创建梯形的板边铺铜symbol
        :return:
        :rtype:
        """
        sr_xmin = self.parm.sr_xmin
        sr_ymin = self.parm.sr_ymin
        sr_xmax = self.parm.sr_xmax
        sr_ymax = self.parm.sr_ymax
        rout_x = self.parm.rout_x
        rout_y = self.parm.rout_y
        profile_xmin = self.parm.profile_xmin
        profile_xmax = self.parm.profile_xmax
        profile_ymin = self.parm.profile_ymin
        profile_ymax = self.parm.profile_ymax
        # job_signal_numbers = self.parm.job_signal_numbers
        lam_rout = self.parm.lam_rout
        lenth = 13
        width = 63
        # --长边clip板内坐标定义
        clip_Iy_xmax = sr_xmin - 2.5
        clip_Iy_xmin = sr_xmax + 2.5
        clip_Iy_ymin = profile_ymin - 5
        clip_Iy_ymax = profile_ymax + 5
        # --短边clip板内坐标定义
        clip_Ix_xmin = sr_xmin - 2.5 - 5
        clip_Ix_xmax = sr_xmax + 2.5 + 5
        clip_Ix_ymin = sr_ymin - 2.5
        clip_Ix_ymax = sr_ymax + 2.5
        # --短边clip板外坐标定义
        clip_Ox_xmin = sr_xmin - 2.5 - 5
        clip_Ox_xmax = sr_xmax + 2.5 + 5

        clip_out_dict = {}
        for lamin_i in lam_rout:
            cur_lamin_num = lamin_i[0]
            cur_lamin_routx = lamin_i[1]
            cur_lamin_routy = lamin_i[2]
            clip_Oy_xmin = profile_xmin + (profile_xmax - cur_lamin_routx) * 0.5 + 2
            clip_Oy_xmax = profile_xmax - (profile_xmax - cur_lamin_routx) * 0.5 - 2
            clip_Oy_ymin = profile_ymin + (profile_ymax - cur_lamin_routy) * 0.5 + 2
            clip_Oy_ymax = profile_ymax - (profile_ymax - cur_lamin_routy) * 0.5 - 2
            clip_Ox_ymin = profile_ymin + (profile_ymax - cur_lamin_routy) * 0.5 + 2
            clip_Ox_ymax = profile_ymax - (profile_ymax - cur_lamin_routy) * 0.5 - 2
            clip_out_dict[cur_lamin_num] = {
                'clip_Oy_xmin': clip_Oy_xmin,
                'clip_Oy_xmax': clip_Oy_xmax,
                'clip_Oy_ymin': clip_Oy_ymin,
                'clip_Oy_ymax': clip_Oy_ymax,
                'clip_Ox_xmin': clip_Ox_xmin,
                'clip_Ox_xmax': clip_Ox_xmax,
                'clip_Ox_ymin': clip_Ox_ymin,
                'clip_Ox_ymax': clip_Ox_ymax,
            }
        # === 增加0压数据 ===
        clip_out_dict[0] = {
            'clip_Oy_xmin': profile_xmin + 2,
            'clip_Oy_xmax': profile_xmax - 2,
            'clip_Oy_ymin': profile_ymin + 2,
            'clip_Oy_ymax': profile_ymax - 2,
            'clip_Ox_xmin': clip_Ox_xmin,
            'clip_Ox_xmax': clip_Ox_xmax,
            'clip_Ox_ymin': profile_ymin + 2,
            'clip_Ox_ymax': profile_ymax - 2
        }
        # # --长边clip板外坐标定义
        # clip_Oy_xmin = profile_xmin - 5
        # clip_Oy_xmax = profile_xmax + 5
        # clip_Oy_ymin = profile_ymin - 5
        # clip_Oy_ymax = profile_ymax + 5
        #
        #
        # clip_Ox_ymin = profile_ymin - 5
        # clip_Ox_ymax = profile_ymax + 5
        # --20210118新规则,所有板层同六层板
        # --20210209内层铺铜，四层板仍然要求距锣边1mm
        # if job_signal_numbers == 4:
        #     # --四层板距锣边(profile)1mm
        #     clip_Oy_xmin = profile_xmin + (profile_xmax - rout_x)*0.5 + 1
        #     clip_Oy_xmax = profile_xmax - (profile_xmax - rout_x)*0.5 - 1
        #     clip_Oy_ymin = profile_ymin + (profile_ymax - rout_y)*0.5 + 1
        #     clip_Oy_ymax = profile_ymax - (profile_ymax - rout_y)*0.5 - 1
        #     clip_Ox_ymin = profile_ymin + (profile_ymax - rout_y)*0.5 + 1
        #     clip_Ox_ymax = profile_ymax - (profile_ymax - rout_y)*0.5 - 1
        # --计算长边偏移值
        long_offset_top = 0
        # --注意bot只是在top面的基础上再偏移1.5(默认,后面会调整)
        long_offset_bot = 3
        long_side_top = sr_xmin - 2.5 - clip_Oy_xmin
        long_side_bot = sr_xmin - 2.5 - clip_Oy_xmin + long_offset_bot
        long_model_top = long_side_top % 6.5
        long_model_bot = long_side_bot % 6.5
        long_model_top = float('%.3f' % long_model_top)
        long_model_bot = float('%.3f' % long_model_bot)
        # --最内侧铜皮保留(封口)宽度
        long_revise_top = 5
        long_revise_bot = 5 - long_offset_bot

        # --计算短边偏移值
        short_offset_top = 3
        short_offset_bot = 0
        short_side_bot = sr_ymin - 2.5 - clip_Ox_ymin
        short_side_top = sr_ymin - 2.5 - clip_Ox_ymin + short_offset_top
        short_model_bot = short_side_bot % 6.5
        short_model_top = short_side_top % 6.5
        short_model_top = float('%.3f' % short_model_top)
        short_model_bot = float('%.3f' % short_model_bot)
        short_revise_bot = 5
        short_revise_top = 5 - short_offset_top

        # --长边添加pad的x坐标,5.75为fill_ladder_top中心到边缘的距离,以top面为基准
        x1_top = sr_xmin - 5.75 - 2.5 + long_offset_top
        x2_top = sr_xmax + 5.75 + 2.5 - long_offset_top
        x1_bot = sr_xmin - 5.75 - 2.5 + long_offset_bot
        x2_bot = sr_xmax + 5.75 + 2.5 - long_offset_bot
        # --短边添加pad的y坐标,以bot面为基准
        y1_bot = sr_ymin - 5.75 - 2.5 + short_offset_bot
        y2_bot = sr_ymax + 5.75 + 2.5 - short_offset_bot
        y1_top = sr_ymin - 5.75 - 2.5 + short_offset_top
        y2_top = sr_ymax + 5.75 + 2.5 - short_offset_top
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        for side in ('top', 'bot'):
            if side == 'top':
                layer_y = 'ladder_y_top'
                layer_x = 'ladder_x_top'
                # === TODO 此处应为列表 ===
                layer = 'ladder_top'
                sym = 'fill_ladder_top'
                x1 = x1_top
                x2 = x2_top
                # --设置clip参数使长短边交汇处平齐
                clip_Ox_xmin = sr_xmin - 2.5 - long_revise_top
                clip_Ox_xmax = sr_xmax + 2.5 + long_revise_top
                # --top面短边靠近板内做3.5mm
                y1 = y1_top
                y2 = y2_top
            else:
                layer_y = 'ladder_y_bot'
                layer_x = 'ladder_x_bot'
                layer = 'ladder_bot'
                sym = 'fill_ladder_bot'
                # --bot面长边靠近板内做3.5mm
                x1 = x1_bot
                x2 = x2_bot
                y1 = y1_bot
                y2 = y2_bot
                # --设置clip参数使长短边交汇处平齐
                clip_Ox_xmin = sr_xmin - 2.5 - long_revise_bot
                clip_Ox_xmax = sr_xmax + 2.5 + long_revise_bot
            self.create_tmp_layer(layer_y)
            self.create_tmp_layer(layer_x)
            for cur_lamin_num in clip_out_dict.keys():
                self.create_tmp_layer('%s%s' % (layer, cur_lamin_num))
            self.GEN.WORK_LAYER(layer_y)
            self.GEN.SEL_DELETE()
            # --定义长边添加symbol的参数
            nx = int(long_side_top / lenth) + 2
            ny = int((profile_ymax - profile_ymin) / width) + 2
            y = (profile_ymax - profile_ymin) / 2 - (ny - 1) * width / 2
            dx = lenth * 1000
            dy = width * 1000
            self.GEN.ADD_PAD(x1, y, sym, nx=nx, ny=ny, dx=-dx, dy=dy)
            self.GEN.ADD_PAD(x2, y, sym, nx=nx, ny=ny, dx=dx, dy=dy)
            # print "long_model_top",long_model_top
            # print "long_model_bot",long_model_bot
            # self.GEN.PAUSE("add long pad")
            # --长边板内clip
            self.GEN.COM("clip_area_strt")
            self.GEN.COM("clip_area_xy,x=%s,y=%s" % (clip_Iy_xmin, clip_Iy_ymin))
            self.GEN.COM("clip_area_xy,x=%s,y=%s" % (clip_Iy_xmax, clip_Iy_ymax))
            self.GEN.COM(
                "clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=inside,"
                "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
            # self.GEN.PAUSE("clip pad long inner")
            # --长边板外clip
            for cur_lamin_num in range(0, len(lam_rout)):
                # for item in lam_rout:
                #     if item[0] ==  cur_lamin_num:
                self.GEN.COM("clip_area_strt")
                # self.GEN.COM("clip_area_xy,x=%s,y=%s" % (clip_Oy_xmin, clip_Oy_ymin))
                # self.GEN.COM("clip_area_xy,x=%s,y=%s" % (clip_Oy_xmax, clip_Oy_ymax))
                self.GEN.COM("clip_area_xy,x=%s,y=%s" % (
                    clip_out_dict[cur_lamin_num]['clip_Oy_xmin'], clip_out_dict[cur_lamin_num]['clip_Oy_ymin']))
                self.GEN.COM("clip_area_xy,x=%s,y=%s" % (
                    clip_out_dict[cur_lamin_num]['clip_Oy_xmax'], clip_out_dict[cur_lamin_num]['clip_Oy_ymax']))

                self.GEN.COM(
                    "clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,"
                    "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
                # self.GEN.PAUSE("clip pad long outer")
                self.GEN.SEL_COPY("%s%s" % (layer, cur_lamin_num))
            # --定义短边添加symbol的参数
            ny = int(short_side_bot / lenth) + 2
            nx = int((profile_xmax - profile_xmin) / width) + 2
            dy = lenth * 1000
            dx = width * 1000
            x = (profile_xmax - profile_xmin) / 2 - (nx - 1) * width / 2
            self.GEN.WORK_LAYER(layer_x)
            self.GEN.SEL_DELETE()
            self.GEN.ADD_PAD(x, y1, sym, nx=nx, ny=ny, dx=dx, dy=-dy, angle=90)
            self.GEN.ADD_PAD(x, y2, sym, nx=nx, ny=ny, dx=dx, dy=dy, angle=90)
            # print "short_model_bot",short_model_bot
            # print "short_model_top",short_model_top
            # self.GEN.PAUSE("add short pad")
            # --短边板内clip
            self.GEN.COM("clip_area_strt")
            self.GEN.COM("clip_area_xy,x=%s,y=%s" % (clip_Ix_xmin, clip_Ix_ymin))
            self.GEN.COM("clip_area_xy,x=%s,y=%s" % (clip_Ix_xmax, clip_Ix_ymax))
            self.GEN.COM(
                "clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=inside,"
                "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
            # self.GEN.PAUSE("clip pad short inner")
            # --短边板外clip
            for cur_lamin_num in range(0, len(lam_rout)):
                # for item in lam_rout:
                #     if item[0] ==  cur_lamin_num:
                self.GEN.COM("clip_area_strt")
                # self.GEN.COM("clip_area_xy,x=%s,y=%s" % (clip_Oy_xmin, clip_Oy_ymin))
                # self.GEN.COM("clip_area_xy,x=%s,y=%s" % (clip_Oy_xmax, clip_Oy_ymax))
                self.GEN.COM("clip_area_xy,x=%s,y=%s" % (
                    clip_out_dict[cur_lamin_num]['clip_Ox_xmin'], clip_out_dict[cur_lamin_num]['clip_Ox_ymin']))
                self.GEN.COM("clip_area_xy,x=%s,y=%s" % (
                    clip_out_dict[cur_lamin_num]['clip_Ox_xmax'], clip_out_dict[cur_lamin_num]['clip_Ox_ymax']))

                self.GEN.COM(
                    "clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,"
                    "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
                # self.GEN.PAUSE("clip pad long outer")
                self.GEN.SEL_COPY("%s%s" % (layer, cur_lamin_num))

            # --删除临时层别
            self.GEN.DELETE_LAYER(layer_x)
            self.GEN.DELETE_LAYER(layer_y)
        # self.GEN.PAUSE("check")
        # --通过两次resize,去掉尖角和小于5mil的surface
        for cur_lamin_num in range(0, len(lam_rout)):
            top_layer = 'ladder_top%s' % (cur_lamin_num)
            bot_layer = 'ladder_bot%s' % (cur_lamin_num)
            self.remove_small_surface(size=1000, target_top=top_layer, target_bot=bot_layer)
            # --将梯形铺铜整体化成一整块surface,方便框选其它symbol
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER(top_layer, 'yes')
            self.GEN.AFFECTED_LAYER(bot_layer, 'yes')
            self.GEN.COM('sel_contourize, accuracy=6.35, break_to_islands=no, clean_hole_size=76.2')
            self.GEN.CLEAR_LAYER()
            # --品字形排版sr范围内铺蜂窝铜
            self.copy_sr_honeycomb(target_top=top_layer, target_bot=bot_layer)
            # --排版间距里铺铜条
            for direct in ('horizontal', 'vertical'):
                self.fill_pitch(direct, target_top=top_layer, target_bot=bot_layer)
            # --四角铺铜皮,940,968转角不铺铜皮 === HDI无此要求 ===
            # if self.cusNo not in ('940', '968'):
            self.corner_copper(copper_dis=60, target_top=top_layer, target_bot=bot_layer, cur_lamin_num=cur_lamin_num)
            # --绕内profile一圈添加金线,光电板不需要
            # if not self.parm.is_PHOTOVOLTAIC_board:
            self.add_gold_line(target_top=top_layer, target_bot=bot_layer)
            # --增加属性,方便后续作业
            self.add_attribute(layer=top_layer, attribute='.bit,text=pnl_ladder_cu')
            self.add_attribute(layer=bot_layer, attribute='.bit,text=pnl_ladder_cu')
            self.add_attribute(layer=top_layer, attribute='.string,text=ladder_top')
            self.add_attribute(layer=bot_layer, attribute='.string,text=ladder_bot')
        self.GEN.CLEAR_LAYER()

    def create_honeycomb_sym(self):
        """
        创建蜂窝形状的板边铺铜symbol
        :return:
        :rtype:
        """
        # job_signal_numbers = self.parm.job_signal_numbers
        sr_xmin = self.parm.sr_xmin
        sr_ymin = self.parm.sr_ymin
        sr_xmax = self.parm.sr_xmax
        sr_ymax = self.parm.sr_ymax
        profile_xmin = self.parm.profile_xmin
        profile_xmax = self.parm.profile_xmax
        profile_ymin = self.parm.profile_ymin
        profile_ymax = self.parm.profile_ymax
        # rout_x = self.parm.rout_x
        # rout_y = self.parm.rout_y
        # top_after_margin = self.parm.top_after_margin
        # left_after_margin = self.parm.left_after_margin

        lam_rout = self.parm.lam_rout

        # --将蜂窝临时层的内容物copy到正式层然后clip
        self.GEN.CLEAR_LAYER()
        self.create_tmp_layer('honeycomb-tok')
        self.create_tmp_layer('honeycomb-bok')
        for cur_lamin_num in range(len(lam_rout) + 1):
            self.create_tmp_layer('honeycomb-tok%s' % cur_lamin_num)
            self.create_tmp_layer('honeycomb-bok%s' % cur_lamin_num)
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-t,mode=single,affected=yes")
        # --top临时层copy到top_ok
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-tok,invert=no,dx=0,dy=0,"
                     "size=0,x_anchor=0,y_anchor=0,rotation=0,mirror=none")
        # --bot临时层copy到bot_ok
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-b,mode=single,affected=yes")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-bok,invert=no,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")
        # --切铜参数定义

        # === 使用距离板内2.5mm的铺铜距离，不区分几层板
        cut_copper_x1 = sr_xmin - 2.5
        cut_copper_y1 = sr_ymin - 2.5
        cut_copper_x2 = sr_xmax + 2.5
        cut_copper_y2 = sr_ymax + 2.5

        clip_out_dict = {}
        for cur_lamin_num in range(len(lam_rout) + 1):
            if cur_lamin_num == 0:
                clip_out_dict[0] = dict(
                    cut_copper_x3=profile_xmin + 2,
                    cut_copper_y3=profile_ymin + 2,
                    cut_copper_x4=profile_xmax - 2,
                    cut_copper_y4=profile_ymax - 2
                )
            else:
                cur_lamin_routx = lam_rout[cur_lamin_num - 1][1]
                cur_lamin_routy = lam_rout[cur_lamin_num - 1][2]
                clip_out_dict[cur_lamin_num] = dict(
                    cut_copper_x3=profile_xmin + (profile_xmax - cur_lamin_routx) * 0.5 + 2,
                    cut_copper_y3=profile_ymin + (profile_ymax - cur_lamin_routy) * 0.5 + 2,
                    cut_copper_x4=profile_xmax - (profile_xmax - cur_lamin_routx) * 0.5 - 2,
                    cut_copper_y4=profile_ymax - (profile_ymax - cur_lamin_routy) * 0.5 - 2)

        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tok,mode=single,affected=yes")
        self.GEN.COM("affected_layer,name=honeycomb-bok,mode=single,affected=yes")
        # --伸到板内部分进行clip
        self.GEN.COM("clip_area_strt")
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_copper_x1, cut_copper_y1))
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_copper_x2, cut_copper_y2))
        self.GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=inside,"
                     "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")

        cut_copper_x3 = clip_out_dict[0]['cut_copper_x3']
        cut_copper_y3 = clip_out_dict[0]['cut_copper_y3']
        cut_copper_x4 = clip_out_dict[0]['cut_copper_x4']
        cut_copper_y4 = clip_out_dict[0]['cut_copper_y4']

        # --伸出板外部分进行clip
        self.GEN.COM("clip_area_strt")
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_copper_x3, cut_copper_y3))
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_copper_x4, cut_copper_y4))
        self.GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,"
                     "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")

        # --品字形sr范围内铺蜂窝铜
        self.copy_sr_honeycomb(target_top='honeycomb-tok', target_bot='honeycomb-bok')
        # --排版间距里铺铜条
        for direct in ('horizontal', 'vertical'):
            self.fill_pitch(direct, target_top='honeycomb-tok', target_bot='honeycomb-bok')
        # --通过两次resize,去掉尖角和小于5mil的surface
        self.remove_small_surface(target_top='honeycomb-tok', target_bot='honeycomb-bok')
        # --四角铺铜皮
        self.corner_copper(target_top='honeycomb-tok', target_bot='honeycomb-bok')
        # --绕内profile一圈添加金线
        self.add_gold_line(target_top='honeycomb-tok', target_bot='honeycomb-bok')

        for cur_lamin_num in range(len(lam_rout) + 1):
            cut_copper_x3 = clip_out_dict[cur_lamin_num]['cut_copper_x3']
            cut_copper_y3 = clip_out_dict[cur_lamin_num]['cut_copper_y3']
            cut_copper_x4 = clip_out_dict[cur_lamin_num]['cut_copper_x4']
            cut_copper_y4 = clip_out_dict[cur_lamin_num]['cut_copper_y4']
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER('honeycomb-tok', 'yes')
            self.GEN.AFFECTED_LAYER('honeycomb-bok', 'yes')

            # --伸出板外部分进行clip 放在此位置，避免多次运行
            self.GEN.COM("clip_area_strt")
            self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_copper_x3, cut_copper_y3))
            self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_copper_x4, cut_copper_y4))
            self.GEN.COM(
                "clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,"
                "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER('honeycomb-tok', 'yes')
            self.GEN.SEL_COPY('honeycomb-tok%s' % cur_lamin_num)
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER('honeycomb-bok', 'yes')
            self.GEN.SEL_COPY('honeycomb-bok%s' % cur_lamin_num)
            self.GEN.CLEAR_LAYER()

            self.add_attribute(layer='honeycomb-tok%s' % cur_lamin_num, attribute='surface,text=copper')
            self.add_attribute(layer='honeycomb-bok%s' % cur_lamin_num, attribute='surface,text=copper')
            self.add_attribute(layer='honeycomb-tok%s' % cur_lamin_num, attribute='.string,text=ladder_top')
            self.add_attribute(layer='honeycomb-bok%s' % cur_lamin_num, attribute='.string,text=ladder_bot')
        self.GEN.CLEAR_LAYER()

        # --创建symbol,由于创建symbol会导致在panel查看时移动较卡，所以取消
        # self.GEN.COM("clear_layers")
        # self.GEN.COM("affected_layer,mode=all,affected=no")
        # self.GEN.COM("affected_layer,name=honeycomb-tok,mode=single,affected=yes")
        # self.GEN.COM("sel_create_sym,symbol=panel_symbol_top,x_datum=0,y_datum=0,delete=no,fill_dx=2.54,fill_dy=2.54,"
        #              "attach_atr=no,retain_atr=no")
        #
        # self.GEN.COM("clear_layers")
        # self.GEN.COM("affected_layer,mode=all,affected=no")
        # self.GEN.COM("affected_layer,name=honeycomb-bok,mode=single,affected=yes")
        # self.GEN.COM("sel_create_sym,symbol=panel_symbol_bot,x_datum=0,y_datum=0,delete=no,fill_dx=2.54,fill_dy=2.54,"
        #              "attach_atr=no,retain_atr=no")

    def add_attribute(self, layer=None, attribute=None):
        """
        将铺铜的surface加上属性
        :return:
        :rtype:
        """
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER(layer, 'yes')
        self.GEN.COM('cur_atr_reset')
        self.GEN.COM('cur_atr_set,attribute=%s' % attribute)
        self.GEN.COM('sel_change_atr,mode=add')
        self.GEN.COM('cur_atr_reset')
        self.GEN.AFFECTED_LAYER(layer, 'no')

    def create_honeycomb_tmp(self):
        """
        创建蜂窝临时层别
        :return:
        :rtype:
        """
        self.GEN.OPEN_STEP(self.STEP)
        self.GEN.CLEAR_LAYER()
        self.create_tmp_layer('honeycomb-t')
        self.create_tmp_layer('honeycomb-b')
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        # --top面与bot面用同样的参数fill
        self.GEN.COM("affected_layer,name=honeycomb-t,mode=single,affected=yes")
        self.GEN.COM("affected_layer,name=honeycomb-b,mode=single,affected=yes")
        self.GEN.COM("fill_params,type=pattern,origin_type=datum,solid_type=surface,std_type=line,min_brush=25.4,"
                     "use_arcs=yes,symbol=2oz_fw,dx=9.72312,dy=5.588,std_angle=45,std_line_width=254,"
                     "std_step_dist=1270,std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,"
                     "outline_width=0,outline_invert=no")
        # --超出内profile10mm,超出profile也是10mm
        self.GEN.COM("sr_fill,polarity=positive,step_margin_x=-10,step_margin_y=-10,step_max_dist_x=2540,"
                     "step_max_dist_y=2540,sr_margin_x=-10,sr_margin_y=-10,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,"
                     "consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no")
        # --top面与bot面错位3.14mm
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-t,mode=single,affected=yes")
        self.GEN.COM("sel_move,dx=3.14,dy=0")

    def get_sr_honeycomb(self):
        """
        sr范围内铺蜂窝铜,品字形拼板才会有
        :return:
        :rtype:
        """
        sr_xmin = self.parm.sr_xmin
        sr_ymin = self.parm.sr_ymin
        sr_xmax = self.parm.sr_xmax
        sr_ymax = self.parm.sr_ymax
        # --删除并重新创建临时层别
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.create_tmp_layer('honeycomb-tmp1')
        self.create_tmp_layer('honeycomb-tmp2')
        # --用solid fill tmp1,距内profile 2.5mm,外面超出profile 5mm,以下步骤对品字形排版有用
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tmp1,mode=single,affected=yes")
        self.GEN.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=25.4,"
                     "use_arcs=yes,symbol=2oz_fw,dx=9.72312,dy=5.588,std_angle=45,std_line_width=254,std_step_dist=1270,"
                     "std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,outline_width=0,outline_invert=no")
        self.GEN.COM("sr_fill,polarity=positive,step_margin_x=-5,step_margin_y=-5,step_max_dist_x=2540,"
                     "step_max_dist_y=2540,sr_margin_x=2.5,sr_margin_y=2.5,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,"
                     "consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no")
        # --用solid fill tmp2,铺进板内1000mm,以下步骤对品字形排版有用
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tmp2,mode=single,affected=yes")
        self.GEN.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=25.4,"
                     "use_arcs=yes,symbol=2oz_fw,dx=9.72312,dy=5.588,std_angle=45,std_line_width=254,std_step_dist=1270,"
                     "std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,outline_width=0,outline_invert=no")
        self.GEN.COM("sr_fill,polarity=positive,step_margin_x=-5,step_margin_y=-5,step_max_dist_x=2540,"
                     "step_max_dist_y=2540,sr_margin_x=-1000,sr_margin_y=-1000,sr_max_dist_x=0,sr_max_dist_y=0,"
                     "nest_sr=no,consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no")
        # --tmp1 copy到tmp2,两者合并得到超出内profile 2.5mm的铺满整个内容物的铜皮
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tmp1,mode=single,affected=yes")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-tmp2,invert=yes,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")

        # --对honeycomb-t和honeycomb-b进行clip,保留sr范围内的部分
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-t,mode=single,affected=yes")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-tsr,invert=no,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")

        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-b,mode=single,affected=yes")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-bsr,invert=no,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")

        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tsr,mode=single,affected=yes")
        self.GEN.COM("affected_layer,name=honeycomb-bsr,mode=single,affected=yes")

        # cut_copper_x5 = sr_xmin + 1
        # cut_copper_y5 = sr_ymin + 1
        # cut_copper_x6 = sr_xmax - 1
        # cut_copper_y6 = sr_ymax - 1
        cut_copper_x5 = sr_xmin - 2
        cut_copper_y5 = sr_ymin - 2
        cut_copper_x6 = sr_xmax + 2
        cut_copper_y6 = sr_ymax + 2

        self.GEN.COM("clip_area_strt")
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_copper_x5, cut_copper_y5))
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_copper_x6, cut_copper_y6))
        self.GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,"
                     "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")

        # === v2.12 铺铜距离加大后，限位孔角线被覆盖，切掉多余铜 ===
        # === 1.左下
        self.GEN.COM('clip_area_strt')
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin - 2.5),(sr_ymin - 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin + 2.5),(sr_ymin - 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin + 2.5),(sr_ymin)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin),(sr_ymin)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin),(sr_ymin + 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin - 2.5),(sr_ymin + 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin - 2.5),(sr_ymin - 2.5)))
        self.GEN.COM('clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=polygon,inout=inside,contour_cut=no,margin=0,feat_types=surface')
        # === 2.右下
        self.GEN.COM('clip_area_strt')
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax + 2.5),(sr_ymin - 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax - 2.5),(sr_ymin - 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax - 2.5),(sr_ymin)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax),(sr_ymin)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax),(sr_ymin + 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax + 2.5),(sr_ymin + 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax + 2.5),(sr_ymin - 2.5)))
        self.GEN.COM('clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=polygon,inout=inside,contour_cut=no,margin=0,feat_types=surface')
        # === 3.右上
        self.GEN.COM('clip_area_strt')
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax + 2.5),(sr_ymax + 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax - 2.5),(sr_ymax + 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax - 2.5),(sr_ymax)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax),(sr_ymax)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax),(sr_ymax - 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax + 2.5),(sr_ymax - 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax + 2.5),(sr_ymax + 2.5)))
        self.GEN.COM('clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=polygon,inout=inside,contour_cut=no,margin=0,feat_types=surface')
        # === 4.左上
        self.GEN.COM('clip_area_strt')
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin - 2.5),(sr_ymax + 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin + 2.5),(sr_ymax + 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin + 2.5),(sr_ymax)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin),(sr_ymax)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin),(sr_ymax - 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin - 2.5),(sr_ymax - 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin - 2.5),(sr_ymax + 2.5)))
        self.GEN.COM('clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=polygon,inout=inside,contour_cut=no,margin=0,feat_types=surface')


        # --tmp2整体化后copy到honeycomb-tsr和honeycomb-bsr
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tmp2,mode=single,affected=yes")
        self.GEN.COM("sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-tsr,invert=yes,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-bsr,invert=yes,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")
        # --honeycomb-tsr和honeycomb-bsr进行整体化,这几步对品字形排版有用,对正正排版是在做无用功，copy空气到tok和bok
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tsr,mode=single,affected=yes")
        self.GEN.COM("affected_layer,name=honeycomb-bsr,mode=single,affected=yes")
        # self.GEN.COM("sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
        # --整体化成一整块
        self.GEN.COM("sel_contourize,accuracy=50.8,break_to_islands=no,clean_hole_size=76.2,clean_hole_mode=x_and_y")
        self.GEN.CLEAR_LAYER()

    def copy_sr_honeycomb(self, target_top=None, target_bot=None):
        """
        品字形,sr范围内的蜂窝铜copy到相应层别
        :param target_top: 内层top面
        :param target_bot: 内层bot面
        :return:
        """
        # --分别copy到honeycomb-tok和honeycomb-bok
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tsr,mode=single,affected=yes")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_top)

        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-bsr,mode=single,affected=yes")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_bot)

    def remove_small_surface(self, size=431, target_top='honeycomb-tok', target_bot='honeycomb-bok'):
        """
        通过两次resize,去掉尖角和小于5mil的surface
        :return:
        :rtype:
        """
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=%s,mode=single,affected=yes" % target_top)
        self.GEN.COM("affected_layer,name=%s,mode=single,affected=yes" % target_bot)
        if size == 1000:
            if platform.system() == "Windows":
                # windows环境下,梯形symbol的尖角在resize时没有圆角处理，导致output时报SIP错误
                # 李家兴2019.11.08依据story-view-156修改
                self.GEN.COM('sel_resize,size=-1000,corner_ctl=yes')
                self.GEN.COM('sel_resize,size=1000,corner_ctl=yes')
                self.GEN.COM('fill_params,type=solid,origin_type=datum,solid_type=fill,std_type=line,min_brush=999,'
                             'use_arcs=yes,symbol=,dx=2.54,dy=2.54,std_angle=45,std_line_width=254,std_step_dist=1270,'
                             'std_indent=odd,break_partial=yes,cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no')
                self.GEN.COM('sel_fill')
                self.GEN.FILL_SUR_PARAMS()
                self.GEN.COM('sel_contourize, accuracy=6.35, break_to_islands=no, clean_hole_size=76.2')
            else:
                self.GEN.SEL_RESIZE(-1000)
                self.GEN.SEL_RESIZE(1000)
        else:
            self.GEN.COM("sel_resize,size=-%s,corner_ctl=no" % size)
            self.GEN.COM("sel_resize,size=%s,corner_ctl=no" % size)
            self.GEN.COM('sel_contourize, accuracy=6.35, break_to_islands=no, clean_hole_size=76.2')

    def corner_copper(self, copper_dis=None, target_top='honeycomb-tok', target_bot='honeycomb-bok',
                      cur_lamin_num=None):
        """
        四角铺铜皮
        :return:
        :rtype:
        """
        job_signal_numbers = len(pb.inner) + 2
        sr_xmin = self.parm.sr_xmin
        sr_ymin = self.parm.sr_ymin
        sr_xmax = self.parm.sr_xmax
        sr_ymax = self.parm.sr_ymax
        profile_xmin = self.parm.profile_xmin
        profile_ymin = self.parm.profile_ymin
        profile_xmax = self.parm.profile_xmax
        profile_ymax = self.parm.profile_ymax
        rout_x = self.parm.rout_x
        rout_y = self.parm.rout_y
        top_after_margin = self.parm.top_after_margin
        left_after_margin = self.parm.left_after_margin
        lam_rout = self.parm.lam_rout
        # --切铜参数定义
        # --20210118新规则,所有板层同六层板
        # --20210209内层铺铜，四层板仍然要求距锣边1mm
        if job_signal_numbers == 4:
            if left_after_margin >= 7:
                cut_corner_x1 = sr_xmin - 2.5
                cut_corner_x2 = sr_xmax + 2.5
            else:
                cut_corner_x1 = sr_xmin - 1.5
                cut_corner_x2 = sr_xmax + 1.5
            if top_after_margin >= 7:
                cut_corner_y2 = sr_ymax + 2.5
                cut_corner_y1 = sr_ymin - 2.5
            else:
                cut_corner_y2 = sr_ymax + 1.5
                cut_corner_y1 = sr_ymin - 1.5
        else:
            cut_corner_x1 = sr_xmin - 2.5
            cut_corner_y1 = sr_ymin - 2.5
            cut_corner_x2 = sr_xmax + 2.5
            cut_corner_y2 = sr_ymax + 2.5
        # cut_corner_x1 = sr_xmin - 2.5
        # cut_corner_y1 = sr_ymin - 2.5
        # cut_corner_x2 = sr_xmax + 2.5
        # cut_corner_y2 = sr_ymax + 2.5
        # --四角铺铜皮
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.create_tmp_layer('honeycomb-tmp2')
        self.GEN.COM("affected_layer,name=honeycomb-tmp2,mode=single,affected=yes")
        self.GEN.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=25.4,"
                     "use_arcs=yes,symbol=,dx=2.54,dy=2.54,std_angle=45,std_line_width=254,std_step_dist=1270,"
                     "std_indent=odd,break_partial=yes,cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no")
        # --20210118新规则,所有板层同六层板
        # --20210209内层铺铜，四层板仍然要求距锣边1mm
        if cur_lamin_num:
            for item in lam_rout:
                if item[0] == cur_lamin_num:
                    cur_routx = item[1]
                    cur_routy = item[2]
                    # --四层板距profile(锣边)1mm === HDI距每次锣边 2mm
                    step_margin_x = (profile_xmax - cur_routx) * 0.5 + 2
                    step_margin_y = (profile_ymax - cur_routy) * 0.5 + 2
                    self.GEN.COM("sr_fill,polarity=positive,step_margin_x=%s,step_margin_y=%s,step_max_dist_x=2540,"
                                 "step_max_dist_y=2540,sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,"
                                 "consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no"
                                 % (step_margin_x, step_margin_y))

        else:
            # step_margin_x = '-5'
            # step_margin_y = '-5'
            step_margin_x = 2
            step_margin_y = 2
            self.GEN.COM("sr_fill,polarity=positive,step_margin_x=%s,step_margin_y=%s,step_max_dist_x=2540,"
                         "step_max_dist_y=2540,sr_margin_x=2.5,sr_margin_y=2.5,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,"
                         "consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no"
                         % (step_margin_x, step_margin_y))
        # self.GEN.COM("sr_fill,polarity=positive,step_margin_x=-5,step_margin_y=-5,step_max_dist_x=2540,"
        #              "step_max_dist_y=2540,sr_margin_x=2.5,sr_margin_y=2.5,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,"
        #              "consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no")
        self.GEN.COM("clip_area_strt")
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_corner_x1, cut_corner_y1))
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_corner_x2, cut_corner_y2))
        self.GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,"
                     "inout=inside,contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
        # --判断sr距profile够不够55mm.
        enough_dis_y = sr_ymin - profile_ymin
        enough_dis_x = sr_xmin - profile_xmin
        if enough_dis_y <= 55:
            cut_corner_y1 = profile_ymin + 60
            cut_corner_y2 = profile_ymax - 60
            if copper_dis:
                # --梯形板边封角为60mm
                cut_corner_y1 = profile_ymin + copper_dis
                cut_corner_y2 = profile_ymax - copper_dis
        else:
            enough_dis_y = enough_dis_y + 5
            cut_corner_y1 = profile_ymin + enough_dis_y
            cut_corner_y2 = profile_ymax - enough_dis_y
        cut_corner_x1 = profile_xmin - 6
        cut_corner_x2 = profile_xmax + 6
        self.GEN.COM("clip_area_strt")
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_corner_x1, cut_corner_y1))
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_corner_x2, cut_corner_y2))
        self.GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=inside,"
                     "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
        if enough_dis_x <= 55:
            cut_corner_x1 = profile_xmin + 60
            cut_corner_x2 = profile_xmax - 60
        else:
            enough_dis_x = enough_dis_x + 5
            cut_corner_x1 = profile_xmin + enough_dis_x
            cut_corner_x2 = profile_xmax - enough_dis_x
        cut_corner_y1 = profile_ymin - 6
        cut_corner_y2 = profile_ymax + 6
        self.GEN.COM("clip_area_strt")
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_corner_x1, cut_corner_y1))
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_corner_x2, cut_corner_y2))
        self.GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=inside,"
                     "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_top)
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_bot)

    def add_gold_line(self, target_top=None, target_bot=None):
        """
        绕内profile一圈添加金线
        :return:
        :rtype:
        """
        job_signal_numbers = len(pb.inner) + 2
        sr_xmin = self.parm.sr_xmin
        sr_ymin = self.parm.sr_ymin
        sr_xmax = self.parm.sr_xmax
        sr_ymax = self.parm.sr_ymax
        profile_xmin = self.parm.profile_xmin
        profile_ymin = self.parm.profile_ymin
        profile_xmax = self.parm.profile_xmax
        profile_ymax = self.parm.profile_ymax
        pn_eight = self.JOB[7]
        if pn_eight in ['y', 'r', 'l']:
            if job_signal_numbers >= 4:
                line_x1 = sr_xmin - 1.25
                line_x2 = sr_xmin + 15
                line_x3 = sr_xmax - 15
                line_x4 = sr_xmax + 1.25
                line_y1 = sr_ymin - 1.25
                line_y2 = sr_ymin + 15
                line_y3 = sr_ymax - 15
                line_y4 = sr_ymax + 1.25
                self.GEN.COM("clear_layers")
                self.GEN.COM("affected_layer,mode=all,affected=no")
                self.create_tmp_layer('honeycomb-tmp2')
                self.GEN.COM("affected_layer,name=honeycomb-tmp2,mode=single,affected=yes")
                self.GEN.COM(
                    "add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=s1500,polarity=positive,bus_num_lines=0,"
                    "bus_dist_by=pitch,bus_distance=0,bus_reference=left" % (line_x1, line_y2, line_x1, line_y3))
                self.GEN.COM(
                    "add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=s1500,polarity=positive,bus_num_lines=0,"
                    "bus_dist_by=pitch,bus_distance=0,bus_reference=left" % (line_x4, line_y2, line_x4, line_y3))
                self.GEN.COM(
                    "add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=s1500,polarity=positive,bus_num_lines=0,"
                    "bus_dist_by=pitch,bus_distance=0,bus_reference=left" % (line_x2, line_y1, line_x3, line_y1))
                self.GEN.COM(
                    "add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=s1500,polarity=positive,bus_num_lines=0,"
                    "bus_dist_by=pitch,bus_distance=0,bus_reference=left" % (line_x2, line_y4, line_x3, line_y4))
                loop_num_y = int((sr_ymax - sr_ymin - 30) / 22)
                loop_num_x = int((sr_xmax - sr_xmin - 30) / 22)
                # --线水平方向
                for i in range(1, loop_num_y + 1):
                    s_pad_y = sr_ymin + 22 * i
                    self.GEN.COM("add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=s3000,polarity=negative,"
                                 "bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left"
                                 % (profile_xmin, s_pad_y, profile_xmax, s_pad_y))
                # --线垂直方向
                for i in range(1, loop_num_x + 1):
                    s_pad_x = sr_xmin + 22 * i
                    self.GEN.COM("add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=s3000,polarity=negative,"
                                 "bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left"
                                 % (s_pad_x, profile_ymin, s_pad_x, profile_ymax))
                self.GEN.COM(
                    "sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
                self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                             "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_top)
                self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                             "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_bot)

    def fill_pitch(self, direct, target_top=None, target_bot=None):
        """
        排版间距之间的铺铜
        :return:
        :rtype:
        """
        sr_xmin = self.parm.sr_xmin
        sr_ymin = self.parm.sr_ymin
        sr_xmax = self.parm.sr_xmax
        sr_ymax = self.parm.sr_ymax
        add_eagle_panel = '否'
        # add_eagle_panel = self.parm.add_eagle_panel
        # --solid fill tmp2
        if direct == 'horizontal':
            margin_x = 10
            margin_y = 0.5

            margin2_x = 0
            margin2_y = 2.0
        else:
            margin_y = 10
            margin_x = 0.5

            margin2_y = 0
            margin2_x = 2.0
        self.GEN.CLEAR_LAYER()
        self.GEN.DELETE_LAYER('eagle-clear-pitch')
        if add_eagle_panel == '是':
            self.GEN.COM("copy_layer,source_job=%s,source_step=%s,source_layer=eagle-dot-pitch,"
                         "dest=layer_name,dest_layer=eagle-clear-pitch,mode=append,invert=no" % (self.JOB, self.STEP))
            self.GEN.AFFECTED_LAYER('eagle-clear-pitch', 'yes')
            self.GEN.SEL_CHANEG_SYM('s1651')
            self.GEN.CLEAR_LAYER()

        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.create_tmp_layer('honeycomb-tmp1')

        self.create_tmp_layer('honeycomb-tmp2')
        self.create_tmp_layer('honeycomb-tmp3')

        self.create_tmp_layer('honeycomb-tmp4')
        self.create_tmp_layer('honeycomb-tmp5')

        self.GEN.COM("affected_layer,name=honeycomb-tmp2,mode=single,affected=yes")
        self.GEN.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=25.4,"
                     "use_arcs=yes,symbol=2oz_fw,dx=9.72312,dy=5.588,std_angle=45,std_line_width=254,std_step_dist=1270,"
                     "std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,outline_width=0,outline_invert=no")
        self.GEN.COM("sr_fill,polarity=positive,step_margin_x=-5,step_margin_y=-5,step_max_dist_x=2540,"
                     "step_max_dist_y=2540,sr_margin_x=%s,sr_margin_y=%s,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,"
                     "consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no"
                     % (margin_x, margin_y))

        # --clip掉板外部分
        self.GEN.COM("clip_area_strt")
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (sr_xmin, sr_ymin))
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (sr_xmax, sr_ymax))
        self.GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,"
                     "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")

        # --solid fill tmp1,以下步骤对品字形排版有用
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tmp1,mode=single,affected=yes")
        self.GEN.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=25.4,"
                     "use_arcs=yes,symbol=2oz_fw,dx=9.72312,dy=5.588,std_angle=45,std_line_width=254,std_step_dist=1270,"
                     "std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,outline_width=0,outline_invert=no")
        self.GEN.COM("sr_fill,polarity=positive,step_margin_x=-5,step_margin_y=-5,step_max_dist_x=2540,"
                     "step_max_dist_y=2540,sr_margin_x=2.5,sr_margin_y=2.5,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,"
                     "consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no")
        # --resize tmp1然后copy到tmp2
        self.GEN.COM("sel_resize,size=4000,corner_ctl=no")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-tmp2,invert=yes,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-tmp4,invert=no,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")
        # -- 在tmp5层别铺铜，延step外围 后续此层别被替换为反面外围铜
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('honeycomb-tmp5','yes')
        self.GEN.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=25.4,"
                     "use_arcs=yes,symbol=2oz_fw,dx=9.72312,dy=5.588,std_angle=45,std_line_width=254,std_step_dist=1270,"
                     "std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,outline_width=0,outline_invert=no")
        self.GEN.COM("sr_fill,polarity=positive,step_margin_x=-5,step_margin_y=-5,step_max_dist_x=2540,"
                     "step_max_dist_y=2540,sr_margin_x=%s,sr_margin_y=%s,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,"
                     "consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no"
                     % (margin2_x, margin2_y))
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-tmp4,invert=yes,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('honeycomb-tmp4','yes')
        # === 让出角线位置
        self.GEN.ADD_PAD(sr_xmin,sr_ymin,'s5000',pol='negative')
        self.GEN.ADD_PAD(sr_xmax,sr_ymin,'s5000',pol='negative')
        self.GEN.ADD_PAD(sr_xmin,sr_ymax,'s5000',pol='negative')
        self.GEN.ADD_PAD(sr_xmax,sr_ymax,'s5000',pol='negative')

        self.GEN.COM("sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
        self.GEN.COM('clip_area_strt')
        self.GEN.COM('clip_area_end,layers_mode=affected_layers,layer=,area=profile,area_type=rectangle,inout=outside,contour_cut=no,margin=0,feat_types=line\;pad\;surface\;arc\;text')
        # === 外围一圈线
        self.GEN.COM("copy_layer,source_job=%s,source_step=%s,source_layer=honeycomb-tmp4,"
                     "dest=layer_name,dest_layer=honeycomb-tmp5,mode=replace,invert=no" % (self.JOB, self.STEP))
        # self.GEN.SEL_COPY('honeycomb-tmp2')
        self.GEN.CLEAR_LAYER()

        # --整体化tmp2
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tmp2,mode=single,affected=yes")
        self.GEN.COM("sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
        self.GEN.SEL_COPY('honeycomb-tmp3')
        # --挑选出排版间距之间的铺铜
        self.GEN.COM("filter_reset,filter_name=popup")
        self.GEN.COM("filter_set,filter_name=popup,update_popup=no,feat_types=surface")
        self.GEN.COM("filter_set,filter_name=popup,update_popup=no,polarity=positive")
        self.GEN.FILTER_SELECT()
        self.GEN.COM("affected_layer,name=honeycomb-tmp4,mode=single,affected=yes")

        count = self.GEN.GET_SELECT_COUNT()
        if count > 0:
            # === 为区分正反面，增加层别 ===
            self.GEN.COM('sel_clear_feat')
            if add_eagle_panel == '是':
                self.GEN.COM("copy_layer,source_job=%s,source_step=%s,source_layer=eagle-clear-pitch,"
                             "dest=layer_name,dest_layer=honeycomb-tmp2,mode=append,invert=yes" % (self.JOB,self.STEP))
                self.GEN.COM("affected_layer,name=honeycomb-tmp2,mode=single,affected=no")

            # === top面 ===
            line_length = 5
            line_gap = 2
            split_length = line_length + line_gap
            gap_sym = 's%s' % (line_gap * 1000)
            # 用线去填充.
            loop_num_y = int((sr_ymax - sr_ymin) / split_length)
            loop_num_x = int((sr_xmax - sr_xmin) / split_length)

            fix_start_x = sr_xmin - 3
            fix_end_x = sr_xmax + 3
            fix_start_y = sr_ymin - 3
            fix_end_y = sr_ymax + 3
            # --线水平方向
            if direct == 'vertical':
                for i in range(1, loop_num_y + 1):
                    s_pad_y = sr_ymin + split_length * i
                    self.GEN.COM("add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=%s,polarity=negative,"
                                 "bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left"
                                 % (fix_start_x, s_pad_y, fix_end_x, s_pad_y, gap_sym))
            # --线垂直方向
            if direct == 'horizontal':
                for i in range(1, loop_num_x + 1):
                    s_pad_x = sr_xmin + split_length * i
                    self.GEN.COM("add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=%s,polarity=negative,"
                                 "bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left"
                                 % (s_pad_x, fix_start_y, s_pad_x, fix_end_y, gap_sym))
                # === V2.00 按需求3689 取消 ===
                # gold_finger_c = self.JOB[7]
                # if gold_finger_c == "n":
                #     self.GEN.COM ("sel_delete")


            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER('honeycomb-tmp2','yes')
            self.GEN.COM(
                "sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
            self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                         "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_top)
            self.GEN.CLEAR_LAYER()

            self.GEN.AFFECTED_LAYER('honeycomb-tmp4','yes')
            self.GEN.COM(
                "sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
            self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                         "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_top)
            self.GEN.CLEAR_LAYER()

            self.GEN.AFFECTED_LAYER('honeycomb-tmp3', 'yes')
            self.GEN.AFFECTED_LAYER('honeycomb-tmp5','yes')

            if add_eagle_panel == '是':
                self.GEN.COM("copy_layer,source_job=%s,source_step=%s,source_layer=eagle-clear-pitch,"
                             "dest=layer_name,dest_layer=honeycomb-tmp3,mode=append,invert=yes" % (self.JOB,self.STEP))
                self.GEN.AFFECTED_LAYER('honeycomb-tmp3', 'no')

            # === bot 面 ===
            line_length = 5
            line_gap = 2
            split_length = line_length + line_gap
            gap_sym = 's%s' % (line_gap * 1000)
            # 用线去填充.
            loop_num_y = int((sr_ymax - sr_ymin) / split_length)
            loop_num_x = int((sr_xmax - sr_xmin) / split_length)
            fix_start_x = sr_xmin - 3
            fix_end_x = sr_xmax + 3
            fix_start_y = sr_ymin - 3
            fix_end_y = sr_ymax + 3
            # --线水平方向
            if direct == 'vertical':
                for i in range(1, loop_num_y + 1):
                    s_pad_y = sr_ymin + split_length * i - 2
                    self.GEN.COM("add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=%s,polarity=negative,"
                                 "bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left"
                                 % (fix_start_x, s_pad_y, fix_end_x, s_pad_y, gap_sym))
            # --线垂直方向
            if direct == 'horizontal':
                for i in range(1, loop_num_x + 1):
                    s_pad_x = sr_xmin + split_length * i - 2
                    self.GEN.COM("add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=%s,polarity=negative,"
                                 "bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left"
                                 % (s_pad_x, fix_start_y, s_pad_x, fix_end_y, gap_sym))
            # === V2.00 按需求3689 取消 ===
            # gold_finger_c = self.JOB[7]
            # if gold_finger_c == "n":
            #     self.GEN.COM ("sel_delete")



            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER('honeycomb-tmp3','yes')
            self.GEN.COM(
                "sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
            self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                         "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_bot)
            self.GEN.CLEAR_LAYER()

            self.GEN.AFFECTED_LAYER('honeycomb-tmp5','yes')
            self.GEN.COM(
                "sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
            self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                         "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_bot)
            self.GEN.CLEAR_LAYER()

    def create_tmp_layer(self, layer):
        """
        创建临时层别
        :return:
        :rtype:
        """
        info = self.GEN.DO_INFO('-t layer -e %s/pnl_m/%s -d EXISTS' % (jobName, layer))
        if info['gEXISTS'] == "no":
            self.GEN.COM('create_layer,layer=%s,context=misc,type=signal,polarity=positive,ins_layer=' % layer)
        else:
            # --删除当前panel中内容物，这样不用创建新层，其它step中的内容会被保留
            self.GEN.AFFECTED_LAYER(layer, 'yes')
            self.GEN.COM('sel_delete')
            self.GEN.AFFECTED_LAYER(layer, 'no')

    def add_inn_eagle_pad(self):
        """
        在铺铜时已经添加好的层别进行鹰眼pad的copy
        :return:
        """

        fill_array = self.parm.fill_array

        self.GEN.CLEAR_LAYER()
        for fill_hash in fill_array:
            layer_name = fill_hash.layer_name
            layer_mode = fill_hash.layer_mode
            if layer_mode == 'sec':
                if self.GEN.LAYER_EXISTS('song-tmp', job=self.JOB, step=self.STEP) == 'yes':
                    self.GEN.AFFECTED_LAYER('song-tmp', 'yes')
                    self.GEN.SEL_COPY(layer_name)
                self.GEN.CLEAR_LAYER()
                if self.GEN.LAYER_EXISTS('song-create-tmp', job=self.JOB, step=self.STEP) == 'yes':
                    # --song-create-tmp板边的蝴蝶pad
                    self.GEN.AFFECTED_LAYER('song-create-tmp', 'yes')
                    # --删除与外层symbol相连接的鹰眼pad
                    self.GEN.FILTER_RESET()
                    self.GEN.SEL_REF_FEAT(layer_name, 'disjoint', f_type='line;pad;arc;text')
                    if int(self.GEN.GET_SELECT_COUNT()) > 0:
                        self.GEN.SEL_COPY(layer_name)
                self.GEN.CLEAR_LAYER()
        # === pad eagle
        self.GEN.DELETE_LAYER('song-tmp')
        self.GEN.DELETE_LAYER('song-create-tmp')

class CalculateCopperArea:

    def __init__(self):
        self.GEN = GEN_COM()
        # self.main()

    def main(self):
        job_data = []
        # self.GEN.OPEN_STEP('pnl_m')
        ww_exist = False
        if GEN.LAYER_EXISTS('ww', step='set_m') == 'yes':
            infolines = self.GEN.INFO("-t layer -e %s/set_m/ww  -d FEATURES" % os.environ.get("JOB"))
            if len(infolines) > 2:
                ww_exist = True

        for layer in pb.inner:
            dict = {}
            fill_type = self.get_fill_type(layer['name'])
            dict['type'] = fill_type
            dict['name'] = layer['name']
            copper_areas = self.get_copper_area(layer['name'])
            # self.GEN.PAUSE(copper_areas)
            dict['pc'] = copper_areas
            dict['ww'] = ww_exist
            job_data.append(dict)
        return job_data


    def get_copper_area(self, lay_1):
        infolines = self.GEN.INFO("-t layer -e %s/pnl_m/%s  -d FEATURES" % (os.environ.get("JOB"), lay_1))
        PerCent = None
        for line in infolines:
            if 'copper_persen' in line:
                PerCent =  line.split()[10].strip("'")
                break
        return PerCent

        # unit = self.GEN.GET_UNITS()
        # if unit == 'mm':
        #     self.GEN.CHANGE_UNITS('inch')
        # self.GEN.VOF()
        # self.GEN.COM('copper_area, layer1 = %s, layer2 = , drills = no, consider_rout = no, ignore_pth_no_pad = no, drills_source = matrix,thickness = 0, '
        #              'resolution_value = 1, x_boxes = 3, y_boxes = 3, area = no, dist_map = yes' % lay_1)
        # Arec_V = self.GEN.COMANS
        # area = self.GEN.STATUS
        # self.GEN.VON()
        # self.GEN.CHANGE_UNITS(unit)
        # # --返回
        # if area == 0:
        #     # --以空格分隔出数组
        #     # Area = '%.1f' % float(Arec_V.split(' ')[0])
        #     PerCent = '%.1f' % float(Arec_V.split(' ')[1])
        #     return PerCent
        # else:
        #     return False

    def get_fill_type(self, layer):
        infolines = self.GEN.INFO("-t layer -e %s/set_m/%s  -d FEATURES" % (os.environ.get("JOB"),layer))
        fill_type = None
        for line in infolines:
            if 'fill_lx' in line:
                fill_type = 'lx'
                break
            elif 'fill_fx' in line:
                fill_type = 'fx'
                break
            elif 'fill_yx' in line:
                fill_type = 'yx'
                break
            elif 'fill_cu' in line:
                fill_type = 'cu'
                break
        return fill_type

if __name__ == "__main__":
    # 检测2oz 的symbol
    if platform.system() == "Windows":
        try:
            not_sym = False
            for sym in ['2oz_fw', 'fill_ladder_bot', 'fill_ladder_top']:
                symbol_path = os.environ.get("GENESIS_DIR") + '/fw/lib/symbols/{0}'.format(sym)
                if not os.path.isdir(symbol_path):
                    not_sym = True
                    shutil.copytree(_file_path + "\\{0}".format(sym), os.environ.get("GENESIS_DIR") + '/fw/lib/symbols/{0}'.format(sym))

            if not_sym:
                showMessageInfo(u"genesis目录内没有相应的symbol,程序将退出运行，退出后请重启genesis！")
                sys.exit(0)
        except IOError:
            showMessageInfo(u"COPY symbol 发生错误，请联系程序员解决！")
            sys.exit(0)

    inplan = InPlan(jobName)
    lamin_data_check = inplan.getLaminData()
    if not lamin_data_check:
        showMessageInfo(u"未获取到INPLAN的压合裁磨尺寸")
        sys.exit(0)
    if not inplan.get_Cu_thickness():
        showMessageInfo(u"未获取到INPLAN的内层铜厚信息")
        sys.exit(0)
    set_inplan = {}
    pnl_inplan = {}
    try:
        inplan_stuck = inplan.get_stuck_data()
        set_inplan['x'] = inplan_stuck.get('SET_X')
        set_inplan['y'] = inplan_stuck.get('SET_Y')
        set_inplan['num'] = inplan_stuck.get('SET_PCS')
        pnl_inplan['x'] = inplan_stuck['PNL_X']
        pnl_inplan['y'] = inplan_stuck['PNL_Y']
        pnl_inplan['num'] = inplan_stuck.get('PANEL_SET')
        pnl_inplan['set'] = inplan.getPanelSRTable()
    except:
        showMessageInfo(u"未获取到INPLAN的拼版信息，请手动拼版，名为: set_m")
    erros = []
    if not set_inplan['x']:
        erros.append(u"未获取到InPlan的SET-X尺寸")
    elif not set_inplan['y']:
        erros.append(u"未获取到InPlan的SET-Y尺寸")
    elif not set_inplan['num']:
        erros.append(u"未获取到InPlan的SET中PCS数量")
    elif not pnl_inplan['x']:
        erros.append(u"未获取到InPlan的PNL-X尺寸")
    elif not pnl_inplan['y']:
        erros.append(u"未获取到InPlan的PNL-Y尺寸")
    elif not pnl_inplan['set']:
        erros.append(u"请检查inplan中是否已经拼好PNL")
    if erros:
        STR = '\n'.join(erros)
        msg = msgBox()
        msg.information(None,u"提示", u" {0} \n"
                                        u"未正确获取到到INPLAN的PNL拼版信息，不能自动拼版，解决方案:!\n"
                                       u"  1--在InPlan中完成pnl拼版流程并checkin\n"
                                       u"  2--手动拼版，命名为pnl_m,然后运行铺铜程序".format(STR),QMessageBox.Ok)
        # showMessageInfo(u"未获取到INPLAN的PNL拼版信息，不能自动拼版,请保证完成InPlan拼版流程并checkin名为: pnl_m")
    pb = InfoJob()
    main_win = MyWindow()
    wgt_win = SelWindow()
    dlg = MyDialog()
    # 界面设置居中，改变linux时候不居中的情况
    screen = QtGui.QDesktopWidget().screenGeometry()
    size = main_win.geometry()
    main_win.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)
    main_win.show()
    sys.exit(app.exec_())
