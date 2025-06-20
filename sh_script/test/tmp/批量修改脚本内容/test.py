#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:test.py
   @author:zl
   @time: 2025/1/17 14:01
   @software:PyCharm
   @desc:
"""
import os

search_word = '/workfile/film'
# search_word = 'QListWidget::Item'

search_root = '/incam/server/sys/scripts/'


def search_file():
    log, logs = [], {}
    for root, dirs, files in os.walk(search_root):
        if os.path.join(search_root, 'Logs') in root:
            continue
        for file in files:
            if os.path.isfile(os.path.join(root, file)):
                with open(os.path.join(root, file), 'r') as f:
                    lines = f.readlines()
                for line_no, line in enumerate(lines):
                    if search_word in line:
                        if os.path.join(root, file) not in logs.keys():
                            logs[os.path.join(root, file)] = []
                        logs[os.path.join(root, file)].append('%s: %s' % (line_no, line.strip()))
    logfile = os.path.join('/windows/174.file/HDI_INCMAPRO_JOB_DB', 'find_film_log.txt')
    if not os.path.exists('/windows/174.file/HDI_INCMAPRO_JOB_DB'):
        os.makedirs('/windows/174.file/HDI_INCMAPRO_JOB_DB')
    for key in logs.keys():
        log.append(key)
        log.extend(logs.get(key))
    with open(logfile, 'w') as w:
        w.write("\n".join(log))


if __name__ == '__main__':
    search_file()
