#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:RenameHooksDirUnderUser.py
   @author:zl
   @time: 2025/1/24 11:49
   @software:PyCharm
   @desc:
"""
import datetime
import os


def renameHooksDirUnderUser():
    user_root = '/incam/server/users/'
    log_file = os.path.join(os.path.dirname(__file__), 'RenameHooksDirUnderUser_log')
    logs = []
    for user in os.listdir(user_root):
        for dir in os.listdir(os.path.join(user_root, user)):
            # print(dir)
            if dir == 'hooks':
                src, dst = os.path.join(user_root, user, dir), os.path.join(user_root, user, dir + '_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
                # src, dst = os.path.join(user_root, user, dir), os.path.join(user_root, user, 'hooks')
                # print(src, dst)
                os.rename(src, dst)
                logs.append('rename %s -- > %s' % (src, dst))
    # print(logs)
    logs.append('Execution completed ---%s\n' % datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    with open(log_file, 'a') as writer:
        writer.write("\n".join(logs))


if __name__ == '__main__':
    renameHooksDirUnderUser()
