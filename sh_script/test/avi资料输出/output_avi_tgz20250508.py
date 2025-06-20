#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --加载相对位置，以实现InCAM与Genesis共用
"""
# 20241228 zl 把接触到profile的位置去掉金手指引线
# 20250108 zl 去引线的逻辑   1.n_electric属性的线  2.与金手指接触的线并且超出板外
# 20250120 zl 排除外层特殊命名的型号
"""

import os
import platform
import sys
import shutil
import re
import socket
localip = socket.gethostbyname_ex(socket.gethostname())
computer_id = localip[2][0]
if "172.28.30" in computer_id:
    db = "db3"
else:
    db = "db1"

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
import genClasses_zl as gen
from genesisPackages_zl import get_panelset_sr_step, \
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
            jstr1 = '<span>AVI输出放行.时间:%s,CAM用户:%s.料号%s.有镭雕打码流程，但未运行镭雕资料输出,请放行</span>' % (time_form, self.cam_user,self.job_name)
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
        # 20250120 先找到需要输出的层 再去找里面的二维码
        self.origin_name = self.job_name
        self.tgz_layers = []
        self.silk_layers = []
        # 外层
        self.out_signals = []
        # 防焊
        self.solder_masks = []
        self.check_sgt_layers = ['sgt-c', 'sgt-s']
        self.outline = ['ww', 'out']
        self.drl = ['drl']
        self.check_side = ['top', 'bottom']
        self.sgt_layers = []
        self.get_layers()
        # 20250120 zl 备份动态二维码$$job层
        self.dynamic_barcodes = {}
        current_job = gen.Job(self.job_name)
        self.panel_sr_step = get_panelset_sr_step(self.job_name, 'panel')
        # 20250124 panel中找二维码所在的层
        ewm_layers = []
        panel_step = gen.Step(current_job, 'panel')
        panel_step.initStep()
        for layer in self.tgz_layers:
            flat_layer = '%s+++' % layer
            panel_step.removeLayer(flat_layer)
            panel_step.Flatten(layer, flat_layer)
            layer_obj = gen.Layer(panel_step, flat_layer)
            panel_step.affect(flat_layer)
            panel_step.setFilterTypes('text')
            panel_step.selectAll()
            panel_step.resetFilter()
            if panel_step.Selected_count():
                barcodes = layer_obj.featout_dic_Index(units="mm", options='select+feat_index')["barcodes"]
                if barcodes:
                    ewm_layers.append(layer)
            panel_step.unaffectAll()
            panel_step.removeLayer(flat_layer)
        if ewm_layers:
            for stepname in self.panel_sr_step + ['panel']:
                step = gen.Step(current_job, stepname)
                step.initStep()
                for layer in ewm_layers:
                    tmp_layer = '%s+++%s' % (layer, self.GEN.pid)
                    if step.isLayer(tmp_layer):
                        step.truncate(tmp_layer)
                    layer_obj = gen.Layer(step, layer)
                    step.affect(layer)
                    step.setFilterTypes('text')
                    step.selectAll()
                    step.resetFilter()
                    if step.Selected_count():
                        barcodes = layer_obj.featout_dic_Index(units="mm", options='select+feat_index')["barcodes"]
                        has_dynamic_barcode = False
                        step.unaffectAll()
                        if barcodes:
                            step.affect(layer)
                            step.copySel(tmp_layer)
                            step.unaffectAll()
                            step.affect(tmp_layer)
                            for barcode in barcodes:
                                text = barcode.text.replace("'", "").lower()
                                new_text = barcode.text.replace("'", "").replace('$$', '$#')
                                if '$$job' in text or '$${job}' in text:
                                    step.selectByIndex(tmp_layer, barcode.feat_index)
                                    step.changeText(new_text)
                                    has_dynamic_barcode = True
                                step.clearSel()
                            step.unaffectAll()
                        if has_dynamic_barcode:
                            if stepname not in self.dynamic_barcodes.keys():
                                self.dynamic_barcodes[stepname] = []
                            if layer not in self.dynamic_barcodes[stepname]:
                                self.dynamic_barcodes[stepname].append(layer)
                    step.unaffectAll()
            current_job.save()
        # 20241217 zl 复制料号
        copy_jobname = self.job_name + '+++' + str(self.GEN.pid)
        self.GEN.COPY_ENTITY('job', self.job_name, self.job_name, copy_jobname, copy_jobname, db)
        # 20250120 zl 复制完料号后把临时层删掉
        panel_step.initStep()
        for layer in ewm_layers:
            tmp_layer = '%s+++%s' % (layer, self.GEN.pid)
            panel_step.removeLayer(tmp_layer)
        current_job.save()
        self.job_name = copy_jobname
        self.job = gen.Job(self.job_name)
        self.job.open(1)
        self.SR_INFO = self.GEN.getSrMinMax(self.job_name, 'panel')
        # self.get_layers()
        # if len(self.silk_layers) == 0:
        #     errorMsg = u'没有文字层!'
        #     self.Message('%s' % errorMsg)
        #     sys.exit()
        self.check_profile()
        self.export_tgz()
        # 回到原料号
        gClasses.Top().deleteJob(self.job_name)
        current_job.open(1)


    def __del__(self):
        if self.debug:
            self.GEN.disconnect()

    def get_layers(self):
        # 通过DO_INFO从matrix中获取成型层别
        matrix_info = self.GEN.DO_INFO('-t matrix -e %s/matrix' % self.origin_name)
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
            # if name in self.outline:
            #     self.tgz_layers.append(name)
            # 外形
            if re.match('ww(\d+)?$|out$', name):
                self.tgz_layers.append(name)
            # 控深锣
            if name in ('rout-cdc', 'rout-cds'):
                self.tgz_layers.append(name)
            # 镀金层
            if name in ('gold-c', 'gold-s', 'etch-c', 'etch-s'):
                self.tgz_layers.append(name)

            # 化金选化层
            if name in ('xlym-c', 'xlym-s'):
                self.tgz_layers.append(name)

            # 镀金选化层
            if re.match('linek-(c|s)-?(\d+)?$', name):
                self.tgz_layers.append(name)

            if name in self.drl:
                self.tgz_layers.append(name)

            # 二钻和外层盲孔
            if type == 'drill' and context == 'board':
                if re.match('s1-\d+$|s%s-\d+$|\d+nd$' % lay_num, name):
                    self.tgz_layers.append(name)
                    self.drl.append(name)

            if type == 'silk_screen' and context == 'board':
                self.tgz_layers.append(name)
                self.silk_layers.append(name)

            if type == 'solder_mask' and context == 'board':
                self.tgz_layers.append(name)
                self.solder_masks.append(name)

            if type == 'signal' and context == 'board' and side in ['top', 'bottom']:
                self.tgz_layers.append(name)
                # === Song 2020.7.13 增加检测，外层命名是否标准
                if self.origin_name[:13] in ('he0516gh011c1'):   # 20250120 zl 排除检测外层命名的型号
                    self.out_signals.append(name)
                else:
                    if re.match('^l[0-9][0-9]?$',name):
                        self.out_signals.append(name)
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
            tgz_path = os.path.join(r'D:\disk\film', self.origin_name)
        else:
            # 由于incampro的tmp目录不允许输出tgz，所以新建一级文件夹
            tmp_path = '/tmp/tmp'
            tgz_path = os.path.join(r'/id/workfile/hdi_film', self.origin_name)

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
        # --2023-10-24输入AVI资料删除线路和阻焊层'kscnc-out、kscnc-sm'两个symbol  -- ynh
        # self.del_kscnc_symbols()
        self.del_kscnc_symbols_new() # 20241220 zl
        # 输出资料前的处理
        self.export_pretreatment()
        # 检查控深钻外层是否有加比孔小0.2mm的pad 20230104 by lyh
        check_result = self.check_and_reback_layer("delete")
        # --执行tgz导出
        include_lyrs = '\;'.join(self.tgz_layers)
        self.GEN.VOF()
        self.GEN.COM('check_inout,mode=out,type=job,job=%s' % self.job_name)
        self.GEN.COM('save_job,job=%s,override=no' % self.job_name)
        self.GEN.COM('check_inout,mode=in,type=job,job=%s' % self.job_name)
        reVal = self.GEN.COM('export_job,job=%s,path=%s,mode=tar_gzip,submode=partial,steps_mode=include,steps=%s,'
                             'lyrs_mode=include,lyrs=%s,overwrite=yes,output_name=%s' % (self.job_name, tmp_path, ';'.join(self.panel_sr_step + ['panel']),include_lyrs, self.origin_name))
        self.GEN.CLOSE_JOB(self.job_name)
        self.GEN.VON()

        # if check_result:
        #     self.check_and_reback_layer("reback")
        #
        # # 还原之前修改的层
        # for lay in ks_bk_layers:
        #     if 'edit' in self.GEN.GET_STEP_LIST():
        #         self.GEN.OPEN_STEP('edit')
        #         self.GEN.COPY_LAYER(self.job_name, 'edit', lay + 'compbk', lay)
        #     if 'set' in self.GEN.GET_STEP_LIST():
        #         self.GEN.OPEN_STEP('set')
        #         self.GEN.COPY_LAYER(self.job_name, 'set', lay + 'compbk', lay)

        # self.GEN.VOF()
        # self.GEN.COM('check_inout,mode=out,type=job,job=%s' % self.job_name)
        # self.GEN.COM('save_job,job=%s,override=no' % self.job_name)
        # self.GEN.COM('check_inout,mode=in,type=job,job=%s' % self.job_name)
        # self.GEN.CLOSE_JOB(self.job_name)
        # self.GEN.VON()

        # --export异常，用于后续自动输出异常抛出纪录
        if reVal != 0:
            errorMsg = u"tgz导出失败！\n\n程序即将退出，请联系管理员!"
            self.Message('%s' % errorMsg)
        else:
            # --删除目标地址下的资料
            if os.path.exists(os.path.join(tgz_path, self.origin_name + str('_outavi.tgz'))):
                os.remove(os.path.join(tgz_path, self.origin_name + str('_outavi.tgz')))
            # --重命名临时目录下的tgz,并Move至对应地址
            shutil.move(os.path.join(tmp_path, self.origin_name + str('.tgz')),
                      os.path.join(tgz_path, self.origin_name + str('_outavi.tgz')))

            okMsg = u"tgz导出成功，程序版本：%s！！！" % self.app_Version
            self.Message('%s' % okMsg)

    # 20241220 zl 不能用环境中的JOB,重写
    def del_kscnc_symbols_new(self):
        del_res = {'res':False, 'layers':{'edit':[], 'set':[]},'delkspad':False}
        # del_ks_symbol_layers = self.GEN.GET_ATTR_LAYER('solder_mask') + self.GEN.GET_ATTR_LAYER('outer')
        del_ks_symbol_layers = self.job.matrix.returnRows('board','solder') + self.job.matrix.returnRows('board', 'signal', side='top|bottom')
        for layer in del_ks_symbol_layers:
            steps = []
            if 'edit' in self.job.stepsList:
                steps.append('edit')
            if 'set' in self.job.stepsList:
                steps.append('set')
            for s in steps:
                info = self.job.DO_INFO("-t layer -e %s/%s/%s -m script -d SYMS_HIST -p symbol" % (self.job_name, s , layer))
                print info['gSYMS_HISTsymbol']
                if 'kscnc-sm' in info['gSYMS_HISTsymbol'] or 'kscnc-out' in info['gSYMS_HISTsymbol']:
                    del_res['res'] = True
                    del_res['layers'][s].append(layer)

        if del_res['res']:
            for s in del_res['layers'].keys():
                if del_res['layers'][s]:
                    step = gen.Step(self.job, s)
                    step.initStep()
                    for lay in del_res['layers'][s]:
                        step.affect(lay)
                        step.selectSymbol('kscnc-sm\;kscnc-out')
                        step.selectAll()
                        if step.Selected_count():
                            step.selectDelete()
                        step.resetFilter()
                        step.unaffectAll()

    def del_kscnc_symbols(self):
        del_res = {'res':False, 'layers':{'edit':[], 'set':[]},'delkspad':False}
        # job_name = os.environ.get('JOB') # 20241218 zl 不能使用environ中的JOB
        del_ks_symbol_layers = self.GEN.GET_ATTR_LAYER('solder_mask') + self.GEN.GET_ATTR_LAYER('outer')
        for layer in del_ks_symbol_layers:
            steps = []
            if 'edit' in self.GEN.GET_STEP_LIST():
                steps.append('edit')
            if 'set' in self.GEN.GET_STEP_LIST():
                steps.append('set')
            for s in steps:
                info = self.GEN.DO_INFO("-t layer -e %s/%s/%s -m script -d SYMS_HIST -p symbol" % (self.job_name, s , layer))
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
                        self.GEN.COPY_LAYER(self.job_name, s, lay, lay + '_kscnc_tmp')
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
        self.GEN.VON()

    def export_pretreatment(self):
        # 20250120 zl 把二维码静态层 替换到原始层
        for stepname, layers in self.dynamic_barcodes.items():
            if layers:
                gen_step = gen.Step(self.job, stepname)
                gen_step.initStep()
                for layer in layers:
                    tmp_layer = '%s+++%s' % (layer, self.GEN.pid)
                    gen_step.truncate(layer)
                    gen_step.affect(tmp_layer)
                    gen_step.moveSel(layer)
                    gen_step.unaffectAll()
        all_steps = get_panelset_sr_step(self.job_name, "panel", is_all=True)
        # 合并防焊/文字
        # 20250107 防焊不合并 提出人：徐后强
        # if self.solder_masks:
        #     merge_layer = {}
        #     for solder_mask in self.solder_masks:
        #             if re.match('(.*)-\d+$', solder_mask):
        #                 key = re.match('(.*)-\d+$', solder_mask).group(1)
        #                 if not merge_layer.has_key(key):
        #                     merge_layer[key] = []
        #                 merge_layer[key].append(solder_mask)
        #                 self.tgz_layers.remove(solder_mask)
        #     if merge_layer:
        #             for stepname in all_steps + ['panel']:
        #                 step = gen.Step(self.job, stepname)
        #                 step.initStep()
        #                 for k,v in merge_layer.items():
        #                     for l in v:
        #                         step.affect(l)
        #                     step.copySel(k)
        #                     step.unaffectAll()
        if self.silk_layers:
            merge_layer = {}
            for silk_layer in self.silk_layers:
                    if re.match('(.*)-\d+$', silk_layer):
                        key = re.match('(.*)-\d+$', silk_layer).group(1)
                        if not merge_layer.has_key(key):
                            merge_layer[key] = []
                        merge_layer[key].append(silk_layer)
                        self.tgz_layers.remove(silk_layer)
            if merge_layer:
                    for stepname in all_steps + ['panel']:
                        step = gen.Step(self.job, stepname)
                        step.initStep()
                        for k,v in merge_layer.items():
                            for l in v:
                                step.affect(l)
                            step.copySel(k)
                            step.unaffectAll()
        # 查询此料号是否有树脂塞孔+盖油电镀的流程
        data_info = get_inplan_all_flow(self.job_name[:13].upper(), True)
        process_ = set()
        for dic_info in data_info:
            if '树脂塞孔' in dic_info['WORK_CENTER_CODE']:
                process_.add('树脂塞孔')
            if '盖孔电镀' in dic_info['WORK_CENTER_CODE']:
                process_.add('盖孔电镀')
        if len(process_) == 2:
            # 机械钻
            mech_drills = filter(lambda l: re.match('\d+nd$|bd(c|s)(_ccd)?(-\d+)?$|cd(c|s)(-\d+)?$', l), self.job.matrix.returnRows('board', 'drill'))
            # 树脂塞孔层
            szsk_list = []
            rows = self.job.matrix.returnRows()
            for row in rows:
                if re.match('sz.*\.lp$', row):
                    # TODO 找外层树脂塞孔层
                    szsk_list.append(row)
            for stepname in all_steps + ['panel']:
                step = gen.Step(self.job, stepname)
                step.open()
                step.initStep()
                if mech_drills:
                    for mech_drill in mech_drills:
                        step.affect(mech_drill)
                    step.copySel('drl')
                    step.unaffectAll()
                if szsk_list:
                    # TODO drl去掉树脂塞孔
                    step.affect('drl')
                    step.refSelectFilter('\;'.join(szsk_list), mode='same_center')
                    if step.Selected_count():
                        step.selectDelete()
                    step.unaffectAll()
        # 去掉板外物件
        for stepname in self.job.stepsList:
            info = self.job.DO_INFO('-t step -e %s/%s -m script -d PROF_LIMITS' % (self.job_name, stepname))
            if info['gPROF_LIMITSxmin'] == 0 and info['gPROF_LIMITSymin'] == 0 and info[
                'gPROF_LIMITSxmax'] == 0 and info['gPROF_LIMITSymax'] == 0:
                continue
            step = gen.Step(self.job, stepname)
            step.initStep()
            tmp_prof = 'tmp_prof+++'
            step.removeLayer(tmp_prof)
            step.prof_to_rout(tmp_prof, 100)
            step.affect(tmp_prof)
            step.selectCutData()
            step.unaffectAll()
            for layer in self.out_signals + self.solder_masks + self.silk_layers + self.drl:
                step.affect(layer)
            step.refSelectFilter(tmp_prof)
            if step.Selected_count():
                step.selectReverse()
                if step.Selected_count():
                    step.selectDelete()
            step.unaffectAll()
            step.removeLayer(tmp_prof)
            step.removeLayer(tmp_prof+'+++')

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
        
        # data_info = get_inplan_all_flow(self.job_name.upper(), True)
        data_info = get_inplan_all_flow(self.origin_name[:13].upper(), True) # 用原料号名去查
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
                step.setGroup()
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
                                    # 20241228 和profile接触到的
                                    profile_ = 'profile_tmp+++'
                                    edit_step.removeLayer(profile_)
                                    edit_step.COM('profile_to_rout,layer=%s,width=1' % profile_)
                                    edit_step.affect(worklayer+"set_jsz_line_tmp")                                    
                                    edit_step.COM("sel_resize,size=20")
                                    edit_step.contourize()
                                    edit_step.refSelectFilter(profile_, mode='disjoint')
                                    if edit_step.featureSelected():
                                        edit_step.selectDelete()
                                    edit_step.clearAll()
                                    edit_step.removeLayer(profile_)
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
                            # set set内假手指string=gf如果接触到板内的删除
                            step = gClasses.Step(job, pnl_step)
                            step.open()
                            step.setGroup()
                            step.COM("units,type=mm")
                            step.affect(worklayer)
                            step.COM(
                                'set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=yes,attribute=.string,min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=gf')
                            step.refSelectFilter('sr_fill_surface')
                            step.resetFilter()
                            if step.featureSelected():
                                step.selectDelete()
                            step.clearAll()
                            # edit
                            edit_step = gClasses.Step(job, set_step)
                            edit_step.open()
                            edit_step.COM("units,type=mm")
                            edit_step.clearAll()
                            # 20250108 n_electric属性
                            edit_step.copyLayer(self.job_name, set_step, worklayer, worklayer + "_jsz_bak")
                            profile_ = 'profile_tmp+++'
                            edit_step.removeLayer(profile_)
                            edit_step.COM('profile_to_rout,layer=%s,width=1' % profile_)
                            edit_step.affect(worklayer)
                            edit_step.COM('set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=yes,attribute=.string,min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=gf')
                            edit_step.selectAll()
                            edit_step.resetFilter()
                            if edit_step.featureSelected():
                                edit_step.copySel(worklayer + "set_jsz_line_tmp")
                            edit_step.filter_set('line', 'positive')
                            edit_step.refSelectFilter(worklayer + "set_jsz_line_tmp")
                            if edit_step.featureSelected():
                                edit_step.COM('truncate_layer,layer=%s' % (worklayer + "set_jsz_line_tmp"))
                                edit_step.copySel(worklayer + "set_jsz_line_tmp")
                                edit_step.clearAll()
                                edit_step.affect(worklayer + "set_jsz_line_tmp")  # 接触到金手指的线
                                edit_step.refSelectFilter(profile_)
                                if edit_step.featureSelected():
                                    edit_step.COM('sel_reverse')
                                    if edit_step.featureSelected():
                                        edit_step.selectDelete()   # 只留下接触到profile的线
                            edit_step.clearAll()
                            edit_step.affect(worklayer)
                            edit_step.COM('set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=no,attribute=.n_electric,min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=')
                            edit_step.selectAll()
                            edit_step.resetFilter()
                            if edit_step.featureSelected():
                                edit_step.copySel(worklayer + "set_jsz_line_tmp")
                            edit_step.clearAll()
                            edit_step.affect(worklayer + "set_jsz_line_tmp")
                            edit_step.COM("sel_resize,size=20")
                            edit_step.clearAll()
                            edit_step.removeLayer(profile_)
                            edit_step.resetFilter()
                            edit_step.affect(worklayer)
                            edit_step.refSelectFilter(worklayer + "set_jsz_line_tmp", mode="cover")
                            if edit_step.featureSelected():
                                edit_step.selectDelete()
                            edit_step.clearAll()
                                        
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
        # 20250113 zl 斜边流程不放在if jsz_finger_layers内，单独判断
        if jsz_xiebian:
            for name in ["set", "edit"]:
                if name in matrixinfo["gCOLstep_name"]:
                    step = gClasses.Step(job, name)
                    step.open()
                    step.clearAll()
                    step.COM("display_sr,display=yes")
                    for i, worklayer in enumerate(["m1", "m2", 'm1-1', 'm2-1']):
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



