#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2022/07/26
# @Revision     :    1.1.0
# @File         :    slot_deal_main.py
# @Software     :    PyCharm
# @Usefor       :    槽孔旋转及添加导引孔，合并程序slot_rotata.py 及slot_pre_hole.py
#                   http://192.168.2.120:82/zentao/story-view-4271.html
# 2022.07.28 SQL 语句中，增加distinct，用于去重
# V1.1 2022.08.10 槽引孔分刀设计，孔径大小变更，且一定加两个导引孔 http://192.168.2.120:82/zentao/story-view-4511.html
# 2022.08.23 Song 层别2nd槽孔处理；槽孔未定义属性的检测及直接按pth处理
# 1.2023.03.09 Song 前置槽孔导引孔选择，如果导引孔信息有误，提前报出
# 2.槽孔旋转规范更改：http://192.168.2.120:82/zentao/story-view-5241.html
# ---------------------------------------------------------#
import os, sys, platform, pprint, math
from decimal import Decimal
# --加载相对位置，以实现InCAM与Genesis共用
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
from genesisPackages import get_panelset_sr_step
import genCOM_26 as genCOM
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *
from messageBoxPro import msgBox
import Oracle_DB


class slotRotate(QtGui.QWidget):
    """
    短槽旋转，做角度补偿
    """

    def __init__(self, xs, ys, xe, ye, xc, yc, sym, attr, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.xs = xs
        self.ys = ys
        self.xe = xe
        self.ye = ye
        self.xc = xc
        self.yc = yc
        self.sym = sym
        self.attr = attr
        self.pi = 3.1415926
        self.length = round(math.sqrt((self.xe - self.xs) ** 2 + (self.ye - self.ys) ** 2), 3)
        self.diameter = float(self.sym.strip('r')) / 1000
        real_calc_len = self.length + self.diameter
        # --TODO 20200909应周涌要求，槽孔去掉尾数再算长宽比
        self.diameter_cut = float(int(self.diameter * 1000 / 25) * 25) / 1000
        # self.ratio = float(self.length + self.diameter) / self.diameter_cut
        self.ratio = float(real_calc_len) / self.diameter_cut
        self.slot_len = self.diameter + self.length

    def rotate_slot(self, xs, ys, sym, angle,drl_layer='drl'):
        xmin = xs - 0.1
        xmax = xs + 0.1
        ymin = ys - 0.1
        ymax = ys + 0.1
        g.CLEAR_LAYER()
        g.AFFECTED_LAYER(slot_no_process, 'yes')
        g.COM('filter_reset,filter_name=popup')
        g.COM('filter_set,filter_name=popup,update_popup=no,include_syms=%s' % sym)
        g.COM('filter_area_strt')
        g.COM('filter_area_xy,x=%s,y=%s' % (xmin, ymin))
        g.COM('filter_area_xy,x=%s,y=%s' % (xmax, ymax))
        g.COM(
            'filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,inside_area=yes,intersect_area=yes')
        if int(g.GET_SELECT_COUNT()) == 0:
            msg_box = msgBox()
            msg_box.warning(None, '短槽旋转，做角度补偿', '未选择到钻孔!', QMessageBox.Ok)
        g.COM(
            'sel_move_other,target_layer=slot_rotate,invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0,mirror=none')
        g.AFFECTED_LAYER(slot_no_process, 'no')
        g.AFFECTED_LAYER(slot_rotate, 'yes')
        g.AFFECTED_LAYER(drl_layer, 'yes')
        g.COM('filter_area_strt')
        g.COM('filter_area_xy,x=%s,y=%s' % (xmin, ymin))
        g.COM('filter_area_xy,x=%s,y=%s' % (xmax, ymax))
        g.COM(
            'filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,inside_area=yes,intersect_area=yes')
        if int(g.GET_SELECT_COUNT()) == 0:
            msg_box = msgBox()
            msg_box.warning(None, '短槽旋转，做角度补偿', '未选择到钻孔!', QMessageBox.Ok)
        g.COM(
            'sel_transform,mode=anchor,oper=rotate,duplicate=no,x_anchor=%s,y_anchor=%s,angle=%s,x_scale=1,y_scale=1,x_offset=0,y_offset=0' % (
            xs, ys, angle))
        g.COM('filter_reset,filter_name=popup')
        g.AFFECTED_LAYER(slot_rotate, 'no')

    def add_note(self,add_x,add_y,add_layer='drl'):
        g.COM('note_add,layer=%s,x=%s,y=%s,user=Auto_slot_rotate,text=change_slot_direct' % (add_layer,add_x,add_y))


class Msg_Box:
    """
    MesageBox提示界面
    """

    def __init__(self):
        pass

    def msgBox_option(self, body, title=u'提示信息', msgType='information'):
        """
        可供提示选择的MessagesBox
        :param body:显示内容（支持html样式）
        :param title:标题
        :param msgType:显示类型（包括information, question, warning）QtGui.QMessageBox.ButtonMask 可查看所有
        :return:
        """
        msg = QtGui.QMessageBox.information(self, u"信息", body, QtGui.QMessageBox.Ok,
                                            QtGui.QMessageBox.Cancel)  # , )
        # --返回相应信息
        if msg == QtGui.QMessageBox.Ok:
            return 'Ok'
        else:
            return 'Cancel'

    def msgBox(self, body, title=u'提示信息', msgType='information', ):
        """
        可供提示选择的MessagesBox
        :param body:显示内容（支持html样式）
        :param title:标题
        :param msgType:显示类型（包括information, question, warning）
        :return:
        """
        if msgType == 'information':
            QtGui.QMessageBox.information(self, title, body, u'确定')
        elif msgType == 'warning':
            QtGui.QMessageBox.warning(self, title, body, u'确定')
        elif msgType == 'question':
            QtGui.QMessageBox.question(self, title, body, u'确定')

    def msgText(self, body1, body2, body3=None):
        """
        转换HTML格式
        :param body1:文本1
        :param body2:文本2
        :param body3:文本3
        :return:转换后的文本
        """
        # --转换为Html文本
        textInfo = u"""
                <p>
                    <span style="background-color:#E53333;color:#FFFFFF;font-size:18px;"><strong>%s：</strong></span>
                </p>
                <p>
                    <span style="font-size:18px;">&nbsp;&nbsp;</span>
                    <span style="color:#E53333;font-size:18px;">&nbsp;&nbsp;</span>
                    <span style="color:#E53333;font-size:18px;">&nbsp; &nbsp; </span>
                    <span style="color:#E53333;font-size:16px;">%s</span>
                </p>""" % (body1, body2)

        # --返回HTML样式文本
        return textInfo


class Oracle_info(QtGui.QWidget, Msg_Box):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        Msg_Box.__init__(self)
        self.job_name = os.environ.get('JOB', None)
        self.job_upper13 = self.job_name.upper()[:13]
        # --Oracle相关参数定义,连接ERP Oracle数据库
        self.DB_O = Oracle_DB.ORACLE_INIT()
        self.dbc_o = self.DB_O.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
                                          username='GETDATA', passwd='InplanAdmin')

    def get_Inplan_info(self):
        """
        sql中的%必须用%%进行转义
        :param diameter:
        :param length:
        :return:
        """
        sql_query = """
        SELECT
    cnt.item_name AS 料号名,
    cnp.item_name 钻带,
    dh_a.hole_mark_ 槽符,
    round( dh.actual_drill_size / 39.37, 3 ) AS 槽宽,
    round( dh.length / 39.37, 3 ) AS 槽长,
        (CASE WHEN dh_a.hole_mark_ IS NULL
                    THEN NULL          
                    ELSE 
        (SELECT
            distinct(round( AA.ACTUAL_DRILL_SIZE / 39.37, 2 ))
        FROM
            VGT_HDI.drill_hole AA,
            vgt_hdi.drill_hole_da BB 
        WHERE
            AA.ITEM_ID = bb.item_id 
            AND aa.revision_id = bb.revision_id 
            AND aa.sequential_index = bb.sequential_index 
            AND aa.item_id = dh.item_id 
            AND aa.revision_id = dh.revision_id 
            AND bb.drill_notes_ LIKE '%%' || dh_a.hole_mark_ || '%%引孔%%' 
        ) END) AS 导引孔 
    FROM
        VGT_HDI.Public_Items cnt,
        VGT_HDI.JOB job,
        VGT_HDI.Public_Items cnp,
        VGT_HDI.drill_program dp,
        VGT_HDI.drill_hole dh,
        vgt_hdi.drill_hole_da dh_a 
    WHERE
        cnt.item_id = job.item_id 
        AND cnt.revision_id = job.revision_id 
        AND cnt.root_id = cnp.root_id 
        AND cnp.item_id = dp.item_id 
        AND cnp.revision_id = dp.revision_id 
        AND dp.item_id = dh.item_id 
        AND dp.revision_id = dh.revision_id 
        AND dh.item_id = dh_a.item_id 
        AND dh.revision_id = dh_a.revision_id 
        AND dh.sequential_index = dh_a.sequential_index 
        AND dh_a.drill_notes_ LIKE '%%短槽%%' --筛选短槽
        AND dh.TYPE IN ( 4, 5 ) --slot类型
        AND cnp.item_name IN ( 'drl', 'DRL', 'Drl','2nd' ) --筛选钻带
    -- 	AND cnt.item_name = 'SC7504OI016B1' --料号名
        AND cnt.item_name = '%s' --料号名
    ORDER BY
        dh_a.hole_mark_
        """ % self.job_upper13
        try:
            queryRes = self.DB_O.SELECT_DIC(self.dbc_o, sql_query)
            if len(queryRes):
                return queryRes
            else:
                # showText = self.msgText(u'警告', u"Oracle数据库查询,JOB : %s 没有导引孔数据" % self.job_name)
                # self.msgBox(showText)

                msg_box = msgBox()
                msg_box.warning(None, '警告', "Oracle数据库查询,JOB : %s 没有导引孔和短槽数据，程序退出" % self.job_name,
                                QMessageBox.Ok)
                exit()
        except Exception, e:
            msg_box = msgBox()
            msg_box.warning(None, '警告,程序将以10004退出', "InPlan数据库查询,JOB : %s 导引孔数据有重复值\n以下为后台报错:%s" % (self.job_name,e),
                            QMessageBox.Ok)
            sys.exit(1)

    def Message(self, type, text):
        """
        Msg窗口
        :param text: 显示的内容
        :return:None
        """
        if type == 'information':
            message = QMessageBox.information(None, u'提示信息!', text, QMessageBox.Ok)
        else:
            message = QMessageBox.warning(None, u'警告信息!', text, QMessageBox.Ok)

    def __del__(self):
        self.DB_O.DB_CLOSE(self.dbc_o)


