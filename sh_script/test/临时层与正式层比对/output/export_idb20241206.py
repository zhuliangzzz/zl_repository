#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:export_idb.py
   @author:zl
   @time: 2024/11/13 16:28
   @software:PyCharm
   @desc:
"""
import hashlib
import os
import sys
import tarfile
import time

if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")

import MySQL_DB
class Export_idb(object):
    def __init__(self):
        self.source_dir = '/incampro/incamp_db1/jobs/'
        self.odb_dir = '/id/workfile/film/%s/' % jobname
        self.idb_dir = '/id/workfile/zl/tgz/'
        self.suffix = time.strftime('%Y%m%d%H%M%S')

    def export(self, dir):
        os.chdir(self.source_dir)
        self.tar_tgz(dir)
        self.insert_record()

    def tar_tgz(self, folder):
        if not os.path.exists(self.idb_dir):
            os.makedirs(self.idb_dir)
        output_file = self.idb_dir + folder + self.suffix + '.tgz'
        tar = tarfile.open(output_file, "w:gz")
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                tar.add(file_path)
        tar.close()
        # with tarfile.open(output_file, "w:gz") as tar:
        #     for root, dirs, files in os.walk(folder):
        #         for file in files:
        #             file_path = os.path.join(root, file)
        #             tar.add(file_path)

    @classmethod
    def calculate_md5(cls, file_path):
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:  # 以二进制读取模式打开文件
            for chunk in iter(lambda: f.read(4096), b""):  # 读取文件，每次4096字节
                md5.update(chunk)  # 更新哈希值
        return md5.hexdigest()  # 返回十六进制的哈希值

    def insert_record(self):
        odb_key = self.calculate_md5(self.odb_dir + jobname + '.tgz')
        idb_key = self.calculate_md5(self.idb_dir + jobname + self.suffix + '.tgz')
        sql = 'insert into hdi_engineering.incam_output_tgz_info(jobname,odb_md5_key,idb_md5_key) values(%s,%s,%s)'
        my_sql = MySQL_DB.MySQL()
        my_sql.MYSQL_CONNECT()
        my_sql.SQL_EXECUTE(my_sql.dbc, sql, (jobname, odb_key, idb_key))
        my_sql.DB_CLOSE(my_sql.dbc)


if __name__ == '__main__':
    jobname = sys.argv[1]
    export_idb = Export_idb()
    export_idb.export(jobname)