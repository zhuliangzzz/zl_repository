#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:GenerateJobListCheckFile.py
   @author:zl
   @time: 2025/1/15 19:37
   @software:PyCharm
   @desc:
   # 定时生成料号清单到路径指定文件内
   \\192.168.2.174\GCfiles\HDI_INCMAPRO_JOB_DB\nt_check_jobs
"""
import os


def GenerateJobListCheckFile():
    job_db = "/id/incamp_db1/jobs/"
    file_path = '/windows/174.file/HDI_INCMAPRO_JOB_DB/nt_check_jobs'
    jobs = os.listdir(job_db)
    jobs = filter(lambda job: len(job) == 13, jobs)
    file = 'db1_jobs_list'
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    rows = len(jobs) // 10 + 1 if len(jobs) % 10 else len(jobs) // 10
    joblist = [jobs[i * 10: (i + 1) * 10] for i in range(rows)]
    content = ""
    for row in joblist:
        content += '\t'.join(row) + '\n'
    with open(os.path.join(file_path, file), 'w') as writer:
        writer.write(content)


if __name__ == '__main__':
    GenerateJobListCheckFile()
