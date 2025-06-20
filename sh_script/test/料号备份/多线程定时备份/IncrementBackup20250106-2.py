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
import json
import os
import socket
import sys
import tarfile
from multiprocessing import Pool

# import MySQL_DB


class IncrementBackup(object):
    def __init__(self):
        self.host = socket.gethostname()
        self.ip = socket.gethostbyname(socket.gethostname())
        self.source_dir, self.backup_dir, self.diff_time = None, None, None
        self.count = 0
        try:
            data = json.load(open('increment_config'))
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
            print(e)
        self.schedule_backup()

    # 备份文件夹并打包成tgz
    def backup_folder(self, folder_path):
        os.chdir(self.source_dir)
        try:
            # 确保备份目录存在
            os.makedirs(self.backup_dir, exist_ok=True)
            # 构建目标压缩文件的完整路径
            archive_name = os.path.basename(folder_path) + ".tgz"
            dest_file_path = os.path.join(self.backup_dir, archive_name)

            # 如果压缩文件已存在，则删除旧压缩文件
            if os.path.exists(dest_file_path):
                os.remove(dest_file_path)

            self.tar_tgz(os.path.basename(folder_path))
            # print(f"文件夹 {folder_path} 已备份并打包成 {dest_file_path}")
            print("文件夹%s已备份并打包成%s" % (folder_path, dest_file_path))
            self.count += 1
        except Exception as e:
            # print(f"备份文件夹 {folder_path} 时出错: {e}")
            print("备份文件夹%s时出错:%s" % (folder_path, e))
        if self.count > 50:
            sys.exit()

    def tar_tgz(self, jobname):
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        output_file = os.path.join(self.backup_dir, jobname + '.tgz')
        try:
            tar = tarfile.open(output_file, "w:gz")
            for root, dirs, files in os.walk(jobname):
                for file in files:
                    file_path = os.path.join(root, file)
                    tar.add(file_path)
            tar.close()
        except IOError as e:
            os.chmod(e.filename, 0o664)
            self.tar_tgz(jobname)

    # 获取所有文件夹并进行备份
    def backup_folders(self):
        # 创建一个线程池，最大线程数为10
        folder_list = [os.path.join(self.source_dir, d) for d in os.listdir(self.source_dir) if
                       os.path.isdir(os.path.join(self.source_dir, d))]
        print(folder_list)
        pool = Pool(processes=10)
        # with Pool(processes=10) as pool:
        #     pool.starmap(self.backup_folder, folder_list)
        try:
            pool.map(self.backup_folder, [(folder) for folder in folder_list])
        finally:
            pool.close()
            pool.join()
        print("本次备份任务完成")

    # 每隔1小时执行一次备份任务
    def schedule_backup(self):
        self.backup_folders()


if __name__ == "__main__":
    IncrementBackup()