class slotPreHole(object):
    """
    短槽添加导引孔
    """

    def __init__(self, xs, ys, xe, ye, sym, attr, parent=None):
        self.xs = xs
        self.ys = ys
        self.xe = xe
        self.ye = ye
        self.sym = sym
        self.attr = attr
        self.pi = 3.1415926

        self.length = math.sqrt((self.xe - self.xs) ** 2 + (self.ye - self.ys) ** 2)
        self.diameter = float(self.sym.strip('r')) / 1000
        # --TODO 20200909应周涌要求，槽孔去掉尾数再算长宽比
        self.diameter_cut = float(int(self.diameter * 1000 / 25) * 25) / 1000
        # self.ratio = float(self.length + self.diameter) / self.diameter_cut
        self.slot_len = round(self.diameter + self.length, 4)
        self.ratio = float(self.slot_len) / self.diameter_cut
        

    def angle(self):
        # 获取slot的倾斜角,此处暂时用不上，后续可以参考
        dx = self.xe - self.xs
        dy = self.ye - self.ys
        # 余切值
        if dx == 0:
            angle = 90
        elif dy == 0:
            angle = 0
        else:
            tan_value = dy / dx
            # 通过math.atan求弧度
            radian = math.atan(tan_value)
            # 将弧度转为角度
            angle = float('%.3f' % (radian * 180 / self.pi))
        return math.fabs(angle), angle

    def get_sin_angle(self, subtense, hypotenuse):
        # 获取slot的倾斜角,此处暂时用不上，后续可以参考
        # subtense :对边
        # hypotenuse :斜边
        if subtense == 0:
            angle = 0
        elif hypotenuse == subtense:
            angle = 90
        else:
            sin_value = subtense / hypotenuse
            # 通过math.asin求弧度
            radian = math.asin(sin_value)
            # 将弧度转为角度
            angle = float('%.3f' % (radian * 180 / self.pi))
        return math.fabs(angle)

    def get_bit(self, diameter):
        # 钻嘴取最接近的，钻嘴以0.05递进
        pre_bit = int(diameter / 50) * 50
        next_bit = pre_bit + 50
        pre_diff = diameter - pre_bit
        next_diff = next_bit - diameter
        if next_diff > pre_diff:
            return pre_bit
        else:
            return next_bit

    def get_bit_E(self, length):
        # === 1.699997 类需要先进位再计算 ====
        # pre_bit = int((round(length, 0) - 300) / 2 / 50) * 50
        # pre_bit = int((round(length, 0) - 150) / 2 / 50) * 50
        pre_bit = int((round(length, 0) - 200) / 2.0 / 50) * 50
        # print 'length:%s' % length
        # print 'pre_bit:%s' % pre_bit
        return pre_bit

    def get_bit_inplan(self,cut_tail='no',drl_layer='drl'):
        """
        从inplan中获取槽孔导引孔大小
        :return:
        """
        info_list = slot_info
        bit_size = None
        c_diameter = self.diameter * 1
        if cut_tail == 'yes':
            c_diameter = float(int(self.diameter * 1000 / 25) * 25) / 1000
        for info in info_list:
            if info['钻带'].lower() == drl_layer:
                if info['槽宽'] == c_diameter:
                    if math.fabs(info['槽长'] - self.slot_len) < 0.001:
                        # 取整的问题，不能用==,只能比较差值
                        if info['导引孔']:
                            bit_size = info['导引孔'] * 1000
        return bit_size

    def add_pre_type_A(self):
        # 1.8<(槽长/槽宽)比<=2.0，起点、终点都加预钻孔
        # 导引孔直径为槽孔成品孔径长 - 钻针直径
        pi = self.pi
        angle, true_angle = self.angle()
        tool = self.get_bit_inplan()
        if tool == None:
            # 如果inplan数据库中取不到值
            diameter = int(self.length * 1000)
            # 取板内钻刀
            tool = self.get_bit(diameter)
        # 当所计算出导引孔直径小于0.35mm时，则直接加0.35mm导引孔
        if tool < 350:
            tool = 350
        tool = tool + 150  # 距顶端0.075mm
        # 计算预钻孔坐标
        if self.xs > self.xe:
            xS = self.xs + (self.diameter / 2 - tool / 2000.0) * math.cos(angle * pi / 180)
            xE = self.xe - (self.diameter / 2 - tool / 2000.0) * math.cos(angle * pi / 180)
        else:
            xS = self.xs - (self.diameter / 2 - tool / 2000.0) * math.cos(angle * pi / 180)
            xE = self.xe + (self.diameter / 2 - tool / 2000.0) * math.cos(angle * pi / 180)
        if self.ys > self.ye:
            yS = self.ys + (self.diameter / 2 - tool / 2000.0) * math.sin(angle * pi / 180)
            yE = self.ye - (self.diameter / 2 - tool / 2000.0) * math.sin(angle * pi / 180)
        else:
            yS = self.ys - (self.diameter / 2 - tool / 2000.0) * math.sin(angle * pi / 180)
            yE = self.ye + (self.diameter / 2 - tool / 2000.0) * math.sin(angle * pi / 180)
        tool = tool - 150  # 还原尺寸.075mm

        # 依据坐标和直径添加预钻孔
        g.CLEAR_LAYER()
        g.AFFECTED_LAYER('slot_pre_hole', 'yes')
        # 加non_plated属性
        g.CUR_ART_RESET()
        g.COM('cur_atr_set,attribute=.drill,option=non_plated')
        g.ADD_PAD(xS, yS, "r" + str(tool), attr='yes')
        g.ADD_PAD(xE, yE, "r" + str(tool), attr='yes')
        g.CUR_ART_RESET()
        g.AFFECTED_LAYER('slot_pre_hole', 'no')

    def add_pre_type_B(self):
        # 1.5<(槽长/槽宽)比<=1.8，只在终点加预钻孔
        # 保证预钻孔边到slot孔起点圆边1-5mil,这里取2.5mil
        pi = self.pi
        angle, true_angle = self.angle()
        tool = self.get_bit_inplan()
        if tool == None:
            # 如果inplan数据库中取不到值
            diameter = int(self.length * 1000 - 2500 / 39.37)
            # 取板内钻时，望大取值
            tool = self.get_bit(diameter)
        # 计算预钻孔坐标
        if self.xs > self.xe:
            xE = self.xe - (self.diameter / 2 - tool / 2000.0) * math.cos(angle * pi / 180)
        else:
            xE = self.xe + (self.diameter / 2 - tool / 2000.0) * math.cos(angle * pi / 180)
        if self.ys > self.ye:
            yE = self.ye - (self.diameter / 2 - tool / 2000.0) * math.sin(angle * pi / 180)
        else:
            yE = self.ye + (self.diameter / 2 - tool / 2000.0) * math.sin(angle * pi / 180)
        # 依据坐标和直径添加预钻孔
        g.CLEAR_LAYER()
        g.AFFECTED_LAYER('slot_pre_hole', 'yes')
        # 加non_plated属性
        g.CUR_ART_RESET()
        g.COM('cur_atr_set,attribute=.drill,option=non_plated')
        g.ADD_PAD(xE, yE, "r" + str(tool), attr='yes')
        g.CUR_ART_RESET()
        g.AFFECTED_LAYER('slot_pre_hole', 'no')

    def add_pre_type_C(self):
        # 1.2<(槽长/槽宽)比<=1.5，终点加两个预钻孔
        # Φ≤slot宽×0.37且Φ≤(slot长-slot宽) ×0.8，在满足以上2个条件的前提下Φ尽量取最大值,
        # 当预钻孔小于0.40mm时可以取消预钻.预钻孔大小，在满足图示要求的前提下尽量选用SIZE较大的钻咀
        # diameter = self.diameter*1000/2 - 4000/25.4
        pi = self.pi
        angle, true_angle = self.angle()
        tool = None
        tool = self.get_bit_inplan()
        if tool == None:
            # 如果inplan数据库中取不到值
            # 限制条件1，必须小于slot宽×0.37
            limit_1 = 0.37 * self.diameter * 1000
            # 限制条件2,必须小于(slot长-slot宽) ×0.8
            limit_2 = 0.8 * self.length * 1000
            # 取两个限制条件中的最小值当做预钻孔直径
            maxLimit = max(limit_1, limit_2)
            diameter = maxLimit
            # 取板内最接近的钻刀
            tool_edit = self.get_bit(diameter)
            # 以50um为进制取整取刀径,取值逻辑，与Inplan保持一致，limit_1,limit_2中的最大值递进一把刀
            tool_calc = int(diameter / 50) * 50 + 50
            # 当预钻孔小于0 .40 mm时可以取消预钻
            if tool_calc >= 400:
                tool = tool_calc
            else:
                return
        else:
            if tool < 400:
                # 当预钻孔小于0 .40 mm时可以取消预钻
                return
        # 先用45度角计算出基准坐标
        int_angle = 45
        # EG为终点到G圆中心距离，EH为终点到H圆中心距离
        if true_angle < 0:
            EG = self.diameter / 2 - tool / 2000.0 - 3 / 39.37
            EH = self.diameter / 2 - tool / 2000.0 - 1 / 39.37
        else:
            EG = self.diameter / 2 - tool / 2000.0 - 1 / 39.37
            EH = self.diameter / 2 - tool / 2000.0 - 3 / 39.37
        if self.xs > self.xe:
            xG = self.xe - EG * math.cos(int_angle * pi / 180 + angle * pi / 180)
            xH = self.xe - EH * math.cos(int_angle * pi / 180 - angle * pi / 180)
        else:
            xG = self.xe + EG * math.cos(int_angle * pi / 180 + angle * pi / 180)
            xH = self.xe + EH * math.cos(int_angle * pi / 180 - angle * pi / 180)
        if self.ys > self.ye:
            yG = self.ye - EG * math.sin(int_angle * pi / 180 + angle * pi / 180)
            yH = self.ye + EH * math.sin(int_angle * pi / 180 - angle * pi / 180)
        else:
            yG = self.ye + EG * math.sin(int_angle * pi / 180 + angle * pi / 180)
            yH = self.ye - EH * math.sin(int_angle * pi / 180 - angle * pi / 180)
        # 坐标修正，保证两圆间距1mil,G圆不动，H圆绕xe,ye旋转，计算旋转角度
        GH_now = math.sqrt((xG - xH) ** 2 + (yG - yH) ** 2)
        # 2.29是经验值，按1mil算的时候孔到孔只有0.1mil,所有做了修正
        GH_need = tool / 1000.0 + 2.29 / 39.37
        GH_enlarge = math.fabs(GH_need - GH_now)
        # 计算两个预钻孔的夹角
        rotate_angle = self.get_sin_angle(GH_enlarge / 2, EH)
        rotate_angle *= 2
        # 重新计算H点坐标
        if GH_need > GH_now:
            if self.xs > self.xe:
                xH = self.xe - EH * math.cos(int_angle * pi / 180 + rotate_angle * pi / 180 - angle * pi / 180)
            else:
                xH = self.xe + EH * math.cos(int_angle * pi / 180 + rotate_angle * pi / 180 - angle * pi / 180)
            if self.ys > self.ye:
                yH = self.ye + EH * math.sin(int_angle * pi / 180 + rotate_angle * pi / 180 - angle * pi / 180)
            else:
                yH = self.ye - EH * math.sin(int_angle * pi / 180 + rotate_angle * pi / 180 - angle * pi / 180)
        else:
            if self.xs > self.xe:
                xH = self.xe - EH * math.cos(int_angle * pi / 180 - rotate_angle * pi / 180 - angle * pi / 180)
            else:
                xH = self.xe + EH * math.cos(int_angle * pi / 180 - rotate_angle * pi / 180 - angle * pi / 180)
            if self.ys > self.ye:
                yH = self.ye + EH * math.sin(int_angle * pi / 180 - rotate_angle * pi / 180 - angle * pi / 180)
            else:
                yH = self.ye - EH * math.sin(int_angle * pi / 180 - rotate_angle * pi / 180 - angle * pi / 180)
        # 依据坐标和直径添加预钻孔
        g.CLEAR_LAYER()
        g.AFFECTED_LAYER('slot_pre_hole', 'yes')
        # 加non_plated属性
        g.CUR_ART_RESET()
        g.COM('cur_atr_set,attribute=.drill,option=non_plated')
        g.ADD_PAD(xG, yG, "r" + str(tool), attr='yes')
        g.ADD_PAD(xH, yH, "r" + str(tool), attr='yes')
        g.CUR_ART_RESET()
        g.AFFECTED_LAYER('slot_pre_hole', 'no')

    def add_pre_type_D(self):
        # (槽长/槽宽)比<=1.2 或者槽宽>3，终点加三个预钻孔
        pi = self.pi
        angle, true_angle = self.angle()
        # 加钻孔F的直径为slot宽-2mil
        diam_F = self.diameter * 1000 - 2000 / 25.4
        diam_H = self.get_bit_inplan()
        if diam_H == None:
            # 如果inplan数据库中取不到值
            # 计算加钻孔G和H的直径
            # 大圆半径
            R = self.diameter * 1000 / 2.0
            # slot中心到中心距离
            L = self.length
            """
            根据Inplan提供的公式：
            mm((0+substr(roundf(2*(db2mm(CurrentDrillHole.LENGTH - CurrentDrillHole.ACTUAL_DRILL_SIZE)/2 - 0.05)*sqrt(2)/(2+sqrt(2)),4), 1, 3))*100/100+0.025)*2
            """
            r = "%.4f" % float(2 * (L / 2 - 0.05) * math.sqrt(2) / (2 + math.sqrt(2)))
            r = float(str(r)[0:3])
            r = ((0 + r) * 100.0 / 100.0 + 0.025) * 1000
            diam_H = 2 * (r - 2 / 39.37)
            # 以50um为进制取整取刀径
            diam_H = self.get_bit(diam_H)
            if diam_H >= 400:
                diam_H = diam_H
            else:
                return
        # 为保证G点先钻,在H直径的基础上减1um
        diam_G = diam_H
        # 计算坐标
        if self.xs > self.xe:
            xG = self.xe - ((self.diameter / 2 - diam_G / 2000.0)) * math.cos(pi / 4 + angle * pi / 180)
            yG = self.ye + ((self.diameter / 2 - diam_G / 2000.0)) * math.sin(pi / 4 + angle * pi / 180)
            xH = self.xe - ((self.diameter / 2 - diam_H / 2000.0 - 2 / 25.4)) * math.cos(pi / 4 - angle * pi / 180)
            yH = self.ye - ((self.diameter / 2 - diam_H / 2000.0 - 2 / 25.4)) * math.sin(pi / 4 - angle * pi / 180)
        else:
            xG = self.xe + ((self.diameter / 2 - diam_G / 2000.0)) * math.cos(pi / 4 - angle * pi / 180)
            yG = self.ye + ((self.diameter / 2 - diam_G / 2000.0)) * math.sin(pi / 4 - angle * pi / 180)
            xH = self.xe + ((self.diameter / 2 - diam_H / 2000.0 - 2 / 25.4)) * math.cos(pi / 4 + angle * pi / 180)
            yH = self.ye - ((self.diameter / 2 - diam_H / 2000.0 - 2 / 25.4)) * math.sin(pi / 4 + angle * pi / 180)
        g.CLEAR_LAYER()
        g.AFFECTED_LAYER('slot_pre_hole', 'yes')
        # 加non_plated属性
        g.CUR_ART_RESET()
        g.COM('cur_atr_set,attribute=.drill,option=non_plated')
        g.ADD_PAD(self.xe, self.ye, "r" + str(diam_F))
        g.ADD_PAD(xG, yG, "r" + str(diam_G))
        g.ADD_PAD(xH, yH, "r" + str(diam_H))
        g.CUR_ART_RESET()
        g.AFFECTED_LAYER('slot_pre_hole', 'no')

    def add_pre_type_E(self,drl_layer='drl'):
        """
        # http://192.168.2.120:82/zentao/story-view-4511.html
        并更引孔添加大小规范 ：引孔孔径 = （槽长-0.2）* 0.5 向下取钻咀

        :return:
        """
        # 1.25<(槽长/槽宽)比<=2.0，起点、终点都加预钻孔
        # 导引孔直径为(槽孔成品孔径长 - 0.3) /2 向下取钻咀 ,已作废
        pi = self.pi
        angle, true_angle = self.angle()
        tool = None
        # === TODO 先不取inplan导引孔大小
        tool = self.get_bit_inplan(cut_tail='yes',drl_layer='drl')
        if tool is None:
            # 如果inplan数据库中取不到值
            diameter = int(self.slot_len * 1000)
            # 取板内钻刀
            tool = self.get_bit_E(diameter)
        # print 'xxxxxxxxxxx'
        # print tool
        # 当所计算出导引孔直径小于0.2mm时，则直接加0.2mm导引孔
        # === 2022.07.14 周涌，钉钉，暂时不管控 ===
        if tool < 200:
            tool = 200
        tool = tool + 150  # 距顶端0.075mm
        # 计算预钻孔坐标
        if self.xs > self.xe:
            xS = self.xs + (self.diameter / 2 - tool / 2000.0) * math.cos(angle * pi / 180)
            xE = self.xe - (self.diameter / 2 - tool / 2000.0) * math.cos(angle * pi / 180)
        else:
            xS = self.xs - (self.diameter / 2 - tool / 2000.0) * math.cos(angle * pi / 180)
            xE = self.xe + (self.diameter / 2 - tool / 2000.0) * math.cos(angle * pi / 180)
        if self.ys > self.ye:
            yS = self.ys + (self.diameter / 2 - tool / 2000.0) * math.sin(angle * pi / 180)
            yE = self.ye - (self.diameter / 2 - tool / 2000.0) * math.sin(angle * pi / 180)
        else:
            yS = self.ys - (self.diameter / 2 - tool / 2000.0) * math.sin(angle * pi / 180)
            yE = self.ye + (self.diameter / 2 - tool / 2000.0) * math.sin(angle * pi / 180)
        tool = tool - 150  # 还原尺寸.075mm
        # 依据坐标和直径添加预钻孔
        g.CLEAR_LAYER()
        g.AFFECTED_LAYER(slot_pre_hole, 'yes')
        # 加non_plated属性
        g.CUR_ART_RESET()
        # TOOD 属性需要follow槽孔属性
        if 'non_plated' in self.attr:
            g.COM('cur_atr_set,attribute=.drill,option=non_plated')
        else:
            g.COM('cur_atr_set,attribute=.drill,option=plated')

        # chk_dis = self.slot_len * 1000 - 150 - tool * 2
        # # === 孔间距 >= 0.115 时，才加预钻孔
        # if chk_dis >= 115:
        #     g.ADD_PAD(xS, yS, "r" + str(tool), attr='yes')
        # === 尾数分刀
        g.ADD_PAD(xS, yS, "r" + str(tool+2), attr='yes')
        g.ADD_PAD(xE, yE, "r" + str(tool+4), attr='yes')
        g.CUR_ART_RESET()
        g.AFFECTED_LAYER(slot_pre_hole, 'no')

    def add_pre_type_F(self):
        # 1.5<(槽长/槽宽)比<=1.8，只在终点加预钻孔
        # 保证预钻孔边到slot孔起点圆边1-5mil,这里取2.5mil
        pi = self.pi
        angle, true_angle = self.angle()
        # tool = None
        tool = self.get_bit_inplan(cut_tail='yes')

        if tool is None:
            diameter = int(self.slot_len * 1000)
            # 取板内钻刀
            tool = self.get_bit_E(diameter)
        if tool < 200:
            tool = 200
        tool = tool + 150  # 距顶端0.075mm

        # 计算预钻孔坐标
        if self.xs > self.xe:
            xE = self.xe - (self.diameter / 2 - tool / 2000.0) * math.cos(angle * pi / 180)
        else:
            xE = self.xe + (self.diameter / 2 - tool / 2000.0) * math.cos(angle * pi / 180)
        if self.ys > self.ye:
            yE = self.ye - (self.diameter / 2 - tool / 2000.0) * math.sin(angle * pi / 180)
        else:
            yE = self.ye + (self.diameter / 2 - tool / 2000.0) * math.sin(angle * pi / 180)
        tool = tool - 150  # 还原尺寸.075mm

        # 依据坐标和直径添加预钻孔
        g.CLEAR_LAYER()
        g.AFFECTED_LAYER('slot_pre_hole', 'yes')
        # 加non_plated属性
        g.CUR_ART_RESET()
        g.COM('cur_atr_set,attribute=.drill,option=non_plated')
        g.ADD_PAD(xE, yE, "r" + str(tool), attr='yes')
        g.CUR_ART_RESET()
        g.AFFECTED_LAYER('slot_pre_hole', 'no')


