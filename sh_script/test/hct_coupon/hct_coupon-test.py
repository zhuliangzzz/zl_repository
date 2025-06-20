#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2020/04/15
# @Revision     :    2.0.0
# @File         :    hct_coupon_v2.py
# @Software     :    PyCharm
# @Usefor       :    新版HCT Coupon
# ---------------------------------------------------------#

import os
import platform
import re
import sys
from PyQt4 import QtCore, QtGui

# --加载相对位置，以实现InCAM与Genesis共用
if platform.system() == "Windows":
    # sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"D:/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genCOM_26 as genCOM
import gClasses
from genesisPackages import get_layer_selected_limits
from get_erp_job_info import get_drill_information,get_barcode_mianci


# 设置编码函数
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

# 设置解码函数
try:
    _encoding = QtGui.QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class MAIN:
    def __init__(self):
        self.GEN = genCOM.GEN_COM()
        self.job_name = os.environ.get('JOB', None)
        cust_num = self.job_name[1:4]
        if cust_num == 'b58':
            self.Message(u'客户：%s 不需要跑旧板HCT Coupon,程序退出' % self.appVer)
            exit(0)


        self.inplan_job = self.job_name.split('-')[0].upper()
        self.big_laser_holes = []
        self.dw_size, self.mianci = self.get_inplan_information(self.inplan_job)

        self.appVer = 'v2.6'
        self.panel_step = 'panel'
        self.set_exists = self.GEN.STEP_EXISTS('set')
        if self.set_exists == 'yes':
            self.set_step = 'set'
        else:
            self.set_step = 'edit'
        # 定义板内step名
        self.pcs_step = 'edit'
        self.net_step = 'net'

        self.oldStepExist = 'no'
        self.bakupStepName = 'hct-coupon__bakup__'
        self.allDrlInfo = {}
        self.laser_reg = re.compile(r's\d{2,4}$|s\d{1,2}-\d{1,2}$')
        self.mk_reg = re.compile(r'b\d{2,4}$|b\d{1,2}-\d{1,2}$')
        # --获取相关信息
        self.outLay = self.GEN.GET_ATTR_LAYER('outer')
        self.innerLay = self.GEN.GET_ATTR_LAYER('inner')
        self.drlLay = 'drl'
        self.drill_list = self.GEN.GET_ATTR_LAYER('drill')
        if 'drl' not in self.drill_list:
            if 'cdc' in self.drill_list:
                self.drlLay = 'cdc'
            elif 'cds' in self.drill_list:
                self.drlLay = 'cds'
            else:
                self.Message(u'版本：%s 无有效钻孔层，程序退出' % self.appVer)
                exit(0)

        # 层数定义
        try:
            # === 存在料号名格式不为数字的情况 2020.07.31
            self.layer_num = int(self.job_name[4:6])
        except ValueError:
            # inner + outer的数量
            self.layer_num = len(self.outLay + self.innerLay)
        # === 增加模式选择，当laser层为常规贯穿一层设计时 s1-2、s2-3(反向相同)，有s1-3存在时跑两个hct-coupon
        self.couponTimes = 'Once'
        self.maskLay = self.GEN.GET_ATTR_LAYER('solder_mask')
        self.mdLay = ['md1', 'md2']
        self.etch_layers = self.get_etch_layer()
        self.laser_layers, self.mk_layers = self.get_laser_mk_layers()
        # === 备用变量，当设计两个hct-coupon时，需镭射分孔，以下语句对 self.couponTimes 进行判断
        self.laser_layers_one = []
        self.laser_layers_two = []
        self.top_lasers, self.bot_lasers = self.get_top_bot_laser()
        self.laser_end_layers = []
        self.laser_through_layers = []
        # 备用变量，无pth通孔设计时，用于判断判断埋孔层的起始层别与toplaser的endlayer botlaser的endlayer 是否相同
        self.top_laser_end_layer = ''
        self.bot_laser_end_layer = ''
        self.mk_layer = ''
        # 取toplaser的endlayer botlaser的endlayer
        top_laser_num = list(set(self.splitLaserLayerName(self.top_lasers)))
        top_laser_num.sort(reverse=False)

        if len(self.top_lasers) == 1:
            # === 仅有一层镭射时，不检测镭射层连续性 用于适应仅有s1-3设计的情况
            self.laser_end_layers.append(top_laser_num[-1])
            self.top_laser_end_layer = top_laser_num[-1]
            self.laser_through_layers += top_laser_num[1:-1]
        else:
            if len(top_laser_num) > 0:
                # 检测镭射层是否连续，不连续则提示无此模型
                if self.checkLayerContinue(top_laser_num):
                    self.laser_end_layers.append(top_laser_num[-1])
                    self.top_laser_end_layer = top_laser_num[-1]
                    self.laser_through_layers += top_laser_num[1:-1]

        bot_laser_num = list(set(self.splitLaserLayerName(self.bot_lasers)))
        bot_laser_num.sort(reverse=True)

        if len(self.bot_lasers) == 1:
            # === 仅有一层镭射时，不检测镭射层连续性
            self.laser_end_layers.append(bot_laser_num[-1])
            self.bot_laser_end_layer = bot_laser_num[-1]
            self.laser_through_layers += bot_laser_num[1:-1]
        else:
            # 检测镭射层是否连续，不连续则提示无此模型
            if len(bot_laser_num) > 0:
                # 检测镭射层是否连续，不连续则提示无此模型
                if self.checkLayerContinue(bot_laser_num):
                    self.laser_end_layers.append(bot_laser_num[-1])
                    self.bot_laser_end_layer = bot_laser_num[-1]
                    self.laser_through_layers += bot_laser_num[1:-1]

        self.modeUse = 'normal'  # 另一个是 noPthDrl
        if len(top_laser_num) == 0 or len(bot_laser_num) == 0:
            self.modeUse = 'oneside'
            if len(top_laser_num) == 0:
                self.top_laser_end_layer = 1
                self.sidemode = 's'
            if len(bot_laser_num) == 0:
                self.bot_laser_end_layer = self.layer_num
                self.sidemode = 'c'
        # # TODO 暂时退出项目
        # exit (0)

        # --调用程序
        self.runMain()

    def runMain(self):
        self.check_layer_name(self.laser_layers)
        if not self.create_coupon():
            self.Message(u'版本：%s运行过程中有异常抛出，程序退出' % self.appVer)
            exit(0)
        else:
            self.Message(u'版本：%s程序完成' % self.appVer)
            exit(0)

    def create_coupon(self):
        # 定义镭射hct模块名称
        nPlus = self.get_plus()
        # print nPlus
        self.getAddType()
        if self.modeUse == 'normal':
            self.src_coupon = 'hct-normal'
        elif self.modeUse == 'noPthDrl':
            self.src_coupon = 'hct-nopthdrl'
            # 判断无pth通孔设计时，用于判断判断埋孔层的起始层别与toplaser的endlayer botlaser的endlayer 是否相同
            if 'b%s-%s' % (self.top_laser_end_layer, self.bot_laser_end_layer) in self.mk_layers:
                self.mk_layer = 'b%s-%s' % (self.top_laser_end_layer, self.bot_laser_end_layer)
            else:
                # self.Message(u'无pth通孔设计，埋孔层非laser的end层别，无此模型')
                # return False
                self.allDrlInfo[self.drlLay] = {'min_pth': 452}
                self.modeUse = 'normal'
                self.src_coupon = 'hct-normal'
        elif self.modeUse == 'oneside':
            self.src_coupon = 'hct-oneside'
        else:
            self.Message(u'未定义hct模型')

        if self.couponTimes == 'Once':
            self.createStep(self.src_coupon, 'hct-coupon')
            prof_xmax = 45
            prof_ymax = 6.858
            self.GEN.COM('profile_rect,x1=0,y1=0,x2=%s,y2=%s' % (prof_xmax, prof_ymax))
            self.addLayerDetail('hct-coupon')
            if self.oldStepExist == 'yes':
                self.reUseBackupCoupon()
        elif self.couponTimes == "Twice":
            self.createStep(self.src_coupon, 'hct-coupon')
            prof_xmax = 45
            prof_ymax = 6.858
            self.GEN.COM('profile_rect,x1=0,y1=0,x2=%s,y2=%s' % (prof_xmax, prof_ymax))

            self.addLayerDetail('hct-coupon', throughmode='twice', twicemode='one')
            if self.oldStepExist == 'yes':
                self.reUseBackupCoupon()
            print 'self.laser_layers_two', self.laser_layers_two
            print 'self.big_laser_holes', self.big_laser_holes
            if set(self.laser_layers_two) == set(self.big_laser_holes):
                self.src_coupon = 'hct-bighole'
            print 'self.src_coupon',self.src_coupon
            self.createStep(self.src_coupon, 'hct-coupon-2')
            prof_xmax = 45
            prof_ymax = 6.858
            self.GEN.COM('profile_rect,x1=0,y1=0,x2=%s,y2=%s' % (prof_xmax, prof_ymax))

            self.addLayerDetail('hct-coupon-2', throughmode='twice', twicemode='two')
            if self.oldStepExist == 'yes':
                self.reUseBackupCoupon()
        return True

    def addLayerDetail(self, couStep, throughmode='once', twicemode='one'):
        """

        :param couStep:
        :param throughmode: one or two laser层的贯穿模式，所有镭射层均贯穿一层
        :param twicemode: 当throughmode 非one时,传递参数one 或two，代表贯穿一层或者两层
        :return:
        """
        # --拷贝阻焊层模板至正式阻焊层
        for lay in self.maskLay:
            self.GEN.COPY_LAYER(self.job_name, couStep, 'solder', lay)
        # --拷贝外层模板至正式外层，区分TOP及BOT面
        self.top_signal = self.etch_layers[:1]
        self.bot_signal = self.etch_layers[-1:]
        srctopsignal = 'topsignal'
        srcbotsignal = 'botsignal'
        if self.modeUse == 'oneside':
            srctopsignal = 'topsignal' + self.sidemode
            srcbotsignal = 'botsignal' + self.sidemode
        for lay in self.top_signal:
            self.GEN.COPY_LAYER(self.job_name, couStep, srctopsignal, lay)
        for lay in self.bot_signal:
            self.GEN.COPY_LAYER(self.job_name, couStep, srcbotsignal, lay)
        self.GEN.CLEAR_LAYER()

        if self.mianci == 's':
            self.GEN.AFFECTED_LAYER(self.top_signal[0],'yes')
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_ATR_SYMS('.orbotech_plot_stamp')
            self.GEN.FILTER_SELECT()
            if int(self.GEN.GET_SELECT_COUNT()) == 2:
                self.GEN.SEL_MOVE(self.bot_signal[0], mir='horizontal',x_anchor='35.467',y_anchor='4.5')
            self.GEN.FILTER_RESET()
        self.GEN.CLEAR_LAYER()

        # 判断是哪种添加模式，如果有通孔，copy通孔层，并更改大小
        if self.modeUse == 'normal' or self.modeUse == 'oneside':
            self.GEN.COPY_LAYER(self.job_name, couStep, 'drillthrough', self.drlLay)
            self.GEN.WORK_LAYER(self.drlLay)
            # 钻孔中存在两种孔，根据两种孔径进行区分，定位孔大小固定
            self.filterFeature('r250', 'r%s' % self.allDrlInfo[self.drlLay]['min_pth'])
            self.filterFeature('r1600', 'r%s' % self.dw_size)
            self.GEN.CLEAR_LAYER()
        elif self.modeUse == 'noPthDrl':
            # 在埋孔层中增加钻孔
            self.GEN.COPY_LAYER(self.job_name, couStep, 'mk', self.mk_layer)
            self.GEN.WORK_LAYER(self.mk_layer)
            self.GEN.SEL_CHANEG_SYM('r%s' % self.allDrlInfo[self.mk_layer]['minDrill'])
            self.GEN.CLEAR_LAYER()
            if self.GEN.LAYER_EXISTS(self.drlLay) == 'yes':
                self.GEN.COPY_LAYER(self.job_name, couStep, 'drillthrough', self.drlLay)
            else:
                self.Message(u'无通孔%s设计,新建此层别添加定位孔，请跑完后手动处理' % self.drlLay)
                self.GEN.CREATE_LAYER(self.drlLay)
                self.GEN.COPY_LAYER(self.job_name, couStep, 'drillthrough', self.drlLay)

            self.GEN.CLEAR_LAYER()
        else:
            return False
        # === sgt-c | sgt-s 层别 NPTH孔位置加pad ===
        self.GEN.WORK_LAYER(self.drlLay)
        # 钻孔中存在两种孔，根据两种孔径进行区分，定位孔大小固定
        self.GEN.FILTER_RESET()
        self.GEN.FILTER_OPTION_ATTR('.drill', 'non_plated')
        self.GEN.FILTER_SELECT()

        if int(self.GEN.GET_SELECT_COUNT()) > 0:
            affect_num = 0
            if self.GEN.LAYER_EXISTS('sgt-c', job=self.job_name, step=couStep) == 'yes':
                self.GEN.AFFECTED_LAYER('sgt-c', 'yes')
                affect_num += 1
            if self.GEN.LAYER_EXISTS('sgt-s', job=self.job_name, step=couStep) == 'yes':
                self.GEN.AFFECTED_LAYER('sgt-s', 'yes')
                affect_num += 1
            if affect_num > 0:
                # === 按影响层copy
                self.GEN.COM(
                    'sel_copy_other,dest=affected_layers,target_layer=,invert=no,dx=0,dy=0,size=254,x_anchor=0,y_anchor=0,rotation=0,mirror=none')
        self.GEN.CLEAR_LAYER()

        # === 挡点层制作 ===
        # 删除原有挡点层的内容
        self.GEN.AFFECTED_LAYER('md1', 'yes')
        self.GEN.AFFECTED_LAYER('md2', 'yes')
        self.GEN.SEL_DELETE()
        self.GEN.CLEAR_LAYER()
        self.GEN.WORK_LAYER(self.drlLay)
        self.GEN.SEL_COPY('md1')
        self.GEN.SEL_COPY('md2')
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('md1', 'yes')
        self.GEN.AFFECTED_LAYER('md2', 'yes')
        if 'min_pth' in self.allDrlInfo[self.drlLay]:
            min_size = float(self.allDrlInfo[self.drlLay]['min_pth'])
            resize = 10 * 25.4
            if 410 < min_size < 510:
                resize = 3 * 25.4
            change_size = min_size + resize
            self.filterFeature('r%s' % min_size, 'r%s' % change_size)
        if self.dw_size < 1010:
            resize = 6 * 25.4
        else:
            resize = -8 * 25.4
        change_size = self.dw_size + resize
        self.filterFeature('r%s' % self.dw_size, 'r%s' % change_size)

        # 拷贝镭射层模板至正式镭射层
        currentLaserLayers = []
        currentLaserThroughLayers = []
        currentLaserEndLayers = []
        # === 2020.07.31 增加了贯穿两层的hct模块跑法
        if throughmode == 'once':
            currentLaserLayers = self.laser_layers
            currentLaserThroughLayers = self.laser_through_layers
            currentLaserEndLayers = self.laser_end_layers
            start = int(self.top_laser_end_layer) + 1
            end = int(self.bot_laser_end_layer)
        elif throughmode == 'twice':
            if twicemode == 'one':
                currentLaserLayers = self.laser_layers_one
                currentLaserThroughLayers = []
                currentLaserEndLayers = [2, self.layer_num - 1]
                start = 3
                end = self.layer_num - 1
            elif twicemode == 'two':
                currentLaserLayers = self.laser_layers_two
                # currentLaserThroughLayers = [2, self.layer_num - 1]
                # === 镭射的贯穿层不添加pad ===
                currentLaserThroughLayers = []
                if self.src_coupon == 'hct-bighole':
                    currentLaserThroughLayers = [2, self.layer_num - 1]
                currentLaserEndLayers = [3, self.layer_num - 2]
                start = 4
                end = self.layer_num - 2

        for lay in currentLaserLayers:
            self.GEN.COPY_LAYER(self.job_name, couStep, 'laser', lay)
            # 更改每层最小孔尺寸
            self.GEN.WORK_LAYER(lay)
            if self.src_coupon == 'hct-bighole':
                self.GEN.SEL_CHANEG_SYM('%s' % self.allDrlInfo[lay]['minDrill'])
                self.GEN.COM("sel_break_level,attr_mode=merge")
            else:
                self.GEN.SEL_CHANEG_SYM('r%s' % self.allDrlInfo[lay]['minDrill'])

            self.GEN.COM('cur_atr_reset')
            self.GEN.COM('cur_atr_set,attribute=.drill,option=via')
            self.GEN.COM('cur_atr_set,attribute=.via_type,option=laser')
            self.GEN.COM('sel_change_atr,mode=add')
            self.GEN.COM('cur_atr_reset')

        # 镭射贯穿层
        for inum in currentLaserThroughLayers:
            self.GEN.COPY_LAYER(self.job_name, couStep, 'laserthrough', 'l' + str(inum))

        # 镭射终止层
        for inum in currentLaserEndLayers:
            self.GEN.COPY_LAYER(self.job_name, couStep, 'laserend', 'l' + str(inum))

        # 内层非镭射贯穿层

        # for inum in range(start, int(self.bot_laser_end_layer)):

        for inum in range(start, end):
            print 'x' * 40
            print inum
            self.GEN.COPY_LAYER(self.job_name, couStep, 'innerfill', 'l' + str(inum))

        # TODO 增加挡点层

        # 删除模块中的辅助层别
        for lay in ('solder', 'topsignal', 'botsignal', 'laserthrough', 'laserend', 'drillthrough', 'mk', 'innerfill',
                    'laser', 'topsignalc', 'topsignals', 'botsignalc', 'botsignals'):
            self.GEN.DELETE_LAYER(lay)

    def get_raoshao_laser_hole(self, drill_layer):
        """
        获取绕烧的镭射尺寸 原理建一个symbol 把coupon里面的changesymbol
        :param drill_layer: 钻孔层
        :return:
        """

        gjob = gClasses.Job(self.job_name)
        if self.GEN.STEP_EXISTS(job=self.job_name, step="edit") == 'yes':
            edit_step = gClasses.Step(gjob, "edit")
            edit_step.open()
            self.GEN.CHANGE_UNITS('mm')

            edit_step.removeLayer(drill_layer + "_tmp1")
            edit_step.removeLayer(drill_layer + "_tmp2")
            edit_step.copyLayer(gjob.name, edit_step.name, drill_layer, drill_layer + "_tmp1")
            edit_step.copyLayer(gjob.name, edit_step.name, drill_layer, drill_layer + "_tmp2")
            edit_step.clearAll()
            edit_step.affect(drill_layer + "_tmp1")
            edit_step.contourize(units='mm')
            edit_step.COM("sel_resize,size=-5")
            edit_step.resetFilter()
            edit_step.refSelectFilter(drill_layer + "_tmp2", mode="cover")
            if edit_step.featureSelected():
                edit_step.selectDelete()

            for index in range(1, 5):
                edit_step.VOF()
                edit_step.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(drill_layer + "_tmp1", index))
                edit_step.VON()
                edit_step.COM("sel_reverse")
                if edit_step.featureSelected():
                    edit_step.selectDelete()

                edit_step.resetFilter()
                edit_step.selectAll()
                if edit_step.featureSelected() == 1:
                    break

            edit_step.resetFilter()
            edit_step.selectAll()
            if edit_step.featureSelected() != 1:
                edit_step.removeLayer(drill_layer + "_tmp1")
                edit_step.removeLayer(drill_layer + "_tmp2")
                return None

            edit_step.isLayer()
            edit_step.clearAll()
            edit_step.affect(drill_layer + "_tmp2")
            edit_step.resetFilter()
            edit_step.refSelectFilter(drill_layer + "_tmp1")
            if edit_step.featureSelected():
                xmin, ymin, xmax, ymax = get_layer_selected_limits(edit_step, drill_layer + "_tmp2")
                center_x = (xmin + xmax) * 0.5
                center_y = (ymin + ymax) * 0.5
                edit_step.COM("sel_create_sym,symbol={0},x_datum={1},y_datum={2},"
                         "delete=no,fill_dx=2.54,fill_dy=2.54,attach_atr=no,"
                         "retain_atr=yes".format("raoshao_hole_size_tmp", center_x, center_y))
                edit_step.removeLayer(drill_layer + "_tmp1")
                edit_step.removeLayer(drill_layer + "_tmp2")
                return "raoshao_hole_size_tmp"

        edit_step.removeLayer(drill_layer + "_tmp1")
        edit_step.removeLayer(drill_layer + "_tmp2")
        return None

    def get_inplan_information(self, inplan_job):
        """获取hct coupon定位孔大小 及二维码蚀刻面次"""
        drill_info = get_drill_information(inplan_job,return_type='dict')
        print drill_info
        size = 0

        for info in drill_info:
            if info['DRILL_LAYER_'] == "一次钻孔" and info['DRILL_TYPE_'] == "HCT coupon定位孔":
                size = info['DRILL_SIZE']
                break

        for info in drill_info:
            laserReg = re.compile('L([0-9][0-9]?-[0-9][0-9]?)镭射')
            if laserReg.match(info['DRILL_LAYER_']):
                if "绕烧" in info['ERP_FINISH_SIZE_']:
                    # print 'DRILL_LAYER_', info['DRILL_LAYER_']
                    # print 'DRILL_SIZE', info['DRILL_SIZE']
                    self.big_laser_holes.append('s%s' % laserReg.match(info['DRILL_LAYER_']).group(1))

        mianci_info = get_barcode_mianci(inplan_job)
        mianci = None
        # print mianci_info
        if mianci_info:
            if "C" in mianci_info[0][1].upper():
                mianci = "c"

            if "S" in mianci_info[0][1].upper():
                mianci = "s"

        return size, mianci

    def splitLaserLayerName(self, layers):
        laser_split_reg = re.compile(r's(\d{1,2})-(\d{1,2})$')
        input_num = []
        for layer in layers:
            m = laser_split_reg.match(layer)
            if m:
                digt_s = int(m.group(1))
                digt_e = int(m.group(2))
                input_num += [digt_e] + [digt_s]
        return input_num

    def checkLayerContinue(self, list):
        # 输入列表的第一个值认为为top面的1，或者bot面的层别数
        errorMsg = ''
        if list[0] == 1:
            mode = 'increase'
            for i in range(len(list)):
                checki = i + 1
                if checki in list:
                    pass
                else:
                    errorMsg += u'镭射层别不是连续的设计，层别数字%s不符合添加hct-Coupon条件' % checki
        elif list[0] == int(self.layer_num):
            mode = 'decrease'
            for i in range(list[0], list[0] - len(list), -1):
                if i in list:
                    pass
                else:
                    errorMsg += u'镭射层别不是连续的设计，层别数字%s不符合添加hct-Coupon条件' % i
        else:
            errorMsg += u'镭射层别起始层不是top或bot面不符合添加hct-Coupon条件'
        if errorMsg != '':
            self.Message('%s' % errorMsg)
            return False
        return True

    def getAddType(self):
        """
        根据钻带列表，判断需要添加哪几个测试模块
        :return:返回添加测试模块类型，用于直接从Lib库中调用（建议与lib库中的命名保持一致）
        """
        # --遍历所有孔信息
        self.GEN.LOG(u'遍历传入参数的所有孔信息...')
        # 判断条件1-1 检测通孔层是否存在
        # 判断条件1-2 通孔层存在时是否有PTH孔存在
        # 以上两个条件满足时，使用模型一:normal 否则使用 noPthDrl

        if self.GEN.STEP_EXISTS(job=self.job_name, step="edit") == 'yes':
            # 板内最小孔剔除掉槽孔 及引孔
            gjob = gClasses.Job(self.job_name)

            edit_step = gClasses.Step(gjob, "edit")
            edit_step.open()
            self.GEN.CHANGE_UNITS('mm')
            edit_step.clearAll()
            edit_step.affect(self.drlLay)
            edit_step.copyLayer(gjob.name, "edit", self.drlLay, self.drlLay+"_tmp")
            edit_step.copyLayer(gjob.name, "edit", self.drlLay, self.drlLay+"_tmp1")
            edit_step.clearAll()
            edit_step.affect(self.drlLay+"_tmp1")
            edit_step.contourize(units='mm')
            edit_step.COM("sel_resize,size=-5")

            edit_step.clearAll()
            edit_step.affect(self.drlLay+"_tmp")
            edit_step.resetFilter()
            edit_step.filter_set(feat_types='line;arc')
            edit_step.selectAll()
            if edit_step.featureSelected():
                edit_step.moveSel("slot_tmp")
                edit_step.resetFilter()
                edit_step.refSelectFilter("slot_tmp")
                if edit_step.featureSelected():
                    edit_step.selectDelete()

                edit_step.removeLayer("slot_tmp")

            edit_step.resetFilter()
            edit_step.refSelectFilter(self.drlLay+"_tmp1", mode="cover")
            if edit_step.featureSelected():
                edit_step.selectDelete()

            hole_size = self.getMinPthHole(gjob.name, "edit", self.drlLay+"_tmp")
            if hole_size:
                self.allDrlInfo[self.drlLay]['min_pth'] = hole_size
            else:
                self.modeUse = 'noPthDrl'

            edit_step.removeLayer(self.drlLay+"_tmp")
            edit_step.removeLayer(self.drlLay+"_tmp1")

    def getMinPthHole(self, job, set_name, drill_name):
        """
        获取传入层别的最小pth孔(含via)
        :param job:
        :param set_name:
        :param drill_name:
        :return:
        """
        if self.GEN.LAYER_EXISTS(self.drlLay) == 'yes':
            getlist = self.GEN.DO_INFO("-t layer -e %s/%s/%s -d TOOL -p drill_size+type -o break_sr, units=mm" %
                                       (job, set_name, drill_name))
            if len(getlist['gTOOLdrill_size']) != 0:
                # 只选pth孔
                pth_tool = []
                for i in range(len(getlist['gTOOLdrill_size'])):
                    if getlist['gTOOLtype'][i] in ['via', 'plated']:
                        pth_tool.append(getlist['gTOOLdrill_size'][i])
                if len(pth_tool):
                    # 按孔径大小取最小值，而不是按str格式取 最小值
                    self.allDrlInfo[self.drlLay] = {}
                    mintool = min(pth_tool, key=lambda x: float(x))
                    if float(mintool) > 460:
                        # self.allDrlInfo[self.drlLay]['min_pth'] = 250
                        return None
                        # === V2.4 无合适pth孔时，使用盲埋模型 ===
                        # self.modeUse = 'noPthDrl'
                    else:
                        return mintool
        return None

    def createStep(self, srcStepName, desStepName):
        """
        判断step是否存在和创建step
        :param stepName: 检测的coupon step名
        :return: 创建结果
        """
        # --判断是否存在
        # 重写新建step方法如果存在备份旧的step，rename，并清空层别内容
        if self.GEN.STEP_EXISTS(job=self.job_name, step=desStepName) == 'yes':
            self.GEN.OPEN_STEP(desStepName, job=self.job_name)
            self.GEN.CLEAR_LAYER()
            self.GEN.COM('affected_layer, name=, mode=all, affected=yes')
            self.GEN.SEL_DELETE()
            self.GEN.CLEAR_LAYER()
            self.oldStepExist = 'yes'
            self.GEN.COM('rename_entity,job=%s,name=%s,new_name=%s,is_fw=no,type=step,fw_type=form' %
                         (self.job_name, desStepName, self.bakupStepName))

            # self.GEN.DELETE_ENTITY('step', desStepName, job=self.job_name)
        # --从Lib库中直接拷贝Step
        if platform.system() == "Windows":
            self.GEN.COPY_ENTITY('step', 'genesislib', srcStepName, self.job_name, desStepName)
        else:
            # --待插入Incam下的方法
            # === 区分InCAM 及Genesis
            if os.environ.get('INCAM_PRODUCT', None):
                self.GEN.COM('copy_entity_from_lib, job=%s, name=%s, type=step, profile=none' % (
                    self.job_name, srcStepName))
                self.GEN.COM('rename_entity,job=%s,name=%s,new_name=%s,is_fw=no,type=step,fw_type=form' %
                             (self.job_name, srcStepName, desStepName))
            else:
                self.GEN.COPY_ENTITY('step', 'genesislib', srcStepName, self.job_name, desStepName)

        # --打开STEP
        self.GEN.OPEN_STEP(desStepName, job=self.job_name)
        self.GEN.CHANGE_UNITS('mm')
        return

    def reUseBackupCoupon(self):
        """
        使用旧的step，并进行更新，优点，已拼入panel中的坐标不需变动
        :return:
        """
        self.GEN.OPEN_STEP(self.bakupStepName, job=self.job_name)
        self.GEN.CHANGE_UNITS('mm')
        prof_xmax = 45
        prof_ymax = 6.858
        # 检测新旧的step大小是否一致，不一致需提醒用户
        Pro_INFO = self.GEN.getProMinMax(self.job_name, self.bakupStepName)
        if Pro_INFO['proXmax'] != str(prof_xmax) or Pro_INFO['proYmax'] != str(prof_ymax):
            self.Message(u'更新hct-coupon后profile大小不一致\n，旧：%s，%s 新 %s,%s跑完后检查panel' %
                         (Pro_INFO['proXmax'], Pro_INFO['proYmax'], prof_xmax, prof_ymax))
        # 拼入新跑完的hctcoupon
        self.GEN.COM("sr_tab_add, line=1, step=%s, x=0, y=0, nx=1, ny=1" % 'hct-coupon')
        # 打散拼版，重建profile
        self.GEN.COM("sredit_reduce_nesting, mode = one_highest")
        self.GEN.COM('profile_rect,x1=0,y1=0,x2=%s,y2=%s' % (prof_xmax, prof_ymax))
        # 删除跑好的hct-coupon，重命名后旧的hct-coupon__backup__
        self.GEN.DELETE_ENTITY('step', 'hct-coupon', job=self.job_name)
        self.GEN.COM('rename_entity,job=%s,name=%s,new_name=%s,is_fw=no,type=step,fw_type=form' %
                     (self.job_name, self.bakupStepName, 'hct-coupon'))

    def get_laser_mk_layers(self):
        # 获取钻带名称列表
        laser_layers = []
        mk_layers = []
        drill_layers = self.GEN.GET_ATTR_LAYER('drill')
        for layer in drill_layers:
            if self.laser_reg.match(layer):
                min_laser = self.get_min_laser(layer)
                if layer in self.big_laser_holes:
                    # === TODO 计算出绕烧的孔径
                    min_laser = self.get_raoshao_laser_hole(layer)
                    if not min_laser:
                        self.Message(u'检测到层别：%s,应为大孔绕烧，实际未获得绕烧孔径' % (layer))

                if len(min_laser) > 0:
                    laser_layers.append(layer)
                    self.allDrlInfo[layer] = {'minDrill': min_laser}
            if self.mk_reg.match(layer):
                # min_mk = self.get_min_laser(layer)
                min_laser = self.get_min_laser(layer)
                if len(min_laser) > 0:
                    mk_layers.append(layer)
                    self.allDrlInfo[layer] = {'minDrill': min_laser}
        return laser_layers, mk_layers

    def get_min_laser(self, layer):
        info = self.GEN.DO_INFO("-t layer -e %s/%s/%s -d TOOL -p drill_size+type -o break_sr" %
                                (self.job_name, self.pcs_step, layer))
        if len(info['gTOOLdrill_size']) != 0:
            # 只选pth孔
            pth_tool = []
            for i in range(len(info['gTOOLdrill_size'])):
                if info['gTOOLtype'][i] in ['via', 'plated']:
                    pth_tool.append(info['gTOOLdrill_size'][i])
            if len(pth_tool):
                # 按孔径大小取最小值，而不是按str格式取最小值
                mintool = min(pth_tool, key=lambda x: float(x))
            else:
                mintool = ''
        else:
            mintool = ''
        return mintool

    def get_top_bot_laser(self):
        # 将镭射层区分顶部和底部
        top_laser = []
        bot_laser = []
        single_through = []
        removeLayer = ''
        for layer in self.laser_layers:
            start, end = self.get_drill_through(layer)
            digt_s = start[1:]
            digt_e = end[1:]
            # === 2020.07.31 增加是否镭射贯穿两层与贯穿一层同时存在的判断 eg:s1-2 s1-3
            single_through.append(abs(int(digt_s) - int(digt_e)))
            if int(digt_s) != self.layer_num / 2:
                if abs(int(digt_s) - int(digt_e)) == 1:
                    self.laser_layers_one.append(layer)
                elif abs(int(digt_s) - int(digt_e)) == 2:
                    self.laser_layers_two.append(layer)
                else:
                    self.Message(u'层别%s贯穿中间层非1或2，程序无此模型，退出' % layer)
                    exit(0)
            max_digt = max([int(digt_s), int(digt_e)])
            if int(digt_s) == self.layer_num / 2:
                # 增加ELIC设计，最内层芯板不计入设计
                self.Message(u'Any Layer 设计，最内层镭射不计入hct-coupon设计，忽略层别%s' % layer)
                # 在计数镭射层删除此层别
                removeLayer = layer
            elif max_digt > self.layer_num / 2:
                bot_laser.append(layer)
            else:
                top_laser.append(layer)
        # print 'self.laser_layers_one'
        # print self.laser_layers_one
        # print 'self.laser_layers_two'
        # print self.laser_layers_two
        # print 'x' * 40
        if len(self.laser_layers_one) != 0 and len(self.laser_layers_two) != 0:
            if len(self.laser_layers_one) != 2 or len(self.laser_layers_two) != 2:
                self.Message(u'程序仅支持外层镭射贯穿两层且一阶的情况，特殊类型，跑完后请检查')
                # exit(0)

        if removeLayer != '':
            self.laser_layers.remove(removeLayer)
        # === 增加是否贯穿两层及贯穿一层同时存在的情况
        tmochecklist = [i for i in single_through]
        tmpchecklist2 = list(set(tmochecklist))
        if len(tmpchecklist2) != 1:
            self.couponTimes = 'Twice'
        return top_laser, bot_laser

    def check_layer_name(self, layers):
        # 检查镭射命名
        errorMsg = u""
        for layer in layers:
            start, end = self.get_drill_through(layer)
            start_digt = start[1:]
            end_digt = end[1:]
            if '-' in layer:
                # 层名中间带"-"的情况
                digt_s = re.split(r'[s,b,bd,-]', layer)[-2]
                digt_e = re.split(r'[s,b,bd,-]', layer)[-1]
            else:
                errorMsg += u"%s 层，请按最新标准命名！\n" % layer
                # 层名中间不带"-"的情况
                digts = re.split(r'[s,b,bd,-]', layer)[-1]
                if len(digts) == 2:
                    digt_s = digts[0]
                    digt_e = digts[1]
                elif len(digts) == 3:
                    # s109默认按正确的层别名，先取两码再取一码
                    digt_s = digts[:2]
                    digt_e = digts[2:]
                    if math.fabs(int(digt_s) - int(digt_e)) > 2 and self.laser_reg.match(layer):
                        # 若相差过大，可能是旧的命名方式，先取一码再取两码，如s910,埋孔则不必
                        digt_s = digts[:1]
                        digt_e = digts[1:]
                else:
                    digt_s = digts[:2]
                    digt_e = digts[2:]
            max_digt = max([int(digt_s), int(digt_e)])
            if max_digt > self.layer_num / 2:
                if int(digt_s) < int(digt_e) and int(digt_s) != self.layer_num / 2:
                    errorMsg += u"%s 层钻带名命名不标准(起始层错误)，请按最新标准命名！\n" % layer
            if (digt_s == start_digt and digt_e == end_digt) or (digt_s == end_digt and digt_e == start_digt):
                pass
            else:
                errorMsg += u"%s 层，请检查钻带贯穿层！\n" % layer
        # 当有收集到错误信息时
        if errorMsg != '':
            self.Message('%s' % errorMsg)
            # 2020.06.23 暂时屏蔽此条
            # sys.exit(0)

    def filterFeature(self, includeSymbol, changeSize):
        """
        过滤选择，并修改其大小
        :param att: 属性名称
        :param txt: 对应的属性值
        :param changeSize: 修改的最终大小（含形状属性如:r450）
        :return:
        """
        self.GEN.FILTER_RESET()
        self.GEN.FILTER_SET_INCLUDE_SYMS(includeSymbol)
        self.GEN.FILTER_SELECT()
        if self.GEN.GET_SELECT_COUNT() > 0:
            self.GEN.SEL_CHANEG_SYM(changeSize)
            self.GEN.LOG(u'Symbol %s 属性对应的物体修改为%s 成功！' % (includeSymbol, changeSize))
            return True
        else:
            self.GEN.LOG(u'Symbol %s 属性对应的物体修改为%s 失败！' % (includeSymbol, changeSize))
            return False

    def get_drill_through(self, layer, job=os.environ.get('JOB', None), step=os.environ.get('STEP', None)):
        """返回起始层信息与终止层信息"""
        start = self.GEN.DO_INFO('-t layer -e %s/%s/%s -d DRL_START' % (job, step, layer))
        end = self.GEN.DO_INFO('-t layer -e %s/%s/%s -d DRL_END' % (job, step, layer))
        """防止C面镭射或S面镭射拉错孔带，拉到防焊或者其它非蚀刻层"""
        start_info = self.GEN.DO_INFO('-t layer -e %s/%s/%s -d SIDE' % (job, step, start['gDRL_START']))
        end_info = self.GEN.DO_INFO('-t layer -e %s/%s/%s -d SIDE' % (job, step, end['gDRL_END']))
        start_side = start_info['gSIDE']
        end_side = end_info['gSIDE']
        """顶层钻带校正"""
        if start_side == 'top':
            start_layer = 'l1'
        elif start_side == 'bottom':
            start_layer = 'l' + str(self.layer_num)
        else:
            start_layer = start['gDRL_START']
        """底层钻带校正"""
        if end_side == 'top':
            end_layer = 'l1'
        elif end_side == 'bottom':
            end_layer = 'l' + str(self.layer_num)
        else:
            end_layer = end['gDRL_END']
        # --返回两个值
        return start_layer, end_layer

    def get_plus(self):
        # 根据正反面镭射定义HDI阶数
        plus = 0
        if len(self.top_lasers) >= len(self.bot_lasers):
            plus = len(self.top_lasers)
        else:
            plus = len(self.bot_lasers)
        return plus

    def get_etch_layer(self):
        # 获取蚀刻层列表
        etch_layer = []
        for x, y in enumerate(xrange(self.layer_num), 1):
            etch_layer.append("l" + str(x))
        return etch_layer

    def Message(self, text, sel=1):
        """
        提示用的Message
        :param text: 传入显示的信息
        :param sel: 传入需要显示的按钮信息
        :return:
        """
        from PyQt4 import QtGui
        message = QtGui.QMessageBox()
        message.setText(text)
        if sel == 1:
            message.addButton(u"OK", QtGui.QMessageBox.AcceptRole)
        if sel != 1:
            message.addButton(u"是", QtGui.QMessageBox.AcceptRole)
            message.addButton(u"否", QtGui.QMessageBox.RejectRole)
        message.exec_()

        return message.clickedButton().text()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    # Form = QtGui.QWidget()
    main = MAIN()
    # sys.exit(app.exec_())

"""
2020.06.24 
版本：v2.1
宋超
1.增加hct-oneside模块，用于单面镭射的HCT-COUPON设计

2020.07.30
版本：V2.2
作者：宋超
1.根据多层板事业部六处需求，当有s1-2与s1-3两个镭射存在时，跑出两个hct-coupon

2021.10.08
版本：V2.3
作者：宋超
1.可以跑出s1-3镭射存在的hct-coupon 
http://192.168.2.120:82/zentao/story-view-3535.html

2022.03.18
版本：V2.4
作者：宋超
1.无合适PTH孔径时，使用盲埋模型，考虑是否使用inplan信息
http://192.168.2.120:82/zentao/story-view-4065.html

2022.10.14 
版本：V2.5
作者：宋超
1.Pth孔径判断由0.4 放开至0.45;
2.无合适pth孔径设计时，使用0.452进行钻孔导通
http://192.168.2.120:82/zentao/story-view-4272.html
"""
