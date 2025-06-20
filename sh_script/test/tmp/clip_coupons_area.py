#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2022/02/28
# @Revision     :    1.0.0
# @File         :    clip_coupons_area.py
# @Software     :    PyCharm
# @Usefor       :    切板边coupon的铜
# @from         :    sr_pitch_check.py of Michael
# @url          :    http://192.168.2.120:82/zentao/story-view-3990.html
# @Modify:2022.09.01 Song 新的hct coupon 命名为（hct）不切挡点层 周涌，钉钉反馈
# 2022.10.20 化金时，hct Coupon挡点层切铜，保证下油 http://192.168.2.120:82/zentao/story-view-4719.html
# ---------------------------------------------------------#


import sys
import os
import platform
import re
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QMessageBox
reload(sys)
sys.setdefaultencoding('utf-8')

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
PRODUCT = os.environ.get('INCAM_PRODUCT', None)
if platform.system() == "Windows":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
# --导入Package
import genCOM_26
from messageBox import msgBox


class MyApp(object):
    def __init__(self, step_name):
        self.GEN = genCOM_26.GEN_COM()
        self.job_name = os.environ.get('JOB')
        self.step_name = step_name
        self.g_steps_list = self.get_step_list(self.step_name)
        if len(self.g_steps_list) == 0:
            msg_box = msgBox()
            msg_box.warning(None, 'Step:%s内不包含拼版' % self.step_name, '程序退出！', QMessageBox.Ok)
            exit(1)
        self.fill_layer = 'sr_fill'
        self.flat_layer = 'sr_fill_flat'
        # self.close_sr = 'close_sr'
        self.md_clip = 'md_clip'
        self.md_cover = 'md_cover'
        self.wk_clip = "wk_clip"
        # === 定义全局变量，以下单位为mm
        self.check_dist = 0.500
        self.out_dist = 0.49999 * float(self.check_dist)
        self.xllc_dist = 0.4999 * float(self.check_dist + 0.25)
        self.drill_layers = self.get_end_coupon_names()
        self.inner_layers = self.get_inner_layers()

    def __del__(self):
        self.GEN.COM('disp_on')

    def run(self):
        self.GEN.COM('disp_off')
        self.GEN.OPEN_STEP(self.step_name)
        self.GEN.VOF()
        self.GEN.DELETE_LAYER(self.flat_layer)
        self.GEN.DELETE_LAYER(self.fill_layer)
        self.GEN.DELETE_LAYER(self.md_clip)
        self.GEN.DELETE_LAYER(self.md_cover)
        self.GEN.DELETE_LAYER(self.wk_clip)
        self.GEN.CREATE_LAYER(self.fill_layer)
        self.GEN.VON()
        self.fill_sr(self.step_name)
        self.flatten_layer()
        # === 以下用于外部调用 ===
        self.clip_panel_area()
        # self.check_panel_area()

        self.GEN.VOF()        
        self.GEN.DELETE_LAYER(self.md_cover)
        self.GEN.DELETE_LAYER(self.wk_clip)
        self.GEN.VON()
        msg_box = msgBox()
        msg_box.information(None, 'Step:%s板边模块切铜' % self.step_name, '已完成！', QMessageBox.Ok)

    def fill_sr(self, step_now):
        """
        填充子排版,如果子排版中还有子排版，会递归调用
        :return: None
        """
        fill_layer = self.fill_layer
        SR = self.get_step_list(step_now)
        for step in SR:
            out_dist = self.out_dist
            # 尾孔step也加入 在后面切铜过程中在排除 20230717 by lyh
            # if step in self.drill_layers:
                # === 尾孔模块不铺铜 ===
                # continue
            if re.match(r'^set\d?\d?$|^edit\d?\d?$', step):
                continue

            self.GEN.OPEN_STEP(step)
            self.GEN.CHANGE_UNITS('mm')
            self.GEN.WORK_LAYER(fill_layer)
            # 每个step在fill的时候，都附加一个.string=step的属性
            self.GEN.COM('cur_atr_reset')
            self.GEN.COM('cur_atr_set,attribute=.string,text=%s' % step)
            sr_info = self.GEN.DO_INFO('-t step -e %s/%s -m script -d SR' % (self.job_name, step))

            if step == 'xllc-coupon':
                out_dist = self.xllc_dist
            elif step == 'coupon-qp':  #切片coupon掏大一些
                out_dist = 0.5
            self.GEN.COM('sr_fill,polarity=%s,step_margin_x=%s,step_margin_y=%s,step_max_dist_x=%s,step_max_dist_y=%s,'
                         'sr_margin_x=%s,sr_margin_y=%s,sr_max_dist_x=%s,sr_max_dist_y=%s,nest_sr=no,stop_at_steps=,'
                         'consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=yes'
                         % ('positive', '-' + str(out_dist), '-' + str(out_dist), 2540, 2540, 0, 0, 0, 0))
            self.GEN.COM('cur_atr_reset')
            self.GEN.CLEAR_LAYER()
            self.GEN.CLOSE_STEP()
            if len(sr_info['gSRstep']) > 0:
                # --递归调用，子排版中存在子排版
                self.fill_sr(step)

    def get_step_list(self, cur_step='panel'):
        sr_list = []
        info = self.GEN.DO_INFO('-t step -e %s/%s -m script -d SR' % (self.job_name, cur_step))
        for step in info['gSRstep']:
            if step not in sr_list:
                sr_list.append(step)
        return sr_list

    def flatten_layer(self):
        self.GEN.OPEN_STEP(self.step_name)
        self.GEN.COM('flatten_layer,source_layer=%s,target_layer=%s' % (self.fill_layer, self.flat_layer))
        
        #将尾孔模块移出到挡点切铜层内 20230719 by lyh
        self.GEN.CLEAR_LAYER()
        self.GEN.WORK_LAYER(self.flat_layer)
        self.GEN.VOF()
        for name in self.drill_layers:
            self.GEN.FILTER_RESET()
            self.GEN.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text={0}".format(name))
            self.GEN.FILTER_SELECT()
        count = self.GEN.GET_SELECT_COUNT()
        if count > 0:
            self.GEN.SEL_MOVE(self.wk_clip)        

    def clip_panel_area(self):
        """
        切板边铜
        :return:
        """
        self.GEN.OPEN_STEP(self.step_name)
        self.GEN.CHANGE_UNITS('mm')
        self.GEN.CLEAR_LAYER()
        # === 线路层和防焊层切铜 === 2022.05.11 选化干膜层切铜，需求：3990补充
        self.GEN.COM('affected_filter,filter=(type=signal|solder_mask&context=board)')
        if self.GEN.LAYER_EXISTS('sgt-c', job=self.job_name, step=self.step_name) == 'yes':
            self.GEN.AFFECTED_LAYER('sgt-c', 'yes')
        if self.GEN.LAYER_EXISTS('sgt-s', job=self.job_name, step=self.step_name) == 'yes':
            self.GEN.AFFECTED_LAYER('sgt-s', 'yes')
        self.GEN.COM('clip_area_strt')
        self.GEN.COM('clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,'
                     'contour_cut=no,margin=0,ref_layer=%s,feat_types=surface' % self.flat_layer)
        self.GEN.CLEAR_LAYER()
        if self.GEN.LAYER_EXISTS(self.md_clip, job=self.job_name, step=self.step_name) == 'yes':
            # http://192.168.2.120:82/zentao/story-view-5815.html            
            self.GEN.COM('affected_filter,filter=(type=signal|solder_mask&context=board&side=top|bottom)')
            self.GEN.COM(
                'clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,'
                'contour_cut=no,margin=0,ref_layer=%s,feat_types=surface' % self.md_clip)
            
            # 省金 尾孔也要切外层铜 20230725 by lyh
            if self.GEN.LAYER_EXISTS(self.wk_clip, job=self.job_name, step=self.step_name) == 'yes':
                self.GEN.COM(
                    'clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,'
                    'contour_cut=no,margin=0,ref_layer=%s,feat_types=surface' % (self.wk_clip))
            
        self.GEN.CLEAR_LAYER()
        # === 挡点层要套出货单元。（厂内单元为：1.对准度 # 2.防漏接 3.钻孔测试条 4.hct-coupon 5.尾孔 6.	防爆偏 7.线路测量coupon）
        # self.get_md_clip_copper()
        # 20230719 by lyh 翟鸣通知 挡点层所有模块要全部切铜, 尾孔模块不切铜
        self.GEN.AFFECTED_LAYER('md1', 'yes')
        self.GEN.AFFECTED_LAYER('md2', 'yes')
        self.GEN.COM('clip_area_strt')
        self.GEN.COM(
            'clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,'
            'contour_cut=no,margin=0,ref_layer=%s,feat_types=surface' % self.flat_layer)
        if self.GEN.LAYER_EXISTS(self.md_clip, job=self.job_name, step=self.step_name) == 'yes':            
            self.GEN.COM(
                'clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,'
                'contour_cut=no,margin=0,ref_layer=%s,feat_types=surface' % self.md_clip)
            
        # if self.GEN.LAYER_EXISTS(self.wk_clip, job=self.job_name, step=self.step_name) == 'yes':
        #     self.GEN.COM(
        #         'clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,'
        #         'contour_cut=no,margin=0,ref_layer=%s,feat_types=surface' % (self.wk_clip))
            
        self.GEN.CLEAR_LAYER()
        
        #尾孔模块单独切铜
        if self.GEN.LAYER_EXISTS(self.wk_clip, job=self.job_name, step=self.step_name) == 'yes':
            for name in self.drill_layers:
                self.GEN.CLEAR_LAYER()
                self.GEN.AFFECTED_LAYER(self.wk_clip, 'yes')
                self.GEN.FILTER_RESET()
                self.GEN.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text={0}".format(name))
                self.GEN.FILTER_SELECT()
                count = self.GEN.GET_SELECT_COUNT()
                if count > 0:                
                    self.GEN.SEL_MOVE(name+"_clip_tmp")
                    if name == "drl":                    
                        self.GEN.CLEAR_LAYER()
                        self.GEN.COM('affected_filter,filter=(type=signal|solder_mask&context=board&side=top|bottom)')
                        self.GEN.COM(
                            'clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,'
                            'contour_cut=no,margin=0,ref_layer=%s,feat_types=surface' % (name+"_clip_tmp"))
                    else:
                        # if name.startswith("b"):
                        if re.match("^b\d+-\d+", name):                            
                            top_layer, bot_layer = name.split("-")[0].replace("b", "l"), "l{0}".format(name.split("-")[1])
                            clip = False
                            for layer in self.inner_layers:
                                if int(layer[1:]) <= int(top_layer[1:]):
                                    self.GEN.AFFECTED_LAYER(layer, 'yes')
                                    clip = True
                                if int(layer[1:]) >= int(bot_layer[1:]):
                                    self.GEN.AFFECTED_LAYER(layer, 'yes')
                                    clip = True
                            if clip:
                                self.GEN.COM(
                                    'clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,'
                                    'contour_cut=no,margin=0,ref_layer=%s,feat_types=surface' % (name+"_clip_tmp"))                                
                    
                    self.GEN.DELETE_LAYER(name+"_clip_tmp")
                    
    def get_md_clip_copper(self):

        self.GEN.CLEAR_LAYER()
        flat_layer = self.flat_layer
        # DO_INFO获取surface的index,因为可能有多块金手指对应的防焊开窗，所以要迭代处理
        info = self.GEN.INFO(
            '-t layer -e %s/%s/%s -m script -d FEATURES -o feat_index' % (self.job_name, self.step_name, flat_layer))
        # 只检测edit,set,zk等step,因为其它step经常间距不足1mm

        indexRegex = re.compile(
            r'^#\d+\s+#S P 0;.pattern_fill,.string=(dzd.*|.*floujie|drill_test_coupon|hct(-coupon)?|sm4-coupon|1-2sm4-coupon|xllc-coupon|hct.*)')
        # === 化金表面处理，第七位为g时,挡点不切铜
        if self.job_name[6] == 'g':
            indexRegex = re.compile(
                r'^#\d+\s+#S P 0;.pattern_fill,.string=(dzd.*|.*floujie|drill_test_coupon|sm4-coupon|1-2sm4-coupon|xllc-coupon)')

        indexRegex2 = re.compile(r'^#\d+\s+#S P 0;.pattern_fill,.string=')

        for line in info:
            if re.search(indexRegex2, line):
                if re.search(indexRegex, line):
                    # === 挡点覆盖层 ===
                    index = line.strip().split()[0].strip('#')
                    self.GEN.WORK_LAYER(flat_layer)
                    self.GEN.VOF()
                    self.GEN.COM('sel_layer_feat,operation=select,layer=%s,index=%s' % (flat_layer, index))
                    count = self.GEN.GET_SELECT_COUNT()
                    if count > 0:
                        self.GEN.SEL_COPY(self.md_cover)
                else:
                    index = line.strip().split()[0].strip('#')
                    self.GEN.WORK_LAYER(flat_layer)
                    self.GEN.VOF()
                    self.GEN.COM('sel_layer_feat,operation=select,layer=%s,index=%s' % (flat_layer, index))
                    count = self.GEN.GET_SELECT_COUNT()
                    if count > 0:
                        self.GEN.SEL_COPY(self.md_clip)

        self.GEN.CLEAR_LAYER()

    def check_panel_area(self):
        """
        检测是否切铜
        :return:
        """
        self.GEN.OPEN_STEP(self.step_name)
        self.GEN.CHANGE_UNITS('mm')

    def get_end_coupon_names(self):
        """
        获取料号钻孔层名列表
        :return:
        """
        drill_layers = self.GEN.GET_ATTR_LAYER('drill')
        print drill_layers
        return drill_layers
    
    def get_inner_layers(self):
        """
        获取料号内层名列表
        :return:
        """
        inner_layers = self.GEN.GET_ATTR_LAYER('inner')
        return inner_layers    


# # # # --程序入口
if __name__ == "__main__":
    appc = QtGui.QApplication(sys.argv)
    # app = MyApp('panel')
    # === 与TOPCAM结合，关联工作Step ===
    step = os.environ.get('STEP', None)
    if not step:
        exit(1)
    app = MyApp(step)
    app.run()
