#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import platform
reload(sys)
sys.setdefaultencoding('utf-8')

PRODUCT = os.environ.get('INCAM_PRODUCT',None)
if platform.system() == "Windows":
    sys.path.insert(0,"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.insert(0,"/incam/server/site_data/scripts/Package")

import genCOM_26 as genCOM
from Gateway import Gateway

class forbid_produce(object):
    """
    添加禁止生产字样于板边
    """
    def __init__(self,debug=False):
        """
        初始化
        """
        self.JOB = os.environ.get('JOB', None)
        self.STEP = os.environ.get('STEP', None)
        # 接口定义
        if debug:
            # 通过genesis gateway命令连结pid进行会话,不用在genesis环境下运行，直接用gateway的方式，可在pycharm环境下直接debug
            self.GEN = Gateway()
            self.GEN.genesis_connect()
            # 方法genesis_connect通过查询log-genesis文件获取的料号名
            self.JOB = self.GEN.job_name
            self.pid = self.GEN.pid
        else:
            self.GEN = genCOM.GEN_COM()
            self.pid = os.getpid()

    def add_symbol(self):
        """
        添加symbol
        :return:
        :rtype:
        """
        self.GEN.OPEN_STEP('panel', job=self.JOB)
        self.GEN.COM('units,type=mm')
        info = self.GEN.DO_INFO('-t step -e %s/panel -m script -d PROF_LIMITS' % self.JOB)
        # profile_xmin = float(info['gPROF_LIMITSxmin'])
        # profile_xmax = float(info['gPROF_LIMITSxmax'])
        # profile_ymin = float(info['gPROF_LIMITSymin'])
        profile_ymax = float(info['gPROF_LIMITSymax'])
        for_x = 105
        for_y = profile_ymax*0.5 - 435
        self.GEN.CLEAR_LAYER()
        self.GEN.COM('affected_filter,filter=(type=signal|power_ground|solder_mask|silk_screen|solder_paste&context=board)')
        self.GEN.VOF()
        self.GEN.AFFECTED_LAYER('p1', 'no')
        self.GEN.AFFECTED_LAYER('p2', 'no')
        self.GEN.VON()
        # --如果没有影响层，直接进入下一轮循环
        self.GEN.COM('get_affect_layer')
        layers = self.GEN.COMANS.split()
        if len(layers) == 0:
            return
        self.GEN.COM('add_pad,attributes=no,x=%s,y=%s,symbol=%s,polarity=positive,angle=0,mirror=no,'
                     'nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1'
                     % (for_x, for_y, 'forbid_produce'))
        self.GEN.CLEAR_LAYER()

if __name__ == '__main__':
    forbid_production = forbid_produce()
    forbid_production.add_symbol()
