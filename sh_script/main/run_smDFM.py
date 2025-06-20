#!/usr/bin/env python26
# -*- coding: utf-8 -*-
# --------------------------------------------------------- #
#                VGT SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    Chao.Song
# @Mail         :
# @Date         :    2020.01.04
# @Revision     :    1.0.0
# @File         :    run_smDFM.py
# @Software     :    PyCharm
# @Usefor       :    用于防焊优化主程序，程序与界面分离
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
'''
                   _ooOoo_
                  o8888888o
                  88" . "88
                  (| -_- |)
                  O\  =  /O
               ____/`---'\____
             .'  \\|     |//  `.
            /  \\|||  :  |||//  \
           /  _||||| -:- |||||-  \
           |   | \\\  -  /// |   |
           | \_|  ''\---/''  |   |
           \  .-\__  `-`  ___/-. /
         ___`. .'  /--.--\  `. . __
      ."" '<  `.___\_<|>_/___.'  >'"".
     | | :  `- \`.;`\ _ /`;.`/ - ` : | |
     \  \ `-.   \_ __\ /__ _/   .-` /  /
======`-.____`-.___\_____/___.-`____.-'======
                   `=---='
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           佛祖保佑       永无BUG
'''
import os
import platform
import sys
import time
import shutil
from PyQt4 import QtCore, QtGui
import random
import re

# --加载相对位置，以实现InCAM与Genesis共用
if platform.system () == "Windows":
    sys.path.append (r"Z:/incam/genesis/sys/scripts/Package")
    tmpDir = "C:/tmp"
else:
    sys.path.append (r"/incam/server/site_data/scripts/Package")
    tmpDir = "/tmp"

import genCOM_26 as genCOM

reload (sys)
sys.setdefaultencoding ("utf-8")

GEN = genCOM.GEN_COM ()
from messageBox import msgBox
_revisions = {
    'v1.0': '''
    1> Chao.Song 开发日期：2020.01.05
    2> 增加变量：min_trace_split 用于设定多大的线路做防墓碑 3 --> 2
    3> 增加变量：v_clear_coverage_comp 用于更改coverage的优先级 90 -> 100 '''
}


