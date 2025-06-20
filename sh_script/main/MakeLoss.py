#!/usr/bin/env python26
# -*- coding: utf-8 -*-
# --------------------------------------------------------- #
#                VTG.SH SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    consenmy(吕康侠)
# @Mail         :    1943719064qq.com
# @Date         :    2024/07/15
# @Revision     :    1.0.0
# @File         :    MakeLoss.py
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
__version__ = "V1.0.0"

import platform
import csv
import json,getpass
import math
import os
import re
import sys
from PyQt4 import QtCore, QtGui, Qt
#from PyQt4.QtGui import *
#from PyQt4.QtCore import *
from collections import Mapping, MutableSequence
from operator import itemgetter
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")


from get_icg_coupon_compensate_value import icg_coupon_compensate_value
icg_coupon_compensate = icg_coupon_compensate_value()

from create_ui_model import app
from SMK_Imp_TableDelegate import itemDelegate

import gClasses
from genesisPackages_zl import matrixInfo, job, \
     getSmallestHole, laser_drill_layers, mai_drill_layers, \
     get_drill_start_end_layers, tongkongDrillLayer
    
import genCOM_26 as genCOM
import Oracle_DB
from messageBoxPro import msgBox
from Ui import lossRunUI_NV as FormUi
from datetime import datetime
# os.chdir("./UI")
import MakeLossExcute
# import getCompensationValue as getComp_Val
#reload(sys)
#sys.setdefaultencoding('utf-8')

class InputDialog(QtGui.QDialog):
    def __init__(self, parent=None,message=None):
        super(InputDialog, self).__init__(parent)
        self.setWindowTitle('Input Dialog')

        self.layout = QtGui.QVBoxLayout(self)
        self.label = QtGui.QLabel(message)
        self.edit = QtGui.QLineEdit()
        self.buttons = QtGui.QDialogButtonBox(Qt.QDialogButtonBox.Ok | Qt.QDialogButtonBox.Cancel)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.edit)
        self.layout.addWidget(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
    def getText(self):
        return self.edit.text()


class listView(QtGui.QWidget):

    def __init__(self, parent = None):

        super(listView, self).__init__(parent)

        self.setWindowFlags(Qt.Qt.FramelessWindowHint | Qt.Qt.WindowMinimizeButtonHint | Qt.Qt.WindowSystemMenuHint | Qt.Qt.WindowStaysOnTopHint)

        self.listbox = QtGui.QListWidget()
        label = QtGui.QLabel(u"请勾阻值 然后点击确定")
        pushbtn = QtGui.QPushButton(u"确定")
        self.statusBar = QtGui.QStatusBar()
        self.statusBar.setFixedHeight(30)
        self.statusBar.addWidget(label)
        self.statusBar.addWidget(pushbtn)
        
        self.listbox.addItems(["", "10", "50", "100"])
        
        self.listbox.itemClicked.connect(self.onItemClicked)

        main_layout = QtGui.QVBoxLayout()        
        main_layout.addWidget(self.listbox)
        main_layout.addWidget(self.statusBar)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)        
        pushbtn.clicked.connect(self.set_layers)
        
        self.get_sigle_select_condition()        
        
    def onItemClicked(self, item):
        if self.sigle_select_condition == "yes":
            for i in range(self.listbox.count()):  
                if self.listbox.item(i) != item:  
                    self.listbox.item(i).setCheckState(0)
                    
    def get_sigle_select_condition(self, condition="no"):
        self.sigle_select_condition = condition
        
    def set_layers(self):
        values = []
        for index in range(self.listbox.count()):
            item = self.listbox.item(index)            
            if item.checkState() == 2:
                values.append(unicode(item.text().toUtf8(), 'utf8', 'ignore').encode('cp936').decode("cp936"))
        
        self.hide()
        self.emit(QtCore.SIGNAL("ohm_values(PyQt_PyObject)"), values)
        
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)
    
class UI_info(object):
    # --描述符类，主要用来从UI界面取值或者向UI界面设置值
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, cls):
        """
        通过描述符获取值
        :param instance:描述符实例
        :type instance:
        :param cls:描述符托管类
        :type cls:
        :return:
        :rtype:
        """
        # print "描述符获取类变量"
        if instance is None:
            # --如果是通过类名来调用，直接返回描述符本身
            return self
        else:
            # --如果是通过实例调用
            obj = instance.findChild(QWidget,self.name)
            # print "描述符实例字典中没有值，直接从界面取值"
            if isinstance(obj,QtGui.QComboBox):
                curText = obj.currentText().toUtf8()
                return str(curText)
            elif isinstance(obj,QtGui.QCheckBox):
                return obj.isChecked()
            elif isinstance(obj,QtGui.QRadioButton):
                return obj.isChecked()
            else:
                curText = obj.text().toUtf8()
                try:
                    if isinstance(curText, bool):
                        # --bool值也可以float,False=0.0,True=1.0,所以不能直接转float，避免造成误解
                        curText = bool(curText)
                    else:
                        # --如果LineEdit中的是float,直接返回float,省去后面转换的麻烦
                        curText = float(curText)
                    return curText
                except ValueError:
                    return str(curText)

    def __set__(self, instance, value):
        """
        通过描述符设值
        :param instance:描述符实例
        :type instance:
        :param value:值
        :type value:
        :return:
        :rtype:
        """
        # print "描述符设置类变量"
        obj = instance.findChild(QWidget, self.name)
        if isinstance(obj, QtGui.QComboBox):
            AllItems = [obj.itemText(i) for i in range(obj.count())]
            index = AllItems.index(value)
            obj.setCurrentIndex(index)
        elif isinstance(obj,QtGui.QCheckBox):
            obj.setChecked(value)
        elif isinstance(obj,QtGui.QRadioButton):
            obj.setChecked(value)
        else:
            if isinstance(value,float) or isinstance(value,int):
                # --如果是浮点数，要转成str,否则会报错
                value = str(value)
            obj.setText(value)

class FrozenJSON(object):
    """
    一个只读接口，使用属性表示法访问JSON类对象
    """
    def __init__(self, mapping):
        self.__data = dict(mapping)

    def __getattr__(self, name):
        """
        FrozenJSON 类的关键是__getattr__ 方法
        仅当无法使用常规的方式获取属性(即在实例、类或超类中找不到指定的属性),解释器才会调用特殊的__getattr__方法
        :param name: 属性名比如.keys,.values,.items,不是字典键
        :type name:
        :return:
        :rtype:
        """
        if hasattr(self.__data, name):
            # --比如调用字典的keys、values等方法
            return getattr(self.__data, name)
        else:
            return FrozenJSON.build(self.__data[name])

    @classmethod
    def build(cls, obj):
        """
        类方法，第一个参数是类本身
        :param arg: 构建类的参数
        """
        if isinstance(obj, Mapping):
            # --如果obj 是映射,那就构建一个FrozenJSON对象
            return cls(obj)
        elif isinstance(obj, MutableSequence):
            # --如果参数是序列实例
            return [cls.build(item) for item in obj]
        else:
            # --其它如字符、int形式直接返回
            return obj

