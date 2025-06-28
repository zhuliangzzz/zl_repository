#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------- #
#                VTG.SH SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    LiuChuang
# @Mail         :    Chuang_cs@163.com
# @Date         :    2023/02/06
# @Revision     :    1.0.0
# @File         :    GetData.py
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
'''版本记录
版本    ：V1.0.0
更新日期：2023/02/06
作者    ：Chuang.Liu
更新内容：

'''

import os
import sys
import json

# --导入Package
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")

import Oracle_DB
import MySQL_DB
import PostgreSQL_DB


class Data(object):
    """
    数据操作方法（对接MySQL数据库部分）
    """

    def __init__(self):
        self.siteName = u'HDI事业部'
        # --初始化MySQL DB数据库
        self.DB_M = MySQL_DB.MySQL(printLog=False)
        self.dbc_m = self.DB_M.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                                             username='root', passwd='k06931!')

        # --初始化TOPCAM DB连接
        self.PG = PostgreSQL_DB.PostgreSQL(dbName='topcam', log=False)
        self.db_p = self.PG.POSTGRE_CONNECT()

        # -初始化ERP DB连接
        #self.DB_O = Oracle_DB.ORACLE_INIT(printLog=False)
        #self.dbc_e = self.DB_O.DB_CONNECT(dbName='ERP')

    def get_authorization(self, jobName):
        """
        在MySQL数据库中获取授权用户
        :return:
        """
        job_str = jobName[0:13]
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
        query_result = self.DB_M.SELECT_DIC(self.dbc_m, query_sql)
        if not query_result:
            return None
        result_dict = query_result[0]
        # === 键为中文，需要带上u字符
        # for key in result_dict:
        #     if key == u'内层制作人':
        return result_dict

    def get_ERP_user_code(self, cam_user_name):
        """
        从ERP中获取用户ID对应姓名
        :return:
        """
        query_sql = """SELECT gen01 工号 FROM s01.gen_file WHERE gen02='%s'""" % cam_user_name
        query_result = self.DB_O.SQL_EXECUTE(self.dbc_e, query_sql)

        if query_result:
            e_user_name = query_result[0][0]
            # print  e_user_name.decode('utf8').encode('gbk') # 在Genesis下调试用
            return e_user_name.decode('utf8')
        else:
            return None

    def get_TOPCAM_user_roles(self, userId):
        """
        从TOPCAM中获取登录topcam用户信息(TODO: TOPCAM中考虑是否需要增加锁放群组)
        :return: None
        """
        sql = """select
                    sr.id ,
                    srmu.user_id ,
                    su.username ,
                    su.fullname,
                    sr."name" ,    
                    sr.description
                from
                    sys_role_map_user srmu
                inner join sys_user su on
                    su .id = srmu.user_id
                inner join sys_role sr on
                    srmu.role_id = sr.id
                where
                    su.username = '%s'""" % userId
        # --获取查询结果
        queryResult = self.PG.SELECT_DIC(self.db_p, sql)
        """数据结构如下：
        [{'username': '47773', 'user_id': 2, 'description': '管理员', 'fullname': '柳闯', 'id': 1, 'name': 'ADMIN'},
        {'username': '47773', 'user_id': 2, 'description': '用于多层CAM锁放系统中的锁层权限', 'fullname': '柳闯', 'id': 18, 'name': '多层-料号锁定'},
        {'username': '47773', 'user_id': 2, 'description': '用于多层CAM锁放系统中的解锁权限', 'fullname': '柳闯', 'id': 19, 'name': '多层-料号解锁'}] 
        """
        # print queryResult

        return queryResult

    # region # --操作锁放记录部分
    def uploadLock_Layers(self, jobName, lockJson=None, logJson=None, userId=''):
        """
        插入锁定层的数据至DB中
        :param jobName: 型号名
        :param lockJson: 锁层的数据
        :param lockLog: 解锁、上锁的记录
        :return: True or False
        """
        # --这里的json为Python格式的json,需要改为标准的格式
        if lockJson: lockJson = json.dumps(lockJson)
        if logJson: logJson = json.dumps(logJson)
        # --判断些型号的数据是否存在
        if len(self.getLock_Info(jobName)) == 0:
            sql = """INSERT INTO hdi_engineering.job_lock_data  
                            (site,job_name ,locked_info,locked_log, create_by)
                     VALUES ('%s', '%s', '%s', '%s', '%s')
                  """ % (self.siteName, jobName, lockJson, logJson, userId)
            pass
        else:
            if lockJson and logJson:
                sql = """UPDATE hdi_engineering.job_lock_data  
                            SET 
                            locked_info = '%s',
                            locked_log = '%s',
                            update_by = '%s',
                            update_date = now()
                        WHERE job_name = '%s' ;
                      """ % (lockJson, logJson, userId, jobName)
            elif lockJson and logJson is None:
                sql = """UPDATE hdi_engineering.job_lock_data  
                            SET 
                            locked_info = '%s',                            
                            update_by = '%s',
                            update_date = now()
                        WHERE job_name = '%s' ;
                      """ % (lockJson, userId, jobName)
            elif lockJson is None and logJson:
                sql = """UPDATE hdi_engineering.job_lock_data  
                            SET 
                            locked_log = '%s',                           
                            update_by = '%s',
                            update_date = now()
                        WHERE job_name = '%s' ;
                      """ % (logJson, userId, jobName)
            # --当所有层都解锁完后，上锁的记录为空
            elif not lockJson and not logJson:
                sql = """UPDATE hdi_engineering.job_lock_data  
                            SET 
                            locked_info = '%s',                           
                            update_by = '%s',
                            update_date = now()
                        WHERE job_name = '%s' ;
                      """ % (lockJson, userId, jobName)
            else:
                print "Error!"
                pass

        # --返回执行结果
        # print "-------------->", sql
        return self.DB_M.SQL_EXECUTE(self.dbc_m, sql)

    def getLock_Info(self, jobName):
        """
        从DB中获取锁定层的数据
        :param jobName: 型号名
        :return: dict
        """
        sql = """select * from  hdi_engineering.job_lock_data jld where jld.job_name = '%s'""" % jobName
        result = self.DB_M.SELECT_DIC(self.dbc_m, sql)
        if not result:
            return []

        # --一个料号仅一条数据
        result_dict = result[0]

        return result_dict

    # endregion

    # region # --料号Matrix数据部分
    def getMatrix(self, jobName):
        """
        获取Matrix部分数据
        :param jobName: None
        :return: dict
        """
        sql = """select matrix_info  from hdi_engineering.job_attributes ja 
                    where ja.job_name = '%s'""" % jobName
        result_dict = self.DB_M.SELECT_DIC(self.dbc_m, sql)
        # print len(result_dict)

        if not len(result_dict):
            return []
        else:
            return result_dict
    # endregion


if __name__ == '__main__':
    M = Data()
    # print M.getLock_Info('ha4608pf085a2')
    # M.getMatrix('qa7410pn153a1')
    # M.getMatrix('c51906pnq74c2')
