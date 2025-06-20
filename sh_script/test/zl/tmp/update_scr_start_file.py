#!/usr/bin/env python
# -*- coding: utf-8 -*-
__credits__ = u"""更新配置文件V1.1.0 """

import os
import sys
import time
import filecmp
import pexpect
import socket

localip = socket.gethostbyname_ex(socket.gethostname())
log_path = "/windows/inplan/inplan/cam_log/record.log"
# if os.environ.get("INCAM_PRODUCT", None):

for filename in ["auto.win"]:
    # if filename == "auto.win":
    f1 = "/etc/{0}".format(filename)
    # else:
    #     f1 = "{0}/app_data/{1}".format(os.environ["INCAM_PRODUCT"], filename)
    f2 = "/incam/server/site_data/hooks/{0}".format(filename)
    if not filecmp.cmp(f1, f2) and os.path.exists(f1) and os.path.exists(f2):

        if os.path.exists(log_path):
            strftime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            with open(log_path, "a") as f:
                f.write("start--->{0} {1}\n".format(localip, strftime))

        child = pexpect.spawn("su -")
        child.expect(u"密码：".encode("utf8"), timeout=2)
        child.sendline("VGT-InCAM$.")

        child.expect(u"# ".encode("utf8"), timeout=2)
        child.sendline("cp -rf {0} {1}".format(f2, f1))
        time.sleep(0.1)
        child.sendline("y")

        child.expect(u"# ".encode("utf8"), timeout=2)
        child.sendline("/sbin/service autofs restart")
        time.sleep(5)

        child.expect(u"# ".encode("utf8"), timeout=2)
        child.sendline("exit")

        if filecmp.cmp(f1, f2):
            if os.path.exists(log_path):
                strftime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                with open(log_path, "a") as f:
                    f.write("end--->{0} {1}\n".format(localip, strftime))
