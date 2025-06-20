#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2022/10/12
# @Revision     :    1.0.0
# @File         :    check_job_hct_step_time.py
# @Software     :    PyCharm
# @Usefor       :    用于在打开料号时提醒用户
# ---------------------------------------------------------#

import os
import platform
import re
import sys
from PyQt4 import QtCore, QtGui
import time

# --加载相对位置，以实现InCAM与Genesis共用
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genCOM_26 as genCOM
from messageBox import msgBox


class GetHctTime(object):
    def __init__(self,job_name):
        self.job_name = job_name
        PRODUCT = os.environ.get('INCAM_PRODUCT', None)
        # print PRODUCT
        if platform.system() == "Windows":
            self.userDir = "%s/fw/jobs/%s/user" % (os.environ.get('GENESIS_DIR', 'D:/genesis'), self.job_name)
        else:
            self.userDir = os.environ.get('JOB_USER_DIR', None)
            # === input_tgz 程序引用此程序时 JOB_USER_DIR 可能延续上一个料号
            if self.userDir and '/' + self.job_name + '/' not in self.userDir:
                self.userDir = None
            if PRODUCT and not self.userDir:
                # === 开启了软件，但是没有打开料号时，无JOB_USER_DIR
                job_dir = os.popen(PRODUCT + '/bin/dbutil path jobs ' + self.job_name).readline().strip('\n')
                # print job_dir
                self.userDir = str(job_dir) + '/user'
                # print '===' * 10
                # print self.userDir
            if not PRODUCT and not self.userDir:
                # --Linux环境下网络版genesis没有定义INCAM_PRODUCT环境变量
                self.userDir = "%s/fw/jobs/%s/user" % (os.environ.get('GENESIS_DIR', '/genesis'), self.job_name)

        self.job_path_dir = os.path.dirname(self.userDir)
        print 'JOB_PATH:%s' % self.job_path_dir
        self.hct_step_dir = "%s/steps/hct-coupon" % self.job_path_dir
        if os.path.exists(self.hct_step_dir):
            print 'hct-coupon exist'
            self.get_step_time(self.hct_step_dir)
        else:
            print 'hct-coupon not_exist'

    def get_step_time(self, input_path):
        m_time = (os.path.getmtime(input_path))

        t_time = time.strftime("%Y%m%d%H%M%S", time.localtime(m_time))
        show_time = str(time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(m_time)))
        print show_time
        int_time = int(t_time)
        if int_time < 20221010000000:
            text = "检测到hct的时间为:%s，请更新hct coupon保证内层有铜!" % show_time
            msg_box = msgBox()
            msg_box.warning(self, '警告', '%s' % text, QtGui.QMessageBox.Ok)


# # # # --程序入口
if __name__ == "__main__":
    mapp = QtGui.QApplication(sys.argv)
    job_name = sys.argv[1]
    app = GetHctTime(job_name)