class DfmMain:
    """
    面向对象，创建RunDFM的class
    """

    def __init__(self, ip_val):
        self.ip_val = ip_val
        self.check_layer = '__smrchecklayer__'
        self.sm_array = GEN.GET_ATTR_LAYER('solder_mask')
        self.job_name = os.environ.get('JOB',None)
        self.step_name = os.environ.get('STEP', None)
        # 保存阻焊层和移动阻焊层的名字
        self.omve_sur_layer_dict = {}
        self.min_trace_split = 2
        self.v_clear_coverage_comp = 100
        self.drl = 'drl'

    def run_sm_opt(self):
        """
        防焊优化主程序
        :return:
        """

        # === 判断drl 及tk,ykj 如果有以tk.ykj为准 ===
        misc_layer_list = self.begin_deal_drill_layer()
        GEN.CLEAR_LAYER()
        # === 获取防焊层列表 ===
        # === 获取外层列表 ===
        outer_array = GEN.GET_ATTR_LAYER('outer')
        # ==优化前备份防焊层,move surface到另外的层别==
        for sm_layer in self.sm_array:
            GEN.CLEAR_LAYER ()
            sm_bak = sm_layer + '-bak'
            sm_cu_bak = sm_layer + '-surfaces_tmp'
            if GEN.LAYER_EXISTS(sm_bak) == 'yes':
                GEN.AFFECTED_LAYER(sm_bak, 'yes')
                GEN.SEL_DELETE()
            GEN.CLEAR_LAYER()
            if GEN.LAYER_EXISTS(sm_cu_bak) == 'yes':
                GEN.AFFECTED_LAYER(sm_cu_bak, 'yes')
                GEN.SEL_DELETE()
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER(sm_layer, 'yes')
            GEN.FILTER_RESET()
            GEN.SEL_COPY(sm_bak)
            GEN.FILTER_SET_TYP('surface')
            GEN.FILTER_SET_POL('positive')
            GEN.FILTER_SELECT()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_MOVE(sm_cu_bak)
                # 唐成 2021.01.22 将移动的铜皮层信息放入字典
                self.omve_sur_layer_dict[sm_layer] = sm_cu_bak
            GEN.CLEAR_LAYER ()

        GEN.CLEAR_LAYER()
        GEN.FILTER_RESET()
        # === 2020.06.13 Song 更改on pad 大小1mil --> 0.76mil
        # === 2020.09.16 Song 更改on pad 大小0.76mil --> 1mil
        embedded_smd = 1
        embedded_bga = 1
        partial_smd = 1
        partial_bga = 1
        small_smd = 1
        small_bga = 1
        pad_minimal_size = 0.251
        pad_open_size = float(self.ip_val['pad_open_size'])
        smd_out_addsize = self.ip_val['smd_out_addsize']
        bga_out_addsize = self.ip_val['bga_out_addsize']
        sel_tx_frm = self.ip_val['sel_tx_frm']
        pad_bridge_size = self.ip_val['pad_bridge_size']
        sel_fac_mode = self.ip_val['sel_fac_mode']

        # === 2020.07.16 ===
        # 增加变量用于管控npth参数，npth孔开窗为孔+单边5nil，由于开窗大小设置为1(1.5-->1)，则界面值更改为4mil (3.5-->4)
        # 增加部分孔开窗距铜参数 (3-->5)
        # === 2020.12.15 更改5-开窗优化值
        npth_enlarge = 5 - pad_open_size
        # === 2020.09.21 $partial_drill_clearance 5-->3mil
        partial_drill_clearance = 3
        partial_drill_percentage = 34

        gasket_smd = smd_out_addsize
        gasket_bga = ""
        if bga_out_addsize != "" :
            gasket_bga = bga_out_addsize
        else:
            gasket_bga = smd_out_addsize

        gasket_pth = 4
        gasket_via = 2
        tWorkStep = self.step_name

        # ==优化前删除已有的checklist==
        GEN.VOF()
        GEN.COM("chklist_delete,chklist=smr-scripts")
        GEN.VON()
        GEN.COM("chklist_from_lib,chklist=smr-scripts,profile=none,customer=")

        GEN.COM("top_tab,tab=Checklists")
        GEN.COM("chklist_open,chklist=smr-scripts")
        GEN.COM("chklist_show,chklist=smr-scripts,nact=1,pinned=yes,pinned_enabled=yes")
        GEN.COM("show_tab,tab=Checklists,show=yes")
        GEN.COM("top_tab,tab=Checklists")
        GEN.COM("chklist_erf,chklist=smr-scripts,nact=1,erf=normal")
        GEN.COM("units,type=inch")
        partical_config = ''
        pp_split_clr_for_pad = ''
        pp_partial_embedded_mode = ''
        """
        pp_partial_embedded_mode=Split Clearance
        """
        if sel_tx_frm == u"不做" :
            partical_config = 'pp_partial = SMD\;BGA'
            pp_split_clr_for_pad = 'pp_split_clr_for_pad='
            pp_partial_embedded_mode = 'pp_partial_embedded_mode=Partial Embedded'
            # == coverage min 2.51--> 1.51 opt 3 --> 2 2020.05.25 by song Ver:1.2 ==
            GEN.COM("chklist_cupd,chklist=smr-scripts,nact=1,params="
                    "((pp_layer=.type=signal&context=board&side=top|bottom|none&pol=positive)(pp_min_clear=%s)"
                    "(pp_opt_clear=%s)(pp_min_cover=1.51)(pp_opt_cover=2)(pp_min_bridge=%s)"
                    "(pp_opt_bridge=%s)(pp_selected=All)(pp_use_mask=Yes)(pp_use_shave=Yes)(pp_shave_cu=)"
                    "(pp_rerout_line=)(pp_min_cu_width=5)(pp_min_cu_spacing=2.5)(pp_min_pth_ar=5)(pp_min_via_ar=5)"
                    "(pp_fix_coverage=PTH\;Via\;NPTH\;SMD\;BGA)(pp_fix_bridge=PTH\;Via\;NPTH\;SMD\;BGA)"
                    "(%s)(%s)(pp_gasket_smd_as_regular=%s)"
                    "(pp_gasket_bga_as_regular=%s)(pp_gasket_pth_as_regular=%s)"
                    "(pp_gasket_via_as_regular=%s)(pp_do_small_clearances=)"
                    "(pp_handle_same_size=Same Size Clearance)(pp_handle_embedded_as_regular=)"
                    "(%s)),mode=regular" % (pad_minimal_size,pad_open_size,pad_bridge_size,pad_bridge_size,pp_split_clr_for_pad,
                                            partical_config,gasket_smd,gasket_bga,gasket_pth,gasket_via,
                                            pp_partial_embedded_mode))
        elif sel_tx_frm == u"BGA区域":
            # == coverage min 2.51--> 1.51 opt 3 --> 2 2020.05.25 by song Ver:1.2 ==
            partical_config = 'pp_partial = SMD'
            pp_split_clr_for_pad = 'pp_split_clr_for_pad='
            pp_partial_embedded_mode = 'pp_partial_embedded_mode=Partial Embedded'
            GEN.COM("chklist_cupd,chklist=smr-scripts,nact=1,params="
                    "((pp_layer=.type=signal&context=board&side=top|bottom|none&pol=positive)(pp_min_clear=%s)"
                    "(pp_opt_clear=%s)(pp_min_cover=1.51)(pp_opt_cover=2)(pp_min_bridge=%s)"
                    "(pp_opt_bridge=%s)(pp_selected=All)(pp_use_mask=Yes)(pp_use_shave=Yes)(pp_shave_cu=)"
                    "(pp_rerout_line=)(pp_min_cu_width=5)(pp_min_cu_spacing=2.5)(pp_min_pth_ar=5)(pp_min_via_ar=5)"
                    "(pp_fix_coverage=PTH\;Via\;NPTH\;SMD\;BGA)(pp_fix_bridge=PTH\;Via\;NPTH\;SMD\;BGA)"
                    "(%s)(%s)(pp_gasket_smd_as_regular=%s)"
                    "(pp_gasket_bga_as_regular=%s)(pp_gasket_pth_as_regular=%s)"
                    "(pp_gasket_via_as_regular=%s)(pp_do_small_clearances=)"
                    "(pp_handle_same_size=Same Size Clearance)(pp_handle_embedded_as_regular=)"
                    "(%s)),mode=regular" % (pad_minimal_size,pad_open_size, pad_bridge_size, pad_bridge_size, pp_split_clr_for_pad,
                                            partical_config, gasket_smd, gasket_bga,gasket_pth,gasket_via,
                                            pp_partial_embedded_mode))

        elif sel_tx_frm == u'BGA及SMD区域':
            pp_split_clr_for_pad = 'pp_split_clr_for_pad = SMD\;BGA'
            pp_partial_embedded_mode = 'pp_partial_embedded_mode=Split Clearance'
            partical_config = 'pp_partial=SMD\;BGA'
            # == coverage min 2.51--> 1.51 opt 3 --> 2 2020.05.25 by song Ver:1.2 ==
            # == spacing_split_partial_clearance_2_copper 2 --> 0.5  2020.05.25 by song Ver:1.2 ==
            GEN.COM("chklist_cupd,chklist=smr-scripts,nact=1,params="
                    "((pp_layer=.type=signal&context=board&side=top|bottom|none&pol=positive)(pp_min_clear=%s)"
                    "(pp_opt_clear=%s)(pp_min_cover=1.51)(pp_opt_cover=2)(pp_min_bridge=%s)"
                    "(pp_opt_bridge=%s)(pp_selected=All)(pp_use_mask=Yes)(pp_use_shave=Yes)(pp_shave_cu=)"
                    "(pp_rerout_line=)(pp_min_cu_width=5)(pp_min_cu_spacing=2.5)(pp_min_pth_ar=5)(pp_min_via_ar=5)"
                    "(pp_fix_coverage=PTH\;Via\;NPTH\;SMD\;BGA)(pp_fix_bridge=PTH\;Via\;NPTH\;SMD\;BGA)"
                    "(%s)(%s)(pp_gasket_smd_as_regular=%s)"
                    "(pp_gasket_bga_as_regular=%s)(pp_gasket_pth_as_regular=%s)"
                    "(pp_gasket_via_as_regular=%s)(pp_do_small_clearances=)"
                    "(pp_handle_same_size=Same Size Clearance)(pp_handle_embedded_as_regular=)"
                    "(%s)),mode=regular" %
                    (pad_minimal_size,pad_open_size, pad_bridge_size, pad_bridge_size, pp_split_clr_for_pad,
                     partical_config, gasket_smd, gasket_bga, gasket_pth, gasket_via, pp_partial_embedded_mode))
            GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=spacing_split_partial_clearance_2_copper,value=0.5,options=0")
            GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=split_partial_clearance_smooth_radius,value=1,options=0")
            GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=min_trace_to_split,value=%s,options=0" % self.min_trace_split)
            GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=rectangle_pad_max_sliver,value=0.5,options=0")
            GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=treate_via_pad_as_copper,value=1,options=1")
            GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=add_shave_for_split,value=1,options=1")
        else:
            msg_box = msgBox()
            msg_box.critical(self, '警告', '未获取作用范围：%s, 程序退出！' % sel_tx_frm, QtGui.QMessageBox.Ok)
            exit (0)
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_enlarge_npth_mode,value=Fix value,options=1")
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_enlarge_npth,value=%s,options=0" % npth_enlarge)

        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_small_drill_clearance_handle_mode,value=from drill,options=1")
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_grow_small_clearance_via,value=-1,options=0")
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_grow_small_clearance_pth,value=-1,options=0")
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_grow_small_clearance_npth,value=-1,options=0")
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_small_smd_clearance_handle_mode,value=enlarge current,options=1")
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_grow_small_clearance_smd,value=%s,options=0" % small_smd)
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_small_bga_clearance_handle_mode,value=enlarge current,options=1")
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_grow_small_clearance_bga,value=%s,options=0" % small_bga)
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=use_copper_defined_attr,value=1,options=1")

        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_clear_coverage_comp,value=%s,options=0" % self.v_clear_coverage_comp)
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_comp_clear_coverage_larger_min,value=1,options=1")
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_clear_bridge_comp,value=100,options=0")

        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_same_net_bridge_mode,value=shave clearance,options=1")
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_same_net_bridge_factor,value=1.0,options=0")
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_bridge_over_copper_factor,value=1.0,options=0")
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_shave_same_net,value=Yes,options=1")

        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=shrink_oversized_clearance,value=1,options=1")
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=shrink_clearance_keep_shape,value=1,options=1")
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_max_oversized_clearance,value=6.2,options=0")

        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_enlarge_embedded_smd,value=%s,options=0" % embedded_smd)
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_enlarge_embedded_bga,value=%s,options=0" % embedded_bga)
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_partial_embedded_smd,value=%s,options=0" % partial_smd)
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_partial_embedded_bga,value=%s,options=0" % partial_bga)
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_define_embedded_pad,value=From Attribute,options=1")
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_embedded_original_data,value=Original Signal Pad,options=1")

        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_npth_clear_always,value=1,options=1")
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_partial_drill_clearance,value=%s,options=0" % partial_drill_clearance)
        GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_partial_drill_percent,value=%s,options=0" % partial_drill_percentage)

        if sel_fac_mode == u'树脂塞孔':
            # === 树脂塞孔不处理钻孔 ===
            GEN.COM('chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_handle_partial_via,value=0,options=0')

        #优化前将阻焊铜皮移出阻焊层进行优化 唐成 2021.01.22
        for mask_name,mask_sur_name in self.omve_sur_layer_dict.items():
            if GEN.LAYER_EXISTS(mask_sur_name) == 'yes':
                GEN.CLEAR_LAYER()
                GEN.AFFECTED_LAYER(mask_sur_name, 'yes')
                GEN.SEL_COPY(mask_name, size=2);
                GEN.AFFECTED_LAYER(mask_sur_name, 'no')

        GEN.PAUSE("注意：正在整体优化，请检查防焊优化参数，点击继续。")
        # $f->COM("units,type=inch");
        # ==整体优化过程run==
        GEN.COM("chklist_run,chklist=smr-scripts,nact=1,area=global,async_run=yes")
        GEN.COM("disp_on")
        GEN.COM("origin_on")

        #将优化前完全覆盖的移动到铜皮层 唐成 2021.01.22
        for mask_name,mask_sur_name in self.omve_sur_layer_dict.items():
            if GEN.LAYER_EXISTS(mask_sur_name) == 'yes':
                GEN.CLEAR_LAYER()
                temp_mask_sur = "%s_%s" % (mask_sur_name, random.randint(111, 9999));
                GEN.AFFECTED_LAYER(mask_sur_name, 'yes')
                GEN.COM("sel_resize,size=2,corner_ctl=no")
                GEN.AFFECTED_LAYER(mask_sur_name, 'no')

                GEN.FILTER_RESET()
                GEN.FILTER_SET_TYP('surface')
                GEN.FILTER_SET_POL('positive')
                GEN.AFFECTED_LAYER(mask_name, 'yes')
                GEN.SEL_REF_FEAT(ref_lay=mask_sur_name, mode="cover")
                if(GEN.GET_SELECT_COUNT() > 0):
                    GEN.SEL_MOVE(temp_mask_sur, size=0);
                    GEN.AFFECTED_LAYER(mask_name, 'no')
                    GEN.AFFECTED_LAYER(mask_sur_name, 'yes')
                    GEN.SEL_DELETE();
                    GEN.AFFECTED_LAYER(mask_sur_name, 'no')
                    GEN.AFFECTED_LAYER(temp_mask_sur, 'yes')
                    GEN.SEL_MOVE(mask_sur_name, size=0);
                    GEN.AFFECTED_LAYER(temp_mask_sur, 'no')
                else:
                    GEN.AFFECTED_LAYER(mask_name, 'no')
                GEN.DELETE_LAYER(temp_mask_sur);
        # GEN.PAUSE("dddddddddddddddddddddddddddd");
        if sel_tx_frm == "BGA区域":
            for out_lay in outer_array:
                GEN.CLEAR_LAYER()
                GEN.AFFECTED_LAYER(out_lay, 'yes')
                GEN.FILTER_RESET()
                GEN.COM('filter_atr_reset')
                # === 选中solder_defined bga ===
                GEN.FILTER_SET_TYP('pad')
                GEN.FILTER_SET_POL('positive')
                GEN.FILTER_SET_ATR_SYMS('.bga')
                GEN.FILTER_SET_ATR_SYMS('.solder_defined')
                GEN.FILTER_SELECT()
                GEN.COM("adv_filter_reset")
                if int(GEN.GET_SELECT_COUNT()) > 0:
                    # === 2020.06.13 Song 更改on pad 大小1mil --> 0.76mil
                    embedded_smd = 0.76
                    embedded_bga = 0.76
                    partial_smd = 0.76
                    partial_bga = 0.76
                    spacing_split = 1
                    GEN.COM("top_tab,tab=Checklists")
                    GEN.COM("chklist_open,chklist=smr-scripts")
                    GEN.COM("chklist_show,chklist=smr-scripts,nact=1,pinned=yes,pinned_enabled=yes")
                    GEN.COM("show_tab,tab=Checklists,show=yes")
                    GEN.COM("top_tab,tab=Checklists")
                    GEN.COM("chklist_erf,chklist=smr-scripts,nact=1,erf=normal")
                    # == coverage min 2.51--> 1.51 opt 3 --> 2 2020.05.25 by song Ver:1.2 ==
                    # == spacing_split_partial_clearance_2_copper 2 --> 0.5  2020.05.25 by song Ver:1.2 ==
                    # === 通过选择模式进行优化 ===
                    wk_layer = out_lay
                    pp_selected = 'Selected'
                    pp_split_clr_for_pad = 'pp_split_clr_for_pad=BGA'
                    partical_config = 'pp_partial=SMD\;BGA'
                    pp_partial_embedded_mode = 'pp_partial_embedded_mode=Split Clearance'
                    GEN.COM("chklist_cupd,chklist=smr-scripts,nact=1,params="
                            "((pp_layer=%s)(pp_min_clear=%s)"
                            "(pp_opt_clear=%s)(pp_min_cover=1.51)(pp_opt_cover=2)(pp_min_bridge=%s)"
                            "(pp_opt_bridge=%s)(pp_selected=%s)(pp_use_mask=Yes)(pp_use_shave=Yes)(pp_shave_cu=)"
                            "(pp_rerout_line=)(pp_min_cu_width=5)(pp_min_cu_spacing=2.5)(pp_min_pth_ar=5)(pp_min_via_ar=5)"
                            "(pp_fix_coverage=PTH\;Via\;NPTH\;SMD\;BGA)(pp_fix_bridge=PTH\;Via\;NPTH\;SMD\;BGA)"
                            "(%s)(%s)(pp_gasket_smd_as_regular=%s)"
                            "(pp_gasket_bga_as_regular=%s)(pp_gasket_pth_as_regular=%s)"
                            "(pp_gasket_via_as_regular=%s)(pp_do_small_clearances=)"
                            "(pp_handle_same_size=Same Size Clearance)(pp_handle_embedded_as_regular=)"
                            "(%s)),mode=regular" %
                            (wk_layer, pad_minimal_size,pad_open_size, pad_bridge_size, pad_bridge_size, pp_selected, pp_split_clr_for_pad,
                             partical_config, gasket_smd, gasket_bga, gasket_pth, gasket_via,pp_partial_embedded_mode))

                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=spacing_split_partial_clearance_2_copper,value=0.5,options=0")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=split_partial_clearance_smooth_radius,value=%s,options=0" % spacing_split)
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=min_trace_to_split,value=%s,options=0" % self.min_trace_split)
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=rectangle_pad_max_sliver,value=0.5,options=0")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=treate_via_pad_as_copper,value=1,options=1")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=add_shave_for_split,value=1,options=1")

                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_enlarge_npth_mode,value=Fix value,options=1")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_enlarge_npth,value=%s,options=0" % npth_enlarge)

                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_small_drill_clearance_handle_mode,value=from drill,options=1")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_grow_small_clearance_via,value=-1,options=0")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_grow_small_clearance_pth,value=-1,options=0")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_grow_small_clearance_npth,value=-1,options=0")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_small_smd_clearance_handle_mode,value=enlarge current,options=1")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_grow_small_clearance_smd,value=%s,options=0" % small_smd)
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_small_bga_clearance_handle_mode,value=enlarge current,options=1")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_grow_small_clearance_bga,value=%s,options=0" % small_bga)
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=use_copper_defined_attr,value=1,options=1")

                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_clear_coverage_comp,value=%s,options=0" % self.v_clear_coverage_comp)
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_comp_clear_coverage_larger_min,value=1,options=1")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_clear_bridge_comp,value=100,options=0")

                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_same_net_bridge_mode,value=shave clearance,options=1")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_same_net_bridge_factor,value=1.0,options=0")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_bridge_over_copper_factor,value=1.0,options=0")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_shave_same_net,value=Yes,options=1")

                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=shrink_oversized_clearance,value=1,options=1")
                    # $f->COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=shrink_clearance_keep_shape,value=0,options=0");
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=shrink_clearance_keep_shape,value=1,options=1")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_max_oversized_clearance,value=6.2,options=0")

                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_enlarge_embedded_smd,value=%s,options=0" % embedded_smd)
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_enlarge_embedded_bga,value=%s,options=0" % embedded_bga)
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_partial_embedded_smd,value=%s,options=0" % partial_smd)
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_partial_embedded_bga,value=%s,options=0" % partial_bga)
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_define_embedded_pad,value=From Attribute,options=1")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_embedded_original_data,value=Original Signal Pad,options=1")

                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_npth_clear_always,value=1,options=1")
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_partial_drill_clearance,value=%s,options=0" % partial_drill_clearance)
                    GEN.COM("chklist_erf_variable,chklist=smr-scripts,nact=1,variable=v_partial_drill_percent,value=%s,options=0" % partial_drill_percentage)

                    GEN.PAUSE("注意：正在优化BGA区防墓碑效应，请检查防焊优化参数，点击继续。")
                    GEN.COM("units,type=inch")
                    # ==BGA优化过程run==
                    GEN.COM("chklist_run,chklist=smr-scripts,nact=1,area=global,async_run=yes")
                    GEN.COM("disp_on")
                    GEN.COM("origin_on")

                GEN.CLEAR_LAYER()
                GEN.FILTER_RESET()

        GEN.CLEAR_LAYER ()
        GEN.FILTER_RESET ()
        for sm_lay in self.sm_array:
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER(sm_lay,'yes')
            # === ? 选择线优化什么?
            GEN.COM("reset_filter_criteria,filter_name=,criteria=all")
            GEN.COM("set_filter_type,filter_name=,lines=yes,pads=no,surfaces=no,arcs=no,text=no")
            GEN.COM("set_filter_polarity,filter_name=,positive=yes,negative=no")
            GEN.COM("reset_filter_criteria,filter_name=,criteria=profile")
            GEN.COM("reset_filter_criteria,filter_name=,criteria=inc_attr")
            GEN.COM("reset_filter_criteria,filter_name=,criteria=exc_attr")
            GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=no,symbols=s9:s1000\;r9:r1000")
            GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=yes,symbols=")
            GEN.COM("reset_filter_criteria,filter_name=,criteria=text")
            GEN.COM("reset_filter_criteria,filter_name=,criteria=dcode")
            GEN.COM("reset_filter_criteria,filter_name=,criteria=net")
            GEN.COM("set_filter_length")
            GEN.COM("set_filter_angle")
            GEN.COM("adv_filter_reset")
            GEN.COM("filter_area_strt")
            GEN.COM("filter_area_end,filter_name=popup,operation=select")
            if int(GEN.COMANS) > 0:
                GEN.COM("chklist_single,show=no,action=valor_cleanup_ref_subst")
                GEN.COM("chklist_cupd,chklist=valor_cleanup_ref_subst,nact=1,params=((pp_layer=.affected)(pp_in_selected=Selected)(pp_tol=0.01)(pp_rot_mode=ALL)(pp_connected=Yes)(pp_work=Features)),mode=regular")
                GEN.COM("chklist_cnf_act,chklist=valor_cleanup_ref_subst,nact=1,cnf=no")
                GEN.COM("chklist_set_hdr,chklist=valor_cleanup_ref_subst,save_res=no,stop_on_err=no,run=activated,area=global,mask=None,mask_usage=include")
                GEN.COM("chklist_run,chklist=valor_cleanup_ref_subst,nact=1,area=global,async_run=yes")
                GEN.COM("disp_on")
                GEN.COM("origin_on")

        GEN.FILTER_RESET()
        GEN.CLEAR_LAYER()
        for sm_lay in self.sm_array:
            sm_cu_bak =  sm_lay + '-surfaces_tmp'
            sm_neg_lay = sm_lay + '-negative_tmp_layer'
            if GEN.LAYER_EXISTS(sm_neg_lay) == 'yes':
                GEN.CLEAR_LAYER()
                GEN.AFFECTED_LAYER(sm_neg_lay, 'yes')
                GEN.SEL_DELETE()
                # === surface 会加大2mil，但是不会进行优化处理 === why？

            if GEN.LAYER_EXISTS(sm_cu_bak) == 'yes':
                # 这里步骤改下,加大铜皮，将阻焊层移动到铜皮层，再将铜皮层移回阻焊层 唐成 2021.01.22
                GEN.CLEAR_LAYER()
                # GEN.AFFECTED_LAYER(sm_cu_bak, 'yes')
                # GEN.COM("sel_resize,size=2,corner_ctl=no")
                # GEN.AFFECTED_LAYER(sm_cu_bak, 'no')

                GEN.AFFECTED_LAYER(sm_lay, 'yes');
                GEN.SEL_MOVE(sm_cu_bak, size=0)
                GEN.AFFECTED_LAYER(sm_lay, 'no');
                # === TODO 注意单位是否为mil
                GEN.AFFECTED_LAYER(sm_cu_bak, 'yes')
                GEN.SEL_MOVE(sm_lay, size=0)
                GEN.AFFECTED_LAYER(sm_cu_bak, 'no')
                GEN.DELETE_LAYER(sm_cu_bak)
            # === TODO 翻线上来？
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER(sm_lay, 'yes')
            GEN.COM("reset_filter_criteria,filter_name=,criteria=all")
            GEN.COM("set_filter_type,filter_name=,lines=yes,pads=no,surfaces=no,arcs=no,text=no")
            GEN.COM("set_filter_polarity,filter_name=,positive=no,negative=yes")
            GEN.COM("reset_filter_criteria,filter_name=,criteria=profile")
            GEN.COM("reset_filter_criteria,filter_name=,criteria=inc_attr")
            GEN.COM("reset_filter_criteria,filter_name=,criteria=exc_attr")
            GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=no,symbols=")
            GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=yes,symbols=")
            GEN.COM("reset_filter_criteria,filter_name=,criteria=text")
            GEN.COM("reset_filter_criteria,filter_name=,criteria=dcode")
            GEN.COM("reset_filter_criteria,filter_name=,criteria=net")
            GEN.COM("set_filter_length")
            GEN.COM("set_filter_angle")
            GEN.COM("adv_filter_reset")
            GEN.COM("filter_area_strt")
            GEN.COM("filter_area_end,filter_name=popup,operation=select")
            if int(GEN.COMANS) > 0:
                GEN.SEL_MOVE(sm_neg_lay)
                GEN.CLEAR_LAYER()
                GEN.AFFECTED_LAYER(sm_neg_lay, 'yes')
                GEN.SEL_MOVE(sm_lay)
                GEN.DELETE_LAYER(sm_neg_lay)

        GEN.FILTER_RESET()
        GEN.CLEAR_LAYER()

        text = '程序运行完成'
        if sel_fac_mode != u'树脂塞孔':
            # get_result = self.redeal_via_clearance()
            get_result = self.deal_via2sm()
            if get_result == 'yes':
                text += "有via孔套开窗情形，请检查盖油是否超过SMD 1/4"
            if GEN.LAYER_EXISTS(self.check_layer) == 'yes':
                text += "\n防焊层有正负片叠加情形，请检查check_layer"

        if len(misc_layer_list) > 0:
            self.end_deal_drill_layer(misc_layer_list)

        result_layers = self.check_pos_neg_stackup()
        if len(result_layers) != 0:
            text += '层别：%s存在正负片叠加的情形，请检查！' % ','.join(result_layers)
        msg_box = msgBox()
        msg_box.information(self, '提示', '%s' % text, QtGui.QMessageBox.Ok)
        # === 提示程序运行完成 ===

    def begin_deal_drill_layer(self):
        """
        在防焊优化前处理钻孔层，当drl与tk.ykj同时存在时，misc掉drl层，以tk.ykj为准，优化完成后，再归类回来
        :return:
        """
        drl_exist = GEN.LAYER_EXISTS ('drl', job=self.job_name, step=self.step_name)
        if drl_exist == 'no':
            self.drl = ''
            return []
        ykj_exist = GEN.LAYER_EXISTS('tk.ykj', job=self.job_name, step=self.step_name)
        if ykj_exist == 'yes':
            self.drl = 'tk.ykj'

            # === TODO 增加判断，drl 中的symbol数量与tk.ykj相同 且不为0
            # 获取当前工作层的symbol数量
            getyk = GEN.DO_INFO("-t layer -e %s/%s/%s -d SYMS_HIST" % (self.job_name,self.step_name,self.drl))
            getdrl = GEN.DO_INFO("-t layer -e %s/%s/%s -d SYMS_HIST" % (self.job_name,self.step_name,'drl'))
            if getyk != getdrl:
                text = "验孔层tk.ykj与钻孔层drl设计不一致，请检查，程序misc掉tk.ykj层，请手动恢复！"
                msg_box = msgBox ()
                msg_box.information (self, '提示', '%s' % text, QtGui.QMessageBox.Ok)
                GEN.COM('matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=misc' % (self.job_name, 'tk.ykj'))
                self.drl = 'drl'
                return ['tk.ykj']

            if len(getyk['gSYMS_HISTsymbol']) != 0:
                GEN.COM('matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=misc' % (self.job_name, 'drl'))
        return ['drl']

    def end_deal_drill_layer(self,drill_list,do_context = 'board'):
        """
        在防焊优化前处理钻孔层，当drl与tk.ykj同时存在时，misc掉drl层，以tk.ykj为准，优化完成后，再归类回来
        增加do_context 用于批量board 或者批量misc
        :return:
        """

        for drill_layer in drill_list:
            GEN.COM('matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=%s' % (self.job_name, drill_layer,do_context))

    def redeal_via_clearance(self):
        # === http://192.168.2.120:82/zentao/story-view-2034.html
        # === 处理部分开窗的via钻孔，当部分开窗via做盖油设计时，区分样品做3.5，量产做4mil ===
        sel_fac_mode = self.ip_val['sel_fac_mode']
        add_shave = 'no'
        GEN.CLEAR_LAYER()
        # === 获取防焊层数量，为循环做准备===
        add_value = ''
        if sel_fac_mode == u"样品":
            add_value = 1
        elif sel_fac_mode == u"量产":
            add_value = 2
        else:
            msg_box = msgBox ()
            msg_box.warning (self, '提示', '无法获取量产还是样品信息：%s' % sel_fac_mode, QtGui.QMessageBox.Ok)
        GEN.DELETE_LAYER(self.check_layer)
        for sm_layer in self.sm_array:
            tmp_layer = '___' + sm_layer +'tmp++__'
            GEN.DELETE_LAYER(tmp_layer)
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER(sm_layer,'yes')
            # === 选取防焊层的负片，copy到辅助层，转正极性，和drl层做判断，如果是include孔的，则更改此类为via孔加3.5或4mil
            GEN.FILTER_RESET()
            GEN.COM("filter_atr_reset")
            GEN.FILTER_SET_FEAT_TYPES('pad','no')
            GEN.FILTER_SET_POL('negative','no')
            GEN.FILTER_SELECT()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_COPY(tmp_layer,invert='yes')
                GEN.CLEAR_LAYER()
                GEN.WORK_LAYER(tmp_layer)
                # === 删除已带属性的负片pad，避免重复运行重复添加 ===
                GEN.FILTER_RESET()
                GEN.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=via_cover")
                GEN.FILTER_SELECT()
                if int(GEN.GET_SELECT_COUNT()) > 0:
                    GEN.SEL_DELETE()
                GEN.FILTER_RESET()
                GEN.COM("filter_atr_reset")
                GEN.SEL_REF_FEAT('drl','include')
                if int(GEN.GET_SELECT_COUNT()) > 0:
                    GEN.SEL_REVERSE()
                    if int (GEN.GET_SELECT_COUNT ()) > 0:
                        GEN.SEL_DELETE()
                    # === 防焊层被当前层cover的负片pad，进行加大处理
                    GEN.CLEAR_LAYER()
                    GEN.WORK_LAYER(sm_layer)
                    GEN.FILTER_RESET()
                    GEN.COM("filter_atr_reset")
                    GEN.FILTER_SET_FEAT_TYPES('pad')
                    GEN.FILTER_SET_POL('negative')
                    GEN.SEL_REF_FEAT(tmp_layer,'cover')
                    if int (GEN.GET_SELECT_COUNT ()) > 0:
                        # 满足条件的两步动作，一步加属性，一步加大
                        # 不关闭select的物件,clear_mode=clear_none
                        GEN.COM('sel_options,clear_mode=clear_none,display_mode=all_layers,area_inout=inside,area_select=select,select_mode=standard,area_touching_mode=exclude')
                        GEN.COM('cur_atr_reset')
                        GEN.COM('cur_atr_set,attribute=.string,text=via_cover')
                        GEN.COM('sel_change_atr,mode=add')
                        # 还原select的物件clear_mode=clear_after
                        GEN.COM('sel_options,clear_mode=clear_after,display_mode=all_layers,area_inout=inside,area_select=select,select_mode=standard,area_touching_mode=exclude')
                        GEN.SEL_RESIZE(add_value)
                        add_shave = 'yes'

                    # 增加是否有正片pad被负片padcover的检测，避免测试过程中防焊字位置既加正片又加负片的情形
                    GEN.FILTER_RESET()
                    GEN.COM("filter_atr_reset")
                    GEN.FILTER_SET_FEAT_TYPES('pad','no')
                    GEN.FILTER_SET_POL('positive','no')
                    GEN.SEL_REF_FEAT(tmp_layer,'cover')
                    if int (GEN.GET_SELECT_COUNT ()) > 0:
                        GEN.SEL_COPY(self.check_layer)
                else:
                    GEN.SEL_DELETE()
                GEN.DELETE_LAYER(tmp_layer)
        GEN.CLEAR_LAYER()
        GEN.FILTER_RESET()
        return add_shave

    def get_laser_layers(self):
        """
        获取料号中的镭射层列表
        :return:
        """
        Blind_Reg = re.compile (r'^[s][0-9][0-9]?-?[0-9][0-9]?$')
        blind_list = []
        # --从料号info中获取层别及信息
        info = GEN.DO_INFO ('-t matrix -e %s/matrix -m script -d ROW' % self.job_name)
        for i, name in enumerate (info['gROWname']):
            context = info['gROWcontext'][i]
            layer_type = info['gROWlayer_type'][i]

            # --获取钻孔层
            if context == 'board' and layer_type == 'drill':
                # --匹配镭射钻孔层
                if Blind_Reg.match (name):
                    blind_list.append (name)
        return blind_list

    def deal_via2sm(self):
        """
        由于处理防焊防垂流via到防焊开窗3-3.5（样品） 3-4（量产）无处理方式，此程序用于将此区间的钻孔加盖油距离加至防焊层
        :return:
        """
        chklist_name = 'sm_tmp'
        tail_suffix = '_via2sm'

        sel_fac_mode = self.ip_val['sel_fac_mode']
        add_shave = 'no'
        GEN.CLEAR_LAYER()
        # === 获取防焊层数量，为循环做准备===
        add_value = ''
        if sel_fac_mode == u"样品":
            add_value = 7.04
            range_upper = 0.0035
        elif sel_fac_mode == u"量产":
            add_value = 8.04
            range_upper = 0.004
        else:
            msg_box = msgBox ()
            msg_box.warning (self, '提示', '无法获取量产还是样品信息：%s,不进行盖油孔的后处理'
                             % sel_fac_mode, QtGui.QMessageBox.Ok)
            return None
        # === 分析前misc掉镭射层，后再还原 ===
        blind_list = self.get_laser_layers()

        self.end_deal_drill_layer(blind_list,do_context='misc')

        GEN.DELETE_LAYER(self.check_layer)
        GEN.VOF()
        GEN.COM('chklist_delete,chklist=%s' % chklist_name)
        GEN.VON()
        GEN.COM('chklist_create,chklist=%s,allow_save=yes' % chklist_name)
        GEN.COM('chklist_cadd,chklist=sm_tmp,action=valor_analysis_sm,erf=,params=,row=0')
        pp_sm_layers = '\;' . join(self.sm_array)
        GEN.COM('chklist_cupd,chklist=sm_tmp,nact=1,params=((pp_layers=%s)(pp_ar=10)(pp_coverage=10)'
                '(pp_sm2r=10)(pp_sliver=8)(pp_spacing=6)(pp_bridge=6)(pp_min_clear_overlap=5)(pp_sm2dam=0)'
                '(pp_tests=Drill)(pp_selected=All)(pp_use_compensated_rout=No)),mode=regular' % pp_sm_layers)
        GEN.COM('chklist_run,chklist=sm_tmp,nact=1,area=global,async_run=no')
        GEN.COM('chklist_create_lyrs,chklist=sm_tmp,severity=3,suffix=%s' % tail_suffix)
        self.end_deal_drill_layer(blind_list,do_context='board')

        # === 取出checklist中分析的层别,删除非防焊的其他层别 ===

        get_info = GEN.INFO("-t check -e %s/%s/%s -d MEAS_DISP_ID -o action=1, angle_direction=ccw" %
                            (self.job_name, self.step_name,chklist_name))
        layer_list = [i.split(' ')[0] for i in get_info if i.split(" ")[0] not in self.sm_array]
        layer_list = list(set(layer_list))
        for layer in layer_list:
            GEN.DELETE_LAYER('ms_1_%s_%s' % (layer, tail_suffix))
            GEN.DELETE_LAYER('mk_1_%s_%s' % (layer, tail_suffix))
        GEN.CLEAR_LAYER()
        for sm_chk_layer in self.sm_array:
            GEN.DELETE_LAYER('mk_1_%s_%s' % (sm_chk_layer, tail_suffix))
            GEN.AFFECTED_LAYER('ms_1_%s_%s' % (sm_chk_layer, tail_suffix), 'yes')
        GEN.FILTER_RESET()
        GEN.FILTER_TEXT_ATTR('.string', 'via_2_sm')
        # === 选择线长区间2.9mil 到 4mil
        GEN.COM('filter_set,filter_name=popup,update_popup=yes,slot=line,slot_by=length,min_len=0.0029, max_len=%s'
                % range_upper)
        GEN.FILTER_SELECT()

        if int(GEN.GET_SELECT_COUNT()) == 0:
            # === 无需操作
            GEN.COM('chklist_delete,chklist=%s' % chklist_name)
            GEN.CLEAR_LAYER()
            GEN.FILTER_RESET ()
            for sm_chk_layer in self.sm_array:
                GEN.DELETE_LAYER('ms_1_%s_%s' % (sm_chk_layer, tail_suffix))
            return None
        else:
            GEN.SEL_REVERSE()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_DELETE()
        GEN.CLEAR_LAYER()
        for sm_chk_layer in self.sm_array:
            chk_result_layer = 'ms_1_%s_%s' % (sm_chk_layer, tail_suffix)
            GEN.AFFECTED_LAYER(chk_result_layer, 'yes')
            GEN.SEL_REVERSE()
            count = int(GEN.GET_SELECT_COUNT())
            if count == 0:
                GEN.DELETE_LAYER(chk_result_layer)
                GEN.CLEAR_LAYER()
                continue
            GEN.CLEAR_LAYER ()
            GEN.AFFECTED_LAYER(self.drl,'yes')
            GEN.FILTER_RESET()
            GEN.SEL_REF_FEAT(chk_result_layer,'touch')
            drl_count = int(GEN.GET_SELECT_COUNT())
            if drl_count == 0:
                msg_box = msgBox ()
                msg_box.warning (self, '提示', 'drl层未选择到防焊：%s需做盖油的钻孔' % chk_result_layer, QtGui.QMessageBox.Ok)
                continue
            if drl_count != count:
                msg_box = msgBox ()
                msg_box.warning (self, '提示', '检查结果数量：%s与drl层钻孔数量:%s不符!' % (count,drl_count), QtGui.QMessageBox.Ok)
                GEN.CLEAR_LAYER()
                continue

            tmp_layer = '__tmpdrlvia2sm__'
            GEN.DELETE_LAYER(tmp_layer)
            GEN.SEL_COPY(tmp_layer)
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER(tmp_layer,'yes')
            GEN.COM ('cur_atr_reset')
            GEN.COM ('cur_atr_set,attribute=.string,text=via_2_sm')
            GEN.COM ('sel_change_atr,mode=add')
            GEN.SEL_RESIZE(add_value)
            GEN.SEL_COPY(sm_chk_layer,invert='yes')
            add_shave = 'yes'
            GEN.CLEAR_LAYER()

            # 增加是否有正片pad被负片padcover的检测，避免测试过程中防焊字位置既加正片又加负片的情形
            GEN.AFFECTED_LAYER(sm_chk_layer,'yes')
            GEN.FILTER_RESET ()
            GEN.COM ("filter_atr_reset")
            GEN.FILTER_SET_FEAT_TYPES ('pad')
            GEN.FILTER_SET_POL ('positive')
            GEN.SEL_REF_FEAT (tmp_layer, 'cover')
            if int (GEN.GET_SELECT_COUNT ()) > 0:
                GEN.SEL_COPY (self.check_layer)
            GEN.CLEAR_FEAT()

            GEN.CLEAR_LAYER()
            GEN.DELETE_LAYER(chk_result_layer)
            GEN.DELETE_LAYER(tmp_layer)
        return add_shave

    def check_pos_neg_stackup(self):
        """
        检查是否有正负片叠加添加的情形
        :return:
        """
        result_layers = []
        GEN.CLEAR_LAYER()
        for sm_chk_layer in self.sm_array:
            print sm_chk_layer
            cur_neg_layer = '%s_neg_pad' % sm_chk_layer
            cur_pos_layer = '%s_pos_pad' % sm_chk_layer
            GEN.DELETE_LAYER(cur_neg_layer)
            GEN.DELETE_LAYER(cur_pos_layer)
            GEN.AFFECTED_LAYER(sm_chk_layer,'yes')
            GEN.FILTER_RESET()
            GEN.FILTER_SET_TYP('pad')
            GEN.FILTER_SET_POL('negative')
            GEN.FILTER_SELECT()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_COPY(cur_neg_layer,invert='yes')
                GEN.CLEAR_FEAT()
                GEN.FILTER_SET_POL('positive')
                GEN.SEL_REF_FEAT(cur_neg_layer, 'cover')
                if int(GEN.GET_SELECT_COUNT()) > 0:
                    GEN.SEL_COPY(cur_pos_layer)
                    result_layers.append(cur_pos_layer)
                GEN.DELETE_LAYER(cur_neg_layer)
            GEN.CLEAR_LAYER ()
            GEN.FILTER_RESET()

        return result_layers


# --测试调用入口
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    op_val = dict (pad_open_size=0.8,
                    smd_out_addsize=1.15,
                    bga_out_addsize=1.14,
                    sel_tx_frm=u'BGA及SMD区域',
                    pad_bridge_size=3,
                   sel_fac_mode='样品'
                   )

    M = DfmMain (op_val)
    M.run_sm_opt ()
    # app.exec_()
    sys.exit(0)



"""
1:2021.01.22 唐成按2555 需求将将铜皮移动步骤改了下，在优化前将铜皮移回了阻焊层，优化完后将铜皮层加大覆盖的铜皮又移回了铜皮层 
http://192.168.2.120:82/zentao/story-view-2555.html

2021.11.12
宋超
http://192.168.2.120:82/zentao/story-view-3519.html
1.复了防垂流漏套3.5及4mil的负PAD。（区分样品量产）
2.当tk.ykj与drl同时存在，优化前自动misc掉drl层，使用tk.ykj防焊优化，有旋转的npth槽不需要手动修改开窗大小。
3.优化完成自动将drl还原board。
4.增加正负片pad叠加检测，提醒用户处理。
"""