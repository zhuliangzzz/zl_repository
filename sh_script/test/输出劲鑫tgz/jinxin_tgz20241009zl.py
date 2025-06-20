#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --加载相对位置，以实现InCAM与Genesis共用
import json
import os
import platform
import sys
import shutil
import re
from datetime import datetime
import filecmp

# from sympy import false

if platform.system() == "Windows":
    # sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"E:/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genCOM_26 as genCOM
from Gateway import Gateway
from PyQt4 import QtCore, QtGui, Qt
import Oracle_DB
import mwClass_V2 as diong

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

global long_side
long_side = False


class Main:
    def __init__(self, debug=False):
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
        self.SR_INFO = self.GEN.getSrMinMax(self.job_name, 'panel')
        #self.GEN.PAUSE (str(self.SR_INFO))
        self.tgz_layers = []
        self.silk_layers = []
        self.break_vg_date = False
        self.rename_layers = []
        self.panel_srs = ['panel']
        self.get_layers()
        if len(self.silk_layers) == 0:
            errorMsg = u'没有文字层!'
            self.Message('%s' % errorMsg)
            sys.exit()
        if self.job_name[1:4] == '318':
            get_result = os.system("python /incam/server/site_data/scripts/hdi_scr/Panel/chk_date_code/chk_date_code.py")
            if get_result != 0:
                sys.exit()
        ##检测资料是否保存
        ischange=self.GEN.DO_INFO('-t job -e %s -m script -d IS_CHANGED' % self.job_name)
        
        if ischange['gIS_CHANGED'] == 'yes':
            errorMsg = u'检测到资料未保存！请保存后输出！'
            self.Message('%s' % errorMsg)
            sys.exit()
        # --检测文字层是否有大面积的白油块（超过24%则不允许使用劲鑫打印）
        self.printSilk = True
        self.CheckNetSurface_Persent()
        if not self.printSilk:
            errorMsg = u'检测到文字白油块面积>24%,不允许使用劲鑫打印机生产！'
            self.Message('%s' % errorMsg)
            # if 'h75808gbr97' in self.job_name:
            if re.search('h75808gbr97|t88810pbd47a', self.job_name):
                pass
            else:
                sys.exit()
        # 20220215 ；lkx吕康侠添加识别文字流程只能喷印才能输出
        Checkewm = 'yes'
        ControlTheOutput = self.ControlTheOutput()
        if not ControlTheOutput:
            # self.Message(u'检测到ERP数据没有喷印的文字流程！请确认！程序退出！')
            Checkewm = 'no'
            # pf = diong.showMsg(u"检测到ERP数据没有喷印的文字流程！！", Msg2=u"请输入密码确认放行！", okButton=u"继续", cancel=u"退出",
            #                    passwdCheck=True, passwd="sh-pw")
            pf = diong.AboutDialog(u"检测到ERP数据没有喷印的文字流程！！", Msg2=u"请输入密码确认放行！", okButton=u"继续", cancel=u"退出",
                               passwdCheck=True, passwd="sh-pw")
            pf.exec_()
            if pf.selBut != 'ok': sys.exit()
        if ControlTheOutput == "F":
            if Checkewm == 'yes':
                self.Message(u'板内二维码请转成铜皮并去掉.string=barcode的属性再输出')
                sys.exit()
        if platform.system() == "Windows":
            # --windows环境下copy userattr文件，以使id=101属性生效
            self.add_id_101_user_attr()
        # --TODO 阴阳拼板，释放关第才能输出
        self.flipList = []
        self.recursion_get_sr('panel')
        self.flipStepName('panel')
        self.check_profile()
        self.check_vg_date()
        if self.break_vg_date:
            self.release_depend()
            self.break_vg_date_code()
        self.check_id_101()
        # 检查panel拼版是否有旋转拼版
        rotate_steps = self.check_rotate_tips()
        if rotate_steps:
            self.Message(u'检测到旋转拼版注意更改周期\n拼版旋转的step：' + "、".join(rotate_steps))
        self.export_tgz()

    def __del__(self):
        if self.debug:
            self.GEN.disconnect()

    def get_layers(self):
        # 通过DO_INFO从matrix中获取成型层别
        self.tgz_layers = []
        self.silk_layers = []
        self.top_solder_layers = []
        self.bot_solder_layers = []
        matrix_info = self.GEN.DO_INFO('-t matrix -e %s/matrix' % self.job_name)
        for i, name in enumerate(matrix_info['gROWname']):
            type = matrix_info['gROWlayer_type'][i]
            side = matrix_info['gROWside'][i]
            context = matrix_info['gROWcontext'][i]
            if type == 'silk_screen' and context == 'board':
                self.tgz_layers.append(name)
                self.silk_layers.append(name)
            if type == 'solder_mask' and context == 'board':
                self.tgz_layers.append(name)
                if side == 'top':
                    self.top_solder_layers.append(name)
                elif side == 'bottom':
                    self.bot_solder_layers.append(name)
            if type == 'signal' and context == 'board' and side in ['top', 'bottom']:
                self.tgz_layers.append(name)
                # === Song 2020.7.13 增加检测，外层命名是否标准
                if re.match('^l[0-9][0-9]?$', name):
                    pass
                else:
                    errorMsg = u'%s 非正常外层层别命名，程序退出!' % name
                    self.Message('%s' % errorMsg)
                    sys.exit()
                    
    def get_penyin_silk_layers(self):
        """获取喷印字符层次20230731 by lyh"""
        inplan_flow = get_inplan_all_flow(self.job_name.upper(), select_dic=True)
        #通过判断喷印跟印刷层次跟资料内的文字层都匹配 来决定是否弹出界面
        # 匹配 不弹出界面 不匹配 弹出界面让用户选择
        yinshua_layers = []
        penyin_layers = []
        dic_silk_type = {}# 检测是否喷印跟印刷共存
        erp_penyin_layers = []
        for i in inplan_flow:
            if i["WORK_CENTER_CODE"] and "文字" in i["WORK_CENTER_CODE"]:
                for silk_type in ["印刷", "喷印"]:                    
                    if i["PROCESS_DESCRIPTION"] and silk_type in i["PROCESS_DESCRIPTION"]:
                        dic_silk_type[silk_type] = "exists"
                        if i["WORK_DESCRIPTION"] and "使用曝光资料" in i["WORK_DESCRIPTION"]: 
                            if i['VALUE_AS_STRING'] is not None :
                                value = i['VALUE_AS_STRING']
                                for layer in self.silk_layers:
                                    if layer in value.split(","):
                                        if silk_type == "印刷":
                                            yinshua_layers.append(layer)
                                        else:
                                            penyin_layers.append(layer)
                                            
                                if silk_type == "喷印":
                                    erp_penyin_layers += value.split(",")                                    
        
        select_layers = penyin_layers
        manual = False
        for layer in penyin_layers:
            if layer not in erp_penyin_layers:
                manual = True
                
        for layer in erp_penyin_layers:
            if layer not in penyin_layers:
                manual = True
                
        if manual:
            title = u"检测inplan喷印字符工具{0}跟tgz内的字符层{1}不一致，\n请手动勾选要输出的喷印文字层,\n若喷印字符层没加board属性，请退出程序，加上board属性在输出。"
            select_layers = self.set_select_silk_layer_ui(title.format(list(set(erp_penyin_layers)), list(set(penyin_layers))))
        else:
            if not erp_penyin_layers:
                title = u"抓取inplan喷印字符工具失败，\n请手动勾选要输出的喷印文字层"
                select_layers = self.set_select_silk_layer_ui(title)                
            
        return select_layers, yinshua_layers
    
    def set_select_silk_layer_ui(self, title):
        
        self.sel_layer_widget = QtGui.QDialog()
        self.sel_layer_widget.setWindowTitle(u"选择层别")
        self.sel_layer_widget.setWindowFlags(Qt.Qt.Window | Qt.Qt.WindowStaysOnTopHint)
        self.sel_layer_widget.setGeometry(700, 300, 0, 0)
        title_label = QtGui.QLabel(title)
        label = QtGui.QLabel(u"选中")
        label1 = QtGui.QLabel(u"层别")
        group_layout = QtGui.QGridLayout()
        group_layout.addWidget(title_label, 0, 0, 1, 4, Qt.Qt.AlignCenter)
        group_layout.addWidget(label, 1, 0, 1, 1)
        group_layout.addWidget(label1, 1, 1, 1, 1)
        
        self.dic_editor = {}
        for row, layer in enumerate(self.silk_layers):
            label = QtGui.QLabel(layer)
            self.dic_editor[layer] = [None, None, None]
            self.dic_editor[layer][0] = QtGui.QCheckBox()
            group_layout.addWidget(self.dic_editor[layer][0], row+2, 0, 1, 1)  
            group_layout.addWidget(label, row+2, 1, 1, 1)        
        
        start_btn = QtGui.QPushButton(u"确定")
        quit_btn = QtGui.QPushButton(u"退出")
        quit_btn.hide()
        if u"退出" in title:
            quit_btn.show()
            
        group_layout.addWidget(start_btn, 50, 0, 1, 1)
        group_layout.addWidget(quit_btn, 50, 1, 1, 1)
        
        self.sel_layer_widget.setObjectName("mainWindow")
        self.sel_layer_widget.setLayout(group_layout)
        start_btn.clicked.connect(self.check_value)
        quit_btn.clicked.connect(sys.exit)
        self.sel_layer_widget.exec_()
        
        return self.dic_value.keys()
        
    def check_value(self):
        self.dic_value = {}
        for key, value in self.dic_editor.iteritems():
            select_box = value[0]        
            if select_box.isChecked():
                self.dic_value[key] = "select"
                
        if not self.dic_value:
            QtGui.QMessageBox.information(self.sel_layer_widget,
                                          u'警告',
                                          u"没有层被选中，请勾选层在执行，请检查！",
                                          1)
            return 0
                
        self.sel_layer_widget.accept()        
        
    def CheckNetSurface_Persent(self):
        """
        检测net中文字层的白油块（即大Surface）面积是否超过24%
        :return:None        
        """
        for layer in self.silk_layers:
            getAttr = self.GEN.DO_INFO("-t layer -e %s/net/%s -d ATTR" % (self.job_name, layer))
            for i, name in enumerate(getAttr['gATTRname']):
                attName = getAttr['gATTRname'][i]
                attVal = getAttr['gATTRval'][i]
                # --判断是否为存储字符白油块占比的字段
                if attName == 'silk_surface_persent':
                    if float(attVal) > 24.0:
                        self.printSilk = False
                    break

    def check_vg_date(self):
        """
        检查周期旋转角度，机台只能识别0,90,180及270度的周期
        :return:
        :rtype:
        """
        for step in self.panel_srs:
            self.GEN.COM('open_entity,job=%s,type=step,name=%s,iconic=no' % (self.job_name, step))
            self.GEN.AUX('set_group,group=%s' % self.GEN.COMANS)
            self.GEN.CHANGE_UNITS('mm')
            self.GEN.CLEAR_LAYER()
            if self.break_vg_date:
                break
            for layer in self.silk_layers:
                self.GEN.AFFECTED_LAYER(layer, 'yes')
                self.GEN.FILTER_RESET()
                # --挑选出所有周期
                if platform.system() == 'Windows':
                    self.GEN.FILTER_SET_TYP('text')
                    self.GEN.COM('adv_filter_set,filter_name=popup,update_popup=yes,fontname=vgt_date\;vgt_date_new')
                    self.GEN.FILTER_SELECT()
                    # --反选0,90,180,270角度的周期，剩下非正常角度的周期
                    self.GEN.COM(
                        'adv_filter_set,filter_name=popup,update_popup=yes,rotations=0\;90\;180\;270,min_rotation=0,max_rotation=0')
                    self.GEN.FILTER_SELECT(op='unselect')
                    # --倾斜的文字以text*形式的pad存在genesis中
                    self.GEN.FILTER_RESET()
                    self.GEN.FILTER_SET_TYP('pad')
                    self.GEN.COM('filter_set,filter_name=popup,update_popup=no,include_syms=text*')
                    self.GEN.FILTER_SELECT()
                    self.GEN.FILTER_RESET()
                else:
                    self.GEN.COM('set_filter_type,filter_name=,lines=no,pads=no,surfaces=no,arcs=no,text=yes')
                    self.GEN.COM('adv_filter_reset')
                    self.GEN.COM('adv_filter_set,filter_name=popup,active=yes,limit_box=no,bound_box=no,srf_values=no,'
                                 'srf_area=no,mirror=any,ccw_rotations=,txt_types=string,fontname=vgt_date\;vgt_date_new')
                    self.GEN.FILTER_SELECT()
                    self.GEN.COM('adv_filter_reset')
                    self.GEN.COM('adv_filter_set,filter_name=popup,active=yes,limit_box=no,bound_box=no,srf_values=no,'
                                 'srf_area=no,mirror=any,ccw_rotations=0\;90\;180\;270,txt_types=string,fontname=vgt_date\;vgt_date_new')
                    self.GEN.FILTER_SELECT(op='unselect')
                    self.GEN.FILTER_RESET()
                count = int(self.GEN.GET_SELECT_COUNT())
                if count != 0:
                    rst = QtGui.QMessageBox.warning(None, u'警告信息!', u'%s --> 周期有不规则角度，待产线申请时再输出' %
                                                    layer, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
                    if rst == QtGui.QMessageBox.Yes:
                        self.GEN.AFFECTED_LAYER(layer, 'no')
                        sys.exit()
                    else:
                        # --打散选中的周期
                        self.GEN.AFFECTED_LAYER(layer, 'no')
                        self.break_vg_date = True
                        break
                else:
                    self.GEN.AFFECTED_LAYER(layer, 'no')
            self.GEN.CLOSE_STEP()

    def break_vg_date_code(self):
        """
        打散所有周期
        :return:
        :rtype:
        """
        self.GEN.DELETE_LAYER('c1_before_break')
        self.GEN.DELETE_LAYER('c2_before_break')
        for step in self.panel_srs:
            self.GEN.COM('open_entity,job=%s,type=step,name=%s,iconic=no' % (self.job_name, step))
            self.GEN.AUX('set_group,group=%s' % self.GEN.COMANS)
            self.GEN.CHANGE_UNITS('mm')
            self.GEN.CLEAR_LAYER()
            for layer in self.silk_layers:
                bei_fen_layer = '%s_before_break' % layer
                if self.GEN.LAYER_EXISTS(bei_fen_layer, job=self.job_name, step=step) == 'no':
                    self.GEN.COM('rename_layer,name=%s,new_name=%s' % (layer, bei_fen_layer))
                    self.rename_layers.append(bei_fen_layer)
                    try:
                        # --TODO 考虑阴阳拼创建层时报错,try语句并不能catch此异常，所以并没有什么用
                        self.GEN.CREATE_LAYER(layer, ins_lay=bei_fen_layer, context='board', add_type='silk_screen')
                        # self.GEN.PAUSE("create layer ok")
                    except:
                        # self.GEN.PAUSE("create layer error")
                        pass
                # --TODO 从备份层中copy资料
                self.GEN.COPY_LAYER(self.job_name, step, bei_fen_layer, layer)
                self.GEN.AFFECTED_LAYER(layer, 'yes')
                self.GEN.FILTER_RESET()
                # --挑选出所有周期
                if platform.system() == 'Windows':
                    self.GEN.FILTER_SET_TYP('text')
                    self.GEN.COM('adv_filter_set,filter_name=popup,update_popup=yes,fontname=vgt_date\;vgt_date_new')
                    self.GEN.FILTER_SELECT()
                    # --倾斜的文字以text*形式的pad存在genesis中
                    self.GEN.FILTER_RESET()
                    self.GEN.FILTER_SET_TYP('pad')
                    self.GEN.COM('filter_set,filter_name=popup,update_popup=no,include_syms=text*')
                    self.GEN.FILTER_SELECT()
                    self.GEN.FILTER_RESET()
                else:
                    self.GEN.COM('set_filter_type,filter_name=,lines=no,pads=no,surfaces=no,arcs=no,text=yes')
                    self.GEN.COM('adv_filter_reset')
                    self.GEN.COM('adv_filter_set,filter_name=popup,active=yes,limit_box=no,bound_box=no,srf_values=no,'
                                 'srf_area=no,mirror=any,ccw_rotations=,txt_types=string,fontname=vgt_date\;vgt_date_new')
                    self.GEN.FILTER_SELECT()
                    self.GEN.FILTER_RESET()
                # self.GEN.PAUSE("break rotate text")
                count = self.GEN.GET_SELECT_COUNT()
                if count != 0:
                    # --打散选中的周期
                    self.GEN.COM('sel_break')
                self.GEN.AFFECTED_LAYER(layer, 'no')
            self.GEN.CLOSE_STEP()

    def recursion_get_sr(self, step_name):
        """
        递归获取所有在panel中的step
        :return:
        :rtype:
        """
        info = self.GEN.DO_INFO('-t step -e %s/%s -m script -d SR' % (self.job_name, step_name))
        for step in info['gSRstep']:
            # if step not in self.flipList:
            #     if step.endswith('flip'):
            #         self.flipList.append(step)
            if step not in self.panel_srs:
                self.panel_srs.append(step)
                info_sr = self.GEN.DO_INFO('-t step -e %s/%s -m script -d SR' % (self.job_name, step))
                if info_sr:
                    # --如果子排版中有子排版，则递归调用
                    self.recursion_get_sr(step)

    def flipStepName(self, step):
        """
        递归寻找出有镜像的step，并append到 flipList数组中
        :param step: step名
        :return: None
        """
        DicInfo = self.GEN.DO_INFO('-t step -e %s/%s -m script -d SR -p flip+step' % (self.job_name, step))
        for index, stepName in enumerate(DicInfo['gSRstep']):
            if stepName not in self.flipList:
                if platform.system() == "Windows":
                    if stepName.endswith('flip'):
                        self.flipStepName(stepName)
                        info = self.GEN.DO_INFO('-t step -e %s/%s -m script -d ATTR' % (self.job_name, stepName))
                        for attr, val in zip(info['gATTRname'], info['gATTRval']):
                            if attr == '.flipped_of' and not val == '':
                                self.flipList.append(stepName)
                                break
                else:
                    if DicInfo['gSRflip'][index] == 'yes':
                        self.flipList.append(stepName)
                        self.flipStepName(stepName)
        # --返回
        return

    def release_depend(self):
        """
        释放依赖关系
        :return:
        :rtype:
        """
        for stepName in self.flipList:
            if platform.system() == "Windows":
                self.GEN.VOF()
                self.GEN.COM('change_step_dependency,job=%s,step=%s,operation=release' % (self.job_name, stepName))
                self.GEN.VON()
            else:
                # --打开SETP，并释放关联关系
                self.GEN.OPEN_STEP(job=self.job_name, step=stepName)
                self.GEN.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % self.job_name)
                self.GEN.CLOSE_STEP()

    def restore_depend(self):
        """
        重建依赖关系
        :return:
        :rtype:
        """
        for stepName in self.flipList:
            if platform.system() == "Windows":
                self.GEN.VOF()
                self.GEN.COM('change_step_dependency,job=%s,step=%s,operation=restore' % (self.job_name, stepName))
                self.GEN.VON()
            else:
                self.GEN.OPEN_STEP(job=self.job_name, step=stepName)
                self.GEN.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % self.job_name)
                self.GEN.CLOSE_STEP()

    def check_profile(self):
        """
        当panel中有个别模块未建profile输出时，产线喷墨程式不识别，现输出时检测panel中是否有漏profile的情况出现
        :return:
        """
        for step in self.panel_srs:
            info = self.GEN.DO_INFO('-t step -e %s/%s -m script -d PROF_LIMITS' % (self.job_name, step))
            if info['gPROF_LIMITSxmin'] == '0' and info['gPROF_LIMITSymin'] == '0' and info[
                'gPROF_LIMITSxmax'] == '0' and info['gPROF_LIMITSymax'] == '0':
                errorMsg = u'panel中的%s没有定义profile!\n\n产线喷墨程式不识别!\n\n请定义好profile并保存后再执行脚本!' % step
                self.Message('%s' % errorMsg)
                sys.exit(0)

    def add_id_101_user_attr(self):
        """
        windows环境将Z:/incam/genesis/userattr/userattr文件copy到本机/genesis/fw/lib/misc文件夹中
        :return:
        :rtype:
        """
        # --为了能够正常输出劲鑫tgz,需要加id=101属性，所以要更新userattr文件
        # src_user_attr = "Z:/incam/genesis/userattr/userattr"
        src_user_attr = r"Z:\incam\genesis\fw\lib\misc\userattr"
        GENESIS_DIR = os.environ.get('GENESIS_DIR', None)
        dst_user_attr = "%s/fw/lib/misc/userattr" % GENESIS_DIR
        dst_attr_backup = dst_user_attr + datetime.strftime(datetime.now(), '_bak%Y%m%d')
        if not os.path.exists(dst_user_attr):
            # --如果本机目标文件不存在，直接copy,否则比较时由于文件不存在会报
            # --WindowsError: [Error 2] : 'D:/genesis/fw/lib/misc/userattr'
            shutil.copy(src_user_attr, dst_user_attr)
        else:
            if not filecmp.cmp(src_user_attr, dst_user_attr):
                # --两个文件相等时，不用copy,只有当两个文件内容不同时，才copy
                shutil.move(dst_user_attr, dst_attr_backup)
                shutil.copy(src_user_attr, dst_user_attr)

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

    def check_rotate_tips(self):
        info = self.GEN.DO_INFO('-t step -e %s/panel -d sr' % self.job_name)
        rotate_steps = []
        for step, angle in zip(info.get('gSRstep'),info.get('gSRangle')):
            if angle not in ('0', '90', '180', '270', '360') and step not in rotate_steps:
                rotate_steps.append(step)
        return rotate_steps

    def add_101_attr(self, layer):
        # 如果没有id=101属性，则添加r0及id=101属性
        right_x = []
        right_y = []
        left_x = []
        left_y = []
        upper_x = []
        upper_y = []
        lower_x = []
        lower_y = []
        self.GEN.FILTER_RESET()
        self.GEN.FILTER_SET_INCLUDE_SYMS('sh-dwsd2014')
        # 靶点取有相应的防焊pad的靶点,李家兴2019.10.10依叶龙文要求修改
        info = self.GEN.DO_INFO('-t layer -e %s/panel/%s -m script -d SIDE' % (self.job_name, layer))
        if info['gSIDE'] == 'top':
            # refer_mask = 'm1'
            refer_mask = self.top_solder_layers[0]
        else:
            # refer_mask = 'm2'
            refer_mask = self.bot_solder_layers[0]
        self.GEN.COM('''sel_ref_feat,layers=%s,use=filter,mode=cover,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,
         polarity=positive\;negative,include_syms=,exclude_syms=''' % refer_mask)
        # self.GEN.FILTER_SELECT()
        self.GEN.FILTER_RESET()
        count = int(self.GEN.GET_SELECT_COUNT())
        # === 2022.07.19 如果仅获取到4个，不区分长短边
        if count == 4:
            # 添加r0,附有id=101属性
            self.GEN.CUR_ART_RESET()
            self.GEN.COM('cur_atr_set,attribute=id,int=101')
            info = self.GEN.INFO('-t layer -e %s/panel/%s -d FEATURES -o select' % (self.job_name, layer))
            for line in info[1:]:
                getline = line.split()
                xCoord = float(getline[1])
                yCoord = float(getline[2])
                self.GEN.ADD_PAD(xCoord, yCoord, 'r0.1', attr='yes')
            self.GEN.CUR_ART_RESET()
        elif count == 8:

            info = self.GEN.INFO('-t layer -e %s/panel/%s -d FEATURES -o select' % (self.job_name, layer))
            for line in info[1:]:
                getline = line.split()
                xCoord = float(getline[1])
                yCoord = float(getline[2])
                if xCoord < self.SR_INFO['srXmin'] and self.SR_INFO['srYmin'] < yCoord < self.SR_INFO['srYmax']:
                    left_x.append(xCoord)
                    left_y.append(yCoord)
                if xCoord > self.SR_INFO['srXmax'] and self.SR_INFO['srYmin'] < yCoord < self.SR_INFO['srYmax']:
                    right_x.append(xCoord)
                    right_y.append(yCoord)
                # 2020.5.18依据内联单要求将对位点设置到短边
                if yCoord < self.SR_INFO['srYmin'] and self.SR_INFO['srXmin'] < xCoord < self.SR_INFO['srXmax']:
                    lower_x.append(xCoord)
                    lower_y.append(yCoord)
                if yCoord > self.SR_INFO['srYmax'] and self.SR_INFO['srXmin'] < xCoord < self.SR_INFO['srXmax']:
                    upper_x.append(xCoord)
                    upper_y.append(yCoord)
                    
            if not lower_x or not upper_x or (long_side and (not left_x or not right_x)):                  
                self.GEN.AFFECTED_LAYER(layer, 'no')
                self.GEN.WORK_LAYER(layer, 1)
                self.GEN.FILTER_SET_INCLUDE_SYMS('sh-dwsd2014')
                self.GEN.PAUSE("抓取{0}层短边四个靶点sh-dwsd2014失败，请手动选择短板四个靶点然后继续！".format(layer))
                count = int(self.GEN.GET_SELECT_COUNT())
                while count != 4:
                    self.GEN.PAUSE("选择的靶点数量不是四个，请重新选择，请检查！")
                    count = int(self.GEN.GET_SELECT_COUNT())
                    if count == 4:
                        break
                    
                self.GEN.CUR_ART_RESET()
                self.GEN.COM('cur_atr_set,attribute=id,int=101')
                info = self.GEN.INFO('-t layer -e %s/panel/%s -d FEATURES -o select' % (self.job_name, layer))
                for line in info[1:]:
                    getline = line.split()
                    xCoord = float(getline[1])
                    yCoord = float(getline[2])
                    self.GEN.ADD_PAD(xCoord, yCoord, 'r0.1', attr='yes')
                self.GEN.CUR_ART_RESET()
                self.GEN.CLEAR_LAYER()
                return            
                    
            # 添加r0,附有id=101属性
            self.GEN.CUR_ART_RESET()
            self.GEN.COM('cur_atr_set,attribute=id,int=101')
            if long_side:
                # 取右上右下坐标(长边)
                right_upper_y = max(right_y)
                right_upper_x = right_x[right_y.index(right_upper_y)]
                right_lower_y = min(right_y)
                right_lower_x = right_x[right_y.index(right_lower_y)]
                
                # 取左上左下坐标(长边)
                left_upper_y = max(left_y)
                left_upper_x = left_x[left_y.index(left_upper_y)]
                left_lower_y = min(left_y)
                left_lower_x = left_x[left_y.index(left_lower_y)]
                
                self.GEN.ADD_PAD(left_upper_x, left_upper_y, 'r0.1', attr='yes')
                self.GEN.ADD_PAD(left_lower_x, left_lower_y, 'r0.1', attr='yes')
                self.GEN.ADD_PAD(right_upper_x, right_upper_y, 'r0.1', attr='yes')
                self.GEN.ADD_PAD(right_lower_x, right_lower_y, 'r0.1', attr='yes')
            else:
                # 取右上右下坐标（短边）
                lower_left_x = min(lower_x)
                lower_left_y = lower_y[lower_x.index(lower_left_x)]
                lower_right_x = max(lower_x)
                lower_right_y = lower_y[lower_x.index(lower_right_x)]
                
                # 取左上右上坐标（短边）
                upper_left_x = min(upper_x)
                upper_left_y = upper_y[upper_x.index(upper_left_x)]
                upper_right_x = max(upper_x)
                upper_right_y = upper_y[upper_x.index(upper_right_x)]
                
                self.GEN.ADD_PAD(upper_left_x, upper_left_y, 'r0.1', attr='yes')
                self.GEN.ADD_PAD(upper_right_x, upper_right_y, 'r0.1', attr='yes')
                self.GEN.ADD_PAD(lower_left_x, lower_left_y, 'r0.1', attr='yes')
                self.GEN.ADD_PAD(lower_right_x, lower_right_y, 'r0.1', attr='yes')
            self.GEN.CUR_ART_RESET()
        else:
            self.GEN.AFFECTED_LAYER(layer, 'no')
            self.GEN.WORK_LAYER(layer, 1)
            self.GEN.FILTER_SET_INCLUDE_SYMS('sh-dwsd2014')
            self.GEN.PAUSE("抓取{0}层短边四个靶点sh-dwsd2014失败，请手动选择短板四个靶点然后继续！".format(layer))
            count = int(self.GEN.GET_SELECT_COUNT())
            while count != 4:
                self.GEN.PAUSE("选择的靶点数量不是四个，请重新选择，请检查！")
                count = int(self.GEN.GET_SELECT_COUNT())
                if count == 4:
                    break
                
            self.GEN.CUR_ART_RESET()
            self.GEN.COM('cur_atr_set,attribute=id,int=101')
            info = self.GEN.INFO('-t layer -e %s/panel/%s -d FEATURES -o select' % (self.job_name, layer))
            for line in info[1:]:
                getline = line.split()
                xCoord = float(getline[1])
                yCoord = float(getline[2])
                self.GEN.ADD_PAD(xCoord, yCoord, 'r0.1', attr='yes')
            self.GEN.CUR_ART_RESET()
            self.GEN.CLEAR_LAYER()
            return
        
            #errorMsg = u"防焊层，文字对位symbol,sh-dwsd2014数量不为4或者8,\n\n程序即将退出!"
            #self.Message('%s' % errorMsg)
            #sys.exit(0)
            
    def delete_silk_target_symbol(self, output_silk_layers, reback_layer=False):
        """当同时存在喷印跟印刷流程时，删除喷印上的靶点 20240421 by lyh
        http://192.168.2.120:82/zentao/story-view-6698.html"""
        self.GEN.OPEN_STEP('panel')
        self.GEN.CHANGE_UNITS('mm')        
        for worklayer in output_silk_layers:
            if reback_layer:
                self.GEN.COPY_LAYER(self.job_name, "panel", worklayer+"_jinxin_bak_tmp", worklayer)
                self.GEN.DELETE_LAYER(worklayer+"_jinxin_bak_tmp")
                continue
            else:
                self.GEN.COPY_LAYER(self.job_name, "panel", worklayer, worklayer+"_jinxin_bak_tmp")
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER(worklayer, 'yes')
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_ATR_SYMS('id,min_int_val=101,max_int_val=101')
            self.GEN.FILTER_SELECT()
            self.GEN.FILTER_RESET()
            count = self.GEN.GET_SELECT_COUNT()
            if count:                
                self.GEN.FILTER_SET_INCLUDE_SYMS('sh-dwsd2014')
                self.GEN.COM("sel_ref_feat,layers=,use=select,mode=touch,\
                pads_as=shape,f_types=line\;pad\;surface\;arc\;text,\
                polarity=positive\;negative,include_syms=,exclude_syms=")
                count = self.GEN.GET_SELECT_COUNT()
                if count == 4:
                    self.GEN.SEL_DELETE()
        
        self.GEN.CLEAR_LAYER()

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
         
        #增加判断印刷跟喷印输出的层次 20230731 by lyh
        select_output_silk_layers,yinshua_silk_layers = self.get_penyin_silk_layers()
        if select_output_silk_layers:
            for layer in self.silk_layers:
                if layer in self.tgz_layers:
                    self.tgz_layers.remove(layer)
                    
        if yinshua_silk_layers:
            self.delete_silk_target_symbol(select_output_silk_layers, reback_layer=False)
                    
        # self.GEN.PAUSE(str([self.tgz_layers, select_output_silk_layers]))
        # --执行tgz导出
        include_lyrs = '\;'.join(self.tgz_layers+select_output_silk_layers)
        # --check_out后保存料号，并且马上check_in
        self.save_job_in_out()
        # --输出tgz,部分层别
        # elf.GEN.VOF()
        reVal = self.GEN.COM('export_job,job=%s,path=%s,mode=tar_gzip,submode=partial,'
                             'lyrs_mode=include,lyrs=%s,overwrite=yes' % (self.job_name, tmp_path, include_lyrs))
        # self.GEN.VON()
        
        if yinshua_silk_layers:
            self.delete_silk_target_symbol(select_output_silk_layers, reback_layer=True)
            self.save_job_in_out()
            
        # --export异常，用于后续自动输出异常抛出纪录
        if reVal != 0:
            errorMsg = u"tgz导出失败！\n\n程序即将退出，请联系管理员!"
            self.Message('%s' % errorMsg)
        else:
            # --删除目标地址下的资料
            if os.path.exists(os.path.join(tgz_path, self.job_name + str('_jinxin.tgz'))):
                os.remove(os.path.join(tgz_path, self.job_name + str('_jinxin.tgz')))
            # --重命名临时目录下的tgz,并Move至对应地址
            shutil.move(os.path.join(tmp_path, self.job_name + str('.tgz')),
                        os.path.join(tgz_path, self.job_name + str('_jinxin.tgz')))

            # --TODO 删除备份层改回正式层别名并保存
            if self.break_vg_date:
                self.to_orig_name()
            okMsg = u"tgz导出成功！！！"
            self.Message('%s' % okMsg)

    def save_job_in_out(self):
        """
        check_out后保存料号,并且check_in
        :return:
        :rtype:
        """
        self.GEN.VOF()
        self.GEN.COM('check_inout,mode=out,type=job,job=%s' % self.job_name)
        self.GEN.COM('save_job,job=%s,override=no' % self.job_name)
        self.GEN.COM('check_inout,mode=in,type=job,job=%s' % self.job_name)
        self.GEN.VON()

    def to_orig_name(self):
        """
        因为有非正常角度的周期而改名的文字层，改回原来的层别名
        :return:
        :rtype:
        """
        for layer in self.rename_layers:
            orig_layer = layer.strip('_before_break')
            # --删除flatten出来的层别c1_break/c2_break,后来rename为c1/c2
            self.GEN.DELETE_LAYER(orig_layer)
            self.GEN.COM('rename_layer,name=%s,new_name=%s' % (layer, orig_layer))
        if len(self.rename_layers):
            self.save_job_in_out()
        # --TODO 阴阳拼重建依赖关系
        self.restore_depend()

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

        # app = QtGui.QApplication(sys.argv)
        message = QtGui.QMessageBox.warning(None, u'警告信息!', text, QtGui.QMessageBox.Ok)
        # message.exec_()

    def ControlTheOutput(self):
        GetERPSilkDic = ConnectERP().GetERPSilkData(self.job_name)
        print json.dumps(GetERPSilkDic, indent=2, ensure_ascii=False)
        ValuesList = GetERPSilkDic.values()

        dellayer = []
        delotherlayer = []

        for ii in self.tgz_layers:
            if re.search(r"^(cc|cc2|cc-1|cc2-1|c1|c2|c1-1|c2-1)$", ii):
                dellayer.append(ii)
            elif re.search(r"^c", ii):
                delotherlayer.append(ii)

        straa = ''.join(ValuesList)
        if not "喷印" in straa and not '喷码' in straa:
            return False
        else:
            for k, v in GetERPSilkDic.items():
                if k != '文字' and re.search("印刷", v):
                    for delay in delotherlayer:
                        if delay in self.tgz_layers: self.tgz_layers.remove(delay)
                if k == '文字' and re.search("印刷", v):
                    for delaya in dellayer:
                        if delaya in self.tgz_layers: self.tgz_layers.remove(delaya)
        silks = filter(lambda x: re.search(r"^c", x), self.tgz_layers)
        if not self.CheckEWM(silks):
            return "F"
        return True

    def CheckEWM(self, milklist):
        """
        检测料号中是否有活动二维码设计
        :param milklist:
        :return:
        """

        for ly in milklist:
            dataline = self.GEN.INFO("-t layer -e %s/panel/%s -m script -d FEATURES -o break_sr" % (self.job_name, ly))
            # TODO 以下语句可以用于文字层添加的文字检测
            # text_list = [s for s in dataline if '#T' in s and '.string=pcb_number_tl' not in s]
            # print text_list
            if any("#B" in s for s in dataline): return False
            if filter(lambda s: s.startswith('#P') and "barcode" in s and '.nomenclature' in s, dataline):
                return False
        return True


