#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------- #
#                VTG.SH SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    LiuChuang
# @Mail         :    Chuang_cs@163.com
# @Date         :    2021/08/25
# @Revision     :    1.1.0
# @File         :    TOP_IKM.py
# @Software     :    PyCharm
# @Usefor       :    TOPCAM的DB操作接口
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
更新日期：2021/08/27
作者    ：Chuang.Liu
更新内容：
    1、增加结果报告写入方法(调用源码：..\sys\scripts\sh_script\CheckOnpad_SM\check_onpad_sm.py)

版本    ：V1.1.0
更新日期：2022/05/09
作者    ：Chuang.Liu
更新内容：
    1、原需求链接（警示阻焊二次优化）：http://192.168.2.120:82/zentao/story-view-3892.html
    2、增加日志内容查询方法(调用源码：/incam/server/site_data/scripts/sh_script/MaskOpt/MaskOpt_Main.py)
                                    /incam/server/site_data/scripts/sh_script/Check_SET_Fiducial/CheckSetFiducial.py          
'''

import platform
import sys

# --加载相对位置，以实现InCAM与Genesis共用
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import PostgreSQL_DB


class IKM:
    def __init__(self):
        # --初始化Postgre SQL DB的链接 (不显示Log记录，以用于csh文件接收参数)
        self.PG = PostgreSQL_DB.PostgreSQL(dbName='topcam')
        self.dbc_p = self.PG.POSTGRE_CONNECT()

    def update_flow_report(self, processid, jobid=None, jobName=None, report=None, style=None):
        """
        更新jobflow中的报告信息
        :param report:传入的报告内容
        :param processid:当前执行的流程id
        :param jobid:当前执行的jobid （建议使用jobid，属于topcam %ARGS全局参数中的key）
        :param jobName:当前执行的型号
        :return:更新状态
        """
        if style:
            htmlReport = """<html><body bgcolor="#DDECFE"><font size="3" color="#003DB2">
                                <p style="color:%s"> %s </p>                                
                                </body>
                            </html>""" % (style, report)
        else:
            htmlReport = """<html><body bgcolor="#DDECFE"><font size="3" color="#003DB2">
                                <p> %s </p>
                                </body>
                            </html>""" % report
        sql = None
        # --按传入的参数定义sql
        if jobName:
            sql = """UPDATE pdm_job_workflow 
                        SET report = '%s'
                        WHERE
                            process_id = %s 
                            AND job_id IN (SELECT pj.id FROM pdm_job pj WHERE pj.jobname = '%s')
                  """ % (htmlReport, processid, jobName)
        if jobid:
            sql = """UPDATE pdm_job_workflow 
                        SET report = '%s'
                        WHERE
                            process_id = %s 
                        AND job_id = %s""" % (htmlReport, processid, jobid)
        # --执行SQL
        if self.PG.SQL_EXECUTE(self.dbc_p, sql):
            # self.PG.LOG(u'报告信息更新成功...')
            return True
        else:
            # self.PG.LOG(u'报告信息更新失败...')
            return False

    def get_run_logs(self, pworkId, processid, jobid=None, jobName=None,
                     logType="'New','Cancel','Error','Critical','Warning','Done','Finish'", order=None):
        """
        查询子流程运行的log信息
        :param pworkId:父流程的ID(通过后台软件工程流程管理中查询对应父流程的ID-编号）
        :param processid:当前执行的流程id（当前流程中右键查看流程即可查看对应的ID）
        :param jobid:当前执行的jobid （建议使用jobid，属于topcam %ARGS全局参数中的key）
        :param jobName:当前执行的型号
        :param logType:当前执行的型号日志状态条件
        :param order:当前结果排序规则
        :return:更新状态
        """
        # --过滤条件
        if not jobName:
            whereInfo = "pj.id = %d" % jobid
        else:
            whereInfo = "pj.jobname = '%s'" % jobName
        # --排序
        if not order:
            orderBy = "order by log.action_time DESC"
        else:
            orderBy = "order by %s" % order

        sql = """SELECT
                    pj."id" "型号ID",
                    pj.jobname 型号名,	
                    pwork.ID AS "流程ID",
                    pwork."name" 流程别名,
                    pwork.title 流程中文名,
                    pw.ID AS "子流程ID",
                    pw.title AS 子流程名,
                    pw."name" AS 子流程调用程序名,	
                    log.action_type 子流程执行状态,
                    pjw.user_name 子流程执行用户,
                    log.action_time 日志记录时间 
                FROM
                    pdm_job_workflow pjw
                    INNER JOIN sys_log log ON pjw."id" = log.row_id
                    INNER JOIN pdm_workprocess pw ON pw."id" = pjw.process_id
                    INNER JOIN pdm_job pj ON pjw.job_id = pj.
                    ID INNER JOIN pdm_workflow_lnk_workprocess pwlw ON pwlw.step_id = pjw.process_id
                    INNER JOIN pdm_workflow pwork ON pwork."id" = pwlw.flow_id 
                WHERE
                    pwork.ID = %d 
                    AND pjw.process_id = %d
                    AND %s
                    AND log.action_type IN ( %s )
                    %s""" % (pworkId, processid, whereInfo, logType, orderBy)

        # print (self.PG.SELECT_DIC(self.dbc_p, sql)[0]['型号ID'])
        # print (self.PG.SELECT_DIC(self.dbc_p, sql)[0]['子流程名'])
        return self.PG.SELECT_DIC(self.dbc_p, sql)

    def getJobAttrValue(self, jobId, attrName):
        """
        获取料号信息
        :param jobId:料号ID
        :param attrName:料号属性名称 (可多个属性,注意传入的参数需要带单引号)
        :return:料号属性的值，如果料号属性不存在，则返回undef
        """
        sql = """SELECT
                    PJOB.jobname,
                    PJJ.attr_name,
                    PJJ.value
                FROM
                    PDM_JOB_JOBATTR PJJ
                    INNER JOIN PDM_JOB PJOB ON PJJ.job_id = PJOB.ID 
                WHERE
                    PJOB.jobname = '%s'
                    AND PJJ.attr_name IN ( %s ) """ % (jobId, attrName)
        return self.PG.SELECT_DIC(self.dbc_p, sql)

    def db_close(self):
        """
        关闭数据库的连接
        :param dbc: 连接信息
        :return:None
        """
        self.PG.DB_CLOSE(self.dbc_p)


if __name__ == '__main__':
    M = IKM()
    print (M.get_run_logs(9, 103, 120565, logType="'Done','Finish'"))
    # M.update_flow_report(919, jobid=81865, report='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
