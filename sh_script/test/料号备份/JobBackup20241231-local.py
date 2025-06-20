#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:JobBackup.py
   @author:zl
   @time: 2024/12/30 8:49
   @software:PyCharm
   @desc: 料号备份
"""
import json
import os
import sys
import tarfile
import socket
import MySQL_DB
import ZL_mysqlCon as zlmysql


class JobBackup(object):
    def __init__(self):
        self.host = socket.gethostname()
        # sql = 'insert into hdi_engineering.incam_output_tgz_info(jobname,odb_modify_time,odb_md5_key,idb_file,idb_md5_key,user,host) values(%s,%s,%s,%s,%s,%s,%s)'
        # my_sql = MySQL_DB.MySQL()
        # my_sql.MYSQL_CONNECT()
        # my_sql.SQL_EXECUTE(my_sql.dbc, sql, (jobname, odb_modify_time, odb_key, idb_file, idb_key, username, self.host))
        # my_sql.DB_CLOSE(my_sql.dbc)
        # job存放路径
        # self.job_path = '/incampro/incamp_db1/jobs/'
        self.localDbConnect = zlmysql.LocalDbConnect()
        self.connection = self.localDbConnect.connection
        self.cursor = self.localDbConnect.cursor
        self.job_path, self.job_backup_path, self.diff_time = None, None, None
        try:
            data = json.load(open('config'))
            self.job_path = data.get('job_path')
            # job备份路径
            # self.job_backup_path = '/incam/server/site_data/scripts/zl/tmp/'
            self.job_backup_path = data.get('job_backup_path')
            if 'ntincam' in self.host:
                # self.job_path = '/incampro/incamp_db3/jobs/'
                self.job_path = data.get('nt_job_path')
            # 设置更新时间差 :h
            self.diff_time = float(data.get('diff_time')) * 3600  # 秒
        except Exception as e:
            sql = "insert into incam_job_backup_info(job_path, job_backup_path, diff_time,log) values(%s, %s, %s, %s)"
            try:
                self.cursor.execute(sql,
                                (self.job_path, self.job_backup_path, self.diff_time, '配置信息异常： ' + str(e)))
                self.connection.commit()
            except:
                self.connection.rollback()
            sys.exit()

    def backup(self):
        for job_dir in os.listdir(self.job_path):
            if not os.path.exists(os.path.join(self.job_backup_path, job_dir + '.tgz')):
                self.tar_tgz(job_dir)
            else:
                try:
                    # 判断时间差
                    job_time = os.path.getmtime(os.path.join(self.job_path, job_dir + '/misc/info'))
                    back_time = os.path.getctime(os.path.join(self.job_backup_path, job_dir + '.tgz'))
                    if job_time - back_time > self.diff_time:
                        self.tar_tgz(job_dir)
                    sql = "insert into incam_job_backup_info(jobname,job_path, job_backup_path, diff_time,log) values(%s, %s, %s, %s, %s)"
                    try:
                        self.cursor.execute(sql,
                                            (job_dir, self.job_path, self.job_backup_path, self.diff_time/3600,
                                             '导出成功： %s.tgz' % job_dir))
                        self.connection.commit()
                    except:
                        self.connection.rollback()
                except Exception as e:
                    sql = "insert into incam_job_backup_info(jobname,job_path, job_backup_path, diff_time,log) values(%s, %s, %s, %s, %s)"
                    try:
                        self.cursor.execute(sql,
                                        (job_dir, self.job_path, self.job_backup_path, self.diff_time/3600,
                                         '备份异常： ' + str(e)))
                        self.connection.commit()
                    except:
                        self.connection.rollback()

    def tar_tgz(self, jobname):
        if not os.path.exists(self.job_backup_path):
            os.makedirs(self.job_backup_path)
        output_file = os.path.join(self.job_backup_path, jobname + '.tgz')
        tar = tarfile.open(output_file, "w:gz")
        for root, dirs, files in os.walk(jobname):
            for file in files:
                file_path = os.path.join(root, file)
                tar.add(file_path)
        tar.close()


if __name__ == '__main__':
    jobBackup = JobBackup()
    jobBackup.backup()