class ConnectERP():
    def __init__(self):
        """
        连接erp数据库
        :return:
        """
        # --连接ERP oracle数据库
        self.DB_O = Oracle_DB.ORACLE_INIT()
        # --servername的连接模式
        self.dbc_e = self.DB_O.DB_CONNECT(host='172.20.218.247', servername='topprod', port='1521',
                                          username='zygc', passwd='ZYGC@2019')
        if not self.dbc_e:
            # --sid连接模式
            self.DB_O = Oracle_DB.ORACLE_INIT(tnsName='sid')
            self.dbc_e = self.DB_O.DB_CONNECT(host='172.20.218.247', servername='topprod1', port='1521',
                                              username='zygc', passwd='ZYGC@2019')

    def GetERPSilkData(self, job):
        """
        获取erp的文字流程信息
        :return:
        """
        sql = """
        SELECT 
          sgc01 料号,
          ecb17 说明,
          SGA02 工站,
          ta_sgc01 技术要求
        FROM 
           sgc_file a 
           inner join (SELECT * FROM ecb_file) w on w.ecb01=a.sgc01 AND a.sgc04=w.ecb08 and a.sgc03=w.ecb03
           inner join (SELECT * FROM sga_file) p on p.sga01=a.sgc05
        WHERE sgc01 like '%s' 
        and ecb17 like '%%文字%%' 
        and  (SGA02 like '%%印%%' or SGA02 like '%%喷%%')
        ORDER BY sgc03,sgcslk05 asc
        """ % job.upper()[:13]

        query_result = self.DB_O.SELECT_DIC(self.dbc_e, sql)
        self.__del__()
        if not query_result:
            Main().Message('未能抓取到ERP资源！请注意！！')
            sys.exit()
        datadic = {}

        print sql
        for i in range(len(query_result)):
            datadic[query_result[i]["说明"]] = query_result[i]["工站"]

        return datadic

    def __del__(self):
        # --关闭数据库连接
        if self.dbc_e:
            self.DB_O.DB_CLOSE(self.dbc_e)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    # if platform.system() == "Windows": app = QtGui.QApplication(sys.argv)
    if len(sys.argv) >= 2:
        if sys.argv[1] == 'long_side':
            long_side = True
    main = Main(debug=False)

