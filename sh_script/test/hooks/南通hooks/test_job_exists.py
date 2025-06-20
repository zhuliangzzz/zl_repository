#!/usr/bin/env python
# -*- coding: utf-8 -*-
__credits__ = u"""启动云incam6.0 导入有旋转的tgz """

import os
import sys
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
    
import paramiko

# 远程主机的 IP 地址和端口
hostname = '172.20.218.191'
port = 22

# SSH 用户名和密码
username = 'Incam'
password = 'incam'

remote_command = 'cd /data2/incamp_db1/jobs;ls |grep h75804git71b1'

# 创建 SSH 客户端对象
client = paramiko.SSHClient()
# 允许连接不在 known_hosts 文件中的主机
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# 建立 SSH 连接
client.connect(hostname, port, username, password)
# 执行远程命令
stdin, stdout, stderr = client.exec_command(remote_command)

# 获取命令输出
output = stdout.read() + stderr.read()
print(output)