def slot_Rotate(stepName,drl_layer='drl'):
    # === 槽孔旋转 ===
    # 更改短槽孔旋转角度 http://192.168.2.120:82/zentao/story-view-4511.html

    global slot_no_process,short_slot_exists,slot_rotate
    slot_rotate = 'slot_rot_%s_%s' % (stepName,drl_layer)
    slot_no_process = 'slot_no_process_%s_%s' % (stepName,drl_layer)
    if drl_layer == 'drl':
        bak_layer = 'tk.ykj'
    else:
        bak_layer = '%s++' % drl_layer
    g.VOF()
    g.DELETE_LAYER(slot_rotate)
    g.DELETE_LAYER(slot_no_process)
    # g.DELETE_LAYER('tk.ykj')
    g.VON()
    g.CREATE_LAYER(slot_rotate)
    g.CREATE_LAYER(slot_no_process)
    # 20200410周涌要求备份一个通孔层tk.ykj
    if g.LAYER_EXISTS(bak_layer,job=jobName,step=stepName) == 'no':
        g.CREATE_LAYER(bak_layer, ins_lay=drl_layer, context='board', add_type='drill')
    g.CLEAR_LAYER()
    g.AFFECTED_LAYER(bak_layer,'yes')
    g.SEL_DELETE()
    g.AFFECTED_LAYER(bak_layer,'no')

    # step_info = g.DO_INFO('-t job -e %s -m script -d STEPS_LIST' % jobName)
    # for step in step_info['gSTEPS_LIST']:
    #     g.OPEN_STEP(step)
    #     g.COM(
    #         'copy_layer,source_job=%s,source_step=%s,source_layer=drl,dest=layer_name,dest_layer=tk.ykj,mode=replace,invert=no' % (
    #         jobName, step))
    #     g.CLOSE_STEP()
    # g.OPEN_STEP(stepName,job=jobName)
    g.COM(
        'copy_layer,source_job=%s,source_step=%s,source_layer=%s,dest=layer_name,dest_layer=%s,mode=replace,invert=no' % (
        jobName, stepName,drl_layer,bak_layer))
    g.CHANGE_UNITS('mm')
    g.CLEAR_LAYER()
    g.AFFECTED_LAYER(drl_layer, 'yes')
    g.FILTER_RESET()
    g.FILTER_SET_TYP('line')
    g.FILTER_SELECT()
    g.FILTER_RESET()
    count = int(g.GET_SELECT_COUNT())
    if count > 0:
        g.SEL_COPY(slot_no_process)
    g.AFFECTED_LAYER(drl_layer, 'no')

    rotate_list = []
    info = g.INFO(' -t layer -e %s/%s/%s -m script -d FEATURES,units=mm' % (jobName, stepName, slot_no_process))
    no_define_attr = []
    for line in info[1:]:
        getline = line.strip().split()
        xs = float(getline[1])
        ys = float(getline[2])
        xe = float(getline[3])
        ye = float(getline[4])
        xc = (xe + xs) * 0.5
        yc = (ye + ys) * 0.5
        sym = getline[5]
        try:
            attr = getline[8].strip(';')
        except IndexError:
            attr = '.drill=plated'
            no_define_attr.append(sym)

        slot_obj = slotRotate(xs, ys, xe, ye, xc, yc, sym, attr)
        # === 无需求，增加一个槽孔方向检查，尽量在数学象限的第一二象限，避免什么角度的槽孔都有
        if ye < ys:
            slot_obj.add_note(xs, ys)

        # print 'L:%s Sym:%s Ratid:%s' % (slot_obj.length,slot_obj.sym,slot_obj.ratio)
        s_ratio = Decimal(str(slot_obj.ratio))
        if 0.391 <= slot_obj.diameter < 0.809:
            # 0.391-0.609,也即0.4<=D<=0.6 # 也即0.65<=D<0.8
            # ==========================================================================================================
            if s_ratio >= Decimal('2.0'):
                # 长宽比大于1.95001按2.0补偿0度
                slot_obj.rotate_slot(xs, ys, sym, 0.0,drl_layer=drl_layer)
            elif Decimal('1.8') < s_ratio < Decimal('2.0'):
                # 长宽比大于1.70001按1.75补偿3度
                slot_obj.rotate_slot(xs, ys, sym, 3.0,drl_layer=drl_layer)
                rotate_list.append(sym)
            elif Decimal('1.5') < s_ratio <= Decimal('1.8'):
                # 长宽比大于1.35001按1.4补偿3度
                slot_obj.rotate_slot(xs, ys, sym, 6.0,drl_layer=drl_layer)
                rotate_list.append(sym)
            elif Decimal('1') < s_ratio <= Decimal('1.5'):
                # 长宽比大于0.95001按1.0补偿10度
                slot_obj.rotate_slot(xs, ys, sym, 8.0,drl_layer=drl_layer)
                rotate_list.append(sym)
        # elif 0.641 <= slot_obj.diameter < 0.809:
        #     # 也即0.65<=D<0.8
        #     # ===============================================================================================
        #     if s_ratio >= Decimal('2.0'):
        #         # 长宽比大于1.95001按2.0补偿0度
        #         slot_obj.rotate_slot(xs, ys, sym, 0.0,drl_layer=drl_layer)
        #     elif Decimal('1.75') <= s_ratio < Decimal('2.0'):
        #         # 长宽比大于1.70001按1.75补偿3度
        #         slot_obj.rotate_slot(xs, ys, sym, 3.0,drl_layer=drl_layer)
        #         rotate_list.append(sym)
        #     elif Decimal('1.4') <= s_ratio < Decimal('1.75'):
        #         # 长宽比大于1.35001按1.4补偿3度
        #         slot_obj.rotate_slot(xs, ys, sym, 3.0,drl_layer=drl_layer)
        #         rotate_list.append(sym)
        #     elif Decimal('1') < s_ratio < Decimal('1.4'):
        #         # 长宽比大于0.95001按1.0补偿10度
        #         slot_obj.rotate_slot(xs, ys, sym, 5.0,drl_layer=drl_layer)
        #         rotate_list.append(sym)
        elif 0.841 <= slot_obj.diameter < 1.259:
            # 也即0.85<=D<=1.25
            # ==========================================================================================================
            if s_ratio >= Decimal('2.0'):
                # 长宽比大于1.95001按2.0补偿0度
                slot_obj.rotate_slot(xs, ys, sym, 0.0,drl_layer=drl_layer)
            elif Decimal('1.8') < s_ratio < Decimal('2.0'):
                # 长宽比大于1.70001按1.75补偿3度
                slot_obj.rotate_slot(xs, ys, sym, 3.0,drl_layer=drl_layer)
                rotate_list.append(sym)
            elif Decimal('1.5') < s_ratio <= Decimal('1.8'):
                # 长宽比大于1.35001按1.4补偿3度
                slot_obj.rotate_slot(xs, ys, sym, 4.0,drl_layer=drl_layer)
                rotate_list.append(sym)
            elif Decimal('1.25') < s_ratio <= Decimal('1.5'):
                # 长宽比大于0.95001按1.0补偿10度
                slot_obj.rotate_slot(xs, ys, sym, 5.0,drl_layer=drl_layer)
                rotate_list.append(sym)
            elif Decimal('1') < s_ratio <= Decimal('1.25'):
                # 长宽比大于0.95001按1.0补偿10度
                slot_obj.rotate_slot(xs, ys, sym, 6.0,drl_layer=drl_layer)
                rotate_list.append(sym)
        elif 1.291 <= slot_obj.diameter <= 1.959:
            # 也即1.3<=D<=1.95
            # ==========================================================================================================
            if s_ratio >= Decimal('2.0'):
                # 长宽比大于1.95001按2.0补偿0度
                slot_obj.rotate_slot(xs, ys, sym, 0.0,drl_layer=drl_layer)
            elif Decimal('1.8') < s_ratio < Decimal('2.0'):
                # 长宽比大于1.70001按1.75补偿3度
                slot_obj.rotate_slot(xs, ys, sym, 2.0,drl_layer=drl_layer)
                rotate_list.append(sym)
            elif Decimal('1.5') < s_ratio <= Decimal('1.8'):
                # 长宽比大于1.35001按1.4补偿3度
                slot_obj.rotate_slot(xs, ys, sym, 3.0,drl_layer=drl_layer)
                rotate_list.append(sym)
            elif Decimal('1.25') < s_ratio <= Decimal('1.5'):
                # 长宽比大于1.35001按1.4补偿3度
                slot_obj.rotate_slot(xs, ys, sym, 4.0,drl_layer=drl_layer)
                rotate_list.append(sym)
            elif Decimal('1') < s_ratio <= Decimal('1.25'):
                # 长宽比大于0.95001按1.0补偿10度
                slot_obj.rotate_slot(xs, ys, sym, 5.0,drl_layer=drl_layer)
                rotate_list.append(sym)
        elif 1.991<= slot_obj.diameter <= 3.209:
            # 钻咀大于等于2.0mm
            # ==========================================================================================================
            if s_ratio >= Decimal('2.0'):
                # 长宽比大于1.95001按2.0补偿0度
                slot_obj.rotate_slot(xs, ys, sym, 0.0,drl_layer=drl_layer)
            elif Decimal('1.5') < s_ratio < Decimal('2.0'):
                # 长宽比大于1.35001按1.4补偿3度
                slot_obj.rotate_slot(xs, ys, sym, 2.0,drl_layer=drl_layer)
                rotate_list.append(sym)
            elif Decimal('1.25') < s_ratio <= Decimal('1.5'):
                # 长宽比大于1.35001按1.4补偿3度
                slot_obj.rotate_slot(xs, ys, sym, 3.0,drl_layer=drl_layer)
                rotate_list.append(sym)
            elif Decimal('1') < s_ratio <= Decimal('1.25'):
                # 长宽比大于0.95001按1.0补偿5度
                slot_obj.rotate_slot(xs, ys, sym, 5.0,drl_layer=drl_layer)
                rotate_list.append(sym)
        elif slot_obj.diameter > 3.210:
            # 钻咀大于3.2mm
            # http://192.168.2.120:82/zentao/story-view-6379.html
            # ==========================================================================================================
            if s_ratio >= Decimal('2.0'):
                # 长宽比大于1.95001按2.0补偿0度
                slot_obj.rotate_slot(xs, ys, sym, 0.0,drl_layer=drl_layer)
            elif Decimal('1.5') < s_ratio < Decimal('2.0'):
                # 长宽比大于1.35001按1.4补偿0度
                slot_obj.rotate_slot(xs, ys, sym, 0.0,drl_layer=drl_layer)
                rotate_list.append(sym)
            elif Decimal('1.25') < s_ratio <= Decimal('1.5'):
                # 长宽比大于1.35001按1.4补偿3度
                slot_obj.rotate_slot(xs, ys, sym, 3.0,drl_layer=drl_layer)
                rotate_list.append(sym)
            elif Decimal('1') < s_ratio <= Decimal('1.25'):
                # 长宽比大于0.95001按1.0补偿5度
                slot_obj.rotate_slot(xs, ys, sym, 5.0,drl_layer=drl_layer)
                rotate_list.append(sym)        
        else:
            # msg_box = msgBox()
            # msg_box.warning(None, '短槽旋转,做角度补偿', '孔径:%s,在规范中无定义!' % slot_obj.diameter, QMessageBox.Ok)
            warn_mess_list.append(
                {'type': 'warn', 'info': 'step:%s 层:%s短槽旋转,做角度补偿,孔径:%s,在规范中无定义!' % (stepName, drl_layer, slot_obj.diameter)})
    no_define_num = len(no_define_attr)
    if no_define_num > 0:
        list_str = ','.join(list(set(no_define_attr)))
        warn_mess_list.append(
            {'type': 'warn', 'info': '槽旋转 step:%s 层:%s 槽%s 总数量%s未定义属性,按PTH处理!' % (stepName, drl_layer, list_str,no_define_num)})
    g.WORK_LAYER(drl_layer)
    if len(rotate_list) > 0:
        # g.COM('display_layer,name=%s,display=yes,number=2' % bak_layer)
        # msg_box = msgBox()
        # msg_box.information(None, '短槽旋转,做角度补偿', '脚本运行成功,请检查比较tk.ykj!', QMessageBox.Ok)
        # warn_mess_list.append({'type':'ok','info':'step:%s 层:%s短槽旋转,做角度补偿运行完成，请对比查看层别%s' % (stepName, drl_layer, bak_layer) })
        short_slot_exists = 'yes'
    else:
        pass
        # --没有需要旋转的短槽，删除tk.ykj层别后提醒
        # warn_mess_list.append({'type':'warn','info':'step:%s 层:%s没有需要旋转的短槽，请检查！' % (stepName, drl_layer) })
        # msg_box = msgBox()
        # msg_box.warning(None, '警告：%s,step:%s 层:%s' % (jobName, stepName, drl_layer), '没有需要旋转的短槽，请检查！', QMessageBox.Ok)
        # g.DELETE_LAYER('tk.ykj')
    g.DELETE_LAYER(slot_rotate)
    g.DELETE_LAYER(slot_no_process)
    # g.COM('zoom_home')


