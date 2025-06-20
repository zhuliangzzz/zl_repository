#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    LiuChuang
# @Mail         :    Chuang_cs@163.com
# @Date         :    2019/01/15
# @Revision     :    1.2.1
# @File         :    PostgreSQL_DB.py
# @Software     :    PyCharm
# @Usefor       :    Postgre连接等操作
# ---------------------------------------------------------#

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

import platform
import re

import psycopg2


def rows_as_dicts(cursor):
    """
    转换为字典
    :param cursor:
    :return:
    """
    col_names = [i[0] for i in cursor.description]
    return [dict(zip(col_names, row)) for row in cursor]


class PostgreSQL:

    def __init__(self, file=None, log=True, dbName=None):
        """
        初始化
        :param file:日志文件绝对路径
        :param log: 是否启用打印log
        :param dbName: 连接DB的名称
        """
        # --获取系统类型返回结果“Windows” or "Linux"
        self.system = platform.system()
        self.logFile = file
        self.showLog = log
        self.dbc = None

        # --配置SQL服务器 (TopCAM数据库)
        if dbName == 'topcam':
            self.config = {
                'host': "192.168.2.104",
                'port': 5432,
                'username': "toplinker",
                'password': "TopLinker0510",
                'database': "TOPDFM_SHT_V6"
            }
        else:
            self.config = {
                'host': "192.168.2.104",
                'port': 5432,
                'username': "toplinker",
                'password': "TopLinker0510",
                'database': "TOPDFM_SHT_V6"
            }

    # --连接Oracle数据库
    def POSTGRE_CONNECT(self, hostName=None, database=None, prod=None, username=None, passwd=None):
        """
        Oracle数据库连接
        :param hostName: 主机名
        :param database: 连接数据库名
        :param prod: 端口号
        :param username: 登录用户名
        :param passwd: 登录用户密码
        :return: 登录结果
        """
        # --当默认连接没有传参时使用系统定义
        if hostName is None or database is None or prod is None or username is None or passwd is None:
            hostName = self.config['host']
            database = self.config['database']
            prod = self.config['port']
            username = self.config['username']
            passwd = self.config['password']

        try:
            self.dbc = psycopg2.connect(
                host=hostName,
                port=prod,
                user=username,
                password=passwd,
                database=database)
            self.LOG("PostgreSQL (Host:%s) connection successful !" % hostName)
        except Exception as e:
            self.LOG("PostgreSQL (Host:%s) connection failed !(%s)" % (hostName, e))
            return False

        # --返回链接
        return self.dbc

    # --关闭Oracle
    def DB_CLOSE(self, dbc):
        """
        关闭数据库连接
        :param dbc: 连接的信号
        :return: None
        """
        self.dbc = dbc
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
            self.LOG(sql)

        # --当匹配通过时（以select开头，并无大小写区分）
        if m:
            try:
                sql_info = cursor.fetchall()
                # --返回数据
                return sql_info
            except:
                return False
            finally:
                # --关闭游标
                cursor.close()
        else:
            try:
                dbc.commit()
                return True
            except:
                return False
            finally:
                # --关闭游标
                cursor.close()

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
        # cursor = dbc.cursor(psycopg2.cursors.DictCursor)
        cursor = dbc.cursor()
        cursor.execute(sql)

        # --记录更新的SQL列表
        try:
            self.LOG(sql)
        except:
            self.LOG(sql)

        # --当匹配通过时（以select开头，并无大小写区分）
        if m:
            try:
                # sql_info = cursor.fetchall()
                # # --返回键值对
                # return sql_info
                data = rows_as_dicts(cursor)
                # --返回数据
                return data
            except:
                return False
            finally:
                # --关闭游标
                cursor.close()
        else:
            # --关闭游标
            cursor.close()
            return False

    # --记录日志
    def LOG(self, log_msg):
        """
        记录日志文件至tmp盘
        :param log_msg: 传入的日志信息
        :return: None
        """
        if not self.showLog: return
        import time
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

        # --开始执行转换
        try:
            log_msg = (str(now_time) + ":" + log_msg)
        except:
            log_msg = log_msg

        # --打印Log
        # print(log_msg.encode('gbk'))

        # --是否打印至文本
        if self.logFile is not None:
            f = open(self.logFile, 'a')
            f.write(log_msg + '\n')
            f.close()


# if __name__ == '__main__':
#     M = PostgreSQL(dbName='topcam')
#     M.POSTGRE_CONNECT()
"""
V1.2.0
    连接方法中增加dbname参数，以便在脚本不直接暴露相关连接信息
v1.2.1
    修复Window下打印中文乱码问题
"""