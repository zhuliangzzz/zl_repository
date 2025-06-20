#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:test2.py
   @author:zl
   @time: 2025/1/3 9:41
   @software:PyCharm
   @desc:
"""
import os
import tarfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


# 备份文件夹并打包成tgz
def backup_folder(folder_path, backup_dir):
    try:
        # 确保备份目录存在
        os.makedirs(backup_dir, exist_ok=True)
        # 构建目标压缩文件的完整路径
        archive_name = os.path.basename(folder_path) + ".tgz"
        dest_file_path = os.path.join(backup_dir, archive_name)

        # 如果压缩文件已存在，则删除旧压缩文件
        if os.path.exists(dest_file_path):
            os.remove(dest_file_path)

        # 打包文件夹成tgz
        with tarfile.open(dest_file_path, "w:gz") as tar:
            tar.add(folder_path, arcname=os.path.basename(folder_path))
        print(f"文件夹 {folder_path} 已备份并打包成 {dest_file_path}")
    except Exception as e:
        print(f"备份文件夹 {folder_path} 时出错: {e}")


# 获取所有文件夹并进行备份
def backup_folders(source_dir, backup_dir):
    folder_list = [os.path.join(source_dir, d) for d in os.listdir(source_dir) if
                   os.path.isdir(os.path.join(source_dir, d))]

    # 创建一个线程池，最大线程数为10
    with ThreadPoolExecutor(max_workers=10) as executor:
        # 将文件夹备份任务提交给线程池
        future_to_folder = {executor.submit(backup_folder, folder, backup_dir): folder for folder in folder_list}

        for future in as_completed(future_to_folder):
            folder = future_to_folder[future]
            try:
                future.result()
            except Exception as exc:
                print(f"备份文件夹 {folder} 生成时发生异常: {exc}")

    print("本次备份任务完成。")


# 每隔1小时执行一次备份任务
def schedule_backup(source_dir, backup_dir):
    while True:
        backup_folders(source_dir, backup_dir)
        print("等待1小时后再次执行备份...")
        time.sleep(3600)  # 等待1小时


if __name__ == "__main__":
    source_dir = r'D:\myfiles\zc_scripts'  # 源目录路径
    backup_dir = r'F:\backup'  # 备份目录路径
    schedule_backup(source_dir, backup_dir)