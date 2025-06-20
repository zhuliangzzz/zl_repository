#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2022/02/08
# @Revision     :    1.0.0
# @File         :    pre_move_check.py
# @Software     :    PyCharm
# @Usefor       :    参考netCheck.py的料号更改部分
# ---------------------------------------------------------#

import os
import platform
import sys
import json
from PyQt4 import QtCore, QtGui

from Packages import GetData

_header = {
    'description': '''
    -> 本程序主要服务于胜宏科技（惠州），任何其他团体或个人如需使用，必须经胜宏科技（惠州）相关负责
       人及作者的批准，并遵守以下约定；
    1> 本着尊重创作者的劳动成果，任何团体或个人在使用此程序的时候，均需要知会此程序的原始创作者；
    2> 在任何场合宣导、宣传，在任何文件、报告、邮件中提及本程序的全部或部分功能，均需要声明此程序的
       原始创作者；
    3> 在任何时候对本程序做部分修改或者是升级时，必须要保留文件的原始信息，包括原始文件名、创作者及
       联系方式、创作日期等信息，且不得删除程序中的源代码，只能进行注释处理；
'''
}

# --加载相对位置，以实现InCAM与Genesis共用
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genCOM_26 as genCOM

GEN = genCOM.GEN_COM()

from messageBox import msgBox

app = QtGui.QApplication(sys.argv)


class MainGen():
    """
    GENESIS、InPlan中相关操作
    """

    def __init__(self):
        # MainWindow.__init__(self, '')
        # super(MainGen, self).__init__('')
        self.JOB = os.environ.get('JOB', 's51912pr488a4')
        self.STEP = None
        self.changeNetLay = []
        self.job_lock = '%s_job_lock.json' % self.JOB
        print self.job_lock
        print 'x' * 40
        self.layer_list = []
        
        self.getDATA = GetData.Data()
        # pass
        PRODUCT = os.environ.get('INCAM_PRODUCT', None)
        if platform.system() == "Windows":
            self.userDir = "%s/fw/jobs/%s/user" % (os.environ.get('GENESIS_DIR', 'D:/genesis'), self.JOB)
        else:
            self.userDir = os.environ.get('JOB_USER_DIR', None)
            if not PRODUCT and not self.userDir:
                # --Linux环境下网络版genesis没有定义INCAM_PRODUCT环境变量
                self.userDir = "%s/fw/jobs/%s/user" % (os.environ.get('GENESIS_DIR', '/genesis'), self.JOB)
                
        # --从数据库中获取lock记录 获取不到在从文件内获取 20230904 by lyh
        self.pre_lock = None
        if len(self.JOB) == 13:            
            self.pre_lock = self.getJOB_LockInfo(dataType='locked_info')
            
        if not self.pre_lock:              
            self.pre_lock = self.read_file()
        
    def getJOB_LockInfo(self, dataType='locked_info'):
        """
        从数据库中获取料号的锁记录
        :param dataType: 获取的数据类型（status:locked_info log:locked_log）
        :return:dict
        """
        #GEN.COM('get_user_name')
        #IncamUser = GEN.COMANS
        ## 测试阶段
        #if IncamUser not in ["83288"]:
            #return {}
            
        lockData = self.getDATA.getLock_Info(self.JOB.split("-")[0])

        try:
            return json.loads(lockData[dataType], encoding='utf8')
        except:
            # print u'传入的数据参数异常'
            return {}

    def getChangeDetial(self):
        """
        获取修改的明细
        :return:
        """
        warn_mess=[]
        for lock_step in self.pre_lock:
            if lock_step == self.STEP:
                for lock_layer in self.pre_lock[lock_step]:
                    if lock_layer in self.layer_list:
                        if self.STEP == "lock_panelization_status":
                            warn_mess.append(u'panel拼版已被锁定,不可移动&添加&删除')
                        else:
                            warn_mess.append(u'锁定的Step：%s中_锁定的层别：%s,不可移动&添加&删除' % (lock_step, lock_layer))
                        
            if self.STEP == "check_all_step":
                for lock_layer in self.pre_lock[lock_step]:
                    if lock_layer in self.layer_list:
                        warn_mess.append(u'锁定的Step：%s中_锁定的层别：%s,不可移动&添加&删除' % (lock_step, lock_layer)) 

        if len(warn_mess) != 0:
            GEN.COM('skip_current_command')
            msg_box = msgBox()
            msg_box.critical(self, '警告', u"%s" % "\n".join(warn_mess), QtGui.QMessageBox.Ok)
            exit(-1)

    def read_file(self):
        """
        用json从user文件夹中的job_lock.json中读取字典
        :return:
        :rtype:
        """
        json_dict = {}
        stat_file = os.path.join(self.userDir, self.job_lock)
        if os.path.exists(stat_file):
            fd = open(stat_file, 'r')
            json_dict = json.load(fd)
            fd.close()
        return json_dict


if __name__ == "__main__":    
    print sys.argv
    step_name  = sys.argv[1]
    layer_list = sys.argv[2:]
    M = MainGen()
    M.STEP = step_name
    M.layer_list = layer_list
    M.getChangeDetial()
    sys.exit(0)
