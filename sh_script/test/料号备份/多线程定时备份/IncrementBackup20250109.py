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
import shutil
import socket
import threading
import Queue

# import MySQL_DB


class IncrementBackup(object):
    def __init__(self):
        self.host = socket.gethostname()
        self.ip = socket.gethostbyname(socket.gethostname())
        self.source_dir, self.backup_dir, self.diff_time = None, None, None
        self.num_threads = 10
        self.log_file = os.path.join(os.path.dirname(__file__), 'backup_log')
        self.logs = []
        self.date_dir = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        try:
            data = json.load(open(os.path.join(os.path.dirname(__file__), 'increment_config')))
            # job存放路径
            # self.source_dir = data.get('job_path').encode('utf8')
            self.source_dir = data.get('job_path').encode('utf8')
            # job备份路径
            # self.backup_dir = data.get('job_backup_path').encode('utf8')
            self.backup_dir = data.get('job_backup_path').encode('utf8')
            # print(self.job_backup_path)
            if 'ntincam' in self.host:
                # self.source_dir = data.get('nt_job_path').encode('utf8')
                self.source_dir = data.get('nt_job_path').encode('utf8')
        except Exception as e:
            self.logs.append(str(e))
        self.tmp_dir = os.path.join('/tmp/zl/tmp', self.date_dir)
        self.schedule_backup()

    # 备份文件夹并打包成tgz
    def backup_folder(self, folder_path):
        # os.chdir(self.source_dir)
        try:
            # 构建目标路径
            archive_name = os.path.basename(folder_path)
            dest_file_path = os.path.join(os.path.join(self.backup_dir, self.date_dir), archive_name)
            self.copy_dir(folder_path)
            # print(f"文件夹 {folder_path} 已备份并打包成 {dest_file_path}")
            self.logs.append("文件夹 %s 已备份到 %s"% (folder_path, dest_file_path))
        except Exception as e:
            # print(f"备份文件夹 {folder_path} 时出错: {e}")
            self.logs.append("备份文件夹 %s 时出错: %s" % (folder_path, e))

    # 线程池中的工作函数
    def worker(self, q):
        while not q.empty():
            folder_path = q.get()
            if folder_path is None:
                break
            self.backup_folder(folder_path)
            q.task_done()

    # 获取所有文件夹并进行备份
    def backup_folders(self):
        folder_list = [os.path.join(self.source_dir, d) for d in os.listdir(self.source_dir) if
                       os.path.isdir(os.path.join(self.source_dir, d))]

        # 创建队列和线程池
        queue = Queue.Queue()
        threads = []



        # 将文件夹备份任务添加到队列
        for folder in folder_list[:40]:
            if len(os.path.basename(folder)) != 13:
                continue
            queue.put(folder)

        # 启动线程池
        for _ in range(self.num_threads):
            t = threading.Thread(target=self.worker, args=(queue,))
            t.start()
            threads.append(t)

        # 等待所有线程完成
        for t in threads:
            t.join()

        # if not os.path.exists(os.path.join(self.backup_dir, self.date_dir)):
        #     os.makedirs(os.path.join(self.backup_dir, self.date_dir))
        # shutil.move(self.tmp_dir, os.path.join(self.backup_dir, self.date_dir))
        self.logs.append("本次备份任务完成 %s" % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print(self.logs)
        with open(self.log_file, 'a') as log:
            log.write('\n'.join(self.logs))

    #
    def copy_dir(self, source):
        archive_name = os.path.basename(source)
        tmp_dir = os.path.join(self.tmp_dir, archive_name)
        print(source, tmp_dir)
        try:
            shutil.copytree(source, tmp_dir)
        except IOError as e:
            os.chmod(e.filename, 0o664)
            self.copy_dir(source)

    def schedule_backup(self):
        self.backup_folders()


if __name__ == "__main__":
    IncrementBackup()
