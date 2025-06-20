#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                      #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2022.07.05
# @Revision     :    1.0.0
# @File         :    flp_coupon.py
# @Software     :    PyCharm
# @Usefor       :    防锣偏Coupon(来源于183系列) http://192.168.2.120:82/zentao/story-view-4106.html
# ---------------------------------------------------------#
import math
import os
import platform
import re
import sys
import csv
reload(sys)
sys.setdefaultencoding('utf-8')
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *

# --加载相对位置，以实现InCAM与Genesis共用
if platform.system() == "Windows":
    # sys.path.append(r"E:/Script/Package")
    # sys.path.append(r"D:/genesis/sys/scripts/Package")
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genCOM_26 as genCOM
import Oracle_DB
from messageBoxPro import msgBox

class MainWindow(object):
    def __init__(self):
        self.GEN = genCOM.GEN_COM()
        self.job_name = os.environ.get('JOB', None)
        self.appVer = 'v1.0'
        self.abs_path = os.path.dirname(os.path.abspath(__file__))
        self.layer_num = int(self.job_name[4:6])
        self.pre_run()
        self.runMain()

    def pre_run(self):
        """
        正式运行前相关变量定义
        :return:
        :rtype:
        """
        # --获取相关信息
        self.outLay = self.GEN.GET_ATTR_LAYER('outer')
        self.innerLay = self.GEN.GET_ATTR_LAYER('inner')
        self.maskLay = self.GEN.GET_ATTR_LAYER('solder_mask')
        self.silkLay = self.GEN.GET_ATTR_LAYER('silk_screen')
        step_info = self.GEN.DO_INFO('-t job -e %s -m script -d STEPS_LIST' % self.job_name)
        self.first_step = step_info['gSTEPS_LIST'][0]

    def runMain(self):
        """
        run主函数
        :return:None
        """
        # --中文提醒
        msg_box = msgBox()
        msg_box.warning(self, '自动生成防锣偏模块程序', '请在Mouse命令中指定添加位置!', QMessageBox.Ok)
        self.run_circle()

        # --第一次加完后，弹出是否继续的提示
        while True:
            msg_box = msgBox()
            ret = msg_box.question(self, '自动生成防锣偏模块程序', '是否继续添加?', QMessageBox.Yes, QMessageBox.No)
            if ret == "是":
                self.run_circle()
            else:
                # --运行完成提醒
                msg_box = msgBox()
                msg_box.information(self, '自动生成防锣偏模块程序', '脚本运行成功，请检查!', QMessageBox.Ok)
                break

    def run_circle(self):
        """
        多次调用，写成方法
        :return:
        :rtype:
        """
        # --将snap抓点模式关闭，防止mouse抓到错误的点
        self.GEN.COM('snap_mode,mode=off')
        self.GEN.CHANGE_UNITS('inch')
        # --通过mouse命令获取坐标x,y
        self.GEN.MOUSE('Please sel a point to add !',mode='p')
        mouse_xy = self.GEN.MOUSEANS.split()
        mouse_x = float(mouse_xy[0])
        mouse_y = float(mouse_xy[1])

        # --DO_INFO获取profile信息
        prof_info = self.GEN.DO_INFO('-t step -e %s/set -m script -d PROF_LIMITS' % self.job_name, units='inch')
        prof_xmin = float(prof_info['gPROF_LIMITSxmin'])
        prof_ymin = float(prof_info['gPROF_LIMITSymin'])
        prof_xmax = float(prof_info['gPROF_LIMITSxmax'])
        prof_ymax = float(prof_info['gPROF_LIMITSymax'])

        # --计算mouse抓取的点到profile上下左右的距离
        to_xmin = math.fabs(mouse_x - prof_xmin)
        to_ymin = math.fabs(mouse_y - prof_ymin)
        to_xmax = math.fabs(mouse_x - prof_xmax)
        to_ymax = math.fabs(mouse_y - prof_ymax)

        if min(to_xmin,to_ymin,to_xmax,to_ymax) == to_xmin:
            # --距左侧profile最近的时候
            add_x = prof_xmin
            add_y = mouse_y
            pad_angle = 270

        elif min(to_xmin, to_ymin, to_xmax, to_ymax) == to_ymin:
            # --距底部profile最近的时候
            add_y = prof_ymin
            add_x = mouse_x
            pad_angle = 180

        elif min(to_xmin, to_ymin, to_xmax, to_ymax) == to_xmax:
            # --距右侧profile最近的时候
            add_x = prof_xmax
            add_y = mouse_y
            pad_angle = 90

        elif min(to_xmin, to_ymin, to_xmax, to_ymax) == to_ymax:
            # --距顶部profile最近的时候
            add_y = prof_ymax
            add_x = mouse_x
            pad_angle = 0
        else:
            # --以上均不满足时，给个默认值，防止变量未定义报错
            add_x = mouse_x
            add_y = mouse_y
            pad_angle = 0

        self.addLayerDetail(add_x, add_y, pad_angle)

    def addLayerDetail(self,add_x,add_y,pad_angle):
        """
        依据准则添加相关层别tooling
        :return: None
        """

        to_prof_6mil = 0.0084
        if pad_angle == 0:
            # --4.8mil 线，距profile6mil
            ol_x3 = add_x
            ol_y3 = add_y - to_prof_6mil
            # --4.8mil的外围线坐标
            line_xs3 = ol_x3 - 0.098425
            line_xe3 = ol_x3 + 0.098425
            line_ys3 = ol_y3
            line_ye3 = ol_y3
            # === 测试点pad ===
            pad1_x = line_xs3
            pad1_y = line_ys3 - 0.026
            pad2_x = line_xe3
            pad2_y = line_ye3 - 0.026
            # === 铜皮 ===
            cu_center_x = pad1_x + (pad2_x - pad1_x) * 0.5
            cu_center_y = pad1_y + 0.0060806 + 0.013519 * 0.5
        elif pad_angle == 90:
            # --4.8mil 线，距profile6mil
            ol_x3 = add_x - to_prof_6mil
            ol_y3 = add_y
            # --4.8mil的外围线坐标
            line_xs3 = ol_x3
            line_xe3 = ol_x3
            line_ys3 = ol_y3 - 0.098425
            line_ye3 = ol_y3 + 0.098425
            # === 测试点pad ===
            pad1_x = line_xs3 - 0.026
            pad1_y = line_ys3
            pad2_x = line_xe3 - 0.026
            pad2_y = line_ye3
            # === 铜皮 ===
            cu_center_x = pad1_x + 0.0060806 + 0.013519 * 0.5
            cu_center_y = pad1_y + (pad2_y - pad1_y) * 0.5
        elif pad_angle == 180:
            # --4.8mil 线，距profile6mil
            ol_x3 = add_x
            ol_y3 = add_y + to_prof_6mil
            # --4.8mil的外围线坐标
            line_xs3 = ol_x3 - 0.098425
            line_xe3 = ol_x3 + 0.098425
            line_ys3 = ol_y3
            line_ye3 = ol_y3
            # === 测试点pad ===
            pad1_x = line_xs3
            pad1_y = line_ys3 + 0.026
            pad2_x = line_xe3
            pad2_y = line_ye3 + 0.026
            # === 铜皮 ===
            cu_center_x = pad1_x + (pad2_x - pad1_x) * 0.5
            cu_center_y = pad1_y - 0.0060806 - 0.013519 * 0.5
        elif pad_angle == 270:
            # --4.8mil 线，距profile6mil
            ol_x3 = add_x + to_prof_6mil
            ol_y3 = add_y
            # --4.8mil的外围线坐标
            line_xs3 = ol_x3
            line_xe3 = ol_x3
            line_ys3 = ol_y3 - 0.098425
            line_ye3 = ol_y3 + 0.098425
            # === 测试点pad ===
            pad1_x = line_xs3 + 0.026
            pad1_y = line_ys3
            pad2_x = line_xe3 + 0.026
            pad2_y = line_ye3
            # === 铜皮 ===
            cu_center_x = pad1_x - 0.0060806 - 0.013519 * 0.5
            cu_center_y = pad1_y + (pad2_y - pad1_y) * 0.5

        # === 2022.07.12 增加碰到物件的检测 ===
        tmp_check_layer = '__tmp_check_layer__'
        self.GEN.DELETE_LAYER(tmp_check_layer)
        self.GEN.CREATE_LAYER(tmp_check_layer)
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER(tmp_check_layer,'yes')
        self.GEN.ADD_PAD(pad1_x, pad1_y, 's30', pol='negative')
        self.GEN.ADD_PAD(pad1_x, pad1_y, 's20', pol='positive')
        self.GEN.ADD_PAD(pad2_x, pad2_y, 's30', pol='negative')
        self.GEN.ADD_PAD(pad2_x, pad2_y, 's20', pol='positive')

        self.GEN.ADD_LINE(line_xs3, line_ys3, line_xe3, line_ye3, 'r4.8', pol='positive')
        # self.GEN.ADD_LINE(line_xs7, line_ys7, line_xe7, line_ye7, 'r10',pol='negative')

        self.GEN.ADD_LINE(line_xs3, line_ys3, pad1_x, pad1_y, 'r4.8', pol='positive')
        self.GEN.ADD_LINE(pad2_x, pad2_y, line_xe3, line_ye3, 'r4.8', pol='positive')

        self.add_rect_surface(cu_center_x, cu_center_y, angle=pad_angle)
        self.GEN.FILTER_RESET()
        self.GEN.SEL_REF_FEAT(';'.join(self.outLay),'touch',f_type='pad')
        if int(self.GEN.GET_SELECT_COUNT()) > 0:
            msg_box = msgBox()
            msg_box.warning(self, '添加位置与外层相交，本次不添加', '再次选择位置!', QMessageBox.Ok)
            return False
        self.GEN.SEL_REF_FEAT(';'.join(self.maskLay),'touch')
        if int(self.GEN.GET_SELECT_COUNT()) > 0:
            msg_box = msgBox()
            msg_box.warning(self, '添加位置与防焊相交，本次不添加', '再次选择位置!', QMessageBox.Ok)
            return False

        if self.silkLay:
            self.GEN.SEL_REF_FEAT(';'.join(self.silkLay),'touch')
            if int(self.GEN.GET_SELECT_COUNT()) > 0:
                msg_box = msgBox()
                msg_box.warning(self, '添加位置与文字相交，本次不添加', '再次选择位置!', QMessageBox.Ok)
                return False
        self.GEN.CLEAR_LAYER()
        self.GEN.DELETE_LAYER(tmp_check_layer)

        # --外层加比防焊字大单边3mil的方块
        for lay in self.outLay:
            self.GEN.WORK_LAYER(lay)
            # self.GEN.ADD_PAD(rect_x3, rect_y3, rect_sym, angle=text_angle_top)
            # self.GEN.ADD_PAD(rect_x7, rect_y7, rect_sym, angle=text_angle_top)

            self.GEN.ADD_PAD(pad1_x, pad1_y, 's30',pol='negative')
            self.GEN.ADD_PAD(pad1_x, pad1_y, 's20',pol='positive')
            self.GEN.ADD_PAD(pad2_x, pad2_y, 's30',pol='negative')
            self.GEN.ADD_PAD(pad2_x, pad2_y, 's20',pol='positive')

            self.GEN.ADD_LINE(line_xs3, line_ys3, line_xe3, line_ye3, 'r4.8', pol='positive')
            # self.GEN.ADD_LINE(line_xs7, line_ys7, line_xe7, line_ye7, 'r10',pol='negative')

            self.GEN.ADD_LINE(line_xs3, line_ys3, pad1_x, pad1_y, 'r4.8', pol='positive')
            self.GEN.ADD_LINE(pad2_x, pad2_y, line_xe3, line_ye3, 'r4.8', pol='positive')

            self.add_rect_surface(cu_center_x,cu_center_y,angle=pad_angle)

        # --拷贝阻焊层模板至正式阻焊层
        # for lay in self.maskLay + self.outLay:
        for lay in self.maskLay:
            self.GEN.WORK_LAYER(lay)
            self.GEN.ADD_PAD(pad1_x, pad1_y, 's22', pol='positive')
            self.GEN.ADD_PAD(pad2_x, pad2_y, 's22', pol='positive')

        self.GEN.CLEAR_LAYER()

    def add_rect_surface(self,center_x,center_y,width=0.16685,height=0.013519,angle=0):
        """

        :return:
        """

        if angle == 0 or angle == 180:
            sur_x1 = center_x - width * 0.5
            sur_x2 = center_x + width * 0.5
            sur_y1 = center_y - height * 0.5
            sur_y2 = center_y + height * 0.5
        elif angle == 90 or angle == 270:
            sur_x1 = center_x - height * 0.5
            sur_x2 = center_x + height * 0.5
            sur_y1 = center_y - width * 0.5
            sur_y2 = center_y + width * 0.5

        self.GEN.COM('add_surf_strt,surf_type=feature')
        self.GEN.COM('add_surf_poly_strt,x=%s,y=%s' % (sur_x1, sur_y1))
        self.GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (sur_x1, sur_y2))
        self.GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (sur_x2, sur_y2))
        self.GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (sur_x2, sur_y1))
        self.GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (sur_x1, sur_y1))
        self.GEN.COM('add_surf_poly_end')
        self.GEN.COM('add_surf_end,attributes=no,polarity=positive')

        # # --拷贝阻焊层模板至正式阻焊层
        # # for lay in self.maskLay + self.outLay:
        # for lay in self.maskLay:
        #     self.GEN.WORK_LAYER(lay)
        #     self.GEN.ADD_PAD(tri_x3,tri_y3,'tri12x10',angle=pad_angle)
        #     self.GEN.ADD_LINE(line_xs3,line_ys3,line_xe3,line_ye3,'r5')
        #     self.GEN.ADD_PAD(tri_x7,tri_y7,'tri12x10',angle=pad_angle)
        #     self.GEN.ADD_LINE(line_xs7,line_ys7,line_xe7,line_ye7,'r5')
        #     side_info = self.GEN.DO_INFO('-t layer -e %s/%s/%s -m script -d SIDE' % (self.job_name,self.first_step,lay))
        #     side = side_info['gSIDE']
        #     if side in ['top']:
        #         self.GEN.ADD_TEXT(text_x3t,text_y3t,'3mil',text_x_size,text_y_size,w_factor=0.4166666567,angle=text_angle_top)
        #         self.GEN.ADD_TEXT(text_x7t,text_y7t,'7mil',text_x_size,text_y_size,w_factor=0.4166666567,angle=text_angle_top)
        #     else:
        #         self.GEN.ADD_TEXT(text_x3b,text_y3b,'3mil',text_x_size,text_y_size,w_factor=0.4166666567,angle=text_angle_bot,mirr='yes')
        #         self.GEN.ADD_TEXT(text_x7b,text_y7b,'7mil',text_x_size,text_y_size,w_factor=0.4166666567,angle=text_angle_bot,mirr='yes')


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MainWindow()