"""
#2022/02/15 吕康侠更改

1.增加获取erp信息类GetERPSilkData 和屏蔽输出的层ControlTheOutput方法 需求：http://192.168.2.120:82/zentao/story-view-3949.html

2022.06.01
宋超
1.增加318系列周期字体的检查：http://192.168.2.120:82/zentao/story-view-4258.html

2022.07.15
吕康侠 Note by Song
1. 增加料号更改未保存提示；
2. 有二维码的时候提示有二维码，但是将二维码转铜再输出就部提示，可以直接输出劲鑫。

2022.07.20
宋超
1.取靶点，定位四个或者八个，四个时自动添加；
2.整合公共脚本中的劲鑫tgz输出（长边，jinxin_tgz-gg.py 合并至此脚本）,使用参数控制传入值

2022.07.27
宋超
1.更改GetERPSilkData，SQL语句，兼容文字大站为975-141I1。
http://192.168.2.120:82/zentao/story-view-4462.html

2022.08.17
宋超
1.程序中更改防焊层的默认值设定，更改为取任意top面及bot面之一做id=101添加时的参考层
715-841d1
http://192.168.2.120:82/zentao/story-view-4532.html


2022.09.08
宋超
1.有旋转周期输出劲鑫时，报阴阳拼版错误，更改输出程序，仅当旋转周期存在时，才释放阴阳拼版关系。
http://192.168.2.120:82/zentao/story-view-4622.html



20241009 
zl
1.遇旋转角度拼版的料号，输出劲鑫文字提醒旋转拼版注意更改周期
2.二维码未提示转铜
http://192.168.2.120:82/zentao/story-view-7341.html

"""