# --所有与InPlan查询相关的全部写到InPlan类中
class InPlan(object):
    def __init__(self,job_name):
        self.JOB = job_name
        self.JOB_SQL = self.JOB.upper()[:13]  # --截取前十三位料号名
        if self.JOB == self.JOB[:13] + "-c":
            # --专门做阻抗条的料号,参考K65308GN238A1-C
            self.JOB_SQL = self.JOB.upper()
        self.JOB_like = '%' + self.JOB_SQL + '%'
        self.layer_number = int(self.JOB[4:6])

        # --Oracle相关参数定义
        self.DB_O = Oracle_DB.ORACLE_INIT()
        self.dbc_o = self.DB_O.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
                                          username='GETDATA', passwd='InplanAdmin')

    def __del__(self):
        # --关闭数据库连接
        if self.dbc_o:
            self.DB_O.DB_CLOSE(self.dbc_o)

    def get_diff_imp(self):
        """
        获取差分阻抗信息
        :return:
        :rtype:
        """
        sql = """
        SELECT
            a.item_name AS 料号名,
            i.CREATION_DATE AS 创建时间,
            d.model_type_ AS 阻抗性质,
            d.trace_layer_ AS 测试层1,
            d.ref_layer_ AS 参考层1,
            round(d.finish_lw_, 3) AS 成品线宽,
            round(d.finish_ls_, 3) AS 成品线距,
            d.spacing_2_copper_ AS 到铜皮间距,
            c.customer_required_impedance AS 成品阻抗,
            round(c.artwork_trace_width, 2) work_width 
        FROM
            vgt_hdi.items a
            INNER JOIN vgt_hdi.public_items b ON a.root_id = b.root_id
            INNER JOIN vgt_hdi.impedance_constraint c ON b.item_id = c.item_id 
            AND b.REVISION_ID = c.revision_id
            INNER JOIN vgt_hdi.impedance_constraint_da d ON c.item_id = d.item_id 
            AND c.revision_id = d.revision_id 
            AND c.sequential_index = d.sequential_index
            INNER JOIN vgt_hdi.rpt_job_list i ON i.job_name = a.item_name 
        WHERE
            a.ITEM_NAME = '%s'
            -- AND d.model_type_ in (1,3)
            """ % self.JOB_SQL
        # --返回数据字典
        return self.DB_O.SELECT_DIC(self.dbc_o, sql)

    def get_REQUIRED_CU_WEIGHT_and_LAYER_ORIENTATION(self):
        """
        从InPlan中获取铜厚及层别正反的数据
        :return:sql后的字典
        """
        sql = """
            SELECT I.ITEM_NAME AS JOB_NAME,
                     II.ITEM_NAME AS LAYER_NAME,
                     ROUND(C.REQUIRED_CU_WEIGHT / 28.3495, 2) AS CU_WEIGHT,
                     ROUND(CD.CAL_CU_THK_ , 2) AS FINISH_THICKNESS,
                     C.LAYER_ORIENTATION,
                     C.LAYER_INDEX
            FROM VGT_HDI.PUBLIC_ITEMS    I,
                     VGT_HDI."JOB"           J,
                     VGT_HDI.PUBLIC_ITEMS    II,
                     VGT_HDI.COPPER_LAYER    C,
                     VGT_HDI.COPPER_LAYER_DA CD
            WHERE I.ITEM_TYPE = 2
            AND I.ITEM_NAME = '%s'
            AND I.ROOT_ID = J.ITEM_ID
            AND I.ITEM_ID = J.ITEM_ID
             AND I.REVISION_ID = J.REVISION_ID
             AND I.ROOT_ID = II.ROOT_ID
             AND II.ITEM_TYPE = 3
             AND II.ITEM_ID = C.ITEM_ID
             AND II.REVISION_ID = C.REVISION_ID
             AND C.ITEM_ID = CD.ITEM_ID
             AND C.REVISION_ID = CD.REVISION_ID
            ORDER BY C.LAYER_INDEX""" % self.JOB_SQL
        # --返回数据字典
        return self.DB_O.SELECT_DIC(self.dbc_o, sql)

    def get_hole_wall_thickness(self):
        """
        获取孔壁厚度
        """
        sql = """
            SELECT
                MIN_HOLE_CU_ 
            FROM
                vgt.rpt_drill_program_list 
            WHERE
                job_name = '%s'
                AND program_name = 'drl'
            """ % self.JOB_SQL
        # --返回数据字典
        flowDict = self.DB_O.SELECT_DIC(self.dbc_o, sql)
        wall_thickness = flowDict[0]['MIN_HOLE_CU_']
        wall_thickness = float('%.2f' % wall_thickness)
        hole_thickness = 0.7
        if wall_thickness >= 1.0:
            hole_thickness = 1.0
        elif wall_thickness >= 0.9:
            hole_thickness = 0.9
        elif wall_thickness >= 0.8:
            hole_thickness = 0.8
        elif wall_thickness >= 0.7:
            hole_thickness = 0.7
        return hole_thickness

    def get_flow_type(self):
        """
        从InPlan中获取一次铜、二次铜流程
        :return: flow_content 一次铜、二次铜
        """
        sql = """
            SELECT
                p.item_name as JOB_NAME, 
                i.item_name as LAYER_NAME,
                s.Flow_TYPE_  as FLOW_TYPE
            FROM
                VGT.public_items p,
                VGT.job j,
                VGT.PROCESS pr,
                VGT.PROCESS_DA s,
                VGT.public_items i 
            WHERE
                p.item_type = 2 
                AND p.item_name = '%s' 
                AND j.item_id = p.item_id 
                AND j.revision_id = p.revision_id 
                AND p.root_id = i.root_id 
                AND i.item_type = 7 
                AND i.item_id = s.item_id 
                AND i.revision_id = s.revision_id 
                AND pr.item_id = s.item_id 
                AND pr.revision_id = s.revision_id 
                AND pr.proc_type = 1
                AND pr.proc_subtype=29 """ % self.JOB_SQL

        # --返回数据字典
        flowDict = self.DB_O.SELECT_DIC(self.dbc_o, sql)
        flow_content = flowDict[0]['FLOW_TYPE']
        if flow_content == 1 or flow_content == 2:
            # --2对应none,也当成一次铜
            flow_content = u'一次铜'
        else:
            flow_content = u'二次铜'
        return flow_content

    def get_core_thick(self):
        """
        层别关联core厚度,内层补偿需考虑内层铜厚为1oz，基板厚铜≥0.8MM的界定，间距需3.4MIL，阻抗脚本需判定间距。
        :return:
        :rtype:
        """
        core_thick = dict()
        sql = """
            SELECT
                p.ITEM_NAME,
                pi.ITEM_NAME AS LAYER_NAME,
                ROUND( c.laminate_thickness / 39.37, 3 ) AS CORE_THICKNESS,
                co.layer_index,
                seg.stackup_seg_index 
            FROM
                VGT.public_items P,
                vgt.public_items i,
                vgt.public_items pi,
                vgt.STACKUP_SEG seg,
                VGT.SEGMENT_MATERIAL sm,
                vgt.MATERIAL m,
                vgt.core c,
                vgt.copper_layer co 
            WHERE
                p.item_type = 2 
                AND upper( p.item_name ) = '%s'
                AND i.root_id = p.root_id 
                AND i.item_type = 10 
                AND seg.item_id = i.item_id 
                AND seg.revision_id = i.revision_id 
                AND seg.segment_type = 0 
                AND sm.item_id = i.item_id 
                AND sm.revision_id = i.revision_id 
                AND m.item_id = sm.material_item_id 
                AND m.revision_id = sm.material_revision_id 
                AND m.item_id = c.item_id 
                AND m.REVISION_ID = c.REVISION_ID 
                AND i.root_id = pi.root_id 
                AND pi.item_type = 3 
                AND pi.item_id = co.item_id 
                AND pi.revision_id = co.revision_id 
                AND ( seg.stackup_seg_index = co.layer_index )
                """ % self.JOB_SQL
        query_result = self.DB_O.SELECT_DIC(self.dbc_o, sql)
        for query_dict in query_result:
            layer = query_dict['LAYER_NAME'].lower()
            core_thickness = query_dict['CORE_THICKNESS']
            core_thick[layer] = core_thickness
        return core_thick

    def get_Layer_Mode(self):
        """
        层别归类
        :return:
        :rtype:
        """
        core_thick = self.get_core_thick()
        layerMode = dict()
        outLayers = []
        secLayers = []
        innLayers = []
        sql = """
            SELECT
                p.item_name AS JOB_NAME,
                i.item_name AS LAYERS,
                pr.proc_subtype AS PRO_TYPE,
            -- decode(d.proc_subtype,29,'最外层',28,'子压合',27,'电镀芯板',26,'芯板') as  类型
                s.Flow_TYPE_ AS FLOW_TYPE 
            FROM
                vgt.public_items p
                INNER JOIN vgt.job j ON p.item_id = j.item_id 
                AND p.revision_id = j.revision_id
                INNER JOIN vgt.public_items i ON p.root_id = i.root_id
                INNER JOIN vgt.process pr ON i.item_id = pr.item_id 
                AND i.revision_id = pr.revision_id
                INNER JOIN vgt.process_da s ON i.item_id = s.item_id 
                AND i.revision_id = s.revision_id 
                AND pr.item_id = s.item_id 
                AND pr.revision_id = s.revision_id 
            WHERE
                p.item_name = '%s'
                AND pr.proc_type = 1
            """ % self.JOB_SQL
        query_result = self.DB_O.SELECT_DIC(self.dbc_o, sql)
        for query_dict in query_result:
            layers = query_dict['LAYERS']
            layers = layers.lower().split('-')
            proc_subtype = query_dict['PRO_TYPE']
            if proc_subtype in [26]:
                innLayers.extend(layers)
                if core_thick.has_key(layers[0]):
                    # --补全core的另一个层别
                    core_thick[layers[1]] = core_thick[layers[0]]
                elif core_thick.has_key(layers[1]):
                    # --补全core的另一个层别
                    core_thick[layers[0]] = core_thick[layers[1]]
            elif proc_subtype in [27,28]:
                secLayers.extend(layers)
            elif proc_subtype in [29]:
                outLayers.extend(layers)
        layerMode['out'] = outLayers
        layerMode['sec'] = secLayers
        layerMode['inn'] = innLayers
        return layerMode,core_thick

    def get_bd_info(self):
        """
        通过sql查询获取背钻
        :return:
        :rtype:
        """
        bk_drl = []
        sql = """
        SELECT
            a.item_name AS 料号名,
            c.item_name AS 钻带名,
            decode(
                d.drill_technology,
                0,
                'Mechanical',
                1,
                'Controll Depth',
                2,
                'Laser',
                5,
                'Countersink',
                6,
                'Counterbore',
                7,
                'Backdrill' 
            ) AS 钻带类型,
                decode( e.DRILL_PROGRAM_QUADRANT_, 0, 'Unknown', 1, '第一象限', 2, '第四象限' ) AS 钻带象限,
                d.start_index AS 起始层,
                d.end_index AS 结束层 ,
                e.NON_DRILL_LAYER_ AS 不钻穿层
            FROM
                VGT_HDI.items a INNER join VGT_HDI.job b ON a.item_id = b.item_id 
                AND a.last_checked_in_rev = b.revision_id INNER join VGT_HDI.public_items c
                ON a.root_id = c.root_id INNER join VGT_HDI.drill_program d ON c.item_id = d.item_id 
                AND c.revision_id = d.revision_id INNER join VGT_HDI.drill_program_da e ON d.item_id = e.item_id 
                AND d.revision_id = e.revision_id 
            WHERE
                d.drill_technology IN ( 7 ) 
                AND a.item_name = '%s'
            ORDER BY
                d.odb_layer_name
        """ % self.JOB_SQL
        query_result = self.DB_O.SELECT_DIC(self.dbc_o, sql)
        bd_info = []
        for query_dict in query_result:
            layer = query_dict['钻带名'].lower()
            index_start = query_dict['起始层']
            index_end = query_dict['结束层']
            layer_dict = {
                'layer': layer,
                'index_start': index_start,
                'index_end': index_end, 
                'sig_layer':query_dict['不钻穿层'],
                'drillingLayer':abs(query_dict['不钻穿层']-index_start)
            }
            bd_info.append(layer_dict)
        return bd_info

