#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:test.py
   @author:zl
   @time: 2024/11/1 17:23
   @software:PyCharm
   @desc:
"""
import os
import re
import pwd
import threading
from Queue import Queue


class Test():
    def __init__(self):
        self.db1 = '/data2/incamp_db1/jobs'
        self.num_threads = 10
        self.job_user = []
        self.root_job = []
        self.source_file = '/data3/backup_linshi_jobs/clear_temp_and_back_layer.log'
        self.log_file = '/windows/174.db/test.log'

    def run(self):
        # check_jobs = set()
        # with open(self.source_file) as f:
        #     readlines = f.readlines()
        # for line in readlines:
        #     res = re.search('Job\s(\S*)\scleaning completed', line)
        #     if res:
        #         check_jobs.add(res.group(1))
        check_jobs = os.listdir(self.db1)
        check_jobs = list(filter(lambda check_job: len(check_job) == 13, check_jobs))
        # check_jobs = list(check_jobs)
        # 创建队列和线程
        queue = Queue()
        threads = []
        # 启动线程池
        for _ in range(self.num_threads):
            t = threading.Thread(target=self.worker, args=(queue,))
            t.start()
            threads.append(t)
        # 添加元素
        for check_job in check_jobs:
            lock_json = os.path.join(self.db1, check_job, 'user', '%s_job_lock.json' % check_job)
            if os.path.exists(lock_json):
                queue.put(lock_json)

        # 等待所有任务完成
        queue.join()

        # 等待所有线程完成
        for i in range(self.num_threads):
            queue.put(None)
        for t in threads:
            t.join()
        with open(self.log_file, 'a') as f:
            f.write('\n'.join(self.job_user))
            f.write('\n')
            f.write('\n'.join(self.root_job))

    # 线程池中的工作函数
    def worker(self, q):
        while True:
            folder_path = q.get()
            if folder_path is None:
                break
            try:
                self.get_file_owner(folder_path)
            finally:
                q.task_done()

    def get_file_owner(self, filepath):
        filename = os.path.basename(filepath)
        jobname = filename.split('_')[0]
        # 获取文件的状态
        file_stat = os.stat(filepath)
        # 获取用户ID
        uid = file_stat.st_uid
        # 使用pwd模块将用户ID转换为用户名
        try:
            username = pwd.getpwuid(uid).pw_name
            self.job_user.append('%s %s-->%s' % (jobname, filename, username))
            if username == 'root':
                self.root_job.append(jobname)
        except KeyError:
            # 如果无法找到对应的用户名，可能是因为用户ID不存在或有问题
            self.job_user.append('%s %s-->%s' % (jobname, filename, ''))


if __name__ == '__main__':
    test = Test()
    test.run()
