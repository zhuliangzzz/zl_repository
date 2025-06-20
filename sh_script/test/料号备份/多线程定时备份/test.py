#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:test.py
   @author:zl
   @time: 2025/1/3 9:19
   @software:PyCharm
   @desc:
"""
import os
import shutil
import tarfile
import threading
from concurrent.futures import ThreadPoolExecutor


# 备份文件的函数
def backup_file(file_path, backup_dir):
    try:
        # 确保备份目录存在
        os.makedirs(backup_dir, exist_ok=True)
        # 构建目标文件的完整路径
        dest_file_path = os.path.join(backup_dir, os.path.basename(file_path))
        # 如果文件已存在，则删除旧文件
        if os.path.exists(dest_file_path):
            os.remove(dest_file_path)
        # 复制文件
        shutil.copy2(file_path, dest_file_path)
        print(f"文件 {file_path} 已备份到 {dest_file_path}")
    except Exception as e:
        print(f"备份文件 {file_path} 时出错: {e}")


def tar_tgz(jobname):
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    output_file = os.path.join(backup_dir, jobname + '.tgz')
    try:
        tar = tarfile.open(output_file, "w:gz")
        for root, dirs, files in os.walk(jobname):
            for file in files:
                file_path = os.path.join(root, file)
                tar.add(file_path)
        tar.close()
    except IOError as e:
        os.chmod(e.filename, 0o664)
        tar_tgz(jobname)


# 执行备份任务
def perform_backup(source_dir):
    # 获取源目录中的所有文件
    file_list = [f for f in os.listdir(source_dir) if
                 os.path.isdir(os.path.join(source_dir, f))]

    # 创建一个线程池，最大线程数为10
    with ThreadPoolExecutor(max_workers=10) as executor:
        # 将文件备份任务提交给线程池
        for file_path in file_list:
            print(file_path)
            os.chdir(source_dir)
            executor.submit(tar_tgz, file_path)

    print("本次备份任务完成。")


# 定时执行备份任务
def schedule_backup(source_dir, backup_dir):
    perform_backup(source_dir)
    # 每隔1小时执行一次备份任务
    threading.Timer(3600, schedule_backup, args=(source_dir, backup_dir)).start()


if __name__ == "__main__":
    source_dir = r'D:\myfiles\zc_scripts'  # 源目录路径
    backup_dir = r'F:\backup'  # 备份目录路径
    schedule_backup(source_dir, backup_dir)