class ERP(object):
    def __init__(self):
        # --连接ERP oracle数据库
        self.DB_O = Oracle_DB.ORACLE_INIT()
        # --servername的连接模式
        self.dbc_e = self.DB_O.DB_CONNECT(host='172.20.218.247', servername='topprod', port='1521',username='zygc', passwd='ZYGC@2019')
        if not self.dbc_e:
            # --sid连接模式
            self.DB_O = Oracle_DB.ORACLE_INIT(tnsName='sid')
            self.dbc_e = self.DB_O.DB_CONNECT(host='172.20.218.247', servername='topprod1', port='1521',
                                              username='zygc', passwd='ZYGC@2019')
    def GetcuserJob(self,job):
        job=job.upper()
        sql="""select TA_IMA02 from ima_file where ima01='%s'
        """%job
        query_result = self.DB_O.SELECT_DIC(self.dbc_e, sql)
        if query_result:
            return query_result[0]['TA_IMA02']
        else:
            return ''
    def GetERPBZ(self,job):
        sql="""				 SELECT
                    TC_AAF00 AS JOBNAME,
                    TC_AAF01 AS LAYERTYPE,
                    TC_AAF03 AS TOOLNUM,
                    TC_AAF04 AS TOOLSIZE,
                    TC_AAF06 AS TOOLCONUT,
                    TC_AAF05 AS TOOLTYPE,
                    TC_AAF09 AS TOOLBZ,
                    TC_AAF32 ,
				    TC_AAF40 AS DRLSIZE,
                    TC_AAF42 AS startlayer,
                    TC_AAF43 AS endlayer,
                    TC_AAF44  
                FROM
                    TC_AAF_FILE 
                WHERE
                    TC_AAF00 = '{0}A' 
                    --OR TC_AAF00 LIKE 'BA8614PF357F2A-%A' 
                    AND TC_AAF01 LIKE '%背钻%'
                ORDER BY
                    TC_AAF01,
                    TC_AAF03
        """.format(job.upper())
        query_result = self.DB_O.SELECT_DIC(self.dbc_e, sql)
        if query_result:
            return query_result
        else:
            return ''

    def get_ERP_stackup(self,job):

        job_del = '%-B'
        sql = """
        SELECT
            TC_AAG00 as JOB,
            TC_AAG01 as GROP,
            TC_AAG02 as LAYER,
            TC_AAG09 as TYPE,
            TC_AAG16 as MARK,
            TC_AAG03 as CODE,
            TC_AAG05 as COUNT,
            TC_AAG29 as FINISHTHICK,
            --TC_AAG12,
            --TC_AAG20 as 制作序号,
            TC_AAG26 as THICK
        FROM
            TC_AAG_FILE
        WHERE
            TC_AAG09 <> 'GB'
            AND TC_AAG00 LIKE '%s'
            AND TC_AAG00 NOT LIKE '%s'
            ORDER BY TC_AAG12
        """ % ("%{0}%".format(job[:13].upper()),job_del)
        query_result = self.DB_O.SELECT_DIC(self.dbc_e, sql)
        if query_result:
            return query_result
        else:
            return ''
    def __del__(self):
        # --关闭数据库连接
        if self.dbc_e:
            self.DB_O.DB_CLOSE(self.dbc_e)

# --重写滚轮事件，以免识操作导致选项错误
#class QComboBox(QComboBox):
    #def wheelEvent(self, QWheelEvent):
        #pass

