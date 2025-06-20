#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2022/02/08
# @Revision     :    1.0.0
# @File         :    pre_save_check.py
# @Software     :    PyCharm
# @Usefor       :    参考netCheck.py的料号更改部分
# ---------------------------------------------------------#
# 20241204 zl 排除去细丝所保存的铜皮层



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

import MySQL_DB


class MainGen():
    """
    GENESIS、InPlan中相关操作
    """

    def __init__(self):
        # MainWindow.__init__(self, '')
        # super(MainGen, self).__init__('')
        self.JOB = os.environ.get('JOB', 's51912pr488a4')
        self.STEP = os.environ.get('STEP', 'edit')
        self.changeNetLay = []
        self.job_lock = '%s_job_lock.json' % self.JOB
        self.panel_surface_layer = 'inner_panel_surface' # 20241204 去细丝保留的铜皮层
        DB_M = MySQL_DB.MySQL()
        dbc_m = DB_M.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                                   username='root', passwd='k06931!')        
        sql = u"select * from hdi_engineering.incam_user_authority "
        director_user_info = DB_M.SELECT_DIC(dbc_m, sql)
        dbc_m.close()
        GEN.COM('get_user_name')
        IncamUser = GEN.COMANS
        for dic_info in director_user_info:
            # 50616杨仲彪现在在支援制作，他的保存权限帮忙开下 20240109 by lyh
            # 增加伍青的保存权限
            if str(dic_info["user_id"]) == IncamUser:
                if dic_info["Authority_Name"] == u"审核人权限" and \
                   dic_info["Authority_Status"] ==u"是":
                    GEN.COM('skip_current_command')
                    msg_box = msgBox()
                    msg_box.critical(self, '警告', u"审核人无权限保存资料，请检查！" , QtGui.QMessageBox.Ok)
                    exit(1)                        
        
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
        # 测试阶段
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
        change_dict = {}
        del_dict = {}
        getData = GEN.INFO("-t job -e %s -d CHANGES" % self.JOB)
        # --循环所有保存信息内容
        reName = False
        Modif = False
        lineExists = False
        modifDetail = ""
        Delete = False
        dlineExists = False
        delDetail = ""
        for info in getData:
            # --去除结尾的回车及Tab
            info.strip()
            # --当已进入'Modified Entities'区域信息时，
            if 'Modified Entities' in info or "Renamed Entities" in info:
                reName = False
                Modif = True
                continue

            # --进入'Modified Entities'区域信息时，下面的 ‘----’
            if Modif is True and lineExists is False and '----' in info:
                lineExists = True
                continue
            # --当已进入'Modified Entities'区域，但又出现“----”默认跳出了'Modified Entities'区域
            if lineExists is True and '----' in info:
                Modif = False
                continue

            if 'Deleted Entities' in info:
                Delete = True
            if Delete is True and dlineExists is False and '----' in info:
                dlineExists = True
                continue
            if dlineExists is True and '----' in info:
                Delete = False
                continue
            # --当在'Modified Entities'区域检测是否有修改net的操作(仅修改到了属性，可忽略)
            repInfo = info.replace(' ', '')  # --分割后的数据，类似step=net,layer=l2,relation=relation
            # if Modif is True and 'step=net' in repInfo and 'ent_attributes' not in repInfo:
            # 2022.03.16 增加排除ncset
            if Modif is True and 'step=' in repInfo and \
               'ent_attributes' not in repInfo and \
               'ncset' not in repInfo and \
               "notes=notes" not in repInfo:
                modifDetail += repInfo
                # --统计修改了哪几层，以便后面查看修改内容，还原现场用
                stepN = (repInfo.split(',')[0]).split('=')[1].replace('\n', '')
                if stepN not in change_dict:
                    change_dict[stepN] = []
                try:
                    layN = (repInfo.split(',')[1]).split('=')[1].replace('\n', '')
                    change_dict[stepN].append(layN)
                    change_dict[stepN] = list(set(change_dict[stepN]))
                    # --保证无重复的数组元素
                    # self.changeNetLay = list(set(self.changeNetLay))
                except:
                    pass

            # --当在'Deleted Entities'区域检测是否有修改的操作 删除ncset的动作，可忽略
            if Delete is True and 'step=' in repInfo and 'ncset' not in repInfo:
                delDetail += repInfo
                # --统计修改了哪几层，以便后面查看修改内容，还原现场用
                stepN = (repInfo.split(',')[0]).split('=')[1].replace('\n', '')
                if stepN not in del_dict:
                    del_dict[stepN] = []
                try:
                    layN = (repInfo.split(',')[1]).split('=')[1].replace('\n', '')
                    del_dict[stepN].append(layN)
                    del_dict[stepN] = list(set(del_dict[stepN]))
                    # --保证无重复的数组元素
                    # self.changeNetLay = list(set(self.changeNetLay))
                except:
                    pass
        # === TODO 还有新建的层别 Created
        # --当修改内容不为空时
        if modifDetail != "":
            print change_dict
        if delDetail != "":
            print 'del_dict'
            print del_dict
        warn_mess = []
        print self.pre_lock
        for lock_step in self.pre_lock:
            if lock_step in change_dict:
                for lock_layer in self.pre_lock[lock_step]:
                    if lock_layer == self.panel_surface_layer:  # 20241204 zl 排除去细丝所保存的铜皮层
                        continue
                    if lock_layer in change_dict[lock_step]:
                        warn_mess.append(u'锁定的Step：%s中_锁定的层别：%s,不可编辑' % (lock_step, lock_layer))
            if lock_step in del_dict:
                for lock_layer in self.pre_lock[lock_step]:
                    if lock_layer in del_dict[lock_step]:
                        warn_mess.append(u'锁定的Step：%s中_锁定的层别：%s,不可删除' % (lock_step, lock_layer))

        if len(warn_mess) != 0:
            GEN.COM('skip_current_command')
            msg_box = msgBox()
            msg_box.critical(self, '警告', u"%s" % "\n".join(warn_mess), QtGui.QMessageBox.Ok)
            exit(1)

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
    app = QtGui.QApplication(sys.argv)
    M = MainGen()
    M.getChangeDetial()
    sys.exit(0)
