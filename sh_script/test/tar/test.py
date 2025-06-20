#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:UpdateOutputTgzEffective.py
   @author:zl
   @time: 2024/12/11 18:51
   @software:PyCharm
   @desc:
   更新hdi_engineering.incam_output_tgz_info表中id_effective胡值
   定时任务获取路径下odb文件，根据odb文件的key得到idb文件，并将字段id_effective设置为0
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

class UpdateOutputTgzEffective(object):
    def __init__(self):
        self.odb_path = 'E://testtgz/'
        self.idb_dir = '//192.168.2.172/GCfiles/全套TGZ_IDB格式/'

    def check(self):
        my_sql = MySQL_DB.MySQL()
        my_sql.MYSQL_CONNECT()
        for root, dirs, files in os.walk(self.odb_path):
            print(root, dirs)
            for file in files:

                if not file.endswith('.tgz'):
                    continue
                # print(file)
                odb_key = self.calculate_md5(os.path.join(root, file))
                jobname = file.replace('.tgz', '')[:13]
                # 如果odb对应有is_effective=1的数据，则不进行找idb
                # sql = "select id from hdi_engineering.incam_output_tgz_info where jobname='%s' and odb_md5_key='%s' and is_effective = '1'" % (jobname, odb_key)
                sql = "select id from hdi_engineering.incam_output_tgz_info where jobname='c18302gf824a1-zltest' and odb_md5_key='e95f72fd493fcc28ce2bb6d8df984ad6' and is_effective = '1'"
                data = my_sql.SELECT_DIC(my_sql.dbc, sql)
                if data:
                    print('yes')
                    continue
                flag = False
                print('continue')
                # for idb_root, idb_dirs, idb_files in os.walk(self.idb_dir):
                #     if flag:
                #         break
                #     for idb_file in idb_files:
                #         idb_name = idb_file.rsplit('_', 2)[0]
                #         if idb_name == jobname:
                #             idb_key = self.calculate_md5(idb_root + idb_file)
                #             # 查询表中对应的idb key
                #             # sql = "select id from hdi_engineering.incam_output_tgz_info where jobname='%s' and odb_md5_key='%s' and idb_md5_key='%s'" % (jobname, odb_key, idb_key)
                #             sql = "select id from hdi_engineering.incam_output_tgz_info where jobname='c18302gf824a1-zltest' and odb_md5_key='e95f72fd493fcc28ce2bb6d8df984ad6' and idb_md5_key='e86a6227ea8c0fe34af8d8a76577759c'"
                #             data = my_sql.SELECT_DIC(my_sql.dbc, sql)
                #             if data:
                #                 for d in data:
                #                     # 查询表中对应的idb key
                #                     sql = "update hdi_engineering.incam_output_tgz_info set is_effective = '1' where id=%s"
                #                     my_sql.SQL_EXECUTE(my_sql.dbc, sql, d['id'])
                #                     flag = True
        my_sql.DB_CLOSE(my_sql.dbc)
    @classmethod
    def calculate_md5(cls, file_path):
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:  # 以二进制读取模式打开文件
            for chunk in iter(lambda: f.read(4096), b""):  # 读取文件，每次4096字节
                md5.update(chunk)  # 更新哈希值
        return md5.hexdigest()  # 返回十六进制的哈希值


if __name__ == '__main__':
    updateOutputTgzEffective = UpdateOutputTgzEffective()
    updateOutputTgzEffective.check()