class MainWindow(QtGui.QWidget):
    ###job
    #label_job= UI_info('label_job')
    #label_step = UI_info('label_step')
    ## --测试孔
    #testSize=UI_info('testSize')
    ## --测试定位孔
    #testDw = UI_info('testDw')
    ## --测试护卫孔
    #viaTilt_hw = UI_info('viaTilt_hw')
    ## --外围孔
    #out_linehole = UI_info('out_linehole')
    ## --分布孔
    #fenbuhole = UI_info('fenbuhole')
    ###定位孔
    #dwhole= UI_info('dwhole')
    ####欧姆值
    #comboBox_om=UI_info('comboBox_om')
    #dtx_size = UI_info('dtx')
    def __init__(self,parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.JOB = os.environ.get('JOB', None)
        self.layer_number = int(self.JOB[4:6])
        self.STEP = os.environ.get('STEP', None)
        self.GEN = genCOM.GEN_COM()
        self.abs_path = os.path.dirname(os.path.abspath(__file__))
        # --初始化窗口
        # self.ui = FormUi.Ui_MainWindow()
        # self.ui.setupUi(self)

        #self.COMP_VAL = getComp_Val.Main()
        #self.getFlow, self.matchComp = self.COMP_VAL.getCom(self.JOB)

        # --定义一个字典，收集所有变量
        self.parm = dict()
        # --连接InPlan并查询相关数据
        self.get_InPlan_info()
        # --添加动态子部件
        # self.addPart_Ui()
        # --从料号获取信息并设置界面参数
        # self.set_UI_by_JOB()
        # --定义信号和槽函数
        # self.slot_func()

        self.create_ui_params()
        
    def create_ui_params(self):
        """创建界面参数"""        
        self.setWindowFlags(Qt.Qt.Window )    
        self.setObjectName("mainWindow")
        self.titlelabel = QtGui.QLabel(u"参数确认")
        self.titlelabel.setStyleSheet("QLabel {color:red}")
        self.setGeometry(700, 100, 0, 0)
        self.resize(1000, 500)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.titlelabel.setFont(font)        
    
        self.dic_editor = {}
        self.dic_label = {}
    
        arraylist1 = [ {u"测试孔": "QLineEdit"},
                      {u"测试定位孔": "QLineEdit"},
                      {u"测试护卫孔": "QLineEdit"},
                      {u"外围孔": "QLineEdit"},
                      {u"分布孔": "QLineEdit"},
                      {u"定位孔": "QLineEdit"},
                      {u"端头线粗": "QLineEdit"},
                      {u"最大频率": "QLineEdit"},
                      {u"客户型号": "QLineEdit"},
                      ]

        group_box_font = QtGui.QFont()
        group_box_font.setBold(True)    
        widget1 = self.set_widget(group_box_font,
                                  arraylist1,
                                   u"基本信息确认(单位um)",
                                   "")
        
        self.tableWidget1 = QtGui.QTableView()        
        self.tableWidget2 = QtGui.QTableView()
        
        self.pushButton = QtGui.QPushButton()
        self.pushButton1 = QtGui.QPushButton()
        self.pushButton2 = QtGui.QPushButton()
        self.pushButton.setText(u"运行")
        self.pushButton1.setText(u"退出")
        self.pushButton2.setText(u"加载上一次数据")
        self.pushButton.setFixedWidth(100)
        self.pushButton1.setFixedWidth(100)
        self.pushButton2.setFixedWidth(100)
        btngroup_layout = QtGui.QGridLayout()
        btngroup_layout.addWidget(self.pushButton,0,0,1,1) 
        btngroup_layout.addWidget(self.pushButton1,0,1,1,1)
        # btngroup_layout.addWidget(self.pushButton2,0,2,1,1)
        btngroup_layout.setSpacing(5)
        btngroup_layout.setContentsMargins(5, 5,5, 5)
        btngroup_layout.setAlignment(QtCore.Qt.AlignTop)          
    
        main_layout =  QtGui.QGridLayout()
        main_layout.addWidget(self.titlelabel,0,0,1,10, QtCore.Qt.AlignCenter)
        main_layout.addWidget(widget1,1,0,1,10)
        main_layout.addWidget(self.tableWidget1,2,0,1,3)
        main_layout.addWidget(self.tableWidget2,2,2,1,9)
        main_layout.addLayout(btngroup_layout, 8, 0,1, 10)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(main_layout)
    
        # main_layout.setSizeConstraint(Qt.QLayout.SetFixedSize)
    
        self.pushButton.clicked.connect(self.clickApply)
        self.pushButton1.clicked.connect(sys.exit)
        # self.pushButton2.clicked.connect(self.reloading_data)
    
        self.setWindowTitle(u"SMK LOSS参数确认%s" % __version__)
        self.setMainUIstyle()
        
        self.setTableWidget(self.tableWidget1, [u"钻带", u"最小孔径(um)"])
        self.setTableWidget(self.tableWidget2, [u"勾选", u"分组step", u"层名", u"菲林线宽",
                                                u"菲林线距", u"到铜皮", u"参考1", u"参考2", u"制作线宽",
                                                u"制作线距", u"原稿到铜",u"OHM", u"补偿", u"阻抗类型"])
        
        self.tableItemDelegate = itemDelegate(self)
        self.tableWidget2.setItemDelegateForColumn(0, self.tableItemDelegate)
        self.connect(self.tableItemDelegate, QtCore.SIGNAL("select_item(PyQt_PyObject,PyQt_PyObject)"), self.order_coupon_step)
        
        
        self.filter_listbox = listView()    
        self.filter_listbox.hide()    
        self.filter_listbox.installEventFilter(self)        
        
        self.tableWidget2.horizontalHeader().sectionClicked.connect(self.show_filter_listbox) 
        self.connect(self.filter_listbox, QtCore.SIGNAL("ohm_values(PyQt_PyObject)"), self.update_tablewidget)
        
        #self.tableWidget1.setEnabled(False)
        #self.tableWidget2.setEnabled(False)            
        self.initial_value()

    def order_coupon_step(self, index, check_box):
        """给选中的行进行step分组"""
        model = self.tableWidget2.model()
        select_imp_row_info = []
        for i,j in self.tableItemDelegate.dic_editor.keys():
            if self.tableItemDelegate.dic_editor[i, j].isChecked():
                sig_layer = str(model.item(i, 2).text()).lower()
                ref_layer1 = str(model.item(i, 5).text()).lower()
                ref_layer2 = str(model.item(i, 6).text()).lower()
                #array_indexes = []
                #for layer in [sig_layer, ref_layer1, ref_layer2]:                    
                    #if layer in signalLayers:
                        #array_indexes.append(signalLayers.index(layer))
                        
                #geceng_ref_layers = []# 隔层参考
                #if array_indexes:                    
                    #for layer_index, layer in enumerate(signalLayers):
                        #if min(array_indexes)< layer_index < max(array_indexes) and layer != sig_layer:
                            #geceng_ref_layers.append(layer)
                            
                info = [sig_layer, ref_layer1, ref_layer2, i]

                select_imp_row_info.append(info)
            else:
                model.item(i, 1).setText("")
        
        dic_zu = {}
        for zu in range(1, 10):
            if not dic_zu.has_key(zu):
                dic_zu[zu] = []
                    
                for info in select_imp_row_info:
                    if "finish_group" not in info:
                        if not dic_zu[zu]:
                            info.append("finish_group")
                            dic_zu[zu].append(info)
                        else:
                            for group_info in dic_zu[zu]:
                                
                                if group_info == info:
                                    break
                                
                                if info[0] in group_info[1:]:
                                    break
                                
                                if info[1] == group_info[0] or \
                                   info[2] == group_info[0] :
                                    break
                            else:                                
                                info.append("finish_group")
                                dic_zu[zu].append(info)
                                    
        # print(dic_zu)
        for key, value in dic_zu.iteritems():
            for info in value:
                model.item(info[3], 1).setText(str(key))
        
    def update_tablewidget(self, values):
        """过滤阻值"""
        # print(values)
        recordStyleIndex = []
            
        rowcount = self.tableWidget2.model().rowCount()        
        for i in range(rowcount):            
            self.tableWidget2.showRow(i)
            ohm = str(self.tableWidget2.model().item(i, 11).text())
            for text in values:
                if float(text) == float(ohm): 
                    recordStyleIndex.append(i)
                    
        if not values:
            return
              
        for i in range(rowcount):            
            if i not in recordStyleIndex:                
                self.tableWidget2.hideRow(i)                     

    def show_filter_listbox(self, column):
        """显示层选择框"""        
        
        if column != 11:
            return
        
        self.filter_listbox.move(QtGui.QCursor.pos())   
        self.filter_listbox.show()
        
    def eventFilter(self,  source,  event):        
        if event.type() == QtCore.QEvent.ActivationChange:            
            if QtGui.QApplication.activeWindow() != self.filter_listbox:                
                self.filter_listbox.close()            
            
        return QtGui.QMainWindow.eventFilter(self,  source,  event)
    
    def initial_value(self):
        """初始化参数"""               
        #for item in ["2/6inch", u"2/5/10inch"]:
            #self.dic_editor[u"loss条长度"].addItem(item)
            
        #for item in [u"横排",u"品字型"]:
            #self.dic_editor[u"loss排列方式"].addItem(item)            
        
        self.dic_editor[u"测试孔"].setText("200")
        self.dic_editor[u"测试定位孔"].setText("1600")
        self.dic_editor[u"测试护卫孔"].setText("200")
        self.dic_editor[u"外围孔"].setText("250")
        self.dic_editor[u"分布孔"].setText("200")
        self.dic_editor[u"定位孔"].setText("2000")
        self.dic_editor[u"端头线粗"].setText("150")
        # job.PAUSE(self.Custmer.decode("utf8"))
        self.dic_editor[u"客户型号"].setText(self.Custmer.decode("utf8"))
        
        self.dic_layer_info = {}
        self.add_data_to_table()
        
    def add_data_to_table(self):
        """表格内加载数据"""
        self.dic_min_hole_size = self.get_min_hole_size()
        arraylist = []
        for key, value in self.dic_min_hole_size.iteritems():
            if isinstance(value, (list, tuple)):
                arraylist.append([key, value[0]])
                continue
            arraylist.append([key, value])
        
        self.set_model_data(self.tableWidget1, arraylist)
        
        # self.dic_layer_info = self.get_layer_pad_ring_line_width()
        #arraylist = []
        #for key in sorted(self.dic_layer_info.keys(), key=lambda x: int(x[1:])):
            #arraylist.append([key]+ self.dic_layer_info[key])
            
        arraylist = self.get_inplan_imp_info()            
        self.set_model_data(self.tableWidget2, arraylist)
        
        self.filter_listbox.listbox.clear()
        ohm_vaues = [x[11] for x in arraylist]
        for ohm in  sorted(set(ohm_vaues)):
            item = QtGui.QListWidgetItem(str(ohm), self.filter_listbox.listbox)
            item.setCheckState(0)
            
    def get_min_hole_size(self):
        """获取最小孔径"""
        dic_min_hole_size = {}
        for drillLayer in tongkongDrillLayer + mai_drill_layers + laser_drill_layers:
            dic_min_hole_size[drillLayer] = ""
            if drillLayer in tongkongDrillLayer:
                if "edit" in matrixInfo["gCOLstep_name"]:
                    # 板内最小孔剔除掉槽孔 及引孔
                    edit_step = gClasses.Step(job, "edit")
                    edit_step.open()
                    edit_step.COM("units,type=mm")
                    edit_step.clearAll()
                    edit_step.affect(drillLayer)
                    edit_step.copyLayer(job.name, "edit", drillLayer, drillLayer+"_tmp")
                    edit_step.copyLayer(job.name, "edit", drillLayer, drillLayer+"_tmp1")
                    edit_step.clearAll()
                    edit_step.affect(drillLayer+"_tmp1")
                    edit_step.contourize()
                    edit_step.COM("sel_delete_atr,attributes=.rout_chain")                        
                    edit_step.COM("sel_resize,size=-5")
                    
                    edit_step.clearAll()
                    edit_step.affect(drillLayer+"_tmp")
                    edit_step.resetFilter()
                    edit_step.filter_set(feat_types='line;arc')
                    edit_step.selectAll()
                    if edit_step.featureSelected():
                        edit_step.moveSel("slot_tmp")
                        edit_step.resetFilter()
                        edit_step.refSelectFilter("slot_tmp")
                        if edit_step.featureSelected():
                            edit_step.selectDelete()
                            
                        edit_step.removeLayer("slot_tmp")                  
                    
                    edit_step.resetFilter()
                    edit_step.refSelectFilter(drillLayer+"_tmp1", mode="cover")
                    if edit_step.featureSelected():
                        edit_step.selectDelete()
                    
                    hole_size = getSmallestHole(job.name, "edit", drillLayer+"_tmp") or \
                        getSmallestHole(job.name, "", drillLayer+"_tmp")
                    
                    edit_step.removeLayer(drillLayer+"_tmp")
                    edit_step.removeLayer(drillLayer+"_tmp1")
                else:
                    hole_size = getSmallestHole(job.name, "edit", drillLayer, panel=None)
            else:                        
                hole_size = getSmallestHole(job.name, "edit", drillLayer, panel=None)
                if getattr(self, "big_laser_holes", None) is not None:
                    for laser_layer in self.big_laser_holes:
                        if drillLayer[1:] in laser_layer:
                            symbolname = self.get_raoshao_laser_hole(drillLayer)
                            # step.PAUSE(str(symbolname))
                            # 绕烧不能判断孔径大小 暂定为350
                            # max_laser_hole = 350
                            # dic_raoshao[drillLayer] = "yes"
                            if symbolname:
                                hole_size = (hole_size, symbolname)
                            else:
                                log = u"检测到{0}镭射INPLAN钻孔信息有备注绕烧，但钻带内处理绕烧孔径失败，请手动修改镭射孔径！"
                                # showMessageInfo(log.format(drillLayer))
                                QtGui.QMessageBox.information(self, u'提示', log.format(drillLayer), 1)                                
            
            if drillLayer in tongkongDrillLayer:
                # 有，如通孔里面没有小孔的，取0.452的孔做导通 最大不能超过0.452
                self.tong_hole_type = "has_small_pth"
                if not hole_size:
                    self.tong_hole_type = "no_small_pth"
                    
                hole_size = hole_size if hole_size else 452
                if hole_size > 452:
                    hole_size = 452
            else:
                if not hole_size:
                    if drillLayer in laser_drill_layers:
                        # 镭射层板内没孔的不计算在内
                        del dic_min_hole_size[drillLayer]
                        
                    continue
                
            dic_min_hole_size[drillLayer] = hole_size
            
        return dic_min_hole_size
            
    def get_inplan_imp_info(self):
        """获取inplan阻抗信息
        料号名 ，分组，阻抗类型，原始线宽，原始间距，原始铜距，阻抗层，参考层，
        出货线宽，出货线距，出货铜距，客户需求阻值，是否开窗阻抗"""
        # array_imp_info = get_inplan_imp(job.name.upper())
        array_imp_info = icg_coupon_compensate.get_dic_compensate_imp_info()
        
        arraylist_info = []
        for dic_info in array_imp_info:
            #if u"特性" in dic_info["imodel".upper()].decode("utf8"):
                #continue
            list_info = ["", ""]
            for key in ["trace_layer_", "workLineWid", "workLineSpc",'workSpc2Cu', "ref_layer_", "finish_lw_",
                        "finish_ls_", "spc2cu","cusimp", "compensate_value", "imodel"]:
                if key == "ref_layer_":
                    key = key.upper()
                    ref_layer = dic_info[key].upper()
                    if ref_layer is not None:
                        if "&" in ref_layer:                            
                            layer1, layer2 = sorted(ref_layer.split("&"),key=lambda x: int(x[1:]) )                      
                            list_info.append(layer1)
                            list_info.append(layer2)
                        else:
                            if dic_info["trace_layer_".upper()] == "L1":
                                list_info.append("None")
                                list_info.append(ref_layer)
                            else:
                                list_info.append(ref_layer)
                                list_info.append("None")        
                    else:
                        list_info.append("None")
                        list_info.append("None")
                else:
                    if key in ["org_width", "org_spc"]:
                        key = key.upper()
                        list_info.append("%.2f" % dic_info[key] if dic_info[key] is not None else 0)
                    elif key in ["imodel"]:
                        key = key.upper()
                        if u"差动" in dic_info[key].decode("utf8"):
                            list_info.append("diff")
                        if u"特性" in dic_info[key].decode("utf8"):
                            list_info.append("single")
                    elif key in ["compensate_value"]:
                        list_info.append(0)
                    elif key in ["workLineWid", "workLineSpc", "workSpc2Cu"]:
                        list_info.append(dic_info[key])
                    else:
                        key = key.upper()
                        list_info.append(dic_info[key])
                    
            # list_info.append(0)
            arraylist_info.append(list_info)
    
        return sorted(arraylist_info, key=lambda x: int(x[2][1:]))  
        
    def set_model_data(self, table, data_info):
        """设置表内数据"""
        model = table.model()            
        model.setRowCount(len(data_info))
        for i, array_info in enumerate(data_info):
            for j , data in enumerate(array_info):                
                index = model.index(i,j, QtCore.QModelIndex())
                model.setData(index, data)
                if table == self.tableWidget2:
                    if j == 0:
                        self.tableWidget2.openPersistentEditor(index)
                        if data == "1":
                            self.tableItemDelegate.dic_editor[i, j].setCheckState(2)
                        else:
                            self.tableItemDelegate.dic_editor[i, j].setCheckState(0)
    
    def setTableWidget(self, table, columnHeader):
        # table = self.tableWidget  
        # self.columnHeader = [u"钻带", u"最小孔", u"最小ring环(um)"]
        self.tableModel = QtGui.QStandardItemModel(table)
        self.tableModel.setColumnCount(len(columnHeader))
        for j in range(len(columnHeader)):
            self.tableModel.setHeaderData(
                j, Qt.Qt.Horizontal, columnHeader[j])
        table.setModel(self.tableModel)
        table.verticalHeader().setVisible(False)
        #table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        #table.setEditTriggers(QtGui.QTableWidget.NoEditTriggers)
        
        header = table.horizontalHeader()
        header.setDefaultAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        header.setTextElideMode(QtCore.Qt.ElideRight)
        header.setStretchLastSection(True)
        header.setClickable(True)
        header.setMouseTracking(True)
        table.setColumnWidth(0, 60)
        table.setColumnWidth(1, 60)
        table.setColumnWidth(2, 70)
        table.setColumnWidth(3, 70)
        table.setColumnWidth(4, 70)
        table.setColumnWidth(5, 60)
        table.setColumnWidth(6, 50)
        table.setColumnWidth(7, 50)
        table.setColumnWidth(8, 70)
        table.setColumnWidth(9, 70)
        table.setColumnWidth(10, 70)
        
        table.hideColumn(12)
        table.hideColumn(13)
        # table.hideColumn(1)

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
                col = 2 if i % 2 else 0
                row = -1 if col else 0
                gridlayout.addWidget(self.dic_label[key], i + 1 + row, 1 + col, 1, 1)
                gridlayout.addWidget(self.dic_editor[key], i + 1 + row, 2 + col, 1, 1)
                
                #if key == u"loss条长度":
                    #self.dic_editor[key].currentIndexChanged.connect(self.change_loss_order)

        gridlayout.setSpacing(5)
        gridlayout.setContentsMargins(5, 5,5, 5)
        gridlayout.setAlignment(QtCore.Qt.AlignTop)
        return gridlayout

    def change_loss_order(self, index):
        if index == 0:
            self.dic_editor[u"loss排列方式"].setCurrentIndex(0)
            self.dic_editor[u"loss排列方式"].setEnabled(False)
        else:
            self.dic_editor[u"loss排列方式"].setCurrentIndex(0)
            self.dic_editor[u"loss排列方式"].setEnabled(True)            
    
    def setTableModifyStatus(self):
        if self.sender().isChecked():
            self.tableWidget1.setEnabled(True)
            self.tableWidget2.setEnabled(True)
        else:
            self.tableWidget1.setEnabled(False)
            self.tableWidget2.setEnabled(False)
            
    def setMainUIstyle(self):#设置风格
        file = QtCore.QFile(':/pic/fblue.qss')
        file.open(QtCore.QFile.ReadOnly)
        styleSheet = file.readAll()
        styleSheet = unicode(styleSheet, encoding='gb2312')
        QtGui.qApp.setStyleSheet(styleSheet)
        
    def setValue(self):
        res = 0
        if os.path.exists(smk_info):
            with open(smk_info) as file_obj:
                self.dic_hct_info = json.load(file_obj)

            for key, value in self.dic_editor.iteritems():
                if self.dic_hct_info.get(key):		    
                    if isinstance(self.dic_editor[key], QtGui.QLineEdit):
                        if isinstance(self.dic_hct_info[key], float):
                            self.dic_editor[key].setText("%s" % self.dic_hct_info[key])
                        else:
                            self.dic_editor[key].setText(self.dic_hct_info[key])
                    elif isinstance(self.dic_editor[key], QtGui.QComboBox):
                        pos = self.dic_editor[key].findText(
                            self.dic_hct_info[key], QtCore.Qt.MatchExactly)
                        self.dic_editor[key].setCurrentIndex(pos)
                        
            if self.dic_hct_info.get(u"最小孔径"):
                self.set_model_data(self.tableWidget1, self.dic_hct_info[u"最小孔径"])
            else:
                res += 1
                
            if self.dic_hct_info.get(u"阻抗及补偿信息"):
                self.set_model_data(self.tableWidget2, self.dic_hct_info[u"阻抗及补偿信息"])
            else:
                res += 1
        else:
            res = 1
                
        return res
        
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
               
        arraylist = [ u"测试孔",
                      u"测试定位孔",
                      u"测试护卫孔",
                      u"外围孔",
                      u"分布孔",
                      u"端头线粗",
                      u"最大频率"
                      ]        
        
        for key in arraylist:
            if self.dic_item_value.has_key(key):
                try:
                    self.dic_item_value[key] = float(self.dic_item_value[key])
                except:
                    QtGui.QMessageBox.information(self, u'提示', u'检测到 %s 参数[ %s ]为空或非法数字,请检查~' % (
                        key, self.dic_item_value[key]), 1)
                    # self.show()
                    return 0

        #if self.dic_item_value[u"二维码面次"] == "":
            #QtGui.QMessageBox.information(self, u'提示', u'检测到 二维码面次 为空,请选择C面或S面,请检查~', 1)
            #return 0       
        
        self.dic_item_value[u"最小孔径"] = []
        model = self.tableWidget1.model()
        for row in range(model.rowCount()):
            arraylist = []
            for col in range(model.columnCount()):
                value = str(model.item(row, col).text())
                if col <> 0:
                    try:
                        float(value)
                    except:
                        QtGui.QMessageBox.information(self, u'提示', u'检测到 %s 最小孔 有参数[ %s ]为空或非法数字,请检查~' % (
                            model.item(row, 0).text(), value), 1)
                        return 0
                arraylist.append(value)
                
            self.dic_item_value[u"最小孔径"].append(arraylist)
        
        self.parm["Alldrill_small_hole"] = self.dic_item_value[u"最小孔径"]
            
        self.dic_item_value[u"阻抗及补偿信息"] = []
        model = self.tableWidget2.model()
        for row in range(model.rowCount()):
            arraylist = []
            for col in range(model.columnCount()):
                value = str(model.item(row, col).text())
                arraylist.append(value)
                
            self.dic_item_value[u"阻抗及补偿信息"].append(arraylist)             

        #with open(smk_info, 'w') as file_obj:
            #json.dump(self.dic_item_value, file_obj)

        return 1

    def get_InPlan_info(self):
        """
        从InPlan查询相关信息
        :return:
        :rtype:
        """
        # --连接InPlan并查询相关数据
        self.InPlan = InPlan(self.JOB)
        self.ERP=ERP()
        self.Custmer=self.ERP.GetcuserJob(self.JOB.split("-")[0])
        self.get_ERP_stackup=self.ERP.get_ERP_stackup(self.JOB.split("-")[0])
        self.sqlDic = self.InPlan.get_REQUIRED_CU_WEIGHT_and_LAYER_ORIENTATION()
        # self.CuThickHole = self.InPlan.get_hole_wall_thickness()
        # self.layerMode, self.core_thick = self.InPlan.get_Layer_Mode()
        self.CU_WEIGHT, self.FINISH_THICKNESS = self.convert_layer_thick()
        self.impDict = self.InPlan.get_diff_imp()
        # self.flow_content = self.InPlan.get_flow_type()
        self.bd_info = self.InPlan.get_bd_info()
        self.erp_bd_info=self.ERP.GetERPBZ(self.JOB[:13])
        # om_sort = sorted(list(set([str(x['成品阻抗']) for x in self.impDict])), key=lambda x: float(x))
        # for l in [''] + om_sort: self.ui.comboBox_om.addItem(l)
        if len(self.bd_info) > 0:
            self.is_back_drill = True
        else:
            self.is_back_drill = False
        self.parm['customer'] = self.Custmer
    def addPart_Ui(self, impDict=None):
        """
        在原框架基础上继续加载窗体
        :return:None
        """
        # --加载动态层列表
        if impDict is None:
            impDict = self.impDict
        sqlDic = self.sqlDic
        # --当从InPlan中未获取到参数时
        if len(sqlDic) == 0:
            msg_box = msgBox()
            msg_box.critical(self, '警告', 'Inplan数据库中没有料号:%s的铜厚数据，无法确定补偿值！' % self.JOB, QMessageBox.Ok)
            # sys.exit()
        if len(impDict) == 0:
            msg_box = msgBox()
            msg_box.critical(self, '警告', 'Inplan数据库中没有料号:%s的差分阻抗数据，程序无法执行！' % self.JOB, QMessageBox.Ok)
            # sys.exit()

        # --取出测试层2
        allDict = []
        for rowDir in impDict:
            #layName2 = rowDir['测试层2']
            #refers2 = rowDir['参考层2']
            #if layName2 is not None:
                #layDict = dict(rowDir)
                #layDict['测试层1'] = layName2
                #layDict['参考层1'] = refers2
                #allDict.append(rowDir)
                #allDict.append(layDict)
            #else:
            allDict.append(rowDir)

        # --以层别名进行排序
        allDict = sorted(allDict, key=lambda layDict: int(str(layDict['测试层1'])[1:]))
        # --重新定义行数
        self.ui.tableWidget.setRowCount(len(allDict))
        # --样式（背景色）
        brush_bg = QtGui.QBrush(QtGui.QColor(253, 199, 77))
        brush_bg.setStyle(QtCore.Qt.SolidPattern)

        # --设定QTableWidget各列的宽度
        tableRowWidth = [85, 85, 85, 80, 85, 85, 85, 85, 80]
        for rr in range(len(tableRowWidth)):
            self.ui.tableWidget.setColumnWidth(rr, tableRowWidth[rr])

        # --循环所有层并加入行
        # infoList = []
        for rowDir in allDict:
            # --获取数组序号
            rowNum = allDict.index(rowDir)
            # --获取层名
            layName = rowDir['测试层1']
            layName = layName.lower()
            # --获取原稿线宽
            org_width = float(rowDir['成品线宽'])
            # --获取补偿值
            # compensate = self.get_compensate(layName)
            compensate = 0
            # --获取菲林线宽
            line_width = org_width + compensate
            # --获取原稿间距
            try:
                org_space = float(rowDir['成品线距'])
                # --获取菲林间距
                line_space = org_space - compensate
            except TypeError:
                org_space = None
                # --获取菲林间距
                line_space = None
            ###获取到铜皮
            l2cu =rowDir['到铜皮间距']
            try:
                l2cu=str(float(l2cu)-compensate)
            except :
                l2cu=rowDir['到铜皮间距']
            # --获取参考层
            refers = rowDir['参考层1']
            refers = refers.lower().split('&')
            if len(refers) == 1:
                refers.append('None')
            # --获取欧姆值
            ohms = str(rowDir['成品阻抗'])
            # --层别列：
            item = QtGui.QTableWidgetItem()
            self.table_Item(item, layName, rowNum=rowNum, colNum=0, brush_bg=brush_bg)
            # --线宽列
            item = QtGui.QTableWidgetItem()
            self.table_Item(item, str(line_width), rowNum=rowNum, colNum=1)
            # --间距列
            if line_space is None:line_space='/'
            item = QtGui.QTableWidgetItem()
            self.table_Item(item, str(line_space), rowNum=rowNum, colNum=2)
            ###到铜皮
            if l2cu is None: l2cu = '/'
            item = QtGui.QTableWidgetItem()
            self.table_Item(item, l2cu, rowNum=rowNum, colNum=3)
            # --参考1
            item = QtGui.QTableWidgetItem()
            if refers[0] is None: refers[0] = '/'
            self.table_Item(item, refers[0], rowNum=rowNum, colNum=4)
            # --参考2
            item = QtGui.QTableWidgetItem()
            if refers[1] == 'None' or refers[1] is None : refers[1] = '/'
            self.table_Item(item, refers[1], rowNum=rowNum, colNum=5)
            # --原稿线宽
            item = QtGui.QTableWidgetItem()
            self.table_Item(item, str(org_width), rowNum=rowNum, colNum=6)
            # --原稿间距
            item = QtGui.QTableWidgetItem()
            if org_space is None: org_space = '/'
            self.table_Item(item, str(org_space), rowNum=rowNum, colNum=7)
            ###原稿到铜
            origl2cu=rowDir['到铜皮间距']
            item = QtGui.QTableWidgetItem()
            if origl2cu is None: origl2cu = '/'
            self.table_Item(item, str(origl2cu), rowNum=rowNum, colNum=8)
            # --欧姆值
            item = QtGui.QTableWidgetItem()
            self.table_Item(item, ohms, rowNum=rowNum, colNum=9)
            # --补偿值
            item = QtGui.QTableWidgetItem()
            self.table_Item(item, str(compensate), rowNum=rowNum, colNum=10)
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)

    def set_UI_by_JOB(self):
        self.label_job = "JOB: " + self.JOB
        self.label_step = "step: " + self.STEP if self.STEP else ''
        self.ui.label_2.setText(u"系统信息：机台：%s|用户：%s|时间:%s" % (os.popen('hostname').read().strip(), getpass.getuser(),QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')))
        self.ui.timer = QTimer(self)
        self.ui.timer.timeout.connect(self.updateTime)
        self.ui.timer.start(1000)  # 更新时间间隔为1秒

        self.testSize='200'
        self.testDw='1600'
        self.viaTilt_hw='200'
        self.out_linehole='250'
        self.fenbuhole='200'
        self.dwhole='2000'
        self.dtx_size='150'

        for child in self.findChildren(QLineEdit):child.setEnabled(False)

    def updateTime(self):

        self.ui.label_2.setText(u"系统信息：机台：%s|用户：%s|时间:%s" % (os.popen('hostname').read().strip(), getpass.getuser(),
                                                             QDateTime.currentDateTime().toString(
                                                                 'yyyy-MM-dd hh:mm:ss')))

    def slot_func(self):
        self.ui.comboBox_om.currentIndexChanged.connect(self.on_comboBox_changed)
        # --定义执行按钮的信号、槽连接
        self.connect(self.ui.create_btn, QtCore.SIGNAL("clicked()"), self.clickApply)
        # --QTableWidgetItem变更
        self.connect(self.ui.tableWidget, QtCore.SIGNAL("cellChanged(int, int)"), self.On_cellChange)
        # --安装事件过滤器，达到禁用QComboBox滚轮事件的目的

        self.ui.comboBox_om.installEventFilter(self)

    def On_cellChange(self):
        """
        补偿值列编辑后，更新tableWidget
        :return:
        :rtype:
        """
        # --先断开信号的连接,以免在下面再次修改item时发生递归死循环事件发生
        self.disconnect(self.ui.tableWidget, QtCore.SIGNAL("cellChanged(int, int)"), self.On_cellChange)
        # --获取选中的物件，若没有选中直接return
        items = self.ui.tableWidget.selectedItems()
        if len(items) == 0:
            # --退出前，再次启动信号连接
            self.connect(self.ui.tableWidget, QtCore.SIGNAL("cellChanged(int, int)"), self.On_cellChange)
            return
        # --获取选中的行信息，行号，列号
        selRow = items[0].row()
        selCol = 10
        item_text = self.ui.tableWidget.item(selRow, selCol).text()
        # --获取选择行的补偿信息
        try:
            finishComp = float(item_text)
            if finishComp < 0:
                msg_box = msgBox()
                msg_box.critical(self, '警告', '第%d行%d列 补偿值 %s 不是正数，请修改!' % (selRow + 1, selCol + 1, item_text),
                                 QMessageBox.Ok)
                self.ui.tableWidget.item(selRow, selCol).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                self.connect(self.ui.tableWidget, QtCore.SIGNAL("cellChanged(int, int)"), self.On_cellChange)
                return False
            # --重新更新UI数据
            self.refreshTableWidget(selRow, finishComp)
        except ValueError:
            msg_box = msgBox()
            msg_box.critical(self, '警告', '第%d行%d列 补偿值 %s 不是有效数字，请修改!' % (selRow + 1, selCol + 1, item_text),
                             QMessageBox.Ok)
            self.ui.tableWidget.item(selRow, selCol).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
            # --退出前，再次启动信号连接
            self.connect(self.ui.tableWidget, QtCore.SIGNAL("cellChanged(int, int)"), self.On_cellChange)
            return False
        # --退出前，再次启动信号连接
        self.connect(self.ui.tableWidget, QtCore.SIGNAL("cellChanged(int, int)"), self.On_cellChange)

    def convert_layer_thick(self):
        """
        生成层别:铜厚的字典
        :return:
        :rtype:
        """
        CU_WEIGHT = dict()
        FINISH_THICKNESS = dict()
        for line_dict in self.sqlDic:
            layer_name = line_dict['LAYER_NAME']
            cu_weight = float(line_dict['CU_WEIGHT'])
            finish_thickness = float(line_dict['FINISH_THICKNESS'])
            CU_WEIGHT[layer_name] = cu_weight
            FINISH_THICKNESS[layer_name] = finish_thickness
        return CU_WEIGHT,FINISH_THICKNESS

    def get_compensate(self, layer, compType='Line'):
        """
        传入层别，获取补偿值
        :param layer: 层名
        :param compType: 补偿类型（Line | Pad）
        :return: float
        """

        if layer in self.layerMode['inn']:
            loopList = self.matchComp[u'内层补偿']
        elif layer in self.layerMode['sec']:
            loopList = self.matchComp[u'次外层补偿']
        elif layer in self.layerMode['out']:
            loopList = self.matchComp[u'外层补偿']
        else:
            loopList = self.matchComp

        if compType == 'Line':
            compensate = self.getCompensate_Line(layer, loopList)
        else:
            compensate = self.getCompensate_Pad(layer, loopList)
        return compensate

    def getCompensate_Line(self, layeyKey, loopCompList):
        """
        循环并获取线的补偿数据（用户阻抗线的补偿）
        :param layeyKey: 层名
        :return: float
        """
        layeyKey = layeyKey.upper()
        compMax = 0

        for layDict in loopCompList:
            if layeyKey in layDict.keys():
                # --循环等级，取出最大的一个补偿（按大的补偿）
                for level in layDict[layeyKey].keys():
                    if layeyKey.lower() in self.layerMode['inn']:
                        if layDict[layeyKey][level][u'稀疏区'] > compMax:
                            compMax = layDict[layeyKey][level][u'稀疏区']
                    else:
                        # 正片，且不是次外层
                        if self.getFlow == u'正片' and layeyKey.lower() not in self.layerMode['sec']:
                            if layDict[layeyKey][level][u'稀疏区'] > compMax:
                                compMax = layDict[layeyKey][level][u'稀疏区']
                        else:
                            if layDict[layeyKey][level][u'基础补偿'] > compMax:
                                compMax = layDict[layeyKey][level][u'基础补偿']

                return compMax
                break
        return 0

    def getCompensate_Pad(self, layeyKey, loopCompList):
        """
        循环并获取Pad的补偿数据(用于外层pad补偿）
        :param layeyKey: 层名
        :return: float
        """
        layeyKey = layeyKey.upper()
        compMax = 0
        for layDict in loopCompList:
            if layeyKey in layDict.keys():
                # --循环等级，取出最大的一个补偿（按大的补偿）
                for level in layDict[layeyKey].keys():
                    # 正片，且不是次外层
                    if self.getFlow == u'正片' and layeyKey.lower() not in self.layerMode['sec']:
                        if layDict[layeyKey][level][u'线路开窗Pad'] > compMax:
                            compMax = layDict[layeyKey][level][u'线路开窗Pad']
                    else:
                        if layDict[layeyKey][level][u'SMD小于等于12补偿'] > compMax:
                            compMax = layDict[layeyKey][level][u'SMD小于等于12补偿']
                # return u'匹配到的值不唯一'
                return compMax
                break
        return 0

    def table_Item(self, obj, text, rowNum=None, colNum=None, foreColor='black', brush_bg=None):
        """
        在tableWidget中加入普通的item控件
        :param obj: 控件引用
        :param text: 控件上的文本
        :param rowNum: 传入需要放置的行号
        :param colNum: 传入需要放置的列号
        :param foreColor: 传入前景颜色
        :param brush_bg: 传入背景画刷
        :return:
        """
        if text == '/':
            brush_bg=QColor(220, 220, 220)
        # --设置tabWidgetItem控件不可编辑
        obj.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        # --位置
        self.ui.tableWidget.setItem(rowNum, colNum, obj)
        # --设置文字居中
        obj.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter)
        # --写入文本信息
        obj.setText(text)
        if brush_bg:
            # --如果传入的参数有指定背景刷，则设定背景
            obj.setBackground(brush_bg)
        # --根据传入的颜色设置样式（前景色）
        brush = QtGui.QBrush(QtGui.QColor(foreColor))
        brush.setStyle(QtCore.Qt.NoBrush)
        obj.setForeground(brush)

    def on_comboBox_changed(self):
        sender=self.sender()
        om=str(sender.currentText())
        if not om :
            new_dic=self.impDict
        else:
            new_dic=[x for x in self.impDict if str(x['成品阻抗']) == om ]
        self.addPart_Ui(new_dic)

    #def eventFilter(self,watched,event):
        #"""
        #事件过滤器
        #:param watched:
        #:type watched:
        #:param event:
        #:type event:
        #:return:
        #:rtype:
        #"""
        #if watched in [self.ui.comboBox_om]:
            #if event.type() == QEvent.Wheel:
                ## --拦截事件，不再发送到原来的控件,返回True,继续返回原控件返回False
                #return True
        ## --其它未拦截事件仍然返回原控件
        #return False

    def get_table_widget_info(self):
        """
        从tableWidget中获取信息
        :return:
        :rtype:
        """
        infoList = []
        infoAll = []
        ohmsList = []
        selList = []
        reRowList = []

        ## --TODO 如果没有选中层别，则默认选中所有层别,运用生成器表达式，节省内存
        #selItems = self.ui.tableWidget.selectedItems()
        #items = (self.ui.tableWidget.item(row, 0) for row in range(self.ui.tableWidget.rowCount()))
        #for selObj in items:
            ## --获取选中的行selRow
            #selRow = selObj.row()
            #selCol = selObj.column()
            ## --层别列
            #item = self.ui.tableWidget.item(selRow, 0)
            #layer = str(item.text())
            ## --线宽列
            #item = self.ui.tableWidget.item(selRow, 1)
            #line_width = float(item.text())
            ## --间距列

            #item = self.ui.tableWidget.item(selRow, 2)

            #try:
                #line_space = float(item.text())
            #except ValueError:
                #line_space = 0
            #####到铜皮
            #item = self.ui.tableWidget.item(selRow, 3)
            #try:
                #l2Cu = float(item.text())
            #except ValueError:
                #l2Cu = 0
            ## --参考1
            #item = self.ui.tableWidget.item(selRow, 4)
            #refer1 = str(item.text())
            ## --参考2
            #item = self.ui.tableWidget.item(selRow, 5)
            #refer2 = str(item.text())
            ## --原稿线宽
            #item = self.ui.tableWidget.item(selRow, 6)
            #org_width = float(item.text())
            ## --原稿间距
            #item = self.ui.tableWidget.item(selRow, 7)
            #try:
                #org_space = float(item.text())
            #except ValueError:
                #org_space = 0
            ##原稿到铜
            #item = self.ui.tableWidget.item(selRow, 8)
            #try:
                #org2cu = float(item.text())
            #except ValueError:
                #org2cu = 0
            ## --欧姆值
            #item = self.ui.tableWidget.item(selRow, 9)
            #ohms = float(item.text())
            #if ohms not in ohmsList:
                #ohmsList.append(ohms)
            ## --补偿值
            #item = self.ui.tableWidget.item(selRow, 10)
            #item = self.ui.tableWidget.item(selRow, 10)
            #compensate = float(item.text())
            #layDict = {
                #'layer': layer,
                #'line_width': line_width,
                #'line_space': line_space,
                #'l2Cu': l2Cu,
                #'refer1': refer1,
                #'refer2': refer2,
                #'org_width': org_width,
                #'org_space': org_space,
                #'org2cu':org2cu,
                #'ohms': ohms,
                #'compensate': compensate,
            #}
            #if selObj.isSelected() or len(selItems) == 0:
                #infoList.append(layDict)
            ## --所有阻抗信息存入一个列表
            #infoAll.append(layDict)

        ## --将infoAll赋值到impAll
        #self.parm['impAll'] = infoAll
        ## --为节省空间，尽量错开同一层别不同走线,对阻抗信息进行重排
        #for ohms in ohmsList:
            #for layDict in infoList:
                #ohms_ = layDict['ohms']
                #if ohms_ == ohms:
                    #selList.append(layDict)

        ## --若有相邻走线层，需要错开
        #reRowList = self.insert_adjacent(selList)
        self.parm['adjacent_layer'] = []
        
        dic_array_info = {}
        for info in self.dic_item_value[u"阻抗及补偿信息"]:
            # if info[0] == "1":
            if not dic_array_info.has_key(info[1]):                    
                dic_array_info[info[1]] = [info]
            else:
                dic_array_info[info[1]].append(info)            
            
        for key, values in dic_array_info.iteritems():
            
            infoList = []
            ohmsList = []
            selList = []
            
            for array_info in values:
                ohms = float(array_info[11])
                if ohms not in ohmsList:
                    ohmsList.append(ohms)
                layer, line_width, line_space, l2Cu, refer1, refer2, org_width, org_space, org2cu, ohms = array_info[2:12]
                if refer1 == "None":
                    refer1 = str(refer2.lower())
                    refer2 = "None"
                    
                layDict = {
                    'layer': layer.lower(),
                    'line_width': float(line_width),
                    'line_space': float(line_space),
                    'l2Cu': float(l2Cu),
                    'refer1': refer1.lower() if refer1 != "None" else "/",
                    'refer2': refer2.lower() if refer2 != "None" else "/",
                    'org_width': float(org_width),
                    'org_space': float(org_space),
                    'org2cu': float(org2cu),
                    'ohms': float(ohms),
                    'compensate': 0,
                }
                if str(array_info[0]) == "1":
                    infoList.append(layDict)
                    
                infoAll.append(layDict)

            # --为节省空间，尽量错开同一层别不同走线,对阻抗信息进行重排
            for ohms in ohmsList:
                for layDict in infoList:
                    ohms_ = layDict['ohms']
                    if ohms_ == ohms:
                        selList.append(layDict)
    
            # --若有相邻走线层，需要错开
            reRowList += self.insert_adjacent(selList)
        
        # --将infoAll赋值到impAll
        self.parm['impAll'] = infoAll
        return reRowList

    def insert_adjacent(self, selList):
        """
        在相邻层之间插入其它层，以错开相邻层
        :return:
        :rtype:
        """
        # --相邻走线层中间错开
        pre_refer1 = None
        pre_refer2 = None
        pre_dict = None
        outer = ['l1', 'l%s' % self.layer_number]
        insert_list = []
        before_list = []
        after_list = []
        for count, layDict in enumerate(selList):
            layer = layDict['layer']
            refer1 = layDict['refer1']
            refer2 = layDict['refer2']
            if layer in [pre_refer1, pre_refer2]:
                insert_list = [pre_dict, layDict]
                before_list = selList[:count - 1]
                if count < len(selList) - 1:
                    after_list = selList[count + 1:]
            pre_refer1 = refer1
            pre_refer2 = refer2
            pre_dict = layDict

        # --相邻层存入parm,后续常用
        self.parm['adjacent_layer'] = [layerDict['layer'] for layerDict in insert_list]
        if len(insert_list):
            insert_flag = True
            # --插入相邻层时，先不考虑外层
            for layDict in after_list:
                after_layer = layDict['layer']
                if after_layer not in outer and insert_flag:
                    insert_list.insert(1, layDict)
                    after_list.remove(layDict)
                    insert_flag = False
                    break
            for layDict in reversed(before_list):
                before_layer = layDict['layer']
                if before_layer not in outer and insert_flag:
                    insert_list.insert(1, layDict)
                    before_list.remove(layDict)
                    insert_flag = False
                    break
            # --若有没内层可以插入，才考虑外层
            if insert_flag:
                for layDict in after_list:
                    if insert_flag:
                        insert_list.insert(1, layDict)
                        insert_flag = False
                    else:
                        insert_list.append(layDict)
                for layDict in reversed(before_list):
                    if insert_flag:
                        insert_list.insert(1, layDict)
                        insert_flag = False
                    else:
                        insert_list.insert(0, layDict)
            else:
                # --列表拼接
                insert_list = before_list + insert_list + after_list
            return insert_list
        else:
            # --没有相邻层，直接返回原列表
            return selList

    def get_UI_info(self):
        '''
        从window界面TabWidget控件中获取所有参数
        :return:
        '''
        # 界面关闭前，参数不再变化，统一从界面获取参数并存入字典
        
        self.testSize=self.dic_item_value[u"测试孔"]
        self.testDw=self.dic_item_value[u"测试定位孔"]
        self.viaTilt_hw=self.dic_item_value[u"测试护卫孔"]
        self.out_linehole=self.dic_item_value[u"外围孔"]
        self.fenbuhole=self.dic_item_value[u"分布孔"]
        self.dwhole=self.dic_item_value[u"定位孔"]
        self.dtx_size=self.dic_item_value[u"端头线粗"]
        self.frequency = self.dic_item_value[u"最大频率"]
        
        self.bd_layer_list=[l for l in self.GEN.GET_ATTR_LAYER('all') if re.search('^bd(\d+)-(\d+)$', l)]        

        self.parm['testSize'] = float(self.testSize)
        self.parm['testDw'] = float(self.testDw)
        self.parm['viaTilt_hw'] = float(self.viaTilt_hw)
        self.parm['out_linehole'] = float(self.out_linehole)
        self.parm['fenbuhole'] = float(self.fenbuhole)
        self.parm['dwhole'] = float(self.dwhole)
        self.parm['frequency']=float(self.frequency)
        self.parm['dtx_size'] = float(self.dtx_size)
        self.impList = self.get_table_widget_info()
        self.parm['impList'] = self.impList

        self.parm['is_back_drill'] = self.is_back_drill
        self.parm['layer_number'] = self.layer_number
        self.parm['ERP_STACKUP'] = self.get_ERP_stackup
        self.parm['layer_info'] = self.sqlDic
        self.parm['customer'] = str(self.dic_item_value[u"客户型号"])
        self.parm['bd_info'] = self.bd_info
        self.parm['erp_bd_info'] = self.erp_bd_info
        self.parm['bd_layer_list'] =self.bd_layer_list

    def clickApply(self):
        # self.setCursor(Qt.WaitCursor)
        # --检查界面参数
        #param_ret = self.check_parameter()
        ## --检查参数后再关闭主界面
        #if param_ret:
        # --关闭主界面前从UI界面取值
        res = self.get_item_value()
        if not res:
            return
        
        self.get_UI_info()
        # self.close()
        self.run()
        #else:
            ## --还原光标为normal状态
            #self.setCursor(Qt.ArrowCursor)
            
        sys.exit(0)

    def check_parameter(self):
        return True

    def run(self):
        # try:
        json_string = json.dumps(self.parm, ensure_ascii=False, indent=4, separators=(', ', ': '), sort_keys=True)
        loss = MakeLossExcute.Loss(job_name=self.JOB, step_name=self.STEP, json_data=FrozenJSON(json.loads(json_string,encoding='utf8')),json_dic=self.parm)
        loss.run()
        #except Exception as e:
            #msg_box = msgBox()
            #msg_box.critical(self, u'错误', u'运行中有错误抛出:<<%s>>'  % str(e), Qt.QMessageBox.Ok)
            #import traceback
            #traceback.print_exc()
            #sys.exit()
if __name__ == '__main__':
    # app = QtGui.QApplication(sys.argv)
    myapp = MainWindow()
    myapp.resize(970, 800)
    myapp.setFixedSize(myapp.width(), myapp.height())
    myapp.show()

    app.exec_()
    sys.exit(0)