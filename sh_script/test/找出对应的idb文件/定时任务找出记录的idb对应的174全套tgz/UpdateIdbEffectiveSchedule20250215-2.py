#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:UpdateIdbEffectiveSchedule.py
   @author:zl
   @time: 2025/1/13 8:51
   @software:PyCharm
   @desc:
   20250215 先判断时间是否匹配 不匹配再计算md5
"""
import datetime
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


class UpadateIdbEffectiveSchedule(object):
    def __init__(self):
        self.my_sql = MySQL_DB.MySQL()
        self.my_sql.MYSQL_CONNECT()
        self.odb_tgz_path = u'//192.168.2.174/GCfiles/HDI全套tgz'
        # self.odb_tgz_path = u'/windows/174.file/HDI全套tgz'
        self.logs = None
        # self.log_file = os.path.join(os.path.dirname(__file__), 'update_log')
        self.log_file = os.path.join('/tmp/zl/log', 'update_log')

    # 查询并更新effective值
    def UpdateIdbEffective(self):
        # jobdict
        jobdict = {}
        sql = "select id,jobname,odb_modify_time,odb_md5_key from hdi_engineering.incam_output_tgz_info order by id desc"
        results = self.my_sql.SELECT_DIC(self.my_sql.dbc, sql)
        for result in results:
            jobname = result['jobname']
            if jobname not in jobdict.keys():
                jobdict[jobname] = []
            jobdict[jobname].append({'id': result['id'], 'odb_md5_key': result['odb_md5_key'], 'odb_modify_time': result['odb_modify_time']})
        jobs, ids = [], []
        start_time = datetime.datetime.now()
        # 找每个jobname的odb_md5_key是否在tgz有对应的tgz
        for jobname, datas in jobdict.items():
            # 路径
            dir = jobname[1:4].upper() + u'系列'
            tgz_path = os.path.join(self.odb_tgz_path, dir, '%s.tgz' % jobname)
            if os.path.exists(tgz_path):
                tgz_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(tgz_path)).strftime('%Y-%m-%d %H:%M:%S')
                for data in datas:
                    id = data.get('id')
                    md5_key = data.get('odb_md5_key')
                    modify_time = data.get('odb_modify_time')
                    if tgz_mtime == modify_time:
                        jobs.append(jobname)
                        ids.append(id)
                        print('匹配到 -- ', id)
                        break
                    else:
                        print('检测到新文件：', jobname)
                        tgz_md5_key = self.calculate_md5(tgz_path)
                        if tgz_md5_key == md5_key:
                            jobs.append(jobname)
                            ids.append(id)
                            print('找到新id:', id)
                            break
            tgz_path = os.path.join(self.odb_tgz_path, dir, '%s-inn.tgz' % jobname)
            if os.path.exists(tgz_path):
                tgz_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(tgz_path)).strftime('%Y-%m-%d %H:%M:%S')
                for data in datas:
                    id = data.get('id')
                    md5_key = data.get('odb_md5_key')
                    modify_time = data.get('odb_modify_time')
                    if tgz_mtime == modify_time:
                        print('匹配到 -- ', id)
                        jobs.append(jobname)
                        ids.append(id)
                        break
                    else:
                        print('检测到新文件：', jobname)
                        tgz_md5_key = self.calculate_md5(tgz_path)
                        if tgz_md5_key == md5_key:
                            jobs.append(jobname)
                            ids.append(id)
                            print('找到新id:', id)
                            break
        # print(jobs,ids)
        if ids:
            # 把料号的is_effective重置为0 再把找到的id记录is_effective改为1
            # sql = "update hdi_engineering.incam_output_tgz_info set is_effective = '0' where jobname in (%s)" % ','.join(["'" + job + "'" for job in jobs])
            # self.my_sql.SQL_EXECUTE(self.my_sql.dbc, sql)
            # sql = "update hdi_engineering.incam_output_tgz_info set is_effective = '1' where id in (%s)" %  ','.join([str(id) for id in ids])
            # self.my_sql.SQL_EXECUTE(self.my_sql.dbc, sql)
            end_time = datetime.datetime.now()
            time_consume = end_time - start_time
            now = end_time.strftime('%Y-%m-%d %H:%M:%S')
            self.logs = "更新id: %s\n 本次更新有效记录完成(%s)： 更新数量%s 耗时%ss\n" % (','.join([str(id) for id in ids]), now, len(ids), time_consume)
        else:
            end_time = datetime.datetime.now()
            time_consume = end_time - start_time
            now = end_time.strftime('%Y-%m-%d %H:%M:%S')
            self.logs = "本次未检测到新料号(%s):  耗时%ss\n" % (now, time_consume)
        # with open(self.log_file, 'a') as log:
        #     log.write(self.logs)
        print(self.logs)
        self.my_sql.DB_CLOSE(self.my_sql.dbc)

    @classmethod
    def calculate_md5(cls, file_path):
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:  # 以二进制读取模式打开文件
            for chunk in iter(lambda: f.read(4096), b""):  # 读取文件，每次4096字节
                md5.update(chunk)  # 更新哈希值
        return md5.hexdigest()  # 返回十六进制的哈希值


if __name__ == '__main__':
    schedule = UpadateIdbEffectiveSchedule()
    schedule.UpdateIdbEffective()