def slot_Pre_Hole(stepName,drl_layer='drl'):
    # === 槽孔加预钻孔 ===
    global slot_pre_hole
    slot_pre_hole = 'slot_pre_hole_%s_%s' % (stepName, drl_layer)
    slot_holes = 'slot_holes_%s_%s' % (stepName, drl_layer)
    g.VOF()
    g.DELETE_LAYER(slot_pre_hole)
    g.DELETE_LAYER(slot_holes)
    g.VON()
    g.CREATE_LAYER(slot_pre_hole)
    g.CREATE_LAYER(slot_holes)
    g.CHANGE_UNITS('mm')
    g.CLEAR_LAYER()
    g.AFFECTED_LAYER(drl_layer, 'yes')
    g.FILTER_RESET()
    g.FILTER_SET_TYP('line')
    g.FILTER_SELECT()
    g.FILTER_RESET()
    count = int(g.GET_SELECT_COUNT())
    if count > 0:
        g.SEL_COPY(slot_holes)
    g.AFFECTED_LAYER(drl_layer, 'no')
    info = g.INFO(' -t layer -e %s/%s/%s -m script -d FEATURES,units=mm' % (jobName, stepName, slot_holes))
    no_define_attr = []
    for line in info[1:]:
        getline = line.strip().split()
        xs = float(getline[1])
        ys = float(getline[2])
        xe = float(getline[3])
        ye = float(getline[4])
        sym = getline[5]
        # attr = getline[8].strip(';')
        try:
            attr = getline[8].strip(';')
        except IndexError:
            attr = '.drill=plated'
            no_define_attr.append(sym)
            # warn_mess_list.append(
            #     {'type': 'warn', 'info': '槽导引孔 step:%s 层:%s 槽%s未定义属性,按PTH处理!' % (stepName, drl_layer, sym)})
        slot_obj = slotPreHole(xs, ys, xe, ye, sym, attr)
        if slot_obj.ratio == 1:
            pass
        # elif 0.390 < slot_obj.diameter < 0.610 and Decimal(str(slot_obj.ratio)) <= Decimal('1.25'):
        #     slot_obj.add_pre_type_F()
        elif Decimal(str(slot_obj.ratio)) < Decimal('2'):
            slot_obj.add_pre_type_E(drl_layer=drl_layer)
    no_define_num = len(no_define_attr)
    if no_define_num > 0:
        list_str = ','.join(list(set(no_define_attr)))
        warn_mess_list.append(
            {'type': 'warn', 'info': '槽导引孔 step:%s 层:%s 槽%s 总数量%s 未定义属性,按PTH处理!' % (stepName, drl_layer, list_str, no_define_num)})
    g.CLEAR_LAYER()
    g.AFFECTED_LAYER(slot_pre_hole, 'yes')
    g.CUR_ATR_SET('.bit', text='slot_pre_hole', reset=0, add=True)
    g.SEL_COPY(drl_layer)
    if drl_layer == 'drl':
        if g.LAYER_EXISTS('tk.ykj',job=jobName,step=stepName) == 'yes':
            g.SEL_COPY('tk.ykj')

    g.AFFECTED_LAYER(slot_pre_hole, 'no')
    g.WORK_LAYER(slot_holes)
    g.COM('display_layer,name=%s,display=yes,number=2' % slot_pre_hole)
    g.COM('zoom_home')
    # warn_mess_list.append({'type': 'ok', 'info': 'step:%s 层:%s短槽添加预钻孔运行完成' % (stepName, drl_layer)})


