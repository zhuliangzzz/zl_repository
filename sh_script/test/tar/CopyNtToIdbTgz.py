#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CopyNtToIdbTgz.py
   @author:zl
   @time: 2024/12/11 17:30
   @software:PyCharm
   @desc:
   # 南通idb路径复制到172idb路径
"""
import os
import shutil
def copyNtToIdbTgz():
    source_dir = u'//172.28.30.8/全套tgz_idb格式'
    target_dir = u'//192.168.2.172/GCfiles/全套TGZ_IDB格式'

    # 确保目标文件夹存在
    # 复制文件
    for tgz in os.listdir(source_dir):
        shutil.copy2(os.path.join(source_dir, tgz), target_dir)
        os.unlink(os.path.join(source_dir, tgz))


if __name__ == '__main__':
    copyNtToIdbTgz()
