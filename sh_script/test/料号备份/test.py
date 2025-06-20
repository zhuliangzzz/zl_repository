#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:test.py
   @author:zl
   @time: 2024/12/30 9:26
   @software:PyCharm
   @desc:
"""
import datetime
import json
import os.path
import queue
import threading

job_backup_path = ''

tmp = {"diff_time": 3, "job_path": "C:/genesis/fw/jobs", "nt_job_path": "C:/genesis/fw/jobs", "job_backup_path": "D:/tmp"}

# print(tmp)
# print(json.dump(tmp, open('increment_config', 'w')))
# data = {}

def worker(q):
    while not q.empty():
        print(q.get() + 200)

if __name__ == '__main__':

    queue_queue = queue.Queue()
    for i in range(100000):
        queue_queue.put(i)

    threads = []
    for i in range(10):
        t = threading.Thread(target=worker, args=(queue_queue,))
        t.start()
        threads.append(t)

    for thread in threads:
        thread.join()

    print('end')