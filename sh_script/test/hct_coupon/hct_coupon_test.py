#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2022/12/08
# @Revision     :    1.0.0
# @File         :    hct_coupon-test-V2.6.py
# @Software     :    PyCharm
# @Usefor       :    
# ---------------------------------------------------------#

import os
import platform
import re
import sys
import json
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


class MAIN(object):
    def __init__(self):
        self.GEN = genCOM.GEN_COM()
        self.job_name = os.environ.get('JOB', None)
        self.step_name = os.environ.get('STEP')
        # V2.6 B58客户不添加旧版 hct-coupon
        cust_num = self.job_name[1:4]
        if cust_num == 'b58':
            self.Message(u'客户：%s 不需要跑旧板HCT Coupon,程序退出' % cust_num)
            exit(0)
        self.pcs_step = 'edit'

        self.inplan_job = self.job_name.split('-')[0].upper()
        self.big_laser_holes = []
        self.dw_size, self.mianci = self.get_inplan_information(self.inplan_job)
        self.appVer = 'v2.6'
        self.allDrlInfo = {}
        self.laser_dict = {}
        self.laser_reg = re.compile(r's\d{2,4}$|s\d{1,2}-\d{1,2}$')
        self.mk_reg = re.compile(r'b\d{2,4}$|b\d{1,2}-\d{1,2}$')
        # --获取相关信息
        self.outLay = self.GEN.GET_ATTR_LAYER('outer')
        self.innerLay = self.GEN.GET_ATTR_LAYER('inner')
        self.drill_list = self.GEN.GET_ATTR_LAYER('drill')
        self.maskLay = self.GEN.GET_ATTR_LAYER('solder_mask')
        self.mdLay = ['md1', 'md2']
        if 'drl' in self.drill_list:
            self.drlLay = 'drl'
        else:
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

        self.etch_layers = self.get_etch_layer()
        self.laser_layers, self.mk_layers = self.get_laser_mk_layers()
        self.modeUse = 'normal'  # 另一个是 noPthDrl

        # --调用程序
        self.runMain()

    def runMain(self):
        get_check_result = self.check_layer_name(self.laser_layers)
        if not get_check_result:
            self.Message(u'版本：%s 料号：%s运行过程中检测未通过，程序退出' % (self.appVer,self.job_name))
            exit(0)

        self.get_top_bot_laser(self.laser_layers)
        for time in self.laser_dict:
            self.laser_dict[time]['laser_end_layers'] = []
            self.laser_dict[time]['laser_through_layers'] = []

            for side in ['top_laser','bot_laser']:
                if side in self.laser_dict[time]:
                    laser_num_list = list(set(self.splitLaserLayerName(self.laser_dict[time][side])))
                    if side == 'top_laser':
                        laser_num_list.sort(reverse=False)
                    elif side == 'bot_laser':
                        laser_num_list.sort(reverse=True)
                    else:
                        self.Message(u'版本：%s 料号：%s 字典中的key:%s 不正确' % (self.appVer,self.job_name, side))
                        exit(0)
                    self.laser_dict[time]['laser_end_layers'].append(laser_num_list[-1])
                    self.laser_dict[time]['%s_end_layer' % side] = laser_num_list[-1]
                    self.laser_dict[time]['laser_through_layers'] += laser_num_list[1:-1]
                    if time == 'twice':
                        if len(self.laser_dict[time][side]) == 1:
                            pass
                        else:
                            self.Message(u'版本：%s 料号：%s 目前仅支持hct-2为一阶的情况' % (self.appVer,self.job_name))
                            exit(0)
                    else:
                        get_reuslt = self.checkLayerContinue(laser_num_list)
                        if not get_reuslt:
                            self.Message(u'版本：%s 料号：%s运行过程中检测未通过，程序退出' % (self.appVer,self.job_name))
                            exit(0)

        if not self.create_coupon():
            self.Message(u'版本：%s运行过程中有异常抛出，程序退出' % self.appVer)
            exit(0)
        else:
            self.Message(u'版本：%s程序完成' % self.appVer)
            exit(0)

    def create_coupon(self):
        # 定义镭射hct模块名称
        # nPlus = self.get_plus()
        # # print nPlus
        self.getAddType()
        if self.modeUse == 'normal':
            self.src_coupon = 'hct-normal'
        elif self.modeUse == 'noPthDrl':
            self.src_coupon = 'hct-nopthdrl'

        # elif self.modeUse == 'oneside':
        #     self.src_coupon = 'hct-oneside'
        # else:
        #     self.Message(u'未定义hct模型')

        print json.dumps(self.laser_dict)
        for time in self.laser_dict:
            laser_mode = None
            if 'top_laser' not in self.laser_dict[time]:
                laser_mode = 'oneside'
                lib_coupon = 'hct-oneside'
                self.sidemode = 's'
                self.laser_dict[time]['top_laser_end_layer'] = 1

            elif 'bot_laser' not in self.laser_dict[time]:
                laser_mode = 'oneside'
                lib_coupon = 'hct-oneside'
                self.sidemode = 'c'
                self.laser_dict[time]['bot_laser_end_layer'] = self.layer_num
            else:
                if self.modeUse == 'normal':
                    lib_coupon = 'hct-normal'
                elif self.modeUse == 'noPthDrl':
                    lib_coupon = 'hct-nopthdrl'
                    des_mk_layer = 'b%s-%s' % (self.laser_dict[time]['top_laser_end_layer'], self.laser_dict[time]['bot_laser_end_layer'])
                    if des_mk_layer in self.mk_layers:
                        self.mk_layer = des_mk_layer
                    else:
                        self.allDrlInfo[self.drlLay] = {'min_pth': 452}
                        self.modeUse = 'normal'
                        lib_coupon = 'hct-normal'

            if laser_mode == 'oneside':
                if self.drlLay not in self.allDrlInfo:
                    self.allDrlInfo[self.drlLay] = {'min_pth': 452}
            print json.dumps(self.allDrlInfo,indent=2)
            print 'laser_mode',laser_mode
            # self.GEN.PAUSE('XXXXXXXXXXXXX')

            des_coupon = None
            if time == 'once':
                des_coupon = 'hct-coupon'
            elif time == 'twice':
                des_coupon = 'hct-coupon-2'

            if 'twice' in self.laser_dict:
                throughmode = 'twice'
            else:
                throughmode = 'once'
            self.bakupStepName = '%s__bakup__' % des_coupon
            laser_layers_two = self.laser_dict[time]['laser_layers']
            print 'laser_layers_two', laser_layers_two
            print 'self.big_laser_holes', self.big_laser_holes
            big_hole_mode = False
            if set(laser_layers_two) == set(self.big_laser_holes):
                # self.src_coupon = 'hct-bighole'
                big_hole_mode = True
                lib_coupon = 'hct-bighole'
            # === V2.6 增加，如果镭射孔径大于153 则使用大孔coupon，但不绕烧
            for las_layer in self.laser_dict[time]['laser_layers']:
                if not big_hole_mode:
                    if float(self.allDrlInfo[las_layer]['minDrill']) > 153:
                        lib_coupon = 'hct-bighole'
                        if laser_mode == 'oneside':
                            lib_coupon = 'hct-big-oneside'
                            # self.Message(u'版本：%s, 料号：%s 暂无单面镭射的大孔模型' % (self.appVer,self.job_name))
                            # exit(0)
                        else:
                            if self.modeUse == 'noPthDrl':
                                self.Message(u'版本：%s, 料号：%s 本使用<无通孔模型>，由于大孔laser存在使用<大孔模型>，改为通孔导通' % (self.appVer,self.job_name))
                                self.allDrlInfo[self.drlLay] = {'min_pth': 452}
                                self.modeUse = 'normal'

                        continue

            self.createStep(lib_coupon, des_coupon)
            prof_xmax = 45
            prof_ymax = 6.858
            self.GEN.COM('profile_rect,x1=0,y1=0,x2=%s,y2=%s' % (prof_xmax, prof_ymax))
            self.addLayerDetail(des_coupon,throughmode=throughmode, twicemode=time,big_hole=big_hole_mode,laser_mode=laser_mode)
            if self.oldStepExist == 'yes':
                self.reUseBackupCoupon()

        return True


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
                self.Message('%s' % errorMsg)
                return False
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
            return False
        return True

    def get_top_bot_laser(self, ip_laser_layers):
        # 将镭射层区分顶部和底部
        single_through = []
        for layer in ip_laser_layers:
            start, end = self.get_drill_through(layer)
            digt_s = start[1:]
            digt_e = end[1:]
            key_word = None
            side = None
            # === 2020.07.31 增加是否镭射贯穿两层与贯穿一层同时存在的判断 eg:s1-2 s1-3
            single_through.append(abs(int(digt_s) - int(digt_e)))
            if int(digt_s) == self.layer_num / 2 and abs(int(digt_s) - int(digt_e)) == 1:
                # 增加ELIC设计，最内层芯板不计入设计
                continue
            if abs(int(digt_s) - int(digt_e)) == 1:
                # laser_layers_one.append(layer)
                key_word = 'once'
            elif abs(int(digt_s) - int(digt_e)) == 2:
                # laser_layers_two.append(layer)
                key_word = 'twice'
            else:
                self.Message(u'层别%s贯穿中间层非1或2，程序无此模型，退出' % layer)
                exit(0)

            max_digt = max([int(digt_s), int(digt_e)])
            if max_digt > self.layer_num / 2:
                # bot_laser.append(layer)
                side = 'bot_laser'
            else:
                # top_laser.append(layer)
                side = 'top_laser'
            if key_word not in self.laser_dict:
                self.laser_dict[key_word] = {}
            if side not in self.laser_dict[key_word]:
                self.laser_dict[key_word][side] = []
            if 'laser_layers' not in self.laser_dict[key_word]:
                self.laser_dict[key_word]['laser_layers'] = []

            self.laser_dict[key_word][side].append(layer)
            self.laser_dict[key_word]['laser_layers'].append(layer)

        print self.laser_dict

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

    def getAddType(self):
        """
        根据钻带列表，判断需要添加哪几个测试模块
        :return:返回添加测试模块类型，用于直接从Lib库中调用（建议与lib库中的命名保持一致）
        """
        # --遍历所有孔信息
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

    def get_inplan_information(self, inplan_job):
        """获取hct coupon定位孔大小 及二维码蚀刻面次"""
        drill_info = get_drill_information(inplan_job,return_type='dict')
        print drill_info
        size = 0

        for info in drill_info:
            if (info['DRILL_LAYER_'] == "一次钻孔" or '控深盲孔' in info['DRILL_LAYER_']) and info['DRILL_TYPE_'] == "HCT coupon定位孔":
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

    def get_etch_layer(self):
        # 获取蚀刻层列表
        etch_layer = []
        for x, y in enumerate(xrange(self.layer_num), 1):
            etch_layer.append("l" + str(x))
        return etch_layer

    def get_laser_mk_layers(self):
        """
        获取盲埋孔的列表，并最小孔径信息写入dict self.allDrlInfo
        :return:
        """
        laser_layers = []
        mk_layers = []
        drill_layers = self.GEN.GET_ATTR_LAYER('drill')
        for layer in drill_layers:
            if self.laser_reg.match(layer):
                min_laser = self.get_min_hole(layer)
                if layer in self.big_laser_holes:
                    # === TODO 计算出绕烧的孔径
                    min_laser = self.get_raoshao_laser_hole(layer)
                    if not min_laser:
                        self.Message(u'检测到层别：%s,应为大孔绕烧，实际未获得绕烧孔径,跑完后请手动修改镭射孔径！' % (layer))
                        min_laser = self.get_min_hole(layer)                        

                if len(min_laser) > 0:
                    laser_layers.append(layer)
                    self.allDrlInfo[layer] = {'minDrill': min_laser}
            if self.mk_reg.match(layer):
                # min_mk = self.get_min_laser(layer)
                min_laser = self.get_min_hole(layer)
                if len(min_laser) > 0:
                    mk_layers.append(layer)
                    self.allDrlInfo[layer] = {'minDrill': min_laser}
        return laser_layers, mk_layers

    def get_min_hole(self, layer):
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
        else:
            self.oldStepExist = 'no'

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

    def addLayerDetail(self, couStep, throughmode='once', twicemode='one',big_hole=None,laser_mode=None):
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
        if laser_mode == 'oneside':
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
        # === TODO 测试用 ===
        print json.dumps(self.allDrlInfo,indent=2)
        # 判断是哪种添加模式，如果有通孔，copy通孔层，并更改大小
        if self.modeUse == 'normal' or laser_mode == 'oneside':
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
        if self.drlLay in self.allDrlInfo:
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
        currentLaserLayers = self.laser_dict[twicemode]['laser_layers']
        currentLaserThroughLayers = self.laser_dict[twicemode]['laser_through_layers']
        currentLaserEndLayers = self.laser_dict[twicemode]['laser_end_layers']
        start = int(self.laser_dict[twicemode]['top_laser_end_layer']) + 1
        # 应用于range中end 不需要 -1
        end = int(self.laser_dict[twicemode]['bot_laser_end_layer'])

        if big_hole:
            currentLaserThroughLayers = [2, self.layer_num - 1]

        if throughmode == 'twice' and twicemode == 'twice':
            currentLaserThroughLayers = [2, self.layer_num - 1]

        for lay in currentLaserLayers:
            self.GEN.COPY_LAYER(self.job_name, couStep, 'laser', lay)
            # 更改每层最小孔尺寸
            self.GEN.WORK_LAYER(lay)
            if big_hole:
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

        if throughmode == 'twice' and twicemode == 'twice':
            self.GEN.CLEAR_LAYER()
            for inum in currentLaserThroughLayers:
                self.GEN.AFFECTED_LAYER('l' + str(inum),'yes')
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_TYP('pad')
            self.GEN.FILTER_SELECT()
            if int(self.GEN.GET_SELECT_COUNT()) > 0:
                self.GEN.SEL_DELETE()
            self.GEN.CLEAR_LAYER()

        # 镭射终止层
        for inum in currentLaserEndLayers:
            self.GEN.COPY_LAYER(self.job_name, couStep, 'laserend', 'l' + str(inum))

        # 内层非镭射贯穿层

        # for inum in range(start, int(self.bot_laser_end_layer)):

        for inum in range(start, end):
            print 'x' * 40
            print inum
            self.GEN.COPY_LAYER(self.job_name, couStep, 'innerfill', 'l' + str(inum))

        print json.dumps(self.laser_dict,indent=2)

        # self.GEN.PAUSE('xxxxxxxxxxxxxxxxxxxxxx')
        # 删除模块中的辅助层别
        for lay in ('solder', 'topsignal', 'botsignal', 'laserthrough', 'laserend', 'drillthrough', 'mk', 'innerfill',
                    'laser', 'topsignalc', 'topsignals', 'botsignalc', 'botsignals'):
            self.GEN.DELETE_LAYER(lay)

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

# # # # --程序入口
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    main = MAIN()

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

2022.12.09
版本：V2.6
作者：宋超
0.部分代码重构
1.HCT需要加追溯码。追溯码面次需与板内面次一致；
2.绕烧类型的hct支持；
3.sgt类层别加npth孔开窗；
4.挡点大小变更
http://192.168.2.120:82/zentao/story-view-4272.html
"""
