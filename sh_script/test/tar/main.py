#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:main.py
   @author:zl
   @time: 2024/11/13 15:21
   @software:PyCharm
   @desc:
"""
import os
import tarfile


def create_tgz(folder_path, output_file):
        # tar = tarfile.open(output_file, "w:gz")
        os.chdir('/incampro/incamp_db1/jobs/')
        tar = tarfile.open(output_file, "w:gz")

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                tar.add(file_path)

        tar.close()


create_tgz(r'c18302gf824a1-zltest', r"/id/workfile/zl/tgz/c18302gf824a1-zltest.tgz")