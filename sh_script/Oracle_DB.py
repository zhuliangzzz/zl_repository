#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VGT.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    LiuChuang
# @Mail         :    Chuang_cs@163.com
# @Date         :    2019/01/15
# @Revision     :    1.4
# @File         :    Oracle_DB.py
# @Software     :    PyCharm
# @Usefor       :    Oracle连接等操作
# ---------------------------------------------------------#

_header = {
    'description': '''
    -> 本程序主要服务于胜宏科技（惠州），任何其他团体或个人如需使用，必须经胜宏科技（惠州）相关负责
       人及作者的批准，并遵守以下约定；
    1> 本着尊重创作者的劳动成果，任何团体或个人在使用此程序的时候，均需要知会此程序的原始创作者；
    2> 在任何场合宣导、宣传，在任何文件、报告、邮件中提及本程序的全部或部分功能，均需要声明此程序的
       原始创作者；
    3> 在任何时候对本程序做部分修改或者是升级时，必须要保留文件的原始信息，包括原始文件名、创作者及
       联系方式、创作日期等信息，且不得删除程序中的源代码，只能进行注释处理；'''
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

# --导入Package
import os
import platform
import re

import cx_Oracle

os.environ["NLS_LANG"]='AMERICAN_AMERICA.UTF8'


def rows_as_dicts(cursor):
    """
    转换为字典
    :param cursor:
    :return:
    """
    col_names = [i[0] for i in cursor.description]
    return [dict(zip(col_names, row)) for row in cursor]


# --公用的Class
class ORACLE_INIT:
    # ("172.20.218.253", "topprod", '1521', 'hdigc', 'hdigc')
    __config = {
        'host': "172.20.218.247",
        'port': 1521,
        'username': "zygc",
        'password': "ZYGC@2019",
        'database': "EngTechnology",
        'serName' : 'topprod',
        'charset': "utf8"
    }

    def __init__(self, file = None, tnsName = 'service_name'):
        # --获取系统类型返回结果“Windows” or "Linux"
        self.dbc = None
        self.tns = None
        self.tnsName = tnsName
        self.system = platform.system()
        self.logFile = file

    # --连接Oracle数据库
    def DB_CONNECT(self, host=__config['host'], servername=__config['serName'],
                   port=__config['port'], username=__config['username'], passwd=__config['password'], dbName=None):
        """
        Oracle数据库连接
        :param dbName: 数据库的名称分类（HDI_INPLAN|MLB_INPLFN|ERP|QUERA）
        :param servername: 服务名
        :param prod: 端口号
        :param username: 登录用户名
        :param passwd: 登录用户密码
        :return: 登录结果
        """
        # --根据dbName匹配对应的参数
        if dbName is not None: (host, servername, port, username, passwd) = self.getParameter(dbName)

        try:
            if self.tnsName == 'service_name':
                self.tns = cx_Oracle.makedsn(host, port, service_name=servername)
                self.dbc = cx_Oracle.connect(username, passwd, self.tns)
            else:
                self.tns = cx_Oracle.makedsn(host, port, sid=servername)
                self.dbc = cx_Oracle.connect(username, passwd, self.tns)
            # print("数据库（%s）连接成功！" % servername)
            self.LOG("Oracle db connection successfull ! Host:%s " % host)
        except Exception as e:
            # print("Error：数据库连接失败！")
            self.LOG("Oracle db connection failed ! Host:%s(%s)" % (host, e))
            return None

        # --返回链接
        return self.dbc

    # --关闭Oracle
    def DB_CLOSE(self,dbc):
        """
        关闭数据库连接
        :param dbc: 连接的信号
        :return: None
        """
        self.dbc=dbc
        # --关闭数据库
        self.dbc.close()

    # --执行SQL语句
    def SQL_EXECUTE(self, dbc, sql):
        """
        执行传入的SQL语句，并返回相关信息
        :param dbc: 连接的信号
        :param sql: 查询的SQL语句
        :return: 当为select开头的SQL时，会有对应的返回数据
         当为其它需要提交的SQL时，刚仅返回True or False
        """

        # --定义匹配规则(re.I不区分大小写)
        match_sql = re.compile(r'^(\s+)?(\n+)?select', re.I)
        m = match_sql.search(sql)
        # --执行sql语句
        cursor = dbc.cursor()
        cursor.execute(sql)
        # --记录更新的SQL列表
        try:
            self.LOG(sql)
        except:
            print (sql)

        # --当匹配通过时（以select开头，并无大小写区分）
        if m:
            try:
                sql_info = cursor.fetchall()
                # --返回数据
                return sql_info
            except:
                return False
        else:
            try:
                dbc.commit()
                return True
            except:
                return False

    def SELECT_DIC(self, dbc, sql):
        """
        使用键值对的方法，由键名字来获取数据，只接收Select开头的sql
        :param dbc:连接的信号
        :param sql:查询的SQL语句
        :return:以栏位名为key的字典
        """

        # --定义匹配规则(re.I不区分大小写)
        match_sql = re.compile(r'^(\s+)?(\n+)?select', re.I)
        m = match_sql.search(sql)
        # --执行sql语句
        cursor = dbc.cursor()
        cursor.execute(sql)
        # --记录更新的SQL列表
        try:
            self.LOG(sql)
        except:
            print (sql)

        # --当匹配通过时（以select开头，并无大小写区分）
        if m:
            try:
                data = rows_as_dicts(cursor)
                # --返回数据
                return data
            except:
                return False
        else:
            try:
                dbc.commit()
                return True
            except:
                return False

    # --记录日志
    def LOG(self, log_msg):
        """
        记录日志文件至tmp盘
        :param log_msg: 传入的日志信息
        :return: None
        """
        import time
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

        # --开始执行转换
        try:
            log_msg = (str(now_time) + ":" + log_msg)
        except:
            log_msg = log_msg
        # --打印Log
        print(log_msg)

        # --是否打印至文本
        if self.logFile is not None:
            f = open(self.logFile, 'a')
            f.write(log_msg + '\n')
            f.close()

    def getParameter(self, dbName):
        """
        获取DB对应参数
        :param dbName:数据库分类
        :return:None
        """
        if dbName == 'MLB_INPLAN':
            return '192.168.2.18', 'inmind.fls', '1521', 'GETDATA', 'InplanAdmin'
        elif dbName == 'HDI_INPLAN':
            return '172.20.218.193', 'inmind.fls', '1521', 'GETDATA', 'InplanAdmin'
        elif dbName == 'ERP':
            return '172.20.218.247', 'topprod', '1521', 'zygc', 'ZYGC@2019'
        elif dbName == 'QUERA':
            return '192.168.2.106', 'xe', '1521', 'system', '-apollo-'

    def getJobData(self,dbc,strJOB):
        sql = """select a.item_name 料号名,
               d.customer_name 客户名,
               c.customer_job_name_ 客户品名,
               h.value 工厂,
               i.value 订单类型,
               j.value 出货方式,
               round(c.delivery_width_ / 39.37, 3) 出货尺寸宽,
               round(c.delivery_length_ / 39.37, 3) 出货尺寸长,
               round(f.customer_thickness / 39.37,3) 成品板厚,
               k.value  表面处理,
               l.value 阻焊次数,
               m.value 阻焊面别,
               (select enu.value
                from vgt_hdi.items sm   
               inner join vgt_hdi.mask_layer sm2
                  on sm.item_id = sm2.item_id
                 and sm.last_checked_in_rev = sm2.revision_id
               inner join vgt_hdi.mask_layer_da sm3
                  on sm2.item_id = sm3.item_id
                 and sm2.revision_id = sm3.revision_id
               inner join vgt_hdi.enum_values enu
                  on sm3.sm_color_ = enu.enum
               where sm.root_id = a.root_id
                 and sm2.mask_type = 0
                 and enu.enum_type = 214
                 and enu.value is not null
                 and rownum = 1) 阻焊颜色,
               n.value 字符次数,
               o.value 字符面别,
               (select enu.value
                  from vgt_hdi.items ss   
                 inner join vgt_hdi.mask_layer ss2
                    on ss.item_id = ss2.item_id
                   and ss.last_checked_in_rev = ss2.revision_id
                 inner join vgt_hdi.mask_layer_da ss3
                    on ss2.item_id = ss3.item_id
                   and ss2.revision_id = ss3.revision_id
                 inner join vgt_hdi.enum_values enu
                    on ss3.ss_color_ = enu.enum
                 where ss.root_id = a.root_id
                   and ss2.mask_type = 2
                   and enu.enum_type = 1025
                   and enu.value is not null
                   and rownum = 1) 字符颜色,
                  decode(c.has_qr_code_,0,'无',1,'有') 是否有雷雕,
                  round(g.pcb_size_x/39.37,3) PCS_X,
                  round(g.pcb_size_y/39.37,3) PSC_Y,
                  round(c.set_size_x_/39.37,3) SET_X,
                  round(c.set_size_y_/39.37,3) SET_Y,
                  b.num_arrays PNL中的Set数,
                  c.pcs_per_set_ SET中的Pcs数,
                  p.value 周期面别,
                  q.value 周期格式,
                  r.value 大板Vcut,
                  s.value UL面别,
                  t.value UL标记,
                  c.es_elic_,
       decode(c.sm_plug_type_,0,'否',1,'否',2,'是',3,'是')  是否阻焊塞,
       (select decode(proda.resin_plug_type_,0,'否',1,'否',2,'是')
           from vgt_hdi.public_items pb
           inner join vgt_hdi.process pro
              on pb.item_id = pro.item_id
             and pb.revision_id = pro.revision_id
           inner join vgt_hdi.process_da proda
              on pro.item_id = proda.item_id
             and pro.revision_id = proda.revision_id
           where pb.root_id = a.root_id
             and pro.proc_subtype = 29)  是否树脂塞
          from vgt_hdi.items a
         inner join vgt_hdi.job b
            on a.item_id = b.item_id
           and a.last_checked_in_rev = b.revision_id
         inner join vgt_hdi.job_da c
            on b.item_id = c.item_id
           and b.revision_id = c.revision_id
         inner join vgt_hdi.customer d
            on b.customer_id = d.cust_id
         inner join vgt_hdi.items e
            on a.root_id = e.root_id
         inner join vgt_hdi.stackup f
            on e.item_id = f.item_id
           and e.last_checked_in_rev = f.revision_id
         inner join vgt_hdi.part g
            on b.item_id = g.item_id
           and b.revision_id = g.revision_id
         inner join vgt_hdi.enum_values h
            on c.site_ = h.enum
         inner join vgt_hdi.enum_values i
            on c.order_type_ = i.enum
         inner join vgt_hdi.enum_values j
            on c.delivery_unit_ = j.enum
         inner join vgt_hdi.enum_values k
            on c.surface_finish_ = k.enum
         inner join vgt_hdi.enum_values l
            on c.sm_print_times_ = l.enum
         inner join vgt_hdi.enum_values m
            on c.sm_side_ = m.enum 
         inner join vgt_hdi.enum_values n
            on c.ss_print_times_ = n.enum
         inner join vgt_hdi.enum_values o
            on c.ss_side_ = o.enum 
         inner join vgt_hdi.enum_values p
            on c.dc_side_ = p.enum
         inner join vgt_hdi.enum_values q
            on c.dc_type_ = q.enum
         inner join vgt_hdi.enum_values r
            on c.rout_process_ = r.enum 
         inner join vgt_hdi.enum_values s
            on c.ul_side_ = s.enum
         inner join vgt_hdi.enum_values t
            on c.ul_mark_ = t.enum                     
         where a.item_name = '%s'
            and h.enum_type = 1057
           and i.enum_type = 1007
           and j.enum_type = 1029
           and k.enum_type = 1000
           and l.enum_type = 1114
           and m.enum_type = 1015
           and n.enum_type = 1113
           and o.enum_type = 1038
           and p.enum_type = 1022
           and q.enum_type = 1001
           and r.enum_type = 1045
           and s.enum_type = 1020
           and t.enum_type = 1019
        """ % strJOB
        dataVal = self.SELECT_DIC (dbc,sql)
        return dataVal

    def getLayerThkInfo(self,dbc, strJOB):

        """
        从InPlan中获取需要的数据
        :return:sql后的字典
        """

        # sql = """
        #         select a.item_name JOB_NAME,
        #         c.item_name LAYER_NAME,
        #         d.layer_position,
        #         round(d.required_cu_weight / 28.3495,2) CU_WEIGHT,
        #         e.finish_cu_thk_ FINISH_THICKNESS,
        #         round(e.cal_cu_thk_/ 1.0,2) CAL_CU_THK
        #         from vgt_hdi.items           a,
        #            vgt_hdi.job             b,
        #            vgt_hdi.items           c,
        #            vgt_hdi.copper_layer    d,
        #            vgt_hdi.copper_layer_da e
        #         where a.item_id = b.item_id
        #         and a.last_checked_in_rev = b.revision_id
        #         and a.root_id = c.root_id
        #         and c.item_id = d.item_id
        #         and c.last_checked_in_rev = d.revision_id
        #         and d.item_id = e.item_id
        #         and d.revision_id = e.revision_id
        #         and a.item_name = '%s'
        #         order by d.layer_index""" % strJOB
        sql = """
        SELECT
            a.item_name JOB_NAME,
            LOWER(c.item_name) LAYER_NAME,
            d.layer_position,
            round( d.required_cu_weight / 28.3495, 2 ) CU_WEIGHT,
             e.finish_cu_thk_  FINISH_THICKNESS,
             round(e.cal_cu_thk_/1.0,2)  CAL_CU_THK,
             d.layer_index,
             d.LAYER_ORIENTATION,
             round(e.LW_ORG_,2) 原稿线宽,
             round(e.LS_ORG_,2) 原稿线距,
             round(e.LW_FINISH_,2) 成品线宽,
             round(e.ls_finish_,2) 成品线距 
        FROM
            vgt_hdi.items a,
            vgt_hdi.job b,
            vgt_hdi.items c,
            vgt_hdi.copper_layer d,
            vgt_hdi.copper_layer_da e 
        WHERE
            a.item_id = b.item_id 
            AND a.last_checked_in_rev = b.revision_id 
            AND a.root_id = c.root_id 
            AND c.item_id = d.item_id 
            AND c.last_checked_in_rev = d.revision_id 
            AND d.item_id = e.item_id 
            AND d.revision_id = e.revision_id 
            AND a.item_name = '%s' 
        ORDER BY
            d.layer_index""" % strJOB
        dataVal = self.SELECT_DIC(dbc, sql)
        # --返回数据字典
        return dataVal

    def getLayerThkInfo_plate(self,dbc, strJOB, get_inner_outer=None):

        """
        从InPlan中获取需要的数据
        :return:sql后的字典
        樊后星通知：
        线路补偿 由计算完成厚度CAL_CU_THK_，改为计算完成厚度(不考虑树脂塞孔补偿)CAL_CU_THK_PLATE_
        """

        # sql = """
        #         select a.item_name JOB_NAME,
        #         c.item_name LAYER_NAME,
        #         d.layer_position,
        #         round(d.required_cu_weight / 28.3495,2) CU_WEIGHT,
        #         e.finish_cu_thk_ FINISH_THICKNESS,
        #         round(e.cal_cu_thk_/ 1.0,2) CAL_CU_THK
        #         from vgt_hdi.items           a,
        #            vgt_hdi.job             b,
        #            vgt_hdi.items           c,
        #            vgt_hdi.copper_layer    d,
        #            vgt_hdi.copper_layer_da e
        #         where a.item_id = b.item_id
        #         and a.last_checked_in_rev = b.revision_id
        #         and a.root_id = c.root_id
        #         and c.item_id = d.item_id
        #         and c.last_checked_in_rev = d.revision_id
        #         and d.item_id = e.item_id
        #         and d.revision_id = e.revision_id
        #         and a.item_name = '%s'
        #         order by d.layer_index""" % strJOB
        sql = """
        SELECT
            a.item_name JOB_NAME,
            LOWER(c.item_name) LAYER_NAME,
            d.layer_position,
            round( d.required_cu_weight / 28.3495, 2 ) CU_WEIGHT,
             e.finish_cu_thk_  FINISH_THICKNESS,
             CASE WHEN e.CAL_CU_THK_PLATE_ = 0 THEN round(e.CAL_CU_THK_/1.0,2) ELSE round(e.CAL_CU_THK_PLATE_/1.0,2) END AS CAL_CU_THK,
             -- round(e.CAL_CU_THK_PLATE_/1.0,2)  CAL_CU_THK,
             d.layer_index,
             d.LAYER_ORIENTATION,
             round(e.LW_ORG_,2) 原稿线宽,
             round(e.LS_ORG_,2) 原稿线距,
             round(e.LW_FINISH_,2) 成品线宽,
             round(e.ls_finish_,2) 成品线距 
        FROM
            vgt_hdi.items a,
            vgt_hdi.job b,
            vgt_hdi.items c,
            vgt_hdi.copper_layer d,
            vgt_hdi.copper_layer_da e 
        WHERE
            a.item_id = b.item_id 
            AND a.last_checked_in_rev = b.revision_id 
            AND a.root_id = c.root_id 
            AND c.item_id = d.item_id 
            AND c.last_checked_in_rev = d.revision_id 
            AND d.item_id = e.item_id 
            AND d.revision_id = e.revision_id 
            AND a.item_name = '%s' 
        ORDER BY
            d.layer_index""" % strJOB
        dataVal = self.SELECT_DIC(dbc, sql)
        
        res = self.check_new_cal_cu_thick_diff_mi_lot(dbc, strJOB, dataVal, get_inner_outer)
        if not res:
            dataVal = self.getLayerThkInfo(dbc, strJOB)
            
        # --返回数据字典                
        return dataVal
    
    def check_new_cal_cu_thick_diff_mi_lot(self, dbc, strJOB, 
                                           compare_values,
                                           get_inner_outer):
        """检测新的铜厚栏位是否跟MI报表铜厚一致，不一致取旧栏位值 20240422 by lyh"""
        sql = """select JOB_NAME,CI_SET_NAME,CIT_NAME
        ,ci_note.pre_instantiated_string
        from vgt_hdi.rpt_job_cam_instruction_list ci_Job
        left join (select * from vgt_hdi.ci_note) ci_note on ci_Job.item_id=ci_note.item_id
        and ci_Job.revision_id=ci_note.revision_id
        and ci_Job.sequential_index=ci_note.ci_sequential_index
        where (CIT_NAME='E.外层PCB' or CIT_NAME='D.内层')
        and ci_note.pre_instantiated_string like '%%补偿%%'
        and JOB_NAME='{0}'"""
        if get_inner_outer == "inner":
            sql = """select JOB_NAME,CI_SET_NAME,CIT_NAME
            ,ci_note.pre_instantiated_string
            from vgt_hdi.rpt_job_cam_instruction_list ci_Job
            left join (select * from vgt_hdi.ci_note) ci_note on ci_Job.item_id=ci_note.item_id
            and ci_Job.revision_id=ci_note.revision_id
            and ci_Job.sequential_index=ci_note.ci_sequential_index
            where (CIT_NAME='D.内层')
            and ci_note.pre_instantiated_string like '%%补偿%%'
            and JOB_NAME='{0}'"""            
        data_info = self.SELECT_DIC(dbc, sql.format(strJOB))
        mi_report_layer_cu_thick = {}
        for dic_info in data_info:
            detail_string_info = dic_info["PRE_INSTANTIATED_STRING"]
            if detail_string_info:
                for info in detail_string_info.decode("utf8").split(u"；"):
                    if "OZ" in info:
                        continue
                    
                    pattern = re.compile(u"(l\d+)/(l\d+)层按：(\d+.?\d+?)/(\d+.?\d+?)mil补偿")
                    res = re.search(pattern, info)
                    if res:
                        mi_report_layer_cu_thick[res.group(1)] = float(res.group(3))
                        mi_report_layer_cu_thick[res.group(2)] = float(res.group(4))
        
        if mi_report_layer_cu_thick:
            for dic_info in compare_values:
                layer = dic_info["LAYER_NAME"]
                if mi_report_layer_cu_thick.get(layer):
                    if abs(mi_report_layer_cu_thick[layer] - dic_info["CAL_CU_THK"]) > 0.1:
                        print(layer, mi_report_layer_cu_thick[layer],  dic_info["CAL_CU_THK"])
                        return False
        
        return True
    
    def get_mi_lot_compensate_value(self, dbc, strJOB):
        """获取MI报表上的线路补偿值 20240704 by lyh"""
        sql = """select JOB_NAME,CI_SET_NAME,CIT_NAME
        ,ci_note.pre_instantiated_string
        from vgt_hdi.rpt_job_cam_instruction_list ci_Job
        left join (select * from vgt_hdi.ci_note) ci_note on ci_Job.item_id=ci_note.item_id
        and ci_Job.revision_id=ci_note.revision_id
        and ci_Job.sequential_index=ci_note.ci_sequential_index
        where (CIT_NAME='E.外层PCB' or CIT_NAME='D.内层')
        and ci_note.pre_instantiated_string like '%%补偿%%'
        and JOB_NAME='{0}'"""
        data_info = self.SELECT_DIC(dbc, sql.format(strJOB))
        mi_report_layer_cu_thick = {}
        for dic_info in data_info:
            detail_string_info = dic_info["PRE_INSTANTIATED_STRING"]
            if detail_string_info:
                for info in detail_string_info.decode("utf8").split(u"；"):
                    if "OZ" in info:
                        pattern = re.compile(u"(l\d+)/(l\d+)层按：(\d+.?\d+?)/(\d+.?\d+?)OZ补偿")
                        res = re.search(pattern, info)
                        units = "OZ"
                    else:                    
                        pattern = re.compile(u"(l\d+)/(l\d+)层按：(\d+.?\d+?)/(\d+.?\d+?)mil补偿")
                        res = re.search(pattern, info)
                        units = "mil"
                        
                    if res:
                        mi_report_layer_cu_thick[res.group(1)] = (float(res.group(3)), units)
                        mi_report_layer_cu_thick[res.group(2)] = (float(res.group(4)), units)      
        
        return mi_report_layer_cu_thick

    def get_inplan_imp(self, dbc, strJOB):
        """
        从inplan获取阻抗信息，2021.11.16变更开窗阻抗部分
        :param dbc:
        :param strJOB:
        :return:
        """
        sql = """
            select a.item_name cur_job, 
                d.imp_group_ igroup,
                decode(d.model_type_,0,'特性',1,'差动',2,'特性共面',3,'差动共面') imodel,
                c.original_trace_width org_width,
                c.design_trace_trace_spacing org_spc,
                c.design_trace_ground_spacing org_cu_spc,
                d.trace_layer_,
                d.ref_layer_,
                d.finish_lw_,
                d.finish_ls_,
                d.spacing_2_copper_ spc2cu,
                d.eq_ls_,
                d.eq_lw_,
                d.eq_spacing_2_copper_,
                d.finish_ls_,
                d.finish_ls_,
                d.finish_ls_,
                c.customer_required_impedance cusimp,
                round(c.artwork_trace_width,2) work_width,
                case
                when c.model_name like '%%uncoated%%' and  (substr(d.trace_layer_,2,2) = '1')
                then '是'
                when c.model_name like '%%uncoated%%' and substr(d.trace_layer_,2,2) = ltrim(substr(a.item_name,5,2),'0')
                then '是'
                else '否'
                end  solderopen,
                decode(c.constraint_is_up_to_date,0,'否',1,'是') imp_update,
                c.stackup_ordering_index Ord_index 
                 from vgt_hdi.items a
                inner join vgt_hdi.public_items b
                 on a.root_id = b.root_id
                inner join vgt_hdi.impedance_constraint c
                 on b.item_id = c.item_id
                and b.REVISION_ID = c.revision_id
                inner join vgt_hdi.impedance_constraint_da d
                 on c.item_id = d.item_id
                and c.revision_id = d.revision_id
                and c.sequential_index = d.sequential_index
                where a.ITEM_NAME = '%s'""" % strJOB
        dataVal = self.SELECT_DIC (dbc,sql)
        # 料号名 ，分组，阻抗类型，原始线宽，原始间距，原始铜距，阻抗层，参考层，出货线宽，出货线距，出货铜距，客户需求阻值，是否开窗阻抗
        return dataVal

    def getStackUp(self,dbc, strJOB):

        # strJobName = job_name.split ('-')[0].upper ()
        # TODO NEXT LINE FOR TEST
        # === 2021.01.22 增加镭射层的获取 ===
        # === 2021.04.13 不获取光板层 BUG料号： HB7806PH018A1 ===
        sql = """SELECT
            a.item_name,
            c.item_name,
            e.film_bg_,
            e.DRILL_CS_LASER_ 
        FROM
            vgt_hdi.public_items a
            INNER JOIN vgt_hdi.job b ON a.item_id = b.item_id 
            AND a.revision_id = b.revision_id
            INNER JOIN vgt_hdi.public_items c ON a.root_id = c.root_id
            INNER JOIN vgt_hdi.process d ON c.item_id = d.item_id 
            AND c.revision_id = d.revision_id
            INNER JOIN vgt_hdi.process_da e ON d.item_id = e.item_id 
            AND d.revision_id = e.revision_id 
        WHERE
            a.item_name = '%s' 
            AND d.proc_type = 1 
            AND c.item_name NOT LIKE '%%光板%%'
        ORDER BY
            e.process_num_ DESC""" % strJOB
        dataVal = self.SELECT_DIC (dbc,sql)
        return dataVal

    def getPanelSRTable(self, dbc, strJOB):
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
           and c.is_main = 1''' % strJOB
        # 更新自动抓取AB板 新增条件 c.is_main = 1 20230424 by lyh
        dataVal = self.SELECT_DIC (dbc,sql)
        return dataVal

if __name__ == '__main__':
    import sys
    # print sys.path
    M = ORACLE_INIT(tnsName='service_name')
    dbc_o = M.DB_CONNECT(dbName='ERP')
    dataVal = M.SELECT_DIC(dbc_o, """SELECT * FROM VIEW_HDIGC_OEB A WHERE	A.OEB04 = 'H50208GN013A1'""")
    #dataVal = M.SELECT_DIC(dbc_o,"""SELECT * FROM VIEW_HDIGC_OEB A WHERE	A.OEB04 = 'H50208GN013A1'""")
    #print(dataVal[0]['OEA01'])
    # dataVal = M.SELECT_DIC(dbc_o,"""select TC_AAF00,TC_AAF01,TC_AAF03,TC_AAF04,TC_AAF06,TC_AAF05,TC_AAF09,TC_AAF32 From VIEW_TC_AAF_FILE WHERE TC_AAF00='H50208GN013A1A' ORDER BY TC_AAF01,TC_AAF03""")
    # print dataVal
"""
版本：V1.1
日期：2020.05.20
作者：宋超
1.更改获取inplan 阻抗线主语句get_inplan_imp，增加阻抗线序号
2.更改函数getPanelSRTable 中 由中文--> start_x,start_y 

版本：V1.2
日期：2021.01.22
作者：宋超
1.更改getStackUp 增加镭射层别的获取；

版本：V1.3 
日期：2021.11.16
作者：宋超
1.更改get_inplan_imp更改开窗阻抗语句；

版本：V1.4
日期：2022.04.13
作者：宋超
1.更改层别信息获取，增加原稿线宽线距数据。

"""
