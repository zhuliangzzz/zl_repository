#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:IncrementBackup.py
   @author:zl
   @time: 2025/1/3 17:55
   @software:PyCharm
   @desc:
   增量备份
"""
import datetime
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import threading
import time

from Queue import Queue
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import GetData
import MySQL_DB

class IncrementBackup(object):
    def __init__(self):
        self.host = socket.gethostname()
        self.ip = socket.gethostbyname(socket.gethostname())
        self.my_sql = MySQL_DB.MySQL()
        self.my_sql.MYSQL_CONNECT()
        self.getDATA = GetData.Data()
        self.source_dir, self.backup_dir, self.diff_time = None, None, None
        self.num_threads = 10
        # self.log_file = os.path.join(os.path.dirname(__file__), 'backup_log')
        self.log_file = os.path.join('/tmp/zl/', 'backup_log')
        self.logs = []
        self.date_dir = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        try:
            data = json.load(open(os.path.join(os.path.dirname(__file__), 'increment_config')))
            # job存放路径
            self.source_dir = data.get('job_path').encode('utf8')
            # job备份路径
            self.backup_dir = data.get('job_backup_path').encode('utf8')
            # print(self.job_backup_path)
            if 'ntincam' in self.host:
                self.source_dir = data.get('nt_job_path').encode('utf8')
        except Exception as e:
            self.logs.append(str(e))
            self.backup_dir = '/tmp/zl/'
        finally:
            self.log_file = os.path.join(self.backup_dir, 'backup_log')
            self.schedule_backup()

    # 备份文件夹
    def backup_folder(self, folder_path):
        try:
            # 构建目标路径
            jobname = os.path.basename(folder_path)
            # dest_file_path = os.path.join(self.backup_dir, jobname)
            dest_file_path = os.path.join(self.backup_dir, jobname)
            self.copy_dir(folder_path)
            # print(f"文件夹 {folder_path} 已备份并打包成 {dest_file_path}")
            # print(u"文件夹 %s 已备份到 %s"% (folder_path, dest_file_path))
            self.logs.append("文件夹 %s 已备份到 %s"% (folder_path, dest_file_path))
        except Exception as e:
            # print(f"备份文件夹 {folder_path} 时出错: {e}")
            # print(u"备份文件夹 %s 时出错: %s" % (folder_path, e))
            self.logs.append("备份文件夹 %s 时出错: %s" % (folder_path, e))

    # 线程池中的工作函数
    def worker(self, q):
        while True:
            folder_path = q.get()
            if folder_path is None:
                break
            try:
                self.backup_folder(folder_path)
            finally:
                q.task_done()

    # 获取所有文件夹并进行备份
    def backup_folders(self):
        folder_list = [os.path.join(self.source_dir, d) for d in os.listdir(self.source_dir) if
                       os.path.isdir(os.path.join(self.source_dir, d))]

        # 创建队列和线程
        queue = Queue()
        # threads = []
        # # 启动线程池
        # for _ in range(self.num_threads):
        #     t = threading.Thread(target=self.worker, args=(queue,))
        #     t.start()
        #     threads.append(t)

        # 将文件夹备份任务添加到队列
        for folder in folder_list:
            jobname = os.path.basename(folder)
            if len(jobname) != 13:
                continue
            # 20250110 判断保存时间
            # 判断时间差
            job_time = None
            if os.path.exists(os.path.join(self.source_dir, jobname + '/misc/info')):
                with open(os.path.join(self.source_dir, jobname + '/misc/info'), 'r') as r:
                    content = r.readlines()
                for line in content:
                    if line.startswith('SAVE_DATE'):
                            save_date = line.strip().split('=')[1]
                            # 将给定的日期和时间转换为 datetime 对象
                            dt = datetime.datetime.strptime(save_date, "%Y%m%d.%H%M%S")
                            # 计算时间戳
                            # job_time = int(dt.timestamp())
                            job_time = time.mktime(dt.timetuple())
            if job_time is None:
                e = '无法获取料号%s的info保存时间' % jobname
                self.logs.append(e)
                continue
            # 2024.12.31以后的进行备份
            begin_time = time.mktime(datetime.datetime(2024, 12, 31, 0, 0, 0, 0).timetuple())
            if job_time < begin_time:  # 时间节点之前的跳过
                continue
            if not os.path.exists(os.path.join(self.backup_dir, jobname)):
                queue.put(folder)
            else:
                lock_info = self.getJOB_LockInfo(jobname, dataType='locked_log')
                key_array = sorted(lock_info.keys(), reverse=True)
                check_save_log = False
                for unlock_time in key_array:
                    if len(lock_info[unlock_time]["unlock"]) != 0:
                        for lock_i, lock_detail in enumerate(lock_info[unlock_time]["unlock"]):
                            # unlock_steps = lock_detail['step']
                            unlock_layers = lock_detail['layers']
                            lock_steps = []
                            lock_layers = []
                            for lock_time in key_array:
                                if len(lock_info[lock_time]["lock_add"]) != 0:
                                    for lock_i, lock_detail in enumerate(lock_info[lock_time]["lock_add"]):
                                        lock_steps = lock_detail['step']
                                        lock_layers = lock_detail['layers']

                                if lock_steps and lock_layers and \
                                        int(lock_time) > int(unlock_time) and \
                                        abs(int(unlock_time) - time.time()) < 60 * 60 * 24 * 3:
                                    if set(lock_layers) & set(unlock_layers):
                                        check_save_log = True
                                        break

                            if check_save_log:
                                break
                    if check_save_log:
                        break
                if check_save_log:
                    save_log_path = "%s/user/save_log" % os.path.join(self.source_dir, jobname)
                    arraylist_modify_layer = []
                    if os.path.exists(save_log_path):
                        # print(jobname, save_log_path)
                        # arraylist.append(jobname)
                        lines = file(save_log_path).readlines()
                        check_modify = False
                        for line in lines:
                            if "Created" in line:
                                check_modify = False
                            if "Deleted" in line:
                                check_modify = False
                            if "Modifier" in line:
                                res = re.findall("(202\d/\d{2}/\d{2} \d{2}:\d{2}:\d{2})", line)
                                # print(res)
                                if res:
                                    # print(res)
                                    if res[0] > time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(int(unlock_time))):
                                        check_modify = True

                            if check_modify:
                                if "LAYER" in line:
                                    arraylist_modify_layer.append(line.split("-->")[-1])
                    if arraylist_modify_layer:
                        matrixinfo = self.get_erp_job_matrixinfo(jobname)
                        if not matrixinfo:
                            continue
                        step_list, inner_layers, outer_layers, drill_layers, board_layers = self.get_job_matrix(matrixinfo)
                        all_normal_layers = inner_layers + outer_layers + drill_layers + board_layers
                        modify_normal_layers = []
                        for layer_info in arraylist_modify_layer:
                            for layer in layer_info.split(","):
                                if layer.strip() in all_normal_layers:
                                    # print(jobname, layer.strip())
                                    if layer.strip() not in modify_normal_layers:
                                        modify_normal_layers.append(layer.strip())
                        if modify_normal_layers:
                            queue.put(folder)
        # 等待所有任务完成
        print(queue.qsize())

        # 等待所有线程完成
        # for i in range(self.num_threads):
        #     queue.put(None)
        # for t in threads:
        #     t.join()

        # if not os.path.exists(os.path.join(self.backup_dir, self.date_dir)):
        #     os.makedirs(os.path.join(self.backup_dir, self.date_dir))
        # shutil.move(self.tmp_dir, os.path.join(self.backup_dir, self.date_dir))
        # if self.logs:
        #     self.logs.append("本次备份任务完成 %s" % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        #     # print(self.logs)
        #     with open(self.log_file, 'a') as log:
        #         log.write('\n'.join(self.logs))

    #
    def copy_dir(self, source):
        # archive_name = os.path.basename(source)
        # dest = os.path.join(self.backup_dir, archive_name)
        dest = self.backup_dir
        # 定义命令和参数
        rsync_command = ["rsync", "-avz", "--delete", source, dest]
        # 创建子进程
        process = subprocess.Popen(rsync_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # 获取命令的输出和错误信息
        output, error = process.communicate()
        # 获取命令的退出状态码
        # exit_code = process.returncode
        # print(output, error)
        self.logs.append(str(output))


    def schedule_backup(self):
        self.backup_folders()

    def get_job_matrix(self, m_info):

        inner_layers = []
        outer_layers = []
        drill_layers = []
        board_layers = []
        other_layers = """blue-c
        blue-s
        blue_c
        blue_s
        blue_cs
        ty-c
        ty-s
        sgt-c
        sgt-s
        gold-c
        gold-s
        linemask-c
        linemask-s
        etch-c
        etch-s
        xlym-c
        xlym-s
        linek-c
        linek-s
        linek-c-1
        linek-s-1
        linek-c-2
        linek-s-2
        lp
        """
        other_layers = [x.strip() for x in other_layers.split("\n")]

        step_list = m_info['gCOLstep_name']
        layer_list = m_info['gROWname']
        for row in m_info['gROWrow']:
            num = m_info['gROWrow'].index(row)
            if "-ls" in m_info['gROWname'][num]:
                m_info['gROWname'][num] = m_info['gROWname'][num].split("-")[0]

            if m_info['gROWcontext'][num] == 'board' or m_info['gROWname'][num] in other_layers:
                board_layers.append(m_info['gROWname'][num])
            if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'drill':
                drill_layers.append(m_info['gROWname'][num])

            # 翟鸣通知增加铝片 导气板 树脂塞孔20241213 by lyh
            if m_info['gROWlayer_type'][num] == 'drill':
                if m_info['gROWname'][num] in ['sz.lp', 'sz...dq', "ww"] or \
                        re.match("^sz.*\.lp$|^sz.*\.\.\.dq$", m_info['gROWname'][num]) or \
                        re.match("^dld\d{1,2}-\d{1,2}$", m_info['gROWname'][num]):
                    drill_layers.append(m_info['gROWname'][num])

            if m_info['gROWname'][num] in ["ww"] or \
                    re.match("^dld\d{1,2}-\d{1,2}$", m_info['gROWname'][num]):
                drill_layers.append(m_info['gROWname'][num])

            if m_info['gROWcontext'][num] == 'board' and m_info['gROWside'][num] == 'inner':
                inner_layers.append(m_info['gROWname'][num])

            elif m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'signal' and (
                    m_info['gROWside'][num] == 'top' or m_info['gROWside'][num] == 'bottom'):
                outer_layers.append(m_info['gROWname'][num])

        # 周涌通知 外层盖孔资料需排除掉 20221117 by lyh
        inner_layers = [layer for layer in inner_layers
                        if layer.split("-")[0] not in outer_layers]

        return step_list, inner_layers, outer_layers, drill_layers, board_layers

    def get_erp_job_matrixinfo(self, jobname):
        sql = "select * from hdi_engineering.incam_job_layer_info where job_name = '{0}'".format(jobname)
        datainfo = self.my_sql.SELECT_DIC(self.my_sql.dbc, sql)
        dic_layer_info = {}
        if datainfo:
            try:
                dic_layer_info = json.loads(datainfo[0]["layer_info"], encoding='utf8')
            except:
                dic_layer_info = {}

        return dic_layer_info

    def getJOB_LockInfo(self, jobname, dataType='locked_info'):
        """
        从数据库中获取料号的锁记录
        :param dataType: 获取的数据类型（status:locked_info log:locked_log）
        :return:dict
        """
        lockData = self.getLock_Info(jobname)
        try:
            return json.loads(lockData[dataType], encoding='utf8')
        except:
            # print u'传入的数据参数异常'
            return {}

    def getLock_Info(self, jobname):
        sql = """select * from  hdi_engineering.job_lock_data jld where jld.job_name = '%s'""" % jobname
        result = self.my_sql.SELECT_DIC(self.my_sql.dbc, sql)
        if not result:
            return []

        # --一个料号仅一条数据
        result_dict = result[0]

        return result_dict


if __name__ == "__main__":
    IncrementBackup()
