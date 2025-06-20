#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    LiuChuang
# @Mail         :    Chuang_cs@163.com
# @Date         :    2019/01/15
# @Revision     :    2.2.0
# @File         :    MySQL_DB.py
# @Software     :    PyCharm
# @Usefor       :    MySql连接等操作
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

import platform
import re
import sys

import pymysql


class MySQL:
    # --配置SQL服务器 (MYSQL工程管理数据库)
    __config = {
        'host': "192.168.2.19",
        'port': 3306,
        'username': "root",
        'password': "k06931!",
        'database': "project_status",
        'charset': "utf8"
    }

    def __init__(self, file=None, logCode='gbk', printLog=True):
        # --获取系统类型返回结果“Windows” or "Linux"
        self.logCode = logCode
        self.printLog = printLog
        self.system = platform.system()
        self.logFile = file
        self.dbc = None

    # --连接Oracle数据库
    def MYSQL_CONNECT(self, hostName=__config['host'], database=__config['database'], prod=__config['port'],
                      username=__config['username'], passwd=__config['password']):
        """
        Oracle数据库连接
        :param hostName: 主机名
        :param database: 连接数据库名
        :param prod: 端口号
        :param username: 登录用户名
        :param passwd: 登录用户密码
        :return: 登录结果
        """
        try:
            self.dbc = pymysql.connect(
                host=hostName,
                port=prod,
                user=username,
                passwd=passwd,
                db=database,
                charset=self.__config['charset'])
            # self.LOG(u"数据库（%s）连接成功！" % database)
            self.LOG("MySql db connect successfull ! Host:%s" % hostName)
        except:
            # self.LOG(u"Error：数据库连接失败！")
            self.LOG("MySql db connect failed ! Host:%s" % hostName)
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
    def SQL_EXECUTE(self, dbc, sql, params=None):
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
        #增加带参数执行 20230307 by lyh
        if params is None:            
            cursor.execute(sql)
        else:
            cursor.execute(sql, params)
        # --记录更新的SQL列表
        try:
            self.LOG(sql)
        except:
            print(sql)

        # --当匹配通过时（以select开头，并无大小写区分）
        if m:
            try:
                sql_info = cursor.fetchall()
                cursor.close()
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
        cursor = dbc.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(sql)

        # --记录更新的SQL列表
        try:
            self.LOG(sql)
        except:
            print(sql)

        # --当匹配通过时（以select开头，并无大小写区分）
        if m:
            try:
                dictData = cursor.fetchall()
                # --返回键值对
                return dictData
            except:
                return False
        else:
            return False

    # --记录日志
    def LOG(self, log_msg):
        """
        记录日志文件至tmp盘
        :param log_msg: 传入的日志信息
        :return: None
        """
        # --部分情况下不能打印日志，如Perl程序调用涉及接收回传参数影响
        if not self.printLog: return
        import time
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

        # --开始执行转换
        try:
            # --当传入的只有"\n"回车时，仅打印回车，不打印时间
            if len(re.findall('^\n(?:\n+)?$', log_msg)) == 0:
                log_msg = (str(now_time) + u':' + log_msg)
        except:
            log_msg = log_msg

        # --打印Log
        # print(log_msg.encode('utf-8'))
        try:
            if sys.version[:3] in ('2.6', '2.7'):
                print(log_msg.encode(self.logCode))
            else:
                print(log_msg)
        except:
            print(log_msg)

        # --是否打印至文本
        if self.logFile is not None:
            f = open(self.logFile, 'a')
            # --防止发生传入的数据为数组时，无法连接
            f.write(log_msg)
            f.write('\n')
            f.close()


"""
版本  ：V2.1.0
更新人：柳闯
更新时间：2022-01-06
更新内容：
    增加日志打印的参数，因部分脚本不需要打印；

版本  ：V2.2.0
更新人：柳闯
更新时间：2022-03-08
更新内容：
    LOG打印兼容2.7以后的版本，以免中文出现乱码；

版本  ：V2.2.1
更新人：柳闯
更新时间：2022-04-28
更新内容：
    修复V2.1.0不需要打印的bug；
"""
