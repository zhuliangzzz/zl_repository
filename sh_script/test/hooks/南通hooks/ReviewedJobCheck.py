#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:ReviewedJobCheck.py
   @author:zl
   @time: 2024/11/15 9:01
   @software:PyCharm
   @desc:
   外层已审核料号在南通服务器用户禁止打开
   在hidiincam存在且该料号外层已审核
"""
import sys
import platform,sys
import paramiko


if platform.system() == "Windows":
    sys.path.append("Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append("/incam/server/site_data/scripts/Package")
import genClasses_zl as gen
import MySQL_DB

from PyQt4 import QtGui, QtCore

class ReviewedJobCheck(object):
    def __init__(self):
        self.db = MySQL_DB.MySQL()
        self.dbc = self.db.MYSQL_CONNECT()
        if not self.dbc:
            QtGui.QMessageBox.warning(None, u"提示", u'数据库连接失败')
            sys.exit()

    def check(self):
        # 先判断incam服务器是否存在此料号
        # 远程主机的 IP 地址和端口
        hostname = '172.20.218.191'
        port = 22
        # SSH 用户名和密码
        username = 'Incam'
        password = 'incam'
        # remote_command = 'cd /data2/incamp_db1/jobs;ls |grep ' + jobname
        remote_command = 'cd /data2/incamp_db1/jobs;find . -maxdepth 1 -name ' + jobname
        # 创建 SSH 客户端对象
        client = paramiko.SSHClient()
        # 允许连接不在 known_hosts 文件中的主机
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 建立 SSH 连接
        client.connect(hostname, port, username, password)
        # 执行远程命令
        stdin, stdout, stderr = client.exec_command(remote_command)
        # 获取命令输出
        output = stdout.read() + stderr.read()
        client.close()
        if jobname not in output:
            return
        # hdi incam服务器也有该料号，则判断外层是否已审核
        sql = """
        select psj.ocheckfinish_time
                    from project_status.project_status_jobmanage psj
                    WHERE job = '{0}'
                    order by id desc"""
        job_process_info = self.db.SELECT_DIC(self.dbc, sql.format(jobname))
        self.db.DB_CLOSE(self.dbc)
        # 已审核完的检测
        if job_process_info and job_process_info[0].get("ocheckfinish_time", ''):
            QtGui.QMessageBox.warning(None, u"提示", u'外层已审核，南通用户禁止打开')
            gen.Job(jobname).COM('skip_current_command')
            sys.exit()


if __name__ == '__main__':
    jobname = sys.argv[1]
    app = QtGui.QApplication(sys.argv)
    reviewedJobCheck = ReviewedJobCheck()
    reviewedJobCheck.check()