# --循环STEP列表
def LOOP_STEP():
    # === 2023.03.09 Song 前置槽孔导引孔选择，如果导引孔信息有误，提前报出
    global slot_info
    oracle_info = Oracle_info()
    slot_info = oracle_info.get_Inplan_info()

    for step in step_list:
        # match = re.compile(r'^(edit|set)')
        # --当匹配时，跳过循环
        # if 'edit' in step or 'set' in step:
        # --打开STEP
        g.OPEN_STEP(step)
        g.CLEAR_LAYER()
        # --循环处理DRL层
        LOOP_DRL(step)
        # --还原属性列表
        g.FILTER_RESET()
        # --关闭STEP(保留当前STEP不关闭)
        if step != 'edit':
            # PRINT(u'关闭STEP:' + str(step))
            g.CLOSE_STEP()
        # else:
        #    # 获取的STEP名有BUG为空时候跳过 20250403 by ynh http://192.168.2.120:82/zentao/story-view-8671.html
        #     if not step :
        #         continue
        #     if step in ['orig', 'net']:
        #         continue
        #
        #     g.OPEN_STEP(step)
        #     if g.LAYER_EXISTS('tk.ykj', job=jobName, step=step) == 'no':
        #         g.CREATE_LAYER('tk.ykj', ins_lay='drl', context='board', add_type='drill')
        #     g.COM(
        #         'copy_layer,source_job=%s,source_step=%s,source_layer=drl,dest=layer_name,dest_layer=tk.ykj,mode=replace,invert=no' % (
        #             jobName, step))
        #     g.CLOSE_STEP()

