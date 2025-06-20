#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --加载相对位置，以实现InCAM与Genesis共用

import os
import platform
import sys
import shutil
import re

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genCOM_26 as genCOM
from Gateway import Gateway
from PyQt4 import QtCore, QtGui
import output_avi_tgz_pre
from mwClass_V2 import *
import time
import gClasses
from genesisPackages import get_panelset_sr_step, \
     lay_num, get_sr_area_flatten, get_panel_features_in_set_position
from get_erp_job_info import get_inplan_all_flow

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


class Main:
    def __init__(self, debug=False):
        self.app_Version = 'V1.3'

        self.job_name = os.environ.get('JOB', None)
        self.debug = debug
        # 接口定义
        if debug:
            # 通过genesis gateway命令连结pid进行会话
            self.GEN = Gateway()
            self.GEN.genesis_connect()
            # 方法genesis_connect通过查询log-genesis文件获取的料号名
            self.job_name = self.GEN.job_name
            self.pid = self.GEN.pid
        else:
            self.GEN = genCOM.GEN_COM()
            self.pid = os.getpid()

        # --yk层没有将禁止输出 AresHe 2022.1.13
        if self.GEN.LAYER_EXISTS('yk',step='panel') == 'no':
            okMsg = u"yk层不存在,禁止输出!!!"
            self.Message('%s' % okMsg)
            sys.exit(0)

        self.GEN.COM('get_user_name')
        self.cam_user = self.GEN.COMANS
        app = output_avi_tgz_pre.MyApp()
        check_run_result = app.get_result()
        if not check_run_result:
            # errorMsg = u'程序退出!' % (self.job_name)
            # self.Message('%s' % errorMsg)
            # sys.exit()
            time_key = int(time.time())
            time_form = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_key))
            jstr1 = '<span>AVI输出放行.时间:%s,CAM用户:%s.料号%s.有激光打码流程，但未运行激光打码输出,请放行</span>' % (time_form, self.cam_user,self.job_name)
            # print jstr1
            # === 发送评审请求 ===
            submitData = {
                'site': u'HDI板事业部',
                'job_name': self.job_name,
                'pass_tpye': 'CAM',
                'pass_level': 8,
                'assign_approve': '44813|44566|44926|44024|68027|65389',
                'pass_title': u"%s" % jstr1,
            }
            Dialog = AboutDialog(submitData['pass_title'], cancel=True, appCheck=True, appData=submitData,
                                 style='other')
            Dialog.exec_()
            # endregion
            print Dialog.selBut
            # --根据审批的结果返回值
            if Dialog.selBut == 'cancel':
                sys.exit()
            if Dialog.selBut == 'x':
                sys.exit()

        self.SR_INFO = self.GEN.getSrMinMax(self.job_name, 'panel')
        self.tgz_layers = []
        self.silk_layers = []
        self.check_sgt_layers = ['sgt-c', 'sgt-s']
        self.outline = ['ww', 'out']
        self.drl = ['drl']
        self.check_side = ['top', 'bottom']
        self.sgt_layers = []
        self.get_layers()
        # if len(self.silk_layers) == 0:
        #     errorMsg = u'没有文字层!'
        #     self.Message('%s' % errorMsg)
        #     sys.exit()
        self.check_profile()
        self.export_tgz()

    def __del__(self):
        if self.debug:
            self.GEN.disconnect()

    def get_layers(self):
        # 通过DO_INFO从matrix中获取成型层别
        self.tgz_layers = []
        self.silk_layers = []
        matrix_info = self.GEN.DO_INFO('-t matrix -e %s/matrix' % self.job_name)
        for i, name in enumerate(matrix_info['gROWname']):
            type = matrix_info['gROWlayer_type'][i]
            side = matrix_info['gROWside'][i]
            context = matrix_info['gROWcontext'][i]
            if name in self.check_sgt_layers:
                self.sgt_layers.append(name)
                if self.check_side[self.check_sgt_layers.index(name)] != side:
                    errorMsg = u'%s 层别排列不正确应为%s，程序退出!' % (name,self.check_side[self.check_sgt_layers.index(name)])
                    self.Message ('%s' % errorMsg)
                    sys.exit ()
                self.tgz_layers.append(name)
            if name in self.outline:
                self.tgz_layers.append(name)

            if name in self.drl:
                self.tgz_layers.append(name)

            if type == 'silk_screen' and context == 'board':
                self.tgz_layers.append(name)
                self.silk_layers.append(name)
            if type == 'solder_mask' and context == 'board':
                self.tgz_layers.append(name)
            if type == 'signal' and context == 'board' and side in ['top', 'bottom']:
                self.tgz_layers.append(name)
                # === Song 2020.7.13 增加检测，外层命名是否标准
                if re.match('^l[0-9][0-9]?$',name):
                    pass
                else:
                    errorMsg = u'%s 非正常外层层别命名，程序退出!' % name
                    self.Message ('%s' % errorMsg)
                    sys.exit ()

    def check_profile(self):
        """
        当panel中有个别模块未建profile输出时，产线喷墨程式不识别，现输出时检测panel中是否有漏profile的情况出现
        :return:
        """
        panel_srs = []
        info = self.GEN.DO_INFO('-t step -e %s/panel -m script -d SR' % self.job_name)
        for step in info['gSRstep']:
            if step not in panel_srs:
                panel_srs.append(step)
        for step in panel_srs:
            info = self.GEN.DO_INFO('-t step -e %s/%s -m script -d PROF_LIMITS' % (self.job_name,step))
            if info['gPROF_LIMITSxmin'] == '0' and info['gPROF_LIMITSymin'] == '0' and info['gPROF_LIMITSxmax'] == '0' and info['gPROF_LIMITSymax'] == '0':
                errorMsg = u'panel中的%s没有定义profile!\n\n产线喷墨程式不识别!\n\n请定义好profile并保存后再执行脚本!' % step
                self.Message('%s' % errorMsg)
                sys.exit(0)

    def check_id_101(self):
        """
        检查id=101是否存在
        :return: None
        """
        # 获取成型层对应的step,如果panel中有内容物，以panel以准，否则以所在step为准
        info = self.GEN.DO_INFO('-t step -e %s/panel -d EXISTS' % self.job_name)
        if info['gEXISTS'] == 'no':
            errorMsg = u'step panel 不存在!'
            self.Message('%s' % errorMsg)
            sys.exit()
        # 打开panel，并切换单位为mm
        self.GEN.OPEN_STEP('panel')
        self.GEN.CHANGE_UNITS('mm')
        self.GEN.CLEAR_LAYER()
        for layer in self.silk_layers:
            # 过滤器选择属性
            self.GEN.AFFECTED_LAYER(layer, 'yes')
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_ATR_SYMS('id,min_int_val=101,max_int_val=101')
            self.GEN.FILTER_SELECT()
            self.GEN.FILTER_RESET()
            count = self.GEN.GET_SELECT_COUNT()
            if count != 0:
                # 依据story-view-809要求，所有0.1mm的点，先删除，再重新添加
                self.GEN.SEL_DELETE()
                # 重新添加
                self.add_101_attr(layer)
            else:
                # 没有r0.1mm的情况下，全新添加
                self.add_101_attr(layer)
            self.GEN.CUR_ART_RESET()
            self.GEN.AFFECTED_LAYER(layer, 'no')

    def export_tgz(self):
        # 用partical模式输出tgz
        if platform.system() == "Windows":
            tmp_path = 'C:/tmp'
            tgz_path = os.path.join(r'D:\disk\film', self.job_name)
        else:
            # 由于incampro的tmp目录不允许输出tgz，所以新建一级文件夹
            tmp_path = '/tmp/tmp'
            tgz_path = os.path.join(r'/id/workfile/film', self.job_name)

        #
        # --递归判断目录级是否存在，不存在一级一级向下创建
        if not os.path.exists(tgz_path):
            self.mkdir(tgz_path)

        if not os.path.exists(tmp_path):
            self.mkdir(tmp_path)
        #  此处直接备份外层线路和阻焊层
        ks_bk_layers = self.GEN.GET_ATTR_LAYER('solder_mask') + self.GEN.GET_ATTR_LAYER('outer')
        for lay in ks_bk_layers:
            if 'edit' in self.GEN.GET_STEP_LIST():
                self.GEN.OPEN_STEP('edit')
                self.GEN.COPY_LAYER(self.job_name,'edit', lay, lay + 'compbk')
            if 'set' in self.GEN.GET_STEP_LIST():
                self.GEN.OPEN_STEP('set')
                self.GEN.COPY_LAYER(self.job_name,'set', lay, lay + 'compbk')

        #检查控深钻外层是否有加比孔小0.2mm的pad 20230104 by lyh
        check_result = self.check_and_reback_layer("delete")
        # --2023-10-24输入AVI资料删除线路和阻焊层'kscnc-out、kscnc-sm'两个symbol  -- ynh
        self.del_kscnc_symbols()
        # --执行tgz导出
        include_lyrs = '\;'.join(self.tgz_layers)
        self.GEN.VOF()
        self.GEN.COM('check_inout,mode=out,type=job,job=%s' % self.job_name)
        self.GEN.COM('save_job,job=%s,override=no' % self.job_name)
        self.GEN.COM('check_inout,mode=in,type=job,job=%s' % self.job_name)
        reVal = self.GEN.COM('export_job,job=%s,path=%s,mode=tar_gzip,submode=partial,'
                             'lyrs_mode=include,lyrs=%s,overwrite=yes' % (self.job_name, tmp_path, include_lyrs))
        self.GEN.VON()

        if check_result:
            self.check_and_reback_layer("reback")

        # 还原之前修改的层
        for lay in ks_bk_layers:
            if 'edit' in self.GEN.GET_STEP_LIST():
                self.GEN.OPEN_STEP('edit')
                self.GEN.COPY_LAYER(self.job_name, 'edit', lay + 'compbk', lay)
            if 'set' in self.GEN.GET_STEP_LIST():
                self.GEN.OPEN_STEP('set')
                self.GEN.COPY_LAYER(self.job_name, 'set', lay + 'compbk', lay)

        self.GEN.VOF()
        self.GEN.COM('check_inout,mode=out,type=job,job=%s' % self.job_name)
        self.GEN.COM('save_job,job=%s,override=no' % self.job_name)
        self.GEN.COM('check_inout,mode=in,type=job,job=%s' % self.job_name)
        self.GEN.VON()

        # --export异常，用于后续自动输出异常抛出纪录
        if reVal != 0:
            errorMsg = u"tgz导出失败！\n\n程序即将退出，请联系管理员!"
            self.Message('%s' % errorMsg)
        else:
            # --删除目标地址下的资料
            if os.path.exists(os.path.join(tgz_path, self.job_name + str('_outavi.tgz'))):
                os.remove(os.path.join(tgz_path, self.job_name + str('_outavi.tgz')))
            # --重命名临时目录下的tgz,并Move至对应地址
            shutil.move(os.path.join(tmp_path, self.job_name + str('.tgz')),
                      os.path.join(tgz_path, self.job_name + str('_outavi.tgz')))

            okMsg = u"tgz导出成功，程序版本：%s！！！" % self.app_Version
            self.Message('%s' % okMsg)

    def del_kscnc_symbols(self):
        del_res = {'res':False, 'layers':{'edit':[], 'set':[]},'delkspad':False}
        job_name = os.environ.get('JOB')
        del_ks_symbol_layers = self.GEN.GET_ATTR_LAYER('solder_mask') + self.GEN.GET_ATTR_LAYER('outer')
        for layer in del_ks_symbol_layers:
            steps = []
            if 'edit' in self.GEN.GET_STEP_LIST():
                steps.append('edit')
            if 'set' in self.GEN.GET_STEP_LIST():
                steps.append('set')
            for s in steps:
                info = self.GEN.DO_INFO("-t layer -e %s/%s/%s -m script -d SYMS_HIST -p symbol" % (job_name, s , layer))
                print info['gSYMS_HISTsymbol']
                if 'kscnc-sm' in info['gSYMS_HISTsymbol'] or 'kscnc-out' in info['gSYMS_HISTsymbol']:
                    del_res['res'] = True
                    del_res['layers'][s].append(layer)

        if del_res['res']:
            self.GEN.VOF()
            for layer in del_ks_symbol_layers:
                tmp_layer = layer + '_kscnc_tmp'
                self.GEN.DELETE_LAYER(tmp_layer)
                self.GEN.CREATE_LAYER(tmp_layer)
            self.GEN.VON()
            for s in del_res['layers'].keys():
                if del_res['layers'][s]:
                    self.GEN.OPEN_STEP(s)
                    for lay in del_res['layers'][s]:
                        self.GEN.CLEAR_LAYER()
                        self.GEN.COPY_LAYER(job_name, s, lay, lay + '_kscnc_tmp')
                        self.GEN.FILTER_RESET()
                        self.GEN.FILTER_SET_INCLUDE_SYMS('kscnc-sm\;kscnc-out')
                        self.GEN.AFFECTED_LAYER(lay, affected='yes')
                        self.GEN.FILTER_SELECT()
                        if self.GEN.GET_SELECT_COUNT():
                            self.GEN.SEL_DELETE()
                        self.GEN.FILTER_RESET()
                        self.GEN.CLEAR_LAYER()

        self.GEN.VOF()
        for layer in self.GEN.GET_ATTR_LAYER('solder_mask') + self.GEN.GET_ATTR_LAYER('outer'):
            self.GEN.DELETE_LAYER(layer + '_kscnc_tmp')
        self.GEN.COM('check_inout,mode=out,type=job,job=%s' % self.job_name)
        self.GEN.COM('save_job,job=%s,override=no' % self.job_name)
        self.GEN.COM('check_inout,mode=in,type=job,job=%s' % self.job_name)
        self.GEN.VON()
            
    def check_and_reback_layer(self, modify_type):
        """http://192.168.2.120:82/zentao/story-view-5022.html
        4.LED板有控深钻料号输出AVI资料时自动删除铜Pad
        增加 http://192.168.2.120:82/zentao/story-view-5153.html
        输出AVI时检测是否镀金板，是镀金板自动按属性删除引线，停顿提示人工确认是否删除干净"""
        job = gClasses.Job(self.job_name)
        matrixinfo = job.matrix.getInfo()
        kz_drills = []
        for i, name in enumerate(matrixinfo["gROWname"]):
            if matrixinfo["gROWlayer_type"][i] == "drill" and \
               matrixinfo["gROWcontext"][i] == "board":
                if name in ["cdc", "cds"] or \
                   re.match("^cd[0-9]{1,2}-[0-9]{1,2}[cs]$", name):
                    kz_drills.append(name)
        
        data_info = get_inplan_all_flow(self.job_name.upper(), True)
        jsz_process = False
        jsz_xiebian = False
        for dic_info in data_info:
            if dic_info["OPERATION_CODE"][:6] in ["HDI120", "HDI222", "HDI223"]:
                jsz_process = True
            if dic_info["OPERATION_CODE"][:6] in ["HDI216"]:
                jsz_xiebian = True

        
        
        modify_layer = False
        jsz_finger_layers = []
        if self.job_name[6:8] in ['ph', 'gh', 'gy'] or jsz_process or re.search('gd1012eht02', self.job_name):
            jsz_finger_layers = ["l1", "l{0}".format(int(lay_num))]
                    
            
        if jsz_finger_layers:
            
            for pnl_step, set_step in [("panel", "set"), ("panel", "edit"), ("set", "edit")]:
                
                if pnl_step not in matrixinfo["gCOLstep_name"]:
                    continue
                
                all_steps = get_panelset_sr_step(self.job_name, pnl_step, is_all=False)
                if set_step not in all_steps:
                    continue
                
                step = gClasses.Step(job, pnl_step)
                step.open()
                step.COM("units,type=mm")  
                # get_sr_area_flatten("surface_fill", pnl_step, get_sr_step=True)
                step.removeLayer("sr_fill_surface")
                step.createLayer("sr_fill_surface")
                step.clearAll()
                step.affect("sr_fill_surface")
                step.reset_fill_params()
                step.COM("sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,"
                         "step_max_dist_x=2540,step_max_dist_y=2540,sr_margin_x=0,sr_margin_y=0,"
                         "sr_max_dist_x=2540,sr_max_dist_y=2540,nest_sr=yes,stop_at_steps=,"
                         "consider_feat=no,consider_drill=no,consider_rout=no,"
                         "dest=affected_layers,attributes=no")
                step.COM("sel_resize,size=-1000")
                
                if pnl_step == "panel":
                    if modify_type == "delete":
                        for worklayer in jsz_finger_layers:
                            step.flatten_layer(worklayer, worklayer+"_jsz_tmp")
                            step.clearAll()
                            step.affect(worklayer+"_jsz_tmp")
                            step.resetFilter()
                            #step.refSelectFilter("surface_fill", mode="disjoint")
                            #if step.featureSelected():
                                #step.selectDelete()
                            
                            step.filter_set(feat_types='line;arc', polarity='positive')
                            step.refSelectFilter("sr_fill_surface")
                            step.removeLayer(worklayer+"pnl_jsz_line")
                            if step.featureSelected():
                                step.copySel(worklayer+"pnl_jsz_line")
                                
                            if step.isLayer(worklayer+"pnl_jsz_line"):
                                get_panel_features_in_set_position(self.job_name, set_step,
                                                                   pnl_step,worklayer+"set_jsz_line", 
                                                                   worklayer+"pnl_jsz_line")
                                
                                edit_step = gClasses.Step(job, set_step)
                                edit_step.open()
                                edit_step.COM("units,type=mm")
                                if edit_step.isLayer(worklayer+"set_jsz_line"):
                                    # 删除前备份
                                    modify_layer = True
                                    edit_step.copyLayer(self.job_name, set_step, worklayer, worklayer+"_jsz_bak")
                                    edit_step.copyLayer(self.job_name, set_step,worklayer+"set_jsz_line", worklayer+"set_jsz_line_tmp")
                                    
                                    edit_step.clearAll()
                                    edit_step.affect(worklayer+"set_jsz_line_tmp")                                    
                                    edit_step.COM("sel_resize,size=20")
                                    edit_step.contourize()
                                    
                                    edit_step.clearAll()
                                    edit_step.resetFilter()
                                    edit_step.affect(worklayer)
                                    edit_step.refSelectFilter(worklayer+"set_jsz_line_tmp", mode="cover")
                                    if edit_step.featureSelected():
                                        edit_step.selectDelete()
                                        
                                    edit_step.clearAll()
                                edit_step.close()
                                        
                    if modify_type == "reback":
                        # 还原之前的备份层
                        edit_step = gClasses.Step(job, set_step)
                        edit_step.open()
                        for worklayer in jsz_finger_layers:
                            if edit_step.isLayer(worklayer+"_jsz_bak"):                            
                                edit_step.copyLayer(self.job_name, set_step, worklayer+"_jsz_bak", worklayer)
                        edit_step.close()
                                        
                else:
                    if modify_type == "delete":
                        for worklayer in jsz_finger_layers:
                            if step.isLayer(worklayer+"set_jsz_line"):
                                get_panel_features_in_set_position(self.job_name, set_step,
                                                                   pnl_step,worklayer+"pcs_jsz_line", 
                                                                   worklayer+"set_jsz_line")
                                
                                edit_step = gClasses.Step(job, set_step)
                                edit_step.open()
                                edit_step.COM("units,type=mm")
                                if edit_step.isLayer(worklayer+"pcs_jsz_line"):
                                    # 删除前备份
                                    modify_layer = True
                                    edit_step.copyLayer(self.job_name, set_step, worklayer, worklayer+"_jsz_bak")
                                    edit_step.clearAll()
                                    edit_step.affect(worklayer+"pcs_jsz_line")
                                    edit_step.COM("sel_resize,size=20")
                                    edit_step.contourize()
                                    
                                    edit_step.clearAll()
                                    edit_step.resetFilter()
                                    edit_step.affect(worklayer)
                                    edit_step.refSelectFilter(worklayer+"pcs_jsz_line", mode="cover")
                                    if edit_step.featureSelected():
                                        edit_step.selectDelete()
                                        
                                    edit_step.filter_set(feat_types='pad', polarity='positive')
                                    edit_step.COM("filter_set,filter_name=popup,update_popup=no,profile=out")
                                    edit_step.setAttrFilter(".smd")
                                    
                                    edit_step.refSelectFilter(worklayer+"pcs_jsz_line")
                                    # edit_step.PAUSE("ddd")
                                    if edit_step.featureSelected():
                                        edit_step.selectDelete()
                                        
                                    edit_step.clearAll()
                                edit_step.close()
                                        
                    if modify_type == "reback":
                        # 还原之前的备份层
                        edit_step = gClasses.Step(job, set_step)
                        edit_step.open()
                        for worklayer in jsz_finger_layers:
                            if edit_step.isLayer(worklayer+"_jsz_bak"):                            
                                edit_step.copyLayer(self.job_name, set_step, worklayer+"_jsz_bak", worklayer)
                                
                            edit_step.removeLayer(worklayer+"_jsz_tmp")
                            edit_step.removeLayer(worklayer+"pnl_jsz_line")
                            edit_step.removeLayer(worklayer+"set_jsz_line")
                            edit_step.removeLayer(worklayer+"set_jsz_line_tmp")
                            edit_step.removeLayer(worklayer+"pcs_jsz_line")
                            edit_step.removeLayer(worklayer+"_jsz_bak")
                        edit_step.removeLayer("sr_fill_surface")
                        edit_step.close()

                step.close()
            if modify_type == "delete":
                for name in ["set", "edit"]:
                    if name in matrixinfo["gCOLstep_name"]:
                        step = gClasses.Step(job, name)
                        step.open()
                        step.clearAll()
                        step.COM("display_sr,display=yes")
                        for i, worklayer in enumerate(jsz_finger_layers):
                            step.display_layer(worklayer, num=i+1)
                        step.close()
                            
                if modify_layer:
                    job.PAUSE(u"镀金板输出AVI资料时需要删除金手指引线，请检查edit跟set内引线是否删除干净，同时注意引线是否为内拉设计，请手工删除！".encode("utf8"))
                if not modify_layer:
                    job.PAUSE(u"镀金板输出AVI资料时需要删除金手指引线，删除引线失败，请检查是否有引线并手动删除！".encode("utf8"))
                    
                if jsz_xiebian:
                    for name in ["set", "edit"]:
                        if name in matrixinfo["gCOLstep_name"]:
                            step = gClasses.Step(job, name)
                            step.open()
                            step.clearAll()
                            step.COM("display_sr,display=yes")
                            for i, worklayer in enumerate(["m1", "m2"]):
                                if step.isLayer(worklayer):                                    
                                    step.display_layer(worklayer, num=i+1)
                            step.close()
                                    
                    job.PAUSE(u"检测到此型号有斜边流程，AVI资料输出前请确认是否将斜边位置开窗做出!!".encode("utf8"))
                
        if kz_drills:
            
            all_steps = get_panelset_sr_step(self.job_name, "panel", is_all=True)
            
            dic_zu = {}
            for layer in kz_drills:
                if layer == "cdc":
                    dic_zu[layer] = "l1"
                if layer == "cds":
                    dic_zu[layer] = "l{0}".format(int(lay_num))
                result = re.match("^cd([0-9]{1,2})-([0-9]{1,2})[cs]$", layer)
                if result:
                    if layer.endswith("c"):
                        dic_zu[layer] = "l{0}".format(*result)
                    if layer.endswith("s"):
                        dic_zu[layer] = "l{1}".format(*result)
                                
            for stepname in all_steps:                
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")
                for drill_layer, sig_layer in dic_zu.iteritems():
                    
                    if modify_type == "delete":
                        # 删除前备份
                        step.copyLayer(job.name, stepname, sig_layer, sig_layer+"_kz_bak")
                        
                        step.clearAll()
                        step.affect(drill_layer)
                        step.resetFilter()
                        step.setAttrFilter(".drill,option=non_plated")
                        step.selectAll()
                        step.removeLayer("kz_npth_tmp")
                        if step.featureSelected():
                            step.copySel("kz_npth_tmp")
                        
                            step.clearAll()
                            step.affect(sig_layer)
                            step.resetFilter()
                            step.refSelectFilter("kz_npth_tmp", mode='cover', polarity="positive")
                            if step.featureSelected():
                                step.selectDelete()
                                modify_layer = True
                            
                        step.clearAll()
                            
                    if modify_type == "reback":
                        # 还原之前的备份层
                        if step.isLayer(sig_layer+"_kz_bak"):                            
                            step.copyLayer(job.name, stepname, sig_layer+"_kz_bak", sig_layer)                            
                step.close()
            if modify_type == "reback":
                # 还原备份层之后 清除备份层
                step = gClasses.Step(job, "panel")
                for drill_layer, sig_layer in dic_zu.iteritems():
                    if step.isLayer(sig_layer+"_kz_bak"):       
                        step.removeLayer(sig_layer+"_kz_bak")
                        
                    if step.isLayer(sig_layer+"_jsz_bak"):
                        step.removeLayer(sig_layer+"_jsz_bak")
                        
        return modify_layer

    def mkdir(self, path):
        '''
        递归判断目录级是否存在，不存在一级一级向下创建
        :param path: 传入需要创建的绝对路径
        :return: None
        '''
        if not os.path.isdir(path):
            self.mkdir(os.path.split(path)[0])
        else:
            return
        os.mkdir(path)

    def Message(self, text):
        """
        Msg窗口
        :param text: 显示的内容
        :return:None
        """
        # 警告信息提示框
        message = QtGui.QMessageBox.warning(None, u'警告信息!', text, QtGui.QMessageBox.Ok)
        # message.exec_()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    main = Main(debug=False)


# 2020.12.28
# Song
# 增加drl层

# --yk层没有将禁止输出 AresHe 2022.1.13
# http://192.168.2.120:82/zentao/story-view-3879.html

# app_Version:V1.3
# 2022.05.16
# Song
# AVI输出增加检测此料号是否有镭雕流程，如果有需topcam步骤中已运行此步骤，否则需要审批
# http://192.168.2.120:82/zentao/story-view-4097.html

#20230104 by lyh
#http://192.168.2.120:82/zentao/story-view-5022.html



