#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:GetIdbByOdbPath.py
   @author:zl
   @time: 2024/11/18 16:53
   @software:PyCharm
   @desc:
   通过odb获取对应的idb
"""
import hashlib
import os
import sys


if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")

import MySQL_DB
class GetIdbByOdbPath(object):
    def __init__(self):
        # input_tgz 的路径
        '''
        	if ( $sel_site eq hanzi("胜宏全套"))  {
                $tgz_path = "/windows/33\.tgz/$client_no\系列";
                chdir "$do_path";
            } elsif ( $sel_site eq hanzi("临时")) {
                $tgz_path = "/windows/33\.file/$client_no\系列";
                chdir "$do_path";
            } elsif ( $sel_site eq hanzi("HDI全套")) {
                $tgz_path = "/windows/174\.tgz/$client_no\系列";
                chdir "$do_path";
            }
        '''
        self.odb_dir = '/id/workfile/film/%s/' % jobname
        self.idb_dir = '//192.168.2.172/GCfiles/全套TGZ_IDB格式/'
        # self.tmp_file = '/incam/server/site_data/scripts/zl/tmp/get_idb_path.txt'
        self.tmp_file = '/tmp/get_idb_path'

    def get_idb(self):
        odb_key = self.calculate_md5(odb_path)
        print(odb_key)
        # jobname = odb_path.split('/')[-1].replace('.tgz', '')
        # # 查询表中对应的idb key
        # sql = "select idb_md5_key from hdi_engineering.incam_output_tgz_info where jobname='%s' and odb_md5_key='%s'" % (jobname, odb_key)
        # my_sql = MySQL_DB.MySQL()
        # my_sql.MYSQL_CONNECT()
        # data = my_sql.SELECT_DIC(my_sql.dbc, sql)
        # my_sql.DB_CLOSE(my_sql.dbc)
        # if data:
        #     idb_md5_key = data[0].get('idb_md5_key')
        # for root, dirs, files in os.walk(self.idb_dir):
        #     for file in files:
        #         md5_key = self.calculate_md5(self.idb_dir + file)
        #         if md5_key == idb_md5_key:
        #             return self.idb_dir + file
        # return None
    @classmethod
    def calculate_md5(cls, file_path):
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:  # 以二进制读取模式打开文件
            for chunk in iter(lambda: f.read(4096), b""):  # 读取文件，每次4096字节
                md5.update(chunk)  # 更新哈希值
        return md5.hexdigest()  # 返回十六进制的哈希值


if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    odb_path = ' '.join(sys.argv[1:])
    # print('+' * 10)
    # print(sys.argv)
    # print(odb_path)
    # print('+' * 10)
    getIdbByOdbPath = GetIdbByOdbPath()
    idb_path = getIdbByOdbPath.get_idb()
    print(idb_path)
    # if idb_path:
    #     with open(getIdbByOdbPath.tmp_file, 'w') as f:
    #         f.write(idb_path)
