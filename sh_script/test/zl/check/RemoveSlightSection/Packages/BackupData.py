#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------- #
#                VTG.SH SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    LiuChuang
# @Mail         :    Chuang_cs@163.com
# @Date         :    2023/02/09
# @Revision     :    1.0.0
# @File         :    BackupData.py.py
# @Software     :    PyCharm
# @Usefor       :    
# --------------------------------------------------------- #

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
'''版本记录
版本    ：V1.0.0
更新日期：2023/02/09
作者    ：Chuang.Liu
更新内容：
    1、增加备份功能
    2、genesis与Incam、IncamPro的兼容
'''

import os
import sys
import time

# --加载相对位置，以实现InCAM与Genesis共用
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")

import genCOM_26 as genCOM

# --需要使用窗体模态提醒
from mwClass_V2 import *

GEN = genCOM.GEN_COM()


class Layers:
    def __init__(self, userID=None):
        self.JOB = os.environ.get('JOB', None)
        self.userID = userID
        self.software = GEN.getEnv()['software'].lower()
        pass

    def backupLayers(self, unlockData, autoSave=False):
        """
        备份指定层
        :param autoSave:是否需要自动保存（非审核人员不作自动保存，以名漏修改记录）
        :return:
        """
        backList = []
        # [{'layers': [u'l2'], 'step': u'set'}, {'layers': [u'l2'], 'step': u'fa'}, {'layers': [u'l2'], 'step': u'edit'},
        #  {'layers': [u'l2'], 'step': u'coupon'}, {'layers': [u'l2'], 'step': u'drl'},
        #  {'layers': [u'l2'], 'step': u'net'}, {'layers': [u'l2'], 'step': u'orig'},
        #  {'layers': [u'l2'], 'step': u'panel'}]
        GEN.COM("open_entity,job=%s,type=matrix,name=matrix,iconic=yes" % self.JOB)
        for layDict in unlockData:
            for backLay in layDict['layers']:
                if backLay in backList: continue
                backList.append(backLay)

                # --使用martix功能进行备份
                if not self.matrixBackup(backLay):
                    AboutDialog(u'%s 层备份失败，请检查，并手动备份！' % backLay).exec_()
                    return False
        GEN.COM("matrix_page_close,job=%s,matrix=matrix" % self.JOB)

        # --保存料号
        if autoSave:
            GEN.SAVE_JOB(self.JOB)
            # --写last_save日志
            self.writeLastSave_log()

        return True

    def matrixBackup(self, layName):
        """
        更新matrix里的数据
        :param layName:需要备份的层名
        :return: None
        """
        matrix = GEN.DO_INFO("-t matrix -e %s/matrix" % self.JOB)
        # --使用doinfo获取board层列表，以免用户在没在打开step的情况下保存料号
        for rowNum in matrix["gROWrow"]:
            index = matrix["gROWrow"].index(rowNum)
            matrRowName = matrix["gROWname"][index]
            if matrRowName == layName:
                backTime = time.strftime('%Y%m%d_%H%M%S', time.localtime(int(time.time())))
                # GEN.COM("open_entity,job=h81504pf953b1-liu,type=matrix,name=matrix,iconic=no")
                GEN.VOF()
                GEN.COM("matrix_dup_row,job=%s,matrix=matrix,row=%s" % (self.JOB, rowNum))
                dupResult = GEN.STATUS
                GEN.VON()
                if dupResult != 0:
                    return False

                GEN.COM("matrix_refresh,job=%s,matrix=matrix" % self.JOB)
                # --默认复制后保存在Matrix的下一行，直接获取下一行的层名即备份的层名(仅适用于Genesis中的逻辑，incam下是在最后一行）
                if self.software == 'genesis':
                    moveNum = int(rowNum) + 1
                    dupName = self.getRowName(moveNum)
                else:
                    # --重新取整个matrix数据，取出最后一个num
                    tmpMatrix = GEN.DO_INFO("-t matrix -e %s/matrix" % self.JOB)
                    moveNum = len(tmpMatrix['gROWrow'])
                    lastNum = len(tmpMatrix['gROWrow']) - 1
                    dupName = tmpMatrix['gROWname'][lastNum]
                # --备份异常
                if not dupName: return False
                # --改属性
                GEN.COM("matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=misc" % (self.JOB, dupName))
                # --重命名（后缀：工号+时间戳）
                # @formatter:off
                GEN.COM("matrix_rename_layer,job=%s,matrix=matrix,layer=%s,new_name=%s" % (self.JOB, dupName, str(layName) + "_%s_%s" % (self.userID, backTime)))
                # @formatter:on
                # --置顶
                GEN.COM("matrix_move_row,job=%s,matrix=matrix,row=%s,ins_row=1" % (self.JOB, moveNum))

                GEN.COM("matrix_refresh,job=%s,matrix=matrix" % self.JOB)

                # --当非genesis软件时，还原显示界面
                if self.software != 'genesis': GEN.COM('top_tab,tab=Display')

        return True

    def getRowName(self, row_num):
        """
        通过rowNum获取层名
        :param rowNum:行Num
        :return:
        """
        matrix = GEN.DO_INFO("-t matrix -e %s/matrix" % self.JOB)
        # --使用doinfo获取board层列表，以免用户在没在打开step的情况下保存料号
        for rowNum in matrix["gROWrow"]:
            index = matrix["gROWrow"].index(rowNum)
            matrRowName = matrix["gROWname"][index]
            if int(rowNum) == int(row_num):
                return matrRowName

        return None

    def writeLastSave_log(self):
        """
        自动写最后一次保存时间的日志，以供版本检测用
        :return: None
        """
        saveTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(time.time())))
        jobPath = GEN.getJobPath(self.JOB)
        userDir = os.path.join(jobPath, 'user')

        # --写文件
        f = open(os.path.join(userDir, 'last_savetime'), 'w')
        f.write('%s %s' % (saveTime, self.userID))
        f.close()


if __name__ == '__main__':
    M = Layers()
    M.matrixBackup('l1')
