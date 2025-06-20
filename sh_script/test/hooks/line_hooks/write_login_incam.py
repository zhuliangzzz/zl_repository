#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import socket
import platform

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genCOM_26

log_file = '/id/workfile/login_hdi/job_lock.log'
if not os.path.exists(log_file):
    open(log_file, 'w').close()

try:
    jobName = sys.argv[1]
except:
    jobName = os.environ.get("JOB")

gen = genCOM_26.GEN_COM()
user_name = gen.getUser()

def execCmd(cmd):
    """
    封装执行命令的方法 ps aux|grep incam
    :return: 命令内容
    """
    r = os.popen(cmd)
    text = r.read()
    r.close()
    return text

host_name  = socket.gethostname()
host_ip = socket.gethostbyname(host_name)

# 执行cmd指令
send_mgs = "/incampro/release/bin/dbutil lock list by_job {0}".format(jobName)
get_check_type = execCmd(send_mgs)
# 打开后如果料号没有被check_out则直接退出，
if not get_check_type:
    sys.exit()

lock_job, lock_by_name = get_check_type.strip().split()

# 如果被check_out则判断是否被当前用户check_out, 只有被当前用户check的才写入文件
if lock_by_name == user_name:
    # 获取vnc窗口
    vnc_name = os.environ.get("VNCDISP")
    # 格式按照job, ip(主机名) job  192.168.25.7(hdilinux05)
    if vnc_name:
        log = lock_job + ' ' + user_name + ' ' + host_ip + vnc_name + '({0})'.format(host_name) + '\n'
    else:
        log = lock_job + ' ' + user_name + ' ' + host_ip + '({0})'.format(host_name) + '\n'

    with open(log_file, 'r') as f:
        readlines = f.readlines()

    exist_log = False
    for i, line in enumerate(readlines):
        if line.strip().split()[0] == jobName:
            readlines[i] = log
            exist_log = True
            break
    if exist_log:
        with open(log_file, 'w') as f:
            f.write(''.join(readlines))
    else:
        with open(log_file, 'a') as f:
            f.write(log)