# --循环Drl列表
def LOOP_DRL(step):
    global gDATUMx, gDATUMy
    # --取出当前Step的信息
    # datuMxy = GEN.DO_INFO('-t step -e %s/%s -m script -d DATUM' % (job, step))

    # gDATUMx = float(datuMxy['gDATUMx'])
    # gDATUMy = float(datuMxy['gDATUMy'])

    # --从资料中随便选择一个孔，用于判断是否有改动过初始的origin
    datumDic = g.getDatum(jobName, step, drl_list[0], units='mm')
    gDATUMx = datumDic['datum_x']
    gDATUMy = datumDic['datum_y']
    # GEN.PAUSE("DATUMx:%s DATUMy:%s" % (gDATUMx, gDATUMy))

    for drl in drl_list:
        # PRINT(u'匹配非drl|2nd的钻孔层...')
        # --当匹配时，跳过循环
        if 'drl' != drl and '2nd' != drl:
            continue

        slot_Rotate(step, drl_layer=drl)
        slot_Pre_Hole(step, drl_layer=drl)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    jobName = os.environ.get('JOB', None)
    # stepName = os.environ.get('STEP', None)
    g = genCOM.GEN_COM()
    # global short_slot_exists, warn_mess_list
    short_slot_exists = 'no'
    warn_mess_list = []
    """定义全局变量"""
    # global drl_list, step_list
    # --获取钻带列表
    drl_list = g.GET_ATTR_LAYER('drill')
    # PRINT(eval(drl_list))

    # --获取STEP列表
    step_list = get_panelset_sr_step(jobName, 'panel')
    if not step_list:
        msg_box = msgBox()
        msg_box.warning(None, '警告,程序将以10004退出',
                        'panel内未拼板，请先完成panel拼板，并再次运行程序！',
                        QMessageBox.Ok)
        exit(1)
    if g.LAYER_EXISTS('tk.ykj', job=jobName,step=step_list[0]) == 'yes':
        msg_box = msgBox()
        msg_box.warning(None, '警告,程序将以10004退出', 'tk.ykj 层别存在，如再次运行添加槽孔旋转及预钻孔旋转，请还原tk.ykj层别到钻孔层，并再次运行程序！', QMessageBox.Ok)
        exit(1)
    # --循环STEP处理钻带
    LOOP_STEP()
    print 'short_slot_exists',short_slot_exists
    if g.LAYER_EXISTS('tk.ykj', job=jobName,step=step_list[0]) == 'yes' and short_slot_exists == 'no':
        g.DELETE_LAYER('tk.ykj')
    # print warn_mess_list
    if len(warn_mess_list) != 0:
        msg_box = msgBox()
        msg_box.warning(None, '短槽处理程序完成，有如下提示', "\n".join([i['type']+"___"+i['info'] for i in warn_mess_list]), QMessageBox.Ok)
    else:
        msg_box = msgBox()
        msg_box.information(None, '提示', "短槽处理程序完成", QMessageBox.Ok)

