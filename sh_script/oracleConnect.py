#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

os.environ['NLS_LANG'] = "AMERICAN_AMERICA.UTF8"
import cx_Oracle

def rows_as_dicts(cursor):
    """
    转换为字典
    :param cursor:
    :return:
    """
    col_names = [i[0] for i in cursor.description]
    return [dict(zip(col_names, row)) for row in cursor]


class oracleConn(object):
    def __init__(self,serviceName = 'topprod'):
        super(oracleConn,self).__init__()
        if serviceName in ["topprod"]:
            """inplan信息"""
            (self.sqlServer,self.serviceName,
             self.port, self.user,self.passWord) = ("172.20.218.247",serviceName, '1521', "ZYGC","zygc@2019")
        elif serviceName in ["inmind"]:
            (self.sqlServer, self.serviceName,
             self.port, self.user, self.passWord) = ("172.20.218.193", "inmind.fls", '1521', "GETDATA", "InplanAdmin")
        elif serviceName in ["prod_apps"]:
            (self.sqlServer, self.serviceName,
             self.port, self.user, self.passWord) = ("cderpdb-scan", "PROD", '1521', "INP", "INP")
        elif serviceName in ["PROD"]:
            (self.sqlServer, self.serviceName,
             self.port, self.user, self.passWord) = ("cderpdb-scan", "prod", '1521', "INP", "INP")
        elif serviceName in ["TEST4"]:
            (self.sqlServer,self.serviceName,
             self.port, self.user,self.passWord) = ("10.1.100.14",serviceName, '1530', "apps","apps")
        elif serviceName in ["TEST3"]:
            (self.sqlServer, self.serviceName,
             self.port, self.user, self.passWord) = ("10.1.100.16", serviceName, '1527', "apps", "apps")
        elif serviceName in ["TEST2"]:
            (self.sqlServer, self.serviceName,
             self.port, self.user, self.passWord) = ("10.1.100.152", serviceName, '1526', "INP", "INP")
        elif serviceName in ["OAPROD"]:
            (self.sqlServer, self.serviceName,
             self.port, self.user, self.passWord) = ("10.1.100.170", serviceName, '1521', "v3xuser", "v3xuser")
        else:
            (self.sqlServer, self.serviceName, self.user,
             self.passWord) = ("", serviceName, "", "")

    def get_cnxn(self):
        dsn = cx_Oracle.makedsn(
            self.sqlServer, self.port, service_name=self.serviceName)
        cnxn = cx_Oracle.connect(self.user, self.passWord, dsn)
        return cnxn
                        
    def executeSql(self, sqlstring, ParamValue=None, is_arraysize=True):
        try:
            dsn = cx_Oracle.makedsn(
                self.sqlServer, self.port, service_name=self.serviceName)
            # cnxn = cx_Oracle.connect(self.user, self.passWord, dsn)
            try:            
                cnxn = cx_Oracle.connect(
                    self.user, self.passWord, dsn)
            except Exception, e:
                #if self.serviceName not in ["inmind"]:
                    #print "cnxn error: ", e
                cnxn = cx_Oracle.connect(self.user, self.passWord, dsn.replace(
                    'SERVICE_NAME', 'SID'))
                
            cursor = cnxn.cursor()
            if is_arraysize:
                cursor.arraysize = 100000

            if ParamValue is None:
                cursor.execute(sqlstring)
            else:
                cursor.execute(sqlstring, ParamValue)

            # 某些inplan的sql在查询时 是不能用round计算 否则查询直接报错 20220615
            data_info = cursor.fetchall()

            data_info_bak = []

            if data_info:                
                for items in data_info:
                    items_bak = []
                    #print items
                    for t in items:
                        try:
                            if isinstance(t, cx_Oracle.LOB):
                                #print t
                                items_bak.append(t.read())
                            else:
                                items_bak.append(t)
                        except Exception, e:
                            print e, "oracle error1"
                    data_info_bak.append(items_bak)
                    
            cursor.close()
            cnxn.close()
            
            return data_info_bak        
        except Exception,e:
            print e, "oracle error3"
            return []
        
    def select_dict(self, sqlstring, ParamValue=None, is_arraysize=True):
        try:
            dsn = cx_Oracle.makedsn(
                self.sqlServer, self.port, service_name=self.serviceName)
            # cnxn = cx_Oracle.connect(self.user, self.passWord, dsn)
            try:
                cnxn = cx_Oracle.connect(
                    self.user, self.passWord, dsn)
            except Exception, e:
                # if self.serviceName not in ["inmind"]:
                # print "cnxn error: ", e
                cnxn = cx_Oracle.connect(self.user, self.passWord, dsn.replace(
                    'SERVICE_NAME', 'SID'))

            cursor = cnxn.cursor()
            if is_arraysize:
                cursor.arraysize = 100000

            if ParamValue is None:
                cursor.execute(sqlstring)
            else:
                cursor.execute(sqlstring, ParamValue)

            # 某些inplan的sql在查询时 是不能用round计算 否则查询直接报错 20220615
            try:
                # data_info = cursor.fetchall()

                data_info = rows_as_dicts(cursor)
                # --返回数据
                # return data_info
            except:
                data_info = False

            cursor.close()
            cnxn.close()

            return data_info
        except Exception, e:
            print e, "oracle error4"
            return []
        
    def insertSql(self,sqlstring,ParamValue=None):
        try:
            dsn = cx_Oracle.makedsn(
                self.sqlServer, self.port, service_name=self.serviceName)
            try:
                cnxn = cx_Oracle.connect(self.user,self.passWord,dsn)
            except Exception, e:
                #if self.serviceName not in ["inmind"]:
                    #print "cnxn error: ", e
                cnxn = cx_Oracle.connect(self.user, self.passWord, dsn.replace(
                    'SERVICE_NAME', 'SID'))
                
            cursor = cnxn.cursor()
            if ParamValue is None:
                cursor.execute(sqlstring)
            else:
                cursor.execute(sqlstring,ParamValue)
            cnxn.commit()
            cursor.close()
            cnxn.close()
            return 0
        except Exception,e:
            # print "insert error:", e
            return []

    def updateSql(self, sqlstring, ParamValue=None):
        try:
            dsn = cx_Oracle.makedsn(
                self.sqlServer, self.port, service_name=self.serviceName)
            try:
                cnxn = cx_Oracle.connect(self.user, self.passWord, dsn)
            except Exception, e:
                #if self.serviceName not in ["inmind"]:
                    #print "cnxn error: ", e
                cnxn = cx_Oracle.connect(self.user, self.passWord, dsn.replace(
                    'SERVICE_NAME', 'SID'))
            cursor = cnxn.cursor()
            if ParamValue is None:
                cursor.execute(sqlstring)
            else:
                cursor.execute(sqlstring, ParamValue)
            cnxn.commit()
            cursor.close()
            cnxn.close()
            return 0
        except Exception, e:
            # print "update error:", e
            return []

    def insertSql_clob(self, sqlstring, ParamValue=None, dic_clob={}):
        try:
            dsn = cx_Oracle.makedsn(
                self.sqlServer, self.port, service_name=self.serviceName)
            try:
                cnxn = cx_Oracle.connect(self.user,self.passWord,dsn)
            except Exception, e:
                #if self.serviceName not in ["inmind"]:
                    #print "cnxn error: ", e
                cnxn = cx_Oracle.connect(self.user, self.passWord, dsn.replace(
                    'SERVICE_NAME', 'SID'))
            cursor = cnxn.cursor()
            clob_str = dic_clob.values()[0]
            clob_key = dic_clob.keys()[0]
            clob_data = cursor.var(cx_Oracle.CLOB)
            clob_data.setvalue(0, clob_str)

            ParamValue[clob_key] = clob_data

            # print ParamValue
            if ParamValue is None:
                cursor.execute(sqlstring)
            else:
                cursor.execute(sqlstring, ParamValue)
                
            cnxn.commit()
            cursor.close()
            cnxn.close()
            return 0
        except Exception,e:
            # print "update error1:", e
            return "error"
        
    def excute_procall(self, PROCEDURE, org_id, sqlstring = None):
        """执行过程"""
        try:
            dsn = cx_Oracle.makedsn(self.sqlServer,self.port,service_name=self.serviceName)
            try:            
                cnxn = cx_Oracle.connect(self.user,self.passWord,dsn)
            except Exception, e:
                #if self.serviceName not in ["inmind"]:
                    #print "cnxn error: ", e
                cnxn = cx_Oracle.connect(self.user,self.passWord,dsn.replace('SERVICE_NAME','SID'))
                
            cursor = cnxn.cursor()
            #msg = cursor.var(cx_Oracle.STRING) #plsql出参
            #调用存储过程
            #print PROCEDURE, [org_id, msg]
            cursor.callproc(PROCEDURE, [org_id])
            if sqlstring is not None:                
                cursor.execute(sqlstring)
                data_info = cursor.fetchall()
            else:
                data_info = []
            
            cursor.close()
            cnxn.close()
            return data_info
        except Exception,e:
            print "procall error:",e
            return []

    def excute_procall_args(self, PROCEDURE, args, msg_return=False):
        """执行过程"""
        try:
            dsn = cx_Oracle.makedsn(
                self.sqlServer, self.port, service_name=self.serviceName)
            try:            
                cnxn = cx_Oracle.connect(self.user,self.passWord,dsn)
            except Exception, e:
                #if self.serviceName not in ["inmind"]:
                    #print "cnxn error: ", e
                cnxn = cx_Oracle.connect(self.user,self.passWord,dsn.replace('SERVICE_NAME','SID'))
                
            cursor = cnxn.cursor()
            #x = cursor.var(cx_Oracle.STRING)
            #y = cursor.var(cx_Oracle.STRING)
            if msg_return:
                msg = cursor.var(cx_Oracle.STRING)  # plsql出参
                args = args + (msg, )
            #args = ["83", "100352466E1699A-102", "01", x, y, msg]
            #调用存储过程
            #print PROCEDURE, [org_id, msg]
            cursor.callproc(PROCEDURE, args)
            msg_text = ""
            if msg_return:
                msg_text = msg.getvalue()
            #print msg_text
            cursor.close()
            cnxn.close()

            return msg_text
        except Exception, e:
            print "procall error:",e
            return []  

    def send_wx_message(self, reciever='011065',
                         subject='warning',
                         message='test',
                         acc='011064',
                         url='111',
                         PROCEDURE="APPS.cux_gen_laminating_warning.send_erp_wxwork"):

        if "ping IP" in subject:
            """屏蔽此测试发送通知"""
            return
        
        msg_text = ""
        try:
            dsn = cx_Oracle.makedsn(self.sqlServer,self.port,service_name=self.serviceName)
            try:            
                cnxn = cx_Oracle.connect(self.user,self.passWord,dsn)
            except Exception, e:
                #if self.serviceName not in ["inmind"]:
                    #print "cnxn error: ", e
                cnxn = cx_Oracle.connect(self.user,self.passWord,dsn.replace('SERVICE_NAME','SID'))
                
            cursor = cnxn.cursor()
            
            msg = cursor.var(cx_Oracle.NUMBER)
            cursor.callproc(PROCEDURE, [reciever, subject, message, acc, url, msg])
            msg_text = msg.getvalue()
            cursor.close()
            cnxn.close()
        except Exception, e:
            print e
            msg_text = ""
        return msg